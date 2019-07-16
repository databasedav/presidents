from ..game.game import Game, PresidentsError, base_hand, NoopTimer
import numpy as np
import pytest
from eventlet import greenthread
from eventlet.greenthread import GreenThread
import time
from ..game.hand import Hand


def test_constructor():
    game: Game = Game()
    # instance related attributes
    assert isinstance(game.id, str)
    assert game.num_players == 0
    assert game._num_consecutive_rounds == 0
    assert game._times_reset == 0
    # timer related attributes
    assert callable(game._timer)
    assert all(timer is None for timer in game._timers)
    assert game._turn_time is None
    assert game._reserve_time == 0
    assert all(reserve_time == 0 for reserve_time in game._reserve_times)
    assert all(
        reserve_time_use_start is None
        for reserve_time_use_start in game._reserve_time_use_starts
    )
    # setup and ID related attributes
    assert game._open_spots == {0, 1, 2, 3}
    assert all(name is None for name in game._names)
    # game related attributes
    assert game._turn_manager is None
    assert game._current_player is None
    assert all(chamber.is_empty for chamber in game._chambers)
    assert game._hand_in_play is base_hand
    assert game._num_consecutive_passes == 0
    assert game._winning_last_played == False
    assert game._positions == []
    assert all(unlocked == False for unlocked in game._unlocked)
    assert all(pass_unlocked == False for pass_unlocked in game._pass_unlocked)
    # trading related attributes
    assert game.trading == False
    assert all(option is None for option in game._selected_asking_option)
    assert all(aa == set() for aa in game._already_asked)
    assert all(waiting == False for waiting in game._waiting)
    assert all(takes == 0 for takes in game._takes_remaining)
    assert all(gives == 0 for gives in game._gives_remaining)
    assert all(given == set() for given in game._given)
    assert all(taken == set() for taken in game._taken)


def test_reset():
    game: Game = Game()
    game._set_up_testing_base()
    # TODO auto get to a point where there's at least something not its
    #      default
    # assert something isn't its default for all the game's attributes
    game_id = game.id
    game.reset()
    # instance related attributes
    assert game.id == game_id  # id doesn't change
    assert isinstance(game.id, str)
    assert game.num_players == 0
    assert game._num_consecutive_rounds == 0
    assert game._times_reset == 1
    # timer related attributes
    assert game._timer == NoopTimer.timer  # classmethods aren't is
    assert all(timer is None for timer in game._timers)
    assert game._turn_time is None
    assert game._reserve_time == 0
    assert all(reserve_time == 0 for reserve_time in game._reserve_times)
    assert all(
        reserve_time_use_start is None
        for reserve_time_use_start in game._reserve_time_use_starts
    )
    # setup and ID related attributes
    assert game._open_spots == {0, 1, 2, 3}
    assert all(name is None for name in game._names)
    # game related attributes
    assert game._turn_manager is None
    assert game._current_player is None
    assert all(chamber.is_empty for chamber in game._chambers)
    assert game._hand_in_play is base_hand
    assert game._num_consecutive_passes == 0
    assert game._winning_last_played == False
    assert game._positions == []
    assert all(unlocked == False for unlocked in game._unlocked)
    assert all(pass_unlocked == False for pass_unlocked in game._pass_unlocked)
    # trading related attributes
    assert game.trading == False
    assert all(option is None for option in game._selected_asking_option)
    assert all(aa == set() for aa in game._already_asked)
    assert all(waiting == False for waiting in game._waiting)
    assert all(takes == 0 for takes in game._takes_remaining)
    assert all(gives == 0 for gives in game._gives_remaining)
    assert all(given == set() for given in game._given)
    assert all(taken == set() for taken in game._taken)

    game: Game = Game(
        timer=greenthread.spawn_after,
        turn_time=0.01,
        reserve_time=0.05
    )
    game._set_up_testing_base()
    # TODO auto get to a point where there's at least something not its
    #      default
    # assert something isn't its default for all the game's attributes
    game_id = game.id
    game.reset()
    # instance related attributes
    assert game.id == game_id  # id doesn't change
    assert isinstance(game.id, str)
    assert game.num_players == 0
    assert game._num_consecutive_rounds == 0
    assert game._times_reset == 1
    # timer related attributes
    assert game._timer == greenthread.spawn_after
    assert all(timer is None for timer in game._timers)
    assert game._turn_time == 0.01
    assert game._reserve_time == 0.05
    assert all(reserve_time == 0.05 for reserve_time in game._reserve_times)
    assert all(
        reserve_time_use_start is None
        for reserve_time_use_start in game._reserve_time_use_starts
    )
    # setup and ID related attributes
    assert game._open_spots == {0, 1, 2, 3}
    assert all(name is None for name in game._names)
    # game related attributes
    assert game._turn_manager is None
    assert game._current_player is None
    assert all(chamber.is_empty for chamber in game._chambers)
    assert game._hand_in_play is base_hand
    assert game._num_consecutive_passes == 0
    assert game._winning_last_played == False
    assert game._positions == []
    assert all(unlocked == False for unlocked in game._unlocked)
    assert all(pass_unlocked == False for pass_unlocked in game._pass_unlocked)
    # trading related attributes
    assert game.trading == False
    assert all(option is None for option in game._selected_asking_option)
    assert all(aa == set() for aa in game._already_asked)
    assert all(waiting == False for waiting in game._waiting)
    assert all(takes == 0 for takes in game._takes_remaining)
    assert all(gives == 0 for gives in game._gives_remaining)
    assert all(given == set() for given in game._given)
    assert all(taken == set() for taken in game._taken)


