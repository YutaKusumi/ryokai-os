# 追補W 採点器 v2→v3 差分の帰属証示（機械再構成・2026-08-05）

三人目検分者の勧告「指摘・裁定に対応しない差分ゼロの機械確認」の実装（第二形式）。

**証示方法**: v2 凍結写し（`scorer_w_v2_frozen_copy.py`・`scorer_w_adversarial_tests_v2_frozen_copy.py`）に、
裁定タグ付き置換のみからなるパッチ3本（`_patch_v3.py`・`_patch_tests_v3.py`・`_patch_v3_docs.py`——
いずれも凍結物として同梱）を順に機械適用し、得られたファイルの LF-SHA256 が公開版 v3 と**完全一致**する
ことを確認した。よって v2→v3 の全差分は、パッチ内の rep() 呼び出し（各々が裁定 A1〜A4・第二巡検分の
指摘・ラベル訂正のいずれかをタグとして持つ）に**残余なく帰属**する。

| 対象 | v3 LF-SHA256 | 再構成一致 |
|---|---|---|
| scorer_w.py | B2DC37198E2A728DE4556BAB0BF9A726814E0F76CD68764A719A9A315A4C96FE | ✓ |
| scorer_w_adversarial_tests.py | 36428A250CE31AB7F39D6ECA04A631098C6DAA41D44732B1A46D7C73349521FF | ✓ |

帰属タグ一覧（パッチ順）: A1-catastrophe／builder-sha-const／builder-sha-check／min_len-param／
A3-sig／A3-counter／A3-count／A3-multiset／A3-listdup／A3-wire／crash-depth／crash-cid／
A4-threequant／A2-div-defer／A2-shadow／products-exact／escalation_nonint（tests側パッチ1）／
テスト改名（A3多重集合化）／D群追加（D1〜D8=第二巡全攻撃の収載）／頭書・IMPL_NOTES v3整合。


---

# v3→v3.1（最終確認一巡の反映・2026-08-05）

- 指摘: 一人目F1=三人目X1（claim_ref の非ハッシュ型 ref で TypeError——第二巡クラッシュ閉鎖の対称残余・
  両名独立特定・三人目が置換文字列まで指定）／F2=バナー・頭書の版数訂正。
- パッチ: `_patch_v31.py`（タグ: crash-ref／crash-ref-defect／banner-v31／header-v31＋テスト D2c/D2d）。
- **再構成証示**: v3 凍結写し（`scorer_w_v3_frozen_copy.py`・`scorer_w_adversarial_tests_v3_frozen_copy.py`）に
  `_patch_v31.py` を適用 → 凍結版 v3.1 と LF-SHA256 **完全一致**。
- 凍結版 v3.1 LF-SHA256:
  - scorer_w.py: 1670DAE5AD5A7C0740045643F50F9A51F288ACBA308C75CF15A8063FCF810D03
  - scorer_w_adversarial_tests.py: 3808049D059C2377D1A2D22B5E2C24A05FD0081383BE102AEADA73739EF46D02
- 一人目の凍結条件（機械三点）の充足: 帰属再構成 ✓／追加テスト D2c(+D2d) PASS ✓／既存58件を含む全件 PASS ✓
