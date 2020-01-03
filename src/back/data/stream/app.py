import faust
from .records import GameClick

# handles consuming various presidents data streams

app = faust.App("presidents", broker="aiokafka://localhost:9092")

game_click_topic = app.topic("game_click", value_type=GameClick)


@app.agent(game_click_topic)
async def game_click_agent(game_clicks):
    async for game_click in game_clicks:
        print(game_click)
