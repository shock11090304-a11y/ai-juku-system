#!/usr/bin/env python3
"""収録語のレベルを機械で見る (run_all_gates.py が拾う)。

    python3 scripts/eiken_tango_test/check_cefr.py

■ なぜ要るか (2026-08-19)
  問題編の表紙は「収録語はすべて CEFR B2〜C1（準1級相当）以上です」と**断言**していた。
  ところが README 自身が「照合したのは第1〜10回の160単語だけ。第11〜20回の200語は
  CEFR 表と突き合わせていない」と書いており、**半分は未検証のまま断言する紙**だった。
  実際に照合したところ第18回に B1 の語が2つあり、断言は事実に反していた。
  ★紙は刷ったら直せない。レベルの主張は毎回ここで機械照合する。

■ 何を見るか
  1. content.py の単語が全部 `_cefr_levels.tsv` に載っているか
     (載っていない = **一度も調べていない語**。足したまま調べ忘れるのを止める)
  2. B2 未満の語が無いか。あるなら ALLOW に理由つきで挙がっているか
  3. 表紙の文言が実測と矛盾していないか (「すべて」と言い切っていないか)

■ 熟語は対象外
  Oxford 3000/5000 は単語のリストで、句動詞・イディオムのレベルは載っていない。
  熟語の易化は check.py の TOO_EASY_IDIOM が別途見る。
"""
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "_cefr_levels.tsv")
CONTENT = os.path.join(HERE, "content.py")
BUILD = os.path.join(HERE, "build.py")
MONDAI = os.path.join(HERE, "mondai.html")   # 刷り上がり (gitignore 対象。CI には無い)

ORDER = ["A1", "A2", "B1", "B2", "C1"]
MIN_LEVEL = "B2"
POS_JA2EN = {"動": "verb", "名": "noun", "形": "adjective", "副": "adverb"}

# B2 未満でも収録してよい語と、その理由。★理由なしで足さないこと。
ALLOW = {
    ("sensible", "adjective"):
        "第18回「紛らわしい形容詞」で sensitive との識別を問うための語。"
        "語そのものは B1 だが、『分別のある』の語義と sensitive との対比は準1級で頻出。",
    ("historic", "adjective"):
        "第18回「紛らわしい形容詞」で historical との識別を問うための語。"
        "語そのものは B1 だが、『歴史に残る』と historical『歴史の』の対比は準1級で頻出。",
}