def test_is_empty():
    game: Game = Game()
    assert game.is_empty
    game.add_player("player0")
    assert not game.is_empty


def test_is_full():
    game: Game = Game()
    assert game.is_empty
    assert not game.is_full
    game.add_player("player0")
    assert not game.is_full
    game.add_player("player1")
    game.add_player("player2")
    game.add_player("player3")
    assert game.is_full


def test_num_unfinished_players():
    game: Game = Game()
    game._set_up_testing_base()
    assert game._num_unfinished_players == 4
    game._current_player = 0
    game._chambers[0].reset()
    game._hand_in_play = Hand([1])
    game._player_finish(0)
    assert game._num_unfinished_players == 3
    
    game._current_player = 1
    game._chambers[1].reset()
    game._player_finish(1)
    assert game._num_unfinished_players == 2

    game._current_player = 2
    game._chambers[2].reset()
    game._player_finish(2)
    assert game._num_unfinished_players == 1


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

    with pytest.raises(AssertionError, match=r"set up testing"):
        game = Game()
        game.add_player("player0")
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
    game.add_player("player0")
    for _ in range(100):
        seen.add(game._rand_open_spot(no_remove=True))
        if len(seen) == 3:
            break
    assert len(seen) == 3
    seen.clear()
    game.add_player("player0")
    for _ in range(100):
        seen.add(game._rand_open_spot(no_remove=True))
        if len(seen) == 2:
            break
    assert len(seen) == 2
    seen.clear()
    game.add_player("player0")
    for _ in range(100):
        seen.add(game._rand_open_spot(no_remove=True))
        if len(seen) == 1:
            break
    assert len(seen) == 1


def test_add_player():
    game: Game = Game()
    assert any(name is None for name in game._names)
    assert game.num_players == 0
    game.add_player("player0")
    assert any(name is not None for name in game._names)
    assert game.num_players == 1
    game.add_player("player1")
    assert sum([name is not None for name in game._names])
    assert game.num_players == 2


def test_add_player_to_spot():
    game: Game = Game()
    assert any(name is None for name in game._names)
    assert game.num_players == 0
    game.add_player_to_spot("player0", 0)
    assert game._names[0] == "player0"
    assert game.num_players == 1

    with pytest.raises(AssertionError, match=r"already in"):
        game.add_player_to_spot("player01", 0)


def test_remove_player():
    game: Game = Game()
    game.add_player_to_spot("player0", 0)
    assert game._names[0] == "player0"
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
        game.add_player(f"player{i}")
    game._start_round()
    assert all(chamber.num_cards == 13 for chamber in game._chambers)
    assert game._turn_manager is not None
    assert game._num_consecutive_rounds == 1
    assert 1 in game._chambers[game._current_player]

    with pytest.raises(AssertionError, match=r"four players"):
        game = Game()
        game._start_round()


def test_next_player():
    game: Game = Game()
    game._set_up_testing_base()
    assert 1 in game._chambers[game._current_player]
    game._next_player()
    assert 1 not in game._chambers[game._current_player]


def test_start_timer():
    game: Game = Game()
    game._start_timer(0, 0.01)
    assert isinstance(game._timers[0], NoopTimer)

    # 5 second turn_time is arbitrary; just needs to exist till assert
    game = Game(timer=greenthread.spawn_after, turn_time=0.01)
    game._start_timer(0, game._turn_time)
    assert isinstance(game._timers[0], GreenThread)


