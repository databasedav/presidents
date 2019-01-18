from __future__ import annotations
import eventlet
eventlet.monkey_patch()
try:
    from .utils.utils import main
except ImportError:
    from utils.utils import main
from flask import request, copy_current_request_context
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room

from typing import Dict, Tuple


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)#, logger=True)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template('index.html')


room_game_dict: Dict[str, EmittingGame] = dict()

for room in ['hello', 'world']:
    try:
        from .emitting_game import EmittingGame
    except ImportError:
        from emitting_game import EmittingGame
    game = EmittingGame()
    game.set_room(room)
    room_game_dict[room] = game

sid_room_dict: Dict[str, str] = dict()

sid_game_dict: Dict[str, EmittingGame] = dict()


def get_sid() -> str:
    return request.sid


def room_list():
    return [{'room': room, 'num_players': game.num_players} for room, game in room_game_dict.items()]


@socketio.on('refresh')
def refresh():
    emit('refresh', {'rooms': room_list()}, room=get_sid())


def get_game_from_room(room: str) -> EmittingGame:
    return room_game_dict[room]


def get_room(sid: str) -> str:
    return sid_room_dict[sid]


def get_game_spot_from_sid(sid: str) -> Tuple[EmittingGame, int]:
    room: str = get_room(sid)
    game: EmittingGame = get_game_from_room(room)
    # TODO: check that sid is a player and not a spectator
    spot: int = game._get_spot(sid)
    return game, spot


def get_game_from_sid(sid: str) -> EmittingGame:
    return get_game_from_room(sid_room_dict[sid])


def get_sid_and_game() -> Tuple[str, EmittingGame]:
    return (lambda sid: (sid, get_game_from_sid(sid)))(get_sid())


@socketio.on('connect')
def connect():
    print(f'{get_sid()} connected.')


@socketio.on('disconnect')
def disconnect():
    sid = get_sid()
    print(f'{sid} disconnected.')
    try:  # if in a game simply nuke the game TODO do not simply nuke the game
        del sid_game_dict[sid]
        room = sid_room_dict[sid]
        leave_room(room, sid)
        send_non_leavers_back_to_browser(sid, room)
        room_game_dict[room] = EmittingGame()
    except KeyError:
        pass


def send_non_leavers_back_to_browser(sid: str, room: str) -> None:
    emit('send_to_path', {'path': '/room_browser'}, room=room, include_self=False)


@socketio.on('join_room')
def join_room_as_player(payload) -> None:
    sid = get_sid()
    room = payload['room']
    name = payload['name']
    join_room(room, sid)
    sid_room_dict[sid] = room
    game: EmittingGame = get_game_from_room(room)
    sid_game_dict[sid] = game
    emit('send_to_path', {'path': '/presidents'}, room=sid)
    game.add_player(sid, name)
    # TODO: this shouldn't be here ?
    if game.num_players == 4:
        game._start_round(testing=True)
        # game.get_game_to_trading()


@socketio.on('create_room')
def add_room(payload):
    sid = get_sid()
    room = payload['room']
    if room in room_game_dict:
        emit('set_room_dne', {'room_dne': False}, room=sid)
        return
    else:
        if len(room_game_dict) >= 10:
            remove_room(room_with_least_players())
        game = EmittingGame()
        room_game_dict[room] = game
        refresh()


def remove_room(room: str) -> None:
    emit('send_to_path', {'path': '/room_browser'}, room=room)
    close_room(room)
    del room_game_dict[room]


def room_with_least_players() -> str:
    return sorted(room_list(), key=lambda obj: obj['num_players'])[0]['room']


@socketio.on('card_click')
def card_click(payload):
    (lambda sid: sid_game_dict[sid].add_or_remove_card(sid, payload['card']))(get_sid())


@socketio.on('unlock')
def unlock():
    (lambda sid: sid_game_dict[sid].unlock_handler(sid))(get_sid())


@socketio.on('lock')
def lock():
    (lambda sid: sid_game_dict[sid].lock_handler(sid))(get_sid())


@socketio.on('play')
def play():
    (lambda sid: sid_game_dict[sid].maybe_play_current_hand(sid))(get_sid())


@socketio.on('unlock_pass')
def unlock_pass():
    (lambda sid: sid_game_dict[sid].maybe_unlock_pass_turn(sid))(get_sid())


@socketio.on('pass')
def pass_turn():
    (lambda sid: sid_game_dict[sid].maybe_pass_turn(sid))(get_sid())


@socketio.on('asking_click')
def select_asking_option(payload):
    (lambda sid: sid_game_dict[sid].set_selected_asking_option(sid, payload['value']))(get_sid())


@socketio.on('ask')
def ask():
    (lambda sid: sid_game_dict[sid].ask_for_card(sid))(get_sid())


@socketio.on('give')
def give():
    (lambda sid: sid_game_dict[sid].give_card(sid))(get_sid())


@main
def main():
    socketio.run(app, host='0.0.0.0')
