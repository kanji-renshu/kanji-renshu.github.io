import os
HERE = os.path.dirname(os.path.abspath(__file__)) + '/'
UP = os.environ.get('UPSTREAM', HERE + 'upstream/')  # 元データの置き場所（src/README.md 参照）
import json, sqlite3, sys, re, collections
d=json.load(open(HERE+'../data/kanji_data.json')); g={o['k']:o['g'] for o in d}
c=sqlite3.connect(UP+'jamdict.db')
rd=collections.defaultdict(set)
for t,r in c.execute("select k.text, n.text from Kanji k join Kana n on n.idseq=k.idseq"): rd[t].add(r)
grades=[int(x) for x in sys.argv[1:]]
bad=0
for gr in grades:
    seen=set()
    for i,l in enumerate(open(HERE+f'../data/tw{gr}.txt'),1):
        l=l.rstrip('\n')
        if not l: continue
        p=l.split('\t')
        if len(p)!=4: print(gr,i,'FORMAT',l); bad+=1; continue
        k,w,r,m=p; seen.add(k)
        if g.get(k)!=gr: print(gr,i,'GRADE/UNKNOWN',k); bad+=1
        if k not in w: print(gr,i,'NOT IN WORD',k,w); bad+=1
        hi=[ch for ch in w if '一'<=ch<='鿿' and ch!=k and g.get(ch,9)>gr]
        if hi: print(gr,i,'HIGHER KANJI',k,w,hi)
        if not re.fullmatch(r'[ぁ-ゟ゠-ヿ]+',r): print(gr,i,'READING NOT HIRAGANA',r); bad+=1
        if re.search(r'[一-鿿]',m): print(gr,i,'KANJI IN MEANING',k,m); bad+=1
        if w in rd and r not in rd[w]: print(gr,i,'READING MISMATCH',w,r,sorted(rd[w])[:4])
        if w not in rd: print(gr,i,'(not in dict)',w,r)
    miss=[k for k in g if g[k]==gr and k not in seen]
    if miss: print(gr,'MISSING',''.join(miss)); bad+=1
print('errors',bad)
