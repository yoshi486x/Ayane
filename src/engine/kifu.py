# 対局棋譜、付随情報つき。
class GameKifu:
    def __init__(self):
        # --- public members ---

        # "startpos moves ..."のような対局棋譜
        self.sfen = None  # str

        # 1P側を後手にしたのか？
        self.flip_turn = False

        # 試合結果
        self.game_result = None  # GameResult
