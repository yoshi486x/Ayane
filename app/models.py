import shogi
from typing import List
from app.analyze_usecase import AnalyzeUsecase




class Utils:
    @staticmethod
    def generate_kfk(filename):
        kif = AnalyzeUsecase.import_kif(filename)
        kif_moves = kif['moves']
        kif_sfen = kif['sfen']
        usi = AnalyzeUsecase.define_engine(kif_sfen)

        # define board
        board = shogi.Board()

        # 初手解析
        usi_position = f"sfen {kif_sfen}"
        kfk = KFK()

        for i, move in enumerate(kif_moves):
            # move = kif_moves[i]
            
            # print('usi_position:', usi_position)
            # usi_position += f" {move}"
            usi.usi_position(usi_position)
            # usi.send_command('multipv 1')
            usi.usi_go_and_wait_bestmove("btime 0 wtime 0 byoyomi 1000")
            pv = usi.think_result.pvs[0]
            pv_score = pv.eval 
            pv_moves = pv.pv.split(' ')
            pv_len = len(pv_moves)
            # 読み筋を取り込む
            pv_moves_jp = []
            for j, pv_move in enumerate(pv_moves):
                # print(f"{j}: {pv_move}", end=' ')
                pv_moves_jp.append(AnalyzeUsecase.generate_japanese_kif_move(board, pv_move))
            # print(''.join(pv_moves_jp))
            # print('pv_score:', pv_score)

            # 読み筋で取り込んだ手をすべて待ったする
            for _ in range(len(pv_moves)):
                board.pop()

            # print('move:', move)
            move_str = f'{i+1: > 4}', AnalyzeUsecase.generate_japanese_kif_move(board, move)
            # print(move_str)
            # print(board.kif_str())
            kfk.game_analysis.analysis_info_list.append(AnalysisInfo(move_str, pv_score, ''.join(pv_moves_jp)))
            
            if i == 0:
                usi_position += f" moves {move}"
            else:
                usi_position += f" {move}"

            if i == 50:
                break
        usi.disconnect()


class KFK:
    game_analysis: 'GameAnalysis'

    def __init__(self) -> None:
        self.game_analysis: 'GameAnalysis' = GameAnalysis()


class GameAnalysis:
    kif: str
    score_list: list
    engine_name: str
    time_per_move: int
    analysis_score_list: list = []
    analysis_info_list: List['AnalysisInfo'] = []


class AnalysisInfo:
    # move: str
    # score: int
    # pv: str

    def __init__(self, move, score, pv) -> None:
        self.move: str = move
        self.score: int = score
        self.pv: str = pv