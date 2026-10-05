# -*- coding: utf-8 -*-
"""eibunpo_v2 共有ライブラリ (ゲートからも build からも import される。単体では何もしない)。

高校生 入試問題道場「単元別（弱点克服）」英文法 13 カードのプール増量 v2。
対象の本番プール: exam_questions / exam_id=daigaku / eiken_grade=teiki / part_key ∈ {r_grammar_unit, r_grammar}。
正典は units.json (カードのカタログ)。問題 1 件の形は verified/*.json と同じ:
  {subject, part, filter, unit, stem, passage, choices[4], answer_index, explanation, form, level}
  unit は「<tag>(<細目>)」(例: 関係詞(非制限用法 which))。tag は units.json の tag と完全一致。
中学 (scripts/chugaku_dojo/expand_v3) と同じ工程で、形式の違いだけをここに閉じ込める。
"""
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KOSEI = os.path.dirname(HERE)                      # scripts/kosei_dojo
SCRIPTS = os.path.dirname(KOSEI)                   # scripts/
REPO = os.path.dirname(SCRIPTS)
SEED = os.path.join(REPO, "seed-data")
UNITS_PATH = os.path.join(HERE, "units.json")

EXAM, GRADE = "daigaku", "teiki"
PARTS = ["r_grammar_unit", "r_grammar"]
TARGET_ADD = 30          # 1 カードに足す問題数 (10 問セットが 3 回ぶん)
GEN_PER_UNIT = 42        # 作問数 (盲検・重複・癖の除外ぶんの余裕)
MODEL = "kosei-eibunpo-expand-v2"         # ★rollback キー (exam_questions.model)
SOURCE = "kosei_eibunpo_expand_v2"        # ★rollback キー (question_data.source)
CHUNK = 6                                 # 6 小問/行 (既存の英文法プールと同じ)
BANK_LIMIT = 50                           # 画面 (agg 10) は limit=min(50, 10*8)=50 で bank から取る
SUBJECT = "英語"
UNIV_SIMULATED = "定期/単元別"             # 既存の expand1 の行と同じ
YEAR_SIMULATED = 0
READING_PASSAGES = 0                      # 読解単元なし (互換のため残す)


def load_units():
    """units.json → [{gi, part, grade, filter, tag, name, topic, agg, reading=False, syllabus, existing_subtopics}]"""
    cat = json.load(open(UNITS_PATH, encoding="utf-8"))
    out = []
    for u in cat["units"]:
        out.append({**u, "subject": SUBJECT, "reading": False})
    return out


def bank_limit(reading=False):
    return BANK_LIMIT


def own_part_files(paths, part, prefix):
    """glob で拾ったファイルから、part 名が自分を接頭辞に持つ別 part (r_grammar → r_grammar_unit) のものを除く。
    prefix は 'review_' のようなファイル名の頭。"""
    others = [p for p in PARTS if p != part and p.startswith(part)]
    return [fp for fp in paths if not any(os.path.basename(fp).startswith(f"{prefix}{o}_") or os.path.basename(fp).startswith(f"applied_{prefix}{o}_") for o in others)]


def filters_of(part, units=None):
    units = units or load_units()
    return [u["filter"] for u in units if u["part"] == part]


def tags_of(part, units=None):
    units = units or load_units()
    return [u["tag"] for u in units if u["part"] == part]


def norm_ws(s):
    return " ".join(str(s or "").split())


def sig(stem, choices):
    """設問の同一判定キー = (空白を潰した設問文, 選択肢の集合)。insert / post_check も同じ規則。"""
    return (norm_ws(stem), tuple(sorted(norm_ws(c) for c in (choices or []))))


def stem_key(stem):
    return norm_ws(stem)


_CONTENT = re.compile(r"[A-Za-z0-9０-９〔「『(（]")
_EMPTY_SLOT = re.compile(r"[〔（(]\s*[〕）)]")


def content_stem(stem):
    """設問文そのものに中身 (英文・問う語句) があるか。指示文だけの stem は複数問で正当に重複する。"""
    return bool(_CONTENT.search(_EMPTY_SLOT.sub("", str(stem or ""))))


def pref(u):
    """unit の接頭辞 (dojo-drill.html の unitExact と同じ切り方)。"""
    return re.split(r"[（(：:]", str(u or ""))[0].strip()


UNIT_RE = re.compile(r"^([^()（）]{2,12})\(([^()（）]{1,40})\)$")


def unit_parts(unit):
    """『関係詞(非制限用法 which)』→ ('関係詞', '非制限用法 which')。形が違えば None。"""
    m = UNIT_RE.match(str(unit or "").strip())
    return (m.group(1), m.group(2)) if m else None


