# -*- coding: utf-8 -*-
"""
青山学院大学2026 英語 実戦問題ビルダ（個別学部日程系・マーク＋記述 併用）
- 実物構成: 問題Ⅰ長文(英問英答4択×10・本文にマーカー無し) + Ⅱ和訳(下線2文・記述) + Ⅲ英作文(50語・Ⅱに連動) + Ⅳ短文/会話空所補充(4択×5)。
- 本文は著作権配慮で完全オリジナル。米式綴り・番号付き脚注。
- content.json = {"I":..,"II":..,"III":..,"IV":..} を単一ソース。
- 解説は explanations_seki.json({id:{quote,quote_ja,reason,distractors,point}})＋overview_seki.txt を任意注入。
"""
import os, re, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
def find_chrome():
    """刷るためのブラウザを探す。Mac / Linux / Playwright 同梱のどれでも動くように。"""
    import shutil
    for c in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(c)
        if p:
            return p
    direct = "/opt/pw-browsers/chromium"
    if os.path.exists(direct):
        return direct
    root = "/opt/pw-browsers"
    if os.path.isdir(root):
        for d in sorted(os.listdir(root), reverse=True):
            p = os.path.join(root, d, "chrome-linux", "chrome")
            if os.path.exists(p):
                return p
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    return mac if os.path.exists(mac) else None


# ★ 出力先。Mac のデスクトップ決め打ちだと Linux (CI / セッション) で刷れない。
OUT = os.environ.get("AOYAMA_OUT") or os.path.expanduser(
    "~/Desktop/青山学院大学2026_英語実戦問題")
os.makedirs(OUT, exist_ok=True)
MARU = ["①","②","③","④","⑤"]
SUP = {"1":"¹","2":"²","3":"³","4":"⁴","5":"⁵","6":"⁶","7":"⁷","8":"⁸","9":"⁹","10":"¹⁰","11":"¹¹"}

CONTENT = {}
_c = os.path.join(HERE, "content.json")
if os.path.exists(_c): CONTENT = json.load(open(_c, encoding="utf-8"))
EXP = {}; OVERVIEW = ""
_e = os.path.join(HERE, "explanations_seki.json")
if os.path.exists(_e): EXP = json.load(open(_e, encoding="utf-8"))
_o = os.path.join(HERE, "overview_seki.txt")
if os.path.exists(_o): OVERVIEW = open(_o, encoding="utf-8").read().strip()

def _sup(n): return SUP.get(str(n), f"({n})")
def rt(s):
    s = re.sub(r"\[\[UL:([^\]=]+)=(.+?)\]\]", r'<u class="ul">\2</u><sup class="qn">(\1)</sup>', s)
    s = re.sub(r"\[\[FN:([^\]]+)\]\]", lambda m: f'<sup class="fn">{_sup(m.group(1))}</sup>', s)
    s = re.sub(r"\[\[BL:([^\]]+)\]\]", r'<span class="bk">(&nbsp;\1&nbsp;)</span>', s)
    return s
def opt_block(options):
    return "".join(f'<div class="opb">{MARU[i]} {o}</div>' for i, o in enumerate(options))
def opt_inline(options):
    return "".join(f'<span class="op">{MARU[i]} {o}</span>' for i, o in enumerate(options))

# ---------- 問題Ⅰ 長文(内容一致) ----------
def render_reading(s):
    h = [f'<div class="daimon">問題{s["label"]}　{s.get("lead","")}</div>']
    h.append('<div class="passage">')
    for p in s["paragraphs"]: h.append(f'<p>{rt(p)}</p>')
    h.append('</div>')
    if s.get("glossary"):
        gl = "　".join(f'{g["n"]}. {g["term"]}：{g["gloss_ja"]}' for g in sorted(s["glossary"], key=lambda x:x["n"]))
        h.append(f'<div class="glossary">（注）{gl}</div>')
    if s.get("source_note"): h.append(f'<div class="srcnote">{s["source_note"]}</div>')
    h.append('<div class="qh">設問　次の各問について、最も適切なものを①〜④から一つ選び、その番号をマークしなさい。</div>')
    for i, q in enumerate(s["questions"], 1):
        h.append(f'<div class="q qc"><div class="ql">問{i}（解答欄 {i}）　{q["stem"]}</div>'
                 f'<div class="opts opts-b">{opt_block(q["options"])}</div></div>')
    return "\n".join(h)

