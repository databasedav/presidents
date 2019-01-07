from typing import Dict, List, Optional, Set, Union

from bidict import bidict
from flask_socketio import emit

try:
    from .game import Game, base_hand
    from .emitting_chamber import EmittingChamber
    from .chamber import CardNotInChamberError
    from .hand import Hand, DuplicateCardError, FullHandError
except ImportError:
    from game import Game, base_hand
    from emitting_chamber import EmittingChamber
    from chamber import CardNotInChamberError
    from hand import Hand, DuplicateCardError, FullHandError


class EmittingGame(Game):

    def __init__(self):

        super().__init__(populate_chambers=False)
        self._chambers: List[Optional[EmittingChamber]] = [
            EmittingChamber() for _ in range(4)
        ]
        self._room: Optional[str] = None
        self._spot_sid_bidict: bidict = bidict()
        self.num_spectators: int = 0  # TODO

    # properties

    @property
    def _current_player_sid(self) -> str:
        return self._get_sid(self._current_player)

    # setup related methods

    def set_room(self, room: str) -> None:
        self._room = room

    def add_player(self, sid: str, name: str) -> None:
        rand_open_spot: int = self._rand_open_spot()
        self._spot_sid_bidict.inv[sid] = rand_open_spot
        self._names[rand_open_spot] = name
        self.num_players += 1

    def remove_player(self, sid: str) -> None:
        self._spot_sid_bidict.inv.pop(sid)
        super().remove_player(self._get_spot(sid))

    def _deal_cards(self, testing: bool=False) -> None:
        decks = self._make_shuffled_decks(testing)
        for spot, sid in self._spot_sid_bidict.items():
            chamber = self._chambers[spot]
            chamber.reset()
            chamber.set_sid(sid)
            chamber.add_cards(decks[spot])
            self._emit_set_spot(spot, sid)

    # game flow related methods

    def _next_player(self, hand_won=False):
        try:
            self._emit_set_on_turn(self._current_player, False)
        except KeyError:  # self._current_player is None (round start)
            pass
        super()._next_player()
        self._emit_set_on_turn(self._current_player, True)

    # card management related methods

    def add_or_remove_card(self, sid: str, card: int) -> None:
        spot: int = self._get_spot(sid)
        chamber: EmittingChamber = self._chambers[spot]
        # TODO: verify to add or remove to be first empirically; may
        #       potentially justify looking before leaping if
        #       distribution is symmetric
        try:
            chamber.select_card(card)
            if self.is_asking(spot):
                self._deselect_asking_option(spot, self._selected_asking_option[spot])
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

    def maybe_play_current_hand(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
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

    def pass_turn(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
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
                self._emit_clear_hand_in_play_to_all_players()
                self._next_player()
                return
            else:
                self._next_player()
        # all other players passed on a hand
        elif self._num_consecutive_passes == self._num_unfinished_players - 1:
            self._hand_in_play = None
            self._emit_clear_hand_in_play_to_all_players()
            self._next_player(hand_won=True)
            # TODO: self._message_hand_won(self._current_player)
            return
        else:
            self._next_player()

    # trading related methods

    def _initiate_trading(self) -> None:
        # TODO: maybe just reset the entire game here
        self._current_player = None
        self._emit_clear_hand_in_play_to_all_players()
        self._emit_set_on_turn_to_all_players(False)
        self._deal_cards()
        self._set_trading(True)

    def update_selected_asking_option(self, sid: str, value: int) -> None:
        spot: int = self._get_spot(sid)
        if not self._is_asker(spot):
            self._alert_dont_use_console(spot)
            return
        if not 0 <= value <= 13:
            self._alert_dont_use_console(spot)
            return
        if self._is_already_asked(spot, value):
            self._alert_dont_use_console(spot)
            return
        selected_asking_option: int = self._selected_asking_option[spot]
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
        selected_asking_option: int = self._selected_asking_option[spot]
        # selected_asking_option is 0 if no trading option is selected
        if not selected_asking_option:
            self._alert_dont_use_console(spot)
        else:
            self._unlock(spot)

    def ask_for_card(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        if not self.trading:
            self._alert_dont_use_console(spot)
            return
        if not self._is_asker(spot):
            self._alert_dont_use_console(spot)
        # TODO: remove trading options when takes run out
        value = self._selected_asking_option[spot]
        asked_spot = self._get_opposing_position_spot(spot)
        # chamber for asked
        chamber = self._chambers[asked_spot]
        giving_options = {
            card for card in range((value - 1) * 4 + 1, value * 4 + 1) if card in chamber and card not in self._given[spot]
        }
        if not giving_options:
            self._add_to_already_asked(spot, value)
            self._remove_asking_option(spot, value)
        else:
            self._set_giving_options(asked_spot, giving_options)
            self._wait_for_reply(spot)

    def _select_asking_option(self, spot: int, value: int) -> None:
        self._selected_asking_option[spot] = value
        self._chambers[spot].deselect_selected()
        self.lock(spot)
        self._emit('select_asking_option', {'value': value}, self._get_sid(spot))

    def _deselect_asking_option(self, spot: int, value: int) -> None:
        self._selected_asking_option[spot] = 0
        self.lock(spot)
        self._emit('deselect_asking_option', {'value': value}, self._get_sid(spot))

    def _deselect_selected_asking_option(self, spot: int) -> None:
        self._deselect_asking_option(spot, self._selected_asking_option[spot])

    def _remove_asking_option(self, spot: int, value: int) -> None:
        self.lock(spot)
        self._emit('remove_asking_option', {'value': value}, self._get_sid(spot))

    def _wait_for_reply(self, spot: int) -> None:
        self._deselect_selected_asking_option(spot)
        self.lock(spot)
        self._waiting[spot] = True    

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
            if card in self._giving_options[spot]:
                self._unlock(spot)
            else:
                self._alert_can_only_give_a_giving_option(spot)
        elif self._is_asker(spot):
            if card in self._taken[spot]:
                self._alert_cannot_give_taken_card(spot)
            else:
                self._unlock(spot)

    def give_card(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        card = self._get_current_hand(spot)[4]
        giver_chamber: EmittingChamber = self._chambers[spot]
        asker_chamber: EmittingChamber = self._chambers[self._get_opposing_position_spot(spot)]
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

    def _set_giving_options(self, spot: int, giving_options: Set[int]) -> None:
        if giving_options:  # highlight
            highlight: bool = True
        else:  # unhighlight
            giving_options = self._giving_options[spot]
            highlight: bool = False
        self._emit_set_giving_options(spot, giving_options, highlight)
        self._giving_options[spot] = giving_options

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

    def unlock_handler(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        if self.trading:
            if self.is_asking(spot):
                self.maybe_unlock_ask(spot)
            elif self.is_giving(spot):
                self.maybe_unlock_give(spot)
        else:
            self.maybe_unlock_play(spot)

    def lock_handler(self, sid: str) -> None:
        self.lock(self._get_spot(sid))

    # getters

    def _get_sid(self, spot: int) -> str:
        return self._spot_sid_bidict[spot]

    def _get_spot(self, sid: str) -> int:
        return self._spot_sid_bidict.inv[sid]

    # setters

    def _set_hand_in_play(self, hand: Hand) -> None:
        super()._set_hand_in_play(hand)
        self._emit_set_hand_in_play_to_all_players(hand)

    def _set_asker(self, spot: int, asker: bool, takes_and_gives: int) -> None:
        super()._set_asker(spot, asker, takes_and_gives)
        self._emit_set_asker(spot, asker)

    def _set_trading(self, trading: bool) -> None:
        super()._set_trading(trading)
        self._emit_set_trading(trading)

    def _set_giver(self, spot: int, giver: bool) -> None:
        self._emit_set_giver(spot, giver)

    def _set_takes_remaining(self, spot: int, takes_remaining: int) -> None:
        super()._set_takes_remaining(spot, takes_remaining)
        self._emit_set_takes_remaining(spot, takes_remaining)

    def _set_gives_remaining(self, spot: int, gives_remaining: int) -> None:
        super()._set_gives_remaining(spot, gives_remaining)
        self._emit_set_gives_remaining(spot, gives_remaining)

    # emitters

    def _emit(self, event: str, payload: Dict[str, Union[int, str, List[int]]], spot_or_sid_or_room: Union[int, str]):
        # TODO: verify EAFP or LBYL empirically
        try:  # is a spot
            emit(event, payload, room=self._get_sid(spot_or_sid_or_room))
        except KeyError:  # is an sid or room
            emit(event, payload, room=spot_or_sid_or_room)

    def _emit_set_spot(self, spot: int, sid: str) -> None:
        self._emit('set_spot', {'spot': spot}, sid)

    def _emit_set_hand_in_play_to_all_players(self, hand: Hand) -> None:
        self._emit('set_hand_in_play', {
            'hand_in_play': hand.to_list(),
            'hand_in_play_desc': hand.id_desc}, self._room)

    def _emit_set_on_turn(self, spot: int, on_turn: bool) -> None:
        self._emit('set_on_turn', {'on_turn': on_turn}, spot)

    def _emit_set_unlocked(self, spot: int, unlocked: bool) -> None:
        self._emit('set_unlocked', {'unlocked': unlocked}, spot)

    def _emit_to_all_players(self, event: str, payload: Dict[str, Union[int, str, List[int]]]):
        for sid in self._spot_sid_bidict.values():
            self._emit(event, payload, sid)

    def _emit_to_room(self, event: str, payload: Dict[str, Union[int, str, List[int]]]):
        self._emit(event, payload, self._room)

    def _emit_clear_hand_in_play_to_all_players(self) -> None:
        self._emit('clear_hand_in_play', {}, self._room)

    def _emit_set_takes_remaining(self, spot: int, takes_remaining: int) -> None:
        self._emit('set_takes_remaining', {'takes_remaining': takes_remaining}, spot)

    def _emit_set_gives_remaining(self, spot: int, gives_remaining: int) -> None:
        self._emit('set_gives_remaining', {'gives_remaining': gives_remaining}, spot)

    def _emit_set_trading(self, trading: bool) -> None:
        self._emit('set_trading', {'trading': trading}, self._room)

    def _emit_set_asker(self, spot: int, asker: bool) -> None:
        self._emit('set_asker', {'asker': asker}, self._get_sid(spot))

    def _emit_set_giver(self, spot: int, giver: bool) -> None:
        self._emit('set_giver', {'giver': giver}, self._get_sid(spot))

    def _emit_set_giving_options(self, spot: int, giving_options: Set[int], highlight: bool) -> None:
        self._emit('set_giving_options', {'options': list(giving_options), 'highlight': highlight}, spot)

    def _emit_set_on_turn_to_all_players(self, on_turn: bool) -> None:
        self._emit_to_all_players('set_on_turn', {'on_turn': on_turn})  

    # alerting-related methods

    def _emit_alert(self, alert, spot: int) -> None:
        self._emit('alert', {'alert': alert}, spot)

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
