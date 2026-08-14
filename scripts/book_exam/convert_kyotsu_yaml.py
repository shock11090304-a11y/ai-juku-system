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

# ★ 別セッションの調査報告。変換後にこの数と突き合わせる。
#   合わなければ「抜けている」ということなので必ず落とす。
EXPECTED_COUNT = {"英語R": 22, "国語": 24, "物理": 20}

# 正解の在り処 (上の表)。--probe の見立てと食い違ったら警告を出す。
EXPECTED_FORMAT = {
    "英語R": "A", "国語": "A", "物理": "A",
    "数学IA": "B", "数学IIB": "B",
    "化学": "C", "生物": "C", "日本史": "C", "世界史": "C",
}

CIRCLED = {c: i + 1 for i, c in enumerate("①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳")}
ZENKAKU = {c: i for i, c in enumerate("０１２３４５６７８９")}

# 解説本文から正解を抜く形 (書式が科目ごとに違うので複数持つ)。
#   「問1 → 正解 ②」「**問 A 正解: ②**」「問3 正解 4」など。
#   ★ 「正解」の直後に来る番号だけを拾う。誤答の説明にも番号は出るので、
#     語を挟まない位置に限る。
ANSWER_IN_TEXT = [
    re.compile(r"問\s*([0-9０-９A-Za-z]+)\s*(?:→|➡|:|：)?\s*正解\s*(?:は|:|：)?\s*"
               r"([①-⑳]|[0-9０-９]{1,2})"),
    re.compile(r"正解\s*(?:は|:|：)\s*([①-⑳]|[0-9０-９]{1,2})"),
]


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
    return sorted(set(out))


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


def adapt_b_per_section(doc, questions):
    """B: 大問ごとの answer_key: (ア・イ… の空欄記号 → 値)。

    ★ 共通テストの数学はマーク欄 1 つが 1 つの答え。設問 (小問) と 1 対 1 では
      ないので、**空欄記号ごとに 1 問**として出す。記号は題意の一部なので
      unit_tag に残し、生徒には「ア に入る値」を書かせる。
    """
    keys = []

    def walk(o):
        if isinstance(o, dict):
            ak = o.get("answer_key")
            if isinstance(ak, dict) and ak:
                sec = o.get("id") or o.get("title") or o.get("section") or ""
                for sym, val in ak.items():
                    keys.append((str(sec).strip(), str(sym).strip(), val))
                return
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(doc)
    if not keys:
        return None, None                     # 形 B ではない
    # 記号がカタカナ (ア〜ン) でなければ、これは想定した形ではない
    kata = [s for _sec, s, _v in keys if re.fullmatch(r"[ア-ン]+", s)]
    if len(kata) < len(keys) * 0.8:
        return None, (f"大問ごとの answer_key はあるが、記号がカタカナでない "
                      f"(例 {keys[0][1]!r})。想定した ア・イ 方式ではない")
    return keys, None


def adapt_c_from_text(doc, questions, subject):
    """C: answer_key が無い。解説本文から「正解 ②」を抜く。

    ★ 書式が科目ごとに違うので、**設問ごとに自分の解説から抜く**。
      文書全体を舐めて順番に当てると、誤答の説明を拾って静かにずれる。
    """
    got, missing = [], []
    for i, q in enumerate(questions):
        exp = get_explanation(q) or ""
        val = None
        for pat in ANSWER_IN_TEXT:
            m = pat.search(exp)
            if m:
                val = m.group(m.lastindex)    # 最後の group が正解の番号
                break
        if val is None:
            missing.append(i + 1)
        got.append(val)
    if len(missing) == len(questions):
        return None, None                     # 形 C でもない (1 つも抜けない)
    if missing:
        return None, (f"解説から正解を抜けなかった設問が {len(missing)} 問 "
                      f"(問 {', '.join(str(x) for x in missing[:8])}"
                      f"{' …' if len(missing) > 8 else ''})。"
                      f"{subject} の書式を ANSWER_IN_TEXT に足すこと")
    return got, None


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


def mark_box_reason(keys):
    """形 B を取り込めない理由。★ここを消して通すなら検証器の設計から変えること。"""
    digits = sum(1 for _s, _y, v in keys if re.fullmatch(r"[0-9０-９]", str(v).strip()))
    return (f"マーク欄方式 ({len(keys)} 欄・うち 1 桁の数字が {digits} 欄)。"
            f"記述の正解が数字だけだと validateQuestions が弾くため、"
            f"今のアプリには入れられない "
            f"(exam-book-admin-model.mjs:143 — 選択肢の取りこぼしを捕まえる砦)。"
            f"選択式にしても PDF の「ア」と画面の 1〜10 が食い違い、0 が表せない。"
            f"入れるなら検証器の設計変更が要る")


