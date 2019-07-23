from .records import GameClick, HandPlay
from faust import App
from ..db.models import GameClicks
from datetime import timedelta
from socketio import AsyncRedisManager
import asyncio

app = App("presidents-app", broker="kafka://localhost:9092")

game_click_topic = app.topic("game_click", value_type=GameClick)

hand_play_topic = app.topic("hand_play", value_type=HandPlay)
hand_player_sids_table = (
    app.Table("hand_players", default=int)
    .hopping(size=2, step=1, expires=timedelta(minutes=15))
    .relative_to_field(HandPlay.timestamp)
)
# emits same hand played increment events to appropriate sids
external_sio = AsyncRedisManager("redis://", write_only=True)


@app.agent(game_click_topic)
async def game_click_agent(game_clicks) -> None:
    async for game_click in game_clicks:
        await GameClicks.objects(
            game_id=game_click.game_id,
            user_id=game_click.user_id,
            action=game_click.action,
        ).async_update(timestamps__append=[game_click.timestamp])


@app.agent(hand_play_topic)
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
