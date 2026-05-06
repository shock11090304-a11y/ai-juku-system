#!/bin/bash
# 大学入試 5 問 バッチ投入スクリプト (3視点 team review 済)
# 使い方: CRON_SECRET=xxx ./import.sh
set -euo pipefail
JSON_FILE="${1:-$(dirname "$0")/daigaku_batch_v1.json}"
API="${API:-https://trillion-ai-juku.com}"
if [ -z "${CRON_SECRET:-}" ]; then
  echo "❌ CRON_SECRET 環境変数を設定してください"
  echo "   Railway Dashboard → ai-juku-system → Variables から取得"
  exit 1
fi
echo "📦 import: $JSON_FILE → $API/api/admin/exam-questions/import"
curl -sS -X POST "$API/api/admin/exam-questions/import" \
  -H "X-Cron-Secret: $CRON_SECRET" \
  -H "Content-Type: application/json" \
  --data "@$JSON_FILE"
echo ""
