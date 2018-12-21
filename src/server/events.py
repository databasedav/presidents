import eventlet
# eventlet.monkey_patch()
from json import dumps
from game import Game
from flask import request, session
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import numpy as np
from hand import Hand, DuplicateCardError, FullHandError
from chamber import Chamber
from utils.utils import main


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template('index.html')

game = Game()

def get_sid() -> str:
    return request.sid

@socketio.on('connect')
def connect():
    sid = get_sid()
    game.add_player(sid, 'fuck')
    print(f'{sid} connected.')
    if game.num_players == 4:
        game._start_round()

@socketio.on('list servers')
def list_servers():
    ...

@socketio.on('attempt to join game')
def attempt_to_join_game(payload):
    sid = get_sid()
    room = payload['room']

@socketio.on('join game')
def join_game():
    sid = get_sid()
    game.add_player(sid, 'fuck')
    game.start_game()

@socketio.on('card click')
def card_click(payload):
    sid = get_sid()
    card = payload['card']
    game.add_or_remove_card(sid, card)

@socketio.on('restart')
def restart():
    game.restart()

@main
def main():
    socketio.run(app, host='0.0.0.0', debug=True)
