from __future__ import annotations

from typing import Dict, Tuple
from flask import request, Flask
from flask_socketio import emit, join_room, leave_room, close_room

from .. import socketio
from ..components import EmittingGame

room_game_dict: Dict[str, EmittingGame] = dict()

for room in ['hello', 'world']:
    game = EmittingGame()
    game.set_room(room)
    room_game_dict[room] = game

sid_room_dict: Dict[str, str] = dict()

sid_game_dict: Dict[str, EmittingGame] = dict()

# server = Server


def room_list():
    return [{'room': room, 'num_players': game.num_players} for room, game in room_game_dict.items()]


@socketio.on('refresh')
def refresh():
    emit('refresh', {'rooms': room_list()}, room=request.sid)


@socketio.on('connect')
def connect():
    print(f'{request.sid} connected.')


@socketio.on('disconnect')
def disconnect():
    sid = request.sid
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
    sid = request.sid
    room = payload['room']
    name = payload['name']
    join_room(room, sid)
    sid_room_dict[sid] = room
    game: EmittingGame = room_game_dict[room]
    sid_game_dict[sid] = game
    emit('send_to_path', {'path': '/presidents'}, room=sid)
    game.add_player(sid, name)
    # TODO: this shouldn't be here ?
    if game.num_players == 4:
        game._start_round(testing=False)
        # game.get_game_to_trading()


@socketio.on('create_room')
def add_room(payload):
    room = payload['room']
    if room in room_game_dict:
        emit('set_room_dne', {'room_dne': False}, room=request.sid)
        return
    else:
        if len(room_game_dict) >= 10:
            remove_room(room_with_least_players())
        room_game_dict[room] = EmittingGame()
        refresh()


def remove_room(room: str) -> None:
    emit('send_to_path', {'path': '/room_browser'}, room=room)
    close_room(room)
    del room_game_dict[room]


def room_with_least_players() -> str:
    return sorted(room_list(), key=lambda obj: obj['num_players'])[0]['room']


@socketio.on('card_click')
def card_click(payload):
    (lambda sid: sid_game_dict[sid].add_or_remove_card(sid, payload['card']))(request.sid)


@socketio.on('unlock')
def unlock():
    (lambda sid: sid_game_dict[sid].unlock_handler(sid))(request.sid)


@socketio.on('lock')
def lock():
    (lambda sid: sid_game_dict[sid].lock_handler(sid))(request.sid)


@socketio.on('play')
def play():
    (lambda sid: sid_game_dict[sid].maybe_play_current_hand(sid))(request.sid)


@socketio.on('unlock_pass')
def unlock_pass():
    (lambda sid: sid_game_dict[sid].maybe_unlock_pass_turn(sid))(request.sid)


@socketio.on('pass')
def pass_turn():
    (lambda sid: sid_game_dict[sid].maybe_pass_turn(sid))(request.sid)


@socketio.on('asking_click')
def select_asking_option(payload):
    (lambda sid: sid_game_dict[sid].set_selected_asking_option(sid, payload['value']))(request.sid)


@socketio.on('ask')
def ask():
    (lambda sid: sid_game_dict[sid].ask_for_card(sid))(request.sid)


@socketio.on('give')
def give():
    (lambda sid: sid_game_dict[sid].give_card(sid))(request.sid)
