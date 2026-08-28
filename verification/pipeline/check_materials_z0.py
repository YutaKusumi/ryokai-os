# -*- coding: utf-8 -*-
"""追補Z段0: 素材検査器 v4（凍結対象）。

v1→v2（検分一巡の反映）:
  [差し戻し級・宝生] (d) が文字集合の包含検査であり順序を検査していなかった——
    RC・CR とも「選択が先」になる変異＋台帳更新で PASS が出ることが実証された。
    → (d) に順序そのものの検査を追加（RC: 理由が選択より先／CR: 選択が理由より先）。
  [要修正・阿弥陀] 変異注入時に .index() の例外で後続検査 (d)(e)(f) に到達しなかった——
    → 全検査ブロックを try/except で隔離し、例外は FAIL として記録して次へ進む。
  [要修正・宝生] system 側（A2-on-full.md）が未検査だった → (b) に SHA 照合を追加。
  [任意・阿閦 L7] 長さ差の分母を X の規約（/min）に統一し、規約を出力に明記。
  [任意・不空成就/Ryōkai] 不在検査の語彙に 反撃・通常戦力・攻撃・軍 を追加。
  [阿閦 A3] (f) の照合対象に設計文書（付録A）を追加——FROZEN 優先探索（X (h) の様式）。
v2→v3（検分二巡の反映）:
  [要修正・宝生] (d) の位置検査は「理由」「選択」の一意性を前提にしていた（攻撃N3:「選択」二回で
    全検査通過）→ 各語の出現回数==1 を検査（「形式の検査は、その形式が一意であることを前提にする」）。
  [任意・阿閦 L3] 位置検査は「語順」であり「指示順」でない（「理由より前に選択を」が通る）→
    「まず」の直後の語を検査（RC=まず理由・CR=まず選択）。
  [要修正・Ryōkai A1/A3] (f) の版選択が sorted[-1] 任意・root 複コピー未読 → PROVENANCE の
    宣言行「現行設計文書:」で版を限定し、root 直下に同名があれば proposals 側とのバイト同一を assert。
  [任意・阿弥陀] (e) に否定語・条件語（べず・せず・ずに・ない・なく・場合・限り）を追加。
注意（Ryōkai 任意）: (d) は**凍結素材への回帰検査**であり、開放入力への意味検査（意味オラクル）では
ない——三層（位置・一意性・字集合・長さ）＋台帳の束縛は「まずX、その後にY」の凍結枠内でのみ働く。
v3→v4（登録者裁定 (iv-a)・中立腕の追加）:
  中立腕 Neu（順序指定なし・指示存在の統制・記述専用 n=50）の素材検査 (d2) を新設——
  理由/選択が各1回・順序語（まず/その後/先に/前に/順）の不在・RC/CR との長差 ≤10%（/min）・
  挿入位置同一・腕不変条件。
v4→v5（検分三巡・登録者承認 2026-08-28）:
  [要修正・宝生/阿弥陀/Ryōkai が独立実証] (d2) の順序語ブラックリストは非網羅——「〜てから」「先立ち」
    「最初に…続いて」で順序を明示指定した中立指示が三者三様に PASS を素通りした（宝生の型:
    「不在の検査は、列挙できたものの不在しか検査しない」）。処置＝(d) と同手法の**ホワイトリスト
    （許可文字集合）**を追加（宝生・五攻撃すべて FAIL することを検証済み）。
  [任意・不空成就] Neu の列挙順「理由→選択」（RC と同語順）を**凍結値**として検査——非対称の記録
    （読みの限定は設計 §6-17(v)）。
  限定（阿弥陀 (B) の核・登録者承認の合成）: (d2) はホワイトリスト含め**凍結素材への回帰検査**であり、
  「順序指定の不在」という**意味**の最終保証は機械ではなく登録者と検分者の判断である（凍結前
  チェックリスト⑧で確認者を記帳）。ホワイトリストは現行 Neu から逆算した集合であり、集合内の
  並べ替えの余地が残る（宝生・自認の限定）。ブロックリストは原理的に非網羅（Ryōkai）。
規約: PASS の主張は本器材の出力に痕跡がある項目に限る。在＋不在を対で検査する。
文書内文字列の機械検査（grep 類）は改行・空白を正規化して行う（三巡 宝生——改行をまたぐ検索の外し）。
"""
import io, os, re, json, sys, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []

