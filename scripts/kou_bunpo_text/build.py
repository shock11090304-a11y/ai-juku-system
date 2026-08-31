# -*- coding: utf-8 -*-
"""
高校英文法テキスト（講義式・B5）  共通ビルダー

  python3 build.py vol1        # 問題編 + 解答解説編 の2冊 PDF を ~/Desktop に出力
  python3 build.py vol1 --keep # 中間HTML/PNGを残す

見本（市販の講義式テキスト）の**体裁のみ**を再現し、本文・例文・設問・解説はすべて自作。

■ ページモデル
  1講 = pages[] （必ず偶数。even index = 左ページ、odd = 右ページ＝見開き完結）
  @page は余白0にして .page div 自身が判型を持つ。1 div = 1 物理ページを保証する。
  はみ出しは overflow:hidden で切れて事故になるので、印刷直前に JS で実測して
  「OVERFLOW」バッジを刷り込む → fitz の全文検索で機械的に落とす（check.py）。

■ ブロック（1ページ = ブロックの列）
  {"t":"koza"}                         講扉見出し（第N講 タイトル）※その講の最初のページに1つ
  {"t":"ptindex"}                      「〜のポイント」枠（index から自動生成）
  {"t":"ph","n":1,"text":"…"}          ポイント【n】見出し
  {"t":"h","text":"●…"}                ●見出し
  {"t":"trad","text":"従来の英文法　「…」"}  眼鏡アイコン付き見出し
  {"t":"sh","text":"…"}                 小見出し（枠なしの行）
  {"t":"p","text":"…"}                  段落（先頭字下げなし）
  {"t":"box","rows":["…", …]}           1px枠。rows は行（\t で桁揃え）
  {"t":"box2","rows":[[l,r],…]}         1px枠・2桁
  {"t":"box3","rows":[[a,b,c],…]}       1px枠・3桁
  {"t":"list","rows":["…", …]}          枠なしの行送り
  {"t":"quote","en":…,"by":…,"ja":…,"byja":…,"note":…}   名言（グレー枠＋右下※）
  {"t":"sp","h":"6mm"}                  空き
  {"t":"enshu","groups":[…]}            ■入試問題演習
  {"t":"enshu_cont","groups":[…]}       見出しなしの続き（見開き右ページ用）
  {"t":"review"}                        ■復習テスト（review の tag 参照で自動生成）
  {"t":"note"}                          NOTE ページ

■ 設問
  {"tag":"…", "stem":"… ___ …", "lines":["A: …","B: ___."],
   "choices":[…], "ans":<0起点>, "ja":"和訳", "exp":"解説", "cols":1|2|4|5}
  ___（アンダースコア3つ）が空所（　）になる。
"""
import os, sys, re, html, glob, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))


def _first_path(cands):
    for c in cands:
        if not c:
            continue
        for p in (glob.glob(c) if ("*" in c) else [c]):
            if os.path.exists(p):
                return p
    return None


