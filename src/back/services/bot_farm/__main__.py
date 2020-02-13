import uvicorn

from . import bot_farm

uvicorn.run(bot_farm, host="0.0.0.0", port=80)
