from typing import List, Iterable, Union
from datetime import datetime

from .utils import rank_articler
from .game import base_hand, PresidentsError
from .chamber import Chamber, CardNotInChamberError
from .hand import Hand, DuplicateCardError, FullHandError, NotPlayableOnError
    
async def add_or_remove_card(self, spot: int, card: int) -> None:
    if not self.trading and self._is_finished(spot):
        raise PresidentsError(
            "you have already finished this round", permitted=False
        )
    chamber: Chamber = self._chambers[spot]
    # EAFP is a magnitude faster than LBYL here
    try:
        await chamber.select_card(card)
        if self._is_asking(spot):
            await self._set_selected_asking_option(spot, None)
        await self._lock_if_unlocked(spot)
    except CardNotInChamberError:
        raise PresidentsError("you don't have this card", permitted=False)
    except DuplicateCardError:
        # such an error can only occur if check passes
        await chamber.deselect_card(card, check=False)
        await self._lock_if_unlocked(spot)
    except FullHandError:
        raise PresidentsError("your current hand is full", permitted=True)

async def add_player(self, name: str, **kwargs) -> None:
    await self._add_player_to_spot(
        name=name, spot=self._rand_open_spot(), **kwargs
    )

async def _add_to_already_asked(self, spot: int, value: int) -> None:
    await self._set_selected_asking_option(spot, None)
    self._already_asked[spot].add(value)

async def ask_for_card(self, spot: int) -> None:
    if not self.trading:
        raise PresidentsError("trading is not ongoing", permitted=False)
    if not self._is_asker(spot):
        raise PresidentsError("you are not an asker", permitted=False)
    if not self._unlocked[spot]:
        # await self.lock(spot)  # TODO doing this should be part of resetting the DOM, say
        raise PresidentsError(
            "you must unlock before asking", permitted=False
        )
    # TODO: remove trading options when takes run out
    value: int = self._selected_asking_options[spot]
    articled_rank: str = rank_articler(value)
    asked_spot: int = self._get_opposing_position_spot(spot)
    await self._message(
        f"❓ {self._names[spot]} asks {self._names[asked_spot]} for {articled_rank}"
    )
    # chamber for asked
    chamber = self._chambers[asked_spot]
    giving_options = {
        card
        for card in range((value - 1) * 4 + 1, value * 4 + 1)
        if card in chamber and card not in self._given[spot]
    }

    await self.lock(spot)  # lock whether or not there are giving options
    if not giving_options:
        await self._message(
            f"❎ {self._names[asked_spot]} does not have such a card"
        )
        await self._add_to_already_asked(spot, value)
    else:
        await self._set_giving_options(asked_spot, giving_options)
        await self._wait_for_reply(spot, asked_spot)

async def _auto_give(self, spot) -> None:
    chamber: Chamber = self._chambers[spot]
    currently_selected_cards: List[int] = chamber.hand.to_list()
    if currently_selected_cards:
        await chamber.deselect_selected()

    await self.add_or_remove_card(spot, min(self._giving_options[spot]))
    await self.maybe_unlock_give(spot)
    await self.give_card(spot)

    # reselect giver's selected cards
    for card in currently_selected_cards:  # could be empty list
        try:
            await self.add_or_remove_card(spot, card)
        # one of the selected cards was auto given
        except CardNotInChamberError:
            pass

async def _auto_play_or_pass(self, spot: int) -> None:
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
        await self.maybe_unlock_pass_turn(spot)
        await self.maybe_pass_turn(spot)  # locks pass
        return

    chamber: Chamber = self._chambers[spot]
    currently_selected_cards: List[int] = chamber.hand.to_list()
    if currently_selected_cards:  # not empty list
        await chamber.deselect_selected()

    # min card will be 1 if playing on base hand
    await self.add_or_remove_card(spot, chamber._get_min_card())
    await self.maybe_unlock_play(spot)
    await self.maybe_play_current_hand(spot, timestamp=datetime.utcnow())

    # reselect spot's selected cards
    for card in currently_selected_cards:  # could be empty list
        try:
            await self.add_or_remove_card(spot, card)
        # one of the selected cards was auto played
        except PresidentsError:
            pass

