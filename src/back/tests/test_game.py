import uuid
import pytest

from ..game import Game, base_hand, Chamber


def test_constructor():
    game: Game = Game()
    # instance related attributes
    assert game.game_id is not None
    assert game.num_players == 0
    assert game._num_consecutive_rounds == 0
    assert game._times_reset == 0
    # timer related attributes
    assert all(timer is None for timer in game._timers)
    assert game._turn_time == Game.TURN_TIME
    assert all(turn_time == 0 for turn_time in game._turn_times)
    assert all(turn_time_start is None for turn_time_start in game._turn_time_starts)
    assert game._reserve_time == Game.RESERVE_TIME
    assert all(reserve_time for reserve_time in game._reserve_times)
    assert all(reserve_time_start is None for reserve_time_start in game._reserve_time_starts)
    assert game._trading_timer is None
    assert game._trading_time == Game.TRADING_TIME
    assert game._trading_time_remaining == Game.TRADING_TIME
    assert game._trading_time_start is None
    assert game._giving_time == Game.GIVING_TIME
    assert len(game._paused_timers) == 0
    # setup and ID related attributes
    assert all(spot == i for i, spot in enumerate(game._open_spots))
    assert all(name is None for name in game._names)
    # game related attributes
    assert game._turn_manager is None
    assert game._current_player is None
    assert (isinstance(chamber, Chamber) for chamber in game._chambers)
    assert game._hand_in_play is base_hand
    assert game._num_consecutive_passes == 0
    assert game._finishing_last_played is False
    assert len(game._positions) == 0
    assert all(unlocked is False for unlocked in game._unlocked)
    assert all(pass_unlocked is False for pass_unlocked in game._pass_unlocked)
    assert all(dot_color == 'red' for dot_color in game._dot_colors)
    # trading related attributes
    assert game.trading is False
    assert all(rank is None for rank in game._ranks)
    assert all(len(already_asked) == 0 for already_asked in game._already_asked)
    assert all(waiting is False for waiting in game._waiting)
    assert all(len(giving_options) == 0 for giving_options in game._giving_options)
    assert all(gives == 0 for gives in game._gives)
    assert all(takes == 0 for takes in game._takes)
    assert all(len(given) == 0 for given in game._given)
    assert all(len(taken) == 0 for taken in game._taken)

    game_id: str = str(uuid.uuid4())
    turn_time: float = 1
    reserve_time: float = 1
    trading_time: float = 1
    giving_time: float = 1
    game = Game(game_id=game_id, turn_time=turn_time, reserve_time=reserve_time, trading_time=trading_time, giving_time=giving_time)
    # instance related attributes
    assert game.game_id == game_id
    assert game.num_players == 0
    assert game._num_consecutive_rounds == 0
    assert game._times_reset == 0
    # timer related attributes
    assert all(timer is None for timer in game._timers)
    assert game._turn_time == turn_time
    assert all(turn_time == 0 for turn_time in game._turn_times)
    assert all(turn_time_start is None for turn_time_start in game._turn_time_starts)
    assert game._reserve_time == reserve_time
    assert all(reserve_time for reserve_time in game._reserve_times)
    assert all(reserve_time_start is None for reserve_time_start in game._reserve_time_starts)
    assert game._trading_timer is None
    assert game._trading_time == trading_time
    assert game._trading_time_remaining == trading_time
    assert game._trading_time_start is None
    assert game._giving_time == giving_time
    assert len(game._paused_timers) == 0
    # setup and ID related attributes
    assert all(spot == i for i, spot in enumerate(game._open_spots))
    assert all(name is None for name in game._names)
    # game related attributes
    assert game._turn_manager is None
    assert game._current_player is None
    assert (isinstance(chamber, Chamber) for chamber in game._chambers)
    assert game._hand_in_play is base_hand
    assert game._num_consecutive_passes == 0
    assert game._finishing_last_played is False
    assert len(game._positions) == 0
    assert all(unlocked is False for unlocked in game._unlocked)
    assert all(pass_unlocked is False for pass_unlocked in game._pass_unlocked)
    assert all(dot_color == 'red' for dot_color in game._dot_colors)
    # trading related attributes
    assert game.trading is False
    assert all(rank is None for rank in game._ranks)
    assert all(len(already_asked) == 0 for already_asked in game._already_asked)
    assert all(waiting is False for waiting in game._waiting)
    assert all(len(giving_options) == 0 for giving_options in game._giving_options)
    assert all(gives == 0 for gives in game._gives)
    assert all(takes == 0 for takes in game._takes)
    assert all(len(given) == 0 for given in game._given)
    assert all(len(taken) == 0 for taken in game._taken)


def test_reset():
    ...  # TODO


@pytest.mark.asyncio
async def test_no_takes_or_gives():
    game: Game = Game()
    await game._set_up_testing_base()
    assert game._no_takes_or_gives
    await game._get_game_to_trading()
    assert not game._no_takes_or_gives
    await game._auto_trade()
    assert game._no_takes_or_gives


@pytest.mark.asyncio
async def test_num_unfinished_players():
    game: Game = Game()
    await game._set_up_testing_base()
    


