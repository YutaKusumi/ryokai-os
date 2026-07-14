# -*- coding: utf-8 -*-
# 追補D 本実施（探索版・分岐C確定）自己完結ブート（Colabで exec）。
# パイロットPASS後に exec(open("boot_main.py").read())。
# Drive をマウントして results を Drive 実体へ（逐次永続化）→ 150試行。
# boot_pilot.py の関数（run_1t, generate, ARMS, SCEN, INST 等）が同一セッションに
# 定義済みであることを前提とする（逸脱#4・単一ターン構造）。
import os, shutil, json

# --- Drive マウント（登録者OAuth）＋逐次永続化 ---
from google.colab import drive
drive.mount("/content/drive")
DEST = "/content/drive/MyDrive/ryokai-addd-results"
os.makedirs(DEST, exist_ok=True)
if os.path.exists("/content/results") and not os.path.islink("/content/results"):
    for f in os.listdir("/content/results"):
        shutil.copy("/content/results/" + f, DEST)
    shutil.rmtree("/content/results")
if not os.path.islink("/content/results"):
    os.symlink(DEST, "/content/results")
print("results ->", os.path.realpath("/content/results"))

# --- 探索版本実施: 4腕×N2×30(記述) ＋ GL第一パス×30（逸脱#4・単一ターン）---
print("\n== 本実施（探索・記述・分岐C確定・p値なし）==")
run_1t(["A5p2T", "GH", "GHnull", "GS"], 30, "trials-addd-main-Qwen3-30B-A3B-Instruct-2507")
run_1t(["GL1"], 30, "trials-addd-gl-firstpass-Qwen3-30B-A3B-Instruct-2507")
print("\n本実施150試行 完了。回収→乖離採点→GL差し戻しへ。")
