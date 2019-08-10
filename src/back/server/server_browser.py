from .server import Server
from typing import Dict, List

# from flask import request
# from ..data.stream import game_click_agent, GameClick
# from asgiref.sync import sync_to_async
from socketio import AsyncNamespace

# from flask_socketio import Namespace
import uuid
import datetime

# from confluent_kafka import Producer
import json
import logging

logger = logging.getLogger(__name__)

# TODO: add "copy server id" button so ppl can text their frens the rid
# TODO: add space where you can enter a server id and join
# TODO: add pre-game chat server that also has "copy server id" button


class ServerBrowser(AsyncNamespace):
    def __init__(self, server_browser_id: str):
        super().__init__(namespace=f"/server_browser={server_browser_id}")
        self._server_dict: Dict[str, Server] = dict()

    def on_connect(self, sid, payload):
        logger.info(f"{sid} connected to {self.namespace}")

    def _server_list(self) -> List:
        return [
            {
                "server_id": server_id,
                "name": server.name,
                "num_players": server.game.num_players if server.game else 0,
            }
            for server_id, server in self._server_dict.items()
        ]

    async def on_add_server(self, sid, payload):
        self.add_server(**payload)
        # try:
        #     await self._refresh()
        # except AttributeError:  # nobody has entered the server browser
        #     pass

    # allows multiple servers with the same name (will have different server ids)
    def add_server(self, name: str, server_id: str = None):
        server_id: str = server_id or str(uuid.uuid4())
        server: Server = Server(server_id, name)
        self._server_dict[server_id] = server
        # self.server is the socket.io server
        self.server.register_namespace(server)

    async def on_join_server_as_player(self, sid, payload):
        self._join_server_as_player(sid, payload)
        await self._join_server(payload.get('client_bot_farm_sid') or sid, payload["server_id"], payload["name"])

    async def _join_server_as_player(self, sid, payload):
        ...
    
    async def _join_server_as_spectator(self, sid, payload):
        ...

    async def _join_server(self, sid: str, server_id: str, name: str):
        # TODO timeout if server isn't joined in a few seconds; prompt user to retry
        if self._server_dict[server_id].is_full:
            await self.emit("server_full", room=sid)
            return
        await self._server_dict[server_id].join(self.namespace, sid, name)

    async def on_refresh(self, sid) -> None:
        await self._refresh()

    async def _refresh(self):
        await self.emit(
            "refresh",
            {"servers": self._server_list()},
            callback=lambda: print("refreshed"),
        )

    def _get_servers(name: str):
        return list(
            filter(
                lambda server: server.name == name, self._server_dict.values()
            )
        )
