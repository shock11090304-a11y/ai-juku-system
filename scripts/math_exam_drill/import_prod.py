#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""math_exam_daimon_v1.json を本番(/api/admin/exam-questions/import)へ4大問ずつ取込。
CRON_SECRET は環境変数から(引数に出さない)。`railway run -s ai-juku-api python3 ...` で実行。"""
import os, sys, json, urllib.request, urllib.error

API = "https://ai-juku-api-production.up.railway.app/api/admin/exam-questions/import"
SECRET = os.environ.get("CRON_SECRET")
assert SECRET, "CRON_SECRET 未設定"

here = os.path.dirname(__file__)
fname = sys.argv[1] if len(sys.argv) > 1 else "math_exam_daimon_v1.json"
data = json.load(open(os.path.join(here, fname), encoding="utf-8"))
print(f"file: {fname}")
rows = data["questions"]
print(f"取込対象: {len(rows)} 大問")

def post(chunk):
    body = json.dumps({"questions": chunk, "skip_full": False}).encode("utf-8")
    req = urllib.request.Request(API, data=body, method="POST",
                                 headers={"Content-Type": "application/json", "x-cron-secret": SECRET})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))

total_ins = 0
for i in range(0, len(rows), 4):
    chunk = rows[i:i+4]
    try:
        res = post(chunk)
    except urllib.error.HTTPError as e:
        print(f"[chunk {i//4}] HTTP {e.code}: {e.read().decode('utf-8')[:300]}")
        raise
    total_ins += res.get("inserted", 0)
    print(f"[chunk {i//4}] inserted={res.get('inserted')} skipped_dup={res.get('skipped_dup')} "
          f"gated={res.get('gated_selfcheck')} failed={res.get('failed')} :: {res.get('message')}")
    if res.get("failed"):
        print("  failed_details:", json.dumps(res.get("failed_details"), ensure_ascii=False)[:500])
print(f"=== 合計 inserted = {total_ins} ===")
