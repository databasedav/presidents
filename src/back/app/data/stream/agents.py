from .records import GameClick
from faust import App

app = App('game-click-app', broker='kafka://localhost:9092')
topic = app.topic('game_click', value_type=GameClick)

@app.agent(topic)
async def game_click_agent(game_clicks):
    async for game_click in game_clicks:
        print(
            f'''
            game_id: {game_click.game_id}
            username: {game_click.user_id}
            timestamp: {game_click.timestamp}
            action: {game_click.action}
            '''
        )
        await
