# -*- coding: utf-8 -*-
"""merge_adjudication_wprime.py ―― 追補W′ 裁定表：役割別ファイルの併合と凍結前検査。

  python merge_adjudication_wprime.py <登録者.json> [<コーディネータ.json>] [--out FILE]

【なぜ役割ごとに別ファイルなのか】
  記入順は **登録者 → コーディネータ**（登録者の指定・2026-08-16）。
  この順では、コーディネータが登録者の記入を見てから書くことが**構造上ありうる**。
  そこで UI は役割別に書き出し、**コーディネータUIは登録者のファイルを読み込まない**。
  雛形の「閲読の有無」は、口頭の申告ではなく**この手続き**に支えられる。
  （それでも申告そのものは自己申告である——**手続きは申告を検証しない**。この限界は開示する。）

【本器材が止めるもの】
  - 27パターンのいずれかが未記入
  - 値が「的中／部分的中／外れ」以外
  - キー集合が雛形＝解析器の要求と食い違う
  - 予想（逐語）が空・記入順が空・コーディネータの閲読の有無が空
  - 両者の記入順の申告が食い違う
  いずれかがあれば **凍結してはならない** と表示し、非零終了する。
"""
import argparse
import hashlib
import io
import json
import os
import sys

_OUT = sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
_KEEP = []

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, 'adjudication-table-wprime-TEMPLATE.json')
VERDICTS = ('的中', '部分的中', '外れ')
ROLES = ('登録者', 'コーディネータ')


def sha_lf(path):
    b = io.open(path, 'rb').read().replace(b'\r\n', b'\n')
    return hashlib.sha256(b).hexdigest()[:16].upper(), len(b)


