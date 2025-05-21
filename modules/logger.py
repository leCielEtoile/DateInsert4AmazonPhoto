"""
logger.py - アプリケーション全体で共通使用されるロガー（logging）を設定するモジュール

機能:
- コンソール出力：色付きで視認性の高いログ
- ファイル出力：logs/app.log に全ログを記録
- 二重設定防止：ロガーがすでに設定済みなら再設定しない
"""

import os
import logging
from datetime import datetime

def setup_logger(name="DateInsert4AmazonPhoto", log_file="logs/app.log", console_level=logging.INFO, file_level=logging.DEBUG):
    """
    カスタムロガーを初期化し、StreamHandler（カラー付き）と
    FileHandler（log_file）を設定して返す。

    Args:
        name (str): ロガー名
        log_file (str): ログファイルのパス（省略時は logs/app.log）
        console_level: コンソール出力のログレベル
        file_level: ファイル出力のログレベル

    Returns:
        logging.Logger: 設定済みのロガーオブジェクト
    """
    logger = logging.getLogger(name)

    # 重複設定を防ぐ（すでにハンドラが存在する場合は再設定しない）
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)  # 最も低いレベルに設定

    # ログのフォーマット
    log_format = "%(levelname)-9s %(asctime)s [%(filename)s:%(lineno)d] %(message)s"

    class ColorFormatter(logging.Formatter):
        """
        コンソール出力用のカラー対応フォーマッタ
        """
        COLOR_MAP = {
            logging.DEBUG: "\033[37m",     # 白
            logging.INFO: "\033[32m",      # 緑
            logging.WARNING: "\033[33m",   # 黄
            logging.ERROR: "\033[31m",     # 赤
            logging.CRITICAL: "\033[41m"   # 背景赤
        }
        RESET = "\033[0m"

        def format(self, record):
            color = self.COLOR_MAP.get(record.levelno, self.RESET)
            message = super().format(record)
            return f"{color}{message}{self.RESET}"

    # コンソール用ハンドラ（色付き）
    st_handler = logging.StreamHandler()
    st_handler.setLevel(console_level)
    st_handler.setFormatter(ColorFormatter(log_format))

    # ログディレクトリの作成
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # ファイル用ハンドラ
    fl_handler = logging.FileHandler(filename=log_file, encoding="utf-8")
    fl_handler.setLevel(file_level)
    fl_handler.setFormatter(logging.Formatter(log_format))

    # ハンドラ登録
    logger.addHandler(st_handler)
    logger.addHandler(fl_handler)

    return logger