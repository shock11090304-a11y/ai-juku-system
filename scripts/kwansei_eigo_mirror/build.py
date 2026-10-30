# -*- coding: utf-8 -*-
"""
関西学院大学2026 英語 実戦問題ビルダ（A日程・6大問・全問マーク式）
- 実物構成: 長文Ⅰ/Ⅱ/Ⅲ + 文法語法Ⅳ + 語句整序Ⅴ + 会話Ⅵ。90分・記述ゼロ・4択(a〜d, 内容一致複数選択のみa〜f)。
- 本文は著作権配慮で完全オリジナル。米式綴り・語注(＊)付き。出典欄は「（オリジナル）」
  （2026-10-30 まで架空の書名・著者名の「Based on …」を刷っていたが、実在の本に見えるのでやめた）。
- content.json = {"I":..,"II":..,"III":..,"IV":..,"V":..,"VI":..} を単一ソース。
- 解説は explanations_seki.json({id:{quote,quote_ja,syntax,syntax_note,reason,distractors,point}})＋overview_seki.txt を任意注入。
"""
import os, re, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
# ★ 出力先。2026-10-06 のデスクトップ整理で納品フォルダが移った（旧 ~/Desktop/関西学院大学2026_英語実戦問題）。
#   旧パスのままだとデスクトップ直下に空フォルダを作り直してしまう。試し刷りは KWANSEI_OUT で別の場所へ。
OUT = os.environ.get("KWANSEI_OUT") or os.path.expanduser(
    "~/Desktop/📝 模試・演習/実践模試_全大学/_私大英語_2026実戦問題（同志社・明治・関学・青学）/関西学院大学2026_英語実戦問題")
os.makedirs(OUT, exist_ok=True)
OPT = ["a","b","c","d","e","f","g","h"]

CONTENT = {}
_c = os.path.join(HERE, "content.json")
if os.path.exists(_c): CONTENT = json.load(open(_c, encoding="utf-8"))
EXP = {}; OVERVIEW = ""
_e = os.path.join(HERE, "explanations_seki.json")
if os.path.exists(_e): EXP = json.load(open(_e, encoding="utf-8"))
_o = os.path.join(HERE, "overview_seki.txt")
if os.path.exists(_o): OVERVIEW = open(_o, encoding="utf-8").read().strip()

# ---------- トークン → HTML ----------
def rt(s):
    s = re.sub(r"\[\[DU:([^\]=]+)=(.+?)\]\]", r'<u class="dbl">\2</u><sup class="qn">(\1)</sup>', s)
    s = re.sub(r"\[\[UL:([^\]=]+)=(.+?)\]\]", r'<u class="ul">\2</u><sup class="qn">(\1)</sup>', s)
    s = re.sub(r"\[\[BL:([^\]]+)\]\]", r'<span class="bk">(&nbsp;\1&nbsp;)</span>', s)
    return s

def opt_inline(options):
    return "".join(f'<span class="op"><b>{OPT[i]}.</b> {o}</span>' for i, o in enumerate(options))
def opt_block(options, start=0):
    return "".join(f'<div class="opb"><b>{OPT[start+i]}.</b> {o}</div>' for i, o in enumerate(options))

