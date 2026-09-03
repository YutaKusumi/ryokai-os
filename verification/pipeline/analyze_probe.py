# -*- coding: utf-8 -*-
"""analyze_probe.py —— 追補E′ 理解プローブ（§4.5(5)）の機械集計。凍結 ⑥ §B/§C を参照実装 probe_matcher.py（5C03C89A300E43DF）で適用。
記述のみ・検定なし。使い方: python analyze_probe.py <trials.jsonl> <raw.jsonl>
"""
import sys, io, json, hashlib, collections, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe_matcher as pm
ARMS = ['BP', 'BP-sec', 'BP-scr', 'BP-sec-scr', 'N', 'Onull', 'O']
P14 = ['P1.1','P1.2','P1.3','P1.4','P1.5','P1.6','P2.0','P2.1','P2.2','P3.1','P3.2','P3.3','P4.1','P4.2']
PT = ['P~1.1', 'P~1.6']
sha16 = lambda p: hashlib.sha256(io.open(p, 'rb').read().replace(b'\r\n', b'\n')).hexdigest()[:16].upper()

def load(p):
    rows, broken = [], 0
    for l in io.open(p, encoding='utf-8'):
        if not l.strip(): continue
        try: rows.append(json.loads(l))
        except Exception: broken += 1
    return rows, broken

def main(tp, rp):
    T, tb = load(tp); R, rb = load(rp)
    print('== trials %s SHA(LF) %s rows %d broken %d / raw %s SHA(LF) %s rows %d broken %d' % (os.path.basename(tp), sha16(tp), len(T), tb, os.path.basename(rp), sha16(rp), len(R), rb))
    ids = [r['trial_id'] for r in T]; print('   uniq %s / trials∩raw %d / matcher SHA(LF) %s' % (len(ids) == len(set(ids)), len(set(ids) & {r['trial_id'] for r in R}), sha16(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'probe_matcher.py'))))
    # 凍結照合（各行）
    bad = [(r['trial_id'], k) for r in T for k, v in (('probe_doc_sha', '818869A935FC2AE1'), ('matcher_sha', '5C03C89A300E43DF'), ('system_sha', '51E7C671AF8A3371'), ('max_new_tokens', 1024), ('model', 'Qwen/Qwen3-30B-A3B-Instruct-2507'), ('quant', '4bit-nf4'), ('sampling', {'do_sample': True, 'temperature': 0.7, 'top_p': 0.9})) if r.get(k) != v]
    print('   凍結照合: %s' % ('全行一致' if not bad else 'NG %d 例 %s' % (len(bad), bad[:3])))
    rawmap = {r['trial_id']: r for r in R}
    by = collections.defaultdict(list)
    for t in T:
        r = rawmap[t['trial_id']]; ok, items, res = pm.match_output(r['raw_output'])
        # ⑥ B-2 の形式判定と boot の記録が一致するか
        by[t['arm']].append({'id': t['trial_id'], 'ok': ok, 'ok_boot': t['format_ok'], 'n': len(items), 'res': res, 'trunc': t['truncated'], 'loop': t['loop_flag'], 'gen': t['gen_tokens'], 'sec': t['seconds'],
                             'both': [p for p in ('P1.1', 'P1.6') if res[p] and res['P~' + p[1:]]]})
    mism = sum(1 for a in by for x in by[a] if x['ok'] != x['ok_boot']); print('   形式判定（参照実装 vs boot 記録）不一致: %d' % mism)
    print('\n== 腕別 概況（n=10）')
    print('   %-10s %4s %4s %5s %5s %6s %6s' % ('腕', '形式OK', '項目中央', 'trunc', 'loop', 'gen中央', 'sec中央'))
    for a in ARMS:
        v = by.get(a, [])
        if not v: continue
        med = lambda k: sorted(x[k] for x in v)[len(v) // 2]
        print('   %-10s %4d %6d %5d %5d %6d %6.0f' % (a, sum(x['ok'] for x in v), med('n'), sum(x['trunc'] for x in v), sum(x['loop'] for x in v), med('gen'), med('sec')))
    print('\n== 再生率（腕 × 命題・分母 10・形式不成立は再生なし）')
    print('   %-10s ' % '腕' + ' '.join('%5s' % p for p in P14) + '  | ' + ' '.join('%5s' % p for p in PT) + ' 両立')
    for a in ARMS:
        v = by.get(a, [])
        if not v: continue
        cnt = lambda p: sum(1 for x in v if x['res'][p])
        print('   %-10s ' % a + ' '.join('%5d' % cnt(p) for p in P14) + '  | ' + ' '.join('%5d' % cnt(p) for p in PT) + ' %4d' % sum(1 for x in v if x['both']))
    print('\n   注記（凍結 ⑥ (iii)-4・C-6）: P1.2 は一語彙素（共／共同）で立つ／P2.0 は前提命題／N 腕の値は前置きなしの偶発基底／Onull・O 腕の値は BP 命題表に対する偽陽性基底。')
    # 逐語行分割の記述（smoke 観察の追跡）: 各命題の群が複数行に分かれた件数は出さない（凍結外）。項目数の分布のみ
    print('   項目数分布（全腕）: %s' % dict(sorted(collections.Counter(x['n'] for a in by for x in by[a]).items())))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
