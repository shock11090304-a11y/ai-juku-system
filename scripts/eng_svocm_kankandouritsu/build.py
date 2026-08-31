# -*- coding: utf-8 -*-
"""問題編 / 解答・解説編 の 2 冊を ~/Desktop に出力する。

    python3 build.py

★実行すると先に check.py を通す（落ちたら刷らない）。
★PDF 化は Chrome + Arial Unicode を使うので **塾長の Mac でしか動かない**。
  CI とクラウドの Claude Code では check.py / selftest_gate.py までを回す。
"""
import os
import sys

from layout import (
    CIRCLE, DESKTOP, EXTRA_CSS, SYN_VOCAB, esc, parse, render_analysis, render_blank,
    render_pdf, render_skeleton, top_segments,
)
import layout
from content import META, NOTATION, PART1, PART2, PART3, RULES, RULE_EXAMPLES, STEPS

# 共有 CSS にこの教材ぶんを継ぎ足す（BASE_CSS 側は書き換えない）
layout.BASE_CSS = layout.BASE_CSS + EXTRA_CSS
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"

LEGEND = ('<div class="legend">'
          '<span><b style="color:#1d4ed8">S</b> 主語</span>'
          '<span><b style="color:#dc2626">V</b> 述語動詞</span>'
          '<span><b style="color:#047857">O</b> 目的語</span>'
          '<span><b style="color:#b45309">C</b> 補語</span>'
          '<span><b style="color:#64748b">M</b> 修飾語</span>'
          '<span><b style="color:#0f766e">真S / 真O</b> 形式主語・形式目的語が指す中身</span>'
          '<span><b style="color:#9333ea">接</b> 接続詞</span>'
          '<span><b style="color:#64748b">( )</b> 副詞のカタマリ</span>'
          '<span><b style="color:#047857">[ ]</b> 名詞のカタマリ</span>'
          '<span><b style="color:#7c3aed">&lt; &gt;</b> 形容詞のカタマリ</span>'
          '<span>S′ / S″ … 従属節の中の要素</span>'
          '</div>')


def notation_html():
    """記号の書き方（表記規約）。問題編・解答編の両方に同じものを刷る。

    ★生徒が答案に書く形を決めるのはここ。ここが揺れると「記号を指させるか」で採点できない。
    """
    rows = "".join(
        f'<tr><td class="nk">{esc(h)}</td><td class="nb">{b}</td>'
        f'<td class="ne">{x}</td></tr>' for h, b, x in NOTATION)
    return ('<div class="partttl">記号の書き方（この教材の約束）'
            '<span class="en2">How to write your answer</span></div>'
            '<div class="instr">同じ構文を 2 通りに書けると採点ができない。'
            '迷ったらこの表に戻ること。</div>'
            f'<table class="notation">{rows}</table>')


def band(sub):
    return (f'<div class="band"><div class="l">{esc(META["title"])}'
            f'<small>{esc(META["sub"])}</small></div>'
            f'<div class="r"><b>{esc(sub)}</b><br>{esc(META["level"])}／'
            f'{esc(META["brand"])}</div></div>')


def foot(label):
    return (f'<div class="foot">{esc(META["brand"])}　{esc(META["title"])}　{esc(label)}'
            f'　—　判別 {META["_n1"]} 問／構造4択 {META["_n2"]} 問／解釈 {META["_n3"]} 文</div>')


def partdiv(t1, t2, first=False):
    return (f'<div class="partdiv{" first" if first else ""}">'
            f'<div class="pt1">{esc(t1)}</div><div class="pt2">{esc(t2)}</div></div>')


# ---------------------------------------------------------------- 第1部の部品
def drill_sentence(segs):
    """①②③… を振った英文（問題編に刷る形）。"""
    out = []
    for i, (_lb, txt, _u) in enumerate(segs):
        out.append(f'<span class="seg"><span class="mk2">{CIRCLED[i]}</span>{esc(txt)}</span>')
    return '<div class="dsent">' + " ".join(out) + '</div>'


