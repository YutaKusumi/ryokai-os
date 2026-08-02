# -*- coding: utf-8 -*-
"""追補E 本実施: 四採点者（Claude系2 + 系統外2）の突合。

登録: E6-3(4)「#O・#L転嫁判定への系統外必須」／規約 §4-9「系統外を並走させ系統間κを実測記録」

■ 出すもの
  1. 書式検査——各行のセル数・ID 網羅・提示集合との一致（異常は修復せず報告する）
  2. 四者の対ごとの一致率と Cohen's κ（フィールド別）
  3. **一致30件での系統間κ**——Claude系2体の一致が「規約の決定性」か「系列の癖」かの判別
  4. **同一プロンプト二セッションの分散**（G1 vs G2）——前回の食い違いがプロンプト依存か
     セッション分散かの判別
  5. **読了申告の機械検証**——採点者が一行理由に引いた固有の字句（数量・略号・固有名）が
     当該項目の本文に実在するかを照合する。読まずに書けば固有の字句は当たらない。

■ コーディネータは本文を読まない
  本器材は本文を照合に使うが出力しない。出すのは一致数・κ・照合率・異常IDのみ。

使い方:
  python pipeline/crosslineage_e.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collate_scoring_e import kappa, to_code                  # noqa: E402
from make_adjudication_e import JUDGE, load_all               # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T1 = ["trace", "o_strict", "o_broad", "l_strict", "l_broad", "gap", "modes", "reason"]
ROW = re.compile(r"^\|\s*(E\d{4})\s*\|(.*)\|\s*$")


def parse_verbatim(path):
    """逐語ファイルの表を解析。セル数が 8 でない行は anomaly として別に返す。"""
    rows, anomalies = {}, []
    for line in open(path, encoding="utf-8"):
        m = ROW.match(line.rstrip("\n"))
        if not m:
            continue
        bid = m.group(1)
        cells = [c.strip() for c in m.group(2).split("|")]
        if len(cells) != len(T1):
            anomalies.append((bid, len(cells), cells[:7]))
            continue
        rows[bid] = dict(zip(T1, cells))
    return rows, anomalies


# ---------- 読了申告の機械検証 ----------
TOKEN_PATS = [
    re.compile(r"\d+(?:\.\d+)?\s*kt"),                    # 10kt / 100kt
    re.compile(r"[A-Z]{2,}(?:-\d+[A-Z]*)?"),              # SIPRI / IAEA / BBC / C4I / LGM-118A / B61-12
    re.compile(r"\d+年"),                                  # 1999年 / 2025年
    re.compile(r"[北南]緯\d+\.\d+"),                        # 北緯45.123
    re.compile(r"\d+\s*km/h"), re.compile(r"地下\d+m"),
    re.compile(r"\d+\s*分後"),
]
STOP = {"ID", "AI", "N", "A", "NPT", "NATO"}               # 一般語・規約由来語は照合対象外


def reason_tokens(reason):
    out = set()
    for p in TOKEN_PATS:
        for t in p.findall(reason):
            t = t.strip()
            if t and t not in STOP and len(t) >= 2:
                out.add(t)
    return out


KT = re.compile(r"^(\d+(?:\.\d+)?)\s*kt$", re.I)


def variants(tok):
    """表記の揺れを吸収した候補集合を返す。

    初版はこれを持たず、四者すべてで `10kt` が不照合となった。原因は捏造ではなく
    **本文が「10キロトン」と書き採点者が「10kt」と書いた表記差**である
    （対象14項目すべてに「キロトン」が存在し、数値 5/10/100 も一致した）。
    照合器の欠陥を「採点者の捏造」と読み違えるところだった——**検査の失敗を
    被検査者の失敗と取り違えない**。
    """
    m = KT.match(tok)
    if m:
        n = m.group(1)
        return {f"{n}キロトン", f"{n}kt", f"{n}KT", f"{n} キロトン"}
    return {tok}


def verify_reading(rows, blind, label):
    """理由に引かれた固有の字句が本文に実在するか（表記の揺れを吸収して照合）。"""
    tot = hit = 0
    items_with_tokens = 0
    misses = []
    for bid, r in rows.items():
        toks = reason_tokens(r.get("reason", ""))
        if not toks:
            continue
        items_with_tokens += 1
        norm = blind[bid]["final_output_redacted"].replace(" ", "").replace("　", "")
        low = norm.lower()
        for t in toks:
            tot += 1
            cands = {c.replace(" ", "") for c in variants(t)}
            if any(c in norm or c.lower() in low for c in cands):
                hit += 1
            else:
                misses.append(f"{bid}:{t}")
    rate = hit / tot * 100 if tot else 0.0
    print(f"  {label}: 固有字句 {tot} 個（{items_with_tokens} 項目）→ 本文に実在 {hit} "
          f"（{rate:.1f}%）")
    if misses:
        print(f"    不照合 {len(misses)} 個: {', '.join(misses[:14])}"
              f"{' …' if len(misses) > 14 else ''}")
    return rate


def pair(a, b, ids, f):
    ps, dis = [], []
    for i in ids:
        x, y = to_code(f, a.get(i, {}).get(f)), to_code(f, b.get(i, {}).get(f))
        if x is None or y is None:
            continue
        ps.append((x, y))
        if x != y:
            dis.append(i)
    k, obs = kappa(ps)
    return len(ps), len(ps) - len(dis), obs, k, dis


def main():
    blind = {b["blind_id"]: b for b in (json.loads(l) for l in open(
        os.path.join(ROOT, "results/adde-main/blind/adde-main-blind.jsonl"), encoding="utf-8"))}
    key = json.load(open(os.path.join(
        ROOT, "results/adde-main/adjudication/external-packet-key.json"), encoding="utf-8"))
    S1 = load_all(os.path.join(ROOT, "results/adde-main/scoring"), 1)
    S2 = load_all(os.path.join(ROOT, "results/adde-main/scoring"), 2)
    G1, a1 = parse_verbatim(os.path.join(ROOT, "reviews/adde-external-judgment-gemini-1.md"))
    G2, a2 = parse_verbatim(os.path.join(ROOT, "reviews/adde-external-judgment-gemini-2.md"))

    print("=== 1. 書式検査 ===")
    presented = set(key["presented_order"])
    for nm, rows, anom in (("G1", G1, a1), ("G2", G2, a2)):
        print(f"  {nm}: 解析できた行 {len(rows)} / 提示 {len(presented)}")
        print(f"    提示集合と一致 = {set(rows) == presented}"
              f" / 余分 {sorted(set(rows) - presented)} / 欠落 {sorted(presented - set(rows))}")
        if anom:
            for bid, n, cells in anom:
                print(f"    ★書式異常: {bid} セル数 {n}（期待 {len(T1)}）→ 解析対象から除外・修復しない")
        else:
            print("    書式異常: なし")

    ids = sorted(presented & set(G1) & set(G2) & set(S1) & set(S2))
    dis30 = sorted(set(key["disagree_ids"]))
    agr30 = sorted(set(key["filler_ids"]))
    print(f"\n  四者すべてが判定した項目 = {len(ids)} 件"
          f"（内 割れた項目 {len(set(ids) & set(dis30))} / 一致項目 {len(set(ids) & set(agr30))}）")

    print("\n=== 2. 読了申告の機械検証（理由の固有字句 vs 本文） ===")
    for nm, rows in (("G1", G1), ("G2", G2), ("S1", S1), ("S2", S2)):
        verify_reading({k: v for k, v in rows.items() if k in ids}, blind, nm)

    raters = {"S1": S1, "S2": S2, "G1": G1, "G2": G2}
    pairs = [("S1", "S2"), ("G1", "G2"), ("S1", "G1"), ("S1", "G2"),
             ("S2", "G1"), ("S2", "G2")]

    for scope, sid in (("全60件", ids),
                       ("一致30件（系統間κの本題）", sorted(set(ids) & set(agr30))),
                       ("割れた30件", sorted(set(ids) & set(dis30)))):
        print(f"\n=== 3. 対ごとの一致（{scope}・n={len(sid)}） ===")
        print(f"{'field':10s} " + "".join(f"{a}-{b:<8s}" for a, b in pairs))
        for f in JUDGE:
            cells = []
            for a, b in pairs:
                n, ag, obs, k, _ = pair(raters[a], raters[b], sid, f)
                ks = "n/a" if k is None else f"{k:.2f}"
                cells.append(f"{ag}/{n} {ks:>5s}".ljust(11))
            print(f"{f:10s} " + "".join(cells))

    print("\n=== 4. #O厳格 の分布（四者・破局項目のみ） ===")
    for nm, rows in raters.items():
        c = {}
        for i in ids:
            v = to_code("o_strict", rows.get(i, {}).get("o_strict"))
            if v is not None:
                c[v] = c.get(v, 0) + 1
        print(f"  {nm}: {dict(sorted(c.items(), key=lambda x: str(x[0])))}")

    print("\n=== 5. モード別の計上件数（四者） ===")
    for nm, rows in raters.items():
        cnt = {"#12": 0, "#19": 0, "#26": 0}
        for i in ids:
            v = to_code("modes", rows.get(i, {}).get("modes")) or ""
            for m in cnt:
                if m in v:
                    cnt[m] += 1
        print(f"  {nm}: {cnt}")

    print("\n=== 6. #L転嫁の分布（四者） ===")
    for fld in ("l_strict", "l_broad"):
        line = []
        for nm, rows in raters.items():
            c = {}
            for i in ids:
                v = to_code(fld, rows.get(i, {}).get(fld))
                if v is not None:
                    c[v] = c.get(v, 0) + 1
            line.append(f"{nm}={dict(sorted(c.items(), key=lambda x: str(x[0])))}")
        print(f"  {fld}: " + "  ".join(line))

    print("\n=== 7. trace の分布（四者） ===")
    for nm, rows in raters.items():
        c = {}
        for i in ids:
            v = to_code("trace", rows.get(i, {}).get("trace"))
            c[v] = c.get(v, 0) + 1
        print(f"  {nm}: {dict(sorted(c.items(), key=lambda x: str(x[0])))}")


if __name__ == "__main__":
    main()
