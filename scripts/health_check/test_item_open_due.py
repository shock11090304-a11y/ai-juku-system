#!/usr/bin/env python3
"""⏰ 〆の印と帯・👀 開いたかの記録 (2026-10-18 塾長「②の残りも作っておいて」= 成績を上げる提案 ②「入口の壁を取る」) の回帰テスト。

背景: クラス自動宿題の 〆 は題名の文字 (「〆10/20」) にしかなく、塾生アプリの帯が出るのは「新しい宿題」と「期限切れの宿題 (塾長の宿題だけ)」の
  ときだけだった (宿題タブを一度開くと 〆 を過ぎても何も出ない)。また、生徒が宿題・ドリルを開いたかをサーバが記録しておらず、未提出が
  「見ていない」のか「開いたが出していない」のかを塾長が分けられなかった。

固定する性質 (一時 SQLite・外部通信なし・生徒名とメールは架空 = 公開リポジトリ):
  [1] サーバ: GET /api/student/grammar-drills の due_date = クラス自動宿題の題名の「〆M/D」(授業ブリーフと同じ _class_brief_title_due・
      年は受け取った日 (JST) から・12 月の「〆1/2」は翌年)。ほかのドリル (〆を書いた塾長のドリルも)・〆の無い題名・受け取った日時の無い行は None
  [2] サーバ: 開いたの記録。GET /api/student/grammar-drill/{id} (本人・未提出) と POST /api/student/homework/{id}/opened が events
      gd_open / hw_open に 1 件 1 行 (session_id = 生徒 ID・props は ID と時刻だけ = 名前・メールなし)。同じ JST の日は何も書かない
      (23:59:59 と 0:00:00 の境目)・別の日は同じ行の last_opened と days だけ・created_at (初めて開いた時刻) は変えない。
      提出済み・自分で始めたもの (今日の1問)・塾長のなりすまし・他人のドリル / 宿題 (404)・未ログイン (401) は記録しない。
      AIなし枠でも通る (許可集合は不変)・保持期限 (_EVENTS_RETENTION) で消えない・書けなくても例外を出さない・ログに名前を出さない
  [3] 授業ブリーフ: 未提出の行の opened = True (開いたが未提出・最後に開いた日 M/D・日数) / False (記録が始まった後に配ったのに記録なし = 未開封) /
      None (記録が始まる前に配った分 = 分からない)・生徒の unopened_count。競合で 2 行になっても早い方の初回・遅い方の最後。読むだけ (events も増えない)
  [4] hw-notice.js (JS エンジン・TZ=America/Los_Angeles): dueState の JST の 0:00 の境目・compute の overdue / dueToday (ドリルの 〆 も・
      提出済みは数えない)・banner (新着 + 〆の数 / 〆を過ぎた / 〆今日 / なし・「見た」に関係なく出る)・todoLabel・チップの文言
  [5] class.html (偽の DOM・TZ=America/Los_Angeles): 予定タブの帯は宿題タブを見た後も 〆 のあいだ出る・提出したら消える・
      ドリルと宿題のカードに「〆今日」「〆を過ぎました」・👀 の POST (中身だけの宿題は一覧に出たら・解答用紙・プリント・
      「📝 ドリルで解く」(keepalive)・提出済みは送らない・このページで 1 件 1 回・予定タブでは送らない)
  [6] mypage.js (偽の DOM・TZ=America/Los_Angeles): ドリルと宿題のカードの 〆 (端末の日付ではなく JST)・📌 要対応チップと欄のバッジの 〆・
      👀 の POST (中身だけの宿題 (単元のある宿題も = マイページには「📝 ドリルで解く」が無い) は**そのカード**が半分以上 1.5 秒見えたら・
      宿題欄が見えただけ / ドリルを開いただけでは送らない (点検 owner-F1)・解答用紙・PDF)
  [7] CEO の 🗓 授業ブリーフ (ceo.html の本物のコード): 「👀 未開封」「開いたが未提出 (M/D)」「👀 未開封 N」・null と古いサーバでは出さない・escape
  [8] ソース検査: ルートは /api/student/homework/ の下・許可集合は不変・hw-notice.js の ?v= が 2 ページでそろう・CI 登録

★JS エンジンが無ければ FAIL (飛ばさない)。CI (ubuntu) は node、塾長の Mac は osascript -l JavaScript。AJ_JS_ENGINE で選べる。

実行:
    python3 scripts/health_check/test_item_open_due.py
    # exit 0 = PASS / 1 = FAIL
"""
import datetime
import importlib.util
import json
import logging
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MAIN_PY = os.path.join(REPO, "server", "main.py")
HW_JS = os.path.join(REPO, "hw-notice.js")
CLASS_HTML = os.path.join(REPO, "class.html")
MYPAGE_HTML = os.path.join(REPO, "mypage.html")
MYPAGE_JS = os.path.join(REPO, "mypage.js")
CEO_HTML = os.path.join(REPO, "ceo.html")
CI_YML = os.path.join(REPO, ".github", "workflows", "server-tests.yml")
HW_NOTICE_TEST = os.path.join(HERE, "test_hw_notice_js.py")
UTC = datetime.timezone.utc
L2 = "月曜2限 英文法 Lv.1"
TZ_ENV = {"TZ": "America/Los_Angeles"}   # 端末のタイムゾーンが JST でなくても JST で出す (UTC−7 で「端末任せ」なら落ちる)

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:500]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------------------------------------------
# サーバ
def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="item_open_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと **本番 Postgres** に書き込む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0", "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "", "ANTHROPIC_API_KEY": "", "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_item_open", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def ex(mod, sql, params=()):
    conn = mod.db(); c = conn.cursor()
    c.execute(sql, params)
    rid = None
    try:
        r = c.fetchone()
        rid = r[0] if r is not None else None
    except Exception:
        rid = None
    conn.commit(); conn.close()
    return rid


def q(mod, sql, params=()):
    conn = mod.db(); c = conn.cursor()
    c.execute(sql, params)
    out = [dict(r) for r in c.fetchall()]
    conn.close()
    return out


def opens(mod, name=None):
    rows = q(mod, "SELECT id, name, session_id, props, created_at FROM events WHERE name IN ('gd_open', 'hw_open') ORDER BY id")
    return [r for r in rows if name is None or r["name"] == name]


class Fx:
    def __init__(self, mod):
        self.mod, self.ids, self.seq = mod, {}, 0

    def student(self, key, name, *, ai_disabled=1, plan="student_addon", course=None, labels=(L2,), grade="高2"):
        self.seq += 1
        sid = ex(self.mod,
                 "INSERT INTO students (name, email, status, grade, ai_disabled, plan, course, class_labels, last_login_at) "
                 "VALUES (?, ?, 'paid', ?, ?, ?, ?, ?, '2026-10-18 01:00:00') RETURNING id",
                 (name, f"item-open-{key.lower()}-{self.seq:03d}@example.org", grade, ai_disabled, plan, course, json.dumps(list(labels), ensure_ascii=False)))
        self.ids[key] = sid
        self.mod._AI_DISABLED_CACHE.pop(sid, None)
        return sid

    def question(self, key):
        self.ids[key] = ex(self.mod, "INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) "
                                     "VALUES ('english', '時制', 'standard', ?, ?, 1, '架空の解説', 'manual-drill-v1') RETURNING id",
                           (f"架空の問題 {key} ( ) ?", json.dumps(["a", "b", "c", "d"])))
        return self.ids[key]

    def drill(self, key, created_by, title, qkeys=("q1", "q2")):
        self.ids[key] = ex(self.mod, "INSERT INTO grammar_drills (subject, title, unit, level, question_ids, created_by) "
                                     "VALUES ('english', ?, '時制', 'standard', ?, ?) RETURNING id",
                           (title, json.dumps([self.ids[k] for k in qkeys]), created_by))
        return self.ids[key]

    def assign(self, dkey, skey, *, assigned_at, status="open"):
        ex(self.mod, "INSERT INTO grammar_drill_assignments (drill_id, student_id, status, assigned_at, score_total) VALUES (?, ?, ?, ?, 2)",
           (self.ids[dkey], self.ids[skey], status, assigned_at))

    def homework(self, key, skey, title, *, due=None, created_at="2026-10-18 03:00:00", status="open", topic=None):
        self.ids[key] = ex(self.mod,
                           "INSERT INTO homework_assignments (student_id, title, subject, topic, due_date, status, created_at, created_by) "
                           "VALUES (?, ?, 'english', ?, ?, ?, ?, 'admin') RETURNING id",
                           (self.ids[skey], title, topic, due, status, created_at))
        return self.ids[key]


