import eventlet
# eventlet.monkey_patch()
try:
    from .emitting_game import EmittingGame
    from .utils.utils import main
except ImportError:
    from emitting_game import EmittingGame
    from utils.utils import main
from flask import request
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room

from typing import Dict, Tuple


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template('index.html')


room_game_dict: Dict[str, EmittingGame] = dict()

for room in ['fuck', 'shit']:
    game = EmittingGame()
    game.set_room(room)
    room_game_dict[room] = game

sid_room_dict: Dict[str, str] = dict()


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


@socketio.on('connect')
def connect():
    print(f'{get_sid()} connected.')
#     refresh()
#     room = 'fuck'
#     join_room_as_player(sid, room)


@socketio.on('disconnect')
def disconnect():
    sid = get_sid()
    print(f'{sid} disconnected.')
    try:  # if in a game simply nuke the game TODO do not simply nuke the game
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
    game.add_player(sid, name)
    # emit('join_room', room=sid)

    # TODO: this shouldn't be here
    if game.num_players == 4:
        game._start_round(testing=False)
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
    game, spot = get_game_spot_from_sid(get_sid())
    card = payload['card']
    game.add_or_remove_card(spot, card)


@socketio.on('unlock')
def unlock():
    game, spot = get_game_spot_from_sid(get_sid())
    # TODO: let the game take care of this
    if game.trading:
        if game.is_asking(spot):
            game.maybe_unlock_ask(spot)
        elif game.is_giving(spot):
            game.maybe_unlock_give(spot)
    else:
        game.maybe_unlock_play(spot)


@socketio.on('lock')
def lock():
    game, spot = get_game_spot_from_sid(get_sid())
    game.lock(spot)


@socketio.on('play')
def play():
    game, spot = get_game_spot_from_sid(get_sid())
    game.maybe_play_current_hand(spot)


@socketio.on('pass')
def pass_turn():
    game, spot = get_game_spot_from_sid(get_sid())
    game.pass_turn(spot)


@socketio.on('asking_click')
def select_asking_option(payload):
    game, spot = get_game_spot_from_sid(get_sid())
    value = payload['value']
    game.update_selected_asking_option(spot, value)


@socketio.on('ask')
def ask():
    game, spot = get_game_spot_from_sid(get_sid())
    game.ask_for_card(spot)


@socketio.on('give')
def give():
    game, spot = get_game_spot_from_sid(get_sid())
    game.give_card(spot)


@main
def main():
    socketio.run(app, host='0.0.0.0', debug=True)
