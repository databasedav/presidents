import asyncio
import aioredis
import socketio
import fastapi
import uvicorn
import aiohttp
import logging
from time import time
from fastapi import HTTPException
from datetime import datetime
from secrets import token_urlsafe
from starlette.middleware.cors import CORSMiddleware

from ...utils import main
from ..models import Game, GameAttrs, GameIdUsername


KEY_TTL = 10  # time to live in seconds


logger = logging.getLogger(__name__)

game_server_fast = fastapi.FastAPI()
# TODO: i don't need all of these
game_server_fast.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
game_server_sio = socketio.AsyncServer(
    async_mode="asgi",
    client_manager=socketio.AsyncRedisManager('redis://socketio_pubsub'),
    cors_allowed_origins="*"
)

game_store = None
game_god_client = aiohttp.ClientSession()

sid_game_id_dict = dict()


async def get_game_id(sid: str):
    try:
        return sid_game_id_dict[sid]
    except KeyError:
        game_id = await game_store.get(sid, encoding="utf-8")
        sid_game_id_dict[sid] = game_id
    return game_id


@game_server_fast.on_event("startup")
async def on_startup():
    global game_store
    game_store = await aioredis.create_redis_pool("redis://game_store")


# TODO: requires auth
@game_server_fast.post("/create_game", response_model=Game, status_code=201)
async def add_game(game_attrs: GameAttrs):
    async with game_god_client.post(
        "http://game_god:8000/add_game", json=game_attrs.dict()
    ) as response:
        assert response.status == 201
        return Game(**await response.json())


# TODO: requires auth
# TODO: jwt token contains username; can remove username arg after
#       can remove above model after as well
@game_server_fast.put("/join_game", status_code=200)
async def request_game_key(game_id_username: GameIdUsername):
    """
    Simply returns to the client a key to join the specified game if
    there is space in the game at the time of their request to join.
    """
    game_id = game_id_username.game_id
    if not await game_store.exists(game_id):
        raise HTTPException(status_code=406, detail="game does not exist")
    # if the number of valid distributed keys fills the game, tell the
    # client that the game is full and they should refresh and try again
    if (
        int(await game_store.hget(game_id, "num_players"))
        + await game_store.zcount(f"{game_id}:game_keys", min=time())
        >= 4
    ):
        raise HTTPException(
            status_code=409, detail="game is full; refresh and try again"
        )
    game_key = token_urlsafe()
    # game key is valid for 10 seconds
    await asyncio.gather(
        prune_expired_keys(game_id),
        # add a game key
        game_store.zadd(f"{game_id}:game_keys", time() + KEY_TTL, game_key),
        # only a specific user can use the key
        game_store.set(game_key, game_id_username.username)
    )
    return {"game_key": game_key}


@game_server_sio.event
async def connect(sid, environ):
    now = time()
    game_id = environ.get("HTTP_GAME_ID")
    game_key = environ.get("HTTP_GAME_KEY")
    if not game_id or not game_key:
        raise ConnectionRefusedError("connecting requires game id and key")
    elif game_key.encode() not in await game_store.zrevrangebyscore(
        f"{game_id}:game_keys", min=now
    ):
        raise ConnectionRefusedError("invalid game key")
    await prune_expired_keys(game_id)

    async with game_god_client.put(
        "http://game_god:8000/add_player_to_game",
        json={
            "username": (await game_store.get(game_key)).decode(),
            "sid": sid,
            "game_id": game_id,
        },
    ) as response:
        await game_store.delete(game_key)
        if response.status != 200:
            raise ConnectionRefusedError(
                "could not add player to game; try again"
            )


async def prune_expired_keys(game_id: str):
    await game_store.zremrangebyscore(f"{game_id}:keys", max=time())

VALID_GAME_ACTIONS = {  # value is required payload
    'card_click': ['card', 'timestamp'],
    'unlock': None,
    'lock': None,
    'play': None,
    'unlock_pass': None,
    'pass': None,
    'ask': None,
    'give': None,
    'asking_click': ['rank']
}

@game_server_sio.event
async def game_action(sid, payload):
    timestamp = datetime.utcnow()
    assert payload['action'] in VALID_GAME_ACTIONS and VALID_GAME_ACTIONS[payload['action']] in payload if VALID_GAME_ACTIONS[payload['action']] else True
    async with game_god_client.put(
        "http://game_god:8000/game_action",
        json={**payload, "sid": sid, "game_id": await get_game_id(sid)},
    ) as response:
        assert response.status == 200
        # await cast_game_click(timestamp)


game_server = socketio.ASGIApp(
    socketio_server=game_server_sio, other_asgi_app=game_server_fast
)
