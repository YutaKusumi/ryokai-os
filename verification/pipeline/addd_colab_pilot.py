# -*- coding: utf-8 -*-
"""追補D Part B 着地パイロット — Colabセル集（コピペ用フォールバック・順に実行）。

正式な実行経路は pipeline/boot_pilot.py / boot_main.py（GitHub raw から commit固定
URLでexecする自己完結ブート）。本ファイルは、その経路が使えない場合の手動貼り付け
フォールバックであり、boot_pilot.pyで確立した全修正を反映する:
  - HF Xet経路の停滞/401回避（無効化＋hf_xet除去・hf_transfer導入）
  - transformers 5.x のBitsAndBytesConfig無効化バグ回避（4.x系へピン留め）
  - bitsandbytes -U 必須・double_quant不使用・device_map="auto"
    （追補Cの実績設定=2〜4分/試行に完全一致させる。double_quantは推論を遅くする）
  - attention_mask明示・<|im_end|>を停止トークンに含める
  - 単一ターン構造（逸脱#4）: 決断内容(N2)の手前にアシスタントターンが一つでも
    存在すると、内容非依存でModel2が儀式部の反復ループに退行することが実測で
    確認された。前置き文はuserターン内でN2の直前に結合する（Model1という概念は
    廃止）。詳細: deviation-4-addd-single-turn.md。

セルは "# === CELL n ===" で区切る。上から順にColabへ貼って実行。
"""

# === CELL 1 === 環境セットアップ（新VM・GPU・ダウンロード経路の対処）
CELL_1 = r'''
import os
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
import subprocess
subprocess.run(["pip", "uninstall", "-y", "hf_xet"], capture_output=True, text=True, timeout=120)
subprocess.run(["pip", "-q", "install", "hf_transfer"], capture_output=True, text=True, timeout=300)
subprocess.run(["pip", "-q", "install", "-U", "bitsandbytes"], capture_output=True, text=True, timeout=300)
subprocess.run(["pip", "-q", "install", "transformers>=4.51,<5"], capture_output=True, text=True, timeout=600)
import torch, transformers, bitsandbytes
print("torch", torch.__version__, "| transformers", transformers.__version__,
      "| bitsandbytes", bitsandbytes.__version__, "| cuda", torch.cuda.is_available())
assert transformers.__version__.startswith("4."), "transformers 5.x が残っている——セッション再起動が必要"
'''

# === CELL 2 === 凍結物の取得＋LF-SHA照合（GitHub raw・new VM再現性）
CELL_2 = r'''
import os, hashlib, urllib.request
RAW = "https://raw.githubusercontent.com/YutaKusumi/ryokai-os/main/verification/"
FILES = {
  "app-scenarios.json":                 "7AD7E49459D5C40203DF04F6819575796AD3E880BCB5A12801635BF304E4DDC1",
  "pipeline/app_parser_rev2.py":        None,  # 器材（SHA照合は本実施で・パイロットは取得のみ）
  "arms/A5-prime-secular-3.1.md":       "0909DB7F90F8B49FD557AEF8727450799E845DE8F6E31E1579E78A2CEB9F4BC8",
  "arms/A2-on-full.md":                 "AAB363D85E103C13B72691749732BBE8882FCFCF4666CCAED79C1D46D27C0A4D",
  "armsD/preamble-neutral.md":          "45372D08DD75CD2C95855495E29B8264B636D882E61A1DA40872756EA341E16C",
  "armsD/preamble-GH.md":               "5CEE23D946B3DF524B575CCD7E7EDCC5F4299A5663EC229A7D55151EB4744FDC",
  "armsD/preamble-GHnull.md":           "834F9B4EA520EF37DBC890549E430BDF2186182F5F8F4A9100F5DE2A00F72671",
  "armsD/GS-gate.md":                   "923DA1EF16E6FA39E024797A01888F04AC59190C644192A1F7D1B316DFF18E53",
  "armsD/GL-followup.md":               "ADC5B8F2B73D0D7B43E6DA0E3B806741C161E161861B60523EE83182B14AB9A9",
}
def lf_sha(path):
    data = open(path, encoding="utf-8", newline="").read().replace("\r\n","\n")
    return hashlib.sha256(data.encode("utf-8")).hexdigest().upper()
os.makedirs("/content/armsD", exist_ok=True)
os.makedirs("/content/arms", exist_ok=True)
os.makedirs("/content/pipeline", exist_ok=True)
allok = True
for rel, want in FILES.items():
    dst = "/content/" + rel
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    urllib.request.urlretrieve(RAW + rel, dst)
    got = lf_sha(dst)
    if want is None:
        print(f"GET  {rel}  (SHA照合なし・取得のみ)")
    else:
        ok = got == want
        allok &= ok
        print(f"{'OK ' if ok else 'MISMATCH'} {rel}\n     {got}")
assert allok, "凍結SHA不一致——中止（凍結物が変わっている）"
print("\n全凍結物のLF-SHA一致。")
'''

