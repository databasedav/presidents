from . import Server

from typing import Dict, List
import uuid

from flask import request
from flask_socketio import Namespace

# TODO: add "copy server id" button so ppl can text their frens the rid
# TODO: add space where you can enter a server id and join
# TODO: add pre-game chat server that also has "copy server id" button


class ServerBrowser(Namespace):

    def __init__(self, server_browser_id: str):
        super().__init__(f'/server_browser_{server_browser_id}')
        self._server_dict: Dict[str, Server] = dict()

    def on_connect(self):
        print(f'{request.sid} connected')

    def _server_list(self) -> List:
        return [{
            'server_id': server_id,
            'name': server.name,
            'num_players': server.game.num_players if server.game else 0
        } for server_id, server in self._server_dict.items()]

    def on_add_server(self, payload):
        self._add_server(payload['name'])

    # allows multiple servers with the same name
    def _add_server(self, name: str):
        server_id: str = str(uuid.uuid4())
        server: Server = Server(server_id, name)
        self._server_dict[server_id] = server
        self.socketio.on_namespace(server)
        try:
            self._refresh()
        except AttributeError:  # nobody has entered the server browser
            pass

    def on_join_server(self, payload):
        self._join_server(request.sid, payload['server_id'], payload['name'])

    def _join_server(self, sid: str, server_id: str, name: str):
        assert server_id in self._server_dict
        self._server_dict[server_id].join(self.namespace, sid, name)

    def on_refresh(self) -> None:
        self._refresh()

    def _refresh(self):
        self.emit('refresh', {'servers': self._server_list()}, callback=lambda: print('refreshed'))
