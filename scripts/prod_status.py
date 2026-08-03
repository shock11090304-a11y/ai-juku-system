#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本番の定期実行 (スケジューラ) が生きているかを **読むだけ** で確認する。

【なぜ要るか】
週次レポートは 2 経路で起動される:
  1. Railway の API プロセス内スケジューラ … 毎週日曜 JST 19:00 (本命)
  2. 外部 cron サービス                    … 毎週日曜 JST 20:00 (予備)
2 が「失敗」と表示されても、1 が動いていればレポートは出ている。
逆に 1 が止まっていれば、2 が成功していても中身は空振りしうる。
この切り分けは events テーブルを見ないとできないが、それには DB 端末が要る。

同じ判定は scripts/health_check/prod_healthcheck.py が持っている。あちらは
Postgres へ直接つなぐので `railway run -s Postgres` が必要。こちらは HTTP
だけで済むので GitHub Actions から実行でき、端末が無くても状態が読める。

【読むだけ】
呼ぶのは以下の 2 つで、どちらも DB を書き換えない:
  GET  /api/admin/scheduler/status          … 各スケジューラの最終実行
  POST /api/cron/weekly-reports?dry_run=true … 「送るとしたら誰に何通か」の試算
                                               (dry_run は送信も記録もしない)

【使い方】
  python3 scripts/prod_status.py --token "$CRON_SECRET"
  python3 scripts/prod_status.py --token "$ADMIN_TOKEN" "$CRON_SECRET"   # 複数可
"""
import argparse
import json
import sys
import urllib.error
import urllib.request

API = 'https://ai-juku-api-production.up.railway.app'

# 認証情報の「値」と「ヘッダへの載せ方」の組み合わせを総当たりする。
# 401 のとき値が違うのか載せ方が違うのかを切り分けられないと手が止まるため。
AUTH_MODES = [
    ('x-cron-secret のみ', lambda c: {'X-Cron-Secret': c}),
    ('Bearer のみ', lambda c: {'Authorization': f'Bearer {c}'}),
    ('Bearer + x-cron-secret', lambda c: {'Authorization': f'Bearer {c}', 'X-Cron-Secret': c}),
]


def _call(url, headers, method='GET', timeout=120):
    req = urllib.request.Request(url, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8') or '{}')


def probe_auth(creds):
    """通る (認証情報 × 載せ方) を実際に試して確定する。通らなければ None。"""
    url = f'{API}/api/admin/scheduler/status'
    tried = []
    for ci, cred in enumerate(creds, start=1):
        if not cred:
            continue
        for name, fn in AUTH_MODES:
            label = f'値{ci} / {name}'
            try:
                status, body = _call(url, fn(cred))
                if status == 200:
                    print(f'認証: 「{label}」で通りました\n')
                    return cred, fn, body
                tried.append(f'{label} → HTTP {status}')
            except urllib.error.HTTPError as e:
                tried.append(f'{label} → HTTP {e.code}')
            except Exception as e:
                tried.append(f'{label} → {type(e).__name__}: {e}')
    print('❌ 認証に失敗しました。試した組み合わせ:')
    for t in tried:
        print(f'    {t}')
    print('\n  404 が並ぶ場合は、この確認用ルートがまだ本番へデプロイされていません')
    print('  (main へ merge → Railway のデプロイ完了を待ってから再実行してください)。')
    print('  401 が並ぶ場合は、渡した値が本番の CRON_SECRET と一致していません。')
    return None, None, None


def _pad(s, width):
    """全角を 2 桁として数えて右詰めする (str.ljust は全角を 1 桁と数えるので桁が揃わない)。"""
    import unicodedata
    w = sum(2 if unicodedata.east_asian_width(ch) in 'WF' else 1 for ch in s)
    return s + ' ' * max(0, width - w)


def show_schedulers(body):
    print('=' * 62)
    print(f"定期実行の生存確認  (現在 {body.get('now_jst', '?')})")
    print('=' * 62)
    label = {
        'weekly_reports_run': '週次レポート (日曜19時)',
        'weekly_worksheet_run': '週次弱点プリント (日曜5時)',
        'weakness_aggregation_run': '弱点集計 (毎日)',
        'trial_mgmt_run': '体験フォロー (毎日)',
        'daily_sns_post': 'SNS 投稿 (毎日)',
    }
    for s in body.get('schedulers', []):
        name = label.get(s['name'], s['name'])
        if s.get('last_run_jst'):
            age = s.get('age_hours')
            when = f"{s['last_run_jst']} ({age:.0f}時間前)" if age is not None else s['last_run_jst']
        else:
            when = s.get('error') or '記録なし'
        mark = '⚠️ ' if s.get('stale') else '✅ '
        print(f'  {mark}{_pad(name, 30)} {when}')
        err = (s.get('props') or {}).get('error')
        if err:
            print(f'      └ 直近の実行でエラー: {str(err)[:160]}')
    print()
    print(f"週次レポートの判定: {body.get('weekly_report_verdict', '不明')}")
    print()


def show_weekly_dryrun(cred, fn):
    """「いま送るとしたら誰に何通か」を試算する (送信も記録もしない)。"""
    print('=' * 62)
    print('週次レポートの配信対象 (試算・実際には送りません)')
    print('=' * 62)
    url = f'{API}/api/cron/weekly-reports?dry_run=true'
    try:
        status, body = _call(url, fn(cred), method='POST', timeout=180)
    except urllib.error.HTTPError as e:
        print(f'  照会失敗: HTTP {e.code}')
        return
    except Exception as e:
        print(f'  照会失敗: {type(e).__name__}: {e}')
        return
    previews = body.get('previews') or []
    to_student = sum(1 for p in previews if p.get('student_copy_to'))
    to_parent = sum(1 for p in previews if p.get('parent_copy_to'))
    to_line = sum(1 for p in previews if p.get('would_send_line'))
    print(f"  配信対象の生徒     : {len(previews)} 名")
    print(f"  うち生徒本人へメール: {to_student} 名")
    print(f"  うち保護者へメール  : {to_parent} 名")
    print(f"  うち LINE 配信      : {to_line} 名")
    print(f"  今週活動なしでスキップ: {body.get('skipped', '?')} 名")
    if not previews:
        print('\n  ⚠️ 配信対象が 0 名です。今週まだ誰も学習していないか、')
        print('     集計ソースが切れている可能性があります。')
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--token', nargs='+', required=True,
                    help='CRON_SECRET / 管理トークン (複数可・通るものを自動選択)')
    args = ap.parse_args()

    cred, fn, body = probe_auth(args.token)
    if cred is None:
        return 1
    show_schedulers(body)
    show_weekly_dryrun(cred, fn)
    if body.get('any_stale'):
        print('⚠️ 「記録なし」「◯時間前」が想定周期より古い項目があります。')
        print('   そのスケジューラは停止している可能性があります。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
