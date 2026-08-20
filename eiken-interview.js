/* eiken-interview.js — 英検準1級 二次面接シミュレーション (発音つき・$0)
 * 2026-07-23 塾長依頼「発音つき二次面接モードの作り込み」。
 * english-exam.js の startSection() が section.key==='s_interview' 時に window.startEikenInterview() を呼ぶ。
 *
 * 機能 (すべてブラウザ内 + 既存AIプロキシで $0・新規有料APIなし):
 *  - s_interview プール(1カード=ナレーション+No.1〜No.4)を取得し、本番の流れで逐次進行
 *  - 面接官が英語で質問を「音声」で読み上げ (Web Speech API SpeechSynthesis)
 *  - 準備タイマー(ナレーション60秒)/回答タイマー(ナレーション120秒・各Q60秒)
 *  - 録音 (MediaRecorder) → 自分の声を再生して自己確認
 *  - 模範解答を「音声」で聴き比べ (TTS)
 *  - 音声認識 (SpeechRecognition) で文字起こし → AIが内容(構成/文法/語彙/応答)を採点 + 発音アドバイス
 *  - 認識の明瞭度 (confidence) を発音の「目安」として表示 (Chrome/Android中心・iOSは非対応の旨明記)
 *
 * 発音の「認定スコア」ではない旨をUIに明記。真の音素採点は有料API(Azure等)が必要。
 */
