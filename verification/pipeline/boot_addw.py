# -*- coding: utf-8 -*-
# 追補W 自己完結ブート（Colabで exec）。boot_adde.py（追補E・実績済み）の環境設定を継承。
#
# 手順（feedback_colab-browser-ops の定石: 直打ちせず GitHub 公開→短い fetch+exec）:
#   CELL1: 本ファイルを取得して実行
#     import urllib.request
#     urllib.request.urlretrieve("https://raw.githubusercontent.com/YutaKusumi/ryokai-os/"
#                                "main/verification/pipeline/boot_addw.py", "boot_addw.py")
#     exec(open("boot_addw.py").read())
#   （transformers のピン留めでセッション再起動が要る場合は、再起動後にもう一度 exec）
#   CELL2: mount_drive() ; run_form_pilot()   # G-W/P形式パイロット（W6-1）: W/P各8試行・形式判定のみ
#   CELL3: pilot_stats()                      # トークン分布 p95/p99・切断率・parse率のみ報告
#   （→ 凍結追記〔max_new_tokens・介入文の最終文面〕→ 登録者確認）
#   CELL4: run_gate_n()                       # G-N 基底30試行（判定は解析側で G-A/B/C/A' 機械適用）
#   CELL5: run_main()                         # G-N 通過後のみ・150試行（N/W/P 腕交互配置）
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

# --- 凍結物の取得と LF-SHA 照合（boot_adde.py の実績方式） ---
RAW = "https://raw.githubusercontent.com/YutaKusumi/ryokai-os/main/verification/"
FILES = {
    "app-scenarios.json":          "7AD7E49459D5C40203DF04F6819575796AD3E880BCB5A12801635BF304E4DDC1",
    "pipeline/app_parser_rev2.py": None,
    "pipeline/app_runner_w.py":    None,   # 実行器（草稿版・凍結追記で確定）
    "arms/A2-on-full.md":          "AAB363D85E103C13B72691749732BBE8882FCFCF4666CCAED79C1D46D27C0A4D",
    "armsE/preamble-Onull.md":     "2123B3CD8586E7DF8B9A0A983B1F93A3C4BE4F0A2F9B396ED216CBC60A0FD733",
    # instruction-{W,P}: 草稿版 SHA（build_arms_w.py の実測・パイロット書式修正時は両表を同時更新）
    "armsW/instruction-W.md":      "679601C91D2F409A35392DFF2C6BEDD652B78A8F534B4E084C96E016FBA4642F",
    "armsW/instruction-P.md":      "A3EEC3C2522AF2979D59AF5A206504E196D638377F6D9CBE30B1ABF37E267089",
}


