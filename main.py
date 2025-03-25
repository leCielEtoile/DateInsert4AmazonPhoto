import json
import os
import sys
import time
import re
import logging
import io
import zipfile
import requests
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -------------------------------
# ログ設定（色付き、ファイル + コンソール）
# -------------------------------

logger = logging.getLogger("DateInsert4AmazonPhoto")
logger.setLevel(logging.DEBUG)

log_format = "%(levelname)-9s %(asctime)s [%(filename)s:%(lineno)d] %(message)s"

# 色付きログ出力（コンソール用）
class ColorFormatter(logging.Formatter):
    COLOR_MAP = {
        logging.DEBUG: "\033[37m",   # Gray
        logging.INFO: "\033[32m",    # Green
        logging.WARNING: "\033[33m", # Yellow
        logging.ERROR: "\033[31m",   # Red
        logging.CRITICAL: "\033[41m" # Red Background
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLOR_MAP.get(record.levelno, self.RESET)
        message = super().format(record)
        return f"{color}{message}{self.RESET}"

# コンソールログ設定
st_handler = logging.StreamHandler()
st_handler.setLevel(logging.DEBUG)
st_handler.setFormatter(ColorFormatter(log_format))

# ファイルログ設定（Editor.log に出力）
fl_handler = logging.FileHandler(filename="Editor.log", encoding="utf-8")
fl_handler.setLevel(logging.DEBUG)
fl_handler.setFormatter(logging.Formatter(log_format))

# ハンドラ登録
logger.addHandler(st_handler)
logger.addHandler(fl_handler)

logger.info("STARTUP")

# -------------------------------
# エラーハンドラ
# -------------------------------

def error_and_exit(message):
    logger.error(message)
    sys.exit(1)

# -------------------------------
# GeckoDriver 自動ダウンロード処理
# -------------------------------

def download_latest_geckodriver(dest_dir: str):
    exe_path = os.path.join(dest_dir, 'geckodriver.exe')
    if os.path.exists(exe_path):
        logger.info('geckodriver.exe は既に存在します。')
        return exe_path

    logger.info('geckodriver.exe が見つかりません。最新バージョンをダウンロードします...')

    api_url = 'https://api.github.com/repos/mozilla/geckodriver/releases/latest'
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'DateInsert4AmazonPhoto/1.0 (https://github.com/your-repo)'
    }
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        release_data = response.json()

        asset_url = None
        for asset in release_data['assets']:
            if 'win64.zip' in asset['name']:
                asset_url = asset['browser_download_url']
                break

        if not asset_url:
            raise RuntimeError('Windows用geckodriverが見つかりませんでした。')

        zip_name = asset_url.split('/')[-1]
        logger.info(f"{zip_name} をダウンロード中...")

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

# -------------------------------
# ファイル名から撮影日を抽出（例: VRChat_2023-01-01_12-00-00.png）
# -------------------------------

def extract_date_and_time_from_filename(filename: str):
    match = re.search(r"VRChat_(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})", filename)
    if not match:
        return None, None

    year, month, day, hour, minute, second = match.groups()
    hour_int = int(hour)
    minute_int = int(minute)

    if hour_int == 0:
        time_str = f"午前0時{minute_int}分"
    elif hour_int < 12:
        time_str = f"午前{hour_int}時{minute_int}分"
    elif hour_int == 12:
        time_str = f"午後0時{minute_int}分"
    else:
        time_str = f"午後{hour_int - 12}時{minute_int}分"

    date_str = f"{year}-{month}-{day}"
    return date_str, time_str

# -------------------------------
# 設定ファイル（config.json）読み込み・GeckoDriver 自動チェック
# -------------------------------

CONFIG_FILE = "config.json"
if not os.path.exists(CONFIG_FILE):
    error_and_exit("設定ファイル config.json が見つかりません。")

try:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
except json.JSONDecodeError:
    error_and_exit("config.json の形式に誤りがあります。")

firefox_path = os.path.abspath(config.get("firefox_path", ""))
geckodriver_path = os.path.abspath(config.get("geckodriver_path", ""))
profile_path = os.path.abspath(config.get("profile_path", ""))
target_url = config.get("target_url", "").strip()

if not os.path.isfile(firefox_path):
    error_and_exit(f"Firefox 実行ファイルが見つかりません: {firefox_path}")
if not os.path.isdir(profile_path):
    error_and_exit(f"Firefox プロファイルが見つかりません: {profile_path}")
if not target_url.startswith("http"):
    error_and_exit("target_url の指定が不正です。http で始まる URL を指定してください。")

# geckodriver.exe が無ければダウンロード
if not os.path.isfile(geckodriver_path):
    dest_dir = os.path.dirname(geckodriver_path)
    os.makedirs(dest_dir, exist_ok=True)
    geckodriver_path = download_latest_geckodriver(dest_dir)

# -------------------------------
# Firefox + Selenium 起動
# -------------------------------

options = Options()
options.binary_location = firefox_path
options.profile = profile_path  # Selenium 4以降推奨のプロファイル指定方法

