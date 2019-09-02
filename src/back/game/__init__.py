import inspect
import re
import os
import textwrap
import importlib

from .hand import (
    Hand,
    DuplicateCardError,
    FullHandError,
    CardNotInHandError,
    NotPlayableOnError,
)
from .chamber import Chamber, HandNode, HandPointerNode, CardNotInChamberError
from .emitting_chamber import EmittingChamber
from .game import Game, PresidentsError, base_hand
from .emitting_game import EmittingGame

__all__ = ["Hand", "Chamber", "EmittingChamber", "Game", "EmittingGame"]

ASYNCED_COPY_PASTE_METHODS = [
    "add_player",
    "_start_round",
    "_pause_timers",
    "_handle_playing_timeout",
    "_handle_giving_timeout",
    "_handle_trading_timeout",
    "_auto_play_or_pass",
    "_auto_give",
    "_auto_trade",
    "add_or_remove_card",
    "maybe_unlock_play",
    "maybe_play_current_hand",
    "_post_play_handler",
    "maybe_unlock_pass_turn",
    "maybe_pass_turn",
    "_post_pass_handler",
    "maybe_set_selected_asking_option",
    "maybe_unlock_ask",
    "ask_for_card",
    "maybe_unlock_give",
    "give_card",
    "_set_president",
    "_set_vice_president",
    "_set_vice_asshole",
    "_set_asshole",
    "_add_to_already_asked",
]
ASYNCED_COPY_PASTE_METHODS_FILE = 'asynced_copy_paste_methods.py'
ASYNCED_COPY_PASTE_METHODS_FILE_PATH = f"{os.path.dirname(os.path.abspath(__file__))}/{ASYNCED_COPY_PASTE_METHODS_FILE}"
# go through the list of methods that need to be asynced copy pasted;
# for all instances of f'self.{method}(' where method is overwritten
# with additional async logic in EmittingGame, prepend 'await' to the
# method call and dynamically add the method to EmittingGame
# TODO: add comments to the below

get_async_method_names = lambda _class: [
    method_tuple[0]
    for method_tuple in filter(
        lambda method_tuple: inspect.iscoroutinefunction(method_tuple[1]),
        dict(_class.__dict__).items(),
    )
]

patterns = [
    re.compile(rf"self.{method}\(")
    for method in get_async_method_names(EmittingGame)
    + ASYNCED_COPY_PASTE_METHODS
] + [
    re.compile(rf"[a-z_]*chamber.{method}\(")
    for method in get_async_method_names(EmittingChamber)
]

# reset
open(ASYNCED_COPY_PASTE_METHODS_FILE_PATH, "w").close()
with open(ASYNCED_COPY_PASTE_METHODS_FILE_PATH, "a") as file:
    print('''from typing import List, Iterable, Union
from datetime import datetime

from .utils import rank_articler
from .game import base_hand, PresidentsError
from .chamber import Chamber, CardNotInChamberError
from .hand import Hand, DuplicateCardError, FullHandError, NotPlayableOnError
    ''', file=file)

for method in ASYNCED_COPY_PASTE_METHODS:
    method_str = inspect.getsource(eval(f"Game.{method}")).lstrip()
    method_str = "    async " + method_str
    # prepend await to all async overwritten methods
    for pattern in patterns:
        match = pattern.search(method_str)
        if match:
            method_str = (
                pattern.sub(f"await {match.group(0)}", method_str)
                .replace("\\", "")
                .replace("lambda: await", "lambda:")
            )
    with open(ASYNCED_COPY_PASTE_METHODS_FILE_PATH, "a") as file:
        print(textwrap.dedent(method_str), file=file)

importlib.invalidate_caches()
a = importlib.import_module('.' + ASYNCED_COPY_PASTE_METHODS_FILE[:-3], 'src.back.game')

for method in ASYNCED_COPY_PASTE_METHODS:
    setattr(EmittingGame, method, eval(f'a.{method}'))
