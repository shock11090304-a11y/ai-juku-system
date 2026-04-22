# 🚀 デプロイメントガイド

AI学習コーチ塾の本番環境デプロイ手順（所要時間: 約30分）

---

## 📋 事前準備

- [ ] GitHub アカウント
- [ ] Vercel アカウント（無料: https://vercel.com）
- [ ] ドメイン（お名前.com / ムームードメイン等で取得・年¥1,000〜¥3,000）
- [ ] Anthropic API キー（バックエンド用 / 後述のRailway/Renderにセット）

---

## 1️⃣ フロントエンド (LP + アプリ) のVercelデプロイ

### Step 1: GitHubリポジトリ作成

```bash
cd /Users/adachishouhei/ai-juku-system
git init
git add .
git commit -m "Initial commit"
# GitHub CLIを使う場合
gh repo create ai-juku-system --public --source=. --push
```

### Step 2: Vercelにインポート

1. https://vercel.com/new にアクセス
2. GitHubリポジトリを選択
3. **Framework Preset**: `Other`（静的サイト自動判定）
4. **Root Directory**: 空欄（プロジェクトルート）
5. **Build Command**: 空欄
6. **Output Directory**: 空欄
7. 「Deploy」をクリック

2-3分で自動デプロイ完了。
→ `https://ai-juku-system-xxxx.vercel.app` が発行される。

### Step 3: カスタムドメイン設定

1. Vercel プロジェクト → **Settings** → **Domains**
2. 取得したドメイン（例: `ai-juku.jp`）を追加
3. Vercelから指示されたDNSレコード（Aレコード or CNAME）を
   ドメイン管理画面で設定
4. 数分でSSL証明書自動発行・公開完了

### Step 4: 確認URLの更新

デプロイ完了後、以下のファイルの `your-domain.com` を実URLに置換:

- `broadcast-center.html` のLP URL変数（ブラウザで動的に上書き可能）
- `student-upgrade.html` のお問合せリンク
- `legal.html` の事業者メールアドレス

---

## 2️⃣ バックエンド (FastAPI + SQLite) のデプロイ

### オプションA: Railway（推奨・最速）

1. https://railway.app にサインアップ
2. **New Project** → **Deploy from GitHub repo**
3. `server/` ディレクトリを指定
4. **Variables** タブで以下を設定:

```
ANTHROPIC_API_KEY=sk-ant-api-...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_PRICE_STANDARD=price_...
STRIPE_PRICE_PREMIUM=price_...
STRIPE_PRICE_FAMILY=price_...
LINE_CHANNEL_ACCESS_TOKEN=（任意）
LINE_CHANNEL_SECRET=（任意）
BASE_URL=https://your-domain.com
```

5. Railwayが自動で `uvicorn main:app --host 0.0.0.0 --port $PORT` を実行
6. 公開URL発行（例: `https://ai-juku-api-production.up.railway.app`）

**料金**: 月$5〜（リソース使用量次第）

### オプションB: Render

1. https://render.com → New Web Service
2. GitHub連携
3. **Environment**: Python 3
4. **Build**: `pip install -r server/requirements.txt`
5. **Start**: `cd server && uvicorn main:app --host 0.0.0.0 --port $PORT`
6. 環境変数設定（Railwayと同じ）

**料金**: 無料枠あり（スリープ付き）、常時稼働は月$7〜

### Step 2: フロントエンドから新URLを参照

`checkout.js` の `API_BASE` が本番URLを自動参照するよう既に設定済み:
```js
const API_BASE = window.location.origin.includes(':8090')
  ? 'http://localhost:8000'  // dev
  : window.location.origin;  // prod
```

本番では `BASE_URL` 環境変数がバックエンドを指していればOK。
もしAPI サーバーが別ドメインの場合、以下のように明示指定:

```js
const API_BASE = 'https://ai-juku-api.example.com';
```

---

## 3️⃣ Stripe 本番設定

### Step 1: Stripeダッシュボードで商品作成

https://dashboard.stripe.com/products にて以下を作成:

| 商品名 | 価格 | Billing |
|---|---|---|
| スタンダード | ¥24,980 | Recurring monthly |
| プレミアム | ¥39,800 | Recurring monthly |
| 家族プラン | ¥59,800 | Recurring monthly |
| 塾生アドオン | ¥15,000 | Recurring monthly |
| 入塾金 | ¥20,000 | One-time |
| 3日間体験 | ¥1,980 | One-time |

各商品の **Price ID**（`price_xxx`）をコピー。

### Step 2: Webhook設定

https://dashboard.stripe.com/webhooks にて:
- **Endpoint URL**: `https://your-api-domain/api/stripe/webhook`
- **Events**: `checkout.session.completed`, `customer.subscription.deleted`, `invoice.paid`

Signing Secret (`whsec_xxx`) を環境変数 `STRIPE_WEBHOOK_SECRET` に設定。

---

## 4️⃣ ドメイン・SSL・SEO チェック

- [ ] `https://your-domain.com/lp.html` が閲覧可能
- [ ] `https://your-domain.com/` で LPにリダイレクト
- [ ] SSL証明書が緑色
- [ ] `/robots.txt` が配信される（SEO用・Vercel自動生成）
- [ ] OGP画像が表示される（SNSシェア用）
- [ ] Google Search Console 登録（sitemap.xml送信）

---

## 5️⃣ 環境変数一覧（.env.example）

```bash
# --- Anthropic API ---
ANTHROPIC_API_KEY=sk-ant-api-...

# --- Stripe ---
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_STANDARD=price_...
STRIPE_PRICE_PREMIUM=price_...
STRIPE_PRICE_FAMILY=price_...
STRIPE_PRICE_STUDENT_ADDON=price_...
STRIPE_PRICE_TRIAL=price_...
STRIPE_PRICE_ENROLLMENT=price_...

# --- LINE Messaging API（任意）---
LINE_CHANNEL_ACCESS_TOKEN=
LINE_CHANNEL_SECRET=

# --- 基本設定 ---
BASE_URL=https://your-domain.com
```

---

## 6️⃣ デプロイ後の動作確認

```bash
# 基本疎通確認
curl https://your-domain.com/lp.html  # 200 OK 期待
curl https://api.your-domain.com/api/health  # {"ok": true}

# チェックアウトフロー
1. LP → 「¥1,980で3日間試す」ボタン
2. checkout.html → Stripe Checkout セッション作成
3. 決済完了 → checkout-success.html
4. Webhook でサブスク登録確認（Stripeダッシュボード）
```

---

## 🔧 トラブルシューティング

**Q: Vercelデプロイ後、LPは表示されるがアプリ(index.html)が404**
→ 相対パスリンクの確認。`href="/index.html"` に統一推奨。

**Q: Stripe Webhookが届かない**
→ `STRIPE_WEBHOOK_SECRET` の設定を確認。Stripeダッシュボード→Webhooks→Logsで送信試行を確認。

**Q: Anthropic APIがCORSエラー**
→ バックエンドプロキシ経由で呼び出す設計になっているため、フロントから直接呼ばない。

---

## 📞 問合せ先

- Vercel サポート: https://vercel.com/help
- Railway: https://railway.app/help
- Stripe サポート: https://support.stripe.com
- Anthropic: https://support.anthropic.com
