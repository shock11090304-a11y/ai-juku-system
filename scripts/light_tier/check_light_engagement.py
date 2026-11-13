"""🌱 AI学習アプリ (light) の会員へのドリル配布と見守り (_run_light_engagement) の検査。

2026-11-14 塾長「新規の申込者が離脱しないように監視しながら適宜いい感じの問題を配布してあげて」。
一時 SQLite・外部通信なし・生徒名とメールは架空 (公開リポジトリ)。
実行: PYTHONUNBUFFERED=1 python3 scripts/light_tier/check_light_engagement.py
"""
import os, sys, tempfile, importlib.util, json, time
from datetime import datetime, timedelta, timezone

TMPDB = tempfile.mktemp(suffix=".db")
os.environ["DB_PATH"] = TMPDB
# ★★ 本番 DB 保護: USE_POSTGRES は DATABASE_URL の有無だけで決まる。このテストは students に書くので必ず空にする
os.environ["DATABASE_URL"] = ""
os.environ.setdefault("STRIPE_PRICE_PREMIUM", "price_test_dummy")
os.environ.setdefault("MAGIC_LINK_SECRET", "test-secret")
os.environ.setdefault("APP_SECRET", "test-secret")
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-dummy-for-local-test"
os.environ["GEMINI_API_KEY"] = "dummy-for-local-test"
os.environ["OPENAI_API_KEY"] = ""
os.environ["RESEND_API_KEY"] = ""          # メールは外へ出さない
os.environ["CRON_SECRET"] = "cron-test-secret"
for k in ("LIGHT_ENGAGE_ENABLED", "LIGHT_ENGAGE_EMAIL", "AUTO_DELIVERY_REVIEWED_SOURCES", "WEAKNESS_ROUTINE_OPEN_STALE_DAYS"):
    os.environ.pop(k, None)

MAIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "server", "main.py")
spec = importlib.util.spec_from_file_location("main", MAIN)
main = importlib.util.module_from_spec(spec)
sys.modules["main"] = main
spec.loader.exec_module(main)
if getattr(main, "USE_POSTGRES", False):
    raise SystemExit("ABORT: USE_POSTGRES=True。本番DBを掴んでいる可能性があるため中止します。")

from fastapi.testclient import TestClient

FAIL = []
N = [0]


def ok(cond, label):
    N[0] += 1
    print(("  ✓ " if cond else "  ✗ ") + label)
    if not cond:
        FAIL.append(label)


ROUTINE = main._WEAKNESS_ROUTINE_CREATED_BY
NOW = datetime(2026, 11, 14, 3, 0, tzinfo=timezone.utc)   # JST 12:00
TRIAL_END = "2026-11-16 03:00:00"


def q(sql, params=()):
    conn = main.db(); c = conn.cursor()
    c.execute(sql, params)
    rows = c.fetchall()
    conn.close()
    return rows


def ex(sql, params=()):
    conn = main.db(); c = conn.cursor()
    c.execute(sql, params)
    conn.commit(); conn.close()


def mkstudent(sid, email, *, grade="高校1年", plan="trillion_light", tier="light", status="trial",
              trial_end=TRIAL_END, name="仮名 花子", last_login=None, created="2026-11-14 01:00:00", mail_on=1):
    ex("DELETE FROM students WHERE id = ? OR LOWER(email) = ?", (sid, email))
    ex("INSERT INTO students (id, name, email, grade, plan, feature_tier, status, trial_end, last_login_at, created_at, "
       "parent_email_enabled) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
       (sid, name, email, grade, plan, tier, status, trial_end, last_login, created, mail_on))


def _max_assign_id():
    r = q("SELECT MAX(id) AS m FROM grammar_drill_assignments")
    return int(r[0]["m"] or 0) if r else 0