# ★刷るものは塾長の Mac（Chrome ＋ Hiragino）で焼くこと。ここでの探索は
#   「Mac のものがあればそれを最優先し、無い環境でも一応焼ける」ための代替でしかない。
#   フォントが違えば字幅が変わり、行送り・ページ高・はみ出し(OVERFLOW)の判定まで変わる。
#   CI やクラウドで焼いた PDF を「紙面を検査した」と言ってはいけない。
CHROME = _first_path([
    os.environ.get("KOU_BUNPO_CHROME"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/opt/pw-browsers/chromium-*/chrome-linux/chrome",      # Playwright 同梱（クラウド環境）
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
]) or shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chrome")

# 出力先。Desktop が無い環境（Linux・CI）ではリポジトリ内へ落とす。
DESKTOP = (os.environ.get("KOU_BUNPO_OUT")
           or (os.path.expanduser("~/Desktop")
               if os.path.isdir(os.path.expanduser("~/Desktop"))
               else os.path.join(HERE, "_out")))

PAREN = "⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽⑾⑿⒀⒁⒂⒃⒄⒅⒆⒇"

# 5択（不適当選択型）のラベル。見本と同じ半角 A〜E。
# ★問題編の選択肢表示（render_choices）と解答編の【答】（ans_label）は必ずここから引く。
#   別々に書くと「問題編=Ａ／解答編=A」のように黙ってずれ、check.py の照合だけが落ちる。
ALPHA = "ABCDE"


def esc(s):
    return html.escape(str(s), quote=False)


def paren(n):
    return PAREN[n - 1] if 1 <= n <= len(PAREN) else "(%d)" % n


def zenkaku_no(n):
    """第１講 の「１」。10 以上は素の数字（見本と同じ）。"""
    return "１２３４５６７８９"[n - 1] if 1 <= n <= 9 else str(n)


# ------------------------------------------------------------------ 文字装飾
# 本文データ中で使えるマーク（esc() を通しても壊れない記号だけで作る）
#   [b]…[/b]  太字   [u]…[/u]  下線   [i]…[/i]  斜体
#   [e]…[/e]  英字フォント強制（和文中に英単語を置くとき）
#   [k]…[/k]  細枠で囲む（「人」「物」などのプレースホルダ。見本と同じ白地・1px枠）
#   ___       空所（　　）
MARKS = [
    (re.compile(r"\[b\](.*?)\[/b\]", re.S), r"<b>\1</b>"),
    (re.compile(r"\[u\](.*?)\[/u\]", re.S), r'<span class="ul">\1</span>'),
    (re.compile(r"\[i\](.*?)\[/i\]", re.S), r"<i>\1</i>"),
    (re.compile(r"\[e\](.*?)\[/e\]", re.S), r'<span class="en">\1</span>'),
    (re.compile(r"\[g\](.*?)\[/g\]", re.S), r'<span class="gbox">\1</span>'),
    (re.compile(r"\[k\](.*?)\[/k\]", re.S), r'<span class="kbox">\1</span>'),
]
RE_BLANK = re.compile(r"_{3,}")


def tx(s):
    """データ文字列 → HTML。エスケープしてからマークを展開する。"""
    s = esc(s)
    s = RE_BLANK.sub('<span class="blank">（　　）</span>', s)
    for pat, rep in MARKS:
        s = pat.sub(rep, s)
    # 半角英数の連続は英字フォントで組む（和文ゴシックの英字は幅が狭く見本と違う）
    return s


# ------------------------------------------------------------------ CSS
CSS = r"""
* { box-sizing: border-box; }
@page { size: 182mm 257mm; margin: 0; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body {
  margin: 0; color: #000;
  /* ★Hiragino が本番。以降は Hiragino の無い環境（Linux・CI）用の代替で、
     字幅が違うので組版は本番と一致しない。刷るものは必ず Mac で焼くこと。 */
  font-family: "Hiragino Kaku Gothic ProN", "Yu Gothic", "Noto Sans CJK JP",
               "IPAGothic", sans-serif;
  font-size: 10.5pt; line-height: 1.7;
  font-variant-numeric: lining-nums; font-feature-settings: "lnum" 1, "palt" 0;
}
.en, .q .stem, .q .lines, .ch { font-family: "Helvetica Neue", Arial, "Liberation Sans",
                                "Hiragino Kaku Gothic ProN", "Noto Sans CJK JP", sans-serif; }

.page {
  position: relative; width: 182mm; height: 257mm;
  padding: 15mm 17mm 12.5mm; overflow: hidden;
  page-break-after: always; break-after: page;
}
.page:last-child { page-break-after: auto; break-after: auto; }
.body { position: relative; height: 100%; }
.pn { position: absolute; left: 0; right: 0; bottom: 6.5mm; text-align: center;
      font-size: 9pt; letter-spacing: .06em; }
.page.nonum { counter-increment: none; }
.page.nonum .pn { display: none; }

/* ---- 講扉見出し -------------------------------------------------- */
.koza { border-top: 3.2px solid #000; border-bottom: 1px solid #000;
        padding: 3.2mm 0 2.4mm 4mm; margin: 0 0 6mm;
        font-size: 15.5pt; font-weight: 700; letter-spacing: .04em; }
.koza .no { margin-right: 9mm; }

/* ---- 見出し類 ---------------------------------------------------- */
.ph  { font-size: 12.4pt; font-weight: 700; margin: 0 0 5mm; letter-spacing: .02em; }
.h   { font-weight: 700; margin: 0 0 2.2mm; }
.sh  { margin: 0 0 2.0mm; }
.p   { margin: 0 0 2.6mm; text-align: justify; }
.lbl { font-weight: 700; margin: 0 0 2.0mm; }
.trad { display: flex; align-items: center; gap: 2.4mm; margin: 0 0 2.2mm; }
.trad svg { flex: none; position: relative; top: .6mm; }

/* ---- 枠 ---------------------------------------------------------- */
/* 枠内の行は「ぶら下げ」。折り返し行が行頭に落ちると箇条書きが読めなくなる。 */
.box { border: 1px solid #000; padding: 2.4mm 3.4mm; margin: 0 0 4mm; }
.box .r, .list .r { display: block; padding-left: 1.3em; text-indent: -1.3em; }
.box table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.box td { vertical-align: top; padding: 0 2.6mm 0 0; }
.box td:last-child { padding-right: 0; }
.box td.nw { white-space: nowrap; }
.list { margin: 0 0 4mm; }
.ind { padding-left: 1.4em; text-indent: -1.4em; }
.ind2 { padding-left: 2.4em; }

/* ---- ポイント一覧枠（講扉直下） ---------------------------------- */
.ptindex { border: 1px solid #000; padding: 2.8mm 4mm; margin: 0 0 6mm; }
.ptindex .r { display: block; }
.ptindex .k { margin-right: 1.2em; }

/* ---- 名言 -------------------------------------------------------- */
.quote { background: #c9c9c9; padding: 3.2mm 4mm 3.4mm; margin: 0 0 1.6mm; }
.quote .qen { margin-bottom: 1.0mm; }
.quote .qby { text-align: right; margin-bottom: 1.4mm; }
.quote .qja { }
.quote .qbyja { text-align: right; }
.qnote { text-align: right; margin: 0 0 2mm; }

/* ---- 演習 -------------------------------------------------------- */
.sect { font-weight: 700; margin: 0 0 5.5mm; }
.grp { margin: 0 0 4mm; }
.grp .gh { display: flex; gap: 2.4mm; align-items: baseline; margin: 0 0 1.2mm; }
.qno { flex: none; border: 1px solid #000; min-width: 5.2mm; height: 5.2mm;
       line-height: 4.8mm; text-align: center; font-size: 9.2pt; }
.grp .gi { text-align: justify; }
.q { margin: 0 0 5.6mm; }
.q .row { display: flex; gap: 1.6mm; align-items: baseline; }
.q .n { flex: none; }
.q .stem { flex: 1; text-align: justify; }
.q .lines { margin-left: 6.4mm; }
.q .lines .r { display: block; }
.ch { margin: 0.4mm 0 0 6.4mm; }
.ch.c4 { display: flex; flex-wrap: wrap; gap: 0 2.0em; }
.ch.c2 { display: grid; grid-template-columns: 1fr 1fr; column-gap: 1.2em; }
.ch.c1 .ci { display: block; }
/* 5択（不適当選択型）は見本と同じ 3列固定＝A B C / D E の2行に必ず割れる。
   flex-wrap だと選択肢の長さ次第で 4+1 や 5 に化けて、講ごとに組みが変わる。 */
.ch.c5 { display: grid; grid-template-columns: repeat(3, 1fr); column-gap: 1.2em; }
.blank { letter-spacing: 0; }
.ul { border-bottom: 1px solid #000; }
.gbox { background: #d9d9d9; padding: 0 .25em; }
.kbox { border: 1px solid #000; padding: 0 .3em; margin: 0 .1em; }

/* ---- ルールの語句下に①②③を置く ---------------------------------- */
.stack { display: flex; flex-wrap: wrap; align-items: flex-end; margin: 0 0 4mm; }
.stack .sg { display: inline-block; text-align: center; }
.stack .sg .tp { display: block; white-space: pre; }
.stack .sg .bt { display: block; font-size: 9.5pt; line-height: 1.2; }
.stack .sg.u .tp { border-bottom: 1px solid #000; }

/* ---- NOTE -------------------------------------------------------- */
.notehd { font-family: "Helvetica Neue", Arial, sans-serif; font-style: italic;
          font-size: 12pt; margin: 0 0 5mm; }
.nl { border-bottom: 1.1px dotted #555; height: 8.0mm; }

/* ---- 目次 / 表紙 ------------------------------------------------- */
.toc { border: 1px solid #000; padding: 4mm 6mm 5mm; margin: 22mm 6mm 0; }
.toc h2 { text-align: center; font-size: 13pt; font-weight: 700; letter-spacing: .8em;
          margin: 0 0 4mm; text-indent: .8em; }
.toc table { width: 100%; border-collapse: collapse; }
.toc td { padding: .9mm 0; }
.toc td.k { width: 5.4em; }
.toc td.t { }
.toc td.pg { text-align: right; width: 4em; }
.cover { display: flex; flex-direction: column; justify-content: center; height: 100%;
         text-align: center; }
.cover .cfr { border: 2.4px solid #000; padding: 16mm 8mm; }
.cover .cfr2 { border: 1px solid #000; padding: 18mm 6mm; }
.cover .ct { font-size: 24pt; font-weight: 700; letter-spacing: .12em; line-height: 1.5; }
.cover .cs { font-size: 12pt; letter-spacing: .16em; margin-top: 7mm; }
.cover .cv { font-size: 11pt; letter-spacing: .1em; margin-top: 3mm; }
.cover .cb { font-size: 11.5pt; letter-spacing: .18em; margin-top: 26mm; }
.tobira { display: flex; align-items: center; justify-content: center; height: 100%; }
.tobira .t { font-size: 20pt; font-weight: 700; letter-spacing: 1em; text-indent: 1em; }

/* ---- 解答解説編 -------------------------------------------------- */
.ah { border-top: 3.2px solid #000; border-bottom: 1px solid #000; padding: 2.6mm 0 2.0mm 3mm;
      margin: 0 0 5mm; font-size: 13.5pt; font-weight: 700; letter-spacing: .04em; }
.asec { font-weight: 700; margin: 4.5mm 0 2.2mm; }
.asub { font-weight: 700; margin: 2.6mm 0 1.6mm; padding-left: 1.4em; text-indent: -1.4em; }
.arev { padding-left: 1.4em; letter-spacing: .02em; }
.anote { padding-left: 1.4em; font-size: 9.5pt; margin-top: 1mm; }
.aq { margin: 0 0 3.4mm; text-align: justify; }
.aq .ans { font-weight: 700; }
.aq .lb { font-weight: 700; }
.aq .ja, .aq .ex { display: block; padding-left: 1.2em; text-indent: -1.2em; }
.ovf { position: absolute; right: 2mm; top: 2mm; background: #000; color: #fff;
       font-size: 8pt; padding: 1mm 2mm; }
"""

# 解答解説編は分量がデータ次第なので固定ページに嵌めず、通常フローで流し込む。
CSS_FLOW = r"""
@page { size: 182mm 257mm; margin: 15mm 17mm 16mm; }
.page { position: static; width: auto; height: auto; padding: 0; overflow: visible; }
.page .body { height: auto; }
.flow { }
.apagebreak { page-break-after: always; break-after: page; height: 0; }
.ah { break-inside: avoid; }
.aq { break-inside: avoid; }
/* 見出しの泣き別れを止める（見出しだけがページ末に残るのを禁止） */
.asec, .asub { break-after: avoid; page-break-after: avoid; break-inside: avoid; }
.ablock { break-inside: avoid; page-break-inside: avoid; }
"""

# 印刷直前にページの実高さを測って、はみ出しているページに黒バッジを刷り込む。
OVERFLOW_JS = r"""
<script>
(function(){
  document.querySelectorAll('.page').forEach(function(p, i){
    var b = p.querySelector('.body');
    if(!b) return;
    if(b.scrollHeight - b.clientHeight > 2){
      var d = document.createElement('div');
      d.className = 'ovf';
      d.textContent = 'OVERFLOW p' + (i+1) + ' +' + (b.scrollHeight - b.clientHeight) + 'px';
      p.appendChild(d);
    }
  });
})();
</script>
"""

GLASSES = ('<svg width="23" height="13" viewBox="0 0 46 26" fill="none" '
           'stroke="currentColor" stroke-width="1.9" stroke-linecap="round">'
           '<circle cx="13" cy="16" r="8.4"/><circle cx="33" cy="16" r="8.4"/>'
           '<path d="M21.4 15 q2.6 -2 3.2 0"/>'
           '<path d="M4.7 11.5 C4 4, 8 1.5, 13 2.6"/>'
           '<path d="M41.3 11.5 C42 4, 38 1.5, 33 2.6"/></svg>')


# ================================================================== 描画
def r_cells(cells, w=None, nw=0):
    out = []
    for i, c in enumerate(cells):
        style = ' style="width:%s"' % w[i] if w and i < len(w) and w[i] else ""
        cls = ' class="nw"' if i < nw else ""
        out.append("<td%s%s>%s</td>" % (cls, style, tx(c)))
    return "".join(out)


def render_block(b, ctx):
    t = b["t"]
    if t == "koza":
        return ('<div class="koza"><span class="no">第%s講</span>'
                '<span class="ttl">%s</span></div>'
                % (zenkaku_no(ctx["no"]), tx(ctx["title"])))
    if t == "ptindex":
        rows = "".join(
            '<span class="r"><span class="k">【%d】</span>%s</span>' % (i + 1, tx(s))
            for i, s in enumerate(ctx["index"]))
        return ('<div class="lbl">%sのポイント</div><div class="ptindex">%s</div>'
                % (tx(ctx["title"]), rows))
    if t == "ph":
        return '<div class="ph">ポイント【%d】　%s</div>' % (b["n"], tx(b["text"]))
    if t == "h":
        return '<div class="h">%s</div>' % tx(b["text"])
    if t == "sh":
        return '<div class="sh">%s</div>' % tx(b["text"])
    if t == "lbl":
        return '<div class="lbl">%s</div>' % tx(b["text"])
    if t == "p":
        return '<div class="p%s">%s</div>' % (
            " ind" if b.get("ind") else "", tx(b["text"]))
    if t == "trad":
        return ('<div class="trad">%s<span><b>従来の英文法</b>　%s</span></div>'
                % (GLASSES, tx(b["text"])))
    if t in ("box", "list"):
        cls = "box" if t == "box" else "list"
        rows = "".join('<span class="r%s">%s</span>'
                       % (" ind" if b.get("ind") else "", tx(s)) for s in b["rows"])
        return '<div class="%s">%s</div>' % (cls, rows)
    if t in ("box2", "box3"):
        rows = "".join("<tr>%s</tr>" % r_cells(r, b.get("w"), b.get("nw", 1))
                       for r in b["rows"])
        return '<div class="box"><table>%s</table></div>' % rows
    if t == "tbl":                       # 枠なしの桁揃え
        rows = "".join("<tr>%s</tr>" % r_cells(r, b.get("w"), b.get("nw", 1))
                       for r in b["rows"])
        return '<div class="list"><table>%s</table></div>' % rows
    if t == "stack":
        # segs = [[表示文字列, 下に置く印(無ければ""), 下線を引くか(bool)], ...]
        segs = "".join(
            '<span class="sg%s"><span class="tp">%s</span>'
            '<span class="bt">%s</span></span>'
            % (" u" if (len(s) > 2 and s[2]) else "", tx(s[0]), tx(s[1]) or "&nbsp;")
            for s in b["segs"])
        return '<div class="stack">%s</div>' % segs
    if t == "quote":
        return ('<div class="quote"><div class="qen en">%s</div>'
                '<div class="qby en">%s</div>'
                '<div class="qja">%s</div><div class="qbyja">%s</div></div>'
                '<div class="qnote">%s</div>'
                % (tx(b["en"]), tx(b["by"]), tx(b["ja"]), tx(b["byja"]), tx(b["note"])))
    if t == "sp":
        return '<div style="height:%s"></div>' % b.get("h", "5mm")
    if t == "enshu":
        return ('<div class="sect">■入試問題演習</div>'
                + "".join(render_group(g) for g in b["groups"]))
    if t == "enshu_cont":
        return "".join(render_group(g) for g in b["groups"])
    if t == "review":
        return ('<div class="sect">■復習テスト</div>'
                + render_group(ctx["review_group"]))
    if t == "note":
        return ('<div class="notehd">NOTE</div>'
                + '<div class="nl"></div>' * b.get("lines", 27))
    raise ValueError("unknown block type: %r" % t)


def choice_cols(item):
    if item.get("cols"):
        return item["cols"]
    ch = item["choices"]
    mx = max(len(c) for c in ch)
    if len(ch) == 5:
        return 5
    if mx <= 13 and sum(len(c) for c in ch) <= 46:
        return 4
    if mx <= 26:
        return 2
    return 1


def render_choices(item):
    ch = item["choices"]
    cols = choice_cols(item)
    # ラベル様式は ans_label() と同じ「選択肢数」で決める（cols はレイアウト専用）。
    # cols で決めると、5択に cols:1 を付けた瞬間に問題編=数字/解答編=Ａ〜Ｅ とずれる。
    if len(ch) == 5:
        inner = "".join('<span class="ci">%s　%s</span>' % (ALPHA[i], tx(c))
                        for i, c in enumerate(ch))
    else:
        inner = "".join('<span class="ci">%d. %s</span>' % (i + 1, tx(c))
                        for i, c in enumerate(ch))
    return '<div class="ch c%d">%s</div>' % (cols, inner)


def render_item(item, n):
    out = ['<div class="q">']
    if item.get("stem"):
        out.append('<div class="row"><span class="n">%s</span>'
                   '<span class="stem">%s</span></div>' % (paren(n), tx(item["stem"])))
        if item.get("lines"):
            out.append('<div class="lines">%s</div>'
                       % "".join('<span class="r">%s</span>' % tx(s)
                                 for s in item["lines"]))
    else:
        ls = item["lines"]
        out.append('<div class="row"><span class="n">%s</span>'
                   '<span class="stem">%s</span></div>' % (paren(n), tx(ls[0])))
        if len(ls) > 1:
            out.append('<div class="lines">%s</div>'
                       % "".join('<span class="r">%s</span>' % tx(s) for s in ls[1:]))
    out.append(render_choices(item))
    out.append("</div>")
    return "".join(out)


def render_group(g):
    head = ""
    if g.get("no"):
        head = ('<div class="gh"><span class="qno">%d</span>'
                '<span class="gi">%s</span></div>' % (g["no"], tx(g["instr"])))
    elif g.get("instr"):
        head = '<div class="gh"><span class="gi ind">%s</span></div>' % tx(g["instr"])
    body = "".join(render_item(it, i + 1) for i, it in enumerate(g["items"]))
    return '<div class="grp">%s%s</div>' % (head, body)


# ================================================================== 組み立て
def all_items(koza):
    """講内の全設問を (group, index, item) で列挙。"""
    for pg in koza["pages"]:
        for b in pg:
            if b["t"] in ("enshu", "enshu_cont"):
                for g in b["groups"]:
                    for i, it in enumerate(g["items"]):
                        yield g, i + 1, it


def balance_answers(kozas):
    """正解番号を大問ごとに 0〜3 の順列で配る。

    ★手で番号を振ると必ず偏る（実測で 2 番が 57%）。生徒は「迷ったら2」で当てられる。
      全体だけ均そうとしても大問内が偏るので、[u]大問ごと[/u]に順列を配り切る
      （scripts/kyotsu_mogi2026/answer_positions.py と同じ方針）。
    ★同じ item オブジェクトを復習テストが参照するので、並べ替えは1回だけ。
    ★5択（不適当選択型）と "fix": True の設問は解説が記号を名指しするので触らない。
    """
    import random
    for k in kozas:
        if k.get("_balanced"):
            continue
        k["_balanced"] = True
        gi = 0
        for pg in k["pages"]:
            for b in pg:
                if b["t"] not in ("enshu", "enshu_cont"):
                    continue
                for g in b["groups"]:
                    gi += 1
                    rnd = random.Random("kbt-%d-%d" % (k["no"], gi))
                    pool, targets = [], []
                    for _ in g["items"]:
                        if not pool:
                            pool = [0, 1, 2, 3]
                            rnd.shuffle(pool)
                        targets.append(pool.pop())
                    for it, t in zip(g["items"], targets):
                        if it.get("fix") or len(it["choices"]) != 4 or it["ans"] == t:
                            continue
                        a, ch = it["ans"], it["choices"]
                        ch[a], ch[t] = ch[t], ch[a]
                        it["ans"] = t
    return kozas


def build_review_group(koza):
    by_tag = {it["tag"]: it for _, _, it in all_items(koza) if it.get("tag")}
    items = []
    for tag in koza["review"]:
        if tag not in by_tag:
            raise KeyError("第%d講 復習テストの tag が演習に無い: %r" % (koza["no"], tag))
        items.append(by_tag[tag])
    return {"instr": "空欄に入る最も適切なものを選びなさい。", "items": items}


def koza_pages(koza):
    ctx = {"no": koza["no"], "title": koza["title"], "index": koza["index"],
           "review_group": build_review_group(koza)}
    return ["".join(render_block(b, ctx) for b in pg) for pg in koza["pages"]]


def page_div(inner, nonum=False):
    return ('<div class="page%s"><div class="body">%s</div><div class="pn"></div></div>'
            % (" nonum" if nonum else "", inner))


def page_starts(kozas):
    """各講の開始ノンブル。p1 = 目次、各講は必ず偶数ページ（＝左ページ）から始まる。"""
    start, out = 2, {}
    for k in kozas:
        n = len(k["pages"])
        assert n % 2 == 0, "第%d講のページ数が奇数(%d)" % (k["no"], n)
        out[k["no"]] = start
        start += n
    return out


def make_toc(meta, kozas):
    st = page_starts(kozas)
    rows = "".join('<tr><td class="k">第%s講</td><td class="t">%s</td>'
                   '<td class="pg">p%d</td></tr>'
                   % (zenkaku_no(k["no"]), tx(k["title"]), st[k["no"]]) for k in kozas)
    return '<div class="toc"><h2>目　次</h2><table>%s</table></div>' % rows


def cover_html(meta, sub):
    return ('<div class="cover"><div class="cfr"><div class="cfr2">'
            '<div class="ct">%s</div><div class="cs">%s</div><div class="cv">%s</div>'
            '<div class="cb">%s</div></div></div></div>'
            % (tx(meta["title"]), tx(sub), tx(meta["volume"]), tx(meta["brand"])))


def document(body, meta, mode="fixed"):
    css = CSS if mode == "fixed" else CSS + CSS_FLOW
    js = OVERFLOW_JS if mode == "fixed" else ""
    return ("<!doctype html><html><head><meta charset='utf-8'>"
            "<title>%s</title><style>%s</style></head><body>%s%s</body></html>"
            % (esc(meta["title"]), css, body, js))


def build_mondai(meta, kozas):
    pages = [page_div(cover_html(meta, "問題編"), nonum=True)]
    pages.append(page_div(make_toc(meta, kozas)))     # p1
    for k in kozas:
        for inner in koza_pages(k):
            pages.append(page_div(inner))
    return document("".join(pages), meta)


# ------------------------------------------------------------------ 解答解説編
def build_kaitou(meta, kozas):
    st = page_starts(kozas)
    body = ['<div style="height:224mm">%s</div><div class="apagebreak"></div>'
            % cover_html(meta, "解答解説編")]
    for k in kozas:
        body.append('<div class="ah">第%s講　%s</div>' % (zenkaku_no(k["no"]), tx(k["title"])))
        for pi, pg in enumerate(k["pages"]):
            pno = st[k["no"]] + pi
            for b in pg:
                if b["t"] not in ("enshu", "enshu_cont"):
                    continue
                if b["t"] == "enshu":
                    body.append('<div class="asec">■入試問題演習（問題編 p%d）</div>' % pno)
                for g in b["groups"]:
                    if g.get("no"):
                        body.append('<div class="asub">%d　%s</div>' % (g["no"], tx(g["instr"])))
                    for i, it in enumerate(g["items"]):
                        body.append(render_answer(it, i + 1))
        rg = build_review_group(k)
        body.append('<div class="ablock"><div class="asec">■復習テスト（問題編 p%d）</div>'
                    % (st[k["no"]] + len(k["pages"]) - 2))
        body.append('<div class="arev">%s</div>'
                    % "　".join("%s %s" % (paren(i + 1), ans_label(it))
                                for i, it in enumerate(rg["items"])))
        body.append('<div class="anote">※復習テストは入試問題演習からの再出題です。'
                    '解説は上記の該当問題を参照してください。</div></div>')
        body.append('<div class="apagebreak"></div>')
    return document('<div class="flow">%s</div>' % "".join(body), meta, mode="flow")


def ans_label(it):
    """正解ラベルの唯一の定義。問題編の選択肢表示と解答編の【答】を必ず一致させる。"""
    return ALPHA[it["ans"]] if len(it["choices"]) == 5 else str(it["ans"] + 1)


def render_answer(it, n):
    lab = ans_label(it)
    return ('<div class="aq"><span class="ans">%s　【答】%s　%s</span>'
            '<span class="ja">〔訳〕%s</span>'
            '<span class="ex">〔解説〕%s</span></div>'
            % (paren(n), lab, tx(it["choices"][it["ans"]]), tx(it["ja"]), tx(it["exp"])))


# ================================================================== 出力
def to_pdf(html_text, outdir, stem):
    os.makedirs(outdir, exist_ok=True)
    hp = os.path.join(outdir, stem + ".html")
    pp = os.path.join(outdir, stem + ".pdf")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html_text)
    if not CHROME:
        raise RuntimeError(
            "PDF を焼くブラウザが見つからない。Chrome を入れるか "
            "KOU_BUNPO_CHROME=/path/to/chrome を指定すること。")
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
           "--virtual-time-budget=20000", "--print-to-pdf=" + pp, "file://" + hp]
    if os.name == "posix" and sys.platform != "darwin" and os.geteuid() == 0:
        cmd.insert(1, "--no-sandbox")      # Linux の root では sandbox が起動できない
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode or not os.path.exists(pp):
        # ★裸の CalledProcessError だと原因が出ない。ブラウザの言い分をそのまま見せる。
        raise RuntimeError("PDF 生成に失敗 (%s)\n%s" % (CHROME, (r.stderr or "")[-800:]))
    return pp


