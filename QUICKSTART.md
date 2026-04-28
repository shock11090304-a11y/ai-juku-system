# ⚡ QUICKSTART: 半日で本番稼働（4ステップ）

各ステップ完了後、私（Claude）に「Step X 完了」とお知らせください。
次のステップのサポートや、つまずいた場合の対処を即座に行います。

---

## 🎯 全体像

```
[09:00] Step 1: ドメイン購入            (15分)
[09:15] Step 2: GitHub → Vercel       (30分)
[09:45] Step 3: Railway + 環境変数     (45分)
[10:30] Step 4: Stripe 商品作成         (30分)
[11:00] 🎉 本番稼働・保護者配信開始
```

---

## 📝 Step 1: ドメイン購入（15分・¥1,500程度）

### 推奨サービス
- **お名前.com** https://www.onamae.com （最大手・決済即反映）
- **ムームードメイン** https://muumuu-domain.com （分かりやすい）

### ドメイン名の推奨パターン
既存塾のブランドに合わせて:
- `[塾名]-ai.jp` （例: tokyo-juku-ai.jp）
- `ai-[塾名].com`
- `[塾名]juku.jp`

**避けるべき:**
- 長すぎる名前（検索で入力ミスされる）
- ハイフン2つ以上
- `-school` などの一般名詞のみ

### 購入手順
1. 上記サイトでドメイン検索
2. 利用可能なら「¥年1,000〜¥3,000」で購入
3. WHOIS代行公開（プライバシー保護）を**オン**に設定
4. クレカ決済

### ✅ Step 1 完了条件
- [ ] 購入完了メール受領
- [ ] ドメイン名をメモ（例: `my-juku.jp`）

---

## 🌐 Step 2: GitHub → Vercel デプロイ（30分）

### 2-1. GitHub リポジトリ作成（5分）

```bash
# 既に git init とコミット済み。GitHub CLI があれば:
cd /Users/adachishouhei/ai-juku-system
gh repo create ai-juku-system --public --source=. --push
```

GitHub CLI がない場合:
1. https://github.com/new でリポジトリ作成（名前: `ai-juku-system`、public でOK）
2. ターミナルで:
```bash
cd /Users/adachishouhei/ai-juku-system
git branch -M main
git remote add origin https://github.com/あなたのユーザー名/ai-juku-system.git
git push -u origin main
```

### 2-2. Vercel デプロイ（10分）

1. https://vercel.com にアクセス
2. **Sign up with GitHub** でログイン
3. **Add New... → Project**
4. `ai-juku-system` リポジトリを選択 → **Import**
5. 設定画面はそのまま（Framework: Other、その他デフォルト）
6. **Deploy** ボタン

2-3分で `https://ai-juku-system-xxxx.vercel.app` が発行されます。

### 2-3. カスタムドメイン設定（15分）

1. Vercel プロジェクト → **Settings → Domains**
2. 購入したドメイン（例: `my-juku.jp`）を入力 → **Add**
3. Vercelから表示される指示に従ってDNS設定:
   - **お名前.com**: DNS設定 → DNSレコード設定 → Aレコード `76.76.21.21`
   - 詳細: https://vercel.com/docs/projects/domains/add-a-domain
4. 数分待つと緑のチェックマーク表示 = SSL自動発行完了

### ✅ Step 2 完了条件
- [ ] `https://my-juku.jp/lp.html` でLPが表示される
- [ ] `https://my-juku.jp/` でLPにリダイレクトされる

---

## 🖥 Step 3: Railway で バックエンド稼働（45分）

### 3-1. API キーを用意（15分）

**Anthropic API キー:**
1. https://console.anthropic.com にサインアップ
2. Billing → クレジットカード登録（月$5程度の余裕あり推奨）
3. API Keys → Create Key → コピー（`sk-ant-api03-xxx...`）

**Stripe API キー:**
1. https://stripe.com にサインアップ（日本の事業者として登録）
2. Developer → API keys → Secret key をコピー（`sk_live_xxx...`）
3. **まずテストモードで検証推奨**（キーが `sk_test_xxx` で始まる）

### 3-2. Railway デプロイ（20分）

