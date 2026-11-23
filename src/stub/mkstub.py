#!/usr/bin/env python3
"""旧URL（jyz002xyz.github.io/kanji-renshu/）に置く引っ越し案内ページを作る。
  python3 src/stub/mkstub.py https://kanji-renshu.github.io/ OUTDIR 2.4.0
"""
import base64, hashlib, json, os, re, sys
new, out, ver = sys.argv[1], sys.argv[2], sys.argv[3]
here = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(here, 'stub.html.in'), encoding='utf-8').read().replace('__NEW__', new)
s = re.search(r'<script>(.*?)</script>', t, re.S).group(1)
t = t.replace("'__HASH__'", "'sha256-" + base64.b64encode(hashlib.sha256(s.encode()).digest()).decode() + "'").replace(' navigate-to https:', '')
os.makedirs(out, exist_ok=True)
open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(t)
json.dump({'version': ver, 'changelog': [[ver, '', 'あたらしい ページに おひっこし しました。']]}, open(os.path.join(out, 'version.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('stub ok')
