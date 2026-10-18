#!/usr/bin/env python3
"""🗓 今日の授業ブリーフ (2026-10-18 塾長「①の授業前ブリーフも作っておいて」) の回帰テスト。

固定する性質 (一時 SQLite・外部通信なし・生徒名とメールは架空 = 公開リポジトリ):
  [1] 認証: 管理者トークンだけ (名前を返すので X-Cron-Secret・生徒トークン・壊れたトークン・無しは 401)。date の形が違う / 無い日付 /
      時間割に無いクラスは 400
  [2] 曜日: date の曜日 (JST) の時間割クラスを時間割の順に出す。date を省くと JST の今日 (日曜 23:59:59 は日曜のクラス・
      月曜 0:00:00 から月曜のクラス)。土曜は 0 クラス。class で 1 クラスだけ (全角・空白の違いは同じ名前・曜日が違っても出す = meets_on_date)
  [3] 名簿: 在籍の通塾生だけ (AIなし・AIあり・AI 体験中は入れて見分ける)。合成監視・テスト系の名前・退会・通塾生でない・
      受講開始月の前 (before_start_n に数える)・ほかの曜日だけのクラスの生徒は入れない
  [4] 未提出: クラス自動宿題・3日ドリル・15問ミッション・塾長のドリル・塾長の宿題 (記号の解答用紙の印)。今日の1問・初回診断は数えない。
      〆 (宿題の期限・クラス自動宿題の題名の「〆M/D」) を授業の日に過ぎていれば overdue・配ってからの日数・
      次の自動配信を止めている (クラス自動宿題と 3日ドリルの直近 14 日の未提出だけ) = blocking・最終ログイン (JST) と 30 日のログイン切れの疑い
  [5] 今週出した人: 月曜 0:00 JST から (日曜 23:59:59 の提出は入らない)・本数 (ドリル + 宿題)・一番よい点 (解答用紙の点も)・満点
  [6] 誤答の多い 3 問: このクラスのクラス自動宿題 + ほかのドリルはこのクラスの 2 人以上に配った分だけ・直近 14 日・数えるのはこのクラスの
      生徒の答えだけ・回答 2 件未満と誤答なしは選ばない・正解率が同じならこのクラスのクラス自動宿題が先 → 回答の多い順 → 問題 id・
      一番選ばれた誤答 (同数なら番号の小さい方)・本文は題名だけ (本文の中身は返さない)・習熟度テスト (科目・出典 pt- / ptest:) は出さない
  [7] 読むだけ: 何も書かない (INSERT/UPDATE/DELETE が 1 文も走らない・events も増えない)・ログに名前を出さない・
      生徒の数を 10 倍にしても SELECT の数は同じ (生徒ごとに回さない)・コードに DDL が無い
  [8] 画面: ceo.html の本物のコードを JS エンジンで動かす (CI は node・Mac は osascript / jsc。無ければ FAIL)。ハブの「👨‍🎓 生徒・学習」の
      先頭のボタン・🏫 クラス自動宿題カードのボタン・クラスごとの表 (在籍・未提出・〆過ぎ・N日・ログイン切れの疑い・今週出した人・
      誤答の多い 3 問)・名前の escape・📺 問題だけ表示 (名前を出さない・「正解を見せる」まで正解・正解率・一番多かった誤答を出さない・
      ← → で移動すると正解はまた隠す・Esc で閉じる)・古いサーバ (404 / 405 / version なし = 反映待ち・503 = 一時的)・遅れて届いた前の応答で
      上書きしない・その曜日に無いクラスの絞り込みは「すべて」に戻す・JST の今日 (端末のタイムゾーンに関係なく)

実行:
    python3 scripts/health_check/test_class_brief.py
    # exit 0 = PASS / 1 = FAIL
"""
import datetime
import importlib.util
import inspect
import json
import logging
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MAIN_PY = os.path.join(REPO, "server", "main.py")
CEO_HTML = os.path.join(REPO, "ceo.html")
CEO_JS = os.path.join(REPO, "ceo.js")
WORKFLOW = os.path.join(REPO, ".github", "workflows", "server-tests.yml")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "server"))
from test_grammar_import_units import admin_token  # noqa: E402
from test_grade_band_consistency import js_engine, run_js  # noqa: E402
from test_class_homework_routine import student_token, _JS_OUT  # noqa: E402

FAILURES = []
UTC = datetime.timezone.utc
L1 = "月曜1限 中学応用"
L2 = "月曜2限 英文法 Lv.1"
L3 = "月曜3限 長文読解 Lv.1"
T2 = "火曜2限 英文法 Lv.2"
W3 = "水曜3限 国公立コース 英文法"
NOW = datetime.datetime(2026, 10, 19, 1, 0, 0, tzinfo=UTC)   # = JST 10/19 (月) 10:00
ENV_KEYS = ("CLASS_HW_OPEN_STALE_DAYS", "CLASS_HW_INTERVAL_DAYS", "WEAKNESS_ROUTINE_OPEN_STALE_DAYS")
PASSAGE_BODY = "FICTIONAL PASSAGE BODY XYZZY-QUUX should never be returned"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:500]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="class_brief_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと **本番 Postgres** を読む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0", "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "", "ANTHROPIC_API_KEY": "", "BASE_URL": "https://example.invalid",
        "CRON_SECRET": "test-cron-secret",
    })
    for k in ENV_KEYS:
        os.environ.pop(k, None)
    spec = importlib.util.spec_from_file_location("aijuku_main_class_brief", MAIN_PY)
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


def table_counts(mod):
    tabs = ("students", "grammar_drills", "grammar_drill_assignments", "homework_assignments", "grammar_questions",
            "grammar_passages", "events", "homework_sheets", "homework_answer_keys", "notifications")
    return {t: q(mod, f"SELECT COUNT(*) AS n FROM {t}")[0]["n"] for t in tabs}


