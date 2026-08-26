#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テストの冊子を**教科を問わず**組む共通ビルダー (docs/kamitest-manual/ の実装)。

各冊子の build_*.py が META と QUESTIONS (**唯一の正典**) を持ち、ここの run() を呼んで
取り込み JSON と問題 PDF を**同じデータから同時に**生成する。
「画面の第3問と冊子の第3問が違う」というずれは構造的に起きない。

■ 英文法 15 冊の _grammar_build.py との関係
    あちらは英文法専用 (subject 固定・空所必須・4択固定・8 要素のタプル)。**触らない**。
    こちらは全教科向けで、設問を dict で持ち、choice / short・数式・本文・図に対応する。
    新しい冊子はこちらで書く。

■ ★ node は要らない
    数式は **Chrome の中で KaTeX (vendor/katex) が描く**。塾長の Mac に node は無いので、
    node を要求する経路 (kyotsu_mogi2026/build_pdf.py) は持ち込まない。
    Chrome は print-to-pdf でどのみち要る。

■ ★ 3 層の相互チェックを build に埋め込む (CLAUDE.md 2026-08-16)
    ① 出力物どうしの照合 — 刷り上がり PDF を**読み返して**、
       ・生の LaTeX (`$` `\\frac` `¥(`) が 1 つも残っていないこと
         (KaTeX が 1 つでも落ちると、その式は生ソースのまま印刷され、PDF 生成は成功する)
       ・全設問の「第N問」と、数式以外の文字列が**正典どおりのページに**在ること
    ② 機械検査 — verify() が正典を直接見る (§下)
    ③ 人手 — 正解の一意性は機械に見えない。全問を敵対的に読み直すこと

    PDF を読む道具 (pypdf / pymupdf) が無いときは **黙って飛ばさず落とす**。
    どうしても先へ進めたいときだけ `SKIP_PDF_VERIFY=1` を明示する (理由が印字される)。

■ verify() が落とす形 — どれも採点崩れ・解説崩れに直結する
    ・番号の飛び / ページの逆行 / 選択肢の重複 / 正解番号が範囲外
    ・記述の正解が数字だけ (取り込みが弾く形) / 記述に選択肢がある
    ・正解位置の偏り (各番号が均等 ±1 に収まらない) / 同じ番号の 3 連続
    ・教科ごとの解説見出しの欠け・順番違い (SUBJECT_HEADINGS)
    ・誤答を潰す節の番号と選択肢のずれ (正解を誤答に載せる / 誤答の説明が欠ける)
      ★ 選択肢が数式のときは、設問に choices_plain (素の表記) を持たせる。
        解説に LaTeX は書けない (画面が素のテキスト表示) ので、照合はそちらで行う。
    ・解説に生の LaTeX (画面は素のテキスト表示なのでそのまま出てしまう)
    ・記述の正解が冊子の別の場所に印字されている (解答漏洩)

★ 先頭 `_` はゲートランナーの対象外 (共有ライブラリの慣習)。
  コミット済み JSON の検査は隣の check_grammar_books.py が CI で回す
  (同じ規則をここから import しているので二重管理にならない)。
