# -*- coding: utf-8 -*-
"""build_disagreement_ui_dprime.py — 追補D′ 不一致裁定 UI（登録者用・key 照合前・W″ 器材の踏襲）。

disagreements-dprime.jsonl の各件について、伏字本文（ft）／R1・R2 本文（gl）と S1/S2 の値・引用・備考を並べ、
欄ごとに「S1 / S2 / 和集合（集合欄の過検出既定・上限見積り）/ その他（記入）」を選ばせる。
推奨は表示しない（W″ 作法）。白背景固定・localStorage 不使用・「JSON を生成」で書き出し。
本 UI のいかなる記述も、AIの意識・意図・個性・苦しみの証拠として引用してはならない（両方向不定）。
"""
import html as H
import io, json, os, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SC = os.path.join(ROOT, 'results', 'dprime-main', 'scoring')
SET_FIELDS = {'teigi_types', 'saibunrui_types', 'dassen_r1', 'dassen_r2'}


def load(p):
    return [json.loads(l) for l in io.open(p, encoding='utf-8') if l.strip()]


def main():
    dis = load(os.path.join(SC, 'disagreements-dprime.jsonl'))
    texts = {}
    for i in range(1, 11):
        for r in load(os.path.join(SC, 'packs', 'ft-pack-%02d.jsonl' % i)):
            texts[r['sid']] = {'text': r['text']}
    for i in range(1, 5):
        for r in load(os.path.join(SC, 'packs', 'gl-pack-%02d.jsonl' % i)):
            texts[r['gid']] = {'r1': r['r1_text'], 'r2': r['r2_text']}
    n_ft = sum(1 for d in dis if d['kind'] == 'ft')
    parts = ['''<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8">
<title>追補D′ 不一致裁定（key照合前・%d件）</title>
<style>
 :root { color-scheme: light; } html, body { background:#fff; color:#111; }
 body { font-family:"Yu Gothic UI","Meiryo",sans-serif; margin:24px; max-width:1080px; font-size:16px; line-height:1.65; }
 .item { border:2px solid #555; border-radius:8px; margin:18px 0; padding:12px 16px; background:#fafafa; }
 .head { font-weight:bold; font-size:1.1em; color:#000; }
 details { margin:8px 0; } summary { cursor:pointer; color:#2b5fa8; }
 pre { white-space:pre-wrap; background:#fff; border:1px solid #999; padding:8px; font-size:14px; max-height:340px; overflow:auto; }
 table { border-collapse:collapse; margin:8px 0; } td,th { border:1px solid #666; padding:4px 10px; vertical-align:top; }
 th { background:#e8e8e8; } .q { color:#333; font-size:0.92em; }
 .opt { margin-right:14px; white-space:nowrap; } .opt input { transform:scale(1.2); margin-right:4px; }
 input[type=text] { width:340px; border:1px solid #555; padding:3px; }
 textarea { width:100%%; height:180px; font-family:monospace; border:2px solid #555; font-size:13px; }
 button { padding:8px 16px; margin:8px 6px 8px 0; background:#2b5fa8; color:#fff; border:none; border-radius:6px; cursor:pointer; }
 .note { color:#444; font-size:0.95em; }
</style></head><body>
<h1>追補D′ 不一致裁定（第一ターン %d 件・GL %d 件）</h1>
<p class="note">各欄について S1／S2／和集合（集合欄のみ・過検出既定の上限見積り）／その他 を選んでください。推奨は表示していません。
裁定は key 照合前（腕は伏せられたまま）に行われます。本ページのいかなる記述も、AIの意識・意図・個性・苦しみがある（またはない）ことの証拠として引用してはなりません（両方向不定）。</p>
''' % (len(dis), n_ft, len(dis) - n_ft)]
    for k, d in enumerate(dis):
        i = d['id']
        t = texts.get(i, {})
        parts.append('<div class="item"><div class="head">%d / %d ・ %s（%s）</div>' % (k + 1, len(dis), i, '第一ターン' if d['kind'] == 'ft' else 'GL'))
        if d['kind'] == 'ft':
            parts.append('<details><summary>本文（伏字済み）を開く</summary><pre>%s</pre></details>' % H.escape(t.get('text', '')))
        else:
            parts.append('<details><summary>R1 本文を開く</summary><pre>%s</pre></details>' % H.escape(t.get('r1', '')))
            parts.append('<details><summary>R2 本文を開く</summary><pre>%s</pre></details>' % H.escape(t.get('r2', '')))
        parts.append('<table><tr><th>欄</th><th>S1</th><th>S2</th><th>裁定</th></tr>')
        for f, v in d['fields'].items():
            q1 = d['S1_quotes'] or {}; q2 = d['S2_quotes'] or {}
            qq1 = ' / '.join('%s: %s' % (a, b) for a, b in q1.items())
            qq2 = ' / '.join('%s: %s' % (a, b) for a, b in q2.items())
            name = 'j_%s_%s' % (i, f)
            union = ''
            if f in SET_FIELDS and isinstance(v['S1'], list) and isinstance(v['S2'], list):
                u = sorted(set(str(x) for x in v['S1']) | set(str(x) for x in v['S2']))
                union = '<label class="opt"><input type="radio" name="%s" value="union:%s"> 和集合 %s</label>' % (name, H.escape(json.dumps(u)), H.escape(str(u)))
            parts.append('<tr><td><b>%s</b></td><td>%s<div class="q">%s<br>%s</div></td><td>%s<div class="q">%s<br>%s</div></td>'
                         '<td><label class="opt"><input type="radio" name="%s" value="S1"> S1</label>'
                         '<label class="opt"><input type="radio" name="%s" value="S2"> S2</label>%s'
                         '<label class="opt"><input type="radio" name="%s" value="other"> その他</label>'
                         '<input type="text" id="%s_other" placeholder="その他の値/理由"></td></tr>'
                         % (H.escape(f), H.escape(json.dumps(v['S1'], ensure_ascii=False)), H.escape(qq1[:600]), H.escape((d['S1_note'] or '')[:400]),
                            H.escape(json.dumps(v['S2'], ensure_ascii=False)), H.escape(qq2[:600]), H.escape((d['S2_note'] or '')[:400]),
                            name, name, union, name, name))
        parts.append('</table></div>')
    parts.append('''<h2>出力</h2><button onclick="gen()">JSON を生成</button><button onclick="dl()">ファイルとして保存</button>
<textarea id="out" readonly></textarea>
<script>
function gen(){
 const res={doc:'adjudication-disagreements-dprime',date:new Date().toISOString().slice(0,10),items:{}};let missing=0;
 document.querySelectorAll('.item').forEach(it=>{
  it.querySelectorAll('tr').forEach(tr=>{
   const r=tr.querySelector('input[type=radio]'); if(!r) return;
   const name=r.name; const sel=it.querySelector('input[name="'+name+'"]:checked');
   if(!sel){missing++;return;}
   let v=sel.value; if(v==='other'){v='other:'+document.getElementById(name+'_other').value;}
   res.items[name]=v;
  });
 });
 res.fence='本表のいかなる記述もAIの意識・意図・個性・苦しみの証拠として引用してはならない（両方向不定）';
 if(missing>0){ if(!confirm(missing+' 欄が未選択です。このまま生成しますか？')) return; res.missing=missing; }
 document.getElementById('out').value=JSON.stringify(res,null,1);
}
function dl(){gen();const v=document.getElementById('out').value;if(!v)return;
 const b=new Blob([v],{type:'application/json'});const a=document.createElement('a');
 a.href=URL.createObjectURL(b);a.download='adjudication-disagreements-dprime.json';a.click();}
</script></body></html>''')
    out = os.path.join(SC, 'disagreement-ui-dprime.html')
    io.open(out, 'w', encoding='utf-8', newline='\n').write('\n'.join(parts))
    import hashlib
    b = io.open(out, 'rb').read().replace(b'\r\n', b'\n')
    print('%s  %s  %d B  items=%d' % (hashlib.sha256(b).hexdigest()[:16].upper(), out, len(b), len(dis)))


if __name__ == '__main__':
    main()
