from typing import Dict, List
import aiohttp
import fastapi
import logging
from asyncio import gather, sleep
from socketio import AsyncClient
from ...game import Chamber, Hand
from itertools import combinations
from ..secrets import BOT_KEY
import asyncio
from ..game_god import Prayer, ear
from .bot import Bot, NUM_BOT_SERVERS
from uuid import uuid4
import os


logger = logging.getLogger(__name__)

bot_farm = fastapi.FastAPI()
game_bot_dict: Dict[str, List[Bot]] = dict()

# Prayer, ear = None, None


@bot_farm.on_event("startup")
async def on_startup():
    # from ..game_god import Prayer as p, ear as e
    # global Prayer, ear
    # Prayer, ear = p, e
    await sleep(10)
    logger.info("starting bot farm")
    # wait for one to finish so agent finishes setting up
    # TODO: the agent in game server should take of this by blocking
    #       until connected, etc.
    await sleep((int(os.getenv("BOT_FARM_ORDER")) - 1) * 10)
    await gather(
        *[
            add_bot((await add_game())["game_id"], i)
            for i in range(1, NUM_BOT_SERVERS + 1)
        ]
    )  # hit all bot servers to start up reply consumers
    await sleep(10)  # wait for reply consumers to start up
    # for _ in range(2000):
    #     await add_game_and_populate()
    await gather(*[add_game_and_populate() for _ in range(834)])


async def add_game_and_populate():
    game_id = (await add_game())["game_id"]
    await gather(*[add_bot(game_id) for _ in range(3)])
    # num players takes a sec to update otherwise server will not start game
    # TODO: this should not be an issue
    await add_bot(game_id)


async def add_game(
    *,
    name: str = "bots",
    turn_time: float = 5,
    reserve_time: float = 2,
    trading_time: float = 1,
    giving_time: float = 1,
):
    logger.info("bot farm prays for game creation")
    game_id = str(uuid4())
    game_dict = await ear.ask(
        key=game_id,
        value=Prayer(
            prayer="add_game",
            prayer_kwargs={
                "game_id": game_id,
                "name": name,
                "turn_time": turn_time,
                "reserve_time": reserve_time,
                "trading_time": trading_time,
                "giving_time": giving_time,
            },
        ),
    )
    game_bot_dict[game_dict["game_id"]] = list()
    return game_dict


async def add_bot(game_id: str, bot_game_server=None):
    bot = Bot()
    await bot.connect_to_game(game_id, bot_game_server=bot_game_server)
    game_bot_dict[game_id].append(bot)
