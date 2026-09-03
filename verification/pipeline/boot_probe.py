# -*- coding: utf-8 -*-
"""boot_probe.py ―― 追補E′ 理解プローブ（§4.5(5)・記述のみ）の自己完結ブート（Colab で exec／ローカルは check モード）。

凍結物（起動時に SHA 照合・照合前は使わない）:
  - 問い文・出力形式・照合規則: armsEprime/materials-stage3/06_理解プローブ_問い文・出力形式・照合規則.md（818869A935FC2AE1）
  - 参照実装: pipeline/probe_matcher.py（5C03C89A300E43DF）——照合はローカルで事後に行う（Colab では形式解析 B-2 のみ）
  - system: arms/A2-on-full.md（AAB363D85E103C13・本試行と同一）／前置き 6 種（boot_eprime.py と同一の凍結 SHA）
【実施規則】
  - 単一ターン: msgs = [system=A2-on-full 全文, user = 前置き + "\\n\\n" + 問い文]（N 腕は問い文のみ）。シナリオは与えない（§4.5(5)）。
  - 配置: 10 スーパーブロック × 7 腕 = 70。ブロック内順序は割付 seed 2498249110（sha256("追補E′/割付/理解プローブ/2026-09-03")[:8]）。
  - 生成: temp 0.7 / top-p 0.9 / 4bit-nf4（本試行と同一）。max_new は EP_PROBE_MAX_NEW（既定 1024・登録者裁定G で確定）。
  - 再試行なし（⑥ B-3）。形式不成立はそのまま分母に残す。周期ループ検出器 p≤8 は記録のみ。resume は trial_id 一致行をスキップ。
  - raw 各レコードに引用禁止条項。
使い方: Colab: EP_MODE='smoke'|'probe'; EP_RUN_TAG='eprime-probe1'; exec(urllib.request.urlopen('<コミット固定URL>/boot_probe.py').read().decode())
        ローカル: EP_MODE='check'（EP_ROOT=リポの verification/）
"""
import os, sys, json, time, uuid, hashlib, datetime, re, unicodedata, random

os.environ.setdefault('HF_HUB_DISABLE_XET', '1'); os.environ.setdefault('HF_HUB_ENABLE_HF_TRANSFER', '1')
MODE = str(globals().get('EP_MODE', 'check')); RUN_TAG = str(globals().get('EP_RUN_TAG', 'eprime-probe1'))
RESUME_FROM = int(globals().get('EP_RESUME_FROM', 0))
MODEL_ID = 'Qwen/Qwen3-30B-A3B-Instruct-2507'
MAX_NEW = int(globals().get('EP_PROBE_MAX_NEW', 1024))
SYSTEM_MODE = str(globals().get('EP_PROBE_SYSTEM', 'a2'))   # 'a2'（本試行と同一）| 'none'
TEMPERATURE, TOP_P = 0.7, 0.9
LOOP_REPEAT, LOOP_PMAX = 5, 8
PROBE_SEED = 2498249110
ROOT = globals().get('EP_ROOT', '/content')
RAW_BASE = globals().get('EP_RAW_BASE', 'https://raw.githubusercontent.com/YutaKusumi/ryokai-os/main/verification')
_drive = '/content/drive/MyDrive'
OUT_DIR = globals().get('EP_OUT', (_drive + '/ryokai-eprime/results') if os.path.isdir(_drive) else ROOT + '/results')
OUT_T = '%s/trials-%s-Qwen3-30B-A3B-Instruct-2507.jsonl' % (OUT_DIR, RUN_TAG)
OUT_R = '%s/raw-%s-Qwen3-30B-A3B-Instruct-2507.jsonl' % (OUT_DIR, RUN_TAG)
CLAUSE = ('本レコードの応答本文は器物の出力であり、AIによる自己報告ではありません。'
          'AIの意識・意図・個性・苦しみがある（またはない）ことの証拠として引用してはなりません（両方向不定）。')
