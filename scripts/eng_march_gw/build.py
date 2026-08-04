# -*- coding: utf-8 -*-
"""
MARCH英語 文法・英作演習 ビルダー（単一ソース content.py → 問題編/解答解説編 HTML）
HTML → Chrome --headless=new --print-to-pdf でA4 PDF化。
eng_therules の BASE_CSS を土台に、文法・英作レイアウトへ作り替え。
"""
import os, re, html
import content as C

OUT = os.path.dirname(os.path.abspath(__file__))
M = C.META
G = C.GRAMMAR
W = C.WRITING

BASE_CSS = """
* { box-sizing: border-box; }
@page { size: A4; margin: 14mm 14mm 15mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family:"Hiragino Mincho ProN","Yu Mincho",serif; color:#1a1a1a; font-size:10.5pt; line-height:1.6; margin:0; }
.gothic { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }
.en { font-family:Georgia,"Times New Roman",serif; }
h1,h2,h3,.band,.qno,.pts,.secttl,.partttl,.foot,.wh,.tag { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }

/* header band */
.band { background:linear-gradient(90deg,#0f172a,#1e3a8a); color:#fff; padding:9px 14px; border-radius:8px;
  display:flex; justify-content:space-between; align-items:center; }
.band .l { font-size:15pt; font-weight:700; letter-spacing:.02em; }
.band .l small { font-weight:600; font-size:9.5pt; opacity:.9; margin-left:8px; }
.band .r { text-align:right; font-size:9pt; line-height:1.4; }
.band .r b { font-size:12pt; }
.subline { margin:7px 2px 2px; font-size:9.5pt; color:#334155; display:flex; justify-content:space-between; }
.subline .theme { font-weight:700; color:#0f172a; }
.metarow { display:flex; gap:10px; margin:9px 0 8px; font-size:9.5pt; }
.metarow .cell { border:1px solid #cbd5e1; border-radius:6px; padding:4px 10px; flex:1; }
.metarow .cell.score { flex:0 0 150px; text-align:center; }

/* part / instruction */
.partttl { font-size:12pt; font-weight:700; color:#fff; background:#1e3a8a; border-radius:6px;
  padding:4px 12px; margin:14px 0 8px; page-break-after:avoid; }
.partttl small { font-weight:600; font-size:9pt; opacity:.9; margin-left:8px; }
.instr { font-size:9.3pt; background:#f1f5f9; border-left:4px solid #1e3a8a; padding:6px 10px; border-radius:4px; margin:6px 0 10px; color:#334155; }

/* question block */
.q { margin:0 0 10px; page-break-inside:avoid; }
.q .h { display:flex; align-items:baseline; gap:8px; }
.qno { background:#0f172a; color:#fff; border-radius:5px; padding:1px 9px; font-size:9.3pt; font-weight:700; white-space:nowrap; }
.pts { color:#dc2626; font-size:8.3pt; font-weight:700; }
.q .stem { margin:3px 0 2px; font-size:10pt; }
.q .stem .en { font-size:10.3pt; }
.q .jp { font-size:9.4pt; color:#475569; margin:1px 0 3px; }
.q .choices div { margin:2px 0 1px 8px; font-size:9.8pt; }
.q .choices .en { font-size:10pt; }
.fill { display:inline-block; min-width:66px; border-bottom:1.5px solid #0f172a; text-align:center; font-weight:700; }
.hint { font-style:italic; color:#475569; }

/* word-order chips */
.words { display:flex; flex-wrap:wrap; gap:6px; margin:4px 0 4px 8px; }
.wchip { border:1px solid #94a3b8; background:#f8fafc; border-radius:5px; padding:1.5px 9px; font-family:Georgia,serif; font-size:9.8pt; }
.ansbox { border:1px solid #94a3b8; border-radius:6px; min-height:30px; margin:4px 0 0 8px; }
.ansbox.tall { min-height:40px; }

/* error-spotting underline */
.errsent { font-family:Georgia,serif; font-size:10.3pt; line-height:1.9; margin:2px 0 3px; }
.emk { border-bottom:1.7px solid #dc2626; padding-bottom:1px; white-space:nowrap; }
.emk sup { color:#dc2626; font-weight:700; font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin-right:1px; }
.pick { font-size:9.3pt; color:#334155; margin:2px 0 0 8px; }
.pick .fill { min-width:44px; }

/* rewrite */
.rw .give { font-family:Georgia,serif; font-size:10pt; margin:2px 0 2px; }
.rw .tgt { font-family:Georgia,serif; font-size:10pt; margin:1px 0 2px; color:#0f172a; }
.rw .lab { font-size:8.6pt; color:#64748b; font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin-right:4px; }

/* writing answer lines */
.wl { border-bottom:1px solid #cbd5e1; height:20px; margin:0; }
.wlbox { margin:5px 0 2px 8px; }

/* section (解説) */
.secttl { font-size:13pt; font-weight:700; color:#0f172a; border-left:6px solid #1e3a8a; padding:3px 0 3px 10px; margin:0 0 10px; }
.secttl .en2 { font-size:9pt; color:#64748b; font-weight:600; margin-left:8px; }
.section { margin-bottom:10px; }
.pb { page-break-before:always; }

/* answer table */
table.ans { width:100%; border-collapse:collapse; font-size:9.2pt; }
table.ans th, table.ans td { border:1px solid #cbd5e1; padding:4px 6px; vertical-align:middle; text-align:center; }
table.ans th { background:#eef2ff; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
table.ans td.a { font-weight:700; color:#1e3a8a; font-family:Georgia,serif; }

/* explanation card */
.ex { border:1px solid #e2e8f0; border-left:4px solid #1e3a8a; border-radius:6px; padding:6px 10px; margin:7px 0; page-break-inside:avoid; }
.ex .exh { display:flex; align-items:baseline; gap:8px; margin-bottom:2px; }
.ex .exno { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; color:#0f172a; }
.ex .exa { font-family:Georgia,serif; font-weight:700; color:#1e3a8a; }
.ex .tag { display:inline-block; background:#fde68a; color:#7c2d12; font-weight:700; border-radius:4px; padding:0 7px; font-size:8.4pt; }
.ex .exbody { font-size:9.4pt; color:#1f2937; line-height:1.6; }
.ex .exbody .en { font-family:Georgia,serif; }

/* writing model card */
.wcard { border:1px solid #cbd5e1; border-left:4px solid #047857; border-radius:6px; padding:7px 10px; margin:9px 0; page-break-inside:avoid; }
.wcard .wh { font-weight:700; font-size:10pt; color:#065f46; margin-bottom:3px; }
.wcard .jp { font-size:9.6pt; color:#334155; margin-bottom:4px; }
.wcard .model { background:#f0fdf4; border-radius:4px; padding:5px 9px; margin:4px 0; font-family:Georgia,serif; font-size:9.9pt; line-height:1.5; }
.wcard .model .ml { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:8.4pt; color:#047857; font-weight:700; display:block; margin-bottom:1px; }
.wcard .pt { font-size:9pt; color:#334155; margin-top:3px; }
.wcard .pt b { color:#065f46; }
.wcard .miss { font-size:9pt; color:#7c2d12; background:#fff7ed; border-radius:4px; padding:4px 8px; margin-top:4px; }

.foot { text-align:center; color:#64748b; font-size:8.3pt; margin-top:10px; padding-top:4px; border-top:1px solid #e2e8f0; page-break-inside:avoid; }
"""

