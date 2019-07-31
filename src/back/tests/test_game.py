from ..game.game import Game, PresidentsError, base_hand, NoopTimer
from ..game.chamber import Chamber
from ..game.hand import NotPlayableOnError
import numpy as np
import pytest
from eventlet import greenthread
from eventlet.greenthread import GreenThread
import time
from ..game.hand import Hand
from typing import List


# TODO: hacker boi tests will really matter when testing the emitting
#       versions because the client will have changed a variable
#       allowing them to make an illegal action, and the resulting
#       backend error should correct this variable value
# TODO: add GreenThread testing


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
    assert game._finishing_last_played == False
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
    assert game._finishing_last_played == False
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
        timer=greenthread.spawn_after, turn_time=0.01, reserve_time=0.05
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
    assert game._finishing_last_played == False
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
    assert all(f"player{i}" in game._names for i in range(4))
    assert all(chamber.num_cards == 13 for chamber in game._chambers)
    assert game._num_consecutive_rounds == 1
    assert game._current_player is not None

    with pytest.raises(AssertionError, match=r"set up testing"):
        game = Game()
        game.add_player("player0")
        game._set_up_testing_base()

    game.reset()
    game._set_up_testing_base(
        deck=[
            range(lower, upper)
            for lower, upper in zip(range(1, 53, 13), range(14, 54, 13))
        ]
    )
    assert game.is_full
    assert all(f"player{spot}" in game._names[spot] for spot in range(4))
    assert all(chamber.num_cards == 13 for chamber in game._chambers)
    assert all(card in game._chambers[0] for card in range(1, 14))
    assert all(card in game._chambers[1] for card in range(14, 27))
    assert all(card in game._chambers[2] for card in range(27, 40))
    assert all(card in game._chambers[3] for card in range(40, 53))
    assert game._num_consecutive_rounds == 1
    assert game._current_player is not None

    game.reset()
    game.add_player('player0')
    with pytest.raises(AssertionError, match=r'must be empty'):
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
    game.reset()
    game._deal_cards(
        deck=[
            range(lower, upper)
            for lower, upper in zip(range(1, 53, 13), range(14, 54, 13))
        ]
    )
    assert all(chamber.num_cards == 13 for chamber in game._chambers)
    assert all(card in game._chambers[0] for card in range(1, 14))
    assert all(card in game._chambers[1] for card in range(14, 27))
    assert all(card in game._chambers[2] for card in range(27, 40))
    assert all(card in game._chambers[3] for card in range(40, 53))


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

    game.reset()
    for i in range(4):
        game.add_player(f"player{i}")
    game._start_round(
        deck=[
            range(lower, upper)
            for lower, upper in zip(range(1, 53, 13), range(14, 54, 13))
        ]
    )
    assert all(chamber.num_cards == 13 for chamber in game._chambers)
    assert all(card in game._chambers[0] for card in range(1, 14))
    assert all(card in game._chambers[1] for card in range(14, 27))
    assert all(card in game._chambers[2] for card in range(27, 40))
    assert all(card in game._chambers[3] for card in range(40, 53))
    assert game._turn_manager is not None
    assert game._num_consecutive_rounds == 1
    assert 1 in game._chambers[game._current_player]


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
    assert not game._is_current_player(start_spot)
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
    assert not game._is_current_player(start_spot)
    assert game._hand_in_play == Hand([1])

    # pass
    start_spot = game._current_player
    assert isinstance(game._timers[start_spot], GreenThread)
    assert game._hand_in_play == Hand([1])
    game._auto_play_or_pass(start_spot)
    assert not game._is_current_player(start_spot)
    assert game._hand_in_play == Hand([1])
    # pass
    start_spot = game._current_player
    assert isinstance(game._timers[start_spot], GreenThread)
    assert game._hand_in_play == Hand([1])
    game._auto_play_or_pass(start_spot)
    assert not game._is_current_player(start_spot)
    assert game._hand_in_play == Hand([1])
    # pass
    start_spot = game._current_player
    assert isinstance(game._timers[start_spot], GreenThread)
    assert game._hand_in_play == Hand([1])
    game._auto_play_or_pass(start_spot)
    assert not game._is_current_player(start_spot)
    assert game._hand_in_play is None

    # can play anyhand so play min single
    start_spot = game._current_player
    min_card: int = game._chambers[start_spot]._get_min_card()
    assert game._hand_in_play is None
    game._auto_play_or_pass(start_spot)
    assert not game._is_current_player(start_spot)
    assert game._hand_in_play == Hand([min_card])

    # selected cards should remain selected after auto play or pass
    # if passing
    other_min_card = min_card
    start_spot = game._current_player
    min_card = game._chambers[start_spot]._get_min_card()
    max_card: int = game._chambers[start_spot]._get_max_card()
    game.add_or_remove_card(start_spot, min_card)
    game.add_or_remove_card(start_spot, max_card)
    assert game._get_current_hand(start_spot) == Hand([min_card, max_card])
    game._auto_play_or_pass(start_spot)
    assert not game._is_current_player(start_spot)
    assert game._hand_in_play == Hand([other_min_card])
    assert game._get_current_hand(start_spot) == Hand([min_card, max_card])

    # if playing and min card not in hand
    game._auto_play_or_pass(game._current_player)  # 2nd consecutive pass
    game._auto_play_or_pass(game._current_player)  # 3rd consecutive pass
    start_spot = game._current_player
    min_card = game._chambers[start_spot]._get_min_card()
    max_card = game._chambers[start_spot]._get_max_card()
    for i, card in enumerate(
        game._chambers[start_spot]
    ):  # add second lowest card
        if i == 1:
            game.add_or_remove_card(start_spot, card)
            break
    game.add_or_remove_card(start_spot, max_card)
    assert game._get_current_hand(start_spot) == Hand([card, max_card])
    assert game._hand_in_play is None
    game._auto_play_or_pass(start_spot)
    assert not game._is_current_player(start_spot)
    assert game._hand_in_play == Hand([min_card])
    assert game._get_current_hand(start_spot) == Hand([card, max_card])

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
    assert game._get_current_hand(start_spot) == Hand([min_card, max_card])
    assert game._hand_in_play is None
    game._auto_play_or_pass(start_spot)
    assert not game._is_current_player(start_spot)
    assert game._hand_in_play == Hand([min_card])
    assert game._get_current_hand(start_spot) == Hand([max_card])

    with pytest.raises(AssertionError, match=r"it is not spot"):
        game._auto_play_or_pass(int(not game._current_player))