async def _auto_trade(self) -> None:
    # TODO: only auto trade for a single spot so pres and vice pres
    #       can be done concurrently
    for spot in self._get_president_and_vice_president():
        if not self._has_gives(spot) and not self._has_takes(spot):
            continue

        chamber: Chamber = self._chambers[spot]
        currently_selected_cards: List[int] = chamber.hand.to_list()
        if currently_selected_cards:  # not empty list
            await chamber.deselect_selected()

        for _ in range(self._gives[spot]):  # give before u take
            # get the lowest card that can be given
            for card in chamber:
                if card not in self._taken[spot]:
                    break
            await self.add_or_remove_card(spot, card)
            await self.maybe_unlock_give(spot)
            await self.give_card(spot, auto_trading=True)

        # reselect asker's selected cards
        for card in currently_selected_cards:  # could be empty list
            try:
                await self.add_or_remove_card(spot, card)
            # one of the selected cards was auto given
            except CardNotInChamberError:
                pass

        # deselect to-be-asked's selected cards if exists
        if self._has_takes(spot):
            asked_spot: int = self._get_opposing_position_spot(spot)
            asked_chamber: Chamber = self._chambers[asked_spot]
            asked_currently_selected_cards = asked_chamber.hand.to_list()
            if asked_currently_selected_cards:
                await chamber.deselect_selected()
        else:
            continue

        for _ in range(self._takes[spot]):
            # iterate through ranks, highest to lowest, asking if
            # has not already been asked
            for value in range(13, 0, -1):
                if self._is_already_asked(spot, value):
                    continue

                await self.maybe_set_selected_asking_option(spot, value)
                await self.maybe_unlock_ask(spot)
                # requires auto trading argument that
                await self.ask_for_card(spot)
                if not self._is_waiting(spot):  # asked doesn't have rank
                    continue
                else:  # have asked give lowest allowed card to asker
                    await self.add_or_remove_card(
                        asked_spot, min(self._giving_options[asked_spot])
                    )
                    await self.maybe_unlock_give(asked_spot)
                    await self.give_card(asked_spot, auto_trading=True)
                    break

        # reselect asked's selected cards
        for card in asked_currently_selected_cards:  # could be empty list
            try:
                await self.add_or_remove_card(asked_spot, card)
            # one of the selected cards was auto given
            except CardNotInChamberError:
                pass

    assert self._no_takes_or_gives

async def _decrement_takes(
    self, spot: int, *, auto_trading: bool = False
) -> None:
    self._takes[spot] -= 1
    # TODO: remove asking options when no takes remaining
    if not auto_trading and self._no_takes_or_gives:
        await self._set_trading(False)

async def _decrement_gives(
    self, spot: int, *, auto_trading: bool = False
) -> None:
    self._gives[spot] -= 1
    if not auto_trading and self._no_takes_or_gives:
        await self._set_trading(False)

async def _handle_giving_timeout(self, spot) -> None:
    await self._stop_timer("turn", spot, cancel=False)
    await self._auto_give(spot)

async def _handle_playing_timeout(self, spot: int) -> None:
    """
    Handles turn time and reserve time timing out.
    """
    # was using turn time
    if not self._is_using_reserve_time(spot):
        await self._stop_timer("turn", spot, cancel=False)
        reserve_time: Union[int, float] = self._reserve_times[spot]
        if reserve_time:
            # start reserve time
            await self._set_time("reserve", reserve_time, spot, True)
        else:
            await self._auto_play_or_pass(spot)
    else:  # was using reserve time
        await self._stop_timer("reserve", spot, cancel=False)
        await self._auto_play_or_pass(spot)

async def _handle_trading_timeout(self) -> None:
    # TODO:
    # account for the number of cards the askers have remaining to
    # give and then silently do all the operations that snatch and
    # exchange the appropriate cards from the appropriate players
    if not self._no_takes_or_gives:
        await self._auto_trade()
    await self._set_trading(False, start=False, cancel=False)
    await self._start_round(setup=False)

async def _lock_if_unlocked(self, spot: int) -> None:
    if self._unlocked[spot]:
        await self.lock(spot)

async def _lock_if_pass_unlocked(self, spot: int) -> None:
    if self._pass_unlocked[spot]:
        await self._lock_pass(spot)

async def maybe_pass_turn(self, spot: int) -> None:
    if self._is_finished(spot):
        raise PresidentsError(
            "you have already finished this round", permitted=False
        )
    if not self._pass_unlocked[spot]:
        # await self._lock_pass(spot)  # TODO doing this should be part of resetting the DOM, say
        raise PresidentsError(
            "you must unlock pass before passing", permitted=False
        )
    if not self._is_current_player(spot):
        raise PresidentsError(
            "you can only pass on your turn", permitted=True
        )
    else:
        await self._pass_turn(spot)

