from ..game import EmittingGame
from ..data.stream.agents import game_click_agent
from ..data.stream.agents import GameClick

from socketio import AsyncNamespace

from typing import Optional, Dict
from itertools import cycle
from datetime import datetime

names = cycle(["aa", "bb", "cc", "dd"])


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

    def _set_game(self, game: EmittingGame) -> None:
        self.game = game

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
        await self.emit(
            "send_to_server",
            {"server_namespace": self.namespace},
            namespace=server_browser_namespace,
            room=sid,
        )
        assert self.game is not None
        self.game.add_player(sid, name)
        if self.game.num_players == 4:
            self.game._start_round(
                deck=[
                    range(lower, upper)
                    for lower, upper in zip(
                        range(1, 53, 13), range(14, 54, 13)
                    )
                ]
            )

    def on_connect(self, sid, payload):
        self.test_join(
            server_browser_namespace=self.namespace, sid=sid, name=next(names)
        )

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
        self.game.add_or_remove_card(sid, payload["card"])
        await game_click_agent.send(
            GameClick(
                game_id=self.game.id,
                user_id=self.game.get_user_id(sid),
                timestamp=timestamp,
                action=payload["card"],
            )
        )

    def on_unlock(self, sid) -> None:
        assert self.game is not None
        self.game.unlock_handler(sid)

    def on_lock(self, sid) -> None:
        assert self.game is not None
        self.game.lock_handler(sid)

    def on_play(self, sid) -> None:
        timestamp: datetime.datetime = datetime.utcnow()
        assert self.game is not None
        self.game.maybe_play_current_hand(sid, timestamp)

    def on_unlock_pass(self, sid) -> None:
        assert self.game is not None
        self.game.maybe_unlock_pass_turn(sid)

    def on_pass_turn(self, sid) -> None:
        assert self.game is not None
        self.game.maybe_pass_turn(sid)

    def on_select_asking_option(self, sid, payload) -> None:
        assert self.game is not None
        self.game.set_selected_asking_option(sid, payload["value"])

    def on_ask(self, sid) -> None:
        assert self.game is not None
        self.game.ask_for_card(sid)

    def on_give(self, sid) -> None:
        assert self.game is not None
        self.game.give_card(sid)
