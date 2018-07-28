from hand import Hand, DuplicateCardError, FullHandError
from card_hand_chamber import CardHandChamber
from hand_list import HandList
from flask import request, session, redirect, url_for
from flask_socketio import emit, join_room, leave_room
from .. import socketio
from typing import Dict, List, Generator
from itertools import cycle
import numpy as np
from random import shuffle
from bidict import bidict

# TODO: get rid of all the ".get"s
# TODO: figure out how the imports are working lol
# TODO: how to organize helper functions--maybe a different file entirely?
# TODO: move client updates up as early as possible
# TODO: generally clean the fuck out of this plz wow
# TODO: is this the "server"?
# TODO: encapsulate all the below in a Game class?
# TODO: make sure only socket events access the session or request?
# TODO: order functions
# TODO: it looks like broadcast false is equivalent to room player sid
# TODO: server should tell current player "it's your turn!"
# TODO: add support for a player leaving and then rejoining (spots)
# TODO: add typing
# TODO: fix next player announcement coming before position announcement
# TODO: add turn order
# TODO: add number of cards remaining
# TODO: fix prepending cards
# TODO: when passing hands around when it is safe to pass the main
#       current hand (which is cleared afterwards) or requiring a copy

# TODO: where to put these
current_hand_dict: Dict[str, Hand] = dict()
# TODO: should not be a dict from sid so another player can take over
card_hand_chamber_dict: Dict[str, CardHandChamber] = dict()
hand_in_play_dict: Dict[str, Hand] = dict()
player_sids_dict: Dict[str, List[str]] = dict()
player_cycler_dict: Dict[str, Generator[str, None, None]] = dict()
current_player_dict: Dict[str, str] = dict()
finished_player_sids_dict: Dict[str, List[str]] = dict()
num_unfinished_players_dict: Dict[str, int] = dict()
consecutive_passes_dict: Dict[str, int] = dict()
names_dict: Dict[str, str] = dict()
positions_dict: Dict[str, bidict] = dict()
currently_trading_dict: Dict[str, bool] = dict()
takes_remaining_dict: Dict[str, int] = dict()
gives_remaining_dict: Dict[str, int] = dict()
winning_last_dict: Dict[str, bool] = dict()

# this is from number of unfinished players to position
position_dict: Dict[int, str] = {
    1: 'asshole',
    2: 'vice asshole',
    3: 'vice president',
    4: 'president'
}


def get_room() -> str:
    return session['room']


def get_name() -> str:
    return session['name']


def get_sid() -> str:
    return request.sid


def get_current_hand(player_sid):
    return current_hand_dict[player_sid]


def get_card_hand_chamber(player_sid):
    return card_hand_chamber_dict[player_sid]


def get_hand_in_play(room):
    return hand_in_play_dict[room]


@socketio.on('text', namespace='/presidents')
def text(message):
    room = get_room()
    name = get_name()
    emit('message', {'msg': f"{name}: {message['msg']}"}, room=room)


@socketio.on('joined', namespace='/presidents')
def joined(message):
    room = get_room()
    name = get_name()
    player_sid = get_sid()
    join_room(room)
    add_player(room, name, player_sid)
    emit('status', {'msg': f"{name}" + ' has entered the room.'}, room=room)
    if len(player_sids_dict[room]) == 4:
        start_game(room)


def add_player(room, name, player_sid):
    names_dict[player_sid] = name
    player_sids = player_sids_dict[room] = player_sids_dict.get(room, list())
    player_sids.append(player_sid)
    current_hand_dict[player_sid] = Hand()


# TODO: don't really like this but like wut do
class Start:  # for playing the 3 of clubs on 
    pass
Start = Start()


def start_game(room):
    deal_cards_and_establish_turn_order(room)
    hand_in_play_dict[room] = Start
    positions_dict[room] = bidict()
    finished_player_sids_dict[room] = list()
    num_unfinished_players_dict[room] = 4
    consecutive_passes_dict[room] = 0
    currently_trading_dict[room] = False
    winning_last_dict[room] = False