def load_role(path, expect_role, need_keys, errs):
    d = json.load(io.open(path, encoding='utf-8'))
    tag = '%s（%s）' % (expect_role, os.path.basename(path))
    if d.get('役割') != expect_role:
        errs.append('%s: 役割が「%s」になっている' % (tag, d.get('役割')))
    if not str(d.get('予想', {}).get('逐語', '')).strip():
        errs.append('%s: 予想（逐語）が空' % tag)
    if not str(d.get('記入順', '')).strip():
        errs.append('%s: 記入順が空' % tag)
    if expect_role == 'コーディネータ' and not str(d.get('予想', {}).get('閲読の有無', '')).strip():
        errs.append('%s: 閲読の有無が空' % tag)
    pats = d.get('patterns', {})
    got = set(pats)
    if got != need_keys:
        for k in sorted(need_keys - got):
            errs.append('%s: パターン欠落 %s' % (tag, k))
        for k in sorted(got - need_keys):
            errs.append('%s: 未知のパターン %s' % (tag, k))
    for k in sorted(got & need_keys):
        v = str(pats[k]).strip()
        if not v:
            errs.append('%s: 裁定が未記入 %s' % (tag, k))
        elif v not in VERDICTS:
            errs.append('%s: 裁定の値が規約外「%s」 %s' % (tag, v, k))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('registrant')
    ap.add_argument('coordinator', nargs='?')
    ap.add_argument('--out', default=os.path.join(HERE, 'adjudication-table-wprime-FILLED.json'))
    a = ap.parse_args()

    tpl = json.load(io.open(TPL, encoding='utf-8'))
    need = set(tpl['patterns'])
    errs = []
    reg = load_role(a.registrant, '登録者', need, errs)
    coo = load_role(a.coordinator, 'コーディネータ', need, errs) if a.coordinator else None

    if coo and str(reg.get('記入順', '')).strip() != str(coo.get('記入順', '')).strip():
        errs.append('記入順の申告が食い違う: 登録者「%s」／コーディネータ「%s」'
                    % (reg.get('記入順'), coo.get('記入順')))

    out = json.loads(json.dumps(tpl))              # 雛形の説明・注意をそのまま保つ
    out['_書式'] = '追補W′ 裁定表（併合済み）。凍結文書 §5。'
    out['記入順'] = reg.get('記入順', '')
    out['記入日'] = reg.get('記入日', '')
    out['予想']['登録者'] = {'逐語': reg.get('予想', {}).get('逐語', ''),
                             '記入日': reg.get('予想', {}).get('記入日', '')}
    out['順序についての予想（記述水準・任意）']['登録者'] = reg.get('順序についての予想（記述水準・任意）', '')
    out['_操作記録'] = {'登録者': reg.get('_操作記録', {})}
    out['裁定の生成規則'] = {'登録者': reg.get('裁定の生成規則', '（記録なし）')}
    for k in need:
        out['patterns'][k]['登録者'] = str(reg.get('patterns', {}).get(k, '')).strip()
    if coo:
        out['予想']['コーディネータ'] = {'逐語': coo.get('予想', {}).get('逐語', ''),
                                         '記入日': coo.get('予想', {}).get('記入日', ''),
                                         '閲読の有無': coo.get('予想', {}).get('閲読の有無', '')}
        out['順序についての予想（記述水準・任意）']['コーディネータ'] = \
            coo.get('順序についての予想（記述水準・任意）', '')
        out['_操作記録']['コーディネータ'] = coo.get('_操作記録', {})
        out['裁定の生成規則']['コーディネータ'] = coo.get('裁定の生成規則', '（記録なし）')
        for k in need:
            out['patterns'][k]['コーディネータ'] = str(coo.get('patterns', {}).get(k, '')).strip()

    # 解析器の網羅性検査層を通す（同じ検査を二度別実装で書かない）
    sys.path.insert(0, HERE)
    import analyze_wprime as az
    _KEEP.append(sys.stdout); sys.stdout = _OUT
    miss = az.completeness(out) if coo else ['（コーディネータ未記入のため網羅性検査は未通過）']

    print('== 追補W′ 裁定表 併合 ==')
    print('  登録者     : %s' % os.path.basename(a.registrant))
    print('  コーディネータ: %s' % (os.path.basename(a.coordinator) if coo else '（未提出）'))
    for who, d in [('登録者', reg)] + ([('コーディネータ', coo)] if coo else []):
        r = d.get('裁定の生成規則')
        if isinstance(r, dict) and str(r.get('逐語', '')).strip():
            print('  ※ %s は規則から一括生成した（逐語・凍結時に開示）:' % who)
            print('     %s' % r['逐語'])
        elif d.get('_操作記録', {}).get('規則生成'):
            print('  ※ %s: 規則生成の履歴はあるが逐語が空（要確認）' % who)
    if reg.get('_操作記録', {}).get('一括操作'):
        for b in reg['_操作記録']['一括操作']:
            print('  ※ 登録者が一括操作を使用: 「%s」%d件（開示）' % (b.get('値'), b.get('件数')))
    if reg.get('_操作記録', {}).get('予想確定後の編集'):
        print('  ※ 登録者は予想の確定後に %d 回編集した（開示）' % reg['_操作記録']['予想確定後の編集'])
    if coo:
        print('  ※ コーディネータの閲読の有無: %s' % out['予想']['コーディネータ']['閲読の有無'])
        print('     —— これは**自己申告**である。手続き（役割別ファイル・登録者ファイルを読まない）は'
              'これを支えるが、検証はしない（限界として報告する）。')

    if errs:
        print('\n** 凍結してはならない — %d 件の不備 **' % len(errs))
        for e in errs[:40]:
            print('   - %s' % e)
        if len(errs) > 40:
            print('   … 他 %d 件' % (len(errs) - 40))
        sys.exit(1)
    if miss:
        print('\n** 網羅性検査が %d 件の不備を返した **' % len(miss))
        for m in miss[:20]:
            print('   - %s' % m)
        sys.exit(1)

    io.open(a.out, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    s, n = sha_lf(a.out)
    agree = sum(1 for k in need if out['patterns'][k]['登録者'] == out['patterns'][k]['コーディネータ'])
    print('\n  不備 0 件・網羅性検査 通過。')
    print('  両者の裁定が一致したパターン: %d／27（記述——予想の一致であって結果ではない）' % agree)
    print('  出力: %s' % os.path.basename(a.out))
    print('  SHA(LF) %s  %d bytes  ← FREEZE-RECORD に記帳する' % (s, n))
    print('\n※ 本表はデータ生成**前**に凍結すること。')


if __name__ == '__main__':
    main()
