
# DateInsert4AmazonPhoto

Amazon Photos 上でアップロードされた VRChat のスクリーンショット画像に対して、
ファイル名から撮影日と時刻を自動抽出し、Amazon Photos のメタデータとして反映させる自動化アプリケーションです。

---

## ✨ 主な機能

- VRChat のファイル名 (例: `VRChat_<年>-<月>-<日>_<時>-<分>-00.000_xyz.png`) から日付と時刻を抽出
- Amazon Photos の写真詳細画面を自動操作
- 撮影日および時刻を入力・保存
- すでに設定済みの写真はスキップ
- 設定ファイル (`config.json`) により環境をカスタマイズ可能
- ログ出力 (`Editor.log`) による動作確認

---

## ⚡ 動作要件

- Windows 10 / 11
- Firefox Portable（64bit）
- GeckoDriver（Firefox操作用）
- Python 3.12.9

---

## 🔹 使用方法

### 1. ForefoxPortable・geckodriverをダウンロードし構成ファイルに配置

- [PortableApp](https://portableapps.com/apps/internet/firefox_portable)のサイトにアクセスしFirefoxPortableをダウンロードしてください。
- 続いて[geckodriver](https://github.com/mozilla/geckodriver/releases)をダウンロードしてください
- ファイル内に配置しインストールしてください。
- 最終的に以下のファイル構成になっていれば成功です。

```
DateInsert4AmazonPhoto/
├── FirefoxPortable/           ← ポータブルFirefox一式
|   └── FirefoxPortable.exe    ← ログイン情報登録に使用
├── config.json                ← 設定ファイル
├── geckodriver.exe            ← Firefox制御ドライバ
└── DateInsert4AmazonPhoto.exe
```

### 2. AmazonPhotoにログイン

- `DateInsert4AmazonPhoto\FirefoxPortable\FirefoxPortable.exe` をダブルクリックして起動します
- [Amazon Photo](https://www.amazon.co.jp/photos/)にアクセスしログインします
- これによりプロファイル情報にAmazonPhotoのログイン情報が登録されます

### 4. アプリを起動

- `DateInsert4AmazonPhoto.exe` をダブルクリックして起動します
- 処理が進行し、コンソールと `Editor.log` にログが出力されます

---

### 🔧 `config.json` の設定項目

```json
{
  "firefox_path": "FirefoxPortable/App/Firefox64/firefox.exe",
  "geckodriver_path": "geckodriver.exe",
  "profile_path": "FirefoxPortable/Data/profile",
  "target_url": "https://www.amazon.co.jp/photos/all?timeYear=1000&lcf=time",
  "initial_wait": 5
}
```

- `firefox_path`: ポータブルFirefoxの実行ファイルパス
- `geckodriver_path`: GeckoDriverのパス
- `profile_path`: ログイン済みのFirefoxプロファイルパス
- `target_url`: Amazon Photos 一覧ページのURL
- `initial_wait`: 一覧ページの読み込み待機時間（秒）

## 🌐 配布・再ビルドについて

- 本アプリは `pyinstaller` によりビルドされています
- `config.json`, `geckodriver.exe`, `FirefoxPortable/` は `.exe` に内包していないため、
  配布時は同梱するかユーザーが任意に配置してください(Firefoxは原則再配布禁止の為注意すること)

---

## ⚠ 注意事項

- 本ツールは Amazon Photos の DOM構造・作成時点でのgeckodriver・Firefoxに依存しています。
  DOM構造またはFirefoxのapi等が変更された場合、動作しない可能性があります。
- 自己署名証明書等で署名された `.exe` を使用している場合、
  初回実行時に SmartScreen 警告が表示されることがあります。

---

## 将来

- 導入の簡易化　追加でダウンロードするものも多く導入手順が煩雑なのでLicenseの許す限り自動化ができないか検討中

---

## 🙏 作者・ライセンス

- 開発者: le ciel etoile : [Twitter(X)](https://x.com/_le_ciel_etoile)
- ライセンス: MIT
- このツールは非公式であり、Amazon または VRChat による承認を受けていません。