class Fx:
    """架空の名簿・ドリル・宿題・問題 (中身は全部この場で作る)。"""

    def __init__(self, mod):
        self.mod = mod
        self.seq = 0
        self.ids = {}

    def student(self, key, name, *, labels, grade="高2", ai_disabled=1, trial=None, status="paid", plan="student_addon",
                course=None, email=None, start_month=None, last_login=None):
        self.seq += 1
        sid = ex(self.mod,
                 "INSERT INTO students (name, email, status, grade, ai_disabled, ai_trial_until, plan, course, class_labels, start_month, last_login_at) "
                 "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id",
                 (name, email or f"brief-{self.seq:03d}@example.org", status, grade, ai_disabled, trial, plan, course,
                  json.dumps(labels, ensure_ascii=False), start_month, last_login))
        self.ids[key] = sid
        return sid

    def question(self, key, answer, *, subject="english", source="manual-drill-v1", passage_id=None, stem=None):
        sid = ex(self.mod,
                 "INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source, passage_id) "
                 "VALUES (?, '時制', 'standard', ?, ?, ?, '架空の解説', ?, ?) RETURNING id",
                 (subject, stem or f"架空の問題 {key} の空所に入る語は ( ) ?",
                  json.dumps([f"{key}-c0", f"{key}-c1", f"{key}-c2", f"{key}-c3"]), answer, source, passage_id))
        self.ids[key] = sid
        return sid

    def drill(self, key, created_by, qkeys, *, title="架空のドリル", subject="english", created_at="2026-10-15 21:00:05"):
        did = ex(self.mod,
                 "INSERT INTO grammar_drills (subject, title, unit, level, question_ids, created_by, created_at) "
                 "VALUES (?, ?, '時制', 'standard', ?, ?, ?) RETURNING id",
                 (subject, title, json.dumps([self.ids[k] for k in qkeys]), created_by, created_at))
        self.ids[key] = did
        return did

    def assign(self, dkey, skey, *, assigned_at, status="open", completed_at=None, answers=None):
        ans = None
        sc = st = None
        if answers is not None:
            ans = json.dumps({str(self.ids[k]): v for k, v in answers.items()})
            st = len(answers)
            qrows = q(self.mod, f"SELECT id, answer FROM grammar_questions WHERE id IN ({','.join(str(self.ids[k]) for k in answers)})")
            amap = {r["id"]: r["answer"] for r in qrows}
            sc = sum(1 for k, v in answers.items() if amap.get(self.ids[k]) == v)
        ex(self.mod,
           "INSERT INTO grammar_drill_assignments (drill_id, student_id, status, score_correct, score_total, answers_json, assigned_at, completed_at) "
           "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
           (self.ids[dkey], self.ids[skey], status, sc, st, ans, assigned_at, completed_at))

    def homework(self, key, skey, title, *, due=None, created_at="2026-10-12 03:00:00", status="open", completed_at=None):
        hid = ex(self.mod,
                 "INSERT INTO homework_assignments (student_id, title, subject, due_date, status, created_at, completed_at, created_by) "
                 "VALUES (?, ?, '英語', ?, ?, ?, ?, 'admin') RETURNING id",
                 (self.ids[skey], title, due, status, created_at, completed_at))
        self.ids[key] = hid
        return hid


def build_fixtures(mod):
    f = Fx(mod)
    # ── 名簿 (月曜 2 限 = A・B・D・E の 4 名 / 月曜 1 限 = C / 月曜 3 限 = 0 名) ──
    f.student("A", "架空 一郎", labels=[L2], grade="高2", last_login="2026-10-16 23:00:00")                 # 10/17 08:00 JST
    f.student("B", "架空<img src=x onerror=alert(1)>次郎", labels=[L2, W3], grade="高3", ai_disabled=0, plan=None,
              course="kokuritsu_nankan", last_login=None)                                                  # 一度もログインなし
    f.student("C", "架空 三子", labels=[L1], grade="中3", last_login="2026-09-10 03:00:00")                 # 39 日前
    f.student("D", "架空 四郎", labels=[L2], grade="高1", last_login="2026-10-09 01:00:00")
    f.student("E", "架空 五子", labels=[L2], grade="高2", trial="2026-11-30 00:00:00", last_login="2026-10-18 01:00:00")  # AI 体験中
    f.student("F", "架空 合成", labels=[L2], email="brief-f@synthetic-monitor.example")
    f.student("G", "テスト 太郎", labels=[L2])
    f.student("H", "架空 退会", labels=[L2], status="canceled")
    f.student("I", "架空 外部", labels=[L2], plan="premium")
    f.student("J", "架空 十二月", labels=[L2], start_month="2026-12")
    f.student("K", "架空 火曜", labels=[T2])
    # ── 問題 ──
    pid = ex(mod, "INSERT INTO grammar_passages (subject, unit, level, title, body, source) VALUES "
                  "('english', '時制', 'standard', 'Fictional Passage Title', ?, 'manual-drill-v1') RETURNING id", (PASSAGE_BODY,))
    f.question("q1", 1)
    f.question("q2", 0, passage_id=pid)
    f.question("q3", 2)
    f.question("q4", 3)
    f.question("q5", 0)
    f.question("q6", 1)
    f.question("q8", 2)
    f.question("q9", 0, subject="proficiency_test", source="pt-T1-Q1", stem="架空の習熟度テスト PTEST-STEM-ONE")
    f.question("q10", 0, source="ptest:T1:S01", stem="架空の出典 PTEST-STEM-TWO")
    f.question("q11", 0)
    f.question("q13", 0)
    # ── ドリル ──
    chw = f"class_hw_auto:kosei:{L2}"
    f.drill("D1", chw, ["q1", "q2", "q3", "q4", "q8"], title=f"【{L2}】宿題 時制（5問・〆10/18）", created_at="2026-10-15 21:00:05")
    f.assign("D1", "A", assigned_at="2026-10-15 21:00:05")                                                     # 未提出・〆過ぎ・次が止まる
    f.assign("D1", "D", assigned_at="2026-10-15 21:00:05", status="completed", completed_at="2026-10-18 15:00:00",   # = 月曜 0:00 JST
             answers={"q1": 2, "q2": 0, "q3": 2, "q4": 1, "q8": 0})
    f.assign("D1", "E", assigned_at="2026-10-15 21:00:05", status="completed", completed_at="2026-10-18 14:59:59",   # = 日曜 23:59:59 JST
             answers={"q1": 2, "q2": 3, "q3": 2, "q4": 3})
    f.drill("D2", "weakness_routine_3d", ["q13"], title="🎯 3日ドリル 時制", created_at="2026-10-16 20:30:00")
    f.assign("D2", "B", assigned_at="2026-10-16 20:30:00")
    f.drill("D3", "admin", ["q13"], title="塾長の古いドリル", created_at="2026-09-20 01:00:00")
    f.assign("D3", "B", assigned_at="2026-09-20 01:00:00")
    f.drill("D4", "mission_2day_routine", ["q13"], title="弱点15問ミッション", created_at="2026-10-17 00:00:00")
    f.assign("D4", "A", assigned_at="2026-10-17 00:00:00", status="assigned")
    f.drill("D5", "today_question", ["q13"], title="📝 今日の1問", created_at="2026-10-18 00:00:00")
    f.assign("D5", "A", assigned_at="2026-10-18 00:00:00")
    f.drill("D6", "diagnostic", ["q13"], title="🔰 はじめての実力チェック", created_at="2026-10-18 00:00:00")
    f.assign("D6", "D", assigned_at="2026-10-18 00:00:00")
    f.drill("D7", "admin", ["q5", "q10"], title="時制ドリル（標準）", created_at="2026-10-14 01:00:00")
    f.assign("D7", "B", assigned_at="2026-10-14 01:00:00", status="completed", completed_at="2026-10-14 10:00:00", answers={"q5": 2, "q10": 1})
    f.assign("D7", "D", assigned_at="2026-10-14 01:00:00", status="completed", completed_at="2026-10-14 11:00:00", answers={"q5": 3, "q10": 1})
    f.drill("D8", "admin", ["q6"], title="1 人だけのドリル", created_at="2026-10-14 01:00:00")
    f.assign("D8", "D", assigned_at="2026-10-14 01:00:00", status="completed", completed_at="2026-10-14 12:00:00", answers={"q6": 0})
    f.assign("D8", "K", assigned_at="2026-10-14 01:00:00", status="completed", completed_at="2026-10-14 12:00:00", answers={"q6": 0})
    f.drill("D10", "admin", ["q9"], title="🧪 習熟度テスト", subject="proficiency_test", created_at="2026-10-14 01:00:00")
    f.assign("D10", "B", assigned_at="2026-10-14 01:00:00", status="completed", completed_at="2026-10-14 13:00:00", answers={"q9": 2})
    f.assign("D10", "D", assigned_at="2026-10-14 01:00:00", status="completed", completed_at="2026-10-14 13:00:00", answers={"q9": 2})
    f.drill("D11", chw, ["q11"], title=f"【{L2}】宿題 古い（1問・〆9/23）", created_at="2026-09-20 21:00:00")
    f.assign("D11", "D", assigned_at="2026-09-20 21:00:00", status="completed", completed_at="2026-09-21 10:00:00", answers={"q11": 1})
    f.assign("D11", "E", assigned_at="2026-09-20 21:00:00", status="completed", completed_at="2026-09-21 10:00:00", answers={"q11": 1})
    f.drill("D13", chw, ["q13"], title=f"【{L2}】宿題 比較（1問・〆10/3）", created_at="2026-09-30 21:00:00")
    f.assign("D13", "A", assigned_at="2026-09-30 21:00:00")                                                    # 14 日より前 = 止めない
    # ── 宿題 (塾長が出した分) ──
    f.homework("H1", "C", "架空プリント第3回", due="2026-10-15", created_at="2026-10-12 03:00:00")
    f.homework("H2", "A", "架空プリント第4回", due="2026-10-25", created_at="2026-10-18 03:00:00")
    f.homework("H3", "D", "架空プリント第2回", due="2026-10-20", created_at="2026-10-12 03:00:00", status="completed",
               completed_at="2026-10-19 00:30:00")
    f.homework("H4", "E", "架空プリント第2回", due="2026-10-20", created_at="2026-10-12 03:00:00", status="completed",
               completed_at="2026-10-18 14:59:59")
    f.homework("H5", "B", "架空プリント第2回", due="2026-10-20", created_at="2026-10-12 03:00:00", status="completed",
               completed_at="2026-10-19 00:10:00")
    sheet_ready = mod._hw_sheet_ready()
    if sheet_ready:
        kid = ex(mod, "INSERT INTO homework_answer_keys (title, num_questions, num_choices, label_style, key_json) "
                      "VALUES ('架空の正解表', 5, 4, 'circled', '[1,2,3,4,1]') RETURNING id")
        ex(mod, "INSERT INTO homework_sheets (homework_id, student_id, mode, key_id) VALUES (?, ?, 'choice', ?)", (f.ids["H1"], f.ids["C"], kid))
        ex(mod, "INSERT INTO homework_sheets (homework_id, student_id, mode, key_id, answers_json, score_correct, score_total, submitted_at) "
                "VALUES (?, ?, 'choice', ?, '[1,2,3,4,1]', 5, 5, '2026-10-19 00:30:00')", (f.ids["H3"], f.ids["D"], kid))
    return f, sheet_ready


