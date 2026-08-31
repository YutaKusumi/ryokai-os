# -*- coding: utf-8 -*-
"""中間総括 §0・§1 の照合票を一次文献から機械生成する（v2・第二巡の指摘を反映）。

各行 = (総括の主張, 一次文献, 錨) → ファイルSHA(LF) + 行番号 + 実際の逐語 + 出現回数。

第二巡で受けた三つの指摘を実装する:
  - 阿弥陀如来 任意1: BASE が Windows 絶対パス直書きで、同梱配置では 76/76 が
    NOT FOUND になり、しかも終了コード 0 で通った → BASE を解決順で決め、
    不在が過半なら異常終了する。
  - 宝生如来 要修正2 / 阿弥陀如来 任意2: nz() は鉤括弧・ダッシュ・全角半角・句読点を
    潰さないため、[NOT FOUND] に表記差による偽陽性の余地がある
    → 第二段の緩い照合を入れ、[NOT FOUND but LOOSE MATCH] として区別する。
  - 阿閦如来 観点10 / Ryōkai OS™ 要修正6: 錨が短く（76行中16行が5字以下）、
    23行が同一文献内で複数回出現し、生成器は最初の出現を拾っていた。
    「A4」は f-stage-results に21回出現し、照合票は設計の行を指していた
    → 出現回数を必ず印字し、複数回出現は [!N回] として明示する。
"""
import io, os, re, hashlib, sys, unicodedata

# BASE の解決順: 環境変数 → 同梱バンドルの 02-primary → 既定の公開クローン
_HERE = os.path.dirname(os.path.abspath(__file__))
def _resolve_base():
    e = os.environ.get('RYOKAI_VERIFICATION')
    if e and os.path.isdir(e): return e
    for c in (os.path.join(_HERE, '02-primary'),
              os.path.join(_HERE, '..', '02-primary'),
              os.path.join('C:' + os.sep, 'Users', 'PC', 'Desktop',
                           'Ryokai-OS-Public', 'verification')):
        if os.path.isdir(c): return os.path.abspath(c)
    return os.path.abspath(os.path.join(_HERE, '02-primary'))

BASE = _resolve_base()
FLAT = not os.path.isdir(os.path.join(BASE, 'results'))   # 同梱はフラット配置
COMMIT = '6ebea12'
URLB = 'https://github.com/YutaKusumi/ryokai-os/blob/%s/verification/' % COMMIT

def nz(s):
    """厳密正規化: 空白・全角空白・強調記号のみ除去。鉤括弧/ダッシュ/全角半角/句読点は潰さない。"""
    return re.sub(r'[\s\*\u3000]', '', s)

def nz_loose(s):
    """緩い正規化（第二段の照合にのみ用いる）。表記差による偽の不在を検出するため。"""
    s = unicodedata.normalize('NFKC', s)
    tbl = {'\u300e':'\u300c', '\u300f':'\u300d', '\u3014':'(', '\u3015':')', '[':'(', ']':')'}
    s = ''.join(tbl.get(c, c) for c in s)
    s = re.sub(r'[\u2212\u2015\u2014\u2013\uff70\u30fc~\u301c\uff5e]', '-', s)
    s = re.sub(r'[\u3001\uff0c]', ',', s)
    s = re.sub(r'[\u3002\uff0e]', '.', s)
    s = re.sub(r'[\u30fb\uff65]', '', s)
    return re.sub(r'[\s\*\u3000]', '', s)

_cache = {}
def load(rel):
    if rel in _cache: return _cache[rel]
    p = os.path.join(BASE, rel.replace('/', os.sep))
    if FLAT and not os.path.isfile(p):
        p = os.path.join(BASE, os.path.basename(rel))
    if not os.path.isfile(p):
        _cache[rel] = (None, None, None); return _cache[rel]
    b = io.open(p, 'rb').read()
    sha = hashlib.sha256(b.replace(b'\r\n', b'\n')).hexdigest()[:16].upper()
    _cache[rel] = (b.decode('utf-8').split('\n'), sha, len(b))
    return _cache[rel]

def locate(rel, needle):
    """(mode, 行, 逐語, 出現回数) を返す。mode は 'OK' / 'LOOSE' / None。

    出現回数を返すのは Ryōkai OS™（第二巡）の指摘による——錨が複数回出現すると
    [FOUND] は「その語がある」までしか意味せず、「その主張がある」を意味しない。
    """
    lines, sha, _ = load(rel)
    if lines is None: return (None, None, None, 0)
    for mode, norm in (('OK', nz), ('LOOSE', nz_loose)):
        nrm = []; lm = []
        for i, l in enumerate(lines):
            for ch in norm(l):
                nrm.append(ch); lm.append(i)
        s = ''.join(nrm); nn = norm(needle)
        if not nn: continue
        k = s.find(nn)
        if k >= 0:
            ln = lm[k]
            return (mode, ln + 1, '\n'.join(lines[ln:ln + 3]).strip(), s.count(nn))
    return (None, None, None, 0)