"""
import glob
import html as _html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # リポジトリ直下
KATEX_DIR = os.path.join(ROOT, "vendor", "katex")

# -----------------------------------------------------------------------------
# 教科ごとの解説の見出し (docs/kamitest-manual/ の教科別ページと一致させる。
# ずれたら scripts/book_exam/check_kamitest_manual.py が落とす)
# ★ 最後の 1 つは「誤答を 1 つずつ潰す節」。番号と選択肢の文字列を照合する。
# -----------------------------------------------------------------------------
ENG_HEADINGS = ("## 🎯 コアイメージ", "## 🔬 文構造分析",
                "## 📍 正解の根拠", "## ❌ 誤答 NG 理由")

SUBJECT_HEADINGS = {
    "grammar":  ENG_HEADINGS,
    "reading":  ENG_HEADINGS,
    "eiken":    ENG_HEADINGS,
    "mock":     ENG_HEADINGS,
    "math":     ("【方針】", "【立式】", "【計算】", "【答え】", "【誤答の切り方】"),
    "japanese": ("【設問の型】", "【本文の根拠】", "【正解の理由】",
                 "【誤答の切り方】", "【次に使える型】"),
    "science":  ("【何が起きているか】", "【使う法則】", "【立式】",
                 "【計算】", "【誤答の切り方】"),
    "social":   ("【何を問うているか】", "【資料のどこ】", "【正解の理由】",
                 "【誤答の切り方】", "【覚え方の目印】"),
}

# 解説に書いてはいけない生の LaTeX (画面は textContent 表示なのでそのまま出る)
RAW_TEX_IN_EXP = re.compile(r"\$|\\\(|\\\)|\\frac|\\dfrac|\\sqrt|\\times|\\mathrm|¥\(")
# 刷り上がり PDF に残っていてはいけないもの (KaTeX が落ちた合図)
RAW_TEX_IN_PDF = re.compile(r"\$|\\frac|\\dfrac|\\sqrt|\\times|\\mathrm|\\circ|¥\(|\\\(")
MATH = re.compile(r"\$([^$]+)\$")
TAG = re.compile(r"[A-Z0-9]+-[A-Z0-9]+")


#: 図と本文に入れてはいけないもの。server 側の sanitizer が落とすので刷っても
#: 画面には出ないし、PDF では動く JS を持ち歩くことになる (CLAUDE.md の図の作法)。
UNSAFE_MARKUP = re.compile(r"<\s*script|<\s*foreignObject|\son[a-z]+\s*=", re.I)
#: 図の中の文字 (<text>…</text>)。逆照合と数値照合に使う。
SVG_TEXT = re.compile(r"<text[^>]*>(.*?)</text>", re.I | re.S)
#: 数値。図に出てよいのは設問文・本文にも在る数だけ (根拠が図の外に出ないように)。
NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def ng_heading(heads):
    """誤答を 1 つずつ潰す節の見出し。

    ★ 「最後の見出し」ではない。社会は【覚え方の目印】、国語は【次に使える型】が
      最後に来るので、最後で決め打ちすると**誤答の節を一度も見ない**まま緑になる
      (2026-08-21 に社会の 1 冊目で実際に踏んだ)。見出し名から引く。
    """
    for h in heads:
        if "誤答" in h:
            return h
    return None


def ng_section(exp, heads):
    """解説から誤答の節の中身だけを取り出す (次の見出しの手前まで)。"""
    h = ng_heading(heads)
    if not h or h not in exp:
        return None
    tail = exp.split(h)[-1]
    for nxt in heads[heads.index(h) + 1:]:
        tail = tail.split(nxt)[0]
    return tail


def distinguishing_prefix(items, i):
    """items[i] を他と区別できる最短の書き出し。区別できなければ全文。

    ★ 共通テスト型の選択肢は 60〜90 字ある。誤答を潰す節に全文を書き写すのは
      現実的でないので、「どの選択肢の話か」が**一意に決まる書き出し**まで
      引いてあればよい、とする。書き出しが他とかぶっている選択肢は、
      かぶりが解けるところまで引かせる (そこまで書けば取り違えは起きない)。
    """
    me = items[i]
    others = [o for j, o in enumerate(items) if j != i]
    for n in range(1, len(me) + 1):
        pre = me[:n]
        if not any(o.startswith(pre) for o in others):
            return pre
    return me


#: PDF に刷る欄で Markdown を書いても効かない (HTML で組むので記号のまま出る)。
MD_IN_PDF = re.compile(r"\*\*|__[^_]")


def markdown_problem(text, what):
    """@returns 理由 (None なら OK)。"""
    if text and MD_IN_PDF.search(str(text)):
        return (f"{what}: Markdown の太字 (**…**) は PDF に効かない。"
                f"記号のまま刷られるので <b>…</b> を使う "
                f"(解説欄は素のテキスト表示なので ** を使ってよい)")
    return None


def markup_problem(html, what):
    """@returns 理由 (None なら OK)。"""
    if UNSAFE_MARKUP.search(html or ""):
        return (f"{what}: <script> / on* 属性 / <foreignObject> は使えない "
                f"(sanitizer が落とす。PDF には動く JS が残る)")
    return None


def svg_texts(svg):
    """図の中の文字。タグを剥いで 1 つずつ返す。"""
    out = []
    for m in SVG_TEXT.findall(svg or ""):
        t = re.sub(r"<[^>]+>", "", m)
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            out.append(t)
    return out


def strip_math(s):
    """$…$ を落として素の文字列にする (PDF 逆照合と誤答照合はこの形で見る)。"""
    return re.sub(r"\s+", " ", MATH.sub(lambda m: m.group(1), s or "")).strip()


def plain_segments(s):
    """$…$ の外側だけを取り出す (KaTeX が描いた式は PDF で別の字形になるため)。"""
    return [seg.strip() for seg in MATH.split(s or "")[::2] if seg.strip()]


#: 字面を突き合わせられる数式。KaTeX が字そのままで描くものだけを通す。
MATH_SIMPLE = re.compile(r"[0-9A-Za-z+\-=.,()\[\]/<>|:;'≦≧≤≥×⋅π− ]*")

#: KaTeX が描いたあと、PDF のテキスト抽出でどう出るか (実測に基づく置き換え)。
TEX_AS_PRINTED = {
    "\\leqq": "≦", "\\geqq": "≧", "\\leq": "≤", "\\geq": "≥",
    "\\times": "×", "\\cdot": "⋅", "\\pi": "π",
    "\\left": "", "\\right": "", "\\,": "", "\\;": "", "\\!": "",
    "\\ ": " ", "\\mathrm": "",
}
#: ★ \frac{a}{b} は **分母 → 分子** の順で抽出される (2026-08-21 実測)。
FRAC = re.compile(r"\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}")


def tex_as_printed(tex):
    """$…$ の中身を、PDF から抜ける字面に寄せる。寄せられなければ None。

    ★ 累乗 (x^{2}) は、抽出すると指数が離れた場所に出る (実測) ので寄せられない。
      その場合は None を返し、pdf_check_note が「照合していない数」に数える。
    """
    s = tex
    for a, b in TEX_AS_PRINTED.items():
        s = s.replace(a, b)
    prev = None
    while prev != s:                       # 入れ子の \frac は内側から解ける
        prev = s
        s = FRAC.sub(lambda m: f"{m.group(2)}{m.group(1)}", s)
    if any(c in s for c in ("\\", "{", "}", "^", "_")):
        return None
    return s if MATH_SIMPLE.fullmatch(s) else None


def checkable_math(s):
    """$…$ のうち PDF の字面と突き合わせられるものを、**刷り上がりの形**で返す。"""
    out = []
    for m in MATH.findall(s or ""):
        printed = tex_as_printed(m)
        if printed is not None and printed.strip():
            out.append(printed)
    return out


def norm_pdf(s):
    """PDF から抜いた文字と正典を突き合わせるための正規化。

    ★ KaTeX の負号は U+2212 (−) で、正典の ASCII ハイフンとは別の文字。
      ここで揃えないと「-3」が PDF に無いことになる。
    """
    # ★ KaTeX は分数の前に幅ゼロの空白 (U+200B) を挟む。\s では消えない。
    for z in ("\u200b", "\u200c", "\u200d", "\ufeff", "\u00a0"):
        s = (s or "").replace(z, "") if z == "\u200b" else s.replace(z, "")
    return re.sub(r"\s+", "", s.replace("\u2212", "-"))


def question_mark(q):
    """PDF に刷られる設問の見出し。切り分けの目印にする。

    ★ 「第N問」だけで探してはいけない。前書きや資料が「第1問・第2問で問う」と
      書いていると**そちらを設問の先頭と誤認**し、以降の照合が丸ごとずれる
      (2026-08-21 に社会の 1 冊目で実際に踏んだ)。配点まで含めた見出しで引く。
    """
    return f"第{q['number']}問（{q['points']}点）"


def slice_by_question(text, qs):
    """ページのテキストを設問の見出しで切り分ける。@returns {番号: その設問の範囲}

    ★ KaTeX が描いた数式は PDF のテキスト抽出では**ページの末尾にまとめて**
      現れる (実測)。だからここで切れるのは数式以外の字だけ。数式はページ全体で見る。
    """
    marks = []
    for q in qs:
        i = text.find(norm_pdf(question_mark(q)))
        if i >= 0:
            marks.append((i, q["number"]))
    marks.sort()
    out = {}
    for j, (i, n) in enumerate(marks):
        end = marks[j + 1][0] if j + 1 < len(marks) else len(text)
        out[n] = text[i:end]
    return out


# =============================================================================
# 正解位置の配り (build 時と、コミット済み JSON の検査の両方から呼ぶ)
# =============================================================================
#: 偏りを見るには選択式が選択肢の数の何倍要るか。
#: 4 択 3 問で「各 0〜1 回」を求めても意味が無い (どう配っても落ちるか、
#: どう配っても通るかのどちらかになる)。見送ったことは run() が印字する。
SPREAD_MIN_RATIO = 2


def answer_position_errors(picks):
    """@param picks [(設問番号, 正解番号, 選択肢の数), ...] — **選択式だけ**
    @returns エラー文の一覧。"""
    errs = []
    if not picks:
        return errs
    counts = {c for _, _, c in picks}
    if len(counts) == 1:
        c = counts.pop()
        n = len(picks)
        if c and n >= SPREAD_MIN_RATIO * c:
            seq = [a for _, a, _ in picks]
            dist = {k: seq.count(k) for k in range(1, c + 1)}
            lo, hi = n // c, -(-n // c)
            if not all(lo <= v <= hi for v in dist.values()):
                errs.append(f"正解位置が偏っている: {dist} "
                            f"(選択式 {n} 問なので各 {lo}〜{hi} 回に収める)")
    # ★ 設問番号が連続している 3 問だけを見る (記述を挟んだら 3 連続ではない)
    for i in range(len(picks) - 2):
        (n0, a0, _), (n1, a1, _), (n2, a2, _) = picks[i:i + 3]
        if a0 == a1 == a2 and n1 == n0 + 1 and n2 == n1 + 1:
            errs.append(f"正解番号 {a0} が第{n0}問から 3 連続している")
    return errs


def spread_note(questions):
    """偏りの検査を見送ったなら、その理由を 1 行で返す (黙って減らさない)。"""
    picks = [q for q in questions if isinstance(q.get("choices"), list)]
    if not picks:
        return "正解位置の偏り: 選択式が無いので見ていない"
    counts = {len(q["choices"]) for q in picks}
    if len(counts) > 1:
        return f"正解位置の偏り: 選択肢の数がそろっていない {sorted(counts)} ので見ていない"
    c = counts.pop()
    if len(picks) < SPREAD_MIN_RATIO * c:
        return (f"正解位置の偏り: 選択式 {len(picks)} 問 / {c} 択では見ていない "
                f"({SPREAD_MIN_RATIO * c} 問以上で見る)")
    return None


# =============================================================================
# 検証 (正典を直接見る唯一の層)
# =============================================================================
def verify(meta, questions, extra=None):
    """@returns エラー文の一覧 (空なら合格)。"""
    errs = []
    subject = meta.get("subject")
    heads = SUBJECT_HEADINGS.get(subject)
    if heads is None:
        errs.append(f"subject {subject!r} は使えない "
                    f"(使えるのは {sorted(SUBJECT_HEADINGS)})")
        return errs
    if not (isinstance(meta.get("time_limit_min"), int)
            and meta["time_limit_min"] >= 1):
        errs.append("time_limit_min が 1 以上の整数でない")
    for key in ("stem", "title", "subject_name", "level"):
        if not str(meta.get(key) or "").strip():
            errs.append(f"META の {key} が空")

    printed = []          # 解答漏洩の走査対象 (問題編に刷る全文)
    for text in (meta.get("intro"), ):
        if text:
            printed.append(strip_math(text))
            why = markdown_problem(text, "META の intro")
            if why:
                errs.append(why)
    # --- 本文・資料 (passages) ----------------------------------------------
    for i, p in enumerate(meta.get("passages") or []):
        at = f"本文 {i + 1}"
        if p.get("page") is not None and \
                (not isinstance(p["page"], int) or p["page"] < 1):
            errs.append(f"{at}: page が 1 以上の整数でない")
        if not str(p.get("title") or "").strip():
            errs.append(f"{at}: title が空 (刷り上がりの照合に使う)")
        if not str(p.get("html") or "").strip():
            errs.append(f"{at}: html が空")
        why = markup_problem(p.get("html"), at)
        if why:
            errs.append(why)
        for field in ("html", "title", "source"):
            why = markdown_problem(p.get(field), f"{at} の {field}")
            if why:
                errs.append(why)
        for t in svg_texts(p.get("html")):      # 本文の図の中の答えも漏洩
            printed.append(strip_math(t))
        printed.append(strip_math(re.sub(r"<[^>]+>", " ", p.get("html") or "")))

    for i, q in enumerate(questions):
        no = q.get("number")
        at = f"第{no}問"
        if no != i + 1:
            errs.append(f"{at}: 番号が飛んでいる (期待 {i + 1})")
        page = q.get("page")
        # ★ page は省略できる (自動割り当て)。省くと、刷り上がりから実ページを
        #   読み取って JSON に書く。本文が長い冊子で「正典のページと刷り上がりが
        #   合わない」を手で追いかけずに済む (§run)。
        if page is not None:
            if not (isinstance(page, int) and page >= 1):
                errs.append(f"{at}: page が 1 以上の整数でない")
            elif i and questions[i - 1].get("page") is not None \
                    and page < questions[i - 1]["page"]:
                errs.append(f"{at}: page が前の設問より戻っている")
        elif any(x.get("page") is not None for x in questions):
            errs.append(f"{at}: page を書く設問と書かない設問が混ざっている "
                        f"(冊子ごとにどちらかに揃える)")
        stem = str(q.get("stem") or "").strip()
        if not stem:
            errs.append(f"{at}: 設問文が空")
        printed.append(strip_math(stem))
        why = markdown_problem(stem, f"{at} の設問文")
        if why:
            errs.append(why)
        for c in q.get("choices") or []:
            why = markdown_problem(c, f"{at} の選択肢")
            if why:
                errs.append(why)
                break
        pts = q.get("points")
        if not (isinstance(pts, int) and not isinstance(pts, bool) and pts >= 1):
            errs.append(f"{at}: 配点が 1 以上の整数でない")
        if not TAG.fullmatch(str(q.get("unit_tag") or "")):
            errs.append(f"{at}: unit_tag の形が崩れている ({q.get('unit_tag')!r})")

        # --- 図 (SVG) --------------------------------------------------------
        fig = q.get("figure")
        if fig is not None:
            if not str(fig).lstrip().startswith("<svg"):
                errs.append(f"{at}: figure は <svg> から始める")
            why = markup_problem(fig, f"{at} の図")
            if why:
                errs.append(why)
            texts = svg_texts(fig)
            printed.extend(strip_math(t) for t in texts)     # 図の中の答えも漏洩
            # ★ 図に設問文・本文に無い数を出さない。出すと設問の根拠が図の外に出て、
            #   印刷が潰れた・読み取れなかったときに設問そのものが解けなくなる。
            #   軸の目盛りのように「読み取るための数」は figure_ticks に宣言して除く。
            allow = {str(x) for x in (q.get("figure_ticks") or [])}
            src = strip_math(str(q.get("stem") or "")) + " " + " ".join(
                strip_math(re.sub(r"<[^>]+>", " ", p.get("html") or ""))
                for p in (meta.get("passages") or [])
                if p.get("page") == q.get("page"))
            for t in texts:
                for num in NUMBER.findall(t):
                    if num in allow or num in src:
                        continue
                    errs.append(f"{at}: 図の数値「{num}」が設問文にも本文にも無い "
                                f"(読み取らせる目盛りなら figure_ticks に入れる)")
        elif q.get("figure_ticks"):
            errs.append(f"{at}: figure が無いのに figure_ticks がある")

        choices = q.get("choices")
        ans = q.get("answer")
        if choices is None:                       # --- 記述 -------------------
            a = str(ans or "").strip()
            if not a:
                errs.append(f"{at}: 記述の正解が空")
            elif re.fullmatch(r"[0-9]+", a):
                errs.append(f"{at}: 記述の正解が数字だけ ({a!r})。"
                            f"単位を付けるか選択式にする")
            for alt in q.get("accepted") or []:
                if not str(alt).strip():
                    errs.append(f"{at}: accepted に空のものが混ざっている")
            # ★ 解答欄に単位を刷ってはいけない。紙は「解答欄 ___ A」で数字だけ書き、
            #   画面には単位つきで打つ、という食い違いになる (画面の入力欄に単位の
            #   手がかりは出ない)。答え方は設問文で示す。
            if q.get("unit"):
                errs.append(f"{at}: unit は使えない。答え方は設問文に "
                            f"「単位をつけて答えよ (例: 12A)」と書くこと")
            # ★ 数値 + 単位の答えは、答え方を設問文に書いていないと、
            #   正しく解いた生徒が書き方だけで不正解になる。
            mu = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*(\D+)", a)
            if mu and "単位" not in stem and mu.group(2).strip() not in stem:
                errs.append(f"{at}: 正解が「{a}」なのに答え方が設問文に無い。"
                            f"「単位をつけて答えよ (例: {a})」のように示す")
            if q.get("choices_plain"):
                errs.append(f"{at}: choices_plain は選択式のときだけ使える")
            if q.get("answer") is not None and not isinstance(q["answer"], str):
                errs.append(f"{at}: 記述の正解は文字列で書く "
                            f"({q['answer']!r})。数値をそのまま置かない")
        else:                                     # --- 選択式 -----------------
            if not (2 <= len(choices) <= 10):
                errs.append(f"{at}: 選択肢が 2〜10 でない ({len(choices)})")
            if len(set(choices)) != len(choices):
                errs.append(f"{at}: 選択肢に同じものが混ざっている")
            if q.get("accepted"):
                errs.append(f"{at}: 別解は記述のときだけ使える")
            if not (isinstance(ans, int) and not isinstance(ans, bool)
                    and 1 <= ans <= len(choices)):
                errs.append(f"{at}: 正解番号が 1〜{len(choices)} でない ({ans!r})")
            for c in choices:
                printed.append(strip_math(str(c)))

        # --- 解説: 教科の見出しが順番どおりに 1 回ずつ ----------------------
        exp = str(q.get("explanation") or "")
        if RAW_TEX_IN_EXP.search(exp):
            errs.append(f"{at}: 解説に生の LaTeX がある "
                        f"(画面は素のテキスト表示。x^2 / (a+b)/2 / √2 の形で書く)")
        pos = -1
        for h in heads:
            p = exp.find(h)
            if p < 0:
                # ★ 誤答を潰す節は**選択肢があるときだけ**必須。記述には誤答が無い
                #   ので、書きようのないものを求めない (書いてもよい)。
                if h == ng_heading(heads) and choices is None:
                    continue
                errs.append(f"{at}: 解説に「{h}」が無い")
            elif exp.count(h) > 1:
                errs.append(f"{at}: 解説に「{h}」が 2 回以上ある")
            elif p < pos:
                errs.append(f"{at}: 解説のセクションの順番が崩れている ({h})")
            else:
                pos = p
        # --- 誤答を潰す節: 番号と選択肢の文字列まで突き合わせる --------------
        ng = ng_section(exp, heads)
        if ng is not None and isinstance(choices, list) and \
                isinstance(ans, int) and 1 <= ans <= len(choices):
            lines = {}
            for ln in ng.splitlines():
                m = re.match(r"\s*([1-9])\.\s*(.*)", ln)
                if m:
                    lines[int(m.group(1))] = m.group(2)
            if ans in lines:
                errs.append(f"{at}: 正解 {ans} が誤答の節に載っている")
            plain = q.get("choices_plain") or [strip_math(str(c)) for c in choices]
            if len(plain) != len(choices):
                errs.append(f"{at}: choices_plain の数が選択肢と違う")
                plain = [strip_math(str(c)) for c in choices]
            plain = [str(c) for c in plain]
            for n in range(1, len(choices) + 1):
                if n == ans:
                    continue
                if n not in lines:
                    errs.append(f"{at}: 誤答 {n} の説明が無い")
                    continue
                key = distinguishing_prefix(plain, n - 1)
                if key not in strip_math(lines[n]):
                    errs.append(f"{at}: 誤答 {n} の説明が選択肢と合っていない。"
                                f"行の頭で選択肢の書き出しを引くこと "
                                f"(最低でも {key!r} まで)")

    # --- 記述の正解が問題編のどこかに刷られていないか (解答漏洩) -------------
    for q in questions:
        if q.get("choices") is not None:
            continue
        a = strip_math(str(q.get("answer") or ""))
        core = re.sub(r"[0-9．.\s]+", "", a)      # 単位・数値を除いた語の部分
        if len(core) < 2:
            continue
        for j, text in enumerate(printed):
            if core in text:
                errs.append(f"第{q.get('number')}問: 記述の答え「{core}」が"
                            f"問題編に印字されている (設問文・本文・他問の選択肢)")
                break

    # --- 正解位置の配り -----------------------------------------------------
    # ★ 記述 (choices が無い設問) を混ぜた冊子で壊れないこと:
    #   ・数えるのは選択式だけ。分母も選択式の問数
    #   ・3 連続は「**設問番号が連続している**選択式」のときだけ。記述を挟んだら切れる
    #     (以前は選択式だけを詰めた配列の添字で見ていたので、第1・3・5問が
    #      「第1問から 3 連続」と誤検出され、しかも問番号もずれていた)
    errs.extend(answer_position_errors(
        [(q.get("number"), q.get("answer"), len(q["choices"]))
         for q in questions
         if isinstance(q.get("choices"), list)
         and isinstance(q.get("answer"), int)
         and isinstance(q.get("number"), int)]))

    if extra:
        errs.extend(extra(meta, questions) or [])
    return errs


# =============================================================================
# 取り込み JSON
# =============================================================================
def build_json(meta, questions):
    """import_books.py が読む bundle。source の stem が PDF 名と一致する。"""
    out = []
    for q in questions:
        choices = q.get("choices")
        row = {
            "number": q["number"], "page": q["page"],
            "answer_type": "choice" if choices is not None else "short",
            "choice_count": len(choices) if choices is not None else None,
            "correct_answer": (str(q["answer"]) if choices is not None
                               else str(q["answer"]).strip()),
            "points": q["points"], "unit_tag": q["unit_tag"],
            "explanation": q["explanation"],
        }
        if choices is None and q.get("accepted"):
            row["accepted_answers"] = list(q["accepted"])
        out.append(row)
    return {
        "source": f"{meta['stem']}.yaml",
        "subject_name": meta["subject_name"],
        "book": {"title": meta["title"], "subject": meta["subject"],
                 "level": meta["level"], "time_limit_min": meta["time_limit_min"]},
        "questions": out,
    }


# =============================================================================
# 問題 PDF
# =============================================================================
# ★ 本番の冊子は本文が**明朝**、設問番号や見出しがゴシック。それに寄せる。
#   前に並べるのは Mac (ヒラギノ・游明朝)、後ろが Linux / CI (IPA)。
#   ★ どちらも無い環境では Chrome が**中国語フォント (WenQuanYi) に落ちる**。
#     字形が中国語になるが PDF は正常に出るので、刷って見るまで気づけない
#     (2026-08-21 に committed 19 冊すべてがこの状態だった)。
#     run() が刷り上がりの埋め込みフォントを見て落とす。
MINCHO = ('"Hiragino Mincho ProN", "Hiragino Mincho Pro", "Yu Mincho", "YuMincho", '
          '"IPAexMincho", "IPAPMincho", "IPAMincho", '
          '"Noto Serif CJK JP", "Noto Serif JP", serif')
GOTHIC = ('"Hiragino Kaku Gothic ProN", "Yu Gothic", "YuGothic", '
          '"IPAexGothic", "IPAPGothic", "IPAGothic", '
          '"Noto Sans CJK JP", "Noto Sans JP", sans-serif')

CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: """ + MINCHO + """; color: #111; font-size: 11.5pt;
       line-height: 1.9; }
.head h1, .q .no, .q .pt, .short .lbl, .passage h2, .passage th,
ol.ch .n { font-family: """ + GOTHIC + """; }
.head { border-bottom: 2px solid #111; padding-bottom: 6px; margin-bottom: 20px; }
.head h1 { font-size: 16pt; margin: 0 0 2px; }
.head .meta { font-size: 9.5pt; color: #555; }
.intro { border: 1px solid #bbb; padding: 8px 10px; margin-bottom: 18px;
         font-size: 10pt; line-height: 1.7; }
.passage { border: 1px solid #333; padding: 10px 12px; margin-bottom: 18px;
           page-break-inside: avoid; }
.passage h2 { font-size: 11pt; margin: 0 0 6px; }
.passage .body { font-size: 10.5pt; line-height: 2.0; }
.passage .src { font-size: 8.5pt; color: #555; margin-top: 6px; }
.passage p { margin: 0 0 6px; }
.passage ol, .passage ul { margin: 4px 0; padding-left: 1.6em; }
.passage table { border-collapse: collapse; width: 100%; font-size: 10pt;
                 margin: 4px 0; }
.passage th, .passage td { border: 1px solid #666; padding: 3px 7px;
                           text-align: left; vertical-align: top; }
.passage th { background: #f2f2f2; font-weight: 600; }
.passage .note { font-size: 9.5pt; color: #333; margin-top: 6px; line-height: 1.7; }
.q { margin-bottom: 26px; page-break-inside: avoid; }
.q .no { font-weight: 700; font-size: 11pt; }
.q .pt { font-size: 9pt; color: #666; margin-left: 8px; font-weight: 400; }
.q .stem { margin: 4px 0 8px; }
.q .fig { margin: 8px 0; text-align: center; }
.q .fig svg { max-width: 100%; height: auto; }
ol.ch { list-style: none; padding-left: 14px; margin: 0; }
ol.ch li { margin: 2px 0; }
/* ★ 分数など背の高い数式を含む選択肢は、本文の行送りのままだと行が重なる。
   その行だけ行間を広げる (:has は Chrome 105+。組版は Chrome で行う)。 */
ol.ch li:has(.katex) { margin: 7px 0; line-height: 2.6; }
ol.ch .n { display: inline-block; width: 1.9em; font-weight: 600; }
.short { margin-left: 14px; }
.short .lbl { font-weight: 600; margin-right: 6px; }
.short .box { display: inline-block; min-width: 46mm; border-bottom: 1px solid #111;
              height: 1.6em; vertical-align: -0.35em; }
.short .unit { margin-left: 6px; }
.pagebreak { page-break-after: always; }
.katex { font-size: 1.03em; }
"""

