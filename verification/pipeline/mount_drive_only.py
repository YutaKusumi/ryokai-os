# -*- coding: utf-8 -*-
"""Driveマウント＋/content/results symlink のみを行う（boot_main.pyと同一ロジック）。
resume_after_disconnect.py実行後のセッションで、モデル再ロードを伴わずに
Drive再接続を行うための小さな補助スクリプト。登録内容には触れない。
"""
import os, shutil
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
