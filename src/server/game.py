import random
from eventlet import sleep
from eventlet.timeout import Timeout
from itertools import cycle
from typing import Any, Callable, Dict, List, Optional, Set, Union

import numpy as np

try:
    from .emitting_chamber import EmittingChamber
    from .chamber import Chamber, CardNotInChamberError
    from .hand import Hand, DuplicateCardError, FullHandError
    from .utils.utils import rank_articler
except ImportError:
    from emitting_chamber import EmittingChamber
    from chamber import Chamber, CardNotInChamberError
    from hand import Hand, DuplicateCardError, FullHandError
    from utils.utils import rank_articler


# TODO: fix this class based on functional differences with emitting
#       version, i.e. not having to emit
# TODO: nice way to remove asking options after takes are exhausted
# TODO: deal with mypy's treatment of nonetypes being passed into
#       functions that do not take them
# TODO: make Game JSON-serializable
# TODO: make class more manageable (or not)
# TODO: how to manage base Game alerts? Runtime errors?
# TODO: get rid of trivial getters and setters; only functional setters
#       should be those that also emit in EmittingGame


class Game:

    def __init__(self, populate_chambers: bool=True) -> None:
        """
        Represents a 'game' of presidents. Operates on 'spots'
        attempting confirmation/allowal of certain moves (e.g. unlocking
        play, unlocking pass, etc.), and then actually carrying out
        those moves and changing the game state as necessary.
        """

        # instance related attributes
        self.num_players: int = 0
        self._num_consecutive_rounds: int = 0  # TODO

        # setup and ID related attributes
        self._open_spots = {i for i in range(4)}
        self._names: List[Optional[str]] = [None for _ in range(4)]

        # game related attributes
        self._turn_manager: Optional[TurnManager] = None
        self._current_player: Optional[int] = None
        if populate_chambers:
            self._chambers: List[Optional[Chamber]] = [
                Chamber() for _ in range(4)
            ]
        self._hand_in_play: Optional[Union[BaseHand, Hand]] = base_hand
        self._num_consecutive_passes: int = 0
        self._winning_last_played: bool = False
        self._positions: List[int] = list()
        self._unlocked: List[bool] = [False for _ in range(4)]
        self._timers: List[Optional[Timeout]] = [None for _ in range(4)]

        # trading related attributes
        self.trading: bool = False
        self._selected_asking_option: List[Optional[int]] = [None for _ in range(4)]
        self._already_asked: List[Set[int]] = [set() for _ in range(4)]
        self._waiting: List[bool] = [False for _ in range(4)]
        self._giving_options: List[Optional[Set[int]]] = [
            None for _ in range(4)
        ]
        self._takes_remaining: List[int] = [0 for _ in range(4)]
        self._gives_remaining: List[int] = [0 for _ in range(4)]
        self._given: List[Set[int]] = [set() for _ in range(4)]
        self._taken: List[Set[int]] = [set() for _ in range(4)]

    # properties

    @property
    def _num_unfinished_players(self):
        return self._turn_manager._num_unfinished_players

    @property
    def _no_takes_or_gives_remaining(self) -> bool:
        return not any(self._takes_remaining) and not any(self._gives_remaining)

    # testing related methods TODO: make a separate class for these

    def get_game_to_trading(self) -> None:
        """
        For use when testing to quickly get to trading state from 4 card
        state, i.e. each player has one of the 3's.
        """
        while not self.trading:
            spot: int = self._current_player
            chamber = self._chambers[spot]
            for card in chamber:
                if card not in chamber.current_hand:
                    self.add_or_remove_card(spot, card)
                self.maybe_unlock_play(spot)
                if self._unlocked[spot]:
                    self.maybe_play_current_hand(spot)
                else:
                    self.pass_turn(spot)

    # setup related methods

    def _rand_open_spot(self):
        """
        Returns random open spot. Should not happen when there are no
        open spots.
        """
        assert self._open_spots
        spot = random.sample(self._open_spots, 1)[0]
        self._open_spots.remove(spot)
        return spot

    def add_player(self, name: str) -> None:
        self._names[self._rand_open_spot()] = name
        self.num_players += 1

    def remove_player(self, spot: int) -> None:
        self._names[spot] = None
        self._open_spots.add(spot)
        self.num_players -= 1

    def _make_shuffled_decks(self, testing: bool=False):
        deck = np.arange(1, 53 if not testing else 5, dtype=np.int32)  # deck of cards 1-52
        np.random.shuffle(deck)  # shuffles deck inplace
        decks = deck.reshape(4, 13 if not testing else 1)  # splits deck into 4 decks of 13
        decks.sort(axis=1)  # sorts individual decks
        return decks

    def _deal_cards(self) -> None:
        decks = self._make_shuffled_decks()
        for spot in zip(range(4), decks):
            chamber = self._chambers[spot]
            chamber.reset()
            chamber.add_cards(decks)
    
    def _make_and_set_turn_manager(self) -> None:
        decks = self._get_decks_from_chambers()
        # get which deck has the 3 of clubs
        c3_index = np.where(decks == 1)[0][0]
        self._turn_manager = TurnManager(c3_index)

    # game flow related methods

    def _start_round(self, testing: bool=False) -> None:
        self._deal_cards(testing)
        self._make_and_set_turn_manager()
        self._num_consecutive_rounds += 1
        self._message(f'round {self._num_consecutive_rounds} has begun')
        self._next_player()

    def _next_player(self):
        self._current_player = next(self._turn_manager)
        self._message(f"it's {self._names[self._current_player]}'s turn")
        self._start_timer(self._current_player, 2)

    def _start_timer(self, spot: int, seconds: int) -> None:
        self._timers[spot] = Timeout(seconds, PresidentsError('you ran out of time; using reserve time'))
        try:
            sleep(seconds + 1)
        finally:
            self._auto_play_or_pass(spot)

    def _auto_play_or_pass(self, spot: int) -> None:
        if self._hand_in_play is base_hand:
            self._chambers[spot].deselect_selected()
            self.add_or_remove_card(spot, 1)
            self._unlock(spot)
            self.maybe_play_current_hand(spot)
    
    def _stop_timer(self, spot: int) -> None:
        self._timers[spot].cancel()


    def _player_finish(self, spot: int) -> None:
        # TODO: self._message_player_finished_position(spot)
        self._positions.append(self._current_player)
        self._winning_last_played = True
        self._turn_manager.remove(self._current_player)
        num_unfinished_players = self._num_unfinished_players
        if num_unfinished_players == 3:
            self._set_president(spot)
            self._message(f'{self._names[spot]} is president')
            self._next_player()
        elif num_unfinished_players == 2:
            self._set_vice_president(spot)
            self._message(f'{self._names[spot]} is vice president')
            self._next_player()
        else:
            self._set_vice_asshole(spot)
            self._current_player = next(self._turn_manager)
            self._positions.append(self._current_player)
            self._set_asshole(self._current_player)
            self._message(f'{self._names[spot]} is vice asshole and {self._names[self._current_player]} is asshole')
            self._initiate_trading()

    # card control related methods

    def add_or_remove_card(self, spot: int, card: int) -> None:
        chamber: Chamber = self._chambers[spot]
        # TODO: verify to add or remove to be first empirically; may
        #       potentially justify looking before leaping if
        #       distribution is symmetric
        try:
            chamber.select_card(card)
            if self._is_asking(spot):
                self._deselect_asking_option(spot, self._selected_asking_option[spot])
            self._lock_if_unlocked(spot)
        except CardNotInChamberError:
            # TODO: console use or dom modification
            raise PresidentsError("you don't have this card")
            # TODO self._reset_card_values()
        except DuplicateCardError:
            # such an error can only occur if check passes
            chamber.deselect_card(card, check=False)
            self._lock_if_unlocked(spot)
        except FullHandError:
            raise PresidentsError('your current hand is full')

    # TODO
    def store_hand(self, spot: int) -> None:
        ...

    # playing and passing related methods

    def maybe_unlock_play(self, spot: int):
        hand = self._get_current_hand(spot)
        if hand.is_empty:
            raise PresidentsError('you must add cards before attempting to unlock')
        if not hand.is_valid:
            raise PresidentsError("you can't play invalid hands")
        hip = self._hand_in_play
        if hip is base_hand:  # start of the game
            if self._is_current_player(spot):  # player with 3 of clubs
                if 1 not in hand:  # card 1 is the 3 of clubs
                    raise PresidentsError('the first hand must contain the 3 of clubs')
                else:
                    # any hand with the 3 of clubs is ok
                    self._unlock(spot)
            else:
                # other players (without the 3 of clubs) can unlock
                # whatever hand they want
                self._unlock(spot)
        elif hip is None:  # current player won last hand and can play any hand
            self._unlock(spot)
        else:
            try:
                if hand > hip:
                    self._unlock(spot)
                else:
                    raise PresidentsError('your current hand is weaker than the hand in play')
            except RuntimeError as e:  # hands are not comparable
                raise PresidentsError(str(e))

    def maybe_play_current_hand(self, spot: int) -> None:
        if not self._is_current_player(spot):
            raise PresidentsError('you can only play a hand on your turn')
        elif not self._unlocked[spot]:
            # TODO: console use or dom modification
            self.lock(spot)
            raise PresidentsError('you must unlock before playing')
        else:
            chamber = self._chambers[spot]
            hand = Hand.copy(chamber.current_hand)
            chamber.remove_cards(hand)
            self._num_consecutive_passes = 0
            self._set_hand_in_play(hand)
            self._message(f'{self._names[spot]} played a {hand.id_desc}')
            self.lock(spot)
            # lock others if their currently unlocked hand should no longer be unlocked
            other_spots = [other_spot for other_spot in range(4) if other_spot != spot]
            for other_spot in other_spots:
                if self._unlocked[other_spot]:
                    try:
                        if self._get_current_hand(other_spot) < self._hand_in_play:
                            self.lock(other_spot)
                    except RuntimeError:  # can occur when a bomb is played on a non bomb
                        self.lock(other_spot)
            # TODO: self._message_hand_played(hand)
            if chamber.is_empty:
                # player_finish takes care of going to the next player
                self._player_finish(spot)
            else:
                self._next_player()
                self._winning_last_played = False

    # TODO
    # def maybe_unlock_pass_turn(self, spot: int) -> None:

    def pass_turn(self, spot: int) -> None:
        if not self._is_current_player(spot):
            raise PresidentsError('you can only pass on your turn')
        if self._hand_in_play is base_hand:
            raise PresidentsError('you cannot pass when you have the 3 of clubs')
        if self._hand_in_play is None:
            raise PresidentsError('you can play any hand')
        self._num_consecutive_passes += 1
        self._message(f'{self._names[spot]} passed')
        # all remaining players passed on a winning hand
        if self._winning_last_played:
            if self._num_consecutive_passes == self._num_unfinished_players:
                self._clear_hand_in_play()
                self._next_player()
            else:
                self._next_player()
        # all other players passed on a hand
        elif self._num_consecutive_passes == self._num_unfinished_players - 1:
            self._clear_hand_in_play()
            self._next_player()
            # TODO: self._message_hand_won(self._current_player)
        else:
            self._next_player()

    def _clear_hand_in_play(self) -> None:
        self._hand_in_play = None

    # trading related methods

    def _initiate_trading(self) -> None:
        # TODO: maybe just reset the entire game here
        self._current_player = None
        self._clear_hand_in_play()
        self._deal_cards()
        self._set_trading(True)
        self._message('trading has begun')

    def set_selected_asking_option(self, spot: int, value: int) -> None:
        if not self._is_asker(spot):
            # TODO: console use or dom modification
            raise PresidentsError('you are not an asker')
        if not 0 <= value <= 13:
            # TODO: console use or dom modification
            raise PresidentsError('you cannot ask for this value')
        if self._is_already_asked(spot, value):
            # TODO: console use or dom modification
            raise PresidentsError('you already asked for this value')
        selected_asking_option: int = self._selected_asking_option[spot]
        if selected_asking_option is None:
            self._select_asking_option(spot, value)
        elif selected_asking_option == value:
            self._deselect_asking_option(spot, value)
        else:
            self._deselect_asking_option(spot, selected_asking_option)
            self._select_asking_option(spot, value)

    def maybe_unlock_ask(self, spot: int) -> None:
        if not self.trading:
            # TODO: console use or dom modification
            raise PresidentsError('trading is not ongoing')
        if not self._is_asker(spot):
            # TODO: console use or dom modification
            raise PresidentsError('you are not an asker')
        if self._is_waiting(spot):
            raise PresidentsError('you cannot ask while waiting for a response')
        if not self._has_takes_remaining(spot):
            raise PresidentsError('you have no takes remaining')
        # selected_asking_option is None if no trading option is selected
        if not self._selected_asking_option[spot]:
            # TODO: console use or dom modification
            raise PresidentsError('you have not selected an asking option')
        else:
            self._unlock(spot)

    def ask_for_card(self, spot: int) -> None:
        if not self.trading:
            # TODO: console use or dom modification
            raise PresidentsError('trading is not ongoing')
        if not self._is_asker(spot):
            # TODO: console use or dom modification
            raise PresidentsError('you are not an asker')
        if not self._unlocked[spot]:
            # TODO: console use or dom modification
            self.lock(spot)
            raise PresidentsError('you must unlock before asking')
        # TODO: remove trading options when takes run out
        value = self._selected_asking_option[spot]
        articled_rank = rank_articler(value)
        asked_spot = self._get_opposing_position_spot(spot)
        self._message(f'{self._names[spot]} asks {self._names[asked_spot]} for {articled_rank}')
        # chamber for asked
        chamber = self._chambers[asked_spot]
        giving_options = {
            card for card in range((value - 1) * 4 + 1, value * 4 + 1) if card in chamber and card not in self._given[spot]
        }
        if not giving_options:
            self._message(f'{self._names[asked_spot]} does not have such a card')
            self.lock(spot)
            self._add_to_already_asked(spot, value)
        else:
            self._set_giving_options(asked_spot, giving_options)
            self._wait_for_reply(spot)

    def _select_asking_option(self, spot: int, value: int) -> None:
        self._selected_asking_option[spot] = value
        self._chambers[spot].deselect_selected()
        self._lock_if_unlocked(spot)

    def _deselect_asking_option(self, spot: int, value: int) -> None:
        self._selected_asking_option[spot] = None
        self._lock_if_unlocked(spot)

    def _deselect_selected_asking_option(self, spot: int) -> None:
        self._deselect_asking_option(spot, self._selected_asking_option[spot])

    def _wait_for_reply(self, spot: int) -> None:
        self._deselect_selected_asking_option(spot)
        self._waiting[spot] = True

    def maybe_unlock_give(self, spot: int) -> None:
        if not self.trading:
            # TODO: console use or dom modification
            raise PresidentsError('trading is not ongoing')
        if self._is_asker(spot) and not self._has_gives_remaining(spot):
            raise PresidentsError('you have no gives remaining')
        hand: Hand = self._get_current_hand(spot)
        if hand.is_empty:
            raise PresidentsError('you must add cards before attempting to unlock')
        # TODO: add ability to give valid/invalid 2 card hand
        if not hand.is_single:
            raise PresidentsError('you can only give singles')
        card: int = hand[4]
        if self._is_giver(spot):
            if card in self._giving_options[spot]:
                self._unlock(spot)
            else:
                raise PresidentsError('you can only give a highlighted option')
        elif self._is_asker(spot):
            if card in self._taken[spot]:
                raise PresidentsError('you cannot give a card you took')
            else:
                self._unlock(spot)

    def give_card(self, spot: int) -> None:
        if not self._unlocked[spot]:
            # TODO: console use or dom modification
            self.lock(spot)
            raise PresidentsError('you must unlock before giving')
        card = self._get_current_hand(spot)[4]
        giver_chamber: Chamber = self._chambers[spot]
        receiver_spot: int = self._get_opposing_position_spot(spot)
        receiver_chamber: Chamber = self._chambers[receiver_spot]
        giver_chamber.remove_card(card)
        receiver_chamber.add_card(card)
        self._message(f'{self._names[spot]} gives {self._names[receiver_spot]} a card')
        if self._is_asker(spot):
            self._add_to_given(spot, card)
            self._decrement_gives_remaining(spot)
        elif self._is_giver(spot):
            self._clear_giving_options(spot)
            self._add_to_taken(receiver_spot, card)
            self._decrement_takes_remaining(receiver_spot)
            self._waiting[receiver_spot] = False
        self.lock(spot)

    def _set_giving_options(self, spot: int, giving_options: Set[int]) -> None:
        self._giving_options[spot] = giving_options

    def _clear_giving_options(self, spot: int) -> None:
        self._giving_options[spot].clear()

    def _decrement_takes_remaining(self, spot: int) -> None:
        self._takes_remaining[spot] -= 1
        # TODO: remove asking options when no takes remaining
        if self._no_takes_or_gives_remaining:
            self._end_trading()

    def _decrement_gives_remaining(self, spot: int) -> None:
        self._gives_remaining[spot] -= 1
        if self._no_takes_or_gives_remaining:
            self._end_trading()

    def _end_trading(self) -> None:
        self._set_trading(False)
        self._hand_in_play = base_hand
        self._make_and_set_turn_manager()
        self._next_player()

    # misc

    def _unlock(self, spot: int) -> None:
        self._unlocked[spot] = True

    def lock(self, spot: int) -> None:
        self._unlocked[spot] = False

    def _lock_if_unlocked(self, spot: int) -> None:
        if self._unlocked[spot]:
            self.lock(spot)

    def _message(self, message: str) -> None:
        print(message)

    # getters

    def _get_position(self, spot: int) -> int:
        return self._positions.index(spot)

    def _get_opposing_position_spot(self, spot: int) -> int:
        return self._positions[3 - self._get_position(spot)]

    def _get_decks_from_chambers(self):
        deck = list()
        for chamber in self._chambers:
            deck.extend(chamber)
        try:
            return np.array(deck).reshape(4, 13)
        except:  # TODO: this is caught during testing
            return np.array(deck).reshape(4, 1)

    def _get_president_and_vice_president(self) -> List[int]:
        return self._positions[0:2]

    def _get_asshole_and_vice_asshole(self) -> List[int]:
        return self._positions[2:4]

    def _get_current_hand(self, spot: int) -> Hand:
        return self._chambers[spot].current_hand

    def _get_current_player_name(self) -> str:
        return self._names[self._current_player]

    # setters

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
        self._set_takes_remaining(spot, takes_and_gives)
        self._set_gives_remaining(spot, takes_and_gives)

    def _set_trading(self, trading: bool) -> None:
        self.trading = trading

    def _set_giver(self, spot: int, giver: bool) -> None:
        # TODO: is this the correct way to do this?; i.e. a case where
        #       the base game class need not do anything when setting
        #       the giver
        pass

    def _set_takes_remaining(self, spot: int, takes_remaining: int) -> None:
        self._takes_remaining[spot] = takes_remaining

    def _set_gives_remaining(self, spot: int, gives_remaining: int) -> None:
        self._gives_remaining[spot] = gives_remaining

    def _add_to_given(self, spot: int, card: int) -> None:
        self._given[spot].add(card)

    def _add_to_already_asked(self, spot: int, value: int) -> None:
        self._deselect_asking_option(spot, value)  # TODO: this results in an extra emit
        self._already_asked[spot].add(value)

    def _add_to_taken(self, spot: int, card: int) -> None:
        self._taken[spot].add(card)

    # boolers

    def _is_current_player(self, spot: int) -> bool:
        return spot == self._current_player

    def _is_asking(self, spot: int) -> bool:
        return self.trading and self._selected_asking_option[spot] is not None

    def _is_giving(self, spot: int) -> bool:
        return self.trading and not self._get_current_hand(spot).is_empty

    def _has_takes_remaining(self, spot: int) -> bool:
        return self._takes_remaining[spot] > 0

    def _has_gives_remaining(self, spot: int) -> bool:
        return self._gives_remaining[spot] > 0

    def _is_asker(self, spot: int) -> bool:
        return spot in self._get_president_and_vice_president()

    def _is_giver(self, spot: int) -> bool:
        return spot in self._get_asshole_and_vice_asshole()

    def _is_already_asked(self, spot: int, value: int) -> bool:
        return value in self._already_asked[spot]

    def _is_waiting(self, spot: int) -> bool:
        return self._waiting[spot]


class BaseHand:
    """hand at begininning of game; 3 of clubs must be played on it"""
    pass
base_hand = BaseHand()


class TurnManager:

    def __init__(self, first) -> None:
        self._cycling_list = cycle([i for i in range(4)])
        for _ in range(first):
            next(self._cycling_list)
        self._not_finished_dict: Dict[int, bool] = {i: True for i in range(4)}
        self._num_unfinished_players = 4

    def __next__(self) -> int:
        maybe_next = next(self._cycling_list)
        while self._not_finished_dict[maybe_next] is False:
            maybe_next = next(self._cycling_list)
        return maybe_next

    def remove(self, spot: int) -> None:
        self._not_finished_dict[spot] = False
        self._num_unfinished_players -= 1


class PresidentsError(RuntimeError):
    pass
