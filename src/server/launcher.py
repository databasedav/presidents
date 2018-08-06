from flask import Flask
from flask_socketio import SocketIO, emit
import numpy as np
from hand import Hand, DuplicateCardError, FullHandError
from chamber import Chamber
import eventlet
from json import dumps

eventlet.monkey_patch()
    
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

hand = Hand()
chamber = Chamber()


@socketio.on('deal cards')
def deal_cards():
    # deck = np.arange(1, 53)
    # np.random.shuffle(deck)
    # decks = deck.reshape(4, 13)
    # decks.sort(axis=1)
    deck = np.arange(1, 14)
    hand.reset()
    chamber.reset()
    chamber.add_cards(deck)
    emit('update_current_hand_desc', {'desc': hand.id_desc})
    # the following emit can be used to load saved states (e.g. when the dom has been modified)
    # emit('set_cards_with_selection', {'cards': [{'value': card, 'is_selected': is_selected} for (card, is_selected) in zip(decks[0].tolist(), np.full(13, False).tolist())]})


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
        chamber.select_card(card)
    # TODO: should I just pass the error message through no matter the problem?
    #       what is the point of having these separate errors?
    except DuplicateCardError:
        hand.remove(card)
        chamber.deselect_card(card)
        # card_hand_chamber.deselect_card(card)
    except FullHandError:
        # alert_current_hand_full()
        # TODO: why do i need the line below
        # client_update_current_hand(hand)  # TODO: this one doesn't require changing the session
        return
    except Exception as e:
        # print("Bug: probably the card hand chamber freaking out.")
        raise e
    finally:
        emit('update_current_hand_desc', {'desc': hand.id_desc})


@socketio.on('hand click')
def select_hand(payload):
    print(payload['cards'])
    for card in payload['cards']:
        card_click({'card': card})


@socketio.on('store current hand')
def store_current_hand():
    chamber.add_hand(hand)
    hand.reset()
    emit('update_current_hand_desc', {'desc': hand.id_desc})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
