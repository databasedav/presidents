from __future__ import annotations

from . import Hand, Chamber, HandNode, HandPointerNode

from socketio import AsyncServer
from typing import Dict, List, Any, Optional
import numpy as np

import asyncio

# from ..server.server import Server


# TODO: make repr's more meaningful
# TODO: type hints


class EmittingChamber(Chamber):
    """
    Chamber that emits socketio events. Allows the base data structure
    to be debugged without needing an active HTTP request.
    """

    def __init__(self, server: Server, cards: np.ndarray = None) -> None:
        super().__init__(cards)
        self._server: Server = server
        self._sid: str = None

    async def _emit(self, *args, **kwargs):
        await self._server.emit(*args, room=self._sid, **kwargs)

    async def reset(self) -> None:
        await self._emit("clear_cards", {})
        await self._emit_update_current_hand_str()
        self.set_sid(None)
        # TODO: deal with hands being removed, i.e. the asshole's stored
        #       hands must be removed
        super().reset()

    def set_sid(self, sid: Optional[str]) -> None:
        self._sid = sid
        for hand_node in self._hands.iter_nodes():
            hand_node.set_sid(sid)

    async def add_card(self, card: int, **kwargs) -> None:
        super().add_card(card, **kwargs)
        await self._emit("add_card", {"card": int(card)})

    async def add_cards(self, cards) -> None:
        self._check_cards_not_in(cards)
        # already checked
        await asyncio.gather(
            *[self.add_card(card, check=False) for card in cards]
        )

    async def remove_card(self, card: int, *, update_current_hand_str: bool = True, **kwargs) -> None:
        super().remove_card(card, **kwargs)
        await self._emit("remove_card", {"card": int(card)})
        if update_current_hand_str:
            await self._emit_update_current_hand_str()
    
    async def remove_cards(self, cards) -> None:
        self._check_cards_in(cards)
        # already checked
        await asyncio.gather(
            *[self.remove_card(card, update_current_hand_str=False, check=False) for card in cards]
        )
        await self._emit_update_current_hand_str()

    async def add_hand(self, hand: Hand) -> None:
        """
        Emits hand storage and uses EmittingHandNodes instead of
        HandNodes.
        """
        # TODO: POLL: should the cards be deselected after creating a hand?
        self.deselect_cards(hand)
        await self._emit(
            "store_hand",
            {"id": xxhash.xxh64().intdigest(), "cards": hand.to_list()},
        )
        hand_pointer_nodes: List[HandPointerNode] = list()
        hand_node: HandNode = EmittingHandNode(
            hand_pointer_nodes, self._server
        )
        for card in hand:
            hand_pointer_node: HandPointerNode = HandPointerNode(hand_node)
            hand_pointer_nodes.append(hand_pointer_node)
            self._cards[card].appendnode(hand_pointer_node)
        self._hands.appendnode(hand_node)

    async def select_card(self, card: int, check: bool = True) -> None:
        super().select_card(card, check)
        await self._emit("select_card", {"card": card})
        await self._emit_update_current_hand_str()

    async def deselect_card(self, card: int, check: bool = True) -> None:
        super().deselect_card(card, check)
        await self._emit("deselect_card", {"card": int(card)})
        # TODO: current hand str shouldn't be lazy loaded
        await self._emit_update_current_hand_str()

    async def _emit_update_current_hand_str(self) -> None:
        await self._emit("update_current_hand_str", {"str": str(self.hand)})


class EmittingHandNode(HandNode):
    def __init__(
        self, hand_pointer_nodes: List[HandPointerNode], server
    ) -> None:
        self._server: Server = server
        self._id = None  # TODO: random number or string (which one is better?)
        self._sid: str = None

    def __repr__(self):
        return "EmittingHandNode"  # TODO

    def _emit(self, *args, **kwargs) -> None:
        self._server.emit(*args, {"id": self._sid}, room=self._sid, **kwargs)

    def set_sid(self, sid: str) -> None:
        self._sid = sid

    async def increment_num_selected_cards(self) -> None:
        super().increment_num_selected_cards()
        if self._num_cards_selected == 1:
            await self._emit("select_hand")

    async def decrement_num_selected_cards(self) -> None:
        super().decrement_num_selected_cards()
        if self._num_cards_selected == 0:
            await self._emit("deselect_hand")
