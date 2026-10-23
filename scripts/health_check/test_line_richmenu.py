#!/usr/bin/env python3
"""📱 公式 LINE のリッチメニュー 3×3 (2026-10-23) の回帰テスト。外部通信なし (LINE は偽物)。

server/line_richmenu.py が定義・画像・LINE API の手順を持ち、main.py の
/api/admin/line/richmenu{,/setup,/default} が呼ぶ。固定する性質:
  1. 定義が LINE の制約を満たす (9 ボタン・画像の外に出ない・重ならない・隙間なし・label 20 字・chatBarText 14 字)
  2. 画像が 2500×1686・1MB 未満の JPEG (LINE が受け付ける形)・格子 COL_W/ROW_H の合計と一致
  3. 「やること」「質問」のボタンの文字が bot のコマンド (_LINE_CMD_TODO / _LINE_CMD_QUESTION) に当たる
     ★ずれるとボタンを押しても bot が黙る
  4. 開くページがリポジトリ直下 (Vercel が配信する場所) に実在する (リンク切れのボタンを作らない)
  5. setup は 作成 → 画像 → 既定 の順。途中で失敗したら作ったメニューを消し、既定は変えない
     同じ名前で前に API から作ったメニューだけを消す (別の名前のメニューは残す)
     通信エラー・時間切れ (例外) でも後始末が走る・同時に 2 本走らせない・一覧を読めなければ古いメニューを消さない
  6. API は未認証で 401・dry_run=1 は LINE に書かない・default の DELETE は既定を外すだけ
  7. 未連携の LINE で「質問」→ 行き止まりの連携案内でなく「このトークにそのまま送って」(体験・保護者も押す)

実行:  python3 scripts/health_check/test_line_richmenu.py   # exit 0 = PASS / 1 = FAIL
"""
import importlib.util
import json
import os
import re
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER = os.path.join(REPO, "server")
MAIN_PY = os.path.join(SERVER, "main.py")
sys.path.insert(0, SERVER)

FAILURES = []
CRON = "test-cron-secret"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {detail}" if detail else ""))
    if not cond:
        FAILURES.append(label)


def jpeg_size(data):
    """JPEG の SOF から (幅, 高さ) を読む (PIL を使わない)。"""
    if data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            h = int.from_bytes(data[i + 5:i + 7], "big")
            w = int.from_bytes(data[i + 7:i + 9], "big")
            return w, h
        seg = int.from_bytes(data[i + 2:i + 4], "big")
        i += 2 + seg
    return None


