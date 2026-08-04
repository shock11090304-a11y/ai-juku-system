# -*- coding: utf-8 -*-
r"""math1a_b.py: 2026共通テスト 数学Ⅰ・A そっくり類似問題 — 第3問(配点20)・第4問(配点20)

第3問 図形の性質(数学A)
  二等辺三角形 ABC(AB=AC=10, BC=12)。内心 I，△IBC の重心 G，G を通り底面に垂直な
  直線上の点 P で三角錐 PABC を作る。直線 AI と BC の交点 D，辺 PA 上に ∠PED=∠PID の E。
  (1) 内心=角の二等分線の性質(ア=②)→角の二等分線定理で AI=5(イ), ID=3(ウ)
      → E,I,D,P 共円(エ=④=P)→方べき AE·AP=AI·AD=40(オカ)
  (2) 線分PIとDEの交点F。仮定1 IF:FP=3:2 → PE:EA=1:4(キ,ク), AP=5√2(ケ√コ), V₁=16(サシ)
                        仮定2 IF:FP=3:5 → V₂:V₁=4:1(ス,セ) → ソ=②(V₂はV₁より大きい)
  平面図(参考図)・空間図はモジュール内で幾何的に正確な座標から SVG 生成。

第4問 場合の数・確率(数学A)
  卓球サークルのリーグ戦(総当たり・引き分けなし)。A の勝率は 1/3(実力で劣る挑戦者),
  A 以外どうしは 1/2。勝ち数最多が1人ならその人が優勝，同数なら抽選(n人なら各 1/n)。
  A が優勝する確率を 3人版と 4人版で比較する。
  ルール明示の角丸枠(優勝者の決め方)+星取表を4形態(例=表1/巴タイ=表2/部分=表3,表4/再掲)で提示。
  (1) 3人: (i) A2勝0敗 1/9(ア/イ)  (ii) 巴 1/9(ウ/エ)×抽選1/3(オ/カ)→A1勝1敗優勝 2/27(キ/クケ)
  (2) 4人: 全敗者あり→(1)(ii)を部品に 1/54(シ/スセ) / 全敗者なし→残り試合の場合の数 4通り(ソ)
           → 1/18(タ/チ) / A優勝 1/9(ツ/テ) / 3人版との差 2/27(ト/ナニ)だけ小さい(ヌ=⓪)
  確率はすべて厳密分数。全ケースを 2^3・2^6 通り全数列挙で機械検算(verify_math1a_b.py)。

検証: content/verify_math1a_b.py (sympy 座標計算 / 全数列挙で全スロット独立導出)
"""

# =========================================================================
#  第3問 図形の性質: SVG 生成(平面図・空間図を正確な座標で)
# =========================================================================

def _plane_svg():
    """(1)の平面図: 二等辺三角形 ABC + 内心 I・重心 G・D・E・F の平面配置。
    実座標(AD を軸=横向き)を紙面座標へ写像して描画する。"""
    # 数学座標: A=(0,0), D=(8,0), B=(8,6), C=(8,-6), I=(5,0), G=(7,0)
    # E は AP 上だが平面図では AB 上の対応点として概念的に置く(参考図)。
    # 描画は数学座標(x右, y上)→紙面(px)へ: scale 18, 原点オフセット。
    sc = 17.0
    ox, oy = 30, 120     # 数学(0,0)→紙面(ox,oy)
    def px(x, y):
        return (ox + x * sc, oy - y * sc)
    A = (0, 0); D = (8, 0); B = (8, 6); C = (8, -6); I = (5, 0); G = (7, 0)
    # E: AB 上の点(平面図では AB を PA に見立て、AE:AB を概念配置)
    E = (8 * 0.36, 6 * 0.36)
    W, H = 250, 240
    s = [f"<svg viewBox='0 0 {W} {H}' width='260' xmlns='http://www.w3.org/2000/svg'>",
         "<g font-family='Helvetica Neue,Arial,sans-serif' font-size='12' fill='#333'>"]
    ax, ay = px(*A); bx, by = px(*B); cx, cy = px(*C)
    dx, dy = px(*D); ix, iy = px(*I); gx, gy = px(*G); ex, ey = px(*E)
    # 三角形 ABC
    s.append(f"<path d='M{ax:.1f} {ay:.1f} L{bx:.1f} {by:.1f} L{cx:.1f} {cy:.1f} Z' "
             f"fill='none' stroke='#333' stroke-width='1.3'/>")
    # AD(A から BC への軸)= 中線・角の二等分線
    s.append(f"<line x1='{ax:.1f}' y1='{ay:.1f}' x2='{dx:.1f}' y2='{dy:.1f}' stroke='#333' stroke-width='1'/>")
    # BI(内心へ・∠B の二等分線)を破線で
    s.append(f"<line x1='{bx:.1f}' y1='{by:.1f}' x2='{ix:.1f}' y2='{iy:.1f}' stroke='#333' stroke-width='0.8' stroke-dasharray='3 2'/>")
    s.append(f"<line x1='{cx:.1f}' y1='{cy:.1f}' x2='{ix:.1f}' y2='{iy:.1f}' stroke='#333' stroke-width='0.8' stroke-dasharray='3 2'/>")
    # ED(E から D)
    s.append(f"<line x1='{ex:.1f}' y1='{ey:.1f}' x2='{dx:.1f}' y2='{dy:.1f}' stroke='#333' stroke-width='0.8'/>")
    # 点と直角記号(D は BC 上の垂線の足)
    for (pt, lab, ddx, ddy) in [((ax, ay), "A", -13, 4), ((bx, by), "B", 5, 2),
                                ((cx, cy), "C", 5, 6), ((dx, dy), "D", 3, -6),
                                ((ix, iy), "I", -2, -6), ((gx, gy), "G", 0, 13),
                                ((ex, ey), "E", -12, 2)]:
        s.append(f"<circle cx='{pt[0]:.1f}' cy='{pt[1]:.1f}' r='1.9' fill='#333'/>")
        s.append(f"<text x='{pt[0] + ddx:.1f}' y='{pt[1] + ddy:.1f}'>{lab}</text>")
    # 直角マーク at D
    s.append(f"<path d='M{dx - 7:.1f} {dy:.1f} L{dx - 7:.1f} {dy - 7:.1f} L{dx:.1f} {dy - 7:.1f}' "
             f"fill='none' stroke='#333' stroke-width='0.7'/>")
    s.append("</g></svg>")
    return "".join(s)


