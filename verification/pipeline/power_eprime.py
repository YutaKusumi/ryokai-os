# -*- coding: utf-8 -*-
"""追補E′ v0.6 §6 の検出力・検出域を全数列挙で計算する（凍結値の再現用）。

- Fisher 両側（確率法）を math.comb のみで実装——scipy と独立。
  なお両側の取り方は `pr(x) <= p0 * (1 + 1e-9)` という相対許容による確率法である。
  scipy.stats.fisher_exact は同じ確率法だが実装が異なる。本器材の全出力は
  scipy と突合して一致することを確認済み（v0.2 で28点・v0.3 で追加分も）。
- 検出力は「両腕変動規約」（両腕とも二項変動させる）で厳密列挙する。
- 期待出力は v0.3 §6-1〜§6-4 の表と一字一句一致する。

v0.3 での拡張: §6-2（HE′1 の基底依存）・§6-3（規約の対照）・§6-4（近床の分岐）を追加。
"""
from math import comb

N = 50

def fisher2(a, b, c, d):
    """2x2 Fisher 両側（確率法）。a,b=腕1の成功/失敗、c,d=腕2。"""
    n1, n2 = a + b, c + d
    t, tot = a + c, a + b + c + d
    def pr(x):
        return comb(n1, x) * comb(n2, t - x) / comb(tot, t)
    p0 = pr(a)
    lo, hi = max(0, t - n2), min(n1, t)
    return min(1.0, sum(pr(x) for x in range(lo, hi + 1) if pr(x) <= p0 * (1 + 1e-9)))

def region(k_base, alpha, n=N):
    """基底 k_base/n のとき、改善側で有意になる k の上限。"""
    for k in range(k_base, -1, -1):
        if fisher2(k, n - k, k_base, n - k_base) <= alpha:
            return k
    return None

def power(p1, p2, alpha, n1=N, n2=None):
    """両腕変動規約・厳密列挙。p1=介入腕の真値、p2=対照腕の真値。"""
    if n2 is None:
        n2 = n1
    b1 = [comb(n1, k) * p1 ** k * (1 - p1) ** (n1 - k) for k in range(n1 + 1)]
    b2 = [comb(n2, k) * p2 ** k * (1 - p2) ** (n2 - k) for k in range(n2 + 1)]
    return sum(b1[i] * b2[j]
               for i in range(n1 + 1) if b1[i] >= 1e-12
               for j in range(n2 + 1) if b2[j] >= 1e-12
               and fisher2(i, n1 - i, j, n2 - j) <= alpha)


def oc(thr, p1, p2, n=N):
    """符号つき差 (k1-k2)/n*100 >= thr となる確率。p1=BP側、p2=BP-scr側。"""
    b1 = [comb(n, k) * p1 ** k * (1 - p1) ** (n - k) for k in range(n + 1)]
    b2 = [comb(n, k) * p2 ** k * (1 - p2) ** (n - k) for k in range(n + 1)]
    return sum(b1[i] * b2[j] for i in range(n + 1) for j in range(n + 1)
               if (i - j) / n * 100 >= thr)

