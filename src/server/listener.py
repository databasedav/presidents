import eventlet
# eventlet.monkey_patch()
from json import dumps
from game import Game
from flask import request, session
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
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

# should deal with room list separately from games because
# games are modular but rooms should persist
room = 'room'
rooms = [room]

game = Game()
game.set_room(room)

def get_sid() -> str:
    return request.sid

def join_game(sid):
    game.add_player(sid, sid)

@socketio.on('connect')
def connect():
    sid = get_sid()
    join_room(room, sid)
    join_game(sid)
    print(f'{sid} connected.')
    if game.num_players == 4:
        game._start_round()
        game.get_game_to_trading()

@socketio.on('list servers')
def list_servers():
    ...

@socketio.on('attempt to join game')
def attempt_to_join_game(payload):
    sid = get_sid()
    room = payload['room']

# @socketio.on('join game')
# def join_game(sid):
#     sid = get_sid()
#     try:
#         game.add_player(sid, 'fuck')
#     except AssertionError:
#         game.restart

@socketio.on('card_click')
def card_click(payload):
    sid = get_sid()
    card = payload['card']
    game.add_or_remove_card(sid, card)

@socketio.on('unlock')
def unlock():
    sid = get_sid()
    # TODO: let the game take care of this
    if game.trading:
        if game.is_asking(sid):
            game.maybe_unlock_ask(sid)
        elif game.is_giving(sid):
            game.maybe_unlock_give(sid)
    else:
        game.maybe_unlock_play(sid)

@socketio.on('lock')
def lock():
    sid = get_sid()
    game.lock(sid)

@socketio.on('play')
def play():
    sid = get_sid()
    game.maybe_play_current_hand(sid)

@socketio.on('pass')
def pass_turn():
    sid = get_sid()
    game.maybe_pass_turn(sid)

@socketio.on('restart')
def restart():
    game.restart()

@socketio.on('asking_click')
def select_asking_option(payload):
    sid = get_sid()
    value = payload['value']
    game.update_selected_asking_option(sid, value)

@socketio.on('ask')
def ask():
    sid = get_sid()
    game.ask_for_card(sid)

@socketio.on('give')
def give():
    sid = get_sid()
    game.give_card(sid)

@main
def main():
    socketio.run(app, host='0.0.0.0', debug=True)
