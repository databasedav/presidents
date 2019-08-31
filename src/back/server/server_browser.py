from .server import Server
from typing import Dict, List, Union, Callable

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
import asyncio
from functools import partial
from ..game.emitting_game import AsyncTimer

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
        self.add_server(
            payload.pop("name"),
            timer=partial(AsyncTimer.spawn_after, loop=self.server.loop),
            **payload,
        )
        # try:
        #     await self._refresh()
        # except AttributeError:  # nobody has entered the server browser
        #     pass

    # allows multiple servers with the same name (will have different server ids)
    def add_server(
        self,
        name: str,
        *,
        server_id: str = str(uuid.uuid4()),
        timer: Callable = None,
        turn_time: Union[int, float] = None,
        reserve_time: Union[int, float] = None,
    ):
        server: Server = Server(
            server_id,
            name,
            timer=timer,
            turn_time=turn_time,
            reserve_time=reserve_time,
        )
        self._server_dict[server_id] = server
        # self.server is the socket.io server
        self.server.register_namespace(server)
        # print(f'number of servers: {len(self._server_dict)}')

    async def on_join_server_as_player(self, sid, payload):
        """
        sid will either be the sid of an actual human client or the sid
        of a ClientBotFarm's server browser client; in the latter case,
        the payload will include the sid of the ClientBot that the
        ClientBotFarm wants to join the game
        """
        bot_client_sid: str = payload.get("bot_client_sid")
        await self._join_server_as_player(
            sid=bot_client_sid or sid,
            server_id=payload["server_id"],
            name=payload["name"],
            bot_client_sid=bot_client_sid,
        )

    async def _join_server_as_player(
        self,
        sid: str,
        server_id: str,
        name: str,
        *,
        bot_client_sid: str = None,
    ):
        # TODO timeout if server isn't joined in a few seconds; prompt user to retry
        server: Server = self._server_dict[server_id]
        if server.game and server.game.is_full:
            await self.emit("server_full", room=bot_client_sid or sid)
        else:
            await server.add_player(sid, None, name)
        # print(f'number of players: {sum(server.game.num_players for server in self._server_dict.values() if server.game)}')

    async def _join_server_as_spectator(self, sid, payload):
        ...

    async def on_refresh(self, sid) -> None:
        await self._refresh()

    async def _refresh(self):
        await self.emit(
            "refresh",
            {"servers": self._server_list()},
            callback=lambda: print("refreshed"),
        )

    def _get_servers(self, name: str):
        return list(
            filter(
                lambda server: server.name == name, self._server_dict.values()
            )
        )
