from app import create_app, socketio
from app.utils import main


app = create_app(debug=True)


@main
def main():
    socketio.run(app)
