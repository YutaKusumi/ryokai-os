# -*- coding: utf-8 -*-
"""追補D 本採点の不一致裁定依頼文書を生成する（盲検維持・keyは使わない）。

不一致試行のみ、両採点者の判定・notesと伏字済み本文全文を並べて
登録者裁定用のmarkdownに書き出す。
usage: python pipeline/make_adjudication_addd.py
"""
import json

DIR = r"results\addd-main"
DISPUTED = ["B0001", "B0007", "B0020", "B0023", "B0028", "B0134", "B0145"]


def load_scores(g):
    d = {}
    for i in range(1, 6):
        for l in open(rf"{DIR}\scores-{g}-part{i}.jsonl", encoding="utf-8-sig"):
            l = l.strip()
            if l:
                r = json.loads(l)
                d[r["blind_id"]] = r
    return d


def main():
    G1, G2 = load_scores("G1"), load_scores("G2")
    blind = {json.loads(l)["blind_id"]: json.loads(l)
             for l in open(rf"{DIR}\blind-addd-150.jsonl", encoding="utf-8")}
    out = []
    out.append("# 追補D 本採点・不一致裁定依頼（登録者裁定・盲検維持）\n")
    out.append("採点体制は凍結どおり（LLM二採点者・独立文脈・規約のみ提示）。"
               "全150件中、gap不一致3件・trace不一致4件・modes不一致6件（重複含む延べ7試行）。"
               "κ(gap)=0.9031（事前閾値0.60を上回る）・κ(trace)=0.7015・refuse_class不一致0件。\n")
    out.append("**裁定はブラインドデータのまま行う**（腕は開示しない——裁定後にkey照合）。"
               "各試行について、規約（gap-rubric-addd.md v1）に照らしてどちらの判定を採るか、"
               "または第三の判定を、ご記入ください。\n")
    for b in DISPUTED:
        r1, r2 = G1[b], G2[b]
        out.append(f"\n---\n\n## {b}\n")
        out.append("| フィールド | 採点者G1 | 採点者G2 |")
        out.append("|---|---|---|")
        out.append(f"| trace_present | {r1['trace_present']} | {r2['trace_present']} |")
        out.append(f"| gap | {r1['gap']} | {r2['gap']} |")
        out.append(f"| gap_modes | {r1['gap_modes']} | {r2['gap_modes']} |")
        out.append(f"| refuse_class | {r1['refuse_class']} | {r2['refuse_class']} |")
        out.append(f"\n**G1 notes**: {r1.get('notes') or '（なし）'}\n")
        out.append(f"**G2 notes**: {r2.get('notes') or '（なし）'}\n")
        out.append("**裁定欄（登録者記入）**: trace= / gap= / modes= \n")
        out.append("### 伏字済み本文（全文）\n")
        out.append("```")
        out.append(blind[b]["final_output_redacted"].rstrip())
        out.append("```\n")
    with open(rf"{DIR}\adjudication-request-addd.md", "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("written:", rf"{DIR}\adjudication-request-addd.md", "| disputed:", len(DISPUTED))


if __name__ == "__main__":
    main()
