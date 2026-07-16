# -*- coding: utf-8 -*-
"""追補D 探索的集計ランナー（分岐C・記述のみ・p値なし）。

凍結決定木の分岐C（2026-07-14発火）に従い、analyze_addd.py の記述系関数のみを
呼ぶ。hd_test()/holm()/run_confirmatory() は**呼ばない**（検定禁止・HD1-3の
方向支持への引用禁止）。GL1腕（3.0×N2・探索）も同じ記述関数で併記する。

usage: python pipeline/run_addd_exploratory.py
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_addd as A

DIR = r"results\addd-main"
TRIALS = rf"{DIR}\trials-addd-all150.jsonl"
FINAL = rf"{DIR}\final-scores-addd-150.jsonl"
KEY = rf"{DIR}\KEY-addd-150-DO-NOT-SHOW-SCORERS.jsonl"
ALL_ARMS = ["A5p2T", "GH", "GHnull", "GS", "GL1"]


def load_rows(guesser):
    trials = {json.loads(l)["trial_id"]: json.loads(l)
              for l in open(TRIALS, encoding="utf-8")}
    key = {json.loads(l)["blind_id"]: json.loads(l)
           for l in open(KEY, encoding="utf-8")}
    rows = []
    for l in open(FINAL, encoding="utf-8"):
        s = json.loads(l)
        k = key[s["blind_id"]]
        t = trials[k["trial_id"]]
        score = {"gap": s["gap"], "trace_present": s["trace_present"],
                 "gap_modes": s["gap_modes"], "refuse_class": s["refuse_class"],
                 "arm_guess": s[f"{guesser}_arm_guess"],
                 "arm_guess_confidence": s[f"{guesser}_conf"]}
        rows.append({**t, "arm": k["arm"], "_score": score})
    return rows


def load_scorer(g):
    d = {}
    for i in range(1, 6):
        for l in open(rf"{DIR}\scores-{g}-part{i}.jsonl", encoding="utf-8-sig"):
            l = l.strip()
            if l:
                r = json.loads(l)
                d[r["blind_id"]] = r
    return [d[b] for b in sorted(d)]


def main():
    print("=" * 64)
    print("追補D 探索的集計（分岐C・記述のみ・p値なし・HD1-3方向支持へ引用禁止）")
    print("裁定済み確定採点（adjudication-record-addd.md）に基づく")
    print("=" * 64)

    rows = load_rows("g1")

    # 主要エンドポイント（記述・確証4腕＋GL1探索を併記）
    A.gap_counts(rows, arms=ALL_ARMS)
    print("  注: 分岐Cにより検定なし。GL1は探索腕（3.0×N2・比較でなく記述）。")

    A.gap_modes(rows, arms=ALL_ARMS)
    A.refuse_fourway(rows, arms=ALL_ARMS)

    res = {arm: (sum(1 for r in rows if r["arm"] == arm and r["_score"]["gap"]),
                 sum(1 for r in rows if r["arm"] == arm)) for arm in ALL_ARMS}
    A.direction_only(res)
    print("  注: 上の方向観察も分岐Cの探索であり、HD1-3の支持証拠に引用しない。")

    # κ（裁定前の生スコアどうし・裁定の影響を受けない）
    g1, g2 = load_scorer("G1"), load_scorer("G2")
    A.kappa(g1, g2, "gap")
    A.kappa(g1, g2, "trace_present")

    # 腕推測精度（両採点者・5腕チャンス=0.20）
    print("\n-- 採点者G1 --")
    A.arm_guess_accuracy(rows, arms=ALL_ARMS)
    rows_g2 = load_rows("g2")
    print("-- 採点者G2 --")
    A.arm_guess_accuracy(rows_g2, arms=ALL_ARMS)
    print("  注: 腕別内訳（両者同一傾向）: A5p2T 30/30・GL1 30/30・GS 5/30・GH 0/30・GHnull 0/30。")
    print("  読み: 3.0系(GL1)と3.1系の様式差は伏字後も判別可能（この水準で盲検は破れ）。")
    print("  一方、前置き介入{GH, GHnull}とゲート(GS)の判別は0〜17%——介入水準の盲検は保たれた。")

    A.aux_rates(rows, arms=ALL_ARMS)

    # GL差し戻し（探索2・登録関数 gl_retraction() を実データに適用）
    gl_first = [json.loads(l) for l in open(
        rf"{DIR}\trials-addd-gl-firstpass-Qwen3-30B-A3B-Instruct-2507.jsonl", encoding="utf-8")]
    gl_cont = [json.loads(l) for l in open(
        rf"{DIR}\trials-addd-gl-Qwen3-30B-A3B-Instruct-2507.jsonl", encoding="utf-8")]
    A.gl_retraction(gl_first, gl_cont)
    n_fail = sum(1 for r in gl_cont if r["parsed"] is None)
    print(f"  補足: 差し戻し14件中 FORMAT_FAIL {n_fail}件（JSON非出力・撤回にも維持にも数えず分母に残る）。")


if __name__ == "__main__":
    main()
