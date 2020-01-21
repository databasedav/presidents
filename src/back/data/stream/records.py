from faust import Record
from datetime import datetime


class GameAction(Record, validation=True):
    game_id: str
    user_id: str
    timestamp: datetime
    action: str


class HandPlay(Record):
    hand_hash: int
    timestamp: datetime
    sid: str
