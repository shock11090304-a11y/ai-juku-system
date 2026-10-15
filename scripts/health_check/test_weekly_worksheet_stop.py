#!/usr/bin/env python3
"""⛔ 週次弱点プリント (日曜 5:00) を止めた回帰テスト (2026-10-15 塾長決定)。

背景: 週次弱点プリントは入試道場の exam_questions (AI 生成の行を含む) から選ぶため、
  「自動配信はレビュー済みの科目別ドリルだけ」(2026-10-15 塾長決定) に反する。自動の弱点配信は
  科目別ドリルの 3日ドリルに一本化し、週次プリントは env WEEKLY_WORKSHEET_ENABLED (既定 = 停止) で止める。
  保存済みのプリントと 📚 履歴は消さない。

固定する性質 (一時 SQLite・外部通信なし):
  1. _weekly_worksheet_env_enabled() は未設定で False、1/true/yes/on だけ True
  2. 停止中は _SCHEDULER_MAX_AGE_DAYS に weekly_worksheet_run が無い (8 日後の「停止」誤報を出さない)。
     env=1 で import し直すと入る (別プロセスで確認)
  3. 起動時の登録は env が有効なときだけ (ソース検査)。スケジューラのループも起きるたびに env を見て、停止中は生成しない
  4. POST /api/admin/worksheet/run-weekly-now は停止中 409 で、worksheet_archives は 1 行も増えない (認証が先: 未認証は 401)
  5. GET /api/student/worksheet/this-week は停止中 discontinued: true。JST の今日から 7 日前以降の行だけ返し、
     それより古い行は「今週」として出さない。/history は全部出す (行は消さない)
  6. CEO「生徒の見え方」(admin sapuri preview) は weekly_enabled を返し、ceo.html は false のとき「停止中」と出す
  7. mypage.html は discontinued のとき「終了しました」と 📚 履歴 を案内する / prod_healthcheck は監視から外す

実行:
    python3 scripts/health_check/test_weekly_worksheet_stop.py
    # exit 0 = PASS / 1 = FAIL
"""
import asyncio
import base64
import datetime
import hashlib
import hmac
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import types

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if detail and not cond else ""))
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
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="ws_stop_"), "test.db")
    os.environ.update(_base_env(tmpdb))
    os.environ.pop("WEEKLY_WORKSHEET_ENABLED", None)   # 既定 (未設定) で import する
    spec = importlib.util.spec_from_file_location("aijuku_main_ws_stop", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def student_token(mod, sid, hours=1):
    exp = int(time.time()) + hours * 3600
    payload = f"session.{sid}.{exp}"
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}.{sig}".encode()).decode().rstrip("=")


class _Env:
    """WEEKLY_WORKSHEET_ENABLED を一時的に差し替える (with を抜けたら元に戻す)。None は未設定。"""

    def __init__(self, value):
        self.value = value

    def __enter__(self):
        self.old = os.environ.get("WEEKLY_WORKSHEET_ENABLED")
        if self.value is None:
            os.environ.pop("WEEKLY_WORKSHEET_ENABLED", None)
        else:
            os.environ["WEEKLY_WORKSHEET_ENABLED"] = self.value
        return self

    def __exit__(self, *a):
        if self.old is None:
            os.environ.pop("WEEKLY_WORKSHEET_ENABLED", None)
        else:
            os.environ["WEEKLY_WORKSHEET_ENABLED"] = self.old


def _scheduler_dict_in_subprocess(value):
    """env を value にして main.py を別プロセスで import し、_SCHEDULER_MAX_AGE_DAYS のキーを返す (import 時に評価される dict)。"""
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="ws_stop_sub_"), "test.db")
    env = dict(os.environ)
    env.update(_base_env(tmpdb))
    if value is None:
        env.pop("WEEKLY_WORKSHEET_ENABLED", None)
    else:
        env["WEEKLY_WORKSHEET_ENABLED"] = value
    code = (
        "import importlib.util, json, sys\n"
        f"spec = importlib.util.spec_from_file_location('aijuku_main_ws_sub', {MAIN_PY!r})\n"
        "mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)\n"
        "print('KEYS=' + json.dumps(sorted(mod._SCHEDULER_MAX_AGE_DAYS)))\n"
    )
    r = subprocess.run([sys.executable, "-c", code], env=env, cwd=os.path.join(REPO, "server"),
                       capture_output=True, text=True, timeout=300)
    for line in (r.stdout or "").splitlines():
        if line.startswith("KEYS="):
            return json.loads(line[len("KEYS="):])
    raise RuntimeError(f"subprocess failed rc={r.returncode}: {(r.stderr or '')[-800:]}")