def convert_file(path, forced_base=None):
    """@returns (bundle | None, 問題の一覧, 承知のうえで外したか)

    ★ 3 つめが要る。「今は入れられないと分かっていて外す」ものと
      「変換に失敗した」ものを同じ扱いにすると、前者で毎回ゲートが赤くなり、
      赤いのが普通になって本物の失敗を見落とす。
    """
    subject = subject_of(path)
    try:
        doc = load_yaml(path)
    except Exception as e:
        return None, [f"{os.path.basename(path)}: YAML が読めない ({e})"], False

    questions = harvest(doc)

    # --- B を先に見る。数学は選択肢を持たない小問があり harvest が空でも成立する ---
    keys, err = adapt_b_per_section(doc, questions)
    if err:
        return None, [f"{os.path.basename(path)}: [形B] {err}"], False
    if keys:
        # ★ 変換しない。理由は mark_box_reason() に書いてある。
        return None, [f"{os.path.basename(path)}: [形B] {mark_box_reason(keys)}"], True

    if not questions:
        return None, [f"{os.path.basename(path)}: 選択肢を持つ設問が 1 つも見つからない。"
                      f"--probe で構造を見て harvest() の探すキーを直すこと"], False

    values, err = adapt_a_top_level(doc, questions)
    fmt = "A"
    if err:
        return None, [f"{os.path.basename(path)}: [形A] {err}"], False
    if values is None:
        values, err = adapt_c_from_text(doc, questions,
                                        subject or os.path.basename(path))
        fmt = "C"
        if err:
            return None, [f"{os.path.basename(path)}: [形C] {err}"], False
    if values is None:
        return None, [f"{os.path.basename(path)}: 正解の在り処が 3 通りのどれにも当たらない。"
                      f"--probe で構造を見ること (推測はしない)"], False

    base, why = decide_base(values, questions, forced_base)
    if base is None:
        return None, [f"{os.path.basename(path)}: 選択肢番号の起算を決められない — {why}"], False
    shift = 0 if base == "one" else 1

    out, problems = [], []
    for q, val in zip(questions, values):
        built, bad = build_choice_question(q, len(out) + 1, val, shift)
        if built is None:
            problems.append(bad)
        else:
            out.append(built)
    return finish(path, subject, out, problems, fmt, f"{base} — {why}"), [], False


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
    for name, fn in (("A トップレベル answer_key", adapt_a_top_level),
                     ("B 大問ごと answer_key", adapt_b_per_section)):
        v, e = fn(doc, qs)
        print(f"  --- {name}: " + ("該当せず" if v is None and not e
                                   else (f"✗ {e}" if e else f"○ {len(v)} 個")))
    v, e = adapt_c_from_text(doc, qs, subject_of(path) or "?")
    print("  --- C 解説から抜く: " + ("該当せず" if v is None and not e
                                      else (f"✗ {e}" if e else f"○ {len(v)} 個")))


# =============================================================================
def report(bundles, problems, excluded, meta):
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

    # ★ こちらは落とさない。正解の在り処は別セッションの見立てで、
    #   実物が違っても変換は正しく通っている (中身は照合済み)。
    wrong_fmt = [f"{b['subject_name']}: 形{b['format']} (想定 形{EXPECTED_FORMAT[b['subject_name']]})"
                 for b in bundles
                 if b["subject_name"] in EXPECTED_FORMAT
                 and b["format"] != EXPECTED_FORMAT[b["subject_name"]]]
    if wrong_fmt:
        print(f"\n=== 正解の在り処が想定と違った ({len(wrong_fmt)} 件・落とさない) ===")
        print("   変換自体は通っている。想定表 (EXPECTED_FORMAT) のほうを直すこと。")
        for x in wrong_fmt:
            print(f"     {x}")

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

    ★ 見本は「実物がこうなっているはず」という **想定** を書き下したもの。
      実物と違っていても、この自己検査は通る。通ることが証明するのは
      「3 通りのアダプタが動く」ことだけで、「実物が変換できる」ことではない。
    """
    want = {
        # ファイル名の一部: (問数, 形, 1 問目の正解)
        "sample_a_top_level": (3, "A", "2"),
        "sample_c_in_text": (3, "C", "3"),
    }
    # ★ 形 B は「取り込めないと分かって外す」ほうが正しい。
    #   通ってしまったら検証器の砦が外れたということなので、失敗にする。
    refuse = {"sample_b_per_section": "マーク欄方式"}

    files = sorted(glob.glob(os.path.join(FIXTURES, "*.yaml")))
    if len(files) != len(want) + len(refuse):
        print(f"✗ 見本が {len(files)} 本しかない (想定 {len(want) + len(refuse)} 本)")
        return 1
    bad = []
    for f in files:
        key = os.path.splitext(os.path.basename(f))[0]
        b, errs, excluded = convert_file(f)

        if key in refuse:
            if b is not None:
                bad.append(f"{key}: 取り込めないはずの形 B が変換できてしまった "
                           f"(検証器の砦が外れている)")
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

    # ★ 起算を間違えたら気づけるか。①表記の見本から丸数字を消すと
    #   「決められない」になって落ちるはず。落ちなければ検査が無力。
    doc = load_yaml(os.path.join(FIXTURES, "sample_a_top_level.yaml"))
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

    # ★ 番号で突き合わせているか。answer_key の番号を設問と食い違わせたら
    #   落ちるはず。並び順で当ててしまうと数だけ合って全問ずれる。
    doc2 = load_yaml(os.path.join(FIXTURES, "sample_a_top_level.yaml"))
    doc2["answer_key"] = [{"number": n, "answer": "②"} for n in (1, 2, 99)]
    v, e = adapt_a_top_level(doc2, harvest(doc2))
    if v is not None or not e or "食い違う" not in e:
        bad.append("answer_key の問番号が設問と食い違うのに通してしまった "
                   f"(並び順で当てている疑い) — {e!r}")

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
    print(f"[ok] 共通テスト変換の自己検査 — 見本 {len(files)} 本 (形 A/B/C) を変換し、"
          f"アプリと同じ検証器を通過")
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

    bundles, problems, excluded = [], [], []
    for f in files:
        b, errs, is_excluded = convert_file(f, a.base)
        (excluded if is_excluded else problems).extend(errs)
        if b:
            bundles.append(b)

    fatal = report(bundles, problems, excluded, meta)

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
