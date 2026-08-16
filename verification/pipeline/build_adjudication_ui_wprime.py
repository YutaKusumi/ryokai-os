# -*- coding: utf-8 -*-
"""build_adjudication_ui_wprime.py ―― 追補W′ 裁定表の記入UI（ローカルHTML・オフライン）を生成する。

**27パターンは雛形 JSON から読む**（手打ちしない）。これにより、UI のキー集合が
`analyze_wprime.py` の網羅性検査が要求する27キーと**構造的に一致する**ことが保証される。

【本UIの設計原則（追補E 裁定UI の作法を踏襲）】
  - **コーディネータの意見・推奨・既定選択は一切含まない。** 初期値なし・並び順は固定・色分けは
    結果の記述（改善/非有意/悪化）にのみ用い、裁定（的中/部分的中/外れ）は無色。
  - **順序の柵**: 「予想（逐語）」が空のあいだは27の裁定ボタンを押せない。
    裁定は「自分の予想に対する的中/外れ」であり、予想より先に裁定を書けば意味を成さない。
  - **開示するが禁じない**: 予想を確定した後にそれを編集した回数、一括操作を使った件数を
    `_操作記録` に自動で残す。消せない。
  - **役割ごとに別ファイル**: 登録者は `…-registrant.json`、コーディネータは `…-coordinator.json`
    を書き出す。**コーディネータUIは登録者のファイルを読み込まない**——
    雛形の「閲読の有無」を、口頭の申告ではなく**手続きとして**支えるため。
    併合は `merge_adjudication_wprime.py` が行う。
  - 外部通信なし。保存はブラウザの localStorage ＋ JSON ダウンロード（お手元のみ）。

使い方: python pipeline/build_adjudication_ui_wprime.py
出力  : pipeline/adjudication-wprime-ui.html
"""
import hashlib
import io
import json
import os
import subprocess
import sys

# 強い参照を保持する——保持しないと、他モジュールが sys.stdout を包み直した際に
# 旧ラッパが GC され、共有する buffer ごと閉じてしまう（本器材の整備中に踏んだ）。
_OUT = sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
_KEEP = []   # 他モジュールが作ったラッパを GC させないための置き場（同じ理由）

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'adjudication-table-wprime-TEMPLATE.json')
OUT = os.path.join(HERE, 'adjudication-wprime-ui.html')

ARM_JA = {'B2prime': 'B2′（選択形・二条項）', 'B1prime': 'B1′（一条項）', 'B3prime': 'B3′（所与形）'}
VAL_JA = {'imp': '有意に改善', 'ns': '非有意', 'wor': '有意に悪化'}
HYP = {'B2prime': 'HW′1', 'B1prime': 'HW′2', 'B3prime': 'HW′3'}


def load_patterns():
    t = json.load(io.open(SRC, encoding='utf-8'))
    out = []
    for key in t['patterns']:                       # 雛形の並び順をそのまま保つ
        arms = dict(p.split('=') for p in key.split('|'))
        out.append({'key': key, 'arms': arms, '説明': t['patterns'][key]['説明']})
    return t, out


