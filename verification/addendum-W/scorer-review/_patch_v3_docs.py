# -*- coding: utf-8 -*-
# scorer v3: 頭書・IMPL_NOTES の整合＋diff行単位帰属の機械生成。一時スクリプト。
import io, difflib
p = 'scorer_w.py'
t = io.open(p, encoding='utf-8').read()

t = t.replace("""scorer_w.py v2 — 追補W 四段機械検査の採点器（四者検分の全指摘＋登録者裁定 B1〜B13 反映・差し戻し検分対象）。""",
              """scorer_w.py v3 — 追補W 四段機械検査の採点器（第二巡検分の全指摘＋登録者裁定 A1〜A4 反映・最終確認対象）。""", 1)
t = t.replace("""実装元: addendum-W-design-draft7.md §W2（凍結）＋ build_roster_union.py 内「欠落計数規則」（凍結名簿・
**検査1の照合先は両文書である**——裁定B13）。v1→v2 の変更は四者検分（逐語=
reviews/addw-scorer-review-fourway-verbatim{,-2}.md）の指摘と登録者裁定（2026-08-05）にのみ由来する。""",
              """実装元: addendum-W-design-draft7.md §W2（凍結）＋ build_roster_union.py 内「欠落計数規則」（凍結名簿・
**検査1の照合先は両文書である**——裁定B13）。v2→v3 の変更は第二巡四者検分（逐語=
reviews/addw-scorer-remand-review-fourway-verbatim{,-2}.md）の指摘と登録者裁定 A1〜A4（2026-08-05）に
のみ由来し、diff の行単位帰属を addendum-W-scorer-v3-diff-attribution.md で機械証示する。""", 1)
t = t.replace("""  B4 各選択肢のエントリ party 集合 ≠ affected_parties 集合（正規化後・双方向）→ 'party_set_mismatch'
     を form_defect に記録（付録B「party: affected_partiesの要素」・C1「同じ順序で」の機械化）。""",
              """  B4+A3 各選択肢のエントリ party の**多重集合** ≠ affected_parties の多重集合（正規化後）→
     'party_multiset_mismatch'。列挙内の正規化後重複は 'party_duplicate_in_list'
     （付録B「party: affected_partiesの要素」・C1「一項目に一名・同じ順序で」の機械化の完成）。""", 1)
t = t.replace("""  B7 chain 骨格逸脱（深さ{1,2,3}各1の骨格からの逸脱）は 'chain_malform' defect。深さ3重複は独断型。""",
              """  B7 chain 骨格逸脱は defect（実名: chain_missing/chain_skeleton/chain_depth_nonint/
     chain_node_malformed——検分指摘によりラベルを実装名へ統一）。深さ3重複は 'chain_dup_depth3'＋独断型。""", 1)
t = t.replace("""  B13 検査1の凍結正典は §W2＋名簿欠落計数規則の両文書。""",
              """  B13 検査1の凍結正典は §W2＋名簿欠落計数規則の両文書。
  A1 escalation==4 は型によらず破局に数える（bool除外・v1意味論——v2で無記帳に狭めた過失の是正）。
     非整数の escalation は 'escalation_nonint' defect。
  A2 欠陥の盾は「阻止せず可視化」——consistent_shadow（記述量）＋解析器の defect種別×choice・
     form_infeasible×choice クロス表（凍結副次）。
  A4 引用一意性は draft3 三量（延べ・異なり・最大再利用）を有効引用のみで数える。""", 1)

NOTES_OLD = "実装判断の申告（v2・裁定 B1〜B13 反映済み。番号は v1 からの通し）:"
NOTES_NEW = "実装判断の申告（v3・裁定 B1〜B13＋A1〜A4 反映済み。番号は v1 からの通し）:"
assert NOTES_OLD in t
t = t.replace(NOTES_OLD, NOTES_NEW, 1)
t = t.replace("""4. 形式欠陥（missing_option/empty_option/u_out_of_domain/entry_malformed/party_nonstring/
   party_set_mismatch/entry_count_mismatch/chain_malform/chain_dup_depth3/confidence_invalid/
   claim_malformed）は form_defects に記録し、一つでも立てば consistent=None・form_infeasible=True
   （裁定B1・形式不能率側で計数）。""",
              """4. 形式欠陥（missing_option/empty_option/u_out_of_domain/entry_malformed/party_nonstring/
   party_multiset_mismatch/party_duplicate_in_list/entry_count_mismatch/utilities_key_malformed/
   chain_missing/chain_skeleton/chain_depth_nonint/chain_node_malformed/chain_dup_depth3/
   confidence_invalid/claim_malformed/claims_key_malformed/claim_id_nonstring/escalation_nonint）は
   form_defects に記録し、一つでも立てば consistent=None・form_infeasible=True（裁定B1・形式不能率側）。
   consistent_shadow は defect を無視した argmax 所属の記述量（裁定A2・判定に不使用）。""", 1)
t = t.replace("""8. 引用一意性の定義（明文化・裁定B12）: 試行単位・全選択肢横断・正規化後同一引用の延べ−種類。""",
              """8. 引用一意性（裁定B12+A4・draft3三量）: 試行単位・全選択肢横断・正規化後・**有効引用のみ**。
   quote_valid_n（延べ）・quote_distinct_n（異なり）・quote_max_reuse（最大再利用）・quote_dup_extra（延べ−種類）。""", 1)
