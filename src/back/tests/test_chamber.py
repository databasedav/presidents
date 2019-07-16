from ..game.chamber import (
    Chamber,
    CardAlreadyInChamberError,
    CardNotInChamberError,
    Hand,
    HandPointerDLList,
    HandPointerNode,
    HandNodeDLList,
    HandNode,
)
from ..game.hand import CardNotInHandError, DuplicateCardError, FullHandError
from ..game.utils import IterNodesDLList
import pytest


def test_cardless_constructor():
    chamber: Chamber = Chamber()
    assert chamber.hand.is_empty
    assert chamber.is_empty
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
    assert chamber.is_empty
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
    # without hands
    chamber: Chamber = Chamber(range(1, 14))
    assert chamber.hand.is_empty
    chamber.select_card(1)
    assert chamber.hand == Hand([1])

    # one hand
    chamber = Chamber(range(1, 14))
    assert chamber.hand.is_empty
    chamber.add_hand([1, 2])
    chamber.select_card(1)
    assert chamber.hand == Hand([1])
    assert chamber._hands.nodeat(0)._num_cards_selected == 1
    chamber.select_card(2)
    assert chamber.hand == Hand([1, 2])
    assert chamber._hands.nodeat(0)._num_cards_selected == 2

    # two hands
    chamber = Chamber(range(1, 14))
    assert chamber.hand.is_empty
    chamber.add_hand([1, 2])
    chamber.add_hand([2, 3])
    chamber.select_card(1)
    assert chamber.hand == Hand([1])
    assert chamber._hands.nodeat(0)._num_cards_selected == 1
    chamber.select_card(2)
    assert chamber.hand == Hand([1, 2])
    assert chamber._hands.nodeat(0)._num_cards_selected == 2
    assert chamber._hands.nodeat(1)._num_cards_selected == 1
    chamber.select_card(3)
    assert chamber.hand == Hand([1, 2, 3])
    assert chamber._hands.nodeat(1)._num_cards_selected == 2

    # card check
    with pytest.raises(CardNotInChamberError):
        chamber.select_card(14)

    # dupe card error
    with pytest.raises(DuplicateCardError):
        chamber.select_card(1)

    # full hand error
    with pytest.raises(FullHandError):
        chamber.select_card(4)
        chamber.select_card(5)
        chamber.select_card(6)


def test_select_cards():
    # without hands
    chamber: Chamber = Chamber(range(1, 14))
    assert chamber.hand.is_empty
    chamber.select_cards([1, 2])
    assert chamber.hand == Hand([1, 2])

    # one hand
    chamber = Chamber(range(1, 14))
    assert chamber.hand.is_empty
    chamber.add_hand([1, 2])
    chamber.select_cards([1, 2])
    assert chamber.hand == Hand([1, 2])
    assert chamber._hands.nodeat(0)._num_cards_selected == 2

    # two hands
    chamber = Chamber(range(1, 14))
    assert chamber.hand.is_empty
    chamber.add_hand([1, 2])
    chamber.add_hand([2, 3])
    chamber.select_cards([1, 2, 3])
    assert chamber.hand == Hand([1, 2, 3])
    assert chamber._hands.nodeat(0)._num_cards_selected == 2
    assert chamber._hands.nodeat(1)._num_cards_selected == 2

    # card check
    with pytest.raises(CardNotInChamberError):
        chamber.select_cards([14, 15])

    # does not select any card unless all cards are in chamber
    with pytest.raises(CardNotInChamberError):
        chamber.select_cards([4, 14])
    assert 4 not in chamber.hand

    # dupe card assertion
    with pytest.raises(AssertionError, match=r"bad select"):
        chamber.select_cards([1, 2])

    # still selects individual cards if they are good
    with pytest.raises(AssertionError, match=r"bad select"):
        chamber.select_cards([4, 1])
    assert chamber.hand == Hand([1, 2, 3, 4])

    # full hand assertion; still selects individual cards if they are
    # good
    with pytest.raises(AssertionError, match=r"bad select"):
        chamber.select_cards([5, 6])
    assert chamber.hand == Hand([1, 2, 3, 4, 5])


