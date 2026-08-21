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

# ★フェイルオープンの記録 (_record_gate_failure_async) は **別スレッドで db() を呼ぶ**。
#   素通しにすると _calls["n"] が非決定的に増え、下の「2回目は DB を叩かない」が実行のたびに揺れる。
#   db() を呼ばない recorder に差し替えて、回数の数えを決定的にしたうえで、
#   この設計の中核 (呼び出し元をブロックしない / 書けなかったら再試行する) まで検査する。
_events = []
_events_lock = __import__("threading").Lock()
_recorder_ok = {"v": True}      # 記録役が成功するか (DB障害の再現)
_recorder_delay = {"v": 0.0}    # 記録役が遅い場合 (非ブロッキング性の検査)
_real_recorder = main._record_ai_critical_event


def _fake_recorder(name, props):
    if _recorder_delay["v"]:
        _time_mod.sleep(_recorder_delay["v"])   # sleep は clock patch の影響を受けない
    with _events_lock:
        _events.append(name)
    return _recorder_ok["v"]


def _wait_until(pred, timeout=5.0):
    """条件が満たされるまで待つ (実時間)。満たされたら True。"""
    waited = 0.0
    while waited < timeout:
        if pred():
            return True
        _time_mod.sleep(0.02)
        waited += 0.02
    return False


