from . import Room
from ..game.components import EmittingGame

from typing import Dict, List
from uuid import uuid4

from flask import request
from flask_socketio import SocketIO, Namespace, emit


class RoomBrowser(Namespace):

    def __init__(self, socketio: SocketIO, namespace: str):
        super().__init__(namespace)
        self._socketio: SocketIO = socketio
        # dict from rid (room namespace hash) to Room object
        self._room_dict: Dict[str, Room] = dict()

    def on_connect(self):
        print(f'{request.sid} connected')

    def _room_list(self) -> List:
        return [{'room': room.name, 'num_players': room.game.num_players if room.game else 0} for room in self._room_dict.values()]

    # allows multiple rooms with the same name
    def _add_room(self, name: str):
        rid: str = str(uuid4())
        room: Room = Room(self._socketio, rid, name)
        self._room_dict[rid] = room
        self._socketio.on_namespace(room)
        try:
            self._refresh()
        except AttributeError:  # nobody has entered the room browser
            pass

    def on_add_room(self, payload):
        self._add_room(payload['name'])

    def _join_room(self, rid: str, sid: str, name: str):
        assert rid in self._room_dict
        room: Room = self._room_dict[rid]
        if not room.game:  # room does not have a game
            # set new game
            room.set_game(EmittingGame(self._socketio, room._namespace))
            room.game.add_player(sid, name)
            self._refresh()
        elif room.is_full:
            self._socketio.emit('room_full', namespace=self.namespace, room=sid)
        else:
            room.game.add_player(sid, name)
            self._refresh()

    def on_join_room(self, payload):
        self._join_room(payload['rid'], payload['sid'], payload['name'])

    def on_refresh(self) -> None:
        self._refresh()

    def _refresh(self):
        self._socketio.emit('refresh', {'rooms': self._room_list()},
                            namespace=self.namespace)
