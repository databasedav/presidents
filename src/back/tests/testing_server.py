from functools import partial
import asyncio

from ..app import create_app
from ..utils import main, AsyncTimer
from ..server import ServerBrowser




import logging
# logging.basicConfig(level=logging.DEBUG)

TURN_TIME = 30
RESERVE_TIME = 60

@main
def run():
    uvicorn, sio = create_app(debug=True)
    
    server_browser = ServerBrowser("us-west")
    sio.register_namespace(server_browser)
    server_browser.add_server('dev', server_id='dev', timer=partial(AsyncTimer.spawn_after, loop=uvicorn.loop), turn_time=TURN_TIME, reserve_time=RESERVE_TIME)

    @sio.event
    async def connect(sid, environ):
        print(environ)
        partial(AsyncTimer.spawn_after, loop=uvicorn.loop)(1, server_browser._join_server_as_player, sid=sid, server_id='dev', name=sid[:10])

    uvicorn.run()
