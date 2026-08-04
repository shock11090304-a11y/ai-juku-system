# -*- coding: utf-8 -*-
"""
ブラインド採点の突合。data/<key>.json（正解キー）と verify/<key>.json（独立ソルバーの解答 {id:answer}）を
決定的に比較して flagged.json（不一致）を出す。★判定は Python が行う（LLM は解くだけ）。

  python3 reconcile.py
"""
import json, os, glob, re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
VERIFY = os.path.join(HERE, "verify")


def norm(s):
    s = str(s).lower().strip()
    s = re.sub(r"[.,!?;:\"'`]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def key_items(d, key):
    """id -> (type, canonical_answer, question dict) を作る（make_blind と同じ id 規約）。"""
    out = {}
    if key.split("_")[1].startswith("g"):
        for tier in ("kiso", "hyojun", "nyushi"):
            for i, q in enumerate(d.get(tier, []), start=1):
                out[f"{tier}{i}"] = q
    else:
        for i, q in enumerate(d.get("questions", []), start=1):
            out[f"q{i}"] = q
    return out


def compare(q, solver):
    """(status, detail) を返す。status: OK / MISMATCH / REVIEW / SKIP。"""
    t = q["type"]
    if t in ("mc", "rc_mc"):
        try:
            si = int(solver)
        except (ValueError, TypeError):
            return "REVIEW", f"solver非整数={solver!r}"
        return ("OK" if si == q["ans"] else "MISMATCH"), f"solver={si} key={q['ans']}"
    if t == "error":
        return ("OK" if str(solver).strip().lower().strip("()") == str(q["ans"]).lower()
                else "MISMATCH"), f"solver={solver!r} key={q['ans']!r}"
    if t == "order":
        return ("OK" if norm(solver) == norm(q["ans"]) else "REVIEW"), f"solver={solver!r} key={q['ans']!r}"
    if t == "fill":
        acc = {norm(q["ans"])}
        return ("OK" if norm(solver) in acc else "REVIEW"), f"solver={solver!r} key={q['ans']!r}"
    if t == "rewrite":
        sv = solver if isinstance(solver, list) else re.split(r"[/,]", str(solver))
        sv = [norm(x) for x in sv]
        kv = [norm(x) for x in q["blanks"]]
        return ("OK" if sv == kv else "REVIEW"), f"solver={sv} key={kv}"
    return "SKIP", ""


def main():
    flags = []
    stats = {"OK": 0, "MISMATCH": 0, "REVIEW": 0, "SKIP": 0, "NOANS": 0}
    for dp in sorted(glob.glob(os.path.join(DATA, "*.json"))):
        key = os.path.basename(dp)[:-5]
        vp = os.path.join(VERIFY, key + ".json")
        if not os.path.exists(vp):
            print(f"[warn] verify 無し: {key}")
            continue
        d = json.load(open(dp, encoding="utf-8"))
        v = json.load(open(vp, encoding="utf-8"))
        answers = v.get("answers", v)  # {id: ans} 形式 or ラップ
        items = key_items(d, key)
        for iid, q in items.items():
            if q["type"] in ("ja2en", "rc_desc"):
                continue
            if iid not in answers:
                stats["NOANS"] += 1
                continue
            st, detail = compare(q, answers[iid])
            stats[st] = stats.get(st, 0) + 1
            if st in ("MISMATCH", "REVIEW"):
                flags.append({"key": key, "id": iid, "type": q["type"], "status": st, "detail": detail,
                              "point": q.get("point", "")})
    with open(os.path.join(HERE, "flagged.json"), "w", encoding="utf-8") as f:
        json.dump(flags, f, ensure_ascii=False, indent=1)
    print("突合統計:", stats)
    print(f"要確認 {len(flags)} 件 → flagged.json")
    for fl in flags:
        print(f"  [{fl['status']}] {fl['key']} {fl['id']} ({fl['type']}) {fl['detail']}")


if __name__ == "__main__":
    main()
