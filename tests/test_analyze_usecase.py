import unittest

from app.analyze_usecase import AnalyzeUsecase
from src.settings import get_settings


settings = get_settings()

class TestAnalyzeUsecase(unittest.TestCase):
    def test_main(self):
        try:
            AnalyzeUsecase.main('C4ke/2022-02-05/C4ke-oku002211-20220205_165555.kif')
        except:
            exit(1)

    def test_import_kif(self):
        kif = AnalyzeUsecase.import_kif('C4ke/2022-02-05/C4ke-oku002211-20220205_165555.kif')
        print('kif:', kif)

    def test_define_engine(sef):
        usi = AnalyzeUsecase.define_engine('lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1')
        usi.disconnect()

    def test_pv_handler(self):
        pv = '7i7h 8c8d 3i4h 8d8e 8h7g 7a6b 4i5h 5c5d 4g4f 3a3b 4h4g 3b4c 4f4e 6b5c 4e4d 5c4d 2h4h 8e8f 8g8f 4a3b 5i6h P*8e 6h7i 8e8f P*8h 8b8e 4g5f'
        AnalyzeUsecase.pv_handler(pv)
