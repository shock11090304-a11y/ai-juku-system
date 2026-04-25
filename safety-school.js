/**
 * 滑り止め校提案 (Safety School Recommender)
 *
 * 機能:
 *  - 第一志望校 + 現在の偏差値 → 同系統で「実力相応」「滑り止め」候補を提示
 *  - past-exams-db.js のカテゴリと難易度ランクを活用
 *  - 出願戦略 (チャレンジ/実力相応/滑り止め) を自動構成
 */
(function () {
  'use strict';
  const LS_PREFS = 'ai_juku_safety_school__prefs';

  // 大学難易度ランク (おおよその目安、私立3教科)
  const UNIV_RANK = {
    // 最難関国立 (S+)
    "東京大学":      { tier: 'SS', deviation: 75, type: '国立', region: '関東' },
    "京都大学":      { tier: 'SS', deviation: 73, type: '国立', region: '関西' },
    // 最難関国立 (S)
    "一橋大学":      { tier: 'S',  deviation: 70, type: '国立', region: '関東', specialty: '文系' },
    "東京工業大学":  { tier: 'S',  deviation: 70, type: '国立', region: '関東', specialty: '理系' },
    "大阪大学":      { tier: 'S',  deviation: 68, type: '国立', region: '関西' },
    "名古屋大学":    { tier: 'S',  deviation: 66, type: '国立', region: '中部' },
    "東北大学":      { tier: 'S',  deviation: 66, type: '国立', region: '東北' },
    "北海道大学":    { tier: 'S',  deviation: 64, type: '国立', region: '北海道' },
    "九州大学":      { tier: 'S',  deviation: 65, type: '国立', region: '九州' },
    // 難関国立 (A)
    "神戸大学":      { tier: 'A',  deviation: 63, type: '国立', region: '関西' },
    "筑波大学":      { tier: 'A',  deviation: 62, type: '国立', region: '関東' },
    // 最難関私立 (S)
    "早稲田大学":    { tier: 'S',  deviation: 68, type: '私立', region: '関東' },
    "慶應義塾大学":  { tier: 'S',  deviation: 69, type: '私立', region: '関東' },
    // 難関私立 (A)
    "上智大学":      { tier: 'A',  deviation: 65, type: '私立', region: '関東' },
    "国際基督教大学":{ tier: 'A',  deviation: 65, type: '私立', region: '関東' },
    "同志社大学":    { tier: 'A',  deviation: 62, type: '私立', region: '関西' },
    // MARCH (B)
    "明治大学":      { tier: 'B',  deviation: 60, type: '私立', region: '関東' },
    "青山学院大学":  { tier: 'B',  deviation: 60, type: '私立', region: '関東' },
    "立教大学":      { tier: 'B',  deviation: 60, type: '私立', region: '関東' },
    "中央大学":      { tier: 'B',  deviation: 59, type: '私立', region: '関東' },
    "法政大学":      { tier: 'B',  deviation: 58, type: '私立', region: '関東' },
    // 関関同立 (B)
    "立命館大学":    { tier: 'B',  deviation: 60, type: '私立', region: '関西' },
    "関西学院大学":  { tier: 'B',  deviation: 60, type: '私立', region: '関西' },
    "関西大学":      { tier: 'B',  deviation: 58, type: '私立', region: '関西' },
    // 中堅私立 (C) — DB外だが候補として
    "成蹊大学":      { tier: 'C',  deviation: 55, type: '私立', region: '関東' },
    "明治学院大学":  { tier: 'C',  deviation: 56, type: '私立', region: '関東' },
    "成城大学":      { tier: 'C',  deviation: 55, type: '私立', region: '関東' },
    "獨協大学":      { tier: 'C',  deviation: 53, type: '私立', region: '関東' },
    "國學院大學":    { tier: 'C',  deviation: 54, type: '私立', region: '関東' },
    "武蔵大学":      { tier: 'C',  deviation: 54, type: '私立', region: '関東' },
    "南山大学":      { tier: 'C',  deviation: 56, type: '私立', region: '中部' },
    "西南学院大学":  { tier: 'C',  deviation: 55, type: '私立', region: '九州' },
    "京都産業大学":  { tier: 'C',  deviation: 52, type: '私立', region: '関西' },
    "近畿大学":      { tier: 'C',  deviation: 54, type: '私立', region: '関西' },
    "甲南大学":      { tier: 'C',  deviation: 52, type: '私立', region: '関西' },
    "龍谷大学":      { tier: 'C',  deviation: 52, type: '私立', region: '関西' },
    "日本大学":      { tier: 'C',  deviation: 53, type: '私立', region: '関東' },
    "東洋大学":      { tier: 'C',  deviation: 52, type: '私立', region: '関東' },
    "駒澤大学":      { tier: 'C',  deviation: 53, type: '私立', region: '関東' },
    "専修大学":      { tier: 'C',  deviation: 52, type: '私立', region: '関東' },
  };

  function _read() {
    try { return JSON.parse(localStorage.getItem(LS_PREFS) || '{}'); }
    catch { return {}; }
  }
  function _write(v) {
    try { localStorage.setItem(LS_PREFS, JSON.stringify(v)); }
    catch (e) { console.warn('SafetySchool storage write failed:', e); }
  }

  function savePrefs(prefs) { _write(prefs); }
  function getPrefs() { return _read(); }

  function listUniversities() {
    return Object.entries(UNIV_RANK).map(([name, info]) => ({ name, ...info }));
  }

  /**
   * @param {object} opts - { target: string (大学名), currentDeviation: number, region?: string, type?: '国立'|'私立'|'all' }
   * @returns {object} - { challenge: [], match: [], safety: [], analysis: string }
   */
  function recommend(opts) {
    const { target, currentDeviation, region, type } = opts;
    if (!target || !UNIV_RANK[target]) {
      return { error: `「${target}」のデータがありません。データベースから選択してください。`, options: Object.keys(UNIV_RANK) };
    }
    const targetInfo = UNIV_RANK[target];
    const dev = currentDeviation || targetInfo.deviation - 5;  // 不明時は目標-5想定
    const gap = dev - targetInfo.deviation;  // +なら余裕あり、-なら不足

    const all = Object.entries(UNIV_RANK).filter(([name, info]) => {
      if (name === target) return false;
      if (region && region !== 'all' && info.region !== region) return false;
      if (type && type !== 'all' && info.type !== type) return false;
      return true;
    });

    // 帯ごとに分類
    // チャレンジ: 自分の偏差値より +3 以上 (合格率20-40%)
    // 実力相応: -2 〜 +2 (合格率40-60%)
    // 滑り止め: -3 以下 (合格率70%以上想定)
    const challenge = [];
    const match = [];
    const safety = [];
    all.forEach(([name, info]) => {
      const diff = info.deviation - dev;
      const item = { name, ...info, diff, estimatedRate: _estimateRate(diff) };
      if (diff >= 3) challenge.push(item);
      else if (diff >= -2 && diff <= 2) match.push(item);
      else safety.push(item);
    });

    // ソート: チャレンジは難易度低い順、実力相応は同系統優先、滑り止めは安全度高い順
    challenge.sort((a, b) => a.deviation - b.deviation);
    match.sort((a, b) => Math.abs(a.diff) - Math.abs(b.diff));
    safety.sort((a, b) => b.deviation - a.deviation);  // 直下の少し下の方が後悔少ない

    const analysis = _buildAnalysis(target, targetInfo, dev, gap);
    return {
      ok: true,
      target: { name: target, ...targetInfo },
      currentDeviation: dev,
      gap,
      challenge: challenge.slice(0, 5),
      match: match.slice(0, 5),
      safety: safety.slice(0, 5),
      analysis,
    };
  }

  function _estimateRate(diff) {
    // diff = 大学偏差値 - 自分偏差値
    if (diff >= 5)  return '15-25%';
    if (diff >= 3)  return '25-40%';
    if (diff >= 1)  return '40-55%';
    if (diff >= -1) return '50-65%';
    if (diff >= -3) return '65-80%';
    return '80%+';
  }

  function _buildAnalysis(target, info, dev, gap) {
    const parts = [];
    if (gap >= 5) {
      parts.push(`現在の偏差値${dev}は${target}(${info.deviation})を ${gap} 上回っています。本命は十分射程内。`);
      parts.push('チャレンジ校で1〜2ランク上を目指す価値があります。');
    } else if (gap >= 0) {
      parts.push(`現在の偏差値${dev}は${target}(${info.deviation})と同水準。実力相応校で固めつつ、本命に集中。`);
      parts.push('滑り止めを必ず1〜2校確保しましょう。');
    } else if (gap >= -3) {
      parts.push(`現在の偏差値${dev}は${target}(${info.deviation})まで ${-gap} 不足。本命はチャレンジ枠です。`);
      parts.push('実力相応校2校 + 滑り止め2校以上の構成を強く推奨。');
    } else {
      parts.push(`現在の偏差値${dev}は${target}(${info.deviation})まで ${-gap} の差。本命は厳しい挑戦になります。`);
      parts.push('実力相応校で確実に押さえつつ、本命対策と並行して直近の偏差値アップに集中を。');
    }
    return parts.join(' ');
  }

  function renderRecommendation(containerId, result) {
    const el = document.getElementById(containerId);
    if (!el) return;
    if (result.error) {
      el.innerHTML = `<div style="color:#fca5a5;padding:1rem;background:rgba(239,68,68,0.1);border-radius:8px;">${result.error}</div>`;
      return;
    }
    const renderBand = (label, items, color, emoji) => {
      if (items.length === 0) return '';
      return `
        <div style="margin-top:1rem;">
          <div style="font-weight:800;color:${color};margin-bottom:0.5rem;">${emoji} ${label} <span style="font-size:0.78rem;color:#71717a;">(${items.length}校)</span></div>
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:0.5rem;">
            ${items.map(u => `
              <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-left:3px solid ${color};border-radius:8px;padding:0.7rem;">
                <div style="font-weight:700;color:#e4e4e7;font-size:0.95rem;">${u.name}</div>
                <div style="font-size:0.78rem;color:#a1a1aa;margin:0.25rem 0;">${u.type} · ${u.region} · 偏差値 ${u.deviation}</div>
                <div style="font-size:0.78rem;color:${color};">合格率目安 ${u.estimatedRate}</div>
              </div>`).join('')}
          </div>
        </div>`;
    };
    el.innerHTML = `
      <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:1rem;">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;margin-bottom:0.5rem;">
          <div>
            <div style="font-size:1.05rem;font-weight:800;color:#e4e4e7;">🎯 第一志望: ${result.target.name} <span style="font-size:0.78rem;color:#a78bfa;">偏差値${result.target.deviation}</span></div>
            <div style="font-size:0.85rem;color:#94a3b8;">現在のあなたの偏差値: ${result.currentDeviation} (差${result.gap >= 0 ? '+' : ''}${result.gap})</div>
          </div>
        </div>
        <div style="background:rgba(99,102,241,0.08);padding:0.7rem;border-radius:8px;font-size:0.88rem;color:#cbd5e1;border-left:3px solid #6366f1;">
          💡 ${result.analysis}
        </div>
        ${renderBand('チャレンジ校', result.challenge, '#f59e0b', '🔥')}
        ${renderBand('実力相応校', result.match, '#6366f1', '⚖️')}
        ${renderBand('滑り止め校', result.safety, '#10b981', '🛡️')}
      </div>`;
  }

  window.SafetySchool = {
    listUniversities, recommend, renderRecommendation, savePrefs, getPrefs,
    UNIV_RANK,
  };
})();
