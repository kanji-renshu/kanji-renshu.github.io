#!/usr/bin/env node
/* かんじ れんしゅう セキュリティ回帰テスト
 *
 * ソースからビルドしたページをローカルで配信し、攻撃用のデータを流し込んで
 * 「画面に差し込まれない・スクリプトが動かない・正しい記録が失われない」ことを確かめます。
 *
 *   npm install playwright-core          # 1回だけ（ブラウザ本体はダウンロードしない）
 *   CHROME=/usr/bin/google-chrome node src/tests/security.test.cjs
 *
 * 失敗があれば終了コード 1 で終わります。
 */
const { execFileSync } = require('child_process');
const fs = require('fs'), http = require('http'), os = require('os'), path = require('path');
const { chromium } = require('playwright-core');

const SRC = path.resolve(__dirname, '..');
const OUT = fs.mkdtempSync(path.join(os.tmpdir(), 'kkr-test-'));
const CHROME = process.env.CHROME || ['/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'].find(p => fs.existsSync(p));
// スクリプトと外部リンクを仕込んだ文字列。どの項目に入れても、画面に出てはいけない
const X = '"><img src=x onerror="window.__xss=1"><a id="pwn" href="https://evil.example/">x</a><script>window.__xss=2</script>';
const SVGX = '#ff0000"/><a id="pwn1" href="https://evil.example/"><text>x</text></a><image href="https://evil.example/x.png" onerror="window.__xss=1"/><path d="';

let failed = 0;
const check = (name, ok, detail) => { console.log((ok ? '  ok   ' : '  FAIL ') + name + (ok ? '' : '  ' + JSON.stringify(detail))); if (!ok) failed++; };

