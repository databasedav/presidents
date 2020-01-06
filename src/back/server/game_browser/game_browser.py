from fastapi import FastAPI, HTTPException
from typing import List
import aioredis
import asyncio
from uuid import uuid4
from secrets import token_urlsafe
from time import time
from socketio import AsyncClient
from aiohttp import ClientSession
import aiohttp
import uvicorn

from ..models import GameServer
from ...utils import main


game_browser = FastAPI()

redis = None
game_server_server_client = None


@game_browser.on_event('startup')
async def init_client():
    global redis, game_server_server_client
    redis = await aioredis.create_redis_pool('redis://redis')
    game_server_server_client = ClientSession()


async def add_game_server(
    name: str,
    *,
    turn_time: float = 30,
    reserve_time: float = 60,
    trading_time: float = 60,
    giving_time: float = 10
):
    """
    Adding a game server auto joins that game server.
    """
    # TODO: decide which AsyncServer to host the game server on
    ...
    # create the game server and register it to the AsyncServer
    # this should be done on the GameServerServer...
    async with game_server_server_client.post(
        'game_server_server/add_game_server',
        data={
            'name': name,
            'turn_time': turn_time,
            'reserve_time': reserve_time,
            'trading_time': trading_time,
            'giving_time': giving_time
        }
    ) as response:
        assert response.status == 201
        game_server_id = response.game_server_id
    # add game server to redis game server store
    await redis.hmset_dict(
        game_server_id,
        game_server_id=game_server_id,
        game_server_server_id=1,
        name=name,
        turn_time=turn_time,
        reserve_time=reserve_time,
        trading_time=trading_time,
        giving_time=giving_time,
        # add player after the game server join has been confirmed
        num_players=0
    )

    
@game_browser.get('/join_game/')
async def join_game(game_server_id: str, username: str):
    """
    Simply returns to the client which game server server the game
    server is running on so client can connect to the appropriate
    AsyncServer.
    """
    # first find out which Async server the game is running on
    ...
    # if the number of distributed keys fills the game tell the client
    # that the game is full and they should refresh and try again
    if int(await redis.hget(game_server_id, 'num_players')) + await redis.zcount(f'{game_server_id}:keys', min=time()) >= 4:
        raise HTTPException(status_code=409, detail='game is full; refresh and try again')
    key = token_urlsafe()
    # key is valid for 10 seconds
    await redis.zadd(f'{game_server_id}:keys', time() + 10, key)
    return {'key': key}


@game_browser.post("/create_game/")
async def create_game(name: str):
    await add_game_server(name)


@game_browser.get("/game_servers")
async def game_servers():
    ...

# @main
# def run():
#     uvicorn.run(game_browser, host="127.0.0.1", port=5001)
