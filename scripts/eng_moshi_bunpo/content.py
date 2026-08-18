# -*- coding: utf-8 -*-
"""高3 記述模試対策 英文法・語法 実戦問題集 — 単一ソース。

組版・機械ゲート・盲検証は姉妹編と共有する（データだけがここにある）:
  WORKBOOK_DIR=scripts/eng_moshi_bunpo python3 scripts/eng_kokkoritsu_nankan/build.py
  WORKBOOK_DIR=scripts/eng_moshi_bunpo python3 scripts/eng_kokkoritsu_nankan/check.py
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content_p1 import PART as P1  # noqa: E402
from content_p2 import PART as P2  # noqa: E402
from content_p3 import PART as P3  # noqa: E402

# 問題編に印字してよいフィールド（★ここに exp / point / fix / ans を足さないこと。
# 足した瞬間に「答えが問題編に載る」＝知識ゼロで得点できる冊子になる）
Q_FIELDS = ("stem", "choices", "parts", "frame", "tokens", "ja", "src", "inst",
            "given", "hint", "context")

BOOK = {
    "title": "高3 記述模試対策 英文法・語法 実戦問題集",
    "sub": "四択／語句整序／誤り指摘 ― 文法演習3回分",
    "series": "高3 夏〜秋 直前演習",
    # ★大きな区切りの単位語。この本は模試形式なので「部」でなく「回」で数える
    #   （持たせないと紙面が「第1部 第1回 標準レベル」と二重表記になる）。
    "unit": "回",
    "file": "koushou3_kijutsu_moshi_bunpo",
    "intro": [
        ("この問題集のねらい",
         "高3の夏から秋にかけて受ける記述模試では、文法・語法が独立した大問として出ます。"
         "そこで問われるのは細かい知識の暗記ではなく、"
         "「一文の骨格をつかんで、正しい型を素早く当てはめる力」です。"
         "本書は、記述模試で実際に使われる三つの問われ方"
         "――空所補充・誤文訂正・語句整序――だけを取り出して、"
         "1回20問（四択10問・語句整序5問・誤り指摘5問）×3回分にまとめました。"),
        ("実際の模試での出方",
         "空所補充と誤文訂正は、文法・語法の大問でそのまま出ます。"
         "近年の河合塾 全統記述模試（高3）では大問3がこの二つに分かれており、"
         "駿台全国模試の文法の大問は1問4点前後で、"
         "空所補充か誤文訂正のどちらかが出ることが多い形です。"
         "語句整序は、模試では英作文の大問の一部として出るのが一般的です。"
         "※大問の並びや配点は年度・回によって変わります。"
         "本書は模試1回分を再現したものではなく、"
         "どの回でも問われるこの三つの形式だけを集めた演習書です。"),
        ("3回の並び方",
         "第1回・第2回は日東駒専・地方国公立の帯で、同じ項目を別の角度から2度通します。"
         "第3回だけは一文が長く、構造をつかまないと空所の役割が見えない問題を集めてあり、"
         "GMARCH・地方国公立の文法問題と同程度です。"
         "※第1回から第3回へ一直線に難しくなる作りではありません。"
         "第1回と第2回は同じ帯を2周する回、第3回が一段上がる回だと考えてください。"
         "各回100点満点・制限時間25分で、模試で文法にかけられる時間に合わせてあります。"),
        ("解き方の約束",
         "①辞書を引かずに、時間を計って最後まで解く。"
         "②答え合わせのあと、間違えた問題の「▶ポイント」だけをノートに書き写す。"
         "③一週間後にもう一度、同じ回を解き直す。"
         "四択で当たった問題も、なぜ他の三つが誤りなのかを言えるまでは「解けた」と数えません。"
         "模試で差がつくのは、この「なぜ他が誤りか」を即答できるかどうかです。"),
        ("採点のしかた",
         "四択は解答と一致していれば正解です。"
         "語句整序は語順が完全に一致していれば正解とします。"
         "誤り指摘は、誤りを含む記号と訂正後の形の両方が合っていて正解です"
         "（記号だけ合っていて訂正が誤っている場合は加点しません。模試の採点もこの方式です）。"
         "訂正の形は、解答編に「〜も可」と併記した別解でも正解としてください。"
         "各問の配点は大問見出しに示しました。"),
    ],
    # ★前書きが長いと、構成表だけが1ページに独立して大半が白紙になる。
    #   表のあとに置く節をここに書くと、そのページが埋まる（build.py が対応済み）。
    "after_table": [
        ("この問題集で扱う範囲",
         "本書は英文法・語法に特化しています。前書きに挙げた模試名は、"
         "出題形式と配点の根拠として示したもので、その模試の問題を再現したものではありません。"
         "難易度の目安は、各回の扉に大学名の帯で示してあります。"
         "実際の記述模試では、これに加えて長文読解・和文英訳・自由英作文が課されます。"
         "本書はその土台となる「文を正確に組み立てる力」を鍛えるためのものです。"),
        ("解き終わったら",
         "採点したら、間違えた問題の「▶ポイント」を回ごとに数えてみてください。"
         "同じ項目で2回以上落としているなら、それがあなたの本当の弱点です。"
         "模試までに、その項目だけを文法書で読み直してから、本書を解き直してください。"),
    ],
    "parts": [P1, P2, P3],
}


def _balance_mc():
    """四択の正解位置を stem の md5 順で機械的に散らす。
    ★手で番号を振ると必ず偏る（姉妹編の初版は34問中19問が2番に集中した）。
    ★大問ごとに 0〜3 を配り切る（全体だけ均しても大問内が偏る）。
    解説は選択肢の番号を参照していないので、並べ替えても安全。"""
    for p in BOOK["parts"]:
        for s in p["sections"]:
            if s["kind"] != "mc":
                continue
            items = s["items"]
            order = sorted(range(len(items)),
                           key=lambda i: hashlib.md5(items[i]["stem"].encode()).hexdigest())
            # ★起点を大問ごと・回ごとにずらす。全大問を 0 起点にすると 10問の大問では
            #   必ず 1番3/2番3/3番2/4番2 になり、冊子全体でも同じ偏りが積み上がる
            #   （実測 9/9/6/6）。オフセットを入れると回をまたいで均される。
            off = p["no"] + s["no"]
            for rank, i in enumerate(order):
                it = items[i]
                ch, a, target = it["choices"], it["ans"], (rank + off) % 4
                rest = ch[:a] + ch[a + 1:]
                it["choices"] = rest[:target] + [ch[a]] + rest[target:]
                it["ans"] = target


def _place(it, target):
    """正解を target 番目に置き直す（誤答の相対順は保つ）。"""
    ch, a = it["choices"], it["ans"]
    rest = ch[:a] + ch[a + 1:]
    it["choices"] = rest[:target] + [ch[a]] + rest[target:]
    it["ans"] = target


def _spread(pred, label):
    """pred を満たす問だけを集めて、その中で正解位置を 0〜3 に配り直す。

    ★大問ごとに 0〜3 を配っても、**ある特徴を持つ問だけが同じ位置に固まる**ことがある。
    位置の分布ゲートは冊子全体を見るので、この偏りは素通りする。
    実測で2種類出た:
      ・正解肢が4択中いちばん長い問
      ・助動詞＋have＋過去分詞のような「見慣れない完了形」が正解の問（4問中3問が④）
    どちらも「英文を読まずに形だけで当てられる」ので、機械で散らす。
    """
    hits = [it for p in BOOK["parts"] for s in p["sections"] if s["kind"] == "mc"
            for it in s["items"] if pred(it)]
    hits.sort(key=lambda it: hashlib.md5((label + it["stem"]).encode()).hexdigest())
    for rank, it in enumerate(hits):
        _place(it, rank % 4)


def _is_longest(it):
    L = [len(c) for c in it["choices"]]
    return L[it["ans"]] == max(L) and L.count(max(L)) == 1


def _is_perfect(it):
    """正解が完了形・受動完了などの「見慣れない形」か。"""
    w = it["choices"][it["ans"]].lower().split()
    return "have" in w or "been" in w or "had" in w


# ★誤り指摘は四択と違い、正解位置を機械で散らせない。parts[0..3] は stem の {a}〜{d} に
#   差し込む位置そのものなので、並べ替えると英文が別の語順に組み替わって崩壊する
#   （実際に "this model to to be superior is said" という文が出た）。
#   誤りの位置は作問時に手で散らし、check.py の分布ゲートで担保する。

# ★呼ぶ順序が意味を持つ。まず大問ごとに 0〜3 を配り切り、そのあとで
#   「tell になる特徴を持つ問」だけを配り直す。逆順にすると _balance_mc が上書きして、
#   散らしたはずの偏りが戻る（実際にやって、完了形4問のうち3問が④のまま残った）。
# ★連続の解消は姉妹編と同じ実装を使う（2つ書くと必ず食い違う）。
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _workbook_gates import break_answer_runs  # noqa: E402


_balance_mc()
_spread(_is_perfect, "perfect")
_spread(_is_longest, "longest")
break_answer_runs(BOOK["parts"])

KIND_LABEL = {
    "mc": "四択",
    "error": "誤り指摘",
    "order": "語句整序",
    "fill": "空所補充",
    "rewrite": "書き換え",
    "jtrans": "英文和訳",
    "trans": "和文英訳",
}
# 採点要素で採る（唯一解が無い）出題形式 ― 本書は採用していない
ELEMENT_KINDS = ()


def all_items():
    """(part, section, item, 通し表示名) を順に返す。"""
    for p in BOOK["parts"]:
        for s in p["sections"]:
            for i, it in enumerate(s["items"], start=1):
                where = f'第{p["no"]}回 大問{s["no"]}-{i}'
                yield p, s, it, where


def frame_text():
    """問題編のうち「設問そのもの以外」＝表紙・前書き・回扉・大問見出し・指示文。
    ここに文法項目名が出ると、その大問が何の文法かが割れる。"""
    buf = [BOOK["title"], BOOK["sub"]]
    for h, b in list(BOOK["intro"]) + list(BOOK.get("after_table", [])):
        buf += [h, b]
    for p in BOOK["parts"]:
        buf += [p["level"], p["univ"], p["aim"]]
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
