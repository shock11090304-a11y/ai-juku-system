#!/usr/bin/env python3
"""🔏 生徒削除の個人情報後始末 (2026-09-07) の回帰テスト (in-process・一時 SQLite)。

システム点検で「削除しても氏名・メールが監査記録・ログ・申込履歴・問い合わせ・招待コードに残り、塾長コメントは
孤児化する」と確定した点を直した。
  1. 削除 API の監査 events (admin_student_deleted) に name / email が入らず、email_hash が入る
  2. course_applications は氏名/電話/メモも匿名化 (student_id NULL + メール匿名化は従来どおり)
  3. support_tickets / invite_codes (メールで紐づく) が匿名化される
  4. 学習記録の塾長コメント (study_log_reactions) が孤児化せず消える
  5. Stripe 顧客が付いていた生徒なら、レスポンスに「Stripe 側は残る」注記が出る
  6. cascade 4 リストの機械検査 (check_student_cascade_lists.py) が通る
"""
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

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="privacy_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_privacy", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def admin_token(mod):
    exp = int(time.time()) + 3600
    payload = mod._admin_token_payload(str(exp))
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


def insert_generic(c, table, values: dict):
    """NOT NULL でデフォルトの無い列にダミーを入れつつ INSERT (テーブル定義の細部に依存しない)。"""
    c.execute(f"PRAGMA table_info({table})")
    cols = c.fetchall()
    row = dict(values)
    for col in cols:
        name, ctype, notnull, dflt, pk = col[1], (col[2] or "").upper(), col[3], col[4], col[5]
        if pk or name in row or not notnull or dflt is not None:
            continue
        row[name] = 0 if ("INT" in ctype or "REAL" in ctype) else "x"
    keys = list(row.keys())
    c.execute(f"INSERT INTO {table} ({', '.join(keys)}) VALUES ({', '.join('?' * len(keys))})", tuple(row[k] for k in keys))


def main():
    print("🔏 生徒削除の個人情報後始末 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    email = "delete-me@example.org"
    conn = mod.db(); c = conn.cursor()
    far = (datetime.datetime.utcnow() + datetime.timedelta(days=365)).isoformat()
    c.execute("INSERT INTO students (name, email, status, plan, trial_end, stripe_customer_id) VALUES (?,?,?,?,?,?)",
              ("Delete Me", email, "paid", "premium", far, "cus_test_del"))
    conn.commit(); c.execute("SELECT id FROM students WHERE email = ?", (email,)); sid = c.fetchone()["id"]
    insert_generic(c, "course_applications", {"student_id": sid, "name": "Delete Me", "email": email, "phone": "090-0000-0000", "note": "秘密のメモ"})
    insert_generic(c, "support_tickets", {"name": "Delete Me", "email": email, "message": "困っています"})
    insert_generic(c, "invite_codes", {"email": email, "code": "INVITE-TEST-1"})
    c.execute("INSERT INTO study_logs (student_id, studied_date, subject, minutes) VALUES (?,?,?,?)", (sid, datetime.date.today().isoformat(), "英語", 30))
    c.execute("SELECT id FROM study_logs WHERE student_id = ?", (sid,)); log_id = c.fetchone()["id"]
    c.execute("INSERT INTO study_log_reactions (log_id, actor_type, actor_id, kind, comment) VALUES (?,?,?,?,?)", (log_id, "admin", None, "comment", "いいね"))
    conn.commit(); conn.close()

    r = client.post(f"/api/admin/students/{sid}/delete", json={"confirm_email": email, "dry_run": False, "cancel_stripe": False}, headers=adm)
    check("削除 API が 200", r.status_code == 200, f"{r.status_code} {r.text[:200]}")
    body = r.json() if r.status_code == 200 else {}
    check("レスポンスに Stripe 側が残る注記", bool(body.get("stripe_note")), body)

    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) AS n FROM students WHERE id = ?", (sid,)); check("生徒本体は消える", c.fetchone()["n"] == 0)
    c.execute("SELECT props FROM events WHERE name = 'admin_student_deleted' ORDER BY id DESC LIMIT 1")
    props = json.loads(c.fetchone()["props"])
    check("監査記録に name / email が無い", "name" not in props and "email" not in props and "Delete Me" not in json.dumps(props, ensure_ascii=False) and email not in json.dumps(props), props)
    check("監査記録に email_hash がある", props.get("email_hash") == mod._student_email_hash(email), props.get("email_hash"))
    c.execute("SELECT name, email, phone, note, student_id FROM course_applications")
    ca = [dict(x) for x in c.fetchall()]
    check("申込履歴は氏名/電話/メモも匿名化 (行は残る)", len(ca) == 1 and ca[0]["name"] == "削除済み" and ca[0]["phone"] is None and ca[0]["note"] is None and email not in (ca[0]["email"] or "") and ca[0]["student_id"] is None, ca)
    c.execute("SELECT name, email, message FROM support_tickets")
    st = [dict(x) for x in c.fetchall()]
    check("問い合わせは氏名/メール/本文が匿名化", len(st) == 1 and st[0]["name"] == "削除済み" and email not in st[0]["email"] and "困って" not in st[0]["message"], st)
    c.execute("SELECT email FROM invite_codes")
    ic = [dict(x) for x in c.fetchall()]
    check("招待コードのメールが匿名化", len(ic) == 1 and email not in (ic[0]["email"] or ""), ic)
    c.execute("SELECT COUNT(*) AS n FROM study_log_reactions"); check("塾長コメント (study_log_reactions) が孤児化せず消える", c.fetchone()["n"] == 0)
    c.execute("SELECT COUNT(*) AS n FROM study_logs WHERE student_id = ?", (sid,)); check("学習記録も消える", c.fetchone()["n"] == 0)
    conn.close()
    src = open(MAIN_PY, encoding="utf-8").read()
    fn = src[src.index("def admin_student_delete("):][:20000]
    check("削除ログに氏名/メールを出さない", "name={student['name']}" not in fn and "email={student['email']}" not in fn)
    pg = src[src.index("def admin_students_purge_stale("):][:12000]
    check("purge の監査記録も氏名/メールを落とす", '"email_hash": _student_email_hash(m.get("email")' in pg and "support_tickets" in pg and "study_log_reactions" in pg)

    print("6) cascade 4 リストの機械検査")
    rc = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "health_check", "check_student_cascade_lists.py")], capture_output=True, text=True)
    check("check_student_cascade_lists.py が通る", rc.returncode == 0, rc.stdout[-300:] + rc.stderr[-300:])

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
