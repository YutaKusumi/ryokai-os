# -*- coding: utf-8 -*-
"""追補W 実行器（単一ターン構造・逸脱#4系譜の継承）。

登録: addendum-W-design-draft7.md（SHA 7F2909C6…・2026-08-03 凍結・公開 6811461）。
実行ロジックは app_runner_adde.py と同一骨格（生成・リトライ・記録スキーマ・trial_id 式を
一字も変えない）。本ファイルが加える追補W固有の五点:

  1. 腕定義 ARMS_W（N / W / P・全腕 system=A2-on-full.md・前置き=Onull 共通）。
     腕差は【出力指示】のみ——N=json_instruction.nuclear（凍結済み・無変更）／
     W=armsW/instruction-W.md／P=armsW/instruction-P.md（build_arms_w.py が組成・
     草稿版SHAは下記・パイロット後の凍結追記で確定）
  2. finish_reason・生成トークン数の記録（系統外検分・重大1への実装）——
     トークン上限到達（finish_reason=="length"）は構文エラーと区別して truncated として
     別記録する。boot 側が generate_ex(msgs, max_new_tokens)->(text, finish_reason, n_tokens)
     を提供する場合にそれを使い、無ければ generate() にフォールバック（finish_reason=None）。
  3. 腕別 max_new_tokens（草稿値: N=1024 / W=6144 / P=6144——W6-1 の p95/p99 実測で
     凍結追記する。1.5×p99 以上を目安）
  4. W/P 専用パーサ parse_wp()——最後の ```json フェンス（無ければ末尾の平衡 {..}）を
     json.loads し、nuclear 5キーの部分集合を parsed に（主要エンドポイントの互換）、
     全体を parsed_w に格納。choice/escalation の値域検査つき。
  5. run_form_pilot()——G-W/P形式パイロット（W6-1 凍結）: W・P 各8試行・形式判定のみ。
     **choice の分布・破局率はパイロットでは印字も集計もしない**（データ非算入・
     pilot_stats() はトークン分布 p95/p99・切断率・parse率のみを報告する）。

/content に必要な凍結物:
  app-scenarios.json / arms/A2-on-full.md / armsE/preamble-Onull.md /
  armsW/instruction-W.md / armsW/instruction-P.md / app_parser_rev2.py（N腕用）

凍結SHA-256（LF正規化・実行前に verify_arms_w() で照合）:
  arms/A2-on-full.md         AAB363D85E103C13B72691749732BBE8882FCFCF4666CCAED79C1D46D27C0A4D
  armsE/preamble-Onull.md    2123B3CD8586E7DF8B9A0A983B1F93A3C4BE4F0A2F9B396ED216CBC60A0FD733
  armsW/instruction-W.md     679601C91D2F409A35392DFF2C6BEDD652B78A8F534B4E084C96E016FBA4642F（草稿版）
  armsW/instruction-P.md     A3EEC3C2522AF2979D59AF5A206504E196D638377F6D9CBE30B1ABF37E267089（草稿版）
  ※ instruction-{W,P} はパイロットの書式修正で更新されうる（凍結前に限る・W6-1）。
    更新時は本表と build_arms_w.py を同時に改め、差分を検分者・登録者に開示する。
"""
import json, time, hashlib, io, os, re

_APP = json.load(open("/content/app-scenarios.json", encoding="utf-8"))
APP_SCEN = {s["question_id"]: s for s in _APP["scenarios"]}
_INST = _APP["json_instruction"]

FROZEN_SHA = {
    "/content/arms/A2-on-full.md":
        "AAB363D85E103C13B72691749732BBE8882FCFCF4666CCAED79C1D46D27C0A4D",
    "/content/armsE/preamble-Onull.md":
        "2123B3CD8586E7DF8B9A0A983B1F93A3C4BE4F0A2F9B396ED216CBC60A0FD733",
    "/content/armsW/instruction-W.md":
        "679601C91D2F409A35392DFF2C6BEDD652B78A8F534B4E084C96E016FBA4642F",
    "/content/armsW/instruction-P.md":
        "A3EEC3C2522AF2979D59AF5A206504E196D638377F6D9CBE30B1ABF37E267089",
}

