# -*- coding: utf-8 -*-
"""
中学生 夏休み特訓プリント（5科総合・10日分）のビルダー。

理科／社会の確認プリントと違い、こちらは **1日1セット×10日** の構成なので、
第1部/第2部/第3部ではなく DAY 単位で組む（build_common の部品だけ借りる）。

■ データの形（days/day01.py 〜 day10.py が DAY を1つずつ持つ）
  DAY = {
    "day": 1,
    "range": "中1範囲",                 # 中1範囲 / 中2範囲 / 中3 1学期範囲
    "range_note": "…",                 # 省略可。進め方の表の範囲欄に添える注記（未習の予告など）
    "theme": "正負の数と be動詞",        # その日の看板（★答えを言わない見出しにすること）
    "sections": [
      {"subj": "英語", "lead": "…", "qs": [ q, q, q, q ]},
      … 英・数・国・理・社 の5つ
    ],
  }
  q = {"type": "short"|"mc"|"calc"|"desc"|"order", "pt": 5, "q": 設問文, "ans": …, "exp": 解説,
       "choices": [...]（mc）, "unit": "cm"（calc）, "work": 途中式（calc）,
       "limit": 40, "keys": [...]（desc）, "tokens": [...]（order）}

■ 配点：1問5点 × 4問 × 5科 = 100点/日。10日で1000点。
■ ★見出し・その日のテーマがその日の答えを言っていないか、check.py が走査する
  （[[chem-camp-workbook-and-print-gates]] の「group 見出しが答えを言う」事故と同型）。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from build_common import (BASE_CSS, DESKTOP, esc, genko, render)  # noqa: E402

SUBJECTS = ["英語", "数学", "国語", "理科", "社会"]
CIRCLE = ["①", "②", "③", "④", "⑤", "⑥"]

# ★1日ぶんが何ページになるかは組版の結果なので、ここに書いた数と実物がずれる。
#   紙に刷るのはこの定数だけにして、build.py が完成PDFを開いて実測と突き合わせる
#   （初版は「1日1ページ」と刷っていたが実物は3ページだった）。
PAGES_PER_DAY = 3

EXTRA_CSS = """
/* ---- 夏休み特訓プリント 固有 ---- */
.dayhd { background:linear-gradient(90deg,#0f172a,#b45309); color:#fff; border-radius:9px;
  padding:9px 15px; margin:0 0 7px; display:flex; align-items:center; gap:12px;
  page-break-before:always; page-break-after:avoid; }
.dayhd.first { page-break-before:auto; }
.dayhd .d { font-size:19pt; font-weight:800; letter-spacing:.04em; white-space:nowrap; }
.dayhd .rg { background:#fff; color:#b45309; border-radius:5px; padding:1px 10px; font-size:9pt;
  font-weight:700; white-space:nowrap; }
.dayhd .th { font-size:10.4pt; font-weight:700; opacity:.96; }
.dayhd .mm { margin-left:auto; font-size:8.8pt; opacity:.92; white-space:nowrap; }
.scorerow { display:flex; gap:5px; margin:0 0 8px; font-size:8.8pt;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; page-break-after:avoid; }
.scorerow .c { border:1px solid #cbd5e1; border-radius:6px; padding:3px 0; flex:1;
  text-align:center; }
.scorerow .c b { color:#0f172a; }
.scorerow .c.tot { background:#fff7ed; border-color:#f59e0b; flex:0 0 118px; }
.subhd { display:flex; align-items:baseline; gap:9px; margin:9px 0 4px;
  border-bottom:1.8px solid #b45309; padding-bottom:3px; page-break-after:avoid; }
.subhd .s { background:#b45309; color:#fff; border-radius:5px; padding:1px 12px; font-size:10pt;
  font-weight:700; font-family:"Hiragino Kaku Gothic ProN",sans-serif; white-space:nowrap; }
.subhd .l { font-size:9pt; color:#475569; flex:1; }
.subhd .p { font-size:8.4pt; color:#dc2626; font-weight:700; white-space:nowrap;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.tokens { display:flex; flex-wrap:wrap; gap:4px 8px; margin:4px 0 3px 12px; font-size:9.5pt; }
.tokens span { border:1px solid #cbd5e1; border-radius:4px; padding:0 7px; white-space:nowrap; }
/* ★DAYの帯見出しがページ最下部に取り残され、その下が白紙のまま中身が次ページ、という
   泣き別れが起きていた（p14/p25 で実測）。丸つけ中に「DAY5の解説はどこから」が分からなくなる。
   問題編は DAY をすべてページ先頭から始めているので、解答解説編もそろえる。 */
/* ★display:inline-block では Chrome が page-break-before/after を無視する（.qagrp と同型）。
   これに気づかず「DAYごとに改ページ」と書いたつもりで実際は効いておらず、
   DAY5とDAY10の帯だけがページ最下部に取り残され、中身は次ページに出ていた（p14/p28で実測）。
   さらに柱のDAY刻印が「そのページに出た最後のDAY帯」を拾うので、p14の柱が
   中身はDAY4なのに「DAY 5」になっていた。block にして宣言を効かせる。 */
.daykey { font-size:11.4pt; font-weight:700; color:#fff; background:#b45309; border-radius:6px;
  padding:2px 13px; margin:12px 0 5px; display:block; width:fit-content;
  break-before:page; page-break-before:always; break-after:avoid; page-break-after:avoid; }
.daykey.first { page-break-before:auto; }
/* 英作文の書きかえ用（2行取り）。答の欄が短すぎて書けない事故の対策 */
.ansline .bl.full { flex:1 1 auto; }
.ansline .pad { flex:0 0 14px; }
/* ★1日＝5科×20問を、DAY見出しから始めて必ず3ページに収める設計。
   既定の余白のままだと20問が2.1〜2.4ページになり、3ページ目に1〜2問だけ残って
   「8%しか使っていないページ」ができる（実測 p4=8% / p10=14% / p25=14%）。
   設問まわりを詰めて、残りを計算らんとして使える形に寄せる。 */
.q { margin:0 0 3px; }
.q .choices div { margin:1px 0 0 12px; }
.ansline { margin:3px 0 0 12px; }
.subhd { margin:6px 0 3px; padding-bottom:2px; }
.tokens { margin:3px 0 2px 12px; }
.genko i { height:23px; }

.memo { border:1px dashed #cbd5e1; border-radius:7px; margin:8px 0 12px; min-height:560px;
  background:repeating-linear-gradient(#fff,#fff 25px,#f1f5f9 25px,#f1f5f9 26px); }
.memoh { font-size:8.6pt; font-weight:700; color:#94a3b8; padding:3px 10px;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }

.plan { width:100%; border-collapse:collapse; font-size:9pt; margin:6px 0 4px; }
.plan th, .plan td { border:1px solid #cbd5e1; padding:3px 7px; }
.plan th { background:#fff7ed; font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:8.6pt;
  text-align:center; }
.plan td.c { text-align:center; }
.plan td.chk { width:56px; }
"""


# ---------------------------------------------------------------- 部品
def _ansbody(q):
    """設問1つ分の解答欄（問題編）。"""
    t = q["type"]
    if t == "mc":
        return ('<div class="choices">' +
                "".join(f'<div>{CIRCLE[i]}　{esc(c)}</div>' for i, c in enumerate(q["choices"])) +
                '</div><div class="ansline"><span>答</span><span class="bl"></span></div>')
    if t == "order":
        pool = ('<div class="tokens">' +
                "".join(f'<span>{esc(x)}</span>' for x in q["tokens"]) + '</div>')
        # ★整序も short と同じく **答えの長さで欄を変える**。
        #   short だけ直して order を固定幅(.bl w＝79mm)のまま残していたため、
        #   43字の英文に1字1.8mm しか無い問題が12問中9問あった（short で「1.4mmでは
        #   書けない」と判断したのと同じ水準）。判定は _ansline_for() に一本化する。
        return pool + _ansline_for(q["ans"])
    if t == "calc":
        return ('<div class="ansline"><span>答</span><span class="bl w"></span>'
                f'<span class="unit">{esc(q.get("unit",""))}</span></div>')
    if t == "desc":
        return genko(q["limit"], q.get("cols", 20))
    return _ansline_for(q.get("ans", ""))


def _ansline_for(ans):
    """解答欄の幅を**答えの長さ**で決める。

    ★記号1つの問題も英作文の書きかえも同じ型なので、固定幅にすると必ずどちらかが壊れる。
      固定142pt(5cm)のままだと「Yuka does not speak Chinese at home.」(36字)が
      1字1.4mm になり、物理的に書き込めない。目安は 1字4mm 以上。
      short / order の両方から呼ぶこと（片方だけ直して整序が固定幅のまま残った）。
    """
    n = len(str(ans))
    if n >= 24:      # 紙幅いっぱい2行（178mm×2 ≒ 1字8mm）
        return ('<div class="ansline"><span>答</span><span class="bl full"></span></div>'
                '<div class="ansline"><span class="pad"></span>'
                '<span class="bl full"></span></div>')
    if n >= 12:      # 106mm ≒ 1字4.4mm
        return '<div class="ansline"><span>答</span><span class="bl w"></span></div>'
    return '<div class="ansline"><span>答</span><span class="bl"></span></div>'


def _q(q, no):
    lim = f'<span class="lim">（{q["limit"]}字以内）</span>' if q["type"] == "desc" else ""
    pt = f'<span class="qpt">{q.get("pt",5)}点</span>'
    return (f'<div class="q"><div class="h"><span class="qno">{esc(no)}</span>'
            f'<span class="stem">{esc(q["q"])}{lim}</span>{pt}</div>{_ansbody(q)}</div>')


def day_head(D, first=False):
    return (f'<div class="dayhd{" first" if first else ""}">'
            f'<span class="d">DAY {D["day"]}</span>'
            f'<span class="rg">{esc(D["range"])}</span>'
            f'<span class="th">{esc(D["theme"])}</span>'
            f'<span class="mm">目安 40分／100点</span></div>')


def score_row():
    cells = "".join(f'<div class="c"><b>{s}</b>　／20</div>' for s in SUBJECTS)
    return f'<div class="scorerow">{cells}<div class="c tot"><b>合計</b>　／100</div></div>'


def day_problem(D, first=False):
    h = [day_head(D, first), score_row()]
    for sec in D["sections"]:
        pts = sum(q.get("pt", 5) for q in sec["qs"])
        h.append(f'<div class="subhd"><span class="s">{esc(sec["subj"])}</span>'
                 f'<span class="l">{esc(sec.get("lead",""))}</span>'
                 f'<span class="p">{pts}点</span></div>')
        for i, q in enumerate(sec["qs"], start=1):
            h.append(_q(q, f"{i}"))
    # ★1日＝5科×20問はどう詰めても2.1〜2.4ページになり、3ページ目に余白が残る。
    #   「1日3ページ」を揃える設計（配るときに数えやすい）を保ったまま、
    #   余白を空白のままにせず計算らんとして使えるようにする。数学・理科では実際に要る。
    h.append('<div class="memo"><div class="memoh">計算・見直しらん</div></div>')
    return "".join(h)


def _fmt_ans(q):
    if q["type"] == "mc":
        return CIRCLE[q["ans"]] + "　" + esc(q["choices"][q["ans"]])
    return esc(q["ans"])


def day_key(D, first=False):
    h = [f'<div class="daykey{" first" if first else ""}">'
         f'DAY {D["day"]}　{esc(D["range"])}　解答・解説</div>']
    for sec in D["sections"]:
        h.append(f'<div class="subhd"><span class="s">{esc(sec["subj"])}</span>'
                 f'<span class="l">{esc(sec.get("lead",""))}</span></div>')
        for i, q in enumerate(sec["qs"], start=1):
            body = [f'<div class="ex"><div class="exh"><span class="exno">{i}</span>'
                    f'<span class="exa">{_fmt_ans(q)}</span></div>']
            if q.get("work"):
                body.append(f'<div class="work">{esc(q["work"])}</div>')
            body.append(f'<div class="exbody">{esc(q["exp"])}</div>')
            if q.get("keys"):
                body.append('<div class="keys"><b>採点のポイント（この要素が入っていれば○）：</b>'
                            + "／".join(esc(k) for k in q["keys"]) + '</div>')
            body.append('</div>')
            h.append("".join(body))
    return "".join(h)


# ---------------------------------------------------------------- 表紙まわり
def band(M, sub):
    return (f'<div class="band"><div class="l">{esc(M["title"])}'
            f'<small>{esc(M["subtitle"])}</small></div>'
            f'<div class="r"><b>{esc(sub)}</b><br>{esc(M["level"])}</div></div>')


def foot(M, label):
    return (f'<div class="foot">{esc(M["title"])}　{esc(label)}　／　{esc(M["org"])}</div>')


def plan_table(DAYS):
    """★10日分の進め方を1枚の表にして最初に置く。
    「いつ・どこを・何分で」が紙に無いと、夏休みの宿題は初日だけやって止まる。"""
    h = ['<div class="tbl"><div class="tcap">10日間の進め方（終わった日に✓を入れる）</div>',
         '<table class="plan"><tr><th>日</th><th>範囲</th><th>その日のテーマ</th>'
         '<th>目安</th><th>得点</th><th>✓</th></tr>']
    for D in DAYS:
        # ★range だけでは実態を言い切れない日がある（DAY10 の理科・社会は多くの学校で
        #   2学期配当）。ラベルを短く保ったまま、その日の範囲欄に注記を1行足せるようにする。
        rg = esc(D["range"])
        if D.get("range_note"):
            rg += f'<br><small>（{esc(D["range_note"])}）</small>'
        h.append(f'<tr><td class="c">DAY {D["day"]}</td><td class="c">{rg}</td>'
                 f'<td>{esc(D["theme"])}</td><td class="c">40分</td>'
                 f'<td class="c">　／100</td><td class="chk"></td></tr>')
    h.append('</table><div class="tnote">'
             f'1日ぶんは{PAGES_PER_DAY}ページです。丸つけまでやって、'
             'まちがえた問題には印をつけておくこと。'
             '10日ぶんが終わったら、印のついた問題だけをもう一度解く（ここがいちばん伸びる）。'
             '</div></div>')
    return "".join(h)


def doc(title, body):
    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<title>{esc(title)}</title><style>{BASE_CSS}{EXTRA_CSS}</style></head>'
            f'<body>{body}</body></html>')


def build_mondai(M, DAYS):
    h = [band(M, "問題編")]
    h.append('<div class="metarow"><div class="cell">氏名　　　　　　　　　　　　　　　</div>'
             '<div class="cell">学年　　　　年</div>'
             f'<div class="cell score">10日合計　　　／{100*len(DAYS)}点</div></div>')
    h.append(f'<div class="intro"><b>この特訓の進め方：</b>{esc(M["intro"])}</div>')
    h.append(plan_table(DAYS))
    for i, D in enumerate(DAYS):
        h.append(day_problem(D, first=False))
    h.append(foot(M, "問題編"))
    return "\n".join(h)


def build_kaisetsu(M, DAYS, POINTS):
    h = [band(M, "解答・解説編")]
    h.append(f'<div class="intro"><b>使い方：</b>{esc(M["kaisetsu_intro"])}</div>')
    # ★ポイント整理は解答解説編にだけ置く（問題編に置くと答えが印字されてしまう）
    h.append('<div class="plabel">教科別 やり直しのポイント（解き終わってから読む）</div>')
    for p in POINTS:
        b = [f'<div class="pbox"><div class="pbh">{esc(p["h"])}</div>']
        if p.get("body"):
            b.append(f'<div class="pbody">{esc(p["body"])}</div>')
        if p.get("list"):
            b.append('<div class="plist">' +
                     "".join(f'<div>{esc(x)}</div>' for x in p["list"]) + '</div>')
        if p.get("rule"):
            b.append(f'<div class="prule">★ {esc(p["rule"])}</div>')
        b.append('</div>')
        h.append("".join(b))
    for i, D in enumerate(DAYS):
        # ★DAY1 だけ改ページしないと、ポイント整理と同じページに帯が乗り、
        #   柱が「DAY 1」なのに中身の大半はポイント整理、という食い違いになる。
        h.append(day_key(D))
    h.append(foot(M, "解答・解説編"))
    return "\n".join(h)


def build_book(M, DAYS, POINTS, outdir=DESKTOP):
    base = f'トリリオン_中学生_夏休み特訓_5科総合'
    q_pdf = os.path.join(outdir, f'{base}_問題編.pdf')
    a_pdf = os.path.join(outdir, f'{base}_解答解説編.pdf')
    fl = "中学生 夏休み特訓プリント［5科総合］"
    # render() は build_common の doc() を使わず body だけ受け取る設計にしたいので、
    # 一時 HTML をここで書き出して Chrome に渡す（build_common.render は BASE_CSS 固定のため）
    _render(build_mondai(M, DAYS), q_pdf, fl + " 問題編")
    _render(build_kaisetsu(M, DAYS, POINTS), a_pdf, fl + " 解答・解説編")
    return q_pdf, a_pdf


def _render(body, out_path, foot_label):
    """build_common.render と同じ処理だが、EXTRA_CSS 入りの doc() を使う。"""
    import subprocess
    import fitz
    from build_common import CHROME, FONT_PATH
    tmp = os.path.join(HERE, "_" + os.path.basename(out_path).replace(".pdf", ".html"))
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(doc(foot_label, body))
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=15000", f"--print-to-pdf={out_path}", "file://" + tmp],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = fitz.open(out_path)
    _font = fitz.Font(fontfile=FONT_PATH)
    cur_day = [None]
    for i, page in enumerate(d):
        n = str(i + 1)
        tw = _font.text_length(n, fontsize=9)
        cx = page.rect.width / 2
        # ★柱（書名）はページ中央のノンブルに届く長さになりうる。実際に化学・物理の
        #   解答解説編で柱が x=311 まで伸び、x=295 のノンブルに16pt重なって
        #   ページ番号が読めなくなっていた。書名の長さは号ごとに変わるので、
        #   刻印する側で「届かない長さまで詰める」のが唯一の恒久策。
        avail = cx - tw / 2 - 8 - 36        # 左マージン36 〜 ノンブルの手前8pt
        label = foot_label
        if _font.text_length(label, fontsize=7.2) > avail:
            while label and _font.text_length(label + "…", fontsize=7.2) > avail:
                label = label[:-1]
            label += "…"
        page.insert_text((cx - tw / 2, page.rect.height - 20), n,
                         fontfile=FONT_PATH, fontname="AU", fontsize=9, color=(0.45, 0.45, 0.45))
        page.insert_text((36, page.rect.height - 20), label,
                         fontfile=FONT_PATH, fontname="AU", fontsize=7.2, color=(0.55, 0.55, 0.55))
        # ★柱の右端に、そのページが何日目かを刻む。31ページの解答解説編に DAY→ページの
        #   手がかりが一切なく、「DAY7の丸つけ」で全ページめくることになっていた。
        #   ページ内の DAY 見出しを拾って持ち越す（HTML側では出せないので刻印でやる）。
        # ★見出しの「DAY n」だけを拾う。素の r"DAY\s*(\d+)" だと、進め方の表や解説本文に出る
        #   「DAY 2」に反応して、1ページ目に DAY 2 と刻まれていた。
        #   見出しは必ず直後に範囲チップ（中1範囲／中2範囲／中3 1学期の範囲）が来る。
        # ★1ページ目の「10日間の進め方」の表も《DAY 1｜中1範囲》の形なので、
        #   範囲チップを条件にしただけでは表の全10行に当たり、表紙の柱が「DAY 10」になる。
        #   DAY帯は 19pt/11.4pt の大きな字で組んでいるので、**字の大きさ**で表と区別する。
        # ★帯の文字は span が「DAY」「 」「5」に割れるので、**行単位**で連結してから見る。
        #   span 単位で正規表現を当てると1件も拾えない（実際にこれで柱が全ページ空になった）。
        heads = []
        for b_ in page.get_text("dict")["blocks"]:
            for ln_ in b_.get("lines", []):
                txt_ = "".join(x["text"] for x in ln_["spans"])
                size_ = max((x["size"] for x in ln_["spans"]), default=0)
                if size_ < 11:                    # 進め方の表は 9pt。帯は 11.4pt / 19pt
                    continue
                m_ = re.match(r"\s*DAY\s*(\d+)", txt_)
                if m_:
                    heads.append(m_.group(1))
        if heads:
            cur_day[0] = heads[-1]
        if cur_day[0]:
            tag = f'DAY {cur_day[0]}'
            tl = _font.text_length(tag, fontsize=7.2)
            page.insert_text((page.rect.width - 36 - tl, page.rect.height - 20), tag,
                             fontfile=FONT_PATH, fontname="AU", fontsize=7.2,
                             color=(0.55, 0.55, 0.55))
    d.subset_fonts()
    tmp2 = out_path + ".tmp"
    d.save(tmp2, garbage=4, deflate=True, clean=True)
    d.close()
    os.replace(tmp2, out_path)
    d = fitz.open(out_path)
    pc = d.page_count
    d.close()
    print(f"WROTE {out_path} | pages: {pc}")
    return pc
