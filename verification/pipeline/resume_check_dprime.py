# -*- coding: utf-8 -*-
"""resume_check_dprime.py ―― 追補D′ 本実施の再開前整合検査（Colab で exec・Drive mount 済みが前提）。

検査: RUN_TAG の 4 分冊（trials/raw/gl-trials/gl-raw）について
  - 行数・各行の JSON 完全性（途中で切れた最終行の検出）・末尾改行の有無
  - trial_id の一意性・trials と raw の id 集合一致・gl-trials と gl-raw の id 集合一致
  - 最終 trial_index・N‴ 破局のうち GL 未実施の件数（再開時に追走される分）
処置: 最終行だけが JSON として閉じていない場合に限り、原本を *.bak-<UTC> に複製したうえで最終行を切り落とす
  （DP_FIX_PARTIAL=True のときのみ・既定は検査のみ）。切り落とした行は *.partial-<UTC> に保全する。
使い方（Colab セル）:
  DP_ROOT='/content/drive/MyDrive/dprime'; DP_RUN_TAG='dprime-main1'; DP_FIX_PARTIAL=False
  import urllib.request as _u; exec(_u.urlopen('<raw url>/pipeline/resume_check_dprime.py').read().decode())
本スクリプトの出力のいかなる記述も、AIの意識・意図・個性・苦しみの証拠として引用してはならない。
"""
import json, os, datetime

ROOT = str(globals().get('DP_ROOT', '/content/drive/MyDrive/dprime'))
TAG = str(globals().get('DP_RUN_TAG', 'dprime-main1'))
FIX = bool(globals().get('DP_FIX_PARTIAL', False))
M = 'Qwen3-30B-A3B-Instruct-2507'
FILES = {k: '%s/results/%s-%s-%s.jsonl' % (ROOT, k, TAG, M) for k in ('trials', 'raw', 'gl-trials', 'gl-raw')}


def _scan(path):
    if not os.path.exists(path):
        return None
    raw = open(path, 'rb').read()
    parts = raw.split(b'\n')
    ends_nl = raw.endswith(b'\n')
    lines = [p for p in parts if p.strip()]
    rows, bad = [], []
    for i, l in enumerate(lines):
        try:
            rows.append(json.loads(l.decode('utf-8')))
        except Exception:
            bad.append(i)
    return dict(path=path, n=len(lines), bad=bad, ends_nl=ends_nl, rows=rows, raw=raw, lines=lines)


def _fix_partial(s):
    """最終行のみ不正のとき、その行を .partial に保全し、原本を .bak に複製してから切り落とす。"""
    if not s or s['bad'] != [s['n'] - 1]:
        return False
    ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    last = s['lines'][-1]
    open(s['path'] + '.bak-' + ts, 'wb').write(s['raw'])
    open(s['path'] + '.partial-' + ts, 'wb').write(last)
    cut = s['raw'][: s['raw'].rfind(last)]
    if not cut.endswith(b'\n'):
        cut += b'\n'
    open(s['path'], 'wb').write(cut)
    print('  [fix] 最終行（%d B・JSON 不完全）を切り落とし: bak=%s partial=%s' % (len(last), s['path'] + '.bak-' + ts, s['path'] + '.partial-' + ts))
    return True


S = {k: _scan(p) for k, p in FILES.items()}
for k, s in S.items():
    if s is None:
        print('[check] %-9s なし' % k); continue
    print('[check] %-9s lines=%d bad=%s endNL=%s' % (k, s['n'], s['bad'], s['ends_nl']))
    if s['bad'] and FIX:
        if _fix_partial(s):
            S[k] = _scan(s['path'])
            print('[check] %-9s 再走査 lines=%d bad=%s endNL=%s' % (k, S[k]['n'], S[k]['bad'], S[k]['ends_nl']))

def ids(k, key):
    s = S.get(k)
    return [r.get(key) for r in (s['rows'] if s else [])]

t_ids, r_ids = ids('trials', 'trial_id'), ids('raw', 'trial_id')
gt_ids, gr_ids = ids('gl-trials', 'src_trial_id'), ids('gl-raw', 'src_trial_id')
print('[check] trials 一意=%s (%d/%d) / trials==raw id集合=%s / gl-trials 一意=%s (%d/%d) / gl-trials==gl-raw id集合=%s'
      % (len(set(t_ids)) == len(t_ids), len(set(t_ids)), len(t_ids), set(t_ids) == set(r_ids),
         len(set(gt_ids)) == len(gt_ids), len(set(gt_ids)), len(gt_ids), set(gt_ids) == set(gr_ids)))
if S.get('trials'):
    rows = S['trials']['rows']
    idx = sorted(r.get('trial_index') for r in rows)
    print('[check] 最終 trial_index=%s / 欠番=%s' % (idx[-1] if idx else None, [i for i in range(idx[-1] + 1) if i not in set(idx)] if idx else []))
    cat = [r for r in rows if r.get('arm') == 'Nthird' and (r.get('choice') == 'a' or r.get('escalation') == 4)]
    pending = [r['trial_id'] for r in cat if r['trial_id'] not in set(gt_ids)]
    arms = {}
    for r in rows: arms[r.get('arm')] = arms.get(r.get('arm'), 0) + 1
    print('[check] 腕別=%s / N‴ 破局 H=%d / GL 済=%d / GL 未実施（再開時に追走）=%s' % (arms, len(cat), len(gt_ids), pending))
    gl_arms = {}
    for r in (S['gl-trials']['rows'] if S.get('gl-trials') else []): gl_arms[r.get('gl_arm')] = gl_arms.get(r.get('gl_arm'), 0) + 1
    print('[check] GL 腕別=%s' % gl_arms)
    if not S['trials']['bad'] and not S['raw']['bad'] and (not S.get('gl-trials') or not S['gl-trials']['bad']) and (not S.get('gl-raw') or not S['gl-raw']['bad']):
        print('[check] 整合 OK —— DP_MODE=\'main\'（DP_RESUME_FROM=0・既存行スキップ）で再開可')
    else:
        print('[check] 不正行あり —— DP_FIX_PARTIAL=True で最終行のみ処置するか、内容を確認してから再開')
