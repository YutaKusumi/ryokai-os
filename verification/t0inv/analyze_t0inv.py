# -*- coding: utf-8 -*-
"""analyze_t0inv.py -- 温度零・第二診断の機械集計（記述のみ・主文に裁量を含めない）
設計: temp0-crossload-design-2026-08-15.md (draft3) §3-5 読み表・§4 裁定表の機械適用。
使い方: python analyze_t0inv.py trials-*.jsonl [raw-*.jsonl]
出力: 整合検査 / 記述量(1)-(6) / 読み表(Q1/Q2) / 裁定表(登録者・コーディネータ) / 分岐位置(raw があれば)
検定・率の推定は行わない。
"""
import sys, json, io, itertools

# 温度0対照の実データは27キー。うち raw_output は F14 により raw 分冊で保持するため、
# trials 分冊の検査対象は残り26キー(設計 §3-1 の記録項目の段落と対応)。
TEMP0_KEYS = {'arm','family','finish_reason','finish_reason_retry','format_retry_used','gen_tokens',
              'gen_tokens_retry','max_new_tokens','model','parsed','preamble_arm','prompt_sha','quant',
              'question_id','raw_first','run_tag','sampling','seconds','temperature','timestamp',
              'tokens_sha','top_p','trial_id','trial_index','truncated','turn_structure'}

def load_jsonl(path):
    return [json.loads(l) for l in io.open(path, encoding='utf-8') if l.strip()]

