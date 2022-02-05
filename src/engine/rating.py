import threading
import subprocess
import time
import os
import math
import random
import io
from queue import Queue
from enum import Enum
from enum import IntEnum
from datetime import datetime
from typing import Optional, Union, cast
from typing import List, Tuple, Dict
from settings import get_settings


class EloRating:
    def __init__(self):

        # --- public members ---

        # 1P側の勝利回数
        self.player1_win = 0

        # 2P側の勝利回数
        self.player2_win = 0

        # 先手側の勝利回数
        self.black_win = 0

        # 後手側の勝利回数
        self.white_win = 0

        # 引き分けの回数
        self.draw_games = 0

        # --- public readonly members ---

        # 勝率1P側
        self.win_rate = 0

        # 勝率先手側,後手側
        self.win_rate_black = 0
        self.win_rate_white = 0

        # 1P側は2P側よりどれだけratingが勝るか
        self.rating = 0

        # ratingの差の信頼下限,信頼上限
        self.rating_lowerbound = 0
        self.rating_upperbound = 0

        # レーティング差についてユーザーに見やすい形での文字列
        self.pretty_string = ""

    # このクラスのpublic membersのところを設定して、このcalc()を呼び出すと、
    # レーティングなどが計算されて、public readonly membersのところに反映される。
    def calc(self):

        # 引き分け以外の有効な試合数
        total = float(self.player1_win + self.player2_win)

        if total != 0:
            # 普通の勝率
            self.win_rate = self.player1_win / total
            # 先手番/後手番のときの勝率内訳
            self.win_rate_black = self.black_win / total
            self.win_rate_white = self.white_win / total
        else:
            self.win_rate = 0
            self.win_rate_black = 0
            self.win_rate_white = 0

        # if self.win_rate == 0 or self.win_rate == 1:
        #     self.rating = 0 # 計測不能
        #     rating_str = ""
        # else:

        # →　勝率0% or 100%でも計算はしたほうがいいな。

        self.rating = round(self.calc_rating(self.win_rate), 2)
        rating_str = (
            " R"
            + str(self.rating)
            + "["
            + str(round(EloRating.calc_rating_lowerbound(self.win_rate, total), 2))
            + ","
            + str(round(EloRating.calc_rating_upperbound(self.win_rate, total), 2))
            + "]"
        )

        self.pretty_string = (
            str(self.player1_win)
            + " - "
            + str(self.draw_games)
            + " - "
            + str(self.player2_win)
            + "("
            + str(round(self.win_rate * 100, 2))
            + "%"
            + rating_str
            + ")"
            + " winrate black , white = "
            + str(round(self.win_rate_black * 100, 2))
            + "% , "
            + str(round(self.win_rate_white * 100, 2))
            + "%"
        )

    # cf. http://tadaoyamaoka.hatenablog.com/entry/2017/06/14/203529
    # ここで、rは勝率、nは対局数で、棄却域Rは、有意水準α=0.05とするとR>1.644854となる。

    # r : 実際の対局の勝率 , p0 : 判定したい勝率 , n : 対局数 が 有意水準 0.05で有意かを判定する。
    # def hypothesis_testing(r,n,p0):
    #    return (r - p0)/math.sqrt(p0 * (1-p0)/n) > 1.644854

    # r : 実際の対局の勝率 , n : 対局数 が 有意水準 0.05で有意なp0を返す
    # 上の数式をp0に関して解析的に解く
    @staticmethod
    def solve_hypothesis_testing(r, n):
        a = 1.644854
        return (
            a ** 2
            - math.sqrt(a ** 4 - 4 * (a ** 2) * n * (r ** 2) + 4 * (a ** 2) * n * r)
            + 2 * n * r
        ) / (2 * (a ** 2 + n))
        # cf.
        # https://www.wolframalpha.com/input/?i=(r+-+x)%2Fsqrt(x+*+(1-x)%2Fn)+%3D+a

    # 勝率が与えられたときにレーティングを返す
    @staticmethod
    def calc_rating(r):
        if r == 0:
            return -9999
        if r == 1:
            return +9999
        return -400 * math.log(1 / r - 1, 10)
        # log(x)は自然対数なので、底を10にするならlog(x,10)と書かないといけない。

    # 勝率r,対局数nが与えられたときにレーティングの下限値を返す(信頼下限)
    @staticmethod
    def calc_rating_lowerbound(r, n):
        p0 = EloRating.solve_hypothesis_testing(r, n)
        return EloRating.calc_rating(p0)

    # 勝率r,対局数nが与えられたときにレーティングの上限値を返す(信頼上限)
    @staticmethod
    def calc_rating_upperbound(r, n):
        # 相手側から見た勝率と、相手側から見た信頼下限を出して、その符号を反転させれば良い
        p0 = EloRating.solve_hypothesis_testing(1 - r, n)
        return -EloRating.calc_rating(p0)