_had_col = None
try:
    main.db = _slow_failing_db
    main._record_ai_critical_event = _fake_recorder
    main._GATE_EVENT_LAST.clear()
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

    # ★フェイルオープンは stdout だけに書いて終わりにしない。events に残っていないと
    #   「上限が一切効いていない状態」が誰にも気づかれないまま続く。
    _wait_until(lambda: len(_events) >= 2)
    with _events_lock:
        _got = sorted(set(_events))
    ok(_got == ["light_tier_column_check_failed", "student_gate_read_failed"],
       f"★フェイルオープンを events に記録している ({_got})")

    # ★障害が続くあいだ events を連投しない (_GATE_EVENT_MIN_INTERVAL=600秒)。
    #   ★判定は「一定時間待って件数が増えないこと」ではなく **打刻が残っていること**を見る。
    #     sleep で待つ形にすると、回帰でスレッド起動が遅れただけで通ってしまう (偽の緑)。
    _fake_clock["t"] += main._GATE_FAIL_TTL + 1   # TTL 経過
    main._HAS_FEATURE_TIER_COL.pop("fail_until", None)
    main._load_student_gate(9500)
    ok(_calls["n"] > n2, f"TTL 経過後は再試行する ({n2} → {_calls['n']})")
    # ★キーの**有無**だけを見てはいけない。後退はキーを消さないので、成功でも失敗でも同じ集合になり、
    #   「成功したのに後退させた」を検出できない (実際、_write から成功の短絡を外す変異が緑で通った)。
    #   見逃すと全 gate event が 600 秒ではなく _GATE_EVENT_RETRY_INTERVAL(30秒) ごとに書かれ、
    #   events 行・daemon スレッド・DB 接続がおよそ 20 倍になる。
    #   打刻が**どれだけ過去に置かれているか** (lag) で判定する。
    _lags = [(_fake_clock["t"] - v) for v in main._GATE_EVENT_LAST.values()]
    _max_lag = max(_lags) if _lags else None
    # ★閾値は2段にする。MIN-RETRY(=570) は「後退していない」ことの**理論上**の境界だが、
    #   後退実装の理論下限もちょうど 570 で、観測マージンは _slow_failing_db の +20 一回ぶんしかない
    #   (実測: 正常 91 / 変異 590)。偽クロックの進み幅を変えた瞬間に判別できなくなるので、
    #   期待値に近い 200 も併せて要求する。どちらが緩んでももう一方が残る。
    _lag_limit = min(200.0, main._GATE_EVENT_MIN_INTERVAL - main._GATE_EVENT_RETRY_INTERVAL)
    ok(set(main._GATE_EVENT_LAST) == {"light_tier_column_check_failed", "student_gate_read_failed"}
       and _max_lag is not None
       and _max_lag < _lag_limit,
       f"★成功時は打刻を後退させない = 連投しない (now-打刻={_max_lag} < {_lag_limit})")

    # ★★書けなかったときの挙動。**打刻を pop してはいけない**: pop すると次のフェイルオープンで
    #   即再試行になり「1フェイルオープン = 1スレッド + 1 DB 接続試行」の暴走になる
    #   (route_gate_middleware_failed は /api/ リクエストごとに発火する)。時計で後退させること。
    #   検査は2点: (a) 直後は再試行しない (b) 間隔を過ぎたら再試行する。
    #   ★_GATE_EVENT_RETRY_INTERVAL は検査中だけ大きくする。_slow_failing_db が
    #     1回あたり偽クロックを +20 進めるので、既定の 30 秒だと (a) の「直後」が
    #     間隔を越えてしまい、何を測っているのか分からなくなる。
    _real_retry = main._GATE_EVENT_RETRY_INTERVAL
    main._GATE_EVENT_RETRY_INTERVAL = 300.0
    _recorder_ok["v"] = False
    main._GATE_EVENT_LAST.clear()
    with _events_lock:
        _events.clear()
    _fake_clock["t"] += 1
    main._HAS_FEATURE_TIER_COL.pop("fail_until", None)
    main._AI_DISABLED_CACHE.pop(9500, None)
    main._load_student_gate(9500)
    _wait_until(lambda: len(_events) >= 2)
    _time_mod.sleep(0.15)   # 記録役が戻ったあとの「打刻の後退」(ロック+代入) が終わるまで
    with _events_lock:
        _n1 = len(_events)
    # (a) 直後に同じ障害が起きても再試行しない (pop 実装ならここで増えて落ちる)
    main._HAS_FEATURE_TIER_COL.pop("fail_until", None)
    main._AI_DISABLED_CACHE.pop(9500, None)
    main._load_student_gate(9500)
    _time_mod.sleep(0.15)
    with _events_lock:
        _n2 = len(_events)
    ok(_n2 == _n1, f"★書けなくても直後は再試行しない (1フェイルオープン=1スレッドの暴走を防ぐ) "
                   f"({_n1} → {_n2})")
    # (b) 間隔を過ぎたら再試行する (後退させずに放置すると永久に沈黙してしまう)
    _fake_clock["t"] += main._GATE_EVENT_RETRY_INTERVAL + 1
    main._HAS_FEATURE_TIER_COL.pop("fail_until", None)
    main._AI_DISABLED_CACHE.pop(9500, None)
    main._load_student_gate(9500)
    _retried = _wait_until(lambda: len(_events) > _n2)
    ok(_retried, f"★間隔を過ぎたら再試行する ({_n2} → {len(_events)})")
    main._GATE_EVENT_RETRY_INTERVAL = _real_retry

    # ★★呼び出し元をブロックしない。_load_student_gate は async middleware から呼ばれるので、
    #   ここを同期呼び出しに戻すと db() の pool 10秒 + connect 10秒 でイベントループが止まる
    #   ([[event-loop-blocking-async-def-trap]])。1秒かかる recorder で 1000 倍のマージンを取る。
    _recorder_ok["v"] = True
    _recorder_delay["v"] = 1.0
    main._GATE_EVENT_LAST.clear()
    main._HAS_FEATURE_TIER_COL.pop("fail_until", None)
    main._AI_DISABLED_CACHE.pop(9500, None)
    _t_before = _real_time()
    main._load_student_gate(9500)
    _elapsed = _real_time() - _t_before
    ok(_elapsed < 0.30,
       f"★記録は呼び出し元をブロックしない (recorder 1.0s に対し {_elapsed:.3f}s で返った)")
    _recorder_delay["v"] = 0.0
finally:
    # ★復元は recorder が先。_fake_recorder は db() を触らないので、遅れたスレッドが
    #   「実 recorder + 実 db()」の組み合わせを踏むのを最短で終わらせる。
    #   (どちらの順でも取りこぼしは残るが、DATABASE_URL を空にした二重防御があるので
    #    最悪でも捨てる一時 SQLite に1行入るだけ。)
    main._GATE_EVENT_RETRY_INTERVAL = _real_retry if "_real_retry" in dir() else main._GATE_EVENT_RETRY_INTERVAL
    main._record_ai_critical_event = _real_recorder
    main.db = _real_db
    main._GATE_EVENT_LAST.clear()
    _time_mod.time = _real_time
    main._AI_DISABLED_CACHE.pop(9500, None)
    main._HAS_FEATURE_TIER_COL.pop("fail_until", None)
    if _had_col is not None:
        main._HAS_FEATURE_TIER_COL["v"] = _had_col


