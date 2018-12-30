import random
from itertools import cycle
from typing import Any, Callable, Dict, List, Optional, Set, Union

import numpy as np
from bidict import bidict
from flask_socketio import emit

from emitting_chamber import EmittingChamber
from chamber import Chamber, CardNotInChamberError
from hand import Hand, DuplicateCardError, FullHandError


# TODO: make separate base game that does not emit for local testing
# TODO: nice way to remove asking options after takes are exhausted
# TODO: deal with mypy's treatment of nonetypes being passed into
#       functions that do not take them
# TODO: make Game JSON-serializable
# TODO: make class more manageable (or not)
# TODO: how to manage base Game alerts? Runtime errors?
# TODO: get rid of trivial getters and setters


class Game:

    def __init__(self) -> None:
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
        self._chambers: List[Optional[Chamber]] = [
            Chamber() for _ in range(4)
        ]
        self._hand_in_play: Optional[Union[BaseHand, Hand]] = base_hand
        self._num_consecutive_passes: int = 0
        self._winning_last_played: bool = False
        self._positions: List[int] = list()
        self._unlocked: List[bool] = [False for _ in range(4)]

        # trading related attributes
        self.trading: bool = False
        self._selected_asking_option: List[int] = [0 for _ in range(4)]
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

    def _make_shuffled_decks(self):
        deck = np.arange(1, 53, dtype=np.int32)  # deck of cards 1-52
        np.random.shuffle(deck)  # shuffles deck inplace
        decks = deck.reshape(4, 13)  # splits deck into 4 decks of 13
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
        return TurnManager(c3_index)

    # game flow related methods

    def _start_round(self) -> None:
        if not self._num_consecutive_rounds:
            self._create_chambers()
        self._deal_cards()
        self._make_and_set_turn_manager()
        self._next_player()

    def _next_player(self):
        self._current_player = next(self._turn_manager)
        # TODO: self._message_announce_turn()

    def _player_finish(self, spot: int) -> None:
        # TODO: self._message_player_finished_position(spot)
        self._positions.append(self._current_player)
        self._winning_last_played = True
        self._turn_manager.remove(self._current_player)
        num_unfinished_players = self._num_unfinished_players
        if num_unfinished_players == 3:
            self._set_president(spot)
            self._next_player()
        elif num_unfinished_players == 2:
            self._set_vice_president(spot)
            self._next_player()
        else:
            self._set_vice_asshole(spot)
            self._current_player = next(self._turn_manager)
            self._positions.append(self._current_player)
            self._set_asshole(self._current_player)
            self._initiate_trading()

    # card management related methods

    def add_or_remove_card(self, spot: int, card: int) -> None:
        chamber = self._chambers[spot]
        # TODO: verify to add or remove to be first empirically; may
        #       potentially justify looking before leaping if
        #       distribution is symmetric
        try:
            chamber.select_card(card)
            self.lock(spot)
        except CardNotInChamberError:
            self._alert_dont_modify_dom(spot)
            # TODO self._reset_card_values()
        except DuplicateCardError:
            # such an error can only occur if check passes
            chamber.deselect_card(card, check=False)
            self.lock(spot)
        except FullHandError:
            self._alert_hand_full(spot)

    # TODO
    def store_hand(self, spot: int) -> None:
        ...

    # playing and passing related methods

    def maybe_unlock_play(self, spot: int): 
        hand = self._get_current_hand(spot)
        if hand.is_empty:
            self._alert_add_cards_before_unlocking(spot)
            return
        if not hand.is_valid:
            self._alert_cannot_play_invalid_hand(spot)
            return
        hip = self._hand_in_play
        if hip is base_hand:  # start of the game
            if self._is_current_player(spot):  # player with 3 of clubs
                if 1 not in hand:  # card 1 is the 3 of clubs
                    self._alert_3_of_clubs(spot)
                    return
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
            if hand > hip:
                self._unlock(spot)
            else:
                self._alert_weaker_hand(spot)

    def maybe_play_current_hand(self, spot: int) -> None:
        if not self._is_current_player(spot):
            self._alert_can_only_play_on_turn(spot)
            return
        elif not self._unlocked[spot]:
            # store was modified to allow play emittal without unlocking
            self._alert_dont_modify_dom(spot)
            self.lock(spot)
            return
        else:
            chamber = self._chambers[spot]
            hand = Hand.copy(chamber.current_hand)
            chamber.remove_cards(hand)
            self._num_consecutive_passes = 0
            self.lock(spot)
            self._set_hand_in_play(hand)
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
            self._alert_can_only_pass_on_turn(spot)
            return
        hip = self._hand_in_play
        if hip is base_hand:
            self._alert_must_play_3_of_clubs(spot)
            return
        if hip is None:
            self._alert_can_play_any_hand(spot)
            return
        self._num_consecutive_passes += 1
        # TODO: self._message_passed(sid)
        # all remaining players passed on a winning hand
        if self._winning_last_played:
            if self._num_consecutive_passes == self._num_unfinished_players:
                self._hand_in_play = None
                self._emit_clear_hand_in_play()
                self._next_player()
                return
            else:
                self._next_player()
        # all other players passed on a hand
        elif self._num_consecutive_passes == self._num_unfinished_players - 1:
            self._hand_in_play = None
            self._emit_clear_hand_in_play()
            # TODO: self._message_hand_won(self._current_player)
            self._next_player(hand_won=True)
            return
        else:
            self._next_player()

    # trading related methods



    

    def _all_off_turn(self):
        self._emit('all_off_turn', {}, self._room)

    

    

    # getters



    # setters

    def _set_hand_in_play(self, hand: Hand) -> None:
        self._emit_set_hand_in_play(hand)
        self._hand_in_play = hand

    def _set_president(self, spot: int) -> None:
        self._set_asker(spot, 2)

    def _set_vice_president(self, spot: int) -> None:
        self._set_asker(spot, 1)

    def _set_vice_asshole(self, spot: int) -> None:
        self._set_giver(spot)

    def _set_asshole(self, spot: int) -> None:
        self._set_giver(spot)

    def _set_asker(self, spot: int, takes_and_gives: int) -> None:
        self._set_takes_remaining(spot, takes_and_gives)
        self._set_gives_remaining(spot, takes_and_gives)
        self._emit('set_asker', {}, self._get_sid(spot))

    def _set_giver(self, spot: int) -> None:
        self._emit('set_giver', {}, self._get_sid(spot))

    def _set_takes_remaining(self, spot: int, takes: int) -> None:
        self._takes_remaining[spot] = takes

    def _set_gives_remaining(self, spot: int, gives: int) -> None:
        self._gives_remaining[spot] = gives

    def _set_chamber(self, spot: int, chamber: Chamber) -> None:
        self._chambers[spot] = chamber



    # boolers

    def _is_current_player(self, spot: int) -> bool:
        return spot == self._current_player


    # emitters

    def _emit(self, event: str, payload: Dict[str, Union[int, str, List[int]]], spot_or_room: Union[int, str]):
        # TODO: verify EAFP or LBYL empirically
        try:  # is a spot
            emit(event, payload, room=self._get_sid(spot_or_room))
        except KeyError:  # is an sid
            emit(event, payload, room=spot_or_room)

    def _emit_set_spot(self, spot: int, sid: str) -> None:
        self._emit('set_spot', {'spot': spot}, sid)

    def _emit_set_hand_in_play(self, hand: Hand) -> None:
        self._emit('set_hand_in_play', {
            'hand_in_play': hand.to_list(),
            'hand_in_play_desc': hand.id_desc}, self._room)

    def _emit_flip_turn(self, spot: int) -> None:
        self._emit('flip_turn', {}, spot)

    

    def _emit_set_unlocked(self, spot: int, unlocked: bool) -> None:
        self._emit('set_unlocked', {'unlocked': unlocked}, spot)
    
    def test(self):
        _emit_to_all_players(self._emit_clear_hand_in_play)

    def _emit_to_all_players(self, emit_method: Callable[[int], None], payload: Dict[str, Union[int, str, List[int]]]):
        for sid in self.spot_sid_bidict.values():
            emit_method()
    

    

    

    

    

    

    
    
    def _unlock(self, spot: int) -> None:
        self._emit_set_unlocked(spot, True)
        self._set_unlocked(spot, True)

    def lock(self, spot: int) -> None:
        self._emit_set_unlocked(spot, False)
        self._set_unlocked(spot, False)

    
    

    def _emit_clear_hand_in_play(self) -> None:
        self._emit('clear_hand_in_play', {}, self._room)
    
    def _emit_clear_hand_in_play(self, spot: int) -> None:
        self._emit('clear_hand_in_play', {}, self._get_sid(spot))

    

    def _emit_to_room(self, emit_method: Callable[[int], None]):
        emit_method()

    
        

    def _initiate_trading(self) -> None:
        # TODO: maybe just reset the entire game here
        self._current_player = None
        self._emit_clear_hand_in_play()
        self._all_off_turn()
        self._deal_cards()
        self._set_trading(True)

    def _set_trading(self, trading: bool) -> None:
        self.trading = trading
        self._emit('set_trading', {'trading': trading}, self._room)

    def ask_for_card(self, spot: int) -> None:
        if not self.trading:
            self._alert_dont_use_console(spot)
            return
        if not self._is_asker(spot):
            self._alert_dont_use_console(spot)
        # TODO: remove trading options when takes run out
        value = self._get_selected_asking_option(spot)
        asked = self._get_opposing_position_spot(spot)
        # chamber for asked
        chamber = self._get_chamber(asked)
        giving_options = set()
        # TODO: set comprehension this maybe?
        for card in range((value - 1) * 4 + 1, value * 4 + 1):
            if card in chamber and card not in self._given[spot]:
                giving_options.add(card)
        if not giving_options:
            self._add_to_already_asked(spot, value)
            self._remove_asking_option(spot, value)
        else:
            self._set_giving_options(asked, giving_options)
            self._wait_for_reply(spot)

    def _add_to_given(self, spot: int, card: int) -> None:
        self._given[spot].add(card)

    def _remove_asking_option(self, spot: int, value: int) -> None:
        self.lock(spot)
        self._emit('remove_asking_option', {'value': value}, self._get_sid(spot))

    def _add_to_already_asked(self, spot: int, value: int) -> None:
        self._get_already_asked[spot].add(value)

    def _is_already_asked(self, spot: int, value: int) -> bool:
        return value in self._get_already_asked[spot]

    def _wait_for_reply(self, spot: int) -> None:
        self._deselect_selected_asking_option(spot)
        self.lock(spot)
        self._waiting[spot] = True

    def _is_waiting(self, spot: int) -> bool:
        return self._waiting[spot]

    def _highlight_giving_options(self, spot: int, giving_options: Set[int], highlight: bool) -> None:
        self._emit('highlight_giving_options', {'options': list(giving_options), 'highlight': highlight}, self._get_sid(spot))

    def _set_giving_options(self, spot: int, giving_options: Set[int]) -> None:
        if giving_options:
            highlight: bool = True
        else:
            giving_options = self._get_giving_options(spot)
            highlight: bool = False
        self._highlight_giving_options(spot, giving_options, highlight)
        self._giving_options[spot] = giving_options

    def _get_giving_options(self, spot: int) -> Set[int]:
        return self._giving_options[spot]

    def _get_position(self, spot: int) -> int:
        return self._positions.index(spot)

    def _get_opposing_position_spot(self, spot: int) -> int:
        return self._positions[3 - self._get_position(spot)]

    def update_selected_asking_option(self, spot: int, value: int) -> None:
        if not self._is_asker(spot):
            self._alert_dont_use_console(spot)
            return
        if not 0 <= value <= 13:
            self._alert_dont_use_console(spot)
            return
        if self._is_already_asked(spot, value):
            self._alert_dont_use_console(spot)
            return
        selected_asking_option: int = self._get_selected_asking_option(spot)
        if selected_asking_option == 0:
            self._select_asking_option(spot, value)
        elif selected_asking_option == value:
            self._deselect_asking_option(spot, value)
        else:
            self._deselect_asking_option(spot, selected_asking_option)
            self._select_asking_option(spot, value)

    def maybe_unlock_ask(self, spot: int) -> None:
        if not self.trading:
            self._alert_dont_use_console(spot)
            return
        if not self._is_asker(spot):
            self._alert_dont_use_console(spot)
            return
        if self._is_waiting(spot):
            self._alert_cannot_ask_while_waiting(spot)
            return
        if not self._has_takes_remaining(spot):
            self._alert_no_takes_remaining(spot)
            return
        selected_asking_option: int = self._get_selected_asking_option(spot)
        # selected_asking_option is 0 if no trading option is selected
        if not selected_asking_option:
            self._alert_dont_use_console(spot)
        else:
            self._unlock(spot)

    def is_asking(self, spot: int) -> bool:
        return self.trading and self._get_selected_asking_option(spot) > 0

    def is_giving(self, spot: int) -> bool:
        return self.trading and not self._get_current_hand(spot).is_empty

    def _select_asking_option(self, spot: int, value: int) -> None:
        self._set_selected_asking_option(spot, value)
        self._chambers[spot].deselect_selected()
        self.lock(spot)
        self._emit('select_asking_option', {'value': value}, self._get_sid(spot))

    def _deselect_asking_option(self, spot: int, value: int) -> None:
        self._set_selected_asking_option(spot, 0)
        self.lock(spot)
        self._emit('deselect_asking_option', {'value': value}, self._get_sid(spot))

    def _set_selected_asking_option(self, spot: int, value: int) -> None:
        self._selected_asking_option[spot] = value

    def _get_selected_asking_option(self, spot: int) -> int:
        return self._selected_asking_option[spot]

    def _deselect_selected_asking_option(self, spot: int) -> None:
        self._deselect_asking_option(spot, self._get_selected_asking_option(spot))

    def maybe_unlock_give(self, spot: int) -> None:
        if not self.trading:
            self._alert_dont_use_console(spot)
            return
        if self._is_asker(spot) and not self._has_gives_remaining(spot):
            self._alert_no_gives_remaining(spot)
            return
        hand: Hand = self._get_current_hand(spot)
        if hand.is_empty:
            self._alert_add_cards_before_unlocking(spot)
            return
        # TODO: add ability to give valid/invalid 2 card hand
        if not hand.is_single:
            self._alert_can_only_give_singles(spot)
            return
        card: int = hand[4]
        if self._is_giver(spot):
            if card in self._get_giving_options(spot):
                self._unlock(spot)
            else:
                self._alert_can_only_give_a_giving_option(spot)
        elif self._is_asker(spot):
            if card in self._get_taken(spot):
                self._alert_cannot_give_taken_card(spot)
            else:
                self._unlock(spot)

    def give_card(self, spot: int) -> None:
        card = self._get_current_hand(spot)[4]
        giver_chamber: EmittingChamber = self._chambers[spot]
        asker_chamber: EmittingChamber = self._get_chamber(self._get_opposing_position_spot(spot))
        giver_chamber.remove_card(card)
        asker_chamber.add_card(card)
        if self._is_asker(spot):
            self._add_to_given(spot, card)
            self._decrement_gives_remaining(spot)
        elif self._is_giver(spot):
            self._set_giving_options(spot, set())
            asker_spot = self._get_opposing_position_spot(spot)
            self._add_to_taken(asker_spot, card)
            self._decrement_takes_remaining(asker_spot)
            self._waiting[asker_spot] = False
        self.lock(spot)

    def _get_takes_remaining(self, spot: int) -> int:
        return self._takes_remaining[spot]

    def _has_takes_remaining(self, spot: int) -> bool:
        return self._get_takes_remaining(spot) > 0

    def _decrement_takes_remaining(self, spot: int) -> None:
        self._takes_remaining[spot] -= 1
        # TODO: remove asking options when no takes remaining
        if self._no_takes_or_gives_remaining:
            self._end_trading()

    def _get_gives_remaining(self, spot: int) -> int:
        return self._gives_remaining[spot]

    def _has_gives_remaining(self, spot: int) -> bool:
        return self._get_gives_remaining(spot) > 0

    def _decrement_gives_remaining(self, spot: int) -> None:
        self._gives_remaining[spot] -= 1
        if self._no_takes_or_gives_remaining:
            self._end_trading()

    def _get_taken(self, spot: int) -> Set[int]:
        return self._taken[spot]

    

    def _add_to_taken(self, spot: int, card: int) -> None:
        self._get_taken(spot).add(card)

    def _end_trading(self) -> None:
        # setup turn manager based on cards in chambers since the 3 of
        # clubs may have changed hands
        decks = self._get_decks_from_chambers()
        c3_index = np.where(decks == 1)[0][0]  # get which deck has the 3 of clubs
        self._turn_manager = TurnManager(c3_index)
        self._set_trading(False)
        self._hand_in_play = base_hand
        self._next_player()

    def _get_decks_from_chambers(self):
        deck = list()
        for chamber in self._chambers:
            deck.extend(chamber)
        return np.array(deck).reshape(4, 13)

    def _get_sid(self, spot: int) -> str:
        return self.spot_sid_bidict[spot]

    def get_spot(self, sid: str) -> int:
        return self.spot_sid_bidict.inv[sid]

    def _get_president_and_vice_president(self) -> List[int]:
        return self._positions[0:2]

    def _is_asker(self, spot: int) -> bool:
        return spot in self._get_president_and_vice_president()

    def _get_asshole_and_vice_asshole(self) -> List[int]:
        return self._positions[2:4]

    def _is_giver(self, spot: int) -> bool:
        return spot in self._get_asshole_and_vice_asshole()

    def _get_current_hand(self, spot: int) -> Hand:
        return self._chambers[spot].current_hand

    def _set_unlocked(self, spot: int, unlocked: bool) -> None:
        self._unlocked[spot] = unlocked

    def _get_current_player_name(self) -> str:
        return self._names[self._current_player]

    # alerting-related methods

    def _emit_alert(self, alert, spot: int) -> None:
        self._emit('alert', {'alert': alert}, self._get_sid(spot))

    def _alert_cannot_play_invalid_hand(self, spot: int) -> None:
        self._emit_alert("you can't play invalid hands", spot)

    def _alert_3_of_clubs(self, spot: int) -> None:
        self._emit_alert('the first hand must contain the 3 of clubs', spot)

    def _alert_must_play_3_of_clubs(self, spot: int) -> None:
        self._emit_alert('you cannot pass when you have the 3 of clubs', spot)

    def _alert_hand_full(self, spot: int) -> None:
        self._emit_alert('your current hand is full', spot)

    def _alert_weaker_hand(self, spot: int) -> None:
        self._emit_alert('your current hand is weaker than the hand in play', spot)

    def _alert_dont_modify_dom(self, spot: int) -> None:
        self._emit_alert("please don't hax the dom", spot)

    def _alert_dont_use_console(self, spot: int) -> None:
        self._emit_alert("please don't hax with console", spot)

    def _alert_can_only_play_on_turn(self, spot: int) -> None:
        self._emit_alert("you can only play a hand on your turn", spot)

    def _alert_add_cards_before_unlocking(self, spot: int) -> None:
        self._emit_alert("you must add cards before attempting to unlock", spot)

    def _alert_can_only_pass_on_turn(self, spot: int) -> None:
        self._emit_alert("you can only pass on your turn", spot)

    def _alert_can_play_any_hand(self, spot: int) -> None:
        self._emit_alert("you can play any hand", spot)

    def _alert_can_only_give_singles(self, spot: int) -> None:
        self._emit_alert("you can only give singles", spot)

    def _alert_cannot_ask_while_waiting(self, spot: int) -> None:
        self._emit_alert("you cannot ask while waiting for a response", spot)

    def _alert_can_only_give_a_giving_option(self, spot: int) -> None:
        self._emit_alert("you can only give a highlighted option", spot)

    def _alert_cannot_give_taken_card(self, spot: int) -> None:
        self._emit_alert("you cannot give a card you took", spot)

    def _alert_no_takes_remaining(self, spot: int) -> None:
        self._emit_alert("you have no takes remaining", spot)

    def _alert_no_gives_remaining(self, spot: int) -> None:
        self._emit_alert("you have no gives remaining", spot)

    # def _message_hand_played(self, sid: str, hand: Hand):
    #     self._emit_alert("please don't hax", sid)

    # def _message_current_player_finished_position(self, sid: str):
    #     name = self._get_name(sid)
    #     # emit("message")
    #     ...


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
