from pydantic import BaseModel
from uuid import UUID
from typing import List


class GameAttrs(BaseModel):
    name: str
    turn_time: float = 30
    reserve_time: float = 60
    trading_time: float = 60
    giving_time: float = 10


class Player(BaseModel):
    username: str


class PlayerSidGame(Player):
    sid: str
    game_id: str


class Game(GameAttrs):
    game_id: str = None
    num_players: int = None
    players: List[Player] = None


class GameIdUsername(BaseModel):
    game_id: str
    username: str


class GameAction(BaseModel):
    game_id: str
    sid: str
    action: str
    card: int = None  # for card clicks
    rank: int = None  # for asking clicks
