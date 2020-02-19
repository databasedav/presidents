import logging

from socketio import AsyncClient
from itertools import combinations
from asyncio import gather, sleep
from random import choice, randrange
from numpy.random import binomial

from ..secrets import BOT_KEY
from ...game import Chamber, Hand

logger = logging.getLogger(__name__)

NUM_BOT_SERVERS = 8

# only listens to events that change the state directly visible to bots
# includes everything visible in front end game vue
class Bot:
    def __init__(self):
        self._sio = AsyncClient(request_timeout=300)
        self.chamber = Chamber()
        self.hand_in_play = Hand()
        self.ranks = dict()
        self.num_cards_remaining = [0 for _ in range(4)]
        self.dot_colors = ["red" for _ in range(4)]
        self.gives = [0 for _ in range(4)]
        self.takes = [0 for _ in range(4)]
        self.giving_options = list()
        self.names = ["" for _ in range(4)]
        self.on_turn = False
        self.unlocked = False
        self.pass_unlocked = False
        self.paused = False
        self.hands_stored = False

    async def connect_to_game(self, game_id: str, *, bot_game_server=None):
        self._register_event_handlers()
        await self._sio.connect(
            f"ws://bot_game_server_{bot_game_server or randrange(1, NUM_BOT_SERVERS + 1)}",
            {"bot_key": BOT_KEY, "game_id": game_id},
        )

    def _register_event_handlers(self):
        sio = self._sio
        chamber = self.chamber
        hand_in_play = self.hand_in_play
        ranks = self.ranks
        num_cards_remaining = self.num_cards_remaining
        dot_colors = self.dot_colors
        gives = self.gives
        takes = self.takes
        giving_options = self.giving_options
        names = self.names

        @sio.event
        def add_card(payload):
            chamber.add_card(payload["card"])

        @sio.event
        def alert(payload):
            self.alert = payload["alert"]

        @sio.event
        def clear_cards(payload):
            chamber.reset()

        @sio.event
        def clear_hand_in_play(payload):
            hand_in_play.reset()

        @sio.event
        def deselect_card(payload):
            chamber.deselect_card(payload["card"])

        @sio.event
        def deselect_rank(payload):
            ranks[payload["rank"]] = False

        @sio.event
        def message(payload):
            # TODO: decide how to handle messages
            # self.messages.append(payload['message'])  # TODO
            ...

        @sio.event
        def remove_card(payload):
            chamber.remove_card(payload["card"])

        @sio.event
        def remove_rank(payload):
            del ranks[payload["rank"]]

        @sio.event
        def select_card(payload):
            chamber.select_card(payload["card"])

        @sio.event
        def select_hand(payload):
            chamber.select_cards(payload["hand"])

        @sio.event
        def select_rank(payload):
            ranks[payload["rank"]] = True

        @sio.event
        def set_asker(payload):
            ranks.update({i: False for i in range(1, 14)})

        # TODO: shouldn't need this one
        @sio.event
        def set_rank(payload):
            ...

        @sio.event
        def set_num_cards_remaining(payload):
            num_cards_remaining[payload["spot"]] = payload[
                "num_cards_remaining"
            ]

        @sio.event
        def set_dot_color(payload):
            dot_colors[payload["spot"]] = payload["dot_color"]

        @sio.event
        def set_giver(payload):
            ...

        @sio.event
        def set_gives(payload):
            gives[payload["spot"]] = payload["gives"]

        @sio.event
        def set_giving_options(payload):
            giving_options.extend(payload["options"])

        @sio.event
        def set_hand_in_play(payload):
            if not hand_in_play.is_empty:
                hand_in_play.reset()
            for card in payload["hand_in_play"]:
                hand_in_play.add(card)

        @sio.event
        def set_name(payload):
            names[payload["spot"]] = payload["name"]

        @sio.event
        async def set_on_turn(payload):
            on_turn = payload["on_turn"]
            self.on_turn = on_turn
            if on_turn:
                await self.turn_up()

        @sio.event
        def set_pass_unlocked(payload):
            self.pass_unlocked = payload["pass_unlocked"]

        @sio.event
        def set_paused(payload):
            self.paused = payload["paused"]

        @sio.event
        def set_spot(payload):
            pass

        @sio.event
        def set_takes(payload):
            takes[payload["spot"]] = payload["takes"]

        @sio.event
        def set_time(payload):
            ...  # TODO: how to handle timers for bots? redis ttl?

        @sio.event
        def set_trading(payload):
            trading = payload["trading"]
            self.trading = trading
            if not trading and ranks:
                ranks.clear()

        @sio.event
        def set_unlocked(payload):
            self.unlocked = payload["unlocked"]

        @sio.event
        def set_timer_state(payload):
            ...

        @sio.event
        def update_current_hand_str(payload):
            pass

    async def turn_up(self):
        if not self.hands_stored:
            await self.store_hands()
        hand_in_play = self.hand_in_play
        chamber = self.chamber
        # TODO: randomly play bomb if have bomb
        if 1 in self.chamber:
            await self.cards_unlock_play(
                chamber._cards[1].last.value.value
                if chamber._cards[1].last
                else [1]
            )
            return
        elif hand_in_play.is_empty:
            hand_nodes = list(self.chamber._hand_nodes)
            await self.cards_unlock_play(
                choice(hand_nodes).hand
                if hand_nodes
                else [self.chamber._get_max_card()]
            )
            return
        elif hand_in_play.is_single:
            # usually pass to increase chance of playing multi card hands
            if binomial(1, 0.85):
                self.unlock_pass_pass()
                return
            hand = Hand([self.chamber._get_random_card()])
        else:  # is multi card hand
            if hand_node := getattr(chamber, f"{hand_in_play.id_str}s").last:
                hand = hand_node.value
            else:
                await self.unlock_pass_pass()
                return
        if hand > hand_in_play:
            await self.cards_unlock_play(hand)
        else:
            await self.unlock_pass_pass()

    def _on_success_callback_constructor(self, func, *args, **kwargs):
        async def callback(success):
            if success:
                await func(*args, **kwargs)
            else:
                logger.error(f"game action {action} failed")

        return callback

    async def cards_unlock_play(self, cards):
        # removes cards in hand first if there are any
        cards_to_click = list(self.chamber.hand) + list(cards)
        await gather(*[self.card(card) for card in cards_to_click[:-1]])
        # TODO: replace this mess with a chaining syntax
        await self.card(
            cards_to_click[-1],
            self._on_success_callback_constructor(
                self.unlock, self._on_success_callback_constructor(self.play)
            ),
        )

    async def unlock_pass_pass(self):
        await self.unlock_pass(
            self._on_success_callback_constructor(self.pass_)
        )

    async def store_hands(self):
        """
        Auto stores all available combos.
        """
        chamber = self.chamber
        cards = chamber.cards
        for num_cards in range(2, 6):
            for cards in combinations(cards, num_cards):
                hand = Hand(cards)
                if hand.is_valid:
                    chamber.add_hand(hand)
        self.hands_stored = True

    async def ask(self):
        await self._game_action(-22)

    async def card(self, card: int, callback=None):
        await self._game_action(card, callback)

    async def give(self):
        await self._game_action(-20)

    async def lock(self):
        await self._game_action(-19)

    async def play(self):
        await self._game_action(-17)

    async def pass_(self):
        await self._game_action(-18)

    async def rank(self, rank: int):
        await self._game_action(-rank)

    async def unlock(self, callback):
        await self._game_action(-15, callback)

    async def unlock_pass(self, callback):
        await self._game_action(-14, callback)

    async def _game_action(self, action: int, callback=None):
        await self._emit("game_action", {"action": action}, callback=callback)

    async def _emit(self, *args, **kwargs):
        await self._sio.emit(*args, **kwargs)
