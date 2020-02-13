import faust
import aioredis
import socketio
import functools
from asyncio import gather
from ..utils import AsyncTimer
from functools import reduce
from operator import iconcat
import logging

TTL = 1

logger = logging.getLogger(__name__)

# consumes hand plays and increments "same hand just played" counts on
# appropriate games
hand_play_pinger = faust.App(
    "hand_play_pinger", broker="kafka://kafka:9092",
)

game_store = None
sio = socketio.AsyncRedisManager("redis://socketio_pubsub", write_only=True)


@hand_play_pinger.task
async def on_started():
    global game_store
    # TODO: azure docker compose doesn't support depends so timeout
    logger.info("connecting to redis")
    game_store = await aioredis.create_redis_pool(
        "redis://game_store", timeout=120
    )
    logger.info("connected to redis")


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
    AsyncTimer.spawn_after, TTL, cleanup_game_id_hand_hash
)


class HandPlay(faust.Record):
    game_id: str
    hand_hash: int


hand_play_topic = hand_play_pinger.topic("hand_plays", value_type=HandPlay)


@hand_play_pinger.agent(hand_play_topic)
async def hand_play_processor(hand_plays):
    async for hand_play in hand_plays:
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
                    "set_same_hand_just_played_count",
                    {"count": count},
                    room=sid,
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
                        "increment_same_hand_just_played_count", {}, room=sid
                    )
                )
        # game id is newest game to play hand
        aws.append(game_store.rpush(hand_hash, og_game_id))
        await gather(*aws)  # execute everything concurrently
        # makes sure game id and hand hash are unlinked after a sec
        expire_game_id_hand_hash(og_game_id, hand_hash)
