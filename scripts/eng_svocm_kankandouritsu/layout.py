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


def install_css(extra):
    """この教材ぶんの CSS を、**実際に刷る側**のスタイルシートに継ぎ足す。

    ★`layout.BASE_CSS = layout.BASE_CSS + EXTRA_CSS` と書いてはいけない。
      それは layout モジュールの名前を束ね直すだけで、組版する doc() が読むのは
      共有コア側の BASE_CSS なので、**追加 CSS が 1 文字も紙に届かない**。
      実際にこれで第1部の解答欄が罫線の無い素のテキストで刷られていた
      （check.py は本文の文字列しか見ないので緑のままだった）。
    """
    if extra not in _shared.BASE_CSS:
        _shared.BASE_CSS = _shared.BASE_CSS + extra
    return _shared.BASE_CSS


def stylesheet():
    """いま刷りに使われるスタイルシート（検査用）。"""
    return _shared.BASE_CSS


def document(body, title):
    """刷るときと同じ組み立ての HTML 全体（検査用）。"""
    return _shared.doc(title, body)


# ------------------------------------------------------------------ 構文カテゴリ
# ★重複の検出を tag（自由文）で行うと、書き換えるだけでゲートをすり抜けられる。
#   「同じ構文を何問出したか」は決まった語彙で数える。解答編の巻末に一覧としても刷る。
SYN_VOCAB = {
    # 文型そのもの
    "sv": "第1文型",
    "svc-adj": "第2文型（補語が形容詞）",
    "svc-noun": "第2文型（補語が名詞）",
    "svo": "第3文型",
    "svoo-give": "第4文型（授与型）",
    "svoo-take": "第4文型（与えるのではなく省く・奪う型）",
    "svoc-adj": "第5文型（補語が形容詞）",
    "svoc-noun": "第5文型（補語が名詞）",
    "svoc-bare": "第5文型（補語が原形不定詞）",
    "svoc-to": "第5文型（補語が to 不定詞）",
    "svoc-pp": "第5文型（補語が過去分詞）",
    # 修飾
    "pp-postmod": "名詞に付く前置詞句",
    "participle-postmod": "分詞の後置修飾",
    "long-fronted-pp": "文頭の長い前置詞句",
    "adverb-intrusion": "S と V の間に割り込む副詞",
    # 関係詞
    "relative-subject": "主格の関係代名詞",
    "relative-object": "目的格の関係代名詞",
    "relative-possessive": "所有格の関係代名詞 whose",
    "relative-adverb": "関係副詞",
    "prep-relative": "前置詞 + 関係代名詞",
    "what-clause": "関係代名詞 what",
    "chain-relative": "連鎖関係代名詞",
    "nonrestrictive": "非制限用法",
    "compound-relative": "複合関係詞",
    # 名詞のカタマリ
    "that-clause-object": "接続詞 that 節が目的語",
    "appositive-that": "同格の that 節",
    "whether-clause": "whether 節",
    "gerund-object": "動名詞句が目的語",
    "infinitive-noun": "不定詞の名詞用法",
    "infinitive-adjective": "不定詞の形容詞用法",
    "formal-subject": "形式主語",
    "formal-object": "形式目的語",
    "there-construction": "there 構文",
    # 比較
    "comparative-postmod": "比較の句が名詞を後ろから修飾",
    "not-so-much-as": "not so much A as B",
    "no-more-than": "no more / no less ... than",
    "the-more-the-more": "the 比較級, the 比較級",
    "comparative-ellipsis": "比較の節内の省略",
    "that-of": "比較の代用 that of / those of",
    "superlative-equivalent": "最上級相当",
    # 倒置・強調
    "negative-inversion": "否定の副詞句が文頭に出る倒置",
    "only-inversion": "Only ... の倒置",
    "cleft": "強調構文 It is ... that",
    "do-emphasis": "強調の do",
    "so-that-result": "so / such ... that の結果構文",
    "too-to": "too ... to / enough to",
    # 分詞構文・準動詞
    "participial-construction": "分詞構文",
    "with-absolute": "付帯状況の with",
    "independent-participle": "独立分詞構文",
    # そのほか
    "inanimate-subject": "無生物主語",
    "nominalization": "名詞構文",
    "concessive-as": "譲歩の as",
    "correlative": "相関接続詞による共通関係",
    "subjunctive": "仮定法",
    "subjunctive-inversion": "if の省略による倒置",
    "insertion": "挿入",
    "passive": "受動態",
    "group-verb": "群動詞",
    "causative": "使役動詞",
    "perception-verb": "知覚動詞",
    "ellipsis-clause": "従属節内の省略",
}

# 文型そのものを指すカテゴリ。第1部Ａは「5文型を繰り返し引く」のが目的なので、
# ここだけは同じカテゴリが複数回出てよい（★逆に言うと、他の部で文型カテゴリは使わせない）。
PATTERN_SYN = {"sv", "svc-adj", "svc-noun", "svo", "svoo-give", "svoo-take",
               "svoc-adj", "svoc-noun", "svoc-bare", "svoc-to", "svoc-pp"}

# ★構文の割り当て表（SYN_POOL）は content.py にある。
#   「この教材が何を教えるか」は**編集の決めごと**であってコードではないので、原稿と同じ
#   ファイルに置く。ここ（共通コード）に置くと、原稿がまだ骨格しか無い段階でも 60 問ぶんの
#   設計を宣言したことになり、「宣言と中身が食い違ったままコミットされる」状態ができる。


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

/* ---- 記号の書き方（表記規約） ---- */
table.notation { width:100%; border-collapse:collapse; font-size:9pt; margin:4px 0 8px;
  page-break-inside:avoid; }
table.notation td { border:1px solid #dbe3ef; padding:4px 9px; vertical-align:top;
  line-height:1.6; }
/* ★索引は 57 行あって 1 ページに収まらない。table.notation の page-break-inside:avoid が
   効いたままだと、表が丸ごと次ページへ送られて**見出しだけのページ**ができる（実測）。
   行単位で切れるようにする。 */
table.synindex { page-break-inside:auto; }
table.synindex tr { page-break-inside:avoid; }
table.notation td.nk { width:118px; font-weight:700; color:#1e3a8a; background:#f8fafc;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:8.8pt; white-space:nowrap; }
table.notation td.nb { color:#334155; }
table.notation td.ne { width:210px; font-family:Georgia,serif; color:#0f172a; font-size:9pt;
  background:#fbfcfe; }
"""