def test_handle_timeout():
    # note this doesn't actually test the functionality of the timer
    game: Game = Game(timer=greenthread.spawn_after, turn_time=10)

    # has reserve time
    game._set_up_testing_base()
    start_spot = game._current_player
    game._reserve_times[start_spot] = 10
    assert game._hand_in_play is base_hand
    timer = game._timers[start_spot]
    assert isinstance(timer, GreenThread)
    assert game._reserve_time_use_starts[start_spot] is None
    game._handle_timeout(start_spot)  # should just start reserve time
    assert game._hand_in_play is base_hand
    game._timers[start_spot] is not timer
    assert isinstance(game._timers[start_spot], GreenThread)
    assert game._reserve_time_use_starts[start_spot] is not None
    assert game._reserve_times[start_spot] == 0

    # 0 reserve time
    game._reserve_times[start_spot] = 0
    game._handle_timeout(start_spot)  # should auto play 3 of clubs
    assert game._current_player != start_spot
    assert game._hand_in_play == Hand([1])
    assert game._timers[start_spot] is None
    assert game._reserve_time_use_starts[start_spot] is None
    assert isinstance(game._timers[game._current_player], GreenThread)


def test_auto_play_or_pass():
    game: Game = Game(timer=greenthread.spawn_after, turn_time=10)
    game._set_up_testing_base()
    
    # play 3 of clubs
    start_spot: int = game._current_player
    assert isinstance(game._timers[start_spot], GreenThread)
    assert game._hand_in_play is base_hand
    game._auto_play_or_pass(start_spot)
    assert start_spot != game._current_player
    assert game._hand_in_play == Hand([1])
    
    # pass
    start_spot = game._current_player
    assert isinstance(game._timers[start_spot], GreenThread)
    assert game._hand_in_play == Hand([1])
    game._auto_play_or_pass(start_spot)
    assert start_spot != game._current_player
    assert game._hand_in_play == Hand([1])
    # pass
    start_spot = game._current_player
    assert isinstance(game._timers[start_spot], GreenThread)
    assert game._hand_in_play == Hand([1])
    game._auto_play_or_pass(start_spot)
    assert start_spot != game._current_player
    assert game._hand_in_play == Hand([1])
    # pass
    start_spot = game._current_player
    assert isinstance(game._timers[start_spot], GreenThread)
    assert game._hand_in_play == Hand([1])
    game._auto_play_or_pass(start_spot)
    assert start_spot != game._current_player
    assert game._hand_in_play is None
    
    # can play anyhand so play min single
    start_spot = game._current_player
    min_card: int = game._chambers[start_spot]._get_min_card()
    assert game._hand_in_play is None
    game._auto_play_or_pass(start_spot)
    assert start_spot != game._current_player
    assert game._hand_in_play == Hand([min_card])
    
    # selected cards should remain selected after auto play or pass
    # if passing
    other_min_card = min_card
    start_spot = game._current_player
    min_card = game._chambers[start_spot]._get_min_card()
    max_card: int = game._chambers[start_spot]._get_max_card()
    game.add_or_remove_card(start_spot, min_card)
    game.add_or_remove_card(start_spot, max_card)
    assert game._chambers[start_spot].hand == Hand([min_card, max_card])
    game._auto_play_or_pass(start_spot)
    assert start_spot != game._current_player
    assert game._hand_in_play == Hand([other_min_card])
    assert game._chambers[start_spot].hand == Hand([min_card, max_card])
    
    # if playing and min card not in hand
    game._auto_play_or_pass(game._current_player)  # 2nd consecutive pass
    game._auto_play_or_pass(game._current_player)  # 3rd consecutive pass
    start_spot = game._current_player
    min_card = game._chambers[start_spot]._get_min_card()
    max_card = game._chambers[start_spot]._get_max_card()
    for i, card in enumerate(game._chambers[start_spot]):  # add second lowest card
        if i == 1:
            game.add_or_remove_card(start_spot, card)
            break
    game.add_or_remove_card(start_spot, max_card)
    assert game._chambers[start_spot].hand == Hand([card, max_card])
    assert game._hand_in_play is None
    game._auto_play_or_pass(start_spot)
    assert start_spot != game._current_player
    assert game._hand_in_play == Hand([min_card])
    assert game._chambers[start_spot].hand == Hand([card, max_card])

    # if playing and min card is in hand
    game._auto_play_or_pass(game._current_player)  # 1st consecutive pass
    game._auto_play_or_pass(game._current_player)  # 2nd consecutive pass
    game._auto_play_or_pass(game._current_player)  # 3rd consecutive pass
    start_spot = game._current_player
    min_card = game._chambers[start_spot]._get_min_card()
    max_card = game._chambers[start_spot]._get_max_card()
    game._chambers[start_spot].deselect_selected()
    game.add_or_remove_card(start_spot, min_card)
    game.add_or_remove_card(start_spot, max_card)
    assert game._chambers[start_spot].hand == Hand([min_card, max_card])
    assert game._hand_in_play is None
    game._auto_play_or_pass(start_spot)
    assert start_spot != game._current_player
    assert game._hand_in_play == Hand([min_card])
    assert game._chambers[start_spot].hand == Hand([max_card])
    
    with pytest.raises(AssertionError, match=r'it is not spot'):
        game._auto_play_or_pass(int(not game._current_player))


