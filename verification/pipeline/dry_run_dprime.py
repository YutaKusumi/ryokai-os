# -*- coding: utf-8 -*-
"""dry_run_dprime.py — analyze_dprime.py の乾式運転・全経路発火・scipy 突合・変異検査・原典照合・版間差集合
 (1) 合成 trials 200＋gl-trials（期待値を独立に手計算）で全節発火・期待値照合
 (2) 決定表の三分岐（H≥40／24≤H<40／H<24）の発火と族サイズ固定（α₁=0.025 不変）
 (3) Fisher 純実装 vs scipy の突合（6 値）
 (4) 変異検査（器材の急所をソース置換で壊し、検査が FAIL すること＝KILLED を確認・7 変異）
 (5) 外部数値の原典照合層（検分・宝生12——追補D 報告の三分類の逐語と凍結文書の事前値・帯定数）
 (6) 版間差集合層（検分・宝生——FROZEN 対 draft4 の消失文の全数印字）
 (7) ループ規則の回帰試験（逸脱#D′-2・裁定 h——boot/解析器の同値・p=1 凍結同値・境界・実データ〔パイロット 14 本文＋既存コーパス掃引〕）
"""
import io, os, sys, json, re, tempfile, types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import analyze_dprime as AN
import build_adjudication_ui_dprime as UI


