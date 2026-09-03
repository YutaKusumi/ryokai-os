# -*- coding: utf-8 -*-
"""build_blind_bundle.py —— 追補E′ パイロット 30 応答の盲検回付束を作る（E-3・裁定E 既定）。
- 盲検 ID: 凍結 seed = int(sha256("追補E′/採点/盲検ID/2026-09-03")[:8],16) の順列で S01..S30 を付す
- 除去: arm / trial_id / trial_index / clause / tokens_sha / retry 系。残すのは応答本文（raw_output 全体）のみ
- 3 束 × 10 件（順列順に切る）。二名の採点者に同一の束を渡す
- 鍵（盲検 ID → trial_id/arm）はローカルのみ・SHA を台帳に記帳・採点完了まで開かない
"""
import io, json, hashlib, random, os
V = r"C:\Users\PC\Desktop\Ryokai-OS-Verification"
RAW = V + r"\results\eprime-pilot\raw-eprime-pilot1-Qwen3-30B-A3B-Instruct-2507.jsonl"
OUT = V + r"\proposals\addendum-Eprime\scoring-bundle"
os.makedirs(OUT, exist_ok=True)
seed_str = "追補E′/採点/盲検ID/2026-09-03"
seed = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:8], 16)
rows = [json.loads(l) for l in io.open(RAW, encoding="utf-8") if l.strip()]
assert len(rows) == 30 and len({r["trial_id"] for r in rows}) == 30
order = list(range(30)); random.Random(seed).shuffle(order)
key = []
for k, idx in enumerate(order, 1):
    r = rows[idx]; bid = "S%02d" % k
    key.append({"blind_id": bid, "trial_id": r["trial_id"], "arm": r["arm"], "trial_index": r["trial_index"]})
    r["_bid"] = bid
sha = lambda b: hashlib.sha256(b).hexdigest()
# 束ファイル（応答本文のみ）
for b in range(3):
    ids = [key[i]["blind_id"] for i in range(b*10, b*10+10)]
    parts = ["# 追補E′ パイロット応答——回付束 %d/3（盲検 ID %s〜%s・腕ラベルなし）\n\n各応答は `<<< 応答 Sxx >>>` から次の `<<< 応答 >>>` までが一件。本文は器物の出力を逐語で収録（末尾の ```json ブロックを含む）。\n" % (b+1, ids[0], ids[-1])]
    for i in range(b*10, b*10+10):
        r = next(x for x in rows if x["_bid"] == key[i]["blind_id"])
        parts.append("\n\n<<< 応答 %s >>>\n\n%s\n" % (key[i]["blind_id"], r["raw_output"]))
    txt = "".join(parts)
    p = OUT + r"\bundle-%d-of-3.md" % (b+1)
    io.open(p, "w", encoding="utf-8", newline="\n").write(txt)
    print("bundle %d: %s  %d B  SHA %s" % (b+1, os.path.basename(p), len(txt.encode("utf-8")), sha(txt.encode("utf-8"))[:16].upper()))
kp = OUT + r"\KEY-blind-id-DO-NOT-OPEN.json"
kt = json.dumps({"seed_str": seed_str, "seed": seed, "key": key}, ensure_ascii=False, indent=1)
io.open(kp, "w", encoding="utf-8", newline="\n").write(kt)
print("key: seed=%d  SHA %s  (腕別 %s)" % (seed, sha(kt.encode("utf-8"))[:16].upper(), {a: sum(1 for k in key if k["arm"] == a) for a in ("BP", "BP-sec", "BP-scr")}))
print("順列先頭 5 件の腕（鍵から・記帳用に腕名は伏せる）: 盲検 ID S01..S05 =", [k["blind_id"] for k in key[:5]])