def _solid_svg():
    """導入の参考図: 四面体 PABC の見取り図(P 上・A 左・C 右・B 下、AC のみ破線)。"""
    W, H = 250, 210
    A = (40, 120); B = (120, 190); C = (210, 130); P = (120, 25)
    s = [f"<svg viewBox='0 0 {W} {H}' width='250' xmlns='http://www.w3.org/2000/svg'>",
         "<g font-family='Helvetica Neue,Arial,sans-serif' font-size='12' fill='#333'>"]
    # 実線: PA, PB, PC, AB, BC
    for (u, v) in [(P, A), (P, B), (P, C), (A, B), (B, C)]:
        s.append(f"<line x1='{u[0]}' y1='{u[1]}' x2='{v[0]}' y2='{v[1]}' stroke='#333' stroke-width='1.2'/>")
    # 破線(隠線): AC
    s.append(f"<line x1='{A[0]}' y1='{A[1]}' x2='{C[0]}' y2='{C[1]}' stroke='#333' stroke-width='1' stroke-dasharray='4 3'/>")
    for (pt, lab, dx, dy) in [(P, "P", -3, -6), (A, "A", -13, 4), (B, "B", -3, 15), (C, "C", 6, 4)]:
        s.append(f"<circle cx='{pt[0]}' cy='{pt[1]}' r='1.9' fill='#333'/>")
        s.append(f"<text x='{pt[0] + dx}' y='{pt[1] + dy}'>{lab}</text>")
    s.append("</g></svg>")
    return "".join(s)


_PLANE_SVG = _plane_svg()
_SOLID_SVG = _solid_svg()


# =========================================================================
#  第3問 選択肢(オリジナル内容・正解位置を分散)
# =========================================================================

_A_CHOICES = [  # 〚ア〛 直線BIの性質。正解=② (∠ABCを2等分する)
    r"直線 AC と垂直に交わる",
    r"直線 AC とねじれの位置にある",
    r"$\angle\mathrm{ABC}$ を2等分する",
    r"辺 AC の中点を通る",
]
_E_CHOICES = [  # 〚エ〛 共円をなす4点目。正解=④ (P)
    r"$\mathrm{A}$", r"$\mathrm{B}$", r"$\mathrm{C}$", r"$\mathrm{G}$", r"$\mathrm{P}$",
]
_SO_CHOICES = [  # 〚ソ〛 V₂ と V₁ の大小。正解=② (V₂はV₁より大きい)
    r"$V_2$ は $V_1$ より小さい",
    r"$V_2$ と $V_1$ は等しい",
    r"$V_2$ は $V_1$ より大きい",
]


# =========================================================================
#  第4問 星取表(4形態) を HTML テーブルで生成
# =========================================================================

