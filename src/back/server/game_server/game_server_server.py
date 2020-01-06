import asyncio
import aioredis
from socketio import AsyncServer, ASGIApp
from fastapi import FastAPI
import uvicorn

from .game_server import GameServer
from ...utils import main

game_server_server_game_browser_endpoint = FastAPI()

# TODO: implement unregister_namespace on python-socket.io and pr

class GameServerServer(AsyncServer):
    '''
    "Serves" game servers by managing the 
    '''
    def __init__(self):
        self.redis = asyncio.run(aioredis.create_redis_pool('redis://localhost'))
        super().__init__()

game_server_server_socketio_server = AsyncServer()

def game_server_namespace(game_server_id: str):
    return f'/game_server={game_server_id}'


def remove_game_server(game_server_server, game_server_id: str):
    game_server_server.namespace_handlers.pop(game_server_namespace(game_server_id))


@game_server_server_game_browser_endpoint.post('add_game_server', status_code=201)
async def add_game_server(
    name: str,
    turn_time: float,
    reserve_time: float,
    trading_time: float,
    giving_time: float
):
    game_server = GameServer(
        name,
        turn_time=turn_time,
        reserve_time=reserve_time,
        trading_time=trading_time,
        giving_time=giving_time
    )
    game_server_server_socketio_server.register_namespace(game_server)
    return {'game_server_id': game_server.game_server_id}


game_server_server = ASGIApp(
    socketio_server=game_server_server_socketio_server,
    other_asgi_app=game_server_server_game_browser_endpoint
)
