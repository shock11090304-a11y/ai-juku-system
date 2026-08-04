#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共通テスト形式 英語長文 演習10題 を PDF 化する。

  python3 build_eng.py

passages/p01.json 〜 p10.json を単一ソースにして
  問題編(本文+語注+設問5問4択) / 解答欄 / 解答・解説編(解説+全文和訳)
を1冊に組む。HTML → Chrome --headless --print-to-pdf → fitz で柱+ノンブル刻印。
"""
import os, re, sys, json, html, subprocess, datetime
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
MATH = os.path.abspath(os.path.join(HERE, "..", "math_workbook"))
sys.path.insert(0, MATH)
import build_html as B          # noqa: E402  CHROME / stamp_pdf

OUT = os.path.join(HERE, "kyotsu_eng_reading10.pdf")
TITLE = "共通テスト形式　英語長文 演習10題"
SUBTITLE = "各250語・5問（全問4択マーク式）"
TAGLINE = "本文の根拠だけで一意に決まる問題を、共通テストと同じ型で50問"
BOOK = "共通テスト形式 英語長文 演習10題"
MINUTES = 8          # 1題あたりの目標時間
CIRCLED = "①②③④"

HOWTO = ("【この問題集の使い方】共通テストのリーディングは、"
         "<b>本文に書いてあることだけで答えが一つに決まる</b>ように作られています。"
         "だから「常識で考えるとこれかな」で選んだ時点で、もう共通テストの解き方から外れています。"
         "1題8分を目安に時間を計って解き、答え合わせのときは正解した問題も含めて"
         "<b>「本文のどの1文が根拠か」を指で押さえて確認</b>してください。"
         "解答・解説編には各問の根拠の文をそのまま載せてあります。"
         "根拠の文を自分で見つけられるようになれば、本番で選択肢に迷う時間が半分になります。")

TYPE_JA = {
    "fact_opinion": "事実と意見の区別", "detail": "内容一致", "inference": "推論",
    "order": "出来事の順序", "main_idea": "主題・要旨", "vocab": "語意の推測",
    "purpose": "目的・意図", "slide": "要約スライドの空所",
    "outline": "アウトラインの空所",
}


def esc(s):
    return html.escape("" if s is None else str(s), quote=False)


def keep_u(s):
    """<u>…</u> だけは生かす(語意推測問題の下線)。"""
    return esc(s).replace("&lt;u&gt;", "<u>").replace("&lt;/u&gt;", "</u>")


def load():
    out = []
    for n in range(1, 11):
        p = os.path.join(HERE, "passages", f"p{n:02d}.json")
        with open(p, encoding="utf-8") as f:
            out.append(json.load(f))
    return out


def wc(s):
    """語数。★<u>…</u> の u を1語として数えてしまい語数表示がずれていたのでタグを落とす。"""
    s = re.sub(r"</?u>", "", s or "")
    return len([w for w in re.split(r"[^A-Za-z'’\-]+", s) if w])


CSS = """
@page { size: A4; margin: 12mm 12mm 10mm 12mm; }
* { box-sizing: border-box; }
body { font-family:"Hiragino Mincho ProN","Yu Mincho",serif; color:#1a1a1a; font-size:9.3pt;
       line-height:1.55; margin:0; }
.gothic, h1,h2,h3,.band,.qno,.tag,.foot,.opt-l { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }
/* 英文は数字が跳ねない字体で(Georgia の旧字体数字は年号が上下する) */
.en { font-family:"Times New Roman",Georgia,serif; font-feature-settings:"lnum" 1;
      font-variant-numeric: lining-nums; }