def run(now, **kw):
    """_run_light_engagement を now で回し、その回に作った行の assigned_at・sent_at を now にそろえる
    (DB の既定は実際の時刻なので、そのままだとテストの日付と食い違う)。"""
    before = _max_assign_id()
    nb = int(q("SELECT COALESCE(MAX(id), 0) AS m FROM notifications")[0]["m"])
    res = main._run_light_engagement(now=now, **kw)
    ts = now.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    ex("UPDATE grammar_drill_assignments SET assigned_at = ? WHERE id > ?", (ts, before))
    ex("UPDATE notifications SET sent_at = ? WHERE id > ?", (ts, nb))
    return res


def drills_of(sid):
    return q("SELECT d.id, d.title, d.subject, d.level, d.question_ids, d.created_by, a.status, a.assigned_at "
             "FROM grammar_drill_assignments a JOIN grammar_drills d ON d.id = a.drill_id "
             "WHERE a.student_id = ? ORDER BY a.id", (sid,))


# ── レビュー済みの在庫 (英文法・数学・中学英語) と、自動配信に出してはいけない出典の行 ──
def seed_questions():
    rows = []
    for subj, src, units in (("english", "manual-drill-v1", ("時制", "関係詞")),
                             ("math", "mathct-2026", ("数学I 二次関数", "数学III 極限")),
                             ("chugaku", "chugaku-drill-v1", ("be動詞", "一般動詞"))):
        for unit in units:
            for lv in ("basic", "standard", "advanced"):
                for i in range(8):
                    rows.append((subj, unit, lv, f"{subj}-{unit}-{lv}-{i}", json.dumps(["a", "b", "c", "d"]), 0, "解説", src))
    for i in range(40):   # 未レビュー (pool) の英文法: 自動配信には出ない
        rows.append(("english", "時制", "basic", f"pool-{i}", json.dumps(["a", "b"]), 0, "", "pool"))
    conn = main.db(); c = conn.cursor()
    for row in rows:
        c.execute("INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) "
                  "VALUES (?, ?, ?, ?, ?, ?, ?, ?)", row)
    conn.commit(); conn.close()


seed_questions()
POOL_IDS = {int(r["id"]) for r in q("SELECT id FROM grammar_questions WHERE source = 'pool'")}
MATH3_IDS = {int(r["id"]) for r in q("SELECT id FROM grammar_questions WHERE unit LIKE '数学III%'")}

print("\n[A] 申し込んだばかりの会員 (弱点のデータなし) に「はじめの力だめし」")
mkstudent(9501, "le-new@example.com")
r = run(NOW, seed=1)
d = drills_of(9501)
ok(r["delivered"] == 1 and r["delivered_starter"] == 1 and len(d) == 1, f"1 本だけ配る {r}")
if d:
    qids = json.loads(d[0]["question_ids"])
    ok(d[0]["title"].startswith("🌱はじめの力だめし 英文法ドリル（基礎・標準・10問）"), f"見出し: {d[0]['title']}")
    ok(d[0]["subject"] == "english" and d[0]["level"] == "basic,standard", f"高校生は英文法・基礎と標準 ({d[0]['subject']}, {d[0]['level']})")
    ok(len(qids) == 10 and not (set(qids) & POOL_IDS), "★10 問・レビュー済みの出典だけ (pool の行は出ない)")
    ok(d[0]["created_by"] == ROUTINE and d[0]["status"] == "open", "3日ドリルと同じ印 (錠と読み直しが効く)")
_dump = json.dumps(r, ensure_ascii=False)
ok(r["delivered_ids"] and all(not ({"name", "email"} & set(e)) for e in r["delivered_ids"])
   and "仮名" not in _dump and "@example" not in _dump, "★結果に名前・メールを入れない")

