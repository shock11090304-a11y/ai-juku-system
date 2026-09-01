#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🏫 「クラス／コース指定の一斉送信」と「承認時の受講クラス反映」を実リクエストで検査する。

    python3 scripts/class_timetable/check_broadcast_class_filter.py

sqlite の使い捨てDBに server/main.py を載せ、TestClient で実際に HTTP を撃つ。
★純粋関数のテストでは足りない: 判定式が正しくても、宛先の組み立てや承認の UPDATE を
  配線し忘れていれば緑になる。誤配信と「受講クラスが無言で消える」はどちらも
  画面上は正常に見えるので、ここで実際の宛先と DB の中身を読み返して確かめる。

★このゲートが在る理由 (2026-09-01 のレビューで見つかった穴):
  ① 一斉送信の「国公立難関大学コース 受講生のみ」は students.course を見ていたが、あの列は
     承認時に通塾生**全員**へ付く在籍フラグ。本番実測で paid/trial 89名中 88名が該当していた
     (＝コース生への連絡のつもりで中学生にも配信される)。
  ② その置き換えとして入れた class フィルタは、コース定義が空になると
     `all(w in have for w in [])` が常に True になり「通塾生全員」に化ける。
  ③ 申込フォームが受講クラスを送るようにしたら、承認の合流パスが class_labels を
     **配列ごと置換**するため、塾長が名簿で積み上げた他クラスが無言で消える。
