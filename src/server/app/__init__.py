from flask import Flask
from flask_socketio import SocketIO


socketio = SocketIO()
app = Flask(__name__)
app.debug = False
app.config['SECRET_KEY'] = 'ouh432q8t9ew8ofnuodhuver8'
from .main import main as main_blueprint
app.register_blueprint(main_blueprint)
socketio.init_app(app)
