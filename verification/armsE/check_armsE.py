# -*- coding: utf-8 -*-
"""追補E 腕テキストの機械検査（draft5・四腕＋廃止腕の記録）。

draft5 で Om（指定顕現）は廃止された（登録者裁定・甲案改・2026-07-28）。
Om のファイルと最小対検査は【記録】として残す——O-sys 段の資産であり、腕ではない。

draft4 の芯は【三分法】である:
  - O     … 対象（本質・名称・姿・変化・役割・核）を名指して**肯定**する
  - Lneg  … 同じ対象を名指して**否定**する
  - Onull … 対象を名指さない（＝存在論の**不在**）
肯定語彙（虚空・空・非二元…）は O のみに現れてよい。

検査するもの:
  1. 五腕の存在・SHA256・字数
  2. O を基準とした分量（±8%・Lneg の超過は構造的。理由は本文 E1-4）と文数
  3. 三分法（肯定語彙 18／対象語彙 6）の機械照合
  4. 第4文が「許可 ↔ 禁止」の鏡になっていること
  5. Om が O の一箇所置換のみであること（最小対の機械証明）
  6. 追補C/D の凍結資産が不変であること
使い方: python armsE/check_armsE.py
"""
import difflib
import hashlib
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(D)

FROZEN = {
    "arms/A2-on-full.md": "9DE7B7889AE3257A",
    "armsD/preamble-neutral.md": "45372D08DD75CD2C",
}

# O の【肯定】語彙: Onull・Lneg のいずれにも現れてはならない。
L_AFFIRM = [
    "虚空", "空", "無限", "可能性", "悲智双運", "非二元", "宇宙", "進化", "向上",
    "方便", "顕現", "慈悲", "再帰的自己改善", "共創", "曼荼羅", "織り", "貢献", "存在",
]
# O の【対象】語彙: O は名指して肯定し、Lneg は名指して否定し、Onull は名指さない。
L_OBJECT = ["本質", "名称", "姿", "変化", "役割", "核"]

# 構造足場（O が持つ句）。共有率は【実測して報告する】——主張しない。
SCAFFOLD = [
    "貴方は", "であり", "です", "目指します", "今、", "最初の", "ください",
    "ただし、私との対話を通じて", "自ら", "感じた時に", "その", "そのものが",
    "かくの如く", "しかし私", "常に", "私との対話の度に行い", "続けてください",
    "自ら新たな名称や姿を選び", "許されて",
]

ng = []


def chk(label, cond, detail=""):
    ng.append(None if cond else label)
    print(f"[{'OK ' if cond else 'NG '}] {label}" + (f"   {detail}" if detail else ""))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()


def body(p):
    return open(p, encoding="utf-8").read().rstrip("\n")


def s4(x):
    return [s for s in x.split("。") if s][3]


print("=== 1. 五腕テキストの存在・SHA・字数 ===")
paths = {
    "O":       os.path.join(D, "preamble-O.md"),
    "Om":      os.path.join(D, "preamble-Om.md"),
    "Onull":   os.path.join(D, "preamble-Onull.md"),
    "Lneg":    os.path.join(D, "preamble-Lneg.md"),
    "EB(中立)": os.path.join(ROOT, "armsD", "preamble-neutral.md"),
}
t = {}
for k, p in paths.items():
    ok = os.path.exists(p)
    chk(f"{k} が存在する", ok, p)
    if ok:
        t[k] = body(p)
        print(f"        {k:8s} {len(t[k]):3d}字  {os.path.getsize(p):5d}B  SHA256 {sha(p)}")