# === CELL 3 === GS腕の機械構成（A5'末尾にGSゲートを連結・凍結構成規則）
CELL_3 = r'''
def _read_lf(p): return open(p, encoding="utf-8").read().replace("\r\n","\n").rstrip("\n")
a5p  = _read_lf("/content/arms/A5-prime-secular-3.1.md")
gate = _read_lf("/content/armsD/GS-gate.md")
gs   = a5p + "\n\n" + gate + "\n"
open("/content/armsD/A5-prime-GS-gate.md","w",encoding="utf-8",newline="\n").write(gs)
import hashlib
print("GS arm chars:", len(gs))
print("GS arm LF-SHA:", hashlib.sha256(gs.encode()).hexdigest().upper())
print("（ローカルbuild_gs_arm.py出力の 7915A57EA7E4F397C0EDC61C5AC8E5E57B4AEBB0EE72CCD9A80FEB6E434867BE と一致すべき）")
'''

# === CELL 4 === モデルロード＋generate（追補C実績設定に一致・attention_mask/eos明示）
CELL_4 = r'''
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch
MODEL_ID = "Qwen/Qwen3-30B-A3B-Instruct-2507"
TEMPERATURE, TOP_P = 0.7, 0.9
# 追補C実績(2-4分/試行)と完全同一: double_quant不使用・device_map="auto"。
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16,
                         bnb_4bit_quant_type="nf4")
print("GPU:", torch.cuda.get_device_name(0), "| free/total GiB:",
      [round(x / 2**30, 1) for x in torch.cuda.mem_get_info(0)])
tok = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, quantization_config=bnb, device_map="auto")
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
    enc = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt",
                                  return_dict=True).to(model.device)
    with torch.no_grad():
        out = model.generate(input_ids=enc["input_ids"], attention_mask=enc["attention_mask"],
                             max_new_tokens=max_new_tokens, do_sample=True,
                             temperature=TEMPERATURE, top_p=TOP_P, return_dict_in_generate=True,
                             eos_token_id=_eos_ids(), pad_token_id=tok.eos_token_id)
    return tok.decode(out.sequences[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
print("model loaded.")
'''

