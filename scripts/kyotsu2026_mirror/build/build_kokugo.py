#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""国語(縦書き)の 問題編+解答編 ビルダー。

Chrome は長い vertical-rl フローを複数ページに分割できない(最後の1ページ分しか
出ない既知バグ)ため、固定A4紙面(.sheet)へ**実測ベース**で手動分割する:
  1) 全フロー単位を measure.html に並べ Chrome --dump-dom で各単位の実幅(px)を計測
  2) 実測幅で貪欲パッキング(入り切らない段落は文単位で比例分割)
  3) .sheet 群を組んで --print-to-pdf

紙面: A4縦・縦書き1段(本文ブロック高200mm・12pt・行送り≈1.9)= 実物(B5・43字/行)に
近い1行48字前後の紙面感。実用文の資料は横組み枠(hframe)を縦フローに埋め込む。

UNIT型: lead / para / h / note / q / kanbun / waka / convo_v / hframe / secbreak / vgap
インライン記法: <lA>…</lA>(傍線部A) <wv>…</wv>(波線) <bx>…</bx>(四角囲み) $..$は使わない
"""
import json, os, re, subprocess, sys, html as _html

from common import CHROME, CONTENT, HERE, OUTDIR, ensure_outdir, esc, CIRCLED

MM = 96 / 25.4  # px per mm
COL_H_MM = 200.0        # 本文ブロックの高さ(1段)
PAGE_W_MM = 174.0       # 紙面の使用可能幅
SLACK_MM = 5.0          # 各sheetの安全マージン
FONT_PT = 12.0

_LINE = re.compile(r"&lt;l([A-Fア-オ1-6])&gt;(.*?)&lt;/l\1&gt;", re.S)
_WAVE = re.compile(r"&lt;wv&gt;(.*?)&lt;/wv&gt;", re.S)
_BOXW = re.compile(r"&lt;bx&gt;(.*?)&lt;/bx&gt;", re.S)
_ALLOWED = re.compile(r"&lt;(/?)(b|u|br|ruby|rt|rp|em|small)&gt;")
_DIG = re.compile(r"(?<![0-9])([0-9]{1,3})(?![0-9])")
_SENT = re.compile(r"(?<=[。」！？])")


def vesc(s: str) -> str:
    """縦書き用: エスケープ→許可タグ復元→傍線/波線/囲み→半角数字を縦中横。"""
    e = _html.escape(str(s), quote=False)
    e = _ALLOWED.sub(lambda m: "<%s%s>" % (m.group(1), m.group(2)), e)
    e = _LINE.sub(lambda m: f'<span class="lin"><span class="lin-lab">{m.group(1)}</span>{m.group(2)}</span>', e)
    e = _WAVE.sub(lambda m: f'<span class="wave">{m.group(1)}</span>', e)
    e = _BOXW.sub(lambda m: f'<span class="bxw">{m.group(1)}</span>', e)
    parts = re.split(r"(<[^>]*>)", e)
    e = "".join(p if p.startswith("<") else _DIG.sub(_digrep, p) for p in parts)
    return e


def _digrep(m):
    """半角数字: 2桁以上は縦中横(tcy)、1桁は正立(upr)。1桁を tcy に任せると横倒しになる。"""
    d = m.group(1)
    cls = "tcy" if len(d) >= 2 else "upr"
    return f'<span class="{cls}">{d}</span>'


def vslot(no) -> str:
    """解答番号ボックス。2桁は縦中横(tcy)で1マスに、1桁は upright で正立させる。
    (1桁を tcy に任せると Chrome は既定の mixed 方向で横倒しになるため。)"""
    s = str(no)
    cls = "tcy" if len(s) >= 2 else "upr"
    return f'<span class="vslot"><span class="{cls}">{s}</span></span>'


# ---------------- unit renderers → (html, splittable_sentences|None) ----------------

def u_lead(u):
    return f'<p class="vlead">{vesc(u["text"])}</p>', None


def u_para(u):
    ind = "" if u.get("noindent") else 'style="text-indent:1em"'
    return f'<p class="vpara" {ind}>{vesc(u["text"])}</p>', u["text"]


def u_h(u):
    return f'<div class="vh">{vesc(u["text"])}</div>', None


def u_note(u):
    items = "".join(
        f'<div class="vnote-i"><span class="vnote-no">{vesc(n)}</span>{vesc(w)}――{vesc(m)}</div>'
        for n, w, m in u["items"])
    return f'<div class="vnote"><div class="vnote-h">（注）</div>{items}</div>', None


def u_q(u):
    stem = vesc(u["stem"])
    if "{QB}" in u["stem"]:   # 二つ選べ等: 解答番号ボックスを2つ({Q}・{QB})
        stem = stem.replace("{Q}", vslot(u["no"])).replace("{QB}", vslot(u["no"] + 1))
    elif "{Q}" in u["stem"]:
        stem = stem.replace("{Q}", vslot(u["no"]))
    elif u.get("no") is not None:
        stem += "　" + vslot(u["no"])
    ch = ""
    if u.get("choices"):
        ch = "".join(
            f'<div class="vchoice"><span class="vchlab">{CIRCLED[i+1]}</span>{vesc(c)}</div>'
            for i, c in enumerate(u["choices"]))
    # qlabel を省略した場合は「問N」見出しを出さない(柱書きと選択肢を別ユニットに割る用途)
    # qlabel は vesc を通し、算用数字(問1 等)を正立させる。
    lab = f'<div class="vq-lab">問{vesc(str(u["qlabel"]))}</div>' if u.get("qlabel") not in (None, "") else ""
    stem_html = f'<div class="vq-stem">{stem}</div>' if u.get("stem") else ""
    return (f'<div class="vq">{lab}{stem_html}{ch}</div>'), None


def u_kanbun(u):
    """rows: list of {ch, ok(送り仮名), kaeri(返り点), ruby} or {"punc": "。"} or {"gap":1}"""
    cells = []
    for r in u["rows"]:
        if "punc" in r:
            cells.append(f'<span class="kb-punc">{esc(r["punc"])}</span>')
            continue
        # 振り仮名(ruby)と送り仮名(ok)は文字の右側に「読みの続き」として1列にまとめる
        # (別々に絶対配置すると右側で重なるため)。返り点(kaeri)は左下。
        side = ""
        if r.get("ruby"):
            side += f'<span class="kb-rb">{esc(r["ruby"])}</span>'
        if r.get("ok"):
            side += f'<span class="kb-ok">{esc(r["ok"])}</span>'
        side = f'<span class="kb-side">{side}</span>' if side else ""
        ka = f'<span class="kb-ka">{esc(r["kaeri"])}</span>' if r.get("kaeri") else ""
        line = r.get("line")  # 傍線ラベル(始端の1字のみに付す)
        ul = r.get("ul")       # ラベル無しで下線だけ引く(傍線span内の2字目以降)
        cls = "kb kb-lin" if (line or ul) else "kb"
        lab = f'<span class="lin-lab">{esc(line)}</span>' if line else ""
        cells.append(f'<span class="{cls}">{lab}<span class="kb-ch">{esc(r["ch"])}</span>{side}{ka}</span>')
    return f'<div class="kanbun">{"".join(cells)}</div>', None


def u_waka(u):
    lines = "".join(f'<p class="vwaka">{vesc(x)}</p>' for x in u["lines"])
    return lines, None


def u_convo(u):
    turns = "".join(
        f'<p class="vturn"><span class="vsp">{esc(t["sp"])}</span>――{vesc(t["text"])}</p>'
        for t in u["turns"])
    return f'<div class="vconvo">{turns}</div>', None


def u_hframe(u):
    h = u.get("height_mm", 120)
    w = u.get("width_mm")
    ws = f"width:{w}mm;" if w else ""
    return (f'<div class="hbox" style="height:{h}mm;{ws}">'
            f'<div class="hbox-in">{u["html"]}</div></div>'), None


UNITS = {"lead": u_lead, "para": u_para, "h": u_h, "note": u_note, "q": u_q,
         "kanbun": u_kanbun, "waka": u_waka, "convo_v": u_convo, "hframe": u_hframe,
         "vgap": lambda u: (f'<div style="width:{u.get("mm",6)}mm;display:inline-block"></div>', None)}


CSS = f"""
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin:0; padding:0; background:#fff; }}
body {{ -webkit-print-color-adjust:exact; print-color-adjust:exact;
  font-family:"Hiragino Mincho ProN","YuMincho","Yu Mincho",serif; color:#111; }}
.sheet {{ width:210mm; height:297mm; padding:24mm 18mm 0; position:relative;
  overflow:hidden; break-after:page; }}
.sheet:last-child {{ break-after:auto; }}
@media screen {{ body{{background:#e9edf2;}} .sheet{{margin:12px auto; box-shadow:0 2px 12px rgba(0,0,0,.2); background:#fff;}} }}
.vbody {{ writing-mode:vertical-rl; -webkit-writing-mode:vertical-rl; height:{COL_H_MM}mm;
  font-size:{FONT_PT}pt; line-height:1.9; letter-spacing:.04em; }}
.tcy {{ -webkit-text-combine:horizontal; text-combine-upright:all; }}
.upr {{ text-orientation:upright; -webkit-text-orientation:upright; text-combine-upright:none; }}
.vlead {{ margin:0 0 0 2mm; font-size:10.8pt; }}
.vpara {{ margin:0; }}
.vh {{ font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; margin:0 1.5mm; }}
.lin {{ text-decoration:underline; text-underline-offset:.16em; text-decoration-thickness:.8px; }}
.lin-lab {{ font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:.58em; font-weight:700;
  margin:0 .04em 0 0; vertical-align:.4em; }}
.wave {{ text-decoration:underline wavy; text-underline-offset:.16em; text-decoration-thickness:.7px; }}
.bxw {{ border:.9px solid #222; padding:.15em .02em; }}
.vnote {{ font-size:9.2pt; line-height:1.75; margin:0 2mm 0 1mm; }}
.vnote-h {{ font-weight:600; }}
.vnote-i {{ margin:0; }}
.vnote-no {{ font-size:.8em; margin:.1em .05em 0 0; }}
.vq {{ margin:0 2.2mm; }}
.vq-lab {{ font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; margin:0 0 0 1mm; }}
.vq-stem {{ margin:0; }}
.vchoice {{ margin:0; text-indent:-1.3em; padding-top:1.3em; }}
.vchlab {{ font-family:"Hiragino Kaku Gothic ProN",sans-serif; }}
.vslot {{ display:inline-block; border:1.1px solid #222; padding:.28em .04em; margin:.12em 0;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:.9em; }}
.vwaka {{ margin:0 0 0 1mm; padding-top:2.2em; }}
.vconvo {{ }}
.vturn {{ margin:0; text-indent:-4.6em; padding-top:4.6em; }}
.vsp {{ font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:600; }}
.kanbun {{ line-height:3.0; letter-spacing:.42em; margin:2mm 5mm; }}
.kb {{ position:relative; display:inline-block; }}
.kb-ch {{ }}
/* 振り仮名+送り仮名 を文字右側の1列に(縦書き・上下中央・重なり防止) */
.kb-side {{ position:absolute; right:-.56em; top:50%; transform:translateY(-50%);
  writing-mode:vertical-rl; -webkit-writing-mode:vertical-rl; font-size:.44em;
  line-height:1.04; letter-spacing:0; white-space:nowrap; }}
.kb-rb {{ }}
.kb-ok {{ }}
.kb-ka {{ position:absolute; font-size:.48em; left:-.4em; bottom:-.05em; line-height:1;
  writing-mode:vertical-rl; -webkit-writing-mode:vertical-rl;
  font-family:"Hiragino Mincho ProN",serif; }}
.kb-punc {{ }}
.kb-lin .kb-ch {{ text-decoration:underline; text-underline-offset:.14em; }}
.hbox {{ writing-mode:horizontal-tb; -webkit-writing-mode:horizontal-tb; display:inline-block;
  vertical-align:top; margin:0 3mm; }}
.hbox-in {{ font-size:9.5pt; line-height:1.7; }}
.sec-band {{ writing-mode:horizontal-tb; position:absolute; top:8mm; left:18mm; right:18mm;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:11pt; font-weight:700;
  border-bottom:1.2px solid #333; padding-bottom:1.5mm; }}
.sec-band .pts {{ font-weight:600; font-size:9.5pt; margin-left:1.5em; }}
.pageno {{ writing-mode:horizontal-tb; position:absolute; bottom:8mm; left:0; width:100%;
  text-align:center; font-size:9pt; color:#555; font-family:sans-serif; }}
/* 横組み資料(hframe)内の部品 */
.hbox-in .doc {{ border:1.2px solid #333; padding:3mm 4mm; }}
.hbox-in .doc-t {{ font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700;
  text-align:center; margin-bottom:2mm; font-size:10pt; }}
.hbox-in table {{ border-collapse:collapse; margin:1.5mm auto; font-size:8.8pt; }}
.hbox-in th, .hbox-in td {{ border:1px solid #444; padding:1mm 2.4mm; }}
.hbox-in th {{ background:#f0f0f0; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }}
.hbox-in ul {{ margin:1mm 0; padding-left:1.4em; }}
.hbox-in .src {{ font-size:8pt; color:#444; text-align:right; margin-top:1mm; }}
/* 表紙(横組み) */
.cover-sheet {{ writing-mode:horizontal-tb; }}
.cover {{ height:100%; display:flex; flex-direction:column; align-items:center; padding-top:28mm; }}
.cover .brand {{ font-size:11pt; color:#555; letter-spacing:.3em;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }}
.cover .h {{ font-size:27pt; font-weight:800; margin:10mm 0 3mm; letter-spacing:.14em;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }}
.cover .sub {{ font-size:13pt; margin-bottom:13mm; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }}
.cover .meta {{ font-size:12pt; margin-bottom:11mm; }}
.cover .notes {{ border:1.4px solid #222; padding:5mm 8mm; width:152mm; font-size:10pt; line-height:2.0; }}
.cover .notes .nt {{ font-weight:700; text-align:center; margin-bottom:2mm; font-size:11pt;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }}
.cover .notes ol {{ margin:0; padding-left:1.6em; }}
.cover .foot {{ margin-top:auto; margin-bottom:14mm; font-size:9.5pt; color:#666; }}
"""


def render_unit(u):
    return UNITS[u["t"]](u)


def measure(units_html):
    """各unitの縦書き実幅(px)をChromeで実測して返す。"""
    items = "".join(
        f'<div class="mrow"><div class="vbody mb" id="u{i}">{h}</div></div>'
        for i, h in enumerate(units_html))
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}
.mb {{ display:inline-block; }}
.mrow {{ margin:2px 0; }}
</style></head><body>{items}
<pre id="out"></pre>
<script>
const ws = [];
for (let i = 0; i < {len(units_html)}; i++) {{
  const el = document.getElementById('u' + i);
  ws.push(Math.ceil(el.getBoundingClientRect().width));
}}
document.getElementById('out').textContent = 'MEASURE_JSON=' + JSON.stringify(ws);
</script></body></html>"""
    mp = os.path.join(HERE, "_kokugo_measure.html")
    with open(mp, "w") as f:
        f.write(doc)
    r = subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                        "--virtual-time-budget=6000", "--dump-dom", "file://" + mp],
                       capture_output=True, text=True)
    m = re.search(r"MEASURE_JSON=(\[[0-9,\s]*\])", r.stdout)
    if not m:
        raise SystemExit("計測失敗: dump-domにMEASURE_JSONが無い\n" + r.stderr[:500])
    return json.loads(m.group(1))


def split_para_unit(u, ratio):
    """para unit を文境界で ratio(前半の割合) に近い位置で2分割。"""
    text = u["text"]
    sents = [s for s in _SENT.split(text) if s]
    if len(sents) < 2:
        return None
    total = len(text)
    acc, cut = 0, 0
    for i, s in enumerate(sents[:-1]):
        acc += len(s)
        if acc / total >= ratio * 0.92:
            cut = i + 1
            break
    if cut == 0:
        cut = max(1, len(sents) - 1)
    head = {"t": "para", "text": "".join(sents[:cut]), "noindent": u.get("noindent")}
    tail = {"t": "para", "text": "".join(sents[cut:]), "noindent": True}
    return head, tail


def paginate(section_units):
    """[(sec, unit), ...] → sheets: list of {sec, units_html:[...]}
    大問はsheet先頭から。実測幅で貪欲パック。溢れるparaは比例分割。"""
    page_w = PAGE_W_MM * MM
    sheets = []
    for sec, units in section_units:
        cur, used = [], 0.0
        queue = list(units)
        while queue:
            u = queue.pop(0)
            h, _ = render_unit(u)
            w = measure_cache[id_of(u)] if id_of(u) in measure_cache else None
            if w is None:
                w = measure([h])[0]
            limit = page_w - SLACK_MM * MM
            if used + w <= limit:
                cur.append(h)
                used += w
                continue
            room = limit - used
            if u["t"] == "para" and room > 18 * MM:
                sp = split_para_unit(u, room / w)
                if sp:
                    head, tail = sp
                    hh, _ = render_unit(head)
                    hw = measure([hh])[0]
                    if used + hw <= limit:
                        cur.append(hh)
                        queue.insert(0, tail)
                        sheets.append({"sec": sec, "units": cur})
                        cur, used = [], 0.0
                        continue
                    queue.insert(0, u)  # 前半すら入らない→次sheetへ
                else:
                    queue.insert(0, u)
            else:
                queue.insert(0, u)
            sheets.append({"sec": sec, "units": cur})
            cur, used = [], 0.0
        if cur:
            sheets.append({"sec": sec, "units": cur})
    return sheets


measure_cache = {}


def id_of(u):
    return json.dumps(u, ensure_ascii=False, sort_keys=True)


def load_prob(subject):
    py = os.path.join(CONTENT, subject + ".py")
    if os.path.exists(py):
        import importlib.util, sys as _sys
        if CONTENT not in _sys.path:
            _sys.path.insert(0, CONTENT)
        spec = importlib.util.spec_from_file_location("content_" + subject, py)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.PROB
    with open(os.path.join(CONTENT, subject + ".json")) as f:
        return json.load(f)


def build(subject="kokugo"):
    prob = load_prob(subject)
    ensure_outdir()
    build_from(prob, os.path.join(OUTDIR, f'{prob["meta"]["outname"]}_問題編.pdf'),
               html_name=f"_{subject}_prob.html")


def build_from(prob, out_pdf, html_name="_kokugo_prob.html"):
    meta = prob["meta"]

    # --- 全unitを事前レンダリング&一括計測(キャッシュ) ---
    sec_units = []
    all_units = []
    for sec in prob["sections"]:
        us = sec["units"]
        sec_units.append((sec, us))
        all_units.extend(us)
    htmls = [render_unit(u)[0] for u in all_units]
    widths = measure(htmls)
    for u, w in zip(all_units, widths):
        measure_cache[id_of(u)] = w
    print(f"計測完了: {len(all_units)} units")

    sheets = paginate(sec_units)

    # --- sheet HTML組み立て ---
    body = []
    notes = "".join(f"<li>{esc(n)}</li>" for n in meta.get("notes", []))
    body.append(f"""
<div class="sheet cover-sheet"><div class="cover">
  <div class="brand">TRILLION AI JUKU ── SOKKURI MOCK</div>
  <div class="h">{esc(meta["title"])}</div>
  <div class="sub">2026年共通テスト 完全類似形式 オリジナル問題 ── 問題編</div>
  <div class="meta">試験時間 {esc(meta["time"])} ／ {meta["max_points"]}点満点</div>
  <div class="notes"><div class="nt">注　意　事　項</div><ol>{notes}</ol></div>
  <div class="foot">本問題は2026年度大学入学共通テストの出題形式・難易度を忠実に再現したオリジナル問題です。実際の試験問題ではありません。</div>
</div></div>""")
    prev_sec = None
    pno = 0
    for sh in sheets:
        pno += 1
        sec = sh["sec"]
        band = ""
        if sec["no"] != prev_sec:
            band = (f'<div class="sec-band">第{sec["no"]}問{("　" + esc(sec["title"])) if sec.get("title") else ""}'
                    f'<span class="pts">（配点　{sec["points"]}）</span></div>')
            prev_sec = sec["no"]
        else:
            band = (f'<div class="sec-band" style="border-bottom-color:#bbb;color:#666;">'
                    f'（第{sec["no"]}問　つづき）</div>')
        body.append(f'<div class="sheet">{band}<div class="vbody">{"".join(sh["units"])}</div>'
                    f'<div class="pageno">― {pno} ―</div></div>')

    doc = (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
           f'<title>{esc(meta["title"])} 問題編</title><style>{CSS}</style></head>'
           f'<body>{"".join(body)}</body></html>')
    hp = os.path.join(HERE, html_name)
    with open(hp, "w") as f:
        f.write(doc)
    from common import chrome_pdf
    chrome_pdf(hp, out_pdf, budget=12000)
    print(f"sheets: {len(sheets) + 1}")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "kokugo")
