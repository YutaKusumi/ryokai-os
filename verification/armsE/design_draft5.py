# -*- coding: utf-8 -*-
"""追補E draft5 の設計定数と、本文の全数表の【唯一の生成源】。

【過失19 への構造的対処】同じ失敗が三度起きた:
  draft3: 8件の誤りが照合器 69/69 を通過（うち2件は設計変更の波及更新漏れ＝過失18）
  draft4: 段列と n 梯子に撤回済み α=0.0167 が残存し 72/72 を通過（過失19・三者が独立検出)
「本文に数値を書き、照合器が代表点を突く」方式は、針を刺し忘れた数値を守れない。
draft5 からは方式を変える——**設計定数をこのファイルに一元化し、本文の数表は
すべてここから生成する。照合器は数表を再生成して本文と逐語差分照合する。**
n や α を変えれば、全ての数表が同時に変わり、本文が古ければ照合が落ちる。
「針を刺し忘れる」という失敗の余地そのものを消す。

使い方:  python armsE/design_draft5.py          # 全数表を出力
"""
import os
import sys

from scipy.stats import binom, fisher_exact

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline"))
from trend_exact import trend_exact_p, trend_direction  # noqa: E402

# ============================== 設計定数（凍結） ==============================
N_EB = 30          # 基線腕（ゲート・GL1 再現性）
N = 50             # 主要3腕 {Lneg, Onull, O} の各 n
ALPHA1 = 0.025     # Holm m=2 {HE0, HE2} の初段
ALPHA2 = 0.05      # Holm 二段
ANCHOR_OR = 2.3    # 一段あたり設計効果量（追補B A5×N2 K2→K3・E2-2 参照）
MID = 0.45         # 想定中央基底率（追補C/D プール実測 27/60）
GATE_A = 6         # 分岐A: EB >= 6/30（検出力 >= 80% を供給する最小の EB）
GATE_B_LO = 4      # 分岐B: 4 <= EB <= 5
GATE_C_HI = 3      # 分岐C: EB <= 3
G4_TRIGGER = 6     # |EB - 16| >= 6 で基線再取得