def deal_cards_and_establish_turn_order(room):
    deck = np.arange(1, 53)
    np.random.shuffle(deck)
    decks = deck.reshape(4, 13)
    decks.sort(axis=1)  # sorts each deck
    c3_index = np.where(decks == 1)[0][0]  # which deck has the 3 of clubs
    player_cycler = player_cycler_dict[room] = turn_generator(room, c3_index)
    current_player_dict[room] = next(player_cycler)
    for player_sid, deck in zip(player_sids_dict[room], decks):
        emit('assign cards', {'cards': deck.tolist()}, room=player_sid)
        card_hand_chamber_dict[player_sid] = CardHandChamber(deck, player_sid)


def turn_generator(room, starting_player_index):
    player_cycle = cycle(player_sids_dict[room])
    # iterates to the current player
    for _ in range(starting_player_index):
        next(player_cycle)
    yield from player_cycle


def next_player(room, hand_won=False):
    player_cycler = player_cycler_dict[room]
    current_player = next(player_cycler)
    finished_player_sids = finished_player_sids_dict[room]
    while current_player in finished_player_sids:
        current_player = next(player_cycler)
    current_player_dict[room] = current_player
    name = names_dict[current_player]
    if hand_won:
        message_hand_won(room, name)
    emit('message', {'msg': f"SERVER: it's {name}'s turn!"}, room=room)


@socketio.on('play current hand', namespace='/presidents')
def maybe_play_current_hand():
    room = get_room()
    if currently_trading_dict[room]:
        alert_trading_ongoing()
        return
    name = get_name()
    player_sid = get_sid()
    if player_sid != current_player_dict[room]:
        alert_can_only_play_on_turn()
        return
    hand = get_current_hand(player_sid)
    if not hand.is_valid:
        alert_playing_invalid_hand()
        return
    hand_in_play = hand_in_play_dict[room]
    if hand_in_play is Start:  # hand must contain the 3 of clubs
        if 1 not in hand:
            alert_3_of_clubs()
            return
        else:
            play_hand(hand, room, player_sid, name)
    elif hand_in_play is None:
        play_hand(hand, room, player_sid, name)
    else:
        try:
            if hand > hand_in_play:
                play_hand(hand, room, player_sid, name)
            else:
                alert_weaker_hand()
        except RuntimeError as e:
            emit('alert', {'alert': str(e)}, broadcast=False)


def play_hand(hand: Hand, room: str, player_sid: str, name: str):
    hand_copy = Hand.copy(hand)
    hand_in_play_dict[room] = hand_copy
    client_update_hand_in_play(hand_copy, room)
    message_hand_played(hand_copy, room, name)
    card_hand_chamber = get_card_hand_chamber(player_sid)
    client_clear_current_hand(player_sid)
    winning_last_dict[room] = False
    # TODO: put this in a function called server clear current hand or something
    for card in hand_copy:
        card_hand_chamber.remove_card(card)
    consecutive_passes_dict[room] = 0
    next_player(room)


def client_update_hand_in_play(hand, room):
    emit('hand in play', {'hand': str(hand)}, room=room)


@socketio.on('player finish', namespace='/presidents')
def player_finish():
    room = get_room()
    name = get_name()
    player_sid = get_sid()
    finished_player_sids_dict[room].append(player_sid)
    num_unfinished_players = num_unfinished_players_dict[room]
    positions_dict[room].put(player_sid, 5 - num_unfinished_players)
    if num_unfinished_players == 4:
        takes_remaining_dict[player_sid] = 2
        gives_remaining_dict[player_sid] = 2
    elif num_unfinished_players == 3:
        takes_remaining_dict[player_sid] = 1
        gives_remaining_dict[player_sid] = 1
    winning_last_dict[room] = True
    message_player_finished(room, name, position_dict[num_unfinished_players])
    decrement_unfinished_players(room, name)


def decrement_unfinished_players(room, name):
    num_unfinished_players_dict[room] -= 1
    num_unfinished_players = num_unfinished_players_dict[room]
    if num_unfinished_players == 1:
        # TODO: this is terrible
        for player_sid in player_sids_dict[room]:
            if player_sid not in finished_player_sids_dict[room]:
                positions_dict[room].put(player_sid, 5 - num_unfinished_players)
                break
        message_player_finished(room, names_dict[player_sid], position_dict[1])
        end_game_due_diligence(room)


