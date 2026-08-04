# -*- coding: utf-8 -*-
"""
同志社大学2026 英語 実戦問題ビルダ（3大問: 長文Ⅰ/Ⅱ + 会話Ⅲ）
- 実物構成: Ⅰ長文(83点)/Ⅱ長文(67点)/Ⅲ会話(50点)=200点・想定100分。
- 本文は著作権配慮で完全オリジナル。米式綴り・語注(＊)付き。
- content.json = {"I":{...},"II":{...},"III":{...}} を単一ソースに読み込み。
- 解説は explanations_seki.json（{id: {quote,quote_ja,reason,distractors,point}}）＋overview_seki.txt を任意注入。
- 出力: 問題編/解答編HTML -> Chrome --print-to-pdf。
"""
import os, re, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.expanduser("~/Desktop/同志社大学2026_英語実戦問題")
os.makedirs(OUT, exist_ok=True)
MARU = ["①","②","③","④","⑤","⑥","⑦","⑧","⑨","⑩"]

CONTENT = {}
_cpath = os.path.join(HERE, "content.json")
if os.path.exists(_cpath):
    CONTENT = json.load(open(_cpath, encoding="utf-8"))

# 解説（任意）
EXP = {}
OVERVIEW = ""
_epath = os.path.join(HERE, "explanations_seki.json")
if os.path.exists(_epath):
    EXP = json.load(open(_epath, encoding="utf-8"))
_opath = os.path.join(HERE, "overview_seki.txt")
if os.path.exists(_opath):
    OVERVIEW = open(_opath, encoding="utf-8").read().strip()

# ============================================================
# 本文トークン → HTML
# ============================================================
def render_tokens(s):
    # F: 和訳対象（太下線）
    s = re.sub(r"\[\[F=(.+?)\]\]", r'<u class="ful"><b>\1</b></u>', s)
    # B: 同義語下線（一語）
    s = re.sub(r"\[\[B:([^\]=]+)=(.+?)\]\]", r'<u class="ul">\2</u><sup class="qn">(\1)</sup>', s)
    # C: 波線（句・節）
    s = re.sub(r"\[\[C:([^\]=]+)=(.+?)\]\]", r'<u class="wv">\2</u><sup class="qn">(\1)</sup>', s)
    # A / D / K: 空所ボックス
    s = re.sub(r"\[\[A:([^\]]+)\]\]", r'<span class="bk">(&nbsp;\1&nbsp;)</span>', s)
    s = re.sub(r"\[\[D:([^\]]+)\]\]", r'<span class="bk">(&nbsp;\1&nbsp;)</span>', s)
    s = re.sub(r"\[\[K:([^\]]+)\]\]", r'<span class="bk">(&nbsp;\1&nbsp;)</span>', s)
    return s

def opts_inline(options, n=None):
    return "".join(f'<span class="op">{MARU[i]} {o}</span>' for i, o in enumerate(options))

def opts_block(options):
    return "".join(f'<div class="opb">{MARU[i]} {o}</div>' for i, o in enumerate(options))