print("\n[B] 未提出の間は積まない・解き終えても同じ日は配らない・次の日に次の 10 問")
r = run(NOW + timedelta(hours=1))
ok(r["delivered"] == 0 and r["skipped_open"] == 1 and len(drills_of(9501)) == 1, f"未提出が残っている → 配らない {r}")
ex("UPDATE grammar_drill_assignments SET status = 'completed' WHERE student_id = 9501")
r = run(NOW + timedelta(hours=2))
ok(r["delivered"] == 0 and r["skipped_today"] == 1, f"解き終えても同じ日 (JST) は配らない {r}")
r = run(NOW + timedelta(days=1), seed=2)
d = drills_of(9501)
ok(r["delivered_rotation"] == 1 and len(d) == 2, f"次の日に次の 10 問 {r}")
if len(d) == 2:
    qids2 = json.loads(d[1]["question_ids"])
    ok(d[1]["subject"] == "math" and d[1]["title"].startswith("📝おすすめ 数学ドリル（標準・やや難・10問）"),
       f"2 本目は受け取っていない科目 (数学)・ふだんのレベル: {d[1]['title']}")
    ok(not (set(qids2) & MATH3_IDS), "★数学III は自動配信に出さない")

print("\n[C] 中学生・学年が読めない・小学生")
mkstudent(9502, "le-chu@example.com", grade="中学2年")
mkstudent(9503, "le-unknown@example.com", grade="")
mkstudent(9504, "le-sho@example.com", grade="小学5年")
r = run(NOW, seed=3)
d = drills_of(9502)
ok(len(d) == 1 and d[0]["subject"] == "chugaku" and d[0]["level"] == "basic,standard", f"中学2年 → 中学英語・基礎と標準 {[dict(x) for x in d]}")
ok(not drills_of(9503) and not drills_of(9504) and r["skipped_grade"] >= 2, "★学年が読めない・小学生には配らない (中高の取り違えをしない)")

print("\n[D] 対象外: AI学習アプリでない・体験が切れた・合成監視・解約")
mkstudent(9505, "le-std@example.com", plan="standard", tier="full")
mkstudent(9506, "le-expired@example.com", trial_end="2026-11-13 00:00:00")
mkstudent(9507, "le-mon@synthetic-monitor.example", grade="高校2年")
mkstudent(9508, "le-cancel@example.com", status="canceled")
mkstudent(9509, "le-paid@example.com", status="paid", trial_end=None)
r = run(NOW, seed=4)
ok(not drills_of(9505) and not drills_of(9506) and not drills_of(9507) and not drills_of(9508),
   "★本体プラン・体験切れ・合成監視・解約には配らない")
ok(len(drills_of(9509)) == 1, "支払い中の会員には配る")

print("\n[E] dry-run は何も書かない・1 名だけ")
mkstudent(9510, "le-dry@example.com")
r = run(NOW, only_student_id=9510, dry_run=True)
ok(r["dry_run"] and r["delivered"] == 1 and not drills_of(9510) and r["targets"] == 1, f"dry-run: 数えるが書かない {r}")

print("\n[F] 弱点のデータがあれば弱点ドリル (3日ドリルと同じ選び方)")
_orig_plan = main._weakness_routine_plan
def _fake_plan(c, st, band, **kw):
    rows = q("SELECT id FROM grammar_questions WHERE subject='english' AND unit='関係詞' AND level IN ('standard','advanced') "
             "AND source='manual-drill-v1' ORDER BY id LIMIT 10")
    return {"ok": True, "subject": "english", "unit": "関係詞", "label": "関係詞", "levels": ["standard", "advanced"],
            "qids": [int(x["id"]) for x in rows], "reviewed_available": 16, "unseen_available": 16, "reused_seen": 0}
main._weakness_routine_plan = _fake_plan
try:
    r = run(NOW, only_student_id=9510)
finally:
    main._weakness_routine_plan = _orig_plan
d = drills_of(9510)
ok(r["delivered_weakness"] == 1 and len(d) == 1 and d[0]["title"].startswith("🎯弱点対策 関係詞ドリル"), f"弱点ドリル {r}")

