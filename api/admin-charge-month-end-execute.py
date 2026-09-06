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


def _month_label_ja(month):
    """'YYYY-MM' → 'YYYY年M月分' (請求 description 用・形式外はそのまま)"""
    m = (month or "").strip()
    parts = m.split("-")
    if len(parts) == 2 and len(parts[0]) == 4 and parts[0].isdigit() and parts[1].isdigit():
        return f"{parts[0]}年{int(parts[1])}月分"
    return m


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
    JST = timezone(timedelta(hours=9))
    return datetime.now(JST).strftime("%Y-%m")


def _allowed_charge_months(current_ym, back=3, fwd=1):
    """current_ym ("YYYY-MM") と直前 back ヶ月・直後 fwd ヶ月の集合を返す
    (請求対象月をサーバ側でホワイトリスト化)。
    fwd=1 は「月末に翌月分を請求する」運用 (2026-06-26 塾長要望) のための翌月分。
    fwd を超える未来月・back を超える古すぎる月は弾く。集合の要素は必ず整形済み YYYY-MM。"""
    try:
        y, m = int(current_ym[:4]), int(current_ym[5:7])
    except Exception:
        return {current_ym}
    out = set()
    for i in range(-fwd, back + 1):
        yy, mm = y, m - i
        while mm <= 0:
            mm += 12
            yy -= 1
        while mm > 12:
            mm -= 12
            yy += 1
        out.add(f"{yy:04d}-{mm:02d}")
    return out


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
    desc = f"通塾月謝 — {student} ({_month_label_ja(metadata.get('month', ''))})"[:220]
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
            # registrationIds の扱い (誤一斉課金を防ぐ fail-closed 設計):
            #   キー無し / null              → 全 ready 対象 (従来動作・「未指定」扱い)
            #   1件以上のリスト              → その ID のみ請求
            #   空配列 [] / リスト以外の不正値 → 対象 0 件 (フロントのバグや壊れた入力で全員へ誤課金しない安全側)
            has_filter = ("registrationIds" in payload) and (payload.get("registrationIds") is not None)
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

            # 滞納分 / 翌月前倒し対応: chargeMonth が指定されたら、その月を請求対象にする。
            # 安全のためサーバ側で「翌月＋現在月＋直前3ヶ月」に限定 (それ以外の未来月・古すぎる月は弾く)。
            # 翌月 (fwd=1) は「月末に翌月分を請求する」運用のため (2026-06-26 塾長要望)。
            # 未指定なら従来どおり現在月。confirmMonth ガードは上で「現在月」に対して既に通過済み
            # (operator は現在月を確認済み)。金額は常にサーバ保存の monthly_fee (クライアント金額は不使用)。
            # current_month を target 月に rebind するだけで、以降の done_key / idempotency / history /
            # results が全てその月になる (請求ループ本体は無改変)。
            charge_month_req = (payload.get("chargeMonth") or "").strip()
            if charge_month_req:
                allowed_months = _allowed_charge_months(current_month, 3)
                if charge_month_req not in allowed_months:
                    _json(self, 400, {
                        "error": "CHARGE_MONTH_OUT_OF_RANGE",
                        "message": f"chargeMonth ({charge_month_req}) は対象外です。現在月＋直前3ヶ月のみ請求できます。",
                        "allowed_months": sorted(allowed_months),
                    })
                    return
                current_month = charge_month_req

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

            # filter (任意・特定 ID のみ)。has_filter=True なら空配列でも適用し、
            # 「空配列=全員」フォールバックを防ぐ (誤一斉課金の防止)。
            if has_filter:
                allowed = set(filter_ids)
                ids = [rid for rid in ids if rid in allowed]

            # 🚨 2026-07-02 fix (3並列review P1): 失敗記録がある月の再請求は Idempotency-Key に
            # 失敗世代 salt (charge:failed の failed_at) を混ぜる。
            # 決定的キーのままだと Stripe Idempotency (24h) が「元リクエストの作成レスポンス」を
            # そのまま replay するため、
            #  - Dashboard で PI キャンセル → 台帳❌ → 当日中の💳個別請求 が canceled 済み PI の
            #    requires_action スナップショットを返し、終端 PI の 🔐 ゾンビ (RA record + done
            #    ロック 60日) を再生産する
            #  - カード decline → 当日中の再請求 も実試行されず旧 decline を replay する
            # salt は同一失敗世代内で不変 (連打しても同一キー) なので二重請求防御は従来どおり。
            # KV 全断時は salt 無し (=従来キー) に degrade する (done NX も失敗し請求自体 skip)。
            # ★MGET だけ瞬断で落ちた場合は無 salt キーで旧応答 replay を踏み得るが、課金は
            #   発生しない (Stripe は保存済み応答を返すだけ)。🔐 が再発したら履歴 ❌ 行の
            #   🔁再請求 (mark_unpaid→retry・乱数キー) で回復できる。
            ids_capped = ids[:500]
            failed_salts = {}
            if not dry_run and ids_capped:
                _fkeys = [f"charge:failed:{_r}:{current_month}" for _r in ids_capped]
                for _i in range(0, len(_fkeys), 400):
                    _mres = _redis("MGET", *_fkeys[_i:_i + 400])
                    _vals = _mres.get("result") if (_mres and isinstance(_mres, dict)) else None
                    if not isinstance(_vals, list) or len(_vals) != len(_fkeys[_i:_i + 400]):
                        continue
                    for _rid, _v in zip(ids_capped[_i:_i + 400], _vals):
                        if not _v:
                            continue
                        try:
                            _fa = int(json.loads(_v).get("failed_at") or 0)
                        except Exception:
                            _fa = 0
                        if _fa:
                            failed_salts[_rid] = _fa

            results = []
            summary = {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "total_amount_charged": 0,
            }

            for rid in ids_capped:
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
                # + 失敗記録がある月は失敗世代 salt を付与 (上の failed_salts 参照・replay 回避)
                idempotency = f"juku-monthly-{rid}-{current_month}-{monthly_fee}"
                if failed_salts.get(rid):
                    idempotency = f"{idempotency}-r{failed_salts[rid]}"
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
                        # 🚨 2026-07-02 fix (round3 review): mark_unpaid 由来の tombstone を解除
                        # (reconcile retry の成功時と同じ規約)。残すと以後30日、この月の
                        # payment_intent.succeeded (async 承認の確定) が auto-reconcile されず
                        # 台帳反映が止まる。★requires_action 分岐では消さない: uncertain 起点の
                        # 旧 PI 幽霊復活防止が tombstone の本来目的で、RA 中は月が未決着のため。
                        _redis("DEL", f"charge:unpaid-tombstone:{rid}:{current_month}")
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