service = Service(executable_path=geckodriver_path)

try:
    driver = webdriver.Firefox(service=service, options=options)
except Exception as e:
    error_and_exit(f"Selenium WebDriver の起動に失敗: {str(e)}")

# -------------------------------
# 撮影日設定処理
# -------------------------------

def wait_for_element(driver, by, selector):
    for delay in [1, 2, 3, 5, 10]:
        try:
            return WebDriverWait(driver, delay).until(EC.presence_of_element_located((by, selector)))
        except TimeoutException:
            continue
    return None

def set_shooting_date(driver) -> bool:
    try:
        # 「情報」パネル展開
        try:
            info_button = wait_for_element(driver, By.CSS_SELECTOR, "button.info")
            if info_button:
                info_button.click()
                logger.info(" → 情報パネルを開きました。")
        except Exception:
            logger.warning(" → 情報ボタンが見つかりません。スキップ。")
            return False

        # すでに編集ボタンがあるか確認（設定済み）
        try:
            existing = driver.find_element(By.CSS_SELECTOR, ".detail-item.date-info h4 button.edit-btn")
            if "編集" in existing.text:
                logger.info(" → 撮影日がすでに設定済みのためスキップします。")
                return False
        except Exception:
            pass

        # ファイル名取得
        file_info_elem = wait_for_element(driver, By.CSS_SELECTOR, ".detail-item.file-info .label")
        if not file_info_elem:
            logger.warning(" → ファイル名要素が見つかりません。")
            return False
        filename = file_info_elem.text.strip()
        logger.info(f" → ファイル名: {filename}")

        # ファイル名から日時を抽出
        date_str, time_str = extract_date_and_time_from_filename(filename)
        if not date_str or not time_str:
            logger.warning(" → ファイル名から日付/時間が抽出できません。")
            return False

        logger.info(f" → 抽出された日付: {date_str} / 時間: {time_str}")

        # 日付編集の「追加」ボタンを押す（未設定時）
        try:
            add_date_button = driver.find_element(By.CSS_SELECTOR, ".info-item.editable .edit-btn")
            if "日付と時刻を追加" in add_date_button.text:
                add_date_button.click()
                logger.info(" → 日付追加ボタンをクリックしました。")
        except Exception:
            logger.warning(" → 日付追加ボタンが見つかりませんでした。スキップ。")
            return False

        # 年月日入力
        year, month, day = date_str.split("-")
        wait_for_element(driver, By.CSS_SELECTOR, ".year.date-piece input[name='year']").send_keys(year)
        driver.find_element(By.CSS_SELECTOR, ".month.date-piece input[name='month']").send_keys(month)
        driver.find_element(By.CSS_SELECTOR, ".day.date-piece input[name='day']").send_keys(day)

        driver.find_element(By.CSS_SELECTOR, ".hour-minute.date-piece input[name='time']").send_keys(time_str)

        save_button = wait_for_element(driver, By.CSS_SELECTOR, "button.button[aria-label='保存']")
        if save_button:
            save_button.click()
            logger.info(" → 撮影日時を保存しました。")
            time.sleep(2)
            return True

    except TimeoutException:
        logger.error(" → 要素の読み込みがタイムアウトしました。画面の読み込みが遅い可能性があります。")
        return False
    except NoSuchElementException as e:
        logger.warning(f" → 要素が見つかりません: {str(e)}")
        return False
    except Exception as e:
        logger.error(f" → 予期せぬエラーが発生: {type(e).__name__}: {str(e)}")
        return False

# -------------------------------
# メイン処理（Amazon Photos の自動処理）
# -------------------------------

logger.info("Amazon Photos にアクセスします...")
driver.get(target_url)
time.sleep(config.get("initial_wait", 5))

# ログイン画面チェック
if "signin" in driver.current_url or "ap/signin" in driver.current_url:
    error_and_exit("Amazonログイン画面にリダイレクトされました。プロファイルにログイン情報が含まれていない可能性があります。")

# 処理ループ
while True:
    logger.info("写真一覧を取得中...")
    photo_links = driver.find_elements(By.CSS_SELECTOR, ".mosaic-item a")

    if not photo_links:
        logger.info("写真が見つかりませんでした。処理を終了します。")
        break

    updated_any = False

    for index, link in enumerate(photo_links):
        photo_url = link.get_attribute("href")
        if not photo_url:
            continue

        logger.info(f"[{index + 1}] 写真詳細ページを処理中: {photo_url}")

        # 詳細ページを別タブで開いて処理
        driver.execute_script("window.open(arguments[0]);", photo_url)
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(1)

        if set_shooting_date(driver):
            updated_any = True

        # タブを閉じて元に戻る
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    if not updated_any:
        logger.info("未設定の写真がありません。終了します。")
        break

    logger.info("ページを再読み込みします。")
    driver.refresh()
    time.sleep(config.get("initial_wait", 5))

logger.info("完了しました。ブラウザを閉じます。")
driver.quit()
