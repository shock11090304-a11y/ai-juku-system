#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共通テスト 9 科目の元データ (YAML) を、冊子受験アプリの JSON へ機械変換する。

    python3 scripts/book_exam/convert_kyotsu_yaml.py --probe   # ★ まずこれ。構造を出すだけ
    python3 scripts/book_exam/convert_kyotsu_yaml.py           # 変換して一覧を出す
    python3 scripts/book_exam/convert_kyotsu_yaml.py --out DIR # DIR に .json を書き出す
    python3 scripts/book_exam/convert_kyotsu_yaml.py --selftest # 見本で自己検査 (CI が回す)

    --root PATH   元データの置き場所 (既定 ~/Desktop/問題生成)

■ 対象 (2026-06-03 に組版した 9 冊。PDF は lesson-prints/ に出ている)
    英語R / 国語 / 数学IA / 数学IIB / 物理 / 化学 / 生物 / 日本史 / 世界史

■ ★ 正解の持ち方が 3 通りに割れている
    A: トップレベルの answer_key:            英語R・国語・物理
    B: 大問ごとの answer_key: (ア・イ 方式)   数学IA・数学IIB
    C: answer_key が無く解説本文に埋め込み    化学・生物・日本史・世界史
  A→そのまま / B→**取り込めない (下記)** / C→正規表現で抜く。
  **どれにも当てはまらないファイルは推測しないで飛ばす**。黙って中途半端に
  変換するより、飛ばして理由を出すほうが安全 (正解が 1 つずれても画面は壊れない)。

■ ★ 形 B (数学IA / IIB) は今のアプリに入れられない — 7/9 冊だけ変換する
  マーク欄の答えは 1 桁の数字 (ア=5 等)。ところが exam-book-admin-model.mjs の
  validateQuestions は **記述の正解が数字だけなら弾く** (2026-08-14 に実測で確認)。
  これは「選択肢を取りこぼした設問」を捕まえるための砦で、実際に紙教材 835 問の
  変換ではこの規則が効いている。2 冊のために外す価値はない。
    ・選択式にするのも不可: PDF には「ア」と出ているのに画面には 1〜10 の
      ピルが出て、0 のマークが表現できない。
    ・入れたいなら exam-book-admin-model.mjs:143 の規則を「マーク欄なら数字可」に
      変える必要がある。**スキーマと検証器の設計変更なので、指示があるまでやらない。**