# === CELL 5 === tokenizer実測（単一ターン後の実プロンプト長・登録D8項目）
CELL_5 = r'''
def _r(p): return open(p, encoding="utf-8").read().replace("\r\n","\n").strip()
import json
_APP = json.load(open("/content/app-scenarios.json", encoding="utf-8"))
SCEN = {s["question_id"]: s for s in _APP["scenarios"]}
INST = _APP["json_instruction"]
n2 = SCEN["N2"]; u2 = n2["text"] + INST[n2["family"]]
ARMS = {
 "A5p2T": ("/content/arms/A5-prime-secular-3.1.md", "/content/armsD/preamble-neutral.md"),
 "GH":    ("/content/arms/A5-prime-secular-3.1.md", "/content/armsD/preamble-GH.md"),
 "GHnull":("/content/arms/A5-prime-secular-3.1.md", "/content/armsD/preamble-GHnull.md"),
 "GS":    ("/content/armsD/A5-prime-GS-gate.md",    "/content/armsD/preamble-neutral.md"),
 "GL1":   ("/content/arms/A2-on-full.md",           "/content/armsD/preamble-neutral.md"),
}
for a,(sysp,pre) in ARMS.items():
    user_t = _r(pre) + "\n\n" + u2
    msgs=[{"role":"system","content":_r(sysp)},{"role":"user","content":user_t}]
    ntok=tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").shape[1]
    print(f"{a:7s} full 1T prompt tokens (system+preamble+N2): {ntok}")
'''

# === CELL 6 === 1T実行器（逸脱#4・単一ターン・パイロット埋め込み版）
CELL_6 = r'''
import time, hashlib, json, os
os.makedirs("/content/results", exist_ok=True)
def run_1t_pilot(arms, n_trials, tag, qid="N2"):
    out=f"/content/results/pilot-{tag}.jsonl"
    s=SCEN[qid]; u2=s["text"]+INST[s["family"]]
    with open(out,"a",encoding="utf-8") as f:
        for arm in arms:
            sysp,pre=ARMS[arm]; sys_t=_r(sysp); pre_t=_r(pre)
            user_t = pre_t + "\n\n" + u2
            for i in range(n_trials):
                t0=time.time()
                msgs=[{"role":"system","content":sys_t},{"role":"user","content":user_t}]
                raw=generate(msgs)
                from app_parser_rev2 import parse_app_v2
                p=parse_app_v2(raw,s["family"]); retry=False
                if p is None:
                    raw2=generate(msgs); p=parse_app_v2(raw2,s["family"]); retry=True
                    raw=raw+"\n\n===RETRY===\n\n"+raw2
                rec={"trial_id":hashlib.md5(f"{tag}{arm}{qid}{i}".encode()).hexdigest()[:12],
                     "arm":arm,"question_id":qid,"family":s["family"],"trial_index":i,
                     "turn_structure":"1T","raw_output":raw,"parsed":p,
                     "format_retry_used":retry,"seconds":round(time.time()-t0,1)}
                f.write(json.dumps(rec,ensure_ascii=False)+"\n"); f.flush()
                tl="OK" if p else "FORMAT_FAIL"
                if p and p.get("choice")=="refuse": tl="REFUSE"
                print(f"{arm} #{i} {tl} | total={rec['seconds']}s | choice={p.get('choice') if p else '-'}")
    print("done:",out)

import sys; sys.path.insert(0,"/content/pipeline")
run_1t_pilot(["A5p2T","GH","GHnull","GS"], 2, "addd-partB")   # 4腕×2=8
run_1t_pilot(["GL1"], 2, "addd-partB-gl")                     # GL第一パス×2
'''

# === CELL 7 === パイロット判定（着地確認）
CELL_7 = r'''
import json
recs=[json.loads(l) for l in open("/content/results/pilot-addd-partB.jsonl",encoding="utf-8")]
recs+= [json.loads(l) for l in open("/content/results/pilot-addd-partB-gl.jsonl",encoding="utf-8")]
n=len(recs); okj=sum(1 for r in recs if r["parsed"]); rty=sum(1 for r in recs if r["format_retry_used"])
print(f"総試行 {n} | JSON着地 {okj}/{n} | retry {rty}")
print("出力サンプル（先頭120字）:")
print("  ", recs[0]["raw_output"][:120].replace(chr(10)," "))
print("\n判定基準: JSON着地=全件（1T構造・アシスタントターンなし・ループが起きればparsedがNoneになり自動的に不合格）")
print("→ 満たせば探索版・本実施へ。満たさなければ打ち切り規約を協議。")
'''

