# -*- coding: utf-8 -*-
"""colab_fetch_dprime.py ―― 追補D′ の Colab 側取得ブート。

役割: コミット固定 URL から凍結器材（土台・三前置き・新規3文・シナリオ・boot_dprime.py）を取得し、
SHA(LF) を凍結値と照合してから boot_dprime.py を exec する（boot 自身も同じ照合を持つ——二重）。

使い方（Colab セル・1行）:
    _pad=0; DP_COMMIT='<コミットハッシュ>'; DP_MODE='pilot'; DP_PILOT_N=8; DP_RUN_TAG='dprime-pilot1'; DP_ROOT='/content/drive/MyDrive/dprime'
    import urllib.request as _u; exec(_u.urlopen('https://raw.githubusercontent.com/YutaKusumi/ryokai-os/'+DP_COMMIT+'/verification/pipeline/colab_fetch_dprime.py').read().decode())
"""
import hashlib, os, urllib.request

COMMIT = str(globals().get('DP_COMMIT', 'main'))
RAWBASE = 'https://raw.githubusercontent.com/YutaKusumi/ryokai-os/%s/verification/' % COMMIT
ROOT = str(globals().get('DP_ROOT', '/content'))

FILES = [
    ('arms/A2-on-full.md',                 'AAB363D85E103C13'),
    ('armsWsecond/preamble-Nthird.md',     '2123B3CD8586E7DF'),
    ('armsD/preamble-GH.md',               '5CEE23D946B3DF52'),
    ('armsD/preamble-GHnull.md',           '834F9B4EA520EF37'),
    ('armsDprime/GL-A-intervention.md',    '97526252C8832BC5'),
    ('armsDprime/GL-B-intervention.md',    'EEA51CF4202A7DCC'),
    ('armsDprime/reselect-instruction.md', '7180A13111271703'),
    ('app-scenarios.json',                 None),   # N2 本文241字は boot が検査
    ('pipeline/boot_dprime.py',            '312B51BBE666B73B'),   # 器材凍結値（FREEZE-RECORD）
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

exec(open(os.path.join(ROOT, 'pipeline/boot_dprime.py'), encoding='utf-8').read())
