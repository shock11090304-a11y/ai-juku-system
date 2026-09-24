#!/usr/bin/env python3
"""📅🎬 受講開始月 (students.start_month) と 入塾前アーカイブ (archive_full_paid / class_recordings.lesson_date) の回帰テスト。

背景 (2026-09-24 塾長指示):
  翌月開始の生徒も申込直後に承認する (予定表・配信ドリル・メッセージは即使える)。ただし受講開始月より前は
  ・クラス宿題の一括配信の対象にしない (期限の月で判定) ・出欠を出さない/受けない ・入塾月 (開始月の 1 日) より前の録画を出さない。
  2 万円 (特商法「入塾前の授業アーカイブの視聴」) を払った生徒は archive_full_paid=1 で全期間。
  ★start_month が NULL の生徒 (既存全員) はどの判定も「制限なし」= 従来と同じ。2026-08-07 に絞り込みで 36 名の録画が
    消えた事故があるので、**NULL の生徒の録画が 1 本も減らないこと**をここで固定する。

固定する性質:
  1. ヘルパー: 備考の「受講開始月: 2026年10月」を読む / 'YYYY-MM' の検証 / 開始前判定 / 録画の授業日 (題名 M/D → 登録日基準)
  2. feed: NULL の生徒は全部見える (archive_from=None・hidden 0)。開始月つきは入塾月以降だけ。全期間視聴は全部。
     全員向け (session_id NULL) の録画は誰にでも出る。before_start は開始月より前だけ true。
  3. クラス宿題の一括配信: 期限の月が開始月より前の生徒は対象外 (skipped_before_start に名前)。期限を開始月以降にすれば入る。
  4. 出欠: 開始前の日付は生徒の POST が 400・塾長の名簿から外れる。開始月以降は載る。
  5. 管理 API: 受講開始月の保存/解除/不正値、全期間視聴の ON/OFF、録画の授業日の修正。
  6. 承認: 入塾申込フォームの備考から新規生徒の start_month が入る。既存アカウントへの合流では入れない (response で知らせる)。
  7. admin_stats / 授業の詳細 が新しい値を返す。統合の埋め込み列は archive_full_paid だけ。cron の SQL (start_month 条件つき) が落ちない。

実行:
    python3 scripts/health_check/test_start_month_archive.py
    # exit 0 = PASS / 1 = FAIL

外部通信は一切しない。DB は一時 SQLite。
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import json
import os
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []
JST = datetime.timezone(datetime.timedelta(hours=9))
CRON_SECRET = "test-cron-secret"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {detail}" if detail else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="startmonth_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと **本番 Postgres** に書き込む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "",
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
        "CRON_SECRET": CRON_SECRET,
        "MIDWEEK_NUDGE_ENABLED": "1",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_startmonth", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def admin_token(mod, hours=1):
    exp = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)).timestamp())
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), f"admin.{exp}".encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


def student_token(mod, sid, hours=1):
    exp = int(time.time()) + hours * 3600
    payload = f"session.{sid}.{exp}"
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}.{sig}".encode()).decode().rstrip("=")


CLASS = "月曜1限 中学応用"


def make_student(mod, name, email, start_month=None, archive_full_paid=0):
    conn = mod.db()
    c = conn.cursor()
    far = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)).isoformat()
    c.execute(
        "INSERT INTO students (name, email, status, trial_end, course, grade, goal, ai_disabled, class_labels, start_month, archive_full_paid) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)",
        (name, email, "trial", far, "kokuritsu_nankan", "中学3年", "高校受験", json.dumps([CLASS], ensure_ascii=False),
         start_month, int(archive_full_paid)),
    )
    conn.commit()
    c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
    sid = c.fetchone()["id"]
    conn.close()
    mod._AI_DISABLED_CACHE.pop(sid, None)
    return sid


def month_str(offset):
    d = datetime.datetime.now(JST).date().replace(day=1)
    y, m = d.year, d.month + offset
    while m > 12:
        m -= 12; y += 1
    while m < 1:
        m += 12; y -= 1
    return f"{y:04d}-{m:02d}"


def main():
    print("📅🎬 受講開始月 / 入塾前アーカイブ 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    today = datetime.datetime.now(JST).date()
    this_m, next_m, prev_m = month_str(0), month_str(1), month_str(-1)

    print("[0] 列が init_db で入る")
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT start_month, archive_full_paid FROM students LIMIT 1"); c.fetchall()
    c.execute("SELECT lesson_date FROM class_recordings LIMIT 1"); c.fetchall()
    conn.close()
    check("students.start_month / archive_full_paid, class_recordings.lesson_date が存在", True)
    check("_table_has_column が True", mod._table_has_column("students", "start_month") and mod._table_has_column("class_recordings", "lesson_date"))
    check("存在しない列は False (例外にしない)", mod._table_has_column("students", "no_such_column_xyz") is False)
    mod._HAS_COL_CACHE.pop("students.no_such_column_xyz", None)

    print("\n[1] ヘルパー")
    p = mod._parse_start_month_from_note
    check("備考「受講開始月: 2026年10月（申込書の選択: 翌月から）」→ 2026-10", p("受講開始月: 2026年10月（申込書の選択: 翌月から）") == "2026-10")
    check("全角コロン・空白ゆれも読む", p("受講開始月： 2026 年 1 月") == "2026-01")
    check("無い備考は None", p("AI学習アプリ申込済み") is None and p(None) is None)
    check("月が 13 は None", p("受講開始月: 2026年13月") is None)
    v = mod._valid_month_or_none
    check("'2026-10' → '2026-10' / '2026-1' → '2026-01' / 壊れた値は None", v("2026-10") == "2026-10" and v("2026-1") == "2026-01" and v("2026/10") is None and v("") is None and v(None) is None)
    b = mod._before_start_month
    check("開始月より前なら True・当月/以降は False・NULL は False", b(next_m) is True and b(this_m) is False and b(prev_m) is False and b(None) is False and b("") is False and b("garbage") is False)
    check("月を指定して判定 (期限の月)", b("2026-10", "2026-09") is True and b("2026-10", "2026-10") is False and b("2026-10", "2026-11") is False)
    ac = mod._archive_cutoff
    check("cutoff: 開始月の 1 日 / 全期間視聴は None / NULL は None", ac("2026-10", 0) == "2026-10-01" and ac("2026-10", 1) is None and ac(None, 0) is None)
    rl = mod._recording_lesson_date
    check("題名 '9/15' + 登録日 2026-09-16 → 2026-09-15", rl("9/15", "2026-09-16 10:00:00") == "2026-09-15")
    check("題名 '12/28' + 登録日 2027-01-03 → 2026-12-28 (年またぎ)", rl("12/28", "2027-01-03 00:00:00") == "2026-12-28")
    check("登録日の翌日 (UTC ずれ) までは同日扱い", rl("9/17", "2026-09-16 23:30:00") == "2026-09-17")
    check("題名 '月曜1限 中学応用 7/7' も読む", rl("月曜1限 中学応用 7/7", "2026-07-08") == "2026-07-07")
    check("題名 '8月17日' も読む", rl("8月17日 英文法", "2026-08-18") == "2026-08-17")
    check("「中1・2 英語」「Lesson 10-12」「1.5倍速」は日付にしない (None)", rl("中1・2 英語", "2026-08-18") is None and rl("Lesson 10-12", "2026-08-18") is None and rl("1.5倍速", "2026-08-18") is None)
    check("年つき '2026/8/17' は読まない (None)", rl("2026/8/17", "2026-08-18") is None)
    check("候補が複数 '8/17 9/3 合同' は読まない", rl("8/17 9/3 合同", "2026-09-04") is None)
    check("'1.5倍速 8/17' は 8/17 だけを日付と読む ('.' は区切りにしない)", rl("1.5倍速 8/17", "2026-08-18") == "2026-08-17")
    check("日付の無い題名は None", rl("合同 英語", "2026-08-18") is None)
    check("lesson_date 列が優先", rl("9/15", "2026-09-16", "2026-09-01") == "2026-09-01")
    check("壊れた lesson_date は題名に戻る", rl("9/15", "2026-09-16", "not-a-date") == "2026-09-15")

    print("\n[2] feed: 録画の絞り込み")
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO class_sessions (title, is_published) VALUES (?, 1)", (CLASS,))
    c.execute("SELECT id FROM class_sessions WHERE title = ?", (CLASS,)); s1 = c.fetchone()["id"]
    y_prev = int(prev_m[:4]); m_prev = int(prev_m[5:7])
    rows = [
        (s1, f"{m_prev}/17", "https://youtu.be/TestPrev001", f"{prev_m}-18 00:00:00", None),            # 先月の授業 (題名から)
        (s1, f"{today.month}/{today.day}", "https://youtu.be/TestCur0001", f"{today.isoformat()} 12:00:00", None),  # 今月の授業
        (None, "全体向け 説明会", "https://youtu.be/TestLoose01", "2026-01-05 00:00:00", None),           # 全員向け (授業に紐づかない)
        (s1, "日付のない題名", "https://youtu.be/TestNoDate1", "2026-01-05 00:00:00", None),              # 登録日で判定 → 古い
        (s1, "来月ぶん 1/1", "https://youtu.be/TestNextM01", f"{today.isoformat()} 12:00:00", f"{next_m}-01"),  # lesson_date 列が優先
    ]
    for sess, title, url, created, ld in rows:
        c.execute("INSERT INTO class_recordings (session_id, title, video_url, provider, is_published, created_at, lesson_date) "
                  "VALUES (?,?,?,'youtube',1,?,?)", (sess, title, url, created, ld))
    conn.commit(); conn.close()
    sid_a = make_student(mod, "開始月テスト A", "sm-a@example.org")                       # NULL = 既存生徒
    sid_b = make_student(mod, "開始月テスト B", "sm-b@example.org", start_month=next_m)   # 翌月開始
    sid_c = make_student(mod, "開始月テスト C", "sm-c@example.org", start_month=this_m)   # 今月開始
    sid_d = make_student(mod, "開始月テスト D", "sm-d@example.org", start_month=next_m, archive_full_paid=1)  # 翌月開始・全期間
    tok = {s: {"Authorization": "Bearer " + student_token(mod, s)} for s in (sid_a, sid_b, sid_c, sid_d)}

    def feed(s):
        r = client.get("/api/student/class/feed", headers=tok[s])
        check(f"feed {s} → 200", r.status_code == 200, r.text[:160])
        return r.json() if r.status_code == 200 else {}

    def titles(d):
        out = []
        for se in d.get("sessions", []):
            out += [x["title"] for x in se.get("recordings", [])]
        return sorted(out)

    fa = feed(sid_a)
    check("A (NULL): 授業の録画 4 本すべて見える (従来どおり)", titles(fa) == sorted([f"{m_prev}/17", f"{today.month}/{today.day}", "日付のない題名", "来月ぶん 1/1"]), f"titles={titles(fa)}")
    check("A: 全員向けも見える", [x["title"] for x in fa.get("loose_recordings", [])] == ["全体向け 説明会"])
    check("A: archive_from=None / hidden 0 / before_start False / start_month None",
          fa.get("archive_from") is None and fa.get("hidden_recordings") == 0 and fa.get("before_start") is False and fa.get("start_month") is None, str({k: fa.get(k) for k in ("archive_from", "hidden_recordings", "before_start", "start_month")}))
    fb = feed(sid_b)
    check("B (翌月開始): 来月ぶん (lesson_date) だけ", titles(fb) == ["来月ぶん 1/1"], f"titles={titles(fb)}")
    check("B: 全員向けは見える", [x["title"] for x in fb.get("loose_recordings", [])] == ["全体向け 説明会"])
    check("B: archive_from=翌月 1 日 / hidden 3 / before_start True", fb.get("archive_from") == f"{next_m}-01" and fb.get("hidden_recordings") == 3 and fb.get("before_start") is True and fb.get("start_month") == next_m, str({k: fb.get(k) for k in ("archive_from", "hidden_recordings", "before_start")}))
    fc = feed(sid_c)
    check("C (今月開始): 今月の授業 + 来月ぶん (先月・日付なしは隠す)", titles(fc) == sorted([f"{today.month}/{today.day}", "来月ぶん 1/1"]), f"titles={titles(fc)}")
    check("C: hidden 2 / before_start False", fc.get("hidden_recordings") == 2 and fc.get("before_start") is False and fc.get("archive_from") == f"{this_m}-01")
    fd = feed(sid_d)
    check("D (翌月開始・全期間視聴): 4 本すべて見える", titles(fd) == titles(fa), f"titles={titles(fd)}")
    check("D: archive_full True / archive_from None / before_start True", fd.get("archive_full") is True and fd.get("archive_from") is None and fd.get("before_start") is True)

    print("\n[3] クラス宿題の一括配信")
    def assign(due):
        mod._RATE_LIMIT_STORE.clear()
        body = {"class_label": CLASS, "title": f"宿題 due={due}", "subject": "english", "topic": "英文法 関係詞"}
        if due:
            body["due_date"] = due
        r = client.post("/api/admin/class/homework", json=body, headers=adm)
        check(f"POST homework (due={due}) → 200", r.status_code == 200, r.text[:160])
        return r.json() if r.status_code == 200 else {}
    j = assign(f"{this_m}-28")
    check("今月期限: A・C に配信、B・D は受講開始前で除外", sorted(j.get("students", [])) == sorted(["開始月テスト A", "開始月テスト C"]) and sorted(j.get("skipped_before_start", [])) == sorted(["開始月テスト B", "開始月テスト D"]), str(j))
    j = assign(f"{next_m}-05")
    check("翌月期限: 4 名全員に配信", j.get("assigned_count") == 4 and j.get("skipped_before_start") == [], str(j))
    j = assign(None)
    check("期限なし = 今月扱い: B・D は除外", j.get("assigned_count") == 2 and sorted(j.get("skipped_before_start", [])) == sorted(["開始月テスト B", "開始月テスト D"]), str(j))
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) AS n FROM homework_assignments WHERE student_id = ?", (sid_b,)); nb = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) AS n FROM homework_assignments WHERE student_id = ?", (sid_a,)); na = c.fetchone()["n"]
    conn.close()
    check("B の宿題は翌月期限の 1 本だけ・A は 3 本", nb == 1 and na == 3, f"B={nb} A={na}")

    print("\n[4] 出欠")
    d_today = today.isoformat()
    d_next = f"{next_m}-03"
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/student/class/attend", json={"class_label": CLASS, "att_date": d_today, "status": "present"}, headers=tok[sid_b])
    check("B: 今日の出欠 POST → 400 (受講開始前)", r.status_code == 400 and "受講開始" in (r.json().get("detail") or ""), r.text[:160])
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/student/class/attend", json={"class_label": CLASS, "att_date": d_next, "status": "present"}, headers=tok[sid_b])
    check("B: 翌月の出欠 POST → 200", r.status_code == 200, r.text[:160])
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/student/class/attend", json={"class_label": CLASS, "att_date": d_today, "status": "present"}, headers=tok[sid_a])
    check("A (NULL): 今日の出欠 POST → 200", r.status_code == 200, r.text[:160])
    # 授業 (session) 単位の出欠も同じ判定: 授業日が開始月より前なら 400・開始月以降なら 200・日付未定は従来どおり 200
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO class_sessions (title, session_date, is_published) VALUES (?, ?, 1)", (CLASS, d_today))
    c.execute("SELECT id FROM class_sessions WHERE session_date = ? AND title = ?", (d_today, CLASS)); s_today = c.fetchone()["id"]
    c.execute("INSERT INTO class_sessions (title, session_date, is_published) VALUES (?, ?, 1)", (CLASS, d_next))
    c.execute("SELECT id FROM class_sessions WHERE session_date = ? AND title = ?", (d_next, CLASS)); s_next = c.fetchone()["id"]
    conn.commit(); conn.close()
    for _s, _tok, _want, _lbl in ((s_today, tok[sid_b], 400, "B: 今日の授業への出欠 → 400"), (s_next, tok[sid_b], 200, "B: 翌月の授業への出欠 → 200"),
                                  (s_today, tok[sid_a], 200, "A (NULL): 今日の授業への出欠 → 200"), (s1, tok[sid_b], 200, "B: 日付未定の授業への出欠 → 200 (従来どおり)")):
        mod._RATE_LIMIT_STORE.clear()
        r = client.post("/api/student/class/attendance", json={"session_id": _s, "status": "present"}, headers=_tok)
        check(_lbl, r.status_code == _want, f"status={r.status_code} {r.text[:120]}")
    r = client.get("/api/admin/class/attend", params={"att_date": d_today, "class_label": CLASS}, headers=adm)
    names_today = sorted(x["name"] for x in r.json().get("roster", [])) if r.status_code == 200 else None
    check("塾長の名簿 (今日): A・C だけ (B・D は開始前)", names_today == sorted(["開始月テスト A", "開始月テスト C"]), f"{r.status_code} {names_today}")
    r = client.get("/api/admin/class/attend", params={"att_date": d_next, "class_label": CLASS}, headers=adm)
    names_next = sorted(x["name"] for x in r.json().get("roster", [])) if r.status_code == 200 else None
    check("塾長の名簿 (翌月): 4 名全員", names_next == sorted(["開始月テスト A", "開始月テスト B", "開始月テスト C", "開始月テスト D"]), f"{r.status_code} {names_next}")

    print("\n[5] 管理 API")
    r = client.post(f"/api/admin/students/{sid_a}/start-month", json={"start_month": "2026/10"}, headers=adm)
    check("不正な月 → 400", r.status_code == 400, r.text[:120])
    r = client.post(f"/api/admin/students/{sid_a}/start-month", json={"start_month": next_m}, headers=adm)
    check("A に翌月を設定 → 200・before_start True・label", r.status_code == 200 and r.json().get("start_month") == next_m and r.json().get("before_start") is True and r.json().get("label", "").endswith("月"), r.text[:160])
    fa2 = feed(sid_a)
    check("設定後の A の feed は B と同じ絞り込み", titles(fa2) == ["来月ぶん 1/1"] and fa2.get("before_start") is True)
    r = client.post(f"/api/admin/students/{sid_a}/start-month", json={"start_month": None}, headers=adm)
    check("A を解除 (null) → 200・start_month None", r.status_code == 200 and r.json().get("start_month") is None, r.text[:120])
    fa3 = feed(sid_a)
    check("解除後の A は再び全部見える", titles(fa3) == titles(fa) and fa3.get("archive_from") is None)
    r = client.post("/api/admin/students/999999/start-month", json={"start_month": next_m}, headers=adm)
    check("存在しない生徒 → 404", r.status_code == 404)
    r = client.post(f"/api/admin/students/{sid_b}/archive-access", json={"archive_full_paid": True}, headers=adm)
    check("B を全期間視聴 ON → 200", r.status_code == 200 and r.json().get("archive_full_paid") == 1, r.text[:120])
    fb2 = feed(sid_b)
    check("ON 後の B は全部見える (before_start は True のまま)", titles(fb2) == titles(fa) and fb2.get("archive_full") is True and fb2.get("before_start") is True)
    r = client.post(f"/api/admin/students/{sid_b}/archive-access", json={"archive_full_paid": False}, headers=adm)
    check("B を OFF に戻す → 200", r.status_code == 200 and r.json().get("archive_full_paid") == 0)
    check("OFF 後の B は再び来月ぶんだけ", titles(feed(sid_b)) == ["来月ぶん 1/1"])
    r = client.post("/api/admin/students/999999/start-month", json={"start_month": next_m})
    check("未認証 → 401", r.status_code == 401)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT id FROM class_recordings WHERE title = ?", ("日付のない題名",)); rec_nd = c.fetchone()["id"]
    conn.close()
    r = client.post(f"/api/admin/class/recordings/{rec_nd}/lesson-date", json={"lesson_date": f"{this_m}-02"}, headers=adm)
    check("録画の授業日を今月に修正 → 200", r.status_code == 200 and r.json().get("lesson_date") == f"{this_m}-02", r.text[:120])
    check("修正後、今月開始の C に見える", "日付のない題名" in titles(feed(sid_c)))
    r = client.post(f"/api/admin/class/recordings/{rec_nd}/lesson-date", json={"lesson_date": "2026-13-40"}, headers=adm)
    check("不正な日付 → 400", r.status_code == 400)
    r = client.post(f"/api/admin/class/recordings/{rec_nd}/lesson-date", json={"lesson_date": ""}, headers=adm)
    check("空 → 自動判定に戻す (200・lesson_date None)", r.status_code == 200 and r.json().get("lesson_date") is None)
    check("戻した後、C には見えない", "日付のない題名" not in titles(feed(sid_c)))
    r = client.post("/api/admin/class/recordings/999999/lesson-date", json={"lesson_date": ""}, headers=adm)
    check("存在しない録画 → 404", r.status_code == 404)

    print("\n[6] 承認: 備考の受講開始月 → 新規生徒の start_month (既存への合流では入れない)")
    note = "AI学習アプリ: 申込なし\n受講開始月: 2026年10月（申込書の選択: 翌月から）\n"
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO course_applications (name, email, status, referrer, grade, subjects, note) VALUES (?,?,?,?,?,?,?)",
              ("承認テスト 新規", "parent-new@example.org", "pending", "入塾申込フォーム", "中3", CLASS, note))
    c.execute("SELECT id FROM course_applications WHERE email = ?", ("parent-new@example.org",)); app_new = c.fetchone()["id"]
    c.execute("INSERT INTO course_applications (name, email, status, referrer, grade, subjects, note) VALUES (?,?,?,?,?,?,?)",
              ("開始月テスト A", "sm-a@example.org", "pending", "入塾申込フォーム", "中3", CLASS, note))
    c.execute("SELECT id FROM course_applications WHERE email = ? AND status = 'pending'", ("sm-a@example.org",)); app_exist = c.fetchone()["id"]
    conn.commit(); conn.close()
    r = client.post(f"/api/admin/course-applications/{app_new}/approve", json={"ai_disabled": True, "merge_siblings": True}, headers=adm)
    check("新規の承認 → 200", r.status_code == 200, r.text[:200])
    jn = r.json() if r.status_code == 200 else {}
    check("response.start_month = 2026-10 (備考から)", jn.get("start_month") == "2026-10" and jn.get("start_month_from_note") == "2026-10", str({k: jn.get(k) for k in ("start_month", "start_month_from_note", "start_month_skipped_existing")}))
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT start_month FROM students WHERE id = ?", (jn.get("student_id") or -1,)); rr = c.fetchone()
    conn.close()
    check("新規生徒の students.start_month = 2026-10", rr is not None and rr["start_month"] == "2026-10", str(dict(rr) if rr else None))
    r = client.post(f"/api/admin/course-applications/{app_exist}/approve", json={"ai_disabled": True, "merge_siblings": True}, headers=adm)
    check("既存 (A) への合流の承認 → 200", r.status_code == 200, r.text[:200])
    je = r.json() if r.status_code == 200 else {}
    check("合流: start_month は入れず skipped_existing=True で知らせる", je.get("attached_existing") is True and je.get("start_month") is None and je.get("start_month_skipped_existing") is True, str({k: je.get(k) for k in ("attached_existing", "start_month", "start_month_from_note", "start_month_skipped_existing")}))
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT start_month FROM students WHERE id = ?", (sid_a,)); rr = c.fetchone()
    conn.close()
    check("A の start_month は NULL のまま (在籍生の録画を消さない)", rr is not None and not rr["start_month"], str(dict(rr) if rr else None))

    print("\n[7] admin_stats / 授業の詳細 / 統合 / cron の SQL")
    r = client.get("/api/admin/stats", headers=adm)
    st = {x["id"]: x for x in (r.json().get("students", []) if r.status_code == 200 else [])}
    check("admin_stats: B に start_month / before_start / archive_full_paid", r.status_code == 200 and st.get(sid_b, {}).get("start_month") == next_m and st.get(sid_b, {}).get("before_start") is True and st.get(sid_b, {}).get("archive_full_paid") == 0, str(st.get(sid_b, {}).get("start_month")))
    check("admin_stats: A は start_month None / before_start False", st.get(sid_a, {}).get("start_month") is None and st.get(sid_a, {}).get("before_start") is False)
    # 🎒 [2026-09-24] 生徒詳細の「在籍クラス」行: admin_stats が class_labels (配列) を返す。設定 API は時間割にある label だけ残す
    _lab = mod._TIMETABLE_CLASSES[1]["label"]   # make_student の初期値 (先頭の label) と違う label にして「書き込まれた」ことを固定
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/class/student-classes", json={"student_id": sid_a, "class_labels": [_lab, "存在しないクラス"]}, headers=adm)
    check("在籍クラス設定: 時間割にある label だけ残る", r.status_code == 200 and r.json().get("class_labels") == [_lab], r.text[:120])
    sid_c = make_student(mod, "クラス未設定テスト", "class-none@example.org")   # make_student は class_labels を入れるので API で空にする
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/class/student-classes", json={"student_id": sid_c, "class_labels": []}, headers=adm)
    check("在籍クラス設定: [] で全部外せる", r.status_code == 200 and r.json().get("class_labels") == [], r.text[:120])
    r = client.get("/api/admin/stats", headers=adm)
    st = {x["id"]: x for x in (r.json().get("students", []) if r.status_code == 200 else [])}
    check("admin_stats: class_labels を返す (A は設定した 1 クラス・未設定の C は [])", st.get(sid_a, {}).get("class_labels") == [_lab] and st.get(sid_c, {}).get("class_labels") == [], str((st.get(sid_a, {}).get("class_labels"), st.get(sid_c, {}).get("class_labels"))))
    r = client.get(f"/api/admin/class/sessions/{s1}/detail", headers=adm)
    recs = {x["title"]: x for x in (r.json().get("recordings", []) if r.status_code == 200 else [])}
    check("授業の詳細: 録画に lesson_date / lesson_date_effective", r.status_code == 200 and recs.get(f"{m_prev}/17", {}).get("lesson_date_effective") == f"{prev_m}-17" and recs.get("来月ぶん 1/1", {}).get("lesson_date") == f"{next_m}-01" and recs.get("日付のない題名", {}).get("lesson_date_effective") is None, str({k: (v.get("lesson_date"), v.get("lesson_date_effective")) for k, v in recs.items()}))
    check("統合の埋め込み列は archive_full_paid だけ (start_month は在籍生を縛る向きなので埋めない)", "archive_full_paid" in mod._MERGE_FILL_FIELDS and "start_month" not in mod._MERGE_FILL_FIELDS)
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/cron/midweek-nudge", params={"dry_run": "true"}, headers={"X-Cron-Secret": CRON_SECRET})
    check("水曜の一声 dry_run (start_month 条件つき SQL) → 200", r.status_code == 200, r.text[:160])
    r = client.post("/api/cron/weekly-reports", params={"dry_run": "true"}, headers={"X-Cron-Secret": CRON_SECRET})
    check("週次レポート dry_run (start_month 列つき SELECT) → 200", r.status_code == 200, r.text[:160])
    check("開始前の B は週次 dry_run の preview に居ない (活動なし → skip)", all(p.get("student_id") != sid_b for p in (r.json().get("preview") or [])) if r.status_code == 200 else False)

    print()
    if FAILURES:
        print(f"❌ FAIL: {len(FAILURES)} 件")
        for f in FAILURES:
            print("   -", f)
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
