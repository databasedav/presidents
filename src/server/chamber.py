from __future__ import annotations
import numpy as np
from llist import sllist, sllistnode, dllist, dllistnode
from typing import List, Union, Generator, Dict, Any
from hand import Hand
from flask_socketio import emit
import xxhash
from utils.iternodes_dllist import IterNodesDLList


# TODO: use del for removing nodes?
# TODO: add is not None checks for cards existing
# TODO: utilize weakrefs from the hand nodes to their parents instead of
#       storing the card number in a card node allowing to get rid of 
#       card nodes
# TODO: check for memory leaks?
# TODO: make visual, interactive chamber
# TODO: make high quality representation of what is going on


class Chamber:
    """
    Storage for cards and hands specifically designed for fast runtimes
    in context of front end interaction. Base class for EmittingChamber.
    
    Uses doubly linked list because node removal is constant time.
    """
    def __init__(self, cards: np.ndarray=None) -> None:
        self._num_cards: int = 0
        self._cards: np.ndarray = np.empty(shape=53, dtype=np.object)
        if cards:
            for card in cards:
                self._cards[card] = HandPointerDLList()
                self._num_cards += 1
        self._hands: HandNodeDLList = HandNodeDLList()
    
    def __contains__(self, card) -> bool:
        return self._cards[card] is not None

    # TODO: should be simple but meaningful    
    def __repr__(self) -> str:
        ...

    @property
    def is_empty(self) -> bool:
        return self._num_cards == 0

    def reset(self) -> None:
        self._num_cards = 0
        self._cards = np.empty(shape=53, dtype=np.object)
        self._hands: dllist = dllist()

    def add_card(self, card: np.uint8) -> None:
        self._cards[card] = HandPointerDLList()
        self._num_cards += 1

    def add_cards(self, cards: np.ndarray) -> None:
        for card in cards:
            self.add_card(card)

    def remove_card(self, card: np.uint8) -> None:
        """
        Here is it important to note that we do not need to deselect the
        card before we remove it because all the hand nodes that contain
        the card will be removed.
        """
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
    
    def remove_cards(self, cards):
        for card in cards:
            self.remove_card(card)

    def add_hand(self, hand: Hand) -> None:
        for card in hand:
            self.deselect_card(card)
        hand_pointer_nodes: List[HandPointerNode] = list()
        cards: List[int] = list()
        hand_node: HandNode = HandNode(hand_pointer_nodes)
        for card in hand:
            hand_pointer_node: HandPointerNode = HandPointerNode(hand_node)
            hand_pointer_nodes.append(hand_pointer_node)
            cards.append(card)
            self._cards[card].appendnode(hand_pointer_node)
        self._hands.appendnode(hand_node)
    
    def select_card(self, card: int):
        assert card in self
        # self._cards[card] is a HandPointerDLList; iterating through
        # it, via the class' own __iter__ (which iterates through the
        # values, not the nodes) gives us each HandNode which contains
        # card passed to the function
        for hand_node in self._cards[card]:
            hand_node.increment_num_selected_cards()

    def deselect_card(self, card: int):
        assert card in self
        for hand_node in self._cards[card]:
            hand_node.decrement_num_selected_cards()

    def clear_hands(self) -> None:
        self._reset_card_dllists()
        self._hands.clear()

    def _reset_card_dllists(self) -> None:  # TODO: can be done better
        for maybe_dll in self._cards:
            if maybe_dll is not None:
                maybe_dll.clear()

    def iter_cards(self) -> Generator[int, None, None]:
        for card in range(1, 53):
            if card in self:
                yield card

class HandPointerDLList(IterNodesDLList):
    """
    Labelled wrapper for IterNodesDLList for readability.
    """
    def __repr__(self) -> str:
        return 'HandPointerDLList'
    

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

class HandNodeDLList(IterNodesDLList):
    """
    Labelled wrapper for IterNodesDLList for readability.
    """
    def __repr__(self) -> str:
        return 'HandNodeDLList'


class HandNode(dllistnode):
    """
    .value is the list of HandPointerNodes corresponding to the cards in
    the hand; increments/decrements the number of cards selected in each
    hand as they are selected in the chamber
    """
    def __init__(self, hand_pointer_nodes: List[HandPointerNode]):
        super().__init__(hand_pointer_nodes)
        self._num_cards_selected = 0
        
    def __repr__(self):
        return 'HandNode'

    def set_sid(self, sid: str) -> None:
        self._sid = sid

    def increment_num_selected_cards(self) -> None:
        self._num_cards_selected += 1

    def decrement_num_selected_cards(self) -> None:
        self._num_cards_selected -= 1

