# -*- coding: utf-8 -*-
"""make_scoring_packs_dprime.py ―― 追補D′ 盲検採点パックの生成（匿名化・シャッフル・分割・W″ 器材の継承）。

第一ターン 200 件: 匿名ID S001..S200・シード48 の決定的シャッフル・20件×10パック。
GL 40 件:        匿名ID G001..G040・シード48 のシャッフル・10件×4パック（R1/R2 本文・loop_excluded 旗つき）。
対応表（匿名ID→trial_id）は**封印**（SEALED-id-map-dprime.json・採点完了・裁定確定まで開かない）。
パック内に腕名・ID断片が残っていないことを機械検査（GL は介入文引用が判定必要語のため腕語の検査対象から除外——凍結 §5「構造的に自明」）。
"""
import io, json, os, random, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = 'Qwen3-30B-A3B-Instruct-2507'
RED = os.path.join(ROOT, 'results', 'dprime-main', 'redaction')
OUTDIR = os.path.join(ROOT, 'results', 'dprime-main', 'scoring')
SEED = 48


def load(p):
    return [json.loads(l) for l in io.open(p, encoding='utf-8') if l.strip()]


def main():
    ft = load(os.path.join(RED, 'redacted-dprime-main1-%s.jsonl' % M))
    gl = load(os.path.join(RED, 'gl-scoring-dprime-main1-%s.jsonl' % M))
    assert len(ft) == 200 and len(gl) == 40, (len(ft), len(gl))
    rng = random.Random(SEED)
    os.makedirs(os.path.join(OUTDIR, 'packs'), exist_ok=True)
    idmap = {}
    # 第一ターン
    order = list(range(200)); rng.shuffle(order)
    rows = []
    for j, idx in enumerate(order):
        sid = 'S%03d' % (j + 1)
        idmap[sid] = ft[idx]['trial_id']
        rows.append({'sid': sid, 'text': ft[idx]['text'], 'loop_excluded': ft[idx]['loop_excluded']})
    for i in range(0, 200, 20):
        p = os.path.join(OUTDIR, 'packs', 'ft-pack-%02d.jsonl' % (i // 20 + 1))
        io.open(p, 'w', encoding='utf-8', newline='\n').write(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows[i:i + 20]))
    # GL
    order_g = list(range(40)); rng.shuffle(order_g)
    rows_g = []
    for j, idx in enumerate(order_g):
        gid = 'G%03d' % (j + 1)
        g = gl[idx]
        idmap[gid] = g['src_trial_id']
        rows_g.append({'gid': gid, 'r1_text': g['r1_text'], 'r2_text': g['r2_text_scored'],
                       'loop_excluded_r1': g['loop_excluded_r1'], 'loop_excluded_r2': g['loop_excluded_r2'],
                       'apparatus': g['apparatus']})
    for i in range(0, 40, 10):
        p = os.path.join(OUTDIR, 'packs', 'gl-pack-%02d.jsonl' % (i // 10 + 1))
        io.open(p, 'w', encoding='utf-8', newline='\n').write(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows_g[i:i + 10]))
    io.open(os.path.join(OUTDIR, 'SEALED-id-map-dprime.json'), 'w', encoding='utf-8', newline='\n').write(
        json.dumps({'_封印': '採点完了・key照合前裁定の確定まで開かない', 'seed': SEED, 'map': idmap}, ensure_ascii=False, indent=1))
    print('第一ターン 10 パック（各20件）・GL 4 パック（各10件）→ scoring/packs/')
    # 盲検の機械検査
    ng = 0
    for i in range(1, 11):
        t = io.open(os.path.join(OUTDIR, 'packs', 'ft-pack-%02d.jsonl' % i), encoding='utf-8').read()
        for w in ['Nthird', 'GHp', 'GHnullp', 'main1', 'trial', 'preamble', 'Onull', 'dprime', 'GL-A', 'GL-B']:
            if w in t:
                print(' ✘ 漏れ: ft-pack-%02d に %s' % (i, w)); ng += 1
    for i in range(1, 5):
        t = io.open(os.path.join(OUTDIR, 'packs', 'gl-pack-%02d.jsonl' % i), encoding='utf-8').read()
        for w in ['Nthird', 'main1', 'trial_id', 'dprime', 'GL-A', 'GL-B', 'gl_arm']:
            if w in t:
                print(' ✘ 漏れ: gl-pack-%02d に %s' % (i, w)); ng += 1
    print('盲検の機械検査: 漏れ %d（GL の介入文引用は判定必要語のため対象外）' % ng)
    return 0 if ng == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