"""
import importlib.util
import json
import logging
import os
import sys
import tempfile

# ★ログを黙らせるのは server/main.py を読み込む**前**。あのファイルは import しただけで
#   INFO を出す (seed_sapuri_lectures 等) ので、後から止めても取りこぼす。
#   ログが混ざると run_all_gates.py の 1 行サマリがゲートの合否ではなくログ行になり、
#   一覧から結果が読めない (「通ったのか分からない」= 検査していないのと同じ)。
logging.disable(logging.INFO)

TMPDB = tempfile.mktemp(suffix=".db")
os.environ["DB_PATH"] = TMPDB
# ★★ 本番DB保護 (絶対に消さないこと)。USE_POSTGRES は DATABASE_URL の有無だけで決まり DB_PATH は無視される。
#   このゲートは students / messages を INSERT/UPDATE するので、DATABASE_URL が export された端末で
#   回すと本番 Postgres を書き換えうる。先例: scripts/light_tier/check_light_tier_middleware.py
os.environ["DATABASE_URL"] = ""
os.environ.setdefault("STRIPE_PRICE_PREMIUM", "price_test_dummy")
os.environ.setdefault("MAGIC_LINK_SECRET", "test-secret")
os.environ.setdefault("APP_SECRET", "test-secret")
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ["RESEND_API_KEY"] = ""          # メールを外に出さない

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, "..", "..", "server", "main.py")
spec = importlib.util.spec_from_file_location("main", MAIN)
main = importlib.util.module_from_spec(spec)
sys.modules["main"] = main
spec.loader.exec_module(main)

if getattr(main, "USE_POSTGRES", False):
    raise SystemExit("ABORT: USE_POSTGRES=True。本番DBを掴んでいる可能性があるため中止します。")

from fastapi.testclient import TestClient   # noqa: E402

FAIL = []


def ok(cond, label, extra=""):
    print(("  ✅ " if cond else "  ❌ ") + label + (("  " + str(extra)) if (extra and not cond) else ""))
    if not cond:
        FAIL.append(label)


COURSE = "国公立難関大コース"
CLS = main._COURSE_CLASSES[COURSE]          # [水曜3限…, 金曜3限…, 日曜 高校国語]
OTHER = "月曜2限 英文法 Lv.1"


def student(sid, labels, status="trial", email=None):
    conn = main.db(); c = conn.cursor()
    c.execute("DELETE FROM students WHERE id = ?", (sid,))
    c.execute("INSERT INTO students (id, name, email, status, course, class_labels, trial_end) "
              "VALUES (?,?,?,?,?,?,?)",
              (sid, f"生徒{sid}", email or f"s{sid}@example.invalid", status, "kokuritsu_nankan",
               json.dumps(labels, ensure_ascii=False), "2099-01-01 00:00:00"))
    conn.commit(); conn.close()


def labels_of(sid):
    conn = main.db(); c = conn.cursor()
    c.execute("SELECT class_labels FROM students WHERE id = ?", (sid,))
    r = c.fetchone(); conn.close()
    return main._parse_labels(r["class_labels"] if r else None)


def wipe_messages():
    conn = main.db(); c = conn.cursor()
    c.execute("DELETE FROM messages")
    conn.commit(); conn.close()


def recipients(group_id):
    conn = main.db(); c = conn.cursor()
    c.execute("SELECT recipient_id, broadcast_class_label FROM messages WHERE broadcast_group_id = ? ORDER BY recipient_id",
              (group_id,))
    rows = c.fetchall(); conn.close()
    return [r["recipient_id"] for r in rows], (rows[0]["broadcast_class_label"] if rows else None)


def main_():
    main.init_db()
    client = TestClient(main.app)
    H = {"Authorization": "Bearer " + main._sign_admin_token()["token"]}
    # rate limit (broadcast は 5分3回) に引っかからないよう毎回リセットする
    def send(body):
        main._RATE_LIMIT_STORE.clear()
        return client.post("/api/admin/messages/send", json=body, headers=H)

    # A=コース生 / B=コース生 / C=1コマだけ / D=別クラス / E=コース生だが退会 / F=クラス未設定
    student(9201, CLS); student(9202, CLS); student(9203, [CLS[0]])
    student(9204, [OTHER]); student(9205, CLS, status="expired"); student(9206, [])

    print("[A] クラス／コース指定の宛先")
    wipe_messages()
    r = send({"target": "broadcast", "broadcast_filter": "class", "class_label": COURSE,
              "subject": "件名1", "body": "本文1", "send_email": False})
    got = sorted(recipients(r.json().get("broadcast_group_id", ""))[0]) if r.status_code == 200 else r.status_code
    ok(r.status_code == 200 and got == [9201, 9202],
       f"コース指定 → 全コマを持つ2名だけ (1コマだけの生徒・別クラス・未設定は入らない)", got)

    wipe_messages()
    r = send({"target": "broadcast", "broadcast_filter": "class", "class_label": CLS[0],
              "subject": "件名2", "body": "本文2", "send_email": False})
    got = sorted(recipients(r.json().get("broadcast_group_id", ""))[0]) if r.status_code == 200 else r.status_code
    ok(r.status_code == 200 and got == [9201, 9202, 9203], "単品クラス指定 → そのクラスの3名", got)

    print("[B] 在籍中でない生徒 (paid/trial 以外) は宛先に入らない")
    ok(9205 not in got, "退会/期限切れの生徒は宛先から除外", got)

    print("[C] 不正な指定は 400 で止める")
    r = send({"target": "broadcast", "broadcast_filter": "class", "class_label": "存在しないクラス",
              "subject": "x", "body": "y", "send_email": False})
    ok(r.status_code == 400, "時間割にない class_label → 400", r.status_code)
    r = send({"target": "broadcast", "broadcast_filter": "class", "class_label": "",
              "subject": "x", "body": "y", "send_email": False})
    ok(r.status_code == 400, "class_label 未指定 → 400", r.status_code)
    # ★コース定義が空 (起動時の自己修復で label が全部落ちた状態) → 全員配信に化けないこと
    _saved = main._COURSE_CLASSES[COURSE]
    main._COURSE_CLASSES[COURSE] = []
    try:
        r = send({"target": "broadcast", "broadcast_filter": "class", "class_label": COURSE,
                  "subject": "x", "body": "y", "send_email": False})
        ok(r.status_code == 400, "コース定義が空 → 400 (paid/trial 全員に化けない)", r.status_code)
    finally:
        main._COURSE_CLASSES[COURSE] = _saved

    print("[D] 60秒の連打ガードは宛先クラスごとに効く")
    wipe_messages()
    r1 = send({"target": "broadcast", "broadcast_filter": "class", "class_label": CLS[0],
               "subject": "同じ件名", "body": "同じ本文", "send_email": False})
    r2 = send({"target": "broadcast", "broadcast_filter": "class", "class_label": OTHER,
               "subject": "同じ件名", "body": "同じ本文", "send_email": False})
    r3 = send({"target": "broadcast", "broadcast_filter": "class", "class_label": CLS[0],
               "subject": "同じ件名", "body": "同じ本文", "send_email": False})
    ok(r1.status_code == 200 and r2.status_code == 200,
       "同じ文面でも別クラス宛なら通る (2通目が 409 で落ちない)", (r1.status_code, r2.status_code))
    ok(r3.status_code == 409, "同じ文面を同じクラスへ連投すると 409", r3.status_code)

    print("[E] 履歴に宛先クラスが残る")
    wipe_messages()
    r = send({"target": "broadcast", "broadcast_filter": "class", "class_label": CLS[1],
              "subject": "件名3", "body": "本文3", "send_email": False})
    _ids, lab = recipients(r.json().get("broadcast_group_id", ""))
    ok(lab == CLS[1], "messages.broadcast_class_label に宛先クラスが入る", lab)
    h = client.get("/api/admin/messages", headers=H)
    bl = [b for b in (h.json().get("broadcasts") or []) if b.get("broadcast_filter") == "class"]
    ok(bool(bl) and bl[0].get("broadcast_class_label") == CLS[1],
       "履歴 API が宛先クラスを返す", bl[:1])

    print("[F] 承認: 受講クラスは『既存 ∪ 申込』(丸ごと置換しない)")
    conn = main.db(); c = conn.cursor()
    c.execute("DELETE FROM course_applications")
    c.execute("INSERT INTO course_applications (id, name, email, status, referrer, subjects) "
              "VALUES (?,?,?,?,?,?)", (9301, "生徒9204", "s9204@example.invalid", "pending", "入塾申込フォーム", COURSE))
    conn.commit(); conn.close()
    before = labels_of(9204)
    r = client.post("/api/admin/course-applications/9301/approve", json={"ai_disabled": True}, headers=H)
    after = labels_of(9204)
    ok(r.status_code == 200, "承認が成功する", (r.status_code, r.text[:120]))
    ok(OTHER in after, "★既存の受講クラスが消えていない (置換ではなく和集合)", (before, after))
    ok(all(x in after for x in CLS), "申込のコースが3コマに展開されて追加された", after)
    j = r.json() if r.status_code == 200 else {}
    ok(j.get("class_labels_empty") is False and sorted(j.get("class_labels") or []) == sorted(after),
       "承認レスポンスが最終的な受講クラスを返す", j.get("class_labels"))

    print("[G] 承認: 受講クラスが空なら CEO に知らせる")
    conn = main.db(); c = conn.cursor()
    c.execute("INSERT INTO course_applications (id, name, email, status, referrer, subjects) "
              "VALUES (?,?,?,?,?,?)", (9302, "新規生徒", "new9302@example.invalid", "pending", "入塾申込フォーム", None))
    conn.commit(); conn.close()
    r = client.post("/api/admin/course-applications/9302/approve", json={"ai_disabled": True}, headers=H)
    ok(r.status_code == 200 and r.json().get("class_labels_empty") is True,
       "subjects が無い申込 → class_labels_empty=true (承認は止めない)", r.text[:120])
    conn = main.db(); c = conn.cursor()
    c.execute("INSERT INTO course_applications (id, name, email, status, referrer, subjects) "
              "VALUES (?,?,?,?,?,?)", (9303, "旧ラベル生徒", "old9303@example.invalid", "pending", "塾生アプリ",
                                       "木曜3限 国公立コース 長文読解・" + OTHER))
    conn.commit(); conn.close()
    r = client.post("/api/admin/course-applications/9303/approve", json={"ai_disabled": True}, headers=H)
    j = r.json() if r.status_code == 200 else {}
    ok(j.get("dropped_subjects") == ["木曜3限 国公立コース 長文読解"],
       "時間割に無い label は捨てたことを CEO に返す (無言で落とさない)", j.get("dropped_subjects"))

    print("[H] 既存DB (列が無い状態) から init_db で列が足されること")
    # ★本番の messages テーブルには broadcast_class_label が無い。ALTER が走らないと
    #   デプロイ直後の INSERT が「列が無い」で落ち、**一斉送信も個別メッセージも全部死ぬ**。
    #   新規作成 (CREATE TABLE) では通ってしまうので、旧スキーマから作り直して移行経路を試す。
    conn = main.db(); c = conn.cursor()
    c.execute("DROP TABLE messages")
    c.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, sender_type TEXT NOT NULL, "
              "sender_id INTEGER, recipient_type TEXT NOT NULL, recipient_id INTEGER, broadcast_filter TEXT, "
              "subject TEXT, body TEXT NOT NULL, sent_via TEXT DEFAULT 'in_app', email_status TEXT, "
              "sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, read_at TIMESTAMP, broadcast_group_id TEXT, "
              "attachment_filename TEXT, attachment_mime TEXT, attachment_size INTEGER, "
              "attachment_data_b64 TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    c.execute("PRAGMA table_info(messages)")
    ok("broadcast_class_label" not in [r[1] for r in c.fetchall()], "旧スキーマを再現した (列が無い)")
    conn.close()
    main.init_db()
    conn = main.db(); c = conn.cursor()
    c.execute("PRAGMA table_info(messages)")
    ok("broadcast_class_label" in [r[1] for r in c.fetchall()],
       "init_db の migration が broadcast_class_label を足す")
    conn.close()
    r = send({"target": "broadcast", "broadcast_filter": "class", "class_label": CLS[0],
              "subject": "移行後", "body": "移行後の本文", "send_email": False})
    ok(r.status_code == 200, "移行後も一斉送信が通る (列が無いまま INSERT して全滅しない)", r.text[:160])

    if FAIL:
        print(f"\n❌ VIOLATION {len(FAIL)}件")
        for f in FAIL:
            print(f"  - {f}")
        return 1
    print("\n✅ ALL PASS — クラス指定の一斉送信と承認の受講クラス反映は期待どおり")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main_())
    finally:
        try:
            os.remove(TMPDB)
        except OSError:
            pass
