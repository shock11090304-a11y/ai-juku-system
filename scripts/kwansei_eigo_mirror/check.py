#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""関学 英語 実戦問題の機械ゲート。

★このファイルが要る理由（2026-08-05）
  青学 (`scripts/aoyama_eigo_mirror/`) で、**正解バッジは content.json から・誤答解説は
  explanations_seki.json（オーバーレイ）から同じカードに印字する**構造のせいで、
  解説側の番号が +1 ずれた紙が配布されていた。関学も同じ二枚重ね
  （build.py:145-165 が content から正解バッジを、:97 の `_exp_body` がオーバーレイから解説を描く）
  なのに検査が1本も無かった。

    python3 check.py

★青学の照合はそのままでは当たらない
  関学の選択肢記号は **a〜h の英字**で、解説は丸数字を使わない。しかも参照の書き方が3通りある。
    (1) 短い選択肢（前置詞・動詞1語など）→ 誤答を**英単語そのもの**で名指しする
        例: 「either は either A or B で…」
    (2) 長い選択肢（1文まるごと）      → **記号 a〜d** で名指しする
        例: 「a「研究者がデータを改ざん」は本文が明確に否定」
    (3) 長い選択肢なのに、記号も英文も出さず**日本語の意味だけ**で書いてあるもの（3件）
  そこで「選択肢の長さ」というデータ側の事実でモードを決め打ちする（人が指定しない）。
  (3) は機械で設問と紐づけられないので **名前を挙げて無検査だと明示**する（下の `NO_REF`）。

★どこまで捕まえられるかを実測してある（2026-08-05）
  52 問すべてについて ans を他の選択肢へ振り替える 153 通りを総当たりで作り、
  このゲートが落ちるかを数えた → **144/153 を検出**。すり抜けた 9 通りは
  下の `NO_REF` の3問（各3通り）**だけ**で、それ以外に穴は無い。

★守れない範囲（正直に書く）
  - `NO_REF` の3件（II_B_ア/イ/ウ）は「他の選択肢」欄が日本語の意訳だけで、
    どの記号を指しているか機械では決まらない。**正解と解説の食い違いを検出できない**。
    直すなら解説に記号 (a/b/c/d) を書き足すこと。書き足せば自動で検査対象に入る。
  - 問C（内容一致・主旨）の「該当箇所」は複数箇所を `...` で束ねた要約で、本文に一続きとしては
    存在しない。G3 の通し照合から名指しで外してある（`QUOTE_SKIP`）。
  - 選択肢の**内容が正しいか**（英語として正解が本当に1つか）は見ていない。
