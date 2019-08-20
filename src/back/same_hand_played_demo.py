from .bots.bot_farm import *
import asyncio


TURN_TIME = 2
RESERVE_TIME = 0


async def main():
    client_bot_farm = ClientBotFarm()
    await client_bot_farm.connect_to_server_browser(
        "127.0.0.1", 5000, "us-west"
    )
    await asyncio.sleep(1)

    async def add_server_and_populate(server_id):
        server_str = f"/server={server_id}"
        await client_bot_farm.add_server(
            server_str,
            server_id=str(server_id),
            turn_time=TURN_TIME,
            reserve_time=RESERVE_TIME,
        )
        await asyncio.sleep(1)
        await asyncio.gather(
            *[add_bot_to_server(str(server_id), client) for client in range(4)]
        )

    async def add_bot_to_server(server_id, client):
        bot_id = client_bot_farm.build_a_bot_workshop(server_id, client)
        await client_bot_farm.bot_join_server(bot_id)
        await asyncio.sleep(1)

    await asyncio.gather(
        *[add_server_and_populate(server_id) for server_id in range(1000)]
    )
    # await add_server_and_populate(1)
    await asyncio.sleep(100000000)

    # todo 4 clients isn't enough lol; let a single client handle 


if __name__ == "__main__":
    asyncio.run(main())
