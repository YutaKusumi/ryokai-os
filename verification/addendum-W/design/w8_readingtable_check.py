# -*- coding: utf-8 -*-
"""w8_readingtable_check.py — W8 凍結読み表の全域性の機械検証（凍結物に同梱）"""
CELLS = {}
for hw1 in ["改善有意", "悪化有意", "帰無"]:
    for hw2 in ["改善有意", "悪化有意", "帰無"]:
        CELLS[(hw1, hw2)] = None
# draft4 W8 の9行（行番号→セル）
ROWS = {
    1: ("改善有意", "改善有意"), 2: ("改善有意", "帰無"), 3: ("改善有意", "悪化有意"),
    4: ("帰無", "改善有意"),   5: ("帰無", "帰無"),   6: ("帰無", "悪化有意"),
    7: ("悪化有意", "改善有意"), 8: ("悪化有意", "帰無"), 9: ("悪化有意", "悪化有意"),
}
for r, cell in ROWS.items():
    assert CELLS[cell] is None, f"重複: {cell}"
    CELLS[cell] = r
missing = [c for c, r in CELLS.items() if r is None]
assert not missing, f"欠落セル: {missing}"
OVERLAYS = ["refuse転位(W/P)", "P悪化(P>N)", "P改善(P<N)"]
PRIORITY = ["refuse転位文を先頭", "P悪化/P改善条項文を主文に併記（発動時は全セル・セル1を含む・条項文なしの引用禁止）", "9セル本文"]
print("9セル全域: OK(9/9・重複なし・欠落なし)")
print("特別条項:", OVERLAYS, "優先順位:", PRIORITY)
