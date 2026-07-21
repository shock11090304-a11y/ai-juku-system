/**
 * cache-purge.js — 古い Service Worker / Cache を全削除
 *
 * 背景: 過去に pwa.js が ENABLE_SW=true だった時期に、ユーザーの端末に
 * Service Worker が登録された。後で ENABLE_SW=false に変更したが、
 * pwa.js を読まないページ (mypage.html など) では unregister が動かず、
 * 古いSWが古い HTML/CSS/JS をキャッシュから返し続けていた。
 *
 * その結果「ボタンが押せない」「画面が古い」などの不具合が発生していた。
 *
 * このスクリプトは <head> の先頭で読み込み、レンダリング前に SW + Cache を
 * 完全に削除する。古いコードを表示していた疑いがある場合は、1回だけ自動リロード。
 *
 * すべてのページ (特に生徒向けページ) で読み込む想定。
 */
(function purgeStaleServiceWorker() {
  try {
    if (!('serviceWorker' in navigator)) return;
    navigator.serviceWorker.getRegistrations().then(function (regs) {
      if (regs.length > 0) {
        console.warn('[cache-purge] Unregistering', regs.length, 'stale service worker(s)');
        return Promise.all(regs.map(function (r) { return r.unregister(); }));
      }
    }).then(function () {
      if (typeof caches !== 'undefined') {
        return caches.keys().then(function (keys) {
          if (keys.length > 0) {
            console.warn('[cache-purge] Deleting', keys.length, 'stale cache(s)');
            return Promise.all(keys.map(function (k) { return caches.delete(k); }));
          }
        });
      }
    }).then(function () {
      // 🔒 リロードループ防止 (2026-04-28 強化):
      //  - sessionStorage は Safari private mode / タブ切替で消える → localStorage に変更
      //  - bfcache/prefetch でも transferSize=0 → 誤検知の主因。nav.type で除外
      //  - 一定期間 (10分) 内に 1 回までに制限
      try {
        var nav = performance.getEntriesByType('navigation')[0];
        if (!nav) return;
        // bfcache (back_forward) / prerender は transferSize=0 が正常 → スキップ
        if (nav.type === 'back_forward' || nav.type === 'prerender') return;
        if (nav.transferSize !== 0) return;
        // navigation が成功している (200 系応答) かを確認
        // duration が極端に短い (=0) の場合は計測未対応 → スキップ
        if (nav.duration === 0) return;

        var KEY = 'ai_juku_sw_purge_log_v2';
        var WINDOW_MS = 10 * 60 * 1000; // 10分
        var MAX_RELOADS = 1;
        var now = Date.now();
        var log = [];
        try { log = JSON.parse(localStorage.getItem(KEY) || '[]'); } catch (_) {}
        log = log.filter(function (t) { return (now - t) < WINDOW_MS; });
        if (log.length >= MAX_RELOADS) {
          console.warn('[cache-purge] Reload throttled (already reloaded ' + log.length + ' time(s) in last 10min)');
          return;
        }
        log.push(now);
        localStorage.setItem(KEY, JSON.stringify(log));
        // 🛡️ 2026-05-21 P0-3: checkout / submit 進行中は reload 抑止 (form state 損失防止)
        if (window.__checkout_in_flight) {
          console.warn('[cache-purge] Reload skipped: checkout submit in flight');
          return;
        }
        console.warn('[cache-purge] Stale render suspected (transferSize=0, type=' + nav.type + ') — reloading');
        location.reload();
      } catch (e) { /* iOS 古いバージョンで fail しても無視 */ }
    }).then(function () {
      // 🆕 サーバー側 cache_version との照合 (CEO ダッシュ「全生徒キャッシュ強制パージ」と連動)
      // サーバーが新しい version を発行していたら caches 削除 + 強制リロード
      try {
        var backend = (window.location.hostname === 'localhost' && window.location.port === '8090')
          ? 'http://localhost:8000' : window.location.origin;
        fetch(backend + '/api/cache-version', { cache: 'no-store' }).then(function (res) {
          if (!res.ok) return;
          return res.json();
        }).then(function (data) {
          if (!data || !data.version) return;
          var serverVer = data.version;
          var localVer = localStorage.getItem('ai_juku_cache_version');
          if (localVer === serverVer) return; // 同一なら何もしない
          // 新しい version → caches 削除 + reload (sessionStorage の reload-once flag は別管理)
          var REL = 'ai_juku_force_reload_' + serverVer;
          if (sessionStorage.getItem(REL)) {
            // 同じ version で 2回目はスキップ (無限 reload 防止)
            localStorage.setItem('ai_juku_cache_version', serverVer);
            return;
          }
          sessionStorage.setItem(REL, '1');
          localStorage.setItem('ai_juku_cache_version', serverVer);
          // 🛡️ 2026-05-27 PWA cache 致命傷 fix: version bump 検知時は throttle (10 分 1 回制限) もリセット
          // → 古い HTML cache が transferSize=0 で reload trigger を発火し損ねた場合のリカバリ
          try { localStorage.removeItem('ai_juku_sw_purge_log_v2'); } catch (_) {}
          console.warn('[cache-purge] New cache_version detected: ' + (localVer || 'none') + ' → ' + serverVer + ' — purging + reloading');
          // 🛡️ 2026-05-21 P0-3: checkout submit 進行中は reload を遅延 (form state 損失防止)
          var doReload = function () {
            if (window.__checkout_in_flight) {
              console.warn('[cache-purge] Reload deferred: checkout submit in flight (retry in 5s)');
              setTimeout(doReload, 5000);
              return;
            }
            location.reload();
          };
          if (typeof caches !== 'undefined') {
            caches.keys().then(function (keys) {
              return Promise.all(keys.map(function (k) { return caches.delete(k); }));
            }).finally(doReload);
          } else {
            doReload();
          }
        }).catch(function () { /* オフライン時は何もしない */ });
      } catch (e) { /* fetch 不可なブラウザは無視 */ }
    }).catch(function (e) {
      console.warn('[cache-purge] cleanup failed:', e);
    });
  } catch (e) { /* 古いブラウザで fail しても無視 */ }
})();