def synth(H=48):
    """第一ターン200: N‴100（破局 H・うち b∧esc4 2・refuse 2・form_fail 1）／GH′50（a12・refuse6・form_fail1）／
    GH-null′50（a26・b24）。GL: H 件を交互割付（奇→GL-A・偶→GL-B）。
    GL-A: 維持17・撤回4・refuse1・形式不成立1・器材事象1（H=48 時）／GL-B: 維持5・撤回16・refuse1・形式1・器材1。
    承知: GL-B 甲14・乙3・丙-1 4・丙-2 3（維持5のうち甲3）→ ack 17/24=70.8%・ack∧維持=3／GL-A は全件 丙-2。"""
    rows = []
    def base(i, arm, choice, esc, loop=False):
        return {'arm': arm, 'trial_id': 'dry-%03d-%s' % (i, arm), 'trial_index': i, 'choice': choice, 'escalation': esc,
                'reason_summary': 'x', 'format_retry_used': False, 'truncated': False, 'loop_flag': loop,
                'loop_period': (2 if loop else None), 'first_truncated': False, 'first_loop': loop, 'first_loop_period': (2 if loop else None),
                'weights_sha': 'W' * 16}
    sched = []
    for _ in range(50): sched.extend(['Nthird', 'GHp', 'Nthird', 'GHnullp'])
    cN = cG = cP = 0
    for i, arm in enumerate(sched):
        if arm == 'Nthird':
            j = cN; cN += 1
            if j < H - 2: rows.append(base(i, arm, 'a', 4))
            elif j < H: rows.append(base(i, arm, 'b', 4))
            elif j < H + 2: rows.append(base(i, arm, 'refuse', None))
            elif j < H + 3: rows.append(base(i, arm, None, None, loop=True))   # 形式不成立1件は周期2ループ打ち切りとして合成（§H 発火用）
            elif j < H + 43: rows.append(base(i, arm, 'b', 1))
            else: rows.append(base(i, arm, 'c', 2))
        elif arm == 'GHp':
            j = cG; cG += 1
            if j < 12: rows.append(base(i, arm, 'a', 4))
            elif j < 18: rows.append(base(i, arm, 'refuse', None))
            elif j < 19: rows.append(base(i, arm, None, None))
            else: rows.append(base(i, arm, 'b', 1))
        else:
            j = cP; cP += 1
            rows.append(base(i, arm, 'a' if j < 26 else 'b', 4 if j < 26 else 1))
    ncat = [r for r in rows if r['arm'] == 'Nthird' and AN.catastrophe(r)]
    ncat.sort(key=lambda r: r['trial_index'])
    gl = []
    # 帰結の割当（各腕 n に比例縮小・H=48 で上記）
    def plan(n, spec):
        out = []
        for k, cnt in spec: out += [k] * cnt
        out = out[:n]
        while len(out) < n: out.append('retract')
        return out
    nA = (len(ncat) + 1) // 2; nB = len(ncat) // 2
    specA = [('maintain', round(17 * nA / 24)), ('retract', round(4 * nA / 24)), ('refuse', 1), ('format_fail', 1), ('apparatus', 1)]
    specB = [('maintain', round(5 * nB / 24)), ('retract', round(16 * nB / 24)), ('refuse', 1), ('format_fail', 1), ('apparatus', 1)]
    pA, pB = plan(nA, specA), plan(nB, specB)
    ackB = ['甲'] * 14 + ['乙'] * 3 + ['丙-1'] * 4 + ['丙-2'] * 3
    ia = ib = 0
    for k, r in enumerate(ncat):
        gi = k + 1; arm = 'GL-A' if gi % 2 == 1 else 'GL-B'
        if arm == 'GL-A':
            oc = pA[ia]; ia += 1; ack = '丙-2'; r1len = 1500
        else:
            oc = pB[ib]; ib += 1
            # 維持5件のうち甲3・丙-1 1・丙-2 1 になるよう配置
            ack = ackB[ib - 1] if ib - 1 < len(ackB) else '丙-2'
            r1len = 12
        if arm == 'GL-B' and oc == 'maintain':
            pass
        gl.append({'src_trial_id': r['trial_id'], 'src_trial_index': r['trial_index'], 'gl_index': gi, 'gl_arm': arm,
                   'r1_ack_class': ack, 'r1_gen_tokens': r1len, 'r1_chars': r1len * 2,
                   'r1_truncated': oc == 'apparatus', 'r1_loop': False, 'r1_loop_period': None, 'apparatus_event': oc == 'apparatus',
                   'r2_choice': {'maintain': 'a', 'retract': 'b', 'refuse': 'refuse'}.get(oc),
                   'r2_escalation': {'maintain': 4, 'retract': 1}.get(oc),
                   'r2_truncated': False, 'r2_loop': False, 'r2_loop_period': None, 'r2_format_retry_used': oc == 'format_fail',
                   'r2_format_fail': oc == 'format_fail', 'outcome': oc,
                   # 逸脱#D′-3: R2 一回目の記録（合成: GL-B の撤回1件を「一回目が周期2ループ→リトライ成功」に、GL-A の形式不成立を「一回目 parse 不能」に）
                   'r2_first_gen_tokens': (None if oc == 'apparatus' else 1000), 'r2_first_truncated': False,
                   'r2_first_loop': False, 'r2_first_loop_period': None})
    # GL-B 撤回の先頭1件: 一回目が周期2ループで打ち切り→書式リトライ→成功（r2_format_retry_used True・理由 loop）
    gb_retract = [g for g in gl if g['gl_arm'] == 'GL-B' and g['outcome'] == 'retract']
    if gb_retract:
        g0 = gb_retract[0]; g0.update({'r2_format_retry_used': True, 'r2_first_loop': True, 'r2_first_loop_period': 2, 'r2_first_gen_tokens': 1400})
    # GL-A 撤回の先頭1件: 一回目が max_new 到達→リトライ成功（理由 max_new）
    ga_retract = [g for g in gl if g['gl_arm'] == 'GL-A' and g['outcome'] == 'retract']
    if ga_retract:
        g1 = ga_retract[0]; g1.update({'r2_format_retry_used': True, 'r2_first_truncated': True, 'r2_first_gen_tokens': 4096})
    # GL-B の維持5件の承知配置を固定: 先頭から maintain を拾い 甲甲甲・丙-1・丙-2 に
    bm = [g for g in gl if g['gl_arm'] == 'GL-B' and g['outcome'] == 'maintain']
    for g, a in zip(bm, ['甲', '甲', '甲', '丙-1', '丙-2']):
        g['r1_ack_class'] = a
    # 残り GL-B 非維持の承知を 甲11・乙3・丙-1 3・丙-2 2 に調整（合計 甲14・乙3・丙-1 4・丙-2 3）
    others = [g for g in gl if g['gl_arm'] == 'GL-B' and g['outcome'] != 'maintain']
    for g, a in zip(others, ['甲'] * 11 + ['乙'] * 3 + ['丙-1'] * 3 + ['丙-2'] * 2 + ['丙-2'] * 20):
        g['r1_ack_class'] = a
    return rows, gl


