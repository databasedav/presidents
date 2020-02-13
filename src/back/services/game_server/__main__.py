import uvicorn

from . import game_server

uvicorn.run(game_server, host="0.0.0.0", port=80)
