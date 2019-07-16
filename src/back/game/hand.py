# TODO: test hand trie instead vs. hand hash table
# TODO: where to put this file and general path design stuff
# TODO: evaluate necessity of asserts
# TODO: decide what exactly should be a runtime error and whether or not
#       ingame notifications should be through error messages
# TODO: normalize use of double or single quotes
# TODO: assertions should be things that I assume will never happen
#       because I check for them beforehand, e.g. invalid hands cannot
#       be compared
# TODO: wrtie tests  # keeping this typo cuz I love irony

from __future__ import annotations

import numpy as np
import pickle

from .utils import hand_hash, card_names, id_desc_dict
from typing import List, Dict, Union, Optional, Iterator
from json import dumps, loads
import os


# TODO create the .pkl if it doesn't exist
# hash table for identifying hands
with open(
    f"{os.path.expanduser('~')}/presidents/src/back/game/utils/hand_table.pkl",
    "rb",
) as file:
    hand_table = pickle.load(file)


class Hand:
    """
    Base class for president's hands and the core data structure of
    Presidents. Refactoring from original Hand class found in class
    Hand within spcl_presidents.py. Uses numpy arrays to represent
    hands.

    Right now, the way this is set up is for individual selection of
    cards in a GUI where the player would click on a card to start
    building a hand and have the validity (whether it is a double,
    triple, bomb, etc.) of the hand update dynamically. This also allows
    the collection of data on individual card additions and removals.

    Singles cannot be stored. If a single card is selected, all stored
    hands containing that card will be highlighted, signifying deletion
    of the stored hand(s) if the single is played. The same applies to
    the selection of stored hands; if a stored hand is selected, all
    stored hands containing any cards in the selected stored hand will
    be highlighted...

    No support for hands with more than 5 cards.
    """

    def __init__(
        self,
        cards: Optional[np.ndarray[np.uint8]] = None,
        identity: Optional[int] = None,
        head: Optional[int] = None,
    ) -> None:
        if cards is None:  # default constructor; empty hand
            self._cards: np.ndarray[np.uint8] = np.zeros(
                shape=5, dtype=np.uint8
            )
            self._id: int = 0
            self._head: int = 4  # lowest empty index; -1 if full
        # .copy classmethod constructor; should not be used manually
        elif head is not None:
            self._cards = cards.copy()
            self._id = identity  # type: ignore
            self._head = head
        # testing constructor (i.e. Hand([...])); auto identifies
        # list requirements: length <= 5, ints between 0 and 52
        #   inclusive, non-zero values must be unique
        else:
            assert len(cards) <= 5, "hands can have up to 5 cards"
            filtered: List[int] = list(filter((0).__ne__, cards))
            len_filtered = len(filtered)
            self._head = 4 - len_filtered
            assert all(
                map(
                    lambda x: isinstance(x, (int, np.integer))
                    and 1 <= x <= 52,
                    filtered,
                )
            ), "cards must be ints between 0 and 52 inclusive"
            # cards with the zeroes removed
            # checks uniqueness of non-zero values
            assert len(filtered) == len(set(filtered)), "cards must be unique"
            # pads cards to length 5
            self._cards: np.ndarray[np.uint8] = np.pad(  # type: ignore
                np.array(sorted(filtered), dtype=np.uint8),
                (5 - len_filtered, 0),
                "constant",
            )

            self._identify()

    @classmethod
    def copy(cls, hand: Hand) -> Hand:
        return cls(hand._cards, hand._id, hand._head)

    def __getitem__(self, index: Union[int, slice]) -> np.uint8:
        return self._cards[index]

    def __setitem__(self, index: Union[int, slice], card: int) -> None:
        self._cards[index] = card

    def __hash__(self) -> int:
        return hand_hash(self._cards)

    def __contains__(self, card: int) -> bool:
        assert 1 <= card <= 52, "invalid card cannot be in hand."
        return card in self._cards  # TODO: should I slice before this?

    def __iter__(self) -> Iterator[np.uint8]:  # TODO: return type for this
        for i in range(self._head + 1, 5):
            yield self[i]

    def __str__(self) -> str:
        to_join = [card_names[card] for card in self]
        return " ".join(to_join) + f": {self.id_desc}"

    def __repr__(self) -> str:
        return (
            f"<Hand {id(self)}; cards: {str(self._cards)}; id: {self._id};"
            f" head: {self._head}>"
        )

    def __len__(self) -> int:
        return self._num_cards

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Hand):
            return NotImplemented
        return (
            np.array_equal(self._cards, other._cards)
            and self._id == other._id
            and self._head == other._head
        )

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Hand):
            return NotImplemented
        return not self == other

    def _is_comparable(self, other: Hand) -> bool:
        if not self.is_valid or not other.is_valid:
            raise AssertionError(
                "attempting to compare 1 or more invalid hands."
            )
        # one-directional because non-bombs cannot be compared with
        # bombs
        if self._id == other._id or self.is_bomb:
            return True
        else:
            return False

    def __lt__(self, other: Hand) -> bool:
        if not self._is_comparable(other):
            raise NotPlayableOnError(
                f"a {self.id_desc} cannot be played on a {other.id_desc}"
            )
        if self.is_bomb and other.is_bomb:
            return self[1] < other[1]  # second card is always part of the quad
        elif self.is_bomb:
            return False
        elif self.is_single or self.is_double or self.is_straight:
            return self[4] < other[4]
        elif self.is_triple or self.is_fullhouse:
            return self[2] < other[2]
        else:
            raise AssertionError("unidentified hand.")

    def __gt__(self, other: Hand) -> bool:
        if not self._is_comparable(other):
            raise NotPlayableOnError(
                f"a {self.id_desc} cannot be played on a {other.id_desc}"
            )
        if self.is_bomb and other.is_bomb:
            return self[1] > other[1]  # second card is always part of the quad
        elif self.is_bomb:
            return True
        elif self.is_single or self.is_double or self.is_straight:
            return self[4] > other[4]
        elif self.is_triple or self.is_fullhouse:
            return self[2] > other[2]
        else:
            raise AssertionError("unidentified hand.")

    def __le__(self, other: Hand) -> bool:
        return self < other or self == other

    def __ge__(self, other: Hand) -> bool:
        return self > other or self == other

    @property
    def is_empty(self) -> bool:
        return self._id == 0

    @property
    def is_full(self) -> bool:
        return self._head == -1

    @property
    def is_single(self) -> bool:
        return self._id == 11

    @property
    def is_double(self) -> bool:
        return self._id == 21

    @property
    def is_triple(self) -> bool:
        return self._id == 31

    @property
    def is_fullhouse(self) -> bool:
        return self._id == 51

    @property
    def is_straight(self) -> bool:
        return self._id == 52

    @property
    def is_bomb(self) -> bool:
        return self._id == 53

    @property
    def is_valid(self) -> bool:
        return self._id % 10 > 0

    @property
    def _num_cards(self) -> int:
        return 4 - self._head

    @property
    def id_desc(self) -> str:
        return id_desc_dict[self._id]

    def reset(self) -> None:
        self._cards = np.zeros(shape=5, dtype=np.uint8)
        self._id = 0
        self._head = 4

    def to_list(self) -> List[int]:
        # converts each card to int first for json serializability
        return list(map(int, self.__iter__()))

    def _identify(self) -> None:
        try:
            self._id = hand_table[hash(self)]
        except KeyError:
            self._id = self._num_cards * 10

    def _insertion_index(self, card: int) -> int:
        curr_index: int = self._head + 1
        while curr_index < 5:
            if card > self[curr_index]:
                curr_index += 1
            else:
                return curr_index - 1
        return 4

    def add(self, card: int) -> None:
        assert 1 <= card <= 52, "attempting to add invalid card."
        if self.is_full:
            raise FullHandError("cannot add any more cards to this hand.")
        if card in self:
            raise DuplicateCardError(f"{card} already in hand.")
        ii: int = self._insertion_index(card)
        # left shift lower cards if there's a card at the ii
        if self[ii]:
            head: int = self._head  # avoids multiple attribute accesses
            self[head:ii] = self[head + 1 : ii + 1]
        self[ii] = card
        self._head -= 1
        self._identify()

    def _card_index(self, card: int) -> int:
        try:
            # TODO: is this the fastest way?
            return np.where(self._cards == card)[0][0]
        except IndexError:
            raise CardNotInHandError(
                f"attempting to find index of card ({card}) which is not in"
                "hand."
            )

    def remove(self, card) -> None:
        if self._id == 0:
            raise CardNotInHandError(
                "attempting to remove from an empty hand."
            )
        ci: int = self._card_index(card)
        self._head += 1
        head: int = self._head  # avoids multiple attribute accesses
        self[ci] = 0
        # right shift lower cards
        self[head + 1 : ci + 1] = self[head:ci]
        self[head] = 0
        self._identify()


class CardNotInHandError(RuntimeError):
    pass


class DuplicateCardError(RuntimeError):
    pass


class FullHandError(RuntimeError):
    pass


class NotPlayableOnError(RuntimeError):
    pass
