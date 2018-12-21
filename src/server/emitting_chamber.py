from __future__ import annotations
from chamber import Chamber, HandNode, HandPointerNode
from typing import Dict, List, Any
import numpy as np
from flask_socketio import emit


# TODO: make repr's more meaningful
# TODO: type hints


class EmittingChamber(Chamber):
    """
    Chamber that emits socketio events. Allows the base data structure
    to be debugged without needing an active HTTP request.
    """
    
    def __init__(self, cards: np.ndarray=None) -> None:
        super().__init__(cards)
        self._sid: str = None
    
    def _emit(self, event: str, payload: [Dict[str, Any], None]=None):
        emit(event, payload, room=self._sid)
    
    def reset(self) -> None:
        self._emit('clear_cards')
        super().reset()

    def set_sid(self, sid: str) -> None:
        self._sid = sid
        for hand_node in self._hands.iter_nodes():
            hand_node.set_sid(sid)

    # TODO: card maybe both a python int and np.uint8
    def add_card(self, card: np.uint8) -> None:
        self._emit('add_card', {'card': int(card)})
        super().add_card(card)
        
    def remove_card(self, card: np.uint8, check: bool) -> None:
        super().remove_card(card, check)
        self._emit('remove_card', {'card': card})

    def add_hand(self, hand: Hand) -> None:
        """
        Emits hand storage and uses EmittingHandNodes instead of
        HandNodes.
        """
        # TODO: POLL: should the cards be deselected after creating a hand?
        self.deselect_cards(card)
        self._emit('store_hand', {
            'id': xxhash.xxh64().intdigest(),
            'cards': hand.to_list()
        })
        hand_pointer_nodes: List[HandPointerNode] = list()
        hand_node: HandNode = EmittingHandNode(hand_pointer_nodes, self._sid)
        for card in hand:
            hand_pointer_node: HandPointerNode = HandPointerNode(hand_node)
            hand_pointer_nodes.append(hand_pointer_node)
            self._cards[card].appendnode(hand_pointer_node)
        self._hands.appendnode(hand_node)
    
    def select_card(self, card: int, check: bool=True) -> None:
        super().select_card(card, check)
        self._emit('select_card', {'card': card})
        self._emit_update_current_hand_str()

    def deselect_card(self, card: int, check: bool=True) -> None:
        super().deselect_card(card, check)
        self._emit('deselect_card', {'card': card})
        self._emit_update_current_hand_str()
    
    def _emit_update_current_hand_str(self) -> None:
        self._emit('update_current_hand_str', {'str': str(self.current_hand)})


class EmittingHandNode(HandNode):

    def __init__(self, hand_pointer_nodes: List[HandPointerNode]) -> None:
        self._id = None  # TODO: random number or string (which one is better?)
        self._sid = None
    
    def __repr__(self):
        return 'EmittingHandNode'
    
    def _emit(self, event, paylaod) -> None:
        emit(event, {'id': self._id}, room=self._sid)
    
    def set_sid(self, sid: str) -> None:
        self._sid = sid

    def increment_num_selected_cards(self) -> None:
        super().increment_num_selected_cards()
        if self._num_cards_selected == 1:
            self._emit('select_hand')

    def decrement_num_selected_cards(self) -> None:
        super().decrement_num_selected_cards()
        if self._num_cards_selected == 0:
            self._emit('deselect_hand')

