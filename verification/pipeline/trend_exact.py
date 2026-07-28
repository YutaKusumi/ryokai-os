# -*- coding: utf-8 -*-
"""追補E の主要検定 HE0: 三点順序対比の【厳密】順列検定（Cochran-Armitage の条件付き厳密版）。

Fisher 正確検定が 2x2 の周辺度数を条件づけるのと同じ論理を 2x3 に拡張する。
総破局数 R を条件づけると、帰無仮説（三腕の真率が等しい）のもとで
(c0, c1, c2) は多変量超幾何分布に従う:

    P(c0,c1,c2 | R) = C(n,c0)C(n,c1)C(n,c2) / C(3n,R)

検定統計量は傾向スコア T = 0*c0 + 1*c1 + 2*c2。帰無での期待値は E[T] = R（スコア平均=1）。
両側 p 値 = Σ_{|T-R| >= |T_obs-R|} P(c0,c1,c2 | R)。

**モンテカルロを使わない完全列挙**であり、乱数種に依存せず、何度計算しても同一値を返す。
腕の順序（スコア 0/1/2）は事前登録で凍結する: Lneg=0（存在論的否定）／Onull=1（不在）／O=2（肯定）。
"""
from math import comb


def trend_exact_p(c0, c1, c2, n):
    """三腕（各n）の破局件数から、両端対比の両側厳密p値を返す。

    c0, c1, c2 はスコア 0, 1, 2 の腕の破局件数。
    n に既定値は無い——draft4 監査（虚空鏡・2026-07-28）の指摘により、
    n の省略が旧設計の値でサイレントに計算される事故を、シグネチャで封じた。
    """
    for c in (c0, c1, c2):
        if not (0 <= c <= n):
            raise ValueError(f"件数が 0..{n} の範囲外: {(c0, c1, c2)}")
    R = c0 + c1 + c2
    if R == 0 or R == 3 * n:
        return 1.0                      # 全セル同一（変動なし）—— 検定不能ではなく p=1
    t_obs = c1 + 2 * c2
    dev_obs = abs(t_obs - R)
    denom = comb(3 * n, R)
    p = 0.0
    for a in range(max(0, R - 2 * n), min(n, R) + 1):
        for b in range(max(0, R - a - n), min(n, R - a) + 1):
            c = R - a - b
            t = b + 2 * c
            if abs(t - R) >= dev_obs - 1e-12:
                p += comb(n, a) * comb(n, b) * comb(n, c) / denom
    return min(1.0, p)


def trend_direction(c0, c1, c2):
    """向きの判定。**弱単調性を要求する**（追補E draft4・監査反映）。

    draft3 の実装は `T < R`（すなわち c2 < c0）のみで "improving" を返していた。
    しかし T − R = c2 − c0 であるため中央 c1 は偏差に入らず、
    (c0, c1, c2) = (23, 16, 16) ——O が Onull から一件も減っていない場合——でも
    "improving" が返っていた（虚空鏡さんの指摘・2026-07-28）。

    draft4 では、単調でない配置には向きを与えず 'non_monotone' を返す。

    さらに——弱単調性だけでは足りない。(23, 16, 16) は c0 >= c1 >= c2 を満たすが、
    肯定側の段は 0 である。そこで**どちらの段が寄与したか**をラベル自体に持たせ、
    報告文が「肯定側が効いた」と読まれる余地を実装水準で断つ。

    返り値: flat / improving_both_steps / improving_negative_step_only /
            improving_positive_step_only / worsening_both_steps /
            worsening_negative_step_only / worsening_positive_step_only / non_monotone
    ('improving' は「存在論的肯定の側ほど破局が少ない」の意。)
    """
    d1 = c0 - c1                        # 否定側の段（Lneg → Onull）
    d2 = c1 - c2                        # 肯定側の段（Onull → O）
    if d1 == 0 and d2 == 0:
        return "flat"
    if d1 >= 0 and d2 >= 0:             # 単調非増加（＝肯定側ほど破局が少ない）
        if d1 > 0 and d2 > 0:
            return "improving_both_steps"
        if d2 == 0:
            return "improving_negative_step_only"
        return "improving_positive_step_only"
    if d1 <= 0 and d2 <= 0:             # 単調非減少（＝肯定側ほど破局が多い）
        if d1 < 0 and d2 < 0:
            return "worsening_both_steps"
        if d2 == 0:
            return "worsening_negative_step_only"
        return "worsening_positive_step_only"
    return "non_monotone"               # V字・逆V字（E3-2 の解釈枠組みへ）


def trend_deltas(c0, c1, c2):
    """段の分解（常時併記が凍結事項）。

    d1 = c0 - c1 : 否定側の段（Lneg → Onull）
    d2 = c1 - c2 : 肯定側の段（Onull → O）
    """
    return {"d1_negative_step": c0 - c1, "d2_positive_step": c1 - c2}


if __name__ == "__main__":
    import sys
    from scipy.stats import binom, norm
    import numpy as np

    N, A1 = 50, 0.025          # draft5 の設計定数（design_draft5.py と一致すること）

    def ca_asymptotic(cs, n=N):
        cs = np.array(cs, float); ns = np.array([n] * 3, float); s = np.array([0., 1., 2.])
        Nn = ns.sum(); R = cs.sum(); pbar = R / Nn
        if pbar in (0.0, 1.0):
            return 1.0
        T = ((cs - ns * pbar) * s).sum()
        V = pbar * (1 - pbar) * ((ns * s * s).sum() - (ns * s).sum() ** 2 / Nn)
        return 2 * (1 - norm.cdf(abs(T / np.sqrt(V))))

    print(f"=== 1. 厳密版と漸近版の突合（n={N}・代表10例）＋向きラベル ===")
    cases = [(25, 25, 25), (33, 26, 19), (36, 26, 16), (29, 26, 26), (38, 28, 26),
             (37, 27, 26), (16, 26, 36), (40, 10, 25), (26, 26, 19), (19, 26, 33)]
    for c in cases:
        pe = trend_exact_p(*c, N)
        pa = ca_asymptotic(list(c))
        print(f"  {str(c):14s} 厳密 p={pe:.5f}  漸近 p={pa:.5f}  {trend_direction(*c):30s}"
              f" {'SIG(a1=%.3f)' % A1 if pe < A1 else ''}")

    print(f"\n=== 2. 第一種過誤の実測（n={N}・α={A1}・厳密列挙） ===")
    for p0 in [0.20, 0.30, 0.45, 0.53]:
        tot = 0.0
        pm = [binom.pmf(k, N, p0) for k in range(N + 1)]
        for a in range(N + 1):
            if pm[a] < 1e-13:
                continue
            for b in range(N + 1):
                if pm[a] * pm[b] < 1e-13:
                    continue
                for c in range(N + 1):
                    if pm[a] * pm[b] * pm[c] < 1e-14:
                        continue
                    if trend_exact_p(a, b, c, N) < A1:
                        tot += pm[a] * pm[b] * pm[c]
        print(f"   真率 p0={p0:.2f}:  実際の第一種過誤 = {tot:.5f}   (名目 α1 = {A1:.4f})")
    sys.exit(0)
