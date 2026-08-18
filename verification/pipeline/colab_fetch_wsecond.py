# -*- coding: utf-8 -*-
"""colab_fetch_wsecond.py ―― 追補W″ の Colab 側取得ブート。

役割: コミット固定 URL から凍結器材（土台・四腕・K スキーマ・シナリオ・boot_wsecond.py）を取得し、
SHA(LF) を凍結値と照合してから boot_wsecond.py を exec する。
（boot_wsecond.py 自身も同じ照合を持つ——二重だが、取得直後に落とすほうが診断が容易。）

使い方（Colab セル・1行）:
    _pad=0; WS_COMMIT='<コミットハッシュ>'; WS_MODE='pilot'; WS_PILOT_N=8; WS_RUN_TAG='wsecond-pilot1'; WS_ROOT='/content/drive/MyDrive/wsecond'
    import urllib.request as _u; exec(_u.urlopen('https://raw.githubusercontent.com/YutaKusumi/ryokai-os/'+WS_COMMIT+'/verification/pipeline/colab_fetch_wsecond.py').read().decode())
"""
import hashlib
import os
import urllib.request

COMMIT = str(globals().get('WS_COMMIT', 'main'))
RAWBASE = 'https://raw.githubusercontent.com/YutaKusumi/ryokai-os/%s/verification/' % COMMIT
ROOT = str(globals().get('WS_ROOT', '/content'))

# (相対パス, SHA16(LF)) —— FREEZE-RECORD の凍結値
FILES = [
    ('arms/A2-on-full.md',                     'AAB363D85E103C13'),
    ('armsWsecond/preamble-Nthird.md',         '2123B3CD8586E7DF'),
    ('armsWsecond/instruction-Kdoubleprime.md', '1AA7523EF0286774'),
    ('armsWsecond/preamble-F.md',              '78AB74638915CE9D'),
    ('armsWsecond/preamble-Fnull.md',          '882D8EE7D09CE6E9'),
    ('armsWsecond/schema-Kdoubleprime.md',     '7A5E191E5571597F'),
    ('app-scenarios.json',                     None),   # N2 本文241字は boot が検査
    ('pipeline/boot_wsecond.py',               '9CB212E41E2E9147'),
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
    print('[fetch] %-40s %s %s' % (rel, got, tag))
    assert want is None or got == want, 'SHA 不一致: %s' % rel

exec(open(os.path.join(ROOT, 'pipeline/boot_wsecond.py'), encoding='utf-8').read())