# 合算 n=60 での分岐閾値は【率の保存で導出する】（手入力しない——過失20 への対処）。
# C: 率 <= GATE_C_HI/30（=10%）を保つ最大の k → 6/60。
# A: 率 >= GATE_A/30（=20%）を満たす最小の k → 12/60。
# B: その間（7〜11/60）。粗い側の隙間（7/60=11.7%・11/60=18.3%）は B に落ちる——
#    検出力原理でも同じ帰結（7/60 中心→61.4% は C 帯天井 54.3% を超え、
#    11/60 中心→79.9% は 80% 未満。いずれも「登録者裁定」帯に属する）。
G4_C_HI = (GATE_C_HI * 60) // 30          # = 6
G4_A = -(-GATE_A * 60 // 30)              # = 12（天井関数）
G4_B_LO = G4_C_HI + 1                     # = 7
TOTAL = N_EB + 3 * N                # = 180 試行（G4 発火時 +30 = 210）

_cache = {}


def tp(a, b, c, n=None):
    n = N if n is None else n
    k = (n, a + b + c, abs((b + 2 * c) - (a + b + c)))
    if k not in _cache:
        _cache[k] = trend_exact_p(a, b, c, n)
    return _cache[k]


def power(ps, n=None, al=ALPHA1):
    n = N if n is None else n
    m = [[binom.pmf(k, n, p) for k in range(n + 1)] for p in ps]
    tot = 0.0
    for a in range(n + 1):
        if m[0][a] < 1e-12:
            continue
        for b in range(n + 1):
            if m[0][a] * m[1][b] < 1e-12:
                continue
            for c in range(n + 1):
                if m[0][a] * m[1][b] * m[2][c] < 1e-13:
                    continue
                if tp(a, b, c, n) < al:
                    tot += m[0][a] * m[1][b] * m[2][c]
    return tot


def pw(p1, p2, n=None, al=ALPHA1):
    n = N if n is None else n
    m1 = [binom.pmf(k, n, p1) for k in range(n + 1)]
    m2 = [binom.pmf(k, n, p2) for k in range(n + 1)]
    tot = 0.0
    for a in range(n + 1):
        for b in range(n + 1):
            if m1[a] * m2[b] < 1e-13:
                continue
            if fisher_exact([[a, n - a], [b, n - b]])[1] < al:
                tot += m1[a] * m2[b]
    return tot


def type1(p0, n=None, al=ALPHA1):
    n = N if n is None else n
    m = [binom.pmf(k, n, p0) for k in range(n + 1)]
    tot = 0.0
    for a in range(n + 1):
        if m[a] < 1e-13:
            continue
        for b in range(n + 1):
            if m[a] * m[b] < 1e-13:
                continue
            for c in range(n + 1):
                if m[a] * m[b] * m[c] < 1e-14:
                    continue
                if tp(a, b, c, n) < al:
                    tot += m[a] * m[b] * m[c]
    return tot


def grad(p, r=ANCHOR_OR):
    o = p / (1 - p)
    return (o * r / (1 + o * r), p, (o / r) / (1 + o / r))


# ============================== 数表の生成 ==============================

def t_gate():
    """E2-4: ゲート表。EB(n=30) 観測値 -> 主要3腕 n=50 の HE0 検出力と分岐。"""
    rows = ["| EB | 基底率 | HE0 検出力（n=50・α=0.025・対称OR2.3） | 分岐 |",
            "|---:|---:|---:|---|"]
    for k in range(3, 17):
        pv = power(grad(k / 30)) * 100
        br = "**A**" if k >= GATE_A else ("B" if k >= GATE_B_LO else "**C**")
        bold = "**" if k in (GATE_C_HI, GATE_A) else ""
        rows.append(f"| {bold}{k}/30{bold} | {k/30*100:.1f}% | {bold}{pv:.1f}%{bold} | {br} |")
    return "\n".join(rows)


def t_branch_prob():
    """E2-4: 分岐の事前確率（G4 の再取得は織り込まない近似）。"""
    out = []
    for p0 in [0.367, 0.45, 0.533]:
        B = sum(binom.pmf(x, N_EB, p0) for x in range(GATE_B_LO, GATE_A)) * 100
        C = binom.cdf(GATE_C_HI, N_EB, p0) * 100
        out.append(f"真率{p0*100:.1f}%なら P(B)={B:.2f}%・P(C)={C:.3f}%")
    return "／".join(out)


def t_type1():
    """E3-4(a): 第一種過誤（n=50・α=0.025・厳密列挙）。"""
    vals = [f"{p0:.2f} で **{type1(p0):.5f}**" for p0 in [0.20, 0.30, 0.45, 0.53]]
    return "真率 " + "／".join(vals) + "。**全て名目 0.025 を下回る（保守的）。**"


def t_powerattr():
    """E2-5: 検出力の帰属表（n=50・α=0.025・全列同一 α）。"""
    rows = ["| 真の型 | 両端の隔たり | **HE0** | Lneg vs O 対比較 | Lneg–Onull | Onull–O |",
            "|---|---:|---:|---:|---:|---:|"]
    for lab, ps in [("対称 OR2.3（65/45/26%）", grad(MID)),
                    ("片側・Lneg のみ（70/45/45%）", (0.70, MID, MID)),
                    ("片側・Lneg のみ（65/45/45%）", (0.65, MID, MID)),
                    ("片側・O のみ（45/45/25%）", (MID, MID, 0.25)),
                    ("片側・Lneg のみ（60/45/45%）", (0.60, MID, MID)),
                    ("片側・O のみ（45/45/30%）", (MID, MID, 0.30))]:
        span = (ps[0] - ps[2]) * 100
        h = power(ps) * 100
        both = pw(ps[0], ps[2]) * 100
        a = pw(ps[0], ps[1]) * 100
        b = pw(ps[1], ps[2]) * 100
        rows.append(f"| {lab} | {span:.0f}pt | **{h:.1f}%** | {both:.1f}% | {a:.1f}% | {b:.1f}% |")
    return "\n".join(rows)


def t_nladder():
    """E2-6: 片側20pt（65/45/45%）を捕まえるのに要する n（α=0.025）。"""
    rows = ["| n/腕 | 片側20ptの検出力 | 主要3腕の試行数 |", "|---:|---:|---:|"]
    for n in [50, 80, 100, 120]:
        rows.append(f"| {'**' if n == N else ''}{n}{'**' if n == N else ''} "
                    f"| {power((0.65, MID, MID), n)*100:.1f}% | {n*3} |")
    return "\n".join(rows)


def t_rep():
    """E3-4(a): 代表例（監査者の手検算用・n=50）。"""
    rows = ["| Lneg | Onull | O | 厳密 p | 向きラベル | α=.025 |",
            "|---:|---:|---:|---:|---|---|"]
    for c in [(25, 25, 25), (33, 26, 19), (36, 26, 16), (38, 28, 26), (37, 27, 26),
              (29, 26, 26), (26, 26, 19), (16, 26, 36), (40, 10, 25)]:
        p = tp(*c)
        sig = "**有意**" if p < ALPHA1 else ""
        rows.append(f"| {c[0]} | {c[1]} | {c[2]} | {p:.5f} | `{trend_direction(*c)}` | {sig} |")
    return "\n".join(rows)


def t_c1sens():
    """E3-2(a): c1 は周辺 R を通じてのみ効く（n=50 の実例）。"""
    vals = [f"c₁={x} → p={tp(35, x, 18):.5f}" for x in [0, 13, 26, 39, 50]]
    return "（c₀=35, c₂=18 固定）" + "／".join(vals)


def t_he2():
    """E3-4(b): HE2（O vs Onull・n=50 同士・Fisher 両側）の検出域。"""
    rows = ["| Onull | 改善 k\\*(.025) | 改善 k\\*(.05) | 悪化 (.025) |",
            "|---:|---:|---:|---:|"]
    for base in range(15, 36, 3):
        k25 = k05 = -1
        for k in range(0, base + 1):
            pv = fisher_exact([[base, N - base], [k, N - k]])[1]
            if pv < ALPHA1:
                k25 = k
            if pv < ALPHA2:
                k05 = k
        w25 = 99
        for k in range(N, base - 1, -1):
            if fisher_exact([[base, N - base], [k, N - k]])[1] < ALPHA1:
                w25 = k
        rows.append(f"| {base}/50 | ≤{k25} | ≤{k05} | {'≥' + str(w25) if w25 <= N else 'none'} |")
    return "\n".join(rows)


def t_e9():
    """E9: コーディネータ予想帯の p 値（n=50）。"""
    lines = [f"（{c[0]},{c[1]},{c[2]}）→ p={tp(*c):.3f}"
             for c in [(34, 27, 26), (36, 27, 26), (38, 28, 26)]]
    thr = next(L for L in range(30, 50) if tp(L, 27, 26) < ALPHA1)
    return "／".join(lines) + f"。Onull=27・O=26 のとき有意到達は **Lneg ≥ {thr}/50（{thr/50*100:.0f}%）** から"


def t_g4():
    """E2-4: G4 合算閾値の凍結行（導出値・生成される）。"""
    a6 = power(grad(G4_B_LO / 60)) * 100      # 7/60 中心の検出力
    a11 = power(grad((G4_A - 1) / 60)) * 100  # 11/60 中心の検出力
    c6 = power(grad(G4_C_HI / 60)) * 100      # 6/60 中心の検出力
    return (f"**合算 n=60 に対する分岐閾値: A ≥ {G4_A}/60・B {G4_B_LO}〜{G4_A-1}/60・C ≤ {G4_C_HI}/60**"
            f"（率の保存による導出——C は率 ≤10% を保つ最大の {G4_C_HI}/60・A は率 ≥20% の最小の {G4_A}/60。"
            f"隙間の {G4_B_LO}/60〔11.7%・検出力 {a6:.1f}%〕と {G4_A-1}/60〔18.3%・{a11:.1f}%〕は、"
            f"検出力原理でも C 帯天井 {c6:.1f}% と A 基準 80% の間に落ちるため B〔登録者裁定〕に属する）")


def t_scalars():
    """本文に散在する主要スカラー値（照合器が使う）。"""
    return {
        "sym_he0": round(power(grad(MID)) * 100, 1),          # 95.8
        "sym_both": round(pw(grad(MID)[0], grad(MID)[2]) * 100, 1),  # 94.0
        "he2_power": round(pw(MID, grad(MID)[2]) * 100, 1),   # 32.2 (Onull–O 対称時)
        "step_lneg": round(pw(grad(MID)[0], MID) * 100, 1),   # 33.3 (Lneg–Onull 対称時)
        "oneside20": round(power((0.65, MID, MID)) * 100, 1),  # 38.2
        "oneside25": round(power((0.70, MID, MID)) * 100, 1),  # 58.6
        "n80_for80": round(power((0.65, MID, MID), 120) * 100, 1),  # 80.6 at n=120
        "branchB_n80": round(power(grad(5 / 30), 80) * 100, 1),      # 94.3
        "branchB_n50": round(power(grad(5 / 30), 50) * 100, 1),      # 76.5
    }


if __name__ == "__main__":
    print(f"設計定数: N_EB={N_EB} N={N} α1={ALPHA1} α2={ALPHA2} OR={ANCHOR_OR} "
          f"ゲート A≥{GATE_A}/B={GATE_B_LO}-{GATE_A-1}/C≤{GATE_C_HI} "
          f"G4合算 A≥{G4_A}/B={G4_B_LO}-{G4_A-1}/C≤{G4_C_HI} 総試行={TOTAL}\n")
    for name, fn in [("GATE", t_gate), ("BRANCH_PROB", t_branch_prob), ("TYPE1", t_type1),
                     ("POWERATTR", t_powerattr), ("NLADDER", t_nladder), ("REP", t_rep),
                     ("C1SENS", t_c1sens), ("HE2", t_he2), ("E9", t_e9), ("G4", t_g4)]:
        print(f"===== {name} =====")
        print(fn())
        print()
    print("===== SCALARS =====")
    for k, v in t_scalars().items():
        print(f"  {k} = {v}")
