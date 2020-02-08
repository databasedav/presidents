import faust
import asyncio
import fastapi
import logging
import uvicorn
import aioredis
import socketio
import traceback

from typing import Union
from asyncio import gather
from aiokafka import helpers
from datetime import datetime
from starlette.middleware import cors
from typing import Any, Dict, Optional
from faust.models.fields import StringField
from google.protobuf.timestamp_pb2 import Timestamp

from ..secrets import EVENTHUB_HOST, EVENTHUB_USERNAME, EVENTHUB_PASSWORD
from ...game import EmittingGame
from ..utils import GAME_ACTION_DICT
from ...utils import AsyncTimer, main
from ..utils.models import Game, AddPlayerInfo, Sid, GameId  # , GameAttrs
from ..utils.game_action_pb2 import GameAction as GameActionProtobuf


logger = logging.getLogger(__name__)

# the game god receives prayers and appropriately changes the state
# game_god = fastapi.FastAPI()
# game_god.add_middleware(
#     cors.CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
games = dict()  # from game id to game object

sio = socketio.AsyncRedisManager("redis://socketio_pubsub", write_only=True)
game_store = None


# game_god = faust.App(
#     "game_god",
#     broker=f"kafka://{EVENTHUB_HOST}",
#     broker_credentials=faust.SASLCredentials(
#         username=EVENTHUB_USERNAME,
#         password=EVENTHUB_PASSWORD,
#         ssl_context=helpers.create_ssl_context()
#     ),
#     stream_wait_empty=False
# )

game_god = faust.App(
    'game_god',
    broker='kafka://data_stream:9092',
    stream_wait_empty=False
)


@game_god.task
async def on_started():
    global game_store
    # TODO: azure docker compose doesn't support depends so timeout
    logger.info('connecting to redis')
    game_store = await aioredis.create_redis_pool(
        "redis://game_store", timeout=300
    )
    logger.info('connected to redis')


PRAYER_DICT = {
    "add_game": (
        "name",
        "turn_time",
        "reserve_time",
        "trading_time",
        "giving_time",
    ),
    "add_player": ("game_id", "user_id", "sid", "username"),
    "remove_player": ("sid",),
    "start_game": ("game_id",),
    "resume_game": ("game_id",),
}

# TODO: when multiple game gods, games should be created on round robin,
#       but then need to somehow guarantee that requests related to that
#       game go to the same agent; right now, since the game init gens
#       the id; 

class Prayer(faust.Record):
    prayer: str
    prayer_kwargs: Dict[str, Union[str, float]]


prayer_topic = game_god.topic('prayers', value_type=Prayer)


@game_god.agent(prayer_topic)
async def ear(prayers):
    async for prayer in prayers:
        prayer, kwargs = prayer.prayer, prayer.prayer_kwargs
        required_kwargs = PRAYER_DICT.get(prayer)
        # TODO: do this in record validation?
        if not required_kwargs:
            logger.error(f'game god got false prayer: {prayer}')
            continue
        if not sorted(kwargs.keys()) == sorted(required_kwargs):
            logger.error(f"game god got prayer with false kwargs: {prayer, kwargs}")
            continue
        try:
            yield await eval(prayer)(**kwargs)
        except:
            logger.error(
                f"prayer ({prayer, kwargs}) failed with exception: {traceback.format_exc()}"
            )


async def add_game(
    *,
    name: str,
    turn_time: float,
    reserve_time: float,
    trading_time: float,
    giving_time: float,
):
    game_attrs = {
        "name": name,
        "turn_time": turn_time,
        "reserve_time": reserve_time,
        "trading_time": trading_time,
        "giving_time": giving_time,
    }
    game = EmittingGame(sio=sio, timer=AsyncTimer.spawn_after, **game_attrs)
    game_id = str(game.game_id)
    logger.info(f'adding game {game_id} with attributes {game_attrs}')
    try:
        games[game_id] = game
        game_dict = {
            "game_id": game_id,
            "num_players": 0,
            "fresh": 1,
            **game_attrs,
        }
        await gather(
            game_store.hmset_dict(game_id, game_dict),
            game_store.sadd("game_ids", game_id),
        )
        logger.info(f'added game {game_id}')
        return game_dict
    except:
        logger.error(f'adding game {game_id} failed with exception: {traceback.format_exc()}')
        return 0

async def remove_game(game_id):
    # TODO: incomplete
    logger.info(f'removing game {game_id}')
    await gather(
        game_store.delete(game_id), game_store.srem("game_ids", game_id)
    )
    logger.info(f'removed game {game_id}')


