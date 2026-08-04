#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成した大問ごとの JSON を content_p1/p2/p3.py に組み立てる。

  python3 scripts/chugaku2_eigo_soufukushu/assemble.py <生成JSONのディレクトリ>

★大問の枠（配点・指示文・部の情報）はここが唯一のソース。作問エージェントには
  設問データだけを作らせ、配点や指示文は書かせない（食い違うと自己採点できない冊子になる）。
★空所の書式（(        ) / ( h )）はここで機械的に正規化する。エージェントの書式ゆれで
  組版の正規表現が外れると、空所が潰れた冊子や、ヒント文字が消えた冊子ができる。
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

PARTS = [
    {
        "no": 1,
        "level": "基礎の確認",
        "univ": "教科書の例文レベル／定期テストの基本問題",
        "aim": "まず形を思い出す部です。一文が短く、判断することは一つだけ。"
               "ここが8割取れたら第2部へ進んでください。",
        "time": 40,
        "total": 100,
        "steps": [
            "まず40分を目安に、最後まで解ききる（1回目は時間をこえてもよい）。",
            "わからない問題も飛ばさず、必ず何かを書いてから次へ進む。",
            "答え合わせのあと、間違えた問題の日本語をもう一度読み、自分で英文を作り直す。",
        ],
        "sections": [
            {"no": 1, "kind": "mc", "pt": 2, "src": "P1-Q1",
             "title": "空所補充（四択）",
             "inst": "次の各文の空所に入る最も適切なものを、①〜④から一つ選び、"
                     "その番号を◯で囲め。"},
            {"no": 2, "kind": "fill", "pt": 2, "src": "P1-Q2",
             "title": "空所補充（記述）",
             "inst": "次の各文の空所に入る適切な語句を書け（2語以上になることもある）。"
                     "空所のうしろに語が示してある場合は、その語を適切な形に変えて"
                     "書くこと。空所の中に文字が示してある場合は、その文字で始まる"
                     "語句を書くこと。"},
            {"no": 3, "kind": "order", "pt": 3, "src": "P1-Q3",
             "title": "語句整序",
             "inst": "日本語の意味を表すように、かっこ内の語をすべて並べ替えて英文を"
                     "完成させよ。文の最初に来る語も大文字で示してある"
                     "（人名と I はいつでも大文字）。"},
            {"no": 4, "kind": "rewrite", "pt": 4, "src": "P1-Q4",
             "title": "書き換え",
             "inst": "次の各文を、（　）内の指示にしたがって書き換えよ。"},
            {"no": 5, "kind": "trans", "pt": 4, "src": "P1-Q5",
             "title": "英作文",
             "inst": "次の日本語を英語に直せ。"},
        ],
    },
    {
        "no": 2,
        "level": "実力の確認",
        "univ": "定期テスト・実力テストの標準〜応用レベル",
        "aim": "第1部と同じ範囲を、少し長い文で問い直す部です。"
               "一文の中で決めることが二つになります。ここが8割取れたら第3部へ進んでください。",
        "time": 45,
        "total": 100,
        "steps": [
            "45分を計って解く。",
            "一文を読んだら、まず主語と動詞を指で押さえてから空所を見る。",
            "間違えた問題が12の単元のどれだったかを、解答解説編の一覧で必ず確かめる。",
        ],
        "sections": [
            {"no": 1, "kind": "mc", "pt": 2, "src": "P2-Q1",
             "title": "空所補充（四択）",
             "inst": "次の各文の空所に入る最も適切なものを、①〜④から一つ選び、"
                     "その番号を◯で囲め。"},
            {"no": 2, "kind": "fill", "pt": 2, "src": "P2-Q2",
             "title": "空所補充（記述）",
             "inst": "次の各文の空所に入る適切な語句を書け（2語以上になることもある）。"
                     "空所のうしろに語が示してある場合は、その語を適切な形に変えて"
                     "書くこと。空所の中に文字が示してある場合は、その文字で始まる"
                     "語句を書くこと。"},
            {"no": 3, "kind": "order", "pt": 3, "src": "P2-Q3",
             "title": "語句整序",
             "inst": "日本語の意味を表すように、かっこ内の語をすべて並べ替えて英文を"
                     "完成させよ。文の最初に来る語も大文字で示してある"
                     "（人名と I はいつでも大文字）。"},
            {"no": 4, "kind": "rewrite", "pt": 4, "src": "P2-Q4",
             "title": "書き換え",
             "inst": "次の各文を、（　）内の指示にしたがって書き換えよ。"},
            {"no": 5, "kind": "trans", "pt": 4, "src": "P2-Q5",
             "title": "英作文",
             "inst": "次の日本語を英語に直せ。"},
        ],
    },
    {
        "no": 3,
        "level": "総合仕上げ",
        "univ": "学年末の実力テスト／高校入試の入り口レベル",
        "aim": "一文の中に二つ以上の文法が入ります。読む力と書く力を同時に使う部です。"
               "ここで8割取れたら、中2の文法は仕上がったと考えてよいです。",
        "time": 50,
        "total": 100,
        "steps": [
            "50分を計って解く。",
            "一文の中で決めることが二つ以上ある。二つとも合って正解になる。",
            "8割に届かなかった単元は、第1部の同じ単元の問題をもう一度解き直す。",
        ],
        "sections": [
            {"no": 1, "kind": "mc", "pt": 2, "src": "P3-Q1",
             "title": "空所補充（四択）",
             "inst": "次の各文の空所に入る最も適切なものを、①〜④から一つ選び、"
                     "その番号を◯で囲め。"},
            {"no": 2, "kind": "error", "pt": 3, "src": "P3-Q2",
             "title": "誤りの指摘と訂正",
             "inst": "次の各文には文法上の誤りが1か所ある。誤りを含む部分の記号を一つ選び、"
                     "あわせて正しい形を書け。"},
            {"no": 3, "kind": "order", "pt": 3, "src": "P3-Q3",
             "title": "語句整序",
             "inst": "日本語の意味を表すように、かっこ内の語をすべて並べ替えて英文を"
                     "完成させよ。文の最初に来る語も大文字で示してある"
                     "（人名と I はいつでも大文字）。"},
            {"no": 4, "kind": "rewrite", "pt": 3, "src": "P3-Q4",
             "title": "書き換え",
             "inst": "次の各文を、（　）内の指示にしたがって書き換えよ。"},
            {"no": 5, "kind": "jtrans", "pt": 6, "src": "P3-Q5",
             "title": "英文和訳",
             "inst": "次の英文の下線部を日本語に直せ。下線のない部分は、"
                     "場面がわかるように示したものである。"},
            {"no": 6, "kind": "trans", "pt": 4, "src": "P3-Q6",
             "title": "英作文",
             "inst": "次の日本語を英語に直せ。"},
        ],
    },
]