def end_game_due_diligence(room):
    # TODO: functionize this; it is currently a frankenstein's monster
    emit('clear hand in play', room=room)
    emit('clear current hands', room=room)
    emit('clear stored hands', room=room)
    emit('clear cards', room=room)
    hand_in_play_dict[room] = Start
    finished_player_sids_dict[room] = list()
    num_unfinished_players_dict[room] = 4
    consecutive_passes_dict[room] = 0
    winning_last_dict[room] = False
    deck = np.arange(1, 53)
    np.random.shuffle(deck)
    decks = deck.reshape(4, 13)
    decks.sort(axis=1)  # sorts each deck
    shuffle(player_sids_dict[room])
    for player_sid, deck in zip(player_sids_dict[room], decks):
        emit('assign cards', {'cards': deck.tolist()}, room=player_sid)
        card_hand_chamber_dict[player_sid] = CardHandChamber(deck, player_sid)
    message_round_over_trading_begins(room)
    initiate_trading(room)


def initiate_trading(room: str):
    positions_bidict = positions_dict[room]
    for player_sid in player_sids_dict[room]:
        if positions_bidict[player_sid] in [1, 2]:
            client_add_trading_options(player_sid)
            client_add_give_card_button(player_sid)
    currently_trading_dict[room] = True


def end_trading_and_remove_trading_buttons_and_start_game(room: str):
    currently_trading_dict[room] = False
    client_remove_trading_options(room)
    client_remove_give_card_button(room)
    decks = list()
    # rebuild deck after trading has concluded
    for player_sid in player_sids_dict[room]:
        card_hand_chamber = card_hand_chamber_dict[player_sid]
        deck = list()
        for card in card_hand_chamber.iter_cards():
            deck.append(card)
        decks.append(deck)
    decks = np.array(decks)
    c3_index = np.where(decks == 1)[0][0]  # which deck has the 3 of clubs
    player_cycler = player_cycler_dict[room] = turn_generator(room, c3_index)
    current_player_dict[room] = next(player_cycler)
    positions_dict[room] = bidict()
    message_trading_concluded(room)


def client_add_trading_options(player_sid: str):
    emit('add trading options', room=player_sid)


def client_remove_trading_options(room: str):
    emit('remove trading options', room=room)


# TODO: implement for a confirmation for asking
def client_add_ask_for_card_button(player_sid: str):
    ...


# TODO: currently doesn't ask just takes the minimum matching
@socketio.on('ask for card', namespace='/presidents')
def ask_for_card(data):
    room = get_room()
    asker = get_sid()
    if takes_remaining_dict[asker] == 0:
        alert_no_more_takes()
        return
    position_bidict = positions_dict[room]
    asker_position = position_bidict[asker]
    asked = position_bidict.inv[5 - asker_position]
    card_hand_chamber_asker = card_hand_chamber_dict[asker]
    card_hand_chamber_asked = card_hand_chamber_dict[asked]
    card_value = data['value']
    for card in range((card_value - 1) * 4 + 1, card_value * 4 + 1):
        if card_hand_chamber_asked.contains_card(card):
            card_hand_chamber_asked.remove_card(card)
            card_hand_chamber_asker.add_card(card)
            takes_remaining_dict[asker] -= 1
            if finished_taking_and_giving(asker) and finished_taking_and_giving(position_bidict.inv[other_winner(asker_position)]):
                end_trading_and_remove_trading_buttons_and_start_game(room)
            return
    alert_other_player_does_not_have_value()


def finished_taking_and_giving(player_sid: str):
    return takes_remaining_dict[player_sid] == 0 and gives_remaining_dict[player_sid] == 0


def other_winner(position):
    return 3 - position


def client_add_give_card_button(player_sid: str):
    emit('add give card button', room=player_sid)


def client_remove_give_card_button(room: str):
    emit('remove give card button', room=room)


