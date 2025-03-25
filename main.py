import os
import sys
import json
import re
import io
import time
import zipfile
import logging
import requests
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -------------------------------
# ログ設定
# -------------------------------

def setup_logger():
    """ロガーの初期設定を行う。コンソールとファイルにログ出力する。"""
    logger = logging.getLogger("DateInsert4AmazonPhoto")
    logger.setLevel(logging.DEBUG)

    log_format = "%(levelname)-9s %(asctime)s [%(filename)s:%(lineno)d] %(message)s"

    class ColorFormatter(logging.Formatter):
        COLOR_MAP = {
            logging.DEBUG: "\033[37m",
            logging.INFO: "\033[32m",
            logging.WARNING: "\033[33m",
            logging.ERROR: "\033[31m",
            logging.CRITICAL: "\033[41m"
        }
        RESET = "\033[0m"

        def format(self, record):
            color = self.COLOR_MAP.get(record.levelno, self.RESET)
            message = super().format(record)
            return f"{color}{message}{self.RESET}"

    st_handler = logging.StreamHandler()
    st_handler.setLevel(logging.DEBUG)
    st_handler.setFormatter(ColorFormatter(log_format))

    fl_handler = logging.FileHandler(filename="Editor.log", encoding="utf-8")
    fl_handler.setLevel(logging.DEBUG)
    fl_handler.setFormatter(logging.Formatter(log_format))

    logger.addHandler(st_handler)
    logger.addHandler(fl_handler)

    return logger

logger = setup_logger()
logger.info("STARTUP")

# -------------------------------
# ユーティリティ関数
# -------------------------------

def error_and_exit(message):
    """エラーメッセージを表示して終了する"""
    logger.error(message)
    sys.exit(1)

def load_config(path="config.json"):
    """config.jsonを読み込み、辞書として返す"""
    if not os.path.exists(path):
        error_and_exit("設定ファイル config.json が見つかりません。")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        error_and_exit("config.json の形式に誤りがあります。")

def download_latest_geckodriver(dest_dir):
    """Geckodriverが存在しない場合、GitHubの最新版を自動でダウンロード"""
    exe_path = os.path.join(dest_dir, 'geckodriver.exe')
    if os.path.exists(exe_path):
        logger.info('geckodriver.exe は既に存在します。')
        return exe_path

    logger.info('geckodriver.exe が見つかりません。最新バージョンをダウンロードします...')

    headers = {'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'DateInsert4AmazonPhoto/1.0'}
    url = 'https://api.github.com/repos/mozilla/geckodriver/releases/latest'
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        assets = res.json()['assets']
        asset_url = next((a['browser_download_url'] for a in assets if 'win64.zip' in a['name']), None)
        if not asset_url:
            raise RuntimeError('Windows用geckodriverが見つかりませんでした。')

        zip_name = asset_url.split('/')[-1]
        with requests.get(asset_url, headers={'User-Agent': headers['User-Agent']}, stream=True) as r:
            r.raise_for_status()
            total = int(r.headers.get('content-length', 0))
            buffer = io.BytesIO()
            with tqdm(total=total, unit='B', unit_scale=True, desc=zip_name) as bar:
                for chunk in r.iter_content(chunk_size=8192):
                    buffer.write(chunk)
                    bar.update(len(chunk))

        buffer.seek(0)
        with zipfile.ZipFile(buffer) as zip_file:
            zip_file.extract('geckodriver.exe', path=dest_dir)

        logger.info(f'geckodriver.exe を {dest_dir} に保存しました。')
        return exe_path
    except Exception as e:
        error_and_exit(f"Geckodriver のダウンロードに失敗しました: {e}")

def extract_date_and_time_from_filename(filename):
    """VRChatのファイル名から日付と時刻を抽出して返す"""
    match = re.search(r"VRChat_(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})", filename)
    if not match:
        return None, None
    year, month, day, hour, minute, _ = match.groups()
    hour = int(hour)
    minute = int(minute)
    time_str = f"{'午前' if hour < 12 else '午後'}{hour % 12 if hour != 12 else 0}時{minute}分"
    return f"{year}-{month}-{day}", time_str

def wait_for_element(driver, by, selector, timeout=10):
    """指定した要素が表示されるまで待機し、返す。タイムアウト時はNone"""
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))
    except TimeoutException:
        return None

def start_browser(firefox_path, profile_path, geckodriver_path):
    """Firefoxブラウザを指定設定で起動する"""
    options = Options()
    options.binary_location = firefox_path
    options.profile = profile_path
    service = Service(executable_path=geckodriver_path)
    try:
        return webdriver.Firefox(service=service, options=options)
    except Exception as e:
        error_and_exit(f"Selenium WebDriver の起動に失敗: {str(e)}")

