# ai-juku — プロジェクト指針 (Claude 用)

オンライン塾の受験生向け AI 学習 SaaS。公開: trillion-ai-juku.com

## 構成 / デプロイ
- **静的フロント** (Vercel): リポジトリ直下の `*.html` / `*.js` (mypage.html, dojo-drill.html, app.js, english-exam.js 等)。
- **バックエンド API** (Railway): `server/main.py` (巨大単一 FastAPI)。本番 = `https://ai-juku-api-production.up.railway.app`。
- **DB**: Postgres (Railway)。read-only 照会: `railway run -s Postgres python3 -c "import os,psycopg;c=psycopg.connect(os.environ['DATABASE_PUBLIC_URL'])..."`
- **決済**: Stripe。
- `main` への push で Vercel(静的) と Railway(API) が**両方自動デプロイ**。静的は数秒、API は ~1分。
- **DB接続プール**: `db()` は psycopg_pool(max_size=`DB_POOL_MAX`既定16・単一プロセス前提)。不具合時は env `DB_POOL_ENABLED=0` → 再起動で直接connectへ即フォールバック。★将来 `uvicorn --workers N` 化するなら 16×N が Postgres `max_connections`(現100) を超えないよう `DB_POOL_MAX` を絞ること。in-memory rate limiter (`_RATE_LIMIT_STORE`・curriculum 日次capなど) も per-process なので実効上限が N 倍に希釈される点に注意。
  - 取込API等は**デプロイ済みのコードを検証**するので、新 part/ルートを足したら「push→デプロイ反映確認→その後にデータ投入」の順を守る (逆順は無効扱いで弾かれる)。
- **起動時DDLとロック (2026-09-03「本番API 75分全停止」の再発防止)**: `init_db()` は import 時 (= uvicorn が port を bind する前) に無条件で走る。ここで詰まると healthcheck に到達できずデプロイが失敗し続ける。安全弁が4段ある。
  - ① `db()` が返す全接続に `idle_in_transaction_session_timeout` (既定600秒・env `DB_IDLE_TX_TIMEOUT`・0で無効)。放置された接続を Postgres 側で切る。
  - ② `init_db` **専用接続**に `lock_timeout` (既定10秒・env `DB_INIT_LOCK_TIMEOUT`・0で専用接続を張らず従来の無防備な経路に戻る)。プールから借りないので設定が他のリクエストに漏れない。
  - ③ `ALTER TABLE ADD COLUMN` の前に `information_schema` で列の存在を確認してスキップ。
  - ④ 起動時DDLに壁時計の締切 (既定20秒・env `DB_INIT_DDL_BUDGET`)。ロック1回ごとの上限だけでは合計時間に蓋ができないため。★計時はテーブル定義のまとめ実行から始まるが、**中断できるのは列追加ループの境界だけ** (まとめ実行は1本の巨大クエリなので途中で止められない) = 「必ず20秒で終わる」わけではない。
  - ★**③が本体**。`ALTER` は「列が既にある」と分かる**前に** ACCESS EXCLUSIVE を要求するので、定常状態でも起動のたびに students へ排他ロックを25本投げていた (57本すべてが no-op なのに)。students を読んでいる接続が1本あるだけで詰まる地雷だった。
  - ★**新しい `ALTER TABLE ... ADD COLUMN` を `_migrations` に足すときは「1文で1列だけ」を守ること**。`ADD COLUMN a …, ADD COLUMN b …` と複数列を1文に書くと、事前チェックの正規表現は**先頭の a にしかマッチしない**。a が既存だと文ごとスキップされ **b が永久に作られない**危険があった (2026-09-03 に「ADD COLUMN が2つ以上ある文は事前チェックしない」ガードを入れて塞いだが、1文1列を守るのが本筋)。schema修飾 `public.x` / 引用符 `"x"` は正規表現に合わず従来どおり実行されるので安全側 (`ADD COLUMN IF NOT EXISTS x` はマッチするが列名を "IF" と解釈するため既存列と一致せず、結局実行される = これも安全側)。
  - ★**`db()` の接続を掴んだまま AI/外部APIを待つコードを書かないこと**。①に切られる。AIを呼ぶ前に `conn.commit()` するか、`db()` を取る前に呼ぶ (`past_exam_upload` がこの理由で commit を挟んでいる)。
  - ★残る既知の弱点: `CREATE INDEX IF NOT EXISTS` (90本) も同じ構造で ShareLock を先に取る。ShareLock は通常の SELECT (AccessShareLock) とは衝突しないので 2026-09-03 型の「読み取りまで含む全停止」にはならない。ただし**書き込み中だと待たされ、`lock_timeout` で倒れると executescript は1トランザクションなので147文すべてがロールバックされる** = そのデプロイで増えたテーブル/インデックスが丸ごと未反映になり `init_ddl_skipped` に載る。「書き込みが遅れるだけ」では済まない。
  - ★既定値の正典は `server/main.py` の `_env_int("DB_...")` 行。この文書や `.env.example` と食い違ったらコードが正しい。
- **生徒に紐づくテーブルと削除の整合 (2026-09-04)**: `students` を外部キーで参照するのは `payments` / `referrals` だけで、他は削除時に自力で消さないと孤児化する。長らく削除APIが14テーブルしか消しておらず、合成監視も `students` 行だけ消していたため、孤児が30,388行溜まっていた (うち27,797行は5分ごとの監視が残す `otp_codes`)。
  - ★**生徒に紐づく新しいテーブルを足したら、`_ORPHAN_SWEEP_TABLES` と削除API (`admin_student_delete`) / `purge-stale-data` の cascade リストの3箇所すべてに足すこと**。1箇所でも漏れると同じ孤児化が再発する。
    ★正確には 5 か所 (削除のプレビュー `related_tables`・個別削除・purge・`_ORPHAN_SWEEP_TABLES`・統合 `_MERGE_STUDENT_TABLES`)。`scripts/health_check/check_student_cascade_lists.py` が正典 (init_db の DDL を読む)。
  - CEOダッシュの🧹ボタン (`purge-stale-data`) は、対象の生徒が0件でも「存在しない生徒を指す行」を掃除する。在籍生徒のデータには触れない (条件は `student_id NOT IN (SELECT id FROM students)`)。payload `{"orphans_only": true}` なら生徒本体は消さず孤児行だけ掃除する。
  - ★🧹ボタンの「対象の生徒」(合成監視 `@synthetic-monitor.*` / テスト系キーワード) には、**人手で作ったデモ用アカウントが紛れ込みうる** (2026-09-04 時点で `@synthetic-monitor.local` ドメインのデモ用アカウント6名・`course='kokuritsu_nankan'` 付き)。実行前の一覧で「監視 守」以外の名前が無いか必ず目視すること。★この文書に人名を書かない (公開リポジトリ)。
  - ★`course_applications` / `referrals` は sweep 対象外。申込・紹介の**履歴**なので行は残し、生徒削除時に `student_id` / `referrer_id` / `referred_id` を NULL にするだけ (削除ではない)。「生徒IDの列 (`student_id` / `referrer_id` / `referred_id`) を持つ表は全部 sweep に入れる」と誤解しないこと。★ダッシュの🧹ボタンは2段階確認: 1回目で孤児行の掃除 (常に安全)、2回目で「生徒本体も消すか」を明示的に選ぶ。2回目をキャンセルすると `orphans_only: true` で送られ生徒は残る。
  - ★`anthropic_usage_log` だけは消さず `student_id=NULL` にする。これは生徒のデータではなく**塾のAI利用コストの会計記録**で、CEOダッシュの残量予測が `SUM(cost_usd)` を参照している。消すと過去の費用が下がって見える。

## 本番APIが止まったとき (塾長向けランブック)
1. **まず `https://ai-juku-api-production.up.railway.app/api/health` を開く。**
   - `hint` と `init_ddl_hint` の日本語をそのまま読み、**書いてある指示どおりに動く**。
     ★対処の文面はこの文書に書き写さない (写すと片方だけ更新されて食い違う)。正典は `init_ddl_hint`。
   - ★JSON が読みにくければ、GitHub の Actions タブ →「本番に異常が出ていないか点検」→ Run workflow でも同じ内容が日本語で出る (ただし API が完全に落ちているときは health を直接開く方が速い)。

2. **health が返ってこない / デプロイが何度も失敗する場合** — 2026-09-03 の75分全停止がこれ。デプロイでコンテナを止めても Postgres 側に接続だけが残り、テーブルを掴んだまま起動時DDLを待たせていた。★**再デプロイだけでは直らない** (行列の根元が死んだ接続なので)。実際に再デプロイして同じく失敗した。

   **【塾長がやること】上から順に。1つやるごとに health を開き直す。**
   1. Railway で **ai-juku-api を Restart**。これが最も安全で速い。③の事前チェックにより、起動時DDLは詰まっても数秒〜20秒で諦めて起動する。
   2. **10分待つ**。放置された接続を切る上限が600秒 (①) なので自然復旧する見込みがある。**それより早く諦めて次に進まない**。
      ★ただし①は**接続を張るときに設定するもの**なので、この安全弁が入る前 (2026-09-03 以前) のコンテナが残した接続には効かない。その場合は待っても消えないので次へ進む。
   3. まだ直らないなら ⚠️ **Postgres サービスを Restart**（最終手段）。
      ★これは残った接続を全部切る代わりに、**数十秒〜数分、全生徒がアプリを使えなくなる**。書きかけの操作も中断される。授業中や演習のピーク時間帯は避けること。
      ★ai-juku-api ではなく **Postgres の方**。サービスを間違えないこと。
   4. ここまでで直らなければエンジニアに連絡。ここから先は塾長の作業ではない。

   **⚠️ Rollback はここでは使わない。** 「**直前にコードをデプロイした、その直後から壊れた**」ときだけの別手段。
   - Rollback すると①②③④の安全弁と `healthcheckTimeout=120` が**全部いっぺんに消え**、起動のたびに students へ排他ロックを25本投げる旧コードが復活する。ロックが原因の障害でこれをやると、「書き込みが遅い」程度で済んでいた状態を**読み取り含む全停止に悪化させうる**。
   - Rollback で復旧させた場合は、**原因を直したうえで必ず最新をデプロイし直す**こと。戻したままにすると地雷が再武装された状態で運用が続く。

   **【原因調査 (技術者向け)】**
   - `pg_stat_activity` + `pg_blocking_pids(pid)` で根元を特定し、**先に DDL 側 (ALTER/CREATE INDEX で待機中) を切る**。行列が解けて読み取りが即回復する。
   - ★**ただしこれは止血にすぎない**。根元の `idle in transaction` 残骸を切らない限り、次の起動でまた同じ場所に並ぶ。読み取りが戻ったことを確認してから根元を切る。`idle in transaction` を先に切るのは危険 (一般には未コミットの書き込みを捨てる)。切断前に必ず state・クエリ・放置秒数を照合すること (pid は使い回される)。
   - 詰まっている文の特定に `pg_stat_activity.query` を信用しないこと。`executescript` は147文を1つの文字列で送るため、表示は常に先頭の `CREATE TABLE IF NOT EXISTS students (` になる。**`pg_locks WHERE NOT granted` を見ること**。
   - Railway は各起動を最大120秒待ち (`healthcheckTimeout`)、5回失敗すると自動再試行をやめる (`restartPolicyMaxRetries`)。「何もしていないのに直らない」状態はこれ。

3. **DB接続プールを疑うとき**は env `DB_POOL_ENABLED=0` → 再起動で直接connectへ即フォールバック。★**直ったら必ず `1` に戻す (または変数を削除) → 再起動**。戻し忘れると点検で「DB接続プールが無効です」の警告が毎回出続ける。

## 🎥 月額講座 (英文解釈 ¥1,000/月・英文法 ¥1,500/月・共通テスト対策 ¥1,500/月) の視聴ページ (2026-09-16)
- 受講者は Stripe 支払いリンク (metadata.system=`juku-payment-course`) の顧客で、**`students` には入れない**。身元は `course_members` (メール単位)、
  正典は Stripe の有効サブスク。ログインはメール → リンク (token_type `coursemagic`) → セッション (`course`)。`_verify_session_token` の型が違うので
  塾生 API / ai_disabled ゲートとは混線しない。
- 動画は `course_videos` に **YouTube の ID だけ** 保存し、`/api/course/me` (認証必須) からしか出さない (リポジトリと配信ページは PUBLIC)。
  視聴ページ `course-videos.html` は youtube-nocookie の埋め込みを再生ボタンで遅延生成する (埋め込みからの ID 抽出は防げない = 塾長了承の案 A)。
- 塾長は CEO ダッシュ「🎥 月額講座」で登録。**登録と同時にその講座の有効受講者へ Resend でお知らせ** (`_course_notify_video`・視聴ページ URL のみ)。
  受講案内メール (決済直後) は Vercel `api/stripe-webhook.py` が送る (別系統)。
- 本体 webhook は `juku-payment*` を skip する前に `_course_webhook_touch` で `course_members` を同期し、決済完了時は視聴ページのログインリンクも送る (受講案内メールは Vercel)。students には触らない。
  `COURSE_WELCOME_ENABLED=0` は Vercel (受講案内) と Railway (ログインリンク) で別々に効くので、止めるなら両方に入れる。
  Stripe の支払いリンクは決済ごとに新しい Customer を作る → `_course_fetch_from_stripe` は customer_id とメール検索の顧客を合算する (2026-09-17)。
- テスト: `scripts/health_check/test_course_portal.py` (Stripe は `_course_fetch_from_stripe`、メールは `_course_send_email` を差し替え)。
- 📺 **再生リストから取り込む** (2026-10-05 塾長「サブスクの動画登録も再生リストと同じように」): CEO「🎥 月額講座」で講座ごとに再生リスト URL を保存
  (kv_settings `course_playlist:<講座>`) → 「① 確認する」(dry-run) → 「② この内容で登録」(`POST /api/admin/course/import`)。
  再生リストの読み取りは授業録画と同じ `class_recording_assign.fetch_playlist` (読めなかった講座を「新着 0 本」と言わない)。
  ★② は ① の `plan_token` と一致するときだけ登録 (間に再生リストが変わったら 1 本も入れない)。お知らせは**講座ごとに 1 人 1 通**
  (`_course_notify_import`・台帳 `course_video_notices` は動画ごと)。CEO で削除した動画は `course_import_skip:<講座>:<動画 ID>` (1 動画 1 行・ON CONFLICT DO NOTHING) に載り生き返らない。
  授業録画の再生リストかどうかは `_class_playlist_reason` に一本化: `admin_youtube_playlists` のうち 名前が曜日+限・名前なし・グループ (grp) 付き
  の行は授業録画とみなし講座に使わせない。塾長が一覧に自分で足した (grp 空) 曜日+限の無い名前の行は使える (塾長はあの一覧に講座の再生リストも
  並べる・2026-10-05)。① でその名前を出して確かめさせる。曜日+限の再生リストの中の動画 (クラス未割り当ての回も・100 本超えでも見えている分)・
  `class_recordings` の動画は講座に入れない。すぐ返ってきた読み損ねだけ 1 回読み直し (最大 4 本・+1 秒+15 秒まで)、授業録画の再生リストが
  それでも読めなければ**止めずに** `warnings` (黄色・② の確認にも出る) で題名の確認を求める (2026-10-05 本番で 1 本の一時的な読み損ねで全講座が止まった)。
  ① は貼っただけで保存していない URL を先に保存する。
  お知らせは講座をまたいで 1 本の流れで順に送る (講座ごとにスレッドを立てると `_email_rate_limit` の間隔が効かない)。
  ★名前に曜日+限の無い授業録画の再生リストの中身は見ていない (古い回は `class_recordings` で見る)。
  テスト: `scripts/health_check/test_course_playlist_import.py` (YouTube は `class_recording_assign.http_get` を差し替え)。
- 環境変数: `COURSE_DELIVERY_START` (配信開始日・Railway と Vercel を同じ日付に)、`COURSE_LINE_URL` (公式 LINE)、`COURSE_REPLY_TO` (窓口。Railway/Vercel 両方)、
  `COURSE_PORTAL_URL` (Vercel・視聴ページ URL)、`COURSE_NOTIFY_EMAIL` (Vercel・塾長通知。★未設定だと講座・入塾の要対応通知が一切届かない)。既定値は両ファイルに直書き。
- 🎓 体験授業 (taiken.html・¥1,500 支払いリンク `TAIKEN_TRIAL_PLINK_ID`・metadata 空) は students を作らない単発決済。本体 webhook の divert 分岐で
  塾長通知 (`_notify_admin_new_trial`・決済画面のカスタム欄を goal に) と申込者への案内メール (`_send_taiken_welcome_email`・`TAIKEN_WELCOME_ENABLED=0` で停止) を送る。
  テスト: `scripts/health_check/test_taiken_welcome_mail.py`。

## 🏫 入塾申込書からの初回カード決済 (2026-09-17・塾長決定: 初月受講料は満額 / 入塾金免除なし / 設備費は初回に含める)
- 入塾申込書 (Netlify `入塾書類/index.html`・別オリジン) → `POST /payment/api/register-subscribe` に `firstCharge:true` → **mode=payment** の Checkout
  (入塾金 `ENTRY_FEE` 10,000 + 設備費 + 各コース初月受講料・`setup_future_usage=off_session` でカード保存)。金額はサーバ側カタログのみ
  (`COURSES`/`OPTIONS` と `payment/courses.json` を `scripts/check_course_price_sync.py` で同期)。**入塾金は courses.json に入れない** (毎月請求になる)。
- **AI学習アプリ (月額 +5,000 円・2026-09-23)** はオプション `ai-app-5000` (`OPTIONS` / `courses.json`)。**国公立難関大学コース (`kokuritsu`) には無料で同梱**
  (academy.html の料金表) なので `_validate` が一緒に来た `ai-app-5000` を落とす (申込書側も `payment/register.html` も国公立を選ぶと欄が外れる)。
  同梱のときは内訳に「AI学習アプリ（国公立難関大学コースに同梱） ¥0」を残し、webhook のメールは AI学習アプリを受講料とは別の行 (`option_lines` / `options_label`) に出す。
  テスト A1h/A1i/A1j (aiAppIncluded)・A2x・A4g (do_POST→webhook の往復)・B1x。
- **コース名の 2 本立て (2026-09-23)**: `COURSES[id]["name"]` / `courses.json` の `name` は月謝アプリの名簿の正規名 (`payment/app.js` が名前で正規化・単価照合) なので**変えない**。
  保護者に見せる Stripe 明細・内訳 (`_calculate_fee` の breakdown)・確認メール・`payment/register.html` の表示は `label` (= 入塾申込書と同じ表示名)。`check_course_price_sync.py` が label も照合。
- **受講開始月 (2026-09-23 塾長決定「翌月のみ」)**: 申込書の必須ラジオ「今月から / 翌月から」→ `startMonth: current|next` → `register-subscribe.py` が JST の
  `start_month` (YYYY-MM) を metadata / pending / 応答に入れ、Stripe の明細・確認文を「◯月分」にする。webhook は `metadata.start_month` (無ければ pending の `start_month`) が決済月 (Checkout 作成の JST 月) かその翌月なら
  それを台帳の月にする (charge:done を翌月に書く → 26 日前後の「翌月分」バッチはその生徒を飛ばし、その次の月から引き落とし。メールも「翌月分」)。
  それ以外の値は無視して決済月。再来月以降は受け付けない。テスト A1m / A2e2 / A2y / A4h / A4i / B1w1〜B1w6。
  ★翌月開始の登録月には台帳の記録が無いので、**受講開始月より前の月は請求しない**を 3 か所で守る: 月末バッチ `_before_start_month`
  (今月分実行・滞納まとめ請求とも execute を通る)・`payment/app.js` の滞納判定の下限 `startMonth` (readonly が返す)・`past-due-invoice.py` (💳請求書)。
  webhook は台帳 (charge:done) を名簿より先に書く (26 日のバッチと同時でも二重にならない・テスト B1c2)。ガードのテストは test_monthend_ux。
  ★さらに「初回決済で払った月 (`first_charge_month`) は台帳の有無によらず請求しない」: execute `_paid_by_first_charge`・readonly (引き落とし済み扱い)・
  app.js (滞納候補から除外)。💳請求書 (`past-due-invoice.py` `_month_paid_by_card`) は初回決済の月と台帳に成功記録のある月を拒否
  (失敗履歴だけの月は出せる = 振込を頼む場面。charge:done が 3DS待ち/要確認 の月も出さない → 先に 🔧確定)。名簿の入金印が外れていても二重にならない。
  ★初回決済を返金したときは、その月は execute/請求書とも自動では請求できない (first_charge_month の印は消えない) → Stripe か reconcile の retry で手動対応。
- 特商法の通塾コース版は `legal.html#tokusho-juku` (入塾申込書と決済完了ページからリンク。金額・期日は申込書/HP/メールと同じ値に)。確認メールの AI学習アプリの使い始め方は `{ai_app_note}` (テスト B1x2/B1x4/B1k2)。
- **HP の `enrollment.html` (旧・決済なしの申込書) は 2026-09-23 に廃止**: `vercel.json` で Netlify の申込書へリダイレクトし、`academy.html` の「入塾申込」も同 URL。
  ファイルは `check_timetable_sync.py` の照合元として残す (削除するとゲートが落ちる)。旧申込書からの「入塾申込フォーム」の行は来なくなるが、
  代わりに決済完了の webhook が同じ referrer の行を作る (下記★) ので、申込待ちには従来どおり 2 行 (入塾申込フォーム + 塾生アプリ登録) が並ぶ。
  決済完了 → 月謝アプリ名簿 + 確認メール (塾生アプリ登録 URL 入り)。
  ★旧申込書が承認時に埋めていた `students.parent_email` (保護者週次レポートの宛先。mypage の保護者メール欄は 2026-09-09 にこの自動入力を前提に非表示) を保つため、
  決済完了の webhook `_enroll_post_course_application` が本体 API `/api/course-applications` に referrer=`入塾申込フォーム` の行を作る (KV `enroll:courseapp:<rid>` NX で再送は 1 本・
  失敗は塾長通知 ★要対応・`ENROLL_COURSEAPP_ENABLED=0` で停止・送り先は `ENROLL_COURSEAPP_URL`)。塾生アプリ登録の行と 2 行まとめて承認で従来どおり parent_email が入る。テスト B1s/B1y/B2e。
  parent_email が入る条件 (server/main.py の承認処理・従来どおり): 入塾申込フォーム行のメールがログイン用 (塾生アプリ行) のメールと**違う**・学年が矛盾しない・2 行が 30 日以内・
  既存の parent_email が空のときだけ (上書きしない)。
  同じ保護者メールで承認済みの生徒がいる (兄弟の 2 人目) と本体 API が 409「承認済み」で行を作らない → webhook は `blocked` として ★要対応 (Claude に保護者メールの設定を依頼)。テスト B1y5。
  AI学習アプリ (有料) を申し込んだ生徒は行の note に「AI学習アプリ（月額オプション +5,000 円）申込済み」と書き、`ceo.js` `_aiHint` がそれを見て承認ダイアログのヒント文で［OK］(AIあり) を勧める
  (ダイアログは `confirm()` なので既定値そのものは変わらない。有料なのに AIなしで承認する事故防止)。
  ★申込書 (Netlify) は時間割ゲートの対象外: 時間割を変えたら `入塾書類/index.html` の表も手で直して Netlify に再デプロイ。
- 完了イベントは `api/stripe-webhook.py` `_handle_enroll_first_charge`: reg:completed を **`checkout_mode="setup"` 相当** (PaymentIntent の
  payment_method・`monthly_fee` は月額のみ) で書き、**決済した JST 月の `charge:done` (SET NX) + `charge:history`** を `source=enroll-first-charge` で書く
  → 月末バッチはその月を skip。翌月分から月額を請求する。PaymentIntent の metadata に `month` は付けない (PI.succeeded の月次 reconcile を起こさない)。
- 保護者へ確認メール (`ENROLL_WELCOME_*`・`enroll:welcome:<rid>` で 1 通・`ENROLL_WELCOME_ENABLED=0` で停止) と塾長通知 (`ENROLL_NOTIFY_EMAIL`、無ければ `COURSE_NOTIFY_EMAIL`)。
  メールの Zoom の ID / パスコードは **env `ENROLL_ZOOM_ID` / `ENROLL_ZOOM_PASS`** から差し込む (公開リポジトリなので値を書かない。未設定なら「LINE でお知らせ」)。
  塾生アプリ登録 URL は `ENROLL_APP_REGISTER_URL` (既定 juku-register.html)。授業ルール (5 分前入室・画面オン・音声オフ) は本文に固定。
- 同じ Stripe 顧客の 2 件目の決済は `reg:duplicate:<rid>` に逃がして名簿に足さない (`reg:by_customer:<cus>`)。台帳の月は session.created の JST 月。
  KV に名簿を書けなければ `_RetryLater` → 500 で Stripe に再送させる (他の handler は従来どおり 200)。
- CORS: 申込書のオリジンだけ `Access-Control-Allow-Origin` を返す (`REGISTER_CORS_ORIGINS`、既定 Netlify の graceful-eclair-56bdac)。戻り先は `enroll-thanks.html` (同サイト。`ENROLL_RETURN_BASE` で上書き可)。
- テスト: `scripts/health_check/test_enroll_first_charge.py`。運用手順: `Desktop/🏫 運営・集客/塾運営/入塾申込_初回カード決済/README.md`。

## 教材・問題を作るときのルール (2026-08-02 塾長指摘を反映)
- **解説フォーマットは `server/main.py` の生成プロンプトが正典**。書き始める前に必ず読むこと。自己流の散文で書かない。
  - 数学(理系): 「方針→立式→計算→答え→補足」の 5 段階 (3行以上)。同プールの `seed-data/rikei_kyotsu_math_manual.json` が実例。
  - 英語: `## 🎯 コアイメージ` → `## 🔬 文構造分析` → `## 📍 本文の根拠` → `## ❌ 誤答 NG 理由` の **4セクション必須**「1つでも欠けたら不合格」。
  - 迷ったら**同じ (exam_id, part_key, eiken_grade) の既存 seed に合わせる**。プールごとに慣行が違う。
- **模試は本番形式で作る**。場面設定 300 字以上の会話文 + 誘導連鎖 (前問の結果を次問で使う)。
  各小問が独立した 4 択は「単元別ドリル」であって模試ではない。大問は丸ごと 1 単位で抽選されるので大問内の誘導連鎖は問題なく成立する。
  プールを分ける: 模試 = `math_1a`/`math_2b` (テンプレ `kyotsu_math` が引く) / ドリル = `math_unit`。
