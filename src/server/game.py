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

    def __init__(self) -> None:
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
        self._room: str = ''
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
        self.spot_sid_bidict = bidict()  # spot to sid
        self._unlocked: List[bool] = [False for _ in range(4)]
        self._names: List[str] = [None for _ in range(4)]
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
        sids = list(self.spot_sid_bidict.values())
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
            spot = self._current_player
            chamber = self._get_chamber(spot)
            for card in chamber:
                if card not in chamber.current_hand:
                    self.add_or_remove_card(spot, card)
                self.maybe_unlock_play(spot)
                if self._get_unlocked(spot):
                    self.maybe_play_current_hand(spot)
                else:
                    self.maybe_pass_turn(spot)

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

    def add_player(self, sid: str, name: str) -> None:
        self.spot_sid_bidict.inv[sid] = self._rand_open_spot()
        # TODO self._set_name(sid, name)
        self.num_players += 1

    def remove_player(self, sid: str) -> None:
        # TODO self._set_name(sid, None)
        self._open_spots.add(self._get_spot(sid))
        self.spot_sid_bidict.inv.pop(sid)
        self.num_players -= 1

    def clear_players(self) -> None:
        self.spot_sid_bidict.clear()
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
        for spot, sid in self.spot_sid_bidict.items():
            chamber = self._get_chamber(sid)
            # chamber.reset()
            chamber.set_sid(sid)
            chamber.add_cards(decks[spot])
            self._update_spot(spot, sid)

    def _deal_cards(self) -> None:
        deck = np.arange(1, 53, dtype=np.int32)  # deck of cards 1-52
        np.random.shuffle(deck)  # shuffles deck inplace
        decks = deck.reshape(4, 13)  # splits deck into 4 decks of 13
        decks.sort(axis=1)  # sorts individual decks
        c3_index = np.where(decks == 1)[0][0]  # get which deck has the 3 of clubs
        self._turn_manager = TurnManager(c3_index)
        # self._next_player()
        for spot, sid in self.spot_sid_bidict.items():
            chamber = self._get_chamber(sid)
            chamber.reset()
            chamber.set_sid(sid)
            chamber.add_cards(decks[spot])
            self._update_spot(spot, sid)

    def _update_spot(self, spot: int, sid: str) -> None:
        self._emit('update_spot', {'spot': spot}, sid)

    def maybe_unlock_play(self, spot: int):
        """
        can only unlock valid hands
        """
        # TODO: disable playing current hand when trading
        # TODO: disable playing current hand when not your turn
        hand = self._get_current_hand(spot)
        if hand.is_empty:
            self._alert_add_cards_before_unlocking(spot)
            return
        if not hand.is_valid:
            self._alert_cannot_play_invalid_hand(spot)
            return
        hip = self._hand_in_play
        if hip is BaseHand:  # start of the game
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

    def _is_current_player(self, spot: int) -> bool:
        return spot == self._current_player

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

    def _player_finish(self, spot: int) -> None:
        # TODO: self._message_player_finished_position(sid)
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

    def _set_president(self, spot: int) -> None:
        self._set_asker(spot, 2)

    def _set_vice_president(self, spot: int) -> None:
        self._set_asker(spot, 1)

    def _set_vice_asshole(self, spot: int) -> None:
        self._set_giver(spot, 1)

    def _set_asshole(self, spot: int) -> None:
        self._set_giver(spot, 2)

    def _set_asker(self, spot: int, takes_and_gives: int) -> None:
        self._set_takes_remaining(spot, takes_and_gives)
        self._set_gives_remaining(spot, takes_and_gives)
        self._emit('set_asker', {}, self._get_sid(spot))

    def _set_giver(self, spot: int, gives) -> None:
        self._set_gives_remaining(spot, gives)
        self._emit('set_giver', {}, self._get_sid(spot))

    def _set_takes_remaining(self, spot: int, takes: int) -> None:
        self._takes_remaining[spot] = takes

    def _set_gives_remaining(self, spot: int, gives: int) -> None:
        self._gives_remaining[spot] = gives

    def _next_player(self, hand_won=False):
        if self._current_player is not None:  # TODO: better way to check this
            self._flip_turn(self._current_player)
        self._current_player = next(self._turn_manager)
        # TODO: if hand_won:
            # TODO: self._message_hand_won()
        self._flip_turn(self._current_player)
        # TODO: self._message_announce_turn()
        # if game_end:
        #     return

    def _flip_turn(self, spot: int) -> None:
        self._emit('flip_turn', {}, self._get_sid(spot))

    def _update_hand_in_play(self, hand: Hand) -> None:
        self._emit('update_hand_in_play', {
            'hand_in_play': hand.to_list(),
            'hand_in_play_desc': hand.id_desc}, self._room)
        self._hand_in_play = hand

    def _unlock(self, spot: int) -> None:
        self._emit('unlock', {}, self._get_sid(spot))
        self._set_unlocked(spot, True)

    def lock(self, spot: int) -> None:
        self._emit('lock', {}, self._get_sid(spot))
        self._set_unlocked(spot, False)

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

    def maybe_pass_turn(self, spot: int) -> None:
        if not self._is_current_player(spot):
            self._alert_can_only_pass_on_turn(spot)
            return
        hip = self._hand_in_play
        if hip is BaseHand:
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

    def ask_for_card(self, spot: int) -> None:
        if not self.trading:
            self._alert_dont_use_console(spot)
            return
        if not self._is_asker(spot):
            self._alert_dont_use_console(spot)
        # TODO: remove trading options when takes run out
        value = self._get_selected_asking_option(spot)
        asked = self._get_opposing_position(spot)
        # chamber for asked
        chamber = self._get_chamber(asked)
        giving_options = set()
        # TODO: set comprehension this maybe?
        for card in range((value - 1) * 4 + 1, value * 4 + 1):
            if card in chamber and card not in self._get_given(spot):
                giving_options.add(card)
        if not giving_options:
            self._add_to_already_asked(spot, value)
            self._remove_asking_option(spot, value)
        else:
            self._set_giving_options(asked, giving_options)
            self._wait_for_reply(spot)

    def _remove_asking_option(self, spot: int, value: int) -> None:
        self._emit('removing_asking_option', {'value': value}, self._get_sid(spot))

    def _add_to_already_asked(self, spot: int, value: int) -> None:
        self._get_already_asked(spot).add(value)

    def _get_already_asked(self, spot: int) -> Set[int]:
        return self._already_asked[spot]

    def _is_already_asked(self, spot: int, value: int) -> bool:
        return value in self._get_already_asked(spot)

    def _wait_for_reply(self, spot: int) -> None:
        self._deselect_selected_asking_option(spot)
        self.lock(spot)
        self._set_waiting(spot, True)

    def _set_waiting(self, spot: int, waiting: bool) -> None:
        self._waiting[spot] = waiting

    def _is_waiting(self, spot: int) -> bool:
        return self._waiting[spot]

    def _highlight_giving_options(self, spot: int, giving_options: Set[int]) -> None:
        self._emit('highlight_giving_options', {'options': list(giving_options)}, self._get_sid(spot))

    def _set_giving_options(self, spot: int, giving_options: Set[int]) -> None:
        self._highlight_giving_options(spot, giving_options)
        self._giving_options[spot] = giving_options

    def _get_giving_options(self, spot: int) -> Set[int]:
        return self._giving_options[spot]

    def _no_dont_have_such_card(self):
        ...

    def _get_position(self, spot: int) -> int:
        return self._positions.index(spot)

    def _get_opposing_position(self, spot: int) -> int:
        return 3 - self._get_position(spot)

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
        self._get_chamber(spot).deselect_selected()
        self._emit('select_asking_option', {'value': value}, self._get_sid(spot))

    def _deselect_asking_option(self, spot: int, value: int) -> None:
        self._set_selected_asking_option(spot, 0)
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
        hand = self._get_current_hand(spot)
        # TODO: add ability to give invalid 2 card hand
        if not hand.is_single:
            self._alert_can_only_give_singles(spot)
        if self._is_giver(spot):
            if hand[4] in self._get_giving_options(spot):
                self._unlock(spot)
            else:
                self._alert_can_only_give_a_giving_option(spot)
        elif self._is_asker(spot):
            pass

    def _give_card(self, spot: int) -> None:
        """
        how to handle gives?

        asker cannot give a card that was just given to them
        should givees be able to see the card immediately after they are given?
            should the given card be with the normal cards and selectable?
            maybe just allow free use of the card but check that it isn't being
                given after being taken or being taken after being given
        """
        card = self._get_current_hand(spot)[4]
        if card in self._get_taken(spot):
            pass
        giver_chamber: EmittingChamber = self._get_chamber(spot)
        taker_chamber: EmittingChamber = self._get_chamber(self._get_opposing_position(spot))
        
        giver_chamber

    def _get_taken(self, spot: int) -> Set[int]:
        return self._taken[spot]

    def _get_decks_from_chambers(self):
        deck = list()
        for chamber in self._chambers:
            deck.extend(chamber)
        deck = np.array(deck)
        return deck.reshape(4, 13)

    def _get_sid(self, spot: int) -> str:
        """
        input spot; output: sid
        """
        return self.spot_sid_bidict[spot]

    def _get_spot(self, sid: str) -> int:
        """
        input: sid; output: spot
        """
        return self.spot_sid_bidict.inv[sid]

    def _get_president_and_vice_president(self) -> List[int]:
        return self._positions[0:2]

    def _is_asker(self, spot: int) -> bool:
        return spot in self._get_president_and_vice_president()

    def _get_asshole_and_vice_asshole(self) -> List[int]:
        return self._positions[2:4]

    def _is_giver(self, spot: int) -> bool:
        return spot in self._get_asshole_and_vice_asshole()

    def _get_chamber(self, spot: int) -> EmittingChamber:
        return self._chambers[spot]

    def _get_current_hand(self, spot: int) -> Hand:
        return self._get_chamber(spot).current_hand

    def _get_unlocked(self, spot: int) -> bool:
        return self._unlocked[spot]

    def _set_unlocked(self, spot: int, unlocked: bool) -> None:
        self._unlocked[spot] = unlocked

    def _set_name(self, spot: int, name: str) -> None:
        self._names[spot] = name

    def _get_name(self, spot: int) -> str:
        return self._names[spot]

    def _get_current_player_name(self) -> str:
        return self._names[self._current_player]

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
