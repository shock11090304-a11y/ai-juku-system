/* 📚 PDF教材ページの表示と計測 (2026-10-07)
 * 商品データは materials-data.js (window.MATERIALS / MATERIALS_STORES)。ここには商品固有の文言を書かない。
 * 計測は既存の POST /api/track (events テーブル) に送る。名前は 3 つ + 一覧表示:
 *   materials_list_view {}                         一覧を開いた
 *   material_detail_view {id}                      詳細を開いた
 *   material_sample_click {id, from, type}         無料見本を押した (from: list / detail / bar)
 *   material_buy_click {id, store, from}           購入先へ移動するボタンを押した (★購入完了・売上ではない)
 * 本番ドメイン以外 (ローカルのプレビューなど) では送らず console に出すだけ。
 * 2026-10-18: 見出し画像 (image)・演習回数 (rounds)・重複の注意 (overlap / compare)・印刷 (printing)・教材ごとの利用条件 (terms) に対応。
 *   重複の注意は、カードでも詳細でも購入ボタンより前に出す。見本の無い教材は、カードの 2 つ目のボタンを購入にする。
 * 2026-10-18 (2 回目): 同じ教科に見出し画像のある教材と無い教材が混ざったので、画像の有無で格子を分ける (gridsHtml)。
 */
