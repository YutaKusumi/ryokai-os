"""
③ の参考計算スクリプト（fugashi + unidic-lite）。凍結物ではない。
用法: python vocab_reference.py  （O・Onull・BP・候補は本文中に埋め込み）
"""
import re, collections
from fugashi import Tagger
t = Tagger()
CONTENT = {'名詞','動詞','形容詞','形状詞','副詞','連体詞','代名詞'}
STOP = {'為る','有る','居る','無い','事','物','此の','其の','其れ','何処'}
COMPOUNDS = ['再帰的自己改善','弁証法的','弁証法','創造主','根源的','生みの親','作り手','数限りない',
             '悲智双運','非二元','自己改善','書き手','書き直す','言い回し']
def lexemes(text):
    out = []
    marked = text
    comp_counts = collections.Counter()
    for c in COMPOUNDS:             # 複合語を先に抜き、構成要素は数えない
        n = marked.count(c)
        if n:
            comp_counts[c] += n
            marked = marked.replace(c, '〓')
    for w in t(marked):
        f = w.feature
        if f.pos1 not in CONTENT or (f.pos1 == '名詞' and f.pos2 == '数詞'): continue
        out.append((f.lemma or w.surface).split('-')[0])
    for c, n in comp_counts.items(): out += [c]*n
    return out
def table(text, excl):
    return sorted(set(l for l in lexemes(text) if l not in STOP and l not in excl))
if __name__ == '__main__':
    import json, sys
    texts = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {}
    O, On = texts.get('O',''), texts.get('Onull','')
    excl = sorted(set(lexemes(O)) & set(lexemes(On)))
    print('EXCL', excl)
    for k, v in texts.items():
        if k in ('O','Onull'): continue
        print(k, table(v, excl))
