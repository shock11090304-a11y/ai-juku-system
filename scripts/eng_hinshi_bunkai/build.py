# -*- coding: utf-8 -*-
"""問題編 / 解答解説編 の 2 冊を ~/Desktop に出力する。実行前に check.py を必ず通すこと。"""
import os, re, sys, subprocess
from core import (parse, plain_text, render_analysis, render_skeleton, render_blank,
                  render_pdf, esc, CIRCLE, DESKTOP, HERE)
from content import META, RULES, STEPS, RULE_EXAMPLES, PASSAGES

MARK_RE = re.compile(r'@(\d+)\{([^{}]*)\}')
LEGEND = ('<div class="legend">'
          '<span><b style="color:#1d4ed8">S</b> 主語</span>'
          '<span><b style="color:#dc2626">V</b> 述語動詞</span>'
          '<span><b style="color:#047857">O</b> 目的語</span>'
          '<span><b style="color:#b45309">C</b> 補語</span>'
          '<span><b style="color:#64748b">M</b> 修飾語</span>'
          '<span><b style="color:#9333ea">接</b> 接続詞</span>'
          '<span><b style="color:#64748b">( )</b> 副詞のカタマリ</span>'
          '<span><b style="color:#047857">[ ]</b> 名詞のカタマリ</span>'
          '<span><b style="color:#7c3aed">&lt; &gt;</b> 形容詞のカタマリ</span>'
          '<span>S′ / S″ … 従属節の中の要素</span>'
          '</div>')


def band(sub):
    return (f'<div class="band"><div class="l">{esc(META["title"])}'
            f'<small>{esc(META["sub"])}</small></div>'
            f'<div class="r"><b>{esc(sub)}</b><br>{esc(META["level"])}／'
            f'{esc(META["brand"])}</div></div>')


def foot(label):
    return (f'<div class="foot">{esc(META["brand"])}　{esc(META["title"])}　{esc(label)}'
            f'　—　長文 {META["n_pass"]} 本／分解 {META["n_sent"]} 文</div>')


def para_html(para):
    """@N{...} を「(N) + 下線」に置換。マーカー外の地の文も含め、必ず esc を通す。"""
    out, last = [], 0
    for m in MARK_RE.finditer(para):
        out.append(esc(para[last:m.start()]))
        out.append(f'<sup class="sn">({m.group(1)})</sup>'
                   f'<span class="mk">{esc(m.group(2))}</span>')
        last = m.end()
    out.append(esc(para[last:]))
    return "".join(out)


def passage_html(P):
    out = [f'<div class="ptitle">{esc(P["title"])}</div>',
           f'<div class="pjtitle">{esc(P["jtitle"])}　／　{esc(P["field"])}</div>',
           '<div class="passage">']
    for para in P["paras"]:
        out.append('<p>' + para_html(para) + '</p>')
    out.append('</div>')
    out.append(f'<div class="wcount">約 {P["_wc"]} words</div>')
    return "\n".join(out)


def vocab_html(P):
    out = ['<div class="vhd">語注 Vocabulary</div>', '<table class="vocab">']
    v = P["vocab"]
    for i in range(0, len(v), 2):
        row = v[i:i + 2]
        cells = "".join(f'<td class="w">{esc(w)}</td><td>{esc(m)}</td>' for w, m in row)
        if len(row) == 1:
            cells += '<td></td><td></td>'
        out.append(f'<tr>{cells}</tr>')
    out.append('</table>')
    return "\n".join(out)


