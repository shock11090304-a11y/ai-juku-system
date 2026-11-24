#!/usr/bin/env python3
"""🎬 単元の動画 (2026-11-24) の回帰テスト。

背景: 塾HP に「宿題：塾生アプリで演習し、正解率を測ります。正解率を見て、必要な動画で抜けをなくします」と載せた。
  宿題の英文法ドリルで正解率の低い単元に、その単元の自前の動画 (通塾 英文法の説明動画 第1〜21回・
  問題演習の解説動画 第1〜20回×前半・後半) を出す。動画の一覧と単元の対応はコードの定数、YouTube の ID は表 unit_video_links。

固定する性質 (実際のルートを TestClient で呼ぶ):
  1. 一覧: 61 本・鍵が一意・英文法ドリルの全単元 (GRAMMAR_UNITS) に対応の行がある・回は 1〜21
  2. 弱点の topic → ドリルの単元 (english だけ・「英文法 」の接頭辞・別名・長文は None・中学は None)
  3. CEO の API: 認証・61 行・不正な鍵や URL は 400 で何も書かない・保存・空で外す
  4. 通塾生アプリ GET /api/student/class/unit-videos: 401・正解率 80% 未満で採点 2 問以上の単元だけ・正解率の低い順・
     URL の無い動画は出さない・説明動画を先・同じ単元は 1 回・最大 3 単元・AIなし枠でも 200
  5. mypage の弱点 TOP3 に unit_videos が付く (正解率の低い英文法の単元だけ)
  6. 画面 (class.html / mypage.html / ceo.html) に描画とボタンがある

実行:
    python3 scripts/health_check/test_unit_videos.py
    # exit 0 = PASS / 1 = FAIL
外部通信はしない。DB は一時 SQLite。
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
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="unitvid_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと本番 Postgres に書き込む
        "DATABASE_URL": "",
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_unitvid", MAIN_PY)
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


def make_student(mod, name, email, *, ai_disabled=0):
    conn = mod.db()
    c = conn.cursor()
    te = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)).isoformat()
    c.execute(
        "INSERT INTO students (name, email, status, trial_end, course, grade, goal, ai_disabled, class_labels) "
        "VALUES (?, ?, 'trial', ?, 'kokuritsu_nankan', '高校2年', '国公立大学', ?, '[]')",
        (name, email, te, ai_disabled),
    )
    conn.commit()
    c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
    sid = c.fetchone()["id"]
    conn.close()
    return sid


def add_weak(mod, sid, subject, topic, acc, attempts, count=None):
    conn = mod.db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO student_weakness (student_id, subject, topic, question_count, avg_confidence_score, qa_accuracy, "
        "qa_attempts, last_seen_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (sid, subject, topic, count if count is not None else attempts, acc, acc, attempts,
         datetime.datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def link_count(mod):
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) AS n FROM unit_video_links")
    n = c.fetchone()["n"]
    conn.close()
    return n


def main():
    print("🎬 単元の動画 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    mod._RATE_LIMIT_STORE.clear()

    print("[1] 動画の一覧と単元の対応")
    keys = [v["key"] for v in mod.TG_VIDEOS]
    check("61 本 (説明動画 21 + 問題演習の解説 20×2)", len(keys) == 61, len(keys))
    check("鍵が一意", len(set(keys)) == len(keys))
    check("英文法ドリルの全単元に対応の行がある", set(mod.GRAMMAR_UNITS) == set(mod.TG_DRILL_UNIT_TO_NOS),
          set(mod.GRAMMAR_UNITS) ^ set(mod.TG_DRILL_UNIT_TO_NOS))
    nos = [n for v in mod.TG_DRILL_UNIT_TO_NOS.values() for n in v]
    check("回は 1〜21 の範囲", all(1 <= n <= 21 for n in nos), nos)
    check("第2回は時制・第11回は関係詞・第20回は話法",
          mod.TG_VIDEO_BY_KEY["tg-exp-02"]["unit"] == "時制" and mod.TG_VIDEO_BY_KEY["tg-exp-11"]["unit"] == "関係詞"
          and mod.TG_VIDEO_BY_KEY["tg-prc-20-b"]["unit"] == "話法")
    check("問題演習の解説は第21回 (総復習) が無い", "tg-prc-21-a" not in mod.TG_VIDEO_BY_KEY)

    print("\n[2] 弱点の topic → ドリルの単元")
    U = mod._tg_drill_unit
    check("english 時制 → 時制", U("english", "時制") == "時制")
    check("「英文法 関係詞」→ 関係詞", U("english", "英文法 関係詞") == "関係詞")
    check("ドリル以外の自由な topic は当てない (「現在完了(継続)」「名詞節」「完了形」→ None)",
          U("english", "現在完了(継続)") is None and U("english", "名詞節") is None and U("english", "完了形") is None)
    check("「英文法 時制」(接頭辞つき) → 時制", U("english", "英文法 時制") == "時制")
    check("80% 前後は TOP3 と同じ丸め (0.799 は低くない・0.794 は低い)",
          mod._tg_is_low(0.799, 5) is False and mod._tg_is_low(0.794, 5) is True)
    check("「否定・倒置」→ 否定・倒置", U("english", "否定・倒置") == "否定・倒置")
    check("長文読解 → None", U("english", "長文読解") is None, U("english", "長文読解"))
    check("中学 (chugaku) の時制 → None", U("chugaku", "時制") is None)
    check("数学 → None", U("math", "二次関数") is None)

    print("\n[3] CEO の API")
    r = client.get("/api/admin/unit-videos")
    check("認証なしの一覧は 401/403", r.status_code in (401, 403), r.status_code)
    r = client.get("/api/admin/unit-videos", headers=adm)
    d = r.json()
    check("一覧は 200・ready・61 行", r.status_code == 200 and d.get("ready") is True and len(d.get("items") or []) == 61, d)
    row2 = next(x for x in d["items"] if x["key"] == "tg-exp-02")
    check("第2回の行に出すドリルの単元 (時制)", row2["drill_units"] == ["時制"], row2)
    row1 = next(x for x in d["items"] if x["key"] == "tg-exp-01")
    check("第1回 文型はドリルの単元なし", row1["drill_units"] == [], row1)
    r = client.post("/api/admin/unit-videos/bulk", json={"items": [{"key": "tg-exp-02", "youtube_url": "https://youtu.be/AAAAAAAAAAA"}]})
    check("認証なしの保存は 401/403", r.status_code in (401, 403), r.status_code)
    r = client.post("/api/admin/unit-videos/bulk", headers=adm, json={"items": [
        {"key": "tg-exp-02", "youtube_url": "https://youtu.be/AAAAAAAAAAA"}, {"key": "tg-zzz", "youtube_url": "https://youtu.be/BBBBBBBBBBB"}]})
    check("不正な鍵が混ざると 400・何も書かない", r.status_code == 400 and link_count(mod) == 0, (r.status_code, link_count(mod)))
    r = client.post("/api/admin/unit-videos/bulk", headers=adm, json={"items": [
        {"key": "tg-exp-02", "youtube_url": "https://youtu.be/AAAAAAAAAAA"}, {"key": "tg-exp-03", "youtube_url": "not a url"}]})
    check("不正な URL が混ざると 400・何も書かない", r.status_code == 400 and link_count(mod) == 0, (r.status_code, link_count(mod)))
    r = client.post("/api/admin/unit-videos/bulk", headers=adm, json={"items": [
        {"key": "tg-exp-02", "youtube_url": "https://youtu.be/AAAAAAAAAAA"},
        {"key": "tg-exp-03", "youtube_url": "https://www.youtube.com/watch?v=CCCCCCCCCCC"},
        {"key": "tg-prc-02-a", "youtube_url": "DDDDDDDDDDD"},
        {"key": "tg-exp-10", "youtube_url": "https://youtu.be/EEEEEEEEEEE"},
        {"key": "tg-exp-11", "youtube_url": "https://youtu.be/FFFFFFFFFFF"},
        {"key": "tg-exp-05", "youtube_url": "https://youtu.be/GGGGGGGGGGG"},
        {"key": "tg-exp-19", "youtube_url": "https://youtu.be/HHHHHHHHHHH"},
    ]})
    check("まとめて保存 (URL・watch?v=・ID だけ)", r.status_code == 200 and r.json().get("set") == 7, r.text)
    r = client.put("/api/admin/unit-videos/tg-exp-05", headers=adm, json={"youtube_url": "https://youtu.be/IIIIIIIIIII"})
    check("1 本ずつ上書き (PUT)", r.status_code == 200 and mod._tg_link_map()["tg-exp-05"]["youtube_id"] == "IIIIIIIIIII", r.text)
    r = client.put("/api/admin/unit-videos/tg-nope", headers=adm, json={"youtube_url": "https://youtu.be/IIIIIIIIIII"})
    check("PUT の不正な鍵は 400", r.status_code == 400, r.status_code)
    r = client.post("/api/admin/unit-videos/bulk", headers=adm, json={"items": []})
    check("0 件の bulk は 400", r.status_code == 400, r.status_code)
    r = client.put("/api/admin/unit-videos/tg-exp-05", headers=adm, json={"youtube_url": "https://youtu.be/IIIIIIIIIII"})
    check("同じ ID で上書きしても 200 (行は 1 つ)", r.status_code == 200 and link_count(mod) == 7, (r.status_code, link_count(mod)))

    print("\n[4] 通塾生アプリ GET /api/student/class/unit-videos")
    sid = make_student(mod, "単元動画 A", "unitvid-a@example.org", ai_disabled=1)   # 塾生アプリのみ枠 (AIなし)
    tok = {"Authorization": "Bearer " + student_token(mod, sid)}
    r = client.get("/api/student/class/unit-videos")
    check("トークンなしは 401", r.status_code == 401, r.status_code)
    r = client.get("/api/student/class/unit-videos", headers=tok)
    check("弱点が無ければ items=[] (AIなし枠でも 200)", r.status_code == 200 and r.json().get("items") == [], r.text)
    add_weak(mod, sid, "english", "時制", 0.40, 10)            # 低い・URL あり (exp-02, exp-03, prc-02-a)
    add_weak(mod, sid, "english", "関係詞", 0.90, 3)           # 高い → 出さない
    add_weak(mod, sid, "english", "比較", 0.0, 1)              # 採点 1 問 → まだ測れていない
    add_weak(mod, sid, "english", "語法・イディオム", 0.20, 6)  # 合う回が無い
    add_weak(mod, sid, "english", "助動詞", 0.30, 5)           # URL が無い → 出さない
    add_weak(mod, sid, "english", "英文法 受動態", 0.70, 4)    # 接頭辞つき → 受動態 (exp-05)
    add_weak(mod, sid, "english", "受動態", 0.75, 8)           # 同じ単元 → 1 回だけ
    add_weak(mod, sid, "english", "強調・省略", 0.60, 3)       # 第19回 (exp-19)
    add_weak(mod, sid, "english", "長文読解", 0.10, 9)         # 文法の単元でない
    add_weak(mod, sid, "chugaku", "時制", 0.10, 9)             # 中学は出さない
    r = client.get("/api/student/class/unit-videos", headers=tok)
    items = r.json().get("items") or []
    units = [x["unit"] for x in items]
    check("正解率の低い順に 時制 → 強調・省略 → 受動態 (最大 3 単元)", units == ["時制", "強調・省略", "受動態"], units)
    t = items[0] if items else {}
    check("時制は 説明動画 第2回 → 第3回 → 解説 第2回前半 の順", [v["key"] for v in t.get("videos", [])] == ["tg-exp-02", "tg-exp-03", "tg-prc-02-a"], t)
    check("正解率と問数", t.get("accuracy_pct") == 40 and t.get("attempts") == 10, t)
    check("リンクは youtu.be/ID", (t.get("videos") or [{}])[0].get("url") == "https://youtu.be/AAAAAAAAAAA", t)
    check("受動態は PUT で入れた ID", items and items[-1]["videos"][0]["youtube_id"] == "IIIIIIIIIII", items)
    # 同じ回に当たる単元 (否定・倒置 と 強調・省略 → 第19回) は動画を繰り返さない
    sid_c = make_student(mod, "単元動画 C", "unitvid-c@example.org")
    add_weak(mod, sid_c, "english", "否定・倒置", 0.30, 5)
    add_weak(mod, sid_c, "english", "強調・省略", 0.40, 5)
    add_weak(mod, sid_c, "english", "比較", 0.50, 5)
    r = client.get("/api/student/class/unit-videos", headers={"Authorization": "Bearer " + student_token(mod, sid_c)})
    uc = [x["unit"] for x in r.json().get("items") or []]
    check("第19回は 1 回だけ・枠は次の単元 (比較) に回る", uc == ["否定・倒置", "比較"], uc)
    mod._RATE_LIMIT_STORE.clear()
    r = client.get(f"/api/student/weakness-top3?student_id={sid_c}", headers={"Authorization": "Bearer " + student_token(mod, sid_c)})
    byc = {w["topic"]: w for w in (r.json() or {}).get("weaknesses") or []}
    check("TOP3 でも第19回は上の項目だけ", [v["key"] for v in byc.get("否定・倒置", {}).get("unit_videos", [])] == ["tg-exp-19"]
          and byc.get("強調・省略", {}).get("unit_videos") == [], byc)
    # 回数の制限は生徒ごと (IP 単位でない)
    mod._RATE_LIMIT_STORE.clear()
    for _ in range(30):
        client.get("/api/student/class/unit-videos", headers=tok)
    r1 = client.get("/api/student/class/unit-videos", headers=tok)
    r2 = client.get("/api/student/class/unit-videos", headers={"Authorization": "Bearer " + student_token(mod, sid_c)})
    check("31 回目の本人は 429・別の生徒は 200 (同じ IP でも)", r1.status_code == 429 and r2.status_code == 200, (r1.status_code, r2.status_code))
    mod._RATE_LIMIT_STORE.clear()
    # URL を外すと出なくなる
    r = client.put("/api/admin/unit-videos/tg-exp-03", headers=adm, json={"youtube_url": ""})
    check("空の URL で外す", r.status_code == 200 and r.json().get("cleared") == 1 and "tg-exp-03" not in mod._tg_link_map(), r.text)
    r = client.get("/api/student/class/unit-videos", headers=tok)
    t = (r.json().get("items") or [{}])[0]
    check("外した動画は出ない", [v["key"] for v in t.get("videos", [])] == ["tg-exp-02", "tg-prc-02-a"], t)
    # 他の生徒には出ない (本人の弱点だけ)
    sid_b = make_student(mod, "単元動画 B", "unitvid-b@example.org")
    r = client.get("/api/student/class/unit-videos", headers={"Authorization": "Bearer " + student_token(mod, sid_b)})
    check("ほかの生徒の弱点は混ざらない", r.status_code == 200 and r.json().get("items") == [], r.text)

    print("\n[5] mypage の弱点 TOP3")
    add_weak(mod, sid_b, "english", "時制", 0.30, 6)
    add_weak(mod, sid_b, "english", "関係詞", 0.85, 3)
    add_weak(mod, sid_b, "english", "助動詞", 0.50, 4)
    mod._RATE_LIMIT_STORE.clear()
    r = client.get(f"/api/student/weakness-top3?student_id={sid_b}", headers={"Authorization": "Bearer " + student_token(mod, sid_b)})
    ws = (r.json() or {}).get("weaknesses") or []
    by = {w["topic"]: w for w in ws}
    check("TOP3 は 200", r.status_code == 200 and len(ws) == 3, r.text[:300])
    check("時制に unit_videos (説明 第2回・解説 第2回前半)", [v["key"] for v in by.get("時制", {}).get("unit_videos", [])] == ["tg-exp-02", "tg-prc-02-a"], by.get("時制"))
    check("正解率 85% の関係詞には付けない", "unit_videos" not in by.get("関係詞", {}), by.get("関係詞"))
    check("URL の無い助動詞は空のリスト", by.get("助動詞", {}).get("unit_videos") == [], by.get("助動詞"))
    r = client.get(f"/api/student/weakness-top3?student_id={sid_b}&pool=chugaku", headers={"Authorization": "Bearer " + student_token(mod, sid_b)})
    check("中学プールには付けない", all("unit_videos" not in w for w in (r.json() or {}).get("weaknesses") or []), r.text[:200])

    print("\n[6] 画面")
    cls = open(os.path.join(REPO, "class.html"), encoding="utf-8").read()
    mp = open(os.path.join(REPO, "mypage.html"), encoding="utf-8").read()
    ceo = open(os.path.join(REPO, "ceo.html"), encoding="utf-8").read()
    check("class.html: カードの枠・読み込み・API", 'id="unitVideoCard"' in cls and "loadUnitVideoCard();" in cls
          and "/api/student/class/unit-videos" in cls)
    check("class.html: リンクは ID の検査を通して組み立てる", "/^[A-Za-z0-9_-]{11}$/" in cls)
    check("mypage.html: TOP3 に unit_videos の行", "w.unit_videos" in mp and "${unitVideoRow}" in mp)
    check("ceo.html: メニューのボタンと欄", 'data-hub-target="unitVideosSection"' in ceo and 'id="unitVideosSection"' in ceo
          and "/api/admin/unit-videos/bulk" in ceo)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        return 1
    print("✅ PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
