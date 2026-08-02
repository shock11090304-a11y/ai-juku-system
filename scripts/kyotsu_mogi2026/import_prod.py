#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共通テスト模試 2026 の seed JSON を本番 (/api/admin/exam-questions/import) へ取り込む。

CRON_SECRET は環境変数から読む (引数に出さない)。
  railway run -s ai-juku-api python3 scripts/kyotsu_mogi2026/import_prod.py

引数なし … 英語 + 数学の両方を投入
  python3 scripts/kyotsu_mogi2026/import_prod.py eng    # 英語だけ
  python3 scripts/kyotsu_mogi2026/import_prod.py math   # 数学だけ
  python3 scripts/kyotsu_mogi2026/import_prod.py --dry-run   # 送らずに件数だけ表示

★投入前に必ず preflight.py を通すこと (rotation / 自己完結ゲート / 採点整合の事前確認)。
★import は同一 (exam_id, part_key, eiken_grade) + question_data 完全一致を skipped_dup で弾くので、
  二重実行しても重複は増えない。
"""
import os
import sys
import json
import time
import urllib.request
import urllib.error

API = "https://ai-juku-api-production.up.railway.app/api/admin/exam-questions/import"
CHUNK = 4          # 1 リクエストあたりの大問数 (既存 import_prod.py と同じ粒度)
RETRY = 4          # ネットワーク起因の失敗のみ指数バックオフで再試行

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
FILES = {
    "eng": os.path.join(ROOT, 'seed-data', 'kyotsu_mogi2026_eng_manual.json'),
    "math": os.path.join(ROOT, 'seed-data', 'kyotsu_mogi2026_math_manual.json'),
}


def post(chunk, secret):
    body = json.dumps({"questions": chunk, "skip_full": False}).encode("utf-8")
    req = urllib.request.Request(
        API, data=body, method="POST",
        headers={"Content-Type": "application/json", "x-cron-secret": secret})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode("utf-8"))


def post_with_retry(chunk, secret, label):
    delay = 2
    for attempt in range(RETRY + 1):
        try:
            return post(chunk, secret)
        except urllib.error.HTTPError as e:
            # HTTP エラーは内容が返るので再試行せず即座に出す (401/413/400 は再送しても同じ)
            print(f"  [{label}] HTTP {e.code}: {e.read().decode('utf-8')[:400]}")
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt >= RETRY:
                raise
            print(f"  [{label}] 通信失敗 ({type(e).__name__}) … {delay}s 後に再試行")
            time.sleep(delay)
            delay *= 2


def run(keys, dry_run):
    secret = os.environ.get("CRON_SECRET")
    if not secret and not dry_run:
        print("❌ CRON_SECRET 未設定。`railway run -s ai-juku-api python3 ...` で実行してください。")
        return 1

    grand = {"inserted": 0, "skipped_dup": 0, "gated": 0, "failed": 0}
    for key in keys:
        path = FILES[key]
        if not os.path.exists(path):
            print(f"❌ {os.path.relpath(path, ROOT)} が無い。先に build_{key}.py を実行してください。")
            return 1
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)["questions"]
        n_sub = sum(len(r["question_data"]["questions"]) for r in rows)
        print(f"\n=== {key}: {os.path.relpath(path, ROOT)} … {len(rows)} 大問 / {n_sub} 小問 ===")
        if dry_run:
            print("   (--dry-run のため送信しません)")
            continue

        for i in range(0, len(rows), CHUNK):
            chunk = rows[i:i + CHUNK]
            label = f"{key} chunk {i // CHUNK}"
            res = post_with_retry(chunk, secret, label)
            grand["inserted"] += res.get("inserted", 0) or 0
            grand["skipped_dup"] += res.get("skipped_dup", 0) or 0
            grand["gated"] += res.get("gated_selfcheck", 0) or 0
            grand["failed"] += res.get("failed", 0) or 0   # server は int を返す
            print(f"  [{label}] inserted={res.get('inserted')} skipped_dup={res.get('skipped_dup')} "
                  f"gated={res.get('gated_selfcheck')} failed={res.get('failed')} :: {res.get('message')}")
            if res.get("failed"):
                print("     failed_details:",
                      json.dumps(res.get("failed_details"), ensure_ascii=False)[:600])

    if not dry_run:
        print(f"\n=== 合計 inserted={grand['inserted']} / 重複skip={grand['skipped_dup']} / "
              f"自己完結NG={grand['gated']} / 失敗={grand['failed']} ===")
        if grand["gated"] or grand["failed"]:
            print("⚠️  gated / failed が 0 でない。preflight.py を通してから再実行すること。")
            return 1
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    dry = "--dry-run" in args
    args = [a for a in args if not a.startswith("--")]
    targets = args or ["eng", "math"]
    unknown = [a for a in targets if a not in FILES]
    if unknown:
        print(f"❌ 不明な指定: {unknown} (使えるのは eng / math)")
        sys.exit(1)
    sys.exit(run(targets, dry))