print("\n[G] 毎朝の 3日ドリルと二重にならない")
mkstudent(9511, "le-both@example.com")
run(NOW, only_student_id=9511)
cut = main._light_engage_cutoffs(NOW)
st = q("SELECT id, name, email, line_user_id, grade FROM students WHERE id = 9511")[0]
qs = [int(x["id"]) for x in q("SELECT id FROM grammar_questions WHERE subject='english' AND source='manual-drill-v1' ORDER BY id DESC LIMIT 10")]
conn = main.db(); c = conn.cursor()
res = main._create_routine_grammar_drill(c, conn, "english", "", 10, 9511, st, band="kosei", qids=qs, cutoffs=cut)
conn.close()
ok(isinstance(res, dict) and res.get("race") and len(drills_of(9511)) == 1, f"★同じ生徒に 2 本目を作らない (錠の中の読み直し) {res}")
r = main._run_weakness_drill_routine(only_student_id=9511, now=NOW)
ok(r.get("delivered", 0) == 0 and len(drills_of(9511)) == 1, "毎朝の 3日ドリルも積まない")
ok(main._create_routine_grammar_drill.__kwdefaults__.get("title_prefix") == "🎯弱点対策", "3日ドリルの見出しは今までどおり")

print("\n[H] メール: 既定は送らない・ON なら新しいドリルと催促を 1 回だけ (体験中は 1 日・支払い中は 2 日)")
mkstudent(9512, "le-mail@example.com", created="2026-11-12 00:00:00")
r = run(NOW, only_student_id=9512)
ok(r["email_enabled"] is False and r.get("emails_pending") == 1 and r["emails_sent"] == 0
   and not q("SELECT 1 FROM notifications WHERE student_id = 9512"), f"★既定 (LIGHT_ENGAGE_EMAIL なし) はメールを送らない {r}")
sent = []
fail_mode = [False]
_orig_send = main._send_light_engage_email
def _fake_send(to, name, kind, title, te=None):
    sent.append((to, kind, title, te))
    return {"sent": False, "error": "boom"} if fail_mode[0] else {"sent": True}
