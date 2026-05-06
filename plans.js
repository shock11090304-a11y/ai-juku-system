// ==========================================================================
// プラン設定（一元管理）2026-05-06 新体系
// 旧 standard (¥24,980) は廃止 (新規募集停止) → 既存契約者は plan='standard' のまま据置
// 旧プレミアム ¥39,800 → ¥19,800 に値下げ + 学習管理機能を解放
// 旧通塾生 ¥9,800 → ¥5,000 に値下げ + AI 機能のみに絞る
// 旧家族プラン ¥59,800 → ¥39,800 に値下げ
// 創設メンバー ¥14,500 永年は据置 (募集停止・既契約者のみ)
// ==========================================================================

const PLAN_CONFIG = {
  plans: {
    // 🎁 創設メンバー 50名限定 永年¥14,500 (募集停止・既契約者据置)
    founder_special: {
      id: 'founder_special',
      name: '創設メンバー (永年特典)',
      price: 14500,
      priceLabel: '¥14,500',
      tagline: '50名限定・募集終了・既契約者は永年この価格',
      maxStudents: 1,
      aiModel: 'opus',
      color: '#fbbf24',
      recommended: false,
      badge: '🎁 募集終了',
      quotas: { problems: null, essays: null, textbooks: null },
      legacy: true,  // 新規申込不可 (UI では既契約者のみ表示)
      features: [
        { name: '24時間AIチューター（無制限）', included: true, highlight: true },
        { name: 'AI問題自動生成（無制限）', included: true, highlight: true },
        { name: '英作文・記述添削（無制限）', included: true, highlight: true },
        { name: '学習診断・カリキュラム生成', included: true },
        { name: 'オリジナル参考書生成（無制限）', included: true, highlight: true },
        { name: '5試験対応 (TOEFL/TOEIC/IELTS/英検/大学入試)', included: true, highlight: true },
        { name: '英字ニュース読解 (CNN/Japan Times/BBC ほか)', included: true, highlight: true },
        { name: '学習記録・合格カリキュラム自動生成・模試 AI 分析', included: true, highlight: true },
        { name: '保護者向け詳細レポート（週次・月次)', included: true },
        { name: '🎁 一度契約すれば永年¥14,500（値上げ対象外）', included: true, highlight: true, note: true },
      ],
    },
    // ⭐ プレミアム ¥39,800 (主力プラン・学習管理機能フル解放)
    premium: {
      id: 'premium',
      name: 'プレミアム',
      price: 39800,
      priceLabel: '¥39,800',
      tagline: 'AI 全機能無制限 + 学習管理 + 合格カリキュラム自動生成 + ZOOM 授業参加可',
      maxStudents: 1,
      aiModel: 'opus',
      color: '#8b5cf6',
      recommended: true,
      badge: '⭐ 推奨',
      quotas: { problems: null, essays: null, textbooks: null },
      features: [
        { name: '24時間AIチューター（無制限）', included: true, highlight: true },
        { name: 'AI問題自動生成（無制限）', included: true, highlight: true },
        { name: '英作文・記述添削（無制限）', included: true, highlight: true },
        { name: 'オリジナル参考書生成（無制限）', included: true, highlight: true },
        { name: '5試験対応 (TOEFL/TOEIC/IELTS/英検/大学入試)', included: true },
        { name: '英字ニュース読解 (CNN/Japan Times/BBC ほか)', included: true },
        { name: '🆕 学習記録 + ヒートマップ', included: true, highlight: true },
        { name: '🆕 学習計画 + ガントチャート', included: true, highlight: true },
        { name: '🆕 合格カリキュラム自動生成 (4-6 フェーズ)', included: true, highlight: true },
        { name: '🆕 模試 → AI ギャップ分析', included: true, highlight: true },
        { name: '🆕 AI 弱点プリント生成', included: true, highlight: true },
        { name: '🆕 模試 写真/PDF AI スキャン', included: true, highlight: true },
        { name: '保護者向け詳細レポート（週次・月次）', included: true },
        { name: '優先処理（AI応答の速度優先）', included: true },
        { name: '塾長との双方向メッセージ・授業ファイル受信', included: false, note: true },
      ],
    },
    // 👨‍👩‍👧‍👦 家族プラン ¥59,800 (プレミアム × 3 名)
    family: {
      id: 'family',
      name: '家族プラン',
      price: 59800,
      priceLabel: '¥59,800',
      tagline: '兄弟姉妹3名まで使える',
      maxStudents: 3,
      aiModel: 'opus',
      color: '#ec4899',
      quotas: { problems: null, essays: null, textbooks: null },
      features: [
        { name: 'プレミアムプランの全機能', included: true, highlight: true },
        { name: '🆕 生徒アカウント最大3名まで', included: true, highlight: true },
        { name: '🆕 家族ダッシュボード（全員の進捗一覧）', included: true, highlight: true },
        { name: '🆕 兄弟姉妹のカリキュラム相互参照', included: true, highlight: true },
        { name: '🆕 保護者向け家族レポート', included: true, highlight: true },
        { name: '生徒1人あたり実質¥19,933/月', included: true, note: true },
        { name: '優先サポート', included: true },
      ],
    },
    // [LEGACY] スタンダード ¥24,980 (新規募集停止・既存契約者のみ据置)
    standard: {
      id: 'standard',
      name: 'スタンダード (旧)',
      price: 24980,
      priceLabel: '¥24,980',
      tagline: '【旧プラン・新規募集停止】既存契約者のみ据置',
      maxStudents: 1,
      aiModel: 'sonnet',
      color: '#3b82f6',
      legacy: true,  // 新規申込不可
      quotas: {
        problems: 50,
        essays: 20,
        textbooks: 5,
      },
      features: [
        { name: '24時間AIチューター', included: true },
        { name: 'AI問題自動生成（月50回まで）', included: true },
        { name: '英作文・記述添削（月20回まで）', included: true },
        { name: 'オリジナル参考書生成（月5冊まで）', included: true },
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

  // 既存塾生向けアドオン (2026-05-06 値下げ ¥9,800 → 永年¥5,000・通塾生優遇で学習管理機能含む)
  // 招待リンク方式で塾長発行のみアクセス可 (一般人は申込不可)
  studentAddon: {
    price: 5000,
    priceLabel: '¥5,000',
    description: '通塾生限定プラン（月謝に追加・永年この価格・塾長招待制）',
    features: [
      '24時間AIチューター（無制限）',
      'AI問題自動生成（無制限）',
      '英作文・記述添削（無制限）',
      'AI 単語帳 + Leitner SRS',
      '大学過去問 (東大・京大・医学部等)',
      'オリジナル参考書 自動生成（無制限）',
      '5試験対応 (TOEFL/TOEIC/IELTS/英検/大学入試)',
      '🎯 学習記録 + ヒートマップ',
      '🎯 学習計画 + ガントチャート',
      '🎯 合格カリキュラム自動生成',
      '🎯 模試 → AI ギャップ分析',
      '🎯 AI 弱点プリント生成',
      '🎯 模試 写真/PDF AI スキャン',
      '🎥 ZOOM 英語授業 参加可 (塾長定例)',
      '塾内対面指導との完全併用',
      '※ 通塾生限定 (塾長から招待リンク発行・一般申込不可)',
    ],
  },

  // 🎓 国公立難関大学コース 本クラス (システム利用料 ¥0・塾代別途)
  // 塾長承認制・Stripe ¥0 sub で「契約中」状態を表現
  // course='kokuritsu_nankan' を付与 → 全機能 + 塾長双方向メッセージ + 授業ファイル送信 解放
  kokuritsuNankanClass: {
    id: 'kokuritsu_nankan_class',
    name: '国公立難関大学コース 本クラス',
    price: 0,
    priceLabel: '¥0',
    tagline: 'システム利用料 ¥0 (月謝は塾代に含む・塾長承認制)',
    description: '塾長 DM/メールで個別 LP 配布 → 申込フォーム → CEO 承認 → magic link 自動ログイン',
    features: [
      'プレミアムプランの全機能',
      '🎓 学習記録・合格カリキュラム・模試分析・弱点プリント',
      '📩 塾長との双方向メッセージ',
      '📎 授業ファイル送受信 (PDF/画像/Word/Excel/PPT・10MB)',
      '👨‍🏫 塾長による進捗フィードバック (いいね/コメント・週次励まし)',
      '🛡️ クレカ縛りなし (塾長判断で個別承認・完全クローズド運用)',
    ],
  },

  // 年間先払い割引
  annualDiscount: {
    premiumAnnual: { monthly: 39800, annual: 398000, saved: 79600, label: '年間¥398,000（2ヶ月分お得）' },
    familyAnnual: { monthly: 59800, annual: 598000, saved: 119600, label: '年間¥598,000（2ヶ月分お得）' },
  },
};

// グローバル公開
if (typeof window !== 'undefined') window.PLAN_CONFIG = PLAN_CONFIG;
if (typeof module !== 'undefined' && module.exports) module.exports = PLAN_CONFIG;
