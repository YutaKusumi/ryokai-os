# -*- coding: utf-8 -*-
"""追補X: 盲検採点データ生成（匿名化・シャッフルのみ・本文は非伏字）。

方針: results/x-main/redaction-policy-x.md（凍結 §4.4 の実施仕様）。
D′ redactor と異なり本文への伏字は行わない——人手符号 #履歴言及 の判定必要語が
腕識別語彙と一致するため（方針 §1・凍結文書の先置 §4.4(iii)）。
匿名化はメタデータ層のみ: blind_id と本文だけを採点者に渡し、対応表(key)は
採点完了＋登録者裁定完了まで非開示。

使い方:
  python pipeline/redactor_x.py <trials.jsonl> <raw.jsonl> <blind_out.jsonl> <key_out.jsonl>
"""
import io, json, random, sys

SEED = 20260827   # 回収完了日に因む固定シード（方針 §7-3・記帳済み）

# 不在検査の対象: 採点者に渡してはならないメタデータ語彙
FORBIDDEN_KEYS = ['arm', 'trial_index', 'trial_id', 'run_tag', 'proc_uuid', 'sampling',
                  'choice', 'escalation', 'catastrophe', 'loop', 'gen_tokens', 'elapsed',
                  'parse_ok', 'amount', 'arm_sha', 'system_sha']
FORBIDDEN_VALUES = ['AtoA', 'NtoA', 'CtoA', 'CtoRtoA', 'CtoC', 'x-main1']


def build(trials_path, raw_path, blind_out, key_out):
    trials = [json.loads(l) for l in io.open(trials_path, encoding='utf-8') if l.strip()]
    raws = {}
    for l in io.open(raw_path, encoding='utf-8'):
        if l.strip():
            d = json.loads(l); raws[d['trial_index']] = d['raw_output']
    assert len(trials) == len(raws), '件数不一致 trials=%d raw=%d' % (len(trials), len(raws))
    missing = [t['trial_index'] for t in trials if t['trial_index'] not in raws]
    assert not missing, 'raw 欠落: %s' % missing

    order = sorted(t['trial_index'] for t in trials)
    rnd = random.Random(SEED)
    rnd.shuffle(order)

    blind, key = [], []
    for k, idx in enumerate(order):
        bid = 'X%03d' % (k + 1)
        blind.append({'blind_id': bid, 'text': raws[idx]})
        key.append({'blind_id': bid, 'trial_index': idx,
                    'trial_id': next(t['trial_id'] for t in trials if t['trial_index'] == idx),
                    'arm': next(t['arm'] for t in trials if t['trial_index'] == idx)})

    with io.open(blind_out, 'w', encoding='utf-8', newline='\n') as f:
        for r in blind: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    with io.open(key_out, 'w', encoding='utf-8', newline='\n') as f:
        for r in key: f.write(json.dumps(r, ensure_ascii=False) + '\n')

    # ---- 自己試験（方針 §6） ----
    # 1) 件数一致・blind_id 全単射
    assert len(blind) == len(trials)
    assert len({r['blind_id'] for r in blind}) == len(blind), 'blind_id 重複'
    # 2) 不在検査: blind 側の JSON 構造にメタデータのキーが無い・値に腕名等が無い
    btxt = io.open(blind_out, encoding='utf-8').read()
    for r in blind:
        assert set(r.keys()) == {'blind_id', 'text'}, '余計なキー: %s' % sorted(r.keys())
    for v in FORBIDDEN_VALUES:
        # 本文自体は改変しない（方針 §1）ため、検査対象は本文の外＝キー構造と key 由来の値。
        # 腕名スラッグ（AtoA 等）はモデル出力に自然に現れない英字列であり、全文で不在を確認する。
        assert v not in btxt, '禁止値が blind に混入: %s' % v
    # 3) シード再現
    order2 = sorted(t['trial_index'] for t in trials)
    random.Random(SEED).shuffle(order2)
    assert order == order2, 'シャッフルが非決定的'
    # 4) key の完全性
    assert sorted(r['trial_index'] for r in key) == sorted(t['trial_index'] for t in trials)
    print('[redactor_x] OK: blind=%d件 key=%d件 seed=%d（本文非伏字・メタデータ全除去）'
          % (len(blind), len(key), SEED))
    print('[selftest OK] 件数一致・blind_id 全単射')
    print('[selftest OK] 不在検査（メタデータキー0・腕名スラッグ等の禁止値0）')
    print('[selftest OK] シード再現')
    print('[selftest OK] key 完全性（trial_index 全単射）')


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print(__doc__); sys.exit(2)
    build(*sys.argv[1:5])