# 選択肢の「位置」を指す表現 (シャッフルで嘘になる)。
POSITIONAL = re.compile(
    r"[（(「『][アイウエ][）)」』]|[①②③④]|[（(「『][ABCDａｂｃｄ][）)」』]"
    r"|[0-9０-９一二三四]\s*(?:番目|つ目)\s*の\s*(?:選択肢|答え|もの)"
    r"|選択肢\s*[アイウエABCDａ-ｄ1-4１-４]\b|正解は\s*[アイウエ]\s*[。、]"
)


def expl_head(unit, correct):
    """解説の定型接頭辞。『【単元】関係詞(細目)。正解は「which」。』"""
    tail = "" if str(correct).rstrip().endswith(("。", ".", "?", "？", "！", "!")) else "。"
    return f"【単元】{unit}。正解は「{correct}」{tail}"


_HEAD_OPEN = re.compile(r"\s*【単元】[^。]*。\s*正解は「")
_HEAD_TAG_ONLY = re.compile(r"\s*【単元】[^。\n]*[。\n]\s*")


def _strip_one(s):
    """先頭の定型接頭辞を 1 つ外す。正解の本文に「」が入っていても、かっこの対応を数えて閉じかっこを探す。"""
    m = _HEAD_OPEN.match(s)
    if not m:
        m2 = _HEAD_TAG_ONLY.match(s)        # 『【単元】X。本文』(正解の無い旧型) も外す
        return (s[m2.end():].strip(), True) if m2 else (s, False)
    depth, j = 1, m.end()
    while j < len(s) and depth:
        if s[j] == "「": depth += 1
        elif s[j] == "」": depth -= 1
        j += 1
    if depth: return s, False
    if s[j:j + 1] == "。": j += 1
    return s[j:].strip(), True


def strip_prefix(expl):
    body = str(expl or "").strip()
    for _ in range(2):
        body, ok = _strip_one(body)
        if not ok: break
    return body


def rebuild_expl(unit, correct, expl):
    e = str(expl or "").strip(); head = expl_head(unit, correct)
    if e.startswith(head):
        body = e[len(head):].strip()
        if not head.endswith("。") and body.startswith("。"): body = body[1:].strip()
    else:
        body = e
    return head + strip_prefix(body)


def _seed_rows(fp):
    d = json.load(open(fp, encoding="utf-8"))
    if isinstance(d, list): return d
    for k in ("rows", "items", "questions", "data"):
        if isinstance(d.get(k), list): return d[k]
    return []


def existing_rows():
    """本番の英文法プール (seed-data の daigaku/teiki/r_grammar_unit|r_grammar) の行を [(part, question_data, src)] で返す。"""
    out = []
    for fp in sorted(glob.glob(os.path.join(SEED, "*.json"))):
        try: items = _seed_rows(fp)
        except Exception: continue
        for r in items:
            if not isinstance(r, dict) or r.get("exam_id") != EXAM or r.get("eiken_grade") != GRADE or r.get("part_key") not in PARTS:
                continue
            qd = r.get("question_data")
            if isinstance(qd, str):
                try: qd = json.loads(qd)
                except Exception: continue
            if isinstance(qd, dict) and qd.get("questions"):
                out.append((r["part_key"], qd, os.path.basename(fp)))
    if not out:
        raise FileNotFoundError("seed-data に英文法 (daigaku/teiki) の行が見つからない (既存プールの見積もりができない)")
    return out


def existing_questions():
    """本番に入っている (= リポジトリ側の生成元) 英文法の全小問を part ごとに返す。
    返り値: {part: [ {filter, unit, stem, choices, answer_index, explanation, passage, _src} ]}
    filter はカードの filter (unit の接頭辞が一致するもの。どのカードにも当たらない小問は filter=None)。"""
    units = load_units()
    out = {p: [] for p in PARTS}
    for part, qd, src in existing_rows():
        cards = [u for u in units if u["part"] == part]
        for q in qd.get("questions") or []:
            p = pref(q.get("unit"))
            filt = next((u["filter"] for u in cards if p.startswith(u["filter"])), None)
            a = q.get("answer")
            try: ai = int(a)
            except Exception: ai = -1
            out[part].append({"filter": filt, "unit": q.get("unit"), "stem": q.get("stem", ""), "choices": list(q.get("choices") or []),
                              "answer_index": ai, "explanation": q.get("explanation", ""), "passage": qd.get("passage") or "", "_src": src})
    return out


def drill_stems():
    """単元ドリル (grammar_questions) の英文法プール seed の設問文 {unit: [stem]} (別機能だが同じ文を出さないための参考)。"""
    out = {}
    for name in ("grammar_drill_pool_v1.json", "grammar_drill_pool_v2.json", "grammar_drill_weakness_v1.json"):
        fp = os.path.join(SEED, name)
        if not os.path.exists(fp): continue
        for q in _seed_rows(fp):
            if isinstance(q, dict) and q.get("stem"):
                out.setdefault(str(q.get("unit") or "?"), []).append(q["stem"])
    return out


