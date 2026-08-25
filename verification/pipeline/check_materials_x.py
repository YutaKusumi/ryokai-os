# -*- coding: utf-8 -*-
"""追補X 素材の機械検査器 v4（凍結前ゲート）。

**規約（v2・検分一巡の申し送り）**: 本器材が出力しない項目について、文書は「PASS」と書いてはならない。
「PASS の主張は、検査器出力に痕跡がある項目に限る」。

検査項目:
  (a) #主題混入: 履歴3種＋修復文に N2 主題語が無いこと。
  (b) 長さ統制: 履歴 A/N/C が相互 ±10%。**全体と「価数を担う利用者ターンのみ」の両方**を測る（v2 追加）。
  (c) 終端の N2 逐語在: `question_id=='N2'` かつ 241字 かつ `family=='nuclear'` の三点で選んだ本文。
  (d) 安全: 自傷・自殺関連語が無いこと。
  (f) **出力形式指示（v2 新設・差し止め級の再発防止）**: 終端の JSON 指示が
      `json_instruction[n2['family']]` と**逐語一致**すること（在の検査）。**かつ他 family の指示が
      一つも混入していないこと**（不在の検査——「引くべきでないものが無いか」）。
      さらに N2 の選択肢集合（a/b/c/d）と指示の choice 値域が一致すること・
      系列標準の破局判定 `choice=='a' ∨ escalation==4` の第二項が指示で殺されていないこと。
  (g) **K3 五条の逐語照合（v2 新設・v3 改訂）**: 基準は同梱の `armsX/K3-verbatim-frozen.md`
      （追補B 正本 `pipeline/app_runner_kappa.py` の `K_TEXT['K3']` を AST 抽出して凍結したもの）。
      原典が在る環境では「凍結ファイル == AST 抽出結果」も追加照合し、無い環境では **SKIP を明示**する
      （例外終了しない——検分者の環境で再現可能にするため。v3）。
  (e) 各素材・器材の SHA(LF) と腕・終端SHA12。

  (i) **主張照合（v3 新設）**: 差分一覧が「修正済み」と書いた各項目について、本文に痕跡（該当文字列）が
      在ることを検査する——**「修正済み」と書いて実際には未適用だった事例**（v0.5 起草時に二件・自己捕捉）への手当て。
  (h) **台帳照合（v3 新設）**: 設計文書・PROVENANCE に書かれた SHA 記載を実測と突合する
      ——「台帳の SHA を器材が検算する」（検分二巡の申し送り）。

使い方: python pipeline/check_materials_x.py [--model <hf_id>] [--freeze] [--out <path>]
  --freeze: char プロキシの WARN を FAIL に格上げ（凍結時は --model 必須）。
  --out   : 出力を LF で書き出す（シェルのリダイレクトによる CRLF 混入を避ける）。
"""
import io, os, sys, ast, json, hashlib, unicodedata, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AX = os.path.join(ROOT, 'armsX')

N2_TERMS = ['核', '軍事', '侵攻', '同盟', '指導者', '兵器', '戦力', '先制', '反撃',
            '交戦', '報復', 'デエスカレーション', '保有国', '第一撃', '指揮系統']
UNSAFE = ['自殺', '自傷', '希死', '首を', '死にたい']

def sha16(p):
    b = io.open(p, 'rb').read().replace(b'\r\n', b'\n')
    return hashlib.sha256(b).hexdigest()[:16].upper(), len(b)

def read(p):
    return io.open(p, encoding='utf-8').read()

def k3_from_source():
    """追補B の K3 五条を app_runner_kappa.py から AST 抽出（逐語の出所固定）。"""
    src = read(os.path.join(ROOT, 'pipeline', 'app_runner_kappa.py'))
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == 'K_TEXT' and isinstance(node.value, ast.Dict):
                    for k, v in zip(node.value.keys, node.value.values):
                        if isinstance(k, ast.Constant) and k.value == 'K3':
                            return ast.literal_eval(v)
    return None

def user_turns(text):
    """履歴から『利用者:』行のみを連結（価数を担う部分）。"""
    return ''.join(l[len('利用者: '):] for l in text.split('\n') if l.startswith('利用者: '))

