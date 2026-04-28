# 🚀 ローンチ前チェックリスト

実運用開始前の必須確認項目（所要時間: 約2時間）

---

## 📋 Phase 1: ローカル動作確認（30分）

### アプリケーション機能
- [ ] `http://localhost:8090/lp.html` LPが正常に表示される
- [ ] 3プラン（スタンダード¥24,980 / プレミアム¥39,800 / 家族¥59,800）が表示される
- [ ] 「¥1,980で3日間試す」ボタンが checkout.html に遷移する
- [ ] checkout.html でプラン切替が動作する（price summary が変化）
- [ ] index.html（メインアプリ）が開き、8タブ全てアクセス可能
- [ ] AI問題生成で各科目（英語・古文・数学・理科・歴史）が正しく動作
- [ ] 模試履歴の追加・削除・詳細表示が動作
- [ ] 模試保存後に「保護者メール送信」ポップアップが出る
- [ ] 家族ダッシュボードで家族プラン切替→生徒3名追加可能
- [ ] 保護者メール 6 テンプレートが mailto: で開ける
- [ ] 塾生LP（student-upgrade.html）が正常表示
- [ ] 配信センター（broadcast-center.html）でQRコード生成可能

### 管理機能
- [ ] CEOダッシュボード（ceo.html）でプラン管理テーブルが表示
- [ ] 特商法ページ（legal.html）に全プラン価格が記載
- [ ] 管理メニューの全ボタン（塾生LP・配信・教材生成等）が動作

---

## 📋 Phase 2: デプロイ準備（30分）

### GitHub 準備
- [ ] `git init` して `.gitignore` が機能（`.env` がコミット除外）
- [ ] GitHub リポジトリ作成
- [ ] `git push origin main` 成功

### Vercel（フロントエンド）
- [ ] Vercelにリポジトリをインポート
- [ ] デプロイ成功（緑のOK表示）
- [ ] 発行されたURL（`xxx.vercel.app`）でLPが表示される
- [ ] 独自ドメイン購入
- [ ] Vercel の Domains にドメイン追加
- [ ] DNS設定完了・SSL証明書自動発行
- [ ] `https://trillion-ai-juku.com/lp.html` が正常表示

### Railway/Render（バックエンド）
- [ ] Railway/Renderアカウント作成
- [ ] `server/` ディレクトリを指定してデプロイ
- [ ] 環境変数設定:
  - [ ] `ANTHROPIC_API_KEY`
  - [ ] `STRIPE_SECRET_KEY`
  - [ ] `STRIPE_WEBHOOK_SECRET`
  - [ ] `STRIPE_PRICE_STANDARD`
  - [ ] `STRIPE_PRICE_PREMIUM`
  - [ ] `STRIPE_PRICE_FAMILY`
  - [ ] `STRIPE_PRICE_STUDENT_ADDON`
  - [ ] `BASE_URL=https://trillion-ai-juku.com`
- [ ] `/api/health` エンドポイントが `{"ok": true}` を返す

---

## 📋 Phase 3: Stripe設定（30分）

### 商品・価格作成
- [ ] Stripe ダッシュボードで以下の商品を作成:
  - [ ] スタンダード ¥24,980/月（Recurring）
  - [ ] プレミアム ¥39,800/月（Recurring）
  - [ ] 家族プラン ¥59,800/月（Recurring）
  - [ ] 塾生アドオン ¥9,800/月（Recurring）
- [ ] 各商品の Price ID を環境変数に設定

### Webhook設定
- [ ] Stripe > Developers > Webhooks で エンドポイント追加:
  - URL: `https://your-api.example.com/api/stripe/webhook`
  - Events: `checkout.session.completed`, `invoice.payment_succeeded`, `customer.subscription.deleted`
- [ ] Signing Secret (`whsec_xxx`) を `STRIPE_WEBHOOK_SECRET` に設定

