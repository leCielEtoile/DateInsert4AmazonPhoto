"""
modules パッケージの初期化スクリプト
他のモジュールのファンクションをここでインポートすることで
modules.関数名 として使用できるようにする
"""

from modules.logger import setup_logger
from modules.config import load_config, error_and_exit
from modules.version import __version__