import random
import threading
import time

from game_result import GameResult
from kifu import GameKifu
from server import AyaneruServer
from rating import EloRating


# 並列自己対局のためのクラス
class MultiAyaneruServer:
    def __init__(self):

        # --- public members ---

        # 定跡(= 開始局面の集合 , このなかからランダムに1つ選ばれる)
        self.start_sfens = ["startpos"]  # List[str]

        # 定跡の開始手数。この手数の局面から開始する。
        # 0を指定すると末尾の局面から。
        self.start_gameply = 1

        # 1ゲームごとに手番を入れ替える。
        self.flip_turn_every_game = True

        # これをinit_server()呼び出し前にTrueにしておくと、エンジンの通信内容が標準出力に出力される。
        self.debug_print = False

        # これをinit_server()呼び出し前にTrueにしておくと、エンジンから"Error xxx"と送られてきたときにその内容が標準出力に出力される。
        self.error_print = False

        # --- public readonly members ---

        # 対局サーバー群
        self.servers = []  # List[AyaneruServer]

        # 対局棋譜
        self.game_kifus = []  # List[GameKifu]

        # 終了した試合数。
        self.total_games = 0

        # player1が勝利したゲーム数
        self.player1_win = 0
        # player2が勝利したゲーム数
        self.player2_win = 0

        # 先手の勝利したゲーム数
        self.black_win = 0
        # 後手の勝利したゲーム数
        self.white_win = 0

        # 引き分けたゲーム数
        self.draw_games = 0

        # --- private members ---

        # game_start()のあとこれをTrueにするとすべての対局が停止する。
        self.game_stop_flag = False

        # 対局監視用のスレッド
        self.game_thread: threading.Thread = None

    # 対局サーバーを初期化する
    # num = 用意する対局サーバーの数(この数だけ並列対局する)
    def init_server(self, num: int):
        servers = []
        for _ in range(num):
            server = AyaneruServer()
            server.debug_print = self.debug_print
            server.error_print = self.error_print
            servers.append(server)
        self.servers = servers

    # init_serverのあと、1P側、2P側のエンジンを初期化する。
    # player : 0なら1P側、1なら2P側
    def init_engine(self, player: int, engine_path: str, engine_options: dict):
        for server in self.servers:
            engine = server.engines[player]
            engine.set_engine_options(engine_options)
            engine.connect(engine_path)

    # すべてのあやねるサーバーに持ち時間設定を行う。
    # AyaneruServer.set_time_setting()と設定の仕方は同じ。
    def set_time_setting(self, time_setting: str):
        for server in self.servers:
            server.set_time_setting(time_setting)

    # すべての対局を開始する
    def game_start(self):
        if len(self.servers) == 0:
            raise ValueError("No Servers. Must call init_server()")

        self.total_games = 0
        self.player1_win = 0
        self.player2_win = 0
        self.black_win = 0
        self.white_win = 0
        self.draw_games = 0

        self.game_stop_flag = False

        flip = False
        # それぞれの対局、1個ごとに先後逆でスタートしておく。
        for server in self.servers:
            server.flip_turn = flip
            if self.flip_turn_every_game:
                flip ^= True
            # 対局を開始する
            self.start_server(server)

        # 対局用のスレッドを作成するのがお手軽か..
        self.game_thread = threading.Thread(target=self.game_worker)
        self.game_thread.start()

    # game_start()で開始したすべての対局を停止させる。
    def game_stop(self):
        if self.game_thread is None:
            raise ValueError("game thread is not running.")
        self.game_stop_flag = True
        self.game_thread.join()
        self.game_thread = None

    # 対局結果("70-3-50"みたいな1P勝利数 - 引き分け - 2P勝利数　と、その勝率から計算されるレーティング差を文字列化して返す)
    def game_info(self) -> str:
        elo = self.game_rating()
        return elo.pretty_string

    # Eloレーティングを計算して返す。(EloRating型を)
    def game_rating(self) -> EloRating:
        elo = EloRating()
        elo.player1_win = self.player1_win
        elo.player2_win = self.player2_win
        elo.black_win = self.black_win
        elo.white_win = self.white_win
        elo.draw_games = self.draw_games
        elo.calc()
        return elo

    # ゲーム対局用のスレッド
    def game_worker(self):

        while not self.game_stop_flag:
            for server in self.servers:
                # 対局が終了しているサーバーがあるなら次のゲームを開始する。
                if server.game_result.is_gameover():
                    self.restart_server(server)
            time.sleep(1)

        # serverの解体もしておく。
        for server in self.servers:
            server.terminate()
        self.servers = []

    # 結果を集計、棋譜の保存
    def count_result(self, server: AyaneruServer):
        result = server.game_result

        # 終局内容に応じて戦績を加算
        if result.is_black_or_white_win():
            if result.is_player1_win(server.flip_turn):
                self.player1_win += 1
            else:
                self.player2_win += 1
            if result == GameResult.BLACK_WIN:
                self.black_win += 1
            else:
                self.white_win += 1
        else:
            self.draw_games += 1
        self.total_games += 1

        # 棋譜を保存しておく。
        kifu = GameKifu()
        kifu.sfen = server.sfen
        kifu.flip_turn = server.flip_turn
        kifu.game_result = server.game_result
        self.game_kifus.append(kifu)

    # 対局サーバーを開始する。
    def start_server(self, server: AyaneruServer):
        # sfenをstart_sfensのなかから一つランダムに取得
        sfen = self.start_sfens[random.randint(0, len(self.start_sfens) - 1)]
        server.game_start(sfen, self.start_gameply)

    # 対局結果を集計して、サーバーを再開(次の対局を開始)させる。
    def restart_server(self, server: AyaneruServer):
        # 対局結果の集計
        self.count_result(server)

        # flip_turnを反転させておく。(1局ごとに手番を入れ替え)
        if self.flip_turn_every_game:
            server.flip_turn ^= True

        # 終了していたので再開
        self.start_server(server)

    # 内包しているすべてのあやねるサーバーを終了させる。
    def terminate(self):
        if self.game_thread is not None:
            self.game_stop()

    def __del__(self):
        self.terminate()
