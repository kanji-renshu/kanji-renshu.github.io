import os
HERE = os.path.dirname(os.path.abspath(__file__)) + '/'
UP = os.environ.get('UPSTREAM', HERE + 'upstream/')  # 元データの置き場所（src/README.md 参照）
import sqlite3, json, re, collections
c=sqlite3.connect(UP+'jamdict.db')
g=json.load(open(UP+'grades.json'))
kp=collections.defaultdict(list)
for kid,t in c.execute('select kid,text from KJP'): kp[kid].append(t)
np_=collections.defaultdict(list)
for kid,t in c.execute('select kid,text from KNP'): np_[kid].append(t)
knr=collections.defaultdict(list)
for kid,t in c.execute('select kid,text from KNR'): knr[kid].append(t)
kji=collections.defaultdict(list)
for kid,t in c.execute('select kid,text from KJI'): kji[kid].append(t)
kani=collections.defaultdict(list)
for kid,t in c.execute('select kid,text from KNI'): kani[kid].append(t)
kanas=collections.defaultdict(list)
for i,seq,t,nk in c.execute('select ID,idseq,text,nokanji from Kana'): kanas[seq].append((i,t,nk))
# misc tags per entry (archaic, rare, sensitive etc.)
bad=set()
for seq,t in c.execute('select s.idseq,m.text from misc m join Sense s on s.ID=m.sid'):
    pass
def score(tags):
    if not tags: return None
    s=100
    for t in tags:
        m=re.match(r'nf(\d+)',t)
        if m: s=min(s,int(m.group(1)))
    bonus=sum(1 for t in tags if t in('ichi1','news1','spec1'))
    if s==100: s=30 if bonus else 60
    return s-bonus*3
hira=re.compile(r'^[ぁ-ゟー]+$')
words=collections.defaultdict(list)
seen=collections.defaultdict(set)
for i,seq,t in c.execute('select ID,idseq,text from Kanji'):
    sc=score(kp.get(i))
    if sc is None: continue
    if any(x in ('iK','oK','rK','ateji','sK') for x in kji.get(i,[])): continue
    ks=[ch for ch in t if '一'<=ch<='鿿' or ch=='々']
    if not ks or any(ch!='々' and ch not in g for ch in ks): continue
    if any(not(('一'<=ch<='鿿') or ch=='々' or 'ぁ'<=ch<='ゟ') for ch in t): continue
    if len(t)>6: continue
    # reading
    rd=None
    for kid,kt,nk in kanas[seq]:
        if nk: continue
        if knr.get(kid) and t not in knr[kid]: continue
        if any(x in('ik','ok','sk') for x in kani.get(kid,[])):continue
        rd=kt;break
    if not rd or not hira.match(rd): continue
    mx=max(g[ch] for ch in ks if ch!='々')
    for ch in set(ks):
        if ch=='々' or (t,rd) in seen[ch]: continue
        seen[ch].add((t,rd))
        words[ch].append((sc,len(t),t,rd,mx))
out={}
for ch in g:
    L=sorted(words[ch],key=lambda x:(x[4]>g[ch],x[0],x[1]))
    out[ch]=[[w[2],w[3],w[4]] for w in L[:10]]
json.dump(out,open(HERE+'words.json','w'),ensure_ascii=False)
for ch in '一生見右校森学楽城茨鹿券':print(ch,g[ch],out[ch][:8])
print(sum(1 for v in out.values() if len(v)<3),[k for k,v in out.items() if len(v)<3][:40])
