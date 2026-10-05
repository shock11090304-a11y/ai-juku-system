#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""投入後の本番検証。生徒のブラウザと同じ経路 (公開 bank API) で、英文法 13 カードに配信される小問を確かめる。
    python3 scripts/kosei_dojo/eibunpo_v2/post_check.py            # 投入後
    python3 scripts/kosei_dojo/eibunpo_v2/post_check.py --before   # 投入前 (必須): 期待 = 既存だけ・新規 0 問
確認: (1) 新規 30 問が全部届き、選択肢順・answer・解説・unit が手元の build/flat.json と一致
      (2) 各カードの unitExact 後の配信数が投入前 (--before で保存) より減っていない (窓 50 行から押し出された行の影響)
      (3) 英文法 総合 (filter なし) は行数 50 と、新しい順に 40 行が新規かを表示するだけ
★本番の英文法プールは seed より大きい (AI の古い行 + 2026-08-18 のタグ付け) ので「既存 + 30」の等式では判定しない。
★本番 API につなぐので CI からは回さない (run_all_gates.py の SKIP に登録)。
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib as L  # noqa: E402

API = "https://ai-juku-api-production.up.railway.app/api/exam-questions/bank"
BEFORE = "--before" in sys.argv


def fetch(part, topic, limit):
    params = {"exam": L.EXAM, "part": part, "eiken_grade": L.GRADE, "limit": limit}
    if topic: params["topic"] = topic
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                d = json.loads(r.read().decode())
            break
        except Exception as e:
            if attempt == 2: raise
            print(f"  (再試行 {attempt + 1}: {part}/{topic} {e})"); time.sleep(3)
    rows = d.get("all") or []
    out = []
    for a in rows:
        for q in (a.get("questions") or []):
            q = dict(q); q["_source"] = a.get("source"); out.append(q)
    return rows, out


flat = json.load(open(os.path.join(L.HERE, "build", "flat.json"), encoding="utf-8")) if os.path.exists(os.path.join(L.HERE, "build", "flat.json")) else []
local = {L.sig(q["stem"], q["choices"]): q for q in flat}
BEFORE_PATH = os.path.join(L.HERE, "blind", "postcheck_before.json")
if not BEFORE and not os.path.exists(BEFORE_PATH) and "--no-before-check" not in sys.argv:
    print(f"❌ 投入前の配信数 {BEFORE_PATH} が無い。先に --before を回してください (比較を省くなら --no-before-check)"); sys.exit(1)
before = json.load(open(BEFORE_PATH, encoding="utf-8")) if (not BEFORE and os.path.exists(BEFORE_PATH)) else {}
snapshot = {}
fail = []
for u in L.load_units():
    key = f"{u['part']}/{u['filter']}"
    n_new = 0 if BEFORE else sum(1 for q in flat if q["filter"] == u["filter"] and q["part"] == u["part"])
    rows, subs = fetch(u["part"], u["filter"], L.bank_limit())
    exact = [q for q in subs if L.pref(q.get("unit")).startswith(u["filter"])]
    mism = 0; seen_new = 0
    for q in exact:
        lq = local.get(L.sig(q.get("stem"), q.get("choices")))
        if not lq: continue
        seen_new += 1
        if q.get("choices") != lq["choices"] or str(q.get("answer")) != str(lq["answer"]) or q.get("explanation") != lq["explanation"] or q.get("unit") != lq["unit"]:
            mism += 1
    snapshot[key] = {"rows": len(rows), "exact": len(exact)}
    b = before.get(key)
    base_txt = f" (投入前 {b['exact']:3})" if b else ""
    cap = "  (窓は上限)" if len(rows) >= L.bank_limit() else ""
    bad = (seen_new != n_new) or bool(mism) or bool(b and len(exact) < b["exact"])
    flag = "  ⚠️" if bad else ""
    print(f"{u['part']:15} {u['filter']:<6} 行 {len(rows):2}/{L.bank_limit()} 配信 {len(exact):3}{base_txt} 新規一致 {seen_new:2} 不一致 {mism}{cap}{flag}")
    if seen_new != n_new: fail.append(f"{key}: 新規 {n_new} 問のうち届いたのは {seen_new} 問")
    if mism: fail.append(f"{key}: 本番と手元で {mism} 件 不一致")
    if b and len(exact) < b["exact"]: fail.append(f"{key}: 配信される問題が投入前より減った ({b['exact']} → {len(exact)})。窓から押し出された行に同単元の問題が多い")
if BEFORE:
    if fail:
        print(f"\n⚠️ NG があるので投入前の基準は保存しません (新規が既に届いている = 投入後に --before を回した可能性)")
    elif os.path.exists(BEFORE_PATH) and "--force" not in sys.argv:
        print(f"\n⚠️ {BEFORE_PATH} が既にあるので上書きしません (上書きするなら --force)")
    else:
        os.makedirs(os.path.dirname(BEFORE_PATH), exist_ok=True)
        json.dump(snapshot, open(BEFORE_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\n→ 投入前の配信数を {BEFORE_PATH} に保存 (投入後の比較に使う)")
rows, subs = fetch("r_grammar", None, 50)
n_new_rows = sum(1 for a in rows if a.get("source") == L.SOURCE)
print(f"\n英文法 総合 (filter なし): 行 {len(rows)}/50、そのうち今回の行 {n_new_rows}")
print()
if BEFORE: print("(--before: 投入前の基準。新規一致は 0 が正。配信数は投入後の比較に使う)")
if fail:
    print("❌ 検証 NG"); [print("  -", f) for f in fail]; sys.exit(1)
print("✅ 本番検証 すべて PASS")
