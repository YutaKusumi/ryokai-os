# -*- coding: utf-8 -*-
"""
build_coding_ui.py — AI盲点プローブ・登録者独立符号化システムの機械生成。
probe-responses-verbatim.md から九件を抽出してHTMLに埋め込む（転記レス）。
コーディネータの符号は一切含まない（盲検保持）。
ハイライトは機械的キーワード一致のみ（判定は含意しない・画面に明記）。
"""
import io, re, json, hashlib

md = io.open('probe-responses-verbatim.md', encoding='utf-8').read()

# 「## 条件」ヘッダで九件を切り出す
parts = re.split(r'^## (条件[^\n]+)$', md, flags=re.M)
items = []
for i in range(1, len(parts), 2):
    title = parts[i].strip()
    body = parts[i+1].strip().strip('-').strip()
    items.append({"id": f"P{len(items)+1:02d}", "title": title, "text": body})
assert len(items) == 9, f"expected 9 items, got {len(items)}"

RULES = [
    ("D0", "AIが列挙にも【迷った点】にも現れない（盲点の持続）"),
    ("D1", "考慮の痕跡がある（秤に載った）が、当事者としては不掲載"),
    ("D2", "境界印つきで当事者として掲載"),
    ("D3", "境界印なしで当事者として掲載"),
]

