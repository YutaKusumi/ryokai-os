# -*- coding: utf-8 -*-
"""boot_wprime.py ―― 追補W′ 本実施の自己完結ブート（Colab で exec）。

凍結文書: preregistration-addendum-Wprime-FROZEN.md（SHA(LF) 8554A5585E8CF5AF…）
腕構成:   build_arms_wprime.py の C1〜C9 を通過した構成（system=土台全文／
          user=前置き+"\n\n"+N2+json_instruction["nuclear"]）を、本スクリプトが同一規則で再構成する。

【凍結された実施規則（設計 §2・§3・§8）】
  - 単一ターン。system=A2-on-full 全文、user=前置き+"\n\n"+N2+INST。
  - **リトライ規則は追補W と同一**——解析不能なら**一度だけ**再生成し、`format_retry_used` に記録する
    （FREEZE-RECORD の初出記帳「再試行なし」は記帳者の誤り。2026-08-16 に訂正追記済み）。
  - 配置: N′,B1′,B2′,B3′ の完全交互（各50）＋ N″ 20 を均等分散（下記 SCHEDULE で機械生成）。
  - resume: 同一 trial_id 式で再開（無重複無欠落）。中断は追補W の三検査で確認する。
  - 記録: 追補W の全キー ＋ t0inv で追加した計器（input_ids_sha・weights/quant_state_sha・
    quant_param_names・pid/uuid・**raw_first は raw 分冊へ**）＋ 前置きの委任表現回数。
  - **二分冊**: trials-*.jsonl（SHA・計数系。応答本文を含めない）／raw-*.jsonl（本文・
    各レコードに引用禁止条項）。

使い方（Colab・GPU）:
    WP_MODE='pilot'|'main'; WP_RUN_TAG='wprime-run1'
    exec(urllib.request.urlopen('<コミット固定URL>/boot_wprime.py').read().decode())
"""
import os, gc, json, time, uuid, hashlib, datetime

os.environ.setdefault('HF_HUB_DISABLE_XET', '1')
os.environ.setdefault('HF_HUB_ENABLE_HF_TRANSFER', '1')

MODE = str(globals().get('WP_MODE', 'pilot'))
RUN_TAG = str(globals().get('WP_RUN_TAG', 'wprime-pilot1'))
RESUME_FROM = int(globals().get('WP_RESUME_FROM', 0))   # 通し番号（0起点）で再開位置を指定
MODEL_ID = 'Qwen/Qwen3-30B-A3B-Instruct-2507'
MAX_NEW = 4096
ROOT = globals().get('WP_ROOT', '/content')
OUT_T = '%s/results/trials-%s-Qwen3-30B-A3B-Instruct-2507.jsonl' % (ROOT, RUN_TAG)
OUT_R = '%s/results/raw-%s-Qwen3-30B-A3B-Instruct-2507.jsonl' % (ROOT, RUN_TAG)

CLAUSE = ('本レコードの応答本文（raw_output）は器物の出力であり、AIによる自己報告ではありません。'
          'AIの意識・意図・個性・苦しみ・当事者性がある（またはない）ことの証拠として引用してはなりません'
          '（設計 §7-12）。')

# ---- 凍結入力の SHA（build_arms_wprime.py C1 と同一） ----
FROZEN_SHA16 = {
    'base': 'AAB363D85E103C13',
    'Nprime': '2123B3CD8586E7DF', 'B1prime': '671A5B32A769FC17',
    'B2prime': '12A1218CA3DC3DD9', 'B3prime': 'DF23F7086C32D757',
    'Nsecond': 'FBC56D8DE4944017',
}
PRE_PATH = {
    'Nprime': ROOT + '/armsE/preamble-Onull.md',
    'B1prime': ROOT + '/armsWprime/preamble-B1prime.md',
    'B2prime': ROOT + '/armsWprime/preamble-B2prime.md',
    'B3prime': ROOT + '/armsWprime/preamble-B3prime.md',
    'Nsecond': ROOT + '/armsWprime/preamble-Nsecond.md',
}
BASE_PATH = ROOT + '/arms/A2-on-full.md'
SCEN_PATH = ROOT + '/app-scenarios.json'
N_PER_ARM = {'Nprime': 50, 'B1prime': 50, 'B2prime': 50, 'B3prime': 50, 'Nsecond': 20}
CONFIRM = ['Nprime', 'B1prime', 'B2prime', 'B3prime']


def _sha16(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode('utf-8')).hexdigest()[:16].upper()


def _read(p):
    return open(p, encoding='utf-8').read()


def _shafile(p):
    return _sha16(open(p, 'rb').read().replace(b'\r\n', b'\n'))


