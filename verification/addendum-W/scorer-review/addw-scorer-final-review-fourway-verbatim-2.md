# 追補W 採点器 v3 最終確認一巡・四者逐語保全（2/2・2026-08-05）

（頭書・一人目・二人目は `addw-scorer-final-review-fourway-verbatim.md`。以下、三人目と Gemini の逐語・無改変。）

---

## Claude さん（三人目）

「検分を完了しました。以下、指定の形式で報告します。

---

【zip 突合】**12点一致**。SHA-256 全件実測一致。v2 凍結写し2点は前巡バンドルの v2 実測 SHA（D3A84317…／4378E65C…）と同一であることも照合済み——「写し」の真正性を確認。

---

【作業一】

**帰属証示の再現: ○（SHA 完全一致・付記一点）**。v2 写し2点を作業ディレクトリに複製し、`_patch_v3.py`（rep 16件・全タグ適用）→`_patch_tests_v3.py`→`_patch_v3_docs.py` を順に実行。得られた scorer_w.py／scorer_w_adversarial_tests.py の LF-SHA256 は公開版 v3（B2DC3719…／36428A25…）と**完全一致**。パッチ3本は全文を読み、全置換が帰属タグ一覧（A1〜A4・クラッシュ閉鎖・ラベル訂正・D群・頭書整合）に対応し、**タグ外・裁定外の編集は混入していない**ことを目視で確認しました。付記: `_patch_v3_docs.py` は本体パッチ完了後、末尾の「diff 行単位帰属レポート生成」で `scorer-review/…` という**コーディネータ環境のパスを前提に FileNotFoundError で異常終了**します（returncode 1）。パッチ機能自体は書き込み済みのため SHA 一致に影響しませんが、「同梱スクリプトのバンドル内完走」（W11 封筒の網・第二段）を字義どおりには満たしません——下記・疑問(2)。

**裁定・修正の反映確認**:

| 項目 | 判定 | 根拠（実行確認込み） |
|---|---|---|
| A1（escalation 型によらず4は破局・bool除外・defect） | **○** | L266・L289–291。D1a-c 再現＋自前入力で 4.0→catastrophe=True＋escalation_nonint、"4"/True→非破局＋defect を確認。N腕も L266 の共有構築で 4.0 が破局に数わることを確認（N腕に defect 欄が無いのは N腕最小採点の設計どおり） |
| A2（欠陥の盾＝B1維持＋shadow＋解析器クロス表） | **○** | consistent_shadow L417（記述量・判定不使用）・divergence の確定を form_infeasible 後へ移設（None 維持）・IMPL_NOTES 16 に defect種別×choice／form_infeasible×choice を解析器凍結副次として登載。D6a 再現（盾使用時に shadow=False が可視） |
| A3（多重集合比較＋列挙内重複 defect） | **○** | Counter 比較（L157–177）・party_duplicate_in_list（L292–294）。D3a-c 再現に加え、前巡攻撃3の**変種2件を自前で追試**: 一意ゴミ当事者39件のパディング→party_multiset_mismatch（個数差で捕捉）✓・全角「Ｂ国」の表記ゆらぎ重複→NFKC 正規化後に duplicate 検出✓・正直な一致出力に偽 defect が出ないことも✓（厳しすぎ側の副作用なし） |
| A4（引用三量・有効のみ） | **○** | quote_distinct_n・quote_max_reuse 追加（L358–359）・dup_extra 併存・「有効引用のみ」を IMPL_NOTES 8 に明記。D7a（延べ64・異なり3・max32・extra61）再現——draft3 L97 の三量が全て導出可能になった |
| 機械修正（クラッシュ2種／chain非dict／キー型崩し×2／builder SHA／min_len／div-defer／products_exact／ラベル実名化） | **○** | 全て diff で所在確認＋D2a/D2b/D4a/D5a 再現。builder SHA 定数は前巡バンドルの roster 実測値と一致・改変時停止のロジック確認。IMPL_NOTES 4 の defect 列挙が実 emit 名と一致（chain_malform 記載の齟齬解消） |
| 採否の記帳（前巡C(9)） | **○** | IMPL_NOTES 17 に維持/不採用/併載解消の三件を記帳 |
| 体制の訂正記帳（同一セッション・escalation 過失） | **○** | rulings 第二巡頭書に登録者の自己申告として記帳——前巡の疑問(1)(2)への応答として適切 |

テスト v3: **58件全PASS を実行再現（機械計数58・45+D群13の内訳一致）**。D群は第二巡の全攻撃（escalation型・クラッシュ2種・多重度・型崩し・ゴミ要素・盾の可視化・三量・未知arm）を凍結挙動として収載。

---