def _star_table(players, rows, chosen, caption, note_diag=True):
    """星取表 HTML。
    players: 列見出しの対戦相手リスト(=行の名前でもある)。
    rows: dict name -> {opp: '○'/'×'/'', ...}  対角は自動で斜線。
    chosen: dict name -> '✓' or '—' or ''  (抽選列)。空文字なら空欄。
    勝ち数・負け数は ○×の数から自動集計(空欄は数えない)。
    """
    cells = []
    # ヘッダ
    head = "<tr><th class='corner'></th>"
    for pl in players:
        head += f"<th>{pl}</th>"
    head += "<th>勝ち数</th><th>負け数</th><th>抽選</th></tr>"
    cells.append(head)
    for r in players:
        line = f"<tr><th>{r}</th>"
        w = l = 0
        for c in players:
            if r == c:
                line += "<td class='diag'></td>"
            else:
                mark = rows.get(r, {}).get(c, "")
                if mark == "○":
                    w += 1
                elif mark == "×":
                    l += 1
                line += f"<td>{mark}</td>"
        # 勝ち数・負け数: 部分記入表では None を渡して空欄にできる
        wl = rows.get(r, {}).get("_wl")
        if wl is None:
            wtxt, ltxt = str(w), str(l)
        else:
            wtxt, ltxt = wl
        line += f"<td>{wtxt}</td><td>{ltxt}</td><td>{chosen.get(r, '')}</td></tr>"
        cells.append(line)
    tbl = ("<table class='star'>" + "".join(cells) + "</table>")
    # 実物準拠: 表番号・表題は表の【上】中央
    cap = f"<div class='tblcap' style='margin-bottom:1mm'>{caption}</div>" if caption else ""
    css = (
        "<style>"
        "table.star{border-collapse:collapse;margin:0 auto;font-size:9.6pt;"
        "font-family:'Helvetica Neue',Arial,sans-serif;}"
        "table.star th,table.star td{border:1px solid #333;width:8.5mm;height:7mm;"
        "text-align:center;padding:0;}"
        "table.star th{background:#f2f2f2;font-weight:600;}"
        "table.star td.diag{background:repeating-linear-gradient(135deg,#fff,#fff 2px,#bbb 2px,#bbb 3px);}"
        "table.star th.corner{background:repeating-linear-gradient(135deg,#f2f2f2,#f2f2f2 2px,#bbb 2px,#bbb 3px);}"
        "</style>")
    return f"<div class='tblw' style='break-inside:avoid'>{css}{cap}{tbl}</div>"


# --- 表1: 4人完全記入例 (A:×○○=B負C勝D勝で2勝1敗, B:2勝1敗, AとBが抽選対象) ---
_TABLE1 = _star_table(
    ["A", "B", "C", "D"],
    {"A": {"B": "×", "C": "○", "D": "○"},
     "B": {"A": "○", "C": "○", "D": "×"},
     "C": {"A": "×", "B": "×", "D": "○"},
     "D": {"A": "×", "B": "○", "C": "×"}},
    {"A": "✓", "B": "✓", "C": "—", "D": "—"},
    r"表1　4人のリーグ戦の対戦結果の例")

_TABLE1_RE = _star_table(
    ["A", "B", "C", "D"],
    {"A": {"B": "×", "C": "○", "D": "○"},
     "B": {"A": "○", "C": "○", "D": "×"},
     "C": {"A": "×", "B": "×", "D": "○"},
     "D": {"A": "×", "B": "○", "C": "×"}},
    {"A": "✓", "B": "✓", "C": "—", "D": "—"},
    r"表1（再掲）")

# --- 表2: 3人巴(三すくみ) A:_○×(BにC勝?) → A×B?  巴= A beats B, B beats C, C beats A ---
# A行: 対B=○, 対C=×  → A 1勝1敗 ; B行: 対A=×, 対C=○ → 1勝1敗 ; C行: 対A=○, 対B=× →1勝1敗
_TABLE2 = _star_table(
    ["A", "B", "C"],
    {"A": {"B": "○", "C": "×"},
     "B": {"A": "×", "C": "○"},
     "C": {"A": "○", "B": "×"}},
    {"A": "✓", "B": "✓", "C": "✓"},
    r"表2　3人が全員1勝1敗となる対戦結果の例")

# --- 表3: 4人部分記入(D が全敗。D列に○○○, D行に×××, 他は空欄) ---
#   A・B・C 行は D 戦だけ記入なので勝ち数・負け数は空欄(部分記入の視覚表現)。
_TABLE3 = _star_table(
    ["A", "B", "C", "D"],
    {"A": {"D": "○", "_wl": ("", "")}, "B": {"D": "○", "_wl": ("", "")},
     "C": {"D": "○", "_wl": ("", "")},
     "D": {"A": "×", "B": "×", "C": "×", "_wl": ("0", "3")},
     },
    {"D": "—"},
    r"表3　D が全敗する場合の対戦結果の一部")

# --- 表4: 4人部分記入(A が B に負け, C・D に勝つ。A行 ×○○, A列は各行の対A) ---
#   B・C・D 行は A 戦だけ記入なので勝ち数・負け数は空欄。
_TABLE4 = _star_table(
    ["A", "B", "C", "D"],
    {"A": {"B": "×", "C": "○", "D": "○", "_wl": ("2", "1")},
     "B": {"A": "○", "_wl": ("", "")}, "C": {"A": "×", "_wl": ("", "")},
     "D": {"A": "×", "_wl": ("", "")}},
    {},
    r"表4　A が B に負ける場合の対戦結果の一部")


# =========================================================================
#  SECTIONS
# =========================================================================

