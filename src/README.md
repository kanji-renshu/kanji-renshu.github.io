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
| `static/` | アイコン、manifest（そのまま公開フォルダにコピーされる） |
| `stub/` | 旧URLに置いている引っ越し案内ページ |
| `tools/` | `data/` を作り直すためのスクリプト（ふだんのビルドには不要） |

## データを作り直すとき（tools/）

`tools/` のスクリプトは、次の元データを `tools/upstream/`（または環境変数 `UPSTREAM` で指定した場所）に置いて使います。元データはリポジトリには入れていません。

- `svg/` … KanjiVG の SVG（`kanji/` フォルダ）
- `jamdict.db` … jamdict-data の JMdict データベース
- `grades.json`・`readings.json` … 学年別漢字配当表と常用漢字表の読み（cjkvi-tables・kanji-data から作ったもの）

`build_data.py` が `data/kanji_data.json` を作り直し、`check_tw.py` がテスト用のことばを確認します（ことばに対象の漢字が入っているか、まだ習っていない漢字がないか、読みが辞書と合っているか）。

## ライセンス

プログラム（`template.html.in`・`*.py`）は MIT、データ（`data/`・`tools/` の辞書由来のファイル・アイコン）は CC BY-SA です。くわしくはリポジトリ直下の `LICENSE` と `LICENSE-DATA.md` を見てください。
