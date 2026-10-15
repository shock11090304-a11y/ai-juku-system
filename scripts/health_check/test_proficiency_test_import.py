#!/usr/bin/env python3
"""🧪 習熟度テスト (科目 proficiency_test) の取込・出題順・自動配信からの除外の回帰テスト (2026-10-15 塾長決定)。

習熟度テストは Codex が作ったファイル (1 ファイル = 1 回分・番号は 1 始まり) を取込スクリプトが 0 始まりに直して送る。
1 回分 = 1 単元 (大問 1 つ = 本文 1 つ)。塾長が CEO で配り、全大問を出題順のまま 1 本のドリルにする。自動配信には一切出さない。
送る形は取込スクリプト scripts/drill_import/import_drill_file.py の build_payloads (通信しない純関数) で作る (中身はすべて架空・_fixture)。

  (1) 取込: 大問 3・設問 9 が入る・kv_settings 'ptest_meta:<単元>' (大問数・設問数・skill)
  (2) 1 始まり → 0 始まり: DB の choices[answer] がファイルの choices[correct_choice_no - 1] と全問一致
  (3) 拒否: 単元名の形違い (errors + unknown_units)・questions[] (422)・review なし (422)・大問 13 / 設問 61 (422)・
      ptest_meta の skill が単元ドリルに無い / 設問がテストに無い / 2 回分まとめて (422)・dry_run は kv も書かない
  (4) 取込済みの単元に新しい本文 → ok:false・同じ要求の再送 → already_imported・「第1回改1」は入る
  (5) 配信: passage_count・levels は無視して全大問を取込順・設問はファイルの qid 順 (5 回とも同じ)・題名「🧪 …（全N問）」・
      exclude_drill_id と単元なしは 422・同じ生徒への 2 回目は already_taken・全員なら 409 (ドリルを作らない)・allow_retake
  (6) 👀 プレビュー: 本数・レベルの指定に関わらずテスト全体を出題順に答えつきで
  (7) 生徒の取得は答えを伏せる・正解どおりに出すと満点・分析の名簿と問題別正答率
  (8) 解答は subject='proficiency_test'・topic=単元 → 弱点にならない / PTEST_FEEDS_WEAKNESS=1 なら skill つきの誤答が
      english/関係詞 の解答と弱点になり、skill なしは proficiency_test のまま
  (9) 習熟度テストしか無い DB: 今日の1問・初回診断は 503・3日ドリルは配らない・1 問ずつ / 本文の自動の抽出は 0
      (env AUTO_DELIVERY_REVIEWED_SOURCES で proficiency_test=* と書いても)
  (10) 英検の本文の順は今もランダム (ORDER BY id は習熟度テストだけ)
  (11) CEO の配信済み一覧 subject=proficiency_test はテストだけ・単元一覧は 高校/中学・回・改 の順
  (12) 自動配信の関数のソースに proficiency_test / _PTEST_SUBJECT が出てこない (許可リストに入れていない静的な確認)・
      お知らせのメールの件名「🧪 習熟度テスト「…」が届きました」
  (13) 取込スクリプトの往復: scripts/drill_import/fixtures の ok_proficiency_test / ok_english_long を、取込スクリプト (run) で
      試運転 → --apply → 読み返し (通信は TestClient に差し替え)。DB の全問が 1 始まり → 0 始まりで一致・ptest_meta の skill・
      再送は「取込済み」で増えない・リポジトリの中のファイルは送らない・記録 (import_log) に秘密が無い
  (14) 画面 (CEO・塾生アプリ・マイページ): CEO ① の科目に 📖 英語長文・🧪 習熟度テスト (= サーバの科目すべて)・ラベル表 7 か所・
      ceo.html / class.html / mypage.js の本物のコードを JS エンジン (node → osascript → jsc。無ければ FAIL) で動かす:
      学年の確認 _gdGradeMismatchText(subject, students, unit) はテストの単元名の「中学」「高校」で分ける・④ は隠して
      「テスト全体 (大問N・全M問)」・単元チップ「🧪 大問N・M問」・配信は本数・問題数・弱点対策を送らない・飛ばした生徒の名前 (escape)・
      409 は黄色・在庫 0 の英語長文は送らない・塾生アプリのカード「授業の指示どおりに解いて提出 ・ 提出は1回だけ」・マイページのカード

実行:
    python3 scripts/health_check/test_proficiency_test_import.py
    # exit 0 = PASS / 1 = FAIL

外部通信はしない。DB は一時 SQLite。生徒名・メール・テストの中身は架空 (公開リポジトリ・テストの本物は置かない)。
"""
import base64
import copy
import datetime
import hashlib
import hmac
import importlib.util
import inspect
import io
import json
import os
import random
import re
import shutil
import sys
import tempfile
import time
import urllib.parse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
DRILL_IMPORT = os.path.join(REPO, "scripts", "drill_import")
CEO_HTML = os.path.join(REPO, "ceo.html")
CLASS_HTML = os.path.join(REPO, "class.html")
MYPAGE_JS = os.path.join(REPO, "mypage.js")
MYPAGE_HTML = os.path.join(REPO, "mypage.html")
STUDENT_MODE_JS = os.path.join(REPO, "student-mode.js")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "server"))
from test_grade_band_consistency import js_engine, run_js  # noqa: E402  (JS エンジンの選び方は 3 本のテストで同じ)

FAILURES = []
CIRCLED = "①②③④⑤⑥⑦⑧"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="ptest_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと **本番 Postgres** に書き込む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "",
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
        "BASE_URL": "https://example.invalid",
        "CRON_SECRET": "test-cron-secret",
    })
    for k in ("AUTO_DELIVERY_REVIEWED_SOURCES", "HOMEWORK_NOTIFY_LINE", "PTEST_FEEDS_WEAKNESS"):
        os.environ.pop(k, None)
    os.environ["HOMEWORK_NOTIFY_EMAIL"] = "off"   # 配信のたびのお知らせ (メール) は回さない。件名は [12] で直接確かめる
    spec = importlib.util.spec_from_file_location("aijuku_main_ptest", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def load_importer():
    """取込スクリプト (scripts/drill_import/import_drill_file.py)。読み込むと隣の検査スクリプトも読む。通信は HTTP を差し替えるまでしない。"""
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("import_drill_file_ptest", os.path.join(DRILL_IMPORT, "import_drill_file.py"))
    imp_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(imp_mod)
    sys.dont_write_bytecode = False
    return imp_mod


IMP = load_importer()


def admin_token(mod, hours=1):
    exp = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)).timestamp())
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), f"admin.{exp}".encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


def student_token(mod, sid, hours=1):
    exp = int(time.time()) + hours * 3600
    payload = f"session.{sid}.{exp}"
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}.{sig}".encode()).decode().rstrip("=")


def q(mod, sql, params=()):
    conn = mod.db(); c = conn.cursor()
    c.execute(sql, params)
    out = [dict(r) for r in c.fetchall()]
    conn.close()
    return out


def ex(mod, sql, params=()):
    conn = mod.db(); c = conn.cursor()
    c.execute(sql, params)
    conn.commit(); conn.close()


def counts(mod):
    return {t: q(mod, f"SELECT COUNT(*) AS n FROM {t}")[0]["n"]
            for t in ("grammar_passages", "grammar_questions", "grammar_drills", "grammar_drill_assignments")}


