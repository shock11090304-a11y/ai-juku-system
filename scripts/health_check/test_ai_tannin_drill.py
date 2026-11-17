#!/usr/bin/env python3
"""🧑‍🏫 AI 担任の配信 (POST /api/admin/grammar-drill/create に ai_tannin: true・2026-11-17 塾長「その子のための問題を出してあげて」)。

固定する性質 (一時 SQLite・外部通信なし・メールと LINE は偽物):
  [1] ai_tannin はレビュー済みの出典だけから選ぶ (未レビューの出典が多くても混ざらない)・created_by='ai_tannin'
  [2] お知らせのメールも LINE も送らない (HOMEWORK_NOTIFY_EMAIL=manual の既定でも)・notify_channels はどちらも False
  [3] AIなし枠 (体験中でない) と学年の区分に合わない生徒 (中学生に english) は配らず refused に理由つきで出す・全員だめなら 409
  [4] AI 体験中の AIなし枠には配る・見つからない生徒は refused (not_found)
  [5] レビュー済みが足りなければ 400 (未レビューで埋めない)・習熟度テストは 422
  [6] 前に配った問題は避ける (2 本目は 1 本目と重ならない)・一覧の kind=owner に出る
  [7] ai_tannin を付けない CEO の配信は今までどおり (created_by='admin'・メールは manual で送る)
  [8] 高校の古文 (japanese・2026-11-17 のシードの出典) も同じ決まり: レビュー済みだけ・中学生は断る / 許可リストに無い科目は 400
実行: python3 scripts/health_check/test_ai_tannin_drill.py   # exit 0 = PASS / 1 = FAIL
"""
import datetime
import importlib.util
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="ai_tannin_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        "DATABASE_URL": "",   # ★空にしないと本番 Postgres に書く
        "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0", "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "", "ANTHROPIC_API_KEY": "",
        "BASE_URL": "https://example.invalid", "CRON_SECRET": "test-cron-secret",
    })
    for k in ("HOMEWORK_NOTIFY_EMAIL", "HOMEWORK_NOTIFY_LINE", "AUTO_DELIVERY_REVIEWED_SOURCES"):
        os.environ.pop(k, None)
    spec = importlib.util.spec_from_file_location("aijuku_main_ai_tannin", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def main():
    mod = load_main()
    now = datetime.datetime.now(datetime.timezone.utc)
    te = (now + datetime.timedelta(days=3650)).isoformat()
    future = mod._utc_naive_iso(now + datetime.timedelta(days=5))
    conn = mod.db(); c = conn.cursor()

    def make(name, email, ai_disabled=0, trial=None, grade="高校2年"):
        c.execute("INSERT INTO students (name, email, status, trial_end, course, grade, goal, ai_disabled, ai_trial_until) "
                  "VALUES (?, ?, 'trial', ?, 'kokuritsu_nankan', ?, '国公立大学', ?, ?)", (name, email, te, grade, ai_disabled, trial))
        c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
        return c.fetchone()["id"]

    s_ai = make("架空 生徒A", "tn-a@example.org")
    s_noai = make("架空 生徒B", "tn-b@example.org", 1)
    s_trial = make("架空 生徒C", "tn-c@example.org", 1, future)
    s_chu = make("架空 生徒D", "tn-d@example.org", 0, None, "中学2年")
    reviewed, unreviewed = set(), set()
    for i in range(24):   # レビュー済み 24 問
        c.execute("INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) "
                  "VALUES ('english', '時制', 'standard', ?, ?, 0, '解説', 'manual-drill-v1') RETURNING id",
                  (f"架空のレビュー済み {i} (   ).", json.dumps(["a", "b", "c", "d"])))
        reviewed.add(c.fetchone()["id"])
    for i in range(200):  # 未レビュー 200 問 (出典 pool)
        c.execute("INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) "
                  "VALUES ('english', '時制', 'standard', ?, ?, 0, '解説', 'pool') RETURNING id",
                  (f"架空の未レビュー {i} (   ).", json.dumps(["a", "b", "c", "d"])))
        unreviewed.add(c.fetchone()["id"])
    for i in range(10):   # 仮定法はレビュー済みが 5 問だけ
        c.execute("INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) "
                  "VALUES ('english', '仮定法', 'standard', ?, ?, 0, '解説', ?)",
                  (f"架空の仮定法 {i} (   ).", json.dumps(["a", "b", "c", "d"]), "manual-drill-v1" if i < 5 else "pool"))
    conn.commit(); conn.close()
    mod._AI_DISABLED_CACHE.clear()

    mails, lines = [], []
    mod._send_message_email = lambda to, subject, body, student_name=None: (mails.append(to), {"sent": True})[1]
    mod._do_line_push = lambda sid, template, params=None: (lines.append(sid), {"ok": True})[1]

    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    H = {"X-Cron-Secret": "test-cron-secret"}
    base = {"subject": "english", "unit": "時制", "count": 10, "levels": ["standard"], "ai_tannin": True}

    def drill_row(did):
        cc = mod.db(); k = cc.cursor()
        k.execute("SELECT question_ids, created_by FROM grammar_drills WHERE id = ?", (did,))
        r = k.fetchone(); cc.close()
        return set(json.loads(r["question_ids"])), r["created_by"]

    print("[1][2][3][4] 生徒 4 名 + 見つからない 1 名")
    r = client.post("/api/admin/grammar-drill/create", headers=H,
                    json=dict(base, student_ids=[s_ai, s_noai, s_trial, s_chu, 999999]))
    j = r.json()
    check("200", r.status_code == 200, (r.status_code, r.text[:300]))
    qids1, cb = drill_row(j["drill_id"])
    check("10 問すべてレビュー済みの出典", len(qids1) == 10 and qids1 <= reviewed, qids1 & unreviewed)
    check("created_by = ai_tannin", cb == "ai_tannin", cb)
    check("配ったのは AIあり と AI 体験中の 2 名", sorted(a["student_id"] for a in j["assigned"]) == sorted([s_ai, s_trial]), j["assigned"])
    reasons = {x["student_id"]: x["reason"] for x in j["refused"]}
    check("refused: AIなし=ai_nashi・中学生=band・不明=not_found",
          reasons == {s_noai: "ai_nashi", s_chu: "band", 999999: "not_found"}, reasons)
    check("メール 0・LINE 0・notify_channels どちらも False",
          mails == [] and lines == [] and j["notify_channels"] == {"line": False, "email": False}, (mails, lines, j["notify_channels"]))
    check("reviewed_available = 24", j["reviewed_available"] == 24, j["reviewed_available"])

    print("[3] 全員だめなら 409")
    r = client.post("/api/admin/grammar-drill/create", headers=H, json=dict(base, student_ids=[s_noai, s_chu]))
    check("409", r.status_code == 409, (r.status_code, r.text[:200]))

    print("[5] 在庫不足と習熟度テスト")
    r = client.post("/api/admin/grammar-drill/create", headers=H, json=dict(base, unit="仮定法", student_ids=[s_ai]))
    check("レビュー済み 5 問しかない単元に 10 問 → 400 (未レビューで埋めない)", r.status_code == 400 and "レビュー済み" in r.text, (r.status_code, r.text[:200]))
    r = client.post("/api/admin/grammar-drill/create", headers=H,
                    json={"subject": "proficiency_test", "unit": "x", "ai_tannin": True, "student_ids": [s_ai]})
    check("習熟度テスト → 422", r.status_code == 422, (r.status_code, r.text[:200]))

    r = client.post("/api/admin/grammar-drill/create", headers=H, json=dict(base, ai_tannin="true", student_ids=[s_ai]))
    check("ai_tannin が文字列 \"true\" → 422 (普通の配信に落とさない)", r.status_code == 422, (r.status_code, r.text[:200]))

    print("[6] 2 本目は前の問題を避ける・一覧に出る")
    r = client.post("/api/admin/grammar-drill/create", headers=H, json=dict(base, student_ids=[s_ai]))
    qids2, _ = drill_row(r.json()["drill_id"])
    check("2 本目もレビュー済みだけ・1 本目と重なるのは足りない分だけ (24 問中 14 問は未出 → 重なり 0)",
          qids2 <= reviewed and not (qids1 & qids2), qids1 & qids2)
    lst = client.get("/api/admin/grammar-drill/list?kind=owner&limit=50", headers=H).json()
    check("kind=owner の一覧に出る", any(it["id"] == r.json()["drill_id"] for it in lst.get("items", [])))

    print("[7] ai_tannin なし = 今までどおり")
    r = client.post("/api/admin/grammar-drill/create", headers=H,
                    json={"subject": "english", "unit": "時制", "count": 10, "levels": ["standard"], "student_ids": [s_noai]})
    j = r.json()
    _, cb = drill_row(j["drill_id"])
    check("200・created_by=admin・AIなし枠にも配れる (CEO の配信は変えない)", r.status_code == 200 and cb == "admin"
          and [a["student_id"] for a in j["assigned"]] == [s_noai], (r.status_code, cb))
    check("refused は空・reviewed_available は None", j.get("refused") == [] and j.get("reviewed_available") is None, j)

    print("[8] 高校の古文 (2026-11-17・japanese・出典 kosei-kokugo-v1) も同じ決まり")
    cc = mod.db(); k = cc.cursor()
    kobun_ok, kobun_ng = set(), set()
    for i in range(12):   # レビュー済み 12 問 (basic 6・standard 6)
        k.execute("INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) "
                  "VALUES ('japanese', '古文 単語', ?, ?, ?, 0, '解説', 'kosei-kokugo-v1') RETURNING id",
                  ("basic" if i % 2 else "standard", f"架空の古文 レビュー済み {i}", json.dumps(["a", "b", "c", "d"])))
        kobun_ok.add(k.fetchone()["id"])
    for i in range(60):   # 同じ単元の未レビュー 60 問 (exam_questions を分解した古い行のつもり)
        k.execute("INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) "
                  "VALUES ('japanese', '古文 単語', 'standard', ?, ?, 0, '解説', 'pool') RETURNING id",
                  (f"架空の古文 未レビュー {i}", json.dumps(["a", "b", "c", "d"])))
        kobun_ng.add(k.fetchone()["id"])
    for i in range(30):   # 地学は許可リストに無い科目
        k.execute("INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) "
                  "VALUES ('earth', '地学基礎', 'standard', ?, ?, 0, '解説', 'pool')",
                  (f"架空の地学 未レビュー {i}", json.dumps(["a", "b", "c", "d"])))
    cc.commit(); cc.close()
    n_mail, n_line = len(mails), len(lines)   # [7] の CEO の配信で送ったメールは数えない
    r = client.post("/api/admin/grammar-drill/create", headers=H,
                    json={"subject": "japanese", "unit": "古文 単語", "count": 10, "levels": ["basic", "standard"],
                          "ai_tannin": True, "student_ids": [s_ai, s_chu]})
    j = r.json()
    check("古文: 200", r.status_code == 200, (r.status_code, r.text[:300]))
    q8, cb8 = drill_row(j["drill_id"]) if r.status_code == 200 else (set(), None)
    check("古文: 10 問すべて kosei-kokugo-v1 (同じ単元の未レビュー 60 問は混ざらない)・created_by = ai_tannin",
          len(q8) == 10 and q8 <= kobun_ok and cb8 == "ai_tannin", (q8 & kobun_ng, cb8))
    check("古文: 高校生に配り、中学生は band で断る",
          [a["student_id"] for a in j.get("assigned", [])] == [s_ai]
          and {x["student_id"]: x["reason"] for x in j.get("refused", [])} == {s_chu: "band"}, (j.get("assigned"), j.get("refused")))
    check("古文: reviewed_available = 12・メールも LINE も送らない",
          j.get("reviewed_available") == 12 and len(mails) == n_mail and len(lines) == n_line,
          (j.get("reviewed_available"), mails[n_mail:], lines[n_line:]))
    r = client.post("/api/admin/grammar-drill/create", headers=H,
                    json={"subject": "earth", "unit": "地学基礎", "count": 10, "levels": ["standard"],
                          "ai_tannin": True, "student_ids": [s_ai]})
    check("許可リストに無い科目 (地学) は 400 (未レビューで埋めない)", r.status_code == 400 and "レビュー済み" in r.text, (r.status_code, r.text[:200]))

    print("\nFAIL:" if FAILURES else "\nPASS", *FAILURES, sep="\n  ")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
