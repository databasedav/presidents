from hand import Hand, DuplicateCardError, FullHandError
from typing import List, Dict, Any
from chamber import Chamber
from flask_socketio import emit
import numpy as np
from bidict import bidict
import random

# TODO: adding and removal of players, including management of spot assignment

class Start:
    """hand at begininning of game; 3 of clubs must be played on it"""
    pass
Start = Start()

class Game:

    def __init__(self):
        """
        main event handler should have dict from each room
        to the game object in that room; the game object
        will be fed actions from the event handler with the
        sid of the player who made that action, and the game
        object has a dict from the sid to the spot number
        which is used for everything else

        has full control of the game
        """
        self._hand_in_play: Hand = Hand()
        self._turn_manager = None
        self._current_hands: List[Hand] = [Hand(), Hand(), Hand(), Hand()]
        self._chambers = [Chamber(), Chamber(), Chamber(), Chamber()]
        self._current_player = None
        self._num_consecutive_passes = 0
        self._positions = list()
        self._takes_remaining = [0, 0, 0, 0]
        self._gives_remaining = [0, 0, 0, 0]
        self._num_consecutive_games = 0
        self._winning_last_played = False
        self._room = None
        self._sid_spot_dict = bidict()  # sid to spot
        self._unlocked =  [False, False, False, False]
        self._names = [None, None, None, None]
        self._open_spots = {0, 1, 2, 3}
        self.num_players = 0
        self.num_spectators = 0
    
    # TODO: only for testing not in final game
    def restart(self, sid: str) -> None:
        self.clear_players()
        self.add_player(sid, 'fuck')
        chamber = self._get_chamber(sid)
        chamber.reset()
        self._start_round()

    
    # TODO: make Any type more specific
    def _emit(self, event: str, payload: Dict[str, Any], sid: str):
        emit(event, payload, room=sid)


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
        self.num_players -=1
    
    def clear_players(self) -> None:
        self._sid_spot_dict.clear()
        self._names = [None, None, None, None]
        self.num_players = 0
        self._open_spots = {0, 1, 2, 3}

    def _start_round(self):
        deck = np.arange(1, 53, dtype=np.int32)  # deck of cards 1-52
        np.random.shuffle(deck)  # shuffles deck inplace
        decks = deck.reshape(4, 13)  # splits deck into 4 decks of 13
        decks.sort(axis=1)  # sorts individual decks
        c3_index = np.where(decks == 1)[0][0]  # get which deck has the 3 of clubs
        self._turn_manager = TurnManager(c3_index)
        self._next_player()
        for (sid, spot), deck in zip(self._sid_spot_dict.items(), decks):
            chamber = self._get_chamber(sid)
            chamber.set_sid = sid
            chamber.add_cards(deck)

    def maybe_unlock_play(self, sid):
        """
        can only unlock valid hands
        """
        # TODO: disable playing current hand when trading
        # TODO: disable playing current hand when not your turn
        hand = self._get_current_hand(sid)
        if not hand.is_valid:
            self._alert_cannot_play_invalid_hand(sid)
            return
        hip = self._hand_in_play
        if hip is Start:
            if 1 not in hand:
                self._alert_3_of_clubs(sid)
                return
            else:
                self._unlock_play(sid)
        elif hip is None:  # curr player won last hand
            self._unlock_play(sid)
        else:
            try:
                if hand > hip:
                    self._unlock_play(sid)
                else:
                    self._alert_weaker_hand(sid)
            except RuntimeError as e:
                emit('alert', {'alert': str(e)}, room=sid)
    
    # TODO: this one requires tying together card removal and deselection in the chamber
    #       i.e. removing cards should also deselect them
    def play_current_hand(self, sid):
        if not self._get_unlocked(sid):
            # store was modified to allow play emittal without unlocking
            self._alert_dont_modify_dom(sid)
            self._lock_play(sid)
            return
        else:
            hand = self._get_current_hand(sid)
            chamber = self._get_chamber(sid)
            hand.reset()
            chamber.remove_cards(hand)
            self._update_hand_in_play(hand)
            self._message_hand_played(hand)
            if chamber.is_empty:
                self._player_finish(sid)
            else:
                self._winning_last_played = False
            if self._num_unfinished_players == 1:
                self._next_player(room, game_end=True)


    def _player_finish(self, sid: str):
        # shouldn't include the setting of takes and gives remaining
        # just do that at the end; just set position, winning last,
        # remove from turn manager, and message
        self._positions.append(self._current_player)
        self._winning_last_played = True
        self._turn_manager.remove(self._current_player)
        self._message_player_finished_position(sid)

    def _next_player(self, hand_won=False, game_end=False):
        self._current_player = next(self._turn_manager)
        if game_end:
            return

    def _update_hand_in_play(self, hand: Hand):
        emit('update_hand_in_play', {'hand': hand.to_list()}, room=self._room)
        self._hand_in_play = hand
    
    def _unlock_play(self, sid: str):
        emit('unlock_play', room=sid)
        self._set_unlocked(sid, True)
    
    def _lock_play(self, sid: str):
        emit('lock_play', room=sid)
        self._set_unlocked(sid, False)

    # client can attempt to add any card (via the console) so should first
    # check that the card is actually in the chamber and then notify the
    # client that they should not modify the dom and then reset the card values
    def add_or_remove_card(self, sid: str, card: int) -> None:
        chamber = self._get_chamber(sid)
        if not chamber.contains_card(card):
            self._alert_dont_modify_dom(sid)
            # self._reset_card values
        hand = self._get_current_hand(sid)
        # TODO: verify to add or remove to be first empirically
        try:
            hand.add(card)
            chamber.select_card(card)
        except DuplicateCardError:
            hand.remove(card)
            chamber.deselect_card(card)
        except FullHandError:
            self._alert_hand_full(sid)
        except Exception as e:
            print("Bug: probably the card hand chamber freaking out.")
            raise e

    def _get_spot(self, sid: str) -> int:
        """
        input: sid, output: spot
        """
        return self._sid_spot_dict[sid]
    
    def _get_sid(self, spot: int) -> str:
        """
        input spot, output: sid
        """
        return self._sid_spot_dict.inv[spot]

    def _get_chamber(self, sid: str):
        return self._chambers[self._get_spot(sid)] 
    
    def _get_current_hand(self, sid: str):
        return self._current_hands[self._get_spot(sid)]

    def _get_unlocked(self, sid: str):
        return self._unlocked[self._get_spot(sid)]

    def _set_unlocked(self, sid: str, unlocked: bool):
        self._unlocked[self._get_spot(sid)] = unlocked
    
    def _set_name(self, sid: str, name: str):
        self._names[self._get_spot(sid)] = name
    
    def _get_name(self, sid: str):
        return self._names[self._get_spot(sid)]

    def set_room(self, room: str):
        self._room = room

    def _next_player(self):
        return next(self._turn_manager)

    def _alert_cannot_play_invalid_hand(self, sid: str) -> None:
        # emit("alert")
        ...
    
    def _alert_3_of_clubs(self, sid: str) -> None:
        # emit("alert")
        ...
    
    def _alert_hand_full(self, sid: str) -> None:
        # emit("alert")
        ...
    
    def _alert_weaker_hand(self, sid: str) -> None:
        # emit("alert")
        ...
    
    def _alert_dont_modify_dom(self, sid: str) -> None:
        # emit("alert")
        ...

    def _message_hand_played(self, hand: Hand):
        # emit("message")
        ...
    
    def _message_current_player_finished_position(self, sid: str):
        name = self._get_name(sid)
        # emit("message")
        ...


class TurnManager:

    def __init__(self, first: int) -> None:
        self._spots = list(range(4))
        self._curr = first
        self._num_unfinished_players = 4
    
    def __next__(self):
        if len(self._spots) == 1:
            return -1
        if self._curr >= len(self._spots):
            self._curr = 0
        index = self._curr
        self._curr += 1
        return self._spots[index]

    def remove(self, spot: int) -> None:
        self._spots.remove(spot)
        self._num_unfinished_players -= 1