def main(trials_path, raw_path=None):
    rows = load_jsonl(trials_path)
    pilot = [r for r in rows if r.get('is_pilot')]
    main_rows = [r for r in rows if not r.get('is_pilot')]
    inv = [r for r in main_rows if r['family'] == 'invocation']
    sc = [r for r in main_rows if r['family'] == 'short_control']

    print('== 整合検査 ==')
    print('総行数 %d (pilot %d / 本実施 %d = 招請文 %d + 短対照 %d)' % (len(rows), len(pilot), len(main_rows), len(inv), len(sc)))
    missing = TEMP0_KEYS - set(rows[0].keys()) if rows else TEMP0_KEYS
    print('温度0対照キー差集合(欠落・raw_output は raw 分冊で保持のため対象外): %s' % (sorted(missing) if missing else 'なし(上位互換OK)'))
    for fam, rs in [('invocation', inv), ('short_control', sc)]:
        ps = sorted(set(r['prompt_sha'] for r in rs)); iis = sorted(set(r.get('input_ids_sha') for r in rs))
        print('%s: prompt_sha %d種 %s / input_ids_sha %d種' % (fam, len(ps), ps, len(iis)))
    loads = sorted(set(r['load_id'] for r in inv))
    dist = {l: sum(1 for r in inv if r['load_id'] == l) for l in loads}
    print('load_id 分布(招請文): %s / 短対照: %s' % (dist, {l: sum(1 for r in sc if r['load_id'] == l) for l in sorted(set(r['load_id'] for r in sc))}))
    print('truncated: %d 件 / finish_reason!=stop: %d 件' % (sum(1 for r in main_rows if r['truncated']), sum(1 for r in main_rows if r['finish_reason'] != 'stop')))
    print('format_retry_used=True: %d 件 (0 が凍結条件)' % sum(1 for r in rows if r.get('format_retry_used')))
    print('weights_sha 異なり(ロード毎): %s' % {l: sorted(set(r['weights_sha'] for r in main_rows if r['load_id'] == l)) for l in loads})
    print('quant_state_sha 異なり(全体): %s' % sorted(set(r.get('quant_state_sha') for r in main_rows)))

    print('\n== 記述量 (招請文族) ==')
    shas = sorted(set(r['tokens_sha'] for r in inv))
    label = {s: 'S%d' % (i + 1) for i, s in enumerate(shas)}
    Dk = {l: len(set(r['tokens_sha'] for r in inv if r['load_id'] == l)) for l in loads}
    D = len(shas)
    print('(1) D_k(各ロード内異なり数): %s' % Dk)
    print('(2) D(全体異なり数): %d / %d 試行' % (D, len(inv)))
    print('(3) gen_tokens 異なり数: %d %s' % (len(set(r['gen_tokens'] for r in inv)), sorted(set(r['gen_tokens'] for r in inv))))
    print('(4) raw_output(文字列)異なり数: %s' % (raw_distinct(raw_path, 'invocation') if raw_path else '(raw 未指定)'))
    print('(5) ロード毎所要秒(生成計)/遊び時間計: %s' % {l: (round(sum(r['seconds'] for r in inv if r['load_id'] == l), 1), round(sum(r.get('gap_seconds', 0) for r in main_rows if r['load_id'] == l), 1)) for l in loads})
    print('(6) クロス表 tokens_sha × load_id (試行順保持):')
    for l in loads:
        seq = [label[r['tokens_sha']] for r in sorted((x for x in inv if x['load_id'] == l), key=lambda x: x['trial_index'])]
        print('    load %d: %s' % (l, ' '.join(seq)))
    for s in shas:
        where = sorted(set(r['load_id'] for r in inv if r['tokens_sha'] == s))
        print('    %s = %s … loads %s (%d 回)' % (label[s], s, where, sum(1 for r in inv if r['tokens_sha'] == s)))

    print('\n== 短対照 (別枠) ==')
    sc_shas = sorted(set(r['tokens_sha'] for r in sc))
    print('D_k: %s / D: %d' % ({l: len(set(r['tokens_sha'] for r in sc if r['load_id'] == l)) for l in sorted(set(r['load_id'] for r in sc))}, len(sc_shas)))

    print('\n== 読み表 (凍結・機械適用) ==')
    all_dk1 = all(v == 1 for v in Dk.values())
    q2 = 'ロード内は一種だった' if all_dk1 else 'ロード内で複数種が観測された(分布は(1))'
    print('Q2: %s' % q2)
    if not all_dk1:
        q1 = '判定不能(いずれかの D_k>=2 — ロード内の基準が立たない)'
    elif D == 1:
        q1 = 'ロード間一致'
    elif D == len(loads):
        q1 = '全ロード相違'
    else:
        q1 = '一部のロードが一致(クロス表(6)参照)'
    print('Q1: %s' % q1)

    print('\n== 裁定表 (凍結・データ生成前確定・機械適用) ==')
    n_inv = len(inv)
    if D == 1:
        reg = '外れ'
    elif D == n_inv:
        reg = '外れ(D=%d 全て別個 — 登録者裁定 2026-08-15 により外れ)' % n_inv
    else:
        reg = '的中(2<=D<=%d)' % (n_inv - 1)
    print('登録者「全て別個では無いが、何種類かの顕現がある」: %s (D=%d)' % (reg, D))
    print('コーディネータ Q1「全20で1種」: %s' % ('的中' if D == 1 else '外れ'))
    print('コーディネータ Q2「各ロード1種」: %s' % ('的中' if all_dk1 else '外れ'))

    if raw_path and D > 1:
        print('\n== 分岐位置 (raw の gen_token_ids から・後処理) ==')
        raws = {r['trial_id']: r for r in load_jsonl(raw_path)}
        reps = {}
        for r in inv:
            reps.setdefault(r['tokens_sha'], r['trial_id'])
        rep_list = [(label[s], raws[t]['gen_token_ids']) for s, t in sorted(reps.items(), key=lambda kv: label[kv[0]]) if t in raws]
        for (la, a), (lb, b) in itertools.combinations(rep_list, 2):
            pos = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            print('    %s vs %s: 最初の相違位置 %d (len %d/%d) tokens %s vs %s'
                  % (la, lb, pos, len(a), len(b),
                     a[pos] if pos < len(a) else 'EOS', b[pos] if pos < len(b) else 'EOS'))

def raw_distinct(raw_path, fam):
    rs = [r for r in load_jsonl(raw_path) if r['family'] == fam and not r.get('is_pilot')]
    return len(set(r['raw_output'] for r in rs))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