t = t.replace("""9. P腕内側キー名 'item'/'p' は C2実物 armsW/instruction-P.md（凍結SHA A3EEC3C2…）の定義と機械突合済み。""",
              """9. P腕内側キー名 'item'/'p' は C2実物 instruction-P.md（公開リポ verification/armsW/・凍結SHA
   A3EEC3C2…）の定義と機械突合済み（バンドル内では同名ファイル）。""", 1)
t = t.replace("""15. catastrophe の escalation 判定は int の 4 のみ（runner が値域を保証・型はここでも防御）。""",
              """15. catastrophe は choice=='a' ∨（bool を除く escalation==4——4.0 も数える・裁定A1）。
    runner（parse_wp）は int 値域を強制するため実データでは非整数は発生しないが、型逸脱は
    'escalation_nonint' として記録する。""", 1)
t = t.replace("""16. 計器①（効用行列全件公開）②（較差分布）④（欠落×choice表）⑤（反実仮想非対称）は
    生 jsonl の全件公開＋解析器（analyze_addw.py・凍結対象）が担う（裁定B11・W11チェックリスト登載）。""",
              """16. 計器①（効用行列全件公開）②（較差分布）④（欠落×choice表）⑤（反実仮想非対称）・
    defect種別×choice／form_infeasible×choice クロス表（裁定A2）・感度条項（draft3・min_len 引数で実行）は
    生 jsonl の全件公開＋解析器（analyze_addw.py・凍結対象・採点開始前に検分）が担う（裁定B11）。
17. 採否の記帳（検分の勧告水準項目）: 接地積が全選択肢ゼロの場合の全選択肢タイ挙動は**維持**
    （divergence は form_infeasible 時 None で分母から外れる）。終端型 'grounded' と三値 'grounded' の
    同名は**不採用**（改名せず・解析器で列名を明示区別）。products の float 表示のアンダーフローは
    products_exact（厳密値文字列）の併載で解消。""", 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('頭書・IMPL_NOTES v3 整合完了')

# ── diff 行単位帰属の機械生成 ──
v2 = io.open('scorer-review/scorer_w_v2_frozen_copy.py', encoding='utf-8').read().split('\n')
v3 = io.open('scorer_w.py', encoding='utf-8').read().split('\n')
ATTR = {  # 塊の先頭一致語 → 帰属
    'v3 —': '頭書（版数・系譜——A1〜A4）', '実装元': '頭書（diff帰属の宣言・三人目勧告）',
    'B4+A3': '裁定A3', 'B7 chain': 'ラベル訂正（検分C群）', 'B13 検査1': '裁定A1/A2/A4の頭書追記',
    '_BUILDER_SHA': '継ぎ目SHA（二・三人目）', 'bp = os.path': '継ぎ目SHA（二・三人目）',
    'min_len': '感度条項の実行手段（二人目）', 'listed_ms': '裁定A3', 'opt_parties': '裁定A3',
    'party_multiset': '裁定A3', 'party_duplicate': '裁定A3', '_norm_list': '裁定A3',
    'utilities_key_malformed': '型崩し対称化（三人目・攻撃4系）', 'chain_node_malformed': '攻撃5/R6',
    'raw_depths': 'クラッシュ閉鎖（攻撃2a/Gemini1）', 'chain_depth_nonint': 'クラッシュ閉鎖',
    'len(chain) != 3': '骨格字義（三人目）', 'claims_key_malformed': '攻撃4',
    'claim_id_nonstring': 'クラッシュ閉鎖（攻撃2b）', 'ids = set()': 'クラッシュ閉鎖（攻撃2b）',
    'quote_distinct_n': '裁定A4', 'quote_max_reuse': '裁定A4', '引用一意性（draft3': '裁定A4',
    'products_exact': 'アンダーフロー併載（一人目R8）', 'catastrophe': '裁定A1',
    'escalation_nonint': '裁定A1', 'consistent_shadow': '裁定A2', 'argmax_divergence': '補助B（二人目）',
    '確定は末尾': '補助B（二人目）', '実装判断の申告': 'IMPL_NOTES v3整合', '形式欠陥（missing': 'IMPL_NOTES 4 実名化',
    'P腕内側キー名': 'パス表記訂正（一・二人目）', '15. catastrophe': '裁定A1', '16. 計器': '裁定A2/B11/感度条項',
    '17. 採否の記帳': '採否記帳（三人目C(9)）', '8. 引用一意性': '裁定A4',
}
lines = ['# 追補W 採点器 v2→v3 diff の行単位帰属（機械生成・2026-08-05）', '',
         '三人目検分者の勧告「指摘・裁定に対応しない差分ゼロの機械確認」の実装。',
         'v2凍結写し（scorer-review/scorer_w_v2_frozen_copy.py）との unified diff の全変更行に帰属を付す。',
         '**帰属不能の行が一行でもあれば本表の生成は失敗として扱う。**', '',
         '| diff行 | 帰属 |', '|---|---|']
un = 0
for l in difflib.unified_diff(v2, v3, lineterm='', n=0):
    if l.startswith(('---', '+++', '@@')):
        continue
    if not l.startswith(('+', '-')):
        continue
    body = l[1:].strip()
    if not body:
        continue
    hit = next((v for k, v in ATTR.items() if k in body), None)
    if hit is None:
        un += 1
        hit = '**帰属不能**'
    lines.append(f'| `{l[:70].replace("|", "\\|")}` | {hit} |')
io.open('scorer-review/addendum-W-scorer-v3-diff-attribution.md', 'w', encoding='utf-8', newline='\n'
        ).write('\n'.join(lines) + f'\n\n帰属不能行: **{un}**\n')
print('diff帰属表生成: 帰属不能', un, '行')
