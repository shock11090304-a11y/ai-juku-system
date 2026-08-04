# -*- coding: utf-8 -*-
"""中学2年生 英文法 総復習問題集 — 単一ソース。

組版・機械ゲート・盲検証は英文法問題集の機械と共有する（データだけがここにある）:
  WORKBOOK_DIR=scripts/chugaku2_eigo_soufukushu python3 scripts/eng_kokkoritsu_nankan/build.py

★部扉・大問見出し・前書きに文法項目名を書かないこと（書いた瞬間に何を問う大問かが割れる）。
  扱う単元の一覧と変化表は「解答解説編の巻頭」に置く（BOOK["tables"] / BOOK["flows"]）。
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content_p1 import PART as P1  # noqa: E402
from content_p2 import PART as P2  # noqa: E402
from content_p3 import PART as P3  # noqa: E402

# 問題編に印字してよいフィールド（★ここに exp / point / ans / model を足さないこと。
# 足した瞬間に「答えが問題編に載る」＝知識ゼロで得点できる冊子になる）
Q_FIELDS = ("stem", "choices", "parts", "frame", "tokens", "ja", "src", "inst",
            "given", "hint", "context")

KIND_LABEL = {
    "mc": "四択",
    "fill": "空所補充",
    "order": "語句整序",
    "rewrite": "書き換え",
    "trans": "英作文",
    "error": "誤りの指摘",
    "jtrans": "英文和訳",
}


def _subtitle():
    """★表紙の出題形式リストは実データから作る。手書きにすると必ず古くなる。
    初版は手書きで「誤りの指摘」と「英文和訳」（計30点分）が漏れていた。"""
    seen = []
    for p in (P1, P2, P3):
        for s in p["sections"]:
            if KIND_LABEL[s["kind"]] not in seen:
                seen.append(KIND_LABEL[s["kind"]])
    return "／".join(seen)


BOOK = {
    "title": "中学2年生 英文法 総復習問題集",
    "sub": _subtitle(),
    "series": "トリリオン英語塾　中学英語コース",
    "file": "中2英文法_総復習問題集",
    "intro": [
        ("この問題集について",
         "中学2年生で習う文法を、1年分まとめて復習するための問題集です。"
         "第1部から第3部まで、同じ範囲を3回、少しずつむずかしくしながら解き直します。"
         "3回とも解けるようになれば、中2の文法はひととおり身についたと考えてよいです。"),
        ("三部構成のねらい",
         "第1部（基礎の確認）→第2部（実力の確認）→第3部（総合仕上げ）と進みます。"
         "扱う範囲はどの部も同じで、一文が長くなり、1つの文で気をつけることが増えていきます。"
         "その部だけで1回分のテストになります（各100点満点）。時間を計って解いてください。"),
        ("解き方の約束",
         "① 辞書を使わずに、まず最後まで解く。\n"
         "② 答え合わせのあと、間違えた問題の「▶ポイント」（解答解説編の各問についている"
         "▶の一行）だけをノートに書き写す。\n"
         "③ 一週間後に同じ部をもう一度解く。\n"
         "四択で当たった問題も、他の三つがなぜ誤りかを言えるまでは「解けた」と数えません。"),
        ("採点のしかた",
         "① 四択・空所補充・語句整序・書き換えは、解答編の答えと一致していれば正解です"
         "（解答編に別解が示してあるものは、それでも正解です）。"
         "語句整序は語順が完全に一致していることが必要です。\n"
         "② 誤りの指摘と訂正は、記号と正しい形の両方が合っていて満点です"
         "（記号だけ合っていた場合は1点とします）。\n"
         "　正しい形は、直したあとの語句だけを書けば正解とします"
         "（2語以上になることもあります）。\n"
         "③ 英文和訳と英作文（和文英訳）の2つは、模範解答と一字一句同じである必要は"
         "ありません。解答編の「採点のポイント」を1つ満たすごとに、英文和訳は2点、"
         "英作文は1点を与えてください。ポイントは、日本語の意味がぬけていないかを見る"
         "ためのものなので、模範解答と同じ言い方をしている必要はありません。"
         "1つのポイントを半分だけ満たしたときは、解答編の表に書いてある部分点に"
         "したがってください。"),
        ("復習する範囲",
         "中学2年生で学ぶ文法事項の全体を扱います。どの部にも全単元から出題されるので、"
         "「この部はここが出る」とヤマを張ることはできません。"
         "扱う単元の一覧と、覚えておきたい変化表は、解答解説編の巻頭「基本の確認」に"
         "まとめてあります。答え合わせのときに開いてください。"),
        ("教科書によって学年が変わる項目",
         "使っている教科書によっては、次の4つを中学3年生で習います。"
         "まだ習っていない問題が出てきたら、解答解説編の「基本の確認」と解説を読んでから"
         "解き直してください。\n"
         "①「〜される」の言い方　②「〜してうれしい」など気持ちの原因を表す to ＋ 動詞の原形"
         "　③〈call ＋ 人 ＋ 呼び名〉　④ 形だけの主語 It を立てる It is ... to 〜"),
    ],
    "parts": [P1, P2, P3],

    # 部構成の表と同じページに置く案内（前書きが長いと表だけのページになるため）
    "after_table": [
        ("1冊を2回使うために",
         "1回目はこの本に直接書き込みます。2回目は答えをノートに書けば、同じ本をもう一度"
         "使えます。語句整序と英作文は、書き写すだけでも力がつくので、2回目はノートに"
         "英文を丸ごと書いてみてください。"),
        ("答え合わせのタイミング",
         "1問ごとに答えを見ないでください。大問が1つ終わるごと、できれば1つの部が"
         "終わってからまとめて答え合わせをします。"
         "とちゅうで答えを見ると、自分がどこでつまずいたのかが分からなくなります。"),
        ("解答解説編の使い方",
         "答えが合っていた問題も、解説の ▶ の一行だけは読んでください。"
         "▶ の先頭には〔単元1〕〜〔単元12〕と番号が付いています。"
         "間違いが同じ番号に集まっていたら、その単元をやり直すのがいちばん早い直し方です。"),
    ],

    # ★以下は「解答解説編の巻頭」だけに刷る。問題編に置くと、表を写すだけで解ける設問が出る。
    "tables": [
        {
            "title": "▲ 変化のしかたが決まっていない動詞（中2で必ず使うもの）",
            "lead": "「〜した」と「〜される」の文で必要になります。3つ続けて声に出して覚えてください。解説では3つめを「過去分詞」と呼んでいます。",
            "headers": ["もとの形", "意味", "〜した（過去形）", "〜される（過去分詞）"],
            "widths": [42, 44, 58, 68],
            "rows": [
                ["be (am, is, are)", "〜である", "was, were", "been"],
                ["begin", "始める", "began", "begun"],
                ["break", "こわす", "broke", "broken"],
                ["bring", "持ってくる", "brought", "brought"],
                ["build", "建てる", "built", "built"],
                ["buy", "買う", "bought", "bought"],
                ["catch", "つかまえる", "caught", "caught"],
                ["come", "来る", "came", "come"],
                ["do", "する", "did", "done"],
                ["eat", "食べる", "ate", "eaten"],
                ["find", "見つける", "found", "found"],
                ["get", "手に入れる", "got", "gotten / got"],
                ["give", "あたえる", "gave", "given"],
                ["go", "行く", "went", "gone"],
                ["have", "持っている", "had", "had"],
                ["hear", "聞こえる", "heard", "heard"],
                ["hold", "開く・持つ", "held", "held"],
                ["know", "知っている", "knew", "known"],
                ["leave", "去る・残す", "left", "left"],
                ["make", "作る", "made", "made"],
                ["meet", "会う", "met", "met"],
                ["put", "置く", "put", "put"],
                ["read", "読む", "read (レッド)", "read (レッド)"],
                ["run", "走る", "ran", "run"],
                ["say", "言う", "said", "said"],
                ["see", "見える", "saw", "seen"],
                ["sing", "歌う", "sang", "sung"],
                ["speak", "話す", "spoke", "spoken"],
                ["take", "取る・連れて行く", "took", "taken"],
                ["teach", "教える", "taught", "taught"],
                ["tell", "伝える", "told", "told"],
                ["think", "思う", "thought", "thought"],
                ["write", "書く", "wrote", "written"],
            ],
            "note": "▲ read は形が変わらないが、〜した・〜される のときは「レッド」と読む。"
                    "put / cut / hurt も3つとも同じ形。",
        },
        {
            "title": "▲ 2つ・3つ以上を比べるときの形",
            "lead": "than があれば2つを比べる形、the がついていれば3つ以上で一番、が目印です。",
            "headers": ["もとの形", "2つを比べる形（比較級）", "一番の形（最上級）", "気をつけること"],
            "widths": [40, 56, 54, 62],
            "rows": [
                ["tall", "taller", "tallest", "短い語は -er / -est を付ける"],
                ["large", "larger", "largest", "e で終わる語は -r / -st だけ"],
                ["big", "bigger", "biggest", "最後の1字を重ねてから付ける"],
                ["easy", "easier", "easiest", "〈子音字＋y〉は y を i に変える"],
                ["famous", "more famous", "most famous", "長い語は前に more / most を置く"],
                ["important", "more important", "most important", "同上（-er を付けない）"],
                ["good / well", "better", "best", "形そのものが変わる"],
                ["bad", "worse", "worst", "形そのものが変わる"],
                ["many / much", "more", "most", "形そのものが変わる"],
                ["little", "less", "least", "形そのものが変わる"],
            ],
            "note": "▲ 比べる形を強めるのは much / far。very は使えない（very は もとの形 に付ける）。"
                    "▲ 一番の形のあとは、場所や範囲なら in、仲間の数なら of。",
        },
        {
            "title": "▲ この問題集で復習する12の単元",
            "lead": "どの部にも、この12単元すべてから出題されています。"
                    "答え合わせのとき、間違えた問題がどの単元かをここで確かめてください。",
            "headers": ["", "単元", "基本の形と例"],
            "widths": [16, 66, 130],
            "rows": [
                ["1", "〜した（be動詞・一般動詞）",
                 "was / were ／ 動詞 + ed ／ Did + 主語 + 原形 ?"],
                ["2", "〜していた", "was / were + -ing"],
                ["3", "これから〜する", "will + 原形 ／ be going to + 原形"],
                ["4", "〜しなければ／〜してもよい など（助動詞）",
                 "must, have to, may, should, Can you 〜?, Shall I 〜?"],
                ["5", "2つの文をつなぐ語", "when, while, if, because, that, before, after"],
                ["6", "〜がある・いる", "There is / are + 名詞 + 場所"],
                ["7", "to + 動詞の原形", "〜すること／〜するための／〜するために"],
                ["8", "動詞の -ing 形が名詞のはたらきをする形",
                 "enjoy -ing ／ 前置詞 + -ing ／ -ing が主語"],
                ["9", "〈動詞＋人＋物〉と〈動詞＋人＋呼び名・ようす〉",
                 "give me a pen ／ call him Ken ／ make me happy"],
                ["10", "くらべる言い方", "as 〜 as ／ -er than ／ the -est ／ more, most"],
                ["11", "〜される・〜されている（受け身）", "be動詞 + 過去分詞（+ by 〜）"],
                ["12", "It is ... to 〜 ／ 疑問詞 + to 〜 ／〈人＋to 〜〉",
                 "It is easy to swim. ／ how to use ／ want him to come"],
            ],
            "note": "▲ 現在完了・関係代名詞・分詞のあと置き・間接疑問文は中3の内容なので、"
                    "この問題集では扱っていません。",
        },
    ],
    "flows": [
        {
            "title": "◆ to ＋ 動詞の原形 — 3つの用法の見分け方",
            "steps": [
                "その to 〜 を消してみる。文が成り立たなくなる（主語や目的語が足りない）なら"
                "「〜すること」。\n"
                "例）I want to swim. → I want. では意味が足りない。",
                "消しても文が成り立ち、直前の名詞を「〜するための◯◯」と説明していれば"
                "「〜するための」。\n"
                "例）I have something to eat.（食べるための物）\n"
                "直前が名詞でも、その名詞を説明していないなら次へ。",
                "上のどちらでもなければ「〜するために」「〜して」。\n"
                "例）I got up early to catch the bus.（バスに乗るために早く起きた）\n"
                "例）I am glad to see you.（会えてうれしい）\n"
                "★直前が名詞でも、その名詞の説明になっていなければこちら。\n"
                "例）I went to the park to play tennis. の to play は park の説明ではない。",
            ],
            "warn": "▲ 直前が glad, happy, sorry, surprised のような気持ちを表す語のときは、"
                    "「〜して（うれしい）」と気持ちの原因を表す。",
        },
        {
            "title": "◆ 「〜する」の文を「〜される」の文に直す3手順",
            "steps": [
                "もとの文の目的語（〜を）を、新しい文の主語にする。",
                "動詞を〈be動詞 ＋ 〜される形〉にする。"
                "be動詞は新しい主語の数と、もとの文の時（現在か過去か）に合わせる。",
                "もとの主語を by 〜 にして後ろに置く。"
                "だれがしたかを言う必要がなければ by 〜 は書かなくてよい。",
            ],
            "warn": "▲ 疑問文は be動詞を前に出す（Is this book read by many people?）。"
                    "否定文は be動詞のあとに not を置く。"
                    "▲ by 以外をとる言い方もある: be known to 〜（〜に知られている）、"
                    "be covered with 〜（〜におおわれている）、be interested in 〜。",
        },
        {
            "title": "◆ 動詞の -ing 形 と to ＋ 原形 の使い分け",
            "steps": [
                "-ing 形しか置けない動詞: enjoy, finish, stop, practice。"
                "例 I enjoyed playing the piano.",
                "to ＋ 原形 しか置けない動詞: want, hope, decide, need。"
                "例 I want to play the piano.",
                "どちらでもよい動詞: like, love, start, begin。"
                "例 I like playing [to play] the piano.",
                "前置詞（at, for, without, about, of）のあとは必ず -ing 形。"
                "to が前置詞のこともある: look forward to -ing。",
            ],
            "warn": "▲ 文の主語になるときは -ing 形を使うのがふつう。"
                    "例 Reading books is fun.（主語なので is を使う）",
        },
    ],
}


def _balance_mc():
    """四択の正解位置を stem の md5 順で機械的に散らす。
    ★手で番号を振ると必ず偏る。★連番（0,1,2,3,0,1,2,3…）にすると英文を読まずに
      位置だけで全問正解できてしまうので、順序は md5 でシャッフルしてから rank%4 にする。
    ★★散らすのは「大問ごと」。冊子全体でまとめて散らすと、全体の分布は均等なのに
      大問の中では1番に5/10問固まる、という紙面ができる（実際に出た）。
      生徒が解くのは大問単位なので、偏りは大問の中で消さないと意味がない。
    解説は選択肢の番号を参照していないので、並べ替えても安全（ゲート exp_choice_refs が担保）。"""
    for p in BOOK["parts"]:
        for s in p["sections"]:
            if s["kind"] != "mc":
                continue
            mcs = s["items"]
            order = sorted(range(len(mcs)),
                           key=lambda i: hashlib.md5(mcs[i]["stem"].encode()).hexdigest())
            for rank, i in enumerate(order):
                it = mcs[i]
                ch, a, target = it["choices"], it["ans"], rank % 4
                rest = ch[:a] + ch[a + 1:]
                it["choices"] = rest[:target] + [ch[a]] + rest[target:]
                it["ans"] = target


_balance_mc()

# 採点要素で採る（唯一解が無い）出題形式
ELEMENT_KINDS = ("trans", "jtrans")


def all_items():
    """(part, section, item, 通し表示名) を順に返す。"""
    for p in BOOK["parts"]:
        for s in p["sections"]:
            for i, it in enumerate(s["items"], start=1):
                where = f'第{p["no"]}部 大問{s["no"]}-{i}'
                yield p, s, it, where


def frame_text():
    """問題編のうち「設問そのもの以外」＝表紙・前書き・部扉・大問見出し・指示文。"""
    buf = [BOOK["title"], BOOK["sub"]]
    for h, b in BOOK["intro"]:
        buf += [h, b]
    for p in BOOK["parts"]:
        buf += [p["level"], p["univ"], p["aim"]] + list(p.get("steps", []))
        for s in p["sections"]:
            buf += [s["title"], s["inst"]]
    return "\n".join(buf)


def question_text(exclude=None):
    """問題編に印字される全テキスト（解答漏洩ゲートの走査対象）。"""
    buf = [frame_text()]
    for p in BOOK["parts"]:
        for s in p["sections"]:
            for it in s["items"]:
                if it is exclude:
                    continue
                for f in Q_FIELDS:
                    v = it.get(f)
                    if isinstance(v, list):
                        buf += [str(x) for x in v]
                    elif v:
                        buf.append(str(v))
    return "\n".join(buf)
