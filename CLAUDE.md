# ai-juku — プロジェクト指針 (Claude 用)

オンライン塾の受験生向け AI 学習 SaaS。公開: trillion-ai-juku.com

## 構成 / デプロイ
- **静的フロント** (Vercel): リポジトリ直下の `*.html` / `*.js` (mypage.html, dojo-drill.html, app.js, english-exam.js 等)。
- **バックエンド API** (Railway): `server/main.py` (巨大単一 FastAPI)。本番 = `https://ai-juku-api-production.up.railway.app`。
- **DB**: Postgres (Railway)。read-only 照会: `railway run -s Postgres python3 -c "import os,psycopg;c=psycopg.connect(os.environ['DATABASE_PUBLIC_URL'])..."`
- **決済**: Stripe。
- `main` への push で Vercel(静的) と Railway(API) が**両方自動デプロイ**。静的は数秒、API は ~1分。
- **DB接続プール**: `db()` は psycopg_pool(max_size=`DB_POOL_MAX`既定16・単一プロセス前提)。不具合時は env `DB_POOL_ENABLED=0` → 再起動で直接connectへ即フォールバック。★将来 `uvicorn --workers N` 化するなら 16×N が Postgres `max_connections`(現100) を超えないよう `DB_POOL_MAX` を絞ること。
  - 取込API等は**デプロイ済みのコードを検証**するので、新 part/ルートを足したら「push→デプロイ反映確認→その後にデータ投入」の順を守る (逆順は無効扱いで弾かれる)。

## ⚠️ Vercel Hobby「12 Serverless Function 上限」(最重要 footgun)
- `api/` 配下 (**サブディレクトリ含め再帰的に**) の handler を定義した `.py` が Vercel の Serverless Function として数えられ、**Hobby プランは12個が上限**。`api/v2/foo.py` のようにサブディレクトリに置いても1関数として数えられる(直下だけの問題ではない)。
- **13個目を足すと Vercel デプロイが「全体」失敗し、本番が前ビルドで凍結する** (新URL 404 / app.js が古いまま / `gh` の "Vercel" status=failure)。`py_compile` も `vercel.json` も通るのに本番だけ落ちるため診断が難しく、**過去3回再発** (74e2c5fb / 216d9ac / d59461f)。
- **現在 12/12 (満杯)。** 新しい `api/*.py` を**足さないこと**。
- 新しい決済系エンドポイントが必要なら、**既存関数に action を同居**させる:
  `vercel.json` の rewrite で `/payment/api/<new>` → `/api/<existing>?__ep=<action>` に振り、関数内で `__ep` 分岐。
  (例: `admin-charge-month-end-preview` / `admin-charge-history` は両方 `admin-charge-readonly.py` に同居。)
- ★ `api/*.py` を増やす前に必ず `bash scripts/check_vercel_function_cap.sh` で関数数を確認 (13個=exit 1)。
  CI (`.github/workflows/vercel-function-cap.yml`) も push 時にこれを実行し、超過を即・明確に赤チェック化する。
  (※ API ロジックの追加は基本 Railway 側の `server/main.py` に書く。`api/*.py` は Stripe 等の Vercel 専用関数のみ。)