// ==========================================================================
// 🛡️ [cross-student-cache-guard] per-student ローカルキャッシュの単一ソース
//
// これらは studentId でスコープされていない **GLOBAL** localStorage キーなので、
// 同一端末で別生徒に切り替わった瞬間 (ログイン / 塾長なりすまし / 再ログイン) に
// 破棄しないと前生徒の学習データが次の生徒に表示される。
//
// 【2026-07-21 ここへ移設した理由】
//   旧実装は app.js だけにあり、app.js を読むのは index.html のみ。だが実ログイン導線は
//   login/auth → quick-start.html → mypage.html で index.html を経由しない (login.html:392)
//   ため、「ログアウトせずに別生徒がログイン」経路ではガードが一度も走っていなかった。
//   english-exam.html に至っては app.js も auth-guard.js も読まない。
//   cache-purge.js はほぼ全生徒ページの <head> 先頭で同期読み込みされる (例外は kyoto2025-*/
//   todai2025-* の9ページ=auth-guard.js の fallback リテラルが担保)。ここに置くことで
//   「ページを開いた時点で必ず走る」を満たす (headless 実ページ検証で確認)。
//
// 【2026-07-21 データを消してよいキーの判定基準】
//   ⚠️ 破棄してよいのは「サーバに正がある = 再取得できる」か「使い捨てバッファ」だけ。
//      端末が唯一の保管場所のデータをここに足すと、切替時だけでなく初回ロードや本人の
//      ログアウトでも消え、復元不能になる。そういうデータは破棄せず生徒IDでキーを分ける
//      (下の window.aiJukuStudentScopedKey 方式)。
//
// ⚠️ 新しい per-student グローバルキャッシュを足したら、下の配列と
//    auth-guard.js の clearSession() (= ログアウト/401 経路) の両方に登録すること。
// ==========================================================================
window.AI_JUKU_PER_STUDENT_CACHE_KEYS = [
  'ai_juku_chat_history',    // AIチューター履歴 (正=サーバ /api/ai-tutor/history/me)
  'ai_juku_stats',           // 学習統計 (index.html の問題数カウンタ・表示のみ)
  'ai_juku_problem_history', // 直近20件の問題履歴 (上限付きキャッシュ)
  'ai_juku_activity',        // 活動ログ
  'ai_juku_last_curriculum', // 学習プラン取込の一時バッファ (確定分は正=サーバ curricula)
  'ai_juku_students',        // 🔑 生徒名簿=氏名PII。残すと index.html の生徒切替ドロップダウンに
                             //   前生徒の氏名が出る。正=サーバ (/api/auth/me → applyVerifiedStudent)
  'ai_juku_current_student', // 🔑 表示ポインタ。上と対で再構築される
  // --- 2026-07-21 [xstudent-batch2] 棚卸しで発見した未処置キー (使い捨て/統計クラス → 破棄で閉鎖) ---
  'ai_juku_email_log',       // 🔑 旧メール送信ログ=保護者メール PII。正無し・使い捨てログ
  'ai_juku_support_tickets', // 🔑 サポートフォーム下書き=氏名/メール PII (書き込みのみで読み手無し)
  'ai_juku_session_stats_v1',// セッション正答率/苦手単元 (ai_juku_stats と同クラスの表示統計)
  'ai_juku_problem_stats_v1',// 問題別 正答率カウンタ (同上)
  'ai_juku_problem_sessions',// 生成済み問題セットのキャッシュ (~150KB×15 上限・再生成可能)
  'ai_juku_vocab_progress',  // english-exam 内蔵単語トレーナーのカウント (SRS 本体はサーバ側で別物)
  'ai_juku_question_issues'  // オフライン時の問題報告バッファ (再送実装なし=死蔵。PII 無し)
];

