import numpy as np
import pickle


from itertools import combinations as comb
from typing import Dict
from .utils import hand_hash, cartesian_product_pp, main


cards = np.arange(1, 53, dtype=np.uint8)
suits = cards.reshape(13, 4)


# hash table for identifying combos
hand_table: Dict[int, int] = {}


def _save_hand_table() -> None:
    with open('hand_table.pkl', 'wb') as file:
        pickle.dump(hand_table, file, pickle.HIGHEST_PROTOCOL)


def _add_to_hand_table(hand, id: int) -> None:
    hh = hand_hash(hand)
    if hh in hand_table:
        print('nope')
    hand_table[hh] = id


def _add_to_hand_table_iter(hands, id: int) -> None:
    for hand in hands:
        _add_to_hand_table(hand, id)


def _add_all() -> None:
    _add_singles()
    _add_doubles()
    _add_triples()
    _add_fullhouses()
    _add_straights()
    _add_bombs()


def _add_singles() -> None:
    """
    adds all singles to the hand hash table
    """
    singles = np.zeros(shape=(52, 5), dtype=np.uint8)
    singles[:, 4] = range(1, 53)
    _add_to_hand_table_iter(singles, 11)


def _add_doubles() -> None:
    """
    adds all doubles to the hand hash table
    """
    doubles = np.zeros(shape=(6, 5), dtype=np.uint8)  # (4 C 2) = 6
    for suit in suits:
        doubles[:, 3:5] = list(comb(suit, 2))
        _add_to_hand_table_iter(doubles, 21)


def _add_triples() -> None:
    """
    adds all triples to the hand hash table
    """
    triples = np.zeros(shape=(4, 5), dtype=np.uint8)  # (4 C 3) = 4
    for suit in suits:
        triples[:, 2:5] = list(comb(suit, 3))
        _add_to_hand_table_iter(triples, 31)


def _add_fullhouses() -> None:
    """
    adds all fullhouses to the hand hash table
    """
    fullhouses = np.zeros(shape=(6, 5), dtype=np.uint8)
    for suit1, suit2 in comb(suits, 2):
        # double triples, e.g. [1, 2, 50, 51, 52]
        doubles = list(comb(suit1, 2))
        triples = comb(suit2, 3)
        fullhouses[:, 0:2] = doubles
        for triple in triples:
            fullhouses[:, 2:5] = triple  # numpy array broadcasting
            _add_to_hand_table_iter(fullhouses, 51)

        # triple doubles, e.g. [1, 2, 3, 51, 52]
        triples = comb(suit1, 3)
        doubles = list(comb(suit2, 2))
        fullhouses[:, 3:5] = doubles
        for triple in triples:
            fullhouses[:, 0:3] = triple  # numpy array broadcasting
            _add_to_hand_table_iter(fullhouses, 51)


def _add_straights() -> None:
    """
    adds all straights to the hand hash table
    """
    for i in range(9):
        group_of_5_suits = suits[i: i + 5]
        straights = cartesian_product_pp(group_of_5_suits)
        _add_to_hand_table_iter(straights, 52)


def _add_bombs() -> None:
    """
    adds all bombs to the hand hash table
    """
    bombs = np.zeros(shape=(4, 5), dtype=np.uint8)
    for suit1, suit2 in comb(suits, 2):
        # single quads, e.g. [1, 49, 50, 51, 52]
        bombs[:, 0] = suit1
        bombs[:, 1:5] = suit2  # numpy array broadcasting
        _add_to_hand_table_iter(bombs, 53)

        # quad singles, e.g. [1, 2, 3, 4, 52]
        bombs[:, 0:4] = suit1  # numpy array broadcasting
        bombs[:, 4] = suit2
        _add_to_hand_table_iter(bombs, 53)


@main
def generate():
    _add_all()
    _save_hand_table()
