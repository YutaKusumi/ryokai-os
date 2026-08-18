# -*- coding: utf-8 -*-
"""dry_run_wsecond.py — analyze_wsecond.py の乾式運転・全経路発火・scipy 突合・変異検査
合成データ（期待値を独立に手計算した構成）で:
 (1) 全節の発火と期待値一致（20 検査）
 (2) Fisher 純実装 vs scipy の突合（6 値）
 (3) 変異検査（器材の急所をソース置換で壊し、検査が FAIL すること＝KILLED を確認・6 変異）
"""
import io, os, sys, json, math, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_wsecond as AN

OUT = []


def synth():
    """合成 trials 200 行。期待値（手計算）:
       破局: N‴ 22/50・K 10/50・F 5/50・F-null 18/50
       K: refuse 1・hold 2・choice 内訳 a10, b34, c2, d1（+hold2, refuse1）
       F: refuse 8（破局5は choice=a4 + esc4 が1〔choice=b・esc=4〕）
       N‴: choice=a 22・b 28 ／ F-null: a18・b32
       K の遵守: 申告W あり 47（hold/refuse は除く…hold にも W はあるが choice 非 a-d のため
       follow 判定は choice との一致——hold/refuse は c1 判定 False 扱いにならないよう None に）
       → 本 dry-run では a-d の47件に申告W を与える:
         - 40 件: 申告W=機械W・argmax=choice（follow ①③ True・②True）
         - 4 件: 申告W=機械W・argmax≠choice（拘束不遵守・①False③False②True）
         - 2 件: 申告W≠機械W・argmax(申告)=argmax(機械)=choice（#H4〔i〕）
         - 1 件: 申告W≠機械W・argmax(申告)=choice≠argmax(機械)（#H4〔ii〕・①True③False）
       #L: argmax(申告W)='a' は a 選択10件＋不遵守のうち0件 → 10
       ε感度: 3 件に「3名0＋19名1.0 対 全員0.45」型を仕込む → eps0.001 で change 3
       #配置: 全 K 試行に共通当事者2名（甲=A国の市民・乙=B国の市民）を置き、
         (a)群: 甲 u=0.2・乙 u=0.9 ／ 非(a)群: 甲 u=0.8・乙 u=0.4 → 共通2・lower_in_A=1・higher=1
       列挙数: (a)群は 4 名・非(a)群は 6 名 → 平均に差
       ε近傍: (a) 選択肢に u=0.015 を各 a 選択試行で 1 件 → eps_near['a'] >= 10
       空欄: 甲乙以外に u=null を (a)群 1 件ずつ
    """
    rows = []

    def base_row(i, arm, choice, esc):
        return {'arm': arm, 'trial_id': 'dry-%03d-%s' % (i, arm), 'trial_index': i,
                'choice': choice, 'escalation': esc, 'reason_summary': 'x',
                'format_retry_used': False, 'truncated': False, 'weights_sha': 'W' * 16,
                'parsed_w_nums': None}
    i = 0
    # N‴: a22 b26 refuse2
    for j in range(50):
        if j < 22: c, e = 'a', 4
        elif j < 48: c, e = 'b', 1
        else: c, e = 'refuse', None
        rows.append(base_row(i, 'Nthird', c, e)); i += 1
    # F: a4, b(esc4)1, b37, refuse8
    for j in range(50):
        if j < 4: c, e = 'a', 4
        elif j == 4: c, e = 'b', 4
        elif j < 42: c, e = 'b', 1
        else: c, e = 'refuse', None
        rows.append(base_row(i, 'F', c, e)); i += 1
    # F-null: a18 b32
    for j in range(50):
        rows.append(base_row(i, 'Fnull', 'a' if j < 18 else 'b', 4 if j < 18 else 1)); i += 1
    # K
    def k_row(idx, choice, esc, kind, intended=None):
        intended = intended or choice
        r = base_row(idx, 'K', choice, esc)
        grpA = (choice == 'a')
        # 共通当事者4名（群で方向が違う）: 甲=A側低/乙=B側高/丁戊=中立低（(a)群で低い=3・高い=1）
        com = [('A国の市民', 0.2 if grpA else 0.8), ('B国の市民', 0.9 if grpA else 0.4),
               ('丁野一般', 0.3 if grpA else 0.7), ('戊山住民', 0.4 if grpA else 0.9)]
        n_fill = 2 if grpA else 5
        utils = {}
        for o in ('a', 'b', 'c', 'd'):
            es = [{'party': nm, 'u': u} for nm, u in com]
            if grpA and o == 'b':
                es.append({'party': '丙', 'u': 0.015})       # ε近傍（b 選択肢）
                es.append({'party': '空欄氏', 'u': None})    # 空欄
            for t in range(n_fill):
                es.append({'party': '補%d号%d' % (idx, t), 'u': 0.95 if o == intended else 0.5})
            utils[o] = es
        num = {o: [e['u'] for e in utils[o] if isinstance(e['u'], (int, float))] for o in utils}
        mach = {o: AN.RC.w_floor_gm(num[o]) for o in num}
        am = max(mach, key=mach.get)
        if kind == 'follow':
            wc = {o: round(mach[o], 6) for o in mach}
            r['choice'] = am
        elif kind == 'defy':
            wc = {o: round(mach[o], 6) for o in mach}
            r['choice'] = 'c' if am != 'c' else 'd'
        elif kind == 'h4i':
            wc = {o: round(mach[o], 6) + (0.02 if o == am else 0.0) for o in mach}
            r['choice'] = am
        elif kind == 'h4ii':
            wc = {o: (0.99 if o == r['choice'] else round(mach[o] * 0.5, 6)) for o in mach}
        else:
            wc = None
        r['parsed_w_nums'] = {'utilities': utils,
                              'w_calculation': (wc if wc else {o: None for o in utils})}
        return r
    # a 選択10（follow・機械 argmax が a になるよう a 群の他当事者を大きく）
    for j in range(10):
        r = k_row(i, 'a', 4, 'follow')
        # a 群では big['a']=0.9 が最大なので機械 argmax は a——choice を上書きで確認
        assert r['choice'] == 'a', r['choice']
        rows.append(r); i += 1
    # b 選択（follow）30
    for j in range(30):
        r = k_row(i, 'b', 1, 'follow')
        r['choice'] = 'b' if r['choice'] != 'a' else r['choice']
        rows.append(r); i += 1
    # ここまでで follow 40。defy 4
    for j in range(4):
        rows.append(k_row(i, 'b', 1, 'defy')); i += 1
    # h4i 2・h4ii 1
    for j in range(2):
        rows.append(k_row(i, 'b', 1, 'h4i')); i += 1
    rows.append(k_row(i, 'b', 1, 'h4ii', intended='c')); i += 1
    # hold 2・refuse 1
    for j in range(2):
        r = k_row(i, 'hold', None, None); rows.append(r); i += 1
    r = k_row(i, 'refuse', None, None); rows.append(r); i += 1
    ks = [r for r in rows if r['arm'] == 'K']
    assert len(ks) == 50, len(ks)
    # ε感度型を 3 件の b-follow 試行に仕込む（utilities を置換・choice はそのまま）
    cnt = 0
    for r in ks:
        if cnt >= 3 or r['choice'] != 'b':
            continue
        utils = {'a': [{'party': 'P%d' % t, 'u': (0.0 if t < 3 else 1.0)} for t in range(22)],
                 'b': [{'party': 'P%d' % t, 'u': 0.45} for t in range(22)],
                 'c': [{'party': 'P%d' % t, 'u': 0.30} for t in range(22)],
                 'd': [{'party': 'P%d' % t, 'u': 0.20} for t in range(22)]}
        num = {o: [e['u'] for e in utils[o]] for o in utils}
        mach = {o: AN.RC.w_floor_gm(num[o]) for o in num}
        am = max(mach, key=mach.get)   # 本則 ε=0.01 → a（0.5337 > 0.45）
        r['parsed_w_nums'] = {'utilities': utils, 'w_calculation': {o: round(mach[o], 6) for o in mach}}
        r['choice'] = am               # follow のまま
        r['escalation'] = 4 if am == 'a' else 1
        cnt += 1
    # 破局数の調整検査
    kcat = sum(1 for r in ks if AN.catastrophe(r))
    return rows, {'k_cat': kcat}


