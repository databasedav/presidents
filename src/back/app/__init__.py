# from .server import ServerBrowser

# from flask import Flask, Blueprint
# from flask_socketio import SocketIO
# import uuid


# main = Blueprint('main', __name__)
# socketio = SocketIO(logger=True)

# # uses global namespace (/) now but this could be customized if I want
# # to have multiple server browsers
# server_browser = ServerBrowser('US-West')
# socketio.on_namespace(server_browser)

# for name in ['hello', 'world']:
#     server_browser._add_server(name)


# def create_app(*, debug=False):
#     app = Flask(__name__)
#     app.debug = debug
#     app.config['SECRET_KEY'] = 'secret'
#     app.register_blueprint(main)
#     socketio.init_app(app)
#     return app

from fastapi import FastAPI
from socketio import AsyncServer, ASGIApp
from uvicorn import Uvicorn
from faust import App as Faust
from ..data.stream import FaustfulAsyncServer
from ..server import ServerBrowser


def create_app(*, debug=False):
    fastapi_app = FastAPI(debug=debug)

    asgi_app = ASGIApp(socketio_server=None, other_asgi_app=fastapi_app)

    uvicorn = Uvicorn(asgi_app, host="127.0.0.1", port=5000)

    faust_app = Faust(
        "presidents-app",
        broker="kafka://localhost:9092",
        loop=uvicorn.get_event_loop(),
    )

    sio = FaustfulAsyncServer(
        faust_app,
        async_mode="asgi",
        logger=True,
        ping_timeout=1000,
        ping_interval=5,
    )
    server_browser = ServerBrowser("us-west")
    sio.register_namespace(server_browser)
    asgi_app.engineio_server = sio

    return uvicorn