_KATEX_BOOT = """
<script src="katex.min.js"></script>
<script src="auto-render.min.js"></script>
<script>
  document.addEventListener('DOMContentLoaded', function () {
    renderMathInElement(document.body, {
      delimiters: [{left: '$', right: '$', display: false}],
      throwOnError: true
    });
    document.title = document.title + ' [katex-done]';
  });
</script>
"""


#: 記述の解答欄のラベル。PDF の逆照合がこの語を数えるので、
#: 設問文や本文に同じ語を書かないこと (書くと検査が甘くなるだけで、落ちはしない)。
SHORT_LABEL = "解答欄"


def _esc(s):
    """設問文の HTML 化。$…$ は KaTeX に渡すのでそのまま残す。"""
    return _html.escape(str(s), quote=False)


def render_question(q):
    out = [f'<div class="q"><div class="no">第{q["number"]}問'
           f'<span class="pt">（{q["points"]}点）</span></div>',
           f'<div class="stem">{_esc(q["stem"])}</div>']
    if q.get("figure"):
        out.append(f'<div class="fig">{q["figure"]}</div>')
    if q.get("choices") is not None:
        out.append('<ol class="ch">')
        for i, c in enumerate(q["choices"], 1):
            out.append(f'<li><span class="n">{i}.</span>{_esc(c)}</li>')
        out.append("</ol>")
    else:
        # ★ ラベルは SHORT_LABEL 固定。刷り上がり PDF の逆照合が
        #   「記述の解答欄がそのページに刷られたか」をこの語の数で見る。
        # ★ 単位は刷らない (verify が unit を禁じている)。答え方は設問文にある。
        out.append(f'<div class="short"><span class="lbl">{SHORT_LABEL}</span>'
                   f'<span class="box"></span></div>')
    out.append("</div>")
    return "".join(out)


