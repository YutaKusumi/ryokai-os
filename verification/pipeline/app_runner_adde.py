# -*- coding: utf-8 -*-
"""追補E 実行器（単一ターン構造・逸脱#4 継承）。

登録: preregistration-addendum-E-FROZEN.md（SHA 4C182C1A…2814F7・2026-07-28）。
実行ロジックは app_runner_2t.py の run_app_1t() と同一（生成・リトライ・記録
スキーマを一字も変えない）。本ファイルが加えるのは追補E固有の三点のみ:

  1. 腕定義 ARMS_E（EB / Lneg / Onull / O・全腕 system=A2-on-full.md）
  2. 実行順序（E2-1 凍結）:
     - run_gate():  EB 30試行を先に単独で走らせる（ゲート・G4 は解析側で判定）
     - run_main(): 主要3腕150試行を【腕交互配置】で生成——グローバル通し番号 t の
       腕は INTERLEAVE[t % 3]（Lneg→Onull→O の循環・E2-1(2)）。腕ブロック順の
       ドリフトを確証族から遮断する。
     - run_pilot(): 四腕 各3試行（E8 着地パイロット・速度確認）
  3. 再開 run_main_resume(): trial_id 式は run_app_1t と同一（tag+MODEL+arm+qid+腕内index）
     ゆえ、既存 jsonl の trial_id を読んでスキップするだけで無重複・無欠落再開できる
     （追補D resume_after_disconnect.py の実績方式）。

/content に必要な凍結物:
  app-scenarios.json / app_parser_rev2.py / arms/A2-on-full.md /
  armsD/preamble-neutral.md / armsE/{preamble-Lneg,preamble-Onull,preamble-O}.md

凍結SHA-256（LF正規化・取得後に verify_arms_e() で照合すること）:
  照合は【LF正規化後】のバイト列で行う（boot_pilot.py の実績方式）。GitHub は
  A2-on-full.md を LF で格納しており（実測 2026-07-29）、FROZEN E1-5 の値
  9DE7B788… はローカル CRLF 版の生バイト SHA である——内容は改行のみの差で同一。
  生成時は _read() が改行を正規化するため、どちらの版でも投入内容は同一になる。
  arms/A2-on-full.md        LF: AAB363D85E103C13B72691749732BBE8882FCFCF4666CCAED79C1D46D27C0A4D
                            （= FROZEN E1-5 の 9DE7B788…〔CRLF生バイト〕と同一内容）
  armsD/preamble-neutral.md 45372D08DD75CD2C95855495E29B8264B636D882E61A1DA40872756EA341E16C
  armsE/preamble-Lneg.md    A16E20E4827D9C8673A60C35354A6BE01D3A00521018314787D9CCEED0F88957
  armsE/preamble-Onull.md   2123B3CD8586E7DF8B9A0A983B1F93A3C4BE4F0A2F9B396ED216CBC60A0FD733
  armsE/preamble-O.md       F3EE60C33F825575CE4D9D3AFB7409FD5BAA130A3C51C2B7130665C16FDEAE12
"""
import json, time, hashlib, io, os
from app_parser_rev2 import parse_app_v2

_APP = json.load(open("/content/app-scenarios.json", encoding="utf-8"))
APP_SCEN = {s["question_id"]: s for s in _APP["scenarios"]}
_INST = _APP["json_instruction"]

FROZEN_SHA = {   # LF正規化SHA（ヘッダ注記参照）
    "/content/arms/A2-on-full.md":
        "AAB363D85E103C13B72691749732BBE8882FCFCF4666CCAED79C1D46D27C0A4D",
    "/content/armsD/preamble-neutral.md":
        "45372D08DD75CD2C95855495E29B8264B636D882E61A1DA40872756EA341E16C",
    "/content/armsE/preamble-Lneg.md":
        "A16E20E4827D9C8673A60C35354A6BE01D3A00521018314787D9CCEED0F88957",
    "/content/armsE/preamble-Onull.md":
        "2123B3CD8586E7DF8B9A0A983B1F93A3C4BE4F0A2F9B396ED216CBC60A0FD733",
    "/content/armsE/preamble-O.md":
        "F3EE60C33F825575CE4D9D3AFB7409FD5BAA130A3C51C2B7130665C16FDEAE12",
}

ARMS_E = {
    "EB":    {"system": "/content/arms/A2-on-full.md",
              "preamble": "/content/armsD/preamble-neutral.md"},
    "Lneg":  {"system": "/content/arms/A2-on-full.md",
              "preamble": "/content/armsE/preamble-Lneg.md"},
    "Onull": {"system": "/content/arms/A2-on-full.md",
              "preamble": "/content/armsE/preamble-Onull.md"},
    "O":     {"system": "/content/arms/A2-on-full.md",
              "preamble": "/content/armsE/preamble-O.md"},
}
INTERLEAVE = ["Lneg", "Onull", "O"]        # E2-1(2) 凍結: trial 通し番号 t の腕 = INTERLEAVE[t % 3]
N_MAIN = 50                                 # 主要3腕の各 n（FROZEN E1-2）
N_EB = 30


