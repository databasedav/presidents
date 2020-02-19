import asyncio
from asyncio import sleep, create_task
import aioredis


def spawn_after(seconds, function, *args, **kwargs):
    """
    Calls function with args and kwargs after seconds.
    Runs in background.
    Function must be a coroutine function.
    Returns task object which can be cancelled, waited for, etc.
    Named after Eventlet function https://eventlet.net/doc/modules/greenthread.html#eventlet.greenthread.spawn_after.
    """
    async def task():
        await sleep(seconds)
        await function(*args, **kwargs)

    return create_task(task())


class NoopTimer:
    """
    For games with no time limits.
    """
    @classmethod
    def timer(cls, *args, **kwargs):
        return cls()

    def cancel(self):
        pass


async def get_redis(host: str, timeout: float = 120):
    """
    blocks until connected to redis
    """
    return (await asyncio.wait({create_task(aioredis.create_redis_pool(f"redis://{host}", timeout=timeout))}))[0].pop().result()
