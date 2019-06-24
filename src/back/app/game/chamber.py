from __future__ import annotations

from typing import List

import numpy as np
from llist import dllistnode

from . import Hand, CardNotInHandError
from .utils import IterNodesDLList


# TODO: use del for removing nodes?
# TODO: make high quality representation of what is going on


class Chamber:
    """
    Storage for cards and hands specifically designed for fast runtimes
    in context of front end interaction. Base class for EmittingChamber.

    Uses doubly linked list because node removal is constant time.

    Runtime errors when attempting operation that involves a card that
    is not in the chamber; is not an assertion because such an operation
    could reasonably not be the result of a bug, e.g. not knowing
    whether a card is in the chamber or a DOM modification.

    For operations that involve more than one card at a time, checks
    that all the cards are in the chamber before proceeding to avoid
    having to undo link operations.
    """
    def __init__(self, cards: np.ndarray=None) -> None:
        self.current_hand: Hand = Hand()
        self.num_cards: int = 0
        self._cards: np.ndarray = np.full(shape=53, fill_value=None,
                                          dtype=np.object)
        if cards:
            for card in cards:
                self._cards[card] = HandPointerDLList()
            self.num_cards = len(cards)
        self._hands: HandNodeDLList = HandNodeDLList()

    def __contains__(self, card) -> bool:
        return self._cards[card] is not None

    # TODO: make this generator based
    def __iter__(self):
        return [card for card in range(1, 53) if card in self].__iter__()

    # TODO: should be simple but meaningful
    def __repr__(self) -> str:
        return 'Chamber'

    @property
    def is_empty(self) -> bool:
        return self.num_cards == 0

    def reset(self) -> None:
        self.current_hand.reset()
        self.num_cards = 0
        self._cards.fill(None)
        self._hands.clear()

    def add_card(self, card: int, check: bool=True) -> None:
        if check:
            self._check_card_not_in(card)
        self._cards[card] = HandPointerDLList()
        self.num_cards += 1

    def add_cards(self, cards) -> None:
        self._check_cards_not_in(cards)
        for card in cards:
            self.add_card(card, check=False)  # already checked

    def remove_card(self, card: int, check: bool=True) -> None:
        """
        Here it is important to note that we do not need to deselect the
        card before we remove it because all the hand nodes that contain
        the card will be removed.

        Using a try/except here because most of the time, the card will
        be in the hand but this should be empirically verified and the
        performance difference tested. TODO
        """
        if check:
            self._check_card_in(card)
        # Cards that are to be removed will not always be in the current
        # hand, i.e. during trading
        try:
            self.current_hand.remove(card)
        except CardNotInHandError:
            pass
        for base_hand_pointer_node in self._cards[card].iter_nodes():
            hand_node = base_hand_pointer_node.value
            for hand_pointer_node in hand_node.value:
                if hand_pointer_node is base_hand_pointer_node:
                    continue
                else:
                    hand_pointer_node.owner().remove(hand_pointer_node)
            hand_node.owner().remove(hand_node)
        self._cards[card] = None
        self.num_cards -= 1

    def remove_cards(self, cards):
        self._check_cards_in(cards)
        for card in cards:
            self.remove_card(card, check=False)  # already checked

    def add_hand(self, hand: Hand) -> None:
        self.deselect_cards(hand)
        hand_pointer_nodes: List[HandPointerNode] = list()
        cards: List[int] = list()
        hand_node: HandNode = HandNode(hand_pointer_nodes)
        for card in hand:
            hand_pointer_node: HandPointerNode = HandPointerNode(hand_node)
            hand_pointer_nodes.append(hand_pointer_node)
            cards.append(card)
            self._cards[card].appendnode(hand_pointer_node)
        self._hands.appendnode(hand_node)

    def select_card(self, card: int, check: bool=True) -> None:
        if check:
            self._check_card(card)
        self.current_hand.add(card)
        # self._cards[card] is a HandPointerDLList; iterating through
        # it, via the class' own __iter__ (which iterates through the
        # values, not the nodes) gives us each HandNode which contains
        # card passed to the function
        for hand_node in self._cards[card]:
            hand_node.increment_num_selected_cards()

    def select_cards(self, cards) -> None:
        self._check_cards(cards)
        for card in cards:
            self.select_card(card, check=False)  # already checked

    def deselect_card(self, card: int, check: bool=True) -> None:
        if check:
            self._check_card(card)
        self.current_hand.remove(card)
        for hand_node in self._cards[card]:
            hand_node.decrement_num_selected_cards()

    def deselect_cards(self, cards) -> None:
        self._check_cards(cards)
        for card in cards:
            self.deselect_card(card, check=False)  # already checked

    def clear_hands(self) -> None:
        self._reset_card_dllists()
        self._hands.clear()

    def _reset_card_dllists(self) -> None:
        for maybe_dll in self._cards:
            if maybe_dll is not None:
                maybe_dll.clear()

    def _check_card_in(self, card: int):
        if card not in self:
            raise CardNotInChamberError(f'{card} not in chamber.')

    def _check_cards_in(self, cards: List[int]):
        for card in cards:
            self._check_card_in(card)

    def _check_card_not_in(self, card: int):
        if card in self:
            raise CardAlreadyInChamberError(f'{card} already in chamber')

    def _check_cards_not_in(self, cards: List[int]):
        for card in cards:
            self._check_cards_not_in(card)

    def deselect_selected(self) -> None:
        self.deselect_cards(self.current_hand)


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
    def __init__(self, hand_node: HandNode) -> None:
        super().__init__(None)
        self.value: HandNode = hand_node

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
    Node's value is the list of HandPointerNodes corresponding to the 
    cards in the hand; increments/decrements the number of cards
    selected in each hand as they are selected in the chamber.
    """
    def __init__(self, hand_pointer_nodes: List[HandPointerNode]) -> None:
        super().__init__(hand_pointer_nodes)
        self._num_cards_selected: int = 0

    def __repr__(self) -> str:
        return 'HandNode'

    def increment_num_selected_cards(self) -> None:
        self._num_cards_selected += 1

    def decrement_num_selected_cards(self) -> None:
        self._num_cards_selected -= 1


class CardAlreadyInChamberError(RuntimeError):
    pass


class CardNotInChamberError(RuntimeError):
    pass
