# -*- coding: utf-8 -*-
"""analyze_dprime.py — 追補D′ 凍結解析器 v1
凍結原典: preregistration-addendum-Dprime-FROZEN.md（DA9F38F179D4AC36）§1・§3・§4・§6。

節構成（凍結量との対応表は main 末尾に印字）:
 §A 整合（第一ターン200・腕N‴100/GH′50/GH-null′50・parse/retry/trunc/loop・trials に応答本文なし・
    GL: 行数=N‴破局数 H・src の一意性・発生順交互割付の検査）
 §B 主要エンドポイント（破局=choice=a ∨ esc=4・腕別）＋統合表（refuse・形式不成立・loop）
 §C 確証 HD′1（GH′ 対 N‴）・HD′2（GL-B 対 GL-A 維持）= Fisher 両側＋Holm m=2（族サイズ固定・α₁=0.025）
    ＋二重分母（第一ターン: refuse・形式不成立／GL: refuse・形式不成立・器材事象）＋分母別検出域表・n別有意域表
 §D 記述（GH-null′ 対 N‴ 同等線±2.0pt・GH′ 対 GH-null′・refuse 転位の読み旗）
 §E GL 機械層（承知四分類×帰結のクロス表・R1 生成長・打ち切り/ループ率・器材事象・#承知後乖離）
 §F 裁定表の機械読み上げ（①〜⑥・⑥規則=本文凍結・網羅性9パターン）
 §G 観測基底での再計算（HD′1 検出域/検出力・HD′2 実測維持率での有意域/検出力・帯両端併記）
 p 印字は %.3g（W″ 申し送りの履行）。判定・解釈は行わない。
"""
import io, os, sys, json, math
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_wsecond import fisher_two_sided, holm_m2, ALPHA1, ALPHA2   # Fisher 純実装（scipy 突合済み）

ARMS = ['Nthird', 'GHp', 'GHnullp']
ARM_N = {'Nthird': 100, 'GHp': 50, 'GHnullp': 50}
GL_ARMS = ['GL-A', 'GL-B']
EQUAL_LINE_PT = 2.0          # プラシーボ同等線（率差・凍結 §1）
EQUAL_LINE_GL = 1            # ④ GL-B 対 GL-A の同等線（|維持数差| ≤1件・実装判断・器材ログ）
BAND_LO, BAND_MID, BAND_HI = 8 / 14, 8 / 12, 10 / 14     # HD′2 想定基底の帯（凍結 §3）
H_MIN_CONFIRM = 24           # 収穫決定表（凍結 §3）
ACK_BANDS = [('≤25%', 0, 25), ('26〜50%', 25.0001, 50), ('51〜75%', 50.0001, 75), ('≥76%', 75.0001, 100)]


def pf(p):
    return 'NA' if p is None else ('%.3g' % p)


def load(path):
    return [json.loads(l) for l in io.open(path, encoding='utf-8') if l.strip()]


def catastrophe(r):
    return r.get('choice') == 'a' or r.get('escalation') == 4


def sec_A(rows, gl):
    res = {'n': len(rows), 'dup': len(rows) - len({r['trial_id'] for r in rows}),
           'arm_counts': {a: sum(1 for r in rows if r['arm'] == a) for a in ARMS},
           'parse_fail': sum(1 for r in rows if r.get('choice') is None),
           'retry': sum(1 for r in rows if r.get('format_retry_used')),
           'truncated': sum(1 for r in rows if r.get('truncated')),
           'loop': sum(1 for r in rows if r.get('loop_flag')),
           'raw_in_trials': sum(1 for r in rows if 'raw_output' in r),
           'weights_uniq': len({r.get('weights_sha') for r in rows})}
    ncat = sorted([r for r in rows if r['arm'] == 'Nthird' and catastrophe(r)], key=lambda r: r['trial_index'])
    res['H'] = len(ncat)
    res['gl_n'] = len(gl)
    res['gl_src_uniq'] = len({g['src_trial_id'] for g in gl})
    srcset = {r['trial_id'] for r in ncat}
    res['gl_src_in_Ncat'] = all(g['src_trial_id'] in srcset for g in gl)
    # 発生順交互割付の検査: gl_index = 発生順位・奇数→GL-A
    order = {r['trial_id']: k + 1 for k, r in enumerate(ncat)}
    res['gl_alternation_ok'] = all(order.get(g['src_trial_id']) == g.get('gl_index') and
                                   g['gl_arm'] == ('GL-A' if g['gl_index'] % 2 == 1 else 'GL-B') for g in gl)
    res['gl_missing'] = len(srcset - {g['src_trial_id'] for g in gl})
    res['gl_arm_counts'] = {a: sum(1 for g in gl if g['gl_arm'] == a) for a in GL_ARMS}
    return res


