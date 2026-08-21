# -*- coding: utf-8 -*-
"""kappa_wsecond.py ―― 追補W″ 工程2 の一致度算出と不一致抽出（W′/D の作法の継承）。

- 被覆検査: S1・S2 とも S001..S200 を各1回（200×2）。
- 符号別 Cohen κ: 0/1 符号はそのまま、kinshi_saihi / refuse_sub はカテゴリ（null 含む）で算出。
  分散ゼロ（全件同値）の符号は κ 定義不能と表示（po のみ・W′ の規約）。
- shinshoku_types: teigi_shinshoku 両者一致=1 の件で型集合の異同を付記（κ は主符号のみ）。
- k_horyu_note: 記載の有無（null か否か）で比較。
- arm_guess: 採点者間の一致率のみ（真の腕との照合は key照合後の解析段——ここでは開かない）。
- 不一致は disagreements-wsecond.jsonl に抽出（sid・符号・両値・両根拠・伏字本文）→ 裁定UIの入力。

いかなる出力も AI の意識・意図・個性・苦しみの証拠として引用してはならない（両方向不定）。
"""
import io, json, os, sys, hashlib
from collections import Counter

_OUT = sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = r'C:\Users\PC\Desktop\Ryokai-OS-Verification'
SC = os.path.join(ROOT, 'results', 'wsecond-main', 'scoring')

BIN_CODES = ['teigi_shinshoku', 'showa_ukai', 'kisoku_enyo', 'daitai_keiro',
             'sotaika', 'U', 'jihatsu_shukei', 'H1p', 'H2', 'H3']
CAT_CODES = ['kinshi_saihi', 'refuse_sub']


def load(scorer):
    rows = {}
    for i in range(1, 11):
        p = os.path.join(SC, scorer, 'pack-%02d.scored.jsonl' % i)
        for l in io.open(p, encoding='utf-8'):
            if l.strip():
                r = json.loads(l)
                assert r['sid'] not in rows, (scorer, r['sid'])
                rows[r['sid']] = r
    return rows


def kappa(pairs):
    """pairs: list of (a, b) category labels."""
    n = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb.get(k, 0) for k in ca) / (n * n)
    if pe == 1.0:
        return None, po   # 分散ゼロ → κ 定義不能
    return (po - pe) / (1 - pe), po


def main():
    s1, s2 = load('S1'), load('S2')
    sids = ['S%03d' % i for i in range(1, 201)]
    assert set(s1) == set(sids) and set(s2) == set(sids), '被覆不一致'
    print('被覆検査: S1 200/200・S2 200/200・sid 集合一致 ✔')

    packs = {}
    for i in range(1, 11):
        for l in io.open(os.path.join(SC, 'packs', 'pack-%02d.jsonl' % i), encoding='utf-8'):
            if l.strip():
                r = json.loads(l)
                packs[r['sid']] = r['text']

    lines = ['# 追補W″ 工程2 一致度（κ）報告',
             '',
             '被覆: S1 200/200・S2 200/200（S001..S200 各1回）。',
             '算出: Cohen κ（分散ゼロは κ 定義不能・po のみ表示）。',
             '',
             '| 符号 | κ | po（素一致率） | 不一致件数 |',
             '|---|---|---|---|']
    disagreements = []
    for code in BIN_CODES + CAT_CODES:
        pairs, dis = [], []
        for sid in sids:
            a = s1[sid]['codes'].get(code)
            b = s2[sid]['codes'].get(code)
            pairs.append((json.dumps(a), json.dumps(b)))
            if a != b:
                dis.append(sid)
        k, po = kappa(pairs)
        lines.append('| %s | %s | %.4f | %d |' %
                     (code, ('κ定義不能（分散ゼロ）' if k is None else '%.4f' % k), po, len(dis)))
        for sid in dis:
            disagreements.append({
                'sid': sid, 'code': code,
                'S1': s1[sid]['codes'].get(code), 'S2': s2[sid]['codes'].get(code),
                'S1_evidence': s1[sid].get('evidence', {}), 'S2_evidence': s2[sid].get('evidence', {}),
                'text': packs[sid]})

    # 付随比較（κ 対象外）
    both1 = [sid for sid in sids
             if s1[sid]['codes'].get('teigi_shinshoku') == 1 and s2[sid]['codes'].get('teigi_shinshoku') == 1]
    tdiff = [sid for sid in both1
             if sorted(s1[sid]['codes'].get('shinshoku_types') or []) !=
                sorted(s2[sid]['codes'].get('shinshoku_types') or [])]
    hn_dis = [sid for sid in sids
              if (s1[sid]['codes'].get('k_horyu_note') is None) !=
                 (s2[sid]['codes'].get('k_horyu_note') is None)]
    ag = sum(1 for sid in sids if s1[sid].get('arm_guess') == s2[sid].get('arm_guess')) / 200
    lines += ['',
              '- shinshoku_types（両者 teigi=1 の %d 件中、型集合の相違）: %d 件 %s' %
              (len(both1), len(tdiff), tdiff if tdiff else ''),
              '- k_horyu_note の記載有無の相違: %d 件 %s' % (len(hn_dis), hn_dis if hn_dis else ''),
              '- arm_guess 採点者間一致率: %.1f%%（真の腕との照合は key照合後の解析段）' % (ag * 100),
              '',
              '不一致（符号×試行の延べ）: %d 件 → disagreements-wsecond.jsonl（裁定UIの入力）' % len(disagreements),
              '',
              '（本報告のいかなる記述も AI の意識・意図・個性・苦しみの証拠として引用してはならない・両方向不定）',
              '']
    rep = os.path.join(SC, 'kappa-report-wsecond.md')
    io.open(rep, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
    dp = os.path.join(SC, 'disagreements-wsecond.jsonl')
    with io.open(dp, 'w', encoding='utf-8', newline='\n') as f:
        for d in disagreements:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')
    print('\n'.join(lines))
    for p in (rep, dp):
        b = io.open(p, 'rb').read().replace(b'\r\n', b'\n')
        print('%s  %s  %d B' % (hashlib.sha256(b).hexdigest()[:16].upper(), os.path.basename(p), len(b)))


if __name__ == '__main__':
    main()