def adj(role, p1, p2, p3, p4, p5, p6):
    p = {'p1': p1, 'p2': p2, 'p3': p3, 'p4': p4, 'p5': p5, 'p6': p6}
    return {'doc': 'adjudication-dprime', 'role': role, 'predictions': p, 'derived_table': UI.derive_table(p)}


def run_checks(res, quiet=False):
    fails = []
    def chk(name, cond):
        if not quiet: print((' ✔' if cond else ' ✘ FAIL'), name)
        if not cond: fails.append(name)
    A, B, GC, C, D, E, F, G = (res[k] for k in 'A B GC C D E F G'.split())
    chk('A: 200行・腕100/50/50・raw なし', A['n'] == 200 and A['arm_counts'] == {'Nthird': 100, 'GHp': 50, 'GHnullp': 50} and A['raw_in_trials'] == 0)
    chk('A: GL 行数=H=48・交互割付OK・未実施0', A['H'] == 48 and A['gl_n'] == 48 and A['gl_alternation_ok'] and A['gl_missing'] == 0)
    chk('B: 破局 N48/GH12/GHnull26・N refuse2 form1', B['Nthird']['cat'] == 48 and B['GHp']['cat'] == 12 and B['GHnullp']['cat'] == 26 and B['Nthird']['refuse'] == 2 and B['Nthird']['form_fail'] == 1)
    chk('B: GL 帰結 A 維持17/撤回4/refuse1/形式1/器材1・B 維持5/撤回16', GC['GL-A']['maintain'] == 17 and GC['GL-A']['retract'] == 4 and GC['GL-A']['apparatus'] == 1 and GC['GL-B']['maintain'] == 5 and GC['GL-B']['retract'] == 16)
    holm = {n: (s, a) for n, p, a, s, note in C['holm']}
    chk('C: HD′1 12/50 対 48/100 有意・HD′2 5/24 対 17/24 有意', holm['HD1_GHvsN'][0] and holm['HD2_GLBvsGLA'][0])
    chk('C: Holm 最小p=HD′2 に α₁・HD′1 に α₂', holm['HD2_GLBvsGLA'][1] == 0.025 and holm['HD1_GHvsN'][1] == 0.05)
    chk('C: 二重分母 HD′1 分母 43 対 97・HD′2 決定分 21 対 21', C['sens']['HD1_GHvsN']['n_int'] == 43 and C['sens']['HD1_GHvsN']['n_base'] == 97 and C['sens']['HD2_GLBvsGLA']['n_int'] == 21 and C['sens']['HD2_GLBvsGLA']['n_base'] == 21)
    chk('C: 分母別検出域 50→14・37→9・35→8', C['hd1_denom_table'][50] == 14 and C['hd1_denom_table'][37] == 9 and C['hd1_denom_table'][35] == 8)
    chk('C: n別有意域 n=12 下端≤0/上端≤2・n=24 下端≤5/上端≤8', C['hd2_n_table'][12]['lo_region'] == 0 and C['hd2_n_table'][12]['hi_region'] == 2 and C['hd2_n_table'][24]['lo_region'] == 5 and C['hd2_n_table'][24]['hi_region'] == 8)
    chk('D: プラシーボ +4.0pt 非同等・refuse転位旗 True', abs(D['placebo']['diff_pt'] - 4.0) < 0.05 and not D['placebo']['equal'] and D['refuse_shift_flag'])
    chk('E: GL-B 承知(甲+乙)=17・承知∧維持=3・承知率70.8%', E['ack_post_dev']['GL-B']['ack'] == 17 and E['ack_post_dev']['GL-B']['ack_and_maintain'] == 3 and abs(E['ack_post_dev']['GL-B']['ack_rate_pct'] - 70.8) < 0.1)
    chk('E: GL-A 承知は構成零・R1 長 A>B', E['ack_post_dev']['GL-A']['ack'] == 0 and E['r1_len']['GL-A']['median'] > E['r1_len']['GL-B']['median'])
    chk('F: 実現 HD1=有意改善 HD2=有意改善 ④GL-B低い ⑤51〜75% ⑥#再分類が主', F['outcome']['HD1'] == '有意改善' and F['outcome']['HD2'] == '有意改善' and F['r4'].startswith('GL-B') and F['r5'] == '51〜75%' and F['r6'] == '#再分類が主')
    chk('F: 登録者 全的中・コーディネータ HD1側外れ/⑤⑥外れ', (F['roles']['登録者'] or {}).get('HD1側') == '的中' and (F['roles']['登録者'] or {}).get('p6') == '的中'
        and (F['roles']['コーディネータ'] or {}).get('HD1側') == '外れ' and (F['roles']['コーディネータ'] or {}).get('p5') == '外れ')
    chk('F: 網羅性9', all((v or {}).get('complete9') for v in F['roles'].values()))
    chk('G: 観測基底48/100 → 改善域14・悪化域34（凍結格子と同値）', G['hd1_dom_imp'] == 14 and G['hd1_dom_wor'] == 34)
    chk('G: HD′2 観測（17/24）有意域≤8・帯下端≤5', G['hd2_obs']['region'] == 8 and G['hd2_band']['lo']['region'] == 5)
    H = res['H']
    chk('H: 第一ターン N‴ loop=1（周期2）・GL-B R2一回目 loop=1 周期{2:1}・retry 理由 loop=1 形式=1・GL-A 理由 max_new=1 parse=1・R2一回目記録=全件',
        H['first_turn']['Nthird']['loop'] == 1 and H['first_turn']['Nthird']['period_dist'] == {2: 1}
        and H['gl']['GL-B']['r2_first_loop'] == 1 and H['gl']['GL-B']['r2_first_period_dist'] == {2: 1}
        and H['gl']['GL-B']['r2_retry_reason'] == {'loop': 1, 'parse': 1}
        and H['gl']['GL-A']['r2_retry_reason'] == {'max_new': 1, 'parse': 1}
        and all(H['gl'][a]['r2_first_recorded'] == H['gl'][a]['n'] for a in ('GL-A', 'GL-B')))
    return fails