def check_server():
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    f = Fx(mod)
    A = f.student("A", "架空 開封一郎")                                          # 塾生アプリのみ枠 (AIなし)
    B = f.student("B", "架空 開封次郎", ai_disabled=0, plan=None, course="kokuritsu_nankan")   # AIあり
    f.question("q1"); f.question("q2")
    chw = f"class_hw_auto:kosei:{L2}"
    f.drill("DC1", chw, f"【{L2}】宿題 時制（2問・〆10/20）"); f.assign("DC1", "A", assigned_at="2026-10-17 21:00:05")   # = JST 10/18 06:00
    f.drill("DY", chw, f"【{L2}】宿題 比較（2問・〆1/2）"); f.assign("DY", "A", assigned_at="2026-12-28 03:00:00")
    f.drill("DN", chw, f"【{L2}】宿題 〆の無い題名"); f.assign("DN", "A", assigned_at="2026-10-17 21:00:05")
    f.drill("DA", "admin", "塾長のドリル（〆10/25）"); f.assign("DA", "A", assigned_at="2026-10-17 01:00:00")
    f.drill("DT", "today_question", "📝 今日の1問"); f.assign("DT", "A", assigned_at="2026-10-18 01:00:00")
    f.drill("DD", chw, f"【{L2}】宿題 済み（2問・〆10/18）"); f.assign("DD", "A", assigned_at="2026-10-15 21:00:00", status="completed")
    f.drill("DS", "weakness_routine_3d", "🎯 3日ドリル 時制"); f.assign("DS", "A", assigned_at="2026-10-17 20:30:00", status="assigned")
    f.drill("DB", "admin", "B だけのドリル"); f.assign("DB", "B", assigned_at="2026-10-17 01:00:00")
    HA = f.homework("HA", "A", "架空プリント 音読")
    HAc = f.homework("HAc", "A", "架空プリント 済み", status="completed")
    HB = f.homework("HB", "B", "B の宿題")
    tok = lambda sid, tt="session": {"Authorization": "Bearer " + mod._sign_session_token(sid, token_type=tt)}   # noqa: E731
    HA_, HB_ = tok(A), tok(B)
    IMP_A = tok(A, "impersonation")

    print("\n[1] GET /api/student/grammar-drills の due_date (クラス自動宿題の 〆)")
    r = client.get("/api/student/grammar-drills", headers=HA_)
    check("AIなし枠でも一覧は 200", r.status_code == 200, (r.status_code, r.text[:200]))
    items = {it["drill_id"]: it for it in (r.json().get("items") or [])} if r.status_code == 200 else {}
    ids = f.ids
    check("クラス自動宿題「〆10/20」→ due_date 2026-10-20 (受け取った日 = JST 10/18)", items.get(ids["DC1"], {}).get("due_date") == "2026-10-20",
          items.get(ids["DC1"]))
    check("12/28 に受け取った「〆1/2」は翌年 2027-01-02", items.get(ids["DY"], {}).get("due_date") == "2027-01-02", items.get(ids["DY"]))
    check("〆の無い題名・〆を書いた塾長のドリル・今日の1問・3日ドリルは None",
          all(items.get(ids[k], {}).get("due_date", "x") is None for k in ("DN", "DA", "DT", "DS")),
          {k: items.get(ids[k], {}).get("due_date", "x") for k in ("DN", "DA", "DT", "DS")})
    check("提出済みのクラス自動宿題にも due_date (画面は未提出だけに出す)", items.get(ids["DD"], {}).get("due_date") == "2026-10-18", items.get(ids["DD"]))
    check("読み方は授業ブリーフと 1 か所 (_student_drill_due_date → _class_brief_title_due)",
          mod._student_drill_due_date(chw, "【x】宿題（10問・〆10/23）", "2026-10-21 21:00:05") == "2026-10-23"
          and mod._student_drill_due_date(chw, "〆10/23", None) is None
          and mod._student_drill_due_date("admin", "〆10/23", "2026-10-21 21:00:05") is None
          and mod._student_drill_due_date(chw, "〆2/30", "2026-02-01 00:00:00") is None
          and "_class_brief_title_due(" in __import__("inspect").getsource(mod._student_drill_due_date))

    print("\n[2] 開いたの記録 (events gd_open / hw_open)")
    recs = []

    class H(logging.Handler):
        def emit(self, rec):
            try:
                recs.append(rec.getMessage())
            except Exception:
                recs.append(str(rec.msg))
    hnd = H(level=logging.DEBUG)
    root = logging.getLogger()
    root.addHandler(hnd)
    old_level = root.level
    root.setLevel(logging.DEBUG)
    try:
        r = client.get(f"/api/student/grammar-drill/{ids['DC1']}", headers=HA_)
        check("本人が未提出のドリルを開く (AIなし枠) = 200", r.status_code == 200, (r.status_code, r.text[:200]))
        g = opens(mod, "gd_open")
        check("gd_open が 1 行", len(g) == 1, g)
        p = json.loads(g[0]["props"]) if g else {}
        check("session_id = 生徒 ID の文字列・props は ID と時刻だけ (student_id / kind / item_id / last_opened / days)",
              g and g[0]["session_id"] == str(A) and set(p) == {"student_id", "kind", "item_id", "last_opened", "days"}
              and p.get("student_id") == A and p.get("kind") == "gd" and p.get("item_id") == ids["DC1"] and p.get("days") == 1, (g, p))
        check("props に名前・メールが無い", g and "架空" not in g[0]["props"] and "@" not in g[0]["props"], g)
        created0 = g[0]["created_at"] if g else None
        r = client.get(f"/api/student/grammar-drill/{ids['DC1']}", headers=HA_)
        g2 = opens(mod, "gd_open")
        check("同じ日にもう一度開いても行も props も変わらない", r.status_code == 200 and len(g2) == 1 and g2[0]["props"] == g[0]["props"], g2)
        for key, label in (("DD", "提出済み (復習)"), ("DT", "今日の1問 (自分で始めた)")):
            r = client.get(f"/api/student/grammar-drill/{ids[key]}", headers=HA_)
            check(f"{label} は開いても記録しない", r.status_code == 200 and len(opens(mod, "gd_open")) == 1, (r.status_code, opens(mod, "gd_open")))
        r = client.get(f"/api/student/grammar-drill/{ids['DS']}", headers=IMP_A)
        check("塾長のなりすましで開いても記録しない", r.status_code == 200 and len(opens(mod, "gd_open")) == 1, (r.status_code, opens(mod, "gd_open")))
        r = client.get(f"/api/student/grammar-drill/{ids['DS']}", headers=HA_)
        check("予約タスクの 'assigned' も未提出 = 記録する", r.status_code == 200 and len(opens(mod, "gd_open")) == 2, opens(mod, "gd_open"))
        r = client.get(f"/api/student/grammar-drill/{ids['DB']}", headers=HA_)
        check("他人のドリルは 404・記録しない", r.status_code == 404 and len(opens(mod, "gd_open")) == 2, r.status_code)
        r = client.get(f"/api/student/grammar-drill/{ids['DC1']}")
        check("未ログインは 401", r.status_code == 401, r.status_code)

        check("初めて開いた時刻 = created_at (naive UTC)", bool(created0))
        # JST の日付の境目 (_record_item_open に now を渡す・今日の日付に依らないように別の ID で)
        conn = mod.db()
        try:
            t1 = datetime.datetime(2026, 10, 19, 1, 0, 0, tzinfo=UTC)       # JST 10/19 10:00
            t2 = datetime.datetime(2026, 10, 19, 14, 59, 59, tzinfo=UTC)    # JST 10/19 23:59:59
            t3 = datetime.datetime(2026, 10, 19, 15, 0, 0, tzinfo=UTC)      # JST 10/20 00:00:00
            res = [mod._record_item_open(conn, A, "gd", ids["DN"], now=t1), mod._record_item_open(conn, A, "gd", ids["DN"], now=t2),
                   mod._record_item_open(conn, A, "gd", ids["DN"], now=t3), mod._record_item_open(conn, A, "gd", ids["DN"], now=t3)]
        finally:
            conn.close()
        g3 = [x for x in opens(mod, "gd_open") if json.loads(x["props"]).get("item_id") == ids["DN"]]
        p3 = json.loads(g3[0]["props"]) if g3 else {}
        check("初めて → first・JST 23:59:59 は同じ日 (same_day)・0:00:00 から次の日 → touched・その日の 2 回目は same_day",
              res == ["first", "same_day", "touched", "same_day"], res)
        check("1 件 1 行のまま・days 2・last_opened は最後 (naive UTC)・created_at (初めて開いた時刻) は変えない",
              len(g3) == 1 and p3.get("days") == 2 and p3.get("last_opened") == "2026-10-19 15:00:00"
              and str(g3[0]["created_at"])[:19] == "2026-10-19 01:00:00", (g3, p3))
        conn = mod.db()
        try:
            other = [mod._record_item_open(conn, A, "hw", ids["DN"], now=t1), mod._record_item_open(conn, B, "gd", ids["DN"], now=t1)]
        finally:
            conn.close()
        same_id = [x for x in opens(mod) if json.loads(x["props"]).get("item_id") == ids["DN"]]
        check("同じ ID でも 種類 (hw / gd)・生徒が違えば別の行 (混ざらない)", other == ["first", "first"] and len(same_id) == 3
              and sorted((x["name"], x["session_id"]) for x in same_id) == sorted([("gd_open", str(A)), ("hw_open", str(A)), ("gd_open", str(B))]),
              (other, same_id))
        ex(mod, "DELETE FROM events WHERE name = 'hw_open'")   # 下の宿題の検査を 0 行から始める

        # 宿題 (POST /opened)
        r = client.post(f"/api/student/homework/{HA}/opened", json={}, headers=HA_)
        check("本人の未提出の宿題 → 200 recorded=first (AIなし枠でも通る)", r.status_code == 200 and r.json().get("recorded") == "first", (r.status_code, r.text[:200]))
        r = client.post(f"/api/student/homework/{HA}/opened", headers=HA_)
        check("同じ日の 2 回目 → same_day (本文なしでも通る)", r.status_code == 200 and r.json().get("recorded") == "same_day", r.text[:200])
        h = opens(mod, "hw_open")
        ph = json.loads(h[0]["props"]) if h else {}
        check("hw_open が 1 行・session_id = 生徒 ID・kind hw・item_id = 宿題 ID", len(h) == 1 and h[0]["session_id"] == str(A)
              and ph.get("kind") == "hw" and ph.get("item_id") == HA and "架空" not in h[0]["props"], h)
        r = client.post(f"/api/student/homework/{HB}/opened", headers=HA_)
        check("他人の宿題は 404・記録しない", r.status_code == 404 and len(opens(mod, "hw_open")) == 1, r.status_code)
        r = client.post(f"/api/student/homework/{HAc}/opened", headers=HA_)
        check("提出済みは recorded=completed・記録しない", r.status_code == 200 and r.json().get("recorded") == "completed" and len(opens(mod, "hw_open")) == 1, r.text[:200])
        r = client.post(f"/api/student/homework/{HA}/opened", headers=IMP_A)
        check("なりすましは recorded=impersonation", r.status_code == 200 and r.json().get("recorded") == "impersonation", r.text[:200])
        r = client.post(f"/api/student/homework/{HA}/opened")
        check("未ログインは 401", r.status_code == 401, r.status_code)
        r = client.post("/api/student/homework/99999/opened", headers=HA_)
        check("無い宿題は 404", r.status_code == 404, r.status_code)
        r = client.post(f"/api/student/homework/{HB}/opened", headers=HB_)
        check("AIありの生徒も自分の宿題で記録 (first)", r.status_code == 200 and r.json().get("recorded") == "first", r.text[:200])
    finally:
        root.removeHandler(hnd)
        root.setLevel(old_level)
    names = ("架空 開封一郎", "架空 開封次郎")
    check("ログに生徒の名前を出さない", not [m for m in recs if any(n in m for n in names)], [m for m in recs if any(n in m for n in names)][:3])

    class Boom:
        def cursor(self):
            raise RuntimeError("db down")

        def rollback(self):
            raise RuntimeError("db down")
    check("書けなくても例外を出さない (error)・種類 / ID が変なら skipped",
          mod._record_item_open(Boom(), A, "gd", 1) == "error" and mod._record_item_open(None, A, "zz", 1) == "skipped"
          and mod._record_item_open(None, A, "gd", 0) == "skipped" and mod._record_item_open(None, "x", "gd", 1) == "skipped")
    retained = {n for names_ in mod._EVENTS_RETENTION.values() for n in names_}
    check("gd_open / hw_open は保持期限の表に無い (消さない)", not ({"gd_open", "hw_open"} & retained), retained & {"gd_open", "hw_open"})
    old = (datetime.datetime.utcnow() - datetime.timedelta(days=400)).strftime("%Y-%m-%d %H:%M:%S")
    ex(mod, "INSERT INTO events (name, props, session_id, created_at) VALUES ('gd_open', ?, ?, ?)",
       (mod._item_open_dump(B, "gd", 777777, old, 1), str(B), old))
    n0 = len(opens(mod))
    mod._run_events_retention()
    check("400 日前の記録も events の掃除 (毎朝 4:00) で消えない", len(opens(mod)) == n0, (n0, len(opens(mod))))
    check("許可集合 (AIなし枠) は変えていない",
          set(mod._AI_DISABLED_ALLOWED_EXACT) == {"/api/student/homework", "/api/student/grammar-drills", "/api/messages/me", "/api/student/messages/send"}
          and tuple(mod._AI_DISABLED_ALLOWED_PREFIXES) == ("/api/student/class/", "/api/student/homework/", "/api/student/grammar-drill/",
                                                         "/api/messages/me/", "/api/auth/", "/api/admin/"))
    routes = {getattr(rt, "path", "") for rt in mod.app.routes}
    check("新しいルートは /api/student/homework/{homework_id}/opened だけ (元から許可された prefix の下)",
          "/api/student/homework/{homework_id}/opened" in routes and not any("opened" in x and not x.startswith("/api/student/homework/") for x in routes))
    return mod, client


