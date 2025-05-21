"""
config.py - アプリケーション設定ファイル(config.yaml)の読み込み・検証・自動生成を行うモジュール

主な機能:
- 設定ファイルの存在確認
- 存在しない場合のデフォルト生成
- JSONからYAMLへの自動変換
- YAML形式の読み込みと検証
"""

import os
import json
import yaml
from modules.logger import setup_logger
from modules.utils import error_and_exit

# ロガー初期化
logger = setup_logger()

# 自動生成用のデフォルト設定（初期値）とコメント
DEFAULT_CONFIG = {
    # ブラウザ設定
    "browser_type": "firefox",  # "firefox" または "chrome"
    "firefox_path": "FirefoxPortable/App/Firefox64/firefox.exe",
    "firefox_driver_path": "drivers/geckodriver.exe",
    "chrome_path": "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "chrome_driver_path": "drivers/chromedriver.exe",
    "profile_path": "FirefoxPortable/Data/profile",
    
    # Amazon Photos設定
    "target_url": "https://www.amazon.co.jp/photos/all?timeYear=1000&lcf=time",
    "initial_wait": 5,  # ページ読み込み後の待機時間（秒）
    
    # 写真処理設定
    "filename_pattern": "VRChat_(\\d{4})-(\\d{2})-(\\d{2})_(\\d{2})-(\\d{2})-(\\d{2})",  # 日時抽出用正規表現
    
    # ログ設定
    "log_level_console": "INFO",  # コンソールに表示するログレベル (DEBUG/INFO/WARNING/ERROR/CRITICAL)
    "log_level_file": "DEBUG",    # ファイルに記録するログレベル
    
    # 実行制御
    "max_iterations": 1000        # 処理サイクルの最大数（無限ループ防止）
}

# YAMLファイル用のコメントテンプレート
YAML_COMMENTS = """# DateInsert4AmazonPhoto 設定ファイル
#
# このファイルでは、アプリケーションの動作を制御するための設定を行います。
# 各設定項目の説明は、項目の横のコメントを参照してください。
#
# セクション構成:
# - ブラウザ設定: 使用するブラウザと関連パスの設定
# - Amazon Photos設定: 接続先URLと待機時間
# - 写真処理設定: ファイル名からの日時抽出方法
# - ログ設定: ログの出力レベルと場所
# - 実行制御: プログラムの動作制限

#=====================================================================
# ブラウザ設定
#=====================================================================
"""

