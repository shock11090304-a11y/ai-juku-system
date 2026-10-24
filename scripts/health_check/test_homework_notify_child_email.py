#!/usr/bin/env python3
"""🧒 宿題・プリントのお知らせメールを確認済みの子メール (student_email) にも送る (2026-10-24 塾長「はい」)。

背景: 保護者から「弱点プリントの送信先を変えてほしい。母のアドレスに来ていて、子供にも届いていると思っていたが
  届いていなかった」。宿題・ドリルのお知らせ (_notify_grammar_drill_assigned) と週次弱点プリント (既定で停止中) の
  メールは students.email (保護者) だけ宛だった。子メールを登録しても子には届かない。
  → ログインコードと同じ条件の子メール (確認済み・保護者と別・他家庭の保護者メールと別) にも、同じ文面で送る。

固定する性質 (一時 SQLite・外部通信なし・メールは偽物):
  [1] 確認済みの子メールがある → 保護者・子の順に 2 通 (同じ件名・本文・生徒名で呼びかけ)・child_mail_ok=1
  [2] 子メールが無い / 未確認 / 保護者と同じ (大文字小文字違い) / 他の生徒の保護者メールと同じ → 保護者 1 通だけ (今までどおり)
  [3] 2 通目からは 1.5 秒あける (Resend の上限)・子宛が失敗したら mail_fail に数え、保護者宛の成功は残す
  [4] source='auto' (既定の HOMEWORK_NOTIFY_EMAIL=manual) は今までどおり 0 通・子メールの照会もしない
  [5] 子メールを読めない (DB 障害) → 保護者宛だけ送る (子宛を増やさない側に倒す)
  [6] 週次弱点プリント (既定で停止) も同じ照会 (_homework_child_emails) で子に送る (ソース検査)

実行:
    python3 scripts/health_check/test_homework_notify_child_email.py
    # exit 0 = PASS / 1 = FAIL
"""
import datetime
import importlib.util
import os
import re
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="hw_child_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        "DATABASE_URL": "",   # ★空にしないと本番 Postgres に書き込む
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
        "BASE_URL": "https://example.invalid",
        "CRON_SECRET": "test-cron-secret",
    })
    for k in ("HOMEWORK_NOTIFY_EMAIL", "HOMEWORK_NOTIFY_LINE"):
        os.environ.pop(k, None)
    spec = importlib.util.spec_from_file_location("aijuku_main_hw_child", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


class Fakes:
    """_send_message_email / time.sleep を記録する偽物。fail_to に入れた宛先だけ失敗させる。"""

    def __init__(self, mod, fail_to=()):
        self.mod, self.fail_to = mod, {a.lower() for a in fail_to}
        self.mails, self.sleeps = [], []

    def __enter__(self):
        m = self.mod
        self.orig = (m._send_message_email, time.sleep)

        def fake_mail(to, subj, body, student_name=None):
            self.mails.append((to, subj, body, student_name))
            if to.lower() in self.fail_to:
                return {"sent": False, "error": "boom"}
            return {"sent": True}
        m._send_message_email = fake_mail
        time.sleep = lambda s: self.sleeps.append(s)
        return self

    def __exit__(self, *a):
        self.mod._send_message_email, time.sleep = self.orig


def main():
    print("🧒 宿題・プリントのお知らせを子メールにも 回帰テスト\n")
    mod = load_main()
    te = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)).isoformat()
    conn = mod.db(); c = conn.cursor()

    def make(name, email, child=None, verified=1):
        c.execute(
            "INSERT INTO students (name, email, status, trial_end, course, grade, goal, student_email, student_email_verified) "
            "VALUES (?, ?, 'trial', ?, 'kokuritsu_nankan', '高校2年', '国公立大学', ?, ?)",
            (name, email, te, child, verified),
        )
        c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
        return c.fetchone()["id"]

    # 架空の家庭 (個人情報は使わない)
    s_ok = make("架空 生徒A", "parent-a@example.org", "child-a@example.org", 1)
    s_unv = make("架空 生徒B", "parent-b@example.org", "child-b@example.org", 0)
    s_same = make("架空 生徒C", "parent-c@example.org", "PARENT-C@example.org", 1)
    s_none = make("架空 生徒D", "parent-d@example.org", None, 0)
    s_other = make("架空 生徒E", "parent-e@example.org", "parent-d@example.org", 1)  # 子メール = 他家庭の保護者メール
    conn.commit(); conn.close()
    mod._AI_DISABLED_CACHE.clear()

    def entry(sid, email, name):
        return {"id": sid, "name": name, "email": email, "line_user_id": None}

    print("[1] 確認済みの子メール → 保護者と子に 1 通ずつ")
    with Fakes(mod) as f:
        r = mod._notify_grammar_drill_assigned([entry(s_ok, "parent-a@example.org", "架空 生徒A")], "時制", 10, "english", "manual")
    tos = [m[0] for m in f.mails]
    check("保護者 → 子の順に 2 通", tos == ["parent-a@example.org", "child-a@example.org"], tos)
    check("同じ件名・本文・生徒名", len(f.mails) == 2 and f.mails[0][1:] == f.mails[1][1:], f.mails)
    check("件名は「新しい…の宿題」", f.mails and "宿題「時制」" in f.mails[0][1], f.mails[:1])
    check("mail_ok=2・child_mail_ok=1・mail_fail=0", r.get("mail_ok") == 2 and r.get("child_mail_ok") == 1 and r.get("mail_fail") == 0, r)
    check("2 通目の前に 1.5 秒あける", f.sleeps == [1.5], f.sleeps)

    print("\n[2] 子メールに送らない家庭は保護者 1 通だけ (今までどおり)")
    for sid, email, label in ((s_unv, "parent-b@example.org", "未確認の子メール"),
                              (s_same, "parent-c@example.org", "子メール = 保護者 (大文字小文字違い)"),
                              (s_none, "parent-d@example.org", "子メールなし"),
                              (s_other, "parent-e@example.org", "子メール = 他家庭の保護者メール")):
        with Fakes(mod) as f:
            r = mod._notify_grammar_drill_assigned([entry(sid, email, "架空")], "時制", 10, "english", "manual")
        check(f"{label}: 保護者に 1 通だけ", [m[0] for m in f.mails] == [email] and r.get("child_mail_ok") == 0, f.mails)
    kids = mod._homework_child_emails([s_ok, s_unv, s_same, s_none, s_other])
    check("_homework_child_emails は確認済み・別アドレス・衝突なしの 1 件だけ", kids == {s_ok: "child-a@example.org"}, kids)

    print("\n[3] 複数人・子宛の失敗")
    people = [entry(s_ok, "parent-a@example.org", "A"), entry(s_none, "parent-d@example.org", "D")]
    with Fakes(mod, fail_to=["child-a@example.org"]) as f:
        r = mod._notify_grammar_drill_assigned(people, "時制", 10, "english", "manual")
    check("3 通 (A 保護者・A 子・D 保護者)", [m[0] for m in f.mails] == ["parent-a@example.org", "child-a@example.org", "parent-d@example.org"], f.mails)
    check("2 通目から 1.5 秒ずつ", f.sleeps == [1.5, 1.5], f.sleeps)
    check("子宛の失敗は mail_fail・保護者宛の成功は残る", r.get("mail_ok") == 2 and r.get("mail_fail") == 1 and r.get("child_mail_ok") == 0, r)

    print("\n[4] 自動配信 (source='auto'・既定) は今までどおり 0 通・子メールも照会しない")
    calls = []
    orig = mod._homework_child_emails
    mod._homework_child_emails = lambda ids: (calls.append(ids) or orig(ids))
    try:
        with Fakes(mod) as f:
            r = mod._notify_grammar_drill_assigned(people, "時制", 10, "english", "auto")
        check("0 通・待ちなし", f.mails == [] and f.sleeps == [], (f.mails, f.sleeps))
        check("子メールの照会をしない", calls == [], calls)
        os.environ["HOMEWORK_NOTIFY_EMAIL"] = "all"
        try:
            with Fakes(mod) as f:
                mod._notify_grammar_drill_assigned(people, "時制", 10, "english", "auto")
            check("HOMEWORK_NOTIFY_EMAIL=all の自動配信は子にも届く (塾長の手配りと同じ)",
                  "child-a@example.org" in [m[0] for m in f.mails], f.mails)
        finally:
            os.environ.pop("HOMEWORK_NOTIFY_EMAIL", None)
    finally:
        mod._homework_child_emails = orig

    print("\n[5] 子メールを読めないとき → 保護者宛だけ")
    orig_db = mod.db

    def broken_db():
        raise RuntimeError("db down")
    mod.db = broken_db
    try:
        check("照会は {} を返す (例外にしない)", mod._homework_child_emails([s_ok]) == {})
    finally:
        mod.db = orig_db
    orig = mod._homework_child_emails
    mod._homework_child_emails = lambda ids: {}
    try:
        with Fakes(mod) as f:
            mod._notify_grammar_drill_assigned([entry(s_ok, "parent-a@example.org", "A")], "時制", 10, "english", "manual")
        check("保護者に 1 通だけ", [m[0] for m in f.mails] == ["parent-a@example.org"], f.mails)
    finally:
        mod._homework_child_emails = orig

    print("\n[6] 週次弱点プリント (既定で停止) も子に送る (ソース検査)")
    src = open(MAIN_PY, encoding="utf-8").read()
    fn = src[src.index("def _run_weekly_worksheet_generation"):]
    fn = fn[:fn.index("\ndef ", 10)]
    check("生徒一覧を読んだ後に _homework_child_emails で子メールを 1 回で引く", "_ws_children = _homework_child_emails(" in fn)
    check("保護者宛の後に子宛を同じ件名・本文で送る",
          re.search(r"_send_monitor_email\(subj, body_html, to_email=_child_to\)", fn) is not None)
    check("子宛が保護者と同じアドレスなら送らない", "_child_to.lower() != semail.lower()" in fn)
    blk = fn[fn.index("_child_to = _ws_children.get("):]
    blk = blk[:blk.index("_send_monitor_email(subj, body_html, to_email=_child_to)")]
    check("子宛の前に 1.5 秒あける (保護者宛の直後に続けて送らない)", "time.sleep(1.5)" in blk)
    check("子宛が送れなかったら生徒 ID つきで警告を残す", "[WeeklyWorksheet] child email not sent sid=" in fn)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for x in FAILURES:
            print("  -", x)
        sys.exit(1)
    print("✅ PASS")


if __name__ == "__main__":
    main()
