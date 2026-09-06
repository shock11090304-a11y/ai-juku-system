#!/usr/bin/env python3
"""⏱ イベントループ保護 (2026-09-07) の回帰テスト (AST + ソース検査 + 接続オプション。ネットワーク不要)。

システム点検で確定した点:
  - async def のルートが同期 DB ヘルパー (_verify_student_active / _record_ai_critical_event / _save_invite_code /
    _exam_pool_counts / db) をイベントループ上で直接呼んでいた (写真解答・多視点採点など 4 本)。プールが詰まると
    最大 20 秒ループが止まり全 API が待たされる。→ asyncio.to_thread 経由に。
  - 実行中クエリの時間上限 (statement_timeout) が無かった → 既定 120 秒 (env DB_STATEMENT_TIMEOUT)。
    起動時 DDL の専用接続は statement_timeout=0 (lock_timeout + 壁時計の締切で守る)。
  - 週次弱点プリントは全員分を 1 トランザクションで数分持っていた → 生徒ごとに送信前 commit。
"""
import ast
import importlib.util
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []
SYNC_DB_HELPERS = {"_verify_student_active", "_record_ai_critical_event", "_save_invite_code", "_exam_pool_counts", "db"}


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def is_route(fn):
    for d in fn.decorator_list:
        if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and isinstance(d.func.value, ast.Name) and d.func.value.id == "app":
            return True
    return False


def direct_sync_calls(fn):
    """async ルート本体 (ネストした def の中は除く) で、同期 DB ヘルパーを直接 Call しているものを列挙。"""
    found = []
    def walk(node):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue  # ネストした関数は別スコープ (to_thread で呼ばれる等)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id in SYNC_DB_HELPERS:
                found.append((child.func.id, child.lineno))
            walk(child)
    walk(fn)
    return found


def main():
    print("⏱ イベントループ保護 / statement_timeout 回帰テスト\n")
    src = open(MAIN_PY, encoding="utf-8").read()
    tree = ast.parse(src)
    async_routes = [n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and is_route(n)]
    print(f"1) async ルート {len(async_routes)} 本の本体で同期 DB ヘルパーを直接呼んでいないこと")
    offenders = {}
    for fn in async_routes:
        calls = direct_sync_calls(fn)
        if calls:
            offenders[fn.name] = calls
    check("直接呼び出しゼロ", not offenders, offenders)
    for name in ("ai_tutor_solve_from_image", "mock_exam_grade_essay_multiview", "admin_generate_invite_code", "admin_exam_questions_burst_seed"):
        fn = next((f for f in async_routes if f.name == name), None)
        check(f"{name}: to_thread 経由になっている", fn is not None and "asyncio.to_thread" in ast.get_source_segment(src, fn), name)

    print("2) statement_timeout の配線")
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="asyncchk_"), "test.db")
    os.environ.update({"DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0",
                       "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "", "BASE_URL": "https://example.invalid"})
    spec = importlib.util.spec_from_file_location("aijuku_main_asyncchk", MAIN_PY)
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)
    kw = mod._pg_connect_kwargs()
    check("既定 120 秒の statement_timeout が接続オプションに入る", "statement_timeout=120000" in kw.get("options", ""), kw)
    check("idle_in_transaction_session_timeout も残っている", "idle_in_transaction_session_timeout=" in kw.get("options", ""), kw)
    st = src[src.index("def _startup_db("):][:3000]
    check("起動時 DDL の専用接続は statement_timeout=0 (lock_timeout と壁時計で守る)", "-c statement_timeout=0" in st and "lock_timeout=" in st)

    print("3) 週次弱点プリントは生徒ごとに送信前 commit")
    ws = src[src.index("def _run_weekly_worksheet_generation("):][:30000]
    i = ws.index("worksheets_created += 1")
    check("worksheets_created の直後に conn.commit()", "conn.commit()" in ws[i:i + 400], ws[i:i + 300])

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
