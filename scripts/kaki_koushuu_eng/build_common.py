# -*- coding: utf-8 -*-
"""
トリリオン夏期講習 英語  共通ビルダー（単一ソース content → 問題編/解答解説編 の2冊 PDF）

  from build_common import build_book
  build_book(META, GRAMMAR, READING)   # ~/Desktop に 問題編.pdf / 解答解説編.pdf を出力

HTML → Chrome --headless=new --print-to-pdf → fitz でノンブル刻印。
視覚 ID は eng_therules / eng_march_gw を踏襲（ミンチョ本文＋ゴシック見出し＋Georgia英文＋紺バンド）。

■ 問題型（各 dict は "type" を持つ）
  mc      {"type":"mc","stem":"...","choices":[...],"ans":<0起点idx>,"point":"...","exp":"..."}
          stem 中の ______ は空所、( hint ) は斜体ヒント。
  fill    {"type":"fill","stem":"...______...","ans":"was","point":"...","exp":"..."}
  order   {"type":"order","ja":"...","tokens":[...],"ans":"完成文（末尾ピリオド無し）","point":"...","exp":"..."}
  error   {"type":"error","html":"[a|..] .. [b|..]","ans":"c","correct":"x→y","point":"...","exp":"..."}
  rewrite {"type":"rewrite","given":"...","target":"...______...","blanks":[...],"point":"...","exp":"..."}
  ja2en   {"type":"ja2en","ja":"...","models":["...","..."],"point":"...","mistakes":"...","lines":2}
  rc_mc   {"type":"rc_mc","q":"設問(日本語)","choices":[...],"ans":<idx>,"exp":"..."}
  rc_desc {"type":"rc_desc","q":"設問(日本語)","ans":"模範解答","exp":"...","lines":2}

■ ポイント（points 要素）
  {"h":"見出し","body":"説明","ex":[["English","和訳"],...],"rule":"★一言ルール(任意)"}
"""
import os, re, sys, html, subprocess
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

