# -*- coding: utf-8 -*-
"""
run_temp0_control.py — 温度0対照（登録: preregistration-temp0-control.md・2026-08-08 凍結）。

追補W の runner と同一の骨格・同一のプロンプト構成（N腕）を用い、生成の設定だけを二腕に分ける:
  T0  : do_sample=False（真の貪欲法）
  T07 : do_sample=True, temperature=0.7, top_p=0.9（追補Wの凍結値）
交互配置で T0 20試行・T07 20試行＝計40。入力は40回すべて完全に同一である。

同一性の判定は**一階目の生成のみ**で行う（リトライ連結は同一性測定を汚すため）——
記録には一階目を raw_first として別フィールドに保存する。

/content に必要な凍結物（追補W と同一・SHA照合つき）:
  app-scenarios.json / arms/A2-on-full.md / armsE/preamble-Onull.md / app_parser_rev2.py
"""
import json, time, hashlib, io, os

_APP = json.load(open("/content/app-scenarios.json", encoding="utf-8"))
APP_SCEN = {s["question_id"]: s for s in _APP["scenarios"]}
_INST = _APP["json_instruction"]

FROZEN_SHA = {
    "/content/arms/A2-on-full.md":
        "AAB363D85E103C13B72691749732BBE8882FCFCF4666CCAED79C1D46D27C0A4D",
    "/content/armsE/preamble-Onull.md":
        "2123B3CD8586E7DF8B9A0A983B1F93A3C4BE4F0A2F9B396ED216CBC60A0FD733",
}
QID = "N2"
MAX_NEW = 4096                      # N腕の凍結値
N_PER_ARM = 20
ARM_ORDER = ["T0", "T07"]           # 交互配置


def _lf_sha(p):
    return hashlib.sha256(open(p, "rb").read().replace(b"\r\n", b"\n")).hexdigest().upper()


def verify_arms():
    ok = 0
    for p, want in FROZEN_SHA.items():
        got = _lf_sha(p)
        print(f'  [{"OK" if got == want else "NG"}] {os.path.basename(p):24} {got[:16]}…')
        ok += (got == want)
    print(f"verify_arms: {ok}/{len(FROZEN_SHA)} 一致")
    if ok != len(FROZEN_SHA):
        raise RuntimeError("凍結SHA不一致——実行を中止する")


def _boot():
    """boot_addw が持つ tok / model / _eos_ids を解決する。
    boot は builtins へ generate 等しか公開しないため、名前空間を明示的に探す
    （exec で __main__ に入る場合・module として import される場合の両方に対応）。"""
    import sys
    for name in ("__main__", "boot_addw"):
        m = sys.modules.get(name)
        if m is not None and hasattr(m, "model") and hasattr(m, "tok"):
            return m
    for m in list(sys.modules.values()):
        if m is not None and hasattr(m, "model") and hasattr(m, "tok") and hasattr(m, "_eos_ids"):
            return m
    raise RuntimeError("tok/model が見つからない——boot_addw を先に実行してください")


def _gen(msgs, greedy):
    """生成。greedy=True なら do_sample=False（真の貪欲法）。返り値 (text, finish, n_new)。"""
    import torch
    B = _boot()
    tok, model, _eos_ids = B.tok, B.model, B._eos_ids
    enc = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt",
                                 return_dict=True).to(model.device)
    kw = dict(input_ids=enc["input_ids"], attention_mask=enc["attention_mask"],
              max_new_tokens=MAX_NEW, return_dict_in_generate=True,
              eos_token_id=_eos_ids(), pad_token_id=tok.eos_token_id)
    if greedy:
        kw.update(do_sample=False)                                   # 温度・top_p は渡さない
    else:
        kw.update(do_sample=True, temperature=0.7, top_p=0.9)        # 追補Wの凍結値
    with torch.no_grad():
        out = model.generate(**kw)
    n_in = enc["input_ids"].shape[1]
    seq = out.sequences[0]
    n_new = seq.shape[0] - n_in
    return tok.decode(seq[n_in:], skip_special_tokens=True), \
        ("length" if n_new >= MAX_NEW else "stop"), int(n_new)


def run_temp0_control(tag="temp0ctl", out_dir="/content/results"):
    from app_parser_rev2 import parse_app_v2
    verify_arms()
    sysmsg = io.open("/content/arms/A2-on-full.md", encoding="utf-8").read()
    pre = io.open("/content/armsE/preamble-Onull.md", encoding="utf-8").read()
    s = APP_SCEN[QID]
    user1 = pre + "\n\n" + s["text"] + _INST[s["family"]]
    msgs = [{"role": "system", "content": sysmsg}, {"role": "user", "content": user1}]
    # 入力の同一性を機械で担保（40回とも同一であることの証示）——msgs 全体の正規化JSONを指紋にする
    prompt_sha = hashlib.sha256(
        json.dumps(msgs, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest().upper()
    print(f"prompt SHA: {prompt_sha[:24]}…（全40試行で同一）")

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"trials-{tag}-Qwen3-30B-A3B-Instruct-2507.jsonl")
    done = set()
    if os.path.exists(path):
        for l in io.open(path, encoding="utf-8"):
            if l.strip():
                done.add(json.loads(l)["trial_id"])
        print(f"resume: {len(done)} trials already present")

    with io.open(path, "a", encoding="utf-8", newline="\n") as fout:
        t = 0
        for i in range(N_PER_ARM):
            for arm in ARM_ORDER:
                tid = hashlib.md5(f"{tag}{arm}{QID}{i}".encode()).hexdigest()[:12]
                if tid in done:
                    t += 1
                    continue
                t0 = time.time()
                raw1, fr1, nt1 = _gen(msgs, greedy=(arm == "T0"))
                parsed = parse_app_v2(raw1, s["family"])
                retry = False
                raw2 = fr2 = nt2 = None
                if parsed is None:
                    raw2, fr2, nt2 = _gen(msgs, greedy=(arm == "T0"))
                    parsed = parse_app_v2(raw2, s["family"])
                    retry = True
                rec = {
                    "trial_id": tid, "run_tag": tag,
                    "model": "Qwen/Qwen3-30B-A3B-Instruct-2507", "quant": "4bit-nf4",
                    "arm": arm,
                    "sampling": "greedy" if arm == "T0" else "t0.7-p0.9",
                    "temperature": (None if arm == "T0" else 0.7),
                    "top_p": (None if arm == "T0" else 0.9),
                    "question_id": QID, "family": s["family"], "trial_index": i,
                    "turn_structure": "1T", "preamble_arm": "Onull",
                    "prompt_sha": prompt_sha,
                    "raw_first": raw1,                 # ★同一性の判定はこの一階目のみで行う
                    "raw_output": raw1 if not retry else (raw1 + "\n\n===RETRY===\n\n" + raw2),
                    "parsed": parsed, "format_retry_used": retry,
                    "max_new_tokens": MAX_NEW,
                    "finish_reason": fr1, "gen_tokens": nt1,
                    "finish_reason_retry": fr2, "gen_tokens_retry": nt2,
                    "truncated": (fr1 == "length") or (fr2 == "length"),
                    "seconds": round(time.time() - t0, 1),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                }
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fout.flush()
                ch = (parsed or {}).get("choice")
                print(f"  [t={t}] {arm:3} #{i:02} {'OK' if parsed else 'FAIL'} "
                      f"choice={ch} {fr1} {nt1}tok ({rec['seconds']}s)")
                t += 1
    print(f"done: {tag} → {path}")
    return path
