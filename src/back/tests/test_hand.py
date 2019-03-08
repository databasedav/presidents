from ..app.components import Hand
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

def test_copy_constructor():
    hand: Hand = Hand([1, 2, 3, 4, 5])
    hand_copy = Hand.copy(hand)
    assert hand == hand_copy

