#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""化学［理論］総復習トレーニングの付属2シートを PDF 化する。

  python3 build_sheet_chem.py

1) 自己採点シート(生徒用) … ○×△を書くだけ。スキル名・診断情報は一切載せない。
2) 診断キー(塾長用・部外秘) … 全108問×測定スキル×土台スキルの対応表 + 運用手順。
"""
import os, sys, subprocess, datetime
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
MATH = os.path.abspath(os.path.join(HERE, "..", "math_workbook"))
sys.path.insert(0, MATH)
import build_html as B          # noqa: E402
import diagnosis_chem as D      # noqa: E402

OUT_SHEET = os.path.join(HERE, "kagaku_jiko_saiten_sheet.pdf")
OUT_KEY = os.path.join(HERE, "kagaku_shindan_key.pdf")
LEVEL_JA = {"basic": "基礎", "standard": "標準", "advanced": "発展"}

BASE_CSS = """
@page { size: A4; margin: 15mm 14mm 13mm 14mm; }
* { box-sizing: border-box; }
body { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; color:#1a1a1a;
       font-size:10pt; line-height:1.55; margin:0; }
h1 { color:#1f3a5f; font-size:17pt; margin:0 0 2px; }
table { border-collapse:collapse; width:100%; }
"""


# ------------------------------------------------------------------ 生徒用
def sheet_html():
    rows, cur_area = [], None
    for u in D.units_info():
        if u["area"] != cur_area:
            cur_area = u["area"]
            rows.append(f'<tr class="area"><th colspan="7">{B.esc(cur_area)}</th></tr>')
        cells = "".join(f'<td class="c"><div class="n">{i}</div><div class="m"></div></td>'
                        for i in range(1, u["count"] + 1))
        rows.append(f'<tr><th class="u">C{u["idx"]:02d}　{B.esc(u["name"])}</th>{cells}</tr>')
    css = BASE_CSS + """
    .lead { color:#444; font-size:9.4pt; margin:4px 0 6px; }
    .meta { display:flex; gap:22px; margin:6px 0 9px; font-size:10.5pt; }
    .meta span { border-bottom:1px solid #1a1a1a; min-width:135px; display:inline-block; padding:0 6px 2px; }
    /* ★18単元+6編見出し=24行。1行でも高いと2ページ目に落ちて「1枚に記録」でなくなるので、
       記入マスは○×△が書ける最小(20px≒5.3mm)まで詰めて必ず1ページに収める。 */
    tr.area th { background:#eaeff5; color:#1f3a5f; text-align:left; font-size:8.6pt;
                 font-weight:bold; padding:1.5px 8px; border:0.6px solid #9fb0c3; }
    th.u { background:#1f3a5f; color:#fff; font-size:8.6pt; font-weight:normal; text-align:left;
           padding:2px 7px; white-space:nowrap; width:1%; }
    td.c { border:0.6px solid #9fb0c3; width:30px; vertical-align:top; padding:0; }
    td.c .n { font-size:7pt; color:#8a8a8a; text-align:center; border-bottom:0.4px solid #d5dde6;
              line-height:1.2; }
    td.c .m { height:20px; }
    .how { margin-top:8px; background:#f4f6f9; border-left:3px solid #c8a24e; padding:7px 11px;
           font-size:9pt; line-height:1.45; color:#333; }
    .how b { color:#1f3a5f; }
    """
    today = datetime.date.today().strftime("%Y年%m月")
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>{css}</style></head><body>
<h1>自己採点シート　化学［理論］総復習トレーニング</h1>
<div class="lead">全18単元・108問。答え合わせの結果をこの1枚に記録します。</div>
<div class="meta"><div>名前：<span></span></div><div>実施日：<span></span>〜<span></span></div></div>
<table>{''.join(rows)}</table>
<div class="how"><b>使い方</b><br>
① 単元を解いたら解答・解説編で答え合わせをして、正解は ○、まちがいは × をマスに書く。<br>
② <b>「解説や公式を見てから正解した」ものは △</b>。自力で解けたわけではないので、○にしないこと。
この △ が、次にやることを決めるいちばん大事な情報になります。<br>
③ 解いていない問題は空欄のままでよい。<br>
④ シートの写真を先生に送る。<b>×と△の番号（例：C13-4）</b>が読めるように撮ってください。<br>
⑤ ×だった問題は、解説を読んで<b>日をあけてから</b>もう一度解く。2回連続で○になったらクリア。</div>
<div style="margin-top:4px;color:#8a8a8a;font-size:8.5pt;">{today}　トリリオン AI塾</div>
</body></html>"""


# ------------------------------------------------------------------ 塾長用
def key_html():
    idx = D.index()
    rows, cur_unit = [], None
    for pid, q in idx.items():
        if q["unit"] != cur_unit:
            cur_unit = q["unit"]
            rows.append(f'<tr class="uhead"><th colspan="4">C{q["unit"]:02d}　'
                        f'{B.esc(q["unit_name"])}　<span>{B.esc(q["area"])}</span></th></tr>')
        pre = D.PREREQ.get(q["skill"], [])
        pre_s = " ← " + " / ".join(pre) if pre else ""
        rows.append(
            f'<tr><td class="pid">{pid}</td><td class="lv">{LEVEL_JA.get(q["level"], "")}</td>'
            f'<td class="sk">{B.esc(q["skill"])}<span class="pre">{B.esc(pre_s)}</span></td>'
            f'<td class="an">{B.esc(q["answer"])}</td></tr>')
    css = BASE_CSS + """
    @page { size: A4; margin: 13mm 12mm 11mm 12mm; }
    body { font-size:8.6pt; }
    .warn { background:#fdf3f3; border:1.2px solid #a03030; color:#a03030; padding:7px 11px;
            margin:6px 0 10px; font-size:9.4pt; font-weight:bold; }
    .how { background:#f4f6f9; border-left:3px solid #c8a24e; padding:9px 12px; margin-bottom:10px;
           font-size:9pt; color:#333; }
    .how b { color:#1f3a5f; } .how code { background:#e8edf3; padding:1px 4px; font-size:8.6pt; }
    tr.uhead th { background:#1f3a5f; color:#fff; text-align:left; padding:3px 8px; font-size:9pt;
                  font-weight:normal; }
    tr.uhead th span { opacity:.75; font-size:8pt; margin-left:8px; }
    /* 解答欄に $K_c=\\dfrac{...}$ のような組分数が入るので、行送りを詰めると
       上下の行の指数と分母がぶつかる(overlap_gate.py で検出)。1.9 で 0 件。 */
    td { border-bottom:0.5px solid #d5dde6; padding:3px 6px; vertical-align:top; line-height:1.9; }
    td .katex { line-height:1.2; }
    td.pid { color:#1f3a5f; font-weight:bold; white-space:nowrap; width:16mm; }
    td.lv { color:#666; white-space:nowrap; width:12mm; }
    td.sk { width:78mm; }
    td.sk .pre { color:#a03030; font-size:7.8pt; }
    td.an { color:#c8492e; }
    """
    today = datetime.date.today().strftime("%Y-%m-%d")
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>{css}</style></head><body>
<h1>診断キー　化学［理論］総復習トレーニング</h1>
<div class="warn">塾長用・部外秘。このシートと analyze_chem.py は生徒に渡さない。
生徒に伝えるのは「まず C13-3 と C13-4 をもう一度やってみようか」のように<b>問題番号だけ</b>にする。</div>
<div class="how"><b>使い方</b><br>
① 生徒から自己採点シートの写真をもらう（×と△の番号）。<br>
② <code>python3 analyze_chem.py --name "生徒名" --save --hint "C09-4 C13-5" C05-3 C11-4 ...</code><br>
　 <code>--hint</code> には△（解説を見て正解＝自力ではない）の番号を渡す。重み0.5の誤答として集計される。<br>
③ 出力の「つまずきの根っこ」から順に復習させる。<b>枝葉（発展問題）から潰しても直らない。</b><br>
　 表の赤字「← ○○」がその問題の土台スキル。×が土台側にも出ていたら、必ず土台から戻す。<br>
④ 2回連続で○になったらクリア。1回目と2回目は必ず日をあける。</div>
<table>{''.join(rows)}</table>
<div style="margin-top:8px;color:#8a8a8a;font-size:8pt;">{today}　トリリオン AI塾　診断キー（部外秘）</div>
</body></html>"""


KATEX_HEAD = f"""<link rel="stylesheet" href="{B.KATEX}/katex.min.css">
<script src="{B.KATEX}/katex.min.js"></script>
<script src="{B.KATEX}/auto-render.min.js"></script>"""

KATEX_BOOT = """<script>
window.onload = function(){
  renderMathInElement(document.body, {
    delimiters:[{left:"$",right:"$",display:false}], throwOnError:true, strict:false
  });
  document.title = "done";
};
</script>"""


def render(html_str, out, name):
    """★KaTeX の読み込みとレンダリング呼び出しをここで必ず注入する。

    診断キーは answer 欄に $K_c = \\dfrac{...}$ のような数式をそのまま載せるので、
    これが無いと**全128式が生の LaTeX ソースのまま印刷される**(実際にそうなっていた)。
    PDF は正常に出力され、塾長が紙を見るまで気づけない。
    """
    html_str = html_str.replace("</head>", KATEX_HEAD + "</head>")
    html_str = html_str.replace("</body>", KATEX_BOOT + "</body>")
    p = os.path.join(HERE, f"_build_{name}.html")
    with open(p, "w", encoding="utf-8") as f:
        f.write(html_str)
    subprocess.run([B.CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=15000", f"--print-to-pdf={out}", "file://" + p],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = fitz.open(out)
    print(f"WROTE {out} | pages: {d.page_count}")
    d.close()


if __name__ == "__main__":
    render(sheet_html(), OUT_SHEET, "sheet_chem")
    render(key_html(), OUT_KEY, "key_chem")
