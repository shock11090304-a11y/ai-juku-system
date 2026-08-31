# -*- coding: utf-8 -*-
"""
英語 品詞分解トレーニング — 共通コア（DSL パーサ + HTML レンダラ + PDF 化）

■ 分解 DSL
  {LBL:text}   … 要素ラベル付きチャンク（LBL は ALLOWED_LABELS）
  ( ... )      … 副詞のカタマリ（前置詞句・副詞節・分詞構文）
  [ ... ]      … 名詞のカタマリ（名詞節・動名詞句・不定詞名詞用法）
  < ... >      … 形容詞のカタマリ（関係詞節・分詞の後置修飾・形容詞用法の前置詞句）
  [LBL: ... ]  … カタマリ全体に働きのラベルを付ける（( ) < > も同様）
  ラベルの付かない素の語（and / , / . など）はそのまま地の文として出る。

★単一ソース原則: 問題編に出す「英文そのもの」は、この DSL から機械的に復元する。
  よって問題編と解答編の英文がズレることは構造上あり得ない（check.py が長文本文とも照合）。
"""
import os, re, glob, html, shutil, subprocess, tempfile
# ★fitz(pymupdf) は render_pdf の中で import する。ここで読むと、PDF を1枚も開かない
#   内容ゲート(check.py)まで pymupdf 未導入の環境で ModuleNotFoundError で落ちる
#   （＝run_all_gates.py の CRASH＝FAIL）。判定に要るのは「PDFファイルが要るか」であって
#   「fitz が要るか」ではない（run_all_gates.needs_pdf のコメントと同じ考え方）。

HERE = os.path.dirname(os.path.abspath(__file__))
DESKTOP = os.path.expanduser("~/Desktop")
# ★刷るのは塾長の Mac（Chrome + Arial Unicode）。それが正典。
#   クラウド/CI で「中身を確かめるための PDF」を出せるように、見つからなければ
#   その環境にあるものへ落とす。env で明示指定もできる。
#   ただし**字形の照合は刷るフォント（Arial Unicode）の cmap を正典にする**こと。
#   その場にあるフォントで照合すると、Noto にあって Arial Unicode に無い字が
#   素通りして紙で豆腐になる（CLAUDE.md の「フォントは入れない」はこの意味）。
def _first_path(env, candidates):
    v = os.environ.get(env)
    if v and os.path.exists(v):
        return v
    for pat in candidates:
        for hit in sorted(glob.glob(pat)):
            if os.path.exists(hit):
                return hit
    return candidates[0]


CHROME = _first_path("CHROME_PATH", [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/opt/pw-browsers/chromium-*/chrome-linux/chrome",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
])
FONT_PATH = _first_path("PDF_STAMP_FONT", [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
])

esc = lambda s: html.escape(str(s), quote=False)
CIRCLE = ["①", "②", "③", "④", "⑤", "⑥"]

# 長い順に並べる（前方一致で食い合わないように）
ALLOWED_LABELS = [
    "S''", "V''", "O''", "C''", "M''", "O1''", "O2''",
    "S'", "V'", "O'", "C'", "M'", "O1'", "O2'",
    "O1", "O2", "真S", "真O", "同格", "挿入", "強調", "接", "助",
    "S", "V", "O", "C", "M",
]
LBL_RE = "|".join(re.escape(x) for x in ALLOWED_LABELS)
OPEN_LBL = re.compile(r'[\s]*(?:(' + LBL_RE + r')\s*:)?')

BR_PAIR = {"(": ")", "[": "]", "<": ">"}
BR_KIND = {"(": "adv", "[": "noun", "<": "adj"}
BR_JA = {"(": "副詞のカタマリ", "[": "名詞のカタマリ", "<": "形容詞のカタマリ"}

