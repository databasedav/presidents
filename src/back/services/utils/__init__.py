from asyncio import sleep, create_task


class AsyncTimer:
    @classmethod
    def spawn_after(cls, seconds, callback, *args, **kwargs):
        """
        Calls callback with args and kwargs after seconds.
        """

        async def task():
            await sleep(seconds)
            await callback(*args, **kwargs)

        return create_task(task())


# maps int action to tuple with str action and kwargs
GAME_ACTION_DICT = {
    -22: ("ask", {}),
    -21: ("card", {}),
    -20: ("give", {}),
    -19: ("lock", {}),
    -18: ("pass", {}),
    -17: ("play", {}),
    -16: ("rank", {}),
    -15: ("unlock", {}),
    -14: ("unlock_pass", {}),
    -13: ("rank", {"rank": 13}),
    -12: ("rank", {"rank": 12}),
    -11: ("rank", {"rank": 11}),
    -10: ("rank", {"rank": 10}),
    -9: ("rank", {"rank": 9}),
    -8: ("rank", {"rank": 8}),
    -7: ("rank", {"rank": 7}),
    -6: ("rank", {"rank": 6}),
    -5: ("rank", {"rank": 5}),
    -4: ("rank", {"rank": 4}),
    -3: ("rank", {"rank": 3}),
    -2: ("rank", {"rank": 2}),
    -1: ("rank", {"rank": 1}),
    1: ("card", {"card": 1}),
    2: ("card", {"card": 2}),
    3: ("card", {"card": 3}),
    4: ("card", {"card": 4}),
    5: ("card", {"card": 5}),
    6: ("card", {"card": 6}),
    7: ("card", {"card": 7}),
    8: ("card", {"card": 8}),
    9: ("card", {"card": 9}),
    10: ("card", {"card": 10}),
    11: ("card", {"card": 11}),
    12: ("card", {"card": 12}),
    13: ("card", {"card": 13}),
    14: ("card", {"card": 14}),
    15: ("card", {"card": 15}),
    16: ("card", {"card": 16}),
    17: ("card", {"card": 17}),
    18: ("card", {"card": 18}),
    19: ("card", {"card": 19}),
    20: ("card", {"card": 20}),
    21: ("card", {"card": 21}),
    22: ("card", {"card": 22}),
    23: ("card", {"card": 23}),
    24: ("card", {"card": 24}),
    25: ("card", {"card": 25}),
    26: ("card", {"card": 26}),
    27: ("card", {"card": 27}),
    28: ("card", {"card": 28}),
    29: ("card", {"card": 29}),
    30: ("card", {"card": 30}),
    31: ("card", {"card": 31}),
    32: ("card", {"card": 32}),
    33: ("card", {"card": 33}),
    34: ("card", {"card": 34}),
    35: ("card", {"card": 35}),
    36: ("card", {"card": 36}),
    37: ("card", {"card": 37}),
    38: ("card", {"card": 38}),
    39: ("card", {"card": 39}),
    40: ("card", {"card": 40}),
    41: ("card", {"card": 41}),
    42: ("card", {"card": 42}),
    43: ("card", {"card": 43}),
    44: ("card", {"card": 44}),
    45: ("card", {"card": 45}),
    46: ("card", {"card": 46}),
    47: ("card", {"card": 47}),
    48: ("card", {"card": 48}),
    49: ("card", {"card": 49}),
    50: ("card", {"card": 50}),
    51: ("card", {"card": 51}),
    52: ("card", {"card": 52}),
}