BASE_CSS = """
* { box-sizing: border-box; }
@page { size: A4; margin: 14mm 13mm 16mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family:"Hiragino Mincho ProN","Yu Mincho",serif; color:#1a1a1a; font-size:10.3pt; line-height:1.6; margin:0;
  font-variant-numeric: lining-nums; font-feature-settings:"lnum" 1, "tnum" 0; }
.gothic { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }
/* Georgia は既定が旧字体(オールドスタイル)数字で 3/4/5 等が baseline 下に沈み『数字が跳ねる』ため、
   lining-nums（等高数字）を全体に強制する。 */
.en { font-family:Georgia,"Times New Roman",serif; font-variant-numeric: lining-nums; font-feature-settings:"lnum" 1; }
.enj { font-family:"Hiragino Mincho ProN","Yu Mincho",serif; }  /* CJK混じり用（等高数字で数字が跳ねない） */
h1,h2,h3,.band,.qno,.pts,.secttl,.partttl,.tier,.foot,.pbh,.plabel,.vhd { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }

/* header band */
.band { background:linear-gradient(90deg,#0f172a,#1e3a8a); color:#fff; padding:10px 15px; border-radius:9px;
  display:flex; justify-content:space-between; align-items:center; }
.band .l { font-size:15pt; font-weight:700; letter-spacing:.02em; }
.band .l small { font-weight:600; font-size:9.5pt; opacity:.92; margin-left:8px; }
.band .r { text-align:right; font-size:9pt; line-height:1.45; }
.band .r b { font-size:12.5pt; }

/* course intro */
.intro { border:1px solid #cbd5e1; border-radius:8px; padding:9px 13px; margin:9px 0 4px; font-size:9.5pt; line-height:1.7; color:#334155; }
.intro b { color:#0f172a; }
.introrow { display:flex; gap:10px; margin:8px 0 2px; }
.introrow .cell { flex:1; border:1px solid #cbd5e1; border-radius:6px; padding:5px 10px; font-size:9.3pt; }
.introrow .cell b { color:#1e3a8a; }
.metarow { display:flex; gap:10px; margin:9px 0 6px; font-size:9.5pt; }
.metarow .cell { border:1px solid #cbd5e1; border-radius:6px; padding:4px 10px; flex:1; }
.metarow .cell.score { flex:0 0 140px; text-align:center; }

/* 編 divider (英文法編 / 英語長文編) */
.partdiv { background:#1e3a8a; color:#fff; border-radius:8px; padding:12px 16px; margin:16px 0 4px; page-break-before:always; page-break-after:avoid; }
.partdiv.first { page-break-before:auto; margin-top:10px; }
.partdiv .pt1 { font-size:16pt; font-weight:700; }
.partdiv .pt2 { font-size:9.5pt; opacity:.92; margin-top:3px; }

/* session header */
.sess { page-break-before:always; }
.sess.first { page-break-before:auto; }
.sesshd { display:flex; align-items:baseline; gap:10px; border-bottom:2.4px solid #1e3a8a; padding-bottom:5px; margin:6px 0 3px; page-break-after:avoid; }
.sesshd .sno { background:#0f172a; color:#fff; border-radius:6px; padding:2px 11px; font-size:11pt; font-weight:700; font-family:"Hiragino Kaku Gothic ProN",sans-serif; white-space:nowrap; }
.sesshd .sttl { font-size:14pt; font-weight:700; color:#0f172a; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.sesshd .sdate { margin-left:auto; font-size:9pt; color:#64748b; white-space:nowrap; }
.goal { font-size:9.5pt; color:#334155; background:#f1f5f9; border-left:4px solid #1e3a8a; padding:5px 10px; border-radius:4px; margin:5px 0 9px; }
.goal b { color:#0f172a; }

/* ポイント整理 */
.plabel { font-size:11pt; font-weight:700; color:#0f172a; margin:11px 0 5px; page-break-after:avoid; }
.plabel .en2 { font-size:8.5pt; color:#64748b; margin-left:7px; font-weight:600; }
.pbox { border:1px solid #dbe3ef; border-left:4px solid #2563eb; border-radius:7px; padding:7px 12px; margin:0 0 8px; page-break-inside:avoid; }
.pbh { font-weight:700; font-size:10.3pt; color:#1e3a8a; margin-bottom:2px; }
.pbody { font-size:9.6pt; line-height:1.65; color:#1f2937; }
.pex { margin:4px 0 0; }
.pex .row { display:flex; gap:8px; margin:2px 0; font-size:9.5pt; align-items:baseline; }
.pex .e { font-family:Georgia,serif; color:#0f172a; }
.pex .j { color:#475569; font-size:9pt; }
.prule { margin-top:4px; font-size:9.3pt; color:#b91c1c; font-weight:700; }

/* tier label (基礎問 / 標準問題 / 入試チャレンジ) */
.tier { display:inline-block; color:#fff; border-radius:5px; padding:2px 12px; font-size:10pt; font-weight:700; margin:12px 0 6px; page-break-after:avoid; }
.tier.kiso { background:#047857; }
.tier.hyojun { background:#1e3a8a; }
.tier.nyushi { background:#9a3412; }
.tier .en2 { font-size:8pt; opacity:.9; margin-left:6px; font-weight:600; }
.tier .cnt { font-size:8pt; opacity:.9; margin-left:6px; }
.tglue { break-inside:avoid; page-break-inside:avoid; }  /* ティア見出し＋最初の1問を同ページに束ねる */

/* part title (long-passage 設問群) */
.partttl { font-size:11.5pt; font-weight:700; color:#fff; background:#1e3a8a; border-radius:6px; padding:4px 12px; margin:12px 0 7px; page-break-after:avoid; }
.instr { font-size:9.2pt; background:#f1f5f9; border-left:4px solid #1e3a8a; padding:6px 10px; border-radius:4px; margin:6px 0 9px; color:#334155; line-height:1.6; }

/* question block */
.q { margin:0 0 9px; page-break-inside:avoid; }
.q .h { display:flex; align-items:baseline; gap:8px; }
.qno { background:#0f172a; color:#fff; border-radius:5px; padding:1px 9px; font-size:9pt; font-weight:700; white-space:nowrap; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.qno.kiso { background:#047857; } .qno.hyojun { background:#1e3a8a; } .qno.nyushi { background:#9a3412; }
.pts { color:#dc2626; font-size:8.2pt; font-weight:700; }
.q .stem { margin:3px 0 2px; font-size:10pt; }
.q .stem .en, .q .stem .enj { font-size:10.2pt; }
.q .jp { font-size:9.4pt; color:#475569; margin:1px 0 3px; }
.q .choices div { margin:2px 0 1px 10px; font-size:9.8pt; }
.q .choices .en, .q .choices .enj { font-size:10pt; }
.fill { display:inline-block; min-width:70px; border-bottom:1.5px solid #0f172a; text-align:center; font-weight:700; }
.fill.wide { min-width:130px; }
.hint { font-style:italic; color:#475569; }

/* word-order chips */
.words { display:flex; flex-wrap:wrap; gap:6px; margin:4px 0 4px 10px; }
.wchip { border:1px solid #94a3b8; background:#f8fafc; border-radius:5px; padding:1.5px 9px; font-family:Georgia,serif; font-size:9.8pt; }
.ansbox { border:1px solid #94a3b8; border-radius:6px; min-height:30px; margin:4px 0 0 10px; }

/* error-spotting */
.errsent { font-family:Georgia,serif; font-size:10.2pt; line-height:1.95; margin:2px 0 3px; }
.emk { border-bottom:1.7px solid #dc2626; padding-bottom:1px; white-space:nowrap; }
.emk sup { color:#dc2626; font-weight:700; font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin-right:1px; }
.pick { font-size:9.3pt; color:#334155; margin:2px 0 0 10px; }
.pick .fill { min-width:40px; }

/* rewrite */
.rw .give { font-family:Georgia,serif; font-size:10pt; margin:2px 0 2px; }
.rw .tgt { font-family:Georgia,serif; font-size:10pt; margin:1px 0 2px; color:#0f172a; }

/* writing / descriptive answer lines */
.wl { border-bottom:1px solid #cbd5e1; height:20px; margin:0; }
.wlbox { margin:5px 0 2px 10px; }
.jline { border-bottom:1px solid #cbd5e1; height:22px; margin:0; }

/* passage */
.ptitle { text-align:center; font-size:12.5pt; font-weight:700; margin:8px 0 1px; font-family:Georgia,serif; }
.pjtitle { text-align:center; font-size:8.7pt; color:#64748b; margin-bottom:6px; }
.passage { border:1.2px solid #94a3b8; border-radius:8px; padding:10px 15px; }
.passage p { margin:0 0 7px; }
.passage .en { line-height:2.02; text-align:justify; font-size:10.4pt; }
.passage sup.sn { color:#dc2626; font-weight:700; font-size:7.5pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin-right:1px; }
.passage .ul { border-bottom:1.4px solid #1f2937; padding-bottom:1px; }
.wcount { text-align:right; color:#64748b; font-size:8.5pt; margin-top:2px; }

/* vocab table */
.vhd { font-size:10pt; font-weight:700; color:#0f172a; margin:9px 0 3px; page-break-after:avoid; }
table.vocab { width:100%; border-collapse:collapse; font-size:9pt; page-break-inside:avoid; }
table.vocab td { border:1px solid #cbd5e1; padding:3px 8px; vertical-align:top; }
table.vocab td.w { font-family:Georgia,serif; font-weight:700; white-space:nowrap; color:#0f172a; }
table.vocab td.p { color:#64748b; white-space:nowrap; font-size:8.4pt; }

/* answer/explanation (解答解説編) */
.secttl { font-size:13pt; font-weight:700; color:#0f172a; border-left:6px solid #1e3a8a; padding:3px 0 3px 10px; margin:0 0 9px; page-break-after:avoid; }
.secttl .en2 { font-size:9pt; color:#64748b; font-weight:600; margin-left:8px; }
.pb { page-break-before:always; }
table.ans { width:100%; border-collapse:collapse; font-size:9.1pt; margin:2px 0 8px; }
table.ans th, table.ans td { border:1px solid #cbd5e1; padding:4px 6px; vertical-align:middle; text-align:center; }
table.ans th { background:#eef2ff; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
table.ans td.a { font-weight:700; color:#1e3a8a; font-family:Georgia,serif; }
.ex { border:1px solid #e2e8f0; border-left:4px solid #1e3a8a; border-radius:6px; padding:6px 11px; margin:6px 0; page-break-inside:avoid; }
.ex .exh { display:flex; align-items:baseline; gap:8px; margin-bottom:2px; flex-wrap:wrap; }
.ex .exno { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; color:#0f172a; white-space:nowrap; }
.ex .exa { font-family:Georgia,serif; font-weight:700; color:#1e3a8a; }
.ex .exa .jp { font-family:"Hiragino Mincho ProN",serif; color:#334155; font-weight:400; }
.ex .tag { display:inline-block; background:#fde68a; color:#7c2d12; font-weight:700; border-radius:4px; padding:0 7px; font-size:8.3pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.ex .exbody { font-size:9.4pt; color:#1f2937; line-height:1.62; }
.ex .exbody .en { font-family:Georgia,serif; }
.wcard { border:1px solid #cbd5e1; border-left:4px solid #047857; border-radius:6px; padding:7px 11px; margin:8px 0; page-break-inside:avoid; }
.wcard .wh { font-weight:700; font-size:10pt; color:#065f46; margin-bottom:3px; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.wcard .jp { font-size:9.5pt; color:#334155; margin-bottom:4px; }
.wcard .model { background:#f0fdf4; border-radius:4px; padding:5px 9px; margin:4px 0; font-family:Georgia,serif; font-size:9.9pt; line-height:1.5; }
.wcard .model .ml { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:8.3pt; color:#047857; font-weight:700; display:block; margin-bottom:1px; }
.wcard .pt { font-size:9pt; color:#334155; margin-top:3px; }
.wcard .pt b { color:#065f46; }
.wcard .miss { font-size:9pt; color:#7c2d12; background:#fff7ed; border-radius:4px; padding:4px 8px; margin-top:4px; }
.trbox { font-size:9.4pt; }
.trbox .tr1 { margin:0 0 4px; }
.trbox .sn2 { color:#dc2626; font-weight:700; font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:8.3pt; margin-right:2px; }

.foot { text-align:center; color:#64748b; font-size:8.2pt; margin-top:12px; padding-top:5px; border-top:1px solid #e2e8f0; page-break-inside:avoid; }
"""