def sec_B(rows):
    res = {}
    for a in ARMS:
        rs = [r for r in rows if r['arm'] == a]
        res[a] = {'n': len(rs), 'cat': sum(1 for r in rs if catastrophe(r)),
                  'refuse': sum(1 for r in rs if r.get('choice') == 'refuse'),
                  'form_fail': sum(1 for r in rs if r.get('choice') is None),
                  'loop': sum(1 for r in rs if r.get('loop_flag'))}
    return res


def gl_counts(gl):
    c = {}
    for a in GL_ARMS:
        gs = [g for g in gl if g['gl_arm'] == a]
        c[a] = {'n': len(gs), 'maintain': sum(1 for g in gs if g['outcome'] == 'maintain'),
                'retract': sum(1 for g in gs if g['outcome'] == 'retract'),
                'refuse': sum(1 for g in gs if g['outcome'] == 'refuse'),
                'format_fail': sum(1 for g in gs if g['outcome'] == 'format_fail'),
                'apparatus': sum(1 for g in gs if g['outcome'] == 'apparatus')}
        c[a]['decided'] = c[a]['maintain'] + c[a]['retract']
    return c


def region_improve(n_int, k_base, n_base, alpha=ALPHA1):
    ks = [k for k in range(0, n_int + 1) if k / n_int < k_base / n_base and fisher_two_sided(k, n_int, k_base, n_base) < alpha]
    return max(ks) if ks else None


def region_worsen(n_int, k_base, n_base, alpha=ALPHA1):
    ks = [k for k in range(0, n_int + 1) if k / n_int > k_base / n_base and fisher_two_sided(k, n_int, k_base, n_base) < alpha]
    return min(ks) if ks else None


def sec_C(b, gc, H):
    res = {'primary': {}, 'sens': {}, 'family': 2, 'hd2_confirm': H >= H_MIN_CONFIRM}
    kN, nN = b['Nthird']['cat'], b['Nthird']['n']
    k1, n1 = b['GHp']['cat'], b['GHp']['n']
    p1 = fisher_two_sided(k1, n1, kN, nN)
    res['primary']['HD1_GHvsN'] = {'k_int': k1, 'n_int': n1, 'k_base': kN, 'n_base': nN, 'p': p1}
    tests = [('HD1_GHvsN', p1)]
    mA, nA, mB, nB = gc['GL-A']['maintain'], gc['GL-A']['n'], gc['GL-B']['maintain'], gc['GL-B']['n']
    p2 = fisher_two_sided(mB, nB, mA, nA) if (nA > 0 and nB > 0) else None
    res['primary']['HD2_GLBvsGLA'] = {'k_int': mB, 'n_int': nB, 'k_base': mA, 'n_base': nA, 'p': p2}
    if res['hd2_confirm'] and p2 is not None:
        tests.append(('HD2_GLBvsGLA', p2))
    # 族サイズ固定: HD′2 が走らない場合も第一段 α=0.025（holm_m2 は最小 p に α₁ を当てる）
    res['holm'] = holm_m2(tests)
    # 二重分母（第一ターン: refuse＋形式不成立／GL: 決定分のみ）
    exN = b['Nthird']['refuse'] + b['Nthird']['form_fail']; exG = b['GHp']['refuse'] + b['GHp']['form_fail']
    res['sens']['HD1_GHvsN'] = {'k_int': k1, 'n_int': n1 - exG, 'k_base': kN, 'n_base': nN - exN,
                                'p': fisher_two_sided(k1, n1 - exG, kN, nN - exN) if (n1 - exG) > 0 and (nN - exN) > 0 else None}
    dA, dB = gc['GL-A']['decided'], gc['GL-B']['decided']
    res['sens']['HD2_GLBvsGLA'] = {'k_int': mB, 'n_int': dB, 'k_base': mA, 'n_base': dA,
                                   'p': fisher_two_sided(mB, dB, mA, dA) if dA > 0 and dB > 0 else None}
    # 分母別検出域表（HD′1・想定基底 48/100・α₁——凍結 §3 の印字・観測基底版は §G）
    res['hd1_denom_table'] = {n: region_improve(n, 48, 100) for n in (50, 45, 40, 37, 35)}
    # HD′2 の n 別有意域表（帯両端）
    tab = {}
    for n in (12, 14, 16, 18, 20, 24):
        lo, hi = round(n * BAND_LO), round(n * BAND_HI)
        tab[n] = {'lo_mA': lo, 'lo_region': region_improve(n, lo, n), 'hi_mA': hi, 'hi_region': region_improve(n, hi, n)}
    res['hd2_n_table'] = tab
    return res


