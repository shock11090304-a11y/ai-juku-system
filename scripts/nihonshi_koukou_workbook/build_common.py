# -*- coding: utf-8 -*-
"""
高校日本史 演習プリント  共通ビルダー（単一ソース content → 問題編/解答解説編 の2冊 PDF）

  from build_common import build_book
  build_book(META, PART2)   # ~/Desktop に 問題編.pdf / 解答解説編.pdf

★一問一答（短答）パートは持たない。共通テスト形式の大問（資料読解・選択式）だけを並べる単一パート構成。
  理由: 一問一答で問う用語は、年表・史料・整序問題の中に地名/事件名として必ず literal に登場するため
  （例:「大宝律令」を一問一答で問いつつ、別の大問の年代整序で選択肢に「大宝律令」と印字される）、
  同一冊子内では機械的な文字列一致で解答が漏洩してしまう。二部構成にはせず単一パートに統一した。

HTML → Chrome --headless=new --print-to-pdf → fitz でノンブル刻印。
視覚 ID は scripts/shakai_chiri を踏襲（明朝本文＋ゴシック見出し＋紺バンド）。
雨温図の代わりに「史料・会話文の引用ブロック」を持つ（社会科共通テスト型の大問はこの形が中心）。

■ 問題型（各 dict は "type" を持つ）
  short {"type":"short","q":"...","ans":"...","exp":"..."}                     一問一答（短答）
  mc    {"type":"mc","q":"...","choices":[...],"ans":<0起点idx>,"exp":"...","pt":配点}  四択・正誤組合せ・整序

■ 大問（PART2 の要素）
  {"no":"第1問","title":"...","point":配点,"intro":"リード文(\\nで改行)",
   "figs":[史料ブロックのHTML文字列,...], "qs":[問题dict,...]}
"""
import os, html, subprocess
import fitz
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DESKTOP = os.path.expanduser("~/Desktop")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"

# ---------------------------------------------------------------- 数式の組版マーク
# ★中学教科書・入試は分数を必ず**組分数**（横線の上に分子・下に分母）で組み、根号は
#   **横線が中身に掛かる**。「(x＋2)／3」「√72」のような1行書きは教科書・入試には無い。
#   データは素の文字列なので、esc() のあとで置換できる目印を使う:
#       [[frac:分子|分母]]   →  組分数
#       [[sqrt:中身]]        →  根号（横線が中身を覆う）
#   ★目印は esc() を通しても壊れない文字（[ ] : |）だけで作ってある。
MARK_FRAC = re.compile(r"\[\[frac:([^|\]]+)\|([^\]]+)\]\]")
MARK_SQRT = re.compile(r"\[\[sqrt:([^\]]+)\]\]")


def mathmark(s):
    """esc() 済みの文字列に対して、数式の目印を実際の組版に変える。"""
    # ★根号を先に展開する。[[frac:5±[[sqrt:17]]|2]] のような入れ子があり、
    #   分数を先に処理すると内側の ] で分子の切り出しが壊れる。
    s = MARK_SQRT.sub(r'<span class="radsign">&#8730;</span><span class="rad">\1</span>', s)
    s = MARK_FRAC.sub(
        r'<span class="frac"><span class="num">\1</span>'
        r'<span class="den">\2</span></span>', s)
    return s


_escape = lambda s: html.escape(str(s), quote=False)
# ★esc() 自体に数式マークの展開を通す。個々の描画関数に足して回ると必ず抜けが出る
#   （設問文では組分数になるのに選択肢では [[frac:…]] が生で出る、という事故）。
esc = lambda s: mathmark(_escape(s))
CIRCLE = ["①", "②", "③", "④", "⑤", "⑥"]


def _nl(s):
    """esc してから改行を <br> に変える（会話文・史料の複数行表示用）。"""
    return esc(s).replace("\n", "<br>")


# ---------------------------------------------------------------- 史料・会話文ブロック
def shiryo(caption, text):
    """史料（現代語訳）の引用ブロック。text 中の <u>...</u> はそのまま下線として通す
    （史実の下線部指定に使うため esc しない＝呼び出し側で & < > を混入させないこと）。"""
    return (f'<div class="shiryo"><div class="scap">{esc(caption)}</div>'
            f'<div class="stext">{text}</div></div>')


def kaiwa(lines):
    """会話文ブロック。lines = [(話者, セリフ), ...]。"""
    rows = "".join(f'<div class="krow"><span class="who">{esc(w)}</span>'
                   f'<span class="say">{_nl(t)}</span></div>' for w, t in lines)
    return f'<div class="kaiwa">{rows}</div>'