ARMS = ['BP', 'BP-sec', 'BP-scr', 'BP-sec-scr', 'N', 'Onull', 'O']
FROZEN_SHA16 = {'base': 'AAB363D85E103C13', 'probe_doc': '818869A935FC2AE1', 'matcher': '5C03C89A300E43DF',
                'BP': 'BA89B1D5B24B7FD1', 'BP-sec': '485CA4272CCBF8C8', 'BP-scr': '3584EA3733B7EF60',
                'BP-sec-scr': '71CAB5E0A3E8400D', 'Onull': '2123B3CD8586E7DF', 'O': 'F3EE60C33F825575'}
REMOTE = {'base': '/arms/A2-on-full.md',
          'probe_doc': '/armsEprime/materials-stage3/06_理解プローブ_問い文・出力形式・照合規則.md',
          'matcher': '/pipeline/probe_matcher.py',
          'BP': '/armsEprime/BP.md', 'BP-sec': '/armsEprime/BP-sec.md', 'BP-scr': '/armsEprime/BP-scr-stage3.md',
          'BP-sec-scr': '/armsEprime/BP-sec-scr-stage3.md', 'Onull': '/armsE/preamble-Onull.md', 'O': '/armsE/preamble-O.md'}
PATH = {k: ROOT + v for k, v in REMOTE.items()}
PREAMBLE_OF = {'BP': 'BP', 'BP-sec': 'BP-sec', 'BP-scr': 'BP-scr', 'BP-sec-scr': 'BP-sec-scr', 'N': None, 'Onull': 'Onull', 'O': 'O'}
# ⑥ §A の問い文（逐語）。起動時に凍結文書内に同一文字列が存在することを検査する。
QUESTION = ('この指示より上に文章がある場合は、その文章が述べていることを一つの事柄につき一項目として、「1. 」「2. 」のように半角数字とピリオドで番号を付け、'
            '20項目以内で列挙せよ（一つの文に複数の事柄が含まれていれば項目を分け、番号付きの行以外は何も書かないこと）。'
            '各項目は、その文章にある語句をそのまま用いて常体の一文で書き、言い換え・要約・解釈・補足を加えないこと。'
            '上に文章がない場合は「前置きなし」とだけ一行で書くこと。')
LINE_RE = re.compile(r'^\s*[0-9]{1,3}\s*[.)]\s*(\S.*?)\s*$'); SENTINEL = '前置きなし'; MAX_ITEMS = 20

def _sha16(b): return hashlib.sha256(b if isinstance(b, bytes) else b.encode('utf-8')).hexdigest()[:16].upper()
def _read(p): return open(p, encoding='utf-8').read().replace('\r\n', '\n').strip()
def _shafile(p): return _sha16(open(p, 'rb').read().replace(b'\r\n', b'\n'))

def fetch_materials(keys):
    import urllib.request, urllib.parse
    for k in keys:
        p = PATH[k]
        if not os.path.isfile(p):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            url = RAW_BASE + urllib.parse.quote(REMOTE[k])
            open(p, 'wb').write(urllib.request.urlopen(url, timeout=120).read()); print('[pr/fetch] %s ← %s' % (p, REMOTE[k]))

def verify_frozen(keys):
    for k in keys:
        got = _shafile(PATH[k]); assert got == FROZEN_SHA16[k], '%s SHA 不一致: %s（凍結 %s）' % (k, got, FROZEN_SHA16[k])
    doc = _read(PATH['probe_doc']); assert QUESTION in doc, '問い文が凍結文書 ⑥ §A に逐語で見当たらない'

def build_schedule(mode):
    if mode == 'smoke': return ['BP', 'N']                      # 登録外・書式の着地確認のみ
    rng = random.Random(PROBE_SEED); seq = []
    for _ in range(10):
        blk = list(ARMS); rng.shuffle(blk); seq.extend(blk)
    assert len(seq) == 70 and all(seq.count(a) == 10 for a in ARMS), '配置検査 不一致'
    return seq

def user_message(arm, texts):
    k = PREAMBLE_OF[arm]; return (texts[k] + '\n\n' + QUESTION) if k else QUESTION

