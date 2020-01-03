import asyncio
from functools import partial

from ..app import create_app
from ..utils import main, AsyncTimer
from ..server import ServerBrowser


TURN_TIME = 1
RESERVE_TIME = 1
TRADING_TIME = 10000
GIVING_TIME = 10000

DEBUG = True


@main
def run():
    server, sio = create_app(debug=DEBUG)

    server_browser = ServerBrowser("us-west")
    sio.register_namespace(server_browser)
    server_browser.add_server(
        "dev",
        server_id="dev",
        timer=AsyncTimer.spawn_after,
        turn_time=TURN_TIME,
        reserve_time=RESERVE_TIME,
        trading_time=TRADING_TIME,
        giving_time=GIVING_TIME,
    )

    @sio.event
    async def connect(sid, environ):
        print(sid)
        AsyncTimer.spawn_after(
            1,
            server_browser._join_server_as_player,
            sid=sid,
            server_id="dev",
            name=sid[:10],
        )

    server.run()