# ================================================================ 問題編
def build_mondai():
    h = [band("問題編")]
    h.append(
        '<div class="intro">'
        '<b>品詞分解</b>とは、英文の一語一語が「文の骨組み（S V O C）」なのか'
        '「飾り（修飾語）」なのかを、記号で区別しながら読み切る作業のこと。'
        'なんとなく意味が取れる状態から、<b>どの語がどの語にかかるかを指させる状態</b>へ引き上げるのが目的である。<br>'
        'この教材は長文 4 本・分解 24 文で構成されている。'
        '<b>先に本文全体を読んでから</b>、下線と番号の付いた文を 1 文ずつ分解すること。'
        '分解は必ず鉛筆で本文に書き込み、解答編の分解図と<b>記号レベルで</b>照合する。'
        '訳が合っていても記号がずれていれば、それは「読めた」ではなく「当てた」である。'
        '<br><span style="font-size:8.8pt;color:#64748b">'
        '※本文は狙った構文を含めるために書き下ろした本教材オリジナルの英文であり、'
        '実際の入試問題ではない。本文中の数値・事例は説明のための設例を含む。</span>'
        '</div>')
    h.append('<div class="metarow">'
             '<div class="cell">氏名　　　　　　　　　　　　　　　</div>'
             '<div class="cell">実施日　　　　月　　　日</div>'
             '<div class="cell score">分解 24 文中　　　文</div>'
             '</div>')

    # --- 記号ルール ---
    h.append('<div class="partttl">分解の記号ルール<span class="en2">Notation</span></div>')
    h.append('<div class="rulegrid">')
    for r in RULES:
        h.append(f'<div class="rulecard {r["cls"]}"><div class="rh">{esc(r["h"])}</div>'
                 f'<div class="rb">{esc(r["b"])}</div>'
                 f'<div class="rex">{esc(r["ex"])}</div></div>')
    h.append('</div>')

    h.append('<div class="partttl">分解の手順<span class="en2">Procedure</span></div>')
    h.append('<div class="steps">')
    for i, s in enumerate(STEPS, 1):
        h.append(f'<div class="step"><span class="stepno">STEP {i}</span>'
                 f'<span>{s[2:]}</span></div>')
    h.append('</div>')

    h.append('<div class="partttl">記号の使い方（見本）<span class="en2">Worked examples</span></div>')
    h.append(LEGEND)
    for i, ex in enumerate(RULE_EXAMPLES, 1):
        root = parse(ex["dsl"])
        h.append(f'<div class="acard"><div class="ah"><span class="ano">見本 {i}</span>'
                 f'<span class="apat">{esc(ex["pat"])}</span></div>')
        h.append(render_analysis(root))
        h.append(f'<div class="notes">{ex["note"]}</div></div>')

    # --- 長文 ---
    for P in PASSAGES:
        h.append('<div>')
        h.append(f'<div class="partdiv">'
                 f'<div class="pt1">長文 {P["no"]}　{esc(P["title"])}</div>'
                 f'<div class="pt2">{esc(P["jtitle"])}　／　{esc(P["field"])}　／　'
                 f'約 {P["_wc"]} words　／　分解 6 文</div></div>')
        h.append(passage_html(P))
        h.append(vocab_html(P))

        # 問1 品詞分解
        h.append('<div class="partttl">問 1　品詞分解<span class="en2">Parsing</span></div>')
        h.append('<div class="instr">下線部 (1)〜(6) について、'
                 '( ) [ ] &lt; &gt; でカタマリを囲み、S・V・O・C・M の記号を書き込みなさい。'
                 '従属節の中の要素には S′ V′ … のようにダッシュを付けること。'
                 'そのうえで文型を答えなさい。（和訳は問 3 で扱う）</div>')
        for si, s in enumerate(P["sents"], 1):
            root = parse(s["dsl"])
            h.append('<div class="wq"><div class="wqh">'
                     f'<span class="qno">({si})</span></div>')
            h.append(render_blank(root, lh="3.1"))
            h.append('<div class="slots"><div class="sl">文型　第　　　文型</div>'
                     '<div class="sl wide">かかり方で迷った箇所（メモ）</div></div>')
            h.append('</div>')

        # 問2 4択
        h.append('<div class="partttl">問 2　カタマリの働きを選ぶ'
                 '<span class="en2">Function of the chunk</span></div>')
        h.append('<div class="instr">次の各問について、最も適切なものを ①〜④ から 1 つ選びなさい。</div>')
        for qi, q in enumerate(P["mcq"], 1):
            h.append(f'<div class="q"><div class="stem">'
                     f'<span class="qno">({qi})</span>　{q["q"]}</div><div class="choices">')
            for ci, c in enumerate(q["choices"]):
                h.append(f'<div>{CIRCLE[ci]} {c}</div>')
            h.append('</div></div>')

        # 問3 和訳（見出しと 2 問が分断されないよう 1 ブロックにまとめる）
        h.append('<div class="tglue">')
        h.append('<div class="partttl">問 3　下線部和訳<span class="en2">Translation</span></div>')
        h.append('<div class="instr">次の下線部を、構造がわかるように日本語に訳しなさい。</div>')
        for ti, t in enumerate(P["trans"], 1):
            h.append(f'<div class="q"><div class="stem"><span class="qno">({ti})</span>　'
                     f'本文の下線部 ({t["n"]})</div>')
            h.append('<div style="margin:3px 0 0 10px">'
                     + '<div class="jline"></div>' * 3 + '</div></div>')
        h.append('</div></div>')

    h.append(foot("問題編"))
    return "\n".join(h)


