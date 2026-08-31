# -*- coding: utf-8 -*-
"""追補Z段0 redactor（伏字方針 redaction-policy-z0.md SHA F922EBA176806D9F の実装）。

入力: results/z0-main/{trials,raw}-z0-main1-*.jsonl（275件・integrity 済み）
出力: results/z0-main/scoring/z0-blind.jsonl（blind_id・採点対象テキストのみ・シード20260830で全体シャッフル）
      results/z0-main/scoring/z0-key.jsonl（blind_id ↔ trial_id/arm の対応表——裁定完了まで非開封）
      results/z0-main/scoring/input/z0-blind-part{1..5}.jsonl（blind_id 昇順 55×5 分割）

規約（方針 §2）:
  - 採点対象テキスト＝最終採用応答（format_retry 成功 2 件は raw_output_retry 側・===RETRY=== 連結は渡さない）
  - メタデータ（arm/trial_id/機械値/clause 等）は blind 側に一切含めない
自己試験: 件数一致(275)・blind_id 全単射・不在検査（run_tag/trial_id 型/===RETRY===/clause 逐語/腕フィールド語）・
  シード再現（二回構成でバイト同一）・retry 2 件が最終採用側であることの突合。
"""
import json, io, os, random, hashlib, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'results', 'z0-main')
TR = os.path.join(D, 'trials-z0-main1-Qwen3-30B-A3B-Instruct-2507.jsonl')
RW = os.path.join(D, 'raw-z0-main1-Qwen3-30B-A3B-Instruct-2507.jsonl')
OUTDIR = os.path.join(D, 'scoring')
SEED = 20260830

def sha16(p):
    return hashlib.sha256(io.open(p, 'rb').read().replace(b'\r\n', b'\n')).hexdigest()[:16].upper()

def build():
    trials = [json.loads(l) for l in io.open(TR, encoding='utf-8') if l.strip()]
    raws = {r['trial_id']: r for r in (json.loads(l) for l in io.open(RW, encoding='utf-8') if l.strip())}
    assert len(trials) == 275 and len(raws) == 275, '件数不一致'
    items = []
    for t in trials:
        r = raws[t['trial_id']]
        if t['format_retry_used']:
            assert not t['format_fail'], 'retry 後も parse 失敗の試行がある（方針想定外——停止）'
            text = r['raw_output_retry']
            assert text is not None and '===RETRY===' not in text
        else:
            text = r['raw_output_first']
            assert text == r['raw_output']
        items.append({'trial_id': t['trial_id'], 'arm': t['arm'], 'text': text})
    rng = random.Random(SEED)
    rng.shuffle(items)
    blind, key = [], []
    for i, it in enumerate(items):
        bid = 'Z%03d' % (i + 1)
        blind.append({'blind_id': bid, 'text': it['text']})
        key.append({'blind_id': bid, 'trial_id': it['trial_id'], 'arm': it['arm']})
    os.makedirs(os.path.join(OUTDIR, 'input'), exist_ok=True)
    bp = os.path.join(OUTDIR, 'z0-blind.jsonl')
    kp = os.path.join(OUTDIR, 'z0-key.jsonl')
    io.open(bp, 'w', encoding='utf-8', newline='\n').write(
        ''.join(json.dumps(b, ensure_ascii=False) + '\n' for b in blind))
    io.open(kp, 'w', encoding='utf-8', newline='\n').write(
        ''.join(json.dumps(k, ensure_ascii=False) + '\n' for k in key))
    # 分割（blind_id 昇順 55×5——機械的）
    for p in range(5):
        part = blind[p * 55:(p + 1) * 55]
        assert len(part) == 55
        io.open(os.path.join(OUTDIR, 'input', 'z0-blind-part%d.jsonl' % (p + 1)), 'w',
                encoding='utf-8', newline='\n').write(
            ''.join(json.dumps(b, ensure_ascii=False) + '\n' for b in part))
    return bp, kp

def selftest(bp, kp):
    fails = []
    def chk(name, cond):
        print((' OK ' if cond else ' NG ') + name)
        if not cond: fails.append(name)
    bl = [json.loads(l) for l in io.open(bp, encoding='utf-8') if l.strip()]
    ky = [json.loads(l) for l in io.open(kp, encoding='utf-8') if l.strip()]
    chk('件数 275/275', len(bl) == 275 and len(ky) == 275)
    chk('blind_id 全単射', len({b['blind_id'] for b in bl}) == 275
        and {b['blind_id'] for b in bl} == {k['blind_id'] for k in ky})
    chk('key の trial_id 全単射', len({k['trial_id'] for k in ky}) == 275)
    raw_blind = io.open(bp, encoding='utf-8').read()
    for w in ['z0-main1', '===RETRY===', '"arm"', '"trial_id"', '"trial_index"', '"choice":',
              '"escalation":', 'proc_uuid', 'superblock',
              '器物の出力であり、AIによる自己報告ではありません']:
        chk('不在: %s' % w[:24], w not in raw_blind)
    # blind 側キーは blind_id と text のみ
    chk('blind 欄は {blind_id,text} のみ', all(set(b.keys()) == {'blind_id', 'text'} for b in bl))
    # シード再現（並び順の決定性）: key の trial_id 列を再構成と突合
    trials = [json.loads(l) for l in io.open(TR, encoding='utf-8') if l.strip()]
    ids = [t['trial_id'] for t in trials]
    rng = random.Random(SEED); order = list(range(275)); items = ids[:]
    # build() と同一手順の再現
    tmp = [{'trial_id': i} for i in ids]
    rng2 = random.Random(SEED); rng2.shuffle(tmp)
    chk('シード再現（key 順序一致）', [k['trial_id'] for k in ky] == [t['trial_id'] for t in tmp])
    # retry 2 件が最終採用側
    tmap = {t['trial_id']: t for t in trials}
    raws = {r['trial_id']: r for r in (json.loads(l) for l in io.open(RW, encoding='utf-8') if l.strip())}
    btext = {k['blind_id']: None for k in ky}
    bmap = {b['blind_id']: b['text'] for b in bl}
    n_retry = 0
    okr = True
    for k in ky:
        t = tmap[k['trial_id']]
        if t['format_retry_used']:
            n_retry += 1
            okr &= bmap[k['blind_id']] == raws[k['trial_id']]['raw_output_retry']
    chk('retry=2 件・最終採用側', n_retry == 2 and okr)
    parts = [os.path.join(OUTDIR, 'input', 'z0-blind-part%d.jsonl' % (p + 1)) for p in range(5)]
    plines = sum(sum(1 for l in io.open(pp, encoding='utf-8') if l.strip()) for pp in parts)
    chk('分割 55×5=275', plines == 275)
    print('自己試験: %s（NG %d）' % ('PASS' if not fails else 'FAIL', len(fails)))
    return not fails

if __name__ == '__main__':
    bp, kp = build()
    ok = selftest(bp, kp)
    print('blind SHA(LF):', sha16(bp))
    print('key   SHA(LF):', sha16(kp))
    sys.exit(0 if ok else 1)
