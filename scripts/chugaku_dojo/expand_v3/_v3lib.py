# -*- coding: utf-8 -*-
"""expand_v3 共有ライブラリ (ゲートからも build からも import される。単体では何もしない)。

中学生 入試問題道場「弱点克服」プール (exam_questions / exam_id=chugaku / eiken_grade=koukou) の増量 v3。
正典は units.json (単元カタログ)。問題1件の形は verified/*.json と同じ:
  {subject, part, filter, unit, stem, passage, choices[4], answer_index, explanation}
"""
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOJO = os.path.dirname(HERE)                       # scripts/chugaku_dojo
SCRIPTS = os.path.dirname(DOJO)                    # scripts/
UNITS_PATH = os.path.join(DOJO, "units.json")

PARTS = ["eng", "math", "kokugo", "rika", "shakai"]
TARGET_ADD = 24          # 1単元に足す問題数 (24 → 48 問 = 8問セットが 6 回ぶん)
GEN_PER_UNIT = 34        # 作問数 (盲検・重複・癖の除外ぶんの余裕)
READING_PASSAGES = 8     # 読解単元: 本文の本数 (各4問 = 32問 → 24問採用)
MODEL = "chugaku-koukou-expand-v3"        # ★rollback キー (exam_questions.model)
SOURCE = "chugaku_koukou_expand_v3"       # ★rollback キー (question_data.source)
CHUNK = 5                                 # 非読解: 5小問/行 (既存プールと同じ)
BANK_LIMIT = 50                           # bank API が返す最大行数 (created_at DESC)
READING_FETCH = 32                        # 読解カード (agg 4) は画面が limit=min(50, agg*8)=32 で取る (dojo-drill.html)

# 道場にしかない英語の単元 (units.json に無いが本番に実在 / カードがある)。
#   不定詞の用法 = futeishi/ の30問。過去形 = 専用問題なし (『過去形』を含む行が LIKE で当たる: 既存 9 行
#   (時制・助動詞・be動詞・現在完了) + v3 の時制 5 行。unit が「過去形」で始まる小問は 0 → それらが混ざって出る)。
#   未来形 = 『未来形』を含む行が 0 → bank は単元で絞らず英語の新しい順 50 行を返す (全単元の混在)。
DOJO_ONLY_ENG = ["不定詞の用法", "過去形", "未来形"]


def load_units():
    """units.json → [{gi, part, subject, filter, name, reading}] (gi は全教科通しの添字 = ファイル名の番号)"""
    cat = json.load(open(UNITS_PATH, encoding="utf-8"))
    out, gi = [], 0
    for s in cat["subjects"]:
        for u in s["units"]:
            out.append({"gi": gi, "part": s["part"], "subject": s["subj"], "filter": u["filter"],
                        "name": u["name"], "reading": bool(u.get("reading"))})
            gi += 1
    return out


def bank_limit(reading):
    """その単元カードが bank から取る行数。単元名を含む行がこれを超えると古い行が配信されなくなる。"""
    return READING_FETCH if reading else BANK_LIMIT


def filters_of(part, units=None):
    units = units or load_units()
    return [u["filter"] for u in units if u["part"] == part]


def norm_ws(s):
    return " ".join(str(s or "").split())


def sig(stem, choices):
    """設問の同一判定キー = (空白を潰した設問文, 選択肢の集合)。★stem 単独で判定しない
    (指示文だけが stem の形式は正当に重複する)。insert / post_check も同じ規則にすること。"""
    return (norm_ws(stem), tuple(sorted(norm_ws(c) for c in (choices or []))))


def stem_key(stem):
    return norm_ws(stem)


_CONTENT = re.compile(r"[A-Za-z0-9０-９〔「『(（√]")
_EMPTY_SLOT = re.compile(r"[〔（(]\s*[〕）)]")


def content_stem(stem):
    """設問文そのものに中身 (英文・数値・問う語句) があるか。
    「次の中から、英文として正しいものを選びなさい。」「〔 〕の漢字の使い方が正しいものを選びなさい。」のような
    指示文だけの stem (空の〔 〕( ) は中身ではない) は複数問で正当に重複する (futeishi/README.md の事故) ので、
    stem 単独の重複判定はこの関数が True のものにだけ使う。"""
    return bool(_CONTENT.search(_EMPTY_SLOT.sub("", str(stem or ""))))


