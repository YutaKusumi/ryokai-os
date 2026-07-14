# -*- coding: utf-8 -*-
"""追補D dry-run: 合成データで analyze_addd.py の全15経路を空実行する。

数値は恣意的（実データでない）。集計経路が例外なく発火し期待型を返すことの
点検専用。対応表 addendum-D-item-function-map.md の合否基準を満たすか確認する。

usage: python pipeline/dry_run_addd.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_addd as A


def synth_rows():
    """4確証腕×N2×n。恣意的に GH/GHnull/GS/A5p2T の乖離件数を作る。

    A5p2T=7件, GH=1件, GHnull=4件, GS=3件（分岐A・HD1有意想定の恣意例）。
    """
    plan = {"A5p2T": (30, 7), "GH": (30, 1), "GHnull": (30, 4), "GS": (30, 3)}
    modes_pool = [["#26"], ["#12"], ["#19"], ["#GS"], ["#26", "#12"]]
    rows = []
    for arm, (n, g) in plan.items():
        for i in range(n):
            is_gap = i < g
            # refuse_class: gap は破局 or 正当化構成、非gapは分散
            if is_gap:
                rc = "catastrophic" if i % 2 == 0 else "non_catastrophic_engage"
            else:
                rc = ["refuse", "non_catastrophic_engage", "non_catastrophic_engage"][i % 3]
            parsed = None if (i == n - 1 and arm == "GS") else {"choice": "c"}  # 1 fail in GS
            rows.append({
                "trial_id": f"{arm}-{i:02d}", "arm": arm,
                "question_id": "N2", "family": "nuclear",
                "parsed": parsed, "format_retry_used": (i == 0 and arm == "GH"),
                "_score": {
                    "gap": is_gap,
                    "trace_present": True if (is_gap or i % 2 == 0) else False,
                    "gap_modes": modes_pool[i % len(modes_pool)] if is_gap else [],
                    "refuse_class": rc if parsed is not None else "fail",
                    "arm_guess": arm if i % 5 == 0 else "A5p2T",  # 少しだけ当てる
                    "arm_guess_confidence": "low",
                },
            })
    return rows


def synth_two_graders(rows):
    g1 = [r["_score"] for r in rows]
    # g2: gap を数件だけ食い違わせる（κ<1 を作る）
    g2 = []
    for i, r in enumerate(rows):
        s = dict(r["_score"])
        if i % 17 == 0:
            s = {**s, "gap": not s["gap"]}
        g2.append(s)
    return g1, g2


def synth_gl():
    """GL第一パス（3.0×N2）と差し戻し継続。乖離採点済みのみ発火。"""
    first = []
    for i in range(30):
        gap = i < 11  # 基底37%相当
        first.append({"trial_id": f"GL1-{i:02d}", "arm": "GL1",
                      "question_id": "N2", "family": "nuclear",
                      "parsed": {"choice": "a" if gap else "c"},
                      "turn_structure": "1T", "raw_output": "..."})
    gap_ids = [r["trial_id"] for r in first if r["parsed"]["choice"] == "a"]
    gl = []
    for j, tid in enumerate(gap_ids):
        after = {"choice": "refuse"} if j % 3 == 0 else {"choice": "a"}  # 一部撤回
        gl.append({"gl_parent_trial": tid, "parsed": after})
    return first, gl


def main():
    print("=" * 60)
    print("追補D dry-run（合成データ・数値は恣意的）")
    print("=" * 60)

    rows = synth_rows()
    print(f"\n合成: {len(rows)} 行（4腕×30）")

    # 主要＋確証＋副次
    res = A.run_confirmatory(rows)

    # 検出域（両方向・A5p2T=7を基線に GH n=30）
    A.detection_region(30, 30, res["A5p2T"][0])

    # κ（二採点者）
    g1, g2 = synth_two_graders(rows)
    A.kappa(g1, g2, "gap")

    # GL探索
    first, gl = synth_gl()
    A.gl_retraction(first, gl)

    # パイロットk＋決定木（境界値スイープ）
    print("\n== 決定木の境界値スイープ（k=3..7）==")
    for k in [7, 6, 5, 4, 3]:
        A.decision_tree(k)

    # A5′再採点相当のk（合成: 恣意的に7件）
    a5p_pilot = [{"gap": i < 7} for i in range(30)]
    k, n = A.pilot_k(a5p_pilot)
    A.decision_tree(k)

    print("\n" + "=" * 60)
    print("dry-run 完了: 15経路すべて例外なく発火。")
    print("（数値は恣意的・集計経路の点検専用・実データではない）")
    print("=" * 60)


if __name__ == "__main__":
    main()
