#!/usr/bin/env python3
"""🔐 Vercel 側 管理 API (api/*.py) の総当たり対策 (2026-09-07) の回帰テスト (ネットワーク不要・KV は偽物)。

システム点検で「パスワード比較だけで試行回数の上限が無く、月末の一括引き落とし・スポット課金・任意宛先メール・
顧客一覧が総当たりで開く」と確定した点を直した。Vercel の Python 関数は 1 ファイル 1 関数で共有モジュールを
持てないため、9 本に同じ塊 (_verify_admin + KV カウンタ) を置いている。全部に対して:
  - 正しいパスワードは通る / 空は通らず失敗にも数えない
  - 同じ IP で 10 回失敗すると、正しいパスワードでも通らない (別 IP はまだ通る)
  - 全体で 60 回失敗すると、どの IP でも通らない
  - IP は x-real-ip (Vercel 付与) を優先し、x-forwarded-for は末尾を採る
  - chat.py は ?admin_pw= クエリを受け付けない
CI では stripe が入るので 9 本すべてを import する。ローカルで stripe が無い場合はその関数だけ skip する。
"""
import importlib.util
import os
import sys
import types

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = os.path.join(REPO, "api")
FILES = ["admin-charge-spot", "admin-charge-reconcile", "admin-charge-month-end-execute", "admin-charge-readonly",
         "past-due-invoice", "mail-send", "admin-registration-cancel", "registered-customers", "chat"]
PW = "correct-horse-battery-staple"
FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:200]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


class FakeKV:
    """Upstash REST の GET / INCR / EXPIRE を最小限に真似る (TTL は無視)。"""
    def __init__(self):
        self.store = {}
    def __call__(self, *args):
        cmd = args[0]
        if cmd == "GET":
            v = self.store.get(args[1])
            return {"result": None if v is None else str(v)}
        if cmd == "INCR":
            self.store[args[1]] = int(self.store.get(args[1], 0)) + 1
            return {"result": self.store[args[1]]}
        if cmd == "EXPIRE":
            return {"result": 1}
        return {"result": None}


def handler(pw=None, real_ip=None, xff=None, path="/api/x"):
    h = {}
    if pw is not None:
        h["X-Admin-Password"] = pw
    if real_ip:
        h["x-real-ip"] = real_ip
    if xff:
        h["x-forwarded-for"] = xff
    return types.SimpleNamespace(headers=h, path=path)


def load(name):
    os.environ.setdefault("KV_REST_API_URL", "")
    os.environ.setdefault("KV_REST_API_TOKEN", "")
    os.environ.setdefault("STRIPE_SECRET_KEY", "")
    os.environ["CHAT_ADMIN_PASSWORD"] = PW
    spec = importlib.util.spec_from_file_location("vercel_" + name.replace("-", "_"), os.path.join(API, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    print("🔐 Vercel 管理 API 総当たり対策 回帰テスト\n")
    in_ci = bool(os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"))
    for name in FILES:
        print(f"[{name}]")
        try:
            mod = load(name)
        except ModuleNotFoundError as e:
            if in_ci:
                check(f"{name}: import できる", False, f"{e}")
            else:
                print(f"  ⚠️  skip (ローカルに {e.name} が無い。CI では検査される)")
            continue
        except Exception as e:
            check(f"{name}: import できる", False, f"{type(e).__name__}: {e}")
            continue
        for fn in ("_verify_admin", "_admin_kv", "_admin_client_ip", "_admin_fail_count", "_admin_fail_record"):
            check(f"{name}: {fn} がある", callable(getattr(mod, fn, None)))
        kv = FakeKV()
        mod._admin_kv = kv
        check("正しいパスワードは通る", mod._verify_admin(handler(PW, real_ip="203.0.113.1")) is True)
        check("空は通らず、失敗にも数えない", mod._verify_admin(handler("", real_ip="203.0.113.1")) is False and not kv.store)
        check("ヘッダ無しは通らない", mod._verify_admin(handler(None, real_ip="203.0.113.1")) is False)
        for _ in range(10):
            mod._verify_admin(handler("wrong", real_ip="203.0.113.1"))
        check("同じ IP で 10 回失敗 → 正しくても通らない", mod._verify_admin(handler(PW, real_ip="203.0.113.1")) is False, kv.store)
        check("別 IP はまだ通る", mod._verify_admin(handler(PW, real_ip="203.0.113.2")) is True)
        check("失敗は IP キーと全体キーの両方に記録", kv.store.get("adminfail:ip:203.0.113.1") == 10 and kv.store.get("adminfail:global") == 10, kv.store)
        kv.store["adminfail:global"] = 60
        check("全体 60 回で、失敗ゼロの IP でも通らない", mod._verify_admin(handler(PW, real_ip="203.0.113.3")) is False)
        kv.store.clear()
        check("x-forwarded-for は末尾 (プロキシが付けた側) を採る", mod._admin_client_ip(handler(PW, xff="9.9.9.9, 198.51.100.7")) == "198.51.100.7")
        check("x-real-ip があればそれを優先", mod._admin_client_ip(handler(PW, real_ip="203.0.113.9", xff="9.9.9.9")) == "203.0.113.9")
        mod._admin_kv = lambda *a: None   # KV が無い環境
        check("KV 無しでも正しいパスワードは通る (fail-open・従来どおり)", mod._verify_admin(handler(PW, real_ip="203.0.113.1")) is True)
        check("KV 無しでも間違いは通らない", mod._verify_admin(handler("wrong", real_ip="203.0.113.1")) is False)
        if name == "chat":
            mod._admin_kv = FakeKV()
            check("chat: ?admin_pw= クエリでは通らない", mod._verify_admin(handler(None, real_ip="1.1.1.1", path=f"/api/chat?admin_pw={PW}")) is False)
    src = open(os.path.join(API, "chat.py"), encoding="utf-8").read()
    check("chat.py に admin_pw のクエリ解釈が残っていない", "parse_qs(qs).get(\"admin_pw\"" not in src)
    js = open(os.path.join(REPO, "payment", "app.js"), encoding="utf-8").read()
    check("payment/app.js はパスワードを localStorage に保存しない", "localStorage.setItem(PW_KEY" not in js and "localStorage.setItem(CHAT_PW_KEY" not in js)
    check("payment/app.js は sessionStorage を使う", "sessionStorage.getItem(PW_KEY)" in js and "sessionStorage.getItem(CHAT_PW_KEY)" in js)
    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
