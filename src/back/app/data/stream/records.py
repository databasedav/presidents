from faust import Record
import datetime


class GameClick(Record):
    game_id: str
    user_id: str
    timestamp: str
    action: str
