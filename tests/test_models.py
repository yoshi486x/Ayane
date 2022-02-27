import unittest

from app.models import KFK, Utils
from src.settings import get_settings


settings = get_settings()

class TestUtils(unittest.TestCase):
    def test_generate(self):
        Utils.generate_kfk('C4ke/2022-02-05/C4ke-oku002211-20220205_165555.kif')


class TestKFK(unittest.TestCase):
    def test_generate_xml_str(self):
        KFK()
        