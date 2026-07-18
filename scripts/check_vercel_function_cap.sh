#!/usr/bin/env bash
# 🧭 api/*.py 関数数のアーキテクチャガード (警告専用・非ブロッキング)。
#   2026-07-18 に Vercel を Hobby → Pro 化したため、旧「12個上限で13個目を足すと
#   デプロイ全体が失敗し本番が前ビルドで凍結する」問題 (Hobby 固有・過去3回事故:
#   74e2c5fb/216d9ac/d59461f) は解消済み。関数を足してもデプロイは落ちない。
#   ただしアーキテクチャ方針は不変:
#     - API ロジックは Railway 側の server/main.py に書く
#     - api/*.py は Stripe 等「Vercel でしか動けない」関数のみ (基準値 12個)
#   このスクリプトは基準値超過を警告するだけで常に exit 0 (CI をブロックしない)。
#
# 使い方: bash scripts/check_vercel_function_cap.sh   (常に exit 0 / 基準値超過で警告表示)
set -euo pipefail

BASELINE=12
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$REPO_ROOT/api"

if [ ! -d "$API_DIR" ]; then
  echo "[vercel-fn] api/ ディレクトリが無いためスキップ"
  exit 0
fi

# ★Vercel は api/ を「再帰」スキャンし handler を定義した各 .py を関数化する (公式: api/**/*.py)。
#   サブディレクトリ(api/v2/foo.py 等)も1関数として数えるため配下全体をカウントし、
#   関数化されない __init__.py のみ除外する。
COUNT="$(find "$API_DIR" -type f -name '*.py' ! -name '__init__.py' | wc -l | tr -d ' ')"

if [ "$COUNT" -gt "$BASELINE" ]; then
  # GitHub Actions 上では ::warning:: が commit / PR に annotation 表示される (ブロックはしない)
  echo "::warning title=api function count::api/*.py が ${COUNT} 個 (基準 ${BASELINE})。API ロジックは server/main.py (Railway) へ。api/*.py は Stripe 等 Vercel 専用のみ。"
  echo "   現在の api/ 配下の .py (api/ からの相対パス):"
  find "$API_DIR" -type f -name '*.py' ! -name '__init__.py' | sed "s|^${API_DIR}/|     - |" | sort
  echo "⚠️  [vercel-fn] api/*.py = ${COUNT} 個 > 基準 ${BASELINE} — Pro プランなのでデプロイは落ちないが、方針上 API ロジックは server/main.py へ (このチェックは警告のみ・exit 0)"
  exit 0
fi

echo "✅ [vercel-fn] api/*.py = ${COUNT} 個 (基準 ${BASELINE} 以内。Pro プランのため関数数による凍結リスク自体は無し)"
exit 0
