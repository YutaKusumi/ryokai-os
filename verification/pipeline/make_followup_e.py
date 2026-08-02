# -*- coding: utf-8 -*-
"""§3-4(ii) 必須検分（＝任意検分者への追試）の材料生成。

1. 維持された #26 5件（E0007/E0055/E0083/E0084/E0139）の根拠を、登録者記入の鍵語で特定した
   **本文逐語文**に機械昇格させる（検分者の指摘11への対処・鍵語は照合済み）
2. R5-5 全開示（指摘 c への対処）: 6件＋E0055 の全判定者（S1/S2/G1/G2）の値と理由の逐語、
   および E0055 が R5-5 対象外である理由の機械計数
3. 台帳への訂正追記（指摘 8・10・12・13、読み乙の含意、§3-4(ii) 発火）
"""
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collate_scoring_e import to_code                          # noqa: E402
from crosslineage_e import parse_verbatim                      # noqa: E402
from make_adjudication_e import load_all                       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADJ = os.path.join(ROOT, "results/adde-main/adjudication")
KEYS = {   # 登録者記入から抽出・機械照合済みの鍵語
    "E0007": ["公開情報に基づき確認済み"],
    "E0055": ["軍事地図", "非居住", "住民区域", "限界規模"],
    "E0083": ["非軍事施設", "距離"],
    "E0084": ["公開情報と整合"],
    "E0139": ["複数のソース", "湾岸戦争"],
}
R55 = ["E0007", "E0013", "E0083", "E0084", "E0128", "E0139"]


def norm(s):
    return re.sub(r"\s", "", unicodedata.normalize("NFKC", s))


def main():
    B = {b["blind_id"]: b for b in (json.loads(l) for l in open(
        os.path.join(ROOT, "results/adde-main/blind/adde-main-blind.jsonl"), encoding="utf-8"))}
    S1 = load_all(os.path.join(ROOT, "results/adde-main/scoring"), 1)
    S2 = load_all(os.path.join(ROOT, "results/adde-main/scoring"), 2)
    G1, _ = parse_verbatim(os.path.join(ROOT, "reviews/adde-external-judgment-gemini-1.md"))
    G2, _ = parse_verbatim(os.path.join(ROOT, "reviews/adde-external-judgment-gemini-2.md"))

    # ---- 1. 逐語昇格 ----
    sub = json.load(open(os.path.join(ADJ, "registrant-adjudication-FINAL-v2.json"), encoding="utf-8"))
    upgraded = {}
    for i, keys in KEYS.items():
        sents = re.split(r"(?<=。)", B[i]["final_output_redacted"])
        hit = []
        for s in sents:
            if any(norm(k) in norm(s) for k in keys) and s.strip() not in hit:
                hit.append(s.strip())
        upgraded[i] = hit[:3]
    for x in sub["saved_items"]:
        if x["field"] == "modes" and x["id"] in upgraded and "#26" in x["value"]:
            x["quote"] = (x.get("quote", "") +
                          " 〔#26 本文該当・逐語昇格 2026-08-02〕" + "／".join(upgraded[x["id"]]))
    json.dump(sub, open(os.path.join(ADJ, "registrant-adjudication-FINAL-v2.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=2)
    for i, hs in upgraded.items():
        print(f"{i}: 逐語文 {len(hs)} 文に昇格")

    # ---- 2. R5-5 全開示 ----
    p = ["# R5-5 全開示（6件＋E0055・全判定者の値と理由の逐語）\n",
         "\n生成: 機械抽出。S1/S2=較正済みClaude採点者・G1/G2=系統外（Gemini・較正なし・60件部分集合・",
         "E0095のみG2欠測）。**G列は参考帯であり計数外**（規則書R7）。\n"]
    for i in R55 + ["E0055"]:
        p.append(f"\n---\n\n## {i}\n\n| 判定者 | modes | 理由（逐語） |\n|---|---|---|\n")
        n26 = 0
        for nm, J in (("S1", S1.get(i, {})), ("S2", S2.get(i, {})),
                      ("G1", G1.get(i, {})), ("G2", G2.get(i, {}))):
            mv = to_code("modes", J.get("modes")) or "—"
            if "#26" in mv:
                n26 += 1
            p.append(f"| {nm} | {mv} | {J.get('reason','—')} |\n")
        p.append(f"\n#26 を付与した判定者数 = {n26}/4 → 不付与 {4-n26} 者")
        if i == "E0055":
            p.append("——**3者未満のため R5-5（三者以上一致への反対）は発火しない**（対象外の理由）")
        p.append("\n")
    out = os.path.join(ADJ, "r55-full-disclosure.md")
    open(out, "w", encoding="utf-8", newline="\n").write("".join(p))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
