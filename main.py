"""
main.py - Amazon Photos 上の VRChat スクリーンショットに対して、ファイル名から抽出した日付・時刻を
撮影日時として自動設定するスクリプト。

依存モジュール:
- logger.py: カラー付きログ出力設定
- config.py: 設定ファイルの読み込みとエラー処理
- geckodriver.py: GeckoDriver の存在確認と自動ダウンロード

外部ライブラリ:
- Selenium: ブラウザ操作用
- tqdm, requests: ダウンロード処理支援
"""

from modules import setup_logger, load_config, error_and_exit, download_latest_geckodriver, __version__

import os
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = setup_logger()
logger.info(f"STARTUP - DateInsert4AmazonPhoto v{__version__}")

# -------------------------------
# ユーティリティ関数
# -------------------------------

def extract_date_and_time_from_filename(filename):
    """
    VRChatのファイル名から日付と時刻を抽出して返す。
    ファイル名形式: VRChat_YYYY-MM-DD_HH-MM-SS_xxx.png
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

def start_browser(firefox_path, profile_path, geckodriver_path):
    """
    指定されたFirefox実行ファイル・プロファイル・geckodriverを使用してブラウザを起動する。
    起動に失敗した場合はログを出して終了。
    """
    options = Options()
    options.binary_location = firefox_path
    options.profile = profile_path
    service = Service(executable_path=geckodriver_path)
    try:
        return webdriver.Firefox(service=service, options=options)
    except Exception as e:
        error_and_exit(f"Selenium WebDriver の起動に失敗: {str(e)}")

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
    アプリケーションのエントリーポイント。
    設定を読み込み、ブラウザを起動し、各画像に対して自動的に撮影日時を設定する。
    """
    config = load_config()
    firefox_path = os.path.abspath(config.get("firefox_path", ""))
    gecko_path = os.path.abspath(config.get("geckodriver_path", ""))
    profile_path = os.path.abspath(config.get("profile_path", ""))
    target_url = config.get("target_url", "").strip()
    wait_sec = config.get("initial_wait", 5)

    # 各種パス確認
    if not os.path.isfile(firefox_path):
        error_and_exit(f"Firefox 実行ファイルが見つかりません: {firefox_path}")
    if not os.path.isdir(profile_path):
        error_and_exit(f"Firefox プロファイルが見つかりません: {profile_path}")
    if not target_url.startswith("http"):
        error_and_exit("target_url の指定が不正です。http で始まる URL を指定してください。")

    # GeckoDriverが存在しない場合、自動で取得
    if not os.path.isfile(gecko_path):
        os.makedirs(os.path.dirname(gecko_path), exist_ok=True)
        gecko_path = download_latest_geckodriver(os.path.dirname(gecko_path))

    driver = start_browser(firefox_path, profile_path, gecko_path)

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

    logger.info("処理を終了します。")
    driver.quit()

if __name__ == "__main__":
    main()