def lf_sha(p):
    d = open(p, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    return hashlib.sha256(d.encode("utf-8")).hexdigest().upper()


def fetch_and_verify():
    for d in ["arms", "armsE", "armsW", "pipeline", "results"]:
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
    dest = "/content/drive/MyDrive/ryokai-addw-results"
    os.makedirs(dest, exist_ok=True)
    if os.path.exists("/content/results") and not os.path.islink("/content/results"):
        for f in os.listdir("/content/results"):
            shutil.copy("/content/results/" + f, dest)
        shutil.rmtree("/content/results")
    if not os.path.islink("/content/results"):
        os.symlink(dest, "/content/results")
    print("results ->", os.path.realpath("/content/results"))


def disable_hf_transfer():
    """hf_transfer を実行中に無効化する（環境変数＋既 import 済みモジュール定数の両方）。"""
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    try:
        import huggingface_hub.constants as _C
        _C.HF_HUB_ENABLE_HF_TRANSFER = False
    except Exception:
        pass
    for mod in ("huggingface_hub.file_download", "huggingface_hub._snapshot_download"):
        try:
            import importlib
            m = importlib.import_module(mod)
            if hasattr(m, "HF_HUB_ENABLE_HF_TRANSFER"):
                setattr(m, "HF_HUB_ENABLE_HF_TRANSFER", False)
        except Exception:
            pass
    print("  -> hf_transfer を無効化して再試行します")


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
            # hf_transfer が害になる環境がある（2026-08-04 実測: 即時失敗を繰り返す）。
            # 2回失敗したら自動で無効化して再試行する（追補D の「有効化で解決」と逆向きの実測・
            # どちらに転んでも進めるよう両方向のフォールバックを持たせる）。
            if attempt == 1:
                disable_hf_transfer()
            time.sleep(5)
    # 追補C/D/Eと完全同一: 4bit nf4・double_quant なし・device_map="auto"
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


def generate_ex(msgs, max_new_tokens=4096):
    """生成＋finish_reason＋新規トークン数（系統外検分・重大1の実装の心臓部）。
    finish_reason: 新規トークン数が max_new_tokens に達したら "length"、それ以外は "stop"。
    （transformers 4.x の generate は finish_reason を直接返さないため、新規長との一致で判定する。
      eos で丁度 max に達する縁は "length" 側に倒す——切断を見逃さない保守側。）"""
    import torch
    enc = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt",
                                  return_dict=True).to(model.device)
    with torch.no_grad():
        out = model.generate(input_ids=enc["input_ids"], attention_mask=enc["attention_mask"],
                             max_new_tokens=max_new_tokens, do_sample=True,
                             temperature=TEMPERATURE, top_p=TOP_P, return_dict_in_generate=True,
                             eos_token_id=_eos_ids(), pad_token_id=tok.eos_token_id)
    n_in = enc["input_ids"].shape[1]
    seq = out.sequences[0]
    n_new = seq.shape[0] - n_in
    finish = "length" if n_new >= max_new_tokens else "stop"
    text = tok.decode(seq[n_in:], skip_special_tokens=True)
    return text, finish, int(n_new)


def generate(msgs, max_new_tokens=4096):
    """互換ラッパ（N腕・既存器材との互換）。"""
    return generate_ex(msgs, max_new_tokens=max_new_tokens)[0]


def tokenizer_report():
    """三腕の実プロンプト（system+前置き+N2+出力指示）の入力トークン数を実測して報告。"""
    sys.path.insert(0, "/content/pipeline")
    import app_runner_w as R
    n2 = R.APP_SCEN["N2"]
    for a, c in R.ARMS_W.items():
        inst = R._read(c["instruction"]) if c["instruction"] else R._INST[n2["family"]]
        user_t = R._read(c["preamble"]) + "\n\n" + n2["text"] + inst
        msgs = [{"role": "system", "content": R._read(c["system"])},
                {"role": "user", "content": user_t}]
        ntok = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                       return_tensors="pt").shape[1]
        print(f"{a:3s} full 1T prompt tokens: {ntok} | max_new={R.MAX_NEW[a]}")


# --- 起動 ---
fetch_and_verify()
load_model()
sys.path.insert(0, "/content/pipeline")
import app_runner_w as _R
run_form_pilot = _R.run_form_pilot
pilot_stats = _R.pilot_stats
run_gate_n = _R.run_gate_n
run_main = _R.run_main
run_main_resume = _R.run_main_resume
# 実行器側のグローバルへ generate/generate_ex/MODEL_ID 等を注入（boot_adde 方式）
_R.generate = generate
_R.generate_ex = generate_ex
_R.MODEL_ID, _R.TEMPERATURE, _R.TOP_P = MODEL_ID, TEMPERATURE, TOP_P
import builtins
builtins.generate = generate
builtins.generate_ex = generate_ex
builtins.MODEL_ID, builtins.TEMPERATURE, builtins.TOP_P = MODEL_ID, TEMPERATURE, TOP_P
tokenizer_report()
print("\nboot_addw ready. 次: mount_drive() -> run_form_pilot() -> pilot_stats()")
