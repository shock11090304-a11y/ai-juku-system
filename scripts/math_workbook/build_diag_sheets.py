#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""基礎徹底問題集の付属2シートを PDF 化する。

  python3 build_diag_sheets.py

1) 自己採点シート(生徒用) … ○×を書くだけのグリッド。スキルタグ等の診断情報は一切載せない。
2) 診断キー(塾長用・部外秘) … 全126問×測定スキル×つまずきの根っこ対応表 + 運用手順。

数式(stem)の描画は KaTeX(build_html の資産)を再利用。
"""
import os, subprocess, datetime
import fitz
import build_html as B
import diagnosis_kiso as D
import content_kiso as C


def full_stems():
    """印刷版と同じ採番で 全文stem を取り出す(診断キーの表示用)。"""
    units = [u for p in C.PARTS for u in p["units"]]
    for u in units:
        order, buckets = [], {}
        for q in u["problems"]:
            g = q.get("group", "")
            if g not in buckets:
                buckets[g] = []
                order.append(g)
            buckets[g].append(q)
        u["problems"] = [q for g in order for q in buckets[g]]
    return {f"{ui}-{j}": q["stem"]
            for ui, u in enumerate(units, 1) for j, q in enumerate(u["problems"], 1)}

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_SHEET = os.path.join(HERE, "数列確率ベクトル_自己採点シート.pdf")
OUT_KEY = os.path.join(HERE, "数列確率ベクトル_診断キー_塾長用.pdf")

LEVEL_JA = {"basic": "基礎", "standard": "標準", "advanced": "発展"}

BASE_CSS = """
@page { size: A4; margin: 16mm 15mm 14mm 15mm; }
* { box-sizing: border-box; }
body { font-family: "Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; color:#1a1a1a; font-size:10pt; line-height:1.55; margin:0; }
h1 { color:#1f3a5f; font-size:17pt; margin:0 0 2px; }
.katex { font-size: 1.0em; }
table { border-collapse: collapse; width:100%; }
"""


# ---------------------------------------------------------------- 生徒用
def sheet_html():
    """○×記入グリッドのみ。診断に関する語(弱点/分析/スキル)は使わない。"""
    rows = []
    for u in D.UNITS_INFO:
        cells = "".join(
            f'<td class="c"><div class="n">{i}</div><div class="m"></div></td>'
            for i in range(1, u["count"] + 1))
        pad = "".join('<td class="c pad"></td>' for _ in range(12 - u["count"]))
        rows.append(f'<tr><th class="u">{u["idx"]:02d}　{B.esc(u["name"])}</th>{cells}{pad}</tr>')
    css = BASE_CSS + """
    .lead { color:#444; font-size:10pt; margin:6px 0 10px; }
    .meta { display:flex; gap:24px; margin:10px 0 14px; font-size:11pt; }
    .meta span { border-bottom:1px solid #1a1a1a; min-width:150px; display:inline-block; padding:0 6px 2px; }
    th.u { background:#1f3a5f; color:#fff; font-size:9pt; font-weight:normal; text-align:left;
           padding:4px 7px; white-space:nowrap; width:1%; }
    td.c { border:0.6px solid #9fb0c3; width:30px; vertical-align:top; padding:0; }
    td.c .n { font-size:7.5pt; color:#8a8a8a; text-align:center; border-bottom:0.4px solid #d5dde6; }
    td.c .m { height:30px; }
    td.pad { background:#eef1f5; border:0.6px solid #d5dde6; }
    .how { margin-top:14px; background:#f4f6f9; border-left:3px solid #c8a24e; padding:10px 12px; font-size:9.5pt; color:#333; }
    .how b { color:#1f3a5f; }
    """
    today = datetime.date.today().strftime("%Y年%m月")
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>{css}</style></head><body>
<h1>自己採点シート</h1>
<div class="lead">数列・確率・ベクトル 基礎徹底問題集（全126問）　答え合わせの結果をこの1枚に記録します。</div>
<div class="meta"><div>名前：<span></span></div><div>実施日：<span></span>〜<span></span></div></div>
<table>{''.join(rows)}</table>
<div class="how"><b>使い方</b><br>
① 各単元を解いたら、解答・解説編で答え合わせをして、正解は ○、まちがいは × をマスに書く。<br>
② 解いていない問題は空欄のままでよい。<br>
③ シートの写真を先生に送る。<b>×だった番号（例：07-3）</b>が読めるように撮ってください。<br>
④ ×だった問題は、解説を読んで数日あけてもう一度解く。2回連続で○になったらクリア。</div>
<div style="margin-top:8px;color:#8a8a8a;font-size:8.5pt;">{today}　トリリオン AI塾</div>
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
    code { background:#eef2f7; padding:1px 5px; font-size:8.5pt; font-family:Menlo,monospace; }
    th { background:#1f3a5f; color:#fff; font-weight:normal; padding:3px 6px; font-size:8.5pt; text-align:left; }
    td { border-bottom:0.5px solid #c9d4e0; padding:3px 6px; vertical-align:top; }
    tr { page-break-inside: avoid; }
    thead { display: table-header-group; }  /* ページ跨ぎでヘッダ行を再掲 */
    .unit-h { color:#1f3a5f; font-size:11pt; font-weight:bold; margin:14px 0 4px; page-break-after:avoid; }
    .lv-b { color:#3a7d44; } .lv-s { color:#b06a1f; } .lv-a { color:#a03030; }
    .code { color:#8a8a8a; font-size:8pt; }
    .sub { color:#8a8a8a; }
    section { page-break-inside:auto; }
    .skills td:first-child { white-space:nowrap; }
    """
    # スキル体系表
    from collections import Counter
    cnt_p = Counter(v["skill"] for v in D.MAP.values())
    cnt_s = Counter(c for v in D.MAP.values() for c in v["sub"])
    skill_rows = "".join(
        f'<tr><td><b>{B.esc(D.SKILLS[c])}</b> <span class="code">{c}</span></td>'
        f'<td>{B.esc("、".join(D.SKILLS[p] for p in D.PREREQ.get(c, [])) or "—(根)")}</td>'
        f'<td>{cnt_p[c]}問' + (f' <span class="sub">+副{cnt_s[c]}</span>' if cnt_s[c] else "") + "</td></tr>"
        for c in D.SKILLS)
    # 単元×問題 対応表(問題文は全文をKaTeX描画)
    stems = full_stems()
    unit_tables = []
    for u in D.UNITS_INFO:
        rows = []
        for i in range(1, u["count"] + 1):
            key = f"{u['idx']}-{i}"
            m = D.MAP[key]
            lv = m["level"]
            subs = f'<span class="sub">＋{B.esc("、".join(D.SKILLS[c] for c in m["sub"]))}</span>' if m["sub"] else ""
            root = D.PREREQ.get(m["skill"], [])
            root_txt = B.esc("、".join(D.SKILLS[p] for p in root)) if root else "—"
            rows.append(
                f'<tr><td><b>{u["idx"]:02d}-{i}</b></td>'
                f'<td class="lv-{lv[0]}">{LEVEL_JA.get(lv, lv)}</td>'
                f'<td><b>{B.esc(D.SKILLS[m["skill"]])}</b> <span class="code">{m["skill"]}</span> {subs}</td>'
                f'<td>{root_txt}</td>'
                f'<td class="stem">{B.esc(stems[key])}</td></tr>')
        unit_tables.append(
            f'<div class="unit-h">{u["idx"]:02d}　{B.esc(u["name"])}（{u["count"]}問）</div>'
            f'<table><thead><tr><th style="width:9%">番号</th><th style="width:7%">レベル</th>'
            f'<th style="width:34%">測っている力</th><th style="width:24%">前提(つまずきの根の候補)</th>'
            f'<th>問題</th></tr></thead><tbody>{"".join(rows)}</tbody></table>')
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link rel="stylesheet" href="{B.KATEX}/katex.min.css">
<script src="{B.KATEX}/katex.min.js"></script>
<script src="{B.KATEX}/auto-render.min.js"></script>
<style>{css}</style></head><body>
<h1>診断キー（塾長用）</h1>
<div class="warn">部外秘 — 生徒・保護者には見せない。どの問題が何を測るかを生徒が知ると、
出題意図を意識した解き方になり診断の精度が落ちます。生徒に渡すのは「問題集」と「自己採点シート」だけ。</div>

<h2>運用フロー</h2>
<div class="flow"><ol>
<li>生徒に <b>問題集PDF</b> と <b>自己採点シート</b> を渡す（この診断キーは渡さない）。</li>
<li>生徒が解き終えたら、シートの写真から <b>×の番号</b> と <b>空欄(解いていない)の番号</b> を拾う。</li>
<li>AI(Claude)に「<b>数列確率ベクトル基礎徹底の診断: ×は 07-3 08-6、単元12は未実施</b>」のように伝える。
またはターミナルで:<br>
<code>cd ~/ai-juku-system/scripts/math_workbook && python3 analyze_kiso.py --name 生徒名 --save --skip 12 07-3 08-6</code></li>
<li>弱点スキル・つまずきの根っこ・復習処方(問題番号つき)のレポートが出る(--saveでDesktopに保存)。</li>
<li>生徒への声かけは「まず○○番をもう一回」だけ。弱点タグ名は口にしない。</li>
</ol>
<div style="margin-top:6px;">番号は 07-3 / 7-3 / 全角 / カンマ混在OK。未実施は <code>--skip 12</code>(単元まるごと) か
<code>--skip "12-9 12-10"</code>(問題単位・引用符必須)。解いていない問題を×扱いにしない(正答率が歪む)。</div></div>

<h2>スキル体系（44スキル）</h2>
<table class="skills"><thead><tr><th style="width:34%">スキル</th><th style="width:44%">前提スキル</th><th>担当問題</th></tr></thead>
<tbody>{skill_rows}</tbody></table>

<h2>全126問 × 診断対応表</h2>
{''.join(unit_tables)}
<div style="margin-top:10px;color:#8a8a8a;font-size:8pt;">{today} 生成　·　データ本体: scripts/math_workbook/diagnosis_kiso.py（問題集を改版したら再生成）</div>
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
                    "--virtual-time-budget=15000", f"--print-to-pdf={out_path}",
                    "file://" + tmp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if stamp_title:
        B.stamp_pdf(out_path, stamp_title)
    d = fitz.open(out_path)
    print(f"WROTE {out_path} | pages: {d.page_count}")
    d.close()


def main():
    render(sheet_html(), OUT_SHEET)                      # 生徒用は柱・ノンブル不要(1枚)
    render(key_html(), OUT_KEY, stamp_title="診断キー(塾長用・部外秘)")


if __name__ == "__main__":
    main()
