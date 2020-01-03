from llist import dllist


class IterNodesDLList(dllist):
    """
    Wrapper for dllist with iter_nodes method.
    """

    def __repr__(self) -> str:
        return "IterNodesDLList"

    def iter_nodes(self):
        curr_node = self.first
        while curr_node is not None:
            yield curr_node
            curr_node = curr_node.next
