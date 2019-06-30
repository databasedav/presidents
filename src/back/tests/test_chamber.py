from ..game.chamber import (
    Chamber,
    CardAlreadyInChamberError,
    CardNotInChamberError,
    Hand,
)
import numpy as np
from numpy.testing import assert_array_equal
from ..game.chamber import HandNodeDLList
import pytest


def test_cardless_constructor():
    chamber: Chamber = Chamber()
    assert chamber.hand.is_empty
    assert chamber.num_cards == 0
    assert all(card not in chamber for card in range(1, 53))
    assert chamber._hands.size == 0


def test_cardful_constructor():
    chamber: Chamber = Chamber(range(1, 14))
    assert all(card in chamber for card in range(1, 14))
    assert all(card not in chamber for card in range(14, 53))
    assert chamber.num_cards == 13
    assert isinstance(chamber._hands, HandNodeDLList)
    assert chamber._hands.size == 0


def test__contains__():
    # cards
    chamber: Chamber = Chamber()
    assert all(card not in chamber for card in range(1, 53))
    chamber = Chamber(range(1, 14))
    assert all(card in chamber for card in range(1, 14))
    assert all(card not in chamber for card in range(15, 53))

    # hands
    assert [1, 2] not in chamber
    chamber.add_hand([1, 2])
    assert [1, 2] in chamber
    assert [1, 2, 3, 4, 5] not in chamber
    chamber.add_hand([1, 2, 3, 4, 5])
    assert [1, 2, 3, 4, 5] in chamber


def test__iter__():
    chamber: Chamber = Chamber()
    assert not list(chamber)
    chamber = Chamber(range(1, 14))
    assert list(chamber)
    assert all(i + 1 == card for i, card in enumerate(chamber))


def test__repr__():
    # TODO
    ...


def test_is_empty():
    chamber: Chamber = Chamber()
    assert chamber.is_empty
    chamber = Chamber(range(1, 14))
    assert not chamber.is_empty


def test_reset():
    chamber: Chamber = Chamber(range(1, 14))
    chamber.select_cards([1, 2])
    chamber.add_hand([3, 4])
    assert not chamber.hand.is_empty
    assert any(card in chamber for card in range(1, 53))
    assert chamber.num_cards > 0
    assert chamber._hands.size > 0
    chamber.reset()
    assert chamber.hand.is_empty
    assert all(card not in chamber for card in range(1, 53))
    assert chamber.num_cards == 0
    assert chamber._hands.size == 0


def test_add_card():
    chamber: Chamber = Chamber()
    chamber.add_card(1)
    assert 1 in chamber
    assert chamber.num_cards == 1

    # test card check
    with pytest.raises(CardAlreadyInChamberError):
        chamber.add_card(1)


def test_add_cards():
    chamber: Chamber = Chamber()
    chamber.add_cards(range(1, 14))
    assert all(card in chamber for card in range(1, 14))
    assert chamber.num_cards == 13

    # card check
    with pytest.raises(CardAlreadyInChamberError):
        chamber.add_cards([1, 2])

    # does not add any card unless all cards are not already in chamber
    with pytest.raises(CardAlreadyInChamberError):
        chamber.add_cards([14, 1])
    assert 14 not in chamber


def test_remove_card():
    # no hands
    chamber: Chamber = Chamber(range(1, 14))
    assert all(card in chamber for card in range(1, 14))
    chamber.remove_card(1)
    assert 1 not in chamber
    assert all(card in chamber for card in range(2, 14))
    assert all(card not in chamber for card in range(15, 53))

    # one hand
    chamber = Chamber(range(1, 14))
    chamber.add_hand([1, 2])
    assert chamber._hands.size == 1
    chamber.remove_card(1)
    assert 1 not in chamber
    assert chamber._hands.size == 0

    # two hands
    chamber = Chamber(range(1, 14))
    chamber.add_hand([1, 2])
    chamber.add_hand([1, 3])
    assert chamber._hands.size == 2
    chamber.remove_card(1)
    assert 1 not in chamber
    assert chamber.num_cards == 12
    assert chamber._hands.size == 0

    # hey y not three
    chamber = Chamber(range(1, 14))
    chamber.add_hand([1, 2])
    chamber.add_hand([1, 3])
    chamber.add_hand([1, 4])
    assert chamber._hands.size == 3
    chamber.remove_card(1)
    assert 1 not in chamber
    assert chamber.num_cards == 12
    assert chamber._hands.size == 0

    # three hands with no common card
    chamber = Chamber(range(1, 14))
    chamber.add_hand([1, 2])
    chamber.add_hand([1, 3])
    chamber.add_hand([2, 3])
    assert chamber._hands.size == 3
    chamber.remove_card(1)
    assert 1 not in chamber
    assert chamber.num_cards == 12
    assert chamber._hands.size == 1
    chamber.remove_card(2)
    assert 2 not in chamber
    assert chamber.num_cards == 11
    assert chamber._hands.size == 0

    # three hands with no common card and cards in hand
    chamber = Chamber(range(1, 14))
    chamber.add_hand([1, 2])
    chamber.add_hand([1, 3])
    chamber.add_hand([2, 3])
    chamber.select_cards([1, 2])
    assert chamber._hands.size == 3
    assert chamber.hand == Hand([1, 2])
    chamber.remove_card(1)
    assert 1 not in chamber
    assert chamber.num_cards == 12
    assert chamber._hands.size == 1
    assert chamber.hand == Hand([2])
    chamber.remove_card(2)
    assert 2 not in chamber
    assert chamber.num_cards == 11
    assert chamber._hands.size == 0
    assert chamber.hand.is_empty

    # card check
    with pytest.raises(CardNotInChamberError):
        chamber = Chamber(range(1, 14))
        chamber.remove_card(15)


