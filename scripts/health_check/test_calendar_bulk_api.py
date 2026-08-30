#!/usr/bin/env python3
"""📅 塾カレンダー一括入力 API (POST /api/admin/class/calendar/bulk) の回帰テスト。

背景 (2026-08-30):
  塾生アプリ「予定」タブのカレンダー (休塾日・特別予定) は CEO 画面から1件ずつ登録していた。
  1か月ぶんが 10件を超えると往復が多すぎるので一括入力を足した。**書き込む側**なので
  次の性質を機械で固定する。

  1. 未認証では動かない
  2. 既定は dry-run — **1件も書き込まない**
  3. 日付の読み方 (年の省略・全角・和暦風の「9月3日」・行頭以外の余計な文字) が意図どおり
  4. ★曜日を必ず返す。塾長が日付の打ち間違いに気づける唯一の手がかりがこれ
  5. ★塾生アプリは**1日1件しか表示できない** (class.html の calEvents は日付キーの連想配列)。
     同じ日を二重に入れない・既存を黙って上書きしない
  6. ★エラーが1件でもあれば**1件も書かない**。半分だけ入った月は誰にも検証できない
  7. 二度実行しても増えない (idempotent)
  8. 「休塾日(理由)」の理由に「休塾日」を残さない (画面が "🔴 休塾日（理由）" と組むので二重になる)

実行:
    python3 scripts/health_check/test_calendar_bulk_api.py
    # exit 0 = PASS / 1 = FAIL

外部通信は一切しない。DB は一時 SQLite。
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
JST = datetime.timezone(datetime.timedelta(hours=9))


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {detail}" if detail else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="calbulk_"), "test.db")
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
    spec = importlib.util.spec_from_file_location("aijuku_main_calbulk", MAIN_PY)
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


def main():
    mod = load_main()
    from fastapi.testclient import TestClient
    cli = TestClient(mod.app)
    URL = "/api/admin/class/calendar/bulk"
    H = {"Authorization": "Bearer " + admin_token(mod)}
    today = datetime.datetime.now(JST).date()

    def post(text, apply=False):
        return cli.post(URL, json={"text": text, "apply": apply}, headers=H)

    def count_rows():
        conn = mod.db()
        try:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) AS n FROM class_calendar")
            return c.fetchone()["n"]
        finally:
            conn.close()

    print("塾カレンダー 一括入力 API:")
    check("未認証は 401", cli.post(URL, json={"text": "9/18 休塾日"}).status_code == 401)

    # ---- 日付の読み方 (年の省略は「今日以降のいちばん近い同じ月日」) ----
    #   ★実行日によらず同じ結論になるよう、今日からの相対で作る。
    d1 = today + datetime.timedelta(days=10)
    d2 = today + datetime.timedelta(days=11)
    DOW = "月火水木金土日"
    text = (f"# これはコメント行\n"
            f"\n"
            f"{d1.month}/{d1.day} 休塾日(年間調整日)\n"
            f"{d2.month}月{d2.day}日 アーカイブ配信（LIVE授業なし）\n")
    r = post(text)
    d = r.json()
    check("dry-run が 200 を返す", r.status_code == 200, f"status={r.status_code}")
    check("dry-run で1件も書き込まない", count_rows() == 0, f"rows={count_rows()}")
    check("dry-run の mode が dry-run", d.get("mode") == "dry-run")
    check("コメント行と空行は無視する", len(d["rows"]) == 2, f"rows={len(d['rows'])}")
    rows = {x["date"]: x for x in d["rows"]}
    check("年を省いた日付を今日以降で解決する",
          d1.isoformat() in rows and d2.isoformat() in rows, str(list(rows)))
    check("★曜日を返す (打ち間違いに気づける唯一の手がかり)",
          rows[d1.isoformat()]["weekday"] == DOW[d1.weekday()],
          f"{rows[d1.isoformat()]['weekday']} (正 {DOW[d1.weekday()]})")
    check("「休塾日(理由)」を closed + 理由だけに分ける",
          rows[d1.isoformat()]["kind"] == "closed" and rows[d1.isoformat()]["title"] == "年間調整日",
          f"kind={rows[d1.isoformat()]['kind']} title={rows[d1.isoformat()]['title']!r}")
    # ★塾長が書いた文字をそのまま残すこと。NFKC を丸ごとかけると「（LIVE授業なし）」の
    #   全角括弧が半角になる = 生徒に見えるのは塾長の文章なので勝手に整形しない。
    check("「9月3日」形式を読み、全角括弧をそのまま残す",
          rows[d2.isoformat()]["kind"] == "event"
          and rows[d2.isoformat()]["title"] == "アーカイブ配信（LIVE授業なし）",
          f"kind={rows[d2.isoformat()]['kind']} title={rows[d2.isoformat()]['title']!r}")
    # 全角数字・全角スラッシュで書いても同じ日付として読めること
    r_z = post(f"{d1.month}／{d1.day} 休塾日(年間調整日)".translate(
        str.maketrans("0123456789", "０１２３４５６７８９"))).json()
    check("全角数字・全角スラッシュの日付を読む",
          r_z["rows"] and r_z["rows"][0]["date"] == d1.isoformat(),
          str(r_z["rows"][0].get("date") or r_z["rows"][0].get("error")))

    # ---- 登録 ----
    r = post(text, apply=True).json()
    check("apply で登録される", r["applied"] == 2 and count_rows() == 2, f"applied={r['applied']} rows={count_rows()}")
    check("登録後の読み直しで重複なし", r.get("verified") is True, str(r.get("duplicates")))

    # ---- 二度押しで増えない ----
    r = post(text, apply=True).json()
    check("★同じ内容をもう一度入れても増えない",
          r["applied"] == 0 and r["same"] == 2 and count_rows() == 2,
          f"applied={r['applied']} same={r['same']} rows={count_rows()}")

    # ---- 既存と違う内容は黙って上書きしない ----
    r = post(f"{d1.month}/{d1.day} 予定: 別の予定に変える", apply=True).json()
    check("★既存と違う内容は上書きせず止める", r["conflict"] == 1 and r["applied"] == 0 and count_rows() == 2,
          f"conflict={r['conflict']} applied={r['applied']} rows={count_rows()}")
    check("止めた理由に既存の中身を出す",
          any("年間調整日" in (x.get("error") or "") for x in r["rows"]), str(r["rows"][0].get("error")))

    # ---- 1件でもエラーがあれば1件も書かない ----
    d3 = today + datetime.timedelta(days=12)
    before = count_rows()
    r = post(f"{d3.month}/{d3.day} 休塾日\nこの行は日付ではない\n", apply=True).json()
    check("★エラーが1件でもあれば1件も書かない", r["applied"] == 0 and count_rows() == before,
          f"applied={r['applied']} rows={count_rows()}→{before}")
    check("読めない行を理由つきで返す",
          any(x.get("error") and x["date"] is None for x in r["rows"]))

    # ---- 同じ入力の中の重複 ----
    r = post(f"{d3.month}/{d3.day} 休塾日\n{d3.month}/{d3.day} 予定: ぶつかる\n", apply=True).json()
    check("★同じ入力の中に同じ日付が2回あれば止める", r["applied"] == 0 and count_rows() == before,
          f"applied={r['applied']}")

    # ---- 予定にタイトルが無い / 存在しない日付 ----
    r = post("2026-02-30 休塾日\n2027-03-04\n").json()
    check("存在しない日付を弾く", any("存在しない日付" in (x.get("error") or "") for x in r["rows"]))
    check("タイトルの無い予定を弾く", any("タイトル" in (x.get("error") or "") for x in r["rows"]))

    # ---- 1件ずつの登録欄も同じ日を二重に入れない ----
    #   ★塾生アプリは1日1件しか表示しないので、2件目はどちらが出るか決まらないまま
    #     画面から消える = 登録したのに反映されない、という直しようのない状態になる。
    d9 = today + datetime.timedelta(days=40)
    one = {"event_date": d9.isoformat(), "kind": "closed", "title": "単発テスト"}
    r1 = cli.post("/api/admin/class/calendar", json=one, headers=H)
    n_after_first = count_rows()
    r2 = cli.post("/api/admin/class/calendar", json=one, headers=H)
    check("★1件ずつの登録も同じ日を二重に入れない",
          r1.status_code == 200 and r2.status_code == 409 and count_rows() == n_after_first,
          f"1回目={r1.status_code} 2回目={r2.status_code} rows={count_rows()}")

    # ---- 空入力 ----
    r = post("   \n\n").json()
    check("空入力でも落ちない", r["ok"] is True and r["applied"] == 0)

    if FAILURES:
        print(f"\n❌ VIOLATION: {len(FAILURES)} 件")
        for f in FAILURES:
            print(f"   - {f}")
        return 1
    print("\n=== ALL PASS (認証・dry-run・日付解釈・曜日・上書き防止・全か無か・二度押し) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
