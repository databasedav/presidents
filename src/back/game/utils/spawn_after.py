import asyncio
from typing import Callable

# from aiojobs import Scheduler, create_scheduler


# class SpawnAfter:
#     @classmethod
#     async def create(self, seconds: int, function: Callable, *args, **kwargs):
#         self = SpawnAfter()
#         self.scheduler = await create_scheduler()

#         async def coro():
#             await asyncio.sleep(seconds)
#             function(*args, **kwargs)

#         await self.scheduler.spawn(coro())
#         return self

#     async def cancel(self):
#         await self.scheduler.close()
