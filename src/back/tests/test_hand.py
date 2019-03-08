from ..app.components import Hand
from numpy.testing import assert_array_equal

def test_default_constructor():
    hand: Hand = Hand()
    assert_array_equal(hand._cards, np.zeros(shape=5, dtype=np.uint8))
    