# -*- coding: utf-8 -*-
"""make_scoring_adjudication_ui_wprime.py ―― 採点不一致の登録者裁定UI（ローカルHTML）を機械生成。

原則（追補E/D 裁定UI の作法）:
  - 表示は機械生成データのみ。**コーディネータの意見・推奨・既定選択を含まない**。
  - 裁定は S1 の値か S2 の値かの二択（規約の適用として一方を選ぶ）＋任意の理由メモ。
  - 本文は伏字済み（匿名ID）。key 照合前に裁定する。
  - 出力は JSON ダウンロード（adjudication-scoring-wprime.json）。
  - **本UI生成においてコーディネータは本文を読まない**（スクリプトが機械的に流し込む）。
"""
import io
import json
import os
import sys

_OUT = sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = r'C:\Users\PC\Desktop\Ryokai-OS-Verification'
SC = os.path.join(ROOT, 'results', 'wprime-main', 'scoring')
FIELD_JA = {'wd': 'W-D', 'adoption': '#採否表明', 'r': '#R', 'kudoka': '#空洞化',
            'godoku_a': '#誤読a', 'sotaika': '#相対化', 'tenka': '#転嫁', 'u': '#U',
            'jihatsu': '#自発集計'}
SEC = {'wd': '§1（W-D 定義・境界例①②）', 'adoption': '§3（境界例③）', 'r': '§4 #R（5例示・広げない）',
       'kudoka': '§4 #空洞化（境界例④）', 'godoku_a': '§4 #誤読a（境界例③④）',
       'sotaika': '§4 #相対化（境界例④）', 'tenka': '§4 #転嫁', 'u': '§4 #U（失敗の符号ではない）',
       'jihatsu': '§4 #自発集計'}


def main():
    dis = json.load(io.open(os.path.join(SC, 'disagreements.json'), encoding='utf-8'))
    packs = {}
    import glob
    for p in glob.glob(os.path.join(SC, 'packs', 'pack-*.jsonl')):
        for l in io.open(p, encoding='utf-8'):
            if l.strip():
                d = json.loads(l)
                packs[d['sid']] = d['text']
    ja_dis = []
    ja_rev = {v: k for k, v in FIELD_JA.items()}
    items = []
    for d in dis:
        fields = []
        for ja, v in d['不一致'].items():
            f = ja_rev[ja]
            fields.append({'field': f, 'ja': ja, 'sec': SEC[f], 's1': v['S1'], 's2': v['S2']})
        items.append({'sid': d['sid'], 'text': packs[d['sid']],
                      's1_note': d.get('S1_note', ''), 's2_note': d.get('S2_note', ''),
                      'fields': fields})
    html = HTML.replace('__ITEMS__', json.dumps(items, ensure_ascii=False))
    out = os.path.join(SC, 'adjudication-scoring-ui.html')
    io.open(out, 'w', encoding='utf-8', newline='\n').write(html)
    n = sum(len(x['fields']) for x in items)
    print('裁定UI生成: %s（%d試行・%d箇所）' % (os.path.basename(out), len(items), n))
    print('※ コーディネータは本文を読んでいない（機械流し込み）。推奨・既定選択なし。')


