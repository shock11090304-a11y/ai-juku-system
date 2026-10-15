#!/usr/bin/env python3
"""📊 週次レポートの二重送信を止めた回帰テスト (2026-10-15・一時 SQLite・メール / LINE / AI コメントは偽物)。

背景: 週次レポートは日曜 19:00 の本命 (_weekly_reports_scheduler) と、20:05 の GitHub Actions の予備
  (.github/workflows/weekly-reports-backup.yml → scripts/trigger_weekly_reports.py) が同じ POST /api/cron/weekly-reports を叩く。
  メールは notifications で 6 日の dedup をしていたが LINE には無く、LINE 連携済みの家庭には毎週 2 通届いていた
  (LINE の無料枠も 2 倍使う)。予備の回も、送る相手がいないのに全員分の AI コメントを作り直していた。
  直し方: 生徒ごとに直近 6 日に**成功した**週次レポート (生徒メール・保護者メール・LINE) を 1 回の SELECT で引き
  (_weekly_report_sent_templates)、送る必要がある経路だけ送る。AI コメントは判定の後で、メールを送るときだけ作る。
  メールの上限 (WEEKLY_REPORT_EMAIL_CAP・既定 80) は変えていない。

固定する性質 (生徒名・メールは架空 = 公開リポジトリ):
  [1] 1 回目 (19:00): A (子メール・保護者メール・LINE) に 1 通ずつ・B (LINE だけ) に LINE 1 通・AI コメントはメールを送る生徒の分だけ
      (B には作らない)・7 日前の送信は止めない・2 日前に送り済みの E は送らず skipped_dup
  [2] 2 回目 (20:05 の予備): メール 0・LINE 0 (失敗した D の LINE だけ送り直す)・AI コメント 0・skipped_dup / skipped_dup_line
  [3] 失敗行 (success=0) は止めない: C の前の失敗は 1 回目に送る・1 回目に LINE だけ失敗した D は 2 回目に LINE だけ送り直す
  [4] 重複の判定は AI コメントより前・照会は生徒ごとに 1 回
  [5] 上限は今までどおり: 送り済みの家庭は capped に数えない・上限に達した後の生徒には AI コメントを作らない
  [6] dry_run は SQLite でも動き (row['line_user_id'])・LINE の宛先を出す・何も送らない
  [7] 手動の即送信 (send-one) は dedup しない (塾長の明示の操作)・SQLite でも LINE の経路が動く
  [8] 判定 (_weekly_report_verdict) と prod_healthcheck の weekly_report: 全員が「送り済み」で飛んだ回を「断絶」と誤報しない
      (重複防止が無い回の判定は今までどおり)
  [9] ソース: インラインの dedup 2 本が消えた・row.get('line_user_id') が残っていない・上限の既定 80・
      予備スクリプトの表示 (重複防止の人数・定時の予備が送ったときの注意) と workflow のコメント

実行:
    python3 scripts/health_check/test_weekly_report_dedup.py
    # exit 0 = PASS / 1 = FAIL
"""
import contextlib
import datetime
import importlib.util
import io
import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []
CRON = "test-cron-secret"
STATS = "test-stats-token"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="wr_dedup_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと本番 Postgres に書き込む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "",
        "ANTHROPIC_API_KEY": "", "BASE_URL": "https://example.invalid", "CRON_SECRET": CRON,
        "STATS_TOKEN": STATS, "ZERO_WEEK_REPORT_ENABLED": "1",
    })
    os.environ.pop("WEEKLY_REPORT_EMAIL_CAP", None)
    spec = importlib.util.spec_from_file_location("aijuku_main_wr_dedup", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def utc_str(dt):
    return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def mk(mod, name, email, *, student_email=None, verified=0, parent_email=None, line_user_id=None):
    conn = mod.db(); c = conn.cursor()
    far = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)).isoformat()
    c.execute(
        "INSERT INTO students (name, email, status, plan, trial_end, grade, student_email, student_email_verified, "
        "parent_email, parent_email_enabled, line_user_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (name, email, "paid", "founder_special", far, "高校2年", student_email, verified, parent_email, 1, line_user_id),
    )
    conn.commit()
    c.execute("SELECT id FROM students WHERE name = ?", (name,))
    sid = c.fetchone()["id"]
    conn.close()
    return sid


def add_notification(mod, sid, template, days_ago, success=1, channel="email"):
    conn = mod.db(); c = conn.cursor()
    at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_ago)
    c.execute("INSERT INTO notifications (student_id, channel, template, payload, success, sent_at) VALUES (?,?,?,?,?,?)",
              (sid, channel, template, "{}", success, utc_str(at)))
    conn.commit(); conn.close()