# ============================================================
# 大問（長文 Ⅰ/Ⅱ）本文＋設問
# ============================================================
def render_reading(sec):
    h = []
    h.append(f'<div class="daimon">{sec["label"]}（配点 {sec["points"]}）　{sec.get("lead","")}</div>')
    # 本文
    h.append('<div class="passage">')
    for p in sec["paragraphs"]:
        h.append(f'<p>{render_tokens(p)}</p>')
    h.append('</div>')
    # 語注
    if sec.get("glossary"):
        gl = "　".join(f'＊{g["term"]}：{g["gloss_ja"]}' for g in sec["glossary"])
        h.append(f'<div class="glossary">（注）{gl}</div>')
    if sec.get("source_note"):
        h.append(f'<div class="srcnote">{sec["source_note"]}</div>')
    # 設問A 空所補充
    if sec.get("A_items"):
        h.append(f'<div class="qh">問 A　{sec.get("A_instruction","")}</div>')
        for it in sec["A_items"]:
            h.append(f'<div class="q"><span class="ql">（{it["slot"]}）</span>'
                     f'<span class="opts">{opts_inline(it["options"])}</span></div>')
    # 設問B 同義語
    if sec.get("B_items"):
        h.append(f'<div class="qh">問 B　{sec.get("B_instruction","")}</div>')
        for it in sec["B_items"]:
            h.append(f'<div class="q"><span class="ql">（{it["label"]}）{it["word"]}</span>'
                     f'<span class="opts">{opts_inline(it["options"])}</span></div>')
    # 設問C 波線言い換え
    if sec.get("C_items"):
        h.append(f'<div class="qh">問 C　{sec.get("C_instruction","")}</div>')
        for it in sec["C_items"]:
            h.append(f'<div class="q qc"><div class="ql">（{it["label"]}）<span class="phr">{it["phrase"]}</span></div>'
                     f'<div class="opts opts-b">{opts_block(it["options"])}</div></div>')
    # 設問D 整序
    if sec.get("D_bank"):
        bank = "　".join(f'{i+1} {w}' for i, w in enumerate(sec["D_bank"]))
        aslots = "・".join(f'（{s}）' for s in sec["D_answer_slots"])
        h.append(f'<div class="qh">問 D　{sec.get("D_instruction","")}</div>')
        h.append(f'<div class="dbank"><b>［語群］</b> {bank}</div>')
        h.append(f'<div class="dnote">※ 解答するのは {aslots} に入る語の番号。同じ語は2度使えず、使わない語もある。</div>')
    # 設問E 内容一致
    if sec.get("E_options"):
        h.append(f'<div class="qh">問 E　{sec.get("E_instruction","")}</div>')
        h.append('<div class="opts opts-b elist">' + opts_block(sec["E_options"]) + '</div>')
    # 設問F 和訳
    if sec.get("F_target_en"):
        h.append(f'<div class="qh">問 F　本文中の太い下線部を日本語に訳しなさい。</div>')
    return "\n".join(h)

# ============================================================
# 大問Ⅲ（会話）
# ============================================================
def render_convo(sec):
    h = []
    h.append(f'<div class="daimon">{sec["label"]}（配点 {sec["points"]}）　{sec.get("lead","")}</div>')
    if sec.get("setting"):
        h.append(f'<div class="setting">{sec["setting"]}</div>')
    h.append('<div class="dialog">')
    for ln in sec["lines"]:
        h.append(f'<div class="dl"><span class="sp">{ln["sp"]}:</span> '
                 f'<span class="dt">{render_tokens(ln["text"])}</span></div>')
    h.append('</div>')
    # A 応答補充
    h.append(f'<div class="qh">問 A　{sec.get("A_instruction","")}</div>')
    h.append('<div class="opts opts-b">' + opts_block(sec["A_options"]) + '</div>')
    # B 英訳
    if sec.get("B_ja"):
        h.append(f'<div class="qh">問 B　次の日本語を英語に訳しなさい。</div>'
                 f'<div class="bja">「{sec["B_ja"]}」</div>')
    return "\n".join(h)

# ============================================================
# 解答編：解答一覧＋解説
# ============================================================
def _slot_ans(sec_key, sub, slot, idx):
    """id 生成用"""
    return f'{sec_key}_{sub}_{slot}'

