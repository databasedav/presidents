from typing import Callable, Dict, List, Optional, Set, Union, Iterable

from bidict import bidict
from socketio import AsyncServer

from asyncio import gather
import inspect
import re
from time import mktime

from ..game.hand import NotPlayableOnError
from ..utils import spawn_after
from ..services.monitor import HandPlay

# from ..server.server import Server
Server = None

from . import (
    Hand,
    DuplicateCardError,
    FullHandError,
    CardNotInChamberError,
    EmittingChamber,
    # Game,
    base_hand,
    PresidentsError,
)
from .gamee import Game

from datetime import datetime

# TODO: decide what to do for the removal of asking options; and whether
#       or not to remove them
# TODO: spectators should get a completely hidden view of the game being
#       played and maybe if you are friends with another player, you can
#       see that player's cards and stuff like that
# TODO: block receiving user events during autoplay
# TODO: block autoplaying while user event is being processed
# TODO: in general, make sure certain state has actually changed before
#       notifying client
# TODO: ok here is what is gna happen: timer will start server side
#       w 0 delay and then the on_turn acks will be stored in the db
#       for analysis, the timer start time will be sent to the front
#       end so it can determine how much time the player actually has
#       the fact that the player will actually have less time to play
#       will be handled by the fact that they have reserve time and
#       also the fact that they should get a better internet connection, bitch
# TODO: normalize emit event names with frontend
# TODO: add UI elements for takes and gives remaining
# TODO: go through all gathers and consider whether doing things
#       concurrently won't break something
# TODO: whenever concurrently emitting same event to multiple spots,
#       randomly decide order, e.g. not just
#       "for sid in spot_sid_bidict.values()"  or "for spot in range(4)"
# TODO: fix idling on phone bug
# TODO: make base game class async and agnostic to event emittal
#       implementation
# TODO: serialize and store full game state at the start of every round
#       and store all major game state changing actions in a round (e.g.
#       this includes valid hand plays but excludes card clicks) so when
#       assertions are failed (or some other unknown bug), reproduction
#       can be attempted without accessing game actions table

