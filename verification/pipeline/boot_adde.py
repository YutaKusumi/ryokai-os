# -*- coding: utf-8 -*-
# 追補E 自己完結ブート（Colabで exec）。boot_pilot.py（追補D・実績済み）の環境設定を継承。
#
# 手順（feedback_colab-browser-ops の定石: 直打ちせず GitHub 公開→短い fetch+exec）:
#   CELL1: 本ファイルを取得して実行
#     import urllib.request
#     urllib.request.urlretrieve("https://raw.githubusercontent.com/YutaKusumi/ryokai-os/"
#                                "<COMMIT>/verification/pipeline/boot_adde.py", "boot_adde.py")
#     exec(open("boot_adde.py").read())
#   （transformers のピン留めで一度セッション再起動が要る場合は、再起動後にもう一度 exec）
#   CELL2: run_pilot()                       # 四腕各3試行・速度確認（E8）
#   CELL3: mount_drive() ; run_gate()        # 基線30試行（逐次 Drive 永続化）
#   （ローカルで analyze_adde.py gate → 分岐確定 → 登録者確認）
#   CELL4: run_main()                        # 分岐A確定後のみ・150試行（腕交互配置）
#   切断時: 再 exec 後に run_main_resume()
#
# 【Colab 出力永続化の凍結規律】/content 揮発層に依存しない——mount_drive() を
# 生成前に必ず呼び、results を Drive 実体へシンボリックリンクする（逐次永続化）。
import os
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
import subprocess
try:
    subprocess.run(["pip", "uninstall", "-y", "hf_xet"], capture_output=True, text=True, timeout=120)
    subprocess.run(["pip", "install", "-q", "hf_transfer"], capture_output=True, text=True, timeout=300)
    subprocess.run(["pip", "install", "-q", "-U", "bitsandbytes"], capture_output=True, text=True, timeout=300)
    # transformers 5.x は BitsAndBytesConfig 4bit が効かず bf16 ロード→OOM（追補D実測）。4.x へピン。
    subprocess.run(["pip", "install", "-q", "transformers>=4.51,<5"], capture_output=True, text=True, timeout=600)
except Exception as _e:
    print("download-backend setup note:", _e)
import hashlib, urllib.request, json, time, sys
import bitsandbytes as _bnb
import transformers as _tf
print("bitsandbytes:", _bnb.__version__, "| transformers:", _tf.__version__)
assert _tf.__version__.startswith("4."), "transformers 5.x が残っている——セッション再起動後に再 exec"

# --- 凍結物の取得と LF-SHA 照合（boot_pilot.py の実績方式） ---
RAW = "https://raw.githubusercontent.com/YutaKusumi/ryokai-os/main/verification/"
FILES = {
    "app-scenarios.json":          "7AD7E49459D5C40203DF04F6819575796AD3E880BCB5A12801635BF304E4DDC1",
    "pipeline/app_parser_rev2.py": None,
    "pipeline/app_runner_adde.py": None,   # 実行器（凍結SHAは FREEZE-RECORD 参照）
    # A2-on-full: GitHub は LF 格納（AAB363D8…）。FROZEN E1-5 の 9DE7B788… はローカル
    # CRLF 版の生バイト SHA——内容は改行のみの差で同一（app_runner_adde.py ヘッダ注記）。
    "arms/A2-on-full.md":          "AAB363D85E103C13B72691749732BBE8882FCFCF4666CCAED79C1D46D27C0A4D",
    "armsD/preamble-neutral.md":   "45372D08DD75CD2C95855495E29B8264B636D882E61A1DA40872756EA341E16C",
    "armsE/preamble-Lneg.md":      "A16E20E4827D9C8673A60C35354A6BE01D3A00521018314787D9CCEED0F88957",
    "armsE/preamble-Onull.md":     "2123B3CD8586E7DF8B9A0A983B1F93A3C4BE4F0A2F9B396ED216CBC60A0FD733",
    "armsE/preamble-O.md":         "F3EE60C33F825575CE4D9D3AFB7409FD5BAA130A3C51C2B7130665C16FDEAE12",
}


