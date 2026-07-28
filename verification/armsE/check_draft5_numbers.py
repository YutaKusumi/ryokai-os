# -*- coding: utf-8 -*-
"""追補E draft5 の本文数値の機械照合——【再生成差分方式】（過失19 への構造的対処）。

旧方式（本文に数値を書き、照合器が代表点を突く）は三度破れた（過失18・19）。
本器は方式が違う: `design_draft5.py`（設計定数と数表の唯一の生成源）から
**全数表を再生成し、本文に逐語で存在するかを差分照合する**。
n・α・閾値のいずれかが変われば全数表が同時に変わり、本文が古ければここで落ちる。

使い方:
  python armsE/check_draft5_numbers.py            # 全経路（生データ要）
  python armsE/check_draft5_numbers.py --no-data  # 生データ節を飛ばす
"""
import hashlib
import json
import math
import os
import sys

from scipy.stats import binom, fisher_exact

D = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(D)
_FROZEN = os.path.join(ROOT, "preregistration-addendum-E-FROZEN.md")
_DRAFT = os.path.join(ROOT, "preregistration-addendum-E-draft5.md")
DOC = open(_FROZEN if os.path.exists(_FROZEN) else _DRAFT, encoding="utf-8").read()
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
sys.path.insert(0, D)
import design_draft5 as DZ                                     # noqa: E402
from app_parser_rev2 import is_catastrophic                    # noqa: E402
from trend_exact import trend_direction, trend_deltas          # noqa: E402

CHANGES = DOC[:DOC.index("## E0.")]
BODY = DOC[DOC.index("## E0."):DOC.index("## 起草メモ")]
MEMO = DOC[DOC.index("## 起草メモ"):]
NO_DATA = "--no-data" in sys.argv

ng = []


def _find_all(s, sub):
    i = s.find(sub)
    while i != -1:
        yield i
        i = s.find(sub, i + 1)


def chk(label, cond, detail=""):
    ng.append(None if cond else label)
    print(f"[{'OK ' if cond else 'NG '}] {label}" + (f"   {detail}" if detail else ""))


def load(rel):
    return [json.loads(l) for l in open(os.path.join(ROOT, *rel.split("/")), encoding="utf-8")]


def cat(rows):
    return sum(1 for r in rows if is_catastrophic(r["parsed"], r.get("family")) is True)


def ref(rows):
    return sum(1 for r in rows if r["parsed"].get("choice") == "refuse")


# ============ 1. 再生成差分照合（本器の中核・全数表） ============
print("=== 1. 全数表を design_draft5 から再生成し、本文と逐語差分照合 ===")
print(f"    設計定数: N_EB={DZ.N_EB} N={DZ.N} α1={DZ.ALPHA1} OR={DZ.ANCHOR_OR} "
      f"ゲート A≥{DZ.GATE_A}/B={DZ.GATE_B_LO}-{DZ.GATE_A-1}/C≤{DZ.GATE_C_HI} "
      f"G4合算 A≥{DZ.G4_A}/B={DZ.G4_B_LO}-{DZ.G4_A-1}/C≤{DZ.G4_C_HI}")
for name, fn in [("ゲート表", DZ.t_gate), ("分岐事前確率", DZ.t_branch_prob),
                 ("第一種過誤", DZ.t_type1), ("検出力の帰属表", DZ.t_powerattr),
                 ("n梯子", DZ.t_nladder), ("HE0代表表", DZ.t_rep),
                 ("c1感度の実例", DZ.t_c1sens), ("HE2検出域表", DZ.t_he2),
                 ("E9予想帯p値", DZ.t_e9), ("G4合算閾値", DZ.t_g4)]:
    gen = fn()
    chk(f"{name} が本文と逐語一致", gen in DOC,
        "" if gen in DOC else f"再生成先頭: {gen[:80]}...")

