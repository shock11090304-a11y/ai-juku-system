#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""青学 英語 実戦問題の機械ゲート。

★このファイルが要る理由（2026-08-05 に紙の実害が見つかった）
  正解バッジは content.json から、誤答解説は **explanations_seki.json（オーバーレイ）** から
  同じカードに印字される（build.py:144/152 が正解バッジ、:87 の `_exp_body` が解説）。
  ところが解説側の丸数字が +1 ずれていて、紙が「正解 ④」と出しながら
  「④take off は『離陸する・脱ぐ』」と誤答解説していた。
  **同じカードの中で ④ が正解でもあり誤答でもある**状態で、生徒はまず混乱する。

  この型（選択肢番号のずれ）はこのリポジトリで **4例目**。過去の対策は
  `options[ans-1]` を content の中だけで照合していたので、
  **オーバーレイ側の番号は一度も見ていなかった**。ここで両方を突き合わせる。

    python3 check.py

★照合は「キーで設問を特定する」構造照合にしてある（語で探さない）
  最初は「解説に出る丸数字＋英単語」を content の options から探す実装にした。これは
  **解説中の丸数字 57個のうち 11個しか照合できず**、和訳で選択肢を指す問題Ⅰ(41個)と
  丸数字の直後がかぎ括弧の形を丸ごと素通りさせた。実測で、同じ +1 ズレを問題Ⅰや
  IV_11 に入れても ALL PASS になった＝**見つけた事故と同じ型を見逃すゲート**だった。
  build.py がキーと設問を一意に対応づけている（`I_{i}` ↔ questions[i-1] / `IV_{n}` ↔ items の n）
  ので、そちらを使えば語の曖昧さも書式の違いも関係なくなる。
