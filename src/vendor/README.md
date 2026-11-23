# vendor（外部の部品）

アプリに埋め込んでいる外部ライブラリです。`build.py` がアプリのスクリプトに埋め込みます。中身は npm の公開パッケージを terser で圧縮したもので、改変はしていません。

| ファイル | 元 | ライセンス |
|---|---|---|
| `qrcode-generator-2.0.4.min.js` | npm `qrcode-generator` 2.0.4（`dist/qrcode.js`）・https://github.com/kazuhikoarase/qrcode-generator | MIT（`LICENSE-qrcode-generator`） |
| `jsqr-1.4.0.min.js` | npm `jsqr` 1.4.0（`dist/jsQR.js`）・https://github.com/cozmo/jsQR | Apache-2.0（`LICENSE-jsqr`） |

更新するときは、元の版を確かめ、`eval` や外部への通信が入っていないことを確認してから差し替えます。QR コードは株式会社デンソーウェーブの登録商標です。
