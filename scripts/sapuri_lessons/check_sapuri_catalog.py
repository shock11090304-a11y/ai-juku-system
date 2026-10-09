#!/usr/bin/env python3
"""📺 スタサプ講座カタログ (server/main.py のコード定数) の検査ゲート (2026-10-10 スタサプ段階 A・B)。

server/main.py を **import せず ast で読む** (標準ライブラリだけ・DB に触れない)。引数なし = 全部を検査する。

検査すること:
  1. SAPURI_COURSES: code が一意 / first ≤ last / total_lessons ≥ last-first+1 (番号の無い補講で 1 多い講座がある) /
     共通テスト対策は first=last=total=0 / level・band・subject が語彙内 / has_lessons の講座は講数が公開 /
     講師名の気配が無い (「講師」「先生」の語・「24講 (◯)」のような講数の後ろのかっこ書き) / notes に「題名」が無い (D1)
  2. SAPURI_COVERS (と文化史・史料の TIER1_ONLY): code が実在 / 科目キーが SAPURI_SUBJECT_KEYS / タグが語彙内 /
     共通テスト・中学総復習・総合問題編 (_2) を入れていない / 各科目キーに 高3 と 高1・2 の講座がある (全学年は両方)
  3. SAPURI_TAG_VOCAB / SAPURI_TAG_ALIASES / _UNIT_TAG_ALIASES / SAPURI_MATH_TAG_FIELD の整合
  4. _SAPURI_COURSE_LABELS_DECLARED == _COURSE_CLASSES[_SAPURI_COURSE_NAME] (順不同・3 件)
  5. SAPURI_LEGACY_NAME_TO_CODE の code が実在 / app.js の SAPURI_LEGACY_CAPS がその写しと一致・
     TEXTBOOK_TOTAL_UNITS に旧名の鍵を二重に持たない
  6. 旧初期データ (SAPURI_LECTURES_SEED) の参照が残っていない・起動時に sapuri_lectures へ投入しない・
     sapuri_lectures 表を SELECT/INSERT する箇所が無い
  7. 講の題名の置き場にしない: リポジトリに high_category*.tsv / sapuri_lessons_*.json / sapuri_import/ が無い
  9. 段階 B (講データ): sapuri_lessons / sapuri_lesson_tags / sapuri_topic_lessons の DDL が _schema_sql にあり student_id 列が無い /
     取込 API は管理者 Bearer だけ (_verify_admin_required・X-Cron-Secret を受けない) / 照合 (_sapuri_recommend) を
     weakness-top3・週次プリントの共有カーソルで呼ばない / サーバのログに題名 (title) を出さない /
     文化史 (TIER1_ONLY) は field=文化史 で同じ科目キーの通史が SAPURI_COVERS にある / 史料・テーマ史は照合に使わない
  8. app.js の講数上限表を **実際の JS で** 動かす (node か osascript の JavaScriptCore。CI の ubuntu には node がある):
     SAPURI_COURSES の 138 講座を実行時の表に入れても、参考書のタスク (「セミナー生物 p.100-120」「化学基礎 一問一答 No.30-60」
     「漢文 句法 第15講」等) が入れる前と同じ結果になる / 実行時の鍵に科目名だけ・6 文字未満の鍵が無い /
     スタサプのタスクには上限が効く (総合問題編の第41講は書き換えない) / 端末の控えは 1 日・版なしで読み直し扱い
 10. 生徒画面の「📺 第N講」の組み立て (mypage.js sapuriRecParts/sapuriRecText/sapuriRecLineHtml・class.html の今週見るスタサプ・
     ceo.html の見え方) を **実際の JS で** 動かす: 「（第b講まで）」は講番号が続くときだけ (飛び飛び [3, 15] には付けない・
     to_seq=null は範囲なし) / 画面は講座名の行と「第N講…」の行を分ける (1 行に丸めるとスマホで第N講が切れる)

実行: python3 scripts/sapuri_lessons/check_sapuri_catalog.py   # exit 0 = 合格 / 1 = 違反あり
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
APP_JS = os.path.join(REPO, "app.js")
MYPAGE_JS = os.path.join(REPO, "mypage.js")
CLASS_HTML = os.path.join(REPO, "class.html")
CEO_HTML = os.path.join(REPO, "ceo.html")

LEVELS = {"ベーシック", "スタンダード", "ハイ", "トップ", "トップ&ハイ", "ハイ&スタンダード", "共通テスト", "—"}
BANDS = {"高3", "高1・2", "全学年"}
SUBJECTS = {"英語", "数学", "国語", "物理", "化学", "生物", "地学", "日本史", "世界史", "地理", "政経", "倫理", "公共",
            "情報", "小論文"}
KEYS = {"code", "name", "subject", "field", "level", "band", "first", "last", "total_lessons", "dev_min", "dev_max",
        "weeks", "has_lessons", "notes"}

problems = []
# 科目キーごとに「この学年帯の講座が無いのが正しい」例外 (科目キー → (学年帯, …))。足すときは理由をコメントに書く。
#   2026-10-10 時点: 15 科目キーとも 高3 / 高1・2 (全学年を含む) の講座があるので空。
_BAND_EXCEPTIONS = {}


def bad(msg):
    problems.append(msg)
    print(f"  ❌ {msg}")


def good(msg):
    print(f"  ✅ {msg}")


def load_consts():
    src = open(MAIN_PY, encoding="utf-8").read()
    tree = ast.parse(src)
    want = {"SAPURI_COURSES", "SAPURI_SUBJECT_KEYS", "SAPURI_TAG_VOCAB", "SAPURI_TAG_ALIASES", "SAPURI_MATH_TAG_FIELD",
            "SAPURI_COVERS", "SAPURI_COVERS_TIER1_ONLY", "SAPURI_LEGACY_NAME_TO_CODE", "_SAPURI_COURSE_NAME",
            "_SAPURI_COURSE_LABELS_DECLARED", "_COURSE_CLASSES", "_UNIT_TAG_ALIASES"}
    out = {}
    for node in tree.body:   # module 直下の代入だけ (関数内のローカルは読まない)
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in want:
                if name in out:
                    bad(f"{name} が module 直下で 2 回代入されている (片方だけ直す事故の元)")
                try:
                    out[name] = ast.literal_eval(node.value)
                except Exception as e:
                    bad(f"{name} がリテラルとして読めない ({type(e).__name__})")
    for name in sorted(want - set(out)):
        bad(f"{name} が server/main.py の module 直下に無い")
    return src, tree, out


def norm(s):
    s = unicodedata.normalize("NFKC", str(s or ""))
    s = re.sub(r"[〈《<]", "<", s)
    s = re.sub(r"[〉》>]", ">", s)
    return re.sub(r"\s+", "", s)



# [8] の JS。app.js の上限表の部分 (TEXTBOOK_TOTAL_UNITS 〜 _recapTaskTitle) の後ろに付けて実行する。
#   参考書のタスクは「実行時の表を入れる前」と「入れた後」で結果が同じでなければならない (差分で見る = 期待値を手書きしない)。
_JS_CASES = r"""
var out = [];
function eq(label, got, want) { out.push((got === want ? 'OK  ' : 'NG  ') + label + ' => ' + JSON.stringify(got) + (got === want ? '' : ' (want ' + JSON.stringify(want) + ')')); }
var NON_SAPURI = __NON_SAPURI__;
var ADV = __ADV__;
function snap() {
  var r = {};
  NON_SAPURI.forEach(function (t) { r['recap:' + t] = _recapTaskTitle(t); });
  ADV.forEach(function (a) { [1, 3, 8].forEach(function (w) { r['adv' + w + ':' + a] = _advanceTaskRange(a, w); }); });
  return r;
}
var before = snap();
_sapuriSetRuntimeCaps(__CAPS__, { v: 'gate', at: Date.now() });
var after = snap();
Object.keys(before).forEach(function (k) { eq('実行時の表を入れても参考書のタスクは同じ: ' + k, after[k], before[k]); });
// 実行時の鍵に科目名だけ・短い鍵が無い
var BANNED = ['英語', '数学', '国語', '古文', '漢文', '現代文', '物理', '化学', '生物', '地学', '日本史', '世界史', '地理', '倫理',
              '政治経済', '政経', '公共', '物理基礎', '化学基礎', '生物基礎', '地学基礎', '英語超入門', '情報I', '小論文', '高3生物'];