EXPECT = {"P1-Q1": 10, "P1-Q2": 10, "P1-Q3": 8, "P1-Q4": 6, "P1-Q5": 3,
          "P2-Q1": 10, "P2-Q2": 10, "P2-Q3": 8, "P2-Q4": 6, "P2-Q5": 3,
          "P3-Q1": 10, "P3-Q2": 6, "P3-Q3": 8, "P3-Q4": 6, "P3-Q5": 2, "P3-Q6": 2}

KEEP = {
    "mc": ("unit", "stem", "choices", "ans", "exp", "point"),
    "fill": ("unit", "stem", "ans", "given", "hint", "accept", "exp", "point"),
    "order": ("unit", "ja", "frame", "tokens", "ans", "exp", "point"),
    "rewrite": ("unit", "src", "inst", "ans", "accept", "exp", "point"),
    "error": ("unit", "stem", "parts", "ans", "fix", "exp", "point"),
    "trans": ("unit", "ja", "model", "alts", "elements", "exp", "point"),
    "jtrans": ("unit", "context", "src", "model", "alts", "elements", "exp", "point"),
}

BLANK_MC = "(        )"
problems = []


def norm_item(kind, it, where):
    """空所の書式を組版の正規表現に合わせて正規化し、明らかな欠落を報告する。"""
    out = {k: it[k] for k in KEEP[kind] if it.get(k) not in (None, "", [], {})}

    if kind == "mc":
        n = len(re.findall(r"[（(]\s*[）)]", out.get("stem", "")))
        if n != 1:
            problems.append(f"{where} 四択の空所が {n} か所（1か所にすること）")
        out["stem"] = re.sub(r"[（(]\s*[）)]", BLANK_MC, out["stem"])

    if kind == "fill":
        h = str(out.get("hint", "")).strip()
        # 頭文字ヒントは空所の中に1文字だけ入れる書式に統一する
        blanks = re.findall(r"[（(]\s*[A-Za-z]?\s*[）)]", out.get("stem", ""))
        if len(blanks) != 1:
            problems.append(f"{where} 空所が {len(blanks)} か所（1か所にすること）")
        out["stem"] = re.sub(r"[（(]\s*[A-Za-z]?\s*[）)]",
                             f"( {h} )" if h else "(   )", out["stem"], count=1)
        if h:
            out["hint"] = h[0].lower()
            if not str(out["ans"]).lower().startswith(out["hint"]):
                problems.append(f'{where} 頭文字 {h} と解答「{out["ans"]}」が不一致')

    if kind == "error":
        # ★{a}〜{d} は「下線部をここに差し込む」印であって、下線部の文字列を
        #   そのまま並べて書くところではない。両方書くと組版が
        #   「(a)Did Kaito and AiriDid Kaito and Airi」と二重に刷る（実際に6問全部やった）。
        for j, c in enumerate("abcd"):
            if j < len(out.get("parts", [])):
                out["stem"] = out["stem"].replace("{%s}%s" % (c, out["parts"][j]),
                                                  "{%s}" % c)
        for j, c in enumerate("abcd"):
            if j < len(out.get("parts", [])) and out["parts"][j] in out["stem"]:
                problems.append(f'{where} 下線部「{out["parts"][j][:20]}」が stem にも'
                                f'書かれている（組版が二重に刷る）')

    if kind == "order":
        if out.get("frame", "").count("[") != 1:
            problems.append(f"{where} frame の [ ] が1組でない")
        # 組版は \[\s*\] を空所に置き換える。中に文字が残っていると空所にならない。
        out["frame"] = re.sub(r"\[[^\]]*\]", "[ ]", out.get("frame", ""))

    if kind in ("trans", "jtrans"):
        want = 4 if kind == "trans" else 3
        per = 1 if kind == "trans" else 2
        els = [list(e) for e in out.get("elements", [])]
        if len(els) != want or any(int(e[1]) != per for e in els):
            problems.append(f"{where} elements が {len(els)}個"
                            f"（{want}個×各{per}点にすること）")
        out["elements"] = [[str(e[0]), int(e[1])] for e in els]
        if not out.get("alts"):
            problems.append(f"{where} alts（別解）がない")

    for f, lo in (("exp", 40), ("point", 12)):
        if len(str(out.get(f, ""))) < lo:
            problems.append(f"{where} {f} が {lo}字未満/欠落")
    return out


