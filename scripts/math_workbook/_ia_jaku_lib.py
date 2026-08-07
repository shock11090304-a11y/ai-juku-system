# -*- coding: utf-8 -*-
"""数学I·A 弱点発見トレーニングの共通部品(スキル表・単元計画・KaTeX 実レンダリング)。

執筆コントラクトは `_IA_JAKU_CONTRACT.md`。
"""
import os, re, json, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
KATEX = "file://" + os.path.join(REPO, "vendor", "katex")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PARTS_DIR = os.path.join(HERE, "parts_ia_jaku")

# ---------------------------------------------------------------- スキル体系
SKILLS = {
 # 数と式
 'SK1': '展開の公式', 'SK2': '因数分解', 'SK3': '対称式・式の値',
 'SK4': '平方根の計算・有理化', 'SK5': '二重根号', 'SK6': '絶対値の処理(場合分け)',
 'SK7': '1次不等式・連立不等式',
 # 集合と命題
 'ST1': '集合の演算・ド・モルガン', 'ST2': '要素の個数(包除原理)', 'ST3': '命題の真偽・反例',
 'ST4': '必要条件・十分条件', 'ST5': '逆・裏・対偶', 'ST6': '背理法',
 # 2次関数
 'QF1': '平方完成', 'QF2': 'グラフの平行移動・対称移動', 'QF3': '最大最小(定義域固定)',
 'QF4': '最大最小(場合分け)', 'QF5': '判別式と実数解の個数', 'QF6': '2次方程式を解く・解と係数',
 'QF7': '2次不等式', 'QF8': '解の配置',
 # 図形と計量
 'TR1': '三角比の定義と値', 'TR2': '三角比の相互関係', 'TR3': '90°−θ・180°−θ の変換',
 'TR4': '正弦定理', 'TR5': '余弦定理', 'TR6': '三角形の面積・ヘロン',
 'TR7': '内接円・外接円の半径', 'TR8': '空間図形への応用',
 # データの分析
 'DA1': '代表値(平均・中央値・最頻値)', 'DA2': '四分位数・箱ひげ図・範囲', 'DA3': '分散・標準偏差',
 'DA4': '共分散・相関係数', 'DA5': '変量の変換', 'DA6': '仮説検定の考え方',
 # 場合の数と確率
 'CP1': '積の法則と和の法則', 'CP2': '順列P・階乗', 'CP3': '円順列・重複順列・同じものを含む順列',
 'CP4': '組合せC', 'CP5': '確率の定義', 'CP6': '余事象・和事象', 'CP7': '独立試行・反復試行',
 'CP8': '乗法定理・条件付き確率', 'CP9': '期待値',
 # 図形の性質
 'GE1': '角の二等分線と線分比', 'GE2': '三角形の五心', 'GE3': 'チェバ・メネラウス',
 'GE4': '円周角・円に内接する四角形', 'GE5': '方べきの定理・接線',
 # 数学と人間の活動(整数)
 'IN1': '約数の個数と総和', 'IN2': '最大公約数・最小公倍数', 'IN3': 'ユークリッド互除法',
 'IN4': '1次不定方程式', 'IN5': '余りによる分類・合同', 'IN6': 'n進法',
}

# つまずきの「根っこ」を辿るための前提グラフ(子 → 前提の list)
PREREQ = {
 'SK2': ['SK1'], 'SK3': ['SK1'], 'SK4': ['SK1'], 'SK5': ['SK4'], 'SK6': ['SK7'],
 'ST2': ['ST1'], 'ST4': ['ST3'], 'ST5': ['ST3'], 'ST6': ['ST5'],
 'QF2': ['QF1'], 'QF3': ['QF1'], 'QF4': ['QF3'], 'QF5': ['QF6'], 'QF6': ['SK2'],
 'QF7': ['QF5', 'QF6'], 'QF8': ['QF5', 'QF7'],
 'TR2': ['TR1'], 'TR3': ['TR1'], 'TR4': ['TR1'], 'TR5': ['TR1'],
 'TR6': ['TR1'], 'TR7': ['TR4', 'TR6'], 'TR8': ['TR5'],
 'DA2': ['DA1'], 'DA3': ['DA1'], 'DA4': ['DA3'], 'DA5': ['DA3'],
 # DA6(仮説検定)は根。新課程では数学Iで、反復試行(数学A)も代表値も前提にしない。
 'CP2': ['CP1'], 'CP3': ['CP2'], 'CP4': ['CP2'], 'CP5': ['CP1'], 'CP6': ['CP5'],
 'CP7': ['CP5', 'CP4'], 'CP8': ['CP5'], 'CP9': ['CP5'],
 'GE2': ['GE1'], 'GE3': ['GE1'], 'GE5': ['GE4'],
 'IN2': ['IN1'], 'IN3': ['IN2'], 'IN4': ['IN3'], 'IN6': ['IN5'],
 # IN5(余りによる分類)は根。除法の原理だけで足り、最大公約数を前提としない。
}

