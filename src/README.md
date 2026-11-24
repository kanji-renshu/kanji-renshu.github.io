# ソースとビルド

公開している `index.html` は、このフォルダのテンプレートとデータから `build.py` で作っています。外部への通信やライブラリは使っていません（Python 3 の標準ライブラリだけでビルドできます）。

```
python3 src/build.py                                  # リポジトリ直下に index.html・version.json・アイコン類を出力
python3 src/build.py --out /tmp/site --build "2026-11-23 12:00"
```

`--build` に公開中の `version.json` の `build` の値を渡すと、公開中の `index.html` と**バイト単位で同じもの**ができます（ビルド日時がスクリプトの中に入り、CSP のハッシュも変わるため）。配信されているファイルがこのソースから作られたものかを、誰でも確かめられます。

```
python3 src/build.py --out /tmp/check --build "$(python3 -c "import json;print(json.load(open('version.json'))['build'])")"
cmp /tmp/check/index.html index.html && echo 同じです
```

## ファイル

| パス | 内容 |
|---|---|
| `template.html.in` | アプリ本体（HTML・CSS・JavaScript）。`__DATA__` などの置き換え用の印が入っている |
| `version.json` | 版番号と更新履歴（アプリ内の「これまでの こうしん」に出る） |
| `data/kanji_data.json` | 1026字の書き順（KanjiVG）・読み・意味・熟語 |
| `data/tw1.txt`〜`tw6.txt` | かきとりテストで出すことば（学年ごと。`字<TAB>ことば<TAB>よみ<TAB>いみ`） |
| `data/events.json` | 月ごとのイベント（ことば・ことわざ・ごほうび） |
| `data/pack-g7.json`〜`pack-g12.json` | 4級〜1級の級別データ。ビルドで `pack-g<級>-<ハッシュ>.json` として公開し、本体に埋め込んだ SHA-256 と照合してから読み込む |
| `static/` | アイコン、manifest（そのまま公開フォルダにコピーされる） |
| `stub/` | 旧URLに置いている引っ越し案内ページ |
| `tests/` | セキュリティの回帰テスト |
| `vendor/` | 埋め込んでいる QR コードの部品（ライセンスは同じフォルダ） |
| `tools/` | `data/` を作り直すためのスクリプト（ふだんのビルドには不要） |

## セキュリティのテスト（tests/）

`tests/security.test.cjs` は、ソースからビルドしたページに攻撃用のデータを流し込み、次のことを確かめます。機能を足したら、公開の前に実行してください。

- 保存データ（localStorage）や引き継ぎコードに HTML・スクリプトを仕込んでも、画面に差し込まれず、スクリプトも動かない
- `__proto__` などでプログラムの中身を汚されない
- 壊れたデータ・大きすぎるデータ・展開すると巨大になる圧縮データを断る
- `#import=` 付きのリンクでは記録を取り込まない
- ともだちカードの署名を偽造・流用したもの、ありえない数字のものはランキングに入れない。別の鍵でのなりすましは警告する
- バックアップ（KKR2）は書き換えると読み込まない。古い形式（KKR1・KKZ1・JSON）は 2027-03-31 まで読み込むが、ともだちカードの情報は受け取らない
- 練習回数は、速すぎるものと、同じ字を1日に4回以上書いたものは数えない
- ともだちカード（QR）に HTML や大きすぎる値・未来の週・自分のカードなどを仕込んでも、断るか型どおりに直す。友だちは30人まで
- 正しい記録は、読み込み直しても失われない
- 「かんじを さがす」の入力欄に HTML・スクリプトを入れても文字として扱い、長すぎる入力は切り詰める。変な手書きの線でも壊れない
- ほかのサイトの iframe に埋め込まれると（sandbox 付きを含む）アプリを表示せず、記録も書かない
- `.well-known/security.txt` に連絡先があり、`Expires` が 30 日以上先・1 年以内である（期限が近づくとテストが失敗するので、そのときに日付を更新する）

```
npm install playwright-core
CHROME=/usr/bin/google-chrome node src/tests/security.test.cjs
```

Chrome（または Chromium）と Node.js、Python 3 が必要です。失敗があると終了コード 1 で終わります。新しい保存項目や取り込み機能を足したときは、このテストにもその項目への攻撃を足してください。

## データを作り直すとき（tools/）

`tools/` のスクリプトは、次の元データを `tools/upstream/`（または環境変数 `UPSTREAM` で指定した場所）に置いて使います。元データはリポジトリには入れていません。

- `svg/` … KanjiVG の SVG（`kanji/` フォルダ）
- `jamdict.db` … jamdict-data の JMdict データベース
- `grades.json`・`readings.json` … 学年別漢字配当表と常用漢字表の読み（cjkvi-tables・kanji-data から作ったもの）

`build_ext.py` が4級〜1級の `data/pack-g7.json`〜`pack-g12.json` を作ります（`kanjidb.sqlite`：kanjium、`joyo2010.txt`：常用漢字表も使用。日本語の「いみ」は `tools/meanings_ext/`）。`build_data.py` が `data/kanji_data.json` を作り直し、`check_tw.py` がテスト用のことばを確認します（ことばに対象の漢字が入っているか、まだ習っていない漢字がないか、読みが辞書と合っているか）。

## ライセンス

プログラム（`template.html.in`・`*.py`）は MIT、データ（`data/`・`tools/` の辞書由来のファイル・アイコン）は CC BY-SA です。くわしくはリポジトリ直下の `LICENSE` と `LICENSE-DATA.md` を見てください。

## 脆弱性の報告窓口（static/.well-known/security.txt）

連絡先は GitHub の非公開の脆弱性報告（Private vulnerability reporting）です。リポジトリの Settings → Advanced Security で有効にしておく必要があります。`Expires` は 1 年以内の日付にし、テストが期限切れ間近を知らせたら更新します。

GitHub Pages ではレスポンスヘッダー（`frame-ancestors`、`X-Frame-Options`、`X-Content-Type-Options`、`Permissions-Policy`）を付けられません。埋め込み対策は `framedGuard()`（上のテストで確認）で代わりに行い、ホスティングを変えるときにヘッダーへ移します。