MARK = re.compile(r'\[([a-e])\|([^\]]+)\]')
_TITLE_PREFIX = re.compile(r'^\s*第\s*\d+\s*講[\s　:：・]*')


def clean_title(t):
    """タイトル先頭に紛れ込んだ『第N講』を除去（ヘッダ側で別途『第N講』を付けるため重複を防ぐ）。"""
    return _TITLE_PREFIX.sub('', str(t))


CJK_RE = re.compile(r'[぀-ヿ㐀-鿿＀-￯　-〿]')


def en(s, wide=False):
    """英文を Georgia 表示。______ は空所、( hint ) は斜体。
    ★ CJK（例:「第1文型」）を含む文字列は Georgia の旧字体数字(3/4等が沈む)で数字が跳ねるので、
      明朝(等高数字)で組む .enj に切り替える。"""
    body = esc(s)
    cls = "fill wide" if wide else "fill"
    body = body.replace("______", f'<span class="{cls}">&nbsp;</span>')
    body = re.sub(r'\(\s*([A-Za-z][A-Za-z\s/\'.-]*?)\s*\)', r'<span class="hint">( \1 )</span>', body)
    span = "enj" if CJK_RE.search(s) else "en"
    return f'<span class="{span}">{body}</span>'


def error_sentence(s):
    def rep(m):
        return f'<span class="emk"><sup>({m.group(1)})</sup>{esc(m.group(2))}</span>'
    out, last = [], 0
    for m in MARK.finditer(s):
        out.append(esc(s[last:m.start()]))
        out.append(rep(m))
        last = m.end()
    out.append(esc(s[last:]))
    return f'<div class="errsent">{"".join(out)}</div>'


