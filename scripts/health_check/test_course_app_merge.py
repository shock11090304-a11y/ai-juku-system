#!/usr/bin/env python3
"""🤝 同一生徒の申込まとめ承認 (2026-09-07) の回帰テスト (in-process・一時 SQLite・本番に触れない)。

入塾申込フォーム (STEP1, referrer='入塾申込フォーム') → 塾生アプリ登録 (STEP2, referrer='塾生アプリ') は
同じ生徒から course_applications が 2 行届く設計。従来は 1 行ずつ承認するしかなく、
  - 2 回目は同一メールで既存生徒に合流するが AI 可否は 1 回目で固定 (承認順で結果が逆になる)
  - 案内メール・LINE 連携コードが 2 通ずつ届く
  - 片方を却下すると受講クラス (アプリ側) や電話・保護者情報 (フォーム側) が欠ける
だったのを、同じメール + 同じ氏名 (正規化) の pending 行を 1 回の承認でまとめて処理するようにした。
  1. 2 行とも作られる (現行の重複判定は referrer 違いを通す) / 一覧に group_key が付く
  2. 塾生アプリ行を承認 (AIあり指定) → 生徒 1 人・両行 approved・受講クラスは和集合・メール 1 通・LINE コード 1 個
  3. 逆順 (フォーム行を承認・AIなし) でも同じ結果。学年・志望校はフォーム行を優先
  4. 同じメールで氏名が違う (兄弟) 行は触らない
  5. 単独行の承認は従来どおり (merged_count=0・既存キー健在)
  6. 画面側 (ceo.js の束ね表示 / juku-register.html の引き継ぎ) のソース検査
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
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="camerge_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_camerge", MAIN_PY)
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


def apply(client, **body):
    r = client.post("/api/course-applications", json=body)
    return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else {})


def app_rows(mod, email):
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT id, name, status, student_id, approved_by, referrer FROM course_applications WHERE LOWER(email) = ? ORDER BY id", (email,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def student_rows(mod, email):
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT id, name, grade, goal, class_labels, ai_disabled FROM students WHERE LOWER(email) = ?", (email,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def main():
    print("🤝 同一生徒の申込まとめ承認 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    sent, line = [], []
    mod._send_message_email = lambda to, subject, body, **kw: (sent.append((to, subject, body)) or {"sent": True})
    mod._create_line_link_token = lambda sid: (line.append(sid) or "LINE-TEST-CODE")
    course = list(mod._COURSE_CLASSES)[0]
    course_labels = list(mod._COURSE_CLASSES[course])
    extra_label = sorted(l for l in mod._TIMETABLE_LABELS if l not in course_labels)[0]

    # ------------------------------------------------------------ 1. 2 行できる / group_key
    print("1) STEP1 + STEP2 で 2 行 (現行どおり) と一覧の group_key")
    e1 = "merge-one@example.org"
    st1, j1 = apply(client, name="統合 太郎", email=e1, grade="高校2年", target_university="千葉大学 教育学部", phone="0470000000",
                    referrer="入塾申込フォーム", note="■受講コース: 英検準1級対策(8,500円)\n■保護者: テスト 父", subjects=course)
    check("入塾申込フォームの行 (200)", st1 == 200, (st1, j1))
    st2, j2 = apply(client, name="統合太郎", email=e1, grade="高2", referrer="塾生アプリ", subjects=extra_label, note="よろしくお願いします")
    check("塾生アプリの行も 200 (referrer 違いは通す・従来どおり)", st2 == 200, (st2, j2))
    form_id, app_id = j1.get("application_id"), j2.get("application_id")
    lst = client.get("/api/admin/course-applications?status=pending&limit=100", headers=adm).json()
    keys = {a["id"]: a.get("group_key") for a in lst.get("applications", [])}
    check("一覧の 2 行が同じ group_key (氏名の空白ゆれを吸収)", keys.get(form_id) and keys.get(form_id) == keys.get(app_id), keys)
    check("pending_count = 2", lst.get("pending_count") == 2, lst.get("pending_count"))

    # ------------------------------------------------------------ 2. 塾生アプリ行を承認 (AIあり)
    print("2) 塾生アプリの行を承認 (AIあり指定) → 1 回で両方処理")
    r = client.post(f"/api/admin/course-applications/{app_id}/approve", json={"ai_disabled": False}, headers=adm)
    check("承認 200", r.status_code == 200, r.text[:200])
    j = r.json() if r.status_code == 200 else {}
    check("merged_count = 1 / merged_application_ids = [フォーム行]", j.get("merged_count") == 1 and j.get("merged_application_ids") == [form_id], j)
    sts = student_rows(mod, e1)
    check("生徒は 1 人だけ", len(sts) == 1, sts)
    sid = sts[0]["id"] if sts else None
    rows = app_rows(mod, e1)
    check("両行 approved・同じ student_id", all(x["status"] == "approved" and x["student_id"] == sid for x in rows), rows)
    check("兄弟行の approved_by は merged:<主行>", any(x["id"] == form_id and (x["approved_by"] or "").startswith("merged:") for x in rows), rows)
    labels = json.loads(sts[0]["class_labels"] or "[]") if sts else []
    check("受講クラス = コース 3 コマ + アプリ側 1 コマ の和集合", set(labels) == set(course_labels + [extra_label]), labels)
    check("AIあり (ai_disabled=0)", sts and (sts[0]["ai_disabled"] or 0) == 0, sts)
    check("学年・志望校はフォーム行を優先", sts and sts[0]["grade"] == "高校2年" and sts[0]["goal"] == "千葉大学 教育学部", sts)
    check("案内メール 1 通・LINE コード 1 個", len(sent) == 1 and len(line) == 1, (len(sent), len(line)))
    body = sent[0][2] if sent else ""
    check("塾生アプリ文面 + AI 学習 (マイページ) の入口も案内", "塾生アプリ" in body and "マイページ" in body, body[:200])
    check("塾生アプリ扱い (is_tsujuku_app)", sid and mod._is_juku_app_student(sid) is True)
    lst = client.get("/api/admin/course-applications?status=pending&limit=100", headers=adm).json()
    check("申込待ちから両方消える (pending_count=0)", lst.get("pending_count") == 0 and not lst.get("applications"), lst)
    r = client.post(f"/api/admin/course-applications/{form_id}/approve", json={"ai_disabled": True}, headers=adm)
    check("処理済みの兄弟行をもう一度承認 → 409", r.status_code == 409, r.text[:120])
    st3, j3 = apply(client, name="統合 太郎", email=e1, referrer="塾生アプリ", subjects=extra_label)
    check("承認後の再登録は 409 (承認済み)", st3 == 409, (st3, j3))

    # ------------------------------------------------------------ 3. 逆順 (フォーム行を承認・AIなし)
    print("3) 入塾申込フォームの行を先に承認 (AIなし) でも同じ")
    sent.clear(); line.clear()
    e2 = "merge-two@example.org"
    st1, j1 = apply(client, name="逆順 花子", email=e2, grade="高校1年", target_university="早稲田大学", referrer="入塾申込フォーム", subjects=extra_label)
    st2, j2 = apply(client, name="逆順　花子", email=e2, grade="高1", target_university="未定", referrer="塾生アプリ", subjects=course)
    check("2 行作成", st1 == 200 and st2 == 200, (st1, st2))
    r = client.post(f"/api/admin/course-applications/{j1['application_id']}/approve", json={"ai_disabled": True}, headers=adm)
    j = r.json() if r.status_code == 200 else {}
    check("承認 200・merged_count = 1", r.status_code == 200 and j.get("merged_count") == 1, (r.status_code, j))
    sts = student_rows(mod, e2)
    labels = json.loads(sts[0]["class_labels"] or "[]") if sts else []
    check("生徒 1 人・受講クラスは和集合・AIなし", len(sts) == 1 and set(labels) == set(course_labels + [extra_label]) and (sts[0]["ai_disabled"] or 0) == 1, (sts, labels))
    check("志望校はフォーム行 (早稲田大学) を優先", sts and sts[0]["goal"] == "早稲田大学", sts)
    check("塾生アプリ扱い (承認順に依らない)", sts and mod._is_juku_app_student(sts[0]["id"]) is True)
    check("案内メール 1 通・LINE コード 1 個", len(sent) == 1 and len(line) == 1, (len(sent), len(line)))
    check("AIなしの文面にマイページ案内は出ない", sent and "マイページ" not in sent[0][2], (sent[0][2][:200] if sent else ""))

    # ------------------------------------------------------------ 4. 兄弟 (同メール・別氏名)
    print("4) 同じ保護者メールで氏名が違う (兄弟) 行は触らない")
    sent.clear(); line.clear()
    e3 = "merge-siblings@example.org"
    st1, j1 = apply(client, name="兄弟 一郎", email=e3, referrer="入塾申込フォーム", subjects=extra_label)
    st2, j2 = apply(client, name="兄弟 次郎", email=e3, referrer="塾生アプリ", subjects=extra_label)
    check("2 行作成", st1 == 200 and st2 == 200, (st1, st2))
    r = client.post(f"/api/admin/course-applications/{j1['application_id']}/approve", json={"ai_disabled": False}, headers=adm)
    j = r.json() if r.status_code == 200 else {}
    check("一郎を承認 → merged_count = 0", r.status_code == 200 and j.get("merged_count") == 0, (r.status_code, j))
    rows = app_rows(mod, e3)
    check("次郎は pending のまま (student_id なし)", any(x["name"] == "兄弟 次郎" and x["status"] == "pending" and x["student_id"] is None for x in rows), rows)

    # ------------------------------------------------------------ 5. 単独行 (LP 申込)
    print("5) 単独の申込は従来どおり")
    e4 = "merge-single@example.org"
    st1, j1 = apply(client, name="単独 三郎", email=e4, referrer="友人紹介")
    r = client.post(f"/api/admin/course-applications/{j1['application_id']}/approve", json={"ai_disabled": False}, headers=adm)
    j = r.json() if r.status_code == 200 else {}
    check("承認 200・merged_count = 0・従来キー健在", r.status_code == 200 and j.get("merged_count") == 0
          and all(k in j for k in ("student_id", "attached_existing", "ai_disabled_final", "class_labels", "class_labels_empty", "line_link_code")), (r.status_code, j))

    # ------------------------------------------------------------ 6. 画面側のソース検査
    print("6) 画面側 (ソース検査)")
    ceo_js = open(os.path.join(REPO, "ceo.js"), encoding="utf-8").read()
    ceo_html = open(os.path.join(REPO, "ceo.html"), encoding="utf-8").read()
    reg = open(os.path.join(REPO, "juku-register.html"), encoding="utf-8").read()
    check("ceo.js: group_key で束ねて merged_count を表示", "group_key" in ceo_js and "merged_count" in ceo_js and "data-ids" in ceo_js)
    check("ceo.js: AI 既定は受講内容 (国公立難関大コース / AI管理) で決める", "_aiHint" in ceo_js and "国公立難関大コース" in ceo_js and "AI管理" in ceo_js)
    check("ceo.html: ceo.js の ?v= が更新済み", "ceo.js?v=20260907-dashboard-ops" not in ceo_html and "ceo.js?v=" in ceo_html)
    check("juku-register.html: STEP1 の氏名・メールを引き継ぐ", "trillion_enroll_submitted_v1" in reg)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
