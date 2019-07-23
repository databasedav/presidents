import asyncio
import uvloop
import uvicorn
import pytest
from starlette.testclient import TestClient
from ..main import app
from ..server import ServerBrowser
from fastapi import FastAPI
from socketio import AsyncServer, AsyncClient, ASGIApp
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
import subprocess

HOST = '127.0.0.1'
PORT = 5000

app = FastAPI(debug=True)

sio = AsyncServer(async_mode="asgi", logger=True)
server_browser = ServerBrowser("us-west")
sio.register_namespace(server_browser)

sio_asgi_app = ASGIApp(
    socketio_server=sio, other_asgi_app=app, socketio_path="/api/socket.io"
)

# run uvicorn --host {HOST} --port {PORT} src.back.tests.test_server_browser:sio_asgi_app in a separate terminal before running these test

# @pytest.fixture(autouse=True)
# def start_server():
#     commands = f'''
#         source /Users/asen/.local/share/virtualenvs/presidents-x8_rcTp8/bin/activate
#         uvicorn --host {HOST} --port {PORT} src.back.tests.test_server_browser:sio_asgi_app
#     '''
#     subprocess.Popen('/bin/bash').communicate(commands)


@pytest.mark.asyncio
async def test_on_add_server():
    client = AsyncClient(logger=True)
    await client.connect(f'http://{HOST}:{PORT}', namespaces=['/server_browser=us-west'])
    await client.emit('add_server', {'name': 'test'}, '/server_browser=us-west')
    assert server_browser._server_dict.values()[0].name == 'test'
