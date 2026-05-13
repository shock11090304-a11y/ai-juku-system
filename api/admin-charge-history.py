"""Vercel Function: 月末引き落としの過去履歴・失敗者一覧

Endpoint: GET /payment/api/admin-charge-history?month=2026-05&type=all

塾長専用。失敗/3DS要/uncertain/成功の全 status を月別に返す。
結果モーダルを閉じた後でも、失敗者の連絡先と PaymentIntentId を確認できる。

Query params:
  month  - "YYYY-MM" 形式 (省略時は現在月)
  type   - "all" (既定) / "success" / "failed" / "requires_action" / "uncertain"

Response:
  {
    "month": "2026-05",
    "fetched_at": 1714000000,
    "success": [{"registrationId": "reg_xxx", "studentName": "...", "amount": 7500, "paymentIntentId": "pi_xxx", "chargedAt": ..., "email": "...", "phone": "..."}],
    "failed": [{... "errorCode": "card_declined", "errorDetail": "..."}],
    "requires_action": [{... "redirectUrl": "https://..."}],
    "uncertain": [{... "idempotencyKey": "...", "errorDetail": "..."}],
    "summary": {
      "success_count": 38,
      "failed_count": 2,
      "requires_action_count": 1,
      "uncertain_count": 0,
      "total_amount_charged": 712500
    }
  }

認証: X-Admin-Password (CHAT_ADMIN_PASSWORD)
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


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if not _verify_admin(self):
                _json(self, 401, {"error": "UNAUTHORIZED"})
                return

            # クエリパラメータ
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
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

            _json(self, 200, result)
        except Exception as e:
            _log(f"history internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR", "message": str(e)})
