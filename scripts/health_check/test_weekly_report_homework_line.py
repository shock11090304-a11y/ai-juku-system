#!/usr/bin/env python3
"""📝 週次レポートの「今週の宿題」の 1 行 (2026-10-18 塾長「③の週次レポートの1行も作っておいて」) の回帰テスト。

日曜 19:00 の週次レポート (保護者 / 生徒のメール・LINE・「今週は 0 問」メール) に生徒ごとに 1 行:
  「📝 今週の宿題: 届いた N 本／提出 M 本／〆を過ぎた未提出 K 本（単元を 3 つまで）」+ 宿題を開くリンク。
演習の記録が無い・休眠の生徒でも、未提出の宿題があれば「今週は 0 問」メールを送る (WEEKLY_REPORT_HOMEWORK_ZERO_WEEK・既定 1)。

固定する性質 (一時 SQLite・外へは出さない (偽の urlopen が宛先を全部記録・知らない宛先は落とす)・生徒名とメールは架空 = 公開リポジトリ):
  [1] 数える種類: クラス自動宿題・3日ドリル・塾長のドリル・15問ミッション・塾長の宿題 (記号の解答用紙の宿題も) を数え、今日の1問・初回診断は数えない
  [2] 週の境目 (JST): 月曜 0:00 JST (= 日曜 15:00 UTC) ちょうどは入る・1 秒前は入らない・終わり (次の月曜 0:00) ちょうどは入らない。
      提出は提出の時刻で数える (前の週に届いた分も)・'T' 区切りの時刻も読む。〆は JST の今日で比べる (UTC ではまだ前の日の 0:30 JST)
  [3] 〆を過ぎた: 宿題の期限・クラス自動宿題の題名の「〆M/D」が JST の今日より前の未提出だけ (今日が 〆 は過ぎていない・提出済みは数えない・
      古さで切らない)。3日ドリル・塾長のドリルには 〆 が無い
  [4] 単元: 〆を過ぎた未提出の単元 (〆の新しい順) を 3 つまで・同じ名前は 1 つ・【クラス名】を外す・20 字まで。〆過ぎが無ければ
      未提出の単元を「（未提出: …）」で (前の週に届いた未提出も = 点検 correct-F1)
  [5] 1 行を出さない: 何も届かず・何も出さず・未提出も無い生徒 (今日の1問だけ・何も無い)。前の週に届いた 3日ドリル (〆なし) や
      〆がまだ先の宿題だけが残っている生徒には「…0 本（未提出: …）」で出す (点検 correct-F1)。
      「今週は 0 問」の合図 (pending_recent) は窓の中に届いた未提出と 〆が直近 28 日の 〆過ぎだけ (境目 28 日ちょうど)・
      oldest_open_at = いちばん古い未提出が届いた時刻
  [6] リンク: AIなし枠は class.html?tab=homework・AI 体験中と AIあり は mypage.html?focus=homework (宿題のお知らせと同じ判定)・
      LINE は &openExternalBrowser=1・# 付きは使わない
  [7] 文と描画: LINE の本文は 1 行が無ければ今までと 1 文字も同じ・あればレポートの中に 1 行とリンク。メールの HTML は escape する
  [8] 効率: SELECT の数は生徒を 10 倍にしても同じ (ドリル 1・宿題 1)・書く SQL 0 文・cron は 1 回の実行で 1 回だけ数える
  [9] cron (dry-run): 1 行の数・単元・リンクの種類が preview に載る・全体の数・何も送らない・env OFF (WEEKLY_REPORT_HOMEWORK_ZERO_WEEK=0) では
      演習の記録が無い / 休眠の生徒を「今週は 0 問」に入れない (前からの対象は入る)
  [10] cron (本番): 生徒コピー・保護者コピーの HTML に 1 行・LINE は前から受け取っている生徒だけ (「今週は 0 問」の生徒には LINE を送らない)・
       1 行の無い生徒のメール / LINE は今までどおり・演習の記録が無い生徒の「今週は 0 問」に 1 行と「宿題を開く」(AIなし枠は塾生アプリ)・
       記録が無い生徒には「最後の演習」を書かない・休眠の生徒は書く・受講開始前と連続上限の生徒は送らない・
       古い 〆過ぎだけの休眠 / 記録なしの生徒と、同じ停止のあいだに 2 週送った生徒は送らない (点検 sending-F1 / correct-F2)・
       notifications の payload は数だけ (単元の名前は入れない)
  [11] 上限と重複: WEEKLY_REPORT_EMAIL_CAP・ZERO_WEEK_REPORT_CAP は今までどおり (通常レポートの席を奪わない・宿題で新しく入った家庭は
       前からの対象の後ろ = 枠を先に使わない)・6 日 dedup で 2 回目以降は何も送らない (メールも LINE も)・ログに生徒の名前と単元の名前を出さない
  [12] send-one (手動) も同じ 1 行・ソース (env の既定・DDL なし・CI 登録・CLAUDE.md)
  [13] 「今週は 0 問」の文 (点検 family-F1): 宿題を全部出した週は「お声がけ」「演習まで進まなかった」と書かない・AIなし枠は
       「今日の 1 問」を勧めずボタンは塾生アプリの宿題・今週 宿題を出していれば「ログインがありません」と書かない
  [14] 0〜15 週を続けて回す (点検 sending-F1 / correct-F2): 古い 〆過ぎだけでは送らない・宿題で入れた家庭は 1 回の停止につき 2 週まで
       (新しい宿題が毎週届いても)・演習するか いちばん古い未提出を出すと数え直す・env OFF は従来どおり

実行:
    python3 scripts/health_check/test_weekly_report_homework_line.py
    # exit 0 = PASS / 1 = FAIL
"""
import contextlib
import datetime
import importlib.util
import io
import json
import logging
import os
import re
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MAIN_PY = os.path.join(REPO, "server", "main.py")
WORKFLOW = os.path.join(REPO, ".github", "workflows", "server-tests.yml")
CLAUDE_MD = os.path.join(REPO, "CLAUDE.md")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []
UTC = datetime.timezone.utc
JST = datetime.timezone(datetime.timedelta(hours=9))
CRON = "test-cron-secret"
STATS = "test-stats-token"
BASE = "https://example.invalid"
L2 = "月曜2限 英文法 Lv.1"
CHW = f"class_hw_auto:kosei:{L2}"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:500]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="wr_hwline_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと本番 Postgres に書き込む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0", "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "", "ANTHROPIC_API_KEY": "", "LINE_CHANNEL_ACCESS_TOKEN": "",
        "BASE_URL": BASE, "CRON_SECRET": CRON, "STATS_TOKEN": STATS, "ZERO_WEEK_REPORT_ENABLED": "1",
    })
    for k in ("WEEKLY_REPORT_EMAIL_CAP", "WEEKLY_REPORT_HOMEWORK_ZERO_WEEK", "ZERO_WEEK_REPORT_CAP"):
        os.environ.pop(k, None)
    spec = importlib.util.spec_from_file_location("aijuku_main_wr_hwline", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def u(dt):
    """aware datetime → DB の形 (naive UTC 'YYYY-MM-DD HH:MM:SS')。"""
    return dt.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S")


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


class Fx:
    """架空の生徒・ドリル・宿題 (中身は全部この場で作る)。"""

    def __init__(self, mod):
        self.mod = mod
        self.seq = 0
        self.qid = None

    def student(self, name, *, email=None, student_email=None, verified=0, line=None, ai_disabled=0, trial=None,
                start_month=None, status="paid"):
        self.seq += 1
        far = u(datetime.datetime.now(UTC) + datetime.timedelta(days=365))
        return ex(self.mod,
                  "INSERT INTO students (name, email, status, plan, trial_end, grade, student_email, student_email_verified, "
                  "parent_email, parent_email_enabled, line_user_id, ai_disabled, ai_trial_until, start_month) "
                  "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?) RETURNING id",
                  (name, email, status, "founder_special", far, "高校2年", student_email, verified, None, 1, line,
                   ai_disabled, trial, start_month))

    def _question(self):
        if self.qid is None:
            self.qid = ex(self.mod,
                          "INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) "
                          "VALUES ('english', '時制', 'standard', '架空の問題 ( ) ?', ?, 0, '架空の解説', 'manual-drill-v1') RETURNING id",
                          (json.dumps(["a", "b", "c", "d"]),))
        return self.qid

    def drill(self, sid, created_by, *, assigned_at, unit="時制", title="架空のドリル", status="open", completed_at=None):
        did = ex(self.mod,
                 "INSERT INTO grammar_drills (subject, title, unit, level, question_ids, created_by, created_at) "
                 "VALUES ('english', ?, ?, 'standard', ?, ?, ?) RETURNING id",
                 (title, unit, json.dumps([self._question()]), created_by, assigned_at))
        ex(self.mod,
           "INSERT INTO grammar_drill_assignments (drill_id, student_id, status, assigned_at, completed_at) VALUES (?, ?, ?, ?, ?)",
           (did, sid, status, assigned_at, completed_at))
        return did

    def homework(self, sid, title, *, created_at, due=None, status="open", completed_at=None, topic=None, sheet=False):
        hid = ex(self.mod,
                 "INSERT INTO homework_assignments (student_id, title, subject, topic, due_date, status, created_at, completed_at, created_by) "
                 "VALUES (?, ?, '英語', ?, ?, ?, ?, ?, 'admin') RETURNING id",
                 (sid, title, topic, due, status, created_at, completed_at))
        if sheet:
            ex(self.mod, "INSERT INTO homework_sheets (homework_id, student_id, mode) VALUES (?, ?, 'choice')", (hid, sid))
        return hid

    def attempt(self, sid, at):
        ex(self.mod, "INSERT INTO question_attempts (student_id, source, subject, topic, is_correct, elapsed_ms, created_at) "
                     "VALUES (?, 'grammar_drill', 'english', '時制', 1, 30000, ?)", (sid, u(at)))

    def notification(self, sid, template, days_ago, channel="email"):
        at = datetime.datetime.now(UTC) - datetime.timedelta(days=days_ago)
        ex(self.mod, "INSERT INTO notifications (student_id, channel, template, payload, success, sent_at) VALUES (?,?,?,?,1,?)",
           (sid, channel, template, "{}", u(at)))


class Wire:
    """外への送信の偽物 (Resend・LINE)。宛先と本文を記録する。それ以外の宛先は例外 = 本当の外部通信を 1 本も出さない。"""

    def __init__(self):
        self.mails = []   # {to, subject, html}
        self.lines = []   # {to, text}
        self.other = []

    def urlopen(self, req, timeout=None):
        url = getattr(req, "full_url", str(req))
        body = json.loads((req.data or b"{}").decode("utf-8"))
        if url == "https://api.resend.com/emails":
            self.mails.append({"to": body["to"][0], "subject": body["subject"], "html": body["html"]})
        elif url == "https://api.line.me/v2/bot/message/push":
            self.lines.append({"to": body["to"], "text": body["messages"][0]["text"]})
        else:
            self.other.append(url)
            raise RuntimeError(f"unexpected outbound request: {url}")

        class _R:
            status = 200

            def read(self_):
                return b'{"id": "fixture"}'

            def __enter__(self_):
                return self_

            def __exit__(self_, *a):
                return False
        return _R()

    def clear(self):
        self.mails.clear(); self.lines.clear(); self.other.clear()

    def mails_to(self, to):
        return [m for m in self.mails if m["to"] == to]


@contextlib.contextmanager
def patched(wire):
    real_open, real_sleep = urllib.request.urlopen, time.sleep
    urllib.request.urlopen = wire.urlopen
    time.sleep = lambda s: None
    try:
        yield
    finally:
        urllib.request.urlopen, time.sleep = real_open, real_sleep


class CountConn:
    """SELECT の数を数える接続の包み (書く SQL も記録する)。"""

    def __init__(self, real):
        self.real = real
        self.sqls = []

    def cursor(self):
        rc = self.real.cursor()
        outer = self

        class _C:
            def execute(self_, sql, params=()):
                outer.sqls.append(sql)
                return rc.execute(sql, params)

            def fetchall(self_):
                return rc.fetchall()

            def fetchone(self_):
                return rc.fetchone()
        return _C()

    def close(self):
        self.real.close()


def legacy_line_text(name, hours, acc, problems):
    """2026-10-18 より前の週次レポートの LINE 本文 (1 行が無いときはこれと 1 文字も同じであること)。"""
    return (f"📊 {name}さんの今週のレポート\n\n"
            f"📝 演習問題数: {problems}問\n"
            f"💯 平均正答率: {acc}%\n"
            f"🔥 学習時間: {hours}時間\n\n"
            f"詳しくはマイページをご確認ください👇\n"
            f"{BASE}/mypage.html")


def main():
    print("📝 週次レポートの「今週の宿題」の 1 行 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    fx = Fx(mod)
    B = mod._weekly_report_homework_batch
    line_of = mod._weekly_report_homework_line

    # ── 固定の週 (月〜日) と「今」: 窓 = 10/12 (月) 0:00 JST 〜 10/19 (月) 0:00 JST・今 = 10/19 0:30 JST (= 10/18 15:30 UTC) ──
    LO = datetime.datetime(2026, 10, 12, 0, 0, tzinfo=JST).astimezone(UTC)   # = 10/11 15:00 UTC
    HI = datetime.datetime(2026, 10, 19, 0, 0, tzinfo=JST).astimezone(UTC)   # = 10/18 15:00 UTC
    NOW = datetime.datetime(2026, 10, 19, 0, 30, tzinfo=JST).astimezone(UTC)

    # ------------------------------------------------------------------
    print("[1] 数える種類 (今日の1問・初回診断は数えない)")
    K1 = fx.student("Kind Student", email="kind@example.org")
    fx.drill(K1, CHW, assigned_at="2026-10-13 21:00:05", title=f"【{L2}】宿題 時制（10問・〆10/20）", unit="時制")
    fx.drill(K1, "weakness_routine_3d", assigned_at="2026-10-14 20:30:00", unit="仮定法")
    fx.drill(K1, "admin", assigned_at="2026-10-15 01:00:00", unit="比較")
    fx.drill(K1, "mission_2day_routine", assigned_at="2026-10-15 09:00:00", unit="分詞", status="assigned")
    fx.homework(K1, "記号の解答用紙の宿題", created_at="2026-10-16 01:00:00", due="2026-10-25", sheet=True)
    fx.homework(K1, "プリントの宿題", created_at="2026-10-16 02:00:00", status="completed", completed_at="2026-10-17 02:00:00")
    fx.drill(K1, "today_question", assigned_at="2026-10-16 03:00:00", unit="今日の1問の単元", status="completed",
             completed_at="2026-10-16 03:05:00")
    fx.drill(K1, "diagnostic", assigned_at="2026-10-16 04:00:00", unit="診断")
    r = B([K1], LO, HI, now_utc=NOW).get(K1) or {}
    check("届いた 6 本 (クラス自動宿題・3日ドリル・塾長のドリル・15問ミッション・解答用紙の宿題・プリントの宿題)", r.get("delivered") == 6, r)
    check("提出 1 本 (プリントの宿題・今日の1問の提出は数えない)", r.get("submitted") == 1, r)
    check("〆を過ぎた未提出 0 本・未提出 5 本", r.get("overdue") == 0 and r.get("pending") == 5, r)
    check("今日の1問・初回診断の単元は出ない", "今日の1問の単元" not in (r.get("units") or []) and "診断" not in (r.get("units") or []), r)

    # ------------------------------------------------------------------
    print("\n[2] 週の境目 (JST)・提出の時刻・'T' 区切り")
    W1 = fx.student("Window Student", email="window@example.org")
    fx.drill(W1, "admin", assigned_at="2026-10-11 14:59:59", unit="前の週")                       # 日曜 23:59:59 JST = 前の週
    fx.drill(W1, "admin", assigned_at="2026-10-11 15:00:00", unit="月曜0時")                      # 月曜 0:00:00 JST = 入る
    fx.drill(W1, "admin", assigned_at="2026-10-18 14:59:59", unit="日曜最後")                     # 日曜 23:59:59 JST = 入る
    fx.drill(W1, "admin", assigned_at="2026-10-18 15:00:00", unit="次の週")                       # 次の月曜 0:00 = 入らない
    fx.drill(W1, "admin", assigned_at="2026-10-01 01:00:00", status="completed", completed_at="2026-10-11 14:59:59")   # 前の週に提出
    fx.drill(W1, "admin", assigned_at="2026-10-01 01:00:00", status="completed", completed_at="2026-10-11T15:00:00+00:00")  # 'T' 区切り
    fx.drill(W1, "admin", assigned_at="2026-10-01 01:00:00", status="completed", completed_at="2026-10-18 15:00:00")   # 次の週に提出
    r = B([W1], LO, HI, now_utc=NOW).get(W1) or {}
    check("届いた 2 本 (月曜 0:00 JST ちょうど と 日曜 23:59:59 JST・1 秒前と終わりちょうどは入らない)", r.get("delivered") == 2, r)
    check("提出 1 本 (前の週に届いた分も提出の時刻で数える・'T' 区切りも読む・境目の外は入らない)", r.get("submitted") == 1, r)
    check("未提出の単元: 窓の中に届いた分が先 (新しい順)・前の週に届いた未提出も入る・窓の後 (次の週) に届いた分は入らない",
          r.get("units") == ["日曜最後", "月曜0時", "前の週"] and r.get("units_of") == "pending" and r.get("pending") == 3, r)
    check("「今週は 0 問」の合図は窓の中に届いた未提出だけ (前の週の 〆なしは入らない)・いちばん古い未提出 = 前の週の分",
          r.get("pending_recent") == 2 and r.get("oldest_open_at") == "2026-10-11T14:59:59+00:00", r)
    r_sun = B([W1], LO, None, now_utc=NOW).get(W1) or {}
    check("終わりなし (日曜の実行 = いままで) なら次の月曜 0:00 の分も入る", r_sun.get("delivered") == 3 and r_sun.get("submitted") == 2, r_sun)

    # ------------------------------------------------------------------
    print("\n[3] 〆を過ぎた未提出 (JST の今日で比べる)")
    D1 = fx.student("Due Student", email="due@example.org")
    fx.homework(D1, "期限が昨日 (JST) の宿題", created_at="2026-10-01 01:00:00", due="2026-10-18", topic="関係詞")   # 10/19 JST では過ぎた
    fx.homework(D1, "期限が今日の宿題", created_at="2026-10-01 01:00:00", due="2026-10-19", topic="今日が期限")
    fx.homework(D1, "提出済みで期限過ぎ", created_at="2026-10-01 01:00:00", due="2026-10-10", status="completed",
                completed_at="2026-10-09 01:00:00")
    fx.homework(D1, "ずっと前の未提出", created_at="2026-06-01 01:00:00", due="2026-06-08", topic="古い宿題")
    fx.drill(D1, CHW, assigned_at="2026-10-15 21:00:05", title=f"【{L2}】宿題 不定詞（10問・〆10/18）", unit="不定詞")  # 10/16 JST に配った 〆10/18
    fx.drill(D1, CHW, assigned_at="2026-10-16 21:00:05", title=f"【{L2}】宿題 動名詞（10問・〆10/19）", unit="動名詞")  # 〆今日
    fx.drill(D1, "weakness_routine_3d", assigned_at="2026-09-01 01:00:00", unit="3日ドリルの古い未提出")         # 〆なし = K に入らない
    r = B([D1], LO, HI, now_utc=NOW).get(D1) or {}
    check("〆を過ぎた未提出 3 本 (昨日 (JST) の宿題・〆10/18 のクラス自動宿題・ずっと前の宿題 = 古さで切らない)", r.get("overdue") == 3, r)
    check("今日が 〆 / 提出済み / 〆の無い 3日ドリルは数えない", r.get("overdue") == 3 and "今日が期限" not in r.get("units", []), r)
    check("合図 pending_recent 3 (昨日 〆 の宿題・窓の中に届いた 2 本)・6/8 の 〆過ぎ・古い 3日ドリル・〆が今日の宿題は合図にしない",
          r.get("pending_recent") == 3 and r.get("pending") == 6, r)
    check("oldest_open_at = いちばん古い未提出 (6/1 に出した宿題)", r.get("oldest_open_at") == "2026-06-01T01:00:00+00:00", r)
    r_utc = B([D1], LO, HI, now_utc=datetime.datetime(2026, 10, 18, 14, 0, tzinfo=UTC)).get(D1) or {}   # = 10/18 23:00 JST
    check("JST の 10/18 23:00 では 期限 10/18 の宿題・〆10/18 のドリルはまだ過ぎていない (〆過ぎは 6/8 の 1 本だけ)",
          r_utc.get("overdue") == 1, r_utc)

    print("\n[4] 単元 (〆の新しい順・3 つまで・同じ名前は 1 つ・【】を外す・20 字まで)")
    check("〆を過ぎた未提出の単元を 〆 の新しい順に 3 つ (関係詞 / 不定詞 = 〆10/18・古い宿題 = 6/8)",
          r.get("units_of") == "overdue" and r.get("units", [])[:2] in (["関係詞", "不定詞"], ["不定詞", "関係詞"])
          and r.get("units", [])[2:] == ["古い宿題"], r)
    U1 = fx.student("Unit Student", email="unit@example.org")
    for i, un in enumerate(["時制", "時制", "【月曜2限 英文法 Lv.1】関係詞", "とても長い単元の名前がここに入りますこれは二十字を超えます", "比較"]):
        fx.drill(U1, "admin", assigned_at=f"2026-10-1{3 + i} 01:00:00", unit=un)
    r = B([U1], LO, HI, now_utc=NOW).get(U1) or {}
    us = r.get("units") or []
    check("3 つまで・同じ名前は 1 つ", len(us) == 3 and len(set(us)) == 3, us)
    check("新しい順 (比較 → 長い名前 → 関係詞)", us[:1] == ["比較"] and us[2:] == ["関係詞"], us)
    check("【クラス名】を外す", "関係詞" in us and not any("【" in x for x in us), us)
    check("20 字まで (… で切る)", any(x.endswith("…") and len(x) == 20 for x in us), us)
    check("〆過ぎが無ければ「（未提出: …）」", "（未提出: 比較・" in line_of(r) and line_of(r).startswith("📝 今週の宿題: 届いた 5 本／提出 0 本／〆を過ぎた未提出 0 本"),
          line_of(r))
    r_d1 = B([D1], LO, HI, now_utc=NOW).get(D1) or {}
    check("〆過ぎがあれば単元は K の後ろにそのまま「（関係詞・…）」", re.search(r"〆を過ぎた未提出 3 本（(関係詞|不定詞)・", line_of(r_d1)) is not None
          and "未提出:" not in line_of(r_d1), line_of(r_d1))

    # ------------------------------------------------------------------
    print("\n[5] 1 行を出さない生徒・前の週からの未提出だけの生徒 (点検 correct-F1)・合図の境目")
    E1 = fx.student("Empty Old", email="empty-old@example.org")
    fx.drill(E1, "weakness_routine_3d", assigned_at="2026-08-01 01:00:00", unit="古い3日ドリル")     # 古い未提出 (〆なし) だけ
    E2 = fx.student("Empty Today", email="empty-today@example.org")
    fx.drill(E2, "today_question", assigned_at="2026-10-14 01:00:00", unit="今日の1問")
    E3 = fx.student("Empty None", email="empty-none@example.org")
    E4 = fx.student("Empty Done", email="empty-done@example.org")                                  # 前の週に届いて前の週に提出
    fx.drill(E4, "admin", assigned_at="2026-10-05 01:00:00", unit="提出済み", status="completed", completed_at="2026-10-06 01:00:00")
    res = B([E1, E2, E3, E4], LO, HI, now_utc=NOW)
    check("今日の1問だけ・何も無い・前の週に出し終えた生徒は入らない", not ({E2, E3, E4} & set(res)), res)
    check("前の週からの未提出 (〆なしの 3日ドリル) だけの生徒にも 1 行「…0 本（未提出: 古い3日ドリル）」・合図にはしない",
          line_of(res.get(E1)) == "📝 今週の宿題: 届いた 0 本／提出 0 本／〆を過ぎた未提出 0 本（未提出: 古い3日ドリル）"
          and (res.get(E1) or {}).get("pending_recent") == 0, res.get(E1))
    # 10/18 19:00 JST の日曜の実行 (窓 = 10/12 0:00 JST 〜 いま): 10/08 JST に届いた 3日ドリル (次の 3日ドリルを止めている) と
    #   10/10 に出した 〆10/25 の宿題が未提出 → 1 行に出る (前は {} = 何も届かなかった)
    SUN = datetime.datetime(2026, 10, 18, 19, 0, tzinfo=JST).astimezone(UTC)
    OA = fx.student("Open Older A", email="open-a@example.org")
    fx.drill(OA, "weakness_routine_3d", assigned_at="2026-10-07 21:30:00", unit="仮定法")              # = 10/08 06:30 JST
    fx.homework(OA, "週末までの宿題", created_at="2026-10-10 01:00:00", due="2026-10-25", topic="関係詞")
    OC = fx.student("Open Older C", email="open-c@example.org")
    fx.drill(OC, "weakness_routine_3d", assigned_at="2026-10-07 21:30:00", unit="仮定法")
    fx.drill(OC, "admin", assigned_at="2026-10-13 01:00:00", unit="比較", status="completed", completed_at="2026-10-14 01:00:00")
    res = B([OA, OC], LO, None, now_utc=SUN)
    ra, rc = res.get(OA) or {}, res.get(OC) or {}
    check("A: 前の週に届いた 3日ドリル + 〆がまだ先の宿題 → 1 行 (届いた 0・提出 0・〆過ぎ 0・未提出: 関係詞・仮定法)",
          line_of(ra) == "📝 今週の宿題: 届いた 0 本／提出 0 本／〆を過ぎた未提出 0 本（未提出: 関係詞・仮定法）"
          and ra.get("pending") == 2 and ra.get("pending_recent") == 0, ra)
    check("C: 今週 1 本出しても、前の週からの未提出の単元を出す (全部出したように読ませない)",
          line_of(rc) == "📝 今週の宿題: 届いた 1 本／提出 1 本／〆を過ぎた未提出 0 本（未提出: 仮定法）" and rc.get("pending") == 1, rc)
    R1 = fx.student("Recent Due 28", email="recent-28@example.org")
    fx.homework(R1, "28 日前が 〆", created_at="2026-09-01 01:00:00", due="2026-09-21", topic="倒置")       # 10/19 JST − 28 日
    R2 = fx.student("Recent Due 29", email="recent-29@example.org")
    fx.homework(R2, "29 日前が 〆", created_at="2026-09-01 01:00:00", due="2026-09-20", topic="倒置")
    res = B([R1, R2], LO, HI, now_utc=NOW)
    check("合図の境目: 〆が 28 日前は入る・29 日前は入らない (どちらも K には入る = 古さで切らない)",
          (res.get(R1) or {}).get("pending_recent") == 1 and (res.get(R2) or {}).get("pending_recent") == 0
          and (res.get(R1) or {}).get("overdue") == 1 and (res.get(R2) or {}).get("overdue") == 1, res)
    check("空の値の文は ''", line_of(None) == "" and line_of({"delivered": 0, "submitted": 0, "overdue": 0}) == ""
          and line_of({"delivered": 0, "submitted": 0, "overdue": 0, "pending": 0}) == "")
    check("生徒が 0 人なら {} (SELECT しない)", B([], LO, HI, now_utc=NOW) == {})

    # ------------------------------------------------------------------
    print("\n[6] リンク (AIなし枠 = 塾生アプリ・AI 体験中 / AIあり = マイページ)")
    future = u(datetime.datetime.now(UTC) + datetime.timedelta(days=20))
    LA = fx.student("Link Nashi", email="link-a@example.org", ai_disabled=1)
    LB = fx.student("Link Trial", email="link-b@example.org", ai_disabled=1, trial=future)
    LC = fx.student("Link Ai", email="link-c@example.org", ai_disabled=0)
    for s_ in (LA, LB, LC):
        fx.drill(s_, "admin", assigned_at="2026-10-14 01:00:00", unit="時制")
    res = B([LA, LB, LC], LO, HI, now_utc=NOW)
    check("AIなし枠: class.html?tab=homework", res.get(LA, {}).get("url") == f"{BASE}/class.html?tab=homework"
          and res.get(LA, {}).get("link") == "class", res.get(LA))
    check("AI 体験中: mypage.html?focus=homework", res.get(LB, {}).get("url") == f"{BASE}/mypage.html?focus=homework", res.get(LB))
    check("AIあり: mypage.html?focus=homework", res.get(LC, {}).get("url") == f"{BASE}/mypage.html?focus=homework", res.get(LC))
    check("LINE 用は &openExternalBrowser=1", res.get(LA, {}).get("line_url") == f"{BASE}/class.html?tab=homework&openExternalBrowser=1"
          and res.get(LC, {}).get("line_url") == f"{BASE}/mypage.html?focus=homework&openExternalBrowser=1", res)
    check("# 付きのリンクは使わない", all("#" not in (v.get("url") or "") + (v.get("line_url") or "") for v in res.values()), res)

    # ------------------------------------------------------------------
    print("\n[7] 文と描画 (LINE は 1 行が無ければ今までと同じ・メールは escape)")
    tmpl = mod.LINE_TEMPLATES["weekly_report"]
    base_p = {"name": "Fixture Kid", "hours": 1.5, "accuracy": 80, "problems_done": 12, "questions": 0, "url": f"{BASE}/mypage.html"}
    check("1 行が無い LINE の本文は今までと 1 文字も同じ", tmpl(base_p)["text"] == legacy_line_text("Fixture Kid", 1.5, 80, 12), tmpl(base_p)["text"])
    t_hw = tmpl({**base_p, "homework_line": "📝 今週の宿題: 届いた 2 本／提出 1 本／〆を過ぎた未提出 1 本（時制）",
                 "homework_url": f"{BASE}/class.html?tab=homework&openExternalBrowser=1"})["text"]
    check("1 行がある LINE: 学習時間の後に 1 行と「宿題を開く👇」とリンク・最後はマイページのまま",
          "🔥 学習時間: 1.5時間\n\n📝 今週の宿題: 届いた 2 本／提出 1 本／〆を過ぎた未提出 1 本（時制）\n宿題を開く👇\n"
          f"{BASE}/class.html?tab=homework&openExternalBrowser=1\n\n詳しくはマイページをご確認ください👇\n{BASE}/mypage.html" in t_hw, t_hw)
    X1 = fx.student("Escape Student", email="esc@example.org", ai_disabled=1)
    fx.homework(X1, "題名", created_at="2026-10-14 01:00:00", due="2026-10-15", topic="<b>関係詞</b>")
    hwx = B([X1], LO, HI, now_utc=NOW).get(X1)
    ctx = mod._weekly_report_minimal_ctx("Escape Student", {"hours": 1, "problems_done": 3, "questions": 0, "accuracy": 50,
                                                             "subject_stats": {}, "weakest_subject": None})
    html0 = mod._render_weekly_report_html(dict(ctx))
    check("1 行が無いレポートの HTML には「今週の宿題」が無い", "今週の宿題" not in html0)
    html1 = mod._render_weekly_report_html({**ctx, "homework": hwx})
    check("1 行があるレポートの HTML: 文 (escape 済み) と「宿題を開く」のリンク (AIなし枠 = 塾生アプリ)",
          "📝 今週の宿題: 届いた 1 本／提出 0 本／〆を過ぎた未提出 1 本（&lt;b&gt;関係詞&lt;/b&gt;）" in html1
          and f'href="{BASE}/class.html?tab=homework"' in html1 and "<b>関係詞</b>" not in html1, html1[:300])

    # ------------------------------------------------------------------
    print("\n[8] 効率 (生徒を 10 倍にしても SELECT の数は同じ・書かない)")
    few = [K1, W1, D1]
    many = list(few)
    for i in range(27):
        s_ = fx.student(f"Bulk {i:02d}", email=f"bulk-{i:02d}@example.org")
        fx.drill(s_, CHW, assigned_at="2026-10-14 21:00:05", title=f"【{L2}】宿題 時制（10問・〆10/16）")
        fx.homework(s_, "宿題", created_at="2026-10-14 01:00:00", due="2026-10-15")
        many.append(s_)
    calls = {"link": 0}
    real_link = mod._homework_notify_link_paths

    def link_spy(ids):
        calls["link"] += 1
        return real_link(ids)
    mod._homework_notify_link_paths = link_spy
    cc_few = CountConn(mod.db())
    B(few, LO, HI, now_utc=NOW, conn=cc_few)
    cc_few.close()
    cc_many = CountConn(mod.db())
    res_many = B(many, LO, HI, now_utc=NOW, conn=cc_many)
    cc_many.close()
    mod._homework_notify_link_paths = real_link
    check("SELECT の数: 3 名でも 30 名でも 2 文 (ドリル 1・宿題 1)", len(cc_few.sqls) == 2 and len(cc_many.sqls) == 2,
          (len(cc_few.sqls), len(cc_many.sqls)))
    check("リンクの照会は 1 回の実行で 1 回 (生徒ごとに回さない)", calls["link"] == 2, calls)
    check("書く SQL は 0 文", not any(re.match(r"\s*(INSERT|UPDATE|DELETE|ALTER|CREATE|DROP)", s_, re.I) for s_ in cc_many.sqls + cc_few.sqls))
    check("30 名分を数えた (クラス自動宿題の 〆10/16・宿題の期限 10/15 で 〆過ぎ 2 本)",
          all(res_many.get(s_, {}).get("overdue") == 2 for s_ in many[3:]), {s_: res_many.get(s_) for s_ in many[3:6]})
    # この節で作った生徒は cron の母集団から外す (下の cron の数を読みやすくする)
    ex(mod, f"UPDATE students SET status = 'canceled' WHERE id IN ({','.join(str(x) for x in many + [U1, E1, E2, E3, E4, OA, OC, R1, R2, LA, LB, LC, X1])})")

    # ------------------------------------------------------------------
    # cron の生徒 (今 = 本物の時刻・窓は「3 日前から今まで」に差し替える = 曜日に関係なく同じ結果)
    now = datetime.datetime.now(UTC)
    today = now.astimezone(JST).date()
    yday = today - datetime.timedelta(days=1)
    lo = now - datetime.timedelta(days=3)
    mod._weekly_report_window = lambda now_jst=None: (lo, None)
    mod._weekly_coach_comments = lambda c_: {**c_, **mod._weekly_coach_comments_fallback(c_)}
    mod.RESEND_API_KEY = "re_fixture_not_real"
    mod.LINE_CHANNEL_ACCESS_TOKEN = "line_fixture_not_real"
    in_win = u(now - datetime.timedelta(days=2))
    before = u(now - datetime.timedelta(days=10))
    chw_title_over = f"【{L2}】宿題 時制（10問・〆{yday.month}/{yday.day}）"
    P1 = fx.student("Family P1", email="p1-parent@example.org", student_email="p1-child@example.org", verified=1, line="U-fx-p1")
    fx.attempt(P1, now - datetime.timedelta(hours=1))
    fx.drill(P1, CHW, assigned_at=in_win, title=chw_title_over, unit="時制")                              # 〆昨日 = 〆過ぎ
    fx.drill(P1, "weakness_routine_3d", assigned_at=in_win, unit="仮定法", status="completed", completed_at=u(now - datetime.timedelta(days=1)))
    fx.drill(P1, "admin", assigned_at=before, unit="比較", status="completed", completed_at=u(now - datetime.timedelta(days=1)))
    fx.homework(P1, "週末の宿題", created_at=in_win, due=(today + datetime.timedelta(days=2)).isoformat(), topic="関係詞")
    fx.drill(P1, "today_question", assigned_at=in_win, unit="今日の1問")
    P2 = fx.student("Family P2", email="p2@example.org", line="U-fx-p2", ai_disabled=1)                   # AIなし枠
    fx.attempt(P2, now - datetime.timedelta(hours=2))
    fx.homework(P2, "記号の宿題", created_at=before, due=yday.isoformat(), topic="分詞構文", sheet=True)
    fx.drill(P2, "mission_2day_routine", assigned_at=in_win, unit="不定詞", status="assigned")
    P3 = fx.student("Family P3", email="p3@example.org", line="U-fx-p3")                                  # 宿題なし
    fx.attempt(P3, now - datetime.timedelta(hours=3))
    P4 = fx.student("Family P4", email="p4@example.org")                                                  # 古い未提出 (〆なし) だけ
    fx.attempt(P4, now - datetime.timedelta(hours=4))
    fx.drill(P4, "weakness_routine_3d", assigned_at=u(now - datetime.timedelta(days=30)), unit="古い3日ドリル")
    Z1 = fx.student("Family Z1", email="z1@example.org", line="U-fx-z1", ai_disabled=1)                   # 演習の記録なし・未提出あり
    fx.drill(Z1, CHW, assigned_at=in_win, title=f"【{L2}】宿題 時制（10問・〆{(today + datetime.timedelta(days=1)).month}/"
                                                f"{(today + datetime.timedelta(days=1)).day}）", unit="時制")
    Z2 = fx.student("Family Z2", email="z2@example.org")                                                  # 演習の記録なし・宿題なし
    Z3 = fx.student("Family Z3", email="z3@example.org")                                                  # 休眠 (60 日前)・〆過ぎ
    fx.attempt(Z3, now - datetime.timedelta(days=60))
    fx.homework(Z3, "休眠の宿題", created_at=u(now - datetime.timedelta(days=12)), due=(today - datetime.timedelta(days=5)).isoformat(),
                topic="比較")
    Z4 = fx.student("Family Z4", email="z4@example.org")                                                  # 5 日前に演習 (前からの対象)・未提出あり
    fx.attempt(Z4, now - datetime.timedelta(days=5))
    fx.drill(Z4, "weakness_routine_3d", assigned_at=in_win, unit="助動詞")
    Z5 = fx.student("Family Z5", email="z5@example.org", start_month="2099-01")                           # 受講開始前
    fx.drill(Z5, "admin", assigned_at=in_win, unit="時制")
    Z6 = fx.student("Family Z6", email="z6@example.org")                                                  # 連続上限 (2 週送った)
    fx.drill(Z6, "admin", assigned_at=in_win, unit="時制")
    fx.notification(Z6, "weekly_report_zero_week", 7)
    fx.notification(Z6, "weekly_report_zero_week", 14)
    Z7 = fx.student("Family Z7", email="z7@example.org")                                                  # 5 日前に演習・宿題なし (前からの対象)
    fx.attempt(Z7, now - datetime.timedelta(days=5))
    # ★点検 sending-F1 / correct-F2: 古い 〆過ぎだけの休眠 / 記録なしの家庭と、同じ停止のあいだに 2 週送った家庭には送らない
    Z8 = fx.student("Family Z8", email="z8@example.org")                                                  # 休眠 (60 日前)・古い 〆過ぎだけ
    fx.attempt(Z8, now - datetime.timedelta(days=60))
    fx.homework(Z8, "休眠の古い宿題", created_at=u(now - datetime.timedelta(days=70)),
                due=(today - datetime.timedelta(days=40)).isoformat(), topic="倒置")
    Z9 = fx.student("Family Z9", email="z9@example.org")                                                  # 演習の記録なし・古い 〆過ぎだけ
    fx.homework(Z9, "記録なしの古い宿題", created_at=u(now - datetime.timedelta(days=100)),
                due=(today - datetime.timedelta(days=90)).isoformat(), topic="強調構文")
    Z10 = fx.student("Family Z10", email="z10@example.org")                                               # 記録なし・新しい宿題もあるが、
    fx.homework(Z10, "ずっと出していない宿題", created_at=u(now - datetime.timedelta(days=60)),               #   いちばん古い未提出が届いてから
                due=(today - datetime.timedelta(days=50)).isoformat(), topic="話法")                       #   2 週送った (40・35 日前 = 29 日の外)
    fx.drill(Z10, "admin", assigned_at=in_win, unit="話法")
    fx.notification(Z10, "weekly_report_zero_week", 40)
    fx.notification(Z10, "weekly_report_zero_week", 35)
    NAMES = ["Family P1", "Family P2", "Family P3", "Family P4", "Family Z1", "Family Z2", "Family Z3", "Family Z4",
             "Family Z5", "Family Z6", "Family Z7", "Family Z8", "Family Z9", "Family Z10"]
    UNITS = ["時制", "仮定法", "比較", "関係詞", "分詞構文", "不定詞", "助動詞", "古い3日ドリル", "倒置", "強調構文", "話法"]

    logbuf = io.StringIO()
    handler = logging.StreamHandler(logbuf)
    handler.setLevel(logging.DEBUG)
    root = logging.getLogger()
    old_level = root.level
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)
    mod.log.setLevel(logging.DEBUG)

    batch_calls = {"n": 0}
    real_batch = mod._weekly_report_homework_batch

    def batch_spy(*a, **k):
        batch_calls["n"] += 1
        return real_batch(*a, **k)
    mod._weekly_report_homework_batch = batch_spy

    wire = Wire()

    def run(dry=False):
        wire.clear()
        with patched(wire):
            r_ = client.post("/api/cron/weekly-reports" + ("?dry_run=true" if dry else ""), headers={"X-Cron-Secret": CRON})
        return r_.status_code, (r_.json() if r_.status_code == 200 else r_.text)

    # ------------------------------------------------------------------
    print("\n[9] cron の dry-run")
    os.environ["WEEKLY_REPORT_HOMEWORK_ZERO_WEEK"] = "0"
    st, j = run(dry=True)
    pv = {p["student_id"]: p for p in ((j or {}).get("previews") or [])} if isinstance(j, dict) else {}
    check("env OFF: 200・何も送らない", st == 200 and not wire.mails and not wire.lines and not wire.other, j)
    check("env OFF: 演習の記録が無い Z1・休眠の Z3 は「今週は 0 問」に入らない (従来どおり)", Z1 not in pv and Z3 not in pv, sorted(pv))
    check("env OFF: Z8・Z9・Z10 も入らない", not ({Z8, Z9, Z10} & set(pv)), sorted(pv))
    check("env OFF: 前からの対象 Z4 は入り、1 行も付く", pv.get(Z4, {}).get("zero_week") is True
          and (pv.get(Z4, {}).get("homework") or {}).get("delivered") == 1 and pv.get(Z4, {}).get("zero_week_via_homework") is False, pv.get(Z4))
    check("env OFF: 応答に homework_zero_week_enabled False", isinstance(j, dict) and j.get("homework_zero_week_enabled") is False, j)
    os.environ.pop("WEEKLY_REPORT_HOMEWORK_ZERO_WEEK", None)
    batch_calls["n"] = 0
    st, j = run(dry=True)
    pv = {p["student_id"]: p for p in ((j or {}).get("previews") or [])} if isinstance(j, dict) else {}
    check("env 既定 (ON): 200・何も送らない", st == 200 and not wire.mails and not wire.lines, j)
    check("宿題の数は 1 回の実行で 1 回だけ (生徒ごとに回さない)", batch_calls["n"] == 1, batch_calls)
    h1 = (pv.get(P1) or {}).get("homework") or {}
    check("P1: 届いた 3 (クラス自動宿題・3日ドリル・宿題)・提出 2 (前の週に届いた塾長のドリルも)・〆過ぎ 1・今日の1問は数えない",
          (h1.get("delivered"), h1.get("submitted"), h1.get("overdue")) == (3, 2, 1), h1)
    check("P1: 単元は 〆過ぎの「時制」・リンクはマイページ・文が載る", h1.get("units") == ["時制"] and h1.get("link") == "mypage"
          and h1.get("line") == "📝 今週の宿題: 届いた 3 本／提出 2 本／〆を過ぎた未提出 1 本（時制）", h1)
    h2 = (pv.get(P2) or {}).get("homework") or {}
    check("P2 (AIなし枠): 届いた 1 (15問ミッション)・〆過ぎ 1 (記号の宿題)・リンクは塾生アプリ",
          (h2.get("delivered"), h2.get("submitted"), h2.get("overdue"), h2.get("link")) == (1, 0, 1, "class")
          and h2.get("units") == ["分詞構文"], h2)
    check("P3 (宿題なし) は 1 行なし (homework None)", P3 in pv and pv[P3].get("homework") is None, pv.get(P3))
    h4 = (pv.get(P4) or {}).get("homework") or {}
    check("P4 (前からの未提出 = 30 日前の 3日ドリルだけ) にも 1 行「…0 本（未提出: 古い3日ドリル）」(点検 correct-F1)",
          h4.get("line") == "📝 今週の宿題: 届いた 0 本／提出 0 本／〆を過ぎた未提出 0 本（未提出: 古い3日ドリル）"
          and h4.get("pending") == 1 and h4.get("pending_recent") == 0, h4)
    check("env ON: 演習の記録が無い Z1 が「今週は 0 問」に入る (via_homework・LINE は送らない)",
          pv.get(Z1, {}).get("zero_week") is True and pv.get(Z1, {}).get("zero_week_via_homework") is True
          and pv.get(Z1, {}).get("would_send_line") is False and (pv.get(Z1, {}).get("homework") or {}).get("link") == "class", pv.get(Z1))
    check("env ON: 休眠の Z3 も入る (〆過ぎ 1)", pv.get(Z3, {}).get("zero_week_via_homework") is True
          and (pv.get(Z3, {}).get("homework") or {}).get("overdue") == 1, pv.get(Z3))
    check("宿題の無い Z2・受講開始前の Z5・連続上限の Z6 は入らない", not ({Z2, Z5, Z6} & set(pv)), sorted(pv))
    check("古い 〆過ぎだけの休眠 Z8・記録なし Z9 は入らない (合図は窓の中に届いた未提出と直近 28 日の 〆過ぎだけ = 点検 sending-F1)",
          Z8 not in pv and Z9 not in pv, sorted(pv))
    check("Z10 (新しい宿題はあるが、いちばん古い未提出が届いてから 2 週送った = 29 日の外でも) は入らない (点検 correct-F2)",
          Z10 not in pv, sorted(pv))
    check("前からの対象 Z7 (宿題なし) は今までどおり入る・1 行なし", pv.get(Z7, {}).get("zero_week") is True and pv[Z7].get("homework") is None, pv.get(Z7))
    check("集計: homework_lines 6 (P1・P2・P4・Z1・Z3・Z4)・zero_week_homework 2 (Z1・Z3)",
          isinstance(j, dict) and j.get("homework_lines") == 6 and j.get("zero_week_homework") == 2, j)
    tot = (j or {}).get("homework_totals") or {}
    check("homework_totals (名前なしの数だけ・母集団の生徒の合計: P1・P2・P4・Z1・Z3・Z4・Z5・Z6・Z8・Z9・Z10 = 11 名・届いた 9・〆過ぎ 6)",
          tot.get("students") == 11 and tot.get("delivered") == 3 + 1 + 1 + 0 + 1 + 1 + 1 + 1 and tot.get("submitted") == 2
          and tot.get("overdue") == 1 + 1 + 1 + 3, tot)
    pz = (pv.get(Z1) or {}).get("homework") or {}
    check("dry-run の preview に合図の数 (pending_recent) も載る", pz.get("pending_recent") == 1, pz)

    # ------------------------------------------------------------------
    print("\n[10][11] cron の本番 (上限・重複・中身)")
    reg_emails = sum(bool(p.get("student_copy_to")) + bool(p.get("parent_copy_to")) for p in pv.values() if not p.get("zero_week"))
    os.environ["WEEKLY_REPORT_EMAIL_CAP"] = str(reg_emails)
    try:
        st, j = run()
    finally:
        os.environ.pop("WEEKLY_REPORT_EMAIL_CAP", None)
    check("A (メールの上限 = 通常レポートの通数): 200・外へは Resend と LINE だけ", st == 200 and not wire.other, (j, wire.other))
    check("A: 通常レポートは全部送る (席を奪わない)・「今週は 0 問」は 0 通で capped", isinstance(j, dict) and j.get("sent_email") == reg_emails
          and j.get("zero_week") == 0 and j.get("capped", 0) >= 3 and j.get("zero_week_queued") == 4, j)
    m1c, m1p = wire.mails_to("p1-child@example.org"), wire.mails_to("p1-parent@example.org")
    line1 = "📝 今週の宿題: 届いた 3 本／提出 2 本／〆を過ぎた未提出 1 本（時制）"
    check("P1: 生徒コピー (子) と保護者コピーの両方に 1 行と「宿題を開く」(マイページ)",
          len(m1c) == 1 and len(m1p) == 1 and all(line1 in m["html"] and f'href="{BASE}/mypage.html?focus=homework"' in m["html"]
                                                   for m in m1c + m1p), [m["html"][:200] for m in m1c + m1p])
    m2 = wire.mails_to("p2@example.org")
    check("P2 (AIなし枠): 1 行と塾生アプリの宿題タブのリンク", len(m2) == 1 and "〆を過ぎた未提出 1 本（分詞構文）" in m2[0]["html"]
          and f'href="{BASE}/class.html?tab=homework"' in m2[0]["html"], m2[:1])
    m3, m4 = wire.mails_to("p3@example.org"), wire.mails_to("p4@example.org")
    check("P3: 1 行の無いレポート (今までどおり)", len(m3) == 1 and "今週の宿題" not in m3[0]["html"])
    check("P4: 前からの未提出の 1 行「（未提出: 古い3日ドリル）」と宿題のリンク", len(m4) == 1
          and "〆を過ぎた未提出 0 本（未提出: 古い3日ドリル）" in m4[0]["html"] and f'href="{BASE}/mypage.html?focus=homework"' in m4[0]["html"],
          m4[:1])
    lines = {ln["to"]: ln["text"] for ln in wire.lines}
    check("LINE は前から受け取っている P1・P2・P3 だけ (「今週は 0 問」の Z1 には送らない)", sorted(lines) == ["U-fx-p1", "U-fx-p2", "U-fx-p3"], sorted(lines))
    check("P1 の LINE: 1 行と mypage の宿題のリンク (&openExternalBrowser=1)",
          f"{line1}\n宿題を開く👇\n{BASE}/mypage.html?focus=homework&openExternalBrowser=1\n" in lines.get("U-fx-p1", ""), lines.get("U-fx-p1"))
    check("P2 の LINE: 塾生アプリの宿題タブ (&openExternalBrowser=1)",
          f"宿題を開く👇\n{BASE}/class.html?tab=homework&openExternalBrowser=1\n" in lines.get("U-fx-p2", ""), lines.get("U-fx-p2"))
    p3_line = lines.get("U-fx-p3", "")
    check("P3 の LINE は今までと同じ本文 (1 行なし)", "今週の宿題" not in p3_line and p3_line.endswith(
        "時間\n\n詳しくはマイページをご確認ください👇\n" + f"{BASE}/mypage.html"), p3_line)
    check("A: homework_lines 6 (送った P1・P2・P4 + 積んだ Z1・Z3・Z4)・homework_error なし",
          isinstance(j, dict) and j.get("homework_lines") == 6 and j.get("homework_error") is None, j)

    mod.ZERO_WEEK_REPORT_CAP = 1
    try:
        st, j = run()
    finally:
        mod.ZERO_WEEK_REPORT_CAP = 24
    check("B (ZERO_WEEK_REPORT_CAP=1): 通常レポートは 6 日 dedup で 0 通・LINE 0", isinstance(j, dict)
          and not [m for m in wire.mails if m["to"].startswith("p")] and not wire.lines and j.get("skipped_dup") == 4, j)
    b_mails = list(wire.mails)
    zb = [m["to"] for m in b_mails]
    check("B: 「今週は 0 問」は 1 通だけ・残りは capped", len(zb) == 1 and j.get("zero_week") == 1 and j.get("capped", 0) >= 1, (zb, j))
    check("B: 枠は前からの対象 (Z4・Z7 = 直近 28 日に演習) が先に使う (宿題で新しく入った Z1・Z3 は後ろ = 締め出さない)",
          zb in (["z4@example.org"], ["z7@example.org"]), zb)
    st, j = run()
    c_mails = list(wire.mails)
    zc = [m["to"] for m in c_mails]
    check("C: 残りの「今週は 0 問」を送る (B で送った家庭には送らない)", sorted(zb + zc) == ["z1@example.org", "z3@example.org", "z4@example.org", "z7@example.org"]
          and len(set(zb + zc)) == 4 and not wire.lines, (zb, zc))
    st, j = run()
    check("D: 4 回目は何も送らない (メールも LINE も・6 日 dedup)", not wire.mails and not wire.lines, (wire.mails, wire.lines))
    all_zero = {m["to"]: m for m in b_mails + c_mails}
    z1h = (all_zero.get("z1@example.org") or {}).get("html", "")
    check("Z1 (演習の記録なし・AIなし枠): 1 行・ボタンは「📝 宿題を開く」(塾生アプリ)・「最後の演習」は書かない・「今日の 1 問」は出さない",
          "📝 今週の宿題: 届いた 1 本／提出 0 本／〆を過ぎた未提出 0 本（未提出: 時制）" in z1h and "📝 宿題を開く" in z1h
          and f'href="{BASE}/class.html?tab=homework"' in z1h and "最後の演習" not in z1h and "今日の 1 問" not in z1h, z1h[:600])
    z1s = (all_zero.get("z1@example.org") or {}).get("subject", "")
    check("Z1: 件名は「まだ出していない宿題があります」", "まだ出していない宿題があります" in z1s, z1s)
    z3h = (all_zero.get("z3@example.org") or {}).get("html", "")
    check("Z3 (休眠): 「最後の演習: … 60 日前」を書く・〆過ぎの 1 行", "60 日前" in z3h and "〆を過ぎた未提出 1 本（比較）" in z3h, z3h[:600])
    z7h = (all_zero.get("z7@example.org") or {}).get("html", "")
    check("Z7 (宿題なし・前からの対象): 今までどおり「今日の 1 問」・宿題の 1 行なし",
          "今日の 1 問を解く" in z7h and "今週の宿題" not in z7h and "5 日前" in z7h, z7h[:600])
    check("「最大 2 週連続」の注記はそのまま", all("最大 2 週連続までお送りします" in m["html"] for m in all_zero.values()), list(all_zero))
    rows = q(mod, "SELECT student_id, payload FROM notifications WHERE template = 'weekly_report_zero_week' AND success = 1 "
                  f"AND student_id IN ({Z1}, {Z3}, {Z4})")
    pl = {r_["student_id"]: json.loads(r_["payload"]) for r_ in rows}
    check("notifications の payload: 宿題は数だけ (hw = n/m/k)・単元の名前は入れない・via_homework",
          pl.get(Z1, {}).get("hw") == {"n": 1, "m": 0, "k": 0} and pl.get(Z1, {}).get("via_homework") is True
          and pl.get(Z4, {}).get("via_homework") is False and not any(un in json.dumps(pl, ensure_ascii=False) for un in UNITS), pl)

    print("\n[11] ログに生徒の名前と単元の名前を出さない")
    root.removeHandler(handler)
    root.setLevel(old_level)
    logs = logbuf.getvalue()
    check("ログに生徒の名前が無い", not any(n in logs for n in NAMES), [n for n in NAMES if n in logs])
    check("ログに単元の名前が無い", not any(un in logs for un in UNITS), [un for un in UNITS if un in logs])

    # ------------------------------------------------------------------
    print("\n[12] send-one (手動) とソース")
    mod._weekly_report_homework_batch = real_batch
    wire.clear()
    origin = mod.ALLOWED_ORIGINS[0].rstrip("/")
    with patched(wire):
        r_ = client.post("/api/weekly-reports/send-one", json={"student_id": P1}, headers={"X-Stats-Token": STATS, "Origin": origin})
    check("send-one が 200", r_.status_code == 200, r_.text[:200])
    check("send-one のメールと LINE にも同じ 1 行", any(line1 in m["html"] for m in wire.mails) and any(line1 in ln["text"] for ln in wire.lines),
          (wire.mails[:1], wire.lines[:1]))
    src = open(MAIN_PY, encoding="utf-8").read()
    i0 = src.index("def _weekly_report_homework_batch(")
    body = src[i0:src.index("\ndef ", i0 + 10)]
    check("数える関数に書く SQL・DDL が無い", not re.search(r"\b(INSERT|UPDATE|DELETE|ALTER|CREATE|DROP)\b", body), body[:200])
    check("env の既定は ON (WEEKLY_REPORT_HOMEWORK_ZERO_WEEK=1)", 'os.getenv("WEEKLY_REPORT_HOMEWORK_ZERO_WEEK", "1")' in src)
    os.environ["WEEKLY_REPORT_HOMEWORK_ZERO_WEEK"] = "off"
    off = mod._weekly_report_homework_zero_week_enabled()
    os.environ["WEEKLY_REPORT_HOMEWORK_ZERO_WEEK"] = "1"
    on = mod._weekly_report_homework_zero_week_enabled()
    os.environ.pop("WEEKLY_REPORT_HOMEWORK_ZERO_WEEK", None)
    check("env は呼ぶたびに読む (off → False・1 → True・無し → True)", off is False and on is True and mod._weekly_report_homework_zero_week_enabled() is True)
    i1 = src.index("def cron_weekly_reports(")
    cron = src[i1:src.index("\ndef _require_admin_or_stats_token", i1)]
    check("cron は生徒のループの前に 1 回だけ数える", cron.count("_weekly_report_homework_batch(") == 1
          and cron.index("_weekly_report_homework_batch(") < cron.index("for row in students:"))
    wf = open(WORKFLOW, encoding="utf-8").read()
    check("CI (server-tests.yml) に登録", "test_weekly_report_homework_line.py" in wf)
    check("CLAUDE.md に 1 行の節", "WEEKLY_REPORT_HOMEWORK_ZERO_WEEK" in open(CLAUDE_MD, encoding="utf-8").read())

    # ------------------------------------------------------------------
    print("\n[13] 「今週は 0 問」の文 (宿題を全部出した週・AIなし枠・今週 宿題を出した生徒 = 点検 family-F1)")
    FA = fx.student("Done Ai", email="done-ai@example.org")
    FN = fx.student("Done Nashi", email="done-nashi@example.org", ai_disabled=1)
    FP = fx.student("Part Done", email="part-done@example.org")
    for s_ in (FA, FN):
        fx.homework(s_, "記号の解答用紙の宿題", created_at="2026-10-13 01:00:00", due="2026-10-16", status="completed",
                    completed_at="2026-10-14 01:00:00", sheet=True)
        fx.homework(s_, "プリントの宿題", created_at="2026-10-13 02:00:00", status="completed", completed_at="2026-10-15 01:00:00")
    fx.homework(FP, "出した宿題", created_at="2026-10-13 01:00:00", status="completed", completed_at="2026-10-14 01:00:00")
    fx.homework(FP, "まだの宿題", created_at="2026-10-13 02:00:00", due="2026-10-25", topic="関係詞")
    hwf = B([FA, FN, FP], LO, HI, now_utc=NOW)
    ex(mod, f"UPDATE students SET status = 'canceled' WHERE id IN ({FA}, {FN}, {FP})")
    check("前提: FA・FN は届いた 2・提出 2・未提出 0 / FP は提出 1・未提出 1",
          all((hwf.get(x) or {}).get("submitted") == 2 and (hwf.get(x) or {}).get("pending") == 0 for x in (FA, FN))
          and (hwf.get(FP) or {}).get("submitted") == 1 and (hwf.get(FP) or {}).get("pending") == 1, hwf)

    def zmail(hw, is_parent, recent_login=True):
        wire.clear()
        zw_ = {"days_since": 10, "last_active_date": "2026-10-08", "recent_login": recent_login, "via_homework": False}
        if hw is not None:
            zw_["homework"] = hw
        with patched(wire):
            mod._send_zero_week_report_email("fixture-to@example.org", "Fixture Kid", zw_, is_parent=is_parent)
        return (wire.mails[0] if wire.mails else {"subject": "", "html": ""})

    pa = zmail(hwf.get(FA), True)
    check("FA 保護者: 宿題を全部出した週は「お声がけ」「演習まで進まなかった」と書かず「全部提出できています」",
          "お声がけ" not in pa["html"] and "演習まで進まなかった" not in pa["html"] and "今週の宿題は全部提出できています" in pa["html"]
          and "提出 2 本" in pa["html"] and "「今日は 1 問だけ」から再開できます" in pa["html"], pa["html"][:900])
    sa = zmail(hwf.get(FA), False)
    check("FA 生徒: 件名と文が「全部出せました」・「久しぶりの日は」と書かない・ボタンは今日の 1 問のまま",
          "今週の宿題は全部出せました" in sa["subject"] and "久しぶりの日は" not in sa["html"] and "今日の 1 問を解く" in sa["html"],
          (sa["subject"], sa["html"][:900]))
    pn = zmail(hwf.get(FN), True)
    check("FN 保護者 (AIなし枠): 「今日は 1 問」を勧めない・ボタンは「📝 宿題を開く」(塾生アプリ)・リンクは 1 か所",
          "今日は 1 問" not in pn["html"] and "お声がけ" not in pn["html"] and "📝 宿題を開く" in pn["html"]
          and pn["html"].count(f"{BASE}/class.html?tab=homework") == 1, pn["html"][:900])
    sn = zmail(hwf.get(FN), False)
    check("FN 生徒 (AIなし枠): 件名「今週の宿題は全部出せました」・「今日の 1 問」は出さない・ボタンは塾生アプリの宿題",
          sn["subject"].endswith("今週の宿題は全部出せました") and "今日の 1 問" not in sn["html"]
          and f'href="{BASE}/class.html?tab=homework"' in sn["html"], (sn["subject"], sn["html"][:900]))
    pl_ = zmail(hwf.get(FA), True, recent_login=False)
    check("FA 保護者・直近 7 日のログインなし: 今週 宿題を出しているので「ログインがありません」と書かない",
          "ログインがありません" not in pl_["html"] and "今週の宿題は全部提出できています" in pl_["html"], pl_["html"][:900])
    pp = zmail(hwf.get(FP), True, recent_login=False)
    check("FP 保護者・ログインなし・未提出あり: 「今週は宿題を 1 本提出しています。まだ提出していない宿題があります」",
          "ログインがありません" not in pp["html"] and "今週は宿題を 1 本提出しています。まだ提出していない宿題があります" in pp["html"]
          and "📝 宿題を開く" in pp["html"], pp["html"][:900])
    p0 = zmail(None, True)
    check("宿題の 1 行が無いメールは今までどおり (演習まで進まなかった・お声がけ)",
          "今週は演習まで進まなかったようです" in p0["html"] and "お声がけいただけると助かります" in p0["html"] and "今週の宿題" not in p0["html"],
          p0["html"][:900])
    p00 = zmail(None, True, recent_login=False)
    check("宿題の 1 行が無く・ログインなしは今までどおり「ログインがありません」", "ログインがありません" in p00["html"], p00["html"][:900])

    # ------------------------------------------------------------------
    print("\n[14] 0〜15 週を続けて回す (古い 〆過ぎだけでは送らない・1 回の停止につき 2 週・点検 sending-F1 / correct-F2)")
    ex(mod, "UPDATE students SET status = 'canceled' WHERE status <> 'canceled'")
    mod._weekly_report_window = lambda now_jst=None: (datetime.datetime.now(UTC) - datetime.timedelta(days=3), None)

    def shift_week():
        """DB の時刻を全部 7 日前へ (= 1 週間たった)。"""
        for tbl, cols in (("notifications", ("sent_at",)), ("question_attempts", ("created_at",)),
                          ("grammar_drill_assignments", ("assigned_at", "completed_at")), ("grammar_drills", ("created_at",)),
                          ("homework_assignments", ("created_at", "completed_at")), ("events", ("created_at",)),
                          ("students", ("last_login_at",))):
            for col in cols:
                ex(mod, f"UPDATE {tbl} SET {col} = datetime({col}, '-7 days') WHERE {col} IS NOT NULL AND {col} <> ''")
        ex(mod, "UPDATE homework_assignments SET due_date = date(due_date, '-7 days') WHERE due_date IS NOT NULL AND due_date <> ''")

    def simulate(env_value, tag):
        if env_value is None:
            os.environ.pop("WEEKLY_REPORT_HOMEWORK_ZERO_WEEK", None)
        else:
            os.environ["WEEKLY_REPORT_HOMEWORK_ZERO_WEEK"] = env_value
        n0 = datetime.datetime.now(UTC)
        t0 = n0.astimezone(JST).date()
        sim = {}
        for key in ("stale_never", "stale_stopped", "stream", "one_new", "stream_practice", "stream_oldest_done"):
            sim[key] = fx.student(f"Sim {tag} {key}", email=f"sim-{tag}-{key.replace('_', '-')}@example.org")
        for key in ("stale_never", "stale_stopped"):
            fx.homework(sim[key], "ずっと前の宿題", created_at=u(n0 - datetime.timedelta(days=210)),
                        due=(t0 - datetime.timedelta(days=200)).isoformat(), topic="架空の単元")
        fx.attempt(sim["stale_stopped"], n0 - datetime.timedelta(days=8))   # 8 日前まで演習 (前からの対象)

        def new_hw(sid):
            nn = datetime.datetime.now(UTC)
            fx.homework(sid, "毎週の宿題", created_at=u(nn - datetime.timedelta(days=1)),
                        due=(nn.astimezone(JST).date() + datetime.timedelta(days=2)).isoformat(), topic="架空の単元")
        weeks = {k: [] for k in sim}
        for wk in range(16):
            for key in ("stream", "stream_practice", "stream_oldest_done"):
                if key == "stream_oldest_done" and wk == 7:
                    # 7 週目: 残っていた宿題を全部出した (✓完了 = 演習の記録にはならない) → 起点が進む
                    ex(mod, "UPDATE homework_assignments SET status = 'completed', completed_at = ? WHERE student_id = ? "
                            "AND status <> 'completed'", (u(datetime.datetime.now(UTC) - datetime.timedelta(hours=1)), sim[key]))
                new_hw(sim[key])
            if wk == 0:
                new_hw(sim["one_new"])
            if wk == 8:
                fx.attempt(sim["stream_practice"], datetime.datetime.now(UTC) - datetime.timedelta(hours=1))   # 8 週目に演習した
            run_at = u(datetime.datetime.now(UTC) - datetime.timedelta(seconds=5))
            st_, j_ = run()
            if st_ != 200:
                weeks.setdefault("_errors", []).append((wk, st_, str(j_)[:200]))
            got = {r_["student_id"] for r_ in q(mod, "SELECT DISTINCT student_id FROM notifications WHERE success = 1 AND template IN "
                                                      "('weekly_report_zero_week', 'weekly_report_zero_week_parent') AND sent_at >= ?",
                                                  (run_at,))}
            for key, sid in sim.items():
                if sid in got:
                    weeks[key].append(wk)
            shift_week()
        ex(mod, f"UPDATE students SET status = 'canceled' WHERE id IN ({','.join(str(x) for x in sim.values())})")
        os.environ.pop("WEEKLY_REPORT_HOMEWORK_ZERO_WEEK", None)
        return weeks

    on = simulate(None, "on")
    check("env 既定 (ON): 16 回とも 200", "_errors" not in on, on.get("_errors"))
    check("ON: 演習の記録なし・古い 〆過ぎだけ → 一度も送らない (前は 0・1・5・6・10・11・15 週)", on["stale_never"] == [], on)
    check("ON: 8 日前まで演習・古い 〆過ぎ → 0・1 週だけ (前からの 2 週・その後は休眠 = 古い 〆過ぎでは送らない)",
          on["stale_stopped"] == [0, 1], on)
    check("ON: 記録なし・新しい宿題が毎週届いて未提出 → 0・1 週だけ (1 回の停止につき 2 週・29 日ごとに数え直さない)",
          on["stream"] == [0, 1], on)
    check("ON: 記録なし・新しい宿題 1 本 → 0・1 週だけ", on["one_new"] == [0, 1], on)
    check("ON: 8 週目に演習すると数え直す → 0・1・9・10 週 (演習の後の 2 週・その後は止まる)", on["stream_practice"] == [0, 1, 9, 10], on)
    check("ON: 7 週目に残りを全部出すと (いちばん古い未提出が進む) 数え直す → 0・1・7・8 週", on["stream_oldest_done"] == [0, 1, 7, 8], on)
    check("ON: どの生徒も 29 日 (5 週の窓) に 3 週以上は送らない",
          all(sum(1 for w in ws if a <= w < a + 5) <= 2 for k, ws in on.items() if k != "_errors" for a in range(16)), on)
    off = simulate("0", "off")
    check("env OFF: 従来どおり (記録なしの生徒には送らない・8 日前まで演習なら 0・1 週・演習の後の 2 週)",
          "_errors" not in off and off["stale_never"] == [] and off["stream"] == [] and off["one_new"] == []
          and off["stream_oldest_done"] == [] and off["stale_stopped"] == [0, 1] and off["stream_practice"] == [9, 10], off)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for f_ in FAILURES:
            print(f"   - {f_}")
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