LEVELS = ("basic", "standard", "advanced")

# ---------------------------------------------------------------- 単元計画
# (コード, 単元名, 問数, 編) — 番号は A01〜A18。★接頭辞 A は必須:
#   第1集=01〜12 / 第2集=13〜27 / 化学=C01〜C18 と番号が衝突すると、
#   採点シートの写真から番号を回収したときにどの教材の×か判別できない。
PLAN = [
 ("A01", "展開と因数分解",             7, "第1編　数と式"),
 ("A02", "実数・平方根・式の値",       7, "第1編　数と式"),
 ("A03", "1次不等式と絶対値",          6, "第1編　数と式"),
 ("A04", "集合と要素の個数",           6, "第2編　集合と命題"),
 ("A05", "命題と条件・対偶・背理法", 8, "第2編　集合と命題"),
 ("A06", "2次関数のグラフ",            7, "第3編　2次関数"),
 ("A07", "2次関数の最大・最小",        7, "第3編　2次関数"),
 ("A08", "2次方程式と判別式",          7, "第3編　2次関数"),
 ("A09", "2次不等式と解の配置",        6, "第3編　2次関数"),
 ("A10", "三角比の基本と相互関係",     7, "第4編　図形と計量"),
 ("A11", "正弦定理・余弦定理",         7, "第4編　図形と計量"),
 ("A12", "三角形の面積と空間図形", 7, "第4編　図形と計量"),
 ("A13", "代表値・四分位数・標準偏差", 7, "第5編　データの分析"),
 ("A14", "相関係数と仮説検定の考え方", 5, "第5編　データの分析"),
 ("A15", "場合の数（順列・組合せ）",   7, "第6編　場合の数と確率"),
 ("A16", "確率の計算", 10, "第6編　場合の数と確率"),
 ("A17", "図形の性質", 9, "第7編　図形の性質"),
 ("A18", "整数の性質（数学と人間の活動）", 9, "第8編　数学と人間の活動"),
]
PLAN_BY_CODE = {c: (c, n, cnt, area) for c, n, cnt, area in PLAN}
AREAS = []
for _c, _n, _cnt, _a in PLAN:
    if _a not in AREAS:
        AREAS.append(_a)

MATH_RE = re.compile(r"\$([^$]+)\$")
# $...$ の中に日本語(CJK)が入ると KaTeX が斜体英字化・豆腐化する
CJK_RE = re.compile(r"[぀-ヿ㐀-鿿！-｠]")


def load_unit_module(code):
    """parts_ia_jaku/<code>.py をモジュールとして読む。"""
    import importlib
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    mod = importlib.import_module(f"parts_ia_jaku.{code}")
    return importlib.reload(mod)


def load_unit(code):
    """parts_ia_jaku/<code>.py の UNIT を読む。"""
    return load_unit_module(code).UNIT


def katex_check(exprs, tmp_tag="unit"):
    """数式リストを実際に KaTeX へ通し、失敗した (式, エラー) の list を返す。

    ★ソースを目で見るだけでは足りない: KaTeX が落ちた数式は描画されず
      生の LaTeX ソースのまま印刷される(PDF 生成自体は成功する)。
    """
    exprs = list(dict.fromkeys(exprs))
    if not exprs:
        return []
    html = f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="{KATEX}/katex.min.css">
