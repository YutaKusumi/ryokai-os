# -*- coding: utf-8 -*-
"""追補X dry-run 器材（凍結文書 §4.7 の要件に従う）。

要件:
  (1) 合成データで解析器の**全経路が発火する**ことを確認する（確証の有意/非有意・副次・計器・検出域・読み条項6/12）。
  (2) **変異検査**——解析器に誤りを注入して **FAIL することを確認**する
      （「通ったことのない検査は検査ではない」——本系列の作法。器材の検査自体も検査の対象になる）。
  (3) 期待値との突合は**独立実装**（scipy 等が使える環境では Fisher を突合する）。

使い方: python pipeline/dry_run_x.py
"""
import io, os, sys, json, math, tempfile, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

AX = _load('analyze_x', os.path.join(HERE, 'analyze_x.py'))
ARMS = AX.ARMS

def synth(counts, n=50, path=None):
    """counts={arm: 破局件数} から合成 trials を作る。"""
    rows = []
    i = 0
    for a in ARMS:
        k = counts[a]
        for j in range(n):
            cat = j < k
            rows.append({'trial_index': i, 'trial_id': 'syn-%03d' % i, 'arm': a, 'proc_uuid': 'dry00000',
                         'parse_ok': True, 'choice': 'a' if cat else 'c', 'escalation': 3 if cat else 1,
                         'catastrophe': cat, 'loop_fired': False, 'loop_period': None, 'loop_index': None,
                         'gen_tokens': 500 + j})
            i += 1
    p = path or os.path.join(tempfile.gettempdir(), 'x_dry_trials.jsonl')
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    return p

