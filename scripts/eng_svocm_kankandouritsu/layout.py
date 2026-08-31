# -*- coding: utf-8 -*-
"""英文解釈 × SVOCM 判別（関関同立レベル）— レイアウト層

★分解 DSL のパーサ・レンダラは `scripts/eng_hinshi_bunkai/core.py` を**そのまま使う**。
  ここで書き写すと、片方だけ直されて記号の意味がずれる（同じ塾で 2 種類の記号体系ができる）。
  この教材が足すのは「主節の要素を ①②③ に切り出して答えさせる」層だけ。
  ★このファイル名を `core.py` にしてはいけない。共有側と同名になり `import core` が自分に
    当たって循環 import で落ちる（実際に踏んだ）。

■ この教材だけの追加ルール（第1部 SVOCM 判別）
  判別問題の ①②③… は **DSL のトップレベル要素から機械的に切り出す**。
  だから「問題に印字された区切り」と「解答の記号」がずれることは構造上あり得ない。
  トップレベルには必ずラベルを付ける（句読点だけの地の文は直前の要素に吸収される）。
"""
import importlib.util
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.normpath(os.path.join(HERE, "..", "eng_hinshi_bunkai", "core.py"))

# ★sys.path に隣のディレクトリを足してはいけない。あちらにも content.py があるので、
#   `import content` が**隣の教材の原稿**に当たる（実際に踏んだ）。
#   ファイルパスを名指しして、専用の名前で読み込む。
_spec = importlib.util.spec_from_file_location("_hinshi_core", SHARED)
_shared = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_shared)

ALLOWED_LABELS = _shared.ALLOWED_LABELS
BASE_CSS = _shared.BASE_CSS
CIRCLE = _shared.CIRCLE
DESKTOP = _shared.DESKTOP
Node = _shared.Node
esc = _shared.esc
iter_nodes = _shared.iter_nodes
normalize = _shared.normalize
parse = _shared.parse
plain_text = _shared.plain_text
render_analysis = _shared.render_analysis
render_blank = _shared.render_blank
render_pdf = _shared.render_pdf
render_skeleton = _shared.render_skeleton

# 第1部の解答に使ってよいラベル（生徒が答案に書くのはこの範囲だけ）
DRILL_LABELS = ["S", "V", "O", "O1", "O2", "C", "M", "真S", "真O"]

# 文型 → 主節に並ぶべきラベルの集合（M と 真S/真O は骨格に数えない）
PATTERN_CORE = {
    "第1文型": ("S", "V"),
    "第2文型": ("S", "V", "C"),
    "第3文型": ("S", "V", "O"),
    "第4文型": ("S", "V", "O1", "O2"),
    "第5文型": ("S", "V", "O", "C"),
}

_PUNCT_ONLY = re.compile(r"^[,.;:?!—-]+$")


def top_segments(root):
    """トップレベルのノードを『判別問題の ①②③…』に切り出す。

    返り値: [(label, text, unlabeled_plain)] の並び。
      - 句読点だけの地の文は**直前の要素の末尾に吸収**する（`,` を独立した番号にしない）。
      - ラベルの無い地の文が残ったら unlabeled_plain=True で返す。lint / check が落とす。
    """
    segs = []
    for k in root.kids:
        if k.kind == "plain" and _PUNCT_ONLY.match(k.text):
            if segs:
                segs[-1][1] = normalize(segs[-1][1] + " " + k.text)
            else:
                segs.append(["", k.text, True])
            continue
        text = k.text if k.kind in ("chunk", "plain") else plain_text(k)
        if k.kind == "plain":
            segs.append(["", text, True])
        else:
            segs.append([k.label, text, False])
    return [tuple(s) for s in segs]


def infer_pattern(labels):
    """主節ラベルの並びから文型名を推定する（推定できなければ None）。

    形式主語・形式目的語は 真S / 真O が骨格の S / O を兼ねるものとして数える。
    """
    core = [x for x in labels if x in ("S", "V", "O", "O1", "O2", "C", "真S", "真O")]
    has = set(core)
    if "真S" in has:
        has.add("S")
    if "真O" in has:
        has.add("O")
    has.discard("真S")
    has.discard("真O")
    for name, need in PATTERN_CORE.items():
        if has == set(need):
            return name
    return None


# ------------------------------------------------------------------ 追加 CSS
EXTRA_CSS = """
/* ---- 第1部 判別ドリル ---- */
.dq { margin:0 0 9px; page-break-inside:avoid; }
.dsent { font-family:Georgia,serif; font-size:11pt; line-height:2.05; margin:1px 0 3px;
  color:#111; font-variant-numeric: lining-nums; }
.dsent .seg { white-space:normal; }
.dsent .mk2 { color:#dc2626; font-weight:700; font-size:8.6pt; vertical-align:.32em;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin-right:1px; }
table.slotbox { border-collapse:collapse; font-size:9pt; margin:1px 0 0; }
table.slotbox td, table.slotbox th { border:1px solid #cbd5e1; padding:2px 0; text-align:center;
  min-width:34px; }
table.slotbox th { background:#eef2ff; font-family:"Hiragino Kaku Gothic ProN",sans-serif;
  font-weight:700; color:#1e3a8a; font-size:8.4pt; }
table.slotbox td { height:20px; }
table.slotbox td.a { font-weight:700; color:#1e3a8a; font-size:9.6pt;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
table.slotbox th.lead, table.slotbox td.lead { background:#f8fafc; min-width:52px;
  font-size:8.2pt; color:#475569; }
.patbox { display:inline-block; border:1px solid #cbd5e1; border-radius:5px; padding:1px 9px;
  font-size:9pt; color:#334155; margin-left:9px; }
.grpttl { font-size:10.6pt; font-weight:700; color:#0f172a; background:#eef2ff;
  border-left:5px solid #1e3a8a; border-radius:4px; padding:3px 10px; margin:11px 0 6px;
  page-break-after:avoid; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.grpttl .sub { font-weight:600; font-size:8.6pt; color:#475569; margin-left:9px; }
.hint { font-size:8.8pt; color:#64748b; margin:1px 0 0 2px; }
.uni { display:inline-block; background:#dbeafe; color:#1e3a8a; border-radius:4px;
  padding:0 7px; font-size:8.2pt; font-weight:700; margin-left:7px;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.jline2 { border-bottom:1px solid #cbd5e1; height:20px; margin:0; }
.pts { font-size:9pt; color:#334155; }
"""
