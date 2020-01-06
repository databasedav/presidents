from pydantic import BaseModel
from uuid import UUID
from typing import List

class GameServer(BaseModel):
    game_server_id: UUID
    game_server_server_id: int
    name: str
    turn_time: float
    reserve_time: float
    trading_time: float
    giving_time: float
    num_players: int
    players: List[str]
    keys: List[str]
