/**
 * 紹介プログラム (Referral Program)
 *
 * 機能:
 *  - 自分の紹介コード生成・表示
 *  - 紹介コード利用 (新規入会時)
 *  - 紹介履歴・特典トラッキング
 *  - シェア用URL/SNS文面生成
 *
 * 特典ロジック:
 *  - 紹介者: 1名成立で 1ヶ月無料 (累積)
 *  - 被紹介者: 初月50%OFF (¥12,490)
 */
(function () {
  'use strict';
  const LS_MY_CODE = 'ai_juku_referral__my_code';
  const LS_USED_CODE = 'ai_juku_referral__used_code';
  const LS_HISTORY = 'ai_juku_referral__history';

  function _read(key, fallback) {
    try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; }
    catch { return fallback; }
  }
  function _write(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); }
    catch (e) { console.warn('Referral storage write failed:', e); }
  }

  function _generateCode(seed) {
    // 例: "AIJ-XXXX-YYYY" (英数大文字)
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    const seedStr = (seed || '').toString();
    let h = 0;
    for (let i = 0; i < seedStr.length; i++) h = (h * 31 + seedStr.charCodeAt(i)) >>> 0;
    h = h ^ Date.now();
    let code = 'AIJ-';
    for (let i = 0; i < 4; i++) { code += chars[(h >>> (i * 5)) & 31]; }
    code += '-';
    for (let i = 0; i < 4; i++) { code += chars[(h >>> (i * 7 + 3)) % chars.length]; }
    return code;
  }

  function getMyCode(student) {
    let code = _read(LS_MY_CODE, null);
    if (!code) {
      code = _generateCode(student?.id || student?.email || 'guest');
      _write(LS_MY_CODE, code);
    }
    return code;
  }

  function regenerateMyCode(student) {
    const code = _generateCode((student?.id || 'x') + '_' + Date.now());
    _write(LS_MY_CODE, code);
    return code;
  }

  function getUsedCode() {
    return _read(LS_USED_CODE, null);
  }

  function applyReferralCode(code) {
    if (!code || typeof code !== 'string') return { ok: false, error: 'コードを入力してください' };
    const normalized = code.trim().toUpperCase();
    if (!/^AIJ-[A-Z0-9]{4}-[A-Z0-9]{4}$/.test(normalized)) {
      return { ok: false, error: '紹介コードの形式が正しくありません (例: AIJ-XXXX-YYYY)' };
    }
    const myCode = _read(LS_MY_CODE, null);
    if (myCode === normalized) {
      return { ok: false, error: '自分の紹介コードは使用できません' };
    }
    const existing = _read(LS_USED_CODE, null);
    if (existing) {
      return { ok: false, error: '既に紹介コードを利用済みです: ' + existing };
    }
    _write(LS_USED_CODE, normalized);
    return { ok: true, code: normalized, discount: 12490, message: '✅ 紹介コードを適用。スタンダード初月50%OFF (¥24,980 → ¥12,490) になります。' };
  }

  function getHistory() {
    return _read(LS_HISTORY, []);
  }

  function recordReferralSuccess(refereeIdentifier) {
    // 通常はサーバー側で確定するが、デモ表示用にlocalStorageへ反映
    const hist = _read(LS_HISTORY, []);
    hist.push({
      id: 'r_' + Date.now(),
      referee: refereeIdentifier,
      date: new Date().toISOString().slice(0, 10),
      reward: '1ヶ月無料',
      status: 'confirmed',
    });
    _write(LS_HISTORY, hist);
    return hist;
  }

  function getRewardsSummary() {
    const hist = _read(LS_HISTORY, []);
    return {
      totalReferrals: hist.length,
      monthsFree: hist.length,  // 1名 = 1ヶ月無料
      pending: hist.filter(h => h.status === 'pending').length,
      confirmed: hist.filter(h => h.status === 'confirmed').length,
    };
  }

  function buildShareUrl(code, baseUrl) {
    const url = baseUrl || window.location.origin;
    return `${url}/lp.html?ref=${encodeURIComponent(code)}`;
  }

  function buildShareText(code) {
    const url = buildShareUrl(code);
    return `🎓 AI学習コーチ塾を使ってる！毎日のAI個別指導で偏差値が伸びるよ。
紹介コード ${code} で初月50%OFF (¥12,490) になります。
${url}
#AI塾 #個別指導 #受験`;
  }

  function renderReferralWidget(containerId, student) {
    const el = document.getElementById(containerId);
    if (!el) return;
    const code = getMyCode(student);
    const summary = getRewardsSummary();
    const used = getUsedCode();
    const shareUrl = buildShareUrl(code);
    el.innerHTML = `
      <div style="background:linear-gradient(135deg,rgba(99,102,241,0.12),rgba(236,72,153,0.08));border:1px solid rgba(167,139,250,0.3);border-radius:14px;padding:1.2rem;">
        <div style="font-weight:800;font-size:1.05rem;color:#e4e4e7;margin-bottom:0.3rem;">🎁 紹介プログラム</div>
        <p style="font-size:0.85rem;color:#cbd5e1;margin:0 0 0.8rem 0;">友達を紹介すると <strong style="color:#fbbf24;">あなたは1ヶ月無料</strong>、<strong style="color:#34d399;">友達は初月50%OFF (¥12,490)</strong>。</p>

        <div style="background:rgba(0,0,0,0.4);border-radius:10px;padding:0.8rem;margin-bottom:0.7rem;">
          <div style="font-size:0.78rem;color:#94a3b8;margin-bottom:0.3rem;">あなたの紹介コード</div>
          <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;">
            <code id="rpCode" style="font-size:1.2rem;font-weight:800;color:#fbbf24;letter-spacing:0.05em;">${code}</code>
            <button onclick="navigator.clipboard.writeText('${code}').then(()=>this.textContent='✓ コピー済')" style="background:rgba(99,102,241,0.3);color:#c7d2fe;border:1px solid rgba(99,102,241,0.5);padding:0.3rem 0.7rem;border-radius:6px;font-size:0.78rem;cursor:pointer;">📋 コピー</button>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:0.5rem;margin-bottom:0.7rem;">
          <div style="background:rgba(255,255,255,0.05);padding:0.6rem;border-radius:8px;text-align:center;">
            <div style="font-size:0.72rem;color:#94a3b8;">紹介成立</div>
            <div style="font-size:1.4rem;font-weight:800;color:#a78bfa;">${summary.totalReferrals}名</div>
          </div>
          <div style="background:rgba(16,185,129,0.1);padding:0.6rem;border-radius:8px;text-align:center;">
            <div style="font-size:0.72rem;color:#94a3b8;">無料月数</div>
            <div style="font-size:1.4rem;font-weight:800;color:#34d399;">${summary.monthsFree}ヶ月</div>
          </div>
        </div>

        <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">
          <button onclick="ReferralProgram._shareLine('${code}')" style="background:#06c755;color:white;border:none;padding:0.5rem 0.9rem;border-radius:6px;font-size:0.82rem;cursor:pointer;font-weight:700;">📱 LINEで送る</button>
          <button onclick="ReferralProgram._shareTwitter('${code}')" style="background:#000;color:white;border:none;padding:0.5rem 0.9rem;border-radius:6px;font-size:0.82rem;cursor:pointer;font-weight:700;">𝕏 で投稿</button>
          <button onclick="navigator.clipboard.writeText('${shareUrl}').then(()=>alert('✅ URL をコピーしました'))" style="background:rgba(255,255,255,0.08);color:#cbd5e1;border:1px solid rgba(255,255,255,0.15);padding:0.5rem 0.9rem;border-radius:6px;font-size:0.82rem;cursor:pointer;">🔗 URLをコピー</button>
        </div>

        ${used ? `<div style="margin-top:0.8rem;font-size:0.78rem;color:#94a3b8;">✓ あなたが利用した紹介コード: <code style="color:#fbbf24;">${used}</code></div>` : ''}
      </div>`;
  }

  function _shareLine(code) {
    const text = buildShareText(code);
    const url = `https://line.me/R/msg/text/?${encodeURIComponent(text)}`;
    window.open(url, '_blank');
  }
  function _shareTwitter(code) {
    const text = buildShareText(code);
    const url = `https://x.com/intent/post?text=${encodeURIComponent(text)}`;
    window.open(url, '_blank');
  }

  // URL から ref パラメータを自動適用 (招待リンクからの遷移)
  function autoApplyFromUrl() {
    try {
      const params = new URLSearchParams(window.location.search);
      const ref = params.get('ref');
      if (ref && !getUsedCode()) {
        const r = applyReferralCode(ref);
        if (r.ok) console.info('[Referral] Auto-applied:', ref);
        return r;
      }
    } catch {}
    return null;
  }

  window.ReferralProgram = {
    getMyCode, regenerateMyCode, getUsedCode, applyReferralCode,
    getHistory, recordReferralSuccess, getRewardsSummary,
    buildShareUrl, buildShareText, renderReferralWidget, autoApplyFromUrl,
    _shareLine, _shareTwitter,
  };
})();