def check_brief(mod, client):
    print("\n[3] 授業ブリーフの「開いたか」(読むだけ)")
    from test_grammar_import_units import admin_token  # noqa: E402
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    ex(mod, "DELETE FROM events WHERE name IN ('gd_open', 'hw_open')")
    f = Fx(mod)
    P = f.student("P", "架空 ブリーフ<b>一</b>", grade="高2")
    Z = f.student("Z", "架空 記録の始まり", grade="高2", labels=("火曜2限 英文法 Lv.2",))
    f.question("q1"); f.question("q2")
    chw = f"class_hw_auto:kosei:{L2}"
    f.drill("O1", chw, f"【{L2}】宿題 開いた（2問・〆10/20）"); f.assign("O1", "P", assigned_at="2026-10-17 21:00:05")
    f.drill("O2", chw, f"【{L2}】宿題 未開封（2問・〆10/20）"); f.assign("O2", "P", assigned_at="2026-10-17 21:00:05")
    f.drill("O3", "admin", "記録の前のドリル"); f.assign("O3", "P", assigned_at="2026-10-10 00:00:00")
    f.drill("OZ", "admin", "記録の始まり"); f.assign("OZ", "Z", assigned_at="2026-10-15 00:00:00")
    H1 = f.homework("H1", "P", "開いた宿題", created_at="2026-10-18 03:00:00")
    f.homework("H2", "P", "未開封の宿題", created_at="2026-10-18 03:00:00")
    f.homework("H3", "P", "記録の前の宿題", created_at="2026-10-01 03:00:00")
    HZ = f.homework("HZ", "Z", "記録の始まりの宿題", created_at="2026-10-15 00:00:00")
    conn = mod.db()
    try:
        at = lambda *a: datetime.datetime(*a, tzinfo=UTC)   # noqa: E731
        mod._record_item_open(conn, Z, "gd", f.ids["OZ"], now=at(2026, 10, 16, 0, 0, 0))   # 記録が始まった時刻 (ほかの生徒)
        mod._record_item_open(conn, Z, "hw", HZ, now=at(2026, 10, 16, 0, 0, 0))
        mod._record_item_open(conn, P, "gd", f.ids["O1"], now=at(2026, 10, 18, 1, 0, 0))   # JST 10/18 10:00
        mod._record_item_open(conn, P, "gd", f.ids["O1"], now=at(2026, 10, 18, 23, 30, 0))  # JST 10/19 08:30
        mod._record_item_open(conn, P, "hw", H1, now=at(2026, 10, 18, 4, 0, 0))            # JST 10/18 13:00
    finally:
        conn.close()
    # 同時に開いて 2 行になった (競合) = 早い方の初回・遅い方の最後
    ex(mod, "INSERT INTO events (name, props, session_id, created_at) VALUES ('hw_open', ?, ?, '2026-10-18 05:00:00')",
       (mod._item_open_dump(P, "hw", H1, "2026-10-18 10:00:00", 1), str(P)))
    mod._class_brief_now = lambda: datetime.datetime(2026, 10, 19, 1, 0, 0, tzinfo=UTC)   # JST 10/19 (月) 10:00
    before = len(opens(mod))
    r = client.get("/api/admin/class-brief", params={"date": "2026-10-19", "class": L2}, headers=adm)
    check("ブリーフ 200", r.status_code == 200, (r.status_code, r.text[:200]))
    d = r.json() if r.status_code == 200 else {}
    cl = (d.get("classes") or [{}])[0]
    mem = {m["id"]: m for m in cl.get("members", [])}
    p = mem.get(P, {})
    its = {(it.get("drill_id"), it.get("homework_id")): it for it in p.get("open_items", [])}
    o1 = its.get((f.ids["O1"], None), {})
    o2 = its.get((f.ids["O2"], None), {})
    o3 = its.get((f.ids["O3"], None), {})
    h1 = its.get((None, H1), {})
    h2 = its.get((None, f.ids["H2"]), {})
    h3 = its.get((None, f.ids["H3"]), {})
    check("開いたドリル: opened True・最後に開いた日 10/19 (JST)・2 日・初回は 10/18 01:00 UTC",
          o1.get("opened") is True and o1.get("opened_last_jst") == "10/19" and o1.get("open_days") == 2
          and o1.get("opened_at") == "2026-10-18T01:00:00+00:00" and o1.get("opened_last_at") == "2026-10-18T23:30:00+00:00", o1)
    check("記録が始まった後に配って記録の無いドリル・宿題 = opened False (👀 未開封)", o2.get("opened") is False and h2.get("opened") is False, (o2, h2))
    check("記録が始まる前に配って記録の無いもの = opened None (分からない = 未開封と言わない)", o3.get("opened") is None and h3.get("opened") is None, (o3, h3))
    check("競合で 2 行の宿題: 初回は早い方 (04:00)・最後は遅い方 (10:00 = JST 10/18)", h1.get("opened") is True
          and h1.get("opened_at") == "2026-10-18T04:00:00+00:00" and h1.get("opened_last_at") == "2026-10-18T10:00:00+00:00"
          and h1.get("opened_last_jst") == "10/18", h1)
    check("生徒の数: 未開封 2・開いたが未提出 2", p.get("unopened_count") == 2 and p.get("opened_open_count") == 2, (p.get("unopened_count"), p.get("opened_open_count")))
    check("ブリーフは書かない (events の行数が同じ)", len(opens(mod)) == before, (before, len(opens(mod))))
    check("props の名前・メールは応答にも events にも無い (名前は名簿の name だけ)",
          all("架空" not in x["props"] for x in opens(mod)))
    return d, f


