#!/usr/bin/env python3
"""🎬 授業録画の自動割り当て — 毎朝 7 時の自動実行 (2026-10-08 塾長決定「毎日自動にしたい」) の回帰テスト。

ボタン (POST /api/admin/class-recordings/auto-assign) の性質は test_auto_assign_api.py が見る。
こちらは中身を切り出した _class_rec_auto_assign_run と、毎朝の実行 (_class_rec_auto_assign_daily /
_class_rec_auto_assign_scheduler) の性質を固定する:

  1. 定期実行は dry_run=False・allow_partial=True・source="scheduled" で本体を呼ぶ。scheduler は to_thread 経由で呼び、
     busy なら 10 分後、一時的な失敗 (retry) なら 30 分後に最大 2 回やり直す (最後の回だけ final_attempt=True)。
     起動時の登録は CRON_SECRET と CLASS_REC_AUTO_ASSIGN_ENABLED の両方が要る。env は 0/false/off/no だけが無効
  2. 同じ日に 2 回走らない (外側の確認・錠の中の確認の両方)
  3. 2 回目の実行で二重登録しない / 取得している間に別の登録が入っても二重にしない (書く直前の読み直し)
  4. 排他: 同じプロセスの並行実行は片方が諦める (ボタン 409・定期 busy)。別プロセスの錠 (advisory lock) が
     取れないときも 1 件も書かない
  5. すぐ返ってきた取得失敗を 1 回読み直す (ボタンは時間切れ・接続できないを読み直さない。毎朝の実行は読み直す)
  6. 実行記録とメール本文に動画ID・再生リストIDが入らない (先頭4文字も)。記録は 4000 字で切られても JSON のまま
  7. 何も無い日はメールしない。登録した日・停止の日は送る。保留だけの日は前回送れた通知と中身が違う日だけ
     (同じなら 7 日ごと・送れなかったら翌朝もう一度)。STALE・録画0本も知らせる。全体停止は props.error = 監視の失敗に乗る
  8. 例外・YouTube 全断は最後の回だけ記録・メールし、その記録は「今日は済んだ」に数えない。例外の記録は錠の中で
     「今日もう済んだか」を確かめてから書く。ボタンで直したら回復の記録で監視の失敗を止める
  9. ボタンの応答の形 (キー) と主な値が変わらない

実行:
    python3 scripts/health_check/test_class_rec_daily_assign.py
    # exit 0 = PASS / 1 = FAIL

外部通信は一切しない (http_get とメール送信を差し替える)。DB は一時 SQLite。
"""
import asyncio
import base64
import datetime
import hashlib
import hmac
import importlib.util
import inspect
import json
import os
import sys
import tempfile
import threading

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if detail else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    """一時 SQLite + ダミー env で server/main.py を in-process ロード。"""
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="recdaily_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと **本番 Postgres** に書き込む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "",
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",   # 起動30秒後に本番へ申込 POST を撃つ
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
        "CLASS_REC_AUTO_ASSIGN_ENABLED": "1",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_recdaily", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    mod._CLASS_REC_SCHED_FETCH_RETRY_WAIT = 0   # 毎朝の実行の「接続できない」読み直し前の待ち (試験では待たない)
    return mod


def admin_token(mod, hours=1):
    exp = int((datetime.datetime.now(datetime.timezone.utc)
               + datetime.timedelta(hours=hours)).timestamp())
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), f"admin.{exp}".encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


def recent(weekday, weeks_ago=0):
    """直近の指定曜日 (今日を含まない過去) の date。日付ラベルの検算を通る値を作る。"""
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date()
    back = (today.weekday() - weekday) % 7 or 7
    return today - datetime.timedelta(days=back + 7 * weeks_ago)


def md(d):
    return f"{d.month}/{d.day}"


def yt_page(titles_ids):
    """[(動画ID, タイトル)] → 本物と同じ形の再生リストページ HTML。"""
    data = {
        "contents": {"x": [
            {"lockupViewModel": {
                "contentType": "LOCKUP_CONTENT_TYPE_VIDEO", "contentId": vid,
                "metadata": {"lockupMetadataViewModel": {"title": {"content": t}}},
            }} for vid, t in titles_ids]},
        "header": {"t": {"content": f"{len(titles_ids)} 本の動画"}},
    }
    if not titles_ids:
        data["header"]["e"] = {"simpleText": "この再生リストには動画がありません"}
        data["header"].pop("t")
    return f'<script>var ytInitialData = {json.dumps(data, ensure_ascii=False)};</script>'


