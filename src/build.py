#!/usr/bin/env python3
"""かんじ れんしゅう ビルドスクリプト

src/ のテンプレートとデータから、公開用の index.html と version.json を作ります。

  python3 src/build.py                       # リポジトリ直下に index.html / version.json / アイコン類を出力
  python3 src/build.py --build "2026-11-23 12:00"   # ビルド日時を固定（公開版と同じものを再現する）
  python3 src/build.py --out /tmp/site       # 出力先を変える
"""
import argparse, base64, datetime, hashlib, json, os, re, shutil

SRC = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--out', default=os.path.dirname(SRC))
ap.add_argument('--build', help='ビルド日時 "YYYY-MM-DD HH:MM"（JST）。省略時は現在時刻')
a = ap.parse_args()

v = json.load(open(os.path.join(SRC, 'version.json'), encoding='utf-8'))
t = open(os.path.join(SRC, 'template.html.in'), encoding='utf-8').read()
if a.build:
    assert re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', a.build), a.build
    build = a.build
else:
    jst = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)
    build = jst.strftime('%Y-%m-%d %H:%M')

kd = json.load(open(os.path.join(SRC, 'data', 'kanji_data.json'), encoding='utf-8'))
tw = {}
for g in range(1, 7):
    for line in open(os.path.join(SRC, 'data', f'tw{g}.txt'), encoding='utf-8'):
        p = line.rstrip('\n').split('\t')
        if len(p) == 4:
            tw[p[0]] = p[1:]
for o in kd:
    if o['k'] in tw:
        o['t'] = tw[o['k']]
data = json.dumps(kd, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
events = json.dumps(json.load(open(os.path.join(SRC, 'data', 'events.json'), encoding='utf-8')), ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

# データに HTML として解釈される文字が入っていないことを確かめる（アプリは一部を innerHTML で表示するため）
def _strings(x):
    if isinstance(x, str): yield x
    elif isinstance(x, dict):
        for k, v2 in x.items(): yield k; yield from _strings(v2)
    elif isinstance(x, list):
        for v2 in x: yield from _strings(v2)
_bad = [s for s in list(_strings(kd)) + list(_strings(json.loads(events))) + list(_strings(v['changelog'])) if re.search(r'[<>&"\u2028\u2029]', s)]
assert not _bad, ('HTML 文字を含むデータ', _bad[:5])

# QR コードの部品（src/vendor/。ライセンスは同じフォルダの LICENSE-*）を、アプリと同じ1つのスクリプトに埋め込む
def _vendor(name, var):
    code = open(os.path.join(SRC, 'vendor', name), encoding='utf-8').read().replace('</', '<\\/')
    return f'const {var} = (function(){{ var module = {{exports:{{}}}}, exports = module.exports, define; {code}\n; return module.exports; }})();\n'
vendor = _vendor('qrcode-generator-2.0.4.min.js', 'QRGEN') + _vendor('jsqr-1.4.0.min.js', 'QRSCAN')
assert t.count('/*__VENDOR__*/') == 1
t = t.replace('/*__VENDOR__*/', vendor)

out = (t.replace('__VERSION__', v['version']).replace('__BUILD__', build)
        .replace('__CHANGELOG__', json.dumps(v['changelog'], ensure_ascii=False).replace('</', '<\\/'))
        .replace('__EVENTS__', events).replace('__DATA__', data))

# CSP: インラインスクリプトは1つだけ。その sha256 を CSP に入れる
m = list(re.finditer(r'<script>(.*?)</script>', out, re.S))
assert len(m) == 1, len(m)
out = out.replace('__CSP_HASH__', 'sha256-' + base64.b64encode(hashlib.sha256(m[0].group(1).encode('utf-8')).digest()).decode())
assert not re.search(r'__(VERSION|BUILD|CSP_HASH|DATA|EVENTS|CHANGELOG)__', out)

os.makedirs(a.out, exist_ok=True)
open(os.path.join(a.out, 'index.html'), 'w', encoding='utf-8').write(out)
json.dump({'version': v['version'], 'build': build}, open(os.path.join(a.out, 'version.json'), 'w', encoding='utf-8'), ensure_ascii=False)
for f in os.listdir(os.path.join(SRC, 'static')):
    shutil.copy(os.path.join(SRC, 'static', f), os.path.join(a.out, f))
print(v['version'], build, hashlib.sha256(out.encode('utf-8')).hexdigest()[:16])
