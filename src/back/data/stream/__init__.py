# from faust import App
# from .topics import register_presidents_topics
# from .tables import register_hand_player_sids_table
# from .agents import register_presidents_agents
# from socketio import AsyncServer


# def setup_presidents_faust_app(app: App):
#     """
#     Set's up presidents-related things for app, including topics,
#     agents, and tables.
#     """
#     topics = register_presidents_topics(app)
#     tables = {"hand_player_sids": register_hand_player_sids_table(app)}
#     agents = register_presidents_agents(app, topics, tables)
#     return topics, tables, agents


# class FaustfulAsyncServer(AsyncServer):
#     def __init__(self, faust_app, **kwargs):
#         """
#         Saves event loop (for server access), sets up faust app, and
#         saves agents (for server access).
#         """
#         super().__init__(**kwargs)
#         self.agents = setup_presidents_faust_app(faust_app)[2]

import faust
from .records import GameAction

# handles consuming all presidents data streams
presidents_processor = faust.App("presidents", broker="kafka://kafka:9092")

game_action_topic = presidents_processor.topic(
    "game_action", value_type=GameAction
)


@presidents_processor.agent(game_action_topic)
async def game_action_agent(game_actions):
    async for game_action in game_actions:
        print(game_action)
