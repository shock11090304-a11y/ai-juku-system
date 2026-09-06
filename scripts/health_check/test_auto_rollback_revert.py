#!/usr/bin/env python3
"""⏪ 自動ロールバックの回帰テスト (GitHub API は偽物・ネットワーク不要・一時 SQLite)。

システム点検で「_attempt_auto_rollback が main を parent SHA へ force 更新する (履歴の書き換え) ため、塾長の手元と
食い違って次の push が拒否され、複数 commit の push は末尾 1 つしか戻らない」と確定した点を直した。
  - parent の tree を持ち現 HEAD を親にする commit を POST git/commits で作る (= git revert)
  - refs/heads/main の更新は force=False (fast-forward のみ)
  - 記録 (to_sha) は revert commit の SHA、内容の戻り先は reverted_tree_of
  - force 付きの PATCH は一切呼ばない
"""
import asyncio
import importlib.util
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="rollback_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid", "GITHUB_REVERT_PAT": "ghp_dummy_for_test", "AUTO_ROLLBACK_ENABLED": "1",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_rollback", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def main():
    print("⏪ 自動ロールバック (revert commit 方式) 回帰テスト\n")
    mod = load_main()
    branch = mod.AUTO_ROLLBACK_BRANCH
    calls = []

    def fake_api(method, path, body=None, timeout=15):
        calls.append((method, path, body))
        if method == "GET" and path.endswith(f"/git/refs/heads/{branch}"):
            return {"ok": True, "status": 200, "json": {"object": {"sha": "HEADSHA1234567"}}}
        if method == "GET" and path.endswith("/commits/HEADSHA1234567") and "/git/" not in path:
            return {"ok": True, "status": 200, "json": {"parents": [{"sha": "PARENTSHA12345"}], "commit": {"message": "bad commit", "author": {"name": "dev"}}}}
        if method == "GET" and path.endswith("/git/commits/PARENTSHA12345"):
            return {"ok": True, "status": 200, "json": {"tree": {"sha": "PARENTTREE"}}}
        if method == "POST" and path.endswith("/git/commits"):
            return {"ok": True, "status": 201, "json": {"sha": "REVERTSHA99999"}}
        if method == "PATCH" and path.endswith(f"/git/refs/heads/{branch}"):
            return {"ok": True, "status": 200, "json": {"object": {"sha": (body or {}).get("sha")}}}
        return {"ok": False, "status": 0, "error": f"unexpected {method} {path}"}

    mod._github_api = fake_api
    res = asyncio.run(mod._attempt_auto_rollback("regression test", ["f1"], force=True))
    check("成功する", res.get("ok") is True, res)
    check("新しい HEAD は revert commit", res.get("revert_commit_sha") == "REVERTSHA99999", res)
    check("内容の戻り先は parent", res.get("reverted_to_sha") == "PARENTSHA12345", res)
    posts = [c for c in calls if c[0] == "POST" and c[1].endswith("/git/commits")]
    check("git/commits に POST が 1 回", len(posts) == 1, calls)
    if posts:
        body = posts[0][2] or {}
        check("revert commit の tree は parent の tree", body.get("tree") == "PARENTTREE", body)
        check("revert commit の親は現 HEAD (履歴が一直線に残る)", body.get("parents") == ["HEADSHA1234567"], body)
        check("commit message に理由と手順", "regression test" in body.get("message", "") and "revert" in body.get("message", "").lower(), body.get("message"))
    patches = [c for c in calls if c[0] == "PATCH"]
    check("refs の更新は 1 回・force=False (fast-forward のみ)", len(patches) == 1 and (patches[0][2] or {}).get("force") is False and (patches[0][2] or {}).get("sha") == "REVERTSHA99999", patches)
    check("force=True の PATCH は一切無い", not any((c[2] or {}).get("force") is True for c in calls if c[0] == "PATCH"))
    rec = res.get("rb_record") or {}
    check("記録: to_sha=revert commit / reverted_tree_of=parent", rec.get("to_sha") == "REVERTSHA99999" and rec.get("reverted_tree_of") == "PARENTSHA12345", rec)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) AS n FROM events WHERE name = 'auto_rollback'"); n = c.fetchone()["n"]; conn.close()
    check("events に auto_rollback が記録される", n == 1, n)
    # ループ防止: 現 HEAD が直近 rollback の戻り先 (revert commit) なら再ロールバックしない
    calls.clear()
    def fake_api2(method, path, body=None, timeout=15):
        if method == "GET" and path.endswith(f"/git/refs/heads/{branch}"):
            return {"ok": True, "status": 200, "json": {"object": {"sha": "REVERTSHA99999"}}}
        return fake_api(method, path, body, timeout)
    mod._github_api = fake_api2
    res2 = asyncio.run(mod._attempt_auto_rollback("second failure", ["f2"], force=False))
    check("ロールバック直後の再失敗では、さらに過去へ戻さない (loop 防止 or cooldown で skip)", res2.get("ok") is False, res2)
    check("その際 GitHub には何も書かない", not any(c[0] in ("POST", "PATCH") for c in calls), calls)
    src = open(MAIN_PY, encoding="utf-8").read()
    fn = src[src.index("async def _attempt_auto_rollback"):][:9000]
    check("ソースに force: True の ref 更新が残っていない", '"force": True' not in fn)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