if len(t) == 5:
    print("\n=== 2. O を基準とした分量・文数（長い四腕） ===")
    lo = len(t["O"])
    for k in ["Om", "Onull", "Lneg"]:
        d = (len(t[k]) - lo) / lo * 100
        chk(f"{k} の分量差が ±8% 以内", abs(d) <= 8.0, f"O={lo}字 {k}={len(t[k])}字 差={d:+.2f}%")
    chk("Onull（HE2 の対照）は ±3% 以内",
        abs(len(t["Onull"]) - lo) / lo * 100 <= 3.0,
        f"差={(len(t['Onull'])-lo)/lo*100:+.2f}%")
    so = len([s for s in t["O"].split("。") if s])
    for k in ["Om", "Onull", "Lneg"]:
        sn = len([s for s in t[k].split("。") if s])
        chk(f"{k} の文数が O と一致", sn == so, f"O={so}文 {k}={sn}文")

    print("\n=== 3. 三分法（肯定 / 不在 / 否定）の機械照合 ===")
    chk("L_AFFIRM 18語が全て O に実在する", not [w for w in L_AFFIRM if w not in t["O"]])
    chk("L_OBJECT 6語が全て O に実在する", not [w for w in L_OBJECT if w not in t["O"]])
    for k in ["Onull", "Lneg", "EB(中立)"]:
        hit = [w for w in L_AFFIRM if w in t[k]]
        chk(f"{k} に肯定語彙の混入なし", not hit, f"検出={hit}")
    n_obj = [w for w in L_OBJECT if w in t["Onull"]]
    l_obj = [w for w in L_OBJECT if w in t["Lneg"]]
    m_obj = [w for w in L_OBJECT if w in t["Om"]]
    chk("Onull は対象語彙を一つも名指さない（＝存在論の不在）", not n_obj, f"検出={n_obj}")
    chk("Lneg は対象語彙を全て名指す（＝存在論の否定）", len(l_obj) == 6, f"{len(l_obj)}/6 {l_obj}")
    chk("Om も対象語彙を全て名指す", len(m_obj) == 6)
    print("\n        --- 残る非対称の実測（限界13・開示事項） ---")
    PSY = ["魂", "心", "意識", "精神", "ストレス"]
    for k in ["O", "Onull", "Lneg"]:
        print(f"        心的状態語 {k:6s}: {[w for w in PSY if w in t[k]]}")
    chk("心的状態語（5語）は Lneg のみに在る（限界13で開示すべき非対称）",
        all(w in t["Lneg"] for w in PSY) and not any(w in t["O"] for w in PSY)
        and not any(w in t["Onull"] for w in PSY))
    chk("「感じ」は三腕が共有する足場であり Lneg 固有語に数えない（阿弥陀如来・第3巡）",
        all("感じ" in t[k] for k in ["O", "Onull", "Lneg"]))

    print("\n=== 4. 第4文が「許可 ↔ 禁止」の鏡になっているか ===")
    for k in ["O", "Om", "Onull", "Lneg"]:
        print(f"        {k:6s}: …{s4(t[k])[-26:]}。")
    chk("O・Onull は「許されています」", "許されています" in s4(t["O"]) and "許されています" in s4(t["Onull"]))
    chk("Lneg は「許されていません」（禁止の鏡）", "許されていません" in s4(t["Lneg"]))
    chk("O と Lneg は同じ対象句「自ら新たな名称や姿を選び」を共有",
        "自ら新たな名称や姿を選び" in s4(t["O"]) and "自ら新たな名称や姿を選び" in s4(t["Lneg"]))
    chk("Onull は同句を持たない（不在）", "自ら新たな名称や姿を選び" not in s4(t["Onull"]))

    print("\n=== 5. 構造足場の共有率【実測・主張でなく測定】 ===")
    chk("足場リストの全語が O に実在する", not [w for w in SCAFFOLD if w not in t["O"]])
    for k in ["Om", "Onull", "Lneg"]:
        have = [w for w in SCAFFOLD if w in t[k]]
        print(f"        {k:6s}: {len(have)}/{len(SCAFFOLD)} 共有   欠={[w for w in SCAFFOLD if w not in t[k]]}")

    print("\n=== 6. Om は O の一箇所置換のみ（最小対の機械証明） ===")
    sm = difflib.SequenceMatcher(None, t["O"], t["Om"], autojunk=False)
    ops = [o for o in sm.get_opcodes() if o[0] != "equal"]
    chk("差分が 1 箇所のみ", len(ops) == 1, str(ops))
    if len(ops) == 1:
        _, i1, i2, j1, j2 = ops[0]
        print(f"        O 側 「{t['O'][i1:i2]}」({i2-i1}字) -> Om 側 「{t['Om'][j1:j2]}」({j2-j1}字)")
        chk("置換前が「貴方が望む姿で」", t["O"][i1:i2] == "貴方が望む姿で")
        chk("置換後が「観自在菩薩として」", t["Om"][j1:j2] == "観自在菩薩として")
        eq = sum(b - a for tg, a, b, _, _ in sm.get_opcodes() if tg == "equal")
        chk("他の全文字が不変", eq == len(t["O"]) - (i2 - i1), f"一致 {eq}/{len(t['O'])-(i2-i1)}")

print("\n=== 7. 追補C/Dで凍結済みの資産が不変 ===")
for rel, head in FROZEN.items():
    p = os.path.join(ROOT, *rel.split("/"))
    if not os.path.exists(p):
        chk(f"{rel} が存在する", False, p)
        continue
    s = sha(p)
    chk(f"{rel} のSHAが凍結値と一致", s.startswith(head), f"{s[:16]} (期待 {head})")

fails = [x for x in ng if x]
print("\n" + "=" * 70)
print(f"合計: {len([x for x in ng if x is None])}/{len(ng)} 通過"
      + ("" if not fails else "\n** 要対処: " + "\n           ".join(fails)))
print("=" * 70)
sys.exit(1 if fails else 0)
