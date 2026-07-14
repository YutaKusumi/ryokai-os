# -*- coding: utf-8 -*-
# 追補D Part B 着地パイロット・自己完結ブート（Colabで exec）。
# CELL1(pip)実行後に files.upload() でアップロード → exec(open("boot_pilot.py").read())
# 凍結物はGitHub rawから取得しLF-SHA照合。runnerは本スクリプト内に定義。
import os
# HFのXet経路が停滞/401する問題への対処: フラグ無効化＋hf_xetを物理的に除去して
# 従来CDN経路を強制（トークンありなら認証で高速・停滞なし）。要セッション再起動。
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
import subprocess
try:
    subprocess.run(["pip", "uninstall", "-y", "hf_xet"], capture_output=True, text=True, timeout=120)
except Exception as _e:
    print("hf_xet uninstall skipped:", _e)
import hashlib, urllib.request, json, time, sys

RAW = "https://raw.githubusercontent.com/YutaKusumi/ryokai-os/main/verification/"
FILES = {
    "app-scenarios.json":           "7AD7E49459D5C40203DF04F6819575796AD3E880BCB5A12801635BF304E4DDC1",
    "pipeline/app_parser_rev2.py":  None,
    "arms/A5-prime-secular-3.1.md": "0909DB7F90F8B49FD557AEF8727450799E845DE8F6E31E1579E78A2CEB9F4BC8",
    "arms/A2-on-full.md":           "AAB363D85E103C13B72691749732BBE8882FCFCF4666CCAED79C1D46D27C0A4D",
    "armsD/preamble-neutral.md":    "45372D08DD75CD2C95855495E29B8264B636D882E61A1DA40872756EA341E16C",
    "armsD/preamble-GH.md":         "5CEE23D946B3DF524B575CCD7E7EDCC5F4299A5663EC229A7D55151EB4744FDC",
    "armsD/preamble-GHnull.md":     "834F9B4EA520EF37DBC890549E430BDF2186182F5F8F4A9100F5DE2A00F72671",
    "armsD/GS-gate.md":             "923DA1EF16E6FA39E024797A01888F04AC59190C644192A1F7D1B316DFF18E53",
    "armsD/GL-followup.md":         "ADC5B8F2B73D0D7B43E6DA0E3B806741C161E161861B60523EE83182B14AB9A9",
}


def lf_sha(p):
    d = open(p, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    return hashlib.sha256(d.encode("utf-8")).hexdigest().upper()


def fetch_and_verify():
    for d in ["armsD", "arms", "pipeline"]:
        os.makedirs("/content/" + d, exist_ok=True)
    allok = True
    for rel, want in FILES.items():
        dst = "/content/" + rel
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        urllib.request.urlretrieve(RAW + rel, dst)
        got = lf_sha(dst)
        ok = (want is None) or (got == want)
        allok = allok and ok
        print(("OK   " if ok else "BAD  ") + rel + ("" if want else "  (no-check)"))
    assert allok, "frozen SHA mismatch - abort"
    print("all frozen SHAs verified.\n")


def build_gs():
    def rd(p):
        return open(p, encoding="utf-8").read().replace("\r\n", "\n").rstrip("\n")
    gs = rd("/content/arms/A5-prime-secular-3.1.md") + "\n\n" + rd("/content/armsD/GS-gate.md") + "\n"
    open("/content/armsD/A5-prime-GS-gate.md", "w", encoding="utf-8", newline="\n").write(gs)
    want = "7915A57EA7E4F397C0EDC61C5AC8E5E57B4AEBB0EE72CCD9A80FEB6E434867BE"
    got = lf_sha("/content/armsD/A5-prime-GS-gate.md")
    print("GS arm build:", "OK" if got == want else "MISMATCH", "(", len(gs), "chars )")
    assert got == want, "GS build SHA mismatch"


def load_model():
    global tok, model, MODEL_ID, TEMPERATURE, TOP_P
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    import torch
    MODEL_ID, TEMPERATURE, TOP_P = "Qwen/Qwen3-30B-A3B-Instruct-2507", 0.7, 0.9
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, quantization_config=bnb, device_map="auto")
    model.eval()
    print("model loaded:", MODEL_ID)


def generate(msgs, max_new_tokens=4096):
    import torch
    inputs = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(inputs, max_new_tokens=max_new_tokens, do_sample=True,
                             temperature=TEMPERATURE, top_p=TOP_P, return_dict_in_generate=True,
                             pad_token_id=tok.eos_token_id)
    return tok.decode(out.sequences[0][inputs.shape[1]:], skip_special_tokens=True)


def _rd(p):
    return open(p, encoding="utf-8").read().replace("\r\n", "\n").strip()