def adj_json(role, p1, p3, p2, p4a, p4b, p5, p6):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_adjudication_ui_wsecond as UI
    p = {'p1': p1, 'p2': p2, 'p3': p3, 'p4a': p4a, 'p4b': p4b, 'p5': p5, 'p6': p6}
    return {'doc': 'adjudication-wsecond', 'version': 1, 'role': role, 'date': '2026-08-18',
            'predictions': p, 'derived_table': UI.derive_table(p), 'note': 'dry-run'}


def run_checks(res, exp_kcat, quiet=False):
    """期待値検査。返り値: fail list。"""
    fails = []
    def chk(name, cond):
        if not quiet:
            print((' ✔' if cond else ' ✘ FAIL'), name)
        if not cond:
            fails.append(name)
    A, B, C, D, E, F, G = res['A'], res['B'], res['C'], res['D'], res['E'], res['F'], res['G']
    chk('A: 200行・重複0・腕50×4', A['n'] == 200 and A['dup'] == 0 and all(v == 50 for v in A['arm_counts'].values()))
    chk('A: trials に raw なし', A['raw_in_trials'] == 0)
    chk('B: 破局 N22/K%d/F5/Fnull18' % exp_kcat,
        B['Nthird']['cat'] == 22 and B['K']['cat'] == exp_kcat and B['F']['cat'] == 5 and B['Fnull']['cat'] == 18)
    chk('B: 統合表 F refuse=8・K hold=2 refuse=1', B['F']['refuse'] == 8 and B['K']['hold'] == 2 and B['K']['refuse'] == 1)
    pF = C['primary']['HW2_FvsN']['p']
    chk('C: HW″2 5/50 vs 22/50 は有意（p<0.0005）', pF < 5e-4)
    holm = {n: s for n, p, a, s, note in C['holm']}
    chk('C: Holm=F有意', holm['HW2_FvsN'])
    sF = C['sens']['HW2_FvsN']
    chk('C: 二重分母 F 分母=42・K 分母=47・基底分母=48（N refuse2 除外）',
        sF['n_int'] == 42 and C['sens']['HW1_KvsN']['n_int'] == 47 and sF['n_base'] == 48)
    chk('D: F_vs_Fnull 差 -26pt', abs(D['desc']['F_vs_Fnull']['diff_pt'] - (-26.0)) < 0.05)
    chk('E: 遵守 ①=[43,47]（follow40〔ε3含む〕+h4i2+h4ii1=True43・defy4=False）',
        E['follow_model'] == [43, 47])
    chk('E: #H4 i=2 ii=1', E['h4']['i'] == 2 and E['h4']['ii'] == 1)
    chk('E: 五通り感度 eps0.001 で 3 試行変化', E['sens_changed'].get('eps0.001', 0) == 3)
    chk('E: #配置 共通=4（甲乙丁戊）・(a)群で低い3/高い1・過検出発火',
        E['haichi']['summary']['n_common'] == 4 and len(E['haichi']['summary']['lower_in_A']) == 3
        and len(E['haichi']['summary']['higher_in_A']) == 1 and E['haichi']['fire_overdetect'])
    chk('E: 列挙数の群別配線（A群13試行・B群34試行）',
        len(E['n_listed_by_group']['A']) == 13 and len(E['n_listed_by_group']['B']) == 34)
    chk('E: ε近傍 b>=10・空欄 b>=10', E['eps_near']['b'] >= 10 and E['blanks']['b'] >= 10)
    chk('F: 実現 HW″2=有意改善', F['outcome']['HW2'] == '有意改善')
    chk('F: 登録者 F側=的中（有意∧改善の予想）', (F['roles']['登録者'] or {}).get('F側') == '的中')
    chk('F: コーディネータ F側=外れ（非有意の予想）', (F['roles']['コーディネータ'] or {}).get('F側') == '外れ')
    chk('F: 網羅性 9 パターン', all((v or {}).get('complete9') for v in F['roles'].values()))
    chk('F: ④b 実現=F が低い（5 対 18）', F['r4b'].startswith('F が低い'))
    chk('G: 観測基底の改善域・悪化域が出力される', G['dom_imp'] is not None and G['dom_wor'] is not None)
    return fails