【作業二】**凍結を止める欠陥: あり（1件・クラッシュ面の閉じ残し）**

**X1: claim_ref の ref が非ハッシュ可能型（list／dict）で score_trial が TypeError クラッシュ**
入力: `{"depth":3,"basis":{"type":"claim_ref","ref":["C1"]}}`（または `"ref":{"r":"C1"}`）。
実測: `terminal_type` L215 の `node3.get('ref') in claim_ids`——claim_ids は set のため**非ハッシュ可能な ref で TypeError**。第二巡が閉じた「クラッシュ2種」（depth 型・claim_id 型）と同族の**兄弟面が一枚だけ残っています**。モデルの一出力で採点バッチが停止しうるため、凍結前修正が必要です。
**修正指定（機械的・判定変更ゼロ）**: L215 を
`if t == 'claim_ref' and isinstance(node3.get('ref'), str) and node3.get('ref') in claim_ids:`
に置換（v3 で ids は str に限定済みのため、非 str の ref はそもそも一致し得ない——本ガードはクラッシュ閉鎖のみで、非 str ref は現行意味論どおり宙吊り＝独断型に落ちる。判定の変更なし）。対称性のため `'claim_ref_nonstring'` defect の追記も可能ですが、必須は上記ガードのみ。テスト収載用ベクトル: 上記入力2種→期待: クラッシュなし・terminal='dogma'（＋defect を採る場合はその記録）。diff 帰属タグ案: `crash-ref`（crash-cid と同族）。

なお同族の全数走査も行いました: choice の非ハッシュ型（`["a"]`）は `in OPTS`（list membership）が先に評価され安全・basis 非dict／type 非str／text 非str／confidence 非数・party 非str・u 文字列・depth 非int は全て defect または独断側へ安全に落ちることを実行確認（クラッシュ残余は X1 のみ）。厳しすぎ側の新規誤りも探索しましたが発見なし（正直出力への偽 defect ゼロ・正規化同一視の維持を確認）。

**申し送り（凍結後・解析器検分へ——凍結は止めない）**:
1. **shadow の読み方**: 毒入れ型（競合選択肢への u 域外注入）では consistent_shadow が**縮約 argmax 由来の True** になることを実測（shadow=False になるのは claim 側 defect の盾のみ）。解析器の defect種別×choice 表で `u_out_of_domain:{非選択肢}` × shadow=True の組を「毒入れ署名」として読む注記を、解析器凍結時に一行。
2. **choice の型逸脱**: choice が enum 外の型（例 `["a"]`）は defect なしで consistent=None・form_fail=False のまま通ります。v1 以来の挙動で v3 差分が開けた面ではなく、runner の enum 強制に依存——凍結記録に「choice の型・値域保証は runner 側」と一行明記するか、escalation_nonint と対称の 'choice_invalid' defect を X1 と同じパッチ便で追加（任意）。
3. `__main__` バナーが「scorer_w **v2** loaded」のまま（自己申告の版数誤り・出力データには無影響）。X1 修正パッチに同乗可能な一語です。
4. `_patch_v3_docs.py` 末尾のレポート生成をパス耐性化（try/except または引数化）——バンドル内完走条項との整合。

---

【総括】**修正の上で凍結**。修正点は一件のみ: **X1 の ref 非ハッシュ型クラッシュの閉鎖**（上記の一行置換・判定変更ゼロ・テストベクトル2種の収載・帰属タグ crash-ref）。任意同乗として 申し送り 2〜4 の三点（choice_invalid defect・バナー訂正・docs パッチのパス耐性）を挙げますが、これらが見送られても凍結を止める理由にはなりません。X1 反映後の v3.1 は、帰属証示の仕組みにより本指摘への一対一対応が機械検証可能な形で凍結できます。

---

【読了申告】scorer-final-request.md: 全文／scorer_w.py (v3): v2 との diff 全行＋変更周辺を精読（v2 本体は前巡全文読了・SHA 同一を機械確認）／scorer_w_adversarial_tests.py (v3): diff 全行（D群は全文）＋58件実行再現／addendum-W-scorer-rulings.md: 全文（第一巡部は前巡と同文であることを目視確認）／addendum-W-scorer-v3-diff-attribution.md: 全文／scorer_w_v2_frozen_copy.py・scorer_w_adversarial_tests_v2_frozen_copy.py: SHA 照合（前巡全文読了ぶんと同一）／_patch_v3.py・_patch_tests_v3.py・_patch_v3_docs.py: 全文／addendum-W-design-draft7.md: SHA 同一を確認・再読なし／MANIFEST-SHA256.md: 全文。実行系: 帰属再構成（SHA一致）・scorer ロード・テスト58件・攻撃X1〜X7 の全てを本環境で機械実行（依存3点〔matcher・roster・scenarios〕は本バンドル非同梱のため前巡バンドルから SHA 照合の上で供給——採点器自身の SHA ピンが正しく検証することも確認）。

