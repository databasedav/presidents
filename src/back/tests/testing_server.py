from fastapi import FastAPI
from socketio import AsyncServer, ASGIApp
from ..server.server_browser import ServerBrowser
from uvicorn import Uvicorn
from ..utils import main
import logging
from ..data.stream.records import GameClick, HandPlay
from faust import App
from ..data.db.models import GameClicks
from datetime import timedelta
from socketio import AsyncRedisManager
import asyncio
import uvloop


logging.basicConfig(level=logging.DEBUG)

app = FastAPI(debug=False)

sio = AsyncServer(
    async_mode="asgi", logger=True, ping_timeout=1000, ping_interval=5
)

server_browser = ServerBrowser("us-west")
sio.register_namespace(server_browser)

sio_asgi_app = ASGIApp(socketio_server=sio, other_asgi_app=app)

Uvicorn.add_config(sio_asgi_app, host="127.0.0.1", port=5000)
Uvicorn.add_server()
Uvicorn.extract_loop()

fapp = App("presidents-app", broker="kafka://localhost:9092", loop=Uvicorn.loop)

game_click_topic = fapp.topic("game_click", value_type=GameClick)

hand_play_topic = fapp.topic("hand_play", value_type=HandPlay)
hand_player_sids_table = (
    fapp.Table("hand_players", default=int)
    .hopping(size=2, step=1, expires=timedelta(minutes=15))
    .relative_to_field(HandPlay.timestamp)
)
# emits same hand played increment events to appropriate sids
external_sio = AsyncRedisManager("redis://", write_only=True)


@fapp.agent(game_click_topic)
async def game_click_agent(game_clicks) -> None:
    async for game_click in game_clicks:
        await GameClicks.objects(
            game_id=game_click.game_id,
            user_id=game_click.user_id,
            action=game_click.action,
        ).async_update(timestamps__append=[game_click.timestamp])


@fapp.agent(hand_play_topic)
async def hand_play_agent(hand_plays) -> None:
    async for hand_play in hand_plays:
        hand_player_sids = hand_player_sids_table[hand_play.hand_hash]
        hand_player_sids.append(hand_play.sid)
        await asyncio.gather(
            *[
                external_sio.emit("increment_same_hand_players", {}, room=sid)
                for sid in hand_player_sids
            ]
        )
        hand_player_sids_table[hand_play.hand_hash] = hand_player_sids

@main
def run():
    Uvicorn.run(sio_asgi_app)