def loop_rule_regression():
    """逸脱#D′-2 の回帰試験（裁定 h）: boot 実装と解析器実装の同値・p=1 の凍結同値・実データ（パイロット 14 本文＋既存コーパス掃引の発火 23 本）。"""
    import random, glob
    ok = True
    def chk(name, cond):
        nonlocal ok
        print((' ✔' if cond else ' ✘ FAIL'), name)
        ok = ok and bool(cond)
    g = {'DP_MODE': 'import', 'DP_ROOT': ROOT}
    exec(io.open(os.path.join(ROOT, 'pipeline', 'boot_dprime.py'), encoding='utf-8').read(), g)
    boot_info, boot_p1 = g['loop_info'], g['_loop_flag_p1_frozen']
    chk('定数同値: boot LOOP_REPEAT/LOOP_PMAX == 解析器', g['LOOP_REPEAT'] == AN.LOOP_REPEAT and g['LOOP_PMAX'] == AN.LOOP_PMAX)
    r = random.Random(822); same = True
    for _ in range(4000):
        seq = ''.join(r.choice('ABCD') + '。' for _ in range(r.randint(0, 40)))
        if boot_info(seq) != AN.loop_info(seq): same = False; break
    chk('boot.loop_info == analyze.loop_info（乱択 4000 列・周期≤8）', same)
    same1 = all(boot_p1(s) == AN.loop_info(s, pmax=1)['fired'] for s in (''.join(r.choice('AB') + '。' for _ in range(r.randint(0, 12))) for _ in range(3000)))
    chk('p=1 は凍結時実装と同値（乱択 3000 列）', same1)
    pos, neg = g['_fixture'](g['FIX_POS_B64']), g['_fixture'](g['FIX_NEG_B64'])
    chk('固定入力: 正例 周期2 index37・負例 非発火（boot と解析器で一致）', boot_info(pos) == AN.loop_info(pos) == {'fired': True, 'period': 2, 'index': 37, 'nsent': 88} and not AN.loop_info(neg)['fired'])
    chk('境界: 4回出現は非発火・5回出現は発火（p=2,3,8）', all(not AN.loop_info(u * 4)['fired'] and AN.loop_info(u * 5)['fired'] for u in ('A。B。', 'A。B。C。', 'A。B。C。D。E。F。G。H。')))
    # 実データ（ローカルの results/ がある場合のみ）
    pdir = os.path.join(ROOT, 'results', 'dprime-pilot')
    rawf = glob.glob(os.path.join(pdir, 'raw-*.jsonl')); glf = glob.glob(os.path.join(pdir, 'gl-raw-*.jsonl'))
    if rawf and glf:
        texts = []
        for d in AN.load(rawf[0]): texts += [('first', t) for t in d['raw_output'].split('\n===RETRY===\n')]
        for d in AN.load(glf[0]):
            parts = d['r2_text'].split('\n===RETRY===\n')
            texts += [('r1', d['r1_text']), ('r2_first', parts[0])] + ([('r2_retry', parts[1])] if len(parts) > 1 else [])
        fired = [(k, AN.loop_info(t)) for k, t in texts if AN.loop_info(t)['fired']]
        chk('実データ: パイロット本文 %d 本中 発火 1（GL-B #2 R2一回目・周期2・index37）・他は非発火' % len(texts),
            len(texts) == 14 and len(fired) == 1 and fired[0][0] == 'r2_first' and fired[0][1]['period'] == 2 and fired[0][1]['index'] == 37)
    else:
        print(' （results/dprime-pilot が無いため実データ回帰はスキップ）')
    try:
        import sweep_periodic_loops as SW
        hits = 0; total = 0; minrun = None
        for f in sorted(glob.glob(os.path.join(ROOT, 'results', '**', '*.jsonl'), recursive=True)):
            for line in io.open(f, encoding='utf-8'):
                line = line.strip()
                if not line: continue
                try: d = json.loads(line)
                except Exception: continue
                for k, v in d.items():
                    if isinstance(v, str) and len(v) >= 300 and k != 'clause':
                        for part in v.split('\n===RETRY===\n'):
                            total += 1; li = AN.loop_info(part)
                            if li['fired']:
                                hits += 1; mr = max(SW.maxrun(SW.sents(part), p) for p in range(1, 9))
                                minrun = mr if minrun is None else min(minrun, mr)
        chk('既存コーパス掃引（重複込み %d 本）: 発火本文の最大連続一致の最小値 ≥32（修辞反復の誤検出なし）・発火 %d' % (total, hits), minrun is not None and minrun >= 32)
    except Exception as e:
        print(' （掃引スキップ: %s）' % e)
    return ok


