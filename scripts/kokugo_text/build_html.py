#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""単一ソース content.py から【縦書き】印刷用HTML kokugo-nankan.html を生成。

Chrome は単一の vertical-rl フローを複数ページに正しく分割できない（最後の1ページ分
しか出ず残りが白紙になる既知バグ）。そこで内容を**固定A4サイズの紙面(.sheet)へ手動で
分割**し、各 .sheet を独立した縦書きブロックにする。各 sheet は1ページに収まるので
ページ跨ぎの分割が起きず、Chrome の --print-to-pdf で縦書きのまま正しく出る。

構成 = 本編（講義＋例題＋問題のみ）→ 巻末「解答・解説編」。
確認問題・演習設問は本編では問題のみ、答えは巻末。
"""
import os, html, re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "kokugo-nankan.html")

import content as C

CIRCLED = ["①", "②", "③", "④", "⑤", "⑥"]
_ZI = re.compile(r"（\d+字）\s*$")
_DIG = re.compile(r"\d{1,3}")
_TAG = re.compile(r"<[^>]+>")

# 1 sheet あたりの収容量（縦の段数換算・経験値）。超えたら次の紙面へ。
BUDGET = 23.0

def esc(s):
    return html.escape(str(s), quote=False)

def nz(s):
    """半角数字(1〜3桁)を縦中横で正立。ただしタグ(<...>)内の属性値は触らない。"""
    parts = re.split(r"(<[^>]*>)", s)
    return "".join(
        p if p.startswith("<") else _DIG.sub(lambda m: f'<span class="tcy">{m.group(0)}</span>', p)
        for p in parts)

def plain(s):
    return _TAG.sub("", str(s))

def cols(text, per=30):
    """縦書きで text が占める概算段数。"""
    n = len(plain(text))
    return max(1.0, n / per)

def model_count(model):
    body = _ZI.sub("", str(model)).rstrip()
    return body, len(body)

# ---------------- 講義ブロック → (html, weight, own_sheet) ----------------
def lec(b):
    t = b["t"]
    if t == "lead":
        return f'<div class="lead">{b["html"]}</div>', cols(b["html"]) + 2, False
    if t == "h":
        return f'<h4 class="bh">{esc(b["text"])}</h4>', 1.4, False
    if t == "p":
        return f'<p class="bp">{b["html"]}</p>', cols(b["html"]) + 0.5, False
    if t in ("ul", "ol"):
        tag = "ul" if t == "ul" else "ol"
        items = "".join(f"<li>{x}</li>" for x in b["items"])
        w = sum(cols(x) for x in b["items"]) + 0.4 * len(b["items"])
        return f'<{tag} class="blist">{items}</{tag}>', w, False
    if t == "table":
        th = "".join(f"<th>{esc(h)}</th>" for h in b["head"])
        rows = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>"
                       for r in b["rows"])
        ncol = len(b["head"])
        w = 8.0 if ncol <= 2 else 11.0
        return (f'<div class="tw"><table class="c{ncol}"><thead><tr>{th}</tr></thead>'
                f'<tbody>{rows}</tbody></table></div>'), w, False
    if t == "point":
        return (f'<div class="point"><div class="point-t">▼ {esc(b["title"])}</div>'
                f'<div class="point-b">{b["html"]}</div></div>'), cols(b["html"]) + 2.2, False
    if t == "example":
        steps = ""
        w = 1.5
        for st in b["steps"]:
            steps += (f'<div class="exstep"><span class="exlabel">{esc(st["label"])}</span>'
                      f'<span class="exhtml">{st["html"]}</span></div>')
            w += cols(st["html"]) + 0.5
        return (f'<div class="example"><div class="ex-t">【例題】{esc(b["title"])}</div>'
                f'{steps}</div>'), w, False
    if t == "passage":
        h, w = passage(b)
        return h, w, False
    return "", 0.0, False

def passage(b):
    lines = "".join(f"<p>{ln}</p>" for ln in b["lines"])
    gloss = ""
    gw = 0.0
    if b.get("gloss"):
        gs = "".join(f'<li><b>{esc(w)}</b>＝{esc(m)}</li>' for w, m in b["gloss"])
        gloss = f'<div class="gloss-t">語注</div><ul class="gloss">{gs}</ul>'
        gw = sum(cols(f"{w}{m}", 22) for w, m in b["gloss"]) + 1
    w = sum(cols(ln, 28) for ln in b["lines"]) + 2 + gw
    return (f'<div class="passage"><div class="src">出典：{esc(b["source"])}</div>'
            f'<div class="ptext">{lines}</div>{gloss}</div>'), w

# ---------------- 問題（本編は問題のみ） ----------------
def quiz_problem(b, label):
    ch = "".join(f'<div class="choice">{CIRCLED[i]}　{esc(c)}</div>'
                 for i, c in enumerate(b["choices"]))
    w = cols(b["q"]) + sum(cols(c) for c in b["choices"]) + 1.5
    return (f'<div class="prob"><span class="plabel">{label}</span>'
            f'<span class="pq">{esc(b["q"])}</span>'
            f'<div class="choices">{ch}</div></div>'), w

def qa_problem(b, label):
    w = cols(b["q"]) + 1.0
    return (f'<div class="prob"><span class="plabel rec">{label}</span>'
            f'<span class="pq">{esc(b["q"])}</span></div>'), w

# ---------------- 解答（巻末） ----------------
def quiz_answer(b, label):
    ai = b["answer"]
    w = cols(b["explain"]) + cols(b["choices"][ai]) + 1.5
    return (f'<div class="ans"><span class="alabel">{label}</span>'
            f'<span class="acorrect">正解　{CIRCLED[ai]}　{esc(b["choices"][ai])}</span>'
            f'<div class="aexp">{esc(b["explain"])}</div></div>'), w

def choiceq_answer(q, label):
    ai = q["answer_index"]
    w = cols(q["explain"]) + cols(q["choices"][ai]) + 1.5
    return (f'<div class="ans"><span class="alabel">{label}</span>'
            f'<span class="acorrect">正解　{CIRCLED[ai]}　{esc(q["choices"][ai])}</span>'
            f'<div class="aexp">{esc(q["explain"])}</div></div>'), w

def qa_answer(q, label):
    body, n = model_count(q["model"])
    rub = "".join(f"<li>{esc(r)}</li>" for r in q["rubric"])
    w = cols(body) + sum(cols(r) for r in q["rubric"]) + cols(q["explain"]) + 2.5
    return (f'<div class="ans"><span class="alabel rec">{label}</span>'
            f'<div class="amodel"><b>模範解答</b>　{esc(body)}<span class="ji">（{n}字）</span></div>'
            f'<div class="rub-t">採点ルーブリック（部分点の付き方）</div>'
            f'<ul class="rub">{rub}</ul>'
            f'<div class="aexp"><b>解説</b>　{esc(q["explain"])}</div></div>'), w

# ---------------- フロー組み立て ----------------
def build_flow():
    """flow = list of unit dicts: {html, w, sheet('cover'/'tobira'/'flow'), sec, head(bool)}"""
    flow = []

    def u(html_, w, kind="flow", sec="", head=False):
        flow.append({"html": html_, "w": w, "kind": kind, "sec": sec, "head": head})

    # 表紙
    cnt = "　／　".join(f'{c["label"]} 全{c["lessons"]}講' for c in C.counts())
    u(f'<div class="cover-in"><div class="cover-title">{esc(C.TITLE)}</div>'
      f'<div class="cover-sub">{esc(C.SUBTITLE)}</div>'
      f'<div class="cover-tag">{esc(C.TAGLINE)}</div>'
      f'<div class="cover-line">{cnt}</div>'
      f'<div class="cover-foot">AI塾　trillion-ai-juku.com</div></div>', 0, kind="cover")

    # 使い方
    u(f'<div class="ko-head"><span class="ko-no">使い方</span>'
      f'<span class="ko-t">この教材の進め方</span></div>', 2, sec="使い方", head=True)
    u(f'<p class="bp">{esc(C.COURSE_INTRO)}</p>', cols(C.COURSE_INTRO) + 0.5, sec="使い方")
    how = "".join(f"<li>{esc(x)}</li>" for x in C.HOW_TO_USE)
    u(f'<ol class="blist">{how}</ol>', sum(cols(x) for x in C.HOW_TO_USE) + 2, sec="使い方")
    u('<div class="point"><div class="point-t">▼ 問題と解答について</div>'
      '<div class="point-b">本編には「<b>確認</b>」問題と各編末の「<b>演習</b>」を'
      '<b>問題のみ</b>で載せています。正解・模範解答・採点ルーブリック・解説は'
      '<b>巻末の「解答・解説編」</b>にまとめてあります。'
      'まず自力で解き、答え合わせは巻末で行ってください。</div></div>', 4, sec="使い方")

    kaitou = []
    for ed in C.EDITIONS:
        # 編扉（ねらいの説明も同じ扉に載せる）
        u(f'<div class="tobira-in"><div class="tobira-label">{esc(ed["label"])}編</div>'
          f'<div class="tobira-tag">{esc(ed["tagline"])}</div>'
          f'<div class="tobira-intro">{ed["intro"]}</div></div>', 0, kind="tobira")

        ans_groups = []
        for ls in ed["lessons"]:
            sec = f'{ed["label"]}編 第{ls["no"]}講'
            u(f'<div class="ko-head"><span class="ko-no">第{ls["no"]}講</span>'
              f'<span class="ko-t">{esc(ls["title"])}</span></div>', 2.0, sec=sec, head=True)
            ans_items = []
            pno = 0
            for b in ls["blocks"]:
                if b["t"] == "quiz":
                    pno += 1; lab = f"確認{pno}"
                    h, w = quiz_problem(b, lab); u(h, w, sec=sec)
                    ans_items.append(quiz_answer(b, lab))
                elif b["t"] == "qa":
                    pno += 1; lab = f"記述{pno}"
                    h, w = qa_problem(b, lab); u(h, w, sec=sec)
                    ans_items.append(qa_answer(b, lab))
                else:
                    h, w, _ = lec(b); u(h, w, sec=sec)
            if ans_items:
                ans_groups.append((f'第{ls["no"]}講　{esc(ls["title"])}', ans_items))

        # 演習
        d = ed["drill"]
        dtitle = esc(d["title"].split("──")[-1].strip())
        sec = f'{ed["label"]}編 演習'
        u(f'<div class="ko-head"><span class="ko-no drill">演習</span>'
          f'<span class="ko-t">{dtitle}</span></div>', 2.0, sec=sec, head=True)
        u(f'<p class="bp">{esc(d["intro"])}</p>', cols(d["intro"]) + 0.5, sec=sec)
        ph, pw = passage(d["passage"]); u(ph, pw, sec=sec)
        dans = []
        for i, q in enumerate(d["questions"], 1):
            lab = f"問{i}"
            if "choices" in q:
                ch = "".join(f'<div class="choice">{CIRCLED[j]}　{esc(c)}</div>'
                             for j, c in enumerate(q["choices"]))
                w = cols(q["q"]) + sum(cols(c) for c in q["choices"]) + 1.5
                u(f'<div class="prob"><span class="plabel">{lab}</span>'
                  f'<span class="pq">{esc(q["q"])}</span>'
                  f'<div class="choices">{ch}</div></div>', w, sec=sec)
                dans.append(choiceq_answer(q, lab))
            else:
                h, w = qa_problem(q, lab); u(h, w, sec=sec)
                dans.append(qa_answer(q, lab))
        ans_groups.append((f'演習　{dtitle}', dans))
        kaitou.append((ed["label"], ans_groups))

    # 解答・解説編
    u('<div class="tobira-in ans-tobira"><div class="tobira-label">解答・解説編</div>'
      '<div class="tobira-tag">確認問題・演習の正解／模範解答／採点ルーブリック</div></div>',
      0, kind="tobira")
    for label, groups in kaitou:
        sec = f'{label}編 解答'
        u(f'<div class="ko-head ans-head"><span class="ko-no ans-no">{esc(label)}編</span>'
          f'<span class="ko-t">解答・解説</span></div>', 2.0, sec=sec, head=True)
        for gtitle, items in groups:
            u(f'<h4 class="ans-g">{gtitle}</h4>', 1.5, sec=sec)
            for h, w in items:
                u(h, w, sec=sec)
    return flow

# ---------------- 紙面へ分割 ----------------
def paginate(flow):
    sheets = []  # each: {"kind","sec","items":[html...]}
    cur = None
    wsum = 0.0
    pageno = 0

    def flush():
        nonlocal cur, wsum
        if cur is not None:
            sheets.append(cur)
        cur = None
        wsum = 0.0

    for it in flow:
        if it["kind"] in ("cover", "tobira"):
            flush()
            sheets.append({"kind": it["kind"], "sec": "", "items": [it["html"]]})
            continue
        if it["head"]:
            flush()
            cur = {"kind": "flow", "sec": it["sec"], "items": [it["html"]], "head": True}
            wsum = it["w"]
            continue
        if cur is None:
            cur = {"kind": "flow", "sec": it["sec"], "items": [], "head": False}
            wsum = 0.0
        if wsum + it["w"] > BUDGET and cur["items"]:
            sec = cur["sec"]
            flush()
            cur = {"kind": "flow", "sec": sec, "items": [], "head": False, "cont": True}
            wsum = 0.0
        cur["items"].append(it["html"])
        wsum += it["w"]
    flush()
    return sheets

def render_sheets(sheets):
    out = []
    total = len(sheets)
    for i, sh in enumerate(sheets, 1):
        cls = "sheet"
        inner = ""
        if sh["kind"] == "cover":
            cls += " cover"
            inner = sh["items"][0]
        elif sh["kind"] == "tobira":
            cls += " tobira"
            inner = sh["items"][0]
        else:
            cont = ""
            if sh.get("cont"):
                cont = f'<div class="cont">{esc(sh["sec"])}（つづき）</div>'
            inner = (f'<div class="page-body">{cont}{"".join(sh["items"])}</div>'
                     f'<div class="pageno">{i}</div>')
        out.append(f'<div class="{cls}">{inner}</div>')
    return "".join(out)

def build():
    flow = build_flow()
    sheets = paginate(flow)
    body = nz(render_sheets(sheets))
    doc = TEMPLATE.replace("{{BODY}}", body)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    print("WROTE", OUT, "|", len(doc), "bytes |", len(sheets), "sheets")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>国公立難関 国語 ── 縦書き授業テキスト</title>
<style>
  @page { size: A4; margin: 0; }
  :root{
    --ink:#1a1a1a; --sub:#555; --navy:#1f3a5f; --accent:#b8412a; --gold:#b08a2e;
    --rule:#cfd8e3; --pt-bg:#fbf3e2; --pt-bd:#e0c486; --lead-bg:#eef3fb;
    --ans-bg:#f3f7fc; --ok:#0f7a43; --ok-bg:#eaf6ef;
  }
  *{ box-sizing:border-box; }
  html,body{ margin:0; padding:0; background:#fff; }
  body{ -webkit-print-color-adjust:exact; print-color-adjust:exact;
        font-family:"Hiragino Mincho ProN","YuMincho","Yu Mincho","HGS明朝E","MS Mincho",serif;
        color:var(--ink); }
  .sheet{ width:210mm; height:297mm; padding:15mm 16mm; position:relative;
          overflow:hidden; break-after:page; background:#fff; }
  .sheet:last-child{ break-after:auto; }
  @media screen{
    body{ background:#e9edf2; }
    .sheet{ margin:14px auto; box-shadow:0 2px 14px rgba(0,0,0,.14); }
  }
  .page-body{ writing-mode:vertical-rl; -webkit-writing-mode:vertical-rl;
    height:100%; font-size:10.4pt; line-height:2.05; letter-spacing:.02em; }
  .tcy{ -webkit-text-combine:horizontal; text-combine-upright:all; }
  b{ font-weight:700; }
  u{ text-decoration:underline; text-underline-offset:.18em; }
  .ko-no,.cover-title,.tobira-label,.bh,.point-t,.plabel,.alabel,.ans-no,.ans-g,.exlabel,.ko-t{
    font-family:"Hiragino Kaku Gothic ProN","Yu Gothic","YuGothic","Meiryo",sans-serif;
  }
  .pageno{ position:absolute; bottom:7mm; left:0; width:100%; text-align:center;
    font-size:9pt; color:var(--sub); font-family:sans-serif; }
  /* 表紙・扉（横組み中央） */
  .cover .cover-in,.tobira .tobira-in{ height:100%; display:flex; flex-direction:column;
    align-items:center; justify-content:center; gap:14px; text-align:center; }
  .cover-title{ font-size:34px; font-weight:800; color:var(--navy); letter-spacing:.08em; }
  .cover-sub{ font-size:16px; color:#333; }
  .cover-tag{ font-size:14px; color:var(--accent); border-top:2px solid var(--gold);
    border-bottom:2px solid var(--gold); padding:8px 14px; margin-top:8px; }
  .cover-line{ font-size:12px; color:var(--sub); margin-top:18px; }
  .cover-foot{ font-size:11px; color:var(--sub); margin-top:42px; }
  .tobira-label{ font-size:30px; font-weight:800; color:#fff; background:var(--navy);
    padding:16px 30px; border-radius:10px; letter-spacing:.1em; }
  .ans-tobira .tobira-label{ background:var(--accent); }
  .tobira-tag{ font-size:14px; color:var(--accent); }
  .tobira-intro{ font-size:11.5px; line-height:1.9; color:#333; max-width:130mm;
    margin-top:18px; text-align:left; }
  /* 講見出し */
  .ko-head{ border-right:4px solid var(--navy); padding-right:10px; margin-left:14px;
    display:flex; align-items:flex-start; gap:12px; }
  .ans-head{ border-right-color:var(--accent); }
  .ko-no{ font-size:12px; color:#fff; background:var(--navy); padding:5px 8px; border-radius:6px;
    writing-mode:horizontal-tb; white-space:nowrap; }
  .ko-no.drill,.ko-no.ans-no{ background:var(--accent); }
  .ko-t{ font-size:15px; font-weight:700; }
  .cont{ writing-mode:horizontal-tb; font-size:9pt; color:var(--sub); margin:0 0 6px 14px;
    border-bottom:1px dotted var(--rule); padding-bottom:3px; font-family:sans-serif; }
  /* 本文要素 */
  .bp{ margin:.5em 0; text-indent:1em; }
  .bh{ font-size:12pt; color:var(--navy); margin:.9em 0 .3em; border-right:3px solid var(--accent);
    padding-right:8px; font-weight:600; }
  .blist{ margin:.5em 0; padding:0; }
  .blist li{ margin:.4em 1.2em .4em 0; }
  /* 表（横組みで埋め込む） */
  .tw{ writing-mode:horizontal-tb; margin:8px 6px; display:inline-block; vertical-align:top; }
  table{ border-collapse:collapse; font-family:"Hiragino Kaku Gothic ProN",sans-serif;
    font-size:8.6pt; line-height:1.45; }
  table.c2{ max-width:78mm; } table.c3{ max-width:120mm; }
  th{ background:var(--navy); color:#fff; font-weight:600; text-align:left; padding:3px 7px; }
  td{ border:1px solid var(--rule); padding:3px 7px; vertical-align:top; }
  tbody tr:nth-child(even){ background:#eef3fb; }
  /* 箱 */
  .lead{ background:var(--lead-bg); border:1px solid #cfe0f5; border-radius:8px;
    padding:7px 11px; margin:.6em 0; }
  .point{ background:var(--pt-bg); border:1px solid var(--pt-bd); border-radius:8px;
    padding:7px 11px; margin:.6em 0; }
  .point-t{ color:var(--accent); font-weight:700; font-size:10.6pt; margin-bottom:.2em; }
  .example{ border:1px dashed var(--rule); border-radius:8px; padding:7px 11px; margin:.6em 0; }
  .ex-t{ color:var(--navy); font-weight:700; margin-bottom:.3em; }
  .exstep{ margin:.4em 0; }
  .exlabel{ font-size:8.6pt; color:#fff; background:var(--accent); padding:1px 6px; border-radius:5px;
    writing-mode:horizontal-tb; display:inline-block; margin-bottom:.15em; }
  .exhtml{ display:block; }
  /* 本文（古文漢文評論） */
  .passage{ border:1px solid var(--rule); border-radius:8px; padding:9px 13px; margin:.6em 0;
    background:#fafbfd; }
  .src{ font-size:8.6pt; color:var(--sub); margin-bottom:.4em; }
  .ptext p{ margin:.4em 0; text-indent:1em; font-size:10.8pt; line-height:2.25; }
  .gloss-t{ font-size:9pt; color:var(--navy); font-weight:700; margin:.5em 0 .2em; }
  .gloss{ font-size:9pt; color:#444; margin:0; padding:0; }
  .gloss li{ margin:.22em 1.2em .22em 0; }
  /* 問題 */
  .prob{ border-right:2px solid var(--accent); padding-right:10px; margin:.8em 0; }
  .plabel{ font-size:9.6pt; color:#fff; background:#2a5d9e; padding:2px 7px; border-radius:5px;
    writing-mode:horizontal-tb; display:inline-block; margin-bottom:.3em; }
  .plabel.rec{ background:var(--accent); }
  .pq{ font-weight:600; display:block; }
  .choices{ margin-top:.4em; }
  .choice{ margin:.25em 0; }
  /* 解答編 */
  .ans-g{ font-size:11pt; color:var(--navy); font-weight:700; margin:.9em 0 .4em;
    border-right:3px solid var(--navy); padding-right:8px; }
  .ans{ background:var(--ans-bg); border-radius:8px; padding:7px 11px; margin:.5em 0; }
  .alabel{ font-size:9.6pt; color:#fff; background:#2a5d9e; padding:2px 7px; border-radius:5px;
    writing-mode:horizontal-tb; display:inline-block; margin-bottom:.3em; }
  .alabel.rec{ background:var(--accent); }
  .acorrect{ display:block; color:var(--ok); font-weight:700; }
  .amodel{ background:var(--ok-bg); border-radius:6px; padding:5px 9px; margin:.3em 0; color:#0d5e35; }
  .ji{ font-size:8.6pt; color:var(--sub); }
  .rub-t{ font-size:9pt; color:var(--navy); font-weight:700; margin:.4em 0 .2em; }
  .rub{ font-size:9pt; margin:0; padding:0; }
  .rub li{ margin:.22em 1.2em .22em 0; }
  .aexp{ margin-top:.4em; font-size:9.6pt; color:#21466e; }
</style>
</head>
<body>
{{BODY}}
</body>
</html>"""

if __name__ == "__main__":
    build()
