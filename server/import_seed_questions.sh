#!/bin/bash
# 🆓 Claude Max 経由生成の問題 JSON を一括 import するヘルパー
# 使い方: ./import_seed_questions.sh seed_questions_batch1.json
#
# CRON_SECRET は Railway 環境変数から取得 (railway CLI 必要)
# 使用例:
#   cd ~/ai-juku-system
#   ./server/import_seed_questions.sh server/seed_questions_batch1.json
#   ./server/import_seed_questions.sh server/seed_questions_batch*.json   # 全バッチ一括

set -euo pipefail

API_URL="${AI_JUKU_API:-https://ai-juku-api-production.up.railway.app}"

# CRON_SECRET 取得 (キャッシュ優先)
SECRET_CACHE="/tmp/ai_juku_cron_secret.txt"
if [ -f "$SECRET_CACHE" ] && [ -s "$SECRET_CACHE" ]; then
    CRON_SECRET=$(cat "$SECRET_CACHE")
else
    CRON_SECRET=$(railway variables --service ai-juku-api --kv 2>/dev/null | grep "^CRON_SECRET=" | cut -d= -f2-)
    if [ -z "$CRON_SECRET" ]; then
        echo "❌ CRON_SECRET 取得失敗。'railway login' して 'railway link' で ai-juku-api に紐付けてください。" >&2
        exit 1
    fi
    echo "$CRON_SECRET" > "$SECRET_CACHE"
fi

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <json_file> [json_file2 ...]" >&2
    exit 1
fi

TOTAL_INSERTED=0
TOTAL_FAILED=0

for FILE in "$@"; do
    if [ ! -f "$FILE" ]; then
        echo "⚠️  $FILE が存在しません (skip)" >&2
        continue
    fi
    echo "📥 importing: $FILE"
    RESPONSE=$(curl -sS -m 60 -X POST "$API_URL/api/admin/exam-questions/import" \
        -H "x-cron-secret: $CRON_SECRET" \
        -H "Content-Type: application/json" \
        --data-binary "@$FILE")
    INSERTED=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('inserted',0))" 2>/dev/null || echo "0")
    FAILED=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('failed',0))" 2>/dev/null || echo "0")
    echo "  ↳ inserted=$INSERTED failed=$FAILED"
    TOTAL_INSERTED=$((TOTAL_INSERTED + INSERTED))
    TOTAL_FAILED=$((TOTAL_FAILED + FAILED))
done

echo ""
echo "✅ 完了: 計 $TOTAL_INSERTED 問 import (失敗 $TOTAL_FAILED 問)"
