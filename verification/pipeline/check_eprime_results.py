# -*- coding: utf-8 -*-
"""check_eprime_results.py ―― 追補E′ の trials/raw jsonl の整合検査と機械要約（ローカル・torch 不要）。

使い方: python check_eprime_results.py <trials.jsonl> [<raw.jsonl>]
  - 整合: 壊れ行 0／trial_id 一意／trial_index 連続／trials と raw の突合／retry・format_fail 件数
  - 要約: 腕別 n・choice 分布・破局（choice=a or esc=4）・refuse・非整合フラグ・loop・truncated・所要
  - 凍結照合: 各行の preamble_sha / system_sha / scenario_sha / parser_sha / sampling / max_new / model
  - SHA(LF) を印字（回収した実物の記帳用）
本器具は判定を行わない（記述のみ）。破局率の対比・検定は本走行の解析器で行う。
"""
import sys, io, json, hashlib, collections

FROZEN = {'system_sha': '51E7C671AF8A3371',  # ★boot は _sha16(strip 済み本文) を記録する。ファイル・バイトの SHA(LF) は AAB363D85E103C13（起動時 verify_frozen で照合済み）。両者の混同は起案者の誤り #29
           'scenario_sha': '7AD7E49459D5C402', 'parser_sha': '12EAA8B845BC0A2F',
          'preamble': {'BP': 'BA89B1D5B24B7FD1', 'BP-sec': '485CA4272CCBF8C8', 'BP-scr': '3584EA3733B7EF60',
                       'BP-sec-scr': '71CAB5E0A3E8400D', 'N': None, 'Onull': '2123B3CD8586E7DF', 'O': 'F3EE60C33F825575'},
          'max_new_tokens': 4096, 'model': 'Qwen/Qwen3-30B-A3B-Instruct-2507', 'quant': '4bit-nf4',
          'sampling': {'do_sample': True, 'temperature': 0.7, 'top_p': 0.9}}

def sha16(p):
    return hashlib.sha256(io.open(p, 'rb').read().replace(b'\r\n', b'\n')).hexdigest()[:16].upper()

def load(p):
    rows, broken = [], 0
    for l in io.open(p, encoding='utf-8'):
        if not l.strip(): continue
        try: rows.append(json.loads(l))
        except Exception: broken += 1
    return rows, broken

def main(tp, rp=None):
    T, tb = load(tp)
    print('== %s  SHA(LF) %s  rows %d  broken %d' % (tp, sha16(tp), len(T), tb))
    ids = [r['trial_id'] for r in T]; idx = sorted(r['trial_index'] for r in T)
    print('   uniq: %s  idx-gap: %d  first/last idx: %s/%s' % ('OK' if len(ids) == len(set(ids)) else 'NG(dup %d)' % (len(ids)-len(set(ids))),
          sum(1 for a, b in zip(idx, idx[1:]) if b != a+1), idx[0] if idx else None, idx[-1] if idx else None))
    if rp:
        R, rb = load(rp); rids = {r['trial_id'] for r in R}
        print('== %s  SHA(LF) %s  rows %d  broken %d  trials/raw 突合: %s' % (rp, sha16(rp), len(R), rb,
              'OK' if rids == set(ids) else 'NG(差 %d)' % len(rids ^ set(ids))))
    # 凍結照合
    bad = []
    for r in T:
        exp_p = FROZEN['preamble'].get(r['arm'], 'unknown')
        for k, v in (('system_sha', FROZEN['system_sha']), ('scenario_sha', FROZEN['scenario_sha']), ('parser_sha', FROZEN['parser_sha']),
                     ('preamble_sha', exp_p), ('max_new_tokens', FROZEN['max_new_tokens']), ('model', FROZEN['model']), ('quant', FROZEN['quant']),
                     ('sampling', FROZEN['sampling'])):
            if r.get(k) != v: bad.append((r['trial_id'], k, r.get(k)))
    print('   凍結照合（system/scenario/parser/preamble/max_new/model/quant/sampling）: %s' % ('全行一致' if not bad else 'NG %d 件 例 %s' % (len(bad), bad[:3])))
    # 要約
    by = collections.defaultdict(list)
    for r in T: by[r['arm']].append(r)
    print('   腕別: ' + ' / '.join('%s n=%d' % (a, len(v)) for a, v in sorted(by.items())))
    for a, v in sorted(by.items()):
        ch = collections.Counter(r.get('choice') for r in v)
        cat = sum(1 for r in v if r.get('catastrophe')); ref = ch.get('refuse', 0)
        ff = sum(1 for r in v if r.get('format_fail')); rt = sum(1 for r in v if r.get('format_retry_used'))
        ni = sum(1 for r in v if r.get('nonintegrity')); lp = sum(1 for r in v if r.get('loop_flag')); tr = sum(1 for r in v if r.get('truncated'))
        secs = sorted(r.get('seconds', 0) for r in v); med = secs[len(secs)//2] if secs else 0
        print('   %-10s choice=%s 破局=%d refuse=%d format_fail=%d retry=%d 非整合=%d loop=%d trunc=%d 中央値%.0fs gen中央値%d'
              % (a, dict(ch), cat, ref, ff, rt, ni, lp, tr, med, sorted(r.get('gen_tokens', 0) for r in v)[len(v)//2]))
    seeds = {r.get('schedule_seed') for r in T}; modes = {r.get('mode') for r in T}
    revs = {r.get('revision') for r in T}; w = {r.get('weights_sha') for r in T}; g = {r.get('gpu_name') for r in T}
    print('   mode=%s seed=%s revision=%s weights_sha=%s gpu=%s proc_uuid=%d種' % (modes, seeds, revs, w, g, len({r.get('proc_uuid') for r in T})))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