class PySockGame(Game):
    """
    Game that emits events using a python-socketio server.
    """
    def __init__(self, *, name: str, sio, agents: dict, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self._sio = sio
        self._events_counter = agents.get('events_counter')
        self._hand_play_processor = agents.get('hand_play_processor')
        self._chambers: List[EmittingChamber] = [
            EmittingChamber(self._sio) for _ in range(4)
        ]
        self._spot_sid_bidict: bidict = bidict()
        self._user_ids: List[str] = [None for _ in range(4)]
        self.num_spectators: int = 0  # TODO

    # properties

    @property
    def _current_player_sid(self) -> str:
        return self._get_sid(self._current_player)

    # setup related methods

    def set_sio(self, sio) -> None:
        self._sio = sio
        for chamber in self._chambers:
            chamber.set_sio(sio)

    async def add_player_to_spot(
        self, name: str, spot: int, sid: str, user_id: str
    ) -> None:
        super().add_player_to_spot(name, spot, sid=sid)
        self._spot_sid_bidict[spot] = sid
        self._chambers[spot].set_sid(sid)
        self._user_ids[spot] = user_id

    async def remove_player(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        await super().remove_player(spot)
        self._spot_sid_bidict.pop(spot)
        self._chambers[spot].set_sid(None)
        self._user_ids[spot] = None
    
    async def _emit_set_spot(self, spot: int, sid: str) -> None:
        await self._emit('set_spot', {'spot': spot}, room=sid)

    async def _emit_set_num_cards_remaining(self, spot: int, num_cards_remaining: int) -> None:
        await self._emit_to_players('set_num_cards_remaining', {'spot': spot, 'num_cards_remaining': num_cards_remaining})
    
    async def _emit_set_on_turn(self, spot: int, on_turn: bool) -> None:
        try:
            await self._emit('set_on_turn', {'on_turn': on_turn}, room=self._get_sid(spot))
        except KeyError:  # current player is None at round start
            pass
    
    async def _emit_set_dot_color(self, spot: int, dot_color: str) -> None:
        await self._emit_to_players("set_dot_color", {"spot": spot, "dot_color": dot_color})

    async def _emit_set_on_turn_handler(self, spot: int) -> None:
        await gather(
            self._emit(
                "set_on_turn", {"on_turn": True}, room=self._get_sid(spot)
            ),
            self._set_dot_color(spot, "green"),
        )

    async def _emit_set_time(self, which: str, seconds: float, spot: int) -> None:
        payload = {'which': which, 'time': seconds * 1000}
        if spot:
            payload['spot'] = spot
        await self._emit_to_players('set_time', payload)

    async def _emit_set_timer_state(
        self, which: str, state: bool, spot: int, timestamp: datetime
    ) -> None:
        payload = {
            "which": which,
            "state": state,
        }
        if state:
            # accounts for server/client latency
            payload['timestamp'] = mktime(timestamp.timetuple())
        if spot:
            payload["spot"] = spot
        await self._emit_to_players("set_timer_state", payload)

    async def _emit_set_paused(self, paused: bool) -> None:
        await self._emit_to_players('set_paused', {'paused': paused})

    async def emit_full_state(self, sid: str):
        """
        NOTE: these are all raw emits and their logic must be updated
              manually
        """
        spot: int = self._get_spot(sid)
        events = list()
        events.extend(
            [
                self._emit("add_card", {"card": card}, room=sid)
                for card in self._chambers[spot]
            ]
        )
        events.append(self._emit("set_spot", {"spot": spot}, room=sid))
        events.append(
            self._emit(
                "set_names",
                {
                    "names": [
                        "" if name is None else name for name in self._names
                    ]
                },
                room=sid,
            )
        )
        for spot in range(4):
            events.extend(
                [
                    self._emit(
                        "set_dot_color",
                        {"spot": spot, "dot_color": self._dot_colors[spot]},
                        room=sid,
                    ),
                    self._emit(
                        "set_cards_remaining",
                        {
                            "spot": spot,
                            "cards_remaining": self._chambers[spot].num_cards,
                        },
                        room=sid,
                    ),
                    self._emit(
                        "set_time",
                        {
                            "spot": spot,
                            "which": "turn",
                            "time": self._turn_times[spot] * 1000,
                            "start": False,
                        },
                        room=sid,
                    ),
                    self._emit(
                        "set_time",
                        {
                            "spot": spot,
                            "which": "reserve",
                            "time": self._reserve_times[spot] * 1000,
                            "start": False,
                        },
                        room=sid,
                    ),
                ]
            )
        if self._hand_in_play and self._hand_in_play is not base_hand:
            events.append(
                self._emit(
                    "set_hand_in_play",
                    {
                        "hand_in_play": self._hand_in_play.to_list(),
                        "hand_in_play_desc": self._hand_in_play.id_desc,
                    },
                    room=sid,
                )
            )
        if self.is_paused:
            events.append(self._emit("set_paused", {"paused": True}, room=sid))
        if self.trading:
            spot: int = self._get_spot(sid)
            events.extend(
                [
                    self._emit("set_trading", {"trading": True}, room=sid),
                    self._emit(
                        "set_time",
                        {
                            "which": "trading",
                            "time": self._trading_time_remaining * 1000,
                            "start": False,
                        },
                        room=sid,
                    ),
                ]
            )
            if self._is_asker(spot):
                events.append(
                    self._emit("set_asker", {"asker": True}, room=sid)
                )
            else:
                events.append(
                    self._emit("set_giver", {"giver": True}, room=sid)
                )
                if self._giving_options[spot]:
                    events.append(
                        self._emit(
                            "set_giving_options",
                            {
                                "options": list(self._giving_options[spot]),
                                "highlight": True,
                            },
                            room=sid,
                        )
                    )

        await gather(*events)

    # card management related methods

    async def card_handler(self, sid: str, card: int) -> None:
        spot: int = self._get_spot(sid)
        try:
            await self.add_or_remove_card(spot, card)
            # await cast_game_action(...)
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

    async def play_handler(self, sid: str) -> None:
        try:
            await self.maybe_play_current_hand(self._get_spot(sid), sid=sid)
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
        # this is outside the gather because the num_cards was being
        # evaluated before the chamber after removed the cards
        await chamber.remove_cards(hand)
        await gather(
            self.cast_hand_play(hash(hand)),
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
                {"spot": spot, "cards_remaining": chamber.num_cards},
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

    async def unlock_pass_handler(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            await self.maybe_unlock_pass_turn(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def _unlock_pass(self, spot: int) -> None:
        await self._lock_if_unlocked(spot)
        self._pass_unlocked[spot] = True
        await self._emit(
            "set_pass_unlocked",
            {"pass_unlocked": True},
            room=self._get_sid(spot),
        )

    async def _lock_pass(self, spot: int) -> None:
        super()._lock_pass(spot)
        await self._emit(
            "set_pass_unlocked",
            {"pass_unlocked": False},
            room=self._get_sid(spot),
        )

    async def pass_handler(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            await self.maybe_pass_turn(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def _pass_turn(self, spot: int) -> None:
        """
        NOTE: logic copy/pasted from base; must update manually
              adds dot color setting and a fat gather
        """
        assert self._pass_unlocked[spot], "pass called without unlocking"
        self._num_consecutive_passes += 1
        await gather(
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
        await self._emit_to_players("clear_hand_in_play", {})

    # trading related methods

    async def _set_trading(
        self, trading: bool, *, cancel: bool = True
    ) -> None:
        """
        NOTE: logic copy/pasted from base; must update manually
        cancel: whether to cancel the trading timer; this should be
                False when the handling trading timeout 
        """
        self.trading = trading
        await self._emit_to_players("set_trading", {"trading": trading})
        range_4 = range(4)
        if trading:
            await gather(
                *[self._set_dot_color(spot, "red") for spot in range_4],
                self._emit(
                    "set_on_turn",
                    {"on_turn": False},
                    room=self._current_player_sid,
                ),
                self._clear_hand_in_play(),
                self._setup_round(),
                self._set_time("trading", self._trading_time, start=True),
                self._message("💱 trading has begun"),
            )

            # timer related attributes
            self._timers = [None for _ in range_4]
            self._turn_times = [0 for _ in range_4]
            self._turn_time_use_starts = [None for _ in range_4]
            self._reserve_times: List[float] = [
                self._reserve_time for _ in range_4
            ]
            self._reserve_time_use_starts: List[datetime] = [
                None for _ in range_4
            ]

            # game related attributes
            self._current_player = None
            self._hand_in_play = base_hand
            self._num_consecutive_passes: int = 0
            self._finishing_last_played: bool = False
            self._unlocked: List[bool] = [False for _ in range_4]
            self._pass_unlocked: List[bool] = [False for _ in range_4]
        else:  # elif not trading
            await self._stop_timer("trading", cancel=cancel)
            # trading related attributes
            self._selected_asking_options: List[Optional[int]] = [
                None for _ in range_4
            ]
            self._already_asked: List[Set[int]] = [set() for _ in range_4]
            self._waiting: List[bool] = [False for _ in range_4]
            self._giving_options: List[Optional[Set[int]]] = [
                set() for _ in range_4
            ]
            self._gives: List[int] = [0 for _ in range_4]
            self._takes: List[int] = [0 for _ in range_4]
            self._given: List[Set[int]] = [set() for _ in range_4]
            self._taken: List[Set[int]] = [set() for _ in range_4]

            # game related attributes
            self._positions.clear()
            await self.start_round(setup=False)

    async def rank_handler(self, sid: str, rank: int) -> None:
        spot: int = self._get_spot(sid)
        try:
            await self.maybe_set_selected_asking_option(spot, rank)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def maybe_unlock_ask_handler(self, spot: int, sid: str) -> None:
        try:
            await self.maybe_unlock_ask(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def ask_handler(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            await self.ask_for_card(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def _set_selected_asking_option(self, spot: int, rank: int) -> None:
        """
        NOTE: logic copy/pasted from base; must update manually
              old rank is required for 
        """
        old_rank: int = self._selected_asking_options[spot]
        self._selected_asking_options[spot] = rank
        if rank:  # selecting asking option
            await self._chambers[spot].deselect_selected()
        await self._emit(
            "set_asking_option",
            {"old_rank": old_rank, "new_rank": rank},
            room=self._get_sid(spot),
        )

    async def maybe_unlock_give_handler(self, spot: int, sid: str) -> None:
        try:
            await self.maybe_unlock_give(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def give_handler(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            await self.give_card(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def give_card(
        self, spot: int, *, auto_trading: bool = False
    ) -> None:
        """
        NOTE: logic copy/pasted from base; must update manually
              added remaining cards emits for giver and receiver and
              gathers
        """
        if not self._unlocked[spot]:
            # await self.lock(spot)  # TODO doing this should be part of resetting the DOM, say
            raise PresidentsError(
                "you must unlock before giving", permitted=False
            )
        await self._stop_timer("turn", spot)  # stop giving time
        card = self._get_current_hand(spot)[4]
        giver_chamber: Chamber = self._chambers[spot]
        receiver_spot: int = self._get_opposing_position_spot(spot)
        receiver_chamber: Chamber = self._chambers[receiver_spot]
        await gather(
            giver_chamber.remove_card(card), receiver_chamber.add_card(card)
        )
        # separate gathers because chamber must update num_cards
        await gather(
            *[
                self._emit_to_players(
                    "set_cards_remaining",
                    {"spot": spot, "cards_remaining": chamber.num_cards},
                )
                # list comprehensions evaluate in new frame so orig spot
                # is not overwritten here
                for spot, chamber in zip(
                    [spot, receiver_spot], [giver_chamber, receiver_chamber]
                )
            ],
            self._message(
                f"🎁 {self._names[spot]} gives {self._names[receiver_spot]} a card"
            ),
        )
        if self._is_asker(spot):
            self._add_to_given(spot, card)
            await self._decrement_gives(spot, auto_trading=auto_trading)
        elif self._is_giver(spot):
            await gather(
                self._clear_giving_options(spot),
                self._decrement_takes(
                    receiver_spot, auto_trading=auto_trading
                ),
            )
            self._add_to_taken(receiver_spot, card)
            self._waiting[receiver_spot] = False
        await self.lock(spot)

    async def _set_giving_options(
        self, spot: int, giving_options: Set[int]
    ) -> None:
        super()._set_giving_options(spot, giving_options)
        await self._emit(
            "set_giving_options",
            {"options": list(giving_options), "highlight": True},
            room=self._get_sid(spot),
        )

    async def _clear_giving_options(self, spot: int) -> None:
        await self._emit(
            "set_giving_options",
            {"options": list(self._giving_options[spot]), "highlight": False},
            room=self._get_sid(spot),
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

    async def lock_handler(self, sid: str) -> None:
        await self.lock(self._get_spot(sid))

    async def _unlock(self, spot: int) -> None:
        await gather(
            self._emit(
                "set_unlocked", {"unlocked": True}, room=self._get_sid(spot)
            ),
            self._lock_if_pass_unlocked(spot),
        )
        self._unlocked[spot] = True

    async def lock(self, spot: int) -> None:
        super().lock(spot)
        await self._emit(
            "set_unlocked", {"unlocked": False}, room=self._get_sid(spot)
        )

    async def _message(self, message: str) -> None:
        await self._emit_to_players("message", {"message": message})
        super()._message(message)

    # getters

    def _get_sid(self, spot: int) -> str:
        return self._spot_sid_bidict[spot]

    def _get_spot(self, sid: str) -> int:
        return self._spot_sid_bidict.inv[sid]

    # setters

    async def _emit_set_name(self, spot: int, name: str) -> None:
        await self._emit_to_players("set_name", {'spot': spot, 'name': name or ''})

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
        await gather(
            self._set_takes(spot, takes_and_gives),
            self._set_gives(spot, takes_and_gives),
            self._emit(
                "set_asker", {"asker": asker}, room=self._get_sid(spot)
            ),
        )

    async def _set_giver(self, spot: int, giver: bool) -> None:
        await self._emit(
            "set_giver", {"giver": giver}, room=self._get_sid(spot)
        )

    async def _set_takes(self, spot: int, takes: int) -> None:
        super()._set_takes(spot, takes)
        await self._emit(
            "set_takes", {"takes": takes}, room=self._get_sid(spot)
        )

    async def _set_gives(self, spot: int, gives: int) -> None:
        super()._set_gives(spot, gives)
        await self._emit(
            "set_gives", {"gives": gives}, room=self._get_sid(spot)
        )

    def _add_to_already_asked(self, spot: int, value: int) -> None:
        super()._add_to_already_asked(spot, value)
        # await self._emit('remove_asking_option', {'value': value}, self._get_sid(spot))

    async def _emit_set_dot_color(self, spot: int, dot_color: str) -> None:
        await self._emit_to_players(
            "set_dot_color", {"spot": spot, "dot_color": dot_color}
        )

    # emitters

    async def _emit(self, *args, **kwargs) -> None:
        await self._sio.emit(*args, **kwargs)

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
            await gather(
                *[
                    self._emit(*args, room=sid, **kwargs)
                    for sid in self._spot_sid_bidict.values()
                ]
            )
        elif isinstance(maybe_skip_sid, str):
            await gather(
                *[
                    self._emit(*args, room=sid, **kwargs)
                    for sid in self._spot_sid_bidict.values()
                    if sid != maybe_skip_sid
                ]
            )
        elif isinstance(maybe_skip_sid, list):
            await gather(
                *[
                    self._emit(*args, room=sid, **kwargs)
                    for sid in self._spot_sid_bidict.values()
                    if sid not in maybe_skip_sid
                ]
            )
        else:
            raise AssertionError("skip_sid can only be a string or a list")

    # TODO
    async def _emit_to_spectators(self, *args, **kwargs):
        ...

    # TODO
    async def _emit_to_server(self, *args, **kwargs):
        """
        Emits to players and spectators
        """
        ...


    async def cast_event(self, event):
        await self._events_counter.cast(event)

    async def cast_hand_play(self, hand_hash: int):
        await self._hand_play_processor.cast(
            HandPlay(game_id=self.game_id, hand_hash=hand_hash)
        )
    


    # alerting related methods

    async def _emit_alert(self, alert, sid: str) -> None:
        await self._emit("alert", {"alert": alert}, room=sid)