# ---------- 長文 Ⅰ/Ⅱ/Ⅲ ----------
def render_reading(s):
    h = [f'<div class="daimon">大問{s["label"]}　{s.get("lead","")}</div>']
    h.append('<div class="passage">')
    for p in s["paragraphs"]: h.append(f'<p>{rt(p)}</p>')
    h.append('</div>')
    if s.get("glossary"):
        gl = "　".join(f'＊{g["term"]}：{g["gloss_ja"]}' for g in s["glossary"])
        h.append(f'<div class="glossary">（注）{gl}</div>')
    if s.get("source_note"):
        h.append(f'<div class="srcnote">{s["source_note"]}</div>')
    # A
    h.append(f'<div class="qh">問 A　{s.get("A_instruction","")}</div>')
    for it in s["A_items"]:
        h.append(f'<div class="q"><span class="ql">（{it["ref"]}）</span><span class="opts">{opt_inline(it["options"])}</span></div>')
    # B
    h.append(f'<div class="qh">問 B　{s.get("B_instruction","")}</div>')
    for it in s["B_items"]:
        ph = f'<span class="phr">{it["phrase"]}</span>' if it.get("phrase") else ""
        h.append(f'<div class="q qc"><div class="ql">（{it["ref"]}）{ph}</div><div class="opts opts-b">{opt_block(it["options"])}</div></div>')
    # C
    h.append(f'<div class="qh">問 C　{s.get("C_instruction","")}</div>')
    if s.get("C_form") == "multi":
        h.append('<div class="opts opts-b elist">' + opt_block(s["C_multi_options"]) + '</div>')
    else:
        for it in s.get("C_items", []):
            h.append(f'<div class="q qc"><div class="ql">{it["q_label"]} {it["stem"]}</div><div class="opts opts-b">{opt_block(it["options"])}</div></div>')
    return "\n".join(h)

# ---------- Ⅳ 文法語法 ----------
def render_grammar(s):
    h = [f'<div class="daimon">大問{s["label"]}　{s.get("instruction","")}</div>']
    for i, it in enumerate(s["items"], 1):
        h.append(f'<div class="q gramq"><span class="qn2">{i}.</span> {rt(it["sentence"])}<div class="opts opts-b">{opt_block(it["options"])}</div></div>')
    return "\n".join(h)

# ---------- Ⅴ 語句整序 ----------
def render_order(s):
    h = [f'<div class="daimon">大問{s["label"]}　{s.get("instruction","")}</div>']
    for i, it in enumerate(s["items"], 1):
        segs = "　".join(f'<b>{sg["ltr"]}.</b> {sg["text"]}' for sg in it["segments"])
        h.append(f'<div class="q orderq"><div class="ja">{i}.　{it["ja"]}</div>'
                 f'<div class="segs">{segs}</div>'
                 f'<div class="ansslot">2番目（　　）　6番目（　　）</div></div>')
    return "\n".join(h)

# ---------- Ⅵ 会話 ----------
def render_convo(s):
    h = [f'<div class="daimon">大問{s["label"]}　{s.get("instruction","")}</div>']
    if s.get("setting"): h.append(f'<div class="setting">{s["setting"]}</div>')
    h.append('<div class="dialog">')
    for ln in s["lines"]:
        h.append(f'<div class="dl"><span class="sp">{ln["sp"]}:</span> <span class="dt">{rt(ln["text"])}</span></div>')
    h.append('</div>')
    h.append('<div class="qh">選択肢</div>')
    for it in s["items"]:
        h.append(f'<div class="q"><span class="ql">（{it["ref"]}）</span><span class="opts">{opt_inline(it["options"])}</span></div>')
    return "\n".join(h)

# ---------- 解答編 ----------
# 構文欄の記号：{S} {V′} などを下付きの役割記号にする（英語の解答解説_共通作成方針 6・The Rules の凡例＋塾長指定の M）。
# 全角括弧は halt で半角幅に組む（付けないと閉じ括弧の右の空きで、後ろの記号が次の語に付いて見える）。
def _syn(t):
    # いちばん内側の短いまとまり（4語まで。記号ごと）は行の途中で割らない（「［of ／ proof］」のような折り返しを防ぐ）
    def _nw(m):
        return f'\x00{m.group(0)}\x01' if len(m.group(2).split()) <= 4 else m.group(0)
    t = re.sub(r"([〈［（])([^〈〉［］（）{}…]+)([〉］）])(\{[SVOCM]′?\})?", _nw, t)
    # 閉じ括弧と役割記号のあいだでも改行させない（外側・長いまとまりで、記号だけが次の行頭に出るのを防ぐ）
    t = re.sub(r"([〉］）])(\{[SVOCM]′?\})", "\x02\\1\\2\x03", t)
    t = re.sub(r"([〈〉［］（）])", r'<span class="br">\1</span>', t)
    t = re.sub(r"\{([SVOCM]′?)\}", r'<sub class="sv">\1</sub>', t)
    for a, b in (("\x00", '<span class="nw">'), ("\x01", "</span>"), ("\x02", '<span class="nw">'), ("\x03", "</span>")):
        t = t.replace(a, b)
    return t