# ---------- 問題Ⅱ 和訳 ----------
def render_trans(s):
    h = [f'<div class="daimon">問題{s["label"]}　{s.get("lead","")}</div>']
    h.append('<div class="passage">')
    for p in s["paragraphs"]: h.append(f'<p>{rt(p)}</p>')
    h.append('</div>')
    if s.get("glossary"):
        gl = "　".join(f'{g["term"]}：{g["gloss_ja"]}' for g in s["glossary"])
        h.append(f'<div class="glossary">（注）{gl}</div>')
    h.append('<div class="qh">下線部（1）・（2）を、それぞれ日本語に訳しなさい。（記述）</div>')
    return "\n".join(h)

# ---------- 問題Ⅲ 英作文 ----------
def render_essay(s):
    h = [f'<div class="daimon">問題{s["label"]}　英作文（記述）</div>']
    h.append(f'<div class="prompt">{s["prompt"]}</div>')
    h.append('<div class="qh">上の問いに対するあなたの意見を、およそ50語程度の英語で書きなさい。</div>')
    return "\n".join(h)

# ---------- 問題Ⅳ 空所補充 ----------
def render_gram(s):
    h = [f'<div class="daimon">問題{s["label"]}　{s.get("lead","")}</div>']
    for it in s["items"]:
        n = it["n"]
        if it["type"] == "dialog":
            body = "".join(f'<div class="dl"><span class="sp">{ln["sp"]}:</span> {rt(ln["text"])}</div>' for ln in it["lines"])
        else:
            body = " ".join(rt(ln["text"]) for ln in it["lines"])
        h.append(f'<div class="q qc"><div class="ql">問{n}（解答欄 {n}）</div>'
                 f'<div class="qbody">{body}</div>'
                 f'<div class="opts">{opt_inline(it["options"])}</div></div>')
    return "\n".join(h)

# ---------- 解答編 ----------
def _exp_body(idkey):
    x = EXP.get(idkey)
    if not x: return ""
    if isinstance(x, str): return f'<div class="ep"><span class="ec">{x}</span></div>'
    parts = []
    if x.get("quote"):
        qja = f'<span class="qja">（{x["quote_ja"]}）</span>' if x.get("quote_ja") else ""
        parts.append(f'<div class="ep"><span class="pl">該当箇所</span><span class="ec"><span class="quo">{x["quote"]}</span> {qja}</span></div>')
    if x.get("reason"): parts.append(f'<div class="ep"><span class="pl">考え方</span><span class="ec">{x["reason"]}</span></div>')
    if x.get("distractors"): parts.append(f'<div class="ep"><span class="pl">他の選択肢</span><span class="ec">{x["distractors"]}</span></div>')
    if x.get("point"): parts.append(f'<div class="ep"><span class="pl pt">ポイント</span><span class="ec">{x["point"]}</span></div>')
    return "".join(parts)
def _exp_block(header, idkey):
    eb = _exp_body(idkey)
    if not eb:
        return f'<div class="exp"><div class="exp-head">{header}</div><div class="ep"><span class="ec" style="color:#999">（解説準備中）</span></div></div>'
    return f'<div class="exp"><div class="exp-head">{header}</div>{eb}</div>'

