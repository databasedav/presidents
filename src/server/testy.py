from chamber import *
from hand import Hand
import numpy as np
import flask
from flask_socketio import SocketIO, SocketIOTestClient

a = Chamber(debug=True)
a.add_cards(np.arange(1, 14))
h1 = Hand([1,2,3,4,5])
h2 = Hand([6,7,8,9,10])
a.add_hand(h1)
a.add_hand(h2)