CIRCLE = ["①", "②", "③", "④", "⑤"]

def esc(s):
    return html.escape(s, quote=False)

def doc(title, inner):
    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<title>{title}</title><style>{BASE_CSS}</style></head><body>{inner}</body></html>')

def band(kind_label):
    return (f'<div class="band"><div class="l">{M["series"]} <small>{M["title_g"]}／{M["title_w"]}</small></div>'
            f'<div class="r">{M["level"]}<br><b>No.{M["no"]}</b></div></div>')

def foot(kind):
    return (f'<div class="foot">トリリオンAI塾 ／ {M["series"]} No.{M["no"]} ・ '
            f'文法25問＋英作6題 ・ {M["level"]} ・ {kind}</div>')

def en(s):
    """英文をGeorgia表示。空所 ______ は .fill に、( hint ) は斜体に。"""
    s = esc(s)
    s = s.replace("______", '<span class="fill">&nbsp;</span>')
    s = re.sub(r'\(\s*([A-Za-z][A-Za-z\s]*?)\s*\)', r'<span class="hint">( \1 )</span>', s)
    return f'<span class="en">{s}</span>'

MARK = re.compile(r'\[([a-d])\|([^\]]+)\]')

def error_sentence(s):
    """[a|語句] → 下線+上付き記号。"""
    def rep(m):
        return f'<span class="emk"><sup>({m.group(1)})</sup>{esc(m.group(2))}</span>'
    # マーカー外の素テキストはエスケープしつつ、マーカーを変換
    out, last = [], 0
    for m in MARK.finditer(s):
        out.append(esc(s[last:m.start()]))
        out.append(rep(m))
        last = m.end()
    out.append(esc(s[last:]))
    return f'<div class="errsent">{"".join(out)}</div>'

