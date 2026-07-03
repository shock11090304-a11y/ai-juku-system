#!/usr/bin/env bash
# rotation 登録(main.py)が本番反映されたか確認。★`railway run -s ai-juku-api bash scripts/chugaku_dojo/confirm_deploy.sh`
#   pool-status に chugaku の5 part が現れれば = デプロイ反映済(取込を開始してよい)。
set -uo pipefail
BASE="${API_BASE:-https://trillion-ai-juku.com}"
: "${CRON_SECRET:?CRON_SECRET 未設定 (railway run -s ai-juku-api で実行)}"
resp=$(curl -sS "$BASE/api/admin/exam-questions/pool-status" -H "X-Cron-Secret: $CRON_SECRET" --max-time 60)
python3 - "$resp" <<'PY'
import sys,json
d=json.loads(sys.argv[1])
parts=d.get("parts",[])
chu=[p for p in parts if p.get("exam")=="chugaku"]
want={("chugaku","eng","koukou"),("chugaku","math","koukou"),("chugaku","kokugo","koukou"),("chugaku","rika","koukou"),("chugaku","shakai","koukou")}
have={(p.get("exam"),p.get("part"),p.get("grade")) for p in chu}
missing=want-have
print("rotation_size:",d.get("rotation_size"),"| chugaku parts in pool-status:",sorted(have))
if missing:
    print("❌ 未反映(まだデプロイ前 or 反映途中):", sorted(missing)); sys.exit(2)
print("✅ chugaku 5part すべて反映済み → 取込OK")
for p in sorted(chu, key=lambda x:x.get("part")):
    print(f"   {p.get('part'):7} count={p.get('count')}")
PY
