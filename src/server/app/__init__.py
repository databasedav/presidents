from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO(logger=True)

def create_app(*, debug=False):
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'secret'
    socketio.init_app(app)
    return app