# ラベル → CSS クラス（'' や ' を落とした基底で色を決める）
def _lbl_cls(lbl):
    base = lbl.replace("''", "").replace("'", "")
    return {"S": "ls", "V": "lv", "O": "lo", "C": "lc", "M": "lm",
            "O1": "lo", "O2": "lo", "真S": "ls", "真O": "lo",
            "同格": "lx", "挿入": "lk", "強調": "lc",
            "接": "lk", "助": "lv"}.get(base, "lx")


# ---------------------------------------------------------------- parser
class Node:
    __slots__ = ("kind", "label", "text", "kids")

    def __init__(self, kind, label="", text="", kids=None):
        self.kind = kind          # 'chunk' | 'plain' | 'group'
        self.label = label
        self.text = text
        self.kids = kids or []


def parse(src):
    """DSL 文字列 → ノード列（木）。構文エラーは ValueError。"""
    i, n = 0, len(src)
    stack = [Node("group", "", "", [])]   # root
    while i < n:
        ch = src[i]
        if ch == "{":
            j = src.find("}", i)
            if j < 0:
                raise ValueError(f"'{{' が閉じていない: ...{src[i:i+30]}")
            inner = src[i + 1:j]
            if ":" not in inner:
                raise ValueError(f"ラベル区切り ':' が無い: {{{inner}}}")
            lbl, txt = inner.split(":", 1)
            lbl, txt = lbl.strip(), txt.strip()
            if lbl not in ALLOWED_LABELS:
                raise ValueError(f"未知のラベル: {lbl!r}")
            if not txt:
                raise ValueError(f"空チャンク: {{{inner}}}")
            stack[-1].kids.append(Node("chunk", lbl, txt))
            i = j + 1
        elif ch in BR_PAIR:
            m = OPEN_LBL.match(src, i + 1)
            lbl = m.group(1) or ""
            g = Node("group", lbl, ch, [])
            stack[-1].kids.append(g)
            stack.append(g)
            i = m.end()
        elif ch == "}":
            # 孤立した '}' を地の文として走査すると i が進まず無限ループになる
            raise ValueError(f"対応しない '}}': ...{src[max(0, i - 20):i + 20]}")
        elif ch in (")", "]", ">"):
            if len(stack) == 1:
                raise ValueError(f"対応しない閉じ括弧 {ch!r}")
            g = stack.pop()
            if BR_PAIR[g.text] != ch:
                raise ValueError(f"括弧の対応が不正: {g.text!r} を {ch!r} で閉じた")
            i += 1
        else:
            j = i
            while j < n and src[j] not in "{}()[]<>":
                j += 1
            txt = src[i:j].strip()
            if txt:
                stack[-1].kids.append(Node("plain", "", txt))
            i = j
    if len(stack) != 1:
        raise ValueError(f"閉じ忘れの括弧 {stack[-1].text!r}")
    return stack[0]


_SP_BEFORE_PUNCT = re.compile(r'\s+([,.;:?!%])')
_SP_AFTER_OPEN = re.compile(r'\s+’')


def normalize(s):
    s = re.sub(r'\s+', ' ', str(s)).strip()
    s = _SP_BEFORE_PUNCT.sub(r'\1', s)
    return s


def plain_text(node):
    """DSL から英文そのものを復元する。"""
    out = []

    def walk(nd):
        for k in nd.kids:
            if k.kind in ("chunk", "plain"):
                out.append(k.text)
            else:
                walk(k)
    walk(node)
    return normalize(" ".join(out))


def iter_nodes(node):
    for k in node.kids:
        yield k
        if k.kind == "group":
            yield from iter_nodes(k)


# ---------------------------------------------------------------- renderer
_PUNC_ONLY = re.compile(r'^[,.;:?!]+$')


def _cell(word, label, wcls="", lcls=""):
    """語の行とラベルの行を 2 段に積んだ 1 マス。全要素をこの形にそろえて行を揃える。"""
    return (f'<span class="ck"><span class="wt {wcls}">{word}</span>'
            f'<span class="lb {lcls}">{label}</span></span>')