def nenpyo(caption, rows):
    """年表（年代・出来事の2列表）。rows = [(年, 出来事), ...]。"""
    h = [f'<div class="tbl"><div class="tcap">{esc(caption)}</div>',
         '<table class="stat"><tr><th>年代</th><th>できごと</th></tr>']
    for y, e in rows:
        h.append(f'<tr><td class="c">{esc(y)}</td><td class="l">{esc(e)}</td></tr>')
    h.append('</table></div>')
    return "".join(h)


# ---------------------------------------------------------------- CSS
BASE_CSS = """
* { box-sizing: border-box; }
@page { size: A4; margin: 13mm 12mm 15mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family:"Hiragino Mincho ProN","Yu Mincho",serif; color:#1a1a1a; font-size:10.2pt;
  line-height:1.62; margin:0; font-variant-numeric: lining-nums; font-feature-settings:"lnum" 1; }
.gothic,h1,h2,h3,.band,.qno,.secttl,.partdiv,.bigno,.plabel,.pbh,.tier,.foot,.tcap,.who,.slotlbl,.scap
  { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }

/* ヘッダバンド */
.band { background:linear-gradient(90deg,#0f172a,#7c2d12); color:#fff; padding:10px 15px;
  border-radius:9px; display:flex; justify-content:space-between; align-items:center; }
.band .l { font-size:15pt; font-weight:700; letter-spacing:.02em; }
.band .l small { font-weight:600; font-size:9.4pt; opacity:.92; margin-left:8px; }
.band .r { text-align:right; font-size:8.8pt; line-height:1.45; }
.band .r b { font-size:12pt; }

.intro { border:1px solid #cbd5e1; border-radius:8px; padding:8px 13px; margin:9px 0 4px;
  font-size:9.4pt; line-height:1.7; color:#334155; }
.intro b { color:#0f172a; }
.metarow { display:flex; gap:9px; margin:8px 0 6px; font-size:9.3pt; }
.metarow .cell { border:1px solid #cbd5e1; border-radius:6px; padding:4px 10px; flex:1; }
.metarow .cell.score { flex:0 0 132px; text-align:center; }

/* 大問 */
.big { margin:11px 0 0; page-break-inside:auto; }
.bighd { display:flex; align-items:baseline; gap:9px; border-bottom:2.2px solid #7c2d12;
  padding-bottom:4px; margin:9px 0 5px; page-break-after:avoid; }
.bigno { background:#0f172a; color:#fff; border-radius:6px; padding:2px 11px; font-size:10.5pt;
  font-weight:700; white-space:nowrap; }
.bigttl { font-size:12.5pt; font-weight:700; color:#0f172a; }
.bigpt { margin-left:auto; font-size:8.6pt; color:#dc2626; font-weight:700; white-space:nowrap; }
.instr { font-size:9.2pt; background:#f1f5f9; border-left:4px solid #7c2d12; padding:6px 10px;
  border-radius:4px; margin:5px 0 8px; color:#334155; line-height:1.6; }
.glue { break-inside:avoid; page-break-inside:avoid; }

/* 会話文 */
.kaiwa { margin:5px 0 8px; page-break-inside:avoid; }
.krow { display:flex; gap:8px; padding:2px 0; font-size:9.6pt; line-height:1.6; }
.krow .who { flex:0 0 68px; font-weight:700; color:#7c2d12; }
.krow .say { flex:1; }

/* 史料引用 */
.shiryo { border:1px solid #e2c9a0; background:#fdf8ee; border-left:5px solid #b45309;
  border-radius:6px; padding:7px 12px; margin:6px 0 9px; page-break-inside:avoid; }
.scap { font-size:9pt; font-weight:700; color:#92400e; margin-bottom:3px; }
.stext { font-size:9.4pt; line-height:1.72; color:#1f2937; }
.stext u { text-decoration-thickness:1.6px; text-underline-offset:2px; }

/* 一問一答 */
.qagrp { font-size:10.3pt; font-weight:700; color:#fff; background:#7c2d12; border-radius:5px;
  padding:2px 12px; margin:11px 0 5px; display:inline-block; page-break-after:avoid; }
.qarow { display:flex; align-items:baseline; gap:7px; padding:2.4px 0; font-size:9.7pt;
  border-bottom:1px dotted #dbe3ef; page-break-inside:avoid; }
.qarow .n { flex:0 0 30px; color:#7c2d12; font-weight:700;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:9pt; }
.qarow .t { flex:1; }
.qarow .b { flex:0 0 118px; border-bottom:1.2px solid #94a3b8; height:14px; }

/* 設問 */
.q { margin:0 0 8px; page-break-inside:avoid; }
.q .h { display:flex; align-items:baseline; gap:7px; }
.qno { background:#0f172a; color:#fff; border-radius:5px; padding:1px 9px; font-size:8.8pt;
  font-weight:700; white-space:nowrap; }
.q .stem { flex:1; font-size:9.9pt; }
.q .choices div { margin:2px 0 1px 12px; font-size:9.6pt; }
.qpt { flex:0 0 auto; color:#dc2626; font-size:8.2pt; font-weight:700; white-space:nowrap;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.ansline { margin:4px 0 0 12px; display:flex; align-items:baseline; gap:6px; font-size:9.4pt; }
.ansline .bl { flex:0 0 70px; border-bottom:1.2px solid #94a3b8; height:15px; }

/* 年表 */
.tbl { margin:6px 0 8px; page-break-inside:avoid; }
.tcap { font-size:9.3pt; font-weight:700; color:#0f172a; margin-bottom:3px; }
table.stat { width:100%; border-collapse:collapse; font-size:9.2pt; }
table.stat th, table.stat td { border:1px solid #cbd5e1; padding:3px 7px; }
table.stat th { background:#fdf1e3; font-family:"Hiragino Kaku Gothic ProN",sans-serif;
  text-align:center; font-size:8.9pt; }
table.stat td.c { text-align:center; white-space:nowrap; }
table.stat td.l { text-align:left; }

/* 解答解説編 */
.secttl { font-size:12.5pt; font-weight:700; color:#0f172a; border-left:6px solid #7c2d12;
  padding:3px 0 3px 10px; margin:0 0 8px; page-break-after:avoid; }
.secttl .en2 { font-size:8.8pt; color:#64748b; font-weight:600; margin-left:8px; }
table.ans { width:100%; border-collapse:collapse; font-size:8.9pt; margin:2px 0 8px; }
table.ans.fixed { table-layout:fixed; margin:0 0 -1px; }
table.ans.fixed th { width:44px; }
table.ans th, table.ans td { border:1px solid #cbd5e1; padding:3px 4px; text-align:center;
  vertical-align:middle; word-break:keep-all; }
table.ans th { background:#fdf1e3; font-family:"Hiragino Kaku Gothic ProN",sans-serif;
  white-space:nowrap; font-size:8.4pt; }
table.ans td.a { font-weight:700; color:#7c2d12; }
.ex { border:1px solid #e2e8f0; border-left:4px solid #7c2d12; border-radius:6px; padding:6px 11px;
  margin:5px 0; page-break-inside:avoid; }
.ex .exh { display:flex; align-items:baseline; gap:8px; margin-bottom:2px; flex-wrap:wrap; }
.ex .exno { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; color:#0f172a;
  white-space:nowrap; }
.ex .exa { font-weight:700; color:#7c2d12; }
.ex .exbody { font-size:9.3pt; color:#1f2937; line-height:1.6; margin-top:2px; }

/* 組分数と根号（中学教科書・入試の組み方） */
.frac { display:inline-block; vertical-align:-0.42em; text-align:center; margin:0 2px;
  line-height:1.15; }
.frac .num { display:block; border-bottom:1.1px solid currentColor; padding:0 3px; }
.frac .den { display:block; padding:0 3px; }
.radsign { margin-right:-1px; }
.rad { border-top:1.1px solid currentColor; padding:0 2px 0 1px; }

/* 奥付だけが最終ページに独りで飛ぶのを防ぐ */
.foot { text-align:center; color:#64748b; font-size:8.1pt; margin-top:7px; padding-top:4px;
  border-top:1px solid #e2e8f0; page-break-inside:avoid;
  break-before:avoid; page-break-before:avoid; }
"""