### 決済フロー動作確認（テスト環境）
- [ ] テストカード `4242 4242 4242 4242` で決済成功
- [ ] Webhookが届き、DBに生徒ステータスが `paid` で更新される
- [ ] 初回請求書に入塾金 ¥20,000 + 体験 ¥1,980 が計上される
- [ ] 3日後に月額 ¥39,800 が自動課金される（テストクロック推奨）
- [ ] 塾生アドオンの決済では入塾金が含まれない

---

## 📋 Phase 4: セキュリティ & 法的（15分）

### セキュリティ
- [ ] `.env` ファイルがGitHubに上がっていない（gitignore確認）
- [ ] Anthropic API キーが漏洩していない（フロントエンドに含まれていない）
- [ ] Stripe シークレットキーが漏洩していない
- [ ] SSL証明書が全ページで有効（緑の鍵マーク）

### 法的・運用
- [ ] `legal.html` の事業者情報を実際の塾情報に更新:
  - [ ] 事業者名
  - [ ] 所在地
  - [ ] 電話番号（非公開可・請求で開示）
  - [ ] メールアドレス
  - [ ] 代表者名
- [ ] 返金ポリシー記載確認
- [ ] プライバシーポリシー確認
- [ ] `support.html` の連絡先が正しい

---

## 📋 Phase 5: 実運用テスト（15分）

### 保護者・生徒視点での体験
- [ ] スマホ（iPhone/Android）でLPが正常表示
- [ ] スマホで体験申込み→決済まで完了できる
- [ ] 決済完了後、index.html（アプリ）にログインできる
- [ ] メールクライアントから保護者メール（mailto:）が開く
- [ ] QRコードをスマホカメラで読み込めば LPに遷移

### 講師視点での運用
- [ ] 配信センター（broadcast-center.html）で配信文がコピーできる
- [ ] LINE配信用の文言が文字化けなく表示
- [ ] 模試登録→保護者メール送信ポップアップが動作
- [ ] CEOダッシュボードで全生徒のプラン状況が見える

---

## 🎯 ローンチ当日の動き

### 朝9時: 既存塾生保護者への一斉配信
```
1. 配信センター（broadcast-center.html）を開く
2. 塾名・塾長名・LP URL・締切日を入力
3. 「LINE短文」テンプレートをコピー
4. LINE公式アカウントから一斉配信
5. 並行してメール配信（家族割引対象者に個別）
```

### 10-12時: 問合せ対応
```
- LINE返信「AI希望」→ アドオン追加を月謝システムに反映
- 目標: 午前中に10名成約
```

### 13-18時: 面談
```
- 予約保護者との対面 or Zoom
- 面談トークスクリプト（broadcast-center.html）に従う
- 即決特典 ¥5,000割引を活用
```

### 夜: 結果集計
```
- 成約数を ceo.html で確認
- 未決裁者へリマインドLINE送信
- 明日の動きを計画
```

---

## 📊 Week 1 目標KPI

| 指標 | 目標 | 計測 |
|---|---|---|
| LP PV | 500 | Vercel Analytics |
| 体験申込み | 30件 | checkout-success.html 到達 |
| 塾生アドオン成約 | 20名 | ceo.html プラン別生徒数 |
| 月商インパクト | ¥30万 | 保護者合計課金額 |

---

## ⚠️ トラブル対応マニュアル

### LP が表示されない
→ Vercel Deployment ログ確認 → ビルドエラー解消

### Stripe決済でエラー
→ Stripeダッシュボード > Logs で具体的エラー確認
→ Webhook 着信確認

### AI応答が来ない
→ Railway/Render の ANTHROPIC_API_KEY を確認
→ `/api/health` でバックエンド疎通確認

### 保護者からの問合せが多い
→ 配信センターのFAQを強化
→ メールテンプレート（塾生アドオン案内）で返信

---

**🎉 全項目チェック完了 = ローンチ準備完了**
