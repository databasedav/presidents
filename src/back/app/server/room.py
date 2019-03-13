from ..game.components import EmittingGame

from flask import request
from flask_socketio import SocketIO, Namespace, join_room, leave_room, close_room
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

    # must explicitly set new game if want
    def _set_game(self, game: EmittingGame):
        self.game = game


    def join(self, sid: str, name: str) -> None:
        if not self.game:
            self._set_game(EmittingGame(self.server, self.namespace))
        else:
            self.emit('join_room', room=sid)


            
    # TODO: joining room should just add you as a spectator
    @property
    def is_full(self) -> bool:
        try:
            return self.game.is_full
        except AttributeError:  # no game has been added yet
            return False

    def on_card_click(self, payload) -> None:
        self.game.add_or_remove_card(request.sid, payload['card'])

    def on_unlock(self) -> None:
        print('wut')
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
