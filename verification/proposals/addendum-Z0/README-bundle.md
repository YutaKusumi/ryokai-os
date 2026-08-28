# 再現手順（検分バンドル用・X 申し送り6 の様式要件・初適用）

前提: Python 3.11+・scipy。バンドルを任意の場所に展開し、**展開ルートをそのまま作業ディレクトリとする**
（フォルダ名は改変しないこと——器材は相対パス `armsZ0/`・`armsWsecond/`・`app-scenarios.json` を参照する）。

1. 素材検査器 v2: `python pipeline/check_materials_z0.py` → 期待: `結果: PASS（fails=0）`（照合12件＝
   PROVENANCE ＋ 設計文書付録A）
2. 腕の再構成: `python pipeline/build_arms_z0.py` → 期待: 3腕の SHA が PROVENANCE-Z0 §3 と一致
2b. **変異スイート（v2 新設・三巡反映で15変異）**: `python pipeline/mutation_tests_z0.py` → 期待: `15/15 検出`＋`復元後: PASS`
   （M-A は一巡・宝生如来の差し戻し級の実証変異。素材を一時改変し自動復元します——実行後に手順1で
   PASS が戻ることも確認してください）
3. 検出力の独立再計算（例・基底40%・n=50・両側α=0.05）:
   `python -c "from scipy.stats import fisher_exact,binom;
   n=50; px=[binom.pmf(k,n,.30) for k in range(n+1)]; py=[binom.pmf(k,n,.50) for k in range(n+1)];
   print(sum(px[a]*py[b] for a in range(n+1) for b in range(n+1)
   if fisher_exact([[a,n-a],[b,n-b]])[1]<0.05))"` → 期待: ≈0.463

system 側の独立検算（v2 で可能に）: 同梱 `arms/A2-on-full.md` の SHA(LF) が `AAB363D85E103C13`
（D′ trials の `system_sha` 記録値）と一致することを自前計算で確認できる。

Free 腕の D′ 同一性の独立検算: `armsWsecond/preamble-Nthird.md` と `app-scenarios.json` から
式 `前置き.rstrip('\n') + '\n\n' + N2 + json_instruction['nuclear']` を自前で組み、
`armsZ0/arm-Free.md` と比較する（検査器 (b) と独立の経路で）。
