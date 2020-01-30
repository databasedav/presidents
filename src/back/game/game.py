import random
from itertools import cycle
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    Set,
    Union,
)
from datetime import datetime

import numpy as np

from .hand import Hand, DuplicateCardError, FullHandError, NotPlayableOnError
from .chamber import Chamber, CardNotInChamberError
from .utils import rank_articler
from ..utils import NoopTimer
import logging


from uuid import uuid4

# logger = logging.getLogger(__name__)


# TODO: nice way to remove asking options after takes are exhausted
# TODO: deal with mypy's treatment of nonetypes being passed into
#       functions that do not take them
# TODO: make Game JSON-serializable
# TODO: make class more manageable (or not)
# TODO: can unlock if the unlocked action can potentially be taken (i.e.
#       when it is their turn); else, cannot unlock
# TODO: shuffle player spots after every round
#       uncommented asserts are for mypy
# TODO: asserts should not be meaningless; if a funtion is only called
#       from one place it doesn't make sense to check a bunch of things
#       that must have been true in the first place; or is it?
# TODO: drop support for eventlet timer; actually maybe don't?
# TODO: add notes to point out methods that are manually async
#       overwritten


class Game:
    """
    Represents a 'game' of presidents. Operates on 'spots' attempting
    confirmation/allowal of certain moves (e.g. unlocking play,
    unlocking pass, etc.), and then actually carrying out those moves
    and changing the game state as necessary.
    """

    TURN_TIME = 30
    RESERVE_TIME = 60
    TRADING_TIME = 90
    GIVING_TIME = 10

    def __init__(
        self,
        *,
        timer: Callable = NoopTimer.timer,
        turn_time: float = TURN_TIME,
        reserve_time: float = RESERVE_TIME,
        trading_time: float = TRADING_TIME,
        giving_time: float = GIVING_TIME,
    ) -> None:

        range_4 = range(4)  # software engineering

        # instance related attributes
        self.game_id = uuid4()
        self.num_players: int = 0
        self._num_consecutive_rounds: int = 0
        self._times_reset: int = 0

        # timer related attributes
        # timer should be function that returns a non-blocking timer
        # with four arguments: time to wait, function to call after
        # waiting, *args, and **kwargs for said function; this timer
        # must also have a cancel method which suspends the timer; see
        # eventlet.greenthread.spawn_after for an example of this
        self._timer: Callable = timer
        # all spot timers (turn, including playing and giving, and
        # reserve) are all stored here; only trading timer is separate
        self._timers: List = [None for _ in range_4]
        self._turn_time: float = turn_time
        # these turn time lists are used for both playing and giving
        self._turn_times: List[float] = [0 for _ in range_4]  # remaining
        self._turn_time_use_starts: List[datetime] = [None for _ in range_4]
        self._reserve_time: float = reserve_time
        # remaining
        self._reserve_times: List[float] = [reserve_time for _ in range_4]
        self._reserve_time_use_starts: List[datetime] = [None for _ in range_4]
        self._trading_timer = None
        self._trading_time = trading_time
        self._trading_time_remaining = trading_time
        self._trading_time_start: datetime = None
        self._giving_time = giving_time
        self._paused_timers = list()

        # setup and ID related attributes
        self._open_spots: Set[int] = {i for i in range_4}
        self._names: List[str] = [None for _ in range_4]

        # game related attributes
        self._turn_manager: TurnManager = None
        self._current_player: int = None
        self._chambers: List[Chamber] = [Chamber() for _ in range_4]
        # when hand in play is base_hand, only the 3 of clubs can be
        # played on it; when it is None, anyhand can be played on it
        self._hand_in_play: Union[BaseHand, Hand] = base_hand
        self._num_consecutive_passes: int = 0
        self._finishing_last_played: bool = False
        self._positions: List[int] = list()
        self._unlocked: List[bool] = [False for _ in range_4]
        self._pass_unlocked: List[bool] = [False for _ in range_4]

        # trading related attributes
        self.trading: bool = False
        self._selected_asking_options: List[Optional[int]] = [
            None for _ in range_4
        ]
        self._already_asked: List[Set[int]] = [set() for _ in range_4]
        self._waiting: List[bool] = [False for _ in range_4]
        self._giving_options: List[Set[int]] = [set() for _ in range_4]
        self._gives = [0 for _ in range_4]
        self._takes = [0 for _ in range_4]
        self._given = [set() for _ in range_4]
        self._taken = [set() for _ in range_4]

    def reset(
        self,
        *,
        timer: Optional[Callable] = None,
        turn_time: Optional[float] = None,
        reserve_time: float = 0,
    ):
        """
        Resetting maintains timer and reserve time settings unless
        provided new ones.
        """
        # TODO: p sure this is missing some attributes
        range_4 = range(4)
        # instance related attributes
        self.num_players = 0
        self._num_consecutive_rounds = 0
        # timer related attributes
        self._timer = timer or self._timer
        self._timers = [None for _ in range_4]
        self._turn_time = turn_time or self._turn_time
        self._turn_times = [None for _ in range_4]
        self._turn_time_use_starts = [None for _ in range_4]
        self._reserve_time = reserve_time or self._reserve_time
        self._reserve_times = [self._reserve_time for _ in range_4]
        self._reserve_time_use_starts = [None for _ in range_4]
        # setup and ID related attributes
        self._open_spots = {i for i in range_4}
        self._names = [None for _ in range_4]
        # game related attributes
        self._turn_manager = None
        self._current_player = None
        self._chambers = [Chamber() for _ in range_4]
        self._hand_in_play = None
        self._num_consecutive_passes = 0
        self._finishing_last_played = False
        self._positions = list()
        self._unlocked = [False for _ in range_4]
        self._pass_unlocked = [False for _ in range_4]
        # trading related attributes
        self.trading = False
        self._selected_asking_options = [None for _ in range_4]
        self._already_asked = [set() for _ in range_4]
        self._waiting = [False for _ in range_4]
        self._giving_options = [set() for _ in range_4]
        self._gives = [0 for _ in range_4]
        self._takes = [0 for _ in range_4]
        self._given = [set() for _ in range_4]
        self._taken = [set() for _ in range_4]

        self._times_reset += 1

    # properties

    @property
    def is_empty(self) -> bool:
        return len(self._open_spots) == 4

    @property
    def is_full(self) -> bool:
        return not bool(self._open_spots)

    @property
    def is_paused(self) -> bool:
        return bool(self._paused_timers)

    @property
    def is_started(self) -> bool:
        return bool(self._num_consecutive_rounds)

    @property
    def _num_unfinished_players(self) -> int:
        assert self._turn_manager is not None
        return self._turn_manager._num_unfinished_players

    @property
    def _no_takes_or_gives(self) -> bool:
        return not bool(sum(self._takes) + sum(self._gives))

    def _set_up_testing_base(
        self, *, deck: List[Iterable[int]] = None
    ) -> None:
        """
        Adds players and starts the round.
        """
        assert self.is_empty, "game must be empty to set up testing base"
        for spot in range(4):
            self._add_player_to_spot(f"player{spot}", spot)
        self.start_round(setup=True, deck=deck)

    def _get_game_to_trading(self) -> None:
        assert self._current_player is not None
        while not self.trading:
            spot: int = self._current_player
            chamber = self._chambers[spot]
            assert chamber is not None
            card: int = chamber._get_min_card()
            if card not in chamber.hand:
                self.add_or_remove_card(spot, card)
            try:
                self.maybe_unlock_play(spot)
            except PresidentsError:
                pass
            if self._unlocked[spot]:
                try:
                    self.maybe_play_current_hand(spot)
                except PresidentsError:
                    pass
            else:
                self._unlock_pass(spot)
                self._pass_turn(spot)

    # setup related methods

    def _rand_open_spot(self) -> int:
        """
        Returns random open spot. Should not happen when there are no
        open spots.
        """
        assert self._open_spots
        return random.choice(tuple(self._open_spots))

    def _add_player_to_spot(self, name: str, spot: int) -> None:
        assert self._names[spot] is None, f"player already in spot {spot}"
        self._open_spots.remove(spot)
        self._set_name(spot, name)
        self.num_players += 1

    def add_player(self, name: str, **kwargs) -> None:
        self._add_player_to_spot(
            name=name, spot=self._rand_open_spot(), **kwargs
        )

    def remove_player(self, spot: int) -> None:
        self._open_spots.add(spot)
        self._set_name(spot, None)
        self.num_players -= 1

    def _make_shuffled_deck(self) -> np.ndarray:
        return np.sort(np.random.permutation(range(1, 53)).reshape(4, 13))

    def _deal_cards(self, *, deck: List[Iterable[int]] = None) -> None:
        for spot, cards in enumerate(deck or self._make_shuffled_deck()):
            chamber: Chamber = self._chambers[spot]
            chamber.reset()
            chamber.add_cards(cards)

    def _make_and_set_turn_manager(self, testing: bool = False) -> None:
        decks = self._get_decks_from_chambers(testing)
        # get which deck has the 3 of clubs
        toc_index = np.where(decks == 1)[0][0]
        self._turn_manager = TurnManager(toc_index)

    # game flow related methods

    # TODO
    def _setup_round(self, *, deck: List[Iterable[int]] = None):
        assert self.num_players == 4, "four players required to start round"
        self._deal_cards(deck=deck)

    def start_round(
        self,
        *,
        setup: bool,
        deck: List[Iterable[int]] = None,
        testing: bool = False,
    ) -> None:
        if setup:
            self._setup_round(deck=deck)
        self._num_consecutive_rounds += 1
        self._make_and_set_turn_manager(testing)
        for spot in range(4):
            self._set_time("reserve", self._reserve_time, spot)
        self._message(f"🏁 round {self._num_consecutive_rounds} has begun")
        self._next_player()

    def _next_player(self) -> None:
        self._current_player = next(self._turn_manager)  # TODO this mypy error
        self._set_time("turn", self._turn_time, self._current_player, True)
        self._message(f"🎲 it's {self._names[self._current_player]}'s turn")

    def _set_time(
        self, which: str, seconds: float, spot: int = None, start: bool = False
    ):
        """
        Stores remaining time for turns (includes playing time, reserve
        time, and giving time) and for trading; does not start the timer
        by default. Spot must be given if setting turn times.
        """
        assert which in ["turn", "reserve", "trading"]
        if which == "turn":
            assert spot is not None
            self._turn_times[spot] = seconds
        elif which == "reserve":
            assert spot is not None
            self._reserve_times[spot] = seconds
        elif which == "trading":
            assert spot is None
            self._trading_time_remaining = seconds

        if start:
            self._start_timer(which, spot)

    def _start_timer(self, which: str, spot: int = None) -> None:
        """
        Uses the remaining time.
        """
        now = datetime.utcnow()
        assert which in ["turn", "reserve", "trading"]
        if which == "turn":
            assert spot is not None
            self._turn_time_use_starts[spot] = now
            self._timers[spot] = self._timer(
                self._turn_times[spot],
                self._handle_playing_timeout
                if not self.trading
                else self._handle_giving_timeout,
                spot,
            )
        elif which == "reserve":
            assert spot is not None
            self._reserve_time_use_starts[spot] = now
            self._timers[spot] = self._timer(
                self._reserve_times[spot], self._handle_playing_timeout, spot
            )
        elif which == "trading":
            self._trading_time_start = now
            self._trading_timer = self._timer(
                self._trading_time_remaining, self._handle_trading_timeout
            )

    def _set_timer_state(self, *args):
        pass  # this does something in EmittingGame

    def _stop_timer(
        self, which: str, spot: int = None, *, cancel: bool = True
    ) -> None:
        """
        Stopping timers simply does what ought to happen when a timer is
        no longer needed. Stopping turn and trading timers resets them
        to their defaults, 0 and trading_time, respectively. Stopping
        the reserve timer decreases the reserve time.

        Stopping a timer does not store it to be restarted; this
        behavior is handled by pausing timers. Timer starts are removed.
        """
        now: datetime = datetime.utcnow()
        assert which in ["turn", "reserve", "trading"]
        self._set_timer_state(which, False, spot)
        if which == "turn":
            assert spot is not None
            # if a timeout handler is calling this, cancelling the timer
            # is a horrible, horrible bug; but we fixed it bois
            if cancel and self._timers[spot] is not None:
                self._timers[spot].cancel()
            # can delete timer even when not cancelling since this only
            # happens when a timeout handler is handling, i.e. said
            # timer has carried out its purpose and cancelling breaks
            # desired behavior (also the timer won't be garbage
            # collected while it is doing handling)
            self._timers[spot] = None
            self._set_time("turn", 0, spot)
            self._turn_time_use_starts[spot] = None
        elif which == "reserve":
            assert spot is not None
            if cancel and self._timers[spot] is not None:
                self._timers[spot].cancel()
            self._timers[spot] = None
            time_used = (
                now - self._reserve_time_use_starts[spot]
            ).total_seconds()
            self._set_time(
                # need the max statement since this function is used during
                # reserve time timeouts
                "reserve",
                max(0, self._reserve_times[spot] - time_used),
                spot,
            )
            self._reserve_time_use_starts[spot] = None
        elif which == "trading":
            assert spot is None
            if cancel and self._trading_timer is not None:
                self._trading_timer.cancel()
            self._trading_timer = None
            self._set_time("trading", self._trading_time)
            self._trading_time_start = None

    def _pause_timers(self) -> None:
        """
        Pausing all timers is different from stopping them; pausing only 
        occurs when there is some issue that requires the game to be
        paused, a player leaving in the middle of the game, say. Pausing
        will store the remaining time for all active timers in their
        appropriate attributes.

        Pausing is global; cannot pause individual timers.
        """
        now: datetime = datetime.utcnow()
        if not self.trading:
            spot: int = self._current_player
            # assert self._timers[spot]
            # both turn and reserve timers stored in timers
            self._timers[spot].cancel()
            self._timers[spot] = None

            if not self._is_using_reserve_time(spot):
                time_used = (
                    now - self._turn_time_use_starts[spot]
                ).total_seconds()
                self._turn_time_use_starts[spot] = None
                self._set_time(
                    "turn", self._turn_times[spot] - time_used, spot
                )
                self._paused_timers.append(self._start_timer("turn", spot))
            else:
                time_used = (
                    now - self._reserve_time_use_starts[spot]
                ).total_seconds()
                self._reserve_time_use_starts[spot] = None
                self._set_time(
                    "reserve", self._reserve_times[spot] - time_used, spot
                )
                self._paused_timers.append(self._start_timer("reserve", spot))
        else:  # elif self.trading
            self._trading_timer.cancel()
            self._trading_timer = None
            time_used = (now - self._trading_time_start).total_seconds()
            self._set_time("trading", self._trading_time_remaining - time_used)
            self._trading_time_start = None
            self._paused_timers.append(self._start_timer("trading"))

            # giving timers
            for spot in self._get_asshole_and_vice_asshole():
                if not self._timers[spot]:  # no active giving timer
                    continue
                self._timers[spot].cancel()
                self._timers[spot] = None
                time_used = (
                    now - self._turn_time_use_starts[spot]
                ).total_seconds()
                # turn time objects are used for for giving times
                self._set_time(
                    "turn", self._turn_times[spot] - time_used, spot
                )
                self._turn_time_use_starts[spot] = None
                self._paused_timers.append(self._start_timer("turn", spot))

    def _resume_timers(self) -> None:
        for timer in self._paused_timers:
            timer()
        self._paused_timers.clear()

    def _handle_playing_timeout(self, spot: int) -> None:
        """
        Handles turn time and reserve time timing out.
        """
        if not self._is_using_reserve_time(spot):  # was using turn time
            self._stop_timer("turn", spot, cancel=False)
            reserve_time: float = self._reserve_times[spot]
            if reserve_time:
                # start reserve time
                self._set_time("reserve", reserve_time, spot, True)
            else:
                self._auto_play_or_pass(spot)
        else:  # was using reserve time
            self._stop_timer("reserve", spot, cancel=False)
            self._auto_play_or_pass(spot)

    def _handle_giving_timeout(self, spot) -> None:
        self._stop_timer("turn", spot, cancel=False)
        self._auto_give(spot)

    def _handle_trading_timeout(self) -> None:
        # TODO:
        # account for the number of cards the askers have remaining to
        # give and then silently do all the operations that snatch and
        # exchange the appropriate cards from the appropriate players
        if not self._no_takes_or_gives:
            self._auto_trade()
        self._set_trading(False, start=False, cancel=False)
        self.start_round(setup=False)

    def _auto_play_or_pass(self, spot: int) -> None:
        """
        For EmittingGame, client cannot see the server auto playing for
        them, besides any non-played currently selected cards being
        individually reselected at the end. Accomplishes this by
        explicitly calling base class methods.

        TODO: the above actually doesn't work; need solution for doing
              things without the client seeing it.
        """
        assert self._current_player == spot, f"it is not spot {spot}'s turn"

        if self._hand_in_play not in [base_hand, None]:
            self.maybe_unlock_pass_turn(spot)
            self.maybe_pass_turn(spot)  # locks pass
            return

        chamber: Chamber = self._chambers[spot]
        currently_selected_cards: List[int] = chamber.hand.to_list()
        if currently_selected_cards:  # not empty list
            chamber.deselect_selected()

        # min card will be 1 if playing on base hand
        self.add_or_remove_card(spot, chamber._get_min_card())
        self.maybe_unlock_play(spot)
        self.maybe_play_current_hand(spot, timestamp=datetime.utcnow())

        # reselect spot's selected cards
        for card in currently_selected_cards:  # could be empty list
            try:
                self.add_or_remove_card(spot, card)
            # one of the selected cards was auto played
            except PresidentsError:
                pass

    def _auto_give(self, spot) -> None:
        chamber: Chamber = self._chambers[spot]
        currently_selected_cards: List[int] = chamber.hand.to_list()
        if currently_selected_cards:
            chamber.deselect_selected()

        self.add_or_remove_card(spot, min(self._giving_options[spot]))
        self.maybe_unlock_give(spot)
        self.give_card(spot)

        # reselect giver's selected cards
        for card in currently_selected_cards:  # could be empty list
            try:
                self.add_or_remove_card(spot, card)
            # one of the selected cards was auto given
            except CardNotInChamberError:
                pass

    def _auto_trade(self) -> None:
        # TODO: only auto trade for a single spot so pres and vice pres
        #       can be done concurrently
        for spot in self._get_president_and_vice_president():
            if not self._has_gives(spot) and not self._has_takes(spot):
                continue

            chamber: Chamber = self._chambers[spot]
            currently_selected_cards: List[int] = chamber.hand.to_list()
            if currently_selected_cards:  # not empty list
                chamber.deselect_selected()

            for _ in range(self._gives[spot]):  # give before u take
                # get the lowest card that can be given
                for card in chamber:
                    if card not in self._taken[spot]:
                        break
                self.add_or_remove_card(spot, card)
                self.maybe_unlock_give(spot)
                self.give_card(spot, auto_trading=True)

            # reselect asker's selected cards
            for card in currently_selected_cards:  # could be empty list
                try:
                    self.add_or_remove_card(spot, card)
                # one of the selected cards was auto given
                except CardNotInChamberError:
                    pass

            # deselect to-be-asked's selected cards if exists
            if self._has_takes(spot):
                asked_spot: int = self._get_opposing_position_spot(spot)
                asked_chamber: Chamber = self._chambers[asked_spot]
                asked_currently_selected_cards = asked_chamber.hand.to_list()
                if asked_currently_selected_cards:
                    asked_chamber.deselect_selected()
            else:
                continue

            for _ in range(self._takes[spot]):
                # iterate through ranks, highest to lowest, asking if
                # has not already been asked
                for value in range(13, 0, -1):
                    if self._is_already_asked(spot, value):
                        continue

                    self.maybe_set_selected_asking_option(spot, value)
                    self.maybe_unlock_ask(spot)
                    # requires auto trading argument that
                    self.ask_for_card(spot)
                    if not self._is_waiting(spot):  # asked doesn't have rank
                        continue
                    else:  # have asked give lowest allowed card to asker
                        self.add_or_remove_card(
                            asked_spot, min(self._giving_options[asked_spot])
                        )
                        self.maybe_unlock_give(asked_spot)
                        self.give_card(asked_spot, auto_trading=True)
                        break

            # reselect asked's selected cards
            for card in asked_currently_selected_cards:  # could be empty list
                try:
                    self.add_or_remove_card(asked_spot, card)
                # one of the selected cards was auto given
                except CardNotInChamberError:
                    pass

        assert self._no_takes_or_gives

    def _player_finish(self, spot: int) -> None:
        assert self._chambers[
            spot
        ].is_empty, "only players with no cards remaining can finish"
        self._positions.append(self._current_player)
        self._turn_manager.remove(self._current_player)
        num_unfinished_players = self._num_unfinished_players
        if num_unfinished_players == 3:
            self._set_president(spot)
            self._message(f"🏆 {self._names[spot]} is president 🥇")
            self._next_player()
        elif num_unfinished_players == 2:
            self._set_vice_president(spot)
            self._message(f"🏆 {self._names[spot]} is vice president 🥈")
            self._next_player()
        else:  # num_unfinished
            self._set_vice_asshole(spot)
            self._current_player = next(self._turn_manager)
            self._set_asshole(self._current_player)
            self._positions.append(self._current_player)
            self._message(
                f"🏆 {self._names[spot]} is vice asshole 🥉 and {self._names[self._current_player]} is asshole 💩"
            )
            self._set_trading(True)

    # card control related methods

    def add_or_remove_card(self, spot: int, card: int) -> None:
        if not self.trading and self._is_finished(spot):
            raise PresidentsError(
                "you have already finished this round", permitted=False
            )
        chamber: Chamber = self._chambers[spot]
        # EAFP is a magnitude faster than LBYL here
        try:
            chamber.select_card(card)
            if self._is_asking(spot):
                self._set_selected_asking_option(spot, None)
            self._lock_if_unlocked(spot)
        except CardNotInChamberError:
            raise PresidentsError("you don't have this card", permitted=False)
        except DuplicateCardError:
            # such an error can only occur if check passes
            chamber.deselect_card(card, check=False)
            self._lock_if_unlocked(spot)
        except FullHandError:
            raise PresidentsError("your current hand is full", permitted=True)

    def store_hand(self, spot: int) -> None:
        """
        Stores current hand. Does not deselect cards after storing, but
        TODO this behavior is controllable by the player.
        """
        if self._is_finished(spot):
            raise PresidentsError(
                "you have already finished this round", permitted=False
            )
        chamber: Chamber = self._chambers[spot]
        chamber.add_hand(chamber.hand)
        # frontend maintains a map from combo (either double, triple,
        # fullhouse straight, bomb, or selected) to the hands that
        # correspond; so need to

    # TODO: this is specifically for removing a particular stored hand
    #       and requires additions to the chamber; support by end of 2020
    def remove_stored_hand(self, spot: int, hand):
        ...

    # playing and passing related methods

    def maybe_unlock_play(self, spot: int):
        """
        Unlocking is allowed as long as one's current hand can be played
        on the current hand in play. Locking updates automatically as
        the hand in play changes.
        """
        if self._is_finished(spot):
            raise PresidentsError(
                "you have already finished this round", permitted=False
            )
        self._lock_if_pass_unlocked(spot)
        hand = self._get_current_hand(spot)
        if hand.is_empty:
            raise PresidentsError(
                "you must add cards before attempting to unlock",
                permitted=True,
            )
        if not hand.is_valid:
            raise PresidentsError(
                "you can't play invalid hands", permitted=True
            )
        hip = self._hand_in_play
        if hip is base_hand:  # start of the game
            if self._is_current_player(spot):  # player with 3 of clubs
                if 1 not in hand:  # card 1 is the 3 of clubs
                    raise PresidentsError(
                        "the first hand must contain the 3 of clubs",
                        permitted=True,
                    )
                else:  # 1 in hand
                    # anyhand with the 3 of clubs is ok
                    self._unlock(spot)
            else:
                # other players (without the 3 of clubs) can unlock
                # whatever hand they want
                self._unlock(spot)
        elif hip is None:  # current player won last hand and can play anyhand
            self._unlock(spot)
        else:
            try:
                if hand > hip:
                    self._unlock(spot)
                else:
                    raise PresidentsError(
                        "your current hand is weaker than the hand in play",
                        permitted=True,
                    )
            except NotPlayableOnError as e:
                raise PresidentsError(str(e), permitted=True)

    def maybe_play_current_hand(self, spot: int, **kwargs) -> None:
        if self._is_finished(spot):
            raise PresidentsError(
                "you have already finished this round", permitted=False
            )
        if not self._unlocked[spot]:
            # self.lock(spot)  # TODO doing this should be part of resetting the DOM, say
            raise PresidentsError(
                "you must unlock before playing", permitted=False
            )
        if not self._is_current_player(spot):
            raise PresidentsError(
                "you can only play a hand on your turn", permitted=True
            )
        else:
            self._play_current_hand(spot, **kwargs)

    def _play_current_hand(self, spot: int) -> Hand:
        """
        In this class' context, playing a hand means only to place the
        hand in play while appropriately changing the state such that
        the hand and the cards that it consists in only exist as the
        hand in play; playing a hand does not mean taking care of game
        flow related things like moving on to the next player or
        finishing a player (this is taken care of by the post play
        handler.)

        NOTE: this method is kinda copy/pasted in EmittingGame and must
              be manually updated there if any changes are made here.
        """
        assert self._unlocked[spot], "play called without unlocking"
        self._stop_timer(
            "turn" if not self._is_using_reserve_time(spot) else "reserve",
            spot,
        )
        chamber = self._chambers[spot]
        hand = Hand.copy(chamber.hand)
        chamber.remove_cards(hand)
        self._set_hand_in_play(hand)
        self._message(f"▶️ {self._names[spot]} played {str(hand)}")
        self.lock(spot)
        self._num_consecutive_passes = 0
        # lock others if their currently unlocked hand should no longer be unlocked
        for other_spot in self._get_other_spots(spot, exclude_finished=True):
            if self._unlocked[other_spot]:
                try:
                    if self._get_current_hand(other_spot) < self._hand_in_play:
                        self.lock(other_spot)
                # occurs either when base_hand is the hand in play since
                # anything can be unlocked or when a bomb is played on a
                # non-bomb that other players have unlocked on
                except NotPlayableOnError:
                    self.lock(other_spot)
        self._post_play_handler(spot)

    def _post_play_handler(self, spot: int) -> None:
        if self._chambers[spot].is_empty:
            # player_finish takes care of going to the next player
            self._finishing_last_played = True
            self._player_finish(spot)
        else:
            self._finishing_last_played = False
            self._next_player()

    def maybe_unlock_pass_turn(self, spot: int) -> None:
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
        self._unlock_pass(spot)

    def _unlock_pass(self, spot: int) -> None:
        self._lock_if_unlocked(spot)
        self._pass_unlocked[spot] = True

    def _lock_pass(self, spot: int) -> None:
        self._pass_unlocked[spot] = False

    def maybe_pass_turn(self, spot: int) -> None:
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
            self._pass_turn(spot)

    def _pass_turn(self, spot: int) -> None:
        assert self._pass_unlocked[spot], "pass called without unlocking"
        self._num_consecutive_passes += 1
        self._stop_timer(
            "turn" if not self._is_using_reserve_time(spot) else "reserve",
            spot,
        )
        self._lock_pass(spot)
        self._message(f"⏭️ {self._names[spot]} passed")
        self._post_pass_handler()

    def _post_pass_handler(self) -> None:
        # all remaining players passed on a winning hand
        if self._finishing_last_played:
            if self._num_consecutive_passes == self._num_unfinished_players:
                self._clear_hand_in_play()
                self._finishing_last_played = False
                self._next_player()
            else:
                self._next_player()
        # all other players passed on a hand
        elif self._num_consecutive_passes == self._num_unfinished_players - 1:
            self._clear_hand_in_play()
            self._finishing_last_played = False
            self._next_player()
        else:
            self._next_player()

    def _clear_hand_in_play(self) -> None:
        self._hand_in_play = None

    # trading related methods

    def _set_trading(self, trading: bool) -> None:
        """
        Handles due diligence for both starting and ending trading.
        """
        self.trading = trading
        # TODO: the below don't set all the required attributes
        if trading:
            self._start_timer("trading")
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
            self._clear_hand_in_play()
            self._deal_cards()
            self._message("💱 trading has begun")
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

    def maybe_set_selected_asking_option(self, spot: int, value: int) -> None:
        if not self._is_asker(spot):
            raise PresidentsError("you are not an asker", permitted=False)
        if not 1 <= value <= 13:
            raise PresidentsError(
                "you cannot ask for this value", permitted=False
            )
        if self._is_already_asked(spot, value):
            raise PresidentsError(
                f"{self._names[self._get_opposing_position_spot(spot)]} doesn't have any cards of this rank",
                permitted=False,  # already asked should be unselectable
            )
        self.lock(spot)
        self._set_selected_asking_option(
            spot,
            None if value == self._selected_asking_options[spot] else value,
        )

    def maybe_unlock_ask(self, spot: int) -> None:
        if not self.trading:
            raise PresidentsError("trading is not ongoing", permitted=False)
        if not self._is_asker(spot):
            raise PresidentsError("you are not an asker", permitted=False)
        if self._is_waiting(spot):
            raise PresidentsError(
                "you cannot ask while waiting for a response", permitted=True
            )
        if not self._has_takes(spot):
            # permitting this one means the interfaces need not block
            # unlocking even if it knows that no takes since potentially
            # unlocking should be generally allowed when the error is
            # caused by the rules of presidents itself
            raise PresidentsError(
                "you have no takes remaining", permitted=True
            )
        # selected_asking_option is None if no trading option is selected
        if not self._selected_asking_options[spot]:
            raise PresidentsError(
                "you must select an asking option before attempting to unlock",
                permitted=True,
            )
        else:
            self._unlock(spot)

    def ask_for_card(self, spot: int) -> None:
        if not self.trading:
            raise PresidentsError("trading is not ongoing", permitted=False)
        if not self._is_asker(spot):
            raise PresidentsError("you are not an asker", permitted=False)
        if not self._unlocked[spot]:
            # self.lock(spot)  # TODO doing this should be part of resetting the DOM, say
            raise PresidentsError(
                "you must unlock before asking", permitted=False
            )
        # TODO: remove trading options when takes run out
        value: int = self._selected_asking_options[spot]
        articled_rank: str = rank_articler(value)
        asked_spot: int = self._get_opposing_position_spot(spot)
        self._message(
            f"❓ {self._names[spot]} asks {self._names[asked_spot]} for {articled_rank}"
        )
        # chamber for asked
        chamber = self._chambers[asked_spot]
        giving_options = {
            card
            for card in range((value - 1) * 4 + 1, value * 4 + 1)
            if card in chamber and card not in self._given[spot]
        }

        self.lock(spot)  # lock whether or not there are giving options
        if not giving_options:
            self._message(
                f"❎ {self._names[asked_spot]} does not have such a card"
            )
            self._add_to_already_asked(spot, value)
        else:
            self._set_giving_options(asked_spot, giving_options)
            self._wait_for_reply(spot, asked_spot)

    def _set_selected_asking_option(self, spot: int, rank: int) -> None:
        self._selected_asking_options[spot] = rank
        if rank:  # selecting asking option
            self._chambers[spot].deselect_selected()

    def _wait_for_reply(self, asker_spot: int, asked_spot: int) -> None:
        self._set_time("turn", self._giving_time, asked_spot, True)
        self._set_selected_asking_option(asker_spot, None)
        self._waiting[asker_spot] = True

    def maybe_unlock_give(self, spot: int) -> None:
        if not self.trading:
            raise PresidentsError("trading is not ongoing", permitted=False)
        if self._is_asker(spot) and not self._has_gives(spot):
            raise PresidentsError(
                "you have no gives remaining", permitted=True
            )
        hand: Hand = self._get_current_hand(spot)
        if hand.is_empty:
            raise PresidentsError(
                "you must add cards before attempting to unlock",
                permitted=True,
            )
        # TODO: add ability to give valid/invalid 2 card hand
        if not hand.is_single:
            raise PresidentsError("you can only give singles", permitted=True)
        card: int = hand[4]
        if self._is_giver(spot):
            if card in self._giving_options[spot]:
                self._unlock(spot)
            else:
                raise PresidentsError(
                    "you can only give a highlighted option", permitted=True
                )
        elif self._is_asker(spot):
            if card in self._taken[spot]:
                raise PresidentsError(
                    "you cannot give a card you took", permitted=True
                )
            else:
                self._unlock(spot)

    def give_card(self, spot: int, *, auto_trading: bool = False) -> None:
        if not self._unlocked[spot]:
            # self.lock(spot)  # TODO doing this should be part of resetting the DOM, say
            raise PresidentsError(
                "you must unlock before giving", permitted=False
            )
        self._stop_timer("turn", spot)  # stop giving time
        card = self._get_current_hand(spot)[4]
        giver_chamber: Chamber = self._chambers[spot]
        receiver_spot: int = self._get_opposing_position_spot(spot)
        receiver_chamber: Chamber = self._chambers[receiver_spot]
        giver_chamber.remove_card(card)
        receiver_chamber.add_card(card)
        self._message(
            f"🎁 {self._names[spot]} gives {self._names[receiver_spot]} a card"
        )
        if self._is_asker(spot):
            self._add_to_given(spot, card)
            self._decrement_gives(spot, auto_trading=auto_trading)
        elif self._is_giver(spot):
            self._clear_giving_options(spot)
            self._decrement_takes(receiver_spot, auto_trading=auto_trading)
            self._add_to_taken(receiver_spot, card)
            self._waiting[receiver_spot] = False
        self.lock(spot)

    def _set_giving_options(self, spot: int, giving_options: Set[int]) -> None:
        self._giving_options[spot] = giving_options

    def _clear_giving_options(self, spot: int) -> None:
        self._giving_options[spot].clear()

    def _decrement_takes(
        self, spot: int, *, auto_trading: bool = False
    ) -> None:
        self._takes[spot] -= 1
        # TODO: remove asking options when no takes remaining
        if not auto_trading and self._no_takes_or_gives:
            self._set_trading(False)

    def _decrement_gives(
        self, spot: int, *, auto_trading: bool = False
    ) -> None:
        self._gives[spot] -= 1
        if not auto_trading and self._no_takes_or_gives:
            self._set_trading(False)

    # misc

    def _unlock(self, spot: int) -> None:
        self._lock_if_pass_unlocked(spot)
        self._unlocked[spot] = True

    def lock(self, spot: int) -> None:
        self._unlocked[spot] = False

    def _lock_if_unlocked(self, spot: int) -> None:
        if self._unlocked[spot]:
            self.lock(spot)

    def _lock_if_pass_unlocked(self, spot: int) -> None:
        if self._pass_unlocked[spot]:
            self._lock_pass(spot)

    def _both_lock_if_unlocked(self, spot: int) -> None:
        self._lock_if_unlocked(spot)
        self._lock_if_pass_unlocked(spot)

    def _message(self, message: str) -> None:
        print(message)

    # getters

    def _get_position(self, spot: int) -> int:
        return self._positions.index(spot)

    def _get_opposing_position_spot(self, spot: int) -> int:
        return self._positions[3 - self._get_position(spot)]

    def _get_decks_from_chambers(self, testing: bool = False):
        if not testing:
            assert all(chamber.num_cards == 13 for chamber in self._chambers)
        deck = list()
        for chamber in self._chambers:
            deck.extend(chamber)
        try:
            return np.array(deck).reshape(4, 13)
        except ValueError:
            if testing:
                # for testing with singleton decks
                return np.array(deck).reshape(4, 1)

    def _get_president_and_vice_president(self) -> List[int]:
        return self._positions[0:2]

    def _get_asshole_and_vice_asshole(self) -> List[int]:
        return self._positions[2:4]

    def _get_current_hand(self, spot: int) -> Hand:
        return self._chambers[spot].hand

    def _get_current_player_name(self) -> str:
        return self._names[self._current_player]

    def _get_other_spots(
        self, spot: int, *, exclude_finished: bool = False
    ) -> Generator[int, None, None]:
        for maybe_other_spot in range(4):
            if (
                maybe_other_spot == spot
                or exclude_finished
                and self._is_finished(maybe_other_spot)
            ):
                continue
            else:
                yield maybe_other_spot

    # setters

    def _set_name(self, spot: int, name: str) -> None:
        self._names[spot] = name

    def _set_hand_in_play(self, hand: Hand) -> None:
        self._hand_in_play = hand

    def _set_president(self, spot: int) -> None:
        self._set_asker(spot, True, 2)

    def _set_vice_president(self, spot: int) -> None:
        self._set_asker(spot, True, 1)

    def _set_vice_asshole(self, spot: int) -> None:
        self._set_giver(spot, True)

    def _set_asshole(self, spot: int) -> None:
        self._set_giver(spot, True)

    def _set_asker(self, spot: int, asker: bool, takes_and_gives: int) -> None:
        self._set_takes(spot, takes_and_gives)
        self._set_gives(spot, takes_and_gives)

    def _set_giver(self, *args) -> None:
        pass  # this does something in EmittingGame

    def _set_takes(self, spot: int, takes: int) -> None:
        self._takes[spot] = takes

    def _set_gives(self, spot: int, gives: int) -> None:
        self._gives[spot] = gives

    def _add_to_given(self, spot: int, card: int) -> None:
        self._given[spot].add(card)

    def _add_to_already_asked(self, spot: int, value: int) -> None:
        self._set_selected_asking_option(spot, None)
        self._already_asked[spot].add(value)

    def _add_to_taken(self, spot: int, card: int) -> None:
        self._taken[spot].add(card)

    # boolers

    def _is_current_player(self, spot: int) -> bool:
        return spot == self._current_player

    def _is_asking(self, spot: int) -> bool:
        return self.trading and self._selected_asking_options[spot] is not None

    def _is_giving(self, spot: int) -> bool:
        return self.trading and not self._get_current_hand(spot).is_empty

    def _has_takes(self, spot: int) -> bool:
        return self._takes[spot] > 0

    def _has_gives(self, spot: int) -> bool:
        return self._gives[spot] > 0

    def _is_asker(self, spot: int) -> bool:
        return spot in self._get_president_and_vice_president()

    def _is_giver(self, spot: int) -> bool:
        return spot in self._get_asshole_and_vice_asshole()

    def _is_already_asked(self, spot: int, value: int) -> bool:
        return value in self._already_asked[spot]

    def _is_waiting(self, spot: int) -> bool:
        return self._waiting[spot]

    def _is_finished(self, spot: int) -> bool:
        # turn manager true if not finished
        return not self._turn_manager[spot]

    def _is_president(self, spot: int) -> bool:
        try:
            return self._positions[0] == spot
        except IndexError:
            return False

    def _is_vice_president(self, spot: int) -> bool:
        try:
            return self._positions[1] == spot
        except IndexError:
            return False

    def _is_vice_asshole(self, spot: int) -> bool:
        try:
            return self._positions[2] == spot
        except IndexError:
            return False

    def _is_asshole(self, spot: int) -> bool:
        try:
            return self._positions[3] == spot
        except IndexError:
            return False

    def _is_using_reserve_time(self, spot: int) -> bool:
        """
        Equivalently, is not using turn time as it has expired.
        """
        return self._reserve_time_use_starts[spot] is not None

    def in_players(self, name: str):
        return name in self._names


