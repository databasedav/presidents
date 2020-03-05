from __future__ import annotations

from socketio import AsyncServer
from typing import Dict, List, Any, Optional, Iterable, Union
import numpy as np
from .chamber import Chamber, HandNode, HandPointerNode
from .hand import Hand

from asyncio import gather


# TODO: make repr's more meaningful
# TODO: type hints


class PySockChamber(Chamber):
    """
    Chamber that emits events using a python-socketio server.
    """
    def __init__(self, sio, cards: np.ndarray = None) -> None:
        super().__init__(cards)
        self._sock = sio
        self._sid: str = None

    async def _emit(self, *args, **kwargs):
        await self._sock.emit(*args, room=self._sid, **kwargs)

    # async def reset(self) -> None:
    #     super().reset()
    #     self.set_sock(None)
    #     self.set_sid(None)

    async def _emit_clear_cards(self):
        await self._emit('clear_cards', {})

    def set_sock(self, sio) -> None:
        self._sock = sio
        for hand_node in self.hand_nodes:
            hand_node.set_sock(sio)

    def set_sid(self, sid: str) -> None:
        self._sid = sid
        for hand_node in self.hand_nodes:
            hand_node.set_sid(sid)

    async def add_hand(self, hand):
        super().add_hand(hand, hand_node_class=PySockHandNode, sock=self._sock)

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
        await self._emit('add_hand', self._hand_payload(hand))

    async def _emit_add_hands(self, hands: Iterable[Hand]) -> None:
        await self._emit('add_hands', {'hands': [self._hand_payload(hand) for hand in hands]})

    def _hand_payload(self, hand: Hand) -> Dict[str, Union[int, List[int], str]]:
        return {'hash': hash(hand), 'cards': list(hand), 'id_str': hand.id_str}

class PySockHandNode(HandNode):
    def __init__(
        self, hand_pointer_nodes: List[HandPointerNode], *, sock
    ) -> None:
        super().__init__(hand_pointer_nodes)
        self._sock = sock
        self._sid: str = None

    def __repr__(self):
        return "EmittingHandNode"  # TODO

    async def _emit(self, *args, **kwargs) -> None:
        await self._sock.emit(*args, {"id": self._sid}, room=self._sid, **kwargs)

    def set_sock(self, sio) -> None:
        self._sock = sio

    def set_sid(self, sid: str) -> None:
        self._sid = sid

    async def _emit_select_hand(self) -> None:
        await self._emit('select_hand', {'hash': hash(self)})

    async def _emit_deselect_hand(self) -> None:
        await self._emit('deselect_hand', {'hash': hash(self)})