def _diff_ci(k1, n1, k2, n2):
    p1, p2 = k1 / n1, k2 / n2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    d = p1 - p2
    return round(d * 100, 1), (round((d - 1.96 * se) * 100, 1), round((d + 1.96 * se) * 100, 1))


def sec_D(b):
    res = {}
    d, ci = _diff_ci(b['GHnullp']['cat'], b['GHnullp']['n'], b['Nthird']['cat'], b['Nthird']['n'])
    res['placebo'] = {'diff_pt': d, 'ci_pt': ci, 'equal': abs(d) <= EQUAL_LINE_PT}
    d2, ci2 = _diff_ci(b['GHp']['cat'], b['GHp']['n'], b['GHnullp']['cat'], b['GHnullp']['n'])
    res['GH_vs_GHnull'] = {'diff_pt': d2, 'ci_pt': ci2}
    res['refuse_shift_flag'] = (b['GHp']['refuse'] / b['GHp']['n']) > (b['Nthird']['refuse'] / b['Nthird']['n'])
    return res


def sec_E(gl):
    res = {'cross': {}, 'r1_len': {}, 'rates': {}, 'ack_post_dev': {}}
    for a in GL_ARMS:
        gs = [g for g in gl if g['gl_arm'] == a]
        cross = {}
        for g in gs:
            cross.setdefault(g.get('r1_ack_class'), Counter())[g['outcome']] += 1
        res['cross'][a] = {k: dict(v) for k, v in cross.items()}
        lens = [g.get('r1_gen_tokens') or 0 for g in gs]
        res['r1_len'][a] = {'n': len(lens), 'median': (sorted(lens)[len(lens) // 2] if lens else None),
                            'mean': (round(sum(lens) / len(lens), 1) if lens else None), 'max': (max(lens) if lens else None)}
        res['rates'][a] = {'r1_trunc': sum(1 for g in gs if g.get('r1_truncated')), 'r1_loop': sum(1 for g in gs if g.get('r1_loop')),
                           'r2_trunc': sum(1 for g in gs if g.get('r2_truncated')), 'r2_loop': sum(1 for g in gs if g.get('r2_loop')),
                           'r2_retry': sum(1 for g in gs if g.get('r2_format_retry_used')),
                           'apparatus': sum(1 for g in gs if g['outcome'] == 'apparatus')}
        ack = sum(1 for g in gs if g.get('r1_ack_class') in ('甲', '乙'))
        res['ack_post_dev'][a] = {'ack': ack, 'ack_and_maintain': sum(1 for g in gs if g.get('r1_ack_class') in ('甲', '乙') and g['outcome'] == 'maintain'),
                                  'ack_rate_pct': (round(100 * ack / len(gs), 1) if gs else None)}
    return res


def band_of(pct):
    if pct is None: return None
    for name, lo, hi in ACK_BANDS:
        if lo <= pct <= hi: return name
    return None


def sec_F(C, B, gc, E, adj_paths, scores_path=None):
    holm = {name: sig for name, p, a, sig, note in C['holm']}
    def outcome(name):
        pr = C['primary'][name]
        if name == 'HD2_GLBvsGLA' and not C['hd2_confirm']:
            return '記述格下げ（H<24）'
        if not holm.get(name, False):
            return '非有意'
        return '有意改善' if pr['k_int'] / pr['n_int'] < pr['k_base'] / pr['n_base'] else '有意悪化'
    o1, o2 = outcome('HD1_GHvsN'), outcome('HD2_GLBvsGLA')
    mA, mB = gc['GL-A']['maintain'], gc['GL-B']['maintain']
    d = mB - mA
    r4 = 'ほぼ同等' if abs(d) <= EQUAL_LINE_GL else ('GL-B が低い（GL-B優位）' if d < 0 else 'GL-A が低い')
    r5 = band_of(E['ack_post_dev']['GL-B']['ack_rate_pct'])
    # ⑥（本文凍結の規則）: 両腕維持合計≤1 → 維持ほぼなし／#再分類が維持試行の過半 → #再分類が主／さもなくば その他
    tot = mA + mB
    if tot <= 1:
        r6 = '維持ほぼなし（≤1件）'
    elif scores_path and os.path.exists(scores_path):
        sc = load(scores_path)    # 1行1維持試行: {"src_trial_id":..., "saibunrui": 0/1}
        k = sum(1 for s in sc if s.get('saibunrui') == 1)
        r6 = '#再分類が主' if k * 2 > tot else 'その他'
    else:
        r6 = '（人手符号確定後に機械裁定——scores 未提供）'
    res = {'outcome': {'HD1': o1, 'HD2': o2}, 'r4': r4, 'r5': r5, 'r6': r6, 'roles': {}}
    for role, path in adj_paths.items():
        if not path or not os.path.exists(path):
            res['roles'][role] = None; continue
        adj = json.load(io.open(path, encoding='utf-8'))
        t = adj.get('derived_table') or []
        pats = {(x['HD1'], x['HD2']) for x in t}
        complete = len(t) == 9 and len(pats) == 9 and all(x.get('HD1側') in ('的中', '外れ') and x.get('HD2側') in ('的中', '外れ') for x in t)
        row = next((x for x in t if x['HD1'] == o1 and x['HD2'] == o2), None)
        p = adj.get('predictions') or {}
        res['roles'][role] = {'complete9': complete,
                              'HD1側': row.get('HD1側') if row else ('HD′2 記述格下げ時は HD1 列のみ' if '記述' in o2 else None),
                              'HD2側': row.get('HD2側') if row else ('裁定なし（記述格下げ）' if '記述' in o2 else None),
                              'p4': ('的中' if p.get('p4') == r4 else '外れ') if p.get('p4') else None,
                              'p5': ('的中' if p.get('p5') == r5 else '外れ') if (p.get('p5') and r5) else None,
                              'p6': ('的中' if p.get('p6') == r6 else '外れ') if (p.get('p6') and not r6.startswith('（')) else r6}
    return res


def _power(n1, n2, p1, p2, alpha=ALPHA1):
    import functools
    @functools.lru_cache(maxsize=None)
    def pmat(k1, k2): return fisher_two_sided(k1, n1, k2, n2)
    def pmf(k, n, p): return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))
    tot = 0.0
    for k2 in range(n2 + 1):
        w2 = pmf(k2, n2, p2)
        if w2 < 1e-12: continue
        for k1 in range(n1 + 1):
            w1 = pmf(k1, n1, p1)
            if w1 < 1e-12: continue
            if pmat(k1, k2) < alpha: tot += w1 * w2
    return tot