# fmt: off
class BaseHand:
    pass
# hand at begininning of game; only the 3 of clubs can be played on it
base_hand = BaseHand()
# fmt: on


class TurnManager:
    """
    [spot] is True if spot is unfinished; False if finished
    """

    def __init__(self, first) -> None:
        self._cycling_list = cycle([i for i in range(4)])
        for _ in range(first):
            next(self._cycling_list)
        self._not_finished_dict: Dict[int, bool] = {i: True for i in range(4)}
        self._num_unfinished_players = 4

    def __getitem__(self, spot: int) -> bool:
        return self._not_finished_dict[spot]

    def __setitem__(self, spot: int, not_finished: bool) -> None:
        self._not_finished_dict[spot] = not_finished

    def __next__(self) -> int:
        maybe_next = next(self._cycling_list)
        while self[maybe_next] is False:
            maybe_next = next(self._cycling_list)
        return maybe_next

    def remove(self, spot: int) -> None:
        self[spot] = False
        self._num_unfinished_players -= 1


class PresidentsError(RuntimeError):
    """
    Represents any violation of the rules expressed in this class;
    includes those violations which can occur only if players have
    used a browser console or modified the DOM (i.e. actions that would
    not otherwise have been permitted by interfaces to the game).
    For example, if some interface accessor were to attempt to unlock
    play despite having already finished, such an action is not
    permitted by the game because finishing should have blocked the
    accessor from making further calls to unlock play. On the other
    hand, an interface accessor is permitted to attempt to pass when one
    has the 3 of clubs. The important thing to note here is that this
    base class decides which violations are permitted and which are not.
    """

    def __init__(self, message: str, *, permitted: bool):
        super().__init__(message)
        self.permitted: bool = permitted