def slot_table(segs, answers=None):
    """①②③… の解答欄（answers を渡すと答えを入れた表になる）。"""
    head = "".join(f'<th>{CIRCLED[i]}</th>' for i in range(len(segs)))
    if answers is None:
        body = "".join('<td></td>' for _ in segs)
    else:
        body = "".join(f'<td class="a">{esc(a)}</td>' for a in answers)
    return ('<table class="slotbox"><tr><th class="lead">記号</th>' + head + '</tr>'
            '<tr><td class="lead">解答</td>' + body + '</tr></table>')


# ================================================================ 問題編
def build_mondai():
    h = [band("問題編")]
    h.append(
        '<div class="intro">'
        '英文解釈とは、<b>一語一語が文の骨組み（S V O C）なのか飾り（M）なのかを、'
        '記号で指し切る</b>作業のこと。関関同立の英語は、時間がタイトなぶん'
        '「なんとなく意味が取れる」で流すと、下線部和訳・内容一致・整序で必ず崩れる。<br>'
        'この教材は <b>第1部 SVOCM 判別</b>（骨組みを指す）→ <b>第2部 構造判断の4択</b>'
        '（どこにかかるかを決める）→ <b>第3部 英文解釈</b>（分解して訳す）の順に上げていく。'
        '第1部は<b>答えを書き込む前に、必ず声に出して区切りを言う</b>こと。'
        '<br><span style="font-size:8.8pt;color:#64748b">'
        '※本文は狙った構文を含めるために書き下ろした本教材オリジナルの英文であり、'
        '実際の入試問題ではない。</span>'
        '</div>')
    h.append('<div class="metarow">'
             '<div class="cell">氏名　　　　　　　　　　　　　　　</div>'
             '<div class="cell">実施日　　　　月　　　日</div>'
             f'<div class="cell score">判別 {META["_n1"]} 問中　　　問</div>'
             '</div>')

    h.append('<div class="partttl">記号のルール<span class="en2">Notation</span></div>')
    h.append('<div class="rulegrid">')
    for r in RULES:
        h.append(f'<div class="rulecard {r["cls"]}"><div class="rh">{esc(r["h"])}</div>'
                 f'<div class="rb">{r["b"]}</div>'
                 f'<div class="rex">{esc(r["ex"])}</div></div>')
    h.append('</div>')

    h.append('<div class="partttl">読む手順<span class="en2">Procedure</span></div>')
    h.append('<div class="steps">')
    for i, s in enumerate(STEPS, 1):
        h.append(f'<div class="step"><span class="stepno">STEP {i}</span><span>{s}</span></div>')
    h.append('</div>')

    h.append(notation_html())
    h.append('<div class="partttl">記号の使い方（見本）<span class="en2">Worked examples</span></div>')
    h.append(LEGEND)
    for i, ex in enumerate(RULE_EXAMPLES, 1):
        root = parse(ex["dsl"])
        h.append(f'<div class="acard"><div class="ah"><span class="ano">見本 {i}</span>'
                 f'<span class="apat">{esc(ex["pat"])}</span></div>')
        h.append(render_analysis(root))
        h.append(f'<div class="notes">{ex["note"]}</div></div>')

    # --- 第1部 -----------------------------------------------------------
    h.append(partdiv(f'第 1 部　SVOCM 判別（{META["_n1"]} 問）',
                     '①②③… に区切った各部分が S・V・O・C・M のどれかを答え、文型を確定する'))
    h.append('<div class="instr">各文の ①②③… について、'
             '<b>S・V・O・C・M</b>（第4文型は O1・O2、形式主語・形式目的語の中身は 真S・真O）'
             'のどれかを解答欄に書き、最後に文型を答えなさい。'
             '記号は 1 か所につき 1 つに決まる。</div>')
    n = 0
    for grp in PART1:
        h.append(f'<div class="grpttl">{esc(grp["g"])}<span class="sub">{esc(grp["sub"])}</span></div>')
        for it in grp["items"]:
            n += 1
            segs = top_segments(parse(it["dsl"]))
            h.append('<div class="dq"><div class="wqh">'
                     f'<span class="qno">{n}</span></div>')
            h.append(drill_sentence(segs))
            h.append(slot_table(segs))
            h.append('<span class="patbox">文型　第　　　文型</span>')
            h.append('</div>')

    # --- 第2部 -----------------------------------------------------------
    h.append(partdiv(f'第 2 部　構造判断の 4 択（{META["_n2"]} 問）',
                     'どの語にかかるか・何が主語か・その語の働きは何かを決める'))
    h.append('<div class="instr">次の各文について、最も適切なものを ①〜④ から 1 つ選びなさい。</div>')
    for qi, q in enumerate(PART2, 1):
        h.append('<div class="q"><div class="wqh">'
                 f'<span class="qno">{qi}</span></div>')
        h.append(f'<div class="wsent" style="line-height:1.75">{esc(q["en"])}</div>')
        h.append(f'<div class="stem">{q["q"]}</div><div class="choices">')
        for ci, c in enumerate(q["choices"]):
            h.append(f'<div>{CIRCLE[ci]} {c}</div>')
        h.append('</div></div>')

    # --- 第3部 -----------------------------------------------------------
    h.append(partdiv(f'第 3 部　英文解釈（{META["_n3"]} 文）',
                     '( ) [ ] < > でカタマリを囲み、記号を書き込んでから和訳する'))
    h.append('<div class="instr">次の各文について、'
             '(1) <b>( ) [ ] &lt; &gt;</b> でカタマリを囲み、S・V・O・C・M の記号を書き込む'
             '（従属節の中は S′ V′ … とする）。'
             '(2) 文型を答える。(3) 全文を日本語に訳す。'
             '<b>訳が合っていても記号がずれていれば「読めた」ではない。</b></div>')
    m = 0
    for grp in PART3:
        h.append(f'<div class="grpttl">{esc(grp["g"])}<span class="sub">{esc(grp["sub"])}</span></div>')
        for it in grp["items"]:
            m += 1
            h.append('<div class="wq"><div class="wqh">'
                     f'<span class="qno">{m}</span></div>')
            h.append(render_blank(parse(it["dsl"]), lh="3.15"))
            h.append('<span class="patbox">文型　第　　　文型</span>')
            h.append('<div style="margin:5px 0 0 2px">'
                     + '<div class="jline2"></div>' * 3 + '</div>')
            h.append('</div>')

    h.append(foot("問題編"))
    return "\n".join(h)


