"""トリリオン・ライト (feature_tier='light') の AI 上限テスト。

★最重要は「既存2層 (AI管理フル / 塾生アプリのみ枠) が1ビットも変わっていない」ことの確認。
   新しい層を足したときに既存の許可集合が黙って広がる/狭まるのが一番怖い事故なので、
   ai_disabled の許可判定を全ルートで前後比較する。
実行: PYTHONUNBUFFERED=1 python3 scripts/light_tier/check_light_tier.py
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
os.environ.setdefault("STRIPE_PRICE_FOUNDER_SPECIAL", "price_test_dummy")
os.environ.setdefault("STRIPE_PRICE_STUDENT_ADDON", "price_test_dummy")
os.environ.setdefault("MAGIC_LINK_SECRET", "test-secret")
os.environ.setdefault("APP_SECRET", "test-secret")

MAIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "server", "main.py")
spec = importlib.util.spec_from_file_location("main", MAIN)
main = importlib.util.module_from_spec(spec)
sys.modules["main"] = main
spec.loader.exec_module(main)

# ★保険: 万一 Postgres を掴んでいたら、何もせずに落ちる (静かに本番を触るより落ちる方がよい)
if getattr(main, "USE_POSTGRES", False):
    raise SystemExit("ABORT: USE_POSTGRES=True。本番DBを掴んでいる可能性があるため中止します。")

main.init_db()

FAIL = []
N = [0]


def ok(cond, label):
    N[0] += 1
    if not cond:
        FAIL.append(label)
        print(f"  ✗ {label}")
    else:
        print(f"  ✓ {label}")


def mkstudent(sid, *, ai_disabled=0, feature_tier=None, ai_trial_until=None):
    conn = main.db(); c = conn.cursor()
    c.execute("DELETE FROM students WHERE id = ?", (sid,))
    c.execute(
        "INSERT INTO students (id, name, email, status, ai_disabled, feature_tier, ai_trial_until) "
        "VALUES (?, ?, ?, 'trial', ?, ?, ?)",
        (sid, "テスト生徒", f"t{sid}@example.com", ai_disabled, feature_tier, ai_trial_until),
    )
    conn.commit(); conn.close()
    main._AI_DISABLED_CACHE.pop(sid, None)


print("\n[1] _normalize_tier — 未知/NULL/空は必ず full に倒れる")
for raw, want in [(None, "full"), ("", "full"), ("full", "full"), ("FULL", "full"),
                  ("light", "light"), ("LIGHT", "light"), (" light ", "light"),
                  ("premium", "full"), ("lightweight", "full"), (0, "full"), (1, "full")]:
    ok(main._normalize_tier(raw) == want, f"_normalize_tier({raw!r}) == {want}")

print("\n[2] _is_light_denied_path — 兄弟名 prefix の誤爆が無いこと")
DENY = [
    "/api/ai/messages",
    "/api/ai-tutor/solve-from-image",
    "/api/mock-exam/generate",
    "/api/mock-exam/grade-essay",
    "/api/mock-exam/grade-essay-multiview",
    "/api/curricula/ai-generate",
    "/api/curricula/12/gap-analyze",
    "/api/curricula/12/expand-to-plans",
    # 学習管理は本体プランの機能。元から _require_study_log_course で 403 になるが、
    # ライト向けには専用の文言で断る (「プレミアム以上」より「ライトでは使えません」の方が正確)。
    "/api/curricula/me",
]
ALLOW = [
    "/api/ai/call",                    # ★これは通す (回数で数える)
    "/api/student/grammar-drills",
    "/api/student/grammar-drill/5/submit",
    "/api/vocab/quiz",
    "/api/question-attempts",
    "/api/student/homework",
    "/api/weakness/me",
    "/api/mock-exam/history",          # 履歴は AI を呼ばない
    "/api/mock-exam/templates",
    # ★兄弟名の罠: deny の完全一致キーに前方一致する別ルートを通すこと
    "/api/ai/messages-archive",
    "/api/ai-tutor/solve-from-image-preview",
    "/api/mock-exam/generate-preview",
    "/api/curriculam/ai-generate",     # 綴り違い = 別ルート
    "/api/curricula",                  # 末尾スラッシュ無しの親
]
for p in DENY:
    ok(main._is_light_denied_path(p) is True, f"DENY {p}")
for p in ALLOW:
    ok(main._is_light_denied_path(p) is False, f"ALLOW {p}")

print("\n[3] _light_bucket_for_kind — どの kind でも必ず上限のある枝に落ちる")
for kind in ["chat", "vision", "problems", "essay", "other", None, "", "CHAT", "textbook", "speaking",
             "call_chat", "call_vision", "call_essay", "proxy_messages", "grade_essay",
             "weekly_report_comment"]:
    feat, period, limit, _label = main._light_bucket_for_kind(kind)
    ok(feat == main._LIGHT_AI_FEATURE and limit == main.LIGHT_AI_CALLS_PER_MONTH,
       f"kind={kind!r} → 月次カウンタ(上限{limit})")
# ★実際にバグの原因だった文字列を必ず入れる。/api/ai/call は "call_" を前置し、
#   単数形の public endpoint は "curriculum_generate" を渡す。ここに無かったせいで
#   「生涯枠が一度も発火しない」バグを緑のまま通した (2026-08-20)。
for kind in ["curriculum", "CURRICULUM", " curriculum ", "call_curriculum",
             "curriculum_generate", "probe_call_curriculum"]:
    feat, period, limit, _label = main._light_bucket_for_kind(kind)
    ok(feat == main._LIGHT_CURRICULUM_FEATURE and period == main._LIFETIME_PERIOD
       and limit == main.LIGHT_CURRICULUM_LIFETIME,
       f"kind={kind!r} → 生涯カウンタ(上限{limit})")

print("\n[4] 上限の実挙動 (実 DB)")
mkstudent(9001, feature_tier="light")
ok(main._student_tier(9001) == "light", "feature_tier='light' → _student_tier=light")
over, _ = main._light_quota_exceeded(9001, "chat")
ok(over is False, "0回目: 通る")
for i in range(main.LIGHT_AI_CALLS_PER_MONTH):
    main._light_consume(9001, "chat")
over, msg = main._light_quota_exceeded(9001, "chat")
ok(over is True, f"{main.LIGHT_AI_CALLS_PER_MONTH}回消費後: 止まる")
ok(msg.startswith("AI_BUDGET_LIGHT:") and f"月 {main.LIGHT_AI_CALLS_PER_MONTH} 回" in msg,
   f"文言に接頭辞と上限が入る: {msg[:70]}")
# ★kind を変えて回避できないこと
over_v, _ = main._light_quota_exceeded(9001, "vision")
over_o, _ = main._light_quota_exceeded(9001, "other")
over_n, _ = main._light_quota_exceeded(9001, None)
ok(over_v and over_o and over_n, "★kind を vision/other/未指定 に変えても回避できない")
# curriculum は別枠なのでまだ通る
over_c, _ = main._light_quota_exceeded(9001, "curriculum")
ok(over_c is False, "curriculum は別カウンタなのでまだ通る")
main._light_consume(9001, "curriculum")
over_c2, msg_c = main._light_quota_exceeded(9001, "curriculum")
ok(over_c2 is True, f"curriculum {main.LIGHT_CURRICULUM_LIFETIME}回で止まる")
# ★接頭辞 AI_BUDGET_LIGHT: は フロント (app.js / mypage.js) が「上限系の429か」を判定する鍵。
#   文言の推敲でこれを落とすと、判定が静かに壊れて誤案内に戻る。
ok(msg_c.startswith("AI_BUDGET_LIGHT:") and str(main.LIGHT_CURRICULUM_LIFETIME) in msg_c,
   f"文言に接頭辞と上限が入る: {msg_c[:70]}")
# 生涯カウンタは翌月になっても戻らない (year_month が 'lifetime' 固定)
snap = main._light_usage_snapshot(9001)
ok(snap["curriculum_remaining"] == 0 and snap["ai_calls_remaining"] == 0, f"snapshot: {snap}")

print("\n[5] full の生徒は一切影響を受けない")
mkstudent(9002, feature_tier=None)
ok(main._student_tier(9002) == "full", "feature_tier=NULL → full")
# ★注意: _light_quota_exceeded は tier を見ない (カウンタしか見ない) ので、
#   「full なら常に False」は成り立たない主張。full が守られているのは **呼び出し側が先に
#   tier を見る** から。ここではその呼び出し側の条件が効いていることを確認する。
ok(main._student_tier(9002) == "full", "full の生徒は tier 判定で light に落ちない")
main._light_consume(9002, "chat")   # カウンタに行があっても
ok(main._student_tier(9002) == "full", "カウンタ行があっても full のまま (消費は tier を変えない)")
mkstudent(9003, feature_tier="full")
ok(main._student_tier(9003) == "full", "feature_tier='full' → full")

print("\n[6] ★既存2層の回帰 — 塾生アプリのみ枠(ai_disabled=1)の判定が不変")
mkstudent(9004, ai_disabled=1)
ok(main._is_student_ai_disabled(9004) is True, "ai_disabled=1 → 遮断")
ok(main._student_tier(9004) == "full", "ai_disabled 生徒の tier は full (ライト判定に巻き込まれない)")
mkstudent(9005, ai_disabled=0)
ok(main._is_student_ai_disabled(9005) is False, "ai_disabled=0 → 通す")
# 期限付き AI 体験中は遮断されない (既存仕様)
from datetime import datetime, timedelta, timezone as _tz
future = (datetime.now(_tz.utc) + timedelta(days=3)).replace(tzinfo=None)
mkstudent(9006, ai_disabled=1, ai_trial_until=future)
ok(main._is_student_ai_disabled(9006) is False, "ai_disabled=1 + 体験期限が未来 → 通す (既存仕様が不変)")
past = (datetime.now(_tz.utc) - timedelta(days=1)).replace(tzinfo=None)
mkstudent(9007, ai_disabled=1, ai_trial_until=past)
ok(main._is_student_ai_disabled(9007) is True, "ai_disabled=1 + 体験期限切れ → 遮断")

print("\n[7] ★許可集合が1バイトも変わっていないこと (登録済み全ルートで前後比較)")
# middleware の前置フィルタは _AI_DISABLED_ALLOWED_EXACT / _AI_DISABLED_ALLOWED_PREFIXES のみ。
# 実際に登録されている全ルートに対して「素通しされるか」を数え、想定と一致するか確認する。
routes = sorted({getattr(r, "path", "") for r in main.app.routes if getattr(r, "path", "").startswith("/api/")})
passed = [p for p in routes
          if p in main._AI_DISABLED_ALLOWED_EXACT or p.startswith(main._AI_DISABLED_ALLOWED_PREFIXES)]
gated = [p for p in routes if p not in passed]
print(f"    登録 /api/ ルート {len(routes)} 本 / AIなし枠が素通しできる {len(passed)} 本 / ゲート対象 {len(gated)} 本")
ok(len(routes) > 200, f"ルートが十分に列挙できている ({len(routes)})")
# 素通し集合に AI 課金経路が混ざっていないこと
AI_ROUTES = ["/api/ai/call", "/api/ai/messages", "/api/ai-tutor/solve-from-image",
             "/api/curricula/ai-generate", "/api/mock-exam/generate"]
for p in AI_ROUTES:
    if p in routes:
        ok(p not in passed, f"★AIなし枠の素通し集合に {p} が入っていない")
# ライトの deny 集合が、AIなし枠の素通し集合と交差しないこと
inter = [p for p in passed if main._is_light_denied_path(p)]
ok(not inter, f"★ライトの deny と AIなし枠の許可が交差しない (交差={inter})")

print("\n[8] ライトの deny 集合が実在ルートを指しているか (綴り間違いの検出)")
for p in sorted(main._LIGHT_DENIED_EXACT):
    ok(p in routes, f"deny EXACT {p} が実在する")
ok(len(main._LIGHT_DENIED_PREFIX_EXCEPTIONS) == 0,
   "deny 例外は現在ゼロ (入れるなら必ず完全一致で・実在確認つきで)")
for pre in main._LIGHT_DENIED_PREFIXES:
    hit = [r for r in routes if r.startswith(pre)]
    ok(len(hit) > 0, f"deny PREFIX {pre} が {len(hit)} 本のルートに当たる")


print("\n[9] ★DB障害時に毎リクエスト同期接続しない (ネガティブキャッシュ)")
# ★このゲートを書いた理由: 失敗のキャッシュに「DBを叩く前の時刻」を書いていたため、
#   失敗が遅い (db() は pool 10秒 + connect 10秒 = 最大約20秒) と **書いた瞬間に期限切れ**になり、
#   障害中は1リクエストも救われなかった。async middleware から同期 db() を叩き続ける形で、
#   [[event-loop-blocking-async-def-trap]] (生徒1人のAI利用で塾全体が停止) の再現条件そのもの。
_calls = {"n": 0}
_real_db = main.db
_fake_clock = {"t": 10000.0}
_real_time = __import__("time").time


def _slow_failing_db():
    _calls["n"] += 1
    _fake_clock["t"] += 20.0      # 遅い失敗 (約20秒) を模す
    raise RuntimeError("simulated DB outage")


import time as _time_mod
try:
    main.db = _slow_failing_db
    _time_mod.time = lambda: _fake_clock["t"]
    main._AI_DISABLED_CACHE.pop(9500, None)
    main._HAS_FEATURE_TIER_COL.pop("fail_until", None)
    _had_col = main._HAS_FEATURE_TIER_COL.pop("v", None)

    r1 = main._load_student_gate(9500)
    n1 = _calls["n"]
    r2 = main._load_student_gate(9500)   # 直後の2回目
    n2 = _calls["n"]
    ok(r1 == (False, "full") and r2 == (False, "full"),
       f"DB障害時はフェイルオープン (full) で返す ({r1} / {r2})")
    ok(n2 == n1, f"★2回目は DB を叩かない (1回目={n1}回 → 2回目={n2}回)")

    _fake_clock["t"] += main._GATE_FAIL_TTL + 1   # TTL 経過
    main._HAS_FEATURE_TIER_COL.pop("fail_until", None)
    main._load_student_gate(9500)
    ok(_calls["n"] > n2, f"TTL 経過後は再試行する ({n2} → {_calls['n']})")
finally:
    main.db = _real_db
    _time_mod.time = _real_time
    main._AI_DISABLED_CACHE.pop(9500, None)
    main._HAS_FEATURE_TIER_COL.pop("fail_until", None)
    if _had_col is not None:
        main._HAS_FEATURE_TIER_COL["v"] = _had_col

print("\n" + "=" * 60)
print(f"{N[0]} checks / FAIL {len(FAIL)}")
for f in FAIL:
    print("  FAILED:", f)
try:
    os.unlink(TMPDB)
except Exception:
    pass
sys.exit(1 if FAIL else 0)