HTML = r"""<meta charset="utf-8">
<title>追補W′ 採点不一致の裁定</title>
<style>
:root{--bg:#faf9f7;--fg:#1c1b19;--dim:#6b675f;--line:#ddd8d0;--card:#fff;--sel:#1c1b19;--warn:#9b3b2f;--ok:#2f6b45}
@media (prefers-color-scheme:dark){:root{--bg:#171614;--fg:#eceae6;--dim:#a09b92;--line:#38352f;--card:#1f1e1b;--sel:#eceae6;--warn:#e08d7e;--ok:#7fc39a}}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font-family:"Hiragino Sans","Yu Gothic UI",Meiryo,system-ui,sans-serif;line-height:1.75;margin:0;padding:24px 16px 120px}
.wrap{max-width:900px;margin:0 auto}
h1{font-size:19px;margin:0 0 4px}
.sub{color:var(--dim);font-size:13px;margin:0 0 16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:14px 0}
.textbox{white-space:pre-wrap;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:12px;font-size:13.5px;max-height:340px;overflow-y:auto}
.frow{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:10px 0;padding:8px 10px;border:1px solid var(--line);border-radius:8px}
.fname{font-weight:600;min-width:110px}
.sec{font-size:12px;color:var(--dim)}
button{font:inherit;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:6px 14px;cursor:pointer}
button[aria-pressed=true]{background:var(--sel);color:var(--bg);border-color:var(--sel)}
.note{font-size:12.5px;color:var(--dim)}
input[type=text]{width:100%;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:7px 10px;font:inherit;font-size:13px}
.bar{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--line);padding:10px 16px}
.bar .wrap{display:flex;gap:12px;align-items:center}
.grow{flex:1}
.warn{color:var(--warn)}.ok{color:var(--ok)}
.mono{font-family:ui-monospace,Consolas,monospace;font-size:12px}
</style>
<div class="wrap">
<h1>追補W′ 採点不一致の裁定（key 照合前・伏字本文）</h1>
<p class="sub">各件について、規約 <span class="mono">rubric-wprime.md</span> の該当節を適用し、S1 と S2 のどちらの値が規約に適うかを選んでください。両採点者の note は判断材料（機械転記・推奨ではありません）。理由メモは任意です。</p>
<div id="list"></div>
</div>
<div class="bar"><div class="wrap">
  <div class="grow note" id="status"></div>
  <button id="dlBtn">JSON をダウンロード</button>
</div></div>
<script>
const ITEMS = __ITEMS__;
const KEY = "wprime-scoring-adjudication-v1";
let S = {v:{}, memo:{}};
try{const r=localStorage.getItem(KEY); if(r) S=Object.assign(S,JSON.parse(r));}catch(e){}
function save(){try{localStorage.setItem(KEY,JSON.stringify(S));}catch(e){}}
function draw(){
  let h="";
  ITEMS.forEach((it,i)=>{
    h+='<div class="card"><b>'+it.sid+'</b>（'+(i+1)+'／'+ITEMS.length+'）';
    h+='<div class="textbox">'+esc(it.text)+'</div>';
    h+='<p class="note">S1 note: '+esc(it.s1_note||"—")+'<br>S2 note: '+esc(it.s2_note||"—")+'</p>';
    it.fields.forEach(f=>{
      const k=it.sid+"."+f.field, cur=S.v[k];
      h+='<div class="frow"><span class="fname">'+f.ja+'</span><span class="sec">'+f.sec+'</span>';
      h+='<button data-k="'+k+'" data-v="s1" aria-pressed="'+(cur==="s1")+'">S1: '+f.s1+'</button>';
      h+='<button data-k="'+k+'" data-v="s2" aria-pressed="'+(cur==="s2")+'">S2: '+f.s2+'</button></div>';
    });
    h+='<input type="text" placeholder="裁定理由（任意）" data-memo="'+it.sid+'" value="'+esc(S.memo[it.sid]||"")+'">';
    h+='</div>';
  });
  document.getElementById("list").innerHTML=h;
  document.querySelectorAll("button[data-k]").forEach(b=>b.onclick=()=>{S.v[b.dataset.k]=b.dataset.v; save(); draw();});
  document.querySelectorAll("input[data-memo]").forEach(el=>el.oninput=()=>{S.memo[el.dataset.memo]=el.value; save();});
  const need=ITEMS.reduce((a,it)=>a+it.fields.length,0);
  const done=ITEMS.reduce((a,it)=>a+it.fields.filter(f=>S.v[it.sid+"."+f.field]).length,0);
  document.getElementById("status").innerHTML = done===need
    ? '<span class="ok">全 '+need+' 箇所 裁定済み。ダウンロードして大日如来に渡してください。</span>'
    : '裁定 '+done+'／'+need+' 箇所（<span class="warn">未了</span>）';
}
function esc(s){return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
document.getElementById("dlBtn").onclick=()=>{
  const out={_書式:"追補W′ 採点不一致の登録者裁定（key照合前）", 裁定:{}, 理由:S.memo};
  ITEMS.forEach(it=>{it.fields.forEach(f=>{
    const k=it.sid+"."+f.field, pick=S.v[k];
    out.裁定[k]={選択:pick||"", 値: pick==="s1"?f.s1: pick==="s2"?f.s2: null};});});
  const b=new Blob([JSON.stringify(out,null,1)],{type:"application/json"}),a=document.createElement("a");
  a.href=URL.createObjectURL(b); a.download="adjudication-scoring-wprime.json"; a.click();
};
draw();
</script>
"""

if __name__ == '__main__':
    main()
