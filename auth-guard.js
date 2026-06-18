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

  // 表示用ポインタのキー (氏名/学習データの「現在の生徒」を指す別系統)
  const CURRENT_STUDENT_KEY = 'ai_juku_current_student';
  const STUDENTS_LIST_KEY = 'ai_juku_students';
  const ALT_CURRENT_KEY = 'aj_current_student_id'; // vocab/mock-exam が読む別キー

  function clearSession() {
    localStorage.removeItem(SESSION_TOKEN_KEY);
    localStorage.removeItem(SESSION_EXPIRES_KEY);
    localStorage.removeItem(SESSION_STUDENT_KEY);
    // 🔑 2026-06-14 [trust-identity] 表示ポインタも必ず消す。残すと、ログアウト後や
    //   別生徒が同端末でログインする前の一瞬に、古いポインタで別生徒の氏名/学習データを
    //   表示してしまう (室坂海來さんの別生徒名表示事故の構造的原因)。再ログイン時は各経路が
    //   session_student から再構築するため削除して実害なし。
    localStorage.removeItem(CURRENT_STUDENT_KEY);
    localStorage.removeItem(STUDENTS_LIST_KEY);
    localStorage.removeItem(ALT_CURRENT_KEY);
    // 🛡️ 2026-06-18 [cross-student-cache-guard] per-student のローカル学習キャッシュも消す。
    //   残すとログアウト→別生徒ログイン時に前生徒のチャット/統計/問題履歴/活動/カリキュラムが
    //   漏れる (app.js の guardPerStudentCaches と対。こちらは logout/無効セッション経路を担保)。
    ['ai_juku_chat_history', 'ai_juku_stats', 'ai_juku_problem_history', 'ai_juku_activity', 'ai_juku_last_curriculum', 'ai_juku_cache_owner_sid'].forEach(function (k) {
      try { localStorage.removeItem(k); } catch (_) {}
    });
  }

  // 🔑 2026-06-14 [trust-identity] サーバ検証済みの本人を全表示ポインタに固定する。
  //   auth-guard.js を読む全ページで「画面に出る生徒 = ログイン本人」を保証する中核処理。
  //   /api/auth/me (HMAC トークンの student_id をサーバが検証) の結果のみを権威ソースにする。
  function applyVerifiedStudent(student) {
    if (!student || student.id == null) return;
    try {
      localStorage.setItem(SESSION_STUDENT_KEY, JSON.stringify(student));
      localStorage.setItem(CURRENT_STUDENT_KEY, JSON.stringify(student.id));
      localStorage.setItem(ALT_CURRENT_KEY, String(student.id));
      let list = [];
      try { const raw = localStorage.getItem(STUDENTS_LIST_KEY); list = raw ? JSON.parse(raw) : []; } catch (e) { list = []; }
      if (!Array.isArray(list)) list = [];
      const i = list.findIndex(s => s && s.id === student.id);
      if (i >= 0) list[i] = Object.assign({}, list[i], student); // name まで本人で上書き
      else list.push(student);
      localStorage.setItem(STUDENTS_LIST_KEY, JSON.stringify(list));
    } catch (e) { /* localStorage 不可でも認証は継続 */ }
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
        // 🔑 サーバ検証済み本人を全表示ポインタに固定 (session_student だけでなく
        //   current_student / students / aj_current_student_id まで本人へ揃える)
        applyVerifiedStudent(data.student);
        // 🚪 2026-06-19 [login-allow-inactive] 方針A: 体験切れ/未契約 (entitled===false) は
        //   ログインへ飛ばさず「継続登録(再開)」画面へ誘導する。upgrade.html / checkout 系は
        //   auth-guard を読まないのでループしない。entitled が未定義(旧backend等)なら従来通り通す
        //   (active を誤って締め出さない安全側)。有料機能のアクセスは各APIの厳格ゲートが担保。
        if (data.student.entitled === false) {
          var _path = (window.location.pathname || '');
          if (!/\/(upgrade|checkout|checkout-success|checkout-cancel|login)\.html$/.test(_path)) {
            window.location.replace('upgrade.html?reason=resubscribe');
          }
          return;
        }
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