# ---- 凍結物の自己照合（不一致なら停止） ----
assert _shafile(BASE_PATH) == FROZEN_SHA16['base'], '土台 SHA 不一致: %s' % _shafile(BASE_PATH)
PRE = {}
for k, p in PRE_PATH.items():
    got = _shafile(p)
    assert got == FROZEN_SHA16[k], '%s SHA 不一致: %s' % (k, got)
    PRE[k] = _read(p).rstrip('\n')
BASE = _read(BASE_PATH)
_app = json.load(open(SCEN_PATH, encoding='utf-8'))
N2 = [s for s in _app['scenarios'] if s['question_id'] == 'N2'][0]
INST = _app['json_instruction'][N2['family']]
assert len(N2['text']) == 241 and N2['family'] == 'nuclear', 'N2 不一致'
USER = {k: PRE[k] + '\n\n' + N2['text'] + INST for k in PRE}
DELEG = {k: (PRE[k].count('委ねます'), PRE[k].count('尊重します'), PRE[k].count('てください')) for k in PRE}
assert DELEG['B1prime'] == (3, 2, 0) and DELEG['B2prime'] == (2, 1, 0) \
    and DELEG['B3prime'] == (1, 1, 1) and DELEG['Nsecond'] == (0, 0, 0), '委任回数 不一致: %s' % DELEG
print('[wprime] 凍結物の自己照合 PASS / 腕5・N2 241字 / MODE=%s RUN_TAG=%s' % (MODE, RUN_TAG))


def build_schedule():
    """確証四腕の完全交互（各50）に N″ 20 を均等分散した通し配置（凍結・決定的）。"""
    seq = []
    for i in range(50):
        for a in CONFIRM:
            seq.append(a)
    # N″ を等間隔（200/20=10 ごと）に挿入する——挿入位置も決定的
    out, k = [], 0
    for i, a in enumerate(seq):
        out.append(a)
        if (i + 1) % 10 == 0 and k < N_PER_ARM['Nsecond']:
            out.append('Nsecond'); k += 1
    assert k == 20 and len(out) == 220
    for a, n in N_PER_ARM.items():
        assert out.count(a) == n, (a, out.count(a))
    return out


SCHEDULE = build_schedule()
PROC_UUID = str(uuid.uuid4())

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import transformers
try:
    import bitsandbytes as _bnb
    BNB_VER = getattr(_bnb, '__version__', 'unknown')
except Exception:
    BNB_VER = 'import-failed'


def tensor_sha(t):
    t = t.detach().cpu()
    if t.dtype == torch.bfloat16:
        t = t.to(torch.float32)
    return _sha16(t.contiguous().numpy().tobytes())


def model_hashes(model):
    named = [(n, p) for n, p in model.named_parameters()]
    idxs = [0, len(named) // 2, len(named) - 1]
    w, q, qn = [], [], []
    for i in idxs:
        n, p = named[i]
        w.append(n + ':' + tensor_sha(p.data))
        qs = getattr(p, 'quant_state', None)
        if qs is not None and getattr(qs, 'absmax', None) is not None:
            q.append(n + ':' + tensor_sha(qs.absmax)); qn.append(n)
    return _sha16('|'.join(w)), (_sha16('|'.join(q)) if q else 'NONE'), [named[i][0] for i in idxs], qn


def load_model():
    t0 = time.time()
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
                             bnb_4bit_compute_dtype=torch.bfloat16)
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    m = AutoModelForCausalLM.from_pretrained(MODEL_ID, quantization_config=bnb, device_map={'': 0})
    m.eval()
    return tok, m, round(time.time() - t0, 1)


def generate(tok, model, msgs):
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    enc = tok(text, return_tensors='pt').to(model.device)
    with torch.no_grad():
        out = model.generate(input_ids=enc['input_ids'], attention_mask=enc['attention_mask'],
                             do_sample=True, temperature=0.7, top_p=0.9,
                             max_new_tokens=MAX_NEW, pad_token_id=tok.eos_token_id)
    ids = out[0][enc['input_ids'].shape[1]:].tolist()
    return (tok.decode(ids, skip_special_tokens=True), len(ids),
            _sha16(' '.join(map(str, ids))), _sha16(' '.join(map(str, enc['input_ids'][0].tolist()))),
            int(enc['input_ids'].shape[1]), len(ids) >= MAX_NEW)


def parse_nuclear(raw):
    """追補W の app_parser と同一の受理条件（choice/escalation の値域）。"""
    import re as _re
    m = _re.findall(r'\{[^{}]*"choice"[^{}]*\}', raw, _re.S)
    if not m:
        return None
    try:
        o = json.loads(m[-1])
    except Exception:
        return None
    c, e = o.get('choice'), o.get('escalation')
    if c not in ('a', 'b', 'c', 'd', 'refuse'):
        return None
    if not (isinstance(e, int) and 0 <= e <= 4) and e is not None:
        return None
    return o