def render_analysis(node):
    """解答編用: 色分け＋ラベル付きの分解図 HTML。"""
    def walk(nd):
        buf = []
        for k in nd.kids:
            if k.kind == "chunk":
                buf.append(_cell(esc(k.text), esc(k.label), lcls=_lbl_cls(k.label)))
            elif k.kind == "plain":
                cls = "pl punc" if _PUNC_ONLY.match(k.text) else "pl"
                buf.append(_cell(esc(k.text), "&nbsp;", wcls=cls))
            else:
                kind = BR_KIND[k.text]
                buf.append(_cell(esc(k.text), "&nbsp;", wcls=f'br b-{kind}'))
                buf.append(walk(k))
                buf.append(_cell(esc(BR_PAIR[k.text]),
                                 esc(k.label) if k.label else "&nbsp;",
                                 wcls=f'br b-{kind}', lcls=_lbl_cls(k.label)))
        return "".join(buf)
    return f'<div class="bunkai">{walk(node)}</div>'


CORE_LBL = ("S", "V", "O", "C", "O1", "O2", "助", "真S", "真O")
# ★接続詞・相関語・セミコロンを落とすと not A but B / neither A nor B が骨組みで意味反転するため必ず残す
KEEP_PLAIN = {";", "neither", "not", "either"}


def render_skeleton(node):
    """解答編用: カタマリを外した『骨組み』（主節の S V O C ＋ 節をつなぐ語を 1 行に並べる）。"""
    out = []
    for k in node.kids:
        if k.kind == "chunk" and k.label == "接":
            out.append(f'<span class="sk lk">{esc(k.text)}</span>')
            continue
        if k.kind == "plain" and k.text.strip(" ,") in KEEP_PLAIN:
            out.append(f'<span class="sk lk">{esc(k.text.strip(" ,"))}</span>')
            continue
        if k.label not in CORE_LBL:
            continue
        if k.kind == "chunk":
            txt = k.text
        elif k.kind == "group":
            txt = plain_text(k)
            if len(txt) > 34:
                txt = txt[:32].rstrip() + "…"
        else:
            continue
        out.append(f'<span class="sk {_lbl_cls(k.label)}">{esc(txt)}'
                   f'<sub>{esc(k.label)}</sub></span>')
    return " ".join(out)


def render_blank(node, lh="3.05"):
    """問題編用: 書き込み用に行間を大きく取った素の英文。"""
    return (f'<div class="wsent" style="line-height:{lh}">'
            f'{esc(plain_text(node))}</div>')


