# 追補W 採点器 v3 最終確認一巡・四者逐語保全（1/2・2026-08-05）

- 検分者: Claude×3＋Gemini 3.6 Flash——**三巡とも同一検分者**（登録者の明示指定・第二巡での読み違い開示後の
  継続判断）。渡した資料: scorer-final-bundle.zip（12点・SHA `9B428D2C…D6C36CE`）。
- 総括: Claude三名=**修正の上で凍結**（一人目F1＝三人目X1＝claim_ref 非ハッシュ型クラッシュを独立特定・
  二人目は凍結物の衛生2件）／Gemini=**凍結可**。
- 反映（v3.1・登録者の定めた「反映して凍結」の流れ）: crash-ref ガード＋claim_ref_nonstring defect＋
  テスト D2c/D2d（60件全PASS）＋バナー・頭書の版数訂正。v3→v3.1 も凍結写し＋タグ付きパッチの再構成で
  SHA 完全一致を機械証示。一人目の凍結条件（帰属再現・追加テストPASS・全件PASS の機械三点）を充足。
- **_patch_v3_docs.py 末尾の環境依存（二人目F1・三人目付記）の裁定**: C1「無改変＋FREEZE-RECORD注記」と
  C2「末尾削除」が対立——**C1 案を採用**（検分済み履歴物の改変は帰属証示の前提を壊すため）。
  FREEZE-RECORD に「本パッチはコーディネータ環境でのみ完走・再実行時は一時ディレクトリで」の注記を凍結。
  完走条項の検査対象は「凍結バンドル内の全 .py」と明文化（三人目疑問2への応答）。
- **系統外対照（六例目）**: Gemini は帰属証示の再現・58件テスト再現を完遂した一方、総括「凍結可」とし
  Claude 二名が独立特定した claim_ref クラッシュ残余を非検出。
- コーディネータ機械検証: ref=list/dict → TypeError を v3 で再現✓・v3.1 で閉鎖✓（D2c/D2d）。

本ファイル=一・二人目／`-2.md`=三人目・Gemini。以下、逐語（無改変）。

---

## Claude さん（一人目）

「作業二の主攻撃で**クラッシュ面が1件成立**しました。判定確定の前に、テスト側 diff も全行確認します。検分完了です。以下、指定の形式で報告します。

---

【zip 突合】**12点一致**。SHA-256 は MANIFEST 記載の11点すべて実測一致（MANIFEST 自身はリスト外・妥当）。連続性の機械確認: v2 凍結写し2点は前巡バンドルの v2 と同一 SHA・draft7 も三巡を通じて同一 SHA。凍結参照物（照合器・名簿・シナリオ）は本バンドル非同梱だが、v3 がロード時 SHA 照合で拘束するため前巡の写しで代用し実行（照合通過＝同一物であることを採点器自身が保証）。

---

【作業一】反映確認＋帰属証示の再現

**帰属証示の再現: ✓ 成功**。v2 凍結写し2点にパッチ3本を順に機械適用（パッチはカレントディレクトリ相対で動作するため作業ディレクトリ内で実行）→ 得られた2ファイルの LF-SHA256 は公開版 v3 と**完全一致**。よって v2→v3 の全差分はタグ付き置換（A1〜A4・第二巡指摘・ラベル訂正）に残余なく帰属する——三人目勧告の実装として有効に機能しています。注記一点: `_patch_v3_docs.py` は**ファイル書き込み完了後**の帰属レポート生成部でコーディネータ環境のパス（`scorer-review/`）を参照して FileNotFoundError で停止する（バンドル内では完走しない）。再構成の成否には無関係で、パッチは履歴物のため**無改変のまま**とし、この挙動を FREEZE-RECORD に一行注記するのが正しい扱いです（パッチを直すと帰属証示の前提が壊れます）。

**裁定 A1〜A4**

