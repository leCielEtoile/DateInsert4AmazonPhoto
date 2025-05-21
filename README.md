# DateInsert4AmazonPhoto

Amazon Photos にアップロードされた VRChat のスクリーンショット画像に対して、
**ファイル名から撮影日時を自動抽出し、Amazon Photos のメタデータとして反映する自動化ツール**です。

---
<br>

## ✨ 主な機能

- VRChat のファイル名 (例: `VRChat_<年>-<月>-<日>_<時>-<分>-00.000_xyz.png`) から日付と時刻を抽出
- Amazon Photos の写真詳細画面を自動操作
- 撮影日および時刻を入力・保存
- 既存の日時設定を自動比較し、必要に応じて修正
- 設定ファイル (`config.yaml`) によりカスタマイズ可能
- 詳細なログ出力（コンソールとファイル）による動作確認

---
<br>

## ⚡ 動作要件

- Windows 10 / 11
- Firefox（Portable版 または 通常インストール版）または Chrome
- WebDriver（Firefox用GeckoDriver/Chrome用ChromeDriver - 自動ダウンロードされます）
- Python 3.8以上

---
<br>

## 🔹 使用方法

### 1. ブラウザの設定

#### Firefoxを使用する場合

##### Portable版Firefoxを使用する場合:

- [PortableApps.com](https://portableapps.com/apps/internet/firefox_portable) より Firefox Portable をダウンロードしてください
- 任意のフォルダに解凍し、以下のような構成にしてください：

```
DateInsert4AmazonPhoto/
├── FirefoxPortable/           ← ポータブルFirefox一式
|   └── FirefoxPortable.exe    ← ログイン情報登録に使用
└── DateInsert4AmazonPhoto.exe
```

##### 通常のFirefoxを使用する場合:

- `DateInsert4AmazonPhoto.exe` を起動すると `config.yaml` が自動生成されます
- 以下のように設定を編集してください：

```yaml
# ブラウザ設定
browser_type: firefox  # 使用するブラウザ ('firefox' または 'chrome')
firefox_path: C:/Program Files/Mozilla Firefox/firefox.exe  # Firefox実行ファイルのパス
profile_path: C:/Users/ユーザー名/AppData/Roaming/Mozilla/Firefox/Profiles/xxxxx.default  # プロファイルフォルダ
```

#### Chromeを使用する場合:

- `config.yaml` で以下のように設定します：

```yaml
# ブラウザ設定
browser_type: chrome  # 使用するブラウザ ('firefox' または 'chrome')
chrome_path: C:/Program Files/Google/Chrome/Application/chrome.exe  # Chrome実行ファイルのパス
profile_path: C:/Users/ユーザー名/AppData/Local/Google/Chrome/User Data/Default  # プロファイルフォルダ
```

### 2. Amazon Photos にログイン

- 設定したブラウザを起動し、[Amazon Photos](https://www.amazon.co.jp/photos/) にアクセスしてログインしてください
- ログイン情報はプロファイルに保存され、以後の自動操作で利用されます

---

### 3. アプリを起動

- `DateInsert4AmazonPhoto.exe` を実行すると、以下の処理が行われます：
  - 設定されていない画像には新規に撮影日時が設定されます
  - 既に設定済みの画像は、ファイル名から抽出した日時と比較し、不一致があれば自動的に修正されます
- 進捗ログはコンソールと `logs/app.log` に出力されます

---
<br>

## 🔧 config.yaml の設定項目

```yaml
# DateInsert4AmazonPhoto 設定ファイル
#
# このファイルでは、アプリケーションの動作を制御するための設定を行います。
# 各設定項目の説明は、項目の横のコメントを参照してください。

#=====================================================================
# ブラウザ設定
#=====================================================================
browser_type: firefox  # 使用するブラウザ ('firefox' または 'chrome')
firefox_path: FirefoxPortable/App/Firefox64/firefox.exe  # Firefox実行ファイルのパス
firefox_driver_path: drivers/geckodriver.exe  # GeckoDriverのパス（自動ダウンロード可能）
chrome_path: C:/Program Files/Google/Chrome/Application/chrome.exe  # Chrome実行ファイルのパス
chrome_driver_path: drivers/chromedriver.exe  # ChromeDriverのパス（自動ダウンロード可能）
profile_path: FirefoxPortable/Data/profile  # ブラウザプロファイルのパス（ログイン情報など）

#=====================================================================
# Amazon Photos設定
#=====================================================================
target_url: https://www.amazon.co.jp/photos/all?timeYear=1000&lcf=time  # 接続先URL
initial_wait: 5  # ページロード後の待機時間（秒）

#=====================================================================
# 写真処理設定
#=====================================================================
filename_pattern: 'VRChat_(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})'  # ファイル名から日時を抽出する正規表現パターン

#=====================================================================
# ログ設定
#=====================================================================
log_level_console: INFO  # コンソールに表示するログレベル (DEBUG/INFO/WARNING/ERROR/CRITICAL)
log_level_file: DEBUG  # ファイルに記録するログレベル

#=====================================================================
# 実行制御
#=====================================================================
max_iterations: 1000  # 処理サイクルの最大数（無限ループ防止）
```

| 項目名               | 説明 |
|---------------------|------|
| `browser_type`      | 使用するブラウザ（"firefox" または "chrome"） |
| `firefox_path`      | Firefox実行ファイルのパス |
| `firefox_driver_path` | GeckoDriverのパス（自動ダウンロードされます） |
| `chrome_path`       | Chrome実行ファイルのパス |
| `chrome_driver_path` | ChromeDriverのパス（自動ダウンロードされます） |
| `profile_path`      | ログイン済みのブラウザプロファイルフォルダ |
| `target_url`        | Amazon Photosの初期アクセスURL |
| `initial_wait`      | 初期ロード待機時間（秒） |
| `filename_pattern`  | ファイル名から日時を抽出する正規表現パターン |
| `log_level_console` | コンソールに表示するログレベル（"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"） |
| `log_level_file`    | ログファイルに記録するログレベル |
| `max_iterations`    | 処理サイクルの最大数（無限ループ防止） |

---
<br>

## 🔄 旧設定ファイル (config.json) からの移行

バージョン1.3.0より、設定ファイル形式がJSONからYAMLに変更されました。古いconfigファイルをお持ちの場合：

- アプリケーションは起動時に自動的に`config.json`を検出し、`config.yaml`に変換します
- 元のJSONファイルは`config.json.bak`としてバックアップされます
- 手動変換が必要な場合は、古いJSONファイルを削除し、アプリケーションを起動すると新しいYAMLファイルが自動生成されます

---
<br>

## 🌐 配布・再ビルドについて

- 本アプリは PyInstaller により `.exe` としてビルドされています
- `config.yaml`, ブラウザ, WebDriverは `.exe` に含まれないため、配布時には同梱または別途取得が必要です
- Firefox Portable の再配布はライセンス上禁止されているため、使用者が各自ダウンロードしてください

---
<br>

## 🧩 使用ライブラリ・外部ツール

| ライブラリ名 | 用途 |
|--------------|------|
| `requests`   | WebDriverの自動取得 |
| `tqdm`       | ダウンロード時の進捗表示 |
| `selenium`   | ブラウザ自動操作 |
| `PyYAML`     | 設定ファイル処理 |

インストール方法：

```bash
pip install requests tqdm selenium PyYAML
```
※ 仮想環境（venv等）を使っている場合は、先に有効化してから実行してください


また本アプリケーションは以下の外部ツールを利用しています：

- [GeckoDriver](https://github.com/mozilla/geckodriver)  
  Firefox を自動操作するための WebDriver
- [ChromeDriver](https://sites.google.com/chromium.org/driver/)  
  Chrome を自動操作するための WebDriver

初回起動時に、選択したブラウザに対応するWebDriverが自動ダウンロードされます。

---
<br>

## ⚠ 注意事項

- 本ツールは Amazon Photos の DOM構造・各ブラウザのWebDriver APIに依存しています
  Amazon Photos のDOM構造変更・WebDriver API変更などにより動作しなくなる可能性があります
- 初回実行時に SmartScreen 警告が表示されることがあります

---
<br>

## 📌 今後の予定

- 処理効率の改善（並列処理の検討）
- エラーハンドリングの強化

---
<br>

## 🙏 開発者・ライセンス

- 開発者: le ciel etoile [Twitter (X)](https://x.com/_le_ciel_etoile)
- ライセンス: MIT License
- 本ツールは非公式であり、Amazon社および VRChat社による承認を受けていません