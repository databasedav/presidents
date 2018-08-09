from __future__ import annotations
import numpy as np
from llist import sllist, sllistnode, dllist, dllistnode
from typing import List, Union, Generator
from hand import Hand
from flask_socketio import emit
import xxhash


# TODO: use del for hand?
# TODO: add is not None checks for cards existing
# TODO: utilize weakrefs from the hand nodes to their parents instead of
#       storing the card number in a card node allowing to get rid of 
#       card nodes
# TODO: check for memory leaks?
# TODO: should not have socketio event in the class itself; maybe make a
#       a class that interprets changes in the chamber and emits approp.
#       or just keep it this way; if I keep the emits in the class
#       how do I write test that ignore the emits
# TODO: too many int calls


class CardNotInChamberError(RuntimeError):
    pass


class Chamber:
    """
    Storage for cards and hands specifically designed for fast runtimes
    in context of front end interaction. Emits events containing hashes
    that can identify and modify vue components quickly.

    (note the hash functionality described will only be added once vue
    starts supporting maps officially)
    """
    def __init__(self, cards: np.ndarray = None) -> None:
        self._num_cards = 0
        self._cards = np.empty(shape=53, dtype=np.object)
        if cards:
            for card in cards:
                self._cards[card] = HandPointerDLList()
                self._num_cards += 1
        self._hands: dllist = dllist()  # a dllist of HandNodes

    def reset(self):
        self._num_cards = 0
        self._cards = np.empty(shape=53, dtype=np.object)
        self._hands: dllist = dllist()

    def add_card(self, card: int) -> None:
        self._cards[card] = HandPointerDLList()
        self._num_cards += 1
        emit('add_card', {'id': xxhash.xxh64().intdigest(), 'value': card, 'is_selected': False})

    def add_cards(self, cards: np.ndarray) -> None:
        for card in cards:
            self.add_card(int(card))

    def remove_card(self, card: int) -> None:
        for base_hand_pointer_node in self._cards[card].iter_nodes():
            hand_node = base_hand_pointer_node.value
            for hand_pointer_node in hand_node.value:
                if hand_pointer_node is base_hand_pointer_node:
                    continue
                else:
                    hand_pointer_node.owner().remove(hand_pointer_node)
            hand_node.owner().remove(hand_node)
        self._cards[card] = None
        self._num_cards -= 1

    def add_hand(self, hand: Hand) -> None:
        hand_pointer_nodes: List[HandPointerNode] = list()
        cards: List[int] = list() # TODO: replace with uuid once vue adds map support
        for card in hand:
            self.deselect_card(int(card))
        hand_node: HandNode = HandNode(hand_pointer_nodes, cards)
        for card in hand:
            hand_pointer_node: HandPointerNode = HandPointerNode(hand_node)
            hand_pointer_nodes.append(hand_pointer_node)
            cards.append(int(card))
            self._cards[card].appendnode(hand_pointer_node)
        self._hands.appendnode(hand_node)
        emit('store_hand', {'cards': [{'id': id, 'value': int(value)} for id, value in zip([xxhash.xxh64().intdigest() for _ in range(len(hand))], hand)]})
        # emit('deselect_all_hands')

    def select_card(self, card: int):
        if self._cards[card] is None:
            raise CardNotInChamberError('The desired card is not in the chamber; possible DOM modification.')
        for hand_node in self._cards[card]:
            hand_node.increment_num_selected_cards()
        emit('select_card', {'card': card})

    def deselect_card(self, card: int):
        if self._cards[card] is None:
            raise CardNotInChamberError('The desired card is not in the chamber; possible DOM modification.')
        for hand_node in self._cards[card]:
            hand_node.decrement_num_selected_cards()
        emit('deselect_card', {'card': card})

    def clear_hands(self) -> None:
        for hand_node in self._hands:
            hand_node.remove_hand()
        self._hands.clear()
        self._reset_card_dllists()

    def _reset_card_dllists(self) -> None:  # TODO: can be done better
        for card, dll in enumerate(self._cards):
            if dll is not None:
                self[card].clear()

    def contains_card(self, card: int) -> bool:
        return self._cards[card] is not None

    def contains_hand(self, hand: Hand) -> bool:
        for hand_node in self._hands:
            if hand_node.hand == hand:
                return True
        return False

    def iter_cards(self) -> Generator[int, None, None]:
        for card in range(1, 53):
            if self.contains_card(card):
                yield card

class HandPointerDLList(dllist):
    """
    Wrapper for dllist with an iter_nodes method.
    """
    def iter_nodes(self):
        assert self.first, "Bug: attempting to iterate through empty HandPointerDLList."
        curr_node = self.first
        while curr_node is not None:
            yield curr_node
            curr_node = curr_node.next
        return StopIteration


class HandPointerNode(dllistnode):
    """
    Wrapper for dllistnode that allows the value of the node to be a
    pointer to another node.
    """
    def __init__(self, hand_node: HandNode):
        super().__init__(None)
        self.value = hand_node
    
    def __repr__(self):
        return 'HandPointerNode'


class HandNode(dllistnode):
    """
    .value is the list of HandPointerNodes corresponding to the cards in the hand
    will be uuid after vue supports maps
    """
    def __init__(self, hand_pointer_nodes: List[HandPointerNode], cards: List[int]):
        super().__init__(hand_pointer_nodes)
        self._num_cards_selected = 0
        self._cards = cards

    def __repr__(self):
        return 'HandNode'

    def increment_num_selected_cards(self) -> None:
        self._num_cards_selected += 1
        if self._num_cards_selected == 1:
            emit('select_hand', {'cards': self._cards})

    def decrement_num_selected_cards(self) -> None:
        self._num_cards_selected -= 1
        if self._num_cards_selected == 0:
            emit('deselect_hand', {'cards': self._cards})
