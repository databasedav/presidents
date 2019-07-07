from ..game.Game import Game, PresidentsError, base_hand

def test_constructor():
    game: Game = Game()
    assert game.num_players == 0
    assert game._num_consecutive_rounds == 0
    assert game._open_spots == {0, 1, 2, 3}
    assert game._turn_manager is None
    assert game._current_player is None
    assert all(chamber is None for chamber in game._chambers)
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
    assert all(aa == {} for aa in game._already_asked)
    assert all(takes == 0 for takes in game._takes_remaining)
    assert all(gives == 0 for gives in game._gives_remaining)
    assert all(given == {} for given in game._given)
    assert all(taken == {} for taken in game._taken)


def test_is_full():
    game: Game = Game()
    assert not game.is_full
    game.add_player('player0')
    assert not game.is_full
    game.add_player('player1')
    game.add_player('player2')
    game.add_player('player3')
    assert game.is_full


# quick way to have game setup with exactly the stuff
# that i want to test; will there be any conflicting settings?



