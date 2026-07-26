#!/usr/bin/env python3
"""イベントループ・ブロッキングの回帰テスト (2026-07-26 の本番502事故)。

【事故の要約】
  22:40 JST に /api/trial/signup が Railway edge から 502 "Application failed to respond"。
  直後に GET /api/health (DBもNWも触らない純粋 dict 返却) が **51.66 秒**かかった。
  その時間帯の Anthropic 呼び出しは1時間で5件しかなく、「同時アクセス過多」では説明できない。

【真因】
  `async def` のまま同期ブロッキング処理をイベントループ上で直接実行していた。
  uvicorn は単一プロセス・単一イベントループなので、ループが塞がると全リクエストが停止し、
  新規TCP接続すら受け付けられなくなる → edge から見ると「アプリが応答しない」= 502。
  最悪だったのが /api/ai/call (ai_proxy) で、**await が1つも無いのに async def** のまま
  _call_anthropic_safe() (既定180秒・最大600秒 × 3モデルtier × 再試行) を直叩きしていた。

【このテストが守っているもの】
  「遅いAI呼び出しが実行中でも /api/health が即答すること」。
  修正前に実行すると health が 17秒ブロックされて FAIL する (実測値)。
  修正後は 5ms 前後で PASS する。

使い方:
    python3 scripts/health_check/test_event_loop_blocking.py
    (終了コード 0 = PASS / 1 = FAIL / 2 = テスト自体が無効)

★このテストは外部へ一切通信しない (Anthropic 呼び出しは sleep に差し替える)。
"""
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER_DIR = os.path.join(REPO, "server")
sys.path.insert(0, SERVER_DIR)
os.chdir(SERVER_DIR)

SLOW_SECONDS = 6.0   # 1回のAI呼び出しが何秒ブロックする想定か
PORT = 8771
CONCURRENT_AI_CALLS = 3
HEALTH_BUDGET_S = 1.0   # AI実行中でも health はこの秒数以内に返るべき

import main            # noqa: E402
import uvicorn         # noqa: E402


def _fake_slow_anthropic(body, *, kind="chat", student_id=None):
    """本物と同じく**同期でブロックする**スタブ (実際のAnthropicは呼ばない)。"""
    time.sleep(SLOW_SECONDS)
    return {"content": [{"type": "text", "text": "ok"}],
            "usage": {"input_tokens": 1, "output_tokens": 1}}


def main_test() -> int:
    # 外部通信とゲートを差し替え、ai_proxy 本体まで到達させる
    main._call_anthropic_safe = _fake_slow_anthropic
    main._origin_allowed = lambda request: True
    main._get_current_student = lambda auth: {"id": 1, "name": "t", "plan": "founder_special"}
    main._check_ai_budget = lambda *a, **k: None
    main._check_quota = lambda *a, **k: None
    main._record_ai_usage = lambda *a, **k: None
    main.ANTHROPIC_API_KEY = main.ANTHROPIC_API_KEY or "sk-test-dummy"

    cfg = uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="error")
    srv = uvicorn.Server(cfg)
    threading.Thread(target=srv.run, daemon=True).start()
    base = f"http://127.0.0.1:{PORT}"
    for _ in range(100):
        try:
            urllib.request.urlopen(base + "/api/health", timeout=1).read()
            break
        except Exception:
            time.sleep(0.2)
    else:
        print("❌ サーバが起動しなかった")
        return 2

    def get_health():
        t0 = time.time()
        try:
            urllib.request.urlopen(base + "/api/health", timeout=90).read()
            return time.time() - t0, None
        except Exception as e:
            return time.time() - t0, type(e).__name__

    print(f"baseline /api/health: {get_health()[0] * 1000:.0f}ms\n")

    results = []

    def fire_ai():
        body = json.dumps({
            "kind": "chat", "student_id": 1, "system": "you are a tutor",
            "messages": [{"role": "user", "content": "hi"}], "max_tokens": 16,
        }).encode()
        req = urllib.request.Request(
            base + "/api/ai/call", data=body, method="POST",
            headers={"Content-Type": "application/json", "Authorization": "Bearer x",
                     "Origin": "https://trillion-ai-juku.com"})
        t0 = time.time()
        try:
            urllib.request.urlopen(req, timeout=120).read()
            results.append(("ok", time.time() - t0))
        except urllib.error.HTTPError as e:
            results.append((f"http{e.code}", time.time() - t0))
        except Exception as e:
            results.append((type(e).__name__, time.time() - t0))

    threads = [threading.Thread(target=fire_ai) for _ in range(CONCURRENT_AI_CALLS)]
    for t in threads:
        t.start()
    time.sleep(1.0)   # AI呼び出しが確実に in-flight になるまで待つ

    print(f"--- 遅いAI呼び出し{CONCURRENT_AI_CALLS}本が実行中 (各{SLOW_SECONDS}s) の health 応答 ---")
    worst = 0.0
    for i in range(5):
        d, err = get_health()
        worst = max(worst, d)
        print(f"  health #{i + 1}: {d * 1000:7.0f}ms  {err or ''}")
        time.sleep(0.6)
    for t in threads:
        t.join()

    srv.should_exit = True

    # 前提条件: AI呼び出しが本当に遅い処理へ到達していたか (到達していなければテストは無効)
    reached = [d for st, d in results if st == "ok" and d >= SLOW_SECONDS * 0.9]
    if len(reached) != CONCURRENT_AI_CALLS:
        print(f"\n⚠️ 無効なテスト: AI呼び出しが遅延処理に到達していない -> {results}")
        return 2
    print(f"\n前提OK: AI呼び出し{CONCURRENT_AI_CALLS}本とも {SLOW_SECONDS}s ブロックした")
    print(f"AI実行中の health 最悪応答: {worst * 1000:.0f}ms (許容 {HEALTH_BUDGET_S * 1000:.0f}ms)")
    if worst < HEALTH_BUDGET_S:
        print("✅ PASS: イベントループは空いている (遅いAI呼び出しに巻き込まれない)")
        return 0
    print(f"❌ FAIL: health が {worst:.1f}s ブロックされた = ループが塞がれている")
    print("   → `async def` のまま同期ブロッキングしているハンドラ/スケジューラを探すこと")
    return 1


if __name__ == "__main__":
    sys.exit(main_test())