class Fakes:
    """メール・LINE・AI コメント・重複の照会・time.sleep を記録する偽物。順番は self.log に (種類, 生徒ID or 宛先) で残す。"""

    def __init__(self, mod):
        self.mod = mod
        self.log = []
        self.line_fail = set()      # この生徒の LINE は失敗させる (notifications に success=0 を書く = 本物と同じ)
        self.mail_fail = set()      # この宛先のメールは失敗させる
        real_lookup = mod._weekly_report_sent_templates

        def lookup(sid):
            self.log.append(("dedup", int(sid)))
            return real_lookup(sid)

        def ai(ctx):
            self.log.append(("ai", int(ctx["sid"])))
            return ctx

        def mail(to, ctx):
            self.log.append(("mail", to))
            if to in self.mail_fail:
                return {"sent": False, "error": "fixture failure"}
            return {"sent": True}

        def line(sid, tmpl, params=None):
            ok = int(sid) not in self.line_fail
            self.log.append(("line", int(sid), tmpl))
            _c = mod.db(); _cur = _c.cursor()
            _cur.execute("INSERT INTO notifications (student_id, channel, template, payload, success) VALUES (?, 'line', ?, '{}', ?)",
                         (int(sid), tmpl, 1 if ok else 0))
            _c.commit(); _c.close()
            return {"ok": ok}

        mod._weekly_report_sent_templates = lookup
        mod._weekly_coach_comments = ai
        mod._build_weekly_report_ctx = lambda sid, name, stats: {"sid": int(sid), "name": name, "stats": stats}
        mod._send_weekly_report_email = mail
        mod._do_line_push = line
        mod._compute_weekly_stats = lambda sid, days=7, week_aligned=True: {
            "hours": 1.5, "questions": 12, "problems_done": 12, "accuracy": 75, "weakest_subject": None,
            "subject_stats": {}, "days": 7}

    def kinds(self, kind):
        return [e for e in self.log if e[0] == kind]


@contextlib.contextmanager
def no_sleep():
    real = time.sleep
    time.sleep = lambda s: None
    try:
        yield
    finally:
        time.sleep = real


def run(client, fk, dry=False):
    fk.log.clear()
    with no_sleep():
        r = client.post("/api/cron/weekly-reports" + ("?dry_run=true" if dry else ""), headers={"X-Cron-Secret": CRON})
    return r.status_code, (r.json() if r.status_code == 200 else r.text)