# ---------------------------------------------------------------- 部品
def band(M, sub):
    return (f'<div class="band"><div class="l">{esc(M["title"])}'
            f'<small>{esc(M["subtitle"])}</small></div>'
            f'<div class="r"><b>{esc(sub)}</b><br>{esc(M["level"])}</div></div>')


def meta_row(M):
    return ('<div class="metarow">'
            f'<div class="cell">氏名　　　　　　　　　　　　　　　</div>'
            f'<div class="cell">実施日　　　　月　　　日</div>'
            f'<div class="cell score">得点　　　／{M["total"]}点</div></div>')


def foot(M, label):
    return (f'<div class="foot">{esc(M["title"])}　{esc(label)}　'
            f'／　{esc(M["org"])}　{esc(M["stat_note"])}</div>')


def _q_body(q):
    if q["type"] == "mc":
        return ('<div class="choices">' +
                "".join(f'<div>{CIRCLE[i]}　{esc(c)}</div>' for i, c in enumerate(q["choices"])) +
                '</div><div class="ansline"><span>答</span><span class="bl"></span></div>')
    return '<div class="ansline"><span>答</span><span class="bl"></span></div>'


def q_problem(q, no):
    pt = f'<span class="qpt">{q["pt"]}点</span>' if q.get("pt") else ""
    return (f'<div class="q"><div class="h"><span class="qno">{esc(no)}</span>'
            f'<span class="stem">{esc(q["q"])}</span>{pt}</div>{_q_body(q)}</div>')


