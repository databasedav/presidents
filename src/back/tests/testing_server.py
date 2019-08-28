from ..app import create_app
from ..utils import main

import logging
# logging.basicConfig(level=logging.DEBUG)

TURN_TIME = 30
RESERVE_TIME = 60

@main
def run():
    uvicorn = create_app(debug=True, **{'turn_time': TURN_TIME, 'reserve_time': RESERVE_TIME})
    uvicorn.run()
