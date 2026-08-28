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
  ログインさせて実地確認する。届かないときの救済は CEO 画面の
  **「🔗 magic link 指定アドレス送信」**(送信 cap も LINE 優先配信も迂回して直送) →
  それでも駄目なら **「🔑 OTP 緊急発行」**(コードを画面に出して口頭で渡す)。
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
- 子メールを確認済みにすると、**週次レポートの生徒向けコピーの主宛先が親→子に移る**。保護者にも
  残すなら生徒本人のマイページで「保護者メール」(`students.parent_email` = 別列) を設定してもらう。

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
  を出さないと全クラスの配布が恒久的に止まる。再生リストURL等「動画IDを隠しようがない URL」は
  止めない (`may_hide_video_id`)。provider 列が空の古い行は URL から見分ける (`provider_of`)。
- ★**この仕組みの目的は「配布漏れを配布済みと誤報告しない」こと**。「取得できなかった」を
  「0本 = 新着なし」と言わせない判定が本体で、`scripts/class_recordings/check_assign_logic.py` が
  機械で固定している。ガードを1つ消すとこのゲートが落ちる (変異11種で確認済み。
  日付・URL 判定と `build_plan` の計画づくりも同じゲートが見る)。
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