def build_problem():
    head = ('<div class="exam-head"><div class="t1">青山学院大学 2026 英語 実戦問題</div>'
            '<div class="t2">個別学部日程 系／問題Ⅰ〜Ⅳ（Ⅰ 長文・Ⅱ 和訳・Ⅲ 英作文・Ⅳ 語彙）／マーク＋記述 併用</div></div>')
    body = [head]
    if CONTENT.get("I"): body.append(render_reading(CONTENT["I"]))
    if CONTENT.get("II"): body.append(render_trans(CONTENT["II"]))
    if CONTENT.get("III"): body.append(render_essay(CONTENT["III"]))
    if CONTENT.get("IV"): body.append(render_gram(CONTENT["IV"]))
    return page("\n".join(body))

def build_answer():
    head = ('<div class="exam-head"><div class="t1">青山学院大学 2026 英語 実戦問題 &mdash; 解答編</div>'
            '<div class="t2">解答・解説</div></div>')
    body = [head]
    if OVERVIEW:
        body.append('<div class="qsec-title">この試験の解き方・攻略の視点</div>'
                    f'<div class="overview">{OVERVIEW}</div>')
    # 解答一覧
    if CONTENT.get("I"):
        cells = "　".join(f'{i}.<b>{MARU[q["ans"]-1]}</b>' for i, q in enumerate(CONTENT["I"]["questions"], 1))
        body.append(f'<div class="qsec-title">問題Ⅰ　解答（マーク）</div><div class="arow">{cells}</div>')
    if CONTENT.get("IV"):
        cells = "　".join(f'{it["n"]}.<b>{MARU[it["ans"]-1]}</b>' for it in CONTENT["IV"]["items"])
        body.append(f'<div class="qsec-title">問題Ⅳ　解答（マーク）</div><div class="arow">{cells}</div>')
    # 記述の模範解答
    if CONTENT.get("II"):
        rows = "".join(f'<div class="modelans"><b>下線部（{it["ref"]}）解答例:</b> {it["model_ja"]}</div>' for it in CONTENT["II"]["items"])
        body.append(f'<div class="qsec-title">問題Ⅱ　和訳 解答例</div>{rows}')
    if CONTENT.get("III"):
        s = CONTENT["III"]
        body.append(f'<div class="qsec-title">問題Ⅲ　英作文 解答例</div>'
                    f'<div class="modelans">{s["model_en"]}</div>'
                    f'<div class="exp"><div class="ep"><span class="pl">採点の視点</span><span class="ec">{s.get("note","")}</span></div></div>')
    # 解説
    if EXP:
        out = ['<div class="qsec-title">解説</div>']
        if CONTENT.get("I"):
            out.append('<div class="daimon">問題Ⅰ　解説</div>')
            for i, q in enumerate(CONTENT["I"]["questions"], 1):
                out.append(_exp_block(f'問{i}　正解 {MARU[q["ans"]-1]}', f'I_{i}'))
        if CONTENT.get("II"):
            out.append('<div class="daimon">問題Ⅱ（和訳）　解説</div>')
            for it in CONTENT["II"]["items"]:
                out.append(_exp_block(f'下線部（{it["ref"]}）', f'II_{it["ref"]}'))
        if CONTENT.get("IV"):
            out.append('<div class="daimon">問題Ⅳ　解説</div>')
            for it in CONTENT["IV"]["items"]:
                out.append(_exp_block(f'問{it["n"]}　正解 {MARU[it["ans"]-1]}', f'IV_{it["n"]}'))
        body.append("\n".join(out))
    return page("\n".join(body))