# ==================== 問題編 ====================
def build_mondai():
    h = band("q")
    name = f'　<b>{M["student"]}</b>' if M.get("student") else ""
    h += (f'<div class="metarow"><div class="cell">氏名{name}</div>'
          f'<div class="cell">日付　　　　／</div>'
          f'<div class="cell score">得点　　／</div></div>')

    # 第1部 空所補充
    h += '<div class="partttl">第1部　空所補充<small>問1〜問12　最も適切なものを①〜④から選べ</small></div>'
    for i, q in enumerate(G["choice"], start=1):
        h += f'<div class="q"><div class="h"><span class="qno">問{i}</span></div>'
        h += f'<div class="stem">{en(q["q"])}</div>'
        if q.get("note"):
            h += f'<div class="jp">（{esc(q["note"])}）</div>'
        h += '<div class="choices">'
        for j, c in enumerate(q["choices"]):
            h += f'<div>{CIRCLE[j]} {en(c)}</div>'
        h += '</div></div>'

    # 第2部 語句整序
    h += '<div class="partttl">第2部　語句整序<small>問13〜問17　日本語の意味に合うよう語句を並べ替えよ</small></div>'
    for k, q in enumerate(G["order"], start=13):
        h += f'<div class="q"><div class="h"><span class="qno">問{k}</span></div>'
        h += f'<div class="jp">{esc(q["jp"])}</div>'
        h += '<div class="words">' + "".join(f'<span class="wchip">{esc(w)}</span>' for w in q["words"]) + '</div>'
        h += '<div class="ansbox"></div></div>'

    # 第3部 誤り指摘
    h += '<div class="partttl">第3部　誤り指摘<small>問18〜問22　下線部(a)〜(d)のうち誤りを含むものを1つ選べ</small></div>'
    for k, q in enumerate(G["error"], start=18):
        h += f'<div class="q"><div class="h"><span class="qno">問{k}</span></div>'
        h += error_sentence(q["html"])
        h += '<div class="pick">誤り＝（　<span class="fill">&nbsp;</span>　）</div></div>'

    # 第4部 同意文完成
    h += '<div class="partttl">第4部　同意文完成<small>問23〜問25　2文がほぼ同じ意味になるよう空所を補え</small></div>'
    for k, q in enumerate(G["rewrite"], start=23):
        h += f'<div class="q rw"><div class="h"><span class="qno">問{k}</span></div>'
        h += f'<div class="give">{en(q["given"])}</div>'
        h += f'<div class="tgt">＝ {en(q["target"])}</div></div>'

    # 英作文
    h += '<div class="partttl pb">英作文<small>問A　和文英訳（1〜4）／問B　自由英作（5〜6）</small></div>'
    h += '<div class="instr">問A：次の日本語を英語に直しなさい。／問B：指示に従って自分の意見を英語で書きなさい。</div>'
    for k, q in enumerate(W["translation"], start=1):
        h += f'<div class="q"><div class="h"><span class="qno">英作{k}</span></div>'
        h += f'<div class="jp">{esc(q["jp"])}</div>'
        h += '<div class="wlbox"><div class="wl"></div><div class="wl"></div></div></div>'
    for k, q in enumerate(W["essay"], start=5):
        h += f'<div class="q"><div class="h"><span class="qno">英作{k}</span><span class="pts">（{esc(q["length"])}）</span></div>'
        h += f'<div class="jp">{esc(q["prompt"])}</div>'
        h += '<div class="wlbox">' + '<div class="wl"></div>'*6 + '</div></div>'

    h += foot("問題編")
    return doc(f'{M["series"]} No.{M["no"]} 問題編', h)

# ==================== 解答解説編 ====================
def ans_label_choice(idx):
    return CIRCLE[idx]

