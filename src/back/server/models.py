from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional
import datetime


class GameAttrs(BaseModel):
    name: str
    turn_time: float = 30
    reserve_time: float = 60
    trading_time: float = 60
    giving_time: float = 10


class Username(BaseModel):
    username: str


class Sid(BaseModel):
    sid: str


class GameId(BaseModel):
    game_id: str


class UsernameSidGameId(Username, Sid, GameId):
    pass


class Game(GameAttrs):
    game_id: str
    num_players: int = None
    players: List[Username] = None
    fresh: int = 1  # redis doesn't support bools


class GameList(BaseModel):
    games: List[Optional[Game]]


class GameKey(BaseModel):
    game_key: str


class GameIdUsername(BaseModel):
    game_id: str
    username: str


class GameAction(BaseModel):
    game_id: str
    sid: str
    action: str
    card: int = None  # for card clicks
    rank: int = None  # for asking clicks
    timestamp: datetime.datetime = None


class Token(BaseModel):
    access_token: str
    token_type: str


class UsernamePasswordReenterPassword(BaseModel):
    username: str
    password: str
    reenter_password: str
