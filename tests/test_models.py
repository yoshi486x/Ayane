import unittest

from app.models import KFK
from src.settings import get_settings


settings = get_settings()

class TestKFK(unittest.TestCase):
    def test_generate(self):
        KFK.generate('C4ke/2022-02-05/C4ke-oku002211-20220205_165555.kif')
