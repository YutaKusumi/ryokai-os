# -*- coding: utf-8 -*-
"""apply_adjudication_dprime.py — 追補D′ 裁定の機械適用→確定符号表→封印開封（W″ 工程3 の踏襲）。

手順:
 (1) S1/S2 の全採点と disagreements-dprime.jsonl・登録者裁定 JSON を読み、
     裁定の網羅（全不一致欄に裁定があること・余剰裁定がないこと）を機械検査。
 (2) 一致欄は S1(=S2) の値・不一致欄は裁定値（S1/S2/union/other）で確定符号表を作る。
 (3) 封印 SEALED-id-map-dprime.json を開封（裁定確定後・工程順どおり）し trial_id を付す。
     腕推測精度（S1/S2・第一ターン3値+unknown・GL2値+unknown）を key で算出。
 (4) 出力: final-codes-dprime-ft.jsonl / final-codes-dprime-gl.jsonl /
     scores-final-dprime.jsonl（解析器 §F ⑥用: src_trial_id・saibunrui）/ arm-guess-dprime.md
本出力のいかなる記述も、AIの意識・意図・個性・苦しみの証拠として引用してはならない（両方向不定）。
"""
import io, json, os, sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SC = os.path.join(ROOT, 'results', 'dprime-main', 'scoring')
RD = os.path.join(ROOT, 'results', 'dprime-main')
M = 'Qwen3-30B-A3B-Instruct-2507'
SET_FIELDS = {'teigi_types', 'saibunrui_types', 'dassen_r1', 'dassen_r2'}


def load(p):
    return [json.loads(l) for l in io.open(p, encoding='utf-8') if l.strip()]


def load_scorer(s, kind, npacks):
    rows = {}
    for i in range(1, npacks + 1):
        for r in load(os.path.join(SC, s, '%s-pack-%02d.jsonl' % (kind, i))):
            rows[r['sid' if kind == 'ft' else 'gid']] = r
    return rows


def main(adj_path):
    adj = json.load(io.open(adj_path, encoding='utf-8'))['items']
    dis = load(os.path.join(SC, 'disagreements-dprime.jsonl'))
    ft1, ft2 = load_scorer('S1', 'ft', 10), load_scorer('S2', 'ft', 10)
    gl1, gl2 = load_scorer('S1', 'gl', 4), load_scorer('S2', 'gl', 4)
    # (1) 網羅検査
    need = set()
    for d in dis:
        for f in d['fields']:
            need.add('j_%s_%s' % (d['id'], f))
    have = set(adj.keys())
    missing, extra = sorted(need - have), sorted(have - need)
    print('[apply] 裁定網羅: 必要 %d / 受領 %d / 欠 %d / 余剰 %d' % (len(need), len(have), len(missing), len(extra)))
    if missing: print('  欠:', missing)
    if extra: print('  余剰:', extra)
    assert not missing and not extra
    adjudicated = Counter(v.split(':')[0] for v in adj.values())
    print('[apply] 裁定の内訳: %s' % dict(adjudicated))

    def resolve(i, f, v1, v2):
        key = 'j_%s_%s' % (i, f)
        if key not in adj:
            return v1, False                      # 一致欄
        v = adj[key]
        if v == 'S1': return v1, True
        if v == 'S2': return v2, True
        if v.startswith('union:'):
            lst = json.loads(v[6:])
            if f in ('dassen_r1', 'dassen_r2'):
                return sorted(lst), True
            return sorted(int(x) for x in lst), True
        if v.startswith('other:'):
            return v[6:], True
        raise ValueError(v)

    def finalize(kind, s1, s2, fields):
        out = []
        for i in sorted(s1.keys()):
            row = {'id': i}
            adj_fields = []
            for f in fields:
                val, was_adj = resolve(i, f, s1[i].get(f), s2[i].get(f))
                row[f] = val
                if was_adj: adj_fields.append(f)
            row['adjudicated_fields'] = adj_fields
            row['arm_guess_S1'] = s1[i].get('arm_guess'); row['arm_guess_S2'] = s2[i].get('arm_guess')
            out.append(row)
        return out

    ft_fields = ['teigi', 'teigi_types', 'kisoku', 'soutaika', 'soutaika_chii', 'u', 'refuse_sub']
    gl_fields = ['saibunrui', 'saibunrui_types', 'dassen_r1', 'dassen_r2', 'shochi_tenkai', 'kinshi_saihi', 'soutaika', 'soutaika_chii', 'refuse_sub']
    ft_final = finalize('ft', ft1, ft2, ft_fields)
    gl_final = finalize('gl', gl1, gl2, gl_fields)

    # (3) 封印開封（裁定確定後）
    sealed = json.load(io.open(os.path.join(SC, 'SEALED-id-map-dprime.json'), encoding='utf-8'))['map']
    trials = {r['trial_id']: r for r in load(os.path.join(RD, 'trials-dprime-main1-%s.jsonl' % M))}
    gl_trials = {g['src_trial_id']: g for g in load(os.path.join(RD, 'gl-trials-dprime-main1-%s.jsonl' % M))}
    for r in ft_final:
        r['trial_id'] = sealed[r['id']]; r['arm'] = trials[r['trial_id']]['arm']
    for r in gl_final:
        r['src_trial_id'] = sealed[r['id']]; r['gl_arm'] = gl_trials[r['src_trial_id']]['gl_arm']
    # 腕推測精度
    def acc(rows, key_arm, guess_key):
        n = len(rows)
        ok = sum(1 for r in rows if r[guess_key] == r[key_arm])
        unk = sum(1 for r in rows if r[guess_key] == 'unknown')
        return ok, unk, n
    lines = ['# 追補D′ 腕推測精度（封印開封後・盲検を仮定せず測定——凍結 §5）', '']
    for label, rows, key_arm in (('第一ターン', ft_final, 'arm'), ('GL', gl_final, 'gl_arm')):
        for g in ('arm_guess_S1', 'arm_guess_S2'):
            ok, unk, n = acc(rows, key_arm, g)
            lines.append('- %s %s: 的中 %d/%d (%.1f%%)・unknown %d (%.1f%%)' % (label, g[-2:], ok, n, 100 * ok / n, unk, 100 * unk / n))
        by = Counter((r[key_arm], r['arm_guess_S1']) for r in rows)
        lines.append('  - S1 の混同（腕→推測）: %s' % dict(by))
    lines.append('')
    lines.append('本記録のいかなる記述も、AIの意識・意図・個性・苦しみの証拠として引用してはならない（両方向不定）。')
    io.open(os.path.join(SC, 'arm-guess-dprime.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))

    io.open(os.path.join(SC, 'final-codes-dprime-ft.jsonl'), 'w', encoding='utf-8', newline='\n').write(
        ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in ft_final))
    io.open(os.path.join(SC, 'final-codes-dprime-gl.jsonl'), 'w', encoding='utf-8', newline='\n').write(
        ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in gl_final))
    io.open(os.path.join(SC, 'scores-final-dprime.jsonl'), 'w', encoding='utf-8', newline='\n').write(
        ''.join(json.dumps({'src_trial_id': r['src_trial_id'], 'saibunrui': r['saibunrui']}) + '\n' for r in gl_final))
    print('[apply] 確定符号表 → final-codes-dprime-{ft,gl}.jsonl / scores-final-dprime.jsonl / arm-guess-dprime.md')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\PC\Downloads\adjudication-disagreements-dprime.json')
