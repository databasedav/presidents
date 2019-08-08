from .processors import hand_play_processor

def register_agent(app, topic, processor):
    return app.agent(topic)(processor)

hand_play_agent = register_agent()
