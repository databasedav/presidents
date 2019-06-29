try:
    from .app import create_app, socketio
    from .utils import main
except (
    ImportError,
    ModuleNotFoundError,
):  # does this even happen?; y does this happen?
    from app import create_app, socketio
    from utils import main


app = create_app(debug=False)


@main
def dev():
    socketio.run(app)