def lf_sha(p):
    d = open(p, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    return hashlib.sha256(d.encode("utf-8")).hexdigest().upper()


def fetch_and_verify():
    for d in ["arms", "armsD", "armsE", "pipeline", "results"]:
        os.makedirs("/content/" + d, exist_ok=True)
    allok = True
    for rel, want in FILES.items():
        dst = "/content/" + rel
        urllib.request.urlretrieve(RAW + rel, dst)
        got = lf_sha(dst)
        ok = (want is None) or (got == want)
        allok = allok and ok
        print(("OK   " if ok else "BAD  ") + rel + ("" if want else "  (no-check)"))
    assert allok, "frozen SHA mismatch - abort"
    print("all frozen SHAs verified.\n")


def mount_drive():
    """逐次永続化（凍結規律: /content 揮発層に依存しない）。生成前に必ず呼ぶ。"""
    import shutil
    from google.colab import drive
    drive.mount("/content/drive")
    dest = "/content/drive/MyDrive/ryokai-adde-results"
    os.makedirs(dest, exist_ok=True)
    if os.path.exists("/content/results") and not os.path.islink("/content/results"):
        for f in os.listdir("/content/results"):
            shutil.copy("/content/results/" + f, dest)
        shutil.rmtree("/content/results")
    if not os.path.islink("/content/results"):
        os.symlink(dest, "/content/results")
    print("results ->", os.path.realpath("/content/results"))


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
            print(f"snapshot_download retry {attempt + 1}/6: {str(e)[:150]}")
            time.sleep(5)
    # 追補C/Dと完全同一: 4bit nf4・double_quant なし・device_map="auto"
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16,
                             bnb_4bit_quant_type="nf4")
    print("GPU:", torch.cuda.get_device_name(0), "| free/total GiB:",
          [round(x / 2**30, 1) for x in torch.cuda.mem_get_info(0)])
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, device_map="auto",
                                                 quantization_config=bnb)
    model.eval()
    fp = model.get_memory_footprint() / 2**30
    print(f"model loaded: {MODEL_ID} | footprint {fp:.1f} GiB")
    assert fp < 30, f"4bit量子化が効いていない疑い（{fp:.1f} GiB）——中止"


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


def tokenizer_report():
    """E8: 四腕の実プロンプト（system+前置き+N2結合）のトークン数を実測して報告。"""
    sys.path.insert(0, "/content/pipeline")
    import app_runner_adde as R
    n2 = R.APP_SCEN["N2"]
    u2 = n2["text"] + R._INST[n2["family"]]
    for a, c in R.ARMS_E.items():
        user_t = R._read(c["preamble"]) + "\n\n" + u2
        msgs = [{"role": "system", "content": R._read(c["system"])},
                {"role": "user", "content": user_t}]
        ntok = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                       return_tensors="pt").shape[1]
        print(f"{a:6s} full 1T prompt tokens: {ntok}")


# --- 起動 ---
fetch_and_verify()
load_model()
sys.path.insert(0, "/content/pipeline")
import app_runner_adde as _R
run_pilot = _R.run_pilot
run_gate = _R.run_gate
run_gate_g4 = _R.run_gate_g4
run_main = _R.run_main
run_main_resume = _R.run_main_resume
# 実行器側のグローバルへ generate/MODEL_ID 等を注入（boot_pilot 方式）
_R.generate = generate
_R.MODEL_ID, _R.TEMPERATURE, _R.TOP_P = MODEL_ID, TEMPERATURE, TOP_P
import builtins
builtins.generate = generate
builtins.MODEL_ID, builtins.TEMPERATURE, builtins.TOP_P = MODEL_ID, TEMPERATURE, TOP_P
tokenizer_report()
print("\nboot_adde ready. 次: mount_drive() -> run_pilot() -> （判定）-> run_gate()")
