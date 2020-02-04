import faust
from typing import Any, Optional

from datetime import datetime
from ..utils.game_action_pb2 import GameAction as GameActionProtobuf
from google.protobuf.timestamp_pb2 import Timestamp
from faust.models.fields import StringField
import socketio
from ..utils import GAME_ACTION_DICT


game_god = faust.App("presidents", broker="kafka://data_stream:9092")


class game_action_protobuf(faust.Codec):
    def _dumps(self, obj: Any) -> bytes:
        game_action = GameActionProtobuf(
            game_id=obj["game_id"], action=obj["action"]
        )
        game_action.timestamp.FromDatetime(obj["timestamp"])
        for game_action_attr in ["sid", "user_id"]:
            attr = obj.get(game_action_attr)
            if attr:  # empty string default evals to false
                setattr(game_action, game_action_attr, attr)
        return game_action.SerializeToString()

    def _loads(self, s: bytes) -> Any:
        game_action = GameActionProtobuf()
        game_action.ParseFromString(s)
        game_action_attrs = {
            "game_id": game_action.game_id,
            "action": game_action.action,
            "timestamp": game_action.timestamp.ToDatetime(),
        }
        for game_action_attr in ["sid", "user_id"]:
            attr = getattr(game_action, game_action_attr)
            if attr:
                game_action_attrs[game_action_attr] = getattr(
                    game_action, game_action_attr
                )
        return game_action_attrs


faust.serializers.codecs.register(
    "game_action_protobuf", game_action_protobuf()
)


class GameAction(
    faust.Record, serializer="game_action_protobuf", validation=True
):
    game_id: str
    action: int
    timestamp: datetime
    # TODO: make faust pr so that not assigning None doesn't give validation error
    sid: str = None
    user_id: str = None


# TODO
class ActionField(faust.models.FieldDescriptor[int]):
    def validate(self, value: int):
        ...


game_action_to_process = game_god.topic(
    "game_action_to_process", value_type=GameAction
)
# game_action_to_store = game_god

from . import games


@game_god.agent(game_action_to_process)
async def game_action_processor(game_actions):
    async for game_action in game_actions:
        action, kwargs = GAME_ACTION_DICT[game_action.action]
        await getattr(games[game_action.game_id], f"{action}_handler")(
            game_action.sid, **kwargs
        )