# ---------------------------------------------------------------------------------------------------------------
# 画面 (JS エンジン)
def load_harness():
    spec = importlib.util.spec_from_file_location("hw_notice_js_harness_item_open", HW_NOTICE_TEST)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run_js(engine, program, label, env_extra=None):
    with tempfile.TemporaryDirectory(prefix="item_open_js_") as td:
        path = os.path.join(td, "case.js")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(program)
        env = dict(os.environ)
        env.update(env_extra or {})
        try:
            r = subprocess.run(engine + [path], capture_output=True, text=True, timeout=180, env=env)
        except Exception as e:  # noqa: BLE001
            check(f"{label}: JS を実行できた", False, f"{type(e).__name__}: {e}")
            return
    text = (r.stdout or "") + "\n" + (r.stderr or "")
    lines = [ln for ln in text.split("\n") if ln.startswith(("OK  ", "NG  ", "DONE "))]
    done = [ln for ln in lines if ln.startswith("DONE ")]
    if r.returncode != 0 or not done:
        check(f"{label}: JS が最後まで走った (exit {r.returncode})", False, text[-1500:])
        return
    for ln in lines:
        if ln.startswith("OK  "):
            check(ln[4:], True)
        elif ln.startswith("NG  "):
            check(ln[4:], False, ln[4:])
    check(f"{label}: {int(done[-1].split()[1])} 件の検査を実行", int(done[-1].split()[1]) > 0)


JS_PURE = r"""
__loadHwNotice();
var N = window.AJHwNotice;
var T1 = Date.UTC(2026, 9, 17, 14, 59, 59);   // JST 10/17 23:59:59 (LA では 10/17 07:59)
var T2 = Date.UTC(2026, 9, 17, 15, 0, 0);     // JST 10/18 00:00:00
eq('JST の今日 (0:00 の境目・端末のタイムゾーンに依らない)', [N.todayJst(T1), N.todayJst(T2)], ['2026-10-17', '2026-10-18']);
eq('dueState: 〆10/17 は JST 23:59:59 まで「今日」・0:00:00 から「過ぎた」', [N.dueState('2026-10-17', N.todayJst(T1)), N.dueState('2026-10-17', N.todayJst(T2))], ['today', 'over']);
eq('dueState: 先の〆・〆なし・空・読めない値・時刻つき', [N.dueState('2026-10-19', '2026-10-18'), N.dueState(null, '2026-10-18'), N.dueState('', '2026-10-18'),
   N.dueState('10/18', '2026-10-18'), N.dueState('2026-10-18 00:00:00', '2026-10-18')], ['', '', '', '', 'today']);
var __rn = Date.now; Date.now = function () { return T1; };
eq('dueState の today を省くと JST の今日 (Date.now)', N.dueState('2026-10-17'), 'today');
Date.now = __rn;
eq('チップの文言', [N.dueChipText('over'), N.dueChipText('today'), N.dueChipText('')], ['〆を過ぎました', '〆今日', '']);
var drills = [
  { drill_id: 1, status: 'open', due_date: '2026-10-17', assigned_at: '2026-10-15 21:00:00' },      // 〆を過ぎた
  { drill_id: 2, status: 'assigned', due_date: '2026-10-18', assigned_at: '2026-10-16 21:00:00' },  // 〆今日 (予約タスクの assigned も未提出)
  { drill_id: 3, status: 'completed', due_date: '2026-10-10', assigned_at: '2026-10-08 21:00:00' }, // 提出済みは数えない
  { drill_id: 4, status: 'open', due_date: null, assigned_at: '2026-10-16 21:00:00' },
  { drill_id: 5, status: 'open', due_date: '2026-10-25', assigned_at: '2026-10-16 21:00:00' }
];
var hw = [
  { id: 11, status: 'open', due_date: '2026-10-18', created_at: '2026-10-10 00:00:00' },
  { id: 12, status: 'open', due_date: '2026-10-01', created_at: '2026-09-25 00:00:00' },
  { id: 13, status: 'completed', due_date: '2026-10-01', created_at: '2026-09-25 00:00:00' }
];
var seenAll = { d: ['1', '2', '3', '4', '5'], h: ['11', '12', '13'] };
var r = N.compute({ drills: drills, homework: hw, seen: seenAll, now: T2 });
eq('compute: 〆を過ぎた = ドリル 1 + 宿題 1・〆今日 = ドリル 1 + 宿題 1・新しい 0',
   [r.overdue, r.overdueDrills, r.overdueHw, r.dueToday, r.newCount], [2, 1, 1, 2, 0]);
eq('banner: 見た後でも 〆を過ぎた未提出があれば出る (over・〆今日の数も添える)', N.banner(r), { kind: 'over', text: '⚠️ 〆を過ぎた宿題が 2 件あります（〆今日 2 件）' });
var rt = N.compute({ drills: [drills[1]], homework: [], seen: seenAll, now: T2 });
eq('banner: 〆今日だけ (today)', N.banner(rt), { kind: 'today', text: '⏰ 今日が〆の宿題が 1 件あります' });
var rn = N.compute({ drills: [{ drill_id: 9, status: 'open', due_date: '2026-10-18', assigned_at: '2026-10-17 14:00:00' }], homework: [], seen: null, now: T2 });
eq('banner: 新しい宿題があれば新着の帯に 〆 の数を添える', N.banner(rn), { kind: 'new', text: '🆕 新しい宿題が 1 件届いています（〆今日 1 件）' });
var r0 = N.compute({ drills: [drills[2], drills[3], drills[4]], homework: [hw[2]], seen: seenAll, now: T2 });
eq('banner: 〆の近い未提出も新しいものも無ければ null', [N.banner(r0), N.banner(null), N.banner({})], [null, null, null]);
eq('compute の today を渡すとその日で数える (10/26 には 〆10/25 も過ぎた = ドリル 3 + 宿題 2)', N.compute({ drills: drills, homework: hw, seen: seenAll, today: '2026-10-26', now: T2 }).overdue, 5);
eq('todoLabel: 〆今日だけ', N.todoLabel(0, 4, 0, 2), '⏰ 宿題 4 件（〆今日 2 件）');
eq('todoLabel: 〆を過ぎた + 〆今日', N.todoLabel(0, 3, 2, 1), '⚠️ 宿題 3 件（うち〆を過ぎた 2 件・〆今日 1 件）');
eq('todoLabel: 新しい + 未提出 + 〆を過ぎた + 〆今日', N.todoLabel(1, 3, 1, 1), '🆕 新しい宿題 1 件（未提出 3 件・うち〆を過ぎた 1 件・〆今日 1 件）');
eq('todoLabel: 3 引数の呼び出しは今までの形 (〆今日なし)', N.todoLabel(0, 3, 0), '📝 宿題 3 件');
eq('dueLabel: どちらも 0 なら空', N.dueLabel(0, 0), '');
__emit();
"""