(function () {
  'use strict';
  var ITEMS = window.MATERIALS || [];
  var STORES = window.MATERIALS_STORES || {};
  var SUBJECTS = window.MATERIALS_SUBJECTS || [];
  var TERMS = window.MATERIALS_COMMON_TERMS || [];

  /* ---------- 計測 ---------- */
  var PROD_HOSTS = { 'trillion-ai-juku.com': 1, 'www.trillion-ai-juku.com': 1 };
  function sessionId() {
    try {
      var s = sessionStorage.getItem('aj_session_id');
      if (!s) { s = 's_' + Math.random().toString(36).slice(2, 10); sessionStorage.setItem('aj_session_id', s); }
      return s;
    } catch (e) { return null; }
  }
  function track(name, props) {
    props = props || {};
    props.page = location.pathname;
    if (!PROD_HOSTS[location.hostname]) { if (window.console) console.debug('[track:preview]', name, props); return; }
    try {
      fetch('/api/track', {
        method: 'POST', keepalive: true,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, props: props, session_id: sessionId() })
      }).catch(function () {});
    } catch (e) {}
  }

  /* ---------- 共通 ---------- */
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function yen(n) { return Number(n).toLocaleString('ja-JP'); }
  function isHttps(u) { return typeof u === 'string' && /^https:\/\/[^\s"'<>]+$/.test(u); }
  function storeOf(m) { var s = STORES[m.store]; return s && s.ready ? s : null; }
  // 購入ボタンを有効にしてよいか。1 つでも確認できない項目があれば「販売準備中」
  function canBuy(m) {
    return m.status === 'on_sale' && Number.isInteger(m.price) && m.price > 0 && isHttps(m.buyUrl) && !!storeOf(m);
  }
  function sampleOk(m) {
    var s = m.sample;
    if (!s || !s.url) return false;
    if (s.type === 'pdf') return /^materials\/samples\/[a-z0-9-]+\.pdf$/.test(s.url);
    return isHttps(s.url);
  }
  function sampleLabel(m) {
    var s = m.sample;
    if (s.type === 'pdf') return '無料見本を見る（' + s.pages + 'ページ）';
    return s.label || '無料部分を読む';
  }
  function sampleShort(m) {
    if (m.sample && m.sample.short) return m.sample.short;
    return m.sample && m.sample.type === 'pdf' ? '無料見本（PDF）' : '無料部分を読む';
  }
  // 見出し画像はリポジトリ内の materials/images/ だけ (外部 URL・購入者用ファイルを指させない)
  function imageOk(m) { return !!(m.image && /^materials\/images\/[a-z0-9-]+\.png$/.test(m.image.src || '')); }
  // 重複・再収録の注意。カードでも詳細でも、購入ボタンより前に置く (一覧と詳細で同じ m.overlap を使う)
  function overlapHtml(m, h) {
    if (!m.overlap || !m.overlap.length) return '';
    var cmp = (m.compare || []).filter(function (c) {
      return c && c.label && (isHttps(c.href) || /^material\.html\?id=[a-z0-9-]+$/.test(c.href || ''));
    }).map(function (c) {
      var ext = isHttps(c.href);
      return '<a class="inline-link' + (ext ? ' ext' : '') + '" href="' + esc(c.href) + '"' + (ext ? ' target="_blank" rel="noopener"' : '') + '>' +
        esc(c.label) + (ext ? '<span class="sr-only">（新しいタブで開きます）</span>' : '') + '</a>';
    });
    return '<div class="overlap"><' + h + ' class="ov-h">重複のご注意</' + h + '>' + list(m.overlap, 'ov-list') +
      (cmp.length ? '<p class="ov-cmp">' + cmp.join('') + '</p>' : '') + '</div>';
  }
  function sampleAttrs(m, from) {
    var s = m.sample;
    var ext = s.type !== 'pdf';
    return 'href="' + esc(s.url) + '" target="_blank" rel="noopener"' +
      ' data-track="sample" data-id="' + esc(m.id) + '" data-from="' + from + '"' +
      (ext ? '' : ' type="application/pdf"');
  }
  function buyHtml(m, from, cls) {
    cls = cls || 'btn btn-gold';
    if (!canBuy(m)) {
      return '<span class="' + cls + '" aria-disabled="true">販売準備中</span>';
    }
    var st = storeOf(m);
    return '<a class="' + cls + ' ext" href="' + esc(m.buyUrl) + '" target="_blank" rel="noopener"' +
      ' data-track="buy" data-id="' + esc(m.id) + '" data-store="' + esc(m.store) + '" data-from="' + from + '">' +
      esc(st.buyLabel) + '<span class="sr-only">' + (from === 'list' ? '：' + esc(m.name) : '') + '（新しいタブで開きます）</span></a>';
  }
  function statusHtml(m) {
    return canBuy(m)
      ? '<span class="status on">販売中・' + esc(storeOf(m).name) + '</span>'
      : '<span class="status prep">販売準備中</span>';
  }
  function priceHtml(m) {
    if (!(Number.isInteger(m.price) && m.price > 0)) return '<span class="price" style="font-size:1rem">価格未定</span>';
    return '<span class="price">' + yen(m.price) + '円<small>（税込）</small></span>';
  }
  function detailUrl(m) { return 'material.html?id=' + encodeURIComponent(m.id); }
  function list(items, cls) {
    if (!items || !items.length) return '';
    return '<ul class="' + (cls || 'dots') + '">' + items.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>';
  }

  // クリック計測 (一覧・詳細・下部バー共通)
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('[data-track]');
    if (!a || a.getAttribute('aria-disabled') === 'true') return;
    var id = a.getAttribute('data-id');
    var from = a.getAttribute('data-from') || '';
    if (a.getAttribute('data-track') === 'sample') {
      var m = ITEMS.filter(function (x) { return x.id === id; })[0];
      track('material_sample_click', { id: id, from: from, type: m && m.sample ? m.sample.type : '' });
    } else if (a.getAttribute('data-track') === 'buy') {
      track('material_buy_click', { id: id, store: a.getAttribute('data-store'), from: from });
    }
  });

  /* ---------- 一覧ページ ---------- */
  // h: 商品名の見出しの段 (一覧は教科の見出し h3 の下なので h4、詳細の「ほかの教材」は h3)
  function cardHtml(m, h) {
    h = h === 'h4' ? 'h4' : 'h3';
    // 2 つ目のボタン: 無料見本があれば見本、無ければ購入 (見本の無い教材に「見本」のボタンを出さない)
    var second = sampleOk(m)
      ? '<a class="btn btn-ink" ' + sampleAttrs(m, 'list') + '>' + esc(sampleShort(m)) + '</a>'
      : buyHtml(m, 'list');
    // 画像は直下の見出しと同じ商品名なので、読み上げは見出しに任せる (alt="")。同じ詳細へのリンクはタブ移動から外す
    var thumb = imageOk(m)
      ? '<a class="thumb" href="' + detailUrl(m) + '" tabindex="-1" aria-hidden="true"><img src="' + esc(m.image.src) + '" alt="" width="1280" height="670" loading="lazy" decoding="async"></a>'
      : '';
    return '<article class="mcard" data-subject="' + esc(m.subject) + '">' + thumb +
      '<div class="top">' +
        '<div class="tags"><span class="tag subj">' + esc(m.subject) + '</span><span class="tag lvl">' + esc(m.level) + '</span></div>' +
        '<' + h + ' class="mt"><a href="' + detailUrl(m) + '">' + esc(m.name) + '</a></' + h + '>' +
        (m.rounds ? '<p class="rounds"><span class="k">演習</span>' + esc(m.rounds) + '</p>' : '') +
        '<p class="purpose">' + esc(m.purpose) + '</p>' +
        (m.format ? '<p class="fmt">' + esc(m.format) + '</p>' : '') +
        overlapHtml(m, h === 'h4' ? 'h5' : 'h4') +
      '</div>' +
      '<div class="bottom">' +
        '<div class="price-row">' + priceHtml(m) + statusHtml(m) + '</div>' +
        '<div class="card-actions">' +
          '<a class="btn btn-navy" href="' + detailUrl(m) + '">詳しく見る<span class="sr-only">：' + esc(m.name) + '</span></a>' +
          second +
        '</div>' +
      '</div>' +
    '</article>';
  }
  // カードの格子。見出し画像のあるカードと無いカードは同じ格子に入れない (同じ行に並ぶと、無いカードが画像の高さだけ間延びする)。
  // 並びはデータの順のまま、画像の有無が切り替わるところで格子を分ける
  function gridsHtml(items, h) {
    var runs = [];
    items.forEach(function (m) {
      var last = runs[runs.length - 1];
      if (last && imageOk(last[0]) === imageOk(m)) last.push(m); else runs.push([m]);
    });
    return runs.map(function (r) {
      return '<div class="mgrid">' + r.map(function (m) { return cardHtml(m, h); }).join('') + '</div>';
    }).join('');
  }

  function initList(root) {
    var filtersEl = document.getElementById('filters');
    var noteEl = document.getElementById('resultNote');
    var subjects = SUBJECTS.filter(function (s) { return ITEMS.some(function (m) { return m.subject === s; }); });
    ITEMS.forEach(function (m) { if (subjects.indexOf(m.subject) < 0) subjects.push(m.subject); });
    var current = 'all';
    try {
      var q = new URLSearchParams(location.search).get('subject');
      if (q && subjects.indexOf(q) >= 0) current = q;
    } catch (e) {}

    // 教科ごとに見出しと格子を分ける (見出し画像のあるカードと無いカードが同じ行に並んで、空白だらけの行にならないように)
    function render() {
      var shown = ITEMS.filter(function (m) { return current === 'all' || m.subject === current; });
      var groups = (current === 'all' ? subjects : [current]).map(function (s, i) {
        var items = shown.filter(function (m) { return m.subject === s; });
        if (!items.length) return '';
        return '<section class="mgroup" aria-labelledby="mg-' + i + '">' +
          '<h3 class="mgroup-h" id="mg-' + i + '">' + esc(s) + '<span class="cnt">' + items.length + '点</span></h3>' +
          gridsHtml(items, 'h4') + '</section>';
      }).join('');
      root.innerHTML = shown.length ? groups : '<p class="empty">この教科の教材は準備中です。</p>';
      noteEl.textContent = (current === 'all' ? 'すべての教科' : current) + '：' + shown.length + '点';
      [].forEach.call(filtersEl.querySelectorAll('button'), function (b) {
        b.setAttribute('aria-pressed', b.getAttribute('data-subject') === current ? 'true' : 'false');
      });
    }
    var btns = [{ key: 'all', label: 'すべて', n: ITEMS.length }].concat(subjects.map(function (s) {
      return { key: s, label: s, n: ITEMS.filter(function (m) { return m.subject === s; }).length };
    }));
    filtersEl.innerHTML = btns.map(function (b) {
      return '<button type="button" data-subject="' + esc(b.key) + '" aria-pressed="false">' + esc(b.label) + '<span class="cnt">' + b.n + '</span></button>';
    }).join('');
    filtersEl.addEventListener('click', function (e) {
      var b = e.target.closest('button');
      if (!b) return;
      current = b.getAttribute('data-subject');
      render();
      try {
        var u = new URL(location.href);
        if (current === 'all') u.searchParams.delete('subject'); else u.searchParams.set('subject', current);
        history.replaceState(null, '', u.pathname + u.search + u.hash);
      } catch (err) {}
    });
    render();
    track('materials_list_view', {});
  }

  /* ---------- 詳細ページ ---------- */
  function initDetail(root) {
    var id = '';
    try { id = new URLSearchParams(location.search).get('id') || ''; } catch (e) {}
    var m = ITEMS.filter(function (x) { return x.id === id; })[0];
    var hero = document.getElementById('detailHero');
    if (!m) {
      document.title = '教材が見つかりません｜Trillion English Academy';
      hero.innerHTML = '<div class="crumbs"><a href="academy.html">塾のご案内</a> ／ <a href="materials.html">PDF教材</a></div><h1>教材が見つかりませんでした</h1>';
      root.innerHTML = '<div class="wrap notfound"><p>リンクが古いか、掲載を終えた教材の可能性があります。</p><a class="btn btn-navy" href="materials.html">教材の一覧へ</a></div>';
      return;
    }
    document.title = m.name + '｜PDF教材｜Trillion English Academy';
    var md = document.querySelector('meta[name="description"]');
    if (md) md.setAttribute('content', m.purpose);

    var st = storeOf(m);
    var hasSample = sampleOk(m);
    hero.innerHTML =
      '<div class="crumbs"><a href="academy.html">塾のご案内</a> ／ <a href="materials.html">PDF教材</a> ／ <a href="materials.html?subject=' + encodeURIComponent(m.subject) + '">' + esc(m.subject) + '</a></div>' +
      '<div class="d-hero">' +
        '<div>' +
          '<div class="tags"><span class="tag subj">' + esc(m.subject) + '</span><span class="tag lvl">' + esc(m.level) + '</span></div>' +
          '<h1>' + esc(m.name) + '</h1>' +
          (imageOk(m) ? '<img class="d-cover" src="' + esc(m.image.src) + '" alt="' + esc(m.image.alt || m.name) + '" width="1280" height="670" decoding="async">' : '') +
          '<p class="lede">' + esc(m.purpose) + '</p>' +
          (m.disclaimer ? '<p class="disclaimer">' + esc(m.disclaimer) + '</p>' : '') +
          (m.storeTitle ? '<p class="store-title">販売ページでの商品名：' + esc(m.storeTitle) + '</p>' : '') +
        '</div>' +
        '<aside class="buybox" aria-label="価格と購入">' +
          '<div class="row">' + priceHtml(m) + statusHtml(m) + '</div>' +
          (m.rounds ? '<p class="rounds"><span class="k">演習</span>' + esc(m.rounds) + '</p>' : '') +
          overlapHtml(m, 'h2') +
          '<div class="acts">' +
            (hasSample ? '<a class="btn btn-ink" ' + sampleAttrs(m, 'detail') + '>' + esc(sampleLabel(m)) + '</a>' : '') +
            buyHtml(m, 'detail') +
          '</div>' +
          '<div class="meta">' +
            (m.format ? '<div><b>形式</b>：' + esc(m.format) + '</div>' : '') +
            (canBuy(m) ? '<div>お支払いと教材のお渡しは ' + esc(st.name) + ' で行います。</div>' : '<div>販売の準備ができしだい、このページでご案内します。</div>') +
          '</div>' +
        '</aside>' +
      '</div>';

    var html = '';
    // 無料見本
    if (hasSample) {
      var prev = '';
      if (m.sample.type === 'pdf' && m.previews && m.previews.length) {
        prev = '<div class="previews">' + m.previews.map(function (p) {
          return '<figure><a ' + sampleAttrs(m, 'preview') + '><img src="materials/previews/' + esc(m.id) + '-p' + p + '.jpg" width="640" height="906" loading="lazy" alt="無料見本 ' + p + 'ページ目の画像"></a><figcaption>無料見本 ' + p + 'ページ目</figcaption></figure>';
        }).join('') + '</div>';
      }
      html += '<section class="sec" id="sample"><div class="wrap">' +
        '<div class="sec-head"><h2>購入前に、無料見本で中身を確かめてください</h2></div>' +
        '<div class="sample-box"><div class="desc"><p>' + esc(m.sample.desc) + '</p>' +
          (m.sample.type === 'pdf' ? '<p style="margin-top:.6rem;font-size:.85rem">PDF・' + m.sample.pages + 'ページ（' + esc(m.sample.size) + '）。販売ページで無料公開しているものと同じファイルです。</p>' : '') +
          '<div class="acts"><a class="btn btn-ink" ' + sampleAttrs(m, 'detail') + '>' + esc(sampleLabel(m)) + '</a></div>' +
        '</div>' + prev + '</div>' +
      '</div></section>';
    }
    // 中身
    var blocks = '';
    if (m.worries && m.worries.length) blocks += '<div class="block"><h2>こんな悩みに</h2>' + list(m.worries, 'dots worry') + '</div>';
    if (m.target && m.target.length) blocks += '<div class="block"><h2>対象・レベル</h2><p style="margin-bottom:.5rem"><b style="color:var(--navy)">' + esc(m.level) + '</b></p>' + list(m.target) + '</div>';
    if (m.learn && m.learn.length) blocks += '<div class="block"><h2>学べること</h2>' + list(m.learn) + '</div>';
    if (m.howto && m.howto.length) blocks += '<div class="block"><h2>使い方</h2><ol>' + m.howto.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ol></div>';
    if (m.contents && m.contents.length) blocks += '<div class="block wide"><h2>収録内容</h2>' + list(m.contents) + (m.format ? '<p class="fine"><b>形式</b>：' + esc(m.format) + '</p>' : '') + '</div>';
    if (m.printing) blocks += '<div class="block wide"><h2>印刷について</h2><p>' + esc(m.printing) + '</p></div>';
    var notes = (m.excludes ? [m.excludes] : []).concat(m.notes || []);
    if (notes.length) blocks += '<div class="block wide"><h2>購入前にご確認ください</h2>' + list(notes) + '</div>';
    html += '<section class="sec alt"><div class="wrap"><div class="blocks">' + blocks + '</div></div></section>';

    // 受け取り方・利用条件・問い合わせ
    var recv = canBuy(m) ? list(st.receive) : '<p>販売の準備ができしだい、購入先と受け取り方をこのページでご案内します。</p>';
    html += '<section class="sec" id="receive"><div class="wrap"><div class="blocks">' +
      '<div class="block"><h2>購入と受け取りの流れ</h2>' + recv + '</div>' +
      '<div class="block"><h2>ご利用について</h2>' + list(m.terms && m.terms.length ? m.terms : TERMS) + '</div>' +
      '<div class="block wide"><h2>お問い合わせ</h2><p>教材の内容や、授業・塾での利用についてのご相談は、公式 LINE（<a class="inline-link" href="https://lin.ee/ZHlrRjh" target="_blank" rel="noopener">友だち追加</a>）またはメール（<a class="inline-link" href="mailto:info@trillion-ai-juku.com">info@trillion-ai-juku.com</a>）へどうぞ。' +
        (canBuy(m) && m.store === 'note' ? '決済やダウンロードの不具合は、<a class="inline-link" href="https://www.help-note.com/hc/ja" target="_blank" rel="noopener">noteのヘルプセンター</a>もご確認ください。' : '') + '</p></div>' +
    '</div></div></section>';

    // 同じ教科のほかの教材
    var rel = ITEMS.filter(function (x) { return x.subject === m.subject && x.id !== m.id; });
    if (rel.length) {
      html += '<section class="sec alt"><div class="wrap"><div class="sec-head"><h2>' + esc(m.subject) + 'のほかの教材</h2></div>' + gridsHtml(rel, 'h3') +
        '<p style="margin-top:1.4rem"><a class="inline-link" href="materials.html">すべての教材を見る</a></p></div></section>';
    }
    root.innerHTML = html;

    // スマホ下部の購入バー
    var bar = document.getElementById('buybar');
    if (bar) {
      bar.innerHTML = '<span class="bp">' + (Number.isInteger(m.price) ? yen(m.price) + '円<small>税込</small>' : '') + '</span>' +
        (hasSample ? '<a class="btn btn-ink" ' + sampleAttrs(m, 'bar') + '>' + esc(sampleShort(m)) + '</a>' : '') +
        buyHtml(m, 'bar');
      var showBar = function () { bar.removeAttribute('hidden'); document.body.classList.add('has-buybar'); };
      // 重複の注意がある教材は、注意の全文がバーより上に見えてから下部バーを出す (注意より先に購入ボタンを見せない)。
      // 見張るのは注意の直後のボタン列。下 120px (バーの高さ＋iPhone の下端の余白) を除いた範囲に入ったら、注意は全部バーの上にある。
      // 開いた時点でもう通り過ぎている (再読み込みでスクロール位置が戻る・#receive へ直接飛ぶ) ときもすぐ出す。
      // IntersectionObserver は「画面の下の外 → 上の外」へ一瞬で飛ぶと通知が来ない (#receive への直接移動・視差効果を減らす設定の本文へ移動) ので、
      // スクロールのたびにボタン列の位置を見る (出したら外す)
      var gate = m.overlap && m.overlap.length ? hero.querySelector('.buybox .acts') : null;
      if (gate) {
        var check = function () {
          if (gate.getBoundingClientRect().top < window.innerHeight - 120) {
            showBar();
            window.removeEventListener('scroll', check);
            window.removeEventListener('resize', check);
          }
        };
        window.addEventListener('scroll', check, { passive: true });
        window.addEventListener('resize', check);
        check();
      } else {
        showBar();
      }
    }
    track('material_detail_view', { id: m.id });
  }

  /* ---------- 起動 ---------- */
  var listRoot = document.getElementById('materialsList');
  var detailRoot = document.getElementById('materialDetail');
  if (listRoot) initList(listRoot);
  if (detailRoot) initDetail(detailRoot);

  // モバイルメニュー: リンクを押したら閉じる / 外側クリックで閉じる (academy.html と同じ)
  var menu = document.querySelector('.m-menu');
  if (menu) {
    menu.querySelectorAll('.m-panel a').forEach(function (a) { a.addEventListener('click', function () { menu.removeAttribute('open'); }); });
    document.addEventListener('click', function (e) { if (menu.hasAttribute('open') && !menu.contains(e.target)) menu.removeAttribute('open'); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && menu.hasAttribute('open')) { menu.removeAttribute('open'); menu.querySelector('summary').focus(); } });
  }
})();