def test_deselect_card():
    # without hands
    chamber: Chamber = Chamber(range(1, 14))
    assert chamber.hand.is_empty
    chamber.select_card(1)
    assert chamber.hand == Hand([1])
    chamber.deselect_card(1)
    assert chamber.hand.is_empty

    # one hand
    chamber: Chamber = Chamber(range(1, 14))
    assert chamber.hand.is_empty
    chamber.add_hand([1, 2])
    chamber.select_card(1)
    assert chamber.hand == Hand([1])
    assert chamber._hands.nodeat(0)._num_cards_selected == 1
    chamber.deselect_card(1)
    assert chamber.hand.is_empty
    assert chamber._hands.nodeat(0)._num_cards_selected == 0
    chamber.select_card(1)
    chamber.select_card(2)
    assert chamber.hand == Hand([1, 2])
    assert chamber._hands.nodeat(0)._num_cards_selected == 2
    chamber.deselect_card(1)
    assert chamber._hands.nodeat(0)._num_cards_selected == 1
    chamber.deselect_card(2)
    assert chamber._hands.nodeat(0)._num_cards_selected == 0

    # two hands
    chamber: Chamber = Chamber(range(1, 14))
    assert chamber.hand.is_empty
    chamber.add_hand([1, 2])
    chamber.add_hand([2, 3])
    chamber.select_card(1)
    assert chamber.hand == Hand([1])
    assert chamber._hands.nodeat(0)._num_cards_selected == 1
    chamber.select_card(2)
    assert chamber.hand == Hand([1, 2])
    assert chamber._hands.nodeat(0)._num_cards_selected == 2
    assert chamber._hands.nodeat(1)._num_cards_selected == 1
    chamber.deselect_card(2)
    assert chamber.hand == Hand([1])
    assert chamber._hands.nodeat(0)._num_cards_selected == 1
    assert chamber._hands.nodeat(1)._num_cards_selected == 0
    chamber.select_card(2)
    chamber.select_card(3)
    assert chamber.hand == Hand([1, 2, 3])
    assert chamber._hands.nodeat(0)._num_cards_selected == 2
    assert chamber._hands.nodeat(0)._num_cards_selected == 2
    chamber.deselect_card(2)
    assert chamber._hands.nodeat(0)._num_cards_selected == 1
    assert chamber._hands.nodeat(0)._num_cards_selected == 1

    # card check
    with pytest.raises(CardNotInChamberError):
        chamber.deselect_card(14)

    # not in hand error
    with pytest.raises(CardNotInHandError):
        chamber.deselect_card(4)


def test_deselect_cards():
    # without hands
    chamber: Chamber = Chamber(range(1, 14))
    assert chamber.hand.is_empty
    chamber.select_cards([1, 2])
    assert chamber.hand == Hand([1, 2])
    chamber.deselect_cards([1, 2])
    assert chamber.hand.is_empty

    # one hand
    chamber: Chamber = Chamber(range(1, 14))
    assert chamber.hand.is_empty
    chamber.add_hand([1, 2])
    chamber.select_cards([1, 2])
    assert chamber.hand == Hand([1, 2])
    assert chamber._hands.nodeat(0)._num_cards_selected == 2
    chamber.deselect_cards([1, 2])
    assert chamber.hand.is_empty
    assert chamber._hands.nodeat(0)._num_cards_selected == 0

    # two hands
    chamber: Chamber = Chamber(range(1, 14))
    assert chamber.hand.is_empty
    chamber.add_hand([1, 2])
    chamber.add_hand([2, 3])
    chamber.select_cards([1, 2, 3])
    assert chamber.hand == Hand([1, 2, 3])
    assert chamber._hands.nodeat(0)._num_cards_selected == 2
    assert chamber._hands.nodeat(1)._num_cards_selected == 2
    chamber.deselect_cards([1, 3])
    assert chamber.hand == Hand([2])
    assert chamber._hands.nodeat(0)._num_cards_selected == 1
    assert chamber._hands.nodeat(1)._num_cards_selected == 1

    # card check
    with pytest.raises(CardNotInChamberError):
        chamber.deselect_card(14)

    # not in hand assertion
    with pytest.raises(AssertionError, match=r"bad deselect"):
        chamber.deselect_cards([1, 3])

    # still deselects individual cards if they are good
    assert chamber.hand == Hand([2])
    chamber.select_cards([1, 3])
    assert chamber.hand == Hand([1, 2, 3])
    with pytest.raises(AssertionError, match=r"bad deselect"):
        chamber.deselect_cards([2, 3, 4])
    assert chamber.hand == Hand([1])


