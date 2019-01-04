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

from .utils.utils import hand_hash
from typing import List, Dict, Union
from json import dumps, loads
from mypy_extensions import NoReturn

# TODO: where to put this?
card_names = [
    None, '3♣', '3♦', '3♥', '3♠', '4♣', '4♦', '4♥', '4♠', '5♣', '5♦', '5♥',
    '5♠', '6♣', '6♦', '6♥', '6♠', '7♣', '7♦', '7♥', '7♠', '8♣', '8♦', '8♥',
    '8♠', '9♣', '9♦', '9♥', '9♠', '10♣', '10♦', '10♥', '10♠', 'j♣', 'j♦', 'j♥',
    'j♠', 'q♣', 'q♦', 'q♥', 'q♠', 'k♣', 'k♦', 'k♥', 'k♠', 'a♣', 'a♦', 'a♥',
    'a♠', '2♣', '2♦', '2♥', '2♠',
]

# hash table for identifying hands
try:
    with open('./src/server/hand_table.pkl', 'rb') as file:
        hand_table = pickle.load(file)
except FileNotFoundError:
    with open('hand_table.pkl', 'rb') as file:
        hand_table = pickle.load(file)


# TODO: should this be in the class?
id_desc_dict = {
    0: "empty hand",  # i.e. [0, 0, 0, 0, 0]
    11: "single",  # e.g. [0, 0, 0, 0, 1]
    20: "invalid hand (2)",  # e.g. [0, 0, 0, 1, 52]
    21: "double",  # e.g. [0, 0, 0, 1, 2]
    30: "invalid hand (3)",  # e.g. [0, 0, 1, 2, 52]
    31: "triple",  # e.g. [0, 0, 1, 2, 3]
    40: "invalid hand (4)",  # e.g. [0, 1, 2, 3, 4]
    50: "invalid hand (5)",  # e.g. [1, 2, 3, 5, 52]
    51: "fullhouse",  # e.g. [1, 2, 3, 51, 52]
    52: "straight",  # e.g. [1, 5, 9, 13, 17]
    53: "bomb",  # e.g. [1, 49, 50, 51, 52]
}

# TODO: where to put these errors
# TODO: are these errors even necessary