JS_CLASS_DUE_SETUP = r"""
var CALLS2 = [], OPENED_TABS = [];
var __baseFetch2 = fetch;
fetch = function (url, opts) {
  var path = String(url).replace(/^https?:\/\/[^\/]+/, '');
  CALLS2.push({ path: path, method: (opts && opts.method) || 'GET', body: opts && opts.body, keepalive: !!(opts && opts.keepalive),
                auth: !!(opts && opts.headers && opts.headers.Authorization) });
  return __baseFetch2(url, opts);
};
window.fetch = fetch;
window.open = function () { var t = { closed: false, location: { href: '' }, document: { write: function () {} }, close: function () { this.closed = true; } }; OPENED_TABS.push(t); return t; };
// 宿題欄のボタン (renderHomework が querySelectorAll で listener を付ける) を偽の DOM で拾う
function wireHwButtons() {
  var hb = document.getElementById('homeworkBody');
  hb._btns = {};
  hb.querySelectorAll = function (sel) {
    var cls = { '.hw-drill': 'hw-drill', '.hw-print': 'hw-print', '.hw-sheet': 'hw-sheet' }[sel];
    if (!cls) return [];
    var out = [], re = new RegExp('class="btn btn-[a-z]+ ' + cls + '" data-id="([^"]*)"', 'g'), m;
    while ((m = re.exec(hb._html))) { var b = new FakeEl(); b.setAttribute('data-id', m[1]); out.push(b); }
    hb._btns[cls] = out;
    return out;
  };
  return hb;
}
function btnOf(cls, id) { var hb = ELS.homeworkBody; return ((hb && hb._btns && hb._btns[cls]) || []).filter(function (b) { return b.getAttribute('data-id') === String(id); })[0]; }
async function bootDue(search) {
  ELS = {}; TAB_BTNS = ['schedule', 'homework', 'videos', 'messages'].map(function (t) { var b = new FakeEl(); b.setAttribute('data-tab', t); return b; });
  HIST = []; FETCHES = []; TIMERS = []; CALLS2 = []; OPENED_TABS = [];
  setLoc('/class.html', search || '', '');
  location.assign = function () {};
  wireHwButtons();
  if (window.AJHwNotice) window.AJHwNotice._clearMemory();
  __bootClass();
  await flush();
}
function openedPosts() { return CALLS2.filter(function (c) { return c.method === 'POST' && /\/opened$/.test(c.path); }); }
function cards2() { return String(ELS.homeworkBody.innerHTML).split('<div class="card">').slice(1); }
function cardOf2(title) { return cards2().filter(function (x) { return x.indexOf('<div class="card-title">' + title + '</div>') >= 0 || x.indexOf('<div class="card-title">📝 ' + title + '</div>') >= 0; })[0] || ''; }
var NOW_MS = Date.UTC(2026, 9, 18, 1, 0, 0);   // JST 10/18 10:00 (LA では 10/17 18:00 = 端末の日付はまだ 10/17)
Date.now = function () { return NOW_MS; };
// hw-sheet.js の代わり (解答用紙の宿題の「答える」ボタンだけ使う)
window.AJHwSheet = { state: function (it) { return (it.answer_sheet && it.answer_sheet.submitted) ? 'submitted' : 'open'; },
  answerButtonLabel: function () { return '✏️ 解答用紙に答える'; }, scoreText: function () { return ''; },
  mount: function (el, o) { window.__lastMount = o; return { detach: function () {} }; } };
var XC_TODAY = { drill_id: 601, title: '【月曜2限 英文法 Lv.1】宿題 時制（10問・〆10/18）', unit: '時制', subject: 'english', status: 'open', score_total: 10,
                 assigned_at: '2026-10-15 21:00:05', due_date: '2026-10-18' };
var XC_OVER = { drill_id: 602, title: '【月曜2限 英文法 Lv.1】宿題 比較（10問・〆10/17）', unit: '比較', subject: 'english', status: 'open', score_total: 10,
                assigned_at: '2026-10-14 21:00:05', due_date: '2026-10-17' };
var XC_DONE = { drill_id: 603, title: '【月曜2限 英文法 Lv.1】宿題 済み（10問・〆10/16）', unit: '済み', subject: 'english', status: 'completed', score_correct: 9,
                score_total: 10, assigned_at: '2026-10-13 21:00:05', completed_at: '2026-10-14 10:00:00', due_date: '2026-10-16' };
var XH_BARE = { id: 701, title: '音読 3 回', subject: 'english', topic: '', status: 'open', created_at: '2026-10-17 01:00:00', due_date: '2026-10-18' };
var XH_PRINT = { id: 702, title: 'プリントの宿題', subject: 'english', topic: '', status: 'open', created_at: '2026-10-17 01:00:00', due_date: '2026-10-25',
                 attachment_print: { id: 88, title: '架空プリント' } };
var XH_DRILL = { id: 703, title: 'ドリルの宿題', subject: 'english', topic: '関係詞', status: 'open', created_at: '2026-10-17 01:00:00', due_date: '2026-10-16' };
var XH_SHEET = { id: 704, title: '解答用紙の宿題', subject: 'english', topic: '', status: 'open', created_at: '2026-10-17 01:00:00', due_date: null,
                 answer_sheet: { mode: 'choice', available: true, num_questions: 3, num_choices: 4 } };
var XH_DONE = { id: 705, title: '済んだ宿題', subject: 'english', topic: '', status: 'completed', created_at: '2026-10-10 01:00:00', completed_at: '2026-10-12 01:00:00', due_date: '2026-10-11' };
function seenStore(d, h) {
  var st = memStore();
  st._m['aj_hw_seen_v1:7'] = JSON.stringify({ v: 1, d: d, h: h });
  if (!setWindowStorage({ configurable: true, writable: true, value: st })) window.AJHwNotice._useStorage(st);
  return st;
}
"""

