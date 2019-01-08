from typing import Dict, List, Optional, Set, Union

from bidict import bidict
from flask_socketio import emit

try:
    from .game import Game, base_hand, PresidentsError
    from .emitting_chamber import EmittingChamber
    from .chamber import CardNotInChamberError
    from .hand import Hand, DuplicateCardError, FullHandError
except ImportError:
    from game import Game, base_hand, PresidentsError
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
            self._emit('set_spot', {'spot': spot}, sid)

    # game flow related methods

    def _next_player(self) -> None:
        try:  # current player is no longer on turn
            self._emit('set_on_turn', {'on_turn': False}, self._current_player_sid)
        except KeyError:  # self._current_player is None (round start)
            pass
        super()._next_player()
        self._emit('set_on_turn', {'on_turn': True}, self._current_player_sid)

    # card management related methods

    def add_or_remove_card(self, sid: str, card: int) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().add_or_remove_card(spot, card)
        except PresidentsError as e:
            self._emit_alert(str(e), sid)

    # TODO
    def store_hand(self, spot: int) -> None:
        super().store_hand(spot)

    # playing and passing related methods

    def maybe_unlock_play(self, spot: int, sid: str) -> None:
        try:
            super().maybe_unlock_play(spot)
        except PresidentsError as e:
            self._emit_alert(str(e), sid)

    def maybe_play_current_hand(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().maybe_play_current_hand(spot)
        except PresidentsError as e:
            self._emit_alert(str(e), sid)

    # TODO
    # def maybe_unlock_pass_turn(self, spot: int) -> None:

    def pass_turn(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().pass_turn(spot)
        except PresidentsError as e:
            self._emit_alert(str(e), sid)

    def _clear_hand_in_play(self) -> None:
        super()._clear_hand_in_play()
        self._emit_to_all_players('clear_hand_in_play', {})

    # trading related methods

    def _initiate_trading(self) -> None:
        # TODO: maybe just reset the entire game here
        super()._initiate_trading()
        self._emit_to_all_players('set_on_turn', {'on_turn': False})

    def set_selected_asking_option(self, sid: str, value: int) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().set_selected_asking_option(spot, value)
        except PresidentsError as e:
            self._emit_alert(str(e), sid)

    def maybe_unlock_ask(self, spot: int, sid: str) -> None:
        try:
            super().maybe_unlock_ask(spot)
        except PresidentsError as e:
            self._emit_alert(str(e), sid)

    def ask_for_card(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().ask_for_card(spot)
        except PresidentsError as e:
            self._emit_alert(str(e), sid)

    def _select_asking_option(self, spot: int, value: int) -> None:
        super()._select_asking_option(spot, value)
        self._emit('select_asking_option', {'value': value}, self._get_sid(spot))

    def _deselect_asking_option(self, spot: int, value: int) -> None:
        super()._deselect_asking_option(spot, value)
        self._emit('deselect_asking_option', {'value': value}, self._get_sid(spot))

    def maybe_unlock_give(self, spot: int, sid: str) -> None:
        try:
            super().maybe_unlock_give(spot)
        except PresidentsError as e:
            self._emit_alert(str(e), sid)

    def give_card(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().give_card(spot)
        except PresidentsError as e:
            self._emit_alert(str(e), sid)

    def _set_giving_options(self, spot: int, giving_options: Set[int]) -> None:
        super()._set_giving_options(spot, giving_options)
        self._emit('set_giving_options', {'options': list(giving_options), 'highlight': False}, self._get_sid(spot))

    def _clear_giving_options(self, spot: int) -> None:
        super()._clear_giving_options(spot)
        self._emit('set_giving_options', {'options': list(self._giving_options[spot]), 'highlight': False}, self._get_sid(spot))

    # misc

    def unlock_handler(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        if self.trading:
            if self._is_asking(spot):
                self.maybe_unlock_ask(spot, sid)
            elif self._is_giving(spot):
                self.maybe_unlock_give(spot, sid)
            else:
                self._emit_alert('you must select something before attempting to unlock', sid)
        else:
            self.maybe_unlock_play(spot, sid)

    def lock_handler(self, sid: str) -> None:
        self.lock(self._get_spot(sid))

    def _unlock(self, spot: int) -> None:
        super()._unlock(spot)
        self._emit('set_unlocked', {'unlocked': True}, self._get_sid(spot))

    def lock(self, spot: int) -> None:
        super().lock(spot)
        self._emit('set_unlocked', {'unlocked': False}, self._get_sid(spot))

    # getters

    def _get_sid(self, spot: int) -> str:
        return self._spot_sid_bidict[spot]

    def _get_spot(self, sid: str) -> int:
        return self._spot_sid_bidict.inv[sid]

    # setters

    def _set_hand_in_play(self, hand: Hand) -> None:
        super()._set_hand_in_play(hand)
        self._emit_to_all_players('set_hand_in_play', {
            'hand_in_play': hand.to_list(),
            'hand_in_play_desc': hand.id_desc
        })

    def _set_asker(self, spot: int, asker: bool, takes_and_gives: int) -> None:
        super()._set_asker(spot, asker, takes_and_gives)
        self._emit('set_asker', {'asker': asker}, self._get_sid(spot))

    def _set_trading(self, trading: bool) -> None:
        super()._set_trading(trading)
        self._emit_to_room('set_trading', {'trading': trading})

    def _set_giver(self, spot: int, giver: bool) -> None:
        self._emit('set_giver', {'giver': giver}, self._get_sid(spot))

    def _set_takes_remaining(self, spot: int, takes_remaining: int) -> None:
        super()._set_takes_remaining(spot, takes_remaining)
        self._emit('set_takes_remaining', {'takes_remaining': takes_remaining}, self._get_sid(spot))

    def _set_gives_remaining(self, spot: int, gives_remaining: int) -> None:
        super()._set_gives_remaining(spot, gives_remaining)
        self._emit('set_gives_remaining', {'gives_remaining': gives_remaining}, self._get_sid(spot))

    def _add_to_already_asked(self, spot: int, value: int) -> None:
        super()._add_to_already_asked(spot, value)
        self._emit('remove_asking_option', {'value': value}, self._get_sid(spot))

    # emitters

    def _emit(self, event: str, payload: Dict[str, Union[int, str, List[int]]], sid: str) -> None:
        emit(event, payload, room=sid)

    def _emit_to_all_players(self, event: str, payload: Dict[str, Union[int, str, List[int]]]):
        for sid in self._spot_sid_bidict.values():
            self._emit(event, payload, sid)

    def _emit_to_room(self, event: str, payload: Dict[str, Union[int, str, List[int]]]):
        self._emit(event, payload, self._room)

    # alerting related methods

    def _emit_alert(self, alert, sid: str) -> None:
        self._emit('alert', {'alert': alert}, sid)
