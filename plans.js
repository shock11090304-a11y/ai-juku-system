// ==========================================================================
// プラン設定（一元管理）
// このファイルを編集するだけで、LP/checkout/チェックアウトに即反映
// ==========================================================================

const PLAN_CONFIG = {
  // 新規向け3プラン
  plans: {
    standard: {
      id: 'standard',
      name: 'スタンダード',
      price: 24980,
      priceLabel: '¥24,980',
      tagline: 'AI学習を始めるなら',
      maxStudents: 1,
      aiModel: 'sonnet',
      color: '#3b82f6',
      features: [
        { name: '24時間AIチューター', included: true },
        { name: 'AI問題自動生成（月30回まで）', included: true },
        { name: '英作文・記述添削（月10回まで）', included: true },
        { name: '学習診断・カリキュラム生成', included: true },
        { name: 'オリジナル参考書生成（月3冊まで）', included: true },
        { name: 'AIモデル: 標準（Sonnet 4.6）', included: true },
        { name: '最上位AIモデル(Opus 4.7)', included: false },
        { name: '添削無制限', included: false },
        { name: '家族プラン（複数生徒）', included: false },
      ],
    },
    premium: {
      id: 'premium',
      name: 'プレミアム',
      price: 39800,
      priceLabel: '¥39,800',
      tagline: '差額¥15,000で全機能解放',
      maxStudents: 1,
      aiModel: 'opus',
      color: '#8b5cf6',
      recommended: true,
      features: [
        { name: '24時間AIチューター（最上位）', included: true },
        { name: 'AI問題自動生成（無制限）', included: true },
        { name: '英作文・記述添削（無制限）', included: true },
        { name: '学習診断・カリキュラム生成', included: true },
        { name: 'オリジナル参考書生成（無制限）', included: true },
        { name: 'AIモデル: 最上位（Opus 4.7 + Extended Thinking）', included: true },
        { name: '優先処理（AI応答の速度優先）', included: true },
        { name: '保護者向け詳細レポート', included: true },
        { name: '家族プラン（複数生徒）', included: false },
      ],
    },
    family: {
      id: 'family',
      name: '家族プラン',
      price: 59800,
      priceLabel: '¥59,800',
      tagline: '兄弟姉妹3名まで使える',
      maxStudents: 3,
      aiModel: 'opus',
      color: '#ec4899',
      features: [
        { name: 'プレミアムプランの全機能', included: true },
        { name: '🆕 生徒アカウント最大3名まで', included: true, highlight: true },
        { name: '🆕 家族ダッシュボード（全員の進捗一覧）', included: true, highlight: true },
        { name: '🆕 兄弟姉妹のカリキュラム相互参照', included: true, highlight: true },
        { name: '🆕 保護者向け家族レポート', included: true, highlight: true },
        { name: '生徒1人あたり実質¥19,933/月', included: true, note: true },
        { name: '優先サポート', included: true },
        { name: 'AIモデル: 最上位（Opus 4.7）', included: true },
        { name: '全機能無制限', included: true },
      ],
    },
  },

  // トライアル・アドオン
  trial: {
    price: 1980,
    priceLabel: '¥1,980',
    duration: '3日間',
    description: '体験料（単発）',
  },

  enrollment: {
    price: 20000,
    priceLabel: '¥20,000',
    description: '入塾金（初回のみ・システム登録費）',
  },

  // 既存塾生向けアドオン
  studentAddon: {
    price: 15000,
    priceLabel: '¥15,000',
    description: '塾生限定アドオン（月謝に追加）',
    features: [
      '最上位AIモデル（Opus 4.7）',
      '全AI機能無制限',
      '教材生成・参考書作成無制限',
      '講師によるAI学習履歴の週次レビュー',
      '塾の宿題とAI自動連携',
      '保護者向け統合レポート',
    ],
  },

  // 年間先払い割引
  annualDiscount: {
    standardAnnual: { monthly: 24980, annual: 249800, saved: 49960, label: '年間¥249,800（2ヶ月分お得）' },
    premiumAnnual: { monthly: 39800, annual: 398000, saved: 79600, label: '年間¥398,000（2ヶ月分お得）' },
    familyAnnual: { monthly: 59800, annual: 598000, saved: 119600, label: '年間¥598,000（2ヶ月分お得）' },
    studentAddonAnnual: { monthly: 15000, annual: 150000, saved: 30000, label: '年間¥150,000（¥30,000お得）' },
  },
};

// グローバル公開
if (typeof window !== 'undefined') window.PLAN_CONFIG = PLAN_CONFIG;
if (typeof module !== 'undefined' && module.exports) module.exports = PLAN_CONFIG;
