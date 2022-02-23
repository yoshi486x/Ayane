import shogi
from typing import List
from app.analyze_usecase import AnalyzeUsecase


class KFK:
    game_analysis: 'GameAnalysis'

    @classmethod
    def generate(cls, filename):
        kif = AnalyzeUsecase.import_kif(filename)
        kif_moves = kif['moves']
        kif_sfen = kif['sfen']
        usi = AnalyzeUsecase.define_engine(kif_sfen)

        # set position
        usi_position = f"sfen {kif_sfen}"
        usi.usi_position(usi_position)
        usi.send_command('multipv 1')
        usi.usi_go_and_wait_bestmove("btime 0 wtime 0 byoyomi 1000")
        pv = usi.think_result.pvs[0]
        print(pv.pv)

        # define board
        board = shogi.Board()

        usi_position += " moves"
        # for move in kif_moves:
        for i in range(len(kif_moves)):
            move = kif_moves[i]
            print(f'{i: > 4}', AnalyzeUsecase.generate_japanese_kif_move(board, move))
            print(board.kif_str())

            usi_position += f" {move}"
            usi.usi_position(usi_position)
            # usi.send_command('multipv 1')
            usi.usi_go_and_wait_bestmove("btime 0 wtime 0 byoyomi 1000")
            pv = usi.think_result.pvs[0]   
            pv_moves = pv.pv.split(' ')
            pv_len = len(pv_moves)

            # 読み筋を取り込む
            # for pv_move in pv_moves:
            pv_moves_jp = []
            for j, pv_move in enumerate(pv_moves):
                pv_moves_jp.append(AnalyzeUsecase.generate_japanese_kif_move(board, pv_move))
            print(''.join(pv_moves_jp))

            # 読み筋で取り込んだ手をすべて待ったする
            for _ in range(len(pv_moves)):
                board.pop()

            if i == 50:
                break

        usi.disconnect()

class GameAnalysis:
    kif: str
    score_list: list
    engine_name: str
    time_per_move: int
    analysis_score_list: list
    analysis_info_list: List['AnalysisInfo']


class AnalysisInfo:
    move: str
    score: str
    pv: str