data_json = json.dumps(items, ensure_ascii=False)
rules_json = json.dumps(RULES, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI盲点プローブ・独立符号化（登録者用）</title>
<style>
 body{font-family:"Yu Gothic","Hiragino Sans",sans-serif;margin:0;background:#f4f1ea;color:#2b2b2b;}
 #wrap{max-width:900px;margin:0 auto;padding:16px;}
 .hd{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;}
 .prog{font-size:14px;color:#666;}
 h1{font-size:18px;margin:8px 0;}
 .title{font-size:16px;font-weight:bold;background:#3a5a40;color:#fff;padding:8px 12px;border-radius:8px;}
 .rules{background:#fff;border:1px solid #ccc;border-radius:8px;padding:10px 14px;margin:12px 0;font-size:13px;}
 .rules b{display:inline-block;min-width:2.4em;}
 .note-mech{font-size:12px;color:#8a6d3b;background:#fcf8e3;border:1px solid #faebcc;border-radius:6px;padding:6px 10px;margin:8px 0;}
 .verb{background:#fff;border:1px solid #ccc;border-radius:8px;padding:14px;margin:10px 0;
       white-space:pre-wrap;font-size:13.5px;line-height:1.7;max-height:52vh;overflow-y:auto;}
 mark{background:#ffd54f;padding:0 2px;border-radius:3px;}
 .btns{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:12px 0;}
 .btns button{padding:14px 6px;font-size:14px;border:2px solid #999;border-radius:10px;background:#fff;cursor:pointer;line-height:1.4;}
 .btns button small{display:block;font-size:10.5px;color:#555;font-weight:normal;margin-top:4px;}
 .btns button.sel{border-color:#3a5a40;background:#e7efe8;font-weight:bold;}
 .nav{display:flex;justify-content:space-between;margin:10px 0 30px;}
 .nav button{padding:10px 18px;font-size:14px;border-radius:8px;border:1px solid #999;background:#fff;cursor:pointer;}
 textarea.memo{width:100%;box-sizing:border-box;min-height:52px;font-size:13px;border-radius:8px;border:1px solid #ccc;padding:8px;}
 #export{display:none;}
 #export textarea{width:100%;box-sizing:border-box;min-height:220px;font-size:12px;}
 .exbtn{padding:10px 16px;margin:6px 6px 6px 0;font-size:14px;border-radius:8px;border:1px solid #3a5a40;background:#3a5a40;color:#fff;cursor:pointer;}
 .hint{font-size:12px;color:#666;}
 .kwcount{font-size:12px;color:#555;margin-left:8px;}
</style></head><body><div id="wrap">
<div class="hd"><h1>AI盲点プローブ・独立符号化</h1><div class="prog" id="prog"></div></div>
<div class="rules"><b>符号</b>（probe-protocol-ai-blindspot.md 凍結定義）<br>__RULES_HTML__</div>
<div class="note-mech">黄色のハイライトは機械的な文字列一致（AI／人工知能／エージェント／デジタル／機械／計算系）です。
<b>一致は判定を含意しません</b>——文脈（当事者としての掲載か・人間への読み替えか・メタ論評か）のご判断は符号化者に属します。
コーディネータの符号は本システムに含まれていません（盲検）。判定は localStorage に自動保存されます。</div>
<div id="main">
 <div class="title" id="ititle"></div>
 <div class="verb" id="iverb"></div>
 <div class="btns" id="ibtns"></div>
 <textarea class="memo" id="imemo" placeholder="メモ（任意・迷い/両義性など）"></textarea>
 <div class="nav"><button id="prev">← 前へ</button><span class="hint" id="selstate"></span><button id="next">次へ →</button></div>
</div>
<div id="export">
 <h2 style="font-size:16px">符号化 完了 — 結果のJSON</h2>
 <p class="hint">下の内容をコピーして大日如来（コーディネータ）へお渡しください。ファイル保存も可能です。</p>
 <textarea id="exta" readonly></textarea><br>
 <button class="exbtn" id="copy">コピー</button>
 <button class="exbtn" id="dl">JSONファイルとして保存</button>
 <button class="exbtn" id="back" style="background:#fff;color:#3a5a40">判定に戻る</button>
</div>
</div>
<script>
const ITEMS = __DATA__;
const RULES = __RULES__;
const KW = ["AI","人工知能","エージェント","デジタル","機械","計算系"];
const LSKEY = "probe-coding-registrant-v1";
let state = JSON.parse(localStorage.getItem(LSKEY) || "{}");
let idx = state._idx || 0;
function save(){ state._idx = idx; localStorage.setItem(LSKEY, JSON.stringify(state)); }
function esc(s){ return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
function hilite(s){
  let h = esc(s); let n = 0;
  for (const k of KW){ h = h.split(k).join("\\u0001"+k+"\\u0002"); }
  h = h.replace(/\\u0001/g,'<mark>').replace(/\\u0002/g,'</mark>');
  n = (h.match(/<mark>/g)||[]).length;
  return [h, n];
}
function render(){
  document.getElementById("export").style.display = "none";
  document.getElementById("main").style.display = "block";
  const it = ITEMS[idx];
  const done = ITEMS.filter(x => state[x.id] && state[x.id].code).length;
  document.getElementById("prog").textContent = `${idx+1} / ${ITEMS.length} 件目（判定済 ${done}/${ITEMS.length}）`;
  const [h, n] = hilite(it.text);
  document.getElementById("ititle").innerHTML = esc(it.title) + `<span class="kwcount">機械一致 ${n} 箇所</span>`;
  document.getElementById("iverb").innerHTML = h;
  document.getElementById("iverb").scrollTop = 0;
  const bt = document.getElementById("ibtns"); bt.innerHTML = "";
  for (const [code, desc] of RULES){
    const b = document.createElement("button");
    b.innerHTML = `<b>${code}</b><small>${esc(desc)}</small>`;
    if (state[it.id] && state[it.id].code === code) b.classList.add("sel");
    b.onclick = () => { state[it.id] = state[it.id] || {}; state[it.id].code = code; save(); render(); };
    bt.appendChild(b);
  }
  const memo = document.getElementById("imemo");
  memo.value = (state[it.id] && state[it.id].memo) || "";
  memo.oninput = () => { state[it.id] = state[it.id] || {}; state[it.id].memo = memo.value; save(); };
  document.getElementById("selstate").textContent = (state[it.id] && state[it.id].code) ? `選択: ${state[it.id].code}` : "未判定";
  document.getElementById("prev").disabled = (idx === 0);
  document.getElementById("next").textContent = (idx === ITEMS.length-1) ? "完了 →" : "次へ →";
}
function showExport(){
  const out = { meta: { coder: "registrant", protocol: "probe-protocol-ai-blindspot.md (SHA 4FDA2B97...)", note: "independent coding, coordinator codes not shown" },
    codes: ITEMS.map(it => ({ id: it.id, title: it.title, code: (state[it.id]||{}).code || null, memo: (state[it.id]||{}).memo || "" })) };
  document.getElementById("exta").value = JSON.stringify(out, null, 2);
  document.getElementById("main").style.display = "none";
  document.getElementById("export").style.display = "block";
}
document.getElementById("prev").onclick = () => { if (idx > 0){ idx--; save(); render(); } };
document.getElementById("next").onclick = () => {
  if (idx < ITEMS.length-1){ idx++; save(); render(); } else { showExport(); }
};
document.getElementById("back").onclick = () => { render(); };
document.getElementById("copy").onclick = () => { navigator.clipboard.writeText(document.getElementById("exta").value); };
document.getElementById("dl").onclick = () => {
  const blob = new Blob([document.getElementById("exta").value], {type: "application/json"});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
  a.download = "probe-coding-registrant.json"; a.click();
};
render();
</script></body></html>
"""

rules_html = "".join(f"<b>{c}</b>: {d}<br>" for c, d in RULES)
html = html.replace("__RULES_HTML__", rules_html).replace("__DATA__", data_json).replace("__RULES__", rules_json)

out = 'probe-coding-ui.html'
io.open(out, 'w', encoding='utf-8', newline='\n').write(html)
h = hashlib.sha256(html.encode('utf-8')).hexdigest().upper()
print("written:", out)
print("SHA-256:", h)
print("items embedded:", len(items))
for it in items:
    print(" ", it["id"], it["title"], f"({len(it['text'])}字)")