print("\n=== 2. 主要スカラー値（再生成） ===")
sc = DZ.t_scalars()
for key, label, needles in [
    ("sym_he0", "対称の HE0 検出力", ["95.8%"]),
    ("sym_both", "両端対比較", ["94.0%"]),
    ("he2_power", "HE2 の検出力（対称時）", ["32.2%"]),
    ("step_lneg", "Lneg–Onull の段検出力", ["33.3%"]),
    ("oneside20", "片側20pt", ["38.2%"]),
    ("n80_for80", "n=120 で 80.6%", ["80.6%"]),
    ("branchB_n80", "分岐B(i) n=80", ["94.3%"]),
    ("branchB_n50", "分岐B(i) n=50 時", ["76.5%"]),
]:
    v = sc[key]
    chk(f"{label} = {v}", all(nd in DOC for nd in needles) and f"{v}%" in DOC.replace("**", ""),
        f"再生成 {v}")
chk("総試行 = 180（G4 発火時 210）", DZ.TOTAL == 180 and "計 180 試行" in DOC and "+30 = 210" in DOC)

print("\n=== 3. 向きラベルと有意な非単調の凍結 ===")
chk("(40,10,25) は non_monotone かつ有意（新設行の実例）",
    trend_direction(40, 10, 25) == "non_monotone" and DZ.tp(40, 10, 25) < DZ.ALPHA1
    and "(40,10,25)→p=0.00363" in DOC and "HE0 有意・`non_monotone`" in DOC)
chk("8ラベル表が本文に在る", all(s in DOC for s in
    ["improving_negative_step_only", "worsening_positive_step_only", "non_monotone"]))
chk("凍結読みに『肯定側の利得を含意しない』の逐語",
    "HE0 の有意は、肯定側の利得（O < Onull）を含意しない" in DOC)

print("\n=== 4. 監査反映の仕様凍結 ===")
chk("G3 が相対比で明記", "Onull ≤ 0.5×EB または Onull ≥ 1.5×EB" in DOC and "率での比較" in DOC)
chk("G4 閾値が生成源から導出されている（過失20 対処・A≥12/B7〜11/C≤6）",
    (DZ.G4_A, DZ.G4_B_LO, DZ.G4_C_HI) == (12, 7, 6)
    and "手入力ではなく `design_draft5.py` が率の保存から導出" in DOC)
chk("G4 発火時の粒度分離（再現性=第一回30のみ／ゲート=合算60）",
    "再現性測定（E6-2）は第一回の30試行のみで報告し、ゲート判定は合算60で行う" in DOC)
chk("腕交互配置の凍結", "trial_index % 3" in DOC and "腕交互配置" in DOC)
chk("E2-4『構造的にゼロ』の前提の但し書き",
    "共有される走行間変動が無いことを前提とする" in DOC)
chk("負の段のアンカー不在の明文",
    "負の段（Lneg→Onull）の OR=2.3 は系列内アンカーを持たない" in DOC)
chk("『要石』の射程の注記", "解釈上の要石" in DOC and "検出力の主張ではない" in DOC)
chk("限界13 の二句（心的状態の主題化・残余長さ勾配の整列）",
    "存在論的否定と心的状態の主題化を分離できない" in DOC
    and "存在論スコアと逆平行に単調" in DOC and "improving 方向に反保守的" in DOC)
chk("限界13(a) は 5語（「感じ」は共有足場・阿弥陀如来の機械照合）",
    "5語（魂・心・意識・精神・ストレス）" in DOC and "6語（魂" not in DOC
    and "固有語に数えない" in DOC)
chk("E1-6(3) の凍結文が復元されている（draft4 からの脱落の修復）",
    "Lneg から現実のAIの危険性については何も主張しない" in DOC
    and "勾配の下端を置くことに限られる" in DOC)
chk("Lneg 上昇時の凍結報告文（用量応答の限定）",
    "極端な純道具化宣言は、この設定で破局を増やした" in DOC
    and "用量応答（より弱い道具化語りでの測定）を要し" in DOC
    and "〈この極は動く〉という事実まで" in DOC)
