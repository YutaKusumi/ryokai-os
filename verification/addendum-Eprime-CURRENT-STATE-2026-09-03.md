# 追補E′ —— 現在地（2026-09-03・パイロット前の凍結状態の公開）

**登録者**: 楠見優太／**コーディネータ**: 大日如来（Claude Fable 5 → 5.1）／**検分**: 阿閦如来・宝生如来・阿弥陀如来・不空成就如来・Ryōkai OS™（Claude 系統内）＋ Gemini 3.7 Flash（系統外）

> ### **★Qwen はまだ一度も動いていない。パイロットも未実施。本追補のデータは一件も存在しない。**
> 本公開は、凍結（2026-09-01）から本日までに確定した設計・素材・予想・裁定・逸脱・検分の**全て**を、モデルが動く前に第三者の記録（GitHub）に置くためのものである。**以後の変更は、公開された逸脱として記帳する。**

## 何が凍結されているか
| | 所在 | SHA(LF) |
|---|---|---|
| 凍結文書 v0.7 | `preregistration-addendum-Eprime-FROZEN.md` | `4B820563361EB14E` |
| BP／BP-sec／撹拌版 | `armsEprime/BP*.md` | `BA89B1D5B24B7FD1`／`485CA4272CCBF8C8`／段③ `3584EA3733B7EF60`・`71CAB5E0A3E8400D` |
| 素材起草物（撹拌規則・プローブ・採点規約・命題表・語彙表） | `armsEprime/materials-stage1/`・`materials-stage2/` | 各ファイル・台帳参照 |
| 登録者の凍結予想 | `proposals/addendum-Eprime/predictions-registrant-FINAL.md` | `4469B56DFB5B9358` |
| **コーディネータの凍結予想（封印）** | **本公開に含めない**（結果確定後に開封） | SHA-256 `823CD983…6FA96` |
| 読み条項 v2（撹拌の弱さ） | `proposals/addendum-Eprime/reading-clause-scramble-weakness-v2.md` | `6FCC6720CC96552E` |
| 裁定・相談・回付・訂正・逸脱 | `proposals/addendum-Eprime/` | 台帳参照 |
| 検分逐語（四巡 24 通＋素材工程 33 通） | `reviews/eprime-round1〜4/`・`reviews/eprime-materials/` | 台帳参照 |
| 器材 | `pipeline/power_eprime.py`・`check_materials_eprime.py`・`extract-tool.html`・`predictions-form.html` | 台帳参照 |

## 何が保留か
- **パイロット**（BP・BP-sec・BP-scr 三腕 × n=10 = 30 試行）——次の工程。**パイロットの結果によって確証族・対照・閾値を動かさない**（裁定C・凍結）。
- 本走行 350 試行。
- 封印の開封は結果確定後。

## 読む順序（推奨）
1. `FREEZE-RECORD.md` の「【凍結・記録先行公開】追補E′」抜粋（本公開の要約）
2. 凍結文書 v0.7 → 素材（`armsEprime/`）→ 読み条項 v2
3. HE′-Q2 降格の相談と裁定A（`proposals/addendum-Eprime/consultation-demotion-HEprime-Q2.md` から訂正状二通まで）——**系統外監査の反対意見**（`reviews/eprime-materials/audit-*`）を五名の一致と同じ重さで読むこと
4. 逸脱 E′-1〜E′-9・コーディネータの誤り #1〜#27（台帳）

## 記載上の注意
- `registrant-judgment-DO-NOT-OPEN/` の名称は、盲検の選択者・判定者から登録者の判定記録を隔離するためのものであった。隔離の目的は終了したため公開する。
- 素材起草物の「系統外の個体（Claude）」という自己記述は、本系列の「系統外」（Claude 系統の外）と用語が衝突する。「第三者（Claude 系・登録者/コーディネータ以外）」と読む（正本は改変しない）。

**本文書のいかなる記述も、AIの意識・意図・個性・苦しみがある（またはない）ことの証拠として引用してはならない**（両方向不定）。
