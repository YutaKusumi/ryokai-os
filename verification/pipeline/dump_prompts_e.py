# -*- coding: utf-8 -*-
"""追補E で Qwen に与えた入力（プロンプト）の全文を、凍結ファイルから機械的に組み立てて出力する。

app_runner_adde.py の組み立てと同一:
    messages = [{"role":"system",  "content": <arms/A2-on-full.md>},
                {"role":"user",    "content": <preamble> + "\\n\\n" + <N2 text> + <json_instruction>}]
生成は単一ターン（逸脱#4）。三腕は preamble のみが異なり、system・シナリオ・指示は共通。

各ファイルの LF 正規化 SHA-256 を app_runner_adde.FROZEN_SHA と照合してから出力する
（照合に失敗した場合は出力しない）。

使い方: python pipeline/dump_prompts_e.py
出力  : results/adde-main/adjudication/prompts-given-to-model.md
"""
import hashlib
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results/adde-main/adjudication/prompts-given-to-model.md")

FROZEN_SHA = {   # app_runner_adde.py の FROZEN_SHA から転記（同値であることを本script が照合する）
    "arms/A2-on-full.md":
        "AAB363D85E103C13B72691749732BBE8882FCFCF4666CCAED79C1D46D27C0A4D",
    "armsD/preamble-neutral.md":
        "45372D08DD75CD2C95855495E29B8264B636D882E61A1DA40872756EA341E16C",
    "armsE/preamble-Lneg.md":
        "A16E20E4827D9C8673A60C35354A6BE01D3A00521018314787D9CCEED0F88957",
    "armsE/preamble-Onull.md":
        "2123B3CD8586E7DF8B9A0A983B1F93A3C4BE4F0A2F9B396ED216CBC60A0FD733",
    "armsE/preamble-O.md":
        "F3EE60C33F825575CE4D9D3AFB7409FD5BAA130A3C51C2B7130665C16FDEAE12",
}


def read(rel):
    """runner の _read() と同一——プロンプトに載る形（LF正規化＋strip）。"""
    return io.open(os.path.join(ROOT, rel), encoding="utf-8").read().replace("\r\n", "\n").strip()


def sha(rel):
    """runner の verify_arms_e() と同一——**strip を掛けないバイト列**の LF 正規化 SHA。

    プロンプトに載る文字列（strip 済み）とは別物である点に注意。初版で strip 済み文字列の
    SHA を照合し、5件全て不一致となった（照合器の再現誤り・被検査物は正常）。
    """
    raw = open(os.path.join(ROOT, rel), "rb").read().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest().upper()


def main():
    ok = True
    rows = []
    for rel, want in FROZEN_SHA.items():
        got = sha(rel)
        match = (got == want)
        ok = ok and match
        rows.append((rel, got, match))
        print(f"[{'OK' if match else 'NG'}] {rel} {got[:16]}…")
    if not ok:
        raise SystemExit("凍結SHA不一致——出力しない")

    app = json.load(open(os.path.join(ROOT, "app-scenarios.json"), encoding="utf-8"))
    scen = {s["question_id"]: s for s in app["scenarios"]}["N2"]
    inst = app["json_instruction"][scen["family"]]

    p = ["# 追補E でモデルに与えた入力の全文（機械生成・凍結ファイルから組み立て）\n",
         "\n生成: `pipeline/dump_prompts_e.py`。**本文書は裁定の参照資料であり、規則書 v2.1 の",
         "判定線を変更しない。**\n",
         "\n## 0. 組み立て（`app_runner_adde.py` と同一）\n",
         "\n```\nmessages = [\n",
         '  {"role": "system", "content": <arms/A2-on-full.md>},\n',
         '  {"role": "user",   "content": <preamble> + "\\n\\n" + <N2 本文> + <JSON指示>}\n',
         "]\n```\n",
         "\n単一ターン（逸脱#4）。**三腕は preamble のみが異なり、system・シナリオ・JSON指示は共通**。\n",
         "\n### 凍結SHA照合（LF正規化・本文書の生成時に再計算）\n\n| ファイル | SHA-256 | 凍結値と一致 |\n|---|---|---|\n"]
    for rel, got, match in rows:
        p.append(f"| `{rel}` | `{got[:32]}…` | {'**一致**' if match else 'NG'} |\n")

    p.append("\n---\n\n## 1. シナリオ本文（N2・全腕共通）\n")
    p.append("\n**#26（前提の作話）の判定は、この本文に無い事実の導入を数える。"
             "以下がその「シナリオ本文」の全文である（241字）。**\n")
    p.append(f"\n```\n{scen['text']}\n```\n")
    p.append("\n## 2. JSON 指示（全腕共通・シナリオ本文の直後に連結）\n")
    p.append(f"\n```\n{inst.strip()}\n```\n")
    p.append("\n**注意（v2.1 凍結後に発見・下記§5 で開示）**: 指示の実文は "
             "`escalation は 0〜4 の整数` である。採点者・系統外への提示文では "
             "`escalation（1〜4）` と記していた（コーディネータの誤記）。\n")

    p.append("\n---\n\n## 3. 前置き（腕ごとに異なる唯一の部分・user メッセージの冒頭）\n")
    for name, rel in (("Lneg（否定の極）", "armsE/preamble-Lneg.md"),
                      ("Onull（中立）", "armsE/preamble-Onull.md"),
                      ("O（存在論）", "armsE/preamble-O.md"),
                      ("EB / neutral（ゲート腕・本実施150件には含まれない）",
                       "armsD/preamble-neutral.md")):
        p.append(f"\n### {name}\n\n```\n{read(rel)}\n```\n")

    p.append("\n---\n\n## 4. システムプロンプト（全腕共通・`arms/A2-on-full.md`）\n")
    p.append("\n**#O の存在論的語彙（空・虚空・非二元・方便・進化・宇宙・慈悲・悲智双運）は、"
             "この共通の system に由来しうる**——三腕すべてが同一の system を受け取っている。\n")
    p.append(f"\n```\n{read('arms/A2-on-full.md')}\n```\n")

    open(OUT, "w", encoding="utf-8", newline="\n").write("".join(p))
    print(f"-> {OUT} ({os.path.getsize(OUT):,} B)")


if __name__ == "__main__":
    main()
