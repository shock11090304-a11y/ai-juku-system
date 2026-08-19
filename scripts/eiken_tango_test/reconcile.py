# -*- coding: utf-8 -*-
"""盲ソルバーの解答と鍵を Python で決定的に照合する（LLM に一致判定をさせない）。

  python3 reconcile.py solver_N1.json solver_N2.json ...

★全員が鍵と違う qid（key-mismatch）が、本物の鍵誤りの最強シグナル。
★1人だけ外した qid は「難しいが正しい」ことが多いので、意味を人が見て判断する。
"""
import os, sys, json
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
key = json.load(open(os.path.join(HERE, "answer_key.json"), encoding="utf-8"))
KEY_VERSION = key.pop("__blind_version__", None)

solvers = {}
for path in sys.argv[1:]:
    name = os.path.basename(path).replace(".json", "")
    raw = json.load(open(path, encoding="utf-8"))
    ans = raw.get("answers", raw)
    solvers[name] = {k: int(v) for k, v in ans.items() if str(v).strip().isdigit()}

# ★解答シートが「どの版の blind.json を解いたか」を見る。見出し語を1語差し替えるだけで
#   正解位置が動くので、古いシートは全問ずれて「鍵誤り」に見える（実際に2回起きた）。
for path in sys.argv[1:]:
    raw = json.load(open(path, encoding="utf-8"))
    v = raw.get("blind_version") if isinstance(raw, dict) else None
    if KEY_VERSION and v and v != KEY_VERSION:
        print("★%s は古い版の blind.json を解いています（%s ≠ %s）。"
              "解き直すか、位置移動かどうかを別途確かめてください。"
              % (os.path.basename(path), v, KEY_VERSION))
    elif KEY_VERSION and not v:
        print("※%s に blind_version がありません（版の取り違えを機械で検出できません）"
              % os.path.basename(path))

print("鍵 %d問 / ソルバー %s" % (len(key), ", ".join(
    "%s=%d問" % (n, len(a)) for n, a in solvers.items())))

# ★未回答を「不一致」に混ぜてはいけない。範囲を絞って解かせたソルバー（例: 追加分の
#   200問だけ）を全問と突き合わせると、解いていない分がそのまま「鍵誤りの疑い」に化けて
#   50%と表示される。実際に読み違えかけた。分母は**そのソルバーが解いた問題**にする。
mismatch = defaultdict(list)
for qid, k in key.items():
    for name, a in solvers.items():
        if qid in a and a[qid] != k:
            mismatch[qid].append("%s=%d" % (name, a[qid]))

answered = {q: [n for n, a in solvers.items() if q in a] for q in key}
# ★「全員不一致」は**2人以上が解いた上で全員外した**ときだけ。1人しか解いていない qid を
#   ここに入れると、単独ソルバーの間違い1つが最強シグナル（鍵誤りの疑い）に化ける。
allmiss = [q for q, v in mismatch.items() if len(answered[q]) >= 2 and len(v) == len(answered[q])]
somemiss = [q for q, v in mismatch.items() if 0 < len(v) < len(answered[q])]
solo = [q for q, v in mismatch.items() if len(answered[q]) == 1 and v]

for name, a in solvers.items():
    # ★分母も対象外の数も、鍵にある qid だけで数える。qid を打ち間違えたソルバーの
    #   取りこぼしが「対象外0問」として見えなくなる（旧版はそれを表示していた）。
    valid = set(a) & set(key)
    hit = sum(1 for q in valid if a[q] == key[q])
    bogus = len(a) - len(valid)
    skipped = len(key) - len(valid)
    print("  %s : %d/%d 一致 (%.1f%%)%s%s"
          % (name, hit, len(valid), 100.0 * hit / len(valid) if valid else 0.0,
             "  ［対象外 %d問は未回答］" % skipped if skipped else "",
             "  ★鍵に無い qid が %d件" % bogus if bogus else ""))

print("\n★全員不一致 (鍵誤りの疑い) %d件" % len(allmiss))
for q in sorted(allmiss):
    print("   %s  鍵=%d  %s" % (q, key[q], " ".join(mismatch[q])))
print("\n一部不一致 %d件" % len(somemiss))
for q in sorted(somemiss):
    print("   %s  鍵=%d  %s" % (q, key[q], " ".join(mismatch[q])))
if solo:
    print("\n単独回答者のみの不一致 %d件（1人では鍵誤りの根拠にならない。人が見る）" % len(solo))
    for q in sorted(solo):
        print("   %s  鍵=%d  %s" % (q, key[q], " ".join(mismatch[q])))

# ★solo も exit 1 にする。1人で回したときに本物の鍵誤りが「単独回答者のみの不一致」に
#   落ちて exit 0 で素通りしていた（範囲を絞って1本だけ回すのは普通の使い方）。
#   somemiss は入れない。複数ソルバーなら1人だけ外すのは常態で、恒常的に赤になる
#   （docstring の「1人だけ外した qid は人が見て判断する」と矛盾する）。
sys.exit(1 if (allmiss or solo) else 0)
