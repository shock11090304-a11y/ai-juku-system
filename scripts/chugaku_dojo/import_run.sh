#!/usr/bin/env bash
# 中学生プールの本番取込。★必ず `railway run -s ai-juku-api bash scripts/chugaku_dojo/import_run.sh` で実行
#   (CRON_SECRET を env から取得)。デプロイ(rotation登録)反映後に実行すること(逆順は invalid rotation で弾かれる)。
set -uo pipefail
API="${API_BASE:-https://trillion-ai-juku.com}/api/admin/exam-questions/import"
DIR="$(cd "$(dirname "$0")" && pwd)/batches/chunks"
: "${CRON_SECRET:?CRON_SECRET 未設定 (railway run -s ai-juku-api で実行してください)}"

tot_recv=0; tot_ins=0; tot_dup=0; tot_gate=0; tot_fail=0; nfiles=0
for f in "$DIR"/*.json; do
  [ -e "$f" ] || { echo "チャンク無し: $DIR"; exit 1; }
  nfiles=$((nfiles+1))
  resp=$(curl -sS -X POST "$API" -H "X-Cron-Secret: $CRON_SECRET" \
      -H "Content-Type: application/json" --data-binary @"$f" --max-time 170)
  # 集計 (python で JSON パース)
  read -r recv ins dup gate fail msg < <(python3 - "$resp" <<'PY'
import sys,json
try:
    d=json.loads(sys.argv[1])
    print(d.get("received",0), d.get("inserted",0), d.get("skipped_dup",0),
          d.get("gated_selfcheck",0), d.get("failed",0), (d.get("message","") or "").replace("\n"," "))
except Exception as e:
    print(0,0,0,0,-1, "PARSE_ERR:"+str(e)[:120])
PY
)
  tot_recv=$((tot_recv+recv)); tot_ins=$((tot_ins+ins)); tot_dup=$((tot_dup+dup))
  tot_gate=$((tot_gate+gate)); tot_fail=$((tot_fail+fail))
  printf "  %-28s recv=%s ins=%s dup=%s gate=%s fail=%s | %s\n" "$(basename "$f")" "$recv" "$ins" "$dup" "$gate" "$fail" "$msg"
  # 失敗があれば詳細を出す
  if [ "${fail:-0}" != "0" ]; then
    echo "$resp" | python3 -c 'import sys,json; d=json.load(sys.stdin); [print("      failed:",x) for x in (d.get("failed_details") or [])[:6]]' 2>/dev/null
  fi
done
echo "──────────────────────────────────────────"
echo "取込完了: files=$nfiles received=$tot_recv inserted=$tot_ins dup_skip=$tot_dup gated=$tot_gate failed=$tot_fail"