def migrate_json_to_yaml():
    """
    既存のconfig.jsonファイルがあれば、config.yamlに変換して削除する
    
    Returns:
        bool: 変換が行われた場合はTrue、それ以外はFalse
    """
    json_path = "config.json"
    yaml_path = "config.yaml"
    
    # JSONファイルが存在しない場合は何もしない
    if not os.path.exists(json_path):
        return False
    
    # YAMLファイルが既に存在する場合は、JSONの変換は行わない
    if os.path.exists(yaml_path):
        logger.info(f"{yaml_path}が既に存在します。{json_path}からの変換は行いません。")
        return False
    
    try:
        # JSONファイルを読み込む
        with open(json_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        # コメント付きYAMLファイルを作成する
        with open(yaml_path, "w", encoding="utf-8") as f:
            # ヘッダーコメントを書き込む
            f.write(YAML_COMMENTS)
            
            # ブラウザ設定セクション
            f.write(f"browser_type: {config_data.get('browser_type', 'firefox')}  # 使用するブラウザ ('firefox' または 'chrome')\n")
            f.write(f"firefox_path: {config_data.get('firefox_path', DEFAULT_CONFIG['firefox_path'])}  # Firefox実行ファイルのパス\n")
            f.write(f"firefox_driver_path: {config_data.get('firefox_driver_path', DEFAULT_CONFIG['firefox_driver_path'])}  # GeckoDriverのパス（自動ダウンロード可能）\n")
            f.write(f"chrome_path: {config_data.get('chrome_path', DEFAULT_CONFIG['chrome_path'])}  # Chrome実行ファイルのパス\n")
            f.write(f"chrome_driver_path: {config_data.get('chrome_driver_path', DEFAULT_CONFIG['chrome_driver_path'])}  # ChromeDriverのパス（自動ダウンロード可能）\n")
            f.write(f"profile_path: {config_data.get('profile_path', DEFAULT_CONFIG['profile_path'])}  # ブラウザプロファイルのパス（ログイン情報など）\n")
            f.write("\n")
            
            # Amazon Photos設定セクション
            f.write("#=====================================================================\n")
            f.write("# Amazon Photos設定\n")
            f.write("#=====================================================================\n")
            f.write(f"target_url: {config_data.get('target_url', DEFAULT_CONFIG['target_url'])}  # 接続先URL\n")
            f.write(f"initial_wait: {config_data.get('initial_wait', DEFAULT_CONFIG['initial_wait'])}  # ページロード後の待機時間（秒）\n")
            f.write("\n")
            
            # 写真処理設定セクション
            f.write("#=====================================================================\n")
            f.write("# 写真処理設定\n")
            f.write("#=====================================================================\n")
            # バックスラッシュのエスケープ処理
            pattern = config_data.get('filename_pattern', DEFAULT_CONFIG['filename_pattern'])
            f.write(f"filename_pattern: '{pattern}'  # ファイル名から日時を抽出する正規表現パターン\n")
            f.write("\n")
            
            # ログ設定セクション
            f.write("#=====================================================================\n")
            f.write("# ログ設定\n")
            f.write("#=====================================================================\n")
            f.write(f"log_level_console: {config_data.get('log_level_console', DEFAULT_CONFIG['log_level_console'])}  # コンソールに表示するログレベル (DEBUG/INFO/WARNING/ERROR/CRITICAL)\n")
            f.write(f"log_level_file: {config_data.get('log_level_file', DEFAULT_CONFIG['log_level_file'])}  # ファイルに記録するログレベル\n")
            f.write("\n")
            
            # 実行制御セクション
            f.write("#=====================================================================\n")
            f.write("# 実行制御\n")
            f.write("#=====================================================================\n")
            f.write(f"max_iterations: {config_data.get('max_iterations', DEFAULT_CONFIG['max_iterations'])}  # 処理サイクルの最大数（無限ループ防止）\n")
        
        logger.info(f"{json_path}を{yaml_path}に変換しました。")
        
        # 変換成功後、JSONファイルの名前を変更してバックアップ
        backup_path = f"{json_path}.bak"
        if os.path.exists(backup_path):
            os.remove(backup_path)  # 既存バックアップを削除
        
        os.rename(json_path, backup_path)
        logger.info(f"元の{json_path}は{backup_path}としてバックアップされました。")
        
        return True
    
    except json.JSONDecodeError:
        logger.warning(f"{json_path}の形式に誤りがあります。YAMLへの変換はスキップします。")
        return False
    except Exception as e:
        logger.warning(f"設定ファイルの変換中にエラーが発生しました: {e}")
        return False

def create_default_config(path):
    """
    デフォルトの config.yaml を生成する。

    Args:
        path (str): 生成先のファイルパス

    動作:
    - コメント付きYAMLファイルとして設定を書き出す
    - ユーザーに編集を促す警告ログを出力する
    """
    with open(path, "w", encoding="utf-8") as f:
        # ヘッダーコメントを書き込む
        f.write(YAML_COMMENTS)
        
        # ブラウザ設定セクション
        f.write(f"browser_type: {DEFAULT_CONFIG['browser_type']}  # 使用するブラウザ ('firefox' または 'chrome')\n")
        f.write(f"firefox_path: {DEFAULT_CONFIG['firefox_path']}  # Firefox実行ファイルのパス\n")
        f.write(f"firefox_driver_path: {DEFAULT_CONFIG['firefox_driver_path']}  # GeckoDriverのパス（自動ダウンロード可能）\n")
        f.write(f"chrome_path: {DEFAULT_CONFIG['chrome_path']}  # Chrome実行ファイルのパス\n")
        f.write(f"chrome_driver_path: {DEFAULT_CONFIG['chrome_driver_path']}  # ChromeDriverのパス（自動ダウンロード可能）\n")
        f.write(f"profile_path: {DEFAULT_CONFIG['profile_path']}  # ブラウザプロファイルのパス（ログイン情報など）\n")
        f.write("\n")
        
        # Amazon Photos設定セクション
        f.write("#=====================================================================\n")
        f.write("# Amazon Photos設定\n")
        f.write("#=====================================================================\n")
        f.write(f"target_url: {DEFAULT_CONFIG['target_url']}  # 接続先URL\n")
        f.write(f"initial_wait: {DEFAULT_CONFIG['initial_wait']}  # ページロード後の待機時間（秒）\n")
        f.write("\n")
        
        # 写真処理設定セクション
        f.write("#=====================================================================\n")
        f.write("# 写真処理設定\n")
        f.write("#=====================================================================\n")
        f.write(f"filename_pattern: '{DEFAULT_CONFIG['filename_pattern']}'  # ファイル名から日時を抽出する正規表現パターン\n")
        f.write("\n")
        
        # ログ設定セクション
        f.write("#=====================================================================\n")
        f.write("# ログ設定\n")
        f.write("#=====================================================================\n")
        f.write(f"log_level_console: {DEFAULT_CONFIG['log_level_console']}  # コンソールに表示するログレベル (DEBUG/INFO/WARNING/ERROR/CRITICAL)\n")
        f.write(f"log_level_file: {DEFAULT_CONFIG['log_level_file']}  # ファイルに記録するログレベル\n")
        f.write("\n")
        
        # 実行制御セクション
        f.write("#=====================================================================\n")
        f.write("# 実行制御\n")
        f.write("#=====================================================================\n")
        f.write(f"max_iterations: {DEFAULT_CONFIG['max_iterations']}  # 処理サイクルの最大数（無限ループ防止）\n")
    
    logger.warning(f"{path} が見つからなかったため、デフォルト設定を作成しました。必要に応じて編集してください。")

def load_config(path="config.yaml"):
    """
    設定ファイルを読み込む。存在しない場合は自動生成する。
    JSONファイルが存在する場合は、YAMLに変換する。

    Args:
        path (str): 読み込む設定ファイルのパス（省略時は config.yaml）

    Returns:
        dict: 設定内容を格納した辞書

    Raises:
        YAMLError: ファイルが存在するが構文が壊れている場合
    """
    # まず既存のJSONファイルがあれば変換を試みる
    migrate_json_to_yaml()
    
    # YAMLファイルが存在しない場合は新規作成
    if not os.path.exists(path):
        create_default_config(path)

    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        error_and_exit(f"config.yaml の形式に誤りがあります: {e}", logger)