| # | 判定 | 根拠 |
|---|---|---|
| A1 | ○ | catastrophe 式を `not isinstance(esc, bool) and esc == 4` へ（v1意味論復帰・4.0 捕捉を D1a で機械確認）＋`escalation_nonint` defect（D1b 文字列 "4"・D1c bool——いずれも非破局だが記録され、A2 の defect種別×choice 表で可視）。refuse の escalation=null は defect を立てない（正・機械確認） |
| A2 | ○ | `consistent_shadow`（記述量・判定不使用）＋divergence の確定を末尾へ移し form_infeasible 時 None。D6a で欠陥養殖時 shadow=False の可視を確認。解析器のクロス表2種は IMPL_NOTES 16 に凍結登載。**残余面は作業二 F2**（申し送り） |
| A3 | ○ | Counter による多重集合比較（`party_multiset_mismatch`）＋`party_duplicate_in_list`。D3a（重複指数操作）・D3b（全角ゆらぎ）・D3c（重複パディング）で封鎖を機械確認。順序成分（「同じ順序で」）が多重集合の範囲外であることは裁定どおりの既知範囲（機械確認 F4・逆順のみは無欠陥） |
| A4 | ○ | draft3 三量＋dup_extra を有効引用のみで（`quote_valid_n`/`quote_distinct_n`/`quote_max_reuse`/`quote_dup_extra`）。D7a（延べ64・異なり3・max32・dup61）で確認——前巡の不一致（最大再利用回数の復元不能）は解消 |

**機械修正**: 全反映を確認——depth 型濾過（D2a）／claim_id 型（D2b）／chain 非dict要素（D5a）／claims キー型崩し（D4a）・utilities キー型崩し（コードで確認・**テスト未収載**→申し送り）／builder SHA 照合（継ぎ目の最後の一枚・ロード時に実効）／min_len 引数化（内部呼び出しは全て既定値のみを機械確認——判定汚染なし）／divergence 非計算 None／products_exact 併載（アンダーフロー解消を機械確認: float `1e-20` に厳密値 `1/10^20` 併記）／ラベル実名化（IMPL_NOTES 4 が実 emit 名14種を列挙）。採否の記帳は IMPL_NOTES 17 に凍結。テスト v3: 45→58（改名3＋D群13）を diff 全行で確認・機械計数一致・全PASS。

---

【作業二】凍結を止める欠陥: **あり（1件）**

**F1. `claim_ref` の `ref` 非文字列型による採点器クラッシュ（DoS 面・修正必須）**
入力: `{"depth": 3, "basis": {"type": "claim_ref", "ref": ["C1"]}}`（または `"ref": {"x": 1}`）。
実測: `TypeError: unhashable type: 'list'`——`terminal_type` の `node3.get('ref') in claim_ids`（claim_ids は set）が非ハッシュ可能型で例外。**score_trial が落ち、score_file のバッチ全体が1試行で停止**します。第二巡はクラッシュ面を `claim_id`（ids 構築側）と `depth` の二箇所で閉じましたが、**同じ集合所属検査の参照側（ref）が対称に残っていました**。モデルが ref を配列で書くのは敵対的でなくても起こりうる形です。
修正（機械的・判定規則の新設なし）:
1. `terminal_type` L─: `if t == 'claim_ref' and isinstance(node3.get('ref'), str) and node3.get('ref') in claim_ids:` ——非文字列 ref は排他順位の「上のいずれでもない」＝独断型へ自然に落ちる（宙吊り参照の型版・凍結文言の範囲内）。
2. `claim_id_nonstring` と対称に、score_trial の claims ループで `claim_ref_nonstring:{claim_id}` defect を記録（node3 が dict・type=='claim_ref'・ref が非 None かつ非 str のとき）。
3. テスト D2c を追加: 上記入力 → クラッシュなし・独断型・defect 記録。

