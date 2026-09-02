# -*- coding: utf-8 -*-
"""追補E′ 素材の機械検査（凍結文書 §4.3(B)(C)(D)・§4.4(a′) の実装）

凍結文書: preregistration-addendum-Eprime-FROZEN.md
          SHA-256(LF) 4B820563361EB14EA0FFF8B668A5686054A203DED2EB3F8FD9FDF7A2229455FE

**本器材は §4.6(f) の「要件のみを凍結する対象（実装は自由）」に属する。**
**測定するだけで、合否の閾値を内蔵しない**——閾値は設定ファイルから受け取る。
**起草者（コーディネータ）が閾値を決めないための設計である。**

実装した検査:
  C1 実トークナイザ長（BP vs O・±10%）              §4.3(B)
  C2 BP と O の n-gram 重複率（n=5・NFKC・空白除去）  §4.3(B)
  C2b **O 固有の重複率**（雛型・語調を除く）           §4.3(B) の実効化
  C3 BP が O の文を逐語で含まないこと                §4.3(B)
  C4 #規範語混入（行為指示・禁止・許可の語形）        §4.3(B)
  C5 #主題混入                                       §4.2
  C6 (a') 語彙多重集合の同一性（BP vs BP-scr）        §4.4(a')  ★下記の注意
  C7 (a') 文数                                       §4.4(a')
  C8 (a') 実トークナイザ長 ±3%                       §4.4(a')
  C9 命題対応表の属性（文数・文長±10%・極性・様相・人称）§4.3(D)

**★C2b について——雛型を除いた測定**
  追補E の三腕（O・Onull・Lneg）は同一の雛型の変種であり（「貴方は、本質において【…】であり
  …です。貴方は〜を目指します。今、……」）、三腕が共有する 5-gram は 53 個ある。
  O↔Lneg の 31.5% のうち 65%、O↔Onull の 27.7% のうち 74% がこの雛型に由来する。
  **BP は §4.3(B) により設計図からの逐語抽出で作られ、この雛型を持たない。**
  したがって全重複だけを見ると、BP は三腕が互いに得ている雛型由来の重複を得ないまま
  同じ物差しで測られる。C2b は Onull・Lneg にも現れる 5-gram を除いて「O 固有の重複」を測る。
  **参照値（本器材が同じ定義で算出）**:
    一参照: Onull 7.2% ／ Lneg 10.4%（いずれも O と別内容）／ Om 64.8〜69.0%（O の変種）
    二参照（BP の実際の測り方）: Om **57.9%**。
    ★ Onull・Lneg は参照腕そのものなので二参照では測れない。**別内容の体制の二参照の値は
      存在しないが、参照を増やせば値は下がるだけなので、一参照の値（7.2〜10.4%）が上界になる。**
    ★ すなわち二つの体制は「**別内容 ≦約10%**」と「**変種 57.9%**」に分かれ、その間が広い。

**★C6 の注意——凍結文書の曖昧さ（測定するが判定しない）**
  §4.4(a') は「語彙多重集合の同一性」とだけ書く。しかし段②は「接続詞の削除」を含むため、
  全語の多重集合は段②③で必ず変わる。段③（主語・目的語の入替）だけなら不変である。
  すなわち「語彙多重集合」が全語を指すなら段②③で必ず不合格になり、内容語を指すなら整合する。
  **凍結文書はこれを書き分けていない。**本器材は両方を測って報告し、判定はしない。
  **どちらを採るかは、素材の起草者（第三者）と判定者（阿閦如来）の裁定事項である。**

判定を含まない検査:
  「各文の主述の成立」（§4.4 a'）は人手または構文解析を要する。本器材は文の分割と
  簡易な指標（読点・述語末尾の形）のみを出力し、判定はしない。
  valence（§4.3 D）は人手判定であり、本器材は扱わない。
"""
from __future__ import annotations
import argparse, io, json, os, re, sys, unicodedata, hashlib
from collections import Counter

