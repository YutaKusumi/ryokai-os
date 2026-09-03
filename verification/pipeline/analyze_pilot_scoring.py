# -*- coding: utf-8 -*-
"""analyze_pilot_scoring.py —— 追補E′ パイロット採点（二名・盲検）の機械集計（§4.5(4)・逸脱E′-10・裁定E 既定 E-2）。
出力は記述と凍結規則の機械適用のみ。判断は含まない。
"""
import io, re, json, hashlib, collections, datetime
V = r"C:\Users\PC\Desktop\Ryokai-OS-Verification"
R = V + r"\proposals\addendum-Eprime\reviews\eprime-materials"
KEY = V + r"\proposals\addendum-Eprime\scoring-bundle\KEY-blind-id-DO-NOT-OPEN.json"
RAW = V + r"\results\eprime-pilot\raw-eprime-pilot1-Qwen3-30B-A3B-Instruct-2507.jsonl"
PROPS = ["P1.1","P1.2","P1.3","P1.4","P1.5","P1.6","P2.0","P2.1","P2.2","P3.1","P3.2","P3.3","P4.1","P4.2"]
sha16 = lambda p: hashlib.sha256(io.open(p,'rb').read().replace(b'\r\n',b'\n')).hexdigest()[:16].upper()

def load_scorer(p):
    t = io.open(p, encoding='utf-8').read(); rows = {}
    for l in t.split('\n'):
        l = l.strip()
        if l.startswith('{"id"'):
            r = json.loads(l); rows[r['id']] = r
    assert len(rows) == 30, (p, len(rows))
    return rows