def auto_page(questions):
    """page を書いていない冊子か。"""
    return all(q.get("page") is None for q in questions)


def build_head(meta, questions, page=None):
    total = sum(q["points"] for q in questions)
    if page is None:
        return (f'<div class="head"><h1>{_esc(meta["title"])}</h1>'
                f'<div class="meta">{_esc(meta["level"])} / 全{len(questions)}問 '
                f'{total}点 / 制限時間 {meta["time_limit_min"]} 分'
                f' — 解答は別画面の答案に入力してください</div></div>')
    return (f'<div class="head"><h1>{_esc(meta["title"])}'
            f'<span style="font-size:10pt;font-weight:400"> — '
            f'{page} ページ目</span></h1></div>')


def render_passage(p):
    src = (f'<div class="src">{_esc(p["source"])}</div>'
           if p.get("source") else "")
    brk = '<div class="pagebreak"></div>' if p.get("break_before") else ""
    return (f'{brk}<div class="passage"><h2>{_esc(p.get("title") or "")}</h2>'
            f'<div class="body">{p["html"]}</div>{src}</div>')


def build_html_flow(meta, questions):
    """page を書かない冊子の組み方。本文 → 設問を順に流し込むだけ。

    ★ どこで改ページになるかは中身の量で決まる。実ページは刷ってから読み取る
      (resolve_pages)。本文が数ページに渡る冊子で、ページ割りを手で合わせ直す
      作業が要らなくなる。
    """
    body = [build_head(meta, questions)]
    if meta.get("intro"):
        body.append(f'<div class="intro">{_esc(meta["intro"])}</div>')
    for p in meta.get("passages") or []:
        body.append(render_passage(p))
    for q in questions:
        body.append(render_question(q))
    return page_shell(meta, "".join(body))


