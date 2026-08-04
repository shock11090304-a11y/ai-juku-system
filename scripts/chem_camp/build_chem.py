#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""化学［理論］総復習トレーニング(全18単元・108問)を KaTeX 教科書組版で PDF 化する。

  python3 build_chem.py

数学の第2集(build_kiso2.py)と同じ体裁で組む。描画部品(CSS / stamp_pdf / KATEX / CHROME)は
math_workbook の build_html・build_kiso から再利用する。
"""
import os, sys, subprocess, datetime
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
MATH = os.path.abspath(os.path.join(HERE, "..", "math_workbook"))
sys.path.insert(0, MATH)

import build_html as B          # noqa: E402  KATEX/CHROME/esc/stamp_pdf/LEVEL
import build_kiso as K          # noqa: E402  CSS と reorder
import content_chem as C        # noqa: E402

OUT = os.path.join(HERE, "kagaku_riron_soufukushu.pdf")   # ★日本語名はNFD/NFCで落ちるので英数字で生成→mv

# ★宛名はコードに書かない。このリポジトリは PUBLIC なので、書くと生徒の氏名が公開される。
#   刷るときだけ環境変数で渡す:  STUDENT_NAME="姓 名" python3 build_chem.py
#   空のままなら宛名なしの汎用版が出る。(scripts/check_no_pii.py が直書きを CI で止める)
STUDENT = os.environ.get("STUDENT_NAME", "")
TITLE = "化学［理論］総復習トレーニング"
SUBTITLE = "気体と液体／状態変化／エネルギー／反応の速さ／平衡／電池と電気分解"
TAGLINE = "夏の勉強合宿 4日間で理論化学の6分野を1周する"
BOOK = "化学［理論］総復習トレーニング"
HOWTO = ("【この問題集の使い方】理論化学の6分野を、どれも取りこぼさないように18単元・108問へ均等に割りました。"
         "1単元6問（基礎2・標準3・発展1）で、はじめの1問は必ず基礎です。"
         "各編のとびらにある「攻略の手順」を先に読んでから解き始めてください。"
         "解説は途中の式を省いていません。数値を代入した形で最後まで書いてあるので、"
         "分からなかった問題は解説をノートに写してから、何も見ずにもう一度解くのがいちばん効きます。"
         "エンタルピー（$\\Delta H$）の符号は、発熱なら負・吸熱なら正。ここだけは最初に頭に入れてください。")


def toc_html(parts):
    rows, ui = [], 1
    for p in parts:
        rows.append(f'<div class="toc-part">{B.esc(p["area"])}</div>')
        for u in p["units"]:
            rows.append(
                f'<div class="toc-row"><span class="toc-no">C{ui:02d}</span>'
                f'<span class="toc-name">{B.esc(u["name"])}</span>'
                # ★ tag は作問管理用のスラッグ(boyle-charles-ideal-gas 等)。生徒配布物に
                #   内部識別子を出さない(しかも 07〜09 だけ日本語で体裁も揃っていなかった)。
                f'<span class="toc-n">{len(u["problems"])}問</span></div>')
            ui += 1
    return "".join(rows)


ALLOW_TAGS = (("&lt;b&gt;", "<b>"), ("&lt;/b&gt;", "</b>"), ("&lt;br&gt;", "<br>"))


def unesc(s):
    """esc 済み文字列のうち、教材で使ってよいタグ(<b>/<br>)だけ復元する。"""
    for a, b in ALLOW_TAGS:
        s = s.replace(a, b)
    return s


def detail(s):
    """解説テキスト → HTML。<b>/<br> は生かし、実改行を <br> に。"""
    return unesc(B.esc(s)).replace("\n", "<br>")


def prob_html(q):
    lvl = B.LEVEL.get(q.get("level"))
    tag = f'<span class="lv" style="color:{lvl[1]}">[{lvl[0]}]</span> ' if lvl else ""
    return (f'<div class="prob"><span class="no">{q["no"]}.</span> {tag}'
            f'<span class="stem">{unesc(B.esc(q["stem"]))}</span></div>')


def ans_html(q):
    return (f'<div class="prob"><div class="ansline"><span class="no">{q["no"]}.</span> '
            f'<span class="ans">{unesc(B.esc(q.get("answer","")))}</span></div>'
            f'<div class="exp">{detail(q.get("explanation",""))}</div></div>')


def section_html(parts, kind):
    out, ui = [], 1
    kicker = "問題" if kind == "prob" else "解答"
    for p in parts:
        pts = C.PART_POINTS.get(p["area"], "")
        box = (f'<div class="pointbox pdivbox"><div class="pb-t">◆ 攻略の手順（先に読む）</div>{detail(pts)}</div>'
               if pts else "")
        out.append(f'<div class="pdiv"><h2>{B.esc(p["area"])}</h2>'
                   f'<div class="d-sub">{B.esc(p.get("sub",""))}</div>{box}</div>')
        for u in p["units"]:
            out.append('<section class="unit">')
            # ★単元番号に C を付ける。この生徒は同時期に数学「第2集」(単元13〜27)を解いており、
            #   C 無しだと化学13〜18と数学13〜18が冊子上で同じ「13」になる。自己採点シートの
            #   写真から番号を回収したときに、どちらの教材の×か判別できなくなる。
            out.append(f'<div class="band"><div class="band-k">{kicker}　C{ui:02d}</div>'
                       f'<div class="band-t">{B.esc(u["name"])}</div></div>')
            cur = None
            for q in u["problems"]:
                g = q.get("group", "")
                if g != cur:
                    cur = g
                    out.append(f'<h3 class="grp">■ {B.esc(g)}</h3>')
                out.append(prob_html(q) if kind == "prob" else ans_html(q))
            out.append('</section>')
            ui += 1
    return "\n".join(out)


EXTRA_CSS = """
.pdiv { page-break-before:always; padding-top:34mm; text-align:center; }
.pdivbox { text-align:left; margin:16mm auto 0; max-width:150mm; }
.cover .who { position:absolute; top:150mm; width:100%; text-align:center;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; color:#1f3a5f; font-size:13pt; }
.cover .who span { border-bottom:1.4px solid #c8a24e; padding:0 26px 4px; }
/* 化学式は $\\mathrm{}$ が多く 1 行に数式が何個も入る。行送りを詰めすぎると
   上下の添字(H_2 の 2 と Cu^{2+} の 2+)が視覚的にぶつかるので広めに取る。
   ★1.95 では足りず、行内 \\dfrac の分母が次の行の指数に物理的に重なって
   印刷されていた(例: 0.20/2.0 の「2.0」が次行「0.80^2」の指数の上に乗り、
   指数が読めなくなっていた)。KaTeX の vlist は height:0 なので数式の高さが
   行ボックスに算入されず、.katex を inline-block にしても解消しない。
   実測で全71ページの重なりが 0 になる値まで上げる(2.7 / 紙は +1 ページ)。
   数式を含む段落の行送りを変えたら、必ず PDF の字形矩形で重なり 0 を再確認すること。 */
.exp { line-height: 2.7; }
.pointbox { line-height: 2.2; }
.exp .katex, .pointbox .katex { line-height: 1.2; }
.prob .stem { line-height: 1.95; }
.prob, .prob:has(.exp br) { break-inside: avoid; page-break-inside: avoid; }
.exp, .pointbox { orphans: 3; widows: 3; }
/* ★目次の直後の【使い方】枠が2行だけ次ページに落ち、1枚の89%が白紙になっていた。
   行を詰めて1ページに収め、万一あふれても枠が割れないように break-inside を効かせる。 */
.toc-name { flex:1; }
.toc-part { margin:9px 0 2px; }
.toc-row { padding:3px 2px; }
.howto { margin-top:10px; line-height:1.7; break-inside: avoid; page-break-inside: avoid; }
"""


def build_html_str(parts, total_q):
    today = datetime.date.today().strftime("%Y年%m月")
    n_units = sum(len(p["units"]) for p in parts)
    who = (f'<div class="who"><span>{B.esc(STUDENT)} さん 専用</span></div>' if STUDENT else "")
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link rel="stylesheet" href="{B.KATEX}/katex.min.css">
<script src="{B.KATEX}/katex.min.js"></script>
<script src="{B.KATEX}/auto-render.min.js"></script>
<style>{K.CSS}{EXTRA_CSS}</style></head><body>
<div class="cover"><div class="cband"></div><div class="rule"></div>
  <div class="title"><h1>{B.esc(TITLE)}</h1><div class="sub">{B.esc(SUBTITLE)}</div>
  <div class="tag">{B.esc(TAGLINE)}</div>
  <div class="meta">全{n_units}単元　計{total_q}問　·　問題編／解答・解説編</div></div>
  {who}
  <div class="foot">{today}　トリリオン AI塾</div>
</div>
<div class="toc"><h2>目次</h2>{toc_html(parts)}
  <div class="howto">{detail(HOWTO)}</div>
</div>
<div class="divider"><h2>問題編</h2><div class="d-sub">全{n_units}単元　計{total_q}問</div></div>
{section_html(parts, 'prob')}
<div class="divider"><h2>解答・解説編</h2></div>
{section_html(parts, 'ans')}
<script>
window.onload = function(){{
  renderMathInElement(document.body, {{
    delimiters:[{{left:"$",right:"$",display:false}}], throwOnError:true, strict:false
  }});
  document.title = "done";
}};
</script></body></html>"""


def main():
    parts = C.PARTS
    for p in parts:
        K.reorder(p["units"])
    total_q = sum(len(u["problems"]) for p in parts for u in p["units"])
    missing = [f'{ui}-{q["no"]}' for ui, u in
               enumerate((u for p in parts for u in p["units"]), 1)
               for q in u["problems"] if not q.get("explanation", "").strip()]
    if missing:
        sys.exit(f"解説が空の問題: {missing}")
    html_path = os.path.join(HERE, "_build_chem.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_html_str(parts, total_q))
    subprocess.run([B.CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=30000", f"--print-to-pdf={OUT}",
                    "file://" + html_path], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    B.stamp_pdf(OUT, BOOK)
    d = fitz.open(OUT)
    print(f"WROTE {OUT} | pages: {d.page_count} | units: {sum(len(p['units']) for p in parts)} | questions: {total_q}")
    d.close()


if __name__ == "__main__":
    main()
