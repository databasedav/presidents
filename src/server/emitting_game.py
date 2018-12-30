from typing import Optional

from bidict import bidict

from game import Game
from emitting_chamber import EmittingChamber
from chamber import Chamber, CardNotInChamberError
from hand import Hand, DuplicateCardError, FullHandError


class EmittingGame(Game):

    def __init__(self):

        super().__init__()
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
        self.spot_sid_bidict.inv[sid] = rand_open_spot
        self._names[rand_open_spot] = name
        self.num_players += 1

    def remove_player(self, sid: str) -> None:
        self.spot_sid_bidict.inv.pop(sid)
        super().remove_player(self._get_spot(sid))

    def _deal_cards(self) -> None:
        decks = self._generate_shuffled_decks()
        for spot, sid in self.spot_sid_bidict.items():
            chamber = self._chambers[spot]
            chamber.reset()
            chamber.set_sid(sid)
            chamber.add_cards(decks[spot])
            self._emit_set_spot(spot, sid)
    
    # game flow related methods

    def _next_player(self, hand_won=False):
        try:
            self._emit_set_on_turn(self._current_player, False)
        except KeyError:  # self._current_player is None
            pass
        super()._next_player()
        self._emit_set_on_turn(self._current_player, True)

    # card management related methods

    def add_or_remove_card(self, spot: int, card: int) -> None:
        chamber = self._get_chamber(spot)
        # TODO: verify to add or remove to be first empirically; may
        #       potentially justify looking before leaping if
        #       distribution is symmetric
        try:
            chamber.select_card(card)
            if self.is_asking(spot):
                self._deselect_asking_option(spot, self._get_selected_asking_option(spot))
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
        elif not self._get_unlocked(spot):
            # store was modified to allow play emittal without unlocking
            self._alert_dont_modify_dom(spot)
            self.lock(spot)
            return
        else:
            chamber = self._get_chamber(spot)
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

    # emitters

    def _emit_set_on_turn(self, spot: int, on_turn: bool) -> None:
        self._emit('set_on_turn', {'on_turn': on_turn}, spot)

    # messagers

    # alerters

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