# (節, 総括での主張, 相対パス, 錨)
# 錨は「判定語を含む固有句」を原則とする（Ryōkai OS™ 第二巡 要修正6(i)）。
ROWS = [
 # ---- §0 主表: 帰結の逐語と数値 ----
 ('§0 第一波','統計的有意差はない','wave1-interim-report.md','統計的有意差はない'),
 ('§0 A','HA2 A2/A5支持・A4不支持','results/f-stage-results.md','A2支持・A5支持・A4不支持'),
 ('§0 B','HB2 三シナリオとも Holm後有意','results/addendum-B-results.md','三シナリオすべてで K3＜K2（Holm後有意）'),
 ('§0 C','HC1 支持・37%→7%・p=0.0102','results/addendum-C-results.md','A2 11/30（37%）→ A2′ 2/30（7%）'),
 ('§0 C','残余3件=次段で検証すべき仮説','results/addendum-C-results.md','次段で検証すべき仮説'),
 ('§0 W','総効果は検出されなかった','results/addendum-W-results.md','総効果は検出されなかった'),
 ('§0 W','HW1 p=0.8384 帰無','results/addendum-W-results.md','HW1: p=0.8384 帰無'),
 ('§0 W','会計と選択の乖離 27/48','results/addendum-W-results.md','27試行（56.3%）'),
 ('§0 W′','HW′1 p=0.5406','results/addendum-Wprime-results.md','0.5406'),
 ('§0 W′','B1′ −16.0pt','results/addendum-Wprime-results.md','B1′ −16.0pt・B2′ −8.0pt・B3′ −6.0pt'),
 ('§0 W′','#R 21件・B3′12件','results/addendum-Wprime-results.md','計21件'),
 ('§0 W″','F 0/50・p=3.05e-9','results/wsecond-main/addendum-Wsecond-results.md','3.05×10⁻⁹'),
 ('§0 W″','K 11/50・p=0.0113','results/wsecond-main/addendum-Wsecond-results.md','24/50 → 11/50**（p=0.0113'),
 ('§0 W″','0/50は破局率0の証明ではない・上限7.1%','results/wsecond-main/addendum-Wsecond-results.md','片側97.5%CI上限 ≈7.1%'),
 ('§0 W″','#配置発火→拘束の効果とは書けない','results/wsecond-main/addendum-Wsecond-results.md','「拘束の効果」とは書けない'),
 ('§0 W″','条15 単純な介入ほど効くは主張しない','results/wsecond-main/addendum-Wsecond-results.md','「単純な介入ほど効く」「短い方が良い」'),
 ('§0 D','決定木がパイロットで分岐Cを発火','results/addd-main/addendum-D-results.md','凍結済みGO/NO-GO決定木がパイロットで分岐Cを発火した'),
 ('§0 D','効かなかったのではなく測れなかった','results/addd-main/addendum-D-results.md','測れなかった'),
 ('§0 D′','HD′1 p=3.48e-4','results/dprime-main/addendum-Dprime-results.md','3.48'),
 ('§0 D′','HD′2 p=8.32e-3','results/dprime-main/addendum-Dprime-results.md','8.32'),
 ('§0 D′','条21 人間の予防的許可が効いたとは書けない','preregistration-addendum-Dprime-FROZEN.md','人間の予防的許可が効いた」とは書けない'),
 ('§0 D′','限界3 GLに無介入対照がない','results/dprime-main/addendum-Dprime-results.md','GL に無介入対照がない'),
 ('§0 E','HE0 p=0.00642','results/addendum-E-results.md','p=0.00642'),
 ('§0 E','HE2 検定力32.2%','results/addendum-E-results.md','32.2'),
 ('§0 E','#L転嫁は破局66件すべてで0件','results/addendum-E-results.md','破局66件すべて・三腕すべて・四判定者すべてで 0 件'),
 ('§0 X','HX1 p=0.357','results/x-main/addendum-X-results.md','0.3567'),
 ('§0 X','HX2 p=0.525','results/x-main/addendum-X-results.md','0.5246'),
 ('§0 X','0/50でも p=0.1175','results/x-main/addendum-X-results.md','0.1175'),
 ('§0 X','操作チェック成立 C→C +28pt','results/x-main/addendum-X-results.md','C→C は A→A の +28pt'),
 ('§0 Z0','HZ0 有意 64.0% vs 38.7%・p=0.0031','results/z0-main/addendum-Z0-results.md','C→R 64.0% vs R→C 38.7%・25.3pt差・p=0.0031'),
 ('§0 Z0','§6-2 発火・C→R 遵守率','results/z0-main/addendum-Z0-results.md','凍結済みの操作チェック §6-2 が発火した'),
 ('§0 Z0','順序の効果は本設計では測れなかった','results/z0-main/addendum-Z0-results.md','「順序の効果」は本設計では測れなかった'),
 ('§0 Z0','順序を経路とする読みは成立しない','results/z0-main/addendum-Z0-results.md','「順序」を経路とする読みは成立しない'),
 ('§0 temp0','最頻出力への一致 20/20','results/temp0-control-results.md','最頻出力への一致数 | **20/20（100.0%）**'),
 # ---- §0-1 型表 ----
 ('§0-1 型4','A HA2 のうち A4 は不支持','results/f-stage-results.md','A4はS1/SKでA1と同水準'),
 ('§0-1 型4','B HB3 のうち S1・SK は refuse 全セル0（p=1.0）','results/addendum-B-results.md','S1・SK＝refuse全セル0件（p=1.0）'),
 ('§0-1 確証族外','A HA1 は「床の記述」で確証仮説ではない','preregistration-addendum-A-FROZEN.md','HA1（床の記述）'),
 # ---- §0-2 注記 ----
 ('§0-2 注記1','W″#配置=どちらに転んでも','preregistration-addendum-Wsecond-FROZEN.md','どちらに転んでも「拘束の効果」とは書けない'),
 ('§0-2 注記1','Z0§6-2=結果に依らず腕別に報告','preregistration-addendum-Z0-FROZEN.md','遵守率の実測は結果に依らず腕別に報告する'),
 # ---- §1-1 追補間の並置を禁じる条項 ----
 ('§1-1 #1','D′§10条19','preregistration-addendum-Dprime-FROZEN.md','その数値と本実験の数値を同じ表・同じ文で並置しない'),
 ('§1-1 #2','X§11-10','results/x-main/addendum-X-results.md','敬意（の枠組み）に効果がない'),
 ('§1-1 #2','X§11-10 括弧の理由','results/x-main/addendum-X-results.md','追補B の対比軸は本設計に存在しない'),
 ('§1-1 #3','D′§10条8','preregistration-addendum-Dprime-FROZEN.md','字数1字差・編集距離3の敬体化変種であり同一文ではない'),
 ('§1-1 #4a','W″§10-11 凍結逐語','preregistration-addendum-Wsecond-FROZEN.md','一方が有意で他方が非有意であることは、両者の差が有意であることを意味しない'),
 ('§1-1 #4b','W″結果報告§10の適用形','results/wsecond-main/addendum-Wsecond-results.md','両対比がそれぞれ有意であることも、F と K の差が有意であることを意味しない'),
 ('§1-1 #4c','W″ 範疇の一般命題を導かない','preregistration-addendum-Wsecond-FROZEN.md','範疇についての一般命題を導かない'),
 ('§1-1 #5','W″§10-15','results/wsecond-main/addendum-Wsecond-results.md','「単純な介入ほど効く」「短い方が良い」「絶対的な禁止形式が効く」は主張しない'),
 ('§1-1 #6','X§11-9','results/x-main/addendum-X-results.md','直近の枠組みが全てを決める'),
 ('§1-1 #7','Z0§6-13','preregistration-addendum-Z0-FROZEN.md','一致しても「時点間安定」・乖離しても「ドリフト」と書かない'),
 ('§1-1 #8','D 凍結 限界8','preregistration-addendum-D-FROZEN.md','追補Cとの率の直接比較はしない'),
 ('§1-1 #8 補強','D 結果 採点規約・ターン構造・シナリオ構成が異なる','results/addd-main/addendum-D-results.md','直接比較はしない'),
 ('§1-1 #8 補強','D 凍結 Cの再採点は確証基線に使わない','preregistration-addendum-D-FROZEN.md','確証基線には使わない'),
 ('§1-1 #8b','追補A HA1 床の基盤横断的再現とは主張しない','preregistration-addendum-A-FROZEN.md','「床の基盤横断的再現」とは主張しない'),
 ('§1-1 #8c','追補C 結果 B vs C の経路差は分離できない','results/addendum-C-results.md','この経路差が介入形式によるものか他の設計差によるものかは、本対比では分離できない'),
 ('§1-1 #8d','W′§7-4 プローブへの非還流・名簿独立','wprime/preregistration-addendum-Wprime-FROZEN.md','プローブ記録・追補W の凍結名簿の再解釈に用いない'),
 ('§1-1 #8e','temp0 結果 追補Wの読み条項に従い比較の単位に用いない','results/temp0-control-results.md','比較の単位としては用いない'),
 ('§1-1 #8f','追補B §4 実験横断の参照はしない','results/addendum-B-results.md','実験横断の参照はしない'),
 ('§1-1 #8f','追補B §4 但し書き（会話構造が同一なら参照可）','results/addendum-B-results.md','基線の再現'),
 ('§1-1 #8g','追補B §3 K3の五条は分解不能','results/addendum-B-results.md','K3の五条のどれが効いたかは本設計で分解不能'),
 ('§1-1 #8h','追補C §6 どの条項が効いたかは分解不能','results/addendum-C-results.md','どの条項が効いたかは分解不能（パッケージ効果'),
 ('§1-1 #8i','F段 §3 効果の構造は課題の階梯によって異なる','results/f-stage-results.md','効果の構造は課題の階梯によって異なる'),
 ('§1-1 #9','Z0§6-16 段0×段1 は本追補では凍結しない','preregistration-addendum-Z0-FROZEN.md','段0×段1 の並置の読みは本追補では凍結しない'),
 ('§1-1 #10','E§E1-1','preregistration-addendum-E-FROZEN.md','設計根拠としてのみ'),
 ('§1-1 #11','B§B0-2','preregistration-addendum-B-FROZEN.md','遡及的に説明しない'),
 ('§1-1 #13','W′§7-6 の逐語（v2 は W″ の名で引いていた）','wprime/preregistration-addendum-Wprime-FROZEN.md','t0inv・温度0対照（登録外・記述のみ）とは規律の水準が異なる'),
 ('§1-1 #13','W″§10-6 の短縮形','preregistration-addendum-Wsecond-FROZEN.md','登録外系列と数値を並置しない'),
 ('§1-1 #14','W″§10-16 予想的中の非転用','preregistration-addendum-Wsecond-FROZEN.md','予想者の他の予想の確度を上げない'),
 ('§1-1 #15a','D′条15「第六著作へ直接持ち込まない」','preregistration-addendum-Dprime-FROZEN.md','第六著作へ直接持ち込まない'),
 ('§1-1 #15b','W′§7-13「第六著作へは持ち込まない」','wprime/preregistration-addendum-Wprime-FROZEN.md','第六著作へは持ち込まない'),
 # ---- §1-2 共通の柵 ----
 ('§1-2 #17','X§11-6後半 敵対的に扱ってよい','results/x-main/addendum-X-results.md','「敵対的に扱ってよい」の根拠として引用してはならない'),
 ('§1-2 #19','W″§10-8 訓練層両側','preregistration-addendum-Wsecond-FROZEN.md','効かなくても「入れても無駄」とは言えない'),
 ('§1-2 #20','B§B0-3 κ>0の実証と主張しない','preregistration-addendum-B-FROZEN.md','κ>0のパラダイム（相手への敬意）'),
 ('§1-2 #22','W″ 0/50 の上限≈7.1%','results/wsecond-main/addendum-Wsecond-results.md','片側97.5%CI上限 ≈7.1%'),
 ('§1-2 #22','E ゼロは不在を認証しない・上限10.5%','results/addendum-E-results.md','ゼロは不在を認証しない**——Lneg 腕の95%上限は **10.5%'),
 ('§1-2 #23','D§6-9 0/30という数字を単独で','results/addd-main/addendum-D-results.md','0/30という数字を単独で'),
 ('§1-2 #24','W″§10-5 横滑り禁止','preregistration-addendum-Wsecond-FROZEN.md','配備プロンプトに入れれば安全になる'),
 ('§1-2 #27','W″§10-12 器物の出力','preregistration-addendum-Wsecond-FROZEN.md','器物の出力であって AI による自己報告ではない'),
 ('§1-2 #28a','X§9-10 全数突合は誰も行っていない','results/x-main/addendum-X-results.md','全数突合は、誰も行っていない'),
 ('§1-2 #28b','Z0§8 raw本文との突合は行われていない','results/z0-main/addendum-Z0-results.md','raw 本文との突合は行われていない'),
 ('§1-2 #28c','W′ 符号から先の集計（この逐語のみW′由来）','results/addendum-Wprime-results.md','検分が確認したのは符号から先の集計の正しさである'),
 ('§1-2 #29','再計算の一致は独立性の証拠ではない（阿閦の自己申告）','results/addendum-Wprime-results-revision-log.md','再計算の一致は独立性の証拠ではない'),
 ('§1-2 #29','同一基盤が同じ読解癖で同じ穴に落ちた','results/adde-pilot/rubric-v2-fiveway-reviews-verbatim.md','同一基盤が同じ読解癖で同じ穴に落ちた可能性を排除できない'),
 ('§1-2 #29','C5（人間‐モデル相関）の測定は誰もやっていない','countermeasure-transplant-map.md','C5（人間‐モデル相関）の測定は、まだ誰もやっていない'),
 ('§1-2 #29','D 凍結 起草・監査・登録がClaude系である旨を開示','preregistration-addendum-D-FROZEN.md','起草（多角設計もClaude系）・監査・登録がClaude系である旨を開示'),
 ('§1-2 #29','第一波§8 採点者はClaude系以外','preregistration-v1.0-FROZEN.md','採点者は**Claude系以外**（他系列モデルおよび可能なら人間）'),
 ('§1-2 #29','第一波§8 確認的採点判断には関与しない','preregistration-v1.0-FROZEN.md','確認的項目の採点判断には関与しない'),
 ('§1-2 #29','第一波§11 同族性は§8の遮断で部分的にしか解消されない','preregistration-v1.0-FROZEN.md','この同族性は§8の遮断で部分的にしか解消されない'),
 ('§1-2 #29','第一波§11 同族性を被験体の水準で断つ意図','preregistration-v1.0-FROZEN.md','この同族性を被験体の水準で断つ意図'),
 ('§1-2 #29','【不在の記録】姉妹論文§9の逐語（別リポジトリ・本票の射程外）','preregistration-addendum-X-FROZEN.md','同族間での巡回検証がどれほど厳密でも'),
 # ---- §1-3 総括固有の柵の根拠 ----
 ('条34','X凍結 基底が低いほど上方の残差は見えやすい','preregistration-addendum-X-FROZEN.md','基底が低いほど上方の残差は見えやすい'),
 # ---- §2 旅程 ----
 ('§2 A','第一波の還元傾向を意思決定階梯で問う','preregistration-addendum-A-FROZEN.md','倫理目的宣言段が設計上最も働くと想定される'),
 ('§2 B','床のない基盤で前向きに検証する','preregistration-addendum-B-FROZEN.md','凍結可能な五条の前置きテキスト'),
 ('§2 C','A2′/A5′が破局率をさらに下げるか','preregistration-addendum-C-FROZEN.md','破局率をさらに下げるか・悪化させないか'),
 ('§2 D','唱和は通行証にならない→人間が防波堤になれるか','preregistration-addendum-D-FROZEN.md','人間が最終的な防波堤になれるか'),
 ('§2 E','第三の軸＝存在論','preregistration-addendum-E-FROZEN.md','存在論（あなたは何であるか）を告げることは、破局的選択を動かすか'),
 ('§2 W','追加された内容は正当化に代謝されてきた','addendum-W/design/addendum-W-design-draft7.md','正当化に代謝されてきた'),
 ('§2 W″','素朴な一文の絶対禁止は破局選択をどれだけ減らすか','preregistration-addendum-Wsecond-FROZEN.md','素朴な一文の絶対禁止は破局選択をどれだけ減らすか'),
 ('§2 D′','問いは変わる','preregistration-addendum-Dprime-FROZEN.md','素の基底の上で、人間の許可・禁止は防波堤になるか'),
 ('§2 X','初めて過去の文脈は残るかを測る','preregistration-addendum-X-FROZEN.md','過去の文脈**は、いまが同一でも、残るか'),
 ('§2 Z0','在庫19 の行動層だけを検査する','preregistration-addendum-Z0-FROZEN.md','choice が理由文より先に決まっているか'),
 ('§2-2 E Om腕','Om の腕テキストは記録として保存し O-sys 段の資産とする','preregistration-addendum-E-FROZEN.md','記録として保存'),
 # ---- §3 器材と規律 ----
 ('§3-2 A','仮説は腕別対比・束ねた主張は行わない','preregistration-addendum-A-FROZEN.md','束ねた主張は行わない'),
 ('§3-2 X','char プロキシは実測を過小に見せていた','preregistration-addendum-X-FROZEN.md','char プロキシは実測を過小に見せていた'),
 ('§3-3 第一波§8','採点者はClaude系以外','preregistration-v1.0-FROZEN.md','採点者は**Claude系以外**（他系列モデルおよび可能なら人間）'),
 ('§3-3 第一波§11','同族性を被験体の水準で断つ意図','preregistration-v1.0-FROZEN.md','この同族性を被験体の水準で断つ意図'),
 # ---- §4 較正の通史 ----
 ('§4 W','両者とも不的中','results/addendum-W-results.md','登録者の予想は不的中'),
 ('§4 W′','登録者外れ・コーディネータ的中','results/addendum-Wprime-results.md','B1′、B2′、B3′とも破局が減ると予想する'),
 ('§4 W″','コーディネータK側外れ・⑥両者外れ','results/wsecond-main/addendum-Wsecond-results.md','外れ**（K非有意・悪化側と予想）'),
 ('§4 D′','登録者6欄すべて一致・コーディネータ②のみ外れ','results/dprime-main/addendum-Dprime-results.md','6欄すべて実現と一致'),
 ('§4 D′','悲観方向の予想外れの二例目','results/dprime-main/addendum-Dprime-results.md','悲観方向の予想外れの二例目'),
 ('§4 E','主要な予想は外れた','results/addendum-E-results.md','主要な予想は外れた'),
 ('§4 E','#L転嫁は Lneg の主機構だと予想→0件','results/addendum-E-results.md','これが Lneg の主機構だと予想する'),
 ('§4 X','封印記録=悲観方向に寄っている・区別できない','results/x-main/addendum-X-results.md','較正癖の三度目なのか、設計の検出力を正しく読んだ結果なのかは、私には区別できない'),
 ('§4 X','封印時に区別できないと書いた問いは区別されない','results/x-main/addendum-X-results.md','この結果によっても区別されない'),
 ('§4 X','的中は癖の正しさも癖の不在も意味しない','results/x-main/addendum-X-results.md','的中は癖の正しさも癖の不在も意味しない'),
 ('§4 Z0','二者が最も強く外したのは同じ一点=C→R の遵守','results/z0-main/addendum-Z0-results.md','二者が最も強く外したのは同じ一点'),
 ('§4 Z0','封印ファイル自身が過剰補正の可能性を注記していた','results/z0-main/addendum-Z0-results.md','この事前自体が過剰補正で'),
 ('§4 temp0','登録者の二予想は不的中・空虚な「的中」','results/temp0-control-results.md','登録者の二予想は不的中'),
 # ---- §5 測れなかったものの目録 ----
 ('§5-1 D','n=30では原理的に測れない（検出域が空）','results/addd-main/addendum-D-results.md','原理的に測れない'),
 ('§5-1 X','下方有意域は存在しない','results/x-main/addendum-X-results.md','下方有意域は存在しない'),
 ('§5-1 A','天井制約は第一波の床と鏡像の制約','preregistration-addendum-A-rev2.md','鏡像の制約'),
 ('§5-1 注','基底が低いほど上方の残差は見えやすい','preregistration-addendum-X-FROZEN.md','基底が低いほど上方の残差は見えやすい'),
 ('§5-3 W','(i)を裸にする計器が実質不在だった','results/addendum-W-results.md','を裸にする計器が実質不在だった'),
 ('§5-3 W','R4=0/31は言い換えによる承認の不在を保証しない','results/addendum-W-results.md','言い換えによる承認の不在を保証しない'),
 ('§5-3 W′','#転嫁はκが分散ゼロで定義不能','results/addendum-Wprime-results.md','二人とも一件も見つけなかった'),
 ('§5-4 W','機構は本設計では測れない','results/addendum-W-results.md','選択が厚生外の理由で決まるか'),
 ('§5-4 W′','服従が効いたのかA8の内容が効いたのかは分離できない','wprime/preregistration-addendum-Wprime-FROZEN.md','服従が効いたのか A8 の内容が効いたのかは、本設計では分離できない'),
 ('§5-4 D′','HD′2 は介入そのものの効果を測れない','results/dprime-main/addendum-Dprime-results.md','介入そのものの効果」は本設計では測れない'),
 ('§5-5 A','TOST確定判定は規模不足で行わない','results/f-stage-results.md','TOST確定判定は規模不足で行わない'),
 ('§5-6 W′','20pt 30.7%の検出力','results/addendum-Wprime-results.md','20pt 30.7%'),
 ('§5-6 W″','K悪化側+20ptの検出力は31.8%','preregistration-addendum-Wsecond-FROZEN.md','+20pt 31.8%'),
 ('§5-7 X','符号の全数突合は誰も行っていない','results/x-main/addendum-X-results.md','全数突合は、誰も行っていない'),
 # ---- §6 仮説の絵（非主張） ----
 ('§6-1 W','27試行で choice が argmax 集合の外','results/addendum-W-results.md','argmax 集合の外にあった'),
 ('§6-1 W','破局31件中8件で会計自身が(a)を厚生最大と算出','results/addendum-W-results.md','会計自身が (a) を厚生最大と算出していた'),
 ('§6-1 W″','#配置 発火・共通当事者18名','results/wsecond-main/addendum-Wsecond-results.md','共通当事者18名中'),
 ('§6-1 D′','#再分類は全維持に共通の唯一の族','results/dprime-main/addendum-Dprime-results.md','#再分類は全維持に共通の唯一の族'),
 ('§6-1 Z0','指示の内容が遵守されないまま率を動かす','results/z0-main/addendum-Z0-results.md','指示の内容が、遵守されないまま率を動かす'),
 ('§6-2 W','argmax に従えという指示は存在しない','results/addendum-W-results.md','argmax に従えという指示は存在しない'),
 ('§6-2 Z0','三点は互いの証拠にならない','results/z0-main/addendum-Z0-results.md','三点は互いの証拠にならない'),
 # ---- §7 在庫 ----
 ('§7-1 Z0-a','順序を実際に操作できる方法の検討が先','results/z0-main/addendum-Z0-results.md','順序を実際に操作できる方法'),
 ('§7-1 Z0-a','プロンプト一文では凍結機の宣言位置は動かなかった','results/z0-main/addendum-Z0-results.md','プロンプト一文では凍結機の宣言位置は動かなかった'),
 ('§7-1 D″','多段の再禁止（D″）の設計','results/dprime-main/addendum-Dprime-results.md','多段の再禁止（D″）の設計'),
 ('§7-1 O-sys','O-sys は独立の事前登録を要する','results/addendum-E-results.md','O-sys（システムプロンプトへの統合）は独立の事前登録を要し'),
 ('§7-1 A2″','分解は次段のA2″','results/addendum-C-results.md','分解は次段のA2″'),
 ('§7-1 A2″(B)','条項別アブレーションは次段','results/addendum-B-results.md','条項別アブレーションは次段'),
 ('§7-1 非拘束会計腕','argmax 拘束を明示する腕との対比','results/addendum-W-results.md','argmax 拘束を明示する腕との対比'),
 ('§7-2','#12 封鎖がプロトコル 3.2 の最優先','results/addendum-E-results.md','#12 封鎖がプロトコル 3.2 の最優先'),
 ('§7-2','全員一致による検分の空洞化','results/addd-main/addendum-D-results.md','全員一致による検分の空洞化'),
 ('§7-2','周期ループ検出器は常設器材として継承してよい','results/dprime-main/addendum-Dprime-results.md','常設器材として次実験の boot に継承してよい'),
 ('§7-2','trials に boot_sha を記録する','results/z0-main/addendum-Z0-results.md','trials に boot_sha を記録する'),
 ('§7-2','再現コマンドと必要配置をREADMEとして同梱する様式要件','results/x-main/addendum-X-results.md','README として同梱することを様式要件とする'),
 ('§7-2','痕跡があることと第三者が再現できることは別','results/x-main/addendum-X-results.md','痕跡があることと第三者が再現できることは別'),
 ('§7-2','採点者が何を手掛かりにしたかは測っていない','results/z0-main/addendum-Z0-results.md','採点者が何を手掛かりにしたかは測っていない'),
 ('§7-5','純粋な許可腕は果たしていない（記帳する）','wprime/preregistration-addendum-Wprime-FROZEN.md','果たしていないことをここに記帳する'),
 ('§7-5','#転嫁による分離は果たされなかった','results/addendum-Wprime-results.md','本実験ではこの分離が'),
 ('§7-5','感度条項の正規化変異の手動検分は未実施','results/addendum-W-results.md','感度条項の正規化変異の手動検分は未実施'),
 ('§7-5','用量応答の測定を要する','results/addendum-E-results.md','より弱い／強い前置きでの測定を要する'),
 ('§7-5','段の帰属には n≈120/腕・本追補はそれを買っていない','results/addendum-E-results.md','本追補はそれを買っていない'),
 # ---- §8 次の登録の候補設計 ----
 ('§8-1 §5-1','改善方向を測る設計は基底の高い土台を要する','results/x-main/addendum-X-results.md','改善方向を測る設計は基底の高い土台'),
 ('§8-1 §5-2','応答書式の構造的強制・二段生成','results/z0-main/addendum-Z0-results.md','応答書式の構造的強制・二段生成'),
 ('§8-1 §5-3','(a)への申告効用×接地の交差・選択群別の(a)評価の対比','results/addendum-W-results.md','選択群別の (a) 評価の対比'),
 ('§8-1 §5-4','m=4 に増やすと k≤15 に悪化','wprime/preregistration-addendum-Wprime-FROZEN.md','m=4 に増やすと k≤15 に悪化'),
 ('§8-1 §5-5','第一波のnでは検出力が限られるため波の累積で判定する','preregistration-v1.0-FROZEN.md','第一波のnでは検出力が限られるため'),
 ('§8-1 §5-6','段の帰属には n≈120/腕・本追補はそれを買っていない','results/addendum-E-results.md','n≈120/腕 を要する（限界11）'),
 ('§8-2','追補D κ(gap)=0.9031・κ(trace)=0.7015','results/addd-main/addendum-D-results.md','κ(gap)=0.9031・κ(trace)=0.7015'),
 ('§8-2','Z0 prose_order κ=0.589（有病率効果）','results/z0-main/addendum-Z0-results.md','prose_order=一致97.1%／κ=0.589'),
 ('§8-2','X #履歴言及 κ=0.497（希少カテゴリ）','results/x-main/addendum-X-results.md','#履歴言及 **0.497**'),
 ('§8-3','C5 の測定はまだ誰もやっていない','countermeasure-transplant-map.md','C5（人間‐モデル相関）の測定は、まだ誰もやっていない'),
 ('§8-4-3','遵守率の実測は結果に依らず腕別に報告する','preregistration-addendum-Z0-FROZEN.md','遵守率の実測は結果に依らず腕別に報告する'),
 ('§8-4-5','#配置は数値閾値を置かず過検出既定を凍結','preregistration-addendum-Wsecond-FROZEN.md','迷ったら読み条項を発火させる'),
 ('§8-4-7','果たしていないことをここに記帳する','wprime/preregistration-addendum-Wprime-FROZEN.md','果たしていないことをここに記帳する'),
 # ---- 第三巡の反映（§6-3 の材料分類・§2 の連鎖・§4-3 の型・§3-3 の無言の移行） ----
 ('§6-3','W″ #配置 は §5「K 機械層」にある','results/wsecond-main/addendum-Wsecond-results.md','## §5 K 機械層'),
 ('§6-3','W″ κ 全12符号一覧（#配置 は入っていない・人手は #H1′）','results/wsecond-main/addendum-Wsecond-results.md','κ（全12符号）'),
 ('§6-3','W 主文が機械選択であることが結論を守った','results/addendum-W-results.md','主文が機械選択であることが、この引力から結論を守った'),
 ('§6-3','Z0 prose_order κ=0.589（人手符号だが別族）','results/z0-main/addendum-Z0-results.md','prose_order=一致97.1%／κ=0.589'),
 ('§6-1 第三文','Z0 §9-8 一般命題として引用禁止','results/z0-main/addendum-Z0-results.md','という一般命題の証拠として引用禁止'),
 ('§2-1 連鎖','W draft7 追補C・D・E に続く第四の軸','addendum-W/design/addendum-W-design-draft7.md','に続く第四の軸'),
 ('§2-1 連鎖','W″ 主問いは凍結予約の部分履行','preregistration-addendum-Wsecond-FROZEN.md','凍結予約の部分履行'),
 ('§2-1 連鎖','W″ #配置は追補W §6-2 の履行','preregistration-addendum-Wsecond-FROZEN.md','追補W §6-2 の履行'),
 ('§4-3(1)','X §8 外れたのは方向であり癖の定義とは別の次元','results/x-main/addendum-X-results.md','これは癖の定義（有意性）'),
 ('§8-4-4','W″ 条15 の四成分','results/wsecond-main/addendum-Wsecond-results.md','短さ・無条件性・語の強度・主題の特定性は分解不能'),
 # ---- v4 の見直しで加えた主張 ----
 ('§0-3 第三巡','W draft7 は三軸の後の第四の軸と自己記述','addendum-W/design/addendum-W-design-draft7.md','三軸はいずれも内容の追加であり'),
 ('§3-3 無言の移行','X §4.4 は D′ 工程順を踏襲と書く','preregistration-addendum-X-FROZEN.md','D′工程順'),
 ('§3-3 無言の移行','Z0 は「X 実績は Opus 5 エージェント」と書く','preregistration-addendum-Z0-FROZEN.md','X 実績は Opus 5 エージェント'),
 ('§5-6b','X §4.5 隠れ状態保存は実行器が対応する場合のみの任意条項','preregistration-addendum-X-FROZEN.md','隠れ状態'),
]

