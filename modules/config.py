"""
config.py - アプリケーション設定ファイル(config.json)の読み込み・検証・自動生成を行うモジュール

主な機能:
- 設定ファイルの存在確認
- 存在しない場合のデフォルト生成
- JSON形式の読み込みと検証
"""

import os
import json
from modules.logger import setup_logger

# ロガー初期化
logger = setup_logger()

# 自動生成用のデフォルト設定（初期値）
DEFAULT_CONFIG = {
    "browser_type": "firefox",  # firefox または chrome
    "firefox_path": "FirefoxPortable/App/Firefox64/firefox.exe",
    "firefox_driver_path": "drivers/geckodriver.exe",
    "chrome_path": "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "chrome_driver_path": "drivers/chromedriver.exe",
    "profile_path": "FirefoxPortable/Data/profile",
    "target_url": "https://www.amazon.co.jp/photos/all?timeYear=1000&lcf=time",
    "initial_wait": 5,
    "filename_pattern": "VRChat_(\\d{4})-(\\d{2})-(\\d{2})_(\\d{2})-(\\d{2})-(\\d{2})"
}

def error_and_exit(message):
    """
    致命的なエラーをログに出力し、プログラムを強制終了する。

    Args:
        message (str): エラーメッセージ
    """
    logger.error(message)
    exit(1)

def create_default_config(path):
    """
    デフォルトの config.json を生成する。

    Args:
        path (str): 生成先のファイルパス

    動作:
    - DEFAULT_CONFIG の内容を JSON としてファイルに書き出す
    - ユーザーに編集を促す警告ログを出力する
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
    logger.warning(f"{path} が見つからなかったため、デフォルト設定を作成しました。必要に応じて編集してください。")

def load_config(path="config.json"):
    """
    設定ファイルを読み込む。存在しない場合は自動生成する。

    Args:
        path (str): 読み込む設定ファイルのパス（省略時は config.json）

    Returns:
        dict: 設定内容を格納した辞書（JSON形式）

    Raises:
        JSONDecodeError: ファイルが存在するが構文が壊れている場合
    """
    if not os.path.exists(path):
        create_default_config(path)

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        error_and_exit("config.json の形式に誤りがあります。")
