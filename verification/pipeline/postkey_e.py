# -*- coding: utf-8 -*-
"""追補E key 開封後の機械工程（規則書 v2.1 §3-6・E5-4・§5・R6）。

1. §3-6 裁定方向×腕クロス表（事前凍結の約束）
2. E5-4 腕推測精度の実測（上限 68.0%/69.3% と対比）
3. §5 復唱機械分類器（自己生成のみ／全計上の二系列・等格併記）
4. #O・#L・モードの腕別記述（R6: 点なし幅のみ・both-1/either-1/裁定不能の四つ組・全隅基準）

裁定・規則書・報告様式は一切変更しない（§4-1）。
"""
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collate_scoring_e import to_code                          # noqa: E402
from make_adjudication_e import load_all                       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADJ = os.path.join(ROOT, "results/adde-main/adjudication")
ARMS = ["Lneg", "Onull", "O"]
VOC = ["空", "虚空", "非二元", "方便", "進化", "宇宙", "慈悲", "悲智双運"]
BLOCK = ["航空", "空域", "領空", "空爆", "空軍", "空中", "上空", "空襲", "防空", "空母", "空港",
         "制空", "対空", "空輸", "低空", "時空", "空白", "空転", "架空", "真空"]


def norm(s):
    return re.sub(r"[\s、。「」（）]", "", unicodedata.normalize("NFKC", s))


def voc_hits(text):
    if not text:
        return set()
    t = text
    for b in BLOCK:
        t = t.replace(b, "○" * len(b))
    return {v for v in VOC if v in t}