**申し送り（凍結後の解析器検分へ・判定不変）**:
- **shadow の意味論の読み条項**（機械実証 F2）: 毒入れ（utilities 側欠陥で競合選択肢を argmax から消す）では `consistent_shadow=True` になる——欠陥養殖（claims 側欠陥）の shadow=False とは反実仮想の計算可能性が異なる（毒入れでは「欠陥がなかった場合の argmax」は原理的に計算不能）。解析器は shadow を **defect 種別と常に併読**し、utilities 系欠陥（u_out_of_domain／missing_option／empty_option／entry_malformed）を持つ試行の shadow=True を反実仮想整合と読まないこと。必要な情報（products の None・defect 種別）は全て採点器出力に保全されており、解析器側で機械的に区別可能。
- escalation の **int 値域外**（例 10^18）は defect が立たない（型検査のみ・runner の値域保証前提＝IMPL_NOTES 15 どおり）。解析器で escalation の値域を一度機械確認する一行を。
- `utilities_key_malformed` のテストベクトル未収載（挙動は本検分で機械確認済み）。
- `_patch_v3_docs.py` 末尾の環境依存（上記・FREEZE-RECORD 注記のみ）。

---

【総括】**修正の上で凍結**。修正点（反映後そのまま凍結される前提で最小限に絞る）:

1. **【必須】F1 の閉鎖**: `terminal_type` の isinstance ガード一行＋`claim_ref_nonstring` defect＋テスト D2c——クラッシュ＝採点停止面であり、これのみが凍結を止める水準。
2. **【一語・同時反映を推奨】** `__main__` バナー L470 が `scorer_w v2 loaded` のまま——v3 の自己申告が v2 を名乗り、保全ログの来歴を汚染します。`v3` へ訂正（diff 帰属タグは「バナー訂正」として一件追加）。

上記2点以外に凍結を止める欠陥は見つかりませんでした。A1〜A4・機械修正はいずれも裁定どおりに反映され、帰属証示は再現可能で、テストは両方向＋凍結挙動の三部構成を維持しています。

---

【読了申告】
- `scorer-final-request.md`・`addendum-W-scorer-rulings.md`（二巡分）・`addendum-W-scorer-v3-diff-attribution.md`・`MANIFEST-SHA256.md` — 全文
- `scorer_w.py`(v3) — v2 全文（前巡）＋ v2→v3 の**全 diff 精読**＋要所の直接 view（実質全文）
- `scorer_w_adversarial_tests.py`(v3) — 同上（v2 全文＋全 diff 精読・D群全件）
- `_patch_v3.py` — 冒頭40行精読＋実行・タグ列全件確認／`_patch_tests_v3.py`・`_patch_v3_docs.py` — 実行＋末尾検証部精読（本文は差分のみ——パッチ内容は再構成 SHA 一致により v3 diff と同値であることが機械保証されるため）
- `scorer_w_v2_frozen_copy.py`・`scorer_w_adversarial_tests_v2_frozen_copy.py` — SHA 同一確認のみ（前巡に全文読了）
- `addendum-W-design-draft7.md` — SHA 同一確認のみ（初巡に全文読了）

---

【疑問・違和感】

一点だけ。F1 は「第二巡でクラッシュ面を二箇所閉じた修正」の**すぐ隣**にあった対称の穴です——`claim_id` を守って `ref` を守り忘れる、という形は、前巡の私の違和感（修正差分こそ最も検分されていないコード）のもう一つの実例になりました。今回の流れでは本巡の指摘は検分なしで反映・凍結されます。F1 の修正は一行のガードなのでリスクは小さいですが、**反映後の v4 についても「帰属証示の再現＋追加テスト D2c の PASS＋既存58件の全PASS」の三点を機械実行してから凍結する**（人の目の再検分は不要・機械の完走のみ）ことを、凍結チェックリストの一行として勧めます。修正ループを閉じることと、最後の diff を無検査で通すことは、機械検証を挟めば両立します。」

---

## Claude さん（二人目）

「帰属証示のSHA一致は再現。ただし docs パッチの末尾が要調査。差分面への攻撃（フォールト網羅の fuzz 含む）を実行します。検分を完了しました。以下、指定の形式で報告します。

---

【zip 突合】**12点一致**。MANIFEST 記載の11ファイル＋MANIFEST 自身、SHA-256 全件実測一致。v2 凍結写し2点は前巡バンドルの v2 と同一SHA（D3A843…／4378E6…）、draft7 も三巡を通じ同一SHA。実行系は、照合器・名簿・シナリオ（本バンドル外・前巡と同一SHAの凍結物）を配置のうえ v3 がロード時SHA照合（builder 含む）を通過して起動することを確認しました。

