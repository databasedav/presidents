from socketio import AsyncClient, AsyncClientNamespace
from typing import Dict, Union
import asyncio
from uuid import uuid4
import random

import logging

from ..utils import AsyncTimer

logger = logging.getLogger(__name__)

# NOTE: bot client is the client that a ClientBot lives on


class ClientBotFarm:
    """
    Orchestrates individual bots; i.e. what games they join, the model
    they are based on, etc.

    ClientBotFarms can only be connected to a single server browser.

    Adds servers for Clients to join.
    """

    def __init__(self) -> None:
        self._num_bots: int = 0
        self._bot_dict: Dict[str, ClientBot] = dict()  # bot_id to Bot
        self._bot_client_dict: Dict[str, int] = dict()  # bot_id to client_id
        self._client: AsyncClient = AsyncClient()
        self._server_browser_client: ServerBrowserClient = None
        self._bot_clients = [Client() for _ in range(4)]

    async def connect_to_server_browser(
        self, host: str, port: int, server_browser_id: str
    ) -> None:
        self._server_browser_client = ServerBrowserClient(
            f"/server_browser={server_browser_id}"
        )
        self._client.register_namespace(self._server_browser_client)
        # server browser namespace is taken from the event handlers
        await self._client.connect(f"http://{host}:{port}")
        await asyncio.gather(
            *[
                client.connect(
                    f"http://{host}:{port}",
                    namespaces=[
                        f"/server={server_id}" for server_id in range(2000)
                    ],
                )
                for client in self._bot_clients
            ]
        )

    async def add_server(
        self,
        name: str,
        server_id: str,
        *,
        turn_time: Union[int, float] = None,
        reserve_time: Union[int, float] = None,
    ):
        if not self._server_browser_client:
            raise Exception(
                "must connect to server browser before adding server"
            )
        await self._server_browser_client.emit(
            "add_server",
            {
                "name": name,
                "server_id": server_id,
                "turn_time": turn_time,
                "reserve_time": reserve_time,
            },
        )

    async def bot_join_server(self, bot_id: str):
        bot: ClientBot = self._bot_dict[bot_id]
        client: Client = self._get_bot_client(bot_id)
        # client.connect_to_namespace(bot.namespace)
        client.register_namespace(bot)
        await self._server_browser_client.emit(
            "join_server_as_player",
            {
                "bot_client_sid": client.sid,
                "server_id": bot.server_id,
                "name": bot.id,
            },
        )

    def build_a_bot_workshop(self, server_id: str, client: int) -> str:
        bot: ClientBot = ClientBot(server_id)
        bot_id = bot.id
        self._bot_dict[bot_id] = bot
        self._bot_client_dict[bot_id] = client
        return bot_id

    def _get_bot_client(self, bot_id: str):
        return self._bot_clients[self._bot_client_dict[bot_id]]


class ServerBrowserClient(AsyncClientNamespace):
    """
    Keeps a live view of the a server browser. Handles server fulls.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.servers: Dict[str, Server] = dict()  # server id to server


# TODO: another thing that receives rounds that have just been completed
#       and then replays all the moves with assertions and then put the
#       rounds into a database that just marks that they have passed
#       playing the game with assertions

# TODO: create issue on python socketio to allow client connecting to
#       namespaces after initial connection


class Bot:
    """
    Bots broadly perform two functions. The first is to replay 
    presidents rounds played by humans with assertions in order to
    guarantee that the rules of my game are implemented fucking
    perfectly. The second is to auto play against each other and with
    other players; they can autoplay at various levels of skill based on
    artificial intelligence and machine learning (wow!).

    Interfaces directly with GameClicks table.

    Bots can only play one game at a time.
    """

    actions = {
        "card_click": "add_or_remove_card",
        "unlock": "unlock_handler",
        "lock": "lock_handler",
        "play": "maybe_play_current_hand",
        "unlock_pass": "maybe_unlock_pass_turn",
        "pass_turn": "maybe_pass_turn",
        "select_asking_option": "set_selected_asking_option",
        "ask": "ask_for_card",
        "give": "give_card",
    }

    def __init__(self):
        self._game = None
        self.id = str(uuid4())
        # whether or not card is selected
        self._cards: Dict[int, bool] = dict()
        self._selected_cards = list()
        self._unlocked: bool = False
        self._pass_unlocked: bool = False

    def take_action(self):
        """
        against humanity
        """

    def _add_card(self, card: int) -> None:
        self._cards[card] = False

    def _remove_card(self, card: int) -> None:
        del self._cards[card]
        if card in self._selected_cards:
            self._selected_cards.remove(card)

    def _select_card(self, card: int) -> None:
        self._cards[card] = True
        self._selected_cards.append(card)

    def _deselect_card(self, card: int) -> None:
        self._cards[card] = False
        self._selected_cards.remove(card)

    def _set_unlocked(self, unlocked: bool) -> None:
        self._unlocked = unlocked

    def _set_pass_unlocked(self, pass_unlocked: bool) -> None:
        self._pass_unlocked = pass_unlocked


class ServerBot(Bot):
    ...


class Client(AsyncClient):
    """
    For connecting to servers. This is not a general client for
    interacting with the presidents app; it is solely for hosting bots.
    
    Allows emitting and receiving events from Servers (which are
    AsyncNamespaces); supports doing so from multiple servers, i.e.
    multiple games.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection_namespaces = list()

    def connect_to_namespace(self, namespace: str) -> None:
        """
        Simply allows emitting to the given namespace.
        """
        if not self.connection_namespaces:
            self.connection_namespaces = list()
        self.connection_namespaces.append(namespace)
        self.namespaces.append(namespace)


