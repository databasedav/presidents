from socketio import AsyncClient, AsyncClientNamespace
from typing import Dict


class BotFarm:
    def __init__(self) -> None:
        self._num_bots: int = 0
        self._bot_dict: Dict[str, Bot]


# TODO: another thing that receives rounds that have just been completed
#       and then replays all the moves with assertions and then put the
#       rounds into a database that just marks that they have passed
#       playing the game with assertions


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
        self._cards: Dict[
            int, bool
        ] = dict()  # whether or not card is selected
        self._unlocked: bool = False
        self._pass_unlocked: bool = False

    def take_action(self):
        """
        against humanity
        """


class ServerBot(Bot):
    ...


class Client(AsyncClient):
    """
    For connecting to server browsers and servers.
    """
    ...


class ClientBot(Bot, AsyncClientNamespace):
    """
    The client bot has the same 'view' of the game state that a human
    player does and communicates with the server with the same socket.io
    events that the web client does.

    Unlike a server bot, the client bot does not have direct access to
    the game instance.

    Allows emitting and receiving events from Servers (which are
    AsyncNamespaces); supports doing so from multiple servers, i.e.
    multiple games.
    """
    def __init__(self, *args, **kwargs):
        AsyncClientNamespace.__init__(self, *args, **kwargs)

    def on_add_card(payload):
        self._cards[payload["card"]] = False

    def on_remove_card(payload):
        del self._cards[payload["card"]]

    async def on_set_on_turn(payload):
        await self._turn_up()

    def on_set_unlocked(payload):
        self._unlocked = payload["unlocked"]

    def on_set_pass_unlocked(payload):
        self._pass_unlocked = payload["pass_unlocked"]

    async def on_alert(payload):
        await self._panic_pass()

    async def turn_up(self):
        # select lowest card if not already selected and attempt to
        # play, otherwise receival of alert will pass instead
        min_card: int = min(self._cards)
        if not self._cards[min_card]:
            await self._click_card(min_card)
        if not self._unlocked:
            await self._unlock()
        if self._unlocked:  # either already unlocked or the above unlocked
            await self.play()

    async def click_card(self, card: int) -> None:
        await self.emit("card_click", {"card": card})

    async def unlock(self) -> None:
        await self.emit("unlock")

    async def play(self) -> None:
        await self.emit("play")

    async def _panic_pass(self) -> None:
        if not self._pass_unlocked:
            await self.emit("unlock_pass")
        if self._pass_unlocked:
            await self.emit("pass_turn")


# TODO: orchestrator for client bots that auto rejoins them to reset
#       games to avoid having to deal with trading
