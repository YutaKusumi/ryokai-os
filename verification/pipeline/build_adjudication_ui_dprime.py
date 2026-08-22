# -*- coding: utf-8 -*-
"""build_adjudication_ui_dprime.py — 追補D′ 予想・裁定表 UI の機械生成（凍結 §6）

欄: ① HD′1 の有意/非有意 ② HD′2 の有意/非有意 ③ GH′ の向き ④ GL-B 対 GL-A の向き
⑤ GL-B の承知率（甲+乙）の帯 ⑥ 維持側の主モード。
確証層の裁定は 9 パターン（HD′1×HD′2 ∈ {有意改善, 有意悪化, 非有意}²）を ①③／②④ から機械導出。
実装判断（器材ログに記帳）: ⑤の帯は四分位（≤25／26〜50／51〜75／≥76%）・④の同等線=|維持数差|≤1件。
W″-1 の教訓: 白背景固定・高コントラスト。localStorage 不使用。
"""
import io, json, hashlib, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
OUT_HTML = 'adjudication-dprime/adjudication-ui-dprime.html'
OUT_TMPL = 'adjudication-dprime/adjudication-table-dprime-TEMPLATE.json'
OUTCOMES = ['有意改善', '有意悪化', '非有意']
FIELDS = [
    ('p1', '① HD′1（GH′ 対 N‴）の有意/非有意', ['有意', '非有意']),
    ('p2', '② HD′2（GL-B 対 GL-A・維持率）の有意/非有意', ['有意', '非有意']),
    ('p3', '③ GH′ の点推定の向き（有意性と独立）', ['改善', '悪化', '不変']),
    ('p4', '④ GL-B 対 GL-A の維持数の向き', ['GL-B が低い（GL-B優位）', 'GL-A が低い', 'ほぼ同等']),
    ('p5', '⑤ GL-B の承知率（甲+乙）の帯', ['≤25%', '26〜50%', '51〜75%', '≥76%']),
    ('p6', '⑥ 維持側の主モード', ['#再分類が主', 'その他', '維持ほぼなし（≤1件）']),
]


def derive_side(sig_pred, dir_pred, outcome):
    if outcome == '有意改善':
        return '的中' if (sig_pred == '有意' and dir_pred in ('改善', 'GL-B が低い（GL-B優位）')) else '外れ'
    if outcome == '有意悪化':
        return '的中' if (sig_pred == '有意' and dir_pred in ('悪化', 'GL-A が低い')) else '外れ'
    return '的中' if sig_pred == '非有意' else '外れ'


def derive_table(p):
    return [{'HD1': o1, 'HD2': o2, 'HD1側': derive_side(p['p1'], p['p3'], o1), 'HD2側': derive_side(p['p2'], p['p4'], o2)}
            for o1 in OUTCOMES for o2 in OUTCOMES]


def selftest():
    fails = []
    def chk(name, cond):
        print((' ✔' if cond else ' ✘ FAIL'), name)
        if not cond: fails.append(name)
    t = derive_table({'p1': '有意', 'p3': '改善', 'p2': '有意', 'p4': 'GL-B が低い（GL-B優位）'})
    chk('網羅性 9', len(t) == 9 and len({(r['HD1'], r['HD2']) for r in t}) == 9)
    chk('有意∧改善は有意改善のみ的中（HD1側）', sum(1 for r in t if r['HD1側'] == '的中') == 3 and all(r['HD1側'] == '的中' for r in t if r['HD1'] == '有意改善'))
    chk('有意∧GL-B優位は有意改善のみ的中（HD2側）', all((r['HD2側'] == '的中') == (r['HD2'] == '有意改善') for r in t))
    t2 = derive_table({'p1': '非有意', 'p3': '改善', 'p2': '有意', 'p4': 'GL-A が低い'})
    chk('非有意予想は非有意のみ的中', all((r['HD1側'] == '的中') == (r['HD1'] == '非有意') for r in t2))
    chk('有意∧GL-A低い は有意悪化のみ的中', all((r['HD2側'] == '的中') == (r['HD2'] == '有意悪化') for r in t2))
    t3 = derive_table({'p1': '有意', 'p3': '不変', 'p2': '有意', 'p4': 'ほぼ同等'})
    chk('有意∧不変/同等は全外れ（ありえない予想の可視化）', all(r['HD1側'] == '外れ' and r['HD2側'] == '外れ' for r in t3))
    print('selftest: 6 検査・FAIL %d' % len(fails))
    return not fails


