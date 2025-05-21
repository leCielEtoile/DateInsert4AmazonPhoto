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
from modules.logger import setup_logger
from modules import load_config

logger = setup_logger()

class PhotoProcessor:
    """Amazon Photos上の写真を処理するクラス"""
    
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
        return self.driver.find_elements(By.CSS_SELECTOR, ".mosaic-item a")
    
    def process_photos(self, photo_links):
        """
        写真リンクのリストを処理
        
        Args:
            photo_links (list): 写真リンク要素のリスト
            
        Returns:
            bool: 少なくとも1つの写真が更新された場合はTrue
        """
        if not photo_links:
            return False
            
        updated_any = False
        
        for i, link in enumerate(photo_links):
            url = link.get_attribute("href")
            if not url:
                continue
                
            logger.info(f"[{i + 1}] 写真詳細ページを処理中: {url}")
            
            # 新しいタブで開く
            self.driver.execute_script("window.open(arguments[0]);", url)
            self.driver.switch_to.window(self.driver.window_handles[1])
            time.sleep(1)
            
            try:
                if self.set_shooting_date():
                    updated_any = True
            except Exception as e:
                logger.error(f"写真処理中にエラー発生: {type(e).__name__}: {e}")
                
            # タブを閉じてメインタブに戻る
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
        return updated_any
    
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
            
        year, month, day, hour, minute, _ = match.groups()
        hour = int(hour)
        minute = int(minute)
        
        # 午前/午後表記
        time_str = f"{'午前' if hour < 12 else '午後'}{hour % 12 if hour % 12 != 0 else 12}時{minute}分"
        
        # ログ出力は行わない（set_shooting_date側で出力する）
        return f"{year}-{month}-{day}", time_str
    
    def set_shooting_date(self):
        """
        現在表示中の写真詳細ページで、撮影日時を設定
        
        Returns:
            bool: 設定に成功した場合はTrue
        """
        try:
            # 情報パネルを開く
            info_button = self._wait_for_element(By.CSS_SELECTOR, "button.info")
            if info_button:
                info_button.click()
                logger.debug(" → 情報パネルを開きました。")
            
            # すでに撮影日があるか確認
            if self._is_date_already_set():
                logger.info(" → 撮影日がすでに設定済みのためスキップします。")
                return False
            
            # ファイル名取得
            filename = self._get_filename()
            if not filename:
                return False
                
            # 日付と時刻を抽出
            date_str, time_str = self.extract_date_and_time_from_filename(filename)
            if not date_str or not time_str:
                logger.warning(" → ファイル名から日付/時間が抽出できません。")
                return False
                
            logger.info(f" → 抽出された日付: {date_str} / 時間: {time_str}")
            
            # 日付入力フォームを開く
            if not self._open_date_form():
                return False
            
            # 入力処理前の値をログ出力（DEBUGレベルに変更）
            try:
                year_val = self.driver.find_element(By.CSS_SELECTOR, ".year.date-piece input[name='year']").get_attribute("value")
                month_val = self.driver.find_element(By.CSS_SELECTOR, ".month.date-piece input[name='month']").get_attribute("value")
                day_val = self.driver.find_element(By.CSS_SELECTOR, ".day.date-piece input[name='day']").get_attribute("value")
                time_val = self.driver.find_element(By.CSS_SELECTOR, ".hour-minute.date-piece input[name='time']").get_attribute("value")
                logger.debug(f" → 入力前の値: 年={year_val}, 月={month_val}, 日={day_val}, 時間={time_val}")
            except Exception as e:
                logger.debug(f" → 入力前の値の取得に失敗: {e}")
            
            # 入力処理
            self._input_date_time(date_str, time_str)
            
            # 入力処理後の値をログ出力（DEBUGレベルに変更）
            try:
                year_val = self.driver.find_element(By.CSS_SELECTOR, ".year.date-piece input[name='year']").get_attribute("value")
                month_val = self.driver.find_element(By.CSS_SELECTOR, ".month.date-piece input[name='month']").get_attribute("value")
                day_val = self.driver.find_element(By.CSS_SELECTOR, ".day.date-piece input[name='day']").get_attribute("value")
                time_val = self.driver.find_element(By.CSS_SELECTOR, ".hour-minute.date-piece input[name='time']").get_attribute("value")
                logger.debug(f" → 入力後の値: 年={year_val}, 月={month_val}, 日={day_val}, 時間={time_val}")
            except Exception as e:
                logger.debug(f" → 入力後の値の取得に失敗: {e}")
            
            # 保存
            return self._save_date_time()
            
        except Exception as e:
            logger.error(f" → 撮影日設定中のエラー: {type(e).__name__}: {e}")
            return False
    
    def _wait_for_element(self, by, selector, timeout=10):
        """
        要素が現れるのを待機
        
        Args:
            by: 検索方法
            selector: セレクタ
            timeout: タイムアウト時間
            
        Returns:
            見つかった要素。見つからなければNone
        """
        for delay in [1, 2, 3, 5, 10]:
            if delay > timeout:
                break
                
            try:
                element = self.driver.find_element(by, selector)
                if element.is_displayed():
                    return element
            except:
                pass
                
            time.sleep(1)
            
        return None
    
    def _is_date_already_set(self):
        """
        すでに撮影日が設定されているか確認
        
        Returns:
            bool: 設定済みの場合はTrue
        """
        try:
            existing = self.driver.find_element(By.CSS_SELECTOR, ".detail-item.date-info h4 button.edit-btn")
            return "編集" in existing.text
        except:
            return False
    
    def _get_filename(self):
        """
        ファイル名を取得
        
        Returns:
            str: ファイル名。取得できない場合はNone
        """
        file_elem = self._wait_for_element(By.CSS_SELECTOR, ".detail-item.file-info .label")
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
            add_btn = self.driver.find_element(By.CSS_SELECTOR, ".info-item.editable .edit-btn")
            if "日付と時刻を追加" in add_btn.text:
                add_btn.click()
                logger.debug(" → 日付追加ボタンをクリックしました。")
                return True
        except Exception:
            logger.warning(" → 日付追加ボタンが見つかりませんでした。スキップ。")
            
        return False
    
    def _input_date_time(self, date_str, time_str):
        """
        日付と時刻を入力
        
        Args:
            date_str (str): 日付文字列（YYYY-MM-DD）
            time_str (str): 時刻文字列（例: 午後2時5分）
        """
        # 日付をパースする
        year, month, day = date_str.split("-")
        
        # 各フィールドに入力前にクリアする
        year_field = self._wait_for_element(By.CSS_SELECTOR, ".year.date-piece input[name='year']")
        month_field = self.driver.find_element(By.CSS_SELECTOR, ".month.date-piece input[name='month']")
        day_field = self.driver.find_element(By.CSS_SELECTOR, ".day.date-piece input[name='day']")
        time_field = self.driver.find_element(By.CSS_SELECTOR, ".hour-minute.date-piece input[name='time']")
        
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
        time.sleep(1)  # 変更が適用されるための短い待機時間
    
    def _save_date_time(self):
        """
        日付と時刻を保存
        
        Returns:
            bool: 保存に成功した場合はTrue
        """
        save_btn = self._wait_for_element(By.CSS_SELECTOR, "button.button[aria-label='保存']")
        if save_btn:
            save_btn.click()
            logger.info(" → 撮影日時を保存しました。")
            time.sleep(2)
            return True
        
        logger.warning(" → 保存ボタンが見つかりません。")
        return False