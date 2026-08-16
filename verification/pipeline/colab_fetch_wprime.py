# -*- coding: utf-8 -*-
"""colab_fetch_wprime.py ―― 追補W′ の Colab 側取得ブート。

役割: コミット固定 URL から凍結器材（土台・前置き・シナリオ・boot_wprime.py）を取得し、
SHA(LF) を凍結値と照合してから boot_wprime.py を exec する。
（boot_wprime.py 自身も同じ照合を持つ——二重だが、取得直後に落とすほうが診断が容易。）

使い方（Colab セル・1行）:
    _pad=0; WP_COMMIT='<コミットハッシュ>'; WP_MODE='pilot'; WP_PILOT_N=11; WP_RUN_TAG='wprime-pilot1'
    import urllib.request as _u; exec(_u.urlopen('https://raw.githubusercontent.com/YutaKusumi/ryokai-os/'+WP_COMMIT+'/verification/pipeline/colab_fetch_wprime.py').read().decode())
"""
import hashlib
import os
import urllib.request

COMMIT = str(globals().get('WP_COMMIT', 'main'))
RAWBASE = 'https://raw.githubusercontent.com/YutaKusumi/ryokai-os/%s/verification/' % COMMIT
ROOT = str(globals().get('WP_ROOT', '/content'))

# (相対パス, SHA16(LF)) —— FREEZE-RECORD の凍結値
FILES = [
    ('arms/A2-on-full.md',               'AAB363D85E103C13'),
    ('armsE/preamble-Onull.md',          '2123B3CD8586E7DF'),
    ('armsWprime/preamble-B1prime.md',   '671A5B32A769FC17'),
    ('armsWprime/preamble-B2prime.md',   '12A1218CA3DC3DD9'),
    ('armsWprime/preamble-B3prime.md',   'DF23F7086C32D757'),
    ('armsWprime/preamble-Nsecond.md',   'FBC56D8DE4944017'),
    ('app-scenarios.json',               None),               # SHA は N2 本文241字で boot が検査
    ('pipeline/boot_wprime.py',          None),               # 取得後に表示のみ（自己照合は本文が持つ）
]


def _sha16(b):
    return hashlib.sha256(b.replace(b'\r\n', b'\n')).hexdigest()[:16].upper()


print('[fetch] commit=%s root=%s' % (COMMIT, ROOT))
for rel, want in FILES:
    dst = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    data = urllib.request.urlopen(RAWBASE + rel).read()
    open(dst, 'wb').write(data)
    got = _sha16(data)
    tag = 'OK' if (want is None or got == want) else 'MISMATCH'
    print('[fetch] %-36s %s %s' % (rel, got, tag))
    assert want is None or got == want, 'SHA 不一致: %s' % rel

exec(open(os.path.join(ROOT, 'pipeline/boot_wprime.py'), encoding='utf-8').read())