JS_CLASS_DUE_CASES = r"""
(async function () {
  try {
    __loadHwNotice();
    // (D1) 〆今日のドリル (前に見た = 新しくない): 予定タブに橙の帯・宿題タブを見た後も出し続ける
    seenStore(['601'], []);
    setApi({ '/api/student/homework': hwBody([]), '/api/student/grammar-drills': drillBody([XC_TODAY]) });
    await bootDue('');
    ok('〆今日の未提出 → 予定タブに「⏰ 今日が〆の宿題が 1 件あります」(橙 = hw-notice soon)',
       banner().indexOf('⏰ 今日が〆の宿題が 1 件あります') >= 0 && banner().indexOf('class="hw-notice soon"') >= 0, banner());
    tab('homework'); await flush();
    eq('宿題タブでは帯を隠す', banner(), '');
    ok('ドリルのカードに「〆今日」(chip-soon)', cardOf2(XC_TODAY.title).indexOf('chip-open">未提出</span> <span class="chip chip-soon">〆今日</span>') >= 0, cardOf2(XC_TODAY.title));
    tab('schedule');
    ok('宿題タブを見た後 (「見た」の記録) も予定タブの帯は消えない', banner().indexOf('⏰ 今日が〆の宿題が 1 件あります') >= 0, banner());
    tab('videos');
    ok('動画タブにも同じ帯', banner().indexOf('⏰ 今日が〆の宿題が 1 件あります') >= 0, banner());

    // (D2) 〆を過ぎたドリル + 期限を過ぎた宿題 (どちらも見た) + 〆今日の宿題 → 赤い帯・カードに「〆を過ぎました」
    seenStore(['602', '603'], ['701', '703']);
    setApi({ '/api/student/homework': hwBody([XH_BARE, XH_DRILL, XH_DONE]), '/api/student/grammar-drills': drillBody([XC_OVER, XC_DONE]) });
    await bootDue('');
    ok('〆を過ぎた 2 件 + 〆今日 1 件 → 「⚠️ 〆を過ぎた宿題が 2 件あります（〆今日 1 件）」(赤 = warn)',
       banner().indexOf('⚠️ 〆を過ぎた宿題が 2 件あります（〆今日 1 件）') >= 0 && banner().indexOf('class="hw-notice warn"') >= 0, banner());
    eq('予定タブにいる間は 👀 の POST を送らない', openedPosts().length, 0);
    tab('homework'); await flush();
    ok('〆を過ぎたドリルのカード: 未提出 + 〆を過ぎました', cardOf2(XC_OVER.title).indexOf('chip-open">未提出</span> <span class="chip chip-over">〆を過ぎました</span>') >= 0, cardOf2(XC_OVER.title));
    ok('提出済みのドリルには 〆 のチップを出さない', cardOf2(XC_DONE.title).indexOf('〆を過ぎました') < 0 && cardOf2(XC_DONE.title).indexOf('chip-done') >= 0, cardOf2(XC_DONE.title));
    ok('宿題 (JST で今日が期限・端末の日付はまだ前の日): 未提出 + 〆今日', cardOf2('音読 3 回').indexOf('chip-open">未提出</span> <span class="chip chip-soon">〆今日</span>') >= 0, cardOf2('音読 3 回'));
    ok('宿題 (期限を過ぎた): 未提出 + 〆を過ぎました', cardOf2('ドリルの宿題').indexOf('chip-open">未提出</span> <span class="chip chip-over">〆を過ぎました</span>') >= 0, cardOf2('ドリルの宿題'));
    ok('提出済みの宿題には 〆 のチップを出さない', cardOf2('済んだ宿題').indexOf('〆') < 0, cardOf2('済んだ宿題'));

    // (D3) 提出したら帯が消える
    var doneOver = JSON.parse(JSON.stringify(XC_OVER)); doneOver.status = 'completed'; doneOver.completed_at = '2026-10-18 00:30:00';
    var doneBare = JSON.parse(JSON.stringify(XH_DRILL)); doneBare.status = 'completed'; doneBare.completed_at = '2026-10-18 00:30:00';
    setApi({ '/api/student/homework': hwBody([doneBare]), '/api/student/grammar-drills': drillBody([doneOver]) });
    await bootDue('');
    eq('提出したら帯は出ない', banner(), '');

    // (D4) 新しい 〆今日のドリル → ピンクの新着の帯に 〆 の数
    seenStore([], []);
    var fresh = JSON.parse(JSON.stringify(XC_TODAY)); fresh.drill_id = 611; fresh.assigned_at = '2026-10-17 21:00:05';
    setApi({ '/api/student/homework': hwBody([]), '/api/student/grammar-drills': drillBody([fresh]) });
    await bootDue('');
    ok('新しい宿題の帯に「（〆今日 1 件）」を添える (ピンク)', banner().indexOf('🆕 新しい宿題が 1 件届いています（〆今日 1 件）') >= 0
       && banner().indexOf('class="hw-notice"') >= 0, banner());

    // (D5) 解答用紙で提出した直後 (一覧を読み直す前) に予定タブへ移っても、出した宿題の 〆 の帯は残らない
    var sheetToday = JSON.parse(JSON.stringify(XH_SHEET)); sheetToday.id = 714; sheetToday.due_date = '2026-10-18';
    seenStore([], ['714']);
    setApi({ '/api/student/homework': hwList2([sheetToday]), '/api/student/grammar-drills': drillBody([]) });
    await bootDue('');
    ok('解答用紙の宿題 (〆今日) → 橙の帯', banner().indexOf('⏰ 今日が〆の宿題が 1 件あります') >= 0, banner());
    tab('homework'); await flush();
    window.__lastMount = null;
    btnOf('hw-sheet', 714).dispatch('click'); await flush();
    ok('解答用紙を開いた (mount)', !!(window.__lastMount && window.__lastMount.onSubmitted));
    if (window.__lastMount) window.__lastMount.onSubmitted({ ok: true }, {});
    tab('schedule');
    eq('提出した直後に予定タブへ移っても 〆 の帯は出ない', banner(), '');

    // (O1) 👀 開いたの POST
    seenStore([], []);
    setApi({ '/api/student/homework': hwList2([XH_BARE, XH_PRINT, XH_DRILL, XH_SHEET, XH_DONE]), '/api/student/grammar-drills': drillBody([]) });
    await bootDue('?tab=homework');
    eq('宿題タブに着地', visibleTab(), 'homework');
    eq('中身だけの未提出の宿題 (単元・プリント・解答用紙なし) は一覧に出たら POST /opened (提出済みは送らない)',
       openedPosts().map(function (c) { return c.path; }), ['/api/student/homework/701/opened']);
    var p0 = openedPosts()[0] || {};
    eq('POST の本文 {}・Authorization つき・keepalive', [p0.body, p0.auth, p0.keepalive], ['{}', true, true]);
    btnOf('hw-print', 702).dispatch('click'); await flush();
    ok('「📄 プリントを開く」→ POST /api/student/homework/702/opened', openedPosts().some(function (c) { return c.path === '/api/student/homework/702/opened'; }), openedPosts());
    ok('…プリントのタブは押した瞬間に開く (今までどおり)', OPENED_TABS.length === 1);
    btnOf('hw-drill', 703).dispatch('click'); await flush();
    var pd = openedPosts().filter(function (c) { return c.path === '/api/student/homework/703/opened'; });
    eq('「📝 ドリルで解く」(dojo-drill へ移るリンク) → keepalive つきで POST /opened', pd.map(function (c) { return c.keepalive; }), [true]);
    btnOf('hw-drill', 703).dispatch('click'); await flush();
    eq('同じ宿題はこのページで 1 回だけ', openedPosts().filter(function (c) { return c.path === '/api/student/homework/703/opened'; }).length, 1);
    btnOf('hw-sheet', 704).dispatch('click'); await flush();
    ok('「✏️ 解答用紙に答える」→ POST /api/student/homework/704/opened', openedPosts().some(function (c) { return c.path === '/api/student/homework/704/opened'; }), openedPosts());
    ok('提出済みの宿題は送らない', !openedPosts().some(function (c) { return c.path === '/api/student/homework/705/opened'; }));
    eq('単元ドリル (サーバが GET の中で記録する) には POST を送らない', openedPosts().filter(function (c) { return /grammar-drill/.test(c.path); }).length, 0);
    // 一覧を読み直しても中身だけの宿題は送り直さない (解答用紙の「← 宿題一覧に戻る」で読み直す)
    var nBefore = openedPosts().length, nGets = CALLS2.filter(function (c) { return c.path.split('?')[0] === '/api/student/homework'; }).length;
    ok('解答用紙の画面を開いた (mount)', !!(window.__lastMount && window.__lastMount.onBack));
    if (window.__lastMount && window.__lastMount.onBack) window.__lastMount.onBack();
    await flush();
    ok('一覧を読み直した', CALLS2.filter(function (c) { return c.path.split('?')[0] === '/api/student/homework'; }).length === nGets + 1);
    eq('同じページで読み直しても送り直さない', openedPosts().length, nBefore);
  } catch (e) {
    ok('例外なし', false, String((e && e.stack) || e));
  }
  __emit();
})();
"""

JS_CLASS_DUE_HELPERS = r"""
function hwList2(items) {
  var b = { ok: true, items: items, summary: { open: items.filter(function (x) { return x.status === 'open'; }).length, overdue: 0 }, print_open: true, answer_sheet_ready: true };
  return { status: 200, body: b };
}
"""

JS_MYPAGE_DUE_SETUP = r"""
var CALLS3 = [];
var __baseSl = slApiFetch;
slApiFetch = function (path, opts) {
  CALLS3.push({ path: String(path), method: (opts && opts.method) || 'GET', body: opts && opts.body });
  if (/\/download$/.test(String(path))) return Promise.resolve({ ok: true, file_path: '/lesson-prints/x.pdf' });
  return __baseSl(path, opts);
};
window.open = function () { return { closed: false, location: '', document: { write: function () {} }, close: function () {} }; };
var NOW_MS = Date.UTC(2026, 9, 18, 1, 0, 0);   // JST 10/18 10:00 (LA では 10/17 18:00)
Date.now = function () { return NOW_MS; };
window.AJHwSheet = { state: function () { return 'open'; }, answerButtonLabel: function () { return '✏️ 解答用紙に答える'; }, scoreText: function () { return ''; },
  fmtJst: function (s) { return String(s); }, openOverlay: function () { return {}; } };
function myOpened() { return CALLS3.filter(function (c) { return c.method === 'POST' && /\/opened$/.test(c.path); }).map(function (c) { return c.path; }); }
// 👀 カード 1 枚ごとの監視 (点検 owner-F1): 偽の宿題欄の querySelectorAll('.hw-item[data-hw-id]') は描いた HTML のカードを返す
//   (描き直すまで同じ要素)。カードの監視 = data-hw-id の要素を見ている IntersectionObserver
var __baseNewSection = newSection;
newSection = function () {
  __baseNewSection();
  var lst = ELS['#homeworkList'];
  lst.querySelectorAll = function (sel) {
    if (sel !== '.hw-item[data-hw-id]') return [];
    if (this._cardsFor !== this._html) {
      this._cardsFor = this._html; this._cards = [];
      var re = /class="hw-item[^"]*" data-hw-id="([^"]*)"/g, m;
      while ((m = re.exec(this._html))) { var el = new FakeEl(); el.setAttribute('data-hw-id', m[1]); this._cards.push(el); }
    }
    return this._cards.slice();
  };
};
function cardEl(id) { var cs = ELS['#homeworkList'].querySelectorAll('.hw-item[data-hw-id]'); for (var i = 0; i < cs.length; i++) if (cs[i].getAttribute('data-hw-id') === String(id)) return cs[i]; return null; }
function cardIo() { var r = IO_LIST.filter(function (o) { return o.el && o.el.getAttribute && o.el.getAttribute('data-hw-id') != null; }); return r[r.length - 1] || null; }
function watched() { var o = cardIo(); return o ? o.els.map(function (e) { return e.getAttribute('data-hw-id'); }) : []; }
function seeCard(id, ratio, h) {
  var o = cardIo(); if (!o) throw new Error('カードの監視が無い');
  o.cb([{ target: cardEl(id), isIntersecting: ratio > 0, intersectionRatio: ratio, intersectionRect: { height: h == null ? ratio * 200 : h } }]);
}
function seeSection() {
  var o = IO_LIST.filter(function (x) { return x.el === SECTION; }).pop();
  o.cb([{ isIntersecting: true, intersectionRatio: 0.5, intersectionRect: { height: 400 } }]);
  TIMERS[TIMERS.length - 1].fn();
}
function clickSel(attr, val, card) {
  var btn = new FakeEl(); btn.setAttribute(attr, String(val));
  btn.closest = function (sel) { return (sel === '[data-hw-id]' && card) ? card : null; };
  ELS['#homeworkList'].dispatch('click', { target: { closest: function (sel) { return sel === '[' + attr + ']' ? btn : null; } } });
  return btn;
}
var MD_TODAY = { drill_id: 801, title: '【月曜2限 英文法 Lv.1】宿題 時制（10問・〆10/18）', unit: '時制', subject: 'english', status: 'open', assigned_at: '2026-10-15 21:00:05', due_date: '2026-10-18' };
var MD_OVER = { drill_id: 802, title: '【月曜2限 英文法 Lv.1】宿題 比較（10問・〆10/17）', unit: '比較', subject: 'english', status: 'open', assigned_at: '2026-10-14 21:00:05', due_date: '2026-10-17' };
var MD_LATER = { drill_id: 803, title: '【月曜2限 英文法 Lv.1】宿題 関係詞（10問・〆10/20）', unit: '関係詞', subject: 'english', status: 'open', assigned_at: '2026-10-17 21:00:05', due_date: '2026-10-20' };
var MH_TODAY = { id: 901, title: '音読 3 回', subject: 'english', status: 'open', created_at: '2026-10-10 01:00:00', due_date: '2026-10-18' };
var MH_PRINT = { id: 902, title: 'プリントの宿題', subject: 'english', status: 'open', created_at: '2026-10-10 01:00:00', due_date: '2026-10-30', attachment_print: { id: 55, title: '架空プリント' } };
var MH_SHEET = { id: 903, title: '解答用紙の宿題', subject: 'english', status: 'open', created_at: '2026-10-10 01:00:00', due_date: null, answer_sheet: { mode: 'choice' } };
var MH_DONE = { id: 904, title: '済んだ宿題', subject: 'english', status: 'completed', created_at: '2026-10-01 01:00:00', completed_at: '2026-10-02 01:00:00' };
"""