_tbCapIndex = null;
var idx = _tbBuildIndex();
var rt = idx.filter(function (e) { return e.rt; });
eq('実行時の鍵がある', rt.length > 50, true);
rt.forEach(function (e) {
  if (e.k.length < 6) eq('実行時の鍵が短い: ' + e.k, false, true);
  if (BANNED.indexOf(e.k) !== -1) eq('実行時の鍵が科目名だけ: ' + e.k, false, true);
});
// スタサプのタスクには効く
eq('総合問題編 第41講は書き換えない', _recapTaskTitle('高3 スタンダードレベル数学IAIIB＋C（ベクトル）＜総合問題編＞ 第41講'), '高3 スタンダードレベル数学IAIIB＋C（ベクトル）＜総合問題編＞ 第41講');
eq('総合問題編 第50講 → 第42講 (2周目)', _recapTaskTitle('高3 スタンダードレベル数学IAIIB＋C（ベクトル）＜総合問題編＞ 第50講'), '高3 スタンダードレベル数学IAIIB＋C（ベクトル）＜総合問題編＞ 第42講 (2周目)');
eq('学年なしの講座名にも上限', _recapTaskTitle('ハイレベル英語<文法編> 第25講'), 'ハイレベル英語<文法編> 第1講 (2周目)');
eq('学年つきの正式名 (地理 20 講) に上限', _recapTaskTitle('高1・高2・高3 地理 第25講'), '高1・高2・高3 地理 第5講 (2周目)');
eq('旧名タスクの上限は残る', _recapTaskTitle('高3 ハイレベル英文法 第30講'), '高3 ハイレベル英文法 第6講 (2周目)');
eq('未知の講座は上限なし', _advanceTaskRange('謎の講座 第1講', 100), '謎の講座 第101講');
// 端末の控えの鮮度
eq('取得したばかりの控えは新しい', _sapuriCapsStale(), false);
_sapuriSetRuntimeCaps(__CAPS__, { v: 'gate', at: Date.now() - 2 * 24 * 60 * 60 * 1000 });
eq('2 日前の控えは読み直す', _sapuriCapsStale(), true);
_sapuriSetRuntimeCaps(__CAPS__, { v: null, at: Date.now() });
eq('版の無い控えは読み直す', _sapuriCapsStale(), true);
var __res = out.join('\n');
if (typeof process !== 'undefined' && typeof console !== 'undefined') { console.log(__res); }
__res;
"""

# 参考書・一般の教材のタスク (スタサプではない)。科目名を含むものを中心に
_NON_SAPURI_TITLES = [
    "セミナー生物 p.100-120", "リードLightノート生物 No.60-80", "セミナー物理基礎 p.40-60", "化学基礎 一問一答 No.30-60",
    "地理 一問一答 No.100-200", "倫理 用語集 p.40-80", "漢文 句法 第15講", "現代文 評論 第20題", "地学基礎 第15章",
    "生物 P.50-60", "化学基礎 P.20-45", "地理総合 P.30-50", "現代文 第15講", "物理基礎 第11章", "セミナー化学基礎 例題 10-25",
    "生物基礎 問題 No.20-40", "政治経済 一問一答 No.300-400", "英語超入門 第5講", "古文 単語 No.200-260",
    "ハイレベル数学I・A・II・Bの完全攻略 p.30-50", "日本史 一問一答 No.500-600", "世界史 用語集 p.120-160",
    "マドンナ古文 第41講", "シス単 No.1-150",
]
_ADV_TITLES = ["化学基礎 問題 1-30", "生物 P.50-60", "現代文 第15講", "地理 No.100-120", "漢文 第3講"]


def _js_engine():
    if shutil.which("node"):
        return ["node"]
    if shutil.which("osascript"):
        return ["osascript", "-l", "JavaScript"]
    return None


def check_appjs_caps_runtime(courses):
    """[8] app.js の上限表を実際の JS で動かす (node / osascript)。"""
    print("\n[8] app.js の講数上限表 (実行時の表 = SAPURI_COURSES を入れて JS で実行)")
    n0 = len(problems)
    js = open(APP_JS, encoding="utf-8").read()
    try:
        seg = js[js.index("const TEXTBOOK_TOTAL_UNITS = {"):js.index("// 指定日がどのフェーズに属するかを判定")]
    except ValueError:
        bad("app.js の上限表の範囲 (const TEXTBOOK_TOTAL_UNITS 〜 「指定日がどのフェーズに属するかを判定」) が見つからない")
        return
    eng = _js_engine()
    if not eng:
        bad("JS の実行環境 (node / osascript) が無い — 上限表を実行して確かめられない")
        return
    caps = [{"name": c["name"], "first": c["first"], "last": c["last"]} for c in courses]
    cases = (_JS_CASES.replace("__CAPS__", json.dumps(caps, ensure_ascii=False))
             .replace("__NON_SAPURI__", json.dumps(_NON_SAPURI_TITLES, ensure_ascii=False))
             .replace("__ADV__", json.dumps(_ADV_TITLES, ensure_ascii=False)))
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "caps_check.js")
        with open(path, "w", encoding="utf-8") as f:
            f.write(seg + "\n" + cases)
        try:
            r = subprocess.run(eng + [path], capture_output=True, text=True, timeout=120)
        except Exception as e:
            bad(f"JS の実行に失敗 ({type(e).__name__})")
            return
    outp = (r.stdout or "").strip()
    if r.returncode != 0 or not outp:
        bad(f"JS が失敗した (exit {r.returncode}): {(r.stderr or '')[:400]}")
        return
    lines = outp.split("\n")
    ng = [l for l in lines if l.startswith("NG")]
    for l in ng:
        bad(l[4:])
    if len(problems) == n0:
        good(f"{len(lines)} 件 OK ({eng[0]}): 参考書 {len(_NON_SAPURI_TITLES)} 件は実行時の表を入れても同じ・科目名だけの鍵なし・"
             f"スタサプの上限と第41講・控えの読み直し")


# [10] の JS。mypage.js / class.html / ceo.html の 📺 行の組み立て部分の後ろに付けて実行する (題名は架空)。
_JS_REC_CASES = r"""
var out = [];
function eq(label, got, want) { out.push((got === want ? 'OK  ' : 'NG  ') + label + ' => ' + JSON.stringify(got) + (got === want ? '' : ' (want ' + JSON.stringify(want) + ')')); }
function L(seqs) { return seqs.map(function (n) { return { seq: n, title: 'テスト講義' + n }; }); }
var CN = 'テスト講座X';
var A = { course_name: CN, lessons: L([3, 15]) };                 // 飛び飛び・to_seq なし (AI 弱点プリント)
var B = { course_name: CN, lessons: L([3, 4, 15]) };              // 先頭が続く
var C = { course_name: CN, lessons: L([12]), to_seq: 14 };        // 表示用 (TOP3・週次・class)
var D = { course_name: CN, lessons: L([12]), to_seq: null };      // 範囲なし
var E = { course_name: CN, lessons: L([3, 15]), to_seq: null };   // サーバが範囲なしと決めた
var F = { course_name: CN, lessons: [] };                         // 講座だけ (Tier 3)
// mypage.js
eq('mypage: 飛び飛び [3,15] は範囲を書かない', sapuriRecText(A, false), CN + ' 第3講「テスト講義3」');
eq('mypage: [3,4,15] は続く所まで', sapuriRecText(B, false), CN + ' 第3講「テスト講義3」（第4講まで）');
eq('mypage: to_seq 14', sapuriRecText(C), '📺 スタサプ：' + CN + ' 第12講「テスト講義12」（第14講まで）');
eq('mypage: to_seq null は範囲なし', sapuriRecText(D, false), CN + ' 第12講「テスト講義12」');
eq('mypage: to_seq null は lessons が飛び飛びでも範囲なし', sapuriRecText(E, false), CN + ' 第3講「テスト講義3」');
eq('mypage: 講座だけ', sapuriRecText(F), '📺 スタサプ：' + CN);
eq('mypage: 講座だけは requireLesson で出さない', sapuriRecText(F, true, true), '');
var h = sapuriRecLineHtml(C, { requireLesson: true });
eq('mypage: 画面は講座名の行と第N講の行を分ける', /<div[^>]*line-clamp:1[^>]*>📺 スタサプ：テスト講座X<\/div><div[^>]*line-clamp:2[^>]*>第12講「テスト講義12」（第14講まで）<\/div>/.test(h), true);
eq('mypage: 講座だけの行は 1 段', /第\d+講/.test(sapuriRecLineHtml(F)) || sapuriRecLineHtml(F).indexOf(CN) < 0, false);
// class.html
eq('class: 飛び飛び [3,15] は範囲を書かない', spLineParts(A).lesson, '第3講「テスト講義3」');
eq('class: to_seq 14', spLineParts(C).lesson, '第12講「テスト講義12」（第14講まで）');
eq('class: to_seq null', spLineParts(E).lesson, '第3講「テスト講義3」');
eq('class: 講座だけは出さない', spLineParts(F), null);
var ch = sapuriCardHtml([Object.assign({ subject: 'english', topic: '関係詞' }, C)]);
eq('class: 講座名の行と第N講の行 (2 行まで) を分ける', ch.indexOf('<div class="sp-course">' + CN + '</div><div class="sp-line">第12講「テスト講義12」（第14講まで）</div>') >= 0, true);
// ceo.html (生徒の見え方)
eq('ceo: 飛び飛び [3,15] は範囲を書かない', recText(A, false), CN + ' 第3講「テスト講義3」');
eq('ceo: [3,4,15] は続く所まで', recText(B, false), CN + ' 第3講「テスト講義3」（第4講まで）');
eq('ceo: to_seq 14', recText(C, true), '📺 スタサプ：' + CN + ' 第12講「テスト講義12」（第14講まで）');
eq('ceo: to_seq null', recText(D, false), CN + ' 第12講「テスト講義12」');
eq('ceo: 画面は 2 段 (生徒画面と同じ)', /line-clamp:1;[^>]*>📺 スタサプ：テスト講座X<\/div><div[^>]*line-clamp:2;[^>]*>第12講/.test(recLineHtml(C, true)), true);
var __res = out.join('\n');
if (typeof process !== 'undefined' && typeof console !== 'undefined') { console.log(__res); }
__res;
"""


def _cut(text, start, end, label):
    try:
        a = text.index(start)
        return text[a:text.index(end, a)]
    except ValueError:
        bad(f"{label} の範囲 ({start.strip()[:40]} 〜 {end.strip()[:40]}) が見つからない")
        return None


def check_front_rec_runtime():
    """[10] 生徒画面の 📺 行の組み立てを実際の JS で動かす (node / osascript)。"""
    print("\n[10] 生徒画面の「📺 第N講」(mypage.js・class.html・ceo.html を JS で実行)")
    n0 = len(problems)
    segs = [
        _cut(open(MYPAGE_JS, encoding="utf-8").read(), "function _sapuriRunEnd(ls) {", "window.sapuriRecParts = sapuriRecParts;", "mypage.js"),
        _cut(open(CLASS_HTML, encoding="utf-8").read(), "    function spRunEnd(ls) {", "    async function loadSapuriCard() {", "class.html"),
        _cut(open(CEO_HTML, encoding="utf-8").read(), "    function recRunEnd(ls) {", "    function previewHtml(d) {", "ceo.html"),
    ]
    if any(x is None for x in segs):
        return
    eng = _js_engine()
    if not eng:
        bad("JS の実行環境 (node / osascript) が無い — 📺 行の組み立てを実行して確かめられない")
        return
    stubs = ("function escapeHtml(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;')"
             ".replace(/>/g, '&gt;').replace(/\"/g, '&quot;'); }\nvar esc = escapeHtml;\n"
             "var SP_SUBJ_JA = { english: '英語' };\n")
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "rec_check.js")
        with open(path, "w", encoding="utf-8") as f:
            f.write(stubs + "\n".join(segs) + "\n" + _JS_REC_CASES)
        try:
            r = subprocess.run(eng + [path], capture_output=True, text=True, timeout=120)
        except Exception as e:
            bad(f"JS の実行に失敗 ({type(e).__name__})")
            return
    outp = (r.stdout or "").strip()
    if r.returncode != 0 or not outp:
        bad(f"JS が失敗した (exit {r.returncode}): {(r.stderr or '')[:400]}")
        return
    lines = outp.split("\n")
    for l in lines:
        if l.startswith("NG"):
            bad(l[4:])
    if len(problems) == n0:
        good(f"{len(lines)} 件 OK ({eng[0]}): 範囲は講番号が続くときだけ・画面は講座名と第N講を分ける (3 画面とも)")


def _fn_src(src, tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(src, node) or ""
    return None


def check_stage_b(src, tree):
    """[9] 段階 B の構造 (講データの表・取込 API の認証・照合の接続・ログ)。"""
    print("\n[9] 段階 B (講データの表・取込 API・照合の接続・ログに題名を出さない)")
    n0 = len(problems)
    m = re.search(r'_schema_sql = f"""(.*?)"""', src, re.S)
    schema = m.group(1) if m else ""
    for tbl, cols in (("sapuri_lessons", ("lesson_key", "course_code", "seq", "title", "active")),
                      ("sapuri_lesson_tags", ("course_code", "lesson_key", "subject_key", "tag")),
                      ("sapuri_topic_lessons", ("course_code", "subject_key", "topic_norm", "lesson_key"))):
        mm = re.search(r"CREATE TABLE IF NOT EXISTS " + tbl + r" \((.*?)\);", schema, re.S)
        if not mm:
            bad(f"_schema_sql に {tbl} の CREATE TABLE が無い")
            continue
        body = mm.group(1)
        for col in cols:
            if not re.search(r"\b" + col + r"\b", body):
                bad(f"{tbl} に列 {col} が無い")
        if re.search(r"\bstudent_id\b", body):
            bad(f"{tbl} に student_id 列がある (生徒の削除・統合の一覧に足す必要が出る。講データは生徒に紐づけない)")
    if "ON sapuri_lessons(lesson_key)" not in schema:
        bad("sapuri_lessons(lesson_key) の UNIQUE INDEX が無い (取込の ON CONFLICT(lesson_key) が効かない)")
    imp = _fn_src(src, tree, "admin_sapuri_lessons_import")
    if imp is None:
        bad("取込 API admin_sapuri_lessons_import が無い")
    else:
        if "_verify_admin_required(authorization)" not in imp:
            bad("取込 API が _verify_admin_required で認証していない")
        if "x_cron_secret" in imp or "_grammar_admin_authed" in imp or "CRON_SECRET" in imp:
            bad("取込 API が cron の合言葉を受け付けている (GitHub Actions から叩く経路を作らない)")
    for fname, must in (("student_weakness_top3", "_sapuri_attach_top3(student_id, weaknesses, pool)"),
                        ("_run_weekly_worksheet_generation", "_sapuri_for_subject_topics(sid, sgrade, subject_topics)")):
        body = _fn_src(src, tree, fname) or ""
        if must not in body:
            bad(f"{fname} が {must} を呼んでいない")
        if re.search(r"_sapuri_recommend\(\s*c\b|_sapuri_\w+\(\s*c\s*,", body):
            bad(f"{fname} が共有カーソル c を照合に渡している (Postgres で 1 文の失敗がトランザクションを壊す)")
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith(("_sapuri", "admin_sapuri", "student_class_sapuri")):
            seg = ast.get_source_segment(src, node) or ""
            for line in seg.split("\n"):
                if re.search(r"\blog\.(info|warning|error|debug)\(", line) and re.search(r"title|題名|\blessons\[", line):
                    bad(f"{node.name}: ログに題名を出している気配: {line.strip()[:80]}")
    if len(problems) == n0:
        good("3 表 (student_id なし・lesson_key の UNIQUE)・取込は管理者 Bearer だけ・照合は自分の接続・ログに題名なし")


def main():
    print("📺 スタサプ講座カタログ ゲート (server/main.py を ast で検査)\n")
    src, tree, K = load_consts()
    courses = K.get("SAPURI_COURSES") or []
    by_code = {}

    print("[1] SAPURI_COURSES")
    n0 = len(problems)
    for c in courses:
        code = c.get("code")
        if set(c) != KEYS:
            bad(f"{code}: 項目が違う ({sorted(set(c) ^ KEYS)})")
            continue
        if code in by_code:
            bad(f"{code}: code が重複")
        by_code[code] = c
        first, last, total = c["first"], c["last"], c["total_lessons"]
        if c["level"] == "共通テスト":
            if (first, last, total) != (0, 0, 0) or c["has_lessons"]:
                bad(f"{code}: 共通テスト対策は講数非公開 (first=last=total=0・has_lessons=False) のはず")
        else:
            if not (1 <= first <= last):
                bad(f"{code}: first ≤ last でない ({first}..{last})")
            if total < last - first + 1 or total > last - first + 2:
                bad(f"{code}: total_lessons={total} が範囲 {first}..{last} と合わない (補講 1 本まで)")
        if c["level"] not in LEVELS:
            bad(f"{code}: level {c['level']!r} が語彙外")
        if c["band"] not in BANDS:
            bad(f"{code}: band {c['band']!r} が語彙外")
        if c["subject"] not in SUBJECTS:
            bad(f"{code}: subject {c['subject']!r} が語彙外")
        if not (isinstance(c["dev_min"], int) and isinstance(c["dev_max"], int) and c["dev_min"] < c["dev_max"]):
            bad(f"{code}: dev_min < dev_max でない")
        for k in ("name", "field", "notes"):
            v = str(c[k])
            if "講師" in v or "先生" in v:
                bad(f"{code}: {k} に講師名の気配 (講師/先生)")
            # 公開ラインナップは講数の後ろに講師の姓を「24講（◯◯）」と書く。写していないか (漢字 1〜4 字だけのかっこ)
            if re.search(r"\d+\s*講\s*[（(]\s*[一-龥々]{1,4}\s*[)）]", v):
                bad(f"{code}: {k} の講数の後ろに姓のようなかっこ書き (講師名を写していないか)")
        if "題名" in str(c["notes"]):
            bad(f"{code}: notes に講の題名の話が書かれている (D1: 題名は本番 DB だけ)")
    if len(problems) == n0 and courses:
        good(f"{len(courses)} 講座: code 一意・講番号の範囲・語彙・講師名なし")

    print("\n[2] SAPURI_COVERS")
    skeys = tuple(K.get("SAPURI_SUBJECT_KEYS") or ())
    vocab = K.get("SAPURI_TAG_VOCAB") or {}
    covers = K.get("SAPURI_COVERS") or {}
    tier1 = K.get("SAPURI_COVERS_TIER1_ONLY") or {}
    n0 = len(problems)
    for label, table in (("SAPURI_COVERS", covers), ("SAPURI_COVERS_TIER1_ONLY", tier1)):
        for code, m in table.items():
            c = by_code.get(code)
            if not c:
                bad(f"{label}: {code} が SAPURI_COURSES に無い")
                continue
            if c["total_lessons"] <= 0 or c["field"] in ("共通テスト", "中学総復習") or code.endswith("_2"):
                bad(f"{label}: {code} ({c['field']}) は講座選びの母集団に入れない (共通テスト/中学総復習/総合問題編)")
            for sk, tags in m.items():
                if sk not in skeys:
                    bad(f"{label}: {code} の科目キー {sk} が SAPURI_SUBJECT_KEYS に無い")
                    continue
                if tags != "*" and (not isinstance(tags, list) or not tags or not set(tags) <= set(vocab.get(sk, []))):
                    bad(f"{label}: {code} の {sk} のタグが語彙外 ({tags})")
    for code in set(covers) & set(tier1):
        bad(f"{code} が SAPURI_COVERS と TIER1_ONLY の両方にある")
    for code, m in tier1.items():
        c = by_code.get(code)
        if c and c["field"] != "文化史":
            bad(f"SAPURI_COVERS_TIER1_ONLY: {code} の field が {c['field']} (文化史だけを置く)")
        for sk in m:
            if not any(sk in mm and by_code.get(cc, {}).get("field") == "通史" for cc, mm in covers.items()):
                bad(f"SAPURI_COVERS_TIER1_ONLY: {code} の {sk} に通史の講座 (SAPURI_COVERS) が無い")
    for code, c in by_code.items():
        if c["field"].startswith("史料") and (code in covers or code in tier1):
            bad(f"{code} (史料・テーマ史) を照合に使っている (段階 B の決定: 使わない)")
    for sk in skeys:
        bands = {by_code[code]["band"] for code, m in covers.items() if sk in m and code in by_code}
        exc = _BAND_EXCEPTIONS.get(sk, ())
        if not (bands & {"高3", "全学年"}) and "高3" not in exc:
            bad(f"科目キー {sk} に 高3 (または全学年) の講座が無い (無いのが正しいなら _BAND_EXCEPTIONS に理由つきで)")
        if not (bands & {"高1・2", "全学年"}) and "高1・2" not in exc:
            bad(f"科目キー {sk} に 高1・2 (または全学年) の講座が無い (無いのが正しいなら _BAND_EXCEPTIONS に理由つきで)")
    if len(problems) == n0:
        good(f"{len(covers)} 講座 (+ 文化史 {len(tier1)}): 実在・語彙内・{len(skeys)} 科目キーとも 高3 / 高1・2 の講座あり")

    print("\n[3] タグの語彙と別名")
    n0 = len(problems)
    if set(vocab) != set(skeys):
        bad(f"SAPURI_TAG_VOCAB の科目キーが SAPURI_SUBJECT_KEYS と違う ({sorted(set(vocab) ^ set(skeys))})")
    for sk, tags in vocab.items():
        if len(tags) != len(set(tags)):
            bad(f"SAPURI_TAG_VOCAB[{sk}] にタグの重複")
    for sk, amap in (K.get("SAPURI_TAG_ALIASES") or {}).items():
        if sk not in vocab:
            bad(f"SAPURI_TAG_ALIASES の科目キー {sk} が語彙に無い")
            continue
        for a, vals in amap.items():
            if a in vocab[sk]:
                bad(f"SAPURI_TAG_ALIASES[{sk}] の別名 {a} が語彙そのもの (別名にしない)")
            if not vals or not set(vals) <= set(vocab[sk]):
                bad(f"SAPURI_TAG_ALIASES[{sk}][{a}] の値 {vals} が語彙外")
    for a, v in (K.get("_UNIT_TAG_ALIASES") or {}).items():
        if v not in vocab.get("eng_grammar", []):
            bad(f"_UNIT_TAG_ALIASES[{a}] = {v} が英文法の語彙に無い")
    mt = K.get("SAPURI_MATH_TAG_FIELD") or {}
    if set(mt) != set(vocab.get("math", [])):
        bad(f"SAPURI_MATH_TAG_FIELD のタグが数学の語彙と違う ({sorted(set(mt) ^ set(vocab.get('math', [])))})")
    if len(problems) == n0:
        good("語彙・別名 (SAPURI_TAG_ALIASES / _UNIT_TAG_ALIASES)・数学のタグ → 科目の表が整合")

    print("\n[4] 対象クラス (D2)")
    n0 = len(problems)
    declared = tuple(K.get("_SAPURI_COURSE_LABELS_DECLARED") or ())
    runtime = (K.get("_COURSE_CLASSES") or {}).get(K.get("_SAPURI_COURSE_NAME"))
    if len(declared) != 3 or runtime is None or sorted(declared) != sorted(runtime):
        bad(f"_SAPURI_COURSE_LABELS_DECLARED {declared} が _COURSE_CLASSES[{K.get('_SAPURI_COURSE_NAME')!r}] {runtime} と違う")
    if len(problems) == n0:
        good(f"宣言の 3 ラベル = _COURSE_CLASSES[{K.get('_SAPURI_COURSE_NAME')}]")

    print("\n[5] 旧名の対応 (SAPURI_LEGACY_NAME_TO_CODE と app.js の SAPURI_LEGACY_CAPS)")
    n0 = len(problems)
    legacy = K.get("SAPURI_LEGACY_NAME_TO_CODE") or {}
    for name, codes in legacy.items():
        for code in codes:
            if code not in by_code:
                bad(f"SAPURI_LEGACY_NAME_TO_CODE[{name}] の {code} が SAPURI_COURSES に無い")
    js = open(APP_JS, encoding="utf-8").read()
    m = re.search(r"const SAPURI_LEGACY_CAPS = \{\n(.*?)\n\};", js, re.S)
    caps = {}
    if not m:
        bad("app.js に const SAPURI_LEGACY_CAPS = {…}; が無い")
    else:
        for line in m.group(1).split("\n"):
            mm = re.match(r'\s*"([^"]+)":\s*\[(\d+),\s*(\d+)\],\s*$', line)
            if not mm:
                bad(f"app.js SAPURI_LEGACY_CAPS の読めない行: {line.strip()[:60]}")
                continue
            caps[mm.group(1)] = (int(mm.group(2)), int(mm.group(3)))
        by_stripped = {}
        for name, codes in legacy.items():
            by_stripped.setdefault(norm(re.sub(r"^高[123]\s*", "", name)), set()).update(codes)
        for k, (a, b) in caps.items():
            if not (1 <= a <= b):
                bad(f"app.js SAPURI_LEGACY_CAPS[{k}] = [{a}, {b}] が不正")
            codes = [x for x in by_stripped.get(norm(k), ()) if x in by_code and by_code[x]["last"] > 0]
            if codes:
                want = (min(by_code[x]["first"] for x in codes), max(by_code[x]["last"] for x in codes))
                if (a, b) != want:
                    bad(f"app.js SAPURI_LEGACY_CAPS[{k}] = [{a}, {b}] がカタログ ({sorted(codes)} → {list(want)}) と違う")
        mt2 = re.search(r"const TEXTBOOK_TOTAL_UNITS = \{(.*?)\n\};", js, re.S)
        tb_keys = set(re.findall(r"'([^']+)':\s*\d+", mt2.group(1))) if mt2 else set()
        dup = {k for k in tb_keys if norm(k) in {norm(x) for x in caps}}
        if dup:
            bad(f"app.js TEXTBOOK_TOTAL_UNITS にスタサプの旧名の鍵が残っている: {sorted(dup)[:5]}")
        if "server/main.py の SAPURI_LEGACY_NAME_TO_CODE" not in js:
            bad("app.js の SAPURI_LEGACY_CAPS に出所 (server/main.py の SAPURI_LEGACY_NAME_TO_CODE) の注記が無い")
    if len(problems) == n0:
        good(f"旧名 {len(legacy)} 件の code が実在・app.js の静的表 {len(caps)} 件がカタログの写しと一致")

    print("\n[6] 旧初期データ・表の読み書きが残っていない")
    n0 = len(problems)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "SAPURI_LECTURES_SEED":
            bad(f"SAPURI_LECTURES_SEED の参照が残っている (行 {node.lineno})")
    for node in tree.body:   # 起動時 (module 直下) の呼び出し
        for sub in ast.walk(node) if isinstance(node, (ast.Expr, ast.Try)) else ():
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id in (
                    "_seed_sapuri_lectures", "_cleanup_old_sapuri_lectures"):
                bad(f"起動時に {sub.func.id}() を呼んでいる (行 {sub.lineno})")
    if re.search(r"(?:SELECT\b[^\"';]*\bFROM\s+sapuri_lectures|INSERT\s+INTO\s+sapuri_lectures)", src, re.I):
        bad("sapuri_lectures 表を SELECT / INSERT する箇所が残っている (講座の正典は SAPURI_COURSES)")
    if len(problems) == n0:
        good("SAPURI_LECTURES_SEED の参照なし・起動時の投入なし・sapuri_lectures を読む箇所なし")

    print("\n[7] 講の題名をリポジトリに置かない (D1)")
    n0 = len(problems)
    try:
        files = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout.split("\n")
    except Exception as e:
        files = None
        bad(f"git ls-files が読めない ({type(e).__name__}) — 確かめられない")
    if files is not None:
        hits = [f for f in files if re.search(r"(^|/)high_category[^/]*\.tsv$|(^|/)sapuri_lessons_[^/]*\.json$|(^|/)sapuri_import/", f)]
        for f in hits:
            bad(f"講の題名の元データ・取込ファイルがリポジトリにある: {f}")
        if len(problems) == n0:
            good(f"high_category*.tsv / sapuri_lessons_*.json / sapuri_import/ はリポジトリに無い ({len([f for f in files if f])} ファイル)")

    check_stage_b(src, tree)

    check_appjs_caps_runtime(courses)

    check_front_rec_runtime()

    print()
    if problems:
        print(f"違反 {len(problems)} 件")
        return 1
    print("✅ スタサプ講座カタログ: 違反なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
