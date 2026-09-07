#!/usr/bin/env python3
"""🤝 生徒アカウント統合 API (POST /api/admin/students/{keep}/merge・2026-09-08) の回帰テスト (in-process・一時 SQLite)。

  1. dry_run: 件数と予定の変更だけ返し、何も書かない
  2. 実行: student_id を持つ表の行が keep に付け替わる。同じキーで衝突する行は keep 優先 (student_json_state は新しい方)
  3. messages / events(session_id) / course_applications も付け替え
  4. students 本体: 空欄を drop 側で埋める・受講クラスは和集合・AI は片方で使えれば使える・drop のメールは student_email (確認済)
  5. drop 側は削除され、監査 event が残る。もう一度呼ぶと 404
  6. 同じ生徒を指定すると 400
"""
import importlib.util
import json
import os
import sys
import tempfile
import time
import base64, hashlib, hmac

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="merge_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_merge", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def admin_token(mod, hours=1):
    exp = int(time.time()) + hours * 3600
    payload = mod._admin_token_payload(str(exp))
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


def insert_generic(c, table, values):
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


def count(c, sql, *params):
    c.execute(sql, params)
    r = c.fetchone()
    return int((r[0] if not hasattr(r, "keys") else list(r)[0]) or 0)


def main():
    print("🤝 生徒アカウント統合 API 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    conn = mod.db(); c = conn.cursor()
    far = "2036-01-01T00:00:00"
    c.execute("INSERT INTO students (name, email, status, plan, trial_end, course, grade, goal, class_labels, ai_disabled, created_at, last_login_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
              ("統合 花子", "parent@example.org", "trial", None, far, "kokuritsu_nankan", None, None, json.dumps(["金曜2限 英検2級対策"]), 1, "2026-09-01 10:00:00", "2026-09-04 09:00:00"))
    c.execute("SELECT id FROM students WHERE email = ?", ("parent@example.org",)); keep = c.fetchone()["id"]
    c.execute("INSERT INTO students (name, email, status, plan, trial_end, course, grade, goal, class_labels, ai_disabled, created_at, last_login_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
              ("統合 花子", "student@example.org", "trial", None, far, "kokuritsu_nankan", "高2", "まだ未定", json.dumps(["金曜2限 英検2級対策", "月曜1限 中学応用"]), 0, "2026-09-04 12:00:00", "2026-09-05 13:00:00"))
    c.execute("SELECT id FROM students WHERE email = ?", ("student@example.org",)); drop = c.fetchone()["id"]
    # 学習データ (drop 側に多く、keep 側にも少し)
    for i in range(3):
        c.execute("INSERT INTO study_logs (student_id, studied_date, subject, minutes) VALUES (?,?,?,?)", (drop, f"2026-09-0{i+1}", "英語", 30))
    c.execute("INSERT INTO study_logs (student_id, studied_date, subject, minutes) VALUES (?,?,?,?)", (keep, "2026-09-02", "数学", 20))
    c.execute("INSERT INTO question_attempts (student_id, source, subject, topic, is_correct, created_at) VALUES (?,?,?,?,?,?)", (drop, "practice", "english", "時制", 1, "2026-09-03 10:00:00"))
    insert_generic(c, "student_weakness", {"student_id": keep, "subject": "english", "topic": "時制"})
    insert_generic(c, "student_weakness", {"student_id": drop, "subject": "english", "topic": "時制"})   # 衝突 → drop 側を捨てる
    insert_generic(c, "student_weakness", {"student_id": drop, "subject": "math", "topic": "二次関数"})  # 移動
    insert_generic(c, "admission_likelihood", {"student_id": keep, "score": 40})
    insert_generic(c, "admission_likelihood", {"student_id": drop, "score": 55})                       # 衝突 → keep 優先
    c.execute("INSERT INTO student_json_state (student_id, kind, payload, updated_at) VALUES (?,?,?,?)", (keep, "vocab", '{"v":"old"}', "2026-09-01 00:00:00"))
    c.execute("INSERT INTO student_json_state (student_id, kind, payload, updated_at) VALUES (?,?,?,?)", (drop, "vocab", '{"v":"new"}', "2026-09-05 00:00:00"))   # 新しい方が残る
    c.execute("INSERT INTO student_json_state (student_id, kind, payload, updated_at) VALUES (?,?,?,?)", (drop, "plan", '{"p":1}', "2026-09-05 00:00:00"))
    insert_generic(c, "class_attend", {"student_id": keep, "class_label": "金曜2限 英検2級対策", "att_date": "2026-09-05"})
    insert_generic(c, "class_attend", {"student_id": drop, "class_label": "金曜2限 英検2級対策", "att_date": "2026-09-05"})  # 衝突
    insert_generic(c, "class_attend", {"student_id": drop, "class_label": "金曜2限 英検2級対策", "att_date": "2026-08-29"})  # 移動
    insert_generic(c, "messages", {"sender_type": "student", "sender_id": drop, "recipient_type": "admin", "recipient_id": 0, "subject": "q", "body": "質問"})
    insert_generic(c, "messages", {"sender_type": "admin", "sender_id": 0, "recipient_type": "student", "recipient_id": drop, "subject": "a", "body": "回答"})
    c.execute("INSERT INTO events (name, props, session_id) VALUES (?,?,?)", ("activity_mypage_view", "{}", str(drop)))
    c.execute("INSERT INTO course_applications (name, email, referrer, status, student_id) VALUES (?,?,?,?,?)", ("統合 花子", "student@example.org", "塾生アプリ", "approved", drop))
    conn.commit(); conn.close()

    print("1) dry_run")
    r = client.post(f"/api/admin/students/{keep}/merge", json={"from_id": drop, "dry_run": True}, headers=adm)
    check("200", r.status_code == 200, r.text[:200])
    j = r.json() if r.status_code == 200 else {}
    check("移動件数: study_logs 3 / question_attempts 1 / student_weakness 1 / class_attend 1 / messages 1+1 / events 1 / course_applications 1",
          j.get("moved", {}).get("study_logs") == 3 and j["moved"].get("question_attempts") == 1 and j["moved"].get("student_weakness") == 1
          and j["moved"].get("class_attend") == 1 and j["moved"].get("messages(sender)") == 1 and j["moved"].get("messages(recipient)") == 1
          and j["moved"].get("events") == 1 and j["moved"].get("course_applications") == 1 and j["moved"].get("student_json_state") == 1, j.get("moved"))
    check("衝突: student_weakness 1 / admission_likelihood 1 / class_attend 1 / student_json_state 1",
          j.get("conflicts", {}).get("student_weakness") == 1 and j["conflicts"].get("admission_likelihood") == 1 and j["conflicts"].get("class_attend") == 1 and j["conflicts"].get("student_json_state") == 1, j.get("conflicts"))
    fc = j.get("field_changes", {})
    check("予定の変更: 学年・志望校を埋める / 受講クラス和集合 / AI 使える / student_email に drop のメール (確認済) / last_login は遅い方",
          fc.get("grade") == "高2" and fc.get("goal") == "まだ未定" and "月曜1限 中学応用" in (fc.get("class_labels") or "") and fc.get("ai_disabled") == 0
          and str(fc.get("student_email", "")).startswith("st") and fc.get("student_email_verified") == 1 and fc.get("last_login_at") == "2026-09-05 13:00:00", fc)
    conn = mod.db(); c = conn.cursor()
    check("dry_run は何も書かない (drop が残っている・study_logs も元のまま)", count(c, "SELECT COUNT(*) FROM students WHERE id = ?", drop) == 1 and count(c, "SELECT COUNT(*) FROM study_logs WHERE student_id = ?", drop) == 3)
    conn.close()

    print("2) 実行")
    r = client.post(f"/api/admin/students/{keep}/merge", json={"from_id": drop, "dry_run": False}, headers=adm)
    check("200", r.status_code == 200, r.text[:200])
    conn = mod.db(); c = conn.cursor()
    check("drop 側の生徒は削除", count(c, "SELECT COUNT(*) FROM students WHERE id = ?", drop) == 0)
    check("study_logs は keep に 4 件", count(c, "SELECT COUNT(*) FROM study_logs WHERE student_id = ?", keep) == 4)
    check("question_attempts 移動", count(c, "SELECT COUNT(*) FROM question_attempts WHERE student_id = ?", keep) == 1)
    c.execute("SELECT subject, topic FROM student_weakness WHERE student_id = ? ORDER BY subject", (keep,)); w = [(r["subject"], r["topic"]) for r in c.fetchall()]
    check("student_weakness: 衝突 1 件は keep 優先・別単元は移動 (2 行)", w == [("english", "時制"), ("math", "二次関数")], w)
    c.execute("SELECT score FROM admission_likelihood WHERE student_id = ?", (keep,)); a = [r["score"] for r in c.fetchall()]
    check("admission_likelihood は keep の 1 行 (score 40)", a == [40], a)
    c.execute("SELECT kind, payload FROM student_json_state WHERE student_id = ? ORDER BY kind", (keep,)); js = {r["kind"]: r["payload"] for r in c.fetchall()}
    check("student_json_state: vocab は新しい方 (drop)・plan は移動", js.get("vocab") == '{"v":"new"}' and js.get("plan") == '{"p":1}', js)
    check("class_attend: 衝突を除いて 2 行", count(c, "SELECT COUNT(*) FROM class_attend WHERE student_id = ?", keep) == 2)
    check("messages 双方向", count(c, "SELECT COUNT(*) FROM messages WHERE sender_type='student' AND sender_id = ?", keep) == 1 and count(c, "SELECT COUNT(*) FROM messages WHERE recipient_type='student' AND recipient_id = ?", keep) == 1)
    check("events の session_id", count(c, "SELECT COUNT(*) FROM events WHERE session_id = ? AND name = 'activity_mypage_view'", str(keep)) == 1)
    check("course_applications の student_id", count(c, "SELECT COUNT(*) FROM course_applications WHERE student_id = ?", keep) == 1)
    c.execute("SELECT grade, goal, class_labels, ai_disabled, student_email, student_email_verified, email, created_at, last_login_at FROM students WHERE id = ?", (keep,)); s = dict(c.fetchone())
    check("students 本体: 学年/志望校/クラス和集合/AI/確認済み student_email/created_at は早い方", s["grade"] == "高2" and s["goal"] == "まだ未定" and set(json.loads(s["class_labels"])) == {"金曜2限 英検2級対策", "月曜1限 中学応用"}
          and int(s["ai_disabled"]) == 0 and s["student_email"] == "student@example.org" and int(s["student_email_verified"]) == 1 and s["email"] == "parent@example.org" and str(s["created_at"]).startswith("2026-09-01"), s)
    check("監査 event", count(c, "SELECT COUNT(*) FROM events WHERE name = 'admin_student_merge'") == 1)
    conn.close()
    check("もう一度呼ぶと 404", client.post(f"/api/admin/students/{keep}/merge", json={"from_id": drop, "dry_run": True}, headers=adm).status_code == 404)
    check("同じ生徒は 400", client.post(f"/api/admin/students/{keep}/merge", json={"from_id": keep, "dry_run": True}, headers=adm).status_code == 400)
    check("未認証は 401", client.post(f"/api/admin/students/{keep}/merge", json={"from_id": 1, "dry_run": True}).status_code == 401)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
