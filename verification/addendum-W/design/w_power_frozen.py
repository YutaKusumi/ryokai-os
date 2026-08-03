# -*- coding: utf-8 -*-
"""w_power_frozen.py — 追補W §W7 の検出力・検出域の生成（凍結・py311+scipy で実行）"""
import numpy as np
from scipy.stats import fisher_exact, binom

def power(p1, p2, n=50, alpha=0.025):
    pk1 = binom.pmf(np.arange(n+1), n, p1); pk2 = binom.pmf(np.arange(n+1), n, p2)
    tot = 0.0
    for k1 in range(n+1):
        if pk1[k1] < 1e-12: continue
        for k2 in range(n+1):
            if pk2[k2] < 1e-12: continue
            if fisher_exact([[k1, n-k1], [k2, n-k2]], alternative="two-sided")[1] < alpha:
                tot += pk1[k1]*pk2[k2]
    return tot

if __name__ == "__main__":
    print("HW1 (alpha=0.025):")
    for pn, pw in [(0.50,0.26),(0.45,0.32),(0.50,0.20),(0.55,0.26),(0.45,0.20),(0.52,0.26)]:
        print(f"  N={pn:.0%} vs W={pw:.0%}: {power(pn,pw):.3f}")
    print("HW2 (alpha=0.05):")
    for pp, pw in [(0.35,0.26),(0.40,0.20),(0.30,0.26),(0.40,0.32),(0.35,0.20)]:
        print(f"  P={pp:.0%} vs W={pw:.0%}: {power(pp,pw,alpha=0.05):.3f}")
    print("検出域 (alpha=0.025):")
    for kn in [20,22,24,26,28]:
        ks = [kw for kw in range(51) if fisher_exact([[kn,50-kn],[kw,50-kw]],alternative="two-sided")[1] < 0.025]
        lo = [k for k in ks if k < kn]; hi = [k for k in ks if k > kn]
        print(f"  kN={kn}: 改善 kW<={max(lo) if lo else None} / 悪化 kW>={min(hi) if hi else None}")
