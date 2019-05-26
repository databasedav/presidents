from ..game import EmittingGame

from flask import request
from flask_socketio import Namespace
from typing import Optional


class Server(Namespace):
    """
    a Server is a server that listens to the people who are inside it
    """

    def __init__(self, server_id: str, name: str,
                 game: Optional[EmittingGame]=None) -> None:
        super().__init__(f'/server_{server_id}')
        self.name: str = name
        self.game: Optional[EmittingGame] = game

    def _set_game(self, game: EmittingGame) -> None:
        self.game = game

    def join(self, server_browser_namespace: str, sid: str, name: str) -> None:
        if not self.game:
            self._set_game(EmittingGame(self.socketio, self.namespace))
        elif self.game.is_full:
            self.emit('server_full', namespace=server_browser_namespace,
                      room=sid)
            return
        self.emit('send_to_server', {'server_namespace': self.namespace},
                  namespace=server_browser_namespace, room=sid)
        self.game.add_player(sid, name)
        if self.game.num_players == 1:
            self.game._start_round(testing=True)  # TODO

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
