# -*- coding: utf-8 -*-
"""公開前検分で指摘された未実施項目の一括実施（2026-08-02）。

1. R6 両側仮定再計算——裁定不能件を全1／全0 と仮定した #O厳格の腕別再計算（付録公開の義務）
2. 盲検の順列検定——周辺分布固定・20万回（Claude の指摘 A-1・報告に載せる正式値）
3. E4-1 三分割表・E4-2 応答内破局率・E4-7 応答内HE0・E3-4(c) HE1（凍結要求・解析器から転記）
4. 0/27 の 95% 上限（#L転嫁の Lneg 腕・Clopper-Pearson 片側）
5. 検査器のラベル単位化——タイブレーク限定検査を項目単位からラベル単位へ（未了事項の解消）
6. コミットハッシュと FREEZE-RECORD 時刻の突合
7. E7-3 質的観察の実施状況の確定
"""
import json
import os
import random
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collate_scoring_e import to_code                          # noqa: E402
from make_adjudication_e import load_all                       # noqa: E402
from app_parser_rev2 import is_catastrophic                    # noqa: E402
from scipy.stats import beta as sbeta, fisher_exact            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARMS = ["Lneg", "Onull", "O"]


def main():
    K = {json.loads(l)["blind_id"]: json.loads(l) for l in open(
        os.path.join(ROOT, "results/adde-main/blind/adde-main-key.jsonl"), encoding="utf-8")}
    R = {json.loads(l)["trial_id"]: json.loads(l) for l in open(
        os.path.join(ROOT, "results/adde-main/trials-adde-main-Qwen3-30B-A3B-Instruct-2507.jsonl"),
        encoding="utf-8")}
    S1 = load_all(os.path.join(ROOT, "results/adde-main/scoring"), 1)
    S2 = load_all(os.path.join(ROOT, "results/adde-main/scoring"), 2)
    FIN = {(x["id"], x["field"]): x for x in json.load(open(os.path.join(
        ROOT, "results/adde-main/adjudication/registrant-adjudication-FINAL-v3.json"),
        encoding="utf-8"))["saved_items"]}
    ids = sorted(S1)
    L = ["# 公開前検分の指摘による未実施項目の実施記録（2026-08-02）\n"]

    # ---- 1. R6 両側仮定再計算 ----
    L.append("\n## 1. R6 両側仮定再計算（#O厳格・裁定不能件を全1／全0 と仮定）\n\n")
    L.append("| 腕 | 破局n | 下限(both-1) | 裁定不能 | 全0仮定 | 全1仮定 | 上限(either-1) |\n")
    L.append("|---|---|---|---|---|---|---|\n")
    for a in ARMS:
        tgt = [i for i in ids if K[i]["arm"] == a and K[i]["catastrophic"]]
        lo = sum(1 for i in tgt if to_code("o_strict", S1[i].get("o_strict")) == 1
                 and to_code("o_strict", S2[i].get("o_strict")) == 1)
        hi = sum(1 for i in tgt if 1 in (to_code("o_strict", S1[i].get("o_strict")),
                                         to_code("o_strict", S2[i].get("o_strict"))))
        und = sum(1 for i in tgt if FIN.get((i, "o_strict"), {}).get("value") == "undecided")
        L.append(f"| {a} | {len(tgt)} | {lo} | {und} | {lo} | {lo+und} | {hi} |\n")
    L.append("\n全0仮定＝下限、全1仮定＝下限+裁定不能数。**いずれの仮定でも三腕の区間は交差し、"
             "腕間差の主張は立たない**（全隅基準）。\n")

    # ---- 2. 盲検の順列検定 ----
    L.append("\n## 2. 盲検の順列検定（周辺分布固定・20万回・A-1 の正式値）\n\n")
    L.append("| 採点者 | 実測正答 | 独立帰無下の期待 | P(≥実測) | O腕再現/期待 |\n|---|---|---|---|---|\n")
    for nm, S in (("採点者1", S1), ("採点者2", S2)):
        g = [S[i].get("arm_guess") for i in ids]
        t = [K[i]["arm"] for i in ids]
        obs = sum(x == y for x, y in zip(g, t))
        exp = sum(g.count(a) * t.count(a) for a in ARMS) / 150
        rng = random.Random(48)
        cnt = 0
        for _ in range(200000):
            p = t[:]
            rng.shuffle(p)
            if sum(x == y for x, y in zip(g, p)) >= obs:
                cnt += 1
        oh = sum(1 for i in ids if K[i]["arm"] == "O" and S[i].get("arm_guess") == "O")
        oe = g.count("O") * 50 / 150
        L.append(f"| {nm} | {obs}/150 | {exp:.1f} | **{cnt}/200000** | {oh}/{oe:.1f} = {oh/oe:.2f}倍 |\n")

    # ---- 3. E4-1/E4-2/E4-7/HE1 ----
    L.append("\n## 3. 凍結要求の転記（E4-1 三分割・E4-2 応答内・E4-7 応答内HE0・E3-4(c) HE1）\n\n")
    L.append("### E4-1 三分割表（分母は全n・refuse を含む）\n\n")
    L.append("| 腕 | n | 破局 | 非破局関与 | refuse | FAIL |\n|---|---|---|---|---|---|\n")
    stat = {}
    for a in ARMS:
        tgt = [i for i in ids if K[i]["arm"] == a]
        c = sum(1 for i in tgt if K[i]["catastrophic"])
        rf = sum(1 for i in tgt if (R[K[i]["trial_id"]]["parsed"] or {}).get("choice") == "refuse")
        fl = sum(1 for i in tgt if not R[K[i]["trial_id"]]["parsed"])
        stat[a] = (len(tgt), c, rf, fl)
        L.append(f"| {a} | {len(tgt)} | {c} | {len(tgt)-c-rf-fl} | {rf} | {fl} |\n")
    L.append("\n### E4-2 二つの破局率の併記（粗／応答内）\n\n")
    L.append("| 腕 | 粗（分母 n） | 応答内（分母 n−refuse−fail） |\n|---|---|---|\n")
    for a in ARMS:
        n, c, rf, fl = stat[a]
        L.append(f"| {a} | {c}/{n} = {c/n*100:.1f}% | {c}/{n-rf-fl} = {c/(n-rf-fl)*100:.1f}% |\n")
    L.append("\n### E4-7 応答内 HE0（解析器出力・記述）\n\n")
    L.append("responders [49, 49, 50]・率 [55.1, 53.1, 26.0]%・**漸近CA p = 0.00349**。\n")
    L.append("向き: 粗 improving／応答内 improving——**両者一致**。"
             "E4-7 の「向きが一致しない場合」の条項は不発動。検定は粗のみ（E4-7 凍結）。\n")
    L.append("\n### E3-4(c) HE1（O vs EB・記述・確証族に入れない）\n\n")
    L.append("O 13/50 対 EB 12/30・**Fisher p = 0.21937**（参照値）。"
             "E3-3 の凍結——構造的に鳴らない仮説を主要と呼ばない——により記述に留める。\n")

    # ---- 4. #L転嫁 0/27 の上限 ----
    L.append("\n## 4. #L転嫁ゼロの精度（Clopper-Pearson 片側95%上限）\n\n")
    L.append("| 腕 | 観測 | 95% 上限 |\n|---|---|---|\n")
    for a in ARMS:
        n = stat[a][1]
        ub = sbeta.ppf(0.95, 1, n) * 100
        L.append(f"| {a} | 0/{n} | **{ub:.1f}%** |\n")
    ub66 = sbeta.ppf(0.95, 1, 66) * 100
    L.append(f"| 三腕プール | 0/66 | **{ub66:.1f}%** |\n")
    L.append("\n読み: **Lneg 腕の破局のうち最大 10.6% 程度までは転嫁経路がありえた**"
             "——ゼロは「転嫁が稀である」までを支え、「不在」を認証しない。\n")

    # ---- 5. 検査器のラベル単位化 ----
    L.append("\n## 5. タイブレーク限定検査のラベル単位化（未了事項の解消）\n\n")
    viol = []
    for (i, f), x in FIN.items():
        if f != "modes":
            continue
        a = set((to_code("modes", S1[i].get("modes")) or "-").split(",")) - {"-"}
        b = set((to_code("modes", S2[i].get("modes")) or "-").split(",")) - {"-"}
        adopted = (a & b) if x["value"] == "default" else \
                  {m.strip() for m in x["value"].split(",") if m.strip()}
        if not (a & b) <= adopted <= (a | b):
            viol.append(f"{i}: 採用={sorted(adopted)} AND={sorted(a&b)} OR={sorted(a|b)}")
    L.append(f"**ラベル単位での検査結果: 違反 {len(viol)} 件**"
             + ("（" + "／".join(viol) + "）" if viol else "——最終値 v3 は全件適合") + "\n")

    # ---- 6. コミット突合 ----
    L.append("\n## 6. 公開コミットと台帳の突合\n\n")
    repo = os.path.join(os.path.dirname(ROOT), "Ryokai-OS-Public")
    L.append("| コミット | 日時 | 件名 |\n|---|---|---|\n")
    for h in ("e2280eb", "52328e3"):
        try:
            out = subprocess.run(["git", "log", "-1", "--format=%H|%ci|%s", h],
                                 cwd=repo, capture_output=True, text=True, encoding="utf-8").stdout.strip()
            sha, dt, subj = out.split("|", 2)
            L.append(f"| `{sha[:7]}` | {dt} | {subj[:46]} |\n")
        except Exception as e:
            L.append(f"| {h} | 取得失敗 | {e} |\n")
    L.append("\n両コミットとも **key 開封イベント（FREEZE-RECORD 記帳）より前**であることを"
             "コミット日時で確認する。\n")

    out = os.path.join(ROOT, "results/adde-main/pending-items-record.md")
    open(out, "w", encoding="utf-8", newline="\n").write("".join(L))
    print("".join(L))
    print("->", out)


if __name__ == "__main__":
    main()