class FakeLine:
    """line_richmenu._call の差し替え。呼ばれた順を記録し、指定した手順で失敗させられる。"""

    def __init__(self, fail_at=None, existing=None, default_id=None, list_status=200):
        self.calls = []
        self.fail_at = fail_at
        self.list_status = list_status
        self.menus = {m["richMenuId"]: m for m in (existing or [])}
        self.default_id = default_id
        self.n = 0

    def __call__(self, method, url, token, body=None, content_type="application/json", timeout=20):
        path = url.split("/v2/bot", 1)[1]
        self.calls.append((method, path, content_type))
        if method == "GET" and path == "/user/all/richmenu":
            return (200, {"richMenuId": self.default_id}) if self.default_id else (404, {"message": "no default"})
        if method == "GET" and path == "/richmenu/list":
            if self.list_status != 200:
                return self.list_status, {"message": "rate limit"}
            return 200, {"richmenus": list(self.menus.values())}
        if method == "POST" and path == "/richmenu":
            if self.fail_at == "create":
                return 400, {"message": "bad"}
            self.n += 1
            rid = f"richmenu-new{self.n}"
            self.menus[rid] = {"richMenuId": rid, "name": body["name"], "areas": body["areas"]}
            return 200, {"richMenuId": rid}
        m = re.fullmatch(r"/richmenu/([^/]+)/content", path)
        if method == "POST" and m:
            if self.fail_at == "upload":
                return 400, {"message": "image"}
            if self.fail_at == "upload_timeout":
                # 本物の _call が時間切れを status=0 に変えて返す形 (下の _call 単体テストで確かめる)
                return 0, "TimeoutError: The read operation timed out"
            return 200, {}
        m = re.fullmatch(r"/user/all/richmenu/([^/]+)", path)
        if method == "POST" and m:
            if self.fail_at == "default":
                return 400, {"message": "default"}
            self.default_id = m.group(1)
            return 200, {}
        if method == "DELETE" and path == "/user/all/richmenu":
            self.default_id = None
            return 200, {}
        m = re.fullmatch(r"/richmenu/([^/]+)", path)
        if method == "DELETE" and m:
            self.menus.pop(m.group(1), None)
            return 200, {}
        return 404, {"message": f"unexpected {method} {path}"}


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="richmenu_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        "DATABASE_URL": "",   # ★空にしないと本番 Postgres を見る
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
        "CRON_SECRET": CRON,
        "LINE_CHANNEL_ACCESS_TOKEN": "test-line-token",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_richmenu", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def main():
    print("📱 LINE リッチメニュー 3×3 回帰テスト\n")
    import line_richmenu as lr

    print("1. 定義が LINE の制約を満たす")
    defn = lr.build_definition()
    errs = lr.validate_definition(defn)
    check("validate_definition が空", not errs, "; ".join(errs))
    check("ボタンは 9 個", len(defn["areas"]) == 9, f"{len(defn['areas'])}")
    check("selected=True (開いた状態で出す)", defn["selected"] is True)
    # validate 自体が壊れていないこと (わざと崩した定義で落ちる)
    bad = json.loads(json.dumps(defn))
    bad["areas"][0]["bounds"]["width"] += 1
    check("重なり/はみ出しを validate が見つける", bool(lr.validate_definition(bad)))
    bad = json.loads(json.dumps(defn))
    bad["areas"].pop()
    check("隙間を validate が見つける", bool(lr.validate_definition(bad)))

    print("\n2. 画像")
    with open(lr.IMAGE_PATH, "rb") as f:
        img = f.read()
    check("1MB 未満", len(img) < 1024 * 1024, f"{len(img)} bytes")
    check("2500×1686 の JPEG", jpeg_size(img) == (2500, 1686), f"{jpeg_size(img)}")
    html = open(os.path.splitext(lr.IMAGE_PATH)[0] + ".html", encoding="utf-8").read()
    for i, a in enumerate(defn["areas"]):
        label = a["action"]["label"]
        check(f"元の HTML の {i + 1} 番目に「{label}」がある", label in html)

    print("\n3. bot のコマンドに当たる")
    src = open(MAIN_PY, encoding="utf-8").read()
    pats = {}
    for name in ("_LINE_CMD_TODO", "_LINE_CMD_QUESTION"):
        m = re.search(name + r' = _line_re\.compile\(r"([^"]+)"\)', src)
        check(f"main.py に {name} がある", bool(m))
        pats[name] = re.compile(m.group(1)) if m else None
    texts = {a["action"]["label"]: a["action"].get("text") for a in defn["areas"] if a["action"]["type"] == "message"}
    check("「今日のやること」→ _LINE_CMD_TODO", bool(pats["_LINE_CMD_TODO"] and pats["_LINE_CMD_TODO"].search(texts.get("今日のやること") or "")))
    check("「質問する」→ _LINE_CMD_QUESTION", bool(pats["_LINE_CMD_QUESTION"] and pats["_LINE_CMD_QUESTION"].search(texts.get("質問する") or "")))

    m = re.search(r'_LINE_TODO_LINK_PATH = "([^"]+)"', src)
    check("「宿題を開く」は bot の宿題リンク (_LINE_TODO_LINK_PATH) と同じ先", bool(m) and defn["areas"][0]["action"].get("uri") == lr.SITE + m.group(1),
          f"{defn['areas'][0]['action'].get('uri')}")

    print("\n4. 開くページが実在する")
    for a in defn["areas"]:
        act = a["action"]
        if act["type"] != "uri" or not act["uri"].startswith(lr.SITE + "/"):
            continue
        page = act["uri"][len(lr.SITE) + 1:].split("?")[0]
        check(f"{page} が実在する", os.path.isfile(os.path.join(REPO, page)))
        check(f"{page} は外部ブラウザで開く (LINE 内ブラウザだとログインが残らない)", "openExternalBrowser=1" in act["uri"])
    check("Instagram も外部で開く (LINE 内ブラウザだとログイン画面が出る)", "openExternalBrowser=1" in defn["areas"][8]["action"]["uri"])

    print("\n5. setup の手順と後始末")
    real_call = lr._call
    try:
        fake = FakeLine(existing=[{"richMenuId": "richmenu-old", "name": lr.MENU_NAME, "areas": []},
                                  {"richMenuId": "richmenu-other", "name": "別のメニュー", "areas": []}],
                        default_id="richmenu-old")
        lr._call = fake
        res = lr.setup("tok")
        check("成功", res.get("ok") is True, json.dumps(res, ensure_ascii=False))
        writes = [(m, p) for m, p, _ in fake.calls if m != "GET"]
        check("作成 → 画像 → 既定 の順", [w[1].split("/")[1] if w[0] == "POST" else "" for w in writes[:3]] == ["richmenu", "richmenu", "user"]
              and writes[1][1].endswith("/content"), f"{writes}")
        check("画像は image/jpeg で送る", any(p.endswith("/content") and ct == "image/jpeg" for _, p, ct in fake.calls))
        check("新しいメニューが既定", fake.default_id == res.get("richMenuId"))
        check("同じ名前の古いメニューを消す", "richmenu-old" not in fake.menus)
        check("別の名前のメニューは残す", "richmenu-other" in fake.menus)
        check("前の既定を返す", res.get("previous_default") == "richmenu-old")

        for step in ("create", "upload", "default"):
            fake = FakeLine(fail_at=step, default_id="richmenu-keep", existing=[{"richMenuId": "richmenu-keep", "name": lr.MENU_NAME, "areas": []}])
            lr._call = fake
            res = lr.setup("tok")
            check(f"{step} で失敗 → ok=False", res.get("ok") is False, json.dumps(res, ensure_ascii=False))
            check(f"{step} で失敗 → 既定は元のまま", fake.default_id == "richmenu-keep")
            check(f"{step} で失敗 → 作りかけのメニューを残さない", set(fake.menus) == {"richmenu-keep"}, f"{set(fake.menus)}")

        fake = FakeLine(fail_at="upload_timeout", default_id="richmenu-keep", existing=[{"richMenuId": "richmenu-keep", "name": lr.MENU_NAME, "areas": []}])
        lr._call = fake
        res = lr.setup("tok")
        check("画像の時間切れ → ok=False・作りかけを消す・既定は元のまま",
              res.get("ok") is False and set(fake.menus) == {"richmenu-keep"} and fake.default_id == "richmenu-keep", json.dumps(res, ensure_ascii=False))

        fake = FakeLine(list_status=429, existing=[{"richMenuId": "richmenu-old", "name": lr.MENU_NAME, "areas": []}], default_id="richmenu-old")
        lr._call = fake
        res = lr.setup("tok")
        check("一覧を読めない → 切り替えはする・古いメニューは消さずにそう返す",
              res.get("ok") is True and "richmenu-old" in fake.menus and isinstance(res.get("deleted_old"), str) and res.get("list_status") == 429,
              json.dumps(res, ensure_ascii=False))

        lr._SETUP_LOCK.acquire()
        try:
            fake = FakeLine()
            lr._call = fake
            res = lr.setup("tok")
            check("実行中にもう一度呼ぶ → busy で LINE に何もしない", res.get("step") == "busy" and fake.calls == [], json.dumps(res, ensure_ascii=False))
        finally:
            lr._SETUP_LOCK.release()
        check("busy の後に鍵が残らない", lr._SETUP_LOCK.acquire(blocking=False) and (lr._SETUP_LOCK.release() or True))
    finally:
        lr._call = real_call

    print("\n5b. _call は通信エラー・時間切れを例外にしない")
    import socket
    import urllib.error as ue
    real_open = lr.urllib.request.urlopen
    try:
        for exc in (TimeoutError("The read operation timed out"), socket.timeout("timed out"),
                    ue.URLError("Name or service not known"), ConnectionResetError("reset")):
            def _boom(*a, _e=exc, **k):
                raise _e
            lr.urllib.request.urlopen = _boom
            try:
                st, d = lr._call("POST", lr.API + "/richmenu", "secret-token-value", {"a": 1})
                check(f"{type(exc).__name__} → status 0", st == 0, f"{st} {d}")
                check(f"{type(exc).__name__} → 返す文にトークンを含めない", "secret-token-value" not in str(d))
            except Exception as e:
                check(f"{type(exc).__name__} → status 0", False, f"例外のまま: {type(e).__name__}")
    finally:
        lr.urllib.request.urlopen = real_open

    print("\n6. API")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    h = {"X-Cron-Secret": CRON}
    for method, path in (("get", "/api/admin/line/richmenu"), ("post", "/api/admin/line/richmenu/setup"),
                         ("delete", "/api/admin/line/richmenu/default")):
        r = getattr(client, method)(path)
        check(f"未認証の {method.upper()} {path} は 401", r.status_code == 401, f"{r.status_code}")
        r = getattr(client, method)(path, headers={"X-Cron-Secret": "wrong"})
        check(f"合言葉違いの {method.upper()} {path} は 401", r.status_code == 401, f"{r.status_code}")
    real_call = lr._call
    try:
        fake = FakeLine()
        lr._call = fake
        r = client.post("/api/admin/line/richmenu/setup?dry_run=1", headers=h)
        d = r.json() if r.status_code == 200 else {}
        check("dry_run は 200", r.status_code == 200, r.text[:200])
        check("dry_run は LINE に書かない", all(m == "GET" for m, _, _ in fake.calls), f"{fake.calls}")
        check("dry_run は検査結果とボタン名を返す", d.get("errors") == [] and len(d.get("buttons") or []) == 9)
        r = client.post("/api/admin/line/richmenu/setup", headers=h)
        check("本番の setup が成功", r.status_code == 200 and r.json().get("ok") is True, r.text[:200])
        r = client.get("/api/admin/line/richmenu", headers=h)
        check("status に新しい既定が出る", r.status_code == 200 and r.json().get("default_richmenu_id") == fake.default_id, r.text[:200])
        r = client.delete("/api/admin/line/richmenu/default", headers=h)
        check("default の DELETE で既定が外れる", r.status_code == 200 and fake.default_id is None, r.text[:200])
        check("default の DELETE はメニュー自体を消さない", len(fake.menus) == 1)
    finally:
        lr._call = real_call

    print("\n7. 「質問」の返事 (bot)")
    calls = []
    orig_api = mod._line_api_call
    mod._line_api_call = lambda endpoint, body: (calls.append((endpoint, body)) or True)
    try:
        for text in ("質問", "質問 体験授業の日程を知りたいです"):
            calls.clear()
            mod._handle_line_event({"type": "message", "replyToken": "rt-q", "webhookEventId": "ev-q-" + text,
                                    "source": {"type": "user", "userId": "U_not_linked_richmenu_00000000000"},
                                    "message": {"type": "text", "text": text}})
            reply = calls[0][1]["messages"][0]["text"] if calls else ""
            check(f"未連携「{text}」→ reply 1 回", [e for e, _ in calls] == ["message/reply"], calls)
            check(f"未連携「{text}」→ このトークにそのまま送れば塾長に届くと案内", reply == mod._LINE_QUESTION_NOT_LINKED and "そのまま送って" in reply, reply)
        calls.clear()
        mod._handle_line_event({"type": "message", "replyToken": "rt-t", "webhookEventId": "ev-t",
                                "source": {"type": "user", "userId": "U_not_linked_richmenu_00000000000"},
                                "message": {"type": "text", "text": "やること"}})
        check("未連携「やること」は今までどおり連携の案内", calls and calls[0][1]["messages"][0]["text"] == mod._LINE_NOT_LINKED_GUIDE, calls)
        check("「質問」だけの案内は「1通で」送るよう書く (内容だけを次に送ると届かない)", "1通で" in mod._LINE_QUESTION_USAGE)
    finally:
        mod._line_api_call = orig_api

    mod.LINE_CHANNEL_ACCESS_TOKEN = ""
    r = client.get("/api/admin/line/richmenu", headers=h)
    check("トークン未設定は 503", r.status_code == 503, f"{r.status_code}")

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for f in FAILURES:
            print("  -", f)
        sys.exit(1)
    print("✅ PASS")


if __name__ == "__main__":
    main()