def test_stop_timer():
    game: Game = Game(
        timer=greenthread.spawn_after, turn_time=10, reserve_time=10
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

    with pytest.raises(AssertionError, match=r"timer is none"):
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
    game._finishing_last_played = True
    game._chambers[start_spot].reset()
    game._player_finish(start_spot)
    assert game._is_president(start_spot)
    assert game._turn_manager[start_spot] == False
    assert game._num_unfinished_players == 3
    assert game._takes_remaining[start_spot] == 2
    assert game._gives_remaining[start_spot] == 2
    assert not game._is_current_player(start_spot)

    for _ in range(3):
        start_spot = game._current_player
        game._unlock_pass(start_spot)
        game._pass_turn(start_spot)
    game._finishing_last_played = False

    start_spot = game._current_player
    spots.remove(start_spot)
    assert game._hand_in_play is None
    game._hand_in_play = Hand([2])
    game._num_consecutive_passes = 0
    game._finishing_last_played = True
    game._chambers[start_spot].reset()
    game._player_finish(start_spot)
    assert game._is_vice_president(start_spot)
    assert game._turn_manager[start_spot] == False
    assert game._num_unfinished_players == 2
    assert game._takes_remaining[start_spot] == 1
    assert game._gives_remaining[start_spot] == 1
    assert not game._is_current_player(start_spot)

    for _ in range(2):
        start_spot = game._current_player
        game._unlock_pass(start_spot)
        game._pass_turn(start_spot)
    game._finishing_last_played = False

    start_spot = game._current_player
    spots.remove(start_spot)
    assert game._hand_in_play is None
    game._hand_in_play = Hand([3])
    game._num_consecutive_passes = 0
    game._finishing_last_played = True
    game._chambers[start_spot].reset()
    game._player_finish(start_spot)
    assert game._is_vice_asshole(start_spot)
    assert game._turn_manager[start_spot] == False
    assert game._num_unfinished_players == 1
    assert game._takes_remaining[start_spot] == 0
    assert game._gives_remaining[start_spot] == 0
    assert not game._is_current_player(start_spot)
    assert game._is_asshole(spots[0])
    assert game.trading

    # empty chamber assertion
    game.reset()
    game._set_up_testing_base()
    with pytest.raises(AssertionError, match=r"with no cards"):
        game._player_finish(game._current_player)


def test_add_or_remove_card():
    game: Game = Game()
    game._set_up_testing_base()
    spot: int = game._current_player
    # add when not unlocked
    assert game._get_current_hand(spot).is_empty
    assert not game._is_asking(spot)
    assert not game._unlocked[spot]
    game.add_or_remove_card(spot, 1)
    assert game._get_current_hand(spot) == Hand([1])
    assert not game._is_asking(spot)
    assert not game._unlocked[spot]
    # add when unlocked
    assert game._get_current_hand(spot) == Hand([1])
    game._get_current_hand(spot).remove(1)
    assert game._get_current_hand(spot).is_empty
    assert not game._is_asking(spot)
    assert not game._unlocked[spot]
    game._unlock(spot)
    assert game._unlocked[spot]
    game.add_or_remove_card(spot, 1)
    assert game._get_current_hand(spot) == Hand([1])
    assert not game._is_asking(spot)
    assert not game._unlocked[spot]
    # add when player is asking and not unlocked
    game.trading = True
    game._selected_asking_option[spot] = 13
    assert game._is_asking(spot)
    assert not game._unlocked[spot]
    assert game._get_current_hand(spot) == Hand([1])
    game._get_current_hand(spot).remove(1)
    assert game._get_current_hand(spot).is_empty
    game.add_or_remove_card(spot, 1)
    assert game._get_current_hand(spot) == Hand([1])
    assert game._selected_asking_option[spot] is None
    assert not game._unlocked[spot]
    # add when player is asking and unlocked
    game.trading = True
    game._selected_asking_option[spot] = 13
    assert game._is_asking(spot)
    assert not game._unlocked[spot]
    game._unlock(spot)
    assert game._unlocked[spot]
    assert game._get_current_hand(spot) == Hand([1])
    game._get_current_hand(spot).remove(1)
    assert game._get_current_hand(spot).is_empty
    game.add_or_remove_card(spot, 1)
    assert game._get_current_hand(spot) == Hand([1])
    assert game._selected_asking_option[spot] is None
    assert not game._unlocked[spot]

    # dealing with the hacker bois
    with pytest.raises(PresidentsError, match=r"don't have this") as e:
        game.add_or_remove_card(not game._current_player, 1)
    assert not e.value.permitted

    # remove when not unlocked
    assert game._get_current_hand(spot) == Hand([1])
    assert not game._unlocked[spot]
    game.add_or_remove_card(spot, 1)
    assert game._get_current_hand(spot).is_empty
    assert not game._unlocked[spot]
    # remove when unlocked
    assert game._get_current_hand(spot).is_empty
    assert not game._unlocked[spot]
    game.add_or_remove_card(spot, 1)
    assert game._get_current_hand(spot) == Hand([1])
    assert not game._unlocked[spot]
    game._unlock(spot)
    assert game._unlocked[spot]
    game.add_or_remove_card(spot, 1)
    assert game._get_current_hand(spot).is_empty
    assert not game._unlocked[spot]

    # full hand error
    with pytest.raises(PresidentsError, match=r"hand is full") as e:
        assert game._get_current_hand(spot).is_empty
        for card in game._chambers[spot]:
            game.add_or_remove_card(spot, card)
    assert e.value.permitted

    # already finished error
    assert not game._is_finished(spot)
    game._turn_manager.remove(spot)
    assert game._is_finished(spot)
    with pytest.raises(PresidentsError, match=r"already finished") as e:
        game.add_or_remove_card(spot, 1)
    assert not e.value.permitted


def test_store_hand():
    # TODO
    ...


def test_maybe_unlock_play():
    game: Game = Game()
    game._set_up_testing_base()
    spot: int = game._current_player

    # base hand; player with 3 of clubs; pass not unlocked; the rest
    # will be with it pass unlocked
    assert 1 in game._chambers[spot]
    game.add_or_remove_card(spot, 1)
    assert game._get_current_hand(spot) == Hand([1])
    assert not game._pass_unlocked[spot]
    assert game._hand_in_play is base_hand
    game.maybe_unlock_play(spot)
    assert game._get_current_hand(spot) == Hand([1])
    assert not game._pass_unlocked[spot]
    assert game._unlocked[spot]

    # empty hand
    assert game._get_current_hand(spot) == Hand([1])
    game.add_or_remove_card(spot, 1)
    assert game._get_current_hand(spot).is_empty
    assert not game._pass_unlocked[spot]
    game._unlock_pass(spot)
    assert not game._unlocked[spot]
    assert game._pass_unlocked[spot]
    with pytest.raises(PresidentsError, match=r"must add cards") as e:
        game.maybe_unlock_play(spot)
    assert e.value.permitted
    assert not game._pass_unlocked[spot]

    # invalid hand

    assert game._get_current_hand(spot).is_empty
    game.add_or_remove_card(spot, 1)
    max_card: int = game._chambers[spot]._get_max_card()
    game.add_or_remove_card(spot, max_card)
    assert game._get_current_hand(spot) == Hand([1, max_card])
    assert not game._get_current_hand(spot).is_valid
    assert not game._pass_unlocked[spot]
    game._unlock_pass(spot)
    assert not game._unlocked[spot]
    assert game._pass_unlocked[spot]
    with pytest.raises(PresidentsError, match=r"play invalid") as e:
        game.maybe_unlock_play(spot)
    assert e.value.permitted
    assert not game._pass_unlocked[spot]

    # base hand; player with 3 of clubs; no 3 of clubs in hand
    assert game._get_current_hand(spot) == Hand([1, max_card])
    game.add_or_remove_card(spot, 1)
    assert game._get_current_hand(spot) == Hand([max_card])
    assert game._hand_in_play is base_hand
    assert not game._pass_unlocked[spot]
    game._unlock_pass(spot)
    assert not game._unlocked[spot]
    assert game._pass_unlocked[spot]
    with pytest.raises(PresidentsError, match=r"contain the 3") as e:
        game.maybe_unlock_play(spot)
    assert e.value.permitted
    assert not game._pass_unlocked[spot]

    # base hand; player other than player with 3 of clubs
    spot = not game._current_player
    assert game._get_current_hand(spot).is_empty
    game.add_or_remove_card(spot, game._chambers[spot]._get_min_card())
    assert game._hand_in_play is base_hand
    assert not game._pass_unlocked[spot]
    game._unlock_pass(spot)
    assert not game._unlocked[spot]
    assert game._pass_unlocked[spot]
    game.maybe_unlock_play(spot)
    assert game._unlocked[spot]
    assert not game._pass_unlocked[spot]

    # hand in play is None; anyone can unlock
    game.reset()
    game._set_up_testing_base()
    game.add_or_remove_card(game._current_player, 1)
    game._unlock(game._current_player)
    game._play_current_hand(game._current_player)
    assert game._hand_in_play == Hand([1])
    for _ in range(3):
        game._unlock_pass(game._current_player)
        game._pass_turn(game._current_player)
    assert game._hand_in_play is None
    assert all(not unlocked for unlocked in game._unlocked)
    assert all(not pass_unlocked for pass_unlocked in game._pass_unlocked)
    for spot in range(4):
        game._unlock_pass(spot)
    assert all(pass_unlocked for pass_unlocked in game._pass_unlocked)
    for spot in range(4):
        game.add_or_remove_card(spot, game._chambers[spot]._get_min_card())
        game.maybe_unlock_play(spot)
        assert game._unlocked[spot]
        assert not game._pass_unlocked[spot]

    # hand in play is actually a hand; stronger hand
    game.reset()
    game._set_up_testing_base()
    spot = game._current_player
    game.add_or_remove_card(spot, 1)
    game.maybe_unlock_play(spot)
    assert game._unlocked[spot]
    game._play_current_hand(spot)
    assert game._hand_in_play == Hand([1])
    spot = game._current_player
    min_card: int = game._chambers[spot]._get_min_card()
    game.add_or_remove_card(spot, min_card)
    assert game._get_current_hand(spot) == Hand([min_card])
    assert not game._unlocked[spot]
    assert not game._pass_unlocked[spot]
    game._unlock_pass(spot)
    assert game._pass_unlocked[spot]
    # everyone else's min card is greater than the 3 of clubs
    game.maybe_unlock_play(spot)
    assert game._unlocked[spot]
    assert not game._pass_unlocked[spot]

    # hand in play is actually a hand; weaker hand
    assert game._hand_in_play == Hand([1])
    assert game._get_current_hand(spot) == Hand([min_card])
    game.add_or_remove_card(spot, min_card)
    assert game._get_current_hand(spot).is_empty
    max_card: int = game._chambers[spot]._get_max_card()
    game.add_or_remove_card(spot, max_card)
    assert game._get_current_hand(spot) == Hand([max_card])
    game.maybe_unlock_play(spot)
    game._play_current_hand(spot)
    assert game._hand_in_play == Hand([max_card])

    # go through players until you find a play with a min card that is
    # lower than the above max_card; it's possible that no one has such
    # a card but this is hilariously unlikely
    for _ in range(3):
        spot = game._current_player
        min_card = game._chambers[spot]._get_min_card()
        if min_card < max_card:
            assert game._get_current_hand(spot).is_empty
            game.add_or_remove_card(spot, min_card)
            assert game._get_current_hand(spot) == Hand([min_card])
            assert not game._pass_unlocked[spot]
            game._unlock_pass(spot)
            assert game._pass_unlocked[spot]
            with pytest.raises(PresidentsError, match=r"hand is weaker") as e:
                game.maybe_unlock_play(spot)
            assert e.value.permitted
            break
        else:
            game._unlock_pass(spot)
            game._pass_turn(spot)
    assert not game._pass_unlocked[spot]

    # hand in play is actually a hand; not playable on
    # keep resetting until the first player has a double 3
    game.reset()
    game._set_up_testing_base()
    while (
        not sum(
            [
                card in game._chambers[game._current_player]
                for card in range(2, 5)
            ]
        )
        >= 1
    ):  # thank you black for this beautiful while condition
        game.reset()
        game._set_up_testing_base()
    spot = game._current_player
    game.add_or_remove_card(spot, 1)
    for card in range(2, 5):
        if card in game._chambers[spot]:
            game.add_or_remove_card(spot, card)
            break
    game.maybe_unlock_play(spot)
    game._play_current_hand(spot)
    assert game._hand_in_play == Hand([1, card])
    spot = game._current_player
    assert game._get_current_hand(spot).is_empty
    min_card = game._chambers[spot]._get_min_card()
    game.add_or_remove_card(spot, min_card)
    assert game._get_current_hand(spot) == Hand([min_card])
    assert not game._unlocked[spot]
    assert not game._pass_unlocked[spot]
    game._unlock_pass(spot)
    assert game._pass_unlocked[spot]
    with pytest.raises(PresidentsError, match=r"cannot be") as e:
        game.maybe_unlock_play(spot)
    assert e.value.permitted

    # already finished error
    assert not game._is_finished(spot)
    game._turn_manager.remove(spot)
    assert game._is_finished(spot)
    with pytest.raises(PresidentsError, match=r"already finished") as e:
        game.maybe_unlock_play(spot)
    assert not e.value.permitted


def test_maybe_play_current_hand():
    game: Game = Game()
    game._set_up_testing_base()
    spot: int = game._current_player

    # hackers bois
    assert not game._unlocked[spot]
    with pytest.raises(PresidentsError, match=r"you must unlock") as e:
        game.maybe_play_current_hand(game._current_player)
    assert not e.value.permitted
    assert not game._unlocked[spot]

    # not current player
    spot = not game._current_player
    assert not game._unlocked[spot]
    game.add_or_remove_card(spot, game._chambers[spot]._get_min_card())
    game.maybe_unlock_play(spot)
    with pytest.raises(PresidentsError, match=r"a hand on") as e:
        game.maybe_play_current_hand(spot)
    assert e.value.permitted

    # all good
    spot = game._current_player
    assert game._get_current_hand(spot).is_empty
    game.add_or_remove_card(spot, 1)
    game.maybe_unlock_play(spot)
    assert game._unlocked[spot]
    assert game._is_current_player(spot)
    assert game._hand_in_play is base_hand
    game.maybe_play_current_hand(spot)
    assert game._hand_in_play == Hand([1])

    # already finished error
    assert not game._is_finished(spot)
    game._turn_manager.remove(spot)
    assert game._is_finished(spot)
    with pytest.raises(PresidentsError, match=r"already finished") as e:
        game.maybe_play_current_hand(spot)
    assert not e.value.permitted


def test_play_current_hand():
    game: Game = Game()
    game._set_up_testing_base()

    with pytest.raises(AssertionError, match=r"called without"):
        game._play_current_hand(game._current_player)

    # other players are not unlocked; no post handling; no passes
    spot: int = game._current_player
    game.add_or_remove_card(spot, 1)
    game.maybe_unlock_play(spot)
    assert game._timers[spot] is not None
    assert 1 in game._chambers[spot]
    assert game._num_consecutive_passes == 0
    assert game._hand_in_play is base_hand
    assert game._unlocked[spot]
    assert all(
        not game._unlocked[other_spot]
        for other_spot in game._get_other_spots(spot)
    )
    assert game._is_current_player(spot)
    assert not game._finishing_last_played
    game._play_current_hand(spot, handle_post=False)
    assert game._timers[spot] is None
    assert 1 not in game._chambers[spot]
    assert game._num_consecutive_passes == 0
    assert game._hand_in_play == Hand([1])
    assert not game._unlocked[spot]
    assert all(
        not game._unlocked[other_spot]
        for other_spot in game._get_other_spots(spot)
    )
    assert game._is_current_player(spot)
    assert not game._finishing_last_played

    # other players not unlocked; handle post; some passes
    game._post_play_handler(spot)
    game._unlock_pass(game._current_player)
    game._pass_turn(game._current_player)
    game._unlock_pass(game._current_player)
    game._pass_turn(game._current_player)
    spot = game._current_player
    min_card: int = game._chambers[spot]._get_min_card()
    game.add_or_remove_card(spot, min_card)
    game.maybe_unlock_play(spot)
    assert game._timers[spot] is not None
    assert min_card in game._chambers[spot]
    assert game._num_consecutive_passes == 2
    assert game._hand_in_play == Hand([1])
    assert game._unlocked[spot]
    assert all(
        not game._unlocked[other_spot]
        for other_spot in game._get_other_spots(spot)
    )
    assert game._is_current_player(spot)
    assert not game._finishing_last_played
    game._play_current_hand(spot)
    assert game._timers[spot] is None
    assert min_card not in game._chambers[spot]
    assert game._num_consecutive_passes == 0
    assert game._hand_in_play == Hand([min_card])
    assert not game._unlocked[spot]
    assert all(
        not game._unlocked[other_spot]
        for other_spot in game._get_other_spots(spot)
    )
    assert not game._is_current_player(spot)
    assert not game._finishing_last_played

    # other players unlocked; handle post; no passes
    game.reset()
    game._set_up_testing_base(
        deck=[
            range(lower, upper)
            for lower, upper in zip(range(1, 53, 13), range(14, 54, 13))
        ]
    )
    game.add_or_remove_card(0, 1)
    game.maybe_unlock_play(0)
    assert game._timers[0] is not None
    assert 1 in game._chambers[0]
    assert game._num_consecutive_passes == 0
    assert game._hand_in_play is base_hand
    assert game._unlocked[0]
    assert all(
        not game._unlocked[other_spot]
        for other_spot in game._get_other_spots(0)
    )
    game.add_or_remove_card(1, 14)
    game.add_or_remove_card(1, 15)
    game.maybe_unlock_play(1)
    game.add_or_remove_card(2, 27)
    game.add_or_remove_card(2, 28)
    game.maybe_unlock_play(2)
    game.add_or_remove_card(3, 41)
    game.add_or_remove_card(3, 42)
    game.maybe_unlock_play(3)
    assert all(
        game._unlocked[other_spot] for other_spot in game._get_other_spots(0)
    )
    assert game._is_current_player(0)
    assert not game._finishing_last_played
    game._play_current_hand(0)
    assert game._timers[0] is None
    assert 1 not in game._chambers[0]
    assert game._num_consecutive_passes == 0
    assert game._hand_in_play == Hand([1])
    assert not game._unlocked[0]
    assert all(
        not game._unlocked[other_spot]
        for other_spot in game._get_other_spots(0)
    )
    assert not game._is_current_player(0)
    assert not game._finishing_last_played

    # handling not playable on
    game.reset()
    game._set_up_testing_base(
        deck=[
            range(lower, upper)
            for lower, upper in zip(range(1, 53, 13), range(14, 54, 13))
        ]
    )
    game.add_or_remove_card(0, 1)
    game.add_or_remove_card(0, 2)
    game.add_or_remove_card(0, 3)
    game.add_or_remove_card(0, 4)
    game.add_or_remove_card(0, 5)
    assert game._get_current_hand(0).is_bomb
    game.maybe_unlock_play(0)
    assert game._timers[0] is not None
    assert 1 in game._chambers[0]
    assert game._num_consecutive_passes == 0
    assert game._hand_in_play is base_hand
    assert game._unlocked[0]
    assert all(
        not game._unlocked[other_spot]
        for other_spot in game._get_other_spots(0)
    )
    game.add_or_remove_card(1, 14)
    game.maybe_unlock_play(1)
    assert game._unlocked[1]
    assert game._is_current_player(0)
    assert not game._finishing_last_played
    with pytest.raises(NotPlayableOnError, match=r'on a bomb'):
        game._get_current_hand(1) < game._get_current_hand(0)
    game._play_current_hand(0)
    assert game._timers[0] is None
    assert 1 not in game._chambers[0]
    assert game._num_consecutive_passes == 0
    assert game._hand_in_play == Hand([1, 2, 3, 4, 5])
    assert not game._unlocked[0]
    assert not game._unlocked[1]
    assert not game._is_current_player(0)
    assert not game._finishing_last_played

    # don't lock if stronger than hand in play
    game.reset()
    game._set_up_testing_base(
        deck=[
            range(lower, upper)
            for lower, upper in zip(range(1, 53, 13), range(14, 54, 13))
        ]
    )
    game.add_or_remove_card(0, 1)
    game.maybe_unlock_play(0)
    assert game._timers[0] is not None
    assert 1 in game._chambers[0]
    assert game._num_consecutive_passes == 0
    assert game._hand_in_play is base_hand
    assert game._unlocked[0]
    assert all(
        not game._unlocked[other_spot]
        for other_spot in game._get_other_spots(0)
    )
    game.add_or_remove_card(1, 14)
    game.maybe_unlock_play(1)
    assert game._unlocked[1]
    assert game._is_current_player(0)
    assert not game._finishing_last_played
    game._play_current_hand(0)
    assert game._timers[0] is None
    assert 1 not in game._chambers[0]
    assert game._num_consecutive_passes == 0
    assert game._hand_in_play == Hand([1])
    assert not game._unlocked[0]
    assert game._unlocked[1]
    assert not game._is_current_player(0)
    assert not game._finishing_last_played

    # handling player finishes
    game.reset()
    game._set_up_testing_base()
    spot = game._current_player
    chamber: Chamber = game._chambers[spot]
    for i, card in enumerate(chamber):
        if i == 0:
            continue
        else:
            chamber.remove_card(card)
    assert chamber.num_cards == 1
    assert 1 in chamber
    game.add_or_remove_card(spot, 1)
    game.maybe_unlock_play(spot)
    assert game._timers[spot] is not None
    assert 1 in game._chambers[spot]
    assert game._num_consecutive_passes == 0
    assert game._hand_in_play is base_hand
    assert game._unlocked[spot]
    other_spot: int = not spot
    game.add_or_remove_card(other_spot, game._chambers[other_spot]._get_min_card())
    assert not game._unlocked[other_spot]
    game.maybe_unlock_play(other_spot)
    assert game._unlocked[other_spot]
    assert game._is_current_player(spot)
    assert not game._finishing_last_played
    game._play_current_hand(spot)
    assert game._timers[spot] is None
    assert game._chambers[spot].is_empty
    assert game._num_consecutive_passes == 0
    assert game._hand_in_play == Hand([1])
    assert not game._unlocked[spot]
    assert game._unlocked[other_spot]
    assert not game._is_current_player(spot)
    assert game._finishing_last_played
    assert game._is_finished(spot)


def test_post_play_handler():
    game: Game = Game()
    game._set_up_testing_base()
    # player has not played all their cards; not finishing last played
    spot: int = game._current_player
    assert game._chambers[spot].num_cards == 13
    game.add_or_remove_card(spot, 1)
    game.maybe_unlock_play(spot)
    game._play_current_hand(spot, handle_post=False)
    assert not game._finishing_last_played
    assert game._is_current_player(spot)
    game._post_play_handler(spot)
    assert not game._finishing_last_played
    assert not game._is_current_player(spot)

    # when player has played all their cards
    while game._chambers[spot].num_cards > 1:
        for _ in range(3):
            game._unlock_pass(game._current_player)
            game._pass_turn(game._current_player)
        game.add_or_remove_card(spot, game._chambers[spot]._get_min_card())
        game.maybe_unlock_play(spot)
        game._play_current_hand(spot)
    for _ in range(3):
        game._unlock_pass(game._current_player)
        game._pass_turn(game._current_player)
    assert game._is_current_player(spot)
    assert game._chambers[spot].num_cards == 1
    game.add_or_remove_card(spot, game._chambers[spot]._get_min_card())
    game.maybe_unlock_play(spot)
    game._play_current_hand(spot, handle_post=False)
    assert game._chambers[spot].is_empty
    assert not game._finishing_last_played
    assert game._is_current_player(spot)
    game._post_play_handler(spot)
    assert game._finishing_last_played
    assert not game._is_current_player(spot)
    assert game._is_finished(spot)
    assert game._is_president(spot)

    # playing on a finishing last played
    game.reset()
    game._set_up_testing_base(
        deck=[
            range(lower, upper)
            for lower, upper in zip(range(1, 53, 13), range(14, 54, 13))
        ]
    )
    for card in range(1, 14):
        game.add_or_remove_card(0, card)
        game.maybe_unlock_play(0)
        game._play_current_hand(0)
        if card == 13:
            break
        for spot in range(1, 4):
            game._unlock_pass(spot)
            game._pass_turn(spot)
    game.add_or_remove_card(1, 14)
    game.maybe_unlock_play(1)
    game._play_current_hand(1, handle_post=False)
    assert game._finishing_last_played
    assert game._is_current_player(1)
    game._post_play_handler(1)
    assert not game._finishing_last_played
    assert game._is_current_player(2)


def test_maybe_unlock_pass_turn():
    game: Game = Game()
    game._set_up_testing_base()
    spot: int = game._current_player
    
    # already finished error
    game._chambers[spot].reset()
    game._player_finish(spot)
    with pytest.raises(PresidentsError, match=r'already finished') as e:
        game.maybe_unlock_pass_turn(spot)
    assert not e.value.permitted

    # is current player with 3 of clubs
    game.reset()
    game._set_up_testing_base()
    spot = game._current_player
    assert game._is_current_player(spot)
    assert game._hand_in_play is base_hand
    with pytest.raises(PresidentsError, match=r'have the 3') as e:
        game.maybe_unlock_pass_turn(spot)
    assert e.value.permitted

    # is current player who can play anyhand
    game.add_or_remove_card(spot, 1)
    game.maybe_unlock_play(spot)
    game.maybe_play_current_hand(spot)
    for _ in range(3):
        game._unlock_pass(game._current_player)
        game._pass_turn(game._current_player)
    assert game._is_current_player(spot)
    assert game._hand_in_play is None
    with pytest.raises(PresidentsError, match=r'play anyhand') as e:
        game.maybe_unlock_pass_turn(spot)
    assert e.value.permitted


def test_unlock_pass():
    game: Game = Game()
    assert not game._unlocked[0]
    assert not game._pass_unlocked[0]
    game._unlock_pass(0)
    assert not game._unlocked[0]
    assert game._pass_unlocked[0]

    game._unlock(1)
    assert game._unlocked[1]
    assert not game._pass_unlocked[1]
    game._unlock_pass(1)
    assert not game._unlocked[1]
    assert game._pass_unlocked[1]


def test_lock_pass():
    game: Game = Game()
    game._unlock_pass(0)
    assert game._pass_unlocked[0]
    game._lock_pass(0)
    assert not game._pass_unlocked[0]


def test_maybe_pass_turn():
    game: Game = Game()
    game._set_up_testing_base()
    spot: int = game._current_player
    
    # already finished error
    game._chambers[spot].reset()
    game._player_finish(spot)
    with pytest.raises(PresidentsError, match=r'already finished') as e:
        game.maybe_pass_turn(spot)
    assert not e.value.permitted

    # pass is not unlocked
    game.reset()
    game._set_up_testing_base()
    spot = game._current_player
    assert not game._pass_unlocked[spot]
    with pytest.raises(PresidentsError, match=r'must unlock pass') as e:
        game.maybe_pass_turn(spot)
    assert not e.value.permitted

    # not current player
    assert not game._pass_unlocked[not spot]
    game._unlock_pass(not spot)
    assert game._pass_unlocked[not spot]
    with pytest.raises(PresidentsError, match=r'only pass on') as e:
        game.maybe_pass_turn(not spot)
    assert e.value.permitted

    # is current player and pass unlocked
    game.add_or_remove_card(spot, 1)
    game.maybe_unlock_play(spot)
    game.maybe_play_current_hand(spot)
    spot = game._current_player
    game._unlock_pass(spot)
    assert game._hand_in_play == Hand([1])
    game.maybe_pass_turn(spot)
    assert game._hand_in_play == Hand([1])
    assert not game._is_current_player(spot)


def test_pass_turn():
    game: Game = Game()
    game._set_up_testing_base()
    spot: int = game._current_player
    with pytest.raises(AssertionError, match=r'pass called'):
        game._pass_turn(spot)
    game.add_or_remove_card(spot, 1)
    game.maybe_unlock_play(spot)
    game.maybe_play_current_hand(spot)

    # don't handle post
    spot = game._current_player
    game.maybe_unlock_pass_turn(spot)
    assert game._timers[spot] is not None
    assert game._pass_unlocked[spot]
    assert game._num_consecutive_passes == 0
    assert game._is_current_player(spot)
    game._pass_turn(spot, handle_post=False)
    assert game._timers[spot] is None
    assert not game._unlocked[spot]
    assert game._num_consecutive_passes == 1
    assert game._is_current_player(spot)

    # handle post
    game._post_pass_handler()
    assert not game._is_current_player(spot)
    spot = game._current_player
    game.maybe_unlock_pass_turn(spot)
    assert game._timers[spot] is not None
    assert game._pass_unlocked[spot]
    assert game._num_consecutive_passes == 1
    assert game._is_current_player(spot)
    game._pass_turn(spot)
    assert game._timers[spot] is None
    assert not game._unlocked[spot]
    assert game._num_consecutive_passes == 2
    assert not game._is_current_player(spot)


def test_post_pass_handler():
    game: Game = Game()
    game._set_up_testing_base()
    
    
    # all remaining players passed on a winning hand

