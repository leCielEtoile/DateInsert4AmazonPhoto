"""
modules パッケージ

このパッケージは DateInsert4AmazonPhoto アプリケーションの主要モジュールを含みます。
- logger: ログ出力初期化
- config: 設定ファイル読み込みとエラー処理
- geckodriver: GeckoDriver 自動ダウンロード処理
- chromedriver: ChromeDriver 自動ダウンロード処理
- version: バージョン管理
"""

from .logger import setup_logger
from .config import load_config, error_and_exit
from .geckodriver import download_latest_geckodriver
from .chromedriver import download_latest_chromedriver
from .version import __version__

__all__ = [
    "setup_logger",
    "load_config",
    "error_and_exit",
    "download_latest_geckodriver",
    "download_latest_chromedriver",
    "__version__"
]
