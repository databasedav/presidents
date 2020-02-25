import faust
from ...utils import get_redis, spawn_after
import socketio
import logging
from asyncio import gather
import functools
import datetime


TTL = 5

logger = logging.getLogger(__name__)

# central monitor
# TODO: separate in game and out of game monitors

monitor = faust.App("monitor", broker="kafka://kafka:9092")


class Event(faust.Record):
    event: str


events_dict = {"connect": 0, "disconnect": 0, 'autoplay': 0}

events_topic = monitor.topic("events", value_type=str)


@monitor.agent()
async def events_counter(events):
    async for event in events:
        events_dict[event] += 1


@monitor.page("/events")
async def get_events(web, request):
    return web.json(events_dict)


game_store = None
sio = socketio.AsyncRedisManager("redis://socketio_pubsub", write_only=True)


@monitor.task
async def on_started():
    global game_store
    logger.info("monitor connecting to game store")
    game_store = await get_redis("game_store")
    logger.info("monitor connected to game store")


async def cleanup_game_id_hand_hash(game_id: str, hand_hash: int):
    await gather(
        # delete from game hash if the hand hash hasn't been overwritten
        # else the game is in this hand hash's exclude set
        game_store.hdel(game_id, "hand_hash")
        if hand_hash == await game_store.hget("game_id", "hand_hash")
        else game_store.srem(f"{hand_hash}:exclude", game_id),
        game_store.lpop(hand_hash),
    )


expire_game_id_hand_hash = functools.partial(
    spawn_after, TTL, cleanup_game_id_hand_hash
)


class HandPlay(faust.Record):
    game_id: str
    hand_hash: int


hand_play_topic = monitor.topic(
    "hand_plays",
    value_type=HandPlay,
    # TODO: separate process should create kafka topics
    partitions=2,
    internal=True,
)

hands_dict = {i: list() for i in range(1, 6)}

# hands of certain size played per minute shown every 10 seconds
# i.e. count hands in 10 second windows times 6
# TODO: have this return subsequent plots
@monitor.page("/hands")
async def get_hands(self, request):
    return self.json(hands_dict)


from ...game.hand import hand_table

hand_size_table = monitor.Table(
    "hand_size", default=int, partitions=2
).tumbling(10, expires=datetime.timedelta(minutes=2))


async def hand_size_sink(hand_id):
    hand_size_table[hand_id // 10] += 1


@monitor.agent(hand_play_topic, sink=[hand_size_sink])
async def hand_play_processor(hand_plays):
    async for hand_play in hand_plays:
        logger.info(f"processing hand play {hand_play}")
        game_id = hand_play.game_id
        hand_hash = hand_play.hand_hash
        # if game id still in another hand hash's list, it should be
        # excluded from future pings for that hand
        if old_hand_hash := await game_store.hget(game_id, "hand_hash"):
            await game_store.sadd(f"{old_hand_hash}:exclude", game_id)

        aws = list()
        # get game ids where same hand was just played, inc. exclusions
        game_ids, exclude_game_ids = await gather(
            game_store.lrange(hand_hash, 0, -1, encoding="utf-8"),
            game_store.smembers(f"{hand_hash}:exclude"),
        )
        count = len(game_ids)
        # first set initial count to game that just played the hand
        async for sid in game_store.isscan(f"{game_id}:sids"):
            aws.append(
                sio.emit(
                    "set_hand_just_played_count",
                    {"count": count},
                    room=sid.decode(),  # read in as bytes,
                )
            )
        og_game_id = game_id
        # then iterate through other games
        for game_id in game_ids:
            if game_id in exclude_game_ids:
                continue
            async for sid in game_store.isscan(f"{game_id}:sids"):
                aws.append(
                    sio.emit(
                        # TODO: make the number pop on increment
                        "increment_hand_just_played_count",
                        {},
                        room=sid.decode(),  # read in as bytes
                    )
                )
        # game id is newest game to play hand
        aws.append(game_store.rpush(hand_hash, og_game_id))
        await gather(*aws)  # execute everything concurrently
        # makes sure game id and hand hash are unlinked after a sec
        expire_game_id_hand_hash(og_game_id, hand_hash)

        yield hand_table[hand_hash]


@monitor.agent()
async def hands_dict_updater(updates):
    async for _ in updates:
        for i in range(1, 6):
            hands_dict[i].append(hand_size_table[i].delta(10))


@monitor.timer(interval=10)
async def update_hands_dict():
    await hands_dict_updater.cast(1)