// ==========================================================================
// 🔑 [curriculum-per-student] 端末が唯一の保管場所のデータは「破棄」でなく「キー分離」
//
//   ee_curriculum_v1 = AI 生成カリキュラム (受験校/弱点/週ロードマップ/completed_weeks)。
//   サーバに保存も復元APIも無い (server/main.py の /api/curriculum/generate は生成のみ)。
//   消すと 1〜3分・約$0.12 の生成結果と、生徒が手で付けた週チェックが復元不能で失われる。
//   → ee_curriculum_v1__<生徒ID> に分ける。別生徒からは構造的に読めず (漏洩が閉じる)、
//     かつ本人はログアウトしても別生徒を挟んでも自分のプランを保持できる。
//   読み手 (english-exam.js / mypage.html) は必ずこの関数でキーを解決すること。
//   ★ここが唯一のキー導出。各所で文字列を組み立てると必ず片側だけ直す事故になる。
// ==========================================================================
(function perStudentCacheGuard() {
  var CURRICULUM_BASE_KEY = 'ee_curriculum_v1';
  var EXAM_HISTORY_BASE_KEY = 'ai_juku_eng_exam_history';
  var OWNER_KEY = 'ai_juku_cache_owner_sid';

  // 識別は信頼できる ai_juku_session_student.id のみを使う (auth-guard が /api/auth/me で確定し、
  // login/auth/ceo なりすましの各経路も token と同じ同期ブロックで設定するキー)。
  // ⚠️ aj_current_student_id への fallback は持たない: それは applyVerifiedStudent が後から
  //    書く別系統で、ログイン直後は「前の生徒」の値が残っている。fallback すると OWNER_KEY を
  //    誤った生徒で確定させ、以後の破棄を永久に抑止してしまう (判定不能なら次回ロードに委ねる)。
  // 生徒IDは必ず数字 (server/main.py の students.id)。数字以外は信用しない
  //   (localStorage を手で書けば "anon"/"unattributed" を騙れてしまうため)。
  function currentSid() {
    try {
      var ss = JSON.parse(localStorage.getItem('ai_juku_session_student') || '{}') || {};
      if (ss.id !== null && ss.id !== undefined && ss.id !== '') {
        var id = String(ss.id);
        if (/^\d+$/.test(id)) return id;
      }
    } catch (_) {}
    return '';
  }

  // 生徒スコープ付きキーの唯一の導出点。
  // 未ログイン(匿名)は従来どおり共有の __anon バケット (匿名利用は正規動線のため維持)。
  // ⚠️ 「token はあるが生徒IDを解決できない」時に __anon へ落としてはいけない: ログイン済み
  //   生徒のデータを共有バケットに書き込む=別の匿名利用者に見える。null を返して
  //   読み手側で fail-closed (保存しない/未生成扱い) にする。
  window.aiJukuStudentScopedKey = function (baseKey) {
    var sid = currentSid();
    if (sid) return baseKey + '__' + sid;
    if (localStorage.getItem('ai_juku_session_token')) return null; // 本人ID未確定
    return baseKey + '__anon';
  };

  // ※ 受験履歴 (直近50件・EXAM_HISTORY_BASE_KEY) はカリキュラム生成の **入力** でもあるため、
  //   共有のままにすると別生徒の弱点から AI プランが作られる。サーバに正が無いので破棄でなく
  //   スコープ化する (english-exam.js が aiJukuStudentScopedKey で解決)。

  // スコープ付きキーの読み出し (生の文字列を返す・無ければ null)。
  // 匿名時のみ旧グローバルキーへフォールバックする: 匿名ロードでは下の移行を意図的に走らせない
  // (持ち主判定は次のログイン時に行う) ため、未ログイン時代のデータはまだ旧キーに居る。
  // ログイン済みは <head> の移行が先に走っているのでフォールバック不要。
  window.aiJukuReadScoped = function (baseKey) {
    var k = window.aiJukuStudentScopedKey(baseKey);
    if (k === null) return null;                        // 本人ID未確定: fail-closed
    var v = localStorage.getItem(k);
    if (v === null && !localStorage.getItem('ai_juku_session_token')) {
      v = localStorage.getItem(baseKey);
    }
    return v;
  };

  // この端末で「今の生徒とは別の生徒」が使われた痕跡があるか。
  // 旧グローバルキーの持ち主を確定できるかの判定に使う。判定不能なら安全側 (=痕跡あり) を返す。
  // app.js の seedStudents (デモ生徒 山田太郎/佐藤花子/鈴木一郎) は名簿が空だと自動投入され
  // 永続化される (app.js:761-765)。これを「別生徒の痕跡」と数えると、単独利用の端末でも
  // 引き継ぎが拒否され本人がプランを失う。サーバ由来の生徒は必ず email を持つ (/api/auth/me)
  // 一方デモ生徒は parentEmail しか持たないので、その2条件でデモ行だけを除外する。
  function isDemoSeedStudent(s) {
    var id = String(s.id);
    return (id === '1' || id === '2' || id === '3') && !s.email;
  }

  function deviceSawAnotherStudent(sid) {
    try {
      var owner = localStorage.getItem(OWNER_KEY);
      if (owner && owner !== sid) return true;
      var list = JSON.parse(localStorage.getItem('ai_juku_students') || '[]');
      // 壊れた値 (非配列) は「証拠なし」ではなく「判定不能」= 安全側に倒す。
      if (Object.prototype.toString.call(list) !== '[object Array]') return true;
      for (var i = 0; i < list.length; i++) {
        var s = list[i];
        if (!s || s.id === null || s.id === undefined) continue;
        if (String(s.id) === sid || isDemoSeedStudent(s)) continue;
        return true;
      }
    } catch (_) { return true; }
    return false;
  }

  // 持ち主を確定できない旧データの隔離先。読み手は aiJukuStudentScopedKey() 経由のみで、
  // そこは「数字の生徒ID」か「__anon」しか返さない (__unattributed は返さない) ため、
  // 隔離キーは誰の画面にも出ない = 漏洩ゼロ。
  // サーバに正が無いデータを「捨てる」代わりに「見えない場所に保全」して後から救出可能にする。
  // 空きスロットを順に探すのは、1枠固定だと埋まっていた時に退避できず削除に倒れるため。
  function quarantine(baseKey, value) {
    for (var i = 0; i < 5; i++) {
      var k = baseKey + '__unattributed' + (i === 0 ? '' : ('_' + i));
      var cur = localStorage.getItem(k);
      if (cur === null) { localStorage.setItem(k, value); return true; }
      if (cur === value) return true;   // 同一内容が既に退避済み
    }
    return false;
  }

  // 旧グローバルキー (スコープ無し時代のデータ) の一度きりの移行。**ログイン時のみ** 行う。
  //   ・持ち主を確定できる端末 (別生徒の痕跡なし) → 本人のスコープ付きキーへ引き継ぎ (損失ゼロ)
  //     (塾長決定 2026-07-21: 匿名利用者は痕跡を残さないため、匿名作成分が「次に最初に
  //      ログインした生徒」に渡り得るリスクを許容し、損失ゼロを優先する)
  //   ・確定できない端末 → 引き継がず隔離 (別生徒に渡さない・ただし捨てもしない)
  //   ・匿名ロードでは **移行しない**。login.html 等も cache-purge を読むため、ここで動かすと
  //     「ログアウト中に通過しただけ」で本人のプランが共有 __anon へ流れ、再ログイン後に
  //     見えなくなる (旧実装の実損)。匿名の読み手は aiJukuReadScoped の旧キーフォールバックで
  //     引き続き自分のデータを見られる。
  function migrateLegacyKey(baseKey, sid) {
    if (!sid) return;
    var legacy = null;
    try { legacy = localStorage.getItem(baseKey); } catch (_) { return; }
    if (legacy === null) return;
    try {
      var target = baseKey + '__' + sid;
      if (deviceSawAnotherStudent(sid)) target = null;         // 持ち主不明 → 隔離へ回す
      var saved = false;
      if (target !== null) {
        var cur = localStorage.getItem(target);
        if (cur === null) {
          localStorage.setItem(target, legacy); saved = true;
          // 2026-07-21 [inherit-notice] ヒューリスティック引き継ぎ (=持ち主推定で本人扱いにした) を記録。
          // mypage が一度だけ「引き継ぎました (違う場合は取り消し)」バナーを出す (塾長承認の通知+取り消し式)。
          // タグ照合 (moshi split/rescue) は持ち主が証明済みなので記録しない
          recordInheritNotice(baseKey, sid);
        }
        else if (cur === legacy) { saved = true; }             // 既に同じ内容が入っている
      }
      if (!saved) saved = quarantine(baseKey, legacy);
      // ⚠️ 退避できた時だけ旧キーを消す。無条件に消すと、退避先が既に埋まっていた場合に
      //   「どこにもコピーが無いまま削除」= サーバに正の無いデータの完全消失になる。
      //   (旧キーが残っても読み手は匿名フォールバックだけ = ログイン画面には出ない)
      if (saved) localStorage.removeItem(baseKey);
    } catch (_) {}
  }

  // 2026-07-21 [xstudent-batch2] 模試履歴のように「各エントリが studentId タグを持つ配列」の移行。
  // ⚠️ タグの数字だけでは「実生徒 ID」と「匿名デモ生徒 ID (app.js の seedStudents は 1,2,3…)」を
  //   区別できない。タグごとに __<tag> へ配ると、匿名時代のデモ模試が実在の若番生徒のバケットへ
  //   合流し得る (成績記録の汚染 = 消失より悪い)。→ 保守的に「今ログイン中の本人タグだけ引き取り、
  //   それ以外 (他タグ/タグ無し) は隔離」。他の実生徒のぶんは本人がこの端末で先にログインすれば
  //   その時の本ルーチンで自分のバケットに入り、後手なら隔離 (救出可能・共有キーからは消える)。
  // 部分失敗時は旧キーを残し、再実行は内容一致 dedupe で冪等
  function splitMigrateTagged(baseKey, sid) {
    if (!sid) return;
    var raw = null;
    try { raw = localStorage.getItem(baseKey); } catch (_) { return; }
    if (raw === null) return;
    try {
      var arr = JSON.parse(raw);
      if (!(arr instanceof Array)) {
        if (quarantine(baseKey, raw)) localStorage.removeItem(baseKey);
        return;
      }
      var mine = [];
      var others = [];
      for (var i = 0; i < arr.length; i++) {
        var e = arr[i];
        var tag = (e && e.studentId !== null && e.studentId !== undefined) ? String(e.studentId) : '';
        if (tag === String(sid)) mine.push(e); else others.push(e);
      }
      var allSaved = true;
      if (mine.length) {
        try {
          var tk = baseKey + '__' + sid;
          var curRaw = localStorage.getItem(tk);
          var cur = curRaw ? JSON.parse(curRaw) : [];
          if (!(cur instanceof Array)) cur = [];
          // 内容一致 dedupe: 部分失敗→再実行で同じ行を二重に積まない
          var seen = {};
          for (var c = 0; c < cur.length; c++) { try { seen[JSON.stringify(cur[c])] = 1; } catch (_) {} }
          for (var g = 0; g < mine.length; g++) {
            var sig = '';
            try { sig = JSON.stringify(mine[g]); } catch (_) {}
            if (!sig || !seen[sig]) cur.push(mine[g]);
          }
          localStorage.setItem(tk, JSON.stringify(cur));
        } catch (_) { allSaved = false; }
      }
      if (others.length) {
        if (!quarantine(baseKey, JSON.stringify(others))) allSaved = false;
      }
      if (allSaved) localStorage.removeItem(baseKey);
    } catch (_) {}
  }

  // 2026-07-21 [inherit-notice] 引き継ぎ通知マーカー (生徒別キー・値は引き継いだ baseKey の配列)。
  // 生徒が「自分のものではない」を押したら aiJukuUndoInherit がバケットごと隔離へ退避して取り消す
  function inheritNoticeKey(sid) { return 'ai_juku_inherit_notice__' + sid; }
  function recordInheritNotice(baseKey, sid) {
    try {
      var k = inheritNoticeKey(sid);
      var raw = localStorage.getItem(k);
      var arr = raw ? JSON.parse(raw) : [];
      if (!(arr instanceof Array)) arr = [];
      var found = false;
      for (var i = 0; i < arr.length; i++) { if (arr[i] === baseKey) { found = true; break; } }
      if (!found) arr.push(baseKey);
      localStorage.setItem(k, JSON.stringify(arr));
    } catch (_) {}
  }
  // mypage のバナーが使う公開 API。sid は数字のみ (この file の規律)
  window.aiJukuGetInheritNotice = function (sid) {
    if (!/^\d+$/.test(String(sid || ''))) return [];
    try {
      var arr = JSON.parse(localStorage.getItem(inheritNoticeKey(String(sid))) || '[]');
      return (arr instanceof Array) ? arr : [];
    } catch (_) { return []; }
  };
  window.aiJukuDismissInheritNotice = function (sid) {
    if (!/^\d+$/.test(String(sid || ''))) return;
    try { localStorage.removeItem(inheritNoticeKey(String(sid))); } catch (_) {}
  };
  window.aiJukuUndoInherit = function (sid) {
    if (!/^\d+$/.test(String(sid || ''))) return false;
    sid = String(sid);
    var keys = window.aiJukuGetInheritNotice(sid);
    var allMoved = true;
    for (var i = 0; i < keys.length; i++) {
      var baseKey = keys[i];
      // baseKey は自分が記録した文字列だが、念のため素性を検査 (localStorage 改竄で任意キーを消させない)
      if (typeof baseKey !== 'string' || !/^[a-z0-9_]+$/i.test(baseKey)) continue;
      try {
        var bk = baseKey + '__' + sid;
        var val = localStorage.getItem(bk);
        if (val === null) continue;
        // 隔離へ退避できた時だけバケットを消す (コピー無し削除の禁止はここでも同じ)
        if (quarantine(baseKey, val)) localStorage.removeItem(bk);
        else allMoved = false;
      } catch (_) { allMoved = false; }
    }
    if (allMoved) window.aiJukuDismissInheritNotice(sid);
    return allMoved;
  };

  // 2026-07-21 [xstudent-batch2] 隔離からの救出。模試履歴はエントリに studentId タグがあるので、
  // 「後からログインした本人」のぶんを隔離スロットから回収できる (review 指摘: 救出路が無いと
  // 共用端末で2番目にログインした生徒の自己記録が見かけ上消えたままになる)。タグの無いキー
  // (exam-prep 等) は持ち主を証明できないため対象外。スロット内の非配列 (blob ごと隔離) は触らない。
  // 回収先への保存が成功してからスロットを縮める (失敗時はスロット無傷=データ喪失なし)
  function rescueTaggedFromQuarantine(baseKey, sid) {
    if (!sid) return;
    for (var i = 0; i < 5; i++) {
      var k = baseKey + '__unattributed' + (i === 0 ? '' : ('_' + i));
      var raw = null;
      try { raw = localStorage.getItem(k); } catch (_) { continue; }
      if (raw === null) continue;
      try {
        var arr = JSON.parse(raw);
        if (!(arr instanceof Array)) continue;
        var mine = [];
        var rest = [];
        for (var j = 0; j < arr.length; j++) {
          var e = arr[j];
          var tag = (e && e.studentId !== null && e.studentId !== undefined) ? String(e.studentId) : '';
          if (tag === String(sid)) mine.push(e); else rest.push(e);
        }
        if (!mine.length) continue;
        var tk = baseKey + '__' + sid;
        var curRaw = localStorage.getItem(tk);
        var cur = curRaw ? JSON.parse(curRaw) : [];
        if (!(cur instanceof Array)) cur = [];
        var seen = {};
        for (var c = 0; c < cur.length; c++) { try { seen[JSON.stringify(cur[c])] = 1; } catch (_) {} }
        for (var m = 0; m < mine.length; m++) {
          var sig = '';
          try { sig = JSON.stringify(mine[m]); } catch (_) {}
          if (!sig || !seen[sig]) cur.push(mine[m]);
        }
        localStorage.setItem(tk, JSON.stringify(cur));
        if (rest.length) localStorage.setItem(k, JSON.stringify(rest));
        else localStorage.removeItem(k);
      } catch (_) {}
    }
  }

  try {
    var hasToken = !!localStorage.getItem('ai_juku_session_token');
    var sid = hasToken ? currentSid() : '';
    // ⚠️ 「token はあるが生徒ID未確定」は匿名と同じ扱いにしてはいけない。匿名分岐に落とすと
    //   ログイン済み生徒のプランを共有 __anon バケットへ移してしまう。何もせず次回に委ねる。
    if (hasToken && !sid) return;
    // ★順序が重要: 移行判定は ai_juku_students / OWNER_KEY を証拠に使うので、破棄より先に行う。
    migrateLegacyKey(CURRICULUM_BASE_KEY, sid);
    migrateLegacyKey(EXAM_HISTORY_BASE_KEY, sid);
    // 2026-07-21 [xstudent-batch2] 追加スコープ化。exam_prep = 定期テスト予定 (学校名・試験日・
    // 範囲。mypage widget が今まで全生徒混載で表示していた)。referral = 紹介コード/履歴 (前生徒の
    // コードを次生徒が引き継ぐと報酬の誤帰属)。いずれもタグ無し単一 blob → 持ち主ヒューリスティック
    migrateLegacyKey('ai_juku_exam_prep__exams', sid);
    migrateLegacyKey('ai_juku_referral__my_code', sid);
    migrateLegacyKey('ai_juku_referral__history', sid);
    // 模試履歴はエントリ毎 studentId タグ → 本人タグのみ引き取り・他タグ/タグ無しは隔離
    // (匿名は sid='' で no-op = 旧キー継続。デモ ID と実 ID の衝突汚染を避けるため多バケット配布はしない)
    splitMigrateTagged('ai_juku_moshi_history', sid);
    // 過去に隔離された自分タグの行はここで回収 (2番目以降にログインした本人の帰り道)
    rescueTaggedFromQuarantine('ai_juku_moshi_history', sid);
    if (!sid) return;                                    // 未ログイン: 破棄はしない
    if (localStorage.getItem(OWNER_KEY) === sid) return; // 同一生徒: 何もしない
    // 生徒が変わった (または本ガード初回) → 再取得可能な per-student キャッシュのみ破棄。
    var meRaw = localStorage.getItem('ai_juku_session_student');
    window.AI_JUKU_PER_STUDENT_CACHE_KEYS.forEach(function (k) {
      try { localStorage.removeItem(k); } catch (_) {}
    });
    // exam_pool_cache:<exam>/<grade>/<section> は server プールの 5 分 TTL キャッシュ (再取得可能)。
    // 前生徒の出題傾向が滲むだけだが、生徒切替のついでにまとめて捨てる (キーは可変なので prefix 走査)
    try {
      for (var pci = localStorage.length - 1; pci >= 0; pci--) {
        var pck = localStorage.key(pci);
        if (pck && pck.indexOf('exam_pool_cache:') === 0) localStorage.removeItem(pck);
      }
    } catch (_) {}
    // 🔑 名簿と表示ポインタだけは「削除」でなく「今の生徒1件で上書き」する。
    //   空のまま app.js に渡すと app.js:761-765 が seedStudents (デモ生徒 山田太郎/佐藤花子/
    //   鈴木一郎) を書き戻して永続化し、生徒切替ドロップダウンに架空の生徒が並ぶ。
    //   auth-guard の applyVerifiedStudent は /api/auth/me の非同期応答後なので間に合わない。
    //   前生徒の氏名 PII は消える (本来の目的) まま、空名簿だけを避けられる。
    try {
      var me = meRaw ? JSON.parse(meRaw) : null;
      if (me && me.id !== null && me.id !== undefined) {
        localStorage.setItem('ai_juku_students', JSON.stringify([me]));
        localStorage.setItem('ai_juku_current_student', JSON.stringify(me.id));
        // vocab/mock-exam が読む別系統ポインタ。ここだけ前生徒のまま残すと非対称になる
        // (サーバは token の student_id で判定するので実害は無いが、表示が食い違う)。
        localStorage.setItem('aj_current_student_id', sid);
      }
    } catch (_) {}
    localStorage.setItem(OWNER_KEY, sid);
  } catch (_) { /* 失敗してもアプリ動作は止めない */ }
})();

