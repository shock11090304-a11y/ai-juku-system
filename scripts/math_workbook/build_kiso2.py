#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""基礎徹底問題集【第2集｜弱点集中トレーニング】を KaTeX 教科書組版で PDF 化する。

  python3 build_kiso2.py

content_kiso2.PARTS(4編)を編の扉+攻略ボックスつきで問題編/解答編に組む。
解説は content 側の explanation に直接書かれた詳細版(第1集の EXPL オーバーレイ相当)。
描画部品(prob_html / stamp_pdf / esc / KATEX / CHROME)は build_html から再利用。
"""
import os, sys, subprocess, datetime
import fitz
import build_html as B
import build_kiso as K          # CSS と reorder を再利用
import content_kiso2 as C

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "数列確率ベクトル_第2集_弱点集中トレーニング.pdf")

# 表紙に出す宛名。★コードに書かない（PUBLIC リポジトリなので公開される）。
#   刷るときだけ:  STUDENT_NAME="姓 名" python3 build_kiso2.py    空なら汎用版。
STUDENT = os.environ.get("STUDENT_NAME", "")
TITLE = "弱点集中トレーニング"
SUBTITLE = "数列・確率・ベクトル 基礎徹底問題集［第2集］"
TAGLINE = "第1集の自己採点から、いま必要な4分野だけを抜き出した追加演習"
BOOK = "弱点集中トレーニング［第2集］"
HOWTO = ("【この問題集の使い方】第1集の答え合わせの結果から、いま伸びしろが大きい分野だけを集めました。"
         "第1集と同じ問題は1問も入っていません（同じ型を、数を変えて何度も解けるように並べてあります）。"
         "各編のとびらにある「攻略の手順」を先に読んでから解き始めてください。"
         "解説は途中の式を省いていません。分からなかった問題は、解説をノートに写してから、"
         "何も見ずにもう一度解くのが最強の勉強法です。")


# ★第1集(単元01〜12)との番号衝突を原理的に断つため、第2集は単元13から始める。
# これで「05-7」がどちらの集か一意に決まり、採点シート回収時の誤診断が起こらない。
UNIT_OFFSET = 12


def toc_html(parts):
    rows, ui = [], 1 + UNIT_OFFSET
    for p in parts:
        rows.append(f'<div class="toc-part">{B.esc(p["area"])}</div>')
        for u in p["units"]:
            rows.append(
                f'<div class="toc-row"><span class="toc-no">{ui:02d}</span>'
                f'<span class="toc-name">{B.esc(u["name"])}</span>'
                f'<span class="toc-tag">{B.esc(u.get("tag",""))}</span>'
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
    """問題行。stem に書いた <br>(帰納法の穴埋め等)を改行として通す。
    build_html.prob_html は全エスケープするので、第2集では自前で組む。"""
    lvl = B.LEVEL.get(q.get("level"))
    tag = f'<span class="lv" style="color:{lvl[1]}">[{lvl[0]}]</span> ' if lvl else ""
    return (f'<div class="prob"><span class="no">{q["no"]}.</span> {tag}'
            f'<span class="stem">{unesc(B.esc(q["stem"]))}</span></div>')


def ans_html(q):
    return (f'<div class="prob"><div class="ansline"><span class="no">{q["no"]}.</span> '
            f'<span class="ans">{B.esc(q.get("answer",""))}</span></div>'
            f'<div class="exp">{detail(q.get("explanation",""))}</div></div>')


def section_html(parts, kind):
    out, ui = [], 1 + UNIT_OFFSET
    kicker = "問題" if kind == "prob" else "解答"
    for p in parts:
        pts = C.PART_POINTS.get(p["area"], "")
        box = (f'<div class="pointbox pdivbox"><div class="pb-t">◆ 攻略の手順（先に読む）</div>{detail(pts)}</div>'
               if pts else "")
        out.append(f'<div class="pdiv"><h2>{B.esc(p["area"])}</h2>'
                   f'<div class="d-sub">{B.esc(p.get("sub",""))}</div>{box}</div>')
        for u in p["units"]:
            out.append('<section class="unit">')
            out.append(f'<div class="band"><div class="band-k">{kicker}　{ui:02d}</div>'
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
/* 編の扉に攻略ボックスを置くのでレイアウトを調整 */
.pdiv { page-break-before:always; padding-top:34mm; text-align:center; }
.pdivbox { text-align:left; margin:16mm auto 0; max-width:150mm; }
.cover .who { position:absolute; top:150mm; width:100%; text-align:center;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; color:#1f3a5f; font-size:13pt; }
.cover .who span { border-bottom:1.4px solid #c8a24e; padding:0 26px 4px; }

/* ★組分数(\\dfrac)の高さを行送りが吸収できず、上の行の分母と下の行の分子が
   物理的に重なっていた(数字の誤読が起きるレベル)。解説・攻略ボックスとも行送りを広げる。 */
.exp { line-height: 1.95; }          /* 解説は \frac 化したのでこの行送りで衝突しない */
.pointbox { line-height: 2.5; }      /* 攻略ボックスは \dfrac のままなので広く取る */
.exp .katex, .pointbox .katex { line-height: 1.2; }   /* 数式内部は詰めたまま */
.prob .stem { line-height: 1.9; }
/* ★解説の末尾数行だけが次ページに落ちる「孤立行ページ」を防ぐ。
   1問=1ブロックとして改ページ位置を決める(最長の解説でも1ページに収まる分量)。 */
.prob, .prob:has(.exp br) { break-inside: avoid; page-break-inside: avoid; }
/* ↑ build_kiso.CSS の `.prob:has(.exp br){break-inside:auto}`(第1集用・長い解説の
   途中改ページを許す設定)は詳細度が高く、素の .prob 指定では上書きできない。
   第2集は1問あたりの解説が1ページに収まる分量なので、同じ詳細度で avoid に戻す。 */
.exp, .pointbox { orphans: 3; widows: 3; }
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
  <div class="howto">{B.esc(HOWTO)}</div>
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
    html_path = os.path.join(HERE, "_build_kiso2.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_html_str(parts, total_q))
    subprocess.run([B.CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=20000", f"--print-to-pdf={OUT}",
                    "file://" + html_path], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    B.stamp_pdf(OUT, BOOK)
    d = fitz.open(OUT)
    print(f"WROTE {OUT} | pages: {d.page_count} | units: {sum(len(p['units']) for p in parts)} | questions: {total_q}")
    d.close()


if __name__ == "__main__":
    main()
