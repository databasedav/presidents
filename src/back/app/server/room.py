from ..game.components import EmittingGame

from flask import request
from flask_socketio import Namespace, join_room, leave_room, close_room

class Room(Namespace):

    def __init__(self, namespace: str, game: EmittingGame) -> None:
        super().__init__(namespace)
        self.game: EmittingGame = game
        
    def on_card_click(self, payload):
        self.game
        ...