1. https://railway.app にサインアップ（GitHub連携）
2. **New Project → Deploy from GitHub repo**
3. `ai-juku-system` を選択
4. **Root directory**: `server` に設定（重要！）
5. デプロイ開始（2-3分）

### 3-3. 環境変数設定（10分）

Railway プロジェクト → **Variables** タブで以下を追加:

```env
ANTHROPIC_API_KEY=sk-ant-api03-あなたのキー
STRIPE_SECRET_KEY=sk_test_あなたのキー
STRIPE_WEBHOOK_SECRET=（Step 4-2 で設定）
STRIPE_PRICE_STANDARD=（Step 4-1 で設定）
STRIPE_PRICE_PREMIUM=（Step 4-1 で設定）
STRIPE_PRICE_FAMILY=（Step 4-1 で設定）
STRIPE_PRICE_STUDENT_ADDON=（Step 4-1 で設定）
BASE_URL=https://my-juku.jp
```

Variables 保存 → 自動再デプロイ → URL発行（例: `ai-juku-api-production.up.railway.app`）

### ✅ Step 3 完了条件
- [ ] `https://ai-juku-api-xxx.up.railway.app/api/health` が `{"ok":true}` を返す

---

## 💳 Step 4: Stripe 商品作成（30分）

### 4-1. 商品・価格作成（20分）

https://dashboard.stripe.com/test/products で「+ 商品を追加」を4回実行:

| # | 商品名 | 価格 | 課金タイプ | 通貨 |
|---|---|---|---|---|
| 1 | スタンダード | 24,980 | 月次（Recurring） | JPY |
| 2 | プレミアム | 39,800 | 月次（Recurring） | JPY |
| 3 | 家族プラン（最大3名） | 59,800 | 月次（Recurring） | JPY |
| 4 | 塾生アドオン | 9,800 | 月次（Recurring） | JPY |

各商品作成後、**Price ID**（`price_xxxx`）をコピーし、Railway の環境変数に設定。

### 4-2. Webhook 設定（10分）

1. Stripe Dashboard → **Developers → Webhooks**
2. **+ Add endpoint**
3. **Endpoint URL**: `https://ai-juku-api-xxx.up.railway.app/api/stripe/webhook`
4. **Events to send** で以下を選択:
   - `checkout.session.completed`
   - `invoice.payment_succeeded`
   - `customer.subscription.deleted`
5. **Add endpoint** → 作成された Webhook の **Signing secret**（`whsec_xxx`）をコピー
6. Railway の環境変数 `STRIPE_WEBHOOK_SECRET` に貼付け保存

### ✅ Step 4 完了条件
- [ ] `my-juku.jp/lp.html` → 「¥1,980で3日間試す」ボタン → Stripe決済画面が開く
- [ ] テストカード `4242 4242 4242 4242` で決済成功
- [ ] Stripe Dashboard の Subscriptions に表示される

---

## 🎉 本番稼働・ローンチ開始

全ステップ完了後、以下を実行:

### 最初の配信（当日）
1. `https://my-juku.jp/broadcast-center.html` を開く
2. 塾名・塾長名・LP URL (`https://my-juku.jp/student-upgrade.html`)・締切日を入力
3. 「LINE短文」テンプレをコピー → LINE公式アカウントから一斉配信
4. 保護者からの問合せ対応開始

### 目標
- Week 1: 塾生アドオン **10名成約** = ¥15万/月
- Week 4: 塾生アドオン **50名成約** = ¥75万/月

---

## 🆘 つまずいたら

各ステップでエラーや不明点があれば、以下の情報をお知らせください:

- どのステップで詰まっているか
- エラーメッセージ（スクショ可）
- 実行したコマンドや設定

私が即座に具体的な対処法をご案内します。

---

## 📦 既に準備済みのファイル

✅ 全文件がコミット済み（git status clean）
✅ `vercel.json` - Vercel設定
✅ `.gitignore` - secrets保護
✅ `.env.example` - 環境変数テンプレート
✅ `server/Dockerfile` / `server/Procfile` / `server/railway.json` - 各ホスティング対応
✅ `server/main.py` - Stripe決済実装（4プラン + 入塾金 + トライアル）
✅ `robots.txt` / `sitemap.xml` - SEO対応

---

**準備OK。Step 1 から順番に進めてください。**