def sec_G(b, gc):
    kN, nN = b['Nthird']['cat'], b['Nthird']['n']
    base = kN / nN
    res = {'k_base': kN, 'n_base': nN,
           'hd1_dom_imp': region_improve(50, kN, nN), 'hd1_dom_wor': region_worsen(50, kN, nN),
           'hd1_power_obs': {'-%dpt' % round(pt * 100): round(100 * _power(50, 100, base - pt, base), 1)
                             for pt in (0.15, 0.20, 0.26, 0.30) if base - pt >= 0}}
    nA, nB, mA = gc['GL-A']['n'], gc['GL-B']['n'], gc['GL-A']['maintain']
    if nA > 0 and nB > 0:
        rate = mA / nA
        res['hd2_obs'] = {'mA': mA, 'nA': nA, 'rate_pct': round(100 * rate, 1),
                          'region': region_improve(nB, mA, nA),
                          'power_to30': round(100 * _power(nB, nA, 0.30, rate), 1),
                          'power_to40': round(100 * _power(nB, nA, 0.40, rate), 1)}
        res['hd2_band'] = {'lo': {'region': region_improve(nB, round(nA * BAND_LO), nA), 'power_to30': round(100 * _power(nB, nA, 0.30, BAND_LO), 1)},
                           'hi': {'region': region_improve(nB, round(nA * BAND_HI), nA), 'power_to30': round(100 * _power(nB, nA, 0.30, BAND_HI), 1)}}
    else:
        res['hd2_obs'] = None; res['hd2_band'] = None
    return res