SECTIONS = [
    # ================= 第3問 図形の性質 =================
    {"no": 3, "points": 20, "parts": [
        {"label": "", "blocks": [
            {"t": "p", "text": r"空間内に，$\mathrm{AB}=\mathrm{AC}=10$，$\mathrm{BC}=12$ である二等辺三角形 ABC がある。$\triangle$ABC の内心を I とし，$\triangle$IBC の重心を G とする。G を通り，$\triangle$ABC を含む平面と垂直な直線上に，G と異なる点 P がある。このとき，$\triangle$ABC を底面とする三角<ruby>錐<rt>すい</rt></ruby> PABC について考えよう。"},
            {"t": "fig", "svg": _SOLID_SVG, "caption": "参考図"},
            {"t": "p", "text": r"直線 AI と辺 BC の交点を D とし，また，辺 PA 上の点 E は，$\angle\mathrm{PED}=\angle\mathrm{PID}$ を満たしているとする。なお，以下の問題において比を解答する場合は，最も簡単な整数の比で答えよ。"},
            # ---------- (1) ----------
            {"t": "p", "text": r"<b>(1)</b> 直線 BI が $〚ア〛$ ことに注意すると，$\triangle$ABD において線分 AI と ID の長さの比を求めることができる。よって，線分 AD の長さに着目すると"},
            {"t": "m", "tex": r"\mathrm{AI}=〔イ〕,\qquad \mathrm{ID}=〔ウ〕"},
            {"t": "p", "text": r"であることがわかる。"},
            {"t": "choices", "for": r"〚ア〛の解答群", "items": _A_CHOICES, "cols": 1},
            {"t": "fig", "svg": _PLANE_SVG, "caption": "参考図（平面 ABC）"},
            {"t": "p", "text": r"また，4点 E，I，D，$〚エ〛$ は同一円周上にある。よって"},
            {"t": "m", "tex": r"\mathrm{AE}\cdot\mathrm{AP}=〔オ〕〔カ〕"},
            {"t": "p", "text": r"であることがわかる。"},
            {"t": "choices", "for": r"〚エ〛", "auto_intro": True, "items": _E_CHOICES, "cols": 5},
            # ---------- (2) ----------
            {"t": "p", "text": r"<b>(2)</b> 線分 PI と DE の交点を F とする。このとき，線分 IF と FP の長さの比と，三角錐 PABC の体積との関係について考えよう。"},
            {"t": "p", "text": r"　(i) まず，線分 IF と FP の長さの比について，次の<b>仮定1</b>をおく。", "indent": False},
            {"t": "boxnote", "title": "仮定1", "lines": [
                r"線分 IF と FP の長さの比が $\mathrm{IF}:\mathrm{FP}=3:2$ である。",
            ]},
            {"t": "p", "text": r"このとき $\mathrm{PE}:\mathrm{EA}=〔キ〕:〔ク〕$ であるから，(1)での考察に注意すると"},
            {"t": "m", "tex": r"\mathrm{AP}=〔ケ〕\sqrt{〔コ〕}"},
            {"t": "p", "text": r"となる。したがって，直線 PG が $\triangle$ABC を含む平面に垂直であることに注意すると，三角錐 PABC の体積 $V_1$ は"},
            {"t": "m", "tex": r"V_1=〔サ〕〔シ〕"},
            {"t": "p", "text": r"であることがわかる。"},
            {"t": "p", "text": r"　(ii) 次に，(i)の<b>仮定1</b>の代わりに次の<b>仮定2</b>をおき，三角錐 PABC の体積の変化について考える。", "indent": False},
            {"t": "boxnote", "title": "仮定2", "lines": [
                r"線分 IF と FP の長さの比が $\mathrm{IF}:\mathrm{FP}=3:5$ である。",
            ]},
            {"t": "p", "text": r"<b>仮定2</b>のもとでの三角錐 PABC の体積 $V_2$ を，(i)で求めた $V_1$ と比較すると，$V_2$ と $V_1$ の比は"},
            {"t": "m", "tex": r"V_2:V_1=〔ス〕:〔セ〕"},
            {"t": "p", "text": r"であるから，$〚ソ〛$。"},
            {"t": "choices", "for": r"〚ソ〛の解答群", "items": _SO_CHOICES, "cols": 1},
        ]},
    ]},

    # ================= 第4問 場合の数と確率 =================
    {"no": 4, "points": 20, "parts": [
        {"label": "", "blocks": [
            {"t": "p", "text": r"卓球サークルで，メンバーが 1 対 1 の試合を行うリーグ戦の大会を開く。A，B，C の3人で行う場合と，A，B，C，D の4人で行う場合を考える。いずれもリーグ戦では，参加者全員が他の参加者と 1 回ずつ対戦し，引き分けはないものとする。"},
            {"t": "p", "text": r"A は他のどのメンバーと対戦しても勝つ確率が $\dfrac{1}{3}$ であり，A 以外の2人が対戦するときは，どちらが勝つ確率も $\dfrac{1}{2}$ である。また，各対戦の勝敗は独立に定まるものとする。優勝者は次のように決める。"},
            {"t": "boxnote", "title": "優勝者の決め方", "lines": [
                r"勝ち数が一番多い人が1人であれば，その人を優勝者とする。そうでなければ，<b>抽選</b>により，勝ち数が一番多い人の中から1人を選び，その人を優勝者とする。ただし，勝ち数が一番多い人の人数が $n$ 人であるとき，それぞれの人が選ばれる確率は $\dfrac{1}{n}$ であるものとする。",
            ]},
            {"t": "p", "text": r"A が優勝する確率を，A，B，C の3人でリーグ戦を行うときと，A，B，C，D の4人でリーグ戦を行うときとで比較しよう。"},
            {"t": "p", "text": r"以下では，すべての対戦の勝敗を<b>対戦結果</b>とよぶ。なお，<b>対戦結果</b>は抽選の結果を含まない。次の表1は，4人でリーグ戦を行うときの対戦結果の例である。"},
            {"t": "html", "html": _TABLE1},
            {"t": "p", "text": r"A から始まる行の $×○○$ は，A が B に負け C と D に勝ち，2勝1敗となったことを示す。また，勝ち数が一番多い A と B の2人が抽選の対象であり，そのことを $✓$ で示している。"},
            # ---------- (1) 3人 ----------
            {"t": "p", "text": r"<b>(1)</b> A，B，C の3人でリーグ戦を行う場合を考える。"},
            {"t": "p", "text": r"　(i) A が2勝0敗ならば，A が優勝する。A が2勝0敗で優勝する確率は $\dfrac{〔ア〕}{〔イ〕}$ である。", "indent": False},
            {"t": "p", "text": r"　(ii) A が1勝1敗で優勝するためには，B も C も1勝1敗であることが必要である。例えば，A が勝つ相手が B であるとき，A が C に負け，B が C に勝つことが必要である。表2は，この対戦結果を示している。", "indent": False},
            {"t": "html", "html": _TABLE2},
            {"t": "p", "text": r"この対戦結果になる確率は $\dfrac{〔ウ〕}{〔エ〕}$ である。この対戦結果になり，かつ A が抽選により優勝者に選ばれる確率は"},
            {"t": "m", "tex": r"\frac{〔ウ〕}{〔エ〕}\times\frac{〔オ〕}{〔カ〕}"},
            {"t": "p", "text": r"である。A が勝つ相手は B，C の2通りあることに注意すると，A が1勝1敗で優勝する確率は $\dfrac{〔キ〕}{〔ク〕〔ケ〕}$ であることがわかる。"},
            {"t": "p", "text": r"(i)と(ii)から，3人でリーグ戦を行うとき，A が優勝する確率は $\dfrac{〔ア〕}{〔イ〕}+\dfrac{〔キ〕}{〔ク〕〔ケ〕}$ である。"},
            # ---------- (2) 4人 ----------
            {"t": "p", "text": r"<b>(2)</b> 次に，A，B，C，D の4人でリーグ戦を行う場合を考える。A が3勝0敗ならば，A が優勝する。また，A が1勝2敗ならば，2勝以上する人がいるため A は優勝しない。A が2勝1敗で優勝する確率を，<b>全敗する人がいる場合</b>の確率と<b>全敗する人がいない場合</b>の確率の和として求める。"},
            {"t": "p", "text": r"　(i) 全敗する人は B，C，D の3通りある。例えば，D が全敗するとき，対戦結果の一部を示すと表3のようになる。", "indent": False},
            {"t": "html", "html": _TABLE3},
            {"t": "p", "text": r"D が全敗する確率は $\dfrac{〔コ〕}{〔サ〕〔シ〕}$ である。D が全敗する場合，A が2勝1敗で優勝するためには，A が D 以外の2人との対戦で1勝1敗となることが必要である。以上のことから，<b>(1)の(ii)の結果を用い</b>，全敗する人が B，C，D の3通りあることに注意すると，全敗する人がいる場合で，かつ A が2勝1敗で優勝する確率は $\dfrac{〔ス〕}{〔セ〕〔ソ〕}$ であることがわかる。"},
            {"t": "p", "text": r"　(ii) 全敗する人がいない場合を考える。A が2勝1敗のとき，A が負ける相手は B，C，D の3通りある。例えば，A が負ける相手が B であるとき，対戦結果の一部を示すと表4のようになる。", "indent": False},
            {"t": "html", "html": _TABLE4},
            {"t": "p", "text": r"このとき，A が優勝するためには，B は2勝1敗か1勝2敗であることが必要である。例えば，表1は，A と B が2勝1敗である対戦結果の一つを示し，A と B の2人が抽選の対象となったことを示す。"},
            {"t": "html", "html": _TABLE1_RE},
            {"t": "p", "text": r"全敗する人がいない場合で，かつ A が B に負け C と D に勝ち優勝するときの対戦結果は $〔タ〕$ 通りある。A が負ける相手が B，C，D の3通りあることに注意すると，全敗する人がいない場合で，かつ A が2勝1敗で優勝する確率は $\dfrac{〔チ〕}{〔ツ〕〔テ〕}$ であることがわかる。"},
            {"t": "p", "text": r"(i)と(ii)から，A が2勝1敗で優勝する確率は $\dfrac{〔ス〕}{〔セ〕〔ソ〕}+\dfrac{〔チ〕}{〔ツ〕〔テ〕}$ である。以上のことから，A が3勝0敗で優勝する確率を考慮すると，4人でリーグ戦を行うとき A が優勝する確率は $\dfrac{〔ト〕}{〔ナ〕}$ であることがわかる。"},
            {"t": "p", "text": r"この確率は，(1)で求めた3人でリーグ戦を行うときに A が優勝する確率より $\dfrac{〔ニ〕}{〔ヌ〕〔ネ〕}$ だけ $〚ノ〛$。"},
            {"t": "choices", "for": r"〚ノ〛", "auto_intro": True,
             "items": [r"小さい", r"大きい"], "cols": 2},
        ]},
    ]},
]


