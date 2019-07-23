from faust import Record
from datetime import datetime


class GameClick(Record):
    game_id: str
    user_id: str
    timestamp: str
    action: str


class HandPlay(Record):
    hand_hash: int
    timestamp: datetime
    sid: str
