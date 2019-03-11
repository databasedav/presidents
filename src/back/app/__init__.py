from flask import Flask, Blueprint
from flask_socketio import SocketIO

main = Blueprint('main', __name__)
socketio = SocketIO(logger=True)


def create_app(*, debug=False):
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'secret'
    app.register_blueprint(main)
    socketio.init_app(app)
    return app
