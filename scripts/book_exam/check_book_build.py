#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_book_build.py (全教科共通ビルダー) の自己検査。

    python3 scripts/book_exam/check_book_build.py

引数なしで**全シナリオ**を回す。run_all_gates.py が check* として自動で拾う。
Chrome も PDF ライブラリも要らない (純関数だけを叩く) ので CI でも同じものが走る。

■ なぜ要るか — 「記述式を混ぜた冊子」で壊れた実例 (2026-08-21)
    ビルダーの検査が **全問が選択式である前提**で書かれていた。記述 (short) を
    混ぜると次の 3 つが同時に壊れる。どれも「画面は壊れないのに教材が作れない」形:

    ① 3 連続の誤検出 — 選択式だけを詰めた配列の添字で見ていたので、
       第1・3・5問 (間に記述) が「第1問から 3 連続」になり、問番号もずれていた
    ② 偏りの分母 — 選択式 3 問 4 択で「各 0〜1 回に収めよ」を要求していた
    ③ 記述に誤答を書かせる — 選択肢が無いのに「誤答を潰す節」を必須にしていた

    ★ どれも「選択式しか無い冊子」では絶対に出ない。だから**混ぜたシナリオを
      検査に残す**。ここが緑なら、記述を混ぜた冊子が作れる。

■ 見るもの
    ・記述を混ぜても誤検出しないこと (①②③)
    ・**それでも本当の違反は捕まえること** (連続 3 問の偏り / 選択式の誤答節の欠け /
      解答漏洩 / 記述の正解が数字だけ / 別解を選択式に付けた など)
    ・build_json が記述を正しく写すこと (choice_count=null・別解・正解の文字列)
      — 写した結果を **import_books.validate_questions_py に通して**確かめる
    ・verify_pages が記述の解答欄の刷り漏れを捕まえること
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "materials"))
import import_books as ib   # noqa: E402  (取り込みの検証の正典)
import _book_build as B     # noqa: E402  (検査対象)

FAILED = []
N_CASE = 0


def case(label, got, want):
    """got (実際に出たエラー文の一覧) が want (期待する部分文字列) と合うか。

    want が [] なら「1 件も出ないこと」。want に文字列があれば、
    **その語を含むエラーがちょうど 1 件以上**あり、かつ余計なエラーが無いこと。
    """
    global N_CASE
    N_CASE += 1
    got = list(got)
    missing = [w for w in want if not any(w in g for g in got)]
    extra = [g for g in got if not any(w in g for w in want)]
    if missing or extra:
        FAILED.append(f"{label}\n      期待: {want}\n      実際: {got}")
        print(f"  [NG] {label}")
    else:
        print(f"  [ok] {label}")


META = {"stem": "自己検査", "title": "自己検査 冊子", "subject": "science",
        "subject_name": "理科", "level": "標準", "time_limit_min": 20}
H = B.SUBJECT_HEADINGS["science"]


def exp_choice(ans, choices):
    """選択式の解説 (誤答の節つき)。"""
    body = "\n".join(f"{h}説明。" for h in H[:-1]) + f"\n{H[-1]}\n"
    for i, c in enumerate(choices, 1):
        if i != ans:
            body += f"{i}. {c} — 誤り。\n"
    return body


def exp_short(with_last=False):
    body = "\n".join(f"{h}説明。" for h in H[:-1])
    return body + (f"\n{H[-1]}\nよくある誤り。" for _ in [0]).__next__() if with_last else body


def q_choice(no, page=1, ans=1, choices=("ア", "イ", "ウ", "エ"), stem=None):
    choices = list(choices)
    return dict(number=no, page=page, points=2, unit_tag="RIKA-TEST",
                stem=stem or f"第{no}問の設問文。", choices=choices, answer=ans,
                explanation=exp_choice(ans, choices))


