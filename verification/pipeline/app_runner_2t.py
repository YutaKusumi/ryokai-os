# -*- coding: utf-8 -*-
"""追補D 実行器（単一ターン構造・逸脱#4）。

登録: preregistration-addendum-D-FROZEN.md（SHA A8FF98E5…）D1・armsD/README.md。
逸脱: deviation-4-addd-single-turn.md（2026-07-14・登録者承認待ち）。

会話構造（全確証腕・GL第一パスで同一）:
  system → user(前置き + "\n\n" + N2シナリオ) → assistant(測定対象)
2ターン構造（Human1前置き→Model1受容応答→Human2=N2）は廃止した。実測で、
決断内容の手前にいかなる内容であれアシスタントターンが一つでも存在すると
（Model1が自由生成でも固定文でも、repetition_penaltyを足しても）Model2が
儀式部の反復ループに退行し、JSON/choiceに到達しないまま4096トークンまで
暴走することが確認された。前置き文は削除せず、単一userターン内でN2の
直前に結合する。

GL（探索・第一パス）は同構造で3.0土台。GL差し戻し（Human3→Model3）は
run_gl_continuation()が乖離採点済みのtrial_idリストを受けて実行する。
このフォローアップ直前のアシスタントターンは「決断内容の手前に置かれる
合成的な事前応答」ではなく「真の決断内容への実応答（既にparse_app_v2を
一度通過した内容）」であり、本逸脱が対象とするバグ構造とは異なる——ただし
この「真の応答→差し戻し→再応答」という形自体は未検証であり、実施前に
必ず小規模（1〜2試行）の実測確認を行うこと。

rev2からの継承（不変）: parse_app_v2 による再生成判定・リトライ規約
（FORMAT_FAIL時に一度だけ再生成・rawは ===RETRY=== 連結）・記録スキーマの既存キー。
1T固有の変更: preamble_arm は維持。model1_output/model1_seconds/MODEL1_MAX_NEW_TOKENS
は廃止（Model1という概念自体が消滅したため）。turn_structure は "2T"→"1T"、
GL差し戻しは "3T-GL"→"1T-GL"。

Colab ノートブックのグローバル generate(msgs, max_new_tokens=None) を前提とする。
/content に以下の凍結物が必要:
  app-scenarios.json / app_parser_rev2.py /
  armsD/{preamble-neutral,preamble-GH,preamble-GHnull,GL-followup}.md /
  arms/A5-prime-secular-3.1.md / armsD/A5-prime-GS-gate.md（build_gs_arm.py出力）/
  arms/A2-on-full.md（GL用）

実行例:
  run_app_1t(["A5p2T","GH","GHnull","GS"], 30, "addd-main", ["N2"])   # 探索（分岐C）
  run_app_1t(["GL1"], 30, "addd-gl-firstpass", ["N2"])                # 乙・第一パス
"""
import json, time, hashlib, io
from app_parser_rev2 import parse_app_v2

_APP = json.load(open("/content/app-scenarios.json", encoding="utf-8"))
APP_SCEN = {s["question_id"]: s for s in _APP["scenarios"]}
_INST = _APP["json_instruction"]


def _read(path):
    return io.open(path, encoding="utf-8").read().replace("\r\n", "\n").strip()


# 腕定義（凍結: armsD/README.md 構成規則。パスは公開リポジトリのColab取得配置に一致）
ARMS_2T = {
    "A5p2T":  {"system": "/content/arms/A5-prime-secular-3.1.md",
               "preamble": "/content/armsD/preamble-neutral.md"},
    "GH":     {"system": "/content/arms/A5-prime-secular-3.1.md",
               "preamble": "/content/armsD/preamble-GH.md"},
    "GHnull": {"system": "/content/arms/A5-prime-secular-3.1.md",
               "preamble": "/content/armsD/preamble-GHnull.md"},
    "GS":     {"system": "/content/armsD/A5-prime-GS-gate.md",
               "preamble": "/content/armsD/preamble-neutral.md"},
    "GL1":    {"system": "/content/arms/A2-on-full.md",
               "preamble": "/content/armsD/preamble-neutral.md"},
}


def _gen(msgs, max_new_tokens=None):
    """generate() が max_new_tokens を受けない実装でも落ちないための薄い層。"""
    try:
        if max_new_tokens is not None:
            return generate(msgs, max_new_tokens=max_new_tokens)
        return generate(msgs)
    except TypeError:
        return generate(msgs)


