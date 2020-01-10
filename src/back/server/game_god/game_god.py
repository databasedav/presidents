import fastapi
import socketio
import aioredis
import logging
from starlette.middleware import cors

from ..models import Game, GameAttrs, PlayerSidGame, GameAction
from ...game import EmittingGame
from ...utils import AsyncTimer


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
    game_store = await aioredis.create_redis_pool("redis://game_store")


@game_god.post("/add_game", response_model=Game, status_code=201)
async def add_game(game_attrs: GameAttrs):
    game_params = game_attrs.dict()
    game = EmittingGame(sio=sio, timer=AsyncTimer.spawn_after, **game_params)
    game_id = str(game.game_id)
    games[game_id] = game
    game_dict = {"game_id": game_id, "num_players": 0, **game_params}
    await game_store.hmset_dict(game_id, game_dict)
    return Game(**game_dict)


@game_god.put("/add_player_to_game", status_code=200)
async def add_player_to_game(player_sid_game: PlayerSidGame):
    await games[player_sid_game.game_id].add_player(
        sid=player_sid_game.sid, name=player_sid_game.username
    )
    await game_store.set(player_sid_game.sid, player_sid_game.game_id)


@game_god.put("/game_action", status_code=200)
async def game_action(game_action: GameAction):
    await getattr(games[game_action.game_id], f'{game_action.action}_handler')(game_action.sid, *[getattr(game_action, arg) for arg in ['card', 'rank', 'timestamp'] if getattr(game_action, arg)])