class Env:
    def __init__(self, **kv):
        self.kv = kv

    def __enter__(self):
        self.old = {k: os.environ.get(k) for k in self.kv}
        for k, v in self.kv.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return self

    def __exit__(self, *a):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def ptest_doc(test_id="HSENG01", round_=1, revision=0, per=(3, 2, 4), target="kosei", subject_ja="英語"):
    """仕様書 (trillion-drill-import/v1) の形の架空のテスト。correct_choice_no は 1 始まり。"""
    sections, qn = [], 0
    for s, n in enumerate(per, 1):
        qs = []
        for _ in range(n):
            qn += 1
            ch = [f"架空の選択肢 {test_id} {qn}-{x}" for x in "abcd"]
            cno = (qn * 3) % 4 + 1
            qs.append({"qid": f"Q{qn:02d}", "stem": f"架空の設問 {test_id} 第{s}問 {qn}", "choices": ch, "correct_choice_no": cno,
                       "explanation": f"正解 {CIRCLED[cno - 1]} {ch[cno - 1]}\n【解説】架空\n【他の選択肢】\n…",
                       "skill": {"subject": "english", "unit": "関係詞"} if qn == 2 else None})
        sections.append({"section_no": s, "title": f"第{s}問", "body": f"第{s}問 架空の指示文 {test_id} 第{round_}回",
                         "body_ja": None, "questions": qs})
    return {"format": "trillion-drill-import/v1", "kind": "proficiency_test", "_fixture": True, "test_id": test_id,
            "target": target, "subject": "english", "subject_ja": subject_ja, "series_ja": "習熟度テスト", "round": round_,
            "revision": revision, "title": f"架空 習熟度テスト 第{round_}回", "time_limit_min": 60, "sections": sections,
            "_review": {"protocol": "trillion-blind/v1", "blind": {"dropped_qids": [], "solvers": [
                {"label": x, "kind": "ai", "date": "2026-10-21", "answers_file": f"_review/blind_{x}.json"} for x in "ABC"]}}}


def unit_of(doc):
    return (f"{'高校' if doc['target'] == 'kosei' else '中学'}{doc['subject_ja']} {doc['series_ja']} 第{doc['round']}回"
            + (f"改{doc['revision']}" if doc.get("revision") else ""))


def to_payload(doc):
    """取込スクリプトの build_payloads で送る形にする (1 始まり → 0 始まり・出典 pt-<test_id>-<qid> / 本文 ptest:<test_id>:S<nn>・
    skill は ptest_meta へ)。1 回分 = 1 要求。"""
    pls = IMP.build_payloads(doc, "0" * 64)
    assert len(pls) == 1, len(pls)
    return pls[0]


