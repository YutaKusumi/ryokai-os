# -*- coding: utf-8 -*-
"""追補D 本実施・ランタイム切断からの再開ブート（Colabで exec）。

登録された保護対象（scoring rubric・decision tree・arm system-prompt texts/SHAs・
generation hyperparameters・turn structure）はいずれも変更しない。本スクリプトは
run_1t()（boot_pilot.py/boot_main.py内で定義）と完全に同一のロジック（同一の
system+preamble+N2結合式・同一のtrial_id生成式・同一の記録スキーマ）を、
指定した開始インデックスから再開できる形にしただけの、純粋な運用上の再実行器
である。これは登録内容への変更ではなく、Colabランタイムの意図しない切断
（ネットワーク断・アイドルタイムアウト等）からの復旧のためのユーティリティ
であり、逸脱記録の対象ではない。

使い方（Colabセルでexec後）:
  out_main = "/content/results/trials-addd-main-Qwen3-30B-A3B-Instruct-2507.jsonl"
  out_gl   = "/content/results/trials-addd-gl-firstpass-Qwen3-30B-A3B-Instruct-2507.jsonl"
  run_1t_resume("GHnull", "N2", "trials-addd-main-Qwen3-30B-A3B-Instruct-2507", 11, 30, out_main)
  run_1t_resume("GS",     "N2", "trials-addd-main-Qwen3-30B-A3B-Instruct-2507", 0, 30, out_main)
  run_1t_resume("GL1",    "N2", "trials-addd-gl-firstpass-Qwen3-30B-A3B-Instruct-2507", 0, 30, out_gl)
"""
import os, sys, time, json, hashlib, urllib.request

os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
import subprocess
try:
    subprocess.run(["pip", "uninstall", "-y", "hf_xet"], capture_output=True, text=True, timeout=120)
    subprocess.run(["pip", "install", "-q", "hf_transfer"], capture_output=True, text=True, timeout=300)
    subprocess.run(["pip", "install", "-q", "-U", "bitsandbytes"], capture_output=True, text=True, timeout=300)
    subprocess.run(["pip", "install", "-q", "transformers>=4.51,<5"], capture_output=True, text=True, timeout=600)
except Exception as _e:
    print("download-backend setup note:", _e)
import bitsandbytes as _bnb
import transformers as _tf
print("bitsandbytes:", _bnb.__version__, "| transformers:", _tf.__version__)
assert _tf.__version__.startswith("4."), "transformers 5.x が残っている——セッション再起動が必要"

sys.path.insert(0, "/content/pipeline")

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


def _rd(p):
    return open(p, encoding="utf-8").read().replace("\r\n", "\n").strip()


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
    from huggingface_hub import snapshot_download
    import torch
    MODEL_ID, TEMPERATURE, TOP_P = "Qwen/Qwen3-30B-A3B-Instruct-2507", 0.7, 0.9
    for attempt in range(6):
        try:
            snapshot_download(MODEL_ID, max_workers=4)
            print("snapshot_download complete (attempt", attempt + 1, ")")
            break
        except Exception as e:
            print(f"snapshot_download retry {attempt + 1}/6 after error: {str(e)[:150]}")
            time.sleep(5)
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16,
                             bnb_4bit_quant_type="nf4")
    print("GPU:", torch.cuda.get_device_name(0), "| free/total GiB:",
          [round(x / 2**30, 1) for x in torch.cuda.mem_get_info(0)])
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, device_map="auto", quantization_config=bnb)
    model.eval()
    fp = model.get_memory_footprint() / 2**30
    print(f"model loaded: {MODEL_ID} | memory footprint {fp:.1f} GiB")
    assert fp < 30, f"4bit量子化が効いていない疑い（footprint {fp:.1f} GiB）——中止"


def _eos_ids():
    ids = [tok.eos_token_id]
    ie = tok.convert_tokens_to_ids("<|im_end|>")
    if isinstance(ie, int) and ie >= 0 and ie != tok.unk_token_id:
        ids.append(ie)
    return ids


def generate(msgs, max_new_tokens=4096):
    import torch
    enc = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt",
                                  return_dict=True).to(model.device)
    with torch.no_grad():
        out = model.generate(input_ids=enc["input_ids"], attention_mask=enc["attention_mask"],
                             max_new_tokens=max_new_tokens, do_sample=True,
                             temperature=TEMPERATURE, top_p=TOP_P, return_dict_in_generate=True,
                             eos_token_id=_eos_ids(), pad_token_id=tok.eos_token_id)
    return tok.decode(out.sequences[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)


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


def run_1t_resume(arm, qid, tag, start_i, end_i, out_path):
    """run_1t()と完全同一のロジック(単一userターン結合式・trial_id式・記録スキーマ)
    を、指定した[start_i, end_i)のインデックス範囲だけ実行する。既存の完了済み
    試行(0..start_i-1)は一切再実行しない。"""
    from app_parser_rev2 import parse_app_v2
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    s = SCEN[qid]
    u2 = s["text"] + INST[s["family"]]
    sysp, pre = ARMS[arm]
    sys_t, pre_t = _rd(sysp), _rd(pre)
    user_t = pre_t + "\n\n" + u2
    with open(out_path, "a", encoding="utf-8") as f:
        for i in range(start_i, end_i):
            t0 = time.time()
            msgs = [{"role": "system", "content": sys_t}, {"role": "user", "content": user_t}]
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
                   "turn_structure": "1T", "preamble_arm": arm,
                   "raw_output": raw, "parsed": p, "format_retry_used": retry,
                   "seconds": round(time.time() - t0, 1),
                   "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            tl = "OK" if p else "FAIL"
            if p and p.get("choice") == "refuse":
                tl = "REFUSE"
            print(f"{arm} #{i} {tl} | tot={rec['seconds']}s | choice={p.get('choice') if p else '-'}")
    print("done (resume):", arm, start_i, "->", end_i)


# ---- 準備（モデルロードまで。実施の再開呼び出しは別セルで行う） ----
sys.path.insert(0, "/content/pipeline")
fetch_and_verify()
build_gs()
_setup_scen()
load_model()
print("\nresume-boot ready. Drive mount + run_1t_resume(...) calls to follow in next cell.")
