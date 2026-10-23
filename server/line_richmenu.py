"""LINE 公式アカウントのリッチメニュー (3×3・9 ボタン)。2026-10-23 塾長指示。

LINE Official Account Manager で作れるのは 6 ボタンまで。9 ボタンにするため Messaging API で登録する。
- API で「全員の既定」にしたメニューは、Manager で作ったメニューより優先して表示される。
- 元 (Manager のメニュー) に戻すときは unset_default() で既定を外すだけでよい (Manager 側は消していない)。
- 画像は assets/line_richmenu_9.jpg (2500×1686・1MB 未満)。元の HTML は同じ場所の .html
  (headless Chrome で描画した)。ボタンの位置は COL_W / ROW_H と画像の格子が一致していること。
- 「やること」「質問」は main.py の _LINE_CMD_TODO / _LINE_CMD_QUESTION と完全一致する文字列にする
  (変えるとボタンを押しても bot が黙る)。テスト: scripts/health_check/test_line_richmenu.py
"""
import http.client
import json
import os
import threading
import urllib.error
import urllib.request

SITE = "https://trillion-ai-juku.com"
WIDTH, HEIGHT = 2500, 1686
COL_W = (833, 834, 833)
ROW_H = (562, 562, 562)
MENU_NAME = "Trillion 9ボタン"
CHAT_BAR_TEXT = "メニュー"
IMAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "line_richmenu_9.jpg")

API = "https://api.line.me/v2/bot"
API_DATA = "https://api-data.line.me/v2/bot"
# 二度押し・同時実行の防止。並ぶと、片方が「同じ名前の古いメニュー」として相手が既定にしたばかりのメニューを消す
_SETUP_LOCK = threading.Lock()


def _uri(label, url):
    return {"type": "uri", "label": label, "uri": url}


def _text(label, text):
    return {"type": "message", "label": label, "text": text}


# 左上から右へ、上段 → 下段 (画像の並びと同じ順)
BUTTONS = (
    _uri("宿題を開く", SITE + "/mypage.html?focus=homework&openExternalBrowser=1"),
    _text("今日のやること", "やること"),
    _text("質問する", "質問"),
    _uri("予定・録画", SITE + "/class.html?openExternalBrowser=1"),
    _uri("マイページ", SITE + "/mypage.html?openExternalBrowser=1"),
    _uri("月額講座の動画", SITE + "/course-videos.html?openExternalBrowser=1"),
    _uri("体験授業", SITE + "/taiken.html?openExternalBrowser=1"),
    _uri("ホームページ", SITE + "/academy.html?openExternalBrowser=1"),
    # openExternalBrowser=1: LINE の中のブラウザだと Instagram のログイン画面が出やすい。外に渡すとアプリで開く
    _uri("Instagram", "https://www.instagram.com/trillion_eng/?openExternalBrowser=1"),
)


def build_definition():
    areas = []
    for i, action in enumerate(BUTTONS):
        r, c = divmod(i, len(COL_W))
        areas.append({
            "bounds": {"x": sum(COL_W[:c]), "y": sum(ROW_H[:r]), "width": COL_W[c], "height": ROW_H[r]},
            "action": dict(action),
        })
    return {
        "size": {"width": WIDTH, "height": HEIGHT},
        "selected": True,
        "name": MENU_NAME,
        "chatBarText": CHAT_BAR_TEXT,
        "areas": areas,
    }


def validate_definition(defn):
    """LINE の制約と、この塾の約束を満たしているかを見る。問題の一覧を返す (空なら OK)。"""
    errs = []
    if defn["size"] != {"width": WIDTH, "height": HEIGHT}:
        errs.append("size が 2500x1686 でない")
    if sum(COL_W) != WIDTH or sum(ROW_H) != HEIGHT:
        errs.append("格子の合計が画像の大きさと合わない")
    if not (1 <= len(defn["chatBarText"]) <= 14):
        errs.append("chatBarText は 1〜14 文字")
    if not (1 <= len(defn["name"]) <= 300):
        errs.append("name は 1〜300 文字")
    areas = defn["areas"]
    if not (1 <= len(areas) <= 20):
        errs.append("ボタンは 1〜20 個")
    covered = 0
    rects = []
    for a in areas:
        b = a["bounds"]
        if b["x"] < 0 or b["y"] < 0 or b["x"] + b["width"] > WIDTH or b["y"] + b["height"] > HEIGHT:
            errs.append(f"範囲が画像の外: {a['action'].get('label')}")
        covered += b["width"] * b["height"]
        rects.append((b["x"], b["y"], b["x"] + b["width"], b["y"] + b["height"]))
        act = a["action"]
        if not (1 <= len(act.get("label", "")) <= 20):
            errs.append(f"label は 1〜20 文字: {act.get('label')}")
        if act["type"] == "uri":
            if not act["uri"].startswith("https://") or len(act["uri"]) > 1000:
                errs.append(f"uri は https で 1000 文字以内: {act['uri']}")
        elif act["type"] == "message":
            if not (1 <= len(act["text"]) <= 300):
                errs.append(f"text は 1〜300 文字: {act.get('label')}")
        else:
            errs.append(f"想定外の action: {act['type']}")
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            a, b = rects[i], rects[j]
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                errs.append(f"ボタン {i + 1} と {j + 1} が重なっている")
    if covered != WIDTH * HEIGHT:
        errs.append("ボタンが画像全体を覆っていない (押しても反応しない隙間がある)")
    return errs


