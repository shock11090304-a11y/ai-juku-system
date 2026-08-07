#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数学I·A 弱点発見トレーニング の付属2シートを PDF 化する。

  python3 build_sheets_ia_jaku.py

1) 自己採点シート(生徒用) … ○×△を書くだけのグリッド。診断情報(スキル・弱点)は一切載せない。
2) 診断キー(塾長用・部外秘) … 全問×測定スキル×つまずきの根っこ対応表 + 運用手順。

★診断キーも KaTeX を読み込むこと。読み込み忘れると数式が全部「生の LaTeX ソース」で
  印刷される(問題集側のゲートは通るので、実物を見るまで気づけない)。
"""
import os, subprocess, datetime, sys
import fitz
import build_html as B
import build_kiso as K
import diagnosis_ia_jaku as D
import content_ia_jaku as C
from _ia_jaku_lib import PLAN

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_SHEET = os.path.join(HERE, "数学IA_弱点発見トレーニング_自己採点シート.pdf")
OUT_KEY = os.path.join(HERE, "数学IA_弱点発見トレーニング_診断キー_塾長用.pdf")

LEVEL_JA = {"basic": "基礎", "standard": "標準", "advanced": "発展"}
AREA_OF = {c: a for c, _n, _cnt, a in PLAN}
MAXQ = max(u["count"] for u in D.UNITS_INFO)

BASE_CSS = """
@page { size: A4; margin: 15mm 14mm 13mm 14mm; }
* { box-sizing: border-box; }
body { font-family: "Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; color:#1a1a1a; font-size:10pt; line-height:1.55; margin:0; }
h1 { color:#1f3a5f; font-size:17pt; margin:0 0 2px; }
.katex { font-size: 1.0em; }
table { border-collapse: collapse; width:100%; }
"""


def stem_html(s):
    """診断キーの表に載せる問題文。★esc しただけだと stem に書いた <br> や <b> が
    「&lt;br&gt;」＝紙に "<br>" とリテラル印字される(20ページ中14ページ・56箇所で実測)。
    生の LaTeX が残るのと同じ型の事故で、PDF は正常に生成されるので実物を見るまで気づけない。
    表のセルなので改行は空白に潰し、強調は落とす。"""
    t = B.esc(s)
    return (t.replace("&lt;br&gt;", "　").replace("&lt;b&gt;", "").replace("&lt;/b&gt;", ""))


def full_stems():
    """印刷版と同じ採番で全文 stem を取り出す(診断キーの表示用)。"""
    for p in C.PARTS:
        K.reorder(p["units"])
    return {f"{code}-{j}": q["stem"]
            for code, u in zip(C.CODES, C.UNITS)
            for j, q in enumerate(u["problems"], 1)}


# ---------------------------------------------------------------- 生徒用
def sheet_html():
    """○×△記入グリッドのみ。診断に関する語(弱点/分析/スキル)は使わない。"""
    rows, cur_area = [], None
    for u in D.UNITS_INFO:
        area = AREA_OF[u["code"]]
        if area != cur_area:
            cur_area = area
            rows.append(f'<tr><td class="area" colspan="{MAXQ + 1}">{B.esc(area)}</td></tr>')
        cells = "".join(
            f'<td class="c"><div class="n">{i}</div><div class="m"></div></td>'
            for i in range(1, u["count"] + 1))
        pad = "".join('<td class="c pad"></td>' for _ in range(MAXQ - u["count"]))
        rows.append(f'<tr><th class="u">{u["code"]}　{B.esc(u["name"])}</th>{cells}{pad}</tr>')
    css = BASE_CSS + """
    /* ★1枚に収める。2枚目に日付だけが残ると、生徒は「表面だけ書けばいい」と思って
       裏面の単元(A17/A18)を空欄のまま返してくる。 */
    @page { margin: 12mm 12mm 8mm 12mm; }
    .lead { color:#444; font-size:9.5pt; margin:4px 0 6px; }
    .meta { display:flex; gap:24px; margin:6px 0 8px; font-size:10.5pt; }
    .meta span { border-bottom:1px solid #1a1a1a; min-width:140px; display:inline-block; padding:0 6px 2px; }
    td.area { background:#eef2f7; color:#1f3a5f; font-size:8pt; font-weight:bold;
              padding:2px 7px; border:0.6px solid #c9d4e0; }
    th.u { background:#1f3a5f; color:#fff; font-size:8pt; font-weight:normal; text-align:left;
           padding:3px 7px; white-space:nowrap; width:1%; }
    td.c { border:0.6px solid #9fb0c3; width:28px; vertical-align:top; padding:0; }
    td.c .n { font-size:7pt; color:#8a8a8a; text-align:center; border-bottom:0.4px solid #d5dde6; }
    td.c .m { height:17px; }
    td.pad { background:#eef1f5; border:0.6px solid #d5dde6; }
    .how { margin:0 0 8px; line-height:1.5; background:#f4f6f9; border-left:3px solid #c8a24e; padding:7px 11px; font-size:9pt; color:#333; }
    .how b { color:#1f3a5f; }
    """
    today = datetime.date.today().strftime("%Y年%m月")
    total = sum(u["count"] for u in D.UNITS_INFO)
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>{css}</style></head><body>
<h1>自己採点シート</h1>
<div class="lead">数学 I·A 弱点発見トレーニング（全{total}問）　答え合わせの結果をこの1枚に記録します。</div>
<div class="meta"><div>名前：<span></span></div><div>実施日：<span></span>〜<span></span></div></div>
<div class="how"><b>書き方</b><br>
① 各単元を解いたら、解答・解説編で答え合わせをして、マスに記号を書く。<br>
　　<b>○</b>＝何も見ずに正解　／　<b>△</b>＝公式や解説を見てから正解　／　<b>×</b>＝まちがい<br>
② <b>解いていない問題は空欄のまま</b>にする（×にしない）。どこを飛ばしたかも大事な情報です。<br>
③ シートの写真を先生に送る。<b>×と△の番号（例：A07-3）</b>が読めるように撮ってください。<br>
④ ×だった問題は、解説を読んで数日あけてもう一度解く。2回連続で○になったらクリア。</div>
<table>{''.join(rows)}</table>
<div style="margin-top:4px;color:#8a8a8a;font-size:8pt;">{today}　トリリオン AI塾</div>
</body></html>"""


# ---------------------------------------------------------------- 塾長用
def key_html():
    today = datetime.date.today().strftime("%Y-%m-%d")
    css = BASE_CSS + """
    body { font-size:9pt; }
    .warn { background:#fdeeee; border:1.5px solid #c8492e; color:#a03030; font-weight:bold;
            padding:8px 12px; margin:8px 0 12px; font-size:10.5pt; }
    h2 { color:#1f3a5f; font-size:12.5pt; border-left:4px solid #1f3a5f; padding-left:8px; margin:18px 0 6px; }
    .flow { background:#f4f6f9; padding:10px 12px; font-size:9.5pt; }
    .flow ol { margin:4px 0 2px 18px; padding:0; }
    /* ★語中で折り返すと PDF から選択コピーしたとき途中に改行が入り、そのまま貼ると
       「エラー: 番号の形式が不正です:「-」」で止まる。単語は割らせない。 */
    code { background:#eef2f7; padding:1px 5px; font-size:8.5pt; font-family:Menlo,monospace; }
    /* ★塾長が実際に打つ唯一のコマンド。語の途中で折り返すと、PDFから選択コピーした
       ときに改行が混ざり「--save -」「-skip A18」と割れてそのままでは動かない。
       pre + 十分小さい字で1行に収め、折り返しを起こさせない。 */
    pre.cmd { background:#eef2f7; border-left:3px solid #1f3a5f; padding:6px 8px; margin:6px 0 0;
              font-family:Menlo,monospace; font-size:7.2pt; line-height:1.6;
              white-space:pre; overflow:hidden; }
    th { background:#1f3a5f; color:#fff; font-weight:normal; padding:3px 6px; font-size:8.5pt; text-align:left; }
    /* ★行送りを 1.9 まで上げる。狭い列に KaTeX の数式が折り返して入るので、既定のままだと
       上の行の $\\leqq$ に下の行の文字が物理的に乗る(p8 で5件実測)。数式内部は詰めたまま。 */
    td { border-bottom:0.5px solid #c9d4e0; padding:4px 6px; vertical-align:top; line-height:2.2; }
    tr { page-break-inside: avoid; }
    thead { display: table-header-group; }
    .unit-h { color:#1f3a5f; font-size:11pt; font-weight:bold; margin:14px 0 4px; page-break-after:avoid; }
    .area-h { color:#8a6a1f; font-size:10pt; font-weight:bold; margin:16px 0 2px; page-break-after:avoid;
              border-bottom:1px solid #c8a24e; }
    .lv-b { color:#3a7d44; } .lv-s { color:#b06a1f; } .lv-a { color:#a03030; }
    .code { color:#8a8a8a; font-size:8pt; }
    .sub { color:#8a8a8a; }
    section { page-break-inside:auto; }
    .skills td:first-child { white-space:nowrap; }
    """
    from collections import Counter
    cnt_p = Counter(v["skill"] for v in D.MAP.values())
    cnt_s = Counter(c for v in D.MAP.values() for c in v["sub"])
    skill_rows = "".join(
        f'<tr><td><b>{B.esc(D.SKILLS[c])}</b> <span class="code">{c}</span></td>'
        f'<td>{B.esc("、".join(D.SKILLS[p] for p in D.PREREQ.get(c, [])) or "—(根)")}</td>'
        f'<td>{cnt_p[c]}問' + (f' <span class="sub">+副{cnt_s[c]}</span>' if cnt_s[c] else "") + "</td></tr>"
        for c in D.SKILLS)

    stems = full_stems()
    unit_tables, cur_area = [], None
    for u in D.UNITS_INFO:
        area = AREA_OF[u["code"]]
        if area != cur_area:
            cur_area = area
            unit_tables.append(f'<div class="area-h">{B.esc(area)}</div>')
        rows = []
        for i in range(1, u["count"] + 1):
            key = f"{u['code']}-{i}"
            m = D.MAP[key]
            lv = m["level"]
            subs = (f'<span class="sub">＋{B.esc("、".join(D.SKILLS[c] for c in m["sub"]))}</span>'
                    if m["sub"] else "")
            root = D.PREREQ.get(m["skill"], [])
            root_txt = B.esc("、".join(D.SKILLS[p] for p in root)) if root else "—"
            rows.append(
                f'<tr><td><b>{key}</b></td>'
                f'<td class="lv-{lv[0]}">{LEVEL_JA.get(lv, lv)}</td>'
                f'<td><b>{B.esc(D.SKILLS[m["skill"]])}</b> <span class="code">{m["skill"]}</span> {subs}</td>'
                f'<td>{root_txt}</td>'
                f'<td class="stem">{stem_html(stems[key])}</td></tr>')
        unit_tables.append(
            f'<div class="unit-h">{u["code"]}　{B.esc(u["name"])}（{u["count"]}問）</div>'
            f'<table><thead><tr><th style="width:9%">番号</th><th style="width:7%">レベル</th>'
            f'<th style="width:32%">測っている力</th><th style="width:22%">前提(つまずきの根の候補)</th>'
            f'<th>問題</th></tr></thead><tbody>{"".join(rows)}</tbody></table>')

    total = sum(u["count"] for u in D.UNITS_INFO)
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link rel="stylesheet" href="{B.KATEX}/katex.min.css">
<script src="{B.KATEX}/katex.min.js"></script>
<script src="{B.KATEX}/auto-render.min.js"></script>
<style>{css}</style></head><body>
<h1>診断キー（塾長用）— 数学 I·A 弱点発見トレーニング</h1>
<div class="warn">部外秘 — 生徒・保護者には見せない。どの問題が何を測るかを生徒が知ると、
出題意図を意識した解き方になり診断の精度が落ちます。生徒に渡すのは「問題集」と「自己採点シート」だけ。</div>

<h2>運用フロー</h2>
<div class="flow"><ol>
<li>生徒に <b>問題集PDF</b> と <b>自己採点シート</b> を渡す（この診断キーは渡さない）。</li>
<li>生徒が解き終えたら、シートの写真から <b>×の番号</b>・<b>△の番号</b>・<b>空欄(未実施)の番号</b>を拾う。</li>
<li>AI(Claude)に「<b>数学IA弱点発見の診断: ×は A06-3 A07-1、△は A11-2、A18は未実施</b>」のように伝える。
またはターミナルで（下の2行をそのままコピーして貼る）:
<pre class="cmd">cd ~/ai-juku-system/scripts/math_workbook
python3 analyze_ia_jaku.py --name 生徒名 --save --skip A18 --hint "A11-2" A06-3 A07-1</pre></li>
<li>弱点スキル・つまずきの根っこ・復習処方(問題番号つき)のレポートが出る(--save で Desktop に保存)。</li>
<li>生徒への声かけは「まず○○番をもう一回」だけ。<b>弱点タグ名は口にしない</b>。</li>
</ol>
<div style="margin-top:6px;">番号は <b>A07-3 の形（接頭辞 A 必須）</b>。全角・カンマ混在OK。
A を付けない「07-3」はエラーにしている —— 第2集(単元13〜27)や化学(C01〜C18)を同時に解いている生徒で、
番号を貼り間違えても検出できなくなるため。未実施は <code>--skip A18</code>(単元まるごと) か
<code>--skip "A18-7 A18-8"</code>(問題単位・引用符必須)。解いていない問題を×扱いにしない(正答率が歪む)。<br>
<b>△(公式や解説を見てから正解)</b> は <code>--hint</code> に渡す。×だけ見ると「見れば解ける層」を取りこぼす。</div></div>

<h2>スキル体系（{len(D.SKILLS)}スキル）</h2>
<table class="skills"><thead><tr><th style="width:32%">スキル</th><th style="width:44%">前提スキル</th><th>担当問題</th></tr></thead>
<tbody>{skill_rows}</tbody></table>

<h2>全{total}問 × 診断対応表</h2>
{''.join(unit_tables)}
<div style="margin-top:10px;color:#8a8a8a;font-size:8pt;">{today} 生成　·　データ本体: scripts/math_workbook/diagnosis_ia_jaku.py（問題集を改版したら gen_diagnosis_ia_jaku.py で再生成）</div>
<script>
window.onload = function(){{
  renderMathInElement(document.body, {{
    delimiters:[{{left:"$",right:"$",display:false}}], throwOnError:false, strict:false
  }});
  document.title = "done";
}};
</script>
</body></html>"""


def render(html_str, out_path, stamp_title=None):
    tmp = os.path.join(HERE, "_build_" + os.path.basename(out_path).replace(".pdf", ".html"))
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html_str)
    subprocess.run([B.CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=20000", f"--print-to-pdf={out_path}",
                    "file://" + tmp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if stamp_title:
        B.stamp_pdf(out_path, stamp_title)
    d = fitz.open(out_path)
    print(f"WROTE {out_path} | pages: {d.page_count}")
    d.close()


def main():
    render(sheet_html(), OUT_SHEET)                      # 生徒用は柱・ノンブル不要
    render(key_html(), OUT_KEY, stamp_title="数学I·A 診断キー(塾長用・部外秘)")


if __name__ == "__main__":
    main()
