#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""明治 英語 実戦問題の機械ゲート。

★このファイルが要る理由（2026-08-05）
  青学 (`scripts/aoyama_eigo_mirror/`) で、正解バッジと誤答解説を別ソースから同じカードに
  印字していたせいで、「正解 ④」と刷りながら「④…は誤り」と解説する紙が配布されていた。
  明治は **番号と語を同じソースから刷る**（build.py:359 `f'{MARU[q["ans"]-1]} {q["opts"][q["ans"]-1]}'`）
  ので青学と同型の事故は構造的に起きない。**が、解説だけは外部の
  explanations_seki.json で上書きされる**（build.py:215-227 `_inject`）ので、
  「content の ans」と「オーバーレイの解説が指す番号」がずれる余地は残っている。そこを見る。

    python3 check.py

★明治固有の事情2つ
  (1) 設問データが content.json ではなく **build.py の中**にある（MARK / DESC）。
      なので check.py は build.py を import して、**ビルダが実際に使う値**を検査する。
      import で `~/Desktop/...` が作られるのを避けるため、その間だけ os.makedirs を止める。
  (2) 「異なるものを選べ／一致しないものを選べ」型が3問（問11・問14・問24）ある。
      この型は **正解肢を誤答欄に挙げるのが正しい書き方**なので、青学の
      「正解は誤答欄に出てはいけない」をそのまま当てると誤検出になる（実測3件）。
      設問文から機械で見分けて極性を切り替える（番号のハードコードはしない）。

★守れない範囲（正直に書く）
  - 異質選択型の3問は「どれが浮いているか」を機械で判定できない（発音・語法の判断が要る）。
    このゲートが見るのは「全選択肢に言及があるか」「正解番号にも触れているか」まで。
    **正解が別の肢にすり替わっても検出できない**。実測でも3問×4通り＝12通りが素通りする。
  - 記述式（問A〜F）の答案の妥当性は見ていない。抜き出し（問A）が本文に実在するか、
    該当箇所が本文に実在するかまで。
  - 選択肢の内容が正しいか（英語として正解が本当に1つか）は見ていない。

★どこまで捕まえられるかを実測してある（2026-08-05）
  正解を1つずつ別の値へ振り替える変異 92 通り（1問あたり4通りのサンプリング。
  問8 が16択なので真の総当たりは 103 通り）→ **80/92 を検出**。
  すり抜けた 12 通りは上記の異質選択型3問**だけ**。
"""
import html
import json
import os
import re
import sys

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _mirror_negation import negates  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MARU = "①②③④⑤⑥⑦"

# ★実測値。等式で押さえる（印字するだけだと検査量が黙って減っても ALL PASS になる）。
EXPECT_MARK = 24     # マーク式設問
EXPECT_DESC = 6      # 記述式設問（A〜F）
EXPECT_EXP = 30      # explanations_seki.json のキー総数（24 + 6）
EXPECT_QUOTE = 30    # 該当箇所を本文と通し照合できる件数
EXPECT_BLANK = 14    # 空所補充＝該当箇所に正解が入っているはずの設問（単独12 ＋ 組合せ/共通2）
EXPECT_POS = 94      # 「丸数字＋選択肢の英語」で位置まで照合できた件数
EXPECT_ODD = 3       # 「異なる／一致しない」を選ばせる設問（極性が逆＝別扱い）
# 「異なるものを選べ」型の見分け。★番号でハードコードしない（設問が増えたら自動で入る）。
# ★タグを空白に置き換えてから当ててはいけない。設問文は `合致<b>しない</b>もの` と
#   語の途中にタグが入るので、空白にすると「合致しない」に当たらず問24を取りこぼす（実測）。
ODD_RE = re.compile(r"(?:異な|合致しない|一致しない|適切でないもの|誤っているもの)")


def tight(s):
    """タグを**詰めて**落とす。語の途中の <b> で語が割れるのを防ぐ（ODD 判定用）。"""
    return html.unescape(re.sub(r"<[^>]+>", "", str(s)))


FAILS, WARNS = [], []



def fail(m):
    FAILS.append(m)


def warn(m):
    WARNS.append(m)


def plain(s):
    """HTML タグと実体参照を落として素の文字列にする。’ は ' にそろえる。"""
    return html.unescape(re.sub(r"<[^>]+>", " ", str(s))).replace("’", "'").replace("‘", "'")


