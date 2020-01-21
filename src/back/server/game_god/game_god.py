import fastapi
import socketio
import aioredis
import logging
import uvicorn
import asyncio
from starlette.middleware import cors

from ..models import (
    Game,
    GameAttrs,
    UsernameSidGameId,
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
    while not game_store:
        try:
            game_store = await aioredis.create_redis_pool("redis://game_store")
        except ConnectionRefusedError:
            await asyncio.sleep(0.5)


@game_god.post("/add_game", response_model=Game, status_code=201)
async def add_game(payload: GameAttrs):
    game_params = payload.dict()
    game = EmittingGame(sio=sio, timer=AsyncTimer.spawn_after, **game_params)
    game_id = str(game.game_id)
    games[game_id] = game
    game_dict = {
        "game_id": game_id,
        "num_players": 0,
        "paused": 0,
        **game_params,
    }
    await asyncio.gather(
        game_store.hmset_dict(game_id, game_dict),
        game_store.sadd("game_ids", game_id),
    )
    return Game(**game_dict)


@game_god.put("/add_player_to_game", status_code=200)
async def add_player_to_game(payload: UsernameSidGameId):
    game_id = payload.game_id
    sid = payload.sid
    game = games[game_id]
    await game.add_player(sid=sid, name=payload.username)
    # above not in gather to confirm player was added
    await asyncio.gather(
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
    if not int(await game_store.hget(game_id, "paused")):
        await game.pause()
    await game.remove_player(sid)
    # above not in gather to confirm player was removed
    await asyncio.gather(
        game_store.hset(game_id, "paused", 1),
        game_store.delete(sid),  # sid no longer tied to game
        # decrement num players
        game_store.hincrby(game_id, "num_players", -1),
    )


# TODO: can take a custom deck (e.g. within rules or something like
#       everyone gets a 2 of spades); maybe this wouldn't go here...
@game_god.put("/start_game", status_code=200)
async def start_game(payload: GameId):
    game = games[payload.game_id]
    assert game.num_players == 4
    await game.start_round(setup=True)


@game_god.put("/resume_game", status_code=200)
async def resume_game(payload: GameId):
    game_id = payload.game_id
    game = games[game_id]
    assert game.num_players == 4
    await game.resume()
    await game_store.hset(game_id, "paused", 0)


@game_god.put("/game_action", status_code=200)
async def game_action(payload: GameAction):
    action = payload.action
    method = getattr(games[payload.game_id], f"{payload.action}_handler")
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