def main():
    mod = load_main()
    import class_recording_assign as core
    from fastapi import HTTPException
    from fastapi.testclient import TestClient

    # --- 材料 (★ID は「このリポジトリに書かない」対象なので架空値) -------------------
    PL_MON, PL_TUE, PL_WED, PL_THU = "PLtest_mon", "PLtest_tue", "PLtest_wed", "PLtest_thu"
    MON_D, MON_OLD, MON_2W = recent(0), recent(0, 1), recent(0, 2)
    TUE_D, THU_D = recent(1), recent(3)
    V_MON_NEW, V_MON_OLD = "MonNew00001", "MonOld00001"
    V_TUE_NEW, V_TUE_BAD = "TueNew00001", "TueBad00001"    # TUE_BAD = 日付が読めない (保留)
    V_THU_NEW = "ThuNew00001"
    V_RACE, V_LOCK = "RaceVd00001", "LockVd00001"
    ALL_IDS = [PL_MON, PL_TUE, PL_WED, PL_THU, V_MON_NEW, V_MON_OLD, V_TUE_NEW, V_TUE_BAD,
               V_THU_NEW, V_RACE, V_LOCK]

    mon_items = [(V_MON_OLD, md(MON_OLD)), (V_MON_NEW, md(MON_D))]
    PAGES = {
        PL_MON: lambda: yt_page(mon_items),
        PL_TUE: lambda: yt_page([(V_TUE_NEW, md(TUE_D)), (V_TUE_BAD, "第3回 まとめ")]),
        PL_WED: lambda: None,                 # 取得できない (接続できない = 読み直さない)
        PL_THU: lambda: yt_page([(V_THU_NEW, md(THU_D))]),
    }
    calls = {}
    flaky = {"thu_left": 0}                   # >0 の間、木曜は「解析できないページ」を返す (並行取得で実際に起きる形)
    side_effect = {}                          # pid → 取得中に走らせる処理 (取得中に別の登録が入る形)
    gate = {"ev": None}                       # 取得を止めておく (並行実行の試験)

    def fake_get(url, timeout=30):
        pid = url.split("list=")[-1]
        calls[pid] = calls.get(pid, 0) + 1
        ev = gate["ev"]
        if ev is not None:
            ev.wait(10)
        fn = side_effect.pop(pid, None)
        if fn:
            fn()
        if pid == PL_THU and flaky["thu_left"] > 0:
            flaky["thu_left"] -= 1
            return "<html><body>ちょっと待ってください</body></html>", None
        body = PAGES.get(pid, lambda: None)()
        if body is None:
            return None, "YouTube に接続できない — ネット接続を確認してもう一度実行してください"
        return body, None

    core.http_get = fake_get        # ★本体は関数内 import なのでこの差し替えが効く

    mails = []

    def fake_mail(subject, body_html, to_email=None):
        mails.append((subject, body_html))
        return {"sent": True}

    mod._send_monitor_email = fake_mail

    def q(sql, params=()):
        cn = mod.db()
        try:
            cur = cn.cursor()
            cur.execute(sql, params)
            if sql.lstrip().upper().startswith("SELECT"):
                return cur.fetchall()
            cn.commit()
        finally:
            cn.close()

    for t in ("月曜1限 中学応用", "火曜1限 高校数学", "水曜1限 高校英語", "木曜1限 高校国語"):
        q("INSERT INTO class_sessions (title, is_published) VALUES (?,1)", (t,))
    sess = {r["title"]: r["id"] for r in q("SELECT id, title FROM class_sessions")}
    for pid, name in [(PL_MON, "8月以降月曜日1時間目"), (PL_TUE, "8月以降火曜日1時間目"),
                      (PL_WED, "8月以降水曜日1時間目"), (PL_THU, "8月以降木曜日1時間目")]:
        q("INSERT INTO admin_youtube_playlists (playlist_id, name) VALUES (?,?)", (pid, name))
    q("INSERT INTO class_recordings (session_id, title, video_url, provider, is_published) VALUES (?,?,?,'youtube',1)",
      (sess["月曜1限 中学応用"], md(MON_OLD), f"https://youtu.be/{V_MON_OLD}"))
    q("INSERT INTO class_recordings (session_id, title, video_url, provider, is_published) VALUES (?,?,?,'youtube',1)",
      (sess["木曜1限 高校国語"], md(recent(3, 1)), "https://youtu.be/ThuOld00001"))

    def n_rec():
        return q("SELECT COUNT(*) AS n FROM class_recordings")[0]["n"]

    def n_vid(vid):
        return sum(1 for r in q("SELECT video_url FROM class_recordings") if core.video_id(r["video_url"]) == vid)

    def events():
        return q("SELECT props FROM events WHERE name = ? ORDER BY id", (mod._CLASS_REC_ASSIGN_EVENT,))

    def leaks(text):
        """全ID と先頭4文字 (画面と同じ伏せ方) のどれかが載っていれば返す。"""
        return [x for x in ALL_IDS if x in text] + [x[:4] + "…" for x in ALL_IDS if x[:4] + "…" in text]

    client = TestClient(mod.app)
    tok = admin_token(mod)

    def button(body):
        mod._RATE_LIMIT_STORE.clear()
        return client.post("/api/admin/class-recordings/auto-assign", json=body,
                           headers={"Authorization": f"Bearer {tok}"})

    # =====================================================================
    print("1) 定期実行の経路")
    src = open(MAIN_PY, encoding="utf-8").read()
    real_run = mod._class_rec_auto_assign_run
    seen = []

    def spy_run(**kw):
        seen.append(kw)
        return {"_record": {"applied": 0, "held": 0, "blocking": 0}, "ok": True}

    mod._class_rec_auto_assign_run = spy_run
    try:
        r = mod._class_rec_auto_assign_daily()
    finally:
        mod._class_rec_auto_assign_run = real_run
    check("dry_run=False・allow_partial=True・source=scheduled で本体を呼ぶ",
          seen == [{"dry_run": False, "allow_partial": True, "source": "scheduled", "final_attempt": True}], seen)
    check("何も無い日はメールしない", r.get("mailed") is False and not mails, r)
    check("起動時の登録は CRON_SECRET と CLASS_REC_AUTO_ASSIGN_ENABLED の両方が要る",
          "if CRON_SECRET and CLASS_REC_AUTO_ASSIGN_ENABLED:\n        task = asyncio.create_task(_class_rec_auto_assign_scheduler())" in src)
    sched_src = inspect.getsource(mod._class_rec_auto_assign_scheduler)
    check("scheduler は asyncio.to_thread 経由で呼ぶ (直接呼ぶとサーバ全体が止まる)",
          "asyncio.to_thread(_class_rec_auto_assign_daily, " in sched_src
          and "_class_rec_auto_assign_daily(" not in sched_src.replace("asyncio.to_thread(_class_rec_auto_assign_daily, ", ""))
    mod.CLASS_REC_AUTO_ASSIGN_ENABLED = False
    check("CLASS_REC_AUTO_ASSIGN_ENABLED=0 なら何もしない",
          mod._class_rec_auto_assign_daily().get("status") == "disabled")
    mod.CLASS_REC_AUTO_ASSIGN_ENABLED = True
    env_bad = []
    for v, exp in [("0", False), ("false", False), ("OFF", False), (" no ", False),
                   ("1", True), ("true", True), ("yes", True), ("", True), (" 1", True)]:
        os.environ["CLASS_REC_AUTO_ASSIGN_ENABLED"] = v
        if mod._class_rec_auto_assign_env_enabled() is not exp:
            env_bad.append(v)
    os.environ.pop("CLASS_REC_AUTO_ASSIGN_ENABLED")
    if mod._class_rec_auto_assign_env_enabled() is not True:
        env_bad.append("(未設定)")
    os.environ["CLASS_REC_AUTO_ASSIGN_ENABLED"] = "1"
    check("env は 0 / false / off / no だけが無効 (true・空文字・' 1' は有効 = 黙って止まらない)", not env_bad, env_bad)
    check("監視の対象 (_SCHEDULER_MAX_AGE_DAYS) も同じ判定関数で決める",
          '**({"class_rec_assign_run": 2} if _class_rec_auto_assign_env_enabled() else {})' in src
          and "CLASS_REC_AUTO_ASSIGN_ENABLED = _class_rec_auto_assign_env_enabled()" in src)

    # scheduler のループを実際に回す (sleep を差し替え・目標時刻を 0 時にして「過ぎている」状態を作る)
    real_sleep, real_daily, real_hour = asyncio.sleep, mod._class_rec_auto_assign_daily, mod._CLASS_REC_AUTO_ASSIGN_HOUR_JST
    sleeps, daily_threads, finals = [], [], []
    results = [{"status": "busy"}, {"status": "retry"}, {"status": "retry"}, {"status": "done"}]

    async def fake_sleep(secs, *a, **k):
        sleeps.append((secs, len(daily_threads)))   # (寝た秒数, それまでに本体を呼んだ回数)
        if len(sleeps) >= 5:
            raise asyncio.CancelledError()

    def spy_daily(final_attempt=True):
        daily_threads.append(threading.get_ident())
        finals.append(final_attempt)
        return results.pop(0) if results else {"status": "done"}

    asyncio.sleep = fake_sleep
    mod._class_rec_auto_assign_daily = spy_daily
    # 目標時刻 = いまの時 (JST) の 0 分 → 「今日の分は過ぎている」状態。次は約 24 時間後になる
    mod._CLASS_REC_AUTO_ASSIGN_HOUR_JST = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).hour
    try:
        try:
            asyncio.run(mod._class_rec_auto_assign_scheduler())
        except asyncio.CancelledError:
            pass
    finally:
        asyncio.sleep, mod._class_rec_auto_assign_daily = real_sleep, real_daily
        mod._CLASS_REC_AUTO_ASSIGN_HOUR_JST = real_hour
    check("7時を過ぎて起動したら、その日の分をすぐ走らせる・busy なら 10 分後にやり直す",
          len(sleeps) == 5 and sleeps[0] == (120, 0) and sleeps[1] == (600, 1), f"sleeps={sleeps}")
    check("一時的な失敗 (retry) は 30 分後に最大 2 回やり直す (busy は回数に数えない)",
          sleeps[2:4] == [(1800, 2), (1800, 3)], sleeps)
    check("最後のやり直しの回だけ final_attempt=True (そこでだけ記録・メールする)",
          finals == [False, False, False, True], finals)
    check("やり直しで済ませた後は翌日の目標時刻まで寝る (1 日 1 回)",
          len(sleeps) == 5 and sleeps[4][0] > 20 * 3600 and sleeps[4][1] == 4, sleeps)
    check("本体はイベントループとは別のスレッドで動く",
          daily_threads and all(t != threading.get_ident() for t in daily_threads))

    # =====================================================================
    print("2) 本番と同じ形で 1 回走らせる (取れた分だけ登録・保留はメール)")
    flaky["thu_left"] = 1
    calls.clear()
    before = n_rec()
    r = mod._class_rec_auto_assign_daily()
    rec = r.get("record") or {}
    check("status=done", r.get("status") == "done", r)
    check("取れた分 (月・火・木の新着 3 本) を登録する", rec.get("applied") == 3 and n_rec() == before + 3,
          f"applied={rec.get('applied')} {before}→{n_rec()}")
    check("取得できない水曜は保留 (止めずに他を登録)", rec.get("blocking", 0) >= 1 and not rec.get("error"), rec)
    check("日付の読めない動画は保留に数える", rec.get("held", 0) >= 2, rec.get("held"))
    check("すぐ返ってきた取得失敗 (解析できないページ) は 1 回だけ読み直す", calls.get(PL_THU) == 2, calls)
    check("毎朝の実行は「接続できない」も 1 回だけ読み直す (画面が待っていない)", calls.get(PL_WED) == 2, calls)
    check("読み直しで取れた木曜の新着が入る", n_vid(V_THU_NEW) == 1)
    ev = events()
    check("実行記録が 1 件", len(ev) == 1, len(ev))
    props_txt = ev[0]["props"] if ev else ""
    try:
        props = json.loads(props_txt)
    except Exception:
        props = None
    check("実行記録は JSON として読める", isinstance(props, dict), props_txt[:80])
    check("実行記録に動画ID・再生リストIDが入らない (先頭4文字も)", not leaks(props_txt), leaks(props_txt))
    check("実行記録にクラス名と日付 (M/D) が残る",
          isinstance(props, dict) and any(c_["class"] == "月曜1限 中学応用" and md(MON_D) in c_["dates"]
                                         for c_ in props.get("classes", [])), props_txt[:200])
    check("登録・保留のあった日はメールを 1 通送る", len(mails) == 1 and r.get("mailed") is True, len(mails))
    subj, body = mails[-1] if mails else ("", "")
    check("メールに動画ID・再生リストIDが入らない (先頭4文字も)", not leaks(subj + body), leaks(subj + body))
    check("メールに授業名・日付・件数・保留の理由がある",
          "月曜1限 中学応用" in body and md(MON_D) in body and "3件" in subj and "保留あり" in subj
          and "接続できない" in body, subj)
    check("メールに生徒の情報が無い (students を読まない)", "@" not in body.replace("example.invalid", ""))

    print("3) 同じ日に 2 回走らない")
    nm = len(mails)
    calls.clear()
    r2 = mod._class_rec_auto_assign_daily()
    check("2 回目は skipped_today", r2.get("status") == "skipped_today", r2)
    check("2 回目は YouTube も見に行かない・記録も増えない・メールも出ない",
          not calls and len(events()) == 1 and len(mails) == nm, calls)
    # 外側の確認をすり抜けた形 (別の replica が同時に確認を通った) → 錠の中の確認で止まる
    out_in = mod._class_rec_auto_assign_run(dry_run=False, allow_partial=True, source="scheduled")
    check("錠の中でも「今日はもう走った」を確かめて、記録を二重に書かない",
          out_in.get("_skipped_today") is True and len(events()) == 1)

    print("4) 翌日 (2 回目の実行) で二重登録しない")
    q("DELETE FROM events WHERE name = ?", (mod._CLASS_REC_ASSIGN_EVENT,))
    n0, nm = n_rec(), len(mails)
    r3 = mod._class_rec_auto_assign_daily()
    check("翌日の実行は新着 0", (r3.get("record") or {}).get("applied") == 0, r3.get("record"))
    check("行が増えない", n_rec() == n0, f"{n0}→{n_rec()}")
    check("どの動画も 1 件ずつ", all(n_vid(v) == 1 for v in (V_MON_NEW, V_TUE_NEW, V_THU_NEW)))
    check("前の通知と同じ保留だけの日はメールを繰り返さない", len(mails) == nm and r3.get("mailed") is False,
          (r3.get("record") or {}).get("fp"))

    print("4b) 通知の重複抑止: 新しい保留・7 日ごとの再通知・送れなかった日の再送")
    V_TUE_BAD2 = "TueBad00002"
    ALL_IDS.append(V_TUE_BAD2)
    PAGES[PL_TUE] = lambda: yt_page([(V_TUE_NEW, md(TUE_D)), (V_TUE_BAD, "第3回 まとめ"), (V_TUE_BAD2, "第4回 演習")])
    real_mail = mod._send_monitor_email
    mod._send_monitor_email = lambda *a, **k: {"sent": False}   # Resend の一時障害
    try:
        q("DELETE FROM events WHERE name = ?", (mod._CLASS_REC_ASSIGN_EVENT,))
        rf = mod._class_rec_auto_assign_daily()
    finally:
        mod._send_monitor_email = real_mail
    mev = q("SELECT props FROM events WHERE name = ? ORDER BY id", (mod._CLASS_REC_MAIL_EVENT,))
    last_mev = json.loads(mev[-1]["props"]) if mev else {}
    check("新しい保留が増えた日は送ろうとする・送れなかったことを記録に残す",
          rf.get("mailed") is False and last_mev.get("sent") is False and last_mev.get("why") == "new_hold", last_mev)
    check("送信結果の記録に ID が入らない", not leaks(json.dumps(last_mev, ensure_ascii=False)))
    nm = len(mails)
    q("DELETE FROM events WHERE name = ?", (mod._CLASS_REC_ASSIGN_EVENT,))
    rr = mod._class_rec_auto_assign_daily()
    check("送れなかった保留は翌朝もう一度送る", rr.get("mailed") is True and len(mails) == nm + 1, rr.get("mailed"))
    check("増えた保留がメールに出る (題名で。ID は出さない)",
          "第4回 演習" in mails[-1][1] and not leaks(mails[-1][0] + mails[-1][1]) if mails else False)
    q("DELETE FROM events WHERE name = ?", (mod._CLASS_REC_ASSIGN_EVENT,))
    rs = mod._class_rec_auto_assign_daily()
    check("同じ保留の翌日は送らない", rs.get("mailed") is False and len(mails) == nm + 1)
    q("UPDATE events SET created_at = ? WHERE name = ?",
      ((datetime.datetime.utcnow() - datetime.timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S"),
       mod._CLASS_REC_MAIL_EVENT))
    q("DELETE FROM events WHERE name = ?", (mod._CLASS_REC_ASSIGN_EVENT,))
    rw = mod._class_rec_auto_assign_daily()
    check("同じ保留でも 7 日たったらもう一度知らせる", rw.get("mailed") is True and len(mails) == nm + 2, rw.get("mailed"))
    fp_a = mod._class_rec_hold_fingerprint({"problems": ["月曜1限: 最新の録画が 30日前 (2026-09-01) で止まっている"]})
    fp_b = mod._class_rec_hold_fingerprint({"problems": ["月曜1限: 最新の録画が 31日前 (2026-09-01) で止まっている"]})
    fp_c = mod._class_rec_hold_fingerprint({"problems": ["火曜1限: 最新の録画が 30日前 (2026-09-01) で止まっている"]})
    fp_d = mod._class_rec_hold_fingerprint({"problems": [f"月曜1限: 動画 {V_MON_NEW[:4]}… ('x') が別の授業に登録されている"]})
    fp_e = mod._class_rec_hold_fingerprint({"problems": [f"月曜1限: 動画 {V_MON_OLD[:4]}… ('x') が別の授業に登録されている"]})
    check("指紋: 毎日変わる「N日前」は同じ扱い・クラスが違えば別", fp_a == fp_b and fp_a != fp_c, (fp_a, fp_b, fp_c))
    check("指紋は ID を伏せた文から作る (ID の先頭4文字だけ違う保留は同じ扱い)", fp_d == fp_e)

    print("5) 取得している間に別の登録が入っても二重にしない (書く直前の読み直し)")
    mon_items.append((V_RACE, md(MON_2W)))
    side_effect[PL_MON] = lambda: q(
        "INSERT INTO class_recordings (session_id, title, video_url, provider, is_published) VALUES (?,?,?,'youtube',1)",
        (sess["月曜1限 中学応用"], md(MON_2W), f"https://www.youtube.com/watch?v={V_RACE}"))
    calls.clear()
    n_ev = len(events())
    resp = button({"apply": True, "allow_partial": True})
    out = resp.json()
    check("ボタンは 200", resp.status_code == 200, resp.status_code)
    check("ボタンは「接続できない」を読み直さない (画面を待たせない)", calls.get(PL_WED) == 1, calls)
    check("毎朝の実行の最新の記録が error でなければ、ボタンは実行記録を足さない", len(events()) == n_ev)
    check("計画には入っていた (① の読みの後に登録された)", any(p["label"] == md(MON_2W) for p in out.get("planned", [])))
    check("書く直前の読み直しで飛ばす (URL の書き方が違っても)", n_vid(V_RACE) == 1, n_vid(V_RACE))
    check("飛ばしたことを確認事項に出す", any("別の登録が先に入っていた" in p for p in out.get("problems", [])))
    check("飛ばした分は applied に数えない", out.get("applied") == 0, out.get("applied"))

    print("6) 排他")
    mon_items.append((V_LOCK, md(recent(0, 3))))
    # 6-a 別プロセスが錠を持っている (advisory lock が取れない) → 1 件も書かない
    real_lock = mod._class_rec_try_db_lock
    mod._class_rec_try_db_lock = lambda c: False
    try:
        n0 = n_rec()
        rb = button({"apply": True, "allow_partial": True})
        check("錠が取れないボタンは 409", rb.status_code == 409, rb.status_code)
        q("DELETE FROM events WHERE name = ?", (mod._CLASS_REC_ASSIGN_EVENT,))
        rd = mod._class_rec_auto_assign_daily()
        check("錠が取れない定期実行は busy (記録しない = 後でやり直す)", rd.get("status") == "busy" and not events(), rd)
        check("錠が取れないときは 1 件も書かない", n_rec() == n0, f"{n0}→{n_rec()}")
        check("dry-run は錠を使わないので押せる", button({}).status_code == 200)
    finally:
        mod._class_rec_try_db_lock = real_lock
    lock_src = inspect.getsource(real_lock)
    run_src = inspect.getsource(real_run)
    check("錠は pg_try_advisory_xact_lock (待たない・トランザクション終了で外れる)",
          "pg_try_advisory_xact_lock" in lock_src and "pg_advisory_lock(" not in lock_src)
    check("錠は YouTube を読んだ後・登録済みの読み直しより前に取る",
          run_src.index("_auto_assign_fetch(") < run_src.index("_class_rec_try_db_lock(c)")
          < run_src.index('SELECT video_url FROM class_recordings'))
    # 6-b 同じプロセスで並行 → 片方は諦める
    gate["ev"] = threading.Event()
    th_out = {}

    def bg():
        try:
            th_out["r"] = mod._class_rec_auto_assign_run(dry_run=True, source="button")
        except Exception as e:
            th_out["e"] = e
    th = threading.Thread(target=bg)
    th.start()
    for _ in range(200):
        if calls:
            break
        threading.Event().wait(0.01)
    calls.clear()
    try:
        rb2 = button({})
        rd2 = mod._class_rec_auto_assign_daily()
    finally:
        gate["ev"].set()
        th.join(20)
        gate["ev"] = None
    check("実行中にボタンを押すと 409", rb2.status_code == 409, rb2.status_code)
    check("実行中の定期実行は busy", rd2.get("status") == "busy", rd2)
    check("先に走っていた方は最後まで終わる", "r" in th_out and th_out["r"].get("ok"), th_out)
    # 錠が空いたら V_LOCK が入る
    r6 = mod._class_rec_auto_assign_daily()
    check("錠が空いた後の実行で登録される (1 件だけ)", n_vid(V_LOCK) == 1 and r6.get("status") == "done", r6.get("status"))

    print("7) 監視: 全体停止は props.error、保留だけの日は error にしない")
    rows = {e["name"]: e for e in mod._scheduler_status_rows()}
    row = rows.get(mod._CLASS_REC_ASSIGN_EVENT)
    check("監視の対象 (_SCHEDULER_MAX_AGE_DAYS) に入っている", row is not None and row["max_age_days"] == 2, list(rows))
    check("保留だけの日は失敗扱いにしない",
          mod._CLASS_REC_ASSIGN_EVENT not in [e["name"] for e in mod._failed_schedulers(list(rows.values()))])
    # 二重登録の恐れ (hazard) → 全体停止
    q("INSERT INTO class_recordings (session_id, title, video_url, provider, is_published) VALUES (?,?,?,'youtube',1)",
      (sess["火曜1限 高校数学"], "手入力", "youtu.be/Abcdefg hijk"))
    q("DELETE FROM events WHERE name = ?", (mod._CLASS_REC_ASSIGN_EVENT,))
    mon_items.append(("HazVid00001", md(recent(0, 4))))
    ALL_IDS.append("HazVid00001")
    nm, n0 = len(mails), n_rec()
    rh = mod._class_rec_auto_assign_daily()
    rech = rh.get("record") or {}
    check("hazard は「取れた分だけ」でも登録しない", n_rec() == n0 and rech.get("applied") == 0, rech)
    check("hazard の全体停止は props.error として記録する", "二重登録の恐れ" in str(rech.get("error")), rech.get("error"))
    rows = {e["name"]: e for e in mod._scheduler_status_rows()}
    check("全体停止は監視の失敗 (_failed_schedulers) に乗る",
          mod._CLASS_REC_ASSIGN_EVENT in [e["name"] for e in mod._failed_schedulers(list(rows.values()))])
    snap_lbl = "授業録画の自動割り当て (毎朝7時)"
    check("監視アラートの表示名が 2 か所にある", src.count(f'"{mod._CLASS_REC_ASSIGN_EVENT}": "{snap_lbl}"') == 2)
    check("停止の日はメールする (件名に停止)", len(mails) == nm + 1 and "停止" in mails[-1][0], mails[-1][0] if mails else "")
    check("停止メールにも ID が入らない", not leaks(mails[-1][0] + mails[-1][1]) if mails else False)
    check("hazard の停止は「今日は済んだ」に数える (人の対応が要る = やり直しても同じ)", mod._class_rec_ran_today())
    q("DELETE FROM class_recordings WHERE title = ?", ("手入力",))
    # 塾長が悪い URL を直してボタンで登録 → 回復の記録で監視の失敗が止まる
    q("UPDATE events SET created_at = ? WHERE name = ?",
      ((datetime.datetime.utcnow() - datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
       mod._CLASS_REC_ASSIGN_EVENT))   # SQLite の時刻は秒単位。同じ秒だと「最新」がどちらか決まらない
    rb_fix = button({"apply": True, "allow_partial": True})
    check("直した後のボタンで HazVid が 1 件入る", rb_fix.status_code == 200 and n_vid("HazVid00001") == 1,
          rb_fix.status_code)
    evs = events()
    last_p = json.loads(evs[-1]["props"]) if evs else {}
    check("最新が error のときボタンで直したら回復の記録 (source=button・recovered) を足す",
          len(evs) == 2 and last_p.get("source") == "button" and last_p.get("recovered") is True
          and not last_p.get("error"), last_p)
    check("回復の記録にも ID が入らない", not leaks(evs[-1]["props"]) if evs else False)
    rows = {e["name"]: e for e in mod._scheduler_status_rows()}
    check("回復の記録の後は監視の失敗 (_failed_schedulers) に乗らない",
          mod._CLASS_REC_ASSIGN_EVENT not in [e["name"] for e in mod._failed_schedulers(list(rows.values()))])
    check("ボタンの回復の記録は「今日の自動実行は済んだ」に数えない (hazard の記録を消した状態で)",
          (q("DELETE FROM events WHERE name = ? AND props NOT LIKE ?", (mod._CLASS_REC_ASSIGN_EVENT, '%"button"%'))
           or True) and not mod._class_rec_ran_today())
    # 例外で落ちた日
    q("DELETE FROM events WHERE name = ?", (mod._CLASS_REC_ASSIGN_EVENT,))

    def boom(**kw):
        raise HTTPException(status_code=500, detail=f"登録に失敗しました (IntegrityError) https://youtu.be/{V_MON_NEW}")
    mod._class_rec_auto_assign_run = boom
    try:
        re_ = mod._class_rec_auto_assign_daily()
    finally:
        mod._class_rec_auto_assign_run = real_run
    evs = events()
    check("例外の日は status=error で記録し、error に理由", re_.get("status") == "error" and len(evs) == 1
          and "登録に失敗しました" in json.loads(evs[0]["props"]).get("error", ""), re_)
    check("例外の記録にも ID が入らない", not leaks(evs[0]["props"]) if evs else False, evs[0]["props"] if evs else "")
    check("例外の記録は retryable =「今日は済んだ」に数えない (再起動・別の replica が走り直せる)",
          json.loads(evs[0]["props"]).get("retryable") is True and not mod._class_rec_ran_today() if evs else False)
    # やり直しが残っている回の例外 → 記録もメールもしない
    q("DELETE FROM events WHERE name = ?", (mod._CLASS_REC_ASSIGN_EVENT,))
    nm = len(mails)
    mod._class_rec_auto_assign_run = boom
    try:
        rr_ = mod._class_rec_auto_assign_daily(final_attempt=False)
    finally:
        mod._class_rec_auto_assign_run = real_run
    check("やり直しが残っている回の例外は status=retry・記録もメールもしない",
          rr_.get("status") == "retry" and not events() and len(mails) == nm, rr_)
    # 別の replica が今日の分を正常に済ませた後に、こちらが最後の回で例外 → 打ち消さない・上書きしない
    mod._record_scheduler_run(mod._CLASS_REC_ASSIGN_EVENT, {"source": "scheduled", "applied": 1})
    real_ran_today = mod._class_rec_ran_today
    mod._class_rec_ran_today = lambda: False   # 外側の確認をすり抜けた形 (同時に入った)
    mod._class_rec_auto_assign_run = boom
    try:
        rx = mod._class_rec_auto_assign_daily(final_attempt=True)
    finally:
        mod._class_rec_auto_assign_run = real_run
        mod._class_rec_ran_today = real_ran_today
    check("例外の記録も錠の中で「今日もう済んだか」を確かめる (正常な記録の後に error を書かない・メールしない)",
          rx.get("status") == "skipped_today" and len(events()) == 1 and len(mails) == nm, rx)
    check("例外の記録は錠の中で書く", "_class_rec_try_db_lock(c)" in inspect.getsource(mod._class_rec_record_error_locked))

    print("7b) YouTube 全断 (1 クラスも取得できない) は 30 分後にやり直し、最後の回だけ記録")
    q("DELETE FROM events WHERE name = ?", (mod._CLASS_REC_ASSIGN_EVENT,))
    saved_pages = dict(PAGES)
    for k in list(PAGES):
        PAGES[k] = lambda: None
    nm = len(mails)
    calls.clear()
    try:
        rt = mod._class_rec_auto_assign_daily(final_attempt=False)
        check("やり直しが残っている回は status=retry・記録もメールもしない",
              rt.get("status") == "retry" and not events() and len(mails) == nm, rt)
        check("毎朝の実行は「接続できない」を 1 回読み直してから諦める", calls.get(PL_MON) == 2, calls)
        rt2 = mod._class_rec_auto_assign_daily(final_attempt=True)
        rect = rt2.get("record") or {}
        check("最後の回は error (retryable) を記録して「停止」メール",
              rt2.get("status") == "done" and "見に行けませんでした" in str(rect.get("error"))
              and rect.get("retryable") is True and len(mails) == nm + 1 and "停止" in mails[-1][0], rect)
        check("全断の記録は「今日は済んだ」に数えない (回線が戻った後の再起動で走り直せる)",
              len(events()) == 1 and not mod._class_rec_ran_today())
    finally:
        PAGES.update(saved_pages)
    check("hazard は「一時的な失敗」に数えない (やり直さず即 error)",
          not mod._class_rec_assign_is_transient({"refused": "x", "summary": {"sessions_total": 3, "covered": 0},
                                                  "rows": [{"ok": False}]}))

    print("8) 何も無い日はメールしない")
    # 水曜のクラスを閉じる (授業を非公開にし、再生リストも一覧から外す。片方だけだと「0件マッチ」で保留が残る)
    q("UPDATE class_sessions SET is_published = 0 WHERE title = ?", ("水曜1限 高校英語",))
    q("DELETE FROM admin_youtube_playlists WHERE playlist_id = ?", (PL_WED,))
    PAGES[PL_TUE] = lambda: yt_page([(V_TUE_NEW, md(TUE_D))])
    q("DELETE FROM events WHERE name = ?", (mod._CLASS_REC_ASSIGN_EVENT,))
    nm = len(mails)
    rq = mod._class_rec_auto_assign_daily()
    recq = rq.get("record") or {}
    check("新着なし・保留なしの日", recq.get("applied") == 0 and recq.get("held") == 0 and recq.get("blocking") == 0
          and not recq.get("error"), recq)
    check("その日はメールを送らない", len(mails) == nm and rq.get("mailed") is False)
    check("それでも実行記録は残す (生存監視)", len(events()) == 1)

    print("8b) 配布が止まっているクラス (STALE) も知らせる")
    q("INSERT INTO class_sessions (title, is_published) VALUES (?,1)", ("金曜1限 高校理科",))
    sid_fri = q("SELECT id FROM class_sessions WHERE title = ?", ("金曜1限 高校理科",))[0]["id"]
    PL_FRI, V_FRI = "PLtest_fri", "FriOld00001"
    ALL_IDS.extend([PL_FRI, V_FRI])
    q("INSERT INTO admin_youtube_playlists (playlist_id, name) VALUES (?,?)", (PL_FRI, "8月以降金曜日1時間目"))
    old_d = recent(4, 6)
    q("INSERT INTO class_recordings (session_id, title, video_url, provider, is_published, created_at) "
      "VALUES (?,?,?,'youtube',1,?)", (sid_fri, md(old_d), f"https://youtu.be/{V_FRI}",
                                       (datetime.datetime.utcnow() - datetime.timedelta(days=40)).strftime("%Y-%m-%d %H:%M:%S")))
    PAGES[PL_FRI] = lambda: yt_page([(V_FRI, md(old_d))])
    q("DELETE FROM events WHERE name = ?", (mod._CLASS_REC_ASSIGN_EVENT,))
    nm = len(mails)
    rst = mod._class_rec_auto_assign_daily()
    recst = rst.get("record") or {}
    check("STALE は登録も止めず保留にも数えないが、件数を記録に残す",
          recst.get("stale") == 1 and recst.get("held") == 0 and recst.get("blocking") == 0 and not recst.get("error"), recst)
    check("STALE だけの日もメールで知らせる", rst.get("mailed") is True and len(mails) == nm + 1
          and "止まって" in mails[-1][1] and not leaks(mails[-1][0] + mails[-1][1]) if len(mails) > nm else False,
          mails[-1][0] if mails else "")
    q("DELETE FROM events WHERE name = ?", (mod._CLASS_REC_ASSIGN_EVENT,))
    rst2 = mod._class_rec_auto_assign_daily()
    check("同じ STALE は翌日は送らない", rst2.get("mailed") is False and len(mails) == nm + 1)

    print("9) 実行記録は 4000 字で切られても壊れない")
    big = {"today": "2026-10-08", "mode": "apply", "applied": 300, "summary": {}, "rows": [], "planned": [],
           "problems": [], "_written": [{"session_title": f"{i:03d} " + "長い授業名" * 20, "slot": "月曜1限",
                                         "label": f"{1 + i % 12}/{1 + i % 28}"} for i in range(300)]}
    rec_big = mod._class_rec_assign_record(big, "scheduled")
    txt = json.dumps(rec_big, ensure_ascii=False)
    check("要約は 3500 字以内 (授業一覧は 20 クラス・1 クラス 12 日付まで。超えたら一覧を落として件数だけ)",
          len(txt) <= 3500 and len(rec_big.get("classes", [])) <= 20, len(txt))
    mod._record_scheduler_run("class_rec_assign_test", rec_big)
    got = q("SELECT props FROM events WHERE name = 'class_rec_assign_test'")
    try:
        ok_json = json.loads(got[0]["props"]).get("applied") == 300
    except Exception:
        ok_json = False
    check("_record_scheduler_run を通しても JSON のまま読める", ok_json)
    small = mod._class_rec_assign_record({"rows": [], "planned": [{"video_id": V_MON_NEW}], "summary": {}}, "scheduled")
    check("planned (生の動画ID入り) は件数しか使わない",
          small.get("planned") == 1 and not leaks(json.dumps(small, ensure_ascii=False)))

    print("10) ボタンの応答の形が変わらない")
    base_keys = {"ok", "mode", "today", "summary", "rows", "planned", "problems", "notes",
                 "blocking", "hazard", "applied", "refused", "message"}
    summary_keys = {"playlist_total", "playlist_named", "sessions_total", "recordings_total", "fetched",
                    "skipped_name", "covered", "uncovered", "no_playlist"}
    d = button({}).json()
    check("dry-run の応答のキーは従来どおり", set(d) == base_keys, sorted(set(d) ^ base_keys))
    check("dry-run の応答の値も従来どおり (mode・applied・refused・message・summary のキー)",
          d.get("mode") == "dry-run" and d.get("applied") == 0 and d.get("refused") is None and d.get("ok") is True
          and d.get("message") == ("新しい録画はありません。" if not d.get("problems")
                                   else "登録できる新着はありません (確認が要る項目があります)。")
          and set(d.get("summary") or {}) == summary_keys and d.get("summary", {}).get("covered") == 4, d.get("message"))
    mon_items.append(("ShapeV00001", md(recent(0, 5))))
    ALL_IDS.append("ShapeV00001")
    a = button({"apply": True, "allow_partial": True}).json()
    check("apply の応答のキーは従来どおり (+ verified / duplicates)",
          set(a) == base_keys | {"verified", "duplicates"}, sorted(set(a) ^ (base_keys | {"verified", "duplicates"})))
    check("apply の応答の値も従来どおり (mode・applied・verified・duplicates・refused・message)",
          a.get("mode") == "apply" and a.get("applied") == 1 and a.get("verified") is True and a.get("duplicates") == []
          and a.get("refused") is None and a.get("message") == "✅ 1件を登録しました (各1件で入っていることを確認済み)"
          and len(a.get("planned") or []) == 1 and a["planned"][0].get("video") == "Shap…", a.get("message"))
    d2 = button({}).json()
    check("登録の後の dry-run は新着 0 (planned 空・applied 0)", d2.get("planned") == [] and d2.get("applied") == 0)
    check("応答に内部用のキー (_ で始まる) を出さない", not [k for k in list(d) + list(a) if k.startswith("_")])
    check("応答に動画IDの生値が載らない", not [x for x in ALL_IDS if x in json.dumps(a, ensure_ascii=False)])

    if FAILURES:
        print(f"\n❌ VIOLATION: {len(FAILURES)} 件")
        for f in FAILURES:
            print(f"   - {f}")
        return 1
    print("\n=== ALL PASS (定期実行の経路・1日1回・やり直し・二重登録防止・排他・読み直し・伏せ字・通知の重複抑止・監視・応答の形) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
