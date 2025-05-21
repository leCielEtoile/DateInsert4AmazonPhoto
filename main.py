"""
main.py - Amazon Photos 上の VRChat スクリーンショットに対して、ファイル名から抽出した日付・時刻を
撮影日時として自動設定するスクリプト。

依存モジュール:
- modules/logger.py: カラー付きログ出力設定
- modules/config.py: 設定ファイルの読み込みとエラー処理
- modules/driver_manager.py: WebDriverの管理とブラウザ操作
- modules/photo_processor.py: 写真の日時処理ロジック

対応ブラウザ:
- Firefox（GeckoDriver）
- Chrome（ChromeDriver）
"""

import os
import re
import time
import logging
from modules import setup_logger, load_config, error_and_exit, __version__
from modules.driver_manager import DriverManager
from modules.photo_processor import PhotoProcessor

# 設定ファイルの読み込み
config = load_config()

# ログレベルの取得と変換
log_levels = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}
console_level = log_levels.get(config.get("log_level_console", "INFO"), logging.INFO)
file_level = log_levels.get(config.get("log_level_file", "DEBUG"), logging.DEBUG)

# ロガー初期化
logger = setup_logger(console_level=console_level, file_level=file_level)

def main():
    """
    アプリケーションのエントリーポイント。
    設定を読み込み、ブラウザを起動し、各画像に対して自動的に撮影日時を設定する。
    """
    logger.info(f"STARTUP - DateInsert4AmazonPhoto v{__version__}")
    
    # 初期設定値
    browser_type = config.get("browser_type", "firefox").lower()
    browser_path = os.path.abspath(config.get(f"{browser_type}_path", ""))
    driver_path = os.path.abspath(config.get(f"{browser_type}_driver_path", ""))
    profile_path = os.path.abspath(config.get("profile_path", ""))
    target_url = config.get("target_url", "").strip()
    wait_sec = config.get("initial_wait", 5)
    
    # 設定値の検証
    if not os.path.isfile(browser_path):
        logger.warning(f"ブラウザ実行ファイルが見つかりません: {browser_path}")
        # ブラウザパスの自動検出を試みる
        if browser_type == "firefox":
            potential_paths = [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
                # 追加のパス候補
            ]
            for path in potential_paths:
                if os.path.isfile(path):
                    browser_path = path
                    logger.info(f"Firefox実行ファイルを自動検出しました: {browser_path}")
                    break
        
        elif browser_type == "chrome":
            potential_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                # 追加のパス候補
            ]
            for path in potential_paths:
                if os.path.isfile(path):
                    browser_path = path
                    logger.info(f"Chrome実行ファイルを自動検出しました: {browser_path}")
                    break
        
        # それでも見つからない場合はエラー
        if not os.path.isfile(browser_path):
            error_and_exit(f"ブラウザ実行ファイルが見つかりません: {browser_path}")
    
    # プロファイルパスのチェック（警告のみ）
    if not os.path.isdir(profile_path):
        logger.warning(f"ブラウザプロファイルが見つかりません: {profile_path}")
        # デフォルトプロファイルを使用する
    
    if not target_url.startswith("http"):
        error_and_exit("target_url の指定が不正です。http で始まる URL を指定してください。")
    
    # ドライバーマネージャの初期化とブラウザ起動
    driver_manager = DriverManager(browser_type, browser_path, profile_path, driver_path)
    driver = driver_manager.start_browser()
    
    try:
        # Amazon Photos にアクセス
        logger.info("Amazon Photos にアクセスします...")
        driver.get(target_url)
        time.sleep(wait_sec)
        
        # ログイン状態確認
        if "signin" in driver.current_url or "ap/signin" in driver.current_url:
            error_and_exit("Amazonログイン画面にリダイレクトされました。ログイン情報が含まれていない可能性があります。")
        
        # 写真処理用プロセッサ初期化
        processor = PhotoProcessor(driver)
        
        # メイン処理ループ（画像1枚ずつ開いて処理）
        while True:
            logger.info("写真一覧を取得中...")
            photo_links = processor.get_photo_links()
            
            if not photo_links:
                logger.info("写真が見つかりませんでした。終了します。")
                break
            
            # 各写真に対して処理
            needs_more_processing = processor.process_photos(photo_links)
            
            if not needs_more_processing:
                logger.info("すべての写真が正しく設定されました。終了します。")
                break
            
            logger.info("ページを再読み込みします。")
            driver.refresh()
            time.sleep(wait_sec)
    
    finally:
        # 終了処理
        logger.info("処理を終了します。")
        driver_manager.quit_browser()

if __name__ == "__main__":
    main()