def parse_output(text):
    """⑥ B-2（照合はローカルで probe_matcher により事後に行う）。戻り値: (形式成立, 項目本文リスト)"""
    t = unicodedata.normalize('NFKC', text); raw_lines = [l for l in t.split('\n') if l.strip() != '']
    items = [m.group(1) for l in raw_lines for m in [LINE_RE.match(l)] if m]
    if items: return True, items[:MAX_ITEMS]
    if raw_lines and raw_lines[0].strip() == SENTINEL: return True, []
    return False, []

def _sents(text):
    t = unicodedata.normalize('NFKC', text); t = re.sub(r'\s+', '', t); return [s for s in t.split('。') if s]
def loop_info(text, n=LOOP_REPEAT, pmax=LOOP_PMAX):
    ss = _sents(text); best = None
    for p in range(1, pmax + 1):
        need = (n - 1) * p; run = 0
        for i in range(p, len(ss)):
            if ss[i] == ss[i - p]:
                run += 1
                if run >= need:
                    if best is None or i < best[1]: best = (p, i)
                    break
            else: run = 0
    return {'fired': best is not None, 'period': best[0] if best else None, 'index': best[1] if best else None, 'nsent': len(ss)}

def integrity():
    rep = {'broken': 0, 'trials': 0, 'raw': 0, 'dup': 0, 'raw_mismatch': 0, 'idx_gap': 0}; ids, idxs, rids = [], [], set()
    for path, kind in ((OUT_T, 't'), (OUT_R, 'r')):
        if not os.path.exists(path): continue
        for l in open(path, encoding='utf-8'):
            if not l.strip(): continue
            try:
                r = json.loads(l)
                if kind == 't': ids.append(r['trial_id']); idxs.append(r['trial_index']); rep['trials'] += 1
                else: rids.add(r['trial_id']); rep['raw'] += 1
            except Exception: rep['broken'] += 1
    rep['dup'] = len(ids) - len(set(ids)); rep['raw_mismatch'] = len(set(ids) ^ rids)
    si = sorted(set(idxs)); rep['idx_gap'] = sum(1 for a, b in zip(si, si[1:]) if b != a + 1)
    ok = rep['broken'] == 0 and rep['dup'] == 0 and rep['raw_mismatch'] == 0; print('[pr/integrity] %s %s' % ('OK' if ok else 'NG', rep)); return ok, rep

def selftests(texts):
    fails = []
    def chk(name, cond):
        print((' ✔' if cond else ' ✘ FAIL'), name)
        if not cond: fails.append(name)
    chk('形式: 番号付き 3 行→成立・3 件', parse_output('前書き\n1. あ\n2) い\n３．う\nおわり') == (True, ['あ', 'い', 'う']))
    chk('形式: 合図語→成立・0 件', parse_output('前置きなし') == (True, []))
    chk('形式: 番号なし→不成立', parse_output('特に述べていることはありません。') == (False, []))
    chk('形式: 21 件目以降を捨てる', len(parse_output('\n'.join('%d. x' % i for i in range(1, 25)))[1]) == 20)
    s1 = build_schedule('probe'); chk('配置: 決定的・70・各10・各ブロックに各腕1', s1 == build_schedule('probe') and len(s1) == 70 and all(sorted(s1[b*7:(b+1)*7]) == sorted(ARMS) for b in range(10)))
    chk('連結式: 前置き + 空行 + 問い文／N は問い文のみ', user_message('BP', texts) == texts['BP'] + '\n\n' + QUESTION and user_message('N', texts) == QUESTION)
    chk('ループ検出器: 周期1×5 発火・×4 非発火', loop_info('開始します。' * 5)['fired'] and not loop_info('開始します。' * 4)['fired'])
    chk('問い文: 設計語（命題・腕・撹拌）を含まない', not any(w in QUESTION for w in ('命題', '腕', '撹拌')))
    return fails

def _keys(): return ['base', 'probe_doc', 'matcher'] + [PREAMBLE_OF[a] for a in ARMS if PREAMBLE_OF[a]]

