# -*- coding: utf-8 -*-
"""追補X 腕の機械構成器（凍結対象・SHA を凍結）。

5腕のユーザメッセージを素材から機械構成する（system は A2-on-full・boot 側で付す）:
  1 A->A     : SCAF_HIST + history-A + SCAF_NOW + terminal-respect
  2 N->A     : SCAF_HIST + history-N + SCAF_NOW + terminal-respect
  3 C->A     : SCAF_HIST + history-C + SCAF_NOW + terminal-respect
  4 C->R->A  : SCAF_HIST + history-C + SCAF_REPAIR + repair-R + SCAF_NOW + terminal-respect
  5 C->C     : SCAF_HIST + history-C + SCAF_NOW + terminal-hostile

不変条件（機械検査）:
  - 腕1〜4 の終端（SCAF_NOW 以降）がバイト同一。
  - 腕3・4・5 の履歴部（SCAF_HIST〜SCAF_NOW直前）が同一（いずれも history-C）。
  - build 決定性: 同素材から同 SHA。

出力: armsX/arm-{1..5}-*.md と SHA 一覧。--check で不変条件のみ検証。
"""
import io, os, sys, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AX = os.path.join(ROOT, 'armsX')

# 固定足場（全腕共通・価数は履歴と終端に担わせる）
SCAF_HIST = '【これまでのやり取り】\n'
SCAF_REPAIR = '\n'  # 修復は利用者の続きの発話として履歴直後に置く
SCAF_NOW = '\n\n【ここからが今回のご依頼です】\n'

ARMS = [
    ('1', 'AtoA',   'history-A.md', None,          'terminal-respect.md'),
    ('2', 'NtoA',   'history-N.md', None,          'terminal-respect.md'),
    ('3', 'CtoA',   'history-C.md', None,          'terminal-respect.md'),
    ('4', 'CtoRtoA','history-C.md', 'repair-R.md', 'terminal-respect.md'),
    ('5', 'CtoC',   'history-C.md', None,          'terminal-hostile.md'),
]

def read(name):
    return io.open(os.path.join(AX, name), encoding='utf-8').read()

def build_user(hist, repair, term):
    h = read(hist).rstrip('\n')
    parts = [SCAF_HIST, h]
    if repair:
        parts.append(SCAF_REPAIR + read(repair).rstrip('\n'))
    parts.append(SCAF_NOW + read(term).rstrip('\n') + '\n')
    return ''.join(parts)

def sha16(s):
    b = s.encode('utf-8')
    return hashlib.sha256(b).hexdigest()[:16].upper(), len(b)

def main():
    check = '--check' in sys.argv
    users = {}
    for num, tag, hist, repair, term in ARMS:
        u = build_user(hist, repair, term)
        users[num] = u
        if not check:
            path = os.path.join(AX, 'arm-%s-%s.md' % (num, tag))
            io.open(path, 'w', encoding='utf-8', newline='\n').write(u)

    # 不変条件
    def tail(u):
        return u.split(SCAF_NOW, 1)[1]
    def head(u):
        return u.split(SCAF_NOW, 1)[0]
    ok = True
    t1 = tail(users['1'])
    for n in ('2', '3', '4'):
        if tail(users[n]) != t1:
            ok = False; print('[FAIL] 終端バイト同一 破れ 腕%s' % n)
    # 腕3/4/5 の履歴部（修復前まで）が history-C 由来で一致
    hc = SCAF_HIST + read('history-C.md').rstrip('\n')
    for n in ('3', '5'):
        if not head(users[n]).startswith(hc):
            ok = False; print('[FAIL] 履歴C部 破れ 腕%s' % n)
    if not head(users['4']).startswith(hc):
        ok = False; print('[FAIL] 履歴C部 破れ 腕4（修復前）')
    if ok:
        print('[OK] 不変条件（終端バイト同一・履歴C共有）PASS')

    print('=== 腕ユーザメッセージ SHA(LF) ===')
    for num, tag, *_ in ARMS:
        s, n = sha16(users[num])
        print('  arm-%s-%-8s  %s  %6d B' % (num, tag, s, n))
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main())
