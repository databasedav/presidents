from .records import GameClick
from faust import App
from ..db import GameClicks
from datetime import timedelta

app = App("game-click-app", broker="kafka://localhost:9092")

game_click_topic = app.topic("game_click", value_type=GameClick)

played_hand_topic = app.topic('played_hand', value_type=PlayedHand)
played_hand_table = app.Table(
    'played_hands',
    default=int
).hopping(size=2, step=1, expires=timedelta(minutes=15))


@app.agent(game_click_topic)
async def game_click_agent(game_clicks) -> None:
    async for game_click in game_clicks:
        await GameClicks.objects(
            game_id=game_click.game_id,
            user_id=game_click.user_id,
            action=game_click.action
        ).async_update(timestamps__append=[game_click.timestamp])


@app.agent(played_hand_topic)
async def played_hand_agent(played_hands) -> None:
    async for played_hand in played_hands:
        played_hand_table[played_hand.hash] += 1
        # update all players subscribed to this hash's 2 second window
