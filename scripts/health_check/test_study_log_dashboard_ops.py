#!/usr/bin/env python3
"""📚 学習記録ダッシュボードの運用改善 (2026-09-07・残件 3/4/5) の回帰テスト (in-process・一時 SQLite)。

  3. タイムラインは offset/total でページングできる (従来は 200 件で無言に打ち切り)。読み込みはパネルごとに独立 (ソース検査)
  4. 自己申告は 1 日合計に上限 (既定 16 時間)。投稿も修正も超えたら 400。ヒートマップに演習 (question_attempts) の日別件数が重なる
  5. テスト系の名前 (テスト/test/ダミー/確認用 …) は母集団から外れる。ヒートマップに学年/記録ありフィルタ、0 分は薄い赤、単位は時間 (ソース検査)
  「全データ更新」ボタンに学習記録の再読込が入っている (ソース検査)
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import os
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
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="dashops_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid", "STUDY_LOG_DAILY_CAP_MIN": "960",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_dashops", MAIN_PY)
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


def student_token(mod, sid):
    exp = int(time.time()) + 3600
    payload = f"session.{sid}.{exp}"
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}.{sig}".encode()).decode().rstrip("=")


def mk(mod, name, email):
    conn = mod.db(); c = conn.cursor()
    far = (datetime.datetime.utcnow() + datetime.timedelta(days=365)).isoformat()
    c.execute("INSERT INTO students (name, email, status, plan, trial_end, course, grade) VALUES (?,?,?,?,?,?,?)",
              (name, email, "paid", "premium", far, "kokuritsu_nankan", "高校3年"))
    conn.commit(); c.execute("SELECT id FROM students WHERE email = ?", (email,)); sid = c.fetchone()["id"]; conn.close()
    return sid


def main():
    print("📚 学習記録ダッシュボード 運用改善 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    A = mk(mod, "Student A", "a@example.org")
    T = mk(mod, "テスト太郎", "t@example.org")          # テスト系の名前 → 母集団から外れる
    tok = {"Authorization": "Bearer " + student_token(mod, A)}
    today = mod._today_jst().isoformat()
    mod._RATE_LIMIT_STORE.clear()

    print("4) 1 日合計の上限 (16 時間)")
    r = client.post("/api/study-logs", json={"subject": "英語", "minutes": 900, "material": "A"}, headers=tok)
    check("900 分は通る", r.status_code == 200, r.text[:120])
    lid = r.json().get("id")
    r = client.post("/api/study-logs", json={"subject": "数学", "minutes": 100, "material": "B"}, headers=tok)
    check("同日に +100 分 (合計 1000 > 960) は 400", r.status_code == 400 and "16 時間" in r.text, f"{r.status_code} {r.text[:150]}")
    r = client.post("/api/study-logs", json={"subject": "数学", "minutes": 60, "material": "B"}, headers=tok)
    check("同日に +60 分 (合計 960) は通る", r.status_code == 200, r.text[:120])
    lid2 = r.json().get("id")
    r = client.patch(f"/api/study-logs/{lid2}", json={"minutes": 61}, headers=tok)
    check("修正で合計が超える (900+61) と 400", r.status_code == 400, f"{r.status_code} {r.text[:120]}")
    r = client.patch(f"/api/study-logs/{lid}", json={"minutes": 800}, headers=tok)
    check("自分の分を減らす修正は通る (この記録自身は合計から除く)", r.status_code == 200, r.text[:120])
    yesterday = (mod._today_jst() - datetime.timedelta(days=1)).isoformat()
    r = client.patch(f"/api/study-logs/{lid2}", json={"studied_date": yesterday, "minutes": 900}, headers=tok)
    check("別の日に移す修正は、その日の合計で判定 (通る)", r.status_code == 200, r.text[:120])

    print("4) ヒートマップに演習の日別件数")
    conn = mod.db(); c = conn.cursor()
    now_utc = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    for _ in range(3):
        c.execute("INSERT INTO question_attempts (student_id, source, subject, topic, is_correct, created_at) VALUES (?,?,?,?,?,?)", (A, "practice", "english", "時制", 1, now_utc))
    conn.commit(); conn.close()
    hm = client.get("/api/admin/study-logs/heatmap?days=7", headers=adm).json()
    row = next((s for s in hm.get("students", []) if s.get("student_id") == A), {})
    check("qa[today] = 3・qa_total = 3", (row.get("qa") or {}).get(today) == 3 and row.get("qa_total") == 3, row)
    check("data[today] は修正後の 800 分", (row.get("data") or {}).get(today) == 800, row.get("data"))

    print("5) テスト系の名前は母集団から外れる")
    ids = {s.get("student_id") for s in hm.get("students", [])}
    check("『テスト太郎』はヒートマップに出ない", T not in ids and A in ids, ids)
    check("_is_blocked_test_name", mod._is_blocked_test_name("テスト太郎") and mod._is_blocked_test_name("Demo User") and not mod._is_blocked_test_name("山田 花子"))

    print("3) タイムラインのページング")
    tl = client.get("/api/admin/study-logs/timeline?days=7&limit=1&offset=0", headers=adm).json()
    check("limit=1: 1 件返り total は 2", tl.get("count") == 1 and tl.get("total") == 2 and tl.get("offset") == 0, {k: tl.get(k) for k in ("count", "total", "offset")})
    tl2 = client.get("/api/admin/study-logs/timeline?days=7&limit=1&offset=1", headers=adm).json()
    check("offset=1: 残り 1 件 (重複しない)", tl2.get("count") == 1 and tl2["logs"][0]["id"] != tl["logs"][0]["id"], (tl.get("logs"), tl2.get("logs")))

    print("   ソース検査 (ceo.js / ceo.html)")
    js = open(os.path.join(REPO, "ceo.js"), encoding="utf-8").read()
    html = open(os.path.join(REPO, "ceo.html"), encoding="utf-8").read()
    check("読み込みはパネルごと (Promise.allSettled) で失敗を表示", "Promise.allSettled(panels.map" in js and "読み込みに失敗しました" in js)
    check("タイムラインに「さらに読み込む」と 表示/全件", "loadMoreStudyLogTimeline" in js and "slTlMoreBtn" in js and "slTlTotal" in js)
    check("ヒートマップに学年/記録ありフィルタと演習マーク", "applyStudyLogHeatmapFilter" in js and "slHmActiveOnly" in js and "演習 ${q}問" in js)
    check("0 分は薄い赤・単位は時間", "rgba(220,38,38,0.16)" in js and "0 (未記録)" in js and "計 (h)" in js)
    check("「全データ更新」に学習記録の再読込", "['studyLog',        typeof loadStudyLogDashboard === 'function' ? loadStudyLogDashboard : null]" in html)
    check("ceo.js の ?v= が更新されている", "ceo.js?v=20260907-dashboard-ops" in html)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