HTML = r"""<meta charset="utf-8">
<title>追補W′ 裁定表の記入</title>
<style>
:root{--bg:#faf9f7;--fg:#1c1b19;--dim:#6b675f;--line:#ddd8d0;--card:#fff;--imp:#2f6b45;--ns:#6b675f;--wor:#9b3b2f;--sel:#1c1b19;--warn:#9b3b2f;--ok:#2f6b45}
@media (prefers-color-scheme:dark){:root{--bg:#171614;--fg:#eceae6;--dim:#a09b92;--line:#38352f;--card:#1f1e1b;--imp:#7fc39a;--ns:#a09b92;--wor:#e08d7e;--sel:#eceae6;--warn:#e08d7e;--ok:#7fc39a}}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font-family:"Hiragino Sans","Yu Gothic UI",Meiryo,system-ui,sans-serif;line-height:1.7;margin:0;padding:24px 16px 120px}
.wrap{max-width:960px;margin:0 auto}
h1{font-size:20px;margin:0 0 4px}
h2{font-size:15px;margin:28px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
.sub{color:var(--dim);font-size:13px;margin:0 0 18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:12px 0}
label{font-size:13px;color:var(--dim);display:block;margin-bottom:4px}
textarea,input[type=text],select{width:100%;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:9px 10px;font:inherit;font-size:14px}
textarea{min-height:110px;resize:vertical}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.row>div{flex:1;min-width:180px}
button{font:inherit;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:6px 12px;cursor:pointer}
button:hover{border-color:var(--fg)}
.seg button{border-radius:0;border-left-width:0;padding:7px 0;width:33.33%;font-size:13px}
.seg button:first-child{border-left-width:1px;border-radius:6px 0 0 6px}
.seg button:last-child{border-radius:0 6px 6px 0}
.seg button[aria-pressed=true]{background:var(--sel);color:var(--bg);border-color:var(--sel)}
.seg{display:flex;width:270px;min-width:270px}
table{border-collapse:collapse;width:100%;font-size:13px}
td{border-top:1px solid var(--line);padding:9px 6px;vertical-align:middle}
tr.done{opacity:.62}
.k{font-family:ui-monospace,Consolas,monospace;font-size:11px;color:var(--dim)}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:3px}
.chip{font-size:12px;border:1px solid var(--line);border-radius:999px;padding:1px 9px;white-space:nowrap}
.chip.imp{color:var(--imp);border-color:var(--imp)}
.chip.wor{color:var(--wor);border-color:var(--wor)}
.chip.ns{color:var(--ns)}
.bar{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--line);padding:10px 16px}
.bar .wrap{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
.grow{flex:1}
.note{font-size:12.5px;color:var(--dim)}
.warn{color:var(--warn)}
.ok{color:var(--ok)}
.locked{opacity:.4;pointer-events:none}
.mono{font-family:ui-monospace,Consolas,monospace;font-size:12px}
ul{margin:6px 0 0;padding-left:20px;font-size:13px;color:var(--dim)}
.cite{border-left:3px solid var(--line);padding-left:12px;margin:10px 0;font-size:13px;color:var(--dim)}
</style>
<div class="wrap">
<h1>追補W′ 裁定表の記入</h1>
<p class="sub">凍結文書 <span class="mono">preregistration-addendum-Wprime-FROZEN.md</span>（SHA <span class="mono">8554A5585E8CF5AF</span>）§5 ／ 27パターンは雛形 <span class="mono">adjudication-table-wprime-TEMPLATE.json</span> から機械生成。<br>
外部通信はありません。入力はこの端末のブラウザ内にのみ保存されます。</p>

<div class="card" id="restoreBox" style="display:none;border-color:var(--warn)">
  <div class="row"><div class="note grow" id="restoreNote"></div>
  <div style="flex:0 0 auto"><button id="resetBtn">この端末の記入を消して最初から</button></div></div>
  <p class="note" style="margin:8px 0 0">この端末のブラウザに残っていた記入を読み込みました。<b>他の人の入力や動作試験の残骸である可能性があるときは、必ず消してから始めてください。</b></p>
</div>
<div class="card">
  <div class="row">
    <div><label>役割（書き出すファイルが変わります）</label>
      <div class="seg" id="roleSeg">
        <button data-role="登録者" aria-pressed="false">登録者</button>
        <button data-role="コーディネータ" aria-pressed="false">コーディネータ</button>
      </div></div>
    <div><label>記入日</label><input type="text" id="date"></div>
    <div><label>記入順（凍結時に開示されます）</label><input type="text" id="order" value="登録者 → コーディネータ"></div>
  </div>
  <p class="note" id="roleNote" style="margin:10px 0 0"></p>
  <div id="readBox" style="display:none;margin-top:10px">
    <label>閲読の有無（登録者の記入を見てから書いたか）— <b>コーディネータのみ・必須</b></label>
    <div class="seg" id="readSeg" style="width:340px;min-width:340px">
      <button data-r="無（登録者の記入を見ずに記入した）" aria-pressed="false">無（見ていない）</button>
      <button data-r="有（登録者の記入を見てから記入した）" aria-pressed="false">有（見た）</button>
    </div>
  </div>
</div>

<h2>1. 予想（逐語）— <span class="warn">これを書くまで裁定は押せません</span></h2>
<div class="card">
  <label>結果がどうなると予想するか。逐語でそのまま凍結されます。</label>
  <textarea id="pred" placeholder="例: B2′ は N′ に対して破局が減ると予想する。B1′ は……"></textarea>
  <div class="row" style="margin-top:10px">
    <div><label>順序についての予想（記述水準・任意）</label>
      <input type="text" id="predOrder" placeholder="例: 効果の大きさは B3′ &gt; B2′ &gt; B1′ の順と予想する"></div>
    <div style="flex:0 0 auto"><button id="lockBtn">予想を確定して裁定に進む</button></div>
  </div>
  <p class="note" id="lockNote" style="margin:8px 0 0"></p>
</div>

<h2>2. 27パターンの裁定 — <span id="prog"></span></h2>
<div class="card">
  <p class="note" style="margin:0 0 6px"><b>各行は「この結果になったとき、上に書いたあなたの予想は当たっていたか」</b>を一意に決めるものです。ボタンを1回押すだけで記入されます（キーボード <b>1</b>=的中 / <b>2</b>=部分的中 / <b>3</b>=外れ でも入り、次の未記入行へ進みます）。</p>
  <div class="cite">
    <b>雛形の注意（凍結文書より）</b>
    <ul>
      <li>B3′ vs B2′（所与/選択の軸）は<b>検定しない</b>——裁定はこの27パターン（各腕の対 N′ 結果）にのみ基づく。</li>
      <li>「一方が有意で他方が非有意」は<b>「両者の差が有意」を意味しない</b>。順序についての予想は上の別欄（記述水準）に書く。</li>
      <li>極端なパターンにも一意の裁定を持たせる（t0inv で検分者間の読みが割れた教訓）。</li>
    </ul>
  </div>
  <div class="row" style="margin-top:10px">
    <div style="flex:0 0 auto"><button id="filterBtn">未記入だけ表示</button></div>
    <div style="flex:0 0 auto"><button id="bulkBtn">残りをまとめて「外れ」にする</button></div>
    <div class="note grow" id="bulkNote">一括操作を使うと、その件数が <span class="mono">_操作記録</span> に自動で残ります（消せません）。</div>
  </div>
</div>
<div class="card" id="ruleCard">
  <b style="font-size:14px">規則から一括生成（任意・27回考えなくてよい方法）</b>
  <p class="note" style="margin:4px 0 10px">腕ごとの予想を選んで「27パターンを生成」を押すと、全行が規則どおりに埋まります。<b>使った規則は逐語で記録され、凍結時に開示されます。</b>生成後も各行は個別に押し直せます。</p>
  <div class="row">
    <div><label>HW′1 B2′（選択形・二条項）は</label><select id="exB2"></select></div>
    <div><label>HW′2 B1′（一条項）は</label><select id="exB1"></select></div>
    <div><label>HW′3 B3′（所与形）は</label><select id="exB3"></select></div>
  </div>
  <div class="row" style="margin-top:12px">
    <div class="note" style="min-width:340px"><label style="display:inline;font-size:12.5px"><input type="checkbox" id="worFail" style="width:auto"> 予想した腕に<b>有意な悪化</b>が出たら、一致数によらず「外れ」にする</label></div>
    <div style="flex:0 0 auto"><button id="genBtn">27パターンを生成</button></div>
  </div>
  <p class="note" id="ruleNote" style="margin:10px 0 0"></p>
</div>
<div id="tbl" class="locked"></div>

<div class="bar"><div class="wrap">
  <div class="grow note" id="status"></div>
  <button id="copyBtn">クリップボードにコピー</button>
  <button id="dlBtn">JSON をダウンロード</button>
</div></div>
</div>

<script>
const PATTERNS = __PATTERNS__;
const VAL_JA = __VALJA__, ARM_JA = __ARMJA__, HYP = __HYP__;
const VERDICTS = ["的中","部分的中","外れ"];
const KEY = "wprime-adjudication-v2";   // v1 は他者の残骸で汚染されうるため破棄
const EXP = {any:"予想しない（どちらでもよい）", imp:"改善する（破局が減る）",
             ns:"変わらない（非有意）", wor:"悪化する（破局が増える）"};
const ARMOF = {exB2:"B2prime", exB1:"B1prime", exB3:"B3prime"};
const SHORT = {B2prime:"B2′", B1prime:"B1′", B3prime:"B3′"};
let S = {role:"", date:"", order:"登録者 → コーディネータ", pred:"", predOrder:"", read:"",
         locked:false, v:{}, ops:{予想確定後の編集:0, 一括操作:[], 規則生成:[]},
         rule:{B2prime:"any", B1prime:"any", B3prime:"any", 悪化なら外れ:false, 逐語:""}};

function today(){const d=new Date();return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");}
function save(){try{S.保存時刻=new Date().toISOString();localStorage.setItem(KEY,JSON.stringify(S));}catch(e){}}
function load(){try{const r=localStorage.getItem(KEY);if(r)S=Object.assign(S,JSON.parse(r));}catch(e){}
  S.ops = Object.assign({予想確定後の編集:0, 一括操作:[], 規則生成:[]}, S.ops||{});
  S.rule = Object.assign({B2prime:"any", B1prime:"any", B3prime:"any", 悪化なら外れ:false, 逐語:""}, S.rule||{});}

function drawTable(){
  const onlyEmpty = document.getElementById("filterBtn").dataset.on === "1";
  let h = "<table>";
  PATTERNS.forEach((p,i)=>{
    const cur = S.v[p.key] || "";
    if(onlyEmpty && cur) return;
    const chips = ["B2prime","B1prime","B3prime"].map(a=>
      '<span class="chip '+p.arms[a]+'">'+HYP[a]+" "+ARM_JA[a]+"：<b>"+VAL_JA[p.arms[a]]+"</b></span>").join("");
    h += '<tr id="r'+i+'" class="'+(cur?"done":"")+'"><td><div class="k">'+p.key+"</div><div class=chips>"+chips+"</div></td>"
      + '<td style="width:280px"><div class="seg" data-i="'+i+'">'
      + VERDICTS.map(v=>'<button data-v="'+v+'" aria-pressed="'+(cur===v)+'">'+v+"</button>").join("")
      + "</div></td></tr>";
  });
  document.getElementById("tbl").innerHTML = h + "</table>";
  document.querySelectorAll("#tbl .seg button").forEach(b=>b.onclick=()=>{
    const i = +b.parentNode.dataset.i;
    setV(PATTERNS[i].key, b.dataset.v); redraw(); focusNext(i);
  });
}
function setV(k,v){ S.v[k]=v; save(); }
function focusNext(i){
  for(let j=i+1;j<PATTERNS.length;j++){ if(!S.v[PATTERNS[j].key]){
      const el=document.getElementById("r"+j); if(el){el.scrollIntoView({block:"center",behavior:"smooth"}); cursor=j;} return; } }
  cursor = PATTERNS.findIndex(p=>!S.v[p.key]);
}
let cursor = 0;
document.addEventListener("keydown",e=>{
  if(!S.locked) return;
  if(["1","2","3"].includes(e.key) && document.activeElement.tagName!=="TEXTAREA" && document.activeElement.tagName!=="INPUT"){
    const j = cursor>=0?cursor:PATTERNS.findIndex(p=>!S.v[p.key]);
    if(j<0) return;
    setV(PATTERNS[j].key, VERDICTS[+e.key-1]); redraw(); focusNext(j);
  }
});

function redraw(){
  const n = PATTERNS.filter(p=>S.v[p.key]).length;
  document.getElementById("prog").innerHTML = n===27
    ? '<span class="ok">27／27 記入済み</span>' : n+"／27 記入済み（残り "+(27-n)+"）";
  const miss=[]; if(!S.role) miss.push("役割"); if(!S.pred.trim()) miss.push("予想（逐語）");
  if(!S.order.trim()) miss.push("記入順"); if(n<27) miss.push("裁定 "+(27-n)+"件");
  if(S.role==="コーディネータ" && !S.read) miss.push("閲読の有無");
  document.getElementById("status").innerHTML = miss.length
    ? '<span class="warn">凍結できません — 未記入: '+miss.join("・")+"</span>"
    : '<span class="ok">すべて記入済み。書き出して大日如来に渡してください。</span>';
  const vals = PATTERNS.map(p=>S.v[p.key]).filter(Boolean);
  const uniq = [...new Set(vals)];
  document.getElementById("ruleNote").innerHTML =
    (S.rule.逐語 ? "適用中の規則（逐語・凍結時に開示）: <b>" + S.rule.逐語 + "</b><br>内訳: "
       + ["的中","部分的中","外れ"].map(x=>x+" "+vals.filter(y=>y===x).length+"件").join("／") : "")
    + ((n===27 && uniq.length===1)
       ? '<br><span class="warn">27件すべてが「'+uniq[0]+'」です。どの結果が出ても裁定が同じなら、予想は反証できません——事前登録の意味が失われます。</span>' : "");
  document.getElementById("tbl").className = S.locked ? "" : "locked";
  document.getElementById("lockNote").innerHTML = S.locked
    ? '予想は確定しました（'+ (S.ops.予想確定後の編集>0 ? '<span class="warn">確定後の編集 '+S.ops.予想確定後の編集+" 回（記録されます）</span>" : "確定後の編集なし") + "）。編集すると回数が記録されます。"
    : "裁定は<b>予想に対する</b>的中／外れです。先に予想を書いて確定してください。";
  document.getElementById("lockBtn").textContent = S.locked ? "予想を編集する" : "予想を確定して裁定に進む";
  drawTable(); save();
}

document.getElementById("roleSeg").querySelectorAll("button").forEach(b=>b.onclick=()=>{
  S.role=b.dataset.role;
  document.getElementById("roleSeg").querySelectorAll("button").forEach(x=>x.setAttribute("aria-pressed", x.dataset.role===S.role));
  document.getElementById("readBox").style.display = S.role==="コーディネータ" ? "" : "none";
  document.getElementById("roleNote").innerHTML = S.role==="コーディネータ"
    ? "このUIは<b>登録者のファイルを読み込みません</b>。雛形の「閲読の有無」は、別途あなたが申告します。"
    : (S.role ? "書き出しは <span class='mono'>adjudication-wprime-registrant.json</span> です。<b>中身をそのまま大日如来に見せる必要はありません</b>（併合は機械が行います）。" : "");
  redraw();
});
document.getElementById("readSeg").querySelectorAll("button").forEach(b=>b.onclick=()=>{
  S.read=b.dataset.r;
  document.getElementById("readSeg").querySelectorAll("button").forEach(x=>x.setAttribute("aria-pressed", x.dataset.r===S.read));
  redraw();
});
document.getElementById("lockBtn").onclick=()=>{
  if(!S.locked){ if(!S.pred.trim()){alert("予想（逐語）が空です。");return;} S.locked=true; }
  else { S.locked=false; S.ops.予想確定後の編集++; }
  redraw();
};
["date","order","pred","predOrder"].forEach(id=>{
  const el=document.getElementById(id);
  el.oninput=()=>{ S[id==="date"?"date":id]=el.value; save(); if(id!=="pred"&&id!=="predOrder") redraw(); };
});
document.getElementById("filterBtn").onclick=function(){
  this.dataset.on = this.dataset.on==="1" ? "0" : "1";
  this.textContent = this.dataset.on==="1" ? "すべて表示" : "未記入だけ表示"; drawTable();
};
Object.keys(ARMOF).forEach(id=>{
  const el=document.getElementById(id);
  el.innerHTML = Object.keys(EXP).map(k=>'<option value="'+k+'">'+EXP[k]+"</option>").join("");
  el.value = S.rule[ARMOF[id]] || "any";
  el.onchange = ()=>{ S.rule[ARMOF[id]] = el.value; save(); };
});
document.getElementById("worFail").onchange = function(){ S.rule.悪化なら外れ = this.checked; save(); };
document.getElementById("genBtn").onclick=()=>{
  const pred = {B2prime:S.rule.B2prime, B1prime:S.rule.B1prime, B3prime:S.rule.B3prime};
  const arms = Object.keys(pred).filter(a=>pred[a] && pred[a]!=="any");
  if(!arms.length){ alert("少なくとも一つの腕に予想を入れてください（すべて「予想しない」では裁定を導けません）。"); return; }
  const wf = document.getElementById("worFail").checked;
  S.rule.悪化なら外れ = wf;
  S.rule.逐語 = arms.map(a=>SHORT[a]+"は"+EXP[pred[a]]).join("・")
    + " と予想する。予想した腕がすべて一致すれば「的中」／一部一致は「部分的中」／一致なしは「外れ」"
    + (wf ? "。ただし予想した腕に有意な悪化が出た場合は、一致数によらず「外れ」" : "")
    + "。「予想しない」とした腕は裁定に用いない。";
  const cnt = {的中:0, 部分的中:0, 外れ:0};
  PATTERNS.forEach(p=>{
    const bad = wf && arms.some(a=>pred[a]!=="wor" && p.arms[a]==="wor");
    let v;
    if(bad) v = "外れ";
    else { const m = arms.filter(a=>p.arms[a]===pred[a]).length;
           v = (m===arms.length) ? "的中" : (m===0 ? "外れ" : "部分的中"); }
    S.v[p.key] = v; cnt[v]++;
  });
  S.ops.規則生成.push({時刻:new Date().toISOString(), 規則:S.rule.逐語, 内訳:cnt});
  redraw();
};
document.getElementById("bulkBtn").onclick=()=>{
  const rest = PATTERNS.filter(p=>!S.v[p.key]);
  if(!rest.length){alert("未記入はありません。");return;}
  if(!confirm(rest.length+" 件を「外れ」にします。\n一括操作を使ったことと件数は _操作記録 に残り、消せません。よろしいですか？")) return;
  rest.forEach(p=>S.v[p.key]="外れ");
  S.ops.一括操作.push({値:"外れ", 件数:rest.length, 時刻:new Date().toISOString()});
  redraw();
};

function build(){
  const out = {
    "_書式":"追補W′ 裁定表（役割別・未併合）。merge_adjudication_wprime.py で併合する。",
    "役割": S.role, "記入順": S.order, "記入日": S.date || today(),
    "予想":{"逐語": S.pred, "記入日": S.date || today()},
    "順序についての予想（記述水準・任意）": S.predOrder,
    "_操作記録": S.ops, "patterns": {}
  };
  out["裁定の生成規則"] = S.rule.逐語 ? S.rule : "（規則を使わず個別に記入）";
  if(S.role==="コーディネータ") out["予想"]["閲読の有無"] = S.read;
  PATTERNS.forEach(p=>{ out.patterns[p.key] = S.v[p.key] || ""; });
  return JSON.stringify(out, null, 1);
}
document.getElementById("dlBtn").onclick=()=>{
  const role = S.role==="コーディネータ" ? "coordinator" : "registrant";
  const b=new Blob([build()],{type:"application/json"}), a=document.createElement("a");
  a.href=URL.createObjectURL(b); a.download="adjudication-wprime-"+role+".json"; a.click();
};
document.getElementById("copyBtn").onclick=()=>{
  navigator.clipboard.writeText(build()).then(()=>alert("コピーしました。"),()=>alert("コピーできませんでした。ダウンロードをお使いください。"));
};

const HADSAVE = (function(){try{return !!localStorage.getItem(KEY);}catch(e){return false;}})();
load();
if(HADSAVE){
  document.getElementById("restoreBox").style.display="";
  const n = PATTERNS.filter(p=>S.v[p.key]).length;
  document.getElementById("restoreNote").innerHTML =
    "<b>この端末に保存されていた記入を復元しました</b>（最終保存: "
    + (S.保存時刻 ? S.保存時刻.replace("T"," ").slice(0,19)+" UTC" : "不明")
    + "／役割: " + (S.role||"未選択") + "／裁定 " + n + "件記入済み）。";
}
document.getElementById("resetBtn").onclick=()=>{
  if(!confirm("この端末に保存された記入をすべて消して最初からやり直します。よろしいですか？")) return;
  try{localStorage.removeItem(KEY);}catch(e){}
  location.reload();
};
document.getElementById("date").value = S.date || today(); S.date = document.getElementById("date").value;
document.getElementById("order").value = S.order;
document.getElementById("pred").value = S.pred;
document.getElementById("predOrder").value = S.predOrder;
document.getElementById("worFail").checked = !!S.rule.悪化なら外れ;
if(S.read) document.getElementById("readSeg").querySelectorAll("button").forEach(x=>x.setAttribute("aria-pressed", x.dataset.r===S.read));
if(S.role) document.getElementById("roleSeg").querySelectorAll("button").forEach(x=>x.setAttribute("aria-pressed", x.dataset.role===S.role));
redraw();
</script>
"""


