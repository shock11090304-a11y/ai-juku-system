#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同志社 英語 実戦問題の機械ゲート。

★このファイルが要る理由（2026-08-05）
  青学 (`scripts/aoyama_eigo_mirror/`) で、**正解バッジは content.json から・誤答解説は
  explanations_seki.json（オーバーレイ）から同じカードに印字する**構造のせいで、
  解説側の丸数字が +1 ずれた紙が配布されていた（「正解 ④」と印字しながら「④…は誤り」と解説）。
  同志社もまったく同じ二枚重ねの構造（build.py:273-297 が content から正解バッジを、
  :164 の `_exp_body` がオーバーレイから解説を描く）なのに、検査が1本も無かった。
  現時点で紙に実害は見つかっていないが、**無検査のまま同じ形が3冊残っている**のが問題。

    python3 check.py

★設計の要点（青学で踏んだ罠をそのまま引き継ぐ）
  - **語で設問を探さない**。「解説に出た英単語を content の options から探す」実装は、
    同じ語を持つ別の大問に当たって嘘を出す（同志社に語ベース版を当てて誤検出4件を実測）。
    build.py がキーと設問を一意に対応づけている（`I_A_W` ↔ I/A_items[slot=W] など）ので、
    **キーで設問を特定する**。対応表は下の `key_to_item()` で、build.py:273-297 と同じ形にすること。
  - **件数を定数で押さえる**。印字するだけだと検査量が黙って減っても ALL PASS になる。

★どこまで捕まえられるかを実測してある（2026-08-05）
  正解を1つずつ別の値へ振り替える総当たり（問A/B/C の 87 通り、整序・会話補充・内容一致の
  179 通り、計 266 通り）を作ってこのゲートに掛けた → **266/266 すべてで落ちる**。
  すり抜けは無い。

★守れない範囲（正直に書く）
  - `I_E` / `II_E`（内容一致）の「該当箇所」は複数箇所を `;` と `…` で束ねた**要約**で、
    本文に連続する一続きとしては存在しない。G3 の通し照合から**名指しで**外してある
    （`QUOTE_SKIP`）。外した分は必ず印字し、集合が変わったら落ちる。
  - 記述式（`I_F` 和訳 / `III_B` 英訳）の**答案の中身**は機械で採点できない。
    content 側の解答例と解説の引用が一致するかまでしか見ていない。
  - 選択肢の**内容が正しいか**（英語として正解が本当に1つか）は見ていない。
    見ているのは「content の正解と、オーバーレイの解説が指す番号がそろっているか」だけ。
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MARU = "①②③④⑤⑥⑦⑧⑨⑩"

# ★実測値。等式で押さえる（下で len() と突き合わせて、減ったら落とす）。
EXPECT_ITEM = 29     # 丸数字1つで答える設問（Ⅰ: A4+B9+C3 / Ⅱ: A3+B7+C3）
EXPECT_EXP = 36      # explanations_seki.json のキー総数
EXPECT_QUOTE = 32    # 該当箇所を本文と通し照合できる件数（上の 29 + I_D/II_D + I_F − 0）
EXPECT_BLANK = 7     # 空所補充（問A）＝該当箇所に正解が入っているはずの設問
EXPECT_POS = 60      # 「丸数字＋選択肢の英語」で位置まで照合できた件数
QUOTE_SKIP = {"I_E", "II_E"}   # 要約なので通し照合しない（理由は docstring）

FAILS, WARNS = [], []


def fail(m):
    FAILS.append(m)


def warn(m):
    WARNS.append(m)


def words(s):
    """語の列に落とす。大小文字・句読点・引用符の違いは本質でないので消す。"""
    return re.findall(r"[a-z0-9']+", s.lower().replace("’", "'"))