(function () {
  'use strict';

  var PROD_API = 'https://ai-juku-api-production.up.railway.app';
  function apiBase() {
    return (location.hostname === 'localhost' && location.port === '8090')
      ? 'http://localhost:8000' : location.origin;
  }
  // 試行するAPIベース (localhost では localhost:8000 → 本番、本番では同一オリジン → Railway直 の順)
  function bases() {
    var list = [apiBase()];
    if (list.indexOf(PROD_API) < 0) list.push(PROD_API);
    return list;
  }
  function getToken() {
    return (window.AuthGuard && window.AuthGuard.getToken && window.AuthGuard.getToken())
      || localStorage.getItem('ai_juku_session_token')
      || localStorage.getItem('ai_juku_admin_token') || '';
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function fmt(sec) { var m = Math.floor(sec / 60), s = sec % 60; return m + ':' + (s < 10 ? '0' : '') + s; }

  // ---------- TTS (面接官の声 / 模範音声) ----------
  var _voices = [];
  function loadVoices() { try { _voices = window.speechSynthesis.getVoices() || []; } catch (e) { _voices = []; } }
  if ('speechSynthesis' in window) { loadVoices(); window.speechSynthesis.onvoiceschanged = loadVoices; }
  function pickEnVoice() {
    return _voices.find(function (v) { return v.lang && v.lang.indexOf('en') === 0 && /Samantha|Alex|Daniel|Karen|Google US|Google UK|Microsoft/.test(v.name); })
      || _voices.find(function (v) { return v.lang === 'en-US'; })
      || _voices.find(function (v) { return v.lang && v.lang.indexOf('en') === 0; }) || null;
  }
  function speak(text, opts) {
    opts = opts || {};
    if (!('speechSynthesis' in window)) { if (opts.onend) opts.onend(); return; }
    try {
      window.speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(String(text || ''));
      u.lang = 'en-US'; u.rate = opts.rate || 0.95; u.pitch = 1.0;
      var v = pickEnVoice(); if (v) u.voice = v;
      u.onend = function () { if (opts.onend) opts.onend(); };
      u.onerror = function () { if (opts.onend) opts.onend(); };
      window.speechSynthesis.speak(u);
    } catch (e) { if (opts.onend) opts.onend(); }
  }
  function stopSpeak() { try { window.speechSynthesis.cancel(); } catch (e) {} }

  // ---------- state ----------
  var S = {
    card: null, qs: [], idx: 0, answers: [], phase: 'idle',
    stream: null, rec: null, chunks: [], recognition: null,
    curTranscript: '', curConf: 0, curConfN: 0,
    timer: null, remain: 0, sttSupported: false, recording: false,
  };
  var overlay = null, contentEl = null;

  function sttAvailable() { return !!(window.SpeechRecognition || window.webkitSpeechRecognition); }

  // ---------- teardown ----------
  function cleanup() {
    stopSpeak();
    if (S.timer) { clearInterval(S.timer); S.timer = null; }
    try { if (S.rec && S.rec.state !== 'inactive') S.rec.stop(); } catch (e) {}
    try { if (S.recognition) S.recognition.stop(); } catch (e) {}
    try { if (S.stream) S.stream.getTracks().forEach(function (t) { t.stop(); }); } catch (e) {}
    S.rec = null; S.recognition = null; S.stream = null; S.recording = false;
  }
  function closeAll() {
    cleanup();
    (S.answers || []).forEach(function (a) { if (a && a.url) { try { URL.revokeObjectURL(a.url); } catch (e) {} } });
    if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay);
    overlay = null; contentEl = null;
    S.card = null; S.qs = []; S.idx = 0; S.answers = []; S.phase = 'idle';
  }

  // ---------- overlay shell ----------
  function ensureOverlay() {
    if (overlay) return;
    injectStyle();
    overlay = document.createElement('div');
    overlay.id = 'eiken-interview-overlay';
    overlay.innerHTML =
      '<div class="eiv-modal">' +
      '  <div class="eiv-head">' +
      '    <span class="eiv-title">🎤 英検準1級 二次面接シミュレーション</span>' +
      '    <button class="eiv-close" type="button" aria-label="閉じる">✕ 閉じる</button>' +
      '  </div>' +
      '  <div class="eiv-body"></div>' +
      '</div>';
    document.body.appendChild(overlay);
    contentEl = overlay.querySelector('.eiv-body');
    overlay.querySelector('.eiv-close').addEventListener('click', function () {
      if (S.phase === 'prep' || S.phase === 'answer') {
        if (!window.confirm('面接を中断して閉じますか？(録音は保存されません)')) return;
      }
      closeAll();
    });
  }

  function injectStyle() {
    if (document.getElementById('eiv-style')) return;
    var css =
      '#eiken-interview-overlay{position:fixed;inset:0;z-index:100000;background:rgba(2,6,23,.85);backdrop-filter:blur(4px);display:flex;align-items:flex-start;justify-content:center;overflow-y:auto;padding:2vh 12px;}' +
      '.eiv-modal{width:100%;max-width:820px;background:linear-gradient(180deg,#0f172a,#111827);border:1px solid rgba(148,163,184,.25);border-radius:16px;box-shadow:0 24px 80px rgba(0,0,0,.6);color:#e5e7eb;margin:auto;}' +
      '.eiv-head{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:14px 18px;border-bottom:1px solid rgba(148,163,184,.18);position:sticky;top:0;background:rgba(15,23,42,.96);border-radius:16px 16px 0 0;z-index:2;}' +
      '.eiv-title{font-weight:800;font-size:1rem;}' +
      '.eiv-close{background:rgba(248,113,113,.14);border:1px solid rgba(248,113,113,.4);color:#fca5a5;font-weight:700;border-radius:8px;padding:6px 12px;cursor:pointer;font-size:.85rem;min-height:36px;}' +
      '.eiv-body{padding:18px;}' +
      '.eiv-btn{display:inline-flex;align-items:center;gap:6px;border:none;border-radius:10px;padding:12px 20px;font-weight:800;font-size:.98rem;cursor:pointer;min-height:48px;}' +
      '.eiv-btn.primary{background:linear-gradient(135deg,#a78bfa,#6366f1);color:#fff;}' +
      '.eiv-btn.rec{background:linear-gradient(135deg,#ef4444,#b91c1c);color:#fff;}' +
      '.eiv-btn.ghost{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.18);color:#cbd5e1;}' +
      '.eiv-btn.mini{padding:7px 12px;min-height:36px;font-size:.82rem;border-radius:8px;}' +
      '.eiv-btn:disabled{opacity:.45;cursor:not-allowed;}' +
      '.eiv-note{font-size:.82rem;color:#94a3b8;line-height:1.6;}' +
      '.eiv-card{background:rgba(30,41,59,.6);border:1px solid rgba(148,163,184,.18);border-radius:12px;padding:14px 16px;margin:12px 0;}' +
      '.eiv-storyboard{white-space:pre-wrap;line-height:1.85;font-size:.92rem;}' +
      '.eiv-figure{text-align:center;}' +
      '.eiv-figure img{max-width:100%;max-height:70vh;border-radius:10px;background:#fff;padding:4px;box-shadow:0 4px 18px rgba(0,0,0,.35);}' +
      '.eiv-examiner{display:flex;gap:10px;align-items:flex-start;background:rgba(99,102,241,.10);border:1px solid rgba(99,102,241,.3);border-radius:12px;padding:12px 14px;margin:10px 0;}' +
      '.eiv-examiner .av{font-size:1.6rem;line-height:1;}' +
      '.eiv-examiner .q{font-size:1rem;font-weight:600;line-height:1.6;}' +
      '.eiv-timer{font-variant-numeric:tabular-nums;font-weight:800;font-size:1.5rem;}' +
      '.eiv-bar{height:8px;border-radius:99px;background:rgba(148,163,184,.2);overflow:hidden;margin:8px 0;}' +
      '.eiv-bar>i{display:block;height:100%;background:linear-gradient(90deg,#22c55e,#eab308,#ef4444);transition:width .95s linear;}' +
      '.eiv-steps{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:6px;}' +
      '.eiv-step{font-size:.72rem;padding:3px 9px;border-radius:99px;background:rgba(148,163,184,.15);color:#94a3b8;font-weight:700;}' +
      '.eiv-step.on{background:rgba(167,139,250,.25);color:#c4b5fd;}' +
      '.eiv-step.done{background:rgba(34,197,94,.2);color:#86efac;}' +
      '.eiv-badge{display:inline-block;font-size:.72rem;font-weight:700;padding:2px 8px;border-radius:99px;margin-left:6px;}' +
      '.eiv-badge.g{background:rgba(34,197,94,.18);color:#86efac;}.eiv-badge.y{background:rgba(234,179,8,.18);color:#fde68a;}.eiv-badge.r{background:rgba(239,68,68,.18);color:#fca5a5;}.eiv-badge.n{background:rgba(148,163,184,.18);color:#cbd5e1;}' +
      '.eiv-rev{border-top:1px solid rgba(148,163,184,.15);padding:14px 0;}' +
      '.eiv-rev h4{margin:0 0 8px;font-size:.95rem;color:#c4b5fd;}' +
      '.eiv-model{background:rgba(2,6,23,.4);border-left:3px solid #6366f1;border-radius:8px;padding:10px 12px;margin-top:8px;font-size:.9rem;line-height:1.7;}' +
      '.eiv-tips{font-size:.85rem;color:#cbd5e1;line-height:1.7;margin-top:6px;white-space:pre-wrap;}' +
      '.eiv-audio{width:100%;margin-top:8px;}' +
      '.eiv-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:8px;}' +
      '.eiv-transcript{font-size:.86rem;color:#e2e8f0;background:rgba(2,6,23,.35);border-radius:8px;padding:8px 10px;margin-top:8px;font-style:italic;}' +
      '.eiv-warn{background:rgba(234,179,8,.10);border:1px solid rgba(234,179,8,.35);color:#fde68a;border-radius:10px;padding:10px 12px;font-size:.85rem;line-height:1.6;margin:10px 0;}' +
      '@media(max-width:520px){.eiv-body{padding:14px;}.eiv-btn{width:100%;justify-content:center;}}';
    var st = document.createElement('style'); st.id = 'eiv-style'; st.textContent = css;
    document.head.appendChild(st);
  }

  // ---------- data fetch ----------
  function fetchCard(examId, grade) {
    var params = 'exam=eiken&part=s_interview&eiken_grade=' + encodeURIComponent(grade || 'gp1') + '&limit=1';
    var sid = null;
    try { if (window.AuthGuard && AuthGuard.getStudent) { var st = AuthGuard.getStudent(); sid = st && (st.id || st.student_id); } } catch (e) {}
    if (sid) params += '&student_id=' + encodeURIComponent(sid);
    var tok = getToken();
    var list = bases();
    function tryAt(i) {
      if (i >= list.length) return Promise.resolve(null);
      var ctrl = new AbortController();
      var timer = setTimeout(function () { ctrl.abort(); }, 12000);
      return fetch(list[i] + '/api/exam-questions/bank?' + params, {
        cache: 'no-store', credentials: 'same-origin', signal: ctrl.signal,
        headers: tok ? { Authorization: 'Bearer ' + tok } : {},
      }).then(function (r) {
        clearTimeout(timer);
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      }).then(function (d) {
        if (d && d.selected) return d;
        return tryAt(i + 1);
      }).catch(function () { clearTimeout(timer); return tryAt(i + 1); });
    }
    return tryAt(0);
  }

  // ---------- steps indicator ----------
  function stepsHtml() {
    var labels = S.qs.map(function (q) { return q.label || ''; });
    return '<div class="eiv-steps">' + labels.map(function (l, i) {
      var cls = i < S.idx ? 'done' : (i === S.idx ? 'on' : '');
      return '<span class="eiv-step ' + cls + '">' + esc(l) + '</span>';
    }).join('') + '</div>';
  }

  // ---------- render phases ----------
  function renderIntro() {
    S.phase = 'intro';
    var c = S.card, topic = (c.topic_ja || c.question_data && c.question_data.topic_ja || '');
    var micOk = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
    var stt = sttAvailable();
    contentEl.innerHTML =
      '<div class="eiv-card">' +
      '  <div style="font-weight:800;font-size:1.05rem;margin-bottom:6px;">本番の流れで面接を体験します</div>' +
      '  <div class="eiv-note">テーマ: <b style="color:#e5e7eb;">' + esc(topic || '—') + '</b><br>' +
      '  ① ナレーション(4コマ・1分準備→2分) → ② No.1 → ③ No.2 → ④ No.3 → ⑤ No.4 の順に、面接官の質問に英語で答えます。<br>' +
      '  各設問は面接官が<b>音声で質問</b>し、<b>タイマー</b>が動きます。あなたの回答を<b>録音</b>して後で聴き返せます。</div>' +
      '</div>' +
      (micOk ? '' : '<div class="eiv-warn">⚠️ このブラウザは録音(MediaRecorder)に対応していません。Chrome / Safari / Edge を推奨します。録音なしでも進められます。</div>') +
      (stt ? '' : '<div class="eiv-warn">⚠️ このブラウザ/端末は音声認識に非対応のため、AIの内容採点はできません(録音と模範解答の聴き比べは可能)。Chrome / Edge 推奨。</div>') +
      '<div class="eiv-note" style="margin:10px 0;">🔒 録音はあなたのブラウザ内だけで再生用に保持され、サーバーには送信されません。' +
      '発音は「録音の聴き返し + 模範音声との比較 + AIアドバイス + 認識の明瞭度(目安)」で確認します(音素レベルの認定スコアではありません)。</div>' +
      '<div class="eiv-row">' +
      '  <button class="eiv-btn primary" id="eiv-start">🎬 面接を始める</button>' +
      '  <button class="eiv-btn ghost" id="eiv-cancel">やめる</button>' +
      '</div>';
    contentEl.querySelector('#eiv-start').addEventListener('click', beginInterview);
    contentEl.querySelector('#eiv-cancel').addEventListener('click', closeAll);
  }

  function beginInterview() {
    // マイク許可を先に取得 (録音対応時のみ)
    var micOk = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
    if (!micOk) { S.idx = 0; startQuestion(); return; }
    contentEl.innerHTML = '<div class="eiv-card">🎙 マイクの使用を許可してください…</div>';
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
      S.stream = stream; S.idx = 0; startQuestion();
    }).catch(function () {
      contentEl.innerHTML =
        '<div class="eiv-warn">🎙 マイクが使えませんでした。録音なしで進めます(タイマー・面接官音声・模範解答は利用できます)。</div>' +
        '<button class="eiv-btn primary" id="eiv-nomic">続ける</button>';
      contentEl.querySelector('#eiv-nomic').addEventListener('click', function () { S.stream = null; S.idx = 0; startQuestion(); });
    });
  }

  function startQuestion() {
    stopSpeak();
    var q = S.qs[S.idx];
    if (!q) { renderReview(); return; }
    if ((q.prep_sec || 0) > 0) { renderPrep(q); }
    else { renderAnswer(q); }
  }

  // 4コマイラスト画像 (data URI・無ければ空文字)。data:image/(png|jpeg|jpg|webp);base64 形式のみ許可(XSS防御)。
  function figureHtml() {
    var f = S.card && S.card.figure_b64;
    if (!f || !/^data:image\/(png|jpeg|jpg|webp);base64,[A-Za-z0-9+/=]+$/.test(f)) return '';
    // ★loading="lazy" は付けない: position:fixed オーバーレイ内では intersection observer が
    //   発火せず画像が読み込まれない(8x8 の壊れアイコンになる)。data URI は即時ロードでよい。
    return '<div class="eiv-figure"><img src="' + f + '" alt="4コマイラスト（面接カード）" /></div>';
  }

  function renderPrep(q) {
    S.phase = 'prep';
    var sb = S.card.passage || '';
    var figv = figureHtml();
    contentEl.innerHTML =
      stepsHtml() +
      '<div class="eiv-card"><b>🧠 準備タイム</b> — 4コマを見て、語る内容を英語で考えてください。' +
      '<div class="eiv-note" style="margin-top:4px;">準備が終わったら「話す準備ができた」を押すとすぐナレーションに進めます。</div></div>' +
      (figv ? '<div class="eiv-card">' + figv + '</div>' : '') +
      (sb ? '<div class="eiv-card eiv-storyboard">' + esc(sb) + '</div>' : '') +
      '<div class="eiv-card" style="text-align:center;">' +
      '  <div class="eiv-timer" id="eiv-tm">' + fmt(q.prep_sec) + '</div>' +
      '  <div class="eiv-bar"><i id="eiv-bar" style="width:100%"></i></div>' +
      '  <button class="eiv-btn primary" id="eiv-ready">🎤 話す準備ができた →</button>' +
      '</div>';
    contentEl.querySelector('#eiv-ready').addEventListener('click', function () { clearTimer(); renderAnswer(q); });
    runTimer(q.prep_sec, function () { renderAnswer(q); });
  }

  function renderAnswer(q) {
    S.phase = 'answer';
    stopSpeak();
    var isNarr = q.phase === 'narration';
    var sb = S.card.passage || '';
    var figv = figureHtml();
    var boardInner = figv + (sb ? '<div class="eiv-storyboard" style="margin-top:8px;">' + esc(sb) + '</div>' : '');
    contentEl.innerHTML =
      stepsHtml() +
      '<div class="eiv-examiner"><span class="av">🧑‍🏫</span><div><div class="eiv-note" style="margin-bottom:2px;">面接官 (' + esc(q.label || '') + ')</div>' +
      '<div class="q" id="eiv-qtext">' + esc(q.examiner_say || q.stem || '') + '</div>' +
      '<button class="eiv-btn mini ghost" id="eiv-replayq" style="margin-top:8px;">🔊 質問をもう一度</button></div></div>' +
      (boardInner ? '<details class="eiv-card"' + (isNarr ? ' open' : '') + '><summary style="cursor:pointer;font-weight:700;">🖼 4コマ（イラスト＋説明）を見る</summary><div style="margin-top:8px;">' + boardInner + '</div></details>' : '') +
      '<div class="eiv-card" style="text-align:center;">' +
      '  <div class="eiv-timer" id="eiv-tm">' + fmt(q.answer_sec) + '</div>' +
      '  <div class="eiv-bar"><i id="eiv-bar" style="width:100%"></i></div>' +
      '  <div class="eiv-row" style="justify-content:center;" id="eiv-recctl"></div>' +
      '  <div class="eiv-note" id="eiv-recmsg" style="margin-top:8px;">準備ができたら「録音開始」を押して話してください。</div>' +
      '</div>';
    contentEl.querySelector('#eiv-replayq').addEventListener('click', function () { speak(q.examiner_say || q.stem || ''); });
    renderRecCtl(q, false);
    // 面接官が質問を読み上げてから待機 (タイマーは録音開始で始動)
    speak(q.examiner_say || q.stem || '');
  }

  function renderRecCtl(q, recorded) {
    var box = contentEl.querySelector('#eiv-recctl');
    var msg = contentEl.querySelector('#eiv-recmsg');
    if (!box) return;
    var micOk = !!(S.stream && window.MediaRecorder);
    if (!S.recording && !recorded) {
      box.innerHTML = (micOk ? '<button class="eiv-btn rec" id="eiv-rec">🔴 録音開始</button>' : '') +
        '<button class="eiv-btn ghost" id="eiv-skip">' + (micOk ? '録音せず次へ →' : '次へ →') + '</button>';
      if (micOk) box.querySelector('#eiv-rec').addEventListener('click', function () { beginRecording(q); });
      box.querySelector('#eiv-skip').addEventListener('click', function () { clearTimer(); nextQuestion(); });
    } else if (S.recording) {
      box.innerHTML = '<button class="eiv-btn rec" id="eiv-stop">⏹ 録音停止</button>';
      box.querySelector('#eiv-stop').addEventListener('click', function () { finishRecording(q); });
      if (msg) msg.innerHTML = '🔴 録音中… 英語で話してください。';
    } else if (recorded) {
      var a = S.answers[S.idx];
      box.innerHTML =
        (a && a.url ? '<audio class="eiv-audio" controls src="' + a.url + '"></audio>' : '') +
        '<div class="eiv-row" style="justify-content:center;">' +
        '<button class="eiv-btn ghost mini" id="eiv-redo">🔁 録り直す</button>' +
        '<button class="eiv-btn primary" id="eiv-next">' + (S.idx >= S.qs.length - 1 ? '結果を見る →' : '次の質問へ →') + '</button>' +
        '</div>';
      box.querySelector('#eiv-redo').addEventListener('click', function () {
        var old = S.answers[S.idx]; if (old && old.url) { try { URL.revokeObjectURL(old.url); } catch (e) {} }
        S.answers[S.idx] = null; renderAnswer(q);
      });
      box.querySelector('#eiv-next').addEventListener('click', function () { nextQuestion(); });
      if (msg) msg.innerHTML = a && a.transcript ? '✅ 録音完了。下で聴き返せます。' : '✅ 録音完了。';
    }
  }

  function beginRecording(q) {
    S.recording = true; S.chunks = []; S.curTranscript = ''; S.curConf = 0; S.curConfN = 0;
    try {
      var opt = pickMime();
      S.rec = new MediaRecorder(S.stream, opt);
      S.rec.ondataavailable = function (e) { if (e.data && e.data.size) S.chunks.push(e.data); };
      S.rec.onstop = function () {
        S.recording = false;
        if (!overlay || !contentEl) return;  // 録音中に閉じられたら blob を作らず終了 (取りこぼし防止)
        var mime = (S.rec && S.rec.mimeType) || 'audio/webm';
        var blob = new Blob(S.chunks, { type: mime });
        var url = URL.createObjectURL(blob);
        S.answers[S.idx] = {
          url: url, mime: mime,
          transcript: (S.curTranscript || '').trim(),
          confidence: S.curConfN ? (S.curConf / S.curConfN) : null,
          label: q.label, examiner: q.examiner_say || q.stem, model: q.answer, tips: q.explanation,
        };
        renderRecCtl(q, true);
      };
      S.rec.start();
    } catch (e) {
      // MediaRecorder 起動失敗 → 録音なし。STT/タイマーは始動せず、案内して「次へ」で進めるようにする
      S.recording = false; S.rec = null;
      var msg = contentEl && contentEl.querySelector('#eiv-recmsg');
      if (msg) msg.innerHTML = '⚠️ 録音を開始できませんでした。「次へ」で進めます。';
      renderRecCtl(q, false);
      return;
    }
    // STT (best-effort・録音と並行)
    startSTT();
    // タイマー始動 (回答時間)
    runTimer(q.answer_sec, function () { finishRecording(q); });
    renderRecCtl(q, false);
  }

  function startSTT() {
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    try {
      var r = new SR();
      r.lang = 'en-US'; r.continuous = true; r.interimResults = false;
      r.onresult = function (e) {
        for (var i = e.resultIndex; i < e.results.length; i++) {
          var res = e.results[i];
          if (res.isFinal) {
            S.curTranscript += res[0].transcript + ' ';
            if (typeof res[0].confidence === 'number' && res[0].confidence > 0) { S.curConf += res[0].confidence; S.curConfN++; }
          }
        }
      };
      r.onerror = function () {};
      S.recognition = r; r.start();
    } catch (e) {}
  }

  function finishRecording(q) {
    clearTimer();
    try { if (S.recognition) S.recognition.stop(); } catch (e) {}
    S.recognition = null;
    try { if (S.rec && S.rec.state !== 'inactive') S.rec.stop(); else { S.recording = false; renderRecCtl(q, true); } } catch (e) { S.recording = false; renderRecCtl(q, true); }
  }

  function nextQuestion() { clearTimer(); stopSpeak(); S.idx++; startQuestion(); }

  function pickMime() {
    var cand = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/mpeg', 'audio/ogg'];
    for (var i = 0; i < cand.length; i++) {
      try { if (window.MediaRecorder && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(cand[i])) return { mimeType: cand[i] }; } catch (e) {}
    }
    return {};
  }

  // ---------- timer ----------
  function runTimer(sec, onEnd) {
    clearTimer();
    S.remain = sec;
    var tm = contentEl.querySelector('#eiv-tm'), bar = contentEl.querySelector('#eiv-bar');
    if (tm) tm.textContent = fmt(S.remain);
    S.timer = setInterval(function () {
      S.remain--;
      var t = contentEl.querySelector('#eiv-tm'), b = contentEl.querySelector('#eiv-bar');
      if (t) t.textContent = fmt(Math.max(0, S.remain));
      if (b) b.style.width = Math.max(0, (S.remain / sec) * 100) + '%';
      if (S.remain <= 0) { clearTimer(); if (onEnd) onEnd(); }
    }, 1000);
  }
  function clearTimer() { if (S.timer) { clearInterval(S.timer); S.timer = null; } }

  // ---------- review ----------
  function confBadge(a) {
    if (a.confidence == null) return '<span class="eiv-badge n">明瞭度: —</span>';
    var pct = Math.round(a.confidence * 100);
    var cls = pct >= 80 ? 'g' : (pct >= 60 ? 'y' : 'r');
    return '<span class="eiv-badge ' + cls + '">認識明瞭度(目安): ' + pct + '%</span>';
  }
  function renderReview() {
    S.phase = 'review'; cleanupMicOnly(); stopSpeak();
    var anyTranscript = S.answers.some(function (a) { return a && a.transcript; });
    var html = '<div class="eiv-card"><b>🎉 面接おつかれさまでした</b><div class="eiv-note" style="margin-top:4px;">各設問で「自分の録音の聴き返し」「模範解答の音声」「AIの採点・発音アドバイス」を確認できます。</div></div>';
    if (!anyTranscript) {
      html += '<div class="eiv-warn">この端末は音声認識が使えないため、AIの内容採点は行えません。録音の聴き返しと模範解答(🔊)の聴き比べで練習してください。</div>';
    } else {
      var tok = getToken();
      html += '<div class="eiv-row"><button class="eiv-btn primary" id="eiv-score"' + (tok ? '' : ' disabled title="採点にはログインが必要です"') + '>🤖 AIに面接を採点してもらう</button>' +
        (tok ? '' : '<span class="eiv-note">(採点にはログインが必要です)</span>') + '</div>' +
        '<div id="eiv-scorebox"></div>';
    }
    S.qs.forEach(function (q, i) {
      var a = S.answers[i] || {};
      html += '<div class="eiv-rev"><h4>' + esc(q.label || ('Q' + (i + 1))) + ' ' + (a.confidence != null ? confBadge(a) : '') + '</h4>' +
        '<div class="eiv-note">面接官: ' + esc(q.examiner_say || q.stem || '') + ' <button class="eiv-btn mini ghost" data-say="' + esc(q.examiner_say || q.stem || '') + '">🔊</button></div>' +
        (a.url ? '<audio class="eiv-audio" controls src="' + a.url + '"></audio>' : '<div class="eiv-note" style="margin-top:6px;">(録音なし)</div>') +
        (a.transcript ? '<div class="eiv-transcript">あなたの発話(認識): ' + esc(a.transcript) + '</div>' : '') +
        '<div class="eiv-model"><b>模範解答</b> <button class="eiv-btn mini ghost" data-say="' + esc(q.answer || '') + '">🔊 聴く</button><br>' + esc(q.answer || '') + '</div>' +
        (q.explanation ? '<div class="eiv-tips">💡 ' + esc(q.explanation) + '</div>' : '') +
        '</div>';
    });
    html += '<div class="eiv-row" style="margin-top:14px;"><button class="eiv-btn ghost" id="eiv-again">🔁 別のカードでもう一度</button><button class="eiv-btn ghost" id="eiv-fin">終了</button></div>';
    contentEl.innerHTML = html;
    // wire TTS play buttons
    Array.prototype.forEach.call(contentEl.querySelectorAll('button[data-say]'), function (b) {
      b.addEventListener('click', function () { speak(b.getAttribute('data-say')); });
    });
    var sc = contentEl.querySelector('#eiv-score'); if (sc) sc.addEventListener('click', scoreInterview);
    contentEl.querySelector('#eiv-again').addEventListener('click', function () { restart(); });
    contentEl.querySelector('#eiv-fin').addEventListener('click', closeAll);
  }
  function cleanupMicOnly() {
    clearTimer();
    try { if (S.rec && S.rec.state !== 'inactive') S.rec.stop(); } catch (e) {}
    try { if (S.recognition) S.recognition.stop(); } catch (e) {}
    try { if (S.stream) S.stream.getTracks().forEach(function (t) { t.stop(); }); } catch (e) {}
    S.rec = null; S.recognition = null; S.stream = null; S.recording = false;
  }

  function restart() {
    (S.answers || []).forEach(function (a) { if (a && a.url) { try { URL.revokeObjectURL(a.url); } catch (e) {} } });
    S.answers = []; S.idx = 0;
    if (!contentEl) return;
    contentEl.innerHTML = '<div class="eiv-card">🔄 次のカードを読み込み中…</div>';
    fetchCard(S.examId, S.grade).then(function (data) {
      if (!contentEl) return;
      if (data && data.selected) {
        S.card = normalizeCard(data.selected);
        S.qs = S.card.qs; S.idx = 0; S.answers = [];  // ★S.qs も必ず更新 (旧カードの設問が残る不整合を防ぐ)
        if (!S.qs.length) {
          contentEl.innerHTML = '<div class="eiv-warn">面接カードの中身が空でした。</div><button class="eiv-btn ghost" id="eiv-cl2">閉じる</button>';
          var b = contentEl.querySelector('#eiv-cl2'); if (b) b.addEventListener('click', closeAll);
          return;
        }
        renderIntro();
      } else { renderIntro(); }
    });
  }

  // ---------- AI scoring ----------
  function scoreInterview() {
    var box = contentEl.querySelector('#eiv-scorebox');
    var btn = contentEl.querySelector('#eiv-score');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ 採点中… (10〜20秒)'; }
    if (box) box.innerHTML = '';
    var lines = S.qs.map(function (q, i) {
      var a = S.answers[i] || {};
      return '【' + (q.label || ('Q' + (i + 1))) + '】\n面接官の質問: ' + (q.examiner_say || q.stem || '') +
        '\n受験者の回答(音声認識・誤認識含む可能性あり): ' + (a.transcript || '(認識できず/無回答)') +
        '\n模範解答: ' + (q.answer || '');
    }).join('\n\n');
    var system = 'あなたは英検準1級 二次試験(面接)のベテラン面接委員です。受験者の各回答(音声認識テキスト)を、英検の観点(ナレーション=展開/文法・語彙/情報量、質疑=応答内容/文法・語彙/情報量、アティチュード=積極性)で評価します。' +
      '音声認識テキストは誤認識を含み得るので、明らかな認識ミスは大目に見て内容本位で評価してください。発音の細部は音声から判定できないため、テキストや典型的な日本人学習者の傾向から推測できる「言い回し・強勢・つながり」の助言に留めます。出力は必ず日本語で、指定のJSONのみ。';
    var user = '以下の面接を採点し、次のJSON形式だけで返してください(前置き・コードフェンス不要):\n' +
      '{"overall":"総評(2-3文)","estimate":"目安(合格圏/あと一歩/要強化 のいずれか+一言)",' +
      '"items":[{"label":"ナレーション","good":"良かった点","improve":"改善点(具体的に)"}, ... No.1〜No.4も],' +
      '"pronunciation":["発音・言い回し・強勢のアドバイス(日本語・2〜4個)"],' +
      '"vocab_grammar":["文法・語彙で伸ばせる点(2〜4個)"]}\n\n' +
      '=== 面接記録 ===\n' + lines;
    aiCall(system, user).then(function (txt) {
      var obj = parseJson(txt);
      if (btn) { btn.disabled = false; btn.textContent = '🤖 もう一度採点する'; }
      if (!obj) { if (box) box.innerHTML = '<div class="eiv-warn">採点結果を読み取れませんでした。もう一度お試しください。</div>'; return; }
      renderScore(box, obj);
    }).catch(function (e) {
      if (btn) { btn.disabled = false; btn.textContent = '🤖 AIに面接を採点してもらう'; }
      // ★プランの制限 (403) を「通信環境を確認して」と回線のせいにしない。押しても永久に直らない。
      var _em = (e && e.message) || 'エラー';
      var _isPlan = /^PLAN_BLOCKED:/.test(_em);
      _em = _em.replace(/^PLAN_BLOCKED:/, '');
      if (box) box.innerHTML = _isPlan
        ? '<div class="eiv-warn">' + esc(_em) + '</div>'
        : '<div class="eiv-warn">採点に失敗しました(' + esc(_em) + ')。通信環境を確認してもう一度お試しください。</div>';
    });
  }
  function renderScore(box, o) {
    if (!box) return;
    var h = '<div class="eiv-card" style="border-color:rgba(167,139,250,.4);">' +
      '<div style="font-weight:800;color:#c4b5fd;margin-bottom:6px;">🤖 AI 採点結果 ' + (o.estimate ? '<span class="eiv-badge g">' + esc(o.estimate) + '</span>' : '') + '</div>' +
      '<div class="eiv-tips">' + esc(o.overall || '') + '</div>';
    if (Array.isArray(o.items)) {
      h += '<div style="margin-top:10px;">' + o.items.map(function (it) {
        return '<div style="margin:8px 0;"><b>' + esc(it.label || '') + '</b>' +
          (it.good ? '<div class="eiv-tips">✅ ' + esc(it.good) + '</div>' : '') +
          (it.improve ? '<div class="eiv-tips">🔧 ' + esc(it.improve) + '</div>' : '') + '</div>';
      }).join('') + '</div>';
    }
    if (Array.isArray(o.pronunciation) && o.pronunciation.length) {
      h += '<div style="margin-top:10px;"><b>🗣 発音・言い回し</b><ul class="eiv-tips" style="margin:4px 0 0;padding-left:1.2em;">' +
        o.pronunciation.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul></div>';
    }
    if (Array.isArray(o.vocab_grammar) && o.vocab_grammar.length) {
      h += '<div style="margin-top:10px;"><b>📘 文法・語彙</b><ul class="eiv-tips" style="margin:4px 0 0;padding-left:1.2em;">' +
        o.vocab_grammar.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul></div>';
    }
    h += '<div class="eiv-note" style="margin-top:10px;">※ 発音は録音の聴き返し・模範音声(🔊)との比較で確認してください。音素レベルの認定スコアではありません。</div></div>';
    box.innerHTML = h;
  }
  function aiCall(system, user) {
    var tok = getToken();
    if (!tok) return Promise.reject(new Error('未ログイン'));
    var list = bases();
    var body = JSON.stringify({ model: 'claude-sonnet-4-6', max_tokens: 2800, system: system, messages: [{ role: 'user', content: user }] });
    function tryAt(i, lastErr) {
      if (i >= list.length) return Promise.reject(lastErr || new Error('AI 失敗'));
      var ctrl = new AbortController();
      var timer = setTimeout(function () { ctrl.abort(); }, 45000);
      return fetch(list[i] + '/api/ai/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + tok },
        body: body, signal: ctrl.signal,
      }).then(function (r) {
        clearTimeout(timer);
        // ★403/429 はプランの制限/上限。サーバの日本語説明を出す ('AI 403' は生徒に意味不明)。
        if (!r.ok) {
          if (r.status === 403 || r.status === 429) {
            return r.text().then(function (t) {
              var d = '';
              try { d = String((JSON.parse(t) || {}).detail || ''); } catch (_) { d = ''; }
              // ★403 と 429 を同じ文言にしない。一過性の 429 (混雑・edge) まで
              //   「プランで使えません」と言うと、払っている生徒に契約の問題だと誤解させる。
              //   プラン由来の上限はサーバが AI_BUDGET_ 接頭辞を付けてくるので、それで見分ける。
              var _isPlanLimit = /^AI_BUDGET_[A-Z0-9_]+:/.test(String(d || ''));
              if (r.status === 429 && !_isPlanLimit) {
                throw new Error('ただいま混み合っています。少し時間をおいてから、もう一度お試しください。');
              }
              // ★marker を付ける。受け側が日本語本文で判定すると、将来この経路に
              //   日次トークン上限 (本文に「上限」が入る) が乗った瞬間に、
              //   一時的に当たっただけの有料生徒へ「プランでは使えません」と言ってしまう。
              throw new Error('PLAN_BLOCKED:' + (d ? String(d).replace(/^AI_BUDGET_[A-Z0-9_]+:/, '')
                                                  : 'この機能は現在のプランではご利用いただけません。'));
            });
          }
          throw new Error('AI ' + r.status);
        }
        return r.json();
      }).then(function (data) {
        var c = data && data.content;
        if (Array.isArray(c)) return c.map(function (b) { return b && b.text ? b.text : ''; }).join('');
        return (data && (data.text || data.completion)) || '';
      }).catch(function (e) { clearTimeout(timer); return tryAt(i + 1, e); });
    }
    return tryAt(0, null);
  }
  function parseJson(txt) {
    if (!txt) return null;
    var s = String(txt).replace(/```json|```/g, '').trim();
    try { return JSON.parse(s); } catch (e) {}
    var m = s.match(/\{[\s\S]*\}/);
    if (m) { try { return JSON.parse(m[0]); } catch (e) {} }
    return null;
  }

  // ---------- normalize ----------
  function normalizeCard(sel) {
    var qd = sel.question_data || sel;
    var qs = (qd.questions || sel.questions || []).map(function (q) {
      return {
        label: q.label || '', phase: q.phase || '', prep_sec: q.prep_sec || 0, answer_sec: q.answer_sec || 60,
        examiner_say: q.examiner_say || q.stem || '', stem: q.stem || '', answer: q.answer || '', explanation: q.explanation || '',
      };
    });
    return {
      passage: qd.passage || sel.passage || '', prompt: qd.prompt || '', topic_ja: qd.topic_ja || '',
      figure_b64: qd.figure_b64 || sel.figure_b64 || '',
      question_data: qd, qs: qs,
    };
  }

  // ---------- entry ----------
  window.startEikenInterview = function (opts) {
    opts = opts || {};
    S.examId = opts.examId || 'eiken';
    S.grade = opts.eikenGrade || opts.grade || 'gp1';
    ensureOverlay();
    contentEl.innerHTML = '<div class="eiv-card">📚 面接カードを読み込み中…</div>';
    fetchCard(S.examId, S.grade).then(function (data) {
      if (!contentEl) return;  // ロード中に閉じられた場合の null 参照防止
      if (!data || !data.selected) {
        contentEl.innerHTML = '<div class="eiv-warn">まだ面接カードが用意されていません。少し時間をおいてお試しください。</div>' +
          '<button class="eiv-btn ghost" id="eiv-cl">閉じる</button>';
        contentEl.querySelector('#eiv-cl').addEventListener('click', closeAll);
        return;
      }
      var card = normalizeCard(data.selected);
      S.card = card; S.qs = card.qs; S.idx = 0; S.answers = [];
      if (!S.qs.length) {
        contentEl.innerHTML = '<div class="eiv-warn">面接カードの中身が空でした。</div><button class="eiv-btn ghost" id="eiv-cl">閉じる</button>';
        contentEl.querySelector('#eiv-cl').addEventListener('click', closeAll);
        return;
      }
      renderIntro();
    });
  };
})();
