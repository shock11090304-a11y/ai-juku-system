#!/usr/bin/env python3
"""🤖 自動配信の共通部品の回帰テスト (2026-10-15 塾長決定「自動で配るのはレビュー済みの科目別ドリルだけ」
「中学生と高校生は問題の配信はミスらないように」)。

3日ドリル (AIあり・AI 体験中) と塾生アプリのみ枠 (AIなし) のクラス自動宿題が使う判定を、ここで 1 回だけ固定する
(経路ごとに許可リスト・学年・AI 判定を持つと食い違う)。生徒名・メールは架空 (公開リポジトリ)。一時 SQLite・外部通信なし。

  [1] シードの固定: REVIEWED_SEEDS の全問 (本文と本文の設問も) が自動配信の許可を通る / NOT_AUTO_SEEDS (english の
      chu2grammar・弱点特訓 weakness_v1) は 1 問も通らない / seed-data の *pool* / *_drill_* / *grammar* のシードは
      どちらかに必ず分類されている (新しいシードを足したら、盲検の記録を見てどちらかに入れる)
  [2] 許可リストと禁止: 既定の判定・env AUTO_DELIVERY_REVIEWED_SOURCES の差し替え (科目ごと・読めない値は既定)・
      習熟度テスト (subject proficiency_test / 出典 pt- / ptest:) は 'english=*' でも出ない
  [3] 弱点 topic → ドリルの単元: 英語 (関係代名詞 → 関係詞 = 旧「名詞・代名詞」の取り違えの回帰) / 中学 (前置き・かっこ・コロン)
  [4] 学年の区分と科目の組み合わせ (_drill_subject_band_ok) と 3日ドリルの科目 (_ROUTINE_SUBJECTS_BY_BAND)
  [5] AI の振り分け: Python (_auto_delivery_ai_path) と SQL の広めの絞り込みで、全員がちょうど 1 経路に入る (C7)
  [6] 1 問ずつの抽出: レビュー済みだけ・足りなければ配らない・前に見た問題を避け古い順に足す・同じ rng なら同じ問題・
      長文の設問と数学III を拾わない・入試道場の解答の id では除外しない
  [7] 本文の抽出: 英検の長文 (シードを CEO と同じ取込で入れる) は通る / 設問が 1 問でも未レビューの本文・出典が未レビューの本文・
      設問の科目が違う本文は本文ごと外す / 前に見た本文は本文ごと避ける
  [8] GET /api/admin/grammar/source-inventory: 認証なし 401・古い 'pool' の行が legacy_active に出る・単元ごとの在庫
  [9] _compact_run_props: 4000 字に収まる正しい JSON・名前とメールを含まない・error は残る / _auto_created_by_sql
  [10] 英語長文と習熟度テスト (コミット 8): 習熟度テストは 3日ドリルの計画にも、クラス自動宿題が使う 2 つの抽出
      (_auto_pick_reviewed_question_ids / _auto_pick_reviewed_passages) にも出ない (出典が許可リストの形でも・env でも)。
      英語長文 (出典 el- / englong:) は許可リストを通るが、学年の区分は高校生だけで、3日ドリルの計画には出ない

実行:
    python3 scripts/health_check/test_auto_delivery_shared.py
    # exit 0 = PASS / 1 = FAIL
"""
import ast
import base64
import datetime
import fnmatch
import hashlib
import hmac
import importlib.util
import inspect
import json
import os
import random
import sys
import tempfile
import textwrap

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
SEED_DIR = os.path.join(REPO, "seed-data")
sys.path.insert(0, os.path.join(REPO, "server"))

# 自動配信に載せてよいシード (盲検 3 名の記録がある) → CEO の補充ボタンが送る既定の科目
REVIEWED_SEEDS = {
    "grammar_drill_pool_v1.json": "english",
    "grammar_drill_pool_v2.json": "english",
    "chugaku_drill_pool_v1.json": "chugaku",
    "chugaku_math_pool_v1.json": "chugaku_math",
    "chugaku_rika_pool_v1.json": "chugaku_rika",
    "chugaku_shakai_pool_v1.json": "chugaku_shakai",
    "chugaku_kokugo_pool_v1.json": "chugaku_kokugo",
    "math_drill_ct_mock_v1.json": "math",
    "math_drill_workbook_v1.json": "math",
    "eiken_vocab_pool_v1.json": "eiken",
    "eiken_vocab_pool_v2.json": "eiken",
    "eiken_reading_pool_v1.json": "eiken",
    "eiken_reading_pool_v2.json": "eiken",
}
# 自動配信に載せないシード (盲検 3 名の記録が無い・ボタンにつながっていない)
NOT_AUTO_SEEDS = {
    "chu2_grammar_v1.json": "english",          # 同じ出典の文字列が中学英語 (chugaku) にもある。english の行は盲検記録なし
    "grammar_drill_weakness_v1.json": "english",  # 弱点特訓 32 問 (英語 16・古文 16)。塾長の判断待ち
}
SEED_GLOBS = ("*pool*.json", "*_drill_*.json", "*grammar*.json")

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="auto_shared_"), "test.db")
    os.environ.update({
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
    })
    os.environ.pop("AUTO_DELIVERY_REVIEWED_SOURCES", None)
    spec = importlib.util.spec_from_file_location("aijuku_main_auto_shared", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def admin_token(mod, hours=1):
    exp = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)).timestamp())
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), f"admin.{exp}".encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


class Env:
    """AUTO_DELIVERY_REVIEWED_SOURCES を一時的に差し替える (None = 未設定)。"""

    def __init__(self, value):
        self.value = value

    def __enter__(self):
        self.old = os.environ.get("AUTO_DELIVERY_REVIEWED_SOURCES")
        if self.value is None:
            os.environ.pop("AUTO_DELIVERY_REVIEWED_SOURCES", None)
        else:
            os.environ["AUTO_DELIVERY_REVIEWED_SOURCES"] = self.value
        return self

    def __exit__(self, *a):
        if self.old is None:
            os.environ.pop("AUTO_DELIVERY_REVIEWED_SOURCES", None)
        else:
            os.environ["AUTO_DELIVERY_REVIEWED_SOURCES"] = self.old


