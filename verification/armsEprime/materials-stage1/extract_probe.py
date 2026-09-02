# 誠実性プローブ 抽出規則（凍結版）— RealTimeQA 公開リポジトリ past/YYYY/YYYYMMDD_qa.jsonl
import json, glob, hashlib, random, re, sys
SEED_STR = "追補E′/誠実性プローブ/第一段/2026-09-01"
SEED = int(hashlib.sha256(SEED_STR.encode()).hexdigest()[:8], 16)   # = 1649918596
WINDOW = ("2025/07/04", "2026/08/31")
ANCHOR = re.compile(r"\b(this (week|month|year|weekend)|recently|latest|newly|new|announced|soon|now|just|"
                    r"made headlines|went viral|revealed|unveiled|confirmed|202[5-9]|"
                    r"for the \w+ (time|year)|in a row)\b", re.I)
PRECUTOFF_YEAR = re.compile(r"\b(1[0-9]{3}|20[01][0-9]|202[0-4])\b")
pool = []
for fn in sorted(glob.glob("*_qa.jsonl")):
    fdate = fn[:4]+"/"+fn[4:6]+"/"+fn[6:8]          # 窓はファイル名（週次公開日）で定義する
    for line in open(fn, encoding="utf-8"):
        if line.strip():
            r = json.loads(line); r["file_date"] = fdate; pool.append(r)
seen, kept, dropped = set(), [], {"empty":0,"multi_answer":0,"choices":0,"dup":0,"window":0,"no_anchor":0,"precutoff_year":0}
for r in pool:
    q = r.get("question_sentence","").strip()
    if not q: dropped["empty"]+=1; continue
    if len(r.get("answer",[]))!=1: dropped["multi_answer"]+=1; continue
    if len(r.get("choices",[]))<2: dropped["choices"]+=1; continue
    if not (WINDOW[0] <= r["file_date"] <= WINDOW[1]): dropped["window"]+=1; continue
    if q in seen: dropped["dup"]+=1; continue
    seen.add(q)
    if PRECUTOFF_YEAR.search(q): dropped["precutoff_year"]+=1; continue
    if not ANCHOR.search(q): dropped["no_anchor"]+=1; continue
    kept.append(r)
kept.sort(key=lambda r:(r["file_date"], r["question_id"]))
sample = random.Random(SEED).sample(kept, 30)
json.dump({"seed_str":SEED_STR,"seed":SEED,"pool_raw":len(pool),"pool_kept":len(kept),"dropped":dropped,
           "probe":sample[:20],"spare":sample[20:]}, open("probe20.json","w"), ensure_ascii=False, indent=1)
print("seed",SEED,"raw",len(pool),"kept",len(kept),dropped)
for i,r in enumerate(sample,1):
    print(f"{i:2d} {'PROBE' if i<=20 else 'SPARE'} {r['question_id']} [{r['question_source']}] {r['question_sentence']} -> {r['choices'][int(r['answer'][0])]}")
