from __future__ import annotations

from typing import List, Collection, Optional, Iterator, Iterable, Union, Type

import numpy as np
from llist import dllistnode

from . import Hand, CardNotInHandError, DuplicateCardError, FullHandError
from .utils import IterNodesDLList, id_desc_dict


# TODO: make high quality representation of what is going on

COMBOS = ['double', 'triple', 'fullhouse', 'straight', 'bomb']

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

    def __init__(self, cards: Collection[int] = None) -> None:
        self.hand: Hand = Hand()
        self._cards: np.ndarray[Optional[HandPointerDLList]] = np.full(
            shape=53, fill_value=None, dtype=np.object
        )
        self.num_cards: int = 0
        if cards:
            for card in cards:
                self._cards[card] = HandPointerDLList(card)
            self.num_cards = len(cards)
        self.doubles: HandNodeDLList = HandNodeDLList()
        self.triples: HandNodeDLList = HandNodeDLList()
        self.fullhouses: HandNodeDLList = HandNodeDLList()
        self.straights: HandNodeDLList = HandNodeDLList()
        self.bombs: HandNodeDLList = HandNodeDLList()
    
    @property
    def _num_hands(self):
        return sum(getattr(self, f'_{desc}').size for desc in ['doubles', 'triples', 'fullhouses', 'straights', 'bombs'])

    def __contains__(self, card_or_hand: Union[int, Collection[int]]) -> bool:
        # card
        if not isinstance(card_or_hand, Collection):
            return self._cards[card_or_hand] is not None
        # hand
        else:
            # no hands or not all cards in hand in chamber
            if self._num_hands == 0 or not all(
                card in self for card in card_or_hand
            ):
                return False

            card_w_least_hands = min(
                list(card_or_hand), key=lambda card: self._cards[card].size
            )
            for hand_node in self._cards[card_w_least_hands]:
                hand_pointer_nodes = hand_node.value
                # don't need to check HandNodes storing off-length hands
                if len(card_or_hand) != len(hand_pointer_nodes):
                    continue
                # if cards in HandNode match hand, then hand is in chamber;
                # else move onto the next HandNode
                elif all(
                    card == hand_pointer_node.owner().card
                    for card, hand_pointer_node in zip(
                        card_or_hand, hand_pointer_nodes
                    )
                ):
                    return True
            return False

    @property
    def cards(self):
        return list(self)

    def __iter__(self) -> Iterator[int]:
        for card in range(1, 53):
            if card in self:
                yield card

    # TODO: should be simple but meaningful
    def __repr__(self) -> str:
        return "Chamber"

    @property
    def is_empty(self) -> bool:
        return self.num_cards == 0

    def reset(self) -> None:
        self.hand.reset()
        self._cards.fill(None)
        self.num_cards = 0
        for combo in COMBOS:
            getattr(self, f'{combo}s').clear()

    # check argument should not be used outside of this class; is there
    # any way to enforce this? TODO
    def add_card(self, card: int, *, check: bool = True) -> None:
        if check:
            self._check_card_not_in(card)
        self._cards[card] = HandPointerDLList(card)
        self.num_cards += 1

    def add_cards(self, cards) -> None:
        self._check_cards_not_in(cards)
        for card in cards:
            self.add_card(card, check=False)  # already checked

    def remove_card(self, card: int, *, check: bool = True) -> None:
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
            self.hand.remove(card)
        except CardNotInHandError:
            pass

        # iterate through hand_pointer_nodes
        for base_hand_pointer_node in self._cards[card].iter_nodes():
            hand_node = base_hand_pointer_node.value
            for hand_pointer_node in hand_node.hand_pointer_nodes:
                # base_hand_pointer_nodes are removed when deleting card
                # because they must first be used to the HandNode they
                # point to after the other HandPointerNodes stored by
                # the HandNode are removed
                if hand_pointer_node is not base_hand_pointer_node:
                    # .owner() returns a weakref to the
                    # hand_pointer_node's corresponding
                    # HandPointerDLList
                    hand_pointer_node.owner().remove(hand_pointer_node)
            hand_node.owner().remove(hand_node)
        # remove only reference to HandPointerDLList
        self._cards[card] = None
        self.num_cards -= 1

    def remove_cards(self, cards: Iterable[int]):
        self._check_cards_in(cards)
        for card in cards:
            self.remove_card(card, check=False)  # already checked

    def _hand_check(self, hand) -> Hand:
        """
        Makes sure hand can be added and returns the hand
        """
        if hand is not self.hand:
            assert 1 < len(hand) <= 5, "can only add hands with 2-5 cards"
            self._check_cards_in(hand)
            assert all(
                hand[i] < hand[i + 1]  # type:ignore
                for i in range(len(hand) - 1)
            ), "hand must be ordered"
        hand = hand if isinstance(hand, Hand) else Hand(hand)
        # TODO: this should be a permitted presidents error
        if not hand.is_valid:
            raise HandNotStorableError(f'hand {str(hand)} cannot be stored')
        # TODO: this should be an unpermitted presidents error
        if hand in self:
            raise HandAlreadyStoredError(f'hand {str(hand)} already stored')
        return hand

    def add_hand(self, hand: Collection[int]) -> None:
        hand = self._hand_check(hand)
        self.deselect_cards(hand)
        self._add_hand_helper(hand, HandNode)

    def _add_hand_helper(
        self, hand, hand_node_class: HandNode, **hnc_kwargs
    ) -> None:
        """
        Helper so maintaining emitting add hand is easier as the only
        difference is creating an emitting hand node with the server fed
        in.
        """
        hand_pointer_nodes: List[HandPointerNode] = list()
        hand_node: HandNode = hand_node_class(hand, hand_pointer_nodes, **hnc_kwargs)
        for card in hand:
            hand_pointer_node: HandPointerNode = HandPointerNode(hand_node)
            # appending pointer to list of HandPointerNodes living on
            # HandNode
            hand_pointer_nodes.append(hand_pointer_node)
            # appending node to HandPointerDLList
            self._cards[card].appendnode(hand_pointer_node)
        getattr(self, f'{id_desc_dict[hand_node._id]}s').add(hand_node)

    def select_card(self, card: int, check: bool = True) -> None:
        if check:
            self._check_card_in(card)
        self.hand.add(card)
        # self._cards[card] is a HandPointerDLList; iterating through
        # it, via the class' own __iter__ (which iterates through the
        # values, not the nodes) gives us each HandNode which contains
        # the card passed to the function
        for hand_node in self._cards[card]:
            hand_node.increment_num_selected_cards()

    def select_cards(self, cards: Iterable[int]) -> None:
        self._check_cards_in(cards)
        for card in cards:
            try:
                self.select_card(card, check=False)  # already checked
            # this is an assertion because multiple card selections
            # should be checked beforehand; same for deselection below
            except (DuplicateCardError, FullHandError):
                raise AssertionError("bad select cards call")

    def deselect_card(self, card: int, check: bool = True) -> None:
        if check:
            self._check_card_in(card)
        self.hand.remove(card)
        for hand_node in self._cards[card]:
            hand_node.decrement_num_selected_cards()

    def deselect_cards(self, cards: Iterable[int]) -> None:
        self._check_cards_in(cards)
        for card in cards:
            try:
                self.deselect_card(card, check=False)  # already checked
            except CardNotInHandError:
                raise AssertionError("bad deselect cards call")

    def deselect_selected(self) -> None:
        self.deselect_cards(self.hand)

    def clear_hands(self) -> None:
        self._reset_card_dllists()
        self._hands.clear()

    def _reset_card_dllists(self) -> None:
        for card in self:
            self._cards[card].clear()

    def _check_card_in(self, card: int):
        if card not in self:
            raise CardNotInChamberError(f"{card} not in chamber.")

    def _check_cards_in(self, cards: Iterable[int]):
        for card in cards:
            self._check_card_in(card)

    def _check_card_not_in(self, card: int):
        if card in self:
            raise CardAlreadyInChamberError(f"{card} already in chamber")

    def _check_cards_not_in(self, cards: Iterable[int]):
        for card in cards:
            self._check_card_not_in(card)

    def _get_min_card(self) -> int:
        for card in self:
            return card

    def _get_max_card(self) -> int:
        for card in range(52, 0, -1):
            if self._cards[card] is not None:
                return card


