#!/usr/bin/env python3
"""📜 古文単語 (AI 単語帳の古文) のデータを作る (2026-10-28・すべて書き下ろし)。

入力:
  master.tsv      見出し語・品詞・レベル・正解になる意味 (core)・補足の意味 (other)・誤答を選ぶ範囲 (dgroup)・意味の近さ (clusters)
  content.json    作例 (ex)・現代語訳 (ex_jp)・補足 (note)。見出し語ごと
  overrides.json  点検で直した誤答 (distractors) など。無ければ空
出力:
  server/kobun_vocab_v1.json   サーバが読む正本 (_KOBUN_VOCAB)
  --blind DIR を付けると、答えを伏せた盲検用 (blind.json) と答え (answer_key.json) も書く

誤答 3 つの選び方 (語ごとに固定・乱数は見出し語で決まる):
  1. 同じ dgroup の別の語の core から選ぶ (すべて実在する古語の意味なので、形だけでは消せない)
  2. clusters を 1 つでも共有する語は使わない (意味の近い語・同じ語の別の漢字)
  3. 正解の語の意味 (core と other) と同じ言葉を含む意味は使わない
  4. 誤答どうしも clusters を共有しない (同義の 2 つは「どちらも違う」で消せてしまう)
  5. 意味の数 (「／」の数) と長さが正解に近いものを優先し、同じ誤答が何度も出ないようにする
"""
import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(REPO, "server", "kobun_vocab_v1.json")
LEVELS = {"K": "kobun_kiso", "H": "kobun_hyojun", "N": "kobun_nankan"}
LEVEL_LABELS = {"kobun_kiso": "基礎", "kobun_hyojun": "標準", "kobun_nankan": "難関"}
# 出題時の見出しは「かる（離る）」の括弧を外して「かる」と出す (漢字で答えが分かるため)。
# たまふ は四段 (尊敬) と下二段 (謙譲) で意味が逆になり、誤答にもう一方の正解が入っているので括弧を残す
KEEP_PAREN = {"たまふ（四段）", "たまふ（下二段）"}


def display_of(word):
    return word if word in KEEP_PAREN else re.sub(r"（[^）]*）$", "", word)


