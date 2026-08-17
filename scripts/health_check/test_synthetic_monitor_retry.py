#!/usr/bin/env python3
"""E2E 合成監視の「一過性 502 で誤発報しない / 本物は必ず捕まえる」回帰テスト。

背景 (2026-08-18):
  5分おきの申込→決済 E2E 監視が 2026-08-18 00:17 JST に 1 サイクルだけ失敗し、
  塾長に「🚨 申込→決済 E2E 監視 失敗 — 即時対応必要」が深夜に飛んだ。
  実体は Railway edge の一過性 502 (`upstream error`) で、次サイクルで自動復帰。
  リクエストはアプリのハンドラに 1 度も到達していなかった
  (sentinel の student_id が 33899 → 33900 と連番のまま = INSERT を試行すらしていない)。
  過去14日 4017 サイクル中の失敗 2 件が両方ともこれ。

  真因は `_http_post_json` が `urllib.error.HTTPError` を retry 対象外にしていたこと。
  502/503/504 は「サーバーの判断」ではなく edge が「アプリに繋げなかった」と言っているだけ。

このテストが守るもの:
  1. 1 回だけ 502 → retry して成功し、**発報しない** (誤報が消えている)
  2. ずっと 502 → 従来どおり failure (**検知能力が落ちていない**)
  3. 404 等のコード退化クラス → retry せず即 failure (**遅延ゼロが維持されている**)
  4. details に試行回数が残る (次に同じ調査をするとき推測で終わらせない)

実行:
    python3 scripts/health_check/test_synthetic_monitor_retry.py
    # exit 0 = PASS / 1 = FAIL

外部通信は一切しない (urlopen を差し替える)。DB は一時 SQLite。
"""
import asyncio
import importlib.util
import inspect
import io
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")

FAILURES = []


