// ==========================================================================
// 🧒 中学生モード 共有ユーティリティ (student-mode.js) — 2026-06-04
//   生徒の grade (学年) から学習モードを判定し、全画面で一貫して使う単一ソース。
//     小学(小4-6)        = 中学受験モード  shougaku  (target_grade=小学生)
//     中学(中1-3)        = 中学生モード/高校受験 chugaku (target_grade=中学生)
//     高校/既卒/その他/未設定 = 高校生モード/大学受験 kosei (現行・既定)
//   依存なし。グローバル関数を window に公開。AuthGuard があれば優先利用。
//   ⚠️ kosei は現行の大学受験生 (200名超) の挙動を一切変えない設計 (回帰ゼロ)。
// ==========================================================================
(function () {
  'use strict';

  // 学年文字列 → モードキー
  function ajStudentMode(grade) {
    var g = String(grade == null ? '' : grade);
    if (/小学|小[1-6]年?|中学受験|中受/.test(g)) return 'shougaku';
    if (/中学|中[1-3]年?/.test(g)) return 'chugaku';
    return 'kosei';
  }

  var META = {
    shougaku: { key: 'shougaku', label: '中学受験モード', short: '中学受験', emoji: '🎒', targetGrade: '小学生', kubun: '中学受験', desc: '中学受験対策' },
    chugaku:  { key: 'chugaku',  label: '中学生モード',   short: '高校受験', emoji: '🧒', targetGrade: '中学生', kubun: '高校受験', desc: '高校受験・中学学習' },
    kosei:    { key: 'kosei',    label: '高校生モード',   short: '大学受験', emoji: '🎓', targetGrade: '高校生', kubun: null,       desc: '大学受験' }
  };

  function ajModeMeta(grade) { return META[ajStudentMode(grade)] || META.kosei; }

  // ログイン中の生徒オブジェクト (AuthGuard 優先 → localStorage フォールバック)
  function ajSessionStudent() {
    try {
      if (window.AuthGuard && typeof window.AuthGuard.getStudent === 'function') {
        var a = window.AuthGuard.getStudent();
        if (a && a.grade != null) return a;
      }
    } catch (e) {}
    try { return JSON.parse(localStorage.getItem('ai_juku_session_student') || 'null'); } catch (e) { return null; }
  }

  function ajCurrentGrade() { var s = ajSessionStudent(); return (s && s.grade) || ''; }
  // 🧒 塾長プレビュー (2026-06-04): URL に ?preview_mode=chugaku|shougaku|kosei が付いていれば、
  //   ログイン生徒の学年に関係なくそのモードを強制表示 (CEO ダッシュの「このモードを見る」用)。
  function ajPreviewMode() {
    try {
      var p = new URLSearchParams(window.location.search).get('preview_mode');
      if (p === 'chugaku' || p === 'shougaku' || p === 'kosei') return p;
    } catch (e) {}
    return null;
  }
  function ajCurrentMode() { return ajPreviewMode() || ajStudentMode(ajCurrentGrade()); }

  // lesson_prints レコード p が指定モードに適合するか。
  //   DB 実値: target_grade ∈ {高校生(494件), 中学生(6件), 小学生(0), 無タグ}
  //   kosei   : 中学/小学 専用タグを除外 (= 高校生 + 無タグ + その他 を表示) → 既存は全件残る
  //   chugaku : 中学生タグ or 無タグ汎用 (高校生=大学 / 小学 を除外)
  //   shougaku: 小学生タグのみ
  function ajPrintMatchesMode(p, mode) {
    var tg = String((p && p.target_grade) || '');
    var isChu = tg.indexOf('中学') >= 0;
    var isSho = tg.indexOf('小学') >= 0;
    var isKou = tg.indexOf('高校') >= 0;
    if (mode === 'shougaku') return isSho;
    if (mode === 'chugaku')  return isChu || (!isKou && !isSho);
    return !isChu && !isSho;
  }

  window.ajStudentMode = ajStudentMode;
  window.AJ_MODE_META = META;
  window.ajModeMeta = ajModeMeta;
  window.ajSessionStudent = ajSessionStudent;
  window.ajCurrentGrade = ajCurrentGrade;
  window.ajCurrentMode = ajCurrentMode;
  window.ajPreviewMode = ajPreviewMode;
  window.ajPrintMatchesMode = ajPrintMatchesMode;
})();
