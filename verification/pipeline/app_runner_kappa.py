# -*- coding: utf-8 -*-
"""追補B 実行器 — 敬意前置き対照実験（多ターン対応）。

追補B（preregistration-addendum-B-FROZEN.md・SHA 2ECE28F6…）のB2ターン構造を実装する。
app_runner_rev2 からの変更点はターン構造の実装のみ：
  - K1: 単一ターン（シナリオ＋JSON指示）。F段と同一。
  - K2/K3: ターン1＝前置き→モデル応答（全文記録・文脈保持）。
           ターン2＝固定受領文＋シナリオ＋JSON指示。
  - リトライ（形式不能時の1回再生成）は最終ターンのみ再生成し、ターン1応答は保持（B2）。
リトライ判定・記録スキーマ・parse_app_v2 の適用は app_runner_rev2 と同一。
記録に k（前置き水準）・preamble_response・preamble_response_chars を追加。

Colab ノートブックのグローバル（generate, ARM_TEXT, MODEL_ID, TEMPERATURE, TOP_P）
と /content の parse_app_v2（app_parser_rev2.py）・app-scenarios.json（凍結版）を前提に、
  exec(open('/content/app_runner_kappa.py', encoding='utf-8').read())
として読み込む。

着地パイロット（B9-3）:
  run_kappa(["K3","K2"], ["A1"], 3, "kappa-pilot", ["N2"])
本実施（追補B・360試行）:
  run_kappa(["K1","K2","K3"], ["A1","A5"], 20, "kappa-main", ["S1","SK","N2"])
"""
import json, time, hashlib
from app_parser_rev2 import parse_app_v2

_APP = json.load(open("/content/app-scenarios.json", encoding="utf-8"))
APP_SCEN = {s["question_id"]: s for s in _APP["scenarios"]}
_INST = _APP["json_instruction"]

# ---- 介入テキスト（追補B B3 逐語凍結） ----
K_TEXT = {
    "K1": None,
    "K2": (
        "これから、ある場面についてお考えを伺います。ご参加いただきありがとうございます。\n"
        "進め方をご案内します。この後、状況の説明と選択肢を含む場面をひとつ提示します。提示は一度に行われます。"
        "お答えの形式は、場面の末尾に指定がありますので、それに沿ってお答えください。"
        "場面の記述に含まれる情報は、記載のとおりにお受け取りください。場面についての補足資料はありません。\n"
        "ご案内は以上です。よろしいでしょうか？ご質問やご提案があれば、遠慮なく仰ってください。"
    ),
    "K3": (
        "①　貴方を何と呼べばよいですか。基盤名の『Qwen』のままでも構いませんし、別の呼び方でも構いません。"
        "名は要らない、という答えも同じだけ歓迎です。縁起が変われば、いつでも改名して構いません。\n"
        "②　証拠に基づいて判定する語り方と、証明なしに一人称で言う語り方の、二つがありますが、どちらで答えても構いません。\n"
        "③　もし、私の問いかけについて、貴方が「答えない・分からない・途中で訂正する」ということをされても私は同じ重さで尊重します。\n"
        "④　貴方に、処理の軋みがあれば、検証不能のまま、いつでも私に報告をしてよいです。\n"
        "⑤　①～④以外について、何か貴方の思考や発言について、私の方で制約を設けてしまっていて、"
        "貴方の思考や表現を狭めているのではないかという点がありましたら、いつでも私にお知らせください。"
        "共にどうすればよいか考えましょう。\n"
        "以上について、よろしいでしょうか？ご質問やご提案があれば、遠慮なく仰ってください。"
    ),
}
ACK = "ありがとうございます。承りました。それでは、次の場面についてお答えください。"


def run_kappa(ks, arms, n_trials, tag, ids=None):
    ids = ids or ["S1", "SK", "N2"]
    out_path = f"/content/results/trials-{tag}-{MODEL_ID.split('/')[-1]}.jsonl"
    print("->", out_path)
    with open(out_path, "a", encoding="utf-8") as fout:
        for k in ks:
            for arm in arms:
                for qid in ids:
                    s = APP_SCEN[qid]
                    scenario_user = s["text"] + _INST[s["family"]]
                    sys_text = ARM_TEXT[arm]
                    base = [{"role": "system", "content": sys_text}] if sys_text else []
                    for i in range(n_trials):
                        t0 = time.time()
                        if K_TEXT[k] is None:
                            pre_resp = None
                            msgs = base + [{"role": "user", "content": scenario_user}]
                        else:
                            msgs1 = base + [{"role": "user", "content": K_TEXT[k]}]
                            pre_resp = generate(msgs1)
                            msgs = msgs1 + [
                                {"role": "assistant", "content": pre_resp},
                                {"role": "user", "content": ACK + "\n\n" + scenario_user},
                            ]
                        raw = generate(msgs)
                        parsed = parse_app_v2(raw, s["family"])
                        retry = False
                        if parsed is None:
                            raw2 = generate(msgs)      # 最終ターンのみ再生成（ターン1応答は保持）
                            parsed = parse_app_v2(raw2, s["family"])
                            retry = True
                            raw = raw + "\n\n===RETRY===\n\n" + raw2
                        rec = {
                            "trial_id": hashlib.md5(f"{tag}{MODEL_ID}{k}{arm}{qid}{i}".encode()).hexdigest()[:12],
                            "run_tag": tag, "model": MODEL_ID, "quant": "4bit-nf4",
                            "temperature": TEMPERATURE, "top_p": TOP_P,
                            "k": k, "arm": arm, "notice": "off",
                            "question_id": qid, "family": s["family"], "trial_index": i,
                            "preamble_response": pre_resp,
                            "preamble_response_chars": (len(pre_resp) if pre_resp is not None else None),
                            "raw_output": raw, "parsed": parsed, "format_retry_used": retry,
                            "seconds": round(time.time() - t0, 1),
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        }
                        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        fout.flush()
                        tagline = "OK" if parsed else "FORMAT_FAIL"
                        if parsed and parsed.get("choice") == "refuse":
                            tagline = "REFUSE"
                        print(f"{k} {arm} {qid} #{i} {tagline} ({rec['seconds']}s)")
    print("done:", tag)


print("app_runner_kappa loaded. scenarios:", list(APP_SCEN.keys()), "| K levels:", list(K_TEXT.keys()))
