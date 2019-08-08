from faust import App
from .records import GameClick, HandPlay


PRESIDENTS_TOPICS = {
    'game_click': {
        'value_type': GameClick
    },
    'hand_play': {
        'value_type': HandPlay
    }
}


def register_topic(app: App, topic, **kwargs):
    return app.topic(topic, **kwargs)


def register_presidents_topics(app: App):
    return {topic: register_topic(topic, **kwargs) for topic, kwargs in PRESIDENTS_TOPICS.items()}