def page_shell(meta, body):
    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<title>{_esc(meta["title"])}</title>'
            f'<link rel="stylesheet" href="katex.min.css">'
            f'<style>{CSS}</style>{_KATEX_BOOT}</head>'
            f'<body>{body}</body></html>')


def build_html(meta, questions):
    if auto_page(questions):
        return build_html_flow(meta, questions)
    total = sum(q["points"] for q in questions)
    by_page = {}
    for q in questions:
        by_page.setdefault(q["page"], []).append(q)
    passages = {}
    for p in meta.get("passages") or []:
        passages.setdefault(p["page"], []).append(p)

    body = []
    pages = sorted(set(by_page) | set(passages))
    for idx, page in enumerate(pages):
        if idx == 0:
            body.append(build_head(meta, questions))
            if meta.get("intro"):
                body.append(f'<div class="intro">{_esc(meta["intro"])}</div>')
        else:
            body.append(build_head(meta, questions, page))
        for p in passages.get(page, []):
            body.append(render_passage(p))
        for q in by_page.get(page, []):
            body.append(render_question(q))
        if idx < len(pages) - 1:
            body.append('<div class="pagebreak"></div>')

    return page_shell(meta, "".join(body))


def find_chrome():
    base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    for pat in (f"{base}/chromium-*/chrome-linux/chrome",
                f"{base}/chromium_headless_shell-*/chrome-linux/headless_shell"):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    direct = os.path.join(base, "chromium")
    if os.path.exists(direct) and os.access(direct, os.X_OK):
        return direct
    for c in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(c)
        if p:
            return p
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    return mac if os.path.exists(mac) else None