"""
import json
import os
import re
import sys

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _mirror_negation import negates  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# ★実測値を定数で持ち、等式で押さえる。「印字するだけ」だと検査量が黙って減っても
#   ALL PASS になる（実測: distractors キーを一部改名すると 15問→5問に減って緑のまま。
#   run_all_gates は最終行しか出さないので「設問 2 問」は人の目にも入らない）。
EXPECT_Q = 15          # 選択式の設問数（問題Ⅰ 10 + 問題Ⅳ 5）
EXPECT_POS = 15        # G3 が位置照合できる件数（問題Ⅳ の英単語形）
MARU = "①②③④⑤⑥⑦⑧⑨"
FAILS, WARNS = [], []



def fail(m):
    FAILS.append(m)


def warn(m):
    WARNS.append(m)


def key_to_question(content):
    """解説キー → 設問。**build.py:144/148/152 と同じ対応**にすること。

    ずれると照合が空振りするので、下の「1問も対応づかない＝失敗」で気づけるようにしてある。
    """
    out = {}
    for i, q in enumerate(content.get("I", {}).get("questions", []), 1):
        out[f"I_{i}"] = q
    for it in content.get("IV", {}).get("items", []):
        out[f"IV_{it['n']}"] = it
    # II は記述式（options が無い）ので選択肢の照合対象外
    return out


def main():
    content = json.load(open(os.path.join(HERE, "content.json"), encoding="utf-8"))
    exp_path = os.path.join(HERE, "explanations_seki.json")
    if not os.path.exists(exp_path):
        # ★黙って飛ばさない。オーバーレイが無いのに build が参照していれば紙が壊れる。
        sys.exit("✗ explanations_seki.json が無い（build.py が参照している）")
    expl = json.load(open(exp_path, encoding="utf-8"))
    kq = key_to_question(content)

    print(f"選択式の設問 {len(kq)} 問 / 解説 {len(expl)} 件")

    # --- G1: ans が options の範囲内か（0始まり混在の定番事故）
    for k, q in kq.items():
        n = len(q.get("options", []))
        a = q.get("ans")
        if not isinstance(a, int) or not (1 <= a <= n):
            fail(f"[G1] {k}: ans={a} が options {n} 個の範囲外（1始まりで書くこと）")

    # --- G2: 「他の選択肢」欄の丸数字が **ちょうど「全番号 − 正解」** になっているか。
    #   「正解が誤答欄に出ている」（今回の実害）に加えて「誤答を1つ書き忘れた」
    #   「存在しない番号を書いた」も同時に捕まる。実データ 15/15 で成立する。
    #   語ではなく番号で見るので、選択肢が英単語でも和訳でも、括弧が続いても効く。
    checked = 0
    for k, ex in expl.items():
        q = kq.get(k)
        if q is None:
            continue                       # II_* の記述問題など
        a = q.get("ans")
        if not isinstance(a, int) or not (1 <= a <= len(q.get("options", []))):
            continue
        dis = ex.get("distractors", "") if isinstance(ex, dict) else str(ex)
        if not dis:
            warn(f"{k}: 誤答解説(distractors)が空")
            continue
        checked += 1
        want = {MARU[i] for i in range(len(q["options"]))} - {MARU[a - 1]}
        got = {ch for ch in dis if ch in MARU}
        if MARU[a - 1] in got:
            # 「なお②は④（正解）と紛らわしい」のような対比言及は正当なので落とさない
            # ★肯定語の白リストで例外にすると、列挙に無い自然な対比表現を全部落とす（実測10/10）。
            #   「その番号を否定している一文があるか」で見る（共通ヘルパ）。
            if negates(dis, MARU[a - 1]):
                fail(f"[G2] {k}: 正解 {MARU[a-1]} が「他の選択肢」欄に出ている"
                     f"（紙は『正解 {MARU[a-1]}』と印字するので同じカードで自己矛盾する）")
        if got - want - {MARU[a - 1]}:
            fail(f"[G2] {k}: 誤答解説に選択肢に無い番号 "
                 f"{''.join(sorted(got - want - {MARU[a-1]}))} がある"
                 f"（選択肢は {len(q['options'])} 個）")
        if want - got:
            # ★warn では「書き方を変えるだけでゲートが無力化し、しかも緑のまま」になる。
            #   実データは 15/15 で全誤答に言及しているので FAIL にしてよい。
            fail(f"[G2] {k}: 誤答 {''.join(sorted(want - got))} に触れていない"
                 f"（言及を消すと検査が空振りする）")

    if checked == 0:
        # ★1問も照合できていないのは「合格」ではない。キー対応が壊れた可能性がある。
        fail("[G2] 解説と設問が1問も対応づかない（key_to_question が build.py とずれている？）")
    print(f"  誤答解説と正解バッジを {checked} 問で照合")
    if len(kq) != EXPECT_Q:
        fail(f"[G2] 選択式の設問が {len(kq)} 問しかない（{EXPECT_Q} 問のはず）"
             f"— content の構造が変わって取りこぼしている")
    if checked != len(kq):
        fail(f"[G2] 照合できたのは {checked}/{len(kq)} 問"
             f"（distractors が無い設問がある＝その分は無検査）")

    # --- G2b: 解説キーと設問の対応が**両方向で**そろっているか。
    #   ★`checked == 0` は全損しか捕まえない。content の一部だけ構造が変わって
    #     設問が黙って消えても、残りで照合が成立するので ALL PASS になる（実測で10問消えた）。
    #     片側にしか無いキーを落とすことで、部分的な取りこぼしに気づけるようにする。
    #   ★片側を `^(I|IV)_\d+$` のホワイトリストで絞ると、**その正規表現に当たらないキーは
    #     「無い」のと同じ**になる。大問Ⅴを増設しても孤児キーを足しても素通りした（実測）。
    #     記述式(II_)だけを名前で除外するブラックリストにする。
    sel_keys = set(kq)
    exp_sel = {k for k in expl if not k.startswith("II_")}
    for k in sorted(sel_keys - exp_sel):
        fail(f"[G2b] {k}: 設問はあるのに解説が無い")
    for k in sorted(exp_sel - sel_keys):
        fail(f"[G2b] {k}: 解説はあるのに設問が見つからない"
             f"（content の構造が変わった？対応づけが壊れている）")

    # --- G2c: reason（考え方）欄の丸数字は **すべて正解を指しているか**。
    #   ★「◯が正解」の形だけ見ていたのでは足りない。実データの reason にある丸数字11個のうち
    #     8個は「④の a milestone … がその言い換え」のように**正解を番号で名指しする**形で、
    #     ここが +1 ずれると紙は「正解 ④」と印字しながら本文が「①の…」と書く＝実害と同型。
    #     誤答への言及は distractors 欄に書く、という規約とセット（実データ 11/11 で成立）。
    for k, ex in expl.items():
        q = kq.get(k)
        if q is None or not isinstance(ex, dict):
            continue
        a = q.get("ans")
        if not isinstance(a, int) or not (1 <= a <= len(q.get("options", []))):
            continue
        reason = ex.get("reason", "")
        for m in re.finditer(r"[①-⑨]", reason):
            if m.group(0) == MARU[a - 1]:
                continue
            # 「①が正解に見えるが本文と逆」のような否定つきの言及は正当なので落とさない
            tail = reason[m.end():m.end() + 24]
            if re.search(r"(?:に見える|と思わせ|ではない|は誤り|は不可|ひっかけ|紛らわし)", tail):
                continue
            fail(f"[G2c] {k}: 考え方の欄が {m.group(0)} を指しているが正解バッジは {MARU[a-1]}"
                 f"（誤答への言及は「他の選択肢」欄に書くこと）")

    # --- G3: 番号つきで名指しされた選択肢の位置が content の並びと合っているか（書ける範囲の保険）。
    pos = 0
    for k, ex in expl.items():
        q = kq.get(k)
        if q is None:
            continue
        opts = [str(x).strip() for x in q.get("options", [])]
        dis = ex.get("distractors", "") if isinstance(ex, dict) else str(ex)
        for m in re.finditer(r"([①-⑨])\s*([A-Za-z][A-Za-z \-']*[A-Za-z])", dis):
            idx, word = MARU.index(m.group(1)), m.group(2).strip()
            if word not in opts:
                continue                   # 選択肢そのものを指していない言及
            pos += 1
            if opts.index(word) != idx:
                fail(f"[G3] {k}: 解説の「{m.group(1)}{word}」は content では "
                     f"{MARU[opts.index(word)]}")
    print(f"  番号つきで名指しされた選択肢の位置を {pos} 件照合")
    if pos < EXPECT_POS:
        fail(f"[G3] 位置を照合できたのが {pos} 件しかない（{EXPECT_POS} 件のはず）"
             f"— 解説の書き方が変わって照合が空振りしている")

    for w in WARNS:
        print("WARN", w)
    for f in FAILS:
        print(" ×", f)
    print(f"\n=== {'ALL PASS' if not FAILS else f'FAIL {len(FAILS)}件'}"
          f"（{len(WARNS)} warnings）===")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
