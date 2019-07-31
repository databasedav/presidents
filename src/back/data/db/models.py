from cassandra.cqlengine.models import Model
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

DateTime.truncate_microseconds = False


class GameClicks(Model):
    __table_name__ = "game_user_clicks"
    __keyspace__ = "presidents"
    game_id = UUID(primary_key=True, partition_key=True, required=True)
    user_id = UUID(primary_key=True, partition_key=True, required=True)
    action = Text(primary_key=True, required=True, clustering_order="ASC")
    timestamps = List(value_type=DateTime, required=True)


class UserGames(Model):
    __table_name__ = "user_games"
    __keyspace__ = "presidents"
    user_id = UUID(primary_key=True, partition_key=True, required=True)
    game_ids = List(value_type=UUID, required=False)


class UserRoundtimeSpots(Model):
    __table_name__ = "user_jointime_spots"
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


class UserLeavetimes(Model):
    __table_name__ = "user_leave_timestamps"
    __keyspace__ = "presidents"
    user_id = UUID(primary_key=True, partition_key=True, required=True)
    game_id = UUID(primary_key=True, partition_key=True, required=True)
    leave_timestamps = List(value_type=DateTime, required=False)


class Game(Model):
    __table_name__ = "game"
    __keyspace__ = "presidents"
    game_id = UUID(primary_key=True, partition_key=True, required=True)
    user_ids = List(value_type=UUID, required=False)
    creation_timestamp = DateTime(required=True)
    destruction_timestamp = DateTime(required=False)
    round_ids = List(value_type=UUID, required=False)
    pause_start_timestamps = List(value_type=DateTime, required=False)
    pause_end_timestamps = List(value_type=DateTime, required=False)


class Round(Model):
    __table_name__ = "round"
    __keyspace__ = "presidents"
    round_id = UUID(primary_key=True, partition_key=True, required=True)
    game_id = UUID(required=True)
    start_timestamp = DateTime(required=True)
    end_timestamp = DateTime(required=False)
    round_number = Integer(required=True)


class RoundCards(Model):
    __table_name__ = "round_cards"
    __keyspace__ = "presidents"
    round_id = UUID(primary_key=True, partition_key=True, required=True)
    spot = TinyInt(primary_key=True, required=True, clustering_order="ASC")
    cards = List(value_type=TinyInt, required=True)