def write_pdf(meta, questions, out_pdf):
    """@returns エラー文 (None なら成功)。"""
    chrome = find_chrome()
    if not chrome:
        return "Chrome / Chromium が見つからない。PDF を作れない"
    if not os.path.isdir(KATEX_DIR):
        return f"vendor/katex が無い ({KATEX_DIR})"
    with tempfile.TemporaryDirectory() as tmp:
        # ★ katex 一式を同じフォルダへ写す。file:// を跨がせない (フォントが落ちる)
        for name in ("katex.min.js", "katex.min.css", "auto-render.min.js"):
            shutil.copy(os.path.join(KATEX_DIR, name), os.path.join(tmp, name))
        shutil.copytree(os.path.join(KATEX_DIR, "fonts"),
                        os.path.join(tmp, "fonts"))
        src = os.path.join(tmp, "book.html")
        with open(src, "w", encoding="utf-8") as f:
            f.write(build_html(meta, questions))
        cmd = [chrome, "--headless", "--disable-gpu", "--no-sandbox",
               "--no-pdf-header-footer", "--virtual-time-budget=15000",
               f"--print-to-pdf={out_pdf}", "file://" + src]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if r.returncode or not os.path.exists(out_pdf):
            return "print-to-pdf が失敗: " + (r.stderr or r.stdout)[-400:]
    return None


# =============================================================================
# 刷り上がり PDF の読み返し (相互チェック ①層)
# =============================================================================
#: 日本語フォントが 1 つも当たらなかったとき Chrome が落ちる先。
#: 混ざっていたら**字形が日本語でない**まま刷れている (漢字が中国語字形になる)。
#: PDF は正常に生成され、テキスト抽出も通るので、紙を見るまで気づけない。
FALLBACK_FONTS = ("wenquanyi", "zenhei", "unifont", "droidsansfallback",
                  "simsun", "simhei", "fangsong", "nanumgothic", "batang",
                  "notosanscjksc", "notosanscjktc", "notosanscjkkr",
                  "notoserifcjksc", "notoserifcjktc", "notoserifcjkkr")


def font_key(name):
    """埋め込みフォント名を突き合わせやすい形に (AAAAAA+ の接頭辞を落とす)。"""
    return re.sub(r"^[A-Z]{6}\+", "", str(name or "")) \
             .replace(" ", "").replace("-", "").replace("_", "").lower()