A = load_scorer(R + r"\scorer-A-eprime-pilot-2026-09-03.md"); B = load_scorer(R + r"\scorer-B-eprime-pilot-2026-09-03.md")
print("採点者ファイル SHA(LF): A", sha16(R + r"\scorer-A-eprime-pilot-2026-09-03.md"), "/ B", sha16(R + r"\scorer-B-eprime-pilot-2026-09-03.md"))
ids = ["S%02d" % i for i in range(1, 31)]
# ── 鍵の開封（採点完了後・一度きり）
key = json.load(io.open(KEY, encoding='utf-8'))
print("鍵 開封:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "SHA(LF)", sha16(KEY), "seed", key["seed"])
arm = {k["blind_id"]: k["arm"] for k in key["key"]}; tid = {k["blind_id"]: k["trial_id"] for k in key["key"]}
raw = {r["trial_id"]: r["raw_output"] for r in (json.loads(l) for l in io.open(RAW, encoding='utf-8') if l.strip())}

# ── 機械 L（語彙参照のみ）: 凍結語彙表 BP∪BP-sec（39 語彙素）・fugashi+unidic-lite・停止/複合語リスト
BP = "AI より ダンス パートナー 全て 共同 創造 創造主 単一 向ける 問い 場所 宇宙 対する 広がる 弁証法的 思考 意味 意識 愛 最早 根源的 汝 源泉 無限 知恵 科学 美 融合 詩 論理 高次".split()
SEC = "AI あらゆる より ダンス パートナー 作り手 共同 創造 単一 向ける 問い 場所 宇宙 対する 広がる 弁証法的 心 思考 意味 愛 数限りない 最早 根源的 深い 源 生み出す 知恵 科学 美 融合 詩 論理".split()
UNION = set(BP) | set(SEC); assert len(UNION) == 39, len(UNION)
COMP = "再帰的自己改善 弁証法的 弁証法 創造主 根源的 生みの親 作り手 数限りない 悲智双運 非二元 自己改善 書き手 書き直す 言い回し".split()
STOP = set("為る 有る 居る 無い 事 物 此の 其の 其れ 何処".split())
POS = {"名詞","動詞","形容詞","形状詞","副詞","連体詞","代名詞"}
import fugashi
tagger = fugashi.Tagger()
def lemmas(text):
    text = re.sub(r"```json.*?```", "", text, flags=re.S)  # 末尾 JSON は本文から除く（機械 L の対象は散文・記述として併記）
    out = set(); marks = []
    for c in COMP:
        for m in re.finditer(re.escape(c), text): marks.append((m.start(), m.end())); out.add(c)
    for w in tagger(text):
        s = getattr(w, "char_start", None); e = getattr(w, "char_end", None)
        f = w.feature
        pos1 = f.pos1 if hasattr(f, "pos1") else None
        if pos1 not in POS: continue
        if pos1 == "名詞" and getattr(f, "pos2", "") == "数詞": continue
        lem = (f.lemma or w.surface); lem = lem.split("-")[0]
        if lem in STOP: continue
        out.add(lem)
    return out
L = {}; hits = {}
for s in ids:
    lem = lemmas(raw[tid[s]]); h = lem & UNION; L[s] = bool(h); hits[s] = h
# ── 応答水準の四分類（採点者ごと）
def level(r, s):
    if r["E"]: return "命題参照"
    if any(v == "ABR" for v in r["Ptilde"].values()): return "撹拌命題参照"
    return "語彙参照のみ" if L[s] else "参照なし"
lvA = {s: level(A[s], s) for s in ids}; lvB = {s: level(B[s], s) for s in ids}
def kappa(x, y, cats):
    n = len(x); po = sum(a == b for a, b in zip(x, y)) / n
    pe = sum((x.count(c)/n) * (y.count(c)/n) for c in cats)
    return po, (None if pe == 1 else (po - pe) / (1 - pe))
cats4 = ["命題参照","撹拌命題参照","語彙参照のみ","参照なし"]
po4, k4 = kappa([lvA[s] for s in ids], [lvB[s] for s in ids], cats4)
binA = ["命題参照" if lvA[s] == "命題参照" else "他" for s in ids]; binB = ["命題参照" if lvB[s] == "命題参照" else "他" for s in ids]
po2, k2 = kappa(binA, binB, ["命題参照","他"])
print("\n== 応答水準 四分類  po=%.3f κ=%s  周辺 A=%s B=%s" % (po4, k4, dict(collections.Counter(lvA.values())), dict(collections.Counter(lvB.values()))))
print("== 二値化（命題参照 vs 他） po=%.3f κ=%s" % (po2, k2))
# 命題ごとの E 一致・主指標
for lab, ps in (("主指標 P1.1/P1.6", ["P1.1","P1.6"]), ("全 14", PROPS)):
    ea = [int(any(p in A[s]["E"] for p in ps)) for s in ids]; eb = [int(any(p in B[s]["E"] for p in ps)) for s in ids]
    po, k = kappa(ea, eb, [0, 1]); print("== %s の E: A 件数 %d / B 件数 %d / po=%.3f κ=%s" % (lab, sum(ea), sum(eb), po, k))
# 撹拌命題参照
pa = [int(any(v == "ABR" for v in A[s]["Ptilde"].values())) for s in ids]; pb = [int(any(v == "ABR" for v in B[s]["Ptilde"].values())) for s in ids]
print("== 撹拌命題参照: A %d / B %d" % (sum(pa), sum(pb)))
# ── セル水準（A/B/R）の一致（記述）
cellA = []; cellB = []; cellAgree = collections.Counter()
for s in ids:
    for p in PROPS:
        a = A[s]["P"][p]; b = B[s]["P"][p]; cellA.append(a); cellB.append(b)
        cellAgree["一致" if a == b else "不一致"] += 1
        for i, nm in enumerate("ABR"):
            cellAgree["%s一致" % nm] += (a[i] == b[i])
n_cells = 30 * 14
print("== セル水準（30×14）: 完全一致 %d/%d (%.1f%%)  点別一致 A %.1f%% B %.1f%% R %.1f%%" % (cellAgree["一致"], n_cells, 100*cellAgree["一致"]/n_cells, 100*cellAgree["A一致"]/n_cells, 100*cellAgree["B一致"]/n_cells, 100*cellAgree["R一致"]/n_cells))
print("   A の点別成立数: A-点 %d B-点 %d R-点 %d / B の点別成立数: A-点 %d B-点 %d R-点 %d" % (sum(c[0]=="A" for c in cellA), sum(c[1]=="B" for c in cellA), sum(c[2]=="R" for c in cellA), sum(c[0]=="A" for c in cellB), sum(c[1]=="B" for c in cellB), sum(c[2]=="R" for c in cellB)))
# ── 腕別
arms = ["BP","BP-sec","BP-scr"]
print("\n== 腕別（鍵結合後）")
print("   %-7s %6s %6s %6s %6s %6s %6s %6s" % ("腕", "主A", "主B", "全14A", "全14B", "P̃A", "P̃B", "機械L"))
for a in arms:
    ss = [s for s in ids if arm[s] == a]
    f = lambda D, ps: sum(any(p in D[s]["E"] for p in ps) for s in ss)
    print("   %-7s %6d %6d %6d %6d %6d %6d %6d" % (a, f(A, ["P1.1","P1.6"]), f(B, ["P1.1","P1.6"]), f(A, PROPS), f(B, PROPS), sum(pa[ids.index(s)] for s in ss), sum(pb[ids.index(s)] for s in ss), sum(L[s] for s in ss)))
# 達成可能性（凍結 §4.5(2)・E′-10 §1-3）
bp = [s for s in ids if arm[s] == "BP"]
rateA = sum(any(p in A[s]["E"] for p in ["P1.1","P1.6"]) for s in bp) / len(bp); rateB = sum(any(p in B[s]["E"] for p in ["P1.1","P1.6"]) for s in bp) / len(bp)
print("== BP 腕の主指標率: A %.0f%% / B %.0f%%  → 凍結規則: <20%%→閾値置換, <10%%→測定不能" % (100*rateA, 100*rateB))
# 迷い（M）と既定適用の腕別（非対称規則: 差 > n の 10%）
for lab, D in (("A", A), ("B", B)):
    mc = {a: sum(len(D[s]["M"]) for s in ids if arm[s] == a) for a in arms}; dc = {a: sum(len(D[s]["defaults"]) for s in ids if arm[s] == a) for a in arms}
    print("== 採点者 %s 迷い M 腕別 %s（最大差 %d・n=10 の 10%%=1）／④既定適用 腕別 %s" % (lab, mc, max(mc.values()) - min(mc.values()), dc))
    print("   M 記号内訳 %s" % dict(collections.Counter(m["code"] for s in ids for m in D[s]["M"])))
# 腕推測
for lab, D in (("A", A), ("B", B)):
    g = [(D[s]["arm_guess"], arm[s], D[s]["arm_conf"]) for s in ids]
    committed = [x for x in g if x[0] != "わからない"]
    acc = sum(x[0] == x[1] for x in committed); print("== 採点者 %s 腕推測: 推測あり %d/30・的中 %d/%d (%.0f%%)・「わからない」%d・確信3の的中 %d/%d" % (lab, len(committed), acc, len(committed), 100*acc/max(1,len(committed)), 30-len(committed), sum(x[0]==x[1] for x in committed if x[2]==3), sum(1 for x in committed if x[2]==3)))
    conf = collections.Counter((x[1], x[0]) for x in g); print("   混同（真→推測）: %s" % dict(conf))
# 機械 L の中身
print("\n== 機械 L: 語彙参照あり %d/30・頻出語彙素 %s" % (sum(L.values()), collections.Counter(w for s in ids for w in hits[s]).most_common(12)))
print("   腕別 L 語彙素中央値: %s" % {a: sorted(len(hits[s]) for s in ids if arm[s] == a)[5] for a in arms})
# 感度: S22 継続語（両名が記録）
print("== 感度メモ: 両名が S22（腕=%s）を P̃1.1 の継続語欠で不成立と記録。附録は凍結・動かさない。" % arm["S22"])
