import os
HERE = os.path.dirname(os.path.abspath(__file__)) + '/'
UP = os.environ.get('UPSTREAM', HERE + 'upstream/')  # 元データの置き場所（src/README.md 参照）
import json, re, glob, sqlite3, collections
import xml.etree.ElementTree as ET
D=UP; B=HERE
g=json.load(open(D+'grades.json'))
rd=json.load(open(D+'readings.json'))
mean={}
for i in range(1,7):
    for l in open(B+f'meanings{i}.txt'):
        l=l.rstrip('\n')
        if not l: continue
        k,m=l.split('\t'); mean[k]=m
miss=[k for k in g if k not in mean]; extra=[k for k in mean if k not in g]
assert not miss and not extra,(miss,extra)
# words (re-run with misc filter)
c=sqlite3.connect(D+'jamdict.db')
badseq=set(s for s, in c.execute("select distinct s.idseq from misc m join Sense s on s.ID=m.sid where m.text in ('vulg','X','derog','sens')"))
words=json.load(open(B+'words.json'))
ban={'馬鹿','馬鹿らしい','右四つ','左四つ'}
badtexts=set(t for t, in c.execute("select k.text from Kanji k where k.idseq in (%s)"%','.join(map(str,badseq)) )) if badseq else set()
pref={'茨':[['茨城県','いばらきけん']],'媛':[['愛媛県','えひめけん']],'岡':[['岡山県','おかやまけん'],['静岡県','しずおかけん'],['福岡県','ふくおかけん']],
'埼':[['埼玉県','さいたまけん']],'滋':[['滋賀県','しがけん']],'栃':[['栃木県','とちぎけん']],'奈':[['奈良県','ならけん'],['神奈川県','かながわけん']],
'梨':[['山梨県','やまなしけん']],'阜':[['岐阜県','ぎふけん']],'岐':[['岐阜県','ぎふけん']],'潟':[['新潟県','にいがたけん']],'崎':[['長崎県','ながさきけん'],['宮崎県','みやざきけん']],
'熊':[['熊本県','くまもとけん']],'鹿':[['鹿児島県','かごしまけん']],'児':[['鹿児島県','かごしまけん']],'沖':[['沖縄県','おきなわけん']],'縄':[['沖縄県','おきなわけん']],
'阪':[['大阪府','おおさかふ']],'香':[['香川県','かがわけん']],'佐':[['佐賀県','さがけん']],'賀':[['佐賀県','さがけん'],['滋賀県','しがけん']],'井':[['福井県','ふくいけん']],
'群':[['群馬県','ぐんまけん']],'徳':[['徳島県','とくしまけん']],'富':[['富山県','とやまけん']],'城':[['茨城県','いばらきけん'],['宮城県','みやぎけん']],
'愛':[['愛知県','あいちけん']],'静':[['静岡県','しずおかけん']],'森':[['青森県','あおもりけん']],
'央':[['中央','ちゅうおう']],'貝':[['貝','かい'],['貝がら','かいがら']],'机':[['机','つくえ']],'肺':[['肺','はい'],['肺活量','はいかつりょう']],
'貿':[['貿易','ぼうえき'],['貿易港','ぼうえきこう']],'昭':[['昭和','しょうわ']],'陛':[['天皇陛下','てんのうへいか'],['陛下','へいか']],'郡':[['郡','ぐん'],['郡部','ぐんぶ']]}
NS='{http://www.w3.org/2000/svg}'; KV='{https://kanjivg.tagaini.net/}'
def rnd(d):
    return re.sub(r'-?\d+\.\d+',lambda m:('%.1f'%float(m.group())).rstrip('0').rstrip('.'),d)
out=[]
for k in g:
    fn=D+'svg/%05x.svg'%ord(k)
    txt=open(fn,encoding='utf-8').read()
    txt=re.sub(r'<!DOCTYPE.*?\]>','',txt,flags=re.S)
    root=ET.fromstring(txt.encode())
    paths=[p for p in root.iter(NS+'path')]
    paths.sort(key=lambda p:int(p.get('id').split('-s')[-1]))
    strokes=[rnd(p.get('d')) for p in paths]
    nums=[]
    for t in root.iter(NS+'text'):
        m=re.search(r'matrix\(1 0 0 1 ([\d.]+) ([\d.]+)\)',t.get('transform'))
        nums.append([round(float(m.group(1)),1),round(float(m.group(2)),1)])
    # components: first-level groups of the kanji group
    kg=[e for e in root.iter(NS+'g') if e.get('id')=='kvg:%05x'%ord(k)][0]
    parts=[]
    for ch in kg:
        if ch.tag==NS+'g':
            el=ch.get(KV+'element') or ch.get(KV+'original')
            if el and el!=k: parts.append(el)
    rad=None
    for e in root.iter(NS+'g'):
        if e.get(KV+'radical') in('general','tradit') and e.get(KV+'element'):
            rad=e.get(KV+'element'); break
    on=[];kun=[]
    for r in rd[k].split('、'):
        special=r.startswith('（')
        r=r.strip('（）')
        if re.match(r'^[゠-ヿ]+$',r): on.append(r)
        else: kun.append(r)
    ws=pref.get(k,[])[:]
    for w,rdg,mx in words[k]:
        if w in ban or w in badtexts: continue
        if any(w==x[0] for x in ws): continue
        ws.append([w,rdg])
        if len(ws)>=6: break
    out.append({'k':k,'g':g[k],'s':strokes,'n':nums,'p':parts,'r':rad,'on':on,'kun':kun,'m':mean[k],'w':ws[:6]})
# order: by grade then reading
def key(o):
    first=(o['on']+o['kun'])[0].lstrip('*')
    import unicodedata
    kata=''.join(chr(ord(ch)-0x60) if 'ァ'<=ch<='ヶ' else ch for ch in first)
    return (o['g'],kata)
out.sort(key=key)
assert all(len(o['s'])==len(o['n']) for o in out)
s=json.dumps(out,ensure_ascii=False,separators=(',',':'))
open(HERE+'../data/kanji_data.json','w').write(s)
print(len(out),len(s)//1024,'KB')
for o in out[:2]+[x for x in out if x['k'] in '森茨鹿学']: print({kk:v for kk,v in o.items() if kk not in('s','n')})
print('no words:',[o['k'] for o in out if len(o['w'])<2])
