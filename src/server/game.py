from hand import Hand, DuplicateCardError, FullHandError
from typing import List, Dict, Set, Any
from chamber import CardNotInChamberError
from emitting_chamber import EmittingChamber
from flask_socketio import emit
import numpy as np
from bidict import bidict
import random
from itertools import cycle

# TODO: change all sid's to spot's because the game should operate on
#       and not have to pass around the sid everywhere. this includes
#       changing the sid_spot_dict to a spot_sid_dict.


class Game:

    def __init__(self, room: str=None) -> None:
        """
        main event handler should have dict from each room
        to the game object in that room; the game object
        will be fed actions from the event handler with the
        sid of the player who made that action, and the game
        object has a dict from the sid to the spot number
        which is used for everything else

        has full control of the game
        """
        # TODO: organize attributes
        self._room: str = room
        self._hand_in_play: [BaseHand, Hand] = BaseHand
        self._turn_manager: [None, TurnManager] = None
        self._current_hands: List[Hand] = [Hand() for _ in range(4)]
        self._chambers: List[EmittingChamber] = [EmittingChamber() for _ in range(4)]
        self._current_player: [None, int] = None
        self._num_consecutive_passes: int = 0
        self._positions: List[int] = list()
        self._takes_remaining: List[int] = [0 for _ in range(4)]
        self._gives_remaining: List[int] = [0 for _ in range(4)]
        self._num_consecutive_games: int = 0
        self._winning_last_played: bool = False
        self._sid_spot_dict = bidict()  # sid to spot
        self._unlocked: List[bool] = [False for _ in range(4)]
        self._names = [None for _ in range(4)]
        self._open_spots = {i for i in range(4)}
        self.num_players: int = 0
        self.num_spectators: int = 0  # TODO
        self.trading: bool = False
        self._selected_asking_option: List[int] = [0 for _ in range(4)]
        self._already_asked: List[Set[int]] = [set() for _ in range(4)]
        self._waiting: List[bool] = [False for _ in range(4)]
        self._giving_options: List[Set] = [set() for _ in range(4)]
        self._given: List[Set[int]] = [set() for _ in range(2)]  # only for askers
        self._taken: List[Set[int]] = [set() for _ in range(2)]  # only for askers

    @property
    def _current_player_sid(self) -> str:
        return self._get_sid(self._current_player)

    def set_room(self, room: str) -> None:
        self._room = room

    # TODO: only for testing not in final game
    def restart(self) -> None:
        sids = list(self._sid_spot_dict.keys())
        self.clear_players()
        for i, sid in enumerate(sids):
            self.add_player(sid, f'fuck{i}')
            chamber = self._get_chamber(sid)
            chamber.reset()
        self._all_off_turn()
        self._start_round()

    def get_game_to_trading(self) -> None:
        """
        For use when testing to quickly get to trading state from 4 card
        state, i.e. each player has one of the 3's.
        """
        while not self.trading:
            sid = self._current_player_sid
            chamber = self._get_chamber(sid)
            for card in chamber:
                if card not in chamber.current_hand:
                    self.add_or_remove_card(sid, card)
                self.maybe_unlock_play(sid)
                if self._get_unlocked(sid):
                    self.maybe_play_current_hand(sid)
                else:
                    self.maybe_pass_turn(sid)

    def _all_off_turn(self):
        self._emit('all_off_turn', {}, self._room)

    # TODO: make Any type more specific
    def _emit(self, event: str, payload: Dict[str, Any], room: str):
        emit(event, payload, room=room)

    def start_game(self):
        if self.num_players == 1:
            self._start_round()

    @property
    def _num_unfinished_players(self):
        return self._turn_manager._num_unfinished_players

    def _rand_open_spot(self):
        """
        removes random open spot; should not happen when there are no open spots
        """
        assert self._open_spots
        spot = random.sample(self._open_spots, 1)[0]
        self._open_spots.remove(spot)
        return spot

    def add_player(self, sid, name):
        self._sid_spot_dict[sid] = self._rand_open_spot()
        self._set_name(sid, name)
        self.num_players += 1

    def remove_player(self, sid):
        self._set_name(sid, None)
        self._open_spots.add(self._get_spot(sid))
        self._sid_spot_dict.pop(sid)
        self.num_players -= 1

    def clear_players(self) -> None:
        self._sid_spot_dict.clear()
        self._names = [None for _ in range(4)]
        self.num_players = 0
        self._open_spots = {0, 1, 2, 3}
        self._current_player = None

    def _start_round(self) -> None:
        deck = np.arange(1, 5, dtype=np.int32)  # deck of cards 1-52
        np.random.shuffle(deck)  # shuffles deck inplace
        decks = deck.reshape(4, 1)  # splits deck into 4 decks of 13
        decks.sort(axis=1)  # sorts individual decks
        c3_index = np.where(decks == 1)[0][0]  # get which deck has the 3 of clubs
        self._turn_manager = TurnManager(c3_index)
        self._next_player()
        for sid, spot in self._sid_spot_dict.items():
            chamber = self._get_chamber(sid)
            # chamber.reset()
            chamber.set_sid(sid)
            chamber.add_cards(decks[spot])
            self._update_spot(sid, spot)

    def _deal_cards(self) -> None:
        deck = np.arange(1, 53, dtype=np.int32)  # deck of cards 1-52
        np.random.shuffle(deck)  # shuffles deck inplace
        decks = deck.reshape(4, 13)  # splits deck into 4 decks of 13
        decks.sort(axis=1)  # sorts individual decks
        c3_index = np.where(decks == 1)[0][0]  # get which deck has the 3 of clubs
        self._turn_manager = TurnManager(c3_index)
        # self._next_player()
        for sid, spot in self._sid_spot_dict.items():
            chamber = self._get_chamber(sid)
            chamber.reset()
            chamber.set_sid(sid)
            chamber.add_cards(decks[spot])
            self._update_spot(sid, spot)

    def _update_spot(self, sid: str, spot: int) -> None:
        self._emit('update_spot', {'spot': spot}, sid)

    def maybe_unlock_play(self, sid):
        """
        can only unlock valid hands
        """
        # TODO: disable playing current hand when trading
        # TODO: disable playing current hand when not your turn
        hand = self._get_current_hand(sid)
        if hand.is_empty:
            self._alert_add_cards_before_unlocking(sid)
            return
        if not hand.is_valid:
            self._alert_cannot_play_invalid_hand(sid)
            return
        hip = self._hand_in_play
        if hip is BaseHand:  # start of the game
            if self._is_current_player(sid):  # player with 3 of clubs
                if 1 not in hand:  # card 1 is the 3 of clubs
                    self._alert_3_of_clubs(sid)
                    return
                else:
                    # any hand with the 3 of clubs is ok
                    self._unlock(sid)
            else:
                # other players (without the 3 of clubs) can unlock
                # whatever hand they want
                self._unlock(sid)
        elif hip is None:  # current player won last hand and can play any hand
            self._unlock(sid)
        else:
            if hand > hip:
                self._unlock(sid)
            else:
                self._alert_weaker_hand(sid)

    def _is_current_player(self, sid: str) -> bool:
        return sid is self._sid_spot_dict.inv[self._current_player]

    def maybe_play_current_hand(self, sid) -> None:
        if not self._is_current_player(sid):
            self._alert_can_only_play_on_turn(sid)
            return
        elif not self._get_unlocked(sid):
            # store was modified to allow play emittal without unlocking
            self._alert_dont_modify_dom(sid)
            self.lock(sid)
            return
        else:
            chamber = self._get_chamber(sid)
            hand = Hand.copy(chamber.current_hand)
            chamber.remove_cards(hand)
            self._num_consecutive_passes = 0
            self.lock(sid)
            self._update_hand_in_play(hand)
            # TODO: self._message_hand_played(hand)

            if chamber.is_empty:
                # player_finish takes care of going to the next player
                self._player_finish(sid)
            else:
                self._next_player()
                self._winning_last_played = False

    def _player_finish(self, sid: str) -> None:
        # TODO: self._message_player_finished_position(sid)
        self._positions.append(self._current_player)
        self._winning_last_played = True
        self._turn_manager.remove(self._current_player)
        num_unfinished_players = self._num_unfinished_players
        if num_unfinished_players == 3:
            self._set_president(sid)
            self._next_player()
        elif num_unfinished_players == 2:
            self._set_vice_president(sid)
            self._next_player()
        else:
            self._set_vice_asshole(sid)
            self._current_player = next(self._turn_manager)
            self._positions.append(self._current_player)
            self._set_asshole(self._current_player_sid)
            self._initiate_trading()

    def _set_president(self, sid: str) -> None:
        self._set_asker(sid, 2)

    def _set_vice_president(self, sid: str) -> None:
        self._set_asker(sid, 1)

    def _set_vice_asshole(self, sid: str) -> None:
        self._set_giver(sid, 1)

    def _set_asshole(self, sid: str) -> None:
        self._set_giver(sid, 2)

    def _set_asker(self, sid: str, takes_and_gives: int) -> None:
        self._set_takes_remaining(sid, takes_and_gives)
        self._set_gives_remaining(sid, takes_and_gives)
        self._emit('set_asker', {}, sid)

    def _set_giver(self, sid: str, gives) -> None:
        self._set_gives_remaining(sid, gives)
        self._emit('set_giver', {}, sid)

    def _set_takes_remaining(self, sid: str, takes: int) -> None:
        self._takes_remaining[self._get_spot(sid)] = takes

    def _set_gives_remaining(self, sid: str, gives: int) -> None:
        self._gives_remaining[self._get_spot(sid)] = gives

    def _next_player(self, hand_won=False):
        if self._current_player is not None:  # TODO: better way to check this
            self._flip_turn(self._current_player_sid)
        self._current_player = next(self._turn_manager)
        # TODO: if hand_won:
            # TODO: self._message_hand_won()
        self._flip_turn(self._current_player_sid)
        # TODO: self._message_announce_turn()
        # if game_end:
        #     return

    def _flip_turn(self, sid: str) -> None:
        self._emit('flip_turn', {}, sid)

    def _update_hand_in_play(self, hand: Hand) -> None:
        self._emit('update_hand_in_play', {
            'hand_in_play': hand.to_list(),
            'hand_in_play_desc': hand.id_desc}, self._room)
        self._hand_in_play = hand

    def _unlock(self, sid: str) -> None:
        self._emit('unlock', {}, sid)
        self._set_unlocked(sid, True)

    def lock(self, sid: str) -> None:
        self._emit('lock', {}, sid)
        self._set_unlocked(sid, False)

    def add_or_remove_card(self, sid: str, card: int) -> None:
        chamber = self._get_chamber(sid)
        # TODO: verify to add or remove to be first empirically; may
        #       potentially justify looking before leaping if
        #       distribution is symmetric
        try:
            chamber.select_card(card)
            if self.is_asking(sid):
                self._deselect_asking_option(sid, self._get_selected_asking_option(sid))
            self.lock(sid)
        except CardNotInChamberError:
            self._alert_dont_modify_dom(sid)
            # TODO self._reset_card_values()
        except DuplicateCardError:
            # such an error can only occur if check passes
            chamber.deselect_card(card, check=False)
            self.lock(sid)
        except FullHandError:
            self._alert_hand_full(sid)

    def maybe_pass_turn(self, sid: str) -> None:
        if not self._is_current_player(sid):
            self._alert_can_only_pass_on_turn(sid)
            return
        hip = self._hand_in_play
        if hip is BaseHand:
            self._alert_must_play_3_of_clubs(sid)
            return
        if hip is None:
            self._alert_can_play_any_hand(sid)
            return
        self._num_consecutive_passes += 1
        # TODO: self._message_passed(sid)
        # all remaining players passed on a winning hand
        if self._winning_last_played:
            if self._num_consecutive_passes == self._num_unfinished_players:
                self._hand_in_play = None
                self._clear_hand_in_play()
                self._next_player()
                return
            else:
                self._next_player()
        # all other players passed on a hand
        elif self._num_consecutive_passes == self._num_unfinished_players - 1:
            self._hand_in_play = None
            self._clear_hand_in_play()
            self._next_player(hand_won=True)
            return
        else:
            self._next_player()

    def _clear_hand_in_play(self) -> None:
        self._emit('clear_hand_in_play', {}, self._room)

    def _initiate_trading(self) -> None:
        self.trading = True
        self._clear_hand_in_play()
        self._all_off_turn()
        self._deal_cards()
        self._set_trading(True)

    def _set_trading(self, trading: bool) -> None:
        self._emit('set_trading', {'trading': trading}, self._room)

    def ask_for_card(self, sid: str) -> None:
        if not self.trading:
            self._alert_dont_use_console(sid)
            return
        if not self._is_asker(sid):
            self._alert_dont_use_console(sid)
        # TODO: remove trading options when takes run out
        value = self._get_selected_asking_option(sid)
        asked_sid = self._get_opposing_position_sid(sid)
        # chamber for asked
        chamber = self._get_chamber(asked_sid)
        giving_options = set()
        # TODO: set comprehension this maybe?
        for card in range((value - 1) * 4 + 1, value * 4 + 1):
            if card in chamber and card not in self._get_given(sid):
                giving_options.add(card)
        if not giving_options:
            self._add_to_already_asked(sid, value)
            self._remove_asking_option(sid, value)
        else:
            self._set_giving_options(asked_sid, giving_options)
            self._wait_for_reply(sid)

    def _remove_asking_option(self, sid: str, value: int) -> None:
        self._emit('removing_asking_option', {'value': value}, sid)

    def _add_to_already_asked(self, sid: str, value: int) -> None:
        self._get_already_asked(sid).add(value)

    def _get_already_asked(self, sid: str) -> Set[int]:
        return self._already_asked[self._get_spot(sid)]

    def _is_already_asked(self, sid: str, value: int) -> bool:
        return value in self._get_already_asked(sid)

    def _wait_for_reply(self, sid: str) -> None:
        self._deselect_selected_asking_option(sid)
        self.lock(sid)
        self._set_waiting(sid, True)

    def _set_waiting(self, sid: str, waiting: bool) -> None:
        self._waiting[self._get_spot(sid)] = waiting

    def _is_waiting(self, sid: str) -> bool:
        return self._waiting[self._get_spot(sid)]

    def _highlight_giving_options(self, sid: str, giving_options: Set[int]) -> None:
        self._emit('highlight_giving_options', {'options': list(giving_options)}, sid)

    def _set_giving_options(self, sid: str, giving_options: Set[int]) -> None:
        self._highlight_giving_options(sid, giving_options)
        self._giving_options[self._get_spot(sid)] = giving_options

    def _get_giving_options(self, sid: str) -> Set[int]:
        return self._giving_options[self._get_spot(sid)]

    def _no_dont_have_such_card(self):
        ...

    def _get_position(self, sid: str) -> int:
        return self._positions.index(self._get_spot(sid))

    def _get_opposing_position(self, sid: str) -> int:
        return 3 - self._get_position(sid)

    def _get_position_sid(self, position: int) -> str:
        return self._get_sid(self._positions[position])

    def _get_opposing_position_sid(self, sid: str) -> str:
        return self._get_position_sid(self._get_opposing_position(sid))

    def update_selected_asking_option(self, sid: str, value: int) -> None:
        if not self._is_asker(sid):
            self._alert_dont_use_console(sid)
            return
        if not 0 <= value <= 13:
            self._alert_dont_use_console(sid)
            return
        if self._is_already_asked(sid, value):
            self._alert_dont_use_console(sid)
            return
        selected_asking_option: int = self._get_selected_asking_option(sid)
        if selected_asking_option == 0:
            self._select_asking_option(sid, value)
        elif selected_asking_option == value:
            self._deselect_asking_option(sid, value)
        else:
            self._deselect_asking_option(sid, selected_asking_option)
            self._select_asking_option(sid, value)

    def maybe_unlock_ask(self, sid: str) -> None:
        if not self.trading:
            self._alert_dont_use_console(sid)
            return
        if not self._is_asker(sid):
            self._alert_dont_use_console(sid)
            return
        if self._is_waiting(sid):
            self._alert_cannot_ask_while_waiting(sid)
            return
        selected_asking_option: int = self._get_selected_asking_option(sid)
        # selected_asking_option is 0 if no trading option is selected
        if not selected_asking_option:
            self._alert_dont_use_console(sid)
        else:
            self._unlock(sid)

    def is_asking(self, sid: str) -> bool:
        return self.trading and self._get_selected_asking_option(sid) > 0

    def is_giving(self, sid: str) -> bool:
        return self.trading and not self._get_current_hand(sid).is_empty

    def _select_asking_option(self, sid: str, value: int) -> None:
        self._set_selected_asking_option(sid, value)
        self._get_chamber(sid).deselect_selected()
        self._emit('select_asking_option', {'value': value}, sid)

    def _deselect_asking_option(self, sid: str, value: int) -> None:
        self._set_selected_asking_option(sid, 0)
        self._emit('deselect_asking_option', {'value': value}, sid)

    def _set_selected_asking_option(self, sid: str, value: int) -> None:
        self._selected_asking_option[self._get_spot(sid)] = value

    def _get_selected_asking_option(self, sid: str) -> int:
        return self._selected_asking_option[self._get_spot(sid)]

    def _deselect_selected_asking_option(self, sid: str) -> None:
        self._deselect_asking_option(sid, self._get_selected_asking_option(sid))

    def maybe_unlock_give(self, sid: str) -> None:
        if not self.trading:
            self._alert_dont_use_console(sid)
            return
        hand = self._get_current_hand(sid)
        # TODO: add ability to give invalid 2 card hand
        if not hand.is_single:
            self._alert_can_only_give_singles(sid)
        if self._is_giver(sid):
            if hand[4] in self._get_giving_options(sid):
                self._unlock(sid)
            else:
                self._alert_can_only_give_a_giving_option(sid)
        elif self._is_trader(sid):
            pass

    def _give_card(self, sid: str) -> None:
        """
        how to handle gives?

        asker cannot give a card that was just given to them
        should givees be able to see the card immediately after they are given?
            should the given card be with the normal cards and selectable?
            maybe just allow free use of the card but check that it isn't being
                given after being taken or being taken after being given
        """
        card = self._get_current_hand(sid)[4]
        if card in self._get_taken(sid):
            pass
        giver_chamber: EmittingChamber = self._get_chamber(sid)
        taker_chamber: EmittingChamber = self._get_chamber(self._get_opposing_position_sid(sid))
        
        giver_chamber

    def _get_taken(self, sid: str) -> Set[int]:
        return self._taken[self._get_spot(sid)]

    def _get_decks_from_chambers(self):
        deck = list()
        for chamber in self._chambers:
            deck.extend(chamber)
        deck = np.array(deck)
        return deck.reshape(4, 13)

    def _get_spot(self, sid: str) -> int:
        """
        input: sid; output: spot
        """
        return self._sid_spot_dict[sid]

    def _get_sid(self, spot: int) -> str:
        """
        input spot; output: sid
        """
        return self._sid_spot_dict.inv[spot]

    def _get_president_and_vice_sids(self) -> List[str]:
        return [self._get_sid(position) for position in self._positions[0:2]]

    def _is_asker(self, sid: str) -> bool:
        return sid in self._get_president_and_vice_sids()

    def _get_asshole_and_vice_sids(self) -> List[str]:
        return [self._get_sid(position) for position in self._positions[2:4]]

    def _is_giver(self, sid: str) -> bool:
        return sid in self._get_asshole_and_vice_sids()

    def _get_chamber(self, sid: str) -> EmittingChamber:
        return self._chambers[self._get_spot(sid)]

    def _get_current_hand(self, sid: str) -> Hand:
        return self._get_chamber(sid).current_hand

    def _get_unlocked(self, sid: str) -> bool:
        return self._unlocked[self._get_spot(sid)]

    def _set_unlocked(self, sid: str, unlocked: bool) -> None:
        self._unlocked[self._get_spot(sid)] = unlocked

    def _set_name(self, sid: str, name: str) -> None:
        self._names[self._get_spot(sid)] = name

    def _get_name(self, sid: str) -> str:
        return self._names[self._get_spot(sid)]

    def _get_current_player_name(self) -> str:
        return self._names[self._current_player]

    def _emit_alert(self, alert, sid: str) -> None:
        self._emit('alert', {'alert': alert}, sid)

    def _alert_cannot_play_invalid_hand(self, sid: str) -> None:
        self._emit_alert("you can't play invalid hands", sid)

    def _alert_3_of_clubs(self, sid: str) -> None:
        self._emit_alert('the first hand must contain the 3 of clubs', sid)

    def _alert_must_play_3_of_clubs(self, sid: str) -> None:
        self._emit_alert('you cannot pass when you have the 3 of clubs', sid)

    def _alert_hand_full(self, sid: str) -> None:
        self._emit_alert('your current hand is full', sid)

    def _alert_weaker_hand(self, sid: str) -> None:
        self._emit_alert('your current hand is weaker than the hand in play', sid)

    def _alert_dont_modify_dom(self, sid: str) -> None:
        self._emit_alert("please don't hax the dom", sid)

    def _alert_dont_use_console(self, sid: str) -> None:
        self._emit_alert("please don't hax with console", sid)

    def _alert_can_only_play_on_turn(self, sid: str) -> None:
        self._emit_alert("you can only play a hand on your turn", sid)

    def _alert_add_cards_before_unlocking(self, sid: str) -> None:
        self._emit_alert("you must add cards before attempting to unlock", sid)

    def _alert_can_only_pass_on_turn(self, sid: str) -> None:
        self._emit_alert("you can only pass on your turn", sid)

    def _alert_can_play_any_hand(self, sid: str) -> None:
        self._emit_alert("you can play any hand", sid)
        
    def _alert_can_only_give_singles(self, sid: str) -> None:
        self._emit_alert("you can only give singles", sid)

    def _alert_cannot_ask_while_waiting(self, sid: str) -> None:
        self._emit_alert("you cannot ask while waiting for a response", sid)
    
    def _alert_can_only_give_a_giving_option(self, sid: str) -> None:
        self._emit_alert("you can only give a highlighted option", sid)

    # def _message_hand_played(self, sid: str, hand: Hand):
    #     self._emit_alert("please don't hax", sid)

    # def _message_current_player_finished_position(self, sid: str):
    #     name = self._get_name(sid)
    #     # emit("message")
    #     ...


class BaseHand:
    """hand at begininning of game; 3 of clubs must be played on it"""
    pass
BaseHand = BaseHand()


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