def words(s):
    return re.findall(r"[a-z0-9']+", plain(s).lower())


def load_build():
    """build.py を import して MARK / DESC / PARAS を取り出す。

    ★import すると build.py:11 が `~/Desktop/明治大学2026_英語実戦問題` を作る。
      検査がユーザのデスクトップにフォルダを作るのは筋が悪いので、その間だけ止める。
      PDF 生成は `__main__` ガードの中なので走らない。
    """
    # ★`import build` は **pyc キャッシュ**を使う。有効性の判定はソースの mtime(秒)と
    #   サイズだけなので、`ans=3` → `ans=4` のような**サイズが変わらない書き換え**は、
    #   同じ秒に保存されると古い pyc が再利用されて **ゲートが古いデータを見て ALL PASS** になる
    #   （実測で再現。この環境は sys.pycache_prefix があり __pycache__ が見えないので気づけない）。
    #   ソースを読んで exec する（キャッシュを一切経由しない）。
    import types
    path = os.path.join(HERE, "build.py")
    src = open(path, encoding="utf-8").read()
    mod = types.ModuleType("build")
    mod.__file__ = path
    sys.path.insert(0, HERE)
    real = os.makedirs
    os.makedirs = lambda *a, **k: None       # import 時に ~/Desktop にフォルダを作らせない
    try:
        sys.modules["build"] = mod
        exec(compile(src, path, "exec"), mod.__dict__)
    finally:
        os.makedirs = real
    return mod


def appears_in(quote, text, slack=4):
    """引用が本文に（小さな省略を許して）実在するか。語の並びが崩れたら不一致。"""
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


def filled_passage(b):
    """本文の空所を**正解で埋めて**平文にする。

    空所を空のままにすると「該当箇所」が本文に無いことになる。正解で埋めると、
    引用が実在するかと「その空所の正解は引用と整合しているか」を一度に見られる。
    """
    mark = {q["n"]: q for q in b.MARK}
    desc = {q["L"]: q for q in b.DESC}

    def fill(label):
        if label in desc:                       # 空欄 F（記述式）
            return desc[label]["ans"]
        n = int(label.split("-")[0])
        q = mark.get(n)
        if q is None:
            return "?"
        if q.get("ans") is None:                # 語句整序：正しい並びを流し込む
            return " ".join(q["opts"][i - 1] for i in q["order"])
        opt = plain(q["opts"][q["ans"] - 1])
        if "-" in label:                        # 組合せ補充（12-ア / 12-イ）と同一語（23-ア/イ）
            parts = [x.strip() for x in re.split(r"—|-", opt) if x.strip()]
            if len(parts) == 1:
                return parts[0]
            return parts[0] if label.endswith("ア") else parts[-1]
        return opt

    t = " ".join(b.PARAS)
    t = re.sub(r'<span class="bk">\(&nbsp;([^&]+)&nbsp;\)</span>',
               lambda m: " %s " % fill(m.group(1)), t)
    return plain(t)


