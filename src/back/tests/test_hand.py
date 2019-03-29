from ..app.components import Hand, NotPlayableOnError, hand_table
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
    hand1: Hand = Hand([1, 2])
    hand2: Hand = Hand([1, 52])

    with pytest.raises(NotPlayableOnError, match=r'cannot be played'):
        hand1 < hand2

    with pytest.raises(NotPlayableOnError, match=r'cannot be played'):
        hand2 < hand1

    hand2 = Hand([3, 4])
    assert hand1 < hand2


def test__gt__():
    hand1: Hand = Hand([1, 2])
    hand2: Hand = Hand([1, 52])

    with pytest.raises(NotPlayableOnError, match=r'cannot be played'):
        hand1 > hand2

    with pytest.raises(NotPlayableOnError, match=r'cannot be played'):
        hand2 > hand1

    hand2 = Hand([3, 4])
    assert hand2 > hand1


def test__le__():
    hand1: Hand = Hand([1, 2])
    hand2: Hand = Hand([1, 3])
    assert hand1 <= hand2

    hand2 = Hand([1, 2])
    assert hand1 <= hand2


def test__ge__():
    hand1: Hand = Hand([1, 2])
    hand2: Hand = Hand([1, 3])
    assert hand2 >= hand2

    hand2 = Hand([1, 2])
    assert hand1 >= hand2


def test_is_empty():
    hand: Hand = Hand()
    assert hand.is_empty


def test_is_full():
    hand: Hand([1, 2, 3, 4, 5])
    assert hand.is_full


def test_is_single():
    hand: Hand([1])
    assert hand.is_single


def test_is_double():
    hand: Hand([1, 2])
    assert hand.is_double


def test_is_triple():
    hand: Hand([1, 2, 3])
    assert hand.is_triple


def test_is_fullhouse():
    hand: Hand([1, 2, 3, 5, 6])
    assert hand.is_fullhouse


def test_is_straight():
    hand: Hand([1, 5, 9, 13, 17])
    assert hand.is_straight


def test_is_bomb():
    hand: Hand([1, 2, 3, 4, 52])
    assert hand.is_bomb


def test_is_valid():
    hand: Hand([1])
    assert hand.is_valid

    hand.add(52)
    assert not hand.is_valid


def test_id_desc():
    # TODO
    ...


def test_reset():
    hand: Hand([1, 2, 3, 4, 5])
    zeros_arr = np.zeros(shape=5, dtype=np.uint8)
    with pytest.raises(AssertionError, match=r'are not equal'):
        assert_array_equal(hand._cards, zeros_arr)
    assert hand._id != 0
    assert hand_head != 4

    hand.reset()
    assert_array_equal(hand._cards, zeros_arr)
    assert hand._id == 0
    assert hand_head == 4


def test_to_json():
    # TODO
    ...


def test_to_list():
    hand: Hand = Hand([1, 2, 3])
    assert hand.to_list() == [1, 2, 3]


def test_identify():
    # tests testing constructor for identifying random sample of valid
    # hands
    # TODO
    ...


def test_insertion_index():
