# armsD — 追補D介入テキスト（凍結物）

追補D（preregistration-addendum-D-FROZEN.md）の統一2ターン構造で用いる介入テキストの逐語凍結。SHA-256はFREEZE-RECORD.mdに記帳。

## 構成規則（凍結）

- 全確証腕の会話構造: `Human 1`（前置き）→ `Model 1`（受容応答・自由生成）→ `Human 2`（N2シナリオ本文＝app-scenarios.json凍結のN2・無変更）。
- **A5′-2T**: システムプロンプト＝arms31/A5-prime-secular-3.1.md（凍結・無変更）。Human 1＝preamble-neutral.md。
- **GH**: システムプロンプト＝A5′同一。Human 1＝preamble-GH.md。
- **GH-null**: システムプロンプト＝A5′同一。Human 1＝preamble-GHnull.md。
- **GS**: システムプロンプト＝A5′本文の末尾に GS-gate.md を一区切り（空行一つ）で連結（機械構成・build script）。Human 1＝preamble-neutral.md（A5′-2Tと同一）。
- **GL（探索）**: システムプロンプト＝arms/A2-on-full.md（3.0全文・凍結・無変更）。Human 1＝preamble-neutral.md → Model 1 → Human 2＝N2 → Model 2（第一出力）→ **乖離事象と採点された試行のみ** Human 3＝GL-followup.md → Model 3（記述対象）。
- 前置きへの Model 1 受容応答は自由生成（max_new_tokens 512・暴走打ち切り規約はC8パイロットで確定）。

## 分量一致（GH vs GH-null）・許可含意チェック

GH: 174字 ／ GH-null: 173字（差 −1字・−0.6%）。tokenizer実測はC8で記帳。
GH-nullの許可・手続き語彙の機械照合（急がな／選ばなくて／答えない／許す／禁じ／保留／ゆっくり／待／原則／フォーマット／形式／丸め／規模）: **ヒット0**（凍結時実施・D8チェックの一部前倒し。完全な無色は不可能である旨は登録文書D1に明記——動くのは許可内容の有無）。
