from faust import App
from .agents import register_presidents_agents
from socketio import AsyncServer


def setup_presidents_faust_app(app: App):
    '''
    Set's up presidents-related things for app, including topics,
    agents, and tables.
    '''
    return register_presidents_agents(app)


class FaustfulAsyncServer(AsyncServer):
        def __init__(self, faust_app, **kwargs):
            super().__init__(**kwargs)
            self.agents = setup_presidents_faust_app(faust_app)
