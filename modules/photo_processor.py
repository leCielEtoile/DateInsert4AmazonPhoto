"""
photo_processor.py - Amazon Photos上の写真を処理するモジュール

このモジュールでは、以下の機能を提供:
- 写真一覧の取得
- 写真詳細ページの操作
- ファイル名からの日付時刻情報の抽出
- 撮影日時の設定
"""

import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from modules.logger import setup_logger
from modules import load_config

logger = setup_logger()

class PhotoProcessor:
    """Amazon Photos上の写真を処理するクラス"""
    
    # セレクタの一元管理（変更されやすい箇所）
    SELECTORS = {
        'photo_links': '.mosaic-item a',
        'info_button': 'button.info',
        'edit_button': '.detail-item.date-info h4 button.edit-btn',
        'date_label': '.detail-item.date-info .label',
        'time_span': '.detail-item.date-info .subs span',
        'file_info': '.detail-item.file-info .label',
        'add_date_button': '.info-item.editable .edit-btn',
        'year_field': '.year.date-piece input[name="year"]',
        'month_field': '.month.date-piece input[name="month"]',
        'day_field': '.day.date-piece input[name="day"]',
        'time_field': '.hour-minute.date-piece input[name="time"]',
        'save_button': 'button.button[aria-label="保存"]'
    }
    
    def __init__(self, driver):
        """
        初期化
        
        Args:
            driver (WebDriver): 初期化済みのWebDriverインスタンス
        """
        self.driver = driver
        self.config = load_config()
        self.filename_pattern = self.config.get("filename_pattern", 
                                               "VRChat_(\\d{4})-(\\d{2})-(\\d{2})_(\\d{2})-(\\d{2})-(\\d{2})")
    
    def get_photo_links(self):
        """
        現在表示されている写真一覧からリンクを取得
        
        Returns:
            list: 写真リンク要素のリスト
        """
        return self.driver.find_elements(By.CSS_SELECTOR, self.SELECTORS['photo_links'])
    
    def process_photos(self, photo_links):
        """
        写真リンクのリストを処理
        
        Args:
            photo_links (list): 写真リンク要素のリスト
            
        Returns:
            bool: まだ処理が必要な写真がある場合はTrue
                  （すべての写真が正しい日付で設定済みならFalse）
        """
        if not photo_links:
            return False
            
        all_processed = True  # すべての写真が正しく処理された場合True
        
        for i, link in enumerate(photo_links):
            try:
                url = link.get_attribute("href")
                if not url:
                    continue
                    
                logger.info(f"[{i + 1}/{len(photo_links)}] 写真詳細ページを処理中: {url}")
                
                # 新しいタブで開く
                self.driver.execute_script("window.open(arguments[0]);", url)
                self.driver.switch_to.window(self.driver.window_handles[1])
                time.sleep(1)
                
                try:
                    # 写真の処理が必要だった場合（設定されていないか、不正確な場合）
                    if self.set_shooting_date():
                        all_processed = False  # まだ処理が必要な写真がある
                except Exception as e:
                    logger.error(f"写真処理中にエラー発生: {type(e).__name__}: {e}")
                    all_processed = False  # エラーが発生したので再処理の可能性あり
                    
            except (StaleElementReferenceException, NoSuchElementException) as e:
                logger.warning(f"要素にアクセスできません: {e}")
                all_processed = False
            finally:
                # タブを閉じてメインタブに戻る
                try:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                except Exception as e:
                    logger.error(f"タブ操作中にエラー: {e}")
                    # ブラウザを回復させる試み
                    if len(self.driver.window_handles) > 0:
                        self.driver.switch_to.window(self.driver.window_handles[0])
        
        # 戻り値を逆にする - まだ処理が必要な写真があるかどうか
        return not all_processed
    
    def extract_date_and_time_from_filename(self, filename):
        """
        ファイル名から日付と時刻を抽出
        
        Args:
            filename (str): ファイル名
            
        Returns:
            tuple: (date_str, time_str) または抽出失敗時は (None, None)
                   例: ("2024-03-25", "午後2時5分")
        """
        match = re.search(self.filename_pattern, filename)
        if not match:
            return None, None
            
        # すべての値を取得 (year, month, day, hour, minute, second)
        groups = match.groups()
        if len(groups) < 6:
            logger.warning("ファイル名のパターンが期待する形式と一致しません。少なくとも6つのグループが必要です。")
            return None, None
            
        year, month, day, hour, minute, _ = groups
        
        try:
            hour_int = int(hour)
            minute_int = int(minute)
            
            # 午前/午後表記
            am_pm = '午前' if hour_int < 12 else '午後'
            hour_12 = hour_int % 12
            if hour_12 == 0:
                hour_12 = 12
                
            time_str = f"{am_pm}{hour_12}時{minute_int}分"
            date_str = f"{year}-{month}-{day}"
            
            return date_str, time_str
        except ValueError as e:
            logger.warning(f"日付/時間の変換エラー: {e}")
            return None, None
    
    def set_shooting_date(self):
        """
        現在表示中の写真詳細ページで、撮影日時を設定または更新
        
        Returns:
            bool: 設定/更新に成功した場合はTrue
        """
        try:
            # 情報パネルを開く
            info_button = self._wait_for_element(By.CSS_SELECTOR, self.SELECTORS['info_button'])
            if info_button:
                info_button.click()
                logger.debug(" → 情報パネルを開きました。")
            else:
                logger.warning(" → 情報ボタンが見つかりません。")
                return False
            
            # ファイル名取得
            filename = self._get_filename()
            if not filename:
                return False
                
            # ファイル名から日付と時刻を抽出
            file_date_str, file_time_str = self.extract_date_and_time_from_filename(filename)
            if not file_date_str or not file_time_str:
                logger.warning(" → ファイル名から日付/時間が抽出できません。")
                return False
                
            logger.info(f" → ファイル名から抽出: 日付={file_date_str}, 時間={file_time_str}")
            
            # 既存の日付設定を確認
            is_date_set, current_date_str, current_time_str = self._is_date_already_set()
            
            if is_date_set:
                logger.debug(f" → 現在の設定: 日付={current_date_str}, 時間={current_time_str}")
                
                # 日付と時刻が正しいか比較
                if current_date_str == file_date_str and current_time_str == file_time_str:
                    logger.info(" → 撮影日時は正しく設定されています。スキップします。")
                    return False
                else:
                    logger.info(" → 撮影日時が異なります。更新します。")
                    # 編集ボタンをクリック
                    edit_btn = self.driver.find_element(By.CSS_SELECTOR, self.SELECTORS['edit_button'])
                    edit_btn.click()
                    logger.debug(" → 日付編集ダイアログを開きました。")
            else:
                # 日付設定がまだない場合
                logger.info(" → 撮影日時が未設定です。新規設定します。")
                if not self._open_date_form():
                    return False
            
            # 日付と時刻を入力
            if not self._input_date_time(file_date_str, file_time_str):
                return False
            
            # 保存
            result = self._save_date_time()
            if result:
                if is_date_set:
                    logger.info(" → 撮影日時を更新しました。")
                else:
                    logger.info(" → 撮影日時を新規設定しました。")
            return result
            
        except Exception as e:
            logger.error(f" → 撮影日設定中のエラー: {type(e).__name__}: {e}")
            return False
    
    def _wait_for_element(self, by, selector, timeout=10, condition=EC.presence_of_element_located):
        """
        指定した条件に一致する要素が現れるまで待機
        
        Args:
            by: 検索方法
            selector: セレクタ
            timeout: タイムアウト時間
            condition: 待機条件
            
        Returns:
            見つかった要素。見つからなければNone
        """
        if hasattr(self.driver, 'wait_for_element'):
            # DriverManagerのメソッドを使用
            return self.driver.wait_for_element(by, selector, timeout, condition)
        
        # 従来のポーリング方式（互換性のため）
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                element = self.driver.find_element(by, selector)
                if element.is_displayed():
                    return element
            except:
                pass
            time.sleep(0.5)
        return None
    
    def _is_date_already_set(self):
        """
        撮影日が設定されているか確認し、設定されている場合は
        現在設定されている日付と時刻を取得する
        
        Returns:
            tuple: (is_set, date_str, time_str)
                is_set: 設定済みの場合はTrue
                date_str: 設定されている日付 (例: "2025-05-15")
                time_str: 設定されている時間 (例: "午後9時10分")
        """
        try:
            edit_btn = self.driver.find_element(By.CSS_SELECTOR, self.SELECTORS['edit_button'])
            if "編集" in edit_btn.text:
                # 日付要素と時刻要素を取得
                date_label = self.driver.find_element(By.CSS_SELECTOR, self.SELECTORS['date_label']).text
                time_span = self.driver.find_element(By.CSS_SELECTOR, self.SELECTORS['time_span']).text
                
                # フォーマット変換 (例: "2025年5月15日" -> "2025-05-15")
                date_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_label)
                if date_match:
                    year, month, day = date_match.groups()
                    month = month.zfill(2)  # 1桁の月を2桁に
                    day = day.zfill(2)      # 1桁の日を2桁に
                    date_str = f"{year}-{month}-{day}"
                    
                    # 時刻はそのまま使用 (例: "午後9時10分")
                    time_str = re.sub(r"^.*?, ", "", time_span)  # "木曜日, 午後9時10分" -> "午後9時10分"
                    
                    return True, date_str, time_str
        except Exception as e:
            logger.debug(f" → 日付情報の解析エラー: {e}")
        
        return False, None, None
    
    def _get_filename(self):
        """
        ファイル名を取得
        
        Returns:
            str: ファイル名。取得できない場合はNone
        """
        file_elem = self._wait_for_element(By.CSS_SELECTOR, self.SELECTORS['file_info'])
        if not file_elem:
            logger.warning(" → ファイル名要素が見つかりません。")
            return None
            
        filename = file_elem.text.strip()
        logger.info(f" → ファイル名: {filename}")
        return filename
    
    def _open_date_form(self):
        """
        日付入力フォームを開く
        
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            add_btn = self.driver.find_element(By.CSS_SELECTOR, self.SELECTORS['add_date_button'])
            if "日付と時刻を追加" in add_btn.text:
                add_btn.click()
                logger.debug(" → 日付追加ボタンをクリックしました。")
                # ダイアログが表示されるまで短時間待機
                time.sleep(0.5)
                return True
        except NoSuchElementException:
            logger.warning(" → 日付追加ボタンが見つかりませんでした。")
        except Exception as e:
            logger.warning(f" → 日付追加ボタンのクリック中にエラー: {e}")
            
        return False
    
    def _input_date_time(self, date_str, time_str):
        """
        日付と時刻を入力
        
        Args:
            date_str (str): 日付文字列（YYYY-MM-DD）
            time_str (str): 時刻文字列（例: 午後2時5分）
            
        Returns:
            bool: 入力に成功した場合はTrue
        """
        try:
            # 日付をパースする
            year, month, day = date_str.split("-")
            
            # 各フィールドを取得
            year_field = self._wait_for_element(
                By.CSS_SELECTOR, 
                self.SELECTORS['year_field'],
                condition=EC.visibility_of_element_located
            )
            
            if not year_field:
                logger.warning(" → 入力フォームが見つかりません。")
                return False
                
            month_field = self.driver.find_element(By.CSS_SELECTOR, self.SELECTORS['month_field'])
            day_field = self.driver.find_element(By.CSS_SELECTOR, self.SELECTORS['day_field'])
            time_field = self.driver.find_element(By.CSS_SELECTOR, self.SELECTORS['time_field'])
            
            # フィールドをクリア
            year_field.clear()
            month_field.clear()
            day_field.clear()
            time_field.clear()
            
            # 各フィールドに入力
            year_field.send_keys(year)
            month_field.send_keys(month)
            day_field.send_keys(day)
            time_field.send_keys(time_str)
            
            # 念のため日付確定のために、日付の選択後に別の要素にフォーカスを移す
            self.driver.execute_script("arguments[0].blur();", time_field)
            # 変更が適用されるための短い待機時間
            time.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f" → 日付入力中にエラー: {e}")
            return False
    
    def _save_date_time(self):
        """
        日付と時刻を保存
        
        Returns:
            bool: 保存に成功した場合はTrue
        """
        save_btn = self._wait_for_element(
            By.CSS_SELECTOR, 
            self.SELECTORS['save_button'],
            condition=EC.element_to_be_clickable
        )
        
        if save_btn:
            try:
                save_btn.click()
                # 保存が完了するまで待機
                time.sleep(2)
                logger.info(" → 撮影日時を保存しました。")
                return True
            except Exception as e:
                logger.error(f" → 保存ボタンのクリック中にエラー: {e}")
        else:
            logger.warning(" → 保存ボタンが見つかりません。")
            
        return False