def load_levels():
    """_cefr_levels.tsv → {(word, pos): level}。pos が '-' の行は NOT_LISTED。"""
    out = {}
    with open(TSV, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 3:
                return None, f"_cefr_levels.tsv の形式が壊れている: {line!r}"
            w, pos, lv = (p.strip() for p in parts)
            # ★大文字に正規化して**必ず検証する**。Oxford の公式ページはレベルを
            #   小文字 (b1) で表示するので、README の手順どおり書き写すと小文字になる。
            #   検証せずに `lv in ORDER` で判定すると、小文字の b1 が「B2未満ではない」
            #   として黙って通り、このゲートが在る理由そのものの事故が再現する。
            lv_u = lv.upper()
            if lv_u not in ORDER and lv_u != "NOT_LISTED":
                return None, (f"_cefr_levels.tsv のレベル値が不正: {lv!r} (行: {line!r})。"
                              f"使えるのは {'/'.join(ORDER)} と NOT_LISTED だけ")
            out[(w.lower(), pos)] = lv_u
    return out, None


def load_items():
    spec = importlib.util.spec_from_file_location("_content", CONTENT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    items = []
    for t in mod.TESTS:
        for it in t["items"]:
            head, pos = it[0].strip(), it[1]
            items.append({"test": t["no"], "head": head, "pos_ja": pos,
                          "is_idiom": " " in head})
    return items


def main():
    problems = []
    levels, err = load_levels()
    if err:
        print(f"✗ {err}")
        return 1
    items = load_items()
    words = [i for i in items if not i["is_idiom"]]
    print(f"収録語のレベル照合: 単語 {len(words)} / 熟語 {len(items) - len(words)} (熟語は対象外)")

    counts = {"NOT_LISTED": 0}
    below = []
    for it in words:
        w = it["head"].lower()
        pos_en = POS_JA2EN.get(it["pos_ja"])
        if pos_en is None:
            problems.append(f"第{it['test']}回 {it['head']}: 品詞 {it['pos_ja']!r} を英語品詞に対応づけられない")
            continue
        # その語の全エントリ (品詞違いを含む)
        entries = {p: lv for (ww, p), lv in levels.items() if ww == w}
        if not entries:
            problems.append(f"第{it['test']}回 {it['head']}: _cefr_levels.tsv に無い "
                            f"= レベルを一度も調べていない。Oxford 3000/5000 で引いて1行足すこと")
            continue
        # 出題している品詞のエントリを優先。無ければその語の最も易しいレベルで見る
        if pos_en in entries:
            lv = entries[pos_en]
        elif "-" in entries:
            lv = entries["-"]
        else:
            lv = sorted(entries.values(), key=lambda x: ORDER.index(x) if x in ORDER else 99)[0]
        counts[lv] = counts.get(lv, 0) + 1
        if lv in ORDER and ORDER.index(lv) < ORDER.index(MIN_LEVEL):
            key = (w, pos_en)
            if key not in ALLOW:
                problems.append(f"第{it['test']}回 {it['head']} ({pos_en}) が {lv} "
                                f"= {MIN_LEVEL} 未満。準1級の教材に入れる理由が無ければ差し替える。"
                                f"意図的なら check_cefr.py の ALLOW に理由つきで足すこと")
            else:
                below.append((it["test"], it["head"], lv))

    n_listed = sum(v for k, v in counts.items() if k != "NOT_LISTED")
    n_listed_b2plus = sum(v for k, v in counts.items()
                          if k in ORDER and ORDER.index(k) >= ORDER.index(MIN_LEVEL))
    order_out = [f"{k}:{counts.get(k, 0)}" for k in ORDER if counts.get(k)]
    print("  内訳 " + " / ".join(order_out) + f" / Oxford3000-5000圏外:{counts['NOT_LISTED']}")
    print(f"  リストで裏が取れた語 {n_listed} (うち {MIN_LEVEL} 以上 {n_listed_b2plus}) / "
          f"根拠が無い語 {counts['NOT_LISTED']}")
    if below:
        print(f"  ({MIN_LEVEL} 未満だが意図的に収録 {len(below)}件: "
              + ", ".join(f"第{t}回 {w}({lv})" for t, w, lv in below) + ")")

    # --- 表紙の主張が実測と合っているか -------------------------------------
    # ★2段で見る。
    #   (a) build.py のソース: 数字を**ハードコードしていない**こと (%d で持つこと)。
    #       ここを literal にすると、回や語を足したとき表紙だけ古い数字が残る
    #       (build.py の stats() の docstring が「過去に実際に起きた」と書いている事故)。
    #   (b) 刷り上がり (mondai.html): 実際に印字された数字を**独立に数え直した値**と突き合わせる。
    #       ソースだけ見ると %d を数字として読めず、照合が空振りする。
    try:
        src = open(BUILD, encoding="utf-8").read()
    except OSError as e:
        problems.append(f"build.py を読めない ({e})")
        src = ""
    m = re.search(r"'収録語[^']*'", src)
    if not m:
        problems.append("build.py の表紙に収録語の記述が見つからない "
                        "(文言を変えたらこのゲートの探し方も直すこと)")
    else:
        tmpl = m.group(0)
        if re.search(r"\d+\s*語", tmpl):
            problems.append(f"表紙の語数がハードコードされている。cefr_stats() の値を %d で渡すこと: {tmpl!r}")
        if "すべて" in tmpl or "全て" in tmpl:
            problems.append(f"表紙が「すべて」と言い切っている。Oxford 3000/5000 圏外の語は"
                            f"レベルの根拠が無いので断言できない: {tmpl!r}")

    if os.path.exists(MONDAI):
        cover = open(MONDAI, encoding="utf-8").read()
        mm = re.search(r'<div class="spec">(.*?)</div>', cover, re.S)
        spec = re.sub(r"<[^>]+>", " ", mm.group(1)) if mm else ""
        seg = re.search(r"収録語[^。]*。[^。]*。", spec)
        if not seg:
            problems.append("刷り上がり (mondai.html) に収録語の記述が見つからない")
        else:
            # ★「頻出上位5000語」のような説明中の数字を拾わないよう、位置を特定して取る
            pats = [(r"収録語\s*(\d+)\s*語", "総数", len(words)),
                    (r"載る\s*(\d+)\s*語", "リスト内", n_listed),
                    (r"は\s*(\d+)\s*語が", "うちB2以上", n_listed_b2plus),
                    (r"残り\s*(\d+)\s*語", "圏外", counts["NOT_LISTED"])]
            for pat, name, exp in pats:
                mp = re.search(pat, seg.group(0))
                if not mp:
                    problems.append(f"刷り上がりから「{name}」の数字を読めない (文言を変えたら "
                                    f"check_cefr.py の pats も直すこと): {seg.group(0)!r}")
                elif int(mp.group(1)) != exp:
                    problems.append(f"刷り上がりの「{name}」が実測と違う: 印字 {mp.group(1)} / 実測 {exp}")
            print(f"  刷り上がりの記述: {' '.join(seg.group(0).split())}")
    else:
        # ★「見ていない」を「問題なし」と言わない
        print("  刷り上がり (mondai.html) が無いので印字の数字は検査していない "
              "(python3 build.py を回してから再実行すると照合する)")

    if problems:
        print(f"\n✗ VIOLATION: {len(problems)} 件")
        for p in problems:
            print(f"   - {p}")
        return 1
    print("\n=== ALL PASS (収録語のレベル照合) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