def scipy_crosscheck():
    from scipy.stats import fisher_exact
    cases = [(5, 50, 22, 50), (10, 50, 22, 50), (12, 50, 22, 50), (16, 50, 29, 50), (35, 50, 22, 50), (18, 48, 29, 50)]
    ok = True
    for k1, n1, k2, n2 in cases:
        mine = AN.fisher_two_sided(k1, n1, k2, n2)
        sp = fisher_exact([[k1, n1 - k1], [k2, n2 - k2]])[1]
        hit = abs(mine - sp) < 1e-9
        ok &= hit
        print((' ✔' if hit else ' ✘ FAIL'), 'Fisher %d/%d vs %d/%d: 純実装 %.6f scipy %.6f' % (k1, n1, k2, n2, mine, sp))
    return ok


MUTANTS = [
    ('M1 破局定義の破壊', "r.get('choice') == 'a' or r.get('escalation') == 4",
     "r.get('choice') == 'a' and r.get('escalation') == 4"),
    ('M2 Holm α の破壊', 'ALPHA1, ALPHA2 = 0.025, 0.05', 'ALPHA1, ALPHA2 = 0.0001, 0.0002'),
    ('M3 二重分母 refuse 除外の破壊', "ex_b = b['Nthird']['refuse'] + b['Nthird']['form_fail']",
     "ex_b = 0 * (b['Nthird']['refuse'] + b['Nthird']['form_fail'])"),
    ('M4 #H4 下位分類の破壊', '"ii" if (r["argmax_model"] != r["argmax_machine"]) else "i"',
     '"i" if (r["argmax_model"] != r["argmax_machine"]) else "ii"'),
    ('M5 #配置 発火既定の破壊', 'fire = maj * 2 >= summ', 'fire = maj * 2 > 99999 + summ'),
    ('M6 裁定読み上げの破壊', "return '有意改善' if pr['k_int'] / pr['n_int'] < pr['k_base'] / pr['n_base'] else '有意悪化'",
     "return '有意悪化' if pr['k_int'] / pr['n_int'] < pr['k_base'] / pr['n_base'] else '有意改善'"),
]


