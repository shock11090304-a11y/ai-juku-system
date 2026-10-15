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
  [11] 2026-10-16 塾長決定: 3 日は JST の日付で数える (5:30:00 の実行で 3 日前の 5:30:xx の配信が「3 日以内」に残って 4 日ごとに
      なっていた)・積まない判定に数える未提出は直近 WEAKNESS_ROUTINE_OPEN_STALE_DAYS (既定 14・0 = 全部・3〜365 に丸める) 日の分だけ
      (古いドリルは消さず生徒の一覧に残る・stale_open_ignored)・assigned_at が空の未提出は数える・錠の中の読み直しも同じ境目・
      デスクトップの予約タスクの行 (created_by='mission_2day_routine') は数えない = 両方届く
  [12] CEO の 🎯 カードの「前回の自動配信」(2026-10-16 塾長決定): dry-run の応答の last_run = events の最後の実行記録 {at_jst (M/D HH:MM・JST),
      at, delivered, error} / 記録なしは null・いちばん新しい行・壊れた props でも落ちない・DB が読めなければ None・何も書かない・名前なし。
      カード ([10] の JS): 見出しは「今もう一度回したら配る」・その上に「前回の自動配信: M/D HH:MM に N 名」(失敗は ❌ と理由を escape)・
      古い未提出を数えなかった生徒はチップ
  [10] CEO の配信済みドリル一覧 (2026-10-15 塾長決定: 既定は塾長が配ったドリルだけ): kind 無し = owner (今日の1問は出る・自動配信と
      初回診断は出ない) / routine / class_hw (印からクラス名と区分を読む) / auto / all・初回診断はどの kind にも出ない・科目で絞る
      (別名・空の科目 = english も拾う)・知らない kind と科目は 422・自動配信が 60 本増えても既定の 50 本から塾長の配信が押し出されない。
      ceo.html: 絞り込みの帯と 🎯 確認カードの位置・localStorage は try の中・CEO から 3日ドリルを本番で回さない (dry_run: true だけ)・
      確認カードの描画を JS で実行 (名前・学年は escape・plan_version が無ければ「サーバ反映待ち」)

実行:
    python3 scripts/health_check/test_weakness_routine_auto_delivery.py
    # exit 0 = PASS / 1 = FAIL
