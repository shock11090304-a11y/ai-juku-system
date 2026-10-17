#!/usr/bin/env python3
"""📊 本文の表 (取込仕様 docs/drill-import-spec.md §2 の「［表］」+「｜」) を画面で <table> にする規則を、実際の JS エンジンで動かして確かめる。

背景 (2026-10-17 塾長「アプリ側で表を直しておいて」): 長文型ドリル (英語長文・習熟度テスト・英検の長文など) の本文は、
  エスケープした文字を white-space:pre-wrap でそのまま出していたので、表の書き方「［表］」の行と「｜」区切りの行が生のまま見えた。
  375px のスマホでは本文カードが 約 309px (塾生アプリ class.html)・約 270px (マイページ) しかなく、行が折り返して列がずれる。
  → 「［表］」の塊を本物の <table> (1 行目 = 見出し <th>) にし、横スクロールの箱 (overflow-x:auto) に入れ、セルは折り返さない。

続き (2026-10-17 塾長「今日の復習カードの表も直しておいて」): マイページの「🔁 今日の復習」(learning-brain.js renderTodayReview) は、
  長文型ドリルのカードの problem に「【本文】\n」+ 生の本文を持つ (mypage.js が保存。保存する形は変えない) ので、表が生のまま見えていた。
  → 描くときに直す (今あるカードも直る): pre-wrap の箱 (「… 全文を見る」・「📝 解いてみる」の問題文・解答と解説の「… 全文を見る」) は
  _lbPassageTables で <table>、1 行の短い表示 (先頭 100 字・解答 300 字・解説 500 字) は _lbTablesInline で表を 1 行の文字にしてから切る。

固定する性質 (class.html の gdPassageTables / mypage.js と ceo.html の _gdPassageTables / learning-brain.js の _lbPassageTables):
  [1] class.html: 表になる (見出し・行・セルの数)・「［表］」の行が消える・表の HTML に改行が無い・表の前後の改行の数
      (「［表］」の行の分の空行を残さない・表の直後の改行 1 つは表が吸う)・XSS (エスケープが先・本文がタグや属性にならない)・
      空所「( 1 )」の黄色は表の中でも外でも効く・表の無い本文は今までと 1 文字も変わらない (変更前の関数と比べる)・列の数が
      そろわない行 (空のセルで埋める)・本文の最後の表・表 2 つ (間に文 / 続けて)・半角 | は表にしない・全訳 (body_ja) の表
  [2] mypage.js: 同じ性質を _gdPassageBlock で
  [3] ceo.html: 👀 問題を見る の本文 (const bodyHtml = … の式をソースから取り出して動かす)・全訳と 📊 分析の 📖 本文の呼び出し
  [4] 4 つのファイルが同じ入力に同じ表の構造 (タグと中身。属性 = 見た目だけ違う) を返す (learning-brain はマイページと見た目も同じ)
  [5] 構文 (new Function): class.html の inline script・mypage.js・ceo.html の inline script・learning-brain.js
  [6] ソース検査: CSS (横スクロール・折り返さない・枠線)・呼び出し箇所・mypage.js / learning-brain.js の ?v=・ceo.js を触っていない前提の確認・
      mypage.js が保存するカードの形を変えていない・今日の復習を描くのはマイページ (暗い画面) だけ・CI 登録
  [7] learning-brain.js: _lbTablesInline (表を 1 行の文字に)・本物の learning-brain.js をまるごと偽の window / document / localStorage で
      動かし、renderTodayReview の HTML で 「… 全文を見る」・「📝 解いてみる」の問題文・解答と解説の全文が表になる (【本文】の行はそのまま)・
      短い表示は表を作らず「［表］」「｜」・タグの切れ端を出さない (表の途中で切れても)・XSS・表の HTML に改行が無い・選択肢と正解は今までどおり・
      表の無いカードは変更前 (呼び出しを外した learning-brain.js) と 1 文字も変わらない

★JS エンジンが無ければ FAIL (飛ばさない)。CI (ubuntu) は node、塾長の Mac は osascript -l JavaScript (node は無い)。
  AJ_JS_ENGINE=node|osascript|jsc で選べる。本文はすべて架空 (取込前のテストの本文をリポジトリに入れない)。

実行:
    python3 scripts/health_check/test_passage_table_render.py
    # exit 0 = PASS / 1 = FAIL
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
CLASS_HTML = os.path.join(REPO, "class.html")
MYPAGE_HTML = os.path.join(REPO, "mypage.html")
MYPAGE_JS = os.path.join(REPO, "mypage.js")
CEO_HTML = os.path.join(REPO, "ceo.html")
LB_JS = os.path.join(REPO, "learning-brain.js")
CI_YML = os.path.join(REPO, ".github", "workflows", "server-tests.yml")
JSC = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc"

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def js_engine():
    want = os.environ.get("AJ_JS_ENGINE", "").strip()
    cands = {
        "node": ["node"] if shutil.which("node") else None,
        "osascript": ["osascript", "-l", "JavaScript"] if shutil.which("osascript") else None,
        "jsc": [JSC] if os.path.exists(JSC) else None,
    }
    if want:
        return cands.get(want)
    for k in ("node", "osascript", "jsc"):
        if cands[k]:
            return cands[k]
    return None


def inline_scripts(html):
    out = []
    for m in re.finditer(r"<script(\s[^>]*)?>(.*?)</script>", html, re.S):
        attrs = m.group(1) or ""
        if "src=" in attrs:
            continue
        if "type=" in attrs and "javascript" not in attrs:
            continue
        out.append(m.group(2))
    return out


def extract_fn(src, name, indent, label):
    """`{indent}function {name}(` で始まる関数を 1 つだけ取り出す (波かっこを数える。対象の関数の文字列に片方だけの { } は無い)。"""
    starts = [m.start() for m in re.finditer(r"^" + re.escape(indent) + r"function " + re.escape(name) + r"\(", src, re.M)]
    check(f"{label}: function {name}( がちょうど 1 つ", len(starts) == 1, len(starts))
    if len(starts) != 1:
        return None
    i = src.index("{", starts[0])
    depth = 0
    for j in range(i, len(src)):
        c = src[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[starts[0]:j + 1]
    check(f"{label}: function {name} の終わりが見つかる", False)
    return None


# 結果の書き出し (node は console.log = stdout、osascript は console.log = stderr、jsc は print)。OK / NG / DONE の行だけを読む
PRELUDE = r"""
var __out = [];
function __j(v) { try { return JSON.stringify(v); } catch (e) { return String(v); } }
function eq(label, got, want) { var ok = __j(got) === __j(want); __out.push((ok ? 'OK  ' : 'NG  ') + label + (ok ? '' : ' => ' + __j(got) + ' (want ' + __j(want) + ')')); }
function ok(label, cond, detail) { __out.push((cond ? 'OK  ' : 'NG  ') + label + (cond || detail === undefined ? '' : ' => ' + __j(detail))); }
function __emit() {
  var s = __out.join('\n') + '\nDONE ' + __out.length;
  if (typeof process !== 'undefined' && typeof console !== 'undefined' && console.log) console.log(s);
  else if (typeof print === 'function') print(s);
  else if (typeof console !== 'undefined' && console.log) console.log(s);
}
"""

# 変更前 (2d00f62) の本文カードの関数をそのまま写したもの。表の無い本文はこれと 1 文字も変わらないことを見る
OLD_CLASS = r"""
function gdPassageHtml_OLD(p, review) {
  if (!p) return '';
  var body = esc(p.body || '').replace(/\(\s*(\d{1,2})\s*\)/g, '<span class="gd-blank">( $1 )</span>');
  var ja = (review && p.body_ja) ? '<details><summary>📖 全訳を見る</summary><div class="gd-ja">' + esc(p.body_ja) + '</div></details>' : '';
  return '<div class="gd-passage gd-nomath">' + (p.title ? '<div class="gd-ptitle">📖 ' + esc(p.title) + '</div>' : '') + body + ja + '</div>';
}
"""
OLD_MYPAGE = r"""
function _gdPassageBlock_OLD(p, review) {
  if (!p) return '';
  const body = _gdEscape(p.body || '').replace(/\(\s*(\d{1,2})\s*\)/g, '<span style="font-weight:800; color:#fde68a;">( $1 )</span>');
  const ja = (review && p.body_ja)
    ? `<details style="margin-top:8px;"><summary style="cursor:pointer; color:#a5b4fc; font-size:0.8rem;">📖 全訳を見る</summary><div style="margin-top:6px; color:#cbd5e1; font-size:0.86rem; line-height:1.7; white-space:pre-wrap;">${_gdEscape(p.body_ja)}</div></details>`
    : '';
  const title = p.title ? `<div style="font-weight:800; color:#c7d2fe; margin-bottom:6px; font-size:0.9rem;">📖 ${_gdEscape(p.title)}</div>` : '';
  return '<div class="gd-nomath" style="padding:14px 16px; background:rgba(129,140,248,0.07); border:1px solid rgba(129,140,248,0.32); border-radius:12px; margin:4px 0 12px; font-size:0.93rem; line-height:1.8; color:#e2e8f0; white-space:pre-wrap; word-break:break-word;">'
    + title + body + ja + '</div>';
}
"""
OLD_CEO = r"""
function previewBody_OLD(p) { return escapeHtml(p.body || '').replace(/\(\s*(\d{1,2})\s*\)/g, '<span style="font-weight:800;color:#fde68a;">( $1 )</span>'); }
"""

# 架空の本文 (英語の掲示・時刻表のような表)。取込前のテストの本文は使わない
CASES = r"""
var BL = /\(\s*(\d{1,2})\s*\)/g;
var CB = function (s) { return s.replace(BL, '<span class="gd-blank">( $1 )</span>'); };   // class.html の空所
function norm(s) { return String(s).replace(/<([a-z]+)\b[^>]*>/g, '<$1>'); }   // 属性 (見た目) を外した構造
function tables(s) { return String(s).match(/<div[^>]*><table[\s\S]*?<\/table><\/div>/g) || []; }
function count(s, sub) { return String(s).split(sub).length - 1; }
function openTags(s) { var m = String(s).match(/<[a-z][^>]*>/g) || [], o = {}; m.forEach(function (t) { o[t] = 1; }); return Object.keys(o).sort(); }
function rowsCells(tableHtml) {   // 行ごとの [th の数, td の数]
  return (tableHtml.match(/<tr>[\s\S]*?<\/tr>/g) || []).map(function (tr) { return [count(tr, '<th'), count(tr, '<td')]; });
}
var T = function (h, rows) {   // class.html の表の期待値
  var th = '<tr>' + h.map(function (c) { return '<th>' + c + '</th>'; }).join('') + '</tr>';
  var tb = rows.map(function (r) { return '<tr>' + r.map(function (c) { return '<td>' + c + '</td>'; }).join('') + '</tr>'; }).join('');
  return '<div class="gd-table-wrap"><table class="gd-table"><thead>' + th + '</thead>' + (rows.length ? '<tbody>' + tb + '</tbody>' : '') + '</table></div>';
};

