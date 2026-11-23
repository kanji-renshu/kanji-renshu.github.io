#!/usr/bin/env python3
"""4級〜1級（g7〜g12）の級別データを作る。

  UPSTREAM=<元データ> python3 src/tools/build_ext.py

元データ（UPSTREAM）に置くもの：
  svg/            KanjiVG の kanji/ フォルダ（全字）
  joyo2010.txt    常用漢字表（字・旧字・画数・学年・追加年・読み）
  kanjidb.sqlite  kanjium（漢検の級の目安・常用外の読み・英語の意味）
  jamdict.db      JMdict（熟語とその読み）

出力：src/data/pack-g7.json 〜 pack-g12.json と src/data/packs.json（字の一覧）。
日本語の「いみ」は src/tools/meanings_ext/g<級>.txt（字<TAB>いみ）から入れる。
"""
import collections, json, os, re, sqlite3, sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__)) + '/'
UP = os.environ.get('UPSTREAM', HERE + 'upstream/')
SVG = os.environ.get('KANJIVG', UP + 'svg/')
OUT = HERE + '../data/'
NS = '{http://www.w3.org/2000/svg}'; KV = '{https://kanjivg.tagaini.net/}'
LV = {7: '4', 8: '3', 9: '準2', 10: '2', 11: '準1', 12: '1'}

base = json.load(open(OUT + 'kanji_data.json', encoding='utf-8'))
KG = {o['k']: o['g'] for o in base}

# --- 級の割りあて ---
joyo = {}
for line in open(UP + 'joyo2010.txt', encoding='utf-8'):
    if line.startswith('#') or not line.strip(): continue
    p = line.rstrip('\n').split('\t')
    joyo[p[0]] = p[5]
km = sqlite3.connect(UP + 'kanjidb.sqlite')
kmd = {r[0]: r[1:] for r in km.execute('select kanji, kanken, grade, onyomi, kunyomi, meaning from kanjidict')}
JHS = {'Jōyō (1st grade of junior high school)': 7, 'Jōyō (2nd grade of junior high school)': 8, 'Jōyō (3rd grade of junior high school)': 9, 'Jōyō (high school)': 10}
has_svg = lambda k: os.path.exists(SVG + '%05x.svg' % ord(k))
lv = {}
for k in joyo:
    if k in KG: continue
    gr = kmd.get(k, (None, ''))[1]
    assert gr in JHS, (k, gr)
    lv[k] = JHS[gr]
def jis0208(k):  # 漢検1級の対象は JIS 第1・第2水準（JIS X 0208）。それ以外は端末に字形がないことがある
    try: k.encode('shift_jis'); return True
    except UnicodeEncodeError: return False
for k, (ken, gr, *_ ) in kmd.items():
    if k in KG or k in lv or not has_svg(k) or not jis0208(k): continue
    if ken == 'pre-1': lv[k] = 11
    elif ken == '1': lv[k] = 12
for k, g in lv.items(): KG[k] = g
cnt = collections.Counter(lv.values()); print('級ごとの字数', {LV[g]: cnt[g] for g in sorted(cnt)})
assert [cnt[g] for g in (7, 8, 9, 10)] == [313, 284, 328, 185], cnt

# --- 読み ---
def joyo_readings(s):
    on, kun = [], []
    for r in s.split('、'):
        r = r.strip().strip('（）')
        if not r: continue
        (on if re.fullmatch(r'[゠-ヿ]+', r) else kun).append(r)
    return on, kun
def km_readings(ons, kuns):
    on = [re.sub(r'\(.*?\)', '', x).strip() for x in re.split('[、,]', ons or '')]
    on = [x for x in on if re.fullmatch(r'[゠-ヿ]+', x)]
    kun = []
    for x in re.split('[、,]', kuns or ''):
        x = x.strip().replace('（', '-').replace('）', '').replace('(', '-').replace(')', '')
        x = x.strip('-')
        if re.fullmatch(r'[ぁ-ゖー]+(-[ぁ-ゖー]+)?', x): kun.append(x)
    dedup = lambda l: list(dict.fromkeys(l))
    return dedup(on)[:5], dedup(kun)[:6]

# --- 熟語（JMdict） ---
jd = sqlite3.connect(UP + 'jamdict.db')
bad_seq = set(s for s, in jd.execute("select distinct s.idseq from misc m join Sense s on s.ID=m.sid where m.text in ('vulg','X','derog','sens')"))
kpri = collections.defaultdict(list)
for kid, t in jd.execute('select kid, text from KJP'): kpri[kid].append(t)
kirr = set(kid for kid, t in jd.execute('select kid, text from KJI'))
knr = collections.defaultdict(set)
for kid, t in jd.execute('select kid, text from KNR'): knr[kid].add(t)
kanas = collections.defaultdict(list)
for i, seq, t, nk in jd.execute('select ID, idseq, text, nokanji from Kana order by ID'): kanas[seq].append((i, t, nk))
def score(tags):
    s = 100
    for t in tags:
        mm = re.match(r'nf(\d+)', t)
        if mm: s = min(s, int(mm.group(1)))
    if s == 100: s = 30 if any(t in ('ichi1', 'news1', 'spec1', 'gai1') for t in tags) else (55 if tags else 70)
    return s
