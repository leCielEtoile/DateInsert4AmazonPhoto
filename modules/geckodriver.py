"""
geckodriver.py - GeckoDriver の自動ダウンロードモジュール

このモジュールは、Selenium WebDriver（Firefox）に必要な geckodriver.exe を
GitHub の公式リリースから取得し、プロジェクトディレクトリに展開する処理を提供します。

主な機能:
- 既に geckodriver.exe が存在するかチェック
- 存在しない場合は GitHub API を通じて最新の Windows 版 geckodriver を取得
- プログレスバー付きでダウンロード、zip 解凍して保存
"""

import os
import io
import zipfile
import requests
from tqdm import tqdm
from modules.logger import setup_logger
from modules.version import __version__

# ロガーの重複設定を防止（setup_logger 側で hasHandlers チェック済み）
logger = setup_logger()

def error_and_exit(message):
    """
    致命的なエラーをログに記録して、スクリプトを終了する。
    """
    logger.error(message)
    exit(1)

def download_latest_geckodriver(dest_dir):
    """
    GeckoDriver が指定ディレクトリに存在しない場合、
    GitHub の最新版を自動でダウンロードして展開します。

    引数:
        dest_dir (str): geckodriver.exe を保存するディレクトリのパス

    戻り値:
        str: 展開された geckodriver.exe のパス

    処理概要:
    - GitHub API を使って最新リリースのアセット一覧を取得
    - Windows 64bit 用 zip ファイルを見つけてダウンロード
    - tqdm を使ってプログレスバー表示しながら zip をメモリに展開
    - zip から geckodriver.exe を抽出して dest_dir に保存
    """
    exe_path = os.path.join(dest_dir, 'geckodriver.exe')
    if os.path.exists(exe_path):
        logger.info('geckodriver.exe は既に存在します。')
        return exe_path

    logger.info('geckodriver.exe が見つかりません。最新バージョンをダウンロードします...')

    headers = {
        'Accept': 'application/vnd.github.v3+json',
        "User-Agent": f"DateInsert4AmazonPhoto/{__version__}"
    }
    url = 'https://api.github.com/repos/mozilla/geckodriver/releases/latest'

    try:
        # 最新リリース情報を取得
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        assets = res.json().get('assets', [])

        # Windows 64bit 用の zip ファイルを探す
        asset_url = next((a['browser_download_url'] for a in assets if 'win64.zip' in a['name']), None)
        if not asset_url:
            raise RuntimeError('Windows用geckodriverが見つかりませんでした。')

        zip_name = asset_url.split('/')[-1]

        # zip ファイルをダウンロード（メモリ上に保存）
        with requests.get(asset_url, headers={'User-Agent': headers['User-Agent']}, stream=True) as r:
            r.raise_for_status()
            total = int(r.headers.get('content-length', 0))
            buffer = io.BytesIO()
            with tqdm(total=total, unit='B', unit_scale=True, desc=zip_name) as bar:
                for chunk in r.iter_content(chunk_size=8192):
                    buffer.write(chunk)
                    bar.update(len(chunk))

        # zip 解凍して geckodriver.exe を抽出
        buffer.seek(0)
        with zipfile.ZipFile(buffer) as zip_file:
            zip_file.extract('geckodriver.exe', path=dest_dir)

        logger.info(f'geckodriver.exe を {dest_dir} に保存しました。')
        return exe_path

    except Exception as e:
        error_and_exit(f"Geckodriver のダウンロードに失敗しました: {e}")
