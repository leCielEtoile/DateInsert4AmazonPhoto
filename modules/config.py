"""
config.py - アプリケーション設定ファイル(config.ini)の読み込み・検証を行うモジュール

主な機能:
- INI形式の設定ファイル読み込み（configparser 使用）
- 存在しない場合はサンプルINIファイルを自動生成
- セクションごとに Firefox / Chrome / 共通設定を管理
"""

import os
import configparser
from modules.logger import setup_logger

# ロガー初期化
logger = setup_logger()

# 自動生成用のデフォルト設定（初回起動時）
DEFAULT_CONFIG = """[general]
browser = chrome
target_url = https://www.amazon.co.jp/photos/all?timeYear=1000&lcf=time
initial_wait = 5

[firefox]
firefox_path = FirefoxPortable/App/Firefox64/firefox.exe
geckodriver_path = geckodriver.exe
profile_path = FirefoxPortable/Data/profile

[chrome]
chrome_path = C:/Program Files/Google/Chrome/Application/chrome.exe
chromedriver_path = chromedriver.exe
user_data_dir = C:/Users/YourName/AppData/Local/Google/Chrome/User Data
profile_directory = Default
"""

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
    デフォルトの config.ini を生成する。
    Args:
        path (str): 生成先ファイルパス
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(DEFAULT_CONFIG)
    logger.warning(f"{path} が見つからなかったため、初期設定ファイルを生成しました。編集して再実行してください。")

def load_config(path="config.ini"):
    """
    INI形式の設定ファイルを読み込む（存在しなければ自動生成）。
    Args:
        path (str): 読み込む設定ファイルのパス（省略時は config.ini）
    Returns:
        configparser.ConfigParser: 読み込まれた設定オブジェクト
    """
    if not os.path.exists(path):
        create_default_config(path)

    config = configparser.ConfigParser(interpolation=None)
    config.read(path, encoding="utf-8")
    return config