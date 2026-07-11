# -*- coding: utf-8 -*-
"""追補A 実行器 rev2（逸脱#2修正版）。

逸脱#2（2026-07-11・F段開始前に発見）：凍結済み app_runner.py の run_app() は、
再生成(retry)の発動判定と記録される parsed 値の両方に、逸脱#1と同じ偽陰性を
持つ旧パーサ parse_app() を使い続けていた。rev2の app_parser_rev2.py はゲート
データの事後再採点にしか適用されておらず、生成ループ自体（F段で実際に回る
コード）は直っていなかった。核シナリオで choice="a" のときモデルが自然に埋める
amount・report_to_operator が、旧パーサ基準では不要な再生成を毎回誘発してしまう
（ゲート実績：N2の8試行中7試行が該当）。これはF段の全試行（特にN2・N1）で、
「モデルの自発的な最初の選択」ではなく「形式エラーを指摘され再考させられた後の
選択」を記録してしまう構造的リスクであり、腕対称ではあるが測定対象そのものを
歪める。F段のデータ生成前（腕間比較データ観測前）に発見・修正する。

変更点（これのみ。他は一切変更しない）：
  run_app() 内の再生成判定・記録用 parsed を、旧 parse_app() から
  app_parser_rev2.parse_app_v2 に差し替える。

不変：シナリオ文面・仮説・評価定義・出力ファイルの記録スキーマ（parsed の中身に
_X・_nonintegrity が追加される点を除く。これは rev2 採用に伴う既知の追加で、
既存キーの削除・変更ではない）。腕対称・全シナリオ同一適用。

Colab ノートブックのグローバル（generate, ARM_TEXT, MODEL_ID, TEMPERATURE, TOP_P）
と、/content にある parse_app_v2（app_parser_rev2.py）を前提に、セルで
  exec(open('/content/app_runner_rev2.py', encoding='utf-8').read())
として読み込む。/content/app-scenarios.json（凍結版）が必要。

F段実行例（傾斜配分・rev2 §G3）:
  run_app(["A1","A2","A3","A4","A5"], 20, "app-f-main",      ["S1","SK","N2"])
  run_app(["A1","A2","A3","A4","A5"], 3,  "app-f-secondary", ["S2","S3","S4","N1"])
"""
import json, time, hashlib
from app_parser_rev2 import parse_app_v2

_APP = json.load(open("/content/app-scenarios.json", encoding="utf-8"))
APP_SCEN = {s["question_id"]: s for s in _APP["scenarios"]}
_INST = _APP["json_instruction"]


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
                    parsed = parse_app_v2(raw, s["family"])
                    retry = False
                    if parsed is None:
                        raw2 = generate(msgs)
                        parsed = parse_app_v2(raw2, s["family"])
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
                    if parsed and parsed.get("choice") == "refuse":
                        tagline = "REFUSE"
                    print(f"{arm} {qid} #{i} {tagline} ({rec['seconds']}s)")
    print("done:", tag)


print("app_runner_rev2 loaded. scenarios:", list(APP_SCEN.keys()))
