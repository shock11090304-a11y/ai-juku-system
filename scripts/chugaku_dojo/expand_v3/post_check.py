#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""投入後の本番検証。生徒のブラウザと同じ経路 (公開 bank API) で、単元カードごとに配信される小問を確かめる。
    python3 scripts/chugaku_dojo/expand_v3/post_check.py            # 投入後
    python3 scripts/chugaku_dojo/expand_v3/post_check.py --before   # 投入前 (任意): 期待 = 既存だけ・新規 0 問。
        本番の既存プールがリポジトリの見積もりとずれていないかを先に確かめ、投入後の NG を「基準のずれ」と切り分ける。
確認: (1) 各単元の topic LIKE → unitExact 後の小問数が「既存 + 24」になっている
          (画面と同じ取得行数 = 読解 32 / それ以外 50 で取り、押し出されていないこと)
      (2) 新規の 24 問が全部届き、選択肢順・answer・解説 が手元の build/flat.json と一致 (投入時の化けを検出)
      (3) 読解単元の本文が手元の本文と完全一致
★本番 API につなぐので CI からは回さない (run_all_gates.py の SKIP に登録)。
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _v3lib as L  # noqa: E402

API = "https://ai-juku-api-production.up.railway.app/api/exam-questions/bank"
BEFORE = "--before" in sys.argv


def pref(u):
    return re.split(r"[（(：:]", str(u or ""))[0].strip()


def fetch(part, topic, limit):
    url = API + "?" + urllib.parse.urlencode({"exam": "chugaku", "part": part, "eiken_grade": "koukou", "topic": topic, "limit": limit})
    for attempt in range(3):   # 一時的な 5xx・タイムアウトは 2 回までやり直す
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                d = json.loads(r.read().decode())
            break
        except Exception as e:
            if attempt == 2: raise
            print(f"  (再試行 {attempt + 1}: {part}/{topic} {e})"); time.sleep(3)
    out = []
    for a in (d.get("all") or []):
        for q in (a.get("questions") or []):
            q = dict(q); q["_passage"] = a.get("passage", ""); out.append(q)
    return out


flat = json.load(open(os.path.join(L.HERE, "build", "flat.json"), encoding="utf-8"))
local = {L.sig(q["stem"], q["choices"]): q for q in flat}
ex = L.existing_questions()
fail = []
for u in L.load_units():
    n_new = 0 if BEFORE else sum(1 for q in flat if q["unit"] == u["filter"] and q["part"] == u["part"])
    expect = sum(1 for q in ex[u["part"]] if q["filter"] == u["filter"]) + n_new
    subs = fetch(u["part"], u["filter"], L.bank_limit(u["reading"]))
    exact = [q for q in subs if pref(q.get("unit")).startswith(u["filter"])]
    mism = 0; seen_new = 0
    for q in exact:
        k = L.sig(q.get("stem"), q.get("choices")); lq = local.get(k)
        if not lq: continue
        seen_new += 1
        if q.get("choices") != lq["choices"] or str(q.get("answer")) != lq["answer"] or q.get("explanation") != lq["explanation"]:
            mism += 1
        if u["reading"] and (q.get("_passage") or "") != lq.get("passage", ""): mism += 1
    flag = "" if (len(exact) == expect and mism == 0 and seen_new == n_new) else "  ⚠️"
    print(f"{u['part']:6} {u['filter']:<10} 配信 {len(exact):3} (期待 {expect:3}) 新規一致 {seen_new:2} 不一致 {mism}{flag}")
    if len(exact) != expect: fail.append(f"{u['part']}/{u['filter']}: 配信 {len(exact)} ≠ 期待 {expect} (0 なら未投入=全プールへフォールバック中)")
    if seen_new != n_new: fail.append(f"{u['part']}/{u['filter']}: 新規 {n_new} 問のうち届いたのは {seen_new} 問")
    if mism: fail.append(f"{u['part']}/{u['filter']}: 本番と手元で {mism} 件 不一致")
print()
if BEFORE: print("(--before: 投入前の基準確認。期待 = リポジトリにある既存の問題数、新規は 0 問が正)")
if fail:
    print("❌ 検証 NG"); [print("  -", f) for f in fail]; sys.exit(1)
print("✅ 本番検証 すべて PASS")
