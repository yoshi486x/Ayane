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


# ゲームの終局状態を示す
class GameResult(IntEnum):
    BLACK_WIN = 0  # 先手勝ち
    WHITE_WIN = 1  # 後手勝ち
    DRAW = 2  # 千日手引き分け(現状、サポートしていない)
    MAX_MOVES = 3  # 最大手数に到達
    ILLEGAL_MOVE = 4  # 反則の指し手が出た
    INIT = 5  # ゲーム開始前
    PLAYING = 6  # まだゲーム中
    STOP_GAME = 7  # 強制stopさせたので結果は保証されず

    # win_turn側が勝利したときの定数を返す
    @staticmethod
    def from_win_turn(win_turn: Turn) -> int:  # GameResult(IntEnum)
        return GameResult.BLACK_WIN if win_turn == Turn.BLACK else GameResult.WHITE_WIN

    # ゲームは引き分けであるのか？
    def is_draw(self) -> bool:
        return self == GameResult.DRAW or self == GameResult.MAX_MOVES

    # 先手か後手が勝利したか？
    def is_black_or_white_win(self) -> bool:
        return self == GameResult.BLACK_WIN or self == GameResult.WHITE_WIN

    # ゲームの決着がついているか？
    def is_gameover(self) -> bool:
        return self != GameResult.INIT and self != GameResult.PLAYING

    # 1P側が勝利したのか？
    # flip_turn : AyaneruServer.flip_turnを渡す
    def is_player1_win(self, flip_turn: bool) -> bool:
        # ""== True"とかクソダサいけど、対称性があって綺麗なのでこう書いておく。
        return (self == GameResult.BLACK_WIN and (not flip_turn)) or (
            self == GameResult.WHITE_WIN and flip_turn
        )