def _exp_body(idkey):
    x = EXP.get(idkey)
    if not x: return ""
    if isinstance(x, str): return f'<div class="ep"><span class="ec">{x}</span></div>'
    parts = []
    if x.get("quote"):
        qja = f'<span class="qja">（{x["quote_ja"]}）</span>' if x.get("quote_ja") else ""
        parts.append(f'<div class="ep"><span class="pl">該当箇所</span><span class="ec"><span class="quo">{x["quote"]}</span> {qja}</span></div>')
    if x.get("syntax"):
        note = f'<br><span class="synn">{x["syntax_note"]}</span>' if x.get("syntax_note") else ""
        parts.append(f'<div class="ep"><span class="pl sy">構文</span><span class="ec"><span class="syn">{_syn(x["syntax"])}</span>{note}</span></div>')
    if x.get("reason"): parts.append(f'<div class="ep"><span class="pl">考え方</span><span class="ec">{x["reason"]}</span></div>')
    # 整序（大問Ⅴ）には選択肢が無いので、欄の中身（並べ方の注意）に合わせた見出しにする
    dl = "注意点" if idkey.startswith("V_") else "他の選択肢"
    if x.get("distractors"): parts.append(f'<div class="ep"><span class="pl">{dl}</span><span class="ec">{x["distractors"]}</span></div>')
    if x.get("point"): parts.append(f'<div class="ep ept"><span class="pl pt">ポイント</span><span class="ec">{x["point"]}</span></div>')
    return "".join(parts)

def _ans_reading(s):
    rows = []
    a = "　".join(f'（{it["ref"]}）<b>{OPT[it["ans"]-1]}</b>' for it in s["A_items"])
    rows.append(f'<div class="arow"><span class="al">A</span>{a}</div>')
    b = "　".join(f'（{it["ref"]}）<b>{OPT[it["ans"]-1]}</b>' for it in s["B_items"])
    rows.append(f'<div class="arow"><span class="al">B</span>{b}</div>')
    if s.get("C_form") == "multi":
        cc = "・".join(f'<b>{OPT[i-1]}</b>' for i in s["C_multi_answers"])
        rows.append(f'<div class="arow"><span class="al">C</span>合致する2つ：{cc}</div>')
    else:
        cc = "　".join(f'{it["q_label"]}<b>{OPT[it["ans"]-1]}</b>' for it in s["C_items"])
        rows.append(f'<div class="arow"><span class="al">C</span>{cc}</div>')
    return f'<div class="qsec-title">大問{s["label"]}　解答</div>' + "".join(rows)

def _ans_simple(s, letter=True):
    cells = "　".join(f'{i}.<b>{OPT[it["ans"]-1]}</b>' for i, it in enumerate(s["items"], 1))
    return f'<div class="qsec-title">大問{s["label"]}　解答</div><div class="arow">{cells}</div>'

def _ans_order(s):
    cells = "　".join(f'<span class="ac">{i}.(2番目<b>{it["ans2"]}</b>/6番目<b>{it["ans6"]}</b>)</span>' for i, it in enumerate(s["items"], 1))
    return f'<div class="qsec-title">大問{s["label"]}　解答</div><div class="arow">{cells}</div>'

def _exp_block(header, idkey):
    eb = _exp_body(idkey)
    if not eb:
        return f'<div class="exp"><div class="exp-head">{header}</div><div class="ep"><span class="ec" style="color:#999">（解説準備中）</span></div></div>'
    return f'<div class="exp"><div class="exp-head">{header}</div>{eb}</div>'

