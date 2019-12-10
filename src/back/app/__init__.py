from fastapi import FastAPI
from socketio import AsyncServer, ASGIApp, AsyncRedisManager
from uvicorn import Config, Server
from faust import App as Faust
from ..data.stream import FaustfulAsyncServer
from ..server import ServerBrowser
from ..utils import AsyncTimer
import asyncio
from functools import partial
import logging

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.ERROR)
# logger.disabled = True

def create_app(*, debug=False, **kwargs):
    fastapi_app = FastAPI(debug=debug)
    
    asgi_app = ASGIApp(socketio_server=None, other_asgi_app=fastapi_app)

    config = Config(asgi_app, host="127.0.0.1", port=5000, reload=debug, log_level='debug')
    server = Server(config=config)

    faust_app = Faust(
        "presidents-app",
        broker="aiokafka://localhost:9092",
        loop=server.get_event_loop(),
    )

    # @fastapi_app.on_event("startup")
    # def start_faust_app():
    #     asyncio.create_task(faust_app.start())

    sio = FaustfulAsyncServer(
        faust_app,
        logger=False,
        async_mode="asgi",
        # client_manager=AsyncRedisManager("redis://"),
        cors_allowed_origins=["http://127.0.0.1:8080", "http://127.0.0.1:8081"],
        ping_timeout=10000000,
    )

    # TODO: socket connection should be opened right after login
    #       actually eventually the home page will have a lot more shit
    #       so the socket connection would be opened immediately
    @sio.on("connect")
    def on_connect(sid, payload) -> None:
        ...

    asgi_app.engineio_server = sio

    return server, sio