def load_master():
    rows = []
    with open(os.path.join(HERE, "master.tsv"), encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            c = (line.split("\t") + [""] * 8)[:8]
            lv, word, kanji, pos, dgroup, clusters, core, other = [x.strip() for x in c]
            rows.append({
                "level": LEVELS[lv], "word": word, "kanji": "" if kanji == "—" else kanji, "pos": pos,
                "dgroup": dgroup, "clusters": [x for x in clusters.split(",") if x],
                "meaning_jp": core, "other": other,
            })
    return rows


def load_json(name, default):
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


_PAREN = re.compile(r"[（(][^）)]*[）)]")


def tokens(text):
    """意味の文字列 → 比べる単位の集合。括弧の中 (誰に・補助動詞 など) は外して、「／」「・」で区切る。"""
    out = set()
    for part in re.split(r"[／・、]", _PAREN.sub("", text or "")):
        part = part.strip().replace("〜", "")
        if len(part) >= 2:
            out.add(part)
    return out


def senses(text):
    return len((text or "").split("／"))


def seeded(word, salt=""):
    return int(hashlib.sha256((word + salt).encode("utf-8")).hexdigest(), 16)


def pick_distractors(rows, overrides):
    by_group = {}
    for r in rows:
        by_group.setdefault(r["dgroup"], []).append(r)
    used = {}  # 誤答に使った回数 (同じ誤答ばかり出ないように)
    result = {}
    for r in rows:
        ov = (overrides.get(r["word"]) or {}).get("distractors")
        if ov:
            result[r["word"]] = list(ov)
            for d in ov:
                used[d] = used.get(d, 0) + 1
            continue
        t_tokens = tokens(r["meaning_jp"]) | tokens(r["other"])
        t_cl = set(r["clusters"])
        cands = []
        for d in by_group[r["dgroup"]]:
            if d["word"] == r["word"] or d["meaning_jp"] == r["meaning_jp"]:
                continue
            if t_cl & set(d["clusters"]):
                continue
            if t_tokens & tokens(d["meaning_jp"]):
                continue
            cands.append(d)
        L = len(r["meaning_jp"])
        S = senses(r["meaning_jp"])

        def score(d):
            sense_pen = 0 if senses(d["meaning_jp"]) == S else 3
            ratio = len(d["meaning_jp"]) / max(L, 1)
            len_pen = abs(1 - ratio) * 4
            return sense_pen + len_pen + used.get(d["meaning_jp"], 0) * 0.8 + (seeded(r["word"], d["word"]) % 1000) / 2000

        chosen = []
        for d in sorted(cands, key=score):
            if any(set(d["clusters"]) & set(x["clusters"]) for x in chosen):
                continue
            if any(tokens(d["meaning_jp"]) & tokens(x["meaning_jp"]) for x in chosen):
                continue
            chosen.append(d)
            if len(chosen) == 3:
                break
        if len(chosen) < 3:
            raise SystemExit(f"誤答が 3 つ選べない: {r['word']} (候補 {len(cands)})")
        result[r["word"]] = [d["meaning_jp"] for d in chosen]
        for d in chosen:
            used[d["meaning_jp"]] = used.get(d["meaning_jp"], 0) + 1
    return result


def study_order(rows):
    """出す順 = 基礎→標準→難関。同じレベルの中は品詞 (dgroup) を 1 語ずつ順に混ぜる
    (新しい語は id 順に出るので、1 回 20 語が動詞だけ・名詞だけにならないように)。"""
    out = []
    for lv in LEVELS.values():
        queues = {}
        for r in rows:
            if r["level"] == lv:
                queues.setdefault(r["dgroup"], []).append(r)
        while any(queues.values()):
            for g in list(queues):
                if queues[g]:
                    out.append(queues[g].pop(0))
    assert len(out) == len(rows)
    return out


def build(blind_dir=None):
    rows = load_master()
    content = {x["word"]: x for x in load_json("content.json", {"items": []})["items"]}
    overrides = load_json("overrides.json", {})
    for r in rows:  # 点検で直した意味・例文を先に当てる (誤答の選び方にも効かせる)
        for k, v in (overrides.get(r["word"]) or {}).items():
            if k in ("meaning_jp", "other", "kanji", "pos", "level", "clusters"):
                r[k] = v
    dist = pick_distractors(rows, overrides)
    rows = study_order(rows)
    words = []
    problems = []
    for i, r in enumerate(rows, 1):
        c = dict(content.get(r["word"]) or {})
        for k, v in (overrides.get(r["word"]) or {}).items():
            if k in ("ex", "ex_jp", "note"):
                c[k] = v
        if not c.get("ex") or not c.get("ex_jp") or not c.get("note"):
            problems.append(f"作例・訳・補足が無い: {r['word']}")
        words.append({
            "no": i, "word": r["word"], "display": display_of(r["word"]), "kanji": r["kanji"], "pos": r["pos"], "level": r["level"],
            "meaning_jp": r["meaning_jp"], "other": r["other"], "note": c.get("note", ""),
            "example": c.get("ex", ""), "example_jp": c.get("ex_jp", ""), "distractors": dist[r["word"]],
        })
    names = {r["word"] for r in rows}
    problems += [f"master.tsv に無い見出し語の上書き・本文: {k}" for k in list(overrides) + list(content) if k not in names]
    problems += check(words)
    return words, problems


def check(words):
    """機械で見られる不変条件。ここで落ちたら出さない。"""
    p = []
    seen = set()
    for w in words:
        if w["word"] in seen:
            p.append(f"見出し語の重複: {w['word']}")
        seen.add(w["word"])
        ds = w["distractors"]
        if len(ds) != 3 or len(set(ds)) != 3:
            p.append(f"誤答が 3 つそろっていない: {w['word']}")
        if w["meaning_jp"] in ds:
            p.append(f"誤答に正解と同じ文: {w['word']}")
        allt = tokens(w["meaning_jp"]) | tokens(w["other"])
        for d in ds:
            if allt & tokens(d):
                p.append(f"誤答が正解の語の意味と重なる: {w['word']} / {d}")
        same = [x for x in words if x is not w and x["display"] == w["display"]]  # あやし（怪し）/（賤し）など
        for x in same:
            if x["meaning_jp"] in ds:
                p.append(f"同じ見出しで出る語の正解が誤答に入っている: {w['word']} / {x['word']}")
        ex = w["example"]
        if ex and not ex.endswith("。"):
            p.append(f"作例が句点で終わらない: {w['word']}")
        if re.search(r"[A-Za-z]", ex + w["example_jp"] + w["note"]):
            p.append(f"英字が入っている: {w['word']}")
    return p


def stats(words):
    longest = sum(1 for w in words if len(w["meaning_jp"]) > max(len(d) for d in w["distractors"]))
    shortest = sum(1 for w in words if len(w["meaning_jp"]) < min(len(d) for d in w["distractors"]))
    use = {}
    for w in words:
        for d in w["distractors"]:
            use[d] = use.get(d, 0) + 1
    by_level = {}
    for w in words:
        by_level[w["level"]] = by_level.get(w["level"], 0) + 1
    return {
        "words": len(words), "by_level": by_level,
        "correct_is_strictly_longest": f"{longest}/{len(words)}",
        "correct_is_strictly_shortest": f"{shortest}/{len(words)}",
        "max_reuse_of_one_distractor": max(use.values()),
    }


def write_blind(words, d):
    os.makedirs(d, exist_ok=True)
    blind, key = [], {}
    for w in words:
        ch = [w["meaning_jp"]] + w["distractors"]
        order = sorted(range(4), key=lambda i: seeded(w["word"], "blind%d" % i))
        ch = [ch[i] for i in order]
        qid = "Q%03d" % w["no"]
        blind.append({"qid": qid, "word": w["display"], "pos": w["pos"], "choices": {k: v for k, v in zip("ABCD", ch)}})
        key[qid] = "ABCD"[ch.index(w["meaning_jp"])]
    with open(os.path.join(d, "blind.json"), "w", encoding="utf-8") as f:
        json.dump(blind, f, ensure_ascii=False, indent=1)
    with open(os.path.join(d, "answer_key.json"), "w", encoding="utf-8") as f:
        json.dump(key, f, ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blind", help="盲検用の blind.json / answer_key.json を書くフォルダ")
    ap.add_argument("--check", action="store_true", help="書かずに検査だけ (server/kobun_vocab_v1.json と一致するかも見る)")
    a = ap.parse_args()
    words, problems = build()
    for x in problems:
        print("❌", x)
    print(json.dumps(stats(words), ensure_ascii=False))
    data = {
        "version": "2026-10-28",
        "note": "古文単語 (AI 単語帳)。意味・作例・訳・補足・誤答はすべてこの塾の書き下ろし。scripts/kobun_vocab/build.py で生成",
        "level_labels": LEVEL_LABELS,
        "words": words,
    }
    text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    if a.check:
        cur = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if cur != text:
            print("❌ server/kobun_vocab_v1.json が master.tsv / content.json / overrides.json から作り直したものと違う")
            problems.append("stale")
        sys.exit(1 if problems else 0)
    if problems:
        sys.exit(1)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote", OUT)
    if a.blind:
        write_blind(words, a.blind)
        print("wrote blind to", a.blind)


if __name__ == "__main__":
    main()
