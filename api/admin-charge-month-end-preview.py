"""Vercel Function: 月末一斉引き落とし プレビュー

Endpoint: GET /payment/api/admin-charge-month-end-preview

塾長専用。`reg:completed:*` から全カード登録済顧客を読み、月末引き落としの
プレビュー (生徒/月額/カード有無) を返す。**実際の引き落としはここでは行わない**。

Response:
  {
    "month": "2026-05",
    "preview_at": 1714000000,
    "total_customers": 42,
    "total_amount": 856800,
    "ready_count": 40,
    "missing_card_count": 2,
    "previously_charged_this_month": 0,
    "customers": [
      {
        "registrationId": "reg_xxx",
        "customerId": "cus_xxx",
        "paymentMethodId": "pm_xxx",
        "studentName": "山田 太郎",
        "parentName": "山田 花子",
        "grade": "高校2年",
        "email": "yamada@example.com",
        "monthlyFee": 7500,
        "feeBreakdown": "中学2年 ¥7,500",
        "ready": true,
        "alreadyChargedThisMonth": false,
        "issue": null
      },
      ...
    ]
  }

認証: X-Admin-Password (CHAT_ADMIN_PASSWORD)
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import time
import hmac
import urllib.request
from datetime import datetime, timezone, timedelta


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
    now = datetime.now(JST)
    return now.strftime("%Y-%m")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if not _verify_admin(self):
                _json(self, 401, {"error": "UNAUTHORIZED"})
                return

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

            _json(self, 200, {
                "month": month_str,
                "preview_at": int(time.time()),
                "total_customers": len(customers),
                "total_amount": total_amount,
                "ready_count": ready_count,
                "missing_card_count": missing_card_count,
                "previously_charged_this_month": already_charged_count,
                "customers": customers,
            })
        except Exception as e:
            _log(f"preview internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR", "message": str(e)})