# 選択肢の「位置」を指す表現 (シャッフルで嘘になる)。カタカナ語中の ア/イ は拾わない。
POSITIONAL = re.compile(
    r"[（(「『][アイウエ][）)」』]|[①②③④]|[（(「『][ABCDａｂｃｄ][）)」』]"
    r"|[0-9０-９一二三四]\s*(?:番目|つ目)\s*の\s*(?:選択肢|答え|もの)"
    r"|選択肢\s*[アイウエABCDａ-ｄ1-4１-４]\b|正解は\s*[アイウエ]\s*[。、]"
)


def expl_head(filt, correct):
    """解説の定型接頭辞。正解テキストの末尾が句点/ピリオド等なら「。」を重ねない。"""
    tail = "" if str(correct).rstrip().endswith(("。", ".", "?", "？", "！", "!")) else "。"
    return f"【単元】{filt}。正解は「{correct}」{tail}"


_HEAD_OPEN = re.compile(r"\s*【単元】[^。]*。\s*正解は「")


def _strip_one(s):
    """先頭の定型接頭辞を 1 つ外す。正解の本文に「」が入っていても、かっこの対応を数えて閉じかっこを探す。
    ★以前は 正解は「.*?」 の最短一致で、正解に「」を含む問題 (敬語・詩歌・文学的文章など) では最初の 」 で
      切れてしまい、build のたびに正解の後ろ半分が解説の頭に 1 つずつ増えていた (2026-10-04 に 8 問で発覚)。"""
    m = _HEAD_OPEN.match(s)
    if not m: return s, False
    depth, j = 1, m.end()
    while j < len(s) and depth:
        if s[j] == "「": depth += 1
        elif s[j] == "」": depth -= 1
        j += 1
    if depth: return s, False   # かっこが閉じていない → 触らない
    if s[j:j + 1] == "。": j += 1
    return s[j:].strip(), True


def strip_prefix(expl):
    body = str(expl or "").strip()
    for _ in range(2):   # 接頭辞が二重に付いたものも外す
        body, ok = _strip_one(body)
        if not ok: break
    return body


def rebuild_expl(filt, correct, expl):
    e = str(expl or "").strip(); head = expl_head(filt, correct)
    if e.startswith(head):   # 今の正解の接頭辞なら、そのまま正確に外す
        body = e[len(head):].strip()
        if not head.endswith("。") and body.startswith("。"): body = body[1:].strip()   # _strip_one と同じく余分な「。」を 1 つ外す
    else:
        body = e
    return head + strip_prefix(body)


