#!/usr/bin/env python3
"""🧒 中学数学ドリル (科目 chugaku_math・seed-data/chugaku_math_pool_v1.json) の回帰テスト。

背景 (2026-09-28 塾長指示「さらに中学生用の問題を追加して」→ 数学・国語・理科・社会を1教科ずつ。まず数学):
  中学の他教科は単元ドリルの **教科ごとの別科目** (chugaku_math …) にした。高校の数学 (math) には混ぜない。
  ★ただし生徒の解答は入試道場と同じ「中学」の1バケット subject='chugaku' ＋ topic=単元名 で記録する。
    中学生の弱点・週次プリント・弱点 TOP3 はその前提で組まれているため。

固定する性質:
  1. シードの形式: subject=chugaku_math・unit は server の _GRAMMAR_SUBJECT_UNIT_ORDER['chugaku_math'] と完全一致・
     4 択相異・answer が範囲内・解説に ①/「選択肢」が無い・stem 一意・マイナスは「−」(半角 - を使わない)・
     「図のように」等の図を前提にした問題が無い・高校範囲の語 (sin/判別式/ベクトル 等) が無い
  2. 取込 API が subject=chugaku_math を受理し全問入る (再取込は 0 件)。english / math / chugaku のバンクは増えない
  3. 単元一覧が入試道場のカタログ順 (scripts/chugaku_dojo/units.json の math) で在庫つき・ラベル「中学数学」
  4. 中学生に配信 → 取得 → 提出 が通り、question_attempts は subject='chugaku' / topic=単元名 で記録される
  5. 記録科目のヘルパ: 中学英語は 'chugaku' のまま・高校の english / math はそのまま (既存の挙動を変えない)
  6. 正解位置が単元ごとに散っている (どの位置も 40% 以下)・各単元で標準＋やや難が 25 問以上

実行:
    python3 scripts/health_check/test_chugaku_math_drill_pool.py
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
SEED = os.path.join(REPO, "seed-data", "chugaku_math_pool_v1.json")
CATALOG = os.path.join(REPO, "scripts", "chugaku_dojo", "units.json")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {detail}" if detail else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="chumath_"), "test.db")
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
    spec = importlib.util.spec_from_file_location("aijuku_main_chumath", MAIN_PY)
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


def make_student(mod, name, email, grade="中学3年", ai_disabled=1):
    """ai_disabled=1 は塾生アプリのみ枠 (通塾生の典型)。入試道場 (/api/question-attempts) を使えるのは 0 (AIあり) だけ。"""
    conn = mod.db()
    c = conn.cursor()
    far = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)).isoformat()
    c.execute("INSERT INTO students (name, email, status, trial_end, course, grade, goal, ai_disabled) VALUES (?, ?, 'trial', ?, 'kokuritsu_nankan', ?, '公立高校', ?)",
              (name, email, far, grade, int(ai_disabled)))
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


HS_TERMS = re.compile(r"sin|cos|tan|判別式|解と係数|log|数列|ベクトル|微分|積分|余弦定理|正弦定理")
FIGURE = re.compile(r"図のように|下の図|右の図|左の図|次の図")
POSREF = re.compile(r"[①②③④]|選択肢")


def main():
    print("🧒 中学数学ドリル 回帰テスト\n")
    seed = json.load(open(SEED, encoding="utf-8"))
    qs = seed.get("questions") or []
    cat = json.load(open(CATALOG, encoding="utf-8"))
    cat_units = [u["filter"] for s in cat["subjects"] if s["part"] == "math" for u in s["units"]]
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    ORDER = mod._GRAMMAR_SUBJECT_UNIT_ORDER.get("chugaku_math") or []

    print("[1] シードの形式")
    check("問題数が 750 以上", len(qs) >= 750, f"n={len(qs)}")
    check("科目 chugaku_math が canonical・別名「中学数学」", "chugaku_math" in mod._GRAMMAR_CANON_SUBJECTS and mod._canon_grammar_subject("中学数学") == "chugaku_math")
    check("単元の並び順が入試道場のカタログ (math) と完全一致", ORDER == cat_units, f"server={ORDER}")
    bad = []
    seen = set()
    for i, q in enumerate(qs):
        tag = f"#{i}"
        if q.get("subject") != "chugaku_math": bad.append(f"{tag}: subject {q.get('subject')!r}")
        if q.get("unit") not in ORDER: bad.append(f"{tag}: unit {q.get('unit')!r}")
        if q.get("level") not in ("basic", "standard", "advanced"): bad.append(f"{tag}: level {q.get('level')!r}")
        stem = q.get("stem") or ""
        ch = [str(x) for x in (q.get("choices") or [])]
        if len(ch) != 4 or len(set(x.strip() for x in ch)) != 4: bad.append(f"{tag}: choices {ch}")
        a = q.get("answer")
        if not isinstance(a, int) or not (0 <= a <= 3): bad.append(f"{tag}: answer {a!r}")
        ex = q.get("explanation") or ""
        if not (60 <= len(ex) <= 200): bad.append(f"{tag}: 解説 {len(ex)}字")
        if POSREF.search(ex): bad.append(f"{tag}: 解説に位置参照")
        for part in [stem] + ch:
            if "-" in part: bad.append(f"{tag}: 半角の - がある (マイナスは「−」): {part[:30]}")
            if HS_TERMS.search(part): bad.append(f"{tag}: 高校範囲の語: {part[:30]}")
        if FIGURE.search(stem): bad.append(f"{tag}: 図を前提にしている")
        if stem.strip() in seen: bad.append(f"{tag}: stem 重複")
        seen.add(stem.strip())
    check("全問が形式検査を通る", not bad, "; ".join(bad[:8]))
    by_unit = {}
    lv_unit = {}
    for q in qs:
        by_unit.setdefault(q["unit"], [0, 0, 0, 0])
        lv_unit.setdefault(q["unit"], {"basic": 0, "standard": 0, "advanced": 0})
        if isinstance(q.get("answer"), int) and 0 <= q["answer"] <= 3:
            by_unit[q["unit"]][q["answer"]] += 1
        lv_unit[q["unit"]][q["level"]] += 1
    skew = {u: max(v) / max(1, sum(v)) for u, v in by_unit.items()}
    check("正解位置がどの単元でも 40% 以下", all(x <= 0.40 for x in skew.values()), str({u: round(x, 2) for u, x in skew.items() if x > 0.4}))
    check("全15単元に問題がある", set(by_unit) == set(ORDER), str(sorted(set(ORDER) - set(by_unit))))
    check("各単元で 標準＋やや難 が 25 問以上 (既定の25問ドリルが作れる)",
          all(v["standard"] + v["advanced"] >= 25 for v in lv_unit.values()), str({u: v["standard"] + v["advanced"] for u, v in lv_unit.items()}))

    print("\n[2] 取込 API")
    before = count_by_subject(mod)
    inserted = skipped = 0
    for i in range(0, len(qs), 400):
        mod._RATE_LIMIT_STORE.clear()
        r = client.post("/api/admin/grammar/import", json={"questions": qs[i:i + 400], "subject": "chugaku_math", "dedup": True}, headers=adm)
        check(f"POST import ({i + 1}〜) → 200", r.status_code == 200, r.text[:160])
        d = r.json() if r.status_code == 200 else {}
        inserted += int(d.get("inserted") or 0); skipped += int(d.get("skipped") or 0)
    check("全問が入る (inserted == 問題数・skipped 0)", inserted == len(qs) and skipped == 0, f"inserted={inserted} skipped={skipped}")
    after = count_by_subject(mod)
    check("english / math / chugaku のバンクは増えない",
          all(after.get(k, 0) == before.get(k, 0) for k in ("english", "math", "chugaku")), f"before={before} after={after}")
    check("chugaku_math の在庫 = 問題数", after.get("chugaku_math", 0) == len(qs), f"chugaku_math={after.get('chugaku_math')}")
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar/import", json={"questions": qs[:50], "subject": "chugaku_math", "dedup": True}, headers=adm)
    check("再取込は dedup で 0 件", r.status_code == 200 and int(r.json().get("inserted") or 0) == 0, r.text[:120])

    print("\n[3] 単元一覧とラベル")
    r = client.get("/api/admin/grammar/units", params={"subject": "chugaku_math"}, headers=adm)
    units = r.json().get("units", []) if r.status_code == 200 else []
    check("応答の subject が chugaku_math (画面の再デプロイ待ち判定が効く)", r.status_code == 200 and r.json().get("subject") == "chugaku_math", r.text[:120])
    check("単元が入試道場のカタログ順", [u["unit"] for u in units][:len(ORDER)] == ORDER, str([u["unit"] for u in units]))
    check("各単元の在庫がシードの数と一致",
          all(next((u for u in units if u["unit"] == k), {}).get("total") == sum(v.values()) for k, v in lv_unit.items()),
          str({u["unit"]: u.get("total") for u in units}))
    check("科目ラベルは「中学数学」", mod._grammar_subject_label_ja("chugaku_math") == "中学数学")

    print("\n[4] 中学生に配信 → 取得 → 提出 → 解答の記録")
    sid = make_student(mod, "中学数学テスト A", "chumath-a@example.org")
    tok = {"Authorization": "Bearer " + student_token(mod, sid)}
    unit = ORDER[0]
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar-drill/create", json={"subject": "chugaku_math", "unit": unit, "count": 25, "student_ids": [sid], "levels": ["standard", "advanced"]}, headers=adm)
    check(f"配信 ({unit}・25 問) → 200", r.status_code == 200, r.text[:200])
    r = client.get("/api/student/grammar-drills", headers=tok)
    drills = (r.json().get("drills") or r.json().get("items") or []) if r.status_code == 200 else []
    check("生徒のドリル一覧に 1 本", r.status_code == 200 and len(drills) == 1, f"status={r.status_code} n={len(drills)}")
    did = drills[0].get("id") or drills[0].get("drill_id") if drills else None
    r = client.get(f"/api/student/grammar-drill/{did}", headers=tok)
    qlist = (r.json() if r.status_code == 200 else {}).get("questions") or []
    check("取得 → 200・25 問・正解は伏せてある", r.status_code == 200 and len(qlist) == 25 and all(q.get("answer") is None for q in qlist), f"status={r.status_code} n={len(qlist)}")
    answers = {str(q.get("id") or q.get("question_id")): 0 for q in qlist}
    r = client.post(f"/api/student/grammar-drill/{did}/submit", json={"answers": answers}, headers=tok)
    check("提出 → 200・採点結果あり", r.status_code == 200 and r.json().get("score_total") == 25, f"status={r.status_code} body={r.text[:200]}")
    check("提出の応答に科目 chugaku_math (mypage が誤答の復習カードを「数学」に振り分ける)",
          r.status_code == 200 and r.json().get("subject") == "chugaku_math", str(r.json().get("subject") if r.status_code == 200 else r.status_code))
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT subject, topic, COUNT(*) AS n FROM question_attempts WHERE student_id = ? GROUP BY subject, topic", (sid,))
    rows = [dict(x) for x in c.fetchall()]
    conn.close()
    check(f"★解答は入試道場と同じ subject='chugaku' / topic='{unit}' で 25 件", rows == [{"subject": "chugaku", "topic": unit, "n": 25}], str(rows))
    # ★記録の文字列だけでなく「入試道場の記録と同じ弱点に合算される」ことまで見る。弱点のキー作り
    #   (_weakness_subject_key / _WEAKNESS_POOL_TO_SUBJECT) が変わって2つに割れても、上の検査は緑のままなので。
    #   入試道場を使えるのは AIあり の生徒なので、AIあり の中学生 B に同じドリルを解かせてから、
    #   入試道場 (dojo-drill.html) と同じ形 (subject なし・exam_id=chugaku・part_key=math・topic=単元名) で3問足す。
    sid_b = make_student(mod, "中学数学テスト B", "chumath-b@example.org", ai_disabled=0)
    tok_b = {"Authorization": "Bearer " + student_token(mod, sid_b)}
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar-drill/create", json={"subject": "chugaku_math", "unit": unit, "count": 25, "student_ids": [sid_b], "levels": ["standard", "advanced"]}, headers=adm)
    did_b = r.json().get("drill_id") if r.status_code == 200 else None
    r = client.get(f"/api/student/grammar-drill/{did_b}", headers=tok_b)
    qlist_b = (r.json() if r.status_code == 200 else {}).get("questions") or []
    r = client.post(f"/api/student/grammar-drill/{did_b}/submit", json={"answers": {str(q.get("id") or q.get("question_id")): 0 for q in qlist_b}}, headers=tok_b)
    check("AIあり の中学生 B もドリルを提出できる", r.status_code == 200 and r.json().get("score_total") == 25, f"status={r.status_code}")
    codes = []
    for _ in range(3):
        r = client.post("/api/question-attempts", json={"source": "practice", "exam_id": "chugaku", "part_key": "math",
                                                        "topic": unit, "is_correct": 0, "metadata": {"drill": True}}, headers=tok_b)
        codes.append(r.status_code)
    check("入試道場と同じ形の記録 (exam_id=chugaku / part_key=math) → 200", all(x == 200 for x in codes), str(codes))
    mod._run_weakness_aggregation(only_student_id=sid_b)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT subject, topic, question_count FROM student_weakness WHERE student_id = ?", (sid_b,))
    wrows = [dict(x) for x in c.fetchall()]
    conn.close()
    check(f"★弱点は入試道場とドリルが1行にまとまる (chugaku / {unit} / 25 + 3 = 28 件)",
          wrows == [{"subject": "chugaku", "topic": unit, "question_count": 28}], str(wrows))
    # 汎用の記録 API に教科名 (「中学数学」) で届いても 'chugaku' で保存する (週次レポートに別枠の科目を作らない)
    r = client.post("/api/question-attempts", json={"source": "practice", "subject": "中学数学", "topic": "一次関数", "is_correct": 1}, headers=tok_b)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT subject FROM question_attempts WHERE student_id = ? AND topic = ?", (sid_b, "一次関数"))
    srows = [x["subject"] for x in c.fetchall()]
    conn.close()
    check("記録 API に subject=「中学数学」→ 'chugaku' で保存", r.status_code == 200 and srows == ["chugaku"], f"status={r.status_code} rows={srows}")

    print("\n[5] 記録科目のヘルパが既存の挙動を変えない")
    f = mod._drill_attempt_subject
    check("中学英語 chugaku → chugaku", f("chugaku") == "chugaku")
    check("中学数学 chugaku_math → chugaku", f("chugaku_math") == "chugaku")
    check("高校 english → english・math → math・eiken → eiken", (f("english"), f("math"), f("eiken")) == ("english", "math", "eiken"))
    check("未指定 → english (従来の既定)", f(None) == "english" and f("") == "english")
    check("表記ゆれも中学にまとめる (「中学数学」・大文字)", f("中学数学") == "chugaku" and f(" CHUGAKU_MATH ") == "chugaku")
    k = mod._weakness_subject_key
    check("弱点キー: 中学の教科は 'chugaku' の1バケット (chugaku_math・「中学数学」・chugaku)",
          (k("chugaku_math"), k("中学数学"), k("chugaku")) == ("chugaku", "chugaku", "chugaku"))
    check("弱点キー: 高校の english / math / eiken・日本語の「数学」は変わらない",
          (k("english"), k("math"), k("eiken"), k("数学")) == ("english", "math", "eiken", "math"))

    print()
    if FAILURES:
        print(f"❌ FAIL: {len(FAILURES)} 件")
        for x in FAILURES:
            print("   -", x)
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