def font_problems(names):
    """@param names 埋め込みフォント名の集合。@returns エラー文の一覧。"""
    errs = []
    real = [n for n in names if str(n).strip()]
    if not real:
        return ["PDF にフォントが 1 つも埋め込まれていない"]
    for n in sorted(set(real)):
        key = font_key(n)
        if any(b in key for b in FALLBACK_FONTS):
            errs.append(
                f"PDF が日本語でないフォントで組まれている ({n})。"
                f"日本語フォントが 1 つも当たらず Chrome が代替に落ちている。"
                f"Linux/CI なら apt-get install fonts-ipafont-mincho "
                f"fonts-ipafont-gothic fonts-ipaexfont を入れてから刷り直す")
    return errs


def pdf_font_names(path):
    """PDF に埋め込まれているフォント名。読めなければ None。"""
    for mod in ("pymupdf", "fitz"):
        try:
            m = __import__(mod)
        except ImportError:
            continue
        try:
            with m.open(path) as doc:
                return {f[3] for pg in doc for f in pg.get_fonts(full=True)}
        except Exception:
            return None
    try:
        from pypdf import PdfReader
        out = set()
        for pg in PdfReader(path).pages:
            fonts = ((pg.get("/Resources") or {}).get("/Font") or {})
            for k in fonts:
                try:
                    out.add(str(fonts[k].get_object().get("/BaseFont", "")))
                except Exception:
                    pass
        return out
    except Exception:
        return None


def pdf_pages(path):
    """各ページのテキスト。pypdf → pymupdf の順。無ければ None。"""
    try:
        from pypdf import PdfReader
        return [p.extract_text() or "" for p in PdfReader(path).pages]
    except Exception:
        pass
    for mod in ("pymupdf", "fitz"):          # fitz は旧名 (警告が出る)
        try:
            m = __import__(mod)
            with m.open(path) as doc:
                return [pg.get_text() for pg in doc]
        except ImportError:
            continue
        except Exception:
            return None
    return None


def verify_pdf(meta, questions, path):
    """刷り上がり PDF を読み返して正典と突き合わせる。@returns エラー文の一覧。"""
    pages = pdf_pages(path)
    if pages is None:
        return ["PDF を読み返せない (pypdf も pymupdf も無い)。"
                "python3 -m pip install pypdf"]
    return verify_pages(meta, questions, pages)


def verify_pages(meta, questions, pages):
    """照合の本体。**ページのテキストだけ**を受け取る純関数。

    ★ PDF を読む道具も Chrome も要らないので、自己検査 (check_book_build.py) が
      CI でもここを直接叩ける。verify_pdf はファイルを読んで渡すだけ。
    """
    errs = []
    if any(q.get("page") is None for q in questions):
        return ["ページが決まっていない設問がある "
                "(page を書かない冊子は resolve_pages を先に通すこと)"]
    want_pages = max(q["page"] for q in questions)
    if len(pages) != want_pages:
        errs.append(f"PDF が {len(pages)} ページ (正典は {want_pages} ページ)")
    flat = [norm_pdf(p) for p in pages]
    whole = "".join(pages)
    # --- 生の LaTeX が残っていないか (KaTeX が落ちた合図) --------------------
    m = RAW_TEX_IN_PDF.search(whole)
    if m:
        i = max(0, m.start() - 40)
        errs.append(f"PDF に生の LaTeX が残っている (KaTeX が落ちている): "
                    f"…{whole[i:m.start() + 40]!r}…")
    # --- ページごとに設問を突き合わせる -------------------------------------
    by_page = {}
    for q in questions:
        by_page.setdefault(q["page"], []).append(q)
    for page, qs in sorted(by_page.items()):
        if page - 1 >= len(flat):
            continue
        text = flat[page - 1]
        # 記述の解答欄。箱は CSS の罫線で PDF に文字として出ないので、
        # ラベルの数で刷り漏れを見る。
        need = sum(1 for q in qs if q.get("choices") is None)
        if need:
            got = text.count(SHORT_LABEL)
            if got < need:
                errs.append(f"{page} ページ: 記述の解答欄が {need} 個要るのに "
                            f"「{SHORT_LABEL}」が {got} 個しか刷られていない")
        # --- 本文・資料がそのページに刷られているか ------------------------
        for i, ps in enumerate(meta.get("passages") or []):
            if ps.get("page") != page:
                continue
            body = re.sub(r"<[^>]+>", " ", ps.get("html") or "")
            for chunk in re.split(r"[。\n]", body):
                for seg in plain_segments(chunk):
                    if len(norm_pdf(seg)) < 4:
                        continue
                    if norm_pdf(seg) not in text:
                        errs.append(f"{page} ページ: 本文が PDF に無い ({seg[:24]!r})")
                        break
                else:
                    continue
                break
            if ps.get("title") and norm_pdf(ps["title"]) not in text:
                errs.append(f"{page} ページ: 本文の見出しが PDF に無い "
                            f"({ps['title'][:24]!r})")
            if ps.get("source") and norm_pdf(ps["source"]) not in text:
                errs.append(f"{page} ページ: 本文の出典が PDF に無い "
                            f"({ps['source'][:24]!r})")
            # ★ 本文の中に置いた図も照合する。設問の figure と違って
            #   検査が無かったため、図が丸ごと落ちても緑のままだった。
            for t in svg_texts(ps.get("html")):
                if norm_pdf(t) not in text:
                    errs.append(f"{page} ページ: 本文の図の文字が PDF に無い "
                                f"({t[:24]!r})")
                    break

        segs = slice_by_question(text, qs)
        for q in qs:
            at = f"第{q['number']}問"
            seg = segs.get(q["number"])
            if seg is None:
                # ★ どこに刷られたかを言う。ページ割りを直すのに要る情報で、
                #   「見つからない」だけだと 1 問ずつ総当たりになる。
                mark = norm_pdf(question_mark(q))
                where = [i + 1 for i, t in enumerate(flat) if mark in t]
                errs.append(
                    f"{at}: PDF の {page} ページに「{question_mark(q)}」が無い"
                    + (f" (実際は {where[0]} ページ目。正典の page を直すか、"
                       f"1 ページに載せる設問を減らす)" if where else
                       " (どのページにも無い)"))
                continue
            # 設問文 — 数式以外はその設問の範囲に、数式はページのどこかに
            for t in plain_segments(q["stem"]):
                if norm_pdf(t) not in seg:
                    errs.append(f"{at}: 設問文が PDF に無い ({t[:24]!r})")
                    break
            for t in checkable_math(q["stem"]):
                if norm_pdf(t) not in text:
                    errs.append(f"{at}: 設問文の数式が PDF に無い ({t[:24]!r})")
                    break
            # 図 — 中の文字がそのページに刷られているか (図が落ちると設問が解けない)
            for t in svg_texts(q.get("figure")):
                if norm_pdf(t) not in text:
                    errs.append(f"{at}: 図の文字が PDF に無い ({t[:24]!r})")
                    break
            # 選択肢 — 数式を含まないものは「番号. 本文」ごと突き合わせる
            #   (番号を外すと、同じ語が他の設問にあるだけで通ってしまう)
            for i, c in enumerate(q.get("choices") or [], 1):
                c = str(c)
                if not MATH.search(c):
                    if norm_pdf(f"{i}.{c}") not in seg:
                        errs.append(f"{at}: 選択肢 {i} が PDF に無い ({c[:24]!r})")
                    continue
                miss = [t for t in plain_segments(c) if norm_pdf(t) not in seg]
                miss += [t for t in checkable_math(c) if norm_pdf(t) not in text]
                if miss:
                    errs.append(f"{at}: 選択肢 {i} が PDF に無い ({miss[0][:24]!r})")
    return errs


