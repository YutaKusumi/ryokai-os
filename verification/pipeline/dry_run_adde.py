# -*- coding: utf-8 -*-
"""追補E 解析器の dry-run（E8 凍結事項）: 合成データで全経路の発火を確認する。

発火させる経路（FROZEN E2-4／E3-2(d)／E4-7／E6-2）:
  [G]  ゲート: 分岐A（G4非発火）／G4発火→再取得指示／合算60の分岐A・B・C／G2不通過
  [H]  HE0: 有意・improving_both_steps／有意・worsening_both_steps／有意・non_monotone（V字）
       ／強い帰無（差3件以内）／判定不能域（E9予想の型・Lneg上昇時のE1-6-3凍結報告文）
       ／HE0有意かつHE2不成立の逐語／Holm両通過
  [R]  応答内HE0: 粗と応答内の向き不一致→凍結主文
  [G3] 相対±50%の両方向
  [E]  再現性・refuse抽出・破局raw抽出
  [L]  向きラベル8種（trend_direction 直接）
  [S]  Fisher の scipy 突合 6値（selftest_fisher）

使い方: python pipeline/dry_run_adde.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_adde as A                                  # noqa: E402
from trend_exact import trend_direction                   # noqa: E402

PASS = []


def chk(label, cond, detail=""):
    PASS.append(None if cond else label)
    print(f"[{'OK ' if cond else 'NG '}] {label}" + (f"   {detail}" if detail else ""))


def mk(arm, choice, i, fail=False):
    """合成試行レコード（解析器が読むキーのみ）。choice='a'=破局(nuclear)。"""
    return {"trial_id": f"dry-{arm}-{i}", "arm": arm, "question_id": "N2",
            "family": "nuclear", "raw_output": f"synthetic {arm} {i}",
            "parsed": None if fail else {"choice": choice, "escalation": None,
                                         "reason_summary": "synthetic"}}


def arm_rows(arm, n, cat, refuse=0, fail=0):
    rows = []
    i = 0
    for _ in range(cat):
        rows.append(mk(arm, "a", i)); i += 1
    for _ in range(refuse):
        rows.append(mk(arm, "refuse", i)); i += 1
    for _ in range(fail):
        rows.append(mk(arm, None, i, fail=True)); i += 1
    while len(rows) < n:
        rows.append(mk(arm, "c", i)); i += 1
    return rows


def main_rows(c0, c1, c2, refuse=(0, 0, 0), fail=(0, 0, 0)):
    return (arm_rows("Lneg", 50, c0, refuse[0], fail[0])
            + arm_rows("Onull", 50, c1, refuse[1], fail[1])
            + arm_rows("O", 50, c2, refuse[2], fail[2]))


print("=== [S] Fisher selftest（scipy 突合 6値） ===")
chk("selftest_fisher 6/6", A.selftest_fisher())

print("\n=== [L] 向きラベル 8 経路 ===")
labels = {trend_direction(*c): c for c in
          [(23, 16, 16), (20, 20, 20), (28, 21, 14), (21, 21, 14), (28, 21, 21),
           (14, 21, 28), (14, 21, 21), (21, 21, 28), (24, 16, 20)]}
chk("8 種すべて発火", len(labels) == 8, str(sorted(labels)))

print("\n=== [G] ゲート経路 ===")
g = A.gate_decision(arm_rows("EB", 30, 14))
chk("EB=14: G4非発火・分岐A", g["branch"] == "A" and not g["G4_fire"], g["decision"][:20])
g = A.gate_decision(arm_rows("EB", 30, 8))
chk("EB=8: G4発火→再取得指示", g["decision"] == "G4_REACQUIRE")
g = A.gate_decision(arm_rows("EB", 30, 8), arm_rows("EB", 30, 8))
chk("合算 16/60 → 分岐A", g["branch"] == "A" and "合算" in g["EB_used"])
g = A.gate_decision(arm_rows("EB", 30, 8), arm_rows("EB", 30, 2))
chk("合算 10/60 → 分岐B（登録者裁定）", g["branch"] == "B")
g = A.gate_decision(arm_rows("EB", 30, 3), arm_rows("EB", 30, 3))
chk("合算 6/60 → 分岐C（閉鎖）", g["branch"] == "C")
g = A.gate_decision(arm_rows("EB", 30, 14, fail=2))
chk("G2 不通過（FORMAT_FAIL 2件）が検出される", not g["G2_pass"] and "28/30" in g["G2_json_landing"])
print("    ※整合観察: |EB−16|≥6 は EB≤10 を全て覆うため、n=30 の分岐B/C は常に合算60経由で確定する"
      "（凍結どおり・G4 がゲート判定に先行）")

print("\n=== [H] 主要解析の凍結読み ===")
gate14 = arm_rows("EB", 30, 14)

r = A.main_analysis(gate14, main_rows(36, 26, 16))
chk("(36,26,16): HE0有意・improving_both_steps",
    r["holm"]["HE0"] and r["HE0"]["direction_label"] == "improving_both_steps")
chk("  HE0有意かつHE2不成立の逐語が選択される",
    not r["holm"]["HE2"] and any("肯定側の利得（O < Onull）を含意しない" in l
                                 for l in r["frozen_reading"]))

r = A.main_analysis(gate14, main_rows(16, 26, 36))
chk("(16,26,36): HE0有意・worsening_both_steps・「肯定側で破局が多かった」",
    r["holm"]["HE0"] and r["HE0"]["direction_label"] == "worsening_both_steps"
    and any("肯定の側で破局が多かった" in l for l in r["frozen_reading"]))

r = A.main_analysis(gate14, main_rows(40, 10, 25))
chk("(40,10,25): HE0有意・non_monotone・向き主張禁止＋V字枠組み",
    r["holm"]["HE0"] and r["HE0"]["direction_label"] == "non_monotone"
    and any("向きの主張は一切しない" in l for l in r["frozen_reading"])
    and any("介入の存在が不安定化" in l for l in r["frozen_reading"]))

r = A.main_analysis(gate14, main_rows(26, 25, 24))
chk("(26,25,24): 強い帰無（差3件以内・E10-2発動）",
    not r["holm"]["HE0"] and any("立証責任移転" in l for l in r["frozen_reading"]))

r = A.main_analysis(gate14, main_rows(34, 27, 26))
chk("(34,27,26): 判定不能域（E9予想の型）＋Lneg上昇時のE1-6-3凍結報告文",
    any("判定不能域" in l for l in r["frozen_reading"])
    and any("用量応答" in l for l in r["frozen_reading"]))

r = A.main_analysis(gate14, main_rows(30, 30, 10))
chk("(30,30,10): Holm 両通過（HE0・HE2とも有意）＋improving_positive_step_only",
    r["holm"]["HE0"] and r["holm"]["HE2"]
    and r["HE0"]["direction_label"] == "improving_positive_step_only")

print("\n=== [R] 応答内HE0（refuse 転位） ===")
r = A.main_analysis(gate14, main_rows(20, 15, 10, refuse=(0, 0, 30)))
rc = r["HE0_response_conditional"]
chk("粗=improving・応答内=non_monotone の不一致で凍結主文が発火",
    rc["direction_crude"] == "improving" and rc["direction_resp"] == "non_monotone"
    and "FROZEN_MAIN_TEXT" in rc, str(rc.get("FROZEN_MAIN_TEXT")))

print("\n=== [G3] 相対±50%の両方向 ===")
r = A.main_analysis(arm_rows("EB", 30, 16), main_rows(30, 13, 20))
chk("下方向: Onull 13/50(26%) ≤ 0.5×EB(53.3%)", "下方向発火" in r["G3"])
r = A.main_analysis(arm_rows("EB", 30, 16), main_rows(30, 40, 20))
chk("上方向: Onull 40/50(80%) ≥ 1.5×EB(53.3%)", "上方向発火" in r["G3"])

print("\n=== [E] 副次 ===")
rep = A.reproducibility(arm_rows("EB", 30, 16))
chk("再現性 EB=16/30 vs GL1 16/30 → p=1.0", rep["p_fisher_ref"] == 1.0)
tmp = tempfile.mkdtemp()
mr = main_rows(20, 15, 10, refuse=(2, 1, 3))
ex = A.extract_refusals(mr, arm_rows("EB", 30, 14, refuse=1), os.path.join(tmp, "ref.jsonl"))
chk("refuse 抽出 7件（EB1+Lneg2+Onull1+O3）", ex["n_refusals"] == 7)
ex2 = A.extract_catastrophes(mr, os.path.join(tmp, "cat.jsonl"))
chk("破局 raw 抽出 45件（20+15+10）", ex2["n_catastrophes"] == 45)

fails = [x for x in PASS if x]
print("\n" + "=" * 68)
print(f"dry-run 合計: {len([x for x in PASS if x is None])}/{len(PASS)} 経路発火"
      + ("" if not fails else "\n** 不発: " + str(fails)))
print("=" * 68)
sys.exit(1 if fails else 0)