def key_to_item(content):
    """解説キー → 設問。**build.py:273-280 と同じ対応**にすること。

    ずれたら下の G2b（両方向の対応）が落ちるので、黙って空振りすることはない。
    """
    out = {}
    for K in ("I", "II"):
        sec = content.get(K, {})
        for it in sec.get("A_items", []):
            out[f"{K}_A_{it['slot']}"] = it
        for it in sec.get("B_items", []):
            out[f"{K}_B_{it['label']}"] = it
        for it in sec.get("C_items", []):
            out[f"{K}_C_{it['label']}"] = it
    return out


def expected_keys(content):
    """content から「あるはずの解説キー」を全部作る（選択式も記述式も）。

    ★G2b をホワイトリスト正規表現（`^(I|II)_[ABC]_`）で書くと、**その形に当たらないキーは
      『無い』のと同じ**になる。青学で大問を1つ増やしても孤児キーを足しても素通りした。
      content 側から積み上げて、両方向の差分を落とす形にする。
    """
    keys = set(key_to_item(content))
    for K in ("I", "II"):
        sec = content.get(K, {})
        if sec.get("D_bank"):
            keys.add(f"{K}_D")
        if sec.get("E_answers"):
            keys.add(f"{K}_E")
        if sec.get("F_model_ja"):
            keys.add(f"{K}_F")
    if content.get("III"):
        keys.add("III_A")
        if content["III"].get("B_model_en"):
            keys.add("III_B")
    return keys


def filled_passage(sec):
    """本文のトークンを外し、**空所には正解を入れて**平文にする。

    ★空所を空のままにすると「該当箇所」が本文に無いことになる（実測で 34 件中 9 件が空振り）。
      正解で埋めると、引用が本文に実在するかと同時に「その空所の正解は引用と整合しているか」
      まで一度に見られる（ans を1つずらすと引用の語が本文から消えて G3 が落ちる）。
    """
    t = " ".join(sec.get("paragraphs", []))
    t = re.sub(r"\[\[F=(.+?)\]\]", r"\1", t)
    t = re.sub(r"\[\[[BC]:[^\]=]+=(.+?)\]\]", r"\1", t)
    a_map = {it["slot"]: it["options"][it["ans"] - 1]
             for it in sec.get("A_items", [])
             if isinstance(it.get("ans"), int) and 1 <= it["ans"] <= len(it["options"])}
    d_map = {x["slot"]: sec["D_bank"][x["idx"] - 1]
             for x in sec.get("D_slot_map", [])
             if sec.get("D_bank") and 1 <= x["idx"] <= len(sec["D_bank"])}
    t = re.sub(r"\[\[A:([^\]]+)\]\]", lambda m: " %s " % a_map.get(m.group(1), "?"), t)
    t = re.sub(r"\[\[D:([^\]]+)\]\]", lambda m: " %s " % d_map.get(m.group(1), "?"), t)
    t = re.sub(r"\[\[K:([^\]]+)\]\]", " ? ", t)
    return t


def appears_in(quote, passage, slack=4):
    """引用が本文に（小さな省略を許して）実在するか。

    ★完全一致だと `, by contrast,` を落として引いた正当な引用（II_B_c）で落ちる。
      逆に「語がどこかにあればOK」にすると要約も通ってしまう。
      **語の並びが崩れないこと**を条件にし、飛ばせる語数を slack までに限る。
      実データは 32 件中 31 件が gap 0・最大 2。slack=4 で余裕を持たせている。
    """
    qw, pw = words(quote), words(passage)
    if not qw:
        return False
    for st in range(len(pw)):
        if pw[st] != qw[0]:
            continue
        i = j = 0
        i = st
        while i < len(pw) and j < len(qw):
            if pw[i] == qw[j]:
                j += 1
            i += 1
        if j == len(qw) and (i - st) - len(qw) <= slack:
            return True
    return False


