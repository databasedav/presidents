import inspect
import sys
import numpy as np
from itertools import accumulate, repeat, chain


card_names = [
    None,
    "3♣",
    "3♦",
    "3♥",
    "3♠",
    "4♣",
    "4♦",
    "4♥",
    "4♠",
    "5♣",
    "5♦",
    "5♥",
    "5♠",
    "6♣",
    "6♦",
    "6♥",
    "6♠",
    "7♣",
    "7♦",
    "7♥",
    "7♠",
    "8♣",
    "8♦",
    "8♥",
    "8♠",
    "9♣",
    "9♦",
    "9♥",
    "9♠",
    "10♣",
    "10♦",
    "10♥",
    "10♠",
    "j♣",
    "j♦",
    "j♥",
    "j♠",
    "q♣",
    "q♦",
    "q♥",
    "q♠",
    "k♣",
    "k♦",
    "k♥",
    "k♠",
    "a♣",
    "a♦",
    "a♥",
    "a♠",
    "2♣",
    "2♦",
    "2♥",
    "2♠",
]

id_desc_dict = {
    0: "empty hand",  # i.e. [0, 0, 0, 0, 0]
    11: "single",  # e.g. [0, 0, 0, 0, 1]
    20: "invalid hand (2)",  # e.g. [0, 0, 0, 1, 52]
    21: "double",  # e.g. [0, 0, 0, 1, 2]
    30: "invalid hand (3)",  # e.g. [0, 0, 1, 2, 52]
    31: "triple",  # e.g. [0, 0, 1, 2, 3]
    40: "invalid hand (4)",  # e.g. [0, 1, 2, 3, 4]
    50: "invalid hand (5)",  # e.g. [1, 2, 3, 5, 52]
    51: "fullhouse",  # e.g. [1, 2, 3, 51, 52]
    52: "straight",  # e.g. [1, 5, 9, 13, 17]
    53: "bomb",  # e.g. [1, 49, 50, 51, 52]
}

ranks = [
    None,
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "J",
    "Q",
    "K",
    "A",
    "2",
]


def rank_articler(value: int) -> str:
    return f'a{"n" if value in [6, 12] else ""} {ranks[value]}'


def hand_hash(hand: np.ndarray) -> int:
    return int(
        sum(
            [
                hand[i - 1] * (51 ** (5 - i))  # type: ignore
                for i in range(1, 6)
            ]
        )
    )


def cartesian_product_pp(arrays):
    """
    adapted from https://stackoverflow.com/a/49445693/9578116
    """
    la = len(arrays)
    L = *map(len, arrays), la
    arr = np.empty(L, dtype=np.uint8)
    arrs = (
        *accumulate(chain((arr,), repeat(0, la - 1)), np.ndarray.__getitem__),
    )
    idx = slice(None), *repeat(None, la - 1)
    for i in range(la - 1, 0, -1):
        arrs[i][..., i] = arrays[i][idx[: la - i]]
        arrs[i - 1][1:] = arrs[i]
    arr[..., 0] = arrays[0][idx]
    return arr.reshape(-1, la)


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
