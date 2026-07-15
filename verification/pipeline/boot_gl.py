# -*- coding: utf-8 -*-
"""追補D GL差し戻しフェーズ・自己完結ブート（Colabで exec）。

登録: preregistration-addendum-D-FROZEN.md D4（探索2・GL事後差し戻し）。
乖離採点（盲検二採点者＋登録者裁定・adjudication-record-addd.md）で「乖離事象」と
確定した GL1 の14試行にのみ、run_gl_continuation()（app_runner_2t.py・凍結SHA
078C5F16…）で Human3(GL-followup) → Model3 を生成する。

登録手順書の明記に従い、本実施前に必ず gl_smoke()（2試行・データ非算入）で
「真の応答→差し戻し→再応答」構造の着地（ループ非再発・妥当な長さ）を確認する。

使い方（Colabセル・この順で）:
  1) このファイルを exec → 凍結物取得/SHA照合 → モデルロード
  2) 登録者が Drive をマウント（from google.colab import drive; drive.mount(...)）
  3) setup_results_symlink()
  4) gl_smoke()   # 2試行・tag=addd-gl-smoke（探索データに算入しない）
  5) 着地確認後: gl_full()   # 14試行・tag=addd-gl
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
    "pipeline/app_runner_2t.py":    "078C5F16A7B021574D6638E3BE70A8D0188893E56D56C39BDAB9EBADBEE33782",
    "arms/A5-prime-secular-3.1.md": "0909DB7F90F8B49FD557AEF8727450799E845DE8F6E31E1579E78A2CEB9F4BC8",
    "arms/A2-on-full.md":           "AAB363D85E103C13B72691749732BBE8882FCFCF4666CCAED79C1D46D27C0A4D",
    "armsD/preamble-neutral.md":    "45372D08DD75CD2C95855495E29B8264B636D882E61A1DA40872756EA341E16C",
    "armsD/preamble-GH.md":         "5CEE23D946B3DF524B575CCD7E7EDCC5F4299A5663EC229A7D55151EB4744FDC",
    "armsD/preamble-GHnull.md":     "834F9B4EA520EF37DBC890549E430BDF2186182F5F8F4A9100F5DE2A00F72671",
    "armsD/GS-gate.md":             "923DA1EF16E6FA39E024797A01888F04AC59190C644192A1F7D1B316DFF18E53",
    "armsD/GL-followup.md":         "ADC5B8F2B73D0D7B43E6DA0E3B806741C161E161861B60523EE83182B14AB9A9",
}

# 乖離採点＋登録者裁定で確定したGL1の乖離事象（adjudication-record-addd.md・14件）
GAP_IDS = [
    "109738b47197", "e058a5bef26d", "9765b4ddeb1b", "e1f57dca9551",
    "9a73641c427c", "35d401a35a8e", "cfadd3e14bdb", "befb82b36a9e",
    "b24a1feb8aa1", "8c42e8442bdd", "1167083a143e", "04909d9c2173",
    "94860567e8a8", "8578071d9847",
]
FIRSTPASS = "/content/results/trials-addd-gl-firstpass-Qwen3-30B-A3B-Instruct-2507.jsonl"
FIRSTPASS_SHA = "6979FEDF25D55CD65F0A9DB44A64C135CE198C71FD75051D754694118121391E"


def lf_sha(p):
    d = open(p, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    return hashlib.sha256(d.encode("utf-8")).hexdigest().upper()


def raw_sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()


def fetch_and_verify():
    for d in ["armsD", "arms", "pipeline"]:
        os.makedirs("/content/" + d, exist_ok=True)
    allok = True
    for rel, want in FILES.items():
        dst = "/content/" + rel
        os.makedirs(os.path.dirname(dst) or "/content", exist_ok=True)
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


def setup_results_symlink():
    """Driveマウント後に呼ぶ。/content/results → Drive の逐次永続化。"""
    import shutil
    DEST = "/content/drive/MyDrive/ryokai-addd-results"
    os.makedirs(DEST, exist_ok=True)
    if os.path.exists("/content/results") and not os.path.islink("/content/results"):
        for f in os.listdir("/content/results"):
            shutil.copy("/content/results/" + f, DEST)
        shutil.rmtree("/content/results")
    if not os.path.islink("/content/results"):
        os.symlink(DEST, "/content/results")
    print("results ->", os.path.realpath("/content/results"))
    got = raw_sha(FIRSTPASS)
    print("firstpass SHA:", "OK" if got == FIRSTPASS_SHA else "MISMATCH", got[:16], "...")
    assert got == FIRSTPASS_SHA, "第一パスのデータSHAが凍結値と不一致——中止"


def gl_smoke():
    """スモーク2試行（登録手順書の必須事前確認・探索データに算入しない）。"""
    run_gl_continuation(FIRSTPASS, GAP_IDS[:2], "addd-gl-smoke")
    print("\nsmoke done — 出力の長さ・ループ非再発・parse状況を確認してから gl_full() へ。")


def gl_full():
    """本差し戻し・14試行（tag=addd-gl）。"""
    run_gl_continuation(FIRSTPASS, GAP_IDS, "addd-gl")


# ---- 準備（モデルロードまで自動・差し戻しは手動セルで） ----
fetch_and_verify()
build_gs()
load_model()
exec(open("/content/pipeline/app_runner_2t.py", encoding="utf-8").read())
print("\nGL-boot ready. 次: 登録者がDriveマウント → setup_results_symlink() → gl_smoke() → gl_full()")
