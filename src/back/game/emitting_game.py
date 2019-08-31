from typing import Callable, Dict, List, Optional, Set, Union, Iterable

from bidict import bidict
from socketio import AsyncServer

import asyncio
import inspect
import re

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



# go through the list of methods that need to be asynced copy pasted
# for all instances of f'self.{method}(' where method is overwritten
# with additional async logic in EmittingGame, prepend 'await' to the
# method call and store the completely transformed method; transform
# all such methods before registering all of them to EmittingGame

ASYNCED_COPY_PASTE_METHODS = [
    'add_or_remove_card',
    'maybe_unlock_play',
    'maybe_play_current_hand',
    '_handle_timeout',
    '_auto_play_or_pass',
    '_start_round',
    'add_player'
]

class EmittingGame(Game):

    def __init__(self, server: Server, **kwargs):
        super().__init__(**kwargs)
        # TODO: server stuff (including emitting should be entirely handled by the Server, which is an AsyncNamespace)
        self._server: Server = server
        self._chambers: List[Optional[EmittingChamber]] = [
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

    async def _add_player_to_spot(self, sid: str, user_id: str, name: str, spot: int) -> None:
        self._chambers[spot].set_sid(sid)
        self._spot_sid_bidict.inv[sid] = spot
        self._sid_user_id_dict[sid] = user_id
        await self._set_name(spot=spot, name=name)
        self.num_players += 1
        # TODO: THIS SHOULD NOT BE HERE.
        if self.num_players == 4:
            await self._start_round()

    def remove_player(self, sid: str) -> None:
        self._spot_sid_bidict.inv.pop(sid)
        self._sid_user_id_dict.pop(sid)
        super().remove_player(self._get_spot(sid))

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
        await chamber.add_cards(cards)
        await self._emit("set_spot", {"spot": spot}, sid)

    # game flow related methods

    async def _next_player(self) -> None:
        try:  # current player is no longer on turn
            await self._emit("set_on_turn", {"on_turn": False},  room=self._current_player_sid))
        except KeyError:  # self._current_player is None on round start
            pass
        self._current_player = spot = next(self._turn_manager)  # TODO this mypy error
        events = list()
        events.append(await self._start_timer(spot=spot, seconds=self._turn_time))
        events.append(await self._message(f"🎲 it's {self._names[spot]}'s turn"))
        events.append(await self._emit_set_on_turn_handler(spot))
        await asyncio.gather(*events)

    async def _emit_set_on_turn_handler(self, spot: int) -> None:
        events = list()
        events.append(self._emit("set_on_turn", {"on_turn": True}, room=self._get_sid(spot)))
        events.append(self._set_dot_color(spot, "green"))
        await asyncio.gather(*events)

    async def _start_timer(self, **kwargs) -> None:
        await self._emit_to_players("set_time", {"spot": kwargs.get('spot'), "time": kwargs.get('seconds') * 1000})
        super()._start_timer(**kwargs)

    async def _stop_timer(self, **kwargs) -> None:
        

    async def _player_finish(self, spot: int) -> None:
        await self._set_dot_color(spot, "purple")
        await self._player_finish_helper(spot)

    async def _player_finish_helper(self, spot: int) -> None:
        assert self._chambers[
            spot
        ].is_empty, "only players with no cards remaining can finish"
        self._positions.append(self._current_player)
        self._turn_manager.remove(self._current_player)
        num_unfinished_players = self._num_unfinished_players
        if num_unfinished_players == 3:
            await self._set_president(spot)
            await self._message(f"🏆 {self._names[spot]} is president 🥇")
            await self._next_player()
        elif num_unfinished_players == 2:
            await self._set_vice_president(spot)
            await self._message(f"🏆 {self._names[spot]} is vice president 🥈")
            await self._next_player()
        else:  # num_unfinished
            await self._set_vice_asshole(spot)
            self._current_player = next(self._turn_manager)
            await self._set_asshole(self._current_player)
            self._positions.append(self._current_player)
            await self._message(
                f"🏆 {self._names[spot]} is vice asshole 🥉 and {self._names[self._current_player]} is asshole 💩"
            )
            await self._initiate_trading()
    
    async def emit_correct_state(self, sid: str):
        spot: int = self._get_spot(sid)
        await self._emit('correct_state', {
            'cards': list(self._chambers[spot]),
            'selected_cards': self._get_current_hand(spot).to_list(),
            'unlocked': self._unlocked[spot],
            'pass_unlocked': self._pass_unlocked[spot]
        }, room=sid)

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

    async def _play_current_hand(
        self, spot: int, *, handle_post: bool = True, **kwargs
    ) -> Hand:
        assert self._unlocked[spot], "play called without unlocking"
        self._stop_timer(spot)
        chamber = self._chambers[spot]
        hand = Hand.copy(chamber.hand)
        events = list()
        # events.append(self.hand_play_agent.cast(
        #     HandPlay(
        #         hand_hash=hash(hand),
        #         sid=kwargs.get("sid", self._get_sid(spot)),
        #         timestamp=kwargs.get("timestamp"),
        #     )
        # ))
        events.append(chamber.remove_cards(hand))
        events.append(self._set_hand_in_play(hand))
        events.append(self._message(f"▶️ {self._names[spot]} played {str(hand)}"))
        events.append(self.lock(spot))
        events.append(self._set_dot_color(spot, "blue"))
        for other_spot in self._get_other_spots(spot, exclude_finished=True):
            events.append(self._set_dot_color(other_spot, "red"))
        events.append(self._emit_to_players(
            "set_cards_remaining",
            {"spot": spot, "cards_remaining": self._chambers[spot].num_cards},
        ))
        await asyncio.gather(*events)
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
        if handle_post:
            await self._post_play_handler(spot)

    async def _post_play_handler(self, spot: int) -> None:
        if self._chambers[spot].is_empty:
            # player_finish takes care of going to the next player
            self._finishing_last_played = True
            await self._player_finish(spot)
        else:
            self._finishing_last_played = False
            await self._next_player()

    async def maybe_unlock_pass_turn(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            await self._maybe_unlock_pass_turn_helper(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def _maybe_unlock_pass_turn_helper(self, spot: int) -> None:
        """
        Copy/paste from base game class with asynced methods.
        """
        if self._is_finished(spot):
            raise PresidentsError(
                "you have already finished this round", permitted=False
            )
        if self._is_current_player(spot):
            if self._hand_in_play is base_hand:
                raise PresidentsError(
                    "you cannot pass when you have the 3 of clubs",
                    permitted=True,
                )
            if self._hand_in_play is None:
                raise PresidentsError("you can play anyhand", permitted=True)
        await self._unlock_pass(spot)

    async def _unlock_pass(self, spot: int) -> None:
        await self._unlock_pass_helper(spot)
        await self._emit(
            "set_pass_unlocked", {"pass_unlocked": True}, self._get_sid(spot)
        )

    async def _unlock_pass_helper(self, spot: int) -> None:
        await self._lock_if_unlocked(spot)
        self._pass_unlocked[spot] = True

    async def _lock_pass(self, spot: int) -> None:
        super()._lock_pass(spot)
        await self._emit(
            "set_pass_unlocked", {"pass_unlocked": False}, self._get_sid(spot)
        )

    async def maybe_pass_turn(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            await self._maybe_pass_turn_helper(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def _maybe_pass_turn_helper(self, spot: int) -> None:
        """
        Copy/paste from base game class with asynced methods.
        """
        if self._is_finished(spot):
            raise PresidentsError(
                "you have already finished this round", permitted=False
            )
        if not self._pass_unlocked[spot]:
            # self._lock_pass(spot)  # TODO doing this should be part of resetting the DOM, say
            raise PresidentsError(
                "you must unlock pass before passing", permitted=False
            )
        if not self._is_current_player(spot):
            raise PresidentsError(
                "you can only pass on your turn", permitted=True
            )
        else:
            await self._pass_turn(spot)

    async def _pass_turn(self, spot):
        await self._pass_turn_helper(spot, handle_post=False)
        await self._set_dot_color(spot, "yellow")
        await self._post_pass_handler_helper()

    async def _pass_turn_helper(
        self, spot: int, handle_post: bool = True
    ) -> None:
        """
        Copy/paste from base game class with asynced methods.
        """
        assert self._pass_unlocked[spot], "pass called without unlocking"
        self._stop_timer(spot)
        await self._lock_pass(spot)
        self._num_consecutive_passes += 1
        await self._message(f"⏭️ {self._names[spot]} passed")
        if handle_post:
            await self._post_pass_handler_helper()

    async def _post_pass_handler_helper(self) -> None:
        # all remaining players passed on a winning hand
        if self._finishing_last_played:
            if self._num_consecutive_passes == self._num_unfinished_players:
                await self._clear_hand_in_play()
                self._finishing_last_played = False
                await self._next_player()
            else:
                await self._next_player()
        # all other players passed on a hand
        elif self._num_consecutive_passes == self._num_unfinished_players - 1:
            await self._clear_hand_in_play()
            self._finishing_last_played = False
            await self._next_player()
        else:
            await self._next_player()

    async def _clear_hand_in_play(self) -> None:
        super()._clear_hand_in_play()
        await self._emit_to_players("clear_hand_in_play")

    # trading related methods

    async def _initiate_trading(self) -> None:
        # TODO: THIS SHOULD NOT BE HERE.
        self._num_consecutive_passes: int = 0
        self._finishing_last_played: bool = False
        self._timers = [None for _ in range(4)]
        self._selected_asking_option: List[Optional[int]] = [
            None for _ in range(4)
        ]
        self._already_asked: List[Set[int]] = [set() for _ in range(4)]
        self._giving_options: List[Optional[Set[int]]] = [
            set() for _ in range(4)
        ]
        self._given: List[Set[int]] = [set() for _ in range(4)]
        self._taken: List[Set[int]] = [set() for _ in range(4)]
        self._current_player = None
        await self._clear_hand_in_play()
        self._positions.clear()
        self._hand_in_play = base_hand
        await self._start_round()
        return
        # ---- below should be here
        super()._initiate_trading()
        for spot in range(4):
            await self._set_dot_color(spot, "red")
        await self._emit_to_players("set_on_turn", {"on_turn": False})

    async def set_selected_asking_option(self, sid: str, value: int) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().set_selected_asking_option(spot, value)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def maybe_unlock_ask(self, spot: int, sid: str) -> None:
        try:
            super().maybe_unlock_ask(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def ask_for_card(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().ask_for_card(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def _select_asking_option(self, spot: int, value: int) -> None:
        super()._select_asking_option(spot, value)
        await self._emit(
            "select_asking_option", {"value": value}, self._get_sid(spot)
        )

    async def _deselect_asking_option(self, spot: int, value: int) -> None:
        super()._deselect_asking_option(spot, value)
        await self._emit(
            "deselect_asking_option", {"value": value}, self._get_sid(spot)
        )

    async def maybe_unlock_give(self, spot: int, sid: str) -> None:
        try:
            super().maybe_unlock_give(spot)
        except PresidentsError as e:
            await self._emit_alert(str(e), sid)

    async def give_card(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().give_card(spot)
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
                await self.maybe_unlock_ask(spot, sid)
            elif self._is_giving(spot):
                await self.maybe_unlock_give(spot, sid)
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
        await self._unlock_helper(spot)
        await self._emit(
            "set_unlocked", {"unlocked": True}, self._get_sid(spot)
        )
    
    async def _unlock_helper(self, spot: int) -> None:
        """
        Copy/paste from base game class with asynced methods.
        """
        await self._lock_if_pass_unlocked(spot)
        self._unlocked[spot] = True

    async def lock(self, spot: int) -> None:
        super().lock(spot)
        await self._emit(
            "set_unlocked", {"unlocked": False}, self._get_sid(spot)
        )

    async def _lock_if_unlocked(self, spot: int) -> None:
        """
        Copy/paste from base game class with asynced methods.
        """
        if self._unlocked[spot]:
            await self.lock(spot)

    async def _lock_if_pass_unlocked(self, spot: int) -> None:
        """
        Copy/paste from base game class with asynced methods.
        """
        if self._pass_unlocked[spot]:
            await self._lock_pass(spot)

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
            raise Exception('hand is empty or invalid wtf ???')  # TODO
        super()._set_hand_in_play(hand)
        await self._emit_to_players(
            "set_hand_in_play",
            {
                "hand_in_play": hand.to_list(),
                "hand_in_play_desc": hand.id_desc,
            },
        )

    async def _set_president(self, spot: int) -> None:
        """
        Copy/paste from base game class with asynced methods.
        """
        await self._set_asker(spot, True, 2)

    async def _set_vice_president(self, spot: int) -> None:
        """
        Copy/paste from base game class with asynced methods.
        """
        await self._set_asker(spot, True, 1)

    async def _set_vice_asshole(self, spot: int) -> None:
        """
        Copy/paste from base game class with asynced methods.
        """
        await self._set_giver(spot, True)

    async def _set_asshole(self, spot: int) -> None:
        """
        Copy/paste from base game class with asynced methods.
        """
        await self._set_giver(spot, True)

    async def _set_asker(
        self, spot: int, asker: bool, takes_and_gives: int
    ) -> None:
        """
        Copy/paste from base game class with asynced methods.
        """
        await self._set_asker_helper(spot, asker, takes_and_gives)
        await self._emit("set_asker", {"asker": asker}, self._get_sid(spot))

    async def _set_asker_helper(
        self, spot: int, asker: bool, takes_and_gives: int
    ) -> None:
        await self._set_takes_remaining(spot, takes_and_gives)
        await self._set_gives_remaining(spot, takes_and_gives)

    async def _set_trading(self, trading: bool) -> None:
        super()._set_trading(trading)
        await self._emit_to_server("set_trading", {"trading": trading})

    async def _set_giver(self, spot: int, giver: bool) -> None:
        await self._emit("set_giver", {"giver": giver}, self._get_sid(spot))

    async def _set_takes_remaining(
        self, spot: int, takes_remaining: int
    ) -> None:
        super()._set_takes_remaining(spot, takes_remaining)
        await self._emit(
            "set_takes_remaining",
            {"takes_remaining": takes_remaining},
            self._get_sid(spot),
        )

    async def _set_gives_remaining(
        self, spot: int, gives_remaining: int
    ) -> None:
        super()._set_gives_remaining(spot, gives_remaining)
        await self._emit(
            "set_gives_remaining",
            {"gives_remaining": gives_remaining},
            self._get_sid(spot),
        )

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
        await self._emit("alert", {"alert": alert}, room=sid)


# go through the list of methods that need to be asynced copy pasted;
# for all instances of f'self.{method}(' where method is overwritten
# with additional async logic in EmittingGame, prepend 'await' to the
# method call and dynamically add the method to EmittingGame

get_async_method_names = lambda _class: [method_tuple[0] for method_tuple in filter(lambda method_tuple: inspect.iscoroutinefunction(method_tuple[1]), dict(_class.__dict__).items())]
patterns = [re.compile(rf'self.{method}(') for method in get_async_method_names(EmittingGame)] + [re.compile(rf'chamber.{method}(') for method in get_async_method_names(EmittingChamber)]

for method in ASYNCED_COPY_PASTE_METHODS:
    method_str = inspect.getsource(eval(f'Game.{method}')).lstrip()
    method_str = 'async ' + method_str
    # prepend await to all async overwritten methods
    for pattern in patterns: 
        if pattern.pattern in method_str: 
            method_str = pattern.sub(f'await {pattern.pattern}', method_str)
    exec(method_str)
    setattr(EmittingGame, method, eval(method))
