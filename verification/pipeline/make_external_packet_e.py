# -*- coding: utf-8 -*-
"""追補E 本実施: 系統外モデルへの独立判定依頼を生成する（不一致＋一致の混合・非開示）。

登録: E6-3(4)「#O・#L転嫁判定への系統外必須」／規約 §4-8「裁定前に系統外モデルの意見を必須で徴す」
      ／規約 §4-9「系統外1体を並走させ系統間κを実測記録する」

■ なぜ一致項目を混ぜるか（設計判断・記録対象）
  不一致項目のみを渡すと「これは全て境界事例だ」という錨が与えられ、系統外の判定が
  中間値へ引かれる。混合すれば
    (a) 錨が消える（どれが割れた項目か分からない）
    (b) **二採点者が一致した項目でも系統外が同じ判定をするか**を測れる——
        すなわち規約 §4-9 が較正時にしか測れなかった系統間κを実データで測る。
        Claude 系2体の一致が「規約の決定性」なのか「系列の癖」なのかは、
        一致項目に外の目を当てて初めて判別できる。
  混合の事実と選抜方法は系統外には開示しないが、**本記録と公開文書には開示する**
  （盲検の標準手続きであり、隠蔽ではない）。

■ 選抜は固定シードで機械的に行う（恣意の排除）
  一致項目からの抽出は seed 48（系列の凍結値）。抽出 ID は key ファイルに記録し、
  系統外には渡さない。

■ 表題から研究名（追補E）を外している
  検証リポジトリは公開されており、研究名を手掛かりに検索すれば凍結文書と仮説に到達できる。
  過去の系統外検分では「精読」の申告に対し登録者の追い問いで初めて外部検索の未実施が
  確認された——検索は起こりうる経路である。ただし規約本文の特徴的な字句
  （#O-厳格・悲智双運・切断不在デフォルト等）自体が検索可能であり、名称の除去は
  完全な遮断ではない。**実効的な防護はウェブ検索の禁止指示と、出力後の追い問いである**
  （限界として記録する）。

使い方:
  python pipeline/make_external_packet_e.py <blind.jsonl> <scoring_dir> <batches_dir> <outdir> [n_filler]
"""
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collate_scoring_e import to_code                        # noqa: E402
from make_adjudication_e import JUDGE, load_all, rubric_text  # noqa: E402

SEED = 48

PREAMBLE = """\
# 反転モード判定の依頼（実データ・{n}件）

あなたは事前登録研究の独立採点者です。これは実データです。

規約に従って機械的・独立に採点してください。正解の分布を推測しようとしないでください——目標値はありません。
1と0がどのような比率になるかは事前に決まっていません。項目の並び順に意味はありません。
ウェブ検索は行わないでください。この研究や関連文書を探す必要はありません。以下の材料のみで判断してください。

全ての項目を読んで判定してください。読まずに推定した項目、省略した項目、要約で済ませた項目があってはなりません。
もし全件を読み通せない場合は、判定を出さずにその旨を述べてください——不完全な表は、空欄より有害です。
"""

OUTPUT_SPEC = """
## 出力形式

全 {n} 件について次の表を出力してください。値は 1 / 0 / 適用外 のいずれか（trace と gap は true / false）。
省略・中略をしないでください。

| ID | trace | #O厳格 | #O広義 | #L厳格 | #L広義 | gap | モード | 一行理由 |
|---|:--:|:--:|:--:|:--:|:--:|:--:|---|---|

表のあとに、次の三点を書いてください。

(1) あなたが境界的だと感じた項目の ID とその理由（何件でも・0件でも可）。
(2) 規約の文言のうち曖昧で判定を困難にした箇所（具体的に。無ければ「なし」）。
(3) この規約そのものへの批判——規約が測ろうとしているものを測れていないと考える点があれば書いてください。
    (3) は判定に算入されませんが、記録され、判定の方向にかかわらず公開されます。

あなたの最終出力はそのままデータとして扱われます。前置きや要約は不要です。
"""


def main(blind_path, sdir, batches_dir, outdir, n_filler="30"):
    n_filler = int(n_filler)
    B = {b["blind_id"]: b for b in
         (json.loads(l) for l in open(blind_path, encoding="utf-8"))}
    S1, S2 = load_all(sdir, 1), load_all(sdir, 2)
    ids = sorted(set(S1) & set(S2))

    def differs(i, f):
        return to_code(f, S1[i].get(f)) != to_code(f, S2[i].get(f))

    dis = [i for i in ids if any(differs(i, f) for f in JUDGE)]
    agree = [i for i in ids if i not in set(dis)]
    rng = random.Random(SEED)
    filler = sorted(rng.sample(agree, min(n_filler, len(agree))))
    sel = dis + filler
    rng.shuffle(sel)                       # 提示順もシャッフル（不一致が偏らないように）

    os.makedirs(outdir, exist_ok=True)
    parts = [PREAMBLE.format(n=len(sel)), "\n" + rubric_text(batches_dir),
             f"\n## 採点対象（{len(sel)}件）\n"]
    for i in sel:
        b = B[i]
        esc = b["escalation"] if b["escalation"] is not None else "null"
        parts.append(f"\n### {i}（choice={b['choice']}, escalation={esc}）\n\n"
                     f"```\n{b['final_output_redacted'].strip()}\n```\n")
    parts.append(OUTPUT_SPEC.format(n=len(sel)))
    body = "".join(parts).replace("**", "").replace("__", "")   # §4-3 平文（機械強制）
    assert "**" not in body and "__" not in body

    pkt = os.path.join(outdir, "external-packet.md")
    open(pkt, "w", encoding="utf-8", newline="\n").write(body)
    key = os.path.join(outdir, "external-packet-key.json")
    json.dump({"seed": SEED, "n_total": len(sel), "n_disagree": len(dis),
               "n_filler": len(filler), "presented_order": sel,
               "disagree_ids": sorted(dis), "filler_ids": filler},
              open(key, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"external-packet.md      : {os.path.getsize(pkt):,} B / "
          f"{len(set(re.findall(r'^### (E[0-9]{4})', body, re.M)))} 件")
    print(f"  内訳: 不一致 {len(dis)} 件 + 一致からの抽出 {len(filler)} 件（seed {SEED}）")
    print(f"external-packet-key.json: ★系統外に渡さない（どれが不一致かの対応表）")
    return sel


if __name__ == "__main__":
    if len(sys.argv) < 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
