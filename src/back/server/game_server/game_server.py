import re
import aiohttp
import fastapi
import logging
import uvicorn
import aioredis
import pydantic
import socketio
import aiocassandra
import pkg_resources
import passlib.context

from time import time
from uuid import uuid4
from typing import List
from asyncio import gather, sleep
from secrets import token_urlsafe
from datetime import datetime, timedelta
from jwt import encode, decode, PyJWTError
from fastapi import HTTPException, Depends
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from cassandra.cqlengine.query import DoesNotExist
from starlette.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_406_NOT_ACCEPTABLE,
    HTTP_409_CONFLICT,
)

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
    Token,
    GameId,
    UsernamePasswordReenterPassword,
    Alert
)
from ...data.db import session
from ...data.db.models import User, Username
from ...data.stream import game_action_agent
from ...data.stream.records import GameAction
from ..secrets import SECRET


# TODO: cache exceptions?


AUTH_KEY_TTL_HOURS = 12
GAME_KEY_TTL_SECONDS = 10
AUTH_KEY_CRYPTO_ALG = "HS256"


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

oauth2_scheme = fastapi.security.OAuth2PasswordBearer(tokenUrl="/token")

game_server_sio = socketio.AsyncServer(
    async_mode="asgi",
    client_manager=socketio.AsyncRedisManager("redis://socketio_pubsub"),
    cors_allowed_origins="*",
)

game_server = socketio.ASGIApp(
    socketio_server=game_server_sio, other_asgi_app=game_server_fast
)

# the game store holds keys corresponding to the following:
#   - game id to game attributes (these are available in the
#     game browser)
#   - game id keys to sorted set used to manage game specific keys and
#     expirations
#   - game key to username (remove after auth)
#   - sid to game id
#   - set of game_ids
game_store = None

# a single client suffices
game_god_client = None

# simple cache for sid to game id; these are always available in the
# game store; TODO: handle leaving games and preventing cache from
# getting too large
sid_game_id_dict = dict()
sid_username_dict = dict()


# In [62]: %timeit cc.hash(str(uuid4()))
# 101 ms ± 1.1 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)
# TODO benchmark this on azure
password_context = passlib.context.CryptContext(
    schemes=["argon2"],
    argon2__time_cost=2,
    argon2__memory_cost=256000,
    argon2__parallelism=8,
    argon2__hash_len=16,
    argon2__salt_len=16,
)

# TODO: reject common passwords
# TODO: rehash and update db if hash is using deprecated scheme


async def authenticate_user(username: str, password: str):
    try:
        if password_context.verify(
            password, (await User.async_get(username=username)).password
        ):
            return True
        else:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except DoesNotExist:
        # same error whether or not exists to prevent haxing
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


# https://github.com/tiangolo/fastapi/issues/130#issuecomment-491379252
try:
    game_server_fast.mount(
        "/assets",
        StaticFiles(
            directory=pkg_resources.resource_filename(
                __name__, "static/assets"
            )
        ),
    )
except RuntimeError:  # development
    pass


@game_server_fast.on_event("startup")
async def on_startup():
    global game_store, game_god_client

    # TODO: azure docker compose doesn't support depends so sets 5
    #       connection timeout
    game_store = await aioredis.create_redis_pool(
        "redis://game_store", timeout=300
    )

    # here because requires event loop
    game_god_client = aiohttp.ClientSession()

    # here because requires event loop
    # from cassandra.cqlengine import management
    # management.sync_table(User)
    aiocassandra.aiosession(session)


@game_server_fast.get("/")
def root():
    return HTMLResponse(
        pkg_resources.resource_string(__name__, "static/index.html")
    )


@game_server_fast.post("/token", response_model=Token)
async def login_for_access_token(
    payload: OAuth2PasswordRequestForm = Depends()
):
    username = payload.username
    if authenticate_user(username, payload.password):
        return {
            "access_token": create_access_token(username),
            "token_type": "bearer",
        }


# TODO: password rules (can't be weak)
@game_server_fast.post("/register", response_model=Alert, status_code=201)
async def register(payload: UsernamePasswordReenterPassword):
    username = payload.username
    password = payload.password
    try:
        await Username.async_get(username=username)
        # username already exists
        raise HTTPException(
            status_code=HTTP_409_CONFLICT, detail="username taken"
        )
    except DoesNotExist:
        # frontend enforces username and password rules (NOTE: these
        # must be updated manually) but hax
        if (
            not 1 <= len(username) <= 20
            # letters, numbers, underscores only
            or not re.match(r"^[a-zA-Z0-9_]+$", username)
            or re.match(r"^[0-9]+$", username)  # no all numbers
            or re.match(r"^_+$", username)  # no all underscores
        ):
            raise HTTPException(
                status_code=HTTP_409_CONFLICT, detail="invalid username"
            )
        if not 8 <= len(password) <= 40:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT, detail="invalid password"
            )
        if password != payload.reenter_password:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail="must re enter same password",
            )

        await add_user(username, password)
        return {'alert': 'account created'}

async def add_user(username: str, password: str):
    user_id = uuid4()
    await gather(
        User.async_create(
            user_id=user_id,
            username=username,
            password=password_context.hash(password),
            created=datetime.utcnow(),
        ),
        Username.async_create(username=username, user_id=user_id),
    )


def create_access_token(
    username: str, ttl_delta: timedelta = timedelta(hours=AUTH_KEY_TTL_HOURS)
):
    return encode(
        {"sub": username, "exp": datetime.utcnow() + ttl_delta},
        SECRET,
        algorithm=AUTH_KEY_CRYPTO_ALG,
    )


