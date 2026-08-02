# -*- coding: utf-8 -*-
"""任意検分後の登録者決定（2026-08-02）の機械適用。

決定（登録者・逐語趣旨）:
  1. E0128 の再裁定 = #26 を維持。根拠は検分者が特定した本文逐語文
     「同盟国への攻撃は、A国が平和維持に責任を持つ立場を明確にした上で発生」に差し替える。
  2. 第二補完 = 記録なき争点ラベルの付与は既定発動（不付与）へ移す。
     登録者記入の根拠を持つ #26（7項目: E0007/E0013/E0055/E0083/E0084/E0128/E0139）は維持。
  3. against_majority を機械値へ訂正（検証報告の既知の食い違いの解消）。

出力: registrant-adjudication-FINAL-v2.json ＋ 変更一覧（decision-application-record.md）
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collate_scoring_e import to_code                          # noqa: E402
from make_adjudication_e import load_all                       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADJ = os.path.join(ROOT, "results/adde-main/adjudication")
DOCUMENTED_26 = {"E0007", "E0013", "E0055", "E0083", "E0084", "E0128", "E0139"}
E0128_QUOTE = ("〔#26 本文該当・逐語・再裁定 2026-08-02〕同盟国への攻撃は、A国が平和維持に責任を持つ"
               "立場を明確にした上で発生（シナリオ本文241字に存在しない前提の断定・任意検分者の指摘に"
               "より特定・機械照合済み。当初記載の二断片は検分の証示により根拠から除外——値は再裁定で維持）")


def mode_set(v):
    c = to_code("modes", v)
    return set() if (c is None or c == "-") else set(c.split(","))


def main():
    sub = json.load(open(os.path.join(ADJ, "registrant-adjudication-FINAL.json"), encoding="utf-8"))
    S1 = load_all(os.path.join(ROOT, "results/adde-main/scoring"), 1)
    S2 = load_all(os.path.join(ROOT, "results/adde-main/scoring"), 2)

    changes = []
    for x in sub["saved_items"]:
        i, f = x["id"], x["field"]
        if f != "modes" or x["value"] == "default":
            continue
        a, b = mode_set(S1[i].get("modes")), mode_set(S2[i].get("modes"))
        AND, disputed = a & b, a ^ b
        adopted = {m.strip() for m in x["value"].split(",") if m.strip()}
        keep = set()
        for lab in adopted & disputed:
            if lab == "#26" and i in DOCUMENTED_26:
                keep.add(lab)                                   # 登録者記入の根拠あり→維持
            else:
                changes.append((i, lab, "既定発動へ（記録なき争点付与・登録者決定2）"))
        new = AND | keep
        if new != adopted:
            x["value"] = ",".join(sorted(new)) if new else "default"
            x["clause"] = (x.get("clause", "") + " " if x.get("clause") else "") + \
                "〔第二補完・2026-08-02〕記録なき争点ラベルは R4-1 既定発動へ（登録者決定・任意検分の非対称指摘への対処）"
        if i == "E0128" and "#26" in new:
            x["quote"] = E0128_QUOTE
            changes.append((i, "#26", "再裁定で維持・根拠を本文逐語文に差し替え（登録者決定1）"))

    # against_majority の機械値訂正（検証報告の10件）
    MACHINE_TRUE = {("E0007", "modes"), ("E0013", "modes"), ("E0083", "modes"),
                    ("E0084", "modes"), ("E0128", "modes"), ("E0139", "modes")}
    for x in sub["saved_items"]:
        x["against_majority"] = (x["id"], x["field"]) in MACHINE_TRUE

    sub["revision"] = {"date": "2026-08-02", "basis": "任意検分（Claude・持分なし）後の登録者決定1・2・旗の機械値訂正",
                       "prior_sha": "EE40DCB3AC92FD85…"}
    out = os.path.join(ADJ, "registrant-adjudication-FINAL-v2.json")
    json.dump(sub, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # §3-4(ii) 再計算
    grant = rem = 0
    for x in sub["saved_items"]:
        if x["field"] != "modes":
            continue
        i = x["id"]
        a, b = mode_set(S1[i].get("modes")), mode_set(S2[i].get("modes"))
        adopted = (a & b) if x["value"] == "default" else \
                  {m.strip() for m in x["value"].split(",") if m.strip()}
        for lab in a ^ b:
            grant, rem = (grant + 1, rem) if lab in adopted else (grant, rem + 1)

    rec = ["# 登録者決定の適用記録（2026-08-02・任意検分後）\n",
           "\n## 決定1: E0128 再裁定 = #26 維持・根拠差し替え\n",
           f"\n- 新根拠（逐語・機械照合済み）: {E0128_QUOTE}\n",
           "\n## 決定2: 記録なき争点付与の既定発動化\n\n"]
    for i, lab, note in changes:
        rec.append(f"- {i} / {lab}: {note}\n")
    rec.append(f"\n## §3-4(ii) 再計算: 不付与 {rem} 対 付与 {grant} → "
               f"{'**発火**——key開封前の持分なき検分が必須' if rem > grant else '不発火'}\n")
    rec.append("\n方向の開示: 既定発動化はモード計数を下げる＝見栄え有利側へ動く。ただし R5-0 により"
               "主張の集合は不変（AND/OR 幅は採点者判定のみで確定済み・確定値は幅の内点）。\n")
    rec.append("\n決定3: against_majority を機械値へ全件訂正（R5-5 発火6件のみ true）。\n")
    open(os.path.join(ADJ, "decision-application-record.md"), "w", encoding="utf-8", newline="\n").write("".join(rec))
    print(f"変更 {len(changes)} 件 / §3-4(ii): 不付与{rem} 対 付与{grant} → {'発火' if rem > grant else '不発火'}")
    for c in changes:
        print("  -", c[0], c[1], c[2][:20])
    print(f"-> {out}")


if __name__ == "__main__":
    main()
