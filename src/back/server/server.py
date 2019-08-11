from ..game import EmittingGame

# from ..data.stream.agents import game_click_agent
from ..data.stream.records import GameClick

from socketio import AsyncNamespace

from typing import Optional, Dict
from itertools import cycle
from datetime import datetime


import logging

logger = logging.getLogger(__name__)


class Server(AsyncNamespace):
    """
    a Server is a server that listens to the people who are inside it

    one game per server for now

    server namespace is 'server_' + server_id
    """

    def __init__(
        self, server_id: str, name: str, game: Optional[EmittingGame] = None
    ) -> None:
        super().__init__(namespace=f"/server={server_id}")
        self.name: str = name
        self.game: Optional[EmittingGame] = game
    
    def is_full(self) -> None:
        return self.game.is_full if self.game else False

    def _set_game(self, game: EmittingGame) -> None:
        self.game = game
    
    def add_player(self):
        if not self.game:
            self._set_game(EmittingGame(self))
        await self.game.add_player(sid, user_id, name)

    def add_spectator(self):
        ...

    async def join(
        self, server_browser_namespace: str, sid: str, name: str
    ) -> None:
        if not self.game:
            self._set_game(EmittingGame(self))
        elif self.game.is_full:
            await self.emit(
                "server_full", namespace=server_browser_namespace, room=sid
            )
            return
        # await self.emit(
        #     "send_to_server",
        #     {"server_namespace": self.namespace},
        #     namespace=server_browser_namespace,
        #     room=sid,
        # )
        await self.game.add_player(sid, name)
        # TODO: this shouldn't be here
        if self.game.num_players == 4:
            await self.game._start_round(
                deck=[
                    range(lower, upper)
                    for lower, upper in zip(
                        range(1, 53, 13), range(14, 54, 13)
                    )
                ]
            )

    # def on_connect(self, sid, payload):
    #     self.test_join(
    #         server_browser_namespace=self.namespace, sid=sid, name=next(names)
    #     )

    def test_join(
        self, server_browser_namespace: str, sid: str, name: str
    ) -> None:
        if not self.game:
            self._set_game(EmittingGame(self.server, self.namespace))
        # elif self.game.is_full:
        #     await self.emit('server_full', namespace=server_browser_namespace,
        #               room=sid)
        #     return
        # await self.emit('send_to_server', {'server_namespace': self.namespace},
        #           namespace=server_browser_namespace, room=sid)
        assert self.game is not None
        self.game.add_player(sid, name)
        if self.game.num_players == 4:
            self.game._start_round(testing=True)  # TODO

    async def on_card_click(self, sid: str, payload: Dict) -> None:
        timestamp: datetime.datetime = datetime.utcnow()
        assert self.game is not None
        await self.game.add_or_remove_card(sid, payload["card"])
        # await game_click_agent.send(
        #     GameClick(
        #         game_id=self.game.id,
        #         user_id=self.game.get_user_id(sid),
        #         timestamp=timestamp,
        #         action=payload["card"],
        #     )
        # )

    async def on_unlock(self, sid) -> None:
        assert self.game is not None
        await self.game.unlock_handler(sid)

    def on_lock(self, sid) -> None:
        assert self.game is not None
        self.game.lock_handler(sid)

    async def on_play(self, sid) -> None:
        timestamp: datetime.datetime = datetime.utcnow()
        assert self.game is not None
        await self.game.maybe_play_current_hand(sid, timestamp)

    async def on_unlock_pass(self, sid) -> None:
        assert self.game is not None
        await self.game.maybe_unlock_pass_turn(sid)

    async def on_pass_turn(self, sid) -> None:
        assert self.game is not None
        await self.game.maybe_pass_turn(sid)

    async def on_select_asking_option(self, sid, payload) -> None:
        assert self.game is not None
        await self.game.set_selected_asking_option(sid, payload["value"])

    async def on_ask(self, sid) -> None:
        assert self.game is not None
        await self.game.ask_for_card(sid)

    async def on_give(self, sid) -> None:
        assert self.game is not None
        await self.game.give_card(sid)
