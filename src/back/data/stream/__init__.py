from faust import App
from .topics import register_presidents_topics
from .tables import register_hand_player_sids_table
from .agents import register_presidents_agents
from socketio import AsyncServer


def setup_presidents_faust_app(app: App):
    """
    Set's up presidents-related things for app, including topics,
    agents, and tables.
    """
    topics = register_presidents_topics(app)
    tables = {"hand_player_sids": register_hand_player_sids_table(app)}
    agents = register_presidents_agents(app, topics, tables)
    return topics, tables, agents


class FaustfulAsyncServer(AsyncServer):
    def __init__(self, loop, faust_app, **kwargs):
        """
        Saves event loop (for server access), sets up faust app, and
        saves agents (for server access).
        """
        super().__init__(**kwargs)
        self.loop = loop
        self.agents = setup_presidents_faust_app(faust_app)[2]
