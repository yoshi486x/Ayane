from enum import Enum, IntEnum


# 手番を表現するEnum
class Turn(IntEnum):
    BLACK = 0  # 先手
    WHITE = 1  # 後手

    # 反転させた手番を返す
    def flip(self) -> "Turn":
        return Turn(int(self) ^ 1)


# UsiEngineクラスのなかで用いるエンジンの状態を表現するenum
class UsiEngineState(Enum):
    WaitConnecting = 1  # 起動待ち
    Connected = 2  # 起動完了
    WaitReadyOk = 3  # "readyok"待ち
    WaitCommand = 4  # "position"コマンド等を送信できる状態になった
    WaitBestmove = 5  # "go"コマンドを送ったので"bestmove"が返ってくるのを待っている状態
    WaitOneLine = 6  # "moves"など1行応答を返すコマンドを送信したのでその1行が返ってくるのを待っている状態
    Disconnected = 999  # 終了した


# 特殊な評価値(Eval)を表現するenum
class UsiEvalSpecialValue(IntEnum):
    # 0手詰めのスコア(rootで詰んでいるときのscore)
    # 例えば、3手詰めならこの値より3少ない。
    ValueMate = 100000

    ValueMaxMatePly = 2000

    # ValueMaxMatePly(2000)手で詰むときのスコア
    ValueMateInMaxPly = ValueMate - ValueMaxMatePly

    # 詰まされるスコア
    ValueMated = -int(ValueMate)

    # ValueMaxMatePly(2000)手で詰まされるときのスコア
    ValueMatedInMaxPly = -int(ValueMateInMaxPly)

    # Valueの取りうる最大値(最小値はこの符号を反転させた値)
    # ValueInfinite = 100001

    # 無効な値
    ValueNone = 100002

# 読み筋として返ってきた評価値がfail low/highしたときのスコアであるか
class UsiBound(Enum):
    BoundNone = 0
    BoundUpper = 1
    BoundLower = 2
    BoundExact = 3

    # USIプロトコルで使う文字列化して返す。
    def to_string(self) -> str:
        if self == self.BoundUpper:
            return "upperbound"
        elif self == self.BoundLower:
            return "lowerbound"
        return ""
