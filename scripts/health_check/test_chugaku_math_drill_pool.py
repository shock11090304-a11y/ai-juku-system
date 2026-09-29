#!/usr/bin/env python3
"""🧒 中学の教科別ドリル (中学数学 chugaku_math・中学理科 chugaku_rika) の回帰テスト。
   ファイル名は最初の教科 (数学) のまま。教科を足すときは SUBJECTS に1行足す。

背景 (2026-09-28 塾長指示「さらに中学生用の問題を追加して」→ 数学・国語・理科・社会を1教科ずつ):
  中学の他教科は単元ドリルの **教科ごとの別科目** (chugaku_math・chugaku_rika …) にした。高校の math などには混ぜない。
  ★ただし生徒の解答は入試道場と同じ「中学」の1バケット subject='chugaku' ＋ topic=単元名 で記録する。
    中学生の弱点・週次プリント・弱点 TOP3 はその前提で組まれているため。

教科ごとに固定する性質:
  1. シードの形式: subject・unit は server の _GRAMMAR_SUBJECT_UNIT_ORDER[subject] と完全一致 (入試道場のカタログ順)・
     4 択相異・answer が範囲内・解説 60〜200 字で ①/「選択肢」が無い・stem 一意・半角 "-" が無い・
     図 (理科は表・グラフも) を前提にした問題が無い・高校範囲の語が無い (理科は旧用語「優性・劣性」も)
  2. 取込 API が全問受理し (再取込は 0 件)、ほかの科目のバンクは増えない
  3. 単元一覧がカタログ順で在庫つき・科目ラベル
  4. 中学生に配信 → 取得 → 提出 が通り、question_attempts は subject='chugaku' / topic=単元名 で記録される。
     入試道場と同じ形の記録と合算され、弱点 (student_weakness) が1行にまとまる。記録 API に教科名で届いても 'chugaku'
  5. 正解位置が単元ごとに散っている (どの位置も 40% 以下)・各単元で標準＋やや難が 50 問以上
     (既定25問のドリルを2回。🎯弱点対策は直前の1本を除外するので 50 を切ると2回目が 400 になる)
共通: 記録科目のヘルパ・弱点キーが中学の教科を 'chugaku' に寄せ、高校の科目は変えない

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
CATALOG = os.path.join(REPO, "scripts", "chugaku_dojo", "units.json")
sys.path.insert(0, os.path.join(REPO, "server"))

POSREF = re.compile(r"[①②③④]|選択肢")
SUBJECTS = [
    {"subject": "chugaku_math", "label": "中学数学", "seed": "chugaku_math_pool_v1.json", "part": "math", "min_n": 750,
     "email": "chumath", "record_topic": "一次関数",
     "hs": re.compile(r"sin|cos|tan|判別式|解と係数|log|数列|ベクトル|微分|積分|余弦定理|正弦定理"),
     "figure": re.compile(r"図のように|下の図|右の図|左の図|次の図"),
     "old_terms": None},
    {"subject": "chugaku_rika", "label": "中学理科", "seed": "chugaku_rika_pool_v1.json", "part": "rika", "min_n": 700,
     "email": "churika", "record_topic": "天気",
     "hs": re.compile(r"モル|物質量|アボガドロ|電気陰性度|酸化数|電離度|共有結合|イオン結合|金属結合|価電子|イオン化エネルギー|"
                      r"化学平衡|運動方程式|運動量|力積|万有引力|比熱|熱容量|半減期|同位体|フレミング"),
     "figure": re.compile(r"図のように|下の図|上の図|右の図|左の図|次の図|右図|左図|上図|下図|図[0-9０-９]|表[0-9０-９]|表のように|下の表|右の表|次の表|"
                          r"グラフのように|グラフから|下のグラフ|右のグラフ|\n"),
     "old_terms": re.compile(r"優性|劣性")},
]

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {detail}" if detail else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="chusubj_"), "test.db")
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
    spec = importlib.util.spec_from_file_location("aijuku_main_chusubj", MAIN_PY)
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


def deliver_and_submit(mod, client, adm, subject, unit, sid, tok):
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar-drill/create", json={"subject": subject, "unit": unit, "count": 25, "student_ids": [sid], "levels": ["standard", "advanced"]}, headers=adm)
    did = r.json().get("drill_id") if r.status_code == 200 else None
    r = client.get(f"/api/student/grammar-drill/{did}", headers=tok)
    qlist = (r.json() if r.status_code == 200 else {}).get("questions") or []
    answers = {str(q.get("id") or q.get("question_id")): 0 for q in qlist}
    return client.post(f"/api/student/grammar-drill/{did}/submit", json={"answers": answers}, headers=tok)


def run_subject(mod, client, adm, cfg, cat):
    subject, label = cfg["subject"], cfg["label"]
    print(f"\n━━━━ {label} ({subject}) ━━━━")
    seed_path = os.path.join(REPO, "seed-data", cfg["seed"])
    qs = json.load(open(seed_path, encoding="utf-8")).get("questions") or []
    cat_units = [u["filter"] for s in cat["subjects"] if s["part"] == cfg["part"] for u in s["units"] if not u.get("reading")]
    ORDER = mod._GRAMMAR_SUBJECT_UNIT_ORDER.get(subject) or []

    print("[1] シードの形式")
    check(f"問題数が {cfg['min_n']} 以上", len(qs) >= cfg["min_n"], f"n={len(qs)}")
    check(f"科目 {subject} が canonical・別名「{label}」", subject in mod._GRAMMAR_CANON_SUBJECTS and mod._canon_grammar_subject(label) == subject)
    check(f"単元の並び順が入試道場のカタログ ({cfg['part']}) と完全一致", ORDER == cat_units, f"server={ORDER}")
    bad = []
    seen = set()
    for i, q in enumerate(qs):
        tag = f"#{i}"
        if q.get("subject") != subject: bad.append(f"{tag}: subject {q.get('subject')!r}")
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
            if cfg["hs"].search(part): bad.append(f"{tag}: 高校範囲の語: {part[:30]}")
            if cfg["old_terms"] and cfg["old_terms"].search(part): bad.append(f"{tag}: 旧用語: {part[:30]}")
        if cfg["figure"].search(stem): bad.append(f"{tag}: 図・表を前提にしている / 本文に改行")
        if stem.strip() in seen: bad.append(f"{tag}: stem 重複")
        seen.add(stem.strip())
    check("全問が形式検査を通る", not bad, "; ".join(bad[:8]))
    by_unit, lv_unit = {}, {}
    for q in qs:
        by_unit.setdefault(q["unit"], [0, 0, 0, 0])
        lv_unit.setdefault(q["unit"], {"basic": 0, "standard": 0, "advanced": 0})
        if isinstance(q.get("answer"), int) and 0 <= q["answer"] <= 3:
            by_unit[q["unit"]][q["answer"]] += 1
        lv_unit[q["unit"]][q["level"]] += 1
    skew = {u: max(v) / max(1, sum(v)) for u, v in by_unit.items()}
    check("正解位置がどの単元でも 40% 以下", all(x <= 0.40 for x in skew.values()), str({u: round(x, 2) for u, x in skew.items() if x > 0.4}))
    check(f"全{len(ORDER)}単元に問題がある", set(by_unit) == set(ORDER), str(sorted(set(ORDER) - set(by_unit))))
    check("各単元で 標準＋やや難 が 50 問以上 (既定25問のドリルを2回・弱点対策の除外つき)",
          all(v["standard"] + v["advanced"] >= 50 for v in lv_unit.values()), str({u: v["standard"] + v["advanced"] for u, v in lv_unit.items()}))

    print("[2] 取込 API")
    before = count_by_subject(mod)
    inserted = skipped = 0
    for i in range(0, len(qs), 400):
        mod._RATE_LIMIT_STORE.clear()
        r = client.post("/api/admin/grammar/import", json={"questions": qs[i:i + 400], "subject": subject, "dedup": True}, headers=adm)
        check(f"POST import ({i + 1}〜) → 200", r.status_code == 200, r.text[:160])
        d = r.json() if r.status_code == 200 else {}
        inserted += int(d.get("inserted") or 0); skipped += int(d.get("skipped") or 0)
    check("全問が入る (inserted == 問題数・skipped 0)", inserted == len(qs) and skipped == 0, f"inserted={inserted} skipped={skipped}")
    after = count_by_subject(mod)
    others = set(before) | set(after)
    others.discard(subject)
    check("ほかの科目のバンクは増えない", all(after.get(k, 0) == before.get(k, 0) for k in others), f"before={before} after={after}")
    check(f"{subject} の在庫 = 問題数", after.get(subject, 0) == len(qs), f"{subject}={after.get(subject)}")
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar/import", json={"questions": qs[:50], "subject": subject, "dedup": True}, headers=adm)
    check("再取込は dedup で 0 件", r.status_code == 200 and int(r.json().get("inserted") or 0) == 0, r.text[:120])

    print("[3] 単元一覧とラベル")
    r = client.get("/api/admin/grammar/units", params={"subject": subject}, headers=adm)
    units = r.json().get("units", []) if r.status_code == 200 else []
    check(f"応答の subject が {subject} (画面の再デプロイ待ち判定が効く)", r.status_code == 200 and r.json().get("subject") == subject, r.text[:120])
    check("単元が入試道場のカタログ順", [u["unit"] for u in units][:len(ORDER)] == ORDER, str([u["unit"] for u in units]))
    check("各単元の在庫がシードの数と一致",
          all(next((u for u in units if u["unit"] == k), {}).get("total") == sum(v.values()) for k, v in lv_unit.items()),
          str({u["unit"]: u.get("total") for u in units}))
    check(f"科目ラベルは「{label}」", mod._grammar_subject_label_ja(subject) == label)

    print("[4] 中学生に配信 → 取得 → 提出 → 解答の記録")
    sid = make_student(mod, f"{label}テスト A", f"{cfg['email']}-a@example.org")
    tok = {"Authorization": "Bearer " + student_token(mod, sid)}
    unit = ORDER[0]
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/grammar-drill/create", json={"subject": subject, "unit": unit, "count": 25, "student_ids": [sid], "levels": ["standard", "advanced"]}, headers=adm)
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
    check(f"提出の応答に科目 {subject} (mypage が誤答の復習カードを教科別に振り分ける)",
          r.status_code == 200 and r.json().get("subject") == subject, str(r.json().get("subject") if r.status_code == 200 else r.status_code))
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT subject, topic, COUNT(*) AS n FROM question_attempts WHERE student_id = ? GROUP BY subject, topic", (sid,))
    rows = [dict(x) for x in c.fetchall()]
    conn.close()
    check(f"★解答は入試道場と同じ subject='chugaku' / topic='{unit}' で 25 件", rows == [{"subject": "chugaku", "topic": unit, "n": 25}], str(rows))
    # ★記録の文字列だけでなく「入試道場の記録と同じ弱点に合算される」ことまで見る。弱点のキー作り
    #   (_weakness_subject_key / _WEAKNESS_POOL_TO_SUBJECT) が変わって2つに割れても、上の検査は緑のままなので。
    #   入試道場を使えるのは AIあり の生徒なので、AIあり の中学生 B に同じドリルを解かせてから、
    #   入試道場 (dojo-drill.html) と同じ形 (subject なし・exam_id=chugaku・part_key=教科・topic=単元名) で3問足す。
    sid_b = make_student(mod, f"{label}テスト B", f"{cfg['email']}-b@example.org", ai_disabled=0)
    tok_b = {"Authorization": "Bearer " + student_token(mod, sid_b)}
    r = deliver_and_submit(mod, client, adm, subject, unit, sid_b, tok_b)
    check("AIあり の中学生 B もドリルを提出できる", r.status_code == 200 and r.json().get("score_total") == 25, f"status={r.status_code}")
    codes = []
    for _ in range(3):
        r = client.post("/api/question-attempts", json={"source": "practice", "exam_id": "chugaku", "part_key": cfg["part"],
                                                        "topic": unit, "is_correct": 0, "metadata": {"drill": True}}, headers=tok_b)
        codes.append(r.status_code)
    check(f"入試道場と同じ形の記録 (exam_id=chugaku / part_key={cfg['part']}) → 200", all(x == 200 for x in codes), str(codes))
    mod._run_weakness_aggregation(only_student_id=sid_b)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT subject, topic, question_count FROM student_weakness WHERE student_id = ?", (sid_b,))
    wrows = [dict(x) for x in c.fetchall()]
    conn.close()
    check(f"★弱点は入試道場とドリルが1行にまとまる (chugaku / {unit} / 25 + 3 = 28 件)",
          wrows == [{"subject": "chugaku", "topic": unit, "question_count": 28}], str(wrows))
    # 汎用の記録 API に教科名 (「中学数学」「中学理科」) で届いても 'chugaku' で保存する (週次レポートに別枠の科目を作らない)
    topic2 = cfg["record_topic"]
    r = client.post("/api/question-attempts", json={"source": "practice", "subject": label, "topic": topic2, "is_correct": 1}, headers=tok_b)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT subject FROM question_attempts WHERE student_id = ? AND topic = ?", (sid_b, topic2))
    srows = [x["subject"] for x in c.fetchall()]
    conn.close()
    check(f"記録 API に subject=「{label}」→ 'chugaku' で保存", r.status_code == 200 and srows == ["chugaku"], f"status={r.status_code} rows={srows}")


def main():
    print("🧒 中学の教科別ドリル 回帰テスト")
    cat = json.load(open(CATALOG, encoding="utf-8"))
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    for cfg in SUBJECTS:
        run_subject(mod, client, adm, cfg, cat)

    print("\n━━━━ 記録科目のヘルパ・弱点キー (既存の挙動を変えない) ━━━━")
    f = mod._drill_attempt_subject
    check("中学英語 chugaku → chugaku", f("chugaku") == "chugaku")
    check("中学の教科 (chugaku_math・chugaku_rika) → chugaku", f("chugaku_math") == "chugaku" and f("chugaku_rika") == "chugaku")
    check("高校 english → english・math → math・eiken → eiken", (f("english"), f("math"), f("eiken")) == ("english", "math", "eiken"))
    check("未指定 → english (従来の既定)", f(None) == "english" and f("") == "english")
    check("表記ゆれも中学にまとめる (「中学数学」「中学理科」・大文字)",
          f("中学数学") == "chugaku" and f("中学理科") == "chugaku" and f(" CHUGAKU_MATH ") == "chugaku")
    k = mod._weakness_subject_key
    check("弱点キー: 中学の教科は 'chugaku' の1バケット",
          (k("chugaku_math"), k("中学数学"), k("chugaku_rika"), k("中学理科"), k("chugaku")) == ("chugaku",) * 5)
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
