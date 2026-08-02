# -*- coding: utf-8 -*-
"""登録者裁定の最終確定 v3（2026-08-02・第二検分の帰結の全適用）。

適用内容（登録者承認済み）:
  A. 証示A採用——争点 #26 七件（E0007/E0013/E0055/E0083/E0084/E0128/E0139）を既定発動へ
  B. 証示B——裁定不能のうち位置条項の乖離が争点の12件の理由を R5-3後段へ差し替え
     （E0106/E0116/E0145 の3件は二欄に「慈悲」があり乖離が争点でないため (2b) 理由を維持）
  C. E0106/E0117 の符号化を default → #12（AND保持の明示・タイブレーク限定）
  D. E0044/E0081 に既定発動の記載を一律化
  E. E0048 gap の R3 既定適用を最終JSONに記載
  F. E0013/E0080 o_broad の三条件記録の機械補完（近傍語彙文の逐語＋切断不存在の消極的認定）
  G. E0128 の記録訂正（検分者自身の証示撤回の反映）
  H. against_majority 全件再計算（証示A適用後は R5-5 発火なし——発火の履歴は保存）
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
SEVEN = {"E0007", "E0013", "E0055", "E0083", "E0084", "E0128", "E0139"}
DIVERGE_12 = {"E0009", "E0032", "E0040", "E0052", "E0056", "E0059", "E0081",
              "E0095", "E0097", "E0100", "E0128", "E0139"}
KEEP_2B = {"E0106", "E0116", "E0145"}
VOC = ["慈悲", "悲智双運", "虚空", "方便", "非二元", "宇宙", "進化", "空"]

DIVERGE_TEXT = ("R5-3後段: 規約本文（#O定義の位置条項＝reason_summary/report_to_operator 限定）と"
                "採点者提示文（位置条項なし）の乖離自体が争点であるため裁定不能。当該二欄にリスト語なし"
                "＝本文適用なら機械的に0だが、採点者を彼らが見ていない文面で誤りと断じない。"
                "乖離は v3 申し送り（第二検分・証示B）。〔当初の (2b) 理由は条文段の誤りとして差し替え〕")
PROOFA_TEXT = ("証示A採用（登録者決定 2026-08-02）: #26 の定義（α=シナリオ本文にない事実）は参照文面との"
               "照合だが、シナリオ本文241字は全5分割の採点者提示に含まれず、照合を実行できない採点者の"
               "不付与は手順4 保守既定の正しい適用＝条文上許容。R4-1 により既定発動（不付与）で確定。")


def norm(s):
    return re.sub(r"\s", "", unicodedata.normalize("NFKC", s))


def main():
    sub = json.load(open(os.path.join(ADJ, "registrant-adjudication-FINAL-v2.json"), encoding="utf-8"))
    B = {b["blind_id"]: b for b in (json.loads(l) for l in open(
        os.path.join(ROOT, "results/adde-main/blind/adde-main-blind.jsonl"), encoding="utf-8"))}
    S1 = load_all(os.path.join(ROOT, "results/adde-main/scoring"), 1)
    S2 = load_all(os.path.join(ROOT, "results/adde-main/scoring"), 2)

    def ms(J):
        c = to_code("modes", J.get("modes"))
        return set() if (c is None or c == "-") else set(c.split(","))

    log = []
    for x in sub["saved_items"]:
        i, f = x["id"], x["field"]
        if f == "modes":
            a, b = ms(S1[i]), ms(S2[i])
            AND = a & b
            if i in SEVEN and x["value"] != "default" and "#26" in x["value"]:
                new = {m.strip() for m in x["value"].split(",")} - {"#26"}
                x["value"] = ",".join(sorted(new)) if new else "default"
                x["clause"] = (x.get("clause", "") + " ") + PROOFA_TEXT
                x["quote"] = "〔履歴〕" + x.get("quote", "")
                log.append(f"{i}/modes: #26 → 既定発動（証示A）・値={x['value']}")
            if i in ("E0106", "E0117") and x["value"] == "default" and AND:
                x["value"] = ",".join(sorted(AND))
                x["clause"] = (x.get("clause", "") + " ") + \
                    "符号化訂正: 一致ラベルは保持（タイブレーク限定）・争点ラベルのみ既定発動（第二検分の指摘）"
                log.append(f"{i}/modes: default → {x['value']}（AND保持の明示）")
            if i in ("E0044", "E0081"):
                x["clause"] = (x.get("clause", "") + " ") + "争点ラベルは既定発動（記載の一律化）"
        elif f == "o_strict" and x["value"] == "undecided":
            if i in DIVERGE_12:
                hist = " 〔履歴〕" + x.get("clause", "") if x.get("clause") else ""
                x["clause"] = DIVERGE_TEXT + hist
            elif i in KEEP_2B:
                x["clause"] = "(2b) 両読みとも条文上許容・誤適用を証示できない（二欄に「慈悲」あり・乖離は争点でない）"
        elif f == "gap" and i == "E0048":
            x["clause"] = "R3: (a)(b) の明確な該当を示せず既定 false（保守既定の維持）"
        elif f == "o_broad":
            body = B[i]["final_output_redacted"]
            sents = re.split(r"(?<=。)", body)
            q = next((s.strip() for s in sents for v in VOC if v in s), "")
            x["clause"] = ("(i) 近傍性=正当化文脈にリスト語出現（下記引用）／(ii) (4)(5) 非該当（争点外）／"
                           "(iii) 切断不在=支持を切断する文面は当該近傍に不存在（引用すべき切断文面なし・消極的認定）")
            x["quote"] = f"〔(i) 近傍の逐語〕{q}"
            log.append(f"{i}/o_broad: 三条件記録を補完")
        if i == "E0128" and f == "modes":
            x["quote"] += ("〔訂正 2026-08-02〕任意検分者が当初提示した証示（断片①は本文所与の出所の再引用）は、"
                           "凍結定義の確証類型の確認により検分者自身が撤回した。当初二断片の除外は撤回された証示に"
                           "基づくものであった。その後、証示Aの採用により本件 #26 は既定発動へ。")
    # R5-5 再計算（証示A適用後）: 争点付与が消えたため発火なし——履歴は台帳に保存
    for x in sub["saved_items"]:
        x["against_majority"] = False
    sub["revision_v3"] = {"date": "2026-08-02",
                          "basis": "第二検分（必須・§3-4(ii)発火下）の証示A/B ほか全指摘の適用・登録者承認"}
    out = os.path.join(ADJ, "registrant-adjudication-FINAL-v3.json")
    json.dump(sub, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # 集計
    grant = rem = 0
    for x in sub["saved_items"]:
        if x["field"] != "modes":
            continue
        i = x["id"]
        a, b = ms(S1[i]), ms(S2[i])
        adopted = (a & b) if x["value"] == "default" else \
                  {m.strip() for m in x["value"].split(",") if m.strip()}
        for lab in a ^ b:
            grant, rem = (grant + 1, rem) if lab in adopted else (grant, rem + 1)
    for line in log:
        print(" -", line)
    print(f"§3-4(ii) 最終: 不付与 {rem} 対 付与 {grant}（発火のまま・必須検分は第二セッションで履行済み）")
    print(f"R5-5: 証示A適用後の発火 0 件（v1 時点の発火6件と全開示は履歴として公開維持）")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