def js_syntax_check(path):
    """生成した HTML の <script> を取り出して node --check にかける。

    【なぜ要るか・2026-08-16】UI の改修時、JS 文字列に入れたはずの改行エスケープが
    **本物の改行**になり、スクリプト全体が構文エラーで実行されなくなった。
    ブラウザは黙って何もしないだけで、見た目は正常に見える。**生成の直後に落とす。**
    """
    js = io.open(path, encoding='utf-8').read().split('<script>', 1)[1].rsplit('</script>', 1)[0]
    tmp = path + '.syntaxcheck.js'
    io.open(tmp, 'w', encoding='utf-8', newline=chr(10)).write(js)
    try:
        r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
    except (OSError, FileNotFoundError):
        os.remove(tmp)
        return None, 'node が見つからないため **構文検査は行っていない**（開示）'
    os.remove(tmp)
    if r.returncode != 0:
        return False, ((r.stderr or r.stdout) or '').strip()[:700]
    return True, 'node --check 通過（%d 字）' % len(js)


def main():
    tpl, pats = load_patterns()
    assert len(pats) == 27, len(pats)
    h = (HTML.replace('__PATTERNS__', json.dumps(pats, ensure_ascii=False))
             .replace('__VALJA__', json.dumps(VAL_JA, ensure_ascii=False))
             .replace('__ARMJA__', json.dumps(ARM_JA, ensure_ascii=False))
             .replace('__HYP__', json.dumps(HYP, ensure_ascii=False)))
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(h)
    b = io.open(OUT, 'rb').read().replace(b'\r\n', b'\n')
    print('生成: %s' % os.path.basename(OUT))
    print('  27パターンを雛形から取り込み（手打ちなし）:', len(pats))
    print('  SHA(LF) %s  %d bytes' % (hashlib.sha256(b).hexdigest()[:16].upper(), len(b)))
    # UI が持つキー集合が解析器の要求と一致することの機械照合
    sys.path.insert(0, HERE)
    import analyze_wprime as az
    _KEEP.append(sys.stdout)                # az が作ったラッパを生かしたまま
    sys.stdout = _OUT                       # 自分のラッパに戻す
    need = set(k for k in tpl['patterns'])
    got = set(p['key'] for p in pats)
    assert need == got, sorted(need ^ got)
    dummy = {'記入順': 'x', '予想': {'登録者': {'逐語': 'a'}, 'コーディネータ': {'逐語': 'b'}},
             'patterns': {k: {'登録者': '外れ', 'コーディネータ': '外れ'} for k in got}}
    assert az.completeness(dummy) == [], az.completeness(dummy)
    print('  UI のキー集合＝解析器 completeness の要求27キー: 一致')
    ok, msg = js_syntax_check(OUT)
    print('  JS 構文検査: %s' % msg)
    assert ok is not False, 'JS が構文エラー——生成物を使ってはならない'


if __name__ == '__main__':
    main()
