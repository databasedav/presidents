from ..app import create_app
from ..utils import main


@main
def run():
    create_app(debug=True).run()
    # uvicorn.run(sio_asgi_app, host='127.0.0.1', port=5000)