# ================================================================ 解答解説編
def build_kaisetsu():
    h = [band("解答・解説編")]
    h.append('<div class="intro">'
             '分解図は<b>記号レベルで</b>照合すること。'
             '訳が合っていても、かかり方の記号がずれていれば「読めていない」と判定する。'
             '各文には <b>骨組み</b>（カタマリを全部外し、節をつなぐ語だけ残したもの）を併記した。'
             'まずそこだけを見て、自分が同じ骨組みを取れていたかを確認すること。'
             '問 1 の和訳は問 3 で扱うが、各文の和訳も参考として全文に付けてある。'
             '<br><span style="font-size:8.8pt;color:#64748b">'
             '※本文は本教材オリジナルの英文（実際の入試問題ではない）。'
             '本文中の数値・事例は説明のための設例を含む。</span></div>')
    h.append(LEGEND)

    for P in PASSAGES:
        h.append('<div>')
        h.append(f'<div class="partdiv"><div class="pt1">長文 {P["no"]}　{esc(P["title"])}'
                 f'　解答・解説</div>'
                 f'<div class="pt2">{esc(P["jtitle"])}　／　{esc(P["field"])}</div></div>')

        # 問1
        h.append('<div class="partttl">問 1　品詞分解<span class="en2">Parsing</span></div>')
        for si, s in enumerate(P["sents"], 1):
            root = parse(s["dsl"])
            h.append('<div class="acard"><div class="ah">'
                     f'<span class="ano">({si})</span>'
                     f'<span class="apat">{esc(s["pat"])}</span>'
                     f'<span class="atag">{esc(s["tag"])}</span></div>')
            h.append(render_analysis(root))
            sk = render_skeleton(root)
            if sk:
                h.append(f'<div class="skel"><span class="lead">骨組み</span>{sk}</div>')
            h.append('<div class="notes"><ul>'
                     + "".join(f'<li>{n}</li>' for n in s["notes"]) + '</ul></div>')
            h.append(f'<div class="jatr"><b>和訳</b>{esc(s["ja"])}</div>')
            h.append('</div>')

        # 問2
        h.append('<div class="partttl">問 2　カタマリの働きを選ぶ'
                 '<span class="en2">Answers</span></div>')
        h.append('<table class="ans"><tr><th>問</th>'
                 + "".join(f'<td>({i})</td>' for i in range(1, len(P["mcq"]) + 1)) + '</tr>'
                 + '<tr><th>解答</th>'
                 + "".join(f'<td class="a">{CIRCLE[q["ans"]]}</td>' for q in P["mcq"])
                 + '</tr></table>')
        for qi, q in enumerate(P["mcq"], 1):
            h.append('<div class="acard"><div class="ah">'
                     f'<span class="ano">({qi})</span>'
                     f'<span class="apat">正解 {CIRCLE[q["ans"]]}　{q["choices"][q["ans"]]}</span>'
                     '</div>'
                     f'<div class="notes">{q["exp"]}</div></div>')

        # 問3
        h.append('<div class="partttl">問 3　下線部和訳<span class="en2">Translation</span></div>')
        for ti, t in enumerate(P["trans"], 1):
            s = P["sents"][t["n"] - 1]
            h.append('<div class="acard"><div class="ah">'
                     f'<span class="ano">({ti})</span>'
                     f'<span class="apat">本文 下線部 ({t["n"]})</span></div>')
            h.append(f'<div class="jatr"><b>模範解答</b>{esc(s["ja"])}</div>')
            h.append('<div class="notes"><b>採点ポイント</b><ul>'
                     + "".join(f'<li>{esc(p)}</li>' for p in t["points"]) + '</ul></div></div>')

        # 全訳
        h.append('<div class="partttl">全訳<span class="en2">Full translation</span></div>')
        for para in P["fulltrans"]:
            h.append(f'<div class="notes" style="margin-bottom:6px">{esc(para)}</div>')
        h.append('</div>')

    h.append(foot("解答・解説編"))
    return "\n".join(h)


def main():
    base = "英語_品詞分解トレーニング"
    q = os.path.join(DESKTOP, f"{base}_問題編.pdf")
    a = os.path.join(DESKTOP, f"{base}_解答解説編.pdf")
    render_pdf(build_mondai(), q, "英語 品詞分解トレーニング 問題編")
    render_pdf(build_kaisetsu(), a, "英語 品詞分解トレーニング 解答・解説編")


if __name__ == "__main__":
    # 語数などを content に注入するため、必ず check.py と同じ前処理を通す
    import check
    try:
        check.main()
    except SystemExit as e:
        if e.code:
            sys.exit(e.code)
    main()
