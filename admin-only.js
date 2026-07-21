/**
 * 管理者専用ページ ガード
 *
 * <head> の先頭で読み込むと、未認証時に:
 *   1. document.documentElement.innerHTML を即座に消去 (HTML が一瞬も見えない)
 *   2. window.location.replace('ceo.html') で強制リダイレクト
 *   3. throw で以降のスクリプト実行を停止
 *
 * 【重要】これはあくまで第一層の防御 (DevTools で無効化可能)。
 * 真のガードは:
 *   - 各 admin endpoint (/api/admin/*) が Bearer token 必須
 *   - personalized-outreach 等は backend API 経由でしかデータ取得できない
 *   - 個人情報を含む静的ファイル (juku-manager-data.json 等) は public 配信禁止
 *
 * 使い方 (管理者専用 HTML の <head> 先頭):
 *   <script src="admin-only.js"></script>
 */
(function () {
  'use strict';
  var tok = null;
  try {
    tok = localStorage.getItem('ai_juku_admin_token');
    // 🛡️ 2026-07-21 [admin-token-hygiene] 期限切れ token は「無い」扱いにして掃除する
    //   (server は期限を強制するが、client が presence だけ見ると期限切れ端末で admin UI の
    //   殻が開いて API 401 の壊れ画面になる)。expires は epoch 秒 (ceo.html saveSession と同じ)
    var exp = parseInt(localStorage.getItem('ai_juku_admin_expires') || '0', 10);
    if (tok && exp && Math.floor(Date.now() / 1000) >= exp) {
      localStorage.removeItem('ai_juku_admin_token');
      localStorage.removeItem('ai_juku_admin_expires');
      tok = null;
    }
  } catch (e) {
    tok = null;
  }
  if (tok) return;  // 認証済みなら何もしない

  // 未認証: 即座にページ全体を消す → リダイレクト
  try {
    document.title = '';
    if (document.documentElement) {
      document.documentElement.innerHTML = '';
    }
  } catch (e) { /* noop */ }

  try {
    var here = location.pathname + location.search;
    var url = 'ceo.html?reason=admin_required&from=' + encodeURIComponent(here);
    window.location.replace(url);
  } catch (e) {
    try { window.location.href = 'ceo.html'; } catch (e2) {}
  }

  // 以降のスクリプト・DOM処理を全て停止
  throw new Error('[admin-only] unauthorized — redirecting to ceo.html');
})();
