#!/usr/bin/env python3
"""🎯 3日ドリル (自動の弱点配信の本線) の回帰テスト (2026-10-15 塾長決定「自動で配るのはレビュー済みの科目別ドリルだけ」
「中学生と高校生は問題の配信はミスらないように」)。

固定する性質 (一時 SQLite・外部通信なし・生徒名とメールは架空 = 公開リポジトリ):
  [1] ON/OFF と監視: WEAKNESS_DRILL_ROUTINE_ENABLED は 1/true/yes/on だけ ON・既定 OFF。ON で import したときだけ
      _SCHEDULER_MAX_AGE_DAYS に weakness_drill_routine_run (2 日)。停止・失敗の通知の名前の表 2 つと prod_status にラベル。
      prod_healthcheck は実行履歴が無いうちは PASS (未有効化)。スケジューラは要約 (_compact_run_props) を記録する
  [2] レビュー済みだけ: 出典が pool / english の chu2grammar / weakness_v1 / pt- の行は 30 回選んでも 1 問も出ない。
      'english=*' にしても習熟度テスト (pt-) は出ない。高校の物理だけが弱点の生徒は配らない (no_reviewed_pool:physics)。
      未レビューの行しか無い単元は skipped_no_reviewed_inventory
  [3] 中高の取り違えなし: 「中２」→ 中学英語 (基礎+標準)・「中三」→ 中学数学 (標準+やや難)・高校生の 'chugaku' の弱点は band_mismatch・
      中学生の english の弱点は出さない・前置きつきの写しは出さない・小学生と判定できない学年は出さない (env で判定できない学年だけ高校生)。
      200 通りの弱点 × 2 区分のどれでも区分をまたがない。書き込み直前のガードは区分違いを書かずに数え、通常の実行では 0 回
  [4] 英語の単元: 「関係代名詞」は 関係詞 (旧ルーティンの「名詞・代名詞」の取り違えの回帰)
  [5] 生徒ごとの既出の除外: 塾長が配ったドリルの問題・単元ドリルの解答は出さない / 足りなければ最後に見たのが古い問題から足す /
      在庫が 10 問に満たなければ配らない / 入試道場の解答 (id の空間が違う) では除外しない
  [6] dry-run は本番と同じ: 同じ seed なら dry-run と本番で同じ生徒・科目・単元・レベル・問題。dry-run は何も書かない。
      在庫が無い弱点は dry-run でも「配る」に数えない。上限 (CAP) の数え方も同じ。API の応答 (plan_version 2・許可リスト・名前は include_names だけ)
  [7] AI の振り分け (D5): AIあり・AI 体験中は対象・体験が切れた/読めない AIなし枠は対象外・全員がちょうど 1 経路。
      ai_trial_until の列が無い環境でも落ちない。開始月 (start_month) は見ない
  [8] 監視と競合: 全員の作成に失敗した実行は props.error (監視 _failed_schedulers が拾う)。要約は 60 名でも 4000 字未満の正しい JSON で
      名前を含まない。計画と書き込みの間に別の実行が配った生徒は skipped_race (2 本目を作らない)
  [9] LINE は 1 回も送らない・既定ではメールも送らない (自動配信は source='auto')

実行:
    python3 scripts/health_check/test_weakness_routine_auto_delivery.py
    # exit 0 = PASS / 1 = FAIL
"""
import datetime
import importlib.util
import json
import os
import random
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "server"))
from test_grammar_import_units import admin_token, import_like_ceo, load_seed, Api  # noqa: E402

FAILURES = []
ROUTINE = "weakness_routine_3d"
ENV_KEYS = ("WEAKNESS_DRILL_ROUTINE_ENABLED", "WEAKNESS_ROUTINE_UNKNOWN_GRADE_AS_KOSEI", "AUTO_DELIVERY_REVIEWED_SOURCES",
            "HOMEWORK_NOTIFY_EMAIL", "HOMEWORK_NOTIFY_LINE", "WEAKNESS_DRILL_ROUTINE_CAP", "WEEKLY_WORKSHEET_ENABLED")
SEEDS = (("grammar_drill_pool_v1.json", "english"), ("chugaku_drill_pool_v1.json", "chugaku"),
         ("chugaku_math_pool_v1.json", "chugaku_math"), ("math_drill_ct_mock_v1.json", "math"))


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def _base_env(tmpdb):
    return {
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと **本番 Postgres** に書き込む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "",
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
        "BASE_URL": "https://example.invalid",
        "CRON_SECRET": "test-cron-secret",
    }


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="routine_auto_"), "test.db")
    os.environ.update(_base_env(tmpdb))
    for k in ENV_KEYS:
        os.environ.pop(k, None)
    spec = importlib.util.spec_from_file_location("aijuku_main_routine_auto", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


class Env:
    """env を一時的に差し替える (None = 未設定)。"""

    def __init__(self, **kv):
        self.kv = kv

    def __enter__(self):
        self.old = {k: os.environ.get(k) for k in self.kv}
        for k, v in self.kv.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return self

    def __exit__(self, *a):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _scheduler_keys_in_subprocess(value):
    """WEAKNESS_DRILL_ROUTINE_ENABLED=value で main.py を別プロセスで import し、_SCHEDULER_MAX_AGE_DAYS を返す (import 時に評価される)。"""
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="routine_auto_sub_"), "test.db")
    env = dict(os.environ)
    env.update(_base_env(tmpdb))
    env.pop("WEAKNESS_DRILL_ROUTINE_ENABLED", None)
    if value is not None:
        env["WEAKNESS_DRILL_ROUTINE_ENABLED"] = value
    code = (
        "import importlib.util, json, sys\n"
        f"spec = importlib.util.spec_from_file_location('aijuku_main_routine_sub', {MAIN_PY!r})\n"
        "mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)\n"
        "print('KEYS=' + json.dumps(mod._SCHEDULER_MAX_AGE_DAYS))\n"
    )
    r = subprocess.run([sys.executable, "-c", code], env=env, cwd=os.path.join(REPO, "server"),
                       capture_output=True, text=True, timeout=300)
    for line in (r.stdout or "").splitlines():
        if line.startswith("KEYS="):
            return json.loads(line[len("KEYS="):])
    raise RuntimeError(f"subprocess failed rc={r.returncode}: {(r.stderr or '')[-800:]}")