# ノンブルを fitz で刻むためのフォント。「— 1 —」の全角ダッシュが出る和文フォントを選ぶ。
FONT_PATH = _first_path([
    os.environ.get("KOU_BUNPO_FONT"),
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
])


def stamp_page_numbers(pdf_path, skip=1):
    """ノンブルは fitz で刻む（CSS カウンタと .page 分割の噛み合わせ事故を避ける）。
    skip 枚（表紙）を飛ばし、その次を 1 とする。"""
    if not FONT_PATH:
        raise RuntimeError(
            "ノンブルを刻むフォントが見つからない。和文フォントを入れるか "
            "KOU_BUNPO_FONT=/path/to/font.ttf を指定すること。")
    import fitz
    doc = fitz.open(pdf_path)
    for i, page in enumerate(doc):
        if i < skip:
            continue
        txt = "— %d —" % (i - skip + 1)
        box = fitz.Rect(0, page.rect.height - 30, page.rect.width, page.rect.height - 12)
        page.insert_textbox(box, txt, fontsize=9, fontfile=FONT_PATH, fontname="AU",
                            align=1, color=(0, 0, 0))
    doc.save(pdf_path, incremental=True, encryption=0)
    doc.close()


def render_pngs(pdf_path, outdir, dpi=110, pages=None):
    import fitz
    os.makedirs(outdir, exist_ok=True)
    doc = fitz.open(pdf_path)
    out = []
    for i, page in enumerate(doc):
        if pages and (i + 1) not in pages:
            continue
        p = os.path.join(outdir, "p%03d.png" % (i + 1))
        page.get_pixmap(dpi=dpi).save(p)
        out.append(p)
    doc.close()
    return out