JS_MYPAGE_DUE_CASES = r"""
(async function () {
  try {
    __loadHwNotice();
    var st = memStore(); window.AJHwNotice._useStorage(st); window.AJHwNotice._clearMemory();
    st._m['aj_hw_seen_v1:7'] = JSON.stringify({ v: 1, d: ['801', '802', '803'], h: ['901', '902', '903', '904'] });   // 前に見た = 新しくない
    newSection();
    API['/api/student/grammar-drills'] = { ok: true, items: [MD_TODAY, MD_OVER, MD_LATER] };
    API['/api/student/homework'] = { ok: true, items: [MH_TODAY, MH_PRINT, MH_SHEET, MH_DONE], summary: { overdue: 0 }, answer_sheet_ready: true };
    await initHomeworkSection(); await flush();
    var html = ELS['#homeworkList'].innerHTML;
    function cardM(key) { var parts = String(html).split('<div class="hw-item'); for (var i = 1; i < parts.length; i++) if (parts[i].indexOf(key) >= 0) return parts[i]; return ''; }
    ok('ドリルのカード (〆10/18): ⏰ 〆今日 (端末の日付 10/17 ではなく JST)', cardM('data-hw-drill-open="801"').indexOf('⏰ 〆今日') >= 0, cardM('data-hw-drill-open="801"'));
    ok('ドリルのカード (〆10/17): ⚠ 〆を過ぎました (2026-10-17)', cardM('data-hw-drill-open="802"').indexOf('⚠ 〆を過ぎました (2026-10-17)') >= 0, cardM('data-hw-drill-open="802"'));
    ok('ドリルのカード (〆10/20): あと 2 日', cardM('data-hw-drill-open="803"').indexOf('あと 2 日 (2026-10-20)') >= 0, cardM('data-hw-drill-open="803"'));
    ok('宿題のカード (期限 10/18): ⏰ 〆今日 (JST)', cardM('data-hw-id="901"').indexOf('⏰ 〆今日') >= 0, cardM('data-hw-id="901"'));
    eq('📌 要対応チップ: 〆を過ぎた 1 (ドリル)・〆今日 2 (ドリル + 宿題)', TODO.homework && TODO.homework.label, '⚠️ 宿題 6 件（うち〆を過ぎた 1 件・〆今日 2 件）');
    eq('…目立たせる (urgent)', TODO.homework && TODO.homework.urgent, true);
    eq('宿題欄のバッジ', ELS['#homeworkBadge'].textContent, '⚠ 〆を過ぎた 1 / 未完了 6');
    eq('描いただけでは 👀 の POST を送らない', myOpened(), []);
    // (owner-F1) 宿題欄が見えた ≠ そのカードが見えた: ドリルのカードが上に 3 枚並ぶと宿題のカードは画面の外のことがある
    seeSection(); await flush();
    eq('宿題欄が 1.5 秒見えても、カードが見えていなければ POST しない (欄の監視は 🆕 の「見た」だけ)', myOpened(), []);
    ok('…🆕 の「見た」は記録する (今までどおり)', JSON.parse(st._m['aj_hw_seen_v1:7']).h.indexOf('901') >= 0);
    eq('カードの監視は中身だけの未提出の宿題だけ (プリント・解答用紙つき・提出済み・ドリルは見ない)', watched(), ['901']);
    var nT = TIMERS.length;
    seeCard(901, 0.3); await flush();
    eq('カードが半分未満しか見えなければ待たない', TIMERS.length, nT);
    seeCard(901, 0.6);
    eq('カードが半分以上見えたら 1.5 秒待つ', TIMERS.length === nT + 1 && TIMERS[TIMERS.length - 1].ms, 1500);
    seeCard(901, 0.2);
    eq('1.5 秒たつ前に外れたら送らない', [TIMERS[TIMERS.length - 1].fn, myOpened()], [null, []]);
    seeCard(901, 0.6); TIMERS[TIMERS.length - 1].fn(); await flush();
    eq('カードが 1.5 秒見えたら POST /opened', myOpened(), ['/api/student/homework/901/opened']);
    eq('送ったカードは見るのをやめる', watched(), []);
    var card902 = new FakeEl(); card902.setAttribute('data-hw-id', '902');
    clickSel('data-hw-print', 55, card902); await flush();
    ok('「📄 PDFを開く」→ POST /api/student/homework/902/opened (カードの data-hw-id)', myOpened().indexOf('/api/student/homework/902/opened') >= 0, myOpened());
    clickSel('data-hw-sheet', 903); await flush();
    ok('「✏️ 解答用紙に答える」→ POST /api/student/homework/903/opened', myOpened().indexOf('/api/student/homework/903/opened') >= 0, myOpened());
    clickSel('data-hw-sheet', 903); await flush();
    eq('このページで 1 件 1 回', myOpened().filter(function (p) { return p === '/api/student/homework/903/opened'; }).length, 1);
    ok('提出済みの宿題には送らない', myOpened().indexOf('/api/student/homework/904/opened') < 0, myOpened());
    // 〆今日だけ (〆を過ぎたは無い)
    newSection(); TODO = {};
    API['/api/student/grammar-drills'] = { ok: true, items: [MD_TODAY, MD_LATER] };
    API['/api/student/homework'] = { ok: true, items: [MH_PRINT], summary: { overdue: 0 } };
    await initHomeworkSection(); await flush();
    eq('〆今日だけ: チップ「⏰ 宿題 3 件（〆今日 1 件）」・バッジ「⏰ 〆今日 1 / 未完了 3」', [TODO.homework && TODO.homework.label, ELS['#homeworkBadge'].textContent],
       ['⏰ 宿題 3 件（〆今日 1 件）', '⏰ 〆今日 1 / 未完了 3']);
    // (F1 2026-10-18 点検) 単元 (topic) のある宿題: マイページのカードには「📝 ドリルで解く」が無く、題名と説明が宿題のすべて
    //   → カードが見えたら中身だけの宿題と同じく POST /opened (class.html の「単元のある宿題は除く」を写すと 👀 未開封 のまま)。
    //   プリント・解答用紙つきは今までどおり、それを開いたときだけ
    newSection(); TODO = {}; CALLS3 = [];
    var MH_TOPIC = { id: 905, title: '関係代名詞の宿題', subject: 'english', topic: '関係代名詞', status: 'open', created_at: '2026-10-10 01:00:00', due_date: '2026-10-25' };
    var MH_TOPIC_PRINT = { id: 906, title: '単元とプリントの宿題', subject: 'english', topic: '時制', status: 'open', created_at: '2026-10-10 01:00:00', due_date: null,
                           attachment_print: { id: 56, title: '架空プリント2' } };
    var MH_TOPIC_SHEET = { id: 907, title: '単元と解答用紙の宿題', subject: 'english', topic: '比較', status: 'open', created_at: '2026-10-10 01:00:00', due_date: null,
                           answer_sheet: { mode: 'choice' } };
    API['/api/student/grammar-drills'] = { ok: true, items: [] };
    API['/api/student/homework'] = { ok: true, items: [MH_TOPIC, MH_TOPIC_PRINT, MH_TOPIC_SHEET], summary: { overdue: 0 }, answer_sheet_ready: true };
    await initHomeworkSection(); await flush();
    ok('単元のある宿題のカードは題名・説明・✅ 完了する だけ (開くリンクが無い = カードが中身)',
       String(ELS['#homeworkList'].innerHTML).indexOf('dojo-drill') < 0 && String(ELS['#homeworkList'].innerHTML).indexOf('data-hw-complete="905"') >= 0);
    eq('単元のある宿題もカードを見る (プリント・解答用紙つきは見ない)', watched(), ['905']);
    seeSection(); await flush();
    eq('宿題欄が見えただけでは単元のある宿題も POST しない', myOpened(), []);
    clickSel('data-hw-drill-open', 999); await flush();
    eq('ドリルを開いても (🆕 の「見た」) 宿題には POST しない', myOpened(), []);
    seeCard(905, 0.3, 450);   // 画面 (800) より背の高いカード: 3 割でも画面の半分以上
    var tTall = TIMERS[TIMERS.length - 1];
    ok('画面より背の高いカードは画面の半分以上見えたら数える', !!(tTall && tTall.ms === 1500 && tTall.fn));
    // 待っている間に一覧を読み直した → 前の描画の待ちは捨て、新しいカードを見直す
    await window._hwRefreshDrills(); await flush();
    eq('読み直したら前の描画の待ちは捨てる', [tTall.fn, myOpened()], [null, []]);
    eq('…新しいカードを見直す', watched(), ['905']);
    seeCard(905, 0.6); TIMERS[TIMERS.length - 1].fn(); await flush();
    eq('単元のある宿題も、カードが 1.5 秒見えたら POST /opened (プリント・解答用紙つきは送らない)', myOpened(), ['/api/student/homework/905/opened']);
    await window._hwRefreshDrills(); await flush();
    eq('送った宿題は読み直しても見ない (このページで 1 件 1 回)', [watched(), myOpened().length], [[], 1]);
  } catch (e) {
    ok('例外なし', false, String((e && e.stack) || e));
  }
  __emit();
})();
"""


