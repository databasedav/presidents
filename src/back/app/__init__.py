from fastapi import FastAPI
from socketio import AsyncServer, ASGIApp
from uvicorn import Uvicorn
from faust import App as Faust
from ..data.stream import FaustfulAsyncServer
from ..server import ServerBrowser
import asyncio


def create_app(*, debug=False):
    fastapi_app = FastAPI(debug=debug)

    asgi_app = ASGIApp(socketio_server=None, other_asgi_app=fastapi_app)

    uvicorn = Uvicorn(asgi_app, host="127.0.0.1", port=5000)#, loop='asyncio')

    faust_app = Faust(
        "presidents-app",
        broker="aiokafka://localhost:9092",
        loop=uvicorn.loop,
    )

    @fastapi_app.on_event('startup')
    def start_faust_app():
        asyncio.ensure_future(faust_app.start(), loop=uvicorn.loop)

    sio = FaustfulAsyncServer(
        faust_app,
        async_mode="asgi",
        # logger=True,
        # ping_timeout=1000,
        # ping_interval=5,
    )
    server_browser = ServerBrowser("us-west")
    sio.register_namespace(server_browser)
    asgi_app.engineio_server = sio

    return uvicorn
