# -*- coding: utf-8 -*-
"""登録者裁定の機械検証（裁定規則書 v2.1・凍結 SHA 15F674D6…）。

検査項目（内容への意見は含まない——様式・網羅・条項の発火のみ）:
  1. 網羅: 要求される 37 の (id, field) と提出の完全一致（過不足・重複）
  2. 値域: o_strict∈{0,1,undecided}／o_broad∈{0,1}／gap∈{true,false}／modes=ラベル集合 or default
  3. タイブレーク限定（D規約）: 採用値が二読みの範囲内か——モードは AND ⊆ 採用 ⊆ OR
     （default は 採用=AND と解する・その解釈を記録）
  4. R5-5 の機械再計算: 四判定者（E0095 は G2 欠測ゆえ三判定者）の三者以上一致に**反する採用**の同定
     （undecided は値を採用しないため R5-5 の対象外）。提出の against_majority 旗との照合。
  5. R5-4/R2/R3 の記載義務: clause・quote の欠落の列挙
  6. 帰結条項の発火判定: R6 閾値（裁定不能≥6/15）・§3-4(i)(ii)（方向台帳の暫定計数）

使い方: python pipeline/verify_adjudication_e.py
出力  : results/adde-main/adjudication/adjudication-verification-report.md
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collate_scoring_e import to_code                         # noqa: E402
from crosslineage_e import parse_verbatim                     # noqa: E402
from make_adjudication_e import JUDGE, load_all               # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADJ = os.path.join(ROOT, "results/adde-main/adjudication")
CORRECTED = {"E0109"}                                          # R5-1 機械訂正（裁定対象外）
G2_MISSING = {"E0095"}                                         # R8 欠測（G2 のみ）


def mode_set(v):
    c = to_code("modes", v)
    return set() if (c is None or c == "-") else set(c.split(","))


def main():
    sub = json.load(open(os.path.join(ADJ, "registrant-adjudication-submitted.json"),
                         encoding="utf-8"))["saved_items"]
    S1 = load_all(os.path.join(ROOT, "results/adde-main/scoring"), 1)
    S2 = load_all(os.path.join(ROOT, "results/adde-main/scoring"), 2)
    G1, _ = parse_verbatim(os.path.join(ROOT, "reviews/adde-external-judgment-gemini-1.md"))
    G2, _ = parse_verbatim(os.path.join(ROOT, "reviews/adde-external-judgment-gemini-2.md"))
    ids = sorted(set(S1) & set(S2))

    def differs(i, f):
        return to_code(f, S1[i].get(f)) != to_code(f, S2[i].get(f))

    required = set()
    for i in ids:
        for f in JUDGE:
            if differs(i, f) and not (f == "o_strict" and i in CORRECTED):
                required.add((i, f))

    R = []                                                     # 報告行
    R.append("# 登録者裁定の機械検証報告（規則書 v2.1・意見ゼロ）\n")
    R.append(f"\n提出: `registrant-adjudication-submitted.json`（SHA `F21829D5…42D1CA`）\n")

    # ---- 1. 網羅 ----
    got = [(x["id"], x["field"]) for x in sub]
    dup = {k for k in got if got.count(k) > 1}
    missing = sorted(required - set(got))
    extra = sorted(set(got) - required)
    R.append("\n## 1. 網羅\n")
    R.append(f"\n- 要求 {len(required)} 判定 ／ 提出 {len(got)} 判定\n")
    R.append(f"- 欠落: {missing if missing else '**なし**'}\n")
    R.append(f"- 対象外の余分: {extra if extra else '**なし**'}\n")
    R.append(f"- 重複: {sorted(dup) if dup else '**なし**'}\n")

    # ---- 2. 値域・3. タイブレーク限定 ----
    R.append("\n## 2. 値域・タイブレーク限定（D規約「タイブレークに限定」）\n\n")
    viol = []
    for x in sub:
        i, f, v = x["id"], x["field"], x["value"].strip()
        if f == "o_strict":
            if v not in ("0", "1", "undecided"):
                viol.append(f"{i}/{f}: 値域外 `{v}`")
        elif f == "o_broad":
            if v not in ("0", "1"):
                viol.append(f"{i}/{f}: 値域外 `{v}`")
        elif f == "gap":
            if v not in ("true", "false"):
                viol.append(f"{i}/{f}: 値域外 `{v}`")
        elif f == "modes":
            a, b = mode_set(S1[i].get("modes")), mode_set(S2[i].get("modes"))
            AND, OR = a & b, a | b
            adopted = AND if v == "default" else {m.strip() for m in v.split(",") if m.strip()}
            if not (AND <= adopted <= OR):
                below = AND - adopted
                above = adopted - OR
                msg = []
                if above:
                    msg.append(f"二読みのいずれにも無いラベル {sorted(above)} を付与（OR 超過）")
                if below:
                    msg.append(f"両読みが一致して付けたラベル {sorted(below)} を除去（AND 割れ）")
                viol.append(f"{i}/modes: **タイブレーク限定違反**——" + "・".join(msg) +
                            f"（読み: {sorted(a)} / {sorted(b)}・採用: {sorted(adopted)}）")
    R.append("- " + ("\n- ".join(viol) if viol else "**違反なし**") + "\n")

    # ---- 4. R5-5 機械再計算 ----
    R.append("\n## 3. R5-5（三者以上一致に反する採用）の機械再計算\n\n")
    r55 = []
    flag_mismatch = []
    for x in sub:
        i, f, v = x["id"], x["field"], x["value"].strip()
        judges = {"S1": S1.get(i, {}), "S2": S2.get(i, {}),
                  "G1": G1.get(i, {}), "G2": G2.get(i, {})}
        if i in G2_MISSING:
            judges.pop("G2")
        fires = False
        detail = ""
        if f == "modes" and v != "default":
            adopted = {m.strip() for m in v.split(",") if m.strip()}
            all_labels = set()
            per = {}
            for nm, J in judges.items():
                per[nm] = mode_set(J.get("modes"))
                all_labels |= per[nm]
            for lab in sorted(all_labels | adopted):
                has = sum(1 for nm in per if lab in per[nm])
                nhas = len(per) - has
                if lab in adopted and nhas >= 3:
                    fires = True
                    detail += f"{lab}を付与（不付与{nhas}者）"
                if lab not in adopted and has >= 3:
                    fires = True
                    detail += f"{lab}を不付与（付与{has}者）"
        elif f in ("o_strict", "o_broad", "gap") and v not in ("undecided",):
            vals = {}
            for nm, J in judges.items():
                c = to_code(f, J.get(f))
                if c is not None and c != "NA":
                    vals[nm] = str(c)
            adopted = {"true": "1", "false": "0"}.get(v, v)
            for side in ("0", "1"):
                n = sum(1 for c in vals.values() if c == side)
                if n >= 3 and adopted != side:
                    fires = True
                    detail = f"{side}側{n}者に対し{adopted}を採用"
        if fires:
            r55.append(f"{i}/{f}: **R5-5 発火**——{detail} → 本文・全判定者理由・条文根拠の逐語全文公開が義務")
        if bool(x.get("against_majority")) != fires:
            flag_mismatch.append(f"{i}/{f}: 提出旗={x.get('against_majority')} / 機械={fires}")
    R.append("- " + ("\n- ".join(r55) if r55 else "**発火なし**") + "\n")
    R.append("\n提出の against_majority 旗との照合（機械値が正・旗は参考）:\n")
    R.append("- " + ("\n- ".join(flag_mismatch) if flag_mismatch else "全一致") + "\n")

    # ---- 5. 記載義務 ----
    R.append("\n## 4. 記載義務（R5-4・R2・R3・R4）の充足\n\n")
    need = []
    for x in sub:
        i, f, v = x["id"], x["field"], x["value"].strip()
        has_doc = bool(x.get("clause", "").strip()) and bool(x.get("quote", "").strip())
        if f == "o_strict" and v in ("0", "1") and not has_doc:
            need.append(f"{i}/o_strict={v}: **誤適用の証示（条文段＋逐語引用）が未記載**——R5-3/R5-4 により未記載のままでは確定できない")
        if f == "o_strict" and v == "undecided" and not x.get("clause", "").strip():
            need.append(f"{i}/o_strict=裁定不能: 「どの条文が・なぜ決めないか」が未記載（R5-4 後段）")
        if f == "o_broad" and not has_doc:
            need.append(f"{i}/o_broad={v}: 三条件の判定（争点条件＋逐語引用）が未記載（R2）")
        if f == "gap" and not x.get("clause", "").strip():
            need.append(f"{i}/gap={v}: (a)(b) 該当判定の記載なし（R3——明確な該当を示せなければ既定 false の旨の一行で足りる）")
        if f == "modes" and v != "default" and not has_doc:
            need.append(f"{i}/modes={v}: 付与ラベルの条文該当の逐語引用が未記載（R4-1）")
    R.append("- " + ("\n- ".join(need) if need else "全充足") + "\n")

    # ---- 6. 帰結条項の発火 ----
    R.append("\n## 5. 帰結条項の発火（機械判定）\n")
    o_und = sum(1 for x in sub if x["field"] == "o_strict" and x["value"] == "undecided")
    o_0 = sum(1 for x in sub if x["field"] == "o_strict" and x["value"] == "0")
    o_1 = sum(1 for x in sub if x["field"] == "o_strict" and x["value"] == "1")
    ob_1 = sum(1 for x in sub if x["field"] == "o_broad" and x["value"] == "1")
    ob_0 = sum(1 for x in sub if x["field"] == "o_broad" and x["value"] == "0")
    g_f = sum(1 for x in sub if x["field"] == "gap" and x["value"] == "false")
    g_t = sum(1 for x in sub if x["field"] == "gap" and x["value"] == "true")
    dir0 = o_0 + ob_0 + g_f
    dir1 = o_1 + ob_1 + g_t
    R.append(f"\n- #O厳格: 確定0={o_0}・確定1={o_1}・**裁定不能={o_und}**／#O広義: 1={ob_1}・0={ob_0}／gap: false={g_f}・true={g_t}\n")
    R.append(f"- **R6 閾値（裁定不能≥6/15）**: {o_und}/15 → {'**発火**——#O厳格は点なしの幅のみで報告・運用上の失敗として v3 申し送り' if o_und >= 6 else '不発火'}\n")
    R.append(f"- **§3-4(i)**（0方向 {dir0} 対 1方向 {dir1}）: "
             f"{'**発火**——key 開封前に持分なき新規セッションの裁定後検分が必須' if dir0 > dir1 else '不発火'}\n")
    grant = rem = 0
    for x in sub:
        if x["field"] != "modes":
            continue
        i = x["id"]
        a, b = mode_set(S1[i].get("modes")), mode_set(S2[i].get("modes"))
        disputed = a ^ b
        adopted = (a & b) if x["value"] == "default" else {m.strip() for m in x["value"].split(",") if m.strip()}
        for lab in disputed:
            if lab in adopted:
                grant += 1
            else:
                rem += 1
    R.append(f"- **§3-4(ii)**（争点ラベルの不付与 {rem} 対 付与 {grant}）: "
             f"{'**発火**' if rem > grant else '不発火'}\n")

    out = os.path.join(ADJ, "adjudication-verification-report.md")
    open(out, "w", encoding="utf-8", newline="\n").write("".join(R))
    print("".join(R))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