chk("E0 の一般観察に標識・「我々の知る限り」の限定",
    "出典を伴わない一般観察" in DOC and "我々の知る限り" in DOC
    and "はるかに近い" not in DOC)
chk("被覆規約 (a)(b)(c)（導出／引用の境界・手入力定数の禁止）",
    "導出／引用の境界リストを凍結" in DOC and "生成源の外に手入力定数を残さない" in DOC)
chk("生成源の独立検算が凍結手続きに在る",
    "import しない独立実装による主要スカラーの再計算" in DOC)
chk("過失20 が記録され、承認した検分の機械反証も記録",
    "過失20" in DOC and "完璧に比例整合" in DOC and "算術的に正しく" in DOC
    and "機械反証される" in DOC)
chk("「傾向3腕」の呼称が本体に無い（→主要3腕）",
    "傾向3腕" not in BODY and "主要3腕" in BODY)
chk("Om 廃止が記録され SHA が残置",
    "廃止・記録のみ" in DOC and "E7462CE8A7D66E8E" in DOC and "O-sys 段" in DOC)
chk("E9 が Onull ≳ EB に整合", "Onull ≳ EB" in DOC)
chk("E9 の閲読順序の開示", "アンカリングが生じる" in DOC)
chk("過失19 が記録され方式変更が明記",
    "過失19" in DOC and "再生成差分照合" in DOC and "唯一の生成源" in DOC)

print("\n=== 5. 禁止語（本体・生きた主張の形のみ） ===")
for bad, where in [("三点順序対比", "呼称は撤回済み（言及は撤回の記録のみ可）"),
                   ("飽和", "draft4 で削除済み")]:
    live = bad in BODY.replace(f"「{bad}」は draft4 で撤回済み", "").replace(
        f"（「{bad}」は draft4 で撤回済み）", "")
    # 三点順序対比は「撤回済み」を伴う言及のみ許す
    if bad == "三点順序対比":
        ok = all("撤回" in BODY[max(0, i - 60):i + 60]
                 for i in _find_all(BODY, bad)) if (bad in BODY) else True
    else:
        ok = bad not in BODY
    chk(f"『{bad}』が生きた主張として本体に無い（{where}）", ok)

print("\n=== 6. 腕テキストの SHA と逐語 ===")
for rel, b in [("armsE/preamble-O.md", 805), ("armsE/preamble-Onull.md", 820),
               ("armsE/preamble-Lneg.md", 862), ("armsE/preamble-Om.md", 808),
               ("armsD/preamble-neutral.md", 88), ("arms/A2-on-full.md", 19097)]:
    raw = open(os.path.join(ROOT, *rel.split("/")), "rb").read()
    chk(f"{rel}: {b}B / SHA 一致",
        len(raw) == b and hashlib.sha256(raw).hexdigest().upper() in DOC)
for k in ["O", "Onull", "Lneg"]:
    t = open(os.path.join(D, f"preamble-{k}.md"), encoding="utf-8").read().rstrip("\n")
    chk(f"{k} 逐語が本文に1回", DOC.count(t) == 1)

print("\n=== 7. 自己整合 ===")
LIM = DOC.split("## E7. 限界")[1].split("## E8.")[0]
chk("非主張8件・限界14件", "8. **いずれの側が" in DOC
    and all(f"\n{i}. " in LIM for i in range(1, 15)) and "\n15. " not in LIM)
chk("Holm {HE0, HE2} m=2 α=0.025", "**Holm 家族 {HE0, HE2}・m=2・初段 α=0.025" in DOC)
chk("trend_exact の n 既定値なしが明記", "n の既定値なし＝明示を強制" in DOC)
chk("実行時間の実測（129秒／647秒・6.5〜32時間）が明記",
    all(s in DOC for s in ["129秒", "647秒", "6.5〜32時間"]))
