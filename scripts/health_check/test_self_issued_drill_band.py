#!/usr/bin/env python3
"""🔰 生徒が自分で始める「今日の1問」「はじめての実力チェック (初回診断)」の回帰テスト
(2026-10-15 塾長「中学生と高校生は問題の配信はミスらないように」+「自動で選ぶものはレビュー済みだけ」)。

背景: 2 つとも学年を見ずに english の全行 (exam_questions を分解した未レビューの古い行を含む) から ORDER BY RANDOM() で選んでいた。
mypage の「おかえり」と ?today=1 は中学生モードでも今日の1問を開くので、中学生に高校の英文法が出ていた。

固定する性質 (一時 SQLite・外部通信なし・生徒名とメールは架空 = 公開リポジトリ):
  [1] 今日の1問: 高校生と学年未入力 → 英文法 english・中学生 (「中２」も) → 中学英語 chugaku・小学生モード → 409 (理由の文つき)。
      問題はレビュー済みの出典だけ (pool・english の chu2grammar・weakness_v1・pt- は 40 回でも出ない)。基礎から先に出す。
      再利用は同じ科目の未完了の今日の1問だけ (前に出た英文法の 1 問を中学生に再利用しない)。レビュー済みが無ければ 503
  [2] 初回診断: 高校生と学年未入力 → 5 単元 × 2 問 (基礎 1 + 標準 1) がすべてレビュー済みの英文法。中学生・小学生モード → 409
  [3] ソース: 2 つの入口に ORDER BY RANDOM() が残っていない・判定は _self_issued_subject / _self_issued_reviewed_ids の 1 か所

実行:
    python3 scripts/health_check/test_self_issued_drill_band.py
    # exit 0 = PASS / 1 = FAIL
"""
import base64
import hashlib
import hmac
import importlib.util
import json
import os
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
LEGACY = ("pool", "chu2grammar-20260709", "weakness_v1", "pt-x-1", "")


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="self_issued_"), "test.db")
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
    spec = importlib.util.spec_from_file_location("aijuku_main_self_issued", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def student_token(mod, sid, hours=1):
    exp = int(time.time()) + hours * 3600
    payload = f"session.{sid}.{exp}"
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}.{sig}".encode()).decode().rstrip("=")


