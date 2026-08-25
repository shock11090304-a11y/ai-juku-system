#!/usr/bin/env python3
"""📺 再生リストの登録/命名 API (POST /api/admin/youtube-playlists) の回帰テスト。

背景 (2026-08-25 塾長依頼「この YouTube のリンクを日曜日国語に埋め込んで」):
  新しく作った再生リストは admin_youtube_playlists に行が無いので一覧に出ず、
  **名前を付ける場所が画面に無かった** (保存 API 自体は新規 INSERT に対応していたのに、
  押すボタンが存在しなかった)。youtube-playlists.html に追加フォームを足したので、
  その土台になる API の性質を機械で固定する。

  この画面の目的は「保存すること」ではなく **自動割り当てに繋ぐこと**。名前から曜日+限を
  読めない再生リストは丸ごと対象外になるので (server/class_recording_assign.py の slot_of)、
  保存 API は「どの授業に繋がるか」まで返し、画面がそれを出す。返さなくなると
  「名前を付けたのに配布漏れ」が緑のまま見逃される。

固定する性質:
  1. 未認証では登録できない (再生リストIDは限定公開録画へのアクセス権)
  2. 再生リストの **URL をそのまま** 受け取れる (&si= 等の追跡パラメータ付きでも)
  3. 同じ再生リストを二度送っても**増えない** (created=False = 名前の更新になる)
  4. 読み取れない入力は 400 で断る。DB に半端な行を作らない
  5. 名前 → 授業の対応 (slot / target_slot / session_title) を返す
     ★判定は class_recording_assign.slot_of() が正典。ここが独自判定に化けていないことを、
       正典を直接呼んだ結果と突き合わせて確認する
  6. 曜日+限を読めない名前でも保存は成功するが、slot=None を返して画面に警告させる
  7. 日曜の別名扱い (SLOT_OVERRIDE「日曜1限」→「日曜」) が API 経由でも効く
  8. 公開中の授業が無い / 複数該当する場合を、繋がった場合と区別して返す

実行:
    python3 scripts/health_check/test_playlist_save_api.py
    # exit 0 = PASS / 1 = FAIL

外部通信は一切しない (YouTube は見に行かない)。DB は一時 SQLite。
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []

# ★このリポジトリは PUBLIC。**本物の再生リストIDは絶対に書かない** (限定公開録画への
#   アクセス権そのもの)。形式だけ合わせた架空の値を使う。
FAKE_PID = "PLtest0000000000000000000000000000"
FAKE_PID2 = "PLtest1111111111111111111111111111"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {detail}" if detail else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    """一時 SQLite + ダミー env で server/main.py を in-process ロード。"""
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="ytsave_"), "test.db")
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
    spec = importlib.util.spec_from_file_location("aijuku_main_ytsave", MAIN_PY)
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


def row_count(mod):
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) AS n FROM admin_youtube_playlists")
    n = c.fetchone()["n"]; conn.close()
    return n


def make_session(mod, title, published=1):
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO class_sessions (title, is_published) VALUES (?, ?)", (title, published))
    conn.commit(); conn.close()


def main():
    print("📺 再生リスト登録/命名 API 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    hdr = {"Authorization": f"Bearer {admin_token(mod)}"}
    save = lambda body, h=hdr: client.post("/api/admin/youtube-playlists", json=body, headers=(h or {}))

    # 日曜の授業を 1 つだけ公開しておく (本番と同じ「日曜 高校国語」の形)
    make_session(mod, "日曜 高校国語")

    # ============================================================
    print("1. 未認証では登録できない")
    r = client.post("/api/admin/youtube-playlists", json={"id": FAKE_PID, "name": "日曜日1時間目"})
    check("認証なしは 401/403", r.status_code in (401, 403), f"status={r.status_code}")
    check("DB に行を作らない", row_count(mod) == 0, f"rows={row_count(mod)}")

    # ============================================================
    print("\n2. 再生リストの URL をそのまま貼れる (&si= 付きでも)")
    url = f"https://youtube.com/playlist?list={FAKE_PID}&si=AbCdEfGhIjKlMnOp"
    r = save({"id": url, "name": "8月以降日曜日1時間目"})
    check("HTTP 200", r.status_code == 200, f"status={r.status_code} body={r.text[:200]}")
    d = r.json() if r.status_code == 200 else {}
    check("URL から再生リストIDを抜き出す", d.get("playlist_id") == FAKE_PID, f"playlist_id={d.get('playlist_id')}")
    check("追跡パラメータ (si) を ID に混ぜない", "si" not in (d.get("playlist_id") or ""))
    check("新規登録として扱う", d.get("created") is True, f"created={d.get('created')}")
    check("1 行だけ増える", row_count(mod) == 1, f"rows={row_count(mod)}")

    # ============================================================
    print("\n3. 名前 → 授業の対応を返す (日曜の別名扱いを含む)")
    check("slot を返す", d.get("slot") == "日曜1限", f"slot={d.get('slot')}")
    check("SLOT_OVERRIDE で日曜に寄せる", d.get("target_slot") == "日曜", f"target_slot={d.get('target_slot')}")
    check("繋がる授業名を返す", d.get("session_title") == "日曜 高校国語", f"session_title={d.get('session_title')}")
    # ★判定が独自実装に化けていないこと (正典と同じ答えか) を直接突き合わせる
    sys.path.insert(0, os.path.join(REPO, "server"))
    import class_recording_assign as cra
    canon = cra.slot_of("8月以降日曜日1時間目")
    check("正典 slot_of と同じ判定", bool(canon) and canon[1] == d.get("slot") and canon[2] == d.get("target_slot"),
          f"canon={canon} api=({d.get('slot')}, {d.get('target_slot')})")

    # ============================================================
    print("\n4. 同じ再生リストを二度送っても増えない (名前の更新になる)")
    r = save({"id": f"https://www.youtube.com/playlist?list={FAKE_PID}", "name": "8月以降日曜日1限"})
    d2 = r.json()
    check("HTTP 200", r.status_code == 200, f"status={r.status_code}")
    check("新規ではなく更新", d2.get("created") is False, f"created={d2.get('created')}")
    check("行が増えない", row_count(mod) == 1, f"rows={row_count(mod)}")
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT name FROM admin_youtube_playlists WHERE playlist_id = ?", (FAKE_PID,))
    check("名前が上書きされている", (c.fetchone() or {"name": ""})["name"] == "8月以降日曜日1限")
    conn.close()

    # ============================================================
    print("\n5. 読み取れない入力は断る。半端な行を作らない")
    before = row_count(mod)
    for bad, why in [("", "空"), ("https://www.youtube.com/watch?v=abcdefghijk", "動画URL (list= が無い)"),
                     ("not a playlist!", "記号混じり")]:
        r = save({"id": bad, "name": "日曜日1時間目"})
        check(f"400 で断る ({why})", r.status_code == 400, f"status={r.status_code}")
    check("断った分は DB に入っていない", row_count(mod) == before, f"rows={row_count(mod)} (前 {before})")

    # ============================================================
    print("\n6. 曜日+限を読めない名前 — 保存はするが「対象外」と返す")
    r = save({"id": FAKE_PID2, "name": "英文法まとめ"})
    d3 = r.json()
    check("HTTP 200 (保存自体は成功)", r.status_code == 200, f"status={r.status_code}")
    check("slot は None (自動割り当ての対象外)", d3.get("slot") is None, f"slot={d3.get('slot')}")
    check("繋がる授業も返さない", d3.get("session_title") is None, f"session_title={d3.get('session_title')}")
    check("行は作られる", row_count(mod) == before + 1, f"rows={row_count(mod)}")

    # ============================================================
    print("\n7. 対応する公開中の授業が無い / 複数ある を区別する")
    r = save({"id": FAKE_PID2, "name": "水曜日2時間目"})   # 水曜の授業は作っていない
    d4 = r.json()
    check("授業0件を session_count=0 で返す", d4.get("session_count") == 0, f"session_count={d4.get('session_count')}")
    check("繋がる授業名は返さない", d4.get("session_title") is None, f"session_title={d4.get('session_title')}")
    check("slot 自体は読めている", d4.get("slot") == "水曜2限", f"slot={d4.get('slot')}")

    make_session(mod, "水曜2限 数学")
    make_session(mod, "水曜2限 英語")
    r = save({"id": FAKE_PID2, "name": "水曜日2時間目"})
    d5 = r.json()
    check("授業が複数該当したら件数を返す", d5.get("session_count") == 2, f"session_count={d5.get('session_count')}")
    check("どれか1つを勝手に選ばない", d5.get("session_title") is None, f"session_title={d5.get('session_title')}")

    # ★非公開の授業は数えない (登録しても誰にも見えないため)
    make_session(mod, "土曜1限 理科", published=0)
    r = save({"id": FAKE_PID2, "name": "土曜日1時間目"})
    d6 = r.json()
    check("非公開の授業は繋がり先に数えない", d6.get("session_count") == 0, f"session_count={d6.get('session_count')}")

    print("\n" + "=" * 60)
    if FAILURES:
        print(f"❌ FAIL — {len(FAILURES)} 件")
        for f in FAILURES:
            print(f"   - {f}")
        return 1
    print("✅ ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