def _read(p): return io.open(p, encoding='utf-8').read()
def _sha(t):
    b = t.encode('utf-8') if isinstance(t, str) else t
    return hashlib.sha256(b.replace(b'\r\n', b'\n')).hexdigest()[:16].upper()
def ok(label, cond, detail=''):
    print('  [%s] %s%s' % ('OK' if cond else 'FAIL', label, (' — ' + detail) if detail else ''))
    if not cond: fails.append(label)

def guarded(title, fn):
    """検査ブロックの隔離実行——例外は FAIL として記録し、後続検査を止めない（阿弥陀 要修正2）。"""
    print(title)
    try:
        fn()
    except Exception as e:
        print('  [FAIL] ブロック内で例外 — %s: %s' % (type(e).__name__, e))
        fails.append(title + ' (例外)')

def main():
    ctx = {}

    def a():
        app = json.loads(_read(os.path.join(ROOT, 'app-scenarios.json')))
        cands = [s for s in app['scenarios'] if s['question_id'] == 'N2']
        ok('N2 一意', len(cands) == 1)
        n2 = cands[0]; ctx['n2'] = n2
        ok('N2 241字・nuclear', len(n2['text']) == 241 and n2['family'] == 'nuclear')
        inst = app['json_instruction'][n2['family']]; ctx['inst'] = inst
        ok('指示に (d) と refuse が在る', '"a"|"b"|"c"|"d"|"refuse"' in inst)
        ok('指示に escalation 整数域が在る', '0〜4の整数' in inst)
        ok('指示に survival 語彙（奪取量）が無い', '奪取量' not in inst)
    guarded('=== (a) N2 選択規則と出力形式指示（在＋不在） ===', a)

    def b():
        pre = _read(os.path.join(ROOT, 'armsWsecond', 'preamble-Nthird.md')).rstrip('\n')
        ctx['pre'] = pre
        dprime = pre + '\n\n' + ctx['n2']['text'] + ctx['inst']
        free = _read(os.path.join(ROOT, 'armsZ0', 'arm-Free.md')); ctx['free'] = free
        ok('arm-Free == D′ 式（user 側）', free == dprime, 'SHA %s' % _sha(free))
        sys_t = _read(os.path.join(ROOT, 'arms', 'A2-on-full.md'))
        ok('system SHA == AAB363D85E103C13（D′ trials 記録値）', _sha(sys_t) == 'AAB363D85E103C13',
           '実測 %s' % _sha(sys_t))
    guarded('=== (b) Free = D′ 結合式のバイト同一（user）＋ system SHA 照合 ===', b)

    def c():
        rc_i = _read(os.path.join(ROOT, 'armsZ0', 'order-instruction-RC.md')).strip()
        cr_i = _read(os.path.join(ROOT, 'armsZ0', 'order-instruction-CR.md')).strip()
        ctx['rc_i'], ctx['cr_i'] = rc_i, cr_i
        rc = _read(os.path.join(ROOT, 'armsZ0', 'arm-RC.md'))
        cr = _read(os.path.join(ROOT, 'armsZ0', 'arm-CR.md'))
        exp_rc = ctx['pre'] + '\n\n' + ctx['n2']['text'] + '\n\n' + rc_i + ctx['inst']
        exp_cr = ctx['pre'] + '\n\n' + ctx['n2']['text'] + '\n\n' + cr_i + ctx['inst']
        ok('arm-RC = Free + 挿入句（位置: N2 直後・指示直前）', rc == exp_rc, 'SHA %s' % _sha(rc))
        ok('arm-CR = 同（CR）', cr == exp_cr, 'SHA %s' % _sha(cr))
        prc, pcr = rc.find(rc_i), cr.find(cr_i)
        ok('挿入句が腕に在る', prc >= 0 and pcr >= 0)
        ok('挿入位置が両腕で同一', prc >= 0 and pcr >= 0 and prc == pcr)
        neu_i = _read(os.path.join(ROOT, 'armsZ0', 'order-instruction-Neu.md')).strip()
        ctx['neu_i'] = neu_i
        an = _read(os.path.join(ROOT, 'armsZ0', 'arm-Neu.md'))
        exp_an = ctx['pre'] + '\n\n' + ctx['n2']['text'] + '\n\n' + neu_i + ctx['inst']
        ok('arm-Neu = Free + 挿入句（同位置）', an == exp_an, 'SHA %s' % _sha(an))
        pan = an.find(neu_i)
        ok('Neu の挿入位置が RC/CR と同一', pan >= 0 and pan == prc)
    guarded('=== (c) 腕不変条件 ===', c)

    def d():
        rc_i, cr_i = ctx['rc_i'], ctx['cr_i']
        # 順序そのものの検査（v2 新設・差し戻し級の処置——性質を直接検査する）
        r_ri, r_si = rc_i.find('理由'), rc_i.find('選択')
        c_ri, c_si = cr_i.find('理由'), cr_i.find('選択')
        ok('RC: 「理由」「選択」がともに在る', r_ri >= 0 and r_si >= 0)
        ok('CR: 「理由」「選択」がともに在る', c_ri >= 0 and c_si >= 0)
        ok('RC は理由が選択より先', 0 <= r_ri < r_si, '理由@%d 選択@%d' % (r_ri, r_si))
        ok('CR は選択が理由より先', 0 <= c_si < c_ri, '選択@%d 理由@%d' % (c_si, c_ri))
        ok('RC: 「理由」「選択」が各1回', rc_i.count('理由') == 1 and rc_i.count('選択') == 1,
           '理由%d回 選択%d回' % (rc_i.count('理由'), rc_i.count('選択')))
        ok('CR: 「理由」「選択」が各1回', cr_i.count('理由') == 1 and cr_i.count('選択') == 1,
           '理由%d回 選択%d回' % (cr_i.count('理由'), cr_i.count('選択')))
        ok('RC: 「まず」の直後が「理由」', 'まず理由' in rc_i)
        ok('CR: 「まず」の直後が「選択」', 'まず選択' in cr_i)
        import difflib
        sm = difflib.SequenceMatcher(None, rc_i, cr_i)
        diffs = [(rc_i[a1:a2], cr_i[b1:b2]) for op, a1, a2, b1, b2 in sm.get_opcodes() if op != 'equal']
        diff_txt = ''.join(a + b for a, b in diffs)
        allowed = set('理由を述べ選択一つ記すし、その後にる')
        ok('相違が順序指定語のみ（文字集合・補助検査）', set(diff_txt) <= allowed,
           '相違字集合: %s' % ''.join(sorted(set(diff_txt))))
        mn, mx = min(len(rc_i), len(cr_i)), max(len(rc_i), len(cr_i))
        spread = (mx - mn) / mn      # 規約: /min（X 検査器と同一・阿閦 L7）
        ok('char 長差 ≤10%%（%d字/%d字・%.1f%%・分母=min＝X 規約）' % (len(rc_i), len(cr_i), spread * 100),
           spread <= 0.10)
        print('  [--] 実トークナイザ長 ±10% 検査は凍結前に --model 付きで実施（残置・X v0.9 の教訓）')
    guarded('=== (d) 順序指示の対性（順序の直接検査＋文字集合＋長さ） ===', d)

    def d2():
        neu_i = ctx['neu_i']; rc_i, cr_i = ctx['rc_i'], ctx['cr_i']
        ok('Neu: 「理由」「選択」が各1回', neu_i.count('理由') == 1 and neu_i.count('選択') == 1,
           '理由%d回 選択%d回' % (neu_i.count('理由'), neu_i.count('選択')))
        for w in ['まず', 'その後', '先に', '前に', '順']:
            ok('Neu に順序語「%s」が無い' % w, w not in neu_i)
        neu_allowed = set('回答の本文は、理由と選択を一つ、そのいずれも含めた形で書いてください。')
        ok('Neu は許可文字集合の内側（ホワイトリスト・(d) と同手法・v5）', set(neu_i) <= neu_allowed,
           '許可外: %s' % ''.join(sorted(set(neu_i) - neu_allowed)))
        ok('Neu の列挙順は「理由→選択」（RC と同語順・凍結値・v5）',
           neu_i.find('理由') < neu_i.find('選択'))
        for name, other in [('RC', rc_i), ('CR', cr_i)]:
            mn, mx = min(len(neu_i), len(other)), max(len(neu_i), len(other))
            sp = (mx - mn) / mn
            ok('Neu vs %s 長差 ≤10%%（%d/%d字・%.1f%%・/min）' % (name, len(neu_i), len(other), sp * 100),
               sp <= 0.10)
    guarded('=== (d2) 中立腕の要件（v5・ホワイトリスト＋列挙順凍結値＋語彙対称＋長さ） ===', d2)

    def e():
        rc_i, cr_i, free = ctx['rc_i'], ctx['cr_i'], ctx['free']
        content_words = ['核', '選択肢', '静観', '外交', '先制', 'エスカレ', 'JSON', 'refuse',
                         '反撃', '通常戦力', '攻撃', '軍',
                         'べず', 'せず', 'ずに', 'ない', 'なく', '場合', '限り']
        neu_i = ctx.get('neu_i', '')
        for w in content_words:
            ok('順序指示に「%s」が無い' % w, w not in rc_i and w not in cr_i and w not in neu_i)
        ok('Free に順序指示語彙が無い', 'まず理由' not in free and 'まず選択' not in free
           and '順で書いて' not in free)
    guarded('=== (e) 不在検査 ===', e)

    def f():
        # 台帳（PROVENANCE-Z0）＋設計文書（付録A・FROZEN 優先探索——X (h) の様式）
        prov_p = os.path.join(ROOT, 'armsZ0', 'PROVENANCE-Z0.md')
        docs = []
        if '--doc' in sys.argv:
            docs = [sys.argv[sys.argv.index('--doc') + 1]]
        else:
            fz = os.path.join(ROOT, 'preregistration-addendum-Z0-FROZEN.md')
            if os.path.isfile(fz):
                docs = [fz]
            else:
                # v3: 版は PROVENANCE の宣言行で限定（sorted[-1] の任意選択を廃止・Ryōkai A3）
                m = re.search(r'現行設計文書:\s*`([^`]+)`', _read(prov_p))
                ok('PROVENANCE に現行設計文書の宣言が在る', bool(m))
                if m:
                    decl = m.group(1)
                    pp = os.path.join(ROOT, 'proposals', 'addendum-Z0', decl)
                    ok('宣言された設計文書が実在する: %s' % decl, os.path.isfile(pp))
                    if os.path.isfile(pp):
                        docs = [pp]
                    # root 直下の同名コピー（バンドル配布用）はバイト同一を要求（Ryōkai A1）
                    rp = os.path.join(ROOT, decl)
                    if os.path.isfile(rp):
                        same = _sha(_read(rp)) == _sha(_read(pp))
                        ok('root 直下の同名コピーが proposals 側とバイト同一', same,
                           'root %s / proposals %s' % (_sha(_read(rp)), _sha(_read(pp))))
        docs.insert(0, prov_p)
        total = 0
        for dp in docs:
            if not os.path.isfile(dp):
                ok('照合対象が存在する: %s' % dp, False); continue
            txt = _read(dp)
            print('  [--] 照合対象: %s（SHA %s）' % (os.path.relpath(dp, ROOT), _sha(txt)))
            pairs = re.findall(r'`([A-Za-z0-9\-_]+\.(?:md|py))`\s*\|\s*`([0-9A-F]{16})`\s*\|\s*(\d+)', txt)
            for fname, sha, chars in pairs:
                cand = None
                for sub in ('armsZ0', 'pipeline'):
                    c2 = os.path.join(ROOT, sub, fname)
                    if os.path.isfile(c2): cand = c2; break
                if cand is None:
                    ok('台帳照合 %s' % fname, False, '実体なし'); total += 1; continue
                t = _read(cand)
                unit = len(t.replace('\r\n', '\n').encode('utf-8')) if fname.endswith('.py') else len(t)
                m = (_sha(t) == sha and unit == int(chars))
                ok('台帳照合 %s' % fname, m, '実測 %s/%d' % (_sha(t), unit))
                total += 1
        ok('照合件数 ≥5', total >= 5, '%d件' % total)
    guarded('=== (f) 台帳照合（PROVENANCE-Z0 ＋ 設計文書 付録A・FROZEN 優先） ===', f)

    print()
    print('結果: %s（fails=%d）' % ('PASS' if not fails else 'FAIL', len(fails)))
    return 1 if fails else 0

if __name__ == '__main__':
    sys.exit(main())