jukugo = set(r[0] for r in km.execute('select jukugo from jukugo'))
cand = collections.defaultdict(list)
for kid, seq, text in jd.execute('select ID, idseq, text from Kanji'):
    if seq in bad_seq or kid in kirr or len(text) > 6: continue
    rd = next((t for i, t, nk in kanas[seq] if not nk and (not knr.get(i) or text in knr[i])), None)
    if not rd: continue
    sc = score(kpri.get(kid, [])) - (8 if text in jukugo else 0)
    for ch in set(text):
        if ch in lv: cand[ch].append((sc, len(text), text, rd))

def words_for(k):
    g = lv[k]; seen = set(); ok, other = [], []
    for sc, ln, w, rd in sorted(cand[k]):
        if w in seen or ln < 1: continue
        seen.add(w)
        fine = all(KG.get(c, 99) <= g or not ('一' <= c <= '鿿') for c in w)
        (ok if fine else other).append([w, rd])
    return (ok + other)[:6]
def test_word(k, ws):
    g = lv[k]
    for w, rd in ws:
        if len(w) >= 2 and all(KG.get(c, 99) <= g or not ('一' <= c <= '鿿') for c in w) and re.fullmatch(r'[ぁ-ゖー]+', rd): return [w, rd, '']
    return None

# --- 書き順（KanjiVG） ---
def rnd(d): return re.sub(r'-?\d+\.\d+', lambda mm: ('%.1f' % float(mm.group())).rstrip('0').rstrip('.'), d)
def strokes(k):
    txt = re.sub(r'<!DOCTYPE.*?\]>', '', open(SVG + '%05x.svg' % ord(k), encoding='utf-8').read(), flags=re.S)
    root = ET.fromstring(txt.encode())
    paths = sorted(root.iter(NS + 'path'), key=lambda p: int(p.get('id').split('-s')[-1]))
    nums = []
    for t in root.iter(NS + 'text'):
        mm = re.search(r'matrix\(1 0 0 1 ([\d.-]+) ([\d.-]+)\)', t.get('transform'))
        nums.append([round(float(mm.group(1)), 1), round(float(mm.group(2)), 1)])
    kg = [e for e in root.iter(NS + 'g') if e.get('id') == 'kvg:%05x' % ord(k)][0]
    parts = [ch.get(KV + 'element') or ch.get(KV + 'original') for ch in kg if ch.tag == NS + 'g']
    parts = [p for p in parts if p and p != k]
    rad = None
    for e in root.iter(NS + 'g'):
        if e.get(KV + 'radical') in ('general', 'tradit') and e.get(KV + 'element'): rad = e.get(KV + 'element'); break
    return [rnd(p.get('d')) for p in paths], nums, parts, rad

def meanings(g):
    f = HERE + f'meanings_ext/g{g}.txt'; m = {}
    if os.path.exists(f):
        for line in open(f, encoding='utf-8'):
            line = line.rstrip('\n')
            if '\t' in line: k, v = line.split('\t', 1); m[k] = v.strip()
    return m

# 旧字体：対応する新字体の いみ を使う（kanjium の variants 表）
SHIN = {r[0]: r[1] for r in km.execute("select kanji, shinjitai from variants where shinjitai is not null and shinjitai != ''")}
ALLMEAN = {o['k']: o['m'] for o in base}
for _g in range(7, 13): ALLMEAN.update(meanings(_g))
def meaning_of(k, mean):
    if mean.get(k): return mean[k]
    nk = SHIN.get(k)
    if nk and ALLMEAN.get(nk): return f'「{nk}」の旧字体。' + ALLMEAN[nk]
    return ''

index = {}
for g in range(7, 13):
    mean = meanings(g); out = []
    for k in [k for k in lv if lv[k] == g]:
        s, n, p, r = strokes(k)
        if len(s) != len(n): n = n[:len(s)] + [[0, 0]] * (len(s) - len(n))
        on, kun = joyo_readings(joyo[k]) if k in joyo else km_readings(kmd[k][2], kmd[k][3])
        if not on and not kun: continue
        ws = words_for(k); o = {'k': k, 'g': g, 's': s, 'n': n, 'p': p, 'r': r, 'on': on, 'kun': kun, 'm': meaning_of(k, mean), 'w': ws}
        t = test_word(k, ws)
        if t: o['t'] = t
        out.append(o)
    def key(o):
        first = (o['on'] + o['kun'])[0]
        return ''.join(chr(ord(ch) - 0x60) if 'ァ' <= ch <= 'ヶ' else ch for ch in first)
    out.sort(key=key)
    s = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
    open(OUT + f'pack-g{g}.json', 'w', encoding='utf-8').write(s)
    index[g] = ''.join(o['k'] for o in out)
    print(f'{LV[g]}級 g{g}: {len(out)}字 {len(s)//1024}KB いみあり {sum(1 for o in out if o["m"])} テスト語あり {sum(1 for o in out if "t" in o)} 熟語0 {sum(1 for o in out if not o["w"])}')
json.dump({str(g): index[g] for g in index}, open(OUT + 'packs.json', 'w', encoding='utf-8'), ensure_ascii=False)
