from flask import Flask
from flask_socketio import SocketIO, emit
import numpy as np
from hand import Hand
    
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

hand = Hand()

@socketio.on('deal cards')
def deal_cards():
    deck = np.arange(1, 53)
    np.random.shuffle(deck)
    decks = deck.reshape(4, 13)
    decks.sort(axis=1)
    emit('deal_cards', {'spot': 0, 'cards': list(map(int, decks[0]))})

@socketio.on('clear current hand')
def clear_current_hand():
    pass

@socketio.on('add_card')
def add_card(card):
    hand.add(card)
    print(hand)
    emit('update_hand_desc', {'spot': 0, 'desc': hand.id_desc})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)