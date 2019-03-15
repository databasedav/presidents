from . import Room
from ..game.components import EmittingGame

from typing import Dict, List
import uuid

from flask import request
from flask_socketio import SocketIO, Namespace, emit
import random

# TODO: add "copy room id" button so ppl can text their frens the rid
# TODO: add space where you can enter a room id and join
# TODO: add pre-game chat room that also has "copy room id" button


class RoomBrowser(Namespace):

    def __init__(self, rbid: str):
        super().__init__(f'/room_browser-{rbid}')
        # dict from rid (room namespace uuid) to Room object
        self._room_dict: Dict[int, Room] = dict()

    def on_connect(self):
        print(f'{request.sid} connected')

    def _room_list(self) -> List:
        return [{'rid': rid, 'room': room.name, 'num_players': room.game.num_players if room.game else 0} for rid, room in self._room_dict.items()]

    # allows multiple rooms with the same name
    def _add_room(self, name: str):
        rid: str = str(uuid.uuid4())
        room: Room = Room(rid, name)
        self._room_dict[rid] = room
        self.socketio.on_namespace(room)
        try:
            self._refresh()
        except AttributeError:  # nobody has entered the room browser
            pass

    def on_add_room(self, payload):
        self._add_room(payload['name'])

    def _join_room(self, sid: str, rid: str, name: str):
        assert rid in self._room_dict
        self._room_dict[rid].join(this.namespace, sid, name)

    def on_join_room(self, payload):
        self._join_room(request.sid, payload['rid'], payload['name'])

    def on_refresh(self) -> None:
        self._refresh()

    def _refresh(self):
        self.emit('refresh', {'rooms': self._room_list()})
