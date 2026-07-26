# ai-juku 本番 健全性チェック

`prod_healthcheck.py` — READ-ONLY・決定的(LLM不要)の本番点検ツール。
2026-07-02 の多視点監査で「見つかったが自動では気づけていなかった」バグ群を、
今後は毎回・機械的に検出するための常設ハーネス。

## 使い方

```bash
# 静的/APIチェックのみ(DB不要・どこでも実行可)
python3 scripts/health_check/prod_healthcheck.py --static-only

# DBチェックも含める(本番Postgresへ read-only 接続)
railway run -s Postgres python3 scripts/health_check/prod_healthcheck.py

# JSON出力(CI/cronで集計する場合)
railway run -s Postgres python3 scripts/health_check/prod_healthcheck.py --json

# Stripe webhook 購読検査も含める(opt-in: STRIPE_SECRET_KEY があるときだけ・READ-ONLY GET)
# 鍵が無い場合は「スキップ (鍵なし)」の WARN 1行で明示される(失敗にはならない)
STRIPE_SECRET_KEY="$(railway variables -s ai-juku-api --kv | sed -n 's/^STRIPE_SECRET_KEY=//p')" \
    railway run -s Postgres python3 scripts/health_check/prod_healthcheck.py
```

FAIL が1件でもあれば終了コード 1(WARN のみ/全PASS は 0)。
鍵なしの通常運用では `stripe_webhook_events` が常に WARN 1件(スキップ表示)残るので、
CI/cron の判定は**終了コード / FAIL 件数**で行うこと(`WARN>0` で発報すると常時鳴る)。

## チェック項目と、対応する過去のバグ

| section | 何を見るか | 元になった実バグ |
|---|---|---|
| `api_health` | /api/health と主要公開ページの 200 + サーバの混み具合(処理枠)・DB接続プールの状態 | 死活の基本。2026-07-26 の 502 事故(イベントループ停止で全API待ち)の予兆を、200 が返るうちに掴むため |
| `deploy_freshness` | git HEAD と本番配信の md5 一致 | ビルド凍結/デプロイ未反映で本番が古いまま (旧Hobby時代は12関数上限が主因・2026-07-18 Pro化で上限は解消) |
| `vercel_cap` | api/*.py が基準値(12)以内か (Pro化後は警告のみ・超過してもFAILしない) | 旧Hobby時代: 13個目でデプロイ全体失敗 |
| `subject_canonical` | 非canonical な subject の混入 | 日本語ラベル保存で弱点集計/CEO科目配信が空振り |
| `orphan_rows` | 削除済み生徒を参照する活動行 | KPI水増し・ゾンビ assignment |
| `drill_stored_live` | ドリルの「N問」表記 vs 実出題(active=1) | 無効化問題参照で 10問→9問のズレ |
| `answer_bias` | 直近取込問題の正解位置偏り | 取込前ラウンドロビン均等化漏れ |
| `weekly_report` | 週次レポートが全生徒スキップでないか | 集計ソース断絶で無音no-op(一度も配信されず) |
| `monitor_storm` | 監視アラートの誤発報ストーム | login_rate 誤発報で本物の critical が埋没 |
| `scheduler_live` | in-process スケジューラの最終実行 | cron 停止の検知 |
| `stripe_webhook_events` | Stripe webhook endpoint の必須イベント購読(opt-in: STRIPE_SECRET_KEY がある時だけ) | LIVE endpoint に payment_intent.succeeded/payment_failed/canceled が未購読で、3DS完了・キャンセル等の自動反映ハンドラが本番で無音不発 (2026-07-02 実測) |

## 定期実行(任意)

日次で回すなら cron / GitHub Actions から `--json` 出力を保存し、FAIL 時に通知。
`deploy_freshness` は push 直後は一時的に FAIL(Vercel 反映まで数秒)になり得るので、
デプロイ直後の実行では数十秒おいてから判定すること。