class Hand(object):
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

    def __init__(self,
                 _cards: np.ndarray=None,
                 _id: int=None,
                 _insertion_index: int=None) -> None:
        if _cards is None:  # default empty hand
            self._cards = np.zeros(shape=5, dtype=np.uint8)
            self._id = 0
            self._insertion_index = 4
        else:
            assert len(_cards) == 5
            self._cards = np.array(_cards, dtype=np.uint8)
            if _id is not None and _insertion_index is not None:
                self._id = _id
                self._insertion_index = _insertion_index
            # this case should only be used for testing and debugging
            # TODO: I don't like this, mostly because of the number of
            #       cards hack, ultimately I think the amount it will
            #       make testing easier is probably worth it
            elif _id is None and _insertion_index is None:
                self._identify()
                self._insertion_index = 4 - self._id // 10
            else:
                raise AssertionError("Bug: only id or insertion index is " +
                                     "given with custom hand constructor.")

    @classmethod
    def from_json(cls, json_hand: str):
        # hd = hand dict
        hd: Dict[str, Union[np.ndarray, int]] = loads(json_hand)
        return cls(hd['_cards'], hd['_id'], hd['_insertion_index'])

    @classmethod
    def copy(cls, hand: Hand) -> Hand:
        return cls(hand._cards, hand._id, hand._insertion_index)

    def __getitem__(self, key: Union[int, slice]) -> int:
        return self._cards[key]

    def __setitem__(self, key: Union[int, slice], card: int) -> None:
        self._cards[key] = card

    def __hash__(self) -> int:
        return hand_hash(self._cards)

    def __contains__(self, card: int) -> object:
        assert 1 <= card <= 52, "Bug: invalid card cannot be in hand."
        return card in self._cards  # TODO: should I slice before this?

    def __iter__(self):  # TODO: return type for this
        return self[self._insertion_index + 1:].__iter__()

    def __str__(self) -> str:
        to_join = [card_names[card] for card in self]
        return " ".join(to_join) + f": {self.id_desc}"

    def __repr__(self) -> str:
        # TODO: how to multiline f string plz
        return f"cards: {str(self._cards)}; id: {self._id}; ii: " + \
               f"{self._insertion_index}"

    def __len__(self) -> int:
        return self._number_of_cards

    def __eq__(self, other: Hand) -> bool:
        return (np.array_equal(self._cards, other._cards) and  # type: ignore
                self._id == other._id and  # type: ignore
                (self._insertion_index
                    == other._insertion_index))  # type: ignore

    def __ne__(self, other: Hand) -> bool:
        return not self == other

    def __lt__(self, other: Hand) -> bool:
        if not self._is_comparable(other):
            # TODO: should this be a runtime error?
            raise RuntimeError(
                f"A {self.id_desc} cannot be played on a {other.id_desc}.")
        if self.is_bomb and other.is_bomb:
            return self[1] < other[1]  # second card is always part of the quad
        elif self.is_bomb:
            return False
        elif other.is_bomb:
            return True
        elif self.is_single or self.is_double or self.is_straight:
            return self[4] < other[4]
        elif self.is_triple or self.is_fullhouse:
            return self[2] < other[2]
        else:
            raise AssertionError("Bug: unidentified hand.")

    def __gt__(self, other: Hand) -> bool:
        if not self._is_comparable(other):
            raise RuntimeError(
                f"A {self.id_desc} cannot be played on a {other.id_desc}.")
        if self.is_bomb and other.is_bomb:
            return self[1] > other[1]  # second card is always part of the quad
        elif self.is_bomb:
            return True
        elif other.is_bomb:
            return False
        elif self.is_single or self.is_double or self.is_straight:
            return self[4] > other[4]
        elif self.is_triple or self.is_fullhouse:
            return self[2] > other[2]
        else:
            raise AssertionError("Bug: unidentified hand.")

    def __le__(self, other: Hand) -> NoReturn:
        raise AssertionError('A <= call was made by a Hand.')

    def __ge__(self, other: Hand) -> NoReturn:
        raise AssertionError('A >= call was made by a Hand.')

    @property
    def is_empty(self) -> bool:
        return self._id == 0

    @property
    def is_full(self) -> bool:
        return self._insertion_index == -1

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
    def _number_of_cards(self) -> int:
        try:
            return 4 - self._insertion_index
        except AttributeError:
            return 5 - np.argmax(self._cards)

    @property
    def id_desc(self) -> str:
        return id_desc_dict[self._id]

    def reset(self) -> None:
        self._cards = np.zeros(shape=5, dtype=np.uint8)
        self._id = 0
        self._insertion_index = 4

    # TODO: why do I need this?
    def intersects(self, other: Hand) -> bool:  # TODO: refine this
        for card1 in self:
            for card2 in other:
                if card1 == card2:
                    return True
        return False

    def to_json(self) -> str:
        return dumps(self.__dict__, default=lambda x: x.tolist())

    def to_list(self) -> List:
        return list(map(int, self.__iter__()))

    def _is_comparable(self, other: Hand) -> bool:
        assert self.is_valid and other.is_valid, \
            "Bug: attempting to compare 1 or more invalid hands."
        # TODO: this case is specifically to show that one cannot
        #       possibly play a non bomb on a bomb, but should it be
        #       handled here? also this clearly is not symmetric so 
        #       don't like it since if I wanted the server to verify it
        #       as well, it would have to be the opposite
        if other.is_bomb and not self.is_bomb:
            return False
        elif self.is_bomb or self._id == other._id:
            return True
        else:
            return False

    def _identify(self) -> None:
        try:
            self._id = hand_table[hash(self)]
        except KeyError:
            self._id = self._number_of_cards * 10

    # TODO: is there any benefit to doing this recursively?
    def _insert_pos(self, card: int, current_index: int) -> int:
        if current_index == 5:
            return 4
        elif card > self[current_index]:
            return self._insert_pos(card, current_index + 1)
        else:
            return current_index - 1

    def add(self, card: int) -> None:
        # TODO: do I need these assertions?
        assert 1 <= card <= 52, "Bug: attempting to add invalid card."
        if card in self:
            raise DuplicateCardError(f'{card} already in hand.')
        if (self.is_full):  # TODO: should this be an error?
            raise FullHandError("Cannot add any more cards to this hand.")
        ii: int = self._insertion_index
        ip: int = self._insert_pos(card, ii + 1)
        self[ii: ip] = self[ii + 1: ip + 1]  # left shift lower cards
        self[ip] = card
        self._insertion_index -= 1
        self._identify()

    def _card_index(self, card: int) -> int:
        try:
            return np.where(self._cards == card)[0][0]  # TODO: justify in notebook
        except IndexError:
            raise CardNotInHandError('Attempting to find index of card ({card}) which is not in hand.')

    def remove(self, card) -> None:
        assert self._id != 0, "Bug: attempting to remove from an empty hand."
        ci: int = self._card_index(card)
        self[ci] = 0
        self._insertion_index += 1
        ii: int = self._insertion_index
        self[ii + 1: ci + 1] = self[ii: ci]  # right shift lower cards
        self[ii] = 0
        self._identify()


class DuplicateCardError(RuntimeError):
    pass


class FullHandError(RuntimeError):
    pass


class CardNotInHandError(RuntimeError):
    pass