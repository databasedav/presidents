from fastapi import FastAPI
from socketio import AsyncServer, ASGIApp, AsyncRedisManager
from uvicorn import Uvicorn
from faust import App as Faust
from ..data.stream import FaustfulAsyncServer
from ..server import ServerBrowser
from ..utils import AsyncTimer
import asyncio
from functools import partial


def create_app(*, debug=False, **kwargs):
    fastapi_app = FastAPI(debug=debug)

    asgi_app = ASGIApp(socketio_server=None, other_asgi_app=fastapi_app)

    uvicorn = Uvicorn(
        asgi_app, host="127.0.0.1", port=5000, reload=debug
    )  # , loop='asyncio')

    faust_app = Faust(
        "presidents-app", broker="aiokafka://localhost:9092", loop=uvicorn.loop
    )

    @fastapi_app.on_event("startup")
    def start_faust_app():
        asyncio.ensure_future(faust_app.start(), loop=uvicorn.loop)

    sio = FaustfulAsyncServer(
        uvicorn.loop,
        faust_app,
        async_mode="asgi",
        logger=debug,
        client_manager=AsyncRedisManager('redis://')
    )

    # TODO: socket connection should be opened right after login
    #       actually eventually the home page will have a lot more shit
    #       so the socket connection would be opened immediately
    @sio.on("connect")
    def on_connect(sid, payload) -> None:
        ...

    server_browser = ServerBrowser("us-west")
    sio.register_namespace(server_browser)
    server_browser.add_server('test', timer=partial(AsyncTimer.spawn_after, loop=uvicorn.loop), turn_time=kwargs.get('turn_time'), reserve_time=kwargs.get('reserve_time'))
    asgi_app.engineio_server = sio

    return uvicorn
