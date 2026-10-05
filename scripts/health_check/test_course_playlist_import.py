#!/usr/bin/env python3
"""📺 月額講座「再生リストから取り込む」(POST /api/admin/course/import・/api/admin/course/playlists) の回帰テスト
(in-process・一時 SQLite・ネットワーク不要)。YouTube は class_recording_assign.http_get を、メールは _course_send_email を差し替える。

  P. 再生リストの保存: URL (&si= 付き) から ID を抜く・空で解除・授業録画の再生リスト / 他講座と同じ再生リストは 409・管理 API は 401
  D. ① 確認 (dry-run): 何も登録しない・メールも送らない・動画 ID は先頭 4 文字だけ・登録済み / 削除済み / 授業録画 / 題名なしを分ける
  A. ② 登録: plan_token が一致するときだけ・タイトルは YouTube の動画名・公開日は今日・講座ごとに 1 人 1 通 (複数本をまとめる)
     お知らせ済みの台帳は動画ごと → あとで「📧 通知」を押しても二重に届かない・1 本だけのときは手登録と同じ件名
  F. 読めなかった講座は「新着 0 本」と言わない・他の講座は登録できる・1 ページ上限超えは登録しない
  T. ① のあとで再生リストが変わったら 1 本も登録しない (メールも送らない)
  N. notify=false はメールなし・あとで「📧 通知」で 1 本ずつ送れる
  L. 同時実行は 409
  C. 授業録画の再生リストに入っている動画 (まだクラスに割り当てていない回も) は取り込まない・その再生リストが読めなければ全講座止める
  S. 削除した動画の台帳は 1 動画 1 行 (同じ講座で 2 本消しても両方残る)
  B. 宛先が多い (合計 16 名以上) ときは 1 本のバックグラウンドで講座順に送る・宛先 0 の講座は「送信中」と言わない
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
import threading
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="courseimport_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "sk_test_dummy_for_course_import", "STRIPE_WEBHOOK_SECRET": "",
        "MONITORING_ENABLED": "0", "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "re_dummy", "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_course_import", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def admin_token(mod, hours=1):
    exp = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)).timestamp())
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), f"admin.{exp}".encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


def yt_page(videos, shown=None, alert=None, alert_type="INFO"):
    """再生リストページ (ytInitialData) を合成する。videos = [(動画 ID, 題名)]。"""
    d = {"contents": {"x": [{"lockupViewModel": {
        "contentType": "LOCKUP_CONTENT_TYPE_VIDEO", "contentId": vid,
        "metadata": {"lockupMetadataViewModel": {"title": {"content": title}}}}} for vid, title in videos]}}
    n = len(videos) if shown is None else shown
    d["header"] = {"t": {"content": f"{n} 本の動画"}} if n else {"e": {"simpleText": "この再生リストには動画がありません"}}
    if alert:
        d["alerts"] = [{"alertRenderer": {"type": alert_type, "text": {"runs": [{"text": alert}]}}}]
    return f'<html><script>var ytInitialData = {json.dumps(d, ensure_ascii=False)};</script></html>'


def main():
    mod = load_main()
    import class_recording_assign as cra
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    print("📺 月額講座 再生リストから取り込む 回帰テスト")

    # ---- 偽 YouTube / 偽メール ----
    YT = {}          # 再生リスト ID → ページ本文 (None なら取得失敗)
    FETCHED = []

    def fake_http_get(url, timeout=30):
        pid = url.split("list=", 1)[1] if "list=" in url else ""
        FETCHED.append(pid)
        body = YT.get(pid)
        return (body, None) if body is not None else (None, "YouTube に接続できない — ネット接続を確認してもう一度実行してください")
    cra.http_get = fake_http_get
    MAILS = []
    mod._course_send_email = lambda to, subject, body: (MAILS.append({"to": to, "subject": subject, "body": body, "thread": threading.current_thread().name}) or {"sent": True, "resend_id": "re_x"})
    mod._email_rate_limit = lambda *a, **k: None
    ADMIN = {"Authorization": "Bearer " + admin_token(mod)}
    today = mod._course_today_jst()

    # 受講者: A は解釈+文法、B は解釈だけ、C は文法だけ、D は解約済み (解釈)
    mod._course_upsert_member("a@example.invalid", ["kaishaku", "bunpo"], "cus_a", "テスト 一郎")
    mod._course_upsert_member("b@example.invalid", ["kaishaku"], "cus_b", "")
    mod._course_upsert_member("c@example.invalid", ["bunpo"], "cus_c", "テスト 三郎")
    mod._course_upsert_member("d@example.invalid", ["kaishaku"], "cus_d", "")
    conn = mod.db(); c = conn.cursor(); c.execute("UPDATE course_members SET status = 'canceled' WHERE email = 'd@example.invalid'"); conn.commit(); conn.close()

    def imp(**body):
        # 取り込みは IP あたり 10 回/分 (R1 で確かめる)。テストは続けて押すので毎回数え直す
        for k in [k for k in list(mod._RATE_LIMIT_STORE) if isinstance(k, tuple) and k[-1] == "course_import"]:
            mod._RATE_LIMIT_STORE.pop(k, None)
        return client.post("/api/admin/course/import", headers=ADMIN, json=body)

    def videos(course=None):
        conn = mod.db(); c = conn.cursor()
        c.execute("SELECT * FROM course_videos ORDER BY id")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return [r for r in rows if course is None or r["course_key"] == course]

    # ---- P. 再生リストの保存 ----
    check("P0. 管理 API は Bearer 無しで 401",
          client.get("/api/admin/course/playlists").status_code == 401
          and client.post("/api/admin/course/playlists", json={"course_key": "kaishaku", "playlist": "PLkaishaku01"}).status_code == 401
          and client.post("/api/admin/course/import", json={}).status_code == 401)
    g0 = client.get("/api/admin/course/playlists", headers=ADMIN).json()
    check("P1. 最初は 3 講座とも未設定", [p["playlist_id"] for p in g0["playlists"]] == ["", "", ""] and [p["course_key"] for p in g0["playlists"]] == ["kaishaku", "bunpo", "kyotsu"], g0)
    d0 = imp()
    check("P2. 未設定で ① → 「設定されていません」・何も読まない", d0.status_code == 200 and "設定されていません" in d0.json()["message"] and not FETCHED and d0.json()["planned_total"] == 0, d0.text)
    s1 = client.post("/api/admin/course/playlists", headers=ADMIN, json={"course_key": "kaishaku", "playlist": "https://youtube.com/playlist?list=PLkaishaku01&si=abcDEF"})
    s2 = client.post("/api/admin/course/playlists", headers=ADMIN, json={"course_key": "bunpo", "playlist": "https://www.youtube.com/watch?v=AAAAAAAAAAA&list=PLbunpo0002"})
    check("P3. 共有 URL (&si= 付き)・動画 URL の list= から ID を抜いて保存", s1.status_code == 200 and s1.json()["playlist_id"] == "PLkaishaku01" and s2.status_code == 200 and s2.json()["playlist_id"] == "PLbunpo0002", (s1.text, s2.text))
    bad = client.post("/api/admin/course/playlists", headers=ADMIN, json={"course_key": "kyotsu", "playlist": "https://youtu.be/AAAAAAAAAAA"})
    badkey = client.post("/api/admin/course/playlists", headers=ADMIN, json={"course_key": "math", "playlist": "PLx"})
    check("P4. 再生リストでない URL・不正な講座は 400", bad.status_code == 400 and badkey.status_code == 400, (bad.text, badkey.text))
    dup = client.post("/api/admin/course/playlists", headers=ADMIN, json={"course_key": "kyotsu", "playlist": "PLkaishaku01"})
    check("P5. 他の講座と同じ再生リストは 409", dup.status_code == 409 and "英文解釈講座" in dup.json().get("detail", ""), dup.text)
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO admin_youtube_playlists (playlist_id, name, grp, sort_order) VALUES (?,?,?,?)", ("PLclassMon1", "月曜1限", "", 0))
    conn.commit(); conn.close()
    YT["PLclassMon1"] = yt_page([("CLS00000002", "10/5")])     # まだクラスに割り当てていない授業録画
    cls = client.post("/api/admin/course/playlists", headers=ADMIN, json={"course_key": "kyotsu", "playlist": "PLclassMon1"})
    check("P6. 授業録画の再生リストは講座に使えない (409)", cls.status_code == 409 and "授業録画" in cls.json().get("detail", ""), cls.text)
    g1 = client.get("/api/admin/course/playlists", headers=ADMIN).json()
    check("P7. 保存した ID が読める (kyotsu は未設定のまま)", {p["course_key"]: p["playlist_id"] for p in g1["playlists"]} == {"kaishaku": "PLkaishaku01", "bunpo": "PLbunpo0002", "kyotsu": ""}, g1)
    YT["PLclassTue2"] = yt_page([])
    check("P8. 授業録画の再生リスト画面の保存も同じ抜き出し (URL を貼れる)",
          client.post("/api/admin/youtube-playlists", headers=ADMIN, json={"id": "https://www.youtube.com/playlist?list=PLclassTue2&si=x", "name": "火曜2限"}).json().get("playlist_id") == "PLclassTue2"
          and client.post("/api/admin/youtube-playlists", headers=ADMIN, json={"id": "https://youtu.be/AAAAAAAAAAA", "name": "x"}).status_code == 400)

    # ---- D. ① 確認 ----
    # 解釈: 4 本 (1 本は手登録済み・1 本は授業録画として登録済み・1 本は題名なし) / 文法: 2 本
    client.post("/api/admin/course/videos", headers=ADMIN, json={"course_key": "kaishaku", "title": "手で登録した回", "youtube_url": "https://youtu.be/KAI00000001", "notify": False})
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO class_recordings (session_id, title, video_url, provider, is_published, created_at) VALUES (NULL, '8/17', 'https://youtu.be/CLS00000001', 'youtube', 1, ?)", (mod._utc_naive_iso(),))
    conn.commit(); conn.close()
    YT["PLkaishaku01"] = yt_page([("KAI00000001", "手で登録した回"), ("KAI00000002", "第2回 SVOC の見抜き方"), ("CLS00000001", "8/17"),
                                  ("KAI00000003", "第3回 関係詞"), ("KAI00000004", "")])
    YT["PLbunpo0002"] = yt_page([("BUN00000001", "第1回 時制"), ("BUN00000002", "第2回 助動詞")])
    MAILS.clear(); FETCHED.clear()
    n_before = len(videos())
    d1 = imp()
    j1 = d1.json() if d1.status_code == 200 else {}
    rows = {r["course_key"]: r for r in j1.get("courses", [])}
    check("D1. ① は 200・dry-run・何も登録しない・メールも送らない", d1.status_code == 200 and j1["mode"] == "dry-run" and len(videos()) == n_before and not MAILS, d1.text[:300])
    check("D2. 解釈: 再生リスト 5 本・登録済み 1・新しく 2 本 (再生リストの順)", rows.get("kaishaku", {}).get("total") == 5 and rows["kaishaku"]["already"] == 1
          and [v["title"] for v in rows["kaishaku"]["new"]] == ["第2回 SVOC の見抜き方", "第3回 関係詞"], rows.get("kaishaku"))
    sk = rows.get("kaishaku", {}).get("skipped", [])
    check("D3. 授業録画として登録済みの動画・題名なしの動画は取り込まず理由を出す", len(sk) == 2 and "授業録画" in sk[0]["reason"] and "動画名を読めません" in sk[1]["reason"], sk)
    check("D4. 文法 2 本・共通テストは未設定・受講者数 (解約は数えない)", [v["title"] for v in rows.get("bunpo", {}).get("new", [])] == ["第1回 時制", "第2回 助動詞"]
          and rows.get("kyotsu", {}).get("status") == "unset" and rows["kaishaku"]["members"] == 2 and rows["bunpo"]["members"] == 2, rows)
    check("D5. 応答に動画 ID は先頭 4 文字しか出ない", j1.get("planned_total") == 4 and "KAI00000002" not in d1.text and "BUN00000001" not in d1.text and rows["kaishaku"]["new"][0]["video"] == "KAI0…", d1.text[:300])
    check("D6. plan_token が付く・「4 本を登録できます」", bool(j1.get("plan_token")) and "4 本を登録できます" in j1.get("message", ""), j1.get("message"))

    # ---- T. ① のあとで再生リストが変わったら登録しない ----
    YT["PLbunpo0002"] = yt_page([("BUN00000001", "第1回 時制"), ("BUN00000002", "第2回 助動詞"), ("BUN00000003", "第3回 仮定法")])
    t1 = imp(apply=True, plan_token=j1["plan_token"])
    check("T1. 再生リストが変わった → refused・1 本も登録しない・メールなし", t1.status_code == 200 and t1.json()["refused"] and t1.json()["applied"] == 0 and len(videos()) == n_before and not MAILS, t1.text[:300])
    t2 = imp(apply=True)
    check("T2. plan_token なしの apply も登録しない", t2.status_code == 200 and t2.json()["refused"] and len(videos()) == n_before, t2.text[:200])
    YT["PLbunpo0002"] = yt_page([("BUN00000001", "第1回 時制"), ("BUN00000002", "第2回 助動詞")])

    # ---- A. ② 登録 ----
    d2 = imp().json()
    check("A0. 同じ再生リストなら plan_token は同じ", d2["plan_token"] == j1["plan_token"], (d2["plan_token"], j1["plan_token"]))
    a1 = imp(apply=True, plan_token=d2["plan_token"])
    ja = a1.json() if a1.status_code == 200 else {}
    kai = videos("kaishaku"); bun = videos("bunpo")
    check("A1. 4 本登録・各 1 件の確認済み", a1.status_code == 200 and ja["applied"] == 4 and ja["verified"] is True and "4 本を登録しました" in ja["message"], a1.text[:400])
    check("A2. タイトルは YouTube の動画名・公開日は今日・公開・ひとことは空",
          [v["title"] for v in kai] == ["手で登録した回", "第2回 SVOC の見抜き方", "第3回 関係詞"] and [v["title"] for v in bun] == ["第1回 時制", "第2回 助動詞"]
          and all(v["publish_date"] == today and v["is_published"] == 1 and (v["note"] or "") == "" for v in kai[1:] + bun), (kai, bun))
    by_to = {}
    for m in MAILS:
        by_to.setdefault(m["to"], []).append(m)
    check("A3. 講座ごとに 1 人 1 通 (A は解釈と文法で 2 通・B は 1 通・C は 1 通・解約した D には送らない)",
          {k: len(v) for k, v in by_to.items()} == {"a@example.invalid": 2, "b@example.invalid": 1, "c@example.invalid": 1}, {k: [m["subject"] for m in v] for k, v in by_to.items()})
    mb = by_to.get("b@example.invalid", [{}])[0]
    check("A4. まとめた 1 通: 件名「【英文解釈講座】新しい動画を 2 本追加しました」・本文に 2 本の題名と視聴ページ・動画 URL は無い",
          mb.get("subject") == "【英文解釈講座】新しい動画を 2 本追加しました" and "・第2回 SVOC の見抜き方\n・第3回 関係詞\n" in mb.get("body", "")
          and "course-videos.html" in mb.get("body", "") and "youtu" not in mb.get("body", "") and mb.get("body", "").startswith("受講者の皆さま"), mb)
    check("A5. 名前のある受講者は「様」で始まる", any(m["body"].startswith("テスト 一郎 様") for m in by_to.get("a@example.invalid", [])), by_to.get("a@example.invalid"))
    check("A6. 応答に講座ごとの送信結果", ja.get("notified", {}).get("kaishaku") == {"sent": 2, "failed": 0, "recipients": 2} and ja["notified"].get("bunpo") == {"sent": 2, "failed": 0, "recipients": 2}, ja.get("notified"))
    lst = {v["title"]: v for v in client.get("/api/admin/course/videos", headers=ADMIN).json()["videos"]}
    check("A7. 動画ごとの通知 累計 (解釈の各動画 2・文法の各動画 2)", lst["第2回 SVOC の見抜き方"]["notified_count"] == 2 and lst["第3回 関係詞"]["notified_count"] == 2 and lst["第1回 時制"]["notified_count"] == 2, {k: v["notified_count"] for k, v in lst.items()})
    MAILS.clear()
    rn = client.post(f"/api/admin/course/videos/{lst['第3回 関係詞']['id']}/notify", headers=ADMIN)
    check("A8. あとで「📧 通知」を押しても、まとめて受け取った人には届かない (0 通)", rn.status_code == 200 and rn.json()["notified"]["recipients"] == 0 and not MAILS, rn.text)
    sess_me = None
    d3 = imp().json()
    check("A9. もう一度 ① → 新しい動画はありません", d3["planned_total"] == 0 and d3["message"].startswith("新しい動画はありません"), d3["message"])
    a2 = imp(apply=True, plan_token=d3["plan_token"])
    check("A10. 新着 0 本で ② を押しても何も起きない", a2.status_code == 200 and a2.json()["applied"] == 0 and not MAILS and len(videos()) == n_before + 4, a2.text[:200])

    # 1 本だけのときは手登録と同じ件名
    YT["PLbunpo0002"] = yt_page([("BUN00000001", "第1回 時制"), ("BUN00000002", "第2回 助動詞"), ("BUN00000003", "第3回 仮定法")])
    MAILS.clear()
    d4 = imp().json()
    a4 = imp(apply=True, plan_token=d4["plan_token"]).json()
    check("A11. 1 本だけなら件名は手登録と同じ「【英文法講座】新しい動画: 第3回 仮定法」",
          a4["applied"] == 1 and len(MAILS) == 2 and all(m["subject"] == "【英文法講座】新しい動画: 第3回 仮定法" for m in MAILS)
          and all("■ 今回の動画\n第3回 仮定法\n" in m["body"] for m in MAILS), [m["subject"] for m in MAILS])

    # ---- 削除した動画は生き返らせない ----
    vid_del = [v for v in videos("bunpo") if v["title"] == "第3回 仮定法"][0]["id"]
    client.delete(f"/api/admin/course/videos/{vid_del}", headers=ADMIN)
    d5 = imp().json()
    r5 = {r["course_key"]: r for r in d5["courses"]}["bunpo"]
    check("A12. CEO 画面で削除した動画は、再生リストに残っていても取り込まない (理由つき)",
          d5["planned_total"] == 0 and len(r5["skipped"]) == 1 and "削除した動画" in r5["skipped"][0]["reason"], r5)
    rm = client.post("/api/admin/course/videos", headers=ADMIN, json={"course_key": "bunpo", "title": "第3回 仮定法 (撮り直し)", "youtube_url": "https://youtu.be/BUN00000003", "notify": False})
    d5b = imp().json()
    check("A13. 削除した動画も上の欄から手で登録し直せる・その後は「登録済み」に数える", rm.status_code == 200 and {r["course_key"]: r for r in d5b["courses"]}["bunpo"]["already"] == 3 and d5b["planned_total"] == 0, (rm.text, d5b["courses"]))

    # ---- N. notify=false ----
    YT["PLkaishaku01"] = yt_page([("KAI00000001", "手で登録した回"), ("KAI00000002", "第2回 SVOC の見抜き方"), ("CLS00000001", "8/17"),
                                  ("KAI00000003", "第3回 関係詞"), ("KAI00000004", ""), ("KAI00000005", "第4回 分詞構文")])
    MAILS.clear()
    d6 = imp().json()
    a6 = imp(apply=True, plan_token=d6["plan_token"], notify=False).json()
    v6 = [v for v in client.get("/api/admin/course/videos", headers=ADMIN).json()["videos"] if v["title"] == "第4回 分詞構文"]
    check("N1. notify=false: 登録するがメールは送らない・「未通知」のまま", a6["applied"] == 1 and not MAILS and a6["notified"] == {} and v6 and v6[0]["notified_at"] is None and "送っていません" in a6["message"], a6)
    rn6 = client.post(f"/api/admin/course/videos/{v6[0]['id']}/notify", headers=ADMIN) if v6 else None
    check("N2. あとで「📧 通知」で送れる (受講者 2 名)", rn6 is not None and rn6.json()["notified"]["sent"] == 2 and len(MAILS) == 2, rn6.text if rn6 is not None else None)

    # ---- F. 読めなかった講座 ----
    client.post("/api/admin/course/playlists", headers=ADMIN, json={"course_key": "kyotsu", "playlist": "PLkyotsu003"})
    YT["PLkyotsu003"] = None     # 取得失敗
    YT["PLkaishaku01"] = yt_page([("KAI00000001", "手で登録した回"), ("KAI00000006", "第5回 倒置")])
    MAILS.clear()
    d7 = imp().json()
    r7 = {r["course_key"]: r for r in d7["courses"]}
    check("F1. 取得に失敗した講座は error (「新着 0 本」と言わない)・他の講座は登録できる",
          r7["kyotsu"]["status"] == "error" and "読めませんでした" in r7["kyotsu"]["error"] and r7["kaishaku"]["status"] == "ok" and d7["planned_total"] == 1
          and "共通テスト対策講座は取り込みません" in d7["message"], (d7["message"], r7["kyotsu"]))
    a7 = imp(apply=True, plan_token=d7["plan_token"]).json()
    check("F2. ② は読めた講座だけ登録し、取り込まなかった講座を伝える", a7["applied"] == 1 and "共通テスト対策講座は取り込みません" in a7["message"], a7["message"])
    YT["PLkyotsu003"] = yt_page([("KYO%08d" % i, "回 %d" % i) for i in range(100)], shown=130)
    d8 = imp().json()
    r8 = {r["course_key"]: r for r in d8["courses"]}["kyotsu"]
    check("F3. 1 ページ上限 (100 本) を超えた再生リストは登録しない", r8["status"] == "error" and "1ページ上限" in r8["error"] and d8["planned_total"] == 0, r8)
    deleted = '<script>var ytInitialData = ' + json.dumps({"contents": {"x": []}, "alerts": [{"alertRenderer": {"type": "ERROR", "text": {"runs": [{"text": "この再生リストは存在しません。"}]}}}]}, ensure_ascii=False) + ';</script>'
    YT["PLkyotsu003"] = deleted
    d9 = imp().json()
    r9 = {r["course_key"]: r for r in d9["courses"]}["kyotsu"]
    check("F4. 削除された再生リスト (YouTube のエラー表示) は error で、0 本と言わない", r9["status"] == "error" and "存在しません" in r9["error"], r9)
    YT["PLkyotsu003"] = yt_page([])
    d10 = imp().json()
    r10 = {r["course_key"]: r for r in d10["courses"]}["kyotsu"]
    check("F5. 本当に空の再生リストは ok・0 本", r10["status"] == "ok" and r10["total"] == 0 and d10["message"].startswith("新しい動画はありません"), (r10, d10["message"]))
    # 授業録画の再生リストに後から入れられた講座の再生リスト
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO admin_youtube_playlists (playlist_id, name, grp, sort_order) VALUES (?,?,?,?)", ("PLkyotsu003", "以前の再生リスト", "", 9))
    conn.commit(); conn.close()
    d11 = imp().json()
    r11 = {r["course_key"]: r for r in d11["courses"]}["kyotsu"]
    check("F6. 授業録画の再生リストにも登録された再生リストは取り込まない (見出しは「読めなかった」と言わない)",
          r11["status"] == "error" and "授業録画" in r11["error"] and "共通テスト対策講座は取り込みません" in d11["message"] and "読めな" not in d11["message"], (r11, d11["message"]))
    client.post("/api/admin/course/playlists", headers=ADMIN, json={"course_key": "kyotsu", "playlist": ""})
    check("F7. 空で保存すると設定を外せる", {p["course_key"]: p["playlist_id"] for p in client.get("/api/admin/course/playlists", headers=ADMIN).json()["playlists"]}["kyotsu"] == "")

    # ---- L. 同時実行 ----
    mod._COURSE_IMPORT_LOCK.acquire()
    try:
        lk = imp()
    finally:
        mod._COURSE_IMPORT_LOCK.release()
    check("L1. 取り込みの実行中にもう一度押すと 409", lk.status_code == 409, lk.text)

    # ---- 計画の純関数: 他の講座にも登録済みの動画は印をつけて登録する ----
    p = mod._course_import_plan({"kaishaku": "PLa", "bunpo": "PLb"},
                                {"kaishaku": ([("SAME0000001", "共通回")], None, None), "bunpo": ([("SAME0000001", "共通回")], None, None)},
                                {"kaishaku": set(), "bunpo": {"SAME0000001"}, "kyotsu": set()}, {}, set(), set())
    pr = {r["course_key"]: r for r in p["rows"]}
    check("U1. 他の講座に登録済みの動画は「〜にも登録済み」と出して登録する", pr["kaishaku"]["new"][0]["also_in"] == ["英文法講座"] and pr["bunpo"]["already"] == 1 and len(p["planned"]) == 1, pr)
    ok_items = ([("SAME0000002", "共通回 2")], None, None)
    p2 = mod._course_import_plan({"kaishaku": "PLsame", "bunpo": "PLsame"}, {"kaishaku": ok_items, "bunpo": ok_items}, {}, {}, set(), set())
    check("U2. 同じ再生リストが 2 講座に設定されていたら両方 error (中身が読めていても)",
          all(r["status"] == "error" and "同じ再生リスト" in (r["error"] or "") for r in p2["rows"][:2]) and not p2["planned"], p2["rows"])

    # ---- R. 押しすぎ ----
    imp()
    codes = [client.post("/api/admin/course/import", headers=ADMIN, json={}).status_code for _ in range(10)]
    check("R1. 取り込みは 1 分に 10 回まで (11 回目は 429)", codes[:9] == [200] * 9 and codes[9] == 429, codes)

    # ---- B. 宛先が多いときはバックグラウンド ----
    for i in range(20):
        mod._course_upsert_member(f"bulk{i}@example.invalid", ["kaishaku"], f"cus_b{i}", "")
    YT["PLkaishaku01"] = yt_page([("KAI00000001", "手で登録した回"), ("KAI00000007", "第6回 比較")])
    MAILS.clear()
    d12 = imp().json()
    a12 = imp(apply=True, plan_token=d12["plan_token"]).json()
    for _ in range(80):
        if len(MAILS) >= 22:
            break
        time.sleep(0.05)
    nk = a12.get("notified", {}).get("kaishaku", {})
    check("B1. 宛先 16 名以上はバックグラウンドで送り queued を返す (全 22 名に 1 通ずつ)", nk.get("background") and nk.get("queued") == 22 and len(MAILS) == 22 and len({m["to"] for m in MAILS}) == 22, (nk, len(MAILS)))

    # ---- B2. 講座ごとには 15 名以下でも、合計が 16 名以上ならバックグラウンド (1 本の流れで講座順に)・宛先 0 の講座 ----
    conn = mod.db(); c = conn.cursor(); c.execute("UPDATE course_members SET status = 'canceled', courses = '[]' WHERE email LIKE 'bulk%'"); conn.commit(); conn.close()
    for i in range(10):
        mod._course_upsert_member(f"kai{i}@example.invalid", ["kaishaku"], f"cus_k{i}", "")
    for i in range(6):
        mod._course_upsert_member(f"bun{i}@example.invalid", ["bunpo"], f"cus_n{i}", "")
    client.post("/api/admin/course/playlists", headers=ADMIN, json={"course_key": "kyotsu", "playlist": "PLkyotsu004"})
    YT["PLkaishaku01"] = yt_page([("KAI00000001", "手で登録した回"), ("KAI00000008", "第7回 省略")])
    YT["PLbunpo0002"] = yt_page([("BUN00000001", "第1回 時制"), ("BUN00000004", "第4回 不定詞")])
    YT["PLkyotsu004"] = yt_page([("KYO00000001", "共テ 第1回")])
    MAILS.clear()
    d13 = imp().json()
    a13 = imp(apply=True, plan_token=d13["plan_token"]).json()
    n13 = a13.get("notified", {})
    for _ in range(120):
        if len(MAILS) >= 20:
            break
        time.sleep(0.05)
    time.sleep(0.1)
    check("B2. 合計 20 名 (解釈 12・文法 8) → 両講座ともバックグラウンド・宛先どおりの通数",
          a13.get("applied") == 3 and n13.get("kaishaku", {}).get("background") and n13["kaishaku"].get("queued") == 12
          and n13.get("bunpo", {}).get("background") and n13["bunpo"].get("queued") == 8 and len(MAILS) == 20, (n13, len(MAILS)))
    check("B3. 送信は 1 本のスレッドで講座順 (講座ごとに並行して送らない)",
          len({m["thread"] for m in MAILS}) == 1 and [m["subject"].split("】")[0] for m in MAILS] == ["【英文解釈講座"] * 12 + ["【英文法講座"] * 8, [(m["thread"], m["subject"][:8]) for m in MAILS][:3])
    check("B4. 受講者 0 名の講座は「送信中」にしない (recipients 0)", n13.get("kyotsu") == {"sent": 0, "failed": 0, "recipients": 0}, n13.get("kyotsu"))
    check("B5. ② の画面用に講座ごとの実際の登録数 (registered)", {r["course_key"]: r.get("registered") for r in a13["courses"]} == {"kaishaku": 1, "bunpo": 1, "kyotsu": 1}, a13["courses"])

    # ---- C. 授業録画の再生リストに入っている動画 ----
    YT["PLkaishaku01"] = yt_page([("KAI00000001", "手で登録した回"), ("CLS00000002", "10/5"), ("KAI00000009", "第8回 強調構文")])
    d14 = imp().json()
    r14 = {r["course_key"]: r for r in d14["courses"]}["kaishaku"]
    check("C1. 授業録画の再生リスト (月曜1限) に入っている動画は、クラス未割り当てでも取り込まない (理由に再生リスト名)",
          [v["title"] for v in r14["new"]] == ["第8回 強調構文"] and len(r14["skipped"]) == 1 and "月曜1限" in r14["skipped"][0]["reason"], r14)
    YT["PLclassMon1"] = None
    d15 = imp().json()
    check("C2. 授業録画の再生リストが読めないときは、全講座 1 本も取り込まない",
          d15["planned_total"] == 0 and all(r["status"] == "error" and "授業録画の再生リスト" in r["error"] for r in d15["courses"] if r["status"] != "unset"), d15["courses"])
    YT["PLclassMon1"] = yt_page([("CLS00000002", "10/5")])
    # 授業録画の再生リストが 100 本を超えた: 理由と直し方を出す (「少し待って」だけにしない)
    YT["PLclassMon1"] = yt_page([("CLM%08d" % i, "回 %d" % i) for i in range(100)], shown=130)
    d15b = imp().json()
    e15b = [r["error"] for r in d15b["courses"] if r["status"] == "error"]
    check("C2b. 100 本を超えた授業録画の再生リスト → 理由 (1ページ上限) と「分けて」を出し、全講座止める",
          d15b["planned_total"] == 0 and e15b and all("1ページ上限" in e and "分けてください" in e and "月曜1限" in e for e in e15b), e15b[:1])
    YT["PLclassMon1"] = yt_page([("CLS00000002", "10/5")])
    # 講座 (共通テスト) の再生リストが後から授業録画の再生リスト (水曜1限) にもされた: その講座は止め、中身は他の講座から守る
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO admin_youtube_playlists (playlist_id, name, grp, sort_order) VALUES (?,?,?,?)", ("PLkyotsu004", "水曜1限", "", 10))
    conn.commit(); conn.close()
    YT["PLkyotsu004"] = yt_page([("KYO00000001", "共テ 第1回"), ("CLS00000003", "10/7")])
    YT["PLkaishaku01"] = yt_page([("KAI00000001", "手で登録した回"), ("CLS00000003", "10/7"), ("KAI00000009", "第8回 強調構文")])
    d15c = imp().json()
    r15c = {r["course_key"]: r for r in d15c["courses"]}
    check("C3. 講座と授業録画の両方に登録された再生リスト: その講座は error・中の授業録画は他の講座でも取り込まない",
          r15c["kyotsu"]["status"] == "error" and [v["title"] for v in r15c["kaishaku"]["new"]] == ["第8回 強調構文"]
          and any("水曜1限" in x["reason"] for x in r15c["kaishaku"]["skipped"]), (r15c["kyotsu"]["error"], r15c["kaishaku"]))
    conn = mod.db(); c = conn.cursor(); c.execute("DELETE FROM admin_youtube_playlists WHERE playlist_id = 'PLkyotsu004'"); conn.commit(); conn.close()

    # ---- S. 削除の台帳は 1 動画 1 行 ----
    vs = [v for v in videos("bunpo") if v["title"] in ("第1回 時制", "第4回 不定詞")]
    for v in vs:
        client.delete(f"/api/admin/course/videos/{v['id']}", headers=ADMIN)
    conn = mod.db(); c = conn.cursor(); c.execute("SELECT key FROM kv_settings WHERE key LIKE 'course_import_skip:bunpo:%'"); keys = sorted(r["key"] for r in c.fetchall()); conn.close()
    d16 = imp().json()
    r16 = {r["course_key"]: r for r in d16["courses"]}["bunpo"]
    check("S1. 同じ講座で 2 本消すと台帳に 2 行・どちらも取り込まない",
          len([k for k in keys if k.endswith(("BUN00000001", "BUN00000004"))]) == 2 and not r16["new"] and len(r16["skipped"]) == 2, (keys, r16))

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 件失敗: {FAILURES}")
        sys.exit(1)
    print("✅ 全件 OK")


if __name__ == "__main__":
    main()
