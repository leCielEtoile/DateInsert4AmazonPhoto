"""
utils.py - 共通ユーティリティ関数を提供するモジュール
"""

import logging

def error_and_exit(message, logger=None):
    """
    致命的なエラーをログに記録して、スクリプトを終了する。
    
    Args:
        message (str): エラーメッセージ
        logger: 使用するロガー（省略時はルートロガー）
    """
    if logger:
        logger.error(message)
    else:
        logging.error(message)
    exit(1)