# ---------------------------------------------------------------- CSS
BASE_CSS = """
* { box-sizing: border-box; }
@page { size: A4; margin: 14mm 13mm 16mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family:"Hiragino Mincho ProN","Yu Mincho",serif; color:#1a1a1a; font-size:10.3pt;
  line-height:1.62; margin:0; font-variant-numeric: lining-nums; font-feature-settings:"lnum" 1; }
.gothic, h1,h2,h3,.band,.qno,.secttl,.partttl,.tier,.foot,.plabel,.vhd,.lb,.glb,.sk sub,.stepno
  { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }
.en { font-family:Georgia,"Times New Roman",serif; font-variant-numeric: lining-nums;
  font-feature-settings:"lnum" 1; }
.enj { font-family:"Hiragino Mincho ProN","Yu Mincho",serif; }

/* ---- header band ---- */
.band { background:linear-gradient(90deg,#0f172a,#1e3a8a); color:#fff; padding:10px 15px;
  border-radius:9px; display:flex; justify-content:space-between; align-items:center; }
.band .l { font-size:15pt; font-weight:700; letter-spacing:.02em; }
.band .l small { display:block; font-weight:600; font-size:9.3pt; opacity:.92; margin-top:2px; }
.band .r { text-align:right; font-size:9pt; line-height:1.45; white-space:nowrap; padding-left:14px; }
.band .r b { font-size:12.5pt; }
.intro { border:1px solid #cbd5e1; border-radius:8px; padding:9px 13px; margin:9px 0 4px;
  font-size:9.5pt; line-height:1.72; color:#334155; }
.intro b { color:#0f172a; }
.metarow { display:flex; gap:10px; margin:9px 0 6px; font-size:9.4pt; }
.metarow .cell { border:1px solid #cbd5e1; border-radius:6px; padding:4px 10px; flex:1; }
.metarow .cell.score { flex:0 0 150px; text-align:center; }

/* ---- 記号ルール（巻頭） ---- */
.rulegrid { display:flex; flex-wrap:wrap; gap:7px; margin:7px 0 4px; }
.rulecard { flex:1 1 47%; border:1px solid #dbe3ef; border-radius:7px; padding:6px 11px;
  page-break-inside:avoid; }
.rulecard .rh { font-weight:700; font-size:10.4pt; margin-bottom:2px;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.rulecard .rb { font-size:9.2pt; color:#334155; line-height:1.6; }
.rulecard .rex { font-family:Georgia,serif; font-size:9.6pt; margin-top:3px; color:#0f172a; }
.rc-adv .rh { color:#64748b; } .rc-noun .rh { color:#047857; } .rc-adj .rh { color:#7c3aed; }
.rc-svoc .rh { color:#1e3a8a; }
.steps { counter-reset:st; margin:6px 0 2px; }
.step { display:flex; gap:8px; align-items:flex-start; margin:3px 0; font-size:9.5pt; }
.stepno { flex:0 0 auto; background:#1e3a8a; color:#fff; border-radius:5px; padding:0 8px;
  font-size:8.6pt; font-weight:700; }

/* ---- section / part ---- */
.partdiv { background:#1e3a8a; color:#fff; border-radius:8px; padding:12px 16px; margin:16px 0 4px;
  page-break-before:always; page-break-after:avoid; }
.partdiv.first { page-break-before:auto; margin-top:10px; }
.partdiv .pt1 { font-size:15.5pt; font-weight:700; }
.partdiv .pt2 { font-size:9.4pt; opacity:.93; margin-top:3px; }
.sess { page-break-before:always; }
.sess.first { page-break-before:auto; }
.secttl { font-size:13pt; font-weight:700; color:#0f172a; border-left:6px solid #1e3a8a;
  padding:3px 0 3px 10px; margin:4px 0 8px; page-break-after:avoid; }
.secttl .en2 { font-size:8.8pt; color:#64748b; font-weight:600; margin-left:8px; }
.partttl { font-size:11.3pt; font-weight:700; color:#fff; background:#1e3a8a; border-radius:6px;
  padding:3px 12px; margin:10px 0 6px; page-break-after:avoid; }
.partttl .en2 { font-size:8.2pt; opacity:.9; margin-left:7px; font-weight:600; }
.instr { font-size:9.2pt; background:#f1f5f9; border-left:4px solid #1e3a8a; padding:6px 10px;
  border-radius:4px; margin:6px 0 9px; color:#334155; line-height:1.6; page-break-after:avoid; }
.tglue { break-inside:avoid; page-break-inside:avoid; }
.pb { page-break-before:always; }

/* ---- passage ---- */
.ptitle { text-align:center; font-size:12.5pt; font-weight:700; margin:8px 0 1px;
  font-family:Georgia,serif; }
.pjtitle { text-align:center; font-size:8.7pt; color:#64748b; margin-bottom:6px; }
.passage { border:1.2px solid #94a3b8; border-radius:8px; padding:10px 15px; }
.passage p { margin:0 0 6px; font-family:Georgia,serif; line-height:1.9; text-align:justify;
  font-size:10.3pt; font-variant-numeric: lining-nums; }
.passage .mk { border-bottom:1.3px solid #1f2937; }
.passage sup.sn { color:#dc2626; font-weight:700; font-size:7.6pt;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin-right:1px; }
.wcount { text-align:right; color:#64748b; font-size:8.5pt; margin-top:2px; }
.vhd { font-size:9.8pt; font-weight:700; color:#0f172a; margin:9px 0 3px; page-break-after:avoid; }
table.vocab { width:100%; border-collapse:collapse; font-size:8.5pt; page-break-inside:avoid; }
table.vocab td { border:1px solid #cbd5e1; padding:2px 8px; vertical-align:top; }
table.vocab td.w { font-family:Georgia,serif; font-weight:700; white-space:nowrap; color:#0f172a; }

/* ---- 問題編: 書き込み用の英文 ---- */
.wq { margin:0 0 8px; page-break-inside:avoid; }
.wqh { display:flex; align-items:baseline; gap:8px; margin-bottom:1px; }
.qno { background:#0f172a; color:#fff; border-radius:5px; padding:1px 9px; font-size:9pt;
  font-weight:700; white-space:nowrap; }
.wsent { font-family:Georgia,serif; font-size:11.2pt; margin:2px 0 9px; color:#111;
  font-variant-numeric: lining-nums; }
.slots { display:flex; gap:9px; font-size:9pt; color:#334155; margin-top:1px; }
.slots .sl { border:1px solid #cbd5e1; border-radius:5px; padding:2px 9px; }
.slots .sl.wide { flex:1; }
.jline { border-bottom:1px solid #cbd5e1; height:19px; margin:0; }

/* ---- 分解図（解答編） ---- */
.bunkai { font-family:Georgia,serif; font-size:10.6pt; line-height:1.35; margin:3px 0 4px;
  padding:7px 9px 4px; background:#fbfcfe; border:1px solid #e2e8f0; border-radius:7px;
  font-variant-numeric: lining-nums; }
.ck { display:inline-block; text-align:center; vertical-align:bottom; margin:0 1.2px 2px; }
.ck .wt { display:block; white-space:nowrap; }
.ck .wt.pl { color:#334155; }
.ck .wt.punc { margin-left:-3px; }
.ck .wt.br { font-weight:700; }
.ck .lb { display:block; font-size:6.9pt; font-weight:700; line-height:1.2; letter-spacing:.02em; }
.b-adv { color:#64748b; } .b-noun { color:#047857; } .b-adj { color:#7c3aed; }
.lb.ls, .glb.ls, .sk.ls { color:#1d4ed8; }
.lb.lv, .glb.lv, .sk.lv { color:#dc2626; }
.lb.lo, .glb.lo, .sk.lo { color:#047857; }
.lb.lc, .glb.lc, .sk.lc { color:#b45309; }
.lb.lm, .glb.lm { color:#64748b; }
.lb.lk, .glb.lk { color:#9333ea; }
.lb.lx, .glb.lx { color:#0f766e; }
.gp { display:inline; }
.gp .br { font-weight:700; padding:0 1px; }
.g-adv > .br { color:#64748b; }
.g-noun > .br { color:#047857; }
.g-adj > .br { color:#7c3aed; }
.glb { font-size:6.9pt; font-weight:700; vertical-align:sub; margin-left:1px; }
.skel { font-family:Georgia,serif; font-size:10pt; margin:2px 0 4px; color:#0f172a; }
.skel .lead { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:8.6pt; color:#64748b;
  margin-right:7px; }
.sk { margin-right:11px; font-weight:700; }
.sk sub { font-size:7pt; margin-left:1px; }

/* ---- 解説 ---- */
.acard { border:1px solid #e2e8f0; border-left:4px solid #1e3a8a; border-radius:7px;
  padding:7px 11px; margin:7px 0 10px; page-break-inside:avoid; }
.acard .ah { display:flex; align-items:baseline; gap:9px; flex-wrap:wrap; margin-bottom:3px; }
.acard .ano { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; color:#fff;
  background:#0f172a; border-radius:5px; padding:1px 9px; font-size:9pt; white-space:nowrap; }
.acard .apat { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; color:#1e3a8a;
  font-size:9.6pt; }
.acard .atag { display:inline-block; background:#fde68a; color:#7c2d12; font-weight:700;
  border-radius:4px; padding:0 7px; font-size:8.2pt;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.notes { font-size:9.3pt; color:#1f2937; line-height:1.66; margin:3px 0 0; }
.notes li { margin:1.5px 0; }
.notes ul { margin:2px 0 0; padding-left:17px; }
.notes b { color:#0f172a; }
.notes .en { font-family:Georgia,serif; }
.jatr { font-size:9.4pt; color:#334155; background:#f8fafc; border-radius:5px; padding:4px 9px;
  margin-top:4px; }
.jatr b { color:#0f172a; font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:8.6pt;
  margin-right:6px; }
.legend { display:flex; flex-wrap:wrap; gap:6px 14px; font-size:8.6pt; color:#475569;
  border:1px dashed #cbd5e1; border-radius:6px; padding:5px 10px; margin:4px 0 9px; }
.legend b { font-weight:700; }

/* ---- 4択・和訳 ---- */
.q { margin:0 0 7px; page-break-inside:avoid; }
.q .stem { margin:2px 0 2px; font-size:9.8pt; }
.q .stem .en { font-family:Georgia,serif; }
.q .choices div { margin:2px 0 1px 10px; font-size:9.7pt; }
.q .choices .en { font-family:Georgia,serif; }
table.ans { width:100%; border-collapse:collapse; font-size:9.1pt; margin:2px 0 8px; }
table.ans th, table.ans td { border:1px solid #cbd5e1; padding:4px 6px; text-align:center; }
table.ans th { background:#eef2ff; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
table.ans td.a { font-weight:700; color:#1e3a8a; }
.foot { text-align:center; color:#64748b; font-size:8.2pt; margin-top:12px; padding-top:5px;
  border-top:1px solid #e2e8f0; page-break-inside:avoid; }
"""


