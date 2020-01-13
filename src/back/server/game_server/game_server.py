import asyncio
import aioredis
import socketio
import fastapi
import uvicorn
import aiohttp
import logging
from time import time
from typing import List
from fastapi import HTTPException
from datetime import datetime
from secrets import token_urlsafe
from starlette.middleware.cors import CORSMiddleware

from ...utils import main
from ..models import (
    Game,
    GameAttrs,
    GameIdUsername,
    UsernameSidGameId,
    GameKey,
    Username,
    GameList,
    GameAction,
)


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
    client_manager=socketio.AsyncRedisManager("redis://socketio_pubsub"),
    cors_allowed_origins="*",
)

# the game store holds keys corresponding to the following:
#   - game id to game attributes (these are available in the
#     game browser)
#   - game id keys to sorted set used to manage game specific keys and
#     expirations
#   - game key to username (remove after auth)
#   - sid to game id
#   - list of game_ids
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
    while not game_store:
        try:
            game_store = await aioredis.create_redis_pool("redis://game_store")
        except ConnectionRefusedError:
            await asyncio.sleep(0.5)


# TODO: requires auth
@game_server_fast.post("/create_game", response_model=Game, status_code=201)
async def add_game(payload: GameAttrs):
    async with game_god_client.post(
        "http://game_god:8000/add_game", json=payload.dict()
    ) as response:
        assert response.status == 201
        return Game(**await response.json())


# TODO: requires auth
# TODO: jwt token contains username; can remove username arg after
#       can remove above model after as well
@game_server_fast.put("/join_game", response_model=GameKey, status_code=200)
async def request_game_key(payload: GameIdUsername):
    """
    Simply returns to the client a key to join the specified game if
    there is space in the game at the time of their request to join.
    """
    game_id = payload.game_id
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
        game_store.set(game_key, payload.username),
    )
    return GameKey(game_key=game_key)


@game_server_fast.get("/get_games", response_model=GameList)
async def get_games():
    return GameList(
        games=[
            {
                key.decode(): value.decode()
                for key, value in (await game_store.hgetall(game_id)).items()
            }
            async for game_id in game_store.isscan("game_ids")
        ]
    )


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
    # else key is valid
    await prune_expired_keys(game_id)

    async with game_god_client.put(
        "http://game_god:8000/add_player_to_game",
        json={
            "username": (await game_store.get(game_key)).decode(),
            "sid": sid,
            "game_id": game_id,
        },
    ) as response:
        # consume key even if player could not be added
        await asyncio.gather(
            game_store.zrem(f"{game_id}:game_keys", game_key),
            game_store.delete(game_key),
        )

        if response.status != 200:
            raise ConnectionRefusedError(
                "could not add player to game; try again"
            )
        else:
            num_players = int(await game_store.hget(game_id, "num_players"))
            if num_players == 4:
                # game is paused
                if int(await game_store.hget(game_id, "paused")):
                    async with game_god_client.put(
                        "http://game_god:8000/resume_game",
                        json={"game_id": game_id},
                    ) as response:
                        assert response.status == 200
                else:
                    async with game_god_client.put(
                        "http://game_god:8000/start_game",
                        json={"game_id": game_id},
                    ) as response:
                        assert response.status == 200


async def prune_expired_keys(game_id: str):
    await game_store.zremrangebyscore(f"{game_id}:game_keys", max=time())


@game_server_sio.event
async def disconnect(sid):
    # remove player from game (pauses game)
    # tell other players in game that a player has left and the game
    # will start again once they rejoin
    async with game_god_client.delete(
        "http://game_god:8000/remove_player_from_game", json={"sid": sid}
    ) as response:
        assert response.status == 200
    ...


VALID_GAME_ACTIONS = {  # value is required payload
    "card_click": "card",
    "unlock": None,
    "lock": None,
    "play": None,
    "unlock_pass": None,
    "pass": None,
    "ask": None,
    "give": None,
    "asking_click": "rank",
}


@game_server_sio.event
async def game_action(sid, payload):
    timestamp = datetime.utcnow()

    # action and payload validation
    action = payload["action"]
    assert action in VALID_GAME_ACTIONS
    required_payload = VALID_GAME_ACTIONS[action]
    if required_payload:
        assert required_payload in payload

    async with game_god_client.put(
        "http://game_god:8000/game_action",
        json={"game_id": await get_game_id(sid), "sid": sid, **payload},
    ) as response:
        assert response.status == 200
        # await cast_game_click(timestamp)


game_server = socketio.ASGIApp(
    socketio_server=game_server_sio, other_asgi_app=game_server_fast
)


@main
def run():
    uvicorn.run(game_server, host="0.0.0.0")