<script src="{KATEX}/katex.min.js"></script></head>
<body><pre id="out" style="font-size:5pt;white-space:pre-wrap"></pre>
<script>
var tests = {json.dumps(exprs, ensure_ascii=False)};
var bad = [];
for (var i = 0; i < tests.length; i++) {{
  try {{ katex.renderToString(tests[i], {{throwOnError:true, strict:false}}); }}
  catch (e) {{ bad.push("###" + i + "@@@" + e.message.slice(0,90)); }}
}}
document.getElementById("out").textContent =
  "TOTAL " + tests.length + " BAD " + bad.length + "\\n" + bad.join("\\n");
document.title = "done";
</script></body></html>"""
    hp = os.path.join(HERE, f"_katex_{tmp_tag}.html")
    pp = os.path.join(HERE, f"_katex_{tmp_tag}.pdf")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=30000", f"--print-to-pdf={pp}", "file://" + hp],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import fitz
    txt = "".join(p.get_text() for p in fitz.open(pp))
    for p in (hp, pp):
        try:
            os.remove(p)
        except OSError:
            pass
    head = re.search(r"TOTAL (\d+) BAD (\d+)", txt)
    if not head:
        raise RuntimeError("KaTeX ゲートの出力を読めなかった")
    out = []
    if int(head.group(2)):
        for chunk in txt.replace("\n", " ").split("###")[1:]:
            m = re.match(r"\s*(\d+)\s*@@@\s*(.*)", chunk)
            if m:
                i = int(m.group(1))
                out.append((exprs[i] if i < len(exprs) else "?", m.group(2).strip()[:80]))
    return out


# ---------------------------------------------------------------- 図のラベルの実寸
# ★`Canvas.svg()` を w_mm 無しで呼ぶと、紙の寸法は CSS(`build_kiso.CSS`)の
#   `.fig svg{max-width:62mm; max-height:44mm}` が決める。つまり実効スケールは 44mm/H で、
#   **viewBox の縦を大きくするほど図もラベルも小さく印刷される**。
#   これを目で見て気づくのは無理で、実際に A17-8 が 6.40pt・A06 が 6.46pt(本文 9.7pt)の
#   まま出荷された。作った本人は「size は紙の大きさ」だと思っているので誰も疑わない。
#   → 図を1つ足すたびに機械が実寸を計算する。下限を割ったら単元検査で落とす。
_MM2PT = 72 / 25.4
_CHROME_PRINT_SCALE = 0.90685      # Chrome の print-to-pdf が文書全体にかける縮小(実測)
CSS_FIG_MAX_H_MM = 44.0            # build_kiso.CSS の .fig svg{max-height}
FIG_LABEL_MIN_PT = 8.0             # これを割ると紙で読めない(本文 9.7pt / 他の図 8.0〜11.3pt)
_VIEWBOX_RE = re.compile(r'viewBox="0 0 ([\d.]+) ([\d.]+)"')
_SVG_W_MM_RE = re.compile(r'<svg viewBox="[^"]*" width="([\d.]+)mm"')
_FONT_SIZE_RE = re.compile(r'font-size="([\d.]+)"')


def fig_label_pts(svg):
    """図(SVG文字列)が紙に出したときのラベルの大きさを pt で返す。
    戻り値: (幅mm, 高さmm, w_mm指定か, {font-size(user unit): pt})"""
    m = _VIEWBOX_RE.search(svg)
    if not m:
        return None
    W, H = float(m.group(1)), float(m.group(2))
    mw = _SVG_W_MM_RE.search(svg)
    fixed = bool(mw)
    w_mm = float(mw.group(1)) if fixed else W * (CSS_FIG_MAX_H_MM / H)
    scale = w_mm / W                                   # mm / user unit
    pts = {float(fs): float(fs) * scale * _MM2PT * _CHROME_PRINT_SCALE
           for fs in set(_FONT_SIZE_RE.findall(svg))}
    return w_mm, w_mm * H / W, fixed, pts


def unit_math(unit):
    """単元内の全 $...$ を (式, 出現場所) で返す。"""
    got = []
    for j, q in enumerate(unit["problems"], 1):
        for field in ("stem", "answer", "explanation"):
            for m in MATH_RE.finditer(q.get(field) or ""):
                got.append((m.group(1), f"{j}:{field}"))
    return got
