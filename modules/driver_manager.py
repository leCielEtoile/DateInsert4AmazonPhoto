"""
driver_manager.py - WebDriverの管理とブラウザ操作

このモジュールは以下の機能を提供:
- Firefox/Chrome用のWebDriverの初期化と管理
- ドライバーの自動ダウンロード
- ブラウザ操作のユーティリティ関数
"""

import os
import time
import io
import zipfile
import requests
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from modules.logger import setup_logger
from modules.version import __version__

logger = setup_logger()

def error_and_exit(message):
    """
    致命的なエラーをログに記録して、スクリプトを終了する。
    """
    logger.error(message)
    exit(1)

class DriverManager:
    """WebDriverを管理し、ブラウザ操作の共通機能を提供するクラス"""
    
    def __init__(self, browser_type, browser_path, profile_path, driver_path):
        """
        初期化
        
        Args:
            browser_type (str): "firefox" または "chrome"
            browser_path (str): ブラウザ実行ファイルのパス
            profile_path (str): ブラウザプロファイルのパス
            driver_path (str): WebDriverのパス（存在しない場合は自動ダウンロード）
        """
        self.browser_type = browser_type.lower()
        self.browser_path = browser_path
        self.profile_path = profile_path
        self.driver_path = driver_path
        self.driver = None
        
        # ドライバーディレクトリの作成
        driver_dir = os.path.dirname(driver_path)
        if not os.path.exists(driver_dir):
            os.makedirs(driver_dir, exist_ok=True)
        
        # ドライバーの存在チェック
        if not os.path.exists(driver_path):
            self._download_driver()
    
    def _download_driver(self):
        """
        適切なWebDriverをダウンロードする
        """
        if self.browser_type == "firefox":
            self._download_geckodriver()
        elif self.browser_type == "chrome":
            self._download_chromedriver()
        else:
            error_and_exit(f"未対応のブラウザタイプ: {self.browser_type}")
    
    def _download_geckodriver(self):
        """
        GeckoDriverの最新バージョンをダウンロードして展開する
        """
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
                # フォールバック: 直接特定バージョンを指定してダウンロード
                fallback_version = "v0.33.0"
                fallback_url = f"https://github.com/mozilla/geckodriver/releases/download/{fallback_version}/geckodriver-{fallback_version}-win64.zip"
                logger.warning(f"GithubAPIからドライバが見つからなかったため、固定バージョン{fallback_version}を使用します。")
                self._download_and_extract(fallback_url, 'geckodriver.exe', headers)
                return
                
            logger.info(f"GeckoDriver最新バージョンをダウンロードします: {asset_url}")
            self._download_and_extract(asset_url, 'geckodriver.exe', headers)
            
        except Exception as e:
            error_and_exit(f"Geckodriver のダウンロードに失敗しました: {e}")
    
    def _download_chromedriver(self):
        """
        ChromeDriverの最新バージョンをダウンロードして展開する
        """
        logger.info('chromedriver.exe が見つかりません。最新バージョンをダウンロードします...')
        
        try:
            # Chrome のバージョンを確認する方法をここに実装する必要がある
            # 現在は最新の安定版をダウンロードするシンプルな実装
            url = "https://chromedriver.storage.googleapis.com/LATEST_RELEASE"
            version = requests.get(url).text.strip()
            
            download_url = f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_win32.zip"
            headers = {"User-Agent": f"DateInsert4AmazonPhoto/{__version__}"}
            
            self._download_and_extract(download_url, 'chromedriver.exe', headers)
            
        except Exception as e:
            error_and_exit(f"Chromedriver のダウンロードに失敗しました: {e}")
    
    def _download_and_extract(self, url, exe_name, headers):
        """
        URLからZIPファイルをダウンロードし、指定された実行ファイルを抽出する
        
        Args:
            url (str): ダウンロードURL
            exe_name (str): 抽出する実行ファイル名
            headers (dict): HTTPリクエストヘッダー
        """
        dest_dir = os.path.dirname(self.driver_path)
        zip_name = url.split('/')[-1]
        
        # zipファイルをダウンロード（メモリ上に保存）
        with requests.get(url, headers=headers, stream=True) as r:
            r.raise_for_status()
            total = int(r.headers.get('content-length', 0))
            buffer = io.BytesIO()
            with tqdm(total=total, unit='B', unit_scale=True, desc=zip_name) as bar:
                for chunk in r.iter_content(chunk_size=8192):
                    buffer.write(chunk)
                    bar.update(len(chunk))
        
        # zipを解凍してdriverを抽出
        buffer.seek(0)
        with zipfile.ZipFile(buffer) as zip_file:
            files = zip_file.namelist()
            driver_file = next((f for f in files if f.endswith(exe_name)), None)
            if driver_file:
                zip_file.extract(driver_file, path=dest_dir)
                # ネストされたパスの場合は移動
                if driver_file != exe_name:
                    os.rename(
                        os.path.join(dest_dir, driver_file),
                        os.path.join(dest_dir, exe_name)
                    )
            else:
                raise RuntimeError(f"{exe_name} が見つかりませんでした。")
        
        logger.info(f'{exe_name} を {dest_dir} に保存しました。')
    
    def start_browser(self):
        """
        選択したブラウザを起動し、WebDriverインスタンスを返す
        
        Returns:
            webdriver: 初期化されたWebDriverインスタンス
        """
        if self.browser_type == "firefox":
            options = FirefoxOptions()
            options.binary_location = self.browser_path
            
            # Firefox profileのパスを設定
            if os.path.isdir(self.profile_path):
                options.profile = self.profile_path
            
            # GeckoDriverを明示的に設定
            if not os.path.exists(self.driver_path):
                logger.warning(f"指定されたドライバパスが存在しません: {self.driver_path}")
                self._download_driver()
            
            # SeleniumのSystemPathに追加
            driver_dir = os.path.dirname(os.path.abspath(self.driver_path))
            os.environ["PATH"] = f"{driver_dir}{os.pathsep}{os.environ.get('PATH', '')}"
            
            service = FirefoxService(executable_path=self.driver_path)
            try:
                logger.info(f"Firefoxを起動します。ドライバパス: {self.driver_path}")
                self.driver = webdriver.Firefox(service=service, options=options)
                logger.info("Firefox WebDriverの起動に成功しました。")
            except Exception as e:
                error_and_exit(f"Firefox WebDriver の起動に失敗: {str(e)}")
        
        elif self.browser_type == "chrome":
            options = ChromeOptions()
            options.binary_location = self.browser_path
            options.add_argument(f"user-data-dir={self.profile_path}")
            
            # ChromeDriverを明示的に設定
            if not os.path.exists(self.driver_path):
                logger.warning(f"指定されたドライバパスが存在しません: {self.driver_path}")
                self._download_driver()
            
            # SeleniumのSystemPathに追加
            driver_dir = os.path.dirname(os.path.abspath(self.driver_path))
            os.environ["PATH"] = f"{driver_dir}{os.pathsep}{os.environ.get('PATH', '')}"
            
            service = ChromeService(executable_path=self.driver_path)
            try:
                logger.info(f"Chromeを起動します。ドライバパス: {self.driver_path}")
                self.driver = webdriver.Chrome(service=service, options=options)
                logger.info("Chrome WebDriverの起動に成功しました。")
            except Exception as e:
                error_and_exit(f"Chrome WebDriver の起動に失敗: {str(e)}")
        
        else:
            error_and_exit(f"未対応のブラウザタイプ: {self.browser_type}")
        
        return self.driver
    
    def wait_for_element(self, by, selector, timeout=10, polling=0.5):
        """
        指定したセレクタに一致する要素が表示されるまで待機
        
        Args:
            by: 検索方法（By.ID, By.CSS_SELECTOR など）
            selector: 検索するセレクタ
            timeout: タイムアウト時間（秒）
            polling: ポーリング間隔（秒）
            
        Returns:
            見つかった要素。見つからなければ None
        """
        if not self.driver:
            return None
            
        try:
            return WebDriverWait(self.driver, timeout, poll_frequency=polling).until(
                EC.presence_of_element_located((by, selector))
            )
        except TimeoutException:
            return None
    
    def quit_browser(self):
        """
        ブラウザを安全に終了する
        """
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"ブラウザ終了時にエラーが発生: {e}")
            finally:
                self.driver = None