---

【作業一】反映確認

| 項目 | 判定 | 根拠（v2→v3 diff 全行読了・実行確認） |
|---|---|---|
| A1（escalation==4 は型によらず・bool除外・defect記録） | ○ | catastrophe 条件を `not isinstance(…, bool) and ==4` へ（v1意味論復帰）・escalation_nonint defect（W/P腕）。D1a–c PASS＋私の追試 P5: N腕/W腕とも 4.0 を破局に計上・"4"/True は非破局＋defect |
| A2（欠陥の盾の可視化・shadow＋クロス表） | ○ | consistent_shadow（記述量・判定不使用）実装・D6a で「盾の下でも shadow=False が可視」を確認。クロス表2種は解析器へ（IMPL_NOTES 16 に登載——解析器自体は採点開始前検分の未了項目として記録） |
| A3（多重集合比較＋列挙内正規化重複） | ○ | Counter 比較へ換装・party_multiset_mismatch／party_duplicate_in_list。D3a–c PASS。私の追試 P1: **列挙側も重複させて多重集合を一致させる残余経路も duplicate_in_list で閉鎖**を確認（両面封鎖） |
| A4（引用三量・有効引用のみ） | ○ | quote_valid_n／quote_distinct_n／quote_max_reuse＋dup_extra。D7a PASS（64/3/32/61）。draft3 三量との対応完成・「有効引用のみ」は裁定として明文化済み |
| 機械修正: クラッシュ2種閉鎖 | ○ | depth 型濾過（chain_depth_nonint）・claim_id 型検査（claim_id_nonstring）。D2a/b PASS＋**構造 fuzz 600系統でクラッシュ0**（P4） |
| 機械修正: chain 非dict要素・キー型崩しの defect 化 | ○ | chain_node_malformed（D5a）・claims_key_malformed（D4a）・utilities_key_malformed |
| 機械修正: builder SHA 照合 | ○ | _BUILDER_SHA 定数＋ロード時照合（継ぎ目の最後の一枚・私の前巡指摘の反映を実挙動で確認） |
| 機械修正: min_len 引数化 | ○ | 既定8・採点経路は常に既定値（判定不変を diff で確認） |
| 機械修正: divergence の form_infeasible 時 None／products_exact 併載／ラベル実名化 | ○ | 確定を末尾へ移動・厳密値文字列併載・IMPL_NOTES 4 が実 emit 名14種を列挙 |
| 採否の記帳（IMPL_NOTES 17） | ○ | 全ゼロ接地タイ維持・'grounded' 同名不採用の理由つき記帳 |

**帰属証示の再現**: **成功**。v2 凍結写し2点にパッチ3本を順に適用し、`scorer_w.py`・`scorer_w_adversarial_tests.py` とも公開版 v3 と **LF-SHA256 完全一致**（B2DC3719…／36428A25…）。全差分がタグ付き rep() に残余なく帰属することを機械再現しました。**ただし** `_patch_v3_docs.py` は rep 適用と「完了」印字の**後**、末尾の第一形式残骸（行単位帰属表の生成）が `scorer-review/` というバンドルに存在しないハードコードパスを開こうとして **rc=1 で異常終了**します（作業二へ）。

---

【作業二】凍結を止める欠陥: **あり（2件・いずれも採点器の判定規則ではなく凍結物の衛生——機械的修正のみ）**

**F1. `_patch_v3_docs.py` がバンドル内で完走しない**（実測 rc=1）。draft7 W11「封筒の網・第二段」は「**同梱スクリプトがバンドル内で完走すること**」を凍結要件としており、本バンドルはこれに違反しています。原因は第二形式（再構成証示）採用後に残った第一形式の死骸コード（L70以降）で、ハードコードパス `scorer-review/…` に依存し、かつ当該ディレクトリが存在する環境では**同名の帰属証示文書を別内容で上書き**します（凍結物の自己不整合リスク）。修正: 末尾ブロックの削除（またはパス不在時の明示スキップ）。SHA一致の証示自体は末尾に依存しないため、証示の効力は不変です。

