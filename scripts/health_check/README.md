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
| `r_grammar_unit_tags` | daigaku/r_grammar 全小問の unit/【単元】タグ存在 (週次プリント①単元一致選定の前提。cron result の unit_tag_picks/like_fallback_picks で①比率も監視) | 2026-08-18 導入。タグ無しの新規行は単元一致選定から無言で漏れ精度27%水準に劣化 |
| `stripe_webhook_events` | Stripe webhook endpoint の必須イベント購読(opt-in: STRIPE_SECRET_KEY がある時だけ) | LIVE endpoint に payment_intent.succeeded/payment_failed/canceled が未購読で、3DS完了・キャンセル等の自動反映ハンドラが本番で無音不発 (2026-07-02 実測) |

## 定期実行(任意)

日次で回すなら cron / GitHub Actions から `--json` 出力を保存し、FAIL 時に通知。
`deploy_freshness` は push 直後は一時的に FAIL(Vercel 反映まで数秒)になり得るので、
デプロイ直後の実行では数十秒おいてから判定すること。

## 回帰テスト (`test_*.py`) — 自動配信・お知らせ・取込 (2026-10-15)

`test_*.py` は本番には触れない回帰テスト (一時 SQLite・`DATABASE_URL=''`)。CI は `.github/workflows/server-tests.yml`。
手元では `python3 scripts/health_check/<ファイル>` (exit 0 = PASS)。
ここには 2026-10-15 の自動配信の見直し (CLAUDE.md「🗺️ 自動配信の全体図」) と週次レポートの二重送信防止で足した分だけを書く (ほかは server-tests.yml の各 step のコメントを見る)。
「JS」の付いたテストは画面の本物のコードを JS エンジン (CI は node・Mac は osascript / jsc) で動かし、エンジンが無ければ FAIL する。

| テスト | 何を見るか |
|---|---|
| `test_weekly_worksheet_stop.py` | 日曜の週次弱点プリントの停止 (`WEEKLY_WORKSHEET_ENABLED`・既定 停止): 起動時に登録しない・監視の表から外す・今すぐ生成は 409・mypage の「終了しました」・📚 履歴は消さない (今週のプリントが無くても 📚 履歴 を押せる = mypage の本物のコードを JS で動かす) |
| `test_homework_notify_in_app.py` | 宿題・ドリルのお知らせ: 宿題の LINE は 0 回・メールは塾長の配信 (`source='manual'`) だけ (`HOMEWORK_NOTIFY_EMAIL`)・リンクは AIなし = `class.html?tab=homework` / AIあり = `mypage.html?focus=homework`・'assigned' も未提出・ログインコードの LINE と AIなし枠の許可集合は不変 |
| `test_hw_notice_js.py` (JS) | アプリ内の「🆕 新しい宿題 N 件」: hw-notice.js の数え方と「見た」の記録 (端末ごと・72 時間)・塾生アプリの帯と `?tab=homework`・マイページのチップ |
| `test_grade_band_consistency.py` (JS・無ければソースの突き合わせ) | 学年の判定 (「中２」「中三」も中学): サーバの `_student_grade_band`・student-mode.js・ceo.html の `_gdMode` が同じ答え・student-mode.js の `?v=` がそろっている |
| `test_auto_delivery_shared.py` | 自動配信の共通部品: レビュー済みの出典の許可リスト (シードの分類を固定)・習熟度テストの禁止・弱点 → 単元・学年の区分と科目・AI の振り分け (1 人 1 経路)・既出の除外・在庫照会 API・実行記録の要約 |
| `test_weakness_routine_auto_delivery.py` (JS は [10]) | 🎯 3日ドリル: レビュー済みだけ・中高の取り違えなし (選ぶときと書く直前)・dry-run と本番が同じ問題・監視・競合・LINE 0 回。[10] は CEO の配信済み一覧の絞り込みと 🎯 カード。[11] は 2026-10-16 の塾長決定 (3 日は JST の日付で・14 日より前の未提出は積まない判定に数えない (`WEAKNESS_ROUTINE_OPEN_STALE_DAYS`・古いドリルは消さない)・錠の中の読み直しも同じ境目・予約タスクの行は数えない) |
| `test_self_issued_drill_band.py` | 生徒が自分で始める今日の1問・初回診断: 学年で科目を分ける (小学生モードは 409)・レビュー済みだけ |
| `test_class_homework_routine.py` (JS は [14]) | 🏫 クラス自動宿題: クラスの表 = 時間割・AIなしの通塾生だけ (3日ドリルと合わせて 1 人 1 経路)・中高の取り違えなし・2 日に 1 本・未提出なら積まない・前の日のドリルには足さない (〆 はいつも受け取った日 + 2 日)・2 クラスの生徒はドリルを作る日がずれても両方が交互に届く・単元の選び方・LINE 0 回・`CLASS_HW_AUTO_ONLY_CLASSES` の打ち間違いは 0 クラス + error。[14] は CEO の 🏫 カードと塾生アプリのカードの 〆 |
| `test_weekly_report_dedup.py` | 週次レポートの二重送信防止: 日曜 19:00 の本命と 20:05 の予備で、生徒メール・保護者メール・LINE をそれぞれ 6 日 dedup・AI コメントは dedup の後・失敗行は止めない・上限 80 は不変・send-one は dedup しない・全員が送り済みの回を断絶と誤報しない・予備スクリプトの表示 |
| `test_english_long_drill.py` | 英語長文 (`english_long`) の取込 API: 本文型だけ・盲検の記録 (review) 必須・dry_run / all_or_nothing・set_id ごとの照合・配信と自動配信の範囲 |
| `test_proficiency_test_import.py` | 習熟度テスト (`proficiency_test`): 取込 (送る形は `scripts/drill_import/import_drill_file.py` の `build_payloads`)・全大問を出題順・同じ生徒に 2 回配らない・弱点と自動配信に入らない。[13] で `scripts/drill_import/fixtures` を取込スクリプトで試運転 → `--apply` → 読み返し (通信は TestClient) し、全問の 1 始まり → 0 始まりを照合。[14] で画面 (CEO ① 科目・④・学年の確認・配信 / 塾生アプリとマイページのカード) の本物のコードを JS エンジンで動かす (無ければ FAIL) |
| `test_drill_import_parity.py` | 取込の検査・取込スクリプト (デスクトップの `_tools/` で単体で動かす) に写したサーバの単元表が `server/main.py` と同じか・出典の形・Python 3.9 の標準ライブラリだけで `python3 -I` で動くか・取込スクリプトの安全装置・仕様書 11 章のコード |
