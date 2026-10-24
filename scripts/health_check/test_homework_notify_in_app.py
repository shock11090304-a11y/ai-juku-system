#!/usr/bin/env python3
"""📣 宿題・ドリルのお知らせはアプリの中で — LINE 停止・メールは HOMEWORK_NOTIFY_EMAIL・リンクは AI 判定 (2026-10-15 塾長決定)。

背景: 塾長「アプリを開けば分かる」。宿題・ドリルを配ったときのお知らせはアプリ内表示 (🆕 新しい宿題) が基本。
  LINE は宿題・ドリルのお知らせに使わない (ログインコードの LINE はそのまま)。登録メール (多くは保護者のアドレス) は
  塾長が CEO で手で配ったとき (source='manual') だけ。自動配信 (3日ドリル・クラス自動宿題) は LINE もメールも送らない。

固定する性質 (一時 SQLite・外部通信なし・LINE とメールは偽物):
  [1] 既定: source='manual' は LINE 0・メール 1。source='auto' は LINE 0・メール 0 で、待ちもリンクの照会もせずすぐ返る
  [2] HOMEWORK_NOTIFY_EMAIL=off / all / 1 / 0 / 不明な値 (= manual)・HOMEWORK_NOTIFY_LINE=1 (非常スイッチで LINE が戻る)
  [3] メールのリンク: AIなし → /class.html?tab=homework、AIなし + AI 体験中 → /mypage.html?focus=homework、
      AIあり → mypage、体験が切れた AIなし → class。# 付きのリンクは使わない
  [4] POST /api/admin/grammar-drill/create (塾長の配信 = manual): 200・LINE 0・メールは既定で送る・notify_channels・
      経路に合った message (「LINE/メールで通知を送信しました」と決め打ちしない)・off なら「送っていません」
  [5] 3日ドリル (_run_weakness_drill_routine) は source='auto': 既定で LINE 0・メール 0・summary.notify。all ならメール
  [6] GET /api/student/grammar-drills: 'assigned' も未提出 (summary.open・並び順)・self_issued (今日の1問・診断)
  [7] ログインコードの LINE (magic_link_login) は変わらない・AIなし枠の許可集合は不変・呼び出し側は source を渡す

実行:
    python3 scripts/health_check/test_homework_notify_in_app.py
    # exit 0 = PASS / 1 = FAIL
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import json
import os
import re
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []
BASE = "https://example.invalid"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="hw_notify_"), "test.db")
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
        "BASE_URL": BASE,
        "CRON_SECRET": "test-cron-secret",
    })
    for k in ("HOMEWORK_NOTIFY_EMAIL", "HOMEWORK_NOTIFY_LINE"):
        os.environ.pop(k, None)
    spec = importlib.util.spec_from_file_location("aijuku_main_hw_notify", MAIN_PY)
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


class Env:
    """HOMEWORK_NOTIFY_EMAIL / HOMEWORK_NOTIFY_LINE を一時的に差し替える (None = 未設定)。"""

    def __init__(self, email=None, line=None):
        self.want = {"HOMEWORK_NOTIFY_EMAIL": email, "HOMEWORK_NOTIFY_LINE": line}

    def __enter__(self):
        self.old = {k: os.environ.get(k) for k in self.want}
        for k, v in self.want.items():
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


class Fakes:
    """_do_line_push / _send_message_email / time.sleep / リンクの照会を記録する偽物 (with の間だけ差し替える)。"""

    def __init__(self, mod):
        self.mod = mod
        self.lines, self.mails, self.sleeps, self.lookups = [], [], [], []

    def __enter__(self):
        m = self.mod
        self.orig = (m._do_line_push, m._send_message_email, time.sleep, m._homework_notify_link_paths)
        orig_lookup = m._homework_notify_link_paths

        def fake_line(sid, template, params=None):
            self.lines.append((sid, template, dict(params or {})))
            return {"ok": True}

        def fake_mail(to, subject, body, student_name=None):
            self.mails.append({"to": to, "subject": subject, "body": body})
            return {"sent": True}

        def lookup(ids):
            self.lookups.append(list(ids))
            return orig_lookup(ids)

        m._do_line_push = fake_line
        m._send_message_email = fake_mail
        m._homework_notify_link_paths = lookup
        time.sleep = lambda s: self.sleeps.append(s)
        return self

    def __exit__(self, *a):
        m = self.mod
        m._do_line_push, m._send_message_email, time.sleep, m._homework_notify_link_paths = self.orig


def main():
    mod = load_main()
    src = open(MAIN_PY, encoding="utf-8").read()
    now = datetime.datetime.now(datetime.timezone.utc)
    te = (now + datetime.timedelta(days=3650)).isoformat()
    future = mod._utc_naive_iso(now + datetime.timedelta(days=5))
    past = mod._utc_naive_iso(now - datetime.timedelta(days=1))

    conn = mod.db(); c = conn.cursor()

    def make(name, email, ai_disabled=0, trial=None, grade="高校2年", line=True):
        c.execute(
            "INSERT INTO students (name, email, status, trial_end, course, grade, goal, ai_disabled, ai_trial_until, line_user_id) "
            "VALUES (?, ?, 'trial', ?, 'kokuritsu_nankan', ?, '国公立大学', ?, ?, ?)",
            (name, email, te, grade, ai_disabled, trial, ("U-" + email.split("@")[0]) if line else None),
        )
        c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
        return c.fetchone()["id"]

    sid_ai = make("架空 生徒A", "hw-a@example.org", 0)
    sid_noai = make("架空 生徒B", "hw-b@example.org", 1)
    sid_trial = make("架空 生徒C", "hw-c@example.org", 1, future)
    sid_expired = make("架空 生徒D", "hw-d@example.org", 1, past)
    sid_rt = make("架空 生徒R", "hw-r@example.org", 0)        # 3日ドリル (既定 env)
    sid_rt2 = make("架空 生徒S", "hw-s@example.org", 0)       # 3日ドリル (HOMEWORK_NOTIFY_EMAIL=all)
    # 英文法「時制」をレビュー済みの出典 (manual-drill-v1) で 30 問 (標準・やや難)
    for i in range(30):
        c.execute("INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) "
                  "VALUES ('english', '時制', ?, ?, ?, 0, '解説', 'manual-drill-v1')",
                  ("standard" if i % 2 else "advanced", f"架空の問題 {i} (   ).", json.dumps(["a", "b", "c", "d"])))
    for sid in (sid_rt, sid_rt2):
        c.execute("INSERT INTO student_weakness (student_id, subject, topic, question_count, qa_accuracy, qa_attempts) "
                  "VALUES (?, 'english', '時制', 10, 0.3, 10)", (sid,))
    conn.commit(); conn.close()
    mod._AI_DISABLED_CACHE.clear()

    def entry(sid, email):
        return {"id": sid, "name": "架空", "email": email, "line_user_id": "U-x"}

    one = [entry(sid_ai, "hw-a@example.org")]

    print("[1] 既定 (HOMEWORK_NOTIFY_EMAIL 未設定 = manual・HOMEWORK_NOTIFY_LINE 未設定 = 0)")
    with Env(), Fakes(mod) as f:
        ch = mod._homework_notify_channels("manual")
        check("manual の経路: LINE なし・メールあり", ch["line"] is False and ch["email"] is True and ch["email_mode"] == "manual", ch)
        r = mod._notify_grammar_drill_assigned(one, "時制", 10, "english", "manual")
        check("source='manual': LINE は 0 回 (LINE 連携済みでも)", f.lines == [], f.lines)
        check("source='manual': メールは 1 通", len(f.mails) == 1 and r["mail_ok"] == 1, (f.mails, r))
    with Env(), Fakes(mod) as f:
        r = mod._notify_grammar_drill_assigned(one * 3, "時制", 10, "english", "auto")
        check("source='auto': LINE 0・メール 0", f.lines == [] and f.mails == [], (f.lines, f.mails))
        check("source='auto': 待ち (sleep) もリンクの照会もせずすぐ返る", f.sleeps == [] and f.lookups == [], (f.sleeps, f.lookups))
        check("返り値に経路と件数", r == {"line_ok": 0, "mail_ok": 0, "mail_fail": 0, "child_mail_ok": 0, "channels": r["channels"]}
              and r["channels"]["source"] == "auto", r)
        r = mod._notify_grammar_drill_assigned(one, "時制", 10, "english")
        check("source を渡し忘れると 'auto' (メールを増やさない側)", f.mails == [] and r["channels"]["source"] == "auto", r)
        r = mod._notify_grammar_drill_assigned(one, "時制", 10, "english", "MANUAL")
        check("'manual' 以外の文字は 'auto' 扱い", f.mails == [] and r["channels"]["source"] == "auto", r)

    print("[2] env の切り替え (呼ぶたびに読む)")
    with Env(email="off"), Fakes(mod) as f:
        mod._notify_grammar_drill_assigned(one, "時制", 10, "english", "manual")
        check("off: 塾長の配信でもメールを送らない", f.mails == [] and f.lines == [], (f.mails, f.lines))
    with Env(email="all"), Fakes(mod) as f:
        mod._notify_grammar_drill_assigned(one, "時制", 10, "english", "auto")
        check("all: 自動配信でもメールを送る (LINE は送らない)", len(f.mails) == 1 and f.lines == [], (f.mails, f.lines))
    for v, want in (("1", "all"), ("true", "all"), ("ON", "all"), ("0", "off"), ("false", "off"), ("manual", "manual"),
                    ("", "manual"), ("garbage", "manual"), ("毎回", "manual")):
        with Env(email=v):
            ch_m, ch_a = mod._homework_notify_channels("manual"), mod._homework_notify_channels("auto")
            check(f"HOMEWORK_NOTIFY_EMAIL={v!r} → {want}", ch_m["email_mode"] == want
                  and ch_m["email"] == (want in ("manual", "all")) and ch_a["email"] == (want == "all"), (ch_m, ch_a))
    with Env(email="garbage"), Fakes(mod) as f:
        mod._notify_grammar_drill_assigned(one, "時制", 10, "english", "manual")
        mod._notify_grammar_drill_assigned(one, "時制", 10, "english", "auto")
        check("不明な値は manual と同じ (manual だけ 1 通)", len(f.mails) == 1, f.mails)
    with Env(email="off", line="1"), Fakes(mod) as f:
        mod._notify_grammar_drill_assigned(one, "時制", 10, "english", "auto")
        check("HOMEWORK_NOTIFY_LINE=1 (非常スイッチ): LINE が grammar_drill_assigned で戻る",
              len(f.lines) == 1 and f.lines[0][1] == "grammar_drill_assigned" and f.mails == [], (f.lines, f.mails))
    for v in ("0", "", "no", "2"):
        with Env(line=v):
            check(f"HOMEWORK_NOTIFY_LINE={v!r} は LINE を送らない", mod._homework_notify_channels("manual")["line"] is False)
    lt = mod.LINE_TEMPLATES["grammar_drill_assigned"]({"unit": "時制", "question_count": 10, "url": BASE, "subject_label": "英文法"})["text"]
    check("LINE テンプレ (非常スイッチ用) のリンクは /mypage.html?focus=homework (# を使わない)",
          lt.rstrip().endswith(f"{BASE}/mypage.html?focus=homework") and "#" not in lt, lt[-80:])

    print("[3] メールのリンク (AIなし = class.html?tab=homework / AIあり・体験中 = mypage.html?focus=homework)")
    people = [entry(sid_ai, "hw-a@example.org"), entry(sid_noai, "hw-b@example.org"),
              entry(sid_trial, "hw-c@example.org"), entry(sid_expired, "hw-d@example.org")]
    with Env(), Fakes(mod) as f:
        mod._notify_grammar_drill_assigned(people, "時制", 10, "english", "manual")
        by = {m["to"]: m["body"] for m in f.mails}
        check("4 名に 1 通ずつ (2 通目からは 1.5 秒あける)", len(f.mails) == 4 and f.sleeps.count(1.5) == 3, (len(f.mails), f.sleeps))
        check("リンクの照会は 1 回 (生徒ごとに DB を引かない)", len(f.lookups) == 1, f.lookups)
        check("AIあり → mypage.html?focus=homework", f"{BASE}/mypage.html?focus=homework" in by.get("hw-a@example.org", ""),
              by.get("hw-a@example.org"))
        check("AIなし → class.html?tab=homework (塾生アプリの「📝 宿題」タブ)",
              f"{BASE}/class.html?tab=homework" in by.get("hw-b@example.org", "") and "📝 宿題" in by.get("hw-b@example.org", ""),
              by.get("hw-b@example.org"))
        check("AIなし + AI 体験中 → mypage (体験中は AIあり扱い)", f"{BASE}/mypage.html?focus=homework" in by.get("hw-c@example.org", ""),
              by.get("hw-c@example.org"))
        check("AI 体験が切れた AIなし → class.html", f"{BASE}/class.html?tab=homework" in by.get("hw-d@example.org", ""),
              by.get("hw-d@example.org"))
        check("どのメールにも # 付きのリンクが無い (ログインをはさむと # が消える)", all("#" not in b for b in by.values()))
        check("リンク先の判定は _ai_blocked_now と一致",
              {s: mod._homework_notify_link_paths([s])[s] for s in (sid_ai, sid_noai, sid_trial, sid_expired)}
              == {s: ("class" if mod._ai_blocked_now(d, t) else "mypage")
                  for s, d, t in ((sid_ai, 0, None), (sid_noai, 1, None), (sid_trial, 1, future), (sid_expired, 1, past))})
    orig_has = mod._students_has_ai_trial_until
    mod._students_has_ai_trial_until = lambda: False
    try:
        paths = mod._homework_notify_link_paths([sid_noai, sid_trial])
        check("ai_trial_until の列が無いときも落ちない (体験なし扱い)", paths == {sid_noai: "class", sid_trial: "class"}, paths)
    finally:
        mod._students_has_ai_trial_until = orig_has
    orig_db = mod.db
    mod.db = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("db down"))
    try:
        paths = mod._homework_notify_link_paths([sid_noai])
        check("照会に失敗したら mypage に倒す (AIなし枠は mypage が class.html へ送る)", paths == {sid_noai: "mypage"}, paths)
    finally:
        mod.db = orig_db

    print("[4] CEO の配信 POST /api/admin/grammar-drill/create (source='manual')")
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    cron = {"X-Cron-Secret": "test-cron-secret"}
    body = {"subject": "english", "unit": "時制", "count": 10, "levels": ["standard", "advanced"], "student_ids": [sid_ai, sid_noai]}
    with Env(), Fakes(mod) as f:
        r = client.post("/api/admin/grammar-drill/create", json=body, headers=cron)
        j = r.json() if r.status_code == 200 else {}
        check("200", r.status_code == 200, (r.status_code, r.text[:200]))
        check("LINE は 0 回 (バックグラウンドの送信が終わった後も)", f.lines == [], f.lines)
        check("既定 (manual) では登録メールを送る (2 名)", sorted(m["to"] for m in f.mails) == ["hw-a@example.org", "hw-b@example.org"],
              [m["to"] for m in f.mails])
        check("notify_channels = {line: False, email: True}", j.get("notify_channels") == {"line": False, "email": True}, j)
        check("message に「LINE」は出ない・登録メールでお知らせと書く", "LINE" not in j.get("message", "")
              and "登録メールでお知らせ" in j.get("message", ""), j.get("message"))
        check("notified = 2", j.get("notified") == 2, j)
    with Env(email="off"), Fakes(mod) as f:
        r = client.post("/api/admin/grammar-drill/create", json=body, headers=cron)
        j = r.json() if r.status_code == 200 else {}
        check("off: 200・LINE 0・メール 0", r.status_code == 200 and f.lines == [] and f.mails == [], (r.status_code, f.lines, f.mails))
        check("off: notify_channels はどちらも False・notified 0", j.get("notify_channels") == {"line": False, "email": False}
              and j.get("notified") == 0, j)
        check("off: message は「アプリに表示」「LINE・メールは送っていません」", "🆕 新しい宿題" in j.get("message", "")
              and "送っていません" in j.get("message", ""), j.get("message"))
    with Env(), Fakes(mod) as f:
        r = client.post("/api/admin/grammar-drill/create", json=dict(body, student_ids=[999999]), headers=cron)
        j = r.json() if r.status_code == 200 else {}
        check("配った生徒が 0 名なら「新しく配った生徒はいません」・メールも 0", r.status_code == 200 and f.mails == []
              and "新しく配った生徒はいません" in j.get("message", ""), (r.status_code, j.get("message"), f.mails))
    check("message の文は _drill_create_message の 1 か所 (D6 の習熟度テストも使う)",
          "名に配信し、LINE/メールで通知を送信しました" not in src and "def _drill_create_message(" in src
          and '"message": _drill_create_message(len(assigned), title, sent_ch, already_taken=len(already_taken))' in src)
    check("_drill_create_message: LINE の非常スイッチの文", "LINE・メールでお知らせ" in mod._drill_create_message(3, "x", {"line": True, "email": True})
          and "LINEでお知らせ" in mod._drill_create_message(3, "x", {"line": True, "email": False}))

    print("[5] 3日ドリル (_run_weakness_drill_routine) は source='auto'")
    with Env(), Fakes(mod) as f:
        dry = mod._run_weakness_drill_routine(only_student_id=sid_rt, dry_run=True)
        check("dry_run の summary に notify = {line: False, email: False}", dry.get("notify") == {"line": False, "email": False}, dry)
        res = mod._run_weakness_drill_routine(only_student_id=sid_rt)
        check("既定: 1 名に配る", res.get("delivered") == 1, res)
        check("既定: LINE 0・メール 0・待ち (sleep) 0", f.lines == [] and f.mails == [] and f.sleeps == [], (f.lines, f.mails, f.sleeps))
        check("summary.notify = {line: False, email: False}", res.get("notify") == {"line": False, "email": False}, res)
    with Env(email="all"), Fakes(mod) as f:
        res = mod._run_weakness_drill_routine(only_student_id=sid_rt2)
        check("HOMEWORK_NOTIFY_EMAIL=all: 3日ドリルでもメール 1 通 (LINE は 0)",
              res.get("delivered") == 1 and len(f.mails) == 1 and f.lines == [], (res, f.mails, f.lines))
        check("all のメールは mypage.html?focus=homework (AIあり)", f.mails and f"{BASE}/mypage.html?focus=homework" in f.mails[0]["body"],
              f.mails)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) AS n FROM notifications WHERE template = 'grammar_drill_assigned'")
    check("notifications に grammar_drill_assigned の行が 1 行も無い", c.fetchone()["n"] == 0)
    conn.close()

    print("[6] GET /api/student/grammar-drills (未提出 = completed 以外・self_issued)")
    conn = mod.db(); c = conn.cursor()
    sid6 = sid_noai   # AIなし枠 (許可集合の EXACT /api/student/grammar-drills)

    def drill(title, created_by, status, assigned_at):
        c.execute("INSERT INTO grammar_drills (subject, title, unit, level, question_ids, created_by) "
                  "VALUES ('english', ?, '時制', 'standard', '[]', ?) RETURNING id", (title, created_by))
        did = c.fetchone()["id"]
        c.execute("INSERT INTO grammar_drill_assignments (drill_id, student_id, status, score_total, assigned_at) "
                  "VALUES (?, ?, ?, 10, ?)", (did, sid6, status, assigned_at))
        return did

    c.execute("DELETE FROM grammar_drill_assignments WHERE student_id = ?", (sid6,))
    d_done = drill("完了したドリル", "admin", "completed", "2026-10-14 01:00:00")
    d_assigned = drill("予約タスクのドリル", "admin", "assigned", "2026-10-10 01:00:00")
    d_today = drill("📝 今日の1問", "today_question", "open", "2026-10-13 01:00:00")
    d_diag = drill("診断", "diagnostic", "open", "2026-10-12 01:00:00")
    conn.commit(); conn.close()
    mod._RATE_LIMIT_STORE.clear()
    r = client.get("/api/student/grammar-drills", headers={"Authorization": "Bearer " + student_token(mod, sid6)})
    j = r.json() if r.status_code == 200 else {}
    items = j.get("items") or []
    ids = [it["drill_id"] for it in items]
    by = {it["drill_id"]: it for it in items}
    check("AIなし枠の生徒でも 200", r.status_code == 200, (r.status_code, r.text[:200]))
    check("status='assigned' (デスクトップの予約タスク) も未提出に数える: summary.open = 3",
          (j.get("summary") or {}).get("open") == 3 and (j.get("summary") or {}).get("completed") == 1, j.get("summary"))
    check("未提出 ('assigned' を含む) が完了より先に並ぶ", ids and ids[-1] == d_done and d_assigned in ids[:-1], ids)
    check("今日の1問・診断は self_issued: true、塾長の配信は false",
          by.get(d_today, {}).get("self_issued") is True and by.get(d_diag, {}).get("self_issued") is True
          and by.get(d_assigned, {}).get("self_issued") is False and by.get(d_done, {}).get("self_issued") is False,
          {k: v.get("self_issued") for k, v in by.items()})
    check("created_by の生の値は返さない", all("created_by" not in it for it in items))
    fn = src[src.index("def _line_build_todo_text("):][:2500]
    check("LINE「やること」の未提出の数え方も completed 以外", "status = 'open'" not in fn and fn.count("status <> 'completed'") == 2)

    print("[7] 変えないもの")
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT * FROM students WHERE id = ?", (sid_ai,))
    row = c.fetchone()
    conn.close()
    with Env(), Fakes(mod) as f:
        ok = mod._try_line_login_push(row, f"{BASE}/login?t=x", "123456")
        check("ログインコードの LINE (magic_link_login) は既定でも送る (HOMEWORK_NOTIFY_LINE と無関係)",
              ok is True and len(f.lines) == 1 and f.lines[0][1] == "magic_link_login", f.lines)
    lp = src[src.index("def _try_line_login_push("):][:1200]
    check("_try_line_login_push は _do_line_push(..., \"magic_link_login\", ...) のまま",
          '_do_line_push(int(row["id"]), "magic_link_login"' in lp and "_homework_notify_channels" not in lp)
    check("AIなし枠の EXACT 許可集合は不変", set(mod._AI_DISABLED_ALLOWED_EXACT) == {
        "/api/student/homework", "/api/student/grammar-drills", "/api/messages/me", "/api/student/messages/send"})
    check("AIなし枠の PREFIX 許可集合は不変", tuple(mod._AI_DISABLED_ALLOWED_PREFIXES) == (
        "/api/student/class/", "/api/student/homework/", "/api/student/grammar-drill/", "/api/messages/me/", "/api/auth/", "/api/admin/"))
    calls = [m.start() for m in re.finditer(r"_notify_grammar_drill_assigned\b", src)]
    bad = []
    for pos in calls:
        line = src[src.rfind("\n", 0, pos) + 1:src.find("\n", pos)]
        if line.lstrip().startswith(("def ", "#")) or "_notify_grammar_drill_assigned を" in line:
            continue
        call = src[pos:src.find(")", pos) + 1]
        if not ('"manual"' in call or "source=" in call):
            bad.append(call)
    check("_notify_grammar_drill_assigned の呼び出しはすべて source を明示する ('manual' か source=)", calls and not bad, bad)
    check("'manual' で呼ぶのは CEO の配信 (grammar-drill/create) だけ",
          src.count('_notify_grammar_drill_assigned, notify_list, unit, count, subject, "manual"') == 1
          and src.count('source="manual"') == 0)

    print()
    if FAILURES:
        print(f"❌ FAIL ({len(FAILURES)} 件)")
        for f_ in FAILURES:
            print("   -", f_)
        sys.exit(1)
    print("✅ PASS")


if __name__ == "__main__":
    main()
