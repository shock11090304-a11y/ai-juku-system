"""Vercel Function: uncertain (timeout) 状態の手動 reconcile + 個別再請求

Endpoint: POST /payment/api/admin-charge-reconcile

塾長専用。timeout などで charge:uncertain に残った record を、
Stripe Dashboard で実際の状態を確認後、塾長が手動で確定/取消する。

Body (JSON):
  {
    "action": "mark_paid" | "mark_unpaid" | "retry",
    "registrationId": "reg_xxx",
    "month": "2026-05",            // 必須・操作ミス防止
    "paymentIntentId": "pi_xxx"    // mark_paid 時に指定 (Stripe Dashboard で確認した PI)
  }

- mark_paid: Stripe で実際は課金されていた → charge:done を success にマーク + charge:history 作成
- mark_unpaid: Stripe で実際は未課金 → charge:uncertain と done_key を削除 (再実行可能化)
- どちらも charge:uncertain / charge:requires_action の record + index を掃除する
  (webhook _clear_charge_source_state と同じ規約。2026-07-02 fix: 従来は uncertain のみで、
   requires_action の月を手動決着させると RA record が TTL 1年残り台帳に 🔐 が並存し続けた)
- mark_unpaid は RA record が指す 3DS 待ち PI を Stripe 側でも cancel してから消す
  (raw API の requires_action PI は自動失効しない = 放置すると顧客が後から 3DS 完了 → 二重課金。
   cancel 不能 = 実は succeeded/processing なら 400 で拒否して mark_paid へ誘導。
   mark_paid も決着 PI と別の生きた RA PI があれば best-effort で cancel する)
- retry: mark_unpaid 後に新規 Idempotency-Key で即時再請求 (=execute と同じロジックを 1 件だけ)

Response:
  {"ok": true, "action": "mark_paid", "registrationId": "reg_xxx", "month": "2026-05"}

認証: X-Admin-Password (CHAT_ADMIN_PASSWORD)
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import secrets
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


def _stripe_get(secret_key, path):
    try:
        req = urllib.request.Request(
            f"https://api.stripe.com/v1/{path}",
            headers={"Authorization": f"Bearer {secret_key}", "Stripe-Version": "2024-06-20"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        _log(f"stripe GET {path} error: {e}")
        return None


def _stripe_post(secret_key, path, form, idempotency_key=None):
    body = urllib.parse.urlencode(form).encode()
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Stripe-Version": "2024-06-20",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    req = urllib.request.Request(f"https://api.stripe.com/v1/{path}", data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_record(key):
    got = _redis("GET", key)
    if not got or not isinstance(got, dict): return None
    s = got.get("result")
    if not s: return None
    try: return json.loads(s)
    except Exception: return None


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

            action = (payload.get("action") or "").strip()
            rid = (payload.get("registrationId") or "").strip()
            month = (payload.get("month") or "").strip()
            pi_id = (payload.get("paymentIntentId") or "").strip()

            # 🚨 2026-05-13: Vercel Hobby plan 12 function 上限のため migrate_legacy 機能を統合
            # 旧 Subscription mode 顧客を Setup mode に移行 (1-shot 操作)
            if action == "migrate_legacy_batch":
                return _handle_migrate_legacy_batch(self, payload)

            if action not in ("mark_paid", "mark_unpaid", "retry"):
                _json(self, 400, {"error": "INVALID_ACTION", "message": "action は mark_paid / mark_unpaid / retry のいずれか"})
                return
            if not rid or not month:
                _json(self, 400, {"error": "MISSING_PARAMS", "message": "registrationId と month は必須"})
                return

            # registration 存在確認
            reg = _get_record(f"reg:completed:{rid}")
            if not reg:
                _json(self, 404, {"error": "REGISTRATION_NOT_FOUND"})
                return

            uncertain_key = f"charge:uncertain:{rid}:{month}"
            requires_action_key = f"charge:requires_action:{rid}:{month}"
            done_key = f"charge:done:{rid}:{month}"

            if action == "mark_paid":
                # Stripe で実際は課金されていた → charge:done + charge:history を作成
                amount = int(reg.get("monthly_fee", 0) or 0)
                student_name = reg.get("studentName") or reg.get("student_name") or ""
                email = reg.get("email", "")
                phone = reg.get("phone", "")
                now_ts = int(time.time())
                # PI ID を Stripe で verify (任意・指定された場合のみ)
                if pi_id:
                    secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
                    if secret_key:
                        pi = _stripe_get(secret_key, f"payment_intents/{pi_id}")
                        if not pi or pi.get("status") not in ("succeeded", "processing"):
                            _json(self, 400, {
                                "error": "PI_NOT_VERIFIED",
                                "message": f"指定された PaymentIntent ({pi_id}) は succeeded/processing でないため mark_paid できません",
                                "pi_status": pi.get("status") if pi else None,
                            })
                            return
                _redis("SET", done_key, json.dumps({
                    "payment_intent_id": pi_id,
                    "status": "succeeded",
                    "amount": amount,
                    "charged_at": now_ts,
                    "manually_reconciled": True,
                }, ensure_ascii=False), "EX", "5184000")
                _redis("ZADD", "charge:history:index", str(now_ts), f"{rid}:{month}")
                _history_record_mr = {
                    "payment_intent_id": pi_id,
                    "registration_id": rid,
                    "month": month,
                    "amount": amount,
                    "student_name": student_name,
                    "email": email,
                    "phone": phone,
                    "charged_at": now_ts,
                    "status": "succeeded",
                    "manually_reconciled": True,
                    "source": "manual-mark-paid",
                }
                _redis("SET", f"charge:history:{rid}:{month}", json.dumps(_history_record_mr, ensure_ascii=False), "EX", "31536000")
                # 🚨 3rd review fix: append-only audit log
                _redis("RPUSH", f"charge:history:audit:{rid}:{month}", json.dumps(_history_record_mr, ensure_ascii=False))
                _redis("EXPIRE", f"charge:history:audit:{rid}:{month}", "31536000")
                # 🚨 2026-07-02 fix (3並列review 収束): RA record が「決着に使った PI とは別の」
                # 生きた 3DS PI を指している場合、痕跡を消す前に best-effort で cancel する
                # (放置すると顧客が後から旧 3DS リンクを完了 → 二重課金し得る)。
                # mark_paid の主目的 (回収記録) は cancel 失敗でも成立するため abort はしない
                # (succeeded 済み PI への cancel は Stripe 側が拒否するので誤爆も起きない)。
                ra_rec_mp = _get_record(requires_action_key)
                ra_pi_mp = (ra_rec_mp.get("payment_intent_id") or "").strip() if ra_rec_mp else ""
                mp_warning = ""
                if ra_pi_mp and ra_pi_mp != pi_id:
                    _sk_mp = os.environ.get("STRIPE_SECRET_KEY", "").strip()
                    if _sk_mp:
                        try:
                            _stripe_post(_sk_mp, f"payment_intents/{ra_pi_mp}/cancel",
                                         [("cancellation_reason", "duplicate")])
                            _log(f"reconcile: mark_paid canceled stray RA PI {ra_pi_mp} rid={rid} month={month}")
                        except Exception as e:
                            # 🚨 round2 review P2: 失敗をログだけにしない。現況を取得して
                            # 「二重回収の可能性 (succeeded)」と「生きた PI 放置」を warning で塾長に見せる
                            _pi_now_mp = _stripe_get(_sk_mp, f"payment_intents/{ra_pi_mp}")
                            _pi_now_mp_status = (_pi_now_mp or {}).get("status", "")
                            if _pi_now_mp_status in ("succeeded", "processing"):
                                if pi_id:
                                    # 決着 PI を明示指定した上で「別の」PI も回収済み = 真の二重回収疑い
                                    mp_warning = (f"⚠️ この月には別の PaymentIntent ({ra_pi_mp}) も"
                                                  f" {_pi_now_mp_status} で存在します (二重回収の可能性)。"
                                                  " Stripe Dashboard で確認し、必要なら返金してください")
                                    _log(f"reconcile CRITICAL: mark_paid found ANOTHER {_pi_now_mp_status} PI {ra_pi_mp} rid={rid} month={month} - possible double collection")
                                else:
                                    # 🚨 round3 review: PI ID 未入力の mark_paid では、succeeded の RA PI は
                                    # 「いま記録した回収そのもの」である可能性が最も高い。ここで
                                    # 「二重回収→返金」と断定調に出すと正当な月謝の返金を誘発するため中立文言
                                    mp_warning = (f"この月の 3DS 待ちだった PI ({ra_pi_mp}) は Stripe 上"
                                                  f" {_pi_now_mp_status} です。いま『成功』として記録した回収は"
                                                  " この PI 自体の可能性が高いです (PI ID を入力すると照合できます)。"
                                                  " 念のため Dashboard で二重になっていないかご確認ください")
                                    _log(f"reconcile: mark_paid RA PI {ra_pi_mp} is {_pi_now_mp_status} (no pi_id given - likely the actual collection) rid={rid} month={month}")
                            elif _pi_now_mp_status in ("canceled",):
                                _log(f"reconcile: mark_paid stray RA PI {ra_pi_mp} already canceled")
                            else:
                                mp_warning = (f"3DS 待ちの別 PI ({ra_pi_mp}) の cancel に失敗しました"
                                              f" (現況 status={_pi_now_mp_status or '取得不能'})。"
                                              " 放置すると顧客が後から 3DS 完了して二重課金になり得ます。"
                                              " Stripe Dashboard で手動キャンセルしてください")
                                _log(f"reconcile WARN: mark_paid could not cancel stray RA PI {ra_pi_mp}: {e!r} - Stripe Dashboard で要確認")
                    else:
                        mp_warning = (f"STRIPE_SECRET_KEY 未設定のため 3DS 待ちの別 PI ({ra_pi_mp}) を"
                                      " cancel できませんでした。Stripe Dashboard で手動キャンセルしてください")
                        _log(f"reconcile WARN: mark_paid stray RA PI {ra_pi_mp} not canceled (no STRIPE_SECRET_KEY)")
                _redis("DEL", uncertain_key)
                # uncertain index からも削除
                _redis("ZREM", "charge:uncertain:index", f"{rid}:{month}")
                # 🚨 2026-07-02 fix: requires_action (3DS 待ち) の月を Dashboard 確認後に
                # mark_paid で決着させた場合も record + index を掃除 (webhook と同じ規約)。
                # 従来は uncertain のみ掃除で、RA record が TTL 1年残り台帳・詳細履歴に
                # 🔐 が ✅ と並存し続けていた
                _redis("DEL", requires_action_key)
                _redis("ZREM", "charge:requires_action:index", f"{rid}:{month}")
                # 🚨 Round 4 fix (H1): tombstone も削除 (mark_unpaid → mark_paid 順序の整合性)
                _redis("DEL", f"charge:unpaid-tombstone:{rid}:{month}")
                _log(f"reconcile: mark_paid rid={rid} month={month} pi={pi_id}")
                _resp_mp = {"ok": True, "action": "mark_paid", "registrationId": rid, "month": month}
                if mp_warning:
                    _resp_mp["warning"] = mp_warning
                _json(self, 200, _resp_mp)
                return

            if action == "mark_unpaid":
                # Stripe で実際は未課金 → done_key + uncertain を削除 (再実行可能化)
                # 🚨 3rd review fix: tombstone を SET して webhook auto-reconcile による「幽霊復活」を防ぐ
                # mark_unpaid 後に SCA 後の payment_intent.succeeded event が遅延到着しても、
                # webhook 側で tombstone check して auto-reconcile を skip する
                #
                # 🚨 2026-07-02 fix (3並列review P1): RA record が生きた 3DS PI を指す場合、
                # KV の痕跡を消す「前に」Stripe 側でその PI を cancel する。
                # raw API 作成の requires_action PI は放置では自動キャンセルされず、顧客が
                # 後から旧 3DS リンクを完了すると succeeded し得る (retry 済みなら二重課金・
                # source record 消滅済みで auto-reconcile もされず台帳に出ない)。
                # cancel 不能 = 実は回収済み (succeeded/processing) なら mark_unpaid 自体を
                # 拒否して mark_paid へ誘導する (誤った tombstone + 再請求 = 二重課金を防ぐ)。
                ra_rec_mu = _get_record(requires_action_key)
                ra_pi_mu = (ra_rec_mu.get("payment_intent_id") or "").strip() if ra_rec_mu else ""
                # 🚨 2026-07-03 fix (3並列review P2): RA record が欠落していても (execute/retry の
                # RA 分岐が done SET 後・RA record SET 前でクラッシュした窓)、done ロックが
                # requires_action で PI を知っていればそれを cancel 対象に拾う。
                # 拾わないと生きた 3DS PI を Stripe 側に残したまま掃除・再請求可能化してしまい、
                # 顧客が後から旧リンクを完了すると二重課金になり得る (時刻ゲートで succeeded は
                # ミュートされるため台帳にも現れない)。
                if not ra_pi_mu:
                    _done_rec_mu = _get_record(done_key)
                    if _done_rec_mu and _done_rec_mu.get("status") == "requires_action":
                        ra_pi_mu = (_done_rec_mu.get("payment_intent_id") or "").strip()
                cancel_warning = ""
                ra_pi_dead = False  # cancel 成功 / canceled 済み / Stripe 上不存在 = もう課金し得ない
                ra_dead_reason = ""  # 監査用: charge:failed.error_detail に刻む dead 判定理由
                if ra_pi_mu:
                    secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
                    if not secret_key:
                        cancel_warning = (f"STRIPE_SECRET_KEY 未設定のため 3DS 待ち PI ({ra_pi_mu}) を"
                                          " cancel できませんでした。Stripe Dashboard で手動キャンセルしてください")
                        _log(f"reconcile CRITICAL: mark_unpaid without STRIPE_SECRET_KEY - live RA PI {ra_pi_mu} not canceled")
                    else:
                        try:
                            _stripe_post(secret_key, f"payment_intents/{ra_pi_mu}/cancel",
                                         [("cancellation_reason", "abandoned")])
                            ra_pi_dead = True
                            ra_dead_reason = "canceled-by-mark-unpaid"
                            _log(f"reconcile: mark_unpaid canceled RA PI {ra_pi_mu} rid={rid} month={month}")
                        except urllib.error.HTTPError as he:
                            # 404 = この Stripe アカウントに PI が存在しない (test-mode 残骸等)。
                            # Dashboard でもキャンセル不能な PI で 502 恒久ブロックにしない (round2 review)
                            if getattr(he, "code", None) == 404:
                                ra_pi_dead = True
                                ra_dead_reason = "not-found-on-stripe-404"
                                _log(f"reconcile: mark_unpaid RA PI {ra_pi_mu} not found on Stripe (404) - treating as dead")
                            else:
                                # cancel 不能 = 既に終端 or 進行中 → 現況を取得して分岐
                                pi_now = _stripe_get(secret_key, f"payment_intents/{ra_pi_mu}")
                                pi_now_status = (pi_now or {}).get("status", "")
                                if pi_now_status in ("succeeded", "processing"):
                                    _json(self, 400, {
                                        "error": "PI_NOT_CANCELABLE",
                                        "message": (f"この月の 3DS 待ち PI ({ra_pi_mu}) は Stripe 上"
                                                    f" {pi_now_status} (回収済み/処理中) です。"
                                                    " mark_unpaid ではなく mark_paid で決着させてください"),
                                        "pi_status": pi_now_status,
                                    })
                                    return
                                if pi_now_status != "canceled":
                                    _json(self, 502, {
                                        "error": "STRIPE_CANCEL_FAILED",
                                        "message": (f"PI ({ra_pi_mu}) の cancel に失敗しました"
                                                    f" (現況 status={pi_now_status or '取得不能'})。"
                                                    " Stripe Dashboard で手動キャンセル後に再実行してください"),
                                    })
                                    return
                                # canceled 済み → 続行 (Dashboard キャンセル後の mark_unpaid 等・冪等)
                                ra_pi_dead = True
                                ra_dead_reason = "already-canceled"
                        except Exception as e:
                            _json(self, 502, {
                                "error": "STRIPE_CANCEL_FAILED",
                                "message": (f"PI ({ra_pi_mu}) の cancel 中にエラー: {str(e)[:150]}。"
                                            " Stripe Dashboard で手動キャンセル後に再実行してください"),
                            })
                            return
                if ra_pi_dead:
                    # 🚨 2026-07-02 fix (round2 3並列review P1): 死んだ RA PI の月は charge:failed を
                    # 書いて「失敗世代」を進める (failed_at は execute の Idempotency salt 供給源)。
                    # 書かないと mark_unpaid → 当日中の 💳個別請求 (execute) が旧バッチと同一の
                    # 決定的キーになり、Stripe Idempotency (24h) が canceled 済み PI の
                    # requires_action スナップショットを replay して 🔐 ゾンビを再生産する。
                    # ★uncertain 起点 (RA PI 不明) では書かない: そこでは同一キー replay が
                    #   「原試行が実は成功していた場合に新 PI を作らず同一応答を返す」二重課金
                    #   防止の安全装置として機能するため、世代を進めてはいけない。
                    # ★掃除 (DEL) より先に書く (webhook 側と同じ順序規約・クラッシュ窓対策)。
                    _now_mu = int(time.time())
                    _failed_rec_mu = {
                        "registration_id": rid,
                        "month": month,
                        "amount": int((ra_rec_mu or {}).get("amount") or 0) or int(reg.get("monthly_fee", 0) or 0),
                        "student_name": (ra_rec_mu or {}).get("student_name") or reg.get("studentName") or reg.get("student_name") or "",
                        "email": (ra_rec_mu or {}).get("email") or reg.get("email", ""),
                        "phone": (ra_rec_mu or {}).get("phone") or reg.get("phone", ""),
                        "payment_intent_id": ra_pi_mu,
                        "error_code": "manually_marked_unpaid",
                        "decline_code": "",
                        "error_detail": f"mark_unpaid: 3DS 待ち PI ({ra_pi_mu}) を未課金確定 (dead={ra_dead_reason or 'unknown'})",
                        "failed_at": _now_mu,
                        "source_event": "manual-mark-unpaid",
                    }
                    _redis("SET", f"charge:failed:{rid}:{month}", json.dumps(_failed_rec_mu, ensure_ascii=False), "EX", "31536000")
                    _redis("ZADD", "charge:failed:index", str(_now_mu), f"{rid}:{month}")
                _redis("DEL", done_key)
                _redis("DEL", uncertain_key)
                _redis("ZREM", "charge:uncertain:index", f"{rid}:{month}")
                # 🚨 2026-07-02 fix: requires_action record + index も掃除 (mark_paid 側と同様)。
                # 「未課金」と塾長が確定した月に 🔐 3DS待ち表示を残さない。
                # ★KV record を消しても Stripe 側の旧 PI は生きている可能性があるため、
                #   上の cancel 処理で先に殺してから消す (順序に意味がある)
                _redis("DEL", requires_action_key)
                _redis("ZREM", "charge:requires_action:index", f"{rid}:{month}")
                # tombstone (30 日 TTL・retry/再実行が完了するまで)
                _redis("SET", f"charge:unpaid-tombstone:{rid}:{month}", json.dumps({
                    "marked_at": int(time.time()),
                    "reason": "manually marked unpaid by admin",
                }, ensure_ascii=False), "EX", "2592000")  # 30 days
                _log(f"reconcile: mark_unpaid rid={rid} month={month} (tombstone set)")
                _resp_mu = {"ok": True, "action": "mark_unpaid", "registrationId": rid, "month": month}
                if cancel_warning:
                    _resp_mu["warning"] = cancel_warning
                _json(self, 200, _resp_mu)
                return

            if action == "retry":
                # 個別再請求: execute と同じロジックを 1 件だけ実行
                # 🚨 2nd review fix: retry 開始前に SET NX EX で in-flight lock を取得 (二重課金回避)
                # 同時 2 連打を防ぎ、Stripe Idempotency と二重防御
                retry_lock_key = f"charge:retry-inflight:{rid}:{month}"
                lock_acquired = _redis("SET", retry_lock_key, "1", "NX", "EX", "120")  # 120s in-flight
                if not lock_acquired or not isinstance(lock_acquired, dict) or lock_acquired.get("result") != "OK":
                    _json(self, 429, {
                        "error": "RETRY_IN_PROGRESS",
                        "message": "別の retry が進行中です。2 分後に再度お試しください",
                    })
                    return
                # 再請求の前提検証 (done プリロックより前に済ませ、失敗時のロック掃除を不要にする)
                secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
                if not secret_key:
                    _redis("DEL", retry_lock_key)
                    _json(self, 503, {"error": "STRIPE_SECRET_KEY_NOT_SET"})
                    return
                customer_id = reg.get("stripe_customer_id", "")
                payment_method_id = reg.get("stripe_payment_method_id", "")
                monthly_fee = int(reg.get("monthly_fee", 0) or 0)
                if not customer_id or not payment_method_id or monthly_fee <= 0:
                    _redis("DEL", retry_lock_key)
                    _json(self, 400, {"error": "INVALID_REG", "message": "customer/pm/fee が欠落"})
                    return
                # 必ず mark_unpaid 状態 (= done_key が無い) を確認しつつ、確認と同時に
                # SET NX "pending" で二重請求ロックを取る (execute の一斉ループと同じプリロック)。
                # 🚨 2026-07-03 fix (3並列review P1): 従来は GET 確認のみで Stripe 呼出中
                # (最大20秒) を done ロック無しで走り、並走した月末バッチ/個別請求 execute が
                # この月を NX 取得 → 課金 → done=succeeded 確定した後に、戻ってきた retry が
                # plain SET で succeeded を中間 status へ降格上書きし得た (両者が課金する
                # 二重課金 race の入口)。プリロックがあれば並走 execute 側は NX 失敗 =
                # "already charged" skip になり、retry 側が負けた場合はここで 400 を返すため、
                # 窓そのものが閉じる。
                nx_done = _redis("SET", done_key, "pending", "NX", "EX", "5184000")
                if not nx_done or not isinstance(nx_done, dict) or nx_done.get("result") != "OK":
                    _redis("DEL", retry_lock_key)  # lock 解除
                    _json(self, 400, {
                        "error": "ALREADY_LOCKED",
                        "message": "done_key が既に存在します。先に mark_unpaid してから retry してください",
                    })
                    return
                student_name = reg.get("studentName") or reg.get("student_name") or ""
                email = reg.get("email", "")
                # 🚨 Idempotency-Key 衝突回避: secrets.token_hex(4) を含めて連続 retry でも別 key になる
                # Stripe 公式仕様: 同じ key で同じ body 再送 = cached response、同じ key で異 body = 400
                # token_hex で衝突確率実質ゼロ → 連打 retry でも別 PI 作成
                idempotency = f"juku-monthly-retry-{rid}-{month}-{monthly_fee}-{int(time.time())}-{secrets.token_hex(4)}"
                form = [
                    ("amount", str(monthly_fee)),
                    ("currency", "jpy"),
                    ("customer", customer_id),
                    ("payment_method", payment_method_id),
                    ("off_session", "true"),
                    ("confirm", "true"),
                    ("description", f"通塾月謝 — {student_name} ({_month_label_ja(month)}・手動 retry)"[:220]),
                ]
                if email and "@" in email:
                    form.append(("receipt_email", email))
                _meta = {
                    "system": "juku-payment-monthly",
                    "registration_id": rid,
                    "student_name": student_name,
                    "month": month,
                    "monthly_fee": str(monthly_fee),
                    "email": email,
                    "source": "month-end-batch-retry-v1",
                    "retried_at": str(int(time.time())),
                }
                for k, v in _meta.items():
                    if v is None: continue
                    form.append((f"metadata[{k}]", str(v)[:240]))
                try:
                    pi = _stripe_post(secret_key, "payment_intents", form, idempotency_key=idempotency)
                    pi_new_id = pi.get("id", "")
                    pi_status = pi.get("status", "")
                    if pi_status in ("succeeded", "processing"):
                        now_ts = int(time.time())
                        # 🚨 3rd review fix: retry 成功時は tombstone を削除 (再度 webhook auto-reconcile を許可)
                        _redis("DEL", f"charge:unpaid-tombstone:{rid}:{month}")
                        _redis("SET", done_key, json.dumps({
                            "payment_intent_id": pi_new_id,
                            "status": pi_status,
                            "amount": monthly_fee,
                            "charged_at": now_ts,
                            "retry": True,
                            "retry_count_inc": True,
                        }, ensure_ascii=False), "EX", "5184000")
                        # 🚨 2nd review fix: charge:history は retry suffix で別 key に保存 (元 history を消さない・監査履歴保全)
                        # メインの charge:history:{rid}:{month} は最新成功 PI を上書き OK だが、
                        # それとは別に charge:history-retry:{rid}:{month}:{retry_count} で履歴を残す
                        _redis("ZADD", "charge:history:index", str(now_ts), f"{rid}:{month}")
                        _history_record_retry = {
                            "payment_intent_id": pi_new_id,
                            "registration_id": rid,
                            "month": month,
                            "amount": monthly_fee,
                            "student_name": student_name,
                            "email": email,
                            "phone": reg.get("phone", ""),
                            "charged_at": now_ts,
                            "status": pi_status,
                            "retry": True,
                            "source": "manual-retry",
                            "idempotency_key": idempotency,
                        }
                        _redis("SET", f"charge:history:{rid}:{month}", json.dumps(_history_record_retry, ensure_ascii=False), "EX", "31536000")
                        # 🚨 3rd review fix: append-only audit log
                        _redis("RPUSH", f"charge:history:audit:{rid}:{month}", json.dumps(_history_record_retry, ensure_ascii=False))
                        _redis("EXPIRE", f"charge:history:audit:{rid}:{month}", "31536000")
                        # 履歴追跡: retry 回数を ZADD で記録 (元の history と並列で時系列保存)
                        _redis("ZADD", f"charge:history-retries:{rid}:{month}", str(now_ts), pi_new_id)
                        _redis("SET", f"charge:retry:{rid}:{month}:{pi_new_id}", json.dumps({
                            "payment_intent_id": pi_new_id,
                            "registration_id": rid,
                            "month": month,
                            "amount": monthly_fee,
                            "student_name": student_name,
                            "idempotency_key": idempotency,
                            "retried_at": now_ts,
                            "status": pi_status,
                        }, ensure_ascii=False), "EX", "31536000")
                        _redis("DEL", retry_lock_key)  # in-flight lock 解除
                        _json(self, 200, {
                            "ok": True, "action": "retry", "registrationId": rid, "month": month,
                            "paymentIntentId": pi_new_id, "stripeStatus": pi_status,
                        })
                        return
                    if pi_status == "requires_action":
                        # 🚨 2026-07-02 fix (df439e6 3並列review 残穴①): retry の新 PI が 3DS 要求に
                        # なった場合も execute の RA 分岐と同じく done ロック + charge:requires_action
                        # record + index を書く。従来は「unexpected status」で無記録のまま返しており、
                        #  - done 無し = 月末バッチ/個別請求が同月に別 PI を作れる (3DS 完了と重なると二重課金)
                        #  - source record 無し = 顧客が後から 3DS 完了しても webhook auto-reconcile
                        #    が不発 (課金済みなのに pi:succeeded 監査にしか残らず台帳・売上集計から漏れる)
                        # ★tombstone はここでは消さない (execute RA 分岐と同じ規約。uncertain 起点の
                        #   旧 PI succeeded ミュートが本来目的で、この新 PI の 3DS 完了は webhook 側が
                        #   「RA record との PI 完全一致」(fallback: marked_at vs PI created 比較) で通す)
                        now_ts = int(time.time())
                        next_action = pi.get("next_action", {}) or {}
                        redirect = (next_action.get("redirect_to_url") or {}).get("url", "")
                        _redis("SET", done_key, json.dumps({
                            "payment_intent_id": pi_new_id,
                            "status": "requires_action",
                            "amount": monthly_fee,
                            "noted_at": now_ts,
                            "retry": True,
                        }, ensure_ascii=False), "EX", "5184000")
                        _redis("SET", requires_action_key, json.dumps({
                            "payment_intent_id": pi_new_id,
                            "registration_id": rid,
                            "month": month,
                            "amount": monthly_fee,
                            "student_name": student_name,
                            "email": email,
                            "phone": reg.get("phone", ""),
                            "redirect_url": redirect,
                            "noted_at": now_ts,
                            "retry": True,
                            "source": "manual-retry",
                            "idempotency_key": idempotency,
                        }, ensure_ascii=False), "EX", "31536000")
                        _redis("ZADD", "charge:requires_action:index", str(now_ts), f"{rid}:{month}")
                        _redis("DEL", retry_lock_key)  # in-flight lock 解除
                        _log(f"reconcile: retry requires_action rid={rid} month={month} pi={pi_new_id}")
                        _json(self, 200, {
                            "ok": False, "action": "retry", "registrationId": rid, "month": month,
                            "paymentIntentId": pi_new_id, "stripeStatus": pi_status,
                            "redirectUrl": redirect,
                            "warning": ("3DS 認証待ちです (まだ課金されていません)。🔐3DS認証要の一覧に"
                                        "記録しました。顧客に認証 URL を送り、本人認証が完了すると"
                                        "自動で回収記録に反映されます"),
                        })
                        return
                    # その他の status (canceled 等) = 課金不成立 → プリロック解放 (execute の else 分岐と同規約)
                    _redis("DEL", done_key)
                    _redis("DEL", retry_lock_key)
                    _json(self, 200, {
                        "ok": False, "action": "retry", "registrationId": rid, "month": month,
                        "paymentIntentId": pi_new_id, "stripeStatus": pi_status,
                        "message": f"unexpected status: {pi_status}",
                    })
                    return
                except urllib.error.HTTPError as e:
                    # Stripe がエラー応答 = リクエストは届いた = 課金は走っていない → プリロック解放
                    _redis("DEL", done_key)
                    _redis("DEL", retry_lock_key)
                    detail = ""
                    try: detail = e.read().decode("utf-8", errors="replace")[:300]
                    except Exception: pass
                    _json(self, 502, {"error": "STRIPE_API_ERROR", "detail": detail})
                    return
                except Exception as e:
                    # 🚨 2026-07-03 fix (3並列review): timeout 等 = Stripe 側で課金されたか不明。
                    # 従来はロック無しのまま 500 を返すだけで、直後の再試行 (retry は乱数キー) が
                    # 原試行の成功と重なると二重課金し得た。execute の uncertain 規約と同じく
                    # done ロックを温存し ⚠️要確認 (charge:uncertain) に記録して、塾長の
                    # mark_paid / mark_unpaid 決着に誘導する。
                    _now_rt = int(time.time())
                    _redis("SET", done_key, json.dumps({
                        "status": "uncertain",
                        "amount": monthly_fee,
                        "idempotency_key": idempotency,
                        "noted_at": _now_rt,
                        "retry": True,
                        "error": str(e)[:200],
                    }, ensure_ascii=False), "EX", "5184000")
                    _redis("SET", uncertain_key, json.dumps({
                        "registration_id": rid,
                        "month": month,
                        "amount": monthly_fee,
                        "student_name": student_name,
                        "email": email,
                        "phone": reg.get("phone", ""),
                        "idempotency_key": idempotency,
                        "error": str(e)[:300],
                        "noted_at": _now_rt,
                        "retry": True,
                        "source": "manual-retry",
                    }, ensure_ascii=False), "EX", "31536000")
                    _redis("ZADD", "charge:uncertain:index", str(_now_rt), f"{rid}:{month}")
                    _redis("DEL", retry_lock_key)
                    _log(f"reconcile: retry uncertain rid={rid} month={month} err={e!r}")
                    _json(self, 500, {
                        "error": "RETRY_UNCERTAIN",
                        "message": ("Stripe との通信が不確定に終わりました (課金された可能性があります)。"
                                    "⚠️要確認に記録したので、Stripe Dashboard で実際の状態を確認し、"
                                    "成功なら mark_paid・未課金なら mark_unpaid で決着してください: "
                                    + str(e)[:150]),
                    })
                    return
        except Exception as e:
            _log(f"reconcile internal error: {e!r}")
            _json(self, 500, {"error": "INTERNAL_ERROR", "message": str(e)})


# ============================================================================
# 🚨 2026-05-13: 旧 Subscription mode → Setup mode 移行 (Vercel 12 function 上限のため統合)
# 塾長指示「既存 3 名を手間ゼロで月末バッチに自動移行」(2026-05-13)
# 処理: Stripe Customer から PaymentMethod 取得 + Subscription を cancel_at_period_end
#       + KV reg:completed を新形式に更新 (checkout_mode='setup' + monthly_fee + payment_method_id)
# ============================================================================

def _ml_stripe_get(secret_key, path):
    """Stripe GET helper"""
    req = urllib.request.Request(
        f"https://api.stripe.com/v1/{path}",
        headers={"Authorization": f"Bearer {secret_key}", "Stripe-Version": "2024-06-20"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _ml_resolve_payment_method(secret_key, customer_id, subscription):
    """Customer/Subscription から有効な PaymentMethod ID を取得"""
    if subscription:
        pm = subscription.get("default_payment_method")
        if pm: return pm if isinstance(pm, str) else pm.get("id")
    customer = _ml_stripe_get(secret_key, f"customers/{customer_id}")
    inv = customer.get("invoice_settings", {}) or {}
    pm = inv.get("default_payment_method")
    if pm: return pm if isinstance(pm, str) else pm.get("id")
    # fallback: list attached card payment methods
    pm_list = _ml_stripe_get(secret_key, f"payment_methods?customer={customer_id}&type=card&limit=10")
    pms = pm_list.get("data", [])
    if pms: return pms[0].get("id")
    return None


def _handle_migrate_legacy_batch(handler_self, payload):
    """旧 mode=subscription 顧客を Setup mode に一括移行"""
    confirm = (payload.get("confirmText") or "").strip()
    if confirm != "MIGRATE_LEGACY_SUBSCRIPTIONS":
        _json(handler_self, 400, {
            "error": "CONFIRM_TEXT_MISMATCH",
            "message": "confirmText に 'MIGRATE_LEGACY_SUBSCRIPTIONS' を指定してください",
        })
        return
    rids = payload.get("registrationIds") or []
    if not isinstance(rids, list) or not rids:
        _json(handler_self, 400, {"error": "MISSING_RIDS"})
        return
    dry_run = bool(payload.get("dryRun", False))
    secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not secret_key:
        _json(handler_self, 503, {"error": "STRIPE_SECRET_KEY_NOT_SET"})
        return

    migrated = []
    failed = []
    for rid in rids[:50]:
        try:
            reg = _get_record(f"reg:completed:{rid}")
            if not reg:
                failed.append({"registrationId": rid, "error": "registration not found in KV"})
                continue
            student_name = reg.get("studentName") or reg.get("student_name") or ""
            customer_id = reg.get("stripe_customer_id", "")
            subscription_id = reg.get("stripe_subscription_id", "")
            monthly_fee = int(reg.get("monthly_fee", 0) or reg.get("amount", 0) or 0)
            if not customer_id:
                failed.append({"registrationId": rid, "studentName": student_name, "error": "stripe_customer_id 欠落"})
                continue
            if monthly_fee <= 0:
                failed.append({"registrationId": rid, "studentName": student_name, "error": "monthly_fee/amount 欠落 or 0"})
                continue

            subscription_obj = None
            if subscription_id:
                try:
                    subscription_obj = _ml_stripe_get(secret_key, f"subscriptions/{subscription_id}")
                except urllib.error.HTTPError as e:
                    _log(f"migrate {rid}: subscription {subscription_id} fetch failed: {e.code}")

            payment_method_id = _ml_resolve_payment_method(secret_key, customer_id, subscription_obj)
            if not payment_method_id:
                failed.append({"registrationId": rid, "studentName": student_name,
                              "error": "PaymentMethod 取得不能 (Customer に attach されていない)"})
                continue

            sub_canceled = False
            sub_period_end = None
            if subscription_obj and not dry_run:
                sub_status = subscription_obj.get("status", "")
                if sub_status in ("active", "trialing", "past_due"):
                    try:
                        updated_sub = _stripe_post(
                            secret_key,
                            f"subscriptions/{subscription_id}",
                            [("cancel_at_period_end", "true"),
                             ("metadata[migrated_to_setup_mode]", "true"),
                             ("metadata[migration_rid]", rid),
                             ("metadata[system]", "juku-payment-monthly")],
                            idempotency_key=f"migrate-cancel-{rid}-{int(time.time())}",
                        )
                        sub_canceled = bool(updated_sub.get("cancel_at_period_end"))
                        sub_period_end = updated_sub.get("current_period_end")
                    except urllib.error.HTTPError as e:
                        detail_raw = b""
                        try: detail_raw = e.read()
                        except Exception: pass
                        detail = detail_raw.decode("utf-8", errors="replace")[:300]
                        failed.append({"registrationId": rid, "studentName": student_name,
                                      "error": f"subscription cancel 失敗: {detail}"})
                        continue
                elif sub_status == "canceled":
                    sub_canceled = True
                    sub_period_end = subscription_obj.get("current_period_end")

            if not dry_run:
                now_ts = int(time.time())
                updated_rec = {
                    **reg,
                    "checkout_mode": "setup",
                    "stripe_payment_method_id": payment_method_id,
                    "monthly_fee": monthly_fee,
                    "system": "juku-payment-monthly",
                    "migrated_at": now_ts,
                    "migration_source": "legacy-subscription-to-setup-v1",
                    "legacy_subscription_id": subscription_id,
                    "legacy_subscription_canceled_at_period_end": sub_canceled,
                    "legacy_subscription_period_end": sub_period_end,
                }
                _redis("SET", f"reg:completed:{rid}", json.dumps(updated_rec, ensure_ascii=False))

            migrated.append({
                "registrationId": rid,
                "studentName": student_name,
                "customerId": customer_id,
                "paymentMethodId": payment_method_id,
                "monthlyFee": monthly_fee,
                "legacySubscriptionId": subscription_id,
                "subscriptionCanceledAtPeriodEnd": sub_canceled,
                "subscriptionPeriodEnd": sub_period_end,
                "dryRun": dry_run,
            })
        except urllib.error.HTTPError as e:
            detail_raw = b""
            try: detail_raw = e.read()
            except Exception: pass
            detail = detail_raw.decode("utf-8", errors="replace")[:300]
            failed.append({"registrationId": rid, "error": f"Stripe API error: {detail}"})
        except Exception as e:
            failed.append({"registrationId": rid, "error": f"{type(e).__name__}: {str(e)[:200]}"})

    _json(handler_self, 200, {
        "migrated": migrated,
        "failed": failed,
        "summary": {"total": len(rids), "migrated": len(migrated), "failed": len(failed)},
        "dryRun": dry_run,
    })
