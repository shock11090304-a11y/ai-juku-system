"""Vercel Function: 入金管理の読み取り専用GET 2系統を1関数に集約

このファイルは元々独立していた2つの Vercel Function を統合したもの:
  - 月末一斉引き落とし「プレビュー」 (旧 admin-charge-month-end-preview.py)
  - 月末引き落としの「過去履歴・失敗者一覧」 (旧 admin-charge-history.py)

統合理由: Vercel Hobby プランは「1デプロイあたり最大12 Serverless Functions」。
api/*.py が13個になるとデプロイ全体がビルド失敗し本番が前ビルドで凍結する
(過去 74e2c5fb / 216d9ac で同型対応の前例あり)。読み取り専用GETの2本を
1ファイルに畳んで枠を1つ空け、実課金POST系 (execute/reconcile/spot/past-due/
webhook/register-subscribe) には一切触れない。

Endpoints (vercel.json rewrite でいずれも本ファイルへ転送):
  GET /payment/api/admin-charge-month-end-preview          → __ep=preview
  GET /payment/api/admin-charge-history?month=&type=       → __ep=history

振り分けは Vercel rewrite の挙動に依存しないよう3層フォールバック:
  (1) destination に埋め込んだ ?__ep=preview / ?__ep=history (一次)
  (2) self.path に history / preview(month-end) が含まれるか (source保持時)
  (3) クエリに month/type/include_audit/audit_rid があれば history・無ければ preview

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


def _verify_admin(handler):
    expected = os.environ.get("CHAT_ADMIN_PASSWORD", "").strip()
    if not expected:
        return False
    got = handler.headers.get("X-Admin-Password", "").strip()
    return hmac.compare_digest(got, expected) if got else False


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
    month_str = _current_month_jst()

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
        })

    _json(handler, 200, {
        "month": month_str,
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


def _route(self):
    """preview か history かを Vercel rewrite 挙動に依らず3層で判定。"""
    parsed = urlparse(self.path)
    params = parse_qs(parsed.query)
    # (1) destination に埋め込んだ識別子 (一次・最も確実)
    ep = (params.get("__ep", [""])[0] or "").strip().lower()
    # (2) self.path が source を保持している場合のフォールバック
    if ep not in ("preview", "history"):
        p = (parsed.path or "").lower()
        if "history" in p:
            ep = "history"
        elif "preview" in p or "month-end" in p:
            ep = "preview"
    # (3) クエリ特徴での最終フォールバック (history は常に month/type 付き・preview は無)
    if ep not in ("preview", "history"):
        if any(k in params for k in ("month", "type", "include_audit", "audit_rid")):
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
            else:
                _handle_preview(self)
        except Exception as e:
            _log(f"readonly internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR", "message": str(e)})
