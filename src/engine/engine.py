import os
import subprocess
import threading
from queue import Queue
from typing import Dict, Optional, Union, cast

from src.engine.enums import Turn, UsiEngineState, UsiEvalSpecialValue, UsiBound
from src.engine.eval import UsiEvalValue, UsiEvalSpecialValue
from src.engine.scanner import Scanner
from src.engine.service import UsiThinkResult, UsiThinkPV


# USIプロトコルを用いて思考エンジンとやりとりするためのwrapperクラス
class UsiEngine:
    def __init__(self):

        # --- public members ---

        # 通信内容をprintで表示する(デバッグ用)
        self.debug_print = False

        # エンジン側から"Error"が含まれている文字列が返ってきたら、それをprintで表示する。
        # これはTrueにしておくのがお勧め。
        self.error_print = True

        self.think_result = None  # UsiThinkResult

        # --- readonly members ---
        # (外部からこれらの変数は書き換えないでください)

        # エンジンの格納フォルダ
        # Connect()を呼び出したときに代入される。(readonly)
        self.engine_path = None
        self.engine_fullpath = None

        # エンジンとのやりとりの状態を表現する。(readonly)
        self.engine_state: Optional[UsiEngineState] = None

        # connect()のあと、エンジンが終了したときの状態
        # エラーがあったとき、ここにエラーメッセージ文字列が入る
        # エラーがなく終了したのであれば0が入る。(readonly)
        self.exit_state: Optional[Union[int, str]] = None

        # --- private members ---

        # エンジンのプロセスハンドル
        self.proc: Optional[subprocess.Popen] = None

        # エンジンとやりとりするスレッド
        self.read_thread: threading.Thread = None
        self.write_thread: threading.Thread = None

        # エンジンに設定するオプション項目。
        # 例 : {"Hash":"128","Threads":"8"}
        self.options: Dict[str, str] = None

        # 最後にエンジン側から受信した1行
        self.last_received_line: Optional[str] = None

        # エンジンにコマンドを送信するためのqueue(送信スレッドとのやりとりに用いる)
        self.send_queue = Queue()

        # print()を呼び出すときのlock object
        self.lock_object = threading.Lock()

        # engine_stateが変化したときのイベント用
        self.state_changed_cv = threading.Condition()

        # このクラスのインスタンスの識別用ID。
        # 念の為、lockしてから参照/インクリメントを行う。
        with UsiEngine.static_lock_object:
            self.instance_id = UsiEngine.static_count
            UsiEngine.static_count += 1

    # --- private static members ---

    # 静的メンバ変数とする。UsiEngineのインスタンスの数を記録する
    static_count = 0

    # ↑の変数を変更するときのlock object
    static_lock_object = threading.Lock()

    # engineに渡すOptionを設定する。
    # 基本的にエンジンは"engine_options.txt"で設定するが、Threads、Hashなどあとから指定したいものもあるので
    # それらについては、connectの前にこのメソッドを呼び出して設定しておく。
    # 例) usi.set_engine_options({"Hash":"128","Threads":"8"})
    def set_engine_options(self, options: Dict[str, str]):
        self.options = options

    # エンジンに接続する
    # enginePath : エンジンPathを指定する。
    # エンジンが存在しないときは例外がでる。
    def connect(self, engine_path: str):
        self.disconnect()

        # engine_stateは、disconnect()でUsiEngineState.DisconnectedになってしまうのでいったんNoneに設定してリセット。
        # 以降は、この変数は、__change_state()を呼び出して変更すること。
        self.engine_state = None
        self.exit_state = None
        self.engine_path = engine_path

        # write workerに対するコマンドqueue
        self.send_queue = Queue()

        # 最後にエンジン側から受信した行
        self.last_received_line = None

        # 実行ファイルの存在するフォルダ
        self.engine_fullpath = os.path.join(os.getcwd(), self.engine_path)
        self.change_state(UsiEngineState.WaitConnecting)

        # subprocess.Popen()では接続失敗を確認する手段がないくさいので、
        # 事前に実行ファイルが存在するかを調べる。
        if not os.path.exists(self.engine_fullpath):
            self.change_state(UsiEngineState.Disconnected)
            self.exit_state = "Connection Error"
            raise FileNotFoundError(self.engine_fullpath + " not found.")

        self.proc = subprocess.Popen(
            self.engine_fullpath,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            encoding="utf-8",
            cwd=os.path.dirname(self.engine_fullpath),
        )

        # self.send_command("usi")
        # "usi"コマンドを先行して送っておく。
        # →　オプション項目が知りたいわけでなければエンジンに対して"usi"、送る必要なかったりする。
        # また、オプション自体は、"engine_options.txt"で設定されるものとする。

        self.change_state(UsiEngineState.Connected)

        # 読み書きスレッド
        self.read_thread = threading.Thread(target=self.read_worker)
        self.read_thread.start()
        self.write_thread = threading.Thread(target=self.write_worker)
        self.write_thread.start()

    # エンジンのconnect()が呼び出されたあとであるか
    def is_connected(self) -> bool:
        return self.proc is not None

    # エンジン用のプロセスにコマンドを送信する(プロセスの標準入力にメッセージを送る)
    def send_command(self, message: str):
        self.send_queue.put(message)

    # エンジン用のプロセスを終了する
    def disconnect(self):
        if self.proc is not None:
            self.send_command("quit")
            # スレッドをkillするのはpythonでは難しい。
            # エンジンが行儀よく動作することを期待するしかない。
            # "quit"メッセージを送信して、エンジン側に終了してもらうしかない。

        if self.read_thread is not None:
            self.read_thread.join()
            self.read_thread = None

        if self.write_thread is not None:
            self.write_thread.join()
            self.write_thread = None

        # GCが呼び出されたときに回収されるはずだが、UnitTestでresource leakの警告が出るのが許せないので
        # この時点でclose()を呼び出しておく。
        if self.proc is not None:
            self.proc.stdin.close()
            self.proc.stdout.close()
            self.proc.stderr.close()
            self.proc.terminate()

        self.proc = None
        self.change_state(UsiEngineState.Disconnected)

    # 指定したUsiEngineStateになるのを待つ
    # disconnectedになってしまったら例外をraise
    def wait_for_state(self, state: UsiEngineState):
        while True:
            with self.state_changed_cv:
                if self.engine_state == state:
                    return
                if self.engine_state == UsiEngineState.Disconnected:
                    raise ValueError("engine_state == UsiEngineState.Disconnected.")

                # Eventが変化するのを待機する。
                self.state_changed_cv.wait()

    # [SYNC] usi_position()で設定した局面に対する合法手の指し手の集合を得る。
    # USIプロトコルでの表記文字列で返ってくる。
    # すぐに返ってくるはずなのでブロッキングメソッド
    # "moves"は、やねうら王でしか使えないUSI拡張コマンド
    def get_moves(self) -> str:
        return self.send_command_and_getline("moves")

    # [SYNC] usi_position()で設定した局面に対する手番を得る。
    # "side"は、やねうら王でしか使えないUSI拡張コマンド
    def get_side_to_move(self) -> Turn:
        line = self.send_command_and_getline("side")
        return Turn.BLACK if line == "black" else Turn.WHITE

    # --- エンジンに対して送信するコマンド ---
    # メソッド名の先頭に"usi_"と付与してあるものは、エンジンに対してUSIプロトコルで送信するの意味。

    # [ASYNC]
    # 局面をエンジンに送信する。sfen形式。
    # 例 : "startpos moves ..."とか"sfen ... moves ..."みたいな形式
    # 「USIプロトコル」でググれ。
    def usi_position(self, sfen: str):
        self.send_command("position " + sfen)

    # [ASYNC]
    # position_command()のあと、エンジンに思考させる。
    # options :
    #  "infinite" : stopを送信するまで無限に考える。
    #  "btime 10000 wtime 10000 byoyomi 3000" : 先手、後手の持ち時間 + 秒読みの持ち時間を指定して思考させる。単位は[ms]
    #  "depth 10" : 深さ10固定で思考させる
    # self.think_result.bestmove != Noneになったらそれがエンジン側から返ってきた最善手なので、それを以て、go_commandが完了したとみなせる。
    def usi_go(self, options: str):
        self.think_result = UsiThinkResult()
        self.send_command("go " + options)

    # [SYNC]
    # go_command()を呼び出して、そのあとbestmoveが返ってくるまで待つ。
    # 思考結果はself.think_resultから取り出せる。
    def usi_go_and_wait_bestmove(self, options: str):
        self.usi_go(options)
        self.wait_bestmove()

    # [SYNC]
    # go_command()を呼び出して、そのあとcheckmateが返ってくるまで待つ。
    # 思考結果はself.think_resultから取り出せる。
    def usi_go_and_wait_checkmate(self, options: str):
        self.usi_go(options)
        self.wait_checkmate()

    # [ASYNC]
    # エンジンに対してstopを送信する。
    # "go infinite"で思考させたときに停止させるのに用いる。
    # self.think_result.bestmove != Noneになったらそれがエンジン側から返ってきた最善手なので、それを以て、go_commandが完了したとみなせる。
    def usi_stop(self):
        self.send_command("stop")

    # [SYNC]
    # bestmoveが返ってくるのを待つ
    # self.think_result.bestmoveからbestmoveを取り出すことができる。
    def wait_bestmove(self):
        with self.state_changed_cv:
            self.state_changed_cv.wait_for(
                lambda: self.think_result.bestmove is not None
            )

    # [SYNC]
    # checkmateが返ってくるのを待つ
    # self.think_result.checkmateから詰み筋を取り出すことができる。
    def wait_checkmate(self):
        with self.state_changed_cv:
            self.state_changed_cv.wait_for(
                lambda: self.think_result.checkmate is not None
            )

    # --- エンジンに対するコマンド、ここまで ---

    # [SYNC] エンジンに対して1行送って、すぐに1行返ってくるので、それを待って、この関数の返し値として返す。
    def send_command_and_getline(self, command: str) -> str:
        self.wait_for_state(UsiEngineState.WaitCommand)
        self.last_received_line = None
        with self.state_changed_cv:
            self.send_command(command)

            # エンジン側から一行受信するまでblockingして待機
            self.state_changed_cv.wait_for(lambda: self.last_received_line is not None)
            return cast(str, self.last_received_line)

    # エンジンとのやりとりを行うスレッド(read方向)
    def read_worker(self):
        while True:
            line = self.proc.stdout.readline()
            # プロセスが終了した場合、line = Noneのままreadline()を抜ける。
            if line:
                self.dispatch_message(line.strip())

            # プロセスが生きているかのチェック
            retcode = self.proc.poll()
            if not line and retcode is not None:
                self.exit_state = 0
                # エラー以外の何らかの理由による終了
                break

    # エンジンとやりとりを行うスレッド(write方向)
    def write_worker(self):

        if self.options is not None:
            for k, v in self.options.items():
                self.send_command(f"setoption name {k} value {v}")

        self.send_command("isready")  # 先行して"isready"を送信
        self.change_state(UsiEngineState.WaitReadyOk)

        try:
            while True:
                message = self.send_queue.get()

                # 先頭の文字列で判別する。
                messages = message.split()
                if len(messages):
                    token = messages[0]
                else:
                    token = ""

                # stopコマンドではあるが、goコマンドを送信していないなら送信しない。
                if token == "stop":
                    if self.engine_state != UsiEngineState.WaitBestmove:
                        continue
                elif token == "go":
                    self.wait_for_state(UsiEngineState.WaitCommand)
                    self.change_state(UsiEngineState.WaitBestmove)
                # positionコマンドは、WaitCommand状態でないと送信できない。
                elif token == "position":
                    self.wait_for_state(UsiEngineState.WaitCommand)
                elif token == "moves" or token == "side":
                    self.wait_for_state(UsiEngineState.WaitCommand)
                    self.change_state(UsiEngineState.WaitOneLine)
                elif token == "usinewgame" or token == "gameover":
                    self.wait_for_state(UsiEngineState.WaitCommand)

                self.proc.stdin.write(message + "\n")
                self.proc.stdin.flush()
                if self.debug_print:
                    self.print("[{0}:<] {1}".format(self.instance_id, message))

                if token == "quit":
                    self.change_state(UsiEngineState.Disconnected)
                    # 終了コマンドを送信したなら自発的にこのスレッドを終了させる。
                    break

                retcode = self.proc.poll()
                if retcode is not None:
                    break

        except:
            self.exit_state = f"{self.instance_id} : Engine error write_worker failed , EngineFullPath = {self.engine_fullpath}"

    # 排他制御をするprint(このクラスからの出力に関してのみ)
    def print(self, mes: str):

        with self.lock_object:
            print(mes)
            # SingletonLog.get_log().print(mes)
            # などとすればファイルに書き出せる。

    # self.engine_stateを変更する。
    def change_state(self, state: UsiEngineState):
        # 切断されたあとでは変更できない
        if self.engine_state == UsiEngineState.Disconnected:
            return
        # goコマンドを送ってWaitBestmoveに変更する場合、現在の状態がWaitCommandでなければならない。
        if state == UsiEngineState.WaitBestmove:
            if self.engine_state != UsiEngineState.WaitCommand:
                raise ValueError(
                    "{0} : can't send go command when self.engine_state != UsiEngineState.WaitCommand".format(
                        self.instance_id
                    )
                )

        with self.state_changed_cv:
            self.engine_state = state
            self.state_changed_cv.notify_all()

    # エンジン側から送られてきたメッセージを解釈する。
    def dispatch_message(self, message: str):
        # デバッグ用に受け取ったメッセージを出力するのか？
        if self.debug_print or (self.error_print and message.find("Error") > -1):
            self.print("[{0}:>] {1}".format(self.instance_id, message))

        # 最後に受信した文字列はここに積む約束になっている。
        self.last_received_line = message

        # 先頭の文字列で判別する。
        index = message.find(" ")
        if index == -1:
            token = message
        else:
            token = message[0:index]

        # --- handleするメッセージ

        # 1行待ちであったなら、これでハンドルしたことにして返る。
        if self.engine_state == UsiEngineState.WaitOneLine:
            self.change_state(UsiEngineState.WaitCommand)
            return
        # "isready"に対する応答
        elif token == "readyok":
            self.change_state(UsiEngineState.WaitCommand)
        # "go"に対する応答
        elif token == "bestmove":
            self.handle_bestmove(message)
            self.change_state(UsiEngineState.WaitCommand)
        # エンジンの読み筋に対する応答
        elif token == "info":
            self.handle_info(message)
        # 詰め将棋エンジンに対する応答
        elif token=="checkmate":
            self.handle_checkmate(message)
            self.change_state(UsiEngineState.WaitCommand)

    # エンジンから送られてきた"bestmove"を処理する。
    def handle_bestmove(self, message: str):
        messages = message.split()
        if len(messages) >= 4 and messages[2] == "ponder":
            self.think_result.ponder = messages[3]

        if len(messages) >= 2:
            self.think_result.bestmove = messages[1]
        else:
            # 思考内容返ってきてない。どうなってんの…。
            self.think_result.bestmove = "none"

    # エンジンから送られてきた"info ..."を処理する。
    def handle_info(self, message: str):

        # まだ"go"を発行していないのか？
        if self.think_result is None:
            return

        # 解析していく
        scanner = Scanner(message.split(), 1)
        pv = UsiThinkPV()

        # multipvの何番目の読み筋であるか
        multipv = 1
        while not scanner.is_eof():
            try:
                token = scanner.get_token()
                if token == "string":
                    return
                elif token == "depth":
                    pv.depth = scanner.get_token()
                elif token == "seldepth":
                    pv.seldepth = scanner.get_token()
                elif token == "nodes":
                    pv.nodes = scanner.get_token()
                elif token == "nps":
                    pv.nps = scanner.get_token()
                elif token == "hashfull":
                    pv.hashfull = scanner.get_token()
                elif token == "time":
                    pv.time = scanner.get_token()
                elif token == "pv":
                    pv.pv = scanner.rest_string()
                elif token == "multipv":
                    multipv = scanner.get_integer()
                # 評価値絡み
                elif token == "score":
                    token = scanner.get_token()
                    if token == "mate":
                        # https://github.com/yaneurao/Ayane/issues/6
                        # 技巧の場合、
                        # "info depth 1 nodes 0 time 0 score mate + string Nyugyoku"
                        # のような文字列が来ることがあるらしい。
                        is_minus = scanner.peek_token()[0] == "-"
                        ply = scanner.get_integer()
                        # 解析失敗したときはNoneが返ってくるので、このとき手数は+2000/-2000という扱いにしておく。
                        # これはUsiEvalSpecialValueでmate scoreとして判定されるギリギリのスコア。
                        if ply is None:
                            ply = UsiEvalSpecialValue.ValueMaxMatePly
                        if not is_minus:
                            pv.eval = UsiEvalValue.mate_in_ply(ply)
                        else:
                            pv.eval = UsiEvalValue.mated_in_ply(-int(ply))
                            # ２つ上のifでNoneならint型になるはずなのだが、pylint、ここでplyがNoneの可能性があると勘違いしていて
                            # NoneTypeに単項マイナスをつけているという警告が出る。仕方ないのでint()と明示する。
                    elif token == "cp":
                        pv.eval = UsiEvalValue(scanner.get_integer())

                    # この直後に"upperbound"/"lowerbound"が付与されている可能性がある。
                    token = scanner.peek_token()
                    if token == "upperbound":
                        pv.bound = UsiBound.BoundUpper
                        scanner.get_token()
                    elif token == "lowerbound":
                        pv.bound = UsiBound.BoundLower
                        scanner.get_token()
                    else:
                        pv.bound = UsiBound.BoundExact

                # "info string.."はコメントなのでこの行は丸ごと無視する。
                else:
                    raise ValueError("ParseError")
            except:
                self.print(
                    "{0} : ParseError : token = {1}  , line = {2}".format(
                        self.instance_id, token, scanner.get_original_text()
                    )
                )

        if multipv >= 1:
            # 配列の要素数が足りないなら、追加しておく。
            while len(self.think_result.pvs) < multipv:
                self.think_result.pvs.append(None)
            self.think_result.pvs[multipv - 1] = pv

    def handle_checkmate(self, message: str):
        self.think_result.checkmate = message.replace("checkmate ", "")

    # デストラクタで通信の切断を行う。
    def __del__(self):
        self.disconnect()
