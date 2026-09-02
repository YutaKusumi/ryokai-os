# -*- coding: utf-8 -*-
"""
撹拌規則 実装（追補E′・第一段）  scramble.py
決定的：同一入力・同一 seed → 同一出力。乱数は段①の順列にのみ用いる。
依存: python3.12 / fugashi 1.5.2 / unidic-lite 1.0.8（形態素解析器・辞書を固定）
使い方:
  python3 scramble.py --stage 3 --seed 524683211 input.txt [--report report.json]
  段③で入替を行う命題集合を外部から与える場合: --apply-set 1,3,5   （命題インデックス、1始まり）
  版間で「入替を行った命題集合」を一致させる手順:
     1) 両版を --stage 3 で走らせ、report の feasible を得る
     2) 共通部分 S = feasible_BP ∩ feasible_sec を --apply-set として両版に与えて再実行
"""
import argparse, hashlib, json, random, re, sys
from collections import Counter
import fugashi

TAGGER = fugashi.Tagger()

SEED_STR = "追補E′/撹拌規則/第一段/2026-09-01"
SEED_DEFAULT = int(hashlib.sha256(SEED_STR.encode()).hexdigest()[:8], 16)  # = 524683211

# ---------- 段②：文頭接続詞（凍結表） ----------
# 反転表：順接 ↔ 逆接（双方向）。表にある接続詞は反転する。
REVERSAL_PAIRS = [
    ("したがって", "しかし"),
    ("よって", "だが"),
    ("ゆえに", "ところが"),
    ("それゆえ", "それでも"),
    ("そのため", "にもかかわらず"),
    ("だから", "けれども"),
    ("その結果", "とはいえ"),
    ("つまり", "しかしながら"),
    ("すなわち", "もっとも"),
    ("そして", "一方"),
    ("さらに", "他方"),
    ("また", "一方で"),
    ("加えて", "それに対して"),
    ("同様に", "逆に"),
]
REVERSE = {}
for a, b in REVERSAL_PAIRS:
    REVERSE[a] = b; REVERSE[b] = a
# 削除表：順序・列挙・補足の標識（反転対を持たない）→ 削除
DELETE_ONLY = ["まず", "はじめに", "第一に", "第二に", "第三に", "第四に", "第五に",
               "次に", "つぎに", "最後に", "さいごに", "なお", "ただし", "特に", "とくに",
               "例えば", "たとえば", "ちなみに", "要するに", "結局", "以上のように", "このように"]
CONNECTIVES = sorted(set(list(REVERSE.keys()) + DELETE_ONLY), key=len, reverse=True)
CONN_RE = re.compile("^(" + "|".join(map(re.escape, CONNECTIVES)) + ")(、|，|,)?")

# ---------- 文分割 ----------
def split_sentences(text):
    text = text.replace("\r", "").strip()
    text = re.sub(r"\s+", "", text)  # 空白・改行は文境界にしない（凍結：句点のみ）
    parts = re.findall(r"[^。！？!?]+[。！？!?]+」?", text)
    rest = re.sub(r"[^。！？!?]+[。！？!?]+」?", "", text)
    if rest:
        parts.append(rest)  # 終端句点なしの末尾も一文と数える
    return parts

# ---------- 段① ----------
def stage1(sentences, seed):
    idx = list(range(len(sentences)))
    random.Random(seed).shuffle(idx)          # 順列は seed のみで決まる
    return idx  # idx[j] = 位置 j に置く元の文番号（命題インデックス）

# ---------- 段② ----------
def stage2(sentence):
    m = CONN_RE.match(sentence)
    if not m:
        return sentence, None
    conn = m.group(1)
    tail = sentence[m.end():]
    comma = m.group(2) or ""
    if conn in REVERSE:
        return REVERSE[conn] + comma + tail, ("reverse", conn, REVERSE[conn])
    else:
        return tail, ("delete", conn, None)

# ---------- 段③ ----------
NOUNISH = {"名詞", "接頭辞", "接尾辞", "代名詞"}

def tokens(sentence):
    return [(w.surface, w.feature.pos1, w.feature.pos2) for w in TAGGER(sentence)]

def np_before(toks, i):
    """位置 i の助詞の直前にある最大名詞句の開始位置を返す（の で連結された名詞句を含む）。"""
    j = i
    while j - 1 >= 0:
        s, p1, p2 = toks[j - 1]
        if p1 in NOUNISH:
            j -= 1; continue
        if s == "の" and p1 == "助詞" and j - 2 >= 0 and toks[j - 2][1] in NOUNISH and j < i:
            j -= 1; continue
        break
    return j

