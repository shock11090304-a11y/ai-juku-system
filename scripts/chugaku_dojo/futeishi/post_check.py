#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""投入後の本番検証。生徒のブラウザと同じ経路(公開 bank API)で確認する。

実行: python3 scripts/chugaku_dojo/futeishi/post_check.py

確認項目:
  1. topic='不定詞の用法' で 30小問が unitExact 後に残る (0件だと server が全プールへ
     フォールバックし、別単元がこのカードで配信される = 事故)
  2. 既存カード topic='不定詞・動名詞' に新問題が混ざっていない (24問のまま)
  3. 新問題側に既存の '不定詞・動名詞' が混ざっていない
  4. 保存された answer/選択肢/解説が手元の flat.json と 1問ずつ一致する (投入時の化けを検出)
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request

API = "https://ai-juku-api-production.up.railway.app/api/exam-questions/bank"
BASE = os.path.dirname(os.path.abspath(__file__))
UNIT = "不定詞の用法"
OTHER = "不定詞・動名詞"


def pref(u):
    return re.split(r"[（(：:]", str(u or ""))[0].strip()


def fetch(topic):
    url = API + "?" + urllib.parse.urlencode(
        {"exam": "chugaku", "part": "eng", "eiken_grade": "koukou", "topic": topic, "limit": 50})
    with urllib.request.urlopen(url) as r:
        d = json.loads(r.read().decode())
    subs = [q for a in (d.get("all") or []) for q in (a.get("questions") or [])]
    return subs


fail = []

new_all = fetch(UNIT)
new_exact = [q for q in new_all if pref(q.get("unit")).startswith(UNIT)]
print(f"[1] topic='{UNIT}': LIKE {len(new_all)}小問 → unitExact {len(new_exact)}小問")
if len(new_exact) != 30:
    fail.append(f"新単元の小問が30でない: {len(new_exact)} "
                "(0 なら未投入=server が全プールへフォールバックし別単元が配信されます)")

old_all = fetch(OTHER)
old_exact = [q for q in old_all if pref(q.get("unit")).startswith(OTHER)]
leak_into_old = [q for q in old_all if pref(q.get("unit")).startswith(UNIT)]
print(f"[2] topic='{OTHER}': unitExact {len(old_exact)}小問 / 新問題の混入 {len(leak_into_old)}件")
if len(old_exact) != 24:
    fail.append(f"既存カードの小問数が24から変化: {len(old_exact)}")
if leak_into_old:
    fail.append(f"既存カードに新問題が混入: {len(leak_into_old)}件")

leak_into_new = [q for q in new_all if pref(q.get("unit")).startswith(OTHER)]
print(f"[3] 新カードへの既存問題の混入: {len(leak_into_new)}件")
if leak_into_new:
    fail.append(f"新カードに既存問題が混入: {len(leak_into_new)}件")

def sig(q):
    """照合キー = 設問文 + 選択肢。指示文だけの stem は複数問で重複しうるので stem 単独は不可。"""
    return (" ".join(str(q.get("stem", "")).split()),
            tuple(sorted(str(c) for c in (q.get("choices") or []))))


local = {sig(q): q
         for q in json.load(open(os.path.join(BASE, "build", "flat.json"), encoding="utf-8"))}
mismatch = []
for q in new_exact:
    k = sig(q)
    lq = local.get(k)
    if not lq:
        mismatch.append((k[0][:40], "手元に無い設問(設問文か選択肢が違う)"))
        continue
    if q.get("choices") != lq["choices"]:
        mismatch.append((k[0][:40], "選択肢の順序が不一致"))
    elif str(q.get("answer")) != lq["answer"]:
        mismatch.append((k[0][:40], f"answer 不一致 本番={q.get('answer')} 手元={lq['answer']}"))
    elif q.get("explanation") != lq["explanation"]:
        mismatch.append((k[0][:40], "解説が不一致"))
    elif q["choices"][int(q["answer"])] not in q["explanation"]:
        mismatch.append((k[0][:40], "解説が正解テキストを含まない"))
print(f"[4] 本番データ vs 手元 flat.json: 不一致 {len(mismatch)}件")
for s, why in mismatch[:10]:
    print(f"    {s}… {why}")
if mismatch:
    fail.append(f"本番と手元で {len(mismatch)}件 不一致")

print()
if fail:
    print("❌ 検証 NG")
    for f in fail:
        print("  -", f)
    sys.exit(1)
print("✅ 本番検証 すべてPASS")