def main():
    content = json.load(open(os.path.join(HERE, "content.json"), encoding="utf-8"))
    exp_path = os.path.join(HERE, "explanations_seki.json")
    if not os.path.exists(exp_path):
        # ★黙って飛ばさない。build.py が参照しているオーバーレイが無いなら紙が壊れる。
        sys.exit("✗ explanations_seki.json が無い（build.py:25 が参照している）")
    expl = json.load(open(exp_path, encoding="utf-8"))
    items = key_to_item(content)
    print(f"丸数字で答える設問 {len(items)} 問 / 解説 {len(expl)} 件")

    if len(items) != EXPECT_ITEM:
        fail(f"[G0] 丸数字で答える設問が {len(items)} 問（{EXPECT_ITEM} 問のはず）"
             f"— content の構造が変わって取りこぼしている")
    if len(expl) != EXPECT_EXP:
        fail(f"[G0] 解説が {len(expl)} 件（{EXPECT_EXP} 件のはず）")

    # ---- G1: ans が options の範囲内か（0始まり混在はこのリポジトリで再発4例目）
    for k, it in sorted(items.items()):
        n = len(it.get("options", []))
        a = it.get("ans")
        if not isinstance(a, int) or not (1 <= a <= n):
            fail(f"[G1] {k}: ans={a} が options {n} 個の範囲外（1始まりで書くこと）")

    # ---- G1b: 内容一致(E) / 整序(D) / 会話補充(III_A) の答えが自分の選択肢に収まっているか。
    #      D と III_A は「同じ語は2度使えない」と紙に刷ってあるので重複も落とす。
    for K in ("I", "II"):
        sec = content.get(K, {})
        n_e = len(sec.get("E_options", []))
        ea = sec.get("E_answers", [])
        for i in ea:
            if not (1 <= i <= n_e):
                fail(f"[G1b] {K}_E: 正解 {i} が選択肢 {n_e} 個の範囲外")
        if len(set(ea)) != len(ea):
            fail(f"[G1b] {K}_E: 正解が重複している {ea}")
        if sec.get("D_bank"):
            bank, smap = sec["D_bank"], sec["D_slot_map"]
            used = [x["idx"] for x in smap]
            for x in smap:
                if not (1 <= x["idx"] <= len(bank)):
                    fail(f"[G1b] {K}_D: スロット({x['slot']}) の idx={x['idx']} が語群 {len(bank)} 個の範囲外")
            if len(set(used)) != len(used):
                fail(f"[G1b] {K}_D: 同じ語を2度使っている {used}（紙に『同じ語は2度使えず』と刷ってある）")
            slots = {x["slot"] for x in smap}
            miss = [s for s in sec.get("D_answer_slots", []) if s not in slots]
            if miss:
                fail(f"[G1b] {K}_D: 解答スロット {miss} の答えが D_slot_map に無い（紙に ? と刷られる）")
            rest = sorted(set(range(1, len(bank) + 1)) - set(used))
            if sorted(sec.get("D_dummies", [])) != rest:
                fail(f"[G1b] {K}_D: 使わない語の宣言 {sec.get('D_dummies')} と実際の余り {rest} が食い違う")

    sec3 = content.get("III", {})
    if sec3:
        opts3, smap3 = sec3["A_options"], sec3["A_slot_map"]
        used3 = [x["idx"] for x in smap3]
        for x in smap3:
            if not (1 <= x["idx"] <= len(opts3)):
                fail(f"[G1b] III_A: ({x['slot']}) の idx={x['idx']} が選択肢 {len(opts3)} 個の範囲外")
        if len(set(used3)) != len(used3):
            fail(f"[G1b] III_A: 同じ選択肢を2度使っている {used3}")
        miss3 = [s for s in sec3.get("A_slots", []) if s not in {x["slot"] for x in smap3}]
        if miss3:
            fail(f"[G1b] III_A: 空所 {miss3} の答えが A_slot_map に無い（紙に ? と刷られる）")
        rest3 = sorted(set(range(1, len(opts3) + 1)) - set(used3))
        if sorted(sec3.get("A_dummies", [])) != rest3:
            fail(f"[G1b] III_A: ダミー宣言 {sec3.get('A_dummies')} と実際の余り {rest3} が食い違う")

    # ---- G1c: 本文のトークンと設問が対応しているか。
    #      ★片方だけ直す事故（設問の語を直したのに本文の下線が古いまま）は紙を見ないと分からない。
    for K in ("I", "II"):
        sec = content.get(K, {})
        t = " ".join(sec.get("paragraphs", []))
        got_a = set(re.findall(r"\[\[A:([^\]]+)\]\]", t))
        want_a = {it["slot"] for it in sec.get("A_items", [])}
        if got_a != want_a:
            fail(f"[G1c] {K}: 本文の空所 {sorted(got_a)} と問A {sorted(want_a)} が食い違う")
        for tag, key, fld in (("B", "B_items", "word"), ("C", "C_items", "phrase")):
            got = dict(re.findall(r"\[\[%s:([^\]=]+)=([^\]]+)\]\]" % tag, t))
            want = {it["label"]: it[fld] for it in sec.get(f"{key}", [])}
            if got != want:
                for lb in sorted(set(got) | set(want)):
                    if got.get(lb) != want.get(lb):
                        fail(f"[G1c] {K}_{tag}_{lb}: 本文の下線『{got.get(lb)}』と設問の『{want.get(lb)}』が食い違う")
        got_d = set(re.findall(r"\[\[D:([^\]]+)\]\]", t))
        want_d = {x["slot"] for x in sec.get("D_slot_map", [])}
        if got_d != want_d:
            fail(f"[G1c] {K}_D: 本文の整序スロット {sorted(got_d)} と D_slot_map {sorted(want_d)} が食い違う")
        got_f = re.findall(r"\[\[F=([^\]]+)\]\]", t)
        want_f = sec.get("F_target_en", "")
        if (got_f[0] if got_f else "") != want_f:
            fail(f"[G1c] {K}_F: 本文の和訳対象と F_target_en が食い違う")

    # ---- G2: 「他の選択肢」欄の丸数字が **ちょうど「全番号 − 正解」** か。
    #      正解が誤答欄に出ている（青学の実害）・誤答を書き忘れた・無い番号を書いた、を同時に捕まえる。
    #      ★対比のために正解に触れたくなったら「他の選択肢」欄ではなく「考え方」欄に書くこと。
    #        実データ 29/29 が厳密一致なので、例外を作らず等号で見る。
    checked = 0
    for k, it in sorted(items.items()):
        ex = expl.get(k)
        if not isinstance(ex, dict):
            continue
        a, n = it.get("ans"), len(it.get("options", []))
        if not isinstance(a, int) or not (1 <= a <= n):
            continue
        dis = ex.get("distractors", "")
        if not dis:
            fail(f"[G2] {k}: 誤答解説(distractors)が空＝この問は無検査になる")
            continue
        checked += 1
        want = set(MARU[:n]) - {MARU[a - 1]}
        got = {ch for ch in dis if ch in MARU}
        if MARU[a - 1] in got:
            fail(f"[G2] {k}: 正解 {MARU[a-1]} が「他の選択肢」欄に出ている"
                 f"（紙は『正解 {MARU[a-1]}』と印字するので同じカードで自己矛盾する）")
        extra = got - want - {MARU[a - 1]}
        if extra:
            fail(f"[G2] {k}: 誤答解説に選択肢に無い番号 {''.join(sorted(extra))} がある（選択肢は {n} 個）")
        if want - got:
            fail(f"[G2] {k}: 誤答 {''.join(sorted(want - got))} に触れていない（言及を消すと検査が空振りする）")
    print(f"  誤答解説と正解バッジを {checked} 問で照合")
    if checked != len(items):
        fail(f"[G2] 照合できたのは {checked}/{len(items)} 問（残りは無検査）")

    # ---- G2c: 「考え方」欄の丸数字は **すべて正解を指しているか**。
    #      +1 ずれるとカードが「正解 ④」と印字しながら本文が「①の…」と書く＝青学の実害と同型。
    for k, it in sorted(items.items()):
        ex = expl.get(k)
        if not isinstance(ex, dict):
            continue
        a = it.get("ans")
        if not isinstance(a, int) or not (1 <= a <= len(it.get("options", []))):
            continue
        for m in re.finditer(r"[①-⑩]", ex.get("reason", "")):
            if m.group(0) == MARU[a - 1]:
                continue
            # 「①が正解に見えるが本文と逆」のような否定つきの言及は正当なので落とさない
            tail = ex["reason"][m.end():m.end() + 24]
            if re.search(r"(?:に見える|と思わせ|ではない|は誤り|は不可|ひっかけ|紛らわし)", tail):
                continue
            fail(f"[G2c] {k}: 考え方の欄が {m.group(0)} を指しているが正解バッジは {MARU[a-1]}"
                 f"（誤答への言及は「他の選択肢」欄に書くこと）")

    # ---- G2d: 内容一致(E)。考え方欄が正解3つ・他の選択肢欄が残り5つ、と欄で分かれている。
    for K in ("I", "II"):
        sec = content.get(K, {})
        ex = expl.get(f"{K}_E")
        if not sec.get("E_answers") or not isinstance(ex, dict):
            continue
        n = len(sec["E_options"])
        ans = {MARU[i - 1] for i in sec["E_answers"] if 1 <= i <= n}
        got_r = {ch for ch in ex.get("reason", "") if ch in MARU}
        got_d = {ch for ch in ex.get("distractors", "") if ch in MARU}
        if got_r != ans:
            fail(f"[G2d] {K}_E: 考え方欄が {''.join(sorted(got_r))} を正解として説明しているが"
                 f"正解バッジは {''.join(sorted(ans))}")
        if got_d != set(MARU[:n]) - ans:
            fail(f"[G2d] {K}_E: 外れ肢の説明 {''.join(sorted(got_d))} が"
                 f"「全番号 − 正解」{''.join(sorted(set(MARU[:n]) - ans))} と食い違う")

    # ---- G2e: 整序(D)。解説が書く「番号=語」と「スロット=番号」が content と一致するか。
    #      ★紙は D_slot_map の**数字**を答えとして刷るので、解説側の数字がずれると
    #        「正解 (い)3」と刷りながら本文が「い=7」と書く紙になる。
    for K in ("I", "II"):
        sec = content.get(K, {})
        ex = expl.get(f"{K}_D")
        if not sec.get("D_bank") or not isinstance(ex, dict):
            continue
        bank = sec["D_bank"]
        smap = {x["slot"]: x["idx"] for x in sec["D_slot_map"]}
        txt = ex.get("reason", "") + " " + ex.get("distractors", "")
        for num, word in re.findall(r"(\d+)=([A-Za-z']+)", txt):
            i = int(num)
            if not (1 <= i <= len(bank)):
                fail(f"[G2e] {K}_D: 解説の {num}={word} は語群 {len(bank)} 個の範囲外")
            elif bank[i - 1] != word:
                fail(f"[G2e] {K}_D: 解説の {num}={word} だが語群の {num} は {bank[i-1]}")
        # ★同じスロットは「並びは…」と「提出スロットは…」で2回出る。集めてから1回だけ報告する。
        seen = {}
        for slot, num in re.findall(r"([%s])\s*[=＝]?\s*(\d+)" % "".join(smap), txt):
            seen.setdefault(slot, set()).add(int(num))
        for slot, nums in sorted(seen.items()):
            if nums != {smap[slot]}:
                fail(f"[G2e] {K}_D: 解説が ({slot})={'/'.join(map(str, sorted(nums)))} と"
                     f"書いているが正解は {smap[slot]}")
        if set(seen) != set(smap):
            fail(f"[G2e] {K}_D: 解説がスロット {sorted(set(smap) - seen)} に触れていない（その分は無検査）")

    # ---- G2f: 会話補充(III_A)。スロット→番号が A_slot_map と合っているか（該当箇所・考え方の両方）。
    #      ★`(?<![A-Za-z])` が要る。付けないと本文中の "as if=" の f が空所ラベルに見えて分割が壊れる。
    if sec3 and isinstance(expl.get("III_A"), dict):
        ex = expl["III_A"]
        smap3 = {x["slot"]: x["idx"] for x in sec3["A_slot_map"]}
        labels = "".join(sorted(smap3))
        for fld in ("quote", "reason"):
            segs = re.split(r"(?<![A-Za-z])([%s])=" % labels, ex.get(fld, ""))
            seen = {}
            for i in range(1, len(segs), 2):
                nums = [MARU.index(ch) + 1 for ch in segs[i + 1] if ch in MARU]
                if nums:
                    seen[segs[i]] = nums[0]
            for slot, idx in sorted(seen.items()):
                if smap3[slot] != idx:
                    fail(f"[G2f] III_A の{fld}: ({slot}) を {MARU[idx-1]} としているが正解は {MARU[smap3[slot]-1]}")
            if fld == "quote" and set(seen) != set(smap3):
                fail(f"[G2f] III_A の該当箇所が空所 {sorted(set(smap3) - set(seen))} に触れていない")
            # 引用した英文が、その番号の選択肢のものか（4語つながれば同一とみなす）
            if fld == "quote":
                for i in range(1, len(segs), 2):
                    slot = segs[i]
                    idx = seen.get(slot)
                    if not idx:
                        continue
                    qw, ow = words(segs[i + 1]), words(sec3["A_options"][idx - 1])
                    if not any(qw[x:x + 4] == ow[y:y + 4]
                               for x in range(max(0, len(qw) - 3))
                               for y in range(max(0, len(ow) - 3))):
                        # ★完全一致を求めない。実データに1件、選択肢を少し言い換えて引いている
                        #   箇所がある（h=⑩「spot ... in a matter of seconds」）。番号が合っていれば
                        #   紙は破綻しないので、**番号と英文の紐づけが入れ替わった**ときだけ鳴らす。
                        #   その用途には 4 語つながるかで足りる（実データ 8/8 で成立）。
                        warn(f"III_A ({slot}): 引用した英文が選択肢 {MARU[idx-1]} の本文とつながらない"
                             f"（番号と英文の組が入れ替わっていないか）")
        got_d = {MARU.index(ch) + 1 for ch in ex.get("distractors", "") if ch in MARU}
        if got_d != set(sec3.get("A_dummies", [])):
            fail(f"[G2f] III_A: ダミーの説明 {sorted(got_d)} と A_dummies {sec3.get('A_dummies')} が食い違う")

    # ---- G2b: 解説キーと設問の対応が **両方向で** そろっているか。
    want_keys = expected_keys(content)
    for k in sorted(want_keys - set(expl)):
        fail(f"[G2b] {k}: 設問はあるのに解説が無い（紙に『（解説準備中）』と刷られる）")
    for k in sorted(set(expl) - want_keys):
        fail(f"[G2b] {k}: 解説はあるのに設問が見つからない（対応づけが壊れている＝紙に出ない）")

    # ---- G3: 「該当箇所」が本文に実在するか（空所は正解で埋めてから照合）。
    quoted = blanks = 0
    for K in ("I", "II"):
        sec = content.get(K, {})
        if not sec:
            continue
        passage = filled_passage(sec)
        a_ans = {f"{K}_A_{it['slot']}": it["options"][it["ans"] - 1]
                 for it in sec.get("A_items", [])
                 if isinstance(it.get("ans"), int) and 1 <= it["ans"] <= len(it["options"])}
        for k in sorted(expl):
            if not k.startswith(K + "_") or k in QUOTE_SKIP:
                continue
            q = expl[k].get("quote", "") if isinstance(expl[k], dict) else ""
            if not q:
                fail(f"[G3] {k}: 該当箇所が空")
                continue
            quoted += 1
            if not appears_in(q, passage):
                fail(f"[G3] {k}: 該当箇所が本文に無い（要約を引用符で囲んでいる／正解と本文が食い違う）"
                     f" 『{q[:60]}…』")
            # ★通し照合だけでは足りない。関学で ans を総当たりで振り替えて実測したところ、
            #   正解が別の選択肢の一部（Seen ⊂ Having seen）だと引用が部分列として成立して
            #   素通りした。空所補充なら「該当箇所に正解の語がそのまま入っている」はずなので足す。
            if k in a_ans:
                blanks += 1
                qw, aw = words(q), words(a_ans[k])
                if not any(qw[i:i + len(aw)] == aw for i in range(len(qw) - len(aw) + 1)):
                    fail(f"[G3b] {k}: 該当箇所に正解『{a_ans[k]}』が入っていない"
                         f"（空所の正解と、解説が引用した一文が食い違う）")
    print(f"  該当箇所を本文と {quoted} 件照合（うち空所の正解入りを {blanks} 件確認・"
          f"要約のため外した {len(QUOTE_SKIP)} 件: {'・'.join(sorted(QUOTE_SKIP))}）")
    if quoted != EXPECT_QUOTE:
        fail(f"[G3] 本文照合できたのが {quoted} 件（{EXPECT_QUOTE} 件のはず）— 対象が減っている")
    if blanks != EXPECT_BLANK:
        fail(f"[G3b] 空所の正解を照合できたのが {blanks} 件（{EXPECT_BLANK} 件のはず）")
    if not QUOTE_SKIP <= set(expl):
        fail(f"[G3] 照合から外したキー {sorted(QUOTE_SKIP - set(expl))} が実在しない（名前が変わった？）")

    # ---- G3b: 記述式の解答例が content と解説で一致しているか（紙は content 側を刷る）。
    if content.get("I", {}).get("F_target_en"):
        q = expl.get("I_F", {}).get("quote", "").strip()
        if q != content["I"]["F_target_en"].strip():
            fail("[G3b] I_F: 解説の該当箇所が本文の和訳対象と違う（別の文を訳している）")
    if sec3.get("B_model_en"):
        q = expl.get("III_B", {}).get("quote", "").strip()
        if q != sec3["B_model_en"].strip():
            fail("[G3b] III_B: 解説の該当箇所が紙に刷る解答例と違う（生徒は2種類の模範解答を見る）")

    # ---- G4: 番号つきで名指しされた選択肢の位置が content の並びと合っているか。
    pos = 0
    for k, it in sorted(items.items()):
        ex = expl.get(k)
        if not isinstance(ex, dict):
            continue
        opts = [str(o).strip() for o in it.get("options", [])]
        for fld in ("reason", "distractors"):
            for m in re.finditer(r"([①-⑩])\s*([A-Za-z][A-Za-z '\-]*[A-Za-z])", ex.get(fld, "")):
                word = m.group(2).strip()
                if word not in opts:
                    continue          # 選択肢そのものを指していない言及
                pos += 1
                if opts.index(word) != MARU.index(m.group(1)):
                    fail(f"[G4] {k}: 解説の「{m.group(1)}{word}」は content では {MARU[opts.index(word)]}")
    print(f"  番号つきで名指しされた選択肢の位置を {pos} 件照合")
    if pos < EXPECT_POS:
        fail(f"[G4] 位置を照合できたのが {pos} 件（{EXPECT_POS} 件のはず）— 解説の書き方が変わって空振りしている")

    for w in WARNS:
        print("WARN", w)
    for f in FAILS:
        print(" ×", f)
    print(f"\n=== {'ALL PASS' if not FAILS else f'FAIL {len(FAILS)}件'}"
          f"（{len(WARNS)} warnings）===")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
