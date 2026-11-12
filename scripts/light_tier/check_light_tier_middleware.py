"""middleware 経由の実リクエストで、ライトの遮断が本当に効くかを確認する。

★純粋関数のテストは「判定が正しい」ことしか示さない。middleware に配線し忘れていても緑になる。
   ここでは TestClient で実際に HTTP を撃ち、status code で確かめる。
実行: PYTHONUNBUFFERED=1 python3 scripts/light_tier/check_light_tier_middleware.py
"""
import os, sys, tempfile, importlib.util

TMPDB = tempfile.mktemp(suffix=".db")
os.environ["DB_PATH"] = TMPDB

# ★★ 本番 DB 保護 (絶対に消さないこと)
#   USE_POSTGRES は DATABASE_URL の有無だけで決まり (server/main.py:75-76)、DB_PATH は無視される。
#   このテストは students を DELETE/INSERT するので、DATABASE_URL が export された端末で
#   run_all_gates.py を回すと **本番 Postgres の生徒行を消しうる**。
#   run_all_gates.py:490 は DROP_ENV 以外の env を丸ごと子に渡すため、ここで自衛する。
#   先例: scripts/health_check/test_synthetic_monitor_retry.py:57-61
os.environ["DATABASE_URL"] = ""

os.environ.setdefault("STRIPE_PRICE_PREMIUM", "price_test_dummy")
os.environ.setdefault("MAGIC_LINK_SECRET", "test-secret")
os.environ.setdefault("APP_SECRET", "test-secret")
# ★ai_proxy は先頭で ANTHROPIC_API_KEY 未設定なら 503 を返す (ライト判定より前)。
#   ダミーを入れて先へ進める。上限で 429 になれば実 API には到達しない = 課金は発生しない。
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-dummy-for-local-test"  # ★ハード代入 (本物の鍵を使わせない)
os.environ["GEMINI_API_KEY"] = "dummy-for-local-test"            # ★同上。urlopen はモックするので外に出ない
os.environ["OPENAI_API_KEY"] = ""                                 # OpenAI へは絶対に出さない

MAIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "server", "main.py")
spec = importlib.util.spec_from_file_location("main", MAIN)
main = importlib.util.module_from_spec(spec)
sys.modules["main"] = main
spec.loader.exec_module(main)

# ★保険: 万一 Postgres を掴んでいたら、何もせずに落ちる (静かに本番を触るより落ちる方がよい)
if getattr(main, "USE_POSTGRES", False):
    raise SystemExit("ABORT: USE_POSTGRES=True。本番DBを掴んでいる可能性があるため中止します。")


from fastapi.testclient import TestClient

FAIL = []
N = [0]


def ok(cond, label):
    N[0] += 1
    print(("  ✓ " if cond else "  ✗ ") + label)
    if not cond:
        FAIL.append(label)


def mkstudent(sid, *, ai_disabled=0, feature_tier=None):
    conn = main.db(); c = conn.cursor()
    c.execute("DELETE FROM students WHERE id = ?", (sid,))
    c.execute(
        "INSERT INTO students (id, name, email, status, ai_disabled, feature_tier, trial_end) "
        "VALUES (?, ?, ?, 'trial', ?, ?, ?)",
        (sid, "テスト生徒", f"t{sid}@example.com", ai_disabled, feature_tier, "2099-01-01 00:00:00"),
    )
    conn.commit(); conn.close()
    main._AI_DISABLED_CACHE.pop(sid, None)