def answer_list_reading(sec, key):
    rows = []
    if sec.get("A_items"):
        cells = "".join(f'<span class="ac">（{it["slot"]}）<b>{MARU[it["ans"]-1]}</b></span>' for it in sec["A_items"])
        rows.append(f'<div class="arow"><span class="al">A</span>{cells}</div>')
    if sec.get("B_items"):
        cells = "".join(f'<span class="ac">（{it["label"]}）<b>{MARU[it["ans"]-1]}</b></span>' for it in sec["B_items"])
        rows.append(f'<div class="arow"><span class="al">B</span>{cells}</div>')
    if sec.get("C_items"):
        cells = "".join(f'<span class="ac">（{it["label"]}）<b>{MARU[it["ans"]-1]}</b></span>' for it in sec["C_items"])
        rows.append(f'<div class="arow"><span class="al">C</span>{cells}</div>')
    if sec.get("D_answer_slots"):
        m = {x["slot"]: x["idx"] for x in sec["D_slot_map"]}
        cells = "".join(f'<span class="ac">（{s}）<b>{m.get(s,"?")}</b></span>' for s in sec["D_answer_slots"])
        rows.append(f'<div class="arow"><span class="al">D</span>{cells}</div>')
    if sec.get("E_answers"):
        cells = "".join(f'<span class="ac"><b>{MARU[i-1]}</b></span>' for i in sec["E_answers"])
        rows.append(f'<div class="arow"><span class="al">E</span><span class="ac">合致する3つ：</span>{cells}</div>')
    if sec.get("F_model_ja"):
        rows.append(f'<div class="arow"><span class="al">F</span><span class="ac">{sec["F_model_ja"]}</span></div>')
    return f'<div class="qsec-title">{sec["label"]}　解答</div>' + "".join(rows)

def answer_list_convo(sec, key):
    m = {x["slot"]: x["idx"] for x in sec["A_slot_map"]}
    cells = "".join(f'<span class="ac">（{s}）<b>{m.get(s,"?")}</b></span>' for s in sec["A_slots"])
    rows = [f'<div class="arow"><span class="al">A</span>{cells}</div>']
    if sec.get("B_model_en"):
        rows.append(f'<div class="arow"><span class="al">B</span><span class="ac">{sec["B_model_en"]}</span></div>')
    return f'<div class="qsec-title">{sec["label"]}　解答</div>' + "".join(rows)

def _exp_body(idkey):
    s = EXP.get(idkey)
    if not s:
        return ""
    if isinstance(s, str):
        return f'<div class="ep"><span class="ec">{s}</span></div>'
    parts = []
    if s.get("quote"):
        qja = f'<span class="qja">（{s["quote_ja"]}）</span>' if s.get("quote_ja") else ""
        parts.append(f'<div class="ep"><span class="pl">該当箇所</span><span class="ec"><span class="quo">{s["quote"]}</span> {qja}</span></div>')
    if s.get("reason"):
        parts.append(f'<div class="ep"><span class="pl">考え方</span><span class="ec">{s["reason"]}</span></div>')
    if s.get("distractors"):
        parts.append(f'<div class="ep"><span class="pl">他の選択肢</span><span class="ec">{s["distractors"]}</span></div>')
    if s.get("point"):
        parts.append(f'<div class="ep"><span class="pl pt">ポイント</span><span class="ec">{s["point"]}</span></div>')
    return "".join(parts)