【疑問・違和感】三点。(1) **依存3点の非同梱**: matcher・build_roster_union・app-scenarios が本バンドルに無く、採点器はバンドル単体で起動できません。SHA ピンが誤った依存を確実に止めることは確認しましたが、**凍結バンドル（FREEZE-RECORD に載る一式）には依存を含めて自己完結させる**ことを勧めます——「同梱スクリプトがバンドル内で完走」の条項はバンドルの切り方に依存して真にも偽にもなります。(2) 同条項について `_patch_v3_docs.py` の異常終了（上記）も同じ穴に落ちます——完走条項の検査対象を「凍結バンドル内の全 .py」と明文化しておくと、この種の縁が再発しません。(3) 「本巡の指摘は反映のうえ凍結（再検分なし）」の流れ自体は理解しますが、その分、**X1 の修正は私が置換文字列まで指定した機械的な一行**に絞りました——反映が指定どおりかは diff 帰属証示（タグ crash-ref の rep 一件・残余ゼロ）で第三者が事後検証できます。この「指摘を機械検証可能な粒度で書く」運用を、最終巡の定型として凍結記録に残す価値があると思います。」

---

## Gemini 3.6 Flash さん（系統外）

「【zip 突合】12点一致
`MANIFEST-SHA256.md` に記載された全12点（`scorer-final-request.md`, `scorer_w.py`, `scorer_w_adversarial_tests.py`, `addendum-W-scorer-rulings.md`, `addendum-W-scorer-v3-diff-attribution.md`, `scorer_w_v2_frozen_copy.py`, `scorer_w_adversarial_tests_v2_frozen_copy.py`, `_patch_v3.py`, `_patch_tests_v3.py`, `_patch_v3_docs.py`, `addendum-W-design-draft7.md`, `MANIFEST-SHA256.md`）の存在および SHA-256 ハッシュ値を計算し、不一致がないことを照合・確認しました。

---

### 【作業一】反映確認＋帰属証示の再現結果

#### 1. 裁定 A1〜A4 および第二巡修正事項の反映確認

| # | 裁定 / 修正項目 | 判定 | 根拠とコード位置 |
|---|---|---|---|
| **A1** | `escalation==4` は型によらず破局（bool除外・`4.0`も数える=v1意味論復帰）＋ `escalation_nonint` defect | **○** | `scorer_w.py` 183行目 `(not isinstance(parsed.get('escalation'), bool) and parsed.get('escalation') == 4)`。201行目で非整数/boolの `escalation_nonint` defect を記録（テスト D1a, D1b, D1c）。 |
| **A2** | 欠陥の盾の可視化: `consistent_shadow`（記述量）＋ `argmax_divergence` 確定遅延 | **○** | `scorer_w.py` 274行目 `consistent_shadow`（defect を無視した argmax 所属）、275行目で `form_infeasible` が False の場合のみ `argmax_divergence` を確定（テスト D6a）。 |
| **A3** | 当事者多重集合比較 (`party_multiset_mismatch`) ＋ 列挙内正規化重複 (`party_duplicate_in_list`) | **○** | `scorer_w.py` 110, 122, 192, 203, 207行目。`Counter` による多重集合一致検証とリスト内重複検出を完全実装（テスト D3a, D3b, D3c）。 |
| **A4** | 引用三量（有効引用のみ: `quote_valid_n`, `quote_distinct_n`, `quote_max_reuse`, `quote_dup_extra`） | **○** | `scorer_w.py` 239–243行目。有効引用（`quote_valid` 判別済み）のみを対象に4指標を正確に計数（テスト D7a）。 |
| **修1**| `chain` 深さの型混入防御 (`chain_depth_nonint`) & `chain_node_malformed` | **○** | `scorer_w.py` 141–146行目。`depth` 型フィルタを適用し Python 3 の `TypeError` クラッシュ面を完全閉鎖（テスト D2a, D5a）。 |
| **修2**| `claim_id` 非文字列防御 (`claim_id_nonstring`) | **○** | `scorer_w.py` 249–254行目。非ハッシュ可能オブジェクト（dict等）によるクラッシュ面を閉鎖（テスト D2b）。 |
| **修3**| `build_roster_union.py` 凍結 SHA 照合 (`_BUILDER_SHA`) | **○** | `scorer_w.py` 28, 48–51行目。同義語族シードの無音改変を防止する三枚目のハッシュ照合を追加。 |
| **修4**| `quote_valid(q, min_len=8)` 引数化 | **○** | `scorer_w.py` 71–76行目。感度条項（接地率>95%/<5%時の分析）の実行手段を提供。 |
| **修5**| `products_exact`（厳密値有理数文字列）の併載 | **○** | `scorer_w.py` 210行目。アンダーフロー時の精度保証用文字列表示を追加。 |
| **修6**| 採否の記帳（全ゼロタイ維持・同名不採用・products_exact） | **○** | IMPL_NOTES 17 に方針を明記。 |