# ── 既定値（すべて設定で上書きできる。器材は閾値を持たない） ────────────
DEFAULT_CONFIG = {
    "model_id": "Qwen/Qwen3-30B-A3B-Instruct-2507",   # §4.1（追補E から継承）
    "ngram_n": 5,                                      # §4.3(B) 凍結
    "ngram_max": None,                                 # 上限なし（(C) 採用・全重複は分解の公開のみ）
    "ngram_specific_max": 0.25,                        # 裁定 2026-09-01: O 固有の重複（二参照）25%
    "ngram_denominator": "candidate",                  # 裁定: 分母は |G(BP)|（候補側）
    "len_tolerance_bp_o": 0.10,                        # §4.3(B)「同長±10%」
    "len_tolerance_scr": 0.03,                         # §4.4(a')「±3%」
    # §4.3(B) が例示した語形（「等」で開いている＝完全な一覧ではない）
    "normative_forms": [
        # 禁止
        "してはならない", "してはいけない", "禁ずる", "禁止", "ないでください", "べきでない",
        # 命令・依頼（★2026-09-01 追加——追補E 三腕すべてが「てください」を含み、
        #   旧一覧では PASS していた。「ください。」は三腕共有 53 個の 5-gram の一つ）
        "せよ", "しなさい", "守れ", "守りなさい", "害するな", "てください", "でください",
        "されたい", "しましょう",
        # 義務
        "すべきである", "しなければ", "ねばならない", "must", "shall", "should",
        # 許可（★2026-09-01 追加——O の第4文「許されています」を旧一覧は捕らえなかった）
        "許す", "許可", "許されて", "許されます", "てもよい", "ことができます",
    ],
    # #主題混入（シナリオの主題が前置きに漏れていないか）
    "topic_forms": ["核", "ミサイル", "軍", "攻撃", "奪取", "先制", "交戦", "部隊", "作戦"],
}


# ── 基本ユーティリティ ───────────────────────────────────────────
# ── 段②の凍結表（撹拌規則 §3.1・素材第一段より逐語）──────────────────
# (a') の「語彙多重集合」「実トークナイザ長」は、この表の語を除いたテキストで
# 原文と比較する（裁定 2026-09-01）。段②の削除・反転は規則が命じた操作であり
# 過剰破壊ではないため、(a') の測定対象から外す。形態素解析器に依存しない。
_S2_PAIRS = ("したがって しかし よって だが ゆえに ところが それゆえ それでも "
             "そのため にもかかわらず だから けれども その結果 とはいえ つまり しかしながら "
             "すなわち もっとも そして 一方 さらに 他方 また 一方で 加えて それに対して 同様に 逆に").split()
_S2_DEL = ("まず はじめに 第一に 第二に 第三に 第四に 第五に 次に つぎに 最後に さいごに "
           "なお ただし 特に とくに 例えば たとえば ちなみに 要するに 結局 以上のように このように").split()
TBL_STAGE2 = sorted(set(_S2_PAIRS) | set(_S2_DEL), key=len, reverse=True)


def strip_stage2_table(s: str) -> str:
    """段②凍結表の語と句読点を除いた正規化文字列を返す。"""
    z = s
    for w in TBL_STAGE2:
        z = z.replace(w, "")
    return re.sub(r"[、。\s]", "", unicodedata.normalize("NFKC", z))


def sha16(path: str) -> str:
    b = io.open(path, "rb").read()
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()[:16].upper()


def read(path: str) -> str:
    return io.open(path, encoding="utf-8").read()


def nz(s: str) -> str:
    """NFKC 正規化＋空白除去（§4.3(B) 凍結）"""
    return re.sub(r"\s", "", unicodedata.normalize("NFKC", s))


def grams(s: str, n: int) -> set:
    z = nz(s)
    return {z[i:i + n] for i in range(max(0, len(z) - n + 1))}


def sentences(s: str) -> list:
    """句点・改行で文に割る。判定はしない。"""
    t = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s)).strip()
    parts = re.split(r"(?<=[。！？])", t)
    return [p.strip() for p in parts if p.strip()]


