from .game import Game

class FaustGame(Game):
    """
    Game that emits events using faust.
    """
    async def _emit_hand_play(self, hand_hash: int):
        await self._hand_play_processor.cast(
            HandPlay(game_id=self.game_id, hand_hash=hand_hash)
        )