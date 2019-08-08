from ..app import create_app
from ..utils import main

@main
def run():
    create_app(debug=True).run()
    # uvicorn.run(sio_asgi_app, host='127.0.0.1', port=5000)


# faust app needs to be given the same event loop that the ASGI app uses
# during serving with uvicorn but want the faust app and agents to be in
# separate modules