"""
import json
import os
import re
import sys

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _mirror_negation import negates  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OPT = "abcdefgh"

# ★実測値。等式で押さえる（印字するだけだと検査量が黙って減っても ALL PASS になる）。
EXPECT_ITEM = 52       # 記号1つ（または複数）で答える設問の総数
EXPECT_EXP = 57        # explanations_seki.json のキー総数（設問 52 + Ⅴ5 … 下で内訳を検算する）
EXPECT_LETTER = 9      # 記号 a〜h で誤答を名指ししている設問
EXPECT_WORD = 40       # 誤答を英単語そのもので名指ししている設問
EXPECT_QUOTE = 51      # 該当箇所を本文/例文/会話と通し照合できる件数
EXPECT_BLANK = 30      # 空所補充（Ⅰ/Ⅱ問A・Ⅳ・Ⅵ）＝該当箇所に正解が入っているはずの設問
# 正解を誤答欄で否定している形（「〜は不可」「〜は誤り」）。語のすぐ後ろだけ見る。
_NEGATED = re.compile(r"(?:不可|誤り|×|ならない|なれない|成り立たない|使えない"
                      r"|合わない|ズレ|できない|不適|は違う)")
LONG_OPT_WORDS = 5     # これを超える語数の選択肢は「記号で参照する」流儀（実測: 短い側は最大5語、
                       # 長い側は最小12語で、間にはっきり空きがある）
NO_REF = {"II_B_ア", "II_B_イ", "II_B_ウ"}                       # docstring 参照
QUOTE_SKIP = {"I_C_i", "I_C_ii", "I_C_iii", "II_C", "III_C_i", "III_C_ii"}

# 記号での名指し。`(?<![A-Za-z])` が要る（付けないと "as if=" の f、"world「" の d を拾う）。
LABEL = re.compile(r"(?<![A-Za-z])([a-h])(?:\s*[「『=＝：:]|\s+は(?![A-Za-z]))")

FAILS, WARNS = [], []



def fail(m):
    FAILS.append(m)


def warn(m):
    WARNS.append(m)


def words(s):
    return re.findall(r"[a-z0-9']+", s.lower().replace("’", "'"))


def appears_in(quote, text, slack=4):
    """引用が本文に（小さな省略を許して）実在するか。

    ★完全一致だと「, by contrast,」を落として引いた正当な引用で落ちる。逆に語の集合だけ見ると
      要約も通る。**語の並びが崩れないこと**を条件に、飛ばせる語数を slack までに限る。
    """
    qw, pw = words(quote), words(text)
    if not qw:
        return False
    for st in range(len(pw)):
        if pw[st] != qw[0]:
            continue
        i, j = st, 0
        while i < len(pw) and j < len(qw):
            if pw[i] == qw[j]:
                j += 1
            i += 1
        if j == len(qw) and (i - st) - len(qw) <= slack:
            return True
    return False


def mentions(text, option):
    """選択肢の英文が text の中に語として出てくるか（大小文字・記号は無視）。"""
    o = " ".join(words(option))
    t = " ".join(words(text))
    return bool(o) and re.search(r"(?<![a-z0-9])" + re.escape(o) + r"(?![a-z0-9])", t) is not None


def collect_items(c):
    """解説キー → (選択肢, 正解のリスト)。**build.py:144-165 と同じ対応**にすること。"""
    out = {}
    for K in ("I", "II", "III"):
        s = c.get(K)
        if not s:
            continue
        for it in s["A_items"]:
            out[f"{K}_A_{it['ref']}"] = (it["options"], [it.get("ans")])
        for it in s["B_items"]:
            out[f"{K}_B_{it['ref']}"] = (it["options"], [it.get("ans")])
        if s.get("C_form") == "multi":
            out[f"{K}_C"] = (s["C_multi_options"], list(s.get("C_multi_answers", [])))
        else:
            for it in s.get("C_items", []):
                out[f"{K}_C_{it['q_label'].strip('()')}"] = (it["options"], [it.get("ans")])
    for i, it in enumerate(c.get("IV", {}).get("items", []), 1):
        out[f"IV_{i}"] = (it["options"], [it.get("ans")])
    for it in c.get("VI", {}).get("items", []):
        out[f"VI_{it['ref']}"] = (it["options"], [it.get("ans")])
    return out


def main():
    content = json.load(open(os.path.join(HERE, "content.json"), encoding="utf-8"))
    exp_path = os.path.join(HERE, "explanations_seki.json")
    if not os.path.exists(exp_path):
        # ★黙って飛ばさない。build.py:21 が参照しているオーバーレイが無いなら紙が壊れる。
        sys.exit("✗ explanations_seki.json が無い（build.py:21 が参照している）")
    expl = json.load(open(exp_path, encoding="utf-8"))
    items = collect_items(content)
    n_v = len(content.get("V", {}).get("items", []))
    print(f"記号で答える設問 {len(items)} 問 ＋ 語句整序 {n_v} 問 / 解説 {len(expl)} 件")

    if len(items) != EXPECT_ITEM:
        fail(f"[G0] 記号で答える設問が {len(items)} 問（{EXPECT_ITEM} 問のはず）— 構造が変わって取りこぼしている")
    if len(expl) != EXPECT_EXP:
        fail(f"[G0] 解説が {len(expl)} 件（{EXPECT_EXP} 件のはず）")
    if len(items) + n_v != len(expl):
        fail(f"[G0] 設問 {len(items)}＋整序 {n_v} と解説 {len(expl)} 件の数が合わない")

    # ---- G1: ans が選択肢の範囲内か（0始まり混在はこのリポジトリで再発4例目）
    for k, (opts, ans) in sorted(items.items()):
        if not ans or any(a is None for a in ans):
            fail(f"[G1] {k}: 正解が入っていない")
            continue
        for a in ans:
            if not isinstance(a, int) or not (1 <= a <= len(opts)):
                fail(f"[G1] {k}: 正解 {a} が選択肢 {len(opts)} 個の範囲外（1始まりで書くこと）")
        if len(set(ans)) != len(ans):
            fail(f"[G1] {k}: 正解が重複している {ans}")

    # ---- G1b: 複数選択（内容一致）の個数。
    #      ★build.py:118 は「合致する2つ：」と**数を紙に焼き込んでいる**ので、データ側が3つに
    #        なっても紙は「2つ」と刷る。設問文の数字とも突き合わせる。
    for K in ("I", "II", "III"):
        s = content.get(K, {})
        if s.get("C_form") != "multi":
            continue
        n = len(s.get("C_multi_answers", []))
        m = re.search(r"(\d+)\s*つ選", s.get("C_instruction", ""))
        if n != 2:
            fail(f"[G1b] {K}_C: 正解が {n} 個（build.py:118 が「合致する2つ」と紙に焼き込んでいる）")
        if m and int(m.group(1)) != n:
            fail(f"[G1b] {K}_C: 設問文は「{m.group(1)}つ選べ」なのに正解が {n} 個")

    # ---- G1c: 本文のトークンと設問が対応しているか。
    #      ★片方だけ直す事故（設問の語を直したのに本文の下線が古いまま）は紙を見ないと分からない。
    for K in ("I", "II", "III"):
        s = content.get(K)
        if not s:
            continue
        t = " ".join(s["paragraphs"])
        blanks = set(re.findall(r"\[\[BL:([^\]]+)\]\]", t))
        lines = dict(re.findall(r"\[\[(?:UL|DU):([^\]=]+)=([^\]]+)\]\]", t))
        anchors = blanks | set(lines)
        for it in s["A_items"]:
            if it["ref"] not in anchors:
                fail(f"[G1c] {K}_A_{it['ref']}: 設問はあるのに本文に空所も下線も無い")
        for it in s["B_items"]:
            if it["ref"] not in lines:
                fail(f"[G1c] {K}_B_{it['ref']}: 設問はあるのに本文に下線が無い")
            elif lines[it["ref"]] != it.get("phrase"):
                fail(f"[G1c] {K}_B_{it['ref']}: 本文の下線『{lines[it['ref']]}』と"
                     f"設問の『{it.get('phrase')}』が食い違う")
        extra = anchors - {it["ref"] for it in s["A_items"]} - {it["ref"] for it in s["B_items"]}
        if extra:
            fail(f"[G1c] {K}: 本文に印だけあって設問が無い {sorted(extra)}")
    for i, it in enumerate(content.get("IV", {}).get("items", []), 1):
        bl = re.findall(r"\[\[BL:([^\]]+)\]\]", it["sentence"])
        if bl != [str(i)]:
            fail(f"[G1c] IV_{i}: 例文の空所が {bl}（[[BL:{i}]] が1つのはず）")
    vi = content.get("VI", {})
    if vi:
        bl = set(re.findall(r"\[\[BL:([^\]]+)\]\]", " ".join(l["text"] for l in vi["lines"])))
        refs = [it["ref"] for it in vi["items"]]
        if bl != set(refs):
            fail(f"[G1c] VI: 会話の空所 {sorted(bl)} と設問 {sorted(set(refs))} が食い違う")
        # ★build.py:125 の解答一覧は ref でなく **並び順の連番**で刷る。ずれると番号が二重定義になる。
        if refs != [str(i) for i in range(1, len(refs) + 1)]:
            fail(f"[G1c] VI: 設問の ref {refs} が 1..{len(refs)} の連番でない"
                 f"（build.py:125 の解答一覧は連番で刷るので番号がずれる）")

    # ---- G2: 「他の選択肢」欄が **ちょうど全部の誤答**を指しているか。
    #      選択肢の長さでモードを決める（人が指定しない＝設問が増えても自動でどちらかに入る）。
    n_letter = n_word = 0
    noref = set()
    for k, (opts, ans) in sorted(items.items()):
        ex = expl.get(k)
        if not isinstance(ex, dict):
            continue
        if not all(isinstance(a, int) and 1 <= a <= len(opts) for a in ans):
            continue                       # G1 で落としている
        dis = ex.get("distractors", "")
        cor = {OPT[a - 1] for a in ans}
        want = set(OPT[:len(opts)]) - cor
        if not dis:
            fail(f"[G2] {k}: 誤答解説(distractors)が空＝この問は無検査になる")
            continue
        if max(len(o.split()) for o in opts) > LONG_OPT_WORDS:
            got = set(LABEL.findall(dis))
            if not got:
                noref.add(k)
                continue
            n_letter += 1
            if cor & got:
                fail(f"[G2] {k}: 正解 {''.join(sorted(cor & got))} が「他の選択肢」欄に出ている"
                     f"（紙は『正解 {''.join(sorted(cor))}』と印字するので同じカードで自己矛盾する）")
            if got - want - cor:
                fail(f"[G2] {k}: 誤答解説に選択肢に無い記号 {''.join(sorted(got - want - cor))} がある"
                     f"（選択肢は {len(opts)} 個）")
            if want - got:
                fail(f"[G2] {k}: 誤答 {''.join(sorted(want - got))} に触れていない"
                     f"（言及を消すと検査が空振りする）")
            # 「考え方」欄の記号は正解だけを指すこと（+1 ずれたら本文が別の肢を語りだす）
            for lb in sorted(set(LABEL.findall(ex.get("reason", ""))) - cor):
                fail(f"[G2c] {k}: 考え方の欄が {lb} を指しているが正解バッジは {''.join(sorted(cor))}"
                     f"（誤答への言及は「他の選択肢」欄に書くこと）")
        else:
            n_word += 1
            miss = [o for i, o in enumerate(opts, 1) if i not in ans and not mentions(dis, o)]
            if miss:
                fail(f"[G2] {k}: 誤答 {miss} に触れていない"
                     f"（正解が1つずれると『実際の正解』が誤答欄に並ぶので、ここで気づける）")
            # ★語方式でも「正解を誤答欄で否定していないか」を見る。ここが無いと
            #   **このゲートを作った理由そのもの**（紙が「正解 b: on」と刷りながら
            #   「on は文法的に不可」と解説する自己矛盾）を 52問中40問で見逃す。
            #   語は本文引用にも出るので、否定語がすぐ後ろに続くときだけ落とす
            #   （実データで誤検出0・変異40/40検出を実測）。
            for i in ans:
                cor_word = opts[i - 1]
                # ★窓を「N文字」で切ると、実データの「…ので不可。」が25文字目に来て届かない。
                #   語境界を付けないと本文引用の中の同じ綴りを拾う。共通ヘルパで一文単位で見る。
                if negates(dis, cor_word, word_boundary=True):
                    fail(f"[G2] {k}: 正解 {cor_word!r} を誤答欄で否定している"
                         f"（紙は同じカードでこれを正解として印字する）")
    print(f"  誤答解説と正解バッジを照合: 記号方式 {n_letter} 問 ＋ 語方式 {n_word} 問"
          f" ＋ 参照なしで無検査 {len(noref)} 問")
    if n_letter != EXPECT_LETTER or n_word != EXPECT_WORD:
        fail(f"[G2] 照合できたのが 記号 {n_letter}/{EXPECT_LETTER}・語 {n_word}/{EXPECT_WORD} 問"
             f"— 解説の書き方が変わって空振りしている")
    if noref != NO_REF:
        # ★無検査の設問が黙って増えるのを止める。減った（＝直った）ときもここで気づける。
        fail(f"[G2] 「他の選択肢」欄が選択肢を指していない設問の顔ぶれが変わった: "
             f"{sorted(noref)}（既知は {sorted(NO_REF)}）— 解説に記号 a/b/c/d を書けば検査対象に入る")
    if n_letter + n_word + len(noref) != len(items):
        fail(f"[G2] 設問 {len(items)} 問のうち {n_letter + n_word + len(noref)} 問しか見ていない")

    # ---- G2b: 解説キーと設問の対応が **両方向で** そろっているか。
    #      ★ホワイトリスト正規表現で片側を絞ると、その形に当たらないキーは「無い」のと同じになる。
    want_keys = set(items) | {f"V_{i}" for i in range(1, n_v + 1)}
    for k in sorted(want_keys - set(expl)):
        fail(f"[G2b] {k}: 設問はあるのに解説が無い（紙に『（解説準備中）』と刷られる）")
    for k in sorted(set(expl) - want_keys):
        fail(f"[G2b] {k}: 解説はあるのに設問が見つからない（対応づけが壊れている＝紙に出ない）")

    # ---- G3: 「該当箇所」が本文/例文/会話に実在するか（空所は正解で埋めてから照合）。
    #      ★空所を空のまま照合すると 9 件が空振りする。正解で埋めると「引用が実在するか」と
    #        「その空所の正解は引用と整合しているか」を一度に見られる。
    quoted = 0
    blanks_checked = 0

    def check_quote(key, text, answer=None):
        """answer を渡すと「該当箇所に正解が入っているか」まで見る（空所補充だけ）。

        ★通し照合だけでは足りない。実測（ans を総当たりで振り替える 153 通り）で
          `Seen` → `Having seen`、`If` → `Even if` のように **正解が別の選択肢の一部**だと
          引用が部分列として成立してしまい、正解をずらしても素通りした（2件）。
          空所補充なら「該当箇所には正解の語がそのまま入っている」はずなので、それを足す。
        """
        nonlocal quoted, blanks_checked
        ex = expl.get(key)
        q = ex.get("quote", "") if isinstance(ex, dict) else ""
        if not q:
            fail(f"[G3] {key}: 該当箇所が空")
            return
        quoted += 1
        if not appears_in(q, text):
            fail(f"[G3] {key}: 該当箇所が本文に無い（要約を引用符で囲んでいる／正解と本文が食い違う）"
                 f" 『{q[:60]}…』")
        if answer is None:
            return
        blanks_checked += 1
        qw, aw = words(q), words(answer)
        if not aw or not any(qw[i:i + len(aw)] == aw for i in range(len(qw) - len(aw) + 1)):
            fail(f"[G3b] {key}: 該当箇所に正解『{answer}』が入っていない"
                 f"（空所の正解と、解説が引用した一文が食い違う）")

    for K in ("I", "II", "III"):
        s = content.get(K)
        if not s:
            continue
        t = " ".join(s["paragraphs"])
        t = re.sub(r"\[\[(?:UL|DU):[^\]=]+=([^\]]+)\]\]", r"\1", t)
        amap = {it["ref"]: it["options"][it["ans"] - 1] for it in s["A_items"]
                if isinstance(it.get("ans"), int) and 1 <= it["ans"] <= len(it["options"])}
        t = re.sub(r"\[\[BL:([^\]]+)\]\]", lambda m: " %s " % amap.get(m.group(1), "?"), t)
        for it in s["A_items"]:
            # 問A が下線型（Ⅲ）のときは本文の語そのものを問うので、正解は引用に入らない
            check_quote(f"{K}_A_{it['ref']}", t,
                        amap.get(it["ref"]) if s.get("A_kind") == "blank" else None)
        for it in s["B_items"]:
            check_quote(f"{K}_B_{it['ref']}", t)
    for i, it in enumerate(content.get("IV", {}).get("items", []), 1):
        if isinstance(it.get("ans"), int) and 1 <= it["ans"] <= len(it["options"]):
            sent = re.sub(r"\[\[BL:[^\]]+\]\]", it["options"][it["ans"] - 1], it["sentence"])
            check_quote(f"IV_{i}", sent, it["options"][it["ans"] - 1])
    for i, it in enumerate(content.get("V", {}).get("items", []), 1):
        check_quote(f"V_{i}", it.get("full_en", ""))
    if vi:
        amap = {it["ref"]: it["options"][it["ans"] - 1] for it in vi["items"]
                if isinstance(it.get("ans"), int) and 1 <= it["ans"] <= len(it["options"])}
        t = re.sub(r"\[\[BL:([^\]]+)\]\]", lambda m: " %s " % amap.get(m.group(1), "?"),
                   " ".join(l["text"] for l in vi["lines"]))
        for it in vi["items"]:
            check_quote(f"VI_{it['ref']}", t, amap.get(it["ref"]))
    print(f"  該当箇所を本文と {quoted} 件照合（うち空所の正解入りを {blanks_checked} 件確認・"
          f"要約のため外した {len(QUOTE_SKIP)} 件: 問C）")
    if blanks_checked != EXPECT_BLANK:
        fail(f"[G3b] 空所の正解を照合できたのが {blanks_checked} 件（{EXPECT_BLANK} 件のはず）")
    if quoted != EXPECT_QUOTE:
        fail(f"[G3] 本文照合できたのが {quoted} 件（{EXPECT_QUOTE} 件のはず）— 対象が減っている")
    if not QUOTE_SKIP <= set(expl):
        fail(f"[G3] 照合から外したキー {sorted(QUOTE_SKIP - set(expl))} が実在しない（名前が変わった？）")

    # ---- G4: 大問Ⅴ（語句整序）。ここは全部を機械で決められる。
    #      紙は ans2/ans6 を答えとして刷り、解説の見出しは full_en を「完成文」として刷るので、
    #      order・ans2/ans6・full_en の3つが1つでもずれると紙の中で自己矛盾する。
    for i, it in enumerate(content.get("V", {}).get("items", []), 1):
        seg = {s["ltr"]: s["text"] for s in it["segments"]}
        order = it.get("order", [])
        if sorted(order) != sorted(seg):
            fail(f"[G4] V_{i}: 並び {order} が語群 {sorted(seg)} の順列でない")
            continue
        if it.get("ans2") != order[1]:
            fail(f"[G4] V_{i}: 2番目の答え {it.get('ans2')} だが並びの2番目は {order[1]}")
        if len(order) >= 6 and it.get("ans6") != order[5]:
            fail(f"[G4] V_{i}: 6番目の答え {it.get('ans6')} だが並びの6番目は {order[5]}")
        if words(" ".join(seg[l] for l in order)) != words(it.get("full_en", "")):
            fail(f"[G4] V_{i}: 語群を並びどおりつないだ文と完成文 full_en が一致しない")
        # 解説が書いている並び（例: 「並びは cegfadhb」）も同じか
        ex = expl.get(f"V_{i}", {})
        seqs = re.findall(r"(?<![a-z])[a-h]{%d}(?![a-z])" % len(order), ex.get("reason", ""))
        if not seqs:
            fail(f"[G4] V_{i}: 考え方の欄に並び（{len(order)}文字）が書かれていない＝解説側は無検査")
        for s in seqs:
            if list(s) != order:
                fail(f"[G4] V_{i}: 解説の並び {s} が正解の並び {''.join(order)} と食い違う")

    for w in WARNS:
        print("WARN", w)
    for f in FAILS:
        print(" ×", f)
    print(f"\n=== {'ALL PASS' if not FAILS else f'FAIL {len(FAILS)}件'}"
          f"（{len(WARNS)} warnings）===")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