main._send_light_engage_email = _fake_send
try:
    mkstudent(9513, "le-mail2@example.com", trial_end="2026-11-20 00:00:00", created="2026-11-12 00:00:00")
    r = run(NOW, only_student_id=9513, send_email=True)
    ok(r["emails_sent"] == 1 and sent and sent[-1][1] == "new" and "はじめの力だめし" in sent[-1][2]
       and sent[-1][3] is not None, f"ON: 新しいドリルのお知らせ (体験の終わりの日時つき) {sent}")
    rows = q("SELECT success, error FROM notifications WHERE student_id = 9513")
    ok(len(rows) == 1 and int(rows[0]["success"]) == 1 and rows[0]["error"] is None, "送った記録 (送信中 → 送れた に書き換え)")
    r = run(NOW + timedelta(hours=12), only_student_id=9513, send_email=True)
    ok(r["emails_sent"] == 0, "半日では催促しない")
    r = run(NOW + timedelta(days=1, hours=1), only_student_id=9513, send_email=True)
    ok(r["emails_sent"] == 1 and sent[-1][1] == "reminder", f"体験中は 1 日たっても開いていなければ催促 {sent[-1][1]}")
    r = run(NOW + timedelta(days=1, hours=2), only_student_id=9513, send_email=True)
    ok(r["emails_sent"] == 0, "★同じドリルの催促は 2 回送らない")
    # レプリカが 2 つ: 同じ催促の権利を 2 回は取れない
    conn = main.db(); c = conn.cursor()
    a1 = main._light_engage_claim_mail(c, conn, 9513, "light_drill_test", 999, "2026-11-14 00:00:00")
    a2 = main._light_engage_claim_mail(c, conn, 9513, "light_drill_test", 999, "2026-11-14 00:00:00")
    conn.close()
    ok(a1 is not None and a2 is None, "★送る権利は 1 回だけ取れる (送信中の行があれば 2 本目は送らない)")
    # 支払い中の会員は 2 日で
    mkstudent(9516, "le-mail3@example.com", status="paid", trial_end=None, created="2026-11-01 00:00:00")
    run(NOW, only_student_id=9516, send_email=True)
    n0 = len(sent)
    r = run(NOW + timedelta(days=1, hours=1), only_student_id=9516, send_email=True)
    ok(r["emails_sent"] == 0, "支払い中の会員は 1 日では催促しない")
    r = run(NOW + timedelta(days=2, hours=1), only_student_id=9516, send_email=True)
    ok(r["emails_sent"] == 1 and sent[-1][1] == "reminder" and sent[-1][3] is None, "支払い中は 2 日で催促 (体験の案内なし)")
    # 送れなかったら: 同じ日は送り直さない・次の日にもう一度・3 回で止める
    fail_mode[0] = True
    mkstudent(9517, "le-fail@example.com", status="paid", trial_end=None, created="2026-11-01 00:00:00")
    run(NOW, only_student_id=9517, send_email=True)          # new: 失敗 1 回目 (new は作った回だけ)
    tries = []
    for h in (49, 50, 73, 97, 121):
        r = run(NOW + timedelta(hours=h), only_student_id=9517, send_email=True)
        tries.append(r["emails_failed"])
    ok(tries == [1, 0, 1, 1, 0], f"★送れなかった催促は 1 日 1 回・3 回まで {tries}")
    fail_mode[0] = False
    # お知らせのメールを止めた会員には送らない
    mkstudent(9518, "le-optout@example.com", created="2026-11-01 00:00:00", mail_on=0)
    r = run(NOW, only_student_id=9518, send_email=True)
    ok(r["delivered"] == 1 and r["emails_sent"] == 0 and r["emails_failed"] == 0, "★parent_email_enabled=0 の会員には送らない")
    # 登録したばかり (ウェルカムメールが届く) の会員には新しいドリルのメールを重ねない
    mkstudent(9515, "le-fresh@example.com")
    r = run(NOW, only_student_id=9515, send_email=True)
    ok(r["delivered"] == 1 and r["emails_sent"] == 0, "★登録から 24 時間以内はドリルのメールを送らない (ウェルカムメールと重ねない)")
    # 毎日使っている会員には新しいドリルのメールを送らない
    mkstudent(9514, "le-active@example.com", last_login="2026-11-14 02:30:00", created="2026-11-10 00:00:00")
    r = run(NOW, only_student_id=9514, send_email=True)
    ok(r["delivered"] == 1 and r["emails_sent"] == 0, "24 時間以内にログインした会員には送らない")
finally:
    main._send_light_engage_email = _orig_send
t = main._light_engage_email_text("new", "🌱はじめの力だめし 英文法ドリル（基礎・標準・10問）",
                                  datetime(2026, 11, 16, 12, 0, tzinfo=main.JST), "仮名 花子")
ok("月額2,500円" in t["body"] and "11月16日 12時00分" in t["body"] and "通常" not in t["body"]
   and "お申し込みの日から有料" in t["body"] and "料金はかかりません" in t["body"], "文面: 体験の終わり・月額・有料になる日 (「通常価格」と書かない)")
ok(t["subject"].startswith("【トリリオン AI学習アプリ】仮名 花子さんの") and "分" not in t["body"].split("\n")[1],
   "文面: 保護者あて (〇〇さんの)・所要時間を書かない")

print("\n[I] 見守り (人数だけ)")
_fc = main.db()
f = main._light_engagement_funnel(_fc.cursor(), NOW)
_fc.close()
ok(f["members"] >= 10 and f["in_trial"] >= 1 and f["paying"] >= 1 and f["trial_ended_unpaid"] >= 1, f"人数 {f}")
ok(f["drills_30d"]["completed"] >= 1 and f["members_completed_any"] >= 1, "解き終えた本数と人数")
ok(f["no_grade"] >= 1, f"学年が無い・読めない会員の数 (ドリルが届かない) {f['no_grade']}")
ok(all(isinstance(v, (int, dict)) for v in f.values()) and "仮名" not in json.dumps(f, ensure_ascii=False), "★人数だけ (名前・id なし)")

