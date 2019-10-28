from ..game import EmittingGame

# from ..data.stream.agents import game_click_agent
from ..data.stream.records import GameClick

from socketio import AsyncNamespace

from typing import Optional, Dict, Callable, Union
from itertools import cycle
from datetime import datetime
import asyncio
from time import time


import logging

logger = logging.getLogger(__name__)


class Server(AsyncNamespace):
    """
    a Server is a server that listens to the people who are inside it

    one game per server for now

    server namespace is f'/server={server_id}'
    """

    def __init__(
        self,
        server_id: str,
        name: str,
        *,
        game: EmittingGame = None,
        timer: Callable = None,
        turn_time: Union[int, float] = None,
        reserve_time: Union[int, float] = None,
    ) -> None:
        """
        Provided timer, turn time, and reserve time overwrites game's if
        given.
        """
        super().__init__(namespace=f"/server={server_id}")
        self.name: str = name
        self.game: EmittingGame = game
        if game:
            game._timer = timer
            game._turn_time = turn_time
            game._reserve_time = reserve_time
        self._timer = timer
        self._turn_time = turn_time
        self._reserve_time = reserve_time

    def is_full(self) -> None:
        return self.game.is_full if self.game else False

    def _set_game(self, game: EmittingGame) -> None:
        self.game = game

    async def add_player(self, sid: str, user_id: str, name: str) -> None:
        if not self.game:
            self._set_game(
                EmittingGame(
                    self,
                    timer=self._timer,
                    turn_time=self._turn_time,
                    reserve_time=self._reserve_time,
                )
            )
        await self.game.add_player(sid=sid, user_id=user_id, name=name)

    def add_spectator(self):
        ...

    async def on_card_click(self, sid: str, payload: Dict) -> None:
        timestamp: float = time() * 10 ** 6  # seconds to microseconds
        card: int = payload["card"]
        await asyncio.gather(
            self.game.add_or_remove_card_handler(sid, card),
            self.cast_gameclick(sid, timestamp, str(card))
        )

    async def on_unlock(self, sid) -> None:
        timestamp: float = time() * 10 ** 6  # seconds to microseconds
        await asyncio.gather(
            self.game.unlock_handler(sid),
            self.cast_gameclick(sid, timestamp, 'unlock')
        )

    async def on_lock(self, sid) -> None:
        timestamp: float = time() * 10 ** 6  # seconds to microseconds
        await asyncio.gather(
            self.game.lock_handler(sid),
            self.cast_gameclick(sid, timestamp, 'lock')
        )

    async def on_play(self, sid) -> None:
        timestamp: float = time()
        await asyncio.gather(
            self.game.maybe_play_current_hand_handler(sid, timestamp),
            self.cast_gameclick(sid, timestamp, 'play')
        )

    async def on_unlock_pass_turn(self, sid) -> None:
        timestamp: float = time()
        await asyncio.gather(
            self.game.maybe_unlock_pass_turn_handler(sid),
            self.cast_gameclick(sid, timestamp, 'unlock pass')
        )

    async def on_pass_turn(self, sid) -> None:
        timestamp: float = time()
        await asyncio.gather(
            self.game.maybe_pass_turn_handler(sid),
            self.cast_gameclick(sid, timestamp, 'pass')
        )
        
    async def on_select_asking_option(self, sid, payload) -> None:
        timestamp: float = time()
        rank: int = payload['rank']
        await asyncio.gather(
            self.game.maybe_set_selected_asking_option_handler(sid, rank),
            self.cast_gameclick(sid, timestamp, str(-rank))
        )

    async def on_ask(self, sid) -> None:
        timestamp: float = time()
        await asyncio.gather(
            self.game.ask_for_card_handler(sid),
            self.cast_gameclick(sid, timestamp, 'ask')
        )
        
    async def on_give(self, sid) -> None:
        timestamp: float = time()
        await asyncio.gather(
            self.game.give_card_handler(sid),
            self.cast_gameclick(sid, timestamp, 'give')
        )

    async def on_request_correct_state(self, sid) -> None:
        await self.game.emit_correct_state(sid)

    async def cast_gameclick(self, sid: str, timestamp: float, action: str) -> None:
        self.game_click_agent.cast(
            GameClick(
                game_id=self.game.id,
                user_id=self.game.get_user_id(sid),
                timestamp=timestamp,
                action=action,
            )
        )