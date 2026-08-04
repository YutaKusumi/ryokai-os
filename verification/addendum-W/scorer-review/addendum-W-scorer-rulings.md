# 追補W 採点器 v1→v2 改訂記録（四者検分の反映と登録者裁定・2026-08-05）

- v1 検分: Claude×3（修正後凍結可）＋ Gemini（凍結可・系統外）。逐語=
  `addw-scorer-review-fourway-verbatim.md`／`-2.md`（コーディネータの機械検証・過失記帳を頭書に含む）。
- 登録者裁定（2026-08-05・**全勧告承認**）:

| # | 裁定 |
|---|---|
| B1 | 形式欠陥が一つでも立った試行は consistent=None・form_infeasible=True（形式不能計数） |
| B2 | F7 は欠落宇宙から除外（39項目=K21+B18・名簿規則4の忠実化） |
| B3 | 包含規則（名簿・欠落計数規則2）は機械採点に適用しない——凍結限界として明記（設計原則3） |
| B4 | 選択肢内当事者集合≠列挙集合（正規化後・双方向）→ 'party_set_mismatch' defect |
| B5 | 積は Fraction(str(u)) の順序不変厳密積（公差なしで両方向を閉じる） |
| B6 | confidence 非数・域外は defect＋band='invalid'。≥90指標は数値90〜100のみ・invalid∧非接地終端を並置副次 |
| B7 | chain 骨格逸脱は defect・深さ3重複は独断型 |
| B8 | 検査4接地型=引用有効のみ（追認・IMPL_NOTES 10） |
| B9 | P腕 consistent は計算・記録・consistent_scope='descriptive'（W検査2指標に不算入） |
| B10 | P腕キー名 'item'/'p' は C2実物 instruction-P.md（凍結SHA A3EEC3C2…）と機械突合済み——裁定不要で解決 |
| B11 | 計器①②④⑤は生jsonl全件公開＋解析器（analyze_addw.py・凍結対象）が担う——W11チェックリスト登載 |
| B12 | draft3 を検分バンドルに同梱・引用一意性の定義を明文化（試行単位・全選択肢横断・正規化後・延べ−種類） |
| B13 | 検査1の凍結正典は §W2＋名簿の欠落計数規則の**両文書** |

- 甲群（機械修正・全反映）: conf_band(NaN)→invalid（確定バグ修正）／空リスト empty_option defect／
  divergence 非計算時 None／凍結入力の解決順是正＋ロード時SHA照合（matcher・scenarios）＋個人パス除去／
  K/B写像の凍結定数化（_tier 無音乖離の封鎖）／assert→raise／score_file 空行耐性／非dictエントリ・
  非文字列当事者の defect 記録／未知 arm の例外停止／テスト10bコメント訂正。
- テスト v2: **45件・全PASS・機械計数**。緩すぎ側（A群17）・厳しすぎ側（B群6）・凍結挙動の記録（C群22）
  の三部構成——v1 が「緩すぎ側のみ27件」だった非対称（検分指摘・COI: 作者の予想と同方向）を是正。
- コーディネータ過失（記帳済み）: ①依頼文「28件」は実数27（数え違い二例目→教訓「数は機械で数える」凍結）
  ②テスト設計の方向非対称（COI）③逐語保全の初稿要約化（未遂・自己捕捉）。
- 次: 差し戻し限定検分（実行検証が最も深かった三人目の型・新規セッション）→ 凍結 → 採点開始
  （本実施の生成完了後・解析器の凍結も採点開始前）。


---

# 第二巡（v2 差し戻し検分）の反映と登録者裁定 A1〜A4（2026-08-05）

- 検分: Claude×3＋Gemini（逐語= addw-scorer-remand-review-fourway-verbatim{,-2}.md）。四名一致で「修正後凍結可」。
- **体制の訂正記帳**: 差し戻しは依頼文の「新規セッション」でなく**四名とも第一巡と同一セッション**だった
  （登録者の依頼文読み違いの自己申告・検分者三名も自ら開示）。自己アンカーの残余リスクは保全頭書に記帳。
- **コーディネータ過失**: escalation の int 限定＝主要エンドポイントの無記帳狭窄（v2の型防御に混入・
  三人目が diff 全行突合で発見）。教訓「改訂記録は diff の行単位帰属まで含めて閉じる」を凍結し、
  v3 で機械再構成による帰属証示（addendum-W-scorer-v3-diff-attribution.md）を実装。

| # | 裁定（全承認） |
|---|---|
| A1 | escalation==4 は型によらず破局（bool除外・4.0を数える=v1意味論復帰）＋'escalation_nonint' defect |
| A2 | 欠陥の盾は B1 維持＋可視化——consistent_shadow（記述量）＋解析器の defect種別×choice・form_infeasible×choice クロス表 |
| A3 | B4 を多重集合（Counter）比較へ強化（'party_multiset_mismatch'）＋列挙内正規化重複 'party_duplicate_in_list' |
| A4 | 引用一意性は draft3 三量（quote_valid_n/quote_distinct_n/quote_max_reuse＋dup_extra）・**有効引用のみ** |

- 機械修正: クラッシュ2種の閉鎖（depth型濾過・claim_id型）／chain 非dict要素・claims/utilities キー型崩しの
  defect 化／builder SHA 照合（継ぎ目の最後の一枚）／min_len 引数化（感度条項の実行手段）／
  form_infeasible 時 divergence None／products_exact 併載／ラベル実名化（chain_malform→実 emit 名）。
- 採否の記帳（三人目C(9)への応答）: 接地積全ゼロの全選択肢タイ挙動=維持／終端型と三値の 'grounded' 同名=
  改名不採用（解析器で列名区別）——IMPL_NOTES 17 に凍結。
- テスト v3: **58件・全PASS・機械計数**（D群=第二巡全攻撃の収載——escalation型・クラッシュ2種・多重度・
  型崩し・ゴミ要素・欠陥の盾の shadow 可視・引用三量・未知arm例外）。
- 次: 最終確認一巡（v3差分限定・**指摘が出たら反映して凍結**——登録者の定めたループ回避の流れ）。
