from typing import Callable, Dict, List, Optional, Set, Union, Iterable

from bidict import bidict
from socketio import AsyncServer

import asyncio
import inspect
import re
from time import time

from ..game.hand import NotPlayableOnError
from ..utils import AsyncTimer

# from ..server.server import Server
Server = None

from . import (
    Hand,
    DuplicateCardError,
    FullHandError,
    CardNotInChamberError,
    EmittingChamber,
    Game,
    base_hand,
    PresidentsError,
)

from datetime import datetime

from ..data.stream.records import HandPlay

# from ..server.server import Server  # TODO: pls fix this omg

# from ..data.stream.agents import hand_play_agent

# TODO: decide what to do for the removal of asking options
# TODO: spectators should get a completely hidden view of the game being
#       played and maybe if you are friends with another player, you can
#       see that player's cards and stuff like that
# TODO: block receiving user events during autoplay, block autoplaying
#       while user event is being processed
# TODO: in general, make sure certain state has actually changed before
#       notifying client

# TODO: ok here is what is gna happen: timer will start server side
#       w 0 delay and then the on_turn acks will be stored in the db
#       for analysis, the timer start time will be sent to the front
#       end so it can determine how much time the player actually has
#       the fact that the player will actually have less time to play
#       will be handled by the fact that they have reserve time and
#       also the fact that they should get a better internet connection, bitch

# TODO: kwargs strat has failed... (this is referring to autoplaying
#       not happening invisibly to the player)


