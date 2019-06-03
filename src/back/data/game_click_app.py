import faust
from faust.utils import iso8601
import datetime
from . import session, GameClicks


class GameClick(faust.Record):
    game_id: str
    user_id: str
    timestamp: datetime.datetime
    action: str
        

app = faust.App('game-click-app', broker='kafka://localhost:9092')
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

        # await session.execute_async(
        #     f'''
        #     update presidents.game_clicks 
        #     set timestamps = timestamps + ['{iso8601.parse(game_click.timestamp[:-2])}']
        #     where game_id='{game_click.game_id}'
        #         and username='{game_click.username}'
        #         and action='{game_click.action}'
        #     '''
        # ).result()

        # session.execute_async(
        #     f'''
        #     update presidents.game_click
        #     set timestamps = timestamps + [{iso8601.parse(game_click.timestamp)}]
        #     where game_id={game_click.game_id}
        #         and username={game_click.username}
        #         and action={game_click.action}
        #     '''
        # )

        # await GameClicks.objects(
        #     game_id=game_click.game_id,
        #     username=game_click.username,
        #     action=game_click.action
        # ).update(timestamps__append=[iso8601.parse(game_click.timestamp)])


if __name__ == '__main__':
    app.main()