def _rd(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _js_block(src, head, end="\n    }\n"):
    """src の head から、同じ字下げで閉じる } までを切り出す (無ければ '')。"""
    i = src.find(head)
    if i < 0:
        return ""
    j = src.find(end, i)
    return src[i:j + len(end)] if j > i else ""


def _js_between(src, a, b):
    i = src.find(a)
    j = src.find(b, i + 1) if i >= 0 else -1
    return src[i:j] if 0 <= i < j else ""


def _js_line(src, head):
    i = src.find(head)
    return src[i:src.find("\n", i)] if i >= 0 else ""


def check_screens(mod):
    """[14] 画面: CEO の ① 科目・④・学年の確認・配信 / 塾生アプリのカード / マイページのカードとラベル (2026-10-15)。
    ceo.html / class.html / mypage.js の本物のコードを切り出して JS エンジンで動かす (偽の DOM・偽の fetch・名前に HTML を入れて escape を確かめる)。"""
    print("\n[14] 画面: CEO ① 科目・④・学年の確認・配信 / 塾生アプリのカード / マイページ")
    ceo, cls, myjs, myhtml = _rd(CEO_HTML), _rd(CLASS_HTML), _rd(MYPAGE_JS), _rd(MYPAGE_HTML)

    i_sel = ceo.find('<select id="gdSubject"')
    opts = set(re.findall(r'<option value="([a-z_]+)"', ceo[i_sel:ceo.find("</select>", i_sel)])) if i_sel >= 0 else set()
    check("CEO ① 科目の選択肢 = サーバの科目すべて (📖 英語長文・🧪 習熟度テストを含む)",
          opts == set(mod._GRAMMAR_CANON_SUBJECTS), sorted(opts ^ set(mod._GRAMMAR_CANON_SUBJECTS)))
    want = {k: mod._GRAMMAR_SUBJECT_LABEL_JA[k] for k in ("english_long", "proficiency_test")}
    tables = [("ceo.html _GD_SUBJ_JA (配信済み一覧・🎯 確認カード)", ceo, "const _GD_SUBJ_JA = {"),
              ("ceo.html _gdGradeMismatchText の科目名", ceo, "const _subjJa = {"),
              ("ceo.html やるべきこと SUBJ", ceo, "const SUBJ = { english: '英語'"),
              ("ceo.html _SJ_LABEL (📨 の対象外の注記)", ceo, "var _SJ_LABEL = {"),
              ("class.html GD_SUBJ_JA (宿題カードの科目チップ)", cls, "var GD_SUBJ_JA = {"),
              ("mypage.js _SUBJ_DRILL_LABEL (宿題カード)", myjs, "const _SUBJ_DRILL_LABEL = {"),
              ("mypage.html subjectLabel (弱点 TOP3)", myhtml, "const subjectLabel = {")]
    for name, src_, head in tables:
        i = src_.find(head)
        body = src_[i:src_.find("};", i)] if i >= 0 else ""
        got = {}
        for k in want:
            m = re.search(r"\b" + k + r":\s*'([^']*)'", body)
            got[k] = m.group(1) if m else None
        check(f"{name} に英語長文・習熟度テストのラベル", i >= 0 and all(got[k] and want[k] in got[k] for k in want), got)
    check("_gdGradeMismatchText は 3 引数 (subject, students, unit)", "function _gdGradeMismatchText(subject, students, unit) {" in ceo)
    check("📤 配信 (gdCreate) は単元を渡す", re.search(r"_gdGradeMismatchText\(_gdSubject \|\| 'english', [^\n]*, _gdSelUnit\)", ceo) is not None)
    check("📨 弱点ドリル (_assignWeaknessDrill) は今までどおり 2 引数",
          "window._gdGradeMismatchText(subject, [{ id: Number(sid), name: sname, grade }])" in ceo)
    pre = "^(高校|中学)(英語|数学|国語|理科|社会)"
    check("テストの単元名の頭 (高校/中学 + 教科) はサーバ _PTEST_UNIT_RE と同じ形 (マイページの復習カードの教科もこれで読む)",
          mod._PTEST_UNIT_RE.pattern.startswith(pre) and "/" + pre + "/" in myjs, mod._PTEST_UNIT_RE.pattern)

    esc_line = _js_line(ceo, "    function escapeHtml(s) {")
    parts = {
        "ceo gdCurrentLevels": _js_block(ceo, "    function gdCurrentLevels() {"),
        "ceo 単元チップと④": _js_between(ceo, "    const _GD_PASSAGE_ONLY = ", "    function gdSelUnit("),
        "ceo 学年の確認": _js_between(ceo, "    function _gdMode(grade) {", "    function gdFilterStudents("),
        "ceo gdCreate": _js_block(ceo, "    async function gdCreate() {"),
        "class esc": _js_block(cls, "    function esc(s) {"),
        "class _pad2": _js_line(cls, "    function _pad2(n) {"),
        "class gdIsOpen": _js_line(cls, "    function gdIsOpen(x) {"),
        "class gdLocalDate": _js_block(cls, "    function gdLocalDate(s, withTime) {"),
        "class gdMetaText": _js_block(cls, "    function gdMetaText(it) {"),
        "mypage _hwEscape": _js_block(myjs, "function _hwEscape(s) {", "\n}\n"),
        "mypage _hwIsNew": _js_line(myjs, "function _hwIsNew(map, id) {"),
        "mypage _SUBJ_DRILL_LABEL": _js_line(myjs, "const _SUBJ_DRILL_LABEL = {"),
        "mypage _gdLevelJa": _js_block(myjs, "function _gdLevelJa(lv) {", "\n}\n"),
        "mypage _renderDrillAsHwItem": _js_block(myjs, "function _renderDrillAsHwItem(item) {", "\n}\n"),
    }
    check("画面のコードを切り出せた", esc_line and all(parts.values()), [k for k, v in parts.items() if not v])
    eng = js_engine()
    check("JS の実行環境がある (node / osascript / jsc。無ければ FAIL)", bool(eng))
    if not eng or not all(parts.values()):
        return
    ku, cu = "高校英語 習熟度テスト 第1回", "中学英語 習熟度テスト 第1回"
    prog = "\n".join([
        "var window = (typeof globalThis !== 'undefined') ? globalThis : this;",
        "(function () {", _rd(STUDENT_MODE_JS), "})();",
        esc_line,
        "var __els = {};",
        "function __el(id) { if (!__els[id]) __els[id] = { id: id, value: '', innerHTML: '', textContent: '', style: {}, dataset: {} }; return __els[id]; }",
        "var __checked = [];",
        "var document = { getElementById: function (id) { return __el(id); }, querySelectorAll: function (sel) {"
        " return sel === '.gd-st:checked' ? __checked.map(function (v) { return { value: String(v), checked: true }; }) : []; } };",
        "var __confirms = [], __confirmAnswer = true;",
        "function confirm(t) { __confirms.push(String(t)); return __confirmAnswer; }",
        "var __posts = [], __resp = null;",
        "var AdminAuth = { fetch: function (path, opt) { __posts.push({ path: path, body: JSON.parse((opt && opt.body) || '{}') }); return Promise.resolve(__resp); } };",
        "function __r(status, body) { return { ok: status >= 200 && status < 300, status: status, json: function () { return Promise.resolve(body); } }; }",
        "function gdSelectAll() {} function gdRefresh() {}",
        "var _gdCreating = false, _gdSelUnit = null, _gdSubject = 'english', _gdUnits = [], _gdStudents = [], _gdExcludeDrillId = null;",
        "function _gdClearRemediation() { _gdExcludeDrillId = null; }",
        parts["ceo gdCurrentLevels"], parts["ceo 単元チップと④"], parts["ceo 学年の確認"], parts["ceo gdCreate"],
        parts["class esc"], parts["class _pad2"], parts["class gdIsOpen"], parts["class gdLocalDate"], parts["class gdMetaText"],
        parts["mypage _hwEscape"], parts["mypage _hwIsNew"],
        "var _hwNewIds = { d: {}, h: {} }, _HW_NEW_BADGE = '<b>NEW</b>';",
        "function _gdRich(t) { return _hwEscape(t); }",
        parts["mypage _SUBJ_DRILL_LABEL"], parts["mypage _gdLevelJa"], parts["mypage _renderDrillAsHwItem"],
        f"var KU = {json.dumps(ku, ensure_ascii=False)}, CU = {json.dumps(cu, ensure_ascii=False)};",
        "var STU = [{ id: 1, name: '架空 高校生', grade: '高2' }, { id: 2, name: '架空 中学生', grade: '中２' },"
        " { id: 3, name: '架空 未設定', grade: '' }, { id: 4, name: '架空 小学生', grade: '小６' }];",
        "var __o = {};",
        "function __sync() { return [__el('gdCountWrap').style.display, __el('gdPassageCountWrap').style.display, __el('gdPtestWrap').style.display, __el('gdPtestText').textContent]; }",
        "__o.mmPtK = _gdGradeMismatchText('proficiency_test', STU, KU);",
        "__o.mmPtC = _gdGradeMismatchText('proficiency_test', STU, CU);",
        "__o.mmPtNoUnit = _gdGradeMismatchText('proficiency_test', STU);",
        "__o.mmLong = _gdGradeMismatchText('english_long', STU, '長文 Lv.1');",
        "__o.mmEiken = _gdGradeMismatchText('eiken', STU, '2級 単語');",
        "__o.mmChu = _gdGradeMismatchText('chugaku', STU);",
        "__o.mmEngOk = _gdGradeMismatchText('english', [STU[0], STU[2]], '時制');",
        "_gdSubject = 'proficiency_test';",
        "_gdUnits = [{ unit: KU, basic: 0, standard: 9, advanced: 0, total: 9, passages: 3 }, { unit: '高校英語 習熟度テスト 第2回<b>', total: 0, passages: 0 }];",
        "_gdSelUnit = null; gdRenderUnits(); __o.chips = __el('gdUnits').innerHTML; __o.syncNoSel = __sync();",
        "_gdSelUnit = KU; _gdSyncCountInputs(); __o.syncSel = __sync();",
        "_gdSubject = 'english_long'; _gdUnits = [{ unit: '長文 Lv.1', total: 10, passages: 2 }, { unit: '長文 Lv.2', total: 0, passages: 0 }];",
        "_gdSelUnit = '長文 Lv.2'; gdRenderUnits(); __o.longChips = __el('gdUnits').innerHTML; __o.syncLong = __sync();",
        "_gdSubject = 'english'; _gdUnits = [{ unit: '時制', basic: 0, standard: 30, advanced: 0, total: 30, passages: 0 }];",
        "_gdSelUnit = '時制'; gdRenderUnits(); __o.syncEng = __sync();",
        "__o.metaPt = gdMetaText({ subject: 'proficiency_test', title: '🧪 ' + KU + '（全9問）', status: 'open', score_total: 9, assigned_at: '2026-10-16 00:00:00' });",
        "__o.metaPtAssigned = gdMetaText({ subject: 'proficiency_test', title: 'テスト', status: 'assigned', score_total: 9 });",
        "__o.metaEng = gdMetaText({ subject: 'english', title: '時制ドリル（標準・10問）', status: 'open', score_total: 10 });",
        "__o.metaDone = gdMetaText({ subject: 'proficiency_test', title: 'テスト', status: 'completed', score_correct: 7, score_total: 9 });",
        "__o.cardPt = _renderDrillAsHwItem({ drill_id: 5, subject: 'proficiency_test', unit: KU, level: 'basic,standard,advanced', title: '🧪 ' + KU + '（全9問）', status: 'open' });",
        "__o.cardPtDone = _renderDrillAsHwItem({ drill_id: 5, subject: 'proficiency_test', unit: KU, level: 'basic,standard,advanced', title: 'テスト', status: 'completed', score_correct: 7, score_total: 9 });",
        "__o.cardLong = _renderDrillAsHwItem({ drill_id: 6, subject: 'english_long', unit: '長文 Lv.1', level: 'standard', title: '長文 Lv.1ドリル（本文2本・8問）', status: 'open' });",
        "function __out() { var __s = 'RESULT ' + JSON.stringify(__o);",
        "  if (typeof process !== 'undefined' && typeof console !== 'undefined' && console.log) console.log(__s);",
        "  else if (typeof print === 'function') print(__s);",
        "  else if (typeof console !== 'undefined' && console.log) console.log(__s); }",
        "(async function () {",
        "  try {",
        # (a) テスト: 本数・問題数・弱点対策の除外を送らない。飛ばした生徒の名前は escape
        "  _gdSubject = 'proficiency_test'; _gdUnits = [{ unit: KU, total: 9, passages: 3 }]; _gdSelUnit = KU;",
        "  __el('gdLevel').value = 'adv'; __el('gdCount').value = '30'; __el('gdPassageCount').value = '4';",
        "  _gdStudents = STU; __checked = [1, 3]; _gdExcludeDrillId = 77;",
        "  __resp = __r(200, { ok: true, message: '✅ ドリル「テスト」を 1名に配信しました', already_taken: [{ student_id: 3, name: '架空 <i>未設定</i>' }] });",
        "  await gdCreate(); __o.a = { posts: __posts.slice(), msg: __el('gdCreateMsg').innerHTML, confirms: __confirms.length, excl: _gdExcludeDrillId };",
        # (b) 409 = 全員配信済み → 黄色
        "  __posts = []; __resp = __r(409, { detail: '⚠️ 「テスト」: 選んだ生徒は全員このテストを配信済みです' });",
        "  await gdCreate(); __o.b = { n: __posts.length, msg: __el('gdCreateMsg').innerHTML };",
        # (c) 高校のテストに中学生 → 確認 → いいえ
        "  __posts = []; __confirms = []; __confirmAnswer = false; __checked = [1, 2];",
        "  await gdCreate(); __o.c = { n: __posts.length, confirms: __confirms.slice(), msg: __el('gdCreateMsg').innerHTML }; __confirmAnswer = true;",
        # (d) 英語長文: 本文の本数を送る
        "  __posts = []; __confirms = []; _gdSubject = 'english_long'; _gdUnits = [{ unit: '長文 Lv.1', total: 10, passages: 4 }, { unit: '長文 Lv.2', total: 0, passages: 0 }];",
        "  _gdSelUnit = '長文 Lv.1'; __checked = [1]; __el('gdPassageCount').value = '1';",
        "  __resp = __r(200, { ok: true, message: 'ok', already_taken: [] });",
        "  await gdCreate(); __o.d = { posts: __posts.slice(), msg: __el('gdCreateMsg').innerHTML };",
        # (e) 在庫 0 の英語長文 → 送らない
        "  __posts = []; _gdSelUnit = '長文 Lv.2'; await gdCreate(); __o.e = { n: __posts.length, msg: __el('gdCreateMsg').innerHTML };",
        # (f) 英文法は従来どおり count・detail が配列の 422 でも落ちない
        "  __posts = []; _gdSubject = 'english'; _gdUnits = [{ unit: '時制', standard: 30, total: 30, passages: 0 }]; _gdSelUnit = '時制';",
        "  __resp = __r(422, { detail: [{ msg: 'x' }] }); await gdCreate(); __o.f = { posts: __posts.slice(), msg: __el('gdCreateMsg').innerHTML };",
        "  } catch (e) { __o.error = String(e && e.stack || e); }",
        "  __out();",
        "})();",
    ])
    out, err = run_js(eng, prog)
    check("画面のコードが JS で動く", out is not None and not (out or {}).get("error"), (out or {}).get("error") or err)
    o = out or {}

    def has(s, *subs):
        return isinstance(s, str) and all(x in s for x in subs)

    def lacks(s, *subs):
        return isinstance(s, str) and not any(x in s for x in subs)

    check("学年の確認: 高校のテストは中学生・小学生だけ (高校生・学年未設定は出さない)・「高校生用」",
          has(o.get("mmPtK"), "架空 中学生", "架空 小学生", "2名", "高校生用") and lacks(o.get("mmPtK"), "架空 高校生", "架空 未設定"), o.get("mmPtK"))
    check("学年の確認: 「中学英語 …」のテストは中学生以外 (高校生・小学生)・「中学生用」",
          has(o.get("mmPtC"), "架空 高校生", "架空 小学生", "中学生用") and lacks(o.get("mmPtC"), "架空 中学生", "架空 未設定"), o.get("mmPtC"))
    check("学年の確認: 単元が無いテスト (📨 の 2 引数の呼び方) は高校の規則に倒す",
          has(o.get("mmPtNoUnit"), "架空 中学生", "高校生用") and lacks(o.get("mmPtNoUnit"), "架空 高校生"), o.get("mmPtNoUnit"))
    check("学年の確認: 英語長文は大学受験の規則 (中学生・小学生に確認・科目名「英語長文」)",
          has(o.get("mmLong"), "架空 中学生", "架空 小学生", "英語長文", "大学受験用") and lacks(o.get("mmLong"), "架空 高校生"), o.get("mmLong"))
    check("学年の確認: 英検は縛らない・中学英語は今までどおり・高校生への英文法は確認なし",
          o.get("mmEiken") == "" and has(o.get("mmChu"), "架空 高校生", "高校入試の問題") and o.get("mmEngOk") == "",
          (o.get("mmEiken"), o.get("mmChu"), o.get("mmEngOk")))
    check("単元チップ: テストは「🧪 大問3・9問」・単元名の HTML は escape",
          has(o.get("chips"), "🧪 大問3・9問", "第2回&lt;b&gt;") and lacks(o.get("chips"), "第2回<b>"), (o.get("chips") or "")[:300])
    check("④: テストは問題数・本文の本数を隠し「テスト全体を出題順のまま配信」(未選択はテストを選ぶ案内)",
          o.get("syncNoSel") == ["none", "none", "", "テスト全体を出題順のまま配信 (② でテストを選んでください)"]
          and o.get("syncSel") == ["none", "none", "", "テスト全体 (大問3・全9問) を出題順のまま配信"], (o.get("syncNoSel"), o.get("syncSel")))
    check("④: 英語長文は在庫 0 でも本文の本数 (チップも「本文0本」)・英文法は問題数",
          has(o.get("longChips"), "本文2本", "本文0本") and (o.get("syncLong") or [None] * 3)[:3] == ["none", "", "none"]
          and (o.get("syncEng") or [None] * 3)[:3] == ["", "none", "none"], (o.get("syncLong"), o.get("syncEng")))
    a = o.get("a") or {}
    body_a = ((a.get("posts") or [{}])[0] or {}).get("body") or {}
    check("配信 (テスト): 送るのは科目・単元・生徒だけ (本数・問題数・弱点対策の除外・題名を送らない)",
          len(a.get("posts") or []) == 1 and a["posts"][0].get("path") == "/api/admin/grammar-drill/create"
          and body_a.get("subject") == "proficiency_test" and body_a.get("unit") == ku and body_a.get("student_ids") == [1, 3]
          and not ({"passage_count", "count", "exclude_drill_id", "title"} & set(body_a)) and a.get("confirms") == 0, body_a)
    check("配信 (テスト): 配信済みで飛ばした生徒の名前を出す (escape)",
          has(a.get("msg"), "配信済みで飛ばした生徒", "架空 &lt;i&gt;未設定&lt;/i&gt;") and lacks(a.get("msg"), "<i>"), a.get("msg"))
    b = o.get("b") or {}
    check("配信 (テスト): 409 (全員配信済み) は黄色で理由を出す (❌ にしない)",
          b.get("n") == 1 and has(b.get("msg"), "全員このテストを配信済み", "#fbbf24") and lacks(b.get("msg"), "❌"), b)
    c = o.get("c") or {}
    check("配信 (テスト): 高校のテストを中学生に配ろうとすると確認が出て、いいえなら送らない",
          c.get("n") == 0 and len(c.get("confirms") or []) == 1 and has((c.get("confirms") or [""])[0], "架空 中学生", "高校生用")
          and has(c.get("msg"), "配信を中止しました"), c)
    d = o.get("d") or {}
    body_d = ((d.get("posts") or [{}])[0] or {}).get("body") or {}
    check("配信 (英語長文): 本文の本数を送る", body_d.get("subject") == "english_long" and body_d.get("passage_count") == 1
          and "exclude_drill_id" not in body_d, body_d)
    e = o.get("e") or {}
    check("配信 (英語長文): 本文 0 本の単元はサーバに送らず理由を出す", e.get("n") == 0 and has(e.get("msg"), "本文がまだありません"), e)
    f = o.get("f") or {}
    body_f = ((f.get("posts") or [{}])[0] or {}).get("body") or {}
    check("配信 (英文法): 今までどおり問題数を送る・detail が配列の 422 でも「❌ 配信失敗 (HTTP 422)」",
          body_f.get("count") == 30 and "passage_count" not in body_f and has(f.get("msg"), "❌", "HTTP 422"), f)
    check("塾生アプリのカード: テストは「授業の指示どおりに解いて提出 ・ 提出は1回だけ」(いつでもOK・自動採点と書かない)",
          has(o.get("metaPt"), "授業の指示どおりに解いて提出 ・ 提出は1回だけ", "出題 ") and lacks(o.get("metaPt"), "いつでもOK", "自動採点", "全 9 問")
          and has(o.get("metaPtAssigned"), "全 9 問 ・ 授業の指示どおりに解いて提出"), (o.get("metaPt"), o.get("metaPtAssigned")))
    check("塾生アプリのカード: ドリルは今までどおり・提出済みのテストはスコア",
          has(o.get("metaEng"), "その場で自動採点 ・ いつでもOK") and has(o.get("metaDone"), "スコア 7 / 9"), (o.get("metaEng"), o.get("metaDone")))
    check("マイページのカード: テストは「🧪 習熟度テスト」+ 提出の決まり (「ドリル」・レベル・単元のチップは出さない)",
          has(o.get("cardPt"), "🧪 習熟度テスト", "授業の指示どおりに解いて提出 ・ 提出は1回だけ")
          and lacks(o.get("cardPt"), "ドリル</span>", "基礎・標準・やや難", "📝 "), (o.get("cardPt") or "")[:400])
    check("マイページのカード: 提出済みのテストは決まりを出さずスコア・英語長文は「📝 英語長文ドリル」",
          has(o.get("cardPtDone"), "スコア 7/9") and lacks(o.get("cardPtDone"), "授業の指示どおり")
          and has(o.get("cardLong"), "📝 英語長文ドリル", "長文 Lv.1"), ((o.get("cardPtDone") or "")[:200], (o.get("cardLong") or "")[:200]))


def main():
    print("🧪 習熟度テスト (proficiency_test) 取込・出題順・自動配信からの除外 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app, raise_server_exceptions=False)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    cron = {"X-Cron-Secret": "test-cron-secret"}

    def imp(body):
        mod._RATE_LIMIT_STORE.clear()
        r = client.post("/api/admin/grammar/import", json=body, headers=adm)
        return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else {})

    def create(**body):
        mod._RATE_LIMIT_STORE.clear()
        r = client.post("/api/admin/grammar-drill/create", json=dict({"subject": "proficiency_test"}, **body), headers=adm)
        return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else {})

    seq = [0]

    def make(grade="高校2年", ai_disabled=0):
        seq[0] += 1
        conn = mod.db(); c = conn.cursor()
        c.execute("INSERT INTO students (name, email, status, grade, ai_disabled) VALUES (?, ?, 'paid', ?, ?) RETURNING id",
                  (f"架空 テスト{seq[0]:02d}", f"ptest-{seq[0]:02d}@example.org", grade, ai_disabled))
        sid = c.fetchone()["id"]
        conn.commit(); conn.close()
        mod._AI_DISABLED_CACHE.pop(sid, None)
        return sid

    check("科目 proficiency_test が canonical・別名「習熟度テスト」・ラベル「習熟度テスト」",
          "proficiency_test" in mod._GRAMMAR_CANON_SUBJECTS and mod._canon_grammar_subject("習熟度テスト") == "proficiency_test"
          and mod._grammar_subject_label_ja("proficiency_test") == "習熟度テスト")
    check("自動配信の禁止の科目 (env でも外せない)", "proficiency_test" in mod._AUTO_DELIVERY_DENY_SUBJECTS)

    # ------------------------------------------------------------------
    print("\n[1] 取込")
    doc = ptest_doc()
    unit = unit_of(doc)
    check("単元名は「高校英語 習熟度テスト 第1回」(_PTEST_UNIT_RE に合う・取込スクリプトと同じ組み立て)",
          unit == "高校英語 習熟度テスト 第1回" and bool(mod._PTEST_UNIT_RE.match(unit)) and IMP.V.ptest_unit_name(doc) == unit)
    pl = to_payload(doc)
    code, d = imp(pl)
    check("大問 3・設問 9 が入る (ok・errors 0・already_imported false・ptest_meta_saved)",
          code == 200 and d.get("ok") is True and d.get("passages_inserted") == 3 and d.get("inserted") == 9 and d.get("errors") == 0
          and d.get("already_imported") is False and d.get("ptest_meta_saved") is True, d)
    kv = q(mod, "SELECT value FROM kv_settings WHERE key = ?", ("ptest_meta:" + unit,))
    meta = json.loads(kv[0]["value"]) if kv else {}
    check("kv_settings 'ptest_meta:<単元>' に大問数・設問数・skill (設問の出典 → 科目|単元)",
          meta.get("section_count") == 3 and meta.get("question_count") == 9 and meta.get("test_id") == "HSENG01"
          and meta.get("skills") == {"pt-HSENG01-Q02": "english|関係詞"} and meta.get("time_limit_min") == 60, meta)
    rows = q(mod, "SELECT COUNT(*) AS n FROM grammar_questions WHERE subject = 'proficiency_test' AND passage_id IS NULL")
    check("習熟度テストの設問はすべて本文 (大問) に紐づく", rows[0]["n"] == 0)
    ev = q(mod, "SELECT props FROM events WHERE name = 'grammar_import_review'")
    check("events 'grammar_import_review' に記録 (test_id・単元)",
          len(ev) == 1 and json.loads(ev[0]["props"]).get("review", {}).get("test_id") == "HSENG01"
          and json.loads(ev[0]["props"]).get("units") == [unit], ev)

    # ------------------------------------------------------------------
    print("\n[2] 1 始まり → 0 始まり")
    by_src = {r["source"]: r for r in q(mod, "SELECT source, choices, answer FROM grammar_questions WHERE subject = 'proficiency_test'")}
    bad = []
    for sec in doc["sections"]:
        for qq in sec["questions"]:
            r = by_src.get(f"pt-HSENG01-{qq['qid']}")
            if not r or json.loads(r["choices"])[int(r["answer"])] != qq["choices"][qq["correct_choice_no"] - 1]:
                bad.append(qq["qid"])
    check("全 9 問で DB の choices[answer] == ファイルの choices[correct_choice_no - 1]", not bad and len(by_src) == 9, bad)

    # ------------------------------------------------------------------
    print("\n[3] 拒否")
    before = counts(mod)
    d2 = ptest_doc("HSENG02", round_=2)
    p2 = to_payload(d2)
    for p_ in p2["passages"]:
        p_["unit"] = "HSENG02 第2回"
    code, d = imp(dict(p2, all_or_nothing=False, ptest_meta=None))
    check("単元名の形違い (「HSENG02 第2回」) は入れずに errors 3・unknown_units・warning に正しい形",
          code == 200 and d.get("errors") == 3 and d.get("passages_inserted") == 0
          and (d.get("unknown_units") or [{}])[0].get("unit") == "HSENG02 第2回" and "高校英語 習熟度テスト 第1回" in (d.get("warning") or "")
          and counts(mod) == before, d)
    code, d = imp(dict(p2, ptest_meta=None))
    check("all_or_nothing なら ok:false (unknown_unit)・0 行", code == 200 and d.get("ok") is False and d.get("reason") == "unknown_unit"
          and counts(mod) == before, d)
    code, d = imp({"subject": "proficiency_test", "questions": [{"unit": unit, "stem": "x", "choices": ["a", "b"], "answer": 0}]})
    check("questions[] (1 問ずつ) → 422", code == 422 and counts(mod) == before, (code, d))
    code, d = imp(dict(to_payload(ptest_doc("HSENG03", round_=3)), review=None))
    check("review なし → 422・0 行", code == 422 and counts(mod) == before, (code, d))
    code, d = imp(to_payload(ptest_doc("HSENG04", round_=4, per=(1,) * 13)))
    check("大問 13 (上限 12) → 422・0 行", code == 422 and "大問 12" in str(d.get("detail")) and counts(mod) == before, (code, d))
    code, d = imp(to_payload(ptest_doc("HSENG05", round_=5, per=(15, 15, 15, 15, 1))))
    check("設問 61 (上限 60) → 422・0 行", code == 422 and counts(mod) == before, (code, d))
    p6 = to_payload(ptest_doc("HSENG06", round_=6))
    for bad_skill, why in (({"pt-HSENG06-Q02": "math|数と式"}, "高校の math (単元名が決まっていない)"),
                           ({"pt-HSENG06-Q02": "english|関係代名詞"}, "english に無い単元"),
                           ({"pt-HSENG06-Q02": "proficiency_test|x"}, "習熟度テスト自身"),
                           ({"pt-HSENG06-Q99": "english|関係詞"}, "テストに無い設問"),
                           ({"pt-HSENG06-Q02": "english"}, "'|' が無い")):
        code, d = imp(dict(p6, ptest_meta=dict(p6["ptest_meta"], skills=bad_skill)))
        check(f"ptest_meta の skill が不正 ({why}) → 422・0 行", code == 422 and counts(mod) == before, (code, d))
    code, d = imp(dict(p6, ptest_meta=dict(p6["ptest_meta"], skills={"pt-HSENG06-Q02": "chugaku|関係代名詞"})))
    check("skill は中学英語の単元も可 (chugaku|関係代名詞)", code == 200 and d.get("ok") is True and d.get("ptest_meta_saved") is True, d)
    two = to_payload(ptest_doc("HSENG07", round_=7))
    two["passages"] += to_payload(ptest_doc("HSENG08", round_=8))["passages"]
    code, d = imp(two)
    check("ptest_meta を 2 回分まとめて送る → 422", code == 422, (code, d))
    before = counts(mod)
    kv_before = q(mod, "SELECT COUNT(*) AS n FROM kv_settings")[0]["n"]
    code, d = imp(dict(to_payload(ptest_doc("HSENG09", round_=9)), dry_run=True))
    check("dry_run: 大問 3 と数え、本文・設問・kv (ptest_meta) は書かない",
          code == 200 and d.get("dry_run") is True and d.get("passages_inserted") == 3 and counts(mod) == before
          and q(mod, "SELECT COUNT(*) AS n FROM kv_settings")[0]["n"] == kv_before, d)

    # ------------------------------------------------------------------
    print("\n[4] 取込済みの単元・再送・改1")
    before = counts(mod)
    code, d = imp(pl)
    check("同じ要求の再送は already_imported: true・0 行", code == 200 and d.get("ok") is True and d.get("already_imported") is True
          and d.get("passages_inserted") == 0 and counts(mod) == before, d)
    more = copy.deepcopy(pl)
    more["passages"].append(dict(copy.deepcopy(more["passages"][0]), body="第4問 架空の追加の大問", source="ptest:HSENG01:S04"))
    more["ptest_meta"] = None
    code, d = imp(more)
    check("取込済みのテストに大問を足す要求は ok:false (group_exists)・0 行",
          code == 200 and d.get("ok") is False and d.get("reason") == "group_exists" and counts(mod) == before, d)
    rev = ptest_doc(revision=1)
    code, d = imp(to_payload(rev))
    check("直した版「高校英語 習熟度テスト 第1回改1」は入る (本文が同じでも単元が別)",
          code == 200 and d.get("ok") is True and d.get("passages_inserted") == 3 and unit_of(rev) == "高校英語 習熟度テスト 第1回改1", d)

    # ------------------------------------------------------------------
    print("\n[5] 配信 (全大問を取込順・同じ生徒に 2 回は配らない)")
    want_src = [f"pt-HSENG01-{qq['qid']}" for sec in doc["sections"] for qq in sec["questions"]]
    src_of = {r["id"]: r["source"] for r in q(mod, "SELECT id, source FROM grammar_questions WHERE subject = 'proficiency_test'")}
    sa, sb, sc_ = make(), make(), make()
    code, d = create(unit=unit, passage_count=1, levels=["advanced"], count=5, student_ids=[sa])
    check("passage_count=1・levels=advanced を送っても全大問 3・全 9 問・題名「🧪 高校英語 習熟度テスト 第1回（全9問）」",
          code == 200 and d.get("passage_count") == 3 and d.get("question_count") == 9
          and d.get("title") == "🧪 高校英語 習熟度テスト 第1回（全9問）", d)
    drill_a = d.get("drill_id")
    qids = json.loads(q(mod, "SELECT question_ids FROM grammar_drills WHERE id = ?", (drill_a,))[0]["question_ids"])
    check("設問の順 = ファイルの qid 順 (Q01..Q09)", [src_of.get(x) for x in qids] == want_src, [src_of.get(x) for x in qids])
    orders = set()
    for _ in range(5):
        code, d = create(unit=unit, student_ids=[sc_], allow_retake=True)
        orders.add(tuple(json.loads(q(mod, "SELECT question_ids FROM grammar_drills WHERE id = ?", (d.get("drill_id"),))[0]["question_ids"]))
                   if code == 200 else None)
    check("5 回作っても同じ順 (allow_retake で同じ生徒にも配れる)", orders == {tuple(qids)}, orders)
    sa_st = q(mod, "SELECT score_total FROM grammar_drill_assignments WHERE drill_id = ?", (drill_a,))
    check("score_total = 設問数 9", sa_st and sa_st[0]["score_total"] == 9, sa_st)
    n_drills = counts(mod)["grammar_drills"]
    code, d = create(unit=unit, student_ids=[sa, sb])
    check("配信済みの生徒 A は外して B だけに配る (already_taken に A・message に「飛ばしました」)",
          code == 200 and [x["student_id"] for x in d.get("assigned", [])] == [sb]
          and [x["student_id"] for x in d.get("already_taken", [])] == [sa] and d["already_taken"][0].get("name")
          and "1名は飛ばしました" in (d.get("message") or ""), d)
    n_drills = counts(mod)["grammar_drills"]
    code, d = create(unit=unit, student_ids=[sa, sb])
    check("全員が配信済み → 409・空のドリルを作らない", code == 409 and counts(mod)["grammar_drills"] == n_drills
          and "全員このテストを配信済み" in str(d.get("detail")), (code, d))
    code, d = create(unit=unit, student_ids=[sa], allow_retake=True)
    check("allow_retake: true なら配れる (追試・CEO には出さない)", code == 200 and [x["student_id"] for x in d.get("assigned", [])] == [sa], d)
    code, d = create(unit=unit, student_ids=[sb], allow_retake="yes")
    check("allow_retake は true (真偽値) のときだけ ('yes' は 409)", code == 409, (code, d))
    code, d = create(unit=unit, exclude_drill_id=drill_a, student_ids=[make()])
    check("exclude_drill_id → 422 (弱点対策の再配信に使わない)", code == 422, (code, d))
    code, d = create(unit="", student_ids=[make()])
    check("単元なし (科目まるごと) → 422", code == 422, (code, d))
    code, d = create(unit="高校英語 習熟度テスト 第99回", student_ids=[make()])
    check("取り込んでいない単元 → 400", code == 400 and "取り込まれていません" in str(d.get("detail")), (code, d))
    check("_drill_create_message: 全員配信済みの文・一部の文",
          "全員このテストを配信済み" in mod._drill_create_message(0, "x", None, already_taken=2)
          and "（このテストを配信済みの 2名は飛ばしました）" in mod._drill_create_message(1, "x", {}, already_taken=2)
          and "飛ばしました" not in mod._drill_create_message(1, "x", {}))

    # ------------------------------------------------------------------
    print("\n[6] 👀 プレビュー")
    r = client.get("/api/admin/grammar/preview", params={"subject": "proficiency_test", "unit": unit, "passage_count": 1, "levels": "advanced"},
                   headers=adm)
    pv = r.json() if r.status_code == 200 else {}
    pq = pv.get("questions") or []
    check("本数・レベルの指定に関わらずテスト全体 (大問 3・9 問) を出題順に",
          r.status_code == 200 and pv.get("passage_count") == 3 and [src_of.get(x["id"]) for x in pq] == want_src, r.text[:200])
    want_ans = [qq["correct_choice_no"] - 1 for sec in doc["sections"] for qq in sec["questions"]]
    check("答え (0 始まり)・解説つき", [x.get("answer") for x in pq] == want_ans and all(x.get("explanation") for x in pq), pq[:2])

    # ------------------------------------------------------------------
    print("\n[7] 生徒の取得・提出・分析")
    tok = {"Authorization": "Bearer " + student_token(mod, sa)}
    mod._RATE_LIMIT_STORE.clear()
    r = client.get(f"/api/student/grammar-drill/{drill_a}", headers=tok)
    g = r.json() if r.status_code == 200 else {}
    gq = g.get("questions") or []
    check("取得: 9 問・答えと解説を伏せる", r.status_code == 200 and len(gq) == 9 and all("answer" not in x and "explanation" not in x for x in gq),
          r.text[:200])
    answers = {str(x): a for x, a in zip(qids, want_ans)}
    mod._RATE_LIMIT_STORE.clear()
    r = client.post(f"/api/student/grammar-drill/{drill_a}/submit", json={"answers": answers}, headers=tok)
    s = r.json() if r.status_code == 200 else {}
    check("正解どおりに提出すると 9/9・subject は proficiency_test", r.status_code == 200 and s.get("score_correct") == 9
          and s.get("score_total") == 9 and s.get("subject") == "proficiency_test", r.text[:200])
    mod._RATE_LIMIT_STORE.clear()
    r = client.post(f"/api/student/grammar-drill/{drill_a}/submit", json={"answers": answers}, headers=tok)
    check("2 回目の提出は 409 (提出は 1 回だけ)", r.status_code == 409, r.status_code)
    r = client.get(f"/api/admin/grammar-drill/{drill_a}/analytics", headers=adm)
    a = r.json() if r.status_code == 200 else {}
    roster = a.get("students") or []
    check("分析: 名簿に提出済み 1 名・問題別正答率 100% が 9 問",
          r.status_code == 200 and a.get("summary", {}).get("completed") == 1
          and len(a.get("questions") or []) == 9 and all(x.get("correct_rate") == 100.0 for x in a.get("questions") or [])
          and any(x.get("student_id") == sa for x in roster), r.text[:300])

    # ------------------------------------------------------------------
    print("\n[8] 弱点に入れない (PTEST_FEEDS_WEAKNESS)")
    rows = q(mod, "SELECT subject, topic, metadata FROM question_attempts WHERE student_id = ?", (sa,))
    check("解答は subject='proficiency_test'・topic=単元・metadata.ptest_unit で 9 行",
          len(rows) == 9 and all(x["subject"] == "proficiency_test" and x["topic"] == unit
                                 and json.loads(x["metadata"]).get("ptest_unit") == unit for x in rows), rows[:2])
    mod._run_weakness_aggregation()
    w = q(mod, "SELECT subject, topic FROM student_weakness WHERE subject = 'proficiency_test' OR topic = ?", (unit,))
    check("弱点集計の後も proficiency_test の弱点は 0 行 (単元名が弱点にならない)", w == [], w)
    sf = make()
    code, d = create(unit=unit, student_ids=[sf])
    drill_f = d.get("drill_id")
    wrong = {str(x): (a + 1) % 4 for x, a in zip(qids, want_ans)}   # 全問まちがえる
    with Env(PTEST_FEEDS_WEAKNESS="1"):
        mod._RATE_LIMIT_STORE.clear()
        r = client.post(f"/api/student/grammar-drill/{drill_f}/submit", json={"answers": wrong},
                        headers={"Authorization": "Bearer " + student_token(mod, sf)})
    rows = q(mod, "SELECT exam_question_id, subject, topic, metadata FROM question_attempts WHERE student_id = ? ORDER BY id", (sf,))
    q02 = [x for x in rows if src_of.get(x["exam_question_id"]) == "pt-HSENG01-Q02"]
    others = [x for x in rows if src_of.get(x["exam_question_id"]) != "pt-HSENG01-Q02"]
    check("PTEST_FEEDS_WEAKNESS=1: skill つきの Q02 は english/関係詞 で記録 (metadata.ptest_skill)",
          r.status_code == 200 and len(q02) == 1 and q02[0]["subject"] == "english" and q02[0]["topic"] == "関係詞"
          and json.loads(q02[0]["metadata"]).get("ptest_skill") is True, q02)
    check("skill なしの 8 問は proficiency_test のまま", len(others) == 8 and all(x["subject"] == "proficiency_test" for x in others), others[:2])
    mod._run_weakness_aggregation()
    w = q(mod, "SELECT subject, topic FROM student_weakness WHERE student_id = ?", (sf,))
    check("弱点集計の後: english/関係詞 の弱点が立ち、proficiency_test の弱点は無い",
          {"subject": "english", "topic": "関係詞"} in w and not any(x["subject"] == "proficiency_test" for x in w), w)
    check("PTEST_FEEDS_WEAKNESS の既定は OFF", mod._ptest_feeds_weakness() is False)

    # ------------------------------------------------------------------
    print("\n[9] 習熟度テストしか無い DB: 自動・自己発行の経路に出ない")
    s9 = make()
    tok9 = {"Authorization": "Bearer " + student_token(mod, s9)}
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/student/today-question/start", headers=tok9)
    check("今日の1問 → 503", r.status_code == 503, (r.status_code, r.text[:200]))
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/student/diagnostic/start", headers=tok9)
    check("初回診断 → 503", r.status_code == 503, (r.status_code, r.text[:200]))
    ex(mod, "INSERT INTO student_weakness (student_id, subject, topic, question_count, qa_accuracy, qa_attempts) "
            "VALUES (?, 'proficiency_test', ?, 10, 0.1, 10)", (s9, unit))
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT id, name, email, line_user_id, grade, ai_disabled, ai_trial_until FROM students WHERE id = ?", (s9,))
    st = c.fetchone()
    reasons = {}
    p = mod._weakness_routine_plan(c, st, "kosei", rng=random.Random(1), reasons=reasons)
    check("3日ドリル: 習熟度テストの弱点の行があっても配らない (not_routine_subject:proficiency_test)",
          not p["ok"] and reasons.get("not_routine_subject:proficiency_test") == 1, (p, reasons))
    check("CEO の 1 問ずつの抽出 (科目まるごと) は 0 問",
          mod._grammar_pick_drill_question_ids(c, "proficiency_test", "", True, ["basic", "standard", "advanced"], 5, None) == [])
    for env_v in (None, "english=*;proficiency_test=*"):
        with Env(AUTO_DELIVERY_REVIEWED_SOURCES=env_v):
            r1 = mod._auto_pick_reviewed_question_ids(c, "proficiency_test", "", ["basic", "standard", "advanced"], 1, {}, rng=random.Random(1))
            r2 = mod._auto_pick_reviewed_passages(c, "proficiency_test", unit, ["standard"], 1, {}, rng=random.Random(1))
            idx = mod._auto_reviewed_passages(c, "proficiency_test", unit, ["standard"])
            check(f"自動の抽出 (3日ドリル・クラス自動宿題が使う 2 つ) は 0 (env={env_v!r})",
                  r1["ids"] == [] and r2["qids"] == [] and r2["reviewed_available"] == 0 and idx["passages"] == {}
                  and idx["rejected"]["unreviewed_body"] == 3, (r1, r2, idx["rejected"]))
            check(f"学年の区分の判定でも出ない (env={env_v!r})",
                  not any(mod._drill_subject_band_ok("proficiency_test", b) for b in ("kosei", "chugaku", "shougaku", "")))
    conn.close()
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/weakness-drill-routine/run", json={"dry_run": True, "student_id": s9}, headers=cron)
    check("3日ドリルの dry-run: 配る生徒 0", r.status_code == 200 and r.json().get("delivered") == 0, r.text[:300])

    # ------------------------------------------------------------------
    print("\n[10] 英検の本文の順はランダムのまま")
    eik = []
    for n in range(6):
        eik.append({"unit": "準1級 長文 内容一致", "level": "standard", "title": f"架空 {n}", "body": f"Fictional eiken passage {n}. ( 1 )",
                    "source": f"test-eik-{n}", "questions": [{"stem": f"架空の設問 {n}", "choices": ["a", "b", "c", "d"], "answer": n % 4}]})
    code, d = imp({"subject": "eiken", "dedup": True, "passages": eik})
    check("英検の本文 6 本 (CEO の補充ボタンと同じ送り方・review なし) は従来どおり入る", code == 200 and d.get("passages_inserted") == 6, d)
    conn = mod.db(); c = conn.cursor()
    eorders = {tuple(mod._grammar_pick_drill_passages(c, "eiken", "準1級 長文 内容一致", ["standard"], 6, None)[1]) for _ in range(20)}
    porders = {tuple(mod._grammar_pick_drill_passages(c, "proficiency_test", unit, ["basic", "standard", "advanced"], 12, None)[1]) for _ in range(20)}
    conn.close()
    check("英検: 20 回で本文の順が 2 通り以上", len(eorders) >= 2, len(eorders))
    check("習熟度テスト: 20 回とも同じ順 (id の昇順)", len(porders) == 1 and list(next(iter(porders))) == sorted(next(iter(porders))), porders)

    # ------------------------------------------------------------------
    print("\n[11] CEO の配信済み一覧・単元一覧")
    sid_e = make()
    code, d = create(subject="eiken", unit="準1級 長文 内容一致", passage_count=1, student_ids=[sid_e])
    r = client.get("/api/admin/grammar-drill/list", params={"subject": "proficiency_test", "kind": "all"}, headers=adm)
    items = r.json().get("items", []) if r.status_code == 200 else []
    check("list?subject=proficiency_test はテストだけ (英検のドリルは出ない)",
          r.status_code == 200 and items and all(x.get("subject") == "proficiency_test" for x in items), [x.get("subject") for x in items])
    r = client.get("/api/admin/grammar-drill/list", params={"subject": "習熟度テスト"}, headers=adm)
    check("別名「習熟度テスト」でも絞れる", r.status_code == 200 and r.json().get("subject") == "proficiency_test", r.text[:200])
    for tid, rnd, tgt in (("HSENG10", 10, "kosei"), ("HSENG02X", 2, "kosei"), ("JHENG01", 1, "chugaku")):
        code, d = imp(to_payload(ptest_doc(tid, round_=rnd, target=tgt)))
        check(f"{tid} 第{rnd}回 ({tgt}) が入る", code == 200 and d.get("ok") is True and d.get("passages_inserted") == 3, d)
    r = client.get("/api/admin/grammar/units", params={"subject": "proficiency_test"}, headers=adm)
    names = [u["unit"] for u in (r.json().get("units", []) if r.status_code == 200 else [])]
    check("単元一覧は 高校 → 中学・回の数字の順・改は元の回の後",
          names == ["高校英語 習熟度テスト 第1回", "高校英語 習熟度テスト 第1回改1", "高校英語 習熟度テスト 第2回",
                    "高校英語 習熟度テスト 第6回", "高校英語 習熟度テスト 第10回", "中学英語 習熟度テスト 第1回"], names)

    # ------------------------------------------------------------------
    print("\n[12] 自動配信の関数に習熟度テストの名前が出てこない・お知らせ")
    funcs = [mod._run_weakness_drill_routine, mod._weakness_routine_pick_drills, mod._weakness_routine_plan,
             mod._create_routine_grammar_drill, mod.student_today_question_start, mod.student_diagnostic_start,
             mod._self_issued_subject, mod._self_issued_reviewed_ids, mod._auto_pick_reviewed_question_ids,
             mod._auto_pick_reviewed_passages, mod._auto_reviewed_passages]
    # クラス自動宿題 (コミット 11) の関数ができたらここに足す
    for name in ("_run_class_homework_routine", "_class_hw_deliver_group", "_class_hw_plan"):
        if hasattr(mod, name):
            funcs.append(getattr(mod, name))
    hits = [f.__name__ for f in funcs if "proficiency_test" in inspect.getsource(f) or "_PTEST_SUBJECT" in inspect.getsource(f)]
    check("自動配信・自己発行の関数のソースに proficiency_test / _PTEST_SUBJECT が無い (許可リスト方式・禁止は共通部品)", not hits, hits)
    mails = []
    orig_send, orig_sleep = mod._send_message_email, time.sleep
    mod._send_message_email = lambda to, subject, body, student_name=None: (mails.append((subject, body)), {"sent": True})[1]
    time.sleep = lambda s: None
    try:
        with Env(HOMEWORK_NOTIFY_EMAIL=None):   # 既定 = manual (塾長が手で配ったときだけメール)
            res = mod._notify_grammar_drill_assigned([{"id": sb, "name": "架空", "email": "ptest-02@example.org"}], unit, 9,
                                                     "proficiency_test", "manual")
    finally:
        mod._send_message_email, time.sleep = orig_send, orig_sleep
    check("メールの件名「🧪 習熟度テスト「高校英語 習熟度テスト 第1回」が届きました」",
          mails and mails[0][0] == "🧪 習熟度テスト「高校英語 習熟度テスト 第1回」が届きました", mails)
    check("本文に「全9問」と提出は 1 回・「解説がその場で」は書かない",
          mails and "全9問" in mails[0][1] and "提出は1回だけ" in mails[0][1] and "解説がその場で" not in mails[0][1], mails)
    check("LINE は送らない (既定)", res.get("line_ok") == 0 and res.get("channels", {}).get("line") is False, res)

    # ------------------------------------------------------------------
    print("\n[13] 取込スクリプトの往復 (fixtures → 試運転 → --apply → 読み返し・通信は TestClient に差し替え)")
    calls = []
    base = "https://ai-juku-api.test.invalid"

    def fake_http(method, url, headers, body=None):
        u = urllib.parse.urlsplit(url)
        calls.append((method, u.path, headers.get("X-Cron-Secret") == "test-cron-secret", url.startswith(base + "/")))
        mod._RATE_LIMIT_STORE.clear()
        r = client.request(method, u.path, params=dict(urllib.parse.parse_qsl(u.query)) or None, json=body, headers=headers)
        try:
            return r.status_code, r.json()
        except ValueError:
            return r.status_code, {"_text": r.text[:300]}

    IMP.HTTP = fake_http
    work = tempfile.mkdtemp(prefix="ptest_fx_")
    shutil.copytree(os.path.join(DRILL_IMPORT, "fixtures"), os.path.join(work, "fixtures"))
    fxd = os.path.join(work, "fixtures")
    with Env(AI_JUKU_API_BASE=base, CRON_SECRET="test-cron-secret"):
        for name in ("ok_proficiency_test.json", "ok_english_long.json"):
            path = os.path.join(fxd, name)
            fdoc = json.load(open(path, encoding="utf-8"))
            r0 = IMP.V.validate(path)
            check(f"{name}: 検査スクリプトでエラー・警告なし", not r0.errors and not r0.warnings, (r0.errors + r0.warnings)[:3])
            before = counts(mod)
            out = io.StringIO()
            rc = IMP.run([path], out=out)
            check(f"{name}: 試運転 → exit 0・DB は増えない", rc == 0 and "試運転 OK" in out.getvalue() and counts(mod) == before,
                  out.getvalue()[-500:])
            out = io.StringIO()
            rc = IMP.run([path, "--apply"], out=out)
            check(f"{name}: --apply → 入れて読み返しも一致 (単元の本数・👀 プレビュー)",
                  rc == 0 and "取り込みました (読み返しも一致)" in out.getvalue(), out.getvalue()[-700:])
            if fdoc["kind"] == "english_long":
                pref, groups, unit_f = f"el-{fdoc['set_id']}-", fdoc["passages"], fdoc["unit"]
            else:
                pref, groups, unit_f = f"pt-{fdoc['test_id']}-", fdoc["sections"], IMP.V.ptest_unit_name(fdoc)
            rows = {r["source"]: r for r in q(mod, "SELECT g.source, g.unit, g.stem, g.choices, g.answer, g.explanation, p.body, p.body_ja "
                                                  "FROM grammar_questions g JOIN grammar_passages p ON p.id = g.passage_id "
                                                  "WHERE g.subject = ?", (fdoc["kind"],)) if str(r["source"]).startswith(pref)}
            bad, nq = [], 0
            for g in groups:
                for qq in g["questions"]:
                    nq += 1
                    r = rows.get(pref + qq["qid"])
                    ch = json.loads(r["choices"]) if r else None
                    if (not r or r["unit"] != unit_f or r["stem"] != qq["stem"].strip() or ch != qq["choices"]
                            or int(r["answer"]) != qq["correct_choice_no"] - 1
                            or ch[int(r["answer"])] != qq["choices"][qq["correct_choice_no"] - 1]
                            or r["explanation"] != qq["explanation"] or r["body"] != g["body"].strip()
                            or (r["body_ja"] or None) != (g.get("body_ja") or None)):
                        bad.append(qq["qid"])
            check(f"{name}: 全 {nq} 問が DB と一致 (answer = correct_choice_no - 1・選択肢・解説・本文・全訳・単元)",
                  not bad and len(rows) == nq, (bad, len(rows), nq))
            if fdoc["kind"] == "proficiency_test":
                kv = q(mod, "SELECT value FROM kv_settings WHERE key = ?", ("ptest_meta:" + unit_f,))
                want = {pref + qq["qid"]: f"{qq['skill']['subject']}|{qq['skill']['unit']}"
                        for g in groups for qq in g["questions"] if qq.get("skill")}
                got = json.loads(kv[0]["value"]).get("skills") if kv else None
                check(f"{name}: ptest_meta の skill = ファイルの skill ({len(want)} 問)", got == want and want, (got, want))
            before = counts(mod)
            out = io.StringIO()
            n_calls = len(calls)
            rc = IMP.run([path, "--apply"], out=out)
            check(f"{name}: 2 回目の --apply は「取込済み」で何も増えない (試運転だけ送る)",
                  rc == 0 and "取込済み" in out.getvalue() and counts(mod) == before
                  and [c[1] for c in calls[n_calls:]] == ["/api/admin/grammar/import"], out.getvalue()[-300:])
            log = open(path + ".import_log.json", encoding="utf-8").read()
            check(f"{name}: 記録 (import_log.json) は 3 回分・秘密は書かない",
                  len(json.loads(log)) == 3 and "test-cron-secret" not in log, log[:200])
        n_calls = len(calls)
        out = io.StringIO()
        rc = IMP.run([os.path.join(DRILL_IMPORT, "fixtures", "ok_english_long.json"), "--apply"], out=out)
        check("リポジトリの中のファイルは送らない (exit 2・通信しない)", rc == 2 and len(calls) == n_calls, out.getvalue()[-300:])
    check("送った要求はすべて X-Cron-Secret つき・送り先は AI_JUKU_API_BASE", calls and all(c[2] and c[3] for c in calls), calls[:3])
    shutil.rmtree(work, ignore_errors=True)

    check_screens(mod)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for f in FAILURES:
            print(f"   - {f}")
        return 1
    print("✅ PASS (習熟度テスト: 1 回分 = 1 本・取込順・同じ生徒に 2 回配らない・弱点と自動配信に入らない)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