class Recorder:
    """LINE / メール / sleep を記録する偽物 (テストの最初から最後まで差し替える)。"""

    def __init__(self, mod):
        self.mod = mod
        self.lines, self.mails = [], []
        mod._do_line_push = lambda sid, template, params=None: (self.lines.append((sid, template)), {"ok": True})[1]
        mod._send_message_email = lambda to, subject, body, student_name=None: (self.mails.append(to), {"sent": True})[1]
        time.sleep = lambda s: None


def q(mod, sql, params=()):
    conn = mod.db(); c = conn.cursor()
    c.execute(sql, params)
    out = [dict(r) for r in c.fetchall()]
    conn.close()
    return out


def ex(mod, sql, params=()):
    conn = mod.db(); c = conn.cursor()
    c.execute(sql, params)
    conn.commit(); conn.close()


def counts(mod):
    return {t: q(mod, f"SELECT COUNT(*) AS n FROM {t}")[0]["n"]
            for t in ("grammar_drills", "grammar_drill_assignments", "events", "worksheet_archives", "notifications")}


def main():
    print("🎯 3日ドリル (レビュー済みだけ・中高の取り違えなし・既出の除外・dry-run の一致) 回帰テスト\n")
    mod = load_main()
    rec = Recorder(mod)
    src = open(MAIN_PY, encoding="utf-8").read()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app, raise_server_exceptions=False)
    api = Api(mod, client, {"Authorization": "Bearer " + admin_token(mod)})
    cron = {"X-Cron-Secret": "test-cron-secret"}
    for fname, subj in SEEDS:
        d = load_seed(fname)
        t = import_like_ceo(api, "questions", d["questions"] if isinstance(d, dict) else d, subj, 400)
        check(f"シード {fname} が入る", t["inserted"] > 0 and t["errors"] == 0, str(t)[:200])

    now = datetime.datetime.now(datetime.timezone.utc)
    future = mod._utc_naive_iso(now + datetime.timedelta(days=5))
    past = mod._utc_naive_iso(now - datetime.timedelta(days=1))
    seq = [0]

    def make(grade, *, ai_disabled=0, trial=None, status="paid", name=None):
        seq[0] += 1
        n = name or f"架空 生徒{seq[0]:03d}"
        conn = mod.db(); c = conn.cursor()
        c.execute("INSERT INTO students (name, email, status, grade, ai_disabled, ai_trial_until) VALUES (?, ?, ?, ?, ?, ?) RETURNING id",
                  (n, f"rt-{seq[0]:03d}@example.org", status, grade, ai_disabled, trial))
        sid = c.fetchone()["id"]
        conn.commit(); conn.close()
        return sid

    def weak(sid, subject, topic, acc=0.3, att=10):
        ex(mod, "INSERT INTO student_weakness (student_id, subject, topic, question_count, qa_accuracy, qa_attempts) VALUES (?, ?, ?, ?, ?, ?)",
           (sid, subject, topic, att, acc, att))

    def st_of(sid):
        conn = mod.db(); c = conn.cursor()
        c.execute("SELECT id, name, email, line_user_id, grade, ai_disabled, ai_trial_until FROM students WHERE id = ?", (sid,))
        r = c.fetchone()
        conn.close()
        return r

    def plan(sid, band, seed=None, reasons=None):
        conn = mod.db(); c = conn.cursor()
        p = mod._weakness_routine_plan(c, st_of(sid), band, rng=random.Random(seed) if seed is not None else None,
                                       reasons=reasons if reasons is not None else {})
        conn.close()
        return p

    def only_active(ids):
        """全員の実行 (only_student_id なし) の対象をこの生徒だけにする (ほかは canceled)。"""
        ex(mod, f"UPDATE students SET status = CASE WHEN id IN ({','.join('?' * len(ids))}) THEN 'paid' ELSE 'canceled' END", tuple(ids))

    def reset_routine():
        ex(mod, "DELETE FROM grammar_drill_assignments WHERE drill_id IN (SELECT id FROM grammar_drills WHERE created_by = ?)", (ROUTINE,))
        ex(mod, "DELETE FROM grammar_drills WHERE created_by = ?", (ROUTINE,))

    def sources_of(ids):
        if not ids:
            return []
        return q(mod, f"SELECT id, subject, unit, level, source FROM grammar_questions WHERE id IN ({','.join('?' * len(ids))})", tuple(ids))

    # ------------------------------------------------------------------
    print("\n[1] ON/OFF と監視")
    with Env(WEAKNESS_DRILL_ROUTINE_ENABLED=None):
        check("未設定なら OFF", mod._weakness_drill_routine_env_enabled() is False and mod._weakness_drill_routine_enabled() is False)
    for v in ("1", "true", "YES", " on "):
        with Env(WEAKNESS_DRILL_ROUTINE_ENABLED=v):
            check(f"{v!r} なら ON (スケジューラと監視が同じ関数)", mod._weakness_drill_routine_env_enabled() is True
                  and mod._weakness_drill_routine_enabled() is True)
    for v in ("", "0", "false", "off", "2"):
        with Env(WEAKNESS_DRILL_ROUTINE_ENABLED=v):
            check(f"{v!r} なら OFF", mod._weakness_drill_routine_enabled() is False)
    check("既定 (OFF) で import した監視の dict に weakness_drill_routine_run は無い",
          "weakness_drill_routine_run" not in mod._SCHEDULER_MAX_AGE_DAYS, list(mod._SCHEDULER_MAX_AGE_DAYS))
    try:
        on_keys = _scheduler_keys_in_subprocess("1")
        off_keys = _scheduler_keys_in_subprocess(None)
        check("WEAKNESS_DRILL_ROUTINE_ENABLED=1 で import すると weakness_drill_routine_run が 2 日で入る",
              on_keys.get("weakness_drill_routine_run") == 2, on_keys)
        check("未設定で import すると入らない (別プロセスでも同じ)", "weakness_drill_routine_run" not in off_keys, off_keys)
    except Exception as e:
        check("別プロセスの import", False, e)
    check("停止・失敗の通知の名前の表 2 つにラベルがある",
          src.count('"weakness_drill_routine_run": "弱点ドリル 3日ごと (毎日5時半)"') == 2)
    ps = open(os.path.join(REPO, "scripts", "prod_status.py"), encoding="utf-8").read()
    check("prod_status.py にラベルがある", "'weakness_drill_routine_run':" in ps)
    sched = src[src.index("async def _weakness_drill_routine_scheduler"):][:3000]
    check("スケジューラは要約 (_compact_run_props) を記録する (名前を入れない・4000 字で JSON を壊さない)",
          "props = _compact_run_props(result)" in sched and '_record_scheduler_run("weakness_drill_routine_run", props)' in sched)
    check("スケジューラは毎日 env を見る (OFF の日は何もしない)", "if not _weakness_drill_routine_enabled():" in sched)
    spec = importlib.util.spec_from_file_location("prod_hc_routine", os.path.join(HERE, "prod_healthcheck.py"))
    hc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hc)
    check("prod_healthcheck: weakness_drill_routine_run は OPTIONAL_UNTIL_FIRST_RUN", "weakness_drill_routine_run" in hc.OPTIONAL_UNTIL_FIRST_RUN)

    class _HcCur:
        def execute(self, sql, params=None):
            self.last = sql

        def fetchone(self):
            return (None,)

    hc._table_exists = lambda cur, name: True
    hc.results.clear()
    hc.check_scheduler_live(_HcCur())
    mine = [r for r in hc.results if "weakness_drill_routine_run" in r[2]]
    others = [r for r in hc.results if "weakness_drill_routine_run" not in r[2]]
    check("実行履歴が無いうちは PASS (未有効化)", mine and all(r[1] == hc.PASS for r in mine), mine)
    check("ほかのスケジューラは今までどおり 実行履歴なし = WARN", others and all(r[1] == hc.WARN for r in others), others[:2])

    # ------------------------------------------------------------------
    print("\n[2] レビュー済みの出典だけ")
    legacy = [("english", "時制", "standard", "pool", 100), ("english", "時制", "advanced", "chu2grammar-20260709", 20),
              ("english", "時制", "standard", "weakness_v1", 20), ("english", "時制", "advanced", "pt-x-1", 20),
              ("english", "時制", "standard", "", 10), ("physics", "力学", "standard", "pool", 50)]
    conn = mod.db(); c = conn.cursor()
    for subj, unit, lv, srcname, n in legacy:
        for i in range(n):
            c.execute("INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source, active) "
                      "VALUES (?, ?, ?, ?, ?, 0, '解説', ?, 1)",
                      (subj, unit, lv, f"未レビューの架空の問題 {srcname or 'blank'} {i} (   ).", json.dumps(["a", "b", "c", "d"]), srcname))
    conn.commit(); conn.close()
    k1 = make("高校2年")
    weak(k1, "english", "時制")
    bad_sources = {"pool", "chu2grammar-20260709", "weakness_v1", "pt-x-1", ""}
    picked_src, ok_all = set(), True
    for s in range(30):
        p = plan(k1, "kosei", seed=s)
        if not (p.get("ok") and p["subject"] == "english" and p["unit"] == "時制"):
            ok_all = False
            break
        rows = sources_of(p["qids"])
        picked_src |= {r["source"] for r in rows}
        ok_all = ok_all and len(rows) == 10 and all(mod._auto_delivery_source_ok("english", r["source"]) for r in rows)
    check("30 回選んでも全問がレビュー済み (英文法 時制・10 問)", ok_all, picked_src)
    check("pool / english の chu2grammar / weakness_v1 / pt- / 空の出典は 1 問も出ない", not (picked_src & bad_sources), picked_src)
    with Env(AUTO_DELIVERY_REVIEWED_SOURCES="english=*"):
        star = set()
        for s in range(30):
            p = plan(k1, "kosei", seed=s)
            star |= {r["source"] for r in sources_of(p.get("qids") or [])}
        check("'english=*' にすると古い行も出る (env が効いている)", "pool" in star, star)
        check("'english=*' でも習熟度テスト (pt-) は出ない", not any(x.startswith("pt-") for x in star), star)
    k2 = make("高校3年")
    weak(k2, "physics", "力学", acc=0.1)
    reasons = {}
    p = plan(k2, "kosei", reasons=reasons)
    check("高校の物理だけが弱点 → 配らない (no_reviewed_pool:physics)",
          not p["ok"] and p["reason"] == "no_deliverable_weakness" and reasons.get("no_reviewed_pool:physics") == 1, (p, reasons))
    res = mod._run_weakness_drill_routine(only_student_id=k2, dry_run=True)
    check("dry-run でも 配る 0・skipped_no_weakness 1", res["delivered"] == 0 and res["skipped_no_weakness"] == 1, res)
    k3 = make("高校1年")
    weak(k3, "english", "話法")
    ex(mod, "UPDATE grammar_questions SET active = 0 WHERE subject = 'english' AND unit = '話法'")
    for i in range(30):
        ex(mod, "INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) VALUES "
                "('english', '話法', 'standard', ?, ?, 0, '解説', 'pool')", (f"古い話法の架空の問題 {i} (   ).", json.dumps(["a", "b", "c", "d"])))
    res = mod._run_weakness_drill_routine(only_student_id=k3, dry_run=True)
    check("未レビューの行しか無い単元 → skipped_no_reviewed_inventory (dry-run でも配るに数えない)",
          res["delivered"] == 0 and res["skipped_no_reviewed_inventory"] == 1 and res["eligible"] == 0, res)

    # ------------------------------------------------------------------
    print("\n[3] 中学生と高校生を取り違えない")
    k4 = make("高校2年")
    weak(k4, "chugaku", "関係代名詞", acc=0.1)
    reasons = {}
    p = plan(k4, "kosei", reasons=reasons)
    check("高校生の 'chugaku' (高校入試演習) の弱点 → 配らない (band_mismatch:chugaku)",
          not p["ok"] and reasons.get("band_mismatch:chugaku") == 1, (p, reasons))
    c1 = make("中２")
    weak(c1, "chugaku", "関係代名詞")
    check("「中２」(全角) は中学生", mod._student_grade_band("中２") == "chugaku")
    p = plan(c1, "chugaku", seed=1)
    rows = sources_of(p.get("qids") or [])
    check("「中２」の 関係代名詞 → 中学英語 chugaku / 関係代名詞・基礎+標準・10 問",
          p.get("ok") and p["subject"] == "chugaku" and p["unit"] == "関係代名詞" and p["levels"] == ["basic", "standard"]
          and len(rows) == 10 and all(r["subject"] == "chugaku" and r["unit"] == "関係代名詞" and r["level"] in ("basic", "standard")
                                      and mod._auto_delivery_source_ok("chugaku", r["source"]) for r in rows), (p, rows[:2]))
    check("題名用のラベルは「中学英語 関係代名詞」", p.get("label") == "中学英語 関係代名詞", p.get("label"))
    c2 = make("中三")
    weak(c2, "chugaku", "正負の数（累乗）")
    p = plan(c2, "chugaku", seed=2)
    rows = sources_of(p.get("qids") or [])
    check("「中三」の 正負の数（累乗） → 中学数学 chugaku_math / 正負の数・標準+やや難",
          p.get("ok") and p["subject"] == "chugaku_math" and p["unit"] == "正負の数" and p["levels"] == ["standard", "advanced"]
          and len(rows) == 10 and all(r["subject"] == "chugaku_math" and r["level"] in ("standard", "advanced") for r in rows), p)
    c3 = make("中学1年")
    weak(c3, "chugaku", "中学数学 正負の数")
    reasons = {}
    p = plan(c3, "chugaku", reasons=reasons)
    check("前置きつきの写し (中学数学 正負の数) だけ → 配らない (chugaku_prefixed_copy)",
          not p["ok"] and reasons.get("chugaku_prefixed_copy") == 1, (p, reasons))
    c4 = make("中1")
    weak(c4, "english", "時制", acc=0.1)
    reasons = {}
    p = plan(c4, "chugaku", reasons=reasons)
    check("中学生の english (高校のプール) の弱点 → 配らない (band_mismatch:english)",
          not p["ok"] and reasons.get("band_mismatch:english") == 1, (p, reasons))
    c5 = make("中学生")
    weak(c5, "chugaku", "関係代名詞")
    p = plan(c5, "chugaku", seed=3)
    check("学年の数字が読めない中学生 (「中学生」) は 基礎+標準", p.get("ok") and p["levels"] == ["basic", "standard"], p)
    s1 = make("小６")
    weak(s1, "chugaku", "関係代名詞")
    u1 = make("その他")
    weak(u1, "english", "時制")
    u2 = make("")
    weak(u2, "english", "時制")
    reset_routine()
    only_active([k4, c1, c2, c3, c4, c5, s1, u1, u2])
    res = mod._run_weakness_drill_routine(dry_run=True, seed=11)
    by_id = {e["id"]: e for e in res["delivered_students"]}
    check("全員の dry-run: 配るのは 中２・中三・中学生 の 3 名", set(by_id) == {c1, c2, c5}, sorted(by_id))
    check("band=chugaku の生徒には chugaku* だけ", all(e["band"] == "chugaku" and e["subject"].startswith("chugaku") for e in by_id.values()),
          list(by_id.values())[:2])
    check("「小６」は skipped_shougaku", res["skipped_shougaku"] == 1, res)
    check("「その他」と空の学年は skipped_grade_unknown (一覧に id)",
          res["skipped_grade_unknown"] == 2 and {e["id"] for e in res["grade_unknown_students"]} == {u1, u2}, res)
    check("名前は include_names のときだけ", all("name" not in e for e in res["delivered_students"] + res["grade_unknown_students"]))
    check("band_counts", res["band_counts"].get("chugaku") == 5 and res["band_counts"].get("kosei") == 1
          and res["band_counts"].get("shougaku") == 1 and res["band_counts"].get("unknown") == 2, res["band_counts"])
    with Env(WEAKNESS_ROUTINE_UNKNOWN_GRADE_AS_KOSEI="1"):
        res = mod._run_weakness_drill_routine(dry_run=True, seed=11)
        by_id = {e["id"]: e for e in res["delivered_students"]}
        check("WEAKNESS_ROUTINE_UNKNOWN_GRADE_AS_KOSEI=1: 判定できない学年は高校生として english",
              by_id.get(u1, {}).get("band") == "kosei" and by_id.get(u2, {}).get("subject") == "english"
              and res["skipped_grade_unknown"] == 0, res)

    print("  (200 通りの弱点 × 高校生・中学生で区分をまたがない)")
    chu_topics = []
    for s_ in mod._CHU_DRILL_SUBJECTS:
        for u in mod._GRAMMAR_SUBJECT_UNIT_ORDER.get(s_, ()):
            chu_topics.append(("chugaku", u))
            chu_topics.append(("chugaku", f"{mod._GRAMMAR_SUBJECT_LABEL_JA[s_]} {u}"))
            chu_topics.append(("chugaku", f"{u}（応用）"))
    pool = ([("english", u) for u in mod.GRAMMAR_UNITS] + [("english", t) for t in ("関係代名詞", "時制の一致", "長文読解", "語彙", "間接疑問文")]
            + [("math", t) for t in ("基礎数学 二次関数", "数学III 微分法", "数学A 確率")]
            + [("physics", "力学"), ("japanese", "古文 助動詞"), ("social", "世界史"), ("eiken", "2級 単語"), ("chemistry", "酸と塩基")]
            + chu_topics + [("chugaku_math", "一次関数"), ("数学", "二次関数"), ("英語", "関係代名詞")])
    rnd = random.Random(20261015)
    fk, fc = make("高校2年"), make("中学2年")
    allowed = {"kosei": set(mod._ROUTINE_SUBJECTS_BY_BAND["kosei"]), "chugaku": set(mod._CHU_DRILL_SUBJECTS)}
    trips0 = mod._ROUTINE_BAND_GUARD_TRIPS
    crossed, delivered_any = [], {"kosei": 0, "chugaku": 0}
    for band, sid in (("kosei", fk), ("chugaku", fc)):
        for it in range(200):
            ex(mod, "DELETE FROM student_weakness WHERE student_id = ?", (sid,))
            for subj, topic in rnd.sample(pool, rnd.randint(1, 8)):
                weak(sid, subj, topic, acc=round(rnd.random() * 0.79, 2), att=rnd.randint(1, 20))
            conn = mod.db(); c = conn.cursor()
            picks = mod._weakness_routine_pick_drills(c, sid, band=band)
            conn.close()
            bad = [p_ for p_ in picks if p_["subject"] not in allowed[band] or not mod._drill_subject_band_ok(p_["subject"], band)]
            if bad:
                crossed.append((band, it, bad))
            if it % 10 == 0:
                p = plan(sid, band, seed=it)
                if p.get("ok"):
                    delivered_any[band] += 1
                    rows = sources_of(p["qids"])
                    if any(r["subject"] != p["subject"] for r in rows) or p["subject"] not in allowed[band]:
                        crossed.append((band, it, "plan", p["subject"]))
    check("200 通り × 2 区分: 高校生に chugaku* なし・中学生に english/math/eiken なし", not crossed, crossed[:3])
    check("(この fuzz が意味を持つ: どちらの区分でも配れる計画がある)", delivered_any["kosei"] > 0 and delivered_any["chugaku"] > 0, delivered_any)
    check("選ぶ側が正しければ書き込み直前のガードは 0 回", mod._ROUTINE_BAND_GUARD_TRIPS == trips0, mod._ROUTINE_BAND_GUARD_TRIPS)

    print("  (書き込み直前の学年ガード)")
    before = counts(mod)
    conn = mod.db(); c = conn.cursor()
    r1 = mod._create_routine_grammar_drill(c, conn, "chugaku", "関係代名詞", 10, k1, st_of(k1), band="kosei")
    r2 = mod._create_routine_grammar_drill(c, conn, "english", "時制", 10, c1, st_of(c1), band="chugaku")
    r3 = mod._create_routine_grammar_drill(c, conn, "physics", "", 10, k1, st_of(k1), band="kosei")
    r4 = mod._create_routine_grammar_drill(c, conn, "english", "時制", 10, u1, st_of(u1), band="")
    conn.close()
    check("区分違い (高校生に中学英語・中学生に英文法・3日ドリルで出さない科目・判定できない学年) は None", [r1, r2, r3, r4] == [None] * 4,
          [r1, r2, r3, r4])
    check("1 行も書かない", counts(mod) == before, (before, counts(mod)))
    check("_ROUTINE_BAND_GUARD_TRIPS が 4 増える", mod._ROUTINE_BAND_GUARD_TRIPS == trips0 + 4, mod._ROUTINE_BAND_GUARD_TRIPS)
    trips1 = mod._ROUTINE_BAND_GUARD_TRIPS
    reset_routine()
    only_active([k1, c1, c2, c5])
    res = mod._run_weakness_drill_routine(seed=5)
    check("通常の本番の実行: 4 名に配り、ガードは 0 回 (band_guard_trips 0・error なし)",
          res["delivered"] == 4 and res["band_guard_trips"] == 0 and "error" not in res
          and mod._ROUTINE_BAND_GUARD_TRIPS == trips1, res)
    drills = q(mod, "SELECT d.subject, d.question_ids, d.title, a.student_id FROM grammar_drills d JOIN grammar_drill_assignments a "
                    "ON a.drill_id = d.id WHERE d.created_by = ?", (ROUTINE,))
    mism = []
    for d in drills:
        ids = json.loads(d["question_ids"])
        for r in sources_of(ids):
            if r["subject"] != d["subject"]:
                mism.append((d["student_id"], d["subject"], r["subject"]))
    check("書いたドリルの全問の科目がドリルの科目と同じ", drills and not mism, mism[:3])
    t_chu = [d["title"] for d in drills if d["student_id"] == c1]
    check("中学生の題名に教科名が入る (🎯弱点対策 中学英語 関係代名詞ドリル)", t_chu and t_chu[0].startswith("🎯弱点対策 中学英語 関係代名詞ドリル（基礎・標準・10問）"),
          t_chu)
    res2 = mod._run_weakness_drill_routine(seed=5)
    check("同じ日にもう一度回しても積まない (未提出 = skipped_open)", res2["delivered"] == 0 and res2["skipped_open"] == 4, res2)
    ex(mod, "UPDATE grammar_drill_assignments SET status = 'assigned' WHERE drill_id IN (SELECT id FROM grammar_drills WHERE created_by = ?)", (ROUTINE,))
    res3 = mod._run_weakness_drill_routine(seed=5)
    check("status='assigned' (デスクトップの予約タスクの書き方) も未提出として数える", res3["skipped_open"] == 4 and res3["delivered"] == 0, res3)
    ex(mod, "UPDATE grammar_drill_assignments SET status = 'completed' WHERE drill_id IN (SELECT id FROM grammar_drills WHERE created_by = ?)", (ROUTINE,))
    res4 = mod._run_weakness_drill_routine(seed=5)
    check("提出済みでも 3 日以内なら配らない (skipped_recent)", res4["skipped_recent"] == 4 and res4["delivered"] == 0, res4)

    # ------------------------------------------------------------------
    print("\n[4] 英語の弱点 → 文法の単元")
    k5 = make("高校3年")
    weak(k5, "english", "関係代名詞")
    p = plan(k5, "kosei", seed=4)
    check("「関係代名詞」→ 関係詞 (「名詞・代名詞」にしない)", p.get("ok") and p["unit"] == "関係詞", p)

    # ------------------------------------------------------------------
    print("\n[5] 生徒ごとの既出の除外")
    n1 = make("高校1年")
    weak(n1, "english", "時制")
    rev = [r["id"] for r in q(mod, "SELECT id, source FROM grammar_questions WHERE subject = 'english' AND unit = '時制' "
                                   "AND level IN ('standard', 'advanced') AND active = 1 ORDER BY id")
           if mod._auto_delivery_source_ok("english", r["source"])]
    check("レビュー済みの 時制 (標準+やや難) が 26 問 (このテストの前提)", len(rev) == 26, len(rev))
    A, B, rest = rev[:10], rev[10:16], rev[16:]
    ex(mod, "INSERT INTO grammar_drills (subject, title, unit, level, question_ids, created_by) VALUES ('english', '塾長の配信', '時制', "
            "'standard', ?, 'admin')", (json.dumps(A),))
    did = q(mod, "SELECT MAX(id) AS id FROM grammar_drills")[0]["id"]
    ex(mod, "INSERT INTO grammar_drill_assignments (drill_id, student_id, status, assigned_at) VALUES (?, ?, 'completed', '2026-01-01 00:00:00')",
       (did, n1))
    for qid in B:
        ex(mod, "INSERT INTO question_attempts (student_id, source, exam_question_id, subject, topic, is_correct, created_at) "
                "VALUES (?, 'grammar_drill', ?, 'english', '時制', 0, '2026-05-01 00:00:00')", (n1, qid))
    for qid in rest:   # 入試道場の解答 (exam_questions の id。同じ数字でも別の問題)
        ex(mod, "INSERT INTO question_attempts (student_id, source, exam_question_id, subject, topic, is_correct) "
                "VALUES (?, 'dojo_drill', ?, 'english', '時制', 0)", (n1, qid))
    ok = True
    for s in range(10):
        p = plan(n1, "kosei", seed=s)
        ok = ok and p.get("ok") and set(p["qids"]) == set(rest) and p["reused_seen"] == 0
    check("塾長が配った問題・単元ドリルで解いた問題を避け、残りの 10 問 (入試道場の解答の id では除外しない)", ok, p)
    keep = rest[:5] + A[:5] + B[:5]   # 未出 5・古い既出 5 (A=1 月)・新しい既出 5 (B=5 月)
    ex(mod, f"UPDATE grammar_questions SET active = 0 WHERE id IN ({','.join('?' * len(rev))}) AND id NOT IN ({','.join('?' * len(keep))})",
       tuple(rev) + tuple(keep))
    p = plan(n1, "kosei", seed=9)
    check("在庫 15 問・既出 10 問 → 未出 5 + 最後に見たのが古い既出 5 (reused_seen 5)",
          p.get("ok") and set(p["qids"]) == set(rest[:5] + A[:5]) and p["reused_seen"] == 5 and p["unseen_available"] == 5, p)
    ex(mod, f"UPDATE grammar_questions SET active = 0 WHERE id IN ({','.join('?' * 7)})", tuple(keep[:7]))
    p = plan(n1, "kosei", seed=9)
    check("在庫 8 問 → 配らない (no_reviewed_inventory)", not p["ok"] and p["reason"] == "no_reviewed_inventory", p)
    ex(mod, f"UPDATE grammar_questions SET active = 1 WHERE id IN ({','.join('?' * len(rev))})", tuple(rev))

    # ------------------------------------------------------------------
    print("\n[6] dry-run は本番と同じ選び方")
    x1 = make("中学3年")
    weak(x1, "chugaku", "天体：月")      # 中学理科 天体 (このテストでは理科のシードを入れていない = 在庫なし)
    reset_routine()
    group = [k1, c1, c2, k5, x1]
    only_active(group)
    before = counts(mod)
    dry = mod._run_weakness_drill_routine(dry_run=True, seed=42)
    check("dry-run は何も書かない (ドリル・割当・events・プリント・お知らせ)", counts(mod) == before, (before, counts(mod)))
    check("在庫の無い弱点 (中学理科 天体) は dry-run でも配るに数えない (skipped_no_reviewed_inventory)",
          dry["skipped_no_reviewed_inventory"] == 1 and x1 not in {e["id"] for e in dry["delivered_students"]}, dry)
    real = mod._run_weakness_drill_routine(dry_run=False, seed=42)

    def sig(res):
        return sorted((e["id"], e["subject"], e["unit"], tuple(e["levels"]), tuple(e["qids"])) for e in res["delivered_students"])

    check("同じ seed なら dry-run と本番で 生徒・科目・単元・レベル・問題 が同じ", sig(dry) == sig(real) and len(sig(real)) == 4,
          (sig(dry)[:1], sig(real)[:1]))
    stored = {r["student_id"]: (r["subject"], json.loads(r["question_ids"])) for r in
              q(mod, "SELECT d.subject, d.question_ids, a.student_id FROM grammar_drills d JOIN grammar_drill_assignments a ON a.drill_id = d.id "
                     "WHERE d.created_by = ?", (ROUTINE,))}
    check("DB に書いた問題 = 応答の qids", all(stored.get(e["id"]) == (e["subject"], e["qids"]) for e in real["delivered_students"]), stored)
    reset_routine()
    with Env(WEAKNESS_DRILL_ROUTINE_CAP="1"):
        d1 = mod._run_weakness_drill_routine(dry_run=True, seed=42)
        r1_ = mod._run_weakness_drill_routine(dry_run=False, seed=42)
        check("上限 1: dry-run も本番も 配る 1・capped 3 (eligible 4)",
              (d1["delivered"], d1["capped"], d1["eligible"]) == (1, 3, 4) == (r1_["delivered"], r1_["capped"], r1_["eligible"]), (d1, r1_))
    reset_routine()
    r = client.post("/api/admin/weakness-drill-routine/run", json={})
    check("認証なし → 401", r.status_code == 401, r.status_code)
    r = client.post("/api/admin/weakness-drill-routine/run", json={"seed": 42}, headers=cron)
    j = r.json() if r.status_code == 200 else {}
    check("既定は dry_run (書かない)", r.status_code == 200 and j.get("dry_run") is True and counts(mod)["grammar_drills"] == before["grammar_drills"], j)
    check("応答に plan_version 2・enabled_env・weekly_worksheet_enabled・許可リスト・禁止",
          j.get("plan_version") == 2 and j.get("enabled_env") is False and j.get("weekly_worksheet_enabled") is False
          and j.get("allowlist", {}).get("english") == ["manual-drill-v1", "manual-drill-v2"]
          and j.get("deny", {}).get("subjects") == ["proficiency_test"] and "pt-" in j.get("deny", {}).get("source_prefixes", []), j)
    check("API の dry-run も同じ seed なら同じ計画", sig(j) == sig(dry) if j else False)
    check("名前は既定で返さない", all("name" not in e for e in j.get("delivered_students", [])))
    j2 = client.post("/api/admin/weakness-drill-routine/run", json={"seed": 42, "include_names": True}, headers=cron).json()
    check("include_names: true のときだけ名前 (CEO の確認カード)", j2.get("delivered_students") and all(e.get("name", "").startswith("架空")
                                                                                     for e in j2["delivered_students"]), j2.get("delivered_students"))
    ex(mod, "UPDATE students SET grade = '中２' WHERE id = ?", (c1,))
    j3 = client.post("/api/admin/weakness-drill-routine/run", json={"dry_run": True}, headers=cron).json()
    mc = {e["id"]: e for e in j3.get("mode_changed_by_normalization", [])}
    check("dry-run の mode_changed_by_normalization: 「中２」は 旧 kosei → 新 chugaku (画面のモードが変わる生徒)",
          mc.get(c1, {}).get("old") == "kosei" and mc.get(c1, {}).get("new") == "chugaku" and c2 in mc and k1 not in mc,
          j3.get("mode_changed_by_normalization"))

    # ------------------------------------------------------------------
    print("\n[7] AI の振り分け (AIあり・AI 体験中だけ・1 人 1 経路)")
    a0 = make("高校2年", ai_disabled=0)
    tf = make("高校2年", ai_disabled=1, trial=future)
    tp = make("高校2年", ai_disabled=1, trial=past)
    nn = make("高校2年", ai_disabled=1, trial=None)
    tg = make("高校2年", ai_disabled=1, trial="not-a-date")
    ap = make("高校2年", ai_disabled=0, trial=past)
    fixture = [a0, tf, tp, nn, tg, ap]
    for sid in fixture:
        weak(sid, "english", "時制")
    only_active(fixture)
    res = mod._run_weakness_drill_routine(dry_run=True, seed=1)
    got = {e["id"] for e in res["delivered_students"]}
    check("AIあり・AI 体験中・体験が切れた AIあり は対象", got == {a0, tf, ap}, sorted(got))
    check("体験が切れた / 期限が読めない AIなし枠は Python で外す (skipped_ai_nashi 2)", res["skipped_ai_nashi"] == 2, res)
    rows = {r["id"]: r for r in q(mod, f"SELECT id, ai_disabled, ai_trial_until FROM students WHERE id IN ({','.join('?' * len(fixture))})",
                                  tuple(fixture))}
    part = [sid for sid in fixture
            if (sid in got) == (mod._auto_delivery_ai_path(rows[sid]["ai_disabled"], rows[sid]["ai_trial_until"]) == "ai_nashi")]
    check("全員がちょうど 1 経路 (3日ドリル か 塾生アプリのみ枠のクラス自動宿題)", not part, part)
    ex(mod, "UPDATE students SET start_month = '2099-01' WHERE id = ?", (a0,))
    res = mod._run_weakness_drill_routine(only_student_id=a0, dry_run=True)
    check("開始月 (start_month) は見ない (AIあり は承認した日から)", res["delivered"] == 1, res)
    orig_has = mod._students_has_ai_trial_until
    mod._students_has_ai_trial_until = lambda: False
    try:
        res = mod._run_weakness_drill_routine(dry_run=True, seed=1)
        got = {e["id"] for e in res["delivered_students"]}
        check("ai_trial_until の列が無い環境でも落ちない (ai_disabled=0 だけ)", got == {a0, ap}, (sorted(got), res.get("error")))
    except Exception as e:
        check("ai_trial_until の列が無い環境でも落ちない", False, f"{type(e).__name__}: {e}")
    finally:
        mod._students_has_ai_trial_until = orig_has

    # ------------------------------------------------------------------
    print("\n[8] 監視と競合")
    reset_routine()
    only_active([k1])
    orig_create = mod._create_routine_grammar_drill
    mod._create_routine_grammar_drill = lambda *a, **k: None
    try:
        res = mod._run_weakness_drill_routine(seed=3)
    finally:
        mod._create_routine_grammar_drill = orig_create
    check("全員の作成に失敗 → props.error・create_failed", res.get("error") and res["create_failed"] == 1 and res["delivered"] == 0, res)
    props = mod._compact_run_props(res)
    mod._record_scheduler_run("weakness_drill_routine_run", props)
    mod._SCHEDULER_MAX_AGE_DAYS["weakness_drill_routine_run"] = 2
    try:
        failed = mod._failed_schedulers(mod._scheduler_status_rows())
    finally:
        mod._SCHEDULER_MAX_AGE_DAYS.pop("weakness_drill_routine_run", None)
    check("監視 (_failed_schedulers) が拾う", any(f["name"] == "weakness_drill_routine_run" for f in failed), failed)
    big = dict(dry)
    big["delivered_students"] = [dict(e, id=10000 + i, name=f"架空 長い名前の生徒 {i}") for i, e in
                                 enumerate((dry["delivered_students"] * 60)[:60])]
    big["grade_unknown_students"] = [{"id": 20000 + i, "grade": "その他", "name": f"架空 学年なし {i}"} for i in range(40)]
    big["reasons"] = {f"no_reviewed_pool:subject_{i}": i for i in range(40)}
    big["error"] = "テスト用のエラー"
    props = mod._compact_run_props(big)
    txt = json.dumps(props, ensure_ascii=False)
    check("要約は 60 名でも 4000 字未満", len(txt) < 4000, len(txt))
    check("要約は正しい JSON で名前を含まない・error は残る", json.loads(txt) == props and "架空" not in txt and props.get("error"), txt[:300])
    check("要約に配った人数と id (30 件まで)", props.get("delivered_students_n") == 60 and len(props.get("delivered_students_ids", [])) <= 30, props)

    reset_routine()
    only_active([k1])
    orig_plan = mod._weakness_routine_plan

    def racing_plan(c, st, band, **kw):
        p = orig_plan(c, st, band, **kw)
        conn2 = mod.db(); c2 = conn2.cursor()      # 計画と書き込みの間に、別のレプリカが同じ生徒に配った
        c2.execute("INSERT INTO grammar_drills (subject, title, unit, level, question_ids, created_by) VALUES "
                   "('english', '別の実行', '時制', 'standard', '[]', ?) RETURNING id", (ROUTINE,))
        d_ = c2.fetchone()["id"]
        c2.execute("INSERT INTO grammar_drill_assignments (drill_id, student_id, status) VALUES (?, ?, 'open')", (d_, st["id"]))
        conn2.commit(); conn2.close()
        return p

    mod._weakness_routine_plan = racing_plan
    try:
        res = mod._run_weakness_drill_routine(seed=3)
    finally:
        mod._weakness_routine_plan = orig_plan
    n_rt = q(mod, "SELECT COUNT(*) AS n FROM grammar_drill_assignments a JOIN grammar_drills d ON d.id = a.drill_id "
                  "WHERE d.created_by = ? AND a.student_id = ?", (ROUTINE, k1))[0]["n"]
    check("計画と書き込みの間に配られた → skipped_race・2 本目を作らない", res["skipped_race"] == 1 and res["delivered"] == 0 and n_rt == 1,
          (res, n_rt))
    check("競合は error にしない (監視を鳴らさない)", "error" not in res, res.get("error"))
    lock_src = src[src.index("def _create_routine_grammar_drill"):][:6000]
    check("Postgres の錠は 2 引数 (8675313, 生徒ID) を f-string で埋める (psycopg3 の bigint を避ける)",
          "pg_try_advisory_xact_lock({int(_ROUTINE_PG_LOCK_KEY)}, {int(sid)})" in lock_src and "_ROUTINE_PG_LOCK_KEY = 8675313" in src)
    check("錠の中で未提出 (completed 以外)・3 日以内を読み直す", "<> 'completed' OR a.assigned_at >= ?" in lock_src)

    # ------------------------------------------------------------------
    print("\n[9] お知らせ")
    check("テストの間 LINE は 1 回も送っていない", rec.lines == [], rec.lines[:3])
    check("既定 (HOMEWORK_NOTIFY_EMAIL 未設定) ではメールも 0 通 (自動配信は source='auto')", rec.mails == [], rec.mails[:3])
    run_src = src[src.index("def _run_weakness_drill_routine"):][:12000]
    check("3日ドリルのお知らせは source='auto'", 'source="auto"' in run_src and "source=\"manual\"" not in run_src)

    print()
    if FAILURES:
        print(f"❌ FAIL ({len(FAILURES)} 件)")
        for f in FAILURES:
            print("   -", f)
        sys.exit(1)
    print("✅ PASS (3日ドリル: レビュー済みだけ・中高の取り違えなし・既出の除外・dry-run の一致・1 人 1 経路)")


if __name__ == "__main__":
    main()