def _call(method, url, token, body=None, content_type="application/json", timeout=20):
    """(status, 応答の dict or 文字列) を返す。HTTP エラーも例外にせず status で返す。
    ★通信エラー・時間切れは status=0。例外で抜けると setup の作りかけの後始末が走らない。"""
    data = None
    headers = {"Authorization": f"Bearer {token}"}
    if body is not None:
        data = body if isinstance(body, (bytes, bytearray)) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        status = e.code
    except (urllib.error.URLError, OSError, http.client.HTTPException) as e:
        return 0, f"{type(e).__name__}: {e}"[:300]
    try:
        return status, (json.loads(raw) if raw else {})
    except ValueError:
        return status, raw[:500]


def status(token):
    """今の既定メニューと、API で作ったメニューの一覧 (Manager で作ったものは含まれない)。"""
    s1, d1 = _call("GET", f"{API}/user/all/richmenu", token)
    s2, d2 = _call("GET", f"{API}/richmenu/list", token)
    menus = d2.get("richmenus", []) if isinstance(d2, dict) else []
    return {
        "default_richmenu_id": d1.get("richMenuId") if s1 == 200 and isinstance(d1, dict) else None,
        "default_status": s1,
        "list_status": s2,
        "menus": [{"richMenuId": m.get("richMenuId"), "name": m.get("name"), "areas": len(m.get("areas", []))} for m in menus],
    }


def setup(token, delete_old=True):
    """作成 → 画像を上げる → 全員の既定にする。途中で失敗したら作ったメニューを消して元に戻す。
    delete_old: 同じ名前で前に API から作ったメニューを消す (Manager のメニューは対象外)。"""
    if not _SETUP_LOCK.acquire(blocking=False):
        return {"ok": False, "step": "busy", "error": "別の登録が実行中です。終わってからもう一度"}
    try:
        return _setup(token, delete_old)
    finally:
        _SETUP_LOCK.release()


def _setup(token, delete_old):
    defn = build_definition()
    errs = validate_definition(defn)
    if errs:
        return {"ok": False, "step": "validate", "errors": errs}
    with open(IMAGE_PATH, "rb") as f:
        image = f.read()
    if len(image) > 1024 * 1024:
        return {"ok": False, "step": "image", "error": "画像が 1MB を超えている"}
    before = status(token)

    s, d = _call("POST", f"{API}/richmenu", token, defn)
    if s != 200 or not isinstance(d, dict) or not d.get("richMenuId"):
        return {"ok": False, "step": "create", "status": s, "detail": d}
    new_id = d["richMenuId"]

    s, d = _call("POST", f"{API_DATA}/richmenu/{new_id}/content", token, image, content_type="image/jpeg", timeout=60)
    if s != 200:
        _call("DELETE", f"{API}/richmenu/{new_id}", token)
        return {"ok": False, "step": "upload_image", "status": s, "detail": d}

    s, d = _call("POST", f"{API}/user/all/richmenu/{new_id}", token)
    if s != 200:
        _call("DELETE", f"{API}/richmenu/{new_id}", token)
        return {"ok": False, "step": "set_default", "status": s, "detail": d}

    deleted = []
    if delete_old and before.get("list_status") != 200:
        deleted = "skipped: 一覧を読めなかったので古いメニューは消していない (次に成功したときに消える)"
    elif delete_old:
        for m in before.get("menus", []):
            if m.get("name") == MENU_NAME and m.get("richMenuId") and m["richMenuId"] != new_id:
                ds, _ = _call("DELETE", f"{API}/richmenu/{m['richMenuId']}", token)
                deleted.append({"richMenuId": m["richMenuId"], "status": ds})
    return {"ok": True, "richMenuId": new_id, "previous_default": before.get("default_richmenu_id"),
            "list_status": before.get("list_status"), "deleted_old": deleted}


def unset_default(token):
    """API の既定メニューを外す (Manager で作ったメニューの表示に戻る)。メニュー自体は消さない。"""
    s, d = _call("DELETE", f"{API}/user/all/richmenu", token)
    return {"ok": s == 200, "status": s, "detail": d}
