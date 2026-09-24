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
- **取込 API の落とし穴**: `POST /api/admin/grammar/import` は 1 リクエスト **2000 問まで**。
  `unit` は `server/main.py` の `GRAMMAR_UNITS` と**完全一致**でないと **無言で skip** される (英語のみ。他科目は任意 unit 可)。
  重複判定は `source_exam_question_id` があれば (その id + stem)、無ければ (stem + unit + subject) の完全一致。
  **押し直しても二重登録されない**代わりに、既存問題の解説を直したいときは再 import では**上書きされない** (INSERT 専用)。
  直すなら DB を直接更新するか、行を無効化 (`active=0`) してから入れ直すこと。
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
- 初回診断・今日の1問・弱点ルーティンは `subject = 'english'` を直書きしているので、科目を分けるだけで
  「高3の最初の1問が中2の過去形」を防御コード無しに避けられる。
- CEO のレベル4択は「範囲の軸」なので、そこに学年の軸を混ぜると「基礎も含める」と区別できなくなる。
- 単元名は `scripts/chugaku_dojo/units.json` の eng の `filter` と**完全一致**させる (入試道場の弱点 topic と突き合わせるため)。
  並び順は `server/main.py` の `_GRAMMAR_SUBJECT_UNIT_ORDER` が持つ (english 以外は既定で在庫数の降順になり、学習順にならない)。
- ★**`question_attempts.subject = 'chugaku'` は中学生の英数国理社が collapse した 1 バケット** (`:6705` の注記)。
  ドリル科目の「中学英語」とは別物なので、週次レポートの科目ラベルは `_WEEKLY_SUBJECT_LABEL_OVERRIDE` で
  「高校入試演習」に差し替えてある。ここを `_GRAMMAR_SUBJECT_LABEL_JA` に任せると、数学しか解いていない生徒の
  保護者レポートが「中学英語が苦手」になる。弱点ルーティンが chugaku をドリル化しないのも同じ理由 (科目が特定できない)。
- **在庫は 1 単元 100 問 (基礎25 / 標準45 / やや難30。時制だけ基礎38で113問)**。2026-09-24 に中学生が
  25 名いると分かったので 741→1,213 問に増やした。既定 (標準〜やや難) が 75 問なので、同じ単元で
  25 問のドリルを **3 回**まで配れる。★ただし `exclude_drill_id` は **ドリル1本しか除外できない**ので、
  3 回目は 2 回目とは別だが **1 回目と半分ほど重なる** (75-25=50 問から引くため)。「3回とも別問題」ではない。
  ★**この 3 回という数字が在庫設計の根拠**。50 問だと 2 回、25 問ちょうどだと 2 回目が必ず 400 になる。
- シードは `seed-data/chugaku_drill_pool_v1.json` 1 本 (1,213問・約18,000行)。ボタンは `#chugakuPoolImportBtn`。
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
- 提出は `question_attempts.subject='eiken'` / `topic=単元名` で記録される。診断・今日の1問・弱点ルーティンは english 直書きなので英検問題は流れない。
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

### 📖 長文型ドリル = 本文 1 つに設問が複数 (2026-09-24 塾長「長文読解・長文空所補充も単元ドリルに」→「A で」)
- 表 `grammar_passages` (subject/unit/level/title/body/body_ja/source/body_hash/active) + `grammar_questions.passage_id / passage_seq` (後付け列)。
  `_grammar_has_passages()` は **列と表の両方** を `_table_has_column` で見る (CREATE TABLE だけロック待ちで飛び ALTER だけ通ると「列はあるが表が無い」
  になり、Postgres では失敗したトランザクションが同じ接続の単発ドリル抽出まで 500 にする)。**本文のある単元は「本文 N 本」単位で出題**
  (`_grammar_pick_drill_passages`・設問は passage_seq 順・score_total は設問数・`passage_count` 既定 2 = 本番の大問 1 回分・上限 5・設問が全部
  inactive の本文は選ばない)。判定はサーバが単元の在庫で行う (client が count を送っても無視) ので、弱点対策の再配信など古い経路から来ても本文が
  バラけない。`exclude_drill_id` は前回の **本文ごと** 除外。1 問ずつの抽出 (`_grammar_pick_drill_question_ids` = 科目全体・弱点ルーティン) は
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
- **平日に `POST /api/cron/weekly-reports?dry_run=true` を叩くと「先週の完了週」で評価される** (`_weekly_report_window`)。
  日曜だけ「今週」。平日の dry run で対象外と出ても日曜に送られないとは限らない。