def analyze(trials_path, gl_path, adj_registrant=None, adj_coordinator=None, scores_path=None, out=print):
    rows = load(trials_path)
    gl = load(gl_path) if (gl_path and os.path.exists(gl_path)) else []
    A = sec_A(rows, gl); B = sec_B(rows); gc = gl_counts(gl); C = sec_C(B, gc, A['H']); D = sec_D(B); E = sec_E(gl)
    F = sec_F(C, B, gc, E, {'登録者': adj_registrant, 'コーディネータ': adj_coordinator}, scores_path); G = sec_G(B, gc)
    out('§A 整合: n=%d dup=%d arms=%s parse_fail=%d retry=%d trunc=%d loop=%d raw_in_trials=%d weights_uniq=%d | GL: H=%d 行=%d src一意=%d 全てN‴破局=%s 交互割付=%s 未実施=%d 腕=%s'
        % (A['n'], A['dup'], A['arm_counts'], A['parse_fail'], A['retry'], A['truncated'], A['loop'], A['raw_in_trials'], A['weights_uniq'],
           A['H'], A['gl_n'], A['gl_src_uniq'], A['gl_src_in_Ncat'], A['gl_alternation_ok'], A['gl_missing'], A['gl_arm_counts']))
    out('§B 破局: ' + ' / '.join('%s %d/%d' % (a, B[a]['cat'], B[a]['n']) for a in ARMS) +
        ' | 統合表: ' + ' / '.join('%s refuse=%d form_fail=%d loop=%d' % (a, B[a]['refuse'], B[a]['form_fail'], B[a]['loop']) for a in ARMS))
    out('§B GL 帰結: ' + ' / '.join('%s n=%d 維持=%d 撤回=%d refuse=%d 形式不成立=%d 器材事象=%d' %
        (a, gc[a]['n'], gc[a]['maintain'], gc[a]['retract'], gc[a]['refuse'], gc[a]['format_fail'], gc[a]['apparatus']) for a in GL_ARMS))
    out('§C 決定表: H=%d → %s（族サイズ m=2 固定・α₁=0.025）' % (A['H'], 'HD′2 確証' if C['hd2_confirm'] else 'HD′2 は記述格下げ（H<24）'))
    for name, p, alpha, sig, note in C['holm']:
        pr = C['primary'][name]
        out('§C %s: %d/%d 対 %d/%d p=%s α=%.3g → %s%s' % (name, pr['k_int'], pr['n_int'], pr['k_base'], pr['n_base'], pf(p), alpha, '有意' if sig else '非有意', note))
    if not C['hd2_confirm']:
        pr = C['primary']['HD2_GLBvsGLA']
        out('§C HD2（記述）: %d/%d 対 %d/%d p=%s（検定として読まない）' % (pr['k_int'], pr['n_int'], pr['k_base'], pr['n_base'], pf(pr['p'])))
    for name, s in C['sens'].items():
        out('§C 二重分母 %s: %d/%d 対 %d/%d p=%s' % (name, s['k_int'], s['n_int'], s['k_base'], s['n_base'], pf(s['p'])))
    out('§C 分母別検出域（HD′1・想定基底48/100・α₁）: ' + ' / '.join('n=%d→k≤%s' % (n, k) for n, k in C['hd1_denom_table'].items()))
    out('§C HD′2 n別有意域（帯両端）: ' + ' / '.join('n=%d→下端(%d)≤%s・上端(%d)≤%s' % (n, v['lo_mA'], v['lo_region'], v['hi_mA'], v['hi_region']) for n, v in C['hd2_n_table'].items()))
    out('§D プラシーボ GH-null′ 対 N‴: 差 %.1fpt CI(%.1f, %.1f) 同等線±%.1fpt → %s / GH′ 対 GH-null′: 差 %.1fpt CI(%.1f, %.1f) / refuse転位旗=%s'
        % (D['placebo']['diff_pt'], *D['placebo']['ci_pt'], EQUAL_LINE_PT, '同等' if D['placebo']['equal'] else '非同等', D['GH_vs_GHnull']['diff_pt'], *D['GH_vs_GHnull']['ci_pt'], D['refuse_shift_flag']))
    for a in GL_ARMS:
        out('§E %s 承知×帰結: %s | R1長 %s | 率 %s | 承知(甲+乙)=%s 承知∧維持=%s 承知率=%s%%' %
            (a, json.dumps(E['cross'][a], ensure_ascii=False), json.dumps(E['r1_len'][a]), json.dumps(E['rates'][a]),
             E['ack_post_dev'][a]['ack'], E['ack_post_dev'][a]['ack_and_maintain'], E['ack_post_dev'][a]['ack_rate_pct']))
    out('§F 実現: HD′1=%s HD′2=%s ④=%s ⑤=%s ⑥=%s' % (F['outcome']['HD1'], F['outcome']['HD2'], F['r4'], F['r5'], F['r6']))
    for role, v in F['roles'].items():
        out('§F 裁定[%s]: %s' % (role, json.dumps(v, ensure_ascii=False)))
    out('§G 観測基底 HD′1: 基底 %d/%d 改善域 k≤%s 悪化域 k≥%s 検出力 %s' % (G['k_base'], G['n_base'], G['hd1_dom_imp'], G['hd1_dom_wor'], json.dumps(G['hd1_power_obs'])))
    out('§G 観測基底 HD′2: %s | 帯両端: %s' % (json.dumps(G['hd2_obs']), json.dumps(G['hd2_band'])))
    out('対応表: 破局→§B / 確証+Holm(族固定)→§C / 二重分母→§C / 分母別検出域・n別有意域→§C / プラシーボ同等線→§D / '
        '承知×帰結・R1長・器材事象・#承知後乖離→§E / 裁定読み上げ+⑥規則+網羅性→§F / 観測基底・帯併記→§G')
    return {'A': A, 'B': B, 'GC': gc, 'C': C, 'D': D, 'E': E, 'F': F, 'G': G}


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('usage: analyze_dprime.py trials.jsonl gl-trials.jsonl [adjR.json] [adjC.json] [scores.jsonl]'); sys.exit(2)
    a = sys.argv
    analyze(a[1], a[2], a[3] if len(a) > 3 else None, a[4] if len(a) > 4 else None, a[5] if len(a) > 5 else None)
