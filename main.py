"""
main.py - Amazon Photos 上の VRChat スクリーンショットに対して、ファイル名から抽出した日付・時刻を
撮影日時として自動設定するスクリプト。

依存モジュール:
- logger.py: カラー付きログ出力設定
- config.py: 設定ファイルの読み込みとエラー処理（INI形式対応）
- geckodriver.py / chromedriver.py: 各ブラウザ用ドライバの確認と自動ダウンロード

外部ライブラリ:
- Selenium: ブラウザ操作用
- tqdm, requests: ダウンロード処理支援
"""

from modules import setup_logger, load_config, error_and_exit, download_latest_geckodriver, download_latest_chromedriver, __version__

import os
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions

# ロガー初期化
logger = setup_logger()
logger.info(f"STARTUP - DateInsert4AmazonPhoto v{__version__}")

# -------------------------------
# ユーティリティ関数
# -------------------------------

def extract_date_and_time_from_filename(filename):
    """
    VRChat のスクリーンショットファイル名から日付と時刻を抽出する
    ファイル形式: VRChat_YYYY-MM-DD_HH-MM-SS_xxx.png
    Returns:
        (date_str, time_str) 例: ("2024-03-25", "午後2時5分")
    """
    match = re.search(r"VRChat_(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})", filename)
    if not match:
        return None, None
    year, month, day, hour, minute, _ = match.groups()
    hour = int(hour)
    minute = int(minute)
    time_str = f"{'午前' if hour < 12 else '午後'}{hour % 12 if hour != 12 else 0}時{minute}分"
    return f"{year}-{month}-{day}", time_str

def wait_for_element(driver, by, selector):
    """
    セレクタに一致する要素がDOM上に現れるまで1, 2, 3, 5, 10秒try
    見つからない場合はNoneを返す。
    """
    for delay in [1, 2, 3, 5, 10]:
        try:
            return WebDriverWait(driver, delay).until(EC.presence_of_element_located((by, selector)))
        except TimeoutException:
            continue
    return None

def expand_env_path(path):
    """Windows環境変数（%APPDATA% など）を展開する"""
    return os.path.expandvars(path)

def start_browser(config):
    """
    指定されたブラウザ（firefox または chrome）を起動する。
    config.ini に基づき必要なパスを読み取り、自動でドライバも確認・ダウンロードする。
    Returns:
        Selenium WebDriver オブジェクト
    """
    browser = config.get("general", "browser", fallback="firefox").lower()

    if browser == "firefox":
        firefox_path = config.get("firefox", "firefox_path")
        gecko_path = config.get("firefox", "geckodriver_path")
        profile_path = config.get("firefox", "profile_path")
        if not os.path.isfile(gecko_path):
            os.makedirs(os.path.dirname(gecko_path), exist_ok=True)
            gecko_path = download_latest_geckodriver(os.path.dirname(gecko_path))
        options = FirefoxOptions()
        options.binary_location = firefox_path
        options.profile = profile_path
        service = FirefoxService(executable_path=gecko_path)
        return webdriver.Firefox(service=service, options=options)

    elif browser == "chrome":
        chrome_path = config.get("chrome", "chrome_path")
        chromedriver_path = config.get("chrome", "chromedriver_path")
        profile_directory = config.get("chrome", "profile_directory", fallback="Default")
        # %appdata%などを展開
        raw_user_data_dir = config.get("chrome", "user_data_dir")
        user_data_dir = expand_env_path(raw_user_data_dir)
        os.makedirs(user_data_dir, exist_ok=True)

        if not os.path.isfile(chromedriver_path):
            os.makedirs(os.path.dirname(chromedriver_path), exist_ok=True)
            chromedriver_path = download_latest_chromedriver(os.path.dirname(chromedriver_path))

        options = ChromeOptions()
        options.binary_location = chrome_path
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument(f"--profile-directory={profile_directory}")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        service = ChromeService(executable_path=chromedriver_path)
        return webdriver.Chrome(service=service, options=options)

    else:
        error_and_exit(f"未対応のブラウザが指定されました: {browser}")

def set_shooting_date(driver):
    """
    現在表示中のAmazon Photosの詳細ページで、ファイル名から抽出した日時を撮影日として入力する。
    編集済みの場合はスキップする。
    Returns:
        True: 日付設定に成功した場合
        False: スキップまたは失敗
    """
    try:
        if (info_button := wait_for_element(driver, By.CSS_SELECTOR, "button.info")):
            info_button.click()
            logger.info(" → 情報パネルを開きました。")

        # すでに撮影日があるか確認
        try:
            existing = driver.find_element(By.CSS_SELECTOR, ".detail-item.date-info h4 button.edit-btn")
            if "編集" in existing.text:
                logger.info(" → 撮影日がすでに設定済みのためスキップします。")
                return False
        except Exception:
            pass  # 編集ボタンが見つからなければ、未設定扱い

        # ファイル名取得
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

        # 日付入力フォームを開く
        try:
            add_btn = driver.find_element(By.CSS_SELECTOR, ".info-item.editable .edit-btn")
            if "日付と時刻を追加" in add_btn.text:
                add_btn.click()
                logger.info(" → 日付追加ボタンをクリックしました。")
        except Exception:
            logger.warning(" → 日付追加ボタンが見つかりませんでした。スキップ。")
            return False

        # 入力処理
        year, month, day = date_str.split("-")
        wait_for_element(driver, By.CSS_SELECTOR, ".year.date-piece input[name='year']").send_keys(year)
        driver.find_element(By.CSS_SELECTOR, ".month.date-piece input[name='month']").send_keys(month)
        driver.find_element(By.CSS_SELECTOR, ".day.date-piece input[name='day']").send_keys(day)
        driver.find_element(By.CSS_SELECTOR, ".hour-minute.date-piece input[name='time']").send_keys(time_str)

        # 保存ボタン押下
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
    """
    アプリのエントリーポイント。config.ini を読み込み、指定ブラウザで Amazon Photos にアクセス。
    撮影日時が未設定の画像に対し、ファイル名から撮影日時を自動設定する。
    """
    config = load_config()
    target_url = config.get("general", "target_url", fallback="").strip()
    wait_sec = config.getint("general", "initial_wait", fallback=5)

    if not target_url.startswith("http"):
        error_and_exit("target_url の指定が不正です。http で始まる URL を指定してください。")

    driver = None
    try:
        driver = start_browser(config)
        logger.info("Amazon Photos にアクセスします...")
        driver.get(target_url)
        time.sleep(wait_sec)

        if "signin" in driver.current_url or "ap/signin" in driver.current_url:
            error_and_exit("Amazonログイン画面にリダイレクトされました。ログイン情報が含まれていない可能性があります。")

        # メイン処理ループ（画像1枚ずつ開いて処理）
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

    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.warning(f"ブラウザの終了時にエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