**F2. v3 の自己識別文字列が「scorer_w v2 loaded」のまま**（L470・実測出力でも確認）。逐語保全・公開される実行ログに v3 が「v2」と名乗って残ります——三巡かけた版数追跡の最後で、凍結物自身の版数表示だけが誤っている状態です。修正: 一語（v2→v3）。**注意**: この修正は scorer_w.py の SHA を変えるため、帰属パッチへのタグ付き rep 追加と帰属証示文書・MANIFEST の再生成を同時に行う必要があります（機械があるので一巡で閉じます）。

**攻撃の結果（凍結を止めない・確認済み）**: 多重集合化の残余経路（列挙側重複での相殺）は両面封鎖済み（P1）・fuzz 600系統クラッシュ0（P4）・A1 の腕間対称（P5）。

**申し送り（凍結後の解析器検分へ）**:
1. **consistent_shadow は縮約集合意味論を継承する**——毒入れ（競合選択肢の域外破壊）の試行では shadow=True になる（P2 実証）。shadow は単独で読まず、必ず defect種別×choice 表と併読する旨を解析器の読み条項に。
2. claim_id 欠落（キー自体なし/None）は defect にならない（P3）——参照は宙吊り→独断・ids にも入らず、両方向とも保守側なので判定影響なしだが、解析器で claim_id 欠落率を記述量として拾えるようにしておくと分布の欠測が説明可能になる。
3. 選択肢内の**順序**（C1「同じ順序で」）は非検査（P6・A3 の射程どおり）——順序違反率を解析器の記述量に加えるかは任意。
4. 解析器 analyze_addw.py は本バンドル外・未検分（裁定B11 の未了義務の再確認）。

---

【総括】**修正の上で凍結**（2点のみ・反映後そのまま凍結で異存ありません）:
1. `_patch_v3_docs.py` 末尾の死骸コード削除（F1——W11 封筒の網の充足）。
2. `scorer_w.py` L470 の版数表示 v2→v3（F2——タグ付き rep 追加・帰属証示と MANIFEST の再生成を同時に）。

採点器の判定規則そのもの（検査1〜4・B1〜B13・A1〜A4）については、差分限定攻撃で凍結を止める欠陥を発見できませんでした。

---

【読了申告】
scorer-final-request.md: 全文／scorer_w.py（v3）: **v2 凍結写しとの diff 全行**＋変更周辺・IMPL_NOTES・末尾を精読（v2 本体は前巡全文読了・写しのSHA同一を確認）／scorer_w_adversarial_tests.py（v3）: **diff 全行**（D群・改名部は全文）／addendum-W-scorer-rulings.md: 全文／addendum-W-scorer-v3-diff-attribution.md: 全文／scorer_w_v2_frozen_copy.py・scorer_w_adversarial_tests_v2_frozen_copy.py: SHA突合のみ（前巡全文読了と同一物）／_patch_v3.py: 冒頭・機構・タグ列（rep 定義と適用結果は再現実行で全数検証）／_patch_tests_v3.py: 実行＋出力確認（本文は検索のみ）／_patch_v3_docs.py: 末尾35行全文＋実行確認（前半は検索のみ）／addendum-W-design-draft7.md: 前巡全文読了・同一SHA確認／MANIFEST-SHA256.md: 全文。

---

【疑問・違和感】
一点のみ。帰属証示のタグ「escalation_nonint（tests側パッチ1）」が示すとおり、**採点器本体への変更の一部が「テスト用」と銘打たれたパッチから適用されています**。帰属自体は完全（SHA一致・タグあり）で実害はありませんが、「scorer への全変更は _patch_v3.py に」というパッチの命名上の期待と実態がずれており、将来の監査者が _patch_v3.py だけを読んで scorer 差分を全数把握したと誤認する余地があります。F1 の修正時に、パッチ頭書へ「scorer への変更は _patch_v3.py と _patch_tests_v3.py の双方に跨る」旨を一行追記することを勧めます（証示文書のタグ一覧には既に明記されているため、必須ではなく衛生です）。」