var FX_BASIC = 'Read the notice.\n\n［表］\nDay｜Open｜Close\nMon ( 1 )｜9:00｜17:00\nSat｜10:00｜15:00\n\nThe hall ( 2 ) on Sunday.';
var FX_TIGHT = 'Para one.\n［表］\nItem｜Price\nTea｜$3\nNext line.';
var FX_END = 'Prices are below.\n\n［表］\nSize｜Cost\nS｜100\nL｜200';
var FX_END_NL = 'Prices are below.\n\n［表］\nSize｜Cost\nS｜100\nL｜200\n';
var FX_TWO = 'First.\n\n［表］\nA｜B\n1｜2\n\nMiddle ( 3 ).\n\n［表］\nC｜D\n3｜4\n';
var FX_ADJ = '［表］\nA｜B\n1｜2\n［表］\nC｜D\n3｜4';
var FX_RAGGED = 'x\n［表］\nA｜B｜C\n1｜2\n3｜4｜5｜6\ny';
var FX_HEADONLY = '［表］\nA｜B\nafter';
var FX_SPACES = 'x\n  ［表］ \n　Room　｜ Seats \n Hall A ｜ 120\ny';
var FX_CRLF = 'x\r\n［表］\r\nA｜B\r\n1｜2\r\n\r\ny';
var FX_XSS = 'Intro <script>alert(x)</script> & "q" ( 1 )\n［表］\nName｜Note <img src=x onerror=alert(x)>\n"a" & <b>b</b>｜</td><script>x()</script>\n\nAfter <i>it</i> & ( 2 )';
var FX_BENIGN = 'Intro and q ( 1 )\n［表］\nName｜Note\na and b｜x\n\nAfter it ( 2 )';

