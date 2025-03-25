"""
config.py - アプリケーション設定（config.json）の読み込みと検証を行うモジュール

主な機能:
- 設定ファイル(config.json)の存在確認と読み込み
- 不正な形式や欠落に対してはログ出力し即時終了
"""

import os
import json
from modules.logger import setup_logger

# 共通ロガーの取得
logger = setup_logger()

def error_and_exit(message):
    """
    致命的なエラーをログに出力し、プログラムを強制終了する。

    Args:
        message (str): エラーメッセージ
    """
    logger.error(message)
    exit(1)

def load_config(path="config.json"):
    """
    指定されたパスからJSON形式の設定ファイルを読み込み、辞書として返す。

    Args:
        path (str): 読み込む設定ファイルのパス（デフォルト: config.json）

    Returns:
        dict: 設定内容を格納した辞書

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        JSONDecodeError: JSONの構文が不正な場合
    """
    if not os.path.exists(path):
        error_and_exit("設定ファイル config.json が見つかりません。")

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        error_and_exit("config.json の形式に誤りがあります。")