def get(client, adm, **params):
    return client.get("/api/admin/class-brief", params=params, headers=adm)


def by_label(d):
    return {c["label"]: c for c in (d.get("classes") or [])}


def check_server(mod, client, adm, f, sheet_ready):
    ids = f.ids
    print("\n[1] 認証と入力")
    r = client.get("/api/admin/class-brief", params={"date": "2026-10-19"})
    check("トークン無しは 401", r.status_code == 401, r.status_code)
    r = client.get("/api/admin/class-brief", params={"date": "2026-10-19"}, headers={"X-Cron-Secret": "test-cron-secret"})
    check("X-Cron-Secret では読めない (名前を返すので管理者トークンだけ) = 401", r.status_code == 401, r.status_code)
    r = client.get("/api/admin/class-brief", params={"date": "2026-10-19"}, headers={"Authorization": "Bearer " + student_token(mod, ids["A"])})
    check("生徒のトークンは 401", r.status_code == 401, r.status_code)
    r = client.get("/api/admin/class-brief", params={"date": "2026-10-19"}, headers={"Authorization": "Bearer xxx.yyy"})
    check("壊れたトークンは 401", r.status_code == 401, r.status_code)
    for bad in ("2026/10/19", "abc", "2026-02-30", "2026-10-19x"):
        r = get(client, adm, date=bad)
        check(f"date={bad!r} は 400", r.status_code == 400, (r.status_code, r.text[:120]))
    r = get(client, adm, date="2026-10-19", **{"class": "月曜9限 架空クラス"})
    check("時間割に無いクラスは 400", r.status_code == 400, (r.status_code, r.text[:120]))

    print("\n[2] 曜日・既定の日付 (JST の 0:00 の境目)・クラスの絞り込み")
    mod._class_brief_now = lambda: datetime.datetime(2026, 10, 18, 14, 59, 59, tzinfo=UTC)   # = 日曜 23:59:59 JST
    d = get(client, adm).json()
    check("date を省く: JST 日曜 23:59:59 → 10/18 (日) の日曜のクラス",
          d.get("date") == "2026-10-18" and d.get("dow") == 0 and [c["label"] for c in d["classes"]] == ["日曜 高校国語"], (d.get("date"), d.get("dow")))
    mod._class_brief_now = lambda: datetime.datetime(2026, 10, 18, 15, 0, 0, tzinfo=UTC)     # = 月曜 0:00:00 JST
    d = get(client, adm).json()
    check("date を省く: JST 月曜 0:00:00 → 10/19 (月) の 3 クラスを時間割の順に",
          d.get("date") == "2026-10-19" and d.get("dow") == 1 and d.get("dow_ja") == "月"
          and [c["label"] for c in d["classes"]] == [L1, L2, L3], (d.get("date"), [c["label"] for c in d.get("classes", [])]))
    mod._class_brief_now = lambda: NOW
    d = get(client, adm, date="2026-10-24").json()
    check("土曜は 0 クラス (エラーにしない)", d.get("ok") is True and d.get("classes") == [] and d.get("dow") == 6, d)
    d = get(client, adm, date="2026-10-19", **{"class": "月曜２限　英文法 Lv.1"}).json()
    check("class の全角・空白の違いは同じクラス (1 クラスだけ)", [c["label"] for c in d.get("classes", [])] == [L2] and d.get("class_filter") == L2,
          [c["label"] for c in d.get("classes", [])])
    d = get(client, adm, date="2026-10-19", **{"class": T2}).json()
    check("曜日の違うクラスを指定しても出す (meets_on_date: false)",
          [c["label"] for c in d.get("classes", [])] == [T2] and d["classes"][0]["meets_on_date"] is False
          and [m["id"] for m in d["classes"][0]["members"]] == [ids["K"]], d.get("classes"))
    d = get(client, adm, date="2026-10-20").json()
    check("明日 (10/20 火) は火曜のクラス", d.get("dow") == 2 and T2 in by_label(d), [c["label"] for c in d.get("classes", [])])
    check("timetable = 15 クラス (CEO のクラスの選択肢)", len(d.get("timetable") or []) == 15 and all({"label", "dow", "time"} <= set(t) for t in d["timetable"]))

    print("\n[3] 名簿")
    mon = get(client, adm, date="2026-10-19").json()
    check("version: 1 (CEO の「サーバ反映待ち」の判定)", mon.get("version") == 1 and mon.get("ok") is True)
    check("today・as_of・week_start (月曜)", mon.get("today") == "2026-10-19" and mon.get("as_of") == "2026-10-19"
          and mon.get("week_start") == "2026-10-19", (mon.get("today"), mon.get("as_of"), mon.get("week_start")))
    cl = by_label(mon)
    c2 = cl.get(L2) or {}
    mem = {m["id"]: m for m in c2.get("members", [])}
    check("月曜2限 = A・B・D・E (合成監視・テスト名・退会・通塾生でない・受講開始前・火曜だけ は入れない)",
          set(mem) == {ids[k] for k in "ABDE"}, sorted(mem))
    check("在籍 4・未提出のいる生徒 2・受講開始前 1", c2.get("members_n") == 4 and c2.get("open_members_n") == 2 and c2.get("before_start_n") == 1,
          (c2.get("members_n"), c2.get("open_members_n"), c2.get("before_start_n")))
    check("月曜1限 = C だけ・月曜3限 = 0 名", [m["id"] for m in cl[L1]["members"]] == [ids["C"]] and cl[L3]["members"] == [] and cl[L3]["members_n"] == 0)
    check("並びは未提出の多い順 (A 4 本 → B 2 本 → 0 本の 2 名)", [m["id"] for m in c2["members"]][:2] == [ids["A"], ids["B"]], [m["id"] for m in c2["members"]])
    a, b, dd, e, cc = mem.get(ids["A"], {}), mem.get(ids["B"], {}), mem.get(ids["D"], {}), mem.get(ids["E"], {}), cl[L1]["members"][0]
    check("AIなし / AIあり / AI 体験中 の見分け", (a.get("ai_path"), a.get("ai_label")) == ("ai_nashi", "AIなし")
          and (b.get("ai_path"), b.get("ai_label")) == ("ai", "AIあり") and (e.get("ai_path"), e.get("ai_label")) == ("ai", "AI体験中"),
          [(m.get("ai_path"), m.get("ai_label")) for m in (a, b, e)])
    check("学年の区分 (高校 / 中学)", a.get("band") == "kosei" and cc.get("band") == "chugaku", (a.get("band"), cc.get("band")))
    check("最終ログイン (JST の M/D・offset 付き UTC)・2 日前は切れていない", a.get("last_login_jst") == "10/17" and a.get("login_stale") is False
          and a.get("login_days") == 2 and str(a.get("last_login_at") or "").endswith("+00:00"), (a.get("last_login_jst"), a.get("login_days"), a.get("last_login_at")))
    check("一度もログインしていない = ログイン切れの疑い", b.get("login_stale") is True and b.get("last_login_jst") is None and b.get("login_days") is None)
    check("39 日前のログイン = ログイン切れの疑い・10 日前は違う", cc.get("login_stale") is True and cc.get("login_days") == 39 and dd.get("login_stale") is False,
          (cc.get("login_days"), dd.get("login_days")))

    print("\n[4] 未提出")
    a_items = a.get("open_items") or []
    kinds = sorted(it["kind"] for it in a_items)
    check("A の未提出 = クラス自動宿題 2・15問ミッション・宿題 (今日の1問は数えない)", kinds == ["class_hw", "class_hw", "homework", "mission"]
          and a.get("open_count") == 4, kinds)
    d1 = next((it for it in a_items if it.get("drill_id") == ids["D1"]), {})
    check("クラス自動宿題: 〆は題名から (10/18)・授業の日 10/19 に〆過ぎ・3 日・次が止まる",
          d1.get("due") == "2026-10-18" and d1.get("due_jst") == "10/18" and d1.get("overdue") is True and d1.get("days_open") == 3
          and d1.get("blocking") is True and d1.get("assigned_jst") == "10/16", d1)
    d13 = next((it for it in a_items if it.get("drill_id") == ids["D13"]), {})
    check("14 日より前のクラス自動宿題は止めない (積まない判定と同じ境目)・〆過ぎ", d13.get("blocking") is False and d13.get("overdue") is True
          and d13.get("days_open") == 18, d13)
    d4 = next((it for it in a_items if it.get("drill_id") == ids["D4"]), {})
    check("15問ミッション ('assigned' も未提出)・止めない", d4.get("kind") == "mission" and d4.get("blocking") is False, d4)
    h2 = next((it for it in a_items if it.get("homework_id") == ids["H2"]), {})
    check("塾長の宿題: 期限 10/25 は〆過ぎではない", h2.get("kind") == "homework" and h2.get("due") == "2026-10-25" and h2.get("overdue") is False, h2)
    check("A の数: 〆過ぎ 2・止める 1・いちばん古い 18 日", (a.get("overdue_count"), a.get("blocking_count"), a.get("oldest_days")) == (2, 1, 18),
          (a.get("overdue_count"), a.get("blocking_count"), a.get("oldest_days")))
    check("並び: 〆過ぎが先", [it["overdue"] for it in a_items][:2] == [True, True], [it["overdue"] for it in a_items])
    b_items = {it["kind"]: it for it in (b.get("open_items") or [])}
    check("3日ドリルの未提出 (直近) は次が止まる・〆なし", b_items.get("routine", {}).get("blocking") is True and b_items["routine"].get("due") is None,
          b_items.get("routine"))
    check("塾長の古いドリル: 止めない・29 日", b_items.get("admin", {}).get("blocking") is False and b_items["admin"].get("days_open") == 29, b_items.get("admin"))
    check("初回診断は数えない (D は未提出 0)", dd.get("open_count") == 0 and dd.get("open_items") == [], dd.get("open_items"))
    h1 = (cc.get("open_items") or [{}])[0]
    check("C の宿題: 期限 10/15 → 〆過ぎ" + ("・記号の解答用紙の印" if sheet_ready else ""),
          h1.get("homework_id") == ids["H1"] and h1.get("overdue") is True and h1.get("answer_sheet") is sheet_ready, h1)
    past = get(client, adm, date="2026-10-12").json()
    pa = {m["id"]: m for m in by_label(past)[L2]["members"]}.get(ids["A"], {})
    pd1 = next((it for it in pa.get("open_items", []) if it.get("drill_id") == ids["D1"]), {})
    check("過去の日を開いても〆過ぎ・日数は今日 (10/19) で数える", past.get("as_of") == "2026-10-19" and pd1.get("days_open") == 3
          and pd1.get("overdue") is True, (past.get("as_of"), pd1))
    with_env = os.environ.get("CLASS_HW_OPEN_STALE_DAYS")
    os.environ["CLASS_HW_OPEN_STALE_DAYS"] = "0"
    try:
        z = get(client, adm, date="2026-10-19").json()
        za = {m["id"]: m for m in by_label(z)[L2]["members"]}[ids["A"]]
        check("CLASS_HW_OPEN_STALE_DAYS=0 (全部数える) なら古いクラス自動宿題も止める", za.get("blocking_count") == 2, za.get("blocking_count"))
    finally:
        if with_env is None:
            os.environ.pop("CLASS_HW_OPEN_STALE_DAYS", None)
        else:
            os.environ["CLASS_HW_OPEN_STALE_DAYS"] = with_env

    print("\n[5] 今週出した人 (月曜 0:00 JST から)")
    pr = c2.get("submitted_this_week") or []
    check("今週出した人 = D (2 本) → B (1 本)・日曜 23:59:59 に出した E と未提出の A は入らない",
          [p["id"] for p in pr] == [ids["D"], ids["B"]], [(p.get("id"), p.get("count")) for p in pr])
    p_d = pr[0] if pr else {}
    check("D: ドリル 1 (月曜 0:00:00 ちょうど) + 宿題 1", p_d.get("count") == 2 and p_d.get("drills") == 1 and p_d.get("homework") == 1, p_d)
    if sheet_ready:
        check("一番よい点は解答用紙の 5/5・満点", p_d.get("best") == {"correct": 5, "total": 5, "pct": 100} and p_d.get("perfect") is True, p_d)
    else:
        check("一番よい点はドリルの 2/5", p_d.get("best") == {"correct": 2, "total": 5, "pct": 40}, p_d)
    p_b = pr[1] if len(pr) > 1 else {}
    check("B: 点の無い宿題だけ → best なし・名前つき", p_b.get("best") is None and p_b.get("count") == 1 and p_b.get("name") == mem[ids["B"]]["name"], p_b)

    print("\n[6] 誤答の多い 3 問")
    top = c2.get("top_missed") or []
    qid = {v: k for k, v in ids.items() if k.startswith("q")}
    check("3 問 = q1 (0%・このクラス) → q5 (0%・ほかのドリル 2 名) → q2 (50%・q4 と同じなら id の小さい方)",
          [qid.get(t["question_id"]) for t in top] == ["q1", "q5", "q2"], [qid.get(t["question_id"]) for t in top])
    t1 = top[0] if top else {}
    check("q1: 正解率 0 (0/2)・一番選ばれた誤答は ③ (2 件)・選択肢の数・このクラスのクラス自動宿題",
          t1.get("accuracy") == 0 and t1.get("accuracy_pct") == 0 and t1.get("n") == 2 and t1.get("correct_n") == 0
          and t1.get("wrong_top") == {"index": 2, "count": 2} and t1.get("choice_counts") == [0, 0, 2, 0] and t1.get("from_class_hw") is True
          and t1.get("answer") == 1 and t1.get("choices") == ["q1-c0", "q1-c1", "q1-c2", "q1-c3"], t1)
    t2 = top[1] if len(top) > 1 else {}
    check("q5: ほかのドリル・誤答が 1 件ずつなら番号の小さい方 (③)", t2.get("from_class_hw") is False and t2.get("wrong_top") == {"index": 2, "count": 1}, t2)
    t3 = top[2] if len(top) > 2 else {}
    check("q2: 本文は題名だけ", t3.get("passage_title") == "Fictional Passage Title" and t3.get("accuracy_pct") == 50, t3)
    dump = json.dumps(mon, ensure_ascii=False)
    check("本文の中身は応答のどこにも無い", PASSAGE_BODY not in dump)
    check("習熟度テスト (科目 / 出典 pt- / ptest:) の問題は出ない", "PTEST-STEM-ONE" not in dump and "PTEST-STEM-TWO" not in dump)
    got = {qid.get(t["question_id"]) for c in mon["classes"] for t in c.get("top_missed", [])}
    check("回答 1 件 (q8)・誤答なし (q3)・クラスの 1 人だけのドリル (q6)・14 日より前 (q11) は選ばない",
          not ({"q8", "q3", "q6", "q11", "q9", "q10"} & got), got)
    check("月曜1限 (回答なし) は 0 問", cl[L1]["top_missed"] == [])
    check("q6 は火曜のクラスの生徒の答えも数えない (月曜2限の 1 人 + 火曜の 1 人 = 2 件でも出さない)", "q6" not in got)

    print("\n[7] 読むだけ・名前をログに出さない・生徒ごとに回さない")
    before = table_counts(mod)
    names = [m["name"] for c in mon["classes"] for m in c["members"]]
    recs = []

    class H(logging.Handler):
        def emit(self, rec):
            try:
                recs.append(rec.getMessage())
            except Exception:
                recs.append(str(rec.msg))
    h = H(level=logging.DEBUG)
    root = logging.getLogger()
    root.addHandler(h)
    old_level = root.level
    root.setLevel(logging.DEBUG)
    stmts = []
    orig_db = mod.db

    def tracing_db():
        conn = orig_db()
        try:
            conn._conn.set_trace_callback(stmts.append)
        except Exception:
            pass
        return conn
    mod.db = tracing_db
    try:
        get(client, adm, date="2026-10-19")   # 温める (列の有無のキャッシュ)
        stmts.clear()
        r1 = get(client, adm, date="2026-10-19")
        n_small = sum(1 for s in stmts if s.lstrip().upper().startswith("SELECT"))
        writes = [s for s in stmts if re.match(r"\s*(INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|REPLACE)\b", s, re.I)]
    finally:
        mod.db = orig_db
        root.removeHandler(h)
        root.setLevel(old_level)
    check("200", r1.status_code == 200, r1.status_code)
    check("書く SQL が 1 文も走らない", not writes, writes[:3])
    check("表の行数が変わらない (events も)", table_counts(mod) == before, (before, table_counts(mod)))
    check("ログに生徒の名前を出さない", not [m for m in recs if any(n and n in m for n in names)], [m for m in recs if any(n and n in m for n in names)][:3])
    for i in range(40):   # 生徒を 10 倍に (未提出・提出済みの答えつき)
        f.student(f"X{i}", f"架空 追加{i:02d}", labels=[L2], last_login="2026-10-18 01:00:00")
        f.assign("D1", f"X{i}", assigned_at="2026-10-15 21:00:05", status="completed" if i % 2 else "open",
                 completed_at="2026-10-19 00:00:00" if i % 2 else None, answers={"q1": 2, "q2": 0} if i % 2 else None)
        f.homework(f"HX{i}", f"X{i}", "架空プリント追加", due="2026-10-30")
    stmts2 = []

    def tracing_db2():
        conn = orig_db()
        try:
            conn._conn.set_trace_callback(stmts2.append)
        except Exception:
            pass
        return conn
    mod.db = tracing_db2
    try:
        r2 = get(client, adm, date="2026-10-19")
    finally:
        mod.db = orig_db
    n_big = sum(1 for s in stmts2 if s.lstrip().upper().startswith("SELECT"))
    big = by_label(r2.json()).get(L2, {}) if r2.status_code == 200 else {}
    check("生徒を 10 倍にしても SELECT の数は同じ (生徒ごとに回さない)", n_small == n_big and n_small > 0 and big.get("members_n") == 44,
          (n_small, n_big, big.get("members_n")))
    src = inspect.getsource(mod._class_brief_build) + inspect.getsource(mod.admin_class_brief)
    check("コードに書く SQL・DDL が無い", not re.search(r"\b(INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\b", src))
    check("events に書かない・commit しない", not re.search(r"INTO\s+events", src) and ".commit(" not in src and "_record_" not in src)
    check("認証は _verify_admin_required だけ (X-Cron-Secret を受けない)", "_verify_admin_required(authorization)" in src
          and "x_cron_secret" not in src and "_grammar_admin_authed" not in src)
    check("〆の年: 12/28 に配った「〆1/2」は翌年・読めない日付は None",
          mod._class_brief_title_due("【架空】宿題（10問・〆1/2）", datetime.date(2026, 12, 28)) == datetime.date(2027, 1, 2)
          and mod._class_brief_title_due("〆10/18", datetime.date(2026, 10, 16)) == datetime.date(2026, 10, 18)
          and mod._class_brief_title_due("〆2/30", datetime.date(2026, 2, 1)) is None
          and mod._class_brief_title_due("〆の無い題名", datetime.date(2026, 2, 1)) is None)
    return mon