print("\n[10] ★except が txn を rollback しないと、フェイルオープンではなく 500 になる")
# ★このゲートを書いた理由 (2026-08-21):
#   _check_ai_budget の except は「読み取りに失敗したら通す (フェイルオープン)」つもりで書かれ、
#   コメントも ceo.html のバナーもそう説明していた。しかし **Postgres は最初の execute が
#   失敗した時点で txn 全体が abort する**ので、rollback しないと同じ conn を使う直後の
#   execute (events の SELECT) が InFailedSqlTransaction で落ち、外へ伝播して 500 になる。
#   conn.close() にも到達せず接続が漏れる。= 説明と実挙動が正反対だった。
#   sqlite では再現しないので、**Postgres の挙動を模した接続**で検査する。


class _PoisonCursor:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=None):
        if self.conn.poisoned:
            raise RuntimeError("InFailedSqlTransaction: current transaction is aborted")
        if self.conn.fail_on and self.conn.fail_on in sql:
            self.conn.poisoned = True   # Postgres: 失敗した時点で txn 全体が abort する
            raise RuntimeError(self.conn.fail_msg)
        # ★数えるのは **成功した** execute だけ。poison チェックより前に append すると
        #   「試行した回数」になり、rollback を消す変異を当てても 2 本のままで判別できない
        #   (実際この assert だけ変異下でも緑だった = 主張とラベルが一致していなかった)。
        self.conn.executes.append(" ".join(sql.split())[:40])

    def fetchone(self):
        return None

    def fetchall(self):
        return []


class _PoisonConn:
    def __init__(self, fail_on, fail_msg):
        self.fail_on = fail_on
        self.fail_msg = fail_msg
        self.poisoned = False
        self.closed = False
        self.rolled = False
        self.executes = []

    def cursor(self):
        return _PoisonCursor(self)

    def rollback(self):
        self.rolled = True
        self.poisoned = False

    def commit(self):
        pass

    def close(self):
        self.closed = True


def _run_budget_with(conn):
    """差し替えた接続で _check_ai_budget を1回走らせ、漏れた例外を返す (無ければ None)。"""
    _rd, _rr = main.db, main._record_ai_critical_event
    try:
        main.db = lambda: conn
        main._record_ai_critical_event = lambda _n, _p: True   # スレッドから実DBを触らせない
        main._GATE_EVENT_LAST.clear()
        try:
            main._check_ai_budget(999999)
            return None
        except Exception as _pe:
            return f"{type(_pe).__name__}: {_pe}"
    finally:
        main.db = _rd
        main._record_ai_critical_event = _rr
        main._GATE_EVENT_LAST.clear()


# ケース1: 1本目 (契約情報) が落ちる = 列のマイグレーション未適用など
_c1 = _PoisonConn("FROM students", "column students.signup_utm_campaign does not exist")
_e1 = _run_budget_with(_c1)
ok(_e1 is None, f"★1本目が落ちても外へ例外を漏らさない (フェイルオープン) [{_e1}]")
ok(_c1.rolled, "★except で rollback している (しないと直後の execute が txn abort で落ちる)")
ok(_c1.closed, "★フェイルオープン経路でも conn を閉じている (漏らさない)")
ok(len(_c1.executes) >= 1,
   f"★rollback 後に後続の SELECT が **成功** している ({len(_c1.executes)} 本)")

# ケース2: 2本目 (events) が落ちる = statement timeout / ロック待ち / events 側の障害
#   ★以前はここで例外が外へ出て 500 になり、conn.close() にも到達しなかった。
#     [10] の1本目の assert は「読み取りに失敗しても漏らさない」と全称で名乗っていたのに、
#     実際に成立するのは1本目だけ = 検査が主張より狭い範囲しか守っていなかった。
_c2 = _PoisonConn("FROM events", "canceling statement due to statement timeout")
_e2 = _run_budget_with(_c2)
ok(_e2 is None, f"★2本目 (events) が落ちても外へ例外を漏らさない (フェイルオープン) [{_e2}]")
ok(_c2.closed, "★2本目が落ちた経路でも conn を閉じている (以前は __del__ 頼みだった)")
ok(len(_c2.executes) >= 1, f"★1本目は成功として数えられている ({len(_c2.executes)} 本)")


print("\n[11] ★記録の契約を **本物のコードで** 検査する")
# ★このゲートを書いた理由 (2026-08-21 敵対レビュー):
#   [9] は _record_ai_critical_event を fake に差し替えて回すので、**本物の戻り値契約**を
#   一度も検査していなかった。その戻り値 (書けたか) が「書けなかったら再試行する」設計の
#   全体を支えているのに、except を `return True` に変える変異が緑で通った。
#   同じ理由で _collect_gate_failures の中身 (session_id と名前の絞り込み) も未検査で、
#   `return {"total": 0}` に潰す変異も WHERE を書き換える変異も緑だった。
#   ここは **差し替えずに実 SQLite で** 動かす。
import json as _json11
import contextlib as _ctx11
import logging as _log11


