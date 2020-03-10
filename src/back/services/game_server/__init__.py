import os
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
from secrets import token_urlsafe
from datetime import datetime, timedelta
from jwt import encode, decode, PyJWTError
from fastapi import HTTPException, Depends
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from asyncio import gather, sleep, create_task
from cassandra.cqlengine.query import DoesNotExist
from starlette.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_406_NOT_ACCEPTABLE,
    HTTP_409_CONFLICT,
)

from .models import (
    Game,
    GameAttrs,
    GameIdUsername,
    GameKey,
    GameList,
    Token,
    GameId,
    UsernamePasswordReenterPassword,
    Alert,
)
from ...basedata import session
from ...basedata.models import User#, Username
from ..secrets import JWT_SECRET, BOT_KEY
from ..monitor import Event, events_counter


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
    client_manager=socketio.AsyncRedisManager(f"redis://socketio_pubsub"),
    ping_timeout=300,
    ping_interval=20,
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


GameAction, game_action_processor, Prayer, ear = None, None, None, None


@game_server_fast.on_event("startup")
async def on_startup():
    from ..game_god import (
        GameAction as ga,
        game_action_processor as gap,
        Prayer as p,
        ear as e,
    )

    # global game_store
    global game_store, GameAction, game_action_processor, Prayer, ear
    GameAction, game_action_processor, Prayer, ear = ga, gap, p, e

    # TODO: azure docker compose doesn't support depends so sets 5
    #       connection timeout
    logger.info("connecting to redis")
    game_store = await aioredis.create_redis_pool(
        "redis://game_store", timeout=120
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
    payload: OAuth2PasswordRequestForm = Depends(),
):
    username = payload.username
    if await authenticate_user(username, payload.password):
        logger.info(f"logged in user {username}")
        return {
            "access_token": await create_access_token(username),
            "token_type": "bearer",
        }


# TODO: remove after affording Username table
async def get_user_from_username(username: str):
    return await User.objects().allow_filtering().async_get(username=username)


# TODO: process database accesses through stream
async def get_user_id(username: str):
    """
    returns user id uuid as str
    """
    # return str((await Username.async_get(username=username)).user_id)
    return str((await get_user_from_username(username)).user_id)


async def get_password(*, user_id: str = None, username: str = None):
    if user_id:
        return (await User.async_get(user_id=user_id)).password
    if username:
        # return await User.async_get(user_id=await get_user_id(username)).password
        return (await get_user_from_username(username)).password


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
        # await Username.async_get(username=username)
        await get_user_from_username(username)
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
        # Username.async_create(username=username, user_id=user_id),
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
        JWT_SECRET,
        algorithm=AUTH_KEY_CRYPTO_ALG,
    )


def token_to_user_id_username(token: str) -> Tuple[str, str]:
    try:
        decoded_token: str = decode(
            token, JWT_SECRET, algorithms=AUTH_KEY_CRYPTO_ALG
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


@game_server_fast.post(
    "/create_game",
    dependencies=[Depends(authenticated_user)],
    response_model=Game,
    status_code=201,
)
async def add_game(payload: GameAttrs):
    # TODO: rate limit
    # TODO: populate game table
    logger.info("game server prays for game creation")
    prayer_kwargs = payload.dict()
    prayer_kwargs["game_id"] = game_id = str(uuid4())
    game_dict = await ear.ask(
        key=game_id,
        value=Prayer(prayer="add_game", prayer_kwargs=prayer_kwargs),
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
    user_id, username, game_key = None, None, None
    # so bots can join games without authentication
    if (bot_key := environ.get("HTTP_BOT_KEY")) and bot_key == BOT_KEY:
        pass
    elif auth := environ.get("HTTP_AUTHORIZATION"):
        # 7 chars in 'Bearer '
        user_id, username = token_to_user_id_username(auth[7:])
    else:
        raise ConnectionRefusedError("requires authentication")
    if not (game_id := environ.get("HTTP_GAME_ID")):
        raise ConnectionRefusedError("requires game id")
    if not bot_key and (
        not (game_key := environ.get("HTTP_GAME_KEY"))
        or game_key.encode()
        not in await game_store.zrevrangebyscore(
            f"{game_id}:game_keys", min=now
        )
    ):
        raise ConnectionRefusedError(
            "requires game key" if not game_key else "invalid game key"
        )
    # else key is valid

    await events_counter.cast("connect")
    # do adding to game as background task so socket connection is
    # accepted immediately after validation
    # TODO: prevent garbage collection of this task
    game_server_sio.start_background_task(add_player, game_id, sid, bot_key, game_key, user_id, username)
    


async def add_player(
    game_id: str,
    sid: str,
    bot_key: str,
    game_key: str,
    user_id: str,
    username: str,
):
    player_added = await ear.ask(
        # TODO: generate game id upstream so events are sent to correct agent
        key=game_id,
        value=Prayer(
            prayer="add_player",
            prayer_kwargs={
                "game_id": game_id,
                "user_id": user_id or str(uuid4()),
                "sid": sid,
                "username": username or "bot",
            },
        ),
    )
    # consume key even if player could not be added
    if not bot_key:
        await gather(
            game_store.zrem(f"{game_id}:game_keys", game_key),
            game_store.delete(game_key),
            prune_expired_game_keys(game_id),
        )
    if not player_added:
        # TODO: on this error (used to be in the connect listener)
        #       should disconnect the socket and client should handle
        #       switching to the game browser on socket disconnect
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
    await events_counter.cast("disconnect")


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
    return await game_action_processor.ask(
        key=game_id,
        value=GameAction(
            game_id=game_id,
            action=payload["action"],
            timestamp=timestamp,
            sid=sid,
        ),
    )