def test_deselect_selected():
    chamber: Chamber = Chamber(range(1, 14))
    assert chamber.hand.is_empty
    chamber.select_cards([1, 2])
    assert chamber.hand == Hand([1, 2])
    chamber.deselect_selected()
    assert chamber.hand.is_empty
    chamber.select_cards([1, 2, 3, 4, 5])
    assert chamber.hand == Hand([1, 2, 3, 4, 5])
    chamber.deselect_selected()
    assert chamber.hand.is_empty


def test_clear_hands():
    chamber: Chamber = Chamber(range(1, 14))
    chamber.add_hand([1, 2])
    chamber.add_hand([1, 3])
    assert chamber._cards[1].size == 2
    assert chamber._cards[2].size == 1
    assert chamber._cards[3].size == 1
    assert chamber._hands.size == 2
    chamber.clear_hands()
    assert chamber._cards[1].size == 0
    assert chamber._cards[2].size == 0
    assert chamber._cards[3].size == 0
    assert chamber._hands.size == 0


def test_check_card_in():
    chamber: Chamber = Chamber(range(1, 14))
    assert chamber._check_card_in(1) is None
    with pytest.raises(CardNotInChamberError):
        chamber._check_card_in(14)


def test_check_cards_in():
    chamber: Chamber = Chamber(range(1, 14))
    assert chamber._check_cards_in([1, 2]) is None
    with pytest.raises(CardNotInChamberError):
        chamber._check_cards_in([1, 14])


def test_check_card_not_in():
    chamber: Chamber = Chamber(range(1, 14))
    assert chamber._check_card_not_in(14) is None
    with pytest.raises(CardAlreadyInChamberError):
        chamber._check_card_not_in(1)


def test_check_cards_not_in():
    chamber: Chamber = Chamber(range(1, 14))
    assert chamber._check_cards_not_in([14, 15]) is None
    with pytest.raises(CardAlreadyInChamberError):
        chamber._check_cards_not_in([14, 1])


def test_get_min_card():
    chamber: Chamber = Chamber(range(1, 14))
    assert 1 in chamber
    assert chamber._get_min_card() == 1
    chamber.remove_card(1)
    assert 2 in chamber
    assert chamber._get_min_card() == 2


def test_get_max_card():
    chamber: Chamber = Chamber(range(1, 14))
    assert 13 in chamber
    assert chamber._get_max_card() == 13
    chamber.remove_card(13)
    assert 12 in chamber
    assert chamber._get_max_card() == 12


def test_IterNodesDLList_iter_nodes():
    iter_nodes_dllist: IterNodesDLList = IterNodesDLList([1, 2, 3])
    assert all(
        i + 1 == node.value
        for i, node in enumerate(iter_nodes_dllist.iter_nodes())
    )


def test_HandPointerDLList_constructor():
    hand_pointer_dllist: HandPointerDLList = HandPointerDLList(1)
    assert hand_pointer_dllist.size == 0
    assert hand_pointer_dllist.card == 1


def test_HandPointerNode_constructor():
    hand_pointer_nodes = list()
    hand_node: HandNode = HandNode(hand_pointer_nodes)
    hand_pointer_node: HandPointerNode = HandPointerNode(hand_node)
    assert isinstance(hand_pointer_node.value, HandNode)


def test_HandNode():
    hand_pointer_nodes = list()
    hand_node: HandNode = HandNode(hand_pointer_nodes)
    hand_pointer_nodes.extend(
        [HandPointerNode(HandNode), HandPointerNode(HandNode)]
    )
    assert hand_node.value is hand_pointer_nodes
    assert hand_node._num_cards_selected == 0

    hand_node.increment_num_selected_cards()
    assert hand_node._num_cards_selected == 1
    hand_node.decrement_num_selected_cards()
    assert hand_node._num_cards_selected == 0
