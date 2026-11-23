# データのライセンス / Data licenses

`index.html` には、プログラムとは別に以下のデータが埋め込まれています。
プログラム部分（HTML/CSS/JavaScript）は `LICENSE`（MIT）に従い、データ部分は下記の各ライセンスに従います。

| データ | 出典 | ライセンス |
|---|---|---|
| 書き順（ストロークの形・順番・番号の位置） | [KanjiVG](https://kanjivg.tagaini.net/) © Ulrich Apel and contributors（取得時点の HEAD: `9d7220dfca09`） | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| 熟語の候補（漢字ページの「つかいかた」） | [JMdict](https://www.edrdg.org/jmdict/j_jmdict.html) © Electronic Dictionary Research and Development Group（jamdict-data 1.5 / JMdict 1.08 経由） | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| 音訓（読み） | 常用漢字表（2010）、[cjkvi-tables](https://github.com/cjkvi/cjkvi-tables)（取得時点の HEAD: `096c25525fcc`） | 常用漢字表は公的な告示。cjkvi-tables の利用条件に従います |
| 配当学年 | 学年別漢字配当表（2020年度施行）。[kanji-data](https://github.com/davidluzgouveia/kanji-data)（`00fd7079c389`）をもとに2020年度の移動分を反映 | — |
| 漢字の意味・テスト用のことば・意味・きせつイベントのことば・ことわざの解説 | 本プロジェクトで作成 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |

上記の CC BY-SA のデータを改変・再配布する場合は、出典の表示と、同じライセンス（継承）での配布が必要です。

## 商標について
「漢検」「漢字検定」は公益財団法人 日本漢字能力検定協会の登録商標です。本アプリは同協会とは関係ありません。級の表示は、漢字検定の10級〜5級を目安にしたものです。

## アプリのアイコン

`apple-touch-icon.png`・`icon-192.png`・`icon-512.png`・`icon.svg`、および `index.html` に埋め込んだ小さいアイコンは、本プロジェクトのオリジナル作品です。ただし中央の「字」は KanjiVG の筆画データ（CC BY-SA 3.0）を使って描いているため、アイコンも CC BY-SA 3.0 で配布します。

## 外部ライブラリ（QR コード）

`index.html` には次のライブラリを埋め込んでいます（`src/vendor/`）。

- qrcode-generator 2.0.4 — © 2009 Kazuhiko Arase — MIT License
- jsQR 1.4.0 — https://github.com/cozmo/jsQR — Apache License 2.0（全文は `src/vendor/LICENSE-jsqr`）

QR コードは株式会社デンソーウェーブの登録商標です。

## 4級〜1級のデータ（v3.0.0〜）

`pack-g7-*.json` 〜 `pack-g12-*.json`（もとは `src/data/pack-g7.json` 〜 `pack-g12.json`）は次から作っています。

- 書き順：KanjiVG（CC BY-SA 3.0、上記と同じ）
- 4級〜2級の字と読み：常用漢字表（2010年）と kanjium の学年情報
- 常用外の読み・旧字体の対応（kanjium 経由）：KANJIDIC — © Electronic Dictionary Research and Development Group — CC BY-SA 4.0 — https://www.edrdg.org/edrdg/licence.html
- 準1級・1級の字・読みの一部・旧字体と新字体の対応：kanjium — https://github.com/mifunetoshiro/kanjium — CC BY-SA 4.0。準1級・1級の級分けは kanjium にもとづく目安で、日本漢字能力検定協会が公表する一覧ではありません。JIS X 0208（第1・第2水準）にない字は除いています。
- 熟語とその読み：JMdict（CC BY-SA 4.0、上記と同じ）
- 日本語の「いみ」：本プロジェクトのオリジナル（`src/tools/meanings_ext/`、CC BY-SA 4.0）。旧字体は対応する新字体の「いみ」を使っています。

kanjium の作者の求めにより、次の表示を行います。
"The pitch accent notation, verb particle data, phonetics, homonyms and other additions or modifications to EDICT, KANJIDIC or KRADFILE were provided by Uros O. through his free database."

## 漢字検定との関係

本アプリは公益財団法人 日本漢字能力検定協会とは関係のない、非公式の学習アプリです。級の表示は目安で、検定の出題範囲・筆順・採点基準と同じであることは保証しません。
