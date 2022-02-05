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


# 1対1での対局を管理してくれる補助クラス
class AyaneruServer:
    def __init__(self):

        # --- public members ---

        # 1P側、2P側のエンジンを生成して代入する。
        # デフォルトでは先手が1P側、後手が2P側になる。
        # self.flip_turn == Trueのときはこれが反転する。
        # ※　与えた開始局面のsfenが先手番から始まるとは限らないので注意。
        self.engines = [UsiEngine(), UsiEngine()]

        # デフォルト、0.1秒対局
        self.set_time_setting("byoyomi 100")

        # 引き分けとなる手数(これはユーザー側で変更して良い)
        self.moves_to_draw = 320

        # 先後プレイヤーを入れ替える機能。
        # self.engine(Turn)でエンジンを取得するときに利いてくる。
        # False : 1P = 先手 , 2P = 後手
        # True  : 1P = 後手 , 2P = 先手
        self.flip_turn = False

        # これをgame_start()呼び出し前にTrueにしておくと、エンジンの通信内容が標準出力に出力される。
        self.debug_print = False

        # これをgame_start()呼び出し前にTrueにしておくと、エンジンから"Error xxx"と送られてきたときにその内容が標準出力に出力される。
        self.error_print = False

        # --- publc readonly members

        # 現在の手番側
        self.side_to_move = Turn.BLACK

        # 現在の局面のsfen("startpos moves ..."や、"sfen ... move ..."の形)
        self.sfen = "startpos"

        # 初期局面からの手数
        self.game_ply = 1

        # 現在のゲーム状態
        # ゲームが終了したら、game_result.is_gameover() == Trueになる。
        self.game_result = GameResult.INIT

        # --- private memebers ---

        # 持ち時間残り [1P側 , 2P側] 単位はms。
        self.rest_time = [0, 0]

        # 対局の持ち時間設定
        # self.set_time_setting()で渡されたものをparseしたもの。
        self.time_setting = {}

        # 対局用スレッド
        self.game_thread: threading.Thread = None

        # 対局用スレッドの強制停止フラグ
        self.stop_thread: threading.Thread = False

    # turn側のplayer番号を取得する。(flip_turnを考慮する。)
    # 返し値
    # 0 : 1P側
    # 1 : 2P側
    def player_number(self, turn: Turn) -> int:
        if self.flip_turn:
            turn = turn.flip()
        return int(turn)

    # turn側のplayer名を取得する。(flip_turnを考慮する)
    # "1p" , "2p"という文字列が返る。
    def player_str(self, turn: Turn) -> str:
        return str(self.player_number(turn) + 1) + "p"

    # turn手番側のエンジンを取得する
    # flip_turn == Trueのときは、先手側がengines[1]、後手側がengines[0]になるので注意。
    def engine(self, turn: Turn) -> UsiEngine:
        return self.engines[self.player_number(turn)]

    # turn手番側の持ち時間の残り。
    # self.rest_timeはflip_turnの影響を受ける。
    def get_rest_time(self, turn: Turn) -> int:
        return self.rest_time[self.player_number(turn)]

    # 持ち時間設定を行う
    # time = 先後の持ち時間[ms]
    # time1p = 1p側 持ち時間[ms](1p側だけ個別に設定したいとき)
    # time2p = 2p側 持ち時間[ms](2p側だけ個別に設定したいとき)
    # byoyomi = 秒読み[ms]
    # byoyomi1p = 1p側秒読み[ms]
    # byoyomi2p = 2p側秒読み[ms]
    # inc = 1手ごとの加算[ms]
    # inc1p = 1p側のinc[ms]
    # inc2p = 2p側のinc[ms]
    #
    # 例 : "byoyomi 100" : 1手0.1秒
    # 例 : "time 900000" : 15分
    # 例 : "time1p 900000 time2p 900000 byoyomi 5000" : 15分 + 秒読み5秒
    # 例 : "time1p 10000 time2p 10000 inc 5000" : 10秒 + 1手ごとに5秒加算
    # 例 : "time1p 10000 time2p 10000 inc1p 5000 inc2p 1000" : 10秒 + 先手1手ごとに5秒、後手1手ごとに1秒加算
    def set_time_setting(self, setting: str):
        scanner = Scanner(setting.split())
        tokens = [
            "time",
            "time1p",
            "time2p",
            "byoyomi",
            "byoyomi1p",
            "byoyomi2p",
            "inc",
            "inc1p",
            "inc2p",
        ]
        time_setting = {}

        while not scanner.is_eof():
            token = scanner.get_token()
            param = scanner.get_token()
            # 使えない指定がないかのチェック
            if not token in tokens:
                raise ValueError("invalid token : " + token)
            int_param = int(param)
            time_setting[token] = int_param

        # "byoyomi"は"byoyomi1p","byoyomi2p"に敷衍する。("time" , "inc"も同様)
        for s in ["time", "byoyomi", "inc"]:
            if s in time_setting:
                inc_param = time_setting[s]
                time_setting[s + "1p"] = inc_param
                time_setting[s + "2p"] = inc_param

        # 0になっている項目があるとややこしいので0埋めしておく。
        for token in tokens:
            if not token in time_setting:
                time_setting[token] = 0

        self.time_setting = time_setting

    # ゲームを初期化して、対局を開始する。
    # エンジンはconnectされているものとする。
    # あとは勝手に思考する。
    # ゲームが終了するなどしたらgame_resultの値がINIT,PLAYINGから変化する。
    # そのあとself.sfenを取得すればそれが対局棋譜。
    # start_sfen : 開始局面をsfen形式で。省略すると平手の開始局面。
    # 例 : "startpos" , "startpos moves 7f7g" , "sfen ..." , "sfen ... moves ..."など。
    # start_gameply : start_sfenの開始手数。0を指定すると末尾の局面から。
    def game_start(self, start_sfen: str = "startpos", start_gameply: int = 0):

        # ゲーム対局中ではないか？これは前提条件の違反
        if self.game_result == GameResult.PLAYING:
            raise ValueError("must be gameover.")

        # 局面の設定
        sfen = start_sfen
        if "moves" not in sfen:
            sfen += " moves"

        # 開始手数。0なら無視(末尾の局面からなので)
        if start_gameply != 0:
            sp = sfen.split()
            # "moves"の文字列は上で追加しているので必ず存在すると仮定できる。
            index = min(sp.index("moves") + start_gameply - 1, len(sp) - 1)
            # sp[0]からsp[index]までの文字列を連結する。
            sfen = " ".join(sp[0 : index + 1])

        self.sfen = sfen

        for engine in self.engines:
            if not engine.is_connected():
                raise ValueError("engine is not connected.")
            engine.debug_print = self.debug_print
            engine.error_print = self.error_print

        # 1P側のエンジンを使って、現局面の手番を得る。
        self.side_to_move = self.engines[0].get_side_to_move()
        self.game_ply = 1
        self.game_result = GameResult.PLAYING

        for engine in self.engines:
            engine.send_command("usinewgame")  # いまから対局はじまるよー

        # 開始時 持ち時間
        self.rest_time = [
            self.time_setting["time1p"],
            self.time_setting["time2p"],
        ]

        # 対局用のスレッドを作成するのがお手軽か..
        self.game_thread = threading.Thread(target=self.game_worker)
        self.game_thread.start()

    # 対局スレッド
    def game_worker(self):

        while self.game_ply < self.moves_to_draw:
            # 手番側に属するエンジンを取得する
            # ※　flip_turn == Trueのときは相手番のほうのエンジンを取得するので注意。
            engine = self.engine(self.side_to_move)
            engine.usi_position(self.sfen)

            # 現在の手番側["1p" or "2p]の時間設定
            byoyomi_str = "byoyomi" + self.player_str(self.side_to_move)
            inctime_str = "inc" + self.player_str(self.side_to_move)
            inctime = self.time_setting[inctime_str]

            # inctimeが指定されていないならbyoymiを付与
            if inctime == 0:
                byoyomi_or_inctime_str = "byoyomi {0}".format(
                    self.time_setting[byoyomi_str]
                )
            else:
                byoyomi_or_inctime_str = "binc {0} winc {1}".format(
                    self.time_setting["inc" + self.player_str(Turn.BLACK)],
                    self.time_setting["inc" + self.player_str(Turn.WHITE)],
                )

            start_time = time.time()
            engine.usi_go_and_wait_bestmove(
                f"btime {self.get_rest_time(Turn.BLACK)} wtime {self.get_rest_time(Turn.WHITE)} {byoyomi_or_inctime_str}"
            )
            end_time = time.time()

            # 使用した時間を1秒単位で繰り上げて、残り時間から減算
            # プロセス間の通信遅延を考慮して300[ms]ほど引いておく。(秒読みの場合、どうせ使い切るので問題ないはず..)
            # 0.3秒以内に指すと0秒で指したことになるけど、いまのエンジン、詰みを発見したとき以外そういう挙動にはなりにくいのでまあいいや。
            elapsed_time = (end_time - start_time) - 0.3  # [ms]に変換
            elapsed_time = int(elapsed_time + 0.999) * 1000
            if elapsed_time < 0:
                elapsed_time = 0

            # 現在の手番を数値化したもの。1P側=0 , 2P側=1
            int_turn = self.player_number(self.side_to_move)
            self.rest_time[int_turn] -= int(elapsed_time)
            if (
                self.rest_time[int_turn] + self.time_setting[byoyomi_str] < -2000
            ):  # 秒読み含めて-2秒より減っていたら。0.1秒対局とかもあるので1秒繰り上げで引いていくとおかしくなる。
                self.game_result = GameResult.from_win_turn(self.side_to_move.flip())
                self.game_over()
                # 本来、自己対局では時間切れになってはならない。(計測が不確かになる)
                # 警告を表示しておく。
                print("Error! : player timeup")
                return
            # 残り時間がマイナスになっていたら0に戻しておく。
            if self.rest_time[int_turn] < 0:
                self.rest_time[int_turn] = 0

            bestmove = engine.think_result.bestmove
            if bestmove == "resign":
                # 相手番の勝利
                self.game_result = GameResult.from_win_turn(self.side_to_move.flip())
                self.game_over()
                return
            if bestmove == "win":
                # 宣言勝ち(手番側の勝ち)
                # 局面はノーチェックだが、まあエンジン側がバグっていなければこれでいいだろう)
                self.game_result = GameResult.from_win_turn(self.side_to_move)
                self.game_over()
                return

            self.sfen = self.sfen + " " + bestmove
            self.game_ply += 1

            # inctime分、時間を加算
            self.rest_time[int_turn] += inctime
            self.side_to_move = self.side_to_move.flip()
            # 千日手引き分けを処理しないといけないが、ここで判定するのは難しいので
            # max_movesで抜けることを期待。

            if self.stop_thread:
                # 強制停止なので試合内容は保証されない
                self.game_result = GameResult.STOP_GAME
                return

                # 引き分けで終了
        self.game_result = GameResult.MAX_MOVES
        self.game_over()

    # ゲームオーバーの処理
    # エンジンに対してゲームオーバーのメッセージを送信する。
    def game_over(self):
        result = self.game_result
        if result.is_draw():
            for engine in self.engines:
                engine.send_command("gameover draw")
        elif result.is_black_or_white_win():
            # resultをそのままintに変換したほうの手番側が勝利
            self.engine(Turn(result)).send_command("gameover win")
            self.engine(Turn(result).flip()).send_command("gameover lose")
        else:
            # それ以外サポートしてない
            raise ValueError("illegal result")

    # エンジンを終了させるなどの後処理を行う
    def terminate(self):
        self.stop_thread = True
        self.game_thread.join()
        for engine in self.engines:
            engine.disconnect()

    # エンジンを終了させる
    def __del__(self):
        self.terminate()
