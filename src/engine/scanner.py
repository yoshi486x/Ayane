from typing import List


# 文字列のparseを行うもの。
class Scanner:
    # argsとしてstr[]を渡しておく。
    # args[index]のところからスキャンしていく。
    def __init__(self, args: List[str], index: int = 0):
        self.args = args
        self.index = index

    # 次のtokenを覗き見する。tokenがなければNoneが返る。
    # indexは進めない
    def peek_token(self):
        if self.is_eof():
            return None
        return self.args[self.index]

    # 次のtokenを取得して文字列として返す。indexを1進める。
    def get_token(self):
        if self.is_eof():
            return None
        token = self.args[self.index]
        self.index += 1
        return token

    # 次のtokenを取得して数値化して返す。indexを1進める。
    def get_integer(self):
        if self.is_eof():
            return None
        token = self.args[self.index]
        self.index += 1
        try:
            return int(token)
        except:
            return None

    # indexが配列の末尾まで行ってればtrueが返る。
    def is_eof(self) -> bool:
        return len(self.args) <= self.index

    # index以降の文字列を連結して返す。
    # indexは配列末尾を指すようになる。(is_eof()==Trueを返すようになる)
    def rest_string(self) -> str:
        rest = " ".join(self.args[self.index :])
        self.index = len(self.args)
        return rest

    # 元の配列をスペースで連結したものを返す。
    def get_original_text(self) -> str:
        return " ".join(self.args)
