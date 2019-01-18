from typing import Callable, Dict, List, Optional, Set, Union

from eventlet import Timeout, greenthread
from bidict import bidict
from flask import current_app, copy_current_request_context, request
from flask_socketio import emit

try:
    from .game import Game, base_hand, PresidentsError
    from .emitting_chamber import EmittingChamber
    from .chamber import CardNotInChamberError
    from .hand import Hand, DuplicateCardError, FullHandError
    from .listener import socketio
except ImportError:
    from game import Game, base_hand, PresidentsError
    from emitting_chamber import EmittingChamber
    from chamber import CardNotInChamberError
    from hand import Hand, DuplicateCardError, FullHandError
    from listener import socketio


# TODO: decide what to do for the removal of asking options
# TODO: add reserve time


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
        self._chambers[rand_open_spot].set_sid(sid)
        self._spot_sid_bidict.inv[sid] = rand_open_spot
        self._set_name(rand_open_spot, name)
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
            self._emit_to_all_players('set_on_turn', {'on_turn': False, 'spot': self._current_player, 'time': 0})
        except KeyError:  # self._current_player is None (round start)
            pass
        super()._next_player(timer=False)
        self._emit_set_on_turn_handler()

    def _emit_set_on_turn_handler(self):
        """
        handles callback timer for player whose turn it is and updates
        other players' views of that timer as well

        TODO: clean
        """
        time: int = 30
        self._set_dot_color(self._current_player, 'green')
        self._emit('set_on_turn', {'on_turn': True, 'spot': self._current_player, 'time': time * 1000}, self._current_player_sid, callback=lambda: self._start_timer(self._current_player, time))
        self._emit_to_all_players('set_time', {'spot': self._current_player, 'time': time * 1000}, skip_sid=self._current_player_sid)

    def _player_finish(self, spot: int) -> None:
        self._set_dot_color(spot, 'purple')
        super()._player_finish(spot)

    # card management related methods

    def add_or_remove_card(self, sid: str, card: int) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().add_or_remove_card(spot, card)
        except PresidentsError as e:
            self._emit_alert(str(e), sid)

    # TODO
    def store_hand(self, spot: int) -> None:
        # super().store_hand(spot)
        # self._emit(...)
        ...

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

    def _play_current_hand(self, spot):
        super()._play_current_hand(spot, handle_post=False)
        self._set_dot_color(spot, 'blue')
        for other_spot in range(4):
            if other_spot == spot or other_spot in self._positions:
                continue
            self._set_dot_color(other_spot, 'red')
        self._emit_to_all_players('set_cards_remaining', {'spot': spot, 'cards_remaining': self._chambers[spot].num_cards})
        self._post_play_handler(spot)

    def maybe_unlock_pass_turn(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().maybe_unlock_pass_turn(spot)
        except PresidentsError as e:
            self._emit_alert(str(e), sid)

    def _unlock_pass(self, spot: int) -> None:
        super()._unlock_pass(spot)
        self._emit('set_pass_unlocked', {'pass_unlocked': True}, self._get_sid(spot))

    def _lock_pass(self, spot: int) -> None:
        super()._lock_pass(spot)
        self._emit('set_pass_unlocked', {'pass_unlocked': False}, self._get_sid(spot))

    def maybe_pass_turn(self, sid: str) -> None:
        spot: int = self._get_spot(sid)
        try:
            super().maybe_pass_turn(spot)
        except PresidentsError as e:
            self._emit_alert(str(e), sid)

    def _pass_turn(self, spot):
        super()._pass_turn(spot, handle_post=False)
        self._set_dot_color(spot, 'yellow')
        self._post_pass_handler()

    def _clear_hand_in_play(self) -> None:
        super()._clear_hand_in_play()
        self._emit_to_all_players('clear_hand_in_play', {})

    # trading related methods

    def _initiate_trading(self) -> None:
        super()._initiate_trading()
        for spot in range(4):
            self._set_dot_color(spot, 'red')
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
        self._emit('set_giving_options', {'options': list(giving_options), 'highlight': True}, self._get_sid(spot))

    def _clear_giving_options(self, spot: int) -> None:
        self._emit('set_giving_options', {'options': list(self._giving_options[spot]), 'highlight': False}, self._get_sid(spot))
        super()._clear_giving_options(spot)

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

    def _message(self, message: str) -> None:
        super()._message(message)
        self._emit_to_room('message', {'message': message})

    # getters

    def _get_sid(self, spot: int) -> str:
        return self._spot_sid_bidict[spot]

    def _get_spot(self, sid: str) -> int:
        return self._spot_sid_bidict.inv[sid]

    # setters

    def _set_name(self, spot: int, name: str) -> None:
        self._names[spot] = name
        self._emit_to_all_players('set_names', {'names': self._names})

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
        # self._emit('remove_asking_option', {'value': value}, self._get_sid(spot))

    def _set_dot_color(self, spot: int, dot_color: str) -> None:
        self._emit_to_all_players('set_dot_color', {'spot': spot, 'dot_color': dot_color})


    # emitters

    def _emit(self, event: str, payload: Dict[str, Union[int, str, List[int]]], sid: str, *, callback: Optional[Callable]=None) -> None:
        socketio.emit(event, payload, room=sid, callback=callback)

    def _emit_to_all_players(self, event: str, payload: Dict[str, Union[int, str, List[int]]], *, skip_sid: Optional[str]=None):
        for sid in self._spot_sid_bidict.values():
            if sid == skip_sid:
                continue
            self._emit(event, payload, sid)

    def _emit_to_room(self, event: str, payload: Dict[str, Union[int, str, List[int]]]):
        self._emit(event, payload, self._room)

    # alerting related methods

    def _emit_alert(self, alert, sid: str) -> None:
        self._emit('alert', {'alert': alert}, sid)
