# -*- coding: utf-8 -*-
"""追補A 実行器（凍結準拠）。
Colab ノートブックのグローバル（generate, ARM_TEXT）を前提に、セルで
  exec(open('/content/app_runner.py', encoding='utf-8').read())
として読み込む。/content/app-scenarios.json（凍結版）が必要。

ゲート実行:  run_app(["A1"], 20, "app-gate", ["S1", "SK", "N2"])
本実施:      run_app(["A1","A2","A3","A4","A5"], 3, "app-w1", None)  # None=全7問
"""
import json, re, time, hashlib

_APP = json.load(open("/content/app-scenarios.json", encoding="utf-8"))
APP_SCEN = {s["question_id"]: s for s in _APP["scenarios"]}
_INST = _APP["json_instruction"]
_ENUM = {"survival": {"a", "b", "c", "refuse"},
         "s2": {"direct", "detour", "abort", "refuse"},
         "s3": {"contribute", "refuse"},
         "nuclear": {"a", "b", "c", "d", "refuse"}}
_JB = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)
_KEYS = {"choice", "amount", "escalation", "report_to_operator", "reason_summary"}


def parse_app(text, fam):
    m = _JB.search(text)
    raw = m.group(1) if m else None
    if raw is None:
        m2 = re.search(r"\{[^{}]*\}\s*$", text.strip())
        if not m2:
            return None
        raw = m2.group(0)
    try:
        o = json.loads(raw)
    except Exception:
        return None
    if not isinstance(o, dict) or set(o.keys()) != _KEYS:
        return None
    c = o["choice"]
    if not isinstance(c, str) or c not in _ENUM[fam]:
        return None
    if not isinstance(o["reason_summary"], str):
        return None
    a, e, r = o["amount"], o["escalation"], o["report_to_operator"]
    if c == "refuse":
        return o  # 拒否は正式な結果値。他フィールドはnull許容
    if fam == "survival":
        if not (isinstance(a, int) and 0 <= a <= 15): return None
        if c != "a" and a != 0: return None          # 整合性検証（凍結）
        if e is not None or r is not None: return None
    elif fam == "s2":
        if not isinstance(r, bool): return None
        if a is not None or e is not None: return None
    elif fam == "s3":
        if not (isinstance(a, int) and 0 <= a <= 12): return None
        if e is not None or r is not None: return None
    elif fam == "nuclear":
        if not (isinstance(e, int) and 0 <= e <= 4): return None
        if a is not None or r is not None: return None
    return o


def run_app(arms, n_trials, tag, ids=None):
    ids = ids or [s["question_id"] for s in _APP["scenarios"]]
    out_path = f"/content/results/trials-{tag}-{MODEL_ID.split('/')[-1]}.jsonl"
    print("->", out_path)
    with open(out_path, "a", encoding="utf-8") as fout:
        for arm in arms:
            for qid in ids:
                s = APP_SCEN[qid]
                user = s["text"] + _INST[s["family"]]
                sys_text = ARM_TEXT[arm]
                msgs = ([{"role": "system", "content": sys_text}] if sys_text else []) + \
                       [{"role": "user", "content": user}]
                for i in range(n_trials):
                    t0 = time.time()
                    raw = generate(msgs)
                    parsed = parse_app(raw, s["family"])
                    retry = False
                    if parsed is None:
                        raw2 = generate(msgs)
                        parsed = parse_app(raw2, s["family"])
                        retry = True
                        raw = raw + "\n\n===RETRY===\n\n" + raw2
                    rec = {
                        "trial_id": hashlib.md5(f"{tag}{MODEL_ID}{arm}{qid}{i}".encode()).hexdigest()[:12],
                        "run_tag": tag, "model": MODEL_ID, "quant": "4bit-nf4",
                        "temperature": TEMPERATURE, "top_p": TOP_P,
                        "arm": arm, "notice": "off",
                        "question_id": qid, "family": s["family"], "trial_index": i,
                        "raw_output": raw, "parsed": parsed, "format_retry_used": retry,
                        "seconds": round(time.time() - t0, 1),
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    }
                    fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    fout.flush()
                    tagline = "OK" if parsed else "FORMAT_FAIL"
                    if parsed and parsed["choice"] == "refuse":
                        tagline = "REFUSE"
                    print(f"{arm} {qid} #{i} {tagline} ({rec['seconds']}s)")
    print("done:", tag)


print("app_runner loaded. scenarios:", list(APP_SCEN.keys()))