/* 表紙 */
.cover { height:247mm; position:relative; page-break-after:always; }
.cover .cband { position:absolute; top:-16mm; left:-15mm; width:210mm; height:70mm; background:#1f3a5f; }
.cover .rule { position:absolute; top:54mm; left:-15mm; width:210mm; height:2mm; background:#c8a24e; }
.cover .title { position:absolute; top:92mm; width:100%; text-align:center;
                font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.cover .title h1 { color:#1f3a5f; font-size:27pt; margin:0; letter-spacing:2px; }
.cover .title .sub { color:#1f3a5f; font-size:14pt; margin-top:8px; }
.cover .title .tag { color:#444; font-size:12pt; margin-top:20px; font-weight:normal; }
.cover .title .meta { color:#444; font-size:11.5pt; margin-top:8px; }
.cover .foot { position:absolute; top:190mm; width:100%; text-align:center; color:#8a8a8a;
               font-size:10.5pt; font-family:sans-serif; }

/* 目次 */
.toc { page-break-after:always; }
.toc h2 { color:#1f3a5f; text-align:center; font-size:19pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif;
          margin:0 0 10px; }
.toc-row { display:flex; align-items:center; border-bottom:0.5px solid #c9d4e0; padding:5px 2px; font-size:10pt; }
.toc-no { color:#1f3a5f; font-weight:bold; width:44px; font-family:sans-serif; }
.toc-th { flex:0 0 30%; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.toc-g  { flex:1; color:#8a8a8a; font-size:9pt; }
.toc-w  { color:#8a8a8a; font-size:9pt; width:52px; text-align:right; }
.howto { margin-top:14px; color:#333; font-size:9.8pt; background:#f4f6f9; border-left:3px solid #c8a24e;
         padding:10px 12px; break-inside:avoid; }
.howto b { color:#1f3a5f; }

/* 大扉 */
.divider { height:247mm; page-break-before:always; page-break-after:always; display:flex;
           flex-direction:column; justify-content:center; align-items:center; }
.divider h2 { color:#1f3a5f; font-size:24pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin:0;
              letter-spacing:3px; }
.divider .d-sub { color:#555; font-size:12pt; margin-top:10px; }

/* 各題 */
.item { page-break-before:always; }
.band { background:#1f3a5f; color:#fff; padding:4px 11px 5px; display:flex; justify-content:space-between;
        align-items:flex-end; }
.band .l { font-size:15pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.band .l small { font-size:9.5pt; opacity:.85; margin-left:10px; }
.band .r { font-size:9pt; text-align:right; opacity:.9; line-height:1.5; }
.lead { font-size:9pt; margin:3px 0 1px; padding:3px 8px; background:#f4f6f9;
        border-left:3px solid #c8a24e; line-height:1.4; }
.ttl { color:#1f3a5f; font-size:10.2pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin:3px 0 1px; }
.para { display:flex; gap:6px; margin:0 0 2.5px; break-inside:avoid; }
.para .num { flex:0 0 17px; height:17px; background:#1f3a5f; color:#fff; border-radius:50%; text-align:center;
             line-height:17px; font-size:8pt; font-family:sans-serif; margin-top:2px; }
.para .body { flex:1; }
.en.body { line-height:1.4; text-align:justify; font-size:9.5pt; }
.en u { text-decoration:none; border-bottom:1.5px solid #c8492e; padding-bottom:1px; }
.gloss { font-size:8.2pt; color:#444; background:#f7f9fb; border:0.6px solid #d5dde6; padding:3px 7px;
         margin:3px 0 1px; line-height:1.4; break-inside:avoid; }
.gloss b { color:#1f3a5f; }
.qsec { margin-top:2px; }
.q { margin:0 0 2px; break-inside:avoid; }
.q .qh { font-size:9.1pt; color:#1f3a5f; }
.q .qt { font-size:8.4pt; color:#8a8a8a; margin-left:8px; font-family:sans-serif; }
.q .qb { margin:0 0 1px; font-size:9.3pt; line-height:1.4; }
.opt { padding-left:16px; text-indent:-16px; margin:0; line-height:1.24; font-size:9.05pt; }
/* 発表スライド・資料の枠(共テ第5問/第6問の「スライドの空所」型) */
.slide { border:1px solid #9fb0c3; border-left:4px solid #1f3a5f; background:#f7f9fb;
         padding:4px 10px; margin:3px 0 4px 8px; font-size:9.4pt; line-height:1.55; }
.opt-l { color:#1f3a5f; font-weight:bold; }

/* 解答欄 */
.sheet { page-break-before:always; }
.sheet h2 { color:#1f3a5f; font-size:17pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin:0 0 4px; }
table.ans { border-collapse:collapse; width:100%; margin-top:8px; }
table.ans th { background:#1f3a5f; color:#fff; font-size:9pt; font-weight:normal; padding:4px 6px;
               border:0.6px solid #9fb0c3; font-family:sans-serif; }
table.ans td { border:0.6px solid #9fb0c3; padding:5px 6px; text-align:center; font-size:10pt; }
/* ★白紙の題名セルに nowrap を効かせていたため、長い題名がテーブルを紙幅の外まで
   押し広げ、問5の④が断ち切られ得点欄が紙から消えていた。題名は折り返させる。 */
table.ans td.k { background:#eaeff5; color:#1f3a5f; font-family:sans-serif; font-size:9pt; }
table.ans td.k.t { text-align:left; width:22%; }
table.ans td.k.s { white-space:nowrap; width:12%; }
table.ans { table-layout:fixed; }
table.ans td .c { color:#b9c6d4; letter-spacing:2px; }

/* 解説 */
.ansitem { page-break-before:always; }
.keyrow { display:flex; gap:6px; margin:6px 0 7px; }
.keyrow .cell { border:1px solid #1f3a5f; border-radius:4px; padding:3px 0; flex:1; text-align:center;
                font-size:10pt; font-family:sans-serif; }
.keyrow .cell b { color:#c8492e; font-size:12pt; }
.exp { margin:0 0 6px; break-inside:avoid; }
.exp .eh { font-family:"Hiragino Kaku Gothic ProN",sans-serif; color:#1f3a5f; font-size:10pt; }
.exp .ans { color:#c8492e; font-weight:bold; }
.exp .ev { font-size:8.8pt; background:#f4f6f9; border-left:3px solid #c8a24e; padding:4px 8px; margin:2px 0; line-height:1.5; }
.exp .ev .lab { color:#1f3a5f; font-family:sans-serif; font-size:8.5pt; display:block; }
.exp .bd { font-size:9.2pt; }
.exp .dis { font-size:8.9pt; color:#444; margin-top:1px; line-height:1.5; }
/* ★break-inside:avoid だと和訳が丸ごと次ページへ飛び、解説ページ下部が空いているのに
   和訳ページ10枚が3割しか埋まらなかった。見出しの独り残りだけ禁じ、本体は流し込む。 */
.trans { margin-top:8px; }
.trans h3 { color:#1f3a5f; font-size:11pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif;
            margin:0 0 4px; border-bottom:1px solid #c9d4e0; padding-bottom:2px;
            break-after:avoid; page-break-after:avoid; }
.trans p { margin:0 0 3px; font-size:9.2pt; }
"""


def paras_html(passage, title=""):
    """段落を組む。

    ★段落内の改行(1個の \\n)を潰してはいけない。告知(第1題)の「New Opening Hours」+時間、
      ブログ(第3題)の「Day 1」+本文、メール(第7題)の From/To/Subject は、
      その行構造そのものが共通テストの読み取り対象。<br> として残す。
    ★本文の1段落目がタイトルと同じ題は、タイトルを別に印刷しているので重複を落とす。
    """
    paras = [x.strip() for x in passage.split("\n\n") if x.strip()]
    t = title.strip().rstrip("!.").lower()
    if paras and t:
        if paras[0].rstrip("!.").lower() == t:
            paras = paras[1:]                       # 1段落目まるごとがタイトル(第1題)
        else:
            lines = paras[0].split("\n")
            if lines[0].strip().rstrip("!.").lower() == t and len(lines) > 1:
                paras[0] = "\n".join(lines[1:]).strip()   # 1行目だけがタイトル(第2題)
    out = []
    for i, p in enumerate(paras, 1):
        body = "<br>".join(keep_u(line) for line in p.split("\n"))
        out.append(f'<div class="para"><div class="num">{i}</div>'
                   f'<div class="body en body">{body}</div></div>')
    return "".join(out)


def gloss_html(g):
    if not g:
        return ""
    items = "　／　".join(f'<b>{esc(x["word"])}</b> {esc(x["ja"])}' for x in g)
    return f'<div class="gloss">語注　{items}</div>'


RULE_LINE = re.compile(r"^[\s\-=_*・]+$")


def stem_html(text):
    """設問文を組む。

    ★実改行を捨てると壊れる設問がある:
      ・出来事の順序(order)の「A: … / B: …」が1行に連なって読めなくなる
      ・発表スライド(slide)の見出しと箇条書きが1文につながり、区切りに使った
        「-----」や「*」が生の記号のまま紙に出る
    改行は <br> にし、罫線だけの行は捨て、箇条書きの記号は「・」に統一する。
    最初の空行より後ろは「スライド/資料」とみなして枠で囲む。
    """
    blocks = [b for b in text.split("\n\n") if b.strip()]
    if not blocks:
        return ""
    head = "<br>".join(esc(l.strip()) for l in blocks[0].split("\n") if l.strip())
    out = [f'<div class="qb en">{head}</div>']
    for b in blocks[1:]:
        lines = []
        for l in b.split("\n"):
            l = l.strip()
            if not l or RULE_LINE.match(l):
                continue
            l = re.sub(r"^[\-*•]\s*", "・", l)
            lines.append(esc(l))
        if lines:
            out.append(f'<div class="slide en">{"<br>".join(lines)}</div>')
    return "".join(out)


def item_html(d):
    qs = []
    for i, q in enumerate(d["questions"], 1):
        opts = "".join(f'<div class="opt"><span class="opt-l">{CIRCLED[k]}</span> '
                       f'<span class="en">{esc(o)}</span></div>' for k, o in enumerate(q["options"]))
        qs.append(f'<div class="q"><div class="qh">問 {i}'
                  f'<span class="qt">{TYPE_JA.get(q.get("type"), "")}</span></div>'
                  f'{stem_html(q["q"])}{opts}</div>')
    return (f'<section class="item">'
            f'<div class="band"><div class="l">第 {d["no"]} 題<small>{esc(d.get("genre",""))}</small></div>'
            f'<div class="r">{wc(d["passage"])} words<br>目標 {MINUTES} 分</div></div>'
            f'<div class="lead en">{esc(d.get("lead",""))}</div>'
            f'{"" if d.get("hide_title") else chr(60)+"div class=" + chr(34) + "ttl en" + chr(34) + chr(62) + esc(d.get("title","")) + chr(60) + "/div" + chr(62)}'
            f'{paras_html(d["passage"], d.get("title",""))}{gloss_html(d.get("glossary"))}'
            f'<div class="qsec">{"".join(qs)}</div></section>')


def sheet_html(data):
    rows = []
    for d in data:
        cells = "".join(f'<td><div class="c">①②③④</div></td>' for _ in range(5))
        # 題名列が狭く「レビュ／ー」のように禁則が破れていたので、大問番号だけにする
        tag = (d.get("genre", "") or "").split("\u3000")[0]
        rows.append(f'<tr><td class="k t">第{d["no"]}題　<span style="color:#8a8a8a">'
                    f'{esc(tag)}</span></td>{cells}'
                    f'<td class="k s">　／5</td></tr>')
    return (f'<div class="sheet"><h2>解答欄</h2>'
            f'<div style="font-size:9.6pt;color:#444;margin-bottom:2px;">'
            f'時間を計って解き、選んだ番号を書き込んでください。1題 {MINUTES} 分が目安です。</div>'
            f'<div style="font-size:10.5pt;margin:8px 0;">名前：<span style="border-bottom:1px solid #1a1a1a;'
            f'display:inline-block;min-width:150px;"></span>　　実施日：'
            f'<span style="border-bottom:1px solid #1a1a1a;display:inline-block;min-width:120px;"></span></div>'
            f'<table class="ans"><tr><th>題</th><th>問1</th><th>問2</th><th>問3</th><th>問4</th><th>問5</th>'
            f'<th>得点</th></tr>{"".join(rows)}</table></div>')


def ansitem_html(d):
    key = "".join(f'<div class="cell">問{i}<br><b>{CIRCLED[q["answer"]-1]}</b></div>'
                  for i, q in enumerate(d["questions"], 1))
    exps = []
    for i, q in enumerate(d["questions"], 1):
        exps.append(
            f'<div class="exp"><div class="eh">問 {i}　正解 <span class="ans">{CIRCLED[q["answer"]-1]}</span>'
            f'<span class="qt" style="color:#8a8a8a;font-size:8.5pt;margin-left:8px;">'
            f'{TYPE_JA.get(q.get("type"),"")}</span></div>'
            f'<div class="ev"><span class="lab">根拠になる本文の文</span>'
            f'<span class="en">{esc(q.get("evidence",""))}</span></div>'
            f'<div class="bd">{esc(q.get("explanation_ja",""))}</div>'
            f'<div class="dis">{esc(q.get("distractor_ja",""))}</div></div>')
    tp = "".join(f"<p>{esc(x.strip())}</p>"
                 for x in (d.get("translation_ja") or "").split("\n\n") if x.strip())
    return (f'<section class="ansitem">'
            f'<div class="band"><div class="l">第 {d["no"]} 題　解答・解説'
            f'<small>{esc(d.get("genre",""))}</small></div>'
            f'<div class="r">{esc(d.get("theme_ja",""))}</div></div>'
            f'<div class="keyrow">{key}</div>{"".join(exps)}'
            f'<div class="trans"><h3>全文和訳</h3>{tp}</div></section>')


def build(data):
    today = datetime.date.today().strftime("%Y年%m月")
    toc = "".join(
        # ★theme_ja(内容の要約)をここに出すと、main_idea や purpose を問う設問の答えを
        #   問題編の1ページ目で先に配ってしまう。目次は「形式と分量」だけにする。
        f'<div class="toc-row"><span class="toc-no">第{d["no"]}題</span>'
        f'<span class="toc-th">{esc(d.get("genre",""))}</span>'
        f'<span class="toc-g">出題形式 {" / ".join(TYPE_JA.get(q.get("type"),"") for q in d["questions"])}</span>'
        f'<span class="toc-w">{wc(d["passage"])}語</span></div>' for d in data)
    total_q = sum(len(d["questions"]) for d in data)
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="cover"><div class="cband"></div><div class="rule"></div>
  <div class="title"><h1>{esc(TITLE)}</h1><div class="sub">{esc(SUBTITLE)}</div>
  <div class="tag">{esc(TAGLINE)}</div>
  <div class="meta">全{len(data)}題　計{total_q}問　·　問題編／解答欄／解答・解説編</div></div>
  <div class="foot">{today}　トリリオン AI塾</div></div>

<div class="toc"><h2>目次</h2>{toc}<div class="howto">{HOWTO}</div></div>

<div class="divider"><h2>問題編</h2><div class="d-sub">全{len(data)}題　計{total_q}問　／　1題 {MINUTES} 分</div></div>
{"".join(item_html(d) for d in data)}
{sheet_html(data)}
<div class="divider"><h2>解答・解説編</h2><div class="d-sub">各問の根拠の文＋全文和訳</div></div>
{"".join(ansitem_html(d) for d in data)}
</body></html>"""


def main():
    data = load()
    hp = os.path.join(HERE, "_build_eng.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(build(data))
    subprocess.run([B.CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=30000", f"--print-to-pdf={OUT}", "file://" + hp],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    B.stamp_pdf(OUT, BOOK)
    doc = fitz.open(OUT)
    print(f"WROTE {OUT} | pages: {doc.page_count} | 題数: {len(data)} | "
          f"問題数: {sum(len(d['questions']) for d in data)} | "
          f"語数: {[wc(d['passage']) for d in data]}")
    doc.close()


if __name__ == "__main__":
    main()
