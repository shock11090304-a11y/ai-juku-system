#!/usr/bin/env python3
"""📝 宿題ドリルの結果保存 (POST /api/student/homework/{id}/drill-attempt) の回帰テスト。

背景 (2026-09-24 塾長指示):
  塾生アプリのみ枠 (students.ai_disabled=1) は /api/question-attempts が middleware の許可集合に無く 403 →
  塾長が出した宿題の「📝 ドリルで解く」(dojo-drill.html) が最後に「結果を保存できませんでした」で終わっていた。
  塾長方針は「自由演習は開かない。あくまでも出した宿題のみ」なので、許可集合は変えず、
  宿題 ID を路に持つルートだけを足した。**書き込む側**なので次の性質を機械で固定する。

  1. 塾生アプリのみ枠は /api/question-attempts が従来どおり 403 (自由演習は記録しない)
  2. 同じ生徒でも、自分の宿題 ID の drill-attempt は 200 → question_attempts に 1 行・metadata.homework_id 付き
  3. 他人の宿題 ID / 存在しない ID は 404 で 1 行も入らない (IDOR)
  4. 未ログインは 401
  5. AIあり (ai_disabled=0) の生徒は両方通る = 従来の挙動が変わらない
  6. middleware の許可集合は 1 バイトも変わっていない
     (question-attempts は EXACT に無い・drill-attempt は元からある prefix /api/student/homework/ に乗る)

実行:
    python3 scripts/health_check/test_homework_drill_attempts.py
    # exit 0 = PASS / 1 = FAIL

外部通信は一切しない。DB は一時 SQLite。
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import json
import os
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {detail}" if detail else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="hwdrill_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと **本番 Postgres** に書き込む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "",
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_hwdrill", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def student_token(mod, sid, hours=1):
    """_verify_session_token の新フォーマット (session.sid.exp.sig)。"""
    exp = int(time.time()) + hours * 3600
    payload = f"session.{sid}.{exp}"
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}.{sig}".encode()).decode().rstrip("=")


def make_student(mod, name, email, ai_disabled):
    """通塾生 (course=kokuritsu_nankan・永年 trial)。ai_disabled=1 が「塾生アプリのみ枠」。"""
    conn = mod.db()
    c = conn.cursor()
    far = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)).isoformat()
    c.execute(
        "INSERT INTO students (name, email, status, trial_end, course, grade, goal, ai_disabled) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (name, email, "trial", far, "kokuritsu_nankan", "高校2年", "国公立大学", int(ai_disabled)),
    )
    conn.commit()
    c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
    sid = c.fetchone()["id"]
    conn.close()
    mod._AI_DISABLED_CACHE.pop(sid, None)
    return sid


def make_homework(mod, sid, title):
    conn = mod.db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO homework_assignments (student_id, title, subject, due_date, status, created_by) "
        "VALUES (?, ?, ?, ?, 'open', 'admin')",
        (sid, title, "english", "2030-01-01"),
    )
    conn.commit()
    c.execute("SELECT id FROM homework_assignments WHERE student_id = ? ORDER BY id DESC LIMIT 1", (sid,))
    hid = c.fetchone()["id"]
    conn.close()
    return hid


def attempts(mod, sid):
    conn = mod.db()
    c = conn.cursor()
    c.execute("SELECT source, subject, topic, is_correct, metadata FROM question_attempts WHERE student_id = ? ORDER BY id", (sid,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


ATTEMPT = {
    "source": "practice", "exam_id": "kyotsu", "part_key": "r_grammar", "subject": "english",
    "topic": "英文法 関係詞", "is_correct": 1, "elapsed_ms": 4200,
    "metadata": {"drill": True, "drill_preset": "関係詞", "sub_id": "q1"},
}


def main():
    print("📝 宿題ドリルの結果保存 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)

    print("[0] middleware の許可集合は変えていない")
    check("/api/question-attempts は EXACT 許可に無い (自由演習はAIなし枠で記録しない)",
          "/api/question-attempts" not in mod._AI_DISABLED_ALLOWED_EXACT)
    check("drill-attempt は元からある prefix /api/student/homework/ に乗る",
          "/api/student/homework/1/drill-attempt".startswith(mod._AI_DISABLED_ALLOWED_PREFIXES))
    check("prefix 集合に /api/student/homework/ が 1 本だけ (兄弟名の増殖なし)",
          sum(1 for p in mod._AI_DISABLED_ALLOWED_PREFIXES if p.startswith("/api/student/homework")) == 1)

    sid_a = make_student(mod, "宿題テスト A", "hw-a@example.org", ai_disabled=1)   # 塾生アプリのみ枠
    sid_b = make_student(mod, "宿題テスト B", "hw-b@example.org", ai_disabled=1)
    sid_c = make_student(mod, "宿題テスト C", "hw-c@example.org", ai_disabled=0)   # AIあり
    hw_a = make_homework(mod, sid_a, "英文法 関係詞 20問")
    hw_b = make_homework(mod, sid_b, "英文法 仮定法 20問")
    hw_c = make_homework(mod, sid_c, "英文法 分詞 20問")
    tok_a = {"Authorization": "Bearer " + student_token(mod, sid_a)}
    tok_c = {"Authorization": "Bearer " + student_token(mod, sid_c)}

    print("\n[1] 塾生アプリのみ枠: 自由演習の保存は従来どおり 403")
    r = client.post("/api/question-attempts", json=ATTEMPT, headers=tok_a)
    check("POST /api/question-attempts → 403", r.status_code == 403, f"status={r.status_code}")
    check("403 の文言は middleware のもの (塾生アプリ専用)", "塾生アプリ" in (r.json().get("detail") or ""), r.text[:120])
    check("1 行も入っていない", attempts(mod, sid_a) == [])

    print("\n[2] 塾生アプリのみ枠: 自分の宿題の drill-attempt は 200 で記録される")
    r = client.post(f"/api/student/homework/{hw_a}/drill-attempt", json=ATTEMPT, headers=tok_a)
    check("POST drill-attempt (自分の宿題) → 200", r.status_code == 200, f"status={r.status_code} body={r.text[:160]}")
    check("ok=true・attempt_id あり", r.status_code == 200 and r.json().get("ok") is True and r.json().get("attempt_id"))
    rows = attempts(mod, sid_a)
    check("question_attempts に 1 行", len(rows) == 1, f"rows={len(rows)}")
    meta = json.loads(rows[0]["metadata"]) if rows and rows[0].get("metadata") else {}
    check("metadata.homework_id に宿題 ID", meta.get("homework_id") == hw_a, f"meta={meta}")
    check("元の metadata (drill/preset/sub_id) は残る", meta.get("drill") is True and meta.get("sub_id") == "q1", f"meta={meta}")
    check("source/subject/topic/is_correct が従来どおり保存",
          rows and rows[0]["source"] == "practice" and rows[0]["subject"] == "english"
          and rows[0]["topic"] == "英文法 関係詞" and int(rows[0]["is_correct"] or 0) == 1, f"row={rows[0] if rows else None}")

    print("\n[3] 他人の宿題 / 存在しない宿題は 404 で 1 行も入らない (IDOR)")
    r = client.post(f"/api/student/homework/{hw_b}/drill-attempt", json=ATTEMPT, headers=tok_a)
    check("他人 (B) の宿題 ID → 404", r.status_code == 404, f"status={r.status_code}")
    r = client.post(f"/api/student/homework/{hw_c}/drill-attempt", json=ATTEMPT, headers=tok_a)
    check("他人 (C・AIあり) の宿題 ID → 404", r.status_code == 404, f"status={r.status_code}")
    r = client.post("/api/student/homework/999999/drill-attempt", json=ATTEMPT, headers=tok_a)
    check("存在しない宿題 ID → 404", r.status_code == 404, f"status={r.status_code}")
    check("A の行は増えていない (1 行のまま)", len(attempts(mod, sid_a)) == 1)
    check("B / C に行が入っていない", attempts(mod, sid_b) == [] and attempts(mod, sid_c) == [])

    print("\n[4] 未ログインは 401")
    r = client.post(f"/api/student/homework/{hw_a}/drill-attempt", json=ATTEMPT)
    check("Authorization 無し → 401", r.status_code == 401, f"status={r.status_code}")
    r = client.post(f"/api/student/homework/{hw_a}/drill-attempt", json=ATTEMPT, headers={"Authorization": "Bearer bogus"})
    check("壊れたトークン → 401", r.status_code == 401, f"status={r.status_code}")
    check("A の行は増えていない", len(attempts(mod, sid_a)) == 1)

    print("\n[5] AIあり の生徒は両方のルートが従来どおり通る")
    r = client.post("/api/question-attempts", json=ATTEMPT, headers=tok_c)
    check("AIあり: POST /api/question-attempts → 200", r.status_code == 200, f"status={r.status_code} body={r.text[:120]}")
    r = client.post(f"/api/student/homework/{hw_c}/drill-attempt", json=ATTEMPT, headers=tok_c)
    check("AIあり: drill-attempt (自分の宿題) → 200", r.status_code == 200, f"status={r.status_code} body={r.text[:120]}")
    rows_c = attempts(mod, sid_c)
    check("C に 2 行 (自由演習 1 + 宿題 1)", len(rows_c) == 2, f"rows={len(rows_c)}")
    metas = [json.loads(x["metadata"]) if x.get("metadata") else {} for x in rows_c]
    check("自由演習の行には homework_id が無く、宿題の行にはある",
          "homework_id" not in metas[0] and metas[1].get("homework_id") == hw_c if len(metas) == 2 else False, f"metas={metas}")

    print("\n[5b] 旧ルート /api/question-attempts は client の metadata.homework_id を捨てる (宿題ルートだけが付ける印)")
    spoof = dict(ATTEMPT); spoof["metadata"] = {"drill": True, "homework_id": hw_c}
    r = client.post("/api/question-attempts", json=spoof, headers=tok_c)
    check("AIあり: 自称 homework_id 付き POST → 200", r.status_code == 200, f"status={r.status_code}")
    last_c = json.loads(attempts(mod, sid_c)[-1]["metadata"] or "{}")
    check("保存された metadata に homework_id が無い (drill は残る)", "homework_id" not in last_c and last_c.get("drill") is True, f"meta={last_c}")

    print("\n[6] metadata 無し / 壊れた metadata でも宿題 ID は付く")
    body = dict(ATTEMPT); body.pop("metadata")
    r = client.post(f"/api/student/homework/{hw_a}/drill-attempt", json=body, headers=tok_a)
    check("metadata 無し → 200", r.status_code == 200, f"status={r.status_code}")
    body2 = dict(ATTEMPT); body2["metadata"] = "not-a-dict"
    r = client.post(f"/api/student/homework/{hw_a}/drill-attempt", json=body2, headers=tok_a)
    check("metadata が dict でない → 200 (捨てて homework_id だけ)", r.status_code == 200, f"status={r.status_code}")
    last = attempts(mod, sid_a)[-1]
    check("最後の行の metadata は {homework_id} だけ", json.loads(last["metadata"]) == {"homework_id": hw_a}, f"meta={last['metadata']}")

    print()
    if FAILURES:
        print(f"❌ FAIL: {len(FAILURES)} 件")
        for f in FAILURES:
            print("   -", f)
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
