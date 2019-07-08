from ..game.game import Game, PresidentsError, base_hand
import numpy as np
import pytest

def test_constructor():
    game: Game = Game()
    assert game.num_players == 0
    assert game._num_consecutive_rounds == 0
    assert game._open_spots == {0, 1, 2, 3}
    assert game._turn_manager is None
    assert game._current_player is None
    assert all(chamber.is_empty for chamber in game._chambers)
    assert game._hand_in_play is base_hand
    assert game._num_consecutive_passes == 0
    assert game._winning_last_played == False
    assert game._positions == []
    assert all(unlocked == False for unlocked in game._unlocked)
    assert all(pass_unlocked == False for pass_unlocked in game._pass_unlocked)
    assert all(unlocked == False for unlocked in game._pass_unlocked)
    assert all(timer is None for timer in game._timers)
    assert game.trading == False
    assert all(option is None for option in game._selected_asking_option)
    assert all(waiting == False for waiting in game._waiting)
    assert all(aa == set() for aa in game._already_asked)
    assert all(takes == 0 for takes in game._takes_remaining)
    assert all(gives == 0 for gives in game._gives_remaining)
    assert all(given == set() for given in game._given)
    assert all(taken == set() for taken in game._taken)


def test_is_empty():
    game: Game = Game()
    assert game.is_empty
    game.add_player('player0')
    assert not game.is_empty


def test_is_full():
    game: Game = Game()
    assert game.is_empty
    assert not game.is_full
    game.add_player('player0')
    assert not game.is_full
    game.add_player('player1')
    game.add_player('player2')
    game.add_player('player3')
    assert game.is_full


# quick way to have game setup with exactly the stuff
# that i want to test; will there be any conflicting settings?

def test_num_unfinished_players():
    game: Game = Game()
    game._set_up_testing_base()
    assert game._num_unfinished_players == 4
    game._player_finish(0)
    assert game._num_unfinished_players == 3
    for i in range(1, 4):
        game._player_finish(i)
    assert game._num_unfinished_players == 0


def test_no_takes_or_gives_remaining():
    game: Game = Game()
    assert game._no_takes_or_gives_remaining
    game._set_up_testing_base()
    game._get_game_to_trading()
    assert not game._no_takes_or_gives_remaining


def test_set_up_testing_base():
    game: Game = Game()
    assert game.is_empty
    assert all(chamber.is_empty for chamber in game._chambers)
    assert game._num_consecutive_rounds == 0
    assert game._current_player is None
    game._set_up_testing_base()
    assert game.is_full
    assert all(chamber.num_cards == 13 for chamber in game._chambers)
    assert game._num_consecutive_rounds == 1
    assert game._current_player is not None

    with pytest.raises(AssertionError, match=r'set up testing'):
        game = Game()
        game.add_player('player0')
        game._set_up_testing_base()


def test_get_game_to_trading():
    game: Game = Game()
    game._set_up_testing_base()
    assert not game.trading
    game._get_game_to_trading()
    assert game.trading


def test_rand_open_spot():
    game: Game = Game()
    seen = set()
    # v low prob that these tests fail by chance
    for _ in range(100):
        seen.add(game._rand_open_spot(no_remove=True))
        if len(seen) == 4:
            break
    assert len(seen) == 4
    seen.clear()
    game.add_player('player0')
    for _ in range(100):
        seen.add(game._rand_open_spot(no_remove=True))
        if len(seen) == 3:
            break
    assert len(seen) == 3
    seen.clear()
    game.add_player('player0')
    for _ in range(100):
        seen.add(game._rand_open_spot(no_remove=True))
        if len(seen) == 2:
            break
    assert len(seen) == 2
    seen.clear()
    game.add_player('player0')
    for _ in range(100):
        seen.add(game._rand_open_spot(no_remove=True))
        if len(seen) == 1:
            break
    assert len(seen) == 1


def test_add_player():
    game: Game = Game()
    assert any(name is None for name in game._names)
    assert game.num_players == 0
    game.add_player('player0')
    assert any(name is not None for name in game._names)
    assert game.num_players == 1
    game.add_player('player1')
    assert sum([name is not None for name in game._names])
    assert game.num_players == 2


def test_add_player_to_spot():
    game: Game = Game()
    assert any(name is None for name in game._names)
    assert game.num_players == 0
    game.add_player_to_spot('player0', 0)
    assert game._names[0] == 'player0'
    assert game.num_players == 1

    with pytest.raises(AssertionError, match=r'already in'):
        game.add_player_to_spot('player01', 0)


def test_remove_player():
    game: Game = Game()
    game.add_player_to_spot('player0', 0)
    assert game._names[0] == 'player0'
    assert game.num_players == 1
    game.remove_player(0)
    assert game._names[0] is None
    assert game.num_players == 0


def test_make_shuffled_deck():
    game: Game = Game()
    # v low prob that entire deck is shuffled to numeric order
    assert any(game._make_shuffled_deck().flatten() != np.arange(1, 53))


def test_deal_cards():
    game: Game = Game()
    assert all(chamber.is_empty for chamber in game._chambers)
    game._deal_cards()
    assert all(chamber.num_cards == 13 for chamber in game._chambers)


def test_make_and_set_turn_manager():
    game: Game = Game()
    game._deal_cards()
    assert game._turn_manager is None
    game._make_and_set_turn_manager()
    assert game._turn_manager is not None
    assert 1 in game._chambers[next(game._turn_manager)]


def test_start_round():
    game: Game = Game()
    for i in range(4):
        game.add_player(f'player{i}')
    game._start_round()
    assert all(chamber.num_cards == 13 for chamber in game._chambers)
    assert game._turn_manager is not None
    assert game._num_consecutive_round == 1
    assert 1 in game._chambers[game._current_player]
    
    with pytest.raises(AssertionError, match=r'four players'):
        game = Game()
        game._start_round()


def test_next_player():
    game: Game = Game()
