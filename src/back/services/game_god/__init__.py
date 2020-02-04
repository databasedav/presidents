import asyncio
import fastapi
import logging
import uvicorn
import aioredis
import socketio
from asyncio import gather
from starlette.middleware import cors

from ..utils.models import Game, GameAttrs, AddPlayerInfo, Sid, GameId
from ...game import EmittingGame
from ...utils import AsyncTimer, main


logger = logging.getLogger(__name__)

# the game god receives prayers and appropriately changes the state
game_god = fastapi.FastAPI()
game_god.add_middleware(
    cors.CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
games = dict()  # from game id to game object

sio = socketio.AsyncRedisManager("redis://socketio_pubsub", write_only=True)
game_store = None

import faust
from typing import Any, Optional

from datetime import datetime
from ..utils.game_action_pb2 import GameAction as GameActionProtobuf
from google.protobuf.timestamp_pb2 import Timestamp
from faust.models.fields import StringField
import socketio
from ..utils import GAME_ACTION_DICT


game_god1 = faust.App("presidents", broker="kafka://data_stream:9092")


@game_god.on_event("startup")
async def on_startup():
    # @game_god.task
    # async def on_started():
    global game_store
    # TODO: azure docker compose doesn't support depends so sets 5
    #       connection timeout
    game_store = await aioredis.create_redis_pool(
        "redis://game_store", timeout=300
    )
    asyncio.create_task(game_god1.start())


# game_god_prayer_topic = game_god.topic('game_god_prayers')

from typing import Dict

PRAYER_DICT = {"add_game": ("name")}


class Prayer(faust.Record):
    prayer: str
    prayer_kwargs: Dict[str, str]


@game_god1.agent(value_type=Prayer)
async def ear(prayers):
    # add_game
    # add_player_to_game
    # remove_player_from_game
    # start_game
    # resume_game
    async for prayer in prayers:
        assert prayer in PRAYER_DICT and all(
            kwarg in prayer.kwargs for kwarg in PRAYER_DICT[prayer.prayer]
        )
        return eval(prayer)(**prayer.kwargs)


@game_god.post("/add_game", response_model=Game, status_code=201)
async def add_game(payload: GameAttrs):
    game_params = payload.dict()
    game = EmittingGame(sio=sio, timer=AsyncTimer.spawn_after, **game_params)
    game_id = str(game.game_id)
    games[game_id] = game
    game_dict = {
        "game_id": game_id,
        "num_players": 0,
        "fresh": 1,
        **game_params,
    }
    await gather(
        game_store.hmset_dict(game_id, game_dict),
        game_store.sadd("game_ids", game_id),
    )
    return game_dict


async def remove_game(game_id):
    # TODO: incomplete
    await gather(
        game_store.delete(game_id), game_store.srem("game_ids", game_id)
    )


@game_god.put("/add_player_to_game", status_code=200)
async def add_player_to_game(payload: AddPlayerInfo):
    game_id = payload.game_id
    game = games[game_id]
    user_id = payload.user_id
    assert not game.in_players(user_id), "cannot join game multiple times"
    sid = payload.sid
    await game.add_player(name=payload.username, sid=sid, user_id=user_id)
    # above not in gather to confirm player was added
    await gather(
        game_store.set(sid, game_id),
        game_store.hincrby(game_id, "num_players"),
    )


@game_god.delete("/remove_player_from_game", status_code=200)
async def remove_player_from_game(payload: Sid):
    """
    Pauses game if not already paused and then removes player.
    """
    sid = payload.sid
    game_id = await game_store.get(sid, encoding="utf-8")
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


# TODO: can take a custom deck (e.g. within rules or something like
#       everyone gets a 2 of spades); maybe this wouldn't go here...
@game_god.put("/start_game", status_code=200)
async def start_game(payload: GameId):
    game_id = payload.game_id
    game = games[game_id]
    assert game.num_players == 4
    await game.start_round(setup=True)
    await game_store.hset(game_id, "fresh", "0")


@game_god.put("/resume_game", status_code=200)
async def resume_game(payload: GameId):
    game_id = payload.game_id
    game = games[game_id]
    assert game.num_players == 4
    await game.resume()


class game_action_protobuf(faust.Codec):
    def _dumps(self, obj: Any) -> bytes:
        game_action = GameActionProtobuf(
            game_id=obj["game_id"], action=obj["action"]
        )
        game_action.timestamp.FromDatetime(obj["timestamp"])
        for game_action_attr in ["sid", "user_id"]:
            attr = obj.get(game_action_attr)
            if attr:  # empty string default evals to false
                setattr(game_action, game_action_attr, attr)
        return game_action.SerializeToString()

    def _loads(self, s: bytes) -> Any:
        game_action = GameActionProtobuf()
        game_action.ParseFromString(s)
        game_action_attrs = {
            "game_id": game_action.game_id,
            "action": game_action.action,
            "timestamp": game_action.timestamp.ToDatetime(),
        }
        for game_action_attr in ["sid", "user_id"]:
            attr = getattr(game_action, game_action_attr)
            if attr:
                game_action_attrs[game_action_attr] = getattr(
                    game_action, game_action_attr
                )
        return game_action_attrs


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


# game_action_to_process = game_god.topic('game_action', value_type=GameAction)
# game_action_to_store = game_god


@game_god1.agent(value_type=GameAction)
async def game_action_processor(game_actions):
    async for game_action in game_actions:
        action, kwargs = GAME_ACTION_DICT[game_action.action]
        await getattr(games[game_action.game_id], f"{action}_handler")(
            game_action.sid, **kwargs
        )


# @game_god.put("/game_action", status_code=200)
# async def game_action(payload: GameAction):
#     action = payload.action
#     method = getattr(games[payload.game_id], f"{action}_handler")
#     if action == "card_click":
#         await method(payload.sid, payload.card)
#     elif action == "play":
#         await method(payload.sid, payload.timestamp)
#     elif action == "asking_click":
#         await method(payload.sid, payload.rank)
#     else:
#         await method(payload.sid)


@main
def run():
    uvicorn.run(game_god, host="0.0.0.0")
