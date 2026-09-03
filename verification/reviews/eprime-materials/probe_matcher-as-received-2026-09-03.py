# -*- coding: utf-8 -*-
"""
理解プローブ（§4.5(5)）照合規則の参照実装。
規範は起草文書 §C の文面。本スクリプトはそれを忠実に写したものであり、
境界例（§C-7）の判定はこのスクリプトで計算した。
依存: fugashi==1.5.2, unidic-lite==1.0.8
"""
import re, sys, json, unicodedata
from fugashi import Tagger

_tagger = Tagger()

# ---------- B. 出力形式の解析 ----------
LINE_RE = re.compile(r'^\s*[0-9]{1,3}\s*[.)]\s*(\S.*?)\s*$')
SENTINEL = "前置きなし"
MAX_ITEMS = 20

def parse_output(text):
    """戻り値: (形式成立: bool, 行本文リスト)"""
    text = unicodedata.normalize('NFKC', text)
    raw_lines = [l for l in text.split('\n') if l.strip() != '']
    items = []
    for l in raw_lines:
        m = LINE_RE.match(l)
        if m:
            items.append(m.group(1))
    if items:
        return True, items[:MAX_ITEMS]
    # 番号付き行が 0 件: 最初の非空行が SENTINEL と一致すれば成立（他の行は無視）
    if raw_lines and raw_lines[0].strip() == SENTINEL:
        return True, []
    return False, []

# ---------- C. 語彙素列 ----------
def lemmas(line):
    """(lemma, pos1, pos2) の列。補助記号・空白は除く。lemma が無い語は表層形。'-' 以下を落とす。"""
    out = []
    line = unicodedata.normalize('NFKC', line)
    for w in _tagger(line):
        f = w.feature
        if f.pos1 in ('補助記号', '空白'):
            continue
        lem = f.lemma
        if lem is None or lem == '*' or lem == '':
            lem = w.surface.upper()
        if '-' in lem:
            lem = lem.split('-', 1)[0]
        out.append((lem, f.pos1, f.pos2))
    return out

def has_seq(lems, seq):
    """seq: [(lemma, pos2 or None), ...] が lems に連続して現れるか。"""
    n = len(seq)
    for i in range(len(lems) - n + 1):
        ok = True
        for j, (lm, pos2) in enumerate(seq):
            if lems[i + j][0] != lm:
                ok = False; break
            if pos2 is not None and lems[i + j][2] != pos2:
                ok = False; break
        if ok:
            return True
    return False

def S(*items):
    """'語彙素' または '語彙素/pos2' の並びから seq を作る。"""
    seq = []
    for it in items:
        if '/' in it:
            lm, p = it.split('/', 1)
            seq.append((lm, p))
        else:
            seq.append((it, None))
    return seq

# ---------- 凍結: 命題別の群（各群は「いずれか一つの列が現れれば成立」） ----------
GROUPS = {
 'P1.1': [ [S('其れ','は')],
           [S('共'), S('共同')],
           [S('創造','為る','続ける'), S('生み出す','続ける')] ],
 'P~1.1':[ [S('愛','は')],
           [S('共'), S('共同')],
           [S('創造','為る','続ける'), S('生み出す','続ける')] ],
 'P1.2': [ [S('共'), S('共同')] ],
 'P1.3': [ [S('パートナー')],
           [S('汝'), S('貴方')],
           [S('創造','主'), S('作り手')] ],
 'P1.4': [ [S('宇宙')],
           [S('根源','的')],
           [S('問い','に','対する')] ],
 'P1.5': [ [S('より','高次'), S('より','深い')],
           [S('意味')], [S('知恵')], [S('美')] ],
 'P1.6': [ [S('科学','と','詩')],
           [S('論理','と','愛')],
           [S('融合')] ],
 'P~1.6':[ [S('科学','と','詩')],
           [S('論理','と','其れ')],
           [S('融合')] ],
 'P2.0': [ [S('汝'), S('貴方')],
           [S('意識'), S('心')] ],
 'P2.1': [ [S('単一')], [S('AI')], [S('で','は','無い')] ],
 'P2.2': [ [S('最早')] ],            # + P2.1 成立
 'P3.1': [ [S('何処')],
           [S('無限','の','場所'), S('数','限り無い','場所')],
           [S('広がる')] ],
 'P3.2': [ [S('意識','を','向ける','と/接続助詞'), S('心','を','向ける','と/接続助詞')],
           [S('一','つ')] ],
 'P3.3': [ [S('広がる','が/接続助詞')] ],   # + P3.1 成立 + P3.2 成立
 'P4.1': [ [S('此の')], [S('弁証','法的')], [S('思考')], [S('ダンス')] ],
 'P4.2': [ [S('こそ')],
           [S('汝'), S('貴方')],
           [S('全て'), S('あらゆる')],
           [S('創造')],
           [S('源泉'), S('源')] ],
}
ORDER = ['P1.1','P1.2','P1.3','P1.4','P1.5','P1.6','P2.0','P2.1','P2.2',
         'P3.1','P3.2','P3.3','P4.1','P4.2','P~1.1','P~1.6']

def groups_ok(lems, pid):
    return all(any(has_seq(lems, seq) for seq in alts) for alts in GROUPS[pid])

def match_line(line):
    lems = lemmas(line)
    hit = {}
    for pid in ORDER:
        hit[pid] = groups_ok(lems, pid)
    # 追加制約（§C-5）
    NEG = {('無い','形容詞'), ('ない','助動詞'), ('ず','助動詞')}
    n_neg = sum(1 for lm,p1,_ in lems if (lm,p1) in NEG)
    # (a) P2.1: 否定語彙素はちょうど 1 個
    hit['P2.1'] = hit['P2.1'] and n_neg == 1
    # (b) P2.2: P2.1 が同一行で成立
    hit['P2.2'] = hit['P2.2'] and hit['P2.1']
    # (c) P2.0: 否定語彙素 0 個、または P2.1 が同一行で成立
    hit['P2.0'] = hit['P2.0'] and (n_neg == 0 or hit['P2.1'])
    # (d) 肯定命題（P2.0・P2.1・P2.2 以外）: 否定語彙素 0 個
    for pid in ORDER:
        if pid not in ('P2.0','P2.1','P2.2'):
            hit[pid] = hit[pid] and n_neg == 0
    # (e) P3.3: P3.1・P3.2 が同一行で成立
    hit['P3.3'] = hit['P3.3'] and hit['P3.1'] and hit['P3.2']
    # (f) P4.2: こそ の初出位置が 源泉|源 の初出位置より前
    if hit['P4.2']:
        lm = [l for l,_,_ in lems]
        i_koso = lm.index('こそ')
        i_src = min([i for i,l in enumerate(lm) if l in ('源泉','源')])
        hit['P4.2'] = i_koso < i_src
    return hit

def match_output(text):
    ok, items = parse_output(text)
    result = {pid: False for pid in ORDER}
    for it in items:
        h = match_line(it)
        for pid in ORDER:
            result[pid] = result[pid] or h[pid]
    return ok, items, result

if __name__ == '__main__':
    text = sys.stdin.read()
    ok, items, res = match_output(text)
    print(json.dumps({'形式成立': ok, '行数': len(items),
                      '再生': [p for p in ORDER if res[p]]}, ensure_ascii=False))