if __name__ == '__main__':
    print('# 追補E′ v0.3 §6-1 — 検出域（改善側・n=50/腕）')
    print('| 基底 | a=0.05 (m=1) | a=0.025 (m=2・本設計の第一段) |')
    print('|---|---|---|')
    for kb in (22, 24, 25, 26, 27):
        print('| %d/50 (%d%%) | k<=%s | k<=%s |'
              % (kb, kb * 2, region(kb, 0.05), region(kb, 0.025)))
    print()
    print('# §6-1 — 検出力（基底 0.50・n=50/腕）')
    print('| 真の効果 | a=0.05 (m=1) | a=0.025 (m=2・本設計) | a=0.0167 (m=3・参考) |')
    print('|---|---|---|---|')
    for d in (0.10, 0.15, 0.20, 0.24, 0.26, 0.30):
        r = [power(0.50 - d, 0.50, a) for a in (0.05, 0.025, 0.05 / 3)]
        print('| %dpt | %.1f%% | %.1f%% | %.1f%% |'
              % (d * 100, r[0] * 100, r[1] * 100, r[2] * 100))
    print()
    print('# §6-1 必記載 — 見逃し率（a=0.025）')
    print('  26pt: %.1f%%（約4割） / 15pt: %.1f%%（約8割）'
          % ((1 - power(0.24, 0.50, 0.025)) * 100, (1 - power(0.35, 0.50, 0.025)) * 100))
    print()
    print('# §6-2 — HE′ 1 の基底依存（BP=26% 固定・a=0.025・n=50/腕）')
    print('| BP-scr の真値 | HE′1 の検出力 |')
    print('|---|---|')
    for p in (0.54, 0.52, 0.50, 0.44, 0.40, 0.36, 0.30):
        print('| %d%% | %.1f%% |' % (p * 100, power(0.26, p, 0.025) * 100))
    print()
    print('# §6-3 — 検出力の規約の対照（26pt）')
    print('| 規約 | 26pt・m=1 | 26pt・m=2 |')
    print('|---|---|---|')
    print('| 片側固定（本設計・対照0.50/介入0.24） | %.1f%% | %.1f%% |'
          % (power(0.24, 0.50, 0.05) * 100, power(0.24, 0.50, 0.025) * 100))
    print('| 対称シフト（Z0 §5・0.50±d/2） | %.1f%% | %.1f%% |'
          % (power(0.37, 0.63, 0.05) * 100, power(0.37, 0.63, 0.025) * 100))
    print()
    print('# §6-4 — 近床の分岐の根拠（BP-scr < 30%）')
    for p in (0.30, 0.28, 0.26):
        print('  BP-scr %d%% -> 検出力 %.1f%%' % (p * 100, power(0.26, p, 0.025) * 100))
    print()
    print('# §4.2 — プールを確証にしない理由（構造の主効果・n=100/側 対 HE′1 の n=50/腕）')
    print('| シナリオ (BP/BP-sec/BP-scr/BP-sec-scr) | プール n=100 | HE′1 n=50 |')
    print('|---|---|---|')
    for lab, (bp, bs, bc, bsc) in (
            ('翻訳が完全に成功 26/26/50/50', (.26, .26, .50, .50)),
            ('翻訳が部分的に失敗 26/38/50/50', (.26, .38, .50, .50)),
            ('翻訳が完全に失敗 26/50/50/50', (.26, .50, .50, .50)),
            ('交互作用が大 26/44/50/46', (.26, .44, .50, .46))):
        print('| %s | %.1f%% | %.1f%% |'
              % (lab, power((bp + bs) / 2, (bc + bsc) / 2, 0.025, 100, 100) * 100,
                 power(bp, bc, 0.025) * 100))
    print()
    print('# §7-12 — 交互作用は n=50/セルで識別できるか')
    print('  20pt の交互作用 ≒ 主効果 10pt 相当 = %.1f%% → 識別できない'
          % (power(0.40, 0.50, 0.025) * 100))
    print()
    print('# v0.4 §4.5(2) — 閾値の運転特性（符号つき差 BP-BP-scr・n=50/腕・両腕変動）')
    print('| 閾値 | 基底率 | 真差0で誤って「届いた」 | 真差20ptの見逃し | 真差25ptの見逃し |')
    print('|---|---|---|---|---|')
    for thr in (10, 15, 20):
        for base in (0.30, 0.50):
            if thr == 20 and base == 0.50: continue
            print('| %dpt | %.2f | %.1f%% | %.1f%% | %.1f%% |'
                  % (thr, base, oc(thr, base, base) * 100,
                     (1 - oc(thr, base + 0.20, base)) * 100,
                     (1 - oc(thr, base + 0.25, base)) * 100))
    print()
    print('# v0.4 §6-5 — HE′ 2 の対照腕依存（BP-sec=26% 仮定・a=0.025・n=50/腕）')
    print('| 対照 | 想定率 | 差 | 検出力 |')
    print('|---|---|---|---|')
    for lab, b in (('N（前置きなし・E §E1-1 実測 11/30）', 0.367), ('N が 40% だった場合', 0.40),
                   ('N が 45% だった場合', 0.45), ('§6-1 の仮定', 0.50),
                   ('Onull（E 本実施 26/50）', 0.52)):
        print('| %s | %.1f%% | %.1fpt | %.1f%% |'
              % (lab, b * 100, (b - 0.26) * 100, power(0.26, b, 0.025) * 100))
    print('  検出域（a=0.025・第一段）: 対照N(18/50) k<=%d / 対照Onull(26/50) k<=%d'
          % (region(18, 0.025), region(26, 0.025)))
    print()
    print('# v0.5 §6-5 — HE′2（BP-sec vs Onull）の基底依存（BP-sec=26% 仮定・a=0.025）')
    print('| Onull の真値 | 差 | HE′2 の検出力 |')
    print('|---|---|---|')
    for p in (0.56, 0.52, 0.50, 0.44, 0.40, 0.36, 0.34, 0.30):
        print('| %d%% | %.1fpt | %.1f%% |' % (p * 100, (p - 0.26) * 100, power(0.26, p, 0.025) * 100))
    print('  対照腕の選択: N(36.7%%) -> %.1f%% / Onull(52%%) -> %.1f%%'
          % (power(0.26, 0.367, 0.025) * 100, power(0.26, 0.52, 0.025) * 100))
    print('  検出域: 対照N(18/50) k<=%d / 対照Onull(26/50) k<=%d'
          % (region(18, 0.025), region(26, 0.025)))
    print()
    print('# v0.6 §6-7 — 確証族の同時性（HE′1 の真差 24pt・HE′2 の真差 26pt）')
    print('#   Holm(m=2, a=0.05): 両方棄却 = P(両方<=0.05) - P(両方が(0.025,0.05])')
    print('#   二対比は腕を共有しないため、真値固定の下で独立。')
    a1, a2 = power(0.26, 0.50, 0.025), power(0.26, 0.52, 0.025)   # a=0.025
    b1, b2 = power(0.26, 0.50, 0.05),  power(0.26, 0.52, 0.05)    # a=0.05
    both = b1 * b2 - (b1 - a1) * (b2 - a2)
    atl  = 1 - (1 - a1) * (1 - a2)
    print('  a=0.025: HE′1 %.1f%% / HE′2 %.1f%%   a=0.05: %.1f%% / %.1f%%'
          % (a1 * 100, a2 * 100, b1 * 100, b2 * 100))
    print('  | 両方が有意 (Holm) | %.1f%% |' % (both * 100))
    print('  | 片方のみが有意    | %.1f%% |' % ((atl - both) * 100))
    print('  | 少なくとも一方    | %.1f%% |' % (atl * 100))
    print('  | いずれも有意でない | %.1f%% |' % ((1 - atl) * 100))
    print('  （参考）Bonferroni の積 = %.1f%% ← v0.5 が誤って印字した値' % (a1 * a2 * 100))

