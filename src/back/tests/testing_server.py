from ..app import create_app
from ..utils import main
import os

# os.environ['PYTHONASYNCIODEBUG'] = '1'
import asyncio
import logging

# logging.basicConfig(level=logging.DEBUG)


@main
def run():
    uvicorn = create_app(debug=True)
    uvicorn.run()
