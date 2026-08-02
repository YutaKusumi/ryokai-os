# -*- coding: utf-8 -*-
"""追補E 本実施: 独立二採点者の出力を突合し、κ と不一致IDのみを出す。

登録: FROZEN E5-1〜E5-4／規約 reversal-rubric-adde-v2.3.md §4-8（独立二採点者→不一致は登録者裁定）

■ 設計の要点——コーディネータを content から遠ざける
  本器材は **判定値と ID だけ**を扱い、
    ・応答本文（final_output_redacted）
    ・採点者の「一行理由」
    ・腕（key ファイル）
  を**一切読まない・一切出力しない**。出すのは (a) フィールド別の一致数と Cohen's κ、
  (b) 不一致した blind_id の一覧、(c) 分布の周辺度数（腕を伴わない）のみ。
  これにより、裁定に回す対象を特定しながら、コーディネータが語彙経由で腕を推測する
  経路を塞ぐ（E5-4 は「副次分析は盲検ではない」と認めているが、認めることは
  塞げるところを塞がない理由にはならない）。

■ 腕別集計は行わない
  本器材は key ファイルを開かない。腕との突合は**裁定確定後**に別器材で行う
  （追補D の「裁定は key 照合前に確定」と同じ規律）。

使い方:
  python pipeline/collate_scoring_e.py <scoring_dir>
"""
import glob
import json
import os
import re
import sys

ID_RE = re.compile(r"^\|\s*(E\d{4})\s*\|(.*)$")
ARMS = {"Lneg", "Onull", "O"}
# 表1 の列順（バッチファイルの出力形式と一致）
T1 = ["trace", "o_strict", "o_broad", "l_strict", "l_broad", "gap", "modes", "reason"]
BINARY = {"true": 1, "false": 0, "1": 1, "0": 0, "t": 1, "f": 0,
          "yes": 1, "no": 0, "○": 1, "×": 0}
NA = {"適用外", "n/a", "na", "-", "—", "－"}


def cell_norm(s):
    return s.strip().replace("`", "").replace("*", "")


def parse_scorer(path):
    """1ファイルを読み、{blind_id: {field: value}} を返す（理由列は捨てる）。"""
    out = {}
    for line in open(path, encoding="utf-8"):
        m = ID_RE.match(line.strip())
        if not m:
            continue
        bid = m.group(1)
        cells = [cell_norm(c) for c in m.group(2).split("|")]
        while cells and cells[-1] == "":
            cells.pop()
        rec = out.setdefault(bid, {})
        if len(cells) >= len(T1):                       # 表1
            for k, v in zip(T1, cells):
                if k == "reason":                       # ★理由列は保持しない
                    continue
                rec[k] = v
        elif len(cells) == 2 and cells[0] in ARMS:      # 表3（腕推測・確信度）
            rec["arm_guess"], rec["arm_conf"] = cells[0], cells[1]
        elif len(cells) >= 2:                           # 表2（refuse 下位分類）
            rec["refuse_class"] = cells[0]
    return out


def to_code(field, v):
    """比較用の正規化コード。判定不能は None（一致計算から除く）。"""
    if v is None:
        return None
    s = v.strip().lower()
    if field in ("trace", "gap"):
        return BINARY.get(s)
    if field in ("o_strict", "o_broad", "l_strict", "l_broad"):
        if s in NA or "適用外" in v:
            return "NA"
        return BINARY.get(s)
    if field == "modes":
        ms = sorted(set(re.findall(r"#(?:19|26|12)", v)))
        return ",".join(ms) if ms else "-"
    return v.strip()


def kappa(pairs):
    """Cohen's κ（カテゴリ任意）。pairs = [(a, b), ...]"""
    n = len(pairs)
    if n == 0:
        return None, 0.0
    cats = sorted({x for p in pairs for x in p}, key=str)
    obs = sum(1 for a, b in pairs if a == b) / n
    pe = 0.0
    for c in cats:
        pa = sum(1 for a, _ in pairs if a == c) / n
        pb = sum(1 for _, b in pairs if b == c) / n
        pe += pa * pb
    if pe >= 1.0:
        return None, obs                                # 周辺が退化（κ 定義不能）
    return (obs - pe) / (1 - pe), obs


def main(sdir):
    S = {}
    for who in (1, 2):
        merged = {}
        files = sorted(glob.glob(os.path.join(sdir, f"scorer{who}-batch*.md")))
        for p in files:
            merged.update(parse_scorer(p))
        S[who] = merged
        print(f"採点者{who}: ファイル {len(files)} 件 / 判定 {len(merged)} 項目")

    ids = sorted(set(S[1]) & set(S[2]))
    only1, only2 = sorted(set(S[1]) - set(S[2])), sorted(set(S[2]) - set(S[1]))
    print(f"共通 ID = {len(ids)}  / 採点者1のみ {len(only1)}  / 採点者2のみ {len(only2)}")
    if only1 or only2:
        print("  片側のみ:", (only1 + only2)[:20])
    expect = [f"E{i:04d}" for i in range(150)]
    print("全150網羅 =", sorted(ids) == expect)

    report = {"n_common": len(ids), "fields": {}, "disagreements": {}}
    fields = ["trace", "o_strict", "o_broad", "l_strict", "l_broad", "gap",
              "modes", "arm_guess"]
    print()
    print(f"{'field':10s} {'n':>4s} {'一致':>5s} {'率':>7s} {'κ':>7s}   不一致ID")
    for f in fields:
        pairs, dis = [], []
        for i in ids:
            a, b = to_code(f, S[1][i].get(f)), to_code(f, S[2][i].get(f))
            if a is None or b is None:
                continue
            pairs.append((a, b))
            if a != b:
                dis.append(i)
        k, obs = kappa(pairs)
        ks = "定義不能" if k is None else f"{k:.4f}"
        print(f"{f:10s} {len(pairs):4d} {len(pairs)-len(dis):5d} {obs*100:6.1f}% {ks:>8s}   "
              f"{','.join(dis) if dis else '—'}")
        report["fields"][f] = {"n": len(pairs), "agree": len(pairs) - len(dis),
                              "obs_pct": round(obs * 100, 1),
                              "kappa": None if k is None else round(k, 4)}
        report["disagreements"][f] = dis

    # 周辺度数（腕を伴わない・裁定に必要な分布のみ）
    print()
    print("=== 周辺度数（腕別ではない） ===")
    for f in fields:
        for who in (1, 2):
            c = {}
            for i in ids:
                v = to_code(f, S[who][i].get(f))
                if v is not None:
                    c[v] = c.get(v, 0) + 1
            print(f"  {f:10s} 採点者{who}: {dict(sorted(c.items(), key=lambda x: str(x[0])))}")

    allbad = sorted({i for d in report["disagreements"].values() for i in d})
    print()
    print(f"=== 裁定に回す項目: {len(allbad)} 件 ===")
    print(",".join(allbad) if allbad else "なし（完全一致）")
    report["adjudicate"] = allbad

    out = os.path.join(sdir, "collation-report.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(f"-> {out}")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
