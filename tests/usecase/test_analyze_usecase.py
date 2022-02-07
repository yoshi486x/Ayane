import unittest

from app.usecase.analyze_usecase import AnalyzeUsecase
from src.settings import get_settings


settings = get_settings()

class TestAnalyzeUsecase(unittest.TestCase):
    def test_hoge(self):
        AnalyzeUsecase.hoge('C4ke/2022-02-05/C4ke-oku002211-20220205_165555.kif')
