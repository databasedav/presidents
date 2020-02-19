from aiocqlengine.models import AioModel
from cassandra.cqlengine.columns import (
    Boolean,
    DateTime,
    Integer,
    List,
    Map,
    Text,
    TinyInt,
    UUID,
)

# milliseconds suffice
DateTime.truncate_microseconds = True


class User(AioModel):
    __table_name__ = "user"
    __keyspace__ = "presidents"
    user_id = UUID(primary_key=True, partition_key=True, required=True)
    username = Text(required=True)
    previous_usernames = List(value_type=Text)
    password = Text(required=True)  # hashed
    created = DateTime(required=True)
    # stores all user preferences like unselecting cards on store hand,
    # etc.
    settings = Map(key_type=Text, value_type=Text)


class Username(AioModel):
    """
    Maintaining this table trivializes name changes.
    """

    __table_name__ = "username"
    __keyspace__ = "presidents"
    username = Text(primary_key=True, partition_key=True, required=True)
    user_id = UUID(required=True)


class GameClicks(AioModel):
    __table_name__ = "game_user_clicks"
    __keyspace__ = "presidents"
    game_id = UUID(primary_key=True, partition_key=True, required=True)
    user_id = UUID(primary_key=True, partition_key=True, required=True)
    action = Text(primary_key=True, required=True, clustering_order="ASC")
    timestamps = List(value_type=DateTime, required=True)


class UserGames(AioModel):
    __table_name__ = "user_games"
    __keyspace__ = "presidents"
    user_id = UUID(primary_key=True, partition_key=True, required=True)
    game_ids = List(value_type=UUID, required=False)


class UserRoundtimeSpots(AioModel):
    __table_name__ = "user_roundtime_spots"
    __keyspace__ = "presidents"
    user_id = UUID(primary_key=True, partition_key=True, required=True)
    round_id = UUID(primary_key=True, partition_key=True, required=True)
    # round time is either simply start of round if player did not join
    # mid round, or the time the round is joined; it is like this
    # because a player can join and leave the same round multiple times
    roundtime_to_spot = Map(
        key_type=DateTime, value_type=TinyInt, required=True
    )
    spot = TinyInt(required=True)


class UserLeavetimes(AioModel):
    __table_name__ = "user_leave_timestamps"
    __keyspace__ = "presidents"
    user_id = UUID(primary_key=True, partition_key=True, required=True)
    game_id = UUID(primary_key=True, partition_key=True, required=True)
    leave_timestamps = List(value_type=DateTime, required=False)


class Game(AioModel):
    __table_name__ = "game"
    __keyspace__ = "presidents"
    game_id = UUID(primary_key=True, partition_key=True, required=True)
    user_ids = List(value_type=UUID, required=False)
    creation_timestamp = DateTime(required=True)
    destruction_timestamp = DateTime(required=False)
    round_ids = List(value_type=UUID, required=False)
    pause_start_timestamps = List(value_type=DateTime, required=False)
    pause_end_timestamps = List(value_type=DateTime, required=False)


class Round(AioModel):
    __table_name__ = "round"
    __keyspace__ = "presidents"
    round_id = UUID(primary_key=True, partition_key=True, required=True)
    game_id = UUID(required=True)
    start_timestamp = DateTime(required=True)
    end_timestamp = DateTime(required=False)
    round_number = Integer(required=True)


class RoundCards(AioModel):
    __table_name__ = "round_cards"
    __keyspace__ = "presidents"
    round_id = UUID(primary_key=True, partition_key=True, required=True)
    spot = TinyInt(primary_key=True, required=True, clustering_order="ASC")
    cards = List(value_type=TinyInt, required=True)