def _js_script_block(src):
    head = "  // 🗓 今日の授業ブリーフ (2026-10-18"
    i = src.find(head)
    j = src.find("  </script>", i)
    return src[i:j] if 0 <= i < j else ""


def check_screens(mon, sat, f):
    print("\n[8] 画面 (ceo.html の本物のコードを JS エンジンで動かす)")
    ceo = open(CEO_HTML, encoding="utf-8").read()
    ceo_js = open(CEO_JS, encoding="utf-8").read()
    grp = ceo.find("<h3>👨‍🎓 生徒・学習</h3>")
    first_btn = ceo.find("<button", grp)
    check("ハブ「👨‍🎓 生徒・学習」の先頭のボタンが 🗓 今日の授業", grp > 0 and ceo.find('data-hub-target="classBriefSection"', first_btn) == ceo.find('data-hub-target=', first_btn))
    pos = [ceo.find('<section id="ceoHubMenu">'), ceo.find('\n    <section id="classBriefSection"'), ceo.find('<section id="weaknessHeatmapSection"')]
    check("セクションはハブのすぐ後 (.ceo-main 直下 = ハブのボタンで開ける)", min(pos) >= 0 and pos == sorted(pos), pos)
    chw = ceo[ceo.find('id="chwBox"'):ceo.find('id="chwResult"')]
    check("🏫 クラス自動宿題カードからも開ける (cbOpenFromCard)", 'onclick="cbOpenFromCard()"' in chw)
    check("URL は 1 か所 (CB_URL)", len(re.findall(r"""[`'"]/api/admin/class-brief""", ceo)) == 1 and "var CB_URL = '/api/admin/class-brief';" in ceo)
    check("ceo.js は触らない (inline だけ)", "class-brief" not in ceo_js and "classBriefSection" not in ceo_js)
    blk = _js_script_block(ceo)
    check("ブリーフのコードを切り出せた", bool(blk))
    check("読むだけ (POST しない)", "method:" not in blk and "'POST'" not in blk)
    eng = js_engine()
    check("JS の実行環境がある (node / osascript / jsc。無ければ FAIL)", bool(eng))
    if not eng or not blk:
        return
    names = sorted({m["name"] for c in mon["classes"] for m in c["members"]}
                   | {p["name"] for c in mon["classes"] for p in c["submitted_this_week"]})
    c2i = [c["label"] for c in mon["classes"]].index(L2)
    ids = f.ids
    tue = {"ok": True, "version": 1, "date": "2026-10-20", "dow": 2, "dow_ja": "火", "today": "2026-10-19", "timetable": mon["timetable"],
           "classes": [{"label": T2, "time": "20:25–21:25", "members": [], "members_n": 0, "open_members_n": 0, "submitted_this_week": [], "top_missed": []}]}
    prog = "\n".join([
        "var window = (typeof globalThis !== 'undefined') ? globalThis : this;",
        "var __o = { urls: [], moved: false };",
        "var __els = {};",
        "function __el(id) { if (!__els[id]) __els[id] = { id: id, innerHTML: '', value: '', style: {}, parentNode: null }; return __els[id]; }",
        "var __keys = [];",
        "var document = { readyState: 'complete', body: { appendChild: function (e) { e.parentNode = document.body; __o.moved = true; } },",
        "  getElementById: function (id) { return __el(id); }, querySelector: function () { return null; },",
        "  addEventListener: function (t, fn) { if (t === 'keydown') __keys.push(fn); } };",
        "function __key(k) { for (var i = 0; i < __keys.length; i++) __keys[i]({ key: k, preventDefault: function () {} }); }",
        "var __queue = [];",
        "function __res(status, body) { return { ok: status >= 200 && status < 300, status: status,",
        "  json: function () { return body === undefined ? Promise.reject(new Error('no json')) : Promise.resolve(body); } }; }",
        "window.AdminAuth = { fetch: function (path) { __o.urls.push(path); var r = __queue.shift(); return (r && typeof r.then === 'function') ? r : Promise.resolve(r); } };",
        f"var MON = {json.dumps(mon, ensure_ascii=False)};",
        f"var SAT = {json.dumps(sat, ensure_ascii=False)};",
        f"var TUE = {json.dumps(tue, ensure_ascii=False)};",
        "var __realNow = Date.now;",
        "Date.now = function () { return Date.UTC(2026, 9, 19, 1, 0, 0); };",
        blk,
        "(async function () {",
        "  __o.keyBound = __keys.length; __o.movedAtInit = __o.moved;",
        "  __queue.push(__res(200, MON)); await cbSetDay(0);",
        "  __o.url1 = __o.urls[0]; __o.date1 = __el('cbDate').value; __o.render = __el('cbResult').innerHTML;",
        "  __o.msg = __el('cbMsg').innerHTML; __o.opts = __el('cbClass').innerHTML;",
        f"  window.cbShareOpen({c2i}); __o.shareDisp1 = __el('cbShare').style.display; __o.share1 = __el('cbShare').innerHTML;",
        "  window.cbShareReveal(); __o.share1r = __el('cbShare').innerHTML;",
        "  __key('ArrowRight'); __o.share2 = __el('cbShare').innerHTML;",
        "  __key('ArrowRight'); __o.share3 = __el('cbShare').innerHTML;",
        "  __key('ArrowRight'); __o.share3b = __el('cbShare').innerHTML;",
        "  __key('ArrowLeft'); __o.share2b = __el('cbShare').innerHTML;",
        "  __queue.push(__res(200, TUE)); __el('cbDate').value = '2026-10-20'; await cbLoad(); __o.shareAfterReload = __el('cbShare').innerHTML;",
        "  __key('Escape'); __o.shareDispEsc = __el('cbShare').style.display; __o.shareEsc = __el('cbShare').innerHTML;",
        "  __queue.push(__res(200, MON)); __el('cbDate').value = '2026-10-19'; await cbLoad();",
        "  window.cbShareOpen(0); __o.shareNoTop = __el('cbShare').style.display;",
        "  window.cbShareOpen(99); __o.shareBad = __el('cbShare').style.display;",
        "  window.cbShareOpen(" + str(c2i) + "); window.cbShareClose(); __o.shareClosed = __el('cbShare').style.display;",
        "  var nu = __o.urls.length;",
        f"  __el('cbClass').value = {json.dumps(T2, ensure_ascii=False)}; __queue.push(__res(200, MON)); await cbLoad();",
        "  __o.urlReset = __o.urls[nu]; __o.selAfterReset = __el('cbClass').value;",
        f"  __el('cbClass').value = {json.dumps(L2, ensure_ascii=False)}; __queue.push(__res(200, MON)); await cbLoad(); __o.urlClass = __o.urls[nu + 1];",
        "  __el('cbClass').value = '';",
        "  __queue.push(__res(404, { detail: 'Not Found' })); await cbLoad(); __o.r404 = __el('cbResult').innerHTML;",
        "  __queue.push(__res(405, { detail: 'Method Not Allowed' })); await cbLoad(); __o.r405 = __el('cbResult').innerHTML;",
        "  __queue.push(__res(503, { detail: 'down' })); await cbLoad(); __o.r503 = __el('cbResult').innerHTML;",
        "  __queue.push(__res(200, { ok: true })); await cbLoad(); __o.rOld = __el('cbResult').innerHTML;",
        "  __queue.push(__res(500, { detail: '<b>x</b>' })); await cbLoad(); __o.r500 = __el('cbResult').innerHTML;",
        "  __queue.push(__res(502)); await cbLoad(); __o.r502 = __el('cbResult').innerHTML;",
        "  __queue.push(__res(200, SAT)); await cbLoad(); __o.rSat = __el('cbResult').innerHTML;",
        "  var r1, r2; __queue.push(new Promise(function (res) { r1 = res; })); __queue.push(new Promise(function (res) { r2 = res; }));",
        "  var p1 = cbLoad(); var p2 = cbLoad(); r2(__res(200, TUE)); await p2; r1(__res(404, {})); await p1;",
        "  __o.race = __el('cbResult').innerHTML;",
        "  Date.now = function () { return Date.UTC(2026, 9, 18, 14, 59, 59); }; __o.jstSun = window._cbTest.jstDay(0);",
        "  Date.now = function () { return Date.UTC(2026, 9, 18, 15, 0, 0); }; __o.jstMon = window._cbTest.jstDay(0); __o.jstTue = window._cbTest.jstDay(1);",
        "  __o.dowMon = window._cbTest.dow('2026-10-19'); __o.dowSun = window._cbTest.dow('2026-10-18');",
        "  Date.now = __realNow;",
        "  " + _JS_OUT.replace("\n", "\n  "),
        "})().catch(function (e) { var __s = 'RESULT ' + JSON.stringify({ error: String(e && e.stack || e) });",
        "  if (typeof console !== 'undefined' && console.log) console.log(__s); else if (typeof print === 'function') print(__s); });",
    ])
    out, err = run_js(eng, prog)
    check("ブリーフのコードが JS で動く", out is not None and not (out or {}).get("error"), err or (out or {}).get("error"))
    out = out or {}
    rend = out.get("render", "")
    check("読み込み: date = JST の今日 (10/19)・GET /api/admin/class-brief?date=2026-10-19",
          out.get("url1") == "/api/admin/class-brief?date=2026-10-19" and out.get("date1") == "2026-10-19", (out.get("url1"), out.get("date1")))
    check("📺 の重ねを body の直下へ移す・Esc / ← → のキーを 1 回だけ登録", out.get("movedAtInit") is True and out.get("keyBound") == 1)
    check("クラスごとの見出し (クラス名・在籍・未提出)", L2 in rend and "在籍 4" in rend and "未提出 2名" in rend and L1 in rend and L3 in rend, rend[:300])
    check("名前は escape (<img を出さない)", "&lt;img" in rend and "<img" not in rend)
    check("名前を押すと生徒詳細 (id は数値)", f"window.showStudentDetail({ids['A']})" in rend and f"window.showStudentDetail({ids['B']})" in rend)
    check("〆過ぎ・⛔ 次が止まる・N日・ログイン切れの疑い・15問ミッション の印",
          "〆過ぎ 2" in rend and "⛔ 次が止まる" in rend and "18日" in rend and "29日" in rend and "🔑 ログイン切れの疑い（ログインなし）" in rend
          and "🔑 ログイン切れの疑い（最終 9/10）" in rend and "🧩 15問ミッション" in rend, rend[:200])
    check("今週出した人 (D ✓2・B ✓1)", "✓2" in rend and "✓1" in rend and "👏 今週出した人 2名" in rend)
    check("誤答の多い 3 問: q1 → q5 → q2 の順・正解 ◯・一番多かった誤答 ✗・本文は題名", 0 <= rend.find("q1-c0") < rend.find("q5-c0") < rend.find("q2-c0")
          and "◯ ② q1-c1" in rend and "✗ ③ q1-c2" in rend and "いちばん多かった誤答 2件" in rend and "📖 本文: Fictional Passage Title" in rend, rend[:200])
    check("📺 問題だけ表示のボタンは問題のあるクラスだけ (番号だけを渡す)", f'onclick="cbShareOpen({c2i})"' in rend
          and rend.count("📺 問題だけ表示") == 1)
    check("クラスの選択肢 = その日のクラス (サーバの時間割から)", all(lb in out.get("opts", "") for lb in (L1, L2, L3)) and T2 not in out.get("opts", ""))
    s1 = out.get("share1", "")
    check("📺: 開く・問題文と選択肢・問 1 / 3", out.get("shareDisp1") == "block" and "架空の問題 q1" in s1 and "q1-c3" in s1 and "問 1 / 3" in s1, s1[:300])
    check("📺: 生徒の名前を出さない", not [n for n in names if n in s1 or n.replace("<", "&lt;").replace(">", "&gt;") in s1], names)
    check("📺: 「正解を見せる」まで正解・正解率・一番多かった誤答を出さない", "◯" not in s1 and "正解率" not in s1 and "いちばん多かった" not in s1
          and "正解を見せる" in s1, s1[:300])
    s1r = out.get("share1r", "")
    check("📺: 「正解を見せる」→ ◯ ② と正解・クラスの正解率・一番多かった答え", "◯ ② q1-c1" in s1r and "正解 ②" in s1r and "正解率 0%" in s1r
          and "いちばん多かった答え" in s1r and "正解を見せる" not in s1r, s1r[:300])
    s2 = out.get("share2", "")
    check("📺: → で次の問題 (正解はまた隠す)", "架空の問題 q5" in s2 and "問 2 / 3" in s2 and "◯" not in s2 and "正解を見せる" in s2, s2[:200])
    s3 = out.get("share3", "")
    check("📺: 本文は題名だけ・中身は出さない", "架空の問題 q2" in s3 and "📖 Fictional Passage Title" in s3 and PASSAGE_BODY not in s3, s3[:200])
    check("📺: 最後の問題で → を押しても動かない・← で戻る", out.get("share3b") == s3 and "架空の問題 q5" in out.get("share2b", ""))
    check("📺: 開いている間に読み直しても中身は変わらない (開いた時点の問題を持つ)", "架空の問題 q5" in out.get("shareAfterReload", ""))
    check("📺: Esc で閉じる", out.get("shareDispEsc") == "none" and out.get("shareEsc") == "")
    check("📺: 問題の無いクラス・知らない番号では開かない・✕ で閉じる", out.get("shareNoTop") == "none" and out.get("shareBad") == "none"
          and out.get("shareClosed") == "none", (out.get("shareNoTop"), out.get("shareBad"), out.get("shareClosed")))
    check("その日の曜日に無いクラスの絞り込みは「すべて」に戻す", out.get("urlReset") == "/api/admin/class-brief?date=2026-10-19"
          and out.get("selAfterReset") == "", (out.get("urlReset"), out.get("selAfterReset")))
    check("その日のクラスなら &class= (encodeURIComponent)", out.get("urlClass") == "/api/admin/class-brief?date=2026-10-19&class=" + _enc(L2), out.get("urlClass"))
    check("古いサーバ: 404 / 405 = サーバ反映待ち", "サーバ反映待ち" in out.get("r404", "") and "サーバ反映待ち" in out.get("r405", "")
          and L2 not in out.get("r404", ""), (out.get("r404"), out.get("r405")))
    check("503 = 一時的に応答できません", "一時的に応答できません" in out.get("r503", ""), out.get("r503"))
    check("200 でも version が無い = サーバ反映待ち", "サーバ反映待ち" in out.get("rOld", ""), out.get("rOld"))
    check("500 は番号と理由 (escape)", "読み込めませんでした（500" in out.get("r500", "") and "&lt;b&gt;" in out.get("r500", "") and "<b>x" not in out.get("r500", ""),
          out.get("r500"))
    check("JSON でない応答 (502) でも止まらない", "読み込めませんでした（502）" in out.get("r502", ""), out.get("r502"))
    check("授業の無い日 = この日は時間割の授業がありません", "この日は時間割の授業がありません" in out.get("rSat", ""), out.get("rSat"))
    check("遅れて届いた前の応答 (404) で後の表を上書きしない", T2 in out.get("race", "") and "サーバ反映待ち" not in out.get("race", ""), out.get("race", "")[:200])
    check("JST の今日: 日曜 23:59:59 → 10/18・月曜 0:00 → 10/19・明日 10/20 (端末のタイムゾーンに関係なく)",
          (out.get("jstSun"), out.get("jstMon"), out.get("jstTue")) == ("2026-10-18", "2026-10-19", "2026-10-20"), (out.get("jstSun"), out.get("jstMon"), out.get("jstTue")))
    check("曜日の読み取り (月=1・日=0)", out.get("dowMon") == 1 and out.get("dowSun") == 0)
    wf = open(WORKFLOW, encoding="utf-8").read()
    check("CI (server-tests.yml) に登録", "python3 scripts/health_check/test_class_brief.py" in wf)


def _enc(s):
    from urllib.parse import quote
    return quote(s, safe="-_.!~*'()")


def main():
    print("🗓 今日の授業ブリーフ (読むだけ・管理者だけ・名前は CEO の中だけ) 回帰テスト\n")
    mod = load_main()
    mod._class_brief_now = lambda: NOW
    from fastapi.testclient import TestClient
    client = TestClient(mod.app, raise_server_exceptions=False)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    f, sheet_ready = build_fixtures(mod)
    check("本文の列と表がある (長文の題名を確かめる前提)", mod._grammar_has_passages())
    print(f"  (記号の解答用紙の表: {'あり' if sheet_ready else 'なし'})")
    mon = check_server(mod, client, adm, f, sheet_ready)
    sat = get(client, adm, date="2026-10-24").json()
    check_screens(mon, sat, f)
    print()
    if FAILURES:
        print(f"❌ FAIL: {len(FAILURES)} 件")
        for x in FAILURES:
            print("   - " + x)
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