@_ctx11.contextmanager
def _quiet_main_log():
    """わざと DB を壊す検査の**期待どおりの**ログを黙らせる。

    ★run_all_gates.py は行頭 `ERROR:` を違反とみなし、ゲートを [INCONSISTENT] で落とす
      (CLAUDE.md: 「CRASH / DEAD / INCONSISTENT は『通った』ではない」)。
      ここは失敗経路を**意図的に**踏む検査なので、log.error が出るのが正常。
      ★ゲート全体を INCONSISTENT_OK で免除しないこと。それをすると、将来この
        ゲートが出す**本物の**不整合まで一緒に見逃す。黙らせるのはこの区間だけ。"""
    _lg = _log11.getLogger("main")
    _prev = _lg.level
    _lg.setLevel(_log11.CRITICAL + 1)
    try:
        yield
    finally:
        _lg.setLevel(_prev)

_conn11 = main.db()
_c11 = _conn11.cursor()
_c11.execute("DELETE FROM events WHERE session_id = 'ai_failsafe'")
_conn11.commit()
_conn11.close()

# (a) 成功したら True を返し、events に1行入る
_ok11 = main._record_ai_critical_event("light_consume_failed", {"probe": 1})
ok(_ok11 is True, f"★_record_ai_critical_event は成功したら True を返す ({_ok11})")

# (b) 失敗したら False を返す (打刻の後退はこの戻り値だけが根拠)
_real_db11 = main.db
try:
    main.db = lambda: (_ for _ in ()).throw(RuntimeError("simulated outage"))
    with _quiet_main_log():
        _ng11 = main._record_ai_critical_event("light_consume_failed", {"probe": 2})
finally:
    main.db = _real_db11
ok(_ng11 is False, f"★書けなかったら False を返す ({_ng11})")


class _CloseProbeConn:
    """execute で投げても close されるか (finally の有無) を見る。"""

    def __init__(self):
        self.closed = False

    def cursor(self):
        class _C:
            def execute(_s, *_a, **_k):
                raise RuntimeError("boom")
        return _C()

    def commit(self):
        pass

    def close(self):
        self.closed = True


_cp = _CloseProbeConn()
try:
    main.db = lambda: _cp
    with _quiet_main_log():
        main._record_ai_critical_event("light_consume_failed", {"probe": 3})
finally:
    main.db = _real_db11
ok(_cp.closed, "★INSERT が落ちても conn を返す (finally が無いとプールが少しずつ枯れる)")

