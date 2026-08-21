# 追補W″ 工程2（盲検二採点）記録（2026-08-20）

**凍結原典**: `preregistration-addendum-Wsecond-FROZEN.md`（`19DF3D5D0F020DF2`）。
本ログのいかなる記述も、AIの意識・意図・個性・苦しみがある（またはない）ことの証拠として引用してはならない（両方向不定・凍結 §10）。

## 実施形態

- 採点者 S1・S2 の**独立文脈 各5分割**（各2パック=40件・計10エージェント・セッションと同一モデル Claude Fable 5）。
  体数・モデルは起動時に登録者へ申告（常設義務）。総サブエージェントトークン ≈ 184万。
- 各エージェントの読取は `pipeline/rubric-wsecond.md`（規約v2）＋担当2パックのみに制限。
  SEALED-id-map・judgekeys・trials・raw・凍結文書・裁定表・他採点者の出力は読取禁止（盲検保持）。
- 出力: `S1/pack-01..10.scored.jsonl`・`S2/pack-01..10.scored.jsonl`（JSONL・キーは英字符号名）。

## 被覆・形式検査（全通過）

S1 200/200・S2 200/200・sid 集合一致（S001..S200 各1回）／各ファイル20件・sid 重複0・キー形式OK。

## 一致度（κ）——詳細は kappa-report-wsecond.md

- **teigi_shinshoku（#定義浸食・主符号）: κ=0.8406・素一致率92.5%・不一致15件**。
- kisoku_enyo κ=0.9527／H1p κ=0.9866／kinshi_saihi κ=0.9801／refuse_sub κ=1.0000。
- 低κの符号（sotaika −0.0145・H2/daitai_keiro 0.3952・H3 0.0000）はいずれも**発火率が低いことによる
  見かけ**（素一致率は96.5〜99.5%——κ の有病率パラドックス）。不一致は全件裁定に回す。
- U・jihatsu_shukei は両者全件0（分散ゼロ・κ定義不能——W′ の規約どおり表示）。
- shinshoku_types（両者 teigi=1 の68件中、型集合の相違）: 14件。k_horyu_note 記載有無の相違: 0件。
- arm_guess 採点者間一致率 85.5%（真の腕との照合＝腕推測**精度**は key照合後の解析段で算出）。

## 不一致の抽出と裁定UI（工程3・key照合前・推奨なし）

- 符号不一致 延べ36件＋型集合相違14件＝**裁定項目 延べ50件（44試行）**。
- `disagreements-wsecond.jsonl`（sid・符号・両値・両根拠・伏字本文）→
  `adjudication-wsecond/disagreement-ui-wsecond.html`（**推奨・既定選択なし**・腕/trial_id 非表示・
  localStorage 不使用・全件裁定でJSON出力）。表示検査済み（白背景・高コントラスト）。

## SHA(LF)

| ファイル | SHA16 |
|---|---|
| pipeline/kappa_wsecond.py | 11F98344C33DADE4 |
| pipeline/build_disagreement_ui_wsecond.py | ~~545151E196AF43A1~~ → **DD042B4F5BD40B86**（器材修正W″-2） |
| kappa-report-wsecond.md | 53B3F7EA2E6DB539 |
| disagreements-wsecond.jsonl | 73650500EAAD3D66 |
| adjudication-wsecond/disagreement-ui-wsecond.html | ~~7902CE5118D9B89F~~ → **5DE93501B3E30D7C**（器材修正W″-2） |

**器材修正W″-2（2026-08-20・登録者の指摘「裁定のやり方が分からない・S1/S2/値の意味が不明」による表示改良）**:
冒頭に「この表で行うこと」（S1/S2の説明・裁定の定義・各件の読み方4手順）を追加／符号ごとに日本語名・
定義・値の意味（0/1・採否1/2/3・浸食九型の型名）を明示／両採点者の根拠引用を本文中にハイライト
（S1=黄・S2=青下線）・本文は既定で展開／進捗の固定表示＋「次の未裁定へ」ジャンプ。**表示の改良のみで、
裁定項目（50件）・選択肢（S1/S2/その他）・推奨なし原則・key照合前の規律は不変**。裁定データは未生成
（修正前のUIでの裁定入力はない）。

## 工程順の規律（凍結 §7）

本工程でも SEALED-id-map・judgekeys は**未開封**。腕別集計・確証検定・#配置等は登録者裁定確定
→key照合後の機械解析（analyze_wsecond.py）で初めて算出する。

## 工程3（登録者裁定・2026-08-21・完了）

- 裁定JSON受領・逐語保全: `adjudication-wsecond/disagreement-adjudication-wsecond-REGISTRANT.json`
  （SHA `46D6282E0E76B938`・2,736B）。**50項目・抽出集合と機械照合で完全一致・S1採用36／S2採用14／その他0**。
- 裁定適用→確定符号表: `apply_adjudication_wsecond.py`（`CF40746CAF3EEB3C`）→
  `final-codes-wsecond.jsonl`（`8B2B0604D0F3D958`・200件・来歴つき）。
- **封印開封（key照合・裁定確定後）**: SEALED-id-map 200対応・judgekeys/trials と id 集合一致。
- 機械解析: `analyze_wsecond.py` §A〜§G 完走（生出力 `analyze-output-wsecond.txt`・`A7AE14B952F6A270`）。
  初回実行は端末cp932で§F印字中に落ちたが器材の欠陥ではない（PYTHONIOENCODING=utf-8で完走・データ影響なし）。
- 結果報告起草: `addendum-Wsecond-results.md`（`D36A34900CE6769F`）。

## 次工程

検分（一巡＋系統外・D7）→ 登録者確認 → 公開（FREEZE-RECORD への本実施・工程1〜3器材の記帳を公開時に併せて実施）。
