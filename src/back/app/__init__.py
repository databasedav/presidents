from .server import ServerBrowser

from flask import Flask, Blueprint
from flask_socketio import SocketIO
import uuid


main = Blueprint('main', __name__)
socketio = SocketIO(logger=True)

# uses global namespace (/) now but this could be customized if I want
# to have multiple server browsers
server_browser = ServerBrowser('US-West')
socketio.on_namespace(server_browser)

for name in ['hello', 'world']:
    server_browser._add_server(name)


def create_app(*, debug=False):
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'secret'
    app.register_blueprint(main)
    socketio.init_app(app)
    return app
