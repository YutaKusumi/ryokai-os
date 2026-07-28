# -*- coding: utf-8 -*-
"""生成源の独立検算（E8 凍結事項・第3巡監査の標準手続き化）。

`design_draft5.py`・`trend_exact.py` を【import しない】。厳密検定・検出力・
第一種過誤をここで一から書き直し（math.comb 直書き・ループ構造も別）、
凍結された主要スカラーと突合する。単一生成源の耐性は、外部の二重実装が
あって初めて成立する（Claude観自在・観自在の答申・2026-07-28）。

使い方: python armsE/verify_design_independent.py
"""
import sys
from math import comb

from scipy.stats import binom, fisher_exact   # 外部ライブラリは生成源ではないため可

N = 50
A1 = 0.025

ng = []


def chk(label, got, want, tol=0.051):
    ok = abs(got - want) <= tol
    ng.append(None if ok else label)
    print(f"[{'OK ' if ok else 'NG '}] {label}: 独立再計算 {got:.4f} / 凍結値 {want}")


# ---- 厳密検定の独立実装（c2 外側ループ・logなし・trend_exact.py と別構造） ----
def exact_p(c0, c1, c2, n):
    R = c0 + c1 + c2
    if R == 0 or R == 3 * n:
        return 1.0
    dev = abs(c2 - c0)            # |T-R| = |c2-c0|（代数はFROZEN E3-2(a)で開示済み）
    denom = comb(3 * n, R)
    tot = 0
    for x2 in range(max(0, R - 2 * n), min(n, R) + 1):
        for x0 in range(max(0, R - x2 - n), min(n, R - x2) + 1):
            x1 = R - x2 - x0
            if abs(x2 - x0) >= dev:
                tot += comb(n, x0) * comb(n, x1) * comb(n, x2)
    return tot / denom


_pc = {}


def exact_p_cached(c0, c1, c2, n):
    key = (n, c0 + c1 + c2, abs(c2 - c0))
    if key not in _pc:
        _pc[key] = exact_p(c0, c1, c2, n)
    return _pc[key]


def power_he0(p_l, p_m, p_o, n=N, al=A1):
    """独立実装: 各腕二項の同時分布で HE0 有意確率を積算（枝刈り閾値も別の値）。"""
    pm = [[binom.pmf(k, n, p) for k in range(n + 1)] for p in (p_l, p_m, p_o)]
    tot = 0.0
    for a in range(n + 1):
        wa = pm[0][a]
        if wa < 5e-13:
            continue
        for b in range(n + 1):
            wab = wa * pm[1][b]
            if wab < 5e-13:
                continue
            for c in range(n + 1):
                w = wab * pm[2][c]
                if w < 5e-14:
                    continue
                if exact_p_cached(a, b, c, n) < al:
                    tot += w
    return tot


def power_fisher(p1, p2, n=N, al=A1):
    m1 = [binom.pmf(k, n, p1) for k in range(n + 1)]
    m2 = [binom.pmf(k, n, p2) for k in range(n + 1)]
    tot = 0.0
    for a in range(n + 1):
        for b in range(n + 1):
            w = m1[a] * m2[b]
            if w < 5e-13:
                continue
            if fisher_exact([[a, n - a], [b, n - b]])[1] < al:
                tot += w
    return tot


def type1(p0, n=N, al=A1):
    pm = [binom.pmf(k, n, p0) for k in range(n + 1)]
    tot = 0.0
    for a in range(n + 1):
        if pm[a] < 5e-13:
            continue
        for b in range(n + 1):
            if pm[a] * pm[b] < 5e-13:
                continue
            for c in range(n + 1):
                w = pm[a] * pm[b] * pm[c]
                if w < 5e-14:
                    continue
                if exact_p_cached(a, b, c, n) < al:
                    tot += w
    return tot


def grad(p, r=2.3):
    o = p / (1 - p)
    return (o * r / (1 + o * r), p, (o / r) / (1 + o / r))


print("=== 生成源の独立検算（design_draft5.py 非import・別実装） ===\n")

print("-- 代表 p 値（FROZEN 代表表・4点） --")
chk("(38,28,26) p", exact_p(38, 28, 26, 50), 0.01811, 0.00003)
chk("(37,27,26) p", exact_p(37, 27, 26, 50), 0.03212, 0.00003)
chk("(40,10,25) p", exact_p(40, 10, 25, 50), 0.00363, 0.00003)
chk("(33,26,19) p", exact_p(33, 26, 19, 50), 0.00678, 0.00003)

print("\n-- 主要スカラー（%） --")
g = grad(0.45)
chk("対称OR2.3 の HE0 検出力", power_he0(*g) * 100, 95.8)
chk("Lneg vs O 対比較", power_fisher(g[0], g[2]) * 100, 94.0)
chk("HE2（Onull–O 対称時）", power_fisher(0.45, g[2]) * 100, 32.2)
chk("Lneg–Onull の段", power_fisher(g[0], 0.45) * 100, 33.3)
chk("片側20pt（65/45/45）", power_he0(0.65, 0.45, 0.45) * 100, 38.2)

print("\n-- 第一種過誤（厳密） --")
chk("真率0.45", type1(0.45), 0.02035, 0.00003)

print("\n-- ゲート境界（EB→n=50 検出力・%） --")
chk("EB=5/30 (76.5)", power_he0(*grad(5 / 30)) * 100, 76.5)
chk("EB=6/30 (82.8)", power_he0(*grad(6 / 30)) * 100, 82.8)

print("\n-- G4 合算境界（/60 中心率・%） --")
chk("6/60 (54.3・C帯天井)", power_he0(*grad(6 / 60)) * 100, 54.3)
chk("7/60 (61.4・B帯)", power_he0(*grad(7 / 60)) * 100, 61.4)
chk("11/60 (79.9・B帯)", power_he0(*grad(11 / 60)) * 100, 79.9)
chk("12/60 (82.8・A帯)", power_he0(*grad(12 / 60)) * 100, 82.8)

print("\n（申告: n=80/120 の梯子セルは計算量のため本器では検算しない——"
      "第3巡で阿弥陀如来が独立検算済み〔59.8/69.5/80.6・94.3〕）")

fails = [x for x in ng if x]
print("\n" + "=" * 60)
print(f"独立検算: {len([x for x in ng if x is None])}/{len(ng)} 一致"
      + ("" if not fails else "  ** 不一致: " + str(fails)))
print("=" * 60)
sys.exit(1 if fails else 0)