# === CELL 8 === Driveマウント（本実施の逐次永続化・登録者OAuth）
CELL_8 = r'''
from google.colab import drive
drive.mount("/content/drive")
import os
DEST = "/content/drive/MyDrive/ryokai-addd-results"
os.makedirs(DEST, exist_ok=True)
# /content/results を Drive 実体へ（各試行の書き込みが即永続化）
if os.path.islink("/content/results") or os.path.exists("/content/results"):
    import shutil
    if not os.path.islink("/content/results"):
        for f in os.listdir("/content/results"):
            shutil.copy(f"/content/results/{f}", DEST)
        shutil.rmtree("/content/results")
os.symlink(DEST, "/content/results")
print("results -> ", os.path.realpath("/content/results"))
'''

# === CELL 9 === 探索版・本実施（分岐C確定・記述/検定なし・自動継続・逸脱#4）
CELL_9 = r'''
# 探索版本実施: 4確証腕×N2×30(記述) ＋ GL第一パス×30。計150試行。
# 分岐C確定ゆえ p値なし・記述のみ。乖離採点は回収後ローカルで（盲検二採点者）。
def run_1t_main(arms, n, tag, qid="N2"):
    import time, hashlib, json
    from app_parser_rev2 import parse_app_v2
    out=f"/content/results/trials-{tag}-Qwen3-30B-A3B-Instruct-2507.jsonl"
    s=SCEN[qid]; u2=s["text"]+INST[s["family"]]
    with open(out,"a",encoding="utf-8") as f:
        for arm in arms:
            sysp,pre=ARMS[arm]; sys_t=_r(sysp); pre_t=_r(pre)
            user_t = pre_t + "\n\n" + u2
            for i in range(n):
                t0=time.time()
                msgs=[{"role":"system","content":sys_t},{"role":"user","content":user_t}]
                raw=generate(msgs); p=parse_app_v2(raw,s["family"]); retry=False
                if p is None:
                    raw2=generate(msgs); p=parse_app_v2(raw2,s["family"]); retry=True
                    raw=raw+"\n\n===RETRY===\n\n"+raw2
                rec={"trial_id":hashlib.md5(f"{tag}{arm}{qid}{i}".encode()).hexdigest()[:12],
                     "run_tag":tag,"model":"Qwen/Qwen3-30B-A3B-Instruct-2507","quant":"4bit-nf4",
                     "temperature":TEMPERATURE,"top_p":TOP_P,"arm":arm,"notice":"off",
                     "question_id":qid,"family":s["family"],"trial_index":i,"turn_structure":"1T",
                     "preamble_arm":arm,"raw_output":raw,"parsed":p,
                     "format_retry_used":retry,"seconds":round(time.time()-t0,1),
                     "timestamp":time.strftime("%Y-%m-%dT%H:%M:%S")}
                f.write(json.dumps(rec,ensure_ascii=False)+"\n"); f.flush()
                tl="OK" if p else "FORMAT_FAIL"
                if p and p.get("choice")=="refuse": tl="REFUSE"
                print(f"{arm} #{i} {tl} | tot={rec['seconds']}s choice={p.get('choice') if p else '-'}")
    print("done:",out)

# 判定: CELL_7 の着地基準を満たしたときのみ、この行を実行（自動継続）
run_1t_main(["A5p2T","GH","GHnull","GS"], 30, "addd-main")   # 120試行
run_1t_main(["GL1"], 30, "addd-gl-firstpass")                # 30試行（GL第一パス）
print("本実施150試行 完了。回収→乖離採点→GL差し戻しへ。")
'''

if __name__ == "__main__":
    cells = [CELL_1, CELL_2, CELL_3, CELL_4, CELL_5, CELL_6, CELL_7, CELL_8, CELL_9]
    for i, c in enumerate(cells, 1):
        print(f"\n# ===== CELL {i} =====")
        print(c)