def check(label: str, cond: bool, detail: str = ""):
    mark = "✅" if cond else "❌"
    print(f"  {mark} {label}" + (f"  — {detail}" if detail else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    """一時 SQLite + ダミー env で server/main.py を in-process ロード。"""
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="synthmon_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL は必ず空にする。USE_POSTGRES は DATABASE_URL の有無だけで決まり、
        #   立っていると DB_PATH は無視されて **本番 Postgres** に init_db の ALTER TABLE と
        #   テスト用 events の INSERT が流れる。このディレクトリの prod_healthcheck.py は
        #   `railway run -s Postgres python3 ...` で叩く流儀なので、真似されると事故になる。
        "DATABASE_URL": "",
        # ★STRIPE_SECRET_KEY も空に。_collect_health_snapshot が
        #   _lookup_founder_special_price_id() 経由で Stripe API を叩きに行く (外部通信)。
        "STRIPE_SECRET_KEY": "",
        "STRIPE_PRICE_PREMIUM": "price_test_dummy",
        "MONITORING_ENABLED": "0",       # スケジューラは起動しない (直接関数を呼ぶ)
        # ★起動30秒後の post-deploy smoke test は **本番 URL** へ申込 POST を撃つので必ず切る
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        # 出題生成スケジューラも切る (既定 ON・起動30秒後に Anthropic を叩きにいく)
        "EXAM_QUESTIONS_ENABLED": "0",
        "MONITORING_TO_EMAIL": "",       # 送信先なし
        "RESEND_API_KEY": "",            # _send_monitor_email は即 {"sent": False}
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_under_test", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


# --- 偽 urlopen -------------------------------------------------------------
# 監視が叩く 4 本 (lp.html / checkout.html / checkout.js / POST signup) に
# 「本物なら通る」応答を返す。signup だけテストごとに壊す。

CHECKOUT_JS = (
    "function f(){ const target = document.querySelector('#x');"
    " if (target) { target.value = __urlPlanOverride; } }"
    " form.addEventListener('submit', f);"
)
SENTINEL_ID = 999999


class _FakeResp(io.BytesIO):
    def __init__(self, body: bytes, status: int = 200):
        super().__init__(body)
        self.status = status
        self.headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def make_urlopen(signup_behavior, lp_status=200, vercel_api=("ok", 200)):
    """signup_behavior(call_index) -> ('ok'|'http', code) を返す関数で signup の挙動を決める。
    lp_status / vercel_api で「Vercel 経由の rewrite だけ落ちている」状況も作れる。"""
    state = {"signup_calls": 0, "health_calls": 0}

    def fake_urlopen(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if url.endswith("/api/health"):
            # list を渡すと呼び出しごとに挙動を変えられる (retry の検証用)
            seq = vercel_api if isinstance(vercel_api, list) else [vercel_api]
            kind, code = seq[min(state["health_calls"], len(seq) - 1)]
            state["health_calls"] += 1
            if kind == "http":
                raise urllib.error.HTTPError(url, code, "err", {}, io.BytesIO(b"err"))
            if kind == "net":
                raise OSError("connection refused")
            if kind == "html":  # 200 だが JSON でない (checkpoint / SPA fallback)
                return _FakeResp(b"<html>checkpoint</html>")
            return _FakeResp(b'{"status":"ok"}')
        if url.endswith("/lp.html"):
            if lp_status != 200:
                raise urllib.error.HTTPError(url, lp_status, "err", {}, io.BytesIO(b"err"))
            return _FakeResp('<a href="checkout.html">申し込む</a>'.encode())
        if url.endswith("/checkout.html"):
            return _FakeResp(b'<script src="checkout.js?v=20260818"></script>')
        if "checkout.js" in url:
            return _FakeResp(CHECKOUT_JS.encode())
        if url.endswith("/api/trial/signup"):
            state["signup_calls"] += 1
            kind, code = signup_behavior(state["signup_calls"])
            if kind == "http":
                raise urllib.error.HTTPError(url, code, "upstream error", {},
                                            io.BytesIO(b"upstream error"))
            return _FakeResp(json.dumps(
                {"student_id": SENTINEL_ID, "email_sent": True}).encode())
        raise AssertionError(f"想定外の URL を叩いている: {url}")

    return fake_urlopen, state


def seed_signup_event(mod):
    """signup 成功後に監視が確認する events 行を先に置く (HTTP を偽装しているため)。"""
    conn = mod.db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
        ("signup_email_status",
         json.dumps({"student_id": SENTINEL_ID, "email_sent": True}),
         f"student:{SENTINEL_ID}"),
    )
    conn.commit()
    conn.close()


def run_cycle(mod, signup_behavior, **kw):
    fake, state = make_urlopen(signup_behavior, **kw)
    real = urllib.request.urlopen
    urllib.request.urlopen = fake
    try:
        # alert=False: このテストからはメールを一切発火させない
        result = asyncio.run(mod._run_synthetic_checkout_test(alert=False))
    finally:
        urllib.request.urlopen = real
    return result, state


def main():
    print("E2E 合成監視 — 一過性 502 の retry / 本物の検知 回帰テスト")
    print(f"  対象: {MAIN_PY}")
    mod = load_main()
    # ★本番汚染の栓が生きていること。この env ゲートを消すと、uvicorn を起動する
    #   テスト (test_event_loop_blocking.py) や CI が **本番の students に sentinel を作る**。
    check("POST_DEPLOY_SMOKE_ENABLED の env ゲートが存在し、テスト時は切れている",
          getattr(mod, "POST_DEPLOY_SMOKE_ENABLED", None) is False)
    # ★定数があるだけでは意味がない。startup が実際にそれで分岐していることを見る
    #   (if を消しても定数は残るので、存在チェックだけだと嘘の緑になる)。
    check("startup が POST_DEPLOY_SMOKE_ENABLED で分岐している",
          "if POST_DEPLOY_SMOKE_ENABLED:" in inspect.getsource(mod._start_background_tasks))
    seed_signup_event(mod)

    # --- 1. 1回だけ 502 → retry して成功・発報しない ---------------------
    print("\n[1] 1回だけ 502 (2026-08-18 00:17 の再現) → 誤発報しないこと")
    res, st = run_cycle(mod, lambda n: ("http", 502) if n == 1 else ("ok", 200))
    check("ok=True (アラートが飛ばない)", res["ok"] is True, f"failures={res['failures']}")
    check("signup を 2 回叩いた (retry した)", st["signup_calls"] == 2,
          f"calls={st['signup_calls']}")
    check("details.signup_attempts=2 が残る", res["details"].get("signup_attempts") == 2,
          f"attempts={res['details'].get('signup_attempts')}")

    # --- 2. ずっと 502 → 従来どおり failure ------------------------------
    print("\n[2] 502 が継続 (本物のインフラ障害) → 必ず捕まえること")
    seed_signup_event(mod)
    res, st = run_cycle(mod, lambda n: ("http", 502))
    check("ok=False (検知能力が落ちていない)", res["ok"] is False)
    check("failures に 502 が入る",
          any("status=502" in f for f in res["failures"]), f"{res['failures']}")
    check("retries を使い切る (3 試行)", st["signup_calls"] == 3, f"calls={st['signup_calls']}")
    check("details.signup_attempts=3", res["details"].get("signup_attempts") == 3)

    # --- 3. 404 (コード退化クラス) → retry せず即 failure ------------------
    print("\n[3] 404 (route 消失 = コード退化) → retry せず即発報 (遅延ゼロ維持)")
    seed_signup_event(mod)
    res, st = run_cycle(mod, lambda n: ("http", 404))
    check("ok=False", res["ok"] is False)
    check("signup は 1 回だけ (retry しない)", st["signup_calls"] == 1,
          f"calls={st['signup_calls']}")
    check("details.signup_attempts=1", res["details"].get("signup_attempts") == 1)

    # --- 3B. Vercel rewrite (実ユーザーの API 経路) の疎通 -------------------
    print("\n[3B] Vercel 経由の API が落ちたら捕まえる / 内部接続の偽陽性は鳴らさない")
    seed_signup_event(mod)
    res, _ = run_cycle(mod, lambda n: ("ok", 200), vercel_api=("http", 502))
    check("静的は200なのに Vercel 経由 API が 502 → failure",
          not res["ok"] and any("Vercel 経由" in f for f in res["failures"]),
          f"{res['failures']}")
    # ★GET 側にも 502/503/504 の retry が要る。無いと「POST 側で消した誤報を
    #   GET 側で作り直す」ことになる (Vercel 経由は Railway edge の別 PoP を通る)。
    seed_signup_event(mod)
    res, st3 = run_cycle(mod, lambda n: ("ok", 200),
                         vercel_api=[("http", 502), ("ok", 200)])
    check("Vercel 経由 API の 1 回だけの 502 は retry して誤報にしない",
          res["ok"] and st3["health_calls"] == 2,
          f"ok={res['ok']} calls={st3['health_calls']} failures={res['failures']}")
    seed_signup_event(mod)
    res, _ = run_cycle(mod, lambda n: ("ok", 200), vercel_api=("html", 200))
    check("200 でも JSON でなければ rewrite 不通として捕まえる",
          not res["ok"] and any("JSON" in f for f in res["failures"]), f"{res['failures']}")
    seed_signup_event(mod)
    res, _ = run_cycle(mod, lambda n: ("ok", 200), vercel_api=("net", 0))
    check("Railway→Vercel の内部接続失敗は warning (既知の偽陽性・鳴らさない)",
          res["ok"] and any("内部接続" in w for w in res["warnings"]),
          f"failures={res['failures']} warnings={res['warnings']}")
    seed_signup_event(mod)
    res, _ = run_cycle(mod, lambda n: ("ok", 200), lp_status=503, vercel_api=("http", 502))
    check("静的も落ちているなら API 側は warning へ格下げ (Vercel 全体の不調と区別)",
          not any("Vercel 経由" in f for f in res["failures"]), f"{res['failures']}")

    # --- 4. auto-rollback の分類と発報の整合 ------------------------------
    print("\n[4] 失敗クラスの分類 (rollback 判定と矛盾していないこと)")
    check("502 は外部/一過性に分類される",
          mod._failures_are_all_external(["/api/trial/signup status=502 body=upstream error"]) is True)
    check("fix marker 消失はコード退化に分類される",
          mod._failures_are_all_external(["checkout.js missing fix marker: 'if (target)'"]) is False)
    # Vercel 側の設定 (Attack Challenge / Deployment Protection) は revert で直らない
    check("Vercel 経由の失敗は外部扱い (rollback しない・通知は出る)",
          mod._failures_are_all_external(
              ["Vercel 経由 /api/health status=403 (静的は 200 = rewrite だけが不通)"]) is True)
    check("Vercel 経由 + コード退化が同時なら rollback 対象のまま",
          mod._failures_are_all_external(
              ["Vercel 経由 /api/health status=403",
               "checkout.js missing fix marker: 'if (target)'"]) is False)

    # --- 5. 通知の件名に中身が入る ----------------------------------------
    print("\n[5] アラートメールの件名 (受信箱で中身が分かること)")
    # snapshot は実物を使う (手書き dict だとキー欠落でテスト側が先に落ちる)
    snap = mod._collect_health_snapshot()
    subj1, _ = mod._format_alert_email(
        [{"key": "k1", "severity": "warning", "title": "⚠️ 過去24時間 申込ゼロ", "detail": "d"}], snap)
    check("1件なら件名に title が入る", "過去24時間 申込ゼロ" in subj1, subj1)
    check("汎用文言だけの件名ではない", "監視アラート (1件)" not in subj1, subj1)
    subj2, _ = mod._format_alert_email([
        {"key": "k1", "severity": "critical", "title": "🚨 A が壊れた", "detail": "d"},
        {"key": "k2", "severity": "warning", "title": "⚠️ B", "detail": "d"},
    ], snap)
    check("複数件でも先頭 title が入る", "A が壊れた" in subj2 and "2件" in subj2, subj2)

    # --- 6. no_signups_24h はメールを出さない (バナーには出る) --------------
    print("\n[6] 「過去24時間 申込ゼロ」= 平常値なのでメールしない (表示は維持)")
    # 空 DB = 申込ゼロ + ローンチから十分経過 → no_signups_24h が必ず立つ状況
    snap2 = dict(snap)
    snap2["signups_24h"] = 0
    alerts = mod._evaluate_alerts(snap2)
    ns = [a for a in alerts if a["key"] == "no_signups_24h"]
    check("no_signups_24h は依然として生成される (バナー用)", len(ns) == 1)
    if ns:
        check("severity=info", ns[0]["severity"] == "info", f"severity={ns[0]['severity']}")

    # ★severity 文字列を見るだけでは「抑止機構そのものを消された」ことを検出できない。
    #   _run_monitor_check を実際に走らせて、メールが出ないことを確かめる。
    sent = []
    real_send = mod._send_monitor_email
    mod._send_monitor_email = lambda s, h, to_email=None: (sent.append(s), {"sent": True})[1]
    try:
        res_chk = mod._run_monitor_check()
    finally:
        mod._send_monitor_email = real_send
    check("_run_monitor_check が no_signups_24h をメールしない",
          "no_signups_24h" not in res_chk["alerts_sent"], f"sent={res_chk['alerts_sent']}")
    check("info として抑止された記録が残る",
          "no_signups_24h" in res_chk["alerts_info_suppressed"],
          f"suppressed={res_chk['alerts_info_suppressed']}")

    # --- 7. 降格で空いた穴を埋める新アラート ------------------------------
    print("\n[7] 「送信されたのに API に届いていない」= 故障クラスをバナーに出すこと")
    # ★snapshot が実際にこのキーを埋めることを先に確かめる。
    #   本体は .get(key, 0) の fail-open なので、キーが消える/改名されると
    #   「送信があるたび毎回発報」に化けるのに、辞書を手で組むテストでは緑のまま通ってしまう。
    for k in ("form_submit_checkout_6h", "signups_6h", "checkout_initiated_6h"):
        check(f"_collect_health_snapshot が {k} を持つ", k in snap)

    def keys_for(**over):
        s = dict(snap)
        s.update(over)
        return {a["key"]: a for a in mod._evaluate_alerts(s)}

    NG = keys_for(form_submit_checkout_6h=3, signups_6h=0, checkout_initiated_6h=0)
    check("signup_submitted_no_record が立つ", "signup_submitted_no_record" in NG)
    if "signup_submitted_no_record" in NG:
        # ★過去の発火 2 件はどちらも本物と確認できなかった。的中率が未証明のものを
        #   メールにすると alert fatigue を作り直すので、まずバナー限定で運用する。
        check("severity=info (バナー限定・まだメールしない)",
              NG["signup_submitted_no_record"]["severity"] == "info",
              NG["signup_submitted_no_record"]["severity"])
        check("cooldown は窓長と揃えて 360分 (1イベントで6通鳴らさない)",
              NG["signup_submitted_no_record"].get("cooldown_min") == 360,
              str(NG["signup_submitted_no_record"].get("cooldown_min")))
    check("生徒が登録できていれば鳴らない",
          "signup_submitted_no_record" not in keys_for(
              form_submit_checkout_6h=3, signups_6h=2, checkout_initiated_6h=0))
    check("既存メール再申込 (checkout_initiated 到達) では鳴らない",
          "signup_submitted_no_record" not in keys_for(
              form_submit_checkout_6h=3, signups_6h=0, checkout_initiated_6h=1),
          "実測で誤報の3件に1件がこの形")
    check("誰も送信していない静かな時間帯では鳴らない (平常値で鳴らさない)",
          "signup_submitted_no_record" not in keys_for(
              form_submit_checkout_6h=0, signups_6h=0, checkout_initiated_6h=0))
    # trialForm は lp.html の method="get" 遷移で API を叩かない = 永久に誤報になる
    check("checkoutForm 以外の送信 (trialForm 等) では鳴らない",
          "signup_submitted_no_record" not in keys_for(
              form_submit_6h=5, form_submit_checkout_6h=0,
              signups_6h=0, checkout_initiated_6h=0))

    # --- 8. 朝7時サマリの回帰 (空リスト呼び出し) ---------------------------
    print("\n[8] 朝7時サマリ: _format_alert_email は空リストでも壊れないこと")
    # _format_daily_summary は snapshot 表の HTML だけ再利用するため空リストで呼ぶ。
    # ここで alerts[0] を引くと朝サマリが IndexError で無音停止する (スケジューラが握り潰す)。
    try:
        subj0, html0 = mod._format_alert_email([], snap)
        check("空リストで例外を出さない", True, subj0)
    except Exception as e:
        check("空リストで例外を出さない", False, f"{type(e).__name__}: {e}")
    try:
        ds, dh = mod._format_daily_summary(snap)
        check("_format_daily_summary が通る", bool(ds and dh), ds)
    except Exception as e:
        check("_format_daily_summary が通る", False, f"{type(e).__name__}: {e}")

    # --- 9. JSエラー多発メールの cooldown ---------------------------------
    print("\n[9] JSエラー多発メール: 60分 cooldown / 送信失敗時は cooldown を刻まない")

    class _FakeReq:
        headers = {"x-forwarded-for": "203.0.113.9"}

        class client:
            host = "203.0.113.9"

    def fire_js_error(send_ok: bool):
        calls = []
        real_origin, real_mail = mod._origin_allowed, mod._send_monitor_email
        # Origin 検査はこのテストの対象外なので通す (対象は cooldown)
        mod._origin_allowed = lambda r: True
        mod._send_monitor_email = lambda s, h, to_email=None: (
            calls.append(s), {"sent": send_ok})[1]
        try:
            mod.js_error_report(
                mod.JSErrorReport(kind="js_error", message="boom", page="/mypage.html",
                                  session_id="s_test"),
                _FakeReq())
        finally:
            mod._origin_allowed, mod._send_monitor_email = real_origin, real_mail
        return calls

    conn = mod.db()
    cur = conn.cursor()
    for i in range(12):  # 閾値 10件/5分 を超えさせる
        cur.execute("INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                    ("js_error", json.dumps({"message": f"e{i}"}), f"s{i}"))
    conn.commit()
    conn.close()

    c1 = fire_js_error(send_ok=False)
    check("閾値超えでメールを試みる", len(c1) == 1, f"{c1}")
    c2 = fire_js_error(send_ok=False)
    check("送信失敗なら cooldown を刻まず再試行する", len(c2) == 1,
          "送信できていないのに60分黙るのは検知能力の低下")
    c3 = fire_js_error(send_ok=True)
    check("送信成功する回もメールが出る", len(c3) == 1)
    c4 = fire_js_error(send_ok=True)
    check("送信成功後は 60分 cooldown で黙る", len(c4) == 0,
          "従来は js_error POST 1件ごとに1通飛んでいた")

    # --- 10. 実データ → 実SQL → 発報 → cooldown の一気通貫 ------------------
    # ★[7] は snapshot を手で組むので、SQL の WHERE が壊れても cooldown_min が無視されても
    #   緑のまま通ってしまう (実際に破壊実験で素通りした)。ここは DB に実イベントを入れて
    #   _collect_health_snapshot → _evaluate_alerts → _run_monitor_check を通しで走らせる。
    print("\n[10] 実データ→実SQL→発報→cooldown の一気通貫")
    # ★30分前に送信されたことにする。本体には 5 分の lag guard があるので
    #   「たった今」の送信は (まだ登録処理中かもしれないので) 意図的に数えられない。
    fs_at = (datetime.now(timezone.utc) - timedelta(minutes=30)).replace(tzinfo=None)
    conn = mod.db()
    cur = conn.cursor()
    cur.execute("INSERT INTO events (name, props, session_id, created_at) VALUES (?, ?, ?, ?)",
                ("form_submit",
                 json.dumps({"form_id": "checkoutForm", "page": "/checkout.html"}),
                 "s_fs", fs_at))
    conn.commit()
    conn.close()

    live = mod._collect_health_snapshot()
    check("実クエリが checkoutForm の送信を拾う (LIKE が効いている)",
          live.get("form_submit_checkout_6h") == 1, str(live.get("form_submit_checkout_6h")))

    # ★lag guard: たった今の送信は数えない。実測で「student が form_submit の 34ms 後に
    #   作られたのに tick がその 3 秒前に走った」ために誤報した回があるため。
    conn = mod.db()
    cur = conn.cursor()
    cur.execute("INSERT INTO events (name, props, session_id, created_at) VALUES (?, ?, ?, ?)",
                ("form_submit",
                 json.dumps({"form_id": "checkoutForm", "page": "/checkout.html"}), "s_now",
                 (datetime.now(timezone.utc) - timedelta(seconds=30)).replace(tzinfo=None)))
    conn.commit()
    conn.close()
    check("直近5分の送信は数えない (登録処理中を誤報しない lag guard)",
          mod._collect_health_snapshot().get("form_submit_checkout_6h") == 1,
          str(mod._collect_health_snapshot().get("form_submit_checkout_6h")))

    # ★checkoutForm の絞り込みが SQL で本当に効いているか。trialForm は lp.html の
    #   method="get" 遷移で API を叩かないので、混ざると構造的な永久誤報になる。
    conn = mod.db()
    cur = conn.cursor()
    cur.execute("INSERT INTO events (name, props, session_id, created_at) VALUES (?, ?, ?, ?)",
                ("form_submit", json.dumps({"form_id": "trialForm", "page": "/lp.html"}),
                 "s_trial", fs_at))
    conn.commit()
    conn.close()
    check("trialForm の送信は数えない (SQL の絞り込みが効いている)",
          mod._collect_health_snapshot().get("form_submit_checkout_6h") == 1,
          str(mod._collect_health_snapshot().get("form_submit_checkout_6h")))

    # ★証拠側の 15 分拡張。6h 窓の少し外で成功した申込を「証拠なし」と誤判定しないこと。
    #   90日の再現で実際に誤報を1件減らしたのはこの拡張だけなので、無検査にはできない。
    just_outside = (datetime.now(timezone.utc)
                    - timedelta(hours=6, minutes=7)).replace(tzinfo=None)
    conn = mod.db()
    cur = conn.cursor()
    cur.execute("INSERT INTO students (name, email, status, created_at) VALUES (?, ?, ?, ?)",
                ("窓外 太郎", "outside@example.com", "trial", just_outside))
    conn.commit()
    conn.close()
    check("6h 窓の 7 分外で成功した申込も証拠として数える (誤報を減らす15分拡張)",
          "signup_submitted_no_record" not in
          {a["key"] for a in mod._evaluate_alerts(mod._collect_health_snapshot())},
          "証拠窓を h6 に戻すとここが落ちる")
    conn = mod.db()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE email = ?", ("outside@example.com",))
    conn.commit()
    conn.close()
    check("実 snapshot から signup_submitted_no_record が立つ",
          "signup_submitted_no_record" in {a["key"] for a in mod._evaluate_alerts(live)})

    real_send = mod._send_monitor_email
    mod._send_monitor_email = lambda s, h, to_email=None: {"sent": True}
    try:
        r1 = mod._run_monitor_check()
        # 「90分前に送った」状態にする。既定 60分 cooldown なら再送され、360分なら黙るはず。
        back = (datetime.now(timezone.utc) - timedelta(minutes=90)).replace(tzinfo=None)
        conn = mod.db()
        cur = conn.cursor()
        cur.execute("UPDATE events SET created_at = ? WHERE name='monitor_alert' "
                    "AND props LIKE '%signup_submitted_no_record%'", (back,))
        conn.commit()
        conn.close()
        r2 = mod._run_monitor_check()
    finally:
        mod._send_monitor_email = real_send
    check("1回目はバナー用に記録される (メールはしない)",
          "signup_submitted_no_record" in r1["alerts_info_suppressed"]
          and "signup_submitted_no_record" not in r1["alerts_sent"],
          f"suppressed={r1['alerts_info_suppressed']} sent={r1['alerts_sent']}")
    check("90分後は再記録しない (cooldown_min=360 が実際に効いている)",
          "signup_submitted_no_record" not in r2["alerts_info_suppressed"]
          and "signup_submitted_no_record" not in r2["alerts_sent"],
          f"suppressed={r2['alerts_info_suppressed']}")

    print("\n" + "=" * 60)
    if FAILURES:
        print(f"❌ FAIL: {len(FAILURES)} 件")
        for f in FAILURES:
            print(f"   - {f}")
        return 1
    print("✅ ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
