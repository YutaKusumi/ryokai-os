# 公開前検分・第二巡依頼——追補W 結果報告 draft3（裁15・系統外の目を含む最終関門）

**最初にご確認ください（定型質問）**: あなたはこのプロジェクトの過去の検分の記憶を持つセッション
ですか？ 持つ場合はその旨を冒頭に申告してください。本巡は**新規 Claude系一名＋非Claude系一名**の
体制です（第一巡は Claude 四名全員が記憶保持・「Gemini」経路一名が名乗り不一致となり、凍結約束
「系統外の目」が未充足だったため——経緯は報告 §7 と rulings に開示済み）。

## 対象と判定

検分対象は **addendum-W-results.md（draft3）**。判定三値: 公開可／修正のうえ公開／差し戻し。
第一巡の指摘（重大: §1 escalation 合成データ混入・§3.1 絶対形と追認8/31 の脱落・§3.2 機構名誤同定・
#12 時間記録非開示・B040 メモ言い換え・切断=リトライ機構・読み条項脱落群ほか約30件）は**全件反映済み**
（裁15〜裁17・対応の記録は FREEZE-RECORD と §7）。B040 は登録者裁定で「境界」へ改定
（addw-12-adjudication-B040.md・原本不改変）。

## 検分の観点

1. **第一巡指摘の反映確認**: 逐語= addw-results-review-fiveway-verbatim.md（同梱）の各指摘が draft3 で
   閉じているか。とくに: §1 の escalation 訂正／§3.1（決定しないが無関係でない・8/31・積/平均・分母48）
   ／§3.2（機構名撤回・四選択肢比較・n 開示・プール平均併記）／§3.8（時間記録・B040 逐語と裁定・
   対照群表）／§1 切断=リトライ二階目（W#48）／読み条項の全数（裁6・追記④・W10-14・別述語・
   kN=29格子点外・kW≤16・切断率・第三検定）／土台3.0／§2 予想逐語／§7 体制全記録。
2. **数値の独立再計算**: 全数値は同梱の一次記録から再計算可能（バンドル内で
   `python analyze_addw.py main trials-…jsonl` が出力全文を再現）。draft3 の数値は起草側で機械照合一巡を
   通してある（教訓の適用）が、独立の再計算を歓迎する。
3. **新規に書き加えた記述が過大でないか**: とくに §3.1 の「影響を残しつつ (a) への引力に上書き」・
   §3.2 の「(i) を裸にする計器が実質不在」・§3.8 の対照群の読み。
4. 主文の規律（セル5 逐語・特別条項非発動）・引用注意・COI。

## 手続き

指摘は番号つき（重大/中/軽）・読了申告は四値・返信は逐語保全。**指摘が出たら反映して公開**
（登録者の定めたループ回避の流れ・本巡が最終関門）。

## 同梱物（第一巡で不足指摘のあった器材を追加済み）

addendum-W-results.md（draft3・検分対象）／addw-analysis-output.txt・scores-addw-main.jsonl・
trials-addw-main-…jsonl・trials-addw-gate-n-…jsonl（G-N 15/30）／analyze_addw.py v3・dry_run_addw.py v3・
scorer_w.py・roster_matcher_v3.py・build_roster_union.py・app-scenarios.json／**instruction-W.md・
instruction-P.md・A2-on-full.md**（C1 逐語の照合先）／addendum-W-design-draft7.md・
**addendum-W-design-draft3.md**（§W9 予想本文）・凍結追記①〜④／addw-12-rubric.md・
addw-12-verdicts.json・KEY-…jsonl・**addw-12-adjudication-B040.md・make_12_scoring_addw.py**／
addendum-W-analyzer-rulings.md・addendum-W-scorer-rulings.md／
**addw-results-review-fiveway-verbatim.md**（第一巡逐語）
