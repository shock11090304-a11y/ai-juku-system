#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英文の記号・表記を全数検査する(教科書/共通テスト準拠かどうか)。

  python3 typo_gate.py

人間の目視では絶対に取りこぼす層をここで潰す:
  1 全角混入   英文の中に全角英数・全角スペース・全角記号が紛れていないか
  2 引用符     ' と ’ 、" と “” が混在していないか(冊子内で1種類に統一)
  3 ダッシュ   - / – / — の使い分けが揺れていないか
  4 空白       二重スペース、句読点の前の空白、ピリオド後の空白欠落
  5 文の体裁   選択肢が文頭大文字か・終止符の有無が4つで揃っているか
  6 数字表記   同じ題の中で「ten items」と「10 items」のように綴りと数字が混在していないか
  7 丸数字     ①②③④ 以外のマーク記号が混ざっていないか
  8 和文       日本語の解説に半角カタカナ・全角英数が混ざっていないか
"""
import os, re, sys, json, unicodedata, collections

HERE = os.path.dirname(os.path.abspath(__file__))
PASS = os.path.join(HERE, "passages")
NG, WARN = [], []


def add(bucket, pid, axis, msg):
    bucket.append(f"[{axis}] {pid}  {msg}")


# 英文フィールド(半角で書かれるべきもの)
EN_FIELDS = ("passage", "title", "q", "options", "evidence")
# 和文フィールド
JA_FIELDS = ("explanation_ja", "distractor_ja", "translation_ja", "theme_ja", "genre")

FULLWIDTH = re.compile(r"[！-～　]")          # 全角英数記号・全角スペース
HANKAKU_KANA = re.compile(r"[｡-ﾟ]")             # 半角カタカナ
CIRCLED_OK = set("①②③④")
CIRCLED_ANY = re.compile(r"[①-⑳⓪]")        # ①〜⑳など


def en_texts(d):
    """(場所, 英文) を列挙。"""
    yield "passage", d.get("passage", "")
    yield "title", d.get("title", "")
    for i, q in enumerate(d["questions"], 1):
        yield f"問{i}.q", q.get("q", "")
        yield f"問{i}.evidence", q.get("evidence", "")
        for k, o in enumerate(q.get("options", []), 1):
            yield f"問{i}.選択肢{k}", o


def main():
    apos = collections.Counter()
    quot = collections.Counter()
    dash = collections.Counter()

    for no in range(1, 11):
        pid0 = f"{no:02d}"
        d = json.load(open(os.path.join(PASS, f"p{pid0}.json"), encoding="utf-8"))

        # ---- 英文フィールド ----
        for where, t in en_texts(d):
            if not t:
                continue
            loc = f"{pid0} {where}"
            m = FULLWIDTH.search(t)
            if m:
                add(NG, loc, "1", f"英文に全角文字 {m.group(0)!r} (U+{ord(m.group(0)):04X})")
            apos["'"] += t.count("'")
            apos["’"] += t.count("’")
            quot['"'] += t.count('"')
            quot["“"] += t.count("“") + t.count("”")
            for ch in ("–", "—"):
                dash[ch] += t.count(ch)
            # 段落区切りの \n\n を空白に変えると二重空白に見えるので、行ごとに見る
            if any("  " in line for line in t.split("\n")):
                add(WARN, loc, "4", "行内に二重スペースがある")
            # 引用の省略「… ... …」は英語の正しい用法なので除外
            if re.search(r"\s[,.;:!?](?!\.\.)", t.replace("...", "\x00").replace("…", "\x00")):
                add(NG, loc, "4", "句読点の前に空白がある")
            # a.m. / p.m. / e.g. / i.e. / U.S. は正しい略記なので除外してから見る
            tt = re.sub(r"\b(?:a\.m\.|p\.m\.|e\.g\.|i\.e\.|etc\.|U\.S\.|Mr\.|Ms\.|Mrs\.|Dr\.)", " ", t)
            if re.search(r"[a-z][.,;:][A-Za-z]", tt):
                add(NG, loc, "4", f"句読点の後に空白が無い: 「{re.search(chr(91)+'a-z'+chr(93)+'[.,;:][A-Za-z]', tt).group(0)}」")
            for c in CIRCLED_ANY.findall(t):
                if c not in CIRCLED_OK:
                    add(NG, loc, "7", f"①〜④以外の丸数字 {c}")

        # ---- 選択肢の体裁(4つで揃っているか) ----
        for i, q in enumerate(d["questions"], 1):
            opts = q.get("options", [])
            loc = f"{pid0} 問{i}"
            # 空所補充型は小文字始まりの句が正しい。**4つで揃っていない**ときだけ落とす。
            heads = [o[:1] for o in opts]
            caps = {h.isupper() for h in heads if h.isalpha()}
            if len(caps) > 1:
                add(NG, loc, "5", f"大文字始まりと小文字始まりが混在している {heads}")
            ends = [o.rstrip()[-1:] for o in opts]
            has_period = [e == "." for e in ends]
            if len(set(has_period)) != 1:
                add(NG, loc, "5", f"終止符の有無が4つで揃っていない {ends}")

        # ---- 同一題内での数字表記の揺れ ----
        blob = " ".join(t for _, t in en_texts(d) if t)
        # 時刻(9:00)/日付(April 6)/価格(600 yen)/割合(45 percent)/年(2026)/計測値は数字が正しい
        blob = re.sub(r"\d+:\d+|\b\d+\s*(?:percent|yen|words?|minutes?|hours?|degrees?|litres?|"
                      r"lessons?|stores?|shops?|cups?|nets?|students?|residents?)\b|"
                      r"(?:January|February|March|April|May|June|July|August|September|October|"
                      r"November|December)\s+\d+|\b(?:19|20)\d{2}\b|Day\s*\d+", " ", blob, flags=re.I)
        SPELL = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
                 "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twenty": 20, "thirty": 30}
        for word, val in SPELL.items():
            if re.search(rf"\b{word}\b", blob, re.I) and re.search(rf"\b{val}\b", blob):
                add(WARN, pid0, "6", f"「{word}」と「{val}」が同じ題に混在(綴りと数字の揺れ・要目視)")

        # ---- 和文フィールド ----
        for i, q in enumerate(d["questions"], 1):
            for k in ("explanation_ja", "distractor_ja"):
                t = q.get(k) or ""
                if HANKAKU_KANA.search(t):
                    add(NG, f"{pid0} 問{i}.{k}", "8", "半角カタカナが混ざっている")
        if HANKAKU_KANA.search(d.get("translation_ja") or ""):
            add(NG, pid0, "8", "全文和訳に半角カタカナ")

    # ---- 冊子全体での統一 ----
    print("アポストロフィ:", dict(apos), " 引用符:", dict(quot), " ダッシュ:", dict(dash))
    if apos["'"] and apos["’"]:
        add(NG, "全体", "2", f"アポストロフィが混在 直立 {apos[chr(39)]}個 / 曲 {apos['’']}個 → どちらかに統一")
    if quot['"'] and quot["“"]:
        add(NG, "全体", "2", f"引用符が混在 直立 {quot[chr(34)]}個 / 曲 {quot['“']}個")
    if dash["–"] and dash["—"]:
        add(WARN, "全体", "3", f"ダッシュが混在 en {dash['–']}個 / em {dash['—']}個")

    print(f"NG {len(NG)} 件 / WARN {len(WARN)} 件\n")
    for s in NG:
        print("NG   " + s)
    if WARN:
        print()
    for s in WARN[:25]:
        print("warn " + s)
    if len(WARN) > 25:
        print(f"... 他 {len(WARN)-25} 件")
    return 1 if NG else 0


if __name__ == "__main__":
    sys.exit(main())
