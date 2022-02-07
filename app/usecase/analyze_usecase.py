import shogi
import shogi.KIF

from src.models import EngineOptions
from src.engine.engine import UsiEngine
from src.settings import get_settings

settings = get_settings()


class AnalyzeUsecase:
    @staticmethod
    def hoge(filename):
        # import kif
        print('path: ', settings.kifu_path + filename)
        kif = shogi.KIF.Parser.parse_file(settings.kifu_path + filename)[0]
        if kif is None:
            print('kif is None')
            exit(1)
        print('kif:', kif)
        print('black:', kif['names'][shogi.BLACK])
        print('white:', kif['names'][shogi.WHITE])
        kif_moves = kif['moves']

        # set engine
        usi = UsiEngine(debug_print=True)
        # engine_options = EngineOptions(hash=4096, threads=4)
        engine_options = EngineOptions(hash=256, threads=4)
        usi.set_engine_options(engine_options.suisho())
        usi.connect(settings.engine_path)

        # set position
        usi_position = f"sfen {kif['sfen']}"
        usi.usi_position(usi_position)

        usi.send_command('multipv 1')
        usi.usi_go_and_wait_bestmove("btime 0 wtime 0 byoyomi 5000")
        pv = usi.think_result.pvs[0]

        print(pv.pv)

        usi_position += f" moves"
        # for move in kif_moves:
        for i in range(len(kif_moves)):
            move = kif_moves[i]
            print(move)
            usi_position += f" {move}"
            usi.usi_position(usi_position)
            # usi.send_command('multipv 1')
            usi.usi_go_and_wait_bestmove("btime 0 wtime 0 byoyomi 5000")
            pv = usi.think_result.pvs[0]
            print(pv.pv)
            
            if i == 5:
                break
        
        usi.disconnect()