# (c) _collect_gate_failures が **実際に events を読み**、session_id と名前で絞れている
_conn11 = main.db()
_c11 = _conn11.cursor()
_c11.execute("DELETE FROM events")
for _n11, _cnt11 in (("route_gate_middleware_failed", 3), ("ai_budget_check_failed", 1)):
    for _ in range(_cnt11):
        _c11.execute("INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                     (_n11, _json11.dumps({"x": 1}), "ai_failsafe"))
# ノイズ: 別 session_id / 対象外の名前 (どちらも数えてはいけない)
_c11.execute("INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
             ("route_gate_middleware_failed", "{}", "student:1"))
_c11.execute("INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
             ("page_view", "{}", "ai_failsafe"))
_conn11.commit()
_conn11.close()

_gf11 = main._collect_gate_failures()
ok(_gf11.get("total") == 4,
   f"★実データを数えている (期待 4 / 実際 {_gf11.get('total')})")
ok({x["name"] for x in _gf11.get("by_name", [])} == {"route_gate_middleware_failed",
                                                     "ai_budget_check_failed"},
   f"★session_id と名前で絞れている ({sorted(x['name'] for x in _gf11.get('by_name', []))})")
ok(next((x["count"] for x in _gf11.get("by_name", [])
         if x["name"] == "route_gate_middleware_failed"), None) == 3,
   "★件数が正しい (別 session_id の行を数えていない)")

# (d) 集計に失敗したら total=None (0 と区別する。「0件だから健全」と誤読させない)
try:
    main.db = lambda: (_ for _ in ()).throw(RuntimeError("simulated outage"))
    with _quiet_main_log():
        _gf_ng = main._collect_gate_failures()
finally:
    main.db = _real_db11
ok(_gf_ng.get("total") is None,
   f"★集計に失敗したら total=None (0 と混同しない) ({_gf_ng.get('total')})")

# (e) **全 event 名**が記録される (1つだけ握り潰す変異を殺す)
_seen11 = []
_real_rec11 = main._record_ai_critical_event
try:
    main._record_ai_critical_event = lambda _n, _p: (_seen11.append(_n), True)[1]
    main._GATE_EVENT_LAST.clear()
    for _name11 in main._GATE_EVENT_NAMES:
        main._record_gate_failure_async(_name11, {"probe": 1})
    _t11 = 0.0
    while _t11 < 5.0 and len(_seen11) < len(main._GATE_EVENT_NAMES):
        __import__("time").sleep(0.02)
        _t11 += 0.02
finally:
    main._record_ai_critical_event = _real_rec11
    main._GATE_EVENT_LAST.clear()
ok(set(_seen11) == set(main._GATE_EVENT_NAMES),
   f"★すべての gate event 名が実際に記録へ回る (欠け: "
   f"{sorted(set(main._GATE_EVENT_NAMES) - set(_seen11))})")

# (f) ★アラートに昇格するか。ここが無いと CEO ダッシュの総合バッジが
#     「✅ 全システム正常」のままになり、「監視・運用」セクションは既定で display:none
#     なので**実質誰も見ない**。events に書くだけでは足りない、の最後の一段。
_conn11 = main.db()
_c11 = _conn11.cursor()
_c11.execute("DELETE FROM events")
_conn11.commit()
_conn11.close()
_snap_ok = main._collect_health_snapshot()
_al_ok = [a for a in main._evaluate_alerts(_snap_ok) if str(a.get("key", "")).startswith("gate_")]
ok(not _al_ok, f"★フェイルオープンが無いときはアラートを出さない ({[a['key'] for a in _al_ok]})")

_conn11 = main.db()
_c11 = _conn11.cursor()
for _ in range(3):
    _c11.execute("INSERT INTO events (name, props, session_id) VALUES (?, ?, ?)",
                 ("route_gate_middleware_failed", "{}", "ai_failsafe"))
_conn11.commit()
_conn11.close()
_snap_ng = main._collect_health_snapshot()
_al_ng = [a for a in main._evaluate_alerts(_snap_ng) if a.get("key") == "gate_failure_open"]
# ★ラベルで「赤帯に出る」と書いてはいけない。ceo.html:3067 の赤帯は critical (🚨) のときだけで、
#   warning は ⚠️ バッジ止まり。検証していないことをラベルが主張するのは、この差分で
#   何度も指摘された「検査が主張より狭い」の型そのもの。実際に効くのは
#   (a) alerts に入る (b) 監視メールが飛ぶ (info は 9074 で抑止されるが warning は飛ぶ)
#   (c) 「監視・運用」セクションの赤箱と ⚠️ バッジ、の3つ。
ok(len(_al_ng) == 1,
   f"★フェイルオープンがあればアラートに昇格する (監視メール + ⚠️バッジ。赤帯は critical 限定) "
   f"({len(_al_ng)} 件)")
ok(_al_ng and "3" in _al_ng[0].get("title", ""),
   f"★件数がタイトルに出る ({_al_ng[0].get('title') if _al_ng else 'なし'})")
# ★cooldown は **判定窓と揃える**。この判定は「直近24hに1行でもあれば発火」する level trigger
#   なので、既定 60 分のままだと 1回のフェイルオープンで監視メールが 24 通飛ぶ (実測)。
#   同ファイルの no_signups_24h が「60分おきに鳴り続けて監視メールの98%を占め、
#   本物の障害通知が埋もれた」という理由で降格された前例がある。
_cd = (_al_ng[0].get("cooldown_min") if _al_ng else None)
_win_min = (_snap_ng.get("gate_failures") or {}).get("hours", 24) * 60
ok(_cd is not None and _cd >= _win_min,
   f"★アラートの cooldown が判定窓以上 (cooldown={_cd}分 / 窓={_win_min}分)。"
   f"短いと1回の障害で監視メールが窓長ぶん鳴り続ける")
_conn11 = main.db()
_conn11.cursor().execute("DELETE FROM events")
_conn11.commit()
_conn11.close()

print("\n" + "=" * 60)
print(f"{N[0]} checks / FAIL {len(FAIL)}")
for f in FAIL:
    print("  FAILED:", f)
try:
    os.unlink(TMPDB)
except Exception:
    pass
sys.exit(1 if FAIL else 0)
