from ..game.chamber import (
    Chamber,
    CardAlreadyInChamberError,
    CardNotInChamberError,
    Hand,
)
import numpy as np
from numpy.testing import assert_array_equal
from ..game.chamber import HandPointerDLList, HandNodeDLList
import pytest


def test_cardless_constructor():
    chamber: Chamber = Chamber()
    assert chamber.hand.is_empty
    assert chamber.num_cards == 0
    assert_array_equal(chamber._cards, np.array([None] * 53))


def test_cardful_constructor():
    chamber: Chamber = Chamber(range(1, 14))
    for card in range(1, 14):
        assert isinstance(chamber._cards[card], HandPointerDLList)
        assert chamber._cards[card].size == 0
    for card in range(15, 53):
        assert chamber._cards[card] is None
    assert chamber.num_cards == 13
    assert isinstance(chamber._hands, HandNodeDLList)
    assert chamber._hands.size == 0


def test__contains__():
    chamber: Chamber = Chamber()
    assert all([card not in chamber for card in range(1, 53)])
    chamber = Chamber(range(1, 14))
    assert all([card in chamber for card in range(1, 14)])
    assert all([card not in chamber for card in range(15, 53)])


def test__iter__():
    chamber: Chamber = Chamber()
    assert not list(chamber)
    chamber = Chamber(range(1, 14))
    assert list(chamber)
    assert all([i+1 == card for i, card in enumerate(chamber)])


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
    assert any([chamber._cards[card] is not None for card in range(1, 53)])
    assert chamber.num_cards > 0
    assert chamber._hands.size > 0
    chamber.reset()
    assert chamber.hand.is_empty
    assert all([chamber._cards[card] is None for card in range(1, 53)])
    assert chamber.num_cards == 0
    assert chamber._hands.size == 0


def test_add_card():
    chamber: Chamber = Chamber()
    chamber.add_card(1)
    assert isinstance(chamber._cards[1], HandPointerDLList)
    assert chamber.num_cards == 1

    # test check
    with pytest.raises(CardAlreadyInChamberError, match=r'already in'):
        chamber.add_card(1)


def test_add_cards():
    chamber: Chamber = Chamber()
    chamber.add_cards(range(1, 14))
    assert all([isinstance(chamber._cards[card], HandPointerDLList) for card in range(1, 14)])
    assert chamber.num_cards == 13

    # test check
    with pytest.raises(CardAlreadyInChamberError, match=r'already in'):
        chamber.add_cards([1, 2])

    # does not add any card unless all cards are not already in chamber
    with pytest.raises(CardAlreadyInChamberError, match=r'already in'):
        chamber.add_cards([14, 1])
    assert chamber._cards[14] is None
