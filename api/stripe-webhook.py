"""Vercel Function: Stripe Webhook 受信

Endpoint: POST /payment/api/stripe-webhook
  (vercel.json の rewrites で /api/stripe-webhook に流れる)

Stripe Dashboard 設定:
  Developers → Webhooks → Add endpoint
    URL:    https://www.trillion-ai-juku.com/payment/api/stripe-webhook
    Events: checkout.session.completed
            invoice.payment_failed
            invoice.payment_succeeded
            customer.subscription.deleted
            payment_intent.succeeded   (🆕 v2 月末バッチ請求用)
            payment_intent.payment_failed   (🆕 v2 バッチ請求失敗時)
            payment_intent.canceled    (🆕 2026-07-02 塾長が Dashboard で要確認 PI を
                                        キャンセルした時の掃除用。★Dashboard の webhook
                                        endpoint にこのイベントの購読追加が必要。
                                        ★順序: デプロイ反映確認 → 購読追加 の順を厳守
                                        — 先に購読すると旧コードが webhook:seen に 24h
                                        焼き付け、Resend も duplicate 扱いになる)

Env:
  STRIPE_WEBHOOK_SECRET   Stripe webhook signing secret (whsec_...)
  KV_REST_API_URL         Upstash Redis REST URL (Vercel KV 自動付与)
  KV_REST_API_TOKEN       Upstash Redis REST token

機能:
  1. checkout.session.completed → KV pending → completed に更新、registrations index に追加
  2. invoice.payment_failed → KV failures index に追加 (塾長ダッシュで一覧表示用)
  3. customer.subscription.deleted → KV cancellations index に追加
  4. その他のイベントは ack のみして無視 (安全)

依存: 標準ライブラリのみ
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import time
import hmac
import hashlib
import urllib.request
import urllib.error


def _log(msg):
    try:
        print(msg, file=sys.stderr, flush=True)
    except Exception:
        pass


def _json(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _redis_safe(*args):
    url = os.environ.get("KV_REST_API_URL", "").strip()
    token = os.environ.get("KV_REST_API_TOKEN", "").strip()
    if not url or not token:
        return None
    try:
        body = json.dumps(list(args)).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        _log(f"redis error: {e}")
        return None


def _verify_signature(raw_payload: bytes, sig_header: str, secret: str, tolerance: int = 300) -> bool:
    """Stripe-Signature ヘッダ: t=1234,v1=hex,v1=hex,...
    timing-safe HMAC-SHA256 検証 + timestamp tolerance (default 5min)
    """
    if not sig_header or not secret:
        return False
    try:
        items = dict(item.split("=", 1) for item in sig_header.split(",") if "=" in item)
    except Exception:
        return False
    timestamp = items.get("t")
    if not timestamp:
        return False
    # v1 が複数ある場合は最初の v1
    sigs = []
    for part in sig_header.split(","):
        k, _, v = part.partition("=")
        if k == "v1":
            sigs.append(v)
    if not sigs:
        return False
    try:
        ts_int = int(timestamp)
    except Exception:
        return False
    if abs(int(time.time()) - ts_int) > tolerance:
        return False
    signed = f"{timestamp}.".encode() + raw_payload
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, s) for s in sigs)


def _stripe_get(secret_key, path):
    """Stripe GET API helper (SetupIntent 取得用)"""
    if not secret_key:
        return None
    try:
        req = urllib.request.Request(
            f"https://api.stripe.com/v1/{path}",
            headers={
                "Authorization": f"Bearer {secret_key}",
                "Stripe-Version": "2024-06-20",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        _log(f"stripe GET {path} error: {e}")
        return None


def _handle_checkout_completed(event):
    """🆕 v2 (2026-05-13): mode=setup 対応。
    旧 mode=subscription も後方互換のため一応動くようにしておく。
    """
    obj = event.get("data", {}).get("object", {})
    session_id = obj.get("id", "")
    metadata = obj.get("metadata", {}) or {}
    reg_id = metadata.get("registration_id", "")
    customer = obj.get("customer", "")
    subscription = obj.get("subscription", "")  # mode=subscription 時のみ存在
    setup_intent_id = obj.get("setup_intent", "")  # mode=setup 時のみ存在
    mode = obj.get("mode", "")
    amount = obj.get("amount_total", 0)
    email = obj.get("customer_email") or obj.get("customer_details", {}).get("email", "")

    # 🚨 AIコーチングとの完全分離: system metadata で識別
    # juku-payment 系 (system=juku-payment-monthly or reg_id 有り) 以外は skip
    system_tag = metadata.get("system", "")
    if not reg_id and system_tag != "juku-payment-monthly":
        _log(f"webhook: not juku-payment event (mode={mode} system={system_tag}) — skip")
        return

    if not reg_id:
        _log(f"webhook: missing registration_id (mode={mode}) — skip")
        return

    # 🆕 mode=setup: SetupIntent から payment_method を取得
    # 🚨 2nd review fix: STRIPE_SECRET_KEY 未設定時の warning + customer 取得 fallback
    payment_method = ""
    monthly_fee = 0
    setup_intent_customer = ""  # SetupIntent.customer (Customer 取得 fallback)
    if mode == "setup" and setup_intent_id:
        secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
        if not secret_key:
            _log(f"webhook CRITICAL: STRIPE_SECRET_KEY missing in webhook env (rid={reg_id}) - payment_method will be empty")
        si = _stripe_get(secret_key, f"setup_intents/{setup_intent_id}") if secret_key else None
        if si and isinstance(si, dict):
            payment_method = si.get("payment_method") or ""
            setup_intent_customer = si.get("customer") or ""
        # metadata.monthly_fee は register-subscribe.py で必ず設定される
        try:
            monthly_fee = int(metadata.get("monthly_fee", "0"))
        except Exception:
            monthly_fee = 0

    # 🚨 fallback: session.customer が空でも SetupIntent.customer から復元
    if not customer and setup_intent_customer:
        customer = setup_intent_customer
        _log(f"webhook: customer fallback from SetupIntent rid={reg_id} customer={customer}")

    # pending → completed (KV 失敗時は metadata から最低限復元)
    existing_raw = _redis_safe("GET", f"reg:pending:{reg_id}")
    existing = {}
    if existing_raw and isinstance(existing_raw, dict):
        r = existing_raw.get("result")
        if r:
            try: existing = json.loads(r)
            except Exception: pass
    # KV pending が消失していても Stripe metadata から最低限の情報を復元
    if not existing:
        existing = {
            "registration_id": reg_id,
            "student_name": metadata.get("student_name", ""),
            "grade": metadata.get("grade", ""),
            "parent_name": metadata.get("parent_name", ""),
            "phone": metadata.get("phone", ""),
            "courses": [c for c in metadata.get("courses", "").split(",") if c],
            "options": [o for o in metadata.get("options", "").split(",") if o],
            "fee_breakdown": metadata.get("fee_breakdown", ""),
            "restored_from_metadata": True,
        }
    # 🆕 mode によって record の意味が異なる:
    #   mode=setup       : amount=0 / payment_method 必須 / monthly_fee で月額保存
    #   mode=subscription: amount=初回課金額 / subscription_id 必須 (legacy)
    record = {
        **existing,
        "registration_id": reg_id,
        "session_id": session_id,
        "stripe_customer_id": customer,
        "stripe_subscription_id": subscription,  # setup 時は空
        "stripe_payment_method_id": payment_method,  # 🆕 setup 時のみ
        "stripe_setup_intent_id": setup_intent_id,  # 🆕 setup 時のみ
        "checkout_mode": mode,  # "setup" or "subscription"
        "status": "completed",
        "completed_at": int(time.time()),
        "amount": amount,  # setup 時は 0
        "monthly_fee": monthly_fee or existing.get("monthly_fee", 0),  # 🆕 月額 (バッチ請求用)
        "email": email or existing.get("email", ""),
        "system": "juku-payment-monthly",
    }
    _redis_safe("SET", f"reg:completed:{reg_id}", json.dumps(record, ensure_ascii=False))
    _redis_safe("DEL", f"reg:pending:{reg_id}")
    _redis_safe("ZADD", "reg:completed:index", str(record["completed_at"]), reg_id)
    _log(f"webhook: completed reg={reg_id} mode={mode} customer={customer} pm={payment_method} monthly_fee={monthly_fee}")


def _handle_payment_failed(event):
    # 🚨 Round 4 fix (C-EXIST-1): juku-payment 系のみ処理 (AIコーチング invoice event の混入防止)
    obj = event.get("data", {}).get("object", {})
    meta = obj.get("metadata", {}) or {}
    sub_meta = (obj.get("subscription_details") or {}).get("metadata", {}) or {}
    sys_tag = (meta.get("system") or sub_meta.get("system") or "").strip()
    if sys_tag and not sys_tag.startswith("juku-payment"):
        _log(f"webhook: invoice.payment_failed skipped (system={sys_tag} - not juku-payment)")
        return
    invoice_id = obj.get("id", "")
    customer = obj.get("customer", "")
    subscription = obj.get("subscription", "")
    amount_due = obj.get("amount_due", 0)
    next_attempt = obj.get("next_payment_attempt")
    email = obj.get("customer_email", "")
    failure_msg = (obj.get("last_finalization_error") or {}).get("message", "") or ""

    record = {
        "invoice_id": invoice_id,
        "stripe_customer_id": customer,
        "stripe_subscription_id": subscription,
        "amount_due": amount_due,
        "next_attempt": next_attempt,
        "email": email,
        "failure_message": failure_msg[:300],
        "failed_at": int(time.time()),
    }
    _redis_safe("SET", f"pay:failed:{invoice_id}", json.dumps(record, ensure_ascii=False))
    _redis_safe("ZADD", "pay:failed:index", str(record["failed_at"]), invoice_id)
    _log(f"webhook: payment_failed invoice={invoice_id} amount={amount_due}")


def _handle_subscription_deleted(event):
    # 🚨 Round 4 fix (C-EXIST-1): juku-payment 系のみ処理 (AIコーチング subscription event の混入防止)
    obj = event.get("data", {}).get("object", {})
    meta = obj.get("metadata", {}) or {}
    sys_tag = (meta.get("system") or "").strip()
    if sys_tag and not sys_tag.startswith("juku-payment"):
        _log(f"webhook: subscription_deleted skipped (system={sys_tag} - not juku-payment)")
        return
    sub_id = obj.get("id", "")
    customer = obj.get("customer", "")
    canceled_at = obj.get("canceled_at") or int(time.time())
    record = {
        "stripe_subscription_id": sub_id,
        "stripe_customer_id": customer,
        "canceled_at": canceled_at,
        "metadata": meta,
    }
    _redis_safe("SET", f"sub:canceled:{sub_id}", json.dumps(record, ensure_ascii=False))
    _redis_safe("ZADD", "sub:canceled:index", str(canceled_at), sub_id)
    _log(f"webhook: subscription_deleted sub={sub_id}")


def _handle_payment_succeeded(event):
    """invoice.payment_succeeded — 月次サブスク or 過去未納分の請求書が支払われた時"""
    obj = event.get("data", {}).get("object", {})
    # 🚨 Round 4 fix (C-EXIST-1): juku-payment 系のみ処理 (AIコーチング invoice 混入防止)
    # 🆕 2026-08-16: subscription_details.metadata も見る (_handle_payment_failed と対称)。
    #   invoice 自体の metadata は空が普通で、神テスト (kamitest-subscription) のサブスク
    #   請求書がここを素通りして月謝の pay:succeeded 台帳に混ざっていた。
    metadata = obj.get("metadata", {}) or {}
    sub_meta = (obj.get("subscription_details") or {}).get("metadata", {}) or {}
    sys_tag = (metadata.get("system") or sub_meta.get("system") or "").strip()
    if sys_tag and not sys_tag.startswith("juku-payment"):
        _log(f"webhook: invoice.payment_succeeded skipped (system={sys_tag} - not juku-payment)")
        return
    invoice_id = obj.get("id", "")
    customer = obj.get("customer", "")
    subscription = obj.get("subscription", "")
    amount_paid = obj.get("amount_paid", 0)
    source = metadata.get("source", "")
    student_name = metadata.get("student_name", "")
    month = metadata.get("month", "")

    record = {
        "invoice_id": invoice_id,
        "stripe_customer_id": customer,
        "stripe_subscription_id": subscription,
        "amount_paid": amount_paid,
        "metadata": metadata,
        "paid_at": int(time.time()),
        "source": source,
    }
    _redis_safe("SET", f"pay:succeeded:{invoice_id}", json.dumps(record, ensure_ascii=False))
    _redis_safe("ZADD", "pay:succeeded:index", str(record["paid_at"]), invoice_id)

    # past-due 由来なら専用 index にも記録 (塾長ダッシュ用)
    if source == "past-due-invoice-v1":
        _redis_safe("SET", f"pastdue:paid:{invoice_id}", json.dumps(record, ensure_ascii=False))
        _redis_safe("ZADD", "pastdue:paid:index", str(record["paid_at"]), invoice_id)
        _log(f"webhook: past-due paid invoice={invoice_id} student={student_name} month={month} amount={amount_paid}")
    else:
        _log(f"webhook: payment_succeeded invoice={invoice_id} amount={amount_paid}")


def _clear_charge_source_state(source_state, rid, month):
    """月次 auto-reconcile 完了時の中間 state 掃除 (record DEL + index ZREM)。
    mark_paid / mark_unpaid (admin-charge-reconcile.py) も uncertain / requires_action の
    両 namespace をこれと同じ規約で掃除する (2026-07-02 fix: 従来 reconcile は uncertain
    のみで、mark_paid で決着させた RA record が TTL 1年残る残課題があった → 解消済み)。
    🚨 2026-07-02 fix: uncertain 側も index から ZREM する (従来は record DEL のみで
    index にゴミが残り、台帳の MGET 枠 (GET_CAP) を無駄に食っていた)。"""
    if source_state == "uncertain":
        _redis_safe("DEL", f"charge:uncertain:{rid}:{month}")
        _redis_safe("ZREM", "charge:uncertain:index", f"{rid}:{month}")
    elif source_state == "requires_action":
        _redis_safe("DEL", f"charge:requires_action:{rid}:{month}")
        _redis_safe("ZREM", "charge:requires_action:index", f"{rid}:{month}")


def _update_spot_history(meta, pi_id, new_status, source_event):
    """🆕 2026-07-02: 講習など単発スポット課金 (admin-charge-spot.py) の record を
    Stripe event で確定更新する。spot:history は同期 response 時の書き切りで、
    requires_action (3DS) → 顧客の認証完了後に succeeded へ更新する経路が無く、
    台帳 (admin-charge-ledger) で「🎓⚠️要確認」のまま永久に残っていた。
    record key は PI metadata の registration_id + idem_token から再構成する
    (idem_token は admin-charge-spot.py が metadata に焼き込む。無い旧 PI は skip)。"""
    rid = (meta.get("registration_id") or "").strip()
    token = (meta.get("idem_token") or "").strip()
    if not rid or not token:
        _log(f"webhook: spot PI missing registration_id/idem_token metadata pi={pi_id} - skip spot reconcile")
        return
    key = f"spot:history:{rid}:{token}"
    got = _redis_safe("GET", key)
    rec = None
    if got and isinstance(got, dict) and got.get("result"):
        try:
            parsed = json.loads(got["result"])
            if isinstance(parsed, dict):
                rec = parsed
        except Exception:
            pass
    if not rec:
        # 同期 response がまだ record を書いていない (即時成功時は webhook が先着し得る)
        # or TTL 切れ → 同期側の書込を正とする / 触らない
        _log(f"webhook: spot record not found key={key} pi={pi_id} - skip")
        return
    cur = (rec.get("status") or "").strip()
    if cur == new_status:
        return  # 冪等 (Stripe event 再送)
    if cur == "succeeded":
        # out-of-order な failed event で確定成功を降格させない。
        # ★processing は非終端 status (Stripe は processing → payment_failed に正規遷移し得る)
        # なのでここでは守らない = processing → failed は正当な前進遷移として通す (2026-07-02 review)
        _log(f"webhook: spot skip downgrade key={key} {cur} -x-> {new_status} pi={pi_id}")
        return
    if new_status == "failed" and cur not in ("requires_action", "uncertain", "processing"):
        # 同期側で確定済みの failed の再書込は不要・想定外 status からの failed 化はしない
        _log(f"webhook: spot skip failed-transition key={key} cur={cur} pi={pi_id}")
        return
    rec_pi = (rec.get("payment_intent_id") or "").strip()
    if rec_pi and pi_id and rec_pi != pi_id:
        # 同一 idem_token で別 PI は Idempotency-Key 上ありえない → 触らず要調査ログのみ
        _log(f"webhook: spot PI mismatch key={key} rec_pi={rec_pi} event_pi={pi_id} - skip")
        return
    rec["status"] = new_status
    if pi_id and not rec_pi:
        rec["payment_intent_id"] = pi_id
    rec["status_updated_at"] = int(time.time())
    rec["source_event"] = source_event
    # "at" は変更しない (台帳の月割り当ては at 由来。3DS 完了が月を跨いでも請求起票月に留める)
    rec_json = json.dumps(rec, ensure_ascii=False)
    _redis_safe("SET", key, rec_json, "EX", "31536000")  # 1y (spot.py の _record と同じ)
    # index 自己修復: 書込時に ZADD だけ落ちた個体を台帳に復帰させる
    # (score = record の at = 元の起票時刻なので、既存 entry は score 不変 = 順序も不変・冪等)
    try:
        _at_score = int(rec.get("at") or 0) or int(time.time())
    except Exception:
        _at_score = int(time.time())
    _redis_safe("ZADD", "spot:history:index", str(_at_score), f"{rid}:{token}")
    _redis_safe("RPUSH", f"spot:history:audit:{rid}", rec_json)
    _redis_safe("EXPIRE", f"spot:history:audit:{rid}", "31536000")
    _log(f"webhook: spot {cur} -> {new_status} rid={rid} token={token} pi={pi_id}")


def _handle_payment_intent_succeeded(event):
    """🆕 v2 (2026-05-13): 月末バッチ請求の PaymentIntent 成功 event を非同期 reconcile 用に記録。
    execute.py が同期 response で既に charge:history を書いているが、SCA 後の銀行 async 承認 etc で
    後から成功になる case を捕捉するための補完。
    """
    obj = event.get("data", {}).get("object", {})
    meta = obj.get("metadata", {}) or {}
    # 🚨 Round 5 fix (C2): 既存 3 handler と統一して startswith 判定 (空文字 = 既存挙動維持)
    # 将来 juku-payment-yearly 等の派生 system を追加した時にも自動的に処理対象になる
    _pi_sys = (meta.get("system") or "").strip()
    if _pi_sys and not _pi_sys.startswith("juku-payment"):
        _log(f"webhook: PaymentIntent skipped (system={_pi_sys} - not juku-payment)")
        return
    pi_id = obj.get("id", "")
    customer = obj.get("customer", "")
    amount = obj.get("amount_received", 0) or obj.get("amount", 0)
    rid = meta.get("registration_id", "")
    month = meta.get("month", "")
    record = {
        "payment_intent_id": pi_id,
        "stripe_customer_id": customer,
        "registration_id": rid,
        "month": month,
        "amount": amount,
        "metadata": meta,
        "status": "succeeded",
        "succeeded_at": int(time.time()),
        "source_event": "payment_intent.succeeded",
    }
    _redis_safe("SET", f"pi:succeeded:{pi_id}", json.dumps(record, ensure_ascii=False), "EX", "31536000")
    _redis_safe("ZADD", "pi:succeeded:index", str(record["succeeded_at"]), pi_id)
    # 🆕 2026-07-02: 単発スポット課金 (admin-charge-spot.py) は月次 reconcile 対象外。
    # spot:history の status を succeeded に確定して終了 (3DS 完了・async 承認の反映)。
    if _pi_sys == "juku-payment-spot":
        _update_spot_history(meta, pi_id, "succeeded", "payment_intent.succeeded")
        _log(f"webhook: payment_intent.succeeded (spot) rid={rid} pi={pi_id} amount={amount}")
        return
    # 🚨 2nd/3rd/4th review fix: 自動 reconcile (uncertain + requires_action 両方の case を処理)
    # done_key が既に他の status (succeeded/manually_reconciled/retry) で確定済なら override しない
    # tombstone (unpaid マーク済) があれば auto-reconcile を完全に skip (幽霊復活防止)
    if rid and month:
        uncertain_key = f"charge:uncertain:{rid}:{month}"
        requires_action_key = f"charge:requires_action:{rid}:{month}"
        done_key = f"charge:done:{rid}:{month}"
        tombstone_key = f"charge:unpaid-tombstone:{rid}:{month}"
        tombstone_check = _redis_safe("GET", tombstone_key)
        tombstone_active = bool(tombstone_check and isinstance(tombstone_check, dict) and tombstone_check.get("result"))
        if tombstone_active:
            # 🚨 2026-07-02 fix (df439e6 3並列review 残穴②): PI 非照合の無差別ミュートをやめる。
            # mark_unpaid → 💳個別請求/retry → 新 PI が再び requires_action → 顧客が 3DS 完了、
            # の succeeded が握り潰され、回収済みなのに台帳が 🔐 のまま最大 30 日 (tombstone TTL)
            # 止まっていた (execute/retry は成功分岐でしか tombstone を DEL しない)。判定は2段:
            # ① RA record の payment_intent_id と event PI の完全一致 → 通す。
            #    mark_unpaid は RA record を必ず DEL するため、tombstone と併存する RA record は
            #    tombstone より「後」の新試行 (execute/retry の RA 分岐) が書いたもの = その PI は
            #    幽霊ではあり得ない。時刻比較では区別できない同一秒 (UI の mark_unpaid→retry 自動
            #    連鎖で常態的に起きる)・clock skew・Idempotency replay で created が古い正当回収も
            #    これで救う (2026-07-03 3並列review P1)。
            # ② fallback: tombstone の marked_at と PI の created の時刻比較 (canceled handler
            #    ガード3 の canceled_at vs noted_at と同型)。RA record に PI が無い uncertain 起点
            #    向け。created >= marked_at なら新試行 = 通す (「未課金」と確定判断した旧 PI が
            #    判断と同一秒に作成されることは物理的にないため >= が安全)。
            #    marked_at / created が取れない場合は安全側 = ミュート維持。
            ra_probe_pi = ""
            _ra_probe = _redis_safe("GET", requires_action_key)
            if _ra_probe and isinstance(_ra_probe, dict) and _ra_probe.get("result"):
                try:
                    _ra_probe_rec = json.loads(_ra_probe["result"])
                    if isinstance(_ra_probe_rec, dict):
                        ra_probe_pi = (_ra_probe_rec.get("payment_intent_id") or "").strip()
                except Exception:
                    ra_probe_pi = ""
            if pi_id and ra_probe_pi and ra_probe_pi == pi_id:
                tombstone_active = False
                _log(f"webhook: tombstone bypassed (event PI matches live RA record) rid={rid} month={month} pi={pi_id}")
            else:
                marked_at_ts = 0
                try:
                    _tomb = json.loads(tombstone_check["result"])
                    if isinstance(_tomb, dict):
                        marked_at_ts = int(_tomb.get("marked_at") or 0)
                except Exception:
                    marked_at_ts = 0
                try:
                    pi_created_ts = int(obj.get("created") or 0)
                except Exception:
                    pi_created_ts = 0
                if marked_at_ts and pi_created_ts and pi_created_ts >= marked_at_ts:
                    tombstone_active = False
                    _log(f"webhook: tombstone predates PI (marked_at={marked_at_ts} <= created={pi_created_ts}) - allowing auto-reconcile rid={rid} month={month} pi={pi_id}")
        if tombstone_active:
            _log(f"webhook: tombstone found, skipping auto-reconcile rid={rid} month={month} pi={pi_id}")
        else:
            existing_uncertain = _redis_safe("GET", uncertain_key)
            existing_requires_action = _redis_safe("GET", requires_action_key)
            should_auto_reconcile = False
            source_state = None
            if existing_uncertain and isinstance(existing_uncertain, dict) and existing_uncertain.get("result"):
                should_auto_reconcile = True
                source_state = "uncertain"
            # 🚨 Round 4 fix (C-BUG-1): requires_action → succeeded の遷移を捕捉
            # SCA 認証完了後の async PI.succeeded で正常に charge:history を書く
            elif existing_requires_action and isinstance(existing_requires_action, dict) and existing_requires_action.get("result"):
                should_auto_reconcile = True
                source_state = "requires_action"

            if should_auto_reconcile:
                # done_key の既存状態を check
                existing_done_raw = _redis_safe("GET", done_key)
                existing_done = None
                if existing_done_raw and isinstance(existing_done_raw, dict):
                    ed_s = existing_done_raw.get("result")
                    if ed_s:
                        try:
                            _ed = json.loads(ed_s)
                            if isinstance(_ed, dict):
                                existing_done = _ed
                        except Exception: pass
                # 既存 done が succeeded/manually_reconciled なら、上書きせず source state だけ削除
                # 🚨 Round 5 fix (H3): manually_reconciled も skip 条件に追加 (mark_paid との race 防御)
                if existing_done and (
                    existing_done.get("status") in ("succeeded", "processing") or
                    existing_done.get("manually_reconciled") is True
                ):
                    _clear_charge_source_state(source_state, rid, month)
                    _log(f"webhook: {source_state} cleared (done already finalized) rid={rid} month={month} pi={pi_id}")
                else:
                    now_ts = int(time.time())
                    done_payload = json.dumps({
                        "payment_intent_id": pi_id, "status": "succeeded",
                        "amount": amount, "charged_at": now_ts,
                        "auto_reconciled_from": source_state,
                    }, ensure_ascii=False)
                    # 🚨 2026-07-02 fix: execute は uncertain/requires_action 時に done_key を
                    # 中間 status のまま保持する (二重請求防止ロック) ため、常時 SET NX だと
                    # 通常フローで必ず失敗し「race 扱い → history 未記録のまま return」になっていた
                    # (= 3DS 完了/uncertain 自動確定の回収済みが台帳・売上集計から漏れる)。
                    # 既存 done が中間 status (uncertain/requires_action) なら succeeded へ確定上書き。
                    # done_key 不在時のみ SET NX (手動 mark_paid との同時書込 race 防御は従来通り)。
                    if existing_done is not None:
                        set_result = _redis_safe("SET", done_key, done_payload, "EX", "5184000")
                        if not (set_result and isinstance(set_result, dict) and set_result.get("result") == "OK"):
                            # plain SET は race では失敗しない (失敗 = KV エラーのみ)。真実の記録は
                            # history 側なので続行するが、done が中間 status のまま残る事実はログに残す
                            _log(f"webhook: WARN done overwrite kv-error rid={rid} month={month} - proceeding with history write")
                        wrote_done = True
                    else:
                        nx_result = _redis_safe("SET", done_key, done_payload, "NX", "EX", "5184000")
                        wrote_done = bool(nx_result and isinstance(nx_result, dict) and nx_result.get("result") == "OK")
                    if not wrote_done:
                        # 手動 mark_paid が先に書いた → source state だけ削除して終了 (history は mark_paid 側が書く)
                        _clear_charge_source_state(source_state, rid, month)
                        _log(f"webhook: race detected (manual mark_paid won) {source_state} cleared rid={rid} month={month}")
                        return
                    # 🚨 Round 4 fix + 2026-07-02 fix: requires_action だけでなく uncertain 起点の
                    # 自動確定も charge:history に記録する (書かないと台帳 (admin-charge-ledger) の
                    # マスが空欄・月合計/履歴の売上集計から漏れる。charge:done は TTL 60日で消えるため
                    # history が唯一の恒久記録)
                    student_name = meta.get("student_name", "")
                    email = meta.get("email", "")
                    _history_rec = {
                        "payment_intent_id": pi_id,
                        "registration_id": rid,
                        "month": month,
                        "amount": amount,
                        "student_name": student_name,
                        "email": email,
                        "charged_at": now_ts,
                        "status": "succeeded",
                        "auto_reconciled_from": source_state,
                        "source": "sca-async-completion" if source_state == "requires_action" else "uncertain-async-completion",
                    }
                    _redis_safe("ZADD", "charge:history:index", str(now_ts), f"{rid}:{month}")
                    _redis_safe("SET", f"charge:history:{rid}:{month}", json.dumps(_history_rec, ensure_ascii=False), "EX", "31536000")
                    _redis_safe("RPUSH", f"charge:history:audit:{rid}:{month}", json.dumps(_history_rec, ensure_ascii=False))
                    _redis_safe("EXPIRE", f"charge:history:audit:{rid}:{month}", "31536000")
                    _clear_charge_source_state(source_state, rid, month)
                    # 月が succeeded で決着したので tombstone も解除 (execute/retry の成功分岐・
                    # mark_paid と同じ「決着時に消す」規約。残しても done=succeeded ガードで
                    # 実害は無いが、30日間 旧 PI 由来 event のログ文言が紛らわしくなるだけ)
                    _redis_safe("DEL", tombstone_key)
                    _log(f"webhook: auto-reconciled {source_state} → succeeded rid={rid} month={month} pi={pi_id} amount={amount}")
    _log(f"webhook: payment_intent.succeeded rid={rid} month={month} pi={pi_id} amount={amount}")


def _handle_payment_intent_failed(event):
    """🆕 v2 (2026-05-13): 月末バッチ請求の PaymentIntent 失敗 event を記録。
    execute.py が同期 HTTPError で既に charge:failed を書いているが、SCA 後の銀行 async 拒否で
    後から失敗になる case を捕捉するための補完。
    """
    obj = event.get("data", {}).get("object", {})
    meta = obj.get("metadata", {}) or {}
    # 🚨 Round 5 fix (C2): 既存 3 handler と統一して startswith 判定 (空文字 = 既存挙動維持)
    # 将来 juku-payment-yearly 等の派生 system を追加した時にも自動的に処理対象になる
    _pi_sys = (meta.get("system") or "").strip()
    if _pi_sys and not _pi_sys.startswith("juku-payment"):
        _log(f"webhook: PaymentIntent skipped (system={_pi_sys} - not juku-payment)")
        return
    pi_id = obj.get("id", "")
    rid = meta.get("registration_id", "")
    month = meta.get("month", "")
    last_error = obj.get("last_payment_error", {}) or {}
    error_code = last_error.get("code", "")
    decline_code = last_error.get("decline_code", "")
    error_msg = last_error.get("message", "")[:300]
    record = {
        "payment_intent_id": pi_id,
        "registration_id": rid,
        "month": month,
        "amount": obj.get("amount", 0),
        "metadata": meta,
        "error_code": error_code,
        "decline_code": decline_code,
        "error_message": error_msg,
        "failed_at": int(time.time()),
        "source_event": "payment_intent.payment_failed",
    }
    _redis_safe("SET", f"pi:failed:{pi_id}", json.dumps(record, ensure_ascii=False), "EX", "31536000")
    _redis_safe("ZADD", "pi:failed:index", str(record["failed_at"]), pi_id)
    # 🆕 2026-07-02: 単発スポット課金の 3DS 拒否/失敗も record に反映する
    # (succeeded 側と対で、requires_action の「🎓⚠️要確認」が永久に残らないようにする。
    #  _update_spot_history 内で succeeded/processing からの降格は拒否 = out-of-order event 安全)
    if _pi_sys == "juku-payment-spot":
        _update_spot_history(meta, pi_id, "failed", "payment_intent.payment_failed")
    _log(f"webhook: payment_intent.payment_failed rid={rid} month={month} pi={pi_id} code={error_code} decline={decline_code}")


def _kv_get_state(key):
    """KV GET → (exists, parsed_dict|None)。値はあるが JSON dict でない
    (execute の SET NX 初期値 "pending" 等) は (True, None) を返す。"""
    got = _redis_safe("GET", key)
    if not (got and isinstance(got, dict) and got.get("result")):
        return False, None
    try:
        parsed = json.loads(got["result"])
    except Exception:
        return True, None
    return True, parsed if isinstance(parsed, dict) else None


def _handle_payment_intent_canceled(event):
    """🆕 2026-07-02: payment_intent.canceled — 主に塾長が Stripe Dashboard で
    要確認 (uncertain / requires_action) の PI を手動キャンセルした時の掃除。
    従来はハンドラが無く、キャンセルしても charge:uncertain / charge:requires_action /
    spot:history の record が TTL 1年残り、台帳・詳細履歴に ⚠️/🔐 が出続けていた。

    月次: failed 相当の掃除 = 中間 record (uncertain/RA) + 中間 done ロックを解除し、
          charge:failed を書く (台帳 ❌ = execute 同期失敗と同じ「ロック解除済・再請求可能」規約。
          failed_at は再請求時の Idempotency salt 供給源のため掃除より先に書く)。
    spot: _update_spot_history で failed 確定 (succeeded からの降格は同関数が拒否。
          processing→failed は正規の前進遷移として通す = 同関数 L364 の規約どおり)。

    ★安全ガード (succeeded 済みを canceled で降格させない):
      - done or charge:history が succeeded/processing/manually_reconciled → 月の状態は不変
        (同一 PI の残骸 RA record の掃除のみ行う)
      - RA record / 中間 done の payment_intent_id が event と別 PI → 一切触らない
        (retry 等で別 PI が生きている月を旧 PI のキャンセルで誤って unlock しない)
      - PI id を持たない uncertain の record/done ロックは canceled_at vs noted_at の
        前後比較で守る (遅延再送された旧 PI の canceled が新試行のロックを外さない)
      - done が中間 status の JSON dict でない ("pending" = execute 実行中の NX ロック) → done 温存
    ※ Stripe Dashboard の webhook endpoint に payment_intent.canceled の購読追加が必要。
      ★順序厳守: 本コードのデプロイ反映を確認してから購読追加すること。先に購読すると
      旧コードが event id を webhook:seen に焼き付け (TTL 24h)、デプロイ後に Dashboard から
      Resend しても duplicate 扱いで飲まれる (24h 待つか mark_unpaid での手動復旧になる)。"""
    obj = event.get("data", {}).get("object", {})
    meta = obj.get("metadata", {}) or {}
    _pi_sys = (meta.get("system") or "").strip()
    if _pi_sys and not _pi_sys.startswith("juku-payment"):
        _log(f"webhook: PaymentIntent skipped (system={_pi_sys} - not juku-payment)")
        return
    pi_id = obj.get("id", "")
    rid = meta.get("registration_id", "")
    month = meta.get("month", "")
    reason = obj.get("cancellation_reason") or ""
    record = {
        "payment_intent_id": pi_id,
        "registration_id": rid,
        "month": month,
        "amount": obj.get("amount", 0),
        "metadata": meta,
        "cancellation_reason": reason,
        "canceled_at": int(time.time()),
        "source_event": "payment_intent.canceled",
    }
    _redis_safe("SET", f"pi:canceled:{pi_id}", json.dumps(record, ensure_ascii=False), "EX", "31536000")
    _redis_safe("ZADD", "pi:canceled:index", str(record["canceled_at"]), pi_id)
    if _pi_sys == "juku-payment-spot":
        _update_spot_history(meta, pi_id, "failed", "payment_intent.canceled")
        _log(f"webhook: payment_intent.canceled (spot) rid={rid} pi={pi_id} reason={reason}")
        return
    if not rid or not month:
        _log(f"webhook: payment_intent.canceled without rid/month pi={pi_id} - audit only")
        return

    ra_key = f"charge:requires_action:{rid}:{month}"
    unc_key = f"charge:uncertain:{rid}:{month}"
    done_key = f"charge:done:{rid}:{month}"
    ra_exists, ra_rec = _kv_get_state(ra_key)
    unc_exists, unc_rec = _kv_get_state(unc_key)
    done_exists, done_rec = _kv_get_state(done_key)
    _hist_exists, hist_rec = _kv_get_state(f"charge:history:{rid}:{month}")

    # --- ガード1: 月が succeeded で確定済みなら絶対に降格させない ---
    done_final = bool(done_rec and (
        done_rec.get("status") in ("succeeded", "processing") or
        done_rec.get("manually_reconciled") is True))
    hist_final = bool(hist_rec and hist_rec.get("status") in ("succeeded", "processing"))
    if done_final or hist_final:
        # 決着済みの月に残った「同一 PI の」RA 残骸だけは掃除 (旧 mark_paid が RA を
        # 掃除しなかった時代のデータの自己修復。PI 一致 = その record は確実に死んでいる)
        if ra_rec and (ra_rec.get("payment_intent_id") or "") == pi_id:
            _redis_safe("DEL", ra_key)
            _redis_safe("ZREM", "charge:requires_action:index", f"{rid}:{month}")
            _log(f"webhook: canceled PI swept stale RA record (month settled) rid={rid} month={month} pi={pi_id}")
        else:
            _log(f"webhook: payment_intent.canceled ignored (month settled) rid={rid} month={month} pi={pi_id}")
        return

    # --- ガード2: 別 PI がこの月を保持している場合は触らない ---
    ra_pi = (ra_rec.get("payment_intent_id") or "") if ra_rec else ""
    if ra_pi and ra_pi != pi_id:
        _log(f"webhook: canceled PI mismatch (RA holds {ra_pi}) rid={rid} month={month} pi={pi_id} - skip")
        return
    done_intermediate = bool(done_rec and done_rec.get("status") in ("uncertain", "requires_action"))
    done_pi = (done_rec.get("payment_intent_id") or "") if done_rec else ""
    if done_intermediate and done_pi and done_pi != pi_id:
        _log(f"webhook: canceled PI mismatch (done lock holds {done_pi}) rid={rid} month={month} pi={pi_id} - skip")
        return

    # --- ガード3: 遅延/再送 event の stale 判定 (2026-07-02 3並列review P1) ---
    # uncertain の record / done ロックは PI id を持たない (timeout 起因で PI 不明) ため
    # ガード2 で守れない。Stripe は配送失敗時 最大3日 retry / 手動 Resend も可能で、
    # webhook:seen の dedup は 24h しか効かない。PI の canceled_at より「後に」生まれた
    # uncertain 中間 state は別 (より新しい) 試行のもの → 旧 PI の canceled で解除しない
    # (解除すると新試行が実は成功していた場合に ❌ 表示 → 再請求 = 二重請求の入口になる)。
    try:
        canceled_at_ts = int(obj.get("canceled_at") or 0)
    except Exception:
        canceled_at_ts = 0

    def _newer_than_cancel(rec):
        if not canceled_at_ts or not rec:
            return False
        try:
            return int(rec.get("noted_at") or 0) > canceled_at_ts
        except Exception:
            return False

    will_clean = []
    if ra_exists:
        # RA はガード2 で PI 照合済み (同一 PI or 照合不能 record のみここに来る)
        will_clean.append("requires_action")
    if unc_exists:
        if _newer_than_cancel(unc_rec):
            _log(f"webhook: canceled PI stale (uncertain noted_at > canceled_at) rid={rid} month={month} pi={pi_id} - keep uncertain")
        else:
            will_clean.append("uncertain")
    release_done = False
    if done_exists:
        if not done_intermediate:
            # "pending" (execute 実行中の NX ロック) / 想定外形式 → in-flight 二重請求防御を壊さない
            _log(f"webhook: canceled PI keeps non-intermediate done rid={rid} month={month} pi={pi_id}")
        elif not done_pi and _newer_than_cancel(done_rec):
            # PI 無し (uncertain) の done ロックがキャンセルより新しい = 別試行のロック → 温存
            _log(f"webhook: canceled PI stale (done noted_at > canceled_at) rid={rid} month={month} pi={pi_id} - keep done lock")
        else:
            release_done = True
            will_clean.append("done-lock")
    if not will_clean:
        _log(f"webhook: payment_intent.canceled no state to clean rid={rid} month={month} pi={pi_id}")
        return

    # 台帳・詳細履歴に「この月は未回収 (キャンセル)」を残す = execute 同期失敗と同じ charge:failed 規約。
    # ★掃除 (DEL) より先に書く: この record の failed_at は再請求時の Idempotency salt
    # (execute の failed_salts) の供給源なので、途中クラッシュで「掃除済みなのに ❌ が無い
    # (= salt 無しの決定的キーで Stripe replay を踏む)」窓を作らない (2026-07-02 review P2)。
    src_rec = ra_rec or unc_rec or {}
    try:
        amount = int(src_rec.get("amount") or 0) or int(obj.get("amount") or 0)
    except Exception:
        amount = 0
    failed_rec = {
        "registration_id": rid,
        "month": month,
        "amount": amount,
        "student_name": src_rec.get("student_name") or meta.get("student_name", ""),
        "email": src_rec.get("email") or meta.get("email", ""),
        "phone": src_rec.get("phone", ""),
        "payment_intent_id": pi_id,
        "error_code": "payment_intent_canceled",
        "decline_code": reason,
        "error_detail": f"PaymentIntent がキャンセルされました (reason={reason or 'unknown'}・Stripe Dashboard 等での手動キャンセル)",
        "failed_at": int(time.time()),
        "source_event": "payment_intent.canceled",
    }
    _redis_safe("SET", f"charge:failed:{rid}:{month}", json.dumps(failed_rec, ensure_ascii=False), "EX", "31536000")
    _redis_safe("ZADD", "charge:failed:index", str(failed_rec["failed_at"]), f"{rid}:{month}")

    # 掃除 (❌ マーカー確定後)
    if "requires_action" in will_clean:
        _redis_safe("DEL", ra_key)
        _redis_safe("ZREM", "charge:requires_action:index", f"{rid}:{month}")
    if "uncertain" in will_clean:
        _redis_safe("DEL", unc_key)
        _redis_safe("ZREM", "charge:uncertain:index", f"{rid}:{month}")
    if release_done:
        # 中間ロック解除 → 台帳 ❌ + 個別請求で再請求可能に (execute の同期失敗と同じ扱い)
        _redis_safe("DEL", done_key)
    _log(f"webhook: payment_intent.canceled cleaned {'+'.join(will_clean)} rid={rid} month={month} pi={pi_id} reason={reason}")


HANDLERS = {
    "checkout.session.completed": _handle_checkout_completed,
    "invoice.payment_failed": _handle_payment_failed,
    "invoice.payment_succeeded": _handle_payment_succeeded,
    "customer.subscription.deleted": _handle_subscription_deleted,
    "payment_intent.succeeded": _handle_payment_intent_succeeded,
    "payment_intent.payment_failed": _handle_payment_intent_failed,
    "payment_intent.canceled": _handle_payment_intent_canceled,
}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length > 0 else b""
            sig_header = self.headers.get("Stripe-Signature", "")
            secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()

            # 署名検証 (env 未設定なら 503)
            if not secret:
                _log("webhook: STRIPE_WEBHOOK_SECRET not set")
                _json(self, 503, {"error": "WEBHOOK_SECRET_NOT_SET"})
                return

            if not _verify_signature(raw, sig_header, secret):
                _log("webhook: signature verification failed")
                _json(self, 401, {"error": "INVALID_SIGNATURE"})
                return

            try:
                event = json.loads(raw.decode("utf-8"))
            except Exception:
                _json(self, 400, {"error": "INVALID_JSON"})
                return

            event_type = event.get("type", "")
            event_id = event.get("id", "")

            # idempotency: SET NX EX で原子的に重複検知 (race condition 対策)
            # Stripe が並行リトライしても最初の1件だけが処理される
            seen_key = f"webhook:seen:{event_id}"
            seen = _redis_safe("SET", seen_key, "1", "NX", "EX", "86400")
            # Upstash REST: SET NX で既存キーがある場合 result=null、新規なら "OK"
            if seen and isinstance(seen, dict) and seen.get("result") != "OK":
                _log(f"webhook: duplicate event {event_id} ({event_type}) ignored")
                _json(self, 200, {"received": True, "duplicate": True})
                return

            handler_fn = HANDLERS.get(event_type)
            if handler_fn:
                try:
                    handler_fn(event)
                except Exception as e:
                    _log(f"webhook handler error ({event_type}): {e!r}")
                    # Stripe には 200 を返す (本体は KV best-effort なので失敗してもリトライ要らない)
            else:
                _log(f"webhook: ignored event type {event_type}")

            _json(self, 200, {"received": True, "type": event_type})
        except Exception as e:
            _log(f"webhook internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR"})
