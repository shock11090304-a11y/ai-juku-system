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
  [5] 出した人: 前回の授業 (その日より前で一番近い同じ曜日) の開始時刻 (JST) から (1 秒前の提出は入らない・月曜のクラスでも土日の提出が入る)・
      本数 (ドリル + 宿題)・一番よい点 (解答用紙の点も)・満点
  [6] 誤答の多い 3 問: このクラスのクラス自動宿題 + ほかのドリルはこのクラスの 2 人以上に配った分だけ・直近 14 日・数えるのはこのクラスの
      生徒の答えだけ・回答 2 件未満と誤答なしは選ばない・このクラスのクラス自動宿題の問題で先に埋める (ほかのドリルの 0% より先) →
      正解率 → 回答の多い順 → 問題 id・一番選ばれた誤答 (同数なら番号の小さい方)・本文は題名だけ (本文の中身は返さない)・
      習熟度テスト (科目・出典 pt- / ptest:) は出さない
  [9] (木曜・日曜のクラス) 届いていない (未提出 0 本でも直近 14 日に何も届いていない = 出し終えた生徒と分ける・学年が読めない理由)・
      ほかのドリルはクラスの科目だけ (英検のクラスに英文法・どのクラスにも数学を出さない・保留の英語のクラスは英語の 4 科目・国語のクラスは国語)・
      無効化した問題 (active = 0) は 0% でも出さない・前回の授業の開始の求め方
  [7] 読むだけ: 何も書かない (INSERT/UPDATE/DELETE が 1 文も走らない・events も増えない)・ログに名前を出さない・
      生徒の数を 10 倍にしても SELECT の数は同じ (生徒ごとに回さない)・コードに DDL が無い
  [8] 画面: ceo.html の本物のコードを JS エンジンで動かす (CI は node・Mac は osascript / jsc。無ければ FAIL)。ハブの「👨‍🎓 生徒・学習」の
      先頭のボタン・🏫 クラス自動宿題カードのボタン・クラスごとの表 (在籍・未提出・〆過ぎ・N日・ログイン切れの疑い・前回の授業から出した人・
      誤答の多い 3 問)・名前の escape・📺 問題だけ表示 (名前を出さない・「正解を見せる」まで正解・正解率・一番多かった誤答を出さない・
      ← → で移動すると正解はまた隠す・Esc で閉じる)・古いサーバ (404 / 405 / version なし = 反映待ち・503 = 一時的)・遅れて届いた前の応答で
      上書きしない・その曜日に無いクラスの絞り込みは「すべて」に戻す・JST の今日 (端末のタイムゾーンに関係なく)・
      📺 はダイアログ (開くとフォーカスを中へ・Tab は中だけ・外へ向いた Enter / Space は止める・ショートカットへ流さない・閉じたら元へ)・
      ハブと 🏫 カードのボタンは前に選んだ日ではなく JST の今日 (🔄 は選んだ日のまま)・🎉 は全員が届いた分を出したときだけ
      (届いていない生徒がいれば 📭・届いた本数を返さないサーバでも 🎉 にしない)・出した人の境目の表示

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
    # 出した人の境目 = 前回の月曜2限の開始 10/12 20:25 JST (= 11:25:00 UTC)。ちょうどは入る・1 秒前は入らない (どちらも配ったのは 14 日より前)
    f.drill("D14", "admin", ["q13"], title="塾長の前のドリル", created_at="2026-10-01 01:00:00")
    f.assign("D14", "E", assigned_at="2026-10-01 01:00:00", status="completed", completed_at="2026-10-12 11:25:00")
    f.drill("D15", "admin", ["q13"], title="塾長の前のドリル 2", created_at="2026-10-01 01:00:00")
    f.assign("D15", "A", assigned_at="2026-10-01 01:00:00", status="completed", completed_at="2026-10-12 11:24:59")
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
    check("曜日の違うクラスを指定しても出す (meets_on_date: false)・出した人は前回の火曜2限 (10/13 20:25) から",
          [c["label"] for c in d.get("classes", [])] == [T2] and d["classes"][0]["meets_on_date"] is False
          and [m["id"] for m in d["classes"][0]["members"]] == [ids["K"]] and d["classes"][0].get("praise_since_jst") == "10/13 20:25",
          d.get("classes"))
    d = get(client, adm, date="2026-10-20").json()
    check("明日 (10/20 火) は火曜のクラス", d.get("dow") == 2 and T2 in by_label(d), [c["label"] for c in d.get("classes", [])])
    check("timetable = 15 クラス (CEO のクラスの選択肢)", len(d.get("timetable") or []) == 15 and all({"label", "dow", "time"} <= set(t) for t in d["timetable"]))

    print("\n[3] 名簿")
    mon = get(client, adm, date="2026-10-19").json()
    check("version: 1 (CEO の「サーバ反映待ち」の判定)", mon.get("version") == 1 and mon.get("ok") is True)
    cl = by_label(mon)
    c2 = cl.get(L2) or {}
    check("today・as_of・出した人の境目 = 前回の月曜2限の開始 (10/12 20:25 JST = 11:25 UTC)・月曜1限は 19:15",
          mon.get("today") == "2026-10-19" and mon.get("as_of") == "2026-10-19" and "week_start" not in mon
          and c2.get("praise_since") == "2026-10-12T11:25:00+00:00" and c2.get("praise_since_jst") == "10/12 20:25"
          and (cl.get(L1) or {}).get("praise_since_jst") == "10/12 19:15",
          (mon.get("today"), mon.get("as_of"), c2.get("praise_since"), c2.get("praise_since_jst")))
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
    check("届いた本数 (直近 14 日に配った分・提出済みも・今日の1問 / 初回診断 / 14 日より前は数えない): A 3・B 4・D 5・E 2",
          (a.get("received_n"), b.get("received_n"), dd.get("received_n"), e.get("received_n")) == (3, 4, 5, 2),
          (a.get("received_n"), b.get("received_n"), dd.get("received_n"), e.get("received_n")))
    check("未提出 0 本の D・E は「届いた分は全部出した」(届いていないではない)・月曜2限 all_done_n 2・not_delivered_n 0",
          dd.get("not_delivered") is False and e.get("not_delivered") is False and c2.get("all_done_n") == 2 and c2.get("not_delivered_n") == 0
          and a.get("delivery_note") == "" and cc.get("delivery_note") == "", (c2.get("all_done_n"), c2.get("not_delivered_n")))

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

    print("\n[5] 出した人 (前回の授業の開始 = 10/12 20:25 JST から)")
    pr = c2.get("submitted_this_week") or []
    check("出した人 = D (5 本) → E (3 本・日曜 23:59:59 の提出と境目ちょうどの提出も入る) → B (3 本・名前の順)・境目の 1 秒前に出しただけの A は入らない",
          [p["id"] for p in pr] == [ids["D"], ids["E"], ids["B"]], [(p.get("id"), p.get("count")) for p in pr])
    p_d = pr[0] if pr else {}
    check("D: ドリル 4 (水曜の 3 本 + 月曜 0:00:00 の 1 本) + 宿題 1", p_d.get("count") == 5 and p_d.get("drills") == 4 and p_d.get("homework") == 1, p_d)
    p_e = pr[1] if len(pr) > 1 else {}
    check("E: ドリル 2 (日曜 23:59:59・10/12 20:25:00 ちょうど) + 宿題 1・一番よい点 2/4", p_e.get("count") == 3 and p_e.get("drills") == 2
          and p_e.get("homework") == 1 and p_e.get("best") == {"correct": 2, "total": 4, "pct": 50}, p_e)
    if sheet_ready:
        check("一番よい点は解答用紙の 5/5・満点", p_d.get("best") == {"correct": 5, "total": 5, "pct": 100} and p_d.get("perfect") is True, p_d)
    else:
        check("一番よい点はドリルの 2/5", p_d.get("best") == {"correct": 2, "total": 5, "pct": 40}, p_d)
    p_b = pr[2] if len(pr) > 2 else {}
    check("B: ドリル 2 (0/2・0/1) + 点の無い宿題 1 → 一番よい点 0/2・名前つき", p_b.get("best") == {"correct": 0, "total": 2, "pct": 0}
          and p_b.get("count") == 3 and p_b.get("name") == mem[ids["B"]]["name"], p_b)
    check("前回の授業の開始: 月曜のクラスを月曜に開く = 7 日前・水曜に開く = 2 日前・日曜に開く = 6 日前・時刻が読めなければ 0:00",
          mod._class_brief_prev_meeting({"dow": 1, "time": "20:25–21:25"}, datetime.date(2026, 10, 19)) == datetime.datetime(2026, 10, 12, 20, 25)
          and mod._class_brief_prev_meeting({"dow": 1, "time": "20:25–21:25"}, datetime.date(2026, 10, 21)) == datetime.datetime(2026, 10, 19, 20, 25)
          and mod._class_brief_prev_meeting({"dow": 1, "time": "20:25–21:25"}, datetime.date(2026, 10, 18)) == datetime.datetime(2026, 10, 12, 20, 25)
          and mod._class_brief_prev_meeting({"dow": 0, "time": "21:15–22:15"}, datetime.date(2026, 10, 18)) == datetime.datetime(2026, 10, 11, 21, 15)
          and mod._class_brief_prev_meeting({"dow": 5, "time": ""}, datetime.date(2026, 10, 19)) == datetime.datetime(2026, 10, 16, 0, 0))

    print("\n[6] 誤答の多い 3 問")
    top = c2.get("top_missed") or []
    qid = {v: k for k, v in ids.items() if k.startswith("q")}
    check("3 問 = このクラスのクラス自動宿題で埋める: q1 (0%) → q2 (50%) → q4 (50%・同じなら id の小さい方)。ほかのドリルの q5 (0%) は 4 番目で出ない",
          [qid.get(t["question_id"]) for t in top] == ["q1", "q2", "q4"] and all(t.get("from_class_hw") is True for t in top),
          [(qid.get(t["question_id"]), t.get("from_class_hw")) for t in top])
    check("月曜2限 (英文法) のほかのドリルに数える科目 = english・chugaku", c2.get("top_missed_subjects") == ["chugaku", "english"], c2.get("top_missed_subjects"))
    t1 = top[0] if top else {}
    check("q1: 正解率 0 (0/2)・一番選ばれた誤答は ③ (2 件)・選択肢の数・このクラスのクラス自動宿題",
          t1.get("accuracy") == 0 and t1.get("accuracy_pct") == 0 and t1.get("n") == 2 and t1.get("correct_n") == 0
          and t1.get("wrong_top") == {"index": 2, "count": 2} and t1.get("choice_counts") == [0, 0, 2, 0] and t1.get("from_class_hw") is True
          and t1.get("answer") == 1 and t1.get("choices") == ["q1-c0", "q1-c1", "q1-c2", "q1-c3"], t1)
    t2 = top[1] if len(top) > 1 else {}
    check("q2: 本文は題名だけ・50% (1/2)", t2.get("passage_title") == "Fictional Passage Title" and t2.get("accuracy_pct") == 50 and t2.get("n") == 2, t2)
    t3 = top[2] if len(top) > 2 else {}
    check("q4: 50%・誤答は ② (1 件)", t3.get("accuracy_pct") == 50 and t3.get("wrong_top") == {"index": 1, "count": 1} and t3.get("passage_title") is None, t3)
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


