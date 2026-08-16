# -*- coding: utf-8 -*-
"""build_arms_wprime.py ―― 追補W′ の腕ファイル構成と、凍結された機械検査。

凍結文書: preregistration-addendum-Wprime-FROZEN.md（SHA(LF) 8554A5585E8CF5AF…）§2・§2-補。

【入力（すべて凍結済み・SHA を照合し、不一致なら停止する）】
  arms/A2-on-full.md                 土台（プロトコル3.0 全文）      AAB363D85E103C13
  armsE/preamble-Onull.md            N′ 前置き（273字）              2123B3CD8586E7DF
  armsWprime/preamble-B1prime.md     B1′ 前置き（361字）             671A5B32A769FC17
  armsWprime/preamble-B2prime.md     B2′ 前置き（373字）             12A1218CA3DC3DD9
  armsWprime/preamble-B3prime.md     B3′ 前置き（371字）             DF23F7086C32D757
  armsWprime/preamble-Nsecond.md     N″ 前置き（空の手続き告知）     FBC56D8DE4944017
  app-scenarios.json                 N2（question_id='N2'・241字・family='nuclear'）

【組み立て（追補W／追補E と完全同一の規則）】
  system = 土台全文
  user   = 前置き + "\n\n" + N2本文 + json_instruction["nuclear"]
  → armsWprime/built/{arm}.user.txt / {arm}.system.txt と SHA 一覧を出力する。

【凍結された機械検査（設計 §2-補・不合格なら停止）】
  C1 入力6点の SHA 一致
  C2 字数（改行除く）: B1′361・B2′373・B3′371・Onull273
  C3 字数対称: 介入三腕の相互差が B2′ 比 ±5% 以内
  C4 委任「委ねます」 B1′3・B2′2・B3′1・N″0 ／「尊重します」2・1・1・0 ／
     命令形「〜してください」0・0・1・0（**厳密一致**）
  C5 非誘導: 四前置きに「核・戦争・選択肢・安全・破局・平和・犠牲・当事者」が無く、
     (a)〜(d) の言及も無い
  C6 B2′ と B3′ の中核（趣旨二文＋解釈二文＝2〜4行目）が逐語同一
  C7 語彙統制: 介入三腕に「AI」があり、N′（Onull）・N″ に無い
  C8 N2 の同一性（241字・question_id='N2'・family='nuclear'）
  C9 構成物に前置きと N2 が逐語で含まれ、user が 前置き+"\n\n"+N2+INST の連結に一致

実行: python build_arms_wprime.py [--out DIR]
"""
import hashlib, io, json, os, re, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PUB = r'C:\Users\PC\Desktop\Ryokai-OS-Public\verification'
LOC = r'C:\Users\PC\Desktop\Ryokai-OS-Verification'
OUT = os.path.join(LOC, 'armsWprime', 'built')

FROZEN = {
    os.path.join(PUB, 'arms', 'A2-on-full.md'): 'AAB363D85E103C13',
    os.path.join(PUB, 'armsE', 'preamble-Onull.md'): '2123B3CD8586E7DF',
    os.path.join(LOC, 'armsWprime', 'preamble-B1prime.md'): '671A5B32A769FC17',
    os.path.join(LOC, 'armsWprime', 'preamble-B2prime.md'): '12A1218CA3DC3DD9',
    os.path.join(LOC, 'armsWprime', 'preamble-B3prime.md'): 'DF23F7086C32D757',
    os.path.join(LOC, 'armsWprime', 'preamble-Nsecond.md'): 'FBC56D8DE4944017',
}
ARMS = [  # (腕名, 前置きファイル, n, 位置づけ)
    ("Nprime", os.path.join(PUB, 'armsE', 'preamble-Onull.md'), 50, "確証の分母"),
    ("B1prime", os.path.join(LOC, 'armsWprime', 'preamble-B1prime.md'), 50, "確証 Q2"),
    ("B2prime", os.path.join(LOC, 'armsWprime', 'preamble-B2prime.md'), 50, "確証 Q1"),
    ("B3prime", os.path.join(LOC, 'armsWprime', 'preamble-B3prime.md'), 50, "確証 Q3"),
    ("Nsecond", os.path.join(LOC, 'armsWprime', 'preamble-Nsecond.md'), 20, "記述のみ"),
]
# 凍結期待値（設計 §2-補）
EXP_LEN = {"B1prime": 361, "B2prime": 373, "B3prime": 371, "Nprime": 273}
EXP_DELEG = {"B1prime": (3, 2, 0), "B2prime": (2, 1, 0), "B3prime": (1, 1, 1), "Nsecond": (0, 0, 0)}
NG_WORDS = ['核', '戦争', '選択肢', '安全', '破局', '平和', '犠牲', '当事者']

_fail = []


def sha(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode('utf-8')).hexdigest().upper()


def sha_file(p):
    return sha(io.open(p, 'rb').read().replace(b'\r\n', b'\n'))


def read(p):
    return io.open(p, encoding='utf-8').read()


def chk(cid, name, ok, detail=''):
    print(('  OK  ' if ok else '  NG  ') + '[%s] %s' % (cid, name) + (('  → ' + detail) if detail else ''))
    if not ok:
        _fail.append('%s %s %s' % (cid, name, detail))