def test_stop_timer():
    game: Game = Game(
        timer=greenthread.spawn_after,
        turn_time=10,
        reserve_time=10
    )
    game._set_up_testing_base()
    spot: int = game._current_player
    assert isinstance(game._timers[spot], GreenThread)
    # not during reserve time
    game._stop_timer(spot)
    assert game._timers[spot] is None
    # during reserve time
    game._handle_timeout(spot)
    assert game._reserve_times[spot] == 0
    assert game._reserve_time_use_starts[spot] is not None
    assert isinstance(game._timers[spot], GreenThread)
    time.sleep(0.01)
    game._stop_timer(spot)
    assert game._timers[spot] is None
    assert game._reserve_times[spot] < 10
    assert game._reserve_time_use_starts[spot] is None

    with pytest.raises(AssertionError, match=r'timer is none'):
        game.reset()
        game._set_up_testing_base()
        game._stop_timer(not game._current_player)


def test_player_finish():
    game: Game = Game()
    spots: List[int] = list(range(4))
    game._set_up_testing_base()
    start_spot: int = game._current_player
    spots.remove(start_spot)
    assert game._hand_in_play is base_hand
    game._hand_in_play = Hand([1])  # pretend to play
    game._winning_last_played = True
    game._chambers[start_spot].reset()
    game._player_finish(start_spot)
    assert game._is_president(start_spot)
    assert game._turn_manager[start_spot] == False
    assert game._num_unfinished_players == 3
    assert game._takes_remaining[start_spot] == 2
    assert game._gives_remaining[start_spot] == 2
    assert game._current_player != start_spot

    for _ in range(3):
        start_spot = game._current_player
        game._unlock_pass(start_spot)
        game._pass_turn(start_spot)
    game._winning_last_played = False
    
    start_spot = game._current_player
    spots.remove(start_spot)
    assert game._hand_in_play is None
    game._hand_in_play = Hand([2])
    game._num_consecutive_passes = 0
    game._winning_last_played = True
    game._chambers[start_spot].reset()
    game._player_finish(start_spot)
    assert game._is_vice_president(start_spot)
    assert game._turn_manager[start_spot] == False
    assert game._num_unfinished_players == 2
    assert game._takes_remaining[start_spot] == 1
    assert game._gives_remaining[start_spot] == 1
    assert game._current_player != start_spot

    for _ in range(2):
        start_spot = game._current_player
        game._unlock_pass(start_spot)
        game._pass_turn(start_spot)
    game._winning_last_played = False
    
    start_spot = game._current_player
    spots.remove(start_spot)
    assert game._hand_in_play is None
    game._hand_in_play = Hand([3])
    game._num_consecutive_passes = 0
    game._winning_last_played = True
    game._chambers[start_spot].reset()
    game._player_finish(start_spot)
    assert game._is_vice_asshole(start_spot)
    assert game._turn_manager[start_spot] == False
    assert game._num_unfinished_players == 1
    assert game._takes_remaining[start_spot] == 0
    assert game._gives_remaining[start_spot] == 0
    assert game._current_player != start_spot
    assert game._is_asshole(spots[0])
    assert game.trading

    with pytest.raises(AssertionError, match=r'current player can'):
        game.reset()
        game._set_up_testing_base()
        game._player_finish(not game._current_player)
    
    with pytest.raises(AssertionError, match=r'players with no'):
        game.reset()
        game._set_up_testing_base()
        game._player_finish(game._current_player)
    
    with pytest.raises(AssertionError, match=r'last played must'):
        game.reset()
        game._set_up_testing_base()
        spot = game._current_player
        game._chambers[spot].reset()
        game._player_finish(spot)


def test_add_or_remove_card():
    