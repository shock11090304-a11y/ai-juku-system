#!/usr/bin/env bash
# 🛡️ Vercel Hobby プランの Serverless Function 上限(12個)ガード。
#   api/*.py を 13個にすると Vercel デプロイ「全体」が失敗し、本番が前ビルドで凍結する
#   (新URL 404 / app.js が古いまま / gh の "Vercel" status=failure)。py_compile も vercel.json も
#   通るのに本番だけ落ちるため、過去3回(74e2c5fb/216d9ac/d59461f)診断に時間を要した。
#   → 新しい api/*.py を足す前にこのスクリプトで関数数を確認すること。13個目は CI で明確に失敗させる。
#
# 使い方: bash scripts/check_vercel_function_cap.sh   (12以下=exit 0 / 13以上=exit 1)
# 回避策(13個必要になったら): 新規 api/*.py を足さず、既存関数に ?__ep=<action> 等の action を同居させる
#   (例: vercel.json で /payment/api/admin-charge-month-end-preview → /api/admin-charge-readonly?__ep=preview)、
#   または read-only な GET を1本に統合して 12個に戻す。
set -euo pipefail

LIMIT=12
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$REPO_ROOT/api"

if [ ! -d "$API_DIR" ]; then
  echo "[vercel-cap] api/ ディレクトリが無いためスキップ (count guard 対象外)"
  exit 0
fi

# ★Vercel は api/ を「再帰」スキャンし handler を定義した各 .py を関数化する (公式: api/**/*.py)。
#   よって maxdepth で直下だけ数えると、サブディレクトリ(api/v2/foo.py 等)に置いた13個目を見逃し
#   CI緑のまま本番が凍結する偽陰性になる。配下全体を数え、関数化されない __init__.py のみ除外する。
COUNT="$(find "$API_DIR" -type f -name '*.py' ! -name '__init__.py' | wc -l | tr -d ' ')"

echo "[vercel-cap] api/*.py = ${COUNT} 個 (Vercel Hobby 上限 ${LIMIT})"

if [ "$COUNT" -gt "$LIMIT" ]; then
  echo ""
  echo "❌ [vercel-cap] Serverless Function が上限超過: ${COUNT} > ${LIMIT}"
  echo "   このまま push すると Vercel デプロイが全体失敗し、本番が前ビルドで凍結します。"
  echo "   対処: 新規 api/*.py を足さず、既存関数に action 同居 (vercel.json の rewrite + ?__ep=) で 12個に戻す。"
  echo "   現在の api/ 配下の .py (api/ からの相対パス):"
  find "$API_DIR" -type f -name '*.py' ! -name '__init__.py' | sed "s|^${API_DIR}/|     - |" | sort
  exit 1
fi

if [ "$COUNT" -eq "$LIMIT" ]; then
  echo "⚠️  [vercel-cap] 上限ぴったり(${LIMIT}/${LIMIT})。次に api/*.py を1個でも足すと本番が凍結します。新機能は既存関数へ action 同居で。"
fi

echo "✅ [vercel-cap] OK (${COUNT}/${LIMIT})"
exit 0