- **mypage の初期化は補助スクリプトを最大 10 秒しか待たない** (`_ajWidgetWait`)。`slApiFetch` は既定 30 秒でタイムアウト
  (`options.timeoutMs` で個別に延長・AI 生成系は 90 秒)。合格可能性スコアはサーバ失敗 (5xx/429/通信) で消えず再試行を案内し、
  4xx (志望校未設定など) だけ非表示。
- **LINE 連携 CTA** (`#lineLinkSection`) は `/api/auth/me` の `line_linked === false` の生徒にだけ出る (LINE の userId は返さない)。
- 回帰テスト: `scripts/health_check/test_student_ux_2026_09.py` (CI `server-tests.yml`)。

## 塾生アプリのみ枠 (AIなし) と宿題ドリル (2026-09-24 塾長決定)
- **塾長方針: 英語の自由演習は開かない。AIなしの生徒が解けるのは「塾長が出した宿題」と「配信した単元ドリル」だけ。**
  `_AI_DISABLED_ALLOWED_EXACT / _PREFIXES` (middleware の許可集合) は変えない。`check_light_tier_middleware.py` が固定している。
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

## 📅 受講開始月と 🎬 入塾前アーカイブ (2026-09-24 塾長決定)
- **翌月開始の生徒も申込直後に承認してよい** (承認は課金に触れない・Stripe/台帳は月謝アプリ側)。承認すると予定表・配信された単元ドリル・メッセージは即使える。
- `students.start_month` ('YYYY-MM'・JST) が入っている生徒は、**開始月より前**は ①クラス宿題の一括配信 (`/api/admin/class/homework`) の対象外
  (期限の月 / 期限なしは今月で判定・response `skipped_before_start`) ②出欠を出さない (class.html) / 受けない (400) / 塾長の出欠名簿に載せない
  ③入塾月 (開始月の 1 日) より前の授業の録画を feed で出さない (`archive_from`・`hidden_recordings`) ④水曜の一声・ゼロ週メールを送らない
  (活動があった週の通常レポートは送る = 保護者向けの見本)。生徒を指名する配信 (単元ドリル・個別宿題) は対象外 = 塾長が選んだ生徒には出る。
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
  **自動では走らない** (常駐スケジューラも cron も無い)。走らせ方は 2 つ:
  ```
  railway run -s Postgres python3 scripts/class_recordings/assign_from_playlists.py           # 確認だけ (何も登録しない)
  railway run -s Postgres python3 scripts/class_recordings/assign_from_playlists.py --apply   # 投入
  ```
  または **CEO の再生リスト一覧 `youtube-playlists.html` の「🎬 授業録画をクラスに割り当てる」ボタン**
  (サーバ側で同じ処理・ターミナル不要。① 確認する → ② この内容で登録 の 2 段)。
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
- `class_recordings` に UNIQUE 制約が無く**重複は取り返せない**。ボタンとターミナルを同時に走らせないこと
  (ボタン側は同時実行を 409 で弾くが、ターミナルとは排他できない)。

## かきじゅん (書き順学習 PWA・`kakijun-app/`)
- **作業前に `kakijun-app/HANDOFF.md` を必ず読む**。設計の分離 (お手本=フォント / 判定=線データ /
  経路は見せない) を崩すと必ず破綻する。今日それで何度も塾長を往復させた。
- 配信は**ビルド済み成果物をリポジトリ直下 `/kakijun/` に入れて**行う。
  ソースを直しただけでは本番は変わらない。`node tools/publish-to-repo.mjs` を必ず回す。
- 出荷前に Playwright で**実画面のスクリーンショットを撮って自分の目で確認する**。
  検査が緑でも見た目が壊れていることがある。