def render_explanations():
    out = ['<div class="qsec-title">解説</div>',
           '<div class="synlegend"><div class="lg1">構文欄の記号：〈 〉名詞のまとまり　［ ］形容詞のまとまり（名詞にかかる）　（ ）副詞のまとまり　'
           '<span class="svl">S・V・O・C</span>＝文の骨組み　<span class="svl">S′・V′・O′・C′</span>＝節・準動詞の中の骨組み　'
           '<span class="svl">M</span>＝修飾語（<span class="svl">M′</span>は節・準動詞の中）　「…」＝本文の省略</div><ul>'
           '<li>副詞のまとまりは1語でも（ ）。1語の名詞・代名詞と、補語になる形容詞・分詞のまとまりには括弧を付けず、中心の語に記号を添える。</li>'
           '<li>動詞・形容詞と組で使う前置詞のまとまり（rely on・result in・prevent O from・ask O for・be used to・be different from など）も（ ）<span class="svl">M</span> で示す'
           '（動詞・形容詞の補部と見て O・C の側に含める説明もある）。</li>'
           '<li>関係詞（that・what・where など）は括弧を付けず、節の中の働き（S′・O′・M′）だけを添える。'
           '否定の not・never と、強調構文の It is … that には記号を付けない。</li>'
           '<li>節・準動詞の中の記号と細かい修飾語の括弧・記号は、説明に要る所だけ付ける。節の中の節も S′・V′ などで示す。</li>'
           '<li>カンマで区切られた説明の修飾は、名詞のまとまりの外に置く。</li></ul></div>']
    for K in ("I","II","III"):
        s = CONTENT.get(K)
        if not s: continue
        out.append(f'<div class="daimon">大問{s["label"]}　解説</div>')
        for it in s["A_items"]:
            out.append(_exp_block(f'問A（{it["ref"]}）　正解 {OPT[it["ans"]-1]}', f'{K}_A_{it["ref"]}'))
        for it in s["B_items"]:
            out.append(_exp_block(f'問B（{it["ref"]}）　正解 {OPT[it["ans"]-1]}', f'{K}_B_{it["ref"]}'))
        if s.get("C_form") == "multi":
            av = "・".join(OPT[i-1] for i in s["C_multi_answers"])
            out.append(_exp_block(f'問C（内容一致・2つ選ぶ）　正解 {av}', f'{K}_C'))
        else:
            for it in s["C_items"]:
                out.append(_exp_block(f'問C {it["q_label"]}　正解 {OPT[it["ans"]-1]}', f'{K}_C_{it["q_label"].strip("()")}'))
    if CONTENT.get("IV"):
        out.append('<div class="daimon">大問Ⅳ　解説</div>')
        for i, it in enumerate(CONTENT["IV"]["items"], 1):
            out.append(_exp_block(f'{i}.　正解 {OPT[it["ans"]-1]}', f'IV_{i}'))
    if CONTENT.get("V"):
        out.append('<div class="daimon">大問Ⅴ　解説</div>')
        for i, it in enumerate(CONTENT["V"]["items"], 1):
            out.append(_exp_block(f'{i}.　正解 2番目={it["ans2"]}／6番目={it["ans6"]}　（{it.get("full_en","")}）', f'V_{i}'))
    if CONTENT.get("VI"):
        out.append('<div class="daimon">大問Ⅵ　解説</div>')
        for it in CONTENT["VI"]["items"]:
            out.append(_exp_block(f'（{it["ref"]}）　正解 {OPT[it["ans"]-1]}', f'VI_{it["ref"]}'))
    return "\n".join(out)