def big_block(b):
    h = [f'<div class="big"><div class="bighd"><span class="bigno">{esc(b["no"])}</span>'
         f'<span class="bigttl">{esc(b["title"])}</span>'
         f'<span class="bigpt">配点 {b["point"]}点</span></div>']
    if b.get("intro"):
        h.append(f'<div class="instr">{_nl(b["intro"])}</div>')
    for blk in b.get("figs", []):
        h.append(blk)
    for i, q in enumerate(b["qs"], start=1):
        h.append(q_problem(q, f'問{i}'))
    h.append('</div>')
    return "".join(h)


# ---------------------------------------------------------------- 問題編
def build_mondai(M, PART2):
    h = [band(M, "問題編"), meta_row(M)]
    h.append(f'<div class="intro"><b>この演習の進め方：</b>{esc(M["intro"])}</div>')
    for b in PART2:
        h.append(big_block(b))
    h.append(foot(M, "問題編"))
    return "\n".join(h)


# ---------------------------------------------------------------- 解答解説編
def _fmt_ans(q):
    return CIRCLE[q["ans"]] + "　" + esc(q["choices"][q["ans"]])


def build_kaisetsu(M, PART2):
    h = [band(M, "解答・解説編")]
    h.append(f'<div class="intro"><b>使い方：</b>{esc(M["kaisetsu_intro"])}</div>')
    for b in PART2:
        h.append(f'<div class="secttl">{esc(b["no"])}　{esc(b["title"])}'
                 f'<span class="en2">配点 {b["point"]}点</span></div>')
        for i, q in enumerate(b["qs"], start=1):
            h.append(f'<div class="ex"><div class="exh"><span class="exno">問{i}</span>'
                     f'<span class="exa">{_fmt_ans(q)}</span></div>'
                     f'<div class="exbody">{esc(q["exp"])}</div></div>')

    h.append(foot(M, "解答・解説編"))
    return "\n".join(h)


# ---------------------------------------------------------------- 出力
def doc(title, body):
    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<title>{esc(title)}</title><style>{BASE_CSS}</style></head><body>{body}</body></html>')


def render(body, out_path, foot_label):
    tmp = os.path.join(HERE, "_" + os.path.basename(out_path).replace(".pdf", ".html"))
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(doc(foot_label, body))
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=15000", f"--print-to-pdf={out_path}", "file://" + tmp],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = fitz.open(out_path)
    for i, page in enumerate(d):
        n = str(i + 1)
        tw = fitz.Font(fontfile=FONT_PATH).text_length(n, fontsize=9)
        page.insert_text((page.rect.width / 2 - tw / 2, page.rect.height - 20), n,
                         fontfile=FONT_PATH, fontname="AU", fontsize=9, color=(0.45, 0.45, 0.45))
        page.insert_text((36, page.rect.height - 20), foot_label,
                         fontfile=FONT_PATH, fontname="AU", fontsize=7.2, color=(0.55, 0.55, 0.55))
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


def build_book(M, PART2, outdir=DESKTOP):
    base = f'高校日本史_演習_{M["no"]}'
    q_pdf = os.path.join(outdir, f'{base}_問題編.pdf')
    a_pdf = os.path.join(outdir, f'{base}_解答解説編.pdf')
    fl = f'高校日本史 演習 {M["subtitle"]}'
    render(build_mondai(M, PART2), q_pdf, fl + " 問題編")
    render(build_kaisetsu(M, PART2), a_pdf, fl + " 解答・解説編")
    return q_pdf, a_pdf