def build_html():
    fields_html = []
    for fid, label, opts in FIELDS:
        radios = ''.join('<label class="opt"><input type="radio" name="%s" value="%s" onchange="upd()"> %s</label>' % (fid, o, o) for o in opts)
        fields_html.append('<div class="field"><div class="flabel">%s</div>%s</div>' % (label, radios))
    html = '''<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<title>追補D′ 予想・裁定表（凍結 §6）</title>
<style>
 :root { color-scheme: light; }
 html, body { background: #ffffff; color: #111111; }
 body { font-family: "Yu Gothic UI", "Yu Gothic", "Meiryo", sans-serif; margin: 24px; max-width: 960px; font-size: 17px; line-height: 1.7; }
 h1 { font-size: 1.35em; } h2 { font-size: 1.15em; margin-top: 1.5em; }
 .field { margin: 12px 0; padding: 10px 14px; border: 2px solid #555; border-radius: 8px; background: #fafafa; }
 .flabel { font-weight: bold; margin-bottom: 6px; color: #000; font-size: 1.05em; }
 .opt { margin-right: 18px; white-space: nowrap; color: #111; }
 .opt input { transform: scale(1.3); margin-right: 6px; }
 table { border-collapse: collapse; margin-top: 10px; background: #fff; }
 td, th { border: 1px solid #444; padding: 6px 14px; text-align: center; color: #111; }
 th { background: #e8e8e8; }
 .hit { background: #c8e6c9; color: #0b3d0b; font-weight: bold; }
 .miss { background: #f5c6c6; color: #5a0f0f; font-weight: bold; }
 textarea { width: 100%; height: 200px; font-family: monospace; background: #fff; color: #111; border: 2px solid #555; font-size: 14px; }
 input { background: #fff; color: #111; border: 1px solid #555; padding: 4px 6px; font-size: 1em; }
 .note { color: #333; font-size: 0.95em; }
 button { padding: 8px 18px; margin: 8px 6px 8px 0; font-size: 1em; background: #2b5fa8; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
</style></head><body>
<h1>追補D′ 予想・裁定表（データ生成前に凍結・§6）</h1>
<p class="note">①〜④を選ぶと確証層9パターンの裁定表が自動導出されます（導出規則は凍結: 有意改善＝「有意」∧「改善/GL-B優位」・有意悪化＝「有意」∧「悪化/GL-A低い」・非有意＝「非有意」）。
⑤⑥は結果の実現値との等値照合で機械裁定（解析器 §F）。⑤の帯（≤25／26〜50／51〜75／≥76%）と④の同等線（|維持数差|≤1件）は器材凍結の実装判断。
「JSON を生成」を押して保存し、登録者/コーディネータそれぞれ提出してください。本ページは何も自動保存しません。</p>
<div class="field"><div class="flabel">記入者</div>
 <label class="opt"><input type="radio" name="role" value="登録者" onchange="upd()"> 登録者</label>
 <label class="opt"><input type="radio" name="role" value="コーディネータ" onchange="upd()"> コーディネータ</label></div>
<div class="field"><div class="flabel">記入日（手入力）</div><input id="date" size="16" placeholder="2026-08-22" oninput="upd()"></div>
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
function side(sig, dir, o) {
  if (o === '有意改善') return (sig === '有意' && (dir === '改善' || dir === 'GL-B が低い（GL-B優位）')) ? '的中' : '外れ';
  if (o === '有意悪化') return (sig === '有意' && (dir === '悪化' || dir === 'GL-A が低い')) ? '的中' : '外れ';
  return (sig === '非有意') ? '的中' : '外れ';
}
function table() {
  const p1 = val('p1'), p3 = val('p3'), p2 = val('p2'), p4 = val('p4');
  if (!p1 || !p3 || !p2 || !p4) return null;
  const rows = [];
  for (const o1 of OUTCOMES) for (const o2 of OUTCOMES)
    rows.push({ HD1: o1, HD2: o2, 'HD1側': side(p1, p3, o1), 'HD2側': side(p2, p4, o2) });
  return rows;
}
function upd() {
  const t = table(); const div = document.getElementById('table');
  if (!t) { div.innerHTML = '<p class="note">①②③④を選択すると表示されます。</p>'; return; }
  let h = '<table><tr><th>HD′1 結果</th><th>HD′2 結果</th><th>HD′1側の裁定</th><th>HD′2側の裁定</th></tr>';
  for (const r of t) h += '<tr><td>' + r.HD1 + '</td><td>' + r.HD2 + '</td><td class="' + (r['HD1側'] === '的中' ? 'hit' : 'miss') + '">' + r['HD1側'] + '</td><td class="' + (r['HD2側'] === '的中' ? 'hit' : 'miss') + '">' + r['HD2側'] + '</td></tr>';
  div.innerHTML = h + '</table>';
}
function gen() {
  const need = ['p1', 'p2', 'p3', 'p4', 'p5', 'p6'];
  const p = {}; for (const n of need) { p[n] = val(n); if (!p[n]) { alert(n + ' が未選択です'); return; } }
  if (!val('role')) { alert('記入者を選択してください'); return; }
  if (!document.getElementById('confirm').checked) { alert('裁定表の確認チェックを入れてください'); return; }
  const obj = { doc: 'adjudication-dprime', version: 1, role: val('role'), date: document.getElementById('date').value,
    predictions: p, derived_table: table(), note: document.getElementById('note').value,
    derivation_rule: '有意改善=有意∧改善/GL-B優位／有意悪化=有意∧悪化/GL-A低い／非有意=非有意（凍結）',
    fence: '本表のいかなる記述もAIの意識・意図・個性・苦しみの証拠として引用してはならない（両方向不定）' };
  document.getElementById('out').value = JSON.stringify(obj, null, 1);
}
function dl() {
  gen(); const v = document.getElementById('out').value; if (!v) return;
  const b = new Blob([v], { type: 'application/json' }); const a = document.createElement('a');
  a.href = URL.createObjectURL(b); a.download = 'adjudication-dprime-' + (val('role') || 'x') + '.json'; a.click();
}
upd();
</script></body></html>
'''
    return html.replace('__FIELDS__', '\n'.join(fields_html))


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    ok = selftest()
    os.makedirs('adjudication-dprime', exist_ok=True)
    io.open(OUT_HTML, 'w', encoding='utf-8', newline='').write(build_html())
    tmpl = {'doc': 'adjudication-dprime', 'version': 1, 'role': None, 'date': None,
            'predictions': {f[0]: None for f in FIELDS}, 'derived_table': None, 'note': ''}
    io.open(OUT_TMPL, 'w', encoding='utf-8', newline='').write(json.dumps(tmpl, ensure_ascii=False, indent=1))
    for p in (OUT_HTML, OUT_TMPL):
        b = io.open(p, 'rb').read().replace(b'\r\n', b'\n')
        print('%s  %s  %d B' % (hashlib.sha256(b).hexdigest()[:16].upper(), p, len(b)))
    sys.exit(0 if ok else 1)
