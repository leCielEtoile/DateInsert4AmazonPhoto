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
import sys
import logging
import signal
import time
from modules import setup_logger, load_config, __version__
from modules.utils import error_and_exit
from modules.driver_manager import DriverManager
from modules.photo_processor import PhotoProcessor

def setup():
    """
    アプリケーション初期設定を行う
    
    Returns:
        tuple: (config, logger)
    """
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
    
    return config, logger

def signal_handler(sig, frame):
    """
    シグナルハンドラ（Ctrl+Cなどの割り込み処理）
    """
    print("\n処理を中断します。終了処理を行っています...")
    sys.exit(0)

def main():
    """
    アプリケーションのエントリーポイント。
    設定を読み込み、ブラウザを起動し、各画像に対して自動的に撮影日時を設定する。
    """
    # シグナルハンドラ設定
    signal.signal(signal.SIGINT, signal_handler)
    
    # 初期設定
    config, logger = setup()
    
    logger.info(f"STARTUP - DateInsert4AmazonPhoto v{__version__}")
    
    # 初期設定値
    browser_type = config.get("browser_type", "firefox").lower()
    browser_path = os.path.abspath(config.get(f"{browser_type}_path", ""))
    driver_path = os.path.abspath(config.get(f"{browser_type}_driver_path", ""))
    profile_path = os.path.abspath(config.get("profile_path", ""))
    target_url = config.get("target_url", "").strip()
    wait_sec = config.get("initial_wait", 5)
    
    # URLの検証
    if not target_url.startswith("http"):
        error_and_exit("target_url の指定が不正です。http で始まる URL を指定してください。", logger)
    
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
            error_and_exit("Amazonログイン画面にリダイレクトされました。ログイン情報が含まれていない可能性があります。", logger)
        
        # 写真処理用プロセッサ初期化
        processor = PhotoProcessor(driver)
        
        # メイン処理ループ
        process_count = 0
        max_iterations = config.get("max_iterations", 1000)  # 無限ループ防止
        
        while process_count < max_iterations:
            logger.info(f"写真一覧を取得中... (処理サイクル: {process_count + 1})")
            photo_links = processor.get_photo_links()
            
            if not photo_links:
                logger.info("写真が見つかりませんでした。終了します。")
                break
            
            logger.info(f"{len(photo_links)}件の写真を検出しました。")
            
            # 各写真に対して処理
            needs_more_processing = processor.process_photos(photo_links)
            
            if not needs_more_processing:
                logger.info("すべての写真が正しく設定されました。終了します。")
                break
            
            process_count += 1
            logger.info("ページを再読み込みします。")
            driver.refresh()
            time.sleep(wait_sec)
    
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {type(e).__name__}: {e}")
    finally:
        # 終了処理
        logger.info("処理を終了します。")
        driver_manager.quit_browser()

if __name__ == "__main__":
    main()