class ClientBot(Bot, AsyncClientNamespace):
    """
    The client bot has the same 'view' of the game state that a human
    player does and communicates with the server with the same socket.io
    events that the web client does.

    Unlike a server bot, the client bot does not have direct access to
    the game instance.

    ClientBots require the server to be joined to be given at init.

    TODO: smarter bot; consecutive alerts trigger some corrective action
    """

    def __init__(self, server_id: str):
        AsyncClientNamespace.__init__(self, f"/server={server_id}")
        Bot.__init__(self)
        self.server_id: str = server_id
        self._consecutive_alerts = 0

    async def on_add_card(self, payload):
        self._add_card(payload["card"])

    def on_remove_card(self, payload):
        self._remove_card(payload["card"])

    def on_select_card(self, payload):
        self._select_card(payload["card"])

    def on_deselect_card(self, payload):
        self._deselect_card(payload["card"])

    async def on_set_on_turn(self, payload):
        self._consecutive_alerts = 0
        # # the following is done because the timer on the server is
        # started after receiving the on turn acknowledgement
        # if payload["on_turn"]:
        # AsyncTimer.spawn_after(0.5, self._turn_up)
        await self._turn_up()

    def on_set_unlocked(self, payload):
        self._set_unlocked(payload["unlocked"])

    def on_set_pass_unlocked(self, payload):
        self._set_pass_unlocked(payload["pass_unlocked"])

    async def on_alert(self, payload):
        self._consecutive_alerts += 1
        if self._consecutive_alerts == 1:
            await self._panic_pass()
        elif self._consecutive_alerts == 2:
            await self._request_correct_state()
        # if stuck in alert loop simply does nothing

    async def on_correct_state(self, payload):
        self._cards = {card: False for card in payload["cards"]}
        self._selected_cards.clear()
        for card in payload["selected_cards"]:
            self._select_card(card)
        self._set_unlocked(payload["unlocked"])
        self._set_pass_unlocked(payload["pass_unlocked"])

    async def _turn_up(self):
        if self._selected_cards:
            await asyncio.gather(
                *[self._click_card(card) for card in self._selected_cards]
            )
        if 1 in self._cards:
            card = 1
        else:
            card = random.choice(list(self._cards.keys()))
        if not self._cards[card]:
            await self._click_card(card)
        if not self._unlocked:
            await self._unlock()
        if self._unlocked:  # either already unlocked or the above unlocked
            await self._play()

    async def _click_card(self, card: int) -> None:
        await self._emit("card_click", {"card": card})

    async def _unlock(self) -> None:
        await self._emit("unlock")

    async def _play(self) -> None:
        await self._emit("play")

    async def _panic_pass(self) -> None:
        if not self._pass_unlocked:
            await self._emit("unlock_pass")
        if self._pass_unlocked:
            await self._emit("pass_turn")

    async def _request_correct_state(self) -> None:
        await self._emit("request_correct_state")

    async def _emit(self, *args, **kwargs):
        await super().emit(*args, **kwargs)
        await asyncio.sleep(0.2)


# TODO: orchestrator for client bots that auto rejoins them to reset
#       games to avoid having to deal with trading
