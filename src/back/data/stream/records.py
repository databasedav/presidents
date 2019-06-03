from faust import Recod
import datetime

class GameClick(Record):
    game_id: str
    user_id: str
    timestamp: datetime.datetime
    action: str