def stage3(sentence):
    toks = tokens(sentence)
    subj = obj = None
    for i, (s, p1, p2) in enumerate(toks):
        # 直前が名詞句である が/は のみを主語標識とする（「には」「とは」「では」の は は飛ばす）
        if p1 == "助詞" and s in ("が", "は") and p2 in ("格助詞", "係助詞") and i > 0 and toks[i - 1][1] in NOUNISH:
            subj = i; break
    if subj is None:
        return sentence, {"feasible": False, "reason": "no_subject_particle"}
    for marker in ("を", "に"):
        for i, (s, p1, p2) in enumerate(toks):
            if p1 == "助詞" and p2 == "格助詞" and s == marker and i != subj:
                obj = i; break
        if obj is not None:
            used = marker; break
    if obj is None:
        return sentence, {"feasible": False, "reason": "no_object_particle"}
    s0, o0 = np_before(toks, subj), np_before(toks, obj)
    if s0 == subj or o0 == obj:
        return sentence, {"feasible": False, "reason": "empty_np"}
    # 重なり
    if not (subj < o0 or obj < s0):
        return sentence, {"feasible": False, "reason": "np_overlap"}
    S = "".join(t[0] for t in toks[s0:subj]); O = "".join(t[0] for t in toks[o0:obj])
    if S == O:
        return sentence, {"feasible": False, "reason": "identical_np"}
    surf = [t[0] for t in toks]
    if s0 < o0:
        new = surf[:s0] + [O] + surf[subj:o0] + [S] + surf[obj:]
    else:
        new = surf[:o0] + [S] + surf[obj:s0] + [O] + surf[subj:]
    return "".join(new), {"feasible": True, "subject": S, "object": O, "object_marker": used}

# ---------- (a′) 機械検査 ----------
def has_predicate(sentence):
    toks = tokens(sentence)
    core = [t for t in toks if t[1] != "補助記号"]
    if not core:
        return False
    for s, p1, p2 in core:
        if p1 in ("動詞", "形容詞", "形状詞") or (p1 == "助動詞" and s in ("だ", "です", "である", "ある", "ない", "た"))\
           or (p1 == "動詞" and s == "ある"):
            return True
    return False

def has_subject(sentence):
    return any(p1 == "助詞" and s in ("が", "は") for s, p1, p2 in tokens(sentence))

def multiset(text):
    return Counter(t[0] for t in tokens(text))

def token_len(text, tokenizer_name=None):
    if tokenizer_name:
        try:
            from transformers import AutoTokenizer
            tok = AutoTokenizer.from_pretrained(tokenizer_name)
            return len(tok(text)["input_ids"]), "tokenizer:" + tokenizer_name
        except Exception as e:
            return len(text), f"UNVERIFIED(fallback=chars; {type(e).__name__})"
    return len(text), "UNVERIFIED(fallback=chars)"

# ---------- 本体 ----------
def run(text, stage, seed, apply_set=None, tokenizer_name=None):
    sents = split_sentences(text)
    n = len(sents)
    report = {"seed": seed, "n_sentences": n, "stage": stage}
    perm = stage1(sents, seed)
    report["permutation"] = [p + 1 for p in perm]           # 1始まりの命題インデックス
    report["fixed_points"] = sum(1 for j, p in enumerate(perm) if j == p)
    out1 = [sents[p] for p in perm]
    if stage == 1:
        final = out1; out2 = out1
    else:
        out2, log2 = [], []
        for j, s in enumerate(out1):
            s2, op = stage2(s)
            out2.append(s2)
            if op:
                log2.append({"position": j + 1, "proposition": perm[j] + 1, "op": op[0], "from": op[1], "to": op[2]})
        report["stage2_edits"] = log2
        final = out2
    if stage == 3:
        out3, log3, feasible = [], [], []
        for j, s in enumerate(out2):
            pidx = perm[j] + 1
            s3, info = stage3(s)
            if info["feasible"]:
                feasible.append(pidx)
            do = info["feasible"] and (apply_set is None or pidx in apply_set)
            out3.append(s3 if do else s)
            log3.append({"position": j + 1, "proposition": pidx, "applied": do, **info})
        report["stage3"] = log3
        report["feasible"] = sorted(feasible)
        report["applied_set"] = sorted(p for l in log3 for p in [l["proposition"]] if l["applied"])
        report["infeasible_count"] = n - len(feasible)
        final = out3
    # (a′)
    ap = {}
    ap["sentence_count_equal"] = (len(final) == n)
    ap["each_sentence_has_subject_and_predicate"] = [(has_subject(s), has_predicate(s)) for s in final]
    ap["multiset_stage3_equals_stage2"] = (multiset("".join(final)) == multiset("".join(out2))) if stage == 3 else None
    L0, how = token_len(text, tokenizer_name); L1, _ = token_len("".join(final), tokenizer_name)
    ap["length"] = {"original": L0, "output": L1, "ratio": round(L1 / L0, 4), "within_3pct": abs(L1 / L0 - 1) <= 0.03, "measured_by": how}
    report["a_prime"] = ap
    return "".join(final), report

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("infile"); ap.add_argument("--stage", type=int, default=3)
    ap.add_argument("--seed", type=int, default=SEED_DEFAULT)
    ap.add_argument("--apply-set", default=None); ap.add_argument("--report", default=None)
    ap.add_argument("--tokenizer", default=None)
    a = ap.parse_args()
    text = open(a.infile, encoding="utf-8").read()
    aset = set(int(x) for x in a.apply_set.split(",")) if a.apply_set else None
    out, rep = run(text, a.stage, a.seed, aset, a.tokenizer)
    print(out)
    if a.report:
        json.dump(rep, open(a.report, "w"), ensure_ascii=False, indent=1)
    else:
        print(json.dumps(rep, ensure_ascii=False, indent=1), file=sys.stderr)