def main():
    print("🔰 今日の1問・初回診断: 学年で科目を分ける・レビュー済みだけ 回帰テスト\n")
    mod = load_main()
    src = open(MAIN_PY, encoding="utf-8").read()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app, raise_server_exceptions=False)
    api = Api(mod, client, {"Authorization": "Bearer " + admin_token(mod)})
    for fname, subj in (("grammar_drill_pool_v1.json", "english"), ("chugaku_drill_pool_v1.json", "chugaku")):
        t = import_like_ceo(api, "questions", load_seed(fname)["questions"], subj, 400)
        check(f"シード {fname} が入る", t["inserted"] > 0 and t["errors"] == 0, str(t)[:200])

    conn = mod.db(); c = conn.cursor()
    # 未レビューの古い行 (どれも基礎・標準。診断の 10 単元すべてに入れる = 選ばれやすい側に置く)
    for u in mod._DIAGNOSTIC_UNIT_PREFS:
        for srcname in LEGACY:
            for lv in ("basic", "standard"):
                for i in range(6):
                    c.execute("INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) "
                              "VALUES ('english', ?, ?, ?, ?, 0, '解説', ?)",
                              (u, lv, f"未レビューの架空の問題 {u} {srcname or 'blank'} {lv} {i} (   ).",
                               json.dumps(["a", "b", "c", "d"]), srcname))
    conn.commit()
    seq = [0]

    def make(grade):
        seq[0] += 1
        c.execute("INSERT INTO students (name, email, status, grade, ai_disabled) VALUES (?, ?, 'paid', ?, 0) RETURNING id",
                  (f"架空 生徒{seq[0]:02d}", f"si-{seq[0]:02d}@example.org", grade))
        sid = c.fetchone()["id"]
        conn.commit()
        return sid

    def post(path, sid):
        mod._RATE_LIMIT_STORE.clear()
        return client.post(path, json={}, headers={"Authorization": "Bearer " + student_token(mod, sid)})

    def drill(did):
        c.execute("SELECT subject, question_ids, created_by FROM grammar_drills WHERE id = ?", (did,))
        return dict(c.fetchone())

    def rows_of(ids):
        c.execute(f"SELECT id, subject, unit, level, source FROM grammar_questions WHERE id IN ({','.join('?' * len(ids))})", tuple(ids))
        return [dict(r) for r in c.fetchall()]

    def complete_all(sid):
        c.execute("UPDATE grammar_drill_assignments SET status = 'completed' WHERE student_id = ?", (sid,))
        conn.commit()

    print("\n[1] 今日の1問")
    cases = {"高校2年": "english", None: "english", "その他": "english", "中２": "chugaku", "中学3年": "chugaku"}
    for grade, want in cases.items():
        sid = make(grade)
        subjects, srcs, levels, codes = set(), set(), set(), set()
        for _ in range(20):
            r = post("/api/student/today-question/start", sid)
            codes.add(r.status_code)
            if r.status_code != 200:
                break
            d = drill(r.json()["drill_id"])
            subjects.add(d["subject"])
            for row in rows_of(json.loads(d["question_ids"])):
                subjects.add(row["subject"])
                srcs.add(row["source"])
                levels.add(row["level"])
            complete_all(sid)
        check(f"学年 {grade!r} → {want} の 1 問 (20 回・ドリルと問題の科目)", codes == {200} and subjects == {want}, (codes, subjects))
        check(f"学年 {grade!r}: 全問レビュー済みの出典", srcs and all(mod._auto_delivery_source_ok(want, s_) for s_ in srcs), srcs)
        check(f"学年 {grade!r}: 基礎から出す", levels == {"basic"}, levels)
    c.execute("SELECT source FROM grammar_questions WHERE subject = 'english' AND level = 'basic' AND active = 1")
    n_legacy = sum(1 for r_ in c.fetchall() if not mod._auto_delivery_source_ok("english", r_["source"]))
    check("(未レビューの古い行が英文法の基礎に 300 問ある = このテストが意味を持つ)", n_legacy == 300, n_legacy)
    sid = make("小６")
    r = post("/api/student/today-question/start", sid)
    check("小学生モード → 409 (理由の文: 画面は alert で出す)", r.status_code == 409 and "小学生" in r.json().get("detail", ""), (r.status_code, r.text[:200]))
    # 中学生に前の英文法の今日の1問 (2026-10-15 より前に出たもの) が未完了で残っていても、それを再利用しない
    sid = make("中1")
    c.execute("INSERT INTO grammar_drills (subject, title, unit, level, question_ids, created_by) VALUES "
              "('english', '📝 今日の1問', '今日の1問', 'standard', '[1]', 'today_question') RETURNING id")
    old = c.fetchone()["id"]
    c.execute("INSERT INTO grammar_drill_assignments (drill_id, student_id, status) VALUES (?, ?, 'open')", (old, sid))
    conn.commit()
    r = post("/api/student/today-question/start", sid)
    j = r.json() if r.status_code == 200 else {}
    check("中学生: 前の英文法の今日の1問は再利用せず、中学英語の 1 問を新しく出す",
          r.status_code == 200 and j.get("drill_id") != old and not j.get("reused") and drill(j["drill_id"])["subject"] == "chugaku", j)
    r2 = post("/api/student/today-question/start", sid)
    check("同じ科目の未完了は再利用する (二重発行しない)", r2.status_code == 200 and r2.json().get("drill_id") == j.get("drill_id")
          and r2.json().get("reused") is True, r2.text[:200])
    c.execute("SELECT id, source FROM grammar_questions WHERE subject = 'english' AND active = 1")
    reviewed = [r_["id"] for r_ in c.fetchall() if mod._auto_delivery_source_ok("english", r_["source"])]
    c.execute(f"UPDATE grammar_questions SET active = 0 WHERE id IN ({','.join('?' * len(reviewed))})", tuple(reviewed))
    conn.commit()
    sid = make("高校1年")
    r = post("/api/student/today-question/start", sid)
    check("レビュー済みの英文法が 0 問 → 503 (未レビューの行では埋めない)", r.status_code == 503, (r.status_code, r.text[:200]))
    c.execute(f"UPDATE grammar_questions SET active = 1 WHERE id IN ({','.join('?' * len(reviewed))})", tuple(reviewed))
    conn.commit()

    print("\n[2] はじめての実力チェック (初回診断)")
    all_src, ok_shape = set(), True
    for grade in ("高校3年", None, "既卒", "高２", "高校1年", "高3"):
        sid = make(grade)
        r = post("/api/student/diagnostic/start", sid)
        if r.status_code != 200:
            ok_shape = False
            check(f"学年 {grade!r}: 200", False, (r.status_code, r.text[:200]))
            continue
        ids = json.loads(drill(r.json()["drill_id"])["question_ids"])
        rows = rows_of(ids)
        all_src |= {x["source"] for x in rows}
        units = {}
        for x in rows:
            units.setdefault(x["unit"], []).append(x["level"])
        ok_shape = ok_shape and len(ids) == 10 and all(x["subject"] == "english" for x in rows) and len(units) == 5 \
            and all(sorted(v) == ["basic", "standard"] for v in units.values())
    check("高校生と学年未入力: 5 単元 × (基礎 1 + 標準 1) = 10 問の英文法", ok_shape)
    check("全問レビュー済みの出典 (pool・chu2grammar・weakness_v1・pt-・空は出ない)",
          all_src and all(mod._auto_delivery_source_ok("english", s_) for s_ in all_src) and not (all_src & set(LEGACY)), all_src)
    for grade in ("中２", "中学1年", "中三", "小６", "中学受験"):
        sid = make(grade)
        r = post("/api/student/diagnostic/start", sid)
        check(f"学年 {grade!r} → 409 (高校の英文法の診断は出さない)", r.status_code == 409 and r.json().get("detail"), (r.status_code, r.text[:200]))
    c.execute("SELECT COUNT(*) AS n FROM grammar_drills d JOIN grammar_drill_assignments a ON a.drill_id = d.id "
              "JOIN students s ON s.id = a.student_id WHERE d.created_by = 'diagnostic' AND (s.grade LIKE '%中%' OR s.grade LIKE '%小%')")
    check("中学生・小学生に診断のドリルは 1 本も作られていない", c.fetchone()["n"] == 0)

    print("\n[3] ソース")
    for fn in ("def student_diagnostic_start", "def student_today_question_start"):
        blk = src[src.index(fn):][:6000]
        blk = blk[:blk.index("\n@app.")] if "\n@app." in blk else blk
        check(f"{fn[4:]}: ORDER BY RANDOM() が残っていない・_self_issued_subject / _self_issued_reviewed_ids を使う",
              "ORDER BY RANDOM()" not in blk and "_self_issued_subject(student)" in blk and "_self_issued_reviewed_ids(" in blk)
    check("_self_issued_subject は画面と同じ _student_mode_from_grade (未入力は高校生)",
          mod._self_issued_subject({"grade": None}) == "english" and mod._self_issued_subject({"grade": "中Ⅲ"}) == "chugaku"
          and mod._self_issued_subject({"grade": "小学5年"}) == "")
    conn.close()

    print()
    if FAILURES:
        print(f"❌ FAIL ({len(FAILURES)} 件)")
        for f in FAILURES:
            print("   -", f)
        sys.exit(1)
    print("✅ PASS (今日の1問・初回診断: 学年で科目を分ける・レビュー済みだけ)")


if __name__ == "__main__":
    main()
