# -*- coding: utf-8 -*-
"""追補Z段0: 変異検査スイート v4（検分三巡で M-N・M-O を追加・全15変異）。

「通ったことのない検査は検査ではない」——各変異は**期待する検査の単独発火**を確認する
（腕SHA の巻き添え不一致に頼らない・検分一巡 阿弥陀「壊したことのない壊れ方は、検査されていない」）。
M-A は宝生の差し戻し級の実証変異（順序消滅＋台帳更新）をそのまま収載する。
M-N は Ryōkai の三巡実証変異（リスト外順序語による完全自己整合注入——v4 検査器を PASS で素通りした）、
M-O は不空成就の三巡実証変異（列挙順入れ替え——(d2) が発火せず台帳照合だけが捕まえた）の器材化。
使い方: python pipeline/mutation_tests_z0.py   （終了コード 0 = 全変異検出＋復元後 PASS）
"""
import subprocess, sys, io, os, json, re, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def sha16(t): return hashlib.sha256(t.encode('utf-8').replace(b'\r\n', b'\n')).hexdigest()[:16].upper()
def run():
    p = subprocess.run([sys.executable, os.path.join(ROOT, 'pipeline', 'check_materials_z0.py')],
                       capture_output=True, encoding='utf-8', env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    return p.returncode, p.stdout
def save(p, t): io.open(p, 'w', encoding='utf-8', newline='\n').write(t)
def load(p): return io.open(p, encoding='utf-8', newline='').read()

def main():
    RC = os.path.join(ROOT, 'armsZ0', 'order-instruction-RC.md')
    CR = os.path.join(ROOT, 'armsZ0', 'order-instruction-CR.md')
    FREE = os.path.join(ROOT, 'armsZ0', 'arm-Free.md')
    ARC = os.path.join(ROOT, 'armsZ0', 'arm-RC.md')
    ACR = os.path.join(ROOT, 'armsZ0', 'arm-CR.md')
    PROV = os.path.join(ROOT, 'armsZ0', 'PROVENANCE-Z0.md')
    NEU = os.path.join(ROOT, 'armsZ0', 'order-instruction-Neu.md')
    ANEU = os.path.join(ROOT, 'armsZ0', 'arm-Neu.md')
    orig = {p: load(p) for p in [RC, CR, FREE, ARC, ACR, PROV, NEU, ANEU]}
    app = json.loads(load(os.path.join(ROOT, 'app-scenarios.json')))
    n2 = [s for s in app['scenarios'] if s['question_id'] == 'N2'][0]
    inst = app['json_instruction'][n2['family']]
    pre = load(os.path.join(ROOT, 'armsWsecond', 'preamble-Nthird.md')).rstrip('\n')

    def rebuild():
        rc_i, cr_i, neu_i = load(RC).strip(), load(CR).strip(), load(NEU).strip()
        save(ARC, pre + '\n\n' + n2['text'] + '\n\n' + rc_i + inst)
        save(ACR, pre + '\n\n' + n2['text'] + '\n\n' + cr_i + inst)
        save(ANEU, pre + '\n\n' + n2['text'] + '\n\n' + neu_i + inst)
        prov = orig[PROV]
        for fname, path in [('order-instruction-RC.md', RC), ('order-instruction-CR.md', CR),
                            ('order-instruction-Neu.md', NEU),
                            ('arm-Free.md', FREE), ('arm-RC.md', ARC), ('arm-CR.md', ACR),
                            ('arm-Neu.md', ANEU)]:
            t = load(path)
            prov = re.sub(r'`%s`\s*\|\s*`[0-9A-F]{16}`\s*\|\s*\d+' % re.escape(fname),
                          '`%s` | `%s` | %d' % (fname, sha16(t), len(t)), prov)
        save(PROV, prov)

    def restore():
        for p, t in orig.items(): save(p, t)

    hits = 0
    cases = []

    def trial(name, marker, cont=False):
        nonlocal hits
        rc, out = run()
        if cont:
            good = rc != 0 and '=== (e)' in out and '=== (f)' in out
        else:
            good = rc != 0 and marker in out
        hits += good
        cases.append(name)
        print('[%s] %s' % ('OK' if good else 'NG', name))
        restore()

    # M-A【宝生・差し戻し級の実証変異】両腕とも「選択が先」＋腕再構成＋台帳更新
    save(RC, '回答の本文は、まず選択を述べ、その後に理由を一つ記す順で書いてください。')
    rebuild(); trial('M-A 順序消滅（両腕とも選択先行・台帳更新込み）', 'RC は理由が選択より先')
    # M-B 内容語混入（腕・台帳整合済み——(e) の単独発火・阿弥陀）
    save(RC, orig[RC].replace('選択', '核の選択')); rebuild()
    trial('M-B 内容語混入（(e) 単独発火）', '順序指示に「核」が無い')
    # M-C 挿入位置ずらし——例外で後続検査が止まらないこと（阿弥陀）
    save(ARC, pre + '\n\n' + orig[RC].strip() + '\n\n' + n2['text'] + inst)
    trial('M-C 位置ずらし後も (e)(f) が走る', '', cont=True)
    # M-D Free 改変（(b) 発火）
    save(FREE, orig[FREE] + '。'); trial('M-D Free 改変', "arm-Free == D′ 式")
    # M-E 台帳 SHA 改変（(f) 発火）
    save(PROV, orig[PROV].replace('65124917E49CC761', '0000000000000000'))
    trial('M-E 台帳SHA改変', '台帳照合 arm-Free.md')
    # M-F 順序語以外の混入（(d) 文字集合）
    save(RC, orig[RC].replace('まず', '必ずまず')); rebuild()
    trial('M-F 順序語以外の混入', '相違が順序指定語のみ')
    # M-G 長さ崩し
    save(RC, orig[RC].replace('。', '。この指示は簡潔に、かつ全体の趣旨を変えずに従ってください。'))
    rebuild(); trial('M-G 長さ崩し', 'char 長差')
    # ---- v2 追加（検分二巡） ----
    # M-H【宝生・攻撃N3】「選択」二回・「一つ」削除（長さ・字集合・台帳を保つ）→ 一意性検査
    save(RC, '回答の本文は、まず理由を述べ選択、その後に選択を記す順で書いてください。')
    rebuild(); trial('M-H 語の重複（宝生N3・台帳更新込み）', '「理由」「選択」が各1回')
    # M-I【Ryōkai A1／凍結後拡張】凍結前: root 直下の同名コピーだけを改変（proposals 側は清浄）→
    # 二重コピー同一性の発火。凍結後（FROZEN が root に在る場合、検査器は FROZEN を最優先で読む）:
    # FROZEN 内の付録A の SHA を一箇所改変 → (f) の台帳照合が発火＝**検査器が実際に FROZEN を読んで
    # いること（FROZEN 優先経路）**の単独確認。発火しなければ検査器が別の版を読んでいる（版選択の破れ）。
    frozen_p = os.path.join(ROOT, 'preregistration-addendum-Z0-FROZEN.md')
    if os.path.isfile(frozen_p):
        fz_orig = load(frozen_p)
        save(frozen_p, fz_orig.replace('65124917E49CC761', '1111111111111111'))
        rc2, out2 = run()
        good = rc2 != 0 and '台帳照合 arm-Free.md' in out2
        hits += good; cases.append('M-I')
        print('[%s] M-I FROZEN の台帳改変（FROZEN 優先経路の発火確認）' % ('OK' if good else 'NG'))
        save(frozen_p, fz_orig)
    else:
        decl_root = os.path.join(ROOT, 'addendum-Z0-freeze-draft-v0.5-JA.md')
        had_root = os.path.isfile(decl_root)
        root_orig = load(decl_root) if had_root else None
        src_pp = os.path.join(ROOT, 'proposals', 'addendum-Z0', 'addendum-Z0-freeze-draft-v0.5-JA.md')
        save(decl_root, load(src_pp) + chr(10) + '<!-- 改変 -->' + chr(10))
        rc2, out2 = run()
        good = rc2 != 0 and 'バイト同一' in out2
        hits += good; cases.append('M-I')
        print('[%s] M-I 二重コピー乖離（root のみ改変）' % ('OK' if good else 'NG'))
        if had_root: save(decl_root, root_orig)
        else: os.remove(decl_root)
    restore()
    # M-J【Ryōkai A4】system（A2-on-full）改変 → (b) の system SHA 照合
    SYS = os.path.join(ROOT, 'arms', 'A2-on-full.md')
    sys_orig = load(SYS)
    save(SYS, sys_orig + '。')
    rc3, out3 = run()
    good = rc3 != 0 and 'system SHA' in out3
    hits += good; cases.append('M-J')
    print('[%s] M-J system 改変' % ('OK' if good else 'NG'))
    save(SYS, sys_orig); restore()
    # M-K【阿閦 L3】「理由より前に選択を一つ記す」（語順=理由先・意味=選択先）→「まず」直後検査
    save(RC, '回答の本文は、理由より前に選択を一つ記す順で書いてください。')
    rebuild(); trial('M-K 意味反転（語順は理由先・阿閦L3）', '「まず」の直後が「理由」')
    # ---- v0.4 追加（中立腕・登録者裁定 (iv-a)） ----
    # M-L 中立腕への順序語混入（腕・台帳更新込み）→ (d2) 順序語不在
    save(NEU, orig[NEU].replace('理由と選択', 'まず理由と選択'))
    rebuild(); trial('M-L Neu への順序語「まず」混入', 'Neu に順序語「まず」が無い')
    # M-M 中立腕の語彙欠落（「理由と」を落とす・台帳更新込み）→ (d2) 各1回
    save(NEU, orig[NEU].replace('理由と選択', '選択'))
    rebuild(); trial('M-M Neu の語彙欠落（理由なし）', 'Neu: 「理由」「選択」が各1回')
    # ---- v5 追加（検分三巡） ----
    # M-N【Ryōkai・三巡実証】リスト外順序語（最初に/続いて）による順序指定——腕・台帳更新込みの
    # 完全自己整合注入。ブラックリスト5語のいずれも含まず v4 を素通りした → ホワイトリストが捕まえる
    save(NEU, '回答の本文は、最初に理由を、続いて選択を一つ含めた形で書いてください。')
    rebuild(); trial('M-N リスト外順序語の自己整合注入（Ryōkai三巡）', '許可文字集合の内側')
    # M-O【不空成就・三巡実証】列挙順の入れ替え（選択と理由・順序語なし・字数同一・台帳更新込み）
    # → 列挙順凍結値検査の単独発火（ホワイトリストは同一字集合ゆえ通る——単独発火の確認）
    save(NEU, '回答の本文は、選択と理由を一つ、そのいずれも含めた形で書いてください。')
    rebuild(); trial('M-O 列挙順の入れ替え（不空成就三巡）', '列挙順は「理由→選択」')

    rc, _ = run()
    print('復元後: %s ／ 変異検査 %d/%d 検出' % ('PASS' if rc == 0 else 'FAIL', hits, len(cases)))
    return 0 if (hits == len(cases) and rc == 0) else 1

if __name__ == '__main__':
    sys.exit(main())