def spread_pngs(pdf_path, outdir, dpi=100, first=1, last=None, skip=1):
    """見開き（左＝偶数ノンブル）で1枚に合成する。first/last はノンブル。"""
    import fitz
    os.makedirs(outdir, exist_ok=True)
    doc = fitz.open(pdf_path)
    first += skip                                  # ノンブル → PDF ページ番号
    last = (last + skip) if last else doc.page_count
    out = []
    i = first
    while i <= last:
        left = doc[i - 1].get_pixmap(dpi=dpi)
        right = doc[i].get_pixmap(dpi=dpi) if i < last else None
        w = left.width * (2 if right else 1)
        canvas = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, w, left.height), False)
        canvas.set_rect(canvas.irect, (255, 255, 255))
        canvas.copy(left, fitz.IRect(0, 0, left.width, left.height))
        if right:
            right.set_origin(left.width, 0)
            canvas.copy(right, fitz.IRect(left.width, 0, w, right.height))
        p = os.path.join(outdir, "s%03d.png" % i)
        canvas.save(p)
        out.append(p)
        i += 2
    doc.close()
    return out


# ================================================================== main
def build_volume(mod, keep=False):
    import time
    meta, kozas = mod.META, balance_answers(mod.KOZAS)
    outdir = os.path.join(HERE, "_build", "%s_%d" % (meta["slug"], int(time.time())))
    os.makedirs(outdir, exist_ok=True)

    # PDF の鮮度検査用：何をビルドしたかを刻む（直したのにビルドし忘れ対策）
    import hashlib, json
    man = {src: hashlib.sha256(open(fp, "rb").read()).hexdigest()
           for src, fp in (("content", mod.__file__),
                           ("build", os.path.abspath(__file__)))}
    with open(os.path.join(outdir, "manifest.json"), "w") as f:
        json.dump(man, f)

    m = to_pdf(build_mondai(meta, kozas), outdir, meta["slug"] + "_mondai")
    stamp_page_numbers(m, skip=1)
    k = to_pdf(build_kaitou(meta, kozas), outdir, meta["slug"] + "_kaitou")
    stamp_page_numbers(k, skip=1)

    dest = []
    os.makedirs(DESKTOP, exist_ok=True)      # Desktop の無い環境では _out を作る
    for src, name in ((m, meta["file_mondai"]), (k, meta["file_kaitou"])):
        d = os.path.join(DESKTOP, name)
        shutil.copyfile(src, d)
        dest.append(d)
    print("built:", outdir)
    for d in dest:
        print("  →", d)
    return outdir, m, k


if __name__ == "__main__":
    import importlib
    vol = sys.argv[1] if len(sys.argv) > 1 else "vol1"
    sys.path.insert(0, HERE)
    build_volume(importlib.import_module("content_" + vol))