print("\n[J] admin API・申込の直後・スケジューラの登録")
client = TestClient(main.app)
ok(client.get("/api/admin/light/engagement").status_code == 401, "認証なしは 401")
j = client.get("/api/admin/light/engagement", headers={"X-Cron-Secret": "cron-test-secret"}).json()
ok(j.get("ok") and "funnel" in j and j.get("enabled") is True and j.get("email_enabled") is False, f"見守りを返す {list(j)}")
j = client.post("/api/admin/light/engagement/run", json={}, headers={"X-Cron-Secret": "cron-test-secret"}).json()
ok(j.get("dry_run") is True, "手動実行の既定は dry-run")
main.LIGHT_SIGNUP_OPEN = True
main.LIGHT_PAID_CAP = 0
main._send_magic_link_with_retry = lambda *a, **k: {"sent": True}
r = client.post("/api/trial/signup", json={"name": "仮名 次郎", "grade": "高校2年", "plan": "trillion_light",
                                          "email": "le-signup@example.com"})
ok(r.status_code == 200 and r.json().get("light_trial_granted") is True, f"体験の申込 {r.status_code}")
sid = r.json().get("student_id")
got = []
for _ in range(40):
    got = drills_of(sid)
    if got:
        break
    time.sleep(0.1)
ok(len(got) == 1 and got[0]["title"].startswith("🌱はじめの力だめし"), "★申込の直後に最初のドリルが入っている (毎時の見回りを待たない)")
# 決済から直接入った会員 (学年なし) がマイページで学年を選ぶ → すぐ最初のドリル
mkstudent(9520, "le-nograde@example.com", grade=None, status="paid", trial_end=None)
tok = main._sign_session_token(9520)
r = client.patch("/api/student/profile", json={"student_id": 9520, "grade": "中学3年"},
                 headers={"Authorization": f"Bearer {tok}"})
got = []
for _ in range(40):
    got = drills_of(9520)
    if got:
        break
    time.sleep(0.1)
ok(r.status_code == 200 and len(got) == 1 and got[0]["subject"] == "chugaku", f"★学年を選んだらすぐ最初のドリル ({r.status_code}, {len(got)})")
r = client.patch("/api/student/profile", json={"student_id": 9505, "grade": "高校3年"},
                 headers={"Authorization": f"Bearer {main._sign_session_token(9505)}"})
time.sleep(0.5)
ok(r.status_code == 200 and not drills_of(9505), "本体プランの生徒が学年を変えても配らない")
mp = open(os.path.join(os.path.dirname(MAIN), "..", "mypage.html"), encoding="utf-8").read()
ok('id="lightGradePrompt"' in mp and "/api/student/profile" in mp and "'PATCH'" in mp, "マイページに学年を聞く欄 (AI学習アプリ・学年なし)")
ok("send_email=False" in src_new if (src_new := open(MAIN, encoding="utf-8").read()) else False,
   "★申込の直後・学年の直後の配布ではメールを送らない")
os.environ["LIGHT_ENGAGE_ENABLED"] = "0"
ok(main._light_engage_enabled() is False, "LIGHT_ENGAGE_ENABLED=0 で止まる")
os.environ.pop("LIGHT_ENGAGE_ENABLED", None)
src = open(MAIN, encoding="utf-8").read()
ok("asyncio.create_task(_light_engagement_scheduler())" in src, "スケジューラを起動時に登録")
ok(src.count('"light_engagement_run": "AI学習アプリ会員へのドリル配布 (毎時20分)"') == 2, "停止・失敗の通知のラベル")
ok("light_engagement_run" in main._SCHEDULER_MAX_AGE_DAYS, "止まったら監視が拾う (_SCHEDULER_MAX_AGE_DAYS)")

try:
    os.unlink(TMPDB)
except OSError:
    pass
print(f"\n{N[0] - len(FAIL)}/{N[0]} passed")
if FAIL:
    print("FAILED:")
    for x in FAIL:
        print("  - " + x)
    sys.exit(1)
