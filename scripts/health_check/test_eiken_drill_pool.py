#!/usr/bin/env python3
"""🏅 英検 語彙ドリル (科目 eiken・seed-data/eiken_vocab_pool_v1.json) の回帰テスト。

背景 (2026-09-24 塾長指示「英検対策コースの子にも問題プールから英検の語彙問題を出題したい。2級もやって」):
  英検の語彙 (大問1 形式) を単元ドリルの **別科目 `eiken`** として足した。級は unit 名 (2級/準1級 × 単語/句動詞)。
  在庫は塾の書き下ろし教材 (準1級: 本番形式演習 第1弾/第2弾 + 完全模試 全3回 / 2級: 対策問題集 Vol.1/2 + 完全模試 全3回)。

固定する性質:
  1. シードの形式: subject=eiken・unit は server の _GRAMMAR_SUBJECT_UNIT_ORDER['eiken'] と完全一致・空所ちょうど 1 つ・
     4 択相異・answer が範囲内で正解語が解説に出る・解説に ①/「選択肢2」が無い・stem 一意・level は standard
  2. 取込 API が subject=eiken を受理し全問入る (再取込は 0 件 = dedup)。english / chugaku のバンクは増えない
  3. 単元一覧が学習順 (2級 単語 → 2級 句動詞・熟語 → 準1級 単語 → 準1級 句動詞・熟語) で在庫つき
  4. AIなし (塾生アプリのみ) の生徒に配信 → 取得 → 提出 が通り、question_attempts.subject='eiken' で記録される
  5. 正解位置が単元ごとに散っている (どの位置も 40% 以下)

実行:
    python3 scripts/health_check/test_eiken_drill_pool.py
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
import re
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
SEED = os.path.join(REPO, "seed-data", "eiken_vocab_pool_v1.json")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {detail}" if detail else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="eikenpool_"), "test.db")
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
    spec = importlib.util.spec_from_file_location("aijuku_main_eikenpool", MAIN_PY)
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


def make_student(mod, name, email, ai_disabled=1):
    conn = mod.db()
    c = conn.cursor()
    far = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)).isoformat()
    c.execute("INSERT INTO students (name, email, status, trial_end, course, grade, goal, ai_disabled) VALUES (?, ?, 'trial', ?, 'kokuritsu_nankan', '高校1年', '英検準1級', ?)",
              (name, email, far, int(ai_disabled)))
    conn.commit()
    c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
    sid = c.fetchone()["id"]
    conn.close()
    mod._AI_DISABLED_CACHE.pop(sid, None)
    return sid


def count_by_subject(mod):
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT subject, COUNT(*) AS n FROM grammar_questions WHERE active = 1 GROUP BY subject")
    out = {r["subject"]: int(r["n"]) for r in c.fetchall()}
    conn.close()
    return out


def main():
    print("🏅 英検 語彙ドリル 回帰テスト\n")
    seed = json.load(open(SEED, encoding="utf-8"))
    qs = seed.get("questions") or []
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    ORDER = mod._GRAMMAR_SUBJECT_UNIT_ORDER.get("eiken") or []

    print("[1] シードの形式")
    check("問題数が 300 以上", len(qs) >= 300, f"n={len(qs)}")
    check("科目 eiken が canonical", "eiken" in mod._GRAMMAR_CANON_SUBJECTS and mod._canon_grammar_subject("英検") == "eiken")
    check("単元の並び順: 語彙 4 単元 → 長文 4 単元", ORDER == ["2級 単語", "2級 句動詞・熟語", "準1級 単語", "準1級 句動詞・熟語",
                                                     "2級 長文空所補充", "2級 長文 内容一致", "準1級 長文空所補充", "準1級 長文 内容一致"], str(ORDER))
    VOCAB_UNITS = ORDER[:4]
    bad = []
    seen = set()
    for q in qs:
        src = q.get("source", "?")
        if q.get("subject") != "eiken": bad.append(f"{src}: subject")
        if q.get("unit") not in VOCAB_UNITS: bad.append(f"{src}: unit {q.get('unit')!r}")
        if q.get("level") != "standard": bad.append(f"{src}: level {q.get('level')!r}")
        stem = q.get("stem") or ""
        if stem.count("(   )") != 1: bad.append(f"{src}: 空所 {stem.count('(   )')}")
        ch = q.get("choices") or []
        if len(ch) != 4 or len(set(x.lower() for x in ch)) != 4: bad.append(f"{src}: choices {ch}")
        a = q.get("answer")
        if not isinstance(a, int) or not (0 <= a <= 3): bad.append(f"{src}: answer {a!r}")
        ex = q.get("explanation") or ""
        if isinstance(a, int) and 0 <= a <= 3 and ch and ch[a].lower() not in ex.lower(): bad.append(f"{src}: 解説に正解語なし")
        if re.search(r"[①②③④]|選択肢\s*[1-4１-４]|\{\s*[1-4]\s*:|(?<=[ぁ-んァ-ヶ一-龥])[1-4](?=のみ|だけ|が(?:文意|適切|自然|正解)|[。、]|\s|$)", ex): bad.append(f"{src}: 解説に番号参照")
        if len(ex) < 20: bad.append(f"{src}: 解説が短い")
        if stem.lower() in seen: bad.append(f"{src}: stem 重複")
        seen.add(stem.lower())
    check("全問が形式検査を通る", not bad, "; ".join(bad[:8]))
    by_unit = {}
    for q in qs:
        by_unit.setdefault(q["unit"], [0, 0, 0, 0])
        if isinstance(q.get("answer"), int) and 0 <= q["answer"] <= 3:
            by_unit[q["unit"]][q["answer"]] += 1
    skew = {u: max(v) / max(1, sum(v)) for u, v in by_unit.items()}
    check("正解位置がどの単元でも 40% 以下", all(x <= 0.40 for x in skew.values()), str({u: round(x, 2) for u, x in skew.items()}))
    check("各単元に 25 問以上 (25 問ドリルが作れる)", all(sum(v) >= 25 for v in by_unit.values()), str({u: sum(v) for u, v in by_unit.items()}))

    print("\n[2] 取込 API")
    before = count_by_subject(mod)
    inserted = skipped = 0
    for i in range(0, len(qs), 400):
        mod._RATE_LIMIT_STORE.clear()
        r = client.post("/api/admin/grammar/import", json={"questions": qs[i:i + 400], "subject": "eiken", "dedup": True}, headers=adm)
        check(f"POST import ({i + 1}〜) → 200", r.status_code == 200, r.text[:160])
        d = r.json() if r.status_code == 200 else {}
        inserted += int(d.get("inserted") or 0); skipped += int(d.get("skipped") or 0)
    check("全問が入る (inserted == 問題数・skipped 0)", inserted == len(qs) and skipped == 0, f"inserted={inserted} skipped={skipped}")
    after = count_by_subject(mod)
    check("english / chugaku のバンクは増えない", after.get("english", 0) == before.get("english", 0) and after.get("chugaku", 0) == before.get("chugaku", 0), f"before={before} after={after}")
    check("eiken の在庫 = 問題数", after.get("eiken", 0) == len(qs), f"eiken={after.get('eiken')}")
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar/import", json={"questions": qs[:50], "subject": "eiken", "dedup": True}, headers=adm)
    check("再取込は dedup で 0 件", r.status_code == 200 and int(r.json().get("inserted") or 0) == 0, r.text[:120])
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar/import", json={"questions": qs[:1], "subject": "toeic", "dedup": True}, headers=adm)
    check("未知の科目 (toeic) は 422 のまま", r.status_code == 422, f"status={r.status_code}")

    print("\n[3] 単元一覧")
    r = client.get("/api/admin/grammar/units", params={"subject": "eiken"}, headers=adm)
    units = r.json().get("units", []) if r.status_code == 200 else []
    check("単元が学習順 (語彙 4 → 長文 4・在庫 0 の長文単元も 0 で出る)", [u["unit"] for u in units][:len(ORDER)] == ORDER, str([u["unit"] for u in units]))
    check("長文単元は passages=0 (未取込)・語彙単元も passages キーを持つ", all(("passages" in u) for u in units) and all(u.get("passages") == 0 for u in units), str([(u["unit"], u.get("passages")) for u in units]))
    check("各単元の standard 在庫 = シードの数", all(next((u for u in units if u["unit"] == k), {}).get("standard") == sum(v) for k, v in by_unit.items()), str({u["unit"]: u.get("standard") for u in units}))
    check("科目ラベルは「英検」(語彙も長文も同じ科目なので「語彙」は付けない)", mod._grammar_subject_label_ja("eiken") == "英検")

    print("\n[4] AIなしの生徒に配信 → 取得 → 提出")
    sid = make_student(mod, "英検テスト A", "eiken-a@example.org", ai_disabled=1)
    tok = {"Authorization": "Bearer " + student_token(mod, sid)}
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar-drill/create", json={"subject": "eiken", "unit": "2級 単語", "count": 25, "student_ids": [sid], "levels": ["standard", "advanced"]}, headers=adm)
    check("配信 (2級 単語・25 問) → 200", r.status_code == 200, r.text[:200])
    r = client.get("/api/student/grammar-drills", headers=tok)
    drills = (r.json().get("drills") or r.json().get("items") or []) if r.status_code == 200 else []
    check("生徒のドリル一覧に 1 本", r.status_code == 200 and len(drills) == 1, f"status={r.status_code} n={len(drills)} body={r.text[:160]}")
    did = drills[0].get("id") or drills[0].get("drill_id") if drills else None
    r = client.get(f"/api/student/grammar-drill/{did}", headers=tok)
    body = r.json() if r.status_code == 200 else {}
    qlist = body.get("questions") or []
    check("取得 → 200・25 問・正解は伏せてある", r.status_code == 200 and len(qlist) == 25 and all("answer" not in q or q.get("answer") is None for q in qlist), f"status={r.status_code} n={len(qlist)} keys={list(qlist[0].keys()) if qlist else None}")
    answers = {}
    for q in qlist:
        qid = q.get("id") or q.get("question_id")
        answers[str(qid)] = 0
    r = client.post(f"/api/student/grammar-drill/{did}/submit", json={"answers": answers}, headers=tok)
    check("提出 → 200・採点結果あり", r.status_code == 200 and r.json().get("score_total") == 25, f"status={r.status_code} body={r.text[:200]}")
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT subject, topic, COUNT(*) AS n FROM question_attempts WHERE student_id = ? GROUP BY subject, topic", (sid,))
    rows = [dict(x) for x in c.fetchall()]
    conn.close()
    check("question_attempts が subject='eiken' / topic='2級 単語' で 25 件", rows == [{"subject": "eiken", "topic": "2級 単語", "n": 25}], str(rows))

    print()
    if FAILURES:
        print(f"❌ FAIL: {len(FAILURES)} 件")
        for f in FAILURES:
            print("   -", f)
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
