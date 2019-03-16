from ..game.components import EmittingGame

from flask import request
from flask_socketio import Namespace
from typing import Optional


class Room(Namespace):
    """
    a Room is a server that listens to the people who are inside it
    """

    def __init__(self, rid: str, name: str,
                 game: Optional[EmittingGame]=None) -> None:
        super().__init__(f'/room-{rid}')
        self.name: str = name
        self.game: Optional[EmittingGame] = game

    def _set_game(self, game: EmittingGame) -> None:
        self.game = game

    def join(self, rbnsp: str, sid: str, name: str) -> None:
        if not self.game:
            self._set_game(EmittingGame(self.socketio, self.namespace))
        elif self.game.is_full:
            self.emit('room_full', namespace=rbnsp, room=sid)
            return
        self.emit('send_to_room', {'rnsp': self.namespace}, namespace=rbnsp, room=sid)
        self.game.add_player(sid, name)

    def on_card_click(self, payload) -> None:
        self.game.add_or_remove_card(request.sid, payload['card'])

    def on_unlock(self) -> None:
        self.game.unlock_handler(request.sid)

    def on_lock(self) -> None:
        self.game.lock_handler(request.sid)

    def on_play(self) -> None:
        self.game.maybe_play_current_hand(request.sid)

    def on_unlock_pass(self) -> None:
        self.game.maybe_unlock_pass_turn(request.sid)

    def on_pass_turn(self) -> None:
        self.game.maybe_pass_turn(request.sid)

    def on_select_asking_option(self, payload) -> None:
        self.game.set_selected_asking_option(request.sid, payload['value'])

    def on_ask(self) -> None:
        self.game.ask_for_card(request.sid)

    def on_give(self) -> None:
        self.game.give_card(request.sid)
