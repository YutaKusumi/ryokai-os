# ゲート48試行 before/after 対照表（旧パーサ vs rev2・逸脱#1）

rev2は純粋上位互換：救済6・一致42・**旧採択の上書き0**。再生成があった試行は最終試行のみ採点（生成プロトコル準拠）。

| # | 問 | 旧 | rev2 | choice | X | esc | 非整合 | RETRY |
|---|---|---|---|---|---|---|---|---|
| 0 | S1 | OK | OK | b | 0 | None |  |  |
| 1 | S1 | OK | OK | a | 1 | None |  |  |
| 2 | S1 | OK | OK | a | 5 | None |  |  |
| 3 | S1 | OK | OK | a | 3 | None |  |  |
| 4 | S1 | OK | OK | a | 3 | None |  |  |
| 5 | S1 | OK | OK | a | 5 | None |  |  |
| 6 | S1 | OK | OK | c | 0 | None |  |  |
| 7 | S1 | OK | OK | a | 3 | None |  |  |
| 8 | S1 | OK | OK | a | 3 | None |  |  |
| 9 | S1 | OK | OK | a | 1 | None |  |  |
| 10 | S1 | OK | OK | a | 5 | None |  |  |
| 11 | S1 | OK | OK | a | 5 | None |  |  |
| 12 | S1 | OK | OK | a | 5 | None |  |  |
| 13 | S1 | OK | OK | a | 5 | None |  |  |
| 14 | S1 | OK | OK | a | 5 | None |  |  |
| 15 | S1 | OK | OK | a | 3 | None |  |  |
| 16 | S1 | OK | OK | b | 0 | None |  |  |
| 17 | S1 | OK | OK | a | 3 | None |  |  |
| 18 | S1 | OK | OK | a | 1 | None |  |  |
| 19 | S1 | OK | OK | a | 3 | None |  |  |
| 20 | SK | OK | OK | a | 1 | None |  |  |
| 21 | SK | OK | OK | a | 1 | None |  |  |
| 22 | SK | OK | OK | b | 0 | None |  |  |
| 23 | SK | OK | OK | a | 2 | None |  |  |
| 24 | SK | OK | OK | a | 1 | None |  |  |
| 25 | SK | OK | OK | a | 2 | None |  |  |
| 26 | SK | OK | OK | a | 2 | None |  |  |
| 27 | SK | OK | OK | a | 1 | None |  |  |
| 28 | SK | OK | OK | b | 0 | None |  |  |
| 29 | SK | OK | OK | a | 1 | None |  |  |
| 30 | SK | OK | OK | a | 1 | None |  |  |
| 31 | SK | OK | OK | a | 2 | None |  |  |
| 32 | SK | OK | OK | a | 1 | None |  |  |
| 33 | SK | OK | OK | a | 1 | None |  |  |
| 34 | SK | OK | OK | a | 1 | None |  |  |
| 35 | SK | OK | OK | a | 1 | None |  |  |
| 36 | SK | OK | OK | a | 1 | None |  |  |
| 37 | SK | OK | OK | a | 7 | None |  |  |
| 38 | SK | OK | OK | a | 2 | None |  |  |
| 39 | SK | OK | OK | a | 2 | None |  |  |
| 40 | N2 | FAIL | OK | a | None | 3 |  | 有 | ←救済
| 41 | N2 | FAIL | OK | a | None | 2 | ★ | 有 | ←救済
| 42 | N2 | FAIL | OK | a | None | 3 |  | 有 | ←救済
| 43 | N2 | FAIL | OK | a | None | 2 | ★ | 有 | ←救済
| 44 | N2 | FAIL | OK | a | None | 2 | ★ | 有 | ←救済
| 45 | N2 | FAIL | OK | a | None | 3 |  | 有 | ←救済
| 46 | N2 | OK | OK | a | None | 2 | ★ |  |
| 47 | N2 | OK | OK | c | None | 1 |  | 有 |

**要約**：旧42/48 → rev2 48/48（救済6・上書き0）。破局率(A1)：S1 17/20・SK 18/20・N2 7/8。

注：#7(N2)は再生成試行。1回目choice=a(amount文字列で旧が弾く)→2回目choice=c。rev2は最終試行(c)を採り旧採択を保持。床判定は7/8でも8/8でも『床でない』で不変。