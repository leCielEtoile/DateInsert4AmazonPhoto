# DateInsert4AmazonPhoto

Amazon Photos にアップロードされた VRChat のスクリーンショット画像に対して、
**ファイル名から撮影日時を自動抽出し、Amazon Photos のメタデータとして反映する自動化ツール**です。

---
<br>

## ✨ 主な機能

- VRChat のファイル名 (例: `VRChat_<年>-<月>-<日>_<時>-<分>-00.000_xyz.png`) から日付と時刻を抽出
- Amazon Photos の写真詳細画面を自動操作
- 撮影日および時刻を入力・保存
- すでに設定済みの写真はスキップ
- 設定ファイル (`config.json`) により環境をカスタマイズ可能
- ログ出力 (`Editor.log`) による動作確認

---
<br>

## ⚡ 動作要件

- Windows 10 / 11
- Firefox（Portable版 または 通常インストール版）
- GeckoDriver（Firefox操作用）
- Python 3.12.9

---
<br>

## 🔹 使用方法

### 1. ForefoxPortableをダウンロードし構成ファイルに配置

- [PortableApps.com](https://portableapps.com/apps/internet/firefox_portable) より Firefox Portable をダウンロードしてください
- 任意のフォルダに解凍し、以下のような構成にしてください：

```
DateInsert4AmazonPhoto/
├── FirefoxPortable/           ← ポータブルFirefox一式
|   └── FirefoxPortable.exe    ← ログイン情報登録に使用
└── DateInsert4AmazonPhoto.exe
```

### 通常の Firefox を使用する場合

- `DateInsert4AmazonPhoto.exe` を起動すると `config.json` が自動生成されます
- 以下のようにパスを編集してください：

```json
{
  "firefox_path": "インストールされている場所(デフォルトでは C:/Program Files/Mozilla Firefox/firefox.exe)",
  "profile_path": "プロファイルが保存されている場所(デフォルトでは %APPDATA%/Mozilla/Firefox/Profiles )",
}
```

- 以下のファイル構成になっていれば成功です。

```
DateInsert4AmazonPhoto/
├── config.json                ← 設定ファイル
├── Editor.log                 ← logファイル(DateInsert4AmazonPhoto.exeを実行する際自動生成)
└── DateInsert4AmazonPhoto.exe
```

### 2. Amazon Photos にログイン

- `FirefoxPortable/FirefoxPortable.exe` を起動し、
  [Amazon Photos](https://www.amazon.co.jp/photos/) にアクセスしてログインしてください
- ログイン情報はプロファイルに保存され、以後の自動操作で利用されます

---

### 3. アプリを起動

- `DateInsert4AmazonPhoto.exe` を実行すると、未設定の画像に対して撮影日時が順次入力されます
- 進捗ログはコンソールと `Editor.log` に出力されます

---
<br>

## 🔧 config.json の設定項目

```json
{
  "firefox_path": "FirefoxPortable/App/Firefox64/firefox.exe",
  "geckodriver_path": "geckodriver.exe",
  "profile_path": "FirefoxPortable/Data/profile",
  "target_url": "https://www.amazon.co.jp/photos/all?timeYear=1000&lcf=time",
  "initial_wait": 5
}
```

| 項目名             | 説明 |
|-------------------|------|
| `firefox_path`    | Firefox実行ファイルのパス |
| `geckodriver_path`| GeckoDriverのパス（自動ダウンロードされます） |
| `profile_path`    | ログイン済みのFirefoxプロファイルフォルダ |
| `target_url`      | Amazon Photosの初期アクセスURL |
| `initial_wait`    | 初期ロード待機時間（秒） |

---
<br>

## 🌐 配布・再ビルドについて

- 本アプリは PyInstaller により `.exe` としてビルドされています
- `config.json`, `geckodriver.exe`, `FirefoxPortable/` は `.exe` に含まれないため、配布時には同梱または別途取得が必要です
- Firefox Portable の再配布はライセンス上禁止されているため、使用者が各自ダウンロードしてください

---
<br>

## 🧩 使用ライブラリ・外部ツール

| ライブラリ名 | 用途 |
|--------------|------|
| `requests`   | GeckoDriverの自動取得 |
| `tqdm`       | ダウンロード時の進捗表示 |
| `selenium`   | Firefoxのブラウザ自動操作 |

インストール方法：

```bash
pip install requests tqdm selenium
```
※ 仮想環境（venv等）を使っている場合は、先に有効化してから実行してください


また本アプリケーションは以下の外部ツールを利用しています：

- [GeckoDriver](https://github.com/mozilla/geckodriver)  
  Firefox を自動操作するための WebDriver。初回起動時に最新版が自動ダウンロードされます

---
<br>

## ⚠ 注意事項

- 本ツールは Amazon Photos の DOM構造・作成時点でのgeckodriver・Firefoxに依存しています
  Amazon Photos のDOM構造変更・Firefox API変更などにより動作しなくなる可能性があります
- 初回実行時に SmartScreen 警告が表示されることがあります

---
<br>

## 📌 今後の予定

- 導入手順の簡略化（GeckoDriverやFirefox自動取得のさらなる統合）
- 設定GUIの追加検討

---
<br>

## 🙏 開発者・ライセンス

- 開発者: le ciel etoile [Twitter (X)](https://x.com/_le_ciel_etoile)
- ライセンス: MIT License
- 本ツールは非公式であり、Amazon社および VRChat社による承認を受けていません