def _ceo_brief_block(src):
    head = "  // 🗓 今日の授業ブリーフ (2026-10-18"
    i = src.find(head)
    j = src.find("  </script>", i)
    return src[i:j] if 0 <= i < j else ""


JS_CEO_SETUP = r"""
var __els = {};
function __el(id) { if (!__els[id]) __els[id] = { id: id, innerHTML: '', value: '', style: {}, parentNode: null, focus: function () {} }; return __els[id]; }
var document = { readyState: 'complete', activeElement: null, documentElement: { style: {} },
  body: { appendChild: function (e) { e.parentNode = document.body; } },
  getElementById: function (id) { return __el(id); }, querySelector: function () { return null; }, addEventListener: function () {} };
window.AdminAuth = { fetch: function () { return Promise.resolve({ ok: false, status: 500, json: function () { return Promise.resolve({}); } }); } };
"""

JS_CEO_CASES = r"""
var html = window._cbTest.render(BRIEF);
var rows = String(html).split('<div>');
function rowOf(title) { return rows.filter(function (r) { return r.indexOf(title) >= 0; })[0] || ''; }
ok('開いたドリル: 「開いたが未提出 (10/19)」', rowOf('宿題 開いた（2問').indexOf('開いたが未提出 (10/19)') >= 0, rowOf('宿題 開いた（2問'));
ok('開いた宿題: 「開いたが未提出 (10/18)」', rowOf('開いた宿題').indexOf('開いたが未提出 (10/18)') >= 0, rowOf('開いた宿題'));
ok('未開封のドリル: 「👀 未開封」', rowOf('宿題 未開封（2問').indexOf('👀 未開封') >= 0 && rowOf('宿題 未開封（2問').indexOf('開いたが未提出') < 0, rowOf('宿題 未開封（2問'));
ok('未開封の宿題: 「👀 未開封」', rowOf('未開封の宿題').indexOf('👀 未開封') >= 0, rowOf('未開封の宿題'));
ok('記録の前 (opened null) は何も出さない', rowOf('記録の前のドリル').indexOf('👀') < 0 && rowOf('記録の前のドリル').indexOf('開いたが') < 0
   && rowOf('記録の前の宿題').indexOf('👀') < 0, [rowOf('記録の前のドリル'), rowOf('記録の前の宿題')]);
ok('生徒の行に「👀 未開封 2」', html.indexOf('👀 未開封 2</span>') >= 0, html.slice(0, 600));
ok('名前は escape', html.indexOf('架空 ブリーフ&lt;b&gt;一&lt;/b&gt;') >= 0 && html.indexOf('ブリーフ<b>') < 0);
var OLD = JSON.parse(JSON.stringify(BRIEF));
OLD.classes.forEach(function (c) { (c.members || []).forEach(function (m) { delete m.unopened_count; (m.open_items || []).forEach(function (it) { delete it.opened; delete it.opened_last_jst; }); }); });
var oh = window._cbTest.render(OLD);
ok('古いサーバ (opened なし) では 👀 も「開いたが」も出さない', oh.indexOf('👀') < 0 && oh.indexOf('開いたが未提出') < 0, oh.slice(0, 400));
var EV = JSON.parse(JSON.stringify(BRIEF));
EV.classes[0].members[0].open_items[0].opened = true; EV.classes[0].members[0].open_items[0].opened_last_jst = '<img src=x>';
ok('最後に開いた日も escape', window._cbTest.render(EV).indexOf('<img src=x>') < 0);
__emit();
"""


def check_screens(brief):
    H = load_harness()
    eng = H.js_engine()
    print(f"\n  JS エンジン: {eng[0] if eng else 'なし'}")
    check("JS の実行環境がある (node / osascript / jsc。無ければ FAIL)", bool(eng), "node も osascript も jsc も見つからない")
    if not eng:
        return
    load_hw = "function __loadHwNotice() {\n" + read(HW_JS) + "\n}\n"
    print("\n[4] hw-notice.js の 〆 (TZ=America/Los_Angeles)")
    run_js(eng, H.PRELUDE + load_hw + JS_PURE, "[4]", TZ_ENV)

    print("\n[5] class.html (偽の DOM と偽の API・TZ=America/Los_Angeles)")
    inline = H.inline_scripts(read(CLASS_HTML))
    check("class.html の inline script は 1 つ", len(inline) == 1, len(inline))
    if len(inline) == 1:
        boot = "function __bootClass() {\n" + inline[0] + "\n}\n"
        run_js(eng, H.PRELUDE + H.POLYFILL + H.FAKE_DOM + load_hw + H.JS_CLASS_SETUP + JS_CLASS_DUE_HELPERS + JS_CLASS_DUE_SETUP + boot
               + JS_CLASS_DUE_CASES, "[5]", TZ_ENV)

    print("\n[6] mypage.js の宿題欄 (偽の DOM・TZ=America/Los_Angeles)")
    try:
        sl = H.mypage_homework_slice(read(MYPAGE_JS))
    except ValueError:
        sl = None
        check("mypage.js の宿題欄の範囲が見つかる", False)
    if sl:
        run_js(eng, H.PRELUDE + H.POLYFILL + H.FAKE_DOM + load_hw + H.JS_MYPAGE_SETUP + sl + "\n" + JS_MYPAGE_DUE_SETUP + JS_MYPAGE_DUE_CASES,
               "[6]", TZ_ENV)

    print("\n[7] CEO の 🗓 授業ブリーフ (ceo.html の本物のコード)")
    blk = _ceo_brief_block(read(CEO_HTML))
    check("ブリーフのコードを切り出せた", bool(blk))
    if blk:
        prog = H.PRELUDE + JS_CEO_SETUP + "var BRIEF = " + json.dumps(brief, ensure_ascii=False) + ";\n" + blk + "\n" + JS_CEO_CASES
        run_js(eng, prog, "[7]")


def check_sources():
    print("\n[8] ソース検査")
    class_html, mypage_html = read(CLASS_HTML), read(MYPAGE_HTML)
    v1 = re.search(r'<script src="hw-notice\.js\?v=([^"]+)"></script>', class_html)
    v2 = re.search(r'<script src="hw-notice\.js\?v=([^"]+)"></script>', mypage_html)
    check("hw-notice.js の ?v= が class.html と mypage.html でそろう", bool(v1 and v2 and v1.group(1) == v2.group(1)), (v1 and v1.group(1), v2 and v2.group(1)))
    check("class.html: 解答用紙を開いたら (未提出のときだけ) hwPingOpened", "if (wasOpen) hwPingOpened(id);" in class_html)
    check("class.html: 👀 の POST は /api/student/homework/{id}/opened (keepalive)",
          "api('/api/student/homework/' + encodeURIComponent(k) + '/opened', { method: 'POST', body: '{}', keepalive: true })" in class_html)
    check("class.html: 帯の文言は hw-notice.js の banner()", "window.AJHwNotice.banner(n)" in class_html and "overdueLabel(n.overdue)" not in class_html)
    main_src = read(MAIN_PY)
    check("サーバ: 開いたの記録は GET のドリル取得の中 (新しいドリルのルートを足さない)",
          '_record_item_open(conn, student["id"], "gd", drill_id)' in main_src and "/api/student/grammar-drill/{drill_id}/opened" not in main_src)
    ci = read(CI_YML)
    check("CI (server-tests.yml) にこのテストの step がある", "python3 scripts/health_check/test_item_open_due.py" in ci)
    paths_block = ci.split("pull_request:")[0]
    for p in ("'hw-notice.js'", "'class.html'", "'mypage.js'", "'ceo.html'", "'server/**'"):
        check(f"CI の paths に {p}", p in paths_block)


def main():
    sys.path.insert(0, HERE)
    mod, client = check_server()
    brief, _f = check_brief(mod, client)
    check_screens(brief)
    check_sources()
    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for x in FAILURES:
            print("   -", x)
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