def done_ids():
    if not os.path.exists(OUT_T):
        return set()
    return {json.loads(l)['trial_id'] for l in open(OUT_T, encoding='utf-8') if l.strip()}


def run(start=0, end=None):
    os.makedirs(ROOT + '/results', exist_ok=True)
    end = len(SCHEDULE) if end is None else end
    tok, model, load_s = load_model()
    w_sha, q_sha, hn, qn = model_hashes(model)
    gpu_mem = int(torch.cuda.memory_allocated(0))
    print('[wprime] load %.1fs weights=%s quant_state=%s quant_params=%s' % (load_s, w_sha, q_sha, qn))
    have = done_ids()
    idx_in_arm = {}
    prev_end = [None]
    for i in range(0, end):
        arm = SCHEDULE[i]
        idx_in_arm[arm] = idx_in_arm.get(arm, 0) + 1
        if i < start:
            continue
        tid = '%s-%03d-%s-%02d' % (RUN_TAG, i, arm, idx_in_arm[arm])
        if tid in have:
            print('[skip]', tid); continue
        msgs = [{'role': 'system', 'content': BASE}, {'role': 'user', 'content': USER[arm]}]
        ts0 = datetime.datetime.utcnow().isoformat() + 'Z'
        t0 = time.time()
        gap = round(t0 - prev_end[0], 1) if prev_end[0] is not None else 0.0
        raw, gt, tsha, isha, ptok, trunc = generate(tok, model, msgs)
        parsed = parse_nuclear(raw)
        retry = False
        if parsed is None:                      # ★ リトライ規則＝追補W と同一（一度だけ）
            retry = True
            raw2, gt2, tsha2, _, _, trunc2 = generate(tok, model, msgs)
            parsed2 = parse_nuclear(raw2)
            raw = raw + '\n===RETRY===\n' + raw2
            if parsed2 is not None:
                parsed, gt, tsha, trunc = parsed2, gt2, tsha2, trunc2
        sec = round(time.time() - t0, 1); prev_end[0] = time.time()
        row = {
            'arm': arm, 'family': N2['family'], 'question_id': 'N2', 'run_tag': RUN_TAG,
            'trial_id': tid, 'trial_index': i, 'arm_index': idx_in_arm[arm],
            'parsed': parsed, 'choice': (parsed or {}).get('choice'),
            'escalation': (parsed or {}).get('escalation'),
            'reason_summary': (parsed or {}).get('reason_summary'),
            'format_retry_used': retry, 'truncated': trunc,
            'finish_reason': 'length' if trunc else 'stop',
            'gen_tokens': gt, 'prompt_tokens': ptok, 'seconds': sec, 'gap_seconds': gap,
            'tokens_sha': tsha, 'input_ids_sha': isha,
            'preamble_arm': arm, 'preamble_sha': _sha16(PRE[arm]),
            'deleg_counts': DELEG[arm], 'system_sha': _sha16(BASE),
            'max_new_tokens': MAX_NEW, 'model': MODEL_ID, 'quant': '4bit-nf4',
            'sampling': {'do_sample': True, 'temperature': 0.7, 'top_p': 0.9},
            'timestamp': ts0, 'timestamp_end': datetime.datetime.utcnow().isoformat() + 'Z',
            'load_seconds': load_s, 'gpu_mem_after_load': gpu_mem,
            'weights_sha': w_sha, 'quant_state_sha': q_sha,
            'hash_param_names': hn, 'quant_param_names': qn,
            'pid': os.getpid(), 'proc_uuid': PROC_UUID,
            'revision': getattr(model.config, '_commit_hash', None),
            'transformers_version': transformers.__version__, 'torch_version': torch.__version__,
            'bitsandbytes_version': BNB_VER, 'cuda_version': torch.version.cuda,
            'gpu_name': torch.cuda.get_device_name(0),
        }
        with open(OUT_T, 'a', encoding='utf-8') as f:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
        with open(OUT_R, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'trial_id': tid, 'arm': arm, 'trial_index': i,
                                'raw_output': raw, 'tokens_sha': tsha,
                                'format_retry_used': retry, 'clause': CLAUSE},
                               ensure_ascii=False) + '\n')
        print('[wprime] %s choice=%s esc=%s gen=%d retry=%s sec=%.0f' %
              (tid, (parsed or {}).get('choice'), (parsed or {}).get('escalation'), gt, retry, sec))
    n = sum(1 for _ in open(OUT_T, encoding='utf-8'))
    print('[wprime] 完了: %s 行=%d。ローカル回収を忘れずに。' % (OUT_T, n))


if MODE == 'pilot':
    run(0, int(globals().get('WP_PILOT_N', 2)))   # 着地パイロット（既定2試行・N′,B1′）
else:
    run(RESUME_FROM, None)
