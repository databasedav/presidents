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
from typing import List, Tuple
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
from ..utils.models import (
    Game,
    GameAttrs,
    GameIdUsername,
    GameKey,
    Username,
    GameList,
    Token,
    GameId,
    UsernamePasswordReenterPassword,
    Alert,
)
from ...data.db import session
from ...data.db.models import User, Username
from ..game_god import game_action_processor, GameAction

try:
    from .secrets import SECRET
except:
    import os

    SECRET = os.getenv("TOKEN_SECRET")

# TODO: cache exceptions?
# TODO: asap: set max messages on the frontend, fix the auto scroll

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
#   - sid to game id
#   - set of game_ids
#   - game_id to sids
game_store = None

# simple cache for sid to game id; these are always available in the
# game store; TODO: handle leaving games and preventing cache from
# getting too large
sid_game_id_dict = dict()


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
# TODO: cache failed password attempt for a certain time to reduce db
#       reads


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


# async def get_game_store():
#     global game_store
#     if game_store:
#         return game_store
#     else:
#         logger.info('connecting to redis')
#         game_store = await aioredis.create_redis_pool(
#             "redis://game_store", timeout=300
#         )
#         logger.info('connected to redis')


@game_server_fast.on_event("startup")
async def on_startup():
    global game_store, game_god_client

    # TODO: azure docker compose doesn't support depends so sets 5
    #       connection timeout
    logger.info("connecting to redis")
    game_store = await aioredis.create_redis_pool(
        "redis://game_store", timeout=300
    )
    logger.info("connected to redis")

    # here because requires event loop
    logger.info("upgrading cqlengine")
    aiocassandra.aiosession(session)
    logger.info("upgraded cqlengine")


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
    if await authenticate_user(username, payload.password):
        logger.info(f"logged in user {username}")
        return {
            "access_token": await create_access_token(username),
            "token_type": "bearer",
        }


# TODO: process database accesses through stream
async def get_user_id(username: str):
    """
    returns user id uuid as str
    """
    return str((await Username.async_get(username=username)).user_id)


async def get_password(*, user_id: str = None, username: str = None):
    if user_id:
        return (await User.async_get(user_id=user_id)).password
    if username:
        return (
            await User.async_get(user_id=await get_user_id(username))
        ).password


async def authenticate_user(username: str, password: str):
    try:
        if password_context.verify(
            password, await get_password(username=username)
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
        # TODO: password rules (can't be weak)
        if not 8 <= len(password) <= 40:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT, detail="invalid password"
            )
        if password != payload.reenter_password:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail="must re enter same password",
            )

        # else username and password are ok
        await add_user(username, password)
        return {"alert": "account created"}


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


async def create_access_token(
    username: str, ttl_delta: timedelta = timedelta(hours=AUTH_KEY_TTL_HOURS)
):
    return encode(
        {
            "sub": await get_user_id(username),
            "username": username,
            "exp": datetime.utcnow() + ttl_delta,
        },
        SECRET,
        algorithm=AUTH_KEY_CRYPTO_ALG,
    )


def token_to_user_id_username(token: str) -> Tuple[str, str]:
    try:
        decoded_token: str = decode(
            token, SECRET, algorithms=AUTH_KEY_CRYPTO_ALG
        )
        user_id = decoded_token.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="requires authentication",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id, decoded_token.get("username")
    except PyJWTError:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="requires authentication",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def authenticated_user(token: str = Depends(oauth2_scheme)):
    # NOTE: only returns user id for now; might need username as well...
    return token_to_user_id_username(token)[0]


from ..game_god import Prayer, ear


@game_server_fast.post(
    "/create_game",
    dependencies=[Depends(authenticated_user)],
    response_model=Game,
    status_code=201,
)
async def add_game(payload: GameAttrs):
    # TODO: rate limit
    # TODO: populate game table
    logger.info("praying for game creation")
    game_dict = await ear.ask(
        value=Prayer(prayer="add_game", prayer_kwargs=payload.dict())
    )
    if not game_dict:
        return Alert(alert="failed to create game; try again")
    else:
        return Game(**game_dict)


@game_server_fast.put("/join_game", response_model=GameKey, status_code=200)
async def request_game_key(
    payload: GameId, user_id: str = Depends(authenticated_user)
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
        game_store.set(game_key, user_id),
    )
    return {"game_key": game_key}


@game_server_fast.get("/get_games", response_model=GameList)
async def get_games(user_id: str = Depends(authenticated_user)):
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
    auth = environ.get("HTTP_AUTHORIZATION")
    if not auth:
        raise ConnectionRefusedError("requires authentication")
        # 7 chars in 'Bearer '
    user_id, username = token_to_user_id_username(auth[7:])
    game_id = environ.get("HTTP_GAME_ID")
    game_key = environ.get("HTTP_GAME_KEY")

    if not game_id or not game_key:
        raise ConnectionRefusedError("requires game id and game key")
    elif game_key.encode() not in await game_store.zrevrangebyscore(
        f"{game_id}:game_keys", min=now
    ):
        raise ConnectionRefusedError("invalid game key")
    # else key is valid

    player_added = await ear.ask(
        key=game_id,
        value=Prayer(
            prayer="add_player",
            prayer_kwargs={
                "game_id": game_id,
                "user_id": user_id,
                "sid": sid,
                "username": username,
            },
        ),
    )
    # consume key even if player could not be added
    await gather(
        game_store.zrem(f"{game_id}:game_keys", game_key),
        game_store.delete(game_key),
        prune_expired_game_keys(game_id),
    )

    if not player_added:
        raise ConnectionRefusedError("could not add player to game; try again")
    else:
        if int(await game_store.hget(game_id, "num_players")) == 4:
            # game is paused
            if not int(await game_store.hget(game_id, "fresh")):
                assert await ear.ask(
                    key=game_id,
                    value=Prayer(
                        prayer="resume_game",
                        prayer_kwargs={"game_id": game_id},
                    ),
                )
            else:
                assert await ear.ask(
                    key=game_id,
                    value=Prayer(
                        prayer="start_game", prayer_kwargs={"game_id": game_id}
                    ),
                )


async def prune_expired_game_keys(game_id: str):
    await game_store.zremrangebyscore(f"{game_id}:game_keys", max=time())


@game_server_sio.event
async def disconnect(sid):
    assert await ear.ask(
        key=await get_game_id(sid),
        value=Prayer(prayer="remove_player", prayer_kwargs={"sid": sid}),
    )


async def get_game_id(sid: str):
    try:
        return sid_game_id_dict[sid]
    except KeyError:
        game_id = await game_store.get(sid, encoding="utf-8")
        sid_game_id_dict[sid] = game_id
        return game_id


@game_server_sio.event
async def game_action(sid, payload):
    timestamp = datetime.utcnow()
    game_id = await get_game_id(sid)
    await game_action_processor.cast(
        key=game_id,
        value=GameAction(
            game_id=game_id,
            action=payload["action"],
            timestamp=timestamp,
            sid=sid,
        ),
    )


@main
def run():
    uvicorn.run(game_server, host="0.0.0.0", port=8000)
