from faust import App
from .topics import register_presidents_topics
from .tables import register_hand_player_sids_table
from .processors import game_click_processor, get_hand_play_processor


PRESIDENTS_AGENTS = {
    "game_click_agent": {
        "topic": "game_click",
        "processor": game_click_processor,
    },
    "hand_play_agent": {"topic": "hand_play", "processor": None},
}


def register_agent(app: App, topic, processor):
    return app.agent(topic)(processor)


def register_presidents_agents(app: App, topics, tables):
    agents = dict()
    for agent, config in PRESIDENTS_AGENTS.items():
        if agent == "hand_play_agent":
            config["processor"] = get_hand_play_processor(tables['hand_player_sids'])
        agents[agent] = register_agent(
            app, topics[config["topic"]], config["processor"]
        )
    return agents
