#!/usr/bin/env python3
"""🏫 クラス自動宿題 (塾生アプリのみ枠 = AIなし・英語だけ) の回帰テスト (2026-10-15 塾長決定
「AIなしは英語のクラスの宿題として科目別ドリル」「基本的に2日に1回」「中学生と高校生は問題の配信はミスらないように」)。

固定する性質 (一時 SQLite・外部通信なし・生徒名とメールは架空 = 公開リポジトリ):
  [1] クラスの表と監視: 表のキー = 時間割のクラス名 (15)・長文のクラスは english_long の単元 (高校生だけ)・GMARCH/早慶は hold・
      日曜 高校国語は none・英検のクラスはその級の単元だけ・習熟度テストはどこにも無い。CLASS_HW_AUTO_ENABLED は既定 OFF・
      ON で import したときだけ _SCHEDULER_MAX_AGE_DAYS に class_hw_auto_run (2 日)・通知の名前の表 2 つ・prod_status・
      prod_healthcheck は履歴が無いうちは PASS・スケジューラは毎日 env を見て to_thread と要約の記録・実行時刻は 5〜22 に丸める
  [2] 対象の生徒: AIなし 高2 → english / AIなし 中3 → chugaku (別のドリル)・AIあり と AI 体験中・合成監視・テスト名・退会・
      通塾生でない・クラスに入っていない・判定できない学年・小学生・GMARCH だけ・長文クラスだけの中学生には配らない・
      体験が切れた AIなし には配る・受講開始月の前は配らない (NULL は制限なし)
  [3] 中高の取り違えなし: english のドリルは高校生だけ・chugaku のドリルは中学生だけ・どのドリルも問題の科目 = ドリルの科目。
      書き込み直前の学年ガードは区分違いを書かずに数える (通常の実行では 0 回)
  [4] レビュー済みだけ: 未レビュー (pool / pt-) が 100 問あっても 20 回選んで 1 問も出ない・長文クラスはレビュー済みの本文が
      CLASS_HW_READING_MIN_PASSAGES (既定 4) 本になるまで始めない (未レビューの本文は数えない)・4 本で本文 1 本の宿題
  [5] 英検: 英検2級対策の中3 → 2級の単元・長文の単元は本文 2 本 (設問は本文ごとに passage_seq 順)
  [6] 2 日に 1 回: 同じ日の 2 回目は増えない (未提出・積まない)・提出しても 2 日たつまで配らない・2 日後に次の単元・
      (クラス, 区分) のドリルは 2 日に 1 本 (同じ日に後から受け取れるようになった生徒は同じドリルに足す・前の日のドリルには足さず
      次の新しいドリルを待つ = wait_next)・〆 の日に出す生徒も届くドリルの 〆 はいつも受け取った日 + 2 日 (1 日遅れのまま固定しない)・
      英語のクラスを 2 つ取る生徒は 1 回に 1 本で、次は最後に届いたのが古いクラス・ドリルを作る日が 1 日ずれた 2 クラスでも
      (ON の手順の ONLY) 両方が交互に届く (古いクラスが wait_next なら後に届いたクラスに回さず翌朝まで待つ・届いたことが無ければ待たない)
  [7] 単元の選び方: クラスの区分の弱点の正答率の低い順 (合計 3 回未満・0.8 以上は数えない)・直近 14 日に出した単元は飛ばす・
      弱点が無ければ単元の順番・全部が飛ばす期間なら一番前に出した単元・中学は「中学英語 時制」(写し) を数えず「時制（過去）」は 時制
  [8] お知らせ: LINE は 1 回も送らない・既定ではメールも送らない (source='auto')・HOMEWORK_NOTIFY_EMAIL=all ならリンクは
      /class.html?tab=homework (# を使わない)
  [9] dry-run: 何も書かない・15 クラスすべてを返す・同じ seed なら dry-run と本番で同じ単元・問題・生徒。名前は include_names のときだけ・
      管理 API (401・既定は dry-run・時間割に無いクラスと hold のクラスは 400)・CLASS_HW_AUTO_ONLY_CLASSES (全角・空白の違いは同じ名前・
      打ち間違いや保留のクラスだけの指定は全クラスに広げず 0 クラス + props.error)・📤 の 1 クラスだけ
  [10] AIなし の生徒が塾生アプリで解ける: /api/student/homework 200・一覧に出る・取得と提出が 200 (許可集合は変えていない)
  [11] CEO の配信済み一覧: 既定 (塾長) には出ない・kind=class_hw でクラス名と区分つき
  [12] 1 人 1 経路 (3日ドリルと合わせて): ai_disabled 0/1 × 体験の期限 なし/過去/未来/壊れた値 の全員が、ちょうど 1 つの自動配信に入る
  [13] 競合と監視: 計画と書き込みの間に別の実行が配った生徒は race (2 本目を作らない)・全部の書き込みに失敗したら props.error・
      要約は 4000 字未満の正しい JSON で名前を含まない・配信の記録 (events) は生徒 id だけ
  [15] 2026-10-16 塾長決定: 積まない判定に数える未提出は直近 CLASS_HW_OPEN_STALE_DAYS (既定 14・0 = 全部・interval〜365) 日 (JST の日付) に
      配った分だけ (3日ドリルと同じ考え方)。15 日前の未提出だけなら配る (stale_open_ignored)・ちょうど 14 日前は数える・0 で従来どおり・
      assigned_at が空は数える・本番でも錠の中の読み直しで race にしない・古いドリルは消さない。2 日に 1 本の周期は数秒の遅れで
      3 日にずれない (6 時間の遊び)
  [14] 画面: CEO「🏫 クラス自動宿題」カード (🎯 確認カードと配信済み一覧の帯の間・🔍 は dry_run: true・📤 は confirm() の後だけ本番で
      1 クラス・「📋 結果」は一覧を class_hw に切り替える・名前は escape・古いサーバは「サーバ反映待ち」) と塾生アプリのカードの 2 行目
      (題名に 〆 があれば「いつでもOK」と書かない)。ceo.html / class.html の本物のコードを JS エンジンで動かす (無ければ FAIL)。
      2026-10-16: 🔍 の応答の last_run (毎朝の実行の最後の記録)・見出しは「今もう一度回したら配る」・その上に「前回の自動配信」・
      古い未提出を数えなかった生徒のチップ

実行:
    python3 scripts/health_check/test_class_homework_routine.py
    # exit 0 = PASS / 1 = FAIL
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import inspect
import json
import os
import random
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "server"))
from test_grammar_import_units import admin_token, import_like_ceo, load_seed, Api  # noqa: E402
from test_grade_band_consistency import js_engine, run_js  # noqa: E402
CEO_HTML = os.path.join(REPO, "ceo.html")
CLASS_HTML = os.path.join(REPO, "class.html")

FAILURES = []
ENV_KEYS = ("CLASS_HW_AUTO_ENABLED", "CLASS_HW_AUTO_HOUR_JST", "CLASS_HW_INTERVAL_DAYS", "CLASS_HW_AUTO_COUNT", "CLASS_HW_OPEN_STALE_DAYS",
            "CLASS_HW_AUTO_PASSAGES", "CLASS_HW_READING_MIN_PASSAGES", "CLASS_HW_UNIT_COOLDOWN_DAYS", "CLASS_HW_AUTO_ONLY_CLASSES",
            "AUTO_DELIVERY_REVIEWED_SOURCES", "HOMEWORK_NOTIFY_EMAIL", "HOMEWORK_NOTIFY_LINE", "WEAKNESS_DRILL_ROUTINE_ENABLED",
            "WEAKNESS_ROUTINE_UNKNOWN_GRADE_AS_KOSEI", "WEAKNESS_DRILL_ROUTINE_CAP", "WEEKLY_WORKSHEET_ENABLED")
SEEDS = (("grammar_drill_pool_v1.json", "english"), ("chugaku_drill_pool_v1.json", "chugaku"), ("eiken_vocab_pool_v1.json", "eiken"))
PREFIX = "class_hw_auto:"
LV2 = "火曜2限 英文法 Lv.2"
EIKEN2 = "金曜2限 英検2級対策"
READ1 = "月曜3限 長文読解 Lv.1"
REVIEW = {"protocol": "trillion-blind/v1", "all_agree": True, "validator": "validate_drill_import/v1",
          "file_sha256": "0" * 64, "kind": "english_long", "set_id": "CHW001",
          "solvers": [{"label": "A", "kind": "ai", "date": "2026-10-21"}, {"label": "B", "kind": "ai", "date": "2026-10-21"},
                      {"label": "C", "kind": "ai", "date": "2026-10-21"}]}


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def _base_env(tmpdb):
    return {
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
    }


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="class_hw_"), "test.db")
    os.environ.update(_base_env(tmpdb))
    for k in ENV_KEYS:
        os.environ.pop(k, None)
    spec = importlib.util.spec_from_file_location("aijuku_main_class_hw", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


class Env:
    """env を一時的に差し替える (None = 未設定)。"""

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


def _scheduler_keys_in_subprocess(value):
    """CLASS_HW_AUTO_ENABLED=value で main.py を別プロセスで import し、_SCHEDULER_MAX_AGE_DAYS を返す (import 時に評価される)。"""
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="class_hw_sub_"), "test.db")
    env = dict(os.environ)
    env.update(_base_env(tmpdb))
    env.pop("CLASS_HW_AUTO_ENABLED", None)
    if value is not None:
        env["CLASS_HW_AUTO_ENABLED"] = value
    code = (
        "import importlib.util, json, sys\n"
        f"spec = importlib.util.spec_from_file_location('aijuku_main_class_hw_sub', {MAIN_PY!r})\n"
        "mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)\n"
        "print('KEYS=' + json.dumps(mod._SCHEDULER_MAX_AGE_DAYS))\n"
    )
    r = subprocess.run([sys.executable, "-c", code], env=env, cwd=os.path.join(REPO, "server"),
                       capture_output=True, text=True, timeout=300)
    for line in (r.stdout or "").splitlines():
        if line.startswith("KEYS="):
            return json.loads(line[len("KEYS="):])
    raise RuntimeError(f"subprocess failed rc={r.returncode}: {(r.stderr or '')[-800:]}")


class Recorder:
    """LINE / メール / sleep を記録する偽物 (テストの最初から最後まで差し替える)。"""

    def __init__(self, mod):
        self.lines, self.mails = [], []
        mod._do_line_push = lambda sid, template, params=None: (self.lines.append((sid, template)), {"ok": True})[1]
        mod._send_message_email = lambda to, subject, body, student_name=None: (self.mails.append((to, subject, body)), {"sent": True})[1]
        time.sleep = lambda s: None


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
    return {t: q(mod, f"SELECT COUNT(*) AS n FROM {t}")[0]["n"] for t in ("grammar_drills", "grammar_drill_assignments", "events")}


def el_passage(set_id, n, unit="長文 Lv.1", nq=3):
    """取込スクリプトが送る形の英語長文 (中身は架空・出典 el-<set_id>-<qid> / englong:<set_id>:<pid>)。"""
    pid = f"P{n:02d}"
    body = (f"[1] Fictional story {set_id}-{n}: a small town in this story opened a reading room in an old station. "
            f"( 1 ), many people came to borrow books.\n\n[2] Later, {n + 2} nearby towns copied the idea.")
    qs = [{"stem": f"設問 {k} の空所に入るものを選びなさい。", "choices": [f"opt {set_id} {n}-{k} {x}" for x in "abcd"],
           "answer": (n + k) % 4, "explanation": "【根拠】架空の根拠\n【訳】架空の訳", "source": f"el-{set_id}-{pid}-Q{k}"}
          for k in range(1, nq + 1)]
    return {"subject": "english_long", "unit": unit, "level": "standard", "title": f"Fictional {n}", "body": body,
            "body_ja": f"架空の全訳 {n}", "source": f"englong:{set_id}:{pid}", "questions": qs}


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


_JS_OUT = ("var __s = 'RESULT ' + JSON.stringify(__o);\n"
           "if (typeof process !== 'undefined' && typeof console !== 'undefined' && console.log) console.log(__s);\n"
           "else if (typeof print === 'function') print(__s);\n"
           "else if (typeof console !== 'undefined' && console.log) console.log(__s);\n")


def check_screens(mod, client, adm, ids):
    """[14] CEO「🏫 クラス自動宿題」カードと塾生アプリのカードの 2 行目 (本物のコードを JS エンジンで動かす)。"""
    print("\n[14] 画面: CEO 🏫 カード (🔍 は dry-run・📤 は confirm の後だけ・名前は escape) / 塾生アプリのカードの 〆")
    import re
    ceo = open(CEO_HTML, encoding="utf-8").read()
    cls = open(CLASS_HTML, encoding="utf-8").read()
    try:
        pos = [ceo.index('id="gdRoutineBox"'), ceo.index('id="chwBox"'), ceo.index('id="gdListBar"'), ceo.index('<div id="gdList"')]
    except ValueError as e:
        pos = []
        check("ceo.html に 🎯 カード・🏫 カード・絞り込みの帯・一覧がある", False, e)
    check("並び: 🎯 確認カード → 🏫 クラス自動宿題 → 絞り込みの帯 → 一覧", len(pos) == 4 and pos == sorted(pos), pos)
    urls = re.findall(r"""[`'"]/api/admin/class-homework-routine/run""", ceo)
    check("クラス自動宿題の URL は 1 か所 (_CHW_URL) だけに書く", len(urls) == 1 and "const _CHW_URL = '/api/admin/class-homework-routine/run';" in ceo, urls)
    check("3日ドリルを回す呼び出しは今までどおり 🔍 の 1 か所だけ", len(re.findall(r"""[`'"]/api/admin/weakness-drill-routine/run""", ceo)) == 1)
    dry = _js_block(ceo, "    async function chwDryRun() {")
    runc = _js_block(ceo, "    async function chwRunClass(i) {")
    check("🔍 は dry_run: true・all_classes・include_names だけを送る (本番にしない)",
          "_CHW_URL" in dry and "dry_run: true, all_classes: true, include_names: true" in dry and "dry_run: false" not in dry, dry[:300])
    check("📤 は confirm() の後でだけ dry_run: false と class_label を送る",
          "_CHW_URL" in runc and "dry_run: false, class_label: String(row.label)" in runc
          and 0 <= runc.find("confirm(") < runc.find("dry_run: false"), runc[:300])
    check("📤 の onclick にはクラス名を入れず番号だけ (引用符で壊れない)", "onclick=\"chwRunClass(${i})\"" in ceo)
    check("「📋 結果」は一覧を class_hw に切り替える", "window.gdListSetKind('class_hw')" in _js_block(ceo, "    function chwShowResults() {"))
    check("inline onclick から呼ぶ関数を window に出している",
          all(f"window.{f_} = {f_}" in ceo for f_ in ("chwDryRun", "chwRunClass", "chwShowResults")))

    rd = client.post("/api/admin/class-homework-routine/run", json={"dry_run": True, "all_classes": True, "include_names": True}, headers=adm)
    dj = rd.json() if rd.status_code == 200 else {}
    check("CEO の管理者のトークンで 🔍 の応答が読める (名前つき)", rd.status_code == 200 and dj.get("plan_version") == 1, (rd.status_code, rd.text[:200]))
    check("毎朝の実行の記録が無ければ last_run は null (キーはある・2026-10-16)", "last_run" in dj and dj["last_run"] is None, dj.get("last_run"))
    mod._record_scheduler_run("class_hw_auto_run", mod._compact_run_props({"delivered": 5, "drills_created": 2, "assigned_students": [{"id": 1, "name": "架空"}]}))
    ev = q(mod, "SELECT created_at FROM events WHERE name = 'class_hw_auto_run' ORDER BY id DESC LIMIT 1")[0]
    ev_jst = datetime.datetime.strptime(str(ev["created_at"])[:19], "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=9)
    lr = (client.post("/api/admin/class-homework-routine/run", json={"dry_run": True, "all_classes": True}, headers=adm).json() or {}).get("last_run") or {}
    check("last_run: 毎朝の実行 (class_hw_auto_run) の最後の記録の JST の時刻と人数", lr.get("delivered") == 5 and lr.get("error") is None
          and lr.get("at_jst") == f"{ev_jst.month}/{ev_jst.day} {ev_jst:%H:%M}", (lr, str(ev["created_at"])))
    ex(mod, "DELETE FROM events WHERE name = 'class_hw_auto_run'")
    eng = js_engine()
    check("JS の実行環境がある (node / osascript / jsc。無ければ FAIL)", bool(eng))
    esc_line = _js_line(ceo, "    function escapeHtml(s) { return (s||'')")
    subj_ja = _js_between(ceo, "    const _GD_SUBJ_JA = {", "    // 📋 配信済みドリルの絞り込み")
    rt_card = _js_between(ceo, "    const _GD_RT_REASON_JA = {", "    let _gdRtBusy = false;")
    chw = _js_between(ceo, "    // 🏫 クラス自動宿題の確認・配信カード", "    async function gdAnalytics(drillId) {")
    check("CEO のコードを切り出せた", all((esc_line, subj_ja, rt_card, chw)))
    if not eng or not all((esc_line, subj_ja, rt_card, chw)):
        return
    run_resp = {"ok": True, "plan_version": 1, "dry_run": False, "delivered": 2, "drills_created": 1, "drills_joined": 0, "skipped_race": 1}
    prog = "\n".join([
        "var window = (typeof globalThis !== 'undefined') ? globalThis : this;",
        "var __els = {};",
        "function __el(id) { if (!__els[id]) __els[id] = { id: id, innerHTML: '', disabled: false, scrollIntoView: function () { __o.scrolled = true; } }; return __els[id]; }",
        "var document = { getElementById: function (id) { return __el(id); } };",
        "var __o = { posts: [], confirms: [], kinds: [] };",
        "var __confirmAnswer = false;",
        "function confirm(t) { __o.confirms.push(String(t)); return __confirmAnswer; }",
        f"var __dry = {json.dumps(dj, ensure_ascii=False)};",
        f"var __run = {json.dumps(run_resp, ensure_ascii=False)};",
        "function __res(status, body) { return { ok: status === 200, status: status, json: function () { return Promise.resolve(body); } }; }",
        "var AdminAuth = { fetch: function (path, opt) { var b = JSON.parse((opt && opt.body) || '{}'); __o.posts.push({ path: path, body: b });"
        " return Promise.resolve(__res(200, b.dry_run === false ? __run : __dry)); } };",
        "window.gdListSetKind = function (k) { __o.kinds.push(k); };",
        esc_line, subj_ja, rt_card, chw,
        "__o.render = _chwRender(__dry);",
        "var __d2 = JSON.parse(JSON.stringify(__dry)); __d2.last_run = { at_jst: '10/21 06:00', delivered: 5, error: null }; __d2.stale_open_ignored = 1;",
        "__d2.settings = __d2.settings || {}; __d2.settings.open_stale_days = 14; __o.renderLr = _chwRender(__d2);",
        "__o.renderRun = _chwRender({ plan_version: 1, dry_run: false, delivered: 2, last_run: { at_jst: '10/21 06:00', delivered: 5 }, settings: {}, classes: [] });",
        "__o.old = _chwRender({ ok: true, delivered: 3 });",
        "__o.unk = _chwRender({ plan_version: 1, settings: { only_classes: [], only_classes_unknown: ['火曜2限 英文法 Lv.3<b>'] }, classes: [] });",
        "__o.wait = _chwPlanCell({ group: 'kosei', subject: 'english', members: 2, ok: false, mode: 'wait', reason: 'wait_next', drill_id: 7, tried: [] });",
        "async function __ticks() { for (var i = 0; i < 30; i++) { await null; } }",
        "(async function () {",
        "  await chwDryRun();",
        "  __o.afterDry = __el('chwResult').innerHTML; __o.state = __el('chwState').innerHTML;",
        "  var idx = -1; for (var i = 0; i < __dry.classes.length; i++) { if (__dry.classes[i].students.some(function (e) { return e.status === 'deliver'; })) { idx = i; break; } }",
        "  __o.idx = idx; __o.label = idx >= 0 ? __dry.classes[idx].label : null;",
        "  await chwRunClass(idx); __o.postsAfterNo = __o.posts.length;",
        "  __confirmAnswer = true; await chwRunClass(idx); await __ticks();",
        "  __o.msg = __el('chwMsg').innerHTML;",
        "  await chwRunClass(999); __o.postsAfterBad = __o.posts.length;",
        "  chwShowResults();",
        "  " + _JS_OUT.replace("\n", "\n  "),
        "})();",
    ])
    out, err = run_js(eng, prog)
    check("🏫 カードのコードが JS で動く", out is not None, err)
    out = out or {}
    rend = out.get("render", "")
    check("15 クラスの表 (クラス名つき)", rend.count("<tr>") >= 15 + 1 and "火曜2限 英文法 Lv.2" in rend, rend[:300])
    rl = out.get("renderLr", "")
    check("見出しは「今もう一度回したら配る」(「今朝回ったら」は朝の実行の後に読み違える・2026-10-16)・記録なしは「まだ記録がありません」",
          "今もう一度回したら配る:" in rend and "今朝回ったら" not in rend and "前回の自動配信: まだ記録がありません" in rend, rend[:400])
    check("前回の自動配信: 10/21 06:00 に 5 名 (見出しの上)・古い未提出のチップ (14日より前)", "前回の自動配信: 10/21 06:00 に 5 名" in rl
          and rl.index("前回の自動配信") < rl.index("今もう一度回したら配る") and "14日より前の未提出は数えない 1名" in rl, rl[:400])
    check("📤 の後の応答 (dry_run: false) は「配った」で、前回の自動配信は出さない", "配った: 2 名" in out.get("renderRun", "")
          and "前回の自動配信" not in out.get("renderRun", ""), out.get("renderRun", "")[:300])
    check("名前の HTML は escape される (<img を出さない)", "&lt;img" in rend and "<img" not in rend, rend[:300])
    check("学年の HTML も escape される", "&lt;b&gt;未設定&lt;/b&gt;" in rend and "<b>未設定" not in rend)
    check("配る生徒は id つき・押すと生徒詳細", f"window.showStudentDetail({ids['deliver']})" in rend, ids)
    check("ON/OFF が出る (既定は OFF)・お知らせはアプリの中だけ", "毎朝の自動配信 OFF" in rend and "アプリの中だけ" in rend)
    check("外した理由が日本語のチップで出る (学年が判定できない・GMARCH・早慶だけ)", "学年が判定できない" in rend and "GMARCH・早慶だけ" in rend)
    check("📤 はクラスの番号だけを渡す", re.search(r'onclick="chwRunClass\(\d+\)"', rend) is not None)
    check("plan_version の無い古い応答は「サーバ反映待ち」", "反映待ち" in out.get("old", "") and "配る" not in out.get("old", ""))
    check("CLASS_HW_AUTO_ONLY_CLASSES の知らない名前を赤いチップで出す (escape・当たる名前が無ければ「どのクラスにも配りません」)",
          "知らないクラス名" in out.get("unk", "") and "&lt;b&gt;" in out.get("unk", "") and "<b>" not in out.get("unk", "x").split("知らないクラス名")[1]
          and "どのクラスにも配りません" in out.get("unk", ""), out.get("unk", "")[:300])
    check("前の日のドリルを待つ区分は ⏸ で出す (❌ にしない)", "⏸" in out.get("wait", "") and "❌" not in out.get("wait", "x")
          and "ドリル #7" in out.get("wait", ""), out.get("wait"))
    posts = out.get("posts") or []
    check("🔍 → 送ったのは dry_run: true・all_classes・include_names", posts[:1] and posts[0]["path"] == "/api/admin/class-homework-routine/run"
          and posts[0]["body"] == {"dry_run": True, "all_classes": True, "include_names": True}, posts[:1])
    check("📤 で confirm() に「いいえ」なら送らない", out.get("postsAfterNo") == 1 and out.get("confirms"), out.get("postsAfterNo"))
    check("confirm() の文にクラス名と人数", out.get("confirms") and out.get("label") and out["label"] in out["confirms"][0]
          and "名に、クラス自動宿題を今すぐ配信" in out["confirms"][0], out.get("confirms"))
    check("📤 で「はい」→ dry_run: false と class_label (そのクラスだけ)・その後 🔍 で表を読み直す",
          len(posts) >= 3 and posts[1]["body"] == {"dry_run": False, "class_label": out.get("label"), "include_names": True}
          and posts[2]["body"].get("dry_run") is True, posts[1:3])
    check("📤 の結果の文 (配った人数・新しいドリル・別の実行が先に配った)", "2 名に配信しました" in out.get("msg", "") and "別の実行が先に配った 1 名" in out.get("msg", ""),
          out.get("msg"))
    check("知らない番号の 📤 は何も送らない", out.get("postsAfterBad") == len(posts), (out.get("postsAfterBad"), len(posts)))
    check("「📋 結果」→ 一覧の絞り込みを class_hw に", out.get("kinds") == ["class_hw"] and out.get("scrolled") is True, out.get("kinds"))

    parts = [_js_block(cls, "    function esc(s) {"), _js_line(cls, "    function _pad2(n) {"), _js_line(cls, "    function gdIsOpen(x) {"),
             _js_block(cls, "    function gdLocalDate(s, withTime) {"), _js_block(cls, "    function gdMetaText(it) {")]
    check("class.html のカードのコードを切り出せた", all(parts))
    if not all(parts):
        return
    prog2 = "\n".join(["var window = (typeof globalThis !== 'undefined') ? globalThis : this;"] + parts + [
        "var __o = {};",
        "__o.due = gdMetaText({ subject: 'english', title: '【火曜2限 英文法 Lv.2】宿題 時制（10問・〆10/23）', status: 'open', score_total: 10 });",
        "__o.plain = gdMetaText({ subject: 'english', title: '時制ドリル（標準・10問）', status: 'open', score_total: 10 });",
        "__o.pt = gdMetaText({ subject: 'proficiency_test', title: 'テスト〆', status: 'open', score_total: 9 });",
        "__o.done = gdMetaText({ subject: 'english', title: '宿題（10問・〆10/23）', status: 'completed', score_correct: 7, score_total: 10 });",
        _JS_OUT,
    ])
    out2, err2 = run_js(eng, prog2)
    check("塾生アプリのカードの 2 行目のコードが JS で動く", out2 is not None, err2)
    out2 = out2 or {}
    check("題名に 〆 があれば「いつでもOK」と書かない (題名の 10問 も重ねない)",
          "いつでもOK" not in out2.get("due", "x") and "その場で自動採点" in out2.get("due", "") and "全 10 問" not in out2.get("due", ""), out2.get("due"))
    check("〆 の無い題名は今までどおり「その場で自動採点 ・ いつでもOK」", "その場で自動採点 ・ いつでもOK" in out2.get("plain", ""), out2.get("plain"))
    check("習熟度テストの文は変えない", "授業の指示どおりに解いて提出 ・ 提出は1回だけ" in out2.get("pt", ""), out2.get("pt"))
    check("提出済みはスコア", "スコア 7 / 10" in out2.get("done", ""), out2.get("done"))
    check("class.html: カードの 2 行目は今も gdMetaText(it) の 1 か所", "var meta = gdMetaText(it);" in cls)


def main():
    print("🏫 クラス自動宿題 (塾生アプリのみ枠・英語だけ・2 日に 1 回・レビュー済みだけ・中高の取り違えなし) 回帰テスト\n")
    mod = load_main()
    rec = Recorder(mod)
    src = open(MAIN_PY, encoding="utf-8").read()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app, raise_server_exceptions=False)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    api = Api(mod, client, adm)
    for fname, subj in SEEDS:
        d = load_seed(fname)
        t = import_like_ceo(api, "questions", d["questions"] if isinstance(d, dict) else d, subj, 400)
        check(f"シード {fname} が入る", t["inserted"] > 0 and t["errors"] == 0, str(t)[:200])
    d = load_seed("eiken_reading_pool_v1.json")
    t = import_like_ceo(api, "passages", d["passages"], "eiken", 20)
    check("英検の長文 (本文つき) が入る", t["passages_inserted"] > 0 and t["errors"] == 0, str(t)[:200])

    T0 = datetime.datetime(2026, 10, 20, 21, 0, 5, tzinfo=datetime.timezone.utc)   # = JST 10/21 (水) 6:00:05

    def at(days, hours=0):
        return T0 + datetime.timedelta(days=days, hours=hours)

    seq = [0]

    def make(grade, labels, *, ai_disabled=1, trial=None, status="paid", plan="student_addon", course=None, name=None,
             email=None, start_month=None):
        seq[0] += 1
        n = name or f"架空 生徒{seq[0]:03d}"
        conn = mod.db(); c = conn.cursor()
        c.execute("INSERT INTO students (name, email, status, grade, ai_disabled, ai_trial_until, plan, course, class_labels, start_month) "
                  "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id",
                  (n, email or f"chw-{seq[0]:03d}@example.org", status, grade, ai_disabled, trial, plan, course,
                   json.dumps(labels, ensure_ascii=False), start_month))
        sid = c.fetchone()["id"]
        conn.commit(); conn.close()
        return sid

    def weak(sid, subject, topic, acc=0.3, att=10):
        ex(mod, "INSERT INTO student_weakness (student_id, subject, topic, question_count, qa_accuracy, qa_attempts) VALUES (?, ?, ?, ?, ?, ?)",
           (sid, subject, topic, att, acc, att))

    def only_active(ids):
        """全員の実行の対象をこの生徒だけにする (ほかは退会扱い)。"""
        ex(mod, f"UPDATE students SET status = CASE WHEN id IN ({','.join('?' * len(ids))}) THEN 'paid' ELSE 'canceled' END", tuple(ids))

    def reset_chw():
        ex(mod, f"DELETE FROM grammar_drill_assignments WHERE drill_id IN (SELECT id FROM grammar_drills WHERE substr(COALESCE(created_by,''),1,14) = '{PREFIX}')")
        ex(mod, f"DELETE FROM grammar_drills WHERE substr(COALESCE(created_by,''),1,14) = '{PREFIX}'")

    def complete_all(sid=None):
        if sid is None:
            ex(mod, "UPDATE grammar_drill_assignments SET status = 'completed'")
        else:
            ex(mod, "UPDATE grammar_drill_assignments SET status = 'completed' WHERE student_id = ?", (sid,))

    def run(dry=False, now=None, **kw):
        return mod._run_class_homework_routine(dry_run=dry, now=now or T0, **kw)

    def drills_of(sid):
        return q(mod, "SELECT d.id, d.subject, d.unit, d.title, d.question_ids, d.created_by, d.level, a.status, a.assigned_at "
                      "FROM grammar_drill_assignments a JOIN grammar_drills d ON d.id = a.drill_id "
                      f"WHERE a.student_id = ? AND substr(COALESCE(d.created_by,''),1,14) = '{PREFIX}' ORDER BY d.id", (sid,))

    def due_of(x):
        """題名の 〆M/D → date (2026 年)。無ければ None。"""
        import re as _re
        m = _re.search(r"〆(\d+)/(\d+)", x.get("title") or "")
        return datetime.date(2026, int(m.group(1)), int(m.group(2))) if m else None

    def recv_jst(x):
        """受け取った日 (assigned_at = naive UTC) の JST の日付。"""
        return (datetime.datetime.strptime(str(x["assigned_at"])[:19], "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=9)).date()

    def status_of(res, sid, label=None):
        for row in res.get("classes", []):
            if label and row["label"] != label:
                continue
            for e in row.get("students", []):
                if e["id"] == sid:
                    return e["status"]
        return None

    def group_of(res, label, group):
        for row in res.get("classes", []):
            if row["label"] == label:
                for g in row["groups"]:
                    if g["group"] == group:
                        return g
        return {}

    # ------------------------------------------------------------------
    print("\n[1] クラスの表・ON/OFF・監視")
    mp = mod._CLASS_HW_ROUTINE_MAP
    check("表のキー = 時間割のクラス名 (15)", set(mp) == mod._TIMETABLE_LABELS and len(mp) == 15, sorted(set(mp) ^ mod._TIMETABLE_LABELS))
    check("kind は grammar / eiken / reading / hold / none だけ", {v["kind"] for v in mp.values()} <= {"grammar", "eiken", "reading", "hold", "none"})
    check("日曜 高校国語 = none・GMARCH と早慶 = hold", mp["日曜 高校国語"]["kind"] == "none"
          and mp["水曜2限 GMARCH"]["kind"] == "hold" and mp["木曜2限 早慶クラス"]["kind"] == "hold")
    unit_order = mod._GRAMMAR_SUBJECT_UNIT_ORDER
    bad = []
    for lb, ent in mp.items():
        for g in ("kosei", "chugaku"):
            rg = mod._class_hw_range(lb, g)
            if not rg:
                continue
            allowed = set(mod.GRAMMAR_UNITS) if rg["subject"] == "english" else set(unit_order.get(rg["subject"], []))
            if not set(rg["units"]) <= allowed or not rg["units"]:
                bad.append((lb, g, "units"))
            if not set(rg["levels"]) <= set(mod.GRAMMAR_LEVELS) or not rg["levels"]:
                bad.append((lb, g, "levels"))
            if rg["subject"] not in mod._CLASS_HW_SUBJECTS_BY_GROUP[g] or not mod._drill_subject_band_ok(rg["subject"], g):
                bad.append((lb, g, rg["subject"]))
    check("どの (クラス, 区分) も単元は科目の単元表の中・レベルは 3 つの中・科目は区分で出してよいもの", not bad, bad)
    rd = {lb: mod._class_hw_range(lb, "kosei") for lb in ("月曜3限 長文読解 Lv.1", "火曜3限 長文読解 Lv.2", "金曜3限 国公立コース 長文読解")}
    check("長文のクラスは english_long の単元 (長文 Lv.1 / 長文 Lv.2 / 国公立 長文)・標準だけ (critic C4)",
          [(r["subject"], r["units"], r["levels"]) for r in rd.values()]
          == [("english_long", ("長文 Lv.1",), ("standard",)), ("english_long", ("長文 Lv.2",), ("standard",)),
              ("english_long", ("国公立 長文",), ("standard",))], rd)
    check("長文のクラスの中学生には出さない (no_range)", all(mod._class_hw_range(lb, "chugaku") is None for lb in rd))
    e1, e2 = mod._class_hw_range("木曜1限 英検準1級対策", "chugaku"), mod._class_hw_range(EIKEN2, "kosei")
    check("英検のクラスはその級の単元だけ (学年を問わない)", e1 and all(u.startswith("準1級") for u in e1["units"])
          and e2 and all(u.startswith("2級") for u in e2["units"]) and e1["subject"] == e2["subject"] == "eiken", (e1, e2))
    check("中学基礎・中学2年 英語の中学生は中1・中2 の 8 単元・基礎+標準",
          mod._class_hw_range("火曜1限 中学基礎", "chugaku")["units"] == mod._CHU_ENG_UNITS_JH12
          and len(mod._CHU_ENG_UNITS_JH12) == 8 and mod._class_hw_range("水曜1限 中学2年 英語", "chugaku")["levels"] == ("basic", "standard"))
    check("レベル: 英文法 Lv.1 基礎+標準・Lv.2/国公立 標準+やや難・高2 標準・中学応用 標準+やや難 (2026-10-15 の既定)",
          (mod._class_hw_range("月曜2限 英文法 Lv.1", "kosei")["levels"], mod._class_hw_range(LV2, "kosei")["levels"],
           mod._class_hw_range("水曜3限 国公立コース 英文法", "kosei")["levels"], mod._class_hw_range("金曜1限 高2 英文法", "kosei")["levels"],
           mod._class_hw_range("月曜1限 中学応用", "chugaku")["levels"])
          == (("basic", "standard"), ("standard", "advanced"), ("standard", "advanced"), ("standard",), ("standard", "advanced")))
    check("習熟度テストはどのクラスにも無い (自動では出さない)", "proficiency_test" not in json.dumps(mp, ensure_ascii=False))
    with Env(CLASS_HW_AUTO_ENABLED=None):
        check("CLASS_HW_AUTO_ENABLED 未設定なら OFF", mod._class_hw_routine_env_enabled() is False and mod._class_hw_routine_enabled() is False)
    for v in ("1", "true", "YES", " on "):
        with Env(CLASS_HW_AUTO_ENABLED=v):
            check(f"{v!r} なら ON (スケジューラと監視が同じ関数)", mod._class_hw_routine_enabled() is True)
    for v in ("", "0", "false", "off", "2"):
        with Env(CLASS_HW_AUTO_ENABLED=v):
            check(f"{v!r} なら OFF", mod._class_hw_routine_enabled() is False)
    check("既定 (OFF) で import した監視の dict に class_hw_auto_run は無い", "class_hw_auto_run" not in mod._SCHEDULER_MAX_AGE_DAYS)
    try:
        on_keys = _scheduler_keys_in_subprocess("1")
        check("CLASS_HW_AUTO_ENABLED=1 で import すると class_hw_auto_run が 2 日で入る", on_keys.get("class_hw_auto_run") == 2, on_keys)
    except Exception as e:
        check("別プロセスの import", False, e)
    check("停止・失敗の通知の名前の表 2 つにラベルがある", src.count('"class_hw_auto_run": "クラス自動宿題 (毎朝6時・塾生アプリのみ枠)"') == 2)
    ps = open(os.path.join(REPO, "scripts", "prod_status.py"), encoding="utf-8").read()
    check("prod_status.py にラベルがある", "'class_hw_auto_run':" in ps)
    spec = importlib.util.spec_from_file_location("prod_hc_class_hw", os.path.join(HERE, "prod_healthcheck.py"))
    hc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hc)
    check("prod_healthcheck: class_hw_auto_run は OPTIONAL_UNTIL_FIRST_RUN", "class_hw_auto_run" in hc.OPTIONAL_UNTIL_FIRST_RUN)

    class _HcCur:
        def execute(self, sql, params=None):
            self.last = sql

        def fetchone(self):
            return (None,)

    hc._table_exists = lambda cur, name: True
    hc.results.clear()
    hc.check_scheduler_live(_HcCur())
    mine = [r for r in hc.results if "class_hw_auto_run" in r[2]]
    check("prod_healthcheck: 履歴が無いうちは PASS (未有効化)", mine and all(r[1] == hc.PASS for r in mine), mine)
    sched = inspect.getsource(mod._class_hw_routine_scheduler)
    check("スケジューラは毎日 env を見る・今日の実行記録で 2 回目を飛ばす・to_thread・要約を記録",
          "if not _class_hw_routine_enabled():" in sched and '_check_scheduler_ran_today_jst, "class_hw_auto_run"' in sched
          and "asyncio.to_thread(_run_class_homework_routine" in sched and "props = _compact_run_props(result)" in sched
          and '_record_scheduler_run, "class_hw_auto_run", props' in sched)
    check("起動時に登録する (CRON_SECRET のとき・env は毎日ループで見る)", "asyncio.create_task(_class_hw_routine_scheduler())" in src)
    for v, want in (("3", 5), ("23", 22), ("abc", 6), (None, 6), ("7", 7)):
        with Env(CLASS_HW_AUTO_HOUR_JST=v):
            check(f"CLASS_HW_AUTO_HOUR_JST={v!r} → {want} 時 (4:00 の弱点集計より前にしない)", mod._class_hw_hour_jst() == want, mod._class_hw_hour_jst())
    check("_ai_blocked_now の注記にクラス自動宿題がある", "クラス自動宿題 (_class_hw_plan" in inspect.getdoc(mod._ai_blocked_now))
    dsrc = inspect.getsource(mod._class_hw_deliver_group)
    check("書き込みの錠は 1 引数の 8675314 を f-string で (3日ドリルの (8675313, 生徒ID) と別)",
          mod._CLASS_HW_PG_LOCK_KEY == 8675314 and "pg_try_advisory_xact_lock({int(_CLASS_HW_PG_LOCK_KEY)})" in dsrc)
    chw_src = "".join(inspect.getsource(f) for f in (mod._run_class_homework_routine, mod._class_hw_plan, mod._class_hw_plan_group,
                                                      mod._class_hw_deliver_group, mod.admin_class_homework_routine_run))
    check("クラス自動宿題は LINE を直接送らない・3日ドリルの作成関数を使わない・CEO の抽出関数を使わない",
          "_do_line_push" not in chw_src and "_create_routine_grammar_drill" not in chw_src
          and "_grammar_pick_drill_question_ids" not in chw_src and "_grammar_pick_drill_passages" not in chw_src)
    check("お知らせは source='auto' で呼ぶ", '_notify_grammar_drill_assigned(g["notify"], g["unit"], g["nq"], g["subject"], source="auto")' in chw_src)
    check("学年は _student_grade_band (判定できない学年を高校生扱いにしない)", "_student_grade_band(st[\"grade\"])" in chw_src
          and "unknown_as_kosei" not in inspect.getsource(mod._class_hw_plan))

    # ------------------------------------------------------------------
    print("\n[2] 対象の生徒 (英文法 Lv.2 のクラス)")
    future = mod._utc_naive_iso(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=5))
    past = mod._utc_naive_iso(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
    k1 = make("高校2年", [LV2])
    c1 = make("中学3年", [LV2])
    ai1 = make("高校2年", [LV2], ai_disabled=0)
    tr1 = make("高校2年", [LV2], trial=future)
    trx = make("高校1年", [LV2], trial=past)
    syn = make("高校2年", [LV2], email="chw-x@synthetic-monitor.local")
    tst = make("高校2年", [LV2], name="テスト 生徒")
    can = make("高校2年", [LV2], status="canceled")
    nts = make("高校2年", [LV2], plan="premium")
    ntc = make("高校2年", ["日曜 高校国語"])
    nolab = make("高校2年", [])
    gu1 = make("", [LV2])
    gu2 = make("その他", [LV2])
    sho = make("小6", [LV2])
    hold = make("高校3年", ["水曜2限 GMARCH"])
    nr = make("中学2年", [READ1])
    bs = make("高校2年", [LV2], start_month="2026-11")
    bs_ok = make("高校2年", [LV2], start_month="2026-10")
    crs = make("高校3年", [LV2], plan=None, course="kokuritsu_nankan")
    before = counts(mod)
    r = run(dry=True, seed=3, include_names=True)
    check("dry-run は何も書かない", counts(mod) == before, (before, counts(mod)))
    want = {k1: "deliver", c1: "deliver", tr1: "ai_trial", trx: "deliver", tst: "test_name", nts: "not_tsujuku", ntc: "no_class",
            nolab: "no_class", gu1: "grade_unknown", gu2: "grade_unknown", sho: "shougaku", hold: "hold_only", nr: "no_range",
            bs: "before_start", bs_ok: "deliver", crs: "deliver"}
    got = {}
    for row in r["classes"]:
        for e in row["students"]:
            got.setdefault(e["id"], e["status"])
    # クラスの表に出ない生徒 (英語のクラスが無い) は skipped の数で見る
    check("英語のクラスが無い生徒は skipped_no_class (2 名)", r["skipped_no_class"] == 2, r["skipped_no_class"])
    for sid, w in want.items():
        if w == "no_class":
            continue
        check(f"生徒 #{sid} は {w}", got.get(sid) == w, got.get(sid))
    allids = {e["id"] for row in r["classes"] for e in row["students"]}
    check("AIあり・合成監視・退会の生徒はクラス自動宿題の候補にも出ない", not ({ai1, syn, can} & allids), {ai1, syn, can} & allids)
    check("判定できない学年の生徒は名前と学年つきで返す (CEO で直す)",
          sorted(e["id"] for e in r["grade_unknown_students"]) == sorted([gu1, gu2])
          and all(e.get("name") for e in r["grade_unknown_students"]), r["grade_unknown_students"])
    check("skipped_* の数 (体験中 1・通塾生でない 1・テスト名 1・学年 2・小学生 1・GMARCH だけ 1・範囲なし 1・開始月前 1)",
          (r["skipped_ai_trial"], r["skipped_not_tsujuku"], r["skipped_test_name"], r["skipped_grade_unknown"], r["skipped_shougaku"],
           r["skipped_hold_only"], r["skipped_no_range"], r["skipped_before_start"]) == (1, 1, 1, 2, 1, 1, 1, 1),
          {k: v for k, v in r.items() if k.startswith("skipped_")})
    gk, gc = group_of(r, LV2, "kosei"), group_of(r, LV2, "chugaku")
    check("高校生 → english・中学生 → chugaku の別々のドリル (同じクラス)", gk.get("subject") == "english" and gc.get("subject") == "chugaku"
          and gk.get("ok") and gc.get("ok") and gk.get("deliver_n") == 4 and gc.get("deliver_n") == 1, (gk, gc))
    res = run(seed=3)
    check("本番: 5 名に配る・ドリルは 2 本", res["delivered"] == 5 and res["drills_created"] == 2 and not res.get("error"), res)
    dk, dc = drills_of(k1), drills_of(c1)
    check("高校生のドリルは english・created_by = class_hw_auto:kosei:<クラス名>",
          len(dk) == 1 and dk[0]["subject"] == "english" and dk[0]["created_by"] == f"{PREFIX}kosei:{LV2}", dk)
    check("中学生のドリルは chugaku・created_by = class_hw_auto:chugaku:<クラス名>",
          len(dc) == 1 and dc[0]["subject"] == "chugaku" and dc[0]["created_by"] == f"{PREFIX}chugaku:{LV2}", dc)
    check("題名「【<クラス名>】宿題 <単元>（10問・〆M/D）」(〆 = JST で配った日の 2 日後)",
          dk and dk[0]["title"] == f"【{LV2}】宿題 {dk[0]['unit']}（10問・〆10/23）", dk[0]["title"] if dk else None)
    check("レベルは表のとおり (Lv.2 = 標準+やや難)", dk and dk[0]["level"] == "standard,advanced", dk[0]["level"] if dk else None)
    check("体験が切れた AIなし・開始月が今月・course=kokuritsu_nankan の通塾生にも配る",
          all(len(drills_of(s)) == 1 for s in (trx, bs_ok, crs)))
    check("配らない生徒には何も無い", all(not drills_of(s) for s in (tr1, ai1, syn, tst, can, nts, gu1, gu2, sho, hold, nr, bs)))
    first_k1_qids = json.loads(dk[0]["question_ids"]) if dk else []

    # ------------------------------------------------------------------
    print("\n[3] 中高の取り違えなし・学年ガード")

    def all_mode_ok():
        bad_ = []
        for d_ in q(mod, f"SELECT id, subject, created_by, question_ids FROM grammar_drills WHERE substr(COALESCE(created_by,''),1,14) = '{PREFIX}'"):
            grp = d_["created_by"].split(":")[1]
            ids = json.loads(d_["question_ids"])
            subs = {x["subject"] for x in q(mod, f"SELECT subject FROM grammar_questions WHERE id IN ({','.join('?' * len(ids))})", tuple(ids))}
            if subs != {d_["subject"]}:
                bad_.append((d_["id"], "q_subject", subs))
            if not mod._drill_subject_band_ok(d_["subject"], grp):
                bad_.append((d_["id"], "band", grp, d_["subject"]))
            for a in q(mod, "SELECT s.grade FROM grammar_drill_assignments a JOIN students s ON s.id = a.student_id WHERE a.drill_id = ?", (d_["id"],)):
                if mod._student_grade_band(a["grade"]) != grp:
                    bad_.append((d_["id"], "assignee", a["grade"]))
        return bad_

    check("english のドリルは高校生だけ・chugaku は中学生だけ・問題の科目 = ドリルの科目", not all_mode_ok(), all_mode_ok())
    trips0 = mod._CLASS_HW_BAND_GUARD_TRIPS
    conn = mod.db(); c = conn.cursor()
    fake = {"mode": "new", "subject": "english", "unit": "時制", "qids": first_k1_qids, "title": "x", "levels": ["standard"]}
    rr = mod._class_hw_deliver_group(c, conn, LV2, "chugaku", fake, [{"id": c1, "band": "chugaku", "s": {"id": c1}}],
                                     now_txt="2026-10-30 21:00:00", interval_cutoff="2026-10-29 03:00:00")
    rr2 = mod._class_hw_deliver_group(c, conn, LV2, "kosei", dict(fake), [{"id": c1, "band": "chugaku", "s": {"id": c1}}],
                                      now_txt="2026-10-30 21:00:00", interval_cutoff="2026-10-29 03:00:00")
    conn.close()
    check("書き込み直前のガード: 中学生の区分に english → 書かない (数える)", rr.get("error") == "band_guard" and not rr["assigned"], rr)
    check("書き込み直前のガード: 高校の区分に中学生 → 書かない (数える)", rr2.get("error") == "band_guard" and not rr2["assigned"], rr2)
    check("ガードは 2 回数えた・ドリルは増えていない", mod._CLASS_HW_BAND_GUARD_TRIPS - trips0 == 2 and len(drills_of(c1)) == 1)
    mod._CLASS_HW_BAND_GUARD_TRIPS = trips0
    check("通常の実行ではガードは 0 回", res.get("band_guard_trips") == 0, res.get("band_guard_trips"))

    # ------------------------------------------------------------------
    print("\n[4] レビュー済みだけ (未レビューの行・長文の本文の数)")
    conn = mod.db(); c = conn.cursor()
    for i in range(100):
        c.execute("INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source, active) "
                  "VALUES ('english', '時制', 'standard', ?, ?, 0, '解説', ?, 1)",
                  (f"未レビューの架空の問題 {i} (   ).", json.dumps(["a", "b", "c", "d"]), "pool" if i % 2 else "pt-x-1"))
    conn.commit()
    bad_src, picks = set(), 0
    for s_ in range(20):
        gp = mod._class_hw_plan_group(c, LV2, "kosei", members=[k1], weak_rows=[], hist=[], settings=mod._class_hw_settings(),
                                      now_txt="2026-11-01 21:00:00", interval_cutoff="2026-10-31 03:00:00", rng=random.Random(s_))
        if gp["ok"]:
            picks += 1
            for x in q(mod, f"SELECT source FROM grammar_questions WHERE id IN ({','.join('?' * len(gp['qids']))})", tuple(gp["qids"])):
                if not mod._auto_delivery_source_ok("english", x["source"]):
                    bad_src.add(x["source"])
    conn.close()
    check("未レビュー (pool / pt-) が 100 問あっても 20 回選んで 1 問も出ない", picks == 20 and not bad_src, (picks, bad_src))
    rl = make("高校1年", [READ1])
    only_active([rl])
    conn = mod.db(); c = conn.cursor()
    for i in range(6):   # 未レビューの本文 (取込を通さず直接入った行) は数えない
        c.execute("INSERT INTO grammar_passages (subject, unit, level, title, body, source, active) VALUES ('english_long', '長文 Lv.1', 'standard', ?, ?, ?, 1) RETURNING id",
                  (f"draft {i}", f"Unreviewed fictional draft body {i}.", f"codex-draft-{i}"))
        pid = c.fetchone()["id"]
        for k in range(3):
            c.execute("INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source, active, passage_id, passage_seq) "
                      "VALUES ('english_long', '長文 Lv.1', 'standard', ?, ?, 0, '解説', ?, 1, ?, ?)",
                      (f"draft q {i}-{k}", json.dumps(["a", "b", "c", "d"]), f"el-draft-{i}-{k}", pid, k))
    conn.commit(); conn.close()
    r = run(dry=True)
    g_ = group_of(r, READ1, "kosei")
    check("未レビューの本文しか無い長文クラスは配らない (no_reviewed_inventory)", not g_.get("ok") and g_.get("reason") == "no_reviewed_inventory"
          and status_of(r, rl) == "no_inventory", g_)

    def imp(passages):
        mod._RATE_LIMIT_STORE.clear()
        rr_ = client.post("/api/admin/grammar/import", json={"subject": "english_long", "dedup": True, "all_or_nothing": True,
                                                             "review": REVIEW, "passages": passages}, headers=adm)
        return rr_.status_code, (rr_.json() if rr_.status_code == 200 else rr_.text[:200])

    sc, dd = imp([el_passage("CHW001", n) for n in range(1, 4)])
    check("レビュー済みの本文 3 本を取込", sc == 200 and dd.get("passages_inserted") == 3, dd)
    r = run(dry=True)
    g_ = group_of(r, READ1, "kosei")
    check("3 本 (< CLASS_HW_READING_MIN_PASSAGES=4) ではまだ始めない (below_threshold)", not g_.get("ok") and g_.get("reason") == "below_threshold", g_)
    with Env(CLASS_HW_READING_MIN_PASSAGES="3"):
        check("CLASS_HW_READING_MIN_PASSAGES=3 なら始まる", group_of(run(dry=True), READ1, "kosei").get("ok") is True)
    sc, dd = imp([el_passage("CHW002", n) for n in range(4, 5)])
    check("4 本目を取込", sc == 200 and dd.get("passages_inserted") == 1, dd)
    res = run()
    dl = drills_of(rl)
    ids = json.loads(dl[0]["question_ids"]) if dl else []
    rows = q(mod, f"SELECT id, passage_id, passage_seq, source FROM grammar_questions WHERE id IN ({','.join('?' * len(ids))})", tuple(ids)) if ids else []
    check("4 本で始まる: 英語長文の本文 1 本 (設問 3 問・題名は 3問)", len(dl) == 1 and dl[0]["subject"] == "english_long"
          and dl[0]["unit"] == "長文 Lv.1" and len({x["passage_id"] for x in rows}) == 1 and len(ids) == 3
          and "（3問・〆" in dl[0]["title"], (dl, rows))
    check("長文の設問はレビュー済みの出典 el- だけ・passage_seq の順", rows and all(x["source"].startswith("el-CHW00") for x in rows)
          and [x["id"] for x in sorted(rows, key=lambda x: x["passage_seq"])] == ids, rows)

    # ------------------------------------------------------------------
    print("\n[5] 英検 (クラスの級・長文は本文 2 本)")
    e3 = make("中学3年", [EIKEN2])
    only_active([e3])
    res = run()
    de = drills_of(e3)
    check("英検2級対策の中3 → eiken の 2級 の単元 (単語から)", len(de) == 1 and de[0]["subject"] == "eiken" and de[0]["unit"] == "2級 単語"
          and de[0]["created_by"] == f"{PREFIX}chugaku:{EIKEN2}", de)
    complete_all(e3)
    res = run(now=at(2))
    de = drills_of(e3)
    ids = json.loads(de[-1]["question_ids"]) if len(de) == 2 else []
    rows = q(mod, f"SELECT id, passage_id, passage_seq, unit FROM grammar_questions WHERE id IN ({','.join('?' * len(ids))})", tuple(ids)) if ids else []
    by_id = {r_["id"]: r_ for r_ in rows}
    in_order = [by_id[i] for i in ids if i in by_id]
    runs = []   # 本文の並び (同じ本文の設問が続けて出る = 本文ごとにまとまっている)
    for x in in_order:
        if not runs or runs[-1] != x["passage_id"]:
            runs.append(x["passage_id"])
    seq_ok = all([x["passage_seq"] for x in in_order if x["passage_id"] == p] == sorted(x["passage_seq"] for x in in_order if x["passage_id"] == p)
                  for p in runs)
    check("2 日後は次の単元 (2級 長文空所補充)・本文 2 本・設問は本文ごとに passage_seq 順", len(de) == 2 and de[-1]["unit"] == "2級 長文空所補充"
          and len(in_order) == len(ids) and len(runs) == 2 and len(set(runs)) == 2 and seq_ok, (de[-1:], runs))

    # ------------------------------------------------------------------
    print("\n[6] 2 日に 1 回・積まない・同じドリルに足す・2 クラスは古い順")
    reset_chw()
    a1, a2 = make("高校2年", [LV2]), make("高校2年", [LV2])
    only_active([a1, a2])
    res = run()
    check("1 日目: 2 名に 1 本のドリル", res["delivered"] == 2 and res["drills_created"] == 1, res)
    res = run(now=at(0, 1))
    check("同じ日の 2 回目は増えない (未提出 = 積まない)", res["delivered"] == 0 and res["skipped_open"] == 2, res)
    complete_all()
    res = run(now=at(1))
    check("提出しても 2 日たつまでは配らない (recent)", res["delivered"] == 0 and res["skipped_recent"] == 2, res)
    res = run(now=at(2))
    da = drills_of(a1)
    check("2 日後 (同じ時刻) に次のドリル・単元は前と違う", res["delivered"] == 2 and res["drills_created"] == 1 and len(da) == 2
          and da[0]["unit"] != da[1]["unit"], [(x["unit"], x["assigned_at"]) for x in da])
    # 後から受け取れるようになった生徒: 同じ日 (JST) のドリルには足す・前の日のドリルには足さず次の新しいドリルを待つ
    reset_chw()
    b1, b2 = make("高校2年", [LV2]), make("高校2年", [LV2])
    only_active([b1, b2])
    run(now=at(-3))                 # 2 名とも 3 日前に受け取った
    complete_all(b1)                # b1 だけ提出 → 今日受け取れる。b2 は未提出
    res = run(now=at(0))
    check("b1 だけ新しいドリル (b2 は未提出なので積まない)", res["delivered"] == 1 and res["drills_created"] == 1 and res["skipped_open"] == 1, res)
    complete_all(b2)
    res = run(now=at(1))
    db2 = drills_of(b2)
    check("翌日 b2 が提出 → 昨日のドリルには足さない (〆 まで 1 日になる)・新しいドリルも作らない (wait_next)",
          res["delivered"] == 0 and res["drills_created"] == 0 and res["drills_joined"] == 0 and res.get("skipped_wait_next") == 1
          and status_of(res, b2) == "wait_next" and len(db2) == 1 and group_of(res, LV2, "kosei").get("reason") == "wait_next",
          (res.get("skipped_wait_next"), status_of(res, b2), group_of(res, LV2, "kosei")))
    complete_all(b1)
    res = run(now=at(2))
    db1, db2 = drills_of(b1), drills_of(b2)
    check("2 日後: b1 と b2 に同じ新しいドリル (足並みがそろう・〆 は配った日 + 2 日)", res["delivered"] == 2 and res["drills_created"] == 1
          and db1[-1]["id"] == db2[-1]["id"] and due_of(db2[-1]) == recv_jst(db2[-1]) + datetime.timedelta(days=2),
          (res.get("delivered"), db1[-1:], db2[-1:]))
    b3 = make("高校2年", [LV2])
    only_active([b1, b2, b3])
    res = run(now=at(2, 5))         # 同じ日 (JST) の 11:00 (📤 など)
    db3 = drills_of(b3)
    check("同じ日に後から受け取れるようになった生徒は今日のドリルに足す (drills_joined・〆 は同じ)", res["delivered"] == 1
          and res["drills_joined"] == 1 and res["drills_created"] == 0 and len(db3) == 1 and db3[0]["id"] == db1[-1]["id"],
          (res.get("delivered"), res.get("drills_joined"), db3))
    # 〆 の日 (6:00 の実行のあと) に出す生徒も、届くドリルの 〆 はいつも受け取った日 + 2 日 (前の日のドリルに足して 〆 まで 1 日にしない・
    #   それが毎回続いて 1 日遅れのまま戻らない、を防ぐ)。fa はその日のうちに出す・fb は 〆 の日の夕方に出す
    reset_chw()
    fa, fb = make("高校2年", [LV2]), make("高校2年", [LV2])
    only_active([fa, fb])
    for d_ in range(10):
        run(now=at(d_))
        today_ = (at(d_) + datetime.timedelta(hours=9)).date()
        complete_all(fa)
        for x in drills_of(fb):
            if x["status"] != "completed" and due_of(x) is not None and due_of(x) <= today_:
                ex(mod, "UPDATE grammar_drill_assignments SET status = 'completed' WHERE drill_id = ? AND student_id = ?", (x["id"], fb))
    dfa, dfb = drills_of(fa), drills_of(fb)
    bad = [(x["title"], x["assigned_at"]) for x in dfa + dfb if due_of(x) != recv_jst(x) + datetime.timedelta(days=2)]
    check("〆 の日の夕方に出す生徒も、届くドリルの 〆 はいつも受け取った日 + 2 日 (10 日間)", len(dfa) == 5 and len(dfb) >= 3 and not bad,
          (bad[:4], len(dfa), len(dfb)))
    # 英語のクラスを 2 つ取る生徒
    reset_chw()
    m2 = make("高校2年", [EIKEN2, LV2])
    only_active([m2])
    res = run()
    dm = drills_of(m2)
    check("2 クラスでも 1 回に 1 本 (時間割の順で 火曜2限)", res["delivered"] == 1 and len(dm) == 1 and dm[0]["created_by"].endswith(LV2), dm)
    complete_all()
    run(now=at(2))
    dm = drills_of(m2)
    check("次は届いていないクラス (英検2級対策)", len(dm) == 2 and dm[1]["created_by"].endswith(EIKEN2), [x["created_by"] for x in dm])
    complete_all()
    run(now=at(4))
    dm = drills_of(m2)
    check("その次は最後に届いたのが古いクラス (英文法 Lv.2)", len(dm) == 3 and dm[2]["created_by"].endswith(LV2), [x["created_by"] for x in dm])
    check("1 人に届くのは 2 日に 1 本まで (3 本の配信日がそれぞれ 2 日ずつ離れている)",
          [x["assigned_at"][:10] for x in dm] == ["2026-10-20", "2026-10-22", "2026-10-24"], [x["assigned_at"] for x in dm])
    # ドリルを作る日が 1 日ずれた 2 クラス (ON の手順どおり ONLY で 英文法 Lv.2 を 1 日先に始める)。どちらのクラスにも別の生徒がいて、
    #   全員が毎日出す。2 クラスの生徒にも両方のクラスが交互に届く (wait_next のクラスを飛ばして後に届いたクラスばかり配らない)
    reset_chw()
    ms, mu, mt = make("高校2年", [EIKEN2, LV2]), make("高校2年", [LV2]), make("高校2年", [EIKEN2])
    only_active([ms, mu, mt])
    st_ms = {}
    for d_ in range(10):
        with Env(CLASS_HW_AUTO_ONLY_CLASSES=(LV2 if d_ == 0 else None)):
            res = run(now=at(d_))
        st_ms[d_] = (status_of(res, ms, EIKEN2), status_of(res, ms, LV2))
        complete_all()
    dms = drills_of(ms)
    cls_ms = [EIKEN2 if x["created_by"].endswith(EIKEN2) else LV2 for x in dms]
    check("ずれた 2 クラス: 2 クラスの生徒にも両方のクラスが交互に届く (10 日で 英文法 → 英検 → 英文法 → 英検)",
          cls_ms == [LV2, EIKEN2, LV2, EIKEN2], [(x["created_by"], x["assigned_at"]) for x in dms])
    check("ずれた 2 クラス: 英検のドリルが前の日のものの朝は待つ (CEO の 🔍 も wait_next・別のクラスで配ったことにしない)",
          st_ms[2] == ("wait_next", "wait_next"), st_ms)
    gaps = [(recv_jst(b_) - recv_jst(a_)).days for a_, b_ in zip(dms, dms[1:])]
    bad = [x["title"] for x in dms if due_of(x) != recv_jst(x) + datetime.timedelta(days=2)]
    check("ずれた 2 クラス: 間は 2〜3 日 (2 日に 1 本まで・待つのは翌朝まで)・〆 はいつも受け取った日 + 2 日",
          gaps and all(2 <= g_ <= 3 for g_ in gaps) and not bad, (gaps, bad))
    dmu, dmt = drills_of(mu), drills_of(mt)
    check("ずれた 2 クラス: 1 クラスだけの生徒は 2 日に 1 本のまま (英文法 5 本・英検 5 本)", len(dmu) == 5 and len(dmt) == 5,
          (len(dmu), len(dmt)))
    # 届いたことが無い生徒は、時間割の順で先のクラスが wait_next でも待たずに次のクラス (届いた日時が同じ = 同点)
    run(now=at(10))         # 英文法 Lv.2 の新しいドリル (mu)
    complete_all()
    mn = make("高校2年", [EIKEN2, LV2])
    only_active([ms, mu, mt, mn])
    res = run(now=at(11))   # 英文法 Lv.2 は前の日のドリル (wait_next)・英検2級対策は今日の新しいドリル (mt)
    dmn = drills_of(mn)
    check("届いたことが無い 2 クラスの生徒は、先のクラスが wait_next でも次のクラスの今日のドリルを受け取る",
          group_of(res, LV2, "kosei").get("reason") == "wait_next" and len(dmn) == 1 and dmn[0]["created_by"].endswith(EIKEN2),
          (group_of(res, LV2, "kosei").get("reason"), [x["created_by"] for x in dmn]))

    # ------------------------------------------------------------------
    print("\n[7] 単元の選び方 (弱点 → 順番 → 一番前)")
    reset_chw()
    w1, w2, w3 = make("高校2年", [LV2]), make("高校2年", [LV2]), make("中学3年", [LV2])
    only_active([w1, w2, w3])
    weak(w1, "english", "関係代名詞の非制限用法", acc=0.2, att=6)   # → 関係詞
    weak(w2, "english", "関係詞", acc=0.4, att=4)
    weak(w2, "english", "仮定法", acc=0.3, att=10)
    weak(w1, "english", "比較", acc=0.1, att=2)                     # 合計 2 回 = 数えない
    weak(w2, "english", "時制", acc=0.85, att=10)                   # 0.8 以上 = 数えない
    weak(w3, "chugaku", "中学英語 受動態", acc=0.1, att=10)         # 前置きつきの写し = 数えない
    weak(w3, "chugaku", "現在完了（継続）", acc=0.2, att=10)         # → 現在完了
    weak(w3, "english", "仮定法", acc=0.0, att=10)                   # 中学生の english の弱点は高校の区分に混ぜない
    r = run(dry=True)
    gk, gc = group_of(r, LV2, "kosei"), group_of(r, LV2, "chugaku")
    # 関係詞 = (0.2*6 + 0.4*4) / 10 = 0.28 < 仮定法 0.30 (中学生の 0.0 は数えない)
    check("高校の区分: 合わせた正答率の一番低い単元 (関係詞・理由 weakness)", gk.get("unit") == "関係詞" and gk.get("unit_reason") == "weakness", gk)
    check("中学の区分: 写しは数えず「現在完了（継続）」→ 現在完了", gc.get("unit") == "現在完了" and gc.get("unit_reason") == "weakness", gc)
    run()
    complete_all()
    r = run(dry=True, now=at(2))
    gk = group_of(r, LV2, "kosei")
    check("直近 14 日に出した単元は飛ばす → 次に弱い 仮定法", gk.get("unit") == "仮定法" and gk.get("unit_reason") == "weakness", gk)
    run(now=at(2))
    complete_all()
    r = run(dry=True, now=at(4))
    gk = group_of(r, LV2, "kosei")
    units = list(mod.GRAMMAR_UNITS)
    check("弱点が尽きたら単元の順番 (前回の 仮定法 の次 = 比較)", gk.get("unit") == units[units.index("仮定法") + 1]
          and gk.get("unit_reason") == "rotation", gk)
    with Env(CLASS_HW_UNIT_COOLDOWN_DAYS="0"):
        gk0 = group_of(run(dry=True, now=at(4)), LV2, "kosei")
    check("CLASS_HW_UNIT_COOLDOWN_DAYS=0 なら飛ばさない (一番弱い 関係詞 に戻る)", gk0.get("unit") == "関係詞", gk0)
    # 全部が飛ばす期間 → 一番前に出した単元 (英検のクラス 4 単元)
    reset_chw()
    e4 = make("高校1年", [EIKEN2])
    only_active([e4])
    seen_units = []
    for i in range(5):
        run(now=at(2 * i))
        complete_all()
        seen_units.append(drills_of(e4)[-1]["unit"])
    r = run(dry=True, now=at(10))
    check("英検は 単語 → 長文空所補充 → 句動詞・熟語 → 長文 内容一致 の順に回る",
          seen_units[:4] == ["2級 単語", "2級 長文空所補充", "2級 句動詞・熟語", "2級 長文 内容一致"], seen_units)
    check("4 単元とも 14 日以内に出した → 一番前に出した単元 (理由 oldest)", seen_units[4] == "2級 単語"
          and group_of(r, EIKEN2, "kosei").get("unit") == "2級 長文空所補充" and group_of(r, EIKEN2, "kosei").get("unit_reason") == "oldest",
          (seen_units, group_of(r, EIKEN2, "kosei")))
    dq = [set(json.loads(x["question_ids"])) for x in drills_of(e4) if x["unit"] == "2級 単語"]
    check("同じクラスに前に出した問題は避ける (2 回目の 2級 単語 は 1 回目と重ならない)", len(dq) == 2 and not (dq[0] & dq[1]), dq)

    # ------------------------------------------------------------------
    print("\n[8] お知らせ (LINE は送らない・既定はメールも送らない)")
    check("ここまでの本番の実行で LINE は 0 回", rec.lines == [], rec.lines[:3])
    check("ここまでの本番の実行でメールは 0 通 (既定 manual = 自動配信は送らない)", rec.mails == [], rec.mails[:1])
    reset_chw()
    n1 = make("高校2年", [LV2], email="chw-notify@example.org")
    only_active([n1])
    with Env(HOMEWORK_NOTIFY_EMAIL="all"):
        res = run()
    mails = [m for m in rec.mails if m[0] == "chw-notify@example.org"]
    check("HOMEWORK_NOTIFY_EMAIL=all ならメール 1 通・リンクは /class.html?tab=homework (# を使わない)",
          res["delivered"] == 1 and len(mails) == 1 and "/class.html?tab=homework" in mails[0][2] and "#homework" not in mails[0][2], mails)
    check("それでも LINE は 0 回", rec.lines == [], rec.lines[:3])
    check("応答の notify は既定 (line false・email false)", run(dry=True).get("notify") == {"line": False, "email": False})

    # ------------------------------------------------------------------
    print("\n[9] dry-run と本番・管理 API")
    reset_chw()
    p1, p2, p3 = make("高校2年", [LV2]), make("中学2年", ["火曜1限 中学基礎"]), make("高校3年", [EIKEN2])
    only_active([p1, p2, p3])
    before = counts(mod)
    dr = run(dry=True, seed=11)
    check("dry-run: 行数が変わらない・15 クラスすべて", counts(mod) == before and [x["label"] for x in dr["classes"]]
          == [c_["label"] for c_ in mod._TIMETABLE_CLASSES], counts(mod))
    real = run(seed=11)

    def plan_view(res_):
        out_ = {}
        for row in res_["classes"]:
            for g in row["groups"]:
                if g.get("deliver_n"):
                    out_[(row["label"], g["group"])] = (g["unit"], g["title"], g["qids_n"])
        return out_, sorted((e["id"], e["label"], e["group"]) for e in res_["assigned_students"])

    check("同じ seed なら dry-run と本番で同じ単元・題名・問題数・生徒", plan_view(dr) == plan_view(real), (plan_view(dr), plan_view(real)))
    dqs = {x["created_by"]: json.loads(x["question_ids"]) for s_ in (p1, p2, p3) for x in drills_of(s_)}
    conn = mod.db(); c = conn.cursor()
    re_plan = {}
    for row in dr["classes"]:
        for g in row["groups"]:
            if g.get("deliver_n"):
                gp = mod._class_hw_plan_group(c, row["label"], g["group"], members=[], weak_rows=[], hist=[], settings=mod._class_hw_settings(),
                                              now_txt="2026-10-20 21:00:05", interval_cutoff="2026-10-19 03:00:05",
                                              rng=random.Random(f"11:{row['label']}:{g['group']}"))
                re_plan[f"{PREFIX}{g['group']}:{row['label']}"] = gp["qids"]
    conn.close()
    check("本番の問題 = 同じ seed の計画の問題 (dry-run と同じ関数)", dqs == re_plan, (sorted(dqs), sorted(re_plan)))
    check("名前は include_names のときだけ (クラスの表・配る生徒)", all("name" not in e for row in dr["classes"] for e in row["students"])
          and all("name" not in e for e in dr["assigned_students"]) and dr["assigned_students"])
    r_ = client.post("/api/admin/class-homework-routine/run", json={})
    check("管理 API: 認証なしは 401", r_.status_code == 401, r_.status_code)
    before = counts(mod)
    r_ = client.post("/api/admin/class-homework-routine/run", json={}, headers=adm)
    j = r_.json() if r_.status_code == 200 else {}
    check("管理 API: 既定は dry-run (何も書かない)・plan_version 1・enabled_env false・許可リストは英語の科目",
          r_.status_code == 200 and j.get("dry_run") is True and j.get("plan_version") == 1 and j.get("enabled_env") is False
          and set(j.get("allowlist", {})) == {"english", "chugaku", "eiken", "english_long"} and counts(mod) == before, (r_.status_code, str(j)[:300]))
    names = {x["name"] for x in q(mod, "SELECT name FROM students")}
    check("管理 API: include_names が無ければ応答に生徒の名前が無い", not any(n_ in r_.text for n_ in names if n_), "")
    r_ = client.post("/api/admin/class-homework-routine/run", json={"include_names": True}, headers={"X-Cron-Secret": "test-cron-secret"})
    check("管理 API: X-Cron-Secret でも読める・include_names で名前が出る", r_.status_code == 200 and any(n_ in r_.text for n_ in names if n_), r_.status_code)
    for bad_label in ("架空のクラス", "水曜2限 GMARCH", "日曜 高校国語"):
        r_ = client.post("/api/admin/class-homework-routine/run", json={"class_label": bad_label}, headers=adm)
        check(f"管理 API: class_label={bad_label!r} → 400", r_.status_code == 400, r_.status_code)
    reset_chw()
    with Env(CLASS_HW_AUTO_ONLY_CLASSES=f"{EIKEN2}、架空のクラス"):
        r = run(dry=True)
        check("CLASS_HW_AUTO_ONLY_CLASSES: そのクラスだけ (ほかのクラスの生徒は not_selected)・知らない名前は only_classes_unknown",
              r["selected_classes"] == [EIKEN2] and status_of(r, p1) == "not_selected" and status_of(r, p3) == "deliver"
              and r["settings"]["only_classes_unknown"] == ["架空のクラス"] and not r.get("error"),
              (r["selected_classes"], status_of(r, p1), r["settings"], r.get("error")))
        r = run(dry=True, all_classes=True)
        check("all_classes (CEO の 🔍) は CLASS_HW_AUTO_ONLY_CLASSES を無視して全クラス", status_of(r, p1) == "deliver" and len(r["selected_classes"]) == 12)
    # 打ち間違いだけの指定 (段階投入の 1 クラスのつもり) を全クラスに広げない (fail closed・props.error = 監視に出る)
    with Env(CLASS_HW_AUTO_ONLY_CLASSES="火曜2限 英文法 Lv.3、架空のクラス"):
        r = run(dry=True)
        check("CLASS_HW_AUTO_ONLY_CLASSES が打ち間違いだけ → 0 クラス (全クラスに広げない)・error に設定の名前",
              r["selected_classes"] == [] and status_of(r, p1) == "not_selected" and status_of(r, p3) == "not_selected"
              and r["eligible"] == 0 and "CLASS_HW_AUTO_ONLY_CLASSES" in (r.get("error") or ""), (r["selected_classes"], r.get("error")))
        before = counts(mod)
        r = run()
        after = counts(mod)
        check("打ち間違いだけの指定で毎朝の実行 (本番) を回しても 1 本も書かない・実行記録の要約に error が残る",
              r["delivered"] == 0 and after["grammar_drills"] == before["grammar_drills"]
              and after["grammar_drill_assignments"] == before["grammar_drill_assignments"]
              and "CLASS_HW_AUTO_ONLY_CLASSES" in str(mod._compact_run_props(r).get("error") or ""), (r["delivered"], before, after))
        r = run(dry=True, all_classes=True)
        check("🔍 (all_classes) は打ち間違いの指定があっても全クラスを計算し error にしない", len(r["selected_classes"]) == 12 and not r.get("error"))
    with Env(CLASS_HW_AUTO_ONLY_CLASSES="水曜2限 GMARCH"):
        r = run(dry=True)
        check("保留のクラスだけの指定も 0 クラス・error", r["selected_classes"] == [] and bool(r.get("error")), (r["selected_classes"], r.get("error")))
    with Env(CLASS_HW_AUTO_ONLY_CLASSES="火曜２限　英文法　Lv．2，金曜2限 英検2級対策 "):   # 全角の数字・空白・記号と区切り
        r = run(dry=True)
        check("全角の数字・空白・記号の違いは同じクラス名 (only_classes は時間割の正しい名前)",
              r["selected_classes"] == [LV2, EIKEN2] and r["settings"]["only_classes"] == [LV2, EIKEN2]
              and r["settings"]["only_classes_unknown"] == [] and not r.get("error") and status_of(r, p1) == "deliver", (r["selected_classes"], r["settings"]))
    with Env(CLASS_HW_AUTO_ONLY_CLASSES="火曜2限 英文法Lv.2"):   # 空白の抜け
        r = run(dry=True)
        check("空白の抜けも同じクラス名", r["selected_classes"] == [LV2] and r["settings"]["only_classes"] == [LV2], (r["selected_classes"], r["settings"]))
    check("時間割の 15 クラスは照合の形 (_class_hw_label_key) でも重ならない",
          len({mod._class_hw_label_key(x) for x in mod._TIMETABLE_LABELS}) == len(mod._TIMETABLE_LABELS) == 15)
    mod._RATE_LIMIT_STORE.clear()
    r_ = client.post("/api/admin/class-homework-routine/run", json={"dry_run": False, "class_label": "火曜1限 中学基礎"}, headers=adm)
    j = r_.json() if r_.status_code == 200 else {}
    check("📤 (1 クラスだけ本番): そのクラスの生徒だけに配る", r_.status_code == 200 and j.get("delivered") == 1
          and len(drills_of(p2)) == 1 and not drills_of(p1) and not drills_of(p3), (r_.status_code, str(j)[:200]))
    r_ = client.post("/api/admin/class-homework-routine/run", json={"dry_run": False, "class_label": "火曜1限 中学基礎"}, headers=adm)
    check("📤 を押し直しても増えない (未提出 = 積まない)", r_.status_code == 200 and r_.json().get("delivered") == 0 and len(drills_of(p2)) == 1)

    # ------------------------------------------------------------------
    print("\n[10] AIなし の生徒が塾生アプリで解ける (許可集合は変えていない)")
    tok = {"Authorization": "Bearer " + student_token(mod, p2)}
    did = drills_of(p2)[0]["id"]
    mod._RATE_LIMIT_STORE.clear()
    r_ = client.get("/api/student/homework", headers=tok)
    check("GET /api/student/homework は 200 (通塾生 = 403 にならない)", r_.status_code == 200, r_.status_code)
    r_ = client.get("/api/student/grammar-drills", headers=tok)
    items = r_.json().get("items", []) if r_.status_code == 200 else []
    check("GET /api/student/grammar-drills に出る (未提出)", r_.status_code == 200 and any(it.get("drill_id") == did and it.get("status") != "completed"
                                                                                       for it in items), r_.text[:300])
    r_ = client.get(f"/api/student/grammar-drill/{did}", headers=tok)
    qs = r_.json().get("questions", []) if r_.status_code == 200 else []
    check("GET /api/student/grammar-drill/{id} は 200・10 問", r_.status_code == 200 and len(qs) == 10, r_.status_code)
    r_ = client.post(f"/api/student/grammar-drill/{did}/submit", json={"answers": {str(x["question_id"]): 0 for x in qs}}, headers=tok)
    check("提出は 200", r_.status_code == 200, r_.text[:200])
    check("AIなし枠の EXACT 許可集合は不変", set(mod._AI_DISABLED_ALLOWED_EXACT) == {
        "/api/student/homework", "/api/student/grammar-drills", "/api/messages/me", "/api/student/messages/send"})
    check("AIなし枠の PREFIX 許可集合は不変", tuple(mod._AI_DISABLED_ALLOWED_PREFIXES) == (
        "/api/student/class/", "/api/student/homework/", "/api/student/grammar-drill/", "/api/messages/me/", "/api/auth/", "/api/admin/"))

    # ------------------------------------------------------------------
    print("\n[11] CEO の配信済み一覧")
    r_ = client.get("/api/admin/grammar-drill/list", headers=adm)
    own = r_.json().get("items", []) if r_.status_code == 200 else []
    check("既定 (塾長が配信) にはクラス自動宿題が出ない", r_.status_code == 200 and not any(str(it.get("created_by") or "").startswith(PREFIX) for it in own))
    r_ = client.get("/api/admin/grammar-drill/list", params={"kind": "class_hw"}, headers=adm)
    ch = r_.json().get("items", []) if r_.status_code == 200 else []
    mine_ = [it for it in ch if it.get("id") == did]
    check("kind=class_hw: クラス名と区分つき", mine_ and mine_[0].get("class_label") == "火曜1限 中学基礎" and mine_[0].get("group") == "chugaku"
          and mine_[0].get("origin") == "class_hw", mine_)

    # ------------------------------------------------------------------
    print("\n[12] 1 人 1 経路 (3日ドリルと合わせて・AI の振り分けの全組み合わせ)")
    reset_chw()
    ex(mod, "DELETE FROM grammar_drill_assignments")
    now_real = datetime.datetime.now(datetime.timezone.utc)
    trials = {"なし": None, "過去": mod._utc_naive_iso(now_real - datetime.timedelta(days=2)),
              "未来": mod._utc_naive_iso(now_real + datetime.timedelta(days=3)), "壊れた値": "not-a-date"}
    fixture = {}
    for ai in (0, 1):
        for tk, tv in trials.items():
            sid = make("高校2年", [LV2], ai_disabled=ai, trial=tv)
            weak(sid, "english", "時制", acc=0.3, att=10)
            fixture[sid] = (ai, tk)
    only_active(list(fixture))
    rt = mod._run_weakness_drill_routine(dry_run=True, seed=1)
    ch_ = mod._run_class_homework_routine(dry_run=True, seed=1)
    routine_ids = {e["id"] for e in rt["delivered_students"]}
    chw_ids = {e["id"] for e in ch_["assigned_students"]}
    lost = [fixture[s] for s in fixture if s not in routine_ids and s not in chw_ids]
    both = [fixture[s] for s in fixture if s in routine_ids and s in chw_ids]
    check("全員がどちらかの自動配信に入る (どちらにも入らない生徒がいない)", not lost, lost)
    check("両方に入る生徒がいない", not both, both)
    want_path = {s: ("ai" if (ai == 0 or tk == "未来") else "ai_nashi") for s, (ai, tk) in fixture.items()}
    got_path = {s: ("ai" if s in routine_ids else "ai_nashi") for s in fixture}
    check("AIあり と AI 体験中 → 3日ドリル・AIなし (体験なし/切れた/壊れた値) → クラス自動宿題", got_path == want_path,
          {fixture[s]: (want_path[s], got_path[s]) for s in fixture if want_path[s] != got_path[s]})
    check("振り分けは _auto_delivery_ai_path と同じ", all(mod._auto_delivery_ai_path(ai, trials[tk]) == want_path[s]
                                                       for s, (ai, tk) in fixture.items()))

    # ------------------------------------------------------------------
    print("\n[13] 競合・監視・記録")
    reset_chw()
    z1, z2 = make("高校2年", [LV2]), make("高校2年", [LV2])
    only_active([z1, z2])
    orig_plan = mod._class_hw_plan

    def racing_plan(c, **kw):
        out = orig_plan(c, **kw)
        # 計画のあとで別の実行 (別のレプリカ・📤) が z1 に配った
        conn2 = mod.db(); c2 = conn2.cursor()
        c2.execute("INSERT INTO grammar_drills (subject, title, unit, level, question_ids, created_by, created_at) VALUES ('english', '別の実行', '時制', 'standard', '[]', ?, '2026-10-19 00:00:00') RETURNING id",
                   (f"{PREFIX}kosei:水曜3限 国公立コース 英文法",))
        did_ = c2.fetchone()["id"]
        c2.execute("INSERT INTO grammar_drill_assignments (drill_id, student_id, status, assigned_at) VALUES (?, ?, 'open', '2026-10-19 00:00:00')", (did_, z1))
        conn2.commit(); conn2.close()
        return out

    mod._class_hw_plan = racing_plan
    try:
        res = run()
    finally:
        mod._class_hw_plan = orig_plan
    check("計画と書き込みの間に別の実行が配った生徒は race (2 本目を作らない)・もう 1 人には配る",
          res["skipped_race"] == 1 and res["delivered"] == 1 and len(drills_of(z1)) == 1 and len(drills_of(z2)) == 1, res)
    ev = q(mod, "SELECT props, session_id FROM events WHERE name = 'class_hw_auto_delivered' ORDER BY id DESC LIMIT 1")
    pj = json.loads(ev[0]["props"]) if ev else {}
    check("配信の記録 (events class_hw_auto_delivered) は生徒 id だけ (名前なし)", ev and pj.get("student_ids") == [z2]
          and "架空" not in ev[0]["props"] and pj.get("class_label") == LV2, ev)
    props = mod._compact_run_props(res)
    js_ = json.dumps(props, ensure_ascii=False)
    check("実行記録の要約は 4000 字未満の JSON・名前と連絡先を含まない", len(js_) < 4000 and "架空" not in js_ and "@example.org" not in js_
          and json.loads(js_) == props and props.get("delivered") == 1, js_[:300])
    reset_chw()
    orig_deliver = mod._class_hw_deliver_group
    mod._class_hw_deliver_group = lambda *a, **k: {"assigned": [], "race": [], "error": "exception", "mode": "new", "unit": "", "subject": "", "nq": 0}
    try:
        res = run()
    finally:
        mod._class_hw_deliver_group = orig_deliver
    check("全部の書き込みに失敗したら error (監視 _failed_schedulers が拾う)", res["delivered"] == 0 and res["create_failed"] == 2
          and "1 本も配れません" in str(res.get("error")), res.get("error"))
    check("error は要約にも残る", "error" in mod._compact_run_props(res))

    # ------------------------------------------------------------------
    print("\n[15] 2026-10-16 塾長決定: 14 日より前の未提出は「積まない」に数えない (CLASS_HW_OPEN_STALE_DAYS・古いドリルは消さない)")
    check("既定は 14 日", mod._class_hw_settings()["open_stale_days"] == 14, mod._class_hw_settings().get("open_stale_days"))
    for v, want in (("0", 0), ("-1", 0), ("1", 2), ("7", 7), ("400", 365), ("x", 14)):
        with Env(CLASS_HW_OPEN_STALE_DAYS=v):
            check(f"CLASS_HW_OPEN_STALE_DAYS={v!r} → {want} 日 (0 = 全部数える・2 日に 1 本の間隔〜365 に丸める)",
                  mod._class_hw_settings()["open_stale_days"] == want, mod._class_hw_settings().get("open_stale_days"))
    with Env(CLASS_HW_OPEN_STALE_DAYS="1", CLASS_HW_INTERVAL_DAYS="5"):
        check("間隔を 5 日にしたら下限も 5 日", mod._class_hw_settings()["open_stale_days"] == 5, mod._class_hw_settings())

    def give_old(sid, when, status="open", null_at=False):
        txt = when.astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        conn = mod.db(); c = conn.cursor()
        c.execute("INSERT INTO grammar_drills (subject, title, unit, level, question_ids, created_by, created_at) "
                  "VALUES ('english', '架空の古い宿題', '時制', 'standard', '[]', ?, ?) RETURNING id", (f"{PREFIX}kosei:{LV2}", txt))
        d_ = c.fetchone()["id"]
        c.execute("INSERT INTO grammar_drill_assignments (drill_id, student_id, status, assigned_at) VALUES (?, ?, ?, ?)",
                  (d_, sid, status, None if null_at else txt))
        conn.commit(); conn.close()
        return d_

    reset_chw()
    o1 = make("高校2年", [LV2])
    only_active([o1])
    old_did = give_old(o1, at(-15))           # T0 = JST 10/21 6:00 → 10/6 の未提出 (15 日前)
    res = run(dry=True)
    check("15 日前の未提出だけなら数えずに配る (stale_open_ignored 1・settings.open_stale_days 14)",
          status_of(res, o1) == "deliver" and res["skipped_open"] == 0 and res.get("stale_open_ignored") == 1
          and res["settings"].get("open_stale_days") == 14, (status_of(res, o1), res.get("stale_open_ignored"), res["skipped_open"]))
    with Env(CLASS_HW_OPEN_STALE_DAYS="0"):
        res = run(dry=True)
        check("CLASS_HW_OPEN_STALE_DAYS=0 なら従来どおり数える (open)", status_of(res, o1) == "open" and res["skipped_open"] == 1
              and res.get("stale_open_ignored") == 0, (status_of(res, o1), res.get("stale_open_ignored")))
    res = run()
    do1 = drills_of(o1)
    check("本番: 錠の中の読み直しでも古い未提出で止めない (race にしない)・新しいドリルを 1 本", res["delivered"] == 1 and res["skipped_race"] == 0
          and len(do1) == 2, (res.get("delivered"), res.get("skipped_race"), [(x["id"], x["status"]) for x in do1]))
    check("古いドリルは消さない (未提出のまま残る)", any(x["id"] == old_did and x["status"] == "open" for x in do1), do1)
    res = run(now=at(2))
    check("新しい未提出があれば 2 日後も積まない (open)", status_of(res, o1) == "open" and res["delivered"] == 0, status_of(res, o1))
    reset_chw()
    give_old(o1, at(-14))                     # ちょうど 14 日前 (10/7) の未提出
    res = run(dry=True)
    check("ちょうど 14 日前の未提出はまだ数える (open)", status_of(res, o1) == "open" and res.get("stale_open_ignored") == 0, status_of(res, o1))
    reset_chw()
    give_old(o1, at(-30), null_at=True)
    res = run(dry=True)
    check("assigned_at が空の未提出は新しいものとして数える (open)", status_of(res, o1) == "open", status_of(res, o1))
    reset_chw()
    give_old(o1, at(-30))
    give_old(o1, at(-1))
    res = run(dry=True)
    check("古い未提出と新しい未提出の両方があれば積まない", status_of(res, o1) == "open" and res.get("stale_open_ignored") == 0, status_of(res, o1))
    # 2 日に 1 本の周期のずれ (3日ドリルの「72 時間ちょうど」で 1 日ずれた件と同じことが起きないか・2026-10-16 に確かめた):
    #   2 日前の実行が数秒遅れて書いた配信も、2 日後の実行 (少し早く起きても) では「2 日たった」= 6 時間の遊び
    reset_chw()
    give_old(o1, at(-2, 30 / 3600), status="completed")
    res = run(dry=True, now=at(0, -30 / 3600))
    check("2 日前の 6:00:35 に受け取って提出した生徒は、2 日後の 5:59:35 の実行でも届く (周期が 3 日にずれない)",
          status_of(res, o1) == "deliver", status_of(res, o1))

    # [14] 画面: 名前・学年に HTML を入れた生徒で 🔍 の応答を作り、CEO のカードを JS で描く
    reset_chw()
    v1 = make("高校2年", [LV2], name="架空 <img src=x onerror=alert(1)> 生徒")
    v2 = make("<b>未設定</b>", [LV2])
    v3 = make("高校3年", ["水曜2限 GMARCH"])
    only_active([v1, v2, v3])
    check_screens(mod, client, adm, {"deliver": v1})

    print()
    if FAILURES:
        print(f"❌ FAIL ({len(FAILURES)} 件)")
        for f in FAILURES:
            print("   -", f)
        sys.exit(1)
    print("✅ PASS (クラス自動宿題: AIなし枠だけ・英語だけ・2 日に 1 回・レビュー済みだけ・中高の取り違えなし・1 人 1 経路)")


if __name__ == "__main__":
    main()