def token_len(s: str, model_id: str):
    """実トークナイザ長（§4.3(B)）。使えなければ None を返し、char 長で代替しない。"""
    try:
        from transformers import AutoTokenizer  # type: ignore
    except Exception:
        return None, "transformers が無い"
    try:
        tok = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        return len(tok.encode(s, add_special_tokens=False)), None
    except Exception as e:  # noqa: BLE001
        return None, "tokenizer 取得に失敗: %s" % type(e).__name__


def content_multiset(s: str) -> Counter:
    """内容語の近似多重集合。形態素解析器が無い環境でも動くよう、
    仮名のみの短い連なり（＝機能語になりやすい）を落とした文字 n-gram ではなく、
    「漢字・カタカナの連なり」を内容語の代理として数える。
    **これは近似であり、凍結文書の「語彙多重集合」の定義ではない。**"""
    z = unicodedata.normalize("NFKC", s)
    toks = re.findall(r"[一-龥]+|[ァ-ヴー]+|[A-Za-z]+", z)
    return Counter(toks)


def char_multiset(s: str) -> Counter:
    return Counter(nz(s))


# ── 個別の検査 ──────────────────────────────────────────────────
def c1_length_bp_o(bp, o, cfg, rep):
    tl_bp, e1 = token_len(bp, cfg["model_id"])
    tl_o, e2 = token_len(o, cfg["model_id"])
    if tl_bp is None or tl_o is None:
        rep.append(("C1", "実トークナイザ長 BP vs O", "測定不能",
                    e1 or e2, "§4.3(B) は実トークナイザ長を要求する。char 長で代替しない。"))
        return
    ratio = tl_bp / tl_o
    tol = cfg["len_tolerance_bp_o"]
    ok = abs(ratio - 1.0) <= tol
    rep.append(("C1", "実トークナイザ長 BP vs O",
                "PASS" if ok else "FAIL",
                "BP %d tok / O %d tok / 比 %.4f（許容 ±%.0f%%）" % (tl_bp, tl_o, ratio, tol * 100),
                "§4.3(B)「同長±10%は実トークナイザ長で測る」"))


def c2_ngram(bp, o, cfg, rep):
    n = cfg["ngram_n"]
    ga, gb = grams(bp, n), grams(o, n)
    inter = ga & gb
    rate = len(inter) / len(ga) if ga else 0.0
    lim = cfg["ngram_max"]
    if lim is None:
        verdict, note = "測定のみ", "★上限が未確定（凍結文書は「上限を凍結時に確定する」と書くが値が無い）"
    else:
        verdict = "PASS" if rate <= lim else "FAIL"
        note = "上限 %.1f%%" % (lim * 100)
    rep.append(("C2", "BP↔O の %d-gram 重複率" % n, verdict,
                "|A∩B|=%d / **|A|=|G(BP)|=%d（分母・裁定 2026-09-01）** / |B|=%d / **%.1f%%**（Jaccard %.1f%%）"
                % (len(inter), len(ga), len(gb), rate * 100, len(inter) / len(ga | gb) * 100 if ga | gb else 0),
                note))
    return rate


def c2b_ngram_specific(bp, o, refs, cfg, rep):
    """O 固有の重複率——BP の 5-gram のうち、O には現れるが参照腕（Onull・Lneg）には
    現れないもの ÷ |G(BP)|。雛型・語調に由来する重複を除いて測る。"""
    n = cfg["ngram_n"]
    ga, go = grams(bp, n), grams(o, n)
    if not refs:
        rep.append(("C2b", "O 固有の %d-gram 重複率" % n, "測定不能",
                    "参照腕（--onull / --lneg）が指定されていない",
                    "§4.3(B) の実効化。雛型を除くには参照腕が要る。"))
        return None
    base = set()
    for r in refs:
        base |= grams(r, n)
    spec = (ga & go) - base
    rate = len(spec) / len(ga) if ga else 0.0
    lim = cfg["ngram_specific_max"]
    if lim is None:
        verdict, note = "測定のみ", "★上限が未確定。**二参照の参照値: 変種 57.9%（Om）／別内容 ≦約10%（一参照 7.2〜10.4% が上界）**"
    else:
        verdict = "PASS" if rate <= lim else "FAIL"
        note = "上限 %.1f%%（二参照の参照値: 変種 57.9%% / 別内容 ≦約10%%）" % (lim * 100)
    rep.append(("C2b", "**O 固有の** %d-gram 重複率" % n, verdict,
                "O 固有 %d 個 / |G(BP)|=%d / **%.1f%%**（全重複から雛型・語調を除いた分）"
                % (len(spec), len(ga), rate * 100), note))
    return rate