async def add_player(*, game_id: str, user_id: str, sid: str, username: str):
    logger.info(f'adding user {user_id} to game {game_id} with sid {sid} and username {username}')
    game = games[game_id]
    assert not game.in_players(user_id), "cannot join game multiple times"
    try:
        await game.add_player(name=username, sid=sid, user_id=user_id)
        # above not in gather to confirm player was added
        await gather(
            game_store.set(sid, game_id),
            game_store.hincrby(game_id, "num_players"),
        )
        logger.info(f'added user {user_id} to game {game_id} with sid {sid} and username {username}')
        return 1
    except:
        logger.error(f"failed to add user {user_id} to game {game_id} with sid {sid} and username {username} with exception: {traceback.format_exc()}")
        return 0


async def remove_player(*, sid: str):
    """
    Pauses game if not already paused and then removes player.
    """
    logger.info(f'removing sid {sid} from game')
    try:
        game_id = await game_store.get(sid, encoding="utf-8")
        logger.info(f'removing sid {sid} from game')
        game = games[game_id]
        if game.is_started and not game.is_paused:
            await game.pause()
        await game.remove_player(sid)
        # above not in gather to confirm player was removed
        await gather(
            game_store.delete(sid),  # sid no longer tied to game
            # remove game if no players remain; otherwise update num players
            remove_game(game_id)
            if game.num_players == 0
            else game_store.hincrby(game_id, "num_players", -1),
        )
        logger.info(f'removed sid {sid} from game {game_id}')
        return 1
    except:
        logger.error(f"removing sid {sid} failed with exception: {traceback.format_exc()}")
        return 0

# TODO: can take a custom deck (e.g. within rules or something like
#       everyone gets a 2 of spades); maybe this wouldn't go here...
async def start_game(*, game_id: str):
    logger.info(f'starting game {game_id}')
    try:
        game = games[game_id]
        assert game.num_players == 4
        await game.start_round(setup=True)
        await game_store.hset(game_id, "fresh", "0")
        return 1
    except:
        logger.error(f'starting game {game_id} failed with exception: {traceback.format_exc()}')
        return 0


async def resume_game(*, game_id: str):
    logger.info(f'resuming game {game_id}')
    try:
        game = games[game_id]
        assert game.num_players == 4
        await game.resume()
        return 1
    except:
        logger.error(f'resuming game {game_id} failed with exception: {traceback.format_exc()}')
        return 0

class game_action_protobuf(faust.Codec):
    def _dumps(self, obj: Any) -> bytes:
        game_action = GameActionProtobuf(
            game_id=obj["game_id"], action=obj["action"]
        )
        game_action.timestamp.FromDatetime(obj["timestamp"])
        for attr in ['sid', 'user_id']:
            if val := obj.get(attr):
                setattr(game_action, attr, val)
        return game_action.SerializeToString()

    def _loads(self, s: bytes) -> Any:
        game_action = GameActionProtobuf()
        game_action.ParseFromString(s)
        return {
            "game_id": game_action.game_id,
            "action": game_action.action,
            "timestamp": game_action.timestamp.ToDatetime(),
            # empty string is default string in protobuf
            'sid': getattr(game_action, 'sid') or None,
            'user_id': getattr(game_action, 'user_id') or None
        }


faust.serializers.codecs.register(
    "game_action_protobuf", game_action_protobuf()
)


class GameAction(
    faust.Record, serializer="game_action_protobuf", validation=True
):
    game_id: str
    action: int
    timestamp: datetime
    # TODO: make faust pr so that not assigning None doesn't give validation error
    sid: str = None
    user_id: str = None


# TODO
class ActionField(faust.models.FieldDescriptor[int]):
    def validate(self, value: int):
        ...

game_action_topic = game_god.topic('game_actions', key_type=str, value_type=GameAction)

@game_god.agent(game_action_topic)
async def game_action_processor(game_actions):
    async for game_action in game_actions:
        logger.info(f'processing game action {game_action}')
        action, kwargs = GAME_ACTION_DICT[game_action.action]
        try:
            await getattr(games[game_action.game_id], f"{action}_handler")(
                game_action.sid, **kwargs
            )
            yield 1
        except:
            logger.error(
                f"game action {game_action} failed with exception: {traceback.format_exc()}"
            )
            yield 0

# if __name__ == "__main__":
#     import asyncio
#     async def s():
#         await asyncio.sleep(1000000000)
#     asyncio.run(s())