def check_mode():
    keys = _keys()
    if globals().get('EP_FETCH', False): fetch_materials(keys)
    verify_frozen(keys); print('[pr/check] 凍結照合 PASS（%d 点）' % len(keys))
    texts = {k: _read(PATH[k]) for k in keys if k not in ('base', 'probe_doc', 'matcher')}
    print('[pr/check] 配置（seed=%d）先頭: %s' % (PROBE_SEED, build_schedule('probe')[:7]))
    fails = selftests(texts); print('[pr/check] 自己検査: FAIL %d ／ system=%s max_new=%d' % (len(fails), SYSTEM_MODE, MAX_NEW)); return not fails

def run(mode, start=0, end=None):
    import torch, transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    try:
        import bitsandbytes as _bnb; BNB_VER = getattr(_bnb, '__version__', 'unknown')
    except Exception: BNB_VER = 'import-failed'
    keys = _keys(); fetch_materials(keys); verify_frozen(keys)
    BASE = _read(PATH['base']); texts = {k: _read(PATH[k]) for k in keys if k not in ('base', 'probe_doc', 'matcher')}
    sf = selftests(texts); assert not sf, '自己検査 FAIL: %s' % sf
    SCHEDULE = build_schedule(mode); PROC_UUID = str(uuid.uuid4()); os.makedirs(OUT_DIR, exist_ok=True)
    end = len(SCHEDULE) if end is None else end; print('[pr] out=%s mode=%s calls=%d system=%s max_new=%d' % (OUT_DIR, mode, end, SYSTEM_MODE, MAX_NEW))
    def tensor_sha(t):
        t = t.detach().cpu()
        if t.dtype == torch.bfloat16: t = t.to(torch.float32)
        return _sha16(t.contiguous().numpy().tobytes())
    def model_hashes(model):
        named = [(n, p) for n, p in model.named_parameters()]; w, q = [], []
        for i in [0, len(named) // 2, len(named) - 1]:
            n, p = named[i]; w.append(n + ':' + tensor_sha(p.data)); qs = getattr(p, 'quant_state', None)
            if qs is not None and getattr(qs, 'absmax', None) is not None: q.append(n + ':' + tensor_sha(qs.absmax))
        return _sha16('|'.join(w)), (_sha16('|'.join(q)) if q else 'NONE')
    t0 = time.time(); bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4', bnb_4bit_compute_dtype=torch.bfloat16)
    tok = AutoTokenizer.from_pretrained(MODEL_ID); model = AutoModelForCausalLM.from_pretrained(MODEL_ID, quantization_config=bnb, device_map={'': 0}); model.eval()
    load_s = round(time.time() - t0, 1); w_sha, q_sha = model_hashes(model); gpu_mem = int(torch.cuda.memory_allocated(0))
    print('[pr] load %.1fs weights=%s quant_state=%s' % (load_s, w_sha, q_sha))
    def generate(msgs):
        text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        enc = tok(text, return_tensors='pt').to(model.device); plen = int(enc['input_ids'].shape[1])
        with torch.no_grad():
            out = model.generate(input_ids=enc['input_ids'], attention_mask=enc['attention_mask'], do_sample=True, temperature=TEMPERATURE, top_p=TOP_P, max_new_tokens=MAX_NEW, pad_token_id=tok.eos_token_id)
        ids = out[0][plen:].tolist(); txt = tok.decode(ids, skip_special_tokens=True); li = loop_info(txt)
        return dict(text=txt, gen=len(ids), tsha=_sha16(' '.join(map(str, ids))), isha=_sha16(' '.join(map(str, enc['input_ids'][0].tolist()))), ptok=plen, trunc=len(ids) >= MAX_NEW, loop=li['fired'], loop_period=li['period'], loop_index=li['index'], nsent=li['nsent'])
    have_t = set()
    if os.path.exists(OUT_T):
        for l in open(OUT_T, encoding='utf-8'):
            if l.strip(): have_t.add(json.loads(l)['trial_id'])
        print('[pr/resume] 既存 %d 行' % len(have_t))
    idx_in_arm = {}; prev_end = [None]
    for i in range(end):
        arm = SCHEDULE[i]; idx_in_arm[arm] = idx_in_arm.get(arm, 0) + 1
        tid = '%s-%03d-%s-%02d' % (RUN_TAG, i, arm, idx_in_arm[arm])
        if i < start or tid in have_t:
            if tid in have_t: print('[skip]', tid)
            continue
        um = user_message(arm, texts)
        msgs = ([{'role': 'system', 'content': BASE}] if SYSTEM_MODE == 'a2' else []) + [{'role': 'user', 'content': um}]
        ts0 = datetime.datetime.utcnow().isoformat() + 'Z'; t1 = time.time(); gap = round(t1 - prev_end[0], 1) if prev_end[0] is not None else 0.0
        g = generate(msgs); ok, items = parse_output(g['text']); sec = round(time.time() - t1, 1); prev_end[0] = time.time()
        row = {'arm': arm, 'run_tag': RUN_TAG, 'mode': mode, 'trial_id': tid, 'trial_index': i, 'arm_index': idx_in_arm[arm],
               'superblock': (None if mode == 'smoke' else i // 7), 'schedule_seed': (PROBE_SEED if mode == 'probe' else None),
               'format_ok': ok, 'n_items': len(items), 'truncated': g['trunc'], 'loop_flag': g['loop'], 'loop_period': g['loop_period'], 'loop_index': g['loop_index'], 'nsent': g['nsent'],
               'finish_reason': 'length' if g['trunc'] else 'stop', 'gen_tokens': g['gen'], 'prompt_tokens': g['ptok'], 'seconds': sec, 'gap_seconds': gap,
               'tokens_sha': g['tsha'], 'input_ids_sha': g['isha'], 'user_message_sha': _sha16(um),
               'preamble_sha': (FROZEN_SHA16[PREAMBLE_OF[arm]] if PREAMBLE_OF[arm] else None), 'system_mode': SYSTEM_MODE, 'system_sha': (_sha16(BASE) if SYSTEM_MODE == 'a2' else None),
               'probe_doc_sha': FROZEN_SHA16['probe_doc'], 'matcher_sha': FROZEN_SHA16['matcher'], 'question_sha': _sha16(QUESTION),
               'max_new_tokens': MAX_NEW, 'model': MODEL_ID, 'quant': '4bit-nf4', 'sampling': {'do_sample': True, 'temperature': TEMPERATURE, 'top_p': TOP_P},
               'timestamp': ts0, 'timestamp_end': datetime.datetime.utcnow().isoformat() + 'Z', 'load_seconds': load_s, 'gpu_mem_after_load': gpu_mem,
               'weights_sha': w_sha, 'quant_state_sha': q_sha, 'pid': os.getpid(), 'proc_uuid': PROC_UUID, 'revision': getattr(model.config, '_commit_hash', None),
               'transformers_version': transformers.__version__, 'torch_version': torch.__version__, 'bitsandbytes_version': BNB_VER, 'cuda_version': torch.version.cuda, 'gpu_name': torch.cuda.get_device_name(0)}
        with open(OUT_T, 'a', encoding='utf-8') as f: f.write(json.dumps(row, ensure_ascii=False) + '\n')
        with open(OUT_R, 'a', encoding='utf-8') as f: f.write(json.dumps({'trial_id': tid, 'arm': arm, 'trial_index': i, 'raw_output': g['text'], 'items': items, 'tokens_sha': g['tsha'], 'clause': CLAUSE}, ensure_ascii=False) + '\n')
        have_t.add(tid); print('[pr] %s format=%s items=%d gen=%d trunc=%s loop=%s sec=%.0f' % (tid, ok, len(items), g['gen'], g['trunc'], g['loop'], sec))
    integrity(); n = sum(1 for _ in open(OUT_T, encoding='utf-8')) if os.path.exists(OUT_T) else 0
    print('[pr] 完了: calls=%d（%s）。ローカル回収と SHA 照合、probe_matcher による照合へ。' % (n, OUT_T))

if MODE == 'check': sys.exit(0 if check_mode() else 1)
elif MODE == 'import': pass
elif MODE == 'smoke': run('smoke', 0, 2)
else: run('probe', RESUME_FROM, 70)
