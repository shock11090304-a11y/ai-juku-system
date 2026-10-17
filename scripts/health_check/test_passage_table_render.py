#!/usr/bin/env python3
"""📊 本文の表 (取込仕様 docs/drill-import-spec.md §2 の「［表］」+「｜」) を画面で <table> にする規則を、実際の JS エンジンで動かして確かめる。

背景 (2026-10-17 塾長「アプリ側で表を直しておいて」): 長文型ドリル (英語長文・習熟度テスト・英検の長文など) の本文は、
  エスケープした文字を white-space:pre-wrap でそのまま出していたので、表の書き方「［表］」の行と「｜」区切りの行が生のまま見えた。
  375px のスマホでは本文カードが 約 309px (塾生アプリ class.html)・約 270px (マイページ) しかなく、行が折り返して列がずれる。
  → 「［表］」の塊を本物の <table> (1 行目 = 見出し <th>) にし、横スクロールの箱 (overflow-x:auto) に入れ、セルは折り返さない。

固定する性質 (class.html の gdPassageTables / mypage.js と ceo.html の _gdPassageTables):
  [1] class.html: 表になる (見出し・行・セルの数)・「［表］」の行が消える・表の HTML に改行が無い・表の前後の改行の数
      (「［表］」の行の分の空行を残さない・表の直後の改行 1 つは表が吸う)・XSS (エスケープが先・本文がタグや属性にならない)・
      空所「( 1 )」の黄色は表の中でも外でも効く・表の無い本文は今までと 1 文字も変わらない (変更前の関数と比べる)・列の数が
      そろわない行 (空のセルで埋める)・本文の最後の表・表 2 つ (間に文 / 続けて)・半角 | は表にしない・全訳 (body_ja) の表
  [2] mypage.js: 同じ性質を _gdPassageBlock で
  [3] ceo.html: 👀 問題を見る の本文 (const bodyHtml = … の式をソースから取り出して動かす)・全訳と 📊 分析の 📖 本文の呼び出し
  [4] 3 つのファイルが同じ入力に同じ表の構造 (タグと中身。属性 = 見た目だけ違う) を返す
  [5] 構文 (new Function): class.html の inline script・mypage.js・ceo.html の inline script
  [6] ソース検査: CSS (横スクロール・折り返さない・枠線)・呼び出し箇所・mypage.js の ?v=・ceo.js を触っていない前提の確認・CI 登録

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

CASES_SAME = r"""
(function () {
  var L = '3 ファイル: ';
  var FX = [FX_BASIC, FX_TIGHT, FX_END, FX_END_NL, FX_TWO, FX_ADJ, FX_RAGGED, FX_HEADONLY, FX_SPACES, FX_CRLF, FX_BENIGN,
    '訳です。\n\n［表］\n曜日｜時間\n月｜9時\n\n以上。'].concat(NO_TABLE);
  var bad = [];
  FX.forEach(function (b) {
    var s = C.esc(b), c = norm(C.tables(s)), m = norm(M.tables(s)), e = norm(E.tables(s));
    if (c !== m || c !== e) bad.push([b, c, m, e]);
  });
  ok(L + '同じ入力に同じ表の構造 (タグと中身・前後の改行) を返す (' + FX.length + ' 本)', bad.length === 0, bad[0]);
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
    class_inline = inline_scripts(class_html)
    class_script = class_inline[0] if len(class_inline) == 1 else ""
    check("class.html の inline script は 1 つ", len(class_inline) == 1, len(class_inline))

    # 画面の本物の関数を取り出す (ceo.html の escapeHtml は gdPreview / gdAnalytics と同じ IIFE の 4 字下げのもの)
    c_fns = [extract_fn(class_script, n, "    ", "class.html") for n in ("esc", "gdPassageTables", "gdPassageHtml")]
    m_fns = [extract_fn(mypage_js, n, "", "mypage.js") for n in ("escapeHtml", "_gdEscape", "_gdPassageTables", "_gdPassageBlock")]
    e_fns = [extract_fn(ceo_html, n, "    ", "ceo.html") for n in ("escapeHtml", "_gdPassageTables")]
    m_expr = re.findall(r"^\s*const bodyHtml = (.+);\s*$", ceo_html, re.M)
    check("ceo.html: 👀 問題を見る の const bodyHtml = … がちょうど 1 つ", len(m_expr) == 1, len(m_expr))

    eng = js_engine()
    print(f"JS エンジン: {eng[0] if eng else 'なし'}")
    check("JS の実行環境がある (node / osascript / jsc。無ければ FAIL)", bool(eng),
          "node も osascript も jsc も見つからない (AJ_JS_ENGINE の指定も確認)")

    if eng and all(c_fns) and all(m_fns) and all(e_fns) and len(m_expr) == 1:
        prog = PRELUDE
        prog += "var C = (function () {\n" + "\n".join(c_fns) + OLD_CLASS + \
            "\nreturn { esc: esc, tables: gdPassageTables, passage: gdPassageHtml, passageOld: gdPassageHtml_OLD };\n})();\n"
        prog += "var M = (function () {\n" + "\n".join(m_fns) + OLD_MYPAGE + \
            "\nreturn { esc: _gdEscape, tables: _gdPassageTables, passage: _gdPassageBlock, passageOld: _gdPassageBlock_OLD };\n})();\n"
        prog += "var E = (function () {\n" + "\n".join(e_fns) + OLD_CEO + \
            "\nfunction previewBody(p) { return " + m_expr[0] + "; }\n" + \
            "return { esc: escapeHtml, tables: _gdPassageTables, previewBody: previewBody, previewBodyOld: previewBody_OLD };\n})();\n"
        prog += CASES + CASES_CLASS + CASES_MYPAGE + CASES_CEO + CASES_SAME
        print("\n[1]〜[4] 本文の表 (class.html・mypage.js・ceo.html の本物の関数)")
        run_js(eng, prog, "[1-4]")

    if eng:
        print("\n[5] 構文 (new Function)")
        srcs = {"mypage.js": mypage_js}
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
    ci = read(CI_YML)
    check("CI (server-tests.yml) にこのテストの step がある", "python3 scripts/health_check/test_passage_table_render.py" in ci)
    paths_block = ci.split("pull_request:")[0]
    for p in ("'class.html'", "'mypage.js'", "'ceo.html'", "'scripts/health_check/test_*.py'"):
        check(f"CI の paths に {p} (画面だけの push でも走らせる)", p in paths_block)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES[:20]))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