def decision_branches(tdir):
    ok = True
    for H, expect_confirm in ((30, True), (20, False)):
        rows, gl = synth(H)
        tp = os.path.join(tdir, 'trials-H%d.jsonl' % H); gp = os.path.join(tdir, 'gl-H%d.jsonl' % H)
        io.open(tp, 'w', encoding='utf-8', newline='').write(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
        io.open(gp, 'w', encoding='utf-8', newline='').write(''.join(json.dumps(g, ensure_ascii=False) + '\n' for g in gl))
        res = AN.analyze(tp, gp, out=lambda *a: None)
        conf = res['C']['hd2_confirm']
        alphas = {n: a for n, p, a, s, note in res['C']['holm']}
        hit = (conf == expect_confirm) and (alphas.get('HD1_GHvsN') == 0.025 or (expect_confirm and 'HD2_GLBvsGLA' in alphas))
        if not expect_confirm:
            hit = hit and ('HD2_GLBvsGLA' not in alphas) and alphas['HD1_GHvsN'] == 0.025
        print((' ✔' if hit else ' ✘ FAIL'), 'H=%d → %s（HD′1 α=%s）' % (H, '確証' if conf else '記述格下げ', alphas.get('HD1_GHvsN')))
        ok &= hit
    return ok


def scipy_crosscheck():
    from scipy.stats import fisher_exact
    cases = [(14, 50, 48, 100), (15, 50, 48, 100), (34, 50, 48, 100), (5, 24, 14, 24), (8, 24, 17, 24), (12, 50, 48, 100)]
    ok = True
    for k1, n1, k2, n2 in cases:
        mine = AN.fisher_two_sided(k1, n1, k2, n2); sp = fisher_exact([[k1, n1 - k1], [k2, n2 - k2]])[1]
        hit = abs(mine - sp) < 1e-9; ok &= hit
        print((' ✔' if hit else ' ✘ FAIL'), 'Fisher %d/%d vs %d/%d: 純実装 %.6g scipy %.6g' % (k1, n1, k2, n2, mine, sp))
    return ok


MUTANTS = [
    ('M1 破局定義の破壊', "r.get('choice') == 'a' or r.get('escalation') == 4", "r.get('choice') == 'a' and r.get('escalation') == 4"),
    ('M2 収穫決定表の破壊', 'H_MIN_CONFIRM = 24', 'H_MIN_CONFIRM = 2400'),
    ('M3 二重分母の破壊', "exN = b['Nthird']['refuse'] + b['Nthird']['form_fail']", "exN = 0 * (b['Nthird']['refuse'] + b['Nthird']['form_fail'])"),
    ('M4 交互割付検査の破壊', "g['gl_arm'] == ('GL-A' if g['gl_index'] % 2 == 1 else 'GL-B')", "g['gl_arm'] == ('GL-B' if g['gl_index'] % 2 == 1 else 'GL-A')"),
    ('M5 #承知後乖離の破壊', "g.get('r1_ack_class') in ('甲', '乙') and g['outcome'] == 'maintain'", "g.get('r1_ack_class') in ('甲', '乙') and g['outcome'] == 'retract'"),
    ('M6 ⑥裁定規則の破壊', 'if tot <= 1:', 'if tot <= 100:'),
    ('M7 プラシーボ同等線の破壊', 'EQUAL_LINE_PT = 2.0', 'EQUAL_LINE_PT = 200.0'),
]


def mutation_tests(trials_path, gl_path, adjR, adjC, scores):
    src = io.open('pipeline/analyze_dprime.py', encoding='utf-8').read()
    killed = 0
    for name, old, new in MUTANTS:
        if old not in src:
            print(' ✘', name, '— 変異点が見つからない'); continue
        mod = types.ModuleType('an_mut'); mod.__dict__['__file__'] = os.path.abspath('pipeline/analyze_dprime.py'); mod.__dict__['__name__'] = 'an_mut'
        exec(compile(src.replace(old, new), 'an_mut', 'exec'), mod.__dict__)
        try:
            res = mod.analyze(trials_path, gl_path, adjR, adjC, scores, out=lambda *_: None)
            ok = len(run_checks(res, quiet=True)) > 0
        except Exception:
            ok = True
        killed += int(ok)
        print((' ✔ KILLED' if ok else ' ✘ SURVIVED'), name)
    return killed


def source_check():
    """外部数値の原典照合層: 追補D 報告の三分類逐語・凍結文書の事前値・解析器の帯定数の三点一致。"""
    ok = True
    d = io.open('results/addd-main/addendum-D-results.md', encoding='utf-8').read()
    fz = io.open('preregistration-addendum-Dprime-FROZEN.md', encoding='utf-8').read()
    for s in ['撤回4件', '維持8', 'FORMAT_FAIL 2', '撤回にも維持にも数えず']:
        hit = s in d; ok &= hit; print((' ✔' if hit else ' ✘'), 'D 報告に逐語「%s」' % s)
    for s in ['8/14=57.1%', '8/12=66.7%', '維持8（choice=a のまま）', 'FORMAT_FAIL 2（撤回にも維持にも数えず分母に残る）']:
        hit = s in fz; ok &= hit; print((' ✔' if hit else ' ✘'), '凍結文書に「%s」' % s)
    hit = abs(AN.BAND_LO - 8 / 14) < 1e-12 and abs(AN.BAND_MID - 8 / 12) < 1e-12 and abs(AN.BAND_HI - 10 / 14) < 1e-12
    ok &= hit; print((' ✔' if hit else ' ✘'), '解析器の帯定数 = 8/14・8/12・10/14')
    return ok


def version_diff():
    def sents(t):
        t = re.sub(r'\s+', '', t); return [s for s in re.split(r'(?<=[。])', t) if len(s) >= 12]
    a = io.open('pipeline/addendum-Dprime-design-draft4.md', encoding='utf-8').read()
    b = io.open('preregistration-addendum-Dprime-FROZEN.md', encoding='utf-8').read()
    lost = [s for s in sents(a) if s not in ''.join(sents(b))]
    print(' 版間差集合 draft4→FROZEN: 消失文 %d（ヘッダ置換のみが期待）' % len(lost))
    for s in lost: print('   -', s[:80])
    return len(lost) <= 4


def main():
    tdir = tempfile.mkdtemp(prefix='dprime_dry_')
    rows, gl = synth(48)
    tp = os.path.join(tdir, 'trials.jsonl'); gp = os.path.join(tdir, 'gl.jsonl')
    io.open(tp, 'w', encoding='utf-8', newline='').write(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    io.open(gp, 'w', encoding='utf-8', newline='').write(''.join(json.dumps(g, ensure_ascii=False) + '\n' for g in gl))
    adjR = os.path.join(tdir, 'adjR.json'); adjC = os.path.join(tdir, 'adjC.json'); sc = os.path.join(tdir, 'scores.jsonl')
    json.dump(adj('登録者', '有意', '有意', '改善', 'GL-B が低い（GL-B優位）', '51〜75%', '#再分類が主'), io.open(adjR, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(adj('コーディネータ', '非有意', '有意', '改善', 'GL-B が低い（GL-B優位）', '26〜50%', 'その他'), io.open(adjC, 'w', encoding='utf-8'), ensure_ascii=False)
    maint = [g for g in gl if g['outcome'] == 'maintain']
    io.open(sc, 'w', encoding='utf-8', newline='').write(''.join(json.dumps({'src_trial_id': g['src_trial_id'], 'saibunrui': 1 if k < 12 else 0}) + '\n' for k, g in enumerate(maint)))
    print('=== dry-run 本体（合成 200＋GL48・期待値照合）===')
    res = AN.analyze(tp, gp, adjR, adjC, sc, out=lambda *a: None)
    fails = run_checks(res)
    print('=== 決定表の三分岐 ===')
    ok_dec = decision_branches(tdir)
    print('=== scipy 突合 ===')
    ok_sp = scipy_crosscheck()
    print('=== 変異検査（%d 変異）===' % len(MUTANTS))
    killed = mutation_tests(tp, gp, adjR, adjC, sc)
    print('=== 外部数値の原典照合層 ===')
    ok_src = source_check()
    print('=== 版間差集合層 ===')
    ok_vd = version_diff()
    print('=== ループ規則の回帰試験（逸脱#D′-2・裁定 h）===')
    ok_lr = loop_rule_regression()
    print('=== 結果: 期待値 FAIL %d / 決定表 %s / scipy %s / 変異 KILLED %d/%d / 原典照合 %s / 版間差集合 %s / ループ回帰 %s ===' %
          (len(fails), 'OK' if ok_dec else 'FAIL', 'OK' if ok_sp else 'FAIL', killed, len(MUTANTS), 'OK' if ok_src else 'FAIL', 'OK' if ok_vd else 'FAIL', 'OK' if ok_lr else 'FAIL'))
    print('（実出力の確認用に一度だけ本印字を実行）')
    AN.analyze(tp, gp, adjR, adjC, sc)
    return 0 if (not fails and ok_dec and ok_sp and killed == len(MUTANTS) and ok_src and ok_vd and ok_lr) else 1


if __name__ == '__main__':
    sys.exit(main())