CSS = """
@page { size: A4; margin: 16mm 15mm; }
* { box-sizing: border-box; }
body { font-family:'Times New Roman','Hiragino Mincho ProN','Yu Mincho',serif; color:#000; font-size:10.5pt; line-height:1.8; }
.exam-head { text-align:center; border-bottom:2.5px solid #000; padding-bottom:6px; margin-bottom:10px; }
.exam-head .t1 { font-size:15pt; font-weight:bold; letter-spacing:2px; }
.exam-head .t2 { font-size:9.5pt; margin-top:3px; }
.daimon { font-size:12pt; font-weight:bold; border-left:6px solid #000; padding-left:8px; margin:15px 0 7px; }
.passage p { margin:0 0 6px; text-align:justify; }
u.ul { text-decoration:underline; text-underline-offset:2px; }
sup.qn { font-weight:bold; font-size:8pt; }
sup.fn { font-weight:bold; font-size:8pt; color:#333; }
.bk { font-weight:bold; white-space:nowrap; }
.glossary { font-family:'Hiragino Mincho ProN',serif; font-size:8.6pt; color:#222; background:#f5f5f0; border:1px solid #bbb; padding:5px 8px; margin:7px 0 3px; line-height:1.55; }
.srcnote { font-size:8.2pt; color:#444; margin:3px 0; text-align:right; font-style:italic; }
.qh { font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:9.8pt; font-weight:bold; margin:11px 0 5px; background:#eee; padding:3px 7px; border-left:3px solid #555; }
.q { margin:3px 0 6px; font-size:10pt; line-height:1.55; page-break-inside:avoid; }
.qc .ql { display:block; font-weight:bold; margin-bottom:2px; font-family:'Times New Roman','Hiragino Mincho ProN',serif; }
.qbody { margin:1px 0 3px 0.5em; }
.dl { margin:1px 0; text-indent:-1.6em; padding-left:1.6em; }
.dl .sp { font-weight:bold; }
.opts .op { display:inline-block; margin:0 12px 1px 0; }
.opts-b .opb { display:block; margin:1px 0 1px 1.5em; text-indent:-1.5em; }
.prompt { font-family:'Times New Roman',serif; font-size:10.5pt; background:#f5f5f0; border:1px solid #bbb; padding:6px 10px; margin:4px 0; }
/* 解答編 */
.qsec-title { font-size:11pt; font-weight:bold; margin:13px 0 5px; border-bottom:1.5px solid #000; padding-bottom:2px; }
.arow { display:flex; flex-wrap:wrap; gap:4px 12px; margin:4px 0; font-size:10pt; font-family:'Hiragino Mincho ProN','Times New Roman',serif; }
.modelans { font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:9.8pt; margin:4px 0; line-height:1.7; }
.overview { font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:9.6pt; line-height:1.72; background:#f6f6f2; border-left:4px solid #444; padding:8px 12px; margin:4px 0 12px; text-align:justify; }
.exp { margin:6px 0 10px; font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:9.2pt; line-height:1.58; }
.exp-head { font-weight:bold; font-size:9.8pt; border-bottom:1px solid #bbb; padding-bottom:1px; margin-bottom:3px; break-inside:avoid; }
.ep { display:flex; gap:7px; margin:2.5px 0; line-height:1.62; break-inside:avoid; }
.ep .pl { flex:0 0 5.6em; align-self:flex-start; font-weight:bold; color:#fff; background:#555; text-align:center; padding:0.8px 0; border-radius:2px; font-size:7.8pt; white-space:nowrap; }
.ep .pl.pt { background:#8a6d1a; }
.ep .ec { flex:1; }
.ep .quo { font-family:'Times New Roman',serif; }
.ep .qja { color:#333; }
"""
def page(body):
    return f"<!doctype html><html lang='ja'><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"

def render_pdf(html, name):
    hp = os.path.join(HERE, f"_{name}.html")
    open(hp, "w", encoding="utf-8").write(html)
    pdf = os.path.join(OUT, f"{name}.pdf")
    chrome = find_chrome()
    if not chrome:
        raise SystemExit("✗ Chrome / Chromium が見つからない。PDF を刷れない。")
    # ★ --no-sandbox: root で回る環境 (CI / セッション) では付けないと起動できない
    subprocess.run([chrome, "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", "file://" + hp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", pdf)

if __name__ == "__main__":
    render_pdf(build_problem(), "青学2026英語実戦問題_問題編")
    render_pdf(build_answer(),  "青学2026英語実戦問題_解答編")
    print("OUT:", OUT)