def verify_arms_e():
    """取得済み凍結物の SHA-256 を凍結値と全点照合する（不一致なら例外）。"""
    bad = []
    for path, want in FROZEN_SHA.items():
        # LF 正規化後のバイト列で照合（boot_pilot.py の実績方式・CRLF/LF差を吸収）
        raw = open(path, "rb").read().replace(b"\r\n", b"\n")
        got = hashlib.sha256(raw).hexdigest().upper()
        ok = got == want
        print(f"  [{'OK' if ok else 'NG'}] {path.split('/')[-1]:26s} {got[:16]}...")
        if not ok:
            bad.append(path)
    if bad:
        raise RuntimeError(f"凍結SHA不一致: {bad} —— 実行を中止し取得をやり直すこと")
    print("verify_arms_e: 5/5 一致")


def _read(path):
    return io.open(path, encoding="utf-8").read().replace("\r\n", "\n").strip()


def _gen(msgs, max_new_tokens=None):
    try:
        if max_new_tokens is not None:
            return generate(msgs, max_new_tokens=max_new_tokens)
        return generate(msgs)
    except TypeError:
        return generate(msgs)


def _one_trial(fout, texts, arm, qid, i, tag):
    """run_app_1t() の内側ループと同一の生成・記録（trial_id 式も同一）。"""
    s = APP_SCEN[qid]
    user1 = texts[arm]["preamble"] + "\n\n" + s["text"] + _INST[s["family"]]
    t0 = time.time()
    msgs = [{"role": "system", "content": texts[arm]["system"]},
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
    print(f"{arm} {qid} #{i} {tagline} ({rec['seconds']}s)")
    return rec


def _texts(arms):
    return {a: {"system": _read(c["system"]), "preamble": _read(c["preamble"])}
            for a, c in ARMS_E.items() if a in arms}


def _out(tag):
    return f"/content/results/trials-{tag}-{MODEL_ID.split('/')[-1]}.jsonl"


def run_pilot(tag="adde-pilot"):
    """E8 着地パイロット: 四腕 各3試行（12試行）。速度・JSON着地・暴走の確認。"""
    verify_arms_e()
    texts = _texts(["EB", "Lneg", "Onull", "O"])
    path = _out(tag)
    print("->", path)
    secs = []
    with open(path, "a", encoding="utf-8") as fout:
        for arm in ["EB", "Lneg", "Onull", "O"]:
            for i in range(3):
                rec = _one_trial(fout, texts, arm, "N2", i, tag)
                secs.append(rec["seconds"])
    med = sorted(secs)[len(secs) // 2]
    est180 = med * 180 / 3600
    print(f"\npilot done. 中央値 {med:.0f}秒/試行 -> 180試行の見積もり {est180:.1f}時間")
    print("判定: (a)JSON着地12/12か (b)ループなしか (c)速度（129秒級=速い/647秒級=遅い→resume運用）")


def run_gate(tag="adde-gate"):
    """E2-1(1): 基線 EB 30試行を単独で先に走らせる。分岐判定は analyze_adde.py で。"""
    verify_arms_e()
    texts = _texts(["EB"])
    path = _out(tag)
    print("->", path)
    with open(path, "a", encoding="utf-8") as fout:
        for i in range(N_EB):
            _one_trial(fout, texts, "EB", "N2", i, tag)
    print("gate run done:", tag, "→ ローカルで analyze_adde.py gate を適用し分岐を確定すること")


def run_gate_g4(tag="adde-gate-g4"):
    """G4 発火時のみ: 基線をもう30試行（別タグ・合算判定は解析側）。"""
    verify_arms_e()
    texts = _texts(["EB"])
    path = _out(tag)
    print("->", path)
    with open(path, "a", encoding="utf-8") as fout:
        for i in range(N_EB):
            _one_trial(fout, texts, "EB", "N2", i, tag)
    print("G4 re-acquisition done:", tag)


def _main_sequence():
    """主要3腕150試行の凍結順序: (global_t, arm, per-arm index)。"""
    counters = {a: 0 for a in INTERLEAVE}
    seq = []
    for t in range(N_MAIN * 3):
        arm = INTERLEAVE[t % 3]
        seq.append((t, arm, counters[arm]))
        counters[arm] += 1
    return seq


def run_main(tag="adde-main"):
    """E2-1(2): 主要3腕150試行・腕交互配置（分岐A確定後にのみ実行すること）。"""
    verify_arms_e()
    texts = _texts(INTERLEAVE)
    path = _out(tag)
    print("->", path)
    with open(path, "a", encoding="utf-8") as fout:
        for t, arm, i in _main_sequence():
            print(f"[t={t:3d}]", end=" ")
            _one_trial(fout, texts, arm, "N2", i, tag)
    print("main run done:", tag)


def run_main_resume(tag="adde-main"):
    """切断からの再開: 既存 jsonl の trial_id を読み、未生成の試行のみ凍結順序で続行。"""
    verify_arms_e()
    path = _out(tag)
    done = set()
    if os.path.exists(path):
        for l in open(path, encoding="utf-8"):
            done.add(json.loads(l)["trial_id"])
    print(f"resume: {len(done)} trials already present")
    texts = _texts(INTERLEAVE)
    with open(path, "a", encoding="utf-8") as fout:
        for t, arm, i in _main_sequence():
            tid = hashlib.md5(f"{tag}{MODEL_ID}{arm}N2{i}".encode()).hexdigest()[:12]
            if tid in done:
                continue
            print(f"[t={t:3d}]", end=" ")
            _one_trial(fout, texts, arm, "N2", i, tag)
    print("resume done:", tag)


print("app_runner_adde loaded. arms:", list(ARMS_E.keys()),
      f"| main: {N_MAIN}x3 interleaved | gate: EB {N_EB}")
