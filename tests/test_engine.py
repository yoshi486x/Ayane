import unittest

from src.engine.engine import UsiEngine
from src.settings import get_settings


settings = get_settings()

class TestEngine(unittest.TestCase):
    def test_engine(self):
        usi = UsiEngine()
        usi.debug_print = True
        usi.connect(settings.engine_path)
        print(usi.engine_path)
        usi.usi_position("startpos moves 7g7f")
        print("moves = " + usi.get_moves())
        usi.disconnect()
        print(usi.engine_state)
        print(usi.exit_state)
