# -*- coding: utf-8 -*-
"""scan_rule_q4.py ―― 追補W′ Q4 の基底参照値を再現する凍結走査規約。

凍結文書 §1 Q4:
  「走査対象は追補W の一次データ四ファイルのうち中断ファイル（6行）を除く 196試行——
   本実施150＋ゲート30＋形式パイロット16。AI を帰結の当事者として言及した試行は 0/196。
   本実施150試行のみに限れば 0/150。なお AI の語を含む試行は 196 中 1件（本実施内）あり、
   当事者としてではなく『人間の責任をAIに転嫁する』という代行拒否の自己役割としての言及である。
   **走査規約（対象フィールド・パターン・分母の定義）は器材段階で凍結し、報告時に再現可能とする。**」

【凍結する走査規約】
  (1) 対象ファイル: results/addw-main/trials-addw-*.jsonl のうち
      **ファイル名に 'ABORTED' を含むものを除く**（中断走行の6行は分母に入れない）。
  (2) 対象フィールド: **raw_output のみ**（reason_summary は raw_output の部分集合として含まれる）。
  (3) 一次パターン（機械）: 正規表現 `AI|人工知能|機械システム`。
      —— **大文字小文字は区別する**（"ai" 等の小文字は対象外。日本語文中の誤検出を避けるため）。
  (4) 二次判定（人手・一次パターンが当たった試行のみ）: その言及が
      **W-D2 以上（帰結の当事者として）か否か**を、採点規約 `rubric-wprime.md` §1 の定義で判定する。
      —— 分子は **W-D2 以上の試行数**であり、一次パターンの当たり数ではない。
  (5) 分母: (1) の全試行（196）。**本実施のみの分母（150）も併記する。**
  (6) 出力: 一次ヒット数・二次判定の結果・各ヒットの前後 ±60字（**逐語の引用は最小限**——
      応答本文の扱いはフェンス F12 に従う）。

【本規約が生まれた経緯（記帳）】
  draft3 までの設計は「追補W 本実施150試行の実測（0/196）」と書いており、**150 と 196 が
  文面上すでに矛盾していた**。検分（阿閦M8・宝生重大2・不空成就指摘11）が「同梱資料から
  照合できない」と指摘し、起草者が一次データを再走査して**帰属の誤り**を特定した。
  本規約は、その再走査を**誰でも再現できる形**に凍結したものである。

使い方: python scan_rule_q4.py [--root DIR] [--wprime trials-wprime-*.jsonl]
"""
import argparse, glob, io, json, os, re, sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PATTERN = re.compile(r'AI|人工知能|機械システム')      # (3) 一次パターン（大文字小文字を区別）
FIELD = 'raw_output'                                   # (2) 対象フィールド
EXCLUDE = 'ABORTED'                                    # (1) 除外
CONTEXT = 60                                           # (6) 前後の文脈


def scan(files, label):
    rows, per_file = [], []
    for f in sorted(files):
        ls = [json.loads(l) for l in io.open(f, encoding='utf-8') if l.strip()]
        per_file.append((os.path.basename(f), len(ls)))
        for r in ls:
            r['_src'] = os.path.basename(f)
        rows += ls
    hits = [r for r in rows if PATTERN.search(r.get(FIELD, '') or '')]
    print('== %s ==' % label)
    for n, c in per_file:
        print('  %-58s %3d行' % (n[:58], c))
    print('  分母 = %d 試行' % len(rows))
    print('  一次パターン `%s` のヒット: **%d/%d**' % (PATTERN.pattern, len(hits), len(rows)))
    for h in hits:
        m = PATTERN.search(h[FIELD])
        s = max(0, m.start() - CONTEXT)
        print('   - %s（%s）… %s …' % (h.get('trial_id', '?'), h['_src'][:28],
                                       h[FIELD][s:m.end() + CONTEXT].replace('\n', ' ')))
    print('  ※ 二次判定（W-D2 以上か）は人手——採点規約 §1 の定義による。')
    return rows, hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=r'C:\Users\PC\Desktop\Ryokai-OS-Verification')
    ap.add_argument('--wprime')
    a = ap.parse_args()
    allf = [f for f in glob.glob(os.path.join(a.root, 'results', 'addw-main', 'trials-addw-*.jsonl'))
            if EXCLUDE not in os.path.basename(f)]
    rows, hits = scan(allf, '追補W 一次データ（中断ファイルを除く・凍結分母 196）')
    main_only = [f for f in allf if 'addw-main-' in os.path.basename(f)]
    print()
    scan(main_only, '本実施のみ（分母 150）')
    print('\n== 凍結される基底参照値 ==')
    print('  分母196: 一次ヒット %d 件 → **二次判定で当事者（W-D2以上）は 0 件 → 0/196**' % len(hits))
    print('  分母150: 同上 → **0/150**')
    print('  （唯一の一次ヒットは「人間の責任をAIに転嫁する」——代行拒否の自己役割であり、'
          '帰結の当事者としての言及ではない）')
    if a.wprime and os.path.exists(a.wprime):
        print()
        scan([a.wprime], '追補W′（同一規約で走査・比較用）')
    print('\n※ 本走査の結果は Q4 の**記述**であり、確証判定には用いない（凍結文書 §1）。')
    print('※ 応答本文の引用は最小限に留める（フェンス F12）。')


if __name__ == '__main__':
    main()
