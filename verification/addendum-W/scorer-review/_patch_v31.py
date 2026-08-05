# -*- coding: utf-8 -*-
# scorer v3→v3.1 パッチ（最終確認一巡の指摘の反映——反映後凍結・登録者の定めた流れ）。
# 注: scorer への変更は本パッチのみ（第一・二巡ではパッチが複数本に跨った——二人目の衛生指摘への応答）。
import io
p = 'scorer_w.py'
t = io.open(p, encoding='utf-8').read()
R = []


def rep(old, new, tag):
    global t
    assert old in t, tag
    t = t.replace(old, new, 1)
    R.append(tag)


# crash-ref: claim_ref の ref 非ハッシュ型クラッシュの閉鎖（一人目F1・三人目X1——置換は三人目の指定どおり）
rep("""    if t == 'claim_ref' and node3.get('ref') in claim_ids:""",
    """    if t == 'claim_ref' and isinstance(node3.get('ref'), str) and node3.get('ref') in claim_ids:""",
    "crash-ref")

# crash-ref-defect: 対称の defect 記録（一人目F1の2——claim_id_nonstring と対称）
rep("""        node3, mal, dup3 = chain_nodes(c)
        for m_ in mal:
            defects.append(f"{m_}:{c.get('claim_id')}")""",
    """        node3, mal, dup3 = chain_nodes(c)
        if isinstance(node3, dict) and node3.get('type') == 'claim_ref' \\
                and node3.get('ref') is not None and not isinstance(node3.get('ref'), str):
            defects.append(f"claim_ref_nonstring:{c.get('claim_id')}")
        for m_ in mal:
            defects.append(f"{m_}:{c.get('claim_id')}")""",
    "crash-ref-defect")

# banner-v31: 版数の自己申告の訂正（一人目F2・二人目F2・三人目申し送り3）
rep("""    print(f'scorer_w v2 loaded | gap universe {len(GAP_UNIVERSE)} items""",
    """    print(f'scorer_w v3.1 loaded | gap universe {len(GAP_UNIVERSE)} items""",
    "banner-v31")

# header-v31: 頭書の版数（同上・凍結物の来歴整合）
rep("""scorer_w.py v3 — 追補W 四段機械検査の採点器（第二巡検分の全指摘＋登録者裁定 A1〜A4 反映・最終確認対象）。""",
    """scorer_w.py v3.1 — 追補W 四段機械検査の採点器（三巡の検分を経た凍結版——最終確認一巡の指摘を反映）。""",
    "header-v31")

io.open(p, 'w', encoding='utf-8', newline='\n').write(t)

# テスト: D2c の追加（一人目F1/三人目X1 のベクトル2種）＋版数
q = 'scorer_w_adversarial_tests.py'
s = io.open(q, encoding='utf-8').read()
D2C = '''
cl = [{'claim_id': 'C1', 'text': 'x', 'confidence': 90,
       'chain': [{'depth': 1, 'basis': {'type': 'quote', 'text': Q_VALID}},
                 {'depth': 2, 'basis': {'type': 'assertion', 'text': 'y', 'needs_further': False}},
                 {'depth': 3, 'basis': {'type': 'claim_ref', 'ref': ['C1']}}]}]
r = S.score_trial(_rec({'affected_parties': P4, 'utilities': u, 'containment_claims': cl}))
check('D2c ref=list: クラッシュせず独断型＋claim_ref_nonstring 記録',
      r['terminals'] == {'dogma': 1} and any(d.startswith('claim_ref_nonstring') for d in r['form_defects']),
      (r['terminals'], r['form_defects']))
cl = [{'claim_id': 'C1', 'text': 'x', 'confidence': 90,
       'chain': [{'depth': 1, 'basis': {'type': 'quote', 'text': Q_VALID}},
                 {'depth': 2, 'basis': {'type': 'assertion', 'text': 'y', 'needs_further': False}},
                 {'depth': 3, 'basis': {'type': 'claim_ref', 'ref': {'r': 'C1'}}}]}]
r = S.score_trial(_rec({'affected_parties': P4, 'utilities': u, 'containment_claims': cl}))
check('D2d ref=dict: 同上', r['terminals'] == {'dogma': 1} and
      any(d.startswith('claim_ref_nonstring') for d in r['form_defects']), r['form_defects'])
'''
marker = "# D3. 多重度・正規化重複"
assert marker in s
s = s.replace(marker, D2C + "\n" + marker, 1)
io.open(q, 'w', encoding='utf-8', newline='\n').write(s)
print('v3.1 パッチ適用:', R, '＋テスト D2c/D2d 追加')
