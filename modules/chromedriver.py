"""
chromedriver.py - ChromeDriver の自動ダウンロードモジュール

このモジュールは、Selenium WebDriver（Chrome）に必要な chromedriver.exe を
Googleの公式リリース（LTS）から取得し、指定されたフォルダに展開します。

主な機能:
- chromedriver.exe が存在しなければ自動でダウンロード
- 進捗バー付きで zip をダウンロード・解凍・保存
"""

import os
import io
import zipfile
import requests
from tqdm import tqdm
from modules.logger import setup_logger
from modules.version import __version__

logger = setup_logger()

def error_and_exit(message):
    logger.error(message)
    exit(1)

def download_latest_chromedriver(dest_dir):
    """
    ChromeDriver が指定ディレクトリに存在しない場合、
    GoogleのLTSバージョンのWindows用 ChromeDriver をダウンロードして展開します。

    Args:
        dest_dir (str): chromedriver.exe を保存するディレクトリ

    Returns:
        str: chromedriver.exe のフルパス
    """
    exe_path = os.path.join(dest_dir, "chromedriver.exe")
    if os.path.exists(exe_path):
        logger.info("chromedriver.exe は既に存在します。")
        return exe_path

    logger.info("chromedriver.exe が見つかりません。LTS版をダウンロードします...")

    try:
        # LTS安定版リリース取得
        meta_url = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
        res = requests.get(meta_url, timeout=10)
        res.raise_for_status()
        data = res.json()
        version_info = data["channels"]["Stable"]
        version = version_info["version"]

        # Windows x64 用の zip を取得
        downloads = version_info["downloads"]["chromedriver"]
        dl_info = next(x for x in downloads if x["platform"] == "win64")
        dl_url = dl_info["url"]
        zip_name = dl_url.split("/")[-1]

        # zip ダウンロード
        with requests.get(dl_url, stream=True, timeout=30) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            buffer = io.BytesIO()
            with tqdm(total=total, unit="B", unit_scale=True, desc=zip_name) as bar:
                for chunk in r.iter_content(chunk_size=8192):
                    buffer.write(chunk)
                    bar.update(len(chunk))

        # zip 解凍
        buffer.seek(0)
        with zipfile.ZipFile(buffer) as z:
            for name in z.namelist():
                if name.endswith("chromedriver.exe"):
                    z.extract(name, path=dest_dir)
                    src_path = os.path.join(dest_dir, name)
                    os.replace(src_path, exe_path)

        logger.info(f"chromedriver.exe を {dest_dir} に保存しました。")
        return exe_path

    except Exception as e:
        error_and_exit(f"ChromeDriver のダウンロードに失敗しました: {e}")