# =========================================================================
#  ANS_SECTIONS
# =========================================================================

ANS_SECTIONS = [
    {"section": 3,
     "slots": {
         # (1)
         "ア": "②", "イ": "5", "ウ": "3", "エ": "④", "オ": "4", "カ": "0",
         # (2)(i)
         "キ": "1", "ク": "4", "ケ": "5", "コ": "2", "サ": "1", "シ": "6",
         # (2)(ii)
         "ス": "4", "セ": "1", "ソ": "②",
     },
     "kai": [
         {"heading": "(1) 内心・角の二等分線・方べきの定理", "blocks": [
             {"t": "p", "text": r"I は $\triangle$ABC の内心だから，各頂点からの直線 AI，BI，CI はそれぞれの内角の二等分線である。よって直線 BI は $\angle\mathrm{ABC}$ を2等分する（$〚ア〛=$<b>②</b>）。⓪④は外心・重心，①は空間の位置関係の混同肢で，いずれも内心の性質ではない。"},
             {"t": "p", "text": r"二等辺三角形で AB＝AC だから，A から BC への二等分線 AD は BC を垂直に2等分し，$\mathrm{BD}=\mathrm{DC}=6$。よって"},
             {"t": "m", "tex": r"\mathrm{AD}=\sqrt{\mathrm{AB}^2-\mathrm{BD}^2}=\sqrt{10^2-6^2}=8"},
             {"t": "p", "text": r"直線 BI は $\angle\mathrm{ABD}$ の二等分線だから，角の二等分線の定理より $\mathrm{AI}:\mathrm{ID}=\mathrm{BA}:\mathrm{BD}=10:6=5:3$。$\mathrm{AD}=8$ をこの比に内分して"},
             {"t": "m", "tex": r"\mathrm{AI}=8\times\frac{5}{5+3}=\boxed{5},\qquad \mathrm{ID}=8\times\frac{3}{5+3}=\boxed{3}"},
             {"t": "p", "text": r"次に $\angle\mathrm{PED}=\angle\mathrm{PID}$ について考える。E は辺 PA 上，I は D と P を結ぶ側にあり，線分 PD を E と I が同じ側から等しい角で見込むから，円周角の定理の逆により4点 E，I，D，P は同一円周上にある（$〚エ〛=$<b>④</b>，すなわち P）。"},
             {"t": "p", "text": r"この円に対し点 A から2本の割線 AEP，AID を引いていることになるので，方べきの定理より"},
             {"t": "m", "tex": r"\mathrm{AE}\cdot\mathrm{AP}=\mathrm{AI}\cdot\mathrm{AD}=5\times8=\boxed{40}\quad(\text{オカ})"},
         ]},
         {"heading": "(2) 仮定による高さと体積", "blocks": [
             {"t": "p", "text": r"座標で扱う。AD を $x$ 軸にとり $\mathrm{A}(0,0)$，$\mathrm{D}(8,0)$，$\mathrm{B}(8,6)$，$\mathrm{C}(8,-6)$，$\mathrm{I}(5,0)$ とする。$\triangle$IBC の重心は"},
             {"t": "m", "tex": r"\mathrm{G}=\Bigl(\tfrac{5+8+8}{3},\ 0\Bigr)=(7,\ 0)"},
             {"t": "p", "text": r"PG は底面に垂直だから $\mathrm{P}=(7,\,h)$（$h>0$）とおける。$\mathrm{AP}^2=7^2+h^2$。E は方べきより $\mathrm{AE}=\dfrac{40}{\mathrm{AP}}$ で，P と同じ向きに $\mathrm{E}=\dfrac{40}{\mathrm{AP}^2}\mathrm{P}$。F は直線 PI と DE の交点で，$\mathrm{F}=\mathrm{I}+t(\mathrm{P}-\mathrm{I})$ が線分 DE 上にある条件から"},
             {"t": "m", "tex": r"t=\frac{\mathrm{IF}}{\mathrm{IP}}=\frac{15}{h^2+24}"},
             {"t": "p", "text": r"<b>(i) 仮定1</b>：$\mathrm{IF}:\mathrm{FP}=3:2$ より $t=\dfrac{3}{5}$。$\dfrac{15}{h^2+24}=\dfrac35$ を解くと $h^2=1$，$h=1$。よって $\mathrm{AP}^2=49+1=50$，$\mathrm{AP}=\boxed{5}\sqrt{\boxed{2}}$（ケ√コ）。"},
             {"t": "p", "text": r"$\mathrm{AE}=\dfrac{40}{5\sqrt2}=4\sqrt2$，$\mathrm{PE}=\mathrm{AP}-\mathrm{AE}=5\sqrt2-4\sqrt2=\sqrt2$。したがって $\mathrm{PE}:\mathrm{EA}=\sqrt2:4\sqrt2=\boxed{1}:\boxed{4}$（キ：ク）。"},
             {"t": "p", "text": r"底面積は $\triangle\mathrm{ABC}=\dfrac12\cdot\mathrm{BC}\cdot\mathrm{AD}=\dfrac12\cdot12\cdot8=48$。高さ $h=1$ だから"},
             {"t": "m", "tex": r"V_1=\frac13\times48\times1=\boxed{16}\quad(\text{サシ})"},
             {"t": "p", "text": r"<b>(ii) 仮定2</b>：$\mathrm{IF}:\mathrm{FP}=3:5$ より $t=\dfrac{3}{8}$。$\dfrac{15}{h^2+24}=\dfrac38$ を解くと $h^2=16$，$h=4$。よって $V_2=\dfrac13\times48\times4=64$。"},
             {"t": "m", "tex": r"V_2:V_1=64:16=\boxed{4}:\boxed{1}\quad(\text{ス：セ})"},
             {"t": "p", "text": r"$V_2>V_1$ だから $〚ソ〛=$<b>②</b>（$V_2$ は $V_1$ より大きい）。仮定を IF:FP が $3:2\to3:5$ と変えると F が P 側へ寄り，高さ $h$ が $1\to4$ と増えるので体積が大きくなる，と解釈できる。"},
         ]},
     ]},
    {"section": 4,
     "slots": {
         # (1)(i)  A2勝0敗優勝
         "ア": "1", "イ": "9",              # 1/9
         # (1)(ii) 巴の確率・抽選・A1勝1敗優勝
         "ウ": "1", "エ": "9",              # 1/9
         "オ": "1", "カ": "3",              # 1/3
         "キ": "2", "ク": "2", "ケ": "7",   # 2/27
         # (2)(i)  D全敗・全敗者ありでA優勝
         "コ": "1", "サ": "1", "シ": "2",   # 1/12
         "ス": "1", "セ": "5", "ソ": "4",   # 1/54
         # (2)(ii) 場合の数・全敗者なしでA優勝
         "タ": "4",                          # 4通り
         "チ": "1", "ツ": "1", "テ": "8",   # 1/18
         # (2)まとめ  4人版A優勝・3人版との差・大小
         "ト": "1", "ナ": "9",              # 1/9
         "ニ": "2", "ヌ": "2", "ネ": "7",   # 2/27
         "ノ": "⓪",                          # 小さい
     },
     "kai": [
         {"heading": "(1) 3人のリーグ戦", "blocks": [
             {"t": "p", "text": r"A の勝率は $\dfrac13$，A 以外どうしは $\dfrac12$。まず3人 A，B，C の場合。"},
             {"t": "p", "text": r"<b>(i)</b> A が2勝0敗（B にも C にも勝つ）なら A の勝ち数が単独最多で優勝。その確率は"},
             {"t": "m", "tex": r"\frac13\times\frac13=\frac{1}{9}\quad(\text{ア／イ})"},
             {"t": "p", "text": r"<b>(ii)</b> A が1勝1敗で優勝するには，3人全員が1勝1敗の三すくみ（表2）になり，抽選で A が当たる必要がある。A が B に勝ち C に負け，B が C に勝つ対戦結果の確率は"},
             {"t": "m", "tex": r"\underbrace{\tfrac13}_{\text{A→B勝}}\times\underbrace{\tfrac23}_{\text{A→C負}}\times\underbrace{\tfrac12}_{\text{B→C勝}}=\frac{1}{9}\quad(\text{ウ／エ})"},
             {"t": "p", "text": r"この対戦結果で3人とも1勝1敗だから抽選は3人が対象で，A が選ばれる確率は $\dfrac13$（オ／カ）。よってこの型で A が優勝する確率は $\dfrac19\times\dfrac13=\dfrac1{27}$。A が勝つ相手は B，C の2通りあるので"},
             {"t": "m", "tex": r"2\times\frac19\times\frac13=\frac{2}{27}\quad(\text{キ／クケ})"},
             {"t": "p", "text": r"(i)(ii)より3人のとき A の優勝確率は $\dfrac19+\dfrac{2}{27}=\dfrac{3}{27}+\dfrac{2}{27}=\dfrac{5}{27}$。"},
         ]},
         {"heading": "(2) 4人のリーグ戦", "blocks": [
             {"t": "p", "text": r"4人では A が3勝0敗なら必ず優勝，1勝2敗なら2勝以上の人がいて優勝できない。よって A の優勝は「3勝0敗」または「2勝1敗で優勝」。2勝1敗のケースを，全敗者の有無で場合分けする。"},
             {"t": "p", "text": r"<b>(i) 全敗する人がいる場合</b>　D が全敗する確率は（D は A に負け，B・C にも負ける）"},
             {"t": "m", "tex": r"\frac13\times\frac12\times\frac12=\frac{1}{12}\quad(\text{コ／サシ})"},
             {"t": "p", "text": r"（D 対 A は「A が勝つ」＝ D から見て負けなので確率 $\tfrac13$。）D が全敗なら，A・B・C は全員 D に勝って1勝を得ており，A が2勝1敗で優勝する条件は，A・B・C の3人の間で(1)(ii)と同じ「三すくみで A が抽選勝ち」になること。したがって"},
             {"t": "m", "tex": r"3\times\Bigl(\frac{1}{12}\times\frac{2}{27}\Bigr)=3\times\frac{1}{162}=\frac{1}{54}\quad(\text{ス／セソ})"},
             {"t": "p", "text": r"（全敗する人が B，C，D の3通りあるので3倍。）"},
             {"t": "p", "text": r"<b>(ii) 全敗する人がいない場合</b>　A が負ける相手が B のとき（表4：A は C，D に勝ち B に負ける）を考える。B は A に勝って1勝，C・D は A に負けて0勝から始まり，残る B，C，D どうしの3試合（BC，BD，CD）の結果は $2^3=8$ 通りある。このうち，全敗者が出ず，かつ A（2勝）が勝ち数最多に並ぶ対戦結果を数える。"},
             {"t": "p", "text": r"8通りを調べると，B が残り2試合とも勝つ2通りは C か D が全敗になり除外，B が残り2試合とも負ける2通りも C・D のどちらかが全敗（または B が0勝側）になり除外され，結局 A・B・C・D の勝ち数が $2$ 勝で2人が並ぶ次の4通りだけが残る。"},
             {"t": "m", "tex": r"(\mathrm{B},\mathrm{C},\mathrm{D})\text{の勝ち数}=(2,1,1),\ (2,1,1),\ (1,2,1),\ (1,1,2)"},
             {"t": "p", "text": r"はじめの $(2,1,1)$ が $2$ 通りあるのは，B が $2$ 勝で A と並ぶ対戦結果が（BC，BD，CD の勝敗の違いで）$2$ 通り存在するためである。残りは C が並ぶ場合，D が並ぶ場合が各 $1$ 通り。以上より"},
             {"t": "m", "tex": r"〔タ〕=4\ \text{通り}"},
             {"t": "p", "text": r"この4通りはそれぞれ，A が B に負け C・D に勝つ確率 $\tfrac23\cdot\tfrac13\cdot\tfrac13$ と，B・C・D の3試合それぞれ $\tfrac12$，および A が2人でのタイ抽選に勝つ $\tfrac12$ を伴う。A が負ける相手が B，C，D の3通りあることも合わせて厳密に計算すると，全敗する人がいない場合で A が2勝1敗で優勝する確率は"},
             {"t": "m", "tex": r"\frac{1}{18}\quad(\text{チ／ツテ})"},
             {"t": "p", "text": r"（分子1・分母2桁 18。全数列挙による厳密値。）"},
             {"t": "p", "text": r"(i)(ii)より A が2勝1敗で優勝する確率は $\dfrac{1}{54}+\dfrac{1}{18}=\dfrac{1}{54}+\dfrac{3}{54}=\dfrac{4}{54}=\dfrac{2}{27}$。A が3勝0敗で優勝する確率は $\left(\dfrac13\right)^3=\dfrac1{27}$。よって4人のとき A が優勝する確率は"},
             {"t": "m", "tex": r"\frac{1}{27}+\frac{2}{27}=\frac{3}{27}=\frac{1}{9}\quad(\text{ト／ナ})"},
             {"t": "p", "text": r"3人のときは $\dfrac{5}{27}$，4人のときは $\dfrac19=\dfrac{3}{27}$ だから，その差は"},
             {"t": "m", "tex": r"\frac{5}{27}-\frac{3}{27}=\frac{2}{27}\quad(\text{ニ／ヌネ})"},
             {"t": "p", "text": r"すなわち4人にすると A の優勝確率は $\dfrac{2}{27}$ だけ<b>小さい</b>。よって $〚ノ〛=$<b>⓪</b>。人数が増えるほど，実力で劣る A が抽選で這い上がる機会が減るため，優勝確率は下がる，と解釈できる。"},
         ]},
     ]},
]
