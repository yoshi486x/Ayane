import io
import os
import threading
from datetime import datetime
from typing import Optional, cast


# ログの書き出し用
class Log:
    # log_folder   : ログを書き出すフォルダ
    # file_logging : ファイルに書き出すのか？
    # also_print   : 標準出力に出力するのか？
    def __init__(
        self, log_folder: str, file_logging: bool = True, also_print: bool = True
    ):

        # --- public members ---

        # ログフォルダ 絶対path(コンストラクタで渡される)
        # self.print()を呼び出すまでであれば変更可。
        self.log_folder = log_folder

        # ファイルへの書き出しの有効/無効
        # self.print()を呼び出すまでであれば変更可。
        # self.print()の引数でfile_loggingを指定することもできる。
        self.file_logging = file_logging

        # 標準出力への出力の有効/無効
        # self.print()を呼び出すまでであれば変更可。
        # self.print()の引数でalso_printを指定することもできる。
        self.also_print = also_print

        # --- public readonly members ---

        # ログファイル名 絶対path
        self.log_filename = ""

        # 書き出しているファイルのハンドル
        self.log_file: Optional[io.TextIOWrapper] = None

        # --- private members ---

        # print()のときのlock用
        self.lock_object = threading.Lock()

    # ファイルのopen。
    # コンストラクタで呼び出されるため、普通は明示的に呼び出す必要はない。
    # ファイル名は日付で作成される。
    def open(self):
        self.close()

        if not os.path.exists(self.log_folder):
            os.mkdir(self.log_folder)

        # このクラスのインスタンスの識別用ID。
        # 念の為、lockしてから参照/インクリメントを行う。
        # 何番目に生成されたUsiEngineから出力されたログであるかをカウントしておき
        # ログ出力のときに識別子として書き出すためのもの。
        with Log.static_lock_object:
            count = Log.static_count
            Log.static_count += 1

        # 同じタイミングで複数のinstanceからログ・ファイルが生成されることを考慮して、ファイル名の末尾にinstance idみたいなのを付与しておく。
        filename = "log{0}_{1}.txt".format(
            datetime.now().strftime("%Y-%m-%d %H-%M-%S"), count
        )
        self.log_filename = os.path.join(self.log_folder, filename)

        self.log_file = open(self.log_filename, "w", encoding="utf_8_sig")

    # ファイルをcloseする。
    def close(self):
        if self.log_file is not None:
            self.log_file.close()
            self.log_file = None

    # 1行書き出す
    def print(
        self,
        message: str,
        output_datetime: bool = False,
        also_print: bool = None,
        file_logging: bool = None,
    ):
        if output_datetime:
            message = "[{0}]:{1}".format(
                datetime.now().strftime("%Y/%m/%d %H:%M:%S"), message
            )

        with self.lock_object:

            # ファイルへの書き出し
            # 引数でfile_loggingが設定されていたらそれに従う。
            # さもなくば、self.file_loggingに従う。

            if (file_logging is not None and file_logging) or self.file_logging:
                # ファイルをまだopenしていないならopenする
                if self.log_file is None:
                    self.open()

                # Optionalに対するメソッド呼び出しは、MyPyの警告がでるので、
                # castを行ってからメソッドを呼び出す。
                log_file = cast(io.TextIOWrapper, self.log_file)
                log_file.write(message + "\n")
                log_file.flush()

            # 標準出力に書き出すかどうかは、
            # 引数でalso_printが設定されていたら、それに従う。
            # さもなくば、self.also_printに従う。
            if (also_print is not None and also_print) or self.also_print:
                print(message)

    def __del__(self):
        self.close()

    # --- private static members ---

    # 静的メンバ変数とする。UsiEngineのインスタンスの数を記録する
    static_count = 0

    # ↑の変数を変更するときのlock object
    static_lock_object = threading.Lock()


# GlobalなLogが欲しいときは、以下のSingletonLog.get_log()を用いるとよい。
class SingletonLog:
    # Logクラスのインスタンスを取得する
    @staticmethod
    def get_log() -> Log:
        with SingletonLog.__static_lock_object:
            if SingletonLog.__log is None:
                SingletonLog.__log = Log("log")
        return SingletonLog.__log

    # --- private static members

    __log: Optional[Log] = None
    __static_lock_object = threading.Lock()
