from ...game import EmittingGame

# from ..data.stream import game_click_agent
# from ..data.stream.records import GameClick
from ...utils import AsyncTimer

from socketio import AsyncNamespace

from typing import Optional, Dict, Callable, Union
from itertools import cycle
from datetime import datetime
import asyncio

from uuid import uuid4


import logging

# logger = logging.getLogger(__name__)


class GameServer(AsyncNamespace):
    """
    presidents game server.
    
    Implemented as an python-socket.io for the convenience of not having
    to maintain a game sid dictionary; client events are emitted
    directly to the appropriate game server and then game with no
    additional tunneling.
    
    A game server holds exactly one game instance.

    The game server's socket.io namespace is f'/server={server_id}'.

    Game servers live on a python-socket.io AsyncServer. Each
    AsyncServer lives on its own pod and does not use the available
    message queues to coordinate events across AsyncServers as there is
    no inter game communication yet (TODO: what would this even look
    like?).
    
    TODO: orchestrate game server management, i.e. how many game servers
          live on a single AsyncServer. Current idea is to spawn a new
          pod based on cpu load and handle malicious loading via rate
          limiting; then, on creation, game servers would simply be
          assigned to the AsyncServer living on the pod with the lowest
          cpu load.
    """

    def __init__(
        self,
        name: str,
        *,
        game: EmittingGame = None,
        turn_time: float = None,
        reserve_time: float = None,
        trading_time: float = None,
        giving_time: float = None,
    ) -> None:
        """
        Provided timer related attributes overwrites game's
        corresponding attributes if given.
        """
        self.game_server_id = uuid4()
        super().__init__(namespace=f"/game_server={self.game_server_id}")
        self.name: str = name
        self.game: EmittingGame = game
        if game:
            game._turn_time = turn_time
            game._reserve_time = reserve_time
            game._trading_time = trading_time
            game._giving_time = giving_time
        self._turn_time = turn_time
        self._reserve_time = reserve_time
        self._trading_time = trading_time
        self._giving_time = giving_time
        # self._game_click_agent = self.server.agentds["game_click_agent"]

    @property
    def game_server_server(self):
        return self.server

    async def on_connect(self, sid, environ):
        # only look at keys that have not expired
        if environ["HTTP_KEY"] not in self.game_server_server.redis:
            ...
        # remove expired keys after
        # add player to game

    def is_full(self) -> bool:
        return self.game.is_full if self.game else False

    def _set_game(self, game: EmittingGame) -> None:
        self.game = game

    async def add_player(self, sid: str, user_id: str, name: str) -> None:
        if not self.game:
            self._set_game(
                EmittingGame(
                    self,
                    timer=AsyncTimer.spawn_after,
                    turn_time=self._turn_time,
                    reserve_time=self._reserve_time,
                    trading_time=self._trading_time,
                    giving_time=self._giving_time,
                )
            )
        await self.game.add_player(sid=sid, user_id=user_id, name=name)

    def add_spectator(self):
        ...

    async def on_card_click(self, sid: str, payload: Dict) -> None:
        timestamp: datetime = datetime.utcnow()
        card: int = payload["card"]
        await asyncio.gather(
            self.game.add_or_remove_card_handler(sid, card),
            # self._cast_game_click(sid, timestamp, str(card)),
        )

    async def on_unlock(self, sid) -> None:
        timestamp: datetime = datetime.utcnow()
        await asyncio.gather(
            self.game.unlock_handler(sid),
            # self.cast_game_click(sid, timestamp, "unlock"),
        )

    async def on_lock(self, sid) -> None:
        timestamp: datetime = datetime.utcnow()
        await asyncio.gather(
            self.game.lock_handler(sid),
            # self.cast_game_click(sid, timestamp, "lock"),
        )

    async def on_play(self, sid) -> None:
        timestamp: datetime = datetime.utcnow()
        await asyncio.gather(
            self.game.maybe_play_current_hand_handler(sid, timestamp),
            # self.cast_game_click(sid, timestamp, "play"),
        )

    async def on_unlock_pass_turn(self, sid) -> None:
        timestamp: datetime = datetime.utcnow()
        await asyncio.gather(
            self.game.maybe_unlock_pass_turn_handler(sid),
            # self.cast_game_click(sid, timestamp, "unlock pass"),
        )

    async def on_pass_turn(self, sid) -> None:
        timestamp: datetime = datetime.utcnow()
        await asyncio.gather(
            self.game.maybe_pass_turn_handler(sid),
            # self.cast_game_click(sid, timestamp, "pass"),
        )

    async def on_select_asking_option(self, sid, payload) -> None:
        timestamp: datetime = datetime.utcnow()
        rank: int = payload["rank"]
        await asyncio.gather(
            self.game.maybe_set_selected_asking_option_handler(sid, rank),
            # self.cast_game_click(sid, timestamp, str(-rank)),
        )

    async def on_ask(self, sid) -> None:
        timestamp: datetime = datetime.utcnow()
        await asyncio.gather(
            self.game.ask_for_card_handler(sid),
            # self.cast_game_click(sid, timestamp, "ask"),
        )

    async def on_give(self, sid) -> None:
        timestamp: datetime = datetime.utcnow()
        await asyncio.gather(
            self.game.give_card_handler(sid),
            # self.cast_game_click(sid, timestamp, "give"),
        )

    async def on_request_correct_state(self, sid) -> None:
        await self.game.emit_correct_state(sid)

    async def _cast_game_click(
        self, sid: str, timestamp: datetime, action: str
    ) -> None:
        await game_click_agent.cast(
            GameClick(
                game_id=uuid4(),
                user_id=uuid4(),
                timestamp=timestamp,
                action=action,
            )
        )
        # self._game_click_agent.cast(
        #     GameClick(
        #         game_id=self.game.id,
        #         user_id=self.game.get_user_id(sid),
        #         timestamp=timestamp,
        #         action=action,
        #     )
        # )
