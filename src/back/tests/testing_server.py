import logging
# logging.basicConfig(level=logging.DEBUG)
import os
os.environ['PYTHONASYNCIODEBUG'] = '1'
import asyncio
from functools import partial

from ..app import create_app
from ..utils import main, AsyncTimer
from ..server import ServerBrowser

# logger = logging.getLogger("asyncio")
# logger.setLevel(logging.DEBUG)


TURN_TIME = 2
RESERVE_TIME = 0


@main
def run():
    uvicorn, sio = create_app(debug=False)

    server_browser = ServerBrowser("us-west")
    sio.register_namespace(server_browser)
    server_browser.add_server(
        "dev",
        server_id="dev",
        timer=partial(AsyncTimer.spawn_after, loop=uvicorn.loop),
        turn_time=TURN_TIME,
        reserve_time=RESERVE_TIME,
    )

    @sio.event
    async def connect(sid, environ):
        # print(environ)
        partial(AsyncTimer.spawn_after, loop=uvicorn.loop)(
            1,
            server_browser._join_server_as_player,
            sid=sid,
            server_id="dev",
            name=sid[:10],
        )

    uvicorn.run()
