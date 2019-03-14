from .server import RoomBrowser

from flask import Flask, Blueprint
from flask_socketio import SocketIO
import random
import uuid


main = Blueprint('main', __name__)
socketio = SocketIO(logger=True)

# uses global namespace (/) now but this could be customized if I want
# to have multiple room browsers
room_browser = RoomBrowser(str(uuid.uuid4()))
socketio.on_namespace(room_browser)

for name in ['hello', 'world']:
    room_browser._add_room(name)


def create_app(*, debug=False):
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'secret'
    app.register_blueprint(main)
    socketio.init_app(app)
    return app
