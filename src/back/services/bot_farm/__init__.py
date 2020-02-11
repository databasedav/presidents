from typing import Dict, List
import aiohttp
import fastapi
import logging
from asyncio import gather
from socketio import AsyncClient
from ...game import Chamber, Hand
from itertools import combinations
from ..secrets import BOT_KEY
from ..game_god import Prayer, ear
from .bot import Bot


logger = logging.getLogger(__name__)

bot_farm = fastapi.FastAPI()
game_bot_dict: Dict[str, List[Bot]] = dict()
game_server_client = None


@bot_farm.on_event("startup")
async def on_startup():
    global game_server_client
    logger.info("starting bot farm")
    # game_server_client = aiohttp.ClientSession()
    await gather(*[add_game_and_populate() for _ in range(1)])


async def add_game_and_populate():
    game_id = (await add_game())["game_id"]
    await gather(*[add_bot(game_id) for _ in range(4)])


async def add_game(
    *,
    name: str = "bots",
    turn_time: float = 1,
    reserve_time: float = 2,
    trading_time: float = 1,
    giving_time: float = 1,
):
    logger.info('bot farm prays for game creation')
    game_dict = await ear.ask(
        value=Prayer(
            prayer="add_game",
            prayer_kwargs={
                "name": name,
                "turn_time": turn_time,
                "reserve_time": reserve_time,
                "trading_time": trading_time,
                "giving_time": giving_time,
            },
        )
    )
    # async with game_server_client.post(
    #     "http://game_server/create_game",
    #     json={
    #         "name": name,
    #         "turn_time": turn_time,
    #         "reserve_time": reserve_time,
    #         "trading_time": trading_time,
    #         "giving_time": giving_time,
    #     },
    # ) as response:
    #     assert response.status == 201
    game_bot_dict[game_dict["game_id"]] = list()
    return game_dict


async def add_bot(game_id: str):
    bot = Bot()
    await bot.connect_to_game(game_id)
    game_bot_dict[game_id].append(bot)