(async () => {
  execFileSync('python3', [path.join(SRC, 'build.py'), '--out', OUT], {stdio:'ignore'});
  const types = {'.html':'text/html; charset=utf-8', '.json':'application/json', '.png':'image/png', '.svg':'image/svg+xml', '.webmanifest':'application/manifest+json'};
  const server = http.createServer((q, r) => { const f = path.join(OUT, path.basename(q.url.split(/[?#]/)[0]) || 'index.html');
    fs.readFile(f, (e, d) => { if (e){ r.writeHead(404); r.end(); } else { r.writeHead(200, {'content-type': types[path.extname(f)] || 'application/octet-stream'}); r.end(d); } }); });
  await new Promise(ok => server.listen(0, '127.0.0.1', ok));
  const URL0 = `http://127.0.0.1:${server.address().port}/`;
  const browser = await chromium.launch({executablePath: CHROME, args:['--no-sandbox']});

  const open = async () => { const p = await (await browser.newContext({viewport:{width:820, height:1180}})).newPage(); p.errs = []; p.csp = 0;
    p.on('pageerror', e => p.errs.push(e.message.slice(0, 100))); p.on('console', m => { if (/Content Security Policy/.test(m.text())) p.csp++; }); return p; };
  const tour = async p => { for (const s of ["closeOv()", "go('avatar')", "home()", "document.getElementById('verBtn').click()", "closeOv()", "openBackup()", "closeOv()", "go('record')", "home()"]){ try{ await p.evaluate(s); }catch(e){} await p.waitForTimeout(120); } };
  const probe = p => p.evaluate(() => ({xss: window.__xss || 0, injected: document.querySelectorAll('[id^=pwn], a[href*=evil], img, image, video:not(#ov.on video)').length, polluted: ({}).polluted || null, progProto: Object.getPrototypeOf(prog) === Object.prototype, rendered: !!document.querySelector('.lv, .me-av')}));
  const clean = r => r.xss === 0 && r.injected === 0 && r.polluted === null && r.progProto && r.rendered;

  console.log('1. ふつうに ひらく');
  { const p = await open(); await p.goto(URL0); await p.waitForTimeout(900); await tour(p);
    check('エラーも CSP 違反も なし', !p.errs.length && !p.csp, {errs: p.errs, csp: p.csp});
    const csp = await p.evaluate(() => document.querySelector('meta[http-equiv=Content-Security-Policy]').content);
    check("CSP は default-src 'none' と スクリプトのハッシュだけ", /default-src 'none'/.test(csp) && /script-src 'sha256-[A-Za-z0-9+/=]+'(;|$)/.test(csp) && !/unsafe-eval|script-src[^;]*(unsafe-inline|\*|https?:)/.test(csp), csp);
    await p.close(); }

  console.log('2. ほぞんデータ（localStorage）を かきかえる');
  const poison = {
    'avatar のいろに SVG': {'kkr.avatar': JSON.stringify({hairColor: SVGX, clothes: SVGX, skin: SVGX, eyeColor: SVGX, shoeColor: SVGX, name: X})},
    'avatar の えらぶ項目': {'kkr.avatar': JSON.stringify({bg: X, hair: X, outfit: X, pose: X, shoes: X, face: X, eyes: X, item: X, pet: X, effect: X, acc: X})},
    'meta の すうじに HTML': {'kkr.meta': JSON.stringify({pts: X, streak: X, best: X, earned: X, hana: X, last: '2099-01-01', welcomed: true})},
    'meta の かたちが ちがう': {'kkr.meta': JSON.stringify({owned: 'x', days: 5, badges: null, mis: [], ev: 'x', last: '2099-01-01'})},
    'meta の キーに HTML': {'kkr.meta': JSON.stringify({owned: [X], badges: {[X]: X}, days: {[X]: {[X]: X}, '2026-11-01': {[X]: 1}}, mis: {[X]: {[X]: 1}}, ev: {[X]: {best: X}}, last: '2099-01-01'})},
    'settings': {'kkr.settings': JSON.stringify({theme: X, penColor: X, penSize: X, strict: X, penMode: X})},
    'prog が もじれつ': {'kkr.prog': '"abc"'},
    'prog が はいれつ': {'kkr.prog': '[1,2,3]'},
    'prog に __proto__': {'kkr.prog': '{"__proto__":{"polluted":1,"tr":1},"constructor":{"tr":1},"toString":{"tr":1},"一":{"tr":1}}'},
    'prog の あたいに HTML': {'kkr.prog': JSON.stringify({'一': {tr: X, ld: X}, [X]: {tr: 1}})},
    'avatar が すうじ': {'kkr.avatar': '5'},
    'ぜんぶ こわれた JSON': {'kkr.prog': '{', 'kkr.avatar': '{', 'kkr.meta': '{', 'kkr.settings': '{'},
  };
  for (const [name, items] of Object.entries(poison)){ const p = await open(); await p.goto(URL0);
    await p.evaluate(it => { localStorage.clear(); for (const [k, v] of Object.entries(it)) localStorage.setItem(k, v); }, items);
    await p.goto(URL0); await p.waitForTimeout(900); await tour(p); const r = await probe(p);
    check(name, clean(r) && !p.errs.length && !p.csp, {r, errs: p.errs, csp: p.csp});
    if (name.includes('__proto__')) check('  constructor などは 漢字として うけつけない', (await p.evaluate(() => Object.keys(prog).join(','))) === '一');
    await p.close(); }

  console.log('3. ひきつぎコードに しこむ');
  { const p = await open(); await p.goto(URL0); await p.waitForTimeout(600);
    const raw = `{"app":"kanji-renshu","v":2,"ts":9e15,"prog":{"一":{"tr":${JSON.stringify(X)},"fr":1e99,"ts":-5,"ld":${JSON.stringify(X)}},${JSON.stringify(X)}:{"tr":1},"__proto__":{"polluted":1,"tr":5},"constructor":{"tr":1}},` +
      `"settings":{"theme":${JSON.stringify(X)},"penColor":${JSON.stringify(X)},"penSize":${JSON.stringify(X)},"__proto__":{"polluted":1}},` +
      `"avatar":{"name":${JSON.stringify(X)},"hairColor":${JSON.stringify(SVGX)},"clothes":${JSON.stringify(SVGX)},"bg":${JSON.stringify(X)},"outfit":${JSON.stringify(X)},"__proto__":{"polluted":1}},` +
      `"meta":{"pts":${JSON.stringify(X)},"earned":1e99,"streak":${JSON.stringify(X)},"last":${JSON.stringify(X)},"owned":[${JSON.stringify(X)},"outfit:princess"],"badges":{${JSON.stringify(X)}:1},"days":{${JSON.stringify(X)}:{"a":1},"2026-11-01":{${JSON.stringify(X)}:1,"constructor":5}},"ev":{"m11-2026":{"pr":[${JSON.stringify(X)},"constructor","一"],"read":[${JSON.stringify(X)},99,-1,1],"best":${JSON.stringify(X)}}},"__proto__":{"polluted":1}}}`;
    await p.evaluate(async raw => { await restoreFrom('KKR1.' + b64e(raw)); }, raw); await p.waitForTimeout(600); await tour(p);
    let r = await probe(p); check('とりこんだ あと', clean(r) && !p.errs.length && !p.csp, {r, errs: p.errs, csp: p.csp});
    const st = await p.evaluate(() => ({keys: Object.keys(prog).join(','), name: AV.name.length, pts: typeof META.pts, earned: META.earned, owned: META.owned.join(','), theme: settings.theme}));
    check('あたいは かたどおり', st.keys === '一' && st.name <= 8 && st.pts === 'number' && st.earned <= 1e6 + 1000 && !/[<>"]/.test(st.owned) && st.theme === 'normal', st);
    await p.reload(); await p.waitForTimeout(800); await tour(p); r = await probe(p); check('よみこみなおした あと', clean(r) && !p.errs.length && !p.csp, {r, errs: p.errs});
    await p.close(); }

  console.log('4. こわれた・おおきすぎる データ');
  { const p = await open(); await p.goto(URL0); await p.waitForTimeout(600);
    const res = await p.evaluate(async () => { const out = {}; const t = async (n, v) => { try{ applySnapshot(await parseBackup(v)); out[n] = 'applied'; }catch(e){ out[n] = 'rejected'; } };
      const b64 = by => { let s = ''; for (let i = 0; i < by.length; i += 8192) s += String.fromCharCode.apply(null, by.subarray(i, i + 8192)); return btoa(s); };
      await t('garbage', 'KKR1.@@@'); await t('notjson', 'KKR1.' + btoa('{')); await t('array', '[]'); await t('null', 'null'); await t('wrongapp', JSON.stringify({app:'x', prog:{}}));
      await t('deep', '['.repeat(50000) + ']'.repeat(50000)); await t('5MB', 'KKR1.' + 'A'.repeat(5e6));
      const z = await new Response(new Blob(['{"app":"kanji-renshu","prog":{},"x":"' + 'A'.repeat(3e7) + '"}']).stream().pipeThrough(new CompressionStream('deflate-raw'))).arrayBuffer(); await t('zipbomb', 'KKZ1.' + b64(new Uint8Array(z)));
      const big = {app:'kanji-renshu', prog:{}, meta:{days:{}, mis:{}, owned:[]}}; for (let i = 0; i < 20000; i++){ const d = new Date(Date.UTC(2000, 0, 1 + i)).toISOString().slice(0, 10); big.meta.days[d] = {done:1}; big.meta.mis[d] = {a:1}; big.meta.owned.push('outfit:princess'); }
      await t('manydays', JSON.stringify(big)); out.days = Object.keys(META.days).length; out.mis = Object.keys(META.mis).length; out.owned = META.owned.length; out.bytes = JSON.stringify(localStorage).length; return out; });
    check('こわれた データは ことわる', ['garbage', 'notjson', 'array', 'null', 'wrongapp', 'deep', '5MB', 'zipbomb'].every(k => res[k] === 'rejected'), res);
    check('ほぞんする りょうに じょうげん', res.days <= 801 && res.mis <= 61 && res.owned <= 1 && res.bytes < 200000, res);
    check('エラーなし', !p.errs.length, p.errs); await p.close(); }

  console.log('5. リンクで きろくを おくりこむ（#import=）');
  { const p = await open(); await p.goto(URL0); await p.waitForTimeout(500);
    const code = await p.evaluate(() => 'KKR1.' + b64e(JSON.stringify({app:'kanji-renshu', v:2, ts:9e15, prog:{'一':{tr:9, fr:9, ts:9}}, avatar:{name:'わるもの'}, meta:{pts:99999}})));
    const q = await open(); await q.goto(URL0 + '#import=' + encodeURIComponent(code)); await q.waitForTimeout(1000);
    const r = await q.evaluate(() => ({hash: location.hash, stars: totalStars(), name: AV.name, btn: [...document.querySelectorAll('#ov.on button')].some(b => /ひきつぐ/.test(b.textContent))}));
    check('とりこまない・きかない・アドレスから けす', r.hash === '' && r.stars === 0 && r.name === '' && !r.btn && !q.errs.length, {r, errs: q.errs}); await p.close(); await q.close(); }

  console.log('6. ただしい きろくは なくさない');
  { const p = await open(); await p.goto(URL0); await p.waitForTimeout(700);
    await p.evaluate(() => { closeOv();
      DATA.slice(0, 300).forEach((d, i) => { const q = P(d.k); q.tr = 1 + i % 4; if (i % 2) q.fr = 2; if (i % 3 === 0) q.ts = 1; if (i % 7 === 0) q.wk = 1; q.tm = i + 1; q.ld = today(); }); store.set('kkr.prog', prog);
      AV = Object.assign({}, AV_DEFAULT, {name:'ゆうこ', outfit:'princess', shoes:'glass', shoeColor:SHOE_COLORS[1], pose:'peace', eyes:'shoujo', face:'shoujo', bg:'p_bloom', item:ITEMS[2][0], pet:PETS[2][0], effect:EFFECTS[1][0], acc:ACCS[3][0]}); saveAV();
      settings.theme = 'yume'; settings.strict = 'hard'; settings.nums = false; saveSet();
      META.pts = 777; META.owned = Object.entries(SHOP).flatMap(([k, l]) => l.slice(0, 4).map(x => k + ':' + x[0])); META.hana = 12; META.tests = 5; META.perfect = 2; saveMeta(); progressChanged(); });
    await p.waitForTimeout(2200);
    const before = await p.evaluate(() => { closeOv(); return Object.fromEntries(['prog', 'avatar', 'settings', 'meta'].map(k => [k, localStorage.getItem('kkr.' + k)])); });
    await p.reload(); await p.waitForTimeout(600);
    const diff = await p.evaluate(b4 => { const canon = o => JSON.stringify(o, (k, v) => v && typeof v === 'object' && !Array.isArray(v) ? Object.fromEntries(Object.entries(v).sort()) : v);
      return [['prog', prog], ['avatar', AV], ['settings', settings], ['meta', META]].flatMap(([n, cur]) => { const a = JSON.parse(b4[n]); return Object.keys(a).filter(k => !(k in cur) || canon(a[k]) !== canon(cur[k])).map(k => n + '.' + k); }); }, before);
    check('よみこみなおしても おなじ', diff.length === 0 && !p.errs.length, {diff: diff.slice(0, 10), errs: p.errs}); await p.close(); }

  console.log('7. ともだちカード（QR）に しこむ');
  { const p = await open(); await p.goto(URL0); await p.waitForTimeout(600);
    await p.evaluate(() => { closeOv(); go('friends'); }); await p.waitForTimeout(300);
    const res = await p.evaluate(async ({X, SVGX}) => {
      const enc = async o => 'KKC1.' + (await (async () => { const buf = await new Response(new Blob([typeof o === 'string' ? o : JSON.stringify(o)]).stream().pipeThrough(new CompressionStream('deflate-raw'))).arrayBuffer(); let b = ''; new Uint8Array(buf).forEach(x => b += String.fromCharCode(x)); return btoa(b); })());
      const wk = weekKey(), out = {};
      const base = {a:'kkc', v:1, id:'evil000001', n:X, av:{hairColor:SVGX, clothes:SVGX, bg:X, outfit:X, pose:X, name:X, '__proto__':{polluted:1}}, w:wk, d:'<b>9</b>', y:99, s:1e99, m:-5};
      const tryAdd = async (name, code) => { const before = document.querySelectorAll('#ov.on').length; await handleScanned(code); const dialog = !!document.querySelector('#ov.on .fr-conf'); if (dialog) document.querySelector('#ov.on .big-btn:not(.gray)').click(); out[name] = dialog ? 'added' : 'refused'; await new Promise(r => setTimeout(r, 50)); };
      await tryAdd('html', await enc(base));
      const f = FRIENDS.find(x => x.c.id === 'evil000001'); out.vals = f ? {nm:f.c.nm.length, d:f.c.d, y:f.c.y, s:f.c.s, m:f.c.m, hair:f.c.av.hairColor, outfit:f.c.av.outfit} : null;
      const next = new Date(wk + 'T00:00:00'); next.setDate(next.getDate() + 21);
      await tryAdd('future', await enc(Object.assign({}, base, {id:'evil000002', w:today(next)})));
      await tryAdd('notMonday', await enc(Object.assign({}, base, {id:'evil000003', w:today(new Date(new Date(wk + 'T00:00:00').getTime() + 864e5))})));
      await tryAdd('badId', await enc(Object.assign({}, base, {id:'<x>'})));
      await tryAdd('array', await enc([1, 2]));
      await tryAdd('wrongVer', await enc(Object.assign({}, base, {id:'evil000004', v:2})));
      await tryAdd('notCard', 'https://evil.example/');
      await tryAdd('long', 'KKC1.' + 'A'.repeat(5000));
      await tryAdd('bomb', await enc('{"a":"kkc","v":1,"x":"' + 'A'.repeat(5e6) + '"}'));
      await tryAdd('self', await enc(Object.assign({}, base, {id:myCardId()})));
      FRIENDS = []; saveFriends();
      for (let i = 0; i < 35; i++) await tryAdd('fill' + i, await enc(Object.assign({}, base, {id:'fill' + String(i).padStart(6, '0'), n:'f' + i})));
      out.cap = FRIENDS.length; out.maxS = ALLK.length * 3; render(); await new Promise(r => setTimeout(r, 300));
      Object.keys(out).filter(k => /^fill/.test(k)).forEach(k => delete out[k]);
      return out; }, {X, SVGX});
    check('こわれた・へんな カードは ことわる', ['future', 'notMonday', 'badId', 'array', 'wrongVer', 'notCard', 'long', 'bomb', 'self'].every(k => res[k] === 'refused'), res);
    check('へんな あたいは かたどおりに なおす', res.html === 'added' && res.vals && res.vals.nm <= 8 && res.vals.d === 0 && res.vals.y === 7 && res.vals.s <= res.maxS && res.vals.m === 0 && /^#[0-9a-f]{6}$/i.test(res.vals.hair) && res.vals.outfit === 'tshirt', res);
    check(`ともだちは 30にん まで`, res.cap === 30, res.cap);
    let r = await probe(p); check('ランキングに さしこまれない', clean(r) && !p.errs.length && !p.csp, {r, errs: p.errs, csp: p.csp});
    await p.reload(); await p.waitForTimeout(700); await p.evaluate(() => { closeOv(); go('friends'); }); await p.waitForTimeout(300);
    r = await probe(p); check('よみこみなおした あとも', clean(r) && !p.errs.length && !p.csp, {r, errs: p.errs});
    await p.close(); }
  { const p = await open(); await p.goto(URL0);
    await p.evaluate(({X}) => { localStorage.clear(); localStorage.setItem('kkr.friends', JSON.stringify([{c:{a:'kkc', v:1, id:'stored0001', n:X, av:{bg:X}, w:'2026-11-16', d:X, y:X, s:X}, got:X}, {c:null}, 'x', 5, {c:{a:'kkc', v:1, id:'<b>', w:'2026-11-16'}}].concat(Array.from({length:40}, (_, i) => ({c:{a:'kkc', v:1, id:'many' + String(i).padStart(6, '0'), w:'2026-11-16'}, got:1}))))); localStorage.setItem('kkr.cid', JSON.stringify(X)); }, {X});
    await p.goto(URL0); await p.waitForTimeout(800); await p.evaluate(() => { closeOv(); go('friends'); }); await p.waitForTimeout(400);
    const r = await probe(p); const st = await p.evaluate(() => ({n: FRIENDS.length, cid: myCardId()}));
    check('ほぞんした ともだちデータを かきかえても だいじょうぶ', clean(r) && st.n <= 30 && /^[a-z0-9]{10}$/.test(st.cid) && !p.errs.length && !p.csp, {r, st, errs: p.errs, csp: p.csp});
    await p.close(); }

  console.log('8. 4きゅう〜1きゅうの データ（あとから よみこむ）');
  { const p = await open(); await p.route(/pack-g7-.*\.json$/, async r => { const res = await r.fetch(); const t = (await res.text()).replace(/"m":"[^"]*"/, '"m":"<img src=x onerror=window.__xss=9>"'); r.fulfill({response: res, body: t}); });
    await p.goto(URL0); await p.waitForTimeout(600); await p.evaluate(() => { closeOv(); go('list', {g:7}); }); await p.waitForTimeout(1200);
    const r = await p.evaluate(() => ({cur: cur.name, msg: document.querySelector('#ov.on .bk-note')?.textContent || '', loaded: packState[7] === 'ok'}));
    check('かきかえられた データは よみこまない', r.cur === 'home' && !r.loaded && /かきかえられて/.test(r.msg) && !(await p.evaluate(() => window.__xss || 0)), r); await p.close(); }
  { const p = await open(); await p.route(/pack-g8-.*\.json$/, r => r.fulfill({status: 200, contentType: 'application/json', body: '[]'}));
    await p.goto(URL0); await p.waitForTimeout(600); await p.evaluate(() => { closeOv(); go('kanji', {k:[...PACKS[8].ks][0]}); }); await p.waitForTimeout(1000);
    check('ちがう ファイルに すりかえられても よみこまない', await p.evaluate(() => cur.name === 'home' && packState[8] !== 'ok'), null); await p.close(); }
  { const p = await open(); await p.goto(URL0); await p.waitForTimeout(600);
    const r = await p.evaluate(async () => { closeOv(); const out = {}; for (const g of Object.keys(PACKS)){ try{ await ensurePack(g); out[g] = BYK[[...PACKS[g].ks][0]] ? 'ok' : 'missing'; }catch(e){ out[g] = 'err:' + e.message; } } out.total = ALLK.length; out.data = DATA.length; return out; });
    check('ただしい データは ぜんぶ よめる', Object.keys(r).filter(k => /^\d+$/.test(k)).every(k => r[k] === 'ok') && r.total === r.data, r);
    await p.evaluate(() => { const ks = [...PACKS[12].ks].slice(0, 3); ks.forEach(k => prog[k] = {tr:1, fr:1, ts:1, wk:1}); store.set('kkr.prog', prog); });
    await p.reload(); await p.waitForTimeout(700);
    const kept = await p.evaluate(() => [...PACKS[12].ks].slice(0, 3).every(k => stars(k) === 3) && packState[12] !== 'ok');
    check('よみこむ まえでも 上の級の きろくは きえない', kept, null); await p.close(); }

  await browser.close(); server.close(); fs.rmSync(OUT, {recursive: true, force: true});
  console.log(failed ? `\n${failed} けん しっぱい` : '\nぜんぶ OK');
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