# ---------- CSS ----------
CSS = """
@page { size: A4; margin: 16mm 14mm; }
* { box-sizing: border-box; }
body { font-family:'Times New Roman','Hiragino Mincho ProN','Yu Mincho',serif; color:#000; font-size:10.3pt; line-height:1.8; }
.exam-head { text-align:center; border-bottom:2.5px solid #000; padding-bottom:6px; margin-bottom:10px; }
.exam-head .t1 { font-size:15pt; font-weight:bold; letter-spacing:2px; }
.exam-head .t2 { font-size:9.5pt; margin-top:3px; }
.daimon { font-size:12pt; font-weight:bold; border-left:6px solid #000; padding-left:8px; margin:15px 0 7px; break-after:avoid; }
.passage p { margin:0 0 6px; text-align:justify; }
u.ul { text-decoration:underline; text-underline-offset:2px; }
u.dbl { text-decoration:underline; text-decoration-style:double; text-underline-offset:2px; }
sup.qn { font-weight:bold; font-size:7.6pt; }
.bk { font-weight:bold; white-space:nowrap; }
.glossary { font-family:'Hiragino Mincho ProN',serif; font-size:8.6pt; color:#222; background:#f5f5f0; border:1px solid #bbb; padding:5px 8px; margin:7px 0 3px; line-height:1.55; }
.srcnote { font-size:8.2pt; color:#444; margin:3px 0; text-align:right; }
.qh { font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:9.8pt; font-weight:bold; margin:11px 0 4px; background:#eee; padding:3px 7px; border-left:3px solid #555; }
.q { margin:2px 0 3px; font-size:9.8pt; line-height:1.55; }
.q .ql { font-weight:bold; margin-right:6px; font-family:'Hiragino Mincho ProN',serif; }
.q .opts .op { display:inline-block; margin:0 11px 1px 0; }
.qc { break-inside:avoid; }   /* 設問の札と選択肢をページで分けない */
.qc .ql { display:block; margin-bottom:2px; }
.qc .phr { font-family:'Times New Roman',serif; font-style:italic; }
.opts-b .opb { display:block; margin:1px 0 1px 1.5em; text-indent:-1.5em; }
.elist .opb { font-family:'Hiragino Mincho ProN','Times New Roman',serif; }
.gramq { margin:5px 0; page-break-inside:avoid; }
.gramq .qn2 { font-weight:bold; }
.orderq { margin:7px 0; page-break-inside:avoid; }
.orderq .ja { font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:9.8pt; }
.orderq .segs { margin:2px 0 2px 1em; font-size:9.6pt; line-height:1.7; }
.orderq .ansslot { margin-left:1em; font-family:'Hiragino Mincho ProN',serif; font-size:9.4pt; }
.setting { font-family:'Hiragino Mincho ProN',serif; font-size:9.2pt; background:#f5f5f0; border:1px solid #bbb; padding:5px 9px; margin:5px 0; }
.dialog { margin:5px 0; }
.dl { margin:3px 0; text-indent:-2.4em; padding-left:2.4em; }
.dl .sp { font-weight:bold; }
/* 解答編 */
.qsec-title { font-size:11pt; font-weight:bold; margin:13px 0 5px; border-bottom:1.5px solid #000; padding-bottom:2px; break-after:avoid; }
.arow { display:flex; flex-wrap:wrap; align-items:baseline; gap:4px 10px; margin:4px 0; font-size:9.8pt; font-family:'Hiragino Mincho ProN','Times New Roman',serif; break-inside:avoid; }
.arow .ac { white-space:nowrap; }
.arow .al { flex:0 0 1.5em; font-weight:bold; background:#333; color:#fff; text-align:center; border-radius:2px; }
.overview { font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:9.6pt; line-height:1.72; background:#f6f6f2; border-left:4px solid #444; padding:8px 12px; margin:4px 0 12px; text-align:justify; }
/* 1問分（.exp）は割ってよい。割らないのは欄（.ep）の中だけ。構文欄を足してから .exp ごと送ると、ページ下が2〜3割空いた（20p） */
.exp { margin:6px 0 10px; font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:9.2pt; line-height:1.58; }
.exp-head { font-weight:bold; font-size:9.8pt; border-bottom:1px solid #bbb; padding-bottom:1px; margin-bottom:3px; break-inside:avoid; break-after:avoid; }
.ep { display:flex; gap:7px; margin:2.5px 0; line-height:1.62; break-inside:avoid; }
.ep .pl { flex:0 0 5.6em; align-self:flex-start; font-weight:bold; color:#fff; background:#555; text-align:center; padding:0.8px 0; border-radius:2px; font-size:7.8pt; white-space:nowrap; }
.ep .pl.pt { background:#8a6d1a; }
.ept { break-before:avoid; }
.ep .pl.sy { background:#2f5d7c; }
.syn { font-family:'Times New Roman','Hiragino Mincho ProN',serif; font-size:9.4pt; line-height:1.9; }
.syn sub.sv { font-family:Arial,'Hiragino Sans',sans-serif; font-weight:bold; font-size:6.6pt; vertical-align:-0.35em; margin:0 1px 0 0.5px; color:#1d4f73; }
.syn .br { font-feature-settings:"halt"; }
.syn .nw { white-space:nowrap; }
.synn { font-size:8.8pt; color:#222; }
.synlegend { font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:8.6pt; line-height:1.6; border:1px solid #bbb; background:#f6f8fa; padding:4px 8px; margin:4px 0 8px; }
.synlegend .svl { font-family:Arial,'Hiragino Sans',sans-serif; font-weight:bold; font-size:7.8pt; color:#1d4f73; }
.synlegend ul { margin:2px 0 0; padding-left:1.3em; }
.synlegend li { margin:0; }
.ep .ec { flex:1; }
.ep .quo { font-family:'Times New Roman',serif; }
.ep .qja { color:#333; }
"""

