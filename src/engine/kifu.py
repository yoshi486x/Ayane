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
