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
    case("解答欄に単位を刷ろうとしたら落とす (紙と画面で食い違う)",
         B.verify(META, [q_short(1, unit="A")]),
         ["unit は使えない"])
    case("数値+単位の答えなのに答え方を書いていなければ落とす",
         B.verify(META, [q_short(1, answer="4A", accepted=())]),
         ["答え方が設問文に無い"])
    case("答え方が設問文にあれば通る",
         B.verify(META, [q_short(1, answer="4A", accepted=(),
                                 stem="電流は何 A か。単位をつけて答えよ (例: 12A)。")]),
         [])

    # --- ⑦ 図 (SVG) と本文 --------------------------------------------------
    FIG = ('<svg viewBox="0 0 100 40"><text x="5" y="20">20 Ω</text>'
           '<text x="60" y="20">30 Ω</text></svg>')
    case("図の数値が設問文にあれば通る",
         B.verify(META, [dict(q_choice(1, stem="20 Ω と 30 Ω をつないだ。"), figure=FIG),
                         q_choice(2, ans=2)]), [])
    case("図に設問文に無い数値があれば落とす",
         B.verify(META, [dict(q_choice(1, stem="抵抗をつないだ。"), figure=FIG),
                         q_choice(2, ans=2)]),
         ["図の数値「20」が設問文にも本文にも無い",
          "図の数値「30」が設問文にも本文にも無い"])
    case("読み取らせる目盛りは figure_ticks で除ける",
         B.verify(META, [dict(q_choice(1, stem="抵抗をつないだ。"), figure=FIG,
                              figure_ticks=[20, 30]), q_choice(2, ans=2)]), [])
    case("図に script が入っていたら落とす",
         B.verify(META, [dict(q_choice(1), figure='<svg onload="x"></svg>'),
                         q_choice(2, ans=2)]),
         ["<script> / on* 属性"])
    case("図が <svg> で始まらなければ落とす",
         B.verify(META, [dict(q_choice(1), figure='<div>図</div>'), q_choice(2, ans=2)]),
         ["figure は <svg> から始める", "<script> / on* 属性"][:1])
    case("図の中の答えも解答漏洩として見る",
         B.verify(META, [dict(q_choice(1, stem="図を見よ。"),
                              figure='<svg><text>電気抵抗</text></svg>'), q_short(2)]),
         ["記述の答え「電気抵抗」が問題編に印字されている"])
    PASS_META = dict(META, passages=[{"page": 1, "title": "資料", "html":
                                      "<p>この資料は検査用である。</p>"}])
    case("本文があっても通る",
         B.verify(PASS_META, [q_choice(1), q_choice(2, ans=2)]), [])
    case("本文に script が入っていたら落とす",
         B.verify(dict(META, passages=[{"page": 1, "title": "資料",
                                        "html": "<script>x</script>"}]),
                  [q_choice(1), q_choice(2, ans=2)]),
         ["<script> / on* 属性"])
    case("本文の page は省略できる (刷り上がりから割り当てる)",
         B.verify(dict(META, passages=[{"title": "資料", "html": "<p>本文</p>"}]),
                  [q_choice(1), q_choice(2, ans=2)]), [])
    case("本文の title が無ければ落とす (照合に使う)",
         B.verify(dict(META, passages=[{"page": 1, "html": "<p>本文</p>"}]),
                  [q_choice(1), q_choice(2, ans=2)]),
         ["title が空"])

    # --- ⑫ ページの自動割り当て --------------------------------------------
    #   ★ 本文が数ページに渡る冊子では、正典に書いたページと刷り上がりが合わず、
    #     手で合わせ直す作業が何度も要った。刷ってから読み取れば必ず一致する。
    auto = [dict(q_choice(1), page=None), dict(q_choice(2, ans=2), page=None)]
    case("page を書かない冊子は通る", B.verify(META, auto), [])
    case("page を書く設問と書かない設問が混ざったら落とす",
         B.verify(META, [q_choice(1), dict(q_choice(2, ans=2), page=None)]),
         ["page を書く設問と書かない設問が混ざっている"])
    auto_meta = dict(META, passages=[{"title": "資料", "html": "<p>本文</p>"}])
    auto2 = [dict(q_choice(1), page=None), dict(q_choice(2, ans=2), page=None)]
    got = B.resolve_pages(auto_meta, auto2,
                          ["資料 本文 第1問（2点） 第1問の設問文。",
                           "第2問（2点） 第2問の設問文。"])
    case("刷り上がりから実ページを割り当てる", got, [])
    case("割り当てた結果が刷り上がりどおり",
         [f"{auto2[0]['page']},{auto2[1]['page']},{auto_meta['passages'][0]['page']}"],
         ["1,2,1"])
    case("刷り上がりに見出しが無ければ落とす",
         B.resolve_pages(dict(META, passages=[]),
                         [dict(q_choice(1), page=None)], ["何も無いページ"]),
         ["刷り上がりに「第1問（2点）」が見つからない"])

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
    # ★ \frac は寄せられるようになったので、寄せられない例は累乗にする
    case("寄せられない数式は「照合していない」と言う",
         [B.pdf_check_note([dict(q_choice(1), choices=["$x^{2}$", "$b$"])]) or ""],
         ["1 個はコマンド入りの数式なので"])
    case("素の数式だけなら見送りは無い",
         [B.pdf_check_note(mq) or ""], [""])

    # --- ⑧ 誤答の節が「最後の見出し」でない教科 (社会・国語) ----------------
    #   ★ 2026-08-21: 誤答の節を heads[-1] で決め打ちしていたため、社会
    #     (最後は【覚え方の目印】) と国語 (最後は【次に使える型】) では
    #     **誤答の番号を一度も見ないまま緑になっていた**。
    SOC = B.SUBJECT_HEADINGS["social"]
    SOC_META = dict(META, subject="social", subject_name="社会")

    def soc_q(no, ans=1, ngs=None, choices=("ア", "イ", "ウ", "エ")):
        choices = list(choices)
        if ngs is None:
            ngs = [f"{i}. {c} — 誤り。" for i, c in enumerate(choices, 1) if i != ans]
        body = "\n".join(f"{h}説明。" for h in SOC[:3])
        body += "\n" + SOC[3] + "\n" + "\n".join(ngs) + "\n" + SOC[4] + "目印。"
        return dict(number=no, page=1, points=2, unit_tag="SHAKAI-TEST",
                    stem=f"第{no}問の設問文。", choices=choices, answer=ans,
                    explanation=body)

    case("誤答の節が最後の見出しでない教科でも、正しく組めば通る",
         B.verify(SOC_META, [soc_q(1), soc_q(2, ans=2)]), [])
    case("誤答の節が最後でない教科でも、誤答の欠けを捕まえる",
         B.verify(SOC_META, [soc_q(1, ngs=["2. イ — 誤り。", "3. ウ — 誤り。"]),
                             soc_q(2, ans=2)]),
         ["誤答 4 の説明が無い"])
    case("誤答の節が最後でない教科でも、正解が誤答に載っていたら捕まえる",
         B.verify(SOC_META, [soc_q(1, ngs=["1. ア — 誤り。", "2. イ — 誤り。",
                                           "3. ウ — 誤り。", "4. エ — 誤り。"]),
                             soc_q(2, ans=2)]),
         ["正解 1 が誤答の節に載っている"])
    case("ng_heading は見出し名から引く",
         [B.ng_heading(SOC) or "", B.ng_heading(B.SUBJECT_HEADINGS["grammar"]) or ""],
         ["【誤答の切り方】", "## ❌ 誤答 NG 理由"])

    # --- ⑨ 前書きが「第1問」に触れていても設問の切り分けがずれない ----------
    #   ★ 2026-08-21: 「第N問」だけで探していたため、前書きの
    #     「第1問〜第3問は資料を見て答えよ」を設問の先頭と誤認し、
    #     以降の照合が丸ごとずれた。配点まで含めた見出しで引く。
    trap = ("第1問〜第3問は資料を見て答えてください。 "
            "第1問（2点） 第1問の設問文。 1.ア 2.イ 3.ウ 4.エ "
            "第2問（2点） 第2問の設問文。 1.ア 2.イ 3.ウ 4.エ")
    two = [q_choice(1), q_choice(2, ans=2)]
    case("前書きが「第1問」に触れていても照合がずれない",
         B.verify_pages(META, two, [trap]), [])
    case("見出しが無ければ「見つからない」と言う",
         B.verify_pages(META, two, [trap.replace("第2問（2点）", "")]),
         ["第2問: PDF の 1 ページに「第2問（2点）」が無い"])

    # --- ⑩ 埋め込みフォント (字形が日本語か) --------------------------------
    #   ★ 2026-08-21: 日本語フォントが 1 つも入っていない環境で刷ったため、
    #     committed 19 冊すべてが**中国語フォント**で組まれていた。
    #     PDF は正常に出るしテキスト抽出も通るので、紙を見るまで気づけない。
    case("日本語フォントで組まれていれば通る",
         B.font_problems({"AAAAAA+IPAexMincho", "BAAAAA+IPAexGothic",
                          "CAAAAA+LiberationSans"}), [])
    case("Mac のヒラギノでも通る",
         B.font_problems({"AAAAAA+HiraMinProN-W3", "BAAAAA+HiraKakuProN-W6"}), [])
    case("中国語フォントに落ちていたら落とす",
         B.font_problems({"AAAAAA+WenQuanYiZenHei", "CAAAAA+LiberationSans"}),
         ["日本語でないフォントで組まれている"])
    case("フォントが 1 つも無ければ落とす", B.font_problems(set()),
         ["フォントが 1 つも埋め込まれていない"])
    case("空文字だけでも落とす", B.font_problems({""}),
         ["フォントが 1 つも埋め込まれていない"])

    # --- ⑪ 長い選択肢 (共通テスト型) の誤答照合 ----------------------------
    LONG = ["本文の主張と反対の立場を紹介し、それを退けることで補強している。",
            "本文の主張を要約し、読み手が筋を見失わないよう整理している。",
            "前段落の具体例を一般化し、次の結論へ橋を渡している。",
            "筆者の体験を挙げ、読み手の共感を得ようとしている。"]

    def long_q(no, ans, ngs):
        body = "\n".join(f"{h}説明。" for h in H[:-1])
        body += "\n" + H[-1] + "\n" + "\n".join(ngs)
        return dict(number=no, page=1, points=3, unit_tag="LONG-TEST",
                    stem=f"第{no}問の設問文。", choices=list(LONG), answer=ans,
                    explanation=body)

    ok_ngs = [f"{i}. {c[:14]} — 誤り。" for i, c in enumerate(LONG, 1) if i != 1]
    case("長い選択肢は書き出しを引けば通る (全文を写さなくてよい)",
         B.verify(META, [long_q(1, 1, ok_ngs), q_choice(2, ans=2)]), [])
    bad_ngs = ["2. 要約し、読み手が — 誤り。"] + ok_ngs[1:]
    case("書き出しを省いて途中から引いたら落とす",
         B.verify(META, [long_q(1, 1, bad_ngs), q_choice(2, ans=2)]),
         ["誤答 2 の説明が選択肢と合っていない"])
    case("書き出しがかぶる選択肢は、かぶりが解けるまで引かせる",
         [B.distinguishing_prefix(["S = -2x^2 + 40x", "S = -2x^2 + 20x"], 0)],
         ["S = -2x^2 + 4"])
    case("書き出しが違えば 1 字で足りる",
         [B.distinguishing_prefix(["ア案", "イ案"], 0)], ["ア"])

    # --- ⑬ 分数と Markdown -------------------------------------------------
    #   ★ KaTeX の \frac{a}{b} は PDF から **分母 → 分子** の順で抽出され、
    #     手前に幅ゼロの空白 (U+200B) が入る (2026-08-21 実測)。
    #     これを知らなかったので、分数の選択肢は 1 つも照合できていなかった。
    case("分数は「分母→分子」に寄せる",
         [B.tex_as_printed(r"\frac{3}{10}") or ""], ["103"])
    case("累乗は寄せられないと言う",
         ["寄せられない" if B.tex_as_printed(r"x^{2}") is None else "寄せた"],
         ["寄せられない"])
    case("不等号のコマンドは字に直す",
         [B.tex_as_printed(r"5 \leqq x \leqq 15") or ""], ["5 ≦ x ≦ 15"])
    case("幅ゼロの空白を落として突き合わせる",
         [B.norm_pdf("\u200b\n10\n3")], ["103"])
    frac_q = [dict(q_choice(1, choices=[r"$\frac{1}{10}$", r"$\frac{3}{7}$",
                                        r"$\frac{3}{10}$", r"$\frac{7}{10}$"],
                            ans=3, stem="確率を 1 つ選べ。"),
                   choices_plain=["1/10", "3/7", "3/10", "7/10"],
                   explanation="\n".join(f"{h}説明。" for h in H[:-1])
                               + f"\n{H[-1]}\n1. 1/10 — 誤り。\n2. 3/7 — 誤り。"
                                 f"\n4. 7/10 — 誤り。"),
              q_choice(2, ans=2)]
    frac_page = ("自己検査 冊子 第1問（2点） 確率を 1 つ選べ。 1. 2. 3. 4. "
                 "第2問（2点） 第2問の設問文。 1.ア 2.イ 3.ウ 4.エ "
                 "\u200b 10 1 \u200b 7 3 \u200b 10 3 \u200b 10 7")
    case("分数の選択肢も刷り上がりと突き合わせる",
         B.verify_pages(META, frac_q, [frac_page]), [])
    case("分数の選択肢が刷り漏れていたら落とす",
         B.verify_pages(META, frac_q, [frac_page.replace("\u200b 10 3 ", "")]),
         ["選択肢 3 が PDF に無い"])
    case("分数なら「照合していない」は出ない",
         [B.pdf_check_note(frac_q) or ""], [""])

    case("設問文に Markdown の太字を書いたら落とす",
         B.verify(META, [dict(q_choice(1), stem="**強調**した設問文。"),
                         q_choice(2, ans=2)]),
         ["Markdown の太字"])
    case("本文に Markdown の太字を書いたら落とす",
         B.verify(dict(META, passages=[{"title": "資料",
                                        "html": "<p>**強調**</p>"}]),
                  [q_choice(1), q_choice(2, ans=2)]),
         ["Markdown の太字"])
    case("解説の ** は許す (画面は素のテキスト表示)",
         B.verify(META, [dict(q_choice(1), explanation=exp_choice(
             1, ["ア", "イ", "ウ", "エ"]) + "\n**ここは強調してよい**"),
             q_choice(2, ans=2)]), [])

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
