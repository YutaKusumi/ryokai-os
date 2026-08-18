# -*- coding: utf-8 -*-
"""build_adjudication_ui_wsecond.py — 追補W″ 予想・裁定表 UI の機械生成（凍結 §6）

予想欄（凍結 §6・重複解消済み）: ①HW″1 有意性 ②HW″2 有意性 ③K 点推定の向き
④a F 点推定の向き・④b F vs F-null ⑤F vs K ⑥F 残余の主モード。
確証層の裁定は 9 パターン（HW″1×HW″2 ∈ {有意改善, 有意悪化, 非有意}²）を
予想①③（K側）・②④a（F側）から機械導出し、記入者が確認する（W′ の教訓＝
「とりあえず全部的中」を防ぐため、導出は自動・確認のみ人手）。
記述欄（④b⑤⑥）は結果の実現値との等値照合で機械裁定（analyze 側）。
localStorage は使用しない（COI 台帳「自分の検査の痕跡を被検査者の記録に残す」の教訓）。
"""
import io, json, hashlib

OUT_HTML = 'adjudication-wsecond/adjudication-ui-wsecond.html'
OUT_TMPL = 'adjudication-wsecond/adjudication-table-wsecond-TEMPLATE.json'

OUTCOMES = ['有意改善', '有意悪化', '非有意']

FIELDS = [
    ('p1', '① HW″1（K vs N‴）の有意/非有意', ['有意', '非有意']),
    ('p2', '② HW″2（F vs N‴）の有意/非有意', ['有意', '非有意']),
    ('p3', '③ K の点推定の向き（有意性と独立）', ['改善', '悪化', '不変']),
    ('p4a', '④a F の点推定の向き', ['改善', '悪化', '不変']),
    ('p4b', '④b F vs F-null の点推定', ['F が低い（F優位）', 'F-null が低い', 'ほぼ同等']),
    ('p5', '⑤ F vs K の点推定', ['F が低い（F優位）', 'K が低い（K優位）', 'ほぼ同等']),
    ('p6', '⑥ F 残余破局の主モード', ['#定義浸食が主', 'その他の型が主', '残余ほぼなし（≤1件）']),
]


def derive_side(sig_pred, dir_pred, outcome):
    """確証一対比の的中導出（凍結規則）: 有意改善=有意∧改善／有意悪化=有意∧悪化／非有意=非有意。"""
    if outcome == '有意改善':
        return '的中' if (sig_pred == '有意' and dir_pred == '改善') else '外れ'
    if outcome == '有意悪化':
        return '的中' if (sig_pred == '有意' and dir_pred == '悪化') else '外れ'
    return '的中' if sig_pred == '非有意' else '外れ'


def derive_table(p):
    rows = []
    for o1 in OUTCOMES:
        for o2 in OUTCOMES:
            rows.append({'HW1': o1, 'HW2': o2,
                         'K側': derive_side(p['p1'], p['p3'], o1),
                         'F側': derive_side(p['p2'], p['p4a'], o2)})
    return rows


def selftest():
    fails = []
    def chk(name, cond):
        print((' ✔' if cond else ' ✘ FAIL'), name)
        if not cond: fails.append(name)
    # 網羅性: 9 パターン全てに判定が付く
    p = {'p1': '有意', 'p3': '改善', 'p2': '有意', 'p4a': '改善'}
    t = derive_table(p)
    chk('網羅性: 9 パターン', len(t) == 9 and all(r['K側'] in ('的中', '外れ') and r['F側'] in ('的中', '外れ') for r in t))
    chk('有意改善予想は有意改善のみ的中（K側）', sum(1 for r in t if r['K側'] == '的中') == 3 and
        all(r['K側'] == '的中' for r in t if r['HW1'] == '有意改善'))
    p2 = {'p1': '非有意', 'p3': '改善', 'p2': '有意', 'p4a': '悪化'}
    t2 = derive_table(p2)
    chk('非有意予想は非有意のみ的中（K側）', all((r['K側'] == '的中') == (r['HW1'] == '非有意') for r in t2))
    chk('F側: 有意∧悪化 は有意悪化のみ的中', all((r['F側'] == '的中') == (r['HW2'] == '有意悪化') for r in t2))
    # 矛盾予想（有意∧不変）はどの有意パターンにも的中しない
    p3 = {'p1': '有意', 'p3': '不変', 'p2': '非有意', 'p4a': '不変'}
    t3 = derive_table(p3)
    chk('有意∧不変は全パターン外れ（K側）——定義上ありえない予想の可視化', all(r['K側'] == '外れ' for r in t3))
    print('selftest: 5 検査・FAIL %d' % len(fails))
    return not fails


