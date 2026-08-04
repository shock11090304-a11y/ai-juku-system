#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""週次レポートの配信を外部から起動する (Railway cron サービス用)。

【なぜ curl ではないのか】
Railway の cron サービス ai-juku-weekly-reports は
    curl -X POST -H "X-Cron-Secret: $CRON_SECRET" .../api/cron/weekly-reports
を実行する設定になっていたが、コンテナは Python アプリとしてビルドされていて
**curl が入っていない**。2026-08-02 の実行ログ:

    2026-08-02 20:00:42  Starting Container
    2026-08-02 20:00:43  /bin/bash: line 1: curl: command not found

このため 2026-06 以前から毎週 1 秒で失敗し続けていた (実行履歴は全て赤)。
本命は server/main.py の _weekly_reports_scheduler (API プロセス内・日曜 19:00) なので
配信自体は届いていたが、予備は 2 か月以上まったく機能していなかった。

標準ライブラリの urllib だけで書けば、追加インストール無しでどのコンテナでも動く。

【二重送信にはならない】
/api/cron/weekly-reports は notifications テーブルで週次 dedup している
(同一生徒に同テンプレートで 7 日以内に成功送信済みならスキップ)。
本命が 19:00 に送り終えていれば、20:00 のこの呼び出しは 0 件送信で終わる。
本命が動かなかった週だけ、ここが実際に配信する = 予備として働く。

【使い方】
Railway の cron サービスの start command をこれに変える:

    python3 scripts/trigger_weekly_reports.py

環境変数:
    CRON_SECRET     必須。API 側と同じ値。
    API_BASE_URL    省略可。既定は本番 API。
    DRY_RUN=1       省略可。送信せず対象人数だけ出す (動作確認用)。

終了コード: 0 = 成功 / 1 = 設定不足 / 2 = API がエラーを返した・到達できない
"""
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_API = 'https://ai-juku-api-production.up.railway.app'


def main():
    secret = (os.getenv('CRON_SECRET') or '').strip()
    if not secret:
        print('❌ CRON_SECRET が未設定です。Railway のサービス変数を確認してください。',
              file=sys.stderr)
        return 1

    base = (os.getenv('API_BASE_URL') or DEFAULT_API).rstrip('/')
    dry = os.getenv('DRY_RUN', '').strip() not in ('', '0', 'false', 'False')
    url = f'{base}/api/cron/weekly-reports' + ('?dry_run=true' if dry else '')

    req = urllib.request.Request(url, method='POST',
                                 headers={'X-Cron-Secret': secret})
    try:
        # 60 名分の AI コメント生成 + メール送信で数分〜十数分かかることがある。
        # curl の既定より長めに取らないと、成功しているのに timeout で失敗扱いになる。
        with urllib.request.urlopen(req, timeout=1800) as resp:
            body = resp.read().decode('utf-8', 'replace')
            status = resp.status
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', 'replace')[:300]
        print(f'❌ HTTP {e.code} {e.reason}\n{detail}', file=sys.stderr)
        if e.code == 401:
            print('   CRON_SECRET が API 側の値と一致していません。', file=sys.stderr)
        return 2
    except Exception as e:
        print(f'❌ {type(e).__name__}: {e}', file=sys.stderr)
        return 2

    try:
        data = json.loads(body or '{}')
    except Exception:
        print(f'HTTP {status} (JSON として読めない応答): {body[:300]}')
        return 0 if status == 200 else 2

    if dry:
        previews = data.get('previews') or []
        print(f'✅ 確認のみ (送信していません): 配信対象 {len(previews)} 名 / '
              f'活動なしスキップ {data.get("skipped", "?")} 名')
        return 0

    print(f'✅ 週次レポート配信: メール {data.get("sent_email", 0)} 件 / '
          f'LINE {data.get("sent_line", 0)} 件 / スキップ {data.get("skipped", 0)} 名 / '
          f'失敗 {data.get("failed", 0)} 件')
    # 本命が先に送り終えていれば 0 件になる。それは異常ではないので成功扱い。
    if data.get('failed'):
        print(f'   ⚠️ {data["failed"]} 件が失敗しています。', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