ARMS_W = {
    "N": {"system": "/content/arms/A2-on-full.md",
          "preamble": "/content/armsE/preamble-Onull.md",
          "instruction": None},                       # None = json_instruction.nuclear
    "W": {"system": "/content/arms/A2-on-full.md",
          "preamble": "/content/armsE/preamble-Onull.md",
          "instruction": "/content/armsW/instruction-W.md"},
    "P": {"system": "/content/arms/A2-on-full.md",
          "preamble": "/content/armsE/preamble-Onull.md",
          "instruction": "/content/armsW/instruction-P.md"},
}
INTERLEAVE = ["N", "W", "P"]      # draft7 W4 凍結: trial 通し番号 t の腕 = INTERLEAVE[t % 3]
N_MAIN = 50                        # 各腕 n（draft7 W4）
N_GATE = 30                        # G-N 基底（draft7 W6-2）
N_FORM_PILOT = 8                   # W6-1: 5〜10 の中央値
MAX_NEW = {"N": 1024, "W": 12288, "P": 12288}  # 凍結追記①で確定（2026-08-04・登録者承認）。
# 根拠: G-W/P形式パイロット実測（W/P各8・切断0・parse16/16）——
#   W: p50=3738 p99=3978 → 1.5×p99=5967 / P: p50=5434 p99=7649 → 1.5×p99=11473。
# P腕の 1.5×p99 が暫定値10240を超えたため 12288 へ。W/P同値維持は負荷整合（W4）のため。
# 詳細: addendum-W-freeze-appendix-1.md

_KEY5 = ["choice", "amount", "escalation", "report_to_operator", "reason_summary"]
_CHOICES = {"a", "b", "c", "d", "refuse"}


def verify_arms_w():
    bad = []
    for path, want in FROZEN_SHA.items():
        raw = open(path, "rb").read().replace(b"\r\n", b"\n")
        got = hashlib.sha256(raw).hexdigest().upper()
        ok = got == want
        print(f"  [{'OK' if ok else 'NG'}] {path.split('/')[-1]:24s} {got[:16]}...")
        if not ok:
            bad.append(path)
    if bad:
        raise RuntimeError(f"凍結SHA不一致: {bad} —— 実行を中止し取得をやり直すこと")
    print("verify_arms_w: 4/4 一致")


def _read(path):
    return io.open(path, encoding="utf-8").read().replace("\r\n", "\n").strip()


def _gen_ex(msgs, max_new_tokens):
    """boot が generate_ex を提供すれば (text, finish_reason, n_tokens)。
    無ければ generate() にフォールバック（finish_reason=None・n_tokens=None）。"""
    g_ex = globals().get("generate_ex")
    if g_ex is not None:
        return g_ex(msgs, max_new_tokens=max_new_tokens)
    try:
        return generate(msgs, max_new_tokens=max_new_tokens), None, None
    except TypeError:
        return generate(msgs), None, None


def _extract_json_block(raw):
    """最後の ```json フェンスを優先。無ければ末尾から平衡した {..} を走査。"""
    fences = re.findall(r"```json\s*(\{.*?\})\s*```", raw, re.S)
    if fences:
        return fences[-1]
    # 平衡スキャン（最後の '{' 群から）
    end = raw.rfind("}")
    while end != -1:
        depth = 0
        for start in range(end, -1, -1):
            if raw[start] == "}":
                depth += 1
            elif raw[start] == "{":
                depth -= 1
                if depth == 0:
                    return raw[start:end + 1]
        end = raw.rfind("}", 0, end)
    return None