def main():
    mod = load_main()
    src = open(MAIN_PY, encoding="utf-8").read()

    print("[1] env の判定 (既定 = 停止)")
    with _Env(None):
        check("未設定なら False", mod._weekly_worksheet_env_enabled() is False)
    for v in ("1", "true", "TRUE", "yes", "on", " On "):
        with _Env(v):
            check(f"{v!r} なら True", mod._weekly_worksheet_env_enabled() is True)
    for v in ("", "0", "false", "off", "no", "2", "enabled"):
        with _Env(v):
            check(f"{v!r} なら False", mod._weekly_worksheet_env_enabled() is False)

    print("[2] 監視の対象 (_SCHEDULER_MAX_AGE_DAYS は import 時に評価)")
    check("停止中 (既定) は weekly_worksheet_run が監視の対象に無い",
          "weekly_worksheet_run" not in mod._SCHEDULER_MAX_AGE_DAYS, list(mod._SCHEDULER_MAX_AGE_DAYS))
    check("ほかの監視の対象は残っている (weekly_reports_run / weakness_aggregation_run)",
          "weekly_reports_run" in mod._SCHEDULER_MAX_AGE_DAYS and "weakness_aggregation_run" in mod._SCHEDULER_MAX_AGE_DAYS)
    try:
        keys_on = _scheduler_dict_in_subprocess("1")
        check("WEEKLY_WORKSHEET_ENABLED=1 で import すると weekly_worksheet_run が入る (8 日)",
              "weekly_worksheet_run" in keys_on, keys_on)
        keys_off = _scheduler_dict_in_subprocess(None)
        check("未設定で import すると入らない (別プロセスでも同じ)", "weekly_worksheet_run" not in keys_off, keys_off)
    except Exception as e:
        check("別プロセスでの import", False, e)
    hc = open(os.path.join(REPO, "scripts", "health_check", "prod_healthcheck.py"), encoding="utf-8").read()
    watched = hc[hc.index("def check_scheduler_live("):hc.index("def run_db_checks(")]
    check("prod_healthcheck の scheduler_live は weekly_worksheet_run を見ない (停止中に WARN を出し続けない)",
          '"weekly_worksheet_run":' not in watched, watched[:400])

    print("[3] 起動時の登録とスケジューラのループ")
    start = src.index("async def _start_background_tasks(")
    blk = src[start:start + 40000]
    i = blk.index("_weekly_worksheet_scheduler()")
    head = blk[max(0, i - 700):i]
    check("起動時の登録は CRON_SECRET and _weekly_worksheet_env_enabled() のときだけ",
          "if CRON_SECRET and _weekly_worksheet_env_enabled():" in head, head[-300:])
    check("停止中は実際の値をログに出す", "Weekly worksheet scheduler disabled" in blk
          and "os.getenv('WEEKLY_WORKSHEET_ENABLED')!r" in blk)

    calls = {"run": 0, "ran_today": 0, "record": 0, "sleep": 0}

    async def fake_sleep(secs):
        calls["sleep"] += 1
        if calls["sleep"] >= 2:
            raise asyncio.CancelledError()

    async def fake_to_thread(fn, *a, **k):
        return fn(*a, **k)

    def fake_run():
        calls["run"] += 1
        return {"students_processed": 0, "worksheets_created": 0}

    def fake_ran_today(name):
        calls["ran_today"] += 1
        return False

    shim = types.SimpleNamespace(sleep=fake_sleep, to_thread=fake_to_thread, CancelledError=asyncio.CancelledError)
    orig = (mod.asyncio, mod._run_weekly_worksheet_generation, mod._check_scheduler_ran_today_jst, mod._record_scheduler_run)

    def run_loop_once(value):
        for k in calls:
            calls[k] = 0
        mod.asyncio = shim
        mod._run_weekly_worksheet_generation = fake_run
        mod._check_scheduler_ran_today_jst = fake_ran_today
        mod._record_scheduler_run = lambda name, props: calls.__setitem__("record", calls["record"] + 1)
        try:
            with _Env(value):
                try:
                    asyncio.run(mod._weekly_worksheet_scheduler())
                except asyncio.CancelledError:
                    pass
        finally:
            (mod.asyncio, mod._run_weekly_worksheet_generation,
             mod._check_scheduler_ran_today_jst, mod._record_scheduler_run) = orig
        return dict(calls)

    c_off = run_loop_once(None)
    check("停止中: ループが起きても生成しない・実行記録も書かない", c_off["run"] == 0 and c_off["record"] == 0
          and c_off["ran_today"] == 0 and c_off["sleep"] == 2, c_off)
    c_on = run_loop_once("1")
    check("env=1: 従来どおり生成して実行記録を書く", c_on["run"] == 1 and c_on["record"] == 1, c_on)
    check("_run_weekly_worksheet_generation 自体には env の判定を入れていない (テストが直接呼ぶ)",
          "_weekly_worksheet_env_enabled" not in src[src.index("def _run_weekly_worksheet_generation("):
                                                        src.index('@app.get("/api/student/worksheet/this-week")')])

    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    cron = {"X-Cron-Secret": "test-cron-secret"}

    print("[4] 手動実行 API (run-weekly-now)")
    now = datetime.datetime.now(datetime.timezone.utc)
    te = (now + datetime.timedelta(days=3650)).isoformat()
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO exam_questions (exam_id, part_key, question_data) VALUES ('daigaku', 'r_long', ?)",
              (json.dumps({"questions": [{"q": "x"}]}),))

    def make(name, email):
        c.execute(
            "INSERT INTO students (name, email, status, trial_end, course, grade, goal, ai_disabled, line_user_id) "
            "VALUES (?, ?, 'trial', ?, 'kokuritsu_nankan', '高校3年', '国公立大学', 0, ?)",
            (name, email, te, "U-" + email.split("@")[0]),
        )
        c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
        sid = c.fetchone()["id"]
        c.execute("INSERT INTO student_weakness (student_id, subject, topic, question_count, avg_confidence_score, last_seen_at) "
                  "VALUES (?, 'english', NULL, 5, 0.5, ?)", (sid, now.isoformat()))
        return sid

    sid_a = make("テスト生徒 A", "ws-stop-a@example.org")
    sid_b = make("テスト生徒 B", "ws-stop-b@example.org")
    sid_c = make("テスト生徒 C", "ws-stop-c@example.org")
    sid_d = make("テスト生徒 D", "ws-stop-d@example.org")
    conn.commit(); conn.close()

    def n_archives():
        cn = mod.db(); cc = cn.cursor()
        cc.execute("SELECT COUNT(*) AS n FROM worksheet_archives")
        n = cc.fetchone()["n"]
        cn.close()
        return n

    sent = []
    orig_mail, orig_line = mod._send_monitor_email, mod._do_line_push
    mod._send_monitor_email = lambda subj, body, to_email=None: (sent.append(("mail", to_email)) or {"sent": True})
    mod._do_line_push = lambda sid, tmpl, params=None: (sent.append(("line", sid)) or {"ok": True})
    try:
        before = n_archives()
        with _Env(None):
            r = client.post("/api/admin/worksheet/run-weekly-now")
            check("未認証は 401 (認証が先)", r.status_code == 401, (r.status_code, r.text[:200]))
            r = client.post("/api/admin/worksheet/run-weekly-now", headers=cron)
            check("停止中は 409", r.status_code == 409, (r.status_code, r.text[:200]))
            check("409 の理由は日本語で env 名を含む", "WEEKLY_WORKSHEET_ENABLED" in r.text and "停止中" in r.text, r.text[:300])
            r = client.post("/api/admin/worksheet/run-weekly-now",
                            headers={"Authorization": "Bearer " + mod._sign_admin_token()["token"]})
            check("管理者トークンでも停止中は 409", r.status_code == 409, (r.status_code, r.text[:200]))
        check("停止中の手動実行で worksheet_archives は 1 行も増えない", n_archives() == before, (before, n_archives()))
        check("停止中の手動実行でメールも LINE も送らない", sent == [], sent)
        with _Env("1"):
            r = client.post("/api/admin/worksheet/run-weekly-now", headers=cron)
            check("env=1 なら 200 で従来どおり生成する", r.status_code == 200 and (r.json() or {}).get("ok") is True,
                  (r.status_code, r.text[:200]))
        check("env=1 の手動実行では行が増える (既存の挙動は残っている)", n_archives() > before, (before, n_archives()))
    finally:
        mod._send_monitor_email, mod._do_line_push = orig_mail, orig_line

    print("[5] this-week / history (行は消さない・古い行を「今週」にしない)")
    jst_today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date()
    d = lambda n: (jst_today + datetime.timedelta(days=n)).isoformat()
    conn = mod.db(); c = conn.cursor()
    c.execute("DELETE FROM worksheet_archives")

    def put(sid, week_start):
        c.execute("INSERT INTO worksheet_archives (student_id, week_start_date, subject_topics, questions_json, question_count) "
                  "VALUES (?, ?, ?, '[]', 0)", (sid, week_start, json.dumps([{"subject": "english", "topic": "時制"}])))

    days_to_monday = (7 - jst_today.weekday()) % 7 or 7
    put(sid_a, d(-20)); put(sid_a, d(days_to_monday))   # A: 3 週前 + 今週 (次の月曜始まり)
    put(sid_b, d(-20))                                   # B: 3 週前だけ
    put(sid_c, d(-7))                                    # C: ちょうど 7 日前 (境界 = 見える)
    put(sid_d, d(-8))                                    # D: 8 日前 (見えない)
    conn.commit(); conn.close()

    def this_week(sid):
        r = client.get("/api/student/worksheet/this-week", headers={"Authorization": "Bearer " + student_token(mod, sid)})
        return r.status_code, (r.json() if r.status_code == 200 else {})

    with _Env(None):
        code, j = this_week(sid_a)
        check("停止中: 今週の行は返る + discontinued: true",
              code == 200 and (j.get("worksheet") or {}).get("week_start_date") == d(days_to_monday)
              and j.get("discontinued") is True, (code, j))
        code, j = this_week(sid_b)
        check("停止中: 3 週前の行しか無い生徒は worksheet: null + discontinued: true",
              code == 200 and j.get("worksheet") is None and j.get("discontinued") is True, (code, j))
        code, j = this_week(sid_c)
        check("停止中: ちょうど 7 日前 (JST) の行は見える", code == 200 and (j.get("worksheet") or {}).get("week_start_date") == d(-7),
              (code, j))
        code, j = this_week(sid_d)
        check("停止中: 8 日前の行は見えない", code == 200 and j.get("worksheet") is None, (code, j))
        for sid, want in ((sid_a, [d(days_to_monday), d(-20)]), (sid_b, [d(-20)]), (sid_d, [d(-8)])):
            r = client.get("/api/student/worksheet/history", headers={"Authorization": "Bearer " + student_token(mod, sid)})
            got = [x.get("week_start_date") for x in (r.json() or {}).get("history", [])] if r.status_code == 200 else None
            check(f"停止中も /history は全部出す (生徒 #{sid}: {len(want)} 件)", got == want, (r.status_code, got))
    with _Env("1"):
        code, j = this_week(sid_b)
        check("env=1: 従来どおり最新の行を返す (日付の下限なし)・discontinued は付かない",
              code == 200 and (j.get("worksheet") or {}).get("week_start_date") == d(-20) and "discontinued" not in j, (code, j))
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) AS n FROM worksheet_archives")
    check("this-week / history は行を消さない", c.fetchone()["n"] == 5)
    conn.close()

    print("[6] CEO「生徒の見え方」(admin sapuri preview) の weekly_enabled")
    adm = {"Authorization": "Bearer " + mod._sign_admin_token()["token"]}
    with _Env(None):
        r = client.get(f"/api/admin/sapuri/preview?student_id={sid_a}", headers=adm)
        check("停止中は weekly_enabled: false", r.status_code == 200 and (r.json() or {}).get("weekly_enabled") is False,
              (r.status_code, r.text[:200]))
    with _Env("1"):
        r = client.get(f"/api/admin/sapuri/preview?student_id={sid_a}", headers=adm)
        check("env=1 は weekly_enabled: true (呼ぶたびに env を読む)",
              r.status_code == 200 and (r.json() or {}).get("weekly_enabled") is True, (r.status_code, r.text[:200]))
    ceo = open(os.path.join(REPO, "ceo.html"), encoding="utf-8").read()
    check("ceo.html は weekly_enabled === false のとき「停止中」の見出しにする",
          "d.weekly_enabled === false" in ceo and "週次プリントは停止中" in ceo)

    print("[7] mypage.html (inline・?v= 不要) の終了表示")
    mp = open(os.path.join(REPO, "mypage.html"), encoding="utf-8").read()
    fn = mp[mp.index("async function renderWeeklyWorksheet("):mp.index("async function renderVocabSrsWidget(")]
    check("「(毎週日曜 5:00 自動生成)」は id 付きの span (停止中に差し替える)", 'id="worksheetSchedLabel"' in mp)
    check("discontinued のとき「終了しました」と 📚 履歴 を案内する",
          "data.discontinued === true" in fn and "終了しました" in fn and "📚 履歴" in fn)
    check("プリントを一度も受け取っていない生徒には欄ごと出さない (history?limit=1 で確かめる)",
          "/api/student/worksheet/history?limit=1" in fn)

    print()
    if FAILURES:
        print(f"❌ FAIL ({len(FAILURES)} 件)")
        for f in FAILURES:
            print("   -", f)
        sys.exit(1)
    print("✅ PASS")


if __name__ == "__main__":
    main()
