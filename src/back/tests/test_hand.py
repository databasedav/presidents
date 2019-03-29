from ..app.components import *
from typing import Optional
import numpy as np
import pytest
from numpy.testing import assert_array_equal


def test_default_constructor():
    hand: Hand = Hand()
    assert_array_equal(hand._cards, np.zeros(shape=5, dtype=np.uint8))
    assert hand._id == 0
    assert hand._insertion_index == 4


def test_testing_constructor():
    hand: Optional[Hand] = None

    # empty hand
    hand = Hand([])
    assert_array_equal(hand._cards, np.zeros(shape=5, dtype=np.uint8))
    assert hand._id == 0
    assert hand._insertion_index == 4

    # sorted, length < 5
    hand = Hand([1])
    assert_array_equal(hand._cards,
                       np.array([0, 0, 0, 0, 1], dtype=np.uint8))
    assert hand._id == 11
    assert hand._insertion_index == 3

    hand = Hand([0, 0, 1])
    assert_array_equal(hand._cards,
                       np.array([0, 0, 0, 0, 1], dtype=np.uint8))
    assert hand._id == 11
    assert hand._insertion_index == 3

    hand = Hand([1, 52])
    assert_array_equal(hand._cards,
                       np.array([0, 0, 0, 1, 52], dtype=np.uint8))
    assert hand._id == 20
    assert hand._insertion_index == 2

    hand = Hand([1, 5, 9, 13])
    assert_array_equal(hand._cards,
                       np.array([0, 1, 5, 9, 13], dtype=np.uint8))
    assert hand._id == 40
    assert hand._insertion_index == 0

    # unsorted, length < 5
    hand = Hand([1])
    assert_array_equal(hand._cards,
                       np.array([0, 0, 0, 0, 1], dtype=np.uint8))
    assert hand._id == 11
    assert hand._insertion_index == 3

    hand = Hand([1, 0, 0])
    assert_array_equal(hand._cards,
                       np.array([0, 0, 0, 0, 1], dtype=np.uint8))
    assert hand._id == 11
    assert hand._insertion_index == 3

    hand = Hand([52, 1])
    assert_array_equal(hand._cards,
                       np.array([0, 0, 0, 1, 52], dtype=np.uint8))
    assert hand._id == 20
    assert hand._insertion_index == 2

    hand = Hand([13, 9, 5, 1])
    assert_array_equal(hand._cards,
                       np.array([0, 1, 5, 9, 13], dtype=np.uint8))
    assert hand._id == 40
    assert hand._insertion_index == 0

    # sorted length 5
    hand = Hand([1, 2, 3, 4, 5])
    assert_array_equal(hand._cards,
                       np.array([1, 2, 3, 4, 5], dtype=np.uint8))
    assert hand._id == 53
    assert hand._insertion_index == -1

    # unsorted length 5
    hand = Hand([5, 4, 3, 2, 1])
    assert_array_equal(hand._cards,
                       np.array([1, 2, 3, 4, 5], dtype=np.uint8))
    assert hand._id == 53
    assert hand._insertion_index == -1

    # length assertion
    with pytest.raises(AssertionError, match=r'up to 5'):
        hand = Hand([1, 2, 3, 4, 5, 6])

    # int assertion
    with pytest.raises(AssertionError, match=r'must be ints'):
        hand = Hand([1, 'hello', 3, 'world', 5])

    # dupe assertion
    with pytest.raises(AssertionError, match=r'unique'):
        hand = Hand([1, 1])

    with pytest.raises(AssertionError, match=r'unique'):
        hand = Hand([0, 1, 0, 1, 0])


def test_testing_constructor_random():
    # TODO
    ...


def test_copy_constructor():
    hand: Hand = Hand([1, 2, 3, 4, 5])
    hand_copy = Hand.copy(hand)
    assert hand == hand_copy


def test_from_json():
    # TODO
    ...


def test__getitem__():
    hand: Hand = Hand([1, 2, 3, 4, 5])
    assert hand[2] == 3


def test__setitem__():
    hand: Hand = Hand([1, 2, 3, 4, 5])
    hand[4] = 52
    assert hand[4] == 52
    # setting can add duplicate cards
    hand[2] = 5
    asert hand[2] == 5


def test__hash__():
    # TODO
    ...


def test__contains__():
    hand: Hand = Hand([1, 2, 3, 4, 5])
    for card in range(1, 6):
        assert card in hand
    assert 6 not in hand


def test__iter__():
    hand: Hand = Hand([1, 2, 3, 4, 5])
    for card1, card2 in zip(hand, range(1, 6)):
        assert card1 == card2


def test__str___():
    # TODO
    ...


def test__repr__():
    # TODO
    ...


def test__len__():
    hand: Hand = Hand([1, 2, 3])
    assert len(hand) == 3
    hand: Hand = Hand([1, 2, 3, 4, 5])
    assert len(hand) == 5


def test__eq__():
    hand1: Hand = Hand([1, 2, 3, 4, 5])
    hand2: Hand = Hand([1, 2, 3, 4, 5])
    assert hand1 == hand2


def test__ne__():
    hand1: Hand = Hand([1, 2, 3, 4, 6])
    hand2: Hand = Hand([1, 2, 3, 4, 5])
    assert hand1 != hand2


def test_is_comparable():
    # validity
    hand1: Hand = Hand([1, 2])
    hand2: Hand = Hand([1, 52])

    with pytest.raises(AssertionError, match=r'invalid'):
        hand1._is_comparable(hand2)

    with pytest.raises(AssertionError, match=r'invalid'):
        hand2._is_comparable(hand1)

    hand2 = Hand([5, 6])
    assert hand1._is_comparable(hand2)
    assert hand2._is_comparable(hand1)

    hand2 = Hand([5, 6, 7])
    assert not hand1._is_comparable(hand2)
    assert not hand2._is_comparable(hand1)

    # bomb
    hand2 = Hand([5, 6, 7, 8, 9])
    assert not hand1._is_comparable(hand2)
    assert hand2._is_comparable(hand1)


def test__lt__():
    with pytest.raises(NotPlayableOnError, match=r'cannot be played'):
        hand1: Hand = Hand([1, 2])
        hand2: Hand = Hand([1, 52])

    with pytest.raises(NotPlayableOnError, match=r'cannot be played'):
        hand1: Hand = Hand([1, 2])
        hand2: Hand = Hand([1, 52])

