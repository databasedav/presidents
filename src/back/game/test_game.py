import re
from .game import Game


class TestGame(Game):
    """
    overwrites emits to record emits
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._emits = list()
    
    @classmethod
    def _testify_emit_method(cls, emit_method: str):
        exec(f"async def {emit_method}(self, *args):\n self._emits.append(('{emit_method[6:]}', args))")
        setattr(cls, emit_method, eval(emit_method))


for emit_method in filter(re.compile('_emit').match, dir(Game)):
    TestGame._testify_emit_method(emit_method)
