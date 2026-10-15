#!/usr/bin/env python3
"""📖 英語長文 (科目 english_long・長文読解クラス用) の取込と配信の回帰テスト (2026-10-15 塾長決定)。

英語長文は Codex が書いた手元のファイルを取込スクリプト (scripts/drill_import) で入れる別科目。seed-data には置かない。
english に混ぜない (今日の1問・初回診断・3日ドリル・弱点 TOP3 が english を直書きしている) ので、自動で出るのは
長文クラスのクラス自動宿題 (高校生) だけ。取込はサーバが盲検 3 名の記録 (review) を必須にする。

  (1) 科目の表: 別名「英語長文」→ english_long・「長文」「長文読解」は別名にしない・ラベル・単元 3 つ
  (2) 取込: review が無い / 足りない → 422 で 0 行・review ありで本文と設問が入る・questions[] (1 問ずつ) は 422・level は standard
  (3) 単元名の綴り違い (「長文Lv.1」) は errors + unknown_units (all_or_nothing なら全部取り消し)
  (4) dry_run は数えるだけ (行数が変わらない)
  (5) all_or_nothing: 範囲外の answer を含む本文が 1 本でもあれば ok:false で 0 行・同じ set_id に新しい本文 → ok:false・
      同じ set_id を別の単元で → ok:false・同じ要求の再送は already_imported で 0 行
  (6) 単元一覧: 3 単元 (在庫 0 も)・本文の本数
  (7) CEO の配信: 本文 2 本 (既定)・本文の選び方はランダムのまま (12 回で 2 通り以上)
  (8) 生徒の取得 (答えは伏せる)・提出 → question_attempts は subject='english_long'・topic=単元 / 弱点 TOP3 に english_long は出ない
  (9) 英語長文しか無い DB: 今日の1問・初回診断は 503・3日ドリルは配らない (not_routine_subject)・1 問ずつの抽出は 0 問
  (10) AIなし枠の生徒にも配ったドリルが一覧に出る (許可集合の範囲内)
  (11) 自動配信: 出典 el- / englong: は許可リストを通る・高校生だけ (_drill_subject_band_ok)・本文の抽出 (_auto_pick_reviewed_passages)
  (12) CEO の配信済み一覧 subject=english_long・events 'grammar_import_review' (名前なし)・お知らせのメールの件名

実行:
    python3 scripts/health_check/test_english_long_drill.py
    # exit 0 = PASS / 1 = FAIL

外部通信はしない。DB は一時 SQLite。生徒名・メールは架空 (公開リポジトリ)。
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import json
import os
import random
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []
CIRCLED = "①②③④⑤⑥⑦⑧"
REVIEW = {"protocol": "trillion-blind/v1", "all_agree": True, "validator": "validate_drill_import/v1",
          "file_sha256": "0" * 64, "kind": "english_long", "set_id": "L1S001",
          "solvers": [{"label": "A", "kind": "ai", "model": "架空のモデル", "date": "2026-10-21"},
                      {"label": "B", "kind": "ai", "date": "2026-10-21"},
                      {"label": "C", "kind": "ai", "date": "2026-10-21"}]}


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="englong_"), "test.db")
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
    for k in ("AUTO_DELIVERY_REVIEWED_SOURCES", "HOMEWORK_NOTIFY_LINE", "PTEST_FEEDS_WEAKNESS"):
        os.environ.pop(k, None)
    os.environ["HOMEWORK_NOTIFY_EMAIL"] = "off"   # 配信のたびのお知らせ (メール) は回さない。件名は [12] で直接確かめる
    spec = importlib.util.spec_from_file_location("aijuku_main_englong", MAIN_PY)
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
            for t in ("grammar_passages", "grammar_questions", "grammar_drills", "grammar_drill_assignments")}


def passage(set_id, n, unit="長文 Lv.1", nq=4):
    """取込スクリプトが送る形 (answer は 0 始まり・出典は el-<set_id>-<qid> / englong:<set_id>:<pid>)。中身は架空。"""
    pid = f"P{n:02d}"
    body = (f"[1] Story {set_id}-{n}: when the small town library in this fictional story closed for repairs, "
            f"many residents could no longer reach the building. ( 1 ), the staff began delivering books by bicycle.\n\n"
            f"[2] The idea spread to {n + 2} nearby towns. ( 2 ) volunteers joined, and the service became popular.")
    qs = []
    for k in range(1, nq + 1):
        ans = (n + k) % 4
        choices = [f"choice {set_id} {n}-{k} {x}" for x in "abcd"]
        qs.append({"stem": f"( {k} ) に入れるのに最も適切なものを選びなさい。" if k <= 2 else f"本文の内容に合うもの ({k})",
                   "choices": choices, "answer": ans,
                   "explanation": f"正解 {CIRCLED[ans]} {choices[ans]}\n【根拠】架空の根拠\n【訳】架空の訳\n【他の選択肢】\n…",
                   "source": f"el-{set_id}-{pid}-Q{k}"})
    return {"subject": "english_long", "unit": unit, "level": "standard", "title": f"Fictional Story {n}",
            "body": body, "body_ja": f"架空の全訳 {set_id}-{n}", "source": f"englong:{set_id}:{pid}", "questions": qs}


def payload(passages, review=REVIEW, **kw):
    out = {"subject": "english_long", "dedup": True, "all_or_nothing": True, "passages": passages}
    if review is not None:
        out["review"] = review
    out.update(kw)
    return out


def main():
    print("📖 英語長文 (english_long) 取込・配信 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app, raise_server_exceptions=False)
    adm = {"Authorization": "Bearer " + admin_token(mod)}

    def imp(body):
        mod._RATE_LIMIT_STORE.clear()
        r = client.post("/api/admin/grammar/import", json=body, headers=adm)
        return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else {})

    # ------------------------------------------------------------------
    print("[1] 科目の表")
    canon = mod._canon_grammar_subject
    check("「英語長文」「english_long」「english long」→ english_long",
          canon("英語長文") == canon("english_long") == canon("english long") == "english_long")
    check("「長文」「長文読解」は別名にしない (入試道場の「長文読解」が english_long に化けない)",
          canon("長文") == "" and canon("長文読解") == "", (canon("長文"), canon("長文読解")))
    check("弱点集計の科目キーも「長文読解」のまま", mod._weakness_subject_key("長文読解") == "長文読解")
    check("ラベルは「英語長文」", mod._grammar_subject_label_ja("english_long") == "英語長文")
    check("単元は 3 つ (長文 Lv.1 / 長文 Lv.2 / 国公立 長文)",
          mod._GRAMMAR_SUBJECT_UNIT_ORDER.get("english_long") == ["長文 Lv.1", "長文 Lv.2", "国公立 長文"])
    check("本文型だけ・盲検の記録が要る科目", "english_long" in mod._PASSAGE_ONLY_SUBJECTS and "english_long" in mod._REVIEW_REQUIRED_SUBJECTS)
    check("解答の記録先は english_long のまま (chugaku に寄せない)", mod._drill_attempt_subject("english_long") == "english_long")
    check("週次レポートの科目名も「英語長文」", mod._weekly_subject_label("english_long") == "英語長文")

    # ------------------------------------------------------------------
    print("\n[2] 取込 (review 必須・本文型だけ)")
    before = counts(mod)
    code, d = imp(payload([passage("L1S001", 1)], review=None))
    check("review が無い → 422・何も入らない", code == 422 and counts(mod) == before, (code, d))
    for label, rv in (("protocol 違い", dict(REVIEW, protocol="other/v1")),
                      ("解き手 2 名", dict(REVIEW, solvers=REVIEW["solvers"][:2])),
                      ("日付の無い解き手", dict(REVIEW, solvers=[dict(s, date="") for s in REVIEW["solvers"]])),
                      ("同じ label の解き手 3 名", dict(REVIEW, solvers=[dict(s, label="A") for s in REVIEW["solvers"]])),
                      ("all_agree が false", dict(REVIEW, all_agree=False)),
                      ("all_agree が文字列 'true'", dict(REVIEW, all_agree="true")),
                      ("review が文字列", "ok")):
        code, d = imp(payload([passage("L1S001", 1)], review=rv))
        check(f"review の {label} → 422・何も入らない", code == 422 and counts(mod) == before, (code, d))
    code, d = imp({"subject": "english_long", "questions": [
        {"unit": "長文 Lv.1", "stem": "x ( ).", "choices": ["a", "b"], "answer": 0, "source": "el-X-P01-Q1"}], "review": REVIEW})
    check("subject=english_long の questions[] (1 問ずつ) → 422", code == 422 and counts(mod) == before, (code, d))
    code, d = imp({"questions": [{"subject": "英語長文", "unit": "長文 Lv.1", "stem": "y ( ).", "choices": ["a", "b"], "answer": 0}]})
    check("問ごとの subject「英語長文」の questions[] も 422", code == 422 and counts(mod) == before, (code, d))
    ps = [passage("L1S001", n) for n in range(1, 7)]
    ps[0]["level"] = "advanced"
    code, d = imp(payload(ps))
    check("review ありで本文 6 本・設問 24 問が入る (ok・errors 0)",
          code == 200 and d.get("ok") is True and d.get("passages_inserted") == 6 and d.get("inserted") == 24
          and d.get("errors") == 0 and d.get("already_imported") is False and d.get("dry_run") is False, d)
    rows = q(mod, "SELECT DISTINCT level FROM grammar_passages WHERE subject = 'english_long'")
    check("level は standard にそろえる (advanced で送っても)", [r["level"] for r in rows] == ["standard"], rows)
    rows = q(mod, "SELECT DISTINCT level FROM grammar_questions WHERE subject = 'english_long'")
    check("設問の level も standard", [r["level"] for r in rows] == ["standard"], rows)
    rows = q(mod, "SELECT COUNT(*) AS n FROM grammar_questions WHERE subject = 'english_long' AND passage_id IS NULL")
    check("英語長文の設問はすべて本文に紐づく (passage_id IS NULL が 0 行)", rows[0]["n"] == 0, rows)
    rows = q(mod, "SELECT source FROM grammar_questions WHERE subject = 'english_long' ORDER BY id LIMIT 1")
    check("設問の出典は el-<set_id>-<qid>", rows and rows[0]["source"] == "el-L1S001-P01-Q1", rows)
    ev = q(mod, "SELECT props, session_id FROM events WHERE name = 'grammar_import_review'")
    pj = json.loads(ev[0]["props"]) if ev else {}
    check("events 'grammar_import_review' が 1 行 (科目・単元・本数・set_id の接頭辞・盲検の要約)",
          len(ev) == 1 and ev[0]["session_id"] == "admin" and pj.get("subjects") == ["english_long"]
          and pj.get("units") == ["長文 Lv.1"] and pj.get("passages_inserted") == 6 and pj.get("inserted") == 24
          and pj.get("source_prefix") == ["englong:L1S001:"] and pj.get("review", {}).get("all_agree") is True
          and [s["label"] for s in pj.get("review", {}).get("solvers", [])] == ["A", "B", "C"], ev)
    check("events の要約にモデル名などの自由記述を入れない", "架空のモデル" not in (ev[0]["props"] if ev else ""), ev)

    # ------------------------------------------------------------------
    print("\n[3] 単元名の綴り違い")
    bad = passage("L1S002", 1, unit="長文Lv.1")
    code, d = imp(payload([bad], all_or_nothing=False))
    check("「長文Lv.1」(空白なし) は入れずに errors 1・unknown_units", code == 200 and d.get("errors") == 1
          and d.get("passages_inserted") == 0 and (d.get("unknown_units") or [{}])[0].get("unit") == "長文Lv.1", d)
    before = counts(mod)
    code, d = imp(payload([passage("L1S002", 2), bad]))
    check("all_or_nothing: 綴り違いが 1 本あれば ok:false・前の正しい本文も入らない",
          code == 200 and d.get("ok") is False and d.get("reason") == "unknown_unit" and d.get("rejected_index") == 1
          and counts(mod) == before, d)

    # ------------------------------------------------------------------
    print("\n[4] dry_run")
    before = counts(mod)
    ev_before = q(mod, "SELECT COUNT(*) AS n FROM events")[0]["n"]
    code, d = imp(payload([passage("L1S003", n, unit="長文 Lv.2") for n in range(1, 4)], dry_run=True))
    check("dry_run: 本文 3 本・設問 12 問と数える・dry_run: true",
          code == 200 and d.get("ok") is True and d.get("dry_run") is True and d.get("passages_inserted") == 3 and d.get("inserted") == 12, d)
    check("dry_run: 行数が変わらない (本文・設問・ドリル)・events も書かない",
          counts(mod) == before and q(mod, "SELECT COUNT(*) AS n FROM events")[0]["n"] == ev_before, (before, counts(mod)))

    # ------------------------------------------------------------------
    print("\n[5] all_or_nothing・まとまりの照合・再送")
    broken = passage("L1S004", 2)
    broken["questions"][1]["answer"] = 4   # 4 択で 4 = 範囲外
    before = counts(mod)
    code, d = imp(payload([passage("L1S004", 1), broken, passage("L1S004", 3)]))
    check("範囲外の answer を含む本文が 1 本あれば ok:false・0 行 (rejected_index 1)",
          code == 200 and d.get("ok") is False and d.get("rejected_index") == 1 and d.get("reason") == "invalid_question"
          and counts(mod) == before, d)
    code, d = imp(payload([passage("L1S004", 1), broken, passage("L1S004", 3)], all_or_nothing=False))
    check("all_or_nothing なし (CEO の補充ボタンと同じ) は壊れた本文だけ skip",
          code == 200 and d.get("ok") is True and d.get("passages_inserted") == 2 and d.get("passages_skipped") == 1, d)
    before = counts(mod)
    code, d = imp(payload([passage("L1S001", n) for n in range(1, 7)]))
    check("同じ要求の再送は already_imported: true・0 行", code == 200 and d.get("ok") is True and d.get("already_imported") is True
          and d.get("passages_inserted") == 0 and d.get("passages_skipped") == 6 and counts(mod) == before, d)
    code, d = imp(payload([passage("L1S001", n) for n in range(1, 8)]))
    check("取込済みの set_id に新しい本文 (7 本目) を足す要求は ok:false (group_exists)・0 行",
          code == 200 and d.get("ok") is False and d.get("reason") == "group_exists" and "L1S001" in (d.get("detail") or "")
          and counts(mod) == before, d)
    code, d = imp(payload([passage("L1S001", 1, unit="長文 Lv.2")]))
    check("同じ set_id の本文を別の単元で入れ直す要求も ok:false (同じ本文が 2 つの単元に入らない)",
          code == 200 and d.get("ok") is False and d.get("reason") == "group_exists" and counts(mod) == before, d)
    code, d = imp(payload([passage("L1S001", 1)], dedup=False))
    check("dedup: false でも英語長文の本文の重複は見る (0 行)", code == 200 and d.get("passages_inserted") == 0 and counts(mod) == before, d)

    # ------------------------------------------------------------------
    print("\n[6] 単元一覧")
    r = client.get("/api/admin/grammar/units", params={"subject": "english_long"}, headers=adm)
    units = r.json().get("units", []) if r.status_code == 200 else []
    check("3 単元が並び順どおり (在庫 0 の 国公立 長文 も出る)", [u["unit"] for u in units] == ["長文 Lv.1", "長文 Lv.2", "国公立 長文"], units)
    by = {u["unit"]: u for u in units}
    check("本文の本数: 長文 Lv.1 = 8 (L1S001 の 6 + L1S004 の 2)・長文 Lv.2 = 0・国公立 長文 = 0",
          by.get("長文 Lv.1", {}).get("passages") == 8 and by.get("長文 Lv.2", {}).get("passages") == 0
          and by.get("国公立 長文", {}).get("passages") == 0, {k: v.get("passages") for k, v in by.items()})

    # ------------------------------------------------------------------
    print("\n[7] CEO の配信 (本文単位・ランダムのまま)")
    seq = [0]

    def make(grade="高校2年", ai_disabled=0, status="paid"):
        seq[0] += 1
        conn = mod.db(); c = conn.cursor()
        c.execute("INSERT INTO students (name, email, status, grade, ai_disabled) VALUES (?, ?, ?, ?, ?) RETURNING id",
                  (f"架空 長文{seq[0]:02d}", f"englong-{seq[0]:02d}@example.org", status, grade, ai_disabled))
        sid = c.fetchone()["id"]
        conn.commit(); conn.close()
        mod._AI_DISABLED_CACHE.pop(sid, None)
        return sid

    sid = make()
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar-drill/create", json={"subject": "english_long", "unit": "長文 Lv.1", "student_ids": [sid]}, headers=adm)
    d = r.json() if r.status_code == 200 else {}
    check("本文の本数を送らない CEO の配信は本文 2 本 (既定)・題名「長文 Lv.1ドリル（本文2本・8問）」",
          r.status_code == 200 and d.get("passage_count") == 2 and d.get("question_count") == 8
          and d.get("title") == "長文 Lv.1ドリル（本文2本・8問）" and d.get("already_taken") == [], d)
    drill1 = d.get("drill_id")
    sets = set()
    for i in range(12):
        mod._RATE_LIMIT_STORE.clear()
        r = client.post("/api/admin/grammar-drill/create", json={"subject": "english_long", "unit": "長文 Lv.1", "passage_count": 2,
                                                                 "student_ids": [sid]}, headers=adm)
        sets.add(tuple(r.json().get("passage_ids") or []) if r.status_code == 200 else None)
    check("12 回作ると本文の組み合わせ・順が 2 通り以上 (英語長文の本文の順はランダムのまま)", len(sets) >= 2 and None not in sets, sets)

    # ------------------------------------------------------------------
    print("\n[8] 生徒の取得・提出・弱点 TOP3")
    tok = {"Authorization": "Bearer " + student_token(mod, sid)}
    mod._RATE_LIMIT_STORE.clear()
    r = client.get(f"/api/student/grammar-drill/{drill1}", headers=tok)
    g = r.json() if r.status_code == 200 else {}
    qs = g.get("questions") or []
    check("取得: 8 問・本文 2 本・解く前は答えと解説と全訳を返さない",
          r.status_code == 200 and len(qs) == 8 and len(g.get("passages") or {}) == 2
          and all("answer" not in x and "explanation" not in x for x in qs)
          and all("body_ja" not in v for v in (g.get("passages") or {}).values()), r.text[:200])
    mod._RATE_LIMIT_STORE.clear()
    r = client.post(f"/api/student/grammar-drill/{drill1}/submit", json={"answers": {str(x["question_id"]): 0 for x in qs}}, headers=tok)
    s = r.json() if r.status_code == 200 else {}
    check("提出: 200・8 問・subject は english_long", r.status_code == 200 and s.get("score_total") == 8 and s.get("subject") == "english_long",
          r.text[:200])
    rows = q(mod, "SELECT subject, topic, COUNT(*) AS n FROM question_attempts WHERE student_id = ? GROUP BY subject, topic", (sid,))
    check("question_attempts は subject='english_long'・topic='長文 Lv.1' で 8 行",
          rows == [{"subject": "english_long", "topic": "長文 Lv.1", "n": 8}], rows)
    mod._run_weakness_aggregation()
    w = q(mod, "SELECT subject, topic FROM student_weakness WHERE student_id = ?", (sid,))
    check("弱点集計は英語長文の解答を読む (student_weakness に english_long の行)", any(x["subject"] == "english_long" for x in w), w)
    mod._RATE_LIMIT_STORE.clear()
    r = client.get("/api/student/weakness-top3", params={"student_id": sid}, headers=tok)
    t3 = r.json() if r.status_code == 200 else {}
    check("弱点 TOP3 に english_long は出ない (推薦プールが無い・英検と同じ扱い)",
          r.status_code == 200 and "english_long" not in json.dumps(t3, ensure_ascii=False), r.text[:300])
    excl = mod._weakness_top3_exclude_sql()
    check("弱点 TOP3・週次プリントの科目範囲は eiken・english_long・proficiency_test を外す",
          all(f"'{x}'" in excl for x in ("eiken", "english_long", "proficiency_test")) and "NOT IN" in excl, excl)

    # ------------------------------------------------------------------
    print("\n[9] 英語長文しか無い DB では自動・自己発行の経路に出ない")
    sid9 = make()
    tok9 = {"Authorization": "Bearer " + student_token(mod, sid9)}
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/student/today-question/start", headers=tok9)
    check("今日の1問 → 503 (英語長文の設問は出さない)", r.status_code == 503, (r.status_code, r.text[:200]))
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/student/diagnostic/start", headers=tok9)
    check("初回診断 → 503", r.status_code == 503, (r.status_code, r.text[:200]))
    ex(mod, "INSERT INTO student_weakness (student_id, subject, topic, question_count, qa_accuracy, qa_attempts) "
            "VALUES (?, 'english_long', '長文 Lv.1', 10, 0.2, 10)", (sid9,))
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT id, name, email, line_user_id, grade, ai_disabled, ai_trial_until FROM students WHERE id = ?", (sid9,))
    st = c.fetchone()
    reasons = {}
    p = mod._weakness_routine_plan(c, st, "kosei", rng=random.Random(1), reasons=reasons)
    check("3日ドリルは英語長文の弱点から配らない (not_routine_subject:english_long)",
          not p["ok"] and reasons.get("not_routine_subject:english_long") == 1, (p, reasons))
    single = mod._grammar_pick_drill_question_ids(c, "english_long", "", True, ["basic", "standard", "advanced"], 5, None)
    check("1 問ずつの抽出 (CEO の科目まるごと) は英語長文の設問を拾わない", single == [], single)
    auto_single = mod._auto_pick_reviewed_question_ids(c, "english_long", "", ["standard"], 1, {}, rng=random.Random(1))
    check("自動配信の 1 問ずつの抽出も 0 問 (本文の設問は本文ごと)", auto_single["ids"] == [] and auto_single["reviewed_available"] == 0, auto_single)
    conn.close()
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/weakness-drill-routine/run", json={"dry_run": True, "student_id": sid9}, headers={"X-Cron-Secret": "test-cron-secret"})
    dj = r.json() if r.status_code == 200 else {}
    check("3日ドリルの dry-run: 配る生徒 0", r.status_code == 200 and dj.get("delivered") == 0, r.text[:300])

    # ------------------------------------------------------------------
    print("\n[10] AIなし枠の生徒")
    sid10 = make(ai_disabled=1)
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar-drill/create", json={"subject": "english_long", "unit": "長文 Lv.1", "passage_count": 1,
                                                             "student_ids": [sid10]}, headers=adm)
    did10 = r.json().get("drill_id") if r.status_code == 200 else None
    mod._RATE_LIMIT_STORE.clear()
    r = client.get("/api/student/grammar-drills", headers={"Authorization": "Bearer " + student_token(mod, sid10)})
    items = r.json().get("items", []) if r.status_code == 200 else []
    check("AIなし枠 (ai_disabled=1) の生徒にも配った英語長文が一覧に出る", r.status_code == 200 and did10 in [x.get("drill_id") for x in items],
          (r.status_code, r.text[:200]))

    # ------------------------------------------------------------------
    print("\n[11] 自動配信 (クラス自動宿題の長文クラスが使う部品)")
    ok_src = mod._auto_delivery_source_ok
    for src, want in (("el-L1S001-P01-Q1", True), ("englong:L1S001:P01", True), ("pool", False), ("", False),
                      ("manual-drill-v1", False), ("pt-T1-Q01", False), ("ptest:T1:S01", False)):
        check(f"english_long の出典 {src!r} → {want}", ok_src("english_long", src) is want)
    check("英語長文は高校生だけ (_drill_subject_band_ok)", mod._drill_subject_band_ok("english_long", "kosei")
          and not any(mod._drill_subject_band_ok("english_long", b) for b in ("chugaku", "shougaku", "")))
    check("3日ドリルの科目ではない", "english_long" not in mod._ROUTINE_SUBJECTS_BY_BAND["kosei"])
    conn = mod.db(); c = conn.cursor()
    idx = mod._auto_reviewed_passages(c, "english_long", "長文 Lv.1", ["standard"])
    check("取り込んだ本文 8 本はすべて自動配信できる (本文と全設問がレビュー済み)", len(idx["passages"]) == 8, idx["rejected"])
    c.execute("INSERT INTO grammar_passages (subject, unit, level, title, body, source, body_hash, active) "
              "VALUES ('english_long', '長文 Lv.1', 'standard', '架空', '架空の手入力の本文', 'pool', 'h-manual', 1) RETURNING id")
    p_manual = int(c.fetchone()["id"])
    c.execute("INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, source, passage_id, passage_seq, active) "
              "VALUES ('english_long', '長文 Lv.1', 'standard', '架空 ( )', ?, 0, 'pool', ?, 1, 1)", (json.dumps(["a", "b", "c", "d"]), p_manual))
    conn.commit()
    idx = mod._auto_reviewed_passages(c, "english_long", "長文 Lv.1", ["standard"])
    check("取込スクリプトを通らない出典 (pool) の本文は自動配信に出ない", p_manual not in idx["passages"] and idx["rejected"]["unreviewed_body"] == 1,
          idx["rejected"])
    pr = mod._auto_pick_reviewed_passages(c, "english_long", "長文 Lv.1", ["standard"], 1, {}, rng=random.Random(3))
    check("本文 1 本の抽出 (長文クラスは 1 回 1 本)", len(pr["passage_ids"]) == 1 and len(pr["qids"]) == 4 and p_manual not in pr["passage_ids"], pr)
    conn.close()

    # ------------------------------------------------------------------
    print("\n[12] CEO の配信済み一覧・お知らせ")
    r = client.get("/api/admin/grammar-drill/list", params={"subject": "english_long", "kind": "all"}, headers=adm)
    items = r.json().get("items", []) if r.status_code == 200 else []
    check("list?subject=english_long は英語長文のドリルだけ", r.status_code == 200 and items
          and all(x.get("subject") in ("english_long", None) for x in items) and r.json().get("subject") == "english_long", r.text[:200])
    r = client.get("/api/admin/grammar-drill/list", params={"subject": "英語長文"}, headers=adm)
    check("別名「英語長文」でも絞れる", r.status_code == 200 and r.json().get("subject") == "english_long", r.text[:200])
    mails = []
    orig = mod._send_message_email
    mod._send_message_email = lambda to, subject, body, student_name=None: (mails.append((subject, body)), {"sent": True})[1]
    orig_sleep = time.sleep
    time.sleep = lambda s: None
    os.environ["HOMEWORK_NOTIFY_EMAIL"] = "manual"   # 既定 (塾長が手で配ったときだけメール)
    try:
        mod._notify_grammar_drill_assigned([{"id": sid, "name": "架空", "email": "englong-01@example.org"}], "長文 Lv.1", 4,
                                           "english_long", "manual")
    finally:
        mod._send_message_email = orig
        time.sleep = orig_sleep
        os.environ["HOMEWORK_NOTIFY_EMAIL"] = "off"
    check("お知らせのメールの件名「📝 新しい英語長文の宿題「長文 Lv.1」が届きました」",
          mails and mails[0][0] == "📝 新しい英語長文の宿題「長文 Lv.1」が届きました", mails)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for f in FAILURES:
            print(f"   - {f}")
        return 1
    print("✅ PASS (英語長文: 本文型だけ・盲検の記録が必須・まとまりの照合・自動は高校生の長文クラスだけ)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
