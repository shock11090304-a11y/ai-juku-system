# -*- coding: utf-8 -*-
"""英検準1級 ライティング対策プリント — データの機械検査 (相互チェック ②)

    python3 scripts/eiken_junichi/writing/check.py

対象は data/examples.json (例題) と data/set*.json (演習 6 セット) の**全部**。
何を見たかを必ず印字する (引数なしで「見本だけ」を検査して緑にしない)。

■ 要約 (大問4)
  - 本文は 3 段落・195〜215 語 (本番は 200 語程度) / 解答例は 60〜70 語
  - 解答例が本文を 5 語以上連続でそのまま写していない (言い換えの手本なので)
  - 解答例に数字・自分の意見 (I think 等)・短縮形が無い
  - 解説の「言い換え」: 本文側の語句が本文に実在し、解答例側の語句が解答例に実在し、
    かつ解答例側の語句が本文に無い (= 本当に言い換えている)
  - 解説の「削った情報」: 本文に実在する
■ 意見論述 (大問5)
  - 4 段落 (序論・本論2・結論)・120〜150 語 / 本論は First, / Second, 結論は For these reasons,
  - POINTS は 4 つ・使うのはそのうち 2 つ / 反対の立場の骨子も POINTS から 2 つ
  - 立場が序論と結論で一貫している / 反対の立場の書き出しは逆の立場
  - 「使える表現」は解答例に実在する / 短縮形が無い
■ 共通
  - 解説 (日本語) の中に 4 語以上の英語を書いたら、同じセットの英文に実在する
    (CLAUDE.md「解説が引用する英文は本文に実在させる」)
  - 既存の塾教材 (../data/part4_writing.json・../mogi/data_no*.json) と意見論述の TOPIC が重ならない
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

PASSAGE_RANGE = (195, 215)   # 本番は「3段落・200語程度」
SUMMARY_RANGE = (60, 70)
ESSAY_RANGE = (120, 150)
MAX_COPY = 4          # 解答例が本文と一致してよい連続語数の上限
N_SETS = 6

CONTRACTION = re.compile(r"\b\w+n't\b|\b\w+'(?:re|ll|ve|d|m)\b", re.I)
OPINION = re.compile(r"\b(?:I think|I believe|in my opinion|I agree|I disagree)\b", re.I)
NEG = re.compile(r"\b(?:not|disagree)\b|more harm than good", re.I)

errors = []
warns = []


def err(msg):
    errors.append(msg)


def words(text):
    return text.split()


def norm_tokens(text):
    out = []
    for w in text.split():
        w = w.lower().strip(".,;:!?\"()[]")
        if w:
            out.append(w)
    return out


def longest_copy(a, b):
    """a と b の最長共通連続語列 (語数, 語列)。"""
    ta, tb = norm_tokens(a), norm_tokens(b)
    best, where = 0, None
    prev = [0] * (len(tb) + 1)
    for i in range(1, len(ta) + 1):
        cur = [0] * (len(tb) + 1)
        for j in range(1, len(tb) + 1):
            if ta[i - 1] == tb[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best, where = cur[j], i
        prev = cur
    return best, (" ".join(ta[where - best:where]) if where else "")


# 文法の型 (prevent A from doing / be meant to do) は引用ではないので照合しない
PLACEHOLDERS = {"A", "B", "do", "doing", "done"}


def english_runs(ja_text, min_words=4):
    """日本語の解説に埋め込まれた英語の連なり (min_words 語以上)。文法の型は除く。"""
    runs = re.findall(r"[A-Za-z][A-Za-z'\-]*(?:[ ,]+[A-Za-z][A-Za-z'\-]*)+", ja_text)
    out = []
    for r in runs:
        r = r.strip(" ,")
        toks = r.replace(",", " ").split()
        if len(toks) >= min_words and not PLACEHOLDERS & set(toks):
            out.append(r)
    return out


def check_summary(label, s):
    paras = s["paras"]
    passage = " ".join(paras)
    model = s["model"]
    if len(paras) != 3:
        err(f"{label} 要約: 本文が {len(paras)} 段落 (3 段落のはず)")
    n = len(words(passage))
    if not PASSAGE_RANGE[0] <= n <= PASSAGE_RANGE[1]:
        err(f"{label} 要約: 本文 {n} 語 (範囲 {PASSAGE_RANGE})")
    m = len(words(model))
    if not SUMMARY_RANGE[0] <= m <= SUMMARY_RANGE[1]:
        err(f"{label} 要約: 解答例 {m} 語 (範囲 {SUMMARY_RANGE})")
    k, seq = longest_copy(model, passage)
    if k > MAX_COPY:
        err(f"{label} 要約: 解答例が本文を {k} 語連続で写している「{seq}」")
    if re.search(r"\d", model):
        err(f"{label} 要約: 解答例に数字がある (具体的な数字は削る方針)")
    if OPINION.search(model):
        err(f"{label} 要約: 解答例に意見表現がある「{OPINION.search(model).group(0)}」")
    if CONTRACTION.search(model):
        err(f"{label} 要約: 解答例に短縮形「{CONTRACTION.search(model).group(0)}」")
    if len(s["para_roles"]) != 3:
        err(f"{label} 要約: 段落の役割が {len(s['para_roles'])} 行 (3 行のはず)")
    for p in s["paraphrases"]:
        if p["src"] not in passage:
            err(f"{label} 要約: 言い換えの本文側が本文に無い「{p['src']}」")
        if p["dst"] not in model:
            err(f"{label} 要約: 言い換えの解答例側が解答例に無い「{p['dst']}」")
        if p["dst"].lower() in passage.lower():
            err(f"{label} 要約: 言い換えたはずの語句が本文にそのままある「{p['dst']}」")
    for o in s["omitted"]:
        if o["src"] not in passage:
            err(f"{label} 要約: 削った情報が本文に無い「{o['src']}」")
    return n, m, k


def check_essay(label, e, house_topics):
    paras = e["paras"]
    text = " ".join(paras)
    if len(paras) != 4:
        err(f"{label} 意見: {len(paras)} 段落 (4 段落のはず)")
    n = len(words(text))
    if not ESSAY_RANGE[0] <= n <= ESSAY_RANGE[1]:
        err(f"{label} 意見: 解答例 {n} 語 (範囲 {ESSAY_RANGE})")
    for i, head in ((1, "First,"), (2, "Second,"), (3, "For these reasons,")):
        if len(paras) > i and not paras[i].startswith(head):
            err(f"{label} 意見: 第{i + 1}段落が {head} で始まっていない")
    pts = e["points"]
    if len(pts) != 4 or len(set(pts)) != 4:
        err(f"{label} 意見: POINTS が 4 つの異なる語になっていない {pts}")
    used = e["used_points"]
    if len(used) != 2 or len(set(used)) != 2 or not set(used) <= set(pts):
        err(f"{label} 意見: 使う POINTS が POINTS の中の 2 つになっていない {used}")
    opp = e["opposite"]
    opp_pts = [r["point"] for r in opp["reasons"]]
    if len(opp_pts) != 2 or len(set(opp_pts)) != 2 or not set(opp_pts) <= set(pts):
        err(f"{label} 意見: 反対の立場の POINTS が POINTS の中の 2 つになっていない {opp_pts}")
    stance = e["stance"]
    if stance not in ("agree", "disagree"):
        err(f"{label} 意見: stance が agree/disagree でない「{stance}」")
    intro, concl = paras[0], paras[-1]
    if stance == "disagree":
        if not NEG.search(intro) or not NEG.search(concl):
            err(f"{label} 意見: 反対の立場なのに序論か結論に否定が無い")
        if NEG.search(opp["stance_en"]):
            err(f"{label} 意見: 反対の立場の骨子 (賛成側のはず) に否定がある")
    else:
        if NEG.search(intro) or NEG.search(concl):
            err(f"{label} 意見: 賛成の立場なのに序論か結論に否定がある")
        if not NEG.search(opp["stance_en"]):
            err(f"{label} 意見: 反対の立場の骨子 (反対側のはず) に否定が無い")
    if CONTRACTION.search(text):
        err(f"{label} 意見: 短縮形「{CONTRACTION.search(text).group(0)}」")
    for x in e["expressions"]:
        if x["en"] not in text:
            err(f"{label} 意見: 使える表現が解答例に無い「{x['en']}」")
    if e["topic"].strip().lower() in house_topics:
        err(f"{label} 意見: 既存の塾教材と同じ TOPIC「{e['topic']}」")
    per = [len(words(p)) for p in paras]
    # ① の型 (序論 20語前後 / 本論 45〜55語 / 結論 15〜20語) と解答例を食い違わせない
    if len(per) == 4:
        for name, n_, (lo, hi) in (("序論", per[0], (15, 25)), ("本論1", per[1], (45, 55)),
                                   ("本論2", per[2], (45, 55)), ("結論", per[3], (15, 20))):
            if not lo <= n_ <= hi:
                err(f"{label} 意見: {name} {n_} 語 (① の型の目安 {lo}〜{hi} 語)")
    return n, per


def check_quotes(label, blob_en, ja_fields):
    for field, ja in ja_fields:
        for run in english_runs(ja):
            if run not in blob_en:
                err(f"{label} {field}: 解説の英語が英文に実在しない「{run}」")


def ja_fields_of(s, e):
    out = [("要約の要点", r["point_ja"]) for r in s["para_roles"]]
    out += [("要約のメモ", m) for m in s.get("memo_ja", [])]
    out += [("削った理由", o["why_ja"]) for o in s["omitted"]]
    out += [("要約のワンポイント", s["note_ja"]), ("意見のワンポイント", e["note_ja"])]
    out += [("意見のメモ", m) for m in e.get("memo_ja", [])]
    out += [("表現の説明", x["ja"]) for x in e["expressions"]]
    out += [("反対の立場", r["support_ja"]) for r in e["opposite"]["reasons"]]
    return out


def en_blob(s, e):
    parts = list(s["paras"]) + [s["model"]] + list(e["paras"]) + [e["topic"]]
    parts += [e["opposite"]["stance_en"]] + [r["topic_en"] for r in e["opposite"]["reasons"]]
    return "\n".join(parts)


def house_essay_topics():
    topics = set()
    p = os.path.join(HERE, "..", "data", "part4_writing.json")
    if os.path.exists(p):
        for t in json.load(open(p, encoding="utf-8")).get("essay_tasks", []):
            topics.add(t["topic"].strip().lower())
    for p in glob.glob(os.path.join(HERE, "..", "mogi", "data_no*.json")):
        d = json.load(open(p, encoding="utf-8"))
        t = d.get("part4", {}).get("essay", {}).get("topic")
        if t:
            topics.add(t.strip().lower())
    return topics


def load_all():
    ex = json.load(open(os.path.join(DATA, "examples.json"), encoding="utf-8"))
    sets = []
    for p in sorted(glob.glob(os.path.join(DATA, "set*.json"))):
        sets.append(json.load(open(p, encoding="utf-8")))
    return ex, sets


def main():
    ex, sets = load_all()
    house = house_essay_topics()
    print(f"[check] 例題 1 組 + 演習 {len(sets)} セット / 既存教材の TOPIC {len(house)} 件と照合")
    nos = [s["no"] for s in sets]
    if sorted(nos) != list(range(1, N_SETS + 1)):
        err(f"セット番号が 1〜{N_SETS} になっていない {nos}")
    rows = [("例題", ex)] + [(f"Set {s['no']}", s) for s in sorted(sets, key=lambda d: d["no"])]
    topics, themes = set(), set()
    for label, d in rows:
        s, e = d["summary"], d["essay"]
        n, m, k = check_summary(label, s)
        en, per = check_essay(label, e, house)
        check_quotes(label, en_blob(s, e), ja_fields_of(s, e))
        if e["topic"] in topics:
            err(f"{label}: 意見論述の TOPIC が重複")
        topics.add(e["topic"])
        if s["theme_ja"] in themes:
            err(f"{label}: 要約のテーマが重複")
        themes.add(s["theme_ja"])
        print(f"  {label:6s} 要約: 本文 {n:3d} 語 → 解答例 {m:2d} 語 (最長一致 {k} 語)"
              f" ｜ 意見: {en:3d} 語 {per}")
    for w in warns:
        print("  注意:", w)
    if errors:
        for x in errors:
            print("NG:", x)
        print(f"=== FAIL {len(errors)} ===")
        sys.exit(1)
    print(f"=== ALL PASS ({len(warns)} warnings) ===")


if __name__ == "__main__":
    main()
