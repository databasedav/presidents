from __future__ import annotations

from . import Hand, HandNode, HandPointerNode

from socketio import AsyncServer
from typing import Dict, List, Any, Optional, Iterable
import numpy as np
from .chamberr import Chamber


from asyncio import gather

# from ..server.server import Server


# TODO: make repr's more meaningful
# TODO: type hints


class PySockChamber(Chamber):
    """
    Chamber that emits events using a python-socketio server.
    """
    def __init__(self, sio, cards: np.ndarray = None) -> None:
        super().__init__(cards)
        self._sio = sio
        self._sid: str = None

    async def _emit(self, *args, **kwargs):
        await self._sio.emit(*args, room=self._sid, **kwargs)

    # async def reset(self) -> None:
    #     super().reset()
    #     self.set_sio(None)
    #     self.set_sid(None)

    async def _emit_clear_cards(self):
        await self._emit('clear_cards', {})

    def set_sio(self, sio) -> None:
        self._sio = sio
        for hand_node in self._hand_nodes:
            hand_node.set_sio(sio)

    def set_sid(self, sid: str) -> None:
        self._sid = sid
        for hand_node in self._hand_nodes:
            hand_node.set_sid(sid)

    async def _emit_add_card(self, card: int) -> None:
        await self._emit("add_card", {"card": card})

    async def _emit_add_cards(self, cards: Iterable[int]) -> None:
        await self._emit('add_cards', {'cards': list(cards)})

    async def _emit_remove_card(self, card: int) -> None:
        await self._emit('remove_card', {'card': card})
    
    async def _emit_remove_cards(self, cards: Iterable[int]) -> None:
        await self._emit('remove_cards', {'cards': list(cards)})
    
    async def _emit_select_card(self, card: int) -> None:
        await self._emit('select_card', {'card': card})

    async def _emit_select_cards(self, cards: Iterable[int]) -> None:
        await self._emit('select_cards', {'cards': cards})

    async def _emit_deselect_card(self, card: int) -> None:
        await self._emit('deselect_card', {'card': card})

    async def _emit_deselect_cards(self, cards: Iterable[int]) -> None:
        await self._emit('deselect_cards', {'cards': cards})

    async def _emit_update_current_hand_str(self) -> None:
        await self._emit("update_current_hand_str", {"str": str(self.hand)})

    async def _emit_add_hand(self, hand: Hand) -> None:
        await self._emit(
            'add_hand',
            {
                "id": xxhash.xxh64().intdigest(),
                "cards": hand.to_list(),
                "id_desc": hand.id_desc,
            }
        )


class EmittingHandNode(HandNode):
    def __init__(
        self, hand_pointer_nodes: List[HandPointerNode], *, sio
    ) -> None:
        super().__init__(hand_pointer_nodes)
        self._sio = sio
        self._id = None  # TODO: random number or string (which one is better?)
        self._sid: str = None

    def __repr__(self):
        return "EmittingHandNode"  # TODO

    async def _emit(self, *args, **kwargs) -> None:
        await self._sio.emit(*args, {"id": self._sid}, room=self._sid, **kwargs)

    def set_sio(self, sio) -> None:
        self._sio = sio

    def set_sid(self, sid: str) -> None:
        self._sid = sid

    async def _emit_select_hand(self) -> None:
        await self._emit('select_hand')

    async def _emit_deselect_hand(self) -> None:
        await self._emit('deselect_hand')