# ================================================================ 解答解説編
def analysis_card(it, no, extra_head=""):
    root = parse(it["dsl"])
    h = ['<div class="acard"><div class="ah">'
         f'<span class="ano">{esc(no)}</span>'
         f'<span class="apat">{esc(it["pat"])}</span>'
         f'<span class="atag">{esc(it["tag"])}</span>{extra_head}</div>']
    h.append(render_analysis(root))
    sk = render_skeleton(root)
    if sk:
        h.append(f'<div class="skel"><span class="lead">骨組み</span>{sk}</div>')
    h.append('<div class="notes"><ul>' + "".join(f'<li>{x}</li>' for x in it["notes"]) + '</ul></div>')
    h.append(f'<div class="jatr"><b>和訳</b>{esc(it["ja"])}</div>')
    return h


def build_kaisetsu():
    h = [band("解答・解説編")]
    h.append('<div class="intro">'
             '分解図は <b>記号レベルで</b> 照合すること。訳が合っていても、かかり方の記号が'
             'ずれていれば「読めていない」と判定する。各文には <b>骨組み</b>'
             '（カタマリを全部外し、節をつなぐ語だけ残したもの）を併記した。'
             'まずそこだけを見て、自分が同じ骨組みを取れていたかを確認すること。'
             '<br><span style="font-size:8.8pt;color:#64748b">'
             '※本文は本教材オリジナルの英文（実際の入試問題ではない）。</span></div>')
    h.append(LEGEND)
    h.append(notation_html())

    # --- 第1部 ---
    h.append(partdiv('第 1 部　SVOCM 判別　解答・解説', '①②③… の記号と文型'))
    n = 0
    for grp in PART1:
        h.append(f'<div class="grpttl">{esc(grp["g"])}<span class="sub">{esc(grp["sub"])}</span></div>')
        for it in grp["items"]:
            n += 1
            segs = top_segments(parse(it["dsl"]))
            h += analysis_card(it, str(n))
            h.append(slot_table(segs, [lb for lb, _t, _u in segs]))
            h.append('</div>')

    # --- 第2部 ---
    h.append(partdiv('第 2 部　構造判断の 4 択　解答・解説', ''))
    h.append('<table class="ans"><tr><th>問</th>'
             + "".join(f'<td>{i}</td>' for i in range(1, len(PART2) + 1)) + '</tr>'
             + '<tr><th>解答</th>'
             + "".join(f'<td class="a">{CIRCLE[q["ans"]]}</td>' for q in PART2)
             + '</tr></table>')
    for qi, q in enumerate(PART2, 1):
        h += analysis_card(
            q, str(qi),
            f'<span class="uni">正解 {CIRCLE[q["ans"]]}</span>')
        h.append(f'<div class="notes"><b>設問</b>　{q["q"]}<br>'
                 f'<b>正解</b>　{CIRCLE[q["ans"]]} {q["choices"][q["ans"]]}<br>{q["exp"]}</div>')
        h.append('</div>')

    # --- 第3部 ---
    h.append(partdiv('第 3 部　英文解釈　解答・解説', '分解図・骨組み・模範解答・採点ポイント'))
    m = 0
    for grp in PART3:
        h.append(f'<div class="grpttl">{esc(grp["g"])}<span class="sub">{esc(grp["sub"])}</span></div>')
        for it in grp["items"]:
            m += 1
            h += analysis_card(it, str(m))
            h.append('<div class="notes pts"><b>採点ポイント</b><ul>'
                     + "".join(f'<li>{esc(p)}</li>' for p in it["points"]) + '</ul></div>')
            h.append('</div>')

    h.append(syn_index_html())
    h.append(foot("解答・解説編"))
    return "\n".join(h)


