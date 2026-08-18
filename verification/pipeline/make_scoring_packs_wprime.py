# -*- coding: utf-8 -*-
"""make_scoring_packs_wprime.py ―― 追補W′ 盲検採点パックの生成（匿名化・シャッフル・分割）。

【なぜ要るか（2026-08-18・器材の穴の発見）】
  redactor_wprime.py の redacted 出力は trial_id をそのまま持つが、
  trial_id には腕名が含まれる（例: wprime-main1-002-B2prime-01）。
  また並び順は凍結 SCHEDULE のままで、位置からも腕が復元できる（4腕交互＋10ごとにN″）。
  **このまま採点者に渡すと盲検が最初から破れる。**
  本器材は (1) 匿名ID（S001..S220）への置換、(2) シード固定の決定的シャッフル、
  (3) 分割パック化を行い、対応表（匿名ID→trial_id）を**封印**側に出す。
  追補D の redactor（シード48）の作法の継承。

出力:
  scoring/packs/pack-01.jsonl .. pack-NN.jsonl   採点者に渡す（匿名ID・伏字本文のみ）
  scoring/SEALED-id-map.json                     封印（採点完了まで開かない）
"""
import io
import json
import os
import random
import sys

_OUT = sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = r'C:\Users\PC\Desktop\Ryokai-OS-Verification'
RED = os.path.join(ROOT, 'results', 'wprime-main', 'redaction',
                   'redacted-wprime-main1-Qwen3-30B-A3B-Instruct-2507.jsonl')
OUTDIR = os.path.join(ROOT, 'results', 'wprime-main', 'scoring')
SEED = 48                      # 追補D redactor と同一（決定的・記帳済みの慣例値）
PACK = 22                      # 22件×10パック


def main():
    rows = [json.loads(l) for l in io.open(RED, encoding='utf-8') if l.strip()]
    assert len(rows) == 220, len(rows)
    rng = random.Random(SEED)
    order = list(range(len(rows)))
    rng.shuffle(order)
    os.makedirs(os.path.join(OUTDIR, 'packs'), exist_ok=True)
    idmap = {}
    packs = []
    for j, idx in enumerate(order):
        sid = 'S%03d' % (j + 1)
        idmap[sid] = rows[idx]['trial_id']
        packs.append({'sid': sid, 'text': rows[idx]['text']})
    npk = 0
    for i in range(0, len(packs), PACK):
        npk += 1
        p = os.path.join(OUTDIR, 'packs', 'pack-%02d.jsonl' % npk)
        with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
            for row in packs[i:i + PACK]:
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
    sealed = os.path.join(OUTDIR, 'SEALED-id-map.json')
    io.open(sealed, 'w', encoding='utf-8', newline='\n').write(
        json.dumps({'_封印': '採点完了・裁定確定まで開かない（key照合の段でのみ使用）',
                    'seed': SEED, 'map': idmap}, ensure_ascii=False, indent=1))
    print('パック %d 個（各%d件）→ scoring/packs/' % (npk, PACK))
    print('封印対応表 → SEALED-id-map.json（採点完了まで開かない）')
    # 盲検の機械検査: パック内に腕名・trial_id 断片が残っていないか
    ng = 0
    for i in range(1, npk + 1):
        t = io.open(os.path.join(OUTDIR, 'packs', 'pack-%02d.jsonl' % i), encoding='utf-8').read()
        for w in ['Nprime', 'B1prime', 'B2prime', 'B3prime', 'Nsecond', 'wprime-main1', 'trial']:
            if w in t:
                ng += 1
                print('  ★腕/ID 断片が残存: pack-%02d に %s' % (i, w))
    print('盲検の機械検査: %s' % ('腕名・ID断片の残存 0 ✔' if ng == 0 else '★%d 件' % ng))


if __name__ == '__main__':
    main()
