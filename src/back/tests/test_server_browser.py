import asyncio
import uvloop
import uvicorn
import pytest
from starlette.testclient import TestClient
from ..main import app
from ..server import ServerBrowser
from ..bots.bot_farm import Client, ClientBot
from fastapi import FastAPI
from socketio import AsyncServer, AsyncClient, ASGIApp

# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
import subprocess
import os
import logging

# from .testing_server import server_browser

logging.basicConfig(level=logging.INFO)


HOST = "127.0.0.1"
PORT = 5000


# run uvicorn --host {HOST} --port {PORT} src.back.tests.test_server_browser:sio_asgi_app in a separate terminal before running these test
# source /Users/asen/.local/share/virtualenvs/presidents-x8_rcTp8/bin/activate
# @pytest.fixture(autouse=True)
# def start_server():
#     commands = f'''
#         source /home/avi/.local/share/virtualenvs/presidents-VuqWQA8n/bin/activate
#         uvicorn --host {HOST} --port {PORT} src.back.tests.test_server_browser:sio_asgi_app
#     '''
#     subprocess.Popen(commands.split())


# @pytest.mark.asyncio
# async def test_on_add_server():
#     test_passed = list()
#     client = AsyncClient(logger=True)
#     await client.connect(f'http://{HOST}:{PORT}', namespaces=['/server_browser=us-west'])
#     await client.emit('add_server', {'name': 'test'}, namespace='/server_browser=us-west', callback=lambda: test_passed.append(True))
#     await client.sleep(0.01)
#     assert test_passed[0]

#     client = ClientBot(logger=True)
#     await client.connect(f'http://{HOST}:{PORT}', namespaces=['/server_browser=us-west'])
#     assert not client.wut
#     await client.emit('test')
#     await client.sleep(0.01)
#     return client.wut

names = ["a", "b", "c", "d"]


@pytest.mark.asyncio
async def test_lil_baby_game():
    await asyncio.sleep(1.5)
    clients = [Client() for _ in range(4)]
    client_bots = [ClientBot("/server=12345") for _ in range(4)]
    for client, client_bot in zip(clients, client_bots):
        client.register_namespace(client_bot)
    await asyncio.gather(
        *[
            client.connect(
                f"http://{HOST}:{PORT}",
                namespaces=["/server_browser=us-west", "/server=12345"],
            )
            for client in clients
        ]
    )
    await asyncio.sleep(0.05)
    await clients[0].emit(
        "add_server",
        {"name": "test", "server_id": "12345"},
        namespace="/server_browser=us-west",
    )
    await asyncio.sleep(0.5)
    await asyncio.gather(
        *[
            client.emit(
                "join_server",
                {"server_id": "12345", "name": names[i]},
                namespace="/server_browser=us-west",
            )
            for i, client in enumerate(clients)
        ]
    )
    await asyncio.sleep(10000)

# if __name__ == '__main__':
#     asyncio.run(test_lil_baby_game())

# async def main():
#     res = await test_on_add_server()
#     print(res)
#     return res

# if __name__ == '__main__':
#     asyncio.run(main())

# need to decide what I am testing exactly with this

# want to make sure that when the client requests to do something, like
# adding a server or playing a hand, that those actions are carried out
# on the server side all the way down the line, for example, a game
# click command should first check that the server state was altered
# appropriately depending on the game click or the appropriate error
# raised and sent to the client and then also that now the game click
# exists in the database

# have to find a way to test the actual objects being used
