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
        # await asyncio.sleep(1)
        await asyncio.gather(
            *[add_bot_to_server(str(server_id), client) for client in range(4)]
        )

    async def add_bot_to_server(server_id, client):
        bot_id = client_bot_farm.build_a_bot_workshop(server_id, client)
        await client_bot_farm.bot_join_server(bot_id)
        await asyncio.sleep(1)

    await asyncio.gather(
        *[add_server_and_populate(server_id) for server_id in range(500)]
    )
    # await add_server_and_populate(1)
    await asyncio.sleep(100000000)



if __name__ == "__main__":
    asyncio.run(main())

# Traceback (most recent call last):
#   File "/home/avi/presidents/src/back/utils/utils.py", line 13, in task
#     await callback(*args, **kwargs)
#   File "/home/avi/presidents/src/back/game/emitting_game.py", line 185, in _handle_timeout
#     await self._auto_play_or_pass(spot)
#   File "/home/avi/presidents/src/back/game/emitting_game.py", line 231, in _auto_play_or_pass
#     await self.maybe_play_current_hand(sid, datetime.utcnow())
#   File "/home/avi/presidents/src/back/game/emitting_game.py", line 379, in maybe_play_current_hand
#     spot, sid=sid, timestamp=timestamp
#   File "/home/avi/presidents/src/back/game/emitting_game.py", line 404, in _maybe_play_current_hand_helper
#     await self._play_current_hand(spot, **kwargs)
#   File "/home/avi/presidents/src/back/game/emitting_game.py", line 407, in _play_current_hand
#     await self._play_current_hand_helper(spot, handle_post=False, **kwargs)
#   File "/home/avi/presidents/src/back/game/emitting_game.py", line 437, in _play_current_hand_helper
#     await self._set_hand_in_play(hand)
#   File "/home/avi/presidents/src/back/game/emitting_game.py", line 737, in _set_hand_in_play
#     raise Exception('hand is empty or invalid wtf ???')  # TODO
# Exception: hand is empty or invalid wtf ???

