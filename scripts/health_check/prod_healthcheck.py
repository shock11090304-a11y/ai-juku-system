#!/usr/bin/env python3
"""ai-juku 本番 健全性チェック (READ-ONLY・決定的)。

2026-07-02 の多視点監査で「見つかったけれど気づけていなかった」バグ群を、今後は
毎回・機械的に検出できるようにするための常設ツール。各チェックは今回の実所見に対応:

  deploy_freshness   … 本番ビルドの凍結/未反映(HEADと本番のmd5不一致・原因を問わず検出)
  api_health         … 本番API/主要公開ページの死活 + サーバの混み具合(処理枠)/DB接続の予兆
  vercel_cap         … api/*.py 数の方針ガード(2026-07-18 Pro化で旧12個上限は解消・警告のみ)
  subject_canonical  … question_attempts/student_weakness の非canonical subject
                       (弱点集計・CEO科目配信が空振りする原因)
  orphan_rows        … 削除済み生徒を参照する活動行(KPI水増し・ゾンビassignment)
  drill_stored_live  … grammar_drills の「N問」表記と実出題(active=1)のズレ
  r_grammar_unit_tags … daigaku/r_grammar 小問の unit/【単元】タグ漏れ(週次プリントの
                       単元一致選定①から無言で漏れ精度27%水準に劣化。手順:
                       scripts/r_grammar_unit_tags/README.md)
  answer_bias        … 直近取込 grammar_questions の正解位置の偏り(取込前均等化漏れ)
  weekly_report      … 週次レポートが全生徒スキップ(集計ソース断絶で無音no-op)
  monitor_storm      … 監視 monitor_alert の誤発報ストーム(本物のcriticalが埋もれる)
  scheduler_live     … in-process スケジューラの最終実行時刻(停止検知)
  stripe_webhook_events … Stripe webhook endpoint の購読イベント欠落(コードにハンドラを
                       追加しても Dashboard 未購読だと機能が無音で不成立:
                       例 payment_intent.canceled 欠落 → 台帳の⚠️/🔐が残り続ける)

使い方:
  # 静的/APIチェックのみ(DB不要・どこでも可)
  python3 scripts/health_check/prod_healthcheck.py --static-only

  # DBチェックも含める(本番Postgresへ read-only 接続)
  railway run -s Postgres python3 scripts/health_check/prod_healthcheck.py

  # Stripe webhook 購読検査も含める (opt-in: STRIPE_SECRET_KEY があるときだけ・READ-ONLY GET)
  # ※通常の `railway run -s Postgres` の env に Stripe 鍵は無い → その場合は明示スキップ。
  #   鍵は Railway ai-juku-api サービスの env にある (sk_live)。履歴に残さない形で併用可:
  STRIPE_SECRET_KEY="$(railway variables -s ai-juku-api --kv | sed -n 's/^STRIPE_SECRET_KEY=//p')" \
      railway run -s Postgres python3 scripts/health_check/prod_healthcheck.py

  # 静的チェックを飛ばして DB のみ / JSON出力
  ... prod_healthcheck.py --db-only
  ... prod_healthcheck.py --json

終了コード: FAIL が1件でもあれば 1、WARN のみ/全PASS なら 0。CI/cron から使える。
※鍵なしの通常運用では stripe_webhook_events が常に WARN 1件 (スキップ表示) 残る。
  CI/cron の判定は必ず終了コード/FAIL 件数で行うこと (WARN>0 で発報すると常時鳴る)。
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = "https://ai-juku-api-production.up.railway.app"
SITE = "https://trillion-ai-juku.com"
CANON = {"english", "math", "physics", "chemistry", "biology", "earth", "japanese", "social"}
# 本番と HEAD の md5 が一致すべき主要静的ファイル(Vercelビルド凍結の検知)
FRESHNESS_FILES = [
    "app.js", "ceo.html", "mypage.html", "dojo-drill.html",
    "enrollment.html", "class.html", "checkout.js",
]
# Stripe webhook endpoint (api/stripe-webhook.py) が Dashboard 側で購読しているべきイベント。
# 購読が欠けているとハンドラは一切呼ばれず機能が無音で不成立になる
# (例: payment_intent.canceled 欠落 → PIキャンセルしても台帳の⚠️/🔐が残り続ける)。
# WEBHOOK_PATH は直接経路 /api/stripe-webhook。公式登録URLの /payment/api/stripe-webhook は
# vercel.json rewrite でここに流れるだけなので、どちらの形で登録されていても同一機能=両方正とする。
WEBHOOK_PATH = "/api/stripe-webhook"
WEBHOOK_HOST_HINT = "trillion-ai-juku.com"
REQUIRED_WEBHOOK_EVENTS = {
    "checkout.session.completed",
    "invoice.payment_failed",
    "invoice.payment_succeeded",
    "customer.subscription.deleted",
    "payment_intent.succeeded",
    "payment_intent.payment_failed",
    # df439e6 (要確認PI残骸の掃除ハンドラ) 用。ハンドラのマージ前から購読状態を監視したいので
    # 基準に含める (ローカルの HANDLERS に無い間は「購読予定」として区別表示される)。
    "payment_intent.canceled",
}

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"
results = []  # (section, level, message)


def add(section, level, message):
    results.append((section, level, message))


def _http_get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "ai-juku-healthcheck/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.getcode(), r.read()


# ---------------------------------------------------------------- 静的/API 系
def check_api_health():
    try:
        code, raw = _http_get(f"{API}/api/health")
        add("api_health", PASS if code == 200 else FAIL, f"GET /api/health = {code}")
        # 🩺 2026-07-27: 「詰まりかけ」を塾長の目に入れる。
        # ステータスコードだけ見ていると、スレッド枯渇で全APIが待たされていても
        # health は 200 を返すので PASS としか出ず、予兆に気づけない。
        if code == 200:
            # ★解析は独立した try にする: ここで落ちても「GET失敗」と誤ラベルしないため
            #   (GET 自体は上で成功=PASS 済み。矛盾した2行が並ぶと深夜の診断を誤らせる)
            try:
                h = json.loads(raw)
                if not isinstance(h, dict):
                    h = {}
                verdict = h.get("verdict")
                used, total = h.get("threads_used"), h.get("threads_total")
                if verdict and verdict != "ok":
                    add("api_health", WARN if verdict == "busy" else FAIL,
                        f"サーバの混み具合: {verdict} — {h.get('hint','')} (処理枠 {used}/{total})")
                elif used is not None and total:
                    add("api_health", PASS, f"サーバの混み具合: ok (処理枠 {used}/{total})")
                # DB接続の予兆。★db_pool_active=False は「プール自体が無効」で、
                #   下の回数が 0 のままでも健全の証拠にならない (全部が直接接続のため)。
                #   フィールドが無い旧 deploy では None なので `is False` で判定する (誤警告防止)。
                if h.get("db_pool_active") is False:
                    add("api_health", WARN,
                        "DB接続プールが無効です (今は全部が直接つなぎに行く設定)。"
                        "緊急対応でわざと切っている場合はそのままでOK。"
                        "覚えがない/何日も続くならエンジニアに確認してください")
                else:
                    # ★この回数は「サーバ起動からの累計」で時間窓が無い。過去に1回あっただけでも
                    #   次の deploy まで出続けるので、少数のうちは PASS 表示に留めて鳴らし過ぎを防ぐ。
                    fb = h.get("db_pool_fallbacks") or 0
                    if fb >= 5:
                        add("api_health", WARN,
                            f"DB接続の空き待ちが起動から {fb} 回。"
                            "数が増え続けるようならエンジニアに確認してください")
                    elif fb:
                        add("api_health", PASS,
                            f"DB接続の空き待ちが起動から {fb} 回 (少数なら様子見でOK)")
                # 🔒 起動時DDLの未反映 (2026-09-03「本番API 75分全停止」の再発防止で追加)。
                #   ★これを見ないと「あるはずの列が無いまま緑で動いている」状態を見逃す。
                #     health は DB に触らないので verdict は ok のままになる。
                #   ★フィールドが無い旧 deploy では None → falsy なので誤警告しない
                #     (db_pool_active を `is False` で判定しているのと同じ配慮)。
                ddl_skipped = h.get("init_ddl_skipped")
                if ddl_skipped:
                    names = "、".join(str(x) for x in (h.get("init_ddl_skipped_names") or [])[:5])
                    # ★対処の文面は health の init_ddl_hint をそのまま使う (ここに書き写すと
                    #   片方だけ更新されて食い違う)。旧 deploy 等で hint が無いときだけ最小限を補う。
                    hint = h.get("init_ddl_hint") or (
                        "Railway で ai-juku-api を Restart してください。"
                        "2回やってもこの表示が消えないならエンジニアに連絡してください")
                    add("api_health", WARN,
                        f"{hint}{f' (未反映: {names})' if names else ''}")
                elif ddl_skipped == 0:
                    # ★「見た上で0件」と「フィールドが無い旧 deploy (None)」を区別して出す。
                    #   無言だと Rollback 直後などに『チェックできていない』ことに気づけない。
                    add("api_health", PASS, "起動時のデータベース更新: 全部通っています (未反映 0 件)")
                # 🗄️ 2026-09-07 DB バックアップ (R2) の設定有無。未設定だと毎晩の dump が黙ってスキップされる。
                #   停止/失敗そのものは scheduler_live (DB モード) と 5 分監視の critical メールが見る。
                r2c = h.get("r2_backup_configured")
                if r2c is False:
                    add("api_health", FAIL,
                        "DB バックアップ (Cloudflare R2) が未設定です。Railway の ai-juku-api に R2_ACCOUNT_ID 等を設定してください")
                elif r2c is True:
                    add("api_health", PASS, "DB バックアップ (R2): 設定あり")
            except Exception as e:
                add("api_health", WARN, f"health レスポンスの解析に失敗: {type(e).__name__}: {e}")
    except Exception as e:
        add("api_health", FAIL, f"GET /api/health 失敗: {type(e).__name__}: {e}")
    for path in ("mypage.html", "ceo.html", "dojo-drill.html", "enrollment.html"):
        try:
            code, _ = _http_get(f"{SITE}/{path}")
            add("api_health", PASS if code == 200 else FAIL, f"GET /{path} = {code}")
        except Exception as e:
            add("api_health", FAIL, f"GET /{path} 失敗: {type(e).__name__}: {e}")


def check_deploy_freshness():
    """git HEAD のファイル内容と本番配信の md5 を比較。不一致=本番が古い(Vercel凍結の疑い)。"""
    for f in FRESHNESS_FILES:
        try:
            head = subprocess.run(["git", "-C", REPO, "show", f"HEAD:{f}"],
                                   capture_output=True, timeout=20)
            if head.returncode != 0:
                add("deploy_freshness", WARN, f"{f}: HEAD に存在せず(スキップ)")
                continue
            head_md5 = hashlib.md5(head.stdout).hexdigest()
            code, body = _http_get(f"{SITE}/{f}")
            if code != 200:
                add("deploy_freshness", WARN, f"{f}: 本番 HTTP {code}")
                continue
            prod_md5 = hashlib.md5(body).hexdigest()
            if head_md5 == prod_md5:
                add("deploy_freshness", PASS, f"{f}: 本番=HEAD 一致")
            else:
                add("deploy_freshness", FAIL,
                    f"{f}: 本番と HEAD が不一致 (本番が古い/デプロイ凍結の疑い) "
                    f"head={head_md5[:8]} prod={prod_md5[:8]}")
        except Exception as e:
            add("deploy_freshness", WARN, f"{f}: 比較失敗 {type(e).__name__}: {e}")


def check_vercel_cap():
    script = os.path.join(REPO, "scripts", "check_vercel_function_cap.sh")
    if not os.path.exists(script):
        add("vercel_cap", WARN, "check_vercel_function_cap.sh が見つからない")
        return
    try:
        r = subprocess.run(["bash", script], capture_output=True, text=True, timeout=30)
        last = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
        # スクリプトは警告専用で常に exit 0 (2026-07-18 Pro化・上限は解消)。
        # 基準値超過は最終行の ⚠️ マーカーで検出して WARN に上げる (PASS のまま埋もれさせない)。
        add("vercel_cap", WARN if (r.returncode != 0 or last.startswith("⚠️")) else PASS, last)
    except Exception as e:
        add("vercel_cap", WARN, f"実行失敗 {type(e).__name__}: {e}")


def _webhook_required_events():
    """必須イベント = 固定の基準セット ∪ api/stripe-webhook.py の HANDLERS 登録イベント。
    今後ハンドラを足したのに基準セットの更新を忘れても、自動で検査対象に入る。
    返り値 (required, handlers): handlers はこの checkout のコードにハンドラが実在するもの
    (欠落メッセージで「稼働中の未購読」と「購読予定(未デプロイ)」を区別するために分けて返す)。
    ファイルが読めない/形が変わった場合は handlers=空 で基準セットのみ検査 (縮退・検査は止めない)。"""
    handlers = set()
    try:
        with open(os.path.join(REPO, "api", "stripe-webhook.py"), encoding="utf-8") as f:
            src = f.read()
        m = re.search(r"HANDLERS\s*=\s*\{(.*?)\}", src, re.DOTALL)
        if m:
            block = re.sub(r"#[^\n]*", "", m.group(1))  # コメントアウト行を実ハンドラに数えない
            handlers = set(re.findall(
                r'''['"]([a-z0-9_]+(?:\.[a-z0-9_]+)+)['"]\s*:''', block))
    except Exception:
        handlers = set()
    return set(REQUIRED_WEBHOOK_EVENTS) | handlers, handlers


def _analyze_webhook_endpoints(payload, key_mode):
    """webhook_endpoints 一覧の解析部 (check_stripe_webhook_events から分離)。
    endpoint 毎に個別判定する: 署名 secret (STRIPE_WEBHOOK_SECRET) は1本しか合わないため、
    複数 endpoint の enabled_events を union すると「片方にしか無いイベントは実際は401で
    捨てられているのに購読済み扱い」の偽PASSになる。"""
    def _norm(u):
        return (u or "").strip().rstrip("/").lower()

    if payload.get("has_more"):
        add("stripe_webhook_events", WARN,
            "endpoint 一覧が100件超でページ分割 — 2ページ目以降の対象を未登録と誤判定し得る")
    endpoints = payload.get("data") or []
    matches = [ep for ep in endpoints
               if WEBHOOK_HOST_HINT in _norm(ep.get("url"))
               and _norm(ep.get("url")).endswith(WEBHOOK_PATH)]
    if not matches:
        others = sorted(_norm(ep.get("url")) for ep in endpoints)
        shown = (", ".join(others[:4]) + ("…" if len(others) > 4 else "")) if others else "(0件)"
        add("stripe_webhook_events", WARN,
            f"webhook endpoint (…{WEBHOOK_PATH}) が Stripe [{key_mode}] に未登録 "
            f"= 決済 webhook 全イベント未達の恐れ。Dashboard→Developers→Webhooks で登録要 "
            f"[登録済endpoint: {shown}]")
        return
    enabled = [ep for ep in matches if (ep.get("status") or "") == "enabled"]
    if not enabled:
        add("stripe_webhook_events", WARN,
            f"webhook endpoint はあるが全て disabled ({len(matches)}件) [{key_mode}] = イベント未達。"
            f"Dashboard→Developers→Webhooks で有効化要")
        return
    if len(enabled) > 1:
        add("stripe_webhook_events", WARN,
            f"該当 endpoint が {len(enabled)}件 enabled — 署名 secret (STRIPE_WEBHOOK_SECRET) は"
            f"1本しか合わないため他方への配信は401で捨てられる (そちらにしか無い購読は実質無効)。"
            f"endpoint 毎に個別判定する")

    required, handlers = _webhook_required_events()
    multi = len(enabled) > 1
    for ep in sorted(enabled, key=lambda e: (_norm(e.get("url")), str(e.get("id") or ""))):
        url = _norm(ep.get("url"))
        label = (f"{url} ({ep.get('id') or '?'}) [{key_mode}]" if multi
                 else f"{url} [{key_mode}]")
        events = set(ep.get("enabled_events") or [])
        wildcard = "*" in events
        if wildcard:
            add("stripe_webhook_events", PASS,
                f"{label}: enabled_events=['*'] (全イベント購読)")
        else:
            missing = sorted(required - events)
            if not missing:
                add("stripe_webhook_events", PASS,
                    f"{label}: 必須{len(required)}イベントすべて購読済み")
            else:
                # ラベルはこの checkout のコード基準 (デプロイ済みとは限らない)。購読追加の
                # 判断は必ず「本番デプロイ反映確認後」— 末尾の★注意が両群に効く
                miss_impl = [e for e in missing if e in handlers]
                miss_pending = [e for e in missing if e not in handlers]
                parts = []
                if miss_impl:
                    parts.append(f"ハンドラ実装済み(この checkout 基準)の未購読 {miss_impl} "
                                 f"= 機能が無音で不成立")
                if miss_pending:
                    parts.append(f"購読予定 {miss_pending} (ハンドラがこの checkout に無い"
                                 f"=未マージ/未デプロイの可能性)")
                add("stripe_webhook_events", WARN,
                    f"{label}: 購読漏れ{len(missing)}件 — " + " / ".join(parts) +
                    "。追加は Dashboard→Developers→Webhooks。"
                    "★そのハンドラの本番デプロイ反映を確認してから購読追加 "
                    "(逆順は webhook:seen 24h 焼き付きで Resend も duplicate 扱い)")
        # 逆向きの盲点: 実際に配信される required イベント (wildcard は全 required・
        # 通常は購読済み ∩ required) のうちハンドラがこの checkout に無いものは、本番も
        # 同状態なら受信しても処理されず webhook:seen (24h) に焼き付いている
        delivered = required if wildcard else (events & required)
        ghost = sorted(delivered - handlers)
        if ghost:
            add("stripe_webhook_events", WARN,
                f"{label}: 購読済みだがハンドラがこの checkout に無い {ghost} "
                f"= 本番も同状態なら受信イベントが処理されず焼き付き進行中 "
                f"(checkout が本番より古いだけなら pull で解消・そうでなければ要ハンドラdeploy)")


def check_stripe_webhook_events():
    """Stripe Dashboard の webhook endpoint が必須イベントを購読しているか (READ-ONLY GET)。
    opt-in: STRIPE_SECRET_KEY が env にあるときだけ検査する
    (通常運用の `railway run -s Postgres` の env に Stripe 鍵は無い → 明示スキップ)。
    このチェックはどの分岐でも FAIL を出さない (欠落=WARN の設計・exit code を変えない)。"""
    key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not key:
        add("stripe_webhook_events", WARN,
            "スキップ (鍵なし): STRIPE_SECRET_KEY 未設定。付与すると Stripe webhook の"
            "購読イベント欠落を検査 (鍵を履歴に残さない実行例は冒頭 docstring / README.md)")
        return
    try:
        req = urllib.request.Request(
            "https://api.stripe.com/v1/webhook_endpoints?limit=100",
            headers={"Authorization": f"Bearer {key}",
                     "User-Agent": "ai-juku-healthcheck/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            payload = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = (json.loads(e.read().decode("utf-8"))
                      .get("error", {}).get("message", "") or "")[:120]
        except Exception:
            pass
        add("stripe_webhook_events", WARN,
            f"Stripe API 照会失敗 HTTP {e.code} {detail} (鍵の有効性/権限を確認)")
        return
    except Exception as e:
        add("stripe_webhook_events", WARN, f"Stripe API 照会失敗: {type(e).__name__}: {e}")
        return

    # 鍵のモード (sk_live_/rk_live_/sk_test_/rk_test_)。test 鍵だと test 環境の endpoint しか
    # 見えず本番 (live) の購読は未検証のままなので明示する。
    parts = key.split("_")
    key_mode = parts[1] if len(parts) >= 3 and parts[1] in ("live", "test") else "?"
    if key_mode != "live":
        add("stripe_webhook_events", WARN,
            f"鍵が {key_mode} mode — 本番 (live) の購読は未検証 (sk_live_/rk_live_ の鍵で実行を)")
    try:
        _analyze_webhook_endpoints(payload, key_mode)
    except Exception as e:
        # 想定外の応答形でもヘルスチェック全体を落とさない (このチェックは常に WARN 止まり)
        add("stripe_webhook_events", WARN,
            f"Stripe 応答の解析に失敗: {type(e).__name__}: {e}")


# ---------------------------------------------------------------- DB 系
def _connect():
    url = os.environ.get("DATABASE_PUBLIC_URL") or os.environ.get("DATABASE_URL")
    if not url:
        return None
    try:
        import psycopg
    except ImportError:
        add("db", WARN, "psycopg 未インストール — DBチェックをスキップ")
        return None
    try:
        return psycopg.connect(url)
    except Exception as e:
        add("db", FAIL, f"DB接続失敗: {type(e).__name__}: {e}")
        return None


def _table_exists(cur, name):
    cur.execute("SELECT 1 FROM information_schema.tables WHERE table_name=%s", (name,))
    return cur.fetchone() is not None


def check_subject_canonical(cur):
    for tbl in ("question_attempts", "student_weakness"):
        if not _table_exists(cur, tbl):
            continue
        cur.execute(f"SELECT subject, COUNT(*) FROM {tbl} "
                    f"WHERE subject IS NOT NULL GROUP BY subject")
        rows = cur.fetchall()
        noncanon = [(s, n) for (s, n) in rows if (s or "").strip().lower() not in CANON]
        if not noncanon:
            add("subject_canonical", PASS, f"{tbl}: 全 subject が canonical")
        else:
            total = sum(n for _, n in noncanon)
            top = ", ".join(f"{s}={n}" for s, n in sorted(noncanon, key=lambda x: -x[1])[:6])
            add("subject_canonical", WARN,
                f"{tbl}: 非canonical subject {total}件 (弱点集計/配信が空振りし得る) [{top}]")


def check_orphan_rows(cur):
    for tbl in ("question_attempts", "student_weakness", "grammar_drill_assignments"):
        if not _table_exists(cur, tbl):
            continue
        try:
            cur.execute(
                f"SELECT COUNT(*) FROM {tbl} t "
                f"WHERE t.student_id IS NOT NULL AND t.student_id > 0 "
                f"AND NOT EXISTS (SELECT 1 FROM students s WHERE s.id = t.student_id)")
            n = cur.fetchone()[0]
            add("orphan_rows", PASS if n == 0 else WARN,
                f"{tbl}: 削除済み生徒を参照する orphan {n}件")
        except Exception as e:
            add("orphan_rows", WARN, f"{tbl}: 照会失敗 {type(e).__name__}: {e}")


def check_drill_stored_live(cur):
    if not (_table_exists(cur, "grammar_drills") and _table_exists(cur, "grammar_questions")):
        return
    try:
        cur.execute(
            "SELECT id, question_ids FROM grammar_drills "
            "WHERE created_at >= NOW() - INTERVAL '14 days'")
        mism = 0
        for did, qids_raw in cur.fetchall():
            try:
                qids = json.loads(qids_raw) if isinstance(qids_raw, str) else (qids_raw or [])
            except Exception:
                qids = []
            if not qids:
                continue
            ph = ",".join(["%s"] * len(qids))
            cur.execute(f"SELECT COUNT(*) FROM grammar_questions WHERE id IN ({ph}) AND active=1",
                        tuple(qids))
            live = cur.fetchone()[0]
            if live != len(qids):
                mism += 1
        add("drill_stored_live", PASS if mism == 0 else WARN,
            f"直近14日ドリル: stored≠live(active) {mism}本 (「N問」表記と実出題のズレ)")
    except Exception as e:
        add("drill_stored_live", WARN, f"照会失敗 {type(e).__name__}: {e}")


def check_r_grammar_unit_tags(cur):
    """daigaku/r_grammar の全小問に unit フィールド or【単元】タグがあるか。
    2026-08-18 から週次弱点プリントの英語選定が【単元】タグ一致 (server/main.py
    _grammar_unit_rows) になったため、タグ無しの新規行は単元一致選定から**無言で**漏れる
    (フォールバックには乗るので配信は止まらないが、精度改善が不発になる)。"""
    if not _table_exists(cur, "exam_questions"):
        return
    try:
        cur.execute("SELECT id, question_data FROM exam_questions "
                    "WHERE exam_id='daigaku' AND part_key='r_grammar'")
        tag_re = re.compile(r"【単元】\s*[^】\n(（]+")
        bad_rows = []
        n_rows = 0
        for rid, qd_raw in cur.fetchall():
            n_rows += 1
            try:
                qd = json.loads(qd_raw) if isinstance(qd_raw, str) else (qd_raw or {})
            except Exception:
                bad_rows.append(rid)
                continue
            for q in (qd.get("questions") or []):
                if not isinstance(q, dict):
                    continue
                if str(q.get("unit") or "").strip():
                    continue
                if tag_re.search(str(q.get("explanation") or "") + "\n" + str(q.get("stem") or "")):
                    continue
                bad_rows.append(rid)
                break
        add("r_grammar_unit_tags",
            PASS if not bad_rows else WARN,
            f"daigaku/r_grammar {n_rows}大問: 単元タグ無し {len(bad_rows)}大問"
            + (f" (例: id={bad_rows[:5]} — 週次プリントの単元一致選定から漏れる。"
               f"付与手順: scripts/r_grammar_unit_tags/README.md)" if bad_rows else ""))
    except Exception as e:
        add("r_grammar_unit_tags", WARN, f"照会失敗 {type(e).__name__}: {e}")


def check_answer_bias(cur):
    if not _table_exists(cur, "grammar_questions"):
        return
    try:
        cur.execute(
            "SELECT source, COUNT(*) FROM grammar_questions "
            "WHERE created_at >= NOW() - INTERVAL '7 days' AND source IS NOT NULL "
            "GROUP BY source HAVING COUNT(*) >= 12")
        sources = cur.fetchall()
        if not sources:
            add("answer_bias", PASS, "直近7日に新規取込バッチなし")
            return
        for src, cnt in sources:
            cur.execute("SELECT answer, COUNT(*) FROM grammar_questions "
                        "WHERE source=%s GROUP BY answer", (src,))
            dist = {int(a): n for a, n in cur.fetchall() if a is not None}
            tot = sum(dist.values()) or 1
            worst = max(dist.values()) / tot if dist else 0
            missing0 = any(dist.get(i, 0) == 0 for i in range(4))
            if worst > 0.5 or missing0:
                add("answer_bias", WARN,
                    f"source='{src}' ({cnt}問): 正解位置に偏り {dist} "
                    f"(取込前ラウンドロビン均等化を推奨)")
            else:
                add("answer_bias", PASS, f"source='{src}' ({cnt}問): 正解位置は均等 {dist}")
    except Exception as e:
        add("answer_bias", WARN, f"照会失敗 {type(e).__name__}: {e}")


def check_weekly_report(cur):
    if not _table_exists(cur, "events"):
        return
    try:
        cur.execute(
            "SELECT props FROM events WHERE name='weekly_reports_run' "
            "ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
        if not row:
            add("weekly_report", WARN, "weekly_reports_run イベントが無い(未実行?)")
            return
        props = json.loads(row[0]) if isinstance(row[0], str) else (row[0] or {})
        sent = int(props.get("sent_email", 0)) + int(props.get("sent_line", 0))
        skipped = int(props.get("skipped", 0))
        total = int(props.get("total_students", 0) or (sent + skipped))
        if total > 0 and sent == 0:
            add("weekly_report", FAIL,
                f"直近の週次レポートが全スキップ (sent=0 / skipped={skipped} / total={total}) "
                f"= 集計ソース断絶の無音no-op")
        else:
            add("weekly_report", PASS, f"直近の週次レポート sent={sent} skipped={skipped}")
    except Exception as e:
        add("weekly_report", WARN, f"照会失敗 {type(e).__name__}: {e}")


def check_monitor_storm(cur):
    if not _table_exists(cur, "events"):
        return
    try:
        cur.execute(
            "SELECT props FROM events WHERE name='monitor_alert' "
            "AND created_at >= NOW() - INTERVAL '24 hours'")
        counts = {}
        for (p,) in cur.fetchall():
            try:
                key = (json.loads(p) if isinstance(p, str) else (p or {})).get("key", "?")
            except Exception:
                key = "?"
            counts[key] = counts.get(key, 0) + 1
        storms = {k: v for k, v in counts.items() if v > 12}  # 24hで12通超=cooldown想定を超える誤発報
        if storms:
            top = ", ".join(f"{k}={v}" for k, v in sorted(storms.items(), key=lambda x: -x[1]))
            add("monitor_storm", WARN,
                f"監視アラートのストーム(24h>12通): {top} = 誤発報で本物の critical が埋もれる恐れ")
        else:
            add("monitor_storm", PASS, f"監視アラート24h={sum(counts.values())}通・ストームなし")
    except Exception as e:
        add("monitor_storm", WARN, f"照会失敗 {type(e).__name__}: {e}")


def check_scheduler_live(cur):
    if not _table_exists(cur, "events"):
        return
    watched = {
        "weakness_aggregation_run": 2,   # 日次想定 → 2日以内
        "weekly_reports_run": 8,         # 週次(日曜) → 8日以内
        "weekly_worksheet_run": 8,       # 週次プリント生成
        "trial_mgmt_run": 2,             # 体験フォロー/リマインダの日次バッチ(実イベント名)
        "r2_backup_success": 2,          # 🗄️ 2026-09-07 DB バックアップ (毎日 JST 3:00 → R2)
        "admission_recompute_run": 2,    # 合格スコア再計算 (毎日 4:00・2026-09-06 追加)
        "events_retention_run": 2,       # 🧹 計測/監視イベントの掃除 (毎日 4:00・2026-09-07 追加)
    }
    for name, max_days in watched.items():
        try:
            cur.execute(
                "SELECT MAX(created_at) FROM events WHERE name=%s", (name,))
            last = cur.fetchone()[0]
            if last is None:
                add("scheduler_live", WARN, f"{name}: 実行履歴なし")
                continue
            cur.execute("SELECT (NOW() - %s) < (%s || ' days')::interval", (last, max_days))
            ok = cur.fetchone()[0]
            add("scheduler_live", PASS if ok else WARN,
                f"{name}: 最終実行 {last} ({'OK' if ok else f'{max_days}日以上前=停止の疑い'})")
        except Exception as e:
            add("scheduler_live", WARN, f"{name}: 照会失敗 {type(e).__name__}: {e}")


def run_db_checks():
    conn = _connect()
    if conn is None:
        if not any(s == "db" for s, _, _ in results):
            add("db", WARN,
                "DATABASE_PUBLIC_URL 未設定 — DBチェックをスキップ "
                "(`railway run -s Postgres python3 ...` で実行すると有効)")
        return
    try:
        cur = conn.cursor()
        for fn in (check_subject_canonical, check_orphan_rows, check_drill_stored_live,
                   check_r_grammar_unit_tags, check_answer_bias, check_weekly_report,
                   check_monitor_storm, check_scheduler_live):
            try:
                fn(cur)
            except Exception as e:
                add(fn.__name__, WARN, f"チェック中に例外 {type(e).__name__}: {e}")
                try:
                    conn.rollback()
                except Exception:
                    pass
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-only", action="store_true", help="静的/APIチェックを飛ばす")
    ap.add_argument("--static-only", action="store_true", help="DBチェックを飛ばす")
    ap.add_argument("--json", action="store_true", help="結果を JSON で出力")
    args = ap.parse_args()

    if not args.db_only:
        check_api_health()
        check_deploy_freshness()
        check_vercel_cap()
        check_stripe_webhook_events()
    if not args.static_only:
        run_db_checks()

    n_fail = sum(1 for _, lv, _ in results if lv == FAIL)
    n_warn = sum(1 for _, lv, _ in results if lv == WARN)

    if args.json:
        print(json.dumps({
            "summary": {"fail": n_fail, "warn": n_warn,
                        "pass": sum(1 for _, lv, _ in results if lv == PASS)},
            "results": [{"section": s, "level": lv, "message": m} for s, lv, m in results],
        }, ensure_ascii=False, indent=2))
    else:
        icon = {PASS: "✅", WARN: "⚠️ ", FAIL: "❌"}
        last_section = None
        for section, lv, msg in results:
            if section != last_section:
                print(f"\n== {section} ==")
                last_section = section
            print(f"  {icon[lv]} {msg}")
        print(f"\n=== 合計: FAIL={n_fail}  WARN={n_warn}  "
              f"PASS={sum(1 for _, lv, _ in results if lv == PASS)} ===")

    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
