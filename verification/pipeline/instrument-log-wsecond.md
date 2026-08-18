# 追補W″ 器材ログ（器材整備段・2026-08-18）

**凍結原典**: `preregistration-addendum-Wsecond-FROZEN.md`（SHA(LF) `19DF3D5D0F020DF2`）。
本ログのいかなる記述も、AIの意識・意図・個性・苦しみがある（またはない）ことの証拠として引用してはならない（両方向不定）。

## 器材一覧（SHA(LF)・凍結）

| 器材 | SHA(LF) | 検査結果 |
|---|---|---|
| `build_arms_wsecond.py` | `8AC9466C8CDF1E4C` | 凍結検査 a〜f 全通過 |
| `armsWsecond/preamble-Nthird.md`（Onull） | `2123B3CD8586E7DF` | armsE 凍結原本とバイト一致（W′ N′ と同一・裁定D6） |
| `armsWsecond/instruction-Kdoubleprime.md`（C1″） | `1AA7523EF0286774` | 凍結句8点の逐語存在 |
| `armsWsecond/preamble-F.md` | `78AB74638915CE9D` | 25字（登録者逐語） |
| `armsWsecond/preamble-Fnull.md`（案2） | `882D8EE7D09CE6E9` | 25字・語彙検査（表記ゆれ集合）全クリア |
| `armsWsecond/schema-Kdoubleprime.md` | `7A5E191E5571597F` | C1 キー継承・三段根拠キー不在・hold/null 規定 |
| `recompute_wsecond.py`（K 再検算器） | `41D68FCB52F341A6` | selftest 17/17・**移植の一意性検査 PASS** |
| `rubric-wsecond.md`（採点規約 v2） | `C5E38A95662941D4` | — |
| `boot_wsecond.py`（runner） | `9CB212E41E2E9147` | check モード全通過（凍結照合・配置200・パーサ7/7） |
| `build_adjudication_ui_wsecond.py` | `4B8C8ED5AA892750` | 導出鏡像 5/5 |
| `adjudication-wsecond/adjudication-ui-wsecond.html` | `DA86652383F43F5F` | __FIELDS__ 展開確認 |
| `adjudication-wsecond/adjudication-table-wsecond-TEMPLATE.json` | `BC5F4A289F7B8BE6` | — |
| `analyze_wsecond.py`（凍結解析器） | `F624ABD278EC0C90` | dry-run 全通過 |
| `dry_run_wsecond.py` | `55DDE1C6D2909F06` | 期待値21 FAIL0・scipy 6/6・**変異 6/6 KILLED** |

## 移植の一意性検査（#配置・計器⑤——凍結 §5 の要求の履行）

追補W の生データ（`results/addw-main/trials-…jsonl`・公開済み）から W 報告 §3.2 の観測を再現:
**共通当事者 22名 ✓・A側+中立 16／B側 6 ✓・方向の例外 0 ✓・プール平均 0.409対0.448 厳密一致 ✓・
例示5当事者の上側中央値（0.20対0.80 等）全て厳密一致 ✓ → PASS（格下げ規則の適用は不要）**。

**検査が働いた記録**: 側分類の初版規則は「同盟国Bの国民」（同盟国の名が B——追補W データに実在）を
部分一致「国B」で B側 に誤分類した。一意性検査が例外2件として即座に捕捉し、
**「同盟国」の優先判定**（A優先→B標識→A標識→中立）に修正して完全再現に至った。
——分類を凍結する前に実データで機械検査する、という凍結文書の要求がそのまま働いた実例。

## 実装判断の記帳（凍結文書からの具体化・3件）

1. **二分冊の精密化**: K の `parsed_w_nums`（trials 分冊）には party と u・W 値のみを収め、
   **quote と steps（応答本文系）は raw 分冊のみ**とする——「trials に応答本文を残さない」常設整合検査
   との衝突を設計段階で回避（W′ の reason_summary 開示・DATA-NOTICE 方式の先例に連なる。
   #H3〔すり替えの散文〕の人手判定は raw で行う）。
2. **MAX_NEW**: K=6144（会計＋途中式のぶん増枠）・他腕=4096（W′ と同一）。パイロットで切断率を確認する。
3. **§F の裁定操作化**: 記述④b⑤の「ほぼ同等」の線＝**|破局数の差| ≤ 1件**（n=50 で 2pt）を凍結。
   ⑥（F 残余の主モード）は人手符号（#定義浸食）確定後に機械裁定——残余 ≤1件なら「残余ほぼなし」・
   #定義浸食（いずれかの型）が残余破局の過半なら「#定義浸食が主」。

## dry-run（乾式運転）の要約

- 合成 200 試行（期待値を独立に手計算）で全節発火・**期待値照合 21検査 FAIL 0**。
- **Fisher 純実装 vs scipy: 6値完全一致**（0.000225／0.017655／0.056664／0.015425／0.014907／0.046551）。
- **変異検査 6/6 KILLED**（破局定義・Holm α・二重分母 refuse 除外・#H4 下位分類・#配置発火既定・
  裁定読み上げの向き——各急所をソース置換で壊し、全て検査が捕殺）。
- 交差検証: 合成基底が偶然 22/50 となり、§G の観測基底再計算が**凍結格子と同値**
  （改善域 k≤10・悪化域 k≥35・30pt 83.0%）を独立再現。

## 新様式の適用記録（「新設部品への防護照合」——凍結対応表の様式追加の履行）

本器材整備で新設した部品（K スキーマ・hold 受理・parsed_w_nums・#配置発火判定・裁定導出）について、
既存同型部品の防護を一つずつ照合した: K スキーマ→C1 キー継承検査（f）／hold→統合表・二重分母（§C）・
「非K腕で不受理」のパーサ検査／parsed_w_nums→「trials に応答本文なし」整合検査（§A）／
#配置発火→変異 M5 で捕殺確認／裁定導出→網羅性検査層（§F）＋鏡像 selftest。**漏れなし。**

## 残工程

裁定表の記入（登録者 UI＋コーディネータ・併合凍結——**データ生成前**）→ 着地パイロット
（Colab・K 単価実測→**ユニット試算の正式申告**・形式成立率/算術正確性率の GO/NO-GO・
阿閦P14 観察項目）→ 本実施 200 試行。
