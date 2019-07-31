from fastapi import FastAPI
from socketio import AsyncServer, ASGIApp
from ..server.server_browser import ServerBrowser
import uvicorn
from ..utils import main



app = FastAPI(debug=True)

sio = AsyncServer(async_mode="asgi", logger=True, ping_timeout=1000, ping_interval=5)
server_browser = ServerBrowser("us-west")
sio.register_namespace(server_browser)

sio_asgi_app = ASGIApp(socketio_server=sio, other_asgi_app=app)

@main
def run():
    uvicorn.run(sio_asgi_app, host="127.0.0.1", port=5000)