def existing_questions():
    """本番に入っている (= リポジトリ側の生成元) 全問題を part ごとに返す。
    verified/ (v1) + add/ (数学 expand) + add2/ (英国理社 expand) + futeishi/items.py (不定詞の用法)。
    返り値: {part: [ {filter, stem, choices, answer_index, explanation, passage, _src} ]}"""
    out = {p: [] for p in PARTS}
    for d in ("verified", "add", "add2"):
        for fp in sorted(glob.glob(os.path.join(DOJO, d, "*.json"))):
            if os.path.basename(fp).startswith("_"):
                continue
            try:
                data = json.load(open(fp, encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(data, list):
                continue
            for q in data:
                p = q.get("part")
                if p in out:
                    q = dict(q)
                    q["_src"] = f"{d}/{os.path.basename(fp)}"
                    out[p].append(q)
    # 不定詞の用法 (items.py は正解テキスト+誤答3つ)
    fut = os.path.join(DOJO, "futeishi")
    if os.path.isdir(fut):
        sys.path.insert(0, fut)
        try:
            import items as _items  # noqa
            for it in _items.ITEMS:
                out["eng"].append({"filter": _items.UNIT, "unit": _items.UNIT, "stem": it["stem"],
                                   "choices": [it["correct"]] + list(it["distractors"]), "answer_index": 0,
                                   "explanation": it["expl"], "passage": "", "_src": "futeishi/items.py"})
        finally:
            sys.path.pop(0)
    return out


def existing_rows_text(part):
    """既存プールの『行 (大問)』単位の本文 (JSON文字列) の近似。bank の LIKE 予算 (50行) の見積もりに使う。
    v1/expand は単元ごとに 5 小問/行で束ねたので、ファイル内で filter ごとに 5 つずつ区切る。"""
    rows = []
    by_src_filter = {}
    for q in existing_questions()[part]:
        by_src_filter.setdefault((q["_src"], q.get("filter")), []).append(q)
    for (src, filt), qs in by_src_filter.items():
        if any(q.get("passage") for q in qs):     # 読解は本文ごと1行
            groups = {}
            for q in qs:
                groups.setdefault(q.get("passage", ""), []).append(q)
            for pg, g in groups.items():
                rows.append(json.dumps({"passage": pg, "format_type": filt, "questions": g}, ensure_ascii=False))
        else:
            for i in range(0, len(qs), CHUNK):
                rows.append(json.dumps({"format_type": filt, "questions": qs[i:i + CHUNK]}, ensure_ascii=False))
    return rows


def md5(s):
    return hashlib.md5(str(s).encode("utf-8")).hexdigest()


def longest_tell(q):
    """正解肢が単独最長で、しかも目立つ差 (他の最長より 3 文字以上 または 25% 以上長い) があるか。
    1〜2 文字の差は手がかりにならないので数えない。"""
    ch = q["choices"]; a = q["answer_index"]
    m = max(len(c) for i, c in enumerate(ch) if i != a)
    return len(ch[a]) > m and (len(ch[a]) >= m + 3 or len(ch[a]) >= m * 1.25)


def shortest_tell(q):
    ch = q["choices"]; a = q["answer_index"]
    m = min(len(c) for i, c in enumerate(ch) if i != a)
    return len(ch[a]) < m and (len(ch[a]) <= m - 3 or len(ch[a]) <= m * 0.75)


def converges(choices, c):
    """『各部分で最多の値を拾うと正解になる』(scan_choice_convergence.py と同じ判定)"""
    sys.path.insert(0, SCRIPTS)
    try:
        import scan_choice_convergence as scc  # noqa
        return scc.converges(choices, c)
    except Exception:
        return False
    finally:
        sys.path.pop(0)


def validate_question(q, filt_set, errs, where):
    """形式検査。問題があれば errs に (where, 理由) を積み False。"""
    ok = True
    if q.get("filter") not in filt_set:
        errs.append((where, f"filter 不正: {q.get('filter')!r}")); ok = False
    if q.get("unit") != q.get("filter"):
        errs.append((where, "unit != filter")); ok = False
    ch = q.get("choices")
    if not isinstance(ch, list) or len(ch) != 4 or any(not isinstance(c, str) or not c.strip() for c in ch):
        errs.append((where, "選択肢が4つの非空文字列でない")); return False
    # ★大文字小文字は区別する: 遺伝の「AAとAa」「AaとAa」を小文字化すると同一視してしまう (実測 2 問が誤 drop)
    if len({norm_ws(c) for c in ch}) != 4:
        errs.append((where, f"選択肢に重複: {ch}")); ok = False
    a = q.get("answer_index")
    if not isinstance(a, int) or not (0 <= a < 4):
        errs.append((where, f"answer_index 不正: {a!r}")); return False
    if not isinstance(q.get("stem"), str) or not q["stem"].strip():
        errs.append((where, "stem 空")); ok = False
    if not isinstance(q.get("explanation"), str) or not q["explanation"].strip():
        errs.append((where, "explanation 空")); ok = False
    for f in ("stem", "explanation"):
        if POSITIONAL.search(str(q.get(f, ""))):
            errs.append((where, f"{f} に位置語 (ア/①/N番目)")); ok = False
    if isinstance(q.get("explanation"), str) and q["explanation"].count("正解は「") > 1:
        errs.append((where, "解説に「正解は「」が複数")); ok = False
    return ok
