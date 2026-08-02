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
- **PDF を作るなら passage / stem / choices / explanation の 4 つを漏れなく KaTeX に通す**。通し忘れると日本語フォントで `¥(AB=6¥)` と出る。整形は必ず LaTeX 描画の**前**に行う (後だと SVG path が本文に漏れる)。
- 作ったら `scripts/kyotsu_mogi2026/preflight.py` (取込契約) と `audit.py` (総点検) を必ず通す。詳細な経緯は `scripts/kyotsu_mogi2026/README.md`。

## Vercel は Pro プラン (2026-07-18 に Hobby から移行済み)
- 商用利用の規約準拠 + B2B(学校導入)前提で Pro 化 ($20/月・$20分の従量クレジット込み。現使用量は枠内に余裕)。
- **旧「12 Serverless Function 上限」は解消済み**: Hobby 固有の上限だったため、`api/*.py` の個数で Vercel デプロイが失敗することはもう無い (過去3回の本番凍結事故 74e2c5fb / 216d9ac / d59461f は Hobby 時代の話)。
- **アーキテクチャ方針は不変**: API ロジックは Railway 側の `server/main.py` に書く。`api/*.py` は Stripe 等「Vercel でしか動けない」関数のみ (現12個が基準値)。
- `scripts/check_vercel_function_cap.sh` と CI (`.github/workflows/vercel-function-cap.yml`) は基準値超過を**警告するだけの非ブロッキング**(常に exit 0) に変更済み。正当に関数を増やしたときは同スクリプトの `BASELINE` を実数に更新して警告を止める。
- 既存の `__ep` action 同居 (例: `admin-charge-month-end-preview` / `admin-charge-history` は `admin-charge-readonly.py` に同居) はそのまま稼働中・触らない。新規に Vercel 専用関数が本当に必要なら素直に足してよい (同居の曲芸は不要になった)。
- 本番が古いままの症状 (新URL 404 / app.js が古い / `gh` の "Vercel" status=failure) を見たら、関数数ではなく Vercel ビルドログと healthcheck の `deploy_freshness` を見る。
