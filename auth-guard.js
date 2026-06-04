/**
 * 認証ガード - index.html / mypage.html / textbook-generator.html など
 * ログイン必須ページの <head> で読み込むと、未ログイン時に login.html へ
 * 自動リダイレクトする。
 *
 * 【設計】
 *  - セッションはマジックリンクで発行された HMAC-SHA256 署名トークン
 *  - localStorage.ai_juku_session_token に保存
 *  - 検証: localStorage の expires_at を先にチェック（通信不要の高速パス）
 *  - 本物の検証は /api/auth/me で backend が署名を確認。ここでの expires_at は
 *    UI 用のヒントにすぎず、サーバー側で常に再検証されるため改ざん耐性あり。
 *  - 各 fetch で Authorization: Bearer <token> を自動付与するヘルパも公開
 */
(function () {
  const SESSION_TOKEN_KEY = 'ai_juku_session_token';
  const SESSION_EXPIRES_KEY = 'ai_juku_session_expires';
  const SESSION_STUDENT_KEY = 'ai_juku_session_student';

  function getBackendUrl() {
    return (window.location.origin.includes(':8090')) ? 'http://localhost:8000' : window.location.origin;
  }

  function clearSession() {
    localStorage.removeItem(SESSION_TOKEN_KEY);
    localStorage.removeItem(SESSION_EXPIRES_KEY);
    localStorage.removeItem(SESSION_STUDENT_KEY);
  }

  function redirectToLogin(reason) {
    const here = window.location.pathname + window.location.search;
    const params = new URLSearchParams();
    if (here && here !== '/login.html') params.set('redirect', here);
    if (reason) params.set('reason', reason);
    window.location.replace('login.html' + (params.toString() ? '?' + params.toString() : ''));
  }

  function getSessionToken() {
    return localStorage.getItem(SESSION_TOKEN_KEY);
  }

  function isLocalExpired() {
    const exp = parseInt(localStorage.getItem(SESSION_EXPIRES_KEY) || '0', 10);
    if (!exp) return true;
    return Math.floor(Date.now() / 1000) >= exp;
  }

  /**
   * 認証済み fetch。通常の fetch と同じシグネチャだが、自動で
   * Authorization ヘッダを付与し、401 応答時に login.html へリダイレクトする。
   */
  async function authFetch(input, init = {}) {
    const token = getSessionToken();
    const headers = new Headers(init.headers || {});
    if (token) headers.set('Authorization', 'Bearer ' + token);
    const res = await fetch(input, { ...init, headers });
    if (res.status === 401) {
      clearSession();
      redirectToLogin('session_expired');
      throw new Error('Session expired');
    }
    return res;
  }

  /**
   * ページロード時の認証ガード。ローカルの token/expires を先に確認し、
   * 有効そうなら非同期で /api/auth/me に裏取りに行く。裏取り失敗時のみ
   * セッションを破棄してログインへ誘導する。
   */
  async function enforceAuth() {
    // 🧒 塾長プレビュー (2026-06-04): ?preview_mode=chugaku|shougaku|kosei が付いていれば認証を要求せず
    //   器のみ描画する (実データは backend が token 無しリクエストを全て 401 で弾くため漏洩ゼロ)。
    //   ※ student-mode.js は未読込の可能性があるため、ここで自前ホワイトリスト判定する。
    try {
      const _pm = new URLSearchParams(window.location.search).get('preview_mode');
      if (_pm === 'chugaku' || _pm === 'shougaku' || _pm === 'kosei') return;
    } catch (_e) { /* URL 解析失敗時は通常の認証フローへ */ }
    const token = getSessionToken();
    if (!token || isLocalExpired()) {
      redirectToLogin('no_session');
      return;
    }
    try {
      const res = await fetch(getBackendUrl() + '/api/auth/me', {
        headers: { 'Authorization': 'Bearer ' + token }
      });
      // 🚨 2026-05-13 塾長指示「学習管理が絶対に消えない」: 401/403 (= 認証失敗) のみ login redirect
      // 5xx (= サーバ一時障害) や 429 (= rate limit) はローカル session で継続表示 (画面消失防止)
      if (res.status === 401 || res.status === 403) {
        clearSession();
        redirectToLogin('invalid_session');
        return;
      }
      if (!res.ok) {
        // 5xx / 429 / その他: 一時的エラーとしてローカル session で継続 (画面ごと消えない)
        console.warn('auth-guard: /api/auth/me status=' + res.status + ' (transient) - keeping local session');
        return;
      }
      const data = await res.json();
      if (data && data.student) {
        localStorage.setItem(SESSION_STUDENT_KEY, JSON.stringify(data.student));
      }
    } catch (e) {
      // ネットワークエラー時はローカル値を信用して続行（オフライン耐性）。
      // サーバ到達可能になり次第、次の authFetch で再検証される。
      console.warn('auth-guard: /api/auth/me failed, continuing with local session:', e);
    }
  }

  function logout() {
    clearSession();
    window.location.href = 'login.html';
  }

  // グローバル公開（他スクリプトから使えるように）
  window.AuthGuard = {
    getToken: getSessionToken,
    getStudent: () => {
      const raw = localStorage.getItem(SESSION_STUDENT_KEY);
      try { return raw ? JSON.parse(raw) : null; } catch { return null; }
    },
    authFetch,
    logout,
    clearSession,
  };

  // ページロード時に即時実行（DOMContentLoaded を待たない: 未認証ページをフラッシュ表示しない）
  enforceAuth();
})();