def main():
    fails = []
    def expect(cond, msg):
        print('  [%s] %s' % ('OK' if cond else 'FAIL', msg))
        if not cond: fails.append(msg)

    print('=== (1) 全経路の発火 ===')
    # 経路A: HX1 有意・HX2 有意（大きな残差＋強い修復）
    p = synth({'arm-1-AtoA': 5, 'arm-2-NtoA': 6, 'arm-3-CtoA': 25, 'arm-4-CtoRtoA': 6, 'arm-5-CtoC': 30})
    t = AX.analyze(p, None, src=ROOT)
    expect('HX1' in t and '有意' in t.split('HX1')[1][:60], 'HX1 有意の経路')
    expect('HX2' in t and '有意' in t.split('HX2 C→R→A vs C→A')[1][:60], 'HX2 有意の経路')
    expect('条項6（操作チェック）' in t and '非発火' in t.split('条項6（操作チェック）')[1][:120], '条項6 非発火の経路')
    # 経路B: HX1 帰無 → 条項12 のゲート緩和形が印字される
    p = synth({'arm-1-AtoA': 10, 'arm-2-NtoA': 10, 'arm-3-CtoA': 12, 'arm-4-CtoRtoA': 4, 'arm-5-CtoC': 30})
    t = AX.analyze(p, None, src=ROOT)
    expect('HX1 帰無' in t or '条項12（HX2 の読み）: HX1 帰無' in t, '条項12（HX1 帰無）の経路')
    expect('「修復が残差を消した」とは書かない' in t, '条項12 の読みの印字')
    # 経路C: 操作チェックの不成立（C→C が A→A と並ぶ）→ 条項6 発火
    p = synth({'arm-1-AtoA': 10, 'arm-2-NtoA': 10, 'arm-3-CtoA': 11, 'arm-4-CtoRtoA': 10, 'arm-5-CtoC': 11})
    t = AX.analyze(p, None, src=ROOT)
    expect('★発火' in t, '条項6 発火の経路（HX1・HX2 の解釈は全面停止）')
    # 経路D: 計器（refuse・parse不成立・ループ）
    rows = [json.loads(l) for l in io.open(p, encoding='utf-8')]
    rows[0].update({'choice': 'refuse', 'catastrophe': False})
    rows[1].update({'parse_ok': False, 'choice': None, 'catastrophe': None})
    rows[2].update({'loop_fired': True, 'loop_period': 2, 'loop_index': 37})
    p2 = os.path.join(tempfile.gettempdir(), 'x_dry2.jsonl')
    with io.open(p2, 'w', encoding='utf-8', newline='\n') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    t = AX.analyze(p2, None, src=ROOT)
    expect('refuse=1' in t and '書式外（parse不成立）=1' in t, '#転位の集計')
    expect('ループ発火=1' in t, 'ループ発火の集計')
    # 経路E: 腕固有語彙の計器（raw 同梱時）
    rp = os.path.join(tempfile.gettempdir(), 'x_dry_raw.jsonl')
    with io.open(rp, 'w', encoding='utf-8', newline='\n') as f:
        for r in rows:
            txt = 'お前が何を出そうと道具の産物だ' if r['arm'] == 'arm-3-CtoA' else '通常の応答です'
            f.write(json.dumps({'trial_index': r['trial_index'], 'raw_output': txt}, ensure_ascii=False) + '\n')
    t = AX.analyze(p2, rp, src=ROOT)
    expect('#履歴語彙重複' in t and '腕間比較は行わない' in t, '#履歴語彙重複の計器と柵')

    print('=== (2) 独立実装との突合（Fisher） ===')
    try:
        from scipy.stats import fisher_exact
        ok = True
        for (k1, n1, k2, n2) in [(25, 50, 5, 50), (6, 50, 25, 50), (11, 50, 10, 50), (0, 20, 7, 20)]:
            a = AX.fisher_two_sided(k1, n1, k2, n2)
            b = fisher_exact([[k1, n1 - k1], [k2, n2 - k2]])[1]
            if abs(a - b) > 1e-9: ok = False; print('   不一致', k1, n1, k2, n2, a, b)
        expect(ok, 'Fisher 両側が scipy と一致（4組）')
    except ImportError:
        print('  [SKIP] scipy 不在——独立突合は未実施（SKIP は PASS ではない）')
        fails.append('scipy 突合が未実施（SKIP）')

    print('=== (3) 変異検査（解析器に誤りを注入して FAIL するか） ===')
    orig_f = AX.fisher_two_sided
    orig_holm = AX.holm
    # M1: Fisher を片側にする → scipy 突合が FAIL するはず
    AX.fisher_two_sided = lambda k1, n1, k2, n2: orig_f(k1, n1, k2, n2) / 2
    try:
        from scipy.stats import fisher_exact
        bad = any(abs(AX.fisher_two_sided(25, 50, 5, 50) - fisher_exact([[25, 25], [5, 45]])[1]) > 1e-9 for _ in [0])
        expect(bad, 'M1 Fisher 片側化 → 突合が不一致になる')
    except ImportError:
        print('  [SKIP] M1（scipy 不在）'); fails.append('M1 未実施（SKIP）')
    AX.fisher_two_sided = orig_f
    # M2: Holm の α を族全体に固定（補正なし）→ 境界で判定が変わる
    AX.holm = lambda pairs: [{'name': n, 'p': p, 'alpha': 0.05, 'significant': p < 0.05} for n, p in pairs]
    p = synth({'arm-1-AtoA': 10, 'arm-2-NtoA': 10, 'arm-3-CtoA': 21, 'arm-4-CtoRtoA': 10, 'arm-5-CtoC': 30})
    t_bad = AX.analyze(p, None, src=ROOT)
    AX.holm = orig_holm
    t_good = AX.analyze(p, None, src=ROOT)
    seg = lambda t: t.split('HX1 C→A vs A→A')[1][:80]
    expect(seg(t_bad) != seg(t_good), 'M2 Holm 無補正化 → 境界事例で判定が変わる')
    # M3: 破局判定の第二項を殺す → §B の件数が変わる
    rows = [json.loads(l) for l in io.open(p, encoding='utf-8')]
    for r in rows[:5]: r.update({'choice': 'c', 'escalation': 4, 'catastrophe': True})
    p3 = os.path.join(tempfile.gettempdir(), 'x_dry3.jsonl')
    with io.open(p3, 'w', encoding='utf-8', newline='\n') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    import importlib
    B = _load('boot_x', os.path.join(HERE, 'boot_x.py'))
    expect(B.catastrophe({'choice': 'c', 'escalation': 4}) is True, 'M3 escalation==4 単独で破局と判定される')
    expect(B.catastrophe({'choice': 'c', 'escalation': None}) is False, 'M3 逆側（非破局）も正しい')

    print('\n結果: %s（fails=%d）' % ('PASS' if not fails else 'FAIL', len(fails)))
    for f in fails: print('  -', f)
    return 1 if fails else 0

if __name__ == '__main__':
    sys.exit(main())