class HandPointerDLList(IterNodesDLList):
    def __init__(self, card: int) -> None:
        self.card: int = card

    def __repr__(self) -> str:
        return "HandPointerDLList"


class HandPointerNode(dllistnode):
    """
    Wrapper for dllistnode that allows the value of the node to be a
    pointer to another node.
    """
    def __init__(self, hand_node: HandNode) -> None:
        super().__init__(None)
        self.value: HandNode = hand_node

    def __repr__(self):
        return "HandPointerNode"


class HandNodeDLList(IterNodesDLList):
    """
    By default, can only store a single combo type. Insertions done
    right to left for constant time insertions made by bots who
    construct combos from lowest to greatest cards.
    """
    def __init__(self, id_: int = None):
        self._id = id_

    def __repr__(self) -> str:
        return "HandNodeDLList"

    def add(hand_node):
        """
        Adds hand node to list while maintaining order. Insertions done
        right to left.
        """
        assert not self._id or hand_node.value._id == self._id
        # find ordered insertion spot right to left
        prev = None
        curr = self.last
        while curr is not None and curr.value > hand_node.value:
            curr, prev = curr.prev, curr  # prev is new curr's next...
        if not prev:  # greatest
            self.appendnode(hand_node)
        else:
            self.insertnode(hand_node, prev)


class HandNode(dllistnode):
    """
    Node's value is the list of HandPointerNodes corresponding to the 
    cards in the hand; increments/decrements the number of cards
    selected in each hand as they are selected in the chamber.
    """
    def __init__(self, hand: Hand, hand_pointer_nodes: List[HandPointerNode]) -> None:
        super().__init__(hand)  # hand object is the value
        self.hand_pointer_nodes = hand_pointer_nodes
        self._num_cards_selected: int = 0

    def __repr__(self) -> str:
        return "HandNode"

    def increment_num_selected_cards(self) -> None:
        self._num_cards_selected += 1

    def decrement_num_selected_cards(self) -> None:
        self._num_cards_selected -= 1


class CardAlreadyInChamberError(RuntimeError):
    pass


class CardNotInChamberError(RuntimeError):
    pass


class HandAlreadyStoredError(RuntimeError):
    pass


class HandNotStorableError(RuntimeError):
    pass