# ★TestClient を `with` で入れない = FastAPI の startup イベントを走らせない。
#   startup は _post_deploy_smoke_test をスケジュールし、30秒後に
#   _run_synthetic_checkout_test() が **本番の /api/trial/signup に合成申込を POST** する
#   (events を汚している監視 bot と同じ経路)。CI でこれを走らせると本番にゴミ申込が入る。
#   lifespan を起こさなくても middleware はリクエスト毎に実行されるので、検証には十分。
main.init_db()
client = TestClient(main.app)
if True:
    LIGHT, FULL, APPONLY = 9101, 9102, 9103
    mkstudent(LIGHT, feature_tier="light")
    mkstudent(FULL, feature_tier=None)
    mkstudent(APPONLY, ai_disabled=1)
    H = {k: {"Authorization": "Bearer " + main._sign_session_token(k)} for k in (LIGHT, FULL, APPONLY)}

    print("\n[A] ライトで丸ごと使えないルート → 403 + ライト専用の文言")
    for path, body in [
        ("/api/ai/messages", {"messages": [{"role": "user", "content": "hi"}]}),
        ("/api/ai-tutor/solve-from-image", {"image_base64": "x"}),
        ("/api/mock-exam/grade-essay", {"answer": "x"}),
        ("/api/curricula/ai-generate", {}),
    ]:
        r = client.post(path, json=body, headers=H[LIGHT])
        detail = ""
        try:
            detail = (r.json() or {}).get("detail", "")
        except Exception:
            pass
        ok(r.status_code == 403 and "トリリオン AI学習アプリ" in str(detail),
           f"light  POST {path} → {r.status_code} / {str(detail)[:40]}")

    print("\n[B] ★同じルートを full の生徒が叩いても、ライトの 403 にはならない")
    # ★ここで /api/ai/messages を full で叩かないこと = ゲートを通過して実際に Anthropic へ
    #   外向き HTTP が飛ぶ (CI で毎回 401 を叩きに行くのは無駄で遅い)。
    #   pydantic 検証で手前で止まるルートだけを使って「ライトの403ではない」ことを確かめる。
    for path, body in [
        ("/api/curricula/ai-generate", {}),
        ("/api/mock-exam/grade-essay", {}),
    ]:
        r = client.post(path, json=body, headers=H[FULL])
        detail = ""
        try:
            detail = (r.json() or {}).get("detail", "")
        except Exception:
            pass
        ok(not (r.status_code == 403 and "トリリオン AI学習アプリ" in str(detail)),
           f"full   POST {path} → {r.status_code} (ライトの403ではない)")

    print("\n[C] ★塾生アプリのみ枠の挙動が不変 (従来の 403 文言のまま)")
    r = client.post("/api/ai/call", json={"system": "s", "kind": "chat", "messages": []}, headers=H[APPONLY])
    detail = ""
    try:
        detail = (r.json() or {}).get("detail", "")
    except Exception:
        pass
    ok(r.status_code == 403 and "塾生アプリ" in str(detail),
       f"apponly POST /api/ai/call → {r.status_code} / {str(detail)[:40]}")
    r = client.get("/api/student/grammar-drills", headers=H[APPONLY])
    ok(r.status_code != 403, f"apponly GET /api/student/grammar-drills → {r.status_code} (従来どおり通る)")

    print("\n[D] ライトでも通るルート (上限で数える側)")
    r = client.get("/api/student/grammar-drills", headers=H[LIGHT])
    ok(r.status_code != 403, f"light GET /api/student/grammar-drills → {r.status_code}")
    # /api/curricula/me は元から _require_study_log_course (プレミアム以上) で 403。
    # light も full(trial) も 403 = ライト導入で挙動が変わっていないことを確認する。
    rl = client.get("/api/curricula/me", headers=H[LIGHT])
    rf = client.get("/api/curricula/me", headers=H[FULL])
    ok(rl.status_code == 403 and rf.status_code == 403,
       f"curricula/me は light={rl.status_code} / full={rf.status_code} (どちらも既存ゲートで403)")

    print("\n[E] /api/ai/call の上限が middleware ではなくハンドラで効く (2026-11-12 新仕様)")
    # mkstudent は status='trial' で作る = 体験中。体験中の添削は LIGHT_TRIAL_ESSAYS 回まで。
    for _ in range(main.LIGHT_TRIAL_ESSAYS):
        main._light_consume(LIGHT, "essay")
    r = client.post("/api/ai/call", json={"system": "s", "kind": "essay", "messages": [{"role": "user", "content": "hi"}]},
                    headers={**H[LIGHT], "Origin": "https://trillion-ai-juku.com"})
    detail = ""
    try:
        detail = (r.json() or {}).get("detail", "")
    except Exception:
        pass
    ok(r.status_code == 429 and f"{main.LIGHT_TRIAL_ESSAYS} 回まで" in str(detail) and "体験中" in str(detail)
       and str(detail).startswith("AI_BUDGET_LIGHT:"),
       f"light POST /api/ai/call kind=essay (体験中の上限到達) → {r.status_code} / {str(detail)[:60]}")
    # ★問題・参考書の AI 作成は回数に関係なく必ず断る (塾長決定「生徒は新しく作れない」)
    for _k in ("problems", "textbook", "exam_photo_scan", "exam_pdf_scan"):
        r2 = client.post("/api/ai/call", json={"system": "s", "kind": _k, "messages": [{"role": "user", "content": "hi"}]},
                         headers={**H[LIGHT], "Origin": "https://trillion-ai-juku.com"})
        d2 = ""
        try:
            d2 = (r2.json() or {}).get("detail", "")
        except Exception:
            pass
        ok(r2.status_code == 429 and str(d2).startswith("AI_BUDGET_LIGHT:") and "作ることはできません" in str(d2),
           f"★kind={_k} は必ず断る → {r2.status_code} / {str(d2)[:40]}")
    # ★AI の弱点プリント生成も middleware で 403 (plan ではなく tier で止める)
    r5 = client.post("/api/weak-points/generate-worksheet", json={}, headers=H[LIGHT])
    ok(r5.status_code == 403, f"★light POST /api/weak-points/generate-worksheet → {r5.status_code}")
    # ★参考書の作成依頼ルートは middleware で 403
    r3 = client.post("/api/textbooks/request-generation", json={"subject": "英語", "topic": "x"}, headers=H[LIGHT])
    ok(r3.status_code == 403, f"★light POST /api/textbooks/request-generation → {r3.status_code}")
    r4 = client.post("/api/textbooks/request-generation", json={"subject": "英語", "topic": "x"}, headers=H[FULL])
    ok(r4.status_code != 403, f"full POST /api/textbooks/request-generation はライトの403にならない → {r4.status_code}")

    print("\n[F] /api/usage/me が残回数を返す (full には付けない)")
    r = client.get("/api/usage/me", headers=H[LIGHT])
    j = r.json() if r.status_code == 200 else {}
    ok(r.status_code == 200 and j.get("feature_tier") == "light" and "light_usage" in j,
       f"light /api/usage/me → tier={j.get('feature_tier')} light_usage={j.get('light_usage')}")
    r = client.get("/api/usage/me", headers=H[FULL])
    j2 = r.json() if r.status_code == 200 else {}
    ok(r.status_code == 200 and j2.get("feature_tier") == "full" and "light_usage" not in j2,
       f"full  /api/usage/me → tier={j2.get('feature_tier')} light_usage無し={('light_usage' not in j2)}")


    # ─────────────────────────────────────────────────────────────────────────
    print("\n[G] ★成功した呼び出しが「正しいカウンタ」を実際に増やすか")
    # ★これが今回いちばん重要な検査。helper を直接叩くだけのテストでは、
    #   呼び出し側が別の kind 文字列を渡していること (/api/ai/call は "call_" を前置する) も、
    #   model="gemini-*" が _call_anthropic_safe を通らないことも検出できず、
    #   「上限が一度も効かない」バグを緑のまま通してしまった (2026-08-20 レビュー指摘)。
    #   実 API は叩かず urlopen をモックする (課金ゼロ)。
    import urllib.request as _ureq
    import json as _json

    class _FakeResp:
        def __init__(self, payload):
            self._b = _json.dumps(payload).encode()
        def read(self): return self._b
        def __enter__(self): return self
        def __exit__(self, *a): return False

    _ANTHROPIC_OK = {"content": [{"type": "text", "text": "ok"}],
                     "usage": {"input_tokens": 10, "output_tokens": 5},
                     "model": "claude-sonnet-4-6", "stop_reason": "end_turn"}
    _GEMINI_OK = {"candidates": [{"content": {"parts": [{"text": "ok"}]},
                                  "finishReason": "STOP"}],
                  "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5}}

    def _fake_urlopen(req, *a, **kw):
        url = getattr(req, "full_url", str(req))
        return _FakeResp(_GEMINI_OK if "generativelanguage" in url else _ANTHROPIC_OK)

    _real_urlopen = _ureq.urlopen
    _ureq.urlopen = _fake_urlopen

    # ★_call_gemini は urllib ではなく google.genai SDK を使う (resp.candidates / resp.usage_metadata)。
    #   urlopen を差し替えても素通りし、Gemini が失敗 → Anthropic へフォールバックして 200 になる。
    #   それだと「gemini 直行でも数える」を検査したつもりで、実際はフォールバック経路を測ってしまう
    #   (2026-08-20: 実際にこの状態で緑になっていた)。関数ごと差し替えて本当に分岐を通す。
    #   戻り値は _call_gemini の実物と同じ Anthropic 互換エンベロープ。
    _real_call_gemini = main._call_gemini
    _gemini_calls = {"n": 0}

    def _fake_call_gemini(body, *, model=None, kind="chat"):
        _gemini_calls["n"] += 1
        return {
            "id": "gemini_test", "type": "message", "role": "assistant",
            "content": [{"type": "text", "text": "ok"}],
            "model": model or "gemini-2.5-flash", "_actual_model": model or "gemini-2.5-flash",
            "_provider": "gemini", "stop_reason": "end_turn",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }

    main._call_gemini = _fake_call_gemini
    # 直前の失敗で circuit breaker が立っていると Gemini 分岐に入らず Anthropic 直行になる
    try:
        main._GEMINI_QUOTA_FAIL["skip_until"] = 0.0
        main._GEMINI_QUOTA_FAIL["count_in_window"] = 0
    except Exception:
        pass

    def _counters(sid):
        conn = main.db(); c = conn.cursor()
        c.execute("SELECT feature, year_month, used_count FROM usage_monthly WHERE student_id = ?", (sid,))
        rows = {(r["feature"], r["year_month"]): r["used_count"] for r in c.fetchall()}
        conn.close()
        return rows

    try:
        G = 9110
        mkstudent(G, feature_tier="light")
        HG = {"Authorization": "Bearer " + main._sign_session_token(G),
              "Origin": "https://trillion-ai-juku.com"}
        ym = main._jst_year_month()

        # (1) ★通常のチャットは回数で数えない (AI チューターは回数無制限・2026-11-12 塾長決定)
        r = client.post("/api/ai/call",
                        json={"system": "s", "kind": "chat", "messages": [{"role": "user", "content": "hi"}]},
                        headers=HG)
        cnt = _counters(G)
        ok(r.status_code == 200 and cnt == {},
           f"★chat 成功 → カウンタを作らない (status={r.status_code} counters={cnt})")

        # (2) ★kind='curriculum' → 今月のカウンタが +1
        #     /api/ai/call は backstop に "call_curriculum" を渡すので、完全一致だとここで落ちる
        r = client.post("/api/ai/call",
                        json={"system": "s", "kind": "curriculum", "messages": [{"role": "user", "content": "hi"}]},
                        headers=HG)
        cnt = _counters(G)
        ok(r.status_code == 200 and cnt.get((main._LIGHT_CURRICULUM_FEATURE, ym)) == 1,
           f"★curriculum 成功 → 今月 +1 (status={r.status_code} counters={cnt})")

        # (3) ★2回目の curriculum は月1回の上限で 429
        r = client.post("/api/ai/call",
                        json={"system": "s", "kind": "curriculum", "messages": [{"role": "user", "content": "hi"}]},
                        headers=HG)
        ok(r.status_code == 429, f"★curriculum 2回目 → 429 (月1回が効く) → {r.status_code}")

        # (4) ★model='gemini-*' でも添削を数える (_call_anthropic_safe を通らない経路)。体験中なので体験の枠
        before = _counters(G).get((main._LIGHT_ESSAY_FEATURE, main._LIGHT_TRIAL_PERIOD), 0)
        r = client.post("/api/ai/call",
                        json={"system": "s", "kind": "essay", "model": "gemini-2.5-flash",
                              "messages": [{"role": "user", "content": "hi"}]},
                        headers=HG)
        after = _counters(G).get((main._LIGHT_ESSAY_FEATURE, main._LIGHT_TRIAL_PERIOD), 0)
        ok(r.status_code == 200 and after == before + 1 and _gemini_calls["n"] == 1,
           f"★gemini 直行でも添削 +1 ({before}→{after} status={r.status_code} "
           f"gemini実呼び出し={_gemini_calls['n']}回)")
        # ★「本当に Gemini 分岐を通ったか」を別軸で確かめる。通っていなければ
        #   Anthropic フォールバックを測っているだけで、この検査は無意味になる。
        ok(_gemini_calls["n"] == 1, "★Gemini 分岐を実際に通った (フォールバックではない)")

        # (5) ★なりすまし (塾長の確認入室) は消費しない
        before = _counters(G).get((main._LIGHT_ESSAY_FEATURE, main._LIGHT_TRIAL_PERIOD), 0)
        HI = {"Authorization": "Bearer " + main._sign_session_token(G, token_type="impersonation"),
              "Origin": "https://trillion-ai-juku.com"}
        r = client.post("/api/ai/call",
                        json={"system": "s", "kind": "essay", "messages": [{"role": "user", "content": "hi"}]},
                        headers=HI)
        after = _counters(G).get((main._LIGHT_ESSAY_FEATURE, main._LIGHT_TRIAL_PERIOD), 0)
        # ★status も見る。401/403 で弾かれてもカウンタは据置なので、それだけだと
        #   「なりすましが通ったうえで数えなかった」ことの検査にならない。
        ok(after == before and r.status_code == 200,
           f"★なりすましは通るが残回数を減らさない ({before}→{after} status={r.status_code})")

        # (5b) ★契約後 (status='paid') の添削は「今月」の枠で数える (体験の枠ではない)
        _cp = main.db(); _cpc = _cp.cursor()
        _cpc.execute("UPDATE students SET status='paid' WHERE id=?", (G,)); _cp.commit(); _cp.close()
        r = client.post("/api/ai/call",
                        json={"system": "s", "kind": "essay", "messages": [{"role": "user", "content": "hi"}]},
                        headers=HG)
        cnt = _counters(G)
        ok(r.status_code == 200 and cnt.get((main._LIGHT_ESSAY_FEATURE, ym)) == 1,
           f"★paid の添削 → 今月の枠 +1 (status={r.status_code} counters={cnt})")

        # (5c) ★汎用の月次クォータ (essays) で二重に止めない。体験中の添削が「今月の essays」にも
        #      数えられていると、契約後に専用の枠が残っていても「プレミアムにアップグレード」の 429 で止まる。
        _cp = main.db(); _cpc = _cp.cursor()
        _cpc.execute("UPDATE students SET plan='trillion_light' WHERE id=?", (G,))
        _cpc.execute("DELETE FROM usage_monthly WHERE student_id=? AND feature='essays'", (G,))
        _cpc.execute("INSERT INTO usage_monthly (student_id, feature, year_month, used_count) VALUES (?, 'essays', ?, ?)",
                     (G, ym, 50))
        _cp.commit(); _cp.close()
        r = client.post("/api/ai/call",
                        json={"system": "s", "kind": "essay", "feature": "essays",
                              "messages": [{"role": "user", "content": "hi"}]},
                        headers=HG)
        ok(r.status_code == 200,
           f"★汎用の essays が上限でも、専用の枠が残っていれば通る (二重に数えない) → {r.status_code} {str(r.json())[:60]}")

        # (6) full の生徒は何回撃ってもカウンタ行が1つも増えない
        F2 = 9111
        mkstudent(F2, feature_tier=None)
        HF = {"Authorization": "Bearer " + main._sign_session_token(F2),
              "Origin": "https://trillion-ai-juku.com"}
        for _ in range(3):
            client.post("/api/ai/call",
                        json={"system": "s", "kind": "chat", "messages": [{"role": "user", "content": "hi"}]},
                        headers=HF)
        ok(_counters(F2) == {}, f"full はカウンタを1行も作らない ({_counters(F2)})")
    finally:
        _ureq.urlopen = _real_urlopen
        main._call_gemini = _real_call_gemini

    print("\n[H] ★既存2層の許可集合をベースラインで固定する")
    # ★「今の値を再計算して比べる」では、許可集合を広げた変更を検出できない (自分自身と比較するため)。
    #   期待値をここに焼き付ける。この行を書き換える = 塾生アプリのみ枠の許可範囲を変える、ということ。
    EXPECTED_EXACT = {
        "/api/student/homework",
        "/api/student/grammar-drills",
        "/api/messages/me",
        "/api/student/messages/send",
    }
    EXPECTED_PREFIXES = (
        "/api/student/class/",
        "/api/student/homework/",
        "/api/student/grammar-drill/",
        "/api/messages/me/",
        "/api/auth/",
        "/api/admin/",
    )
    ok(set(main._AI_DISABLED_ALLOWED_EXACT) == EXPECTED_EXACT,
       f"AIなし枠の EXACT 許可が期待どおり ({sorted(set(main._AI_DISABLED_ALLOWED_EXACT) ^ EXPECTED_EXACT)})")
    ok(tuple(main._AI_DISABLED_ALLOWED_PREFIXES) == EXPECTED_PREFIXES,
       f"AIなし枠の PREFIX 許可が期待どおり ({main._AI_DISABLED_ALLOWED_PREFIXES})")

print("\n[I] ★申込の受付スイッチと、既存アカウントの断り (体験・決済で同じ条件)")
_SIGN = {"name": "仮名 一郎", "grade": "高校1年", "plan": "trillion_light"}
def _mkrow(sid, email, **cols):
    conn = main.db(); c = conn.cursor()
    c.execute("DELETE FROM students WHERE id = ? OR LOWER(email) = ?", (sid, email))
    keys = ["id", "name", "email"] + list(cols.keys())
    c.execute(f"INSERT INTO students ({', '.join(keys)}) VALUES ({', '.join(['?'] * len(keys))})",
              (sid, "テスト生徒", email, *cols.values()))
    conn.commit(); conn.close()
    main._AI_DISABLED_CACHE.pop(sid, None)
# (1) スイッチが閉じている間は、直接 POST しても体験も決済も受け付けない
main.LIGHT_SIGNUP_OPEN = False
r = client.post("/api/trial/signup", json={**_SIGN, "email": "closed1@example.com"})
ok(r.status_code == 403, f"★受付前: 体験の直接 POST → 403 ({r.status_code})")
conn = main.db(); c = conn.cursor()
c.execute("SELECT COUNT(*) FROM students WHERE LOWER(email) = ?", ("closed1@example.com",))
ok(c.fetchone()[0] == 0, "★受付前: 生徒行を作らない")
conn.close()
r = client.post("/api/stripe/checkout", json={"plan": "trillion_light", "email": "closed1@example.com", "name": "仮名 一郎"})
ok(r.status_code == 403, f"★受付前: 決済の直接 POST → 403 ({r.status_code})")
# (2) 開けたら 3日間・light で体験が付く
main.LIGHT_SIGNUP_OPEN = True
try:
    r = client.post("/api/trial/signup", json={**_SIGN, "email": "open1@example.com"})
    j = r.json() if r.status_code == 200 else {}
    conn = main.db(); c = conn.cursor()
    c.execute("SELECT plan, feature_tier, status, trial_end FROM students WHERE LOWER(email) = ?", ("open1@example.com",))
    row = c.fetchone(); conn.close()
    ok(r.status_code == 200 and j.get("light_trial_granted") is True and row and row["plan"] == "trillion_light"
       and row["feature_tier"] == "light" and row["status"] == "trial",
       f"受付中: 新規の体験 → light で付く ({r.status_code} {dict(row) if row else None})")
    if row:
        _te = row["trial_end"]
        _te = main.datetime.fromisoformat(str(_te).replace("Z", "+00:00"))
        if _te.tzinfo is None:
            _te = _te.replace(tzinfo=main.timezone.utc)
        _days = (_te - main.datetime.now(main.timezone.utc)).total_seconds() / 86400
        ok(2.9 < _days <= 3.01, f"★体験は3日間 ({_days:.2f}日)")
    # (3) 塾生 (AIなし枠)・通塾生・契約中・カード登録つきの体験中は、体験も決済も断る
    _cases = [
        (9201, "jukusei@example.com", {"ai_disabled": 1, "status": "trial"}, "塾生"),
        (9202, "addon@example.com", {"plan": "student_addon", "status": "paid"}, "塾生"),
        (9203, "founder@example.com", {"plan": "founder_special", "status": "paid", "stripe_subscription_id": "sub_x"}, "月額プラン"),
        (9204, "cardtrial@example.com", {"plan": "founder_special", "status": "trial", "stripe_subscription_id": "sub_y"}, "カード登録"),
        (9205, "course@example.com", {"course": "kokuritsu_nankan", "status": "trial"}, "塾生"),
    ]
    for sid, em, cols, word in _cases:
        _mkrow(sid, em, **cols)
        main._RATE_LIMIT_STORE.clear()   # 同じ IP から続けて撃つので、申込の回数制限を毎回空にする
        r1 = client.post("/api/trial/signup", json={**_SIGN, "email": em})
        r2 = client.post("/api/stripe/checkout", json={"plan": "trillion_light", "email": em, "name": "仮名 一郎"})
        d1 = (r1.json() or {}).get("detail", "") if r1.status_code != 200 else ""
        d2 = (r2.json() or {}).get("detail", "") if r2.status_code != 200 else ""
        conn = main.db(); c = conn.cursor()
        c.execute("SELECT plan, feature_tier FROM students WHERE id = ?", (sid,))
        after = dict(c.fetchone()); conn.close()
        ok(r1.status_code == 400 and word in str(d1) and r2.status_code == 409 and word in str(d2)
           and after.get("feature_tier") != "light" and after.get("plan") == cols.get("plan"),
           f"★{em}: 体験 {r1.status_code} / 決済 {r2.status_code} で断り、plan・tier を変えない ({after})")
    # (4) ★カード登録つきの体験中は、体験メールの除外 (_light_member_ids) に入らない (課金前のお知らせを止めない)
    _mkrow(9206, "lightcard@example.com", plan="trillion_light", feature_tier="light", status="trial",
           stripe_subscription_id="sub_z")
    _mkrow(9207, "lightplain@example.com", plan="trillion_light", feature_tier="light", status="trial")
    _ids = main._light_member_ids()
    ok(9207 in _ids and 9206 not in _ids, f"★体験メールの除外: 通常の体験は除外 / カード登録つきは除外しない")
    # (5) ★カード登録つき体験 (founder_special) へ移ったら light を外す
    conn = main.db(); c = conn.cursor()
    main._sync_feature_tier_after_checkout(c, conn, 9207, None, "founder_special")
    c.execute("SELECT feature_tier FROM students WHERE id = ?", (9207,))
    ok(c.fetchone()["feature_tier"] in (None, ""), "★別プランへの同期で light を外す")
    main._sync_feature_tier_after_checkout(c, conn, 9207, None, "trillion_light")
    c.execute("SELECT feature_tier FROM students WHERE id = ?", (9207,))
    ok(c.fetchone()["feature_tier"] == "light", "trillion_light への同期で light を付ける")
    conn.close()
finally:
    main.LIGHT_SIGNUP_OPEN = False

print("\n" + "=" * 60)
print(f"{N[0]} checks / FAIL {len(FAIL)}")
for f in FAIL:
    print("  FAILED:", f)
try:
    os.unlink(TMPDB)
except Exception:
    pass
sys.exit(1 if FAIL else 0)