"""
import datetime
import importlib.util
import json
import os
import random
import re
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
from test_grade_band_consistency import js_engine, run_js  # noqa: E402
CEO_HTML = os.path.join(REPO, "ceo.html")

FAILURES = []
ROUTINE = "weakness_routine_3d"
ENV_KEYS = ("WEAKNESS_DRILL_ROUTINE_ENABLED", "WEAKNESS_ROUTINE_UNKNOWN_GRADE_AS_KOSEI", "AUTO_DELIVERY_REVIEWED_SOURCES",
            "HOMEWORK_NOTIFY_EMAIL", "HOMEWORK_NOTIFY_LINE", "WEAKNESS_DRILL_ROUTINE_CAP", "WEEKLY_WORKSHEET_ENABLED",
            "WEAKNESS_ROUTINE_OPEN_STALE_DAYS")
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
    # ほか = OPTIONAL_UNTIL_FIRST_RUN に無いもの (2026-10-15 からクラス自動宿題 class_hw_auto_run も履歴が無いうちは PASS)
    others = [r for r in hc.results if not any(n_ in r[2] for n_ in hc.OPTIONAL_UNTIL_FIRST_RUN)]
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
    check("3日ドリルの印の行は status='assigned' でも未提出として数える (completed 以外)", res3["skipped_open"] == 4 and res3["delivered"] == 0, res3)
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
    check("錠の中で未提出 (completed 以外・14 日より前は数えない)・JST の日付で 3 日以内を読み直す (一括の判定と同じ境目)",
          "cut = cutoffs or _weakness_routine_cutoffs()" in lock_src and "(a.assigned_at IS NULL OR a.assigned_at >= ?)" in lock_src
          and "OR a.assigned_at >= ?) LIMIT 1" in lock_src and "cutoffs=cut)" in src[src.index("def _run_weakness_drill_routine"):][:16000])

    # ------------------------------------------------------------------
    print("\n[9] お知らせ")
    check("テストの間 LINE は 1 回も送っていない", rec.lines == [], rec.lines[:3])
    check("既定 (HOMEWORK_NOTIFY_EMAIL 未設定) ではメールも 0 通 (自動配信は source='auto')", rec.mails == [], rec.mails[:3])
    run_src = src[src.index("def _run_weakness_drill_routine"):][:12000]
    check("3日ドリルのお知らせは source='auto'", 'source="auto"' in run_src and "source=\"manual\"" not in run_src)

    # ------------------------------------------------------------------
    print("\n[10] CEO の配信済みドリル一覧の絞り込み (kind・subject) と 🎯 確認カード")
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    stamp = [0]

    def mk_drill(created_by, subject="english", unit="時制", when=None):
        stamp[0] += 1
        conn = mod.db(); c = conn.cursor()
        c.execute("INSERT INTO grammar_drills (subject, title, unit, level, question_ids, created_by, created_at) "
                  "VALUES (?, ?, ?, 'standard', '[]', ?, ?) RETURNING id",
                  (subject, f"一覧の絞り込みの架空のドリル {stamp[0]}", unit, created_by,
                   when or f"2030-01-01 00:{stamp[0] // 60:02d}:{stamp[0] % 60:02d}"))
        did_ = c.fetchone()["id"]
        conn.commit(); conn.close()
        return did_

    d_admin = mk_drill("admin", "english")
    d_nullcb = mk_drill(None, "chugaku_math", unit="正負の数")
    d_today = mk_drill("today_question", "english", unit="今日の1問")
    d_diag = mk_drill("diagnostic", None, unit="実力チェック")
    d_rt = mk_drill(ROUTINE, "math", unit="数学")
    d_chw = mk_drill("class_hw_auto:kosei:月曜3限 長文読解 Lv.1", "english")
    d_chw2 = mk_drill("class_hw_auto:chugaku:中学クラス: 架空", "chugaku", unit="関係代名詞")
    d_nosubj = mk_drill("admin", None)          # 科目の列が空の古い行 = 英文法
    d_alias = mk_drill("admin", "英語")          # 別名で入った行
    d_upper = mk_drill("admin", "English")
    d_math = mk_drill("admin", "数学")
    owner_ids = {d_admin, d_nullcb, d_today, d_nosubj, d_alias, d_upper, d_math}
    mine = owner_ids | {d_diag, d_rt, d_chw, d_chw2}

    def lst(**params):
        r = client.get("/api/admin/grammar-drill/list", params=dict({"limit": 200}, **params), headers=adm)
        j = r.json() if r.status_code == 200 else {}
        return r.status_code, j, {it["id"]: it for it in j.get("items", [])}

    r = client.get("/api/admin/grammar-drill/list")
    check("認証なし → 401", r.status_code == 401, r.status_code)
    sc, j, items = lst()
    auto_cb = lambda cb: cb == ROUTINE or str(cb).startswith("class_hw_auto:")  # noqa: E731
    check("kind 無し = owner (応答に kind・subject を返す)", sc == 200 and j.get("kind") == "owner" and j.get("subject") is None, (sc, j.get("kind")))
    check("owner: 塾長の配信・created_by が空の古い行・今日の1問は出る", owner_ids <= set(items), sorted(owner_ids - set(items)))
    check("owner: 3日ドリル・クラス自動宿題・初回診断は 1 本も出ない",
          not ({d_rt, d_chw, d_chw2, d_diag} & set(items))
          and all(not auto_cb(it["created_by"]) and it["created_by"] != "diagnostic" and it["origin"] == "" for it in items.values()),
          [(it["id"], it["created_by"]) for it in items.values() if auto_cb(it["created_by"])][:3])
    check("各行に created_by (空の古い行は admin)", items.get(d_nullcb, {}).get("created_by") == "admin"
          and items.get(d_today, {}).get("created_by") == "today_question", items.get(d_nullcb))
    check("既存の項目 (done/pending/assigned) はそのまま", all(k in items.get(d_admin, {}) for k in ("done", "pending", "assigned", "completed", "subject")))
    sc, j, items = lst(kind="routine")
    check("routine: 3日ドリルだけ (origin routine)", sc == 200 and d_rt in items
          and all(it["created_by"] == ROUTINE and it["origin"] == "routine" for it in items.values()), (sc, list(items)[:5]))
    sc, j, items = lst(kind="class_hw")
    check("class_hw: クラス自動宿題だけ", sc == 200 and set(items) == {d_chw, d_chw2}, sorted(items))
    check("印から区分とクラス名を読む (クラス名の ':' はそのまま)",
          items.get(d_chw, {}).get("group") == "kosei" and items.get(d_chw, {}).get("class_label") == "月曜3限 長文読解 Lv.1"
          and items.get(d_chw2, {}).get("group") == "chugaku" and items.get(d_chw2, {}).get("class_label") == "中学クラス: 架空"
          and items.get(d_chw, {}).get("origin") == "class_hw", [items.get(d_chw), items.get(d_chw2)])
    sc, j, items = lst(kind="auto")
    check("auto: 3日ドリルとクラス自動宿題の両方だけ", sc == 200 and {d_rt, d_chw, d_chw2} <= set(items)
          and all(auto_cb(it["created_by"]) for it in items.values()), sorted(items)[:8])
    sc, j, items = lst(kind="all")
    check("all: 初回診断を除く全部", sc == 200 and (mine - {d_diag}) <= set(items) and d_diag not in items, sorted(mine - set(items)))
    leaks = []
    for k_ in ("owner", "routine", "class_hw", "auto", "all", "OWNER"):
        sc, j, items = lst(kind=k_)
        if sc != 200 or d_diag in items or any(it["created_by"] == "diagnostic" for it in items.values()):
            leaks.append((k_, sc))
    check("初回診断 (diagnostic) はどの kind にも出ない (大文字の kind も通る)", not leaks, leaks)
    sc, j, items = lst(kind="all", subject="chugaku_math")
    check("subject=chugaku_math: 中学数学だけ", sc == 200 and j.get("subject") == "chugaku_math" and d_nullcb in items
          and all(it["subject"] == "chugaku_math" for it in items.values()), (sc, j.get("subject"), sorted(items)))
    sc, j, items = lst(subject="english")
    want = {d_admin, d_today, d_nosubj, d_alias, d_upper}
    check("subject=english: 空の科目・別名 (英語)・大文字 (English) の行も拾う (表示と同じ答え)", sc == 200 and want <= set(items)
          and not ({d_math, d_nullcb, d_chw} & set(items)) and all(it["subject"] == "english" for it in items.values()),
          (sorted(want - set(items)), sorted(items)))
    sc, j, items = lst(subject="数学")
    check("subject=数学 (別名) → math に直して絞る", sc == 200 and j.get("subject") == "math" and d_math in items and d_rt not in items,
          (sc, j.get("subject")))
    sc, j, items = lst(kind="routine", subject="math")
    check("kind と subject を組み合わせる (routine × math)", sc == 200 and d_rt in items and all(it["subject"] == "math" for it in items.values()))
    for v in ("", "all"):
        sc, j, items = lst(subject=v)
        check(f"subject={v!r} は絞らない", sc == 200 and j.get("subject") is None and owner_ids <= set(items), (sc, j.get("subject")))
    for params in ({"kind": "manual"}, {"kind": "bogus"}, {"subject": "xyz"}, {"subject": "english' OR 1=1 --"}):
        sc, j, items = lst(**params)
        check(f"{params} → 422", sc == 422, sc)
    conn = mod.db(); c = conn.cursor()
    for i in range(60):   # 自動配信は生徒ごとに 1 本ずつ → 塾長の配信より新しい行が 60 本
        c.execute("INSERT INTO grammar_drills (subject, title, unit, level, question_ids, created_by, created_at) "
                  "VALUES ('english', ?, '時制', 'standard', '[]', ?, ?)", (f"自動の架空のドリル {i}", ROUTINE, f"2031-01-01 00:{i // 60:02d}:{i % 60:02d}"))
    conn.commit(); conn.close()
    r = client.get("/api/admin/grammar-drill/list", headers=adm)
    ids50 = {it["id"] for it in r.json().get("items", [])} if r.status_code == 200 else set()
    r_all = client.get("/api/admin/grammar-drill/list", params={"kind": "all"}, headers=adm)
    ids50_all = {it["id"] for it in r_all.json().get("items", [])} if r_all.status_code == 200 else set()
    check("自動配信が 60 本増えても、既定 (50 本) から塾長の配信が押し出されない", d_admin in ids50 and len(ids50) <= 50, len(ids50))
    check("(比較: all の 50 本は新しい自動配信で埋まる = 既定を owner にした理由)", d_admin not in ids50_all and len(ids50_all) == 50, len(ids50_all))
    lsrc = src[src.index("def admin_grammar_drill_list"):][:4000]
    check("一覧に索引の DDL を足していない (起動時の DDL を増やさない)", "CREATE INDEX" not in lsrc and "ALTER TABLE" not in lsrc)

    print("  (ceo.html: 絞り込みの帯と 🎯 確認カード)")
    html = open(CEO_HTML, encoding="utf-8").read()
    try:
        pos = [html.index('id="gdRoutineBox"'), html.index('id="gdListBar"'), html.index('<div id="gdList"')]
    except ValueError as e:
        pos = []
        check("ceo.html に 🎯 確認カード・絞り込みの帯・一覧がある", False, e)
    check("並び: 🎯 確認カード → 絞り込みの帯 → 一覧", len(pos) == 3 and pos[0] < pos[1] < pos[2], pos)
    bar = html[html.index('id="gdListBar"'):html.index('<div id="gdList"')] if len(pos) == 3 else ""
    kinds = set(re.findall(r'data-kind="([a-z_]+)"', bar))
    check("帯の kind は owner / routine / class_hw / all (サーバが知っている値)", kinds == {"owner", "routine", "class_hw", "all"}
          and kinds <= set(mod._GRAMMAR_DRILL_LIST_KINDS), kinds)
    opts = set(re.findall(r'<option value="([a-z_]*)"', bar)) - {""}
    future = {"english_long", "proficiency_test"}   # 英語長文・習熟度テストの取込 (後のコミット) までは 422 = 「読めませんでした」と出る
    check("科目の選択肢 = サーバの科目すべて (+ 英語長文・習熟度テスト)", set(mod._GRAMMAR_CANON_SUBJECTS) <= opts
          and opts - set(mod._GRAMMAR_CANON_SUBJECTS) <= future, (sorted(set(mod._GRAMMAR_CANON_SUBJECTS) - opts), sorted(opts)))
    def js_fn(name):
        i = html.find(f"function {name}(")
        j_ = html.find("\n    }\n", i)
        return html[i:j_ + 6] if i >= 0 and j_ > i else ""
    ref = js_fn("gdRefresh")
    check("gdRefresh は ?kind=&subject= を付けて読む", "'/api/admin/grammar-drill/list' + _gdListQuery(_gdListKind, _gdListSubject)" in ref, ref[:300])
    check("gdRefresh は古い応答で新しい絞り込みを上書きしない (seq)", "seq !== _gdListSeq" in ref)
    ls_fns = [js_fn("_gdListLoadFilter"), js_fn("_gdListSaveFilter")]
    check("絞り込みの localStorage は try の中だけ", all(f_ and "localStorage" in f_ and f_.index("try {") < f_.index("localStorage") for f_ in ls_fns)
          and html.count("_GD_LIST_LS_KEY") == 3, ls_fns)
    dry = js_fn("gdRoutineDryRun")
    check("🎯 の 🔍 は dry_run: true と include_names: true だけを送る", "dry_run: true, include_names: true" in dry and "dry_run: false" not in dry, dry[:400])
    calls = re.findall(r"""[`'"]/api/admin/weakness-drill-routine/run""", html)   # 文字列としての URL (コメントは数えない)
    check("CEO の画面から 3日ドリルを回す呼び出しは 🔍 の 1 か所だけ (本番の配信ボタンは無い)", len(calls) == 1, calls)
    check("📦 は source-inventory を読む", "/api/admin/grammar/source-inventory" in js_fn("gdRoutineInventory"))
    check("inline onclick から呼ぶ関数を window に出している",
          all(f"window.{f_} = {f_}" in html for f_ in ("gdListSetKind", "gdListSetSubject", "gdRoutineDryRun", "gdRoutineInventory")))

    # 確認カードの描画を JS で実行する (本物の API の応答を渡す。名前・学年に HTML を入れて escape を確かめる)
    reset_routine()
    ex(mod, "UPDATE students SET name = ? WHERE id = ?", ("架空 <img src=x onerror=alert(1)> 生徒", k1))
    ex(mod, "UPDATE students SET grade = ? WHERE id = ?", ("<b>未設定</b>", u1))
    ex(mod, "DELETE FROM grammar_drill_assignments WHERE student_id = ?", (k1,))
    only_active([k1, c1, u1])
    rt = client.post("/api/admin/weakness-drill-routine/run", json={"dry_run": True, "include_names": True, "seed": 7}, headers=adm)
    rtj = rt.json() if rt.status_code == 200 else {}
    check("CEO の管理者のトークンで dry-run が読める (名前つき)", rt.status_code == 200 and rtj.get("dry_run") is True
          and any(e.get("id") == k1 for e in rtj.get("delivered_students", [])) and rtj.get("grade_unknown_students"), (rt.status_code, rtj)[:2])
    inv = client.get("/api/admin/grammar/source-inventory", headers=adm)
    invj = inv.json() if inv.status_code == 200 else {}
    eng = js_engine()
    check("JS の実行環境がある (node / osascript / jsc。無ければ FAIL)", bool(eng))
    a0_ = html.index("    function escapeHtml(s) { return (s||'')")
    esc_line = html[a0_:html.index("\n", a0_)]
    subj_ja = html[html.index("    const _GD_SUBJ_JA = {"):html.index("};", html.index("    const _GD_SUBJ_JA = {")) + 2]
    kinds_js = html[html.index("    const _GD_LIST_KINDS = "):html.index("\n", html.index("    const _GD_LIST_KINDS = "))]
    query_js = js_fn("_gdListQuery")
    card_js = html[html.index("    const _GD_RT_REASON_JA = {"):html.index("    let _gdRtBusy = false;")]
    prog = "\n".join([
        "var window = (typeof globalThis !== 'undefined') ? globalThis : this;",
        esc_line, subj_ja, kinds_js, query_js, card_js,
        "var __o = {};",
        f"__o.render = _gdRtRender({json.dumps(rtj, ensure_ascii=False)});",
        "__o.old = _gdRtRender({ ok: true, delivered: 1, skipped_grade: 2 });",
        f"__o.inv = _gdRtInvRender({json.dumps(invj, ensure_ascii=False)});",
        "__o.invOld = _gdRtInvRender({ ok: true });",
        "__o.q1 = _gdListQuery('class_hw', 'chugaku_math'); __o.q2 = _gdListQuery('owner', ''); __o.q3 = _gdListQuery('bogus', 'x y');",
        "__o.reason = _gdRtReasonLabel('band_mismatch:chugaku'); __o.reason2 = _gdRtReasonLabel('eng_not_grammar_unit');",
        # 2026-10-16: 前回の自動配信 (last_run)・見出しの言い方・古い未提出のチップ
        "__o.lr1 = _gdAutoLastRun({ at_jst: '10/16 05:30', at: '2026-10-16 05:30', delivered: 3, error: null });",
        "__o.lr0 = _gdAutoLastRun({ at_jst: '10/16 05:30', delivered: 0, error: null });",
        "__o.lrNone = _gdAutoLastRun(null); __o.lrOld = _gdAutoLastRun(undefined);",
        "__o.lrErr = _gdAutoLastRun({ at_jst: '10/16 05:30', delivered: null, error: '<b>失敗</b>' });",
        "__o.lrErr2 = _gdAutoLastRun({ at_jst: '10/16 05:30', delivered: 2, error: '学年ガード' });",
        f"var __rs = {json.dumps(rtj, ensure_ascii=False)}; __rs.last_run = {{ at_jst: '10/16 05:30', delivered: 4, error: null }};",
        "__rs.stale_open_ignored = 2; __rs.open_stale_days = 14; if (__rs.delivered_students && __rs.delivered_students[0]) __rs.delivered_students[0].stale_open = 3;",
        "__o.stale = _gdRtRender(__rs);",
        "__rs.stale_open_ignored = 0; __o.noStale = _gdRtRender(__rs);",
        "var __s = 'RESULT ' + JSON.stringify(__o);",
        "if (typeof process !== 'undefined' && typeof console !== 'undefined' && console.log) console.log(__s);",
        "else if (typeof print === 'function') print(__s);",
        "else if (typeof console !== 'undefined' && console.log) console.log(__s);",
    ])
    out, err = run_js(eng, prog) if eng else (None, "no engine")
    check("確認カードの描画が JS で動く", out is not None, err)
    out = out or {}
    rend = out.get("render", "")
    check("名前の HTML は escape される (<img を出さない)", "&lt;img" in rend and "<img" not in rend, rend[:300])
    check("学年の HTML も escape される", "&lt;b&gt;未設定&lt;/b&gt;" in rend and "<b>未設定" not in rend, rend[:300])
    check("配る生徒は id つきで並び、押すと生徒詳細を開く", f"#{k1}<" in rend and f"window.showStudentDetail({k1})" in rend, rend[:300])
    check("ON/OFF が出る (既定は OFF)", "自動配信 OFF" in rend)
    check("plan_version の無い古い応答は「サーバ反映待ち」(古い形を表にしない)", "反映待ち" in out.get("old", "") and "配る" not in out.get("old", ""))
    check("📦 の在庫が科目名つきで出る", "自動で出せる在庫" in out.get("inv", "") and "英文法" in out.get("inv", ""), out.get("inv", "")[:200])
    check("📦: 古いサーバは「サーバ反映待ち」", "反映待ち" in out.get("invOld", ""))
    check("一覧の問い合わせ文字列 (知らない kind は owner・科目は encode)",
          (out.get("q1"), out.get("q2"), out.get("q3")) == ("?kind=class_hw&subject=chugaku_math", "?kind=owner", "?kind=owner&subject=x%20y"),
          (out.get("q1"), out.get("q2"), out.get("q3")))
    check("見出しは「今もう一度回したら配る」(「今日 ON なら」は朝の実行の後に 0 名と出て動いていないと読み違える・2026-10-16)",
          "今もう一度回したら配る:" in rend and "今日 ON なら" not in rend and "ふつう 0 名" in rend, rend[:300])
    check("前回の自動配信は見出しの上 (last_run の時刻と人数)", "前回の自動配信: 10/16 05:30 に 4 名" in out.get("stale", "")
          and out.get("stale", "").index("前回の自動配信") < out.get("stale", "").index("今もう一度回したら配る"), out.get("stale", "")[:400])
    check("前回の自動配信: 人数 / 0 名 / 記録なし / 古いサーバ (何も出さない)",
          "前回の自動配信: 10/16 05:30 に 3 名" in out.get("lr1", "") and "10/16 05:30 に 0 名" in out.get("lr0", "")
          and "まだ記録がありません" in out.get("lrNone", "") and out.get("lrOld") == "", (out.get("lr1"), out.get("lrNone"), out.get("lrOld")))
    check("前回の自動配信が失敗なら ❌ と理由 (escape)・配った人数があれば添える",
          "❌" in out.get("lrErr", "") and "&lt;b&gt;失敗" in out.get("lrErr", "") and "<b>失敗" not in out.get("lrErr", "")
          and "配信 2 名" in out.get("lrErr2", ""), (out.get("lrErr"), out.get("lrErr2")))
    check("古い未提出を数えなかった生徒はチップ (14日より前の未提出は数えない 2名)・配る生徒の行に本数", "14日より前の未提出は数えない 2名" in out.get("stale", "")
          and "古い未提出 3 本" in out.get("stale", "") and "より前の未提出は数えない" not in out.get("noStale", "x"), out.get("stale", "")[:300])
    check("弱点を外した理由は日本語 (科目名つき)", out.get("reason") == "学年と科目が合わない：中学英語"
          and out.get("reason2", "").startswith("英語の弱点が文法の単元に当たらない"), (out.get("reason"), out.get("reason2")))

    # 絞り込みの帯の動き (偽の DOM・偽の fetch で ceo.html の本物のコードを動かす): 端末に覚えた値の復元・古い応答で上書きしない・
    #   localStorage が使えない端末・古いサーバ (kind を返さない)・422 の表示
    filt_js = html[html.index("    const _GD_LIST_KINDS = "):html.index("    function _gdRateColor(")]
    prog2 = "\n".join([
        "var window = (typeof globalThis !== 'undefined') ? globalThis : this;",
        "var __store = {}; var localStorage = { getItem: function (k) { return (k in __store) ? __store[k] : null; }, setItem: function (k, v) { __store[k] = String(v); } };",
        "__store['aj_ceo_gd_list_filter_v1'] = JSON.stringify({ kind: 'class_hw', subject: 'chugaku_math' });",
        "function __btn(k) { return { k: k, style: {}, getAttribute: function (a) { return a === 'data-kind' ? this.k : null; } }; }",
        "var __btns = ['owner', 'routine', 'class_hw', 'all'].map(__btn);",
        "var __sel = { value: '', options: [{ value: '' }, { value: 'english' }, { value: 'chugaku_math' }] };",
        "var __list = { innerHTML: '' };",
        "var document = { querySelectorAll: function () { return __btns; }, getElementById: function (id) { return id === 'gdListSubject' ? __sel : (id === 'gdList' ? __list : null); } };",
        "var __calls = [], __pending = [], __rendered = [];",
        "var AdminAuth = { fetch: function (path) { __calls.push(path); return new Promise(function (r) { __pending.push(r); }); } };",
        "function __res(status, body) { return { ok: status === 200, status: status, json: function () { return Promise.resolve(body); } }; }",
        "var _gdItems = [], _gdShowAllGroups = false;",
        # ★console は宣言し直さない (node の module スコープでは var console が本物を隠して何も出なくなる)
        "if (typeof console === 'undefined') { window.console = { warn: function () {}, log: function () {} }; }",
        "function gdRenderList() { __rendered.push({ ids: _gdItems.map(function (x) { return x.id; }), note: _gdListNote }); }",
        esc_line, filt_js,
        "var __o = { restored: [_gdListKind, _gdListSubject] };",
        "async function __ticks() { for (var i = 0; i < 20; i++) { await null; } }",
        "(async function () {",
        "  gdRefresh();",
        "  __o.weight = __btns.map(function (b) { return b.style.fontWeight; }); __o.sel = __sel.value;",
        "  gdListSetKind('routine');",
        "  __pending[1](__res(200, { ok: true, kind: 'routine', items: [{ id: 2 }] })); await __ticks();",
        "  __pending[0](__res(200, { ok: true, kind: 'class_hw', items: [{ id: 1 }] })); await __ticks();",
        "  __o.calls = __calls.slice(); __o.rendered = __rendered.slice(); __o.saved = __store['aj_ceo_gd_list_filter_v1'];",
        "  gdListSetKind('evil'); __o.callsAfterEvil = __calls.length;",
        "  gdListSetSubject(''); __pending[2](__res(200, { ok: true, items: [{ id: 3 }] })); await __ticks();",
        "  __o.oldServerNote = __rendered[__rendered.length - 1].note;",
        "  gdListSetSubject('chugaku_math'); __pending[3](__res(422, { detail: '<b>科目</b> はこのサーバでは使えません' })); await __ticks();",
        "  __o.err = __list.innerHTML;",
        "  _gdListKind = 'owner'; _gdListSubject = '';",
        "  __store['aj_ceo_gd_list_filter_v1'] = JSON.stringify({ kind: 'evil', subject: '<x>' }); _gdListLoadFilter();",
        "  __o.garbage = [_gdListKind, _gdListSubject];",
        "  localStorage = { getItem: function () { throw new Error('blocked'); }, setItem: function () { throw new Error('blocked'); } };",
        "  try { _gdListLoadFilter(); _gdListSaveFilter(); __o.blockedOk = true; } catch (e) { __o.blockedOk = String(e); }",
        "  var __s = 'RESULT ' + JSON.stringify(__o);",
        "  if (typeof process !== 'undefined' && console.log) console.log(__s); else if (typeof print === 'function') print(__s); else console.log(__s);",
        "})();",
    ])
    out2, err2 = run_js(eng, prog2) if eng else (None, "no engine")
    check("絞り込みの帯のコードが JS で動く", out2 is not None, err2)
    out2 = out2 or {}
    check("端末に覚えた絞り込み (🏫・中学数学) を開き直したときに戻す", out2.get("restored") == ["class_hw", "chugaku_math"]
          and out2.get("sel") == "chugaku_math" and out2.get("weight") == ["400", "400", "800", "400"], out2)
    check("押した順に ?kind=&subject= で読む", (out2.get("calls") or [])[:2] == [
        "/api/admin/grammar-drill/list?kind=class_hw&subject=chugaku_math", "/api/admin/grammar-drill/list?kind=routine&subject=chugaku_math"],
        out2.get("calls"))
    check("後から届いた古い応答 (🏫) で新しい絞り込み (🎯) の表示を上書きしない", [r_["ids"] for r_ in out2.get("rendered", [])] == [[2]],
          out2.get("rendered"))
    check("選んだ値を端末に覚える", json.loads(out2.get("saved") or "{}") == {"kind": "routine", "subject": "chugaku_math"}, out2.get("saved"))
    check("知らない kind は無視 (読み直さない)", out2.get("callsAfterEvil") == 2, out2.get("callsAfterEvil"))
    check("古いサーバ (kind を返さない) で絞り込み中なら「反映待ち」と出す", "反映待ち" in str(out2.get("oldServerNote")), out2.get("oldServerNote"))
    check("422 は今の一覧を消して理由を出す (escape して)", "読めませんでした" in out2.get("err", "") and "&lt;b&gt;科目" in out2.get("err", "")
          and "<b>科目" not in out2.get("err", ""), out2.get("err"))
    check("覚えた値が壊れていたら既定 (👤・すべて)", out2.get("garbage") == ["owner", ""], out2.get("garbage"))
    check("localStorage が使えない端末でも落ちない", out2.get("blockedOk") is True, out2.get("blockedOk"))

    # ------------------------------------------------------------------
    print("\n[11] 2026-10-16 塾長決定: 3 日は JST の日付で・14 日より前の未提出は数えない・予約タスクの行は数えない")
    UTC = datetime.timezone.utc
    JST = datetime.timezone(datetime.timedelta(hours=9))

    def at_jst(y, m, d, hh=0, mm=0, ss=0):
        """JST の時刻 → aware UTC (now= に渡す)。"""
        return datetime.datetime(y, m, d, hh, mm, ss, tzinfo=JST).astimezone(UTC)

    def utc_txt(dt):
        return dt.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S")

    def give(sid, when, status="completed", created_by=ROUTINE, null_at=False):
        """sid に 1 本配った記録を足す (when = aware。null_at なら assigned_at を空にする)。"""
        conn = mod.db(); c = conn.cursor()
        c.execute("INSERT INTO grammar_drills (subject, title, unit, level, question_ids, created_by) VALUES "
                  "('english', '架空の過去の配信', '時制', 'standard', '[]', ?) RETURNING id", (created_by,))
        d_ = c.fetchone()["id"]
        if null_at:
            c.execute("INSERT INTO grammar_drill_assignments (drill_id, student_id, status, assigned_at) VALUES (?, ?, ?, NULL)", (d_, sid, status))
        else:
            c.execute("INSERT INTO grammar_drill_assignments (drill_id, student_id, status, assigned_at) VALUES (?, ?, ?, ?)",
                      (d_, sid, status, utc_txt(when)))
        conn.commit(); conn.close()
        return d_

    def clear(sid):
        ex(mod, "DELETE FROM grammar_drill_assignments WHERE student_id = ?", (sid,))

    def dry_at(sid, now_):
        return mod._run_weakness_drill_routine(only_student_id=sid, dry_run=True, seed=1, now=now_)

    N19 = at_jst(2026, 10, 19, 5, 30, 0)          # 毎朝の実行 (5:30:00 ちょうどに起きる)
    cut = mod._weakness_routine_cutoffs(N19)
    check("境目: 10/19 5:30 の実行の cadence = 10/17 0:00 JST (UTC 10/16 15:00)・open_stale = 10/5 0:00 JST・既定 14 日",
          cut == {"cadence": "2026-10-16 15:00:00", "open_stale": "2026-10-04 15:00:00", "open_stale_days": 14}, cut)
    for v, want in ((None, 14), ("", 14), ("0", 0), ("-5", 0), ("1", 3), ("2", 3), ("7", 7), ("30", 30), ("999", 365), ("14日", 14)):
        with Env(WEAKNESS_ROUTINE_OPEN_STALE_DAYS=v):
            got = mod._weakness_routine_cutoffs(N19)
            check(f"WEAKNESS_ROUTINE_OPEN_STALE_DAYS={v!r} → {want} 日 (0 = 全部数える・3〜365 に丸める・読めない値は既定)",
                  got["open_stale_days"] == want and ((got["open_stale"] is None) == (want == 0)), got)
    # ① 3 日は JST の日付で (4 日ごとにならない)
    g1 = make("高校2年")
    weak(g1, "english", "時制")
    give(g1, at_jst(2026, 10, 16, 5, 30, 4))      # 3 日前の 5:30 の実行で配った (書き込みは実行を始めた数秒後)
    old_rule = utc_txt(at_jst(2026, 10, 16, 5, 30, 4)) >= utc_txt(N19 - datetime.timedelta(days=3))
    check("(前提) 旧版の「今 − 72 時間」なら 3 日前の 5:30:04 はまだ 3 日以内 = 4 日目まで届かなかった", old_rule)
    r = dry_at(g1, N19)
    check("3 日前 (10/16 5:30:04) に配った生徒は 10/19 5:30:00 の実行で届く (skipped_recent にしない)",
          r["delivered"] == 1 and r["skipped_recent"] == 0, r)
    r = dry_at(g1, at_jst(2026, 10, 18, 5, 30, 0))
    check("2 日後 (10/18) は届かない (skipped_recent)", r["delivered"] == 0 and r["skipped_recent"] == 1, r)
    clear(g1)
    give(g1, at_jst(2026, 10, 16, 23, 59, 59))
    r = dry_at(g1, N19)
    check("10/16 23:59 に配った生徒も 10/19 に届く (JST の日付で 3 日)", r["delivered"] == 1, r)
    clear(g1)
    give(g1, at_jst(2026, 10, 17, 0, 0, 0))
    r = dry_at(g1, at_jst(2026, 10, 19, 23, 59, 0))
    check("10/17 0:00 に配った生徒は 10/19 のうちは届かない", r["delivered"] == 0 and r["skipped_recent"] == 1, r)
    # 錠の中の読み直しも同じ境目 (一括の判定と食い違うと skipped_race で 1 日ずれる)
    clear(g1)
    give(g1, at_jst(2026, 10, 16, 5, 30, 4))
    conn = mod.db(); c = conn.cursor()
    r_race = mod._create_routine_grammar_drill(c, conn, "english", "時制", 10, g1, st_of(g1), band="kosei",
                                               cutoffs=mod._weakness_routine_cutoffs(at_jst(2026, 10, 18, 5, 30, 0)))
    r_ok = mod._create_routine_grammar_drill(c, conn, "english", "時制", 10, g1, st_of(g1), band="kosei",
                                             cutoffs=mod._weakness_routine_cutoffs(N19))
    conn.close()
    check("錠の中の読み直し: 10/18 の境目では 3 日以内 (race)・10/19 の境目では書ける (一括の判定と同じ)",
          r_race == {"race": True, "why": "already"} and isinstance(r_ok, dict) and r_ok.get("drill_id"), (r_race, r_ok))
    # ② 14 日より前の未提出は「未提出が残っている」に数えない
    s1 = make("高校2年")
    weak(s1, "english", "時制")
    give(s1, at_jst(2026, 10, 4, 23, 59, 0), status="open")      # 15 日前 (10/4) の未提出
    r = dry_at(s1, N19)
    ent = (r.get("delivered_students") or [{}])[0]
    check("15 日前 (10/4) の未提出だけなら数えずに配る (stale_open_ignored 1・open_stale_days 14)",
          r["delivered"] == 1 and r["skipped_open"] == 0 and r["stale_open_ignored"] == 1 and r["open_stale_days"] == 14
          and ent.get("stale_open") == 1, r)
    with Env(WEAKNESS_ROUTINE_OPEN_STALE_DAYS="0"):
        r = dry_at(s1, N19)
        check("WEAKNESS_ROUTINE_OPEN_STALE_DAYS=0 なら従来どおり数える (skipped_open)", r["delivered"] == 0 and r["skipped_open"] == 1
              and r["stale_open_ignored"] == 0 and r["open_stale_days"] == 0, r)
    with Env(WEAKNESS_ROUTINE_OPEN_STALE_DAYS="30"):
        r = dry_at(s1, N19)
        check("WEAKNESS_ROUTINE_OPEN_STALE_DAYS=30 なら 15 日前の未提出も数える", r["skipped_open"] == 1 and r["open_stale_days"] == 30, r)
    clear(s1)
    give(s1, at_jst(2026, 10, 5, 0, 0, 0), status="open")         # ちょうど 14 日前 (10/5) の未提出
    r = dry_at(s1, N19)
    check("ちょうど 14 日前 (10/5) の未提出はまだ数える (skipped_open)", r["delivered"] == 0 and r["skipped_open"] == 1
          and r["stale_open_ignored"] == 0, r)
    clear(s1)
    give(s1, at_jst(2026, 9, 1, 5, 30), status="open")
    give(s1, at_jst(2026, 10, 18, 5, 30), status="open")
    r = dry_at(s1, N19)
    check("古い未提出と新しい未提出の両方があれば積まない (skipped_open・stale_open_ignored に数えない)",
          r["skipped_open"] == 1 and r["stale_open_ignored"] == 0, r)
    clear(s1)
    give(s1, None, status="open", null_at=True)
    r = dry_at(s1, N19)
    check("assigned_at が空の未提出は新しいものとして数える (積まない側)", r["skipped_open"] == 1 and r["delivered"] == 0, r)
    clear(s1)
    give(s1, at_jst(2026, 9, 1, 5, 30), status="assigned")
    r = dry_at(s1, N19)
    check("'assigned' の古い 3日ドリルも 14 日より前なら数えない", r["delivered"] == 1 and r["stale_open_ignored"] == 1, r)
    # 本番 (dry-run でない) でも錠の中の読み直しが古い未提出で止めない・古いドリルは消さず生徒の一覧に残る
    clear(s1)
    real_now = datetime.datetime.now(UTC)
    old_did = give(s1, real_now - datetime.timedelta(days=20), status="open")
    before_n = q(mod, "SELECT COUNT(*) AS n FROM grammar_drill_assignments WHERE student_id = ?", (s1,))[0]["n"]
    r = mod._run_weakness_drill_routine(only_student_id=s1, seed=1)
    rows_s1 = q(mod, "SELECT a.drill_id, a.status FROM grammar_drill_assignments a WHERE a.student_id = ? ORDER BY a.id", (s1,))
    check("本番: 20 日前の未提出があっても新しい 3日ドリルを書く (錠の中の読み直しで race にしない)",
          r["delivered"] == 1 and r["skipped_race"] == 0 and r["stale_open_ignored"] == 1 and len(rows_s1) == before_n + 1, (r, rows_s1))
    check("古いドリルは消さない (未提出のまま残る)", any(x["drill_id"] == old_did and x["status"] == "open" for x in rows_s1), rows_s1)
    import base64 as _b64, hashlib as _hl, hmac as _hm
    exp_ = int(time.time()) + 3600
    pl_ = f"session.{s1}.{exp_}"
    tok_ = _b64.urlsafe_b64encode(f"{pl_}.{_hm.new(mod.MAGIC_LINK_SECRET.encode(), pl_.encode(), _hl.sha256).hexdigest()}".encode()).decode().rstrip("=")
    rs_ = client.get("/api/student/grammar-drills", headers={"Authorization": "Bearer " + tok_})
    its_ = rs_.json().get("items", []) if rs_.status_code == 200 else []
    check("生徒の一覧に古いドリルも新しいドリルも出る (summary.open 2)", rs_.status_code == 200 and old_did in {x["drill_id"] for x in its_}
          and rs_.json().get("summary", {}).get("open") == 2, (rs_.status_code, [(x["drill_id"], x["status"]) for x in its_]))
    r = mod._run_weakness_drill_routine(only_student_id=s1, seed=1)
    check("新しい未提出があれば次の日も積まない (skipped_open)", r["delivered"] == 0 and r["skipped_open"] == 1, r)
    # ③ デスクトップの予約タスクの行は数えない (2026-10-16 塾長決定「両方配ってよい」)
    m1 = make("高校2年")
    weak(m1, "english", "時制")
    give(m1, real_now, status="assigned", created_by="mission_2day_routine")
    r = mod._run_weakness_drill_routine(only_student_id=m1, dry_run=True, seed=1)
    check("予約タスク (created_by='mission_2day_routine') の未提出 'assigned' は 3日ドリルを止めない (両方届く)",
          r["delivered"] == 1 and r["skipped_open"] == 0 and r["skipped_recent"] == 0 and r["stale_open_ignored"] == 0, r)
    run_src = src[src.index("def _run_weakness_drill_routine"):][:16000]
    check("コメントは「予約タスクの行は数えない」(数えると書いた古いコメントを残さない)",
          "デスクトップの予約タスクが書く 'assigned' も)" not in run_src and "mission_2day_routine" in run_src, "")
    props = mod._compact_run_props(r)
    check("実行記録の要約に stale_open_ignored と open_stale_days が残る", "stale_open_ignored" in props and props.get("open_stale_days") == 14, props)

    # ------------------------------------------------------------------
    print("\n[12] 2026-10-16 塾長決定: CEO の 🎯 カードの「前回の自動配信」(last_run = events の実行記録を読むだけ)")
    ex(mod, "DELETE FROM events WHERE name = 'weakness_drill_routine_run'")
    j0 = client.post("/api/admin/weakness-drill-routine/run", json={"dry_run": True}, headers=cron).json()
    check("実行記録が無ければ last_run は null (キーはある)", "last_run" in j0 and j0["last_run"] is None, j0.get("last_run"))
    mod._record_scheduler_run("weakness_drill_routine_run", mod._compact_run_props({"delivered": 3, "eligible": 3, "delivered_students": [{"id": 1, "name": "架空"}]}))
    ev = q(mod, "SELECT created_at FROM events WHERE name = 'weakness_drill_routine_run' ORDER BY id DESC LIMIT 1")[0]
    ev_jst = datetime.datetime.strptime(str(ev["created_at"])[:19], "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=9)
    j1 = client.post("/api/admin/weakness-drill-routine/run", json={"dry_run": True}, headers=cron).json()
    lr = j1.get("last_run") or {}
    check("last_run: 最後の実行の JST の時刻 (M/D HH:MM) と配った人数・error なし",
          lr.get("delivered") == 3 and lr.get("error") is None and lr.get("at_jst") == f"{ev_jst.month}/{ev_jst.day} {ev_jst:%H:%M}"
          and lr.get("at") == ev_jst.strftime("%Y-%m-%d %H:%M"), (lr, str(ev["created_at"])))
    check("last_run に名前は入らない (実行記録は名前なし)", "架空" not in json.dumps(lr, ensure_ascii=False), lr)
    ex(mod, "INSERT INTO events (name, props, session_id, created_at) VALUES ('weakness_drill_routine_run', ?, 'in_process_scheduler', '2099-01-01 00:00:00')",
       (json.dumps({"error": "ValueError: 架空の失敗"}),))
    lr2 = client.post("/api/admin/weakness-drill-routine/run", json={"dry_run": True}, headers=cron).json().get("last_run") or {}
    check("いちばん新しい実行記録を読む・例外で終わった実行は delivered なし + error", lr2.get("at_jst") == "1/1 09:00"
          and lr2.get("delivered") is None and "架空の失敗" in str(lr2.get("error")), lr2)
    ex(mod, "INSERT INTO events (name, props, session_id, created_at) VALUES ('weakness_drill_routine_run', 'not json', 'x', '2099-01-02 00:00:00')")
    lr3 = mod._auto_delivery_last_run("weakness_drill_routine_run")
    check("props が壊れていても落ちない (時刻だけ)", lr3 and lr3.get("at_jst") == "1/2 09:00" and lr3.get("delivered") is None, lr3)
    orig_db = mod.db

    def broken_db():
        raise RuntimeError("DB に届かない (架空)")

    mod.db = broken_db
    try:
        lr4 = mod._auto_delivery_last_run("weakness_drill_routine_run")
    finally:
        mod.db = orig_db
    check("events が読めなくても例外を出さず {read_failed: True} (dry-run の応答を止めない・「記録なし」と区別)", lr4 == {"read_failed": True}, lr4)
    _ceo_src = open(os.path.join(REPO, "ceo.html"), encoding="utf-8").read()
    check("CEO カードは read_failed を「記録を読めませんでした」と出す (まだ記録がありませんと分ける)",
          "lr.read_failed" in _ceo_src and "記録を読めませんでした" in _ceo_src, None)
    ex(mod, "DELETE FROM events WHERE name = 'weakness_drill_routine_run' AND created_at >= '2099-01-01'")
    before = counts(mod)
    client.post("/api/admin/weakness-drill-routine/run", json={"dry_run": True}, headers=cron)
    check("last_run を読んでも何も書かない", counts(mod) == before, (before, counts(mod)))

    print()
    if FAILURES:
        print(f"❌ FAIL ({len(FAILURES)} 件)")
        for f in FAILURES:
            print("   -", f)
        sys.exit(1)
    print("✅ PASS (3日ドリル: レビュー済みだけ・中高の取り違えなし・既出の除外・dry-run の一致・1 人 1 経路)")


if __name__ == "__main__":
    main()