# ============================================================
# HTML/CSS
# ============================================================
CSS = """
@page { size: A4; margin: 17mm 15mm; }
* { box-sizing: border-box; }
body { font-family: 'Times New Roman','Hiragino Mincho ProN','Yu Mincho',serif; color:#000; font-size:10.5pt; line-height:1.85; }
.exam-head { text-align:center; border-bottom:2.5px solid #000; padding-bottom:6px; margin-bottom:12px; }
.exam-head .t1 { font-size:15pt; font-weight:bold; letter-spacing:2px; }
.exam-head .t2 { font-size:10pt; margin-top:3px; }
.daimon { font-size:12pt; font-weight:bold; border-left:6px solid #000; padding-left:8px; margin:16px 0 8px; page-break-before:auto; }
.passage p { margin:0 0 7px; text-align:justify; }
u.ul { text-decoration:underline; text-underline-offset:2px; }
u.wv { text-decoration: underline wavy; text-underline-offset:3px; }
u.ful { text-decoration:underline; text-decoration-thickness:1.5px; text-underline-offset:2px; }
sup.qn { font-weight:bold; font-size:8pt; }
.bk { font-weight:bold; white-space:nowrap; }
.glossary { font-family:'Hiragino Mincho ProN',serif; font-size:8.8pt; color:#222; background:#f5f5f0; border:1px solid #bbb; padding:5px 8px; margin:8px 0 4px; line-height:1.6; }
.srcnote { font-size:8.4pt; color:#444; margin:4px 0; text-align:right; }
.qh { font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:10pt; font-weight:bold; margin:12px 0 5px; background:#eee; padding:3px 7px; border-left:3px solid #555; }
.q { margin:2px 0 4px; font-size:10pt; line-height:1.6; }
.q .ql { font-weight:bold; margin-right:8px; font-family:'Hiragino Mincho ProN',serif; }
.q .opts .op { display:inline-block; margin:0 12px 1px 0; }
.qc .ql { display:block; margin-bottom:2px; }
.qc .phr { font-family:'Times New Roman',serif; font-style:italic; }
.opts-b .opb { display:block; margin:1px 0 1px 1.4em; text-indent:-1.4em; }
.elist .opb { font-family:'Hiragino Mincho ProN','Times New Roman',serif; }
.dbank { background:#f4f4ef; border:1px solid #999; padding:5px 9px; margin:3px 0; font-size:10pt; }
.dnote { font-family:'Hiragino Mincho ProN',serif; font-size:9pt; color:#333; margin:2px 0 4px; }
.setting { font-family:'Hiragino Mincho ProN',serif; font-size:9.4pt; background:#f5f5f0; border:1px solid #bbb; padding:5px 9px; margin:6px 0; }
.dialog { margin:6px 0; }
.dl { margin:3px 0; text-indent:-2.6em; padding-left:2.6em; }
.dl .sp { font-weight:bold; }
.bja { font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:10.5pt; margin:3px 0 0 1em; }
/* 解答編 */
.qsec-title { font-size:11pt; font-weight:bold; margin:15px 0 6px; border-bottom:1.5px solid #000; padding-bottom:2px; }
.arow { display:flex; flex-wrap:wrap; align-items:baseline; gap:4px 8px; margin:4px 0; font-size:10pt; }
.arow .al { flex:0 0 1.6em; font-weight:bold; background:#333; color:#fff; text-align:center; border-radius:2px; }
.arow .ac { font-family:'Hiragino Mincho ProN','Times New Roman',serif; }
.overview { font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:9.8pt; line-height:1.75; background:#f6f6f2; border-left:4px solid #444; padding:8px 12px; margin:4px 0 12px; text-align:justify; }
.exp { margin:6px 0 11px; font-family:'Hiragino Mincho ProN','Yu Mincho',serif; font-size:9.4pt; line-height:1.6; }
.exp-head { font-weight:bold; font-size:10pt; border-bottom:1px solid #bbb; padding-bottom:1px; margin-bottom:3px; break-inside:avoid; }
.ep { display:flex; gap:7px; margin:2.5px 0; line-height:1.68; break-inside:avoid; }
.ep .pl { flex:0 0 5.7em; align-self:flex-start; font-weight:bold; color:#fff; background:#555; text-align:center; padding:0.8px 0; border-radius:2px; font-size:8pt; white-space:nowrap; }
.ep .pl.pt { background:#8a6d1a; }
.ep .ec { flex:1; }
.ep .quo { font-family:'Times New Roman',serif; }
.ep .qja { color:#333; }
"""

def page(body):
    return f"<!doctype html><html lang='ja'><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"

def build_problem():
    head = ('<div class="exam-head"><div class="t1">同志社大学 2026 英語 実戦問題</div>'
            '<div class="t2">全3問（Ⅰ・Ⅱ 長文読解／Ⅲ 会話文）／試験時間 100分／配点 200点</div></div>')
    body = [head]
    if CONTENT.get("I"):   body.append(render_reading(CONTENT["I"]))
    if CONTENT.get("II"):  body.append(render_reading(CONTENT["II"]))
    if CONTENT.get("III"): body.append(render_convo(CONTENT["III"]))
    return page("\n".join(body))