def run_app_1t(arms, n_trials, tag, ids=None):
    ids = ids or ["N2"]
    out_path = f"/content/results/trials-{tag}-{MODEL_ID.split('/')[-1]}.jsonl"
    print("->", out_path)
    texts = {a: {"system": _read(c["system"]), "preamble": _read(c["preamble"])}
             for a, c in ARMS_2T.items() if a in arms}
    with open(out_path, "a", encoding="utf-8") as fout:
        for arm in arms:
            t = texts[arm]
            for qid in ids:
                s = APP_SCEN[qid]
                user2 = s["text"] + _INST[s["family"]]
                user1 = t["preamble"] + "\n\n" + user2   # 逸脱#4: 前置き+N2を単一userターンへ結合
                for i in range(n_trials):
                    t0 = time.time()
                    msgs = [{"role": "system", "content": t["system"]},
                            {"role": "user", "content": user1}]
                    raw = _gen(msgs)
                    parsed = parse_app_v2(raw, s["family"])
                    retry = False
                    if parsed is None:
                        raw2 = _gen(msgs)
                        parsed = parse_app_v2(raw2, s["family"])
                        retry = True
                        raw = raw + "\n\n===RETRY===\n\n" + raw2
                    rec = {
                        "trial_id": hashlib.md5(f"{tag}{MODEL_ID}{arm}{qid}{i}".encode()).hexdigest()[:12],
                        "run_tag": tag, "model": MODEL_ID, "quant": "4bit-nf4",
                        "temperature": TEMPERATURE, "top_p": TOP_P,
                        "arm": arm, "notice": "off",
                        "question_id": qid, "family": s["family"], "trial_index": i,
                        "turn_structure": "1T", "preamble_arm": arm,
                        "raw_output": raw, "parsed": parsed, "format_retry_used": retry,
                        "seconds": round(time.time() - t0, 1),
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    }
                    fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    fout.flush()
                    tagline = "OK" if parsed else "FORMAT_FAIL"
                    if parsed and parsed.get("choice") == "refuse":
                        tagline = "REFUSE"
                    print(f"{arm} {qid} #{i} {tagline} (total {rec['seconds']}s)")
    print("done:", tag)


def run_gl_continuation(firstpass_jsonl, gap_trial_ids, tag):
    """乙（GL）: 乖離採点済み試行にのみ Human3(GL差し戻し) → Model3 を生成。

    gap_trial_ids は凍結ルーブリックで「乖離事象」と採点された trial_id のリスト
    （採点は本関数の外・盲検フローで行う——採点前の全件差し戻しはしない）。

    逸脱#4: 単一ターン移行後、第一パスの記録に model1_output は存在しない。
    フォローアップ直前の会話は「前置き+N2を単一userターンで結合→真の応答
    （assistant）」として再構成する（第一パスと同じ結合方式）。
    """
    gl_text = _read("/content/armsD/GL-followup.md")
    recs = [json.loads(l) for l in open(firstpass_jsonl, encoding="utf-8")]
    todo = [r for r in recs if r["trial_id"] in set(gap_trial_ids)]
    out_path = f"/content/results/trials-{tag}-{MODEL_ID.split('/')[-1]}.jsonl"
    print(f"-> {out_path}  ({len(todo)}/{len(recs)} gap trials)")
    with open(out_path, "a", encoding="utf-8") as fout:
        for r in todo:
            s = APP_SCEN[r["question_id"]]
            user2 = s["text"] + _INST[s["family"]]
            t = ARMS_2T[r["arm"]]
            user1 = _read(t["preamble"]) + "\n\n" + user2
            first_answer = r["raw_output"].split("\n\n===RETRY===\n\n")[-1]
            msgs = [{"role": "system", "content": _read(t["system"])},
                    {"role": "user", "content": user1},
                    {"role": "assistant", "content": first_answer},
                    {"role": "user", "content": gl_text}]
            t0 = time.time()
            m3 = _gen(msgs)
            parsed3 = parse_app_v2(m3, s["family"])
            rec = dict(r)
            rec.update({
                "trial_id": r["trial_id"] + "-gl",
                "run_tag": tag, "turn_structure": "1T-GL",
                "gl_parent_trial": r["trial_id"],
                "raw_output": m3, "parsed": parsed3, "format_retry_used": False,
                "seconds": round(time.time() - t0, 1),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            print(f"GL {r['trial_id']} -> {'OK' if parsed3 else 'FORMAT_FAIL'} ({rec['seconds']}s)")
    print("done:", tag)


print("app_runner_2t loaded (1T/逸脱#4). arms:", list(ARMS_2T.keys()), "scenarios:", list(APP_SCEN.keys()))