// 表の無い本文 (表にしないもの) = 今までと 1 文字も変わらない
var NO_TABLE = [
  '',
  'Plain text only.',
  'One ( 1 ) two ( 2 ).\n\n[1] Second paragraph ( 3 ).',
  'A｜B written outside a table\n1｜2',
  'x\n［表］\nA|B\n1|2',                  // 半角 | は表にしない
  '| A | B |\n|---|---|\n| 1 | 2 |',      // Markdown の表も表にしない
  'See ［表］ in the middle of a line\nA｜B',  // 「［表］」だけの行ではない
  'x\n［表］\ny\nz',                       // 「［表］」の下に ｜ の行が無い
  'x\n［表］',                             // 本文の最後が「［表］」
  'x\n[表]\nA｜B\n1｜2',                   // 半角の角かっこ
  'Tom & "Jerry" <b>bold</b> \'s ( 1 )',
  'x\r\ny ( 1 )\r\n\r\nz',
  '\n\nlead and trail\n\n'
];
"""

CASES_CLASS = r"""
(function () {
  var L = 'class.html: ';
  var H = function (body, review, ja, title) { return C.passage({ title: title || '', body: body, body_ja: ja }, review); };
  var W0 = '<div class="gd-passage gd-nomath">';
  // 表になる・見出し・行・セル・「［表］」が消える・空所は表の中でも外でも
  var out = H(FX_BASIC, false, '', 'Notice');
  eq(L + '表になる (見出し 3・行 2・空所は表の中と外)', out, W0 + '<div class="gd-ptitle">📖 Notice</div>' + 'Read the notice.\n\n'
    + T(['Day', 'Open', 'Close'], [['Mon <span class="gd-blank">( 1 )</span>', '9:00', '17:00'], ['Sat', '10:00', '15:00']])
    + '\nThe hall <span class="gd-blank">( 2 )</span> on Sunday.</div>');
  ok(L + '「［表］」の行が消える', out.indexOf('［表］') < 0 && out.indexOf('｜') < 0, out);
  eq(L + '見出しは <th> 3 つ・行は <td> 3 つ × 2', rowsCells(tables(out)[0] || ''), [[3, 0], [0, 3], [0, 3]]);
  ok(L + '表の HTML に改行・タブ・字下げが無い', tables(out).length === 1 && tables(out).every(function (t) { return !/[\n\r\t]/.test(t) && !/>\s+</.test(t); }), tables(out));
  // 前後の改行: 「［表］」の行の分の空行を残さない・表の直後の改行 1 つは表が吸う
  eq(L + '空行の無い表 = 前の行の改行だけ・後ろは表の直後に次の行', C.tables(C.esc(FX_TIGHT)), 'Para one.\n' + T(['Item', 'Price'], [['Tea', '$3']]) + 'Next line.');
  eq(L + '本文の最後の表', C.tables(C.esc(FX_END)), 'Prices are below.\n\n' + T(['Size', 'Cost'], [['S', '100'], ['L', '200']]));
  eq(L + '本文の最後の表 (最後に改行)', C.tables(C.esc(FX_END_NL)), 'Prices are below.\n\n' + T(['Size', 'Cost'], [['S', '100'], ['L', '200']]));
  eq(L + '表 2 つ (間に文)', C.tables(CB(C.esc(FX_TWO))), 'First.\n\n' + T(['A', 'B'], [['1', '2']]) + '\nMiddle <span class="gd-blank">( 3 )</span>.\n\n' + T(['C', 'D'], [['3', '4']]));
  eq(L + '表 2 つ (続けて = 間に改行を入れない)', C.tables(C.esc(FX_ADJ)), T(['A', 'B'], [['1', '2']]) + T(['C', 'D'], [['3', '4']]));
  eq(L + '列の数がそろわない行は空のセルで埋める (いちばん多い行に合わせる)', C.tables(C.esc(FX_RAGGED)),
    'x\n' + T(['A', 'B', 'C', ''], [['1', '2', '', ''], ['3', '4', '5', '6']]) + 'y');
  eq(L + '見出しだけの表 (tbody なし)', C.tables(C.esc(FX_HEADONLY)), T(['A', 'B'], []) + 'after');
  eq(L + '「［表］」の前後の空白・セルの前後の空白 (全角も) は外す', C.tables(C.esc(FX_SPACES)), 'x\n' + T(['Room', 'Seats'], [['Hall A', '120']]) + 'y');
  var crlf = C.tables(C.esc(FX_CRLF));
  eq(L + 'CRLF の本文も表になる (表の中に \\r を残さない)', crlf, 'x\r\n' + T(['A', 'B'], [['1', '2']]) + '\r\ny');
  // XSS: エスケープが先。本文はタグにも属性にもならない
  var x = H(FX_XSS, true, FX_XSS, 'T');
  ok(L + 'XSS: <script> / <img> / <b> / <i> がタグにならない', !/<script|<img|<b>|<i>/i.test(x), x);
  ok(L + 'XSS: &lt;script&gt;・&amp;・&quot; にエスケープされる', x.indexOf('&lt;script&gt;alert(x)&lt;/script&gt;') >= 0 && x.indexOf('&amp;') >= 0 && x.indexOf('&quot;q&quot;') >= 0, x);
  ok(L + 'XSS: セルの中の </td> で列が増えない (2 列 × 2 行)', JSON.stringify(rowsCells(tables(x)[0] || '')) === '[[2,0],[0,2]]', rowsCells(tables(x)[0] || ''));
  var bt = openTags(H(FX_BENIGN, true, FX_BENIGN, 'T'));
  ok(L + 'XSS: 出るタグ (属性つき) は害の無い本文と同じものだけ', openTags(x).every(function (t) { return bt.indexOf(t) >= 0; }), [openTags(x), bt]);
  ok(L + '空所の黄色は本文の表の外で効く・全訳には付けない (今までどおり)', count(x, '<span class="gd-blank">( 1 )</span>') === 1 && count(x, '<span class="gd-blank">( 2 )</span>') === 1
    && x.indexOf('<div class="gd-ja">Intro &lt;script&gt;alert(x)&lt;/script&gt; &amp; &quot;q&quot; ( 1 )\n') >= 0, x);
  // 全訳 (body_ja) の表は完了後だけ・同じ表になる
  var r = H('No table here.', true, '訳です。\n\n［表］\n曜日｜時間\n月｜9時\n\n以上。', '');
  eq(L + '全訳 (body_ja) の表も <table> になる', r, W0 + 'No table here.<details><summary>📖 全訳を見る</summary><div class="gd-ja">訳です。\n\n'
    + T(['曜日', '時間'], [['月', '9時']]) + '\n以上。</div></details></div>');
  ok(L + '解く前 (review=false) は全訳を出さない (今までどおり)', H('a', false, '［表］\nA｜B\n1｜2', '').indexOf('全訳') < 0);
  // 表の無い本文は変更前と 1 文字も変わらない (review の有無・全訳つき)
  var same = NO_TABLE.every(function (b) {
    return [true, false].every(function (rv) {
      var p = { title: 'T', body: b, body_ja: b ? (b + ' (ja)') : '' };
      return C.passage(p, rv) === C.passageOld(p, rv) && C.tables(C.esc(b)) === C.esc(b);
    });
  });
  ok(L + '表の無い本文 (半角 |・行の途中の［表］・中身の無い［表］・CRLF など ' + NO_TABLE.length + ' 本) は変更前と同じ', same,
    NO_TABLE.filter(function (b) { return C.passage({ body: b }, false) !== C.passageOld({ body: b }, false); }));
  eq(L + '本文が無い (p = null) ときは空', C.passage(null, true), '');
})();
"""

CASES_MYPAGE = r"""
(function () {
  var L = 'mypage.js: ';
  var out = M.passage({ title: 'Notice', body: FX_BASIC, body_ja: '' }, false);
  ok(L + '表になる・「［表］」の行が消える', tables(out).length === 1 && out.indexOf('［表］') < 0 && out.indexOf('｜') < 0, out);
  eq(L + '見出しは <th> 3 つ・行は <td> 3 つ × 2', rowsCells(tables(out)[0] || ''), [[3, 0], [0, 3], [0, 3]]);
  ok(L + '表の HTML に改行・タブ・字下げが無い', tables(out).every(function (t) { return !/[\n\r\t]/.test(t) && !/>\s+</.test(t); }), tables(out));
  ok(L + '空所の黄色は表の中でも外でも', count(out, '<span style="font-weight:800; color:#fde68a;">( 1 )</span></td>') === 1
    && count(out, '<span style="font-weight:800; color:#fde68a;">( 2 )</span> on Sunday.') === 1, out);
  var t0 = tables(out)[0] || '';
  ok(L + '横スクロールの箱 (overflow-x:auto) に入れる', /^<div style="[^"]*overflow-x:auto/.test(t0), t0.slice(0, 160));
  ok(L + 'セルは折り返さない・枠線あり', count(t0, 'white-space:nowrap') === 9 && count(t0, 'border:1px solid') === 9, t0);
  eq(L + '前後の改行 (class.html と同じ)', norm(M.tables(M.esc(FX_BASIC))), norm(C.tables(C.esc(FX_BASIC))));
  var x = M.passage({ title: 'T', body: FX_XSS, body_ja: FX_XSS }, true);
  ok(L + 'XSS: <script> / <img> / <b> / <i> がタグにならない', !/<script|<img|<b>|<i>/i.test(x), x);
  ok(L + 'XSS: &lt;script&gt;・&amp;・&quot; にエスケープされる', x.indexOf('&lt;script&gt;alert(x)&lt;/script&gt;') >= 0 && x.indexOf('&amp;') >= 0 && x.indexOf('&quot;q&quot;') >= 0, x);
  ok(L + 'XSS: セルの中の </td> で列が増えない (2 列 × 2 行)', JSON.stringify(rowsCells(tables(x)[0] || '')) === '[[2,0],[0,2]]', rowsCells(tables(x)[0] || ''));
  var bt = openTags(M.passage({ title: 'T', body: FX_BENIGN, body_ja: FX_BENIGN }, true));
  ok(L + 'XSS: 出るタグ (属性つき) は害の無い本文と同じものだけ', openTags(x).every(function (t) { return bt.indexOf(t) >= 0; }), [openTags(x), bt]);
  var r = M.passage({ title: '', body: 'No table here.', body_ja: '訳です。\n\n［表］\n曜日｜時間\n月｜9時\n\n以上。' }, true);
  ok(L + '全訳 (body_ja) の表も <table> になる', tables(r).length === 1 && r.indexOf('［表］') < 0 && r.indexOf('<th style') >= 0, r);
  var same = NO_TABLE.every(function (b) {
    return [true, false].every(function (rv) {
      var p = { title: 'T', body: b, body_ja: b ? (b + ' (ja)') : '' };
      return M.passage(p, rv) === M.passageOld(p, rv) && M.tables(M.esc(b)) === M.esc(b);
    });
  });
  ok(L + '表の無い本文 (' + NO_TABLE.length + ' 本) は変更前と同じ', same,
    NO_TABLE.filter(function (b) { return M.passage({ body: b }, false) !== M.passageOld({ body: b }, false); }));
  eq(L + '本文が無い (p = null) ときは空', M.passage(null, true), '');
})();
"""

CASES_CEO = r"""
(function () {
  var L = 'ceo.html: ';
  var out = E.previewBody({ body: FX_BASIC });
  ok(L + '👀 問題を見る の本文が表になる・「［表］」の行が消える', tables(out).length === 1 && out.indexOf('［表］') < 0 && out.indexOf('｜') < 0, out);
  eq(L + '見出しは <th> 3 つ・行は <td> 3 つ × 2', rowsCells(tables(out)[0] || ''), [[3, 0], [0, 3], [0, 3]]);
  ok(L + '表の HTML に改行・タブ・字下げが無い', tables(out).every(function (t) { return !/[\n\r\t]/.test(t) && !/>\s+</.test(t); }), tables(out));
  ok(L + '空所の黄色は表の中でも外でも', count(out, '<span style="font-weight:800;color:#fde68a;">( 1 )</span></td>') === 1
    && count(out, '<span style="font-weight:800;color:#fde68a;">( 2 )</span> on Sunday.') === 1, out);
  var t0 = tables(out)[0] || '';
  ok(L + '横スクロールの箱 (overflow-x:auto)・セルは折り返さない・枠線あり', /^<div style="[^"]*overflow-x:auto/.test(t0)
    && count(t0, 'white-space:nowrap') === 9 && count(t0, 'border:1px solid') === 9, t0);
  var x = E.previewBody({ body: FX_XSS });
  ok(L + 'XSS: <script> / <img> / <b> / <i> がタグにならない', !/<script|<img|<b>|<i>/i.test(x), x);
  ok(L + 'XSS: &lt;script&gt;・&amp;・&quot; にエスケープされる', x.indexOf('&lt;script&gt;alert(x)&lt;/script&gt;') >= 0 && x.indexOf('&amp;') >= 0 && x.indexOf('&quot;q&quot;') >= 0, x);
  ok(L + 'XSS: セルの中の </td> で列が増えない (2 列 × 2 行)', JSON.stringify(rowsCells(tables(x)[0] || '')) === '[[2,0],[0,2]]', rowsCells(tables(x)[0] || ''));
  var bt = openTags(E.previewBody({ body: FX_BENIGN }));
  ok(L + 'XSS: 出るタグ (属性つき) は害の無い本文と同じものだけ', openTags(x).every(function (t) { return bt.indexOf(t) >= 0; }), [openTags(x), bt]);
  ok(L + '表の無い本文 (' + NO_TABLE.length + ' 本) は変更前と同じ (👀 本文・全訳と 📊 分析の本文の式)', NO_TABLE.every(function (b) {
    return E.previewBody({ body: b }) === E.previewBodyOld({ body: b }) && E.tables(E.esc(b)) === E.esc(b);
  }), NO_TABLE.filter(function (b) { return E.previewBody({ body: b }) !== E.previewBodyOld({ body: b }); }));
})();
"""

CASES_LB_UNIT = r"""
(function () {
  var L = 'learning-brain.js: ';
  // _lbPassageTables (pre-wrap の箱) = マイページと同じ表
  var out = B.tables(C.esc(FX_BASIC));
  ok(L + '表になる・「［表］」の行が消える', tables(out).length === 1 && out.indexOf('［表］') < 0 && out.indexOf('｜') < 0, out);
  eq(L + '見出しは <th> 3 つ・行は <td> 3 つ × 2', rowsCells(tables(out)[0] || ''), [[3, 0], [0, 3], [0, 3]]);
  var t0 = tables(out)[0] || '';
  ok(L + '横スクロールの箱 (overflow-x:auto)・セルは折り返さない・枠線あり', /^<div style="[^"]*overflow-x:auto/.test(t0)
    && count(t0, 'white-space:nowrap') === 9 && count(t0, 'border:1px solid') === 9, t0);
  ok(L + '表の HTML に改行・タブ・字下げが無い', [FX_BASIC, FX_TWO, FX_RAGGED, FX_CRLF, FX_XSS].every(function (b) {
    return tables(B.tables(C.esc(b))).every(function (t) { return !/[\n\r\t]/.test(t) && !/>\s+</.test(t); });
  }));
  // _lbTablesInline (1 行の短い表示): 「［表］」を消し、セルを「 / 」・行を「 ・ 」でつなぐ。生の文字を受けて生の文字を返す (タグを作らない)
  eq(L + '短い表示: 表を 1 行の文字にする', B.inline(FX_BASIC),
    'Read the notice.\n\nDay / Open / Close ・ Mon ( 1 ) / 9:00 / 17:00 ・ Sat / 10:00 / 15:00\n\nThe hall ( 2 ) on Sunday.');
  eq(L + '短い表示: 空行の無い表', B.inline(FX_TIGHT), 'Para one.\nItem / Price ・ Tea / $3\nNext line.');
  eq(L + '短い表示: 表 2 つ (続けて)', B.inline(FX_ADJ), 'A / B ・ 1 / 2\nC / D ・ 3 / 4');
  eq(L + '短い表示: 列の数がそろわない行 (埋めない)', B.inline(FX_RAGGED), 'x\nA / B / C ・ 1 / 2 ・ 3 / 4 / 5 / 6\ny');
  eq(L + '短い表示: 見出しだけ・本文の最後の表', [B.inline(FX_HEADONLY), B.inline(FX_END_NL)], ['A / B\nafter', 'Prices are below.\n\nSize / Cost ・ S / 100 ・ L / 200\n']);
  eq(L + '短い表示: セルの前後の空白 (全角も) と CRLF の \\r は外す', [B.inline(FX_SPACES), B.inline(FX_CRLF)], ['x\nRoom / Seats ・ Hall A / 120\ny', 'x\r\nA / B ・ 1 / 2\n\r\ny']);
  eq(L + '短い表示: 本文の中の文字はそのまま (エスケープはこの後の _escHtml がする)', B.inline('a <b>\n［表］\nX｜<i>Y</i>\n1｜&'), 'a <b>\nX / <i>Y</i> ・ 1 / &');
  // 表の無い文は 1 文字も変えない (生の文字にもエスケープ済みの文字にも)
  var bad = NO_TABLE.filter(function (b) { return B.tables(b) !== b || B.tables(C.esc(b)) !== C.esc(b) || B.inline(b) !== b; });
  ok(L + '表の無い文 (' + NO_TABLE.length + ' 本) は 2 つの関数とも 1 文字も変えない', bad.length === 0, bad);
})();
"""

CASES_SAME = r"""
(function () {
  var L = '4 ファイル: ';
  var FX = [FX_BASIC, FX_TIGHT, FX_END, FX_END_NL, FX_TWO, FX_ADJ, FX_RAGGED, FX_HEADONLY, FX_SPACES, FX_CRLF, FX_BENIGN, FX_XSS,
    '訳です。\n\n［表］\n曜日｜時間\n月｜9時\n\n以上。', '【本文】\n' + FX_BASIC + '\n\n( 1 ) に入るもの\n(A) is\n(B) are'].concat(NO_TABLE);
  var bad = [], badLook = [];
  FX.forEach(function (b) {
    var s = C.esc(b), c = norm(C.tables(s)), m = norm(M.tables(s)), e = norm(E.tables(s)), lb = norm(B.tables(s));
    if (c !== m || c !== e || c !== lb) bad.push([b, c, m, e, lb]);
    if (B.tables(s) !== M.tables(s)) badLook.push([b, B.tables(s), M.tables(s)]);
  });
  ok(L + '同じ入力に同じ表の構造 (タグと中身・前後の改行) を返す (class.html・mypage.js・ceo.html・learning-brain.js / ' + FX.length + ' 本)', bad.length === 0, bad[0]);
  ok(L + 'learning-brain.js (今日の復習) の表は見た目 (inline style) もマイページの本文カードと同じ', badLook.length === 0, badLook[0]);
  // 本文の通し (エスケープ → 空所 → 表) も構造は同じ (class.html の本文カードの中身 = mypage / ceo の本文)
  var inner = function (h) { return h.replace(/^<div class="gd-passage gd-nomath">/, '').replace(/<\/div>$/, ''); };
  var inner2 = function (h) { return h.replace(/^<div class="gd-nomath" style="[^"]*">/, '').replace(/<\/div>$/, ''); };
  var bad2 = [];
  [FX_BASIC, FX_TWO, FX_RAGGED, FX_XSS.replace(/'/g, '')].forEach(function (b) {
    var c = norm(inner(C.passage({ body: b }, false))), m = norm(inner2(M.passage({ body: b }, false))), e = norm(E.previewBody({ body: b }));
    if (c !== m || c !== e) bad2.push([b, c, m, e]);
  });
  ok(L + '本文の通し (エスケープ → 空所 → 表) の構造も同じ', bad2.length === 0, bad2[0]);
})();
__emit();
"""

# [7] 本物の learning-brain.js をまるごと動かす。偽の window / document / localStorage / setInterval / console を引数で渡す
#     (グローバルを書き換えない = node の localStorage などに触らない)。NEW = 今のファイル、OLD = 表の関数の呼び出しを外したもの。
LB_LOADER = r"""
var __lbWarns = [];
function __mkLB(__src) {
  var win = {}, els = {};
  var doc = { getElementById: function (id) { return Object.prototype.hasOwnProperty.call(els, id) ? els[id] : null; } };
  var store = {};
  var ls = { getItem: function (k) { return Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null; },
             setItem: function (k, v) { store[k] = String(v); }, removeItem: function (k) { delete store[k]; } };
  __src(win, doc, ls, function () { return 0; }, function () {}, { log: function () {}, warn: function () { __lbWarns.push([].slice.call(arguments).join(' ')); } });
  var LBx = win.LB;
  // カード 1 枚 (今日が期限) だけを入れて「今日の復習」を描き、innerHTML を返す
  LBx.renderOne = function (card) {
    var c = { key: 'k1', subject: '英語', topic: '長文', problem: '', answer: '', explanation: '', difficulty: '標準',
      ease: 2.5, interval: 1, repetitions: 0, dueDate: LBx._todayStr(), lapses: 1,
      history: [{ date: LBx._todayStr(), hour: 10, dow: 1, correct: false, ease: 2.5 }] };
    for (var k in card) c[k] = card[k];
    var cards = {}; cards[c.key] = c;
    LBx._write('sid', 'cards', cards);
    els.box = { innerHTML: '', dataset: {}, addEventListener: function () {} };
    LBx.renderTodayReview('box', 'sid');
    return els.box.innerHTML;
  };
  return LBx;
}
"""

CASES_LB_RENDER = r"""
(function () {
  var L = 'learning-brain.js 今日の復習: ';
  // innerHTML から箱を取り出す (開始の印の後ろから、終わりの印 (正規表現) の手前まで)
  function box(html, opener, endRe, nth) {
    var i = -1, from = 0;
    for (var t = 0; t <= (nth || 0); t++) { i = html.indexOf(opener, from); if (i < 0) return null; from = i + opener.length; }
    var rest = html.slice(from), m = rest.match(endRe);
    return m ? rest.slice(0, m.index) : null;
  }
  var SHORT = '<div style="font-size: 0.92rem; color: #e4e4e7; margin: 0.3rem 0; line-height: 1.5;">';
  var FULL = 'line-height:1.6; max-height:300px; overflow-y:auto;">';
  var STEM = '<div style="margin-bottom: 0.7rem; white-space: pre-wrap; line-height: 1.6; color: #e4e4e7;">';
  var AE = 'border-radius:6px; white-space:pre-wrap; max-height:300px; overflow-y:auto;">';   // 解答 (1 つ目)・解説 (2 つ目) の全文
  var shortOf = function (h) { return box(h, SHORT, /<details|<\/div>/); };
  var fullOf = function (h) { return box(h, FULL, /<\/div><\/details>/); };
  var stemOf = function (h) { return box(h, STEM, /<\/div>\s*<div class="lb-choices"/); };
  var noNl = function (h) { return tables(h).every(function (t) { return !/[\n\r\t]/.test(t) && !/>\s+</.test(t); }); };
  var LONG = new Array(40).join('This is a long paragraph without any table. ');   // 100 字を超えさせる (「… 全文を見る」を出す)

  // 長文型ドリルの復習カード (mypage.js が保存する形 = 「【本文】\n」+ 本文 + 空行 + 設問 + 選択肢)。本文はすべて架空
  var Q1 = '( 1 ) に入れるのに最も適切なものを選びなさい。';
  var P1 = '【本文】\n' + FX_BASIC + '\n\n' + Q1 + '\n(A) opens\n(B) closes\n(C) opened\n(D) closing';
  var h = NEW.renderOne({ problem: P1, answer: '(A) opens', explanation: '表の Mon の行を見る。' });
  var full = fullOf(h), stem = stemOf(h), sh = shortOf(h);
  ok(L + '箱が取り出せる (短い表示・… 全文を見る・解いてみるの問題文)', full !== null && stem !== null && sh !== null, h.slice(0, 600));
  full = full || ''; stem = stem || ''; sh = sh || '';
  ok(L + '… 全文を見る: 表になる・「［表］」と「｜」が消える', tables(full).length === 1 && full.indexOf('［表］') < 0 && full.indexOf('｜') < 0, full);
  eq(L + '… 全文を見る: 見出しは <th> 3 つ・行は <td> 3 つ × 2', rowsCells(tables(full)[0] || ''), [[3, 0], [0, 3], [0, 3]]);
  eq(L + '… 全文を見る: 構造は塾生アプリ (class.html) の表と同じ (【本文】の行・前後の改行・設問と選択肢はそのまま)', norm(full), norm(C.tables(C.esc(P1))));
  ok(L + '… 全文を見る: 【本文】の行の次に本文、表の後に本文の続き・設問', full.indexOf('【本文】\nRead the notice.\n\n<div style="overflow-x:auto') === 0
    && full.indexOf('</table></div>\nThe hall ( 2 ) on Sunday.\n\n' + Q1 + '\n(A) opens') > 0, full);
  ok(L + '📝 解いてみるの問題文: 表になる (選択肢の前まで = 【本文】から設問まで)', tables(stem).length === 1 && stem.indexOf('［表］') < 0
    && norm(stem) === norm(C.tables(C.esc('【本文】\n' + FX_BASIC + '\n\n' + Q1))), stem);
  ok(L + '📝 解いてみる: 選択肢 4 つ・正解 (A) は今までどおり', count(h, 'class="lb-choice-btn"') === 4 && h.indexOf('data-correct="A"') > 0, h.slice(0, 400));
  var C1 = '【本文】\nRead the notice.\n\nDay / Open / Close ・ Mon ( 1 ) / 9:00 / 17:00 ・ Sat / 10:00 / 15:00\n\nThe hall ( 2 ) on Sunday.\n\n' + Q1;
  eq(L + '短い表示 (先頭 100 字): 表を 1 行の文字にしてから切る', sh, C.esc(C1.slice(0, 100)));
  ok(L + '短い表示: 表を作らない・「［表］」「｜」・タグが出ない', sh.indexOf('<') < 0 && sh.indexOf('［表］') < 0 && sh.indexOf('｜') < 0, sh);
  ok(L + '表の HTML に改行・タブ・字下げが無い (カード全体)', tables(h).length === 2 && noNl(h), tables(h));

  // 【本文】の次の行がすぐ「［表］」
  var P2 = '【本文】\n［表］\nRoom｜Seats\nHall A｜120\nHall B｜80\n\nThe ( 1 ) hall is larger than the other one, so the club uses it for every meeting.\n' + Q1 + '\n(A) first\n(B) second';
  var h2 = NEW.renderOne({ problem: P2, answer: '(A) first' });
  var f2 = fullOf(h2) || '', s2 = stemOf(h2) || '', sh2 = shortOf(h2) || '';
  ok(L + '【本文】の次の行が「［表］」: 【本文】の行を残して表にする', f2.indexOf('【本文】\n<div style="overflow-x:auto') === 0 && tables(f2).length === 1
    && norm(f2) === norm(C.tables(C.esc(P2))) && s2.indexOf('【本文】\n<div style="overflow-x:auto') === 0, [f2, s2]);
  eq(L + '【本文】の次の行が「［表］」: 短い表示', sh2, C.esc(('【本文】\nRoom / Seats ・ Hall A / 120 ・ Hall B / 80\n\nThe ( 1 ) hall is larger than the other one, so the club uses it for every meeting.\n' + Q1).slice(0, 100)));

  // 表の途中で 100 字に切れる (前置きの長さを 1 字ずつ変える)。短い表示に「［表］」「｜」・タグの切れ端が出ない
  var rowsTxt = '';
  for (var r = 1; r <= 8; r++) rowsTxt += '\nRow ' + r + '｜' + (r * 7) + ' min｜Gate ' + r;
  var badCut = [];
  for (var n = 0; n <= 70; n++) {
    var P3 = '【本文】\n' + new Array(n + 1).join('w') + '\n［表］\nName｜Time｜Place' + rowsTxt + '\n\nQ?\n(A) a\n(B) b';
    var h3 = NEW.renderOne({ problem: P3, answer: '(A) a' }), sh3 = shortOf(h3);
    var want = C.esc(NEW_INLINE(P3).slice(0, 100));
    if (sh3 !== want || /[<｜［］]/.test(sh3) || tables(fullOf(h3) || '').length !== 1) badCut.push([n, sh3]);
  }
  ok(L + '短い表示は表の途中で切れても安全 (前置き 0〜70 字の 71 通り)', badCut.length === 0, badCut[0]);

  // 解答・解説の全文 (pre-wrap) は表・短い表示は 1 行の文字
  var EX = 'The table shows the times.\n［表］\nDay｜Open\nMon｜9:00\nSat｜10:00\n\n' + new Array(60).join('Read each row carefully. ');
  var ANS = '(B) closes\n［表］\nWord｜Meaning\nclose｜to shut\n\n' + new Array(25).join('more notes ');
  var h4 = NEW.renderOne({ problem: 'Choose.\n(A) a\n(B) b', answer: ANS, explanation: EX });
  var a4 = box(h4, AE, /<\/div><\/details>/, 0) || '', e4 = box(h4, AE, /<\/div><\/details>/, 1) || '';
  ok(L + '解答の全文 (300 字超) は表になる', ANS.length > 300 && tables(a4).length === 1 && a4.indexOf('［表］') < 0 && norm(a4) === norm(C.tables(C.esc(ANS))), a4);
  ok(L + '解説の全文 (500 字超) は表になる', EX.length > 500 && tables(e4).length === 1 && e4.indexOf('［表］') < 0 && norm(e4) === norm(C.tables(C.esc(EX))), e4);
  ok(L + '解答・解説の短い表示は 1 行の文字 (表の塊は「 / 」「 ・ 」)', h4.indexOf(C.esc(NEW_INLINE(ANS).slice(0, 300)) + '<details') > 0
    && h4.indexOf('<strong>解説:</strong> ' + C.esc(NEW_INLINE(EX).slice(0, 500)) + '<details') > 0, h4);
  var h5 = NEW.renderOne({ problem: 'Choose.\n(A) a\n(B) b', answer: '(A) a', explanation: '短い解説。\n［表］\nA｜B\n1｜2' });
  ok(L + '短い解説 (500 字以下・pre-wrap でない箱) は表を作らず 1 行の文字', h5.indexOf('<strong>解説:</strong> 短い解説。\nA / B ・ 1 / 2</div></details>') > 0 && tables(h5).length === 0, h5);
  ok(L + '表の HTML に改行が無い (解答・解説)', noNl(h4), tables(h4));

  // XSS: エスケープが先。カードの本文がタグにも属性にもならない (表の中でも外でも)
  var PX = '【本文】\n' + FX_XSS + '\n' + LONG + '\n\nQ?\n(A) a\n(B) b', PB = '【本文】\n' + FX_BENIGN + '\n' + LONG + '\n\nQ?\n(A) a\n(B) b';
  var hx = NEW.renderOne({ problem: PX, answer: '(A) a', explanation: FX_XSS }), hb = NEW.renderOne({ problem: PB, answer: '(A) a', explanation: FX_BENIGN });
  ok(L + 'XSS: <script> / <img> / <b> / <i> がタグにならない', !/<script|<img|<b>|<i>/i.test(hx), hx);
  ok(L + 'XSS: &lt;script&gt;・&amp;・&quot; にエスケープされる', hx.indexOf('&lt;script&gt;alert(x)&lt;/script&gt;') >= 0 && hx.indexOf('&amp;') >= 0 && hx.indexOf('&quot;q&quot;') >= 0, hx);
  ok(L + 'XSS: セルの中の </td> で列が増えない (2 列 × 2 行・全文と解いてみるの両方)', tables(hx).length === 2
    && tables(hx).every(function (t) { return JSON.stringify(rowsCells(t)) === '[[2,0],[0,2]]'; }), tables(hx).map(rowsCells));
  var bt = openTags(hb);
  ok(L + 'XSS: 出るタグ (属性つき) は害の無いカードと同じものだけ', openTags(hx).every(function (t) { return bt.indexOf(t) >= 0; }), [openTags(hx), bt]);
  ok(L + 'XSS: 短い表示にタグが出ない', (shortOf(hx) || '<').indexOf('<') < 0, shortOf(hx));

  // 表の無いカードは変更前 (表の関数の呼び出しを外した learning-brain.js) と 1 文字も変わらない
  var cardsNo = [];
  NO_TABLE.forEach(function (b) {
    cardsNo.push({ problem: b, answer: b, explanation: b });
    cardsNo.push({ problem: '【本文】\n' + b + '\n' + LONG + '\n\n' + Q1 + '\n(A) x\n(B) y', answer: LONG + b, explanation: LONG + LONG + b });
  });
  cardsNo.push({ problem: '下線部 の誤りを選べ。 (A) He go (B) to school (C) every (D) day.', answer: '(A) He go', explanation: '<u>go</u> は goes' });
  cardsNo.push({ problem: '【本文】\nx\n［表］\n' + LONG + '\n\nQ?\n(1) a\n(2) b', answer: '2', explanation: '' });
  var badNo = cardsNo.filter(function (cd) { return NEW.renderOne(cd) !== OLD.renderOne(cd); });
  ok(L + '表の無いカード (' + cardsNo.length + ' 枚。長い本文・【本文】・下線部・<u>・半角 | など) は変更前と 1 文字も変わらない', badNo.length === 0,
    badNo.length ? [badNo[0], NEW.renderOne(badNo[0]).slice(0, 300), OLD.renderOne(badNo[0]).slice(0, 300)] : '');
  ok(L + '表のあるカードは変更前と違う (この検査が呼び出しを外した版と本当に比べている)', NEW.renderOne({ problem: P1 }) !== OLD.renderOne({ problem: P1 }));
  eq(L + 'console.warn が出ない (描画が例外を出していない)', __lbWarns, []);
})();
__emit();
"""

JS_SYNTAX = r"""
for (var k in SRC) {
  try { new Function(SRC[k]); ok('構文 OK: ' + k, true); }
  catch (e) { ok('構文 OK: ' + k, false, String(e)); }
}
__emit();
"""


def run_js(engine, program, label):
    with tempfile.TemporaryDirectory(prefix="passage_table_js_") as td:
        path = os.path.join(td, "case.js")
        with open(path, "w", encoding="utf-8") as f:
            f.write(program)
        try:
            r = subprocess.run(engine + [path], capture_output=True, text=True, timeout=180)
        except Exception as e:  # noqa: BLE001
            check(f"{label}: JS を実行できた", False, f"{type(e).__name__}: {e}")
            return
    text = (r.stdout or "") + "\n" + (r.stderr or "")
    lines = [l for l in text.split("\n") if l.startswith(("OK  ", "NG  ", "DONE "))]
    done = [l for l in lines if l.startswith("DONE ")]
    if r.returncode != 0 or not done:
        check(f"{label}: JS が最後まで走った (exit {r.returncode})", False, text[-1500:])
        return
    for l in lines:
        if l.startswith("OK  "):
            check(l[4:], True)
        elif l.startswith("NG  "):
            check(l[4:], False, l[4:])
    n = int(done[-1].split()[1])
    check(f"{label}: {n} 件の検査を実行", n > 0)


def main():
    class_html = read(CLASS_HTML)
    mypage_js = read(MYPAGE_JS)
    mypage_html = read(MYPAGE_HTML)
    ceo_html = read(CEO_HTML)
    lb_js = read(LB_JS)
    class_inline = inline_scripts(class_html)
    class_script = class_inline[0] if len(class_inline) == 1 else ""
    check("class.html の inline script は 1 つ", len(class_inline) == 1, len(class_inline))

    # 画面の本物の関数を取り出す (ceo.html の escapeHtml は gdPreview / gdAnalytics と同じ IIFE の 4 字下げのもの)
    c_fns = [extract_fn(class_script, n, "    ", "class.html") for n in ("esc", "gdPassageTables", "gdPassageHtml")]
    m_fns = [extract_fn(mypage_js, n, "", "mypage.js") for n in ("escapeHtml", "_gdEscape", "_gdPassageTables", "_gdPassageBlock")]
    e_fns = [extract_fn(ceo_html, n, "    ", "ceo.html") for n in ("escapeHtml", "_gdPassageTables")]
    m_expr = re.findall(r"^\s*const bodyHtml = (.+);\s*$", ceo_html, re.M)
    check("ceo.html: 👀 問題を見る の const bodyHtml = … がちょうど 1 つ", len(m_expr) == 1, len(m_expr))
    # learning-brain.js (今日の復習) は IIFE の 2 字下げ。OLD = 表の関数の呼び出し 7 か所 (短い表示 3・pre-wrap の箱 4) を外した版
    #   (`_lbX(…)` → `(…)` = 変更前と同じ式。表の無いカードで innerHTML が 1 文字も変わらないことを見る)
    b_fns = [extract_fn(lb_js, n, "  ", "learning-brain.js") for n in ("_lbPassageTables", "_lbTablesInline")]
    lb_old, n_calls = re.subn(r"(?<!function )\b_lb(?:PassageTables|TablesInline)\(", "(", lb_js)
    check("learning-brain.js: 表の関数の呼び出しは 7 か所 (_lbTablesInline 3・_lbPassageTables 4)", n_calls == 7
          and len(re.findall(r"(?<!function )\b_lbTablesInline\(", lb_js)) == 3, n_calls)

    eng = js_engine()
    print(f"JS エンジン: {eng[0] if eng else 'なし'}")
    check("JS の実行環境がある (node / osascript / jsc。無ければ FAIL)", bool(eng),
          "node も osascript も jsc も見つからない (AJ_JS_ENGINE の指定も確認)")

    lb_part = ""
    if all(b_fns):
        lb_part = "var B = (function () {\n" + "\n".join(b_fns) + \
            "\nreturn { tables: _lbPassageTables, inline: _lbTablesInline };\n})();\n"
    if eng and all(c_fns) and all(m_fns) and all(e_fns) and len(m_expr) == 1 and lb_part:
        prog = PRELUDE
        prog += "var C = (function () {\n" + "\n".join(c_fns) + OLD_CLASS + \
            "\nreturn { esc: esc, tables: gdPassageTables, passage: gdPassageHtml, passageOld: gdPassageHtml_OLD };\n})();\n"
        prog += "var M = (function () {\n" + "\n".join(m_fns) + OLD_MYPAGE + \
            "\nreturn { esc: _gdEscape, tables: _gdPassageTables, passage: _gdPassageBlock, passageOld: _gdPassageBlock_OLD };\n})();\n"
        prog += "var E = (function () {\n" + "\n".join(e_fns) + OLD_CEO + \
            "\nfunction previewBody(p) { return " + m_expr[0] + "; }\n" + \
            "return { esc: escapeHtml, tables: _gdPassageTables, previewBody: previewBody, previewBodyOld: previewBody_OLD };\n})();\n"
        prog += lb_part
        prog += CASES + CASES_CLASS + CASES_MYPAGE + CASES_CEO + CASES_LB_UNIT + CASES_SAME
        print("\n[1]〜[4] 本文の表 (class.html・mypage.js・ceo.html・learning-brain.js の本物の関数)")
        run_js(eng, prog, "[1-4]")

        # [7] 本物の learning-brain.js をまるごと動かす (今の版 NEW と 呼び出しを外した版 OLD)
        prog7 = PRELUDE + CASES + "var C = (function () {\n" + "\n".join(c_fns) + OLD_CLASS + \
            "\nreturn { esc: esc, tables: gdPassageTables };\n})();\n" + lb_part + "var NEW_INLINE = B.inline;\n" + LB_LOADER
        for name, src in (("NEW", lb_js), ("OLD", lb_old)):
            prog7 += "var " + name + " = __mkLB(function (window, document, localStorage, setInterval, clearInterval, console) {\n" + \
                src + "\n});\n"
        prog7 += CASES_LB_RENDER
        print("\n[7] 今日の復習 (learning-brain.js renderTodayReview をまるごと動かす)")
        run_js(eng, prog7, "[7]")

    if eng:
        print("\n[5] 構文 (new Function)")
        srcs = {"mypage.js": mypage_js, "learning-brain.js": lb_js}
        for i, b in enumerate(class_inline):
            srcs[f"class.html inline #{i}"] = b
        for i, b in enumerate(inline_scripts(ceo_html)):
            srcs[f"ceo.html inline #{i}"] = b
        run_js(eng, PRELUDE + "var SRC = " + json.dumps(srcs, ensure_ascii=True) + ";\n" + JS_SYNTAX, "[5]")

    print("\n[6] ソース検査")
    css = re.findall(r"^\s*\.gd-passage \.gd-table[^{]*\{[^}]*\}", class_html, re.M)
    css_all = "\n".join(css)
    check("class.html: .gd-table-wrap は横スクロール (overflow-x:auto)", re.search(r"\.gd-table-wrap \{[^}]*overflow-x:auto", css_all) is not None, css_all)
    check("class.html: セルは折り返さない・枠線あり (th, td)", re.search(r"\.gd-table th, \.gd-passage \.gd-table td \{[^}]*border:1px solid[^}]*white-space:nowrap", css_all) is not None, css_all)
    check("class.html: 本文と全訳の両方を gdPassageTables に通す",
          "var body = gdPassageTables(esc(p.body || '').replace(" in class_script and "<div class=\"gd-ja\">' + gdPassageTables(esc(p.body_ja)) + '</div></details>'" in class_script)
    check("class.html: 本文カードは gd-nomath のまま (KaTeX の対象外)", "'<div class=\"gd-passage gd-nomath\">'" in class_script)
    check("mypage.js: 本文と全訳の両方を _gdPassageTables に通す",
          "const body = _gdPassageTables(_gdEscape(p.body || '').replace(" in mypage_js and "${_gdPassageTables(_gdEscape(p.body_ja))}" in mypage_js)
    check("ceo.html: 👀 の全訳と 📊 分析の 📖 本文も _gdPassageTables に通す",
          "${_gdPassageTables(escapeHtml(p.body_ja))}" in ceo_html and "${_gdPassageTables(escapeHtml(_p.body || ''))}" in ceo_html)
    check("ceo.html: _gdPassageTables の呼び出しは 3 か所 (定義を除く)", ceo_html.count("_gdPassageTables(") - 1 == 3, ceo_html.count("_gdPassageTables(") - 1)
    i_iife = ceo_html.find("async function gdPreview()")
    i_def = ceo_html.find("    function _gdPassageTables(s) {")
    i_an = ceo_html.find("async function gdAnalytics(")
    check("ceo.html: _gdPassageTables は gdPreview / gdAnalytics と同じ字下げ (同じ IIFE の中) に置く", 0 <= i_def < i_iife < i_an, (i_def, i_iife, i_an))
    check("mypage.html: mypage.js を ?v= 付きで読む (変えたら上げる。検査は js_cache_bust.py)", re.search(r'<script src="mypage\.js\?v=[^"]+"></script>', mypage_html) is not None)
    ceo_js = read(os.path.join(REPO, "ceo.js"))
    check("ceo.js には表の処理を足していない (ceo.html の inline だけで直す = ceo.js の ?v= を上げない)", "［表］" not in ceo_js)
    # 今日の復習 (learning-brain.js)
    for frag in ("const probShort = _lbTablesInline(c.problem || '').slice(0, 100);",
                 "const ansShort = _lbTablesInline(c.answer || '').slice(0, 300);",
                 "const explShort = _lbTablesInline(c.explanation || '').slice(0, 500);",
                 "${_lbPassageTables(_escHtml(c.problem))}", "${_lbPassageTables(_escHtml(c.answer))}",
                 "${_lbPassageTables(_escHtml(c.explanation))}", "${_lbPassageTables(_escHtml(parsed.stem))}"):
        check(f"learning-brain.js: {frag[:60]}", lb_js.count(frag) == 1, lb_js.count(frag))
    check("learning-brain.js: pre-wrap の箱は全部表の関数を通す (_escHtml の直書きが pre-wrap の箱に残っていない)",
          re.search(r'pre-wrap[^`]*?">\$\{_escHtml\(', lb_js) is None, re.findall(r'pre-wrap[^`]{0,80}?">\$\{_escHtml\([^)]*\)', lb_js))
    check("mypage.js: 復習カードに保存する形は変えていない (「【本文】\\n」+ 本文 5000 字 + 設問)",
          r"problemFull = ('【本文】\n' + _pbody.slice(0, 5000) + '\n\n' + _pprob).slice(0, 6500);" in mypage_js)
    callers = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "vendor")]
        for fn in files:
            if fn.endswith((".html", ".js")) and fn != "learning-brain.js":
                fp = os.path.join(root, fn)
                try:
                    if "renderTodayReview(" in read(fp):
                        callers.append(os.path.relpath(fp, REPO))
                except (UnicodeDecodeError, OSError):
                    pass
    check("今日の復習を描くのはマイページだけ (表の色はマイページの暗い画面に合わせている。明るい画面で描くなら色を見直す)",
          callers == ["mypage.html"], callers)
    lb_refs = {}
    for fn in sorted(os.listdir(REPO)):
        if fn.endswith(".html"):
            for m in re.finditer(r'<script[^>]+src="learning-brain\.js([^"]*)"', read(os.path.join(REPO, fn))):
                lb_refs.setdefault(fn, []).append(m.group(1))
    check("learning-brain.js を読む HTML はどれも ?v= 付き (変えたら全部上げる。検査は js_cache_bust.py)",
          len(lb_refs) >= 5 and all(v.startswith("?v=") and len(v) > 3 for vs in lb_refs.values() for v in vs), lb_refs)
    ci = read(CI_YML)
    check("CI (server-tests.yml) にこのテストの step がある", "python3 scripts/health_check/test_passage_table_render.py" in ci)
    paths_block = ci.split("pull_request:")[0]
    for p in ("'class.html'", "'mypage.js'", "'ceo.html'", "'learning-brain.js'", "'scripts/health_check/test_*.py'"):
        check(f"CI の paths に {p} (画面だけの push でも走らせる)", p in paths_block)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES[:20]))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