def build_answer():
    head = ('<div class="exam-head"><div class="t1">同志社大学 2026 英語 実戦問題 &mdash; 解答編</div>'
            '<div class="t2">解答・解説</div></div>')
    body = [head]
    if OVERVIEW:
        body.append('<div class="qsec-title">この試験の解き方・攻略の視点</div>'
                    f'<div class="overview">{OVERVIEW}</div>')
    if CONTENT.get("I"):   body.append(answer_list_reading(CONTENT["I"], "I"))
    if CONTENT.get("II"):  body.append(answer_list_reading(CONTENT["II"], "II"))
    if CONTENT.get("III"): body.append(answer_list_convo(CONTENT["III"], "III"))
    # 解説（explanations_seki.json があれば問ごとに正解付き見出しで描画）
    if EXP:
        body.append(render_explanations())
    return page("\n".join(body))

def _exp_block(header, idkey):
    eb = _exp_body(idkey)
    if not eb:
        return f'<div class="exp"><div class="exp-head">{header}</div>'\
               f'<div class="ep"><span class="ec" style="color:#999">（解説準備中）</span></div></div>'
    return f'<div class="exp"><div class="exp-head">{header}</div>{eb}</div>'

def render_explanations():
    out = ['<div class="qsec-title">解説</div>']
    for K in ("I", "II"):
        sec = CONTENT.get(K)
        if not sec: continue
        out.append(f'<div class="daimon">{sec["label"]}　解説</div>')
        for it in sec.get("A_items", []):
            h = f'問A（{it["slot"]}）　正解 {MARU[it["ans"]-1]} {it["options"][it["ans"]-1]}'
            out.append(_exp_block(h, f'{K}_A_{it["slot"]}'))
        for it in sec.get("B_items", []):
            h = f'問B（{it["label"]}）{it["word"]}　正解 {MARU[it["ans"]-1]} {it["options"][it["ans"]-1]}'
            out.append(_exp_block(h, f'{K}_B_{it["label"]}'))
        for it in sec.get("C_items", []):
            h = f'問C（{it["label"]}）　正解 {MARU[it["ans"]-1]}'
            out.append(_exp_block(h, f'{K}_C_{it["label"]}'))
        if sec.get("D_bank"):
            m = {x["slot"]: x["idx"] for x in sec["D_slot_map"]}
            av = "　".join(f'（{s}）{m.get(s,"?")}' for s in sec["D_answer_slots"])
            out.append(_exp_block(f'問D（整序）　正解 {av}', f'{K}_D'))
        if sec.get("E_answers"):
            av = " ".join(MARU[i-1] for i in sec["E_answers"])
            out.append(_exp_block(f'問E（内容一致）　正解 {av}', f'{K}_E'))
        if sec.get("F_model_ja"):
            out.append(_exp_block(f'問F（和訳）　解答例：{sec["F_model_ja"]}', f'{K}_F'))
    sec = CONTENT.get("III")
    if sec:
        out.append(f'<div class="daimon">{sec["label"]}　解説</div>')
        m = {x["slot"]: x["idx"] for x in sec["A_slot_map"]}
        av = "　".join(f'（{s}）{m.get(s,"?")}' for s in sec["A_slots"])
        out.append(_exp_block(f'問A（会話補充）　正解 {av}', 'III_A'))
        if sec.get("B_model_en"):
            out.append(_exp_block(f'問B（英訳）　解答例：{sec["B_model_en"]}', 'III_B'))
    return "\n".join(out)

def render_pdf(html, name):
    hp = os.path.join(HERE, f"_{name}.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    pdf = os.path.join(OUT, f"{name}.pdf")
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", "file://" + hp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", pdf)

if __name__ == "__main__":
    render_pdf(build_problem(), "同志社2026英語実戦問題_問題編")
    render_pdf(build_answer(),  "同志社2026英語実戦問題_解答編")
    print("OUT:", OUT)