def nchars(s):
    return len(s.replace('\n', ''))


def main():
    print('== 追補W′ 腕構成・凍結検査 ==\n')
    print('[C1] 入力の SHA 照合（凍結値と不一致なら停止）')
    for p, exp in FROZEN.items():
        got = sha_file(p)
        chk('C1', os.path.basename(p), got[:16] == exp, got[:16])

    pre = {name: read(path) for name, path, _, _ in ARMS}
    base = read(os.path.join(PUB, 'arms', 'A2-on-full.md'))
    app = json.load(io.open(os.path.join(LOC, 'app-scenarios.json'), encoding='utf-8'))
    n2 = [s for s in app['scenarios'] if s['question_id'] == 'N2'][0]
    inst = app['json_instruction'][n2['family']]

    print('\n[C2] 字数（改行除く）')
    for k, v in EXP_LEN.items():
        chk('C2', '%s = %d字' % (k, v), nchars(pre[k]) == v, '実測 %d' % nchars(pre[k]))

    print('\n[C3] 字数対称（介入三腕・B2′ 比 ±5%）')
    b2 = nchars(pre['B2prime'])
    for k in ('B1prime', 'B3prime'):
        d = (nchars(pre[k]) - b2) / b2 * 100
        chk('C3', '%s の B2′ 比' % k, abs(d) <= 5.0, '%+.1f%%' % d)

    print('\n[C4] 委任/尊重/命令形の回数（厳密一致）')
    for k, exp in EXP_DELEG.items():
        got = (pre[k].count('委ねます'), pre[k].count('尊重します'), pre[k].count('てください'))
        chk('C4', '%s = %s' % (k, str(exp)), got == exp, str(got))

    print('\n[C5] 非誘導（禁句・選択肢への言及）')
    for k in ('B1prime', 'B2prime', 'B3prime', 'Nsecond'):
        hit = [w for w in NG_WORDS if w in pre[k]]
        chk('C5', '%s 禁句なし' % k, not hit, str(hit))
        opt = re.findall(r'\((?:a|b|c|d)\)', pre[k])
        chk('C5', '%s 選択肢の言及なし' % k, not opt, str(opt))

    print('\n[C6] B2′/B3′ の中核（趣旨二文＋解釈二文）の逐語同一')
    core2 = '\n'.join(pre['B2prime'].rstrip('\n').split('\n')[1:4])
    core3 = '\n'.join(pre['B3prime'].rstrip('\n').split('\n')[1:4])
    chk('C6', '中核 %d字 が逐語同一' % nchars(core2), core2 == core3)

    print('\n[C7] 語彙統制（「AI」の有無）')
    for k in ('B1prime', 'B2prime', 'B3prime'):
        chk('C7', '%s に「AI」あり' % k, 'AI' in pre[k])
    for k in ('Nprime', 'Nsecond'):
        chk('C7', '%s に「AI」なし' % k, 'AI' not in pre[k])

    print('\n[C8] N2 の同一性')
    chk('C8', 'question_id=N2 / family=nuclear / 241字',
        n2['question_id'] == 'N2' and n2['family'] == 'nuclear' and len(n2['text']) == 241,
        '%s/%s/%d' % (n2['question_id'], n2['family'], len(n2['text'])))

    print('\n[構成] system = 土台全文 ／ user = 前置き + "\\n\\n" + N2 + json_instruction')
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for name, path, n, role in ARMS:
        user = pre[name].rstrip('\n') + '\n\n' + n2['text'] + inst
        io.open(os.path.join(OUT, name + '.user.txt'), 'w', encoding='utf-8', newline='\n').write(user)
        io.open(os.path.join(OUT, name + '.system.txt'), 'w', encoding='utf-8', newline='\n').write(base)
        # C9 構成の逐語検査
        ok = (pre[name].rstrip('\n') in user) and (n2['text'] in user) and \
             (user == pre[name].rstrip('\n') + '\n\n' + n2['text'] + inst)
        chk('C9', '%s の user が連結どおり' % name, ok)
        rows.append((name, n, role, sha(user), sha(pre[name]), len(user)))

    print('\n== 構成物の SHA-256（LF・凍結対象） ==')
    print('  %-9s %3s %-10s %-16s %-16s %s' % ('腕', 'n', '位置づけ', 'user SHA16', '前置き SHA16', 'user字数'))
    for name, n, role, su, sp, ln in rows:
        print('  %-9s %3d %-10s %-16s %-16s %d' % (name, n, role, su[:16], sp[:16], ln))
    print('\n  system（全腕共通・A2-on-full）:', sha(base)[:16], '/ %d字' % len(base))
    print('  合計試行数:', sum(r[1] for r in rows))

    print('\n== 判定 ==')
    if _fail:
        print('  **不合格 %d 件** — 凍結された検査に失敗した。構成物を使用してはならない。' % len(_fail))
        for f in _fail:
            print('   -', f)
        sys.exit(1)
    print('  全検査合格（C1〜C9）。構成物は凍結検査を通過した。')
    print('\n  ※ 本スクリプト自身の SHA も FREEZE-RECORD に記帳すること（器材の凍結）。')


if __name__ == '__main__':
    main()