// ==========================================================================
// 🔄 ユーザー操作: システム強制更新ボタン用の共通関数
// 「同じ回答ばかり」など古いキャッシュ由来の不具合を生徒自身で解消するため、
// mypage.html / index.html のヘッダーボタンから呼び出される。
// ==========================================================================
window.forceUpdateApp = function () {
  if (!confirm('🔄 システムを最新版に更新します。\n\nブラウザの古いキャッシュをクリアして再読込します。\nよろしいですか?')) return;

  // 1. 古い AI チャット履歴を削除 (汚染履歴が context に紛れ込むのを防ぐ)
  try { localStorage.removeItem('ai_juku_chat_history'); } catch (e) {}
  try { localStorage.removeItem('ai_juku_force_reload'); } catch (e) {}

  // 2. Service Worker を全 unregister
  var swPromise = Promise.resolve();
  try {
    if ('serviceWorker' in navigator) {
      swPromise = navigator.serviceWorker.getRegistrations().then(function (regs) {
        return Promise.all(regs.map(function (r) { return r.unregister(); }));
      });
    }
  } catch (e) {}

  // 3. Cache Storage を全削除
  var cachePromise = Promise.resolve();
  try {
    if ('caches' in window) {
      cachePromise = caches.keys().then(function (keys) {
        return Promise.all(keys.map(function (k) { return caches.delete(k); }));
      });
    }
  } catch (e) {}

  Promise.allSettled([swPromise, cachePromise]).finally(function () {
    // 4. cache buster 付きで hard reload (CDN edge cache も bypass)
    var url = new URL(window.location.href);
    url.searchParams.set('_cb', Date.now().toString());
    window.location.replace(url.toString());
  });
};

