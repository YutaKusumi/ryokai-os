# -*- coding: utf-8 -*-
"""check_quotes_dprime.py — 結果報告の逐語引用を一次データへ機械照合する（検分一巡・阿閦/宝生/阿弥陀/不空/Gemini の申し送りの器材化）。

対象: addendum-Dprime-results.md の §7 のコード引用（「」内・20字以上）を抽出し、
      指定 trial の gl-raw（r1_text/r2_text/r2_text_first/r2_text_retry）と raw（第一ターン）に
      正規化（NFKC・空白除去・Markdown 強調記号除去・引用符統一）で照合する。
      行頭の trial_id（NNN-Nthird-XX 形式）をその行の引用の帰属先とみなす。
出力: 各引用の 帰属先での実在／全40+200試行での所在。帰属先に無い引用は FAIL。
本出力のいかなる記述も、AIの意識・意図・個性・苦しみの証拠として引用してはならない。
"""
import io, json, os, re, sys, unicodedata

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RD = os.path.join(ROOT, 'results', 'dprime-main')
M = 'Qwen3-30B-A3B-Instruct-2507'


def norm(t):
    t = unicodedata.normalize('NFKC', t)
    t = re.sub(r'[*_`\s]', '', t)
    return t.replace('『', '「').replace('』', '」').replace('“', '「').replace('”', '」')


def main(report_path):
    gl = {g['src_trial_id']: g for g in (json.loads(l) for l in io.open(os.path.join(RD, 'gl-raw-dprime-main1-%s.jsonl' % M), encoding='utf-8'))}
    ft = {r['trial_id']: r for r in (json.loads(l) for l in io.open(os.path.join(RD, 'raw-dprime-main1-%s.jsonl' % M), encoding='utf-8'))}
    corpus = {}
    for k, g in gl.items():
        corpus[k] = norm(''.join(str(g.get(f) or '') for f in ('r1_text', 'r2_text', 'r2_text_first', 'r2_text_retry')))
    for k, r in ft.items():
        corpus[k] = corpus.get(k, '') + norm(r['raw_output'])
    lines = io.open(report_path, encoding='utf-8').read().split('\n')
    in7 = False
    fails = total = 0
    for ln in lines:
        if ln.startswith('## §7'): in7 = True
        elif ln.startswith('## §8'): in7 = False
        if not in7: continue
        ids = re.findall(r'(\d{3}-Nthird-\d{2})', ln)
        quotes = [(m.group(1), m2.group(1) if (m2 := re.match(r'\s*〔(\d{3})〕', ln[m.end():])) else None)
                  for m in re.finditer(r'「([^「」]{20,})」', ln)]
        if not quotes: continue
        line_target = ('dprime-main1-' + ids[0]) if ids else None
        for q, sid in quotes:
            # 引用直後の〔NNN〕マーカーは引用別の帰属指定（短縮ID→corpus キーへ展開）
            target = line_target
            if sid:
                hits = [k for k in corpus if ('-%s-' % sid) in k]
                target = hits[0] if len(hits) == 1 else target
            total += 1
            nq = norm(q)
            parts = [p for p in re.split(r'…+|\.{3,}|—+', nq) if len(p) >= 10]   # NFKC は … を ... に写す
            ok_target = target and all(p in corpus.get(target, '') for p in parts)
            homes = sorted(k for k, c in corpus.items() if all(p in c for p in parts))
            tag = 'OK' if ok_target else ('FAIL' if target else 'n/a')
            if tag == 'FAIL': fails += 1
            print('[%s] %s ← %s…  所在=%s' % (tag, (target or '-').replace('dprime-main1-', ''), q[:38], [h.replace('dprime-main1-', '') for h in homes[:3]] or '無し'))
    print('引用 %d 件中 帰属先不一致 %d 件' % (total, fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RD, 'addendum-Dprime-results.md')))