async def maybe_play_current_hand(self, spot: int, **kwargs) -> None:
    if self._is_finished(spot):
        raise PresidentsError(
            "you have already finished this round", permitted=False
        )
    if not self._unlocked[spot]:
        # await self.lock(spot)  # TODO doing this should be part of resetting the DOM, say
        raise PresidentsError(
            "you must unlock before playing", permitted=False
        )
    if not self._is_current_player(spot):
        raise PresidentsError(
            "you can only play a hand on your turn", permitted=True
        )
    else:
        await self._play_current_hand(spot, **kwargs)

async def maybe_set_selected_asking_option(self, spot: int, value: int) -> None:
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
    await self.lock(spot)
    await self._set_selected_asking_option(
        spot,
        None if value == self._selected_asking_options[spot] else value,
    )

async def maybe_unlock_ask(self, spot: int) -> None:
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
        await self._unlock(spot)

async def maybe_unlock_give(self, spot: int) -> None:
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

async def maybe_unlock_pass_turn(self, spot: int) -> None:
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

async def maybe_unlock_play(self, spot: int):
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
        try:
            if hand > hip:
                await self._unlock(spot)
            else:
                raise PresidentsError(
                    "your current hand is weaker than the hand in play",
                    permitted=True,
                )
        except NotPlayableOnError as e:
            raise PresidentsError(str(e), permitted=True)

async def _pause_timers(self) -> None:
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
        assert self._timers[spot]
        # both turn and reserve timers stored in timers
        self._timers[spot].cancel()
        self._timers[spot] = None

        if not self._is_using_reserve_time(spot):
            self._turn_time_use_starts[spot] = None
            time_used = (
                now - self._turn_time_use_starts[spot]
            ).total_seconds()
            await self._set_time("turn", self._turn_times[spot] - time_used)
            self._paused_timers.append(
                lambda: self._start_timer("turn", spot)
            )
        else:
            self._reserve_time_use_starts[spot] = None
            time_used = (
                now - self._reserve_time_use_starts[spot]
            ).total_seconds()
            await self._set_time(
                "reserve", self._reserve_times[spot] - time_used
            )
            self._paused_timers.append(
                lambda: self._start_timer("reserve", spot)
            )
    else:  # elif self.trading
        self._trading_timer.cancel()
        self._trading_timer = None
        time_used = (now - self._trading_time_start).total_seconds()
        self._trading_time -= time_used
        self._trading_time_start = None
        self._paused_timers.append(lambda: self._start_timer("trading"))
        # giving timers if currently active
        for spot in self._get_asshole_and_vice_asshole():
            if not self._timers[spot]:
                continue
            self._timers[spot].cancel()
            self._timers[spot] = None
            time_used = (
                now - self._turn_time_use_starts[spot]
            ).total_seconds()
            self._turn_times[spot] -= time_used
            self._turn_time_use_starts[spot] = None
            self._paused_timers.append(
                lambda: self._start_timer("turn", spot)
            )

async def _post_pass_handler(self) -> None:
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

async def _post_play_handler(self, spot: int) -> None:
    if self._chambers[spot].is_empty:
        # player_finish takes care of going to the next player
        self._finishing_last_played = True
        await self._player_finish(spot)
    else:
        self._finishing_last_played = False
        await self._next_player()

async def _set_asshole(self, spot: int) -> None:
    await self._set_giver(spot, True)

async def _set_president(self, spot: int) -> None:
    await self._set_asker(spot, True, 2)

async def _set_vice_asshole(self, spot: int) -> None:
    await self._set_giver(spot, True)

async def _set_vice_president(self, spot: int) -> None:
    await self._set_asker(spot, True, 1)

async def _setup_round(self, *, deck: List[Iterable[int]] = None):
    assert self.num_players == 4, "four players required to start round"
    await self._deal_cards(deck=deck)

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
    await self._set_timer_state(which, False, spot)
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
        self._turn_time_use_starts[spot] = None
    elif which == "reserve":
        assert spot is not None
        if cancel and self._timers[spot] is not None:
            self._timers[spot].cancel()
        self._timers[spot] = None
        time_used = (
            now - self._reserve_time_use_starts[spot]
        ).total_seconds()
        await self._set_time(
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
        time_used = (now - self._trading_time_start).total_seconds()
        await self._set_time("trading", self._trading_time - time_used)
        self._trading_time_start = None

async def _wait_for_reply(self, asker_spot: int, asked_spot: int) -> None:
    await self._set_time("turn", self._giving_time, asked_spot, True)
    await self._set_selected_asking_option(asker_spot, None)
    self._waiting[asker_spot] = True