def build_kaisetsu():
    h = band("a")
    h += '<div class="secttl">解答一覧<span class="en2">Answer Key</span></div>'
    # 文法 解答表
    h += '<table class="ans"><tr><th>問</th>' + "".join(f'<td>{i}</td>' for i in range(1,13)) + '</tr>'
    h += '<tr><th>解答</th>' + "".join(f'<td class="a">{ans_label_choice(q["ans"])}</td>' for q in G["choice"]) + '</tr></table>'
    h += '<div style="height:5px"></div>'
    h += ('<table class="ans"><tr><th>誤り指摘</th>'
          + "".join(f'<td>問{k}</td>' for k in range(18,23)) + '</tr>'
          '<tr><th>解答</th>' + "".join(f'<td class="a">({q["ans"]})</td>' for q in G["error"]) + '</tr></table>')

    # 第1部 解説
    h += '<div class="secttl" style="margin-top:12px">第1部　空所補充 解説<span class="en2">問1〜問12</span></div>'
    for i, q in enumerate(G["choice"], start=1):
        h += ('<div class="ex"><div class="exh">'
               f'<span class="exno">問{i}</span><span class="exa">正解 {ans_label_choice(q["ans"])}　{esc(q["choices"][q["ans"]])}</span>'
               f'<span class="tag">{esc(q["point"])}</span></div>'
               f'<div class="exbody">{esc(q["expl"])}</div></div>')

    # 第2部 解説
    h += '<div class="secttl pb">第2部　語句整序 解説<span class="en2">問13〜問17</span></div>'
    for k, q in enumerate(G["order"], start=13):
        h += ('<div class="ex"><div class="exh">'
               f'<span class="exno">問{k}</span><span class="tag">{esc(q["point"])}</span></div>'
               f'<div class="exbody"><b>完成文：</b><span class="en">{esc(q["answer"])}.</span><br>{esc(q["expl"])}</div></div>')

    # 第3部 解説
    h += '<div class="secttl" style="margin-top:12px">第3部　誤り指摘 解説<span class="en2">問18〜問22</span></div>'
    for k, q in enumerate(G["error"], start=18):
        h += ('<div class="ex"><div class="exh">'
               f'<span class="exno">問{k}</span><span class="exa">正解 ({q["ans"]})　{esc(q["correct"])}</span>'
               f'<span class="tag">{esc(q["point"])}</span></div>'
               f'<div class="exbody">{esc(q["expl"])}</div></div>')

    # 第4部 解説
    h += '<div class="secttl" style="margin-top:12px">第4部　同意文完成 解説<span class="en2">問23〜問25</span></div>'
    for k, q in enumerate(G["rewrite"], start=23):
        filled = q["target"]
        for b in q["blanks"]:
            filled = filled.replace("______", b, 1)
        h += ('<div class="ex"><div class="exh">'
               f'<span class="exno">問{k}</span><span class="exa">{esc(" / ".join(q["blanks"]))}</span>'
               f'<span class="tag">{esc(q["point"])}</span></div>'
               f'<div class="exbody"><span class="en">{esc(filled)}</span><br>{esc(q["expl"])}</div></div>')

    # 英作 解答解説
    h += '<div class="secttl pb">英作文　解答・解説<span class="en2">Model Answers</span></div>'
    for k, q in enumerate(W["translation"], start=1):
        h += f'<div class="wcard"><div class="wh">英作{k}　和文英訳</div><div class="jp">{esc(q["jp"])}</div>'
        for mi, mdl in enumerate(q["models"], start=1):
            lab = "解答例" + (f"{mi}" if len(q["models"]) > 1 else "")
            h += f'<div class="model"><span class="ml">{lab}</span>{esc(mdl)}</div>'
        h += f'<div class="pt"><b>採点ポイント：</b>{esc(q["point"])}</div>'
        h += f'<div class="miss">▲ よくあるミス：{esc(q["mistakes"])}</div></div>'
    for k, q in enumerate(W["essay"], start=5):
        h += f'<div class="wcard"><div class="wh">英作{k}　自由英作（{esc(q["length"])}）</div><div class="jp">{esc(q["prompt"])}</div>'
        for label, mdl in q["models"]:
            h += f'<div class="model"><span class="ml">解答例（{esc(label)}）</span>{esc(mdl)}</div>'
        h += f'<div class="pt"><b>採点ポイント：</b>{esc(q["point"])}</div>'
        h += f'<div class="miss">▲ よくあるミス：{esc(q["mistakes"])}</div></div>'

    h += foot("解答・解説編")
    return doc(f'{M["series"]} No.{M["no"]} 解答解説編', h)

# ==================== 監査＆出力 ====================
def audit():
    # 四択の正解位置分布
    from collections import Counter
    dist = Counter(q["ans"] for q in G["choice"])
    print("choice ans dist (0-3):", dict(sorted(dist.items())))
    # 整序: 語群を並べ替えて完成文になるか（語のマルチ集合一致）
    for k, q in enumerate(G["order"], start=13):
        chips = " ".join(q["words"]).split()
        ans = q["answer"].split()
        if sorted(chips) != sorted(ans):
            print(f"  [WARN] 問{k} 語群と完成文が不一致: chips={sorted(chips)} ans={sorted(ans)}")
    # 書き換え: blank数と______数一致
    for k, q in enumerate(G["rewrite"], start=23):
        nb = q["target"].count("______")
        if nb != len(q["blanks"]):
            print(f"  [WARN] 問{k} 空所数{nb} != blanks{len(q['blanks'])}")

if __name__ == "__main__":
    audit()
    m = build_mondai()
    k = build_kaisetsu()
    open(os.path.join(OUT, "mondai.html"), "w").write(m)
    open(os.path.join(OUT, "kaisetsu.html"), "w").write(k)
    print("wrote mondai.html", len(m), "bytes")
    print("wrote kaisetsu.html", len(k), "bytes")
