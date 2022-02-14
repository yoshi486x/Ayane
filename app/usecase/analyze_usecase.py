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
        # board.push()

        usi_position += f" moves"
        # for move in kif_moves:
        for i in range(len(kif_moves)):
            move = kif_moves[i]
            print(move)
            usi_position += f" {move}"
            usi.usi_position(usi_position)
            # usi.send_command('multipv 1')
            usi.usi_go_and_wait_bestmove("btime 0 wtime 0 byoyomi 1000")
            pv = usi.think_result.pvs[0]
            # AnalyzeUsecase.pv_handler(pv)
            # print('pvs:', usi.think_result.pvs)
            # print('pv:', pv)
            # print('pv.pv:', pv.pv)
            # print('type(pv.pv):', type(pv.pv))
            
            pv_moves = pv.pv.split(' ')
            # print(pv_moves)
            pv_len = len(pv_moves)
            # 読み筋を取り込む
            # for pv_move in pv_moves:
            for j, pv_move in enumerate(pv_moves):
                print(f'({i}, {j}): ', end=' ')
                # parse pv
                shogi_move = shogi.Move.from_usi(pv_move)
                from_square, to_square, promotion, drop_piece_type = shogi_move.from_square, shogi_move.to_square, shogi_move.promotion, shogi_move.drop_piece_type

                # from_square_name = shogi.SQUARE_NAMES[shogi_move.from_square]
                # to_square_name = shogi.SQUARE_NAMES[shogi_move.to_square]
                if to_square is None:
                    print(' no to_square')
                    exit(1)
                print(f'{shogi.NUMBER_JAPANESE_NUMBER_SYMBOLS[shogi.file_index(to_square)+1]}{shogi.NUMBER_JAPANESE_KANJI_SYMBOLS[shogi.rank_index(to_square)+1]}', end='')
                if from_square is None and to_square is not None:
                    # 打つ
                    print(shogi.PIECE_JAPANESE_SYMBOLS[drop_piece_type], f'(drop_piece_type)', drop_piece_type)
                    # print(f'{i}: jp_piece_type:', shogi.PIECE_JAPANESE_SYMBOLS[drop_piece_type])
                else:
                    from_piece = board.piece_at(from_square)
                    if from_piece is None:
                        print(f' no from_piece, {pv_move}')
                        continue
                    print(shogi.PIECE_JAPANESE_SYMBOLS[from_piece.piece_type], f'(from_piece)', from_piece.piece_type)
                    # print('from_piece:', shogi.PIECE_JAPANESE_SYMBOLS[from_piece.piece_type])
                    if promotion:
                        # 成る
                        pass
                    else:
                        pass

                board.push(shogi_move)
            
            # 読み筋で取り込んだ手をすべて待ったする
            for _ in range(len(pv_moves) - 1):
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
    def print_kif_move():
        