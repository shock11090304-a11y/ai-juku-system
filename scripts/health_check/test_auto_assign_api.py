#!/usr/bin/env python3
"""🎬 授業録画の自動割り当て API (POST /api/admin/class-recordings/auto-assign) の回帰テスト。

背景 (2026-08-21):
  塾長が再生リストに動画を上げたあと、割り当ては `railway run` のターミナル作業だった。
  CEO 画面のボタンから同じことができるようにしたので、**書き込む側**の性質を機械で固定する。
  判定そのもの (取得失敗を0本に化けさせない等) は
  scripts/class_recordings/check_assign_logic.py が見る。こちらは API の振る舞い:

  1. 未認証では動かない (再生リストIDも録画も塾長のもの)
  2. 既定は dry-run — **1件も書き込まない**
  3. apply で各1件だけ入り、書いた URL が次回 video_id() で読み戻せる
  4. もう一度実行しても**増えない** (二重登録しない = 取り返しのつかない事故の本命)
  5. 取得できない再生リストがあるとき「新着なし」で終わらせず、登録を止める
  6. 別クラスに登録済みの動画を勝手に足さない
  7. 応答に動画IDの生値を載せない (限定公開動画のIDはアクセス権そのもの)
  8. 同時実行を弾く (UNIQUE 制約が無いので重複を防げるのはこの錠だけ)

実行:
    python3 scripts/health_check/test_auto_assign_api.py
    # exit 0 = PASS / 1 = FAIL

外部通信は一切しない (http_get を差し替える)。DB は一時 SQLite。
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

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {detail}" if detail else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    """一時 SQLite + ダミー env で server/main.py を in-process ロード。"""
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="autoassign_"), "test.db")
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
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_autoassign", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
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
    from fastapi.testclient import TestClient

    # --- 材料 -------------------------------------------------------------
    # 再生リスト2本 (月曜1限・火曜1限) + 名前が読めない1本 + 取得に失敗する1本。
    # ★ID は「このリポジトリに書かない」対象なので、テスト用の架空値を使う。
    PL_MON, PL_TUE, PL_JUNK, PL_DEAD = "PLtest_mon", "PLtest_tue", "PLtest_junk", "PLtest_dead"
    MON_D, TUE_D = recent(0), recent(1)
    MON_OLD = recent(0, weeks_ago=1)
    V_MON_NEW, V_MON_OLD = "MonNew00001", "MonOld00001"
    V_TUE_NEW, V_SHARED = "TueNew00001", "Shared00001"
    PAGES = {
        PL_MON: yt_page([(V_MON_OLD, f"{MON_OLD.month}/{MON_OLD.day}"),
                         (V_MON_NEW, f"{MON_D.month}/{MON_D.day}")]),
        PL_TUE: yt_page([(V_TUE_NEW, f"{TUE_D.month}/{TUE_D.day}"),
                         (V_SHARED, f"{TUE_D.month}/{TUE_D.day} 合同")]),
        PL_JUNK: yt_page([]),
        PL_DEAD: None,     # 取得できない (通信断・削除)
    }

    def fake_get(url, timeout=30):
        pid = url.split("list=")[-1]
        body = PAGES.get(pid)
        if body is None:
            return None, "YouTube に接続できない — ネット接続を確認してもう一度実行してください"
        return body, None

    core.http_get = fake_get        # ★エンドポイントは関数内 import なのでこの差し替えが効く

    conn = mod.db()
    c = conn.cursor()
    c.execute("INSERT INTO class_sessions (title, is_published) VALUES (?,1)", ("月曜1限 中学応用",))
    c.execute("INSERT INTO class_sessions (title, is_published) VALUES (?,1)", ("火曜1限 高校数学",))
    # ★水曜のクラスも作る。作らないと PL_DEAD は「授業が0件マッチ」で **取得しに行く前に**
    #   弾かれ、肝心の「取得できない」経路を一度も通らない (空振りのテストになる)。
    c.execute("INSERT INTO class_sessions (title, is_published) VALUES (?,1)", ("水曜1限 高校英語",))
    c.execute("SELECT id, title FROM class_sessions ORDER BY id")
    sess = {r["title"]: r["id"] for r in c.fetchall()}
    for pid, name in [(PL_MON, "8月以降月曜日1時間目"), (PL_TUE, "8月以降火曜日1時間目"),
                      (PL_JUNK, "以前のまとめ"), (PL_DEAD, "8月以降水曜日1時間目")]:
        c.execute("INSERT INTO admin_youtube_playlists (playlist_id, name) VALUES (?,?)", (pid, name))
    # 月曜の古い回は登録済み / 合同動画は**別クラス**(月曜)に登録済み
    c.execute("INSERT INTO class_recordings (session_id, title, video_url, provider, is_published) "
              "VALUES (?,?,?,'youtube',1)",
              (sess["月曜1限 中学応用"], f"{MON_OLD.month}/{MON_OLD.day}", f"https://youtu.be/{V_MON_OLD}"))
    c.execute("INSERT INTO class_recordings (session_id, title, video_url, provider, is_published) "
              "VALUES (?,?,?,'youtube',1)",
              (sess["月曜1限 中学応用"], "合同", f"https://youtu.be/{V_SHARED}"))
    conn.commit()
    conn.close()

    client = TestClient(mod.app)
    tok = admin_token(mod)
    URL = "/api/admin/class-recordings/auto-assign"

    def call(body, auth=True):
        mod._RATE_LIMIT_STORE.clear()      # 連続実行で 429 にしない (見たいのは割り当ての側)
        h = {"Authorization": f"Bearer {tok}"} if auth else {}
        return client.post(URL, json=body, headers=h)

    def count_recordings():
        cn = mod.db()
        try:
            cur = cn.cursor()
            cur.execute("SELECT COUNT(*) AS n FROM class_recordings")
            return cur.fetchone()["n"]
        finally:
            cn.close()

    print("授業録画 自動割り当て API:")

    # 1. 未認証
    check("未認証は 401", call({}, auth=False).status_code == 401)

    # 2. dry-run は書き込まない
    before = count_recordings()
    r = call({})
    dry = r.json()
    check("dry-run が 200 を返す", r.status_code == 200, f"status={r.status_code}")
    check("dry-run で1件も書き込まない", count_recordings() == before,
          f"{before} → {count_recordings()}")
    check("dry-run の mode が dry-run", dry.get("mode") == "dry-run")
    slots = sorted(p["slot"] for p in dry.get("planned", []))
    check("新着2件 (月曜1限・火曜1限) を計画する", slots == sorted(["月曜1限", "火曜1限"]), f"planned={slots}")

    # 3. 取得できない再生リストを「新着なし」にしない
    probs = " / ".join(dry.get("problems", []))
    dead_row = [r_ for r_ in dry["rows"] if r_["slot"] == "水曜1限"]
    check("取得できない再生リストは「0本」でなく「取得できず」になる",
          len(dead_row) == 1 and dead_row[0]["ok"] is False, str(dead_row)[:80])
    check("取得できない理由が確認事項に出る",
          any(p_.startswith("水曜1限:") and "接続できない" in p_ for p_ in dry["problems"]), probs[:80])
    check("取得できない分は登録を止める扱い", dry.get("blocking", 0) >= 1, f"blocking={dry.get('blocking')}")
    check("見に行けた授業だけを数える (取得失敗は数えない)",
          dry["summary"]["covered"] == 2 and dry["summary"]["sessions_total"] == 3,
          f"covered={dry['summary']['covered']}/{dry['summary']['sessions_total']}")

    # 4. 別クラスに登録済みの動画を勝手に足さない
    check("別クラス登録済みの動画は計画に入らない",
          all(p["label"] != "合同" for p in dry["planned"]) and "別の授業に登録されている" in probs)

    # 5. 動画IDの生値を返さない
    body_text = json.dumps(dry, ensure_ascii=False)
    leaked = [v for v in (V_MON_NEW, V_TUE_NEW, V_SHARED, V_MON_OLD) if v in body_text]
    check("応答に動画IDの生値が載らない", not leaked, f"leaked={leaked}")

    # 6. blocking があるうちは apply しても登録しない
    r = call({"apply": True})
    check("確認事項があるうちは登録を拒否する", r.json().get("applied") == 0 and r.json().get("refused"),
          str(r.json().get("refused"))[:60])
    check("拒否のときも1件も書き込まない", count_recordings() == before)

    # 7. allow_partial で取れた分だけ登録 → 各1件・URL が読み戻せる
    r = call({"apply": True, "allow_partial": True})
    ap = r.json()
    check("取れた分だけ登録できる", ap.get("applied") == 2, f"applied={ap.get('applied')}")
    check("登録後の読み直しで重複なし", ap.get("verified") is True and not ap.get("duplicates"))
    check("2件増えている", count_recordings() == before + 2, f"{before} → {count_recordings()}")
    cn = mod.db()
    cur = cn.cursor()
    cur.execute("SELECT session_id, title, video_url FROM class_recordings ORDER BY id")
    rows = cur.fetchall()
    cn.close()
    urls = [r_["video_url"] for r_ in rows]
    check("書いた URL は video_id() で読み戻せる",
          all(core.video_id(u) for u in urls), f"読めない={[u for u in urls if not core.video_id(u)]}")
    new_mon = [r_ for r_ in rows if core.video_id(r_["video_url"]) == V_MON_NEW]
    check("月曜の新着が月曜のクラスに1件だけ入る",
          len(new_mon) == 1 and new_mon[0]["session_id"] == sess["月曜1限 中学応用"])
    check("日付ラベルが動画名から取れている",
          new_mon and new_mon[0]["title"] == f"{MON_D.month}/{MON_D.day}",
          new_mon[0]["title"] if new_mon else "")

    # 8. もう一度実行しても増えない (二重登録しない)
    n_before = count_recordings()
    r2 = call({"apply": True, "allow_partial": True})
    check("2回目は新着0件", r2.json().get("applied") == 0, f"applied={r2.json().get('applied')}")
    check("2回目で行が増えない", count_recordings() == n_before, f"{n_before} → {count_recordings()}")

    # 9. 同時実行を弾く
    mod._AUTO_ASSIGN_LOCK.acquire()
    try:
        check("実行中の同時実行は 409", call({}).status_code == 409)
    finally:
        mod._AUTO_ASSIGN_LOCK.release()

    if FAILURES:
        print(f"\n❌ VIOLATION: {len(FAILURES)} 件")
        for f in FAILURES:
            print(f"   - {f}")
        return 1
    print("\n=== ALL PASS (認証・dry-run・登録・二重登録防止・取得失敗・伏せ字・排他) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