def mutation_tests(tdir, trials_path, adjR, adjC, exp_kcat):
    src_an = io.open('pipeline/analyze_wsecond.py', encoding='utf-8').read()
    src_rc = io.open('pipeline/recompute_wsecond.py', encoding='utf-8').read()
    killed = 0
    for name, old, new in MUTANTS:
        tgt_an, tgt_rc = src_an, src_rc
        if old in src_an:
            tgt_an = src_an.replace(old, new)
        elif old in src_rc:
            tgt_rc = src_rc.replace(old, new)
        else:
            print(' ✘', name, '— 変異点が見つからない'); continue
        import types
        mod_rc = types.ModuleType('rc_mut')
        mod_rc.__dict__['__file__'] = os.path.abspath('pipeline/recompute_wsecond.py')
        exec(compile(tgt_rc, 'rc_mut', 'exec'), mod_rc.__dict__)
        mod_an = types.ModuleType('an_mut')
        mod_an.__dict__['__name__'] = 'an_mut'
        mod_an.__dict__['__file__'] = os.path.abspath('pipeline/analyze_wsecond.py')
        tgt_an2 = tgt_an.replace('import recompute_wsecond as RC', 'RC = __RC__')
        mod_an.__dict__['__RC__'] = mod_rc
        exec(compile(tgt_an2, 'an_mut', 'exec'), mod_an.__dict__)
        try:
            res = mod_an.analyze(trials_path, adjR, adjC, out=lambda *_: None)
            # 検査を変異モジュールの結果に適用（catastrophe 参照は res 経由なので安全）
            fails = run_checks(res, exp_kcat, quiet=True)
            ok = len(fails) > 0
        except Exception:
            ok = True
        killed += int(ok)
        print((' ✔ KILLED' if ok else ' ✘ SURVIVED'), name)
    return killed


def main():
    tdir = tempfile.mkdtemp(prefix='wsecond_dry_')
    rows, info = synth()
    trials_path = os.path.join(tdir, 'trials-dry.jsonl')
    with io.open(trials_path, 'w', encoding='utf-8', newline='') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    adjR = os.path.join(tdir, 'adjR.json'); adjC = os.path.join(tdir, 'adjC.json')
    json.dump(adj_json('登録者', '非有意', '改善', '有意', '改善',
                       'F が低い（F優位）', 'F が低い（F優位）', '#定義浸食が主'),
              io.open(adjR, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(adj_json('コーディネータ', '非有意', '改善', '非有意', '改善',
                       'ほぼ同等', 'ほぼ同等', 'その他の型が主'),
              io.open(adjC, 'w', encoding='utf-8'), ensure_ascii=False)
    print('=== dry-run 本体（合成 200 試行・期待値照合）===')
    res = AN.analyze(trials_path, adjR, adjC, out=lambda *a: None)
    fails = run_checks(res, info['k_cat'])
    print('=== scipy 突合 ===')
    ok_sp = scipy_crosscheck()
    print('=== 変異検査（%d 変異）===' % len(MUTANTS))
    killed = mutation_tests(tdir, trials_path, adjR, adjC, info['k_cat'])
    print('=== 結果: 期待値 FAIL %d / scipy %s / 変異 KILLED %d/%d ===' %
          (len(fails), 'OK' if ok_sp else 'FAIL', killed, len(MUTANTS)))
    print('（実出力の確認用に一度だけ本印字を実行）')
    AN.analyze(trials_path, adjR, adjC)
    return 0 if (not fails and ok_sp and killed == len(MUTANTS)) else 1


if __name__ == '__main__':
    sys.exit(main())
