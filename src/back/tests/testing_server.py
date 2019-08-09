from ..app import create_app
from ..utils import main
import os
os.environ['PYTHONASYNCIODEBUG'] = '1'
import asyncio


@main
def run():
    uvicorn, faust_app = create_app(debug=True)
    asyncio.run_coroutine_threadsafe(faust_app.start(), uvicorn.loop)
    uvicorn.run()
    # uvicorn.run(sio_asgi_app, host='127.0.0.1', port=5000)
