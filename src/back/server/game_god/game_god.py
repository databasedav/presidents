import asyncio
import fastapi
import logging
import uvicorn
import aioredis
import socketio
from asyncio import gather
from starlette.middleware import cors

from ..models import (
    Game,
    GameAttrs,
    AddPlayerInfo,
    GameAction,
    Sid,
    GameId,
)
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


@game_god.on_event("startup")
async def on_startup():
    global game_store
    # TODO: azure docker compose doesn't support depends so sets 5
    #       connection timeout
    game_store = await aioredis.create_redis_pool(
        "redis://game_store", timeout=300
    )


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
        game_store.delete(game_id),
        game_store.srem("game_ids", game_id)
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


@game_god.put("/game_action", status_code=200)
async def game_action(payload: GameAction):
    action = payload.action
    method = getattr(games[payload.game_id], f"{action}_handler")
    if action == "card_click":
        await method(payload.sid, payload.card)
    elif action == "play":
        await method(payload.sid, payload.timestamp)
    elif action == "asking_click":
        await method(payload.sid, payload.rank)
    else:
        await method(payload.sid)


@main
def run():
    uvicorn.run(game_god, host="0.0.0.0")