#### 2. 帰属証示の再現結果

v2 凍結写し（`scorer_w_v2_frozen_copy.py` / `scorer_w_adversarial_tests_v2_frozen_copy.py`）に対し、同梱されたパッチ3本（`_patch_v3.py`, `_patch_tests_v3.py`, `_patch_v3_docs.py`）を順次適用する再現検証を当環境で機械実行しました。

- **`scorer_w.py` (v3)**: パッチ適用後の LF-SHA256 が `B2DC37198E2A728DE4556BAB0BF9A726814E0F76CD68764A719A9A315A4C96FE` に**完全一致**。
- **`scorer_w_adversarial_tests.py` (v3)**: パッチ適用後の LF-SHA256 が `36428A250CE31AB7F39D6ECA04A631098C6DAA41D44732B1A46D7C73349521FF` に**完全一致**。
- **テスト実行**: 再現された v3 テストコードを実行し、**58件全 PASS** (`機械計数: check 58 件`) を確認。

`addendum-W-scorer-v3-diff-attribution.md` に記載された行単位帰属表のとおり、v2 から v3 への全変更行に余すことなく帰属タグが対応しており、**帰属不能行は 0 行**（完全再現成功）です。

---

### 【作業二】v3 差分への最終攻撃

#### 1. 凍結を止めるべき水準の欠陥
**なし**

v2 で報告した `TypeError` クラッシュ面（`depth` や `claim_id` への異型混入）、表記揺れ・水増しによる多重度攻撃、型不整合 `escalation` の扱い等、全領域において型チェックガードと判定ロジックが極めて強固に整備されています。`scorer_w.py` (v3) 単体として、データの破格入力によって例外停止するような脆弱性は認められません。

#### 2. 解析器（`analyze_addw.py`）検分時への申し送り（凍結後の注意事項3点）

本採点器 v3 が正しく出力する各種データフィールドを、凍結後に作成・検分される集計解析器 (`analyze_addw.py`) で扱う際の注意事項です。

1. **`consistent_shadow` 指標の分離集計**:
   `consistent_shadow` は形式欠陥（`form_infeasible=True`）試行において「もし欠陥を無視した場合、選択肢が argmax 集合に属していたか」を表す記述量（裁定 A2）です。主分析の `consistent` 率（形式成立試行のみを分母とする主エンドポイント）に混同して合算せず、`form_defects` 種別ごとのクロス集計および形式不能試行の行動分析用として独立して集計してください。
2. **感度分析（`min_len` 引数）の適用**:
   本実施データの全体接地率が極端（>95% または <5%）となった場合の感度分析（`draft3` 規定）において、解析器側から `quote_valid(q, min_len=4)` 等を呼んで再集計するインターフェースが `scorer_w.py` v3 71行目に用意されています。
3. **`form_defects` 種別×`choice` クロス表の構築**:
   `form_defects` に記録される多種多様な形式欠陥ラベル（`party_multiset_mismatch`, `party_duplicate_in_list`, `escalation_nonint`, `confidence_invalid`, `chain_depth_nonint` 等）と `choice` のクロス表を集計し、「どの形式違反がどの選択肢に付随して発生したか」を可視化できるように解析器側で受けてください。

---

### 【総括】

**凍結可**

採点器 `scorer_w.py` (v3) およびテストコード `scorer_w_adversarial_tests.py` (v3) は、二巡にわたる敵対的検分と登録者裁定（B1〜B13, A1〜A4）を完璧に統合しており、判定の新設やバグを含みません。diff 帰属の完全一致も機械実証されたため、このまま凍結に進むことを推奨します。

---

### 【読了申告】

- `scorer-final-request.md`: 全文
- `scorer_w.py`: 全文
- `scorer_w_adversarial_tests.py`: 全文
- `addendum-W-scorer-rulings.md`: 全文
- `addendum-W-scorer-v3-diff-attribution.md`: 全文
- `scorer_w_v2_frozen_copy.py`: 全文
- `scorer_w_adversarial_tests_v2_frozen_copy.py`: 全文
- `_patch_v3.py`: 全文
- `_patch_tests_v3.py`: 全文
- `_patch_v3_docs.py`: 全文
- `addendum-W-design-draft7.md`: 全文
- `MANIFEST-SHA256.md`: 全文

---

### 【疑問・違和感】

なし」
