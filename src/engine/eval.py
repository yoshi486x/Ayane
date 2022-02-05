from src.engine.enums import UsiEvalSpecialValue


# 評価値(Eval)を表現する型
class UsiEvalValue(int):
    # 詰みのスコアであるか
    def is_mate_score(self):
        return (
            UsiEvalSpecialValue.ValueMateInMaxPly
            <= self
            <= UsiEvalSpecialValue.ValueMate
        )

    # 詰まされるスコアであるか
    def is_mated_score(self):
        return (
            UsiEvalSpecialValue.ValueMated
            <= self
            <= UsiEvalSpecialValue.ValueMatedInMaxPly
        )

    # 評価値を文字列化する。
    def to_string(self):
        if self.is_mate_score():
            return "mate " + str(UsiEvalSpecialValue.ValueMate - self)
        elif self.is_mated_score():
            # マイナスの値で表現する。self == UsiEvalSpecialValue.ValueMated のときは -0と表現する。
            return "mate -" + str(self - UsiEvalSpecialValue.ValueMated)
        return "cp " + str(self)

    # ply手詰みのスコアを数値化する
    # UsiEvalValueを返したいが、このクラスの定義のなかでは自分の型を明示的に返せないようで..(コンパイラのバグでは..)
    # ply : integer
    @staticmethod
    def mate_in_ply(ply: int):  # -> UsiEvalValue
        return UsiEvalValue(int(UsiEvalSpecialValue.ValueMate) - ply)

    # ply手で詰まされるスコアを数値化する
    # ply : integer
    @staticmethod
    def mated_in_ply(ply: int):  # -> UsiEvalValue:
        return UsiEvalValue(-int(UsiEvalSpecialValue.ValueMate) + ply)
