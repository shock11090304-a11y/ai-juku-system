#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共通テスト模試 2026 の印刷用 PDF (問題編 / 解答・解説編) を生成する。

seed-data/kyotsu_mogi2026_{eng,math}_manual.json を唯一の入力にして、
アプリで出題される問題とまったく同じ内容の紙冊子を作る (内容の二重管理をしない)。

生成物 (リポジトリ直下・既存 PDF と同じ置き方):
  kyotsu-mogi2026-eng-mondai.pdf     英語 問題編   (80分・100点満点・解答用紙つき)
  kyotsu-mogi2026-eng-kaisetsu.pdf   英語 解答・解説編
  kyotsu-mogi2026-math-mondai.pdf    数学 問題編   (I・A 編 + II・B・C 編・解答用紙つき)
  kyotsu-mogi2026-math-kaisetsu.pdf  数学 解答・解説編

数式は vendor/katex を node 側で静的レンダリングしてから流し込む
(印刷時に JS の実行完了を待たなくてよいので、数式が欠けた PDF が出る事故が起きない)。

必要: node (vendor/katex 用) / playwright (Chromium は /opt/pw-browsers に既設)
実行: python3 scripts/kyotsu_mogi2026/build_pdf.py
"""
import json
import os
import re
import subprocess
import sys
import html as htmllib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
KATEX_DIR = os.path.join(ROOT, 'vendor', 'katex')
WORK = os.path.join(HERE, '_build')

CIRCLED = ['①', '②', '③', '④', '⑤', '⑥']

# 大問ごとの配点 (英語は合計 100 点になるよう調整・数学は 1 小問 4 点で 1 大問 20 点)
ENG_POINTS = {
    "第1問A メッセージ読解": [2, 2, 2],
    "第1問B 告知の読み取り": [2, 2, 2, 2],
    "第2問A 比較とレビュー": [2, 2, 2, 2, 2],
    "第2問B 記事(事実と意見)": [2, 2, 2, 2, 2],
    "第3問B 体験ブログ(時系列)": [3, 3, 3, 2, 2],
    "第4問 複数資料の統合": [3, 3, 3, 2, 2],
    "第5問 伝記とノート作成": [3, 3, 3, 2, 2],
    "第6問A 論説文の要旨": [3, 3, 3, 3, 2],
    "第6問B 説明文の整理": [3, 3, 3, 2, 2],
}
MATH_POINT_PER_SUB = 4


# =====================================================================
# LaTeX の静的レンダリング (node + vendor/katex)
# =====================================================================
TEX_RE = re.compile(r'\\\((.+?)\\\)', re.S)


def render_tex_all(strings):
    """\\( ... \\) を KaTeX の HTML に置き換えた文字列リストを返す。node を 1 回だけ呼ぶ。"""
    exprs = []
    for s in strings:
        exprs.extend(TEX_RE.findall(s or ''))
    if not exprs:
        return list(strings)

    script = r'''
const katex = require(process.argv[2]);
const input = JSON.parse(require('fs').readFileSync(process.argv[3], 'utf8'));
const out = input.map(e => {
  try { return katex.renderToString(e, {throwOnError: true, displayMode: false}); }
  catch (err) { return {__error: String(err.message || err), src: e}; }
});
process.stdout.write(JSON.stringify(out));
'''
    os.makedirs(WORK, exist_ok=True)
    src_path = os.path.join(WORK, '_tex_in.json')
    js_path = os.path.join(WORK, '_katex_render.js')
    with open(src_path, 'w', encoding='utf-8') as f:
        json.dump(exprs, f, ensure_ascii=False)
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(script)

    proc = subprocess.run(
        ['node', js_path, os.path.join(KATEX_DIR, 'katex.min.js'), src_path],
        capture_output=True, text=True, cwd=ROOT)
    if proc.returncode != 0:
        raise SystemExit(f'❌ KaTeX レンダリング失敗:\n{proc.stderr[:2000]}')
    rendered = json.loads(proc.stdout)

    bad = [r for r in rendered if isinstance(r, dict)]
    if bad:
        for b in bad[:10]:
            print(f'   ❌ 数式が壊れている: {b["src"]!r} → {b["__error"]}')
        raise SystemExit(f'❌ KaTeX が解釈できない数式が {len(bad)} 件あります')

    it = iter(rendered)
    out = []
    for s in strings:
        out.append(TEX_RE.sub(lambda _m: next(it), s or ''))
    return out


# =====================================================================
# 本文の整形
# =====================================================================
def esc(s):
    return htmllib.escape(s or '', quote=False)


def format_passage(passage):
    """本文を段落に分ける。整形済みの表・箇条書きブロックだけ等幅で崩さずに出す。"""
    blocks = re.split(r'\n\s*\n', passage.strip())
    out = []
    for b in blocks:
        lines = b.split('\n')
        table_like = (
            sum(1 for ln in lines if re.search(r'\S {2,}\S', ln)) >= 2
            or any(re.search(r'={4,}|-{4,}', ln) for ln in lines)
        )
        if table_like:
            out.append(f'<pre class="fixed">{esc_keep_tex(b)}</pre>')
        else:
            out.append(f'<p class="ps">{esc_keep_tex(b)}</p>')
    return '\n'.join(out)


CSS = r'''
@page { size: A4; margin: 16mm 14mm 16mm 14mm; }
* { box-sizing: border-box; }
body {
  font-family: "IPAPGothic", "IPAGothic", "Noto Sans CJK JP", sans-serif;
  font-size: 9.6pt; line-height: 1.62; color: #16181d; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.cover { height: 247mm; display: flex; flex-direction: column; justify-content: center; }
.cover .brand { font-size: 10pt; color: #5b6472; letter-spacing: .22em; }
.cover h1 { font-size: 25pt; margin: 6mm 0 2mm; color: #12305a; line-height: 1.3; }
.cover .sub { font-size: 13pt; color: #2f6ea5; margin-bottom: 12mm; }
.cover .rule { height: 3px; background: #12305a; width: 46mm; margin-bottom: 9mm; }
.meta { border: 1.2px solid #c3ccd8; border-radius: 3px; padding: 6mm 7mm; margin-bottom: 8mm; }
.meta table { width: 100%; border-collapse: collapse; font-size: 10pt; }
.meta th { text-align: left; width: 26mm; color: #12305a; padding: 1.6mm 0; vertical-align: top; }
.meta td { padding: 1.6mm 0; }
.notes { font-size: 9pt; color: #333; }
.notes h2 { font-size: 10.5pt; color: #12305a; margin: 0 0 3mm; }
.notes ol { margin: 0; padding-left: 5mm; }
.notes li { margin-bottom: 1.6mm; }
.score-box { margin-top: 8mm; border: 1.2px solid #c3ccd8; border-radius: 3px; padding: 4mm 6mm; }
.score-box .t { font-size: 9.5pt; color: #12305a; margin-bottom: 2.5mm; }
.score-box table { border-collapse: collapse; width: 100%; font-size: 9pt; }
.score-box td, .score-box th { border: .8px solid #c3ccd8; padding: 2.4mm 1mm; text-align: center; }
.score-box th { background: #eef2f7; color: #12305a; font-weight: normal; }

.daimon { page-break-before: always; }
.daimon-head {
  background: #12305a; color: #fff; padding: 2.6mm 4mm; border-radius: 2px;
  font-size: 12pt; display: flex; justify-content: space-between; align-items: baseline;
}
.daimon-head .pt { font-size: 9.5pt; opacity: .92; }
.lead { font-size: 9pt; color: #4a5261; margin: 2.5mm 0 3mm; }
.passage { border: 1px solid #d5dce5; background: #fafbfd; border-radius: 3px; padding: 4mm 5mm; margin-bottom: 5mm; }
.passage .ps { margin: 0 0 2.6mm; white-space: pre-wrap; }
.passage .ps:last-child { margin-bottom: 0; }
.passage pre.fixed {
  font-family: "DejaVu Sans Mono", "IPAGothic", monospace;
  font-size: 8.3pt; line-height: 1.45; margin: 0 0 2.6mm; white-space: pre-wrap;
}
.q { margin-bottom: 4.2mm; page-break-inside: avoid; }
.q .stem { font-weight: bold; margin-bottom: 1.6mm; }
.q .stem .no { color: #b03024; margin-right: 2mm; }
.q .stem .pt { color: #6b7686; font-size: 8.4pt; font-weight: normal; margin-left: 2mm; }
.q ol.ch { list-style: none; margin: 0; padding: 0 0 0 4mm; }
.q ol.ch li { margin-bottom: .9mm; text-indent: -5.5mm; padding-left: 5.5mm; }
.q ol.ch .mk { color: #12305a; margin-right: 1.4mm; }

h2.sec {
  page-break-before: always; font-size: 15pt; color: #12305a;
  border-bottom: 2.4px solid #12305a; padding-bottom: 2mm; margin: 0 0 5mm;
}
/* 見出しの直後の大問は改ページしない (見出しだけの空白ページが挟まるのを防ぐ) */
h2.sec + .daimon, h2.sec + table.key { page-break-before: avoid; }
.answer-sheet { page-break-before: always; }
.answer-sheet table { border-collapse: collapse; width: 100%; font-size: 8.6pt; margin-bottom: 5mm; }
.answer-sheet th, .answer-sheet td { border: .8px solid #b9c3d0; padding: 1.9mm 1mm; text-align: center; }
.answer-sheet th { background: #eef2f7; color: #12305a; font-weight: normal; }
.answer-sheet td.mk { letter-spacing: .10em; color: #9aa5b4; }
.answer-sheet caption { text-align: left; font-size: 10pt; color: #12305a; padding-bottom: 2mm; }

table.key { border-collapse: collapse; width: 100%; font-size: 8.8pt; margin-bottom: 4mm; }
table.key th, table.key td { border: .8px solid #b9c3d0; padding: 1.7mm 1.6mm; }
table.key th { background: #12305a; color: #fff; font-weight: normal; }
table.key td.c { text-align: center; }
table.key td.ans { text-align: center; color: #b03024; font-weight: bold; }
table.key tr:nth-child(even) td { background: #f6f8fb; }
.exp { border-left: 3px solid #2f6ea5; padding: 0 0 0 4mm; margin-bottom: 5mm; page-break-inside: avoid; }
.exp .h { font-size: 10pt; color: #12305a; font-weight: bold; margin-bottom: 1.2mm; }
.exp .h .unit { font-size: 8.4pt; color: #5b6472; font-weight: normal; margin-left: 2.5mm; }
.exp .qs { color: #2b3038; margin-bottom: 1.6mm; }
.exp .ans { color: #b03024; font-weight: bold; margin-bottom: 1.6mm; }
.exp .body { color: #23272e; }
.exp-sec {
  font-size: 9.2pt; color: #12305a; font-weight: bold;
  margin: 2.4mm 0 1mm; padding-bottom: .6mm; border-bottom: .8px solid #d5dce5;
}
.exp-sec:first-child { margin-top: 0; }
.exp-step { display: flex; gap: 2.5mm; margin-bottom: 1mm; }
.exp-step .lbl {
  flex: 0 0 11mm; color: #12305a; font-weight: bold; font-size: 8.8pt;
  border-right: 2px solid #cfd8e4; padding-right: 1.8mm;
}
.exp-step .txt { flex: 1; }
.exp-line { margin-bottom: .8mm; white-space: pre-wrap; }
.exp .body ul { margin: 0 0 1.2mm; padding-left: 5mm; }
.exp .body li { margin-bottom: .5mm; }
.exp .body code {
  font-family: "DejaVu Sans Mono", monospace; font-size: 8.4pt;
  background: #eef2f7; padding: 0 .8mm; border-radius: 2px;
}
.exp .body strong { color: #0e2f56; }
.katex { font-size: 1.02em; }
'''


def page_head(title, css_katex):
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8">
<title>{esc(title)}</title>
<style>{css_katex}</style>
<style>{CSS}</style>
</head><body>'''


def cover(title, sub, rows, notes, score_rows):
    meta = ''.join(f'<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>' for k, v in rows)
    notes_html = ''.join(f'<li>{n}</li>' for n in notes)
    head = ''.join(f'<th>{esc(h)}</th>' for h, _ in score_rows)
    body = ''.join(f'<td>{esc(v)}</td>' for _, v in score_rows)
    return f'''<section class="cover">
  <div class="brand">TRILLION AI JUKU</div>
  <h1>{esc(title)}</h1>
  <div class="rule"></div>
  <div class="sub">{esc(sub)}</div>
  <div class="meta"><table>{meta}</table></div>
  <div class="notes"><h2>注意事項</h2><ol>{notes_html}</ol></div>
  <div class="score-box"><div class="t">得点記録</div>
    <table><tr>{head}</tr><tr>{body}</tr></table></div>
</section>'''


def answer_sheet(daimons, get_label):
    """マーク記入用の解答用紙。"""
    tables = []
    for dm, label, pts in daimons:
        qs = dm['question_data']['questions']
        head = ''.join(f'<th>問{i + 1}</th>' for i in range(len(qs)))
        cells = ''.join('<td class="mk">① ② ③ ④</td>' for _ in qs)
        pt = ''.join(f'<td>{p}</td>' for p in pts)
        tables.append(
            f'<table><caption>{esc(label)}（{sum(pts)}点）</caption>'
            f'<tr><th>設問</th>{head}</tr>'
            f'<tr><th>解答欄</th>{cells}</tr>'
            f'<tr><th>配点</th>{pt}</tr></table>')
    return ('<section class="answer-sheet"><h2 class="sec">解答用紙</h2>'
            '<p class="lead">正しいと思う選択肢の番号を 1 つ選び、○ で囲むこと。</p>'
            + ''.join(tables) + '</section>')


# =====================================================================
# 冊子の組み立て
# =====================================================================
def load(name):
    with open(os.path.join(ROOT, 'seed-data', f'kyotsu_mogi2026_{name}_manual.json'), encoding='utf-8') as f:
        return json.load(f)['questions']


def eng_daimons():
    out = []
    for r in load('eng'):
        label = r['question_data']['format_type']
        pts = ENG_POINTS[label]
        qs = r['question_data']['questions']
        if len(pts) != len(qs):
            raise SystemExit(f'❌ 配点表と小問数が不一致: {label} ({len(pts)} vs {len(qs)})')
        out.append((r, label, pts))
    return out


def math_daimons(part):
    out = []
    for r in load('math'):
        if r['part_key'] != part:
            continue
        label = r['question_data']['group']
        qs = r['question_data']['questions']
        out.append((r, label, [MATH_POINT_PER_SUB] * len(qs)))
    return out


def render_daimon(dm, label, pts, lead=None):
    qd = dm['question_data']
    parts = [f'<section class="daimon">',
             f'<div class="daimon-head"><span>{esc(label)}</span>'
             f'<span class="pt">配点 {sum(pts)} 点</span></div>']
    if lead:
        parts.append(f'<div class="lead">{esc(lead)}</div>')
    parts.append(f'<div class="passage">{qd["passage"]}</div>')
    for i, q in enumerate(qd['questions']):
        ch = ''.join(f'<li><span class="mk">{CIRCLED[j]}</span>{c}</li>'
                     for j, c in enumerate(q['choices']))
        parts.append(
            f'<div class="q"><div class="stem"><span class="no">問{i + 1}</span>{q["stem"]}'
            f'<span class="pt">({pts[i]}点)</span></div>'
            f'<ol class="ch">{ch}</ol></div>')
    parts.append('</section>')
    return '\n'.join(parts)


def render_key_table(daimons):
    rows = []
    for dm, label, pts in daimons:
        for i, q in enumerate(dm['question_data']['questions']):
            rows.append(
                f'<tr><td>{esc(label)}</td><td class="c">問{i + 1}</td>'
                f'<td class="ans">{CIRCLED[q["answer"]]}</td>'
                f'<td class="c">{pts[i]}</td><td>{esc(q["unit"])}</td></tr>')
    return ('<table class="key"><tr><th>大問</th><th>設問</th><th>正解</th>'
            '<th>配点</th><th>単元</th></tr>' + ''.join(rows) + '</table>')


MATH_SECTIONS = ('方針', '立式', '計算', '答え', '補足')


def esc_keep_tex(s):
    """LaTeX の \\( ... \\) は素通しし、それ以外の地の文だけ HTML エスケープする。"""
    out, last = [], 0
    for m in TEX_RE.finditer(s or ''):
        out.append(esc(s[last:m.start()]))
        out.append(m.group(0))
        last = m.end()
    out.append(esc((s or '')[last:]))
    return ''.join(out)


def format_explanation(body):
    """解説を組版する。2 つの正規フォーマットをそれぞれの見え方に落とす。

    数学: 「方針/立式/計算/答え/補足」の 5 行 → ラベル付きの段組み
    英語: 「## 🎯 コアイメージ」等の 4 セクション Markdown → 小見出し + 箇条書き
    冒頭の「正解は「…」。」は正解欄に別途出すので本文からは落とす。

    ★ 必ず LaTeX 描画**前**の生テキストに対して呼ぶこと。KaTeX が吐く HTML は
      \\sqrt 等の SVG path に改行を含むため、描画後に行分割すると path データが
      本文として露出する (2026-08-02 に実際に発生)。
    """
    body = re.sub(r'^正解は「.*?」。\s*', '', body or '', flags=re.S)

    if body.lstrip().startswith('##'):          # --- 英語: 4 セクション Markdown ---
        out = []
        for chunk in re.split(r'\n(?=##\s)', body.strip()):
            lines = chunk.split('\n')
            head = lines[0].lstrip('#').strip()
            out.append(f'<div class="exp-sec">{md_inline(esc_keep_tex(head))}</div>')
            in_list = False                     # ★ ul の開閉はフラグ 1 つで管理する
            for ln in lines[1:]:                #   (直前要素を見る方式は li の後に ul を再度開き入れ子になる)
                stripped = ln.strip()
                if stripped.startswith('- '):
                    if not in_list:
                        out.append('<ul>')
                        in_list = True
                    out.append(f'<li>{md_inline(esc_keep_tex(stripped[2:]))}</li>')
                elif stripped:
                    if in_list:
                        out.append('</ul>')
                        in_list = False
                    out.append(f'<div class="exp-line">{md_inline(esc_keep_tex(ln))}</div>')
            if in_list:
                out.append('</ul>')
        return ''.join(out)

    if re.match(r'\s*方針\s*[:：]', body):        # --- 数学: 5 セクション ---
        out = []
        for ln in body.strip().split('\n'):
            m = re.match(r'\s*(' + '|'.join(MATH_SECTIONS) + r')\s*[:：]\s*(.*)$', ln, re.S)
            if m:
                out.append(f'<div class="exp-step"><span class="lbl">{m.group(1)}</span>'
                           f'<span class="txt">{esc_keep_tex(m.group(2))}</span></div>')
            elif ln.strip():
                out.append(f'<div class="exp-line">{esc_keep_tex(ln)}</div>')
        return ''.join(out)

    return f'<div class="exp-line">{esc_keep_tex(body)}</div>'


def md_inline(s):
    """解説内のインライン Markdown (**強調** と `コード`) だけを HTML にする。"""
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    return s


def render_explanations(daimons):
    parts = []
    for dm, label, pts in daimons:
        parts.append(f'<section class="daimon"><div class="daimon-head">'
                     f'<span>{esc(label)}</span><span class="pt">配点 {sum(pts)} 点</span></div>')
        for i, q in enumerate(dm['question_data']['questions']):
            correct = q['choices'][q['answer']]      # 正解は必ず answer から引く (解説文の書式に依存しない)
            parts.append(
                f'<div class="exp"><div class="h">問{i + 1}'
                f'<span class="unit">{esc(q["unit"])} / {pts[i]}点</span></div>'
                f'<div class="qs">{q["stem"]}</div>'
                f'<div class="ans">正解 {CIRCLED[q["answer"]]} … {correct}</div>'
                f'<div class="body">{q["explanation"]}</div></div>')
        parts.append('</section>')
    return '\n'.join(parts)


# =====================================================================
# PDF 出力
# =====================================================================
def katex_css():
    with open(os.path.join(KATEX_DIR, 'katex.min.css'), encoding='utf-8') as f:
        css = f.read()
    # 相対パスのフォント参照を絶対 file:// に書き換える (印刷時にフォントが落ちないように)
    return css.replace('url(fonts/', f'url(file://{KATEX_DIR}/fonts/')


def _chromium_path():
    """既設 Chromium の実体を探す (playwright の期待する build 番号に依存しない)。"""
    import glob
    base = os.environ.get('PLAYWRIGHT_BROWSERS_PATH', '/opt/pw-browsers')
    for pat in (f'{base}/chromium-*/chrome-linux/chrome',
                f'{base}/chromium_headless_shell-*/chrome-linux/headless_shell'):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    return None   # 見つからなければ playwright の既定解決に任せる


def write_pdf(html, out_name, title):
    from playwright.sync_api import sync_playwright
    os.makedirs(WORK, exist_ok=True)
    html_path = os.path.join(WORK, out_name.replace('.pdf', '.html'))
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    out_path = os.path.join(ROOT, out_name)
    footer = ('<div style="width:100%;font-size:7pt;color:#7b8494;'
              'font-family:sans-serif;padding:0 14mm;display:flex;'
              'justify-content:space-between;">'
              f'<span>{esc(title)}</span>'
              '<span><span class="pageNumber"></span> / '
              '<span class="totalPages"></span></span></div>')
    with sync_playwright() as p:
        # playwright の pin と /opt/pw-browsers の build 番号がずれても落ちないよう実体を直接指す
        browser = p.chromium.launch(executable_path=_chromium_path())
        page = browser.new_page()
        page.goto(f'file://{html_path}', wait_until='load')
        page.pdf(path=out_path, format='A4', print_background=True,
                 display_header_footer=True,
                 header_template='<div></div>', footer_template=footer,
                 margin={'top': '16mm', 'bottom': '16mm', 'left': '14mm', 'right': '14mm'})
        browser.close()
    size = os.path.getsize(out_path) / 1024
    print(f'   ✅ {out_name}  ({size:.0f} KB)')
    return out_path


def main():
    if not os.path.isdir(KATEX_DIR):
        raise SystemExit('❌ vendor/katex が見つかりません')
    os.makedirs(WORK, exist_ok=True)
    kcss = katex_css()

    eng = eng_daimons()
    ia = math_daimons('math_1a')
    iib = math_daimons('math_2b')
    print(f'読み込み: 英語 {len(eng)} 大問 / 数学I・A {len(ia)} 大問 / 数学II・B・C {len(iib)} 大問')

    # ---- 英語 問題編 ----
    eng_total = sum(sum(p) for _, _, p in eng)
    body = cover(
        '共通テスト模試 2026  英語（リーディング）', '問題編',
        [('試験時間', '80分'), ('満点', f'{eng_total}点'),
         ('構成', f'{len(eng)}大問 / {sum(len(d[0]["question_data"]["questions"]) for d in eng)}問'),
         ('出題形式', '全問マーク式（4択）')],
        ['解答は各設問の①〜④から最も適当なものを 1 つ選ぶこと。',
         '巻末の解答用紙に記入すること。問題冊子への書き込みは自由。',
         '辞書・電子機器の使用は認めない。',
         '本文の内容に照らして答えること。一般常識ではなく本文の記述を根拠にすること。'],
        [('得点', ''), ('満点', f'{eng_total}'), ('得点率', '      %'), ('実施日', '    /    ')])
    for dm, label, pts in eng:
        body += render_daimon(dm, label, pts)
    body += answer_sheet(eng, None)
    write_pdf(page_head('共通テスト模試2026 英語 問題編', kcss) + body + '</body></html>',
              'kyotsu-mogi2026-eng-mondai.pdf', '共通テスト模試 2026 英語 問題編')

    # ---- 英語 解答・解説編 ----
    body = cover(
        '共通テスト模試 2026  英語（リーディング）', '解答・解説編',
        [('満点', f'{eng_total}点'),
         ('構成', f'{len(eng)}大問 / {sum(len(d[0]["question_data"]["questions"]) for d in eng)}問'),
         ('内容', '正解一覧・設問別の解説（根拠となる本文表現つき）')],
        ['解説には、正解の根拠となる本文中の英文をそのまま引用してある。必ず本文に戻って確認すること。',
         '誤答の選択肢についても、なぜ誤りかを示してある。間違えた問題はそこまで読むこと。',
         '「単元」欄は弱点分析用のタグで、アプリの単元別ドリルの分類と対応している。'],
        [('得点', ''), ('満点', f'{eng_total}'), ('得点率', '      %'), ('実施日', '    /    ')])
    body += '<h2 class="sec">正解一覧</h2>' + render_key_table(eng)
    body += render_explanations(eng)
    write_pdf(page_head('共通テスト模試2026 英語 解答・解説編', kcss) + body + '</body></html>',
              'kyotsu-mogi2026-eng-kaisetsu.pdf', '共通テスト模試 2026 英語 解答・解説編')

    # ---- 数学 問題編 ----
    ia_total = sum(sum(p) for _, _, p in ia)
    iib_total = sum(sum(p) for _, _, p in iib)
    n_math_q = sum(len(d[0]['question_data']['questions']) for d in ia + iib)
    body = cover(
        '共通テスト模試 2026  数学', '問題編（数学I・A / 数学II・B・C）',
        [('構成', f'数学I・A {len(ia)}大問 {ia_total}点 ／ 数学II・B・C {len(iib)}大問 {iib_total}点'),
         ('小問数', f'{n_math_q}問（各4点）'),
         ('目安時間', '各編 90分（大問1つあたり15分）'),
         ('出題形式', '全問マーク式（4択）')],
        ['解答は各設問の①〜④から正しいものを 1 つ選ぶこと。',
         '本番と同じ 70 分で通したい場合は、各編の第1問〜第4問（80点満点）を選んで解くとよい。',
         '計算用紙は各自で用意すること。問題冊子の余白を使ってよい。',
         '各小問は独立しており、前の問題の答えを使わなくても解ける。'
         '必要な条件は各小問に再掲してある。'],
        [('I・A 得点', ''), ('/ 満点', f'{ia_total}'), ('II・B・C 得点', ''),
         ('/ 満点', f'{iib_total}'), ('実施日', '    /    ')])
    body += '<h2 class="sec">数学I・A</h2>'
    for dm, label, pts in ia:
        body += render_daimon(dm, label, pts)
    body += '<h2 class="sec">数学II・B・C</h2>'
    for dm, label, pts in iib:
        body += render_daimon(dm, label, pts)
    body += answer_sheet(ia + iib, None)
    write_pdf(page_head('共通テスト模試2026 数学 問題編', kcss) + body + '</body></html>',
              'kyotsu-mogi2026-math-mondai.pdf', '共通テスト模試 2026 数学 問題編')

    # ---- 数学 解答・解説編 ----
    body = cover(
        '共通テスト模試 2026  数学', '解答・解説編（数学I・A / 数学II・B・C）',
        [('構成', f'数学I・A {len(ia)}大問 ／ 数学II・B・C {len(iib)}大問'),
         ('小問数', f'{n_math_q}問（各4点）'),
         ('内容', '正解一覧・設問別の解説（方針→立式→計算→つまずきやすい点）')],
        ['解説は「どの公式をなぜ選ぶか」から書いてある。答えが合っていた問題も方針を確認すること。',
         '各解説の末尾に、典型的な誤答がどの計算ミスから出るかを示してある。'
         '自分の誤答がそこに載っていれば、原因がその場で特定できる。',
         '「単元」欄は弱点分析用のタグで、アプリの単元別ドリルの分類と対応している。'],
        [('I・A 得点', ''), ('/ 満点', f'{ia_total}'), ('II・B・C 得点', ''),
         ('/ 満点', f'{iib_total}'), ('実施日', '    /    ')])
    body += '<h2 class="sec">正解一覧（数学I・A）</h2>' + render_key_table(ia)
    body += '<h2 class="sec">正解一覧（数学II・B・C）</h2>' + render_key_table(iib)
    body += '<h2 class="sec">解説（数学I・A）</h2>' + render_explanations(ia)
    body += '<h2 class="sec">解説（数学II・B・C）</h2>' + render_explanations(iib)
    write_pdf(page_head('共通テスト模試2026 数学 解答・解説編', kcss) + body + '</body></html>',
              'kyotsu-mogi2026-math-kaisetsu.pdf', '共通テスト模試 2026 数学 解答・解説編')

    print('\n✅ PDF 4 冊を生成しました')


if __name__ == '__main__':
    # 全テキストの LaTeX を先に一括で KaTeX HTML へ (node 呼び出しは 1 回だけ)
    _orig_load = load
    _cache = {}

    def load(name):  # noqa: F811
        if name in _cache:
            return _cache[name]
        rows = _orig_load(name)
        buf, slots = [], []
        for r in rows:
            qd = r['question_data']
            # ★ 本文も必ず LaTeX 描画に通す。通し忘れると \( \) が生のまま残り、
            #   日本語フォントではバックスラッシュが ¥ として表示される (2026-08-02 に発生)。
            qd['passage'] = format_passage(qd['passage'])
            slots.append((qd, 'passage')); buf.append(qd['passage'])
            for q in qd['questions']:
                slots.append((q, 'stem')); buf.append(q['stem'])
                q['explanation'] = format_explanation(q['explanation'])   # ★ 描画前に段組み
                slots.append((q, 'explanation')); buf.append(q['explanation'])
                for i, c in enumerate(q['choices']):
                    slots.append((q['choices'], i)); buf.append(c)
        for (target, key), val in zip(slots, render_tex_all(buf)):
            target[key] = val
        _cache[name] = rows
        return rows

    sys.exit(main() or 0)
