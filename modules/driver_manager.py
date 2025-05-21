"""
driver_manager.py - WebDriverの管理とブラウザ操作

このモジュールは以下の機能を提供:
- Firefox/Chrome用のWebDriverの初期化と管理
- ドライバーの自動ダウンロード
- ブラウザ操作のユーティリティ関数
"""

import os
import sys
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
from selenium.common.exceptions import TimeoutException, WebDriverException

from modules.logger import setup_logger
from modules.utils import error_and_exit
from modules.version import __version__

logger = setup_logger()

class DriverManager:
    """WebDriverを管理し、ブラウザ操作の共通機能を提供するクラス"""
    
    # ブラウザの標準インストールパス
    BROWSER_PATHS = {
        "firefox": {
            "windows": [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            ],
            "darwin": [  # macOS
                "/Applications/Firefox.app/Contents/MacOS/firefox",
                f"{os.path.expanduser('~')}/Applications/Firefox.app/Contents/MacOS/firefox"
            ],
            "linux": [
                "/usr/bin/firefox",
                "/usr/local/bin/firefox"
            ]
        },
        "chrome": {
            "windows": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ],
            "darwin": [  # macOS
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                f"{os.path.expanduser('~')}/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            ],
            "linux": [
                "/usr/bin/google-chrome",
                "/usr/local/bin/google-chrome"
            ]
        }
    }
    
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
        
        # ブラウザタイプの検証
        if self.browser_type not in ["firefox", "chrome"]:
            error_and_exit(f"未対応のブラウザタイプ: {self.browser_type}", logger)
        
        # ドライバーディレクトリの作成
        driver_dir = os.path.dirname(driver_path)
        if driver_dir and not os.path.exists(driver_dir):
            os.makedirs(driver_dir, exist_ok=True)
        
        # ブラウザパスの自動検出（必要な場合）
        if not os.path.isfile(self.browser_path):
            self._detect_browser_path()
        
        # ドライバーの存在チェック
        if not os.path.exists(driver_path):
            self._download_driver()
    
    def _detect_browser_path(self):
        """
        OS に応じてブラウザのパスを自動検出する
        """
        platform = sys.platform
        if platform.startswith('win'):
            platform_key = 'windows'
        elif platform.startswith('darwin'):
            platform_key = 'darwin'
        else:
            platform_key = 'linux'
        
        # 対応するプラットフォームのパスリストを取得
        path_list = self.BROWSER_PATHS.get(self.browser_type, {}).get(platform_key, [])
        
        for path in path_list:
            if os.path.isfile(path):
                self.browser_path = path
                logger.info(f"{self.browser_type.capitalize()}実行ファイルを自動検出しました: {self.browser_path}")
                return
        
        # 見つからない場合はエラー
        error_and_exit(f"{self.browser_type.capitalize()}実行ファイルが見つかりません", logger)
    
    def _download_driver(self):
        """
        適切なWebDriverをダウンロードする
        """
        if self.browser_type == "firefox":
            self._download_geckodriver()
        elif self.browser_type == "chrome":
            self._download_chromedriver()
    
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
            
            # OSに合わせたzipファイルを探す
            platform_tag = ""
            if sys.platform.startswith('win'):
                platform_tag = 'win64.zip'
            elif sys.platform.startswith('darwin'):
                platform_tag = 'macos'
            else:
                platform_tag = 'linux64'
            
            asset_url = next((a['browser_download_url'] for a in assets if platform_tag in a['name']), None)
            if not asset_url:
                # フォールバック: 直接特定バージョンを指定してダウンロード
                fallback_version = "v0.33.0"
                fallback_url = f"https://github.com/mozilla/geckodriver/releases/download/{fallback_version}/geckodriver-{fallback_version}-win64.zip"
                logger.warning(f"GithubAPIからドライバが見つからなかったため、固定バージョン{fallback_version}を使用します。")
                self._download_and_extract(fallback_url, 'geckodriver.exe', headers)
                return
                
            logger.info(f"GeckoDriver最新バージョンをダウンロードします: {asset_url}")
            exe_name = 'geckodriver.exe' if sys.platform.startswith('win') else 'geckodriver'
            self._download_and_extract(asset_url, exe_name, headers)
            
        except Exception as e:
            error_and_exit(f"Geckodriver のダウンロードに失敗しました: {str(e)}", logger)
    
    def _download_chromedriver(self):
        """
        ChromeDriverの最新バージョンをダウンロードして展開する
        """
        logger.info('chromedriver.exe が見つかりません。最新バージョンをダウンロードします...')
        
        try:
            # 最新バージョンを取得
            url = "https://chromedriver.storage.googleapis.com/LATEST_RELEASE"
            version = requests.get(url).text.strip()
            
            # OSに合わせたzipファイルを選択
            zip_suffix = ""
            if sys.platform.startswith('win'):
                zip_suffix = "win32"
            elif sys.platform.startswith('darwin'):
                zip_suffix = "mac64"
            else:  # Linux
                zip_suffix = "linux64"
            
            download_url = f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_{zip_suffix}.zip"
            headers = {"User-Agent": f"DateInsert4AmazonPhoto/{__version__}"}
            
            exe_name = 'chromedriver.exe' if sys.platform.startswith('win') else 'chromedriver'
            self._download_and_extract(download_url, exe_name, headers)
            
        except Exception as e:
            error_and_exit(f"Chromedriver のダウンロードに失敗しました: {str(e)}", logger)
    
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
            
            # exe_nameに一致または終わるファイルを探す
            driver_file = None
            for file in files:
                if file.endswith(exe_name) or file == exe_name:
                    driver_file = file
                    break
                    
            if not driver_file:
                raise RuntimeError(f"{exe_name} が見つかりませんでした。利用可能なファイル: {', '.join(files)}")
            
            zip_file.extract(driver_file, path=dest_dir)
            
            # ネストされたパスの場合は移動
            extracted_path = os.path.join(dest_dir, driver_file)
            target_path = os.path.join(dest_dir, exe_name)
            if extracted_path != target_path:
                os.rename(extracted_path, target_path)
            
            # 実行権限を付与 (Linux/Mac)
            if not sys.platform.startswith('win'):
                os.chmod(target_path, 0o755)
        
        logger.info(f'{exe_name} を {dest_dir} に保存しました。')
    
    def start_browser(self):
        """
        選択したブラウザを起動し、WebDriverインスタンスを返す
        
        Returns:
            webdriver: 初期化されたWebDriverインスタンス
        """
        try:
            if self.browser_type == "firefox":
                self.driver = self._start_firefox()
            elif self.browser_type == "chrome":
                self.driver = self._start_chrome()
                
            return self.driver
            
        except WebDriverException as e:
            error_and_exit(f"{self.browser_type.capitalize()} WebDriver の起動に失敗: {str(e)}", logger)
    
    def _start_firefox(self):
        """
        Firefoxブラウザを起動する
        
        Returns:
            WebDriver: Firefox WebDriverインスタンス
        """
        options = FirefoxOptions()
        options.binary_location = self.browser_path
        
        # Firefox profileのパスを設定
        if os.path.isdir(self.profile_path):
            options.profile = self.profile_path
        
        # SeleniumのSystemPathに追加
        driver_dir = os.path.dirname(os.path.abspath(self.driver_path))
        os.environ["PATH"] = f"{driver_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        
        service = FirefoxService(executable_path=self.driver_path)
        logger.info(f"Firefoxを起動します。ドライバパス: {self.driver_path}")
        driver = webdriver.Firefox(service=service, options=options)
        logger.info("Firefox WebDriverの起動に成功しました。")
        return driver
    
    def _start_chrome(self):
        """
        Chromeブラウザを起動する
        
        Returns:
            WebDriver: Chrome WebDriverインスタンス
        """
        options = ChromeOptions()
        options.binary_location = self.browser_path
        
        # プロファイルパスを設定
        if os.path.isdir(self.profile_path):
            options.add_argument(f"user-data-dir={self.profile_path}")
        
        # SeleniumのSystemPathに追加
        driver_dir = os.path.dirname(os.path.abspath(self.driver_path))
        os.environ["PATH"] = f"{driver_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        
        service = ChromeService(executable_path=self.driver_path)
        logger.info(f"Chromeを起動します。ドライバパス: {self.driver_path}")
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("Chrome WebDriverの起動に成功しました。")
        return driver
    
    def wait_for_element(self, by, selector, timeout=10, condition=EC.presence_of_element_located):
        """
        指定した条件に一致する要素が表示されるまで待機
        
        Args:
            by: 検索方法（By.ID, By.CSS_SELECTOR など）
            selector: 検索するセレクタ
            timeout: タイムアウト時間（秒）
            condition: 待機条件 (例: presence_of_element_located, visibility_of_element_located)
            
        Returns:
            見つかった要素。見つからなければ None
        """
        if not self.driver:
            return None
            
        try:
            return WebDriverWait(self.driver, timeout).until(
                condition((by, selector))
            )
        except TimeoutException:
            logger.debug(f"要素が見つかりませんでした: {by}={selector}")
            return None
    
    def quit_browser(self):
        """
        ブラウザを安全に終了する
        """
        if self.driver:
            try:
                self.driver.quit()
                logger.debug("ブラウザを正常に終了しました。")
            except Exception as e:
                logger.warning(f"ブラウザ終了時にエラーが発生: {e}")
            finally:
                self.driver = None