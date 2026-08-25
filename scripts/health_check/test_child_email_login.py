#!/usr/bin/env python3
"""🔑 子供メール (students.student_email) を登録したとき、子が**自分のアドレスで**
ログインできることの回帰テスト。

背景 (2026-08-25 塾長指示「この子のアドレスを追加して、子供もログインできるようにして」):
  CEO 画面の「子供メール ✏️編集」で student_email を設定すると、
  admin_set_student_email が student_email_verified=1 を立て、以後のログインコードは
  親 (email) と子 (student_email) の両方に届く——というのが **画面が家庭に約束している内容**。
  ところが request_magic_link には、子に一通も届かないのに画面は成功文言を出す経路が
  2 つ残っていた (どちらも「子供もログインできる」を無言で破る):

    (a) LINE 連携済みだと _try_line_login_push の成功でメール送信ブロックごと skip。
        LINE は生徒行に 1 本しか持てず、連携は「ログイン中の本人が mypage で発行」する
        1 経路なので、子メール未登録の家庭で張られている LINE は保護者のもの。
        子が自分のアドレスで要求しても保護者の LINE にしか飛ばない。
    (b) 親アドレスが受信者 cap (10通/時) に到達すると、子アドレスのカウンタが 0 でも
        送信ブロックごと中断していた。cap は受信者単位のキーなので巻き添えの理由が無い。

  ここで固定するのは「子の受信箱は親の都合から独立している」こと。同時に、
  逆方向 (子に送ってはいけない条件) を緩めていないことも必ず見る——ここを緩めると
  第三者アドレスへのメール爆撃の踏み台に戻る。

固定する性質:
  1. 子メールで magic-link を要求すると、その生徒が引ける (親メール専用ではない)
  2. LINE 連携済みでも、確認済みの子メールには届く          ← (a) の回帰
  3. 親アドレスが cap 到達でも、確認済みの子メールには届く   ← (b) の回帰
  4. 親も子も送れないときは新しいコードを発行しない (旧コード温存の保護は維持)
  5. 未確認 (verified=0) の子メールには送らない              ← セキュリティ維持
  6. 他生徒の「親メール」と衝突する子メールには送らない       ← セキュリティ維持
  7. verify-code は magic-link と同じ生徒を引く (子メールで入力しても通る)
  8. 応答は宛先の状態で変化しない (アカウント列挙のオラクルにしない)
  9. admin 設定はログイン側と同じ validator で弾く
     (保存できたのにログインで 422 になるアドレスを作らない) + verified=1 を立てる
 10. CEO ダッシュの 24h 集計が、届いた回 (LINE 配信・子のみ配信) を失敗に数えない
     — 失敗3件で赤く警告する画面なので、混ぜると本物の不達が埋もれる

実行:
    python3 scripts/health_check/test_child_email_login.py
    # exit 0 = PASS / 1 = FAIL

外部通信は一切しない (メール送信と LINE 配信を差し替える)。DB は一時 SQLite。
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import os
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []

# テスト用の架空アドレス (example.com = RFC 2606 が文書用に予約したドメイン。実在の受信箱は無い)
# ★.invalid / .test は pydantic EmailStr (email-validator) が「予約 TLD」として弾くので使えない。
PARENT = "parent-a@example.com"
CHILD = "child-a@example.com"
OTHER_PARENT = "parent-b@example.com"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {detail}" if detail else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    """一時 SQLite + ダミー env で server/main.py を in-process ロード。"""
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="childmail_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと **本番 Postgres** に書き込む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "",
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",   # 起動30秒後に本番へ申込 POST を撃つ
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_childmail", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def admin_token(mod, hours=1):
    exp = int((datetime.datetime.now(datetime.timezone.utc)
               + datetime.timedelta(hours=hours)).timestamp())
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), f"admin.{exp}".encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


def make_student(mod, name, email, student_email="", verified=0, line_uid=None):
    conn = mod.db()
    c = conn.cursor()
    far = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)).isoformat()
    c.execute(
        "INSERT INTO students (name, email, student_email, student_email_verified, "
        "status, plan, trial_end, line_user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (name, email, student_email, verified, "paid", "founder_special", far, line_uid),
    )
    conn.commit()
    c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
    sid = c.fetchone()["id"]
    conn.close()
    return sid


def set_line(mod, sid, line_uid):
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE students SET line_user_id = ? WHERE id = ?", (line_uid, sid))
    conn.commit(); conn.close()


def fill_recipient_cap(mod, email):
    """指定アドレスの受信者 cap (10通/時) を到達済みにする。
    _check_recipient_send_cap / _recipient_send_cap_exceeded と**同じキー**を使う
    (どちらかがキーを変えたらこのテストが先に落ちる = 意図した検知)。"""
    key = (f"rcpt:{email.lower().strip()[:200]}", "magic_link_send")
    mod._RATE_LIMIT_STORE[key] = [time.time()] * 10


def reset_rate_limits(mod):
    """IP rate limit (magic_link は 5回/分) と受信者 cap を毎ケース掃除する。
    掃除しないと 6 ケース目以降が 429 になり、テストが本題と無関係に落ちる。"""
    mod._RATE_LIMIT_STORE.clear()


def main():
    print("🔑 子供メール ログイン経路 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)

    # --- メール送信と LINE 配信を差し替える (外部通信ゼロ) ---
    #   ★_send_magic_link_email (最下層) を差し替える。_send_magic_link_with_retry は
    #     そのまま走らせるので、受信者 cap の実挙動もテスト対象に入る。
    sent_to = []

    def fake_send_email(to_email, student_name, magic_url, otp_code="", is_welcome=False,
                        is_child_verify=False, trial_note=""):
        sent_to.append(to_email)
        return {"sent": True, "resend_id": "test"}

    mod._send_magic_link_email = fake_send_email

    line_ok = {"value": False}
    line_pushes = []

    def fake_line_push(row, magic_url, otp_code):
        # 本番と同じ前提: line_user_id が無ければ必ず False
        try:
            uid = row["line_user_id"] if "line_user_id" in row.keys() else None
        except Exception:
            uid = None
        if not uid:
            return False
        if line_ok["value"]:
            line_pushes.append(uid)
            return True
        return False

    mod._try_line_login_push = fake_line_push

    def request_login(email):
        sent_to.clear()
        line_pushes.clear()
        reset_rate_limits(mod)
        return client.post("/api/auth/magic-link", json={"email": email})

    # ============================================================
    # 1. 子メールで生徒が引ける
    # ============================================================
    print("1. 子メールで magic-link を要求すると生徒が引ける")
    sid = make_student(mod, "テスト生徒A", PARENT, student_email=CHILD, verified=1)
    line_ok["value"] = False
    r = request_login(CHILD)
    check("HTTP 200", r.status_code == 200, f"status={r.status_code}")
    check("親と子の両方に届く", set(sent_to) == {PARENT, CHILD}, f"sent_to={sent_to}")

    # ============================================================
    # 2. LINE 連携済みでも確認済みの子メールには届く  ← 回帰 (a)
    # ============================================================
    print("\n2. LINE 連携済みでも、確認済みの子メールには届く (回帰: LINE がメールを飲み込まない)")
    set_line(mod, sid, "U_parent_line_0000000000000000000")
    line_ok["value"] = True
    r = request_login(CHILD)
    check("LINE に push されている", len(line_pushes) == 1, f"line_pushes={line_pushes}")
    check("子アドレスにメールが届く", CHILD in sent_to, f"sent_to={sent_to}")
    check("親アドレスへのメールは従来どおり抑止 (LINE と重複させない)",
          PARENT not in sent_to, f"sent_to={sent_to}")

    # LINE 配信が失敗したときは従来どおり親にもメールする
    line_ok["value"] = False
    r = request_login(CHILD)
    check("LINE 失敗時は親にもフォールバックする", set(sent_to) == {PARENT, CHILD}, f"sent_to={sent_to}")
    set_line(mod, sid, None)

    # ============================================================
    # 3. 親が cap 到達でも子には届く  ← 回帰 (b)
    # ============================================================
    print("\n3. 親アドレスが受信者 cap 到達でも、子メールには届く (回帰: 巻き添えで止めない)")
    line_ok["value"] = False
    sent_to.clear(); line_pushes.clear()
    reset_rate_limits(mod)
    fill_recipient_cap(mod, PARENT)
    r = client.post("/api/auth/magic-link", json={"email": CHILD})
    check("HTTP 200", r.status_code == 200, f"status={r.status_code}")
    check("子アドレスには届く", sent_to == [CHILD], f"sent_to={sent_to}")

    # ============================================================
    # 4. 親も子も送れないときは新しいコードを発行しない (旧コード温存)
    # ============================================================
    print("\n4. 親も子も cap 到達 (LINE 無し) なら新しい OTP を発行しない (旧コード温存の保護を維持)")

    def active_otp_count(student_id):
        conn = mod.db(); c = conn.cursor()
        c.execute("SELECT COUNT(*) AS n FROM otp_codes WHERE student_id = ? AND used_at IS NULL",
                  (student_id,))
        n = c.fetchone()["n"]; conn.close()
        return n

    before = active_otp_count(sid)
    sent_to.clear(); line_pushes.clear()
    reset_rate_limits(mod)
    fill_recipient_cap(mod, PARENT)
    fill_recipient_cap(mod, CHILD)
    r = client.post("/api/auth/magic-link", json={"email": CHILD})
    check("HTTP 200 (列挙対策で常に 200)", r.status_code == 200, f"status={r.status_code}")
    check("一通も送らない", sent_to == [], f"sent_to={sent_to}")
    check("OTP を増やさない", active_otp_count(sid) == before,
          f"before={before} after={active_otp_count(sid)}")

    # ============================================================
    # 5. 未確認の子メールには送らない (セキュリティ維持)
    # ============================================================
    print("\n5. 未確認 (verified=0) の子メールには送らない")
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE students SET student_email_verified = 0 WHERE id = ?", (sid,))
    conn.commit(); conn.close()
    line_ok["value"] = False
    r = request_login(CHILD)
    check("子アドレスには送らない", CHILD not in sent_to, f"sent_to={sent_to}")
    check("親アドレスには従来どおり届く", PARENT in sent_to, f"sent_to={sent_to}")
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE students SET student_email_verified = 1 WHERE id = ?", (sid,))
    conn.commit(); conn.close()

    # ============================================================
    # 6. 他生徒の「親メール」と衝突する子メールには送らない (セキュリティ維持)
    # ============================================================
    print("\n6. 他生徒の親メールと衝突する子メールには送らない (他人の受信箱を爆撃しない)")
    make_student(mod, "テスト生徒B", OTHER_PARENT)
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE students SET student_email = ?, student_email_verified = 1 WHERE id = ?",
              (OTHER_PARENT, sid))
    conn.commit(); conn.close()
    r = request_login(PARENT)
    check("衝突アドレスには送らない", OTHER_PARENT not in sent_to, f"sent_to={sent_to}")
    check("親アドレスには届く", PARENT in sent_to, f"sent_to={sent_to}")
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE students SET student_email = ?, student_email_verified = 1 WHERE id = ?",
              (CHILD, sid))
    conn.commit(); conn.close()

    # ============================================================
    # 7. verify-code が magic-link と同じ生徒を引く
    # ============================================================
    print("\n7. 子メールで受け取ったコードを子メール欄に入力してログインできる")
    line_ok["value"] = False
    request_login(CHILD)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT code FROM otp_codes WHERE student_id = ? AND used_at IS NULL "
              "ORDER BY id DESC LIMIT 1", (sid,))
    row = c.fetchone(); conn.close()
    code = row["code"] if row else ""
    reset_rate_limits(mod)
    r = client.post("/api/auth/verify-code", json={"email": CHILD, "code": code})
    check("子メール + コードでログインできる", r.status_code == 200, f"status={r.status_code} body={r.text[:200]}")
    if r.status_code == 200:
        check("同じ生徒として認証される", (r.json().get("student") or {}).get("id") == sid,
              f"student={r.json().get('student')}")

    # ============================================================
    # 8. 応答が宛先の状態で変化しない (列挙オラクルにしない)
    # ============================================================
    print("\n8. 応答は宛先の状態で変化しない (アカウント列挙のオラクルにしない)")
    line_ok["value"] = False
    body_no_line = request_login(PARENT).json()
    set_line(mod, sid, "U_parent_line_0000000000000000000")
    line_ok["value"] = True
    body_line = request_login(PARENT).json()
    set_line(mod, sid, None)
    line_ok["value"] = False
    body_unknown = request_login("nobody-here@example.com").json()
    check("LINE 連携の有無で応答が変わらない", body_no_line == body_line,
          f"{body_no_line} != {body_line}")
    check("存在しないアドレスでも応答が同じ", body_no_line == body_unknown,
          f"{body_no_line} != {body_unknown}")

    # ============================================================
    # 9. admin 設定はログイン側と同じ validator で弾く + verified=1
    # ============================================================
    print("\n9. admin の子メール設定: ログインで 422 になるアドレスを保存させない")
    hdr = {"Authorization": f"Bearer {admin_token(mod)}"}
    # RFC 非準拠 (@ の直前がピリオド)。旧ドコモ/au の慣行アドレスに実在する形。
    bad = "bad.@example.com"
    r = client.post(f"/api/admin/students/{sid}/student-email",
                    json={"student_email": bad}, headers=hdr)
    check("RFC 非準拠アドレスを 400 で弾く", r.status_code == 400, f"status={r.status_code} body={r.text[:200]}")
    # 弾いたアドレスが保存されていないこと (「弾いたつもりで書けている」を防ぐ)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT student_email FROM students WHERE id = ?", (sid,))
    check("弾いたアドレスは保存されていない",
          (c.fetchone()["student_email"] or "").lower() != bad.lower())
    conn.close()
    # ログイン側 (pydantic EmailStr) が実際に 422 にすることも見る = 上の 400 が過剰でない証拠
    reset_rate_limits(mod)
    r = client.post("/api/auth/magic-link", json={"email": bad})
    check("そのアドレスはログイン側で 422 になる (弾く判断が正しい)", r.status_code == 422,
          f"status={r.status_code}")

    good = "child-c@example.com"
    r = client.post(f"/api/admin/students/{sid}/student-email",
                    json={"student_email": good}, headers=hdr)
    check("通常のアドレスは保存できる", r.status_code == 200, f"status={r.status_code} body={r.text[:200]}")
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT student_email, student_email_verified FROM students WHERE id = ?", (sid,))
    row = c.fetchone(); conn.close()
    check("小文字で保存される", (row["student_email"] or "") == good, f"student_email={row['student_email']}")
    check("確認済み (verified=1) が立つ", bool(row["student_email_verified"]))
    # 設定した直後に、そのアドレスで本当にコードを受け取れる (画面の約束と実挙動の一致)
    line_ok["value"] = False
    request_login(good)
    check("設定直後にそのアドレスへ届く", good in sent_to, f"sent_to={sent_to}")

    # ============================================================
    # 10. 届いた回を「失敗」に数えない (CEO ダッシュの誤報を止める)
    # ============================================================
    print("\n10. CEO ダッシュの 24h 集計: 届いた回を失敗に数えない")
    # events を空にしてから、LINE 配信 1 回 / 子のみ配信 1 回 を作る
    conn = mod.db(); c = conn.cursor()
    c.execute("DELETE FROM events WHERE name = 'magic_link_email_status'")
    conn.commit(); conn.close()
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE students SET student_email = ?, student_email_verified = 1 WHERE id = ?",
              (CHILD, sid))
    conn.commit(); conn.close()
    set_line(mod, sid, "U_parent_line_0000000000000000000")
    line_ok["value"] = True
    request_login(PARENT)                      # → LINE 配信
    set_line(mod, sid, None)
    line_ok["value"] = False
    sent_to.clear(); reset_rate_limits(mod)
    fill_recipient_cap(mod, PARENT)
    client.post("/api/auth/magic-link", json={"email": CHILD})   # → 子のみ配信
    st = mod._magic_link_24h_stats()
    check("LINE 配信は sent_via_line に入る", st.get("sent_via_line") == 1, f"stats={st}")
    check("子のみ配信は child_only に入る", st.get("child_only") == 1, f"stats={st}")
    check("どちらも send_failed に数えない (赤い誤警告を出さない)",
          st.get("send_failed") == 0, f"stats={st}")

    print("\n" + "=" * 60)
    if FAILURES:
        print(f"❌ FAIL — {len(FAILURES)} 件")
        for f in FAILURES:
            print(f"   - {f}")
        return 1
    print("✅ ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
