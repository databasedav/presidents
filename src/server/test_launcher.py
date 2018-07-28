from flask import Flask
from flask_socketio import SocketIO, emit
from hand import Hand
    
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

hand = Hand()

@socketio.on('add_card')
def add_card(card):
    hand.add(card)
    print(hand)
    emit('hey', {'spot': 0, 'desc': hand.id_desc})

if __name__ == '__main__':
    socketio.run(app, debug=True)