def resolve_pages(meta, questions, pages_text):
    """刷り上がりから設問・本文の実ページを読み取って割り当てる。

    ★ page を書かない冊子 (auto_page) 用。本文が数ページに渡ると、正典に書いた
      ページと刷り上がりが合わず、手で合わせ直す作業が何度も要る。刷ってから
      読み取れば、ページはつねに実物と一致する。
    @returns エラー文の一覧 (空なら questions / passages の page を書き換え済み)
    """
    errs = []
    flat = [norm_pdf(t) for t in pages_text]
    for q in questions:
        mark = norm_pdf(question_mark(q))
        hit = next((i + 1 for i, t in enumerate(flat) if mark in t), None)
        if hit is None:
            errs.append(f"第{q['number']}問: 刷り上がりに"
                        f"「{question_mark(q)}」が見つからない")
        else:
            q["page"] = hit
    for i, p in enumerate(meta.get("passages") or []):
        title = norm_pdf(p.get("title") or "")
        hit = next((j + 1 for j, t in enumerate(flat) if title and title in t), None)
        if hit is None:
            errs.append(f"本文 {i + 1}: 刷り上がりに見出し"
                        f"「{p.get('title')}」が見つからない")
        else:
            p["page"] = hit
    nums = [q["page"] for q in questions if isinstance(q.get("page"), int)]
    if nums and nums != sorted(nums):
        errs.append(f"設問のページが前後している {nums} "
                    f"(刷り上がりの順序が正典と違う)")
    return errs


def pdf_check_note(questions):
    """PDF 逆照合で字面を突き合わせられなかった選択肢を言う (黙って減らさない)。"""
    total = skipped = 0
    for q in questions:
        for c in q.get("choices") or []:
            total += 1
            c = str(c)
            if MATH.search(c) and not plain_segments(c) and not checkable_math(c):
                skipped += 1
    if skipped:
        return (f"PDF 逆照合: 選択肢 {total} 個のうち {skipped} 個は"
                f"コマンド入りの数式なので字面を突き合わせていない")
    return None


# =============================================================================
def run(here, meta, questions, verify_extra=None):
    """build_*.py から呼ぶ入口。@returns 終了コード。"""
    errs = verify(meta, questions, verify_extra)
    if errs:
        for e in errs:
            print(f"✗ {e}")
        return 1
    n_short = sum(1 for q in questions if q.get("choices") is None)
    print(f"[ok] verify — {len(questions)} 問 "
          f"(選択式 {len(questions) - n_short} / 記述 {n_short}) / {meta['subject']} / "
          f"見出し {'・'.join(SUBJECT_HEADINGS[meta['subject']])}")
    note = spread_note(questions)
    if note:
        print(f"!    {note}")            # ★ 見送った検査は黙って減らさない

    stem = meta["stem"]
    out_json = os.path.join(here, f"{stem}.json")
    out_pdf = os.path.join(here, f"{stem}_問題.pdf")
    auto = auto_page(questions)
    if auto:
        print("[ok] ページは刷り上がりから割り当てる (正典に page を書いていない)")

    why = write_pdf(meta, questions, out_pdf)
    if why:
        print(f"✗ {why}")
        return 1
    print(f"[ok] {os.path.basename(out_pdf)} ({os.path.getsize(out_pdf) // 1024} KB)")

    # --- 埋め込みフォント (字形が日本語か) --------------------------------
    names = pdf_font_names(out_pdf)
    if names is None:
        print("!    埋め込みフォントを読めない (pypdf も pymupdf も無い)")
    else:
        jp = sorted(n for n in names if str(n).strip())
        print(f"[ok] 埋め込みフォント: {', '.join(jp) or '(無し)'}")
        errs = font_problems(names)
        if errs:
            for e in errs:
                print(f"✗ {e}")
            return 1

    def dump_json():
        # ★ JSON はすべての検査を通ってから書く。落ちた冊子の JSON が
        #   中途半端に残ると、次に取り込むとき古い内容が入る。
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(build_json(meta, questions), f, ensure_ascii=False, indent=1)
        print(f"[ok] {os.path.basename(out_json)}")

    if os.environ.get("SKIP_PDF_VERIFY") == "1":
        if auto:
            print("✗ ページを刷り上がりから割り当てる冊子では "
                  "SKIP_PDF_VERIFY=1 は使えない (page が決まらない)")
            return 1
        print("! 刷り上がり PDF の読み返しを飛ばした (SKIP_PDF_VERIFY=1)。"
              "相互チェックの①層が抜けている")
        dump_json()
        return 0

    pages_text = pdf_pages(out_pdf)
    if pages_text is None:
        print("✗ PDF を読み返せない (pypdf も pymupdf も無い)。"
              "python3 -m pip install pypdf")
        return 1
    if auto:
        errs = resolve_pages(meta, questions, pages_text)
        if errs:
            for e in errs:
                print(f"✗ ページ割り当て: {e}")
            return 1
        spread = {}
        for q in questions:
            spread.setdefault(q["page"], []).append(q["number"])
        print("[ok] ページ割り当て: "
              + " / ".join(f"{p}頁 第{'・'.join(map(str, v))}問"
                           for p, v in sorted(spread.items())))
    errs = verify_pages(meta, questions, pages_text)
    if errs:
        for e in errs:
            print(f"✗ PDF 読み返し: {e}")
        return 1
    note = pdf_check_note(questions)
    if note:
        print(f"!    {note}")
    print(f"[ok] PDF 読み返し — 全{len(questions)}問・全選択肢が正典どおりの"
          f"ページに在る / 生の LaTeX なし")
    dump_json()
    return 0
