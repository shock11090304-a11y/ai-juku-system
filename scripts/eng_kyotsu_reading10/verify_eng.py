#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共通テスト形式 英語長文10題の機械検証(盲解答で測れない軸を潰す)。

  python3 verify_eng.py

検証する軸:
  A 語数        本文が 240〜260語か
  B 解答形式    answer が1始まりの1〜4か・指定した正解番号と一致するか
  C 正解位置    全50問で①②③④に偏りがないか(並列作問は正解位置が収束する)
  D 選択肢の長さ 正解だけが最長/最短になっていないか(内容を読まずに当てられる手がかり)
  E 本文一致度  正解の選択肢だけが本文の語句をそのまま多く含んでいないか(共テの典型的な"tell")
  F 根拠        evidence が本文中に実在するか
  G 解説        explanation_ja / distractor_ja が埋まっているか
  H 構成        5問×4択・glossary の量・重複設問・場面設定のリード文
  I 同期        passages と stems(盲解答用)がずれていないか
"""
import os, re, sys, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
PASS = os.path.join(HERE, "passages")

# ★build 側と同じ「割り当てた正解番号」。作問が指定を守ったかを機械で確かめる。
# ★当初の配分は10題すべてで「問1〜問4が①②③④の並べ替え」になっており、3問確信すると
#   4問目が消去法で決まった。rekey.py で題内の重複を許す配置に組み替えた(全体は 14/12/12/12)。
KEYS = [
    [2, 4, 1, 1, 3], [3, 1, 4, 4, 2], [1, 3, 3, 4, 2], [4, 2, 2, 1, 3], [2, 1, 4, 4, 1],
    [3, 4, 1, 3, 2], [1, 2, 2, 4, 3], [4, 3, 3, 1, 1], [2, 4, 1, 1, 3], [1, 2, 4, 2, 3],
]

NG, WARN = [], []


def add(bucket, pid, axis, msg):
    bucket.append(f"[{axis}] {pid}  {msg}")


def words(s):
    return [w for w in re.split(r"[^A-Za-z'’\-]+", s or "") if w]


def norm(s):
    """比較用: 小文字化し記号と連続空白を潰す。"""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())).strip()


def ngram_overlap(option, passage_norm, n=3):
    """選択肢と本文が共有する n-gram(語の並び)の数。丸写しの度合い。"""
    ow = norm(option).split()
    if len(ow) < n:
        return 0
    pw = passage_norm.split()
    pset = {" ".join(pw[i:i + n]) for i in range(len(pw) - n + 1)}
    return sum(1 for i in range(len(ow) - n + 1) if " ".join(ow[i:i + n]) in pset)


def main():
    all_answers = []
    longest_is_answer = shortest_is_answer = 0
    rank_of_answer = []
    overlap_top = 0
    n_q = 0

    for no in range(1, 11):
        pid0 = f"{no:02d}"
        path = os.path.join(PASS, f"p{pid0}.json")
        if not os.path.exists(path):
            add(NG, pid0, "H", "ファイルが無い")
            continue
        with open(path, encoding="utf-8") as f:
            d = json.load(f)

        body = d.get("passage", "")
        wc = len(words(body))
        if not (240 <= wc <= 260):
            add(NG, pid0, "A", f"本文が {wc} 語(240〜260であるべき)")
        pn = norm(re.sub(r"</?u>", "", body))

        qs = d.get("questions", [])
        if len(qs) != 5:
            add(NG, pid0, "H", f"設問が {len(qs)} 問(5問であるべき)")
        if len(d.get("glossary") or []) > 6:
            add(WARN, pid0, "H", f"語注が {len(d['glossary'])} 語(多すぎ=語彙が共テ超えの疑い)")
        if not (d.get("translation_ja") or "").strip():
            add(NG, pid0, "G", "全文和訳が空")
        # ★共通テストは必ず場面設定の1文で素材を枠付けする。これが無いと設問の
        #   「According to the website / the blog」が本文中に根拠を持たなくなる。
        if not (d.get("lead") or "").strip():
            add(NG, pid0, "H", "場面設定のリード文(lead)が無い")

        seen_q = set()
        for i, q in enumerate(qs, 1):
            pid = f"{pid0}-{i}"
            n_q += 1
            opts = q.get("options") or []
            a = q.get("answer")

            if len(opts) != 4:
                add(NG, pid, "H", f"選択肢が {len(opts)} 個")
                continue
            if not isinstance(a, int) or not (1 <= a <= 4):
                add(NG, pid, "B", f"answer が {a!r}(1〜4の整数であるべき。0始まりの混入に注意)")
                continue
            all_answers.append(a)
            want = KEYS[no - 1][i - 1]
            if a != want:
                add(NG, pid, "B", f"正解番号が {a}(割り当ては {want})→ 全体の正解位置の配分が崩れる")

            # D 長さ
            L = [len(o) for o in opts]
            if L[a - 1] == max(L) and L.count(max(L)) == 1:
                longest_is_answer += 1
            if L[a - 1] == min(L) and L.count(min(L)) == 1:
                shortest_is_answer += 1
            if len(set(L)) > 1:                     # 全部同じ長さ(order型)は除外
                rank_of_answer.append(sorted(L, reverse=True).index(L[a - 1]) + 1)
            if max(L) > 2.2 * min(L):
                add(WARN, pid, "D", f"選択肢の長さの差が大きい {L}")

            # E 本文の丸写し度
            ov = [ngram_overlap(o, pn) for o in opts]
            if ov[a - 1] == max(ov) and ov.count(max(ov)) == 1 and max(ov) >= 2:
                overlap_top += 1

            # F 根拠
            # evidence は複数文を " / " でつなぐことがあるので、断片ごとに本文実在を見る
            raw = q.get("evidence", "") or ""
            if not norm(raw):
                add(NG, pid, "F", "evidence が空")
            else:
                for frag in re.split(r"\s+/\s+|(?<=[.!?])\s+(?=[A-Z])", raw):
                    # 引用に付けた注記(「Paragraph 2:」「(Day 6)」)は本文には無いので落としてから照合
                    g = re.sub(r"^Paragraph\s*\d+\s*[:(]?\s*", "", frag)
                    g = re.sub(r"\((?:Day|Para\.?|Paragraph)\s*\d+\)", "", g)
                    f = norm(g.strip(" '\""))
                    if len(f) > 25 and f[:55] not in pn:
                        add(WARN, pid, "F", f"evidence の断片が本文に無い: 「{frag.strip()[:60]}…」")

            # G 解説
            for k in ("explanation_ja", "distractor_ja"):
                if not (q.get(k) or "").strip():
                    add(NG, pid, "G", f"{k} が空")

            # H 重複設問
            key = norm(q.get("q", ""))[:50]
            if key in seen_q:
                add(NG, pid, "H", "同じ設問文が同一題内で重複")
            seen_q.add(key)

            if len({norm(o) for o in opts}) != 4:
                add(NG, pid, "H", "選択肢に重複がある")

    # I ★passages と stems のドリフト検査
    #   stems は「答えを見ずに解く側」が読むファイル。本文や選択肢がずれていると、
    #   盲解答の検証が別テキストに対する検証になり無意味になる(実際に1題ずれていた)。
    for no in range(1, 11):
        pa = os.path.join(PASS, f"p{no:02d}.json")
        st = os.path.join(HERE, "stems", f"p{no:02d}.json")
        if not (os.path.exists(pa) and os.path.exists(st)):
            continue
        A = json.load(open(pa, encoding="utf-8"))
        B = json.load(open(st, encoding="utf-8"))
        d2 = []
        if A.get("passage") != B.get("passage"):
            d2.append("本文")
        if A.get("lead") != B.get("lead"):
            d2.append("lead")
        if (A.get("glossary") or []) != (B.get("glossary") or []):
            d2.append("語注")
        for i, (qa, qb) in enumerate(zip(A["questions"], B["questions"]), 1):
            if qa.get("q") != qb.get("q"):
                d2.append(f"問{i}設問文")
            if qa.get("options") != qb.get("options"):
                d2.append(f"問{i}選択肢")
        if d2:
            add(NG, f"{no:02d}", "I", f"passages と stems がずれている: {d2}")

    # C2 題内の並べ替え(消去法で1問取れる)
    for no in range(1, 11):
        k = KEYS[no - 1][:4]
        if sorted(k) == [1, 2, 3, 4]:
            add(NG, f"{no:02d}", "C", f"問1〜問4の正解が①②③④の並べ替え {k} → 3問分かると4問目が消去法で決まる")

    # C 全体の正解位置
    dist = collections.Counter(all_answers)
    print(f"問題数 {n_q}  /  正解位置の分布 " + " ".join(f"{k}:{dist.get(k,0)}" for k in (1, 2, 3, 4)))
    if all_answers:
        hi, lo = max(dist.values()), min(dist.get(k, 0) for k in (1, 2, 3, 4))
        if hi - lo > 5:
            add(NG, "全体", "C", f"正解位置が偏っている {dict(sorted(dist.items()))}")
        rk = collections.Counter(rank_of_answer)
        print("長さ順位における正解の位置 " + " ".join(f"{r}位:{rk.get(r,0)}" for r in (1, 2, 3, 4))
              + "  (各25%前後が自然)")
        if max(rk.values(), default=0) > 0.42 * len(rank_of_answer):
            top = max(rk, key=lambda r: rk[r])
            add(NG, "全体", "D", f"正解の長さ順位が{top}位に {rk[top]}/{len(rank_of_answer)} 集中 "
                                 f"→「長い方から{top}番目を選ぶ」だけで当たってしまう")
        print(f"正解が最長の選択肢 {longest_is_answer}/{len(all_answers)} 問 "
              f"/ 最短 {shortest_is_answer}/{len(all_answers)} 問 "
              f"/ 本文の丸写し最多 {overlap_top}/{len(all_answers)} 問  (いずれも25%前後が自然)")
        for label, v in (("最長", longest_is_answer), ("最短", shortest_is_answer),
                         ("本文の丸写し最多", overlap_top)):
            if v > 0.45 * len(all_answers):
                add(NG, "全体", "D/E", f"正解が{label}になる割合が {v}/{len(all_answers)} "
                                       f"→ 本文を読まずに当てられる手がかりになっている")

    print(f"NG {len(NG)} 件 / WARN {len(WARN)} 件\n")
    for s in NG:
        print("NG   " + s)
    if WARN:
        print()
    for s in WARN:
        print("warn " + s)
    return 1 if NG else 0


if __name__ == "__main__":
    sys.exit(main())