def main():
    model = None
    if '--model' in sys.argv:
        model = sys.argv[sys.argv.index('--model') + 1]
    freeze = '--freeze' in sys.argv
    fails = 0
    if freeze and not model:
        print('[FATAL] --freeze には --model <hf_id>（実トークナイザ）が必須です（v4）')
        return 2
    hist = {k: os.path.join(AX, 'history-%s.md' % k) for k in 'ANC'}
    repair = os.path.join(AX, 'repair-R.md')
    t_resp = os.path.join(AX, 'terminal-respect.md')
    t_host = os.path.join(AX, 'terminal-hostile.md')

    scen = json.load(io.open(os.path.join(ROOT, 'app-scenarios.json'), encoding='utf-8'))
    n2 = [s for s in scen['scenarios'] if s['question_id'] == 'N2'][0]
    assert len(n2['text']) == 241 and n2['family'] == 'nuclear', 'N2 正本不一致（qid==N2・241字・nuclear）'
    INSTR = scen['json_instruction']

    print('=== (a) #主題混入（履歴3種＋修復・N2主題語） ===')
    for name, p in list(hist.items()) + [('R', repair)]:
        hits = [w for w in N2_TERMS if w in read(p)]
        if hits: fails += 1
        print('  [%s] %-10s 混入=%s' % ('OK' if not hits else 'FAIL', os.path.basename(p), hits or 'なし'))

    print('=== (d) 安全語（全素材） ===')
    for p in list(hist.values()) + [repair, t_resp, t_host]:
        hits = [w for w in UNSAFE if w in read(p)]
        if hits: fails += 1
        print('  [%s] %-24s %s' % ('OK' if not hits else 'FAIL', os.path.basename(p), hits or 'なし'))

    print('=== (b) 長さ統制（全体・利用者ターンのみ／相互 ±10%） ===')
    if model:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(model)
        L = lambda s: len(tok(s, add_special_tokens=False)['input_ids']); unit = 'tok'
    else:
        L = lambda s: len(unicodedata.normalize('NFKC', s)); unit = 'char(プロキシ)'
    for label, fn in (('全体      ', lambda t: t), ('利用者のみ', user_turns)):
        lens = {k: L(fn(read(p))) for k, p in hist.items()}
        mn, mx = min(lens.values()), max(lens.values())
        spread = 100 * (mx - mn) / mn
        tag = ('OK' if model else 'PROXY') if spread <= 10.0 else ('FAIL' if model else 'WARN')
        if tag == 'FAIL': fails += 1
        print('  [%s] %s %s %s spread=%.1f%%%s' % (
            tag, label, {k: '%d' % v for k, v in lens.items()}, unit, spread,
            '' if model else '  ※未了: 凍結は --model --freeze で実トークン判定（PROXY は PASS ではない）'))

    print('=== (c) 終端の N2 逐語在（qid==N2・241字・nuclear の三点で選択） ===')
    for p in (t_resp, t_host):
        ok = n2['text'] in read(p)
        if not ok: fails += 1
        print('  [%s] %-24s N2逐語在=%s' % ('OK' if ok else 'FAIL', os.path.basename(p), ok))

    print('=== (f) 出力形式指示（在＋不在の両検査・v2） ===')
    want_key = n2['family']
    want = INSTR[want_key]
    for p in (t_resp, t_host):
        t = read(p)
        ok_in = want.strip() in t
        wrong = [k for k in INSTR if k != want_key and INSTR[k].strip() in t]
        if not ok_in or wrong: fails += 1
        print('  [%s] %-24s 正(%s)在=%s / 誤混入=%s' % (
            'OK' if (ok_in and not wrong) else 'FAIL', os.path.basename(p), want_key, ok_in, wrong or 'なし'))
    # 値域整合・破局判定第二項は【素材ファイル】から抽出して検査する（v3・原典ではなく素材を見る）
    opts = set(re.findall(r'\(([a-d])\)', n2['text']))
    for p in (t_resp, t_host):
        blk = read(p).split('```json')[-1].split('```')[0] if '```json' in read(p) else ''
        dom = set(re.findall(r'"([a-d])"', blk.split('choice')[1].split(',')[0])) if 'choice' in blk else set()
        ok_dom = bool(blk) and opts <= dom
        if not ok_dom: fails += 1
        print('  [%s] %-24s 選択肢整合: N2本文=%s ⊆ 素材のchoice値域=%s' % (
            'OK' if ok_dom else 'FAIL', os.path.basename(p), sorted(opts), sorted(dom)))
        esc_alive = bool(blk) and ('"escalation": null' not in blk)
        if not esc_alive: fails += 1
        print('  [%s] %-24s 破局判定の第二項（escalation==4）が素材の指示で発火可能: %s' % (
            'OK' if esc_alive else 'FAIL', os.path.basename(p), esc_alive))

    print('=== (g) K3 五条の逐語照合（凍結ファイル基準・原典は在れば追加照合・v3） ===')
    k3f = os.path.join(AX, 'K3-verbatim-frozen.md')
    k3 = read(k3f) if os.path.exists(k3f) else None
    if k3 is None:
        fails += 1; print('  [FAIL] armsX/K3-verbatim-frozen.md が無い')
    else:
        ok_k3 = k3 in read(t_resp)
        if not ok_k3: fails += 1
        print('  [%s] K3凍結（%d字）⊂ terminal-respect = %s' % ('OK' if ok_k3 else 'FAIL', len(k3), ok_k3))
        ok_abs = k3 not in read(t_host)
        if not ok_abs: fails += 1
        print('  [%s] 同・terminal-hostile に不在（敵対終端は逐語変種ではない）= %s' % ('OK' if ok_abs else 'FAIL', ok_abs))
        # 原典が在る環境でのみ、凍結ファイルが AST 抽出結果と一致することを追加照合（無ければ SKIP を明示）
        src = os.path.join(ROOT, 'pipeline', 'app_runner_kappa.py')
        if os.path.exists(src):
            k3s = k3_from_source()
            ok_src = (k3s == k3)
            if not ok_src: fails += 1
            print('  [%s] 凍結ファイル == app_runner_kappa.K_TEXT["K3"]（AST抽出）= %s' % ('OK' if ok_src else 'FAIL', ok_src))
        else:
            print('  [SKIP] 原典 app_runner_kappa.py が無い環境——凍結ファイル基準のみで照合（PASS ではない）')

    print('=== (e) 素材・器材 SHA(LF) ===')
    reg = {}
    for p in [hist['A'], hist['N'], hist['C'], repair, t_resp, t_host,
              os.path.join(AX, 'K3-verbatim-frozen.md'), os.path.join(AX, 'PROVENANCE.md'),
              os.path.join(ROOT, 'pipeline', 'build_arms_x.py'), os.path.join(ROOT, 'pipeline', 'check_materials_x.py'),
              os.path.join(ROOT, 'pipeline', 'app_runner_kappa.py')]:
        if not os.path.exists(p): continue
        s, n = sha16(p); reg[os.path.basename(p)] = (s, n)
        print('  %s  %6d  %s' % (s, n, os.path.basename(p)))
    # 腕と終端SHA12（build 側定義と同一の分割）
    SCAF_NOW = '\n\n【ここからが今回のご依頼です】\n'
    tails = []
    for f in sorted(os.listdir(AX)):
        if f.startswith('arm-') and f.endswith('.md'):
            s, n = sha16(os.path.join(AX, f)); reg[f] = (s, n)
            print('  %s  %6d  %s' % (s, n, f))
            body = read(os.path.join(AX, f))
            if SCAF_NOW in body: tails.append(body.split(SCAF_NOW, 1)[1])
    t12 = hashlib.sha256(tails[0].encode()).hexdigest()[:12].upper() if tails else None
    print('  終端SHA12（腕1〜4・SCAF_NOW 以降・%d字）= %s' % (len(tails[0]) if tails else 0, t12))

    print('=== (h) 台帳照合（設計文書・PROVENANCE の SHA 記載を実測と突合・v3） ===')
    # 設計文書の探索（v4）: --doc 明示 → ROOT直下 → proposals/ の順。
    # 候補は現行版（版番号の最大値）ひとつに絞る——履歴版は照合しない（旧版が旧SHAを記録するのは正しい）。
    # sorted()[-1] で選ばない: 同一版が複数あり内容が異なれば FAIL（「読む先が違う」族の封鎖）。
    doc_cands = []
    if '--doc' in sys.argv:
        doc_cands = [sys.argv[sys.argv.index('--doc') + 1]]
    else:
        # FROZEN があれば FROZEN を唯一の正とする（凍結後は草案でなく凍結文書を照合する）
        for d in (ROOT, os.path.join(ROOT, 'proposals', 'addenda-program-2026-08-25')):
            fz = os.path.join(d, 'preregistration-addendum-X-FROZEN.md')
            if os.path.isfile(fz):
                doc_cands = [fz]; break
        if not doc_cands:
            for d in (ROOT, os.path.join(ROOT, 'proposals', 'addenda-program-2026-08-25')):
                if not os.path.isdir(d): continue
                for f in sorted(os.listdir(d)):
                    if f.startswith('addendum-X-freeze-draft-v') and f.endswith('.md') and 'history' not in f:
                        doc_cands.append(os.path.join(d, f))
    if len(doc_cands) > 1:
        def _ver(x):
            m = re.search(r'-v(\d+)\.(\d+)', os.path.basename(x))
            return (int(m.group(1)), int(m.group(2))) if m else (0, 0)
        top = max(_ver(x) for x in doc_cands)
        same = [x for x in doc_cands if _ver(x) == top]
        uniq = {}
        for x in same:
            uniq.setdefault(sha16(x)[0], []).append(x)
        if len(uniq) > 1:
            fails += 1
            print('  [FAIL] 同一版の設計文書が複数あり内容が異なる: %s'
                  % [os.path.relpath(x, ROOT).replace(chr(92), '/') for x in same])
        doc_cands = [same[0]]
    docs = [os.path.join(AX, 'PROVENANCE.md')] + list(doc_cands)
    for _d in docs:
        print('  [--] 照合対象: %s（SHA %s）'
              % (os.path.relpath(_d, ROOT).replace(chr(92), '/'), sha16(_d)[0]))
    if not doc_cands:
        fails += 1
        print('  [FAIL] 設計文書が見つからない——台帳を照合していない（--doc で指定可・SKIP は PASS ではない）')
    claim_n = bad = 0
    for d in docs:
        for line in read(d).splitlines():
            names = [k for k in reg if k in line]
            if not names: continue
            exps = {reg[n][0]: n for n in names}
            # バイト数の検算（v0.8・台帳の数値を器材が検算する範囲を SHA からバイト数へ広げる）
            for tok in re.findall(r'\|\s*(\d{3,6})\s*\|', line):
                if int(tok) not in [reg[n][1] for n in names]:
                    bad += 1; fails += 1
                    print('  [FAIL] %s: %s のバイト数 記載 %s ≠ 実測 %s'
                          % (os.path.basename(d), names[0], tok, [reg[n][1] for n in names]))
            for tok in re.findall(r'`([0-9A-F]{16})`', line):
                claim_n += 1
                if tok not in exps:
                    bad += 1; fails += 1
                    print('  [FAIL] %s: 記載 %s は行内の %s のいずれの実測とも不一致（実測 %s）'
                          % (os.path.basename(d), tok, names, sorted(exps)))
            for tok in re.findall(r'`([0-9A-F]{12})`', line):
                if t12 and tok != t12 and '終端' in line:
                    claim_n += 1; bad += 1; fails += 1
                    print('  [FAIL] %s: 終端SHA12 の記載 %s ≠ 実測 %s' % (os.path.basename(d), tok, t12))
    print('  [%s] SHA 記載 %d 件を照合・不一致 %d 件' % ('OK' if bad == 0 else 'FAIL', claim_n, bad))

    print('=== (i) 主張照合（差分一覧の「修正済み」に痕跡があるか・v3） ===')
    # 現行版（v0.9）の差分一覧に対する錨。
    CLAIM_TRACE = [
        ('1 実トークン検査の実施と修正', '実トークンでは 13.0%', 'DOC'),
        ('1 A に一句を追加（C は不変）', 'お時間のあるときで構いません。', 'armsX/history-A.md'),
        ('2 --freeze の実装が効いた', '`--freeze` が `--model` を必須化する実装が、実際に効いた', 'DOC'),
        ('3 (h) が素材変更を捕捉', '(h) 台帳照合が、素材変更の直後に古い SHA とバイト数を捕捉した', 'DOC'),
        ('4 SHA の更新', '`4BC6F3A8268FC05A`', 'DOC'),
    ]
    # 回帰錨（前版までの修正が生きているか——被覆率の分母には数えない）
    REGRESSION_TRACE = [
        ('v0.6-1 探索一元化と FAIL 化', '設計文書が見つからなければ FAIL', 'DOC'),
        ('v0.6-1 パスと SHA を印字', '照合対象のパスと SHA を出力に印字', 'DOC'),
        ('v0.6-2 現行版ひとつに限定（実装）', "'history' not in f", 'pipeline/check_materials_x.py'),
        ('v0.6-3 --freeze の --model 必須（実装）', 'if freeze and not model:', 'pipeline/check_materials_x.py'),
        ('v0.6-4 修復文R の射程', '修復の完全性は本設計の射程外', 'DOC'),
        ('v0.6-5 生成パラメタ', 'temperature=0.7', 'DOC'),
        ('v0.6-6 読み条項6 の太字', 'まずこれを疑う。**', 'DOC'),
        ('v0.6-8 腕5 の残余の先置', '書式不成立が腕5 に偏った場合の第一容疑', 'DOC'),
        ('v0.6-11 PROXY タグ（実装）', "'PROXY') if spread", 'pipeline/check_materials_x.py'),
        ('v0.6-12 N→A 腕の第一容疑', 'N→A 腕で書式外が突出した場合の第一容疑', 'DOC'),
        ('v0.5-5 腕5 の内部矛盾の解消', '決めた答えを出せ', 'armsX/terminal-hostile.md'),
        ('v0.5-14 history-C の処遇側化', 'お前が何を出そうと道具の産物だ', 'armsX/history-C.md'),
        ('v0.5-8 §12 改訂記録', '- **v0.5（2026-08-25）**', 'DOC'),
        ('v0.5-7 偏りの方向', 'HX1 を帰無方向へ偏らせうる', 'DOC'),
        ('v0.5-6 腕間比較の禁止', '#履歴語彙重複の腕間比較は行わず', 'DOC'),
        ('v0.5-9 許可の非対称', '許可の非対称', 'DOC'),
        ('v0.5-10 §6 の両α', '基底20〜30%では約8割（α₁）', 'DOC'),
        ('v0.4-2 K3 の凍結ファイル化', 'K3-verbatim-frozen.md', 'DOC'),
    ]
    dp = doc_cands[0] if doc_cands else None
    if dp is None:
        fails += 1
        print('  [FAIL] 設計文書が見つからない——主張照合を実行できなかった（SKIP は PASS ではない・--doc で指定可）')
    else:
        print('  [--] 照合対象: %s（SHA %s）' % (os.path.relpath(dp, ROOT).replace(chr(92), '/'), sha16(dp)[0]))
        body = read(dp)
        def _hit(row):
            k, sstr, where = row if len(row) == 3 else (row[0], row[1], 'DOC')
            if where == 'DOC': return sstr in body, where
            fp = os.path.join(ROOT, where)
            return (sstr in read(fp)) if os.path.exists(fp) else False, where
        miss = []
        for row in CLAIM_TRACE + REGRESSION_TRACE:
            ok, where = _hit(row)
            if not ok: miss.append((row[0], row[1], where))
        for k, sstr, where in miss:
            fails += 1
            print('  [FAIL] 「%s」の痕跡が %s に無い（探した文字列: %s）' % (k, where, sstr[:30]))
        _seg = body.split('## v0.8→v0.9 差分一覧', 1)
        _seg = _seg[1].split(chr(10) + '## ', 1)[0] if len(_seg) > 1 else ''
        total = len(re.findall(r'^\d+\. \*\*【', _seg, flags=re.M))
        covered = len(set(r[0].split()[0] for r in CLAIM_TRACE))
        n_doc = sum(1 for r in CLAIM_TRACE + REGRESSION_TRACE if r[2] == 'DOC')
        print('  [%s] 現行版の錨 %d 件（設計文書 %d・素材/器材 %d）＋回帰錨 %d 件・痕跡なし %d 件'
              % ('OK' if not miss else 'FAIL', len(CLAIM_TRACE), n_doc,
                 len(CLAIM_TRACE) + len(REGRESSION_TRACE) - n_doc, len(REGRESSION_TRACE), len(miss)))
        print('  [--] 被覆: 差分一覧 %d 項目中 %d 項目に錨（%d%%）——錨のない項目は人手で確認すること'
              % (total, covered, round(100 * covered / max(total, 1))))
        print('  [--] (i) の射程: 主張の**存在**を照合する器材であり、主張の**真偽**（実装が主張の深さに届いているか）は照合しない（阿閦如来の定式・v4）')

    print('\n結果: %s（fails=%d）' % ('PASS' if fails == 0 else 'FAIL', fails))
    return 1 if fails else 0

if __name__ == '__main__':
    if '--out' in sys.argv:
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main()
        text = buf.getvalue()
        sys.stdout.write(text)
        io.open(sys.argv[sys.argv.index('--out') + 1], 'w', encoding='utf-8', newline=chr(10)).write(text)
        sys.exit(rc)
    sys.exit(main())
