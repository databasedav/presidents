from faust import App
from typing import List
from datetime import timedelta
from .records import HandPlay


def register_hand_player_sids_table(app: App):
    return (
        app.Table("hand_player_sids", default=list).hopping(
            size=2, step=1, expires=timedelta(minutes=5)
        )
        # .relative_to_field(HandPlay.timestamp)
    )