def main():
    print("📊 週次レポートの二重送信を止めた回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    fk = Fakes(mod)

    A = mk(mod, "Family A", "fam-a-parent@example.org", student_email="fam-a-child@example.org", verified=1,
           parent_email="fam-a-parent@example.org", line_user_id="U-fixture-a")
    B = mk(mod, "Family B", None, line_user_id="U-fixture-b")                      # LINE だけ (メールの宛先なし)
    C = mk(mod, "Family C", "fam-c@example.org", line_user_id="U-fixture-c")        # 前の失敗行がある
    D = mk(mod, "Family D", "fam-d@example.org", line_user_id="U-fixture-d")        # 1 回目は LINE が失敗する
    E = mk(mod, "Family E", "fam-e@example.org")                                    # 2 日前に送り済み (send-one など)
    F = mk(mod, "Family F", "fam-f@example.org")                                    # 7 日前の送信 = 先週の分
    add_notification(mod, C, "weekly_report", 1, success=0, channel="line")
    add_notification(mod, C, "weekly_report_email", 1, success=0)
    add_notification(mod, E, "weekly_report_email", 2)
    add_notification(mod, F, "weekly_report_email", 7)
    add_notification(mod, A, "weekly_report", 7, channel="line")
    fk.line_fail = {D}

    # ------------------------------------------------------------------
    print("[1] 1 回目 (日曜 19:00 の本命)")
    st, j = run(client, fk)
    check("200 で返る", st == 200, j)
    mails = sorted(e[1] for e in fk.kinds("mail"))
    check("メール: A の子と保護者・C・D・F に 1 通ずつ (E は送り済み)",
          mails == sorted(["fam-a-child@example.org", "fam-a-parent@example.org", "fam-c@example.org",
                           "fam-d@example.org", "fam-f@example.org"]), mails)
    lines = sorted(e[1] for e in fk.kinds("line"))
    check("LINE: A・B・C・D に 1 回ずつ (7 日前の A の LINE は止めない)", lines == sorted([A, B, C, D]), lines)
    check("LINE のテンプレートは weekly_report", all(e[2] == "weekly_report" for e in fk.kinds("line")), fk.kinds("line"))
    ai = sorted(e[1] for e in fk.kinds("ai"))
    check("AI コメント: メールを送る A・C・D・F の 1 回ずつ (LINE だけの B・送り済みの E には作らない)", ai == sorted([A, C, D, F]), ai)
    check("集計: sent_email 5・sent_line 3 (D は失敗)・skipped_dup 1 (E)・skipped_dup_line 0・failed 0",
          isinstance(j, dict) and j.get("sent_email") == 5 and j.get("sent_line") == 3 and j.get("skipped_dup") == 1
          and j.get("skipped_dup_line") == 0 and j.get("failed") == 0, j)
    check("上限は誰にも当たっていない (capped 0)", isinstance(j, dict) and j.get("capped") == 0, j)

    print("\n[4] 重複の判定は AI コメントより前・照会は生徒ごとに 1 回")
    order_ok = True
    for sid in (A, C, D, F):
        try:
            if fk.log.index(("dedup", sid)) > fk.log.index(("ai", sid)):
                order_ok = False
        except ValueError:
            order_ok = False
    check("A・C・D・F とも 重複の照会 → AI コメント の順", order_ok, fk.log)
    dd = [e[1] for e in fk.kinds("dedup")]
    check("照会は 1 生徒 1 回 (6 名で 6 回)", sorted(dd) == sorted([A, B, C, D, E, F]), dd)

    # ------------------------------------------------------------------
    print("\n[2] 2 回目 (20:05 の GitHub の予備)")
    fk.line_fail = set()
    st, j = run(client, fk)
    check("メールは 0 通", not fk.kinds("mail"), fk.kinds("mail"))
    check("LINE は 1 回目に失敗した D だけ送り直す", [e[1] for e in fk.kinds("line")] == [D], fk.kinds("line"))
    check("AI コメントは 1 回も作らない", not fk.kinds("ai"), fk.kinds("ai"))
    check("集計: sent_email 0・sent_line 1・skipped_dup 5 (A・B・C・E・F)・skipped_dup_line 3 (A・B・C)",
          isinstance(j, dict) and j.get("sent_email") == 0 and j.get("sent_line") == 1 and j.get("skipped_dup") == 5
          and j.get("skipped_dup_line") == 3, j)
    check("skipped (活動なし) の意味は変えない = 0", isinstance(j, dict) and j.get("skipped") == 0, j)

    print("\n[3] 失敗行は止めない・3 回目は全員が送り済み")
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT template, success FROM notifications WHERE student_id = ? AND template IN ('weekly_report', 'weekly_report_email') "
              "ORDER BY id", (C,))
    rows_c = [(r["template"], r["success"]) for r in c.fetchall()]
    c.execute("SELECT success FROM notifications WHERE student_id = ? AND template = 'weekly_report' ORDER BY id", (D,))
    rows_d = [r["success"] for r in c.fetchall()]
    conn.close()
    check("C: 前の失敗行 (success=0) の後に、1 回目でメールと LINE が成功", rows_c[-2:] in ([("weekly_report_email", 1), ("weekly_report", 1)],
                                                                           [("weekly_report", 1), ("weekly_report_email", 1)]), rows_c)
    check("D: LINE は 失敗 → 送り直しで成功", rows_d == [0, 1], rows_d)
    st, j = run(client, fk)
    check("3 回目: 何も送らない・AI コメントなし", not fk.kinds("mail") and not fk.kinds("line") and not fk.kinds("ai"), fk.log)
    check("3 回目: skipped_dup 6・skipped_dup_line 4", isinstance(j, dict) and j.get("skipped_dup") == 6 and j.get("skipped_dup_line") == 4, j)

    # ------------------------------------------------------------------
    print("\n[5] メールの上限 (WEEKLY_REPORT_EMAIL_CAP) は今までどおり・送り済みは数えない")
    G = mk(mod, "Family G", "fam-g@example.org")
    H = mk(mod, "Family H", "fam-h@example.org")
    I = mk(mod, "Family I", "fam-i@example.org")
    add_notification(mod, I, "weekly_report_email", 1)
    J = mk(mod, "Family J", "fam-j@example.org", line_user_id="U-fixture-j")   # メールは送り済み・LINE はまだ
    add_notification(mod, J, "weekly_report_email", 1)
    os.environ["WEEKLY_REPORT_EMAIL_CAP"] = "1"
    try:
        st, j = run(client, fk)
    finally:
        os.environ.pop("WEEKLY_REPORT_EMAIL_CAP", None)
    mails = [e[1] for e in fk.kinds("mail")]
    check("上限 1: メールは G か H の 1 通だけ", len(mails) == 1 and mails[0] in ("fam-g@example.org", "fam-h@example.org"), mails)
    check("capped は送れなかった 1 名だけ (送り済みの A〜F・I と、メールは送り済みで LINE だけ送る J は数えない)",
          isinstance(j, dict) and j.get("capped") == 1, j)
    check("J: メールは送り済みなので LINE だけ送る (上限に関係なく)", [e[1] for e in fk.kinds("line")] == [J], fk.kinds("line"))
    ai = [e[1] for e in fk.kinds("ai")]
    check("上限に達した後の生徒・LINE だけの J には AI コメントを作らない (1 回だけ)", len(ai) == 1 and ai[0] in (G, H), ai)
    check("上限の既定は 80 のまま (変えていない)", 'int(os.getenv("WEEKLY_REPORT_EMAIL_CAP", "80"))' in open(MAIN_PY, encoding="utf-8").read())

    # ------------------------------------------------------------------
    print("\n[6] dry_run (SQLite でも LINE の宛先を出す・何も送らない)")
    st, j = run(client, fk, dry=True)
    pv = {p["student_id"]: p for p in ((j or {}).get("previews") or [])} if isinstance(j, dict) else {}
    check("dry_run が 200 で全員分の preview (failed 0)", st == 200 and isinstance(j, dict) and j.get("failed") == 0 and len(pv) == 10, j)
    check("A・B は would_send_line True / E は False", pv.get(A, {}).get("would_send_line") is True and pv.get(B, {}).get("would_send_line") is True
          and pv.get(E, {}).get("would_send_line") is False, {k: v.get("would_send_line") for k, v in pv.items()})
    check("dry_run は送らない・AI コメントも作らない", not fk.kinds("mail") and not fk.kinds("line") and not fk.kinds("ai"), fk.log)

    # ------------------------------------------------------------------
    print("\n[7] 手動の即送信 (send-one) は dedup しない")
    fk.log.clear()
    origin = mod.ALLOWED_ORIGINS[0].rstrip("/")
    r = client.post("/api/weekly-reports/send-one", json={"student_id": A},
                    headers={"X-Stats-Token": STATS, "Origin": origin})
    jj = r.json() if r.status_code == 200 else r.text
    check("send-one が 200 (SQLite の行でも LINE の経路が動く)", r.status_code == 200, jj)
    check("日曜に送り済みの A にも LINE とメールを 1 回ずつ送る", [e[1] for e in fk.kinds("line")] == [A] and len(fk.kinds("mail")) == 1, fk.log)
    check("send-one は重複の照会をしない", not fk.kinds("dedup"), fk.log)

    # ------------------------------------------------------------------
    print("\n[8] 判定: 全員が送り済みで飛んだ回を「断絶」と誤報しない")
    v_dup = mod._weekly_report_verdict([{"name": "weekly_reports_run", "stale": False,
                                         "props": {"sent_email": 0, "sent_line": 0, "skipped": 3, "skipped_dup": 6, "zero_week": 0}}])
    check("_weekly_report_verdict: skipped_dup があれば正常", v_dup.startswith("正常") and "重複防止 6" in v_dup, v_dup)
    v_old = mod._weekly_report_verdict([{"name": "weekly_reports_run", "stale": False,
                                         "props": {"sent_email": 0, "sent_line": 0, "skipped": 3}}])
    check("_weekly_report_verdict: 重複防止が無く送信 0 件なら今までどおり断絶の疑い", "送信 0 件" in v_old, v_old)
    spec = importlib.util.spec_from_file_location("prod_hc_wr_dedup", os.path.join(HERE, "prod_healthcheck.py"))
    hc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hc)

    class _Cur:
        def __init__(self, props):
            self.props = props

        def execute(self, sql, params=None):
            pass

        def fetchone(self):
            return (json.dumps(self.props),)

    hc._table_exists = lambda cur, name: True
    hc.results.clear()
    hc.check_weekly_report(_Cur({"sent_email": 0, "sent_line": 0, "skipped": 3, "skipped_dup": 6, "total_students": 9}))
    check("prod_healthcheck: 全員が送り済みの回は PASS", hc.results and hc.results[-1][1] == hc.PASS, hc.results)
    hc.results.clear()
    hc.check_weekly_report(_Cur({"sent_email": 0, "sent_line": 0, "skipped": 9, "total_students": 9}))
    check("prod_healthcheck: 送り済みも無く送信 0 なら今までどおり FAIL", hc.results and hc.results[-1][1] == hc.FAIL, hc.results)

    # ------------------------------------------------------------------
    print("\n[9] ソース・予備スクリプト・workflow")
    src = open(MAIN_PY, encoding="utf-8").read()
    i0 = src.index("def cron_weekly_reports(")
    cron_src = src[i0:src.index("\ndef _require_admin_or_stats_token", i0)]
    j0 = src.index("def weekly_reports_send_one(")
    one_src = src[j0:src.index("\n# ====", j0)]
    check("インラインの dedup 2 本 (生徒メール・保護者メール) が消えた",
          "template='weekly_report_email' AND success=1" not in cron_src and "template='weekly_report_parent_email' AND success=1" not in cron_src)
    check("row.get('line_user_id') が残っていない (sqlite3.Row に .get は無い)",
          'row.get("line_user_id")' not in cron_src and 'row.get("line_user_id")' not in one_src
          and "row.get('line_user_id')" not in cron_src + one_src)
    check("cron は重複の照会 → AI コメントの順に書かれている",
          0 < cron_src.find("_weekly_report_sent_templates(") < cron_src.find("_weekly_coach_comments("))
    check("send-one は重複の照会を呼ばない (手動は dedup しない)", "_weekly_report_sent_templates(" not in one_src)

    trig_path = os.path.join(REPO, "scripts", "trigger_weekly_reports.py")
    tspec = importlib.util.spec_from_file_location("trigger_weekly_reports_t", trig_path)
    trig = importlib.util.module_from_spec(tspec)
    tspec.loader.exec_module(trig)

    class _Resp:
        def __init__(self, body):
            self.body = json.dumps(body).encode("utf-8")
            self.status = 200

        def read(self):
            return self.body

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def run_trigger(body, event=None):
        seen = []

        def fake_urlopen(req, timeout=None):
            seen.append(req.full_url)
            return _Resp(body)

        old_env = {k: os.environ.get(k) for k in ("CRON_SECRET", "API_BASE_URL", "DRY_RUN", "GITHUB_EVENT_NAME")}
        os.environ.update({"CRON_SECRET": "fixture-secret", "API_BASE_URL": "http://127.0.0.1:9"})
        os.environ.pop("DRY_RUN", None)
        if event is None:
            os.environ.pop("GITHUB_EVENT_NAME", None)
        else:
            os.environ["GITHUB_EVENT_NAME"] = event
        real = trig.urllib.request.urlopen
        trig.urllib.request.urlopen = fake_urlopen
        out, err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = trig.main()
        finally:
            trig.urllib.request.urlopen = real
            for k, v in old_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        return rc, out.getvalue() + err.getvalue(), seen

    rc, out, seen = run_trigger({"sent_email": 0, "sent_line": 0, "skipped": 3, "failed": 0, "skipped_dup": 40, "skipped_dup_line": 25},
                                event="schedule")
    check("予備スクリプト: 送り済みの人数を出す (重複防止でスキップ 40 名・LINE 25 件)",
          rc == 0 and "重複防止でスキップ: 40 名" in out and "25 件" in out and "予備が送りました" not in out, out)
    check("予備スクリプト: 叩くのは渡した API だけ (本番 URL に出ない)", seen == ["http://127.0.0.1:9/api/cron/weekly-reports"], seen)
    rc, out, _ = run_trigger({"sent_email": 2, "sent_line": 1, "skipped": 3, "failed": 0, "skipped_dup": 38, "skipped_dup_line": 24},
                             event="schedule")
    check("予備スクリプト: 定時の予備が送ったときは 本命で送れなかった分 と出す (exit 0)", rc == 0 and "予備が送りました" in out, out)
    rc, out, _ = run_trigger({"sent_email": 2, "sent_line": 1, "skipped": 3, "failed": 0, "skipped_dup": 0, "skipped_dup_line": 0},
                             event="workflow_dispatch")
    check("予備スクリプト: 手動で送ったときは その注意を出さない", rc == 0 and "予備が送りました" not in out, out)
    rc, out, _ = run_trigger({"sent_email": 0, "sent_line": 0, "skipped": 3, "failed": 0})
    check("予備スクリプト: 古いサーバ (skipped_dup なし) でも落ちず、重複防止の行を出さない", rc == 0 and "重複防止" not in out, out)
    trig_src = open(trig_path, encoding="utf-8").read()
    check("予備スクリプトの説明: LINE も 6 日 dedup", "LINE" in trig_src and "6 日" in trig_src and "7 日以内" not in trig_src)
    wf = open(os.path.join(REPO, ".github", "workflows", "weekly-reports-backup.yml"), encoding="utf-8").read()
    check("workflow のコメント: LINE も重複防止 (_weekly_report_sent_templates)", "_weekly_report_sent_templates" in wf and "LINE" in wf)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for f in FAILURES:
            print(f"   - {f}")
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