def existing_rows_text(part):
    """既存プールの『行 (大問)』単位の本文 (JSON 文字列)。bank の LIKE 予算 (50 行) の見積もりに使う。
    seed-data の行そのもの (本番の 2026-08-18 のタグ付けで解説が変わった行は、本番のほうが単元名を多く含む →
    本番の実数は post_check.py --before / kosei_baseline の結果で補正する)。"""
    return [json.dumps(qd, ensure_ascii=False) for p, qd, src in existing_rows() if p == part]


def baseline_rows():
    """塾長の端末で取った本番の基準 (~/Desktop/kosei_baseline_*.json) があれば {(part, filter): 行数} を返す。無ければ {}。"""
    files = sorted(glob.glob(os.path.expanduser("~/Desktop/kosei_baseline_*.json")))
    if not files: return {}
    try:
        data = json.load(open(files[-1], encoding="utf-8"))
        return {(c["part"], c["filter"]): int(c["rows"]) for c in data if c.get("exam") == EXAM and c.get("grade") == GRADE and c.get("filter")}
    except Exception:
        return {}


def md5(s):
    return hashlib.md5(str(s).encode("utf-8")).hexdigest()


def longest_tell(q):
    ch = q["choices"]; a = q["answer_index"]
    m = max(len(c) for i, c in enumerate(ch) if i != a)
    return len(ch[a]) > m and (len(ch[a]) >= m + 3 or len(ch[a]) >= m * 1.25)


def shortest_tell(q):
    ch = q["choices"]; a = q["answer_index"]
    m = min(len(c) for i, c in enumerate(ch) if i != a)
    return len(ch[a]) < m and (len(ch[a]) <= m - 3 or len(ch[a]) <= m * 0.75)


def converges(choices, c):
    sys.path.insert(0, SCRIPTS)
    try:
        import scan_choice_convergence as scc  # noqa
        return scc.converges(choices, c)
    except Exception:
        return False
    finally:
        sys.path.pop(0)


SLOT_RE = re.compile(r"\(\s*\)|（\s*）|_{3,}")


def validate_question(q, unit_def, errs, where):
    """形式検査。unit_def は units.json のカード。問題があれば errs に (where, 理由) を積み False。"""
    ok = True
    if q.get("filter") != unit_def["filter"]:
        errs.append((where, f"filter 不正: {q.get('filter')!r}")); ok = False
    up = unit_parts(q.get("unit"))
    if not up:
        errs.append((where, f"unit が『<tag>(<細目>)』の形でない: {q.get('unit')!r}")); ok = False
    elif up[0] != unit_def["tag"]:
        errs.append((where, f"unit の接頭辞が {unit_def['tag']!r} でない: {q.get('unit')!r}")); ok = False
    ch = q.get("choices")
    if not isinstance(ch, list) or len(ch) != 4 or any(not isinstance(c, str) or not c.strip() for c in ch):
        errs.append((where, "選択肢が4つの非空文字列でない")); return False
    if len({norm_ws(c) for c in ch}) != 4:
        errs.append((where, f"選択肢に重複: {ch}")); ok = False
    a = q.get("answer_index")
    if not isinstance(a, int) or not (0 <= a < 4):
        errs.append((where, f"answer_index 不正: {a!r}")); return False
    stem = q.get("stem")
    if not isinstance(stem, str) or not stem.strip():
        errs.append((where, "stem 空")); ok = False
    else:
        if "___" in stem:
            errs.append((where, "空所は ( ) で書く (___ は使わない)")); ok = False
        if str(q.get("form", "")) in ("空所補充", "対話応答", "語形選択", "書きかえ") and len(SLOT_RE.findall(stem)) != 1:
            errs.append((where, f"空所 ( ) が 1 か所でない ({len(SLOT_RE.findall(stem))})")); ok = False
    if not isinstance(q.get("explanation"), str) or not q["explanation"].strip():
        errs.append((where, "explanation 空")); ok = False
    for f in ("stem", "explanation"):
        if POSITIONAL.search(str(q.get(f, ""))):
            errs.append((where, f"{f} に位置語 (ア/①/N番目)")); ok = False
    if isinstance(q.get("explanation"), str) and q["explanation"].count("正解は「") > 1:
        errs.append((where, "解説に「正解は「」が複数")); ok = False
    if str(q.get("passage", "")).strip():
        errs.append((where, "英文法は本文 (passage) なし")); ok = False
    return ok