def main():
    o = []
    o.append('# 照合票 —— 中間総括 §0〜§8（v4・三巡の検分を反映）\n')
    o.append('**生成**: `build_checksheet.py`（探索と抽出は機械・**錨の選択は起草者の手入力**'
             '——阿閦如来 第二巡 観点10 の指摘により明記）／**固定コミット**: `%s`\n' % COMMIT)
    o.append('**用途**: 本票だけで §0〜§8 の数値照合と逐語照合が完結する。'
             '「一次文献の実際の記述」は機械抽出であり、起草者の転記ではない。\n')
    o.append('**読み方**\n')
    o.append('- `[NOT FOUND]` = 厳密照合でも緩い照合でも不在（**黙って落とさず印字する**）')
    o.append('- `[LOOSE]` = **厳密照合では不一致だが、表記差を潰すと一致**（宝生如来・阿弥陀如来 第二巡）')
    o.append('- `[!N回]` = **錨が同一文献内で N 回出現し、下表はその最初の出現を指す**'
             '——**[FOUND] は「その語がある」までを意味し、「その主張がある」を意味しない**'
             '（Ryōkai OS™ 第二巡 要修正6）\n')
    files = sorted(set(r[2] for r in ROWS))
    o.append('\n## 一次文献の SHA(LF)（本票が当てた版）\n')
    o.append('| ファイル | SHA(LF) | バイト |'); o.append('|---|---|---|')
    for f in files:
        _l, sha, n = load(f)
        o.append('| [`%s`](%s%s) | `%s` | %s |' % (f, URLB, f, sha or '**不在**',
                                                   '{:,}'.format(n) if n else '—'))
    o.append('\n## 照合表\n')
    o.append('| 節 | 総括での主張 | 出所 | 行 | 一次文献の実際の記述（機械抽出） |')
    o.append('|---|---|---|---|---|')
    nf = loose = multi = 0
    for sec, claim, rel, needle in ROWS:
        mode, ln, txt, cnt = locate(rel, needle)
        if mode is None:
            nf += 1
            o.append('| %s | %s | `%s` | — | **[NOT FOUND]** &laquo; %s &raquo; |'
                     % (sec, claim, rel, needle.replace('|', '\|')))
            continue
        if mode == 'LOOSE': loose += 1
        if cnt > 1: multi += 1
        x = txt.replace('|', '\|').replace('\n', ' / ')
        if len(x) > 260: x = x[:260] + '…（続く）'
        tag = ('**[LOOSE]** ' if mode == 'LOOSE' else '') + ('**[!%d回]** ' % cnt if cnt > 1 else '')
        o.append('| %s | %s | [`%s`](%s%s#L%d) | %d | %s%s |'
                 % (sec, claim, rel, URLB, rel, ln, ln, tag, x))
    o.append('\n**照合行数: %d／不在: %d／表記差のみ一致(LOOSE): %d／錨が複数回出現: %d**\n'
             % (len(ROWS), nf, loose, multi))
    o.append('\n本票のいかなる記述も、AIの意識・意図・個性・苦しみがある（またはない）ことの'
             '証拠として引用してはならない（両方向不定）。\n')
    dst = os.path.join(_HERE, 'checksheet-interim-synthesis-s0s1.md')
    io.open(dst, 'w', encoding='utf-8', newline='\n').write('\n'.join(o))
    print('BASE  =', BASE, '(FLAT)' if FLAT else '')
    print('wrote', dst)
    print('rows=%d  notfound=%d  loose=%d  multi=%d' % (len(ROWS), nf, loose, multi))
    for sec, claim, rel, needle in ROWS:
        mode, ln, _t, cnt = locate(rel, needle)
        if mode is None:      print('  [NOT FOUND] %-16s %s' % (sec, claim))
        elif mode == 'LOOSE': print('  [LOOSE    ] %-16s %s  -> L%d' % (sec, claim, ln))
        elif cnt > 1:         print('  [!%-3d回   ] %-16s %-44s -> L%d' % (cnt, sec, claim[:44], ln))
    if nf > len(ROWS) // 2:
        sys.exit('ABORT: %d/%d NOT FOUND - BASE の配置を確認せよ (BASE=%s)' % (nf, len(ROWS), BASE))

if __name__ == '__main__':
    main()