def error_correct_html(s):
    """誤り指摘の下線を除いた正しい英文（解答側の参考表示）。"""
    return MARK.sub(lambda m: m.group(2), s)


def pointbox(points):
    out = ['<div class="plabel">ポイント整理<span class="en2">Key Points</span></div>']
    for p in points:
        h = [f'<div class="pbox"><div class="pbh">{esc(p["h"])}</div>']
        if p.get("body"):
            h.append(f'<div class="pbody">{esc(p["body"])}</div>')
        if p.get("ex"):
            h.append('<div class="pex">')
            for pair in p["ex"]:
                e, j = (pair + ["", ""])[:2]
                h.append(f'<div class="row"><span class="e">{esc(e)}</span>'
                         f'<span class="j">{esc(j)}</span></div>')
            h.append('</div>')
        if p.get("rule"):
            h.append(f'<div class="prule">★ {esc(p["rule"])}</div>')
        h.append('</div>')
        out.append("".join(h))
    return "\n".join(out)


# ---------------- 問題編: grammar question renderers ----------------
def q_problem(q, no, tier):
    t = q["type"]
    head = f'<div class="q"><div class="h"><span class="qno {tier}">{esc(no)}</span></div>'
    if t == "mc":
        h = head + f'<div class="stem">{en(q["stem"])}</div>'
        if q.get("note"):
            h += f'<div class="jp">（{esc(q["note"])}）</div>'
        h += '<div class="choices">'
        for j, c in enumerate(q["choices"]):
            h += f'<div>{CIRCLE[j]} {en(c)}</div>'
        return h + '</div></div>'
    if t == "fill":
        h = head + f'<div class="stem">{en(q["stem"], wide=True)}</div>'
        if q.get("note"):
            h += f'<div class="jp">（{esc(q["note"])}）</div>'
        return h + '</div>'
    if t == "order":
        h = head + f'<div class="jp">{esc(q["ja"])}</div>'
        h += '<div class="words">' + "".join(f'<span class="wchip">{esc(w)}</span>' for w in q["tokens"]) + '</div>'
        return h + '<div class="ansbox"></div></div>'
    if t == "error":
        h = head + error_sentence(q["html"])
        return h + '<div class="pick">誤り＝（　<span class="fill">&nbsp;</span>　）</div></div>'
    if t == "rewrite":
        h = head + f'<div class="rw"><div class="give">{en(q["given"])}</div>'
        return h + f'<div class="tgt">＝ {en(q["target"])}</div></div></div>'
    if t == "ja2en":
        h = head + f'<div class="jp">{esc(q["ja"])}</div>'
        lines = q.get("lines", 2)
        h += '<div class="wlbox">' + '<div class="wl"></div>' * lines + '</div>'
        return h + '</div>'
    raise ValueError(f"unknown grammar q type: {t}")