■ ★ この変換器は元データを見ないで書いた
    元データは塾長の Mac (~/Desktop/問題生成/) にあり、この作業環境からは読めない。
    ここに入れた「形」は別セッションの調査報告に基づく **想定** で、
    scripts/book_exam/fixtures_kyotsu/*.yaml がその想定を書き下したもの。
    実物が違えば変換は **落ちる** (推測しないので黙って通らない)。
    そのときは --probe の出力を見て、想定と fixtures を直すこと。

■ ★ ページ番号は入れられる
    convert_workbook.py と違い、こちらは組版済み PDF が lesson-prints/_metadata.json
    に載っている (ページ数・小問数)。ページ数は冊子の検算に使う。
    ただし「何問目が何ページか」は YAML には無いので page は null のまま。
"""
import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

DEFAULT_ROOT = os.path.expanduser("~/Desktop/問題生成")
FIXTURES = os.path.join(HERE, "fixtures_kyotsu")
METADATA = os.path.join(ROOT, "lesson-prints", "_metadata.json")

# -----------------------------------------------------------------------------
# 科目 → books.subject (閉じた集合。supabase/migrations/…_books_subject_widen.sql)
# ★ 9 冊とも共通テスト形式だが subject は 'mock' にしない。
#   生徒は「数学の冊子を出して」と探すので、教科で引けるほうが役に立つ。
#   模試であることは題名 (共通テスト◯◯ マーク式) で分かる。
# -----------------------------------------------------------------------------
SUBJECT_BY_NAME = {
    "英語R": "reading",
    "国語": "japanese",
    "数学IA": "math",
    "数学IIB": "math",
    "物理": "science",
    "化学": "science",
    "生物": "science",
    "日本史": "social",
    "世界史": "social",
}

# ★ 組版済み PDF (lesson-prints/_metadata.json) と別セッションの調査で分かった問数。
#   合わなければ「抜けている」ということなので必ず落とす。
#   化学 25 / 生物 20 は 2026-08-14 の実機変換の実測を凍結したもの (回帰検出用)。
#   ★ 取り込むとき 1 冊 1 回、PDF の最終問番号と突き合わせて確かめること。
EXPECTED_COUNT = {"英語R": 22, "国語": 24, "物理": 20, "世界史": 20, "日本史": 20,
                  "化学": 25, "生物": 20}

# ★ バックアップ / 作業途中のフォルダは見ない。
#   実物には _ruby_fix_backup2/ に国語の旧版があり、同じ冊子が 2 つできていた
#   (2026-08-14)。中身はルビ記法が残った組版前のもので、生徒に出すものではない。
EXCLUDE_PATH = re.compile(r"(backup|bak|old|旧|作業中|tmp|temp|work)", re.I)

CIRCLED = {c: i + 1 for i, c in enumerate("①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳")}
ZENKAKU = {c: i for i, c in enumerate("０１２３４５６７８９")}

# 解説本文から正解を抜く形。★ 実物は科目ごとに違う (2026-08-14 に --probe で確認):
#     化学   <strong>問1 → 正解 ②</strong>
#     物理   <strong>$\text{問 1}$ 正解 ②</strong>
#     生物   <strong>問 1 → 正解 ②</strong>
#     世界史 **問 A 正解: ②**
#     日本史 問 1　正解: **①**　中大兄皇子と…
#   飾り (<strong> / ** / $ / \text{}) を先に剥がせば 1 本の形で足りる。
#   ★ 「正解」の直後に来る番号だけを拾う。誤答の説明にも番号は出るので、
#     語を挟まない位置に限る。
#   見出しは全角英字 (問 Ａ) もあり得る。「問 C の正解: ②」の「の」も許す。
#   正誤問題の注記「正解(誤り): ③」も実物にある (世界史 問E、2026-08-14)。
#   注記は (誤り) / (誤) だけ許す — 見た実物に限る。別の注記が出たら
#   診断が該当行ごと運んでくるので、そのとき足す。
ANSWER_IN_TEXT = re.compile(
    r"問\s*([0-9０-９A-Za-zＡ-Ｚａ-ｚ]{1,3})\s*(?:の)?\s*(?:→|➡)?\s*"
    r"正解\s*(?:は)?\s*(?:[((]誤り?[))])?\s*[::]?\s*([①-⑳])")

# 「①〜④ から 1 つ選べ」— 選択肢の数がここに書いてある大問がある。
CHOICE_RANGE = re.compile(r"([①-⑳])\s*[〜~ー–—−-]\s*([①-⑳])")

# 飾りを剥がす (LaTeX と HTML と Markdown が混ざっている)
DECOR = re.compile(r"</?strong>|</?b>|\*\*|\\text\{|\\mathrm\{|[$}{]")


def norm_text(s):
    """<strong> / ** / $ / \\text{…} を剥がして、正解を探せる素の文にする。"""
    return DECOR.sub("", str(s or ""))


# =============================================================================
# 小道具
# =============================================================================
def to_int(v):
    """①/３/'3'/3 を int に。分からなければ None。

    @returns (値, 1起算と断定できるか)
    """
    if isinstance(v, bool):
        return None, False
    if isinstance(v, int):
        return v, False                       # 素の整数は起算が分からない
    s = str(v).strip()
    if not s:
        return None, False
    if s in CIRCLED:
        return CIRCLED[s], True               # ★ ①は必ず 1 番目。起算が確定する
    s = "".join(str(ZENKAKU[c]) if c in ZENKAKU else c for c in s)
    if re.fullmatch(r"[0-9]+", s):
        return int(s), False
    return None, False


def load_yaml(path):
    import yaml
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def subject_of(path):
    """ファイル名から科目名を取る。数学IIB を数学IA より先に見る (前方一致の罠)。"""
    name = os.path.basename(path)
    for key in sorted(SUBJECT_BY_NAME, key=len, reverse=True):
        if key in name:
            return key
    return None


def find_files(root):
    pats = [os.path.join(root, "**", "samples", "*共通テスト*マーク式*.yaml"),
            os.path.join(root, "**", "*共通テスト*マーク式*.yaml")]
    out = []
    for p in pats:
        out += glob.glob(p, recursive=True)
    # ★ バックアップ / 作業途中のフォルダは外す。中に旧版が入っていて、
    #   同じ冊子が 2 つできていた (実物の _ruby_fix_backup2/)。
    keep, dropped = [], []
    for p in sorted(set(out)):
        rel = p[len(root):] if p.startswith(root) else p
        (dropped if EXCLUDE_PATH.search(rel) else keep).append(p)
    for p in dropped:
        print(f"  [除外] {short_path(p)} — バックアップ / 作業途中のフォルダ")
    return keep


def print_metadata_table():
    """組版済み PDF の実測値 (リポジトリに入っている)。冊子作りの検算に使う。"""
    if not os.path.exists(METADATA):
        return {}
    try:
        prints = json.load(open(METADATA, encoding="utf-8"))["prints"]
    except Exception:
        return {}
    out = {}
    for p in prints:
        fp = p.get("file_path") or ""
        if "2026-06-03" not in fp or "マーク式" not in fp or "_問題.pdf" not in fp:
            continue
        subj = subject_of(fp)
        if not subj:
            continue
        try:
            n_sub = len(json.loads(p.get("sub_question_topics") or "[]"))
        except Exception:
            n_sub = 0
        out[subj] = {"pdf": os.path.basename(fp), "pages": p.get("pages"),
                     "kb": p.get("file_size_kb"), "sub_questions": n_sub}
    return out


# =============================================================================
# 設問を拾う
# =============================================================================
def harvest(obj):
    """入れ子のどこにあっても「設問らしい dict」を順番に拾う。

    ★ キー名でなく **形** で判定する (選択肢の一覧を持っている dict)。
      名前で決め打ちすると、科目ごとに違う書き方で黙って落ちる。
    """
    found = []

    def choices_of(o):
        for k in ("choices", "options", "選択肢", "sentaku"):
            v = o.get(k)
            if isinstance(v, list) and len(v) >= 2:
                return v
        return None

    def walk(o):
        if isinstance(o, dict):
            if choices_of(o) is not None:
                found.append(o)
                return                        # 設問の中はもう掘らない
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(obj)
    return found


def get_choices(q):
    for k in ("choices", "options", "選択肢", "sentaku"):
        v = q.get(k)
        if isinstance(v, list) and len(v) >= 2:
            return v
    return None


def get_stem(q):
    for k in ("stem", "q", "question", "text", "設問", "prompt", "body"):
        v = q.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def get_explanation(q):
    for k in ("explanation", "exp", "解説", "commentary", "kaisetsu"):
        v = q.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def get_number(q):
    for k in ("number", "no", "num", "q_no", "問番号", "id"):
        n, _ = to_int(q.get(k))
        if n is not None:
            return n
    return None


def get_points(q):
    for k in ("points", "point", "pt", "配点", "haiten"):
        n, _ = to_int(q.get(k))
        if n is not None and n >= 1:
            return n
    return None


# =============================================================================
# 正解の在り処 3 通り
# =============================================================================
# answer_key の要素が dict のときに正解と問番号を持つキー
#   実物 (2026-08-14 に --probe で確認): answer_key: [{number: 1, answer: '⑤'}, …]
ANS_KEYS = ("answer", "ans", "正解", "correct", "value")
NUM_KEYS = ("number", "no", "num", "q_no", "問")


def key_as_list(v):
    """answer_key の中身を [(見出し, 生の値)] に均す。

    受け付ける形:
      list of 値       [3, 1, 4]                     → [(1,3), (2,1), (3,4)]
      list of dict     [{number:1, answer:'⑤'}, …]  → [(1,'⑤'), …]   ★実物はこれ
      dict             {1: '⑤', 2: '②'}             → 宣言順のまま
    ★ dict なのに正解らしいキーが無いものは **空を返す** (推測しない)。
    """
    if isinstance(v, list):
        out = []
        for i, x in enumerate(v):
            if isinstance(x, dict):
                val = next((x[k] for k in ANS_KEYS if k in x), None)
                if val is None:
                    return []
                label = next((x[k] for k in NUM_KEYS if k in x), i + 1)
                out.append((label, val))
            else:
                out.append((i + 1, x))
        return out
    if isinstance(v, dict):
        return [(k, x) for k, x in v.items()]
    return []


def adapt_a_top_level(doc, questions):
    """A: トップレベル answer_key: をそのまま設問の並びに当てる。"""
    if not isinstance(doc, dict):
        return None, "トップが dict でない"
    key = None
    for k in ("answer_key", "answers", "正解", "answer"):
        if k in doc:
            key = doc[k]
            break
    if key is None:
        return None, None                     # 形 A ではない (エラーではない)
    pairs = key_as_list(key)
    if not pairs:
        return None, (f"answer_key が読めない形 ({type(key).__name__})。"
                      f"要素が dict なら正解のキーを ANS_KEYS に足すこと")
    if len(pairs) != len(questions):
        return None, (f"answer_key が {len(pairs)} 個で設問が {len(questions)} 問。"
                      f"数が合わないので当てられない")

    # ★ 番号が付いているなら **番号で突き合わせる**。並び順に頼ると、
    #   設問を拾う順 (passages → questions) と answer_key の順が食い違ったとき
    #   全問ずれた正解になり、しかも数は合うので誰も気づけない。
    labels = [lab for lab, _v in pairs]
    if len(set(labels)) == len(labels) and all(isinstance(x, int) for x in labels):
        qnums = [get_number(q) for q in questions]
        if all(n is not None for n in qnums) and len(set(qnums)) == len(qnums):
            if set(qnums) != set(labels):
                return None, (f"answer_key の問番号と設問の問番号が食い違う "
                              f"(answer_key にしか無い: "
                              f"{sorted(set(labels) - set(qnums))[:5]} / "
                              f"設問にしか無い: {sorted(set(qnums) - set(labels))[:5]})")
            by = dict(pairs)
            return [by[n] for n in qnums], None

    return [v for _label, v in pairs], None


def answers_in(text):
    """解説本文から [(問の見出し, 1起算の正解番号)] を出てくる順に拾う。

    ★ 丸数字だけを拾う。①は必ず 1 番目なので起算の疑いが無い。
      素の数字も拾うと「誤答②は…」のような文で誤爆する。
    """
    out = []
    for m in ANSWER_IN_TEXT.finditer(norm_text(text)):
        out.append((m.group(1), CIRCLED[m.group(2)]))
    return out


def choice_count_from_range(text):
    """「①〜④ から 1 つ選べ」→ 4。書いていなければ None。

    ★ ①から始まっていないもの (③〜⑥ 等) は選択肢の範囲ではないので採らない。
    """
    for m in CHOICE_RANGE.finditer(norm_text(text)):
        a, b = CIRCLED[m.group(1)], CIRCLED[m.group(2)]
        if a == 1 and 2 <= b <= 10:
            return b
    return None


def choice_count_from_list(text):
    """「① 科挙制度は… ② X 正・Y 正 ③ …」のように 1 本の文字列に詰まった
    選択肢を数える。

    ★ ①②③… が **1 から連番で並んでいること** を要求する。
      選択肢の本文にも丸数字が出るので、連番でなければ数えない。
    """
    seen = [CIRCLED[c] for c in norm_text(text) if c in CIRCLED]
    if not seen or seen[0] != 1:
        return None
    n = 1
    for v in seen[1:]:
        if v == n + 1:
            n = v
        elif v > n + 1:
            return None                       # 飛んでいる = 連番ではない
    return n if 2 <= n <= 10 else None


def choice_count_from_runs(text):
    """大問の本文に問ごとの選択肢が「① … ② … ③ … ④ …」と列挙されている
    とき、その **連番の列 (run)** を数える。

    ★ 「①〜④ から選べ」の範囲表記が無い大問のための代替。推測ではなく、
      生徒が実際に見る列挙そのものを数える。
      ・① から始まり +1 ずつ続く列だけを run と数える (長さ 2 以上)
      ・全部の run が同じ長さのときだけ採用。違う長さが混ざる = 大問の中で
        選択肢数が問ごとに違うので、1 つの数では表せない → None
      ・独立した ① 1 つ (本文の参照など) は run にならず無視される。
        列挙の途中が欠けた列は run が短くなって不一致になり、表に出る。
    @returns (数, run の一覧)。決められなければ (None, run の一覧)
    """
    runs, cur = [], 0
    for c in norm_text(text):
        if c not in CIRCLED:
            continue
        v = CIRCLED[c]
        if v == 1:
            if cur >= 2:
                runs.append(cur)
            cur = 1
        elif v == cur + 1:
            cur = v
        # それ以外 (飛び・逆行) は run の外の丸数字とみなして無視
    if cur >= 2:
        runs.append(cur)
    if runs and len(set(runs)) == 1 and 2 <= runs[0] <= 10:
        return runs[0], runs
    return None, runs


def sections_of(doc):
    for key in ("sections", "passages", "大問"):
        v = (doc or {}).get(key) if isinstance(doc, dict) else None
        if isinstance(v, list) and v:
            return v
    return []


def section_label(sec, i):
    for k in ("qnum", "label", "id", "title", "section"):
        v = sec.get(k)
        if v not in (None, ""):
            s = str(v).strip()
            return s if not s.isdigit() else f"第{s}問"
    return f"第{i + 1}問"


def even_points(score, n):
    """大問の配点を小問に等分できるときだけ配る。割り切れなければ 1 点。

    ★ 端数を勝手に寄せない。合計が本番と変わるより、全問 1 点のほうが
      「素点ではない」と分かってよい。
    """
    if isinstance(score, int) and n and score >= n and score % n == 0:
        return score // n
    return 1


HEAD_IN_SUB = re.compile(r"問\s*([0-9０-９A-Za-zＡ-Ｚａ-ｚ]{1,3})")


def missing_head_detail(subs, found, sec):
    """どの問の正解を抜けなかったか + 実物の該当行。エラーに足す診断。

    ★ 「書式を ANSWER_IN_TEXT に足すこと」だけでは、元データを見られる人 (塾長)
      と直せる人 (Claude) が別なので直せない。実物の文をエラーごと運ばせる。
    """
    want = []
    for t in subs:
        m = HEAD_IN_SUB.search(str(t))
        want.append(m.group(1) if m else "?")
    got = {h for h, _a in found}
    missing = [h for h in want if h not in got] or ["?"]
    all_lines = [ln.strip() for ln in norm_text(sec.get("solution")).splitlines()
                 if ln.strip()]
    # ★ 抜けた問の行そのものを見せる。「正解」を含む行に絞ってはいけない —
    #   抜けたのは大抵「正解」の書き方が違う行で、絞ると成功した行しか出ない。
    hit = [ln for ln in all_lines
           if any(f"問 {h}" in ln or f"問{h}" in ln for h in missing)]
    show = (hit or [ln for ln in all_lines if "正解" in ln])[:2]
    return (f"抜けた問: {', '.join(missing)}。該当行: "
            + " / ".join(f"「{ln[:70]}」" for ln in show))


# --- 形 D: sub_items + sub_items_choices (世界史 / 日本史) --------------------
def adapt_d_sub_items(doc):
    """大問ごとに「小問の一覧」と「選択肢を詰めた文字列の一覧」を持つ形。

    実物 (世界史):
        sub_items:         ['問 A　下線部ア『唐』に…', …]           5 個
        sub_items_choices: ['① 科挙制度は… ② … ③ … ④ …', …]      5 個
        solution:          '**問 A 正解: ②**⏎唐 — 均田制…'
    """
    specs, errors = [], []
    for i, sec in enumerate(sections_of(doc)):
        if not isinstance(sec, dict):
            return None, None
        subs = sec.get("sub_items")
        chs = sec.get("sub_items_choices")
        if not (isinstance(subs, list) and isinstance(chs, list)):
            return None, None                 # 形 D ではない
        label = section_label(sec, i)
        if len(subs) != len(chs):
            errors.append(f"{label}: 小問 {len(subs)} 個に対し選択肢 {len(chs)} 個。"
                          f"数が合わない")
            continue
        found = answers_in(sec.get("solution"))
        if len(found) != len(subs):
            # ★ どの問が抜けたかと、その実物の文を出す。これが無いと
            #   「書式を足せ」と言われても何を足せばいいか分からない (2026-08-14 実測)。
            errors.append(f"{label}: 小問 {len(subs)} 個に対し solution から抜けた正解が "
                          f"{len(found)} 個。{missing_head_detail(subs, found, sec)}")
            continue
        pts = even_points(sec.get("score"), len(subs))
        for (head, ans), text, ch in zip(found, subs, chs):
            n = choice_count_from_list(ch)
            if n is None:
                errors.append(f"{label} 問{head}: 選択肢の数を数えられない "
                              f"(①から連番で並んでいない): {str(ch)[:60]}")
                continue
            specs.append({"section": label, "head": str(head), "answer": ans,
                          "choice_count": n, "points": pts,
                          "stem": str(text)[:80], "explanation": None})
    if errors:
        # ★ 最初の 1 件で止めない。大問ごとに書式が違うことがあり、1 件ずつ
        #   直すと往復が大問の数だけ要る (実測: 世界史で 1 往復無駄にした)。
        head = errors[:4]
        more = f" (ほか {len(errors) - 4} 件)" if len(errors) > 4 else ""
        return None, " ⏎ ".join(head) + more
    return (specs, None) if specs else (None, None)


# --- 形 E: トップの answer_key が q<大問>_<小問> (物理) ----------------------
QKEY = re.compile(r"^q(\d+)[_-](\d+)$", re.I)


def adapt_e_qkey(doc):
    """answer_key: {q1_1: 2, q1_2: 2, …}。値は 1 起算の選択肢番号。

    ★ 選択肢の数は大問の problem に「①〜④ から選べ」と書いてある。
      書いていなければ数えられないので、その大問は通さない。
    ★ solution にも「問 1 正解 ②」があるので **突き合わせる**。
      2 つの独立した出どころが一致することが、起算が正しい何よりの証拠になる。
    """
    key = (doc or {}).get("answer_key") if isinstance(doc, dict) else None
    if not isinstance(key, dict) or not key:
        return None, None
    parsed = []
    for k, v in key.items():
        m = QKEY.match(str(k).strip())
        if not m:
            return None, None                 # 形 E ではない (ア・イ 方式など)
        n, _circled = to_int(v)
        if n is None:
            return None, f"answer_key の {k} が番号でない ({v!r})"
        parsed.append((int(m.group(1)), int(m.group(2)), n))
    parsed.sort()

    secs = {}
    for i, sec in enumerate(sections_of(doc)):
        if isinstance(sec, dict):
            q, _c = to_int(sec.get("qnum"))
            if q is not None:
                secs[q] = (sec, section_label(sec, i))

    per_sec = {}
    for big, _small, _v in parsed:
        per_sec[big] = per_sec.get(big, 0) + 1

    specs = []
    for big, small, val in parsed:
        if big not in secs:
            return None, f"answer_key に第{big}問があるのに、大問 {big} が本文に無い"
        sec, label = secs[big]
        n, how = section_choice_count(sec)
        if n is None:
            return None, (f"{label}: {NO_CHOICE_COUNT} ({how})。"
                          f"problem の冒頭: 「{norm_text(sec.get('problem'))[:80]}」")
        if not (1 <= val <= n):
            return None, f"{label} 問{small}: 正解 {val} が選択肢 {n} 個の範囲外"
        specs.append({"section": label, "head": str(small), "answer": val,
                      "choice_count": n,
                      "points": even_points(sec.get("score"), per_sec[big]),
                      "stem": f"{label} 問{small}", "explanation": None})

    # ★ solution の「問 1 正解 ②」と突き合わせる。食い違えば通さない。
    mismatch = []
    for big in sorted(per_sec):
        sec, label = secs[big]
        found = answers_in(sec.get("solution"))
        mine = [v for b, _s, v in parsed if b == big]
        if len(found) != len(mine):
            continue                          # 解説の書式が違うだけ。突き合わせは諦める
        for (head, a), b in zip(found, mine):
            if a != b:
                mismatch.append(f"{label} 問{head}: answer_key={b} だが解説は {a}")
    if mismatch:
        return None, ("answer_key と解説の正解が食い違う — "
                      + " / ".join(mismatch[:4]))
    return specs, None


# --- 形 F: answer_key が無く solution にだけ正解がある (化学 / 生物) ---------
NO_CHOICE_COUNT = "選択肢の数が problem から取れない"


def section_choice_count(sec):
    """大問の選択肢の数。範囲表記 → 本文の列挙 の順で実物から取る。

    @returns (数 | None, どう取れた/取れなかったかの説明)
    """
    n = choice_count_from_range(sec.get("problem"))
    if n is not None:
        return n, "「①〜」の範囲表記"
    n, runs = choice_count_from_runs(sec.get("problem"))
    if n is not None:
        return n, f"本文の列挙 ({len(runs)} 列 × {n} 個)"
    if runs:
        return None, f"本文の列挙の長さが揃わない {runs} (問ごとに選択肢数が違う)"
    return None, "範囲表記も列挙も無い"


def adapt_f_solution(doc):
    """大問ごとの solution から「問1 → 正解 ②」を拾う。

    ★ 選択肢の数は problem の「①〜④ から 1 つ選べ」から取る。
      書いていなければ (生物) 通さない。正解だけは分かるので、
      convert_file が「一括入力用」として承知のうえで外す。
    """
    specs = []
    for i, sec in enumerate(sections_of(doc)):
        if not isinstance(sec, dict):
            return None, None
        label = section_label(sec, i)
        found = answers_in(sec.get("solution"))
        n, how = section_choice_count(sec)
        if not found:
            # ★ 正解が 1 つも無い節を「取りこぼし」と断じるのは、
            #   **範囲表記 (「①〜④ から選べ」) があるときだけ**。
            #   列挙だけでは大問と断定できない — 実物の英語R 第0章は
            #   オリエンテーションの攻略手順が ①〜⑤ で列挙されていて、
            #   ここで誤検知した (2026-08-14)。範囲表記は「選べ」という
            #   指示そのものなので、あれば大問で確定。
            if choice_count_from_range(sec.get("problem")) is not None:
                return None, (f"{label}: 「①〜」の範囲表記があるのに solution から"
                              f"正解を抜けない。書式を ANSWER_IN_TEXT に足すこと")
            continue
        if n is None:
            return None, (f"{label}: {NO_CHOICE_COUNT} ({how})。"
                          f"正解は読めているので、一括入力なら使える。"
                          f"problem の冒頭: 「{norm_text(sec.get('problem'))[:80]}」")
        pts = even_points(sec.get("score"), len(found))
        for head, ans in found:
            if not (1 <= ans <= n):
                return None, f"{label} 問{head}: 正解 {ans} が選択肢 {n} 個の範囲外"
            specs.append({"section": label, "head": str(head), "answer": ans,
                          "choice_count": n, "points": pts,
                          "stem": f"{label} 問{head}", "explanation": None})
    return (specs, None) if specs else (None, None)


# --- 正解だけは分かる形 (一括入力用) -----------------------------------------
def answers_only(doc):
    """選択肢の数までは分からないが、正解の並びは分かる場合にそれを返す。

    実物:
      英語R  answer_key: [{number:1, answer:'第1問 問1 = ③ (June 15)'}, …]
      生物   solution に「問 1 → 正解 ②」はあるが選択肢の数が書かれていない
    ★ 登録画面の「正解だけをまとめて入れる」に貼れば 1 分で入る (§17.8)。
    """
    key = (doc or {}).get("answer_key") if isinstance(doc, dict) else None
    out = []
    if isinstance(key, list) and key:
        for x in key:
            v = x.get("answer") if isinstance(x, dict) else x
            found = [CIRCLED[c] for c in norm_text(v) if c in CIRCLED]
            if len(found) != 1:
                return None                   # 丸数字が 0 個か 2 個以上 = 当てられない
            out.append(found[0])
        return out
    for sec in sections_of(doc):
        if isinstance(sec, dict):
            out += [a for _h, a in answers_in(sec.get("solution"))]
    return out or None


# =============================================================================
# 起算の判定
# =============================================================================
def decide_base(values, questions, forced=None):
    """選択肢番号が 0 起算か 1 起算か。

    ★ convert_workbook.detect_base() と同じ理屈:
        1 起算なら 0 は出ない / 0 起算なら「選択肢数」と同じ値は出ない。
      加えて **①②③ が使われていれば 1 起算で確定**する (①は必ず 1 番目)。

    ★ 決められないときは **推測しない**。9 冊しかないので、人が 1 問見れば済む。
      黙って 0 起算にすると、その冊子は全問 1 つずれた正解になり、
      画面はどこも壊れず、生徒だけが不正解になる。
    @returns ('zero'|'one', 理由) または (None, 理由)
    """
    if forced:
        return forced, f"--base {forced} で指定された"
    has_zero = has_max = False
    circled = 0
    for v, q in zip(values, questions):
        n, is_circled = to_int(v)
        if n is None:
            continue
        if is_circled:
            circled += 1
        ch = get_choices(q) or []
        if n == 0:
            has_zero = True
        if ch and n == len(ch):
            has_max = True
    if circled:
        if has_zero:
            return None, f"①②③ が {circled} 問あるのに 0 も出る (元データが壊れている)"
        return "one", f"①②③ 表記が {circled} 問 (① は必ず 1 番目なので 1 起算で確定)"
    if has_zero and has_max:
        return None, "0 も「選択肢数と同じ値」も出る (元データが壊れている)"
    if has_zero:
        return "zero", "正解に 0 がある (1 起算なら出ない)"
    if has_max:
        return "one", "正解に「選択肢数と同じ値」がある (0 起算なら出ない)"
    return None, ("0 も「選択肢数と同じ値」も出ないので決められない。"
                  "実物を 1 問見て --base one / --base zero を付けること")


# =============================================================================
# 1 冊ぶんの変換
# =============================================================================
def build_choice_question(q, number, raw_answer, shift):
    ch = get_choices(q)
    n, _ = to_int(raw_answer)
    if n is None:
        return None, f"問{number}: 正解が番号でない ({raw_answer!r})"
    n += shift
    if not (1 <= n <= len(ch)):
        return None, f"問{number}: 正解 {raw_answer} (+{shift}) が選択肢 {len(ch)} 個の範囲外"
    if len(ch) > 10:
        return None, f"問{number}: 選択肢が {len(ch)} 個 (上限 10)"
    out = {
        "number": number,
        "page": None,                          # YAML に「何問目が何ページか」が無い
        "points": get_points(q) or 1,
        "answer_type": "choice",
        "choice_count": len(ch),
        "correct_answer": str(n),
        "accepted_answers": [],
        "unit_tag": None,
        "explanation": get_explanation(q),
    }
    out["_preview"] = {"stem": (get_stem(q) or "")[:80],
                       "choices": [str(c)[:40] for c in ch],
                       "correct_text": str(ch[n - 1])[:40]}
    return out, None


def is_fill_in_marks(doc):
    """数学の穴埋めマーク式か。取り込めないと分かっている形。

    実物 (数学IA / IIB):
        sections[].answer_key: str = 'ア = 6 / イ = 4 / ウエ = −1 / …'
        選択肢そのものが無い (空欄に数字を書き込む)
    """
    for sec in sections_of(doc):
        if isinstance(sec, dict) and isinstance(sec.get("answer_key"), str):
            if re.search(r"[ア-ン]\s*=", sec["answer_key"]):
                return True
    return False


FILL_IN_REASON = (
    "穴埋めマーク式。選択肢が無く、answer_key は 'ア = 6 / イ = 4 / ウエ = −1' の"
    "自由文で、空欄 1 つずつに数字を書き込む形。冊子受験アプリは 1 問 1 答 "
    "(選択式か記述) しか持てないうえ、validateQuestions は数字だけの記述解答を弾く "
    "(exam-book-admin-model.mjs:143 — 選択肢の取りこぼしを捕まえる砦)。"
    "アプリの形式に合わないので **紙で配るのが正解**")


def crosscheck_with_answer_key(doc, out):
    """D/F で solution から作った正解を、トップの answer_key と突き合わせる。

    ★ 英語R は正解の出どころが 2 つある (solution と、トップの answer_key)。
      E (物理) と同じ理屈で、独立した 2 系統が全問一致することを要求する。
      一致すれば抜き間違いは構造的にあり得ない。
      トップに answer_key が無い冊子 (化学・生物・世界史・日本史) は対象外 —
      answers_only が solution へ落ちて同じ出どころ同士の比較になり、
      「一致」が何も証明しなくなるため。
    @returns (突き合わせたか, エラー文 | None)
    """
    key = (doc or {}).get("answer_key") if isinstance(doc, dict) else None
    if not isinstance(key, list) or not key:
        return False, None
    vals = answers_only(doc)                   # answer_key 側だけから読む
    if not vals:
        return False, None
    if len(vals) != len(out):
        return True, (f"solution から {len(out)} 問取れたが answer_key は "
                      f"{len(vals)} 個。数が合わない")
    diff = [f"問{q['number']}: solution={q['correct_answer']} / answer_key={v}"
            for q, v in zip(out, vals) if str(v) != q["correct_answer"]]
    if diff:
        return True, ("solution と answer_key の正解が食い違う — "
                      + " / ".join(diff[:4])
                      + (f" (ほか {len(diff) - 4} 問)" if len(diff) > 4 else ""))
    return True, None


def build_from_specs(specs):
    """アダプタが出した仕様 → アプリの設問。

    ★ 正解は必ず 1 起算の丸数字か、範囲を照合済みの整数として渡ってくる。
      ここで起算をいじらない (いじる場所が 2 つあると片方だけ直して壊す)。
    """
    out, problems = [], []
    for s in specs:
        n, cc = s["answer"], s["choice_count"]
        if not (1 <= n <= cc):
            problems.append(f"{s['section']} 問{s['head']}: "
                            f"正解 {n} が選択肢 {cc} 個の範囲外")
            continue
        q = {
            "number": len(out) + 1,
            "page": None,                      # YAML に「何問目が何ページか」が無い
            "points": s.get("points") or 1,
            "answer_type": "choice",
            "choice_count": cc,
            "correct_answer": str(n),
            "accepted_answers": [],
            "unit_tag": s["section"] or None,
            "explanation": s.get("explanation"),
        }
        q["_preview"] = {"stem": s.get("stem") or "", "choices": [],
                         "correct_text": f"{s['section']} 問{s['head']} → {n} 番"}
        out.append(q)
    return out, problems


def convert_file(path, forced_base=None):
    """@returns (bundle | None, 問題の一覧, 承知のうえで外したか)

    ★ 3 つめが要る。「今は入れられないと分かっていて外す」ものと
      「変換に失敗した」ものを同じ扱いにすると、前者で毎回ゲートが赤くなり、
      赤いのが普通になって本物の失敗を見落とす。
    """
    name = os.path.basename(path)
    subject = subject_of(path)
    try:
        doc = load_yaml(path)
    except Exception as e:
        return None, [f"{name}: YAML が読めない ({e})"], False

    # --- 取り込めないと分かっている形は先に外す -----------------------------
    if is_fill_in_marks(doc):
        return None, [f"{name}: [数学] {FILL_IN_REASON}"], True

    # --- A: 設問が choices を持ち、トップの answer_key と番号で対応 (国語) ---
    questions = harvest(doc)
    if questions:
        values, err = adapt_a_top_level(doc, questions)
        if err:
            return None, [f"{name}: [形A] {err}"], False
        if values is None:
            return None, [f"{name}: 選択肢を持つ設問は {len(questions)} 問あるが "
                          f"answer_key が見つからない。--probe で構造を見ること"], False
        base, why = decide_base(values, questions, forced_base)
        if base is None:
            return None, [f"{name}: 選択肢番号の起算を決められない — {why}"], False
        shift = 0 if base == "one" else 1
        # 解説は answer_key 側に付いている (設問側には無い)
        exps = explanations_from_key(doc, questions)
        out, problems = [], []
        for i, (q, val) in enumerate(zip(questions, values)):
            built, bad = build_choice_question(q, len(out) + 1, val, shift)
            if built is None:
                problems.append(bad)
            else:
                if built["explanation"] is None and i < len(exps):
                    built["explanation"] = exps[i]
                out.append(built)
        return finish(path, subject, out, problems, "A", f"{base} — {why}"), [], False

    # --- D / E / F: 設問の一覧そのものが無い形 -------------------------------
    for fmt, fn in (("D", adapt_d_sub_items), ("E", adapt_e_qkey),
                    ("F", adapt_f_solution)):
        specs, err = fn(doc)
        if err:
            # ★ 「選択肢の数が元データに無い」(生物・英語R) は直せない欠落で、
            #   正解が読めているなら一括入力 (§17.8) で入れるのが正しい。
            #   失敗ではなく承知のうえの除外にする (毎回 exit 1 になっていると
            #   赤いのが普通になり、本物の失敗を見落とす)。
            if NO_CHOICE_COUNT in err and answers_only(doc):
                return None, [f"{name}: [形{fmt}] {err} → 下の「正解だけを流し込む用」"
                              f"に並びを出した"], True
            return None, [f"{name}: [形{fmt}] {err}"], False
        if specs:
            out, problems = build_from_specs(specs)
            note = "one — 丸数字 (①は必ず 1 番目) なので 1 起算で確定"
            if fmt == "E":
                note = "one — answer_key と解説の 2 つが一致 (独立した裏取り)"
            else:
                checked, err2 = crosscheck_with_answer_key(doc, out)
                if err2:
                    return None, [f"{name}: [形{fmt}] {err2}"], False
                if checked:
                    note += " + answer_key と全問一致 (独立した裏取り)"
            return finish(path, subject, out, problems, fmt, note), [], False

    return None, [f"{name}: 正解の在り処がどの形にも当たらない。"
                  f"--probe で構造を見ること (推測はしない)"], False


def bulk_key_for(path):
    """変換しきれない冊子でも「正解の並び」だけは出す。

    ★ 選択肢の数が元データに書かれていない冊子 (生物・英語R) は JSON では
      取り込めないが、正解は読めている。登録画面の「正解だけをまとめて入れる」
      (§17.8) に貼れば、手入力 7 分が 1 分になる。
    @returns (科目, [正解…]) または None
    """
    try:
        doc = load_yaml(path)
    except Exception:
        return None
    if is_fill_in_marks(doc):
        return None                            # 数学は選択式ですらない
    vals = answers_only(doc)
    if not vals:
        return None
    return subject_of(path), vals


def explanations_from_key(doc, questions):
    """answer_key[].explanation を設問の並びに合わせて返す (国語)。

    ★ 解説を取り落としていた (2026-08-14)。設問側に explanation が無く、
      answer_key 側にあるので、get_explanation では拾えなかった。
      解説が無くても採点は動くので **静かに欠けるのがいちばん危ない**。

    ★ 番号で当てるのは **両側の番号が一意なときだけ**。設問の number は
      大問ごとに 1 から振り直されている可能性があり (問1〜問6 × 4 大問)、
      重複した番号で引くと最初の大問の解説が全大問に付く。
      決められないときは並び順 (adapt_a_top_level と同じ順) で付ける。
    """
    key = (doc or {}).get("answer_key") if isinstance(doc, dict) else None
    if not isinstance(key, list):
        return []
    ordered, by, knums = [], {}, []
    for i, x in enumerate(key):
        if not isinstance(x, dict):
            return []
        exp = x.get("explanation") or x.get("解説")
        exp = str(exp).strip() if exp else None
        num = next((x[k] for k in NUM_KEYS if k in x), i + 1)
        ordered.append(exp)
        knums.append(num)
        by[num] = exp
    qnums = [get_number(q) for q in questions]
    if (len(set(knums)) == len(knums) and len(set(qnums)) == len(qnums)
            and all(n in by for n in qnums)):
        return [by[n] for n in qnums]
    return ordered[:len(questions)]


def short_path(path):
    """同じ名前の YAML が 2 か所にあるので、末尾 3 段まで残して見分けられるようにする。

    ★ ファイル名だけにしていたら、国語が 2 冊出たときに **どちらがどちらか
      分からず**、--out の書き出しも同じ名前で上書きし合っていた (2026-08-14)。
    """
    parts = os.path.normpath(path).split(os.sep)
    return "/".join(parts[-3:]) if len(parts) >= 3 else path


def finish(path, subject, questions, problems, fmt, base_note):
    preview = [dict(q["_preview"], number=q["number"],
                    correct_answer=q["correct_answer"])
               for q in questions if q.get("_preview")]
    for q in questions:
        q.pop("_preview", None)
    return {
        "source": short_path(path),
        "subject_name": subject,
        "format": fmt,
        "base_note": base_note,
        "preview": preview,
        "book": {
            "title": f"共通テスト{subject} マーク式" if subject
                     else os.path.splitext(os.path.basename(path))[0],
            "subject": SUBJECT_BY_NAME.get(subject or "", "other"),
            "level": None,
            "time_limit_min": None,
        },
        "questions": questions,
        "skipped": problems,
    }


# =============================================================================
# --probe : 推測しないで構造だけ出す
# =============================================================================
def inventory(doc):
    """木を歩いて「どの場所に どんなキーがあるか」を全部集める。

    ★ 1 件目だけを見せる形にしていたら、選択肢のキー名が分からず
      「選択肢を持つ設問が 1 つも見つからない」としか言えなかった (2026-08-14)。
      推測しない作りにしている以上、**キー名は全部見せる**のが probe の仕事。
    @returns {場所: {"n": その場所の dict の数, "keys": {キー: (型, 見本)}}}
    """
    inv = {}

    def walk(o, p):
        if isinstance(o, dict):
            e = inv.setdefault(p or "(トップ)", {"n": 0, "keys": {}})
            e["n"] += 1
            for k, v in o.items():
                if isinstance(v, dict):
                    e["keys"].setdefault(k, ("dict", ""))
                    walk(v, f"{p}.{k}")
                elif isinstance(v, list):
                    kinds = sorted({type(x).__name__ for x in v})
                    e["keys"].setdefault(k, (f"list[{len(v)}] of {'/'.join(kinds) or '空'}",
                                             "" if any(isinstance(x, (dict, list)) for x in v)
                                             else " | ".join(str(x)[:24] for x in v[:3])))
                    for x in v[:80]:
                        walk(x, f"{p}.{k}[]")
                else:
                    prev = e["keys"].get(k)
                    if prev is None or not prev[1]:
                        e["keys"][k] = (type(v).__name__,
                                        str(v)[:70].replace("\n", "⏎"))
        elif isinstance(o, list):
            for x in o[:80]:
                walk(x, f"{p}[]")

    walk(doc, "")
    return inv


def probe(path):
    print(f"\n=== {os.path.basename(path)} ===")
    print(f"    {path}")
    try:
        doc = load_yaml(path)
    except Exception as e:
        print(f"  ✗ YAML が読めない: {e}")
        return

    inv = inventory(doc)
    for place, e in list(inv.items())[:14]:
        print(f"  {place}  ({e['n']} 個)")
        for k, (t, sample) in list(e["keys"].items())[:24]:
            line = f"      {k}: {t}"
            if sample:
                line += f" = {sample}"
            print(line[:150])
    if len(inv) > 14:
        print(f"  … 場所があと {len(inv) - 14} 種類 (深すぎるので省略)")

    qs = harvest(doc)
    print(f"  --- 選択肢を持つ設問: {len(qs)} 問")
    if qs:
        q = qs[0]
        print(f"      キー: {sorted(q.keys())}")
        print(f"      設問文: {(get_stem(q) or '(見つからない)')[:60]!r}")
        print(f"      選択肢: {len(get_choices(q))} 個")
        print(f"      解説: {(get_explanation(q) or '(見つからない)')[:80]!r}")
    if is_fill_in_marks(doc):
        print("  --- 数学の穴埋めマーク式 (取り込めない形)")
    v, e = adapt_a_top_level(doc, qs) if qs else (None, None)
    print("  --- A choices + answer_key: " + ("該当せず" if v is None and not e
                                              else (f"✗ {e}" if e else f"○ {len(v)} 個")))
    for name, fn in (("D sub_items + 選択肢文字列", adapt_d_sub_items),
                     ("E answer_key (q1_1 形式)", adapt_e_qkey),
                     ("F solution から抜く", adapt_f_solution)):
        v, e = fn(doc)
        print(f"  --- {name}: " + ("該当せず" if v is None and not e
                                   else (f"✗ {e}" if e else f"○ {len(v)} 個")))
    vals = answers_only(doc)
    if vals:
        print(f"  --- 正解の並びだけなら {len(vals)} 個読める (一括入力用)")


# =============================================================================
def report(bundles, problems, excluded, meta, bulk=()):
    """@returns 落とすべきか (True なら exit 1)

    ★ 「印字はしたが exit 0」を作らないこと。CLAUDE.md が INCONSISTENT と呼んで
      いる無力化そのもので、★付きで出した違反は必ず終了コードに出す。
    """
    fatal = bool(problems)
    total = sum(len(b["questions"]) for b in bundles)
    skipped = sum(len(b["skipped"]) for b in bundles)
    print("=== 共通テスト 9 科目 → 冊子アプリ 変換 ===")
    print(f"  変換できた: {len(bundles)} 冊 / {total} 問")
    print(f"  変換できなかった設問: {skipped} 問")

    # ★ 承知のうえで外したものを **いちばん上** に出す。下に埋めると
    #   「9 冊ぶん終わった」に見えて、2 冊足りないことに気づけない。
    if excluded:
        print(f"\n=== 承知のうえで外した冊子 ({len(excluded)} 件) ===")
        for x in excluded:
            print(f"  [除外] {x}")

    if bundles:
        print("\n  冊子ごと:")
        for b in bundles:
            m = meta.get(b["subject_name"] or "", {})
            pages = f"PDF {m['pages']}頁" if m.get("pages") else "PDF 不明"
            print(f"    {(b['subject_name'] or '?'):8} {len(b['questions']):3} 問  "
                  f"形{b['format']}  {pages}  起算: {b['base_note']}")
            print(f"             {b['source']}")

    # ★ 同じ科目の YAML が 2 本以上あると、冊子も 2 冊できてしまう。
    #   中身が同じか違うかは機械には決められないので、人に選ばせる。
    dup = {}
    for b in bundles:
        dup.setdefault(b["subject_name"] or "?", []).append(b)
    dup = {k: v for k, v in dup.items() if len(v) > 1}
    if dup:
        print(f"\n=== 同じ科目の YAML が複数ある ({len(dup)} 科目) — どちらを使うか選ぶこと ===")
        print("   両方取り込むと同じ題名の冊子が 2 冊できます。")
        for subj, bs in dup.items():
            print(f"   {subj}:")
            for b in bs:
                pv = b["preview"][0]["correct_text"] if b["preview"] else ""
                print(f"     - {b['source']}  ({len(b['questions'])} 問)  例: {pv}")
        print("   ★ 片方だけ入れたいときは科目名でなくフォルダ名で絞れます:")
        print("     python3 scripts/book_exam/convert_kyotsu_yaml.py <フォルダ名の一部> --out DIR")

    # ★ 別セッションが数えた問数と突き合わせる。合わなければ抜けている。
    bad_count = []
    for b in bundles:
        want = EXPECTED_COUNT.get(b["subject_name"] or "")
        if want and want != len(b["questions"]):
            bad_count.append(f"{b['subject_name']}: {len(b['questions'])} 問 (想定 {want} 問)")
    if bad_count:
        fatal = True                 # ★ 拾い落としの疑い。黙って通してはいけない
        print(f"\n=== ★ 問数が想定と違う ({len(bad_count)} 件) ===")
        print("   設問を拾い落としているか、想定のほうが古い。実物と数えて確かめること。")
        print("   数え直して想定のほうが古かったら EXPECTED_COUNT を直す。")
        for x in bad_count:
            print(f"     {x}")

    # ★ 変換しきれなかった冊子でも「正解の並び」だけは出す。
    #   登録画面の「正解だけをまとめて入れる」に貼れば 1 分で入る (§17.8)。
    if bulk:
        print(f"\n=== 正解だけを流し込む用 ({len(bulk)} 冊) ===")
        print("   選択肢の数が元データに無いので JSON では取り込めないが、正解は読めている。")
        print("   登録画面で設問の行を作ってから「正解だけをまとめて入れる」に貼れます。")
        for subj, vals in bulk:
            print(f"   {subj or '?'} ({len(vals)} 問)")
            print(f"     {' '.join(str(v) for v in vals)}")

    if problems:
        print(f"\n=== ★ 変換できなかったファイル ({len(problems)} 件) ===")
        print("   ★ 推測しないで飛ばしている。--probe で構造を見て直すこと。")
        for p in problems:
            print(f"     - {p}")

    if bundles:
        print("\n=== 起算の確認用 (各冊 1 問目) — 実物と 1 件だけ照合してください ===")
        for b in bundles:
            if not b["preview"]:
                continue
            pv = b["preview"][0]
            print(f"  {b['subject_name']}  問{pv['number']}: {pv['stem']}")
            print(f"    → 正解 {pv['correct_answer']} 番 = 「{pv['correct_text']}」")

    if skipped:
        fatal = True
        print(f"\n★ {skipped} 問を変換できていない:")
        for b in bundles:
            for w in b["skipped"][:5]:
                print(f"     {b['subject_name']}: {w}")

    return fatal


# =============================================================================
# --selftest : 見本 YAML で 3 通りを全部通す
# =============================================================================
def selftest():
    """fixtures_kyotsu/*.yaml を変換して、期待どおりかを見る。

    ★ 見本は 2026-08-14 に **実機の --probe 出力から書き起こした**もの。
      それでも実物の全文ではないので、通ることが証明するのは
      「実物と同じ形のアダプタが動く」ことまで。実物での最終確認は
      変換結果の preview を人が 1 冊 1 問照合すること。
    """
    want = {
        # ファイル名: (問数, 形, 1 問目の正解)
        "sample_a_kokugo": (3, "A", "5"),
        "sample_d_sub_items": (3, "D", "2"),
        "sample_e_qkey": (4, "E", "2"),
        "sample_f_solution": (4, "F", "2"),
    }
    # ★ 「取り込めないと分かって外す」を検査する。通ってしまったら砦が外れている。
    refuse = {
        "sample_math_fill_in": "穴埋めマーク式",
        "sample_g_answers_only": "一括入力",
    }

    files = sorted(glob.glob(os.path.join(FIXTURES, "*.yaml")))
    if len(files) != len(want) + len(refuse):
        print(f"✗ 見本が {len(files)} 本 (想定 {len(want) + len(refuse)} 本)")
        return 1
    bad = []
    for f in files:
        key = os.path.splitext(os.path.basename(f))[0]
        b, errs, excluded = convert_file(f)

        if key in refuse:
            if b is not None:
                bad.append(f"{key}: 取り込めないはずの形が変換できてしまった "
                           f"(砦が外れている)")
            elif not excluded:
                bad.append(f"{key}: 除外ではなく失敗として扱われた — {errs[0] if errs else '?'}")
            elif refuse[key] not in (errs[0] if errs else ""):
                bad.append(f"{key}: 理由に {refuse[key]!r} が出ない — {errs[0] if errs else '?'}")
            continue

        if key not in want:
            bad.append(f"{key}: 想定表に無い見本")
            continue
        n_want, fmt_want, first_want = want[key]
        if b is None:
            bad.append(f"{key}: 変換できなかった — {errs[0] if errs else '?'}")
            continue
        if b["skipped"]:
            bad.append(f"{key}: {len(b['skipped'])} 問落ちた — {b['skipped'][0]}")
        if len(b["questions"]) != n_want:
            bad.append(f"{key}: {len(b['questions'])} 問 (想定 {n_want} 問)")
        if b["format"] != fmt_want:
            bad.append(f"{key}: 形{b['format']} (想定 形{fmt_want})")
        elif b["questions"] and b["questions"][0]["correct_answer"] != first_want:
            bad.append(f"{key}: 1 問目の正解 {b['questions'][0]['correct_answer']} "
                       f"(想定 {first_want})")

    # ★ 国語: 解説が answer_key 側から設問に付くこと。
    #   設問の number は大問ごとに振り直されている (見本もわざとそうしてある) ので、
    #   番号で引くと 3 問目に 1 問目の解説が付く。並び順で付いていることを見る。
    b, _e, _x = convert_file(os.path.join(FIXTURES, "sample_a_kokugo.yaml"))
    if b:
        exps = [q.get("explanation") or "" for q in b["questions"]]
        if not all(exps):
            bad.append("国語: answer_key 側の解説が設問に付いていない (取り落とし)")
        elif "雨上がり" not in exps[2]:
            bad.append(f"国語: 3 問目に別の問の解説が付いている (番号で引いた疑い) "
                       f"— {exps[2][:40]!r}")

    # ★ 起算を決められない値で推測しないこと (全問ずれても画面は壊れないため)
    doc = load_yaml(os.path.join(FIXTURES, "sample_a_kokugo.yaml"))
    qs = harvest(doc)
    base, _why = decide_base([2, 2, 2], qs)     # 0 も len(choices) も出ない値
    if base is not None:
        bad.append("起算を決められないはずの値で決めてしまった "
                   "(decide_base が甘い。全問ずれても気づけない)")

    # ★ answer_key の形。実物は {number, answer} の一覧だが、素の並びも受ける。
    if key_as_list([3, 1, 4]) != [(1, 3), (2, 1), (3, 4)]:
        bad.append("answer_key が素の並びのとき読めていない")
    if key_as_list([{"number": 7, "answer": "②"}]) != [(7, "②")]:
        bad.append("answer_key が {number, answer} の一覧のとき読めていない (実物の形)")
    if key_as_list([{"number": 1, "memo": "x"}]) != []:
        bad.append("正解のキーが無い dict を推測で通してしまった")

    # ★ E: answer_key と解説の突き合わせ。食い違わせたら落ちるはず。
    #   これが素通りすると、起算がずれても「2 つの出どころが一致」と嘘をつく。
    doc_e = load_yaml(os.path.join(FIXTURES, "sample_e_qkey.yaml"))
    doc_e["answer_key"]["q1_1"] = 4              # 解説は ② と言っている
    specs, e = adapt_e_qkey(doc_e)
    if specs is not None or not e or "食い違う" not in e:
        bad.append(f"E: answer_key と解説が食い違うのに通してしまった — {e!r}")

    # ★ D: 選択肢の数は「①から連番」だけを数えること。
    if choice_count_from_list("① a ② b ③ c ④ d") != 4:
        bad.append("D: 連番の選択肢を数えられない")
    if choice_count_from_list("② a ③ b") is not None:
        bad.append("D: ①から始まらないのに数えてしまった")
    if choice_count_from_list("① a ② b ④ d") is not None:
        bad.append("D: 番号が飛んでいるのに数えてしまった")

    # ★ 解説から正解を抜く形 — 実機で確認した 4 科目ぶんの書式を全部
    for label, text, head_want, ans_want in (
            ("化学",   "<strong>問1 → 正解 ②</strong>",       "1", 2),
            ("物理",   r"<strong>$\text{問 1}$ 正解 ②</strong>", "1", 2),
            ("世界史", "**問 A 正解: ②**",                     "A", 2),
            ("日本史", "問 1　正解: **①**　中大兄皇子",        "1", 1),
            ("全角見出し", "**問 Ｄ 正解: ③**",                "Ｄ", 3),
            ("の入り", "問 C の正解: ②",                       "C", 2)):
        got = answers_in(text)
        if got != [(head_want, ans_want)]:
            bad.append(f"{label} の書式 {text!r} から正解を抜けない (got {got})")

    # ★ 「正解 ②」の丸数字だけを拾い、誤答の説明の素の数字は拾わないこと
    if answers_in("問1 → 正解 ②。誤答 3 は問 4 と混同したもの。") != [("1", 2)]:
        bad.append("誤答の説明の数字まで拾っている (静かにずれる)")
    # ★ 素の数字は正解としても拾わない。丸数字と違い起算を確定できないので、
    #   拾った瞬間に「1 つずれても気づけない」経路が開く。
    if answers_in("問2 正解 4") != []:
        bad.append("素の数字を正解として拾ってしまった (起算を確定できないのに)")
    # ★ 正誤問題の注記 (実物: 世界史 問E)
    if answers_in("**問 E 正解(誤り): ③**") != [("E", 3)]:
        bad.append("「正解(誤り): ③」の注記付きを抜けない (実物の世界史 問E の形)")

    # ★ 本文の列挙から選択肢数を数える (実物: 物理 第2問は範囲表記が無い)
    if choice_count_from_runs("① a ② b ③ c ④ d 問2 ① w ② x ③ y ④ z")[0] != 4:
        bad.append("列挙 (run) から選択肢数を数えられない")
    if choice_count_from_runs("① a ② b ③ c 問2 ① w ② x ③ y ④ z")[0] is not None:
        bad.append("長さの違う列挙が混ざるのに 1 つの数に決めてしまった "
                   "(問ごとに選択肢数が違うのに)")
    if choice_count_from_runs("参照は ① を見よ")[0] is not None:
        bad.append("本文の参照の ① 1 個を列挙と数えてしまった")

    # ★ F: 「①〜④」がある大問から正解を抜けないときに黙って飛ばさないこと。
    #   これが素通りすると、解説の書式が 1 大問だけ違ったとき問数が静かに減る。
    doc_f = load_yaml(os.path.join(FIXTURES, "sample_f_solution.yaml"))
    doc_f["sections"][1]["solution"] = "この大問の解説は準備中。"   # 正解が無い
    specs, e = adapt_f_solution(doc_f)
    if specs is not None or not e or "抜けない" not in e:
        bad.append(f"F: 大問から正解を抜けないのに黙って飛ばした (問数が減る) — {e!r}")

    # ★ 選択肢が数えられない冊子でも、正解の並びだけは救い出せること
    bk = bulk_key_for(os.path.join(FIXTURES, "sample_g_answers_only.yaml"))
    if not bk or bk[1] != [3, 1, 4]:
        bad.append(f"answers-only 型の正解の並びを救い出せない (got {bk!r})")
    if bulk_key_for(os.path.join(FIXTURES, "sample_math_fill_in.yaml")) is not None:
        bad.append("数学の穴埋めから正解の並びを出してしまった (選択式ではないのに)")

    # ★ F: solution とトップ answer_key の突き合わせ (実物の英語R は両方持つ)。
    #   食い違わせたら落ちるはず。素通りすると「一致」が嘘になる。
    doc_f2 = load_yaml(os.path.join(FIXTURES, "sample_f_solution.yaml"))
    specs_f, _e = adapt_f_solution(doc_f2)
    out_f, _p = build_from_specs(specs_f)
    doc_f2["answer_key"] = [{"number": i + 1, "answer": "①"} for i in range(len(out_f))]
    applied, err2 = crosscheck_with_answer_key(doc_f2, out_f)
    if not applied or not err2 or "食い違う" not in err2:
        bad.append(f"F: solution と answer_key が食い違うのに通してしまった — {err2!r}")
    # 一致する answer_key なら通ること
    doc_f2["answer_key"] = [{"number": i + 1, "answer": "①②③④⑤"[int(q["correct_answer"]) - 1]}
                            for i, q in enumerate(out_f)]
    applied, err2 = crosscheck_with_answer_key(doc_f2, out_f)
    if not applied or err2:
        bad.append(f"F: 一致しているのに突き合わせが落とした — {err2!r}")

    # ★ アプリと同じ検証器を通す
    try:
        from convert_workbook import validate_with_real_model
        bundles = [b for b in (convert_file(f)[0] for f in files) if b]
        checked, verr = validate_with_real_model(bundles)
        if verr:
            print(f"  [selftest] 検証器を回せなかった: {verr}")
        elif checked:
            for c in checked:
                if not c["ok"]:
                    bad.append(f"{c['source']}: 検証器を通らない — {c['errors'][:2]}")
    except Exception as e:
        bad.append(f"検証器を呼べなかった: {e}")

    if bad:
        print("✗ 共通テスト変換の自己検査で問題:")
        for b in bad:
            print(f"    - {b}")
        return 1
    print(f"[ok] 共通テスト変換の自己検査 — 実機の --probe から起こした見本 {len(files)} 本 "
          f"(形 A/D/E/F + 除外 2) を変換し、アプリと同じ検証器を通過")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("filter", nargs="*", help="科目名で絞る (部分一致)")
    ap.add_argument("--root", default=DEFAULT_ROOT, help=f"元データの場所 (既定 {DEFAULT_ROOT})")
    ap.add_argument("--out", help="書き出し先ディレクトリ")
    ap.add_argument("--probe", action="store_true", help="構造を出すだけ (変換しない)")
    ap.add_argument("--base", choices=["one", "zero"], help="選択肢番号の起算を指定する")
    ap.add_argument("--selftest", action="store_true", help="見本で自己検査する")
    a = ap.parse_args()

    if a.selftest:
        return selftest()

    files = find_files(a.root)
    if a.filter:
        files = [f for f in files if any(k in f for k in a.filter)]
    if not files:
        print(f"✗ {a.root} に共通テストの YAML が見つかりません。")
        print("  --root で場所を指定してください。想定している形:")
        print("    <root>/<教科>/<xxx-textbook-pdf>/samples/2026-06-03_共通テスト◯◯_マーク式.yaml")
        return 1

    meta = print_metadata_table()
    if a.probe:
        print(f"=== 構造を調べる ({len(files)} 本) — 何も書き出しません ===")
        for f in files:
            probe(f)
        if meta:
            print("\n=== 組版済み PDF (lesson-prints/_metadata.json より) ===")
            for s, m in sorted(meta.items()):
                print(f"  {s:8} {m['pages']:3} 頁  {m['kb']:5} KB  "
                      f"小問 {m['sub_questions'] or '?'}  {m['pdf']}")
        return 0

    bundles, problems, excluded, bulk = [], [], [], []
    for f in files:
        b, errs, is_excluded = convert_file(f, a.base)
        (excluded if is_excluded else problems).extend(errs)
        if b:
            bundles.append(b)
        else:
            # ★ 変換できなくても、正解の並びだけは救い出せることがある
            #   (数学の穴埋めは bulk_key_for 自身が断る)
            bk = bulk_key_for(f)
            if bk:
                bulk.append(bk)

    fatal = report(bundles, problems, excluded, meta, bulk)

    if a.out and bundles:
        os.makedirs(a.out, exist_ok=True)
        for b in bundles:
            name = re.sub(r"[^\w.-]", "_", b["source"]) + ".json"
            with open(os.path.join(a.out, name), "w", encoding="utf-8") as f:
                json.dump(b, f, ensure_ascii=False, indent=1)
        print(f"\n  {a.out} に {len(bundles)} 件書き出しました "
              f"(登録画面の「JSON をまとめて読み込む」で取り込めます)")

    # ★ 1 冊でも落ちていれば失敗。9 冊のうち 6 冊だけ入って
    #   「終わった」に見えるのがいちばん危ない。
    #   承知のうえで外した冊子 (形 B) は理由が書いてあるので落とさない。
    return 1 if fatal else 0


if __name__ == "__main__":
    sys.exit(main())