@socketio.on('give current card', namespace='/presidents')
def give_current_card():
    room = get_room()
    giver = get_sid()
    if gives_remaining_dict[giver] == 0:
        alert_no_more_gives()
        return
    hand = current_hand_dict[giver]
    if not hand.is_single:
        alert_can_only_give_singles()
        return
    position_bidict = positions_dict[room]
    giver_position = position_bidict[giver]
    givee = position_bidict.inv[5 - giver_position]
    card_hand_chamber_giver = card_hand_chamber_dict[giver]
    card_hand_chamber_givee = card_hand_chamber_dict[givee]
    for card in hand:  # happens only once
        client_clear_current_hand(giver)
        card_hand_chamber_giver.remove_card(card)
        card_hand_chamber_givee.add_card(card)
        gives_remaining_dict[giver] -= 1
        if finished_taking_and_giving(giver) and finished_taking_and_giving(position_bidict.inv[other_winner(giver_position)]):
            end_trading_and_remove_trading_buttons_and_start_game(room)
        return

@socketio.on('card click', namespace='/presidents')
def singles_click(data):
    player_sid = get_sid()
    hand = get_current_hand(player_sid)
    card_hand_chamber = get_card_hand_chamber(player_sid)
    # TODO: should I do the conversion in python or javascript (even possible?)
    card = int(data['card'])
    add_or_remove_card(card, hand, card_hand_chamber)
    client_update_current_hand(hand, player_sid)


@socketio.on('hand click', namespace='/presidents')
def hand_click(data):
    player_sid = get_sid()
    hand = get_current_hand(player_sid)
    card_hand_chamber = get_card_hand_chamber(player_sid)
    cards = data['cards']
    client_clear_current_hand(player_sid)
    for card in cards:
        add_or_remove_card(card, hand, card_hand_chamber)
    client_update_current_hand(hand, player_sid)


def add_or_remove_card(card: int, hand: Hand, card_hand_chamber: CardHandChamber):
    # here, we attempt to add a card that has just been clicked:
    #   if the card is not in the current hand, it is added
    #   else, it is remove
    # particular order is to hopefully minimize exceptions but should be
    # verified empirically TODO
    try:
        hand.add(card)
        card_hand_chamber.select_card(card)
    # TODO: should I just pass the error message through no matter the problem?
    #       what is the point of having these separate errors?
    except DuplicateCardError:
        hand.remove(card)
        card_hand_chamber.deselect_card(card)
    except FullHandError:
        alert_current_hand_full()
        # TODO: why do i need the line below
        # client_update_current_hand(hand)  # TODO: this one doesn't require changing the session
        return
    except Exception as e:
        print("Bug: probably the card hand chamber freaking out.")
        raise e


@socketio.on('clear current hand', namespace='/presidents')
def clear_current_hand():
    player_sid = get_sid()
    client_clear_current_hand(player_sid)
    alert_current_hand_cleared()


def client_clear_current_hand(player_sid):
    hand = current_hand_dict[player_sid]
    if hand.is_empty:
        return
    card_hand_chamber = get_card_hand_chamber(player_sid)
    for card in hand:
        card_hand_chamber.deselect_card(card)
    hand.reset()
    emit('clear current hand', room=player_sid)


@socketio.on('pass current hand', namespace='/presidents')
def pass_current_hand():
    """
    handles passing
    """
    room = get_room()
    if currently_trading_dict[room]:
        alert_trading_ongoing()
        return
    name = get_name()
    player_sid = get_sid()
    if player_sid != current_player_dict[room]:
        alert_can_only_pass_on_turn()
        return
    hand_in_play = get_hand_in_play(room)
    if hand_in_play is Start:
        alert_must_play_3_of_clubs()
        return
    if hand_in_play is None:
        alert_can_play_any_hand()
        return
    consecutive_passes_dict[room] += 1
    message_passed(room, name)
    num_unfinished_players = num_unfinished_players_dict[room]
    consecutive_passes = consecutive_passes_dict[room]
    if winning_last_dict[room]:
        if consecutive_passes == num_unfinished_players:
            hand_in_play_dict[room] = None
            client_clear_hand_in_play(room)
            message_default_next_player(room)
            next_player(room)
            return
    elif consecutive_passes == num_unfinished_players - 1:
        next_player(room, hand_won=True)
        hand_in_play_dict[room] = None
        client_clear_hand_in_play(room)
        return
    next_player(room)


def client_clear_hand_in_play(room):
    emit('clear hand in play', room=room)


