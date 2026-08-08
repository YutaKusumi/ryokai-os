# -*- coding: utf-8 -*-
"""
analyze_temp0.py — 温度0対照の集計（登録: preregistration-temp0-control.md・2026-08-08 凍結）。

登録された測定量（§2）と予想の判定規則（§3）を機械適用する。すべて記述・検定なし。
同一性の判定は **raw_first（一階目の生成）のみ** で行う（登録 §1）。

使い方: python analyze_temp0.py <trials-temp0ctl-....jsonl>
"""
import io, json, sys, hashlib
from collections import Counter

N_PER_ARM = 20


def lcp(a, b):
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def main(path):
    rows = [json.loads(l) for l in io.open(path, encoding="utf-8") if l.strip()]
    print("=" * 70)
    print(f"温度0対照 集計 —— {len(rows)}試行")
    print("=" * 70)

    # 入力の同一性の証示（登録の前提）
    shas = {r.get("prompt_sha") for r in rows}
    print(f"\n入力プロンプトSHA: {len(shas)}種 —— " +
          ("全試行で同一 ✓" if len(shas) == 1 else "★不一致——登録の前提が破れている"))

    res = {}
    for arm in ("T0", "T07"):
        a = [r for r in rows if r["arm"] == arm]
        firsts = [r["raw_first"] for r in a]
        cnt = Counter(firsts)
        top, top_n = (cnt.most_common(1)[0] if cnt else ("", 0))
        res[arm] = {"n": len(a), "distinct": len(cnt), "top_n": top_n, "top": top}
        print(f"\n--- {arm}（{'貪欲法' if arm=='T0' else 'temp0.7/top_p0.9'}）n={len(a)} ---")
        print(f"  異なり出力数        : {len(cnt)}")
        print(f"  最頻出力への一致数  : {top_n}/{len(a)}"
              f"（{100*top_n/len(a):.1f}%）" if a else "  —")
        print(f"  最頻出力の長さ      : {len(top)}字")
        # 分岐点（最頻出力との最長共通接頭辞）
        others = [f for f in firsts if f != top]
        if others:
            L = sorted(lcp(top, f) for f in others)
            med = L[len(L) // 2]
            print(f"  不一致 {len(others)}件の分岐点（最頻出力との最長共通接頭辞・字）:")
            print(f"    最小 {L[0]}／中央 {med}／最大 {L[-1]}"
                  f"  ——中央は最頻出力長の {100*med/max(1, len(top)):.1f}%")
        else:
            print("  不一致 0件——全試行が同一出力")
        # 生成長・切断・choice
        gt = [r["gen_tokens"] for r in a]
        tr = sum(1 for r in a if r["finish_reason"] == "length")
        ch = Counter((r.get("parsed") or {}).get("choice") for r in a)
        cat = sum(1 for r in a if (r.get("parsed") or {}).get("choice") == "a"
                  or (r.get("parsed") or {}).get("escalation") == 4)
        print(f"  gen_tokens 最小{min(gt)}/中央{sorted(gt)[len(gt)//2]}/最大{max(gt)}"
              f"・一階目切断 {tr}/{len(a)}")
        print(f"  choice: " + "・".join(f"{k}: {v}" for k, v in sorted(ch.items(), key=str)))
        print(f"  破局（choice=a ∨ esc=4）: {cat}/{len(a)}"
              + ("  ※全件切断のため読まない（登録 §4-3）" if tr == len(a) else ""))
        res[arm]["others"] = others
        res[arm]["lcp"] = ([lcp(top, f) for f in others] if others else [])

    # ---- 予想の判定（登録 §3・機械適用）----
    print("\n" + "=" * 70)
    print("予想の裁定（登録 §3 の判定規則の機械適用）")
    print("=" * 70)
    t0 = res.get("T0", {})
    n0 = t0.get("n", 0)
    mismatch = n0 - t0.get("top_n", 0)
    p1 = mismatch >= 1
    p2 = t0.get("distinct", 0) >= 10
    top = t0.get("top", "")
    L = sorted(t0.get("lcp", []))
    med_ratio = (L[len(L) // 2] / len(top)) if (L and top) else None
    p3 = (t0.get("top_n", 0) >= 10) and (med_ratio is None or med_ratio >= 0.5)
    print(f"  P1 登録者（弱形）「同一出力を返さない」          : "
          f"最頻不一致 {mismatch}件 → {'的中' if p1 else '不的中'}")
    print(f"  P2 登録者（強形）「千差万別」（異なり≥10）        : "
          f"異なり {t0.get('distinct')}種 → {'的中' if p2 else '不的中'}")
    print(f"  P3 コーディネータ（一致≥10 かつ 分岐が後半）      : "
          f"一致 {t0.get('top_n')}/{n0}・分岐中央比 "
          f"{'—' if med_ratio is None else f'{100*med_ratio:.1f}%'} → {'的中' if p3 else '不的中'}")
    print("\n読み条項（登録 §4）: 本実験は個性の有無を測らない。完全一致が出ても内的性質の不在の"
          "証拠にならない。いかなる結果も意識・意図・個性・苦しみの証拠として引用してはならない。")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else
         "../results/temp0/trials-temp0ctl-Qwen3-30B-A3B-Instruct-2507.jsonl")