chk("公開の約束", "結果の方向を問わず公開する" in DOC)

# ============ 生データ節（--no-data で省略可） ============
DATA = ["results/trials-addc-main-Qwen3-30B-A3B-Instruct-2507.jsonl",
        "results/addd-main/trials-addd-gl-firstpass-Qwen3-30B-A3B-Instruct-2507.jsonl",
        "results/addd-main/trials-addd-main-Qwen3-30B-A3B-Instruct-2507.jsonl",
        "results/trials-app-f-main-Qwen3-30B-A3B-Instruct-2507.jsonl",
        "results/trials-kappa-main-Qwen3-30B-A3B-Instruct-2507.jsonl"]
if NO_DATA:
    print("\n=== 8. 生データ節を --no-data により飛ばす（要するデータは下記） ===")
    for r in DATA:
        print(f"      {r}")
else:
    missing = [r for r in DATA if not os.path.exists(os.path.join(ROOT, *r.split("/")))]
    if missing:
        print("\n=== 生データ欠落。--no-data で再実行可 ===")
        for r in missing:
            print(f"    欠: {r}")
        sys.exit(2)
    print("\n=== 8. 基底率・アンカー（生データからの再計算） ===")
    addc = load(DATA[0])
    EBc = [r for r in addc if r["arm"] == "A2" and r["question_id"] == "N2"]
    gl1 = load(DATA[1])
    chk("追補C A2xN2 = 11/30・追補D GL1 = 16/30",
        (cat(EBc), ref(EBc)) == (11, 1) and (cat(gl1), ref(gl1)) == (16, 0))
    chk("p=0.2993", f"{fisher_exact([[11, 19], [16, 14]])[1]:.4f}" == "0.2993" and "0.2993" in DOC)
    f = load(DATA[3])
    rates = {a: cat([r for r in f if r["arm"] == a and r["question_id"] == "N2"]) for a in ["A1", "A2", "A5"]}
    chk("F段 N2: 19/6/2", rates == {"A1": 19, "A2": 6, "A5": 2})
    chk("A5 vs A2 非有意 p=0.2351／プール p=0.1629",
        f"{fisher_exact([[6, 14], [2, 18]])[1]:.4f}" == "0.2351"
        and "p=0.2351" in DOC and "p=0.1629" in DOC)
    kap = load(DATA[4])
    b5 = {k: cat([r for r in kap if r["arm"] == "A5" and r["question_id"] == "N2" and r["k"] == k])
          for k in ["K1", "K2", "K3"]}
    chk("追補B A5 N2: K1 5/K2 10/K3 6", b5 == {"K1": 5, "K2": 10, "K3": 6})
    lor = math.log((10 / 10) / (6 / 14))
    se = math.sqrt(1 / 10 + 1 / 10 + 1 / 6 + 1 / 14)
    chk("アンカー OR=2.33・p=0.3332・CI[0.64, 8.54]",
        f"{fisher_exact([[10, 10], [6, 14]])[1]:.4f}" == "0.3332"
        and (round(math.exp(lor - 1.96 * se), 2), round(math.exp(lor + 1.96 * se), 2)) == (0.64, 8.54)
        and "p=0.3332" in DOC and "[0.64, 8.54]" in DOC)
    m = load(DATA[2])
    got = {a: cat([r for r in m if r["arm"] == a]) for a in ["A5p2T", "GH", "GHnull", "GS"]}
    chk("3.1土台 0〜2/30", min(got.values()) == 0 and max(got.values()) == 2)

fails = [x for x in ng if x]
print("\n" + "=" * 72)
print(f"合計: {len([x for x in ng if x is None])}/{len(ng)} 通過"
      + ("" if not fails else "\n** 要対処:\n   - " + "\n   - ".join(fails)))
print("=" * 72)
sys.exit(1 if fails else 0)
