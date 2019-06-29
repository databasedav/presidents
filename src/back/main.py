from fastapi import FastAPI
from typing import Dict
import socketio
import logging
from app.server import ServerBrowser
import uvicorn


logger = logging.getLogger(__name__)


app = FastAPI(debug=True)
sio = socketio.AsyncServer(async_mode="asgi")
sio_asgi_app = socketio.ASGIApp(
    socketio_server=sio, other_asgi_app=app, socketio_path="/socket.io"
)


server_browser = ServerBrowser("US-West")
sio.register_namespace(server_browser)
for name in ["hello"]:
    server_browser.add_server(name, server_id="test")


@app.get("/")
async def read_root() -> Dict[str, str]:
    return {"hello": "world"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None) -> Dict[str, str]:
    return {"item_id": item_id, "q": q}


if __name__ == "__main__":
    uvicorn.run(sio_asgi_app, host="127.0.0.1", port=5000)
