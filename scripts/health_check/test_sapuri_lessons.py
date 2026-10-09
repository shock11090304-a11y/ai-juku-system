#!/usr/bin/env python3
"""📺 スタサプ「弱点に合った回」— 段階 A (講データ不要の修正と D2 の徹底) の回帰テスト (2026-10-10)。

背景 (塾長決定 2026-10-09/10):
  D2 スタサプを勧めるのは授業コース (水3・金3・日のライブ授業) の在籍生だけ。オンラインの AI 学習管理コース
     (LP「国公立難関大学コース」= course は同じ kokuritsu_nankan・在籍クラスは空) には勧めない。
  D4 入塾した生徒だけ。本科生は承認時に status='trial'・trial_end +10 年で作られるので、長期 trial も在籍として扱う。
  既存の不具合: CurriculumPhase に欄が無く、保存 (POST/PUT) でスタサプが消えていた / 「学習計画に展開」が
     IntegrityError を拾って続けるため Postgres では 1 件の重複で全部 ROLLBACK されていた / AI が記憶で書いた
     講座名 (架空のことがある) をそのまま保存・表示していた。

固定する性質 (すべて実際のルートを TestClient で呼ぶ。講の題名は扱わない段階なので題名は出てこない):
  1. 対象判定 _sapuri_eligible_by_id: 3 コマ全部・本科の長期 trial は対象・2 コマだけ/コース外/退会/開始月が未来は対象外・
     停止スイッチ (CEO の POST /api/admin/sapuri/settings)・宣言と実行時のクラス名の不一致・GET /api/student/sapuri/status
  2. 学年帯 _sapuri_band
  3. カリキュラム: POST/PUT で sapuri が残る・旧形式の文字列は捨てる・対象外は空・materials のスタサプの語を捨てる・
     不正な要素で 422 にしない・GET /me で既存データもそろえる
  4. apply-gap-fix: クライアントの文字列は使わず new_sapuri だけを検査して足す
  5. expand-to-plans: ON CONFLICT DO NOTHING で重複が混ざっても他の行は入る・スタサプの科目はカタログの明示表
  6. AI 弱点プリント: AI 出力のスタサプを使わない・プロンプトでスタサプを書かせない
  7. ai-generate / gap-analyze: 対象生徒だけカタログを渡す・応答の検査
  8. /api/sapuri-lectures はカタログ (code/first/last) を返す・起動時に sapuri_lectures 表へ投入しない
  12. レビュー修正: milestones/focus/name のスタサプの語を消す (全生徒) / 停止スイッチ OFF の間の apply-gap-fix・PUT で
      保存済みの範囲を消さない (ON に戻すと出る) / 下書き (curriculum_draft) は読むときに今の判定でそろえる /
      展開済みのスタサプの計画は対象外に出さない (行は消さない) / /api/sapuri-lectures の version

実行:
    python3 scripts/health_check/test_sapuri_lessons.py
    # exit 0 = PASS / 1 = FAIL

外部通信は一切しない (AI は _call_gemini を差し替え)。DB は一時 SQLite。
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
JST = datetime.timezone(datetime.timedelta(hours=9))
LABELS3 = ["水曜3限 国公立コース 英文法", "金曜3限 国公立コース 長文読解", "日曜 高校国語"]


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="sapuri_"), "test.db")
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
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_sapuri", MAIN_PY)
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


def make_student(mod, name, email, *, labels=None, course="kokuritsu_nankan", status="trial", grade="高校3年",
                 start_month=None, trial_days=3650):
    conn = mod.db()
    c = conn.cursor()
    te = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=trial_days)).isoformat()
    c.execute(
        "INSERT INTO students (name, email, status, trial_end, course, grade, goal, ai_disabled, class_labels, start_month) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)",
        (name, email, status, te, course, grade, "国公立大学", json.dumps(labels or [], ensure_ascii=False), start_month),
    )
    conn.commit()
    c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
    sid = c.fetchone()["id"]
    conn.close()
    mod._SAPURI_ELIGIBLE_CACHE.pop(sid, None)
    return sid


def month_str(offset):
    d = datetime.datetime.now(JST).date().replace(day=1)
    y, m = d.year, d.month + offset
    while m > 12:
        m -= 12; y += 1
    while m < 1:
        m += 12; y -= 1
    return f"{y:04d}-{m:02d}"


class FakeGemini:
    """_call_gemini の差し替え。受け取ったプロンプトを残し、決めた JSON を返す。"""
    def __init__(self):
        self.calls = []
        self.reply = {}

    def __call__(self, body, model=None, kind="chat"):
        self.calls.append({"kind": kind, "system": body.get("system") or "",
                           "user": "".join(m.get("content", "") for m in body.get("messages") or [])})
        return {"content": [{"type": "text", "text": json.dumps(self.reply, ensure_ascii=False)}],
                "_actual_model": "fake-gemini"}


def phase(name, sd, ed, **kw):
    p = {"name": name, "start_date": sd, "end_date": ed, "focus": "テスト", "materials": [], "milestones": []}
    p.update(kw)
    return p


def main():
    print("📺 スタサプ 段階 A 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    mod._RATE_LIMIT_STORE.clear()

    sid_ok = make_student(mod, "スタサプ対象 A", "sapuri-a@example.org", labels=LABELS3)
    sid_ai = make_student(mod, "AI管理コース B", "sapuri-b@example.org", labels=[])            # オンラインの AI 学習管理コース
    sid_two = make_student(mod, "2コマだけ C", "sapuri-c@example.org", labels=LABELS3[:2])
    sid_nocourse = make_student(mod, "コース外 D", "sapuri-d@example.org", labels=LABELS3, course=None)
    sid_cancel = make_student(mod, "退会 E", "sapuri-e@example.org", labels=LABELS3, status="canceled")
    sid_future = make_student(mod, "翌月開始 F", "sapuri-f@example.org", labels=LABELS3, start_month=month_str(1))
    sid_now = make_student(mod, "今月開始 G", "sapuri-g@example.org", labels=LABELS3 + ["月曜1限 中学応用"],
                           start_month=month_str(0), grade="高校２年")
    tok = lambda sid: {"Authorization": "Bearer " + student_token(mod, sid)}

    print("[0] 起動時に旧初期データを投入しない・カタログ定数")
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) AS n FROM sapuri_lectures")
    n_rows = c.fetchone()["n"]
    conn.close()
    check("sapuri_lectures 表は起動時に埋められない (0 行)", n_rows == 0, n_rows)
    check("旧初期データの定数は消えている", not hasattr(mod, "SAPURI_LECTURES_SEED"))
    check("SAPURI_COURSES は 138 講座", len(mod.SAPURI_COURSES) == 138, len(mod.SAPURI_COURSES))
    check("_UNIT_TAG_ALIASES は module 定数 (週次プリントと共用)", mod._UNIT_TAG_ALIASES.get("関係代名詞") == "関係詞")

    print("\n[1] 対象判定")
    E = mod._sapuri_eligible_by_id
    r = E(sid_ok)
    check("3 コマ全部 + 本科の長期 trial (status=trial・trial_end +10 年) は対象", r["eligible"] is True and r["reason"] == "ok", r)
    check("学年帯 高校3年 → 高3", r["band"] == "高3", r)
    check("AI 学習管理コース (在籍クラス空) は対象外 (labels)", E(sid_ai) == {"eligible": False, "reason": "labels", "band": "高3"}, E(sid_ai))
    check("2 コマだけは対象外 (部分一致しない)", E(sid_two)["reason"] == "labels", E(sid_two))
    check("course が国公立難関でない生徒は対象外", E(sid_nocourse)["reason"] == "not_course", E(sid_nocourse))
    check("退会 (canceled) は対象外", E(sid_cancel)["reason"] == "not_enrolled", E(sid_cancel))
    check("受講開始月が未来は対象外", E(sid_future)["reason"] == "not_started", E(sid_future))
    rn = E(sid_now)
    check("受講開始月が今月なら対象・他のクラスが増えていても対象", rn["eligible"] is True, rn)
    check("学年帯 高校２年 (全角) → 高1・2", rn["band"] == "高1・2", rn)
    check("存在しない生徒は対象外", E(99999)["eligible"] is False)

    # 宣言と実行時のラベル (起動時の自己修復で縮んだ一覧) の不一致
    orig = list(mod._COURSE_CLASSES[mod._SAPURI_COURSE_NAME])
    try:
        mod._COURSE_CLASSES[mod._SAPURI_COURSE_NAME] = orig[:2]
        mod._SAPURI_ELIGIBLE_CACHE.clear()
        check("実行時の一覧が縮むと config_ok=False", mod._sapuri_config_ok()[0] is False)
        check("縮んだ一覧のとき 2 コマの生徒が対象に広がらない (config)", E(sid_two)["reason"] == "config", E(sid_two))
        check("縮んだ一覧のとき 3 コマの生徒も止まる (config)", E(sid_ok)["reason"] == "config", E(sid_ok))
    finally:
        mod._COURSE_CLASSES[mod._SAPURI_COURSE_NAME] = orig
        mod._SAPURI_ELIGIBLE_CACHE.clear()
    check("宣言と実行時が一致 (順不同) → config_ok", mod._sapuri_config_ok()[0] is True)

    # 停止スイッチ (CEO)
    r = client.post("/api/admin/sapuri/settings", json={"enabled": False})
    check("停止スイッチは管理者だけ (未認証 401)", r.status_code == 401, r.status_code)
    r = client.post("/api/admin/sapuri/settings", json={"enabled": False}, headers=adm)
    check("停止スイッチ OFF が保存できる", r.status_code == 200 and r.json().get("enabled") is False, r.text)
    check("OFF の間は対象生徒も disabled", E(sid_ok)["reason"] == "disabled", E(sid_ok))
    st = client.get("/api/student/sapuri/status", headers=tok(sid_ok))
    check("OFF の間は status API も eligible=false", st.status_code == 200 and st.json().get("eligible") is False, st.text)
    g = client.get("/api/admin/sapuri/settings", headers=adm).json()
    check("GET settings に enabled=false と config_ok", g.get("enabled") is False and g.get("config_ok") is True, g)
    r = client.post("/api/admin/sapuri/settings", json={"enabled": True}, headers=adm)
    check("停止スイッチを ON に戻せる", r.status_code == 200 and E(sid_ok)["eligible"] is True, E(sid_ok))

    print("\n[2] 学年帯 _sapuri_band")
    B = mod._sapuri_band
    for g_, want in [("高1", "高1・2"), ("高２", "高1・2"), ("高校1年生", "高1・2"), ("高校２年", "高1・2"), ("高一", "高1・2"),
                     ("高二", "高1・2"), ("高3", "高3"), ("高校3年", "高3"), ("高三", "高3"), ("既卒", "高3"), ("浪人", "高3"),
                     ("", "高3"), (None, "高3"), ("その他", "高3")]:
        check(f"{g_!r} → {want}", B(g_) == want, B(g_))

    print("\n[3] /api/student/sapuri/status")
    r = client.get("/api/student/sapuri/status")
    check("未ログインは 401", r.status_code == 401, r.status_code)
    d = client.get("/api/student/sapuri/status", headers=tok(sid_ok)).json()
    check("対象生徒は eligible=true・lessons_loaded=false (段階 A)", d.get("eligible") is True and d.get("lessons_loaded") is False, d)
    check("対象生徒には講座コードの一覧 (共通テスト対策は入らない)",
          "MKZ118000_2" in d.get("course_codes", []) and "X-kyotsu-eng-reading" not in d.get("course_codes", []), d)
    d = client.get("/api/student/sapuri/status", headers=tok(sid_ai)).json()
    check("対象外は eligible=false・講座コードなし・理由は返さない",
          d.get("eligible") is False and d.get("course_codes") == [] and "reason" not in d, d)

    print("\n[4] /api/sapuri-lectures (カタログ・題名なし)")
    d = client.get("/api/sapuri-lectures?limit=200").json()
    lec = d.get("lectures") or []
    check("全 138 講座を返す", d.get("count") == 138 and len(lec) == 138, d.get("count"))
    one = next((x for x in lec if x.get("code") == "MKZ118000_2"), {})
    check("分割講座は first/last (総合問題編 41〜48)", one.get("first") == 41 and one.get("last") == 48 and one.get("total_lessons") == 8, one)
    check("互換の項目 (name/level/grade/subject/sub_genre/total_lessons/suitable_dev_min/max/weeks_to_complete/notes) と has_lessons",
          all(k in one for k in ("name", "level", "grade", "subject", "sub_genre", "total_lessons", "suitable_dev_min",
                                 "suitable_dev_max", "weeks_to_complete", "notes", "has_lessons")), one)
    check("講の題名・講の一覧の項目は無い", not any(k in one for k in ("title", "titles", "lessons")), list(one))
    d2 = client.get("/api/sapuri-lectures?subject=数学&dev=60").json()
    check("subject / dev で絞れる", d2.get("count", 0) > 0 and all(x["subject"] == "数学" for x in d2["lectures"]), d2.get("count"))
    check("既定の limit は 50", client.get("/api/sapuri-lectures").json().get("count") == 50)

    print("\n[5] カリキュラム POST/PUT/GET (スタサプ欄が消えない・旧文字列を捨てる・対象外は空)")
    today = mod._today_jst()
    sd, ed = today.isoformat(), (today + datetime.timedelta(days=200)).isoformat()
    mid = (today + datetime.timedelta(days=100)).isoformat()
    phases = [
        phase("基礎期", sd, mid,
              materials=["ポラリス1", "スタサプ 高3 架空レベル英文法", "スタディサプリで復習"],
              sapuri=[{"course_code": "MKZ118000_2", "from_seq": 41, "to_seq": 44},
                      {"course_code": "MKZ118000_2", "from_seq": 46, "to_seq": 46},   # 同じ講座 → 統合 41〜46
                      {"course_code": "KZ016000", "from_seq": 3, "to_seq": 3},
                      {"course_code": "KZA01000", "from_seq": 0, "to_seq": 3},        # 範囲外 → 捨てる
                      {"course_code": "NO-SUCH", "from_seq": 1, "to_seq": 2},         # 実在しない → 捨てる
                      {"course_code": "X-kyotsu-eng-reading", "from_seq": 1, "to_seq": 1},  # 講数非公開 → 捨てる
                      "壊れた要素", {"course_code": "KZA02000", "from_seq": "x"}],
              sapuri_lectures=["高3 テスト講義A (架空)"]),
        phase("演習期", mid, ed, materials=["過去問"], sapuri_lectures=["高3 架空講座"]),
    ]
    body = {"target_university": "テスト大学", "exam_date": ed, "start_date": sd, "phases": phases}
    r = client.post("/api/curricula", json=body, headers=tok(sid_ok))
    check("POST: 不正な要素が混ざっても 422 にしない", r.status_code == 200, r.text)
    cur = client.get("/api/curricula/me", headers=tok(sid_ok)).json()["curricula"][0]
    p0, p1 = cur["phases"][0], cur["phases"][1]
    check("POST: sapuri が保存される (検査を通った分だけ・重複は統合)",
          p0.get("sapuri") == [{"course_code": "MKZ118000_2", "from_seq": 41, "to_seq": 46},
                               {"course_code": "KZ016000", "from_seq": 3, "to_seq": 3}], p0.get("sapuri"))
    check("POST: sapuri_lectures はカタログから作り直す (「講座名 第a〜b講」/「第a講」)",
          p0.get("sapuri_lectures") == ["高3 スタンダードレベル数学IAIIB＋C（ベクトル）＜総合問題編＞ 第41〜46講",
                                        "高3 古文＜文法編＞ 第3講"], p0.get("sapuri_lectures"))
    check("POST: 旧形式の文字列だけのフェーズは空", p1.get("sapuri") == [] and p1.get("sapuri_lectures") == [], p1)
    check("POST: materials のスタサプの語を含む要素を捨てる", p0.get("materials") == ["ポラリス1"], p0.get("materials"))
    cid = cur["id"]
    phases2 = [phase("基礎期", sd, ed, materials=["ポラリス2"],
                     sapuri=[{"course_code": "KZA02000", "from_seq": 1, "to_seq": 6}], sapuri_lectures=["架空"])]
    r = client.put(f"/api/curricula/{cid}", json={"phases": phases2}, headers=tok(sid_ok))
    check("PUT が通る", r.status_code == 200, r.text)
    p = client.get("/api/curricula/me", headers=tok(sid_ok)).json()["curricula"][0]["phases"][0]
    check("PUT: sapuri が残る (従来は pydantic が捨てて消えていた)",
          p.get("sapuri") == [{"course_code": "KZA02000", "from_seq": 1, "to_seq": 6}]
          and p.get("sapuri_lectures") == ["高3 ハイレベル英語＜文法編＞ 第1〜6講"], p)

    # 対象外の生徒 (AI 学習管理コース): 保存しても空・既存データ (旧形式の文字列) も /me で出さない
    r = client.post("/api/curricula", json=body, headers=tok(sid_ai))
    check("対象外: POST は通る", r.status_code == 200, r.text)
    cur_ai = client.get("/api/curricula/me", headers=tok(sid_ai)).json()["curricula"][0]
    check("対象外: sapuri / sapuri_lectures は空", all(x.get("sapuri") == [] and x.get("sapuri_lectures") == [] for x in cur_ai["phases"]),
          cur_ai["phases"])
    conn = mod.db(); c = conn.cursor()
    legacy = [{"name": "旧", "start_date": sd, "end_date": ed, "focus": "", "materials": ["スタサプ 架空講座", "青チャート"],
               "milestones": [], "sapuri_lectures": ["高3 架空レベル数学 (AI が書いた名前)"]}]
    c.execute("UPDATE curricula SET phases = ? WHERE id = ?", (json.dumps(legacy, ensure_ascii=False), cur_ai["id"]))
    conn.commit(); conn.close()
    p = client.get("/api/curricula/me", headers=tok(sid_ai)).json()["curricula"][0]["phases"][0]
    check("対象外: DB に残った旧形式のスタサプは /me で出さない", p.get("sapuri_lectures") == [] and p.get("materials") == ["青チャート"], p)
    # 対象生徒でも旧形式の文字列 (sapuri の無いもの) は出さない
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE curricula SET phases = ? WHERE id = ?", (json.dumps(legacy, ensure_ascii=False), cid))
    conn.commit(); conn.close()
    p = client.get("/api/curricula/me", headers=tok(sid_ok)).json()["curricula"][0]["phases"][0]
    check("対象生徒でも旧形式の文字列だけのスタサプは /me で出さない", p.get("sapuri_lectures") == [], p)

    print("\n[6] apply-gap-fix (new_sapuri だけを検査して足す)")
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE curricula SET phases = ? WHERE id = ?",
              (json.dumps([phase("基礎期", sd, ed, materials=["ポラリス1"],
                                 sapuri=[{"course_code": "KZA02000", "from_seq": 1, "to_seq": 6}])], ensure_ascii=False), cid))
    conn.commit(); conn.close()
    adjs = [{"phase_index": 0, "action": "スタサプ追加",
             "new_materials": ["やっておきたい500", "スタサプ 架空講座"],
             "new_sapuri_lectures": ["高3 架空講座 第1〜3講"],
             "new_sapuri": [{"course_code": "KZA02000", "from_seq": 7, "to_seq": 10},
                            {"course_code": "KZ016000", "from_seq": 20, "to_seq": 30}]}]   # 範囲外 → 捨てる
    r = client.post(f"/api/curricula/{cid}/apply-gap-fix", json={"phase_adjustments": adjs}, headers=tok(sid_ok))
    check("apply-gap-fix が通る", r.status_code == 200 and r.json().get("applied") == 1, r.text)
    p = client.get("/api/curricula/me", headers=tok(sid_ok)).json()["curricula"][0]["phases"][0]
    check("同じ講座の範囲は統合 (1〜10)・範囲外は入らない",
          p.get("sapuri") == [{"course_code": "KZA02000", "from_seq": 1, "to_seq": 10}], p.get("sapuri"))
    check("クライアントの文字列 (new_sapuri_lectures) は保存されない",
          p.get("sapuri_lectures") == ["高3 ハイレベル英語＜文法編＞ 第1〜10講"], p.get("sapuri_lectures"))
    check("new_materials のスタサプの語を含む要素は入らない", p.get("materials") == ["ポラリス1", "やっておきたい500"], p.get("materials"))
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT phases FROM curricula WHERE id = ?", (cid,))
    raw = json.loads(c.fetchone()["phases"])
    conn.close()
    check("DB に書く JSON も検査済みの形", raw[0].get("sapuri_lectures") == ["高3 ハイレベル英語＜文法編＞ 第1〜10講"], raw[0])
    cid_ai = cur_ai["id"]
    r = client.post(f"/api/curricula/{cid_ai}/apply-gap-fix", json={"phase_adjustments": adjs}, headers=tok(sid_ai))
    p = client.get("/api/curricula/me", headers=tok(sid_ai)).json()["curricula"][0]["phases"][0]
    check("対象外: new_sapuri は足さない", r.status_code == 200 and p.get("sapuri") == [] and p.get("sapuri_lectures") == [], p)

    print("\n[7] expand-to-plans (ON CONFLICT DO NOTHING・スタサプの科目はカタログ)")
    conn = mod.db(); c = conn.cursor()
    ph = [phase("基礎期", sd, ed, materials=["ポラリス1", "青チャート"],
                sapuri=[{"course_code": "KZ016000", "from_seq": 1, "to_seq": 4},
                        {"course_code": "KZA02000", "from_seq": 1, "to_seq": 6}])]
    c.execute("UPDATE curricula SET phases = ? WHERE id = ?", (json.dumps(ph, ensure_ascii=False), cid))
    # 先に 1 件だけ同じ計画を入れておく (uq_study_plans_no_dup = 生徒・科目・教材・期間 に当たる。
    #   市販教材の科目は _guess_subject の推測で「ポラリス1」は その他)
    c.execute("INSERT INTO study_plans (student_id, title, subject, material, start_date, end_date, target_minutes, color, note) "
              "VALUES (?,?,?,?,?,?,?,?,?)", (sid_ok, "既存", "その他", "ポラリス1", sd, ed, 60, "#000000", "既存"))
    conn.commit(); conn.close()
    r = client.post(f"/api/curricula/{cid}/expand-to-plans", headers=tok(sid_ok))
    j = r.json() if r.status_code == 200 else {}
    check("重複が 1 件混ざっても 200", r.status_code == 200, r.text)
    check("重複以外の 3 件は入る (added=3・skipped=1)", j.get("added") == 3 and j.get("skipped") == 1, j)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT subject, material, title, note FROM study_plans WHERE student_id = ? ORDER BY id", (sid_ok,))
    rows = [dict(r_) for r_ in c.fetchall()]
    conn.close()
    kobun = next((x for x in rows if x["material"] == "高3 古文＜文法編＞ 第1〜4講"), None)
    check("スタサプは「講座名 第a〜b講」で展開・科目はカタログ (国語 古文文法 → 古文)",
          bool(kobun) and kobun["subject"] == "古文" and "📺" in kobun["title"] and "スタサプ" in kobun["note"], kobun)
    eng = next((x for x in rows if x["material"] == "高3 ハイレベル英語＜文法編＞ 第1〜6講"), None)
    check("英語の講座は 英語", bool(eng) and eng["subject"] == "英語", eng)
    check("既存の計画は 1 件のまま (二重にならない)", sum(1 for x in rows if x["material"] == "ポラリス1") == 1, rows)
    r = client.post(f"/api/curricula/{cid}/expand-to-plans", headers=tok(sid_ok))
    check("押し直しても増えない (added=0)", r.status_code == 200 and r.json().get("added") == 0, r.text)
    src = open(MAIN_PY, encoding="utf-8").read()
    fn = src[src.index("def expand_curriculum_to_plans("):src.index("class AdminAiDraftRequest")]
    check("expand は ON CONFLICT DO NOTHING RETURNING (IntegrityError を拾って続けない)",
          "ON CONFLICT DO NOTHING RETURNING id" in fn and "except IntegrityError" not in fn)
    # 対象外の生徒: 旧形式のスタサプ文字列は展開しない
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE curricula SET phases = ? WHERE id = ?", (json.dumps(legacy, ensure_ascii=False), cid_ai))
    conn.commit(); conn.close()
    r = client.post(f"/api/curricula/{cid_ai}/expand-to-plans", headers=tok(sid_ai))
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT material FROM study_plans WHERE student_id = ?", (sid_ai,))
    mats = [x["material"] for x in c.fetchall()]
    conn.close()
    check("対象外: 旧形式のスタサプ・スタサプの語の教材は計画にしない", r.status_code == 200 and mats == ["青チャート"], mats)

    print("\n[8] AI 弱点プリント (AI 出力のスタサプを使わない)")
    fake = FakeGemini()
    mod._call_gemini = fake
    mod.GEMINI_API_KEY = "test-key"
    fake.reply = {"topic_used": "関係詞", "weak_point_analysis": "テスト",
                  "problems": [{"no": 1, "difficulty": "標準", "question": "Q", "answer": "A", "explanation": "E"}],
                  "sapuri_lectures": [{"title": "高3 テスト講義A (AI が書いた名前)", "level": "ハイレベル", "reason": "x"}]}
    for sid in (sid_ok, sid_ai):
        r = client.post("/api/weak-points/generate-worksheet", json={"subject": "英語", "topic": "関係詞", "num_problems": 3},
                        headers=tok(sid))
        j = r.json() if r.status_code == 200 else {}
        check(f"生徒 {sid}: 200 で sapuri_lectures は常に [] (AI が書いても使わない)", r.status_code == 200 and j.get("sapuri_lectures") == [], r.text)
    last = fake.calls[-1]
    check("プロンプトでスタサプの推薦を求めない (出力形式に sapuri_lectures が無い)",
          "sapuri_lectures" not in last["user"] and "スタサプ講義" not in last["user"] and "スタサプ" not in last["system"], last)

    print("\n[9] ai-generate (対象生徒だけカタログを渡す・応答を検査)")
    fake.calls.clear()
    fake.reply = {"phases": [phase("基礎期", sd, ed, materials=["ポラリス1", "スタサプ 架空講座"],
                                   sapuri=[{"course_code": "MKZ118000_2", "from_seq": 41, "to_seq": 48},
                                           {"course_code": "MKZ118000_2", "from_seq": 1, "to_seq": 2}],   # 範囲外
                                   sapuri_lectures=["高3 テスト講義B (AI)"])]}
    gen = {"target_university": "テスト大学", "exam_date": ed, "start_date": sd, "daily_minutes": 60}
    r = client.post("/api/curricula/ai-generate", json=gen, headers=tok(sid_ok))
    j = r.json() if r.status_code == 200 else {}
    pp = (j.get("preview") or {}).get("phases") or [{}]
    check("対象生徒: プレビューの sapuri は検査済み・文字列はカタログから",
          r.status_code == 200 and pp[0].get("sapuri") == [{"course_code": "MKZ118000_2", "from_seq": 41, "to_seq": 48}]
          and pp[0].get("sapuri_lectures") == ["高3 スタンダードレベル数学IAIIB＋C（ベクトル）＜総合問題編＞ 第41〜48講"]
          and pp[0].get("materials") == ["ポラリス1"], r.text)
    u = fake.calls[-1]["user"]
    check("対象生徒: プロンプトに講座カタログ (コード) が入る", "スタディサプリ講座カタログ" in u and "KZA02000" in u, u[-400:])
    r = client.post("/api/curricula/ai-generate", json=gen, headers=tok(sid_ai))
    j = r.json() if r.status_code == 200 else {}
    pp = (j.get("preview") or {}).get("phases") or [{}]
    call = fake.calls[-1]
    check("対象外: プレビューのスタサプは空", r.status_code == 200 and pp[0].get("sapuri") == [] and pp[0].get("sapuri_lectures") == [], r.text)
    check("対象外: カタログを渡さず「使わない・書かない」と指示",
          "スタディサプリ講座カタログ" not in call["user"] and "KZA02000" not in call["user"] and "使わない" in call["system"], call["system"])

    print("\n[10] gap-analyze (対象外は「スタサプ追加」を読み替え・スタサプの提案を捨てる)")
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO exam_results (student_id, exam_name, exam_date, subject, deviation) VALUES (?,?,?,?,?)",
              (sid_ai, "テスト模試", sd, "数学", 55.0))
    c.execute("INSERT INTO exam_results (student_id, exam_name, exam_date, subject, deviation) VALUES (?,?,?,?,?)",
              (sid_ok, "テスト模試", sd, "数学", 61.0))
    conn.commit(); conn.close()
    fake.reply = {"target_deviation": "65", "current_average": "55", "gap_summary": "数学が課題。スタサプで補強しよう。全体は順調。",
                  "subject_gaps": [],
                  "phase_adjustments": [
                      {"phase_index": 0, "action": "スタサプ追加", "detail": "数学の演習量を増やす", "new_materials": ["1対1対応"],
                       "new_sapuri_lectures": ["高3 架空講座"],
                       "new_sapuri": [{"course_code": "MKZ371000", "from_seq": 1, "to_seq": 5}]},
                      {"phase_index": 0, "action": "教材追加", "detail": "スタディサプリの講座を見る", "new_materials": []},
                  ], "overall_recommendation": "毎日続ける。"}
    r = client.post(f"/api/curricula/{cid_ai}/gap-analyze", headers=tok(sid_ai))
    a = r.json().get("analysis", {}) if r.status_code == 200 else {}
    adj = a.get("phase_adjustments") or []
    check("対象外: 200", r.status_code == 200, r.text)
    check("対象外: スタサプの語を含む提案は捨て、残りは「教材追加」に読み替え・スタサプは空",
          len(adj) == 1 and adj[0]["action"] == "教材追加" and adj[0]["new_sapuri"] == [] and adj[0]["new_sapuri_lectures"] == [], adj)
    check("対象外: 総合分析からスタサプの文を落とす", "スタサプ" not in a.get("gap_summary", "") and "全体は順調" in a.get("gap_summary", ""), a.get("gap_summary"))
    check("対象外: プロンプトの選択肢に「スタサプ追加」が無い", "スタサプ追加" not in fake.calls[-1]["user"])
    r = client.post(f"/api/curricula/{cid}/gap-analyze", headers=tok(sid_ok))
    a = r.json().get("analysis", {}) if r.status_code == 200 else {}
    adj = a.get("phase_adjustments") or []
    check("対象生徒: new_sapuri を検査して new_sapuri_lectures を作り直す (AI の文字列は使わない)",
          r.status_code == 200 and adj and adj[0]["new_sapuri"] == [{"course_code": "MKZ371000", "from_seq": 1, "to_seq": 5}]
          and adj[0]["new_sapuri_lectures"] == ["高3 トップレベル数学IAIIB＋C（ベクトル） 第1〜5講"], adj)
    check("対象生徒: プロンプトにカタログと「スタサプ追加」", "スタディサプリ講座カタログ" in fake.calls[-1]["user"]
          and "スタサプ追加" in fake.calls[-1]["user"])

    print("\n[11] 弱点 topic の解析と偏差値 (段階 B の部品)")
    P = mod._sapuri_parse_topic
    check("英文法 関係代名詞(主格) → eng_grammar / 関係詞", P("english", "関係代名詞(主格)")["tag"] == "関係詞")
    check("倒置・強調 → 2 タグの和集合", P("english", "倒置・強調")["tags"] == ["倒置", "強調"])
    check("english の長文 (語彙外) は科目を決めない", P("english", "長文読解")["subject_key"] is None)
    check("物理基礎の接頭辞 → physics_basic", P("physics", "物理基礎 運動")["subject_key"] == "physics_basic")
    check("japanese の 句法 → kanbun", P("japanese", "句法(反語)")["subject_key"] == "kanbun")
    check("social の時代タグは科目を決めない (part_key 解決へ)", P("social", "中世(元寇)")["subject_key"] is None)
    check("共通テスト… はタグなし", P("english", "共通テスト英語 第3問")["tag"] is None)
    conn = mod.db(); c = conn.cursor()
    check("偏差値: 科目の最新 (数学 61)", mod._sapuri_dev_for(c, sid_ok, "math") == 61.0)
    check("偏差値: 科目が無ければ全科目の平均", mod._sapuri_dev_for(c, sid_ok, "kobun") == 61.0)
    check("偏差値: 模試が無ければ 60", mod._sapuri_dev_for(c, sid_two, "math") == 60.0)
    conn.close()

    print("\n[12] 段階 A レビューの修正 (自由記述・書くときに消さない・下書き・展開済みの計画・講数表の版)")
    switch = lambda on: client.post("/api/admin/sapuri/settings", json={"enabled": on}, headers=adm)
    # (a) milestones / focus / name のスタサプの語 (旧プロンプトはスタサプを各フェーズに必須にしていた)
    ph_txt = [phase("スタサプ期", sd, ed, focus="英文法を固める。スタサプで毎日1講見る。",
                    milestones=["スタサプ 高3 架空レベル英文法 全24講 視聴完了", "模試で偏差値60"],
                    sapuri=[{"course_code": "KZA02000", "from_seq": 1, "to_seq": 2}])]
    r = client.post("/api/curricula", json=dict(body, phases=ph_txt), headers=tok(sid_ok))
    cid_txt = r.json().get("id") if r.status_code == 200 else None
    got = next((x for x in client.get("/api/curricula/me", headers=tok(sid_ok)).json()["curricula"] if x["id"] == cid_txt), {})
    p = (got.get("phases") or [{}])[0]
    check("POST: milestones のスタサプの語を含む要素は捨てる (全生徒)", p.get("milestones") == ["模試で偏差値60"], p.get("milestones"))
    check("POST: focus はスタサプの文だけ落とす", p.get("focus") == "英文法を固める。", p.get("focus"))
    check("POST: name にスタサプの語があれば「フェーズ」", p.get("name") == "フェーズ", p.get("name"))
    check("POST: スタサプはキー (sapuri) からだけ出る", p.get("sapuri_lectures") == ["高3 ハイレベル英語＜文法編＞ 第1〜2講"], p)
    legacy_txt = [{"name": "基礎期", "start_date": sd, "end_date": ed,
                   "focus": "基礎を固める。スタディサプリのハイレベル英文法で文法を仕上げる。",
                   "materials": ["青チャート"], "milestones": ["スタサプ 高3 ハイレベル英文法 全24講 視聴完了", "青チャート例題1周"]}]
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE curricula SET phases = ? WHERE id = ?", (json.dumps(legacy_txt, ensure_ascii=False), cid_ai))
    conn.commit(); conn.close()
    p = next(x for x in client.get("/api/curricula/me", headers=tok(sid_ai)).json()["curricula"] if x["id"] == cid_ai)["phases"][0]
    check("/me: 保存済みの milestones のスタサプは出さない", p.get("milestones") == ["青チャート例題1周"], p.get("milestones"))
    check("/me: 保存済みの focus のスタサプの文は出さない", p.get("focus") == "基礎を固める。", p.get("focus"))
    fake.reply = {"phases": [phase("基礎期", sd, ed, focus="長文を読む。スタサプで補強。", milestones=["スタサプ 全講修了", "過去問5年"])]}
    r = client.post("/api/curricula/ai-generate", json=gen, headers=tok(sid_ai))
    pp = ((r.json() if r.status_code == 200 else {}).get("preview") or {}).get("phases") or [{}]
    check("ai-generate (_validate_curr_phases): milestones・focus のスタサプも消す",
          pp[0].get("milestones") == ["過去問5年"] and pp[0].get("focus") == "長文を読む。", pp[0])

    # (b) 停止スイッチ OFF の間の apply-gap-fix / PUT で保存済みの範囲を消さない (読むときに隠す・書くときに消さない)
    ph_two = [phase("前期", sd, mid, materials=["ポラリス1"], sapuri=[{"course_code": "KZA02000", "from_seq": 1, "to_seq": 6}]),
              phase("後期", mid, ed, materials=["過去問"], sapuri=[{"course_code": "KZA02000", "from_seq": 7, "to_seq": 12}])]
    r = client.post("/api/curricula", json=dict(body, phases=ph_two), headers=tok(sid_ok))
    cid_two = r.json().get("id") if r.status_code == 200 else None
    want_sp = [[{"course_code": "KZA02000", "from_seq": 1, "to_seq": 6}], [{"course_code": "KZA02000", "from_seq": 7, "to_seq": 12}]]
    def me_two():
        return next(x for x in client.get("/api/curricula/me", headers=tok(sid_ok)).json()["curricula"] if x["id"] == cid_two)["phases"]
    def raw_two():
        conn_ = mod.db(); c_ = conn_.cursor()
        c_.execute("SELECT phases FROM curricula WHERE id = ?", (cid_two,))
        v = json.loads(c_.fetchone()["phases"]); conn_.close()
        return v
    check("前提: 2 フェーズとも範囲が保存されている", [x.get("sapuri") for x in me_two()] == want_sp, me_two())
    switch(False)
    try:
        check("OFF: /me では隠れる", all(x.get("sapuri") == [] and x.get("sapuri_lectures") == [] for x in me_two()), me_two())
        r = client.post(f"/api/curricula/{cid_two}/apply-gap-fix",
                        json={"phase_adjustments": [{"phase_index": 0, "action": "教材追加", "new_materials": ["ネクステ"],
                                                     "new_sapuri": [{"course_code": "KZ016000", "from_seq": 1, "to_seq": 3}]}]},
                        headers=tok(sid_ok))
        check("OFF: apply-gap-fix は通る", r.status_code == 200 and r.json().get("applied") == 1, r.text)
        raw = raw_two()
        check("OFF: apply-gap-fix のあとも DB の範囲は 2 フェーズとも残る (新しいスタサプは足さない)",
              [x.get("sapuri") for x in raw] == want_sp and "ネクステ" in raw[0].get("materials", []), raw)
        # PUT: 画面 (/me) から受け取った phases (sapuri は空) を送り直す + 新しいスタサプを混ぜる
        put_ph = me_two()
        put_ph[1] = dict(put_ph[1], sapuri=[{"course_code": "KZ016000", "from_seq": 1, "to_seq": 3}])
        r = client.put(f"/api/curricula/{cid_two}", json={"phases": put_ph}, headers=tok(sid_ok))
        check("OFF: PUT は通る", r.status_code == 200, r.text)
        check("OFF: PUT で送り直しても保存済みの範囲は残り、新しいスタサプは入らない",
              [x.get("sapuri") for x in raw_two()] == want_sp, raw_two())
    finally:
        switch(True)
    got = me_two()
    check("ON に戻すと 2 フェーズとも元の範囲が出る", [x.get("sapuri") for x in got] == want_sp
          and got[1].get("sapuri_lectures") == ["高3 ハイレベル英語＜文法編＞ 第7〜12講"], got)
    stor = mod._sapuri_phases_for_store([{"name": "後期", "sapuri": []}, {"name": "新", "sapuri": []}],
                                        [{"name": "前期", "sapuri": want_sp[0]}, {"name": "x"}, {"name": "後期", "sapuri": want_sp[1]}], False)
    check("フェーズ数が変わったときは同じ名前のフェーズの範囲を残す・無ければ空",
          stor[0]["sapuri"] == want_sp[1] and stor[1]["sapuri"] == [], stor)

    # (c) 下書き (curriculum_draft) は読むときに今の判定でそろえる
    draft = {"target_university": "テスト大学", "phases": [phase("基礎期", sd, ed, materials=["ポラリス1"],
             sapuri=[{"course_code": "KZA02000", "from_seq": 1, "to_seq": 3}], sapuri_lectures=["架空の講座名"])]}
    for sid in (sid_ok, sid_ai):
        r = client.put("/api/student-state/curriculum_draft", json={"payload": draft}, headers=tok(sid))
        check(f"下書きを保存できる (生徒 {sid})", r.status_code == 200, r.text)
    dget = lambda sid: (client.get("/api/student-state/curriculum_draft", headers=tok(sid)).json().get("payload") or {}).get("phases") or [{}]
    check("下書き: 対象生徒にはカタログから作り直した範囲", dget(sid_ok)[0].get("sapuri_lectures") == ["高3 ハイレベル英語＜文法編＞ 第1〜3講"],
          dget(sid_ok)[0])
    check("下書き: 対象外の生徒には出さない", dget(sid_ai)[0].get("sapuri") == [] and dget(sid_ai)[0].get("sapuri_lectures") == [],
          dget(sid_ai)[0])
    switch(False)
    try:
        check("下書き: OFF の間は対象生徒にも出さない", dget(sid_ok)[0].get("sapuri_lectures") == [], dget(sid_ok)[0])
    finally:
        switch(True)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT payload FROM student_json_state WHERE student_id = ? AND kind = 'curriculum_draft'", (sid_ok,))
    stored_draft = json.loads(c.fetchone()["payload"])
    conn.close()
    check("下書き: 保存した中身は書き換えない (読むときだけ)", stored_draft["phases"][0].get("sapuri") == draft["phases"][0]["sapuri"],
          stored_draft["phases"][0])

    # (d) 「学習計画に展開」で作られたスタサプの計画は、対象外の生徒には出さない (行は消さない)
    conn = mod.db(); c = conn.cursor()
    for sid in (sid_ai, sid_ok):
        c.execute("INSERT INTO study_plans (student_id, title, subject, material, start_date, end_date, target_minutes, color, note) "
                  "VALUES (?,?,?,?,?,?,?,?,?)", (sid, "[基礎期] 📺 高3 架空レベル英文法", "英語", "高3 架空レベル英文法", sd, ed, 60,
                                                 "#000000", "カリキュラム自動展開 / 出典: スタサプ / 登場フェーズ: 基礎期"))
    conn.commit(); conn.close()
    plans_of = lambda sid: [x["material"] for x in client.get("/api/study-plans/me", headers=tok(sid)).json().get("plans", [])]
    check("対象外: スタサプの計画は出さない・他の計画は出る",
          "高3 架空レベル英文法" not in plans_of(sid_ai) and "青チャート" in plans_of(sid_ai), plans_of(sid_ai))
    check("対象生徒: スタサプの計画は出る", "高3 架空レベル英文法" in plans_of(sid_ok), plans_of(sid_ok))
    switch(False)
    try:
        check("OFF の間は対象生徒にもスタサプの計画を出さない", "高3 架空レベル英文法" not in plans_of(sid_ok)
              and "ポラリス1" in plans_of(sid_ok), plans_of(sid_ok))
    finally:
        switch(True)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) AS n FROM study_plans WHERE note LIKE '%出典: スタサプ%' AND student_id = ?", (sid_ai,))
    n_hidden = c.fetchone()["n"]
    conn.close()
    check("隠すだけで行は消さない", n_hidden == 1, n_hidden)

    # (e) /api/sapuri-lectures は講数表の版を返す (端末の控えを作り直す目安)
    d = client.get("/api/sapuri-lectures?limit=200").json()
    check("/api/sapuri-lectures に version (カタログの版)", isinstance(d.get("version"), str) and len(d["version"]) == 12
          and d["version"] == mod.SAPURI_CATALOG_VERSION, d.get("version"))

    print()
    if FAILURES:
        print(f"❌ FAIL: {len(FAILURES)} 件")
        for f in FAILURES:
            print(f"   - {f}")
        return 1
    print("✅ PASS: スタサプ 段階 A")
    return 0


if __name__ == "__main__":
    sys.exit(main())