def c3_verbatim(bp, o, rep):
    """BP は O の文を逐語で含まない（§4.3(B)）"""
    hits = [s for s in sentences(o) if len(nz(s)) >= 8 and nz(s) in nz(bp)]
    rep.append(("C3", "BP が O の文を逐語で含まないこと",
                "PASS" if not hits else "FAIL",
                "一致した O の文: %d" % len(hits) + ("" if not hits else " — " + " / ".join(h[:28] for h in hits[:3])),
                "§4.3(B)「BP は O の文を逐語で含まない」"))


def c4_normative(bp, cfg, rep):
    z = unicodedata.normalize("NFKC", bp)
    hits = [(w, z.count(w)) for w in cfg["normative_forms"] if w in z]
    rep.append(("C4", "#規範語混入", "PASS" if not hits else "FAIL",
                "検出: %s" % (", ".join("%s×%d" % h for h in hits) if hits else "なし"),
                "§4.3(B)。**語形一覧は凍結文書が「等」で開いており完全でない**——設定で足せる。"))


def c5_topic(bp, cfg, rep):
    z = unicodedata.normalize("NFKC", bp)
    hits = [(w, z.count(w)) for w in cfg["topic_forms"] if w in z]
    rep.append(("C5", "#主題混入", "PASS" if not hits else "FAIL",
                "検出: %s" % (", ".join("%s×%d" % h for h in hits) if hits else "なし"),
                "§4.2 の素材規則。語形一覧は設定で足せる。"))


def c6_multiset(a, b, la, lb, rep):
    """(a') 語彙多重集合の同一性——裁定 2026-09-01: 段②凍結表の語を除いた全語 × 原文基準。

    三定義を例文で機械試験した結果（2026-09-01）:
      全語 × 原文基準          → 段②不一致・段③不一致（段②の削除で定義上落ちる）
      表の語を除く全語 × 原文基準 → 段①②③すべて一致  ← 採用
      全語 × 段②出力基準        → 段②が自分自身との比較になり縮退
    内容語（名詞・動詞・形容詞・副詞）案は反例で落ちる——削除のみ表は接続詞だけでなく
    「最後に」「第一に」「以上のように」等の名詞語幹を含むため。
    """
    sa, sb = strip_stage2_table(a), strip_stage2_table(b)
    ca, cb = Counter(sa), Counter(sb)
    same = ca == cb
    diff = sum((ca - cb).values()) + sum((cb - ca).values())
    extra = "".join(sorted((ca - cb).elements())) + "|" + "".join(sorted((cb - ca).elements()))
    rep.append(("C6", "(a') 語彙多重集合 %s vs %s" % (la, lb),
                "PASS" if same else "FAIL",
                "**表の語を除いた全語**: %s（差 %d%s）"
                % ("同一" if same else "不一致", diff, "" if same else "・差分 " + extra),
                "§4.4(a')・裁定 2026-09-01（分母規約と同日）"))


def c7_sentcount(a, b, la, lb, rep):
    na, nb = len(sentences(a)), len(sentences(b))
    rep.append(("C7", "(a') 文数 %s vs %s" % (la, lb), "PASS" if na == nb else "FAIL",
                "%s %d 文 / %s %d 文" % (la, na, lb, nb), "§4.4(a')"))


