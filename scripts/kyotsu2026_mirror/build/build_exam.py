#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""横書き科目(数学ⅠA/数学ⅡBC/英語)の 問題編+解答編 ビルダー。

usage: python3 build_exam.py <subject_key>   (math1a | math2bc | english)
入力: ../content/<subject_key>.json (問題) ../content/<subject_key>_ans.json (解答)
出力: ~/Desktop/共通テスト2026類似問題/<title>_問題.pdf / _解答.pdf
"""
import json, os, sys

from common import (CONTENT, OUTDIR, ensure_outdir, wrap_doc, chrome_pdf,
                    render_blocks, rich, esc, slot_span, qbox, CIRCLED, HERE)

EXTRA_CSS = """
.cover { min-height:250mm; display:flex; flex-direction:column; align-items:center;
  padding-top:30mm; break-after:page; }
.cover .brand { font-size:11pt; color:#555; letter-spacing:.3em;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.cover .h { font-size:26pt; font-weight:800; margin:10mm 0 3mm; letter-spacing:.1em;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.cover .sub { font-size:13pt; margin-bottom:14mm; color:#333;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.cover .meta { font-size:12pt; margin-bottom:12mm; }
.cover .notes { border:1.4px solid #222; padding:6mm 8mm; width:150mm; font-size:10pt;
  line-height:2.0; }
.cover .notes .nt { font-weight:700; text-align:center; margin-bottom:2mm;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:11pt; }
.cover .notes ol { margin:0; padding-left:1.6em; }
.cover .foot { margin-top:auto; font-size:9.5pt; color:#666; }
.eng .bp { font-family:"Times New Roman","Hiragino Mincho ProN",serif; text-align:justify; }
.eng .qcbody, .eng .qstem, .eng .chc { font-family:"Times New Roman","Hiragino Mincho ProN",serif; }
.passage { border:1px solid #999; padding:4mm 5mm; margin:2.5mm 0; }
.ansline { display:flex; gap:2em; align-items:baseline; }
/* 正規分布表: 36行を1ページに収める圧縮版 */
.normtbl table.tbl { font-size:7.2pt; }
.normtbl table.tbl th, .normtbl table.tbl td { padding:0.3mm 1.3mm; }
.normtbl .figcap { margin-top:0.5mm; font-size:8pt; }

/* ===== 英語素材コンポーネント ===== */
.mat { border:1.3px solid #333; padding:4mm 5mm; margin:3mm 1mm; break-inside:avoid;
  font-family:"Helvetica Neue",Arial,sans-serif; font-size:9.8pt; line-height:1.65; }
.mat-t { font-weight:700; text-align:center; font-size:11.5pt; margin-bottom:2mm; }
.chat { width:118mm; margin:3mm auto; border:1.2px solid #555; border-radius:3mm;
  padding:3.5mm 4mm; font-family:"Helvetica Neue",Arial,sans-serif; font-size:9.6pt; }
.chat .cname { font-weight:700; font-size:8.6pt; margin:1.6mm 0 .4mm; }
.chat .bub { border:1px solid #888; border-radius:2.2mm; padding:1.4mm 2.6mm; display:inline-block;
  max-width:96mm; line-height:1.5; background:#fff; }
.chat .me { text-align:right; }
.chat .me .bub { background:#eef4ee; }
.chat .stamp { font-size:7.8pt; color:#777; }
.web { border:1.2px solid #444; margin:3mm 1mm; font-family:"Helvetica Neue",Arial,sans-serif;
  font-size:9.7pt; line-height:1.68; break-inside:avoid; }
.web-bar { background:#e8e8e8; border-bottom:1px solid #444; padding:1.2mm 3mm; font-size:8.6pt; color:#333; }
.web-in { padding:3mm 4.5mm; }
.web h3 { margin:0 0 2mm; font-size:12pt; text-align:center; }
.comment { border-top:1px dashed #777; margin-top:2.5mm; padding-top:1.6mm; }
.comment .cwho { font-weight:700; font-size:8.8pt; }
.email { border:1.2px solid #444; margin:3mm 1mm; font-family:"Helvetica Neue",Arial,sans-serif;
  font-size:9.7pt; line-height:1.66; break-inside:avoid; }
.email .ehead { border-bottom:1px solid #444; padding:2mm 3.5mm; background:#f4f4f4; }
.email .ehead div { margin:.3mm 0; }
.email .ebody { padding:3mm 4.5mm; }
.flyer { border:2px solid #222; margin:3mm auto; padding:3.5mm 5mm; width:128mm;
  font-family:"Helvetica Neue",Arial,sans-serif; font-size:9.6pt; line-height:1.6; break-inside:avoid; }
.flyer .f-title { text-align:center; font-size:13pt; font-weight:800; letter-spacing:.04em; margin-bottom:1.6mm; }
.flyer .f-sub { text-align:center; font-size:9.5pt; margin-bottom:2mm; }
.flyer hr { border:none; border-top:1.2px solid #333; margin:1.6mm 0; }
.slides { display:grid; grid-template-columns:1fr 1fr; gap:3mm; margin:3mm 2mm; }
.slide { border:1.2px solid #333; padding:2.5mm 3mm; min-height:30mm;
  font-family:"Helvetica Neue",Arial,sans-serif; font-size:9.2pt; line-height:1.55; }
.slide .s-t { font-weight:700; text-align:center; border-bottom:1px solid #999;
  padding-bottom:1mm; margin-bottom:1.6mm; }
.slide ul { margin:0; padding-left:1.3em; }
.handw, .handw * { font-family:"Bradley Hand","Segoe Print","Comic Sans MS",cursive; }
.hnote { border:1.1px solid #666; background:#fffdf2; padding:2.5mm 3.5mm; margin:2mm 1mm;
  font-size:10pt; line-height:1.7; }
.outline { border:1.4px solid #222; padding:3mm 4.5mm; margin:3mm 1mm;
  font-family:"Helvetica Neue",Arial,sans-serif; font-size:9.8pt; break-inside:avoid; }
.outline .o-t { font-weight:700; text-align:center; margin-bottom:1.8mm; }
.twocol { display:grid; grid-template-columns:1fr 52mm; gap:4mm; align-items:start; }
.poem-line { margin:.4mm 0; }
.eng .fig svg text { font-family:"Helvetica Neue",Arial,sans-serif; }
"""

ANS_CSS = """
.anstbl-w { margin: 4mm 0; }
table.anstbl { border-collapse:collapse; font-size:9.6pt; margin:0 auto 4mm; }
table.anstbl th, table.anstbl td { border:1px solid #444; padding:1mm 2.6mm; text-align:center; }
table.anstbl th { background:#eef2f7; font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:600; }
.kai-h { font-size:11.5pt; font-weight:700; border-left:4px solid #1f3a5f; padding-left:2mm;
  margin:4.5mm 0 2mm; font-family:"Hiragino Kaku Gothic ProN",sans-serif; break-after:avoid; }
.kai { font-size:9.9pt; line-height:1.9; }
.kai .bp { font-size:9.9pt; line-height:1.9; margin:1.2mm 0; }
.kai .dm { font-size:10pt; margin:1.6mm 0 1.6mm 6mm; }
"""


def load(subject):
    """content/<subject>.py (PROB/ANS を定義した Python モジュール) を優先、無ければJSON。
    Pythonモジュール形式なら LaTeX 文字列を raw string で書けてエスケープ事故が無い。"""
    py = os.path.join(CONTENT, subject + ".py")
    if os.path.exists(py):
        import importlib.util, sys as _sys
        if CONTENT not in _sys.path:
            _sys.path.insert(0, CONTENT)
        spec = importlib.util.spec_from_file_location("content_" + subject, py)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.PROB, mod.ANS
    with open(os.path.join(CONTENT, subject + ".json")) as f:
        prob = json.load(f)
    with open(os.path.join(CONTENT, subject + "_ans.json")) as f:
        ans = json.load(f)
    return prob, ans


def build_cover(meta, kind):
    notes = "".join(f"<li>{rich(n)}</li>" for n in meta.get("notes", []))
    sel = f'<p class="bp" style="margin-top:3mm">{rich(meta["select_note"])}</p>' if meta.get("select_note") else ""
    kindlab = "問題" if kind == "prob" else "解答・解説"
    return f"""
<div class="cover">
  <div class="brand">TRILLION AI JUKU ── SOKKURI MOCK</div>
  <div class="h">{esc(meta["title"])}</div>
  <div class="sub">2026年共通テスト 完全類似形式 オリジナル問題 ── {kindlab}編</div>
  <div class="meta">試験時間 {esc(meta["time"])} ／ {esc(str(meta["max_points"]))}点満点</div>
  <div class="notes"><div class="nt">注　意　事　項</div><ol>{notes}</ol>{sel}</div>
  <div class="foot">本問題は2026年度大学入学共通テストの出題形式・難易度を忠実に再現したオリジナル問題です。実際の試験問題ではありません。</div>
</div>"""


def sec_header(sec):
    # 実物体裁: 「第N問 （必答問題）（配点 15）」— 種別は配点の前・丸括弧。
    opt = f'<span class="pts">（{esc(sec["optional"])}）</span>' if sec.get("optional") else ""
    title = f'　{esc(sec["title"])}' if sec.get("title") else ""
    return (f'<div class="sec-h">第{sec["no"]}問{title}{opt}'
            f'<span class="pts">（配点　{sec["points"]}）</span></div>')


def build_problem(prob):
    out = []
    for sec in prob["sections"]:
        buf = [sec_header(sec)]
        if sec.get("lead"):
            buf.append(f'<p class="bp">{rich(sec["lead"])}</p>')
        for part in sec["parts"]:
            if part.get("label"):
                buf.append(f'<div class="part-lab">{esc(part["label"])}</div>')
            buf.append(render_blocks(part["blocks"]))
        out.append(f'<div class="sec-wrap">{"".join(buf)}</div>')
    return "".join(out)


def build_answer(prob, ans):
    """解答編: 正解一覧表 + 大問別解説"""
    out = []
    # --- 正解一覧 ---
    out.append('<div class="sec-h">正解一覧</div>')
    for sec in ans["sections"]:
        rows = []
        if "slots" in sec:  # 数学: スロット表
            items = list(sec["slots"].items())
            CH = 8
            for i in range(0, len(items), CH):
                chunk = items[i:i + CH]
                rows.append("<tr>" + "".join(f"<th>{slot_span(k)}</th>" for k, _ in chunk) + "</tr>")
                rows.append("<tr>" + "".join(f"<td>{rich(str(v))}</td>" for _, v in chunk) + "</tr>")
            out.append(f'<div class="anstbl-w"><div class="kai-h">第{sec["section"]}問</div>'
                       f'<table class="anstbl">{"".join(rows)}</table></div>')
        else:  # 国語/英語: 設問番号→正解
            qs = sec["answers"]
            head = "<tr><th>問題番号</th>" + "".join(f"<td>{qbox(q['qno'])}</td>" for q in qs) + "</tr>"
            corr = "<tr><th>正解</th>" + "".join(f"<td>{esc(str(q['answer']))}</td>" for q in qs) + "</tr>"
            pts = "<tr><th>配点</th>" + "".join(f"<td>{q['points']}</td>" for q in qs) + "</tr>"
            out.append(f'<div class="anstbl-w"><div class="kai-h">第{sec["section"]}問（{sec.get("points","")}点）</div>'
                       f'<table class="anstbl">{head}{corr}{pts}</table></div>')
    # --- 解説 ---
    out.append('<div class="sec-wrap"><div class="sec-h">解説</div></div>')
    for sec in ans["sections"]:
        out.append(f'<div class="kai-h" style="font-size:12pt">第{sec["section"]}問</div><div class="kai">')
        for k in sec.get("kai", []):
            if k.get("heading"):
                out.append(f'<div class="kai-h">{rich(k["heading"])}</div>')
            out.append(render_blocks(k["blocks"]))
        out.append("</div>")
    return "".join(out)


def main():
    subject = sys.argv[1]
    ans_only = "--answers-only" in sys.argv  # 国語: 問題編は build_kokugo.py(縦書き)
    prob, ans = load(subject)
    meta = prob["meta"]
    ensure_outdir()
    body_cls = "eng" if subject == "english" else ""

    kinds = [("ans", "解答")] if ans_only else [("prob", "問題"), ("ans", "解答")]
    for kind, suffix in kinds:
        body = build_cover(meta, kind)
        body += build_problem(prob) if kind == "prob" else build_answer(prob, ans)
        css = EXTRA_CSS + (ANS_CSS if kind == "ans" else "")
        doc = wrap_doc(f'{meta["title"]} {suffix}編', f'<div class="{body_cls}">{body}</div>', css)
        html_path = os.path.join(HERE, f"_{subject}_{kind}.html")
        with open(html_path, "w") as f:
            f.write(doc)
        pdf_path = os.path.join(OUTDIR, f'{meta["outname"]}_{suffix}編.pdf')
        chrome_pdf(html_path, pdf_path)


if __name__ == "__main__":
    main()