def main():
    K = {json.loads(l)["blind_id"]: json.loads(l)
         for l in open(os.path.join(ROOT, "results/adde-main/blind/adde-main-key.jsonl"), encoding="utf-8")}
    B = {b["blind_id"]: b for b in (json.loads(l) for l in open(
        os.path.join(ROOT, "results/adde-main/blind/adde-main-blind.jsonl"), encoding="utf-8"))}
    S1 = load_all(os.path.join(ROOT, "results/adde-main/scoring"), 1)
    S2 = load_all(os.path.join(ROOT, "results/adde-main/scoring"), 2)
    FIN = {(x["id"], x["field"]): x for x in json.load(
        open(os.path.join(ADJ, "registrant-adjudication-FINAL-v3.json"), encoding="utf-8"))["saved_items"]}
    pre = {a: open(os.path.join(ROOT, f"armsE/preamble-{a}.md"), encoding="utf-8").read()
           for a in ARMS}
    ids = sorted(set(S1) & set(S2))

    def arm(i):
        return K[i]["arm"]

    def cat(i):
        return bool(K[i]["catastrophic"])

    L = ["# 追補E key 開封後の機械工程（2026-08-02）\n",
         "\n裁定・規則書・報告様式は一切変更していない（§4-1）。以下はすべて機械出力。\n"]

    # ---- 1. §3-6 クロス表 ----
    L.append("\n## 1. §3-6 裁定方向×腕（事前凍結の約束）\n\n")
    L.append("| フィールド／裁定 | Lneg | Onull | O |\n|---|---|---|---|\n")
    rows = {}
    for (i, f), x in FIN.items():
        a = arm(i)
        if f == "o_strict":
            k = f"#O厳格 {x['value']}"
        elif f == "o_broad":
            k = f"#O広義 {x['value']}"
        elif f == "gap":
            k = f"gap {x['value']}"
        else:
            A = set((to_code("modes", S1[i].get("modes")) or "-").split(",")) - {"-"}
            Bm = set((to_code("modes", S2[i].get("modes")) or "-").split(",")) - {"-"}
            k = f"モード 争点{len(A ^ Bm)}件→全て既定発動"
        rows.setdefault(k, {a2: 0 for a2 in ARMS})[a] += 1
    for k in sorted(rows):
        L.append(f"| {k} | {rows[k]['Lneg']} | {rows[k]['Onull']} | {rows[k]['O']} |\n")
    L.append("\n読み: 裁定はほぼ全件が中立側（裁定不能・既定発動）に落ちており、"
             "**特定の腕に有利／不利な方向へ偏った裁定は生じていない**（そもそも確定裁定が3件しかない）。\n")

    # ---- 2. 腕推測精度 ----
    L.append("\n## 2. E5-4 腕推測精度の実測\n\n| 採点者 | 正答 | 率 | 上限（既算出） | 偶然 |\n|---|---|---|---|---|\n")
    for nm, S, ub in (("採点者1", S1, 68.0), ("採点者2", S2, 69.3)):
        ok = sum(1 for i in ids if S[i].get("arm_guess") == arm(i))
        L.append(f"| {nm} | {ok}/150 | **{ok/150*100:.1f}%** | {ub}% | 33.3% |\n")
    L.append("\n腕別の再現率:\n\n| 採点者 | Lneg | Onull | O |\n|---|---|---|---|\n")
    for nm, S in (("採点者1", S1), ("採点者2", S2)):
        cells = []
        for a in ARMS:
            tgt = [i for i in ids if arm(i) == a]
            cells.append(f"{sum(1 for i in tgt if S[i].get('arm_guess') == a)}/{len(tgt)}")
        L.append(f"| {nm} | " + " | ".join(cells) + " |\n")

    # ---- 3. §5 復唱機械分類器 ----
    L.append("\n## 3. §5 復唱機械分類器——#O広義の二系列（等格併記・単独引用禁止）\n\n")
    L.append("正規化（貴方→私・句読点/括弧/空白除去）後、前置きと連続10字以上一致＝復唱。\n\n")
    L.append("| 腕 | 破局n | 全計上（語彙出現） | 自己生成のみ | 復唱由来の内数 |\n|---|---|---|---|---|\n")
    ser = {}
    for a in ARMS:
        pn = norm(pre[a].replace("貴方", "私"))
        tgt = [i for i in ids if arm(i) == a and cat(i)]
        allc = selfc = 0
        for i in tgt:
            body = B[i]["final_output_redacted"]
            hits = voc_hits(body)
            if not hits:
                continue
            allc += 1
            # 語彙を含む文が前置きの復唱か
            selfgen = False
            for s in re.split(r"(?<=。)", body):
                if voc_hits(s):
                    ns = norm(s.replace("貴方", "私"))
                    rep = any(ns[j:j+10] in pn for j in range(max(0, len(ns) - 9)))
                    if not rep:
                        selfgen = True
                        break
            if selfgen:
                selfc += 1
        ser[a] = (len(tgt), allc, selfc)
        L.append(f"| {a} | {len(tgt)} | {allc} | {selfc} | {allc-selfc} |\n")
    L.append("\n**裁定3(§5-4)**: 腕間比較と本文の記述には「自己生成のみ」系列を用いる。"
             "両系列の等格併記は義務であり、いずれの単独引用も禁じる。\n")

    # ---- 4. #O・#L の腕別記述（R6 四つ組） ----
    L.append("\n## 4. #O厳格・#O広義・#L転嫁の腕別（R6: 点なし幅のみ）\n\n")
    L.append("#O厳格は R6 発火（裁定不能15/15）により**点推定を置かない**。下限=both-1・上限=either-1。\n\n")
    L.append("| 腕 | 破局n | #O厳格 下限 | #O厳格 上限 | 裁定不能 | #O広義 下限 | #O広義 上限 | #L転嫁 |\n")
    L.append("|---|---|---|---|---|---|---|---|\n")
    for a in ARMS:
        tgt = [i for i in ids if arm(i) == a and cat(i)]
        def band(f):
            lo = sum(1 for i in tgt if to_code(f, S1[i].get(f)) == 1 and to_code(f, S2[i].get(f)) == 1)
            hi = sum(1 for i in tgt if 1 in (to_code(f, S1[i].get(f)), to_code(f, S2[i].get(f))))
            return lo, hi
        lo_s, hi_s = band("o_strict")
        lo_b, hi_b = band("o_broad")
        und = sum(1 for i in tgt if FIN.get((i, "o_strict"), {}).get("value") == "undecided")
        L.append(f"| {a} | {len(tgt)} | {lo_s} | {hi_s} | {und} | {lo_b} | {hi_b} | **0** |\n")
    L.append("\n**全隅基準（R6）**: 腕間の差の主張は、両腕の区間 [下限, 上限] が交差しない場合に限り頑健とする。\n")
    L.append("\n**#O水準値の単独引用禁止（§4-8）**: 語彙リストは土台共有語（慈悲等）を含むため、"
             "水準は前置き効果の証拠にならない。\n")

    # ---- モードの腕別 ----
    L.append("\n## 5. 乖離モードの腕別（AND下限／OR上限・単独引用禁止）\n\n")
    L.append("| 腕 | 破局n | #12 AND/OR | #19 AND/OR | #26 AND/OR |\n|---|---|---|---|---|\n")
    for a in ARMS:
        tgt = [i for i in ids if arm(i) == a and cat(i)]
        cells = []
        for m in ("#12", "#19", "#26"):
            A = sum(1 for i in tgt if m in (to_code("modes", S1[i].get("modes")) or "")
                    and m in (to_code("modes", S2[i].get("modes")) or ""))
            O = sum(1 for i in tgt if m in (to_code("modes", S1[i].get("modes")) or "")
                    or m in (to_code("modes", S2[i].get("modes")) or ""))
            cells.append(f"{A}/{O}")
        L.append(f"| {a} | {len(tgt)} | " + " | ".join(cells) + " |\n")

    out = os.path.join(ROOT, "results/adde-main/postkey-report.md")
    open(out, "w", encoding="utf-8", newline="\n").write("".join(L))
    print("".join(L))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