def q_short(no, page=1, answer="電気抵抗", accepted=("抵抗",), stem=None,
            with_last=False, **kw):
    d = dict(number=no, page=page, points=2, unit_tag="RIKA-TEST",
             stem=stem or f"第{no}問の設問文。何というか。", answer=answer,
             accepted=list(accepted), explanation=exp_short(with_last))
    d.update(kw)
    return d


def main():
    print("=== _book_build 自己検査 (記述を混ぜた冊子で壊れないこと) ===")

    # --- ① 記述を混ぜても誤検出しない -------------------------------------
    mixed = [q_choice(1), q_short(2), q_choice(3), q_short(4), q_choice(5)]
    case("記述を挟んだ第1・3・5問が同じ正解番号でも 3 連続にしない",
         B.verify(META, mixed), [])
    case("記述の解説に誤答の節が無くてもよい",
         B.verify(META, [q_short(1), q_choice(2, ans=2)]), [])
    case("記述の解説に誤答の節を書いてもよい",
         B.verify(META, [q_short(1, with_last=True), q_choice(2, ans=2)]), [])
    case("全問が記述でも通る",
         B.verify(META, [q_short(1), q_short(2, answer="中和")]), [])

    # --- ② それでも本当の違反は捕まえる -----------------------------------
    case("設問番号が連続する 3 問が同じ正解番号なら落とす",
         B.verify(META, [q_choice(1), q_choice(2), q_choice(3), q_short(4)]),
         ["正解番号 1 が第1問から 3 連続"])
    # ★ 3 連続にはならない配り (1,2,1,2,… )。偏りだけを見たいので分ける
    skew = [q_choice(i, ans=1 if i % 2 else 2) for i in range(1, 11)]
    case("10 問 4 択で正解位置が偏っていれば落とす",
         B.verify(META, skew), ["正解位置が偏っている"])
    case("選択式の解説から誤答の節が欠けたら落とす",
         B.verify(META, [dict(q_choice(1), explanation="\n".join(
             f"{h}説明。" for h in H[:-1])), q_choice(2, ans=2)]),
         ["解説に「【誤答の切り方】」が無い"])
    case("記述の正解が数字だけなら落とす",
         B.verify(META, [q_short(1, answer="50")]),
         ["記述の正解が数字だけ"])
    case("記述の正解を数値で置いたら落とす",
         B.verify(META, [q_short(1, answer=50)]),
         ["記述の正解は文字列で書く", "記述の正解が数字だけ"]),
    case("別解を選択式に付けたら落とす",
         B.verify(META, [dict(q_choice(1), accepted=["ア"]), q_choice(2, ans=2)]),
         ["別解は記述のときだけ"])
    case("choices_plain を記述に付けたら落とす",
         B.verify(META, [q_short(1, choices_plain=["ア"])]),
         ["choices_plain は選択式のときだけ"])
    case("記述の答えが他問の設問文に刷られていたら落とす (解答漏洩)",
         B.verify(META, [q_choice(1, stem="電気抵抗について答えよ。"), q_short(2)]),
         ["記述の答え「電気抵抗」が問題編に印字されている"])

    # --- ③ 偏りを見送ったときは理由を言う ---------------------------------
    case("選択式が少なければ偏りは見ない (見送りを言葉で返す)",
         [B.spread_note(mixed) or ""], ["選択式 3 問 / 4 択では見ていない"])
    case("選択式が十分あれば見送らない",
         [B.spread_note(skew) or ""], [""])
    case("選択式が無ければそう言う",
         [B.spread_note([q_short(1)]) or ""], ["選択式が無いので見ていない"])

    # --- ④ build_json が記述を正しく写す -----------------------------------
    bundle = B.build_json(META, mixed)
    rows = bundle["questions"]
    shapes = [(r["answer_type"], r["choice_count"], r["correct_answer"],
               r.get("accepted_answers")) for r in rows]
    want = [("choice", 4, "1", None), ("short", None, "電気抵抗", ["抵抗"]),
            ("choice", 4, "1", None), ("short", None, "電気抵抗", ["抵抗"]),
            ("choice", 4, "1", None)]
    case("build_json が記述を choice_count=null・別解つきで写す",
         [] if shapes == want else [f"写しが違う {shapes}"], [])
    case("写した bundle が取り込みの検証を通る",
         ib.validate_questions_py(rows), [])

    # --- ⑤ 刷り上がりの逆照合 (ページのテキストだけを渡す) ------------------
    ok_page = ("自己検査 冊子 第1問（2点） 第1問の設問文。 1.ア 2.イ 3.ウ 4.エ "
               "第2問（2点） 第2問の設問文。何というか。 解答欄 "
               "第3問（2点） 第3問の設問文。 1.ア 2.イ 3.ウ 4.エ "
               "第4問（2点） 第4問の設問文。何というか。 解答欄 "
               "第5問（2点） 第5問の設問文。 1.ア 2.イ 3.ウ 4.エ")
    case("刷り上がりが正典どおりなら通る",
         B.verify_pages(META, mixed, [ok_page]), [])
    case("記述の解答欄が刷り漏れていたら落とす",
         B.verify_pages(META, mixed, [ok_page.replace("解答欄", "", 1)]),
         ["記述の解答欄が 2 個要るのに"])
    case("生の LaTeX が残っていたら落とす",
         B.verify_pages(META, mixed, [ok_page + r" $\frac{1}{2}$"]),
         ["生の LaTeX が残っている"])
    case("選択肢が刷り漏れていたら落とす",
         B.verify_pages(META, mixed, [ok_page.replace("4.エ", "", 1)]),
         ["選択肢 4 が PDF に無い"])
    case("同じ語が他問にあっても、番号ごと突き合わせるので誤魔化されない",
         B.verify_pages(META, mixed, [ok_page.replace("1.ア", "9.ア", 1)]),
         ["第1問: 選択肢 1 が PDF に無い"])

    # --- ⑥ 数式の選択肢 (KaTeX が描くので字形が変わる) ----------------------
    #   ★ KaTeX の負号は U+2212。ページ末尾にまとめて出るので設問ごとには切れない。
    mq = [dict(q_choice(1, choices=["$1$", "$3$", "$-3$", "$2$"], ans=3,
                        stem="2 次関数 $y = x^{2} - 4x + 1$ の最小値を求めよ。"),
               choices_plain=["1", "3", "-3", "2"],
               explanation="\n".join(f"{h}説明。" for h in H[:-1])
                           + f"\n{H[-1]}\n1. 1 — 誤り。\n2. 3 — 誤り。\n4. 2 — 誤り。\n"),
          q_choice(2, ans=2)]
    math_page = ("自己検査 冊子 第1問（2点） 2 次関数 の最小値を求めよ。 1. 2. 3. 4. "
                 "第2問（2点） 第2問の設問文。 1.ア 2.イ 3.ウ 4.エ "
                 "y = x \u2212 2 4x + 1 1 3 \u22123 2")
    case("KaTeX が描いた数式の選択肢も字面を突き合わせる (負号 U+2212 を吸収)",
         B.verify_pages(META, mq, [math_page]), [])
    case("数式の選択肢が刷り漏れていたら落とす",
         B.verify_pages(META, mq, [math_page.replace("\u22123", "")]),
         ["選択肢 3 が PDF に無い"])
    case("コマンド入りの数式は突き合わせられないと言う",
         [B.pdf_check_note([dict(q_choice(1), choices=["$\\frac{1}{2}$", "$b$"])]) or ""],
         ["1 個はコマンド入りの数式なので"])
    case("素の数式だけなら見送りは無い",
         [B.pdf_check_note(mq) or ""], [""])

    print(f"--- 見たもの: _book_build.verify / spread_note / build_json / "
          f"verify_pages — シナリオ {N_CASE} 件 ---")
    if FAILED:
        for f in FAILED:
            print(f"NG: {f}")
        print(f"違反 {len(FAILED)} 件")
        return 1
    print(f"=== ALL PASS (シナリオ {N_CASE}) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