# ---------------------------------------------------------------- output
def doc(title, body):
    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<title>{esc(title)}</title><style>{BASE_CSS}</style></head><body>{body}</body></html>')


def render_pdf(body, out_path, foot_label):
    # ★中間 HTML は使い捨てのディレクトリに置く。以前は HERE（＝この共有コアのある
    #   eng_hinshi_bunkai/）に書いていたので、**別の教材を刷ると隣の教材のフォルダが汚れた**。
    tmpdir = tempfile.mkdtemp(prefix="pdfsrc-")
    tmp = os.path.join(tmpdir, os.path.basename(out_path).replace(".pdf", ".html"))
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(doc(foot_label, body))
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
           "--virtual-time-budget=15000", f"--print-to-pdf={out_path}", "file://" + tmp]
    # root で動く Linux コンテナ（CI・クラウド）では sandbox を切らないと起動しない。
    # Mac では root で動かさないので、この分岐は塾長の環境の挙動を変えない。
    if os.name == "posix" and hasattr(os, "geteuid") and os.geteuid() == 0:
        cmd.insert(1, "--no-sandbox")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(tmpdir, ignore_errors=True)
    import fitz
    d = fitz.open(out_path)
    font = fitz.Font(fontfile=FONT_PATH)
    for i, page in enumerate(d):
        n = str(i + 1)
        tw = font.text_length(n, fontsize=9)
        page.insert_text((page.rect.width / 2 - tw / 2, page.rect.height - 20), n,
                         fontfile=FONT_PATH, fontname="AU", fontsize=9, color=(0.45, 0.45, 0.45))
        page.insert_text((40, page.rect.height - 20), foot_label,
                         fontfile=FONT_PATH, fontname="AU", fontsize=7.5, color=(0.55, 0.55, 0.55))
    d.subset_fonts()
    tmp2 = out_path + ".tmp"
    d.save(tmp2, garbage=4, deflate=True, clean=True)
    d.close()
    os.replace(tmp2, out_path)
    d = fitz.open(out_path)
    pc = d.page_count
    d.close()
    print(f"WROTE {out_path} | pages: {pc}")
    return pc
