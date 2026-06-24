#!/usr/bin/env python3
"""共テ英語2026 類似問題を本番プールへ取込 (チャンク分割)。

実行: railway run -s ai-juku-api python3 scripts/eng_kyotsu_2026/import_chunks.py
  - CRON_SECRET は env から読む (秘密は露出しない)。
  - 4 大問/リクエストに分割 (一括は90秒timeoutの実績・kyotsu-drill-pool-import-recipe)。
  - dedup は server 側 content hash で安全 (再実行で既存skip)。
  - 自己完結ゲート(Layer A常時 + Layer B EXAM_IMPORT_VERIFY_AI=1)で弾かれた数も集計。
"""
import json, os, sys, urllib.request, urllib.error, time

URL = 'https://trillion-ai-juku.com/api/admin/exam-questions/import'
DEFAULT_SEED = os.path.join(os.path.dirname(__file__), '..', '..', 'seed-data', 'dojo_eng_kyotsu2026_manual.json')
CHUNK = 4

def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SEED
    secret = os.environ.get('CRON_SECRET')
    if not secret:
        print('!! CRON_SECRET が env にありません。railway run -s ai-juku-api 経由で実行してください。')
        sys.exit(1)
    print('seed:', os.path.basename(seed))
    rows = json.load(open(seed))['questions']
    print(f'取込対象: {len(rows)} 大問 / {sum(len(r["question_data"]["questions"]) for r in rows)} 小問')
    tot = {'inserted': 0, 'skipped_full': 0, 'skipped_dup': 0, 'failed': 0, 'gated_selfcheck': 0}
    fails = []
    for i in range(0, len(rows), CHUNK):
        cn = i//CHUNK+1
        chunk = rows[i:i+CHUNK]
        body = json.dumps({'questions': chunk}, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(URL, data=body, method='POST', headers={
            'Content-Type': 'application/json',
            'X-Cron-Secret': secret,
        })
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                d = json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            print(f'  chunk {cn}: HTTP {e.code} {e.read()[:300]!r}')
            tot['failed'] += len(chunk); fails.append((cn, f'HTTP {e.code}')); continue
        except Exception as e:
            print(f'  chunk {cn}: {type(e).__name__}: {e}')
            tot['failed'] += len(chunk); fails.append((cn, str(e))); continue
        for k in tot:
            v = d.get(k, 0)
            tot[k] += v if isinstance(v, int) else 0
        det = d.get('failed_details') or []
        print(f'  chunk {cn}/{(len(rows)+CHUNK-1)//CHUNK}: '
              f"inserted={d.get('inserted')} skip_full={d.get('skipped_full')} "
              f"dup={d.get('skipped_dup')} gated={d.get('gated_selfcheck')} failed={d.get('failed')}")
        for de in det:
            print('      detail:', de)
            fails.append((cn, de))
        time.sleep(0.5)
    print('\n=== 合計 ===')
    print(tot)
    if fails:
        print(f'\n失敗/詳細 ({len(fails)}):')
        for cn, reason in fails[:40]:
            print('  chunk', cn, reason)

if __name__ == '__main__':
    main()
