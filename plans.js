// ==========================================================================
// プラン設定（一元管理）
// このファイルを編集するだけで、LP/checkout/チェックアウトに即反映
// ==========================================================================

const PLAN_CONFIG = {
  // 新規向け3プラン
  plans: {
    // 🎁 創設メンバー 50名限定 永年¥14,500 (体験 → 本契約への目玉プラン)
    // 一度契約すれば永年この価格 (値上げなし)。50名到達で募集終了。
    // 旧 founder1 (¥25,000・100名) は 2026-04-28 廃止 → 本プランに置換。
    // server 側 PRICE_MAP では 'founder1' エイリアスも本プランに紐付け済 (後方互換)。
    founder_special: {
      id: 'founder_special',
      name: '創設メンバー (永年特典)',
      price: 14500,
      priceLabel: '¥14,500',
      tagline: '50名限定・契約後は永年この価格・全機能無制限',
      maxStudents: 1,
      aiModel: 'opus',
      color: '#fbbf24',
      recommended: true,
      badge: '🎁 50名限定',
      quotas: { problems: null, essays: null, textbooks: null },
      features: [
        { name: '24時間AIチューター（無制限）', included: true, highlight: true },
        { name: 'AI問題自動生成（無制限）', included: true, highlight: true },
        { name: '英作文・記述添削（無制限）', included: true, highlight: true },
        { name: '学習診断・カリキュラム生成', included: true },
        { name: 'オリジナル参考書生成（無制限）', included: true, highlight: true },
        { name: '5試験対応 (TOEFL/TOEIC/IELTS/英検/大学入試)', included: true, highlight: true },
        { name: '英字ニュース読解 (CNN/Japan Times/BBC ほか)', included: true, highlight: true },
        { name: '保護者向け詳細レポート（週次・月次）', included: true },
        { name: '🎁 一度契約すれば永年¥14,500（値上げ対象外）', included: true, highlight: true, note: true },
        { name: '優先処理（AI応答の速度優先）', included: true },
      ],
    },
    standard: {
      id: 'standard',
      name: 'スタンダード',
      price: 24980,
      priceLabel: '¥24,980',
      tagline: 'AI学習を始めるなら',
      maxStudents: 1,
      aiModel: 'sonnet',
      color: '#3b82f6',
      // 月次クォータ (server/main.py のチェックロジックが参照)
      quotas: {
        problems: 50,    // 問題生成 月50回
        essays: 20,      // 英作文・記述添削 月20回
        textbooks: 5,    // 参考書生成 月5冊
      },
      features: [
        { name: '24時間AIチューター', included: true },
        { name: 'AI問題自動生成（月50回まで）', included: true },
        { name: '英作文・記述添削（月20回まで）', included: true },
        { name: '学習診断・カリキュラム生成', included: true },
        { name: 'オリジナル参考書生成（月5冊まで）', included: true },
        { name: '保護者向け学習レポート（週次）', included: true },
        { name: '問題生成・添削・参考書を無制限に使う', included: false },
        { name: '保護者向け詳細レポート', included: false },
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
      // 月次クォータ: null = 無制限
      quotas: { problems: null, essays: null, textbooks: null },
      features: [
        { name: '24時間AIチューター', included: true },
        { name: 'AI問題自動生成（無制限）', included: true, highlight: true },
        { name: '英作文・記述添削（無制限）', included: true, highlight: true },
        { name: '学習診断・カリキュラム生成', included: true },
        { name: 'オリジナル参考書生成（無制限）', included: true, highlight: true },
        { name: '優先処理（AI応答の速度優先）', included: true },
        { name: '保護者向け詳細レポート（週次・月次）', included: true },
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
      // 月次クォータ: null = 無制限
      quotas: { problems: null, essays: null, textbooks: null },
      features: [
        { name: 'プレミアムプランの全機能', included: true },
        { name: '🆕 生徒アカウント最大3名まで', included: true, highlight: true },
        { name: '🆕 家族ダッシュボード（全員の進捗一覧）', included: true, highlight: true },
        { name: '🆕 兄弟姉妹のカリキュラム相互参照', included: true, highlight: true },
        { name: '🆕 保護者向け家族レポート', included: true, highlight: true },
        { name: '生徒1人あたり実質¥19,933/月', included: true, note: true },
        { name: '優先サポート', included: true },
        { name: '問題生成・添削・参考書すべて無制限', included: true },
      ],
    },
  },

  // 完全無料 7日間体験 (GW長期休みに集中体験 → 休み明け本契約戦略)
  trial: {
    price: 0,
    priceLabel: '完全無料',
    duration: '7日間',
    description: 'クレジットカード登録不要・自動課金なし・解約手続き不要',
  },

  enrollment: {
    price: 10000,
    priceLabel: '¥10,000',
    description: '入塾金（初回のみ・システム登録費・トライアル後の初回請求に追加）',
  },

  // 入塾金免除キャンペーン (先着100名)
  enrollmentWaiverCampaign: {
    enabled: true,
    limit: 100,
    label: '🎉 先着100名 入塾金¥10,000 免除キャンペーン',
    shortLabel: '入塾金¥10,000 OFF',
    description: '初回請求から入塾金¥10,000が0円に。月額のみで開始可能。',
    apiPath: '/api/campaigns/enrollment-waiver/status',
  },

  // 既存塾生向けアドオン
  studentAddon: {
    price: 15000,
    priceLabel: '¥15,000',
    description: '塾生限定アドオン（月謝に追加）',
    features: [
      '全AI機能無制限',
      '問題生成・添削・教材作成すべて無制限',
      '講師によるAI学習履歴の週次レビュー',
      '塾の宿題とAI自動連携',
      '保護者向け統合レポート',
      '塾内対面指導との完全併用',
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
