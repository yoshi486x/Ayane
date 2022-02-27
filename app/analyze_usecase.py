import shogi
import shogi.KIF, shogi.CSA
import xml

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
            # print(''.join(pv_moves_jp))

            # 読み筋で取り込んだ手をすべて待ったする
            for _ in range(len(pv_moves)):
                board.pop()

            if i == 50:
                break

        usi.disconnect()


    @staticmethod
    def import_kif(filename, filetype='kif'):
        # import kif
        print('path: ', settings.kifu_path + filename)
        if filetype == 'kif':
            kif = shogi.KIF.Parser.parse_file(settings.kifu_path + filename)[0]
        elif filetype == 'csa':
            kif = shogi.CSA.Parser.parse_file(settings.kifu_path + filename)[0]
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
    def generate_japanese_kif_move(board, pv_move):
        turn_icon = '▲'
        to_code = ''
        piece = ''
        special_action = ''
        from_code = ''

        # parse pv
        shogi_move = shogi.Move.from_usi(pv_move)
        from_square, to_square, promotion, drop_piece_type = shogi_move.from_square, shogi_move.to_square, shogi_move.promotion, shogi_move.drop_piece_type

        #先後
        if board.turn == shogi.WHITE:
            turn_icon = '△'
        # 指し手        
        to_square_usi = shogi.SQUARE_NAMES[to_square]
        to_code = f'{JAPANESE_NUMBERS[NUMBERS.index(to_square_usi[0])]}{JAPANESE_KANJI_NUMBERS[ALFABET.index(to_square_usi[1])]}'
        if from_square is None and to_square is not None:
            # 打つ
            piece = shogi.PIECE_JAPANESE_SYMBOLS[drop_piece_type]
            special_action = '打'
        else:
            from_piece = board.piece_at(from_square)
            piece = shogi.PIECE_JAPANESE_SYMBOLS[from_piece.piece_type]
            if promotion:
                # 成る
                piece = shogi.PIECE_JAPANESE_SYMBOLS[from_piece.piece_type]
                special_action = '成'
            from_square_usi = shogi.SQUARE_NAMES[from_square]
            from_code = f'({from_square_usi[0]}{NUMBERS[ALFABET.index(from_square_usi[1])]})'
            
        board.push(shogi_move)
        return f"{turn_icon}{to_code}{piece}{special_action}{from_code}"


NUMBERS = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
JAPANESE_KANJI_NUMBERS =  ['一', '二', '三', '四', '五', '六', '七', '八', '九']
JAPANESE_NUMBERS =  ['１', '２', '３', '４', '５', '６', '７', '８', '９']
ALFABET = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']