TH1 = "木曜1限 英検準1級対策"
TH2 = "木曜2限 早慶クラス"
SUN = "日曜 高校国語"


def check_delivery_and_subjects(mod, client, adm, f):
    print("\n[9] 届いていない・クラスの科目・クラス自動宿題を先に・無効化した問題 (木曜・日曜のクラス)")
    f.student("P", "架空 木一", labels=[TH1, TH2, SUN], grade="高2", last_login="2026-10-18 01:00:00")
    f.student("Q", "架空 木二", labels=[TH1, TH2, SUN], grade="高3", last_login="2026-10-18 01:00:00")
    f.student("R", "架空 学年不明", labels=[TH2], grade="", last_login="2026-10-18 01:00:00")
    f.student("S", "架空 出し終え", labels=[TH2], grade="高1", last_login="2026-10-18 01:00:00")
    f.question("e1", 1, subject="eiken", source="eikenp1-v1")
    f.question("e2", 0, subject="eiken", source="eikenp1-v1")
    f.question("e3", 0, subject="eiken", source="eikenp1-v1")
    f.question("en1", 0)
    f.question("m1", 0, subject="math", source="mathct-v1")
    f.question("j1", 0, subject="japanese", source="manual-kokugo-v1")
    f.question("s1", 0)
    at, done_at = "2026-10-16 21:00:00", "2026-10-17 10:00:00"

    def pair(dkey, created_by, qkey, subject, ans_p, ans_q):   # P と Q の 2 人に配って 2 人とも提出 (= ほかのドリルの条件 2 人以上)
        f.drill(dkey, created_by, [qkey], title=f"架空 {dkey}", subject=subject, created_at=at)
        f.assign(dkey, "P", assigned_at=at, status="completed", completed_at=done_at, answers={qkey: ans_p})
        f.assign(dkey, "Q", assigned_at=at, status="completed", completed_at=done_at, answers={qkey: ans_q})

    f.drill("DT1", f"class_hw_auto:kosei:{TH1}", ["e1", "e3"], title=f"【{TH1}】宿題（2問・〆10/18）", subject="eiken", created_at=at)
    f.assign("DT1", "P", assigned_at=at, status="completed", completed_at=done_at, answers={"e1": 1, "e3": 1})
    f.assign("DT1", "Q", assigned_at=at, status="completed", completed_at=done_at, answers={"e1": 0, "e3": 1})
    pair("DT2", "admin", "e2", "eiken", 2, 3)       # 英検 0%・誤答は 1 件ずつ (③ と ④ → 番号の小さい方)
    pair("DT3", "admin", "en1", "english", 1, 1)    # 英文法 0%
    pair("DT4", "admin", "m1", "math", 1, 2)        # 数学 0% = どのクラスにも出さない
    pair("DT5", "admin", "j1", "japanese", 1, 1)    # 国語 0% = 国語のクラスだけ
    f.drill("DT6", "admin", ["s1"], title="架空 DT6", created_at=at)
    f.assign("DT6", "S", assigned_at=at, status="completed", completed_at=done_at, answers={"s1": 0})
    qid = {f.ids[k]: k for k in ("e1", "e2", "e3", "en1", "m1", "j1", "s1")}

    def tops(d, lb):
        return [qid.get(t["question_id"], t["question_id"]) for t in (by_label(d).get(lb) or {}).get("top_missed", [])]

    d = get(client, adm, date="2026-10-22").json()
    check("英検のクラス: このクラスのクラス自動宿題の e3 (0%) → e1 (50%) → ほかのドリルの英検 e2 (0%)。英文法・数学は数えない",
          tops(d, TH1) == ["e3", "e1", "e2"], tops(d, TH1))
    ex(mod, "UPDATE grammar_questions SET active = 0 WHERE id = ?", (f.ids["e3"],))   # 正解の誤りなどで無効にした
    d = get(client, adm, date="2026-10-22").json()
    c1, c2 = by_label(d).get(TH1) or {}, by_label(d).get(TH2) or {}
    dump = json.dumps(d, ensure_ascii=False)
    check("無効化した問題 (active = 0) は 0% でも出さない・応答のどこにも無い (前の答えが残っていても)",
          tops(d, TH1) == ["e1", "e2"] and "架空の問題 e3 " not in dump, tops(d, TH1))
    check("英検のクラスのほかのドリルに数える科目 = eiken だけ", c1.get("top_missed_subjects") == ["eiken"], c1.get("top_missed_subjects"))
    e2t = next((t for t in c1.get("top_missed", []) if t["question_id"] == f.ids["e2"]), {})
    check("ほかのドリルの問題: from_class_hw false・誤答が 1 件ずつなら番号の小さい方 (③)",
          e2t.get("from_class_hw") is False and e2t.get("wrong_top") == {"index": 2, "count": 1}, e2t)
    check("保留の英語のクラス (早慶): 英語の 4 科目 (英検・英文法) は数え、数学・国語は数えない・同じ 0% なら問題 id の順",
          tops(d, TH2) == ["e2", "en1", "e1"] and c2.get("routine_kind") == "hold"
          and c2.get("top_missed_subjects") == ["chugaku", "eiken", "english", "english_long"], (tops(d, TH2), c2.get("top_missed_subjects")))
    check("どのクラスにも数学の m1 を出さない", all("m1" not in tops(d, lb) for lb in (TH1, TH2)))
    sm = {m["id"]: m for m in c2.get("members", [])}
    r_, s_, p_ = sm.get(f.ids["R"], {}), sm.get(f.ids["S"], {}), sm.get(f.ids["P"], {})
    check("早慶: 在籍 4・未提出 0・届いた分は全部出した 3 (P・Q・S)・届いていない 1 (R)",
          (c2.get("members_n"), c2.get("open_members_n"), c2.get("all_done_n"), c2.get("not_delivered_n")) == (4, 0, 3, 1),
          (c2.get("members_n"), c2.get("open_members_n"), c2.get("all_done_n"), c2.get("not_delivered_n")))
    check("R: 未提出 0 本・届いた 0 本 = 届いていない・理由 = 学年が読めない", r_.get("open_count") == 0 and r_.get("received_n") == 0
          and r_.get("not_delivered") is True and r_.get("delivery_note") == "grade_unknown" and r_.get("band") == "", r_)
    check("S: 未提出 0 本・届いた 1 本 = 届いていないではない / P: 届いた 5 本", s_.get("not_delivered") is False and s_.get("received_n") == 1
          and p_.get("received_n") == 5 and p_.get("not_delivered") is False, (s_, p_.get("received_n")))
    check("木曜のクラスの出した人: 前回の木曜 (10/15) の授業の開始から・P・Q (5 本ずつ)",
          c1.get("praise_since_jst") == "10/15 19:15" and c2.get("praise_since_jst") == "10/15 20:25"
          and sorted(p["id"] for p in c1.get("submitted_this_week", [])) == sorted([f.ids["P"], f.ids["Q"]])
          and all(p["count"] == 5 for p in c1.get("submitted_this_week", [])), [(p["id"], p["count"]) for p in c1.get("submitted_this_week", [])])
    ds = get(client, adm, date="2026-10-22", **{"class": SUN}).json()
    cs = by_label(ds).get(SUN) or {}
    check("国語のクラス: 国語の j1 だけ (英検・英文法・数学は出さない)", tops(ds, SUN) == ["j1"]
          and cs.get("top_missed_subjects") == ["chugaku_kokugo", "japanese"] and cs.get("routine_kind") == "none", (tops(ds, SUN), cs.get("top_missed_subjects")))
    return d


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
    def _m(i, name, received=None, note="", band="kosei"):
        m = {"id": 9000 + i, "name": name, "ai_path": "ai_nashi", "ai_label": "AIなし", "band": band, "open_count": 0, "open_items": [],
             "overdue_count": 0, "blocking_count": 0, "oldest_days": None, "login_stale": False, "delivery_note": note}
        if received is not None:
            m["received_n"] = received
        return m
    syn = {"ok": True, "version": 1, "date": "2026-10-22", "dow": 4, "dow_ja": "木", "today": "2026-10-19", "timetable": mon["timetable"], "classes": [
        {"label": TH1, "time": "19:15–20:15", "routine_kind": "eiken", "members_n": 2, "open_members_n": 0, "praise_since_jst": "10/15 19:15",
         "members": [_m(1, "架空 全出し一", 2), _m(2, "架空 全出し二", 1)], "submitted_this_week": [], "top_missed": []},
        {"label": TH2, "time": "20:25–21:25", "routine_kind": "hold", "members_n": 2, "open_members_n": 0, "praise_since_jst": "10/15 20:25",
         "members": [_m(3, "架空 届かず<b>", 0, "grade_unknown", ""), _m(4, "架空 出し終え", 1)], "submitted_this_week": [], "top_missed": []},
        {"label": "金曜1限 高2 英文法", "time": "19:15–20:15", "routine_kind": "grammar", "members_n": 2, "open_members_n": 0,
         "members": [_m(5, "架空 旧一"), _m(6, "架空 旧二")], "submitted_this_week": [], "top_missed": []},   # 届いた本数を返さないサーバ
    ]}
    tue = {"ok": True, "version": 1, "date": "2026-10-20", "dow": 2, "dow_ja": "火", "today": "2026-10-19", "timetable": mon["timetable"],
           "classes": [{"label": T2, "time": "20:25–21:25", "members": [], "members_n": 0, "open_members_n": 0, "submitted_this_week": [], "top_missed": []}]}
    prog = "\n".join([
        "var window = (typeof globalThis !== 'undefined') ? globalThis : this;",
        "var __o = { urls: [], moved: false };",
        "var __els = {};",
        "function __el(id) { if (!__els[id]) __els[id] = { id: id, innerHTML: '', value: '', style: {}, parentNode: null,",
        "  focus: function () { document.activeElement = this; } }; return __els[id]; }",
        "var __keys = [], __ls = [], __hubFns = [];",
        "var __hub = { addEventListener: function (t, fn) { if (t === 'click') __hubFns.push(fn); } };",
        # 📺 の中のボタン (id が cbShare…Btn) は、重ねの中身にその id があるときだけ見つかる (本物の DOM と同じ)
        "function __shareBtn(id) { return /^cbShare.+Btn$/.test(id); }",
        "var document = { readyState: 'complete', activeElement: null, documentElement: { style: { overflow: '' } },",
        "  body: { appendChild: function (e) { e.parentNode = document.body; __o.moved = true; } },",
        "  getElementById: function (id) { if (__shareBtn(id)) return __el('cbShare').innerHTML.indexOf('id=\"' + id + '\"') >= 0 ? __el(id) : null; return __el(id); },",
        "  querySelector: function (sel) { return String(sel).indexOf('classBriefSection') >= 0 ? __hub : null; },",
        "  addEventListener: function (t, fn, cap) { __ls.push({ t: t, cap: !!cap }); if (t === 'keydown') __keys.push(fn); } };",
        "__el('cbShare').contains = function (t) { return !!t && (t === this || (typeof t.id === 'string' && __shareBtn(t.id) && this.innerHTML.indexOf('id=\"' + t.id + '\"') >= 0)); };",
        "function __key(k, opt) { opt = opt || {}; var ev = { key: k, shiftKey: !!opt.shiftKey, target: opt.target || document.activeElement, prevented: false, stopped: false,",
        "  preventDefault: function () { this.prevented = true; }, stopPropagation: function () { this.stopped = true; }, stopImmediatePropagation: function () { this.stopped = true; } };",
        "  for (var i = 0; i < __keys.length; i++) __keys[i](ev); return ev; }",
        # 本物のボタンと同じ: 止められなかった Space / Enter はフォーカスのあるボタンを押す (✕ なら閉じる)
        "function __press(k) { var ev = __key(k); var t = ev.target;",
        "  if (!ev.prevented && (k === ' ' || k === 'Enter') && t && typeof t.id === 'string' && __el('cbShare').contains(t)) {",
        "    if (t.id === 'cbShareCloseBtn') window.cbShareClose(); else if (t.id === 'cbShareRevealBtn') window.cbShareReveal();",
        "    else if (t.id === 'cbShareNextBtn') window.cbShareNav(1); else if (t.id === 'cbSharePrevBtn') window.cbShareNav(-1); }",
        "  return ev; }",
        "function __open() { return [__el('cbShare').style.display, !!window._cbTest.state()]; }",
        "var __queue = [];",
        "function __res(status, body) { return { ok: status >= 200 && status < 300, status: status,",
        "  json: function () { return body === undefined ? Promise.reject(new Error('no json')) : Promise.resolve(body); } }; }",
        "window.AdminAuth = { fetch: function (path) { __o.urls.push(path); var r = __queue.shift(); return (r && typeof r.then === 'function') ? r : Promise.resolve(r); } };",
        f"var MON = {json.dumps(mon, ensure_ascii=False)};",
        f"var SAT = {json.dumps(sat, ensure_ascii=False)};",
        f"var TUE = {json.dumps(tue, ensure_ascii=False)};",
        f"var SYN = {json.dumps(syn, ensure_ascii=False)};",
        "function __one(i) { var d = JSON.parse(JSON.stringify(SYN)); d.classes = [SYN.classes[i]]; return window._cbTest.render(d); }",
        "var __realNow = Date.now;",
        "Date.now = function () { return Date.UTC(2026, 9, 19, 1, 0, 0); };",
        blk,
        "(async function () {",
        "  __o.keyBound = __keys.length; __o.movedAtInit = __o.moved;",
        "  __o.keyCap = __ls.filter(function (l) { return l.t === 'keydown'; }).map(function (l) { return l.cap; });",
        "  __o.focusInCap = __ls.filter(function (l) { return l.t === 'focusin'; }).map(function (l) { return l.cap; }); __o.hubBound = __hubFns.length;",
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
        # 📺 はダイアログ: 下に隠れた 📺 (cbUnder) にフォーカスがある状態で開く
        "  var under = __el('cbUnder'); under.focus();",
        f"  window.cbShareOpen({c2i}); __o.f1 = document.activeElement && document.activeElement.id; __o.ovf = document.documentElement.style.overflow;",
        "  var ev = __key('Tab'); __o.f2 = document.activeElement.id; __o.tabPrev = ev.prevented;",
        "  __key('Tab'); __o.f3 = document.activeElement.id;",
        "  __key('Tab', { shiftKey: true }); __o.f4 = document.activeElement.id;",
        "  ev = __key(' ', { target: under }); __o.spOut = [ev.prevented, ev.stopped, window._cbTest.state().qi, document.activeElement.id];",
        "  ev = __key('Enter', { target: under }); __o.enOut = [ev.prevented, ev.stopped, window._cbTest.state().qi];",
        "  ev = __key('Enter'); __o.enIn = [ev.prevented, ev.stopped];",
        "  ev = __key('r'); __o.rKey = [ev.prevented, ev.stopped];",
        "  under.focus(); window._cbTest.focusIn({ target: under }); __o.fFocusIn = document.activeElement.id;",
        "  window.cbShareReveal(); __o.f5 = document.activeElement.id;",
        "  __key('ArrowRight'); __o.f6 = document.activeElement.id;",
        "  __key('ArrowRight'); window.cbShareReveal(); __o.f7 = document.activeElement.id; __o.lastHint = __el('cbShare').innerHTML;",
        # 最後の問題で見せた後の Space / Enter (癖・二度押し・Enter の押しっぱなし) で閉じない (閉じると下の名前が Zoom に映る)
        "  ev = __press(' '); __o.lastSp = [ev.prevented].concat(__open(), [document.activeElement.id]);",
        "  __press('Enter'); __press('Enter'); ev = __press('Enter'); __o.lastEn = [ev.prevented].concat(__open(), [document.activeElement.id]);",
        "  __o.lastTab = __key('Tab').prevented && document.activeElement.id;",
        "  __key('Escape'); __o.f8 = document.activeElement && document.activeElement.id; __o.ovf2 = document.documentElement.style.overflow;",
        "  ev = __key('r'); __o.rAfter = [ev.prevented, ev.stopped];",
        # Space だけで最後まで進めても閉じない (3 問: 見せる → 次 → … を 12 回)
        f"  under.focus(); window.cbShareOpen({c2i}); for (var sp = 0; sp < 12; sp++) __press(' ');",
        "  __o.spWalk = __open().concat([window._cbTest.state() && window._cbTest.state().qi, window._cbTest.state() && window._cbTest.state().reveal, document.activeElement.id]);",
        "  __key('Escape'); __o.spWalkEsc = __open();",
        # 問題が 1 問だけのクラス: 開く → Space (見せる) → Space でも閉じない
        f"  var M1 = JSON.parse(JSON.stringify(MON)); M1.classes[{c2i}].top_missed = M1.classes[{c2i}].top_missed.slice(0, 1);",
        "  __queue.push(__res(200, M1)); await cbLoad();",
        f"  under.focus(); window.cbShareOpen({c2i}); __o.one1 = document.activeElement.id;",
        "  __press(' '); __o.one2 = __open().concat([document.activeElement.id]); __o.oneHint = __el('cbShare').innerHTML;",
        "  __press(' '); __press('Enter'); __o.one3 = __open().concat([document.activeElement.id]);",
        "  __press('Escape'); __o.oneEsc = __open().concat([document.activeElement && document.activeElement.id]);",
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
        # ハブと 🏫 カードのボタンは前に選んだ日 (明日) ではなく JST の今日・🔄 (cbLoad) は選んだ日のまま
        "  window.ceoHubShow = function (id) { __o.hubShown = id; };",
        "  __el('cbDate').value = '2026-10-20'; __queue.push(__res(200, MON)); await __hubFns[0](); __o.urlHub = __o.urls[__o.urls.length - 1];",
        "  __el('cbDate').value = '2026-10-20'; __queue.push(__res(200, MON)); await window.cbOpenFromCard(); __o.urlCard = __o.urls[__o.urls.length - 1];",
        "  __el('cbDate').value = '2026-10-20'; __queue.push(__res(200, TUE)); await cbLoad(); __o.urlKeep = __o.urls[__o.urls.length - 1];",
        "  __o.synAll = __one(0); __o.synNd = __one(1); __o.synOld = __one(2);",
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
    check("📺 の重ねを body の直下へ移す・キーは document の capture で 1 回だけ登録 (画面のほかのキー操作より先)・focusin も capture・ハブのボタン 1 つ",
          out.get("movedAtInit") is True and out.get("keyBound") == 1 and out.get("keyCap") == [True] and out.get("focusInCap") == [True]
          and out.get("hubBound") == 1, (out.get("keyBound"), out.get("keyCap"), out.get("focusInCap"), out.get("hubBound")))
    check("クラスごとの見出し (クラス名・在籍・未提出)", L2 in rend and "在籍 4" in rend and "未提出 2名" in rend and L1 in rend and L3 in rend, rend[:300])
    check("名前は escape (<img を出さない)", "&lt;img" in rend and "<img" not in rend)
    check("名前を押すと生徒詳細 (id は数値)", f"window.showStudentDetail({ids['A']})" in rend and f"window.showStudentDetail({ids['B']})" in rend)
    check("〆過ぎ・⛔ 次が止まる・N日・ログイン切れの疑い・15問ミッション の印",
          "〆過ぎ 2" in rend and "⛔ 次が止まる" in rend and "18日" in rend and "29日" in rend and "🔑 ログイン切れの疑い（ログインなし）" in rend
          and "🔑 ログイン切れの疑い（最終 9/10）" in rend and "🧩 15問ミッション" in rend, rend[:200])
    check("出した人 (D ✓5・E ✓3・B ✓3)・前回の授業からの境目を出す", "✓5" in rend and "✓3" in rend and "👏 前回の授業から出した人 3名" in rend
          and "（10/12 20:25 から）" in rend and "今週" not in rend, rend[max(0, rend.find("👏") - 10):rend.find("👏") + 300])
    check("誤答の多い 3 問: q1 → q2 → q4 の順・正解 ◯・一番多かった誤答 ✗・本文は題名・このクラスの宿題の印", 0 <= rend.find("q1-c0") < rend.find("q2-c0") < rend.find("q4-c0")
          and "q5-c0" not in rend and "◯ ② q1-c1" in rend and "✗ ③ q1-c2" in rend and "いちばん多かった誤答 2件" in rend
          and "📖 本文: Fictional Passage Title" in rend and "🏫 このクラスの宿題" in rend, rend[:200])
    check("未提出のいるクラス・在籍のいないクラスでは 🎉 を出さない", "🎉" not in rend)
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
    check("📺: → で次の問題 (正解はまた隠す)", "架空の問題 q2" in s2 and "問 2 / 3" in s2 and "◯" not in s2 and "正解を見せる" in s2, s2[:200])
    check("📺: 本文は題名だけ・中身は出さない", "📖 Fictional Passage Title" in s2 and PASSAGE_BODY not in s2, s2[:200])
    s3 = out.get("share3", "")
    check("📺: 3 問目", "架空の問題 q4" in s3 and "問 3 / 3" in s3 and "📖" not in s3, s3[:200])
    check("📺: 最後の問題で → を押しても動かない・← で戻る", out.get("share3b") == s3 and "架空の問題 q2" in out.get("share2b", ""))
    check("📺: 開いている間に読み直しても中身は変わらない (開いた時点の問題を持つ)", "架空の問題 q2" in out.get("shareAfterReload", ""))
    check("📺: Esc で閉じる", out.get("shareDispEsc") == "none" and out.get("shareEsc") == "")
    check("📺: 問題の無いクラス・知らない番号では開かない・✕ で閉じる", out.get("shareNoTop") == "none" and out.get("shareBad") == "none"
          and out.get("shareClosed") == "none", (out.get("shareNoTop"), out.get("shareBad"), out.get("shareClosed")))
    check("📺 はダイアログ: 開くと下の 📺 からフォーカスを「正解を見せる」へ移す・背後のページを動かさない",
          out.get("f1") == "cbShareRevealBtn" and out.get("ovf") == "hidden", (out.get("f1"), out.get("ovf")))
    check("📺: Tab は重ねの中だけを回る (正解を見せる → 次 → ✕ → Shift+Tab で 次)",
          (out.get("f2"), out.get("f3"), out.get("f4"), out.get("tabPrev")) == ("cbShareNextBtn", "cbShareCloseBtn", "cbShareNextBtn", True),
          (out.get("f2"), out.get("f3"), out.get("f4"), out.get("tabPrev")))
    check("📺: 重ねの外 (下の 📺) に向いた Space / Enter は止める (問 1 に戻らない・フォーカスは中へ)",
          out.get("spOut") == [True, True, 0, "cbShareRevealBtn"] and out.get("enOut") == [True, True, 0], (out.get("spOut"), out.get("enOut")))
    check("📺: 中のボタンの Enter は止めない (押せる)・どのキーも画面のショートカットへ流さない (R で読み直さない)",
          out.get("enIn") == [False, True] and out.get("rKey") == [False, True], (out.get("enIn"), out.get("rKey")))
    check("📺: 重ねの外へフォーカスが移ったら中へ戻す", out.get("fFocusIn") == "cbShareRevealBtn", out.get("fFocusIn"))
    check("📺: 正解を見せたら 次 → へ・次の問題では 正解を見せる へ・最後の問題で見せたら ✕ ではなく重ねそのもの (#cbShare) へ",
          (out.get("f5"), out.get("f6"), out.get("f7")) == ("cbShareNextBtn", "cbShareRevealBtn", "cbShare"), (out.get("f5"), out.get("f6"), out.get("f7")))
    check("📺: 最後の問題で見せた後の Space / Enter (二度押し・押しっぱなし) では閉じない (下の名前を Zoom に出さない)",
          out.get("lastSp") == [True, "block", True, "cbShare"] and out.get("lastEn") == [True, "block", True, "cbShare"],
          (out.get("lastSp"), out.get("lastEn")))
    lh = out.get("lastHint", "")
    check("📺: 最後の問題で見せた後の案内 = 閉じるのは Esc か ✕ (Space / Enter で押す と書かない)",
          "最後の問題です · ← で戻る · 閉じるのは Esc か ✕" in lh and "Space / Enter で押す" not in lh, lh[-300:])
    check("📺: 重ねそのものから Tab を押すと中のボタンへ (✕ は自分で選んだときだけ)", out.get("lastTab") == "cbShareCloseBtn", out.get("lastTab"))
    check("📺: Space だけで最後の問題まで進めても閉じない (問 3 / 3・正解を見せたまま・フォーカスは重ね)・Esc で閉じる",
          out.get("spWalk") == ["block", True, 2, True, "cbShare"] and out.get("spWalkEsc") == ["none", False], (out.get("spWalk"), out.get("spWalkEsc")))
    oh = out.get("oneHint", "")
    check("📺: 1 問だけのクラス: 開く → Space (見せる) → Space / Enter でも閉じない・← で戻る は出さない・Esc で閉じて 📺 へ戻る",
          out.get("one1") == "cbShareRevealBtn" and out.get("one2") == ["block", True, "cbShare"] and out.get("one3") == ["block", True, "cbShare"]
          and "問 1 / 1" in oh and "◯" in oh and "最後の問題です · 閉じるのは Esc か ✕" in oh and "← で戻る" not in oh
          and out.get("oneEsc") == ["none", False, "cbUnder"], (out.get("one1"), out.get("one2"), out.get("one3"), out.get("oneEsc")))
    check("📺: Esc で閉じたら開く前の場所 (📺) へフォーカスを戻す・スクロールを戻す・閉じた後のキーは止めない",
          out.get("f8") == "cbUnder" and out.get("ovf2") == "" and out.get("rAfter") == [False, False], (out.get("f8"), out.get("ovf2"), out.get("rAfter")))
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
    check("ハブの「今日の授業」: 前に 明日 (10/20) を選んでいても JST の今日 (10/19) を読む",
          out.get("urlHub") == "/api/admin/class-brief?date=2026-10-19", out.get("urlHub"))
    check("🏫 カードの「今日の授業ブリーフ」: ブリーフの画面を開いて JST の今日 (10/19) を読む",
          out.get("urlCard") == "/api/admin/class-brief?date=2026-10-19" and out.get("hubShown") == "classBriefSection", (out.get("urlCard"), out.get("hubShown")))
    check("🔄 (cbLoad) は選んだ日 (10/20) のまま", out.get("urlKeep") == "/api/admin/class-brief?date=2026-10-20", out.get("urlKeep"))
    green0 = '#86efac55;margin:0.1rem 0.25rem 0.1rem 0;white-space:nowrap;">未提出 0名'
    sa, sn, so = out.get("synAll", ""), out.get("synNd", ""), out.get("synOld", "")
    check("全員が届いた分を出した = 🎉 と緑の「未提出 0名」", "全員、届いた分を出しています 🎉" in sa and green0 in sa and "📭" not in sa, sa[:300])
    check("前回の授業からまだいない = 境目つきで出す", "前回の授業（10/15 19:15）からまだいません" in sa and "（10/15 19:15 から）" in sa, sa[:300])
    check("何も届いていない生徒がいる = 🎉 も緑も出さず「📭 届いていない」に名前 (escape・押すと生徒詳細)・学年が読めない・保留のクラス",
          "🎉" not in sn and green0 not in sn and "📭 届いていない 1名" in sn and "架空 届かず&lt;b&gt;" in sn and "<b>架空" not in sn
          and "window.showStudentDetail(9003)" in sn and "学年が読めない" in sn and "保留中" in sn and "届いた分は全部出した 1名" in sn
          and "未提出はありません" in sn, sn[:400])
    check("届いた本数を返さないサーバ = 🎉 にしない (未提出なし N名)", "🎉" not in so and green0 not in so and "未提出なし 2名" in so and "📭" not in so, so[:300])
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
    check_delivery_and_subjects(mod, client, adm, f)
    print()
    if FAILURES:
        print(f"❌ FAIL: {len(FAILURES)} 件")
        for x in FAILURES:
            print("   - " + x)
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