def main(gendir):
    for part in PARTS:
        for s in part["sections"]:
            path = os.path.join(gendir, s["src"] + ".json")
            if not os.path.exists(path):
                sys.exit(f"× {path} がない")
            data = json.load(open(path))
            items = data["items"] if isinstance(data, dict) else data
            if len(items) != EXPECT[s["src"]]:
                problems.append(f'{s["src"]} が {len(items)}問'
                                f'（{EXPECT[s["src"]]}問のはず）')
            s["items"] = [norm_item(s["kind"], it, f'{s["src"]}-{i}')
                          for i, it in enumerate(items, 1)]
            s.pop("src")

    for part in PARTS:
        tot = sum(len(s["items"]) * s["pt"] for s in part["sections"])
        if tot != part["total"]:
            problems.append(f'第{part["no"]}部 実配点{tot} ≠ 表示{part["total"]}')
        body = json.dumps(part, ensure_ascii=False, indent=4)
        n = sum(len(s["items"]) for s in part["sections"])
        head = (f'# -*- coding: utf-8 -*-\n'
                f'"""第{part["no"]}部 {part["level"]}（{part["univ"]}）'
                f'{n}問／{part["total"]}点\n\n'
                f'★このファイルは assemble.py が生成する。手で直してよいが、\n'
                f'  再生成すると上書きされる（作問JSON側も直すこと）。\n"""\n\nPART = ')
        with open(os.path.join(HERE, f'content_p{part["no"]}.py'), "w") as f:
            f.write(head + body + "\n")
        print(f'  content_p{part["no"]}.py  {n}問 / {tot}点')

    if problems:
        print(f"\n=== 組み立て時の問題 {len(problems)}件 ===")
        for p in problems:
            print(" ×", p)
        sys.exit(1)
    print("\n組み立て OK")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "gen"))
