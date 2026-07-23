#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""payload.json を本番 (/api/admin/exam-questions/import) へ投入。
実行: railway run -s ai-juku-api python3 scripts/eiken_nijikai_gp1/import_prod.py
  → CRON_SECRET を env から読む (ログに出さない)。ROTATION 反映後に実行すること
  (未反映だと invalid rotation で全 failed)。model タグで rollback 可 (purge --model)。
"""
import json, os, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://ai-juku-api-production.up.railway.app/api/admin/exam-questions/import"
SECRET = os.environ.get("CRON_SECRET")
if not SECRET:
    sys.exit("❌ CRON_SECRET が env に無い。`railway run -s ai-juku-api python3 ...` で実行して。")

payload = json.load(open(os.path.join(HERE, "payload.json"), encoding="utf-8"))
body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(
    API, data=body, method="POST",
    headers={"Content-Type": "application/json; charset=utf-8", "X-Cron-Secret": SECRET},
)
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        res = json.loads(r.read().decode("utf-8"))
        print("HTTP", r.status)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        if res.get("failed"):
            print("\n⚠️ failed あり — 上の failed_details を確認 (invalid rotation ならデプロイ未反映)")
            sys.exit(2)
except urllib.error.HTTPError as e:
    print("HTTP ERROR", e.code)
    print(e.read().decode("utf-8", "replace"))
    sys.exit(1)
