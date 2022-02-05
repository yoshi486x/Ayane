from typing import List


# 思考エンジンから送られてきた読み筋を表現するクラス。
# "info pv ..."を解釈したもの。
# 送られてこなかった値に関してはNoneになっている。
class UsiThinkPV:
    def __init__(self):
        # --- public members ---

        # PV文字列。最善応手列。sfen表記文字列にて。
        # 例 : "7g7f 8c8d"みたいなの。あとは、split()して使ってもらえればと。
        # sfen以外の特殊表記として以下の文字列が混じっていることがあります。(やねうら王のdocs/解説.txtを参考にすること。)
        #  "rep_draw" : 普通の千日手
        #  "rep_sup"  : 優等局面(盤上の駒配置が同一で手駒が一方的に増えている局面への突入。相手からの歩の成り捨て～同金～歩打ち～金引きみたいな循環)
        #  "rep_inf"  : 劣等局面(盤上の駒配置が同一で手駒が一方的に減っている局面への突入)
        #  "rep_win"  : 王手を含む千日手(反則勝ち) // これ実際には出力されないはずだが…。
        #  "rep_lose" : 王手を含む千日手(反則負け) // これ実際には出力されないはずだが…。
        #  読み筋が宣言勝ちのときは読み筋の末尾に "win"
        #  投了の局面で呼び出されたとき "resign"
        self.pv = None  # str

        # 評価値(整数値)
        self.eval = None  # UsiEvalValue

        # 読みの深さ
        self.depth = None  # int

        # 読みの選択深さ
        self.seldepth = None  # int

        # 読みのノード数
        self.nodes = None  # int

        # "go"を送信してからの経過時刻。[ms]
        self.time = None  # int

        # hash使用率 1000分率
        self.hashfull = None  # int

        # nps
        self.nps = None  # int

        # bound
        self.bound = None  # UsiBound

    # 表示できる文字列化して返す。(主にデバッグ用)
    def to_string(self) -> str:
        s: List[str] = []
        self.append(s, "depth", self.depth)
        self.append(s, "seldepth", self.seldepth)
        if self.eval is not None:
            s.append(self.eval.to_string())
        if self.bound is not None:
            s.append("bound")
            s.append(self.bound.to_string())
        self.append(s, "nodes", self.nodes)
        self.append(s, "time", self.time)
        self.append(s, "hashfull", self.hashfull)
        self.append(s, "nps", self.nps)
        self.append(s, "pv", self.pv)

        return " ".join(s)

    # to_string()の下請け。str2がNoneではないとき、s[]に、str1とstr2をappendする。
    @classmethod
    def append(cls, s: List[str], str1: str, str2: str):
        if str2 is not None:
            s.append(str1)
            s.append(str2)


# 思考エンジンに対して送った"go"コマンドに対して思考エンジンから返ってきた情報を保持する構造体
class UsiThinkResult:
    def __init__(self):

        # --- public members ---

        # 最善手(sfen表記文字列にて。例:"7g7f")
        # "bestmove"を受信するまではNoneが代入されている。
        # "resign"(投了) , "win"(宣言勝ち) のような文字列もありうる。
        self.bestmove = None  # str

        # 最善手を指したあとの相手の指し手。(sfen表記文字列にて)
        # ない場合は、文字列で"none"。
        self.ponder = None  # str

        # 最善応手列
        # UsiThinkPVの配列。
        # MultiPVのとき、その数だけ要素を持つ配列になる。
        # 最後に送られてきた読み筋がここに格納される。
        self.pvs = []  # List[UsiThinkPV]

        # 詰め将棋エンジンの応答
        self.checkmate = None # str

    # このインスタンスの内容を文字列化する。(主にデバッグ用)
    def to_string(self) -> str:
        s = ""
        # pvを形にして出力する
        if len(self.pvs) == 1:
            s += self.pvs[0].to_string()
        elif len(self.pvs) >= 2:
            for i, p in enumerate(self.pvs):
                s += "multipv {0} {1}\n".format(i + 1, p.to_string())

        # bestmoveとponderを連結する。
        if self.bestmove is not None:
            s += "bestmove " + self.bestmove
        if self.ponder is not None:
            s += " ponder " + self.ponder
        return s