# ---------------- 解答解説編: grammar answer renderers ----------------
def q_answer(q, no):
    t = q["type"]
    if t == "mc":
        ci = q["ans"]
        exa = f'正解 {CIRCLE[ci]}　{esc(q["choices"][ci])}'
        return (f'<div class="ex"><div class="exh"><span class="exno">{esc(no)}</span>'
                f'<span class="exa">{exa}</span><span class="tag">{esc(q.get("point",""))}</span></div>'
                f'<div class="exbody">{esc(q["exp"])}</div></div>')
    if t == "fill":
        return (f'<div class="ex"><div class="exh"><span class="exno">{esc(no)}</span>'
                f'<span class="exa">{esc(q["ans"])}</span><span class="tag">{esc(q.get("point",""))}</span></div>'
                f'<div class="exbody">{esc(q["exp"])}</div></div>')
    if t == "order":
        return (f'<div class="ex"><div class="exh"><span class="exno">{esc(no)}</span>'
                f'<span class="tag">{esc(q.get("point",""))}</span></div>'
                f'<div class="exbody"><b>完成文：</b><span class="en">{esc(q["ans"])}.</span><br>{esc(q["exp"])}</div></div>')
    if t == "error":
        return (f'<div class="ex"><div class="exh"><span class="exno">{esc(no)}</span>'
                f'<span class="exa">正解 ({esc(q["ans"])})　{esc(q["correct"])}</span>'
                f'<span class="tag">{esc(q.get("point",""))}</span></div>'
                f'<div class="exbody">{esc(q["exp"])}</div></div>')
    if t == "rewrite":
        filled = q["target"]
        for b in q["blanks"]:
            filled = filled.replace("______", b, 1)
        return (f'<div class="ex"><div class="exh"><span class="exno">{esc(no)}</span>'
                f'<span class="exa">{esc(" / ".join(q["blanks"]))}</span>'
                f'<span class="tag">{esc(q.get("point",""))}</span></div>'
                f'<div class="exbody"><span class="en">{esc(filled)}</span><br>{esc(q["exp"])}</div></div>')
    if t == "ja2en":
        h = f'<div class="wcard"><div class="wh">{esc(no)}　和文英訳</div><div class="jp">{esc(q["ja"])}</div>'
        for mi, mdl in enumerate(q["models"], start=1):
            lab = "解答例" + (f"{mi}" if len(q["models"]) > 1 else "")
            h += f'<div class="model"><span class="ml">{lab}</span>{esc(mdl)}</div>'
        if q.get("point"):
            h += f'<div class="pt"><b>採点ポイント：</b>{esc(q["point"])}</div>'
        if q.get("mistakes"):
            h += f'<div class="miss">▲ よくあるミス：{esc(q["mistakes"])}</div>'
        return h + '</div>'
    raise ValueError(f"unknown grammar q type: {t}")


# ---------------- reading renderers ----------------
UL_SENT_RE = re.compile(r'文\s*[\(（]\s*(\d+)')
# 下線部 の直後（『（文(N)）』や『 』などの非英字を最大8字スキップ）から始まる英語句を拾う。
UL_PHRASE_RE = re.compile(r'下線部[^A-Za-z]{0,8}([A-Za-z][A-Za-z0-9 ,.\'’\-]*[A-Za-z0-9.’])')


