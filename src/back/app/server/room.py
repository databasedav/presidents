from ..game.components import EmittingGame
from flask_socketio import join_room, leave_room, close_room

class Room:

    def __init__(self, game: EmittingGame):
        self.rid: str = ...  # alphanumeric hash
        self.game: EmittingGame = game
        