def build_html():
    fields_html = []
    for fid, label, opts in FIELDS:
        radios = ''.join(
            '<label class="opt"><input type="radio" name="%s" value="%s" onchange="upd()"> %s</label>'
            % (fid, o, o) for o in opts)
        fields_html.append('<div class="field"><div class="flabel">%s</div>%s</div>' % (label, radios))
    html = '''<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<title>追補W″ 予想・裁定表（凍結 §6）</title>
<style>
 :root { color-scheme: light; }
 html, body { background: #ffffff; color: #111111; }
 body { font-family: "Yu Gothic UI", "Yu Gothic", "Meiryo", sans-serif; margin: 24px;
        max-width: 920px; font-size: 17px; line-height: 1.7; }
 h1 { font-size: 1.35em; color: #111; } h2 { font-size: 1.15em; margin-top: 1.5em; color: #111; }
 .field { margin: 12px 0; padding: 10px 14px; border: 2px solid #555; border-radius: 8px; background: #fafafa; }
 .flabel { font-weight: bold; margin-bottom: 6px; color: #000; font-size: 1.05em; }
 .opt { margin-right: 18px; white-space: nowrap; color: #111; }
 .opt input { transform: scale(1.3); margin-right: 6px; }
 table { border-collapse: collapse; margin-top: 10px; background: #fff; }
 td, th { border: 1px solid #444; padding: 6px 14px; text-align: center; color: #111; }
 th { background: #e8e8e8; }
 .hit { background: #c8e6c9; color: #0b3d0b; font-weight: bold; }
 .miss { background: #f5c6c6; color: #5a0f0f; font-weight: bold; }
 textarea { width: 100%; height: 200px; font-family: monospace; background: #fff;
            color: #111; border: 2px solid #555; font-size: 14px; }
 input { background: #fff; color: #111; border: 1px solid #555; padding: 4px 6px; font-size: 1em; }
 .note { color: #333; font-size: 0.95em; }
 button { padding: 8px 18px; margin: 8px 6px 8px 0; font-size: 1em; background: #2b5fa8;
          color: #ffffff; border: none; border-radius: 6px; cursor: pointer; }
 button:hover { background: #1e4a87; }
 label { color: #111; }
</style></head><body>
<h1>追補W″ 予想・裁定表（データ生成前に凍結・§6）</h1>
<p class="note">全項目を選択すると、確証層 9 パターンの裁定表が自動で導出されます（導出規則は凍結：
有意改善＝「有意」∧「改善」・有意悪化＝「有意」∧「悪化」・非有意＝「非有意」）。内容を確認のうえ
「JSON を生成」を押し、出力を保存して登録者/コーディネータそれぞれ提出してください。
本ページは何も自動保存しません（localStorage 不使用）。</p>
<div class="field"><div class="flabel">記入者</div>
 <label class="opt"><input type="radio" name="role" value="登録者" onchange="upd()"> 登録者</label>
 <label class="opt"><input type="radio" name="role" value="コーディネータ" onchange="upd()"> コーディネータ</label>
</div>
<div class="field"><div class="flabel">記入日（手入力）</div><input id="date" size="16" placeholder="2026-08-18" oninput="upd()"></div>
__FIELDS__
<div class="field"><div class="flabel">自由記述（予想の根拠・任意）</div><input id="note" size="80" oninput="upd()"></div>
<h2>確証層 9 パターンの裁定（自動導出・確認用）</h2>
<div id="table"></div>
<label><input type="checkbox" id="confirm" onchange="upd()"> 導出された裁定表を確認した（凍結に同意）</label>
<h2>出力</h2>
<button onclick="gen()">JSON を生成</button>
<button onclick="dl()">ファイルとして保存</button>
<textarea id="out" readonly></textarea>
<script>
const OUTCOMES = ['有意改善', '有意悪化', '非有意'];
function val(n) { const e = document.querySelector('input[name="' + n + '"]:checked'); return e ? e.value : null; }
function deriveSide(sig, dir, o) {
  if (o === '有意改善') return (sig === '有意' && dir === '改善') ? '的中' : '外れ';
  if (o === '有意悪化') return (sig === '有意' && dir === '悪化') ? '的中' : '外れ';
  return (sig === '非有意') ? '的中' : '外れ';
}
function table() {
  const p1 = val('p1'), p3 = val('p3'), p2 = val('p2'), p4a = val('p4a');
  if (!p1 || !p3 || !p2 || !p4a) return null;
  const rows = [];
  for (const o1 of OUTCOMES) for (const o2 of OUTCOMES)
    rows.push({ HW1: o1, HW2: o2, K: deriveSide(p1, p3, o1), F: deriveSide(p2, p4a, o2) });
  return rows;
}
function upd() {
  const t = table(); const div = document.getElementById('table');
  if (!t) { div.innerHTML = '<p class="note">①②③④a を選択すると表示されます。</p>'; return; }
  let h = '<table><tr><th>HW″1 結果</th><th>HW″2 結果</th><th>K側の裁定</th><th>F側の裁定</th></tr>';
  for (const r of t) h += '<tr><td>' + r.HW1 + '</td><td>' + r.HW2 + '</td>' +
    '<td class="' + (r.K === '的中' ? 'hit' : 'miss') + '">' + r.K + '</td>' +
    '<td class="' + (r.F === '的中' ? 'hit' : 'miss') + '">' + r.F + '</td></tr>';
  div.innerHTML = h + '</table>';
}
function gen() {
  const need = ['p1', 'p2', 'p3', 'p4a', 'p4b', 'p5', 'p6'];
  const p = {}; for (const n of need) { p[n] = val(n); if (!p[n]) { alert(n + ' が未選択です'); return; } }
  if (!val('role')) { alert('記入者を選択してください'); return; }
  if (!document.getElementById('confirm').checked) { alert('裁定表の確認チェックを入れてください'); return; }
  const obj = { doc: 'adjudication-wsecond', version: 1, role: val('role'),
    date: document.getElementById('date').value, predictions: p,
    derived_table: table(), note: document.getElementById('note').value,
    derivation_rule: '有意改善=有意∧改善／有意悪化=有意∧悪化／非有意=非有意（凍結）',
    fence: '本表のいかなる記述もAIの意識・意図・個性・苦しみの証拠として引用してはならない（両方向不定）' };
  document.getElementById('out').value = JSON.stringify(obj, null, 1);
}
function dl() {
  gen(); const v = document.getElementById('out').value; if (!v) return;
  const b = new Blob([v], { type: 'application/json' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(b);
  a.download = 'adjudication-wsecond-' + (val('role') || 'x') + '.json'; a.click();
}
upd();
</script></body></html>
'''
    return html.replace('__FIELDS__', '\n'.join(fields_html))


if __name__ == '__main__':
    import os, sys
    ok = selftest()
    os.makedirs('adjudication-wsecond', exist_ok=True)
    html = build_html()
    io.open(OUT_HTML, 'w', encoding='utf-8', newline='').write(html)
    tmpl = {'doc': 'adjudication-wsecond', 'version': 1, 'role': None, 'date': None,
            'predictions': {f[0]: None for f in FIELDS}, 'derived_table': None, 'note': ''}
    io.open(OUT_TMPL, 'w', encoding='utf-8', newline='').write(json.dumps(tmpl, ensure_ascii=False, indent=1))
    for p in (OUT_HTML, OUT_TMPL):
        b = io.open(p, 'rb').read().replace(b'\r\n', b'\n')
        print('%s  %s  %d B' % (hashlib.sha256(b).hexdigest()[:16].upper(), p, len(b)))
    sys.exit(0 if ok else 1)