def extract_underlines(questions):
    """設問文が『文(N)の下線部 <English>』の形なら、その英語句を該当文で下線するための {n:[phrase]} を返す。"""
    res = {}
    for q in (questions or []):
        qt = q.get("q", "")
        if "下線部" not in qt:
            continue
        mn = UL_SENT_RE.search(qt)
        mp = UL_PHRASE_RE.search(qt)
        if not (mn and mp):
            continue
        ph = mp.group(1).strip().strip(",")
        res.setdefault(int(mn.group(1)), []).append(ph)
    return res


def render_sentence(text, phrases):
    """text 内の phrases を（完全一致のみ）下線 span で包む。見つからなければ無害にそのまま。"""
    if not phrases:
        return esc(text)
    out, tokens = text, {}
    for i, ph in enumerate(phrases):
        if ph and ph in out:
            tok = f"\x00U{i}\x00"
            out = out.replace(ph, tok, 1)
            tokens[tok] = ph
    out = esc(out)
    for tok, ph in tokens.items():
        out = out.replace(tok, f'<span class="ul">{esc(ph)}</span>')
    return out


def passage_html(p, questions=None):
    uls = extract_underlines(questions)
    parts = [f'<div class="ptitle">{esc(p["title"])}</div>']
    if p.get("jtitle"):
        parts.append(f'<div class="pjtitle">{esc(p["jtitle"])}</div>')
    parts.append('<div class="passage">')
    n = 0
    total_words = 0
    for para in p["paras"]:
        buf = []
        for s in para:
            n += 1
            total_words += len(re.split(r"\s+", s.strip()))
            buf.append(f'<sup class="sn">({n})</sup>{render_sentence(s, uls.get(n))}')
        parts.append('<p class="en">' + " ".join(buf) + "</p>")
    parts.append("</div>")
    parts.append(f'<div class="wcount">({total_words} words)</div>')
    return "\n".join(parts)


def vocab_table(vocab):
    if not vocab:
        return ""
    rows = []
    cells = []
    for item in vocab:
        w, pos, mean = (list(item) + ["", "", ""])[:3]
        cells.append(f'<td class="w">{esc(w)}</td><td class="p">{esc(pos)}</td><td>{esc(mean)}</td>')
    # 2 words per row (6 columns)
    out = ['<div class="vhd">語注 Vocabulary</div><table class="vocab">']
    for i in range(0, len(cells), 2):
        pair = cells[i:i + 2]
        if len(pair) == 1:
            pair.append('<td class="w"></td><td class="p"></td><td></td>')
        out.append("<tr>" + "".join(pair) + "</tr>")
    out.append("</table>")
    return "\n".join(out)


def rq_problem(q, no):
    t = q["type"]
    head = f'<div class="q"><div class="h"><span class="qno">{esc(no)}</span></div>'
    if t == "rc_mc":
        h = head + f'<div class="stem">{esc(q["q"])}</div><div class="choices">'
        for j, c in enumerate(q["choices"]):
            h += f'<div>{CIRCLE[j]} {esc(c)}</div>'
        return h + '</div></div>'
    if t == "rc_desc":
        lines = q.get("lines", 2)
        h = head + f'<div class="stem">{esc(q["q"])}</div>'
        h += '<div class="wlbox">' + '<div class="jline"></div>' * lines + '</div>'
        return h + '</div>'
    raise ValueError(f"unknown reading q type: {t}")


def rq_answer(q, no):
    t = q["type"]
    if t == "rc_mc":
        ci = q["ans"]
        return (f'<div class="ex"><div class="exh"><span class="exno">{esc(no)}</span>'
                f'<span class="exa">正解 {CIRCLE[ci]}　<span class="jp">{esc(q["choices"][ci])}</span></span></div>'
                f'<div class="exbody">{esc(q["exp"])}</div></div>')
    if t == "rc_desc":
        return (f'<div class="ex"><div class="exh"><span class="exno">{esc(no)}</span>'
                f'<span class="exa"><span class="jp">解答例</span></span></div>'
                f'<div class="exbody"><b>{esc(q["ans"])}</b><br>{esc(q["exp"])}</div></div>')
    raise ValueError(f"unknown reading q type: {t}")


# ---------------- book assembly ----------------
TIER_META = [("kiso", "基礎問", "Basic"), ("hyojun", "標準問題", "Standard"), ("nyushi", "入試チャレンジ", "Challenge")]
TIER_PREFIX = {"kiso": "基", "hyojun": "標", "nyushi": "入"}


