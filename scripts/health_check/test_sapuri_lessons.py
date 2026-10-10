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
  20-23. 段階 B レビュー修正: タグの無い弱点は学年帯の外・別系統の講座に移らない (AI 弱点プリントの実ルート) /
      講データの無い講座を選んだら講データのある同じ科目の講座で Tier 1/2 / 「（第b講まで）」は講番号が続くときだけ /
      停止スイッチは読めなければ閉じる側 / 止めた科目の保存済み週次プリントは読むときに外す
  26. 見た回のチェック (2026-10-10): POST /api/student/class/sapuri/watched・GET progress (認証・対象・AIなし/ライトで 200・
      入力の検査・冪等・他人の行・次の回へ・見終わり・取り消し・週次のメール/LINE・カリキュラムと計画の x/y・統合で早い方の日時・
      削除と孤児の掃除・CEO の status/progress/preview・見た回の読み取りは画面ごとに 1 回)
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
import re
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
    print("📺 スタサプ 段階 A・B 回帰テスト\n")
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
        lec = j.get("sapuri_lectures")
        if sid == sid_ai:
            check(f"対象外 (生徒 {sid}): 200 で sapuri_lectures / sapuri_lessons は [] (AI が書いても使わない)",
                  r.status_code == 200 and lec == [] and j.get("sapuri_lessons") == [], r.text)
        else:
            # 段階 B: 対象生徒はサーバの照合結果だけ (講データの取込前なので講座だけ = Tier 3)。AI が書いた名前は使わない
            check(f"対象生徒 (生徒 {sid}): サーバ照合の講座だけ (AI の名前は使わない・取込前は講座だけ)",
                  r.status_code == 200 and isinstance(lec, list) and len(lec) == 1
                  and lec[0].get("title") == "📺 スタサプ：高3 ハイレベル英語＜文法編＞" and "AI が書いた" not in r.text
                  and (j.get("sapuri_lessons") or [{}])[0].get("matched_by") == "course", r.text)
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
    check("偏差値: その科目の模試が無ければ既定 60 (他の科目・全科目の平均は使わない)", mod._sapuri_dev_for(c, sid_ok, "kobun") == 60.0)
    check("偏差値: 模試が無ければ 60", mod._sapuri_dev_for(c, sid_two, "math") == 60.0)
    check("偏差値の根拠: 「数学の模試 61」", mod._sapuri_dev_basis(c, sid_ok, "math") == (61.0, "数学の模試 61"),
          mod._sapuri_dev_basis(c, sid_ok, "math"))
    check("偏差値の根拠: 「古文の模試なし → 既定 60」", mod._sapuri_dev_basis(c, sid_ok, "kobun") == (60.0, "古文の模試なし → 既定 60"),
          mod._sapuri_dev_basis(c, sid_ok, "kobun"))
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

    # ======================================================================
    # 段階 B (講データ・照合・表示)。講の題名はすべて架空 (「テスト講義A1」等)。
    # ======================================================================
    print("\n[13] 取込 API (管理者だけ・cron の合言葉は拒否・表が無いと 503・講数の検査・dry_run・冪等・他講座を止めない)")
    mod._RATE_LIMIT_STORE.clear()
    mod._SAPURI_ELIGIBLE_CACHE.clear()

    def lessons_for(code, prefix, tags=None):
        co = mod.SAPURI_COURSE_BY_CODE[code]
        out = []
        for n in range(co["first"], co["last"] + 1):
            out.append({"seq": n, "title": f"{prefix}{n}", "tags": (tags or {}).get(n, [])})
        return out

    EG = "eng_grammar"
    kza_tags = {n: [{"subject_key": EG, "tag": "時制"}] for n in (1, 2, 3, 4, 7, 8)}   # 粗いタグ (6 講) → Tier 2 にしない
    kza_tags[5] = [{"subject_key": EG, "tag": "関係詞"}]
    kza_tags[6] = [{"subject_key": EG, "tag": "関係詞"}]
    kza_tags[10] = [{"subject_key": EG, "tag": "架空タグ"}, {"subject_key": "nope", "tag": "時制"}]   # 語彙外 → 捨てて報告
    kza_body = {"course_code": "KZA02000", "source": "test", "lessons": lessons_for("KZA02000", "テスト講義A", kza_tags),
                "topic_lessons": [{"subject_key": EG, "topic_norm": "仮定法(I wish + 仮定法過去)", "seqs": [9]},
                                  {"subject_key": EG, "topic_norm": "比較(倍数表現)", "seqs": [11, 12, 13, 14]},   # 4 講 → 捨てる
                                  {"subject_key": EG, "topic_norm": "比較(最上級)", "seqs": [99]}]}               # 範囲外 → 捨てる
    IMP = "/api/admin/sapuri/lessons/import"
    r = client.post(IMP, json=dict(kza_body, dry_run=True))
    check("取込: 未認証は 401", r.status_code == 401, r.status_code)
    r = client.post(IMP, json=dict(kza_body, dry_run=True), headers=tok(sid_ok))
    check("取込: 生徒のトークンは 401", r.status_code == 401, r.status_code)
    orig_cron = mod.CRON_SECRET
    mod.CRON_SECRET = "cron-test-secret"
    try:
        r = client.post(IMP, json=dict(kza_body, dry_run=True), headers={"X-Cron-Secret": "cron-test-secret"})
        check("取込: X-Cron-Secret は受け付けない (401・GitHub Actions から叩く経路を作らない)", r.status_code == 401, r.status_code)
    finally:
        mod.CRON_SECRET = orig_cron
    orig_ready = mod._sapuri_tables_ready
    mod._sapuri_tables_ready = lambda: False
    try:
        r = client.post(IMP, json={"dry_run": True}, headers=adm)
        check("取込: 表が無い (DDL 未反映) なら 503", r.status_code == 503, r.status_code)
        rr = mod._sapuri_recommend(sid_ok, [{"subject_code": "english", "topic": "関係詞"}])
        check("表が無いときの照合は講座だけ (落ちない)", rr and rr[0] and rr[0]["matched_by"] == "course" and rr[0]["lessons"] == [], rr)
    finally:
        mod._sapuri_tables_ready = orig_ready
    r = client.post(IMP, json={"dry_run": True}, headers=adm)
    check("取込: 空の dry_run は版の確認 (match=lesson_key)", r.status_code == 200 and r.json().get("match") == "lesson_key"
          and r.json().get("probe") is True, r.text)

    def n_rows(sql, args=()):
        conn = mod.db(); c = conn.cursor()
        c.execute(sql, args)
        v = c.fetchone()[0]
        conn.close()
        return v

    r = client.post(IMP, json=dict(kza_body, dry_run=True), headers=adm)
    j = r.json() if r.status_code == 200 else {}
    check("dry_run: 講数・タグ・topic の件数と見本 (先頭 2 講と最終講)", r.status_code == 200 and j.get("lessons") == 24
          and j.get("tags") == 8 and j.get("topic_lessons") == 1 and j.get("dry_run") is True
          and [x["seq"] for x in j.get("sample", [])] == [1, 2, 24], r.text)
    check("dry_run: 語彙外のタグと範囲外・4 講以上の topic は捨てて報告",
          len(j.get("dropped", {}).get("tags", [])) == 2 and len(j.get("dropped", {}).get("topics", [])) == 2, j.get("dropped"))
    check("dry_run は書かない", n_rows("SELECT COUNT(*) FROM sapuri_lessons") == 0)

    bad = dict(kza_body, lessons=kza_body["lessons"][:-1])
    r = client.post(IMP, json=bad, headers=adm)
    check("講数が公式 (last-first+1) と違う講座は丸ごと拒否 (400)", r.status_code == 400 and "講数" in r.text, r.text)
    r = client.post(IMP, json=dict(kza_body, course_code="KZ240000", lessons=lessons_for("KZ240000", "テスト講義S")), headers=adm)
    check("has_lessons=False の講座 (講数が公式と合わない) は拒否", r.status_code == 400, r.status_code)
    r = client.post(IMP, json=dict(kza_body, course_code="ZZ999"), headers=adm)
    check("カタログに無い講座は拒否", r.status_code == 400, r.status_code)
    bl = [dict(x) for x in kza_body["lessons"]]
    bl[3]["title"] = "テスト講義 講師の紹介"
    r = client.post(IMP, json=dict(kza_body, lessons=bl), headers=adm)
    check("題名に「講師」→ 拒否", r.status_code == 400 and "講師" in r.text, r.text)
    bl[3]["title"] = "テスト<b>講義</b>"
    r = client.post(IMP, json=dict(kza_body, lessons=bl), headers=adm)
    check("題名に HTML → 拒否", r.status_code == 400, r.status_code)
    bl[3]["title"] = "テ" * 81
    r = client.post(IMP, json=dict(kza_body, lessons=bl), headers=adm)
    check("題名が 80 字超 → 拒否", r.status_code == 400, r.status_code)
    bl = [dict(x) for x in kza_body["lessons"]]
    bl[1]["seq"] = 1
    r = client.post(IMP, json=dict(kza_body, lessons=bl), headers=adm)
    check("seq の重複 → 拒否", r.status_code == 400, r.status_code)
    check("拒否された取込は何も書かない", n_rows("SELECT COUNT(*) FROM sapuri_lessons") == 0)

    r = client.post(IMP, json=kza_body, headers=adm)
    check("本番の取込 (KZA02000)", r.status_code == 200 and r.json().get("ok") is True and r.json().get("lessons") == 24, r.text)
    check("取込の応答に題名は見本だけ", r.status_code == 200 and "テスト講義A7" not in r.text, r.text[:200])
    # 日本史 (通史 KZ277000) と文化史 (KZ121000) — Tier 1 の対応つき
    nh_body = {"course_code": "KZ277000", "source": "test", "lessons": lessons_for("KZ277000", "テスト講義N", {
        n: [{"subject_key": "nihonshi", "tag": "中世"}] for n in range(8, 16)}),
        "topic_lessons": [{"subject_key": "nihonshi", "topic_norm": "中世(元寇)", "seqs": [12]}]}
    r = client.post(IMP, json=nh_body, headers=adm)
    check("本番の取込 (KZ277000)", r.status_code == 200 and r.json().get("lessons") == 28, r.text)
    bk_body = {"course_code": "KZ121000", "source": "test", "lessons": lessons_for("KZ121000", "テスト講義B"),
               "topic_lessons": [{"subject_key": "nihonshi", "topic_norm": "近世(元禄文化)", "seqs": [5]}]}
    r = client.post(IMP, json=bk_body, headers=adm)
    check("本番の取込 (KZ121000 文化史・補講は取り込まない = 12 講)", r.status_code == 200 and r.json().get("lessons") == 12, r.text)
    check("他講座を止めない (KZA02000 の 24 講は有効のまま)",
          n_rows("SELECT COUNT(*) FROM sapuri_lessons WHERE course_code='KZA02000' AND active=1") == 24)
    before = (n_rows("SELECT COUNT(*) FROM sapuri_lessons"), n_rows("SELECT COUNT(*) FROM sapuri_lesson_tags"),
              n_rows("SELECT COUNT(*) FROM sapuri_topic_lessons"))
    r = client.post(IMP, json=kza_body, headers=adm)
    after = (n_rows("SELECT COUNT(*) FROM sapuri_lessons"), n_rows("SELECT COUNT(*) FROM sapuri_lesson_tags"),
             n_rows("SELECT COUNT(*) FROM sapuri_topic_lessons"))
    check("冪等 (同じファイルをもう一度入れても行数が同じ)", r.status_code == 200 and before == after, (before, after))
    kza2 = json.loads(json.dumps(kza_body))
    kza2["lessons"][6]["title"] = "テスト講義A7改"
    r = client.post(IMP, json=kza2, headers=adm)
    check("題名の修正は上書き (lesson_key で upsert)",
          r.status_code == 200 and n_rows("SELECT COUNT(*) FROM sapuri_lessons WHERE lesson_key='KZA02000#7' AND title='テスト講義A7改'") == 1)
    r = client.post(IMP, json=kza_body, headers=adm)
    st = client.get("/api/student/sapuri/status", headers=tok(sid_ok)).json()
    check("status API: 取込後は lessons_loaded=true (対象生徒)", st.get("lessons_loaded") is True, st)
    st = client.get("/api/student/sapuri/status", headers=tok(sid_ai)).json()
    check("status API: 対象外は lessons_loaded=false", st.get("lessons_loaded") is False, st)

    print("\n[14] 照合 (parse・part_key・講座選択・Tier 1/2/3・止めた講は出さない)")
    R = mod._sapuri_recommend
    conn = mod.db(); c = conn.cursor()
    def eq_row(part):
        c.execute("INSERT INTO exam_questions (exam_id, part_key, question_data) VALUES (?, ?, ?) RETURNING id",
                  ("daigaku", part, json.dumps({"questions": []})))
        return c.fetchone()[0]
    q_nh, q_se, q_ko = eq_row("nihonshi"), eq_row("sekaishi"), eq_row("kouminka")
    def qa(sid, topic, qid, source="practice"):
        c.execute("INSERT INTO question_attempts (student_id, source, exam_question_id, subject, topic, is_correct) "
                  "VALUES (?, ?, ?, 'social', ?, 0)", (sid, source, qid, topic))
    qa(sid_ok, "中世(元寇)", q_nh)
    qa(sid_ok, "中世(元寇)", q_se, source="grammar_drill")   # grammar_drill の id は grammar_questions を指す → 使わない
    qa(sid_ok, "近世(鎖国)", q_nh)
    qa(sid_ok, "近世(鎖国)", q_se)                           # 2 科目にまたがる → 推測しない
    qa(sid_ok, "現代(冷戦)", q_ko)                           # 未知の part_key (kouminka) → 推測しない
    qa(sid_ok, "近世(元禄文化)", q_nh)
    conn.commit(); conn.close()
    rr = R(sid_ok, [{"subject_code": "social", "topic": "中世(元寇)"}, {"subject_code": "social", "topic": "近世(鎖国)"},
                    {"subject_code": "social", "topic": "現代(冷戦)"}, {"subject_code": "social", "topic": "近世(元禄文化)"}])
    check("part_key で日本史に確定 (grammar_drill の行は使わない) → Tier 1", rr[0] and rr[0]["subject_key"] == "nihonshi"
          and rr[0]["course_code"] == "KZ277000" and rr[0]["matched_by"] == "topic" and rr[0]["lessons"][0]["seq"] == 12, rr[0])
    check("part_key が 2 つ (日本史と世界史) なら推薦しない", rr[1] is None, rr[1])
    check("未知の part_key (kouminka) なら推薦しない", rr[2] is None, rr[2])
    check("通史に Tier 1 が無いときだけ文化史の Tier 1", rr[3] and rr[3]["course_code"] == "KZ121000"
          and rr[3]["matched_by"] == "topic" and rr[3]["lessons"][0]["seq"] == 5, rr[3])
    rr = R(sid_ok, [{"subject_code": "social", "topic": "日本史 中世(承久の乱)"}])
    check("日本史の接頭辞があれば part_key なしで決まる・粗い時代タグ (8 講) は講座だけ",
          rr[0] and rr[0]["course_code"] == "KZ277000" and rr[0]["matched_by"] == "course" and rr[0]["lessons"] == [], rr[0])
    rr = R(sid_ok, [{"subject_code": "english", "topic": "英文法 関係代名詞(非制限用法)"},
                    {"subject_code": "english", "topic": "時制(現在完了)"},
                    {"subject_code": "english", "topic": "仮定法（I wish + 仮定法過去）"},
                    {"subject_code": "english", "topic": "長文読解"},
                    {"subject_code": "eiken", "topic": "関係詞"},
                    {"subject_code": "chugaku", "topic": "英文法 関係詞"},
                    {"subject_code": "japanese", "topic": "古文"}])
    check("Tier 2: 具体的なタグ (2 講) → tag・seq 順", rr[0] and rr[0]["matched_by"] == "tag"
          and [x["seq"] for x in rr[0]["lessons"]] == [5, 6] and rr[0]["course_code"] == "KZA02000", rr[0])
    check("label は「📺 スタサプ：講座名 第a講「題名」（第b講まで）」", rr[0] and rr[0]["label"] ==
          "📺 スタサプ：高3 ハイレベル英語＜文法編＞ 第5講「テスト講義A5」（第6講まで）", rr[0] and rr[0]["label"])
    check("Tier 2 は粗いタグ (5 講以上) なら講座だけ (course)", rr[1] and rr[1]["matched_by"] == "course" and rr[1]["lessons"] == []
          and rr[1]["label"] == "📺 スタサプ：高3 ハイレベル英語＜文法編＞", rr[1])
    check("Tier 1: 全角かっこの topic も NFKC で当たる", rr[2] and rr[2]["matched_by"] == "topic"
          and rr[2]["lessons"][0]["seq"] == 9, rr[2])
    check("english の語彙外 (長文) は推薦しない", rr[3] is None, rr[3])
    check("英検・中学の弱点には出さない", rr[4] is None and rr[5] is None, rr[4:6])
    check("裸の「古文」は古文の講座だけ (Tier 3)", rr[6] and rr[6]["subject_key"] == "kobun" and rr[6]["course_code"] == "KZ016000"
          and rr[6]["matched_by"] == "course", rr[6])
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE sapuri_lessons SET active = 0 WHERE lesson_key = 'KZA02000#9'")
    c.execute("UPDATE sapuri_lessons SET active = 0 WHERE lesson_key = 'KZA02000#5'")
    conn.commit(); conn.close()
    rr = R(sid_ok, [{"subject_code": "english", "topic": "仮定法(I wish + 仮定法過去)"}, {"subject_code": "english", "topic": "関係詞"}])
    check("止めた講 (active=0) は Tier 1 に出さない", rr[0] and rr[0]["matched_by"] == "course", rr[0])
    check("止めた講 (active=0) は Tier 2 に出さない", rr[1] and [x["seq"] for x in rr[1]["lessons"]] == [6], rr[1])
    r = client.post(IMP, json=kza_body, headers=adm)   # 取り込み直すと戻る
    rr = R(sid_ok, [{"subject_code": "english", "topic": "関係詞"}])
    check("取り込み直すと有効に戻る", rr[0] and [x["seq"] for x in rr[0]["lessons"]] == [5, 6], rr[0])

    # 講座選択 (学年帯・偏差値・全学年)
    PC, CA = mod._sapuri_pick_course, mod._sapuri_candidates
    pick = lambda sk, tags, band, dev: (PC(CA(sk, tags, mod.SAPURI_COVERS), band, dev) or {}).get("code")
    check("英文法 高3・偏差値 61 → ハイ (範囲の中央が近い)", pick(EG, ["関係詞"], "高3", 61) == "KZA02000")
    check("英文法 高3・偏差値 72 → トップ", pick(EG, ["関係詞"], "高3", 72) == "KZA01000")
    check("英文法 高3・偏差値 50 → スタンダード", pick(EG, ["関係詞"], "高3", 50) == "KZA03000")
    check("英文法 高1・2 は高1・2 の講座 (高3 に移らない)", pick(EG, ["関係詞"], "高1・2", 61) == "KZ375000")
    check("英文法 高1・2・偏差値 40 → ベーシック", pick(EG, ["関係詞"], "高1・2", 40) == "EKZB310000")
    check("どの範囲にも入らない偏差値は最も近い講座 (30 → ベーシック)", pick(EG, ["関係詞"], "高1・2", 30) == "EKZB310000")
    check("日本史 高1・2・偏差値 60 → 全学年の講座 (高1・2 にも属する)", pick("nihonshi", ["中世"], "高1・2", 60) == "KZ277000")
    check("日本史 高3・偏差値 70 → トップ&ハイの通史 (文化史は候補にしない)", pick("nihonshi", ["中世"], "高3", 70) == "KZ373000")
    check("数学 二次関数 高3 → 数学IAIIB+C の講座", pick("math", ["二次関数"], "高3", 61) in ("MKZA10000_1", "MKZ118000_1", "MKZ371000"))
    check("数学 二次関数 高1・2 → 高1・2 の数学I の講座", pick("math", ["二次関数"], "高1・2", 61) == "X-h12-high-math1")
    check("数学 極限 高3 → 数学III+C の講座", pick("math", ["極限"], "高3", 61) == "MKZ135000")
    check("化学基礎 → 化学基礎の講座 (高3 化学にしない)", pick("chemistry_basic", ["物質量"], "高3", 61) == "KZ282000")
    check("物理 原子 高3 偏差値 70 → 原子編 (トップ&ハイの本編は原子を扱わない)", pick("physics", ["原子"], "高3", 70) == "KZ123000")
    check("物理 原子 高3 偏差値 55 → スタンダード (全範囲の講座)", pick("physics", ["原子"], "高3", 55) == "KZ191000")
    check("物理 力学 高3 偏差値 70 → トップ&ハイの本編", pick("physics", ["力学"], "高3", 70) == "KZA17000")
    check("史料・テーマ史 (KZ493000) は照合の母集団に無い",
          "KZ493000" not in mod.SAPURI_COVERS and "KZ493000" not in mod.SAPURI_COVERS_TIER1_ONLY)

    print("\n[15] weakness-top3 の sapuri (対象生徒だけ・表示規則)")
    conn = mod.db(); c = conn.cursor()
    def weak(sid, subj, topic, acc, reason):
        c.execute("INSERT INTO student_weakness (student_id, subject, topic, question_count, avg_confidence_score, last_seen_at, "
                  "reason_counts, qa_accuracy, qa_attempts) VALUES (?, ?, ?, 5, 0.5, ?, ?, ?, 3)",
                  (sid, subj, topic, datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   json.dumps({reason: 3}), acc))
    for sid in (sid_ok, sid_ai):
        weak(sid, "english", "関係代名詞(非制限用法)", 0.10, "understanding")   # tag → #5 (〜#6)
        weak(sid, "english", "関係詞(whose)", 0.20, "understanding")            # 同じ #5 → 2 回目は出さない
        weak(sid, "english", "仮定法(I wish + 仮定法過去)", 0.30, "careless")   # Tier 1 だが主因がうっかり → 出さない
        weak(sid, "social", "中世(元寇)", 0.40, "understanding")               # part_key → Tier 1 #12
        weak(sid, "english", "時制(現在完了)", 0.50, "understanding")           # 粗いタグ → 講座だけ → 出さない
    conn.commit(); conn.close()
    r = client.get(f"/api/student/weakness-top3?student_id={sid_ok}&limit=5", headers=tok(sid_ok))
    j = r.json() if r.status_code == 200 else {}
    ws = j.get("weaknesses") or []
    sp = [w.get("sapuri") for w in ws]
    check("対象生徒: 200・sapuri_eligible=true・全項目に sapuri キー", r.status_code == 200 and j.get("sapuri_eligible") is True
          and len(ws) == 5 and all("sapuri" in w for w in ws), r.text[:300])
    check("1 位: タグの講 (最初の 1 講 + 範囲)", sp and sp[0] and sp[0]["matched_by"] == "tag" and len(sp[0]["lessons"]) == 1
          and sp[0]["lessons"][0]["seq"] == 5 and sp[0]["to_seq"] == 6 and "テスト講義A5" in sp[0]["label"], sp[:1])
    check("2 位: 同じ講は 2 回出さない", len(sp) > 1 and sp[1] is None, sp[1:2])
    check("3 位: 主因がうっかりの弱点には出さない", len(sp) > 2 and sp[2] is None, sp[2:3])
    check("4 位: 社会の時代タグは part_key で日本史 → Tier 1", len(sp) > 3 and sp[3] and sp[3]["course_code"] == "KZ277000"
          and sp[3]["lessons"][0]["seq"] == 12, sp[3:4])
    check("5 位: 講座だけ (Tier 3) は TOP3 に出さない", len(sp) > 4 and sp[4] is None, sp[4:5])
    r = client.get(f"/api/student/weakness-top3?student_id={sid_ai}&limit=5", headers=tok(sid_ai))
    j = r.json() if r.status_code == 200 else {}
    check("対象外: sapuri キーが無い・題名も出ない・sapuri_eligible=false", r.status_code == 200
          and all("sapuri" not in w for w in j.get("weaknesses") or [{}]) and "テスト講義" not in r.text
          and j.get("sapuri_eligible") is False, r.text[:300])
    r = client.get(f"/api/student/weakness-top3?student_id={sid_ai}&limit=5", headers=adm)
    check("管理者が対象外の生徒を引いても対象外の判定 (呼んだ人でなく生徒の行で判定)", r.status_code == 200
          and all("sapuri" not in w for w in r.json().get("weaknesses") or [{}]), r.text[:200])
    r = client.get(f"/api/student/weakness-top3?student_id={sid_ok}&limit=5&pool=chugaku", headers=tok(sid_ok))
    check("中学プールでは付けない", r.status_code == 200 and "テスト講義" not in r.text, r.text[:200])
    switch(False)
    try:
        r = client.get(f"/api/student/weakness-top3?student_id={sid_ok}&limit=5", headers=tok(sid_ok))
        check("停止スイッチ OFF の間は対象生徒にも出さない", r.status_code == 200 and "テスト講義" not in r.text
              and all("sapuri" not in w for w in r.json().get("weaknesses") or [{}]), r.text[:200])
    finally:
        switch(True)
    # 照合が落ちても TOP3 は壊れない (自分の接続・例外は握る)
    orig_rec = mod._sapuri_recommend
    mod._sapuri_recommend = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        r = client.get(f"/api/student/weakness-top3?student_id={sid_ok}&limit=5", headers=tok(sid_ok))
        check("照合が例外でも TOP3 は 200 (sapuri だけ欠ける)", r.status_code == 200 and len(r.json().get("weaknesses") or []) == 5, r.text[:200])
    finally:
        mod._sapuri_recommend = orig_rec
    src = open(MAIN_PY, encoding="utf-8").read()
    fn = src[src.index("def student_weakness_top3("):src.index("@app.get(\"/api/student/weakness-progress\")")]
    check("TOP3 の照合は共有カーソルを渡さない (_sapuri_attach_top3 は student_id だけ)",
          "_sapuri_attach_top3(student_id, weaknesses, pool)" in fn and "_sapuri_recommend(c" not in fn)

    print("\n[16] 通塾生アプリ GET /api/student/class/sapuri")
    r = client.get("/api/student/class/sapuri")
    check("未ログインは 401", r.status_code == 401, r.status_code)
    r = client.get("/api/student/class/sapuri", headers=tok(sid_ok))
    j = r.json() if r.status_code == 200 else {}
    items = j.get("items") or []
    check("対象生徒: 最大 3 行 (タグの講・Tier 1)・うっかり/講座だけ/重複は出さない", r.status_code == 200 and len(items) == 2
          and [(x["course_code"], x["lessons"][0]["seq"]) for x in items] == [("KZA02000", 5), ("KZ277000", 12)], r.text[:400])
    r = client.get("/api/student/class/sapuri", headers=tok(sid_ai))
    check("対象外: items は空 (カードごと出さない)", r.status_code == 200 and r.json().get("items") == [], r.text)
    sid_noai = make_student(mod, "AIなし枠 H", "sapuri-h@example.org", labels=LABELS3)
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE students SET ai_disabled = 1 WHERE id = ?", (sid_noai,))
    conn.commit(); conn.close()
    mod._AI_DISABLED_CACHE.clear()
    r = client.get("/api/student/class/sapuri", headers=tok(sid_noai))
    check("AIなし枠 (塾生アプリのみ) の対象生徒でも 200 (prefix /api/student/class/ は許可済み)", r.status_code == 200
          and r.json().get("items") == [], r.text)
    r = client.get(f"/api/student/weakness-top3?student_id={sid_noai}", headers=tok(sid_noai))
    check("(参考) AIなし枠は weakness-top3 には入れない (許可集合は変えていない)", r.status_code == 403, r.status_code)

    print("\n[17] 週次弱点プリント (subject_topics に sapuri・メールは題名なし・LINE の sapuri_line・対象外は外す)")
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO exam_questions (exam_id, part_key, question_data) VALUES ('daigaku', 'r_long', ?)",
              (json.dumps({"questions": [{"q": "x"}]}),))
    c.execute("UPDATE students SET line_user_id = 'U-test-line' WHERE id = ?", (sid_ok,))
    conn.commit(); conn.close()
    mails, lines = [], []
    orig_mail, orig_line = mod._send_monitor_email, mod._do_line_push
    mod._send_monitor_email = lambda subj, body, to_email=None: (mails.append((to_email, body)) or {"sent": True})
    mod._do_line_push = lambda sid, tmpl, params: (lines.append((sid, tmpl, params)) or {"ok": True})
    try:
        res = mod._run_weekly_worksheet_generation()
    finally:
        mod._send_monitor_email, mod._do_line_push = orig_mail, orig_line
    check("週次プリントが作られる", res.get("worksheets_created", 0) >= 2, res)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT student_id, subject_topics FROM worksheet_archives WHERE student_id IN (?, ?)", (sid_ok, sid_ai))
    arch = {r["student_id"]: json.loads(r["subject_topics"]) for r in c.fetchall()}
    conn.close()
    st_ok, st_ai = arch.get(sid_ok) or [], arch.get(sid_ai) or []
    check("対象生徒: subject_topics の 1 位に sapuri (表示規則つき)", st_ok and (st_ok[0].get("sapuri") or {}).get("lessons", [{}])[0].get("seq") == 5
          and all("sapuri" not in x for x in st_ok[1:]), st_ok)
    check("対象外: subject_topics に sapuri が無い", st_ai and all("sapuri" not in x for x in st_ai), st_ai)
    m_ok = next((b for to, b in mails if to == "sapuri-a@example.org"), "")
    m_ai = next((b for to, b in mails if to == "sapuri-b@example.org"), "")
    check("メール: 「📺 今週見るスタサプ：講座名 第N講」(題名なし)", "📺 今週見るスタサプ：高3 ハイレベル英語＜文法編＞ 第5講" in m_ok
          and "テスト講義" not in m_ok, m_ok)
    check("メール: 対象外には 📺 の行が無い", m_ai and "スタサプ" not in m_ai, m_ai)
    lp = next((p for s_, t_, p in lines if s_ == sid_ok), {})
    check("LINE: sapuri_line に講座名と講番号 (題名なし)", lp.get("sapuri_line") == "📺 今週見るスタサプ：高3 ハイレベル英語＜文法編＞ 第5講", lp)
    txt = mod.LINE_TEMPLATES["weekly_worksheet"](lp)["text"]
    check("LINE テンプレ: sapuri_line を本文に入れる", "📺 今週見るスタサプ：" in txt and "テスト講義" not in txt, txt)
    txt0 = mod.LINE_TEMPLATES["weekly_worksheet"]({"name": "テスト", "subject_summary": "english", "question_count": 3, "url": "https://x"})
    check("LINE テンプレ: sapuri_line が無ければ従来の本文 (空行も足さない)", txt0["text"] ==
          "📅 今週の弱点プリントが届きました\n\nテストさんの苦手分野 (english) から\n計 3 問を準備しました。\n\nマイページから確認できます👇\nhttps://x/mypage.html?focus=worksheet",
          txt0["text"])
    h = mod._sapuri_mail_html([{"sapuri": {"course_name": "高3 トップ&ハイレベル日本史<通史>", "lessons": [{"seq": 3}]}}] * 3)
    check("メールの行は html.escape・最大 2 件", "&amp;" in h and "&lt;" in h and h.count("📺") == 2, h)
    r = client.get("/api/student/worksheet/this-week", headers=tok(sid_ok))
    check("this-week: 対象生徒には sapuri (題名つき)", r.status_code == 200
          and "テスト講義A5" in json.dumps(r.json().get("worksheet", {}).get("subject_topics"), ensure_ascii=False), r.text[:300])
    switch(False)
    try:
        r = client.get("/api/student/worksheet/this-week", headers=tok(sid_ok))
        check("this-week: いま対象外 (停止スイッチ OFF) なら sapuri を外す", r.status_code == 200 and "テスト講義" not in r.text
              and all("sapuri" not in x for x in r.json()["worksheet"]["subject_topics"]), r.text[:300])
        r = client.get("/api/student/worksheet/history", headers=tok(sid_ok))
        check("history: いま対象外なら sapuri を外す", r.status_code == 200 and "テスト講義" not in r.text, r.text[:300])
    finally:
        switch(True)
    r = client.get("/api/student/worksheet/history", headers=tok(sid_ok))
    check("history: 対象生徒には残る", r.status_code == 200 and "テスト講義A5" in r.text, r.text[:300])
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT subject_topics FROM worksheet_archives WHERE student_id = ?", (sid_ok,))
    check("隠すだけで保存した行は書き換えない", "テスト講義A5" in (c.fetchone()["subject_topics"] or ""))
    conn.close()
    src = open(MAIN_PY, encoding="utf-8").read()
    wfn = src[src.index("def _run_weekly_worksheet_generation("):src.index("@app.get(\"/api/student/worksheet/this-week\")")]
    check("週次プリントの関数内はヘルパーを 1 行で呼ぶだけ (共有カーソルを渡さない)",
          wfn.count("_sapuri_for_subject_topics(sid, sgrade, subject_topics)") == 1 and "_sapuri_recommend" not in wfn)

    print("\n[18] AI 弱点プリント (対象生徒だけサーバ照合・AI 出力のスタサプは使わない・理科/社会は 1 科目に決まるときだけ)")
    mod._RATE_LIMIT_STORE.clear()
    fake.reply = {"topic_used": "関係詞", "weak_point_analysis": "テスト",
                  "problems": [{"no": 1, "difficulty": "標準", "question": "Q", "answer": "A", "explanation": "E"}],
                  "sapuri_lectures": [{"title": "高3 テスト講義Z (AI が書いた名前)", "level": "ハイ", "reason": "x"}]}
    def ws(sid, subject, topic):
        r = client.post("/api/weak-points/generate-worksheet", json={"subject": subject, "topic": topic, "num_problems": 3},
                        headers=tok(sid))
        return r.status_code, (r.json() if r.status_code == 200 else {}), r.text
    code, j, t = ws(sid_ok, "英語", "関係詞")
    sl = j.get("sapuri_lessons") or []
    check("対象生徒: sapuri_lessons はサーバの照合 (タグの講)", code == 200 and len(sl) == 1 and sl[0]["matched_by"] == "tag"
          and [x["seq"] for x in sl[0]["lessons"]] == [5, 6], t[:300])
    check("互換の sapuri_lectures は [{title: label, level:'', reason:''}]・AI の名前は無い",
          j.get("sapuri_lectures") == [{"title": sl[0]["label"] if sl else None, "level": "", "reason": ""}] and "AI が書いた" not in t, t[:300])
    check("AI へのプロンプトに題名・スタサプを入れない", "テスト講義" not in fake.calls[-1]["user"] + fake.calls[-1]["system"]
          and "スタサプ" not in fake.calls[-1]["system"], fake.calls[-1])
    code, j, t = ws(sid_ok, "古文", "助動詞")
    check("古文 + 語彙外の入力 → 古文の講座だけ (Tier 3)", code == 200 and (j.get("sapuri_lessons") or [{}])[0].get("course_code") == "KZ016000"
          and j["sapuri_lessons"][0]["matched_by"] == "course", t[:300])
    code, j, t = ws(sid_ok, "理科", "力学")
    check("理科 + 力学 (物理だけの語) → 物理の講座", code == 200 and (j.get("sapuri_lessons") or [{}])[0].get("subject_key") == "physics", t[:300])
    code, j, t = ws(sid_ok, "社会", "近代")
    check("社会 + 近代 (日本史・世界史・倫理にある語) → 推薦しない", code == 200 and j.get("sapuri_lessons") == [] and j.get("sapuri_lectures") == [], t[:300])
    code, j, t = ws(sid_ok, "地学", "地震")
    check("地学 → 推薦しない", code == 200 and j.get("sapuri_lessons") == [], t[:300])
    code, j, t = ws(sid_ai, "英語", "関係詞")
    check("対象外: sapuri_lessons / sapuri_lectures は空", code == 200 and j.get("sapuri_lessons") == [] and j.get("sapuri_lectures") == []
          and "テスト講義" not in t, t[:300])

    print("\n[19] CEO: status / preview / coverage (管理者だけ・題名は preview だけ)")
    for path in ("/api/admin/sapuri/status", f"/api/admin/sapuri/preview?student_id={sid_ok}", "/api/admin/sapuri/coverage"):
        r = client.get(path, headers=tok(sid_ok))
        check(f"{path.split('?')[0]}: 生徒のトークンは 401", r.status_code == 401, r.status_code)
    r = client.get("/api/admin/sapuri/status", headers=adm)
    j = r.json() if r.status_code == 200 else {}
    byc = {x["code"]: x for x in j.get("courses", [])}
    stu = {x["id"]: x for x in j.get("students", [])}
    check("status: 停止スイッチ・設定の健全性・表の有無", r.status_code == 200 and j.get("enabled") is True and j.get("config_ok") is True
          and j.get("tables_ready") is True, r.text[:300])
    check("status: 講座ごとの取込講数・最終取込日時", byc.get("KZA02000", {}).get("lessons_active") == 24
          and byc["KZA02000"].get("last_imported_at") and byc["KZA02000"].get("used_for_match") is True
          and byc.get("KZ493000", {}).get("used_for_match") is False, byc.get("KZA02000"))
    check("status: 対象生徒の一覧 (理由つき・AIなし枠の数)", stu.get(sid_ok, {}).get("eligible") is True
          and stu.get(sid_ai, {}).get("reason") == "labels" and stu.get(sid_two, {}).get("reason") == "labels"
          and stu.get(sid_noai, {}).get("ai_disabled") is True and j.get("eligible_ai_disabled_count", 0) >= 1, list(stu.values())[:3])
    check("status: 題名を返さない", "テスト講義" not in r.text)
    r = client.get(f"/api/admin/sapuri/preview?student_id={sid_ok}", headers=adm)
    j = r.json() if r.status_code == 200 else {}
    check("preview: 生徒画面と同じ 📺 行 (TOP3・class.html・週次)", r.status_code == 200 and j.get("eligible") is True
          and [x["lessons"][0]["seq"] for x in j.get("top3", [])] == [5]
          and [x["lessons"][0]["seq"] for x in j.get("class_items", [])] == [5, 12]
          and j.get("weekly_lines") == ["📺 今週見るスタサプ：高3 ハイレベル英語＜文法編＞ 第5講"], r.text[:400])
    check("preview: 弱点ごとの matched_by", [w["matched_by"] for w in j.get("weaknesses", [])] == ["tag", "tag", "topic", "topic", "course"],
          [w.get("matched_by") for w in j.get("weaknesses", [])])
    # 2026-10-10 取込後の点検 (塾長「4つとも直して」): A 見え方の class_items は生徒の class.html と同じもの (科目つき)
    rc = client.get("/api/student/class/sapuri", headers=tok(sid_ok))
    check("preview: class_items は /api/student/class/sapuri の items と同じ (subject を含む)", rc.status_code == 200
          and j.get("class_items") == rc.json().get("items") and all(x.get("subject") for x in j.get("class_items") or [None]),
          (j.get("class_items"), rc.text[:300]))
    # B 出さない理由のコード (出す弱点は None)
    check("preview: 出さない理由 (同じ回・主因がうっかり・粗いタグ)", [w.get("why") for w in j.get("weaknesses", [])]
          == [None, "duplicate", "hidden_reason", None, "tag_too_broad"], [w.get("why") for w in j.get("weaknesses", [])])
    # C 講座のレベルの根拠
    check("preview: 講座のレベルの根拠 (英語の模試が無い → 既定 60)", (j.get("weaknesses") or [{}])[0].get("dev_basis")
          == "英語の模試なし → 既定 60", (j.get("weaknesses") or [{}])[0])
    check("preview: 推薦の dict に理由・根拠を混ぜない (生徒の応答の形は変えない)",
          all("why" not in (w.get("recommendation") or {}) and "dev_basis" not in (w.get("recommendation") or {})
              and "why" not in (w.get("shown") or {}) for w in j.get("weaknesses", [])))
    r = client.get(f"/api/admin/sapuri/preview?student_id={sid_ai}", headers=adm)
    check("preview: 対象外の生徒は何も出ない (理由つき)", r.status_code == 200 and r.json().get("eligible") is False
          and r.json().get("top3") == [] and r.json().get("reason") == "labels", r.text[:200])
    r = client.get("/api/admin/sapuri/coverage", headers=adm)
    j = r.json() if r.status_code == 200 else {}
    check("coverage: matched_by の内訳と推薦できなかった弱点の上位", r.status_code == 200 and j.get("matched_by", {}).get("tag", 0) >= 2
          and j["matched_by"].get("topic", 0) >= 2 and any(x.get("tag") == "時制" and x.get("matched_by") == "course"
                                                             for x in j.get("unmatched_top", [])), r.text[:400])
    check("coverage: 題名を返さない", "テスト講義" not in r.text)
    check("coverage: 出せなかった弱点に理由のコードと例 (3 つまで)", r.status_code == 200
          and any(x.get("tag") == "時制" and x.get("why") == "tag_too_broad" for x in j.get("unmatched_top", []))
          and all(isinstance(x.get("example_topics"), list) and 1 <= len(x["example_topics"]) <= 3 for x in j.get("unmatched_top", [])),
          j.get("unmatched_top"))

    # ======================================================================
    # 段階 B レビューの修正 (2026-10-10)
    # ======================================================================
    print("\n[20] タグの無い弱点は学年帯の外・別系統の講座に移らない (AI 弱点プリントの実ルート)")
    sid_n = make_student(mod, "スタサプ対象 N", "sapuri-n@example.org", labels=LABELS3)          # 高3・模試なし = 偏差値 60
    sid_n2 = make_student(mod, "スタサプ対象 N2", "sapuri-n2@example.org", labels=LABELS3, grade="高校2年")

    def ws_one(sid, subject, topic):
        mod._RATE_LIMIT_STORE.clear()
        code, j, t = ws(sid, subject, topic)
        return code, (j.get("sapuri_lessons") or []), t
    for subject, topic, why in (("数学", "三角関数の合成", "語彙に無い数学 (数学III+C に寄せない)"),
                                ("数学", "ベクトルの内積", "語彙に無い数学"),
                                ("化学", "中和滴定", "高3 に高1・2 のベーシック化学を出さない"),
                                ("化学", "化学平衡", "高3 に高1・2 のベーシック化学を出さない"),
                                ("現代文", "要約", "現代文を語句 (漢字・語彙) の講座に寄せない")):
        code, sl, t = ws_one(sid_n, subject, topic)
        check(f"タグなし {subject}「{topic}」→ 推薦しない ({why})", code == 200 and sl == [], t[:300])
    code, sl, t = ws_one(sid_n, "数学", "数学II 加法定理")
    co = mod.SAPURI_COURSE_BY_CODE.get((sl or [{}])[0].get("course_code")) or {}
    check("数学II の接頭辞 (タグなし) → 高3 の数学IAIIB+C の講座 (数学III+C にしない)", code == 200 and len(sl) == 1
          and co.get("field") == "IAIIB+C" and co.get("band") == "高3" and sl[0]["matched_by"] == "course", t[:300])
    code, sl, t = ws_one(sid_n, "数学", "数学III 区分求積法")
    co = mod.SAPURI_COURSE_BY_CODE.get((sl or [{}])[0].get("course_code")) or {}
    check("数学III の接頭辞 (タグなし) → 数学III+C の講座", code == 200 and len(sl) == 1 and co.get("field") == "III+C", t[:300])
    code, sl, t = ws_one(sid_n2, "化学", "中和滴定")
    check("高1・2 の化学 (タグなし) → 学年帯にある全範囲の講座 (高1・2)", code == 200 and len(sl) == 1
          and (mod.SAPURI_COURSE_BY_CODE.get(sl[0]["course_code"]) or {}).get("band") == "高1・2", t[:300])
    code, sl, t = ws_one(sid_n, "古文", "助動詞")
    check("古文 (タグなし) は学年帯に全範囲の講座があるので講座だけ (従来どおり)", code == 200 and len(sl) == 1
          and sl[0]["course_code"] == "KZ016000", t[:300])
    C3 = mod._sapuri_choose_course
    check("タグなしの数学 (接頭辞なし) は講座を選ばない", C3("math", [], "高3", 60) is None)
    check("タグありは従来どおり学年帯に無ければもう一方 (高1・2 の有機化学 → 学年帯の全範囲の講座)",
          (C3("chemistry", ["有機化学"], "高1・2", 60) or {}).get("band") == "高1・2")

    print("\n[21] 選んだ講座に講データが無ければ、講データのある同じ科目の講座で引く・範囲は講番号が続くときだけ")
    sk_body = {"course_code": "KZ372000", "source": "test", "lessons": lessons_for("KZ372000", "テスト講義W", {
        10: [{"subject_key": "sekaishi", "tag": "中世"}], 11: [{"subject_key": "sekaishi", "tag": "中世"}]}),
        "topic_lessons": [{"subject_key": "sekaishi", "topic_norm": "中世(イスラーム世界)", "seqs": [7]},
                          {"subject_key": "sekaishi", "topic_norm": "近世(大航海時代)", "seqs": [3, 15]},
                          {"subject_key": "sekaishi", "topic_norm": "近代(産業革命)", "seqs": [20, 21, 30]}]}
    r = client.post(IMP, json=sk_body, headers=adm)
    check("本番の取込 (KZ372000 世界史 通史)", r.status_code == 200 and r.json().get("ok") is True, r.text[:300])
    check("前提: 高3・偏差値 60 の世界史は講データの無いスタンダード (KZ240000) を選ぶ",
          (C3("sekaishi", ["中世"], "高3", 60) or {}).get("code") == "KZ240000"
          and mod.SAPURI_COURSE_BY_CODE["KZ240000"]["has_lessons"] is False)
    rr = R(sid_n, [{"subject_code": "social", "topic": "世界史 中世(イスラーム世界)"},
                   {"subject_code": "social", "topic": "世界史 中世(十字軍)"},
                   {"subject_code": "social", "topic": "世界史 古代(ローマ)"},
                   {"subject_code": "social", "topic": "世界史 近世(大航海時代)"},
                   {"subject_code": "social", "topic": "世界史 近代(産業革命)"}])
    check("Tier 1 は講データのある講座 (KZ372000) で引く", rr[0] and rr[0]["course_code"] == "KZ372000"
          and rr[0]["matched_by"] == "topic" and [x["seq"] for x in rr[0]["lessons"]] == [7], rr[0])
    check("Tier 2 も講データのある講座で引く (2 講)", rr[1] and rr[1]["course_code"] == "KZ372000"
          and rr[1]["matched_by"] == "tag" and [x["seq"] for x in rr[1]["lessons"]] == [10, 11] and rr[1]["to_seq"] == 11, rr[1])
    check("当たらなければ Tier 3 は選んだ講座 (講データ無しの印つき)", rr[2] and rr[2]["course_code"] == "KZ240000"
          and rr[2]["matched_by"] == "course" and rr[2]["course_has_lessons"] is False, rr[2])
    check("飛び飛び [3, 15] は「（第15講まで）」を付けない (label・to_seq)", rr[3] and rr[3]["to_seq"] is None
          and "まで" not in rr[3]["label"] and "第3講「テスト講義W3」" in rr[3]["label"], rr[3])
    check("[20, 21, 30] は続く所まで (第21講まで)", rr[4] and rr[4]["to_seq"] == 21 and rr[4]["label"].endswith("（第21講まで）"), rr[4])
    conn = mod.db(); c = conn.cursor()
    for tp in ("世界史 近世(大航海時代)", "世界史 近代(産業革命)", "世界史 中世(イスラーム世界)"):
        c.execute("INSERT INTO student_weakness (student_id, subject, topic, question_count, avg_confidence_score, last_seen_at, "
                  "reason_counts, qa_accuracy, qa_attempts) VALUES (?, 'social', ?, 5, 0.5, ?, ?, 0.1, 3)",
                  (sid_n, tp, datetime.datetime.now(datetime.timezone.utc).isoformat(), json.dumps({"understanding": 3})))
    conn.commit(); conn.close()
    r = client.get("/api/student/class/sapuri", headers=tok(sid_n))
    items = (r.json() if r.status_code == 200 else {}).get("items") or []
    byt = {x["topic"]: x for x in items}
    check("class.html: 高3・偏差値 60 の世界史の弱点にも回が出る (3 件)", r.status_code == 200 and len(items) == 3
          and all(x["course_code"] == "KZ372000" for x in items), r.text[:400])
    check("class.html: 飛び飛びの対応は to_seq=null (範囲を書かない)", (byt.get("世界史 近世(大航海時代)") or {}).get("to_seq", "x") is None,
          byt.get("世界史 近世(大航海時代)"))
    check("class.html: 続く範囲は to_seq=21", (byt.get("世界史 近代(産業革命)") or {}).get("to_seq") == 21, byt.get("世界史 近代(産業革命)"))
    r = client.get("/api/admin/sapuri/coverage", headers=adm)
    check("coverage: 講座だけの弱点に「講データ無し」の印 (no_lessons)", r.status_code == 200
          and all("no_lessons" in x for x in r.json().get("unmatched_top", [])), r.text[:300])

    print("\n[22] 停止スイッチは読めなければ閉じる側 (塾長が OFF にした後の一時的な DB の失敗で出し直さない)")
    class _Cur:
        def __init__(self, cur): self._c = cur
        def execute(self, sql, *a):
            if "kv_settings" in sql:
                raise RuntimeError("kv read failed (test)")
            return self._c.execute(sql, *a)
        def __getattr__(self, n): return getattr(self._c, n)
    class _Conn:
        def __init__(self, conn): self._k = conn
        def cursor(self): return _Cur(self._k.cursor())
        def __getattr__(self, n): return getattr(self._k, n)
    orig_db = mod.db
    switch(False)
    try:
        mod.db = lambda *a, **k: _Conn(orig_db(*a, **k))
        mod._SAPURI_SWITCH_CACHE.update({"until": 0.0})
        mod._SAPURI_ELIGIBLE_CACHE.clear()
        check("OFF の後に kv の読み取りが失敗しても OFF のまま (控え)", mod._sapuri_enabled() is False
              and mod._sapuri_eligible_by_id(sid_ok).get("eligible") is False)
        r = client.get("/api/student/class/sapuri", headers=tok(sid_ok))
        check("その間も生徒画面に出さない (class.html)", r.status_code == 200 and r.json().get("items") == [], r.text[:200])
        mod._SAPURI_SWITCH_CACHE.update({"until": 0.0, "known": False, "enabled": True})
        mod._SAPURI_ELIGIBLE_CACHE.clear()
        check("一度も読めていないプロセスで読み取りが失敗したら OFF", mod._sapuri_enabled() is False
              and mod._sapuri_eligible_by_id(sid_ok).get("eligible") is False)
        check("失敗は 30 秒覚えない (5 秒)", mod._SAPURI_SWITCH_CACHE["until"] - time.time() <= mod._SAPURI_SWITCH_FAIL_TTL + 0.5)
    finally:
        mod.db = orig_db
        switch(True)
    mod._SAPURI_SWITCH_CACHE.update({"until": 0.0})
    mod._SAPURI_ELIGIBLE_CACHE.clear()
    check("読めるようになれば ON に戻る", mod._sapuri_enabled() is True and mod._sapuri_eligible_by_id(sid_ok).get("eligible") is True)
    conn = mod.db(); c = conn.cursor()
    c.execute("DELETE FROM kv_settings WHERE key = 'sapuri_enabled'")
    conn.commit(); conn.close()
    mod._SAPURI_SWITCH_CACHE.update({"until": 0.0})
    check("行が無いのは既定の ON (読み取り失敗とは別)", mod._sapuri_enabled() is True)

    print("\n[23] 止めた科目 (SAPURI_SUBJECT_KEYS) の保存済み週次プリントは読むときに外す")
    mod._SAPURI_ELIGIBLE_CACHE.clear()
    r = client.get("/api/student/worksheet/this-week", headers=tok(sid_ok))
    check("前提: this-week に英文法の sapuri (題名つき)", r.status_code == 200 and "テスト講義A5" in r.text, r.text[:200])
    orig_keys = mod.SAPURI_SUBJECT_KEYS
    mod.SAPURI_SUBJECT_KEYS = tuple(k for k in orig_keys if k != "eng_grammar")
    try:
        r = client.get("/api/student/worksheet/this-week", headers=tok(sid_ok))
        check("this-week: 英文法を止めたら対象生徒でも外す", r.status_code == 200 and "テスト講義" not in r.text
              and all("sapuri" not in x for x in r.json()["worksheet"]["subject_topics"]), r.text[:300])
        r = client.get("/api/student/worksheet/history", headers=tok(sid_ok))
        check("history: 英文法を止めたら外す", r.status_code == 200 and "テスト講義" not in r.text, r.text[:300])
    finally:
        mod.SAPURI_SUBJECT_KEYS = orig_keys
    orig_cov = mod.SAPURI_COVERS
    mod.SAPURI_COVERS = {k: v for k, v in orig_cov.items() if k != "KZA02000"}
    try:
        r = client.get("/api/student/worksheet/this-week", headers=tok(sid_ok))
        check("this-week: 照合から外した講座の sapuri も外す", r.status_code == 200 and "テスト講義" not in r.text, r.text[:300])
    finally:
        mod.SAPURI_COVERS = orig_cov
    r = client.get("/api/student/worksheet/this-week", headers=tok(sid_ok))
    check("戻せばまた出る (保存した行は書き換えていない)", r.status_code == 200 and "テスト講義A5" in r.text, r.text[:200])

    print("\n[24] 取込後の点検の修正 (2026-10-10 塾長「4つとも直して」): 理由のコード・偏差値はその科目だけ・同じ学年帯の代わりの講座")
    mod._RATE_LIMIT_STORE.clear()
    mod._SAPURI_ELIGIBLE_CACHE.clear()
    # 理由のコード (照合)
    sid_r = make_student(mod, "スタサプ対象 R", "sapuri-r@example.org", labels=LABELS3)
    dets = []
    rr = R(sid_r, [{"subject_code": "english", "topic": "事実把握"},
                   {"subject_code": "chemistry", "topic": "化学"},
                   {"subject_code": "chemistry", "topic": "化学基礎"},
                   {"subject_code": "eiken", "topic": "関係詞"},
                   {"subject_code": "social", "topic": "近代(明治維新)"},
                   {"subject_code": "earth", "topic": "地震"},
                   {"subject_code": "japanese", "topic": "要旨把握"},
                   {"subject_code": "english", "topic": "時制(現在完了)"}], details=dets)
    whys = [d.get("reason") for d in dets]
    check("理由: 読解・設問タイプ / 科目名だけ / 講座だけ / 対象外 / 社会が決まらない / 対象外 / 国語が決まらない / 粗いタグ",
          whys == ["english_non_grammar", "subject_only", "course_only", "out_of_scope", "undetermined_social",
                   "out_of_scope", "undetermined_japanese", "tag_too_broad"], whys)
    check("理由のある項目の推薦は None か講座だけ (返り値の形は従来どおり)", rr[0] is None and rr[1] is None
          and rr[2] and rr[2]["matched_by"] == "course" and "reason" not in rr[2] and "why" not in rr[2], rr[:3])
    orig_keys = mod.SAPURI_SUBJECT_KEYS
    mod.SAPURI_SUBJECT_KEYS = tuple(k for k in orig_keys if k != "kobun")
    try:
        dets = []
        R(sid_r, [{"subject_code": "japanese", "topic": "古文 敬語"}], details=dets)
        check("理由: 止めている科目 (subject_stopped)", dets and dets[0].get("reason") == "subject_stopped", dets)
    finally:
        mod.SAPURI_SUBJECT_KEYS = orig_keys
    ceo_src = open(os.path.join(REPO, "ceo.html"), encoding="utf-8").read()
    js_keys = set(re.findall(r"^\s{6}([a-z_]+): '", ceo_src[ceo_src.index("var SP_WHY_JA = {"):ceo_src.index("function whyText(code)")], re.M))
    check("理由のコードは全部 ceo.html の SP_WHY_JA に文言がある (余りも無い)", js_keys == set(mod._SAPURI_WHY_CODES),
          (sorted(set(mod._SAPURI_WHY_CODES) - js_keys), sorted(js_keys - set(mod._SAPURI_WHY_CODES))))

    # C 偏差値はその科目の模試だけ (化学 50 だけの生徒の英文法はハイ・英語 55 ならスタンダード)
    sid_chem = make_student(mod, "スタサプ対象 S", "sapuri-s@example.org", labels=LABELS3)
    sid_eng55 = make_student(mod, "スタサプ対象 T", "sapuri-t@example.org", labels=LABELS3)
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO exam_results (student_id, exam_name, exam_date, subject, deviation) VALUES (?,?,?,?,?)",
              (sid_chem, "テスト模試", sd, "化学", 50.0))
    c.execute("INSERT INTO exam_results (student_id, exam_name, exam_date, subject, deviation) VALUES (?,?,?,?,?)",
              (sid_eng55, "テスト模試", sd, "英語", 55.0))
    c.execute("INSERT INTO exam_results (student_id, exam_name, exam_date, subject, deviation) VALUES (?,?,?,?,?)",
              (sid_eng55, "テスト模試", sd, "化学", 72.0))
    conn.commit(); conn.close()
    dets = []
    rr = R(sid_chem, [{"subject_code": "english", "topic": "関係詞"}], details=dets)
    check("化学 50 だけの生徒の英文法 → ハイ (KZA02000・既定 60)", rr and rr[0] and rr[0]["course_code"] == "KZA02000"
          and dets[0].get("dev") == 60.0 and dets[0].get("dev_basis") == "英語の模試なし → 既定 60", (rr, dets))
    dets = []
    # (KZA03000 は講データが無いので回は講データのある KZA02000 から引く。講座の選択は講の無い単元の Tier 3 で見る)
    rr = R(sid_eng55, [{"subject_code": "english", "topic": "仮定法(should)"}], details=dets)
    check("英語 55 の生徒の英文法 → スタンダード (KZA03000・化学 72 は使わない)", rr and rr[0] and rr[0]["course_code"] == "KZA03000"
          and dets[0].get("dev") == 55.0 and dets[0].get("dev_basis") == "英語の模試 55", (rr, dets))
    rr = R(sid_chem, [{"subject_code": "english", "topic": "仮定法(should)"}])
    check("同じ単元で化学 50 だけの生徒はハイ (KZA02000)", rr and rr[0] and rr[0]["course_code"] == "KZA02000", rr)

    # D 選んだ講座に講データがあるのにそのタグの講が無い → 同じ学年帯でそのタグの講がある講座 (偏差値の目安が近い順)
    EGT = lambda tag: [{"subject_key": EG, "tag": tag}]
    for code, tagmap in (("KZ375000", {n: EGT("関係詞") for n in (5, 6)}),                 # 高1・2 ハイ: 語法の講なし
                         ("EKZB320000", {n: EGT("比較") for n in (7, 8)}),                 # 高1・2 スタンダード: 語法の講なし
                         ("KZA35000", {1: EGT("語法"), 2: EGT("語法")}),                    # 高1・2 トップ: 語法 2 講
                         ("EKZB310000", {9: EGT("語法")})):                                 # ベーシック: 語法 1 講
        r = client.post(IMP, json={"course_code": code, "source": "test", "lessons": lessons_for(code, "テスト講義" + code[-4:], tagmap),
                                   "topic_lessons": []}, headers=adm)
        check(f"本番の取込 ({code})", r.status_code == 200 and r.json().get("ok") is True, r.text[:200])
    sid_k60 = make_student(mod, "スタサプ対象 U", "sapuri-u@example.org", labels=LABELS3, grade="高校2年")
    sid_k52 = make_student(mod, "スタサプ対象 V", "sapuri-v@example.org", labels=LABELS3, grade="高校2年")
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO exam_results (student_id, exam_name, exam_date, subject, deviation) VALUES (?,?,?,?,?)",
              (sid_k52, "テスト模試", sd, "英語", 52.0))
    conn.commit(); conn.close()
    check("前提: 高1・2・偏差値 60 の英文法は KZ375000 / 52 は EKZB320000",
          (C3(EG, ["語法"], "高1・2", 60) or {}).get("code") == "KZ375000" and (C3(EG, ["語法"], "高1・2", 52) or {}).get("code") == "EKZB320000")
    rr = R(sid_k60, [{"subject_code": "english", "topic": "語法・イディオム"}])
    check("偏差値 60: 語法の講が無い KZ375000 → 同じ学年帯の KZA35000 (中央 71.5 が 46.5 より近い) の Tier 2",
          rr and rr[0] and rr[0]["course_code"] == "KZA35000" and rr[0]["matched_by"] == "tag"
          and [x["seq"] for x in rr[0]["lessons"]] == [1, 2], rr)
    rr = R(sid_k52, [{"subject_code": "english", "topic": "語法・イディオム"}])
    check("偏差値 52: 語法の講が無い EKZB320000 → 中央が近いベーシック (EKZB310000) の Tier 2",
          rr and rr[0] and rr[0]["course_code"] == "EKZB310000" and rr[0]["matched_by"] == "tag"
          and [x["seq"] for x in rr[0]["lessons"]] == [9], rr)
    dets = []
    rr = R(sid_k60, [{"subject_code": "english", "topic": "仮定法(I wish)"}], details=dets)
    check("学年帯は越えない: 高1・2 のどの講座にも仮定法の講が無ければ講座だけ (高3 の講座に移らない)",
          rr and rr[0] and rr[0]["course_code"] == "KZ375000" and rr[0]["matched_by"] == "course"
          and dets[0].get("reason") == "no_lesson_for_tag", (rr, dets))
    dets = []
    rr = R(sid_k60, [{"subject_code": "english", "topic": "関係詞(whose)"}], details=dets)
    check("選んだ講座にタグの講があれば従来どおり (代わりを探さない)", rr and rr[0] and rr[0]["course_code"] == "KZ375000"
          and [x["seq"] for x in rr[0]["lessons"]] == [5, 6] and dets[0].get("reason") is None, (rr, dets))

    print("\n[25] 取込後の点検のレビュー指摘 (2026-10-10): 語彙に無い単元・講データの無い講座の理由・代わりの講座のレベル上限・カタログの偏差値")
    mod._RATE_LIMIT_STORE.clear()
    # (1) 単元名はあるのに語彙・別名に無い → unit_not_in_vocab (科目名だけの subject_only・読解の english_non_grammar と分ける)
    dets = []
    R(sid_r, [{"subject_code": "chemistry", "topic": "化学平衡(テスト)"},
              {"subject_code": "english", "topic": "不定詞の意味上の主語"},
              {"subject_code": "japanese", "topic": "現代文 読解"},
              {"subject_code": "math", "topic": "数学C"},
              {"subject_code": "chemistry", "topic": "化学"},
              {"subject_code": "english", "topic": "事実把握(否定)"}], details=dets)
    whys = [d.get("reason") for d in dets]
    check("理由: 語彙に無い単元 ×3 / 科目名だけ ×2 / 読解の設問タイプ",
          whys == ["unit_not_in_vocab", "unit_not_in_vocab", "unit_not_in_vocab", "subject_only", "subject_only",
                   "english_non_grammar"], whys)
    check("英文法らしい語彙外の単元はカバー状況で英文法の行にまとめる (科目キー eng_grammar)",
          dets[1].get("subject_key") == "eng_grammar" and dets[5].get("subject_key") is None, dets)

    # (2) 選んだ講座に講データが無く、講データのある代わりの講座にもその単元の回が無い → no_lesson_data (no_lesson_for_tag ではない)
    dets = []
    rr = R(sid_eng55, [{"subject_code": "english", "topic": "話法(テスト)"}], details=dets)
    check("講データの無い KZA03000 が選ばれ、どの講座にも話法の回が無い → no_lesson_data",
          rr and rr[0] and rr[0]["course_code"] == "KZA03000" and rr[0]["matched_by"] == "course"
          and rr[0]["course_has_lessons"] is False and dets[0].get("reason") == "no_lesson_data", (rr, dets))

    # (3) 代わりの講座は生徒の偏差値がその講座の目安 ±5 に入るときだけ (レベルが大きく離れた講座へ送らない)
    sid_k75 = make_student(mod, "スタサプ対象 W", "sapuri-w@example.org", labels=LABELS3, grade="高校2年")
    sid_k45 = make_student(mod, "スタサプ対象 X", "sapuri-x@example.org", labels=LABELS3, grade="高校2年")
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO exam_results (student_id, exam_name, exam_date, subject, deviation) VALUES (?,?,?,?,?)",
              (sid_k75, "テスト模試", sd, "英語", 75.0))
    c.execute("INSERT INTO exam_results (student_id, exam_name, exam_date, subject, deviation) VALUES (?,?,?,?,?)",
              (sid_k45, "テスト模試", sd, "英語", 45.0))
    conn.commit(); conn.close()
    check("前提: 高1・2・偏差値 75 の英文法は KZA35000 / 45 は EKZB310000",
          (C3(EG, ["比較"], "高1・2", 75) or {}).get("code") == "KZA35000" and (C3(EG, ["関係詞"], "高1・2", 45) or {}).get("code") == "EKZB310000")
    dets = []
    rr = R(sid_k75, [{"subject_code": "english", "topic": "比較(テスト)"}], details=dets)
    check("偏差値 75: 比較の回はスタンダード (EKZB320000・48-62) にしか無い → 送らず講座だけ (fallback_too_far)",
          rr and rr[0] and rr[0]["course_code"] == "KZA35000" and rr[0]["matched_by"] == "course"
          and dets[0].get("reason") == "fallback_too_far" and dets[0].get("fallback_from") is None, (rr, dets))
    dets = []
    rr = R(sid_k45, [{"subject_code": "english", "topic": "関係詞(テスト)"}], details=dets)
    check("偏差値 45: 関係詞の回はハイ (KZ375000・58-70) にしか無い → 送らず講座だけ (fallback_too_far)",
          rr and rr[0] and rr[0]["course_code"] == "EKZB310000" and rr[0]["matched_by"] == "course"
          and dets[0].get("reason") == "fallback_too_far", (rr, dets))
    dets = []
    rr = R(sid_k60, [{"subject_code": "english", "topic": "語法・イディオム"}], details=dets)
    check("代わりの講座から出したら最初に選んだ講座を details の fallback_from に (推薦の dict には入れない)",
          rr and rr[0] and rr[0]["course_code"] == "KZA35000" and (dets[0].get("fallback_from") or {}).get("code") == "KZ375000"
          and "fallback_from" not in rr[0], (rr, dets))
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO student_weakness (student_id, subject, topic, question_count, avg_confidence_score, last_seen_at, "
              "reason_counts, qa_accuracy, qa_attempts) VALUES (?, ?, ?, 5, 0.5, ?, ?, ?, 3)",
              (sid_k60, "english", "語法・イディオム", datetime.datetime.now(datetime.timezone.utc).isoformat(),
               json.dumps({"understanding": 3}), 0.1))
    conn.commit(); conn.close()
    mod._SAPURI_ELIGIBLE_CACHE.clear()
    r = client.get(f"/api/admin/sapuri/preview?student_id={sid_k60}", headers=adm)
    pw = (r.json().get("weaknesses") or [{}])[0] if r.status_code == 200 else {}
    check("preview の弱点行に fallback_from (CEO ③ に「選んだ講座…から」と出す)",
          (pw.get("fallback_from") or {}).get("code") == "KZ375000" and pw.get("shown"), pw)

    # (4) カリキュラムのカタログも講座ごとにその科目の偏差値で絞る (全科目の平均は使わない)
    snip_chem = mod._build_sapuri_lectures_prompt_snippet(band="高3", student_id=sid_chem)
    snip_old = mod._build_sapuri_lectures_prompt_snippet(band="高3", target_dev=50.0)
    check("化学 50 だけの生徒のカタログに英文法のハイ (KZA02000) が残る (英語は既定 60)",
          "KZA02000:" in snip_chem and "KZA02000:" not in snip_old, (len(snip_chem), len(snip_old)))
    snip_e55 = mod._build_sapuri_lectures_prompt_snippet(band="高3", student_id=sid_eng55)
    check("英語 55 の生徒のカタログに英文法のトップ (KZA01000・65-78) は入らず、スタンダード (KZA03000) は入る",
          "KZA01000:" not in snip_e55 and "KZA03000:" in snip_e55, len(snip_e55))

    # ======================================================================
    # 📺 見た回のチェックと進み具合 (2026-10-10 塾長「見た回のチェック（進み具合の記録）機能も作って」)。題名は架空。
    # ======================================================================
    print("\n[26] 見た回のチェック (POST watched / GET progress・次の回へ・見終わり・週次・カリキュラムと計画の x/y・統合と削除)")
    mod._RATE_LIMIT_STORE.clear()
    mod._SAPURI_ELIGIBLE_CACHE.clear()
    mod._AI_DISABLED_CACHE.clear()
    W, PG = "/api/student/class/sapuri/watched", "/api/student/class/sapuri/progress"
    K5, K6, K12 = "KZA02000#5", "KZA02000#6", "KZ277000#12"

    def watch(sid, key, on=True, extra=None, headers=None):
        mod._RATE_LIMIT_STORE.clear()
        body = {"lesson_key": key, "watched": on, "surface": "class"}
        body.update(extra or {})
        return client.post(W, json=body, headers=headers if headers is not None else tok(sid))

    def prog_rows(sid):
        conn = mod.db(); c = conn.cursor()
        c.execute("SELECT lesson_key, watched_at FROM sapuri_lesson_progress WHERE student_id = ? ORDER BY lesson_key", (sid,))
        out = [(r["lesson_key"], str(r["watched_at"])) for r in c.fetchall()]
        conn.close()
        return out

    def cls(sid):
        mod._RATE_LIMIT_STORE.clear()
        r = client.get("/api/student/class/sapuri", headers=tok(sid))
        return r.status_code, ((r.json() if r.status_code == 200 else {}).get("items") or []), r.text

    def top3(sid):
        mod._RATE_LIMIT_STORE.clear()
        r = client.get(f"/api/student/weakness-top3?student_id={sid}", headers=tok(sid))
        return r.status_code, [w.get("sapuri") for w in ((r.json() if r.status_code == 200 else {}).get("weaknesses") or [])], r.text

    # (1) 認証と対象
    check("前提: 見た回の記録は 0 行", n_rows("SELECT COUNT(*) FROM sapuri_lesson_progress") == 0)
    r = client.post(W, json={"lesson_key": K5, "watched": True})
    check("watched: 未ログインは 401", r.status_code == 401, r.status_code)
    r = client.get(PG)
    check("progress: 未ログインは 401", r.status_code == 401, r.status_code)
    r = watch(sid_ai, K5)
    check("watched: 対象外 (AI 学習管理コース) は 403", r.status_code == 403 and "授業コース" in r.text, r.text)
    r = client.get(PG, headers=tok(sid_ai))
    check("progress: 対象外は 200・items 空 (読むときに隠す)", r.status_code == 200 and r.json().get("items") == []
          and r.json().get("eligible") is False, r.text)
    r = watch(sid_noai, K12)
    check("watched: AIなし枠 (塾生アプリのみ) の対象生徒でも 200 (prefix /api/student/class/ は許可済み)", r.status_code == 200
          and r.json().get("watched") is True, r.text)
    sid_light = make_student(mod, "ライト L", "sapuri-light@example.org", labels=LABELS3)
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE students SET feature_tier = 'light' WHERE id = ?", (sid_light,))
    conn.commit(); conn.close()
    mod._AI_DISABLED_CACHE.clear()
    r = watch(sid_light, K12)
    check("watched: ライトの対象生徒も 200 (AI を呼ばない)", r.status_code == 200, r.text)
    mod._RATE_LIMIT_STORE.clear()
    r = client.get(PG, headers=tok(sid_light))
    check("progress: ライトも 200", r.status_code == 200 and r.json().get("total") == 1, r.text)

    # (2) 入力の検査
    for bad_key, why in (("KZA02000-5", "形が違う"), ("ZZ999#1", "カタログに無い講座"), ("KZA02000#99", "範囲外の講番号"),
                         ("KZA02000#0", "第0講"), ("", "空"), ("KZ240000#3", "講データの無い講座 (DB に無い講)")):
        r = watch(sid_ok, bad_key)
        check(f"watched: {why} は 400", r.status_code == 400, (bad_key, r.status_code, r.text[:120]))
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE sapuri_lessons SET active = 0 WHERE lesson_key = 'KZA02000#7'")
    conn.commit(); conn.close()
    r = watch(sid_ok, "KZA02000#7")
    check("watched: 止めた講 (active=0) は記録できない (400)", r.status_code == 400, r.text)
    r = watch(sid_ok, "KZA02000#7", on=False)
    check("watched: 止めた講の取り消しは 200 (記録を消せる)", r.status_code == 200 and r.json().get("watched") is False, r.text)
    client.post(IMP, json=kza_body, headers=adm)   # 戻す
    orig_keys = mod.SAPURI_SUBJECT_KEYS
    mod.SAPURI_SUBJECT_KEYS = tuple(k for k in orig_keys if k != "eng_grammar")
    try:
        r = watch(sid_ok, K5)
        check("watched: 止めた科目 (SAPURI_SUBJECT_KEYS から外した) の講は 400", r.status_code == 400, r.text)
    finally:
        mod.SAPURI_SUBJECT_KEYS = orig_keys
    orig_ready = mod._sapuri_progress_ready
    mod._sapuri_progress_ready = lambda: False
    try:
        r = watch(sid_ok, K5)
        check("watched: 表が無い (DDL 未反映) なら 503", r.status_code == 503, r.text)
        rr = R(sid_ok, [{"subject_code": "english", "topic": "関係詞"}])
        check("表が無いときの照合は従来どおり (全部まだ見ていない扱い)", rr[0] and [x["seq"] for x in rr[0]["lessons"]] == [5, 6]
              and all(x.get("watched") is False for x in rr[0]["lessons"]), rr[0])
    finally:
        mod._sapuri_progress_ready = orig_ready
    check("ここまでで sid_ok の記録は 0 行 (拒否は書かない)", prog_rows(sid_ok) == [], prog_rows(sid_ok))

    # (3) 冪等
    r1 = watch(sid_ok, K5)
    time.sleep(1.1)
    r2 = watch(sid_ok, K5)
    j1, j2 = (r1.json() if r1.status_code == 200 else {}), (r2.json() if r2.status_code == 200 else {})
    check("watched: 200・{ok, lesson_key, watched, watched_at (offset つき), watched_date_jst}", r1.status_code == 200
          and j1.get("ok") is True and j1.get("lesson_key") == K5 and j1.get("watched") is True
          and str(j1.get("watched_at") or "").endswith("+00:00") and re.match(r"^\d{4}-\d{2}-\d{2}$", str(j1.get("watched_date_jst"))), r1.text)
    check("冪等: 二度押しでも 1 行・最初の日時のまま", len(prog_rows(sid_ok)) == 1 and j1.get("watched_at") == j2.get("watched_at"),
          (prog_rows(sid_ok), j1, j2))
    check("watched_at は _utc_naive_iso の形 (offset なし)", "+" not in prog_rows(sid_ok)[0][1] and "T" in prog_rows(sid_ok)[0][1],
          prog_rows(sid_ok))
    r = watch(sid_ok, K6, on=False)
    r2 = watch(sid_ok, K6, on=False)
    check("取り消しは見ていない回でも 200 (冪等)", r.status_code == 200 and r2.status_code == 200, (r.text, r2.text))

    # (4) 他人
    r = watch(sid_now, K5, extra={"student_id": sid_ok})
    check("body の student_id は読まない (トークンの生徒に書く)", r.status_code == 200
          and [k for k, _ in prog_rows(sid_now)] == [K5] and len(prog_rows(sid_ok)) == 1, (prog_rows(sid_now), prog_rows(sid_ok)))
    r = watch(sid_now, K5, on=False)
    check("他人が同じ講を取り消しても自分の行は残る", r.status_code == 200 and prog_rows(sid_now) == [] and len(prog_rows(sid_ok)) == 1,
          (prog_rows(sid_now), prog_rows(sid_ok)))
    mod._RATE_LIMIT_STORE.clear()
    r = client.get(PG, headers=tok(sid_now))
    check("他人の一覧に自分の見た回は出ない", r.status_code == 200 and r.json().get("items") == [], r.text)
    mod._RATE_LIMIT_STORE.clear()
    r = client.get(PG, headers=tok(sid_ok))
    j = r.json() if r.status_code == 200 else {}
    it0 = (j.get("items") or [{}])[0]
    check("progress: 自分の見た回 (講座名・第N講・題名・日付)", r.status_code == 200 and j.get("total") == 1
          and it0.get("lesson_key") == K5 and it0.get("course_code") == "KZA02000" and it0.get("seq") == 5
          and it0.get("course_name") == "高3 ハイレベル英語＜文法編＞" and it0.get("title") == "テスト講義A5"
          and it0.get("watched_date_jst") == j1.get("watched_date_jst"), r.text[:300])

    # (5) 次の回へ進む
    code, items, t = cls(sid_ok)
    check("class: 見た #5 を飛ばして #6 (範囲なし・watched=false・all_watched=false)", code == 200 and items
          and (items[0]["course_code"], items[0]["lessons"][0]["seq"]) == ("KZA02000", 6) and items[0]["to_seq"] is None
          and items[0]["lessons"][0].get("watched") is False and items[0].get("all_watched") is False, t[:400])
    check("class: label も #6 から作り直す (見た #5 の題名を残さない)", items and "テスト講義A6" in items[0]["label"]
          and "テスト講義A5" not in json.dumps(items[0], ensure_ascii=False), items[:1])
    code, sp, t = top3(sid_ok)
    check("TOP3: 次の回 (#6)・2 位は重複のまま出さない", code == 200 and sp and sp[0] and sp[0]["lessons"][0]["seq"] == 6
          and sp[0].get("all_watched") is False and sp[1] is None, t[:300])

    # this-week: 保存済みの週次プリント (#5) は作り直さず ✅ の印だけ
    r = client.get("/api/student/worksheet/this-week", headers=tok(sid_ok))
    st0 = ((r.json().get("worksheet") or {}).get("subject_topics") or [{}])[0] if r.status_code == 200 else {}
    l0 = ((st0.get("sapuri") or {}).get("lessons") or [{}])[0]
    check("this-week: 保存済みの回 (#5) に watched=true と日付・作り直さない", r.status_code == 200 and l0.get("seq") == 5
          and l0.get("watched") is True and l0.get("watched_date_jst") == j1.get("watched_date_jst") and "テスト講義A5" in r.text, st0)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT subject_topics FROM worksheet_archives WHERE student_id = ?", (sid_ok,))
    check("this-week: 保存した行は書き換えない (watched を保存しない)", '"watched"' not in (c.fetchone()["subject_topics"] or ""))
    conn.close()

    # (6) 全部見た
    watch(sid_ok, K6)
    code, items, t = cls(sid_ok)
    check("class: 弱点に合う回を全部見たら出さず、次の弱点 (#12) が上がる", code == 200 and [(x["course_code"], x["lessons"][0]["seq"]) for x in items]
          == [("KZ277000", 12)], t[:400])
    code, sp, t = top3(sid_ok)
    check("TOP3: 見終わり (all_watched=true・lessons 空・題名なし)", code == 200 and sp and sp[0] and sp[0].get("all_watched") is True
          and sp[0]["lessons"] == [] and sp[0]["to_seq"] is None and "テスト講義" not in json.dumps(sp[0], ensure_ascii=False)
          and sp[0]["course_code"] == "KZA02000", sp[:1])
    r = client.get(f"/api/admin/sapuri/preview?student_id={sid_ok}", headers=adm)
    j = r.json() if r.status_code == 200 else {}
    pw = j.get("weaknesses") or []
    check("preview: class_items から消え、why=all_watched・all_watched=true・lessons の watched", r.status_code == 200
          and [(x["course_code"], x["lessons"][0]["seq"]) for x in j.get("class_items") or []] == [("KZ277000", 12)]
          and pw and pw[0].get("why") == "all_watched" and pw[0].get("all_watched") is True
          and all(l.get("watched") is True for l in pw[0]["recommendation"]["lessons"]), r.text[:400])
    check("preview: top3 は見終わりを残す (生徒の TOP3 と同じ)", j.get("top3") and j["top3"][0].get("all_watched") is True, j.get("top3"))
    rc = client.get("/api/student/class/sapuri", headers=tok(sid_ok))
    check("preview: class_items は生徒の class と同じ", rc.status_code == 200 and j.get("class_items") == rc.json().get("items"), rc.text[:200])

    # (7) 取り消すと戻る
    watch(sid_ok, K6, on=False)
    code, sp, t = top3(sid_ok)
    check("取り消し: TOP3 にまた #6", code == 200 and sp and sp[0] and sp[0]["lessons"][0]["seq"] == 6 and sp[0].get("all_watched") is False, sp[:1])
    watch(sid_ok, K6)

    # (8) 週次: 見た回はメール・LINE に出さない
    conn = mod.db(); c = conn.cursor()
    c.execute("DELETE FROM worksheet_archives WHERE student_id = ?", (sid_ok,))
    conn.commit(); conn.close()
    mails, lines = [], []
    orig_mail, orig_line = mod._send_monitor_email, mod._do_line_push
    mod._send_monitor_email = lambda subj, body, to_email=None: (mails.append((to_email, body)) or {"sent": True})
    mod._do_line_push = lambda sid, tmpl, params: (lines.append((sid, tmpl, params)) or {"ok": True})
    try:
        res = mod._run_weekly_worksheet_generation()
    finally:
        mod._send_monitor_email, mod._do_line_push = orig_mail, orig_line
    m_ok = next((b for to, b in mails if to == "sapuri-a@example.org"), None)
    lp = next((p_ for s_, t_, p_ in lines if s_ == sid_ok), None)
    check("週次: プリントは作り直される (前提)", m_ok is not None and lp is not None, (res, len(mails), len(lines)))
    check("週次: 見終わった英文法の回はメールに出ない", m_ok is not None and "ハイレベル英語＜文法編＞" not in m_ok and "テスト講義" not in m_ok, m_ok)
    check("週次: LINE の sapuri_line にも出ない", lp is not None and "ハイレベル英語＜文法編＞" not in str(lp.get("sapuri_line") or ""), lp)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT subject_topics FROM worksheet_archives WHERE student_id = ?", (sid_ok,))
    row = c.fetchone()
    conn.close()
    st_new = json.loads(row["subject_topics"]) if row else []
    check("週次: 保存した subject_topics にも見終わった回は無い", row is not None and all(((x.get("sapuri") or {}).get("course_code") != "KZA02000")
                                                                for x in st_new), st_new)

    # (9) カリキュラムと学習計画の「見た x / y 講」
    sid_p = make_student(mod, "スタサプ対象 P", "sapuri-p@example.org", labels=LABELS3)
    for k in (K5, K6):
        watch(sid_p, k)
    body = {"target_university": "テスト大学", "exam_date": ed, "start_date": sd,
            "phases": [phase("基礎期", sd, ed, materials=["ポラリス1"], sapuri=[{"course_code": "KZA02000", "from_seq": 5, "to_seq": 8},
                                                                             {"course_code": "KZ016000", "from_seq": 1, "to_seq": 3}])]}
    r = client.post("/api/curricula", json=body, headers=tok(sid_p))
    check("前提: カリキュラムを保存", r.status_code == 200, r.text[:200])
    cur = client.get("/api/curricula/me", headers=tok(sid_p)).json()["curricula"][0]
    ph0 = cur["phases"][0]
    check("/me: 範囲ごとに見た x / y 講 (sapuri と同じ並び・講データの無い講座の範囲は None・sapuri の形は変えない)",
          ph0.get("sapuri_progress") == [{"course_code": "KZA02000", "watched_count": 2, "total": 4}, None]
          and ph0.get("sapuri") == [{"course_code": "KZA02000", "from_seq": 5, "to_seq": 8}, {"course_code": "KZ016000", "from_seq": 1, "to_seq": 3}], ph0)
    r = client.put(f"/api/curricula/{cur['id']}", json={"phases": cur["phases"]}, headers=tok(sid_p))
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT phases FROM curricula WHERE id = ?", (cur["id"],))
    raw = c.fetchone()["phases"]
    conn.close()
    check("PUT で送り返しても見た x / y 講は保存しない", r.status_code == 200 and "sapuri_progress" not in raw and "watched_count" not in raw, raw[:300])
    st = mod._sapuri_phase_normalize(dict(ph0), True)
    check("正規化は送り返された sapuri_progress を捨てる (apply-gap-fix・下書きの保存も同じ)", "sapuri_progress" not in st, st)
    r = client.post(f"/api/curricula/{cur['id']}/expand-to-plans", headers=tok(sid_p))
    check("前提: 学習計画に展開", r.status_code == 200 and r.json().get("added", 0) >= 3, r.text[:200])
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO study_plans (student_id, title, subject, material, start_date, end_date, target_minutes, color, note) "
              "VALUES (?,?,?,?,?,?,?,?,?)", (sid_p, "手入力", "英語", "架空の講座 第1〜3講", sd, ed, 60, "#000000", "出典: スタサプ (手入力)"))
    conn.commit(); conn.close()
    r = client.get("/api/study-plans/me", headers=tok(sid_p))
    plans = r.json().get("plans") or [] if r.status_code == 200 else []
    bym = {x["material"]: x for x in plans}
    pk = bym.get("高3 ハイレベル英語＜文法編＞ 第5〜8講") or {}
    check("/study-plans/me: スタサプの計画に見た x / y 講と次の回", pk.get("sapuri_progress") == {
        "watched": 2, "total": 4, "course_code": "KZA02000", "next_seq": 7, "next_key": "KZA02000#7"}, pk.get("sapuri_progress"))
    pko = bym.get("高3 古文＜文法編＞ 第1〜3講") or {}
    check("/study-plans/me: 講データの無い講座の計画には付けない (永久に 0 / 3 のバーにせず勉強時間のバーのまま)",
          bool(pko) and "sapuri_progress" not in pko and pko.get("target_minutes") is not None, pko)
    check("/study-plans/me: スタサプ以外・material が読めない計画には付けない", "sapuri_progress" not in (bym.get("ポラリス1") or {"sapuri_progress": 1})
          and "sapuri_progress" not in (bym.get("架空の講座 第1〜3講") or {"sapuri_progress": 1}), list(bym))
    watch(sid_p, "KZA02000#7")
    r = client.get("/api/study-plans/me", headers=tok(sid_p))
    pk = {x["material"]: x for x in r.json().get("plans") or []}.get("高3 ハイレベル英語＜文法編＞ 第5〜8講") or {}
    check("計画の「☐ 第7講を見た」を押すと 3 / 4・次は第8講", (pk.get("sapuri_progress") or {}).get("watched") == 3
          and (pk.get("sapuri_progress") or {}).get("next_seq") == 8, pk.get("sapuri_progress"))
    # 取込で止めた講 (active=0): まだ見ていなければ分母から外す (押せない回で止まらない)・見た回は記録が残るので数える
    def plan_and_phase():
        mod._RATE_LIMIT_STORE.clear()
        pk_ = {x["material"]: x for x in client.get("/api/study-plans/me", headers=tok(sid_p)).json().get("plans") or []}
        ph_ = client.get("/api/curricula/me", headers=tok(sid_p)).json()["curricula"][0]["phases"][0]
        return (pk_.get("高3 ハイレベル英語＜文法編＞ 第5〜8講") or {}).get("sapuri_progress"), ph_.get("sapuri_progress")
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE sapuri_lessons SET active = 0 WHERE lesson_key IN ('KZA02000#8', ?)", (K5,))
    conn.commit(); conn.close()
    try:
        sp_, pp_ = plan_and_phase()
        check("止めた講: まだ見ていない #8 は分母から外す・見た #5 は数える → 3 / 3・次の回なし (✅ 全部見ました)",
              sp_ == {"watched": 3, "total": 3, "course_code": "KZA02000", "next_seq": None, "next_key": None}, sp_)
        check("止めた講: カリキュラムの範囲も 3 / 3", (pp_ or [None])[0] == {"course_code": "KZA02000", "watched_count": 3, "total": 3}, pp_)
        conn = mod.db(); c = conn.cursor()
        c.execute("UPDATE sapuri_lessons SET active = 0 WHERE lesson_key LIKE 'KZA02000#%'")
        c.execute("DELETE FROM sapuri_lesson_progress WHERE student_id = ?", (sid_p,))
        conn.commit(); conn.close()
        sp_, pp_ = plan_and_phase()
        check("範囲の講が全部止まっていて見た回も無い → 計画にもカリキュラムにも付けない", sp_ is None and pp_ is None, (sp_, pp_))
    finally:
        client.post(IMP, json=kza_body, headers=adm)   # 戻す
        for k in (K5, K6, "KZA02000#7"):
            watch(sid_p, k)

    # (10) 統合: 早い方の日時を残す・消す側の行は 0
    sid_ma = make_student(mod, "統合 残す側", "sapuri-ma@example.org", labels=LABELS3)
    sid_mb = make_student(mod, "統合 消す側", "sapuri-mb@example.org", labels=LABELS3)
    t0 = mod._utc_naive_iso(datetime.datetime(2026, 9, 1, 3, 0, tzinfo=datetime.timezone.utc))
    t1 = mod._utc_naive_iso(datetime.datetime(2026, 10, 1, 3, 0, tzinfo=datetime.timezone.utc))
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO sapuri_lesson_progress (student_id, lesson_key, watched_at, source) VALUES (?, ?, ?, 'class')", (sid_ma, K5, t1))
    c.execute("INSERT INTO sapuri_lesson_progress (student_id, lesson_key, watched_at, source) VALUES (?, ?, ?, 'class')", (sid_mb, K5, t0))
    c.execute("INSERT INTO sapuri_lesson_progress (student_id, lesson_key, watched_at, source) VALUES (?, ?, ?, 'class')", (sid_mb, K6, t1))
    conn.commit(); conn.close()
    r = client.post(f"/api/admin/students/{sid_ma}/merge", json={"from_id": sid_mb, "dry_run": True}, headers=adm)
    jd = r.json() if r.status_code == 200 else {}
    check("統合 dry_run: 衝突 1・移す 1・何も書かない", r.status_code == 200 and (jd.get("conflicts") or {}).get("sapuri_lesson_progress") == 1
          and (jd.get("moved") or {}).get("sapuri_lesson_progress") == 1 and prog_rows(sid_ma) == [(K5, t1)], (r.text[:300], prog_rows(sid_ma)))
    r = client.post(f"/api/admin/students/{sid_ma}/merge", json={"from_id": sid_mb, "dry_run": False}, headers=adm)
    check("統合: 残す側に #5 (早い方の日時) と #6・消す側は 0 行", r.status_code == 200 and prog_rows(sid_ma) == [(K5, t0), (K6, t1)]
          and prog_rows(sid_mb) == [], (r.text[:200], prog_rows(sid_ma), prog_rows(sid_mb)))

    # (11) 削除と孤児の掃除
    r = client.post(f"/api/admin/students/{sid_ma}/delete", json={"confirm_email": "sapuri-ma@example.org", "dry_run": True}, headers=adm)
    check("削除の下見: related_counts に見た回 (2 行)", r.status_code == 200
          and ((r.json().get("snapshot") or {}).get("related_counts") or {}).get("sapuri_lesson_progress") == 2,
          r.text[:300])
    r = client.post(f"/api/admin/students/{sid_ma}/delete", json={"confirm_email": "sapuri-ma@example.org", "dry_run": False,
                                                                  "cancel_stripe": False}, headers=adm)
    check("削除: 見た回の行も消える", r.status_code == 200 and prog_rows(sid_ma) == [], (r.text[:200], prog_rows(sid_ma)))
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO sapuri_lesson_progress (student_id, lesson_key, watched_at) VALUES (?, ?, ?)", (987654, K5, t1))
    conn.commit()
    sw = mod._sweep_student_orphans(conn, c, dry_run=False)
    conn.close()
    check("孤児の掃除: students に無い生徒の見た回を消す", sw.get("sapuri_lesson_progress") == 1 and prog_rows(987654) == [], sw)
    check("_ORPHAN_SWEEP_TABLES と _MERGE_STUDENT_TABLES の両方にある", "sapuri_lesson_progress" in mod._ORPHAN_SWEEP_TABLES
          and any(t == "sapuri_lesson_progress" for t, _ in mod._MERGE_STUDENT_TABLES))

    # (12) 管理
    r = client.get("/api/admin/sapuri/status", headers=adm)
    stu = {x["id"]: x for x in (r.json() if r.status_code == 200 else {}).get("students", [])}
    check("status: 生徒ごとの見た講数と最後に見た日 (日本時間の日付)", stu.get(sid_ok, {}).get("watched_count") == 2
          and re.match(r"^\d{4}-\d{2}-\d{2}$", str(stu.get(sid_ok, {}).get("last_watched_at")))
          and stu.get(sid_ai, {}).get("watched_count") == 0 and stu.get(sid_ai, {}).get("last_watched_at") is None, stu.get(sid_ok))
    check("status: 題名を返さない", "テスト講義" not in r.text)
    for hdr in (tok(sid_ok), {}):
        r = client.get(f"/api/admin/sapuri/progress?student_id={sid_ok}", headers=hdr)
        check("admin progress: 生徒のトークン・未認証は 401", r.status_code == 401, r.status_code)
    r = client.get(f"/api/admin/sapuri/progress?student_id={sid_ok}", headers=adm)
    ja = r.json() if r.status_code == 200 else {}
    check("admin progress: 題名つき・active・source・新しい順", r.status_code == 200 and ja.get("total") == 2
          and [x["lesson_key"] for x in ja.get("items", [])] == [K6, K5] and ja["items"][1].get("title") == "テスト講義A5"
          and ja["items"][0].get("active") is True and ja["items"][0].get("source") == "class", r.text[:300])
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE sapuri_lessons SET active = 0 WHERE lesson_key = ?", (K5,))
    conn.commit(); conn.close()
    mod._RATE_LIMIT_STORE.clear()
    r = client.get(PG, headers=tok(sid_ok))
    i5 = next((x for x in (r.json() if r.status_code == 200 else {}).get("items", []) if x["lesson_key"] == K5), {})
    check("生徒の一覧: 止めた講 (active=0) の記録は残すが題名は出さない (講座名と第N講だけ)", i5.get("seq") == 5 and i5.get("title") is None
          and i5.get("course_name"), i5)
    r = client.get(f"/api/admin/sapuri/progress?student_id={sid_ok}", headers=adm)
    a5 = next((x for x in (r.json() if r.status_code == 200 else {}).get("items", []) if x["lesson_key"] == K5), {})
    check("管理者の一覧: 止めた講も題名と active=false", a5.get("title") == "テスト講義A5" and a5.get("active") is False, a5)
    client.post(IMP, json=kza_body, headers=adm)   # 戻す
    orig_keys = mod.SAPURI_SUBJECT_KEYS
    mod.SAPURI_SUBJECT_KEYS = tuple(k for k in orig_keys if k != "eng_grammar")
    try:
        mod._RATE_LIMIT_STORE.clear()
        r = client.get(PG, headers=tok(sid_ok))
        check("生徒の一覧: 止めた科目の行は出さない (消さない)", r.status_code == 200 and r.json().get("items") == [] and len(prog_rows(sid_ok)) == 2,
              r.text[:200])
    finally:
        mod.SAPURI_SUBJECT_KEYS = orig_keys

    # (12b) 回数制限は生徒ごと (Vercel rewrite で全生徒が同じ IP になっても、1 人の連打で他の生徒が 429 にならない)
    mod._RATE_LIMIT_STORE.clear()
    codes = [client.get(PG, headers=tok(sid_ok)).status_code for _ in range(61)]
    check("progress: 1 人 1 分 60 回までは 200・61 回目は 429", codes[:60] == [200] * 60 and codes[60] == 429, codes[-3:])
    r = client.get(PG, headers=tok(sid_light))
    check("progress: 同じ IP の別の生徒は 200 (IP 単位の枠を共有しない)", r.status_code == 200, r.status_code)
    mod._RATE_LIMIT_STORE.clear()
    body_ = {"lesson_key": K12, "watched": True, "surface": "class"}
    codes = [client.post(W, json=body_, headers=tok(sid_light)).status_code for _ in range(61)]
    check("watched: 1 人 1 分 60 回までは 200・61 回目は 429", codes[:60] == [200] * 60 and codes[60] == 429, codes[-3:])
    r = client.post(W, json=body_, headers=tok(sid_noai))
    check("watched: 同じ IP の別の生徒は 200", r.status_code == 200, r.status_code)
    src_ = open(MAIN_PY, encoding="utf-8").read()
    for fn_ in ("student_class_sapuri_watched", "student_class_sapuri_progress"):
        body_src = src_[src_.index(f"def {fn_}("):]
        body_src = body_src[:body_src.index("\n@app.")]
        check(f"{fn_}: 回数制限は _check_rate_limit_caller (IP 単位の _check_rate_limit_ip を使わない)",
              "_check_rate_limit_caller(request, authorization" in body_src and "_check_rate_limit_ip(" not in body_src)
    mod._RATE_LIMIT_STORE.clear()

    # (13) 見た回の読み取りは画面ごとに 1 回 (N+1 にしない)・カバー状況は読まない
    calls = []
    orig_wm = mod._sapuri_watched_map
    def counting(*a, **k):
        calls.append(1)
        return orig_wm(*a, **k)
    mod._sapuri_watched_map = counting
    try:
        def n_calls(fn):
            calls.clear()
            mod._RATE_LIMIT_STORE.clear()
            r_ = fn()
            return r_.status_code, len(calls)
        conn = mod.db(); c = conn.cursor()
        c.execute("DELETE FROM worksheet_archives WHERE student_id = ?", (sid_p,))
        c.execute("INSERT INTO worksheet_archives (student_id, week_start_date, subject_topics, questions_json, question_count) "
                  "VALUES (?, ?, ?, '[]', 0)", (sid_p, sd, json.dumps([{"subject": "english", "topic": "関係詞", "sapuri": {
                      "subject_key": EG, "course_code": "KZA02000", "course_name": "高3 ハイレベル英語＜文法編＞",
                      "lessons": [{"lesson_key": K5, "seq": 5, "title": "テスト講義A5"}], "to_seq": 6, "matched_by": "tag"}},
                      {"subject": "english", "topic": "時制", "sapuri": {"subject_key": EG, "course_code": "KZA02000",
                       "course_name": "高3 ハイレベル英語＜文法編＞", "lessons": [{"lesson_key": "KZA02000#1", "seq": 1, "title": "テスト講義A1"}],
                       "to_seq": None, "matched_by": "tag"}}], ensure_ascii=False)))
        conn.commit(); conn.close()
        for label, fn, want in (
                ("class/sapuri", lambda: client.get("/api/student/class/sapuri", headers=tok(sid_ok)), 1),
                ("weakness-top3", lambda: client.get(f"/api/student/weakness-top3?student_id={sid_ok}&limit=5", headers=tok(sid_ok)), 1),
                ("this-week (sapuri 2 件)", lambda: client.get("/api/student/worksheet/this-week", headers=tok(sid_p)), 1),
                ("curricula/me", lambda: client.get("/api/curricula/me", headers=tok(sid_p)), 1),
                ("study-plans/me", lambda: client.get("/api/study-plans/me", headers=tok(sid_p)), 1),
                ("admin preview", lambda: client.get(f"/api/admin/sapuri/preview?student_id={sid_ok}", headers=adm), 1),
                ("coverage (見た回に左右されない)", lambda: client.get("/api/admin/sapuri/coverage", headers=adm), 0)):
            code, n = n_calls(fn)
            check(f"見た回の読み取り: {label} は {want} 回", code == 200 and n == want, (code, n))
        r = client.get("/api/student/worksheet/this-week", headers=tok(sid_p))
        sts = (r.json().get("worksheet") or {}).get("subject_topics") or []
        check("this-week: 見た回 (#5) は ✅・見ていない回 (#1) は ☐", [((x.get("sapuri") or {}).get("lessons") or [{}])[0].get("watched") for x in sts]
              == [True, False], sts)
    finally:
        mod._sapuri_watched_map = orig_wm
    src = open(MAIN_PY, encoding="utf-8").read()
    wfn = src[src.index("def _run_weekly_worksheet_generation("):src.index("@app.get(\"/api/student/worksheet/this-week\")")]
    check("週次プリントの関数は変えていない (見た回を読まない・1 行で呼ぶだけ)", "_sapuri_watched_map" not in wfn
          and wfn.count("_sapuri_for_subject_topics(sid, sgrade, subject_topics)") == 1)
    dfn = src[src.index("def _sapuri_display_ex("):src.index("def _sapuri_display(")]
    check("見た回を飛ばすのは _sapuri_display_ex だけ (照合は watched の印を付けるだけ)",
          'l.get("watched")' in dfn and 'if not l.get("watched")' not in src[src.index("def _sapuri_match_one("):src.index("def _sapuri_display_ex(")])

    print()
    if FAILURES:
        print(f"❌ FAIL: {len(FAILURES)} 件")
        for f in FAILURES:
            print(f"   - {f}")
        return 1
    print("✅ PASS: スタサプ 段階 A・B")
    return 0


if __name__ == "__main__":
    sys.exit(main())
