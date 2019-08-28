from .records import GameClick, HandPlay
from faust import App
from ..db.models import GameClicks
from datetime import timedelta
from socketio import AsyncRedisManager
import asyncio
import uvloop


async def game_click_processor(game_clicks) -> None:
    """
    Writes game clicks to database.
    """
    async for game_click in game_clicks:
        await GameClicks.objects(
            game_id=game_click.game_id,
            user_id=game_click.user_id,
            action=game_click.action,
        ).async_update(timestamps__append=[game_click.timestamp])


# emits same hand played increment events to appropriate sids
# external_sio = AsyncRedisManager("redis://", write_only=True)


def get_hand_play_processor(hand_player_sids_table):
    async def hand_play_processor(hand_plays) -> None:
        """
        Writes sids to windowed hand play table and emits increment same
        hand players to all sids corresponding to the hand played.
        """
        async for hand_play in hand_plays:
            # print(hand_play)
            hand_player_sids = hand_player_sids_table[hand_play.hand_hash].value()
            hand_player_sids.append(hand_play.sid)
            print(f'{hand_play.hand_hash}: {len(hand_player_sids)}')
            # # await asyncio.gather(
            # #     *[
            # #         external_sio.emit(
            # #             "increment_same_hand_players", {}, room=sid
            # #         )
            # #         for sid in hand_player_sids
            # #     ]
            # # )
            hand_player_sids_table[hand_play.hand_hash] = hand_player_sids

    return hand_play_processor
