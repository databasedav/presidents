# from fastapi import FastAPI, HTTPException
# from typing import List
# import aioredis
# import asyncio
# from uuid import uuid4
# from secrets import token_urlsafe
# from time import time
# import socketio
# import uvicorn

# from ..models import GameServer
# from ...utils import main


# game_browser = FastAPI()

# game_server_client = socketio.AsyncClient()


# @game_browser.on_event("startup")
# async def on_startup():
#     await game_server_client.connect("http://game_server:8000")


# # TODO: requires auth
# @game_browser.post("/create_game")
# async def add_game(
#     name: str,
#     turn_time: float = None,
#     reserve_time: float = None,
#     trading_time: float = None,
#     giving_time: float = None,
# ):
#     params = {"name": name}
#     for param_str, param in zip(
#         ["turn_time", "reserve_time", "trading_time", "giving_time"],
#         [turn_time, reserve_time, trading_time, giving_time],
#     ):
#         if param:
#             params[param_str] = param
#     await game_server_client.emit("add_game", params)
#     return
#     # assert response.status == 201
#     # # this is for the frontend to auto join a game on adding it
#     # return await response.json()  # {'game_id': game_id}


# # TODO: requires auth
# @game_browser.get("/game_servers")
# async def game_servers():
#     ...


# # @main
# # def run():
# #     uvicorn.run(game_browser, host="127.0.0.1", port=5001)
