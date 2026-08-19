# -*- coding: utf-8 -*-
"""正解を伏せた blind.json と、照合用 answer_key.json を出力する。

★盲ソルバーには必ず「番号の起点」を明示する（このリポジトリで 0始まり/1始まり の
  取り違えが再発しており、全問ずれて『鍵誤り』に見える事故が起きている）。
  blind.json 側は 1〜4 で答えさせ、reconcile.py が 1始まり同士で照合する。
"""
import os, sys, json, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from content import TESTS  # noqa: E402
import build  # noqa: E402

tests = build.assign(TESTS)

blind, key = [], {}
for t in tests:
    items = []
    for it in t["items"]:
        qid = "T%02d-%02d" % (t["no"], it["n"])
        items.append({
            "qid": qid,
            "word": it["word"],
            "pos": it["pos"],
            "choices": {str(i + 1): c for i, c in enumerate(it["choices"])},
        })
        key[qid] = it["answer"] + 1
    blind.append({"test_no": t["no"], "title": t["title"], "items": items})

# ★解答シートは「どの版の blind.json を解いたか」が分からないと、あとから照合できない。
#   見出し語を1語差し替えるだけで正解位置が動くので、古いシートが「鍵誤り」に見える。
#   実際に solver_A〜E（第10回）と solver_N1/N2（第16回）で起きた。
version = hashlib.md5(json.dumps(
    [[it["word"], it["choices"], it["answer"]] for t in tests for it in t["items"]],
    ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]

payload = {
    "blind_version": version,
    "instruction": (
        "英検準1級の単語テスト（4択・意味選択）です。各設問について、見出し語 word の意味として"
        "最も適切な選択肢の番号を答えてください。"),
    "answer_format": "選択肢の番号を 1〜4 の整数で答える（0始まりではない）",
    "output_schema": {"qid": "1〜4の整数"},
    "note_for_solver": "回答ファイルに blind_version をそのまま書き写してください（版の取り違え検出用）",
    "tests": blind,
}
with open(os.path.join(HERE, "blind.json"), "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=1)
key["__blind_version__"] = version
with open(os.path.join(HERE, "answer_key.json"), "w", encoding="utf-8") as f:
    json.dump(key, f, ensure_ascii=False, indent=1)
print("wrote blind.json (%d問) / answer_key.json  版=%s" % (len(key) - 1, version))
