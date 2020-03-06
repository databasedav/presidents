import random
from uuid import uuid4
from ..utils import spawn_after
import numpy as np
from typing import List, Iterable, Coroutine, Set, Union, Dict, Iterator
from asyncio import gather, Task
from .chamber import Chamber
from datetime import datetime
from .hand import Hand, DuplicateCardError, FullHandError, NotPlayableOnError
import itertools
from .chamber import CardNotInChamberError
from .utils import rank_articler

# TODO: mypy clean run
# TODO: handle auto moves silently
# TODO: store last few (100?) emits
# TODO: clear hand in play should just be convenience method for empty set hand in play

class Game:
    """
    Implements presidents game logic. Implementation is async to support
    arbitrary io task attachment to game events. Task must be
    implemented via overriding in subclass.
    """
    TURN_TIME = 30
    RESERVE_TIME = 60
    TRADING_TIME = 120
    GIVING_TIME = 10

    def __init__(
        self,
        *,
        game_id: str = str(uuid4()),
        turn_time: float = TURN_TIME,
        reserve_time: float = RESERVE_TIME,
        trading_time: float = TRADING_TIME,
        giving_time: float = GIVING_TIME,
    ) -> None:
        range_4 = range(4)  # software engineering

        # instance related attributes
        self.game_id: str = game_id
        self.num_players: int = 0
        self._num_consecutive_rounds: int = 0
        self._times_reset: int = 0

        # timer related attributes
        # all spot timers (turn, including playing and giving, and
        # reserve) are all stored here; only trading timer is separate
        self._timers: List[Task] = [None for _ in range_4]
        self._turn_time: float = turn_time
        # these turn time lists are used for both playing and giving
        self._turn_times: List[float] = [0 for _ in range_4]  # remaining
        self._turn_time_starts: List[datetime] = [None for _ in range_4]
        self._reserve_time: float = reserve_time
        self._reserve_times: List[float] = [reserve_time for _ in range_4]  # remaining
        self._reserve_time_starts: List[datetime] = [None for _ in range_4]
        self._trading_timer: Task = None
        self._trading_time: float = trading_time
        self._trading_time_remaining: float = trading_time
        self._trading_time_start: datetime = None
        self._giving_time: float = giving_time
        self._paused_timers: List[Coroutine] = list()

        # setup and ID related attributes
        self._open_spots: Set[int] = {i for i in range_4}
        self._names: List[str] = [None for _ in range_4]

        # game related attributes
        self._turn_manager: TurnManager = None
        self._current_player: int = None  # u r but a spot
        self._chambers: List[Chamber] = [Chamber() for _ in range_4]
        # when hand in play is base_hand, only the 3 of clubs can be
        # played on it; when it is None, anyhand can be played on it
        self._hand_in_play: Union[BaseHand, Hand] = base_hand
        self._num_consecutive_passes: int = 0
        self._finishing_last_played: bool = False
        self._positions: List[int] = list()
        self._unlocked: List[bool] = [False for _ in range_4]
        self._pass_unlocked: List[bool] = [False for _ in range_4]
        self._dot_colors: List[str] = ['red' for _ in range_4]

        # trading related attributes
        self.trading: bool = False
        self._ranks: List[int] = [None for _ in range_4]
        # TODO: there must be a better name for this...
        self._already_asked: List[Set[int]] = [set() for _ in range_4]
        self._waiting: List[bool] = [False for _ in range_4]
        self._giving_options: List[Set[int]] = [set() for _ in range_4]
        self._gives: List[int] = [0 for _ in range_4]
        self._takes: List[int] = [0 for _ in range_4]
        self._given: List[Set[int]] = [set() for _ in range_4]
        self._taken: List[Set[int]] = [set() for _ in range_4]

    @property
    def _no_takes_or_gives(self) -> bool:
        return not bool(sum(self._takes) + sum(self._gives))
    
    @property
    def _num_unfinished_players(self) -> int:
        assert self._turn_manager is not None
        return self._turn_manager._num_unfinished_players

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

    # testing related methods

    async def _set_up_testing_base(
        self, *, deck: List[Iterable[int]] = None
    ) -> None:
        """
        Adds players and starts the round.
        """
        assert self.is_empty, "game must be empty to set up testing base"
        await gather(*[self.add_player_to_spot(f"player{spot}", spot) for spot in range(4)])
        await self.start_round(setup=True, deck=deck)

    async def _get_player_to_finish(self, spot: int) -> None:
        # TODO: this is actually a lil hard cuz doing them sequentially
        # assert self._current_player is not None, 'must start round first'
        # finisher: int = spot

        # while (spot := self._current_player) != finisher:
        #     await self._maybe_unlock_pass(spot)
        #     await self._maybe_pass(spot)
        ...

    async def _get_game_to_trading(self) -> None:
        assert self._current_player is not None, 'must start round first'
        # TODO: algorithm to optimize the minimum number of moves to get
        #       game to trading
        while not self.trading:
            spot: int = self._current_player
            chamber: Chamber = self._chambers[spot]
            
            await self._maybe_add_or_remove_card(spot, chamber.get_min_card())
            try:
                await self._maybe_unlock_play(spot)
            except PresidentsError:
                await chamber.deselect_selected()
            if self._unlocked[spot]:
                try:
                    await self._maybe_play_current_hand(spot)
                except PresidentsError:
                    await chamber.deselect_selected()
            else:
                await self._maybe_unlock_pass(spot)
                await self._maybe_pass(spot)

    async def _cancel_timers(self) -> None:
        """
        blocks while cancelling timers
        """
        for timer in self._timers:
            if timer:
                timer.cancel()
        for timer in self._timers:
            if timer:
                try:
                    await timer
                except:
                    pass
        if timer := self._trading_timer:
            timer.cancel()
            try:
                await timer
            except:
                pass

    # setup related methods

    def reset(self):
        ...  # TODO
        self._times_reset += 1

    def _rand_open_spot(self) -> int:
        """
        Returns random open spot. Should not happen when there are no
        open spots.
        """
        assert self._open_spots
        return random.choice(tuple(self._open_spots))

    async def add_player_to_spot(self, name: str, spot: int) -> None:
        """
        subclass overwrite must set spot to id key prior to calling this 
        """
        assert self._names[spot] is None, f"player already in spot {spot}"

        self._open_spots.remove(spot)
        await gather(
            self._set_name(spot, name),
            self._emit_set_spot(spot)
        )
        
        self.num_players += 1

        if self.is_paused:  # player was added to a game that already started
            await self._emit_state(spot)
        
    async def _emit_state(self, spot: int) -> None:
        # TODO: allow players to correct state while game is running;
        #       will require handling timer math
        assert self.is_paused, 'can only emit state while game is paused'
        aws = [
            self._chambers[spot].emit_state(),
            self._emit_set_spot(spot),
            *[self._emit_set_name(spot, name) for name in self._names],
            *[self._emit_set_dot_color(spot, dot_color) for spot, dot_color in enumerate(self._dot_colors)],
            *[self._emit_set_num_cards_remaining(spot, chamber.num_cards) for spot, chamber in enumerate(self._chambers)],
            *[self._emit_set_time('turn', turn_time, spot) for spot, turn_time in enumerate(self._turn_times)],
            *[self._emit_set_time('reserve', reserve_time, spot) for spot, reserve_time in enumerate(self._reserve_times)],
        ]
        if (hip := self._hand_in_play) and hip is not base_hand:  # pylint: disable=used-before-assignment
            aws.append(self._emit_set_hand_in_play(hip))  # type: ignore
        if self.is_paused:
            aws.append(self._emit_set_paused(True))
        if self.trading:
            aws.extend([
                self._emit_set_trading(True),
                self._emit_set_time('trading', self._trading_time_remaining, spot),
            ])
            if self._is_asker(spot):
                aws.append(self._emit_set_asker(spot, True))
                if rank := self._ranks[spot]:
                    aws.append(self._emit_set_rank(spot, rank))
            else:  # is giver
                aws.append(self._emit_set_giver(spot, True))
                if giving_options := self._giving_options[spot]:
                    aws.append(self._emit_set_giving_options(spot, giving_options))
        
        await gather(*aws)

    async def add_player(self, name: str) -> None:
        # adds player to random spot
        await self.add_player_to_spot(name, self._rand_open_spot())

    async def remove_player(self, spot: int) -> None:
        self._open_spots.add(spot)
        await self._set_name(spot, None)
        self.num_players -= 1

    def _make_shuffled_deck(self) -> np.ndarray:
        return np.sort(np.random.permutation(range(1, 53)).reshape(4, 13))

    async def _deal_cards(self, *, deck: List[Iterable[int]] = None) -> None:
        await gather(*[self._assign_cards_to_spot(spot, cards) for spot, cards in enumerate(deck if deck is not None else self._make_shuffled_deck())])

    async def _assign_cards_to_spot(self, spot: int, cards: Iterable[int]) -> None:
        chamber: Chamber = self._chambers[spot]
        await chamber.reset()
        await chamber.add_cards(cards)
        await self._emit_set_num_cards_remaining(spot, chamber.num_cards)

    async def _emit_set_spot(self, spot: int) -> None:
        pass

    async def _emit_set_num_cards_remaining(self, spot: int, num_cards_remaining:int) -> None:
        pass

    # TODO: remove testing from this pattern
    def _make_and_set_turn_manager(self, testing: bool = False) -> None:
        decks = self._get_deck_from_chambers()
        # get which deck has the 3 of clubs
        toc_index = np.where(decks == 1)[0][0]
        self._turn_manager = TurnManager(toc_index)

    # game flow related methods

    async def _set_up_round(self, *, deck: List[Iterable[int]] = None) -> None:
        assert self.num_players == 4, "four players required to start round"
        await self._deal_cards(deck=deck)

    async def start_round(
        self,
        *,
        setup: bool,
        deck: List[Iterable[int]] = None,
    ) -> None:
        if setup:
            await self._set_up_round(deck=deck)
        self._num_consecutive_rounds += 1
        self._make_and_set_turn_manager()
        await gather(
            *[self._set_time('reserve', self._reserve_time, spot) for spot in range(4)],
            self._message(f"🏁 round {self._num_consecutive_rounds} has begun"),
            self._next_player()
        )

    async def _next_player(self) -> None:
        await self._set_on_turn(self._current_player, False)
        self._current_player = spot = next(self._turn_manager)
        aws = [
            self._set_time("turn", self._turn_time, spot, True),
            self._message(f"🎲 it's {self._names[spot]}'s turn"),
            self._set_on_turn(spot, True)
        ]
        if self._hand_in_play is None:  # can play anyhand so can't pass
            aws.append(self._lock_if_pass_unlocked(spot))
        await gather(*aws)

    async def _set_on_turn(self, spot: int, on_turn: bool) -> None:
        aws = [self._emit_set_on_turn(spot, on_turn)]
        if on_turn:
            aws.append(self._set_dot_color(spot, 'green'))
        await gather(*aws)

    async def _set_dot_color(self, spot: int, dot_color: str) -> None:
        self._dot_colors[spot] = dot_color
        await self._emit_set_dot_color(spot, dot_color)

    async def _emit_set_on_turn(self, spot: int, on_turn: bool) -> None:
        pass

    async def _emit_set_dot_color(self, spot, dot_color: str) -> None:
        pass

    async def _set_time(
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

        await self._emit_set_time(which, seconds, spot)

        if start:
            await self._start_timer(which, spot)

        
    async def _emit_set_time(self, which: str, seconds: float, spot: int):
        pass

    async def _start_timer(self, which: str, spot: int = None) -> None:
        """
        Uses the remaining time.
        """
        now = datetime.utcnow()
        assert which in ["turn", "reserve", "trading"]
        if which == "turn":
            assert spot is not None
            self._turn_time_starts[spot] = now
            self._timers[spot] = spawn_after(
                self._turn_times[spot],
                self._handle_playing_timeout
                if not self.trading
                else self._handle_giving_timeout,
                spot,
            )
        elif which == "reserve":
            assert spot is not None
            self._reserve_time_starts[spot] = now
            self._timers[spot] = spawn_after(
                self._reserve_times[spot], self._handle_playing_timeout, spot
            )
        elif which == "trading":
            self._trading_time_start = now
            self._trading_timer = spawn_after(
                self._trading_time_remaining, self._handle_trading_timeout
            )
        
        await self._emit_set_timer_state(which, True, spot, now)

    async def _emit_set_timer_state(self, which: str, state: bool, spot: int, timestamp: datetime = None) -> None:
        pass

    async def _stop_timer(
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
        await self._emit_set_timer_state(which, False, spot)
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
            await self._set_time("turn", 0, spot)
            self._turn_time_starts[spot] = None
        elif which == "reserve":
            assert spot is not None
            if cancel and self._timers[spot] is not None:
                self._timers[spot].cancel()
            self._timers[spot] = None
            time_used = (
                now - self._reserve_time_starts[spot]
            ).total_seconds()
            await self._set_time(
                # need the max statement since this function is used during
                # reserve time timeouts
                "reserve",
                max(0, self._reserve_times[spot] - time_used),
                spot,
            )
            self._reserve_time_starts[spot] = None
        elif which == "trading":
            assert spot is None
            if cancel and self._trading_timer is not None:
                self._trading_timer.cancel()
            self._trading_timer = None
            await self._set_time("trading", self._trading_time)
            self._trading_time_start = None

    async def pause(self) -> None:
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
            if not (timer := self._timers[spot]):
                return  # game has not started TODO: store has started attr?
            timer.cancel()
            self._timers[spot] = None

            if not self._is_using_reserve_time(spot):
                time_used = (
                    now - self._turn_time_starts[spot]
                ).total_seconds()
                self._turn_time_starts[spot] = None
                await self._set_time(
                    "turn", self._turn_times[spot] - time_used, spot
                )
                self._paused_timers.append(self._start_timer("turn", spot))
            else:
                time_used = (
                    now - self._reserve_time_starts[spot]
                ).total_seconds()
                self._reserve_time_starts[spot] = None
                await self._set_time(
                    "reserve", self._reserve_times[spot] - time_used, spot
                )
                self._paused_timers.append(self._start_timer("reserve", spot))
        else:  # elif self.trading
            self._trading_timer.cancel()
            self._trading_timer = None
            time_used = (now - self._trading_time_start).total_seconds()
            await self._set_time("trading", self._trading_time_remaining - time_used)
            self._trading_time_start = None
            self._paused_timers.append(self._start_timer("trading"))

            # giving timers
            for spot in self._get_asshole_and_vice_asshole():
                if not self._timers[spot]:  # no active giving timer
                    continue
                self._timers[spot].cancel()
                self._timers[spot] = None
                time_used = (
                    now - self._turn_time_starts[spot]
                ).total_seconds()
                # turn time objects are used for for giving times
                self._set_time(
                    "turn", self._turn_times[spot] - time_used, spot
                )
                self._turn_time_starts[spot] = None
                self._paused_timers.append(self._start_timer("turn", spot))
        
        await self._emit_set_paused(True)

    async def _emit_set_paused(self, paused: bool) -> None:
        pass

    async def resume(self) -> None:
        await gather(*self._paused_timers, self._emit_set_paused(False))  
        self._paused_timers.clear()

    async def _handle_playing_timeout(self, spot: int) -> None:
        """
        Handles turn time and reserve time timing out.
        """
        if not self._is_using_reserve_time(spot):  # was using turn time
            await self._stop_timer("turn", spot, cancel=False)
            reserve_time: float = self._reserve_times[spot]
            if reserve_time:
                # start reserve time
                await self._set_time("reserve", reserve_time, spot, True)
            else:
                await self._auto_play_or_pass(spot)
        else:  # was using reserve time
            await gather(
                self._stop_timer("reserve", spot, cancel=False),
                self._auto_play_or_pass(spot)
            )

    async def _handle_giving_timeout(self, spot) -> None:
        await gather(
            self._stop_timer("turn", spot, cancel=False),
            self._auto_give(spot)
        )

    async def _handle_trading_timeout(self) -> None:
        if not self._no_takes_or_gives:
            await self._auto_trade()
        await self._set_trading(False, cancel=False)

    async def _auto_play_or_pass(self, spot: int) -> None:
        assert self._current_player == spot, f"it is not spot {spot}'s turn"

        # pass if can
        if self._hand_in_play not in [base_hand, None]:
            await self._maybe_unlock_pass(spot)
            await self._maybe_pass(spot)  # locks pass
            return

        chamber: Chamber = self._chambers[spot]
        currently_selected_cards: List[int] = list(chamber.hand)
        if currently_selected_cards:  # not empty list
            await chamber.deselect_selected()

        # min card will be 1 if playing on base hand
        await self._maybe_add_or_remove_card(spot, chamber.get_min_card())
        await self._maybe_unlock_play(spot)
        await self._maybe_play_current_hand(spot)

        # reselect spot's selected cards
        for card in currently_selected_cards:  # could be empty list
            try:
                await self._maybe_add_or_remove_card(spot, card)
            # one of the selected cards was auto played
            except PresidentsError:
                pass

    async def _auto_give(self, spot, *, auto_trading=False) -> None:
        chamber: Chamber = self._chambers[spot]
        currently_selected_cards: List[int] = list(chamber.hand)
        if currently_selected_cards:
            await chamber.deselect_selected()

        await self._maybe_add_or_remove_card(spot, min(self._giving_options[spot]))
        await self._maybe_unlock_give(spot)
        await self._give_card(spot, auto_trading=auto_trading)

        # reselect giver's selected cards
        for card in currently_selected_cards:  # could be empty list
            try:
                await self._maybe_add_or_remove_card(spot, card)
            # one of the selected cards was auto given
            except CardNotInChamberError:
                pass

    async def _auto_trade(self) -> None:
        # TODO: only auto trade for a single spot so pres and vice pres
        #       can be done concurrently
        for spot in self._get_president_and_vice_president():
            if not self._has_gives(spot) and not self._has_takes(spot):
                continue

            chamber: Chamber = self._chambers[spot]
            currently_selected_cards: List[int] = list(chamber.hand)
            if currently_selected_cards:  # not empty list
                await chamber.deselect_selected()

            for _ in range(self._gives[spot]):  # give before u take
                # get the lowest card that can be given
                # TODO: user setting for auto giving 3 of clubs
                for card in chamber:
                    if card not in self._taken[spot]:
                        break
                await self._maybe_add_or_remove_card(spot, card)
                await self._maybe_unlock_give(spot)
                await self._give_card(spot, auto_trading=True)

            # reselect asker's selected cards
            for card in currently_selected_cards:  # could be empty list
                try:
                    await self._maybe_add_or_remove_card(spot, card)
                # one of the selected cards was auto given
                except CardNotInChamberError:
                    pass

            # TODO: reuse more of auto give below
            # deselect to-be-asked's selected cards if exists
            if self._has_takes(spot):
                asked_spot: int = self._get_opposing_position_spot(spot)
                asked_chamber: Chamber = self._chambers[asked_spot]
                asked_currently_selected_cards = list(asked_chamber.hand)
                if asked_currently_selected_cards:
                    await asked_chamber.deselect_selected()
            else:
                continue

            if self._is_waiting(spot):
                await gather(
                    self._stop_timer("turn", asked_spot),
                    self._auto_give(asked_spot, auto_trading=True)
                )

            for _ in range(self._takes[spot]):
                # iterate through ranks, highest to lowest, asking if
                # has not already been asked
                for rank in range(13, 0, -1):
                    if self._is_already_asked(spot, rank):
                        continue

                    await self._maybe_set_or_unset_rank(spot, rank)
                    await self._maybe_unlock_ask(spot)
                    await self._ask_for_card(spot)
                    if not self._is_waiting(spot):  # asked doesn't have rank
                        continue
                    else:  # have asked give lowest allowed card to asker
                        await self._maybe_add_or_remove_card(
                            asked_spot, min(self._giving_options[asked_spot])
                        )
                        await self._maybe_unlock_give(asked_spot)
                        await self._give_card(asked_spot, auto_trading=True)
                        break

            # reselect asked's selected cards
            for card in asked_currently_selected_cards:  # could be empty list
                try:
                    await self._maybe_add_or_remove_card(asked_spot, card)
                # one of the selected cards was auto given
                except CardNotInChamberError:
                    pass

        assert self._no_takes_or_gives

    async def _player_finish(self, spot: int) -> None:
        assert self._chambers[
            spot
        ].is_empty, "only players with no cards remaining can finish"
        await self._set_dot_color(spot, "purple")
        self._positions.append(self._current_player)
        self._turn_manager.remove(self._current_player)
        num_unfinished_players = self._num_unfinished_players
        if num_unfinished_players == 3:
            await gather(
                self._set_president(spot),
                self._message(f"🏆 {self._names[spot]} is president 🥇"),
                self._next_player(),
            )
        elif num_unfinished_players == 2:
            await gather(
                self._set_vice_president(spot),
                self._message(f"🏆 {self._names[spot]} is vice president 🥈"),
                self._next_player(),
            )
        else:  # num_unfinished
            await self._set_vice_asshole(spot)
            self._current_player = next(self._turn_manager)
            await self._set_asshole(self._current_player)
            self._positions.append(self._current_player)
            await gather(
                self._message(
                    f"🏆 {self._names[spot]} is vice asshole 🥉 and {self._names[self._current_player]} is asshole 💩"
                ),
                self._set_trading(True),
            )

    # card control related methods

    async def card_handler(self, spot: int, card: int) -> None:
        try:
            await self._maybe_add_or_remove_card(spot, card)
        except PresidentsError as e:
            await self._emit_alert(spot, str(e))
    
    async def _emit_alert(self, spot: int, alert: str) -> None:
        pass

    async def _maybe_add_or_remove_card(self, spot: int, card: int) -> None:
        if not self.trading and self._is_finished(spot):
            raise PresidentsError(
                "you have already finished this round", permitted=False
            )
        chamber: Chamber = self._chambers[spot]
        # EAFP is a magnitude faster than LBYL here
        try:
            await chamber.select_card(card)
            if self._is_asking(spot):
                await self._maybe_set_or_unset_rank(spot, None)
            await self._lock_if_unlocked(spot)
        except CardNotInChamberError:
            raise PresidentsError("you don't have this card", permitted=False)
        except DuplicateCardError:
            # such an error can only occur if check passes
            chamber.deselect_card(card, check=False)
            self._lock_if_unlocked(spot)
        except FullHandError:
            raise PresidentsError("your current hand is full", permitted=True)

    def _store_hand(self, spot: int) -> None:
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

    async def unlock_handler(self, spot: int) -> None:
        which: str = None
        try:
            if self.trading:
                if self._is_asking(spot):
                    which = 'ask'
                else:
                    which = 'give'
            else:
                which = 'play'
            await eval(f'self._maybe_unlock_{which}')(spot, spot)
        except PresidentsError as e:
            await self._emit_alert(spot, str(e))

    async def _maybe_unlock_play(self, spot: int):
        """
        Unlocking is allowed as long as one's current hand can be played
        on the current hand in play. Locking updates automatically as
        the hand in play changes.
        """
        if self._is_finished(spot):
            raise PresidentsError(
                "you have already finished this round", permitted=False
            )
        await self._lock_if_pass_unlocked(spot)
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
                    await self._unlock(spot)
            else:
                # other players (without the 3 of clubs) can unlock
                # whatever hand they want
                await self._unlock(spot)
        elif hip is None:  # current player won last hand and can play anyhand
            await self._unlock(spot)
        else:
            try:  # same combo
                if hand > hip:  # type: ignore
                    await self._unlock(spot)
                else:
                    raise PresidentsError(
                        "your current hand is weaker than the hand in play",
                        permitted=True,
                    )
            except NotPlayableOnError as e:  # different combo
                raise PresidentsError(str(e), permitted=True)

    async def play_handler(self, spot: int) -> None:
        try:
            await self._maybe_play_current_hand(spot)
        except PresidentsError as e:
            await self._emit_alert(spot, str(e))

    async def _maybe_play_current_hand(self, spot: int) -> None:
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
            await self._play_current_hand(spot)

    async def _play_current_hand(self, spot: int) -> None:
        """
        In this class' context, playing a hand means only to place the
        hand in play while appropriately changing the state such that
        the hand and the cards that it consists in only exist as the
        hand in play; playing a hand does not mean taking care of game
        flow related things like moving on to the next player or
        finishing a player (this is taken care of by the post play
        handler).
        """
        assert self._unlocked[spot], "play called without unlocking"
        await self._stop_timer(
            "turn" if not self._is_using_reserve_time(spot) else "reserve",
            spot,
        )
        chamber = self._chambers[spot]
        hand = Hand.copy(chamber.hand)
        await chamber.remove_cards(hand)
        await gather(
            self._set_hand_in_play(hand),
            self._emit_hand_play(hash(hand)),
            self._message(f"▶️ {self._names[spot]} played {str(hand)}"),
            self._lock(spot),
            self._set_dot_color(spot, "blue"),
            *[
                self._set_dot_color(other_spot, "red")
                for other_spot in self._get_other_spots(
                    spot, exclude_finished=True
                )
            ],
            self._emit_set_num_cards_remaining(spot, chamber.num_cards)
        )
        self._num_consecutive_passes = 0
        # lock others if their currently unlocked hand should no longer be unlocked
        for other_spot in self._get_other_spots(spot, exclude_finished=True):
            if self._unlocked[other_spot]:
                try:
                    # hand in play can't be base hand here so ignore type
                    if self._get_current_hand(other_spot) < self._hand_in_play:  # type: ignore
                        await self._lock(other_spot)
                # occurs either when base_hand is the hand in play since
                # anything can be unlocked or when a bomb is played on a
                # non-bomb that other players have unlocked on
                except NotPlayableOnError:
                    await self._lock(other_spot)
        await self._post_play_handler(spot)

    async def _emit_hand_play(self, hand_hash: int) -> None:
        pass

    async def _post_play_handler(self, spot: int) -> None:
        if self._chambers[spot].is_empty:
            # player_finish takes care of going to the next player
            self._finishing_last_played = True
            await self._player_finish(spot)
        else:
            self._finishing_last_played = False
            await self._next_player()

    async def unlock_pass_handler(self, spot: int) -> None:
        try:
            await self._maybe_unlock_pass(spot)
        except PresidentsError as e:
            await self._emit_alert(spot, str(e))

    async def _maybe_unlock_pass(self, spot: int) -> None:
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
        await self._lock_if_unlocked(spot)
        self._pass_unlocked[spot] = True
        await self._emit_set_pass_unlocked(spot, True)

    async def _lock_pass(self, spot: int) -> None:
        self._pass_unlocked[spot] = False
        await self._emit_set_pass_unlocked(spot, False)

    async def _emit_set_pass_unlocked(self, spot: int, pass_unlocked: bool) -> None:
        pass

    async def pass_handler(self, spot: int) -> None:
        try:
            await self._maybe_pass(spot)
        except PresidentsError as e:
            await self._emit_alert(spot, str(e))

    async def _maybe_pass(self, spot: int) -> None:
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
            await self._pass(spot)

    async def _pass(self, spot: int) -> None:
        assert self._pass_unlocked[spot], "pass called without unlocking"
        self._num_consecutive_passes += 1
        await gather(
            self._stop_timer(
                "turn" if not self._is_using_reserve_time(spot) else "reserve",
                spot,
            ),
            self._lock_pass(spot),
            self._message(f"⏭️ {self._names[spot]} passed")
        )
        await self._post_pass_handler()

    async def _post_pass_handler(self) -> None:
        # all remaining players passed on a winning hand
        if self._finishing_last_played:
            if self._num_consecutive_passes == self._num_unfinished_players:
                self._finishing_last_played = False
                await gather(
                    self._clear_hand_in_play(),
                    self._next_player()
                )
            else:
                await self._next_player()
        # all other players passed on a hand
        elif self._num_consecutive_passes == self._num_unfinished_players - 1:
            self._finishing_last_played = False
            await gather(
                self._clear_hand_in_play(),
                self._next_player()
            )
        else:
            await self._next_player()

    async def _clear_hand_in_play(self) -> None:
        self._hand_in_play = None
        await self._emit_clear_hand_in_play()

    async def _emit_clear_hand_in_play(self) -> None:
        pass

    # trading related methods

    async def _set_trading(
        self, trading: bool, *, cancel: bool = True
    ) -> None:
        """
        cancel: whether to cancel the trading timer; this should be
                False when the handling trading timeout 
        """
        self.trading = trading
        await self._emit_set_trading(trading)
        range_4 = range(4)
        if trading:
            await gather(
                *[self._set_dot_color(spot, "red") for spot in range_4],
                self._emit_set_on_turn(self._current_player, False),
                self._clear_hand_in_play(),
                self._set_up_round(),
                self._set_time("trading", self._trading_time, start=True),
                self._message("💱 trading has begun"),
            )

            # timer related attributes
            self._timers = [None for _ in range_4]
            self._turn_times = [0 for _ in range_4]
            self._turn_time_starts = [None for _ in range_4]
            self._reserve_times = [self._reserve_time for _ in range_4]
            self._reserve_time_starts = [None for _ in range_4]

            # game related attributes
            self._current_player = None
            self._hand_in_play = base_hand
            self._num_consecutive_passes = 0
            self._finishing_last_played = False
            self._unlocked = [False for _ in range_4]
            self._pass_unlocked = [False for _ in range_4]
        else:  # elif not trading
            await self._stop_timer("trading", cancel=cancel)
            # trading related attributes
            self._ranks = [None for _ in range_4]
            self._already_asked = [set() for _ in range_4]
            self._waiting = [False for _ in range_4]
            self._giving_options = [set() for _ in range_4]
            self._gives = [0 for _ in range_4]
            self._takes = [0 for _ in range_4]
            self._given = [set() for _ in range_4]
            self._taken = [set() for _ in range_4]

            # game related attributes
            self._positions.clear()
            await self.start_round(setup=False)

    async def _emit_set_trading(self, trading: bool) -> None:
        pass

    async def rank_handler(self, spot: int, rank: int) -> None:
        try:
            await self._maybe_set_or_unset_rank(spot, rank)
        except PresidentsError as e:
            await self._emit_alert(spot, str(e))
    
    async def _maybe_set_or_unset_rank(self, spot: int, rank: int) -> None:
        if not self._is_asker(spot):
            raise PresidentsError("you are not an asker", permitted=False)
        if not 1 <= rank <= 13:
            raise PresidentsError(
                "you cannot ask for this rank", permitted=False
            )
        if self._is_already_asked(spot, rank):
            raise PresidentsError(
                f"{self._names[self._get_opposing_position_spot(spot)]} doesn't have any cards of this rank",
                permitted=False,  # already asked should be unselectable
            )
        await gather(
            self._lock(spot),
            self._set_rank(
                spot,
                # unset if already set
                None if rank == self._ranks[spot] else rank,
            )
        )

    async def _maybe_unlock_ask(self, spot: int) -> None:
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
        if not self._ranks[spot]:
            raise PresidentsError(
                "you must select a rank before attempting to unlock",
                permitted=True,
            )
        else:
            await self._unlock(spot)

    async def ask_handler(self, spot: int) -> None:
        try:
            await self._ask_for_card(spot)
        except PresidentsError as e:
            await self._emit_alert(spot, str(e))

    async def _ask_for_card(self, spot: int) -> None:
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
        rank: int = self._ranks[spot]
        asked_spot: int = self._get_opposing_position_spot(spot)
        await self._message(
            f"❓ {self._names[spot]} asks {self._names[asked_spot]} for {rank_articler(rank)}"
        )
        # chamber for asked
        chamber = self._chambers[asked_spot]
        giving_options = {
            card
            for card in range((rank - 1) * 4 + 1, rank * 4 + 1)
            if card in chamber and card not in self._given[spot]
        }

        await self._lock(spot)  # lock whether or not there are giving options
        if not giving_options:
            await gather(
                self._message(
                    f"❎ {self._names[asked_spot]} does not have a {rank}"
                ),
                self._set_rank(spot, None),
                self._add_to_already_asked(spot, rank)
            )
        else:
            await gather(
                self._set_giving_options(asked_spot, giving_options),
                self._wait_for_reply(spot, asked_spot)
            )
            

    async def _set_rank(self, spot: int, rank: int) -> None:
        self._ranks[spot] = rank
        if rank:  # when setting rank
            await self._chambers[spot].deselect_selected()
        await self._emit_set_rank(spot, rank)
    
    async def _emit_set_rank(self, spot: int, rank: int) -> None:
        pass

    async def _wait_for_reply(self, asker_spot: int, asked_spot: int) -> None:
        await gather(
            self._set_time("turn", self._giving_time, asked_spot, True),
            self._set_rank(asker_spot, None)
        )
        self._waiting[asker_spot] = True

    async def _maybe_unlock_give(self, spot: int) -> None:
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
                await self._unlock(spot)
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
                await self._unlock(spot)

    async def give_handler(self, spot: int) -> None:
        try:
            await self._give_card(spot)
        except PresidentsError as e:
            await self._emit_alert(spot, str(e))

    async def _give_card(
        self, spot: int, *, auto_trading: bool = False
    ) -> None:
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
                self._emit_set_num_cards_remaining(spot, chamber.num_cards)
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
                self._set_giving_options(spot, set()),
                self._decrement_takes(
                    receiver_spot, auto_trading=auto_trading
                ),
            )
            self._add_to_taken(receiver_spot, card)
            self._waiting[receiver_spot] = False
        await self._lock(spot)

    async def _set_giving_options(self, spot: int, giving_options: Set[int]) -> None:
        go: Set[int] = self._giving_options[spot]
        go.clear()
        go.update(giving_options)
        await self._emit_set_giving_options(spot, giving_options)

    async def _emit_set_giving_options(self, spot, giving_options) -> None:
        pass

    async def _decrement_takes(
        self, spot: int, *, auto_trading: bool = False
    ) -> None:
        self._takes[spot] -= 1
        # TODO: remove asking options when no takes remaining ?
        if not auto_trading and self._no_takes_or_gives:
            await self._set_trading(False)

    async def _decrement_gives(
        self, spot: int, *, auto_trading: bool = False
    ) -> None:
        self._gives[spot] -= 1
        if not auto_trading and self._no_takes_or_gives:
            await self._set_trading(False)

    # misc  # TODO: misc is not the best label...

    async def lock_handler(self, spot: int) -> None:
        await self._lock(spot)

    async def _unlock(self, spot: int) -> None:
        await self._lock_if_pass_unlocked(spot)
        self._unlocked[spot] = True
        await self._emit_set_unlocked(spot, True)

    async def _lock(self, spot: int) -> None:
        self._unlocked[spot] = False
        await self._emit_set_unlocked(spot, False)
    
    async def _emit_set_unlocked(self, spot: int, unlocked: bool) -> None:
        pass

    async def _lock_if_unlocked(self, spot: int) -> None:
        if self._unlocked[spot]:
            await self._lock(spot)

    async def _lock_if_pass_unlocked(self, spot: int) -> None:
        if self._pass_unlocked[spot]:
            await self._lock_pass(spot)

    async def _both_lock_if_unlocked(self, spot: int) -> None:
        await self._lock_if_unlocked(spot)
        await self._lock_if_pass_unlocked(spot)

    async def _message(self, message: str) -> None:
        # print(message)
        await self._emit_message(message)

    async def _emit_message(self, message: str) -> None:
        pass

    # getters

    def _get_position(self, spot: int) -> int:
        return self._positions.index(spot)

    def _get_opposing_position_spot(self, spot: int) -> int:
        return self._positions[3 - self._get_position(spot)]

    def _get_deck_from_chambers(self):
        # TODO: disable this when custom deck size or some other way to
        #       handle custom deck sizes
        assert all(chamber.num_cards == 13 for chamber in self._chambers)
        deck = list()
        for chamber in self._chambers:
            deck.extend(chamber)
        return np.array(deck).reshape(4, 13)

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
    ) -> Iterator[int]:
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

    async def _set_name(self, spot: int, name: str) -> None:
        self._names[spot] = name
        await self._emit_set_name(spot, name)
    
    # emitters

    async def _emit_set_name(self, spot: int, name: str) -> None:
        pass

    async def _set_hand_in_play(self, hand: Hand) -> None:
        self._hand_in_play = hand
        await self._emit_set_hand_in_play(hand)

    async def _emit_set_hand_in_play(self, hand: Hand) -> None:
        pass

    async def _set_president(self, spot: int) -> None:
        await self._set_asker(spot, True, 2)

    async def _set_vice_president(self, spot: int) -> None:
        await self._set_asker(spot, True, 1)

    async def _set_vice_asshole(self, spot: int) -> None:
        await self._set_giver(spot, True)

    async def _set_asshole(self, spot: int) -> None:
        await self._set_giver(spot, True)

    async def _set_asker(self, spot: int, asker: bool, takes_and_gives: int) -> None:
        await gather(
            self._set_takes(spot, takes_and_gives),
            self._set_gives(spot, takes_and_gives),
            self._emit_set_asker(spot, asker)
        )

    async def _emit_set_asker(self, spot: int, asker: bool) -> None:
        pass
        
    async def _set_giver(self, spot: int, giver: bool) -> None:
        await self._emit_set_giver(spot, giver)
    
    async def _emit_set_giver(self, spot: int, giver: bool) -> None:
        pass

    async def _set_takes(self, spot: int, takes: int) -> None:
        self._takes[spot] = takes
        await self._emit_set_takes(spot, takes)

    async def _set_gives(self, spot: int, gives: int) -> None:
        self._gives[spot] = gives
        await self._emit_set_gives(spot, gives)

    async def _emit_set_takes(self, spot: int, takes: int) -> None:
        pass

    async def _emit_set_gives(self, spot: int, gives: int) -> None:
        pass

    def _add_to_given(self, spot: int, card: int) -> None:
        self._given[spot].add(card)

    async def _add_to_already_asked(self, spot: int, rank: int) -> None:
        self._already_asked[spot].add(rank)
        await self._emit_add_to_already_asked(spot, rank)

    async def _emit_add_to_already_asked(self, spot: int, rank: int) -> None:
        pass

    async def _add_to_taken(self, spot: int, card: int) -> None:
        self._taken[spot].add(card)
        await self._emit_add_to_taken(spot, card)

    async def _emit_add_to_taken(self, spot: int, card: int) -> None:
        pass

    # boolers

    def _is_current_player(self, spot: int) -> bool:
        return spot == self._current_player

    def _is_asking(self, spot: int) -> bool:
        return self.trading and self._ranks[spot] is not None

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

    def _is_already_asked(self, spot: int, rank: int) -> bool:
        return rank in self._already_asked[spot]

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
        return self._reserve_time_starts[spot] is not None


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
        self._cycling_list = itertools.cycle([i for i in range(4)])
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