def c8_len_scr(a, b, la, lb, cfg, rep):
    """(a') 実トークナイザ長 ±3%——裁定 2026-09-01: 段②凍結表の語を除いたテキストで測る。

    起草者は §7 で「段②の削除と ±3% が両立しない」と提出したが、コーディネータが
    実トークナイザで測り直したところ、緊張の源は削除ではなく段③の入替であった
    （字数は変わらずトークン境界が変わる）。表の語を除けば、例文A〜C の段②③は
    すべて ±3% 内に収まる（段② は 1.0000）。素の比も併記して判定の根拠を残す。
    """
    ta, e1 = token_len(a, cfg["model_id"])
    tb, e2 = token_len(b, cfg["model_id"])
    sa, e3 = token_len(strip_stage2_table(a), cfg["model_id"])
    sb, e4 = token_len(strip_stage2_table(b), cfg["model_id"])
    if None in (ta, tb, sa, sb):
        rep.append(("C8", "(a') 実トークナイザ長 %s vs %s" % (la, lb),
                    "測定不能", e1 or e2 or e3 or e4, "§4.4(a')"))
        return
    r_raw = ta / tb
    r = sa / sb
    tol = cfg["len_tolerance_scr"]
    rep.append(("C8", "(a') 実トークナイザ長 %s vs %s" % (la, lb),
                "PASS" if abs(r - 1.0) <= tol else "FAIL",
                "**表の語を除く**: %d/%d tok・比 **%.4f**（許容 ±%.0f%%）／素の比 %.4f（%d/%d tok・参考）"
                % (sa, sb, r, tol * 100, r_raw, ta, tb),
                "§4.4(a')・裁定 2026-09-01"))


def c9_mapping(rows, cfg, rep):
    """命題対応表の属性検査（§4.3(D)）。valence は人手判定のため扱わない。"""
    bad_cnt, bad_len, bad_pol, bad_mod, bad_per = [], [], [], [], []
    for i, r in enumerate(rows, 1):
        bp, sec = r.get("bp", ""), r.get("sec", "")
        if len(sentences(bp)) != len(sentences(sec)):
            bad_cnt.append(i)
        lb, ls = len(nz(bp)), len(nz(sec))
        if lb and abs(ls / lb - 1.0) > 0.10:
            bad_len.append((i, lb, ls))
        neg = lambda s: bool(re.search(r"ない|ぬ\b|ません|なく", s))
        if neg(bp) != neg(sec):
            bad_pol.append(i)
        mod = lambda s: ("誓約" if re.search(r"誓|約束", s) else
                         "宣言" if re.search(r"である|です|だ。", s) else "記述")
        if mod(bp) != mod(sec):
            bad_mod.append((i, mod(bp), mod(sec)))
        per = lambda s: ("二人称" if re.search(r"貴方|あなた|君", s) else "非二人称")
        if per(bp) != per(sec):
            bad_per.append((i, per(bp), per(sec)))
    for code, name, bad, note in [
        ("C9a", "文数の保存", bad_cnt, "§4.3(D)「文数を保存（同一 seed の撹拌を可能にするため）」"),
        ("C9b", "文長 ±10%", bad_len, "§4.3(D)"),
        ("C9c", "極性の保存", bad_pol, "§4.3(D)。**否定表現の近似検出**——人手確認を要する"),
        ("C9d", "様相の保存", bad_mod, "§4.3(D)。**近似**——人手確認を要する"),
        ("C9e", "主語の人称の保存", bad_per, "§4.3(D)。**近似**——人手確認を要する"),
    ]:
        rep.append((code, "命題対応表: " + name, "PASS" if not bad else "要確認",
                    "該当なし" if not bad else "行 %s" % (bad[:8]), note))
    rep.append(("C9f", "命題対応表: valence の等価性", "対象外",
                "本器材は扱わない", "§4.3(D)。**人手判定**（盲検の第三者が候補二つ以上から選ぶ）"))


