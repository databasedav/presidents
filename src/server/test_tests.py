from chamber import *
from hand import Hand
import numpy as np

a = Chamber(np.arange(1, 14))
b = Hand(np.array([0, 0, 0, 1, 2]))
c = Hand(np.array([0, 0, 0, 2, 3]))
a.add_hand(b)
a.add_hand(c)
