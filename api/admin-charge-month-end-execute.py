"""Vercel Function: 月末一斉引き落とし 実行

Endpoint: POST /payment/api/admin-charge-month-end-execute

塾長専用。プレビューで確認した後にこの endpoint を叩くと、
全 ready 顧客の **月額をカードから一斉引き落とし** する。

Body (JSON):
  {
    "dryRun": false,                    // true: 実行せずシミュレーションのみ
    "registrationIds": ["reg_xxx", ...],  // 任意・特定 ID のみ実行する場合
    "confirmMonth": "2026-05"           // 必須・操作ミス防止 (現在月と一致しないと 400)
  }

Response (200):
  {
    "month": "2026-05",
    "executed_at": 1714000000,
    "dry_run": false,
    "results": [
      {"registrationId": "reg_xxx", "status": "success", "paymentIntentId": "pi_xxx", "amount": 7500},
      {"registrationId": "reg_yyy", "status": "skipped", "reason": "already charged this month"},
      {"registrationId": "reg_zzz", "status": "failed", "error": "card_declined"},
      ...
    ],
    "summary": {
      "total": 42,
      "success": 38,
      "failed": 2,
      "skipped": 2,
      "total_amount_charged": 712500
    }
  }

🚨 安全装置:
  1. dryRun=true でシミュレーション可能
  2. confirmMonth が現在月と一致しないと 400
  3. 各顧客の `charge:done:{rid}:{month}` を SET NX で原子的にチェック → 重複請求防止
  4. metadata.idempotency_key で Stripe 側でも重複防止
  5. Stripe API 失敗時は KV に失敗ログ + Stripe Dashboard で確認可能

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
import urllib.error
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


def _create_payment_intent(secret_key, customer_id, payment_method_id, amount, metadata, idempotency_key):
    """Stripe PaymentIntent 作成 + off_session 即時確定 (=保存済カードから引き落とし)"""
    form = [
        ("amount", str(amount)),
        ("currency", "jpy"),
        ("customer", customer_id),
        ("payment_method", payment_method_id),
        ("off_session", "true"),
        ("confirm", "true"),
    ]
    # 領収書: 有効なメールがある時のみ Stripe receipt_email を設定 (空文字は invalid_request_error)
    _email = (metadata.get("email") or "").strip()
    if _email and "@" in _email:
        form.append(("receipt_email", _email))
    # description (Stripe Dashboard 表示用)
    student = metadata.get("student_name", "")
    desc = f"AI学習コーチ塾 月謝 — {student} ({metadata.get('month', '')})"[:220]
    form.append(("description", desc))
    for k, v in metadata.items():
        if v is None: continue
        form.append((f"metadata[{k}]", str(v)[:240]))

    body = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(
        "https://api.stripe.com/v1/payment_intents",
        data=body,
        headers={
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Stripe-Version": "2024-06-20",
            "Idempotency-Key": idempotency_key,  # Stripe 側で重複防止
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            if not _verify_admin(self):
                _json(self, 401, {"error": "UNAUTHORIZED"})
                return

            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length > 0 else b""
            try:
                payload = json.loads(raw.decode("utf-8")) if raw else {}
            except Exception:
                _json(self, 400, {"error": "INVALID_JSON"})
                return

            dry_run = bool(payload.get("dryRun", False))
            confirm_month = (payload.get("confirmMonth") or "").strip()
            filter_ids = payload.get("registrationIds") or []
            if not isinstance(filter_ids, list):
                filter_ids = []

            current_month = _current_month_jst()
            if not dry_run and confirm_month != current_month:
                _json(self, 400, {
                    "error": "MONTH_MISMATCH",
                    "message": f"confirmMonth (現在月の確認) が一致しません。現在月は {current_month} です。",
                    "expected_month": current_month,
                })
                return

            secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
            if not secret_key:
                _json(self, 503, {"error": "STRIPE_SECRET_KEY_NOT_SET"})
                return

            # 全カード登録済顧客を取得
            zr = _redis("ZRANGE", "reg:completed:index", "0", "-1", "REV")
            ids = []
            if zr and isinstance(zr, dict):
                result = zr.get("result")
                if isinstance(result, list):
                    ids = result

            # filter (任意・特定 ID のみ)
            if filter_ids:
                allowed = set(filter_ids)
                ids = [rid for rid in ids if rid in allowed]

            results = []
            summary = {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "total_amount_charged": 0,
            }

            for rid in ids[:500]:
                summary["total"] += 1
                got = _redis("GET", f"reg:completed:{rid}")
                if not got or not isinstance(got, dict):
                    summary["skipped"] += 1
                    results.append({"registrationId": rid, "status": "skipped", "reason": "no data"})
                    continue
                s = got.get("result")
                if not s:
                    summary["skipped"] += 1
                    results.append({"registrationId": rid, "status": "skipped", "reason": "no data"})
                    continue
                try:
                    r = json.loads(s)
                except Exception:
                    summary["skipped"] += 1
                    results.append({"registrationId": rid, "status": "skipped", "reason": "parse error"})
                    continue

                customer_id = r.get("stripe_customer_id", "")
                payment_method_id = r.get("stripe_payment_method_id", "")
                monthly_fee = int(r.get("monthly_fee", 0) or 0)
                checkout_mode = r.get("checkout_mode", "")
                email = r.get("email", "")
                student_name = r.get("studentName") or r.get("student_name") or ""

                # ready 判定
                if checkout_mode != "setup":
                    summary["skipped"] += 1
                    results.append({"registrationId": rid, "status": "skipped",
                                    "reason": f"checkout_mode={checkout_mode} (バッチ対象外)"})
                    continue
                if not customer_id or not payment_method_id or monthly_fee <= 0:
                    summary["skipped"] += 1
                    results.append({"registrationId": rid, "status": "skipped",
                                    "reason": "customer/pm/fee 欠落"})
                    continue

                # 当月重複請求防止 (SET NX で原子的に判定)
                done_key = f"charge:done:{rid}:{current_month}"
                if not dry_run:
                    nx = _redis("SET", done_key, "pending", "NX", "EX", "5184000")  # 60 days TTL
                    if not nx or not isinstance(nx, dict) or nx.get("result") != "OK":
                        summary["skipped"] += 1
                        results.append({"registrationId": rid, "status": "skipped",
                                        "reason": "already charged this month"})
                        continue

                if dry_run:
                    summary["success"] += 1
                    summary["total_amount_charged"] += monthly_fee
                    results.append({
                        "registrationId": rid,
                        "status": "dry_run",
                        "studentName": student_name,
                        "amount": monthly_fee,
                        "customerId": customer_id,
                    })
                    continue

                # 実行
                # Idempotency-Key には amount を含める (金額変更時の retry で旧額 PI が返るのを防ぐ)
                idempotency = f"juku-monthly-{rid}-{current_month}-{monthly_fee}"
                pi_metadata = {
                    "system": "juku-payment-monthly",
                    "registration_id": rid,
                    "student_name": student_name,
                    "month": current_month,
                    "monthly_fee": str(monthly_fee),
                    "email": email,
                    "source": "month-end-batch-v1",
                }
                try:
                    pi = _create_payment_intent(secret_key, customer_id, payment_method_id,
                                                 monthly_fee, pi_metadata, idempotency)
                    pi_id = pi.get("id", "")
                    pi_status = pi.get("status", "")
                    if pi_status in ("succeeded", "processing"):
                        # 成功時: done_key を success にマーク
                        _redis("SET", done_key, json.dumps({
                            "payment_intent_id": pi_id,
                            "status": pi_status,
                            "amount": monthly_fee,
                            "charged_at": int(time.time()),
                        }, ensure_ascii=False), "EX", "5184000")
                        # 履歴に記録
                        _redis("ZADD", "charge:history:index", str(int(time.time())),
                               f"{rid}:{current_month}")
                        _history_record = {
                            "payment_intent_id": pi_id,
                            "registration_id": rid,
                            "month": current_month,
                            "amount": monthly_fee,
                            "student_name": student_name,
                            "email": email,
                            "phone": r.get("phone", ""),
                            "charged_at": int(time.time()),
                            "status": pi_status,
                            "source": "month-end-batch-v1",
                        }
                        _redis("SET", f"charge:history:{rid}:{current_month}", json.dumps(_history_record, ensure_ascii=False), "EX", "31536000")  # 1 year
                        # 🚨 3rd review fix: append-only 監査ログ (RPUSH list・税務監査用)
                        # メイン history は上書き OK だが、audit log は全試行を順序保存
                        _redis("RPUSH", f"charge:history:audit:{rid}:{current_month}", json.dumps(_history_record, ensure_ascii=False))
                        _redis("EXPIRE", f"charge:history:audit:{rid}:{current_month}", "31536000")  # 1 year
                        summary["success"] += 1
                        summary["total_amount_charged"] += monthly_fee
                        results.append({
                            "registrationId": rid,
                            "status": "success",
                            "paymentIntentId": pi_id,
                            "studentName": student_name,
                            "email": email,
                            "phone": r.get("phone", ""),
                            "amount": monthly_fee,
                            "stripeStatus": pi_status,
                        })
                    elif pi_status == "requires_action":
                        # 🚨 3DS 認証が必要 (off_session で SCA トリガー時)
                        # → done_key は保持 (重複請求防止) + 専用 index に保存
                        # → 顧客への確認 URL を返す (next_action.use_stripe_sdk または redirect_to_url)
                        next_action = pi.get("next_action", {}) or {}
                        redirect = (next_action.get("redirect_to_url") or {}).get("url", "")
                        _redis("SET", done_key, json.dumps({
                            "payment_intent_id": pi_id,
                            "status": "requires_action",
                            "amount": monthly_fee,
                            "noted_at": int(time.time()),
                        }, ensure_ascii=False), "EX", "5184000")
                        _redis("SET", f"charge:requires_action:{rid}:{current_month}", json.dumps({
                            "payment_intent_id": pi_id,
                            "registration_id": rid,
                            "month": current_month,
                            "amount": monthly_fee,
                            "student_name": student_name,
                            "email": email,
                            "phone": r.get("phone", ""),
                            "redirect_url": redirect,
                            "noted_at": int(time.time()),
                        }, ensure_ascii=False), "EX", "31536000")
                        _redis("ZADD", "charge:requires_action:index", str(int(time.time())),
                               f"{rid}:{current_month}")
                        summary["failed"] += 1
                        results.append({
                            "registrationId": rid,
                            "status": "requires_action",
                            "paymentIntentId": pi_id,
                            "studentName": student_name,
                            "email": email,
                            "phone": r.get("phone", ""),
                            "amount": monthly_fee,
                            "stripeStatus": pi_status,
                            "redirectUrl": redirect,
                            "error": "3DS 認証が必要 (顧客にメールでリンクが届きます・カード会社の本人確認後再請求が走ります)",
                        })
                    else:
                        # その他の status (canceled, failed 等) → 重複防止 lock を解除
                        _redis("DEL", done_key)
                        summary["failed"] += 1
                        results.append({
                            "registrationId": rid,
                            "status": "failed",
                            "paymentIntentId": pi_id,
                            "studentName": student_name,
                            "email": email,
                            "phone": r.get("phone", ""),
                            "amount": monthly_fee,
                            "stripeStatus": pi_status,
                            "error": f"unexpected status: {pi_status}",
                        })
                except urllib.error.HTTPError as e:
                    # Stripe API がエラーレスポンスを返した (= リクエストは届いた = 課金は走ってない)
                    # → DEL で lock 解除して再試行を許可
                    detail_raw = b""
                    try: detail_raw = e.read()
                    except Exception: pass
                    detail = detail_raw.decode("utf-8", errors="replace")[:500]
                    error_code = ""
                    decline_code = ""
                    try:
                        err_obj = json.loads(detail).get("error", {})
                        error_code = err_obj.get("code", "")
                        decline_code = err_obj.get("decline_code", "")
                    except Exception:
                        pass
                    # 🚨 Round 4 fix (BUG-2): "No such customer" / resource_missing → zombie 化して毎月失敗ループ防止
                    # Stripe Dashboard で塾長が直接 Customer 削除した場合等を捕捉
                    if error_code == "resource_missing" or "No such customer" in detail or "No such payment_method" in detail:
                        _redis("SET", f"reg:zombie:{rid}", json.dumps({
                            "registration_id": rid, "month": current_month,
                            "student_name": student_name, "email": email,
                            "reason": "Stripe customer/PM not found",
                            "error_code": error_code, "error_detail": detail[:200],
                            "marked_zombie_at": int(time.time()),
                        }, ensure_ascii=False), "EX", "31536000")
                        _redis("ZADD", "reg:zombie:index", str(int(time.time())), rid)
                        # 🚨 Round 5 fix (H1): reg:completed:index から削除のみ (preview に出ないが本体は保持)
                        # 本体を残すことで過去 history で studentName 引ける + 後で復活可能
                        _redis("ZREM", "reg:completed:index", rid)
                        _log(f"CRITICAL: reg={rid} zombie化 (Stripe customer/PM 消失・本体は保持) - 塾長要確認")
                    _redis("DEL", done_key)  # 重複防止 lock を解除 (Stripe 側で課金されていない確認済)
                    _redis("SET", f"charge:failed:{rid}:{current_month}", json.dumps({
                        "registration_id": rid,
                        "month": current_month,
                        "amount": monthly_fee,
                        "student_name": student_name,
                        "email": email,
                        "phone": r.get("phone", ""),
                        "error_code": error_code,
                        "decline_code": decline_code,
                        "error_detail": detail[:300],
                        "failed_at": int(time.time()),
                    }, ensure_ascii=False), "EX", "31536000")
                    _redis("ZADD", "charge:failed:index", str(int(time.time())),
                           f"{rid}:{current_month}")
                    summary["failed"] += 1
                    results.append({
                        "registrationId": rid,
                        "status": "failed",
                        "studentName": student_name,
                        "email": email,
                        "phone": r.get("phone", ""),
                        "amount": monthly_fee,
                        "errorCode": error_code,
                        "declineCode": decline_code,
                        "error": detail[:200],
                    })
                except urllib.error.URLError as e:
                    # 🚨 ネットワーク timeout / 接続切断: Stripe で課金されたか不明
                    # → done_key は保持 (二重課金リスク回避) + 専用 index に「要確認」として記録
                    # → 塾長が Stripe Dashboard で実際の状態を確認後、KV を手動修復する必要あり
                    _log(f"PI URLError reg={rid}: {e!r} - keeping lock (uncertain state)")
                    _redis("SET", done_key, json.dumps({
                        "status": "uncertain",
                        "amount": monthly_fee,
                        "idempotency_key": idempotency,
                        "noted_at": int(time.time()),
                        "error": str(e)[:200],
                    }, ensure_ascii=False), "EX", "5184000")
                    _redis("SET", f"charge:uncertain:{rid}:{current_month}", json.dumps({
                        "registration_id": rid,
                        "month": current_month,
                        "amount": monthly_fee,
                        "student_name": student_name,
                        "email": email,
                        "phone": r.get("phone", ""),
                        "idempotency_key": idempotency,
                        "error": str(e)[:300],
                        "noted_at": int(time.time()),
                    }, ensure_ascii=False), "EX", "31536000")
                    _redis("ZADD", "charge:uncertain:index", str(int(time.time())),
                           f"{rid}:{current_month}")
                    summary["failed"] += 1
                    results.append({
                        "registrationId": rid,
                        "status": "uncertain",
                        "studentName": student_name,
                        "email": email,
                        "phone": r.get("phone", ""),
                        "amount": monthly_fee,
                        "error": f"ネットワーク timeout - Stripe Dashboard で要確認: {str(e)[:150]}",
                    })
                except Exception as e:
                    # 想定外例外: 安全側で lock を保持 (URLError と同様の扱い)
                    _log(f"PI create unexpected error reg={rid}: {e!r} - keeping lock")
                    _redis("SET", done_key, json.dumps({
                        "status": "uncertain",
                        "amount": monthly_fee,
                        "idempotency_key": idempotency,
                        "noted_at": int(time.time()),
                        "error": str(e)[:200],
                    }, ensure_ascii=False), "EX", "5184000")
                    _redis("SET", f"charge:uncertain:{rid}:{current_month}", json.dumps({
                        "registration_id": rid,
                        "month": current_month,
                        "amount": monthly_fee,
                        "student_name": student_name,
                        "email": email,
                        "phone": r.get("phone", ""),
                        "idempotency_key": idempotency,
                        "error": str(e)[:300],
                        "noted_at": int(time.time()),
                    }, ensure_ascii=False), "EX", "31536000")
                    _redis("ZADD", "charge:uncertain:index", str(int(time.time())),
                           f"{rid}:{current_month}")
                    summary["failed"] += 1
                    results.append({
                        "registrationId": rid,
                        "status": "uncertain",
                        "studentName": student_name,
                        "email": email,
                        "phone": r.get("phone", ""),
                        "amount": monthly_fee,
                        "error": f"想定外エラー (要確認): {str(e)[:150]}",
                    })

            _json(self, 200, {
                "month": current_month,
                "executed_at": int(time.time()),
                "dry_run": dry_run,
                "results": results,
                "summary": summary,
            })
        except Exception as e:
            _log(f"execute internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR", "message": str(e)})
