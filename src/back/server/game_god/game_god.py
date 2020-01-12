import fastapi
import socketio
import aioredis
import logging
import uvicorn
import asyncio
from starlette.middleware import cors

from ..models import Game, GameAttrs, UsernameSidGame, GameAction
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
    game_dict = {"game_id": game_id, "num_players": 0, **game_params}
    await game_store.hmset_dict(game_id, game_dict)
    return Game(**game_dict)


@game_god.put("/add_player_to_game", status_code=200)
async def add_player_to_game(payload: UsernameSidGame):
    game_id = payload.game_id
    sid = payload.sid
    await games[game_id].add_player(sid=sid, name=payload.username)
    await asyncio.gather(
        game_store.set(sid, game_id),
        game_store.hincrby(game_id, "num_players"),
    )


@game_god.put("/game_action", status_code=200)
async def game_action(payload: GameAction):
    action = payload.action
    method = getattr(
        games[payload.game_id], f"{payload.action}_handler"
    )
    if action == "card_click":
        await method(game_action.sid, game_action.card)
    elif action == "play":
        await method(game_action.sid, game_action.timestamp)
    elif action == "asking_click":
        await method(game_action.sid, game_action.rank)
    else:
        await method(game_action.sid)


@main
def run():
    uvicorn.run(game_god, host="0.0.0.0")