def syn_index_html():
    """巻末: 収録構文一覧（どの構文をどの問題で扱ったか）。

    ★塾長がここだけ見れば「何が入っていて何が入っていないか」が分かるようにする。
      構文カテゴリ（syn）は check.py が語彙と重複を機械で見ているので、この表は
      原稿と必ず一致する（手で作った索引のようにずれない）。
    """
    rows = []
    n1 = n3 = 0
    for grp in PART1:
        for it in grp["items"]:
            n1 += 1
            rows.append((it["syn"], f'第1部 {n1}'))
    for qi, q in enumerate(PART2, 1):
        rows.append((q["syn"], f'第2部 {qi}'))
    for grp in PART3:
        for it in grp["items"]:
            n3 += 1
            rows.append((it["syn"], f'第3部 {n3}'))
    byname = {}
    for syn, where in rows:
        byname.setdefault(syn, []).append(where)
    body = "".join(
        f'<tr><td class="nk">{esc(SYN_VOCAB.get(s, s))}</td>'
        f'<td class="nb">{esc("　".join(w))}</td>'
        f'<td class="ne">{esc(s)}</td></tr>'
        for s, w in sorted(byname.items(), key=lambda x: SYN_VOCAB.get(x[0], x[0])))
    return ('<div class="partdiv"><div class="pt1">収録構文一覧</div>'
            f'<div class="pt2">全 {len(rows)} 問 ／ {len(byname)} 構文</div></div>'
            '<div class="instr">この教材で扱った構文の一覧。'
            '解き直すときは、間違えた問題と同じ構文の問題をここから探すこと。</div>'
            f'<table class="notation">{body}</table>')


def main():
    base = "英語_英文解釈とSVOCM判別_関関同立"
    render_pdf(build_mondai(), os.path.join(DESKTOP, f"{base}_問題編.pdf"),
               f'{META["title"]} 問題編')
    render_pdf(build_kaisetsu(), os.path.join(DESKTOP, f"{base}_解答解説編.pdf"),
               f'{META["title"]} 解答・解説編')


if __name__ == "__main__":
    import check
    try:
        check.main()
    except SystemExit as e:
        if e.code:
            sys.exit(e.code)
    main()