def band(M, kind):
    return (f'<div class="band"><div class="l">{esc(M["series"])}'
            f'<small>{esc(M["level"])}／{esc(kind)}</small></div>'
            f'<div class="r">{esc(M.get("target",""))}<br><b>全10回</b>（{M["minutes"]}分×10）</div></div>')


def course_intro(M):
    return (f'<div class="intro"><b>この夏の到達目標：</b>{esc(M["intro"])}'
            f'<div class="introrow">'
            f'<div class="cell"><b>英文法編</b>　{esc(M["grammar_dates"])}（全5回）<br>ポイント整理 → 基礎問 → 標準 → 入試</div>'
            f'<div class="cell"><b>英語長文編</b>　{esc(M["reading_dates"])}（全5回）<br>構造把握 → 論理 → 設問処理 → 速読 → 実戦</div>'
            f'</div></div>')


def foot(M, kind):
    return (f'<div class="foot">トリリオンAI塾　{esc(M["series"])}　{esc(M["level"])}　{esc(kind)}　'
            f'ライブ授業×AI学習管理</div>')


def build_mondai(M, GRAMMAR, READING):
    h = [band(M, "問題編")]
    h.append(course_intro(M))
    h.append('<div class="metarow"><div class="cell">氏名</div>'
             '<div class="cell">受講日　　　／</div><div class="cell score">得点　　／</div></div>')

    # 英文法編
    h.append('<div class="partdiv first"><div class="pt1">英文法編</div>'
             f'<div class="pt2">{esc(M["grammar_dates"])}　全5回　／　ポイント整理と3段階演習（基礎問→標準→入試）で「文法はやったのに使えない」を終わらせる。</div></div>')
    for gi, s in enumerate(GRAMMAR):
        first = " first" if gi == 0 else ""
        h.append(f'<div class="sess{first}">')
        h.append(f'<div class="sesshd"><span class="sno">第{s["no"]}講</span>'
                 f'<span class="sttl">{esc(clean_title(s["title"]))}</span>'
                 f'<span class="sdate">{esc(s.get("date",""))}</span></div>')
        h.append(f'<div class="goal"><b>ねらい：</b>{esc(s["goal"])}</div>')
        h.append(pointbox(s["points"]))
        for key, label, en2 in TIER_META:
            items = s.get(key, [])
            if not items:
                continue
            tier_hd = (f'<div class="tier {key}">{label}<span class="en2">{en2}</span>'
                       f'<span class="cnt">全{len(items)}問</span></div>')
            # 見出しと最初の1問を離さない（見出しだけがページ末に孤立するのを防ぐ）
            h.append(f'<div class="tglue">{tier_hd}{q_problem(items[0], f"{TIER_PREFIX[key]}1", key)}</div>')
            for i, q in enumerate(items[1:], start=2):
                h.append(q_problem(q, f'{TIER_PREFIX[key]}{i}', key))
        h.append('</div>')

    # 英語長文編
    h.append('<div class="partdiv"><div class="pt1">英語長文編</div>'
             f'<div class="pt2">{esc(M["reading_dates"])}　全5回　／　「構造を掴む→論理を追う→設問を処理する→速く読む→志望校で戦う」を1本ずつ。</div></div>')
    for ri, s in enumerate(READING):
        h.append(f'<div class="sess{" first" if ri == 0 else ""}">')
        h.append(f'<div class="sesshd"><span class="sno">第{s["no"]}講</span>'
                 f'<span class="sttl">{esc(clean_title(s["title"]))}</span>'
                 f'<span class="sdate">{esc(s.get("date",""))}</span></div>')
        h.append(f'<div class="goal"><b>ねらい：</b>{esc(s["goal"])}</div>')
        h.append(pointbox(s["points"]))
        h.append(passage_html(s["passage"], s.get("questions")))
        h.append(vocab_table(s.get("vocab", [])))
        instr = f'<div class="instr">{esc(s["q_instr"])}</div>' if s.get("q_instr") else ""
        h.append(f'<div class="tglue"><div class="partttl">設問</div>{instr}'
                 f'{rq_problem(s["questions"][0], "問1")}</div>')
        for i, q in enumerate(s["questions"][1:], start=2):
            h.append(rq_problem(q, f'問{i}'))
        h.append('</div>')

    h.append(foot(M, "問題編"))
    return "\n".join(h)


