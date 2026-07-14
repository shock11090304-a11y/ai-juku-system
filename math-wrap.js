// math-wrap.js — 区切り忘れの「生」数式を KaTeX に載せる共有ヘルパ (2026-07-14)
// ---------------------------------------------------------------------------
// AI が数式区切り (\( \) / $ $) を付け忘れて書いた素の数式 —
//   不等号の素 Unicode (≥ ≦ ≧ ≦ ≠ √) や裸の LaTeX コマンド (\geq \dfrac 等) —
// は KaTeX auto-render が拾えず「\geq」やフォント未収録記号のまま表示される。
// これを描画直前に \(...\) で包んで renderMathInElement (自前フォント) に載せる。
//
// canonical ロジック = app.js の _wrapBareMath。app.js は単一 $ を delimiter に持つので
// $...$ で包むが、learning-brain.js / mock-exam.js 等は通貨 $ 誤組版回避で単一 $ を
// delimiter に持たない。そこでこの共有版は **どの画面の delimiter 設定でも描画される
// \(...\) で包む**。全 KaTeX 描画面 (SRS カード / 模試 / 英語試験 / 文法ドリル 等) で
// renderMathInElement の直前に window.wrapBareMath(rootEl) を呼ぶだけで横展開できる。
//
// 安全性: code/pre/kbd/samp/.katex・既に区切り済み ($ や \( や \[ を含む) text node は不変。
//   frac/sqrt/binom を正規表現先頭に置く単一パスで、引数内の \pi 等を二重ラップしない。
(function () {
  if (typeof window.wrapBareMath === 'function') return; // 二重定義防止 (複数画面が同居しても1つ)

  // 引数なしの関係記号・ギリシャ文字・演算子コマンド (長い prefix を先に=最長一致)。
  var NOARG = /\\(?:geqq|leqq|geqslant|leqslant|geq|leq|neqq|neq|equiv|approx|simeq|cong|propto|fallingdotseq|times|div|cdot|pm|mp|to|longrightarrow|rightarrow|leftarrow|Rightarrow|Leftrightarrow|iff|implies|mapsto|infty|angle|perp|parallel|notin|subseteq|subset|supseteq|supset|cup|cap|emptyset|varnothing|forall|exists|therefore|because|partial|nabla|alpha|beta|gamma|delta|varepsilon|epsilon|zeta|eta|vartheta|theta|iota|kappa|lambda|mu|nu|xi|varpi|pi|varrho|rho|varsigma|sigma|tau|upsilon|varphi|phi|chi|psi|omega|Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega|ldots|cdots|dots|circ|prime|le|ge|ne|in)(?![a-zA-Z])/;
  var BRACE = '\\{(?:[^{}]|\\{[^{}]*\\})*\\}'; // 1段ネストまで丸取り
  var TOKEN = new RegExp(
    '\\\\(?:d|t)?frac\\s*' + BRACE + '\\s*' + BRACE +
    '|\\\\binom\\s*' + BRACE + '\\s*' + BRACE +
    '|\\\\sqrt\\s*(?:\\[[^\\]]*\\])?\\s*' + BRACE +
    '|' + NOARG.source +
    '|√\\d+' +
    '|[≦≧≤≥≠≒≈±∞]',
    'g');
  var UMAP = {
    '≦': '\\leqq', '≧': '\\geqq', '≤': '\\leq', '≥': '\\geq',
    '≠': '\\neq', '≒': '\\fallingdotseq', '≈': '\\approx',
    '±': '\\pm', '∞': '\\infty'
  };
  function toLatex(m) {
    if (m.charAt(0) === '\\') return m;                       // 既に LaTeX コマンド/frac/sqrt
    if (m.charAt(0) === '√') return '\\sqrt{' + m.slice(1) + '}'; // √5 → \sqrt{5}
    return UMAP[m] || m;                                      // 素 Unicode 記号 → LaTeX
  }

  window.wrapBareMath = function (container) {
    if (!container || typeof document.createTreeWalker !== 'function' || !window.NodeFilter) return;
    var walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        var p = node.parentNode;
        while (p && p !== container) {
          var tag = (p.tagName || '').toLowerCase();
          if (tag === 'code' || tag === 'pre' || tag === 'kbd' || tag === 'samp') return NodeFilter.FILTER_REJECT;
          if (p.classList && (p.classList.contains('katex') || p.classList.contains('katex-display') || p.classList.contains('katex-html'))) return NodeFilter.FILTER_REJECT;
          p = p.parentNode;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var nodes = [], n;
    while ((n = walker.nextNode())) nodes.push(n);
    nodes.forEach(function (node) {
      var o = node.nodeValue;
      if (!o || o.length < 2) return;
      // 既に区切りを含む text node は触らない (通貨 $ / 既存 \( \[ を保護)
      if (o.indexOf('$') >= 0 || o.indexOf('\\(') >= 0 || o.indexOf('\\[') >= 0) return;
      var t = o.replace(TOKEN, function (m) { return '\\(' + toLatex(m) + '\\)'; });
      if (t !== o) node.nodeValue = t;
    });
  };
})();
