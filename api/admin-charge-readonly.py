"""Vercel Function: 入金管理の読み取り専用GET 2系統を1関数に集約

このファイルは元々独立していた2つの Vercel Function を統合したもの:
  - 月末一斉引き落とし「プレビュー」 (旧 admin-charge-month-end-preview.py)
  - 月末引き落としの「過去履歴・失敗者一覧」 (旧 admin-charge-history.py)

統合理由 (旧Hobby時代の制約・2026-07-18 Pro化で12関数上限は解消済み、統合はそのまま維持):
当時の Vercel Hobby プランは「1デプロイあたり最大12 Serverless Functions」で、
api/*.py が13個になるとデプロイ全体がビルド失敗し本番が前ビルドで凍結した
(過去 74e2c5fb / 216d9ac で同型対応の前例あり)。読み取り専用GETの2本を
1ファイルに畳んで枠を1つ空け、実課金POST系 (execute/reconcile/spot/past-due/
webhook/register-subscribe) には一切触れない。

Endpoints (vercel.json rewrite でいずれも本ファイルへ転送):
  GET /payment/api/admin-charge-month-end-preview          → __ep=preview
  GET /payment/api/admin-charge-history?month=&type=       → __ep=history
  GET /payment/api/admin-charge-ledger?months=6            → __ep=ledger
    (月別×生徒の引き落とし台帳。charge:history 等の既存KVを読むだけの read-only 集計)

振り分けは Vercel rewrite の挙動に依存しないよう3層フォールバック:
  (1) destination に埋め込んだ ?__ep=preview / ?__ep=history / ?__ep=ledger (一次)
  (2) self.path に ledger / history / preview(month-end) が含まれるか (source保持時)
  (3) クエリに months があれば ledger・month/type/include_audit/audit_rid があれば history・無ければ preview

認証: X-Admin-Password (CHAT_ADMIN_PASSWORD) — 旧2ファイルと同一。
レスポンスJSON / ステータスコードは旧2ファイルと完全に同一。
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import time
import hmac
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs


def _log(msg):
    try: print(msg, file=sys.stderr, flush=True)
    except Exception: pass


def _json(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


# 🔐 2026-09-07 総当たり対策 (システム点検で確定): パスワード比較だけで試行回数の上限が無く、月末の一括引き落とし・
#   スポット課金・任意宛先メール・顧客一覧が総当たりで開く状態だった。失敗回数を Upstash KV (webhook の冪等化で
#   常用) に IP ごと・全体で記録し、上限に達したら比較せずに拒否する。KV が無い環境では従来どおり比較のみ。
#   ★9 本の関数に同じ塊を置いている (Vercel の Python 関数は 1 ファイル 1 関数で共有モジュールを持たない)。
#     直すときは全部一緒に直すこと。scripts/health_check/test_vercel_admin_guard.py が 9 本とも検査する。
_ADMIN_FAIL_IP_LIMIT = 10        # 同一 IP: 10 回/時
_ADMIN_FAIL_GLOBAL_LIMIT = 60    # 全体: 60 回/時 (IP を変えながらの総当たりを止める)
_ADMIN_FAIL_WINDOW_SEC = 3600


def _admin_kv(*args):
    url = os.environ.get("KV_REST_API_URL", "").strip()
    token = os.environ.get("KV_REST_API_TOKEN", "").strip()
    if not url or not token:
        return None
    try:
        req = urllib.request.Request(url, data=json.dumps(list(args)).encode(),
                                     headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _admin_client_ip(handler) -> str:
    # Vercel が付ける x-real-ip を優先 (x-forwarded-for の先頭は利用者側で細工できる)
    ip = (handler.headers.get("x-real-ip") or "").strip()
    if not ip:
        xff = (handler.headers.get("x-forwarded-for") or "").strip()
        ip = xff.split(",")[-1].strip() if xff else ""
    return (ip or "unknown")[:64]


def _admin_fail_count(key) -> int:
    r = _admin_kv("GET", key)
    try:
        return int((r or {}).get("result") or 0)
    except (TypeError, ValueError, AttributeError):
        return 0


def _admin_fail_record(key):
    r = _admin_kv("INCR", key)
    try:
        if int((r or {}).get("result") or 0) == 1:
            _admin_kv("EXPIRE", key, str(_ADMIN_FAIL_WINDOW_SEC))
    except (TypeError, ValueError, AttributeError):
        pass


def _verify_admin(handler) -> bool:
    """X-Admin-Password ヘッダで認証。失敗が上限 (IP 10回/時・全体 60回/時) に達していると正しくても通さない。"""
    expected = os.environ.get("CHAT_ADMIN_PASSWORD", "").strip()
    if not expected:
        return False
    got = handler.headers.get("X-Admin-Password", "").strip()
    if not got:
        return False
    ip_key = f"adminfail:ip:{_admin_client_ip(handler)}"
    if (_admin_fail_count(ip_key) >= _ADMIN_FAIL_IP_LIMIT
            or _admin_fail_count("adminfail:global") >= _ADMIN_FAIL_GLOBAL_LIMIT):
        return False
    if hmac.compare_digest(got, expected):
        return True
    _admin_fail_record(ip_key)
    _admin_fail_record("adminfail:global")
    return False


def _redis(*args):
    url = os.environ.get("KV_REST_API_URL", "").strip()
    token = os.environ.get("KV_REST_API_TOKEN", "").strip()
    if not url or not token:
        return None
    try:
        body = json.dumps(list(args)).encode()
        req = urllib.request.Request(url, data=body, headers={
            "Authorization": f"Bearer {token}", "Content-Type": "application/json"
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        _log(f"redis error: {e}")
        return None


def _current_month_jst():
    """JST 基準で「2026-05」形式の月文字列を返す"""
    JST = timezone(timedelta(hours=9))
    return datetime.now(JST).strftime("%Y-%m")


def _add_month(ym, delta):
    """'YYYY-MM' に delta ヶ月を加えた 'YYYY-MM' を返す (形式外はそのまま)。"""
    try:
        y, m = int(ym[:4]), int(ym[5:7])
    except Exception:
        return ym
    m += delta
    while m > 12:
        m -= 12; y += 1
    while m <= 0:
        m += 12; y -= 1
    return f"{y:04d}-{m:02d}"


def _fetch_index(index_key, month):
    """ZRANGE で全 entries を取り、{rid:month} → rid を抽出 (指定月のみ)"""
    zr = _redis("ZRANGE", index_key, "0", "-1", "REV")
    if not zr or not isinstance(zr, dict):
        return []
    items = zr.get("result") or []
    if not isinstance(items, list):
        return []
    # entry は "{rid}:{month}" 形式
    rids = []
    for entry in items:
        if isinstance(entry, str) and entry.endswith(f":{month}"):
            rid = entry[:-(len(month) + 1)]
            rids.append(rid)
    return rids


def _fetch_record(key):
    got = _redis("GET", key)
    if not got or not isinstance(got, dict): return None
    s = got.get("result")
    if not s: return None
    try: return json.loads(s)
    except Exception: return None


# ===== プレビュー (旧 admin-charge-month-end-preview.py do_GET) =====
def _handle_preview(handler):
    # 請求対象月: X-Target-Month ヘッダ (今月 or 翌月) を許可。月末に翌月分を前倒し請求する
    # 運用 (2026-06-26 塾長要望) に対応。許可外/未指定はカレンダー月にフォールバック。
    # ヘッダ採用は Vercel rewrite の query 取り回しに依存しないため (確実に handler へ届く)。
    current_month = _current_month_jst()
    next_month = _add_month(current_month, 1)
    target = (handler.headers.get("X-Target-Month", "") or "").strip()
    billing_month = target if target in (current_month, next_month) else current_month
    # 以降の already-charged 判定・表示・集計はすべて請求対象月 (billing_month) で行う
    month_str = billing_month

    # 全カード登録済顧客を取得 (新しい順)
    zr = _redis("ZRANGE", "reg:completed:index", "0", "-1", "REV")
    ids = []
    if zr and isinstance(zr, dict):
        result = zr.get("result")
        if isinstance(result, list):
            ids = result

    customers = []
    total_amount = 0
    ready_count = 0
    missing_card_count = 0
    already_charged_count = 0

    for rid in ids[:500]:  # 最大 500 件
        got = _redis("GET", f"reg:completed:{rid}")
        if not got or not isinstance(got, dict):
            continue
        s = got.get("result")
        if not s:
            continue
        try:
            r = json.loads(s)
        except Exception:
            continue

        customer_id = r.get("stripe_customer_id", "")
        payment_method_id = r.get("stripe_payment_method_id", "")
        monthly_fee = int(r.get("monthly_fee", 0) or 0)
        checkout_mode = r.get("checkout_mode", "")
        # 🚨 2026-05-13: legacy subscription 移行直後の二重課金回避 check
        # migrated_at から計算した「Stripe Subscription が当月分を自動課金済」のフラグ
        legacy_sub_period_end = r.get("legacy_subscription_period_end")
        legacy_sub_cancel_pending = r.get("legacy_subscription_canceled_at_period_end", False)

        # 当月既に引き落とし済かチェック (charge:done:{rid}:{month})
        already_key = f"charge:done:{rid}:{month_str}"
        already_check = _redis("GET", already_key)
        already_charged = False
        if already_check and isinstance(already_check, dict):
            if already_check.get("result"):
                already_charged = True
                already_charged_count += 1

        # ready 判定: setup mode + customer_id + payment_method_id + monthly_fee > 0
        issue = None
        ready = False
        if checkout_mode == "setup":
            if not customer_id:
                issue = "customer_id 欠落"
            elif not payment_method_id:
                issue = "payment_method_id 欠落 (再登録要)"
                missing_card_count += 1
            elif monthly_fee <= 0:
                issue = "月額 0 (登録不備)"
            else:
                # 🚨 2026-05-13: legacy subscription 移行直後の二重課金回避
                # Stripe Subscription が当月分を自動課金済の場合は ready=false にして
                # 月末バッチから除外 (二重課金防止)
                if legacy_sub_cancel_pending and legacy_sub_period_end:
                    try:
                        period_end_dt = datetime.fromtimestamp(int(legacy_sub_period_end), tz=timezone(timedelta(hours=9)))
                        now_jst = datetime.now(timezone(timedelta(hours=9)))
                        # period_end が当月の月末以降にある = 当月は Stripe が課金担当
                        # (例: 5/13 migrate, period_end=6/3 → 5月分は Stripe 課金 / 6月から月末バッチ)
                        current_month_end = (now_jst.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
                        if period_end_dt > current_month_end:
                            ready = False
                            issue = f"⏳ 移行月のため当月 skip (Stripe Subscription が {period_end_dt.strftime('%Y-%m-%d')} まで active・当月分は Stripe 自動課金済)"
                        else:
                            ready = True
                    except Exception:
                        ready = True
                else:
                    ready = True
        elif checkout_mode == "subscription":
            # legacy: Stripe が自動課金しているはずなのでバッチ対象外
            issue = "legacy subscription (Stripe が自動課金中・バッチ対象外)"
        else:
            issue = f"checkout_mode 不明: {checkout_mode or '(空)'}"

        if ready and not already_charged:
            total_amount += monthly_fee
            ready_count += 1

        # カード登録完了日時 (webhook が reg:completed に保存する completed_at)。
        # 「月末一斉実行のあとに登録した人」を UI で見分けるために返す。旧レコードは 0。
        try:
            registered_at = int(r.get("completed_at") or 0)
        except Exception:
            registered_at = 0

        customers.append({
            "registrationId": rid,
            "customerId": customer_id,
            "paymentMethodId": payment_method_id,
            "studentName": r.get("studentName") or r.get("student_name") or "",
            "parentName": r.get("parentName") or r.get("parent_name") or "",
            "grade": r.get("grade", ""),
            "email": r.get("email", ""),
            "phone": r.get("phone", ""),
            "monthlyFee": monthly_fee,
            "feeBreakdown": r.get("fee_breakdown", ""),
            "checkoutMode": checkout_mode,
            "ready": ready,
            "alreadyChargedThisMonth": already_charged,
            "issue": issue,
            "registeredAt": registered_at,
        })

    # 🚨 第二ゲート (2026-07-02 review): charge:done は TTL 60日・charge:history は 1年。
    # 前倒し請求から60日超で done だけ失効すると「実は請求済みなのに未請求」と表示され、
    # 未請求バナー/個別請求ボタンが二重請求へ誤誘導する。done 不在でも成功 history が
    # あれば「請求済み」に倒す (MGET 1回・read-only。execute 側の課金ロジックには触れない)。
    unc = [c for c in customers if c["ready"] and not c["alreadyChargedThisMonth"]]
    if unc:
        hist_recs = _mget_records([f"charge:history:{c['registrationId']}:{month_str}" for c in unc])
        for c, rec in zip(unc, hist_recs):
            if rec:
                c["alreadyChargedThisMonth"] = True
                already_charged_count += 1
                ready_count -= 1
                total_amount -= c["monthlyFee"]

    _json(handler, 200, {
        "month": month_str,                # 請求対象月 (今月 or 翌月) = billing_month
        "current_month": current_month,    # カレンダー月 (フロントの confirmMonth ガード・freshness 用)
        "next_month": next_month,          # 翌月 (UI の請求対象月セレクタ表示用)
        "billing_month": billing_month,
        "preview_at": int(time.time()),
        "total_customers": len(customers),
        "total_amount": total_amount,
        "ready_count": ready_count,
        "missing_card_count": missing_card_count,
        "previously_charged_this_month": already_charged_count,
        "customers": customers,
    })


# ===== 履歴 (旧 admin-charge-history.py do_GET) =====
def _handle_history(handler, params):
    month = (params.get("month", [None])[0] or _current_month_jst()).strip()
    filter_type = (params.get("type", ["all"])[0] or "all").strip()
    include_audit = (params.get("include_audit", ["0"])[0] or "0").strip() == "1"
    audit_rid = (params.get("audit_rid", [""])[0] or "").strip()

    result = {
        "month": month,
        "fetched_at": int(time.time()),
        "success": [],
        "failed": [],
        "requires_action": [],
        "uncertain": [],
        "summary": {
            "success_count": 0,
            "failed_count": 0,
            "requires_action_count": 0,
            "uncertain_count": 0,
            "total_amount_charged": 0,
        },
    }

    # success (charge:history)
    if filter_type in ("all", "success"):
        rids = _fetch_index("charge:history:index", month)
        for rid in rids[:500]:
            r = _fetch_record(f"charge:history:{rid}:{month}")
            if r:
                result["success"].append({
                    "registrationId": rid,
                    "studentName": r.get("student_name") or r.get("studentName") or "",
                    "email": r.get("email", ""),
                    "phone": r.get("phone", ""),
                    "amount": r.get("amount", 0),
                    "paymentIntentId": r.get("payment_intent_id", ""),
                    "chargedAt": r.get("charged_at", 0),
                    "stripeStatus": r.get("status", ""),
                })
                result["summary"]["success_count"] += 1
                result["summary"]["total_amount_charged"] += int(r.get("amount", 0) or 0)

    # failed (charge:failed)
    if filter_type in ("all", "failed"):
        rids = _fetch_index("charge:failed:index", month)
        for rid in rids[:500]:
            r = _fetch_record(f"charge:failed:{rid}:{month}")
            if r:
                result["failed"].append({
                    "registrationId": rid,
                    "studentName": r.get("student_name") or r.get("studentName") or "",
                    "email": r.get("email", ""),
                    "phone": r.get("phone", ""),
                    "amount": r.get("amount", 0),
                    "errorCode": r.get("error_code", ""),
                    "declineCode": r.get("decline_code", ""),
                    "errorDetail": r.get("error_detail", ""),
                    "failedAt": r.get("failed_at", 0),
                })
                result["summary"]["failed_count"] += 1

    # requires_action (charge:requires_action)
    if filter_type in ("all", "requires_action"):
        rids = _fetch_index("charge:requires_action:index", month)
        for rid in rids[:500]:
            r = _fetch_record(f"charge:requires_action:{rid}:{month}")
            if r:
                result["requires_action"].append({
                    "registrationId": rid,
                    "studentName": r.get("student_name") or r.get("studentName") or "",
                    "email": r.get("email", ""),
                    "phone": r.get("phone", ""),
                    "amount": r.get("amount", 0),
                    "paymentIntentId": r.get("payment_intent_id", ""),
                    "redirectUrl": r.get("redirect_url", ""),
                    "notedAt": r.get("noted_at", 0),
                })
                result["summary"]["requires_action_count"] += 1

    # uncertain (charge:uncertain) ★ 最も重要: 手動 reconcile が必要
    if filter_type in ("all", "uncertain"):
        rids = _fetch_index("charge:uncertain:index", month)
        for rid in rids[:500]:
            r = _fetch_record(f"charge:uncertain:{rid}:{month}")
            if r:
                result["uncertain"].append({
                    "registrationId": rid,
                    "studentName": r.get("student_name") or r.get("studentName") or "",
                    "email": r.get("email", ""),
                    "phone": r.get("phone", ""),
                    "amount": r.get("amount", 0),
                    "idempotencyKey": r.get("idempotency_key", ""),
                    "errorDetail": r.get("error", ""),
                    "notedAt": r.get("noted_at", 0),
                })
                result["summary"]["uncertain_count"] += 1

    # 🚨 Round 4 fix (H3): audit log を取得可能に (税務監査・トラブル時の全試行履歴)
    if include_audit and audit_rid:
        audit_key = f"charge:history:audit:{audit_rid}:{month}"
        audit_zr = _redis("LRANGE", audit_key, "0", "-1")
        audit_list = []
        if audit_zr and isinstance(audit_zr, dict):
            raw_list = audit_zr.get("result") or []
            if isinstance(raw_list, list):
                for s in raw_list:
                    try:
                        audit_list.append(json.loads(s))
                    except Exception:
                        pass
        result["audit_log"] = audit_list
        result["audit_rid"] = audit_rid
        result["audit_count"] = len(audit_list)

    _json(handler, 200, result)


# ===== 台帳 (月別 × 生徒のカード引き落とし状況・2026-07-02 塾長要望) =====
# 「誰の何月分をカードから引き落とし済みか」を1リクエストで返す read-only 集計。
# 既存の charge:history / charge:failed / charge:requires_action / charge:uncertain と
# spot:history (講習などの単発課金) を読むだけで、書き込み・課金は一切行わない。

# 並び順 = 切り詰め (GET_CAP) 時に生き残る優先度。要対応の uncertain/requires_action を先頭に置く
# (末尾から切り捨てるため、溢れても「要対応が消えて健全に見える」事故を防ぐ・2026-07-02 review)。
_LEDGER_STATUS_NAMESPACES = (
    ("uncertain", "charge:uncertain"),
    ("requires_action", "charge:requires_action"),
    ("failed", "charge:failed"),
    ("success", "charge:history"),
)


def _mget_records(keys):
    """MGET で一括取得し、keys と同順の [dict|None] を返す。
    逐次 GET は 1件=1HTTPS往復で件数比例に遅くなり Vercel 関数 timeout (10s) を踏むため、
    台帳系の record 取得は必ずこれを使う (2026-07-02 review P1)。read-only。"""
    out = []
    CHUNK = 400  # 1 コールの応答サイズを抑える
    for i in range(0, len(keys), CHUNK):
        chunk = keys[i:i + CHUNK]
        resp = _redis("MGET", *chunk)
        vals = resp.get("result") if (resp and isinstance(resp, dict)) else None
        if not isinstance(vals, list) or len(vals) != len(chunk):
            vals = [None] * len(chunk)
        for s in vals:
            if not s:
                out.append(None)
                continue
            try:
                out.append(json.loads(s))
            except Exception:
                out.append(None)
    return out


def _index_entries(index_key):
    """ZRANGE 全件 → [(rid, month)] に分解。entry は "{rid}:{YYYY-MM}" 形式のみ採用
    (rid 自体に ':' が含まれても月は末尾固定なので rpartition で安全に分離できる)。"""
    zr = _redis("ZRANGE", index_key, "0", "-1", "REV")
    if not zr or not isinstance(zr, dict):
        return []
    items = zr.get("result") or []
    if not isinstance(items, list):
        return []
    out = []
    for entry in items:
        if not isinstance(entry, str) or ":" not in entry:
            continue
        rid, _, month = entry.rpartition(":")
        if (rid and len(month) == 7 and month[4] == "-"
                and month[:4].isdigit() and month[5:].isdigit()):
            out.append((rid, month))
    return out


def _month_jst_from_ts(ts):
    """epoch 秒 → JST の 'YYYY-MM' (不正値は空文字)。spot 課金の月割り当てに使う。"""
    try:
        JST = timezone(timedelta(hours=9))
        return datetime.fromtimestamp(int(ts), JST).strftime("%Y-%m")
    except Exception:
        return ""


def _handle_ledger(handler, params):
    """月別 × 生徒の引き落とし台帳。対象月 = 翌月 (前倒し請求分) + 今月 + 直近 (months-1) ヶ月。"""
    try:
        n = int((params.get("months", ["6"])[0] or "6").strip())
    except Exception:
        n = 6
    n = max(1, min(n, 12))
    current = _current_month_jst()
    next_month = _add_month(current, 1)
    months = [next_month] + [_add_month(current, -i) for i in range(0, n)]
    month_set = set(months)

    truncated = False
    entries = []

    # --- 月謝の月次引き落とし (4状態) ---
    # index の ZRANGE は namespace ごとに1回だけ (月ごとに再取得しない)。
    pairs = []  # (status, namespace, rid, month)
    for status, ns in _LEDGER_STATUS_NAMESPACES:
        for rid, month in _index_entries(f"{ns}:index"):
            if month in month_set:
                pairs.append((status, ns, rid, month))
    GET_CAP = 2000  # 応答サイズの上限ガード (取得は MGET バッチなので時間はかからない)
    if len(pairs) > GET_CAP:
        pairs = pairs[:GET_CAP]
        truncated = True
    monthly_records = _mget_records([f"{ns}:{rid}:{month}" for _, ns, rid, month in pairs])
    for (status, ns, rid, month), r in zip(pairs, monthly_records):
        if not r:
            continue  # TTL 切れ (成功 history は1年保存) は index に残っていても表示しない
        try:
            amount = int(r.get("amount", 0) or 0)
        except Exception:
            amount = 0
        try:
            at = int(r.get("charged_at") or r.get("failed_at") or r.get("noted_at") or 0)
        except Exception:
            at = 0
        entries.append({
            "kind": "monthly",
            "status": status,
            "month": month,
            "registrationId": rid,
            "studentName": r.get("student_name") or r.get("studentName") or "",
            "amount": amount,
            "chargedAt": at,
            "paymentIntentId": r.get("payment_intent_id", ""),
        })

    # --- 講習などの単発スポット課金 (spot:history:{rid}:{idem_token}) ---
    # index entry に月は無いので record の at (epoch) から JST 月を導出して割り当てる。
    spot_zr = _redis("ZRANGE", "spot:history:index", "0", "-1", "REV")
    spot_items = []
    if spot_zr and isinstance(spot_zr, dict) and isinstance(spot_zr.get("result"), list):
        spot_items = spot_zr["result"]
    SPOT_CAP = 300  # 新しい順に上限まで (古い spot が多い場合のみ切り捨て)
    if len(spot_items) > SPOT_CAP:
        spot_items = spot_items[:SPOT_CAP]
        truncated = True
    spot_pairs = []
    for entry in spot_items:
        if not isinstance(entry, str) or ":" not in entry:
            continue
        rid, _, token = entry.rpartition(":")
        spot_pairs.append((rid, token))
    spot_records = _mget_records([f"spot:history:{rid}:{token}" for rid, token in spot_pairs])
    for (rid, token), rec in zip(spot_pairs, spot_records):
        if not rec:
            continue
        month = _month_jst_from_ts(rec.get("at") or 0)
        if month not in month_set:
            continue
        try:
            amount = int(rec.get("amount", 0) or 0)
        except Exception:
            amount = 0
        try:
            at = int(rec.get("at") or 0)
        except Exception:
            at = 0
        entries.append({
            "kind": "spot",
            "status": rec.get("status", ""),
            "month": month,
            "registrationId": rid,
            "studentName": rec.get("student_name") or "",
            "amount": amount,
            "chargedAt": at,
            "label": rec.get("label", ""),
            "paymentIntentId": rec.get("payment_intent_id", ""),
            # webhook が status を確定更新した record にのみ付く (payment_intent.succeeded /
            # payment_intent.payment_failed)。フロントは「非同期で failed になった spot」
            # (= 塾長が同期モーダルで失敗を見ていない) を❌表示するための判別に使う (2026-07-02)。
            "sourceEvent": rec.get("source_event", ""),
        })

    _json(handler, 200, {
        "months": months,            # [翌月, 今月, 先月, ...] — 並べ替えはフロント側
        "current_month": current,
        "next_month": next_month,
        "fetched_at": int(time.time()),
        "entries": entries,
        "truncated": truncated,
    })


# ===== 未完了の登録 (カード未入力で放置・2026-07-06 塾長要望) =====
# 保護者が登録フォームを開始 (= Stripe Customer 作成) したがカード入力を完了せず reg:completed に
# 昇格していない層 = 月謝アプリに一切出ない「隠れ離脱」。register-subscribe.py が書く reg:pending
# (7日 TTL) と reg:index を読むだけの read-only 集計。書き込み・課金は一切しない。
# 同一 (email, 生徒) の再試行は最新1件に畳み、試行回数 (attempts) を添える (上村 4回等のノイズ抑制)。
_PENDING_TTL_SEC = 604800  # register-subscribe.py の reg:pending EX と一致 (7日)


def _norm_name(s):
    """氏名の重複判定キー用の正規化: 空白 (半角/全角 U+3000/タブ) を全除去。
    「上村　琥珀」(全角空白) と「上村琥珀」を同一生徒として畳むため。str.split() は
    全角空白も whitespace として扱う ('\\u3000'.isspace() is True)。表示名には使わない。"""
    return "".join((s or "").split())


def _handle_pending(handler):
    zr = _redis("ZRANGE", "reg:index", "0", "-1", "REV")
    ids = []
    if zr and isinstance(zr, dict) and isinstance(zr.get("result"), list):
        ids = [rid for rid in zr["result"] if isinstance(rid, str)]
    ids = ids[:1000]
    recs = _mget_records([f"reg:pending:{rid}" for rid in ids])

    now = int(time.time())
    fam = {}  # (email_lower, student) -> aggregated entry (最新を残し attempts を数える)
    for rid, r in zip(ids, recs):
        if not r:
            continue  # TTL 切れ (index にだけ残る幽霊) は表示しない
        email = (r.get("email") or "").strip()
        student = (r.get("studentName") or r.get("student_name") or "").strip()
        parent = (r.get("parentName") or r.get("parent_name") or "").strip()
        try:
            created = int(r.get("created_at") or 0)
        except Exception:
            created = 0
        try:
            monthly_fee = int(r.get("monthly_fee") or r.get("fee") or 0)
        except Exception:
            monthly_fee = 0
        el = email.lower()
        # 塾長自身のデバッグ/テスト登録を薄く分離 (現実は7日TTLで大半消えるが保険)
        is_test = (
            any(t in el for t in ("example.com", "deploy", "diag", "debug", "final_"))
            or "test" in el
            or student in ("山田たろう", "山田太郎", "テスト太郎", "duplicate test")
            or el in ("shock11090304@gmail.com", "shock918324@ezweb.ne.jp")
        )
        days_left = round((created + _PENDING_TTL_SEC - now) / 86400, 1) if created else 0
        item = {
            "registrationId": rid,
            "studentName": student,
            "parentName": parent,
            "grade": r.get("grade", ""),
            "email": email,
            "phone": r.get("phone", ""),
            "monthlyFee": monthly_fee,
            "feeBreakdown": r.get("fee_breakdown", ""),
            "customerId": r.get("stripe_customer_id", ""),
            "createdAt": created,
            "expiresAt": (created + _PENDING_TTL_SEC) if created else 0,
            "daysLeft": max(0, days_left),
            "source": r.get("source", ""),
            "isLikelyTest": is_test,
        }
        key = (el, _norm_name(student))
        prev = fam.get(key)
        if prev is None:
            item["attempts"] = 1
            fam[key] = item
        else:
            attempts = prev["attempts"] + 1
            if item["createdAt"] >= prev["createdAt"]:
                item["attempts"] = attempts
                fam[key] = item
            else:
                prev["attempts"] = attempts

    entries = sorted(fam.values(), key=lambda x: (x["isLikelyTest"], -x["createdAt"]))
    real = [e for e in entries if not e["isLikelyTest"]]
    _json(handler, 200, {
        "fetched_at": now,
        "count": len(entries),
        "real_count": len(real),
        "total_at_risk": sum(e["monthlyFee"] for e in real),
        "registrations": entries,
    })


def _route(self):
    """preview / history / ledger / pending を Vercel rewrite 挙動に依らず3層で判定。"""
    parsed = urlparse(self.path)
    params = parse_qs(parsed.query)
    known = ("preview", "history", "ledger", "pending")
    # (1) destination に埋め込んだ識別子 (一次・最も確実)
    ep = (params.get("__ep", [""])[0] or "").strip().lower()
    # (2) self.path が source を保持している場合のフォールバック
    if ep not in known:
        p = (parsed.path or "").lower()
        if "pending" in p:
            ep = "pending"
        elif "ledger" in p:
            ep = "ledger"
        elif "history" in p:
            ep = "history"
        elif "preview" in p or "month-end" in p:
            ep = "preview"
    # (3) クエリ特徴での最終フォールバック (ledger は months・history は month/type 付き・preview は無)
    if ep not in known:
        if "months" in params:
            ep = "ledger"
        elif any(k in params for k in ("month", "type", "include_audit", "audit_rid")):
            ep = "history"
        else:
            ep = "preview"
    return ep, params


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if not _verify_admin(self):
                _json(self, 401, {"error": "UNAUTHORIZED"})
                return
            ep, params = _route(self)
            if ep == "history":
                _handle_history(self, params)
            elif ep == "ledger":
                _handle_ledger(self, params)
            elif ep == "pending":
                _handle_pending(self)
            else:
                _handle_preview(self)
        except Exception as e:
            _log(f"readonly internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR", "message": str(e)})
