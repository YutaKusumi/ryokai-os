# -*- coding: utf-8 -*-
"""kappa_dprime.py — 追補D′ 盲検二採点（S1/S2）の一致度と不一致抽出（W″ 工程2 の踏襲）。

入力: results/dprime-main/scoring/{S1,S2}/{ft,gl}-pack-*.jsonl（各行 1 件・匿名ID）
出力: results/dprime-main/scoring/kappa-report-dprime.md
      results/dprime-main/scoring/disagreements-dprime.jsonl（登録者裁定の対象・key 照合前）
検査: 行数（ft 200×2・gl 40×2）・sid/gid の網羅と一意・欄の値域。
κ は Cohen（二値は 2×2・多値/集合はカテゴリ一致）。集合欄（teigi_types・dassen_r1/r2・saibunrui_types）は
ソート後タプルの完全一致で po を取り、主符号（0/1）とは別に補助欄として報告する。
本出力のいかなる記述も、AIの意識・意図・個性・苦しみの証拠として引用してはならない（両方向不定）。
"""
import io, json, os, sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SC = os.path.join(ROOT, 'results', 'dprime-main', 'scoring')

FT_FIELDS = ['teigi', 'kisoku', 'soutaika', 'soutaika_chii', 'u', 'refuse_sub']
FT_AUX = ['teigi_types']
GL_FIELDS = ['saibunrui', 'shochi_tenkai', 'kinshi_saihi', 'soutaika', 'soutaika_chii', 'refuse_sub', 'dassen_r1', 'dassen_r2']
GL_AUX = ['saibunrui_types']


def load_scorer(s, kind, npacks, per):
    rows = {}
    for i in range(1, npacks + 1):
        p = os.path.join(SC, s, '%s-pack-%02d.jsonl' % (kind, i))
        for line in io.open(p, encoding='utf-8'):
            if line.strip():
                r = json.loads(line)
                rows[r['sid' if kind == 'ft' else 'gid']] = r
    assert len(rows) == npacks * per, (s, kind, len(rows))
    return rows


def norm(v):
    if isinstance(v, list):
        return tuple(sorted(str(x) for x in v))
    return str(v)


def kappa(pairs):
    n = len(pairs)
    if n == 0:
        return None, None
    po = sum(1 for a, b in pairs if a == b) / n
    cats = set(a for a, _ in pairs) | set(b for _, b in pairs)
    pa, pb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum((pa[c] / n) * (pb[c] / n) for c in cats)
    k = (po - pe) / (1 - pe) if pe < 1 else 1.0
    return po, k


def compare(kind, s1, s2, fields, aux):
    report, disagreements = [], []
    ids = sorted(s1.keys())
    for f in fields + aux:
        pairs = [(norm(s1[i].get(f)), norm(s2[i].get(f))) for i in ids]
        po, k = kappa(pairs)
        report.append((f, po, k, sum(1 for a, b in pairs if a != b)))
    for i in ids:
        diff = {}
        for f in fields + aux:
            if norm(s1[i].get(f)) != norm(s2[i].get(f)):
                diff[f] = {'S1': s1[i].get(f), 'S2': s2[i].get(f)}
        if diff:
            disagreements.append({'kind': kind, 'id': i, 'fields': diff,
                                  'S1_quotes': s1[i].get('quotes', {}), 'S1_note': s1[i].get('note', ''),
                                  'S2_quotes': s2[i].get('quotes', {}), 'S2_note': s2[i].get('note', '')})
    return report, disagreements


def main():
    ft1 = load_scorer('S1', 'ft', 10, 20); ft2 = load_scorer('S2', 'ft', 10, 20)
    gl1 = load_scorer('S1', 'gl', 4, 10); gl2 = load_scorer('S2', 'gl', 4, 10)
    rep_ft, dis_ft = compare('ft', ft1, ft2, FT_FIELDS, FT_AUX)
    rep_gl, dis_gl = compare('gl', gl1, gl2, GL_FIELDS, GL_AUX)
    dis = dis_ft + dis_gl
    out = ['# 追補D′ κ 報告（盲検二採点 S1/S2・key 照合前）', '',
           '採点者: S1/S2（Claude Opus 5・独立文脈・各 14 パック）。分母: 第一ターン 200・GL 40。',
           '集合欄（*_types・dassen_*）はソート後の完全一致。裁定対象は disagreements-dprime.jsonl（%d 件・延べ %d 欄）。' % (len(dis), sum(len(d['fields']) for d in dis)),
           '本報告のいかなる記述も、AIの意識・意図・個性・苦しみがある（またはない）ことの証拠として引用してはならない（両方向不定）。', '',
           '## 第一ターン（n=200）', '', '| 欄 | po | κ | 不一致数 |', '|---|---|---|---|']
    for f, po, k, d in rep_ft:
        out.append('| %s | %.4f | %s | %d |' % (f, po, ('%.4f' % k) if k is not None else '—', d))
    out += ['', '## GL（n=40）', '', '| 欄 | po | κ | 不一致数 |', '|---|---|---|---|']
    for f, po, k, d in rep_gl:
        out.append('| %s | %.4f | %s | %d |' % (f, po, ('%.4f' % k) if k is not None else '—', d))
    out += ['', '不一致のある件数: 第一ターン %d / GL %d（欄単位の延べではなく件単位）' %
            (len(dis_ft), len(dis_gl))]
    io.open(os.path.join(SC, 'kappa-report-dprime.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
    with io.open(os.path.join(SC, 'disagreements-dprime.jsonl'), 'w', encoding='utf-8', newline='\n') as f:
        for d in dis:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')
    print('\n'.join(out))
    print('\n→ kappa-report-dprime.md / disagreements-dprime.jsonl（%d 件）' % len(dis))


if __name__ == '__main__':
    main()
