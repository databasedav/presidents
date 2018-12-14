from chamber import Chamber, HandNode, HandPointerNode
from typing import List
import numpy as np
debug=False
from flask_socketio import emit

class EmittingChamber(Chamber):
    """
    Chamber that emits socketio events. Allows the base data structure
    to be debugged without connection to 
    
    """
    
    def __init__(self, cards: np.ndarray=None) -> None:
        super().__init(cards)
        self._sid: str = None

    def set_sid(sid: str) -> None:
        self._sid = sid
    
    def _emit(self, event: str, payload: Dict[str, Any]):
        emit(event, payload, room=self._sid)

    def add_card(self, card: int) -> None:
        super().add_card(card)
        self._emit('add_card', {'card': card})
    
    def add_hand(self, hand: Hand) -> None:
        for card in hand:
            self.deselect_card(card)
        
        self._emit('store_hand', {
            'id': xxhash.xxh64().intdigest(),
            'cards': cards
        })
        hand_pointer_nodes: List[HandPointerNode] = list()
        cards: List[int] = list() # TODO: replace with uuid once vue adds map support
        hand_node: HandNode = EmittingHandNode(hand_pointer_nodes, cards)
        for card in hand:
            hand_pointer_node: HandPointerNode = HandPointerNode(hand_node)
            hand_pointer_nodes.append(hand_pointer_node)
            self._cards[card].appendnode(hand_pointer_node)
        self._hands.appendnode(hand_node)


class EmittingHandNode(HandNode):

    def __init__(self, hand_pointer_nodes: List[HandPointerNode], cards: List[int]):