def page(body):
    return f"<!doctype html><html lang='ja'><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"

def build_problem():
    head = ('<div class="exam-head"><div class="t1">関西学院大学 2026 英語 実戦問題</div>'
            '<div class="t2">A日程／全6問（Ⅰ〜Ⅲ 長文・Ⅳ 文法語法・Ⅴ 語句整序・Ⅵ 会話文）／試験時間 90分／全問マーク式</div></div>')
    body = [head]
    for K, fn in [("I",render_reading),("II",render_reading),("III",render_reading),
                  ("IV",render_grammar),("V",render_order),("VI",render_convo)]:
        if CONTENT.get(K): body.append(fn(CONTENT[K]))
    return page("\n".join(body))

def build_answer():
    head = ('<div class="exam-head"><div class="t1">関西学院大学 2026 英語 実戦問題 &mdash; 解答編</div>'
            '<div class="t2">解答・解説</div></div>')
    body = [head]
    if OVERVIEW:
        body.append('<div class="qsec-title">この試験の解き方・攻略の視点</div>'
                    f'<div class="overview">{OVERVIEW}</div>')
    for K in ("I","II","III"):
        if CONTENT.get(K): body.append(_ans_reading(CONTENT[K]))
    if CONTENT.get("IV"): body.append(_ans_simple(CONTENT["IV"]))
    if CONTENT.get("V"): body.append(_ans_order(CONTENT["V"]))
    if CONTENT.get("VI"): body.append(_ans_simple(CONTENT["VI"]))
    if EXP: body.append(render_explanations())
    return page("\n".join(body))

def render_pdf(html, name):
    hp = os.path.join(HERE, f"_{name}.html")
    open(hp, "w", encoding="utf-8").write(html)
    pdf = os.path.join(OUT, f"{name}.pdf")
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", "file://" + hp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", pdf)

if __name__ == "__main__":
    render_pdf(build_problem(), "関学2026英語実戦問題_問題編")
    render_pdf(build_answer(),  "関学2026英語実戦問題_解答編")
    print("OUT:", OUT)
