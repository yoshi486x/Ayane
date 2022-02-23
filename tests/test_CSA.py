import unittest

from app import CSA
from src.settings import get_settings


settings = get_settings()

class TestCSA(unittest.TestCase):
    def test_parse_kif(self):
        csa_str = CSA.Reader.read_str(settings.kifu_path + 'C4ke/2022-02-05/C4ke-oku002211-20220205_165555.kif')
        print(csa_str)
