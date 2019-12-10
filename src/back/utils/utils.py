import inspect
import sys
import asyncio
from typing import Callable


class NoopTimer:
    """
    For games with no time limits.
    """

    @classmethod
    def timer(cls, time: int, func: Callable, *args, **kwargs):
        return cls()

    def cancel(self):
        pass


class AsyncTimer:
    @classmethod
    def spawn_after(
        self, seconds, callback, *args, **kwargs
    ):  # loop=None, **kwargs):
        """
        Calls callback with args and kwargs after seconds.
        """

        async def task():
            await asyncio.sleep(seconds)
            await callback(*args, **kwargs)

        return asyncio.create_task(task())


def main(fn):
    """
    source: ucb.py found in any of the python project starter files from
            cs61a.org

    Call fn with command line arguments.  Used as a decorator.

    The main decorator marks the function that starts a program. For
    example,

    @main
    def my_run_function():
        # function body

    Use this instead of the typical __name__ == "__main__" predicate.
    """
    if inspect.stack()[1][0].f_locals["__name__"] == "__main__":
        args = sys.argv[1:]  # Discard the script name from command line
        fn(*args)  # Call the main function
    return fn