@socketio.on('store', namespace='/presidents')
def store():
    """
    stores currently selected cards in a hand
    """
    player_sid = get_sid()
    hand = Hand.copy(get_current_hand(player_sid))
    if not hand.is_valid:
        alert_invalid_hand_storage()
        return
    elif hand.is_single:
        alert_single_storage()
        return
    card_hand_chamber = get_card_hand_chamber(player_sid)
    if card_hand_chamber.contains_hand(hand):
        alert_hand_already_stored()
        return
    client_clear_current_hand(player_sid)
    card_hand_chamber.add_hand(hand)


@socketio.on('clear stored hands', namespace='/presidents')
def clear_stored_hands():
    player_sid = get_sid()
    card_hand_chamber_dict[player_sid].clear_hands()


@socketio.on('left', namespace='/presidents')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    leave_room(room)
    players.remove(request.sid)
    emit('status', {'msg': session.get('name') + ' has left the room.'}, room=room)


def client_update_current_hand(hand, player_sid):
    if hand.is_empty:
        clear_display()
        return
    else:
        emit('update current hand', {'hand': str(hand)}, room=player_sid)


def clear_display():
    emit('clear display')


def alert_current_hand_cleared():
    emit('alert', {'alert': 'Current hand cleared.'}, broadcast=False)


def alert_stored_hands_cleared():
    emit('alert', {'alert': 'Stored hands cleared.'}, broadcast=False)


def alert_current_hand_full():
    emit('alert', {'alert': 'You cannot add any more cards to this hand.'}, broadcast=False)


def alert_invalid_hand_storage():
    emit('alert', {'alert': 'You can only store valid hands.'}, broadcast=False)


def alert_single_storage():
    emit('alert', {'alert': 'You cannot store singles; play them directly!'}, broadcast=False)


def alert_playing_invalid_hand():
    emit('alert', {'alert': 'You can only play valid hands.'}, broadcast=False)


def alert_3_of_clubs():
    emit('alert', {'alert': 'The first hand must contain the 3 of clubs.'}, broadcast=False)


def alert_weaker_hand():
    emit('alert', {'alert': 'This hand is weaker than the hand in play.'}, broadcast=False)


def alert_can_only_play_on_turn():
    emit('alert', {'alert': 'You can only play hands on your turn.'}, broadcast=False)


def alert_can_only_pass_on_turn():
    emit('alert', {'alert': 'You can only pass on your turn.'}, broadcast=False)


def alert_can_play_any_hand():
    emit('alert', {'alert': 'You can play any hand!'}, broadcast=False)


def alert_must_play_3_of_clubs():
    emit('alert', {'alert': 'You must play a hand containing the 3 of clubs.'}, broadcast=False)


def alert_hand_already_stored():
    emit('alert', {'alert': 'This hand is already stored.'}, broadcast=False)


def alert_trading_ongoing():
    emit('alert', {'alert': 'Trading has not concluded.'}, broadcast=False)


def alert_no_more_takes():
    emit('alert', {'alert': 'You have no more takes remaining.'}, broadcast=False)


def alert_no_more_gives():
    emit('alert', {'alert': 'You have no more gives remaining.'}, broadcast=False)


def alert_other_player_does_not_have_value():
    emit('alert', {'alert': 'The other player does not have a card of that value.'}, broadcast=False)


def alert_can_only_give_singles():
    emit('alert', {'alert': 'You can only give singles.'}, broadcast=False)


def message_hand_played(hand, room, name):
    emit('message', {'msg': f"SERVER: {name} played {str(hand)}!"}, room=room)


def message_passed(room, name):
    emit('message', {'msg': f"SERVER: {name} passed!"}, room=room)


def message_hand_won(room, name):
    emit('message', {'msg': f"SERVER: {name} won the hand! They can play any hand!"}, room=room)


def message_player_finished(room, name, position):
    emit('message', {'msg': f"SERVER: {name} is {position}!"}, room=room)


def message_trading_concluded(room):
    emit('message', {'msg': f"SERVER: Trading has concluded! The next round starts now!"}, room=room)


def message_default_next_player(room):
    emit('message', {'msg': f"SERVER: Everyone passed on a winning hand. The next player can play anything!"}, room=room)


def message_round_over_trading_begins(room):
    emit('message', {'msg': f"SERVER: The round is over! Trading starts now!"}, room=room)
