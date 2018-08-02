from flask import Flask
from flask_socketio import SocketIO, emit
import numpy as np
from hand import Hand, DuplicateCardError, FullHandError
    
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
    emit('set_is_selected_arr', {'arr': list(map(list, map(list, np.full((4, 13), False))))})
    emit('set_all_cards', {list(map(list, map(list, deck)))})

@socketio.on('add card')
def add_card(payload):
    card = payload['card']
    hand.add(card)
    emit('update_current_hand', {'spot': 0, 'hand': list(map(int, hand))})
    emit('update_hand_desc', {'spot': 0, 'desc': hand.id_desc})

@socketio.on('remove card')
def remove_card(payload):
    card = payload['card']
    hand.remove(card)
    emit('update_current_hand', {'spot': 0, 'hand': list(map(int, hand))})
    emit('update_hand_desc', {'spot': 0, 'desc': hand.id_desc})

@socketio.on('card click')
def card_click(payload):
    card = payload['card']
    # here, we attempt to add a card that has just been clicked:
    #   if the card is not in the current hand, it is added
    #   else, it is remove
    # particular order is to hopefully minimize exceptions but should be
    # verified empirically TODO
    try:
        hand.add(card)
        # card_hand_chamber.select_card(card)
    # TODO: should I just pass the error message through no matter the problem?
    #       what is the point of having these separate errors?
    except DuplicateCardError:
        hand.remove(card)
        # card_hand_chamber.deselect_card(card)
    except FullHandError:
        # alert_current_hand_full()
        # TODO: why do i need the line below
        # client_update_current_hand(hand)  # TODO: this one doesn't require changing the session
        return
    except Exception as e:
        # print("Bug: probably the card hand chamber freaking out.")
        raise e
    emit('update_hand_desc', {'spot': 0, 'desc': hand.id_desc})

@socketio.on('add_card')
def add_card(card):
    hand.add(card)
    print(hand)
    emit('update_hand_desc', {'spot': 0, 'desc': hand.id_desc})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)