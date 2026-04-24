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
    const token = getSessionToken();
    if (!token || isLocalExpired()) {
      redirectToLogin('no_session');
      return;
    }
    try {
      const res = await fetch(getBackendUrl() + '/api/auth/me', {
        headers: { 'Authorization': 'Bearer ' + token }
      });
      if (!res.ok) {
        clearSession();
        redirectToLogin('invalid_session');
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