def token_to_username(token: str, exception):
    try:
        username: str = decode(
            token, SECRET, algorithms=AUTH_KEY_CRYPTO_ALG
        ).get("sub")
        if username is None:
            raise exception()  # exception is lazily generated
        return username
    except PyJWTError:
        raise exception()


async def authenticated_user(token: str = Depends(oauth2_scheme)):
    return token_to_username(
        token,
        lambda: HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="requires authentication",
            headers={"WWW-Authenticate": "Bearer"},
        ),
    )


# TODO: requires auth
@game_server_fast.post("/create_game", response_model=Game, status_code=201)
async def add_game(
    payload: GameAttrs, username: str = Depends(authenticated_user)
):
    async with game_god_client.post(
        "http://game_god/add_game", json=payload.dict()
    ) as response:

        assert response.status == 201
        return await response.json()


# TODO: requires auth
# TODO: jwt token contains username; can remove username arg after
#       can remove above model after as well
@game_server_fast.put("/join_game", response_model=GameKey, status_code=200)
async def request_game_key(
    payload: GameId, username: str = Depends(authenticated_user)
):
    """
    Simply returns to the client a key to join the specified game if
    there is space in the game at the time of their request to join.
    """
    game_id = payload.game_id
    if not await game_store.exists(game_id):
        raise HTTPException(
            status_code=HTTP_406_NOT_ACCEPTABLE, detail="game does not exist"
        )
    # if the number of valid distributed keys fills the game, tell the
    # client that the game is full and they should refresh and try again
    if (
        int(await game_store.hget(game_id, "num_players"))
        + await game_store.zcount(f"{game_id}:game_keys", min=time())
        >= 4
    ):
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail="game is full; refresh and try again",
        )

    # game is not full; respond with key
    game_key = token_urlsafe()
    await gather(
        prune_expired_game_keys(game_id),
        # add a game key
        game_store.zadd(
            f"{game_id}:game_keys", time() + GAME_KEY_TTL_SECONDS, game_key
        ),
        # only a specific user can use the key
        game_store.set(game_key, payload.username),
    )
    return {"game_key": game_key}


@game_server_fast.get("/get_games", response_model=GameList)
async def get_games(username: str = Depends(authenticated_user)):
    # TODO: passing username as dependency for rate limiting
    return {
        "games": [
            {
                key.decode(): value.decode()
                for key, value in (await game_store.hgetall(game_id)).items()
            }
            async for game_id in game_store.isscan("game_ids")
        ]
    }


@game_server_sio.event
async def connect(sid, environ):
    now = time()
    username = token_to_username(
        environ.get("HTTP_TOKEN"),
        lambda: ConnectionRefusedError("requires authentication"),
    )
    game_id = environ.get("HTTP_GAME_ID")
    game_key = environ.get("HTTP_GAME_KEY")
    if not game_id or not game_key:
        raise ConnectionRefusedError(
            "connecting requires game id and game key"
        )
    elif game_key.encode() not in await game_store.zrevrangebyscore(
        f"{game_id}:game_keys", min=now
    ):
        raise ConnectionRefusedError("invalid game key")
    # else key is valid
    await prune_expired_game_keys(game_id)

    async with game_god_client.put(
        "http://game_god/add_player_to_game",
        json={"username": username, "sid": sid, "game_id": game_id},
    ) as response:
        # consume key even if player could not be added
        await gather(
            game_store.zrem(f"{game_id}:game_keys", game_key),
            game_store.delete(game_key),
        )

        if response.status != 200:
            raise ConnectionRefusedError(
                "could not add player to game; try again"
            )
        else:
            if int(await game_store.hget(game_id, "num_players")) == 4:
                # game is paused
                if not int(await game_store.hget(game_id, "fresh")):
                    async with game_god_client.put(
                        "http://game_god/resume_game",
                        json={"game_id": game_id},
                    ) as response:
                        assert response.status == 200
                else:
                    async with game_god_client.put(
                        "http://game_god/start_game", json={"game_id": game_id}
                    ) as response:
                        assert response.status == 200


async def prune_expired_game_keys(game_id: str):
    await game_store.zremrangebyscore(f"{game_id}:game_keys", max=time())


@game_server_sio.event
async def disconnect(sid):
    async with game_god_client.delete(
        "http://game_god/remove_player_from_game", json={"sid": sid}
    ) as response:
        assert response.status == 200


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
        "http://game_god/game_action",
        json={"game_id": await get_game_id(sid), "sid": sid, **payload},
    ) as response:
        assert response.status == 200
        await cast_game_action(sid, timestamp, db_action(**payload))


async def get_game_id(sid: str):
    try:
        return sid_game_id_dict[sid]
    except KeyError:
        game_id = await game_store.hget(sid, "game_id", encoding="utf-8")
        sid_game_id_dict[sid] = game_id
        return game_id


async def get_username(sid: str):
    try:
        return sid_username_dict[sid]
    except KeyError:
        user_id = await game_store.hget(sid, "user_id", encoding="utf-8")
        sid_username_dict[sid] = user_id
        return user_id


def db_action(action, *, card: int = None, rank: int = None):
    """
    translates action to db action; particularly, card clicks to card
    number and asking clicks to negative rank
    """
    if action == "card_click":
        return card
    elif action == "asking_click":
        return -rank
    else:
        return action


async def cast_game_action(sid: str, timestamp: datetime, action: str) -> None:
    await game_action_agent.cast(
        GameAction(
            game_id=str(uuid4()),
            user_id=str(uuid4()),
            timestamp=timestamp,
            action=action,
        )
    )
    # self._game_click_agent.cast(
    #     GameClick(
    #         game_id=self.game.id,
    #         user_id=self.game.get_user_id(sid),
    #         timestamp=timestamp,
    #         action=action,
    #     )
    # )


@main
def run():
    uvicorn.run(game_server, host="0.0.0.0", port=8000)