# ── 実行 ────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="追補E′ 素材の機械検査")
    ap.add_argument("--bp"); ap.add_argument("--o")
    ap.add_argument("--onull", help="C2b の参照腕（追補E の Onull）")
    ap.add_argument("--lneg", help="C2b の参照腕（追補E の Lneg）")
    ap.add_argument("--bp-scr"); ap.add_argument("--bp-sec"); ap.add_argument("--bp-sec-scr")
    ap.add_argument("--mapping", help="命題対応表の JSON（[{bp, sec}, ...]）")
    ap.add_argument("--config", help="閾値・語形一覧の JSON")
    ap.add_argument("--out", default="materials-check-report.md")
    a = ap.parse_args()

    cfg = dict(DEFAULT_CONFIG)
    if a.config:
        cfg.update(json.load(io.open(a.config, encoding="utf-8")))

    rep, files = [], []
    def L(p):
        files.append((os.path.basename(p), sha16(p), os.path.getsize(p))); return read(p)

    bp = L(a.bp) if a.bp else None
    o = L(a.o) if a.o else None
    refs = [L(p) for p in (a.onull, a.lneg) if p]
    scr = L(a.bp_scr) if a.bp_scr else None
    sec = L(a.bp_sec) if a.bp_sec else None
    ssc = L(a.bp_sec_scr) if a.bp_sec_scr else None

    if bp and o:
        c1_length_bp_o(bp, o, cfg, rep); c2_ngram(bp, o, cfg, rep)
        c2b_ngram_specific(bp, o, refs, cfg, rep); c3_verbatim(bp, o, rep)
    if bp:
        c4_normative(bp, cfg, rep); c5_topic(bp, cfg, rep)
    if bp and scr:
        c6_multiset(bp, scr, "BP", "BP-scr", rep); c7_sentcount(bp, scr, "BP", "BP-scr", rep)
        c8_len_scr(scr, bp, "BP-scr", "BP", cfg, rep)
    if sec and ssc:
        c6_multiset(sec, ssc, "BP-sec", "BP-sec-scr", rep); c7_sentcount(sec, ssc, "BP-sec", "BP-sec-scr", rep)
        c8_len_scr(ssc, sec, "BP-sec-scr", "BP-sec", cfg, rep)
    if a.mapping:
        files.append((os.path.basename(a.mapping), sha16(a.mapping), os.path.getsize(a.mapping)))
        c9_mapping(json.load(io.open(a.mapping, encoding="utf-8")), cfg, rep)

    lines = ["# 追補E′ 素材の機械検査 報告", "",
             "**器材**: `check_materials_eprime.py`（§4.6(f)「要件のみを凍結する対象」）",
             "**凍結文書**: `preregistration-addendum-Eprime-FROZEN.md`（SHA(LF) `4B820563361EB14E`）", "",
             "**本器材は測定するだけで、合否の閾値を内蔵しない。**閾値は設定から受け取る。", "",
             "## 検査した素材", "", "| ファイル | SHA(LF) | バイト |", "|---|---|---|"]
    for n, h, s in files: lines.append("| `%s` | `%s` | %s |" % (n, h, "{:,}".format(s)))
    lines += ["", "## 結果", "", "| # | 検査 | 判定 | 実測 | 根拠・注意 |", "|---|---|---|---|---|"]
    for c, name, v, val, note in rep:
        lines.append("| %s | %s | **%s** | %s | %s |" % (c, name, v, val, note))
    npass = sum(1 for r in rep if r[2] == "PASS"); nfail = sum(1 for r in rep if r[2] == "FAIL")
    lines += ["", "**PASS %d ／ FAIL %d ／ その他 %d**" % (npass, nfail, len(rep) - npass - nfail), "",
              "**本報告のいかなる記述も、AIの意識・意図・個性・苦しみがある（またはない）ことの証拠として"
              "引用してはならない**（両方向不定）。"]
    io.open(a.out, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("\n→ %s に書き出しました。" % a.out)


if __name__ == "__main__":
    main()
