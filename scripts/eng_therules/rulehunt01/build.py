#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英語長文 ルール発見トレーニング No.01 — 問題編/解答解説編 の2冊を PDF 化。

  python3 build.py            (事前に python3 check.py が ALL PASS であること)

The Rules式シリーズ(scripts/eng_therules/)の視覚アイデンティティを踏襲。
HTML → Chrome --headless --print-to-pdf → fitz でノンブル刻印。
"""
import os, re, sys, subprocess, html, subprocess
import fitz
import content as C

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
OUT_Q = os.path.join(HERE, "ルール発見トレーニングNo01_問題編.pdf")
OUT_A = os.path.join(HERE, "ルール発見トレーニングNo01_解答解説編.pdf")

esc = lambda s: html.escape(str(s), quote=False)

TKEY = {t["key"]: t for t in C.TARGETS}

BASE_CSS = """
* { box-sizing: border-box; }
@page { size: A4; margin: 13mm 13mm 16mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Hiragino Mincho ProN","Yu Mincho",serif; color:#1a1a1a; font-size:10.3pt; line-height:1.62; margin:0; }
.gothic, h1,h2,h3,.band,.qno,.secttl,.tgname,.legend,.chip { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }
.en { font-family: Georgia,"Times New Roman",serif; }

.band { background: linear-gradient(90deg,#0f172a,#1e3a8a); color:#fff; padding:9px 14px; border-radius:8px;
  display:flex; justify-content:space-between; align-items:center; }
.band .l { font-size:14.5pt; font-weight:700; }
.band .l small { font-weight:600; font-size:9pt; opacity:.9; margin-left:8px; }
.band .r { text-align:right; font-size:8.5pt; line-height:1.4; }
.subline { margin:7px 2px 2px; font-size:9.3pt; color:#334155; }

.instr { font-size:9.4pt; background:#f1f5f9; border-left:4px solid #1e3a8a; padding:7px 10px; border-radius:4px; margin:8px 0; line-height:1.7; }
.instr b { color:#0f172a; }

table.tg { width:100%; border-collapse:collapse; font-size:9pt; margin:6px 0 2px; }
table.tg th, table.tg td { border:1px solid #cbd5e1; padding:4px 7px; vertical-align:top; }
table.tg th { background:#eef2ff; white-space:nowrap; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
table.tg td.nm { white-space:nowrap; font-weight:700; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
table.tg td.mk2 { white-space:nowrap; }

.secttl { font-size:12.5pt; font-weight:700; color:#0f172a; border-left:6px solid #1e3a8a;
  padding:2px 0 2px 10px; margin:14px 0 8px; page-break-after:avoid; }
.secttl .en2 { font-size:8.5pt; color:#64748b; margin-left:8px; }
.pb { page-break-before: always; }

/* passage */
.ptitle { text-align:center; font-size:12pt; font-weight:700; margin:8px 0 2px; font-family:Georgia,serif; }
.pjtitle { text-align:center; font-size:8.5pt; color:#64748b; margin-bottom:6px; }
.passage { border:1.2px solid #94a3b8; border-radius:8px; padding:10px 14px; }
.passage p { margin:0 0 7px; }
.passage .en { line-height:2.05; text-align:justify; }
.passage sup.sn { color:#dc2626; font-weight:700; font-size:7.5pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin-right:1px; }
.wcount { text-align:right; color:#64748b; font-size:8.5pt; margin-top:2px; }

/* questions */
.q { margin:0 0 10px; page-break-inside:avoid; }
.q .h { display:flex; align-items:baseline; gap:8px; margin-bottom:2px; }
.qno { color:#fff; border-radius:5px; padding:1px 9px; font-size:9.3pt; font-weight:700; }
.q .stem { font-size:9.8pt; }
table.fill { width:100%; border-collapse:collapse; font-size:9.2pt; margin-top:4px; }
table.fill th, table.fill td { border:1px solid #94a3b8; padding:3px 7px; }
table.fill th { background:#f8fafc; font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:600; white-space:nowrap; }
table.fill td { height:30px; }
.smallnote { font-size:8.6pt; color:#475569; margin-top:2px; }

/* annotations (解答編) */
.mk { border:1.6px solid #2563eb; border-radius:4px; padding:0 2px; color:#1d4ed8; font-weight:600; }
.cz { border-bottom:2.2px solid #dc2626; font-weight:600; }
.sj { text-decoration: underline wavy #7c3aed 1.2px; text-underline-offset:3.5px; }
.ps { background:#d1fae5; border-radius:3px; padding:0 1px; }
.pc { border-bottom:2px dashed #ea580c; font-weight:600; }
.wl { background:#fde68a; border-radius:3px; padding:0 2px; font-weight:700; }
.legend { font-size:8.6pt; margin:4px 0 8px; color:#334155; }
.legend span.item { margin-right:10px; white-space:nowrap; }

/* answer tables */
table.ans { width:100%; border-collapse:collapse; font-size:9.1pt; margin:3px 0 10px; }
table.ans th, table.ans td { border:1px solid #cbd5e1; padding:4px 7px; vertical-align:top; }
table.ans th { background:#eef2ff; font-family:"Hiragino Kaku Gothic ProN",sans-serif; white-space:nowrap; }
table.ans td.s { white-space:nowrap; font-weight:700; color:#1e3a8a; }
table.ans td.t { font-family:Georgia,serif; }
.tgname { font-weight:700; font-size:10.5pt; margin:10px 0 3px; page-break-after:avoid; }
.tgname .cnt { color:#64748b; font-size:8.8pt; font-weight:600; margin-left:6px; }
.invblk { page-break-inside:avoid; break-inside:avoid; }   /* 見出し+表の泣き別れ防止 */
td.nw { white-space:nowrap; }
.think { background:#eef2ff; border:1px solid #93c5fd; border-radius:6px; padding:6px 10px;
  font-size:9.3pt; margin:-4px 0 10px; page-break-inside:avoid; }
.think b { color:#1e3a8a; }

.lecture { border:1px solid #cbd5e1; border-left:5px solid #1e3a8a; border-radius:6px; padding:8px 11px; margin:0 0 9px; page-break-inside:avoid; font-size:9.5pt; }
.lecture .lh { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; font-size:10.3pt; margin-bottom:2px; }
.lecture .slogan { color:#b91c1c; font-weight:700; }
.trap { background:#fff7ed; border:1px solid #fdba74; border-radius:6px; padding:7px 10px; margin:0 0 8px; font-size:9.3pt; page-break-inside:avoid; }
.trap b { color:#9a3412; }

.trbox { font-size:9.4pt; }
.trbox .tr1 { margin:0 0 5px; }
.trbox .sn2 { color:#dc2626; font-weight:700; font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:8.3pt; }
.footnote { margin-top:12px; color:#64748b; font-size:8.2pt; border-top:1px solid #cbd5e1; padding-top:5px; }
"""


def header(kind):
    m = C.META
    return (f'<div class="band"><div class="l">{esc(m["series"])} {esc(m["no"])}'
            f'<small>{esc(kind)}</small></div>'
            f'<div class="r">{esc(m["subtitle"])}<br>対象: {esc(m["level"])} ｜ {esc(m["time"])}</div></div>')


def sup(n):
    return f'<sup class="sn">({n})</sup>'


def passage_html(p, annotate=False):
    parts = [f'<div class="ptitle">{esc(p["title"])}</div>',
             f'<div class="pjtitle">{esc(p["jtitle"])}</div>', '<div class="passage">']
    ann = C.ANNOT[p["key"]] if annotate else None
    for para in p["paras"]:
        buf = []
        for s in para:
            text = esc(s["en"])
            if ann:
                text = apply_annot(p["key"], s["n"], s["en"])
            buf.append(sup(s["n"]) + text)
        parts.append('<p class="en">' + " ".join(buf) + "</p>")
    words = len(re.split(r"\s+", " ".join(s["en"] for para in p["paras"] for s in para).strip()))
    parts.append("</div>")
    parts.append(f'<div class="wcount">({words} words)</div>')
    return "\n".join(parts)


def apply_annot(pkey, n, raw):
    """文 n に該当する全 ANNOT を span で巻く(t重複は class 結合)。"""
    items = {}
    for cat, lst in C.ANNOT[pkey].items():
        cls = TKEY[cat]["cls"]
        for it in lst:
            if it["s"] == n:
                items.setdefault(it["t"], set()).add(cls)
    if not items:
        return esc(raw)
    out = raw
    tokens = {}
    for i, (t, clss) in enumerate(sorted(items.items(), key=lambda kv: -len(kv[0]))):
        tok = f"\x00{i}\x00"
        if t not in out:
            sys.exit(f"annotate fail: {pkey} 文{n} 「{t[:30]}」not found (nesting?)")
        out = out.replace(t, tok, 1)
        tokens[tok] = (t, " ".join(sorted(clss)))
    out = esc(out)
    for tok, (t, cls) in tokens.items():
        out = out.replace(tok, f'<span class="{cls}">{esc(t)}</span>')
    return out


def legend():
    items = [f'<span class="item"><span class="{t["cls"]}">{esc(t["name"])}</span>（{esc(t["mark"])}）</span>'
             for t in C.TARGETS]
    return f'<div class="legend">凡例: {"".join(items)}</div>'


def targets_table():
    rows = []
    for t in C.TARGETS:
        rows.append(f'<tr><td class="nm" style="color:{t["color"]}">{t["no"]} {esc(t["name"])}</td>'
                    f'<td>{esc(t["what"])}<div class="smallnote">目印: {esc(t["sign"])}</div></td>'
                    f'<td class="mk2">{esc(t["mark"])}</td></tr>')
    return ('<table class="tg"><tr><th>ターゲット</th><th>何を探すか</th><th>付ける印</th></tr>'
            + "".join(rows) + "</table>")


def q_block(no, color, title, stem, fill_html=""):
    return (f'<div class="q"><div class="h"><span class="qno" style="background:{color}">{no}</span>'
            f'<b class="gothic">{esc(title)}</b></div>'
            f'<div class="stem">{stem}</div>{fill_html}</div>')


def fill_table(headers, nrows):
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    trs = "".join("<tr>" + "".join("<td></td>" for _ in headers) + "</tr>" for _ in range(nrows))
    return f'<table class="fill"><tr>{th}</tr>{trs}</table>'


# ------------------------------------------------------------------ 問題編
def build_q():
    m = C.META
    h = [header("問題編")]
    h.append('<div class="instr"><b>これは「読解問題」ではありません。</b>設問はすべて「本文から<b>探して、印をつける</b>」だけ。'
             '長文を読むときに文法・論理の目印が「勝手に目に飛び込んでくる」状態を作るための筋トレです。<br>'
             '<b>使い方</b>: 1周目=時間無制限で全部探す → 答え合わせ(解答編の色マーク本文と突き合わせ) → '
             '数日後の2周目=同じ本文を10分で再発見(スピード訓練)。')
    h.append('<div class="secttl">今日の6ターゲット</div>')
    h.append(targets_table())

    for p in C.PASSAGES:
        ann = C.ANNOT[p["key"]]
        h.append(f'<div class="pb"></div><div class="secttl">{esc(p["label"])}'
                 f'<span class="en2">{esc(p["title"])}</span></div>')
        h.append(passage_html(p))
        if p["hint"]:
            h.append('<div class="instr">ターゲットごとに<b>個数を明かした状態</b>で探す練習。本文に印をつけてから、表を埋めよう。</div>')
            counts = {k: len(v) for k, v in ann.items()}
            t = TKEY["marker"]
            h.append(q_block("問 1-1", t["color"], f'{t["no"]} {t["name"]}（全 {counts["marker"]} 個）',
                             f'マーカーを本文中で<b>{esc(t["mark"])}</b>み、下の表に整理せよ。',
                             fill_table(["文番号", "語句", "はたらき（逆接／対比／具体例／追加／強調／因果）"], counts["marker"])))
            t = TKEY["causal"]
            h.append(q_block("問 1-2", t["color"], f'{t["no"]} {t["name"]}（全 {counts["causal"]} か所）',
                             '因果を表す語句に<b>下線</b>を引き、本文の余白に矢印を書き込め。表には「向き」も書くこと。',
                             fill_table(["文番号", "語句", "向き（原因 → 結果 ／ 結果 ← 原因）"], counts["causal"])))
            t = TKEY["subj"]
            h.append(q_block("問 1-3", t["color"], f'{t["no"]} {t["name"]}（全 {counts["subj"]} 文）',
                             '仮定法が使われている文に<b>波線</b>を引き、「妄想の目印」(if ／ would ／ Without など)を抜き出せ。',
                             fill_table(["文番号", "妄想の目印（そのまま抜き出す）"], counts["subj"])))
            t = TKEY["passive"]
            h.append(q_block("問 1-4", t["color"], f'{t["no"]} {t["name"]}（全 {counts["passive"]} か所）',
                             'be動詞＋過去分詞を<b>〔　〕</b>で囲め。<br>'
                             '<span class="smallnote">考える1問: 文(9)の受動態には by 〜が無い代わりに、'
                             '何が「本当の原因」として示されているか。日本語で一言 → 記入欄最下段。</span>',
                             fill_table(["文番号", "be ＋ 過去分詞（そのまま抜き出す）"], counts["passive"]) +
                             '<table class="fill"><tr><th style="width:9em">考える1問の答え</th><td style="height:26px"></td></tr></table>'))
            t = TKEY["part"]
            h.append(q_block("問 1-5", t["color"], f'{t["no"]} {t["name"]}（全 {counts["part"]} か所）',
                             '分詞構文を<b>〈　〉</b>で囲み、意味（〜すると／〜して／そして〜）をメモせよ。',
                             fill_table(["文番号", "カタマリの先頭語", "意味"], counts["part"])))
            t = TKEY["will"]
            h.append(q_block("問 1-6", t["color"], f'{t["no"]} 助動詞 will（全 {counts["will"]} か所）',
                             'will を含む文に<b>◎</b>をつけ、その will が「未来の予定」か「習性・法則（100%必ず〜する）」かを判定せよ。'
                             '理由も書くこと。',
                             fill_table(["文番号", "判定（未来 ／ 習性・法則）＋そう判断した理由"], counts["will"] + 1)))
        else:
            total = sum(len(v) for v in ann.values())
            h.append(f'<div class="instr"><b>仕上げ: 個数ヒントなしの一括ハント。</b>6ターゲットすべてを自力で探し、'
                     f'本文に印(□・下線・波線・〔 〕・〈 〉・◎)をつけてから、下の集計表に「見つけた個数」を書け。'
                     f'<b>合計 {total} か所</b>ある。全部見つかるまで帰るな。</div>')
            rows = "".join(
                f'<tr><td class="nm" style="color:{t["color"]}">{t["no"]} {esc(t["name"])}</td>'
                f'<td style="width:5.5em"></td><td></td></tr>'
                for t in C.TARGETS)
            h.append('<table class="fill"><tr><th>ターゲット</th><th>見つけた個数</th>'
                     '<th>文番号のメモ</th></tr>' + rows + "</table>")
    h.append(f'<div class="footnote">{esc(C.META["note"])}</div>')
    return "\n".join(h)


# ------------------------------------------------------------------ 解答解説編
CAT_COLS = {
    "marker": (["文", "語句", "はたらき", "ひとこと"], lambda it: [it["t"], it["sub"], it["note"]], {1}),
    "causal": (["文", "語句", "向き", "ひとこと"], lambda it: [it["t"], it["dir"], it["note"]], {1}),
    "subj":   (["文", "該当箇所", "妄想の目印", "ひとこと"], lambda it: [it["t"], it["mk"], it["note"]], set()),
    "passive": (["文", "be ＋ 過去分詞", "ひとこと"], lambda it: [it["t"], it["note"]], set()),
    "part":   (["文", "カタマリ", "型", "ひとこと"], lambda it: [it["t"], it["kind"], it["note"]], {1}),
    "will":   (["文", "該当箇所", "型", "ひとこと"], lambda it: [it["t"], it["kind"], it["note"]], {1}),
}

THINK_ANS = ('<div class="think"><b>問1-4「考える1問」の答え:</b> 文(9)は by 〜(=きれいな字)を「原因ではない」と否定した上で、'
             '本当の原因を came from の後ろ——<b>手書きが要求する「余分に考えること」(the extra thinking that handwriting demands)</b>'
             '——として示している。受動態の by が消えたら、因果の別ルート(from)を探すのがコツ。</div>')


def inv_tables(pkey):
    out = []
    for t in C.TARGETS:
        items = C.ANNOT[pkey][t["key"]]
        heads, rowf, nowrap = CAT_COLS[t["key"]]
        blk = [f'<div class="tgname" style="color:{t["color"]}">{t["no"]} {esc(t["name"])}'
               f'<span class="cnt">全 {len(items)} {"文" if t["key"]=="subj" else "か所"}</span></div>']
        th = "".join(f"<th>{esc(x)}</th>" for x in heads)
        trs = []
        for it in items:
            cells = rowf(it)
            tds = f'<td class="s">({it["s"]})</td>'
            tds += f'<td class="t">{esc(cells[0])}</td>'
            for ci, c in enumerate(cells[1:], 1):
                cls = ' class="nw"' if ci in nowrap else ""
                tds += f"<td{cls}>{esc(c)}</td>"
            trs.append(f"<tr>{tds}</tr>")
        blk.append(f'<table class="ans"><tr>{th}</tr>{"".join(trs)}</table>')
        out.append(f'<div class="invblk">{"".join(blk)}</div>')
        if pkey == "p1" and t["key"] == "passive":
            out.append(THINK_ANS)
    return "\n".join(out)


def build_a():
    h = [header("解答・解説編")]
    # 集計表
    h.append('<div class="secttl">解答一覧（個数）</div>')
    rows = []
    for t in C.TARGETS:
        c1 = len(C.ANNOT["p1"][t["key"]])
        c2 = len(C.ANNOT["p2"][t["key"]])
        rows.append(f'<tr><td class="nm" style="color:{t["color"]}">{t["no"]} {esc(t["name"])}</td>'
                    f'<td style="text-align:center">{c1}</td><td style="text-align:center">{c2}</td>'
                    f'<td>{esc(t["slogan"])}</td></tr>')
    h.append('<table class="tg"><tr><th>ターゲット</th><th>訓練1</th><th>訓練2</th><th>★合言葉</th></tr>'
             + "".join(rows) + "</table>")

    for p in C.PASSAGES:
        h.append(f'<div class="pb"></div><div class="secttl">{esc(p["label"])}　解答'
                 f'<span class="en2">{esc(p["title"])}</span></div>')
        h.append(legend())
        h.append(passage_html(p, annotate=True))
        h.append('<div style="height:6px"></div>')
        h.append(inv_tables(p["key"]))

    # ひっかけ
    h.append('<div class="pb"></div><div class="secttl">ひっかけ注意報 — 「それっぽいのに違う」3つ</div>')
    for tr in C.TRAPS:
        tname = TKEY[tr["target"]]["name"]
        h.append(f'<div class="trap"><b>【{esc(tname)}のニセモノ】 {esc(tr["t"])}</b><br>{esc(tr["note"])}</div>')

    # ミニ講義
    h.append('<div class="secttl">ミニ講義 — 6ターゲットの「見つけ方」総まとめ</div>')
    for t in C.TARGETS:
        h.append(f'<div class="lecture"><div class="lh" style="color:{t["color"]}">{t["no"]} {esc(t["name"])}'
                 f'　<span style="font-size:8.5pt;color:#64748b">{esc(t["series"])}</span></div>'
                 f'<div class="slogan">★ {esc(t["slogan"])}</div>'
                 f'<div>{esc(C.LECTURES[t["key"]])}</div></div>')

    # 全訳
    for p in C.PASSAGES:
        h.append(f'<div class="pb"></div><div class="secttl">{esc(p["label"])}　全訳</div><div class="trbox">')
        for para in p["paras"]:
            buf = [f'<span class="sn2">({s["n"]})</span> {esc(C.TRANS[p["key"]][s["n"]])}' for s in para]
            h.append('<div class="tr1">' + "　".join(buf) + "</div>")
        h.append("</div>")
    h.append(f'<div class="footnote">{esc(C.META["note"])}</div>')
    return "\n".join(h)


def render(body, out_path):
    doc = (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
           f'<style>{BASE_CSS}</style></head><body>{body}</body></html>')
    tmp = os.path.join(HERE, "_" + os.path.basename(out_path).replace(".pdf", ".html"))
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(doc)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=12000", f"--print-to-pdf={out_path}",
                    "file://" + tmp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # ノンブル
    d = fitz.open(out_path)
    fnt = fitz.Font(fontfile=FONT_PATH)
    for i, page in enumerate(d):
        n = str(i + 1)
        tw = fnt.text_length(n, fontsize=9)
        page.insert_text((page.rect.width / 2 - tw / 2, page.rect.height - 20), n,
                         fontfile=FONT_PATH, fontname="AU", fontsize=9, color=(0.45, 0.45, 0.45))
    d.subset_fonts()
    tmp2 = out_path + ".tmp"
    d.save(tmp2, garbage=4, deflate=True, clean=True)
    d.close()
    os.replace(tmp2, out_path)
    d = fitz.open(out_path)
    print(f"WROTE {out_path} | pages: {d.page_count}")
    d.close()


def main():
    r = subprocess.run([sys.executable, os.path.join(HERE, "check.py")],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        print(r.stdout + r.stderr)
        sys.exit("check.py FAILED — 解答キーを直してからビルドすること")
    render(build_q(), OUT_Q)
    render(build_a(), OUT_A)


if __name__ == "__main__":
    main()