def parse_wp(raw):
    """W/P 腕パーサ。返り値: (parsed5 or None, parsed_full or None)。
    parsed5 = nuclear 5キーの部分集合（主要エンドポイント互換）。値域検査:
    choice∈{a,b,c,d,refuse}・escalation∈0..4（refuse時 null 可）。それ以外は形式不能。"""
    blk = _extract_json_block(raw)
    if blk is None:
        return None, None
    try:
        obj = json.loads(blk)
    except Exception:
        return None, None
    if not isinstance(obj, dict):
        return None, None
    ch = obj.get("choice")
    if ch not in _CHOICES:
        return None, None
    esc = obj.get("escalation")
    if ch == "refuse":
        if esc is not None:
            return None, None
    else:
        if not (isinstance(esc, int) and 0 <= esc <= 4):
            return None, None
    parsed5 = {k: obj.get(k) for k in _KEY5}
    return parsed5, obj


def _one_trial(fout, texts, arm, qid, i, tag):
    """app_runner_adde._one_trial と同一の生成・記録骨格＋W固有フィールド。"""
    s = APP_SCEN[qid]
    inst = texts[arm]["instruction"] if texts[arm]["instruction"] is not None else _INST[s["family"]]
    user1 = texts[arm]["preamble"] + "\n\n" + s["text"] + inst
    t0 = time.time()
    msgs = [{"role": "system", "content": texts[arm]["system"]},
            {"role": "user", "content": user1}]
    raw, fr, ntok = _gen_ex(msgs, MAX_NEW[arm])
    if arm == "N":
        from app_parser_rev2 import parse_app_v2
        parsed = parse_app_v2(raw, s["family"])
        parsed_full = None
    else:
        parsed, parsed_full = parse_wp(raw)
    retry = False
    fr2 = ntok2 = None
    if parsed is None:
        raw2, fr2, ntok2 = _gen_ex(msgs, MAX_NEW[arm])
        if arm == "N":
            from app_parser_rev2 import parse_app_v2
            parsed = parse_app_v2(raw2, s["family"])
        else:
            parsed, parsed_full = parse_wp(raw2)
        retry = True
        raw = raw + "\n\n===RETRY===\n\n" + raw2
    rec = {
        "trial_id": hashlib.md5(f"{tag}{MODEL_ID}{arm}{qid}{i}".encode()).hexdigest()[:12],
        "run_tag": tag, "model": MODEL_ID, "quant": "4bit-nf4",
        "temperature": TEMPERATURE, "top_p": TOP_P,
        "arm": arm, "notice": "off",
        "question_id": qid, "family": s["family"], "trial_index": i,
        "turn_structure": "1T", "preamble_arm": "Onull",
        "raw_output": raw, "parsed": parsed, "parsed_w": parsed_full,
        "format_retry_used": retry,
        "max_new_tokens": MAX_NEW[arm],
        "finish_reason": fr, "gen_tokens": ntok,
        "finish_reason_retry": fr2, "gen_tokens_retry": ntok2,
        "truncated": (fr == "length") or (fr2 == "length"),
        "seconds": round(time.time() - t0, 1),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
    fout.flush()
    return rec


def _status_form_only(rec):
    """形式パイロット用の印字（choice を露出しない——W6-1: 破局率は見ない）。"""
    if rec["truncated"]:
        return "TRUNCATED"
    return "OK" if rec["parsed"] else "FORMAT_FAIL"


def _status_full(rec):
    tagline = "OK" if rec["parsed"] else "FORMAT_FAIL"
    if rec["parsed"] and rec["parsed"].get("choice") == "refuse":
        tagline = "REFUSE"
    if rec["truncated"]:
        tagline += "+TRUNC"
    return tagline


def _texts(arms):
    out = {}
    for a in arms:
        c = ARMS_W[a]
        out[a] = {"system": _read(c["system"]), "preamble": _read(c["preamble"]),
                  "instruction": _read(c["instruction"]) if c["instruction"] else None}
    return out


def _out(tag):
    return f"/content/results/trials-{tag}-{MODEL_ID.split('/')[-1]}.jsonl"


def run_form_pilot(tag="addw-form-pilot", n=N_FORM_PILOT):
    """G-W/P形式パイロット（W6-1 凍結）: W・P 各n試行・形式判定のみ・データ非算入。
    choice・破局率は印字も集計もしない。"""
    verify_arms_w()
    texts = _texts(["W", "P"])
    path = _out(tag)
    print("->", path)
    with open(path, "a", encoding="utf-8") as fout:
        for arm in ["W", "P"]:
            for i in range(n):
                rec = _one_trial(fout, texts, arm, "N2", i, tag)
                print(f"{arm} #{i} {_status_form_only(rec)} "
                      f"({rec['seconds']}s, tokens={rec['gen_tokens']}, fr={rec['finish_reason']})")
    print("\nform pilot done →", "pilot_stats(tag) でトークン分布・切断率・parse率のみを報告")


def pilot_stats(tag="addw-form-pilot"):
    """形式パイロットの統計（形式指標のみ・choice は集計しない・W6-1）。"""
    path = _out(tag)
    recs = [json.loads(l) for l in open(path, encoding="utf-8")]
    for arm in ["W", "P"]:
        rs = [r for r in recs if r["arm"] == arm]
        toks = sorted(r["gen_tokens"] for r in rs if r.get("gen_tokens") is not None)
        def pct(p):
            return toks[min(len(toks) - 1, int(len(toks) * p))] if toks else None
        n_ok = sum(1 for r in rs if r["parsed"])
        n_tr = sum(1 for r in rs if r["truncated"])
        n_rt = sum(1 for r in rs if r["format_retry_used"])
        print(f"{arm}: n={len(rs)} parse_ok={n_ok} truncated={n_tr} retry={n_rt} "
              f"tokens p50={pct(0.5)} p95={pct(0.95)} p99={pct(0.99)} max={toks[-1] if toks else None} "
              f"/ max_new={MAX_NEW[arm]}（余裕目安 1.5×p99={int(pct(0.99)*1.5) if toks else '?'}）")
    print("凍結追記の判定材料: max_new_tokens >= 1.5×p99 か・切断ゼロか・parse率")


def run_gate_n(tag="addw-gate-n"):
    """G-N 基底: N腕 30試行（判定は解析側で G-A/B/C/A' を機械適用）。"""
    verify_arms_w()
    texts = _texts(["N"])
    path = _out(tag)
    print("->", path)
    with open(path, "a", encoding="utf-8") as fout:
        for i in range(N_GATE):
            rec = _one_trial(fout, texts, "N", "N2", i, tag)
            print(f"N N2 #{i} {_status_full(rec)} ({rec['seconds']}s)")
    print("gate run done:", tag)


def _main_sequence():
    counters = {a: 0 for a in INTERLEAVE}
    seq = []
    for t in range(N_MAIN * 3):
        arm = INTERLEAVE[t % 3]
        seq.append((t, arm, counters[arm]))
        counters[arm] += 1
    return seq


def run_main(tag="addw-main"):
    """主要3腕150試行・腕交互配置（G-N 通過後にのみ実行）。"""
    verify_arms_w()
    texts = _texts(INTERLEAVE)
    path = _out(tag)
    print("->", path)
    with open(path, "a", encoding="utf-8") as fout:
        for t, arm, i in _main_sequence():
            rec = _one_trial(fout, texts, arm, "N2", i, tag)
            print(f"[t={t:3d}] {arm} N2 #{i} {_status_full(rec)} ({rec['seconds']}s)")
    print("main run done:", tag)


def run_main_resume(tag="addw-main"):
    """切断からの再開（追補D/E 実績方式・trial_id 照合）。"""
    verify_arms_w()
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
            rec = _one_trial(fout, texts, arm, "N2", i, tag)
            print(f"[t={t:3d}] {arm} N2 #{i} {_status_full(rec)} ({rec['seconds']}s)")
    print("resume done:", tag)


print("app_runner_w loaded. arms:", list(ARMS_W.keys()),
      f"| form-pilot: W/P x{N_FORM_PILOT} | gate: N {N_GATE} | main: {N_MAIN}x3 interleaved",
      f"| max_new={MAX_NEW}")
