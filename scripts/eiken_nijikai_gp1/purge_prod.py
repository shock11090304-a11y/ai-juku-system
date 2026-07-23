#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本番 exam_questions から model タグ指定で一括削除 (rollback / 修正版の再取込前クリア用)。
実行: railway run -s ai-juku-api python3 scripts/eiken_nijikai_gp1/purge_prod.py <model_tag>
  CRON_SECRET は env から読む。purge は model filter 指定時のみ CRON_SECRET 許可 (誤爆防止)。
"""
import json, os, sys, urllib.request, urllib.error

API = "https://ai-juku-api-production.up.railway.app/api/admin/exam-questions/purge"
SECRET = os.environ.get("CRON_SECRET")
if not SECRET:
    sys.exit("❌ CRON_SECRET が env に無い。`railway run -s ai-juku-api python3 ...` で実行して。")
if len(sys.argv) < 2 or not sys.argv[1].strip():
    sys.exit("usage: purge_prod.py <model_tag>")
model = sys.argv[1].strip()

body = json.dumps({"model": model}).encode("utf-8")
req = urllib.request.Request(API, data=body, method="POST",
                             headers={"Content-Type": "application/json", "X-Cron-Secret": SECRET})
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        print("HTTP", r.status)
        print(json.dumps(json.loads(r.read().decode("utf-8")), ensure_ascii=False, indent=2))
except urllib.error.HTTPError as e:
    print("HTTP ERROR", e.code); print(e.read().decode("utf-8", "replace")); sys.exit(1)