class EmittingGame(Game):
    def __init__(self, server: Server, **kwargs):
        super().__init__(**kwargs)
        # TODO: server stuff (including emitting should be entirely handled by the Server, which is an AsyncNamespace)
        self._server: Server = server
        self._chambers: List[EmittingChamber] = [
            EmittingChamber(self._server) for _ in range(4)
        ]
        self._spot_sid_bidict: bidict = bidict()
        self._sid_user_id_dict: Dict[str, str] = dict()
        self.hand_play_agent = server.server.agents["hand_play_agent"]
        self.num_spectators: int = 0  # TODO

    # properties

    @property
    def _current_player_sid(self) -> str:
        return self._get_sid(self._current_player)

    # setup related methods

    def set_server(self, server: str) -> None:
        self._server = server

    async def _add_player_to_spot(
        self, sid: str, user_id: str, name: str, spot: int
    ) -> None:
        """
        NOTE: logic copy/pasted from base; must update manually
        """
        assert self._names[spot] is None, f"player already in spot {spot}"
        self._open_spots.remove(spot)
        self._chambers[spot].set_sid(sid)
        self._spot_sid_bidict.inv[sid] = spot
        self._sid_user_id_dict[sid] = user_id
        await self._set_name(spot=spot, name=name)
        self.num_players += 1

        # TODO TODO: THIS SHOULD NOT BE HERE.
        if self.num_players == 4:
            await self._start_round()

    def remove_player(self, sid: str) -> None:
        super().remove_player(self._get_spot(sid))
        self._spot_sid_bidict.inv.pop(sid)
        self._sid_user_id_dict.pop(sid)

    async def _deal_cards(
        self, *, deck: Optional[List[Iterable[int]]] = None
    ) -> None:
        """
        Deals cards to all players.
        """
        await asyncio.gather(
            *[
                self._deal_cards_indiv(spot, sid, cards)
                for (spot, sid), cards in zip(
                    self._spot_sid_bidict.items(),
                    deck or self._make_shuffled_deck(),
                )
            ]
        )

    async def _deal_cards_indiv(
        self, spot: int, sid: str, cards: Iterable[int]
    ):
        """
        Deals cards to an individual player; for utilizing concurrency
        with asyncio.gather.
        """
        chamber = self._chambers[spot]
        await chamber.reset()
        chamber.set_sid(sid)
        await asyncio.gather(
            chamber.add_cards(cards),
            self._emit("set_spot", {"spot": spot}, sid),
        )

    # game flow related methods

    async def _start_round(self, *, deck: List[Iterable[int]] = None) -> None:
        """
        NOTE: logic copy/pasted from base; must update manually
        """
        assert self.num_players == 4, "four players required to start round"
        await self._deal_cards(deck=deck)
        self._make_and_set_turn_manager()
        self._num_consecutive_rounds += 1
        await asyncio.gather(
            *[
                self._set_time("reserve", self._reserve_time, spot, False)
                for spot in range(4)
            ],
            self._message(f"🏁 round {self._num_consecutive_rounds} has begun"),
            self._next_player(),
        )

    async def _next_player(self) -> None:
        try:  # current player is no longer on turn
            await self._emit(
                "set_on_turn", {"on_turn": False}, self._current_player_sid
            )
        except KeyError:  # self._current_player is None on round start
            pass
        # TODO this mypy error
        self._current_player = spot = next(self._turn_manager)
        await asyncio.gather(
            self._set_time("turn", self._turn_time, spot, True),
            self._message(f"🎲 it's {self._names[spot]}'s turn"),
            self._emit_set_on_turn_handler(spot),
        )

    async def _emit_set_on_turn_handler(self, spot: int) -> None:
        await asyncio.gather(
            self._emit("set_on_turn", {"on_turn": True}, self._get_sid(spot)),
            self._set_dot_color(spot, "green"),
        )

    async def _set_time(
        self,
        which: str,
        seconds: Union[int, float],
        spot: int = None,
        start: bool = False,
    ) -> None:
        await self._emit_to_players(
            "set_time",
            {
                "which": which,
                "spot": spot,
                "time": seconds * 1000,
                "start": start,
                # this item accounts for server/client latency
                "timestamp": time(),  # seconds since epoch
            },
        )
        super()._set_time(which, seconds, spot, False)
        # done like this because the "start" item from above takes care
        # of emitting the start state
        if start:
            super()._start_timer(which, spot)

    async def _start_timer(self, which: str, spot: int = None) -> None:
        await self._emit_to_players(
            "set_timer_state", {"which": which, "spot": spot, "state": True}
        )
        super()._start_timer(which, spot)

    async def _stop_timer(
        self, which: str, spot: int = None, *, cancel: bool = True
    ) -> None:
        """
        NOTE: logic copy/pasted from base; must update manually
        """
        now: datetime = datetime.utcnow()
        assert which in ["turn", "reserve", "trading"]
        await self._emit_to_players(
            "set_timer_state", {"which": which, "spot": spot, "state": False}
        )
        if which == "turn":
            assert spot is not None
            # if a timeout handler is calling this, cancelling the timer
            # is a horrible, horrible bug; but we fixed it bois
            if cancel and self._timers[spot] is not None:
                self._timers[spot].cancel()
            # can delete timer even when not cancelling since this only
            # happens when a timeout handler is handling, i.e. said
            # timer has carried out its purpose and cancelling breaks
            # desired behavior
            self._timers[spot] = None
            await self._emit_to_players(
                "set_time",
                {"which": "turn", "spot": spot, "time": 0, "start": False},
            )
            self._turn_time_use_starts[spot] = None
        elif which == "reserve":
            assert spot is not None
            if cancel and self._timers[spot] is not None:
                self._timers[spot].cancel()
            self._timers[spot] = None
            time_used = (
                now - self._reserve_time_use_starts[spot]
            ).total_seconds()
            # need the max statement since this function is used during
            # reserve time timeouts
            await self._set_time(
                "reserve", max(0, self._reserve_times[spot] - time_used), spot
            )
            self._reserve_time_use_starts[spot] = None
        elif which == "trading":
            # TODO
            # if cancel: ?
            self._trading_timer.cancel()
            self._trading_timer = None
            await self._set_time("trading", self._trading_time)
            self._trading_time_start = None

    async def _pause(self) -> None:
        await self._emit_to_players(
            "set_paused", {"paused": True}
        )  # game has been paused...
        self._pause_timers()

    async def _unpause(self) -> None:
        await asyncio.gather(
            self._emit_to_players("set_paused", {"paused": False}),
            self._unpause_timers(),
        )

    async def _unpause_timers(self) -> None:
        await asyncio.gather(*[timer() for timer in self._paused_timers])

    async def _player_finish(self, spot: int) -> None:
        assert self._chambers[
            spot
        ].is_empty, "only players with no cards remaining can finish"
        await self._set_dot_color(spot, "purple")
        self._positions.append(self._current_player)
        self._turn_manager.remove(self._current_player)
        num_unfinished_players = self._num_unfinished_players
        if num_unfinished_players == 3:
            await asyncio.gather(
                self._set_president(spot),
                self._message(f"🏆 {self._names[spot]} is president 🥇"),
                self._next_player(),
            )
        elif num_unfinished_players == 2:
            await asyncio.gather(
                self._set_vice_president(spot),
                self._message(f"🏆 {self._names[spot]} is vice president 🥈"),
                self._next_player(),
            )
        else:  # num_unfinished
            await self._set_vice_asshole(spot)
            self._current_player = next(self._turn_manager)
            await self._set_asshole(self._current_player)
            self._positions.append(self._current_player)
            await asyncio.gather(
                self._message(
                    f"🏆 {self._names[spot]} is vice asshole 🥉 and {self._names[self._current_player]} is asshole 💩"
                ),
                self._set_trading(True),
            )

    # TODO
    async def emit_correct_state(self, sid: str):
        spot: int = self._get_spot(sid)
        await self._emit(
            "correct_state",
            {
                "cards": list(self._chambers[spot]),
                "selected_cards": self._get_current_hand(spot).to_list(),
                "unlocked": self._unlocked[spot],
                "pass_unlocked": self._pass_unlocked[spot],
            },
            sid,
        )

    # card management related methods

    async def add_or_remove_card_handler(self, sid: str, card: int) -> None:
        spot: int = self._get_spot(sid)
        try:
            await self.add_or_remove_card(spot, card)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    # TODO
    def store_hand(self, spot: int) -> None:
        ...

    # playing and passing related methods

    async def _maybe_unlock_play_handler(self, spot: int, sid: str) -> None:
        try:
            await self.maybe_unlock_play(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def maybe_play_current_hand_handler(
        self, sid: str, timestamp: datetime
    ) -> None:
        try:
            await self.maybe_play_current_hand(
                self._get_spot(sid), sid=sid, timestamp=timestamp
            )
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def _play_current_hand(self, spot: int, **kwargs) -> None:
        assert self._unlocked[spot], "play called without unlocking"
        await self._stop_timer(
            which="turn"
            if not self._is_using_reserve_time(spot)
            else "reserve",
            spot=spot,
        )
        chamber = self._chambers[spot]
        hand = Hand.copy(chamber.hand)
        await asyncio.gather(
            # TODO
            # self.hand_play_agent.cast(
            #     HandPlay(
            #         hand_hash=hash(hand),
            #         sid=kwargs.get("sid", self._get_sid(spot)),
            #         timestamp=kwargs.get("timestamp"),
            #     )
            # ),
            chamber.remove_cards(hand),
            self._set_hand_in_play(hand),
            self._message(f"▶️ {self._names[spot]} played {str(hand)}"),
            self.lock(spot),
            self._set_dot_color(spot, "blue"),
            *[
                self._set_dot_color(other_spot, "red")
                for other_spot in self._get_other_spots(
                    spot, exclude_finished=True
                )
            ],
            self._emit_to_players(
                "set_cards_remaining",
                {
                    "spot": spot,
                    "cards_remaining": self._chambers[spot].num_cards,
                },
            ),
        )
        self._num_consecutive_passes = 0
        # lock others if their currently unlocked hand should no longer be unlocked
        for other_spot in self._get_other_spots(spot, exclude_finished=True):
            if self._unlocked[other_spot]:
                try:
                    if self._get_current_hand(other_spot) < self._hand_in_play:
                        await self.lock(other_spot)
                # occurs either when base_hand is the hand in play since
                # anything can be unlocked or when a bomb is played on a
                # non-bomb that other players have unlocked on
                except NotPlayableOnError:
                    await self.lock(other_spot)
        await self._post_play_handler(spot)

    async def maybe_unlock_pass_turn_handler(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            await self.maybe_unlock_pass_turn(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def _unlock_pass(self, spot: int) -> None:
        await self._lock_if_unlocked(spot)
        self._pass_unlocked[spot] = True
        await self._emit(
            "set_pass_unlocked", {"pass_unlocked": True}, self._get_sid(spot)
        )

    async def _lock_pass(self, spot: int) -> None:
        super()._lock_pass(spot)
        await self._emit(
            "set_pass_unlocked", {"pass_unlocked": False}, self._get_sid(spot)
        )

    async def maybe_pass_turn_handler(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            await self.maybe_pass_turn(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def _pass_turn(self, spot: int) -> None:
        """
        NOTE: logic copy/pasted from base; must update manually
        """
        assert self._pass_unlocked[spot], "pass called without unlocking"
        self._num_consecutive_passes += 1
        await asyncio.gather(
            self._stop_timer(
                "turn" if not self._is_using_reserve_time(spot) else "reserve",
                spot,
            ),
            self._lock_pass(spot),
            self._message(f"⏭️ {self._names[spot]} passed"),
            self._set_dot_color(spot, "yellow"),
            self._post_pass_handler(),
        )

    async def _clear_hand_in_play(self) -> None:
        super()._clear_hand_in_play()
        await self._emit_to_players("clear_hand_in_play")

    # trading related methods

    async def _set_trading(self, trading: bool) -> None:
        """
        NOTE: logic copy/pasted from base; must update manually
        """
        self.trading = trading
        await self._emit_to_server("set_trading", {"trading": trading})
        # TODO: the below don't set all the required attributes
        if trading:
            await asyncio.gather(
                self._start_timer("trading"),
                *[self._set_dot_color(spot, "red") for spot in range(4)],
                self._emit(
                    "set_on_turn", {"on_turn": False}, self._current_player_sid
                ),
                self._clear_hand_in_play(),
                self._deal_cards(),
                self._message("💱 trading has begun"),
            )

            self._num_consecutive_passes: int = 0
            self._finishing_last_played: bool = False
            self._timers = [None for _ in range(4)]
            self._selected_asking_options: List[Optional[int]] = [
                None for _ in range(4)
            ]
            self._already_asked: List[Set[int]] = [set() for _ in range(4)]
            self._giving_options: List[Optional[Set[int]]] = [
                set() for _ in range(4)
            ]
            self._given: List[Set[int]] = [set() for _ in range(4)]
            self._taken: List[Set[int]] = [set() for _ in range(4)]
            self._current_player = None

        else:
            self._stop_timer("trading")
            self._positions.clear()
            self._hand_in_play = base_hand
            # TODO: should be able to do a simple start_round here
            #       need to define and use setup_round method
            self._num_consecutive_rounds += 1
            self._message(f"🏁 round {self._num_consecutive_rounds} has begun")
            self._make_and_set_turn_manager()
            self._next_player()

    async def maybe_set_selected_asking_option_handler(
        self, sid: str, value: int
    ) -> None:
        spot: int = self._get_spot(sid)
        try:
            await self.maybe_set_selected_asking_option(spot, value)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def maybe_unlock_ask_handler(self, spot: int, sid: str) -> None:
        try:
            await self.maybe_unlock_ask(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def ask_for_card_handler(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            await self.ask_for_card(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def _set_selected_asking_option(self, spot: int, value: int) -> None:
        """
        NOTE: logic copy/pasted from base; must update manually
        """
        self._selected_asking_options[spot] = value
        if value:  # selecting asking option
            await self._chambers[spot].deselect_selected()
        await self._emit(
            "set_asking_option", {"value": value or False}, self._get_sid(spot)
        )

    async def maybe_unlock_give_handler(self, spot: int, sid: str) -> None:
        try:
            await self.maybe_unlock_give(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def give_card_handler(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            await self.give_card(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def _set_giving_options(
        self, spot: int, giving_options: Set[int]
    ) -> None:
        super()._set_giving_options(spot, giving_options)
        await self._emit(
            "set_giving_options",
            {"options": list(giving_options), "highlight": True},
            self._get_sid(spot),
        )

    async def _clear_giving_options(self, spot: int) -> None:
        await self._emit(
            "set_giving_options",
            {"options": list(self._giving_options[spot]), "highlight": False},
            self._get_sid(spot),
        )
        super()._clear_giving_options(spot)

    # misc

    async def unlock_handler(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        if self.trading:
            if self._is_asking(spot):
                await self.maybe_unlock_ask_handler(spot, sid)
            elif self._is_giving(spot):
                await self.maybe_unlock_give_handler(spot, sid)
            else:
                await self._emit_alert(
                    "you must select something before attempting to unlock",
                    sid,
                )
        else:
            await self._maybe_unlock_play_handler(spot, sid)

    def lock_handler(self, sid: str) -> None:
        self.lock(self._get_spot(sid))

    async def _unlock(self, spot: int) -> None:
        await asyncio.gather(
            self._emit(
                "set_unlocked", {"unlocked": True}, self._get_sid(spot)
            ),
            self._lock_if_pass_unlocked(spot),
        )
        self._unlocked[spot] = True

    async def lock(self, spot: int) -> None:
        super().lock(spot)
        await self._emit(
            "set_unlocked", {"unlocked": False}, self._get_sid(spot)
        )

    async def _message(self, message: str) -> None:
        # super()._message(message)
        await self._emit_to_server("message", {"message": message})

    # getters

    def _get_sid(self, spot: int) -> str:
        return self._spot_sid_bidict[spot]

    def _get_spot(self, sid: str) -> int:
        return self._spot_sid_bidict.inv[sid]

    def get_user_id(self, sid: str) -> str:
        return self._sid_user_id_dict[sid]

    # setters

    async def _set_name(self, **kwargs) -> None:
        super()._set_name(**kwargs)
        # TODO: make this emit single name plus the spot
        await self._emit_to_players("set_names", {"names": self._names})

    async def _set_hand_in_play(self, hand: Hand) -> None:
        if hand.is_empty or not hand.is_valid:
            raise Exception("hand is empty or invalid wtf ???")  # TODO
        super()._set_hand_in_play(hand)
        await self._emit_to_players(
            "set_hand_in_play",
            {
                "hand_in_play": hand.to_list(),
                "hand_in_play_desc": hand.id_desc,
            },
        )

    async def _set_asker(
        self, spot: int, asker: bool, takes_and_gives: int
    ) -> None:
        await asyncio.gather(
            self._set_takes(spot, takes_and_gives),
            self._set_gives(spot, takes_and_gives),
            self._emit("set_asker", {"asker": asker}, self._get_sid(spot)),
        )

    async def _set_giver(self, spot: int, giver: bool) -> None:
        await self._emit("set_giver", {"giver": giver}, self._get_sid(spot))

    async def _set_takes(self, spot: int, takes: int) -> None:
        super()._set_takes(spot, takes)
        await self._emit("set_takes", {"takes": takes}, self._get_sid(spot))

    async def _set_gives(self, spot: int, gives: int) -> None:
        super()._set_gives(spot, gives)
        await self._emit("set_gives", {"gives": gives}, self._get_sid(spot))

    def _add_to_already_asked(self, spot: int, value: int) -> None:
        super()._add_to_already_asked(spot, value)
        # await self._emit('remove_asking_option', {'value': value}, self._get_sid(spot))

    async def _set_dot_color(self, spot: int, dot_color: str) -> None:
        await self._emit_to_players(
            "set_dot_color", {"spot": spot, "dot_color": dot_color}
        )

    # emitters

    async def _emit(self, *args, **kwargs) -> None:
        await self._server.emit(*args, **kwargs)

    async def _emit_to_players(self, *args, **kwargs):
        """
        Emits to all players by default. Pass in skip_sid with a string
        or a list to skip players.

        The difference between this and _emit_to_server is that the
        latter emits to spectators as well.

        TODO: to should work instead of room
        """
        maybe_skip_sid = kwargs.get("skip_sid")
        if not maybe_skip_sid:
            await asyncio.gather(
                *[
                    self._emit(*args, room=sid, **kwargs)
                    for sid in self._spot_sid_bidict.values()
                ]
            )
        elif isinstance(maybe_skip_sid, str):
            await asyncio.gather(
                *[
                    self._emit(*args, room=sid, **kwargs)
                    for sid in self._spot_sid_bidict.values()
                    if sid != maybe_skip_sid
                ]
            )
        elif isinstance(maybe_skip_sid, list):
            await asyncio.gather(
                *[
                    self._emit(*args, room=sid, **kwargs)
                    for sid in self._spot_sid_bidict.values()
                    if sid not in maybe_skip_sid
                ]
            )
        else:
            raise AssertionError("skip_sid can only be a string or a list")

    async def _emit_to_server(self, *args, **kwargs):
        await self._emit(*args, **kwargs)

    # alerting related methods

    async def _emit_alert(self, alert, sid: str) -> None:
        await self._emit("alert", {"alert": alert}, sid)