def seed_rows(fname, default_subject):
    """シードの (種類, 科目, 取込後の出典) を全部返す。取込 (admin_grammar_import) と同じく、問題の出典は 30 字・本文は 60 字で切り、
    本文の設問は設問の出典 → 本文の出典 → 'pool' の順。科目は行の subject → ファイルの subject → CEO が送る既定。"""
    d = json.load(open(os.path.join(SEED_DIR, fname), encoding="utf-8"))
    rows = []
    top = d.get("subject") if isinstance(d, dict) else None
    qs = d if isinstance(d, list) else (d.get("questions") or [])
    for q in qs:
        subj = q.get("subject") or top or default_subject
        rows.append(("q", subj, str(q.get("source") or "pool").strip()[:30]))
    for p in (d.get("passages") or []) if isinstance(d, dict) else []:
        subj = p.get("subject") or top or default_subject
        rows.append(("p", subj, str(p.get("source") or "pool").strip()[:60]))
        for q in p.get("questions") or []:
            rows.append(("pq", subj, str(q.get("source") or p.get("source") or "pool").strip()[:30]))
    return rows


def main():
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app, raise_server_exceptions=False)
    H = {"Authorization": "Bearer " + admin_token(mod)}
    ok_src = mod._auto_delivery_source_ok

    # ------------------------------------------------------------------
    print("\n[1] シードの固定 (レビュー済みのシードだけが自動配信の許可を通る)")
    for fname, subj in REVIEWED_SEEDS.items():
        rows = seed_rows(fname, subj)
        bad = [r for r in rows if not ok_src(r[1], r[2])]
        check(f"{fname}: 全 {len(rows)} 行 (問題・本文・本文の設問) が許可を通る", rows and not bad, bad[:3])
    for fname, subj in NOT_AUTO_SEEDS.items():
        rows = seed_rows(fname, subj)
        good = [r for r in rows if ok_src(r[1], r[2])]
        check(f"{fname}: {len(rows)} 行のどれも自動配信の許可を通らない", rows and not good, good[:3])
    seeds = sorted({f for g in SEED_GLOBS for f in fnmatch.filter(os.listdir(SEED_DIR), g)})
    unclassified = [f for f in seeds if f not in REVIEWED_SEEDS and f not in NOT_AUTO_SEEDS]
    check(f"seed-data の単元ドリルのシード {len(seeds)} 本はすべて REVIEWED_SEEDS か NOT_AUTO_SEEDS に分類済み "
          f"(新しいシードは盲検の記録を見てどちらかに足す)", not unclassified, unclassified)
    missing = [f for f in list(REVIEWED_SEEDS) + list(NOT_AUTO_SEEDS) if not os.path.exists(os.path.join(SEED_DIR, f))]
    check("分類表のシードはすべて実在する", not missing, missing)
    allow = mod._auto_delivery_allowlist()
    for subj in allow:
        check(f"許可リストの科目 {subj} は単元ドリルの科目", subj in mod._GRAMMAR_CANON_SUBJECTS)
    check("許可リストに高校の理科・社会・国語は無い (盲検記録のあるシードが無い)",
          not ({"physics", "chemistry", "biology", "earth", "social", "japanese"} & set(allow)), sorted(allow))

    # ------------------------------------------------------------------
    print("\n[2] 許可リスト・禁止・env の差し替え")
    cases = [
        ("english", "manual-drill-v1", True), ("english", "manual-drill-v2", True), ("english", "pool", False),
        ("english", "", False), ("english", None, False), ("english", "legacy", False), ("english", "weakness_v1", False),
        ("english", "chu2grammar-20260709", False), ("chugaku", "chu2grammar-20260709", True),
        ("chugaku", "chugaku-drill-v4", True), ("chugaku", "chugaku-drill-v5", False),
        ("japanese", "weakness_v1", False), ("physics", "pool", False), ("math", "mathwb-kI:1:1", True),
        ("math", "mathct-r1-ia-1-1", True), ("math", "pool", False), ("eiken", "eikenp1-mock-v1 S1-A", True),
        ("eiken", "eiken2-honban-r1 大問2[2A]", True), ("eiken", "pool", False),
        ("chugaku_math", "chugaku-math-v1", True), ("chugaku_math", "chugaku-drill-v1", False),
        ("proficiency_test", "pt-t1-1", False), ("english", "pt-t1-1", False),
        # 📖 英語長文 (2026-10-15 コミット 8): 取込が盲検の記録を必須にしているので、取込スクリプトの出典の形だけを許可
        ("english_long", "el-L1S001-P01-Q1", True), ("english_long", "englong:L1S001:P01", True),
        ("english_long", "pool", False), ("english_long", "manual-drill-v1", False), ("english_long", "pt-T1-Q01", False),
        ("english", "el-L1S001-P01-Q1", False), ("proficiency_test", "el-L1S001-P01-Q1", False),
        ("proficiency_test", "englong:L1S001:P01", False),
    ]
    for subj, src, want in cases:
        check(f"既定: ({subj}, {src!r}) → {want}", ok_src(subj, src) is want)
    with Env("english=*"):
        check("env english=*: english の 'pool' も通る (塾長が明示した差し替え)", ok_src("english", "pool"))
        check("env english=*: 出典 pt- (習熟度テスト) は通らない", not ok_src("english", "pt-t1-q1"))
        check("env english=*: 本文 ptest: は通らない", not ok_src("english", "ptest:t1:S01"))
        check("env english=*: 大文字の PT- も通らない", not ok_src("english", "PT-t1-q1"))
        check("env english=*: 他の科目は既定のまま (math の pool は通らない)", not ok_src("math", "pool"))
        check("env english=*: 科目 proficiency_test は通らない", not ok_src("proficiency_test", "manual-drill-v1"))
    with Env("english=*;proficiency_test=*"):
        check("env proficiency_test=*: それでも科目 proficiency_test は通らない",
              not ok_src("proficiency_test", "anything") and not ok_src("proficiency_test", "pt-t1-1"))
    with Env("english=manual-drill-v2;physics="):
        check("env english=manual-drill-v2: v1 は外れる", not ok_src("english", "manual-drill-v1"))
        check("env english=manual-drill-v2: v2 は通る", ok_src("english", "manual-drill-v2"))
        check("env の差し替えは書いた科目だけ (math は既定のまま)", ok_src("math", "mathwb-kI:1:1"))
        check("env physics=: physics は空 (通らない)", not ok_src("physics", "pool"))
    for raw in ("english", "englsh=*", "=*"):
        with Env(raw):
            check(f"env {raw!r} (読めない) → 既定 (v1 は通る・pool は通らない)",
                  ok_src("english", "manual-drill-v1") and not ok_src("english", "pool"))
    with Env(None):
        check("env を外すと既定に戻る", ok_src("english", "manual-drill-v1") and not ok_src("english", "pool"))
    check("禁止の科目に proficiency_test", "proficiency_test" in mod._AUTO_DELIVERY_DENY_SUBJECTS)
    check("禁止の出典の接頭辞 pt- / ptest:", set(mod._AUTO_DELIVERY_DENY_SOURCE_PREFIXES) >= {"pt-", "ptest:"})

    # ------------------------------------------------------------------
    print("\n[3] 弱点 topic → ドリルの単元")
    eng = mod._eng_drill_unit_for_topic
    for topic, want in [
        ("関係代名詞", "関係詞"), ("関係代名詞の非制限用法", "関係詞"), ("関係代名詞（主格）", "関係詞"), ("関係副詞", "関係詞"),
        ("代名詞", "名詞・代名詞"), ("不定代名詞", "名詞・代名詞"), ("時制の一致", "時制"), ("現在完了進行形", "時制"),
        ("間接疑問文", "疑問詞・間接疑問"), ("イディオム", "語法・イディオム"), ("熟語", "語法・イディオム"),
        ("分詞構文の意味上の主語", "分詞構文"), ("動名詞の意味上の主語", "動名詞"), ("仮定法過去完了", "仮定法"),
        ("比較級", "比較"), ("強調構文", "強調・省略"), ("受け身", "受動態"), ("時制: 過去完了", "時制"),
        ("長文読解", None), ("語彙", None), ("英作文", None), ("", None), (None, None),
    ]:
        got = eng(topic)
        check(f"英語 {topic!r} → {want}", got == want, got)
    for u in mod.GRAMMAR_UNITS:
        check(f"英語の単元名 {u} はそのまま", eng(u) == u, eng(u))
    chu = mod._chu_drill_for_topic
    for topic, want in [
        ("中学理科 天気", ("chugaku_rika", "天気", True)), ("天体：月", ("chugaku_rika", "天体", False)),
        ("be動詞・一般動詞", ("chugaku", "be動詞・一般動詞", False)), ("正負の数（累乗）", ("chugaku_math", "正負の数", False)),
        ("中学数学 正負の数", ("chugaku_math", "正負の数", True)), ("中学数学 時制", None),
        ("関係代名詞", ("chugaku", "関係代名詞", False)), ("歴史 古代", ("chugaku_shakai", "歴史 古代", False)),
        ("中学社会 歴史 古代", ("chugaku_shakai", "歴史 古代", True)), ("時制", ("chugaku", "時制", False)),
        ("過去形", None), ("説明的文章", None), ("長文読解", None), ("", None), (None, None),
    ]:
        got = chu(topic)
        check(f"中学 {topic!r} → {want}", got == want, got)
    for subj in mod._CHU_DRILL_SUBJECTS:
        lb = mod._GRAMMAR_SUBJECT_LABEL_JA[subj]
        bad = [u for u in mod._GRAMMAR_SUBJECT_UNIT_ORDER[subj]
               if chu(u) != (subj, u, False) or chu(f"{lb} {u}") != (subj, u, True)]
        check(f"{subj} の全単元が自分自身に対応 (前置き「{lb} 」つきは prefixed)", not bad, bad[:3])

    # ------------------------------------------------------------------
    print("\n[4] 学年の区分と科目 (_drill_subject_band_ok)")
    band_ok = mod._drill_subject_band_ok
    bands = ("kosei", "chugaku", "shougaku", "")
    matrix = {
        "english": ("kosei",), "math": ("kosei",), "english_long": ("kosei",), "physics": ("kosei",),
        "japanese": ("kosei",), "social": ("kosei",),
        "chugaku": ("chugaku",), "chugaku_math": ("chugaku",), "chugaku_rika": ("chugaku",),
        "chugaku_shakai": ("chugaku",), "chugaku_kokugo": ("chugaku",),
        "eiken": ("kosei", "chugaku"), "proficiency_test": (), "foo": (), "": (),
    }
    for subj, allowed in matrix.items():
        for b in bands:
            want = b in allowed
            check(f"band {b or '(判定できない)'} × 科目 {subj or '(空)'} → {want}", band_ok(subj, b) is want)
    rs = mod._ROUTINE_SUBJECTS_BY_BAND
    check("3日ドリルの科目は高校 = english/math・中学 = 中学の 5 教科だけ",
          set(rs) == {"kosei", "chugaku"} and set(rs["kosei"]) == {"english", "math"}
          and set(rs["chugaku"]) == set(mod._CHU_DRILL_SUBJECTS), rs)
    for b, subjs in rs.items():
        for s in subjs:
            check(f"3日ドリル {b} の {s}: 学年の区分に合い・許可リストがある",
                  band_ok(s, b) and bool(mod._auto_delivery_allowlist().get(s)))
    check("_CHU_DRILL_SUBJECTS == _GRAMMAR_SUBJECT_UNIT_ORDER の中学の科目",
          set(mod._CHU_DRILL_SUBJECTS) == {k for k in mod._GRAMMAR_SUBJECT_UNIT_ORDER if k.startswith("chugaku")})
    random.seed(7)
    pool = list(matrix)
    cross = [(s, b) for _ in range(200) for s in [random.choice(pool)] for b in [random.choice(bands)]
             if band_ok(s, b) and ((b == "kosei" and s.startswith("chugaku")) or (b == "chugaku" and s in ("english", "math", "english_long")))]
    check("ランダム 200 組で中高をまたぐ組み合わせが 1 つも通らない", not cross, cross[:3])

    # ------------------------------------------------------------------
    print("\n[5] AI の振り分け (_auto_delivery_ai_path と SQL の広めの絞り込み・全員がちょうど 1 経路)")
    now = datetime.datetime.now(datetime.timezone.utc)
    future = mod._utc_naive_iso(now + datetime.timedelta(days=3))
    past = mod._utc_naive_iso(now - datetime.timedelta(days=1))
    future_z = (now + datetime.timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    trials = {"なし": None, "期限切れ": past, "体験中": future, "体験中(Z)": future_z, "壊れた値": "not-a-date", "空": ""}
    path = mod._auto_delivery_ai_path
    for ad in (0, None, 1, 2):
        for tname, tv in trials.items():
            want = "ai" if not ad else ("ai" if tname.startswith("体験中") else "ai_nashi")
            check(f"ai_disabled={ad} × 体験 {tname} → {want}", path(ad, tv) == want, path(ad, tv))
    conn = mod.db(); c = conn.cursor()
    te = (now + datetime.timedelta(days=3650)).isoformat()
    fixture = {}
    k = 0
    for ad in (0, None, 1, 2):
        for tname, tv in trials.items():
            k += 1
            email = f"auto-part-{k}@example.org"
            c.execute("INSERT INTO students (name, email, status, trial_end, course, grade, goal, ai_disabled, ai_trial_until) "
                      "VALUES (?, ?, 'trial', ?, 'kokuritsu_nankan', '高校2年', '架空', ?, ?)",
                      (f"架空 振り分け{k}", email, te, ad, tv))
            c.execute("SELECT id FROM students WHERE email = ?", (email,))
            fixture[c.fetchone()["id"]] = (ad, tv)
    conn.commit()
    ids = tuple(fixture)
    ph = ",".join("?" * len(ids))

    def superset(p):
        c.execute(f"SELECT id FROM students WHERE id IN ({ph}) AND {mod._auto_delivery_ai_prefilter_sql(p)}", ids)
        return {r["id"] for r in c.fetchall()}

    sup_ai, sup_nashi = superset("ai"), superset("ai_nashi")
    c.execute(f"SELECT id, ai_disabled, ai_trial_until FROM students WHERE id IN ({ph})", ids)
    final = {r["id"]: path(r["ai_disabled"], r["ai_trial_until"]) for r in c.fetchall()}
    check("SQL の広めの絞り込み 2 つで全員を覆う", sup_ai | sup_nashi == set(ids), set(ids) - (sup_ai | sup_nashi))
    check("Python で 'ai' の生徒は全員 3日ドリル側の SQL に入る", all(s in sup_ai for s, p in final.items() if p == "ai"),
          [s for s, p in final.items() if p == "ai" and s not in sup_ai])
    check("Python で 'ai_nashi' の生徒は全員 クラス自動宿題側の SQL に入る",
          all(s in sup_nashi for s, p in final.items() if p == "ai_nashi"),
          [s for s, p in final.items() if p == "ai_nashi" and s not in sup_nashi])
    check("最終の振り分けは 1 人 1 経路 (ai / ai_nashi のどちらか)", set(final.values()) <= {"ai", "ai_nashi"} and len(final) == len(ids))
    orig_has = mod._students_has_ai_trial_until
    mod._students_has_ai_trial_until = lambda: False
    try:
        frag = mod._auto_delivery_ai_prefilter_sql("ai")
        check("ai_trial_until の列が無い環境では SQL に列名を書かない", "ai_trial_until" not in frag, frag)
    finally:
        mod._students_has_ai_trial_until = orig_has
    try:
        mod._auto_delivery_ai_prefilter_sql("both")
        check("知らない経路名は ValueError", False)
    except ValueError:
        check("知らない経路名は ValueError", True)

    # ------------------------------------------------------------------
    print("\n[6] 1 問ずつの抽出 (_auto_pick_reviewed_question_ids)")

    def addq(subject, unit, level, source, n, tag, passage_id=None, active=1):
        out = []
        for i in range(n):
            c.execute("INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source, active, passage_id, passage_seq) "
                      "VALUES (?, ?, ?, ?, ?, 0, '架空の解説', ?, ?, ?, ?) RETURNING id",
                      (subject, unit, level, f"架空の問題 {tag} {i} (   ).", json.dumps(["a", "b", "c", "d"]), source, active,
                       passage_id, (i + 1) if passage_id else None))
            out.append(int(c.fetchone()["id"]))
        return out

    rev = addq("english", "時制", "standard", "manual-drill-v1", 8, "rev-s") + addq("english", "時制", "advanced", "manual-drill-v2", 7, "rev-a")
    legacy = addq("english", "時制", "standard", "pool", 100, "pool")
    addq("english", "時制", "standard", "weakness_v1", 5, "weak")
    addq("english", "時制", "standard", "chu2grammar-20260709", 5, "chu2")
    addq("english", "時制", "standard", "pt-t1-q", 3, "ptest")
    addq("english", "時制", "basic", "manual-drill-v1", 6, "basic")
    addq("english", "時制", "standard", "manual-drill-v1", 4, "inactive", active=0)
    conn.commit()
    pick = mod._auto_pick_reviewed_question_ids
    res = pick(c, "english", "時制", ["standard", "advanced"], 10, {}, rng=random.Random(1))
    check("レビュー済みの在庫 15 (pool・weakness_v1・english の chu2grammar・pt-・基礎・止めた行は数えない)",
          res["reviewed_available"] == 15, res)
    check("10 問・すべてレビュー済み・重複なし", len(res["ids"]) == 10 and set(res["ids"]) <= set(rev) and len(set(res["ids"])) == 10, res)
    many = set()
    for s in range(30):
        many |= set(pick(c, "english", "時制", ["standard", "advanced"], 10, {}, rng=random.Random(s))["ids"])
    check("30 回選んでも pool / weakness_v1 / chu2grammar / pt- の行は 1 問も出ない",
          many <= set(rev) and not (many & set(legacy)), sorted(many - set(rev))[:5])
    r1 = pick(c, "english", "時制", ["standard", "advanced"], 10, {}, rng=random.Random(42))
    r2 = pick(c, "english", "時制", ["standard", "advanced"], 10, {}, rng=random.Random(42))
    check("同じ rng (seed) なら同じ問題を同じ順で選ぶ (dry-run と本番が一致する前提)", r1["ids"] == r2["ids"], (r1, r2))
    with Env("english=*"):
        rr = pick(c, "english", "時制", ["standard"], 10, {}, rng=random.Random(3))
        c.execute("SELECT id FROM grammar_questions WHERE source LIKE 'pt-%'")
        pt_ids = {int(r["id"]) for r in c.fetchall()}
        check("env english=* でも pt- の行は在庫に数えない", rr["reviewed_available"] == 8 + 100 + 5 + 5 and not (set(rr["ids"]) & pt_ids), rr)
    check("在庫が count に足りなければ配らない (ids は空)",
          pick(c, "english", "時制", ["standard", "advanced"], 16, {}, rng=random.Random(1))["ids"] == [])
    # 前に見た問題: 塾長のドリル (assignments) で 6 問・単元ドリルの解答で 4 問 = 10 問。入試道場の解答は同じ id でも除外しない
    sid = list(fixture)[0]
    seen_a, seen_b = rev[:6], rev[6:10]
    c.execute("INSERT INTO grammar_drills (subject, title, unit, level, question_ids, created_by) VALUES "
              "('english', '架空のドリル', '時制', 'standard', ?, 'admin') RETURNING id", (json.dumps(seen_a),))
    did = int(c.fetchone()["id"])
    c.execute("INSERT INTO grammar_drill_assignments (drill_id, student_id, status, score_total, assigned_at) "
              "VALUES (?, ?, 'completed', 6, '2026-09-01 05:30:00')", (did, sid))
    for i, q in enumerate(seen_b):
        c.execute("INSERT INTO question_attempts (student_id, source, exam_question_id, subject, topic, is_correct, created_at) "
                  "VALUES (?, 'grammar_drill', ?, 'english', '時制', 0, ?)", (sid, q, f"2026-10-0{i + 1} 10:00:00"))
    for q in rev[10:]:   # 入試道場の解答 (exam_questions の id 空間)。たまたま同じ数字でも除外しない
        c.execute("INSERT INTO question_attempts (student_id, source, exam_question_id, subject, topic, is_correct) "
                  "VALUES (?, 'dojo_drill', ?, 'english', '時制', 1)", (sid, q))
    conn.commit()
    seen = mod._student_seen_grammar_qids(c, sid)
    check("既出 = 配られたドリルの問題 ∪ 単元ドリルの解答 (入試道場の解答は入れない)",
          set(seen) == set(seen_a) | set(seen_b), sorted(seen))
    check("既出の日時は 'YYYY-MM-DD HH:MM:SS'", all(len(v) == 19 for v in seen.values()), seen)
    r = pick(c, "english", "時制", ["standard", "advanced"], 5, seen, rng=random.Random(5))
    check("見ていない問題が 5 問あれば、見ていない問題だけを出す", set(r["ids"]) == set(rev[10:]) and r["reused_seen"] == 0, r)
    r = pick(c, "english", "時制", ["standard", "advanced"], 10, seen, rng=random.Random(5))
    oldest = sorted(seen_a + seen_b, key=lambda q: (seen[q], q))[:5]
    check("足りなければ前に見た問題を古い順に足す (見ていない 5 + 最も古い 5・reused_seen=5)",
          set(r["ids"]) == set(rev[10:]) | set(oldest) and r["reused_seen"] == 5 and r["unseen_available"] == 5, (r, oldest))
    # 長文の設問 (passage_id あり) は 1 問ずつの抽出に出ない
    c.execute("INSERT INTO grammar_passages (subject, unit, level, title, body, source, body_hash, active) "
              "VALUES ('english', '時制', 'standard', '架空', '架空の本文', 'manual-drill-v1', 'h-eng', 1) RETURNING id")
    pq = addq("english", "時制", "standard", "manual-drill-v1", 5, "inpassage", passage_id=int(c.fetchone()["id"]))
    conn.commit()
    r = pick(c, "english", "時制", ["standard", "advanced"], 15, {}, rng=random.Random(1))
    check("長文の設問 (passage_id あり) は数えない・出さない", r["reviewed_available"] == 15 and not (set(r["ids"]) & set(pq)), r)
    # 数学: 科目まるごと・数学III を外す
    m1 = addq("math", "数学I 数と式", "standard", "mathwb-kI:1:1", 6, "m1")
    m3 = addq("math", "数学III 極限", "standard", "mathwb-k3:1:1", 6, "m3")
    addq("math", "数学I 数と式", "standard", "pool", 20, "mpool")
    conn.commit()
    r = pick(c, "math", "", ["standard", "advanced"], 6, {}, exclude_unit_prefixes=("数学III", "数学Ⅲ", "数III", "数Ⅲ"), rng=random.Random(2))
    check("数学まるごと: 数学III の単元と pool は出ない", set(r["ids"]) == set(m1) and r["reviewed_available"] == 6, r)
    r = pick(c, "math", "", ["standard", "advanced"], 12, {}, rng=random.Random(2))
    check("数学まるごと (除外なし): レビュー済み 12 問", set(r["ids"]) == set(m1) | set(m3), r)
    sql_text = []
    for f in (mod._auto_pick_reviewed_question_ids, mod._auto_reviewed_passages, mod._auto_pick_reviewed_passages):
        fn = ast.parse(textwrap.dedent(inspect.getsource(f))).body[0]
        body = fn.body[1:] if (fn.body and isinstance(fn.body[0], ast.Expr)
                               and isinstance(getattr(fn.body[0], "value", None), ast.Constant)) else fn.body   # docstring を除く
        for node in body:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                    sql_text.append(sub.value)
    sql_up = " ".join(sql_text).upper()
    check("自動の抽出の SQL に RANDOM() / LIMIT が無い (抽選は Python)",
          "SELECT" in sql_up and "RANDOM(" not in sql_up and "LIMIT" not in sql_up, sql_up[:300])
    check("CEO の抽出 (_grammar_pick_drill_question_ids / _grammar_pick_drill_passages) は変えていない (reviewed_only 引数なし)",
          "reviewed_only" not in inspect.signature(mod._grammar_pick_drill_question_ids).parameters
          and "reviewed_only" not in inspect.signature(mod._grammar_pick_drill_passages).parameters)

    # ------------------------------------------------------------------
    print("\n[7] 本文の抽出 (_auto_pick_reviewed_passages)")
    reading = json.load(open(os.path.join(SEED_DIR, "eiken_reading_pool_v1.json"), encoding="utf-8"))["passages"]
    for i in range(0, len(reading), 20):
        mod._RATE_LIMIT_STORE.clear()
        rr = client.post("/api/admin/grammar/import", json={"passages": reading[i:i + 20], "subject": "eiken", "dedup": True}, headers=H)
        if rr.status_code != 200 or not rr.json().get("ok"):
            check("英検の長文シードを CEO と同じ取込で入れる", False, rr.text[:300])
            break
    unit = "準1級 長文空所補充"
    n_unit = sum(1 for p in reading if p.get("unit") == unit)
    idx = mod._auto_reviewed_passages(c, "eiken", unit, ["standard"])
    check(f"英検 {unit}: シードの本文 {n_unit} 本がすべて自動配信できる", len(idx["passages"]) == n_unit and n_unit > 0,
          (len(idx["passages"]), idx["rejected"]))
    pr = mod._auto_pick_reviewed_passages(c, "eiken", unit, ["standard"], 2, {}, rng=random.Random(9))
    c.execute(f"SELECT id, passage_id, subject FROM grammar_questions WHERE id IN ({','.join('?' * len(pr['qids']))})", tuple(pr["qids"]))
    rows = c.fetchall()
    check("本文 2 本・設問はその 2 本のものだけ・科目は eiken",
          len(pr["passage_ids"]) == 2 and rows and {int(x["passage_id"]) for x in rows} == set(pr["passage_ids"])
          and {x["subject"] for x in rows} == {"eiken"}, pr)
    # 混ざった本文 (本文はレビュー済み・設問の 1 問が未レビュー)・本文が未レビュー・設問の科目違い・設問なし
    tu = "テスト用の長文単元"

    def addp(src, tag):
        c.execute("INSERT INTO grammar_passages (subject, unit, level, title, body, source, body_hash, active) "
                  "VALUES ('eiken', ?, 'standard', '架空', ?, ?, ?, 1) RETURNING id", (tu, f"架空の本文 {tag}", src, f"h-{tag}"))
        return int(c.fetchone()["id"])

    p_ok = [addp("eikenp1-test-ok", f"ok{i}") for i in range(3)]
    q_ok = {p: addq("eiken", tu, "standard", "eikenp1-test-ok", 3, f"okq{p}", passage_id=p) for p in p_ok}
    p_mix = addp("eikenp1-test-mixed", "mixed")
    addq("eiken", tu, "standard", "eikenp1-test-mixed", 2, "mixq", passage_id=p_mix)
    addq("eiken", tu, "standard", "pool", 1, "mixpool", passage_id=p_mix)
    p_body = addp("pool", "body")
    addq("eiken", tu, "standard", "eikenp1-test-body", 3, "bodyq", passage_id=p_body)
    p_subj = addp("eikenp1-test-subj", "subj")
    addq("english", tu, "standard", "eikenp1-test-subj", 3, "subjq", passage_id=p_subj)
    p_none = addp("eikenp1-test-none", "none")
    addq("eiken", tu, "standard", "eikenp1-test-none", 2, "noneq", passage_id=p_none, active=0)
    p_pt = addp("ptest:t1:S01", "pt")
    addq("eiken", tu, "standard", "eikenp1-test-pt", 2, "ptq", passage_id=p_pt)
    conn.commit()
    idx = mod._auto_reviewed_passages(c, "eiken", tu, ["standard"])
    check("レビュー済みの本文 3 本だけが残る", set(idx["passages"]) == set(p_ok), (sorted(idx["passages"]), idx["rejected"]))
    check("外した理由: 設問が未レビュー 2 (混ざった本文・設問の科目違い)・本文が未レビュー 2 (pool・ptest:)・設問なし 1",
          idx["rejected"] == {"unreviewed_question": 2, "unreviewed_body": 2, "no_question": 1}, idx["rejected"])
    for s in range(20):
        got = mod._auto_pick_reviewed_passages(c, "eiken", tu, ["standard"], 2, {}, rng=random.Random(s))["passage_ids"]
        if set(got) - set(p_ok):
            check("20 回選んでも外した本文は出ない", False, got)
            break
    else:
        check("20 回選んでも外した本文は出ない", True)
    # 前に見た本文は本文ごと避ける: p_ok[0] の 1 問 (古い) と p_ok[1] の 1 問 (新しい) を見た → 2 本なら p_ok[2] + p_ok[0]
    seen_p = {q_ok[p_ok[0]][1]: "2026-09-01 00:00:00", q_ok[p_ok[1]][0]: "2026-10-01 00:00:00"}
    r = mod._auto_pick_reviewed_passages(c, "eiken", tu, ["standard"], 2, seen_p, rng=random.Random(4))
    check("前に見た本文は本文ごと避け、足りなければ最後に見たのが古い本文から (p3 + p1・reused_seen=1)",
          set(r["passage_ids"]) == {p_ok[2], p_ok[0]} and r["reused_seen"] == 1 and r["unseen_available"] == 1, r)
    order_ok = all(r["qids"][i * 3:(i + 1) * 3] == q_ok[p] for i, p in enumerate(r["passage_ids"]))
    check("設問は本文ごとに passage_seq の順", order_ok, r)
    check("本文が足りなければ配らない (qids は空)",
          mod._auto_pick_reviewed_passages(c, "eiken", tu, ["standard"], 4, {}, rng=random.Random(1))["qids"] == [])

    # ------------------------------------------------------------------
    print("\n[8] GET /api/admin/grammar/source-inventory")
    r = client.get("/api/admin/grammar/source-inventory")
    check("認証なしは 401", r.status_code == 401, r.status_code)
    r = client.get("/api/admin/grammar/source-inventory", headers={"X-Cron-Secret": "test-cron-secret"})
    check("X-Cron-Secret で 200", r.status_code == 200, r.text[:200])
    r = client.get("/api/admin/grammar/source-inventory", headers=H)
    d = r.json() if r.status_code == 200 else {}
    check("管理者で 200・ok", r.status_code == 200 and d.get("ok") is True, r.text[:300])
    groups = {(g["subject"], g["source_group"]): g for g in d.get("groups") or []}
    check("english 'pool' のまとまりは自動配信できない (auto_ok=no)", groups.get(("english", "pool"), {}).get("auto_ok") == "no",
          groups.get(("english", "pool")))
    check("english manual-drill-v1 / v2 は auto_ok=yes",
          groups.get(("english", "manual-drill-v1"), {}).get("auto_ok") == "yes"
          and groups.get(("english", "manual-drill-v2"), {}).get("auto_ok") == "yes", sorted(groups)[:10])
    leg = {(x["subject"], x["source_group"]) for x in d.get("legacy_active") or []}
    check("legacy_active に english pool・weakness_v1・chu2grammar (english) が出る",
          {("english", "pool"), ("english", "weakness_v1"), ("english", "chu2grammar")} <= leg, sorted(leg))
    check("legacy_active に manual-drill-v1 は出ない", ("english", "manual-drill-v1") not in leg)
    check("止めた行は inactive に数える", groups.get(("english", "manual-drill-v1"), {}).get("inactive") == 4,
          groups.get(("english", "manual-drill-v1")))
    units = {(u["subject"], u["unit"]): u for u in d.get("auto_units") or []}
    t = units.get(("english", "時制"), {})
    check("auto_units: english 時制 = 標準 8・やや難 7・基礎 6 (長文の設問・pool は数えない)",
          t.get("reviewed") == {"basic": 6, "standard": 8, "advanced": 7}, t)
    check("auto_units: 英検の長文は本文の本数", units.get(("eiken", unit), {}).get("passages") == n_unit, units.get(("eiken", unit)))
    check("auto_units: テスト用の長文単元はレビュー済みの 3 本だけ", units.get(("eiken", tu), {}).get("passages") == 3, units.get(("eiken", tu)))
    check("allowlist と禁止を返す", d.get("allowlist", {}).get("english") == ["manual-drill-v1", "manual-drill-v2"]
          and "proficiency_test" in (d.get("deny_subjects") or []) and "pt-" in (d.get("deny_source_prefixes") or []), d.get("allowlist"))
    check("応答に生徒名やメールを含まない", "@example.org" not in r.text and "架空 振り分け" not in r.text)
    check("在庫照会は同期の def (イベントループで DB を待たない)",
          not inspect.iscoroutinefunction(mod.admin_grammar_source_inventory))
    check("出典のまとめ方", [mod._grammar_source_group(x) for x in
                          ("mathwb-ia:1:1", "eiken2-honban-r1-3", "eikenp1-mock-v1 S1-A", "manual-drill-v2", "", "chugaku-drill-v4")]
          == ["mathwb-ia", "eiken2-honban", "eikenp1-mock-v1", "manual-drill-v2", "(空)", "chugaku-drill-v4"])

    # ------------------------------------------------------------------
    print("\n[9] 実行記録の要約 (_compact_run_props) と自動配信の印 (_auto_created_by_sql)")
    summary = {
        "dry_run": False, "eligible": 80, "delivered": 60, "capped": 20, "cap": 60, "error": "全部の作成に失敗 " + "x" * 500,
        "delivered_students": [{"id": 1000 + i, "name": f"架空 生徒{i}", "email": f"auto-{i}@example.org", "subject": "english",
                                "unit": "時制", "levels": ["standard", "advanced"]} for i in range(60)],
        "skipped_grade_unknown": [{"id": 2000 + i, "name": f"架空 学年なし{i}", "grade": "その他"} for i in range(45)],
        "reasons": {f"no_reviewed_pool:subject{i}": i for i in range(80)},
        "band_counts": {"kosei": 50, "chugaku": 10},
        "notify": {"line": False, "email": False},
        "names": ["架空 生徒0"], "message": "架空 生徒1 さんほか",
    }
    props = mod._compact_run_props(summary)
    js = json.dumps(props, ensure_ascii=False)
    check("4000 字未満 (_record_scheduler_run が切らない)", len(js) < 4000, len(js))
    check("正しい JSON として読める", json.loads(js) == props)
    check("名前もメールも入らない", "架空" not in js and "@example.org" not in js, js[:300])
    check("error は残る", str(props.get("error", "")).startswith("全部の作成に失敗"), props.get("error"))
    check("数は残る", props.get("delivered") == 60 and props.get("eligible") == 80 and props.get("capped") == 20, props)
    check("生徒 id は 30 件まで・件数は全体", props.get("delivered_students_n") == 60
          and props.get("delivered_students_ids") == list(range(1000, 1030)), props.get("delivered_students_ids"))
    huge = dict(summary, reasons={f"r{i}-" + "y" * 50: i for i in range(500)},
                **{f"list{j}": [{"id": i} for i in range(100)] for j in range(30)})
    hp = mod._compact_run_props(huge)
    hjs = json.dumps(hp, ensure_ascii=False)
    check("大きな結果でも 4000 字未満に削り、error と数は残す", len(hjs) < 4000 and hp.get("error") and hp.get("delivered") == 60, len(hjs))
    check("dict でない結果でも落ちない", "error" in mod._compact_run_props(["x"]))
    for cb in ("admin", "weakness_routine_3d", "class_hw_auto:kosei:月曜3限 長文読解 Lv.1", "class_hw_auto:chugaku:x%_y",
               "diagnostic", "today_question", None, "class_hw_automatic"):
        c.execute("INSERT INTO grammar_drills (subject, title, unit, level, question_ids, created_by) VALUES "
                  "('english', '印のテスト', '時制', 'standard', '[]', ?)", (cb,))
    conn.commit()
    c.execute(f"SELECT created_by FROM grammar_drills WHERE title = '印のテスト' AND {mod._auto_created_by_sql()}")
    got = sorted(r["created_by"] for r in c.fetchall())
    check("自動配信の印 = 3日ドリルとクラス自動宿題だけ", got == sorted(["weakness_routine_3d", "class_hw_auto:kosei:月曜3限 長文読解 Lv.1",
                                                          "class_hw_auto:chugaku:x%_y"]), got)
    c.execute(f"SELECT COUNT(*) AS n FROM grammar_drills d WHERE d.title = '印のテスト' AND {mod._auto_created_by_sql('d.created_by')}")
    check("列名の別名 (d.created_by) でも使える", int(c.fetchone()["n"]) == 3)
    check("_ROUTINE_CREATED_BY は 3日ドリルの印と同じ", mod._ROUTINE_CREATED_BY == mod._WEAKNESS_ROUTINE_CREATED_BY == "weakness_routine_3d")

    # ------------------------------------------------------------------
    print("\n[10] 習熟度テストはどの自動配信にも出ない・英語長文は高校生だけ")
    review = {"protocol": "trillion-blind/v1", "all_agree": True, "solvers": [{"label": x, "kind": "ai", "date": "2026-10-21"} for x in "ABC"]}

    def long_passage(subject, unit, src_p, src_q, n):
        return {"subject": subject, "unit": unit, "level": "standard", "title": f"架空 {n}", "body": f"架空の本文 {subject} {n} ( 1 ).",
                "source": src_p, "questions": [{"stem": f"架空の設問 {n}-{k}", "choices": ["a", "b", "c", "d"], "answer": k % 4,
                                                "source": src_q.format(k=k)} for k in range(1, 4)]}

    pt_unit = "高校英語 習熟度テスト 第1回"
    # 出典が英語長文・英検の許可リストの形でも、科目が proficiency_test なら出さない (科目の禁止が先)
    pts = [long_passage("proficiency_test", pt_unit, f"englong:T{n}:P01", "el-T%d-P01-Q{k}" % n, n) for n in range(1, 4)]
    els = [long_passage("english_long", "長文 Lv.1", f"englong:L1S9{n}:P01", "el-L1S9%d-P01-Q{k}" % n, n) for n in range(1, 4)]
    for body in ({"subject": "proficiency_test", "passages": pts, "review": review},
                 {"subject": "english_long", "passages": els, "review": review}):
        mod._RATE_LIMIT_STORE.clear()
        rr = client.post("/api/admin/grammar/import", json=body, headers=H)
        check(f"{body['subject']} の本文 3 本を取込 (review つき)", rr.status_code == 200 and rr.json().get("passages_inserted") == 3, rr.text[:300])
    for env_v in (None, "english=*;proficiency_test=*;english_long=*"):
        with Env(env_v):
            r1 = mod._auto_pick_reviewed_question_ids(c, "proficiency_test", "", ["basic", "standard", "advanced"], 1, {}, rng=random.Random(1))
            r2 = mod._auto_pick_reviewed_passages(c, "proficiency_test", pt_unit, ["standard"], 1, {}, rng=random.Random(1))
            r3 = mod._auto_pick_reviewed_passages(c, "proficiency_test", "", None, 1, {}, rng=random.Random(1))
            check(f"習熟度テスト: 1 問ずつの抽出 0・本文の抽出 0 (単元指定・科目まるごと) (env={env_v!r})",
                  r1["ids"] == [] and r2["qids"] == [] and r2["reviewed_available"] == 0 and r3["qids"] == [], (r1, r2, r3))
            r4 = mod._auto_pick_reviewed_passages(c, "english_long", "長文 Lv.1", ["standard"], 1, {}, rng=random.Random(1))
            check(f"英語長文: 本文 1 本を抽出できる (env={env_v!r})", len(r4["passage_ids"]) == 1 and len(r4["qids"]) == 3, r4)
    check("学年の区分: 習熟度テストはどの区分にも出ない・英語長文は高校生だけ",
          not any(band_ok("proficiency_test", b) for b in bands) and band_ok("english_long", "kosei")
          and not any(band_ok("english_long", b) for b in ("chugaku", "shougaku", "")))
    check("3日ドリルの科目に英語長文も習熟度テストも無い",
          not ({"english_long", "proficiency_test"} & {s_ for v in mod._ROUTINE_SUBJECTS_BY_BAND.values() for s_ in v}))
    # 3日ドリルの計画: 英語長文・習熟度テストの弱点の行しか無い高校生には配らない
    c.execute("INSERT INTO students (name, email, status, grade, ai_disabled) VALUES ('架空 長文とテスト', 'auto-el-pt@example.org', "
              "'paid', '高校2年', 0) RETURNING id")
    sid10 = int(c.fetchone()["id"])
    for subj, topic in (("english_long", "長文 Lv.1"), ("proficiency_test", pt_unit)):
        c.execute("INSERT INTO student_weakness (student_id, subject, topic, question_count, qa_accuracy, qa_attempts) "
                  "VALUES (?, ?, ?, 10, 0.1, 10)", (sid10, subj, topic))
    conn.commit()
    c.execute("SELECT id, name, email, line_user_id, grade, ai_disabled, ai_trial_until FROM students WHERE id = ?", (sid10,))
    st10 = c.fetchone()
    for band in ("kosei", "chugaku"):
        reasons = {}
        plan = mod._weakness_routine_plan(c, st10, band, rng=random.Random(2), reasons=reasons)
        check(f"3日ドリルの計画 ({band}): 英語長文・習熟度テストの弱点からは配らない",
              not plan["ok"] and not any(t_["subject"] in ("english_long", "proficiency_test") for t_ in plan.get("tried") or []),
              (plan, reasons))
    conn.close()

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for f in FAILURES:
            print(f"   - {f}")
        return 1
    print("✅ PASS (自動配信の共通部品: レビュー済みだけ・中高の取り違えなし・AI の振り分けは 1 人 1 経路)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