def main():
    b = load_build()
    exp_path = os.path.join(HERE, "explanations_seki.json")
    if not os.path.exists(exp_path):
        # ★黙って飛ばさない。build.py:221 が参照しているオーバーレイが無いなら紙が壊れる。
        sys.exit("✗ explanations_seki.json が無い（build.py:221 が参照している）")
    expl = json.load(open(exp_path, encoding="utf-8"))
    mark, desc = b.MARK, b.DESC
    odd = [q for q in mark if ODD_RE.search(tight(q["stem"]))]
    print(f"マーク式 {len(mark)} 問（うち異質選択型 {len(odd)} 問）/ 記述式 {len(desc)} 問"
          f" / 解説 {len(expl)} 件")

    if len(mark) != EXPECT_MARK or len(desc) != EXPECT_DESC:
        fail(f"[G0] 設問が マーク {len(mark)}/{EXPECT_MARK}・記述 {len(desc)}/{EXPECT_DESC} 問")
    if len(expl) != EXPECT_EXP:
        fail(f"[G0] 解説が {len(expl)} 件（{EXPECT_EXP} 件のはず）")
    if len(odd) != EXPECT_ODD:
        fail(f"[G0] 異質選択型が {len(odd)} 問（{EXPECT_ODD} 問のはず）"
             f"— 極性の切り替えが効く範囲が変わった: {[q['n'] for q in odd]}")

    # ---- G1: ans が opts の範囲内か（0始まり混在はこのリポジトリで再発4例目）
    for q in mark:
        n = len(q["opts"])
        if n > len(MARU):
            fail(f"[G1] 問{q['n']}: 選択肢が {n} 個だが build.py:14 の MARU は {len(MARU)} 個しかない"
                 f"（IndexError でビルドが落ちる）")
        if q.get("ans") is None:
            continue                            # 語句整序（G4 で見る）
        if not isinstance(q["ans"], int) or not (1 <= q["ans"] <= n):
            fail(f"[G1] 問{q['n']}: ans={q['ans']} が選択肢 {n} 個の範囲外（1始まりで書くこと）")

    # ---- G1b: 本文の印（空所・下線）と設問が対応しているか。
    #      ★片方だけ直す事故（設問の語を直したのに本文の下線が古いまま）は紙を見ないと分からない。
    P = " ".join(b.PARAS)
    bk = re.findall(r'<span class="bk">\(&nbsp;([^&]+)&nbsp;\)</span>', P)
    ul = re.findall(r"<u>(.*?)</u><sup class=\"qn\">\((\d+)\)</sup>", P)
    ulL = re.findall(r"<u class=\"L\">(.*?)</u><sup class=\"qL\">\(([A-F])\)</sup>", P)
    desc_labels = {q["L"] for q in desc}
    # ★空欄 F は記述式の空所。マーク設問の印と混ぜると「印だけあって設問が無い」と誤検出する。
    anchored = {lb.split("-")[0] for lb in bk if lb.split("-")[0] not in desc_labels} \
        | {n for _, n in ul}
    for q in mark:
        if str(q["n"]) in anchored:
            continue
        # 内容一致は本文全体が対象なので下線が無いのが正しい。それ以外は印の付け忘れ。
        if "内容一致" not in q["kind"]:
            fail(f"[G1b] 問{q['n']}〔{q['kind']}〕: 本文に空所も下線も無い（設問が指す場所が紙に出ない）")
    stray = anchored - {str(q["n"]) for q in mark}
    if stray:
        fail(f"[G1b] 本文に印だけあって設問が無い {sorted(stray)}")
    desc_anchor = {L for _, L in ulL} | {lb for lb in bk if lb in {q["L"] for q in desc}}
    if desc_anchor != {q["L"] for q in desc}:
        fail(f"[G1b] 記述式の印 {sorted(desc_anchor)} と設問 {sorted(q['L'] for q in desc)} が食い違う")
    # 設問文が下線部の語を引用しているなら、本文の下線と一致すること
    ulmap = {n: plain(w).strip() for w, n in ul}
    for q in mark:
        m = re.search(r"下線部\s*\((\d+)\)\s*([A-Za-z][A-Za-z '\-]*)", plain(q["stem"]))
        if m and m.group(1) in ulmap and ulmap[m.group(1)] != m.group(2).strip():
            fail(f"[G1b] 問{q['n']}: 設問文の『{m.group(2).strip()}』と本文の下線『{ulmap[m.group(1)]}』が食い違う")
    ulLmap = {L: plain(w).strip() for w, L in ulL}
    for q in desc:
        m = re.search(r"下線部\s*([A-F])\s*[（(]([^）)]+)[）)]", plain(q["stem"]))
        if m and m.group(1) in ulLmap and ulLmap[m.group(1)] != m.group(2).strip():
            fail(f"[G1b] 問{q['L']}: 設問文の『{m.group(2).strip()}』と本文の下線『{ulLmap[m.group(1)]}』が食い違う")

    # ---- G2: 「他の選択肢」欄が **ちょうど全部の誤答**を指しているか。
    #      正解が誤答欄に出ている（青学の実害）・誤答を書き忘れた・無い番号を書いた、を同時に見る。
    checked = n_odd = 0
    for q in mark:
        ex = expl.get(f"Q{q['n']}")
        if not isinstance(ex, dict):
            fail(f"[G2] 問{q['n']}: 解説が無い（紙は build.py 内蔵の短い exp を刷る）")
            continue
        if q.get("ans") is None:
            continue
        n = len(q["opts"])
        cor, want = MARU[q["ans"] - 1], set(MARU[:n]) - {MARU[q["ans"] - 1]}
        dis = ex.get("distractors", "")
        got = {ch for ch in dis if ch in MARU}
        rea = {ch for ch in ex.get("reason", "") if ch in MARU}
        if q in odd:
            # 異質選択型：正解肢こそが「浮いている肢」なので、誤答欄に出るのが正しい書き方。
            # 見られるのは「全肢に触れているか」「正解番号にも触れているか」まで（docstring 参照）。
            n_odd += 1
            if (got | rea) != set(MARU[:n]):
                fail(f"[G2] 問{q['n']}〔異質選択〕: 解説が触れていない選択肢 "
                     f"{''.join(sorted(set(MARU[:n]) - got - rea))} がある")
            if cor not in (got | rea):
                fail(f"[G2] 問{q['n']}〔異質選択〕: 正解 {cor} に一度も触れていない")
            continue
        checked += 1
        if got - want - {cor}:
            fail(f"[G2] 問{q['n']}: 誤答解説に選択肢に無い番号 {''.join(sorted(got - want - {cor}))} がある"
                 f"（選択肢は {n} 個）")
        if want - got:
            fail(f"[G2] 問{q['n']}: 誤答 {''.join(sorted(want - got))} に触れていない"
                 f"（言及を消すと検査が空振りする）")
        if cor in got:
            # 「④は近いが、⑤が最適」のような比較のための言及は正当。誤りだと断じていたら落とす。
            # ★肯定語の白リストで例外にすると、列挙に無い自然な対比表現を全部落とす（実測10/10）。
            #   「その番号を否定している一文があるか」で見る（共通ヘルパ）。
            if negates(dis, cor):
                fail(f"[G2] 問{q['n']}: 正解 {cor} が「他の選択肢」欄に誤答として出ている"
                     f"（紙は『正解 {cor}』と印字するので同じカードで自己矛盾する）")
        # 「考え方」欄の丸数字はすべて正解を指すこと（+1 ずれたら本文が別の肢を語りだす）
        for m in re.finditer(r"[①-⑦]", ex.get("reason", "")):
            if m.group(0) == cor:
                continue
            tail = ex["reason"][m.end():m.end() + 24]
            if re.search(r"(?:に見える|と思わせ|ではない|は誤り|は不可|ひっかけ|紛らわし)", tail):
                continue
            fail(f"[G2c] 問{q['n']}: 考え方の欄が {m.group(0)} を指しているが正解バッジは {cor}"
                 f"（誤答への言及は「他の選択肢」欄に書くこと）")
    print(f"  誤答解説と正解バッジを {checked} 問で照合（異質選択型 {n_odd} 問は言及の網羅だけ）")
    if checked + n_odd != len([q for q in mark if q.get("ans") is not None]):
        fail(f"[G2] 照合できたのは {checked + n_odd} 問（残りは無検査）")

    # ---- G2b: 解説キーと設問の対応が **両方向で** そろっているか。
    want_keys = {f"Q{q['n']}" for q in mark} | {q["L"] for q in desc}
    for k in sorted(want_keys - set(expl)):
        fail(f"[G2b] {k}: 設問はあるのに解説が無い（紙は build.py 内蔵の短い exp に戻る）")
    for k in sorted(set(expl) - want_keys):
        fail(f"[G2b] {k}: 解説はあるのに設問が見つからない（build.py:224/227 の注入先が無い＝紙に出ない）")

    # ---- G3: 「該当箇所」が本文に実在するか（空所は正解で埋めてから照合）。
    passage = filled_passage(b)
    quoted = blanks = 0
    # 空所ごとに「該当箇所に入っていなければならない語」を集める。
    # 組合せ補充(12-ア/12-イ)と共通語(23-ア/23-イ)は、両方の空所に入る語を両方とも要求する。
    blank_ans = {}
    for lb in bk:
        n = lb.split("-")[0]
        if not n.isdigit():
            continue
        q = next((x for x in mark if x["n"] == int(n)), None)
        if q is None or q.get("ans") is None:
            continue                      # 語句整序（問8）は G5 で見る
        opt = plain(q["opts"][q["ans"] - 1])
        parts = [x.strip() for x in re.split(r"—|-", opt) if x.strip()] if "-" in lb else [opt]
        cur = blank_ans.setdefault(f"Q{n}", [])
        for x in parts:
            if x not in cur:
                cur.append(x)
    for key, ex in sorted(expl.items()):
        qt = ex.get("quote", "") if isinstance(ex, dict) else ""
        if not qt:
            fail(f"[G3] {key}: 該当箇所が空")
            continue
        quoted += 1
        if not appears_in(qt, passage):
            fail(f"[G3] {key}: 該当箇所が本文に無い（要約を引用符で囲んでいる／正解と本文が食い違う）"
                 f" 『{plain(qt)[:60]}…』")
        # ★通し照合だけでは足りない。関学で実測したところ、正解が別の選択肢の一部
        #   （Seen ⊂ Having seen）だと引用が部分列として成立して素通りした。
        #   空所補充なら「該当箇所に正解の語がそのまま入っている」はずなので足す。
        if key in blank_ans:
            blanks += 1
            qw = words(qt)
            for ans_txt in blank_ans[key]:
                aw = words(ans_txt)
                if not any(qw[i:i + len(aw)] == aw for i in range(len(qw) - len(aw) + 1)):
                    fail(f"[G3b] {key}: 該当箇所に正解『{ans_txt}』が入っていない"
                         f"（空所の正解と、解説が引用した一文が食い違う）")
    print(f"  該当箇所を本文と {quoted} 件照合（うち空所の正解入りを {blanks} 件確認）")
    if quoted != EXPECT_QUOTE:
        fail(f"[G3] 本文照合できたのが {quoted} 件（{EXPECT_QUOTE} 件のはず）— 対象が減っている")
    if blanks != EXPECT_BLANK:
        fail(f"[G3b] 空所の正解を照合できたのが {blanks} 件（{EXPECT_BLANK} 件のはず）")

    # ---- G3c: 抜き出し問題（本文中から一語）の答えが本文に実在するか。
    for q in desc:
        if "抜き出" not in plain(q["stem"]):
            continue
        if plain(q["ans"]).strip().lower() not in words(passage):
            fail(f"[G3c] 問{q['L']}: 抜き出しの答え『{q['ans']}』が本文に無い")

    # ---- G4: 番号つきで名指しされた選択肢の位置が opts の並びと合っているか。
    pos = 0
    for q in mark:
        ex = expl.get(f"Q{q['n']}")
        if not isinstance(ex, dict):
            continue
        opts = [plain(o).strip() for o in q["opts"]]
        for fld in ("reason", "distractors"):
            for m in re.finditer(r"([①-⑦])\s*([A-Za-z][A-Za-z '\-]*[A-Za-z])", plain(ex.get(fld, ""))):
                word = m.group(2).strip()
                if word not in opts:
                    continue
                pos += 1
                if opts.index(word) != MARU.index(m.group(1)):
                    fail(f"[G4] 問{q['n']}: 解説の「{m.group(1)}{word}」は選択肢では {MARU[opts.index(word)]}")
    print(f"  番号つきで名指しされた選択肢の位置を {pos} 件照合")
    if pos < EXPECT_POS:
        fail(f"[G4] 位置を照合できたのが {pos} 件（{EXPECT_POS} 件のはず）— 解説の書き方が変わって空振りしている")

    # ---- G5: 語句整序（問8）。**紙に刷る答えを実際に描画して**照合する。
    #      ★build.py:345/359 は「2番目=④／6番目=⑥」を**文字列で焼き込んでいる**ので、
    #        order や ans2 を直しても紙は古い答えのまま刷られる。ソースの目視では気づけない。
    for q in mark:
        if q.get("ans") is not None:
            continue
        order, opts = q.get("order", []), q["opts"]
        if sorted(order) != list(range(1, len(opts) + 1)):
            fail(f"[G5] 問{q['n']}: 並び {order} が選択肢 1..{len(opts)} の順列でない")
            continue
        want2, want6 = order[1], order[5]
        if tuple(q.get("ans2", ())) != (want2, want6):
            fail(f"[G5] 問{q['n']}: ans2={q.get('ans2')} だが並びの2番目/6番目は ({want2}, {want6})")
        # 解説が書いている並び（⑦always seemed／④to understand／…）も同じか
        seq = [MARU.index(a) + 1 for a, w in
               re.findall(r"([①-⑦])\s*([A-Za-z][A-Za-z '\-]*[A-Za-z])", plain(expl.get(f"Q{q['n']}", {}).get("reason", "")))]
        if seq[:len(order)] != order:
            fail(f"[G5] 問{q['n']}: 解説の並び {seq[:len(order)]} が正解の並び {order} と食い違う")

    answer_html = plain(b.build_answer())
    orders = [q for q in mark if q.get("ans") is None]
    if len(orders) > 1:
        # ★刷り上がりから拾う「2番目=…」は設問番号を持たないので、整序が2問以上あると
        #   どの設問のものか決められない。黙って片方だけ見るより、見られないと言う。
        fail(f"[G5] 語句整序が {len(orders)} 問ある: 刷り上がりの「2番目=…」を設問に紐づけられない")
    for q in orders:
        want = {"2": MARU[q["ans2"][0] - 1], "6": MARU[q["ans2"][1] - 1]}
        printed = sorted(set(re.findall(
            r"([26])番目\s*=\s*([①-⑦])\s*([A-Za-z][A-Za-z ]*[A-Za-z])?", answer_html)))
        if not printed:
            fail(f"[G5] 問{q['n']}: 刷り上がりに「2番目=…／6番目=…」が出てこない（描画が変わった）")
        for pos_lbl, maru, word in printed:
            if maru != want[pos_lbl]:
                fail(f"[G5] 問{q['n']}: 紙は「{pos_lbl}番目={maru} {word or ''}」と刷るが"
                     f"正解は {want[pos_lbl]}（build.py:345/359 が答えを文字列で焼き込んでいる）")
            idx = q["ans2"][0 if pos_lbl == "2" else 1]
            if word and word.strip() != plain(q["opts"][idx - 1]).strip():
                fail(f"[G5] 問{q['n']}: 紙は「{pos_lbl}番目={maru} {word.strip()}」と刷るが"
                     f"{maru}の語句は『{plain(q['opts'][idx-1])}』")

    # 記述式の解答が刷り上がりに載っているか。★これは描画経路の生存確認（q["ans"] を
    #   そのまま刷るので値の照合にはならない）。テンプレートを触って解答欄ごと消したら気づける。
    for q in desc:
        if f'問{q["L"]}　解答: {plain(q["ans"])}' not in answer_html:
            fail(f"[G5] 問{q['L']}: 刷り上がりの解答欄に『{q['ans']}』が出ていない（描画が変わった）")

    for w in WARNS:
        print("WARN", w)
    for f in FAILS:
        print(" ×", f)
    print(f"\n=== {'ALL PASS' if not FAILS else f'FAIL {len(FAILS)}件'}"
          f"（{len(WARNS)} warnings）===")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