- **数学の正解は手入力しない**。`correct`/`distractors` を「LaTeX と sympy 値」の組で持ち、`verify()` で独立に再計算して照合する。誤答が正解と同値でないことも確認する (別表記の同値が混じると正解が 2 つある問題になる)。
- **正解番号は大問ごとに 0〜3 の順列で配る** (`scripts/kyotsu_mogi2026/answer_positions.py`)。全体だけ均等にしても大問内が偏る (実測で 3 連続・21大問中10大問が半数以上)。生徒は大問単位で解く。
- **解説が引用する英文は本文に実在させる**。要約を引用符で囲まない。`audit.py` が全数照合する。
- **英語の模試は大問ごとに図版 (`question_data.figure_svg`) を付ける**。本番の共通テスト リーディングは
  カレンダー/ポスター/比較表/グラフ/イラスト/時系列図が全大問に付く。本文だけだと「読解問題」にはなっても
  「共通テスト形式」にはならない (2026-08-02 塾長指摘)。図の作法は `scripts/kyotsu_mogi2026/figures_eng.py`:
  - **図に本文に無い数値を出さない**。出すと設問の根拠が本文外に出て引用照合が破綻する。
    `build_eng.py::check_figure` が図中の全数値を本文と照合する (綴り字 "thirty" ↔ 30 も解決する)。
    軸の目盛りだけは `figures_eng.AXIS_TICKS` に宣言して除外する。
  - **線と文字は `currentColor`**。PDF は白地・Web アプリは暗地なので、固定色だとどちらかで沈む。
    塗りは中間色 (#3b82f6 / #ef4444 / #22c55e / #f59e0b) のみ。
  - **✓ / ✗ は文字で置かず線で描く**。日本語フォントに無いと PDF で豆腐になる。
  - `<script>` と `on*` 属性は禁止 (server 側 sanitizer で落ちる)。
  - ★ `mock-exam.js` は `figure_svg` を描画しない (未対応)。Web 受験に載せるならフロント側の対応が要る。
- **PDF を作るなら passage / stem / choices / explanation の 4 つを漏れなく KaTeX に通す**。通し忘れると日本語フォントで `¥(AB=6¥)` と出る。整形は必ず LaTeX 描画の**前**に行う (後だと SVG path が本文に漏れる)。
- 作ったら `scripts/kyotsu_mogi2026/preflight.py` (取込契約) と `audit.py` (総点検) を必ず通す。詳細な経緯は `scripts/kyotsu_mogi2026/README.md`。
- ★**納品前に必ず「相互チェック」を入れる — 単一経路の生成物を信じない (2026-08-16 塾長指示)**。
  独立した経路どうしを突き合わせて初めて「できた」と言う。教材なら最低この 3 層:
  ① 出力物どうしの照合 — 同一の正典データから全出力を生成し、刷り上がり (PDF 等) からも抽出して全問・全選択肢を逆照合。
  ② 機械検査 — ビルド時 verify (解説の番号と選択肢のずれ・正解位置の偏り等) + コミット済み `check*` ゲート + 取り込み後の DB 読み返し。
  ③ 人手の再点検 — **正解の一意性** (誤答が別解釈で正解にならないか・正解が 2 つないか) は機械では見えないので、全問を敵対的に読み直す。
  book_exam の実装例: `scripts/book_exam/materials/_grammar_build.py::verify` / 同 `check_grammar_books.py` / `import_books.py` の読み返し検証。

### 英文法ドリルの問題プール (`grammar_questions`) を増やすとき (2026-09-17)
CEO の「📝 科目別 単元ドリル」が出題するプール。**問題はアプリ内で生成しない** (塾長指示: AI API の容量を食う)。
セッション側で作って `seed-data/` に JSON を置き、ボタンの取込だけで本番に入れる。
- **シードの追加手順**: `seed-data/grammar_drill_pool_vN.json` を追加 → `ceo.html` の `#grammarPoolImportBtn` の
  `data-seed` にカンマ区切りで足し、`data-size` を合計問数に更新するだけ。ハンドラが順に POST する。
- ★**自動配信 (3日ドリル・クラス自動宿題) に出るのはレビュー済みの出典だけ** (2026-10-15 塾長決定)。出典 (`source`) の許可リストは
  `server/main.py` の `_AUTO_DELIVERY_REVIEWED_SOURCES_DEFAULT` (科目ごと・末尾 `*` は前方一致・判定は `_auto_delivery_source_ok`)。
  新しいシードは **ほかと重ならない出典の接頭辞** にし、盲検 3 名を通したら許可リストと `test_auto_delivery_shared.py` の `REVIEWED_SEEDS` に
  1 行ずつ足す (盲検していないなら `NOT_AUTO_SEEDS`)。どちらにも無い `*pool*` / `*_drill_*` / `*grammar*` のシードがあるとテストが落ちる。
  習熟度テスト (科目 `proficiency_test`・出典 `pt-` / `ptest:`) は env `AUTO_DELIVERY_REVIEWED_SOURCES` でも外せない禁止。
  英語長文 (`english_long`) は取込スクリプトの出典 `el-` / `englong:` を許可 (取込でサーバが盲検の記録を必須にしているため・下の 📖🧪 の節)。
  本番の在庫は `GET /api/admin/grammar/source-inventory` (読むだけ・CEO の管理者か X-Cron-Secret) で、自動配信できない古い行 (`legacy_active`) と単元ごとの在庫を見る。
- **取込 API の落とし穴**: `POST /api/admin/grammar/import` は 1 リクエスト **2000 問まで**。
  `unit` は english なら `server/main.py` の `GRAMMAR_UNITS` と**完全一致**でないと **無言で skip** される。
  `_GRAMMAR_SUBJECT_UNIT_ORDER` に載っている科目 (中学英語・中学数学・英検) は、そこに無い単元名の問題・本文を
  **errors に数えて入れない** (2026-09-29)。CEO の補充ボタンは ⚠️「エラー N」と件数しか出さない。単元名は API 応答の
  `unknown_units` / `warning` (登録済みの単元と見た目が同じ綴り違い = 全角・見えない文字・ー/一 は `looks_like` にその単元) と、
  取込が最後まで通ったときは Railway のログ `[GrammarImport]` に出る。
  新しい単元はシードより先にそこへ足すこと (Vercel が先に出るので、サーバ反映前に押すと弾かれる。反映後に押し直せば残りだけ入る)。
  それ以外の科目は任意 unit 可。回帰テストは `scripts/health_check/test_grammar_import_units.py`。
  重複判定は `source_exam_question_id` があれば (その id + stem)、無ければ (stem + unit + subject) の完全一致。
  **押し直しても二重登録されない**代わりに、既存問題の解説を直したいときは再 import では**上書きされない** (INSERT 専用)。
  直すなら DB を直接更新するか、行を無効化 (`active=0`) してから入れ直すこと。
- 取込 API の任意の指定 (2026-10-15): `dry_run: true` は数えて rollback (何も書かない)・`all_or_nothing: true` は本文 (passages) が
  1 本でも形式不正・知らない単元名なら要求ごと取り消して `ok:false` (`rejected_index` / `reason`。questions[] には効かない)。
  **本文型だけの科目** (`_PASSAGE_ONLY_SUBJECTS` = 英語長文・習熟度テスト) は questions[] で来たら 422、`review` (盲検 3 名の記録) が無ければ 422。
  CEO の補充ボタンはどれも送らないので動きは変わらない。
- **解説に ①②③ や「選択肢2」を書かない**。生徒画面は選択肢の並びをそのまま出すが、値で説明しておけば並びが変わっても壊れない。
- **正解の一意性は盲検でしか取れない** (上記③と同じ)。v2 (985問) は生成 → 機械検査 → 既存との重複照合 →
  **正解を伏せた独立ソルバー 3 名が全問を解いて全員一致した問題だけ採用** → 別担当が解説を校閲 の順で作った。
  20単元×50問=1000 から落ちたのは 15 問 (機械検査と重複照合で 3・盲検の不一致で 12)。解説は 19 件修正。
  その後の 3 視点レビューで v1 と論点まで重なっていた 4 問を差し替えて 985 問。
- **在庫の実測**: このボタン (v1 703 + v2 985) だけなら 1 単元 79〜87 問、弱点特訓 32 問も入れると 79〜92 問。
  ただし **basic は 1 単元 11〜12 問しかなく、v2 でも増えていない**ので、基礎を厚くしたい場合は次のシードで basic を増やすこと。
- 単元バッジの数字は**選択中レベルの在庫**で、合計とは一致しない。既定の「標準〜やや難」では 68〜75 (弱点込みで 68〜80) と出る。
  レベル選択に「基礎のみ」は無いので、25 問のドリルはどのレベル指定でも作れる (標準単独 34〜42・やや難単独 34〜40)。

### 中学英語 (高校受験) のドリルは **別科目 `chugaku`** (2026-09-23)
塾長「この問題プールに中学生レベルも追加できますか」→ **レベルを増やさず科目を増やした**。理由と落とし穴:
- ★**未知の `level` は import で黙って `standard` に丸められ、dedup は level を見ない**ので、入れ間違えると
  手で DELETE するまで英文法プールが汚染される。未知の `subject` は skip されるだけなので、取込順を間違えても汚染しない。
- 初回診断・今日の1問は科目で出題先を決めるので、科目を分けるだけで「高3の最初の1問が中2の過去形」を避けられる。
  ★2026-10-15 から学年でも分ける (`_self_issued_subject` = 画面のモードと同じ `_student_mode_from_grade`・未入力は高校生):
  今日の1問は 高校生 = english・中学生 = chugaku・小学生モード = 409 (mypage は alert で理由を出す)。初回診断は高校生だけ (中学生・小学生は 409)。
  どちらもレビュー済みの出典の行だけ (`_self_issued_reviewed_ids`・`ORDER BY RANDOM()` をやめて Python で選ぶ)。回帰テスト `test_self_issued_drill_band.py`。
  3日ドリル (弱点ルーティン) は 2026-10-15 から学年の区分 (`_student_grade_band`) で english/math と中学 5 教科を分ける (下の 🎯 自動の弱点配信)。
- CEO のレベル4択は「範囲の軸」なので、そこに学年の軸を混ぜると「基礎も含める」と区別できなくなる。
- 単元名は `scripts/chugaku_dojo/units.json` の eng の `filter` と**完全一致**させる (入試道場の弱点 topic と突き合わせるため)。
  並び順は `server/main.py` の `_GRAMMAR_SUBJECT_UNIT_ORDER` が持つ (english 以外は既定で在庫数の降順になり、学習順にならない)。
- ★**`question_attempts.subject = 'chugaku'` は中学生の英数国理社が collapse した 1 バケット** (`:6705` の注記)。
  ドリル科目の「中学英語」とは別物なので、週次レポートの科目ラベルは `_WEEKLY_SUBJECT_LABEL_OVERRIDE` で
  「高校入試演習」に差し替えてある。ここを `_GRAMMAR_SUBJECT_LABEL_JA` に任せると、数学しか解いていない生徒の
  保護者レポートが「中学英語が苦手」になる。★3日ドリルは中学生の 'chugaku' の弱点を **単元名の完全一致** で中学 5 教科の単元に当てる
  (`_chu_drill_for_topic`・単元表は `_GRAMMAR_SUBJECT_UNIT_ORDER`。当たらない topic は配らない = 科目を推測しない)。
- **在庫は 1 単元 138〜149 問 (標準+やや難 103〜113)**。2026-09-24 に中学生が 25 名いると分かったので 741→1,213 問、
  2026-09-29 に 1,730 問へ増やした (v4 は追記のみ・source `chugaku-drill-v4`)。同じ単元で 25 問のドリルを **4 回**まで配れる。
  ★v4 は 590 問を作って盲検・点検を通したが、**独立レビューで「名前や物だけ入れ替えた同じ枠」が 73 問**見つかり外した
  (作問を1単元5回に分け、前の回の stem を渡しても後の回が同じ枠で書く。盲検も単元内の点検も素通りした)。
  追加で作るときは、作問後に「同じ論点・同じ文の枠」だけを探すレビューを単元ごとに別に回すこと。★ただし `exclude_drill_id` は
  **ドリル1本しか除外できない**ので、3 回目以降は直前の回とは別だが、それより前の回と一部重なる。
  ★50 問だと 2 回、25 問ちょうどだと 2 回目が必ず 400 になる (中学数学は 1 単元 標準+やや難 50 問ちょうど = 2 回)。
- シードは `seed-data/chugaku_drill_pool_v1.json` 1 本 (1,730問)。ボタンは `#chugakuPoolImportBtn`。
  ★**本番に取込済みの問題は書き換えない (追記だけ)**。取込は INSERT 専用で、問題文が同じなら飛ばすため、既存行を直しても本番に届かない。
  取込は **400 問ずつに分割して POST** する (1リクエスト2000問の上限と、本文が数百KBになるのを避けるため)。
  途中で失敗しても dedup が効くので押し直せば残りだけが入る。
- ★**中学の範囲は 2021年度の学習指導要領で動いている。**「高校範囲だから除外」と決める前に確認すること。
  - **仮定法のうち基本的なもの（`I wish + 過去形` / `If I were you, I would 〜`）は中3必修**で公立入試に出る。
    v1〜v3 では高校範囲だと思い込んで1問も作っておらず、2026-09-24 に16問追加した（単元は「助動詞」に収めた）。
  - 逆に**関係代名詞は主格 who/which/that と目的格 which/that だけ**。**所有格 whose は高校範囲**なので
    正解にしない（誤答に置くのは可。疑問詞の whose は中1で習うので弁別に効く）。一度 whose を正解にする
    問題を10問作ってしまい、盲検の「範囲外」判定で気づいて全部作り直した。
  - `関係代名詞 what` は誤答としては使ってよい（`the book what I bought` は日本語話者が実際にやる誤り）。
    使ってはいけないのは **whom**（中学で一度も出てこないので、見ただけで消せて弁別に寄与しない）。
- ★**「読まずに解ける」問題は機械検査でも盲検でも落ちない。** 実測した2つの型:
  - 助動詞100問のうち**37問が「4択に助動詞が1つだけ」**で、文を読まず「原形の前に置けるのは助動詞」だけで解けた。
    → 誤答も助動詞にして、意味が文脈に合わないことで切れるようにする。
  - 関係代名詞で**that が選択肢に出た15回のうち13回が正解**（87%）。「that があれば選ぶ」で解けた。
    → 正解語ごとに「選択肢に出た回数 / 正解になった回数」の比を出し、どれかに寄っていないか確かめる。
- ★**盲検の採点は、ソルバーの番号の基準をそろえてから行う。** 3名のうち1名が 0 始まり、1名が 1 始まりで
  答えることが実際に起きる。基準をそろえずに採点して「37問全部が不合格」と誤判定した。
  プロンプトに「0 始まり」と明示し、採点側でも**鍵との一致率で基準を推定してから**突き合わせること。
- ★**デプロイ順は選べない**。`git push` 1 回で Railway と Vercel の両方が走るが、Railway は「Wait for CI」が有効で
  `.github/workflows/server-tests.yml` を待つのに対し、**Vercel は CI を待たないので必ず先に出る**。
  つまり「ceo.html とシードが先・サーバが後」が既定で、その窓では旧サーバが `subject=chugaku` を
  **無言で english にフォールバック**する (`/api/admin/grammar/units` の `if subj not in _GRAMMAR_CANON_SUBJECTS`)。
  → 対策として `gdLoadUnits` が `data.subject !== 選んだ科目` を検出したら単元を空にして
  「サーバの再デプロイ待ちです」と出す。**押しても DB は汚れない** (配信も取込も 422 で止まる)。

### 英検の語彙ドリルは **別科目 `eiken`** (2026-09-24 塾長指示「英検対策コースの子にも英検の語彙問題を。2級もやって」)
- 級は level ではなく **unit 名** で分ける: 「2級 単語」「2級 句動詞・熟語」「準1級 単語」「準1級 句動詞・熟語」。level は全問 `standard`
  (CEO 既定の「標準〜やや難」で全在庫が対象)。並び順は `_GRAMMAR_SUBJECT_UNIT_ORDER['eiken']`、ラベルは「英検」(長文の単元も同じ科目なので「語彙」は付けない)。
- シードは `seed-data/eiken_vocab_pool_v1.json` (400 問 = 2級 130 + 準1級 270)。ボタンは `#eikenPoolImportBtn` (400 問ずつ POST・dedup・無課金)。
  変換スクリプトは `scripts/eiken_vocab/build_eiken_seed.py` (出所と読み方は docstring)。出所は全部この塾の書き下ろし:
  準1級 = 本番形式演習 第1弾/第2弾 (Desktop/📚 教材/英語/_生成元_英語教材_202609/data/eikenp1_mock*) + 完全模試 全3回
  (Desktop/英検準1級_完全模試_…_20260923/_制作ソース/pre1_set*_data.py の P1)、2級 = 対策問題集 Vol.1 (`scripts/eiken_2kyu/data/part1_vocab.json`)
  + Vol.2 と完全模試 全3回 (**生成元が無いので PDF テキストから抽出**。空所は行末の空白/空白行、文頭の空所は消えるので補う。
  模試の選択肢は問題冊子の活用形 = 解説冊子の意味行は原形)。★リポジトリ外の教材は Desktop 側にある (無ければ builder は落ちる = 欠けたシードを書かない)。
  出力の形式は `scripts/check_eiken_vocab_seed.py` が固定する (空所 1 つ・4 択・番号参照なし・正解位置 40% 以下・stem 一意)。
- 学年で縛らない (2級を中3が受ける・準1級を高1が受ける)。CEO の取り違えガードは `eiken` を素通しにしている。
- 提出は `question_attempts.subject='eiken'` / `topic=単元名` で記録される。診断・今日の1問は英文法だけ・3日ドリルは英検を出さない (英検の自動配信は
  塾生アプリのみ枠のクラス自動宿題だけ) ので、英検問題は流れない。
  **週次の弱点プリントと mypage の弱点 TOP3 は `subject <> 'eiken'` で英検を外す** (`_WEAKNESS_SUBJECT_TO_POOL` に eiken が無く、
  枠だけ食って空の節を作るため)。生徒画面の科目ラベル (class.html `GD_SUBJ_JA` / mypage.js `_SUBJ_DRILL_LABEL` / mypage.html `subjectLabel`) には
  eiken を入れてある (入れないと生の `eiken` や「英文法」と出る)。
- ★取り込む前に **正解を伏せた独立ソルバー 3 名** で全問を解かせ、全員一致しない問題は直すか外す (英文法 v2 と同じ工程)。
  2026-09-24 の初回: 401 問を 3 名が解いて全問一致。指摘 3 件 (活用ミス・時制ずれ・第 2 の正解の余地) を直して 400 問にした
  (上書き表は builder の OVERRIDES/DROP。生の解答ファイルは `scripts/**/blind/` の .gitignore 方針どおり入れない)。選択肢や本文を触ったら盲検をやり直す。
  Vol.1 (39 問) には全訳が無い (元データに無い)。回帰テスト: `scripts/health_check/test_eiken_drill_pool.py`。

### 🎒 生徒詳細モーダルの「在籍クラス」行 (2026-09-24 塾長「ここに在籍クラスを出すことは可能？」)
- `admin_stats` が `class_labels` (時間割 label の配列・列が無い環境は []) を返し、申込内容タブの「学年」の下に出す。「✏️ 編集」は
  `/api/admin/class/timetable-classes` のチェック → `POST /api/admin/class/student-classes` (🏫 通塾クラス管理の「生徒別」と同じ API・
  時間割に無い label は落ちる)。旧サーバ (キー自体が無い) は「反映待ち」と出して編集ボタンを出さない (空配列 = 未設定 と区別)。
  この値で決まるのは 出欠の絞り込み・録画の表示 (未設定 = 0 本)・クラス宿題の一括配信・一斉送信 (クラス指定) の宛先。**配布ファイルは
  全通塾生に出る** (class_labels で絞らない)。編集ボタンは通塾生 (course=kokuritsu_nankan / plan=student_addon・受講開始月ブロックと同じ判定)
  にだけ出す: 通塾生以外に付けても feed には効かず一斉送信の宛先にだけ入り、🏫 の名簿からは外せないため (API 自体は生徒を選ばない)。
  保存後は `window.__scReloadStudents` で 🏫 側のキャッシュも更新。回帰テストは `test_start_month_archive.py`。
- ★この値は **単元ドリル ⑤ / 宿題ビルダー ⑥ の「🗓 受講クラスから自動」グループ**にも使う (2026-10-06 塾長「グループの設定を受講科目から
  自動で反映できない？任意の設定はそのまま残して」)。ceo.html の `DGA*` が画面で作る (クラスごと + コースは全コマ受講の生徒だけ・
  クラスとコースの一覧は timetable-classes)。作るのはページを開いたとき・「🔄 読み直す」・同じ画面で在籍クラスを保存したとき
  (生徒詳細・生徒別・クラス別一括の 3 か所が `window.__dgaRefresh` を呼ぶ。ハブでセクションを開き直すだけでは作り直さない)。
  ★**delivery_groups (手動の 👥 グループ) には保存しない**: 手動は名前で上書き保存・✕ で即削除の作りなので、混ぜると同名の手動グループを
  書き換える/自動のものを消せてしまう。入れるのは **通塾生** (course=kokuritsu_nankan / plan=student_addon = `_tsujuku_roster` と同じ。
  本クラスから外すと course だけ消えて class_labels と trial が残るため) で status が trial/paid/past_due、受講開始前でない生徒
  (⑤ は今月・⑥ は宿題の期限の月で判定 = クラス宿題の一括配信と同じ。⑥ で期限を変えると、直前に 🗓 で足した生徒だけ選び直す =
  手でチェックした生徒には触らない)。外した生徒・同じ名前の二重登録 (サーバの _normalize_person_name と同じ照合) は押したときに名前つきで出す。
  ★「⚠️ 時間割に無いクラス名が残っている N名」は直しが要る (生徒詳細の ✏️ 編集で保存すると消える。クラス別一括登録では消えない)。
  在籍クラスが空の通塾生は灰色の情報だけ (オンラインの AI 学習管理コース生も course=kokuritsu_nankan で、クラスが無いのが正しい = 警告にしない)。
  `students.course` (通塾生全員に付く) ではコースを判定しない。学年・プランで分けたグループ (中学生・高校生レベル・夏期講習) は在籍クラスからは
  作れないので手動のまま。🏫 は ⑤ で「塾生アプリ登録の生徒」の印なので、自動グループは 🗓。

### 📖 長文型ドリル = 本文 1 つに設問が複数 (2026-09-24 塾長「長文読解・長文空所補充も単元ドリルに」→「A で」)
- 表 `grammar_passages` (subject/unit/level/title/body/body_ja/source/body_hash/active) + `grammar_questions.passage_id / passage_seq` (後付け列)。
  `_grammar_has_passages()` は **列と表の両方** を `_table_has_column` で見る (CREATE TABLE だけロック待ちで飛び ALTER だけ通ると「列はあるが表が無い」
  になり、Postgres では失敗したトランザクションが同じ接続の単発ドリル抽出まで 500 にする)。**本文のある単元は「本文 N 本」単位で出題**
  (`_grammar_pick_drill_passages`・設問は passage_seq 順・score_total は設問数・`passage_count` 既定 2 = 本番の大問 1 回分・上限 5・設問が全部
  inactive の本文は選ばない)。判定はサーバが単元の在庫で行う (client が count を送っても無視) ので、弱点対策の再配信など古い経路から来ても本文が
  バラけない。`exclude_drill_id` は前回の **本文ごと** 除外。1 問ずつの抽出 (`_grammar_pick_drill_question_ids` = CEO の科目全体・3日ドリルの `_auto_pick_reviewed_question_ids`) は
  `passage_id IS NULL` で長文の設問を拾わない。本文の無い単元は出題ロジック不変 (応答に `passages: {}` / `passage_count: 0` / `passage_ids: []` / `passage_id: null` が増えるだけ)。
- 取込は `POST /api/admin/grammar/import` の `passages: [{unit, level?, title?, body, body_ja?, source?, questions:[{stem, choices, answer, explanation?}]}]`
  (1 リクエスト 200 本まで)。本文は body の正規化ハッシュで重複判定 (本文ごと skip)。**設問は stem で重複判定しない**
  (大問2 の設問は「( 1 ) に入る語」型で本文をまたいで同文)。設問の形式が壊れた本文は本文ごと入らない (ValueError → skip)。それ以外の例外
  (DB 側) は **rollback して中断し ok:false** を返す (Postgres は失敗したトランザクションの commit が黙って ROLLBACK になるため、続けると
  「200 なのに 0 件」になる)。english の本文は受けない (GRAMMAR_UNITS 固定)。取込は level 省略で standard。
- 生徒の GET / 提出 / CEO の分析は `passages: {id: {id, title, body[, body_ja]}}` と設問の `passage_id` を返す。**全訳 body_ja は完了後だけ**。
  class.html / mypage.js は「本文カード (1 回) → その本文の設問…」の順に並べ (`gdBlocksHtml` / `_gdBlocksWithPassages`)、
  空所番号「( 1 )」を黄色にし、本文は KaTeX の対象外 (`ignoredClasses: ['gd-nomath']` = 英文の $20 を数式にしない)。
  復習カード (mypage.js) は長文の設問だけキーを question_id で分け (同文の stem が本文をまたいで衝突するため)、カード本文に【本文】を先に付ける。
- **本文の表 (2026-10-17 塾長「アプリ側で表を直しておいて」)**: 取込仕様 §2 の「［表］」の行 + 全角「｜」区切りの行 (1 行目 = 見出し・「｜」の無い行で終わり) を
  `<table>` にする。class.html `gdPassageTables`・mypage.js `_gdPassageTables`・ceo.html `_gdPassageTables` (👀 問題を見る の本文と全訳・📊 分析の 📖 本文) に
  **同じ規則を 1 つずつ** 持つ (共通 JS にしない = 読み込み順の心配を作らない)。**エスケープ → 空所の黄色 → 表** の順で、表の関数はエスケープ済みの
  文字列だけを受ける。箱は pre-wrap なので表の HTML に改行・字下げを入れない (「［表］」の行は消し、表の直後の改行 1 つは表が吸う = 空行を増やさない)。
  スマホ (カード幅 約 270〜309px) は折り返さずに横スクロール (`overflow-x:auto`・セルは nowrap)。半角 `|` は表にしない。列の数がそろわない行は空のセルで埋めて出す
  (取込の検査 E_TABLE は止める)。表の無い本文は今までと 1 文字も変わらない。
  **今日の復習 (2026-10-17 塾長「今日の復習カードの表も直しておいて」)**: マイページの「🔁 今日の復習」(learning-brain.js `renderTodayReview`) も同じ規則・同じ見た目
  (`_lbPassageTables`)。カードの problem は「【本文】\n」+ 生の本文のまま保存し (mypage.js の保存する形は変えない)、**描くときに**直す (今あるカードも直る)。
  pre-wrap の箱 (「… 全文を見る」・「📝 解いてみる」の問題文・解答と解説の「… 全文を見る」) は `_lbPassageTables(_escHtml(…))` で表、
  1 行の短い表示 (先頭 100 字・解答 300 字・解説 500 字) は `_lbTablesInline` で表を「セル / セル ・ 次の行」の 1 行にしてから切る (表の途中で切れても「［表］」「｜」・タグが出ない)。
  learning-brain.js を変えたら読む HTML 5 枚 (index・english-exam・exam-prep・material-scan・mypage) の ?v= を全部上げる。
  回帰テスト `scripts/health_check/test_passage_table_render.py` (4 ファイルの本物の関数を JS エンジンで動かして突き合わせる・変更前の関数と比べる。
  learning-brain.js はまるごと偽の DOM で動かし、表の関数の呼び出しを外した版と表の無いカードの HTML が 1 文字も変わらないことを見る)。
- CEO: 本文のある単元はバッジが「📖 本文N本」、④ が「本文の本数」の select に切り替わる (`_gdUnitIsPassage`)。分析は本文を折りたたみで 1 回だけ出す。
- **👀 問題を見る** (`gdPreview` → `GET /api/admin/grammar/preview?subject&unit&levels&count&passage_count`): 選択中の単元の問題を答え・解説・全訳つきで
  ランダムに出す (長文型は本文 1 本、それ以外は 5 問)。配信もドリル作成もしない。塾長は生徒名簿に居ないので自分に配って確かめられない
  (2026-09-24「どんな問題か確認したい」)。抽出は配信と同じ関数を使う。
- 英検の単元順は語彙 4 → 長文 4 (「2級 長文空所補充」「2級 長文 内容一致」「準1級 長文空所補充」「準1級 長文 内容一致」)。
- 回帰テスト: `scripts/health_check/test_grammar_passage_drill.py` (取込の dedup・本文単位の作成・順序・除外・GET/提出/分析・単発の不変・👀 プレビュー = 作らない/401/422)。
- **シード** `seed-data/eiken_reading_pool_v1.json` (本文 100 本 / 設問 327 問 = 2級 空所補充 14 本・内容一致 14 本、準1級 空所補充 36 本・
  内容一致 36 本)。ボタンは `#eikenReadingImportBtn` (`eikenReadingImport()`・20 本ずつ POST・本文ごと dedup)。変換は
  `scripts/eiken_vocab/build_eiken_reading_seed.py` (出所と読み方は docstring: 準1級 = 本番形式演習 JSON・完全模試 py・総合対策 py、
  2級 = Vol.1 JSON・Vol.2 PDF・完全模試 PDF・2026-06 の md 模試。PDF は PyMuPDF で行ごとに起こし、段落は行間と行の右端で切る)。
  ★出所ごとに正解の添字が 0 始まり/1 始まり・空所番号が本番の通し番号 (19)(41)((1)) とばらばら → 空所は「( 1 )( 2 )…」に付け直し、正解の添字は 0 始まりにそろえる。
  教材のメール文の架空アドレスは @ を全角 ＠ にして PII ゲートを通す (実在アドレスは出所に無い)。2級 Vol.1 の 6 本は出所に全訳が無いので builder の VOL1_JA に持つ。
  本番形式演習の全訳 6 本は空所の訳が抜けていたので MOCK_JA_FILL で補う。盲検 (2026-09-24): 328 問中 327 問が 3 名一致 = 正解表どおり、
  残る 1 問 (完全模試 第1回 P2B 空所 1) は 3 名とも「別解あり」→ DROP_Q で設問だけ落とした (空所を正解語で埋めて付け直す)。
  形式ゲートは `scripts/check_eiken_reading_seed.py`。盲検 3 名 × 4 分割 (`--blind DIR` → `reconcile_reading_blind.py`) の結果は
  OVERRIDES / DROP に書いて再ビルドする (生出力はコミットしない)。
- **v2 = 本番形式演習 (2026-10-06 塾長「デスクトップに英検の 2 級と準 1 級の問題演習があるので科目別ドリルに追加して」)**:
  `seed-data/eiken_vocab_pool_v2.json` (大問1・417 問 = 2級 255・準1級 162) と `seed-data/eiken_reading_pool_v2.json` (大問2/3・本文 96 本 /
  設問 326 問 = 2級 空所補充 30 本・内容一致 30 本、準1級 空所補充 18 本・内容一致 18 本)。単元名・形式は v1 と同じ (サーバ変更なし)。
  変換は `scripts/eiken_vocab/build_eiken_honban_v2_seed.py` (出所: Desktop/📚 教材/英語/04_英検/2級/英検2級_本番形式演習_*/_制作資料/{part1,reading}.json と
  準1級/英検準1級_本番形式演習_第N回_*/_制作資料/content.py を runpy。準1級は `_確認資料/最終検査.json` が PASS_FINAL の回だけ)。
  ★各回の **問題冊子 PDF の文字列と stem・選択肢の並びを前から照合** し、1 か所でもずれたら書き出さない (データを直した後に刷り直していない回を拾う)。
  大問1 の単元は番号で分ける (2級 1〜10 = 単語・11〜17 = 句動詞・熟語 / 準1級 1〜14 = 単語・15〜18 = 句動詞・熟語)。大問4/5 (要約・英作文) は入れない。
  CEO の 2 つの補充ボタンは `data-seed` を **カンマ区切りで v1 → v2** と持ち、順に読んでつないで送る (取込済みの v1 は dedup で skip)。
  ゲート 2 本は v1/v2 をまたいで stem・本文の一意を見る。盲検 (2026-10-06): 3 名が語彙 417 問・長文 327 問を解き、語彙は全問・長文は 326 問が全員一致。
  準1級 第5回 大問2[A] 空所 1 は 3 名とも別解あり → DROP_Q で落とした。本番形式演習の新しい回ができたら builder を回し直して盲検をやり直す。
- **v2 に 準1級 第10・11回を追加 (2026-10-06 塾長「英検準1級の問題を PDF でデスクトップに追加してあるので問題プールに取り込んで」)**:
  語彙 453 問 (準1級 198)・長文 本文 104 本 / 設問 352 問 (準1級 44 本)。CEO の 2 ボタンの合計は 語彙 853 問・長文 本文 204 本 / 設問 679 問。
  ★デスクトップ整理で各回が `2級/01_本番形式演習_第1〜15回/`・`準1級/01_本番形式演習_第1〜11回/` の中に入った → builder は直下と 1 段下を探す
  (`round_dirs`・同じ回が 2 つあれば止める・回番号はフォルダ名だけから読む)。直下だけ探すと 1 回も見つからない。
  ★最終検査の status は `PASS_FINAL_INDEPENDENT_DELIVERY_CHECK` (別担当の配布前検査まで済んだ回) もある → builder の `P1_PASS_STATUSES` に
  名前を決め打ちで足した (PASS_FINAL だけだと 第1・2・3・7・8 回が黙って落ちてシードが減る。知らない PASS* は止める)。
  ゲート `check_eiken_vocab_seed.py` は retired_sources が今のシードの問題 (同じ source と問題文) を指していないことも見る (指すと同期で止めた行に
  取込の重複判定が当たり、その問題が黙って消える)。
  ★作者が v2 の取込後に配布前検査で 3 か所直していた (最終検査.json の correction): 第8回 Q7「別解になりうる誤答を交換」(問題文は同じ) /
  第7回 Q18「紛らわしい誤答を交換・問題文も変更」/ 第1回 大問3[B]「withdraw の和訳を 履修の中断 へ」。前の 2 つは本番に旧版が入っていたので、
  🏅 語彙ボタンを **同期 → 取込** にした (Q7 は同期でその場で直す = 正解の文と位置が同じなので配信済みでも直す / Q18 は旧版を
  `_meta.retired_sources` の (source, 旧い問題文) で止め、直した版を取込で入れる = builder の `RETIRED_VOCAB`)。
  第1回 大問3[B] の和訳・解説は本番では旧版のまま (長文の設問は source が回ごとの名前で 1 問ずつ照合できない・答えは変わらない)。
  盲検: 第10・11回 (語彙 36 問・長文 26 問) と直った 2 問を 3 名で → 全員一致・指摘なし。

### 📖 英語長文 (科目 `english_long`) と 🧪 習熟度テスト (科目 `proficiency_test`) — 手元のファイルから取込・seed-data に置かない (2026-10-15 塾長決定)
- Codex (別の AI) が取込仕様書 (`docs/drill-import-spec.md`・ファイルの中の番号は 1 始まり) どおりに作って盲検 3 名を通し、塾長が手元の取込スクリプト
  (`scripts/drill_import/`・0 始まりに直して送る) で入れる。**seed-data にもリポジトリにも置かない** (公開されるため。テストの答えが漏れる)。
- english に混ぜず別科目にした理由: english は単元が `GRAMMAR_UNITS` 固定で本文を受けず、今日の1問・初回診断・3日ドリル・弱点 TOP3 が english を
  直書きしている (混ぜると長文の設問が 1 問だけ切り離されて出る)。別科目なら自動の経路に構造上混ざらない。
  別名は「英語長文」「習熟度テスト」だけ。★「長文」「長文読解」は足さない (`/api/question-attempts` が日本語の科目名を寄せるので、入試道場の「長文読解」が化ける)。
  どちらも本文型だけ (`_PASSAGE_ONLY_SUBJECTS`) = 全設問が本文に紐づくので、1 問ずつの抽出 (`passage_id IS NULL`) には出てこない。
- **英語長文**: 単元 = 長文クラス (`長文 Lv.1` 月曜3限・`長文 Lv.2` 火曜3限・`国公立 長文` 金曜3限・`_GRAMMAR_SUBJECT_UNIT_ORDER`)。level は standard だけ
  (取込でそろえる)。出典は設問 `el-<set_id>-<qid>`・本文 `englong:<set_id>:<pid>` で、自動配信の許可リストに入っている。自動で出すのは
  長文クラスのクラス自動宿題 (高校生だけ・1 回 1 本) だけで、3日ドリルの科目ではない。CEO の配信は従来の長文型と同じ (本文 2 本・ランダム)。
- **習熟度テスト**: 1 ファイル = 1 回分 = 1 単元「高校英語 習熟度テスト 第1回」(`_PTEST_UNIT_RE`・直した版は「…第1回改1」)・大問 1 つ = 本文 1 つ
  (1 回分 12 大問・60 問まで)。CEO で配ると **全大問を取込順のまま 1 本のドリル** (`_grammar_pick_drill_passages` は習熟度テストだけ ORDER BY id。
  レベル・本数の指定は使わない・👀 プレビューもテスト全体)。同じ生徒に 2 回は配らない (応答の `already_taken`・全員なら 409・`allow_retake: true` で
  解除 = CEO には出さない)。`exclude_drill_id` と単元なしは 422。答えは提出直後に見えるので、全クラス同じ日に実施する。
  お知らせのメールの件名は「🧪 習熟度テスト「…」が届きました」(「解説がその場で」は書かない・アプリの帯は「🆕 新しい宿題」のまま)。
- **習熟度テストはどの自動配信にも出さない**: `_AUTO_DELIVERY_DENY_SUBJECTS` (env でも外せない)・出典 `pt-` / `ptest:` も禁止・
  `_drill_subject_band_ok` はどの区分にも False。自動配信の関数は許可リスト方式なので、名前を書かなくても出ない (テストがソースを見て固定)。
- 弱点: 習熟度テストの解答は `subject='proficiency_test'`・topic=単元で記録し、弱点集計は読まない (単元名が弱点にならない)。
  env `PTEST_FEEDS_WEAKNESS=1` (既定 0) のときだけ、取込時に skill を付けた設問をその単元ドリルの科目・単元で記録する
  (skill は kv_settings `ptest_meta:<単元>` = 取込と同じトランザクションで保存)。英語長文の解答は弱点集計に入るが、弱点 TOP3・週次プリントの範囲
  (`_WEAKNESS_TOP3_EXCLUDED_SUBJECTS`) からは英検と同じく外す (推薦プールが無い)。週次レポートの小テスト・科目別にはどちらも入る。
- 取込 API の決まり (この 2 科目): `review` = {protocol `trillion-blind/v1`・日付つきの別々の解き手 3 名・`all_agree: true`} が無ければ 422 で何も書かない。
  ★サーバが見るのは形だけ (自己申告)。解き手の答えと正解の照合・item_hash は手元の検査スクリプト (validate_drill_import.py) が行う。
  まとまり (テストの単元 / 英語長文の set_id) が取込済みなら新しい本文は足さない (`ok:false`・`reason: group_exists`)・同じ要求の再送は
  `already_imported: true` で何も増えない (dedup の指定にかかわらず本文の重複を見る)。入れたら events `grammar_import_review` (盲検の要約・名前なし)。
- 取り込んだ後の直し方: 解説・単元は同期 (`/api/admin/grammar/sync`)。選択肢・正解は配る前なら同期、配った後は止めて (retire) 新しい ID で入れ直す。
  テストは revision を上げて「第N回改1」。本文を直すときは新しい pid / set_id (本文の重複判定は active を見ない)。
- 手元の道具 (`scripts/drill_import/`・README あり): `validate_drill_import.py` (検査・`--make-blind` で盲検のシート・解答用紙の照合 =
  item_hash で直した後の盲検を無効にする・0 始まりで書いた解き手を止める) と `import_drill_file.py` (既定は試運転・`--apply` で本番へ・
  入れた後に読み返す・git と seed-data の中のファイルは拒否・秘密は `~/.ai-juku-cron-secret` (0600) を表示しない)。
  ★塾長のデスクトップ `~/Desktop/📝 模試・演習/習熟度テスト/_tools/` に写して単体で動かす (Python 3.9 標準ライブラリだけ・`python3 -I`)。
  そのためサーバの単元表を `SERVER_TABLES` に写して持つ → **単元・科目・テストの単元名の形を変えたら同じ commit で写しも直し**
  (`test_drill_import_parity.py` が落ちる)、デスクトップの `_tools/` にも写し直す。公開リポジトリに取込ファイルが入ったら
  `check_no_test_keys_in_repo.py` (run_all_gates) が落とす (fixtures は架空・`_fixture: true` だけ可)。
- 画面: CEO ① 科目に 📖 英語長文・🧪 習熟度テスト (在庫 0 の単元は「本文0本」)。テストは ④ を隠して「テスト全体 (大問N・全M問) を出題順のまま配信」・
  単元チップ「🧪 大問N・M問」・本数 / 問題数 / 弱点対策の除外を送らない・飛ばした生徒 (`already_taken`) の名前を出す・409 は黄色・分析に 🎯 弱点対策は出さない。
  学年の確認 `_gdGradeMismatchText(subject, students, unit)` はテストだけ単元名の頭で分ける (「中学…」= 中学生だけ・それ以外 = 中学生・小学生に確認)。
  塾生アプリ (`gdMetaText`) とマイページのカードは「授業の指示どおりに解いて提出 ・ 提出は1回だけ」(「いつでもOK」と書かない)。
  ★ラベル表は 7 か所 (ceo.html 4・class.html・mypage.js・mypage.html)。科目を足すときは全部に足す (`test_proficiency_test_import.py` [14] が見る)。
- 回帰テスト: `scripts/health_check/test_english_long_drill.py`・`test_proficiency_test_import.py` (CI `server-tests.yml`・[14] は画面のコードを JS エンジンで動かす)・
  `test_auto_delivery_shared.py` の [10]・`test_drill_import_parity.py`・`scripts/drill_import/validate_drill_import.py` の自己検査 (run_all_gates)。

### 📐 高校数学ドリル (科目 `math`) のシード (2026-10-06 塾長「数学教材は使える？」→「1→2でやって」)
- 科目 `math` は前から canonical (server 変更なし・単元の許可リスト無し)。これまでは「システム側で取込済み」で補充ボタンが無かった
  (exam_questions を分解した在庫。単元が粗い)。**シードは `seed-data/math_drill_*.json`**、ボタンは `#mathPoolImportBtn`
  (`mathPoolImport()`・`data-seed` はカンマ区切りで足していく・400 問ずつ POST・dedup・無課金)。
- **単元名は入試道場の単元タイル (dojo-drill.html の `topic`) と同じ文字列** (「数学I 数と式」「基礎数学 二次関数」「数学B 統計的な推測」…)。
  ドリルの解答は `question_attempts.topic = 単元名` で記録され、弱点の「コーチの一手」(findPresetForWeakness) から道場の同じタイルが開く。
  ★ただし道場は小問ごとの単元タグ (「二次関数(最大最小と平方完成)」など) で記録するので、**弱点の行は道場の分と別に並ぶ** (集計は topic の完全一致)。
  math は server に単元の許可リストが無いので、綴りは形式ゲート `scripts/check_math_drill_seed.py` が dojo-drill.html の topic と照合して止める
  (dojo-drill.html が無ければ落ちる)。単元配信は 5 問から (server が count を 5 以上に丸める) → 5 問未満の単元はゲートが表示する。
- **数式は `\( \)` の LaTeX** (mypage は KaTeX + math-wrap.js、class.html も `\(` があれば KaTeX を読む)。x² ≦ などは文字のまま。
  素の √ を残すと、同じ文字ノードに `\(` があるとき math-wrap が包まない (math-wrap.js は `\(` を含むノードを飛ばす) → √ も全部 `\sqrt{}` にする。
  CEO の 👀 問題を見る と 📊 問題別の分析 も数式を描く (`_gdPreviewMath`: 数式があるときだけ `/vendor/katex/` の KaTeX 0.16.11 を読む
  (jsdelivr は端末によって届かない)・10 秒で打ち切り・区切りは `\( \)` と `\[ \]` だけ = 英文の $ は数式にしない)。`$` はシードに書かない (ゲート)。
  本文 (passages) は gd-nomath で数式を描かないので、数学は 1 問完結の単発で入れる (設定文を各 stem の先頭に付け、行は `\n` で分ける)。
  ★mypage の問題文は 2026-10-06 から `white-space:pre-wrap` (それまでは改行がつぶれて「y = 1/x」と次の行の「x² + y²」がつながって読めた)。
  ★mypage の復習カードの鍵は `('英語__' + 問題文と選択肢).slice(0, 200)` → 設定文の長い math は先頭 200 字が同じになる (統計の 3 問は 244 字まで同じ)
  ので、**200 字で切れる math だけ question_id で鍵を分ける** (`_longMathQ`。英語・中学・英検の鍵は変えない = 既存のカードを孤立させない)。
- 第1弾 `math_drill_ct_mock_v1.json` = 共通テスト数学 第1回・第2回オリジナル模試 122 問 (変換 `scripts/math_drill/build_math_ct_mock_seed.py`:
  生成元の reportlab 部品を記録用に差し替えて問題冊子の組み立てを走らせ、設定文→設問の並びを読む。独自記法 [[f|]] [[v|]] [[o|]] <sub> を LaTeX に)。
  直した点は builder の表に理由つき: PROMPT_FIX (第2回の短い設問文)・CONTEXT_FIX (第2回で R(k)・ゴンドラ・p が未定義)・EXPL_FIX (「前問」参照)・
  CHOICE_SET (誤答が正解の一部だけを変えた 13 問を 2×2 に組み直し。`scan_choice_convergence.py` の手がかり 16 → 3 = 偶然の水準・残りは分数 1 つの誤検出。
  さらに数値の選択肢で正解が「2 番目に大きい値」に 45% 偏っていた → 6 問の誤答を典型的な誤りに入れ替え。表示位置の巡回では値の順位は変わらないので、
  ゲートが正解の順位も 40% 以下か見る)。検証: 盲検 3 名 × 全 122 問 (文や選択肢を直した 35 + 13 + 6 問はやり直し) で全問一致・変換の照合 2 名・
  KaTeX strict で全数式を描画確認・コミット前 3 観点レビュー。
- 第2弾 `math_drill_workbook_v1.json` = 塾の問題集 8 冊 (基礎徹底 数I・数II・数A・数III系 / 問題演習テキスト IA・IIB・IA第2集・IIB第2集。
  生成元は `scripts/math_workbook/content_*.py`) の 650 問 (45f53ec で 675 問を出し、2 冊の重複 25 問を外した)。
  抽出 `scripts/math_drill/extract_workbook_items.py` (`extract()` はファイルを書かない) → 組み立て `build_math_workbook_seed.py`。
  ★**入れない冊子**: 基礎徹底「数列・確率・ベクトル」と「数学IA 弱点発見トレーニング」は自己採点シート＋診断キーと組の診断用 (先に見せると診断が効かない)。
  証明問題と図が無いと解けない問題 (箱ひげ図の読み取り・碁盤目の道) も入れない。
  元は記述式なので、**誤答 3 つと注記は `scripts/math_drill/data/workbook_choices.json`** (id = 冊子:単元番号:問番号。元の問題文と答えのハッシュ
  `stem_hash` / `answer_hash` で結ぶ = 問題集の問題文か答えを直したら builder が止まる)。builder は sympy で「正解の値 = 元の答え av」
  「誤答 ≠ av」「4 つの値が互いに違う」(直線・円の式は定数倍、1 変数の不等式は解の集合で比べる) を確かめ、照合できないまま通さない
  (av の形が違う 31 問は `AV_SHAPE_CHECKED` に目で確かめた記録)。解説は元の解説 + 【よくある誤り】(誤答ごとの誤り)。
  単元は問題集の章 → 道場の topic (`UNIT_MAP`)。★新課程とずれる章は `UNIT_FIX` で付け替え (3 次の展開・因数分解・対称式 → 数学II 式と証明、
  座標で重心・外心・垂心 → 数学II 図形と方程式、複素数の計算と剰余の定理 → 数学II 複素数と方程式、集合の要素の個数 → 基礎数学 確率 (数学A)。
  期待値は新課程で数学A に戻ったので 基礎数学 確率 のまま・確率変数 E(X) は数学B)。道場にタイルが無い「数学II 複素数と方程式」は
  ゲートの `EXTRA_UNITS` に明記 (弱点の「コーチの一手」は道場の通常メニューに落ちる。タイルを足すには道場の在庫が要る)。
  ★2 冊に同じ問題 (言い回しだけ違う) が 24 組 + 2 問を 1 問にしたもの 1 → `SAME_AS` / `DROP` で外し、`_meta.retired_sources` に載せる (下の同期で本番は active=0)。
  原則 問題演習テキスト側を外す (kIII:1:3 だけは中身が数学II の計算なので基礎徹底側を外した)。1 回目のレビューで 23 組、2 回目でさらに 2。
  ★**鮮度ゲート `scripts/math_drill/check_workbook_seed_fresh.py`** (run_all_gates が拾う): 問題集・workbook_choices.json・builder の表を直して
  builder を回し忘れると落ちる (メモリ上で組み直してシードと突き合わせる。`_meta.created` は固定値)。
  検証 (2026-10-06): 盲検 3 名 × 675 問で全員一致 (欠陥の印 2 問)・元の問題集との照合 10 名 (指摘 33 件) → 27 問を直して再盲検 12 問。
  コミット前 3 観点レビュー (45f53ec の後) → 重複 23 組・解説の生の記号 57 問・復習カードの崩れ 14 問・単元の付け間違い 3・正解の順位の偏り 3 単元など。
  ★**誤答の注記 1,935 件を総点検** (10 分割 × 書き手 + 別の確かめ役): 誤りの中身を直した 31・確かめ役の訂正 13・どの誤りからも出ない誤答 5 (3 問) →
  選択肢を作り直し。数式は全部 `\( \)` に入れた (数式の外の ^ や √ は mypage で生の記号のまま出る)。
  ★2×2 の誤答は「誤り A × 誤り B」の組でないと、片方のマスが「どの誤りからも出ない値」になる (注記を書かせると見つかる)。
  正解の順位が単元の中で偏っていた 9 問 (数学I 数と式・数学II 複素数と方程式・基礎数学 三角関数) は誤答を作り直した。選択肢を変えた問題は全部盲検をやり直した。
  ★形式ゲート `scripts/check_math_drill_seed.py` に足したもの: 前後の問を指す言い回し (自己テストつき・「以下の問いに答えよ」は通す)・
  問題文で定義していない (ア)〜(エ)・数式の外の LaTeX の記号・図への言及 (抽出と同じ `FIGURE_REF` を読む。「下図」も)・
  数値の正解の順位を単元ごとにも (6 問以上の単元で 50% 以下。分数・根号・π も数値として読む)・止める問題がシードに残っていないこと。
  在庫は①②合わせて 772 問・1 単元 10〜69 問 (③既定の標準〜やや難では 6〜49 問。数学III 極限 6・積分法 9)。level は 基礎 191・標準 457・やや難 124 (第1弾は全問標準)。
- ★**取込済みの問題を直すのは同期 API `POST /api/admin/grammar/sync`** (2026-10-06)。取込は INSERT 専用で、押し直しても解説・単元は変わらない
  (45f53ec の 675 問は塾長が取込済みだった)。CEO の 📐 数学・🏅 英検 語彙ボタンは **同期 → 取込** の順 (共通の `gdSyncSeed`)。同期は
  **(subject, source, stem) で照合**して unit / explanation をシードに合わせ、choices / answer は**まだどのドリルにも入っていない問題**と、
  **配信済みでも正解の文と位置が同じで、提出済みの解答が選んだ番号の文も変わらない問題** (誤答の差し替えだけ = 採点も過去の解答の表示も変わらない。
  解答は answers_json に番号で残るので、選ばれた誤答を差し替えると振り返りと CEO の選択肢分析が別の文に化ける) を直す。それ以外の配信済みは据え置き
  (`kept_choices_delivered`。★解説の【よくある誤り】は誤答ごとなので、選択肢を据え置いた問題は解説も据え置く)。
  ★**stem を必ず送る**: 英文法・中学の在庫は source が束ごとの名前 (`manual-drill-v1` が 703 問) なので、source だけで照合すると別の問題を
  まとめて書き換え/止めてしまう → stem 無しで問題文の違う生きている行が複数あれば触らない (`ambiguous`。取り外しも同じ)。並びだけ違う
  (同じ 4 つ・同じ正解) のは書き換えない。`retire_sources` は active=0 (行は消さない・配信済みのドリルでも出なくなる。採点は提出時の active な問題で)。
  同じ (source, stem) の生きている行が 2 つ以上なら二重に入った同じ問題 → ドリルに入っている行 (無ければ id の小さい行) を残して active=0 (`deduped`)。
  `retire_sources` は source か {source, stem} (作り直した問題の旧版だけを止める)。応答の `match: "source+stem"` が新しい照合の印:
  ★CEO の `gdSyncSeed` は最初に書き込まない試し (dry_run・空) を送り、この印が無ければ「サーバの反映待ち」で同期も取込もしない
  (Vercel が Railway より先に出るので、反映待ちの間は baace27 の source だけで照合する同期が 200 を返す → 作り直した問題の旧版と新版を取り違える)。
  stem は変えない (取込の重複判定の鍵)。pool のような汎用の source は触らない。dry_run あり。
  ★取込 (/api/admin/grammar/import) も、汎用でない source と同じ問題文の行があれば単元が違っても skip する (2026-10-06)。単元を直したシードを
  同期より先に取り込んでも (古い CEO タブ) 二重に入らない。シード 8,979 問に「同じ source・同じ問題文で単元だけ違う」問題は無いことを確かめた。
  回帰テスト `scripts/health_check/test_math_drill_sync.py` (CI の server-tests に登録)。
- ★**弱点ルーティン (3 日ごと・環境変数 `WEAKNESS_DRILL_ROUTINE_ENABLED`) は math を「科目まるごと」で配る** (`_SUBJECT_LEVEL_DRILL`・
  標準+やや難から 10 問)。★2026-10-15 から**出典が `mathct-*` / `mathwb-*` (このシード) の行だけ** (`_auto_pick_reviewed_question_ids`)。
  exam_questions を分解した古い数学の行は自動では出ない (CEO で手で配るのは今までどおり)。
  ★2026-10-06 塾長「数学Ⅲは自動配信は外して」→ ルーティンの科目まるごとでは **数学III の単元を出さない**
  (`_ROUTINE_SUBJECT_LEVEL_EXCLUDE_UNIT_PREFIXES`・抽出の `exclude_unit_prefixes`。数学III を除いて 10 問に足りなければ
  その弱点は配らず次の弱点へ)。★数学III の弱点 (topic が「数学III」で始まる) は `_weakness_routine_pick_drills` が候補にしない (数学の候補にすると
  数III を出せない数学ドリルが毎回選ばれ、数III の弱点は測り直されないまま先頭に残り、ほかの科目の弱点が配られない)。
  CEO で単元を選ぶ配信と、塾長が押す 📨 弱点ドリル (科目まるごと) は除外しない (数学III も出る)。数学C は除外していない。
  「数学III」「数学Ⅲ」「数III」「数Ⅲ」で始まる単元だけを外す。
- 生徒の復習カード (learning-brain の `_parseChoices`) は問題文中の「(1)」「(ア)」(f'(1)・3 進法の _{(3)}・作図の手順) を選択肢の印と取り違える →
  mypage.js `_gdSyncResultsToReview` がカードの文だけ「( 1 )」に開く (鍵は開く前の文のまま)。★残件: learning-brain.js の見出しは 100 字で切るので
  数式の途中で切れると生の LaTeX が見える (問題集の 4 割)。learning-brain.js は index.html / english-exam.html など 5 枚が読み、?v= を全部上げる必要がある。
- CEO の ①「数学」の単元チップは教科書の順 (`_GD_MATH_UNIT_ORDER`: 数学I → A → II → B → C → III。表に無い単元は後ろ)。

### 中学の他教科 (数学・国語・理科・社会) は教科ごとの別科目 (2026-09-28)
塾長「さらに中学生用の問題を追加して」→ 数学・国語・理科・社会を1教科ずつ。まず **中学数学 `chugaku_math`**
(`seed-data/chugaku_math_pool_v1.json`・ボタン `#chugakuMathPoolImportBtn`)。
- ★**プールは教科ごとに分ける (`chugaku_math` …) が、生徒の解答は `subject='chugaku'` に記録する**
  (`_drill_attempt_subject`)。入試道場も中学5教科を `chugaku` の1バケット＋`topic=単元名` で記録していて、
  弱点・週次プリント・弱点 TOP3 はその前提で組まれている。`chugaku_math` で記録すると、中学生の弱点プリントの対象
  (`subject='chugaku'`) から外れ、同じ「正負の数」の弱点が入試道場とドリルで別々に数えられてしまう。
- 単元名は `scripts/chugaku_dojo/units.json` の各教科の `filter` と**完全一致**させる (弱点 topic の突き合わせ)。
  並び順は `_GRAMMAR_SUBJECT_UNIT_ORDER['chugaku_math']`。国語の読解2単元 (説明的文章・文学的文章) は本文つきなので別扱い。
- ★**画面に図は出せない**ので、図形は条件をすべて文章で書く (「図のように」は禁止)。数式は高校数学プールと同じく
  `x²` `√2` `−3` の記号で書き、`$` や `\(` の区切りは書かない。マイナスは「−」(U+2212) にそろえる。
  ただし **mypage の単元ドリルは `math-wrap.js` が `√数字`(小数も) と `≦ ≧ ≤ ≥ ≠ ≒ ≈ ± ∞`・裸の `\frac` `\sqrt` `\geq` 等を
  KaTeX に載せる** (class.html は素の文字)。
  `√0.25` が `√0` と `.25` に割れていたのを 2026-09-29 に直した (小数まで丸取り)。√ の中が式なら `√(12/27)` とかっこで書く。
- 形式ゲートは `scripts/check_chugaku_drill_seed.py` (中学英語・中学数学・中学理科・中学社会・中学国語を1本で見る)、回帰テストは
  `scripts/health_check/test_chugaku_math_drill_pool.py` (CI の server-tests に登録済み)。
- 次の教科を足すときは、`_GRAMMAR_CANON_SUBJECTS`・別名・ラベル・`_GRAMMAR_SUBJECT_UNIT_ORDER` に1行ずつ、
  CEO の科目選択と補充ボタン・CEO のラベル表 2 つ (学年ミスマッチの確認に出る `_gdGradeMismatchText` の `_subjJa`・配信済みドリルのチップと 🎯 確認カードの `_GD_SUBJ_JA`)、
  CEO の配信済みドリル一覧の科目の絞り込み (`gdListSubject` の選択肢。無いと `test_weakness_routine_auto_delivery.py` が落ちる)、
  CEO「やるべきこと」の `_CHU_DRILL_UNITS` / `_CHU_DRILL_LABEL` と `scripts/check_ceo_chugaku_drill_links.py` の `DOJO_SUBJ`
  (無いとその教科の弱点に 📨 が出ない。ゲートが落ちて教えてくれる。クラス宿題でも出すなら、ゲートの `HW_SUBJS` に教科を足し、
  道場のカードを 1 枚ずつ `HW_DRILL_TOPICS` に `s: 'chugaku'` で足す — これもゲートが見る)、
  生徒画面のラベル表 (`class.html` の `GD_SUBJ_JA`・`mypage.js` の `_SUBJ_DRILL_LABEL` と復習カードの `_lbSubj`・mypage.html の `?v=`) を足す。★補充ボタンは `data-subject`/`data-label`/`data-seed`/`data-size`
  を持たせたうえで、**ラッパー関数 (`chugakuMathPoolImport` と同じ形) と DOMContentLoaded の `addEventListener`・`window.` への公開も要る**
  (取込の中身 `_chugakuSubjectImport` だけが共通。これを忘れると押しても何も起きない)。
  形式ゲート `scripts/check_chugaku_drill_seed.py` の `SEEDS` と、回帰テスト `test_chugaku_math_drill_pool.py` の `SUBJECTS`
  (ファイル名は数学のままだが、中学英語以外の教科別ドリルをすべて回す) にも1行ずつ足し、CI (server-tests.yml) の paths にシードを足す。
- 弱点のキー `_weakness_subject_key` は `chugaku*` を `chugaku` に寄せる (提出時の記録科目とは別に、集計側でも1バケットを保証)。
  回帰テストは入試道場と同じ形の記録と合算されて1行になることまで見ている。
- **中学理科 `chugaku_rika` (2026-09-29)**: 入試道場の rika と同じ14単元。★画面に図・表・グラフは出せないので、実験は
  **条件と結果を1段落の文章で書く** (「図のように」「表1」「グラフから」や本文の改行はゲートで弾く)。用語は2021年度からの教科書に合わせ
  **顕性・潜性** (優性・劣性は旧用語として弾く)。高校範囲の語 (物質量・電気陰性度・運動量・比熱・同位体・フレミング など) も弾く。
  英語 v4 で盲検と単元内の点検を素通りした「名前だけ入れ替えた同じ枠」を防ぐため、生成の最後に**重複点検**の工程を入れ、
  1単元70問 (標準+やや難 60) 作って外しても標準+やや難が 50 を切らないようにした。
- ★**全教科: 組み合わせの選択肢は 2×2 にする。** 理科の独立レビューで「誤答が正解の一部だけを入れ替えたもの」(各要素でいちばん
  多く出る値を拾うと正解) が見つかった。2要素なら各値がちょうど2回ずつ出る 2×2 (3要素以上もどの要素でも正解の値が単独最多にならない)。
  社会は作問ルールに入れ、2要素の組み合わせ約150問はほぼすべて 2×2。英語・数学・理科はルールより前に作ったので、2026-09-30 に
  **`scripts/scan_choice_convergence.py`** (読むだけ・ゲートではない。引数なしで5教科) で洗い、英語24・数学35・理科47・社会1・国語1問の
  選択肢を作り直して盲検3名に通した。理科は独立レビューが挙げた22問 (直したのは21問) のあとに、同じ癖がさらに26問あった
  (機械で20問・機械では拾えない形を目で6問 = レビューも機械検出も網羅しない)。洗った後の「正解が中心」の数は、英語・理科・社会が
  偶然の水準 (誤答を仮の正解にしたときの数) 以下、数学と国語がほぼ同じ (数学13/12.7・国語5/3.3)。残る当たりは拾いすぎ (同じ語が2か所に
  出る 2×2・確率などの分数1つの答え・相似条件の一覧 など)。カエルの発生の並び1問は機械では拾わないが同じ癖があり、本文が両端を
  決めるので 2×2 にすると要点の「胚→幼生」の順を問えなくなる → 元のまま残した。
  ★作り直しで実際に出た新しい癖 (盲検は通るのでレビューでしか見つからない): 一目で消せる誤答 (本文で与えた点や直線そのもの・
  「気体は試験管の外に出た」と書いたのに「銅と二酸化炭素」・理由が結論と矛盾する組・符号だけで消える式) は、それを消した残り3つで
  正解がまた多数派になる。正解だけ形が違う (誤答だけ「〜の活動」・正解だけ係数 1 の化学反応式・正解だけカタカナ) も同じ。
  2×2 でも、どの誤答も本文と知識を使わないと消せないものにする。時制の単元で be 動詞の時制をそろえると時制を問わなくなる、にも注意。
  同じ日に社会の5問も直した (X・Y 正誤の3問が正解「X正・Y誤」にそろっていた・本文の「〜経済」「〜活動」を含む選択肢が正解だけだった)。
  ★英語・数学・理科・社会は本番に取込済みなので、本番の行も同じ内容に書き換える必要がある (取込は同じ問題文を飛ばすので、選択肢だけ
  直してもボタンでは本番に届かない。配信済みドリルに入っている行は書き換えない)。国語は未取込だったのでシードだけで足りる。
  ★**正解だけが長い**も同じ種類の手がかり。社会 v1 は生成直後、単独最長の選択肢がある問題のうち45%でそれが正解だった。
  目立って長い91問のうち重複で外した3問を除く88問を作り直して30%にした (単独最長が無い問題も含めた全体では約15%)。
- **中学国語 `chugaku_kokugo` (2026-09-29)**: 入試道場の kokugo のうち本文を使わない6単元 (漢字・語句・文法・敬語・古文・詩歌)。
  読解の2単元 (説明的文章・文学的文章) は本文つき (長文型ドリル) で、書き下ろしの本文が要るので入れていない。
  ★**下線は class.html に出せない** (mypage は `<u>` を復元するが class.html は素の文字) ので、問う語句は **〔 〕** で示す。
  引用は古文・漢文と、没後70年を過ぎた作者 (芭蕉・蕪村・一茶・子規・啄木・晶子・賢治 など) か自作だけ。現代語訳は自分で書く。
- **中学社会 `chugaku_shakai` (2026-09-29)**: 入試道場の shakai と同じ11単元 (単元名に半角空白を含む: 「歴史 古代」など)。
  ★**年によって変わる統計・順位を正解にしない** (生産量の県別順位・国別の人口や貿易額の順位など。茶は静岡と鹿児島が年で入れかわる)。
  数値が要る問題は問題文で数値を与える。制度は現在の教科書どおり (選挙権・成年年齢18歳・衆議院465・参議院248・消費税10%)。
  地図・資料・写真・年表への参照はゲートで弾く。表記が分かれる歴史用語は併記 (大和政権（ヤマト王権）など)。
- **CEO「やるべきこと」の 📨 弱点ドリル** (2026-09-29・社会/国語は 2026-09-30): 高校入試演習 (`chugaku`) の弱点は topic の単元名で振り分ける
  (`_chuDrillFor`: 中学英語の単元 → `chugaku`・中学数学 → `chugaku_math`・中学理科 → `chugaku_rika`・中学社会 → `chugaku_shakai`・
  中学国語 → `chugaku_kokugo`)。国語の読解 (説明的文章・文学的文章) と、道場にしか無い英語の単元 (過去形・未来形・不定詞の用法・長文読解) は
  従来どおり「対象外」(ゲートの `DOJO_ONLY`)。
  - ★**前置きつきの行「中学数学 正負の数」はボタンにしない**。AIありの生徒が宿題の「📝 ドリルで解く」から解くと、道場が同じ解答を
    元の単元名でも記録する (`dojo-drill.html` の `drillOrigin`) ので、前置きなしの「正負の数」の行の写しになる。単元ドリルの結果は
    「正負の数」にしか入らないため、写しでボタンを出すと克服しても最長 4 か月ほど出続ける (30 日で退役 → 退役弱点として 90 日、
    の窓から算出・review で指摘)。ボタンは前置きなしの行に任せる。写しの行そのもの (弱点一覧・TOP3 に同じ単元が 2 行出る) は道場側の未対応。
  - ★**中学ドリルのボタンは学年が中学か、判定できない (未設定・その他・「社会人」のような自由入力) 生徒にだけ出す** (`window._gdMode`)。
    入試道場の中学タブは誰でも解けるので高校生にも高校入試演習の弱点が立ち、ボタンにすると上限 5 個の枠を高校の科目から奪っていた
    (review で実測)。学年が高校・小学と読める生徒のカードは従来と 1 文字も変わらない (学年の判定の student-mode.js が読めないときも出さない)。
    並びは学年に合うボタンが先: 中学生は中学ドリルが先頭、判定できない生徒はほかの科目のボタンの後ろ。
  - chugaku は5教科の1バケットなので、中学ドリルがある生徒は注記を消さず「高校入試演習のうち「説明的文章」「過去形」…」と単元名を
    別の注記で出す (前置き・かっこの補足を外して二重に数えない)。📨 も 📤 と同じ学年の取り違えガード
    (`_gdGradeMismatchText`・`window` 経由) を通り、学年が合わないときは ⚠️ と「それでも…配信しますか？」でいつもの確認と見分ける。
    判定できない学年の生徒に中学ドリルを送るときも ⚠️ (その生徒の画面は高校生モード。生徒詳細の「学年」の横の「✏️ 編集」へ誘導し、
    学年を直すとその生徒の 📨 が持つ学年 (`data-grade`) も差し替える。★一覧は読み直さない: 読み直すと押した「✅ 配信済」が 📨 に戻り、
    同じドリルを二重に配りうる (`grammar-drill/create` に重複の防止は無い。お知らせはアプリ内表示・メールは `HOMEWORK_NOTIFY_EMAIL` 次第)。
    ボタンの並び・中学ドリルの有無は 🔄 で反映)。
    ★**学年の判定は 1 つの規則** (2026-10-15): 全角・漢数字・ローマ数字 (「中２」「中三」「中Ⅲ」「小６」「高二」) は半角にそろえてから読む。
    サーバ `_normalize_grade_numerals` ↔ student-mode.js `ajNormGrade` (同じ表) を `_student_mode_from_grade` (表示用 3 値・未知は kosei)・
    `ajStudentMode`・ceo.html `_gdMode` が通す。自動配信は 4 値の `_student_grade_band(grade, *, unknown_as_kosei=False)`
    (`shougaku`/`chugaku`/`kosei`/'' = 判定できない。`_GRADE_KNOWN_RE` は `_gdMode` と同じ) と `_student_chugaku_year` を使い、
    別の学年パーサを書かない (NFKC は「中三」を直さない)。「中高一貫 高2」は高校。テスト `test_grade_band_consistency.py` が
    約 30 の学年をサーバ・student-mode.js・`_gdMode` (JS を node / osascript で実行) で突き合わせる。
    ★student-mode.js を変えたら、読む 5 画面 (mypage / ceo / dojo-drill / mock-exam / ai-tutor-photo) の `?v=` を全部同じ値に上げる
    (テストが同じ値かを見る)。「中２」などの生徒はこの変更でマイページが中学生モードに切り替わる。
  - クラス宿題のドリル単元 (`HW_DRILL_TOPICS`) に中学数学15単元を足した (科目は英語と同じ `chugaku`。理科・社会・国語の宿題単元はまだ無い)。★**クラス宿題には学年の
    取り違えガードが無い** (英語の頃から)。英検2級/準1級対策のクラスは中3と高校生が混ざるので、クラス単位で確認を出すと毎回出る。
  - ゲート `scripts/check_ceo_chugaku_drill_links.py` (run_all_gates が拾う・material-gates CI): `_CHU_DRILL_UNITS` は server の
    `_GRAMMAR_SUBJECT_UNIT_ORDER` と、`_CHU_DRILL_LABEL` は道場の topic の前置きと、道場の中学5教科のカードの filter は server の
    単元 (道場だけの単元はゲートの `DOJO_ONLY`) と、`HW_DRILL_TOPICS` の中学の行は道場のカードの topic と照合する。ゲートの `HW_SUBJS`
    (英語・数学) のカードは 1 枚ずつ `HW_DRILL_TOPICS` にも要る。`HW_DRILL_TOPICS` の行は大学の行も含めてキーが `t` / `s` の 2 つだけ
    (キーを足すとゲートが落ちる)。同じ topic のカード 2 枚・単元名のかっこ/コロンも落とす。
    JS はコメント・文字列・テンプレート (入れ子の `${…}` も追う)・正規表現リテラルの中身を空白にしてから読む (`js_mask`。コメントの中の
    `/api/…/*` や入れ子のテンプレートの `</b>` で「以降は全部コメント/文字列」と誤読していた = review 3・4 巡目で実測。空白にした後も
    ceo.html 16 本・dojo-drill.html 1 本の script が JS として読めることを確かめた)。コメントアウト・宣言の二重化・変数・宣言の後からの
    書き換え (JS: 再代入/代入/push/push.apply/delete/Object.assign/同じ `{…}` の中の `var x = NAME`・`var u = NAME.k` (`|| []` つきも)
    の別名から、server: 再代入/global/別名/del/update・append 等/`NAME[k]`・`.get()`・`.get() or []`・`.items()` の別名から (内包表記の変数は
    その式の中だけ)・`NAME[k][:] =`) は「読み漏れ」として落とす (`NAME[k][:]` の写しは通す)。★見ていない: 要素のプロパティをコールバック
    で書き換えるもの (`forEach(x => x.s = …)`)・別名の別名・分割代入/三項演算子/for-of の別名・eval・テンプレートの `${…}` の中・
    server の `NAME[k] if … else []` の別名・書き換える関数に `NAME[k]` を渡すもの・外側 (モジュール直下・外側の関数) で作った別名を内側の
    関数/lambda で書き換えるもの。
    逆に宣言を `Object.freeze({…})` で包むもの・引用符つきのキー・IIFE 直下の `var units = NAME…` (同じ IIFE の別の `units.push` まで拾う) は落ちる
    (メッセージで分かる。別の文の `Object.freeze(NAME);` は書き換えではないので通る)。
    変異 72 種 (壊す 56 種を検出・正しい書き換え 16 種は通す) で確認。

### 検査は `scripts/run_all_gates.py` に寄せる (2026-08-04)
- **教材の全ゲートを回す入口は 1 本**: `python3 scripts/run_all_gates.py` (絞るなら `... rika_kagaku`)。
  `scripts/` 以下を**再帰**で探して `check*` / `verify*` / `validate*` / `audit*` / `qa*` / `*_gate` を実行し、
  最後に `check_no_pii.py` (個人情報) も回す。CI (`material-gates.yml`) も同じコマンド。現在 49 本。
- ★**引数で検査対象が変わるゲートを引数なしで回すと「見本」を検査して緑になる**。実際に
  `kaki_koushuu_eng/check.py` が 1 講しかない `sample_content` を検査して ALL PASS を出しており、
  刷る 2 冊が無検査だった。**引数なしの既定は「刷るもの全部」**にし、何を見たかを必ず印字すること。
  ランナーは argv を読むゲートを一覧に出す (`? ...` の行) ので、そこは出力で対象を確かめる。
- **新しい検査を書いたら、必ずコミットする**。2026-08-04 に調べたら `scripts/` の .py 201 本が未追跡で、
  検査スクリプトが一度も git に入っていなかった。作ったその場でしか動かず、次に同じ教材を作るとき同じ穴を掘り直していた。
- ★**ルールの置き場所はリポジトリの中に限る**。`.claude/` は `.gitignore` 対象で**コミットできない**ので、
  そこに置いたフックや設定は次のセッションに残らない (README に「Stop フックが強制する」と書いてあったが実体が無かった)。
- ランナーが落とすもの: 違反検出 (VIOLATION) / **ゲート自体が壊れた (CRASH)** /
  **書いたのに誰も呼んでいない検査 (DEAD)** / **exit 0 なのに違反を印字している (INCONSISTENT)**。
  ★どれも「通った」ではない。検査していないだけ。`sys.exit(1)` の書き忘れ 1 行でゲートは無力化される。
- 刷った PDF を読む検査は CI では回せない (PDF は生成物でリポジトリに無い)。CI は `--no-pdf`。
  **紙の検査は手元で build 後に `--no-pdf` 無しで回す**こと。外れた分はランナーが一覧に出す。

### ★このリポジトリは PUBLIC — 生徒の氏名を書かない
- `github.com/shock11090304-a11y/ai-juku-system` は**公開**。氏名を1行書いてコミットすると即公開され、
  **履歴に永久に残る** (消すにはリポジトリ全体の履歴書き換えが要る)。「あとで直す」が効かない。
- **宛名はコードに書かない**。`STUDENT = os.environ.get("STUDENT_NAME", "")` にして、
  刷るときだけ `STUDENT_NAME="姓 名" python3 build_xxx.py` で渡す。空なら宛名なしの汎用版。
- 個人あての資料 (指導メモ・面談記録・カルテ) は `.gitignore` 済み。リポジトリに置かない。
- 機械で止める: `python3 scripts/check_no_pii.py` (CI の `material-gates.yml` が回す)。
  既知の検出 (事業者自身の連絡先・教材本文の架空アドレス) は `scripts/_pii_baseline.txt` に記録済みで、
  落ちるのは**新しく入ったものだけ**。★生徒の氏名・連絡先を baseline に足して黙らせてはいけない。
- ★**中身の走査だけでなくファイル名も見る**こと。2026-08-04 に氏名入りのファイル名を見落としかけた。

## Vercel は Pro プラン (2026-07-18 に Hobby から移行済み)
- 商用利用の規約準拠 + B2B(学校導入)前提で Pro 化 ($20/月・$20分の従量クレジット込み。現使用量は枠内に余裕)。
- **旧「12 Serverless Function 上限」は解消済み**: Hobby 固有の上限だったため、`api/*.py` の個数で Vercel デプロイが失敗することはもう無い (過去3回の本番凍結事故 74e2c5fb / 216d9ac / d59461f は Hobby 時代の話)。
- **アーキテクチャ方針は不変**: API ロジックは Railway 側の `server/main.py` に書く。`api/*.py` は Stripe 等「Vercel でしか動けない」関数のみ (現12個が基準値)。
- `scripts/check_vercel_function_cap.sh` と CI (`.github/workflows/vercel-function-cap.yml`) は基準値超過を**警告するだけの非ブロッキング**(常に exit 0) に変更済み。正当に関数を増やしたときは同スクリプトの `BASELINE` を実数に更新して警告を止める。
- 既存の `__ep` action 同居 (例: `admin-charge-month-end-preview` / `admin-charge-history` は `admin-charge-readonly.py` に同居) はそのまま稼働中・触らない。新規に Vercel 専用関数が本当に必要なら素直に足してよい (同居の曲芸は不要になった)。
- 本番が古いままの症状 (新URL 404 / app.js が古い / `gh` の "Vercel" status=failure) を見たら、関数数ではなく Vercel ビルドログと healthcheck の `deploy_freshness` を見る。

## 子供のログイン (子供メール = `students.student_email`)
- 生徒本人が**自分のアドレス**でログインできるようにする設定。CEO 画面 → 生徒詳細 →
  **「子供メール ✏️ 編集」** で入れる (`POST /api/admin/students/{id}/student-email`)。
  塾長が設定した値は `student_email_verified=1` (確認済み) になり、以後ログインコードは
  親 (`email`) と子 (`student_email`) の**両方**に届く。自己登録で入った値は未確認のままで、
  申込メール内「ログインを有効化」(magicv リンク) をタップするまで子には届かない。
- ★**このエンドポイントは子アドレスへ何も送らない**。設定しただけで安心せず、必ず子に 1 回
  ログインさせて実地確認する。届かないときの救済は **CEO 画面 → 生徒名をクリック → 生徒詳細の
  「🔑 ログインの救済」**(2026-09-03 にダッシュボード上部の3つの欄からここへ移設。生徒 ID や
  メールを探さなくてよい)。上から順に:
  ① **ログインリンクを送り直す** (送信 cap も LINE 優先配信も迂回して直送。宛先を変更可) →
  ② **LINE連携コードを発行** (連携すると以後ログインコードが LINE に届く = メール不達の根本解消) →
  ③ **OTP を発行** (コードを画面に出して口頭で渡す)。
  ★③ の OTP は **login.html でメアド照合が要る**ので、メール未登録の生徒には効かない (②か、先にメール登録)。
- ★配信の落とし穴 (2026-08-25 に塞いだ。壊すと「画面は成功・子には0通」に戻る):
  **LINE 連携済みだとログインコードは LINE に飛びメールを送らない**。LINE は生徒行に 1 本しか
  持てず、たいてい保護者のもの。子宛だけは LINE の成否と無関係に必ず別送する。
  親アドレスの受信者 cap (10通/時) も子を巻き添えにしない (cap は受信者単位)。
  逆に**未確認アドレス・他生徒の親メールと衝突するアドレスには送らない**(メール爆撃の踏み台防止)。
  この両方向を `scripts/health_check/test_child_email_login.py` (CI: `server-tests.yml`) が固定する。
- 生徒詳細に **LINE連携** 行がある。「届かない」と言われたらまずここを見る。
- ★**保護者メール (`students.email`) を変える手段は本番に無い**。admin API も CEO ボタンも無く、
  Stripe の顧客メールとも紐づく。切り替えを頼まれたら、まず「子供メールに足す」で足りないかを
  確かめること (親のログインを残したまま子が自分のアドレスで入れる)。
- 子メールを確認済みにすると、**週次レポートの生徒向けコピーの主宛先が親→子に移る**。保護者コピーは
  `students.parent_email` (別列) 宛だが、**`parent_email` が空なら申込メール (`email` = 親) へ送る** (2026-09-09・
  `_weekly_report_recipients` の fallback)。`parent_email` が配管されるのは「生徒用メールを別指定した申込」だけで、
  単一メール申込・Stripe 経由・塾生アプリ承認は NULL のまま (本番 88 名中 16 名にしか入っていない)。
  `parent_email_enabled=0` (明示 OFF) のときだけ保護者コピーを送らない。
  ★2026-09-09 塾長判断で mypage の「保護者向け週次レポート」欄 (`#parentEmailSection`) と「登録すると…」バナーを
  **非表示**にした (`data-aj-hidden="2026-09-09"` + `display:none`)。生徒が自分で `parent_email` を設定する手段は無い
  (上の fallback があるので通常は不要)。必要なら display:none を外す。
- **mypage で 2026-09-09 に非表示にしたもの** (塾長判断・`data-aj-hidden="2026-09-09"` で grep できる): 今月の利用状況、
  次の定期テスト未登録、紹介プログラム (ウィジェットと「友達紹介で双方に特典」の 2 か所)、AIコーチの言葉、保護者メール欄。
  引き継ぎ通知 (`renderInheritNoticeBanner`) は**実際に画面に入った回数** (`aj_inherit_notice_seen:<id>`) を数え、2 回見せたら
  了承扱い。挿入しただけでは数えない (スクロールせず離脱した生徒の「取り消し」の機会を奪わないため)。

## 🔁 生徒ログインの自動延長と LINE「やること」のリンク (2026-10-18 塾長「②の残りも作っておいて」)
- 生徒トークン (`_sign_session_token`・30 日) は、**在籍中の生徒が使っているあいだ自動で延長**する。`GET /api/auth/me` が、残りが
  `STUDENT_SESSION_RENEW_WINDOW_SECONDS` (15 日 = TTL の半分) を切った種別 `session` のトークン (旧 3 パートも) にだけ
  `renewed = {token, expires_at}` を返し (応答は `private, no-store`)、auth-guard.js の `storeRenewedSession` がログインと同じキー
  (`ai_juku_session_token` / `ai_juku_session_expires`) に保存する。保存するのは、問い合わせたトークンが今も保存されていて新しい期限の方が先のときだけ (try/catch)。
- 在籍 = `_enrolled_sql` かつ合成監視・テスト系の名前でない (`_student_session_renewal`)。延長しない: canceled / expired / 体験切れ / 猶予切れの past_due
  (国公立難関大コースで `_get_current_student` が通す生徒も)・なりすまし (impersonation)・講座 / dl / magic。トークンは生徒 id と期限だけ
  (親・子のどちらのアドレスで入ったかは持たない) なので延長しても意味は同じ。ログインコード・OTP・マジックリンク・LINE ログインは不変。管理者は従来どおり `/api/admin/verify`。
- ★auth-guard.js を読む HTML (16 本) は同じ `?v=` にそろえる (テストが 1 つの版を求める)。
- LINE「やること」の返信リンクは全員 `{BASE_URL}/mypage.html?focus=homework&openExternalBrowser=1` (`_LINE_TODO_LINK_PATH`・リッチメニュー A「宿題を開く」と同じ。
  AIなし枠は mypage が `class.html?tab=homework` へ送る)。返信 (reply) だけで push は増やさない。
- 回帰テスト `scripts/health_check/test_student_session_renew.py` (CI `server-tests.yml`・auth-guard.js を JS エンジンで動かす)。

## ⏰ 〆の印と帯・👀 開いたかの記録 (2026-10-18 塾長「②の残りも作っておいて」)
- **〆**: `GET /api/student/grammar-drills` の各 item に `due_date` = クラス自動宿題 (`class_hw_auto:…`) の題名の「〆M/D」を 'YYYY-MM-DD' に
  (`_student_drill_due_date` → 授業ブリーフと同じ `_class_brief_title_due`・年は受け取った日 (JST) から・ほかのドリルは None。**JS で題名を読まない**)。
  判定と文言は hw-notice.js の 1 か所 (`dueState` = JST の今日と日付の文字列で比べる・`dueChipText`・`banner`・`todoLabel(新, 未提出, 〆を過ぎた, 〆今日)`)。
  compute の `overdue` は宿題の期限 + ドリルの 〆 (未提出だけ)・`dueToday`。
  - 塾生アプリ (class.html): カードは「未提出」+「〆今日」(橙 `chip-soon`) /「〆を過ぎました」(赤 `chip-over`)。旧「期限切れ」の状態チップはやめた。
    宿題タブ以外の帯 = `banner()`: 新しい宿題があれば新着の帯に「（〆を過ぎた N 件・〆今日 M 件）」、無ければ〆を過ぎた (赤) / 〆今日 (橙) の帯を
    **「見た」に関係なく未提出が残るあいだ出し続ける** (提出すれば消える)。
  - マイページ (mypage.js): カードのバッジは JST (`_hwJstToday`。旧版は端末の日付)・ドリルのカードにも 〆・📌 要対応チップと欄のバッジに 〆今日。
    hw-notice.js が読めない端末は今までどおり (サーバの宿題の期限切れだけ)。
- **👀 開いた**: events に 1 件 1 行 (`_record_item_open`・表は足さない・DDL なし)。`gd_open` = 単元ドリル (`GET /api/student/grammar-drill/{id}` の中・
  新しいルートなし) / `hw_open` = 塾長の宿題 (`POST /api/student/homework/{id}/opened`・prefix は元から許可 = 許可集合は不変)。session_id = 生徒 ID の文字列
  (統合で移る)・props = {student_id, kind, item_id, last_opened (naive UTC), days} = **ID と時刻だけ**・created_at = 初めて開いた時刻。
  2 回目からは同じ行の last_opened / days を JST の日付が変わったときだけ書き換える (同じ日は書かない)。本人が未提出のものだけ
  (なりすまし・提出済み・今日の1問 / 初回診断・他人の行は記録しない)。`_EVENTS_RETENTION` に載せない (消さない)。書けなくても開く処理は止めない。
  - 画面が /opened を呼ぶのは: 解答用紙を開いた・プリントを開いた・「📝 ドリルで解く」(keepalive)・中身だけの宿題 (単元・プリント・解答用紙なし) が
    一覧に出た (マイページは**そのカード**が半分以上 1.5 秒見えたら = カード 1 枚ごとの IntersectionObserver。宿題欄が見えた・ドリルを開いた
    だけでは送らない = ドリルが上に並ぶと宿題のカードは画面の外で、見ていない宿題が「開いたが未提出」になる・点検 owner-F1。
    IntersectionObserver の無い端末は送らない)。未提出だけ・1 ページ 1 件 1 回・返事は待たない。
    ★マイページは**単元のある宿題も中身だけ**に数える (カードに「📝 ドリルで解く」が無い。class.html の「単元のある宿題は除く」を写すと 👀 未開封 のままになる・点検 F1)。
  - 🗓 授業ブリーフ: 未提出の行に `opened` (True = 開いたが未提出・`opened_last_jst` / False = 👀 未開封 / None = 記録が始まる前に配った分 = 分からない) と
    生徒の `unopened_count`。記録の始まり = 種類ごとの最初の記録 (`_item_open_load`・読むだけ・SELECT は 2 回)。CEO は「👀 未開封」「開いたが未提出 (M/D)」と
    生徒の行に「👀 未開封 N」(null・古いサーバでは出さない)。
- 回帰テスト `scripts/health_check/test_item_open_due.py` (CI `server-tests.yml`・JS は TZ=America/Los_Angeles)。★hw-notice.js を変えたら class.html と mypage.html の `?v=` を両方上げる。

## 💾 単元ドリルの解答の途中保存 (2026-10-18 塾長「②の残りも作っておいて」= 提案 ②「解答を途中で保存 (端末の中だけ)」)
- 共通部品 `gd-draft.js` (root・ES5・class.html と mypage.html が `?v=` 付きで読む。変えたら両方上げる)。単元ドリル (クラス自動宿題・3日ドリル・塾長のドリル・今日の1問) の
  選んだ答えを選ぶたびに localStorage `aj_gd_draft_v1:<生徒ID>:<ドリルID>` に保存 (`{v, t, n, a: {問題ID: [番号, 指紋]}, u: [自信なし], at}` = 選んだ番号だけ・
  正解は提出まで届かないので漏れない・名前なし)。全部 try/catch・保存できない端末 / 生徒 ID なしはページ内だけ。サーバは触らない (表・ルートなし)。
- 開き直したら戻す (問題文・選択肢の指紋が違う問・はみ出す番号は戻さない)・提出できたら / 409 (提出ずみ) / 提出ずみのドリルを開いたら消す・通信に失敗したら残す・
  60 日より古いものは使わず保存のときに消す。カードに「💾 途中 2/3」と「▶ 続きから解く」。塾生アプリの「← 宿題一覧に戻る」は確認しない (トースト)。
  gd-draft.js が読めない端末は今までどおり (戻るときに確認)。塾長の宿題の記号の解答用紙は別 (hw-sheet.js `aj_hw_sheet_v1:`)。
- 回帰テスト `scripts/health_check/test_drill_draft.py` (CI `server-tests.yml`・本物のサーバの GET / 409 を画面に入れ、画面が送った提出をサーバに送り直す)。

## 生徒画面 (mypage) の「続ける仕組み」と家庭への連絡 (2026-09-09 レビュー反映)
- **連続学習日数・「✅ できた！」はサーバ実績が正典** (`GET /api/student/activity-summary` / `POST /api/student/coach-done`)。
  演習 (`question_attempts`)・学習記録 (`study_logs`)・できた！(`events name='coach_done'`, `session_id=str(student_id)`) の
  いずれかがあった JST 日を「活動日」とする。localStorage の値は「サーバに届かなかった時の控え」で、次回サーバ値で上書きされる。
- **おかえり**: 7 日以上活動が無い生徒には、コーチカードが宿題・弱点より先に「今日は 1 問だけ」を出す (`days_since_activity`)。
- **週次レポートの「活動ゼロ週は送らない」規則に例外**: 直近 28 日に演習があった生徒には短い「今週は 0 問」メールを
  生徒コピー + 保護者コピーへ送る (最大 2 週連続・`notifications` template `weekly_report_zero_week` / `_parent`)。
  休眠層と一度も解いていない生徒は従来どおりスキップ。`ZERO_WEEK_REPORT_ENABLED=0` で従来の完全スキップに戻る。
  ★通常レポートを全員分送った**後**の第 2 パスで、残り枠と `ZERO_WEEK_REPORT_CAP` (既定 24 通) の範囲でしか送らない
  (通常レポートの席を奪わない)。同じ週に水曜の一声が届いた生徒本人には重ねず、保護者宛だけ送る。
  連続上限は「活動窓 (28 日) + 1 日」の中で送った週数で数える = 1 回の停止につき最大 2 週分
  (13 日窓だと 14 日前の送付が落ちて上限に届かず毎週送っていた・review で発見)。
  ★2026-09-09 の実例: 生徒が 3 週間ログインで詰まり、レポートが黙って止まり、保護者が先に異変に気づいた。
- **週半ばの一声** (`POST /api/cron/midweek-nudge`・毎週水曜 18:00 JST・`_midweek_nudge_scheduler`): 今週 (JST 月曜〜) 演習 0 問
  かつ 直近 28 日には演習していた生徒へ 1 通 (LINE 連携済みは LINE、無ければ生徒コピー宛メール)。6 日 dedup・CAP 60。
  `MIDWEEK_NUDGE_ENABLED=0` で停止 (スケジューラ自体を登録しない)。`?dry_run=true` は送らずに対象を返す。
  ★`MIDWEEK_NUDGE_ENABLED` / `ZERO_WEEK_REPORT_ENABLED` は import 時に読む定数。**Railway で env を変えたら ai-juku-api を
  再起動**しないと効かない。無効化中は `midweek_nudge_run` を health の停止監視から外す (誤検知防止)。
- **週次レポートの重複防止** (2026-10-15): 日曜 19:00 の本命 (`_weekly_reports_scheduler`) と 20:05 の GitHub Actions の予備
  (`weekly-reports-backup.yml` → `scripts/trigger_weekly_reports.py`) が同じ API を叩く。生徒ごとに直近 6 日に**成功した**
  生徒メール (`weekly_report_email`)・保護者メール (`weekly_report_parent_email`)・LINE (`weekly_report`) を 1 回の SELECT で引き
  (`_weekly_report_sent_templates`)、送り済みの経路は送らない。★それまで LINE だけ dedup が無く、連携済みの家庭に毎週 2 通届いていた。
  失敗行 (success=0) は数えない = 本命で失敗した分は予備が送り直す (予備のログに「予備が送りました」)。
  AI コメントは判定の後で、メールを送る必要があり上限にも達していないときだけ作る (予備の回で作り直さない)。
  応答に `skipped_dup` (経路が全部送り済みの生徒)・`skipped_dup_line` (LINE だけ飛ばした数)。`skipped` は今までどおり「活動なし」。
  `_weekly_report_verdict` と `prod_healthcheck.py` の weekly_report は `skipped_dup` があれば「断絶」と言わない。
  メールの上限 `WEEKLY_REPORT_EMAIL_CAP` (既定 80・1 回の実行ごと) は変えていない (2026-10-15 の既定案は二重送信の修正だけ)。送り済みの家庭は `capped` に数えない。
  手動の即送信 `POST /api/weekly-reports/send-one` は dedup しない。ただし送った行が残るので、6 日以内の日曜はその生徒に送らない (LINE も)。
  回帰テスト `scripts/health_check/test_weekly_report_dedup.py`。
- **📝 今週の宿題の 1 行** (2026-10-18 塾長「③の週次レポートの1行も作っておいて」= 成績を上げる提案 ③): 週次レポート (保護者 / 生徒コピーの HTML・LINE・
  「今週は 0 問」メール・send-one) に「📝 今週の宿題: 届いた N 本／提出 M 本／〆を過ぎた未提出 K 本（単元 3 つまで）」+ 宿題を開くリンク。新しいメール・LINE は増やさない。
  - 数え方は `_weekly_report_homework_batch` 1 か所 (読むだけ・全生徒でドリル 1・宿題 1 の SELECT = 500 件ずつの IN・リンク 1・cron の 1 回の実行で 1 回)。
    週 = レポートと同じ `_weekly_report_window` (JST)。N = 配った日時が窓の中・M = 窓の中に出した本数 (前の週に届いた分も = M > N もある)・
    K = いま未提出で 〆 (宿題の期限 / クラス自動宿題の題名の「〆M/D」= `_class_brief_title_due`) < JST の今日 (hw-notice.js と同じ・古さで切らない・3日ドリル / 塾長のドリルに 〆 は無い)。
    数える = クラス自動宿題・3日ドリル・塾長のドリル (15問ミッションも)・塾長の宿題 (解答用紙も)。今日の1問・初回診断は数えない (`_CLASS_BRIEF_NOT_SELF_SQL`)。
    単元 = 〆過ぎの単元 (無ければ窓の中に届いた未提出の単元を「（未提出: …）」) を新しい順に 3 つ。N・M・K が全部 0 の生徒は 1 行なし (今までと同じ本文)。
  - リンク: AIなし枠 `class.html?tab=homework`・ほか `mypage.html?focus=homework` (`_homework_notify_link_paths`)。LINE は `&openExternalBrowser=1`。
    LINE は前から受け取っている生徒 (連携済み・`need_line`) の `weekly_report` の中だけ (1 行が無ければ本文は 1 文字も変わらない)。「今週は 0 問」は LINE を送らない (今までどおり)。
  - 「今週は 0 問」: 演習の記録が一度も無い・休眠 (28 日より前) の生徒でも、未提出 (窓の中に届いて未提出 / 〆過ぎ) があれば送る
    (`WEEKLY_REPORT_HOMEWORK_ZERO_WEEK` 既定 `1`・`0` / off で従来どおり・呼ぶたびに読む・`_zero_week_report_decision(homework_pending=True)` → `via_homework`)。
    ★上限 (`ZERO_WEEK_REPORT_CAP`・`WEEKLY_REPORT_EMAIL_CAP`・連続 2 週 = 29 日に 2 回まで)・6 日 dedup・受講開始前のスキップ・水曜の一声との重ね方は同じ。
    第 2 パスは前からの対象を先に送り、`via_homework` の家庭は後ろ (枠を先に使って前から届いていた家庭を締め出さない)。
    記録が無い生徒には「最後の演習」を書かない。未提出があるとボタンは「📝 宿題を開く」(AIなし枠は「今日の 1 問」を開けないため)。payload は数だけ (`hw` = n/m/k)。
  - 応答 (events `weekly_reports_run` にも残る・名前なし): `homework_lines`・`zero_week_homework`・`homework_totals` {students, delivered, submitted, overdue}・
    `homework_zero_week_enabled`・`homework_error` (数えられなければ 1 行なしで送る)。dry-run の preview に `homework` {delivered, submitted, overdue, pending, units, link, line}・`zero_week_via_homework`。
  - 回帰テスト `scripts/health_check/test_weekly_report_homework_line.py` (CI `server-tests.yml`)。
- **平日に `POST /api/cron/weekly-reports?dry_run=true` を叩くと「先週の完了週」で評価される** (`_weekly_report_window`)。
  日曜だけ「今週」。平日の dry run で対象外と出ても日曜に送られないとは限らない。
- **mypage の初期化は補助スクリプトを最大 10 秒しか待たない** (`_ajWidgetWait`)。`slApiFetch` は既定 30 秒でタイムアウト
  (`options.timeoutMs` で個別に延長・AI 生成系は 90 秒)。合格可能性スコアはサーバ失敗 (5xx/429/通信) で消えず再試行を案内し、
  4xx (志望校未設定など) だけ非表示。
- **LINE 連携 CTA** (`#lineLinkSection`) は `/api/auth/me` の `line_linked === false` の生徒にだけ出る (LINE の userId は返さない)。
- 回帰テスト: `scripts/health_check/test_student_ux_2026_09.py` (CI `server-tests.yml`)。

## 📺 スタサプ 第N講 (講単位) — 題名は本番 DB だけ (2026-10-10 塾長決定・段階 A = カタログと対象判定 / 段階 B = 講データと照合)
- **D1 講の題名 (第N講の題名) はリポジトリ・Vercel で配信されるファイル・認証なしの API・Actions のログ・サーバのログ・
  AI へのプロンプト・メール/LINE 本文に出さない。** 本番 DB だけに置く (段階 B の取込)。テストの題名は架空 (「テスト講義A」等)。
  講座名と講数 (公開ラインナップの情報) は書いてよい。講師名は書かない。
- **D2 スタサプを勧めるのは授業コース (水3・金3・日のライブ授業) の在籍生だけ**。オンラインの AI 学習管理コース
  (LP「国公立難関大学コース」・course は同じ kokuritsu_nankan で在籍クラスが空) には勧めない (LP・承認メールの文言も外した)。
  **D3** 科目は英語・国語も含む (`SAPURI_SUBJECT_KEYS` から外すと科目ごとに止まる)。**D4** 入塾した生徒だけ。
- 判定は `_sapuri_eligible_by_id(student_id)` 1 か所 (自分の接続・30 秒キャッシュ・例外は対象外): 停止スイッチ (kv_settings
  `sapuri_enabled`・`POST /api/admin/sapuri/settings`) / 実行時の `_COURSE_CLASSES` が宣言 `_SAPURI_COURSE_LABELS_DECLARED` と完全一致 /
  course=kokuritsu_nankan / `_enrolled_sql` (本科の長期 trial を含む) / 在籍クラスに 3 コマ全部 / 受講開始月を過ぎている。
  ★status='paid' では判定しない (本科生は承認時に status='trial'・trial_end +10 年)。生徒画面は `GET /api/student/sapuri/status`。
  停止スイッチは CEO 画面の「📺 スタサプ」(生徒・学習) から切り替える (ceo.html 内のスクリプト)。
- 講座の正典はコード定数 `SAPURI_COURSES` (138 講座・code / first..last / 偏差値と週数は塾の目安)。旧初期データ (2026-05 の 74 講座) は
  架空の講座名が混ざっていたので廃止し、`sapuri_lectures` 表は読まない。`/api/sapuri-lectures` はこの定数を返す (題名は無い)。
- カリキュラムのスタサプは `sapuri: [{course_code, from_seq, to_seq}]` が正典。`sapuri_lectures` (「講座名 第a〜b講」) はサーバが
  作り直す表示用の写し (`_sapuri_phase_normalize`・POST/PUT・/me・ai-generate・gap-analyze・apply-gap-fix・expand-to-plans で共用)。
  旧形式の文字列・AI が書いた講座名・materials / milestones のスタサプの語を含む要素・focus / name のスタサプの文は捨てる (全生徒)。
  対象外の生徒は空。AI 弱点プリントは AI にスタサプを書かせない。
  ★**読むときに隠す・書くときに消さない**: 対象外 (停止スイッチ OFF・ラベル変更直後など一時的なものを含む) を理由に保存済みの
  `sapuri` を消さない。保存 (apply-gap-fix・PUT の phases) は `_sapuri_phases_for_store` を通し、対象外のときは新しいスタサプだけ入れない。
  表示 (/me・下書き `curriculum_draft` の GET・`/api/study-plans/me` の「出典: スタサプ」の計画) は今の判定で隠す (行は消さない)。
- app.js の講数の上限は `/api/sapuri-lectures` の name/first/last から実行時に作る (上限は last・折り返しは first から =
  総合問題編の「第41講」を書き換えない)。端末に残った旧名のタスクは静的表 `SAPURI_LEGACY_CAPS` (`SAPURI_LEGACY_NAME_TO_CODE` の写し)。
  ★学年を外した鍵は講座に固有の形 (「レベル」か「＜…＞」・6 文字以上) だけ。「生物」「地理」「化学基礎」のような科目名だけの鍵を作ると
  参考書のタスク (「セミナー生物 p.100-120」) を「(N周目)」に書き換えて端末に保存してしまう (戻せない)。実行時の鍵は直後に名前の続きが
  来るときは当てない。端末の控えは版 (`version`) と取得日時つきで、1 日より古ければ読み直す。ゲートの [8] が実際の JS で確かめる。
- 検査: `scripts/health_check/test_sapuri_lessons.py` (server-tests) と `scripts/sapuri_lessons/check_sapuri_catalog.py` (カタログ・別名・
  宣言ラベル・app.js の写し・旧データの参照・題名の元データがリポジトリに無いこと)。
- ★**Claude とスクリプトは studysapuri.jp・mediacdn を取得しない** (URL も通信処理も置かない)。講の一覧は塾長がブラウザで保存した
  ファイルから作る。更新したいときは塾長に保存してもらう。
- **段階 B の講データ (第N講) は本番 DB の 3 表だけ**: `sapuri_lessons` (lesson_key =「講座コード#講番号」・題名・active) /
  `sapuri_lesson_tags` (講 → 科目キー・タグ) / `sapuri_topic_lessons` (弱点の topic そのもの → 講)。student_id 列は無い。
  表が無いデプロイ直後は新 API が 503・照合は空。行は消さず、取込で消えた講は active=0。
- **照合 `_sapuri_recommend`** (DB だけ・AI なし・自分の接続): 弱点 topic を `_sapuri_parse_topic` で科目キーとタグに分け
  (社会の時代タグ等は question_attempts→exam_questions の part_key が 1 つに決まるときだけ・grammar_drill は除く)、
  `SAPURI_COVERS` から講座を 1 つ選ぶ (生徒の band → 偏差値が dev_min..dev_max に入る → 中央が近い → code 順・決定的)。
  ★**タグの無い弱点** (自由入力の「中和滴定」等) は、band (全学年を含む) に科目の全範囲 (`"*"`) の講座があるときだけその中から・
  無ければ band にその科目の講座が 1 つだけのときだけ。それ以外は推薦しない (band の外へ移らない = 高3 に高1・2 のベーシック化学を出さない・
  数学の弱点に数学III・現代文の弱点に語句の講座を出さない)。数学は接頭辞 (数学I/A/II/B/III) の系統で選ぶ (数学C・基礎数学は決めない)。
  講座の中は Tier 1 = topic が一致する講 / Tier 2 = タグが一致する講が **4 講以下**のときだけ / Tier 3 = 講座だけ (講なし)。
  選んだ講座に講データが無い (has_lessons=False・未取込) ときは、同じ科目 (とタグ) の講データがある講座で Tier 1/2 を引く
  (band → もう一方・偏差値の近い順)。当たらなければ Tier 3 は選んだ講座 (CEO のカバー状況に「講座に講データ無し」)。
  TOP3・class.html・週次プリントは Tier 1/2 だけ・1 弱点 1 講 (+範囲)・同じ講は 1 回・主因が careless/time/misread の弱点には出さない。
  「（第b講まで）」は講番号が続くときだけ (`to_seq`・飛び飛びの [12, 30] には付けない)。画面は講座名 1 行 + 「第N講…」2 行まで
  (1 行に丸めるとスマホで第N講が切れる)。Tier 3 はカリキュラムと AI 弱点プリントだけ。メール・LINE は講座名と第N講だけ (題名なし)。
  週次プリントの保存済みの sapuri は、読むときに対象外・止めた科目 (`SAPURI_SUBJECT_KEYS` から外した科目キー)・照合から外した講座の分を外す。
  停止スイッチは読めなければ閉じる側 (最後に読めた値・一度も読めていなければ OFF)。
  ★**取込後の点検 (2026-10-10 塾長「4つとも直して」)**: 偏差値は**その科目の模試だけ** (`_sapuri_dev_basis`・無ければ既定 60。
  全科目の平均は使わない = 化学の低い偏差値で英文法の講座が下がらない)。選んだ講座に講データがあるのにそのタグの講が 1 つも無いとき
  (文型だけの講から語法を外した 高1・2 の語法など) は、**同じ band (全学年を含む)** でそのタグの講がある講座のうち偏差値の目安の中央が
  最も近い 1 つで Tier 1/2 (`_sapuri_fallback_courses`・band は越えない)。★ただし生徒の偏差値がその講座の目安 ±5
  (`_sapuri_dev_window_ok`) に入るときだけ (ベーシックの生徒をトップへ送らない・理由 `fallback_too_far`)。代わりから出したら
  CEO ③ に「選んだ講座（…）にこの単元の回が無いので、同じ学年帯の講座から」(details の `fallback_from`)。
  カリキュラム (ai-generate・gap-analyze) のカタログも講座ごとにその科目の偏差値で絞る (`_sapuri_dev_map`・全科目の平均は使わない)。
  講まで出せなかった理由は `_sapuri_recommend(..., details=[])`
  が返すコード (`_SAPURI_WHY_CODES`・推薦の dict には入れない = 生徒の応答の形は不変)。文言は ceo.html の `SP_WHY_JA`
  (テストが鍵の一致を検査)。`subject_only` は topic が科目名だけ (「化学」「数学C」) のときだけ。単元名が語彙・別名に無いもの
  (「化学平衡」・英語の「不定詞の意味上の主語」) は `unit_not_in_vocab` (語彙・別名に足せば出せる)。
  CEO の見え方の class_items は `/api/student/class/sapuri` と同じもの (`_sapuri_class_items`・科目つき)。
- **取込 (塾長の操作)**: CEO「📺 スタサプ講義データ」でフォルダの `sapuri_lessons_<講座コード>.json` を複数選択 → 自動で dry_run して
  要約 (講数・見本 3 講・捨てたタグ・止まる講・講数が合わず拒否された講座) → 「取り込む」で講座ごとに順に本番。
  API は `POST /api/admin/sapuri/lessons/import` (管理者 Bearer だけ・X-Cron-Secret 不可 = Actions から叩く経路を作らない・
  1 回 1 講座・講座の中だけ入れ替え・冪等・講数が first..last と違えば講座ごと 400)。取り込む前にスタサプのアプリで
  2〜3 講座を見比べてもらう (元データは 2022-06 時点の公開一覧)。状態は `GET /api/admin/sapuri/status`、
  生徒の見え方は `/preview?student_id=`、弱点のカバー状況は `/coverage`。どれも題名をログに出さない。
- **講データの作り直し (Claude が手元で)**: 元データと出力は Desktop の `🏫 運営・集客/塾運営/スタサプ講義データ/` だけに置く
  (`元データ/high_category.tsv` = 公開の通年講座一覧・`タグ付け/tagged_final.json` = 講と弱点 topic のタグ付け・`取込用/` = 出力)。
  `python3 scripts/sapuri_lessons/build_sapuri_import.py --tsv … --tags … --out-dir …` (既定はこの 3 か所)。builder は
  server/main.py の `SAPURI_COURSES` / `SAPURI_SUBJECT_KEYS` / `SAPURI_TAG_VOCAB` / `SAPURI_TAG_ALIASES` を ast で読み、
  has_lessons=True かつ講が first..last に 1 講ずつそろう講座だけ書く (合わない講座は summary.json の skipped に理由)。
  補講・第0講は捨て、EKZB は topic_code の講番号で束ねて「／」連結、80 字で切る。語彙外のタグ・科目キーは捨てて数える。
  TSV の講師名 (presenter_name) を含む題名があれば何も書かずに失敗する (名前は表示しない)。
  ★**git の作業ツリーの中のパスは builder が拒否する**。`.gitignore` にも `**/sapuri_lessons_*.json` `**/high_category*.tsv`
  `**/sapuri_import/` `scripts/sapuri_lessons/out/` を入れてある。前回の出力は消さない (summary.json の stale_files に出る)。
- 検査 (段階 B): `scripts/sapuri_lessons/check_build_sapuri_import.py` (builder の自己テスト・架空のデータ・run_all_gates が拾う) と
  `scripts/sapuri_lessons/check_no_titles_in_diff.py` (**手元専用**: 取込用 JSON の 4 文字以上の題名が `git diff --cached` /
  `--range A..B` (コミットメッセージ込み) / `--all-files` に無いか。題名は表示しない。データが無い端末・CI は SKIP)。
  単元名と同じ題名 (タグ語彙・基準コミット 6857cfe に既にある語) は一般語として数えるだけ。**スタサプの作業を commit する前に回す。**
- **見た回のチェック (2026-10-10 塾長「見た回のチェック（進み具合の記録）機能も作って」)**: 表 `sapuri_lesson_progress`
  (student_id, lesson_key, watched_at, source・UNIQUE(student_id, lesson_key)・題名は持たない)。student_id を持つので削除・統合の
  5 つの一覧に入れてある。統合で同じ講を両方が見ていたら早い方の watched_at を残す (admin_student_merge で残す側を早い方へそろえてから
  汎用の重複処理)。★書き込みは必ず `_utc_naive_iso()` (DEFAULT CURRENT_TIMESTAMP は形とタイムゾーンが DB で違い、早い方の比較が狂う)。
  - 生徒 API (prefix `/api/student/class/` = AIなし枠でも通る・許可集合は変えていない): `POST /api/student/class/sapuri/watched`
    `{lesson_key, watched, surface}` (本人だけ・body の student_id は読まない・対象外は 403・有効な講で止めていない科目の講座だけ (400)・
    冪等で最初の日時のまま・取り消しは行を DELETE・止めた講の記録も消せる・回数 60/60 秒) と `GET /api/student/class/sapuri/progress`
    (新しい順 200 件・題名は active な講だけ・止めた科目の行は読むときに隠す・対象外は items 空)。塾長の確認入室中は source='impersonation'。
  - **読み取りは `_sapuri_watched_map` の 1 か所・画面ごとに 1 回** (テストが数える。ループの中で呼ばない)。照合 (`_sapuri_recommend`) は
    lessons[*] に watched を付けるだけで label・to_seq・matched_by は変えない。**見た回を飛ばすのは `_sapuri_display_ex` の 1 か所だけ**:
    表示する講は「まだ見ていない最初の講」、範囲は見ていない回の連続、label はそこから作り直す (見た回の題名を残さない)。
    照合が返した回 (当たった層だけ: Tier 1 で当たれば Tier 2 は見ない) を全部見たら all_watched: 通塾生アプリと週次には出さず次の弱点が
    上がる・TOP3 は「✅ 見終わりました → ⏱ ドリルで確認」(題名なし)。取込で単元の対応が変わると見終わりが戻ることがある (受け入れ)。
    カバー状況と AI 弱点プリントは見た回を見ない (`mark_watched=False`)。
  - 週次プリント: 作るときは見た回を飛ばす (保存する sapuri に watched の印は入れない)。**保存済みは作り直さない** (メール・紙と同じ週の控え):
    /this-week が読むときに表示する講へ watched と日付を付けるだけ。送った後で見てもメールは変わらない。
  - 進み具合: カリキュラムの各フェーズに `sapuri_progress` [{course_code, watched_count, total}] (sapuri と同じ並び・/me・ai-generate の
    プレビュー・下書きの GET で読むときに付ける)。**保存しない**: `_sapuri_phase_normalize` が捨て、`_validate_curr_phases` は決まった欄だけ。
    学習計画は /api/study-plans/me の「出典: スタサプ」の計画に `sapuri_progress` {watched, total, course_code, next_seq, next_key}
    (material を SAPURI_COURSES の名前と完全一致で読む・読めなければ付けない)。next は範囲の中で次にまだ見ていない有効な講 = 計画カードの
    「☐ 第N講を見た」。mypage の計画カードは勉強時間の % の代わりに「📺 見た x / y 講」とバー。
    ★y (total) は**記録できる回だけ**数える = 範囲の中の有効な講 (active=1) + すでに見た回 (止めた講の記録も)。数える回が 0 の範囲
    (講データの無い講座 = カタログの約 4 割・全部止まった範囲) は計画に sapuri_progress を付けない (勉強時間のバーのまま)・カリキュラムは
    その範囲を null (ラベルに x / y を足さない)。b-a+1 で数えると x が永久に y に届かず、押すボタンも無い赤いバーが出る (2026-10-10 レビュー)。
  - 画面のボタン (class.html のカードと一覧・mypage の TOP3・週次プリントの画面・一覧・計画カード) は lesson に watched (bool) の印が
    あるときだけ出す (Vercel が先に出て古いサーバと組み合わさる間に 404 のボタンを出さない)。日付はサーバの日本時間の日付文字列を切るだけ
    (new Date しない)。confirm/alert は使わず、同じボタンで即取り消し + トースト。CEO は ① の生徒一覧に見た講数と最後に見た日・③ に「見た」列と
    「📺 見た回」(`GET /api/admin/sapuri/progress?student_id=`・管理者だけ題名つき・止めた講も・見出しに生徒の名前・
    生徒を切り替えたら一覧と見え方を消す = 前の生徒の一覧が別の生徒の回に見えない)。
  - ★既知の割り切り (D1・塾長判断待ち): 対象生徒は任意の有効な講を「見た」にしてから一覧を読めば、その講の題名を読める (1 分 60 回まで)。
    厳しくするなら POST を「その生徒にいま推薦している講・カリキュラムの範囲の講」に絞る (POST ごとに照合が 1 回増える)。
  - 回数制限は**生徒ごと** (`_check_rate_limit_caller` = トークンの student_id 単位・watched も progress も 60/60 秒)。IP 単位にしない:
    本番は Vercel rewrite 経由で `_client_ip` が共有の出口に縮退し、全生徒が 1 枠を共有して誤 429 になる (2026-10-10 レビュー)。
    見た回の一覧は、押した後の読み直しが失敗 (429・通信) しても出ている一覧を消さない (隠すのは最初の読み込みの失敗と 401/403/404)。
    マイページは eligible:false を一度受けたら、そのページを開いている間は progress を読まない。
  - ★push の後は `/api/health` の `init_ddl_skipped==0` を確かめてから生徒の削除・統合を使う (表が無いまま走らせると Postgres で 500)。
    表が無い間の新 API は 503、照合は「何も見ていない」扱いで従来どおり出る。

## 🗺️ 自動配信の全体図 (2026-10-15 塾長決定・横断のまとめ)
誰に・いつ・何が・どの印で自動で届くかの一覧。細部は下の 🎯 自動の弱点配信・塾生アプリのみ枠・🏫 クラス自動宿題・📣 お知らせ と、上の 📖🧪 の節。
- **塾長方針**: 自動で配るのはレビュー済みの科目別ドリルだけ (盲検 3 名の記録がある出典)・中学生と高校生を取り違えない・
  宿題とドリルのお知らせはアプリの中 (「アプリを開けば分かる」)。問題の自動配信 (週次プリント・3日ドリル・クラス自動宿題) はどれも既定 OFF で、塾長が dry-run を見てから env で ON にする。
- **朝の順番 (JST)**: 3:00 DB バックアップ → 4:00 弱点集計 (`student_weakness`・合格スコア・events 掃除) →
  (日曜 5:00 週次弱点プリント = 既定で停止) → 5:30 🎯 3日ドリル → 6:00 🏫 クラス自動宿題 → 7:00 🎬 授業録画の割り当て。
  3日ドリルとクラス自動宿題は 4:00 の集計を読むので、それより前に回さない (`CLASS_HW_AUTO_HOUR_JST` は 5〜22 に丸める)。
  夕方は 水曜 18:00 週半ばの一声・日曜 19:00 週次レポート (20:05 に GitHub Actions の予備が同じ API を叩く。メールも LINE も 6 日 dedup。
  2026-10-18 から「📝 今週の宿題」の 1 行 = 家庭へ宿題を知らせる唯一の定期便・新しい通知ではない = 「続ける仕組み」の節)。
- **1 人 1 経路** (振り分けは `_auto_delivery_ai_path` = `_ai_blocked_now` の 1 か所。SQL は広めの絞り込みだけ):
  - AIあり・AI 体験中 (`'ai'`) → 🎯 3日ドリル (`WEAKNESS_DRILL_ROUTINE_ENABLED`): 本人の弱点の単元から 10 問・生徒ごとに 3 日に 1 本。
  - AIなし (塾生アプリのみ・体験中でない) の通塾生 (`'ai_nashi'`) → 🏫 クラス自動宿題 (`CLASS_HW_AUTO_ENABLED`): 受講している英語のクラスの宿題・
    10 問 (英検の長文は本文 2 本・長文クラスは本文 1 本)・1 人 2 日に 1 本。
  - 小学生・学年が判定できない (`_student_grade_band` が `shougaku` / 空) → どちらも出さない (dry-run に名前 → CEO で学年を直す)。
  - ほかの条件でどちらにも入らない生徒もいる (3日ドリル = 30 日以上ログインしていない / クラス自動宿題 = 通塾生でない・英語のクラスが無い・受講開始月の前)。
    理由は両方の dry-run に出る。生徒が自分で始める今日の1問・初回診断は配信ではないが、同じく学年で科目を分けてレビュー済みだけから出す。
    塾長が CEO で手で配るもの (📝 科目別 単元ドリル・📖 英語長文・🧪 習熟度テスト) はこの振り分けの外 (学年の確認ダイアログだけ)。
- **ドリルの印** (`grammar_drills.created_by`・列は足していない): `admin` = 塾長が CEO で配った / `today_question` = 今日の1問 /
  `diagnostic` = 初回診断 (CEO の一覧に出さない) / `weakness_routine_3d` = 3日ドリル / `class_hw_auto:<kosei|chugaku>:<クラス名>` = クラス自動宿題。
  CEO の配信済み一覧は `kind=owner` (既定・自動配信と初回診断を除く) / `routine` / `class_hw` / `auto` / `all`。
  ★デスクトップの予約タスク「2日に1回 弱点15問ミッション」は本番 DB に直接 `status='assigned'` を書く (許可リスト・学年ガード・監視を通らない・
  印は `created_by='mission_2day_routine'`)。**2026-10-16 塾長決定: 予約タスクも 3日ドリルも両方配ってよい** (止めない)。
  3日ドリルの「積まない」「3 日以内」の判定は自分の印 (`weakness_routine_3d`) の行だけを数えるので、予約タスクの行では止まらない
  (一括の判定も錠の中の読み直しも同じ・`test_weakness_routine_auto_delivery.py` [11])。生徒の画面の未提出の数には両方が入る。
- **出してよい問題** (`_auto_delivery_source_ok`・許可リスト `_AUTO_DELIVERY_REVIEWED_SOURCES_DEFAULT`): english `manual-drill-v1` `-v2`・
  math `mathct-*` `mathwb-*`・chugaku `chugaku-drill-v1`〜`v4` と `chu2grammar-20260709` (この出典は chugaku の中だけ)・中学 4 教科 `chugaku-<教科>-v1`・
  eiken `eiken2-*` `eikenp1-*`・english_long `el-*` `englong:*`。本文型は本文と全設問の両方が通ること。
  ⛔ 習熟度テスト (科目 `proficiency_test`・出典 `pt-` / `ptest:`) はどの env でも出さない。高校の理科・社会・国語・弱点特訓 32 問 (weakness_v1)・
  exam_questions を分けた古い行 (`pool`) は盲検の記録が無いので出さない。
  ★新しいシードの順番: ほかと重ならない出典の接頭辞 → 盲検 3 名 → 許可リストと `test_auto_delivery_shared.py` の `REVIEWED_SEEDS` に 1 行ずつ
  (盲検していなければ `NOT_AUTO_SEEDS`。どちらにも無いとテストが落ちる)。本番の在庫は `GET /api/admin/grammar/source-inventory`。
- **中高のガードは 2 回**: 選ぶとき (区分の科目だけ = `_ROUTINE_SUBJECTS_BY_BAND` / `_CLASS_HW_ROUTINE_MAP`) と書き込む直前 (`_drill_subject_band_ok`:
  chugaku* は中学生だけ・english / math / english_long / 理社国は高校生だけ・eiken は両方・proficiency_test はなし)。
  直前で止まったら `_ROUTINE_BAND_GUARD_TRIPS` / `_CLASS_HW_BAND_GUARD_TRIPS` と `props.error` (失敗の通知が飛ぶ)。
  学年の読み取りは `_student_grade_band` 1 つ (「中２」「中三」も中学。student-mode.js の `ajNormGrade` と ceo.html の `_gdMode` も同じ表)。
- **お知らせ** (`_homework_notify_channels(source)`): `source='manual'` は `POST /api/admin/grammar-drill/create` だけ (塾長が生徒と中身を選ぶ)。
  アルゴリズムが中身を選ぶものは CEO の 📤 / 「今すぐ」でも `'auto'`。既定では manual = 登録メールだけ・auto = 何も送らない・宿題の LINE はどちらも送らない。
  生徒にはアプリの「🆕 新しい宿題 N 件」(hw-notice.js) で見える。ログインコードの LINE と週次レポートの LINE はこの対象外。
- **env** (★既定値の正典はコード。ここと食い違ったらコードが正しい):
  - `WEEKLY_WORKSHEET_ENABLED` 既定 停止: 日曜の週次弱点プリント (`1` / `true` / `yes` / `on` で再開)。
  - `WEAKNESS_DRILL_ROUTINE_ENABLED` 既定 OFF: 🎯 3日ドリル。`WEAKNESS_DRILL_ROUTINE_CAP` 60 (1〜500) = 1 回の人数。
    `WEAKNESS_ROUTINE_UNKNOWN_GRADE_AS_KOSEI` 0 = 学年が判定できない生徒には出さない (1 で高校生扱い・3日ドリルだけ)。
    `WEAKNESS_ROUTINE_OPEN_STALE_DAYS` 14 (0 = 全部数える・それ以外は 3〜365) = 積まない判定に数える未提出の日数 (2026-10-16)。
  - `CLASS_HW_AUTO_ENABLED` 既定 OFF: 🏫 クラス自動宿題。`CLASS_HW_AUTO_HOUR_JST` 6 (5〜22)・`CLASS_HW_INTERVAL_DAYS` 2 (1〜14・題名の 〆 も配った日 + この日数)・
    `CLASS_HW_AUTO_COUNT` 10 (5〜25)・`CLASS_HW_AUTO_PASSAGES` 2 (1〜5・英検の長文)・`CLASS_HW_READING_MIN_PASSAGES` 4 (1〜50・長文クラスの開始本数)・
    `CLASS_HW_UNIT_COOLDOWN_DAYS` 14 (0〜90)・`CLASS_HW_OPEN_STALE_DAYS` 14 (0 = 全部数える・それ以外は間隔〜365 = 積まない判定に数える未提出の日数・
    2026-10-16)・`CLASS_HW_AUTO_ONLY_CLASSES` 空 = 全クラス (段階投入・カンマか「、」区切り。全角・空白の違いは
    同じ名前 = `_class_hw_label_key`。★当たる名前が 1 つも無い (打ち間違い・保留のクラスだけ) ときは全クラスに広げず 0 クラス + `props.error`)。
  - `HOMEWORK_NOTIFY_EMAIL` 既定 `manual` (`all` / `off`)・`HOMEWORK_NOTIFY_LINE` 既定 0 (1 で宿題の LINE を戻す非常スイッチ)。
  - `AUTO_DELIVERY_REVIEWED_SOURCES` 既定 空 = 上の許可リスト (`english=manual-drill-v1;math=mathct-*` のように科目ごとに差し替え・禁止は外せない)。
  - `PTEST_FEEDS_WEAKNESS` 既定 0 (1 で習熟度テストの skill 付きの設問を弱点に記録)。
  - ほとんどは呼ぶたびに読む (Railway で変えれば次の実行から効く)。★監視の表 `_SCHEDULER_MAX_AGE_DAYS` だけは import 時に ON/OFF を読む
    (変えたら API の再起動で反映)。`prod_healthcheck.py` は API の env を読めないので、3日ドリルとクラス自動宿題は `OPTIONAL_UNTIL_FIRST_RUN`
    (履歴が無いうちは PASS・ON の後で OFF に戻したら手で外す)・週次プリントは監視から外した (再開したら手で戻す)。
- **advisory lock の番号** (Postgres の xact 錠・番号は f-string で埋める。psycopg3 が int を bigint で送ると関数が見つからないため):
  1 引数 = 8675309 授業プリントの同期・8675310 / 8675311 入試道場の解説の差し替え / 取り消し・8675312 授業録画の割り当て・8675314 クラス自動宿題。
  2 引数 = (8675313, 生徒ID) 3日ドリル。**新しい錠は 8675315 以降の空いた番号**。
- **実行記録**: events の `weakness_drill_routine_run` / `class_hw_auto_run` は `_compact_run_props` の要約 (数・理由・生徒 id 30 件まで・名前なし・4000 字未満)。
  名前は dry-run で `include_names: true` のときだけ (CEO のカード)。クラス自動宿題は配信ごとに events `class_hw_auto_delivered` (生徒 id だけ)。
  2 つの管理 API の応答の `last_run` = この実行記録の最後の 1 行 (`_auto_delivery_last_run`・読むだけ・失敗は null) = CEO の「前回の自動配信」。
- **ON にする順番** (塾長): 週次プリント停止 (既定) → 🎯 の dry-run (学年・`mode_changed_by_normalization`・在庫を見る) → (予約タスクは止めない = 2026-10-16 塾長決定) →
  `WEAKNESS_DRILL_ROUTINE_ENABLED=1` → 🏫 の 🔍 → 1 クラスを 📤 → `CLASS_HW_AUTO_ONLY_CLASSES` と `CLASS_HW_AUTO_ENABLED=1` → 1 回まわったら ONLY を外す。
  ★週次プリントを止めてから 3日ドリルを ON にするまでは、自動の弱点配信が 1 本も無い (AI 体験中の生徒も)。
- **回帰テスト** (CI `server-tests.yml`・一時 SQLite・本番に触れない。何を見るかは `scripts/health_check/README.md`):
  `test_weekly_worksheet_stop.py`・`test_homework_notify_in_app.py`・`test_hw_notice_js.py`・`test_grade_band_consistency.py`・`test_auto_delivery_shared.py`・
  `test_weakness_routine_auto_delivery.py`・`test_self_issued_drill_band.py`・`test_class_homework_routine.py`・`test_english_long_drill.py`・
  `test_proficiency_test_import.py`・`test_drill_import_parity.py`。画面の JS を動かすもの (hw_notice・3日ドリルの [10]・クラス自動宿題の [14]・
  習熟度テストの [14]) は JS エンジン (CI は node・Mac は osascript / jsc) が無いと FAIL する (grade_band だけはソースの突き合わせに落とす)。

## 🎯 自動の弱点配信 (2026-10-15 塾長決定)
- **日曜 5:00 の週次弱点プリントは止めた** (env `WEEKLY_WORKSHEET_ENABLED`・既定 = 停止。動くのは `1` / `true` / `yes` / `on` だけ)。
  理由: 出題元が入試道場の `exam_questions` で AI 生成の行が混ざる。塾長方針は「自動で配るのはレビュー済みの科目別ドリルだけ」。
  自動の弱点配信は科目別ドリルの 3日ドリル (`WEAKNESS_DRILL_ROUTINE_ENABLED`・別途 ON にするまで OFF) に一本化する。
  ★止めてから 3日ドリルを ON にするまでの間は、自動の弱点配信が 1 本も無い (AI 体験中の生徒も)。順番は 停止 → dry-run → 3日ドリル ON。
- 止めている間の動き (判定は `_weekly_worksheet_env_enabled()` 1 か所):
  - 起動時にスケジューラを登録しない (ログに実際の値を出す)。ループも起きるたびに env を見て、無効なら何もしない。
  - `POST /api/admin/worksheet/run-weekly-now` は 409 (何も作らない・送らない)。CEO 画面からは呼んでいない。
  - 監視: `_SCHEDULER_MAX_AGE_DAYS` から `weekly_worksheet_run` を外す (import 時に評価 = env を変えたら再起動)。
    `prod_healthcheck.py` の scheduler_live からも外した (API の env を見られないので、再開したら手で戻す)。
  - `GET /api/student/worksheet/this-week` は `discontinued: true` を足し、`week_start_date` が JST の今日から 7 日前以降の行だけ返す
    (最後の 1 枚はその週のあいだ見える)。**行は消さない**。`/history` (📚 履歴) は全部出る。
  - mypage の欄は「配信は終了しました・過去分は 📚 履歴」と出す。プリントを一度も受け取っていない生徒には欄ごと出さない。
  - CEO「📺 生徒の見え方」(`/api/admin/sapuri/preview` の `weekly_enabled`) は週次の行の箱を「停止中」と出す。
    週次メール・LINE の「📺 今週見るスタサプ」は届かなくなる (TOP3・class.html のスタサプは変わらない)。
  - 公開ページ (light.html・academy.html) の「週1回の弱点プリント」の文言は 2026-10-16 塾長決定で直した (3日ドリルは本番 ON):
    light.html = トリリオン・ライト (feature_tier='light' = AI 月10回・AIなし枠ではない = 3日ドリルの側) は「3日ごとの弱点ドリル（自動配信・自動採点）」
    + 注記「中学生・高校生（既卒生を含む）が対象・小学生には届きません・科目 (高校生は英文法・数学、中学生は 5 教科)」
    (申込フォームで 小学5年・小学6年 を選べるが 3日ドリルは skipped_shougaku で配らない → 無条件に書かない。レビュー指摘)
    (10 回を消費しないものの列挙も 弱点プリント → 弱点ドリル)・academy.html の「弱点“習得”ループ」は「3日ごとに届く弱点ドリル
    （レビュー済みの問題・自動採点）」+ 科目の注記 (高校生は英文法・数学、中学生は 5 教科)。★出す科目・周期・学年を変えたらここも直す
    (`test_weekly_worksheet_stop.py` [8] が _ROUTINE_SUBJECTS_BY_BAND と注記を突き合わせる)。
    ★小学生のライト申込者には自動の弱点ドリルが届かない (塾長へ申し送り: 小学生を売るなら案内を変えるか、学年の選択肢を見直す)。
- `_run_weekly_worksheet_generation` 自体には env の判定を入れていない (テストが直接呼ぶ)。止めるのは呼び出し側だけ。
- 回帰テスト: `scripts/health_check/test_weekly_worksheet_stop.py` (CI `server-tests.yml`)。
- **3日ドリル (毎日 5:30・`WEAKNESS_DRILL_ROUTINE_ENABLED`・既定 OFF) が自動の弱点配信の本線** (2026-10-15 版・plan_version 2):
  - 対象: 在籍 (trial/paid)・直近 30 日ログイン・AIあり か AI 体験中 (`_auto_delivery_ai_path == 'ai'`。AIなし枠はクラス自動宿題の側 = 1 人 1 経路)・
    テスト系の名前と合成監視を除く。開始月 (start_month) は見ない。生徒ごと 3 日周期・未提出 (completed 以外) があれば積まない。
  - **周期と積まない判定の境目 (2026-10-16 塾長決定・`_weakness_routine_cutoffs` 1 か所)**:
    - 3 日は **JST の日付**で数える: 最後に配った日 (JST) <= 今日 − 3 日なら配る (10/16 に配った生徒は 5:30:xx でも 23:59 でも 10/19 の朝に届く)。
      旧版は「実行を始めた時刻 − 72 時間」で、毎朝 5:30:00 に起きる実行では 3 日前の 5:30:xx の配信がまだ 3 日以内 = 実際は 4 日ごとだった。
    - 積まない判定に数える未提出は **直近 `WEAKNESS_ROUTINE_OPEN_STALE_DAYS` (既定 14) 日 (JST の日付) に配った分だけ** (10/1 に配った未提出は
      10/16 の朝から数えない)。古い未提出が残っているだけで新しいレビュー済みのドリルが届かなかった (10/16 の dry-run で 41 名中 30 名)。
      **古いドリルは消さない** (生徒の一覧にも未提出の数にも残る)。数えずに先へ進めた生徒は dry-run の `stale_open_ignored` (人数)・
      配る生徒の行の `stale_open` (本数)。assigned_at が空の未提出は新しいものとして数える。`0` で従来どおり全部数える。
    - 一括の判定 (`routine_state`) と錠の中の読み直し (`_create_routine_grammar_drill(cutoffs=)`) は同じ値を使う (1 回の実行で 1 度だけ作って渡す)。
      比べ方は一括 = Python で `_ts_text` の文字列・錠の中 = SQL の `a.assigned_at >= ?` (naive UTC の 'YYYY-MM-DD HH:MM:SS' を渡す・従来と同じ形)。
  - **出すのはレビュー済みの出典だけ** (`_auto_delivery_source_ok`・上の英文法プールの節)。高校の理科・社会・国語と英検は自動では出さない。
  - **学年で中高を分ける** (`_student_grade_band`): 高校生 = english (文法 20 単元・`_eng_drill_unit_for_topic`) と math (科目まるごと・数学III なし)、
    中学生 = 高校入試演習の 'chugaku' の弱点を中学 5 教科の単元に完全一致で当てる (`_chu_drill_for_topic`。前置きつきの写しは使わない)。
    小学生・学年が判定できない生徒 (空・「その他」) には出さない (`WEAKNESS_ROUTINE_UNKNOWN_GRADE_AS_KOSEI=1` で判定できない生徒だけ高校生扱い)。
    選ぶとき (並べる前に区分の弱点だけ残す) と書き込む直前 (`_create_routine_grammar_drill` のガード・`_ROUTINE_BAND_GUARD_TRIPS`) の 2 回。
  - レベル: 高校生 標準+やや難・中3 標準+やや難・中1/中2/学年の数字なし 基礎+標準。
  - **既出の除外**: その生徒に前に配ったドリル (誰が配ったかを問わない) と単元ドリルの解答の問題は出さない。足りなければ最後に見たのが古い問題から足す。
    レビュー済みが 10 問に満たない単元は配らず次の弱点へ。
  - **dry-run は本番と同じ計画関数** (`_weakness_routine_plan`・在庫と既出の除外を含む)。`seed` を渡すと dry-run と本番で同じ問題になる。
    応答に `skipped_*`・`reasons` (区分違い・在庫なしの内訳)・`band_counts`・`grade_unknown_students`・`mode_changed_by_normalization`
    (全角・漢数字の学年で画面のモードが変わる生徒)・`allowlist`・`plan_version: 2`。名前は `include_names: true` のときだけ。
  - 二重配信の防止: Postgres では書き込み直前に `pg_try_advisory_xact_lock(8675313, 生徒ID)` (2 引数・f-string で埋める) を取り、
    錠の中で未提出 (14 日より前は数えない)・JST の日付で 3 日以内の 3日ドリルを読み直す (あれば `skipped_race`)。**1 引数の 8675309〜8675312・8675314 (クラス自動宿題) と番号を重ねない** (新しい錠は 8675315 以降)。
  - 監視: ON で起動したときだけ `_SCHEDULER_MAX_AGE_DAYS` に `weakness_drill_routine_run` (2 日)。実行記録は `_compact_run_props` の要約
    (名前なし・4000 字未満)。全員の作成に失敗したら / 学年ガードが動いたら `props.error` (失敗の通知)。`prod_healthcheck.py` は
    `OPTIONAL_UNTIL_FIRST_RUN` (履歴が無いうちは PASS。ON の後で OFF に戻したらそこから外す)。
  - ON にする手順: 塾長が dry-run を見る (`POST /api/admin/weakness-drill-routine/run` `{"dry_run": true}`・X-Cron-Secret) →
    `skipped_grade_unknown` の学年を直す・`mode_changed_by_normalization` の生徒が本当に中学生か確かめる・`capped` が多ければ `WEAKNESS_DRILL_ROUTINE_CAP` →
    Railway で `WEAKNESS_DRILL_ROUTINE_ENABLED=1` (★2026-10-16 時点で本番は ON・その日の 5:30 に新しいコードが回った)。
    デスクトップの予約タスク「2日に1回 弱点15問ミッション」は止めない (2026-10-16 塾長決定「両方配ってよい」・3日ドリルは予約タスクの行を数えない)。
  - CEO (📝 科目別 単元ドリル の下): 「🎯 自動の弱点ドリル」カードの 🔍 は `dry_run: true`・`include_names: true` だけを送る
    (ON/OFF・配る生徒と単元・在庫・学年が判定できない生徒・理由。**CEO から 3日ドリルを本番で回すボタンは作らない** = ON/OFF は env)。
    📦 は `source-inventory`。応答に `plan_version` が無ければ「サーバ反映待ち」。名前・学年は escapeHtml (inline だけ・ceo.js は触らない)。
    ★2026-10-16 塾長決定: 見出しは「今もう一度回したら配る: N 名」(旧「今日 ON なら配る」は、朝の実行の後は配った生徒が「未提出」
    「3日以内」に移ってふつう 0 名になり、動いていないと読み違えた)。その上に「前回の自動配信: M/D HH:MM に N 名」(応答の `last_run`
    {at_jst, at, delivered, error}・失敗は ❌ と理由・記録が無ければ「まだ記録がありません」・`last_run` の無い古いサーバでは出さない)。
    古い未提出を数えずに先へ進めた生徒は「14日より前の未提出は数えない N名」のチップ・配る生徒の行に「古い未提出 N 本」。
  - 配信済みドリル一覧 (`GET /api/admin/grammar-drill/list`) の既定は **塾長が配った分だけ** (`kind=owner`・今日の1問は出る)。
    自動配信は生徒ごとに 1 本ずつ作るので、混ぜると新しい 50 本から塾長の配信が押し出される。`kind=routine|class_hw|auto|all`・
    `subject=` (別名可・空の科目は english) で切り替える (CEO の帯・選んだ値は端末の localStorage)。初回診断はどれにも出さない。
    知らない kind・科目は 422。各行に `created_by` と `origin` / `group` / `class_label` (`class_hw_auto:<区分>:<クラス名>` から読む)。索引は足さない。
  - 回帰テスト: `scripts/health_check/test_weakness_routine_auto_delivery.py` (CI `server-tests.yml`。[10] が一覧と CEO のカード)。
- 生徒が自分で始める **今日の1問・初回診断** (配信ではないが中身はサーバが選ぶ) も、学年で科目を決めてレビュー済みの出典だけから出す
  (中学英語の節・`test_self_issued_drill_band.py`)。

## 塾生アプリのみ枠 (AIなし) と宿題ドリル (2026-09-24 塾長決定)
- **塾長方針: 英語の自由演習は開かない。AIなしの生徒が解けるのは「塾長が出した宿題」と「配信した単元ドリル」だけ。**
  2026-10-15 から、英語の受講クラスの宿題として科目別ドリルのレビュー済みの問題を自動で配る (下の 🏫 クラス自動宿題・既定 OFF)。
  これも「配信した単元ドリル」なので許可集合は変えない。
  `_AI_DISABLED_ALLOWED_EXACT / _PREFIXES` (middleware の許可集合) は変えない。`check_light_tier_middleware.py` が固定している。
  塾長が CEO で配る 🧪 習熟度テスト・📖 英語長文も「配信した単元ドリル」なので、許可集合を変えずに AIなし枠でも解ける。
- 宿題の「📝 ドリルで解く」(class.html → `dojo-drill.html?w_subject=&w_topic=&hw=<宿題ID>`) の結果保存は
  `POST /api/student/homework/{id}/drill-attempt` (prefix `/api/student/homework/` は元から許可)。本人の宿題でなければ 404、
  payload と INSERT は `/api/question-attempts` と同じ (`_record_question_attempt_core`)。`metadata.homework_id` で宿題を追える。
  ★2026-09-24 まで AIなしの生徒は宿題ドリルの最後に必ず「保存できませんでした (未ログイン or 通信エラー)」が出ていた
  (403 を通信のせいに見せていた)。`hw` 無しで直接開いた道場ドリルは AIなし枠では今も記録しない (方針どおり)。
- AIあり (AI学習アプリ申込・国公立難関大学コース) は承認した日から AI 全部が使える。翌月開始でも開始月まで待たせない (塾長決定 2026-09-24)。
  コード上の開始月ゲートは無い (課金の「翌月開始」= 台帳側の話とは別)。
- 既知の割り切り: 宿題モードの URL (`?hw=&w_topic=`) を手で書き換えれば別単元も宿題として記録できる。塾長方針は「入口を作らない」
  であって攻撃対策ではないので、サーバは本人の宿題かどうかだけを見る (単元一致・status・期限は見ない = 提出済みの解き直しも記録)。
  宿題モードでも弱点クレジット (`drillOrigin`) と `weakness/refresh-self` は従来の経路に投げる (AIなしは 403 を黙って捨てる・AIあり は弱点に反映)。
- 📄 **宿題の添付プリント** (2026-10-18 塾長「◎のとおりでお願いします…記号問題がいい」の第0段): 塾生アプリの宿題カードの
  「📄 プリントを開く」は `POST /api/student/homework/{id}/print` (prefix `/api/student/homework/` は元から許可 = 許可集合は不変)。
  本人の宿題に添付した**公開中**のプリントの `{file_path, title}` だけを返し (他人・添付なし・非公開・`/lesson-prints/` の形でない は 404)、
  画面は `/lesson-prints/….pdf` (vercel.json が R2 へ送る) に移る。AIなし枠は旧 `POST /api/student/lesson-prints/{id}/download` が今も 403
  (mypage は AIなし枠を class.html に送り返すので旧ルートのまま)。DL 履歴は生徒本人だけ数える (なりすましは数えない)。
  ボタンは宿題一覧の `print_open: true` があるときだけ (静的が API より先に出た窓で、押しても開けないボタンを出さない)。
  あわせて class.html の「提出:」と期限切れの判定を JST に (`gdLocalDate` は端末のタイムゾーンでなく JST 固定・`jstToday()`)。
  回帰テスト: `scripts/health_check/test_homework_print_open.py` (CI `server-tests.yml`・class.html は TZ=America/Los_Angeles で実行)。
- 📝 **記号の解答用紙 (マーク)** (同じ塾長決定の第1段・サーバ): 塾長が CEO の個別割当 / 📤 一括割当で `answer_sheet` を付けて出すと、生徒は
  アプリでマークして 1 回だけ提出し、サーバが採点する。★写真の提出 (第2段) は保留 (「記述式は採点が難しいのでしばらくは記号問題」)。
  - 表は 2 つ (init_db の CREATE TABLE IF NOT EXISTS だけ): `homework_answer_keys` (正解表・生徒に紐づけない・`key_json` は 1 始まり。
    要素 = 番号 / 番号の配列 (どれでも正解) / 0 (全員正解)・`label_style` = circled/katakana/upper/lower/seigo・2〜8 択 (正誤は 2)・`print_id`) と
    `homework_sheets` (宿題 1 行に 1 行・`homework_id` UNIQUE・割当と同じトランザクションで作る)。`_hw_sheet_ready()` が False (表が無い) のあいだ
    生徒の提出・解答用紙つきの割当・塾長の画面は 503「準備中」、一覧の `answer_sheet` は全部 None (`answer_sheet_ready: false`)。
  - 割当: `POST /api/admin/homework/assign` と `assign-bulk` の `answer_sheet` = `{mode:'choice', key_id}` か
    `{mode:'choice', key:{num_questions, num_choices, label_style, key}, print_id?}` (`mode:'none'` / 無し = 今までと同じ経路・応答も同じ)。
    中身は DB に触る前に 1 回だけ確かめる (`_hw_parse_answer_sheet`)。解答用紙つきだけ宿題の行を `INSERT … RETURNING id` で作る
    (題名で引き直さない)。同じプリント (添付 = 鍵) + 同じ中身の正解表は使い回す・違えば新しい行 (★割当で既存の表を書き換えない)。
  - 正解の打ち方 (`_hw_parse_key_text`・CEO の確認表 `POST /api/admin/homework/answer-keys/check` と同じ 1 か所): 「3142」「ウアエイ」「CADB」「正誤正正」
    「○×○○」・全角/半角/ひらがな・区切り自由・「問1③」「(1)ウ」「1.ウ」のような問番号つき (丸数字 / 記号があれば数字は問番号として読まない)・
    `[14]` = どれでも正解・`*` = 全員正解。数が違う・範囲外・読めない文字は理由つきの 422。
  - 生徒: 宿題一覧の各 item に `answer_sheet` {mode, available, num_questions, num_choices, label_style, labels, submitted, submitted_at (naive UTC),
    late, reset_count, answers, score_correct, score_total, results (問ごとの ○×), reveal, reveal_on, correct}。提出 `POST /api/student/homework/{id}/sheet`
    `{answers:[番号|null], student_note?}` (prefix は元から許可 = 許可集合は不変・AI なし)。本人の宿題でない / 解答用紙なし は 404・数や範囲は 422・
    番号は整数か短い数字の文字だけ (true・小数 2.0・Infinity / NaN / 1e999 = JSON の float は 422。本文は `Any` で受けて中で確かめる =
    `dict` 型だと本文が Infinity / [NaN] のとき FastAPI の 422 が入力を JSON に書けず 500)・メモは文字だけ・
    二度目は 409 (`submitted_at IS NULL` の UPDATE が 0 行・同時押しも)。採点はサーバだけ・同じトランザクションで宿題を completed。
    期限 (JST) を過ぎた提出は `late`。★正解の番号 (`correct`) は「提出済み かつ 期限の翌日 (JST) 以降」だけ (期限なしは提出直後)。
    提出前は期限が過ぎても出さない (期限後の提出を受け付けるので、見てから写せないように)。点数と ○× は正解表で毎回採点し直した値。
    解答用紙の宿題の `/complete` は 400 (完了 = 提出・古い画面の ✓完了 も止める)。なりすましの提出は `by_impersonation=1`。
    ★弱点集計 (`question_attempts`) には書かない (点数は「自習の記録」・解答解説 PDF は今も公開)。events は点数だけ。
  - 塾長 (admin Bearer): `GET /api/admin/homework/{id}/sheet` (答え・○×・正解・同じ表の問ごとの正解率と選ばれた番号の分布)・
    `GET /api/admin/homework/answer-keys?print_id=` (新しい順 = 先頭が使い回す表・used/submitted)・`GET /api/admin/homework/answer-keys/{key_id}`
    (その表を使う全員の結果と集計)・`PUT /api/admin/homework/answer-keys/{key_id}` (正解を直す → 提出済みを全員まとめて採点し直す・
    提出済みがいると問題数/択数は 409)・`POST /api/admin/homework/{id}/sheet/reset` (「やり直し」: 答え・点数・提出時刻を空に・宿題を open・
    前の答えと点数は events `homework_sheet_reset`)。生徒詳細の宿題一覧 (`/api/admin/homework/list`) と overview にも点数。
  - cascade: `homework_sheets` は 5 リスト + `admin_homework_delete` (同じトランザクション)・孤児掃除は「宿題の行が無い解答用紙」も消す。
    5 リストの loop は `_HW_SHEET_TABLES` を表が無ければ飛ばす (Postgres は失敗した 1 文でトランザクションごと止まるため)。
  - 回帰テスト: `scripts/health_check/test_homework_answer_sheet.py` (CI `server-tests.yml`)。
  - 画面 (同じ塾長決定の第1段・画面): 生徒の解答用紙は **`hw-sheet.js`** (root・ES5・`AJHwSheet`) の 1 か所で、塾生アプリ (class.html: 宿題タブの中に描く) と
    マイページ (mypage.js: 画面いっぱいの重ね `openOverlay`) が同じものを使う。★変えたら class.html と mypage.html の `hw-sheet.js?v=` を**両方**上げる。
    宿題一覧の `answer_sheet_ready === true` のときだけ使う (静的が API より先に出た窓・表が無い DB では今までどおり ✓完了)。
    解答用紙の宿題のカードは「✏️ 解答用紙に答える（全N問）」(✓完了 / ✅ 完了する は出さない = 完了は提出)・提出済みは 📝 8/10・「期限後」・「📝 結果を見る」。
    問ごとに記号のボタン (50px 角・もう一度押すと消せる)。下書きは localStorage `aj_hw_sheet_v1:<生徒ID>:<宿題ID>` (端末ごと・全部 try/catch・
    問題数 / 択数 / やり直しの回数が違う下書きは使わない・提出できたら消す)。空欄があれば問番号つきで確認・1 回だけ送る (送信中は止める)。
    提出したら点数と ○×・正解の記号はサーバの `reveal` のときだけ (期限前は「正解の記号は M/D（期限の翌日）から」)・提出時刻は JST。
    409 は一覧を読み直して提出済みの結果を出す (読めない / まだ未提出 / 正解表が無い 409 でもボタンを「⏳ 採点中…」のまま残さない)・
    422 は理由・503 / 未デプロイの 404 は「準備中」・通信失敗は下書きを残す。返事を待つ間も「← 宿題一覧に戻る」で戻れる
    (返事は裏で受け取り `onSubmitted(res, {left: true})` → 塾生アプリは一覧が出ているときだけ読み直す・マイページは refresh)。
    二度押し: 塾生アプリは一覧が出ていないと開かない (`hwListShown`)・マイページの重ねは 1 枚だけ (`openOverlay` が今の重ねを返す)。
    塾生アプリのメッセージの日時も `gdLocalDate` (JST)。hw-sheet.js が読めない端末・
    正解表が無い宿題は ✓完了 を出さずに案内だけ。hw-notice.js の数え方は変えない (解答用紙の宿題も status で数える = 提出で completed・やり直しで open)。
  - CEO (ceo.html inline の `window.CeoHwSheet`・ceo.js は触らない): 生徒詳細「📚 宿題」と 📤 一括割当に「✍️ 答え方」(完了ボタンだけ / 記号の解答用紙)・
    問題数・選択肢の数 (2〜8)・記号の種類 (①… / ア… / A… / a… / 正誤 = 2 択に固定)・正解 (記号のまま / 数字・全角・貼り付け可)。
    ★確認表 (問1 ウ …) は**サーバの読み方** `POST /api/admin/homework/answer-keys/check` に聞く (画面で読まない = 読み方は 1 か所)。確認中・数違い・読めない記号は割当を止める。
    `GET /api/admin/homework/answer-keys?limit=1` が通らない (表が無い・未デプロイ) と「✍️ 答え方」自体を出さない。payload の `answer_sheet` は
    記号の解答用紙のときだけ足す (無いときは今までと 1 バイトも同じ payload)。プリントを選ぶと `?print_id=` の先頭 (新しい順) の正解表を入れる
    (★打った正解は勝手に置き換えず「入れる」ボタン・「完了ボタンだけ」のときは案内だけ)。★プリント / 科目を替えたら、前のプリントから自動で
    入れた正解 (打ち直していない) は問題数・択数・記号ごと消して確認し直す (残すと正解表の無いプリントに前の正解が ✅ のまま付き、サーバがそれを
    そのプリントの正解表として保存 → 次から「前の正解表」として入る)。前のプリントの「入れる」も消す・別のプリントで打った正解は消さずに「⚠ プリントを
    変えました」。個別は割当てたら `reset()` (題名・プリントも空にする)。★📤 一括は**戻さない** (題名・プリント・期限が残るので、`reset()` で
    「完了ボタンだけ」に戻すと次の組は黙って ✓完了 の宿題になる): 出せたら `markSaved(data.answer_sheet, sheet.value, { title })` = いまの正解を「そのプリントに
    保存した正解表」にする (同じプリントの次の組にもそのまま付く・別のプリント / 科目に替えたら消える)。全員スキップ (answer_sheet が返らない) なら
    何も変えない。★保存した正解表を打ち直さずに入れたままなら、文字ではなく `{mode:'choice', key_id}` で送る (プリントなしの次の組も同じ表 =
    ✏️ で直すと全部の組を採点し直す)。✏️ で直したら、その表を入れたままのフォームに直した正解を入れ直す (打ち直したフォームは触らない)。
    ★プリントなしの表は出した宿題の題名を控え、題名を替えて出すときは `key_id` を使わず文字で送って新しい表にし、確認に「⚠ 入っている正解は、
    宿題「…」で使った正解表 #N のまま」(`getAnswerSheet({ title }).warn`。2026-10-18 点検 L1: 別の宿題が 1 つの表を使い、✏️ で片方を直すと
    もう片方の点数も黙って変わっていた。プリントありはプリントが鍵なので題名は見ない)。解答用紙なしで出すのにプリントに正解表があれば、確認に「⚠ 記号の解答用紙なし」の 1 行 (`getAnswerSheet().warn`)。宿題履歴に 📝 8/10・提出時刻 (JST = `fmtDate`)・期限後・
    なりすましの提出・「📊 問ごとの結果」(`GET answer-keys/{key_id}`: 問ごとの正解率・選ばれた記号の数・その表を使う生徒)・「✏️ 正解を直す」
    (確認表 → confirm「提出済み N 人をまとめて採点し直します」→ PUT)・「↩️ やり直し」(confirm → `POST …/sheet/reset`)。実施状況のチップに ✍️4/5。
  - 画面の回帰テスト: `scripts/health_check/test_homework_sheet_front.py` (CI `server-tests.yml`・node / osascript / jsc。本物のサーバの応答で動かし、
    画面が送る本文・CEO が作る `answer_sheet`・正解表 → 入力欄の文字をサーバに戻して確かめる)。
- 宿題モード (`?hw=`) の dojo-drill はメニュー (自由演習) を一切出さない: 自動起動できない・やめて戻る (確認あり)・読込失敗は
  すべて案内カード + 「塾生アプリの宿題に戻る」。class.html の「📝 ドリルで解く」は **単元 (topic) のある宿題だけ**に出す
  (無い宿題は提出ボタンだけ)。★残る抜け道: 公開の道場トップ (nyushi-dojo.html) からブックマークで直接開けば問題は解ける
  (取得はログイン不要) が、AIなし枠は保存が 403 で「宿題から開いた分だけ記録」と出る。塾長了承の割り切り (入口を作らない、が方針)。
- 宿題モードのドリルの結果は `question_attempts.metadata.homework_id` にだけ残る。**CEO 画面に宿題ごとの結果を出す機能はまだ無い**
  (塾長に見えるのは「✅ 完了 <日付>」と生徒メモだけ)。
- 回帰テスト: `scripts/health_check/test_homework_drill_attempts.py` (CI `server-tests.yml`)。
- 単元ドリルを解き終えた画面 (class.html `gdRenderResult` = 提出直後 / `gdOpen` の完了表示) には AIなし (`feed.ai_home_available === false`) の
  生徒にだけ AI学習アプリの案内 1 つ + 「💬 塾長に聞く」を出す (2026-09-24 塾長方針・`gdAiHintHtml` / `gdWireAskAi`)。ボタンは 💬 メッセージタブへ
  移るだけで mypage / 道場 / AI への入口にはしない。AIあり・旧バックエンド (undefined)・feed 未取得では出ない。
  金額 (+5,000 円) は `payment/courses.json` / `api/register-subscribe.py` に手で追従する (`check_course_price_sync.py` は class.html を見ない)。

## 🏫 クラス自動宿題 (塾生アプリのみ枠・英語だけ) (2026-10-15 塾長決定「基本的に2日に1回」)
- **AIなし (塾生アプリのみ) の通塾生に、受講している英語のクラスの宿題として、科目別ドリルのレビュー済みの問題だけで自動採点ドリルを配る**
  (`_run_class_homework_routine`)。AIあり・AI 体験中の生徒は 3日ドリルの側 (`_auto_delivery_ai_path` 1 か所で振り分け = 1 人 1 経路)。
  ON/OFF は env `CLASS_HW_AUTO_ENABLED` (既定 OFF・1/true/yes/on)。CEO の 🔍 / 📤 と管理 API は ON/OFF に関係なく動く。
- 対象: 在籍 (`_enrolled_sql`)・合成監視とテスト系の名前を除く・AIなし枠 (体験中でない)・通塾生 (course=kokuritsu_nankan か plan=student_addon =
  宿題タブが開ける)・受講クラスに英語のクラスがある・学年の区分が中学か高校 (`_student_grade_band`。空・「その他」・小学生には配らない =
  dry-run の `grade_unknown_students` に名前を出すので CEO で学年を直す)・受講開始月を過ぎている (NULL は制限なし)。
- **2 日に 1 回**: 毎朝 6:00 (`CLASS_HW_AUTO_HOUR_JST`・5〜22 に丸める) に回し、1 人に届くのはどのクラスからでも 2 日に 1 本まで
  (`CLASS_HW_INTERVAL_DAYS`・判定は 6 時間の遊びつき = 毎朝 6:00 の実行で 2 日前の 6:00:xx の配信も「2 日たった」になる。
  3日ドリルのような 1 日ずれは無いことを 2026-10-16 に確かめた・テスト [15])。未提出 (completed 以外) のクラス自動宿題が残っていれば積まない
  (2026-10-16 塾長決定: 数えるのは直近 `CLASS_HW_OPEN_STALE_DAYS`=14 日 (JST の日付) に配った未提出だけ・3日ドリルと同じ考え方・
  古いドリルは消さない・数えずに先へ進めた生徒は dry-run の `stale_open_ignored`・判定は `_class_hw_open_is_fresh` 1 か所 = 計画と錠の中)。
  英語のクラスを 2 つ取る生徒は、最後に届いたのが古いクラスから (同じなら時間割の順)。★そのクラスが下の wait_next の朝は、後に届いた
  クラスに回さずに、そのクラスの次の新しいドリル (ふつうは翌朝) を待つ。回すと、ドリルを作る日が 1 日ずれた 2 クラス (ON の手順の ONLY で
  1 クラスを先に始めたときなど) で、期限どおりに出す生徒ほどずっと同じクラスだけになる。待った回だけ間が 3 日 (テスト [6] が 10 日分で固定)。
- ドリルは (クラス, 区分) ごとに 2 日に 1 本 = 同じクラスの同じ区分は同じ問題 (CEO の問題別の正解率が比べられる)。2 日のうちのドリルがあれば
  新しく作らない。**同じ日 (JST) に作ったドリル**なら、後から受け取れるようになった生徒をそれに足す (`drills_joined`)。前の日に作ったドリルなら
  その朝は足さずに次の新しいドリルを待つ (`skipped_wait_next`・CEO「次の新しいドリルを待つ」)。★前の日のドリルに足すと 〆 まで 1 日になり、
  〆 の日 (6:00 の後) に出す生徒は毎回そうなって 1 日遅れのまま戻らない (`_class_hw_join_cutoff`・テスト [6] が 10 日分で固定)。
  印は `created_by = class_hw_auto:<区分>:<クラス名>` (列は足さない)。
- クラスと範囲は `_CLASS_HW_ROUTINE_MAP` (★キー = 時間割のクラス名。クラスが増えたら明示の 1 行を足す・テストが落ちる):
  英文法・中学英語のクラス → 高校生は english (文法 20 単元)・中学生は chugaku (中学基礎・中学2年 英語は中1・中2 の 8 単元) /
  英検のクラス → クラスの級の eiken (単語 → 長文空所補充 → 句動詞・熟語 → 内容一致・学年を問わない) / 長文のクラス → english_long の
  クラスの単元 (高校生だけ・レビュー済みの本文が `CLASS_HW_READING_MIN_PASSAGES`=4 本になったら始まる・本文 1 本) /
  GMARCH・早慶 = hold (まだ出さない) / 日曜 高校国語 = none。レベルは表の値 (英文法 Lv.1 基礎+標準・Lv.2/国公立 標準+やや難・高2 標準・
  中学応用 標準+やや難・中学基礎/中2 基礎+標準)。量は 10 問 (`CLASS_HW_AUTO_COUNT`)・英検の長文は本文 2 本 (`CLASS_HW_AUTO_PASSAGES`)。
- 単元: そのクラスのその区分の生徒の弱点 (student_weakness・合計 3 回以上・正答率 0.8 未満) を合わせた正答率の低い順 → 無ければ前回の次の単元 →
  全部が直近 `CLASS_HW_UNIT_COOLDOWN_DAYS`=14 日に出した単元なら一番前に出した単元。中学は前置きつきの写し (「中学英語 時制」) を数えない。
  問題はレビュー済みだけ (`_auto_pick_reviewed_question_ids` / 長文は `_auto_pick_reviewed_passages`)・そのクラスのその区分に前に出した問題は避ける。
- 題名「【<クラス名>】宿題 <単元>（N問・〆M/D）」(〆 = 配った日 + `CLASS_HW_INTERVAL_DAYS` 日 = 既定 2 日・JST)。
  塾生アプリのカードの 2 行目 (class.html `gdMetaText`) は、題名に 〆 があれば「いつでもOK」を出さない (題名と食い違うため)。
- 学年ガードは選ぶとき (区分の範囲だけ) と書き込む直前 (`_class_hw_deliver_group`: `_drill_subject_band_ok`・区分の科目・全員の区分・
  問題と本文の読み直し) の 2 回。止めたら `_CLASS_HW_BAND_GUARD_TRIPS` と `props.error`。
- 二重配信の防止: Postgres では書き込みの直前に `pg_try_advisory_xact_lock(8675314)` (1 引数・f-string) を取り、錠の中で 2 日のうちのドリルと
  生徒ごとの未提出 (計画と同じ境目 = 14 日より前は数えない)・2 日以内の受け取りを読み直す (別の実行が先に配った生徒は `skipped_race`)。毎朝の実行は events の実行記録で 1 日 1 回。
- お知らせは自動配信なので `source='auto'` (既定では LINE もメールも送らない・アプリ内の「🆕 新しい宿題」だけ)。
- 監視: ON で起動したときだけ `_SCHEDULER_MAX_AGE_DAYS` に `class_hw_auto_run` (2 日・配る生徒がいない日も記録)。記録は `_compact_run_props`
  (名前なし)。1 本も書けなかった / 学年ガードが動いたら `props.error`。`prod_healthcheck.py` は `OPTIONAL_UNTIL_FIRST_RUN`。
  配信ごとの記録は events `class_hw_auto_delivered` (生徒 id だけ)。
- 管理 API `POST /api/admin/class-homework-routine/run` (管理者トークンか X-Cron-Secret): 既定 `dry_run: true`・`class_label` (1 クラスだけ)・
  `all_classes` (`CLASS_HW_AUTO_ONLY_CLASSES` を無視)・`include_names` (CEO だけ)・`seed`。応答に `classes` (15 クラス・区分ごとの次の単元と理由・
  生徒ごとの状態)・`skipped_*`・`plan_version: 1`。
- ON にする手順: CEO の 🔍 で全クラスを見る (学年未設定・クラス未登録・在庫) → 1 クラスを 📤 で試す → Railway で
  `CLASS_HW_AUTO_ONLY_CLASSES=<そのクラス>` と `CLASS_HW_AUTO_ENABLED=1` → 1 回まわったら ONLY を外す。止めるのは `CLASS_HW_AUTO_ENABLED` を消すだけ。
  ONLY の名前が時間割と 1 つも一致しなければ、その朝はどのクラスにも配らず実行記録が error になる (全クラスに広げない)。🔍 の表の上にも赤いチップで出る。
- CEO (📝 科目別 単元ドリル の下・🎯 カードの次): 「🏫 クラス自動宿題」カード。🔍 は `dry_run: true`・`all_classes`・`include_names` だけ
  (15 クラスの表 = 出題範囲・区分ごとの次の単元と理由と在庫・配る生徒・外した生徒と理由・学年が判定できない生徒)。
  クラスの行の 📤 は confirm() の後でだけ `dry_run: false` + `class_label` (そのクラスだけ・押し直しても増えない)。
  「📋 結果」は下の配信済みドリル一覧を `kind=class_hw` に切り替える。inline だけ (ceo.js は触らない)。名前・学年・クラス名は escapeHtml。
  2026-10-16: 🎯 と同じく見出しは「今もう一度回したら配る」(旧「今朝回ったら配る」)・その上に「前回の自動配信」(`last_run` = events
  `class_hw_auto_run`。📤 の手動配信は入らない)・古い未提出のチップ。📤 の後の応答 (dry_run: false) は「配った」のまま。
- 回帰テスト: `scripts/health_check/test_class_homework_routine.py` (CI `server-tests.yml`)。3日ドリルと合わせた 1 人 1 経路の検査もここ。
  [14] が CEO のカードと塾生アプリのカードの 〆 を JS エンジンで実際に動かす (無ければ FAIL)。

## 🗓 今日の授業ブリーフ (2026-10-18 塾長「①の授業前ブリーフも作っておいて」= 成績を上げる提案 ①「授業で宿題を回す」)
- **読むだけ**の管理 API `GET /api/admin/class-brief?date=YYYY-MM-DD&class=<クラス名>` (`_class_brief_build`)。書かない・表を足さない・DDL なし・
  events にもログにも名前を出さない。★**管理者トークンだけ** (`_verify_admin_required`・名前を返すので X-Cron-Secret は 401)。
  date を省くと JST の今日 (`_class_brief_now` = テストが差し替える)・class は時間割のクラス名 (`_class_hw_label_key` で全角・空白の違いを吸収・
  曜日が違っても出す = `meets_on_date: false`)・形が違う日付と時間割に無いクラスは 400。応答 `version: 1` (CEO は無ければ「サーバ反映待ち」)。
- その日の曜日 (時間割の `dow`) のクラスごとに:
  - 名簿 = クラス自動宿題と同じ決め方 (在籍・合成監視とテスト系の名前を除く・通塾生・受講クラスにそのクラス・受講開始月の前は入れない = `before_start_n`)。
    AIあり / AIなし / AI 体験中 (`_auto_delivery_ai_path`) は入れて見分ける。最終ログインは JST・30 日を過ぎた (か一度も無い) = `login_stale`。
  - 未提出 = クラス自動宿題・3日ドリル・15問ミッション (`mission_2day_routine`)・塾長のドリル・塾長の宿題 (記号の解答用紙は印)。今日の1問・初回診断は数えない
    (生徒の画面の「新しい宿題」と同じ)。〆 = 宿題の期限 / クラス自動宿題の題名の「〆M/D」(`_class_brief_title_due`・12 月の「〆1/2」は翌年)。
    〆過ぎと日数は授業の日 (過去の日なら今日) で数える。`blocking` = 出さないと次の自動配信が止まる行 (クラス自動宿題と 3日ドリルの、積まない判定と同じ
    直近 14 日 = `CLASS_HW_OPEN_STALE_DAYS` / `WEAKNESS_ROUTINE_OPEN_STALE_DAYS`)。
  - 未提出 0 本の生徒は 2 つに分ける (2026-10-18 点検): 直近 14 日 (配った日) に届いたドリル + 宿題の本数 `received_n` が 1 以上 = 届いた分は全部出した
    (`all_done_n`) / 0 = **届いていない** (`not_delivered`・`not_delivered_n`。保留のクラス・学年が読めない・配れる弱点なし など)。届かない理由が分かるときは
    `delivery_note` (`grade_unknown` / `shougaku`)。★CEO の 🎉 と緑の「未提出 0名」は全員が届いた分を出したときだけ (何も届いていない生徒を「出した」と読まない)。
  - 出した人 (`submitted_this_week` = キーの名前は前のまま) = **前回の授業の開始** (`_class_brief_prev_meeting` = その日より前で一番近い同じ曜日の
    時間割の開始時刻・授業の日なら 7 日前) 〜 その日の終わり (JST) に completed (ドリル + 宿題)・一番よい点 (解答用紙の点も)・満点。境目は `praise_since` /
    `praise_since_jst`。旧「週の月曜 0:00 から」は月曜のクラスが当日しか数えず、土日に出した生徒がどこにも名前で出なかったので替えた (2026-10-18 点検)。
  - 誤答の多い 3 問 = 直近 14 日 (配った日) のドリルのうち、このクラスのクラス自動宿題 + ほかのドリルはこのクラスの 2 人以上に配った分で、問題の科目が
    このクラスの科目 (`_class_brief_subject_family` = クラス自動宿題の範囲の科目・保留の英語のクラスは英語の 4 科目・国語のクラスは国語・`top_missed_subjects`)
    のものだけ (英語のクラスに数学・理科を画面共有しない)。数えるのはこのクラスの生徒の提出済みの答えだけ・回答 2 件未満と誤答なしは選ばない・
    **このクラスのクラス自動宿題の問題で先に埋める** (ほかのドリルの 0% より先) → 正解率 → 回答の多い順 → 問題 id・一番選ばれた誤答 (同数なら番号の小さい方)・
    本文は題名だけ・習熟度テスト (科目 / 出典 `pt-` `ptest:`) と**無効化した問題 (`active = 0`・正解の誤りなどで退けた行)** は出さない
    (生徒のドリルの表示・採点と同じ。前の答えが残っていても数えない = 📺 で古い正解を ◯ にしない)。
- SELECT は名簿・未提出 2 (宿題は直近 14 日の提出済みも同じ 1 文で = 届いた本数)・前回の授業から 2 (全クラスの一番早い境目から読んで Python で分ける)・14 日の回答・問題・本文の題名・解答用紙を 1 回ずつ (生徒 id は 500 件ずつの IN・生徒ごとに回さない =
  テストが生徒 10 倍で SELECT の数が同じかを見る)。解答用紙は最後に読み、失敗したら rollback して印なしで続ける (Postgres は失敗した 1 文で止まるため)。
- CEO (ceo.html inline だけ・ceo.js は触らない): ハブ「👨‍🎓 生徒・学習」の**先頭**のボタン「🗓 今日の授業」→ `classBriefSection` (CEO を開いて最初に
  目に入る場所。📝 科目別 単元ドリルは開くまで見えないため)。🏫 クラス自動宿題カードの「🗓 今日の授業ブリーフ」からも開ける (`cbOpenFromCard`)。
  開いたときだけ読む。今日 / 明日 / 日付 / クラス (選択肢はサーバの `timetable` からその曜日のクラス・その曜日に無いクラスは「すべて」に戻す)。
  ★ハブのボタンと 🏫 カードのボタンは押すたびに **JST の今日** (`cbSetDay(0)`。前に 明日 を押した・タブを開いたまま日付が変わった でも今日に戻す)。
  🔄・日付・クラスの絞り込みは選んだ日のまま (`cbLoad`)。
  クラスごとに 在籍・未提出・〆過ぎ・⛔ 次が止まる・N日・🔑 ログイン切れの疑い・📭 届いていない (名前・学年が読めない・保留のクラス)・
  前回の授業から出した人 (✓本数・点・💯・境目の日時)・誤答の多い 3 問 (◯ 正解・✗ 一番多かった誤答・🏫 このクラスの宿題 / 📝 ほかのドリル)。
  名前は押すと生徒詳細。「📺 問題だけ表示」= Zoom の画面共有用の重ね (body 直下へ移す・**生徒の名前を持たない**・正解とクラスの正解率と一番多かった答えは
  「正解を見せる」の後だけ・← → で移ると正解はまた隠す・Esc / ✕ で閉じる・開いた時点の問題を持つ)。★重ねはダイアログ (ceo.js の `ceoConfirmDialog` と同じ型):
  開くとフォーカスを中のボタンへ (正解を見せる → 次 の順・Space / Enter で押せる。★最後の問題 (1 問だけのクラスは その 1 問) で見せた後は ✕ ではなく
  重ねそのもの (`#cbShare`・tabindex=-1) へ置き、そこでの Space / Enter は何もしない = 二度押し・押しっぱなしでも閉じない。閉じるのは Esc か ✕ を押した
  (Tab で選んだ) ときだけ。✕ に置くと続けて押した Space で閉じて下の未提出の名前が Zoom に映る)・Tab は中だけを回る・重ねの外に向いた Enter / Space は止める・
  キーは document の capture で受けて画面のショートカット (R・Esc で生徒詳細を閉じる) へ流さない・focusin で外へ出たら戻す・閉じたら開く前の場所へ戻す・
  開いている間は背後をスクロールさせない (止めないと Chrome は押した 📺 にフォーカスを残し、Space で 問1 に戻る・Tab → Enter で生徒詳細が重ねの下に開いて
  ✕ で閉じた瞬間に Zoom に出る)。404 / 405 / version なし = サーバ反映待ち・503 = 一時的。
  遅れて届いた前の応答で上書きしない (`_cbSeq`)。文字はすべて `_cbE` (escape)。
- 👀 未提出の行の「未開封 / 開いたが未提出」(`opened`・`unopened_count`) は ⏰👀 の節 (`_item_open_load` / `_class_brief_mark_open`・読むだけ)。
- 回帰テスト: `scripts/health_check/test_class_brief.py` (CI `server-tests.yml`・[8] の画面は node / osascript / jsc が無ければ FAIL)。
  [9] = 届いていない・クラスの科目・クラス自動宿題を先に・無効化した問題。[8] は 📺 のフォーカス (Tab・外へ向いた Space / Enter・R・閉じたら戻す・
  最後の問題で見せた後の Space / Enter で閉じない・1 問だけのクラス)・ハブ / 🏫 のボタンが今日を読むこと・🎉 の条件も見る。

## 📣 宿題・ドリルのお知らせはアプリの中で (2026-10-15 塾長決定「アプリを開けば分かる」)
- 宿題・ドリルを配ったときのお知らせは**アプリ内表示が基本**。LINE は宿題・ドリルのお知らせに使わない
  (★ログインコードの LINE `_try_line_login_push` / `magic_link_login` は従来どおり)。送る経路は `_homework_notify_channels(source)` 1 か所で決める。
  env は呼ぶたびに読む (Railway で変えれば再起動は要らない):
  - `HOMEWORK_NOTIFY_EMAIL` (既定 `manual`): `manual` = 塾長が CEO で手で配ったときだけ登録メール (多くは保護者のアドレス) /
    `all` = 自動配信でも毎回 / `off` = 送らない。`1`/`true`/`on` は all、`0`/`false`/`off` は off。不明な値は manual (警告ログ)。
  - `HOMEWORK_NOTIFY_LINE` (既定 `0`): `1` で従来の LINE (`grammar_drill_assigned`) に戻す非常スイッチ。
- **source の契約**: `_notify_grammar_drill_assigned(..., source=)` の `'manual'` は `POST /api/admin/grammar-drill/create`
  (塾長が生徒と中身を選ぶ) だけ。アルゴリズムが中身を選ぶもの (3日ドリル・クラス自動宿題。塾長が「今すぐ実行」を押した場合も) は `'auto'`。
  既定値は `'auto'` (渡し忘れてもメールを増やさない側に倒れる)。既定の env では自動配信は LINE もメールも 0 で、通知のループも待ちも走らない。
  新しい配信経路を足すときは必ず source を明示する (test が呼び出しを全部検査する)。
- メールのリンク: AIなし枠 (`_ai_blocked_now` が True) は `class.html?tab=homework`、AIあり・AI 体験中は `mypage.html?focus=homework`。
  ★`#homework` のような # 付きのリンクは使わない (ログインをはさむと auth-guard.js が path と search しか引き継がず # が消える)。
  照会は 1 回の SELECT (`_homework_notify_link_paths`)・失敗したら mypage (AIなし枠は mypage が class.html へ送り返す)。
- CEO の配信結果の文は `_drill_create_message` (経路に合わせる。「LINE/メールで通知を送信しました」と決め打ちしない・習熟度テストで飛ばした
  配信済みの生徒の数もここ)。応答に `notify_channels`。習熟度テストのメールは件名「🧪 習熟度テスト「…」が届きました」(📖🧪 の節)。
  3日ドリルの summary (dry-run も) に `notify` = {line, email}。
- 未提出 = `status <> 'completed'` (提出 API と同じ。デスクトップの予約タスクが書く `'assigned'` も未提出)。★これは生徒の画面の数え方。
  3日ドリルの「積まない」判定は自分の印の行の、直近 14 日の分だけを数える (🎯 の節)。`GET /api/student/grammar-drills` の
  `summary.open`・並び順、LINE の「やること」もこの数え方。`self_issued` = 生徒が自分で始めたもの (今日の1問・初回診断) で「新しい宿題」に数えない
  (`created_by` の生の値は返さない)。
- **アプリ内の「🆕 新しい宿題」** は `hw-notice.js` (root・ES5) の 1 か所で数える。class.html と mypage.html の両方が `?v=` 付きで読む
  (★変えたら**両方**の `?v=` を上げる)。新しい = 未提出で自分で始めたものではなく、この端末で前に宿題を見たときに無かったもの
  (記録は localStorage `aj_hw_seen_v1:<生徒ID>` に ID だけ・**端末ごと**・読み書きは全部 try/catch。記録が無ければ届いて 72 時間以内)。
  取れなかった一覧は記録を変えない。
  - 塾生アプリ (class.html): 宿題タブ以外の画面の上に帯「🆕 新しい宿題が N 件届いています」(押すと宿題タブ。無ければ 〆を過ぎた / 〆今日 の帯 = ⏰ の節)・カードに 🆕 新着。
    宿題タブで一覧を描いたら「見た」。`?tab=homework` と `#homework` で宿題タブに着地 (URL から消す)・401 のログインに `redirect=`。
    ドリルの未提出判定は `gdIsOpen` (completed 以外。以前は 'assigned' を「完了」と表示していた)・カードの 2 行目は `gdMetaText(it)` の 1 か所
    (〆・習熟度テストの文言はここに足す)。宿題 API が 403 (通塾生コース外) でも配られたドリルは出す。
  - マイページ (mypage.js): 📌 要対応チップが「🆕 新しい宿題 N 件」・カードに 🆕 新着。宿題欄が 1.5 秒見えたら / ドリルを開いたら「見た」。
    `?focus=homework` で宿題欄へスクロール。AIなし枠の送り返しは `class.html?tab=homework` に引き継ぐ。`AJHwNotice` は `_hwNotice()` 経由だけ
    (hw-notice.js が読めない端末は今までどおり)。
- 回帰テスト: `scripts/health_check/test_homework_notify_in_app.py` (サーバ)・`test_hw_notice_js.py` (hw-notice.js・class.html・mypage を
  node / osascript で実際に動かす。JS エンジンが無ければ FAIL) (CI `server-tests.yml`)。

## 📅 受講開始月と 🎬 入塾前アーカイブ (2026-09-24 塾長決定)
- **翌月開始の生徒も申込直後に承認してよい** (承認は課金に触れない・Stripe/台帳は月謝アプリ側)。承認すると予定表・配信された単元ドリル・メッセージは即使える。
- `students.start_month` ('YYYY-MM'・JST) が入っている生徒は、**開始月より前**は ①クラス宿題の一括配信 (`/api/admin/class/homework`) の対象外
  (期限の月 / 期限なしは今月で判定・response `skipped_before_start`) ②出欠を出さない (class.html) / 受けない (400) / 塾長の出欠名簿に載せない
  ③入塾月 (開始月の 1 日) より前の授業の録画を feed で出さない (`archive_from`・`hidden_recordings`) ④水曜の一声・ゼロ週メールを送らない
  (活動があった週の通常レポートは送る = 保護者向けの見本) ⑤クラス自動宿題を配らない (配る日の月で判定・skipped before_start)。
  生徒を指名する配信 (単元ドリル・個別宿題) は対象外 = 塾長が選んだ生徒には出る。3日ドリル (AIあり) も開始月を見ない。
- **`start_month` が NULL の生徒 (既存全員) はどの判定も従来と同じ経路** (feed の録画ループは `_cutoff` が None なら新しい分岐に入らない = 挙動は従来と同一)。
  2026-08-07 の「絞り込みで 36 名の録画が消えた」型の事故を繰り返さないための不変条件。`test_start_month_archive.py` が固定する。
- 承認時、入塾申込フォームの行の備考「受講開始月: 2026年10月（…）」(stripe-webhook が書く) から **新規生徒にだけ** 自動で入る。
  既存アカウントへの合流では入れない (在籍生に入ると入塾前の録画が消える) → response `start_month_skipped_existing` で CEO に知らせ、必要なら生徒詳細で手で入れる。
- 2 万円 (特商法「入塾前の授業アーカイブの視聴 20,000 円」) は `students.archive_full_paid=1` で全期間視聴。徴収は月謝アプリの講習費用 (カード) か振込で、
  **自動連動しない** (受け取ってから CEO の生徒詳細で ON)。全員向けの録画 (session_id NULL) は入塾月に関係なく出す。
- 録画の授業日は `class_recordings.lesson_date` → 無ければ題名の「M/D」を登録日から見て直近の過去に解決 (`_recording_lesson_date`) → 読めなければ登録日。
  自動割り当ては label (検証済み 'M/D') から入れる。CEO の授業詳細に 📅 で表示・修正できる。年つき/候補複数の題名は読まない (date_label と同じ)。
  feed 側の読み取りは区切り '/' と '月' だけ (「中1・2 英語」「Lesson 10-12」「1.5倍速」を日付にしない)。
- 後付け列 (start_month / archive_full_paid / lesson_date) は `_table_has_column` で有無を見てから SQL に書く (起動時の ALTER はロック待ちで飛びうる)。
  列が無い環境では機能が「制限なし」に倒れ、管理 API は 503 を返す。重複生徒の統合 (`_MERGE_FILL_FIELDS`) は `archive_full_paid` だけ埋める
  (`start_month` は在籍生を縛る向きに働くので埋めない = 承認の合流と同じ)。
- 運用メモ: このデプロイより前に承認した翌月開始の生徒は `start_month` が NULL (制限なし) → CEO の生徒詳細で手で入れる。
  題名から日付が読めない録画は授業詳細で「📅 日付不明 (登録日で判定)」と出るので 📅 で入れる。制限は開始月の 1 日 (JST) に自動で外れる。
- ceo.js を変えたら `ceo.html` の `ceo.js?v=` を上げる (2026-09-24: `20260924a-start-month`)。

## 授業録画の割り当て (YouTube 限定公開 → 各クラス)
- 塾長が YouTube の**再生リスト**に授業動画を上げる → それを各クラスの `class_recordings` に割り当てる。
  **毎朝 JST 7:00 に自動で走る** (2026-10-08 塾長決定「毎日自動にしたい」。それまでは自動では走らなかった)。
  - API プロセス内の常駐スケジューラ `_class_rec_auto_assign_scheduler` (起動条件: `CRON_SECRET` があり、
    `CLASS_REC_AUTO_ASSIGN_ENABLED` が `0` / `false` / `off` / `no` でない。判定は `_class_rec_auto_assign_env_enabled` 1 か所で、
    監視の対象もこれで決まる)。**止めるときは Railway の env `CLASS_REC_AUTO_ASSIGN_ENABLED=0` → 再起動**
    (ボタンとターミナルは止まらない)。7 時を過ぎてから起動したら、その日まだ走っていなければすぐ走る。
  - 中身はボタンと同じ `_class_rec_auto_assign_run` を **dry_run=False・allow_partial=True (「取れた分だけ登録」)** で呼ぶ。
    hazard (二重登録の恐れ) は従来どおり免除しない = その日は 1 件も登録しない。
  - **塾長へのメール** (`_send_monitor_email` = 宛先 `MONITORING_TO_EMAIL`、未設定なら `DAILY_SNS_TO_EMAIL`。
    Resend キーか宛先が無ければ送らずログだけ)。本文は授業名・日付 (M/D)・件数・保留の理由だけで、
    動画ID・再生リストIDは先頭4文字も載せない (`_class_rec_mail_safe`)。何も無い日は送らない。
    登録した日・停止の日は必ず送る。**保留・確認事項だけの日は、前回送れた通知と中身 (指紋 `fp`) が違うときだけ**
    (同じなら 7 日ごとに再通知 = 対応しないと決めた保留で毎朝同じメールが届き、本物が埋もれるのを防ぐ)。
    STALE (最新の録画が 28 日より前)・録画 0 本のクラスも通知の理由に入る (`build_plan` の `stale`。自動にすると ① 確認を
    見る人がいなくなるため)。送信結果は events `class_rec_assign_mail` (sent・理由・指紋だけ)。送れなかった保留は翌朝もう一度送る。
  - 実行記録は events `class_rec_assign_run` (件数の要約だけ。新着が無い日も書く)。**登録と同じトランザクション・同じ錠の中で**
    書くので 1 日 1 回 (新旧 2 コンテナが同時に 7 時を迎えても 1 回分)。2 日記録が無ければ停止、全体停止
    (hazard で全部断った・登録後の確認で異常・1 クラスも見に行けなかった) は `props.error` = 5 分監視の「定期実行の失敗」に乗る。
    一部クラスの保留は error にしない (毎朝 critical が鳴ると本物が埋もれる) → その日のメールで知らせる。
  - **一時的な失敗 (例外・YouTube 全断 = 1 クラスも取得できない) は 30 分おきに最大 2 回やり直し** (7:00 → 7:30 → 8:00)、
    最後の回だけ error を記録してメールする。その記録は `retryable` で「今日はもう済んだ」に数えない (再起動すれば走り直す)。
    例外の記録も錠の中で「今日もう済んだか」を確かめてから書く (新旧 2 コンテナの片方の例外が、もう片方の正常な記録を上書きしない)。
    判定は `_class_rec_ran_today_on` (source=scheduled で retryable でない記録だけを数える)。
  - 毎朝の実行が error のまま塾長がボタンの「② 登録」で直したら、回復の記録 (source=button・recovered) を足して監視の
    critical を止める (`_class_rec_mark_recovered`。最新の記録が error のときだけ書く = ボタンで停止を隠さない)。
  - 手で走らせる方法も残っている:
  ```
  railway run -s Postgres python3 scripts/class_recordings/assign_from_playlists.py           # 確認だけ (何も登録しない)
  railway run -s Postgres python3 scripts/class_recordings/assign_from_playlists.py --apply   # 投入
  ```
  または **CEO の再生リスト一覧 `youtube-playlists.html` の「🎬 授業録画をクラスに割り当てる」ボタン**
  (サーバ側で同じ処理・ターミナル不要。① 確認する → ② この内容で登録 の 2 段)。
- ★**手順は「① DB を読む → 接続を返す → ② YouTube を読む → ③ build_plan → ④ 新しい接続で錠を取り、錠の中で登録済みを
  読み直してから書く」**。YouTube を待つ間に DB の接続を持たない (冒頭の「`db()` の接続を掴んだまま外部APIを待たない」)。① と ④ の間に入った登録は
  ④ の読み直し (`video_id()` で比べる = URL の書き方違いも拾う) で飛ばす。並行で読むと YouTube が 1 本だけ解析できない
  ページを返すことがあるので、すぐ返ってきた失敗だけ 1 回読み直す (ボタンでは時間切れ・接続できないは読み直さない。
  毎朝の実行は画面が待っていないので、それも 20 秒あけて 1 回読み直す)。
- ★**排他は 2 段**: 同じプロセスは `_AUTO_ASSIGN_LOCK` (取れなければボタン 409・定期実行は 10 分後にやり直す)、
  プロセスをまたぐのは `pg_try_advisory_xact_lock(8675312)` を ④ の書き込み直前に取る (待たない・トランザクション終了で外れる)。
  **錠を YouTube の取得中に持たない** (接続とトランザクションが要るので、`idle_in_transaction_session_timeout` に切られ、プールも 1 本塞ぐ)。
  `class_recordings` に UNIQUE 制約は足さない (起動時DDLの規則: 既存の重複が 1 件でもあると executescript 全体が巻き戻る)。
- ★**判定の正典は `server/class_recording_assign.py`**。CLI とボタンの API がこれを共有する。
  ロジックを `main.py` や CLI に書き写さないこと (片方だけ直されて判定がずれる)。
  置き場所が `server/` なのは Railway のデプロイ範囲がそこだから (`scripts/` は本番に無い)。
- **どのクラスの録画かは「再生リスト名の曜日+限」で決まる**。動画のタイトルは信用しない
  (2026-08-06: 火曜3限の動画名が「8.３」だったが正は火曜=8/4)。日付ラベルだけは動画名から取り、
  再生リストの曜日・未来日で検算して、読めなければ推測せず手作業に回す。
  **名前が読めない再生リストは丸ごと対象外**なので、新学期に作り直したら名前を付け直すこと
  (名前は同じ画面から編集するとサーバに保存される)。
- ★**日付ラベルの年は「過去側の直近」で決める** (`resolve_year`)。年は動画名に書かれないので、
  「今日にいちばん近い年」を採ると**半年より古い回が翌年に化ける**。2026-08-28 に実測: 日曜1限の
  「2月8日」が 2027-02-08 (月曜) と読まれ、正しい 2026-02-08 (日曜) に「曜日が合わない —
  手で確認する」と誤報していた (画面上は塾長の打ち間違いに見えるので気づけない)。
- ★**「古い日付は打ち間違い」で弾かない**。1年ぶんの回が入った再生リストを初めて取り込むと、
  正しい過去回が丸ごと手作業に回される (同日に日曜1限で実測 11本)。打ち間違いの本命
  =「前回のタイトルをコピペして日付を直し忘れる」は**7の倍数のズレ**なので日数の上限では
  そもそも捕まらない。捕まえるのは `build_plan` の**同じ授業に同じ日付ラベル**検査。
  古い回は登録したうえで「参考」に出す (`OLD_LABEL_DAYS`)。
- ★**読めない URL は「1件ある」で終わらせない**。動画IDを読めない録画は二重登録の恐れ =
  `--allow-partial` でも免除しない停止条件なので、**どの録画か**(録画番号・授業・伏せたURL・理由)
  を出さないと全クラスの配布が恒久的に止まる。録画番号は `ceo.html` の授業詳細にも出している。
- ★**「動画ではない」と断じる判定は、安全な形の側から数える** (`may_hide_video_id`)。
  2026-08-28 に一度「10〜12文字のトークンが無ければ動画ではない」と**壊れ方の側から**数えて、
  貼り付けで空白が1つ混ざった `youtu.be/dQw4w9W gXcQ` を素通りさせた (同じ動画が2本入る。
  UNIQUE 制約が無いので取り返せない)。壊れ方は無限にあるので数えきれない。
  止めないのは再生リスト・チャンネル等の一覧URLと空URLだけ。迷う形は必ず止める側へ。
- ★**`provider_of` は `server/main.py` の `_detect_video_provider` と同じ規則で書く**
  (録画行に provider を付けているのはあちら)。hostname で判定すると `http(s)://` を省いた
  `youtu.be/xxx` が link に落ち、見張りから丸ごと外れる。
- ★**一覧を N件で打ち切るときは、止めている行から並べる**。DB の行順のまま切ると
  「登録は止めません」と書かれた無害な行だけが並び、「1件あるので登録しません」と言いながら
  その1件が画面に出ない = 直したはずの事故が別の形で戻る。溢れた分は「うち何件が止める行か」を言う。
- ★**この仕組みの目的は「配布漏れを配布済みと誤報告しない」こと**。「取得できなかった」を
  「0本 = 新着なし」と言わせない判定が本体で、`scripts/class_recordings/check_assign_logic.py` が
  機械で固定している。ガードを1つ消すとこのゲートが落ちる (変異18種で確認済み。
  日付・URL 判定と `build_plan` の計画づくりも同じゲートが見る)。
  ★**変異試験は「危ない入力が検査の見える位置に無い」形でも試す**こと。並べ替えを足したら
  「無害な行を先頭に置いた入力」、上限で切るなら「上限より多い危ない入力」でないと、
  ガードを消しても偶然緑になる (2026-08-28 に実際に2回この空振りを作った)。
  書き込む側 (二重登録しない・dry-run が本当に書かない) は
  `scripts/health_check/test_auto_assign_api.py` が `server-tests.yml` で見る。
- ★**クラウドの Claude Code (claude.ai/code) からは実行できない**。ネットワークポリシーが
  YouTube と Railway を遮断しており (403)、認証情報の問題ではないので回避できない。
  塾長の端末の Claude Code なら `railway run` が通る。クラウドのセッションに頼むときは
  **CEO 画面のボタンを塾長が押す**か、ターミナルの出力を貼って判断だけさせる。
- `class_recordings` に UNIQUE 制約が無く**重複は取り返せない**。ボタン・毎朝の自動実行とターミナルを同時に走らせないこと
  (ボタンと自動実行は上の 2 段の錠で互いに排他するが、ターミナル `assign_from_playlists.py --apply` とは排他できない。
  朝 7 時台にターミナルで --apply しない)。
- 書き込む側 (毎朝の実行・排他・読み直し・伏せ字・通知・監視) は `scripts/health_check/test_class_rec_daily_assign.py` も見る。

## かきじゅん (書き順学習 PWA・`kakijun-app/`)
- **作業前に `kakijun-app/HANDOFF.md` を必ず読む**。設計の分離 (お手本=フォント / 判定=線データ /
  経路は見せない) を崩すと必ず破綻する。今日それで何度も塾長を往復させた。
- 配信は**ビルド済み成果物をリポジトリ直下 `/kakijun/` に入れて**行う。
  ソースを直しただけでは本番は変わらない。`node tools/publish-to-repo.mjs` を必ず回す。
- 出荷前に Playwright で**実画面のスクリーンショットを撮って自分の目で確認する**。
  検査が緑でも見た目が壊れていることがある。