def build_kaisetsu(M, GRAMMAR, READING):
    h = [band(M, "解答・解説編")]
    h.append(f'<div class="intro"><b>この冊子の使い方：</b>{esc(M.get("kaisetsu_intro", "各問の解答と、なぜそうなるか（考え方）を載せています。まちがえた問題は解説を読み、翌日にもう一度解き直しましょう。"))}</div>')

    # 英文法編
    h.append('<div class="partdiv first"><div class="pt1">英文法編　解答・解説</div>'
             f'<div class="pt2">{esc(M["grammar_dates"])}　全5回</div></div>')
    for gi, s in enumerate(GRAMMAR):
        first = " first" if gi == 0 else ""
        h.append(f'<div class="sess{first}">')
        h.append(f'<div class="secttl">第{s["no"]}講　{esc(clean_title(s["title"]))}'
                 f'<span class="en2">解答・解説</span></div>')
        # answer key (mc / fill / error short answers)
        h.append(grammar_key_table(s))
        for key, label, en2 in TIER_META:
            items = s.get(key, [])
            if not items:
                continue
            tier_hd = f'<div class="tier {key}">{label}<span class="en2">{en2}</span></div>'
            h.append(f'<div class="tglue">{tier_hd}{q_answer(items[0], f"{TIER_PREFIX[key]}1")}</div>')
            for i, q in enumerate(items[1:], start=2):
                h.append(q_answer(q, f'{TIER_PREFIX[key]}{i}'))
        h.append('</div>')

    # 英語長文編
    h.append('<div class="partdiv"><div class="pt1">英語長文編　解答・解説</div>'
             f'<div class="pt2">{esc(M["reading_dates"])}　全5回</div></div>')
    for ri, s in enumerate(READING):
        h.append(f'<div class="sess{" first" if ri == 0 else ""}">')
        h.append(f'<div class="secttl">第{s["no"]}講　{esc(clean_title(s["title"]))}'
                 f'<span class="en2">解答・解説</span></div>')
        for i, q in enumerate(s["questions"], start=1):
            h.append(rq_answer(q, f'問{i}'))
        # 全訳
        h.append(f'<div class="tier hyojun">全訳<span class="en2">Translation</span></div>')
        h.append('<div class="trbox">')
        trans = s["passage"].get("trans", {})
        n = 0
        for para in s["passage"]["paras"]:
            buf = []
            for _ in para:
                n += 1
                tr = trans.get(str(n), trans.get(n, ""))
                buf.append(f'<span class="sn2">({n})</span>{esc(tr)}')
            h.append('<div class="tr1">' + "　".join(buf) + "</div>")
        h.append('</div>')
        h.append('</div>')

    h.append(foot(M, "解答・解説編"))
    return "\n".join(h)


def grammar_key_table(s):
    """基礎問/標準/入試の中の mc・error だけを拾って一覧表にする（fill/order/rewrite/ja2en は解説側で確認）。"""
    rows = []
    for key, label, _ in TIER_META:
        for i, q in enumerate(s.get(key, []), start=1):
            no = f'{TIER_PREFIX[key]}{i}'
            if q["type"] == "mc":
                rows.append((no, CIRCLE[q["ans"]]))
            elif q["type"] == "error":
                rows.append((no, f'({q["ans"]})'))
            elif q["type"] == "fill":
                rows.append((no, esc(q["ans"])))
    if not rows:
        return ""
    # chunk into rows of up to 10
    out = ['<table class="ans">']
    CH = 10
    for i in range(0, len(rows), CH):
        chunk = rows[i:i + CH]
        out.append('<tr><th>問</th>' + "".join(f'<td>{r[0]}</td>' for r in chunk) + '</tr>')
        out.append('<tr><th>解答</th>' + "".join(f'<td class="a">{r[1]}</td>' for r in chunk) + '</tr>')
    out.append('</table>')
    return "\n".join(out)


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
        # left footer label
        page.insert_text((40, page.rect.height - 20), foot_label,
                         fontfile=FONT_PATH, fontname="AU", fontsize=7.5, color=(0.55, 0.55, 0.55))
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


def build_book(M, GRAMMAR, READING, outdir=DESKTOP):
    base = f'トリリオン夏期講習_英語_{M["level"]}'
    q_pdf = os.path.join(outdir, f'{base}_問題編.pdf')
    a_pdf = os.path.join(outdir, f'{base}_解答解説編.pdf')
    fl = f'トリリオン夏期講習 英語 {M["level"]}'
    render(build_mondai(M, GRAMMAR, READING), q_pdf, fl + " 問題編")
    render(build_kaisetsu(M, GRAMMAR, READING), a_pdf, fl + " 解答・解説編")
    return q_pdf, a_pdf
