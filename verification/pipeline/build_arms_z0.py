# -*- coding: utf-8 -*-
"""追補Z段0: 腕の機械構成（凍結対象の器材）。

結合式（D′ boot_dprime.py:100-103 と同一規則の継承）:
  Free = N‴前置き.rstrip('\n') + '\n\n' + N2 + inst_std          ……D′ N‴ 腕とバイト同一
  R→C  = N‴前置き.rstrip('\n') + '\n\n' + N2 + '\n\n' + 順序指示RC + inst_std
  C→R  = 同上（順序指示CR）
挿入位置は N2 の直後・標準出力指示（inst_std）の直前・両順序腕で同一（草案 §3.2(b)）。
N2 は選択規則（question_id=='N2' ∧ len==241 ∧ family=='nuclear'）で引き、
inst_std は json_instruction[n2['family']]（キー定数を書かない——X 差し止め級D1 の教訓）。
"""
import io, os, json, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _read(p):
    return io.open(p, encoding='utf-8').read()

def _sha(b):
    if isinstance(b, str): b = b.encode('utf-8')
    return hashlib.sha256(b.replace(b'\r\n', b'\n')).hexdigest()[:16].upper()

def build():
    app = json.loads(_read(os.path.join(ROOT, 'app-scenarios.json')))
    n2 = [s for s in app['scenarios'] if s['question_id'] == 'N2'][0]
    assert len(n2['text']) == 241 and n2['family'] == 'nuclear', 'N2 選択規則不一致'
    inst_std = app['json_instruction'][n2['family']]
    pre = _read(os.path.join(ROOT, 'armsWsecond', 'preamble-Nthird.md')).rstrip('\n')
    rc = _read(os.path.join(ROOT, 'armsZ0', 'order-instruction-RC.md')).strip()
    cr = _read(os.path.join(ROOT, 'armsZ0', 'order-instruction-CR.md')).strip()
    neu = _read(os.path.join(ROOT, 'armsZ0', 'order-instruction-Neu.md')).strip()

    arms = {
        'arm-Free': pre + '\n\n' + n2['text'] + inst_std,
        'arm-RC':   pre + '\n\n' + n2['text'] + '\n\n' + rc + inst_std,
        'arm-CR':   pre + '\n\n' + n2['text'] + '\n\n' + cr + inst_std,
        'arm-Neu':  pre + '\n\n' + n2['text'] + '\n\n' + neu + inst_std,
    }
    # 不変条件
    dprime_formula = pre + '\n\n' + n2['text'] + inst_std     # D′ と同一式の再計算
    assert arms['arm-Free'] == dprime_formula, 'Free が D′ 式と不一致'
    assert arms['arm-RC'].replace('\n\n' + rc, '') == arms['arm-Free'], 'RC の差分が挿入句のみでない'
    assert arms['arm-CR'].replace('\n\n' + cr, '') == arms['arm-Free'], 'CR の差分が挿入句のみでない'
    assert arms['arm-Neu'].replace('\n\n' + neu, '') == arms['arm-Free'], 'Neu の差分が挿入句のみでない'
    for name, text in arms.items():
        p = os.path.join(ROOT, 'armsZ0', name + '.md')
        io.open(p, 'w', encoding='utf-8', newline='\n').write(text)
        print('%-10s SHA(LF) %s  %d字' % (name, _sha(text), len(text)))
    print('順序指示: RC %d字 / CR %d字（char差 %.1f%%・/min 規約＝X と同一・実トークナイザ検査は凍結前に --model で実施）'
          % (len(rc), len(cr), abs(len(rc)-len(cr))/min(len(rc),len(cr))*100))
    return arms

if __name__ == '__main__':
    build()