def test_remove_cards():
    chamber: Chamber = Chamber(range(1, 14))
    chamber.remove_cards([1, 2])
    assert 1 not in chamber and 2 not in chamber
    assert all(card in chamber for card in range(3, 14))
    assert chamber.num_cards == 11

    # card check
    with pytest.raises(CardNotInChamberError):
        chamber.remove_cards([14, 15])

    # does not remove any card unless all cards are in chamber
    with pytest.raises(CardNotInChamberError):
        chamber.remove_cards([3, 14])
    assert 3 in chamber


def test_add_hand():
    chamber: Chamber = Chamber(range(1, 14))
    chamber.add_hand([1, 2])
    assert chamber._hands.size == 1
    assert chamber._cards[1].size == 1
    assert chamber._cards[2].size == 1
    # checking HandPointerNodes pointing to correct HandNode
    assert chamber._cards[1].nodeat(0).value is chamber._hands.nodeat(0)
    assert chamber._cards[2].nodeat(0).value is chamber._hands.nodeat(0)
    # checking HandNodes storing correct HandPointerNodes
    assert chamber._hands.nodeat(0).value[0] is chamber._cards[1].nodeat(0)
    assert chamber._hands.nodeat(0).value[1] is chamber._cards[2].nodeat(0)

    chamber.add_hand([2, 3])
    assert chamber._hands.size == 2
    assert chamber._cards[1].size == 1
    assert chamber._cards[2].size == 2
    assert chamber._cards[3].size == 1
    assert chamber._cards[1].nodeat(0).value is chamber._hands.nodeat(0)
    assert chamber._cards[2].nodeat(0).value is chamber._hands.nodeat(0)
    assert chamber._cards[2].nodeat(1).value is chamber._hands.nodeat(1)
    assert chamber._cards[3].nodeat(0).value is chamber._hands.nodeat(1)
    assert chamber._hands.nodeat(0).value[0] is chamber._cards[1].nodeat(0)
    assert chamber._hands.nodeat(0).value[1] is chamber._cards[2].nodeat(0)
    assert chamber._hands.nodeat(1).value[0] is chamber._cards[2].nodeat(1)
    assert chamber._hands.nodeat(1).value[1] is chamber._cards[3].nodeat(0)
    # check multiple HandPointerNodes
    assert chamber._cards[2].nodeat(0) is chamber._cards[2].nodeat(1).prev
    assert chamber._cards[2].nodeat(0).next is chamber._cards[2].nodeat(1)

    # card check
    with pytest.raises(CardNotInChamberError):
        chamber.add_hand([13, 14])

    # order assertion
    with pytest.raises(AssertionError, match=r"be ordered"):
        chamber.add_hand([2, 1])

    # length assertion
    with pytest.raises(AssertionError, match=r"2-5 cards"):
        chamber.add_hand([1])

    with pytest.raises(AssertionError, match=r"2-5 cards"):
        chamber.add_hand([1, 2, 3, 4, 5, 6])

    # validity assertion
    with pytest.raises(AssertionError, match=r"valid hands"):
        chamber.add_hand([1, 5])

    # dupe hand assertion
    with pytest.raises(AssertionError, match=r"hand is"):
        chamber.add_hand([1, 2])

    # deselecting cards in hand
    chamber.select_cards([3, 4])
    assert chamber.hand == Hand([3, 4])
    chamber.add_hand(chamber.hand)
    assert chamber.hand.is_empty


def test_select_card():
    ...