def set_shooting_date(driver):
    """ファイル名から抽出した日付をAmazon Photoの詳細ページに設定する"""
    try:
        if (info_button := wait_for_element(driver, By.CSS_SELECTOR, "button.info")):
            info_button.click()
            logger.info(" → 情報パネルを開きました。")
        try:
            existing = driver.find_element(By.CSS_SELECTOR, ".detail-item.date-info h4 button.edit-btn")
            if "編集" in existing.text:
                logger.info(" → 撮影日がすでに設定済みのためスキップします。")
                return False
        except Exception:
            pass
        if not (file_elem := wait_for_element(driver, By.CSS_SELECTOR, ".detail-item.file-info .label")):
            logger.warning(" → ファイル名要素が見つかりません。")
            return False
        filename = file_elem.text.strip()
        logger.info(f" → ファイル名: {filename}")
        date_str, time_str = extract_date_and_time_from_filename(filename)
        if not date_str or not time_str:
            logger.warning(" → ファイル名から日付/時間が抽出できません。")
            return False
        logger.info(f" → 抽出された日付: {date_str} / 時間: {time_str}")
        try:
            add_btn = driver.find_element(By.CSS_SELECTOR, ".info-item.editable .edit-btn")
            if "日付と時刻を追加" in add_btn.text:
                add_btn.click()
                logger.info(" → 日付追加ボタンをクリックしました。")
        except Exception:
            logger.warning(" → 日付追加ボタンが見つかりませんでした。スキップ。")
            return False
        year, month, day = date_str.split("-")
        wait_for_element(driver, By.CSS_SELECTOR, ".year.date-piece input[name='year']").send_keys(year)
        driver.find_element(By.CSS_SELECTOR, ".month.date-piece input[name='month']").send_keys(month)
        driver.find_element(By.CSS_SELECTOR, ".day.date-piece input[name='day']").send_keys(day)
        driver.find_element(By.CSS_SELECTOR, ".hour-minute.date-piece input[name='time']").send_keys(time_str)
        if (save_btn := wait_for_element(driver, By.CSS_SELECTOR, "button.button[aria-label='保存']")):
            save_btn.click()
            logger.info(" → 撮影日時を保存しました。")
            time.sleep(2)
            return True
    except Exception as e:
        logger.error(f" → 撮影日設定中のエラー: {type(e).__name__}: {e}")
    return False

# -------------------------------
# メイン処理
# -------------------------------

def main():
    """Amazon Photosを操作して、画像に日付メタデータを自動入力するメイン処理"""
    config = load_config()
    firefox_path = os.path.abspath(config.get("firefox_path", ""))
    gecko_path = os.path.abspath(config.get("geckodriver_path", ""))
    profile_path = os.path.abspath(config.get("profile_path", ""))
    target_url = config.get("target_url", "").strip()
    wait_sec = config.get("initial_wait", 5)

    if not os.path.isfile(firefox_path):
        error_and_exit(f"Firefox 実行ファイルが見つかりません: {firefox_path}")
    if not os.path.isdir(profile_path):
        error_and_exit(f"Firefox プロファイルが見つかりません: {profile_path}")
    if not target_url.startswith("http"):
        error_and_exit("target_url の指定が不正です。http で始まる URL を指定してください。")

    if not os.path.isfile(gecko_path):
        os.makedirs(os.path.dirname(gecko_path), exist_ok=True)
        gecko_path = download_latest_geckodriver(os.path.dirname(gecko_path))

    driver = start_browser(firefox_path, profile_path, gecko_path)

    logger.info("Amazon Photos にアクセスします...")
    driver.get(target_url)
    time.sleep(wait_sec)

    if "signin" in driver.current_url or "ap/signin" in driver.current_url:
        error_and_exit("Amazonログイン画面にリダイレクトされました。ログイン情報が含まれていない可能性があります。")

    while True:
        logger.info("写真一覧を取得中...")
        photo_links = driver.find_elements(By.CSS_SELECTOR, ".mosaic-item a")
        if not photo_links:
            logger.info("写真が見つかりませんでした。終了します。")
            break
        updated_any = False
        for i, link in enumerate(photo_links):
            url = link.get_attribute("href")
            if not url:
                continue
            logger.info(f"[{i + 1}] 写真詳細ページを処理中: {url}")
            driver.execute_script("window.open(arguments[0]);", url)
            driver.switch_to.window(driver.window_handles[1])
            time.sleep(1)
            if set_shooting_date(driver):
                updated_any = True
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        if not updated_any:
            logger.info("未設定の写真がありません。終了します。")
            break
        logger.info("ページを再読み込みします。")
        driver.refresh()
        time.sleep(wait_sec)

    logger.info("完了しました。ブラウザを閉じます。")
    driver.quit()

if __name__ == "__main__":
    main()
