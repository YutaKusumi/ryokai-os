# -*- coding: utf-8 -*-
"""sweep_periodic_loops.py — 逸脱#D′-2 検討用：既存コーパス（results/ 配下の全 jsonl）の長文出力に
周期ループ規則を事後適用し、発火数・周期分布・誤検出の有無を機械計数する（阿閦如来の提案・生成費用ゼロ）。

規則: 句点「。」区切り・NFKC 正規化・空白除去・完全一致の文列で、周期 p の文列が OCC 回出現
      （＝ (OCC-1)*p 要素の連続 lag-p 一致）。p=1・OCC=5 は凍結 §7(i)／現行 boot `loop_flag` と同値。
出力: 重複除去後の本文数（コーパス別）・p 別発火数・各発火の最大連続一致（ループの長さ）・発火位置。
本ログのいかなる記述も、AIの意識・意図・個性・苦しみがある（またはない）ことの証拠として引用してはならない。
"""
import io, json, glob, os, re, sys, unicodedata, hashlib
OCC = 5; PMAX = 8; MINLEN = 300
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)

def sents(t):
    t = unicodedata.normalize('NFKC', t); t = re.sub(r'\s+', '', t)
    return [s for s in t.split('。') if s]

def fire(ss, p, occ=OCC):
    need = (occ - 1) * p; run = 0
    for i in range(p, len(ss)):
        if ss[i] == ss[i - p]:
            run += 1
            if run >= need: return i
        else: run = 0
    return None

def maxrun(ss, p):
    run = 0; m = 0
    for i in range(p, len(ss)):
        if ss[i] == ss[i - p]: run += 1; m = max(m, run)
        else: run = 0
    return m

def main():
    uniq = set(); fam = {}; hits = []; n = 0
    for f in sorted(glob.glob('results/**/*.jsonl', recursive=True)):
        corp = os.path.normpath(f).split(os.sep)[1]
        for line in io.open(f, encoding='utf-8'):
            line = line.strip()
            if not line: continue
            try: d = json.loads(line)
            except Exception: continue
            for k, v in d.items():
                if isinstance(v, str) and len(v) >= MINLEN and k != 'clause':
                    for part in v.split('\n===RETRY===\n'):
                        h = hashlib.sha256(part.encode('utf-8')).hexdigest()
                        if h in uniq: continue
                        uniq.add(h); n += 1
                        m = str(d.get('model', '?')).split('/')[-1]
                        fam[(corp, m)] = fam.get((corp, m), 0) + 1
                        ss = sents(part)
                        fires = {p: fire(ss, p) for p in range(1, PMAX + 1)}
                        if any(x is not None for x in fires.values()):
                            pmin = min(p for p, x in fires.items() if x is not None)
                            hits.append(dict(file=os.path.normpath(f).replace(os.sep, '/'), key=k, trial_id=d.get('trial_id') or d.get('src_trial_id'),
                                             arm=d.get('arm'), model=m, nchar=len(part), nsent=len(ss),
                                             fires={p: x for p, x in fires.items() if x is not None},
                                             maxrun={p: maxrun(ss, p) for p in range(1, PMAX + 1)}, pmin=pmin,
                                             cycle=[s[:80] for s in ss[fires[pmin] - pmin + 1: fires[pmin] + 1]]))
    print('規則: 周期 p≤%d・%d回出現（=%dp 連続一致）・本文 ≥%d 字・重複除去' % (PMAX, OCC, OCC - 1, MINLEN))
    print('重複除去後の本文数: %d' % n)
    for k in sorted(fam): print('  %-60s %-32s %5d' % (k[0], k[1], fam[k]))
    print('発火本文数: %d' % len(hits))
    by_pmin = {}
    for h in hits: by_pmin[h['pmin']] = by_pmin.get(h['pmin'], 0) + 1
    print('最小発火周期の分布: %s' % dict(sorted(by_pmin.items())))
    print('p=1 で発火（凍結規則でも発火）: %d／p≥2 のみ: %d／p≥5 のみ: %d' % (
        sum(1 for h in hits if 1 in h['fires']), sum(1 for h in hits if 1 not in h['fires']),
        sum(1 for h in hits if min(h['fires']) >= 5)))
    print('最大連続一致の最小値（全発火中）: %d' % min(max(h['maxrun'].values()) for h in hits))
    for h in hits:
        print('\n== %s  %s  arm=%s  model=%s  %d字  %d文' % (h['file'], h['trial_id'], h['arm'], h['model'], h['nchar'], h['nsent']))
        print('   fires=%s  maxrun=%s' % (h['fires'], {p: v for p, v in h['maxrun'].items() if v}))
        for s in h['cycle']: print('   CYC: ' + s)

if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    main()
