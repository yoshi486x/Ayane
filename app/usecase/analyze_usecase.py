import shogi
import shogi.KIF

from src.models import EngineOptions
from src.engine.engine import UsiEngine
from src.settings import get_settings

settings = get_settings()


class AnalyzeUsecase:

    @staticmethod
    def main(filename):
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
            AnalyzeUsecase.print_kif_move(board, move)
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
            for j, pv_move in enumerate(pv_moves):
                print(f'({i}, {j}): ', end=' ')
                AnalyzeUsecase.print_kif_move(board, pv_move)

            # 読み筋で取り込んだ手をすべて待ったする
            for _ in range(len(pv_moves)):
                board.pop()

            if i == 50:
                break

        usi.disconnect()


    @staticmethod
    def import_kif(filename):
        # import kif
        print('path: ', settings.kifu_path + filename)
        kif = shogi.KIF.Parser.parse_file(settings.kifu_path + filename)[0]
        if kif is None:
            print('kif is None')
            exit(1)
        print('kif:', kif)
        print('black:', kif['names'][shogi.BLACK])
        print('white:', kif['names'][shogi.WHITE])

        return kif

    @staticmethod
    def define_engine(sfen: str):
        # set engine
        usi = UsiEngine(debug_print=True)
        # engine_options = EngineOptions(hash=4096, threads=4)
        engine_options = EngineOptions(hash=256, threads=4)
        usi.set_engine_options(engine_options.suisho())
        usi.connect(settings.engine_path)

        return usi

    @staticmethod
    def pv_handler(pv: str):
        pv_moves = pv.split(' ')
        print(pv_moves)
        # Copy Board or use the board and pop

    @staticmethod
    def print_kif_move(board, pv_move):
        # parse pv
        shogi_move = shogi.Move.from_usi(pv_move)
        from_square, to_square, promotion, drop_piece_type = shogi_move.from_square, shogi_move.to_square, shogi_move.promotion, shogi_move.drop_piece_type

        # 指し手
        print(f'{shogi.NUMBER_JAPANESE_NUMBER_SYMBOLS[shogi.file_index(to_square)+1]}{shogi.NUMBER_JAPANESE_KANJI_SYMBOLS[shogi.rank_index(to_square)+1]}', end='')
        if from_square is None and to_square is not None:
            # 打つ
            print(shogi.PIECE_JAPANESE_SYMBOLS[drop_piece_type]+'打')
        else:
            from_piece = board.piece_at(from_square)
            print(shogi.PIECE_JAPANESE_SYMBOLS[from_piece.piece_type], end='')
            if promotion:
                # 成る
                print('成', end='')
            # 
            print(f'({shogi.file_index(to_square)+1}{shogi.rank_index(to_square)+1})')
            
        board.push(shogi_move)
        return