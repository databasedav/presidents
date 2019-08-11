from socketio import AsyncClient, AsyncClientNamespace
from typing import Dict
import asyncio
from uuid import uuid4

import logging

logger = logging.getLogger(__name__)


class ClientBotFarm:
    '''
    Orchestrates individual bots; i.e. what games they join, the model
    they are based on, etc.

    ClientBotFarms can only be connected to a single server browser.

    Adds servers for Clients to join.
    '''

    
    def __init__(self) -> None:
        self._num_bots: int = 0
        self._bot_dict: Dict[str, Bot]  # bot_id to Bot
        self.client: AsyncClient = AsyncClient()

    async def connect_to_server_browser(self, host: str, port: str, server_browser_id: str) -> None:
        client.register_namespace(ServerBrowserClient(f'/server_browser={server_browser_id}'))
        await client.connect(f'http://{host}:{port}')

    def client_join_server_as_player(self, bot_id: str, server_id: str):
        self.client.emit('join_server_as_player', {'server_id': server_id, })
        self._bot_dict[bot_id].join_server(server_id)

    def build_a_bot_workshop(self) -> Bot:
        ...

class ServerBrowserClient(AsyncClientNamespace):
    '''
    Keeps a live view of the a server browser. Handles server fulls.
    '''
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
        self.bot_id = str(uuid4())
        # whether or not card is selected
        self._cards: Dict[int, bool] = dict()
        self._unlocked: bool = False
        self._pass_unlocked: bool = False

    def take_action(self):
        """
        against humanity
        """
    
    def _add_card(self, card: int) -> None:
        self._cards[card] = False
    
    def _remove_card(self, card: int) -> None:
        del self._cards.[card]
    
    def _select_card(self, card: int) -> None:
        self._cards[card] = True

    def _deselect_card(self, card: int) -> None:
        self._cards[card] = False
    
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
    def __init__(self, name: str):
        ...

    def connect_to_namespace(self, namespace: str) -> None:
        '''
        Simply allows emitting to the given namespace.
        '''
        self.connection_namespaces.append(namespace)
        self.namespaces.append(namespace)
    
    async def join_server(self, server_id: str) -> None:
        await self.emit('join_server', {'server_id': server_id})
    


class ClientBot(Bot, AsyncClientNamespace):
    """
    The client bot has the same 'view' of the game state that a human
    player does and communicates with the server with the same socket.io
    events that the web client does.

    Unlike a server bot, the client bot does not have direct access to
    the game instance.

    
    """

    def __init__(self, *args, **kwargs):
        AsyncClientNamespace.__init__(self, *args, **kwargs)
        Bot.__init__(self)

    async def on_add_card(self, payload):
        self._add_card(payload["card"])

    def on_remove_card(self, payload):
        self._remove_card(payload["card"])

    def on_select_card(self, payload):
        self._select_card(payload['card'])
    
    def on_deselect_card(self, payload):
        self._deselect_card(payload['card'])

    async def on_set_on_turn(self, payload):
        if payload['on_turn']:
            await self._turn_up()

    def on_set_unlocked(self, payload):
        self._set_unlocked(payload["unlocked"])

    def on_set_pass_unlocked(self, payload):
        self._set_pass_unlocked(payload["pass_unlocked"])

    async def on_alert(self, payload):
        await self._panic_pass()

    async def _turn_up(self):
        # select lowest card if not already selected and attempt to
        # play, otherwise receival of alert will pass instead
        min_card: int = min(self._cards)
        if not self._cards[min_card]:
            await self._click_card(min_card)
        if not self._unlocked:
            await self._unlock()
        if self._unlocked:  # either already unlocked or the above unlocked
            await self._play()

    async def _click_card(self, card: int) -> None:
        await self.emit("card_click", {"card": card})

    async def _unlock(self) -> None:
        await self.emit("unlock")

    async def _play(self) -> None:
        await self.emit("play")

    async def _panic_pass(self) -> None:
        if not self._pass_unlocked:
            await self.emit("unlock_pass")
        if self._pass_unlocked:
            await self.emit("pass_turn")
    
    async def emit(self, *args, **kwargs):
        await super().emit(*args, **kwargs)
        await asyncio.sleep(0.05)


# TODO: orchestrator for client bots that auto rejoins them to reset
#       games to avoid having to deal with trading
