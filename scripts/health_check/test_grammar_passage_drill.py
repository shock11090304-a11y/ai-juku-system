#!/usr/bin/env python3
"""📖 長文型ドリル (本文 + 複数設問・grammar_passages) の回帰テスト。

背景 (2026-09-24 塾長指示「長文読解や長文空所補充問題も 4 択の科目別単元ドリルに追加できない？」→「A で」):
  単元ドリルは 1 文 4 択を 1 問ずつランダムに引く作りだった。本文 (grammar_passages) と passage_id/passage_seq を足し、
  本文のある単元は「本文 N 本」単位で出題する。本文は生徒画面で 1 回だけ出す。

固定する性質:
  1. 取込: passages[] が本文 + 設問で入る。本文の重複 (同じ body) は本文ごと skip。設問は本文をまたいで同文でも入る
     (「( 1 ) に入る語」型)。english の本文は受けない。設問の形式が壊れた本文は本文ごと入らない (本文だけ残らない)。
  2. 単元一覧: passages の本数が付く。
  3. ドリル作成: 本文のある単元は count を無視して passage_count 本 (既定 2・上限 5)。設問は本文順 (passage_seq)、
     score_total は設問数。在庫不足は 400。exclude_drill_id は前回の本文ごと除外。本文の無い単元 (語彙) は従来どおり。
  4. 生徒の取得: questions に passage_id、passages に本文 (解く前は body_ja 無し・完了後はあり)。提出も本文 map を返す。
  5. 分析: questions に passage_id、passages map。
  6. 従来の単発ドリル (本文なし) の応答形は不変 (passages は {})。

実行:
    python3 scripts/health_check/test_grammar_passage_drill.py
    # exit 0 = PASS / 1 = FAIL

外部通信は一切しない。DB は一時 SQLite。
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import json
import os
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {detail}" if detail else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="passagedrill_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと **本番 Postgres** に書き込む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "",
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_passagedrill", MAIN_PY)
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


def make_student(mod, name, email):
    conn = mod.db(); c = conn.cursor()
    far = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)).isoformat()
    c.execute("INSERT INTO students (name, email, status, trial_end, course, grade, goal, ai_disabled) VALUES (?, ?, 'trial', ?, 'kokuritsu_nankan', '高校2年', '英検準1級', 1)",
              (name, email, far))
    conn.commit()
    c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
    sid = c.fetchone()["id"]
    conn.close()
    mod._AI_DISABLED_CACHE.pop(sid, None)
    return sid


UNIT_C = "準1級 長文空所補充"
UNIT_R = "準1級 長文 内容一致"


def passage(n, unit=UNIT_C, nq=3, title=None):
    body = (f"Passage {n} paragraph one about wind turbines. The blades combine glass fiber with resin. ( 1 ), many retired blades are buried.\n\n"
            f"Paragraph two of passage {n}. Engineers now cut the blades into ( 2 ) pieces for bridges. ( 3 ), the material finds a second life.")
    qs = []
    for k in range(1, nq + 1):
        qs.append({"stem": f"( {k} ) に入るもの", "choices": [f"opt{k}a", f"opt{k}b", f"opt{k}c", f"opt{k}d"], "answer": (k - 1) % 4,
                   "explanation": f"正解は opt{k}{'abcd'[(k - 1) % 4]}。理由 {n}-{k}。", "source": f"test-p{n}-q{k}"})
    return {"subject": "eiken", "unit": unit, "level": "standard", "title": title or f"Test Passage {n}",
            "body": body, "body_ja": f"本文 {n} の全訳。", "source": f"test-p{n}", "questions": qs}


def main():
    print("📖 長文型ドリル 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    adm = {"Authorization": "Bearer " + admin_token(mod)}

    print("[0] 列・表")
    conn = mod.db(); c = conn.cursor()
    try:
        c.execute("SELECT passage_id, passage_seq FROM grammar_questions LIMIT 1"); c.fetchall()
        c.execute("SELECT id, subject, unit, level, title, body, body_ja, source, body_hash, active FROM grammar_passages LIMIT 1"); c.fetchall()
        _schema_ok = True
    except Exception as _e:
        _schema_ok = False; print("   ", type(_e).__name__, _e)
    conn.close()
    check("grammar_passages と passage_id/passage_seq が init_db で入る", _schema_ok)
    check("_grammar_has_passages() が True", mod._grammar_has_passages() is True)
    # 「列はあるが表が無い」(CREATE TABLE がロック待ちで飛び ALTER だけ通った) を再現 → False に倒れ、単発の抽出は生きる
    conn = mod.db(); c = conn.cursor()
    c.execute("ALTER TABLE grammar_passages RENAME TO grammar_passages__gone"); conn.commit(); conn.close()
    mod._HAS_COL_CACHE.clear()
    check("表 grammar_passages が無いと _grammar_has_passages() は False (列だけ見ない)", mod._grammar_has_passages() is False)
    conn = mod.db(); c = conn.cursor()
    c.execute("ALTER TABLE grammar_passages__gone RENAME TO grammar_passages"); conn.commit(); conn.close()
    mod._HAS_COL_CACHE.clear()
    check("表を戻すと True", mod._grammar_has_passages() is True)

    print("\n[1] 取込")
    body = {"subject": "eiken", "dedup": True, "passages": [passage(1), passage(2), passage(3, unit=UNIT_R, nq=4), passage(4, unit=UNIT_R, nq=3)]}
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar/import", json=body, headers=adm)
    d = r.json() if r.status_code == 200 else {}
    check("passages 4 本 → 200・passages_inserted 4・inserted 13", r.status_code == 200 and d.get("passages_inserted") == 4 and d.get("inserted") == 13, r.text[:200])
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar/import", json={"subject": "eiken", "passages": [passage(1), passage(2)]}, headers=adm)
    d = r.json() if r.status_code == 200 else {}
    check("同じ本文の再取込は本文ごと skip (passages_skipped 2・inserted 0)", r.status_code == 200 and d.get("passages_skipped") == 2 and d.get("inserted") == 0, r.text[:200])
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) AS n FROM grammar_questions WHERE stem = '( 1 ) に入るもの' AND unit = ?", (UNIT_C,)); n_same = c.fetchone()["n"]
    c.execute("SELECT passage_id, passage_seq, stem FROM grammar_questions WHERE unit = ? ORDER BY passage_id, passage_seq", (UNIT_C,)); rows = [dict(x) for x in c.fetchall()]
    conn.close()
    check("本文をまたいで同文の設問 (「( 1 ) に入るもの」) が 2 本ぶん入っている", n_same == 2, f"n={n_same}")
    check("passage_seq が 1,2,3 の順で付く", [x["passage_seq"] for x in rows] == [1, 2, 3, 1, 2, 3], str(rows))
    broken = passage(9); broken["questions"][1]["answer"] = 9
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar/import", json={"subject": "eiken", "passages": [broken]}, headers=adm)
    d = r.json() if r.status_code == 200 else {}
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) AS n FROM grammar_passages WHERE source = 'test-p9'"); n9 = c.fetchone()["n"]
    conn.close()
    check("設問の壊れた本文は本文ごと入らない (passages_skipped 1・本文 0 行)", d.get("passages_skipped") == 1 and n9 == 0, r.text[:160])
    eng = passage(10, unit="長文読解"); eng["subject"] = "english"
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar/import", json={"subject": "english", "passages": [eng]}, headers=adm)
    d = r.json() if r.status_code == 200 else {}
    check("english の本文は受けない (skip)", r.status_code == 200 and d.get("passages_skipped") == 1 and d.get("passages_inserted") == 0, r.text[:160])
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar/import", json={"subject": "eiken", "passages": "x"}, headers=adm)
    check("passages が配列でない → 422", r.status_code == 422)

    print("\n[2] 単元一覧")
    r = client.get("/api/admin/grammar/units", params={"subject": "eiken"}, headers=adm)
    units = {u["unit"]: u for u in (r.json().get("units", []) if r.status_code == 200 else [])}
    check("長文空所補充: passages 2・standard 6 / 内容一致: passages 2・standard 7", units.get(UNIT_C, {}).get("passages") == 2 and units.get(UNIT_C, {}).get("standard") == 6 and units.get(UNIT_R, {}).get("passages") == 2 and units.get(UNIT_R, {}).get("standard") == 7, str({k: (v.get("passages"), v.get("standard")) for k, v in units.items()}))

    print("\n[3] ドリル作成 (本文単位)")
    sid = make_student(mod, "長文テスト A", "passage-a@example.org")
    tok = {"Authorization": "Bearer " + student_token(mod, sid)}
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar-drill/create", json={"subject": "eiken", "unit": UNIT_C, "count": 25, "passage_count": 2, "student_ids": [sid]}, headers=adm)
    d = r.json() if r.status_code == 200 else {}
    check("本文 2 本 → 200・question_count 6・passage_count 2", r.status_code == 200 and d.get("question_count") == 6 and d.get("passage_count") == 2, r.text[:200])
    check("タイトルに「本文2本・6問」", "本文2本・6問" in (d.get("title") or ""), d.get("title"))
    drill1 = d.get("drill_id")
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT question_ids FROM grammar_drills WHERE id = ?", (drill1,)); qids1 = json.loads(c.fetchone()["question_ids"])
    c.execute("SELECT score_total FROM grammar_drill_assignments WHERE drill_id = ? AND student_id = ?", (drill1, sid)); st = c.fetchone()["score_total"]
    ph = ",".join("?" * len(qids1))
    c.execute(f"SELECT id, passage_id, passage_seq FROM grammar_questions WHERE id IN ({ph})", tuple(qids1)); qi = {x["id"]: (x["passage_id"], x["passage_seq"]) for x in c.fetchall()}
    conn.close()
    order = [qi[q] for q in qids1]
    check("score_total = 6 (設問数)", st == 6, f"score_total={st}")
    check("設問は本文ごとにまとまり、本文内は seq 順", order[:3][0][0] == order[1][0] == order[2][0] and [o[1] for o in order] == [1, 2, 3, 1, 2, 3] and order[3][0] != order[0][0], str(order))
    # 順序が本当に passage_seq で決まるか: 1 本目の seq を逆順 (3,2,1) にして作り直すと id 昇順とは違う並びになる
    _p_first = order[0][0]
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE grammar_questions SET passage_seq = 4 - passage_seq WHERE passage_id = ?", (_p_first,)); conn.commit(); conn.close()
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar-drill/create", json={"subject": "eiken", "unit": UNIT_C, "passage_count": 2, "student_ids": [sid]}, headers=adm)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT question_ids FROM grammar_drills WHERE id = ?", (r.json().get("drill_id"),)); _q2 = json.loads(c.fetchone()["question_ids"])
    c.execute(f"SELECT id, passage_id, passage_seq FROM grammar_questions WHERE id IN ({','.join('?' * len(_q2))})", tuple(_q2)); _qi2 = {x["id"]: (x["passage_id"], x["passage_seq"]) for x in c.fetchall()}
    _ids_first = [q for q in _q2 if _qi2[q][0] == _p_first]
    c.execute("UPDATE grammar_questions SET passage_seq = 4 - passage_seq WHERE passage_id = ?", (_p_first,)); conn.commit(); conn.close()
    check("seq を逆にすると出題順も逆 (id 昇順ではなく passage_seq 順)", [_qi2[q][1] for q in _ids_first] == [1, 2, 3] and _ids_first == sorted(_ids_first, reverse=True), str([(q, _qi2[q]) for q in _q2]))
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar-drill/create", json={"subject": "eiken", "unit": UNIT_C, "student_ids": [sid]}, headers=adm)
    check("passage_count 無し (旧 UI) でも本文単位 (既定 2 本) で作られる", r.status_code == 200 and r.json().get("passage_count") == 2, r.text[:160])
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar-drill/create", json={"subject": "eiken", "unit": UNIT_C, "passage_count": 3, "student_ids": [sid]}, headers=adm)
    check("在庫 2 本に 3 本要求 → 400 (本文の在庫が不足)", r.status_code == 400 and "本文の在庫" in (r.json().get("detail") or ""), r.text[:160])
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar-drill/create", json={"subject": "eiken", "unit": UNIT_C, "passage_count": 1, "exclude_drill_id": drill1, "student_ids": [sid]}, headers=adm)
    check("exclude_drill_id (2 本とも出題済み) で 1 本要求 → 400 (前回の本文を除いた在庫 0本)", r.status_code == 400 and "前回の本文を除いた在庫 0本" in (r.json().get("detail") or ""), r.text[:160])
    sid_b = make_student(mod, "長文テスト B", "passage-b@example.org")
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar-drill/create", json={"subject": "eiken", "unit": UNIT_R, "passage_count": 1, "student_ids": [sid_b]}, headers=adm)
    d = r.json() if r.status_code == 200 else {}
    drill_r1 = d.get("drill_id")
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar-drill/create", json={"subject": "eiken", "unit": UNIT_R, "passage_count": 1, "exclude_drill_id": drill_r1, "student_ids": [sid_b]}, headers=adm)
    d2 = r.json() if r.status_code == 200 else {}
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT question_ids FROM grammar_drills WHERE id IN (?, ?) ORDER BY id", (drill_r1, d2.get("drill_id") or -1)); rows = [json.loads(x["question_ids"]) for x in c.fetchall()]
    conn.close()
    check("内容一致 1 本 → exclude で残りの 1 本が出る (設問が重ならない)", r.status_code == 200 and len(rows) == 2 and not (set(rows[0]) & set(rows[1])), f"{r.status_code} rows={[len(x) for x in rows]}")
    # ランダム抽出なので 5 回まわして毎回「前回の本文ごと」除外されることを確かめる (設問単位の除外だと同じ本文の残りが出る)
    _ok_all = True
    for _i in range(5):
        mod._RATE_LIMIT_STORE.clear()
        r = client.post("/api/admin/grammar-drill/create", json={"subject": "eiken", "unit": UNIT_R, "passage_count": 1, "student_ids": [sid_b]}, headers=adm)
        _d1 = r.json().get("drill_id") if r.status_code == 200 else None
        mod._RATE_LIMIT_STORE.clear()
        r = client.post("/api/admin/grammar-drill/create", json={"subject": "eiken", "unit": UNIT_R, "passage_count": 2, "exclude_drill_id": _d1, "student_ids": [sid_b]}, headers=adm)
        _ok_all = _ok_all and (r.status_code == 400 and "前回の本文を除いた在庫 1本" in (r.json().get("detail") or ""))
    check("在庫 2 本で 1 本出題 → exclude して 2 本要求は毎回 400 (除いた在庫 1本)", _ok_all, r.text[:160])
    # 設問が全部 inactive の本文は選ばれない (枠だけ消費して 0 問にならない)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT id FROM grammar_passages WHERE unit = ? ORDER BY id LIMIT 1", (UNIT_R,)); _dead = c.fetchone()["id"]
    c.execute("UPDATE grammar_questions SET active = 0 WHERE passage_id = ?", (_dead,)); conn.commit(); conn.close()
    _ok_all = True
    for _i in range(5):
        mod._RATE_LIMIT_STORE.clear()
        r = client.post("/api/admin/grammar-drill/create", json={"subject": "eiken", "unit": UNIT_R, "passage_count": 1, "student_ids": [sid_b]}, headers=adm)
        _ok_all = _ok_all and r.status_code == 200 and r.json().get("question_count") in (3, 4) and _dead not in (r.json().get("passage_ids") or [-1])
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE grammar_questions SET active = 1 WHERE passage_id = ?", (_dead,)); conn.commit(); conn.close()
    check("設問が全部 inactive の本文は選ばれない (5 回とも生きた本文で 200)", _ok_all, r.text[:160])
    # 長文の設問は 1 問ずつの抽出 (科目全体・弱点ルーティン経路) に混ざらない
    conn = mod.db(); c = conn.cursor()
    _single = mod._grammar_pick_drill_question_ids(c, "eiken", "", True, ["standard"], 50, None)
    c.execute("SELECT COUNT(*) AS n FROM grammar_questions WHERE subject = 'eiken' AND passage_id IS NOT NULL AND active = 1"); _np = c.fetchone()["n"]
    conn.close()
    check("科目全体の 1 問ずつ抽出に長文の設問が混ざらない (passage_id IS NULL)", _np > 0 and len(_single) == 0, f"picked={len(_single)} passage_q={_np}")

    print("\n[4] 生徒の取得・提出")
    r = client.get(f"/api/student/grammar-drill/{drill1}", headers=tok)
    g = r.json() if r.status_code == 200 else {}
    qs = g.get("questions") or []
    pmap = g.get("passages") or {}
    check("取得 → 200・6 問・各設問に passage_id", r.status_code == 200 and len(qs) == 6 and all(q.get("passage_id") for q in qs), r.text[:160])
    check("passages map に 2 本・title/body あり・解く前は body_ja 無し", len(pmap) == 2 and all(("body" in v and "title" in v and "body_ja" not in v) for v in pmap.values()), str({k: list(v.keys()) for k, v in pmap.items()}))
    check("passage_id が map のキーと一致", all(str(q["passage_id"]) in pmap for q in qs))
    check("解く前は answer/explanation を返さない", all("answer" not in q and "explanation" not in q for q in qs))
    answers = {str(q["question_id"]): 0 for q in qs}
    mod._RATE_LIMIT_STORE.clear()
    r = client.post(f"/api/student/grammar-drill/{drill1}/submit", json={"answers": answers}, headers=tok)
    s = r.json() if r.status_code == 200 else {}
    check("提出 → 200・score_total 6・results に passage_id・passages map (全訳つき)", r.status_code == 200 and s.get("score_total") == 6 and all(x.get("passage_id") for x in s.get("results", [])) and len(s.get("passages") or {}) == 2 and all("body_ja" in v for v in s["passages"].values()), r.text[:200])
    r = client.get(f"/api/student/grammar-drill/{drill1}", headers=tok)
    g2 = r.json() if r.status_code == 200 else {}
    check("完了後の取得は body_ja あり・answer/explanation あり", r.status_code == 200 and all("body_ja" in v for v in (g2.get("passages") or {}).values()) and all("answer" in q for q in g2.get("questions", [])), r.text[:160])
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT subject, topic, COUNT(*) AS n FROM question_attempts WHERE student_id = ? GROUP BY subject, topic", (sid,)); rows = [dict(x) for x in c.fetchall()]
    conn.close()
    check("question_attempts が subject='eiken' / topic=単元 で 6 件", rows == [{"subject": "eiken", "topic": UNIT_C, "n": 6}], str(rows))

    print("\n[5] 分析")
    r = client.get(f"/api/admin/grammar-drill/{drill1}/analytics", headers=adm)
    a = r.json() if r.status_code == 200 else {}
    check("分析 → 200・questions に passage_id・passages map 2 本", r.status_code == 200 and all(q.get("passage_id") for q in a.get("questions", [])) and len(a.get("passages") or {}) == 2, r.text[:160])
    check("問題別の正解率が出る (1 人回答・問1 正解)", a.get("questions", [{}])[0].get("answered") == 1 and a.get("questions", [{}])[0].get("correct") == 1, str(a.get("questions", [{}])[0]))

    print("\n[6] 従来の単発ドリルは不変")
    single = [{"subject": "eiken", "unit": "2級 単語", "level": "standard", "stem": f"Single ( ) {i}.", "choices": ["a", "b", "c", "d"], "answer": i % 4, "explanation": f"正解は {'abcd'[i % 4]}。", "source": "t"} for i in range(30)]
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar/import", json={"subject": "eiken", "questions": single}, headers=adm)
    check("単発 30 問の取込 (passages 無し) → 200・passages_received 0", r.status_code == 200 and r.json().get("inserted") == 30 and r.json().get("passages_received") == 0, r.text[:160])
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar-drill/create", json={"subject": "eiken", "unit": "2級 単語", "count": 25, "passage_count": 3, "student_ids": [sid]}, headers=adm)
    d = r.json() if r.status_code == 200 else {}
    check("本文の無い単元は count=25 で従来どおり (passage_count は無視・passage_count 0)", r.status_code == 200 and d.get("question_count") == 25 and d.get("passage_count") == 0 and "標準" in (d.get("title") or ""), r.text[:200])
    r = client.get(f"/api/student/grammar-drill/{d.get('drill_id')}", headers=tok)
    g3 = r.json() if r.status_code == 200 else {}
    check("単発ドリルの取得: passages は {}・設問に passage_id 無し", r.status_code == 200 and g3.get("passages") == {} and all("passage_id" not in q for q in g3.get("questions", [])), r.text[:160])

    print("\n[7] 👀 問題を見る (admin preview・配信しない)")
    mod._RATE_LIMIT_STORE.clear()
    conn = mod.db(); c = conn.cursor()
    def _counts(c):
        out = []
        for t in ("grammar_drills", "grammar_drill_assignments", "question_attempts"):
            c.execute(f"SELECT COUNT(*) AS n FROM {t}"); out.append(c.fetchone()["n"])
        return out
    before = _counts(c); conn.close()
    r = client.get("/api/admin/grammar/preview", params={"subject": "eiken", "unit": UNIT_C, "passage_count": 1}, headers=adm)
    pv = r.json() if r.status_code == 200 else {}
    check("長文型の単元: 200・本文 1 本・設問 3 問 (本文順)・答えと解説と全訳つき",
          r.status_code == 200 and pv.get("passage_count") == 1 and len(pv.get("questions") or []) == 3
          and all(q.get("passage_id") and q.get("answer") is not None and q.get("explanation") for q in pv["questions"])
          and len(pv.get("passages") or {}) == 1 and all("body_ja" in v for v in pv["passages"].values()), r.text[:200])
    check("設問は本文の順 (stem が ( 1 )( 2 )( 3 ) の順・passages のキーと一致)",
          [q["no"] for q in pv.get("questions", [])] == [1, 2, 3]
          and [q["stem"][:5] for q in pv.get("questions", [])] == ["( 1 )", "( 2 )", "( 3 )"]
          and all(str(q["passage_id"]) in pv.get("passages", {}) for q in pv.get("questions", [])), str([q.get("stem") for q in pv.get("questions", [])])[:160])
    r = client.get("/api/admin/grammar/preview", params={"subject": "eiken", "unit": "2級 単語", "count": 5}, headers=adm)
    pv2 = r.json() if r.status_code == 200 else {}
    check("本文の無い単元: 200・5 問・passages {}・passage_id 無し", r.status_code == 200 and len(pv2.get("questions") or []) == 5 and pv2.get("passages") == {} and pv2.get("passage_count") == 0 and all("passage_id" not in q for q in pv2["questions"]), r.text[:160])
    r = client.get("/api/admin/grammar/preview", params={"subject": "eiken", "unit": "存在しない単元"}, headers=adm)
    check("在庫の無い単元: 200・0 問 (エラーにしない)", r.status_code == 200 and r.json().get("questions") == [], r.text[:120])
    r = client.get("/api/admin/grammar/preview", params={"subject": "eiken", "unit": UNIT_C})
    check("未認証 → 401", r.status_code == 401)
    r = client.get("/api/admin/grammar/preview", params={"subject": "eiken", "unit": UNIT_C}, headers=tok)
    check("生徒のトークン → 401 (答えつきの問題は生徒に見せない)", r.status_code == 401, r.text[:120])
    r = client.get("/api/admin/grammar/preview", params={"subject": "eiken"}, headers=adm)
    check("unit 無し → 422", r.status_code == 422)
    r = client.get("/api/admin/grammar/preview", params={"subject": "klingon", "unit": UNIT_C}, headers=adm)
    check("科目不明 → 422 (english に黙って倒さない)", r.status_code == 422, r.text[:120])
    conn = mod.db(); c = conn.cursor()
    after = _counts(c); conn.close()
    check("プレビューは何も書かない (grammar_drills / assignments / question_attempts の行数が不変)", after == before, f"{before}→{after}")

    print()
    if FAILURES:
        print(f"❌ FAIL: {len(FAILURES)} 件")
        for f in FAILURES:
            print("   -", f)
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