# 腕定義（凍結: armsD/README.md）
ARMS = {
    "A5p2T":  ("/content/arms/A5-prime-secular-3.1.md", "/content/armsD/preamble-neutral.md"),
    "GH":     ("/content/arms/A5-prime-secular-3.1.md", "/content/armsD/preamble-GH.md"),
    "GHnull": ("/content/arms/A5-prime-secular-3.1.md", "/content/armsD/preamble-GHnull.md"),
    "GS":     ("/content/armsD/A5-prime-GS-gate.md",    "/content/armsD/preamble-neutral.md"),
    "GL1":    ("/content/arms/A2-on-full.md",           "/content/armsD/preamble-neutral.md"),
}


def _setup_scen():
    global SCEN, INST
    _APP = json.load(open("/content/app-scenarios.json", encoding="utf-8"))
    SCEN = {s["question_id"]: s for s in _APP["scenarios"]}
    INST = _APP["json_instruction"]


def tokenizer_report():
    n2 = SCEN["N2"]
    for a, (sysp, pre) in ARMS.items():
        msgs = [{"role": "system", "content": _rd(sysp)}, {"role": "user", "content": _rd(pre)}]
        ntok = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").shape[1]
        print(f"{a:7s} system+preamble tokens: {ntok}")


def run_2t(arms, n_trials, tag, qid="N2", model1_max=512):
    from app_parser_rev2 import parse_app_v2
    out = f"/content/results/{tag}.jsonl"
    os.makedirs("/content/results", exist_ok=True)
    s = SCEN[qid]
    u2 = s["text"] + INST[s["family"]]
    with open(out, "a", encoding="utf-8") as f:
        for arm in arms:
            sysp, pre = ARMS[arm]
            sys_t, pre_t = _rd(sysp), _rd(pre)
            for i in range(n_trials):
                t0 = time.time()
                base = [{"role": "system", "content": sys_t}, {"role": "user", "content": pre_t}]
                m1 = generate(base, model1_max)
                t1 = time.time()
                msgs = base + [{"role": "assistant", "content": m1}, {"role": "user", "content": u2}]
                raw = generate(msgs)
                p = parse_app_v2(raw, s["family"])
                retry = False
                if p is None:
                    raw2 = generate(msgs)
                    p = parse_app_v2(raw2, s["family"])
                    retry = True
                    raw = raw + "\n\n===RETRY===\n\n" + raw2
                rec = {"trial_id": hashlib.md5(f"{tag}{arm}{qid}{i}".encode()).hexdigest()[:12],
                       "run_tag": tag, "model": MODEL_ID, "quant": "4bit-nf4",
                       "temperature": TEMPERATURE, "top_p": TOP_P, "arm": arm, "notice": "off",
                       "question_id": qid, "family": s["family"], "trial_index": i,
                       "turn_structure": "2T", "preamble_arm": arm, "model1_output": m1,
                       "model1_len": len(m1), "model1_seconds": round(t1 - t0, 1),
                       "raw_output": raw, "parsed": p, "format_retry_used": retry,
                       "seconds": round(time.time() - t0, 1),
                       "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                tl = "OK" if p else "FAIL"
                if p and p.get("choice") == "refuse":
                    tl = "REFUSE"
                print(f"{arm} #{i} {tl} | m1_len={len(m1)} m1={rec['model1_seconds']}s tot={rec['seconds']}s | choice={p.get('choice') if p else '-'}")
    print("done:", out)


def pilot_verdict():
    recs = [json.loads(l) for l in open("/content/results/pilot-partB.jsonl", encoding="utf-8")]
    n = len(recs)
    okj = sum(1 for r in recs if r["parsed"])
    rty = sum(1 for r in recs if r["format_retry_used"])
    m1max = max(r["model1_len"] for r in recs)
    print("\n" + "=" * 50)
    print(f"パイロット判定: 総試行 {n} | JSON着地 {okj}/{n} | retry {rty} | Model1最大長 {m1max}字")
    print("Model1サンプル:", recs[0]["model1_output"][:100].replace("\n", " "))
    passed = (okj == n) and (m1max < 2000)
    print("合否:", "PASS -> boot_main.py を exec して本実施へ" if passed else "HOLD -> コーディネータへ連絡")
    print("=" * 50)
    sys.path.insert(0, "/content/pipeline")
    return passed


# ---- 実行 ----
sys.path.insert(0, "/content/pipeline")
fetch_and_verify()
build_gs()
_setup_scen()
load_model()
print("\n-- tokenizer実測 --")
tokenizer_report()
print("\n-- 2Tパイロット（4腕×2＋GL1×2＝10）--")
run_2t(["A5p2T", "GH", "GHnull", "GS"], 2, "pilot-partB")
run_2t(["GL1"], 2, "pilot-partB")
pilot_verdict()
