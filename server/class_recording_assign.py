#!/usr/bin/env python3
"""授業録画(YouTube 限定公開)の割り当て判定 — CLI と API が共有する**唯一の実装**。

置き場所が server/ なのは Railway のデプロイ範囲がここだから (server/railway.json の
startCommand は `uvicorn main:app` = 作業ディレクトリが server/)。呼ぶのは2か所:
  - scripts/class_recordings/assign_from_playlists.py … 塾長のターミナル (railway run)
  - server/main.py の POST /api/admin/class-recordings/auto-assign … CEO 画面のボタン
**同じ関数**を呼ばせる。2か所に書き写すと必ず片方だけ直されて判定がずれ、
「配布漏れを配布済みと誤報告しない」というこの仕組みの目的が片側で壊れる。

★このリポジトリは PUBLIC。再生リストID・動画IDは**絶対にここへ書かない**。
★ネットワーク越しの取得はするが **DB には触らない**(入出力は呼び出し側)。
  判定表ゲート scripts/class_recordings/check_assign_logic.py がこのモジュールを直接検査する。
★「取得できなかった」を「0本(新着なし)」と言わない。ここを間違えると
  配布漏れを「配布済み」と誤報告する。判定は fetch_playlist() を参照。
"""
import collections
import datetime
import re
import socket
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")

# 再生リスト名 → class_sessions.title の先頭ラベル。
# ★時間割とのズレはここに明示する。日付の検算は**再生リスト側の曜日**で行う。
#   [2026-09-01] 「金曜3限 → 木曜3限」の付け替えを撤去した。ズレの正体は再生リスト側ではなく
#   時間割側の誤記で、実授業も録画も金曜3限だった (塾長指摘)。時間割 label を
#   「金曜3限 国公立コース 長文読解」に直したので、再生リスト名とそのまま一致する。
SLOT_OVERRIDE = {"日曜1限": "日曜"}  # 日曜は1コマだけで title が「日曜 高校国語」

# 旧ラベルへの一方向フォールバック。移送の途中だけ使う一時的な表で、平常時は**空**が正しい。
#   [2026-09-01] 「金曜3限 → 木曜3限」の移送は完了したので空にした
#   (本番DB を読み返して students.class_labels / class_attend / class_sessions.title の
#    旧ラベルが 0 件であることを確認済み)。
#   ★同種の改名をするときはここに一時的に入れること。入れないと、コードを先にデプロイした瞬間に
#     「新ラベルで0件マッチ」+「旧ラベルの授業に再生リストが無い」で blocking が2件立ち、
#     **15クラス全部の投入が1件も走らずに止まる**。移送が済んだら必ず空に戻す。
LEGACY_SLOT = {}

DAY = {"月": 0, "火": 1, "水": 2, "木": 3, "金": 4, "土": 5, "日": 6}
DAY_LABEL = {v: k for k, v in DAY.items()}
PAGE_LIMIT = 100          # 1ページに載る上限。継続トークンは追わない。
# ★動画名に年は書かれないので、日付ラベルは「もう終わった回」として**過去側**に読む
#   (resolve_year)。MAX_AGE_DAYS はその解釈幅で、これより古い読みは「来年の日付を先に
#   書いた打ち間違い」と区別が付かないので手作業に回す。
#   ★120日だった頃 (2026-08-28 まで) は、1年ぶんの回が入った再生リストを初めて取り込むと
#     半年前までの正しい回が全部「打ち間違いを疑う」で弾かれた (日曜1限で実測11本)。
#     そもそも打ち間違いの本命 =「前回のタイトルをコピペして日付を直し忘れる」は
#     7の倍数のズレなので日数の上限では捕まらない。捕まえるのは build_plan の
#     **同じ授業に同じ日付ラベル**検査。日数の上限にその役を持たせない。
MAX_AGE_DAYS = 305
OLD_LABEL_DAYS = 120      # これより古い回は登録するが「過去分の取り込み」として知らせる
# ★これは「年をどちらに読むか」の猶予であって、未来日を**受理する**幅ではない
#   (明日の日付は 2026-08-29 と読んだうえで「未来の日付」として拒否する)。この猶予が無いと
#   明日の日付が去年と読まれ、「305日より離れた日付」という的外れな理由で拒否される。
FUTURE_SLACK_DAYS = 2
STALE_DAYS = 28           # このクラスの最新録画がこれより古ければ「止まっている」と知らせる

# 呼び出し側が DB から渡す録画1行。★列を減らすと TypeError で**止まる**(黙って劣化しない)。
Recording = collections.namedtuple("Recording", "session_id video_url provider title rec_id")

JST = datetime.timezone(datetime.timedelta(hours=9))


def today_jst():
    """今日 (JST)。

    ★API 側で date.today() を使ってはいけない。Railway は UTC なので、JST の朝 9時前は
      **前日**になり、その日アップした動画の日付ラベルが「未来の日付」として全部弾かれる
      (date_label の未来チェックに掛かる)。塾のカレンダーは JST が正。
    """
    return datetime.datetime.now(JST).date()


def http_get(url, timeout=30):
    """(本文, エラー文) を返す。**例外は投げない**。

    ★curl の subprocess ではなく urllib を使う: Railway のコンテナに curl が入っている
      保証が無く、入っていないと「YouTube に接続できない」と出続けて原因に辿り着けない。
    """
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ja"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace"), None
    except urllib.error.HTTPError as e:   # ★URLError の派生なので先に捕まえる
        return None, f"YouTube が HTTP {e.code} を返した — 少し待ってもう一度実行してください"
    except urllib.error.URLError as e:
        if isinstance(e.reason, (TimeoutError, socket.timeout)):
            return None, "取得に時間がかかりすぎた — もう一度実行してください"
        return None, "YouTube に接続できない — ネット接続を確認してもう一度実行してください"
    except (TimeoutError, socket.timeout):
        return None, "取得に時間がかかりすぎた — もう一度実行してください"
    except Exception as e:
        # ★例外文をそのまま出さない (URL = 再生リストID が載りうる)
        return None, f"YouTube への接続で想定外のエラー ({type(e).__name__})"


def slot_of(playlist_name):
    """「8月以降火曜日３時間目」→ (曜日index, 再生リスト上のslot, 割り当て先slot)。読めなければ None。"""
    n = unicodedata.normalize("NFKC", playlist_name or "")
    d = re.search(r"([月火水木金土日])曜", n)
    p = re.search(r"([0-9]+)\s*(?:時間目|限)", n)
    if not d or not p or not (1 <= int(p.group(1)) <= 9):
        return None
    raw = f"{d.group(1)}曜{int(p.group(1))}限"
    return DAY[d.group(1)], raw, SLOT_OVERRIDE.get(raw, raw)


def _texts(o, out):
    """ytInitialData から「画面に出る文字列」を全部集める。

    ★YouTube は同じ情報を2レイアウトで返す (実測 2026-08-18):
      新 pageHeaderRenderer      → {"content": "2 本の動画"}          … 1つの文字列
      旧 playlistHeaderRenderer  → {"runs":[{"text":"11"},{"text":" 本の動画"}]} … 分割
    分割側を読めないと、正常な再生リストを「本数が読めない」と誤って弾く
    (実在の公開リスト12本中9本が旧レイアウトだった)。runs は必ず連結してから見る。
    """
    if isinstance(o, dict):
        if isinstance(o.get("runs"), list):
            out.append("".join(r.get("text", "") for r in o["runs"] if isinstance(r, dict)))
        for k in ("content", "simpleText"):
            if isinstance(o.get(k), str):
                out.append(o[k])
        for v in o.values():
            _texts(v, out)
    elif isinstance(o, list):
        for v in o:
            _texts(v, out)


def _alert_severity(data):
    """top-level alerts を (致命か, 本文) にする。無ければ (False, None)。

    ★type を見ること。「1 本の利用できない動画が非表示になっています」は INFO で、
      これを致命扱いすると、動画を1本消しただけでそのクラスが以後ずっと
      「取得できず」になり --apply が全クラス分止まる。
    ★本文は構造から取る。json.dumps は `"text": "…"` と空白を入れるので
      `'"text":"'` の正規表現は**常に不発**になる (旧実装のバグ)。
    """
    alerts = data.get("alerts")
    if not alerts:
        return False, None
    fatal = False
    for entry in alerts if isinstance(alerts, list) else []:
        if not isinstance(entry, dict):
            continue
        for renderer in entry.values():
            if isinstance(renderer, dict) and str(renderer.get("type", "")).upper() == "ERROR":
                fatal = True
    msgs = []
    _texts(alerts, msgs)
    return fatal, next((m for m in msgs if m.strip()), None)


def fetch_playlist(pid, get=None):
    """再生リストを読む → (items, fatal, warn)。items が None なら**中身を信用しない**。

    get は (url) -> (本文, エラー文) の差し替え口。判定表ゲートがここに合成ページを流す
    (ネットワークに出ない)。既定は http_get。

    ★実測(2026-08-18)で確かめた見分け方:
      - 削除/存在しないID → HTTP 200 + ytInitialData あり + alerts(type=ERROR) + contents 無し
        = 素朴に解析すると「0本」に化ける。ここを fatal にするのがこの関数の主目的。
      - 本当に空 → contents あり・alerts 無し・本数表記なし・「この再生リストには動画がありません」あり
      - 正常 → 「N 本の動画」表記があるので解析本数と突き合わせる。食い違えば構造変更 (fatal)。
    """
    import json
    body, err = (get or http_get)(f"https://www.youtube.com/playlist?list={pid}")
    if body is None:
        return None, err or "YouTube を読めなかった", None
    m = re.search(r"ytInitialData\s*=\s*(\{.*?\});\s*</script>", body, re.S)
    if not m:
        return None, "YouTubeのページを解析できない (構造変更かブロック)", None
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        return None, f"ページのJSONを読めない ({e})", None

    fatal_alert, alert_msg = _alert_severity(data)
    if fatal_alert:
        return None, f"再生リストを開けない: {alert_msg or 'YouTubeがエラーを返した'}", None
    if not data.get("contents"):
        return None, "再生リストの中身が返ってこない (非公開・削除・構造変更)", None
    warn = f"YouTubeからのお知らせ: {alert_msg}" if alert_msg else None

    hits = []

    def walk(o):
        if isinstance(o, dict):
            if "lockupViewModel" in o:
                hits.append(o["lockupViewModel"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(data)
    items = []
    for lm in hits:
        if lm.get("contentType") != "LOCKUP_CONTENT_TYPE_VIDEO":
            continue
        vid = lm.get("contentId")
        title = (lm.get("metadata", {}).get("lockupMetadataViewModel", {})
                 .get("title", {}) or {}).get("content", "")
        if vid and not any(v == vid for v, _ in items):
            items.append((vid, title))

    # ★解析結果を YouTube 自身の表示本数で検算する (0本に化ける事故の最後の砦)
    page_texts = []
    _texts(data, page_texts)
    shown = None
    for t in page_texts:
        mm = re.search(r"([0-9,]+)\s*本の動画", t)
        if mm:
            shown = int(mm.group(1).replace(",", ""))
            break
    empty_marker = any("動画がありません" in t or "動画はありません" in t for t in page_texts)

    # ★1ページ上限は**お知らせの有無と無関係に**独立して判定する。
    #   「利用できない動画」の分岐を先に置くと、お知らせが1件あるだけで上限超過が飲み込まれ、
    #   溢れている新しい回が黙って消える (docstring の「100本で止める」が効かなくなる)。
    if shown is not None and shown > PAGE_LIMIT and len(items) >= PAGE_LIMIT - 5:
        # 1ページ目は**先頭**100本。新しい回は末尾に足されるので、溢れているのは新しい方。
        return items, f"1ページ上限 {PAGE_LIMIT}本 (全 {shown}本) — 新しい回が見えていない", warn

    if shown is None:
        if items:
            return None, f"表示本数が読めないのに {len(items)}本 解析した — この行をそのまま開発者に伝えてください", warn
        if not empty_marker:
            # ★ここを「0本」で通すと、renderer 改名時に全リストが警告なしで0本になる
            return None, "本数表記も「動画がありません」も見つからない — この行をそのまま開発者に伝えてください", warn
        return [], None, warn      # 本当に空の再生リスト
    if shown != len(items):
        # ★お知らせの「N 本の利用できない動画」の N を読んで、**欠けた本数と一致するときだけ**許す。
        #   本文の有無だけで許すと、8本消えていても「お知らせがあるから正常」と素通りして
        #   「新しい録画はありません」で終わる = この仕組みが防ぐべき当の事故になる。
        hidden = 0
        if alert_msg:
            mh = re.search(r"([0-9,]+)\s*本の利用できない", alert_msg)
            if mh:
                hidden = int(mh.group(1).replace(",", ""))
        if hidden and shown - len(items) == hidden:
            warn = f"{alert_msg} (表示 {shown}本 / 解析 {len(items)}本 — 差は非表示分と一致)"
        else:
            return None, (f"解析が表示と食い違う (表示 {shown}本 / 解析 {len(items)}本"
                          + (f" / 非表示 {hidden}本" if hidden else "")
                          + ") — この行をそのまま開発者に伝えてください"), warn
    return items, None, warn


def _yt_host(url):
    """(解析済みURL, "youtu.be"|"youtube.com") を返す。YouTube 以外なら (None, None)。

    ★ホストの判定はここ1か所だけ。写すと片方だけ直されて
      `youtube.com.evil.com` のような別ホストを YouTube 扱いする穴になる。
    """
    try:
        u = urllib.parse.urlparse((url or "").strip())
    except ValueError:
        return None, None
    host = (u.hostname or "").lower()
    if host == "youtu.be" or host.endswith(".youtu.be"):
        return u, "youtu.be"
    if host == "youtube.com" or host.endswith(".youtube.com"):
        return u, "youtube.com"
    return None, None


def is_youtube_url(url):
    """URL が YouTube を指しているか (動画URLとは限らない: 再生リスト・チャンネルも真)。"""
    return _yt_host(url)[1] is not None


def video_id(url):
    """URLから動画IDを取り出す。★取りこぼすと既存動画を「新着」と誤認して二重登録する。

    class.html の ytId() が再生できる形は全部ここでも拾う (youtu.be / watch?v= / embed /
    shorts / live、v= がクエリの先頭に無い形、ホスト大文字)。読めなければ None。
    ★ここを「読める形」を増やす方向に広げるときは class.html の ytId() も一緒に見ること。
      生徒の画面で再生できない形 (http(s):// を省いた URL・IDだけ) をここだけで拾うと、
      壊れた録画行を「登録済み」と数えて**永久に直らない**状態を作る。
    """
    if not url:
        return None
    u, host = _yt_host(url)
    if host is None:
        return None
    if host == "youtu.be":
        cand = u.path.lstrip("/").split("/")[0]
        return cand if re.fullmatch(r"[A-Za-z0-9_-]{11}", cand) else None
    v = urllib.parse.parse_qs(u.query).get("v", [None])[0]
    if v and re.fullmatch(r"[A-Za-z0-9_-]{11}", v):
        return v
    m = re.match(r"/(?:embed|shorts|live|v)/([A-Za-z0-9_-]{11})", u.path)
    return m.group(1) if m else None


def provider_of(rec):
    """録画の実配信元。provider 列が空の古い行は URL の文字列から見分ける。

    ★空を無条件に "youtube" とみなすと、Google Drive 等のリンク録画が
      「URLから動画IDを読めない」に数えられ、**直しようのない理由で**割り当てが止まる。
    ★規則は server/main.py の _detect_video_provider と同じにする (録画行に provider を
      付けているのはあちら)。ずらすと、あちらが youtube と付ける行をこちらが link と
      見なし、その行が二重登録の見張りから丸ごと外れる。
    ★hostname で判定しない。http(s):// を省いた `youtu.be/xxxx` は hostname が空になり
      link に落ちる = 読めない YouTube URL が problems にも hazard にも出なくなる
      (2026-08-28 のデプロイ前レビューで見つけた退行)。
    """
    pv = (rec.provider or "").strip().lower()
    if pv:
        return pv
    u = (rec.video_url or "").lower()
    if "youtube.com" in u or "youtu.be" in u:
        return "youtube"
    if "vimeo.com" in u:
        return "vimeo"
    return "link"


# 「動画IDが在りようが無い」と断じてよい YouTube のページ (一覧・チャンネル等)。
_NOT_A_VIDEO_PATH = re.compile(
    r"^/(?:playlist|channel|c|user|feed|results|hashtag|about|premium|@[^/]*)(?:/|$)", re.I)


def may_hide_video_id(url):
    """読めない URL が動画IDを隠し持っている可能性があるか。

    ★既定は True (= 投入を止める)。False にしてよいのは「動画IDが在りようが無い」と
      **確信できる**形だけ。ここを緩めると、壊れた動画URLの行を「動画ではない」と誤って
      断じ、同じ動画をもう一度登録する (UNIQUE 制約が無いので取り返せない)。
    ★2026-08-28 のデプロイ前レビューで、この向きを一度間違えた: 「10〜12文字のトークンが
      無ければ動画ではない」と**壊れ方の側から**数えたため、貼り付けで空白が1つ混ざった
      `https://youtu.be/dQw4w9W gXcQ` (7+4文字に割れる) や、末尾に文字が続いて13文字に
      なった形が素通りした。壊れ方は無限にあるので数えきれない。**安全な形の側を数える**。
    """
    u = (url or "").strip()
    if not u:
        return False                      # 空URL = 隠しようがない
    pu, host = _yt_host(u)
    if host is None:
        return True                       # YouTube ですらない URL が youtube 扱い = 何が起きているか分からない
    if host == "youtu.be":
        return True                       # パスがそのまま動画ID。読めない = 壊れた動画URL
    if not _NOT_A_VIDEO_PATH.match(pu.path or "/"):
        return True                       # watch / embed / shorts / live … 動画ページかもしれない
    # 一覧ページでも v= が付いていれば壊れた動画URL
    return bool(urllib.parse.parse_qs(pu.query or "").get("v"))


def url_problem(url):
    """なぜ動画IDを読めないのかを一言で。★塾長がその場で直せる言葉にする。"""
    u = (url or "").strip()
    if not u:
        return "URL が空"
    if not re.match(r"^https?://", u, re.I):
        return "http(s):// で始まっていない"
    if not is_youtube_url(u):
        return "YouTube のURLではないのに provider が youtube になっている"
    if re.search(r"/playlist\b", _yt_host(u)[0].path or ""):
        return "再生リストのURL (動画のURLではない)"
    return "動画IDの形 (11文字) が見つからない"


def redact_url(url):
    """表示用に伏せた URL。★限定公開動画のIDはアクセス権そのものなので生では出さない。

    ホスト名までは出し、その先は**先頭4文字だけ**にする (動画IDの表示 vid[:4]… と同じ幅)。
    ★トークン単位で伏せる書き方はだめ。`/dQw4w9W%20gXcQ` のように記号で割れると
      短い破片が「伏せる長さ」に満たず素通りして、11文字のIDがほぼ復元できてしまう
      (2026-08-28 のデプロイ前レビュー)。どこがどう壊れているかは url_problem() が言葉で言う。
    """
    u = (url or "").strip()[:200]
    m = re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*://[^/?#]*)(.*)$", u, re.S)
    head, tail = (m.group(1), m.group(2)) if m else ("", u)
    return head + (tail if len(tail) <= 4 else tail[:4] + "…")


def resolve_year(mo, dy, today):
    """年の書かれていない (月, 日) を日付にする → (過去側の直近, 未来側の直近)。

    ★授業の日付は必ず「もう終わった回」なので**過去側の直近**を採る。
      「今日にいちばん近い年」を採っていた頃 (2026-08-28 まで) は、半年より古い日付が
      翌年に化けた: 日曜1限の '2月8日' が 2027-02-08 (月曜) と読まれ、正しい
      2026-02-08 (日曜) に「日付と再生リストの曜日が合わない — 手で確認する」と
      **嘘**を言っていた。半年より古い回は全部これに掛かるので、過去分の取り込みが
      丸ごと壊れる (しかも画面上は塾長の打ち間違いに見える)。
    ★未来側も返すのは、読めなかったときに「過去なら○/未来なら○」と両方見せるため。
      どちらか片方を勝手に選んで断定しない。
    """
    cands = []
    for y in (today.year - 1, today.year, today.year + 1):
        try:
            cands.append(datetime.date(y, mo, dy))
        except ValueError:
            continue                       # 2/29 など、その年に存在しない日付
    past = [d for d in cands if (d - today).days <= FUTURE_SLACK_DAYS]
    ahead = [d for d in cands if (d - today).days > FUTURE_SLACK_DAYS]
    return (max(past) if past else None), (min(ahead) if ahead else None)


def date_label(raw, day_index, today):
    """動画名から日付ラベルを作る → (ラベル, 問題点)。**推測はしない**。

    '8/17'・'8.３'・'８・６'・'8月17日' は拾う。'2026/8/17' のような年つきは
    先頭2桁を月と誤読する (実測で '26/8' になった) ので弾く。
    ★曜日が再生リストと違う / 未来 / 1年近く離れている ものは返さない。
      年は書かれないので、読みが1年近く離れると打ち間違いと区別が付かない (MAX_AGE_DAYS)。
    ★「前回のタイトルをコピペして日付を直し忘れる」打ち間違いは 7 の倍数のズレなので、
      曜日検算でも日数の上限でも捕まらない。それを捕まえるのは build_plan の
      **同じ授業に同じ日付ラベル**検査。ここで日数を絞って代用しようとしない
      (絞ると正しい過去分の取り込みだけが死ぬ)。
    """
    n = unicodedata.normalize("NFKC", raw or "")
    if re.search(r"(?<!\d)(19|20)\d{2}\s*[/.\-年]", n):
        return None, f"年つきの日付は読み取らない ({raw!r})"
    found = re.findall(r"(?<!\d)(\d{1,2})\s*[/.・\-月]\s*(\d{1,2})(?!\d)", n)
    cand = list(dict.fromkeys((int(a), int(b)) for a, b in found))
    if not cand:
        return None, f"動画名から日付を読めない ({raw!r})"
    if len(cand) > 1:
        # 「1.5倍速 英語 8/17」のように候補が複数あると先頭が勝って黙って誤る → 人に回す
        return None, f"日付の候補が複数ある ({raw!r} → {['%d/%d' % c for c in cand]})"
    mo, dy = cand[0]
    if not (1 <= mo <= 12 and 1 <= dy <= 31):
        return None, f"日付として成立しない ({raw!r} → {mo}/{dy})"
    best, ahead = resolve_year(mo, dy, today)
    if best is None:
        if ahead is None:
            return None, f"存在しない日付 ({raw!r} → {mo}/{dy})"
        return None, f"未来の日付 ({raw!r} → {ahead}) — 動画名の打ち間違いを疑う"
    if (today - best).days > MAX_AGE_DAYS:
        # ★過去側の読みが1年近く前 = 未来側の読みと区別が付かない。推測せず人に回す。
        #   近いほうを先に言う (「9/6」を「305日より離れた日付」とだけ言われても意味が通らない)。
        if ahead and (ahead - today).days < (today - best).days:
            return None, (f"未来の日付 ({raw!r} → {ahead}) — 動画名の打ち間違いを疑う "
                          f"(過去と読むなら {best} = {(today - best).days}日前)")
        return None, (f"{MAX_AGE_DAYS}日より離れた日付 ({raw!r} → 過去なら {best}"
                      + (f" / 未来なら {ahead}" if ahead else "")
                      + ") — 動画名の打ち間違いを疑う")
    if best > today:                       # 猶予 (FUTURE_SLACK_DAYS) の中の未来
        return None, f"未来の日付 ({raw!r} → {best}) — 動画名の打ち間違いを疑う"
    if best.weekday() != day_index:
        return None, (f"日付と再生リストの曜日が合わない ({raw!r} → {best} は"
                      f"{DAY_LABEL[best.weekday()]}曜 / 再生リストは{DAY_LABEL[day_index]}曜) — 手で確認する")
    return f"{mo}/{dy}", None


def build_plan(today, playlists, sessions, recordings, last_rec, get=None, progress=None):
    """DB から読んだ材料 → 「何をどこに登録するか」の計画と、確認が要る項目の一覧。

    引数 (全部 呼び出し側が DB から読む。この関数は DB に触らない):
      today      : 判定基準日 (JST。today_jst())
      playlists  : [(playlist_id, name)] … admin_youtube_playlists の**全行**(名前なしも含む)
      sessions   : [(id, title)]        … class_sessions の **is_published=1 のみ**
      recordings : [(session_id, video_url, provider, title, rec_id)] … class_recordings の全行
                   (Recording の並び。★列を減らすと TypeError で止まる = 黙って劣化しない)
      last_rec   : {session_id: 最終登録日時} … 配布が止まっているクラスの検知用
      get        : fetch_playlist に渡す取得口 (試験用の差し替え)
      progress   : 1行できるたびに呼ばれる (CLI が進捗を出すため)。API は None。

    返り値は「印字用の文字列」ではなく**構造**。CLI と API が同じ判断を別の見た目で出せる。
    ★動画IDは planned にだけ生で入る (登録に要るため)。表示用の文字列では先頭4文字に伏せる
      (限定公開動画のIDはアクセス権そのもの)。API はこの planned をブラウザに返さない。
    """
    say = progress or (lambda _line: None)
    named = [(p, n) for p, n in playlists if (n or "").strip()]
    recs = [Recording(*r) for r in recordings]
    session_title = dict(sessions)
    urls = [r.video_url for r in recs]
    # ★(授業, 動画) の組で持つ。動画IDだけで「登録済」と判定すると、**別のクラスに
    #   登録された動画**までこのクラスの登録済みに化け、そのクラスの生徒には1本も
    #   見えていないのに「新着なし」で緑になる (録画は受講クラス限定で配信されるため)。
    known_pairs = {(r.session_id, video_id(r.video_url)) for r in recs
                   if video_id(r.video_url) and r.session_id is not None}
    # session_id が NULL の録画は「全員向け」として全塾生に配信される (server/main.py の
    # loose_recordings)。見えていないわけではないので、誤登録として騒がない。
    loose_vids = {video_id(r.video_url) for r in recs
                  if video_id(r.video_url) and r.session_id is None}
    db_vids = {v for v in (video_id(u) for u in urls) if v}
    # ★provider=vimeo/link は正当な録画。YouTube 以外を「読めないURL」に数えると、
    #   1件あるだけで --apply が恒久的に止まり、直しようのない指示が出る。
    #   provider 列が空の古い行は URL から見分ける (provider_of)。
    bad_urls = [r for r in recs if provider_of(r) == "youtube" and not video_id(r.video_url)]
    # ★**登録を止めている当の行を先に出す**。DB の行順 (SELECT に ORDER BY が無いので
    #   Postgres では実行ごとに変わる) のまま5件で切ると、止めている行が6件目以降に落ちて
    #   「登録は止めません」と書かれた5件だけが並ぶ。塾長には「1件あるので登録しません」と
    #   言いながら、その1件は画面に出ない = このコミットが直そうとした事故の再発になる。
    bad_urls.sort(key=lambda r: (not may_hide_video_id(r.video_url), r.rec_id or 0))

    # ★「同じ授業に同じ日付ラベル」を作らないための台帳 = 前回のタイトルをコピペして
    #   日付を直し忘れる打ち間違い (7の倍数のズレ) の唯一の見張り。曜日検算も日数の上限も
    #   このズレは捕まえられない。自動割り当てが書く title は "M/D" なので、その形の
    #   既存タイトルだけを見る (塾長が手で付けた題名は無関係なので巻き込まない)。
    #   ★"08/23" のような表記ゆれを "8/23" に正規化して入れる (生成する label は
    #     f"{mo}/{dy}" = 前ゼロ無しなので、そのまま入れると照合が外れる)。
    db_labels, run_labels = {}, {}     # DB に既に在る分 / この実行で計画した分 (言い方を変える)
    for r in recs:
        m0 = re.fullmatch(r"(\d{1,2})/(\d{1,2})", (r.title or "").strip())
        if r.session_id is not None and m0:
            db_labels.setdefault(r.session_id, set()).add(f"{int(m0.group(1))}/{int(m0.group(2))}")

    rep = {
        "playlist_total": len(playlists), "playlist_named": len(named),
        "sessions_total": len(sessions), "recordings_total": len(urls),
        "recordings_with_vid": len(db_vids),
        "rows": [], "planned": [], "problems": [], "notes": [],
        "blocking": 0, "hazard": 0, "fetched": 0, "skipped_name": 0,
        "covered": 0, "uncovered": [], "no_playlist": [],
    }
    problems, notes = rep["problems"], rep["notes"]
    # ★「走査」は実際に YouTube を見に行った本数。名前が読めずに飛ばしたものを
    #   走査に数えると「見ていないものを見たと言う」ことになる。
    # ★「実際に YouTube を見に行けた授業」だけを数える。対応表があった時点で数えると、
    #   全リストが取得失敗しても「15/15」と出て、出力中で最も安心させる数字が嘘になる。
    covered_sids, attempted_sids = set(), set()

    # ★読めない URL は**どの録画か**を必ず示す。件数だけ出していた頃 (2026-08-28 まで) は
    #   「1件ある」としか分からず、探しようが無いまま割り当てが恒久的に止まっていた
    #   (これは hazard = --allow-partial でも免除しないので、全クラスの配布が止まる)。
    for i, r in enumerate(bad_urls):
        risky = may_hide_video_id(r.video_url)
        if risky:
            # 自分で「二重登録の恐れ」と書いておいて素通りさせない (UNIQUE 制約が無く取り返せない損害)。
            # ★数えるのは**全件**。表示を5件に絞るのに合わせて数えるのも絞ると、
            #   6件目以降が危ない URL でも登録が通ってしまう。
            rep["blocking"] += 1
            rep["hazard"] += 1
        if i >= 5:
            continue
        if r.session_id is None:
            where = "授業に紐づいていない録画 (全員向け)"
            fix = ("授業に紐づいていないので CEO 画面には出ません。"
                   "この行をそのまま開発担当に伝えて消してもらう")
        else:
            where = f"授業「{session_title.get(r.session_id, f'session {r.session_id}')}」"
            fix = "CEO の授業詳細でこの録画を削除して、https://youtu.be/〜 の形で登録し直す"
        problems.append(
            f"録画 #{r.rec_id} {where} タイトル {(r.title or '')[:24]!r} "
            f"{redact_url(r.video_url)} — URL から動画IDを読めない ({url_problem(r.video_url)})。"
            + ("同じ動画を新着と誤認して二重登録する恐れがあるので、登録を止めています。"
               if risky else "動画のURLではないので二重登録の恐れは無く、登録は止めません。")
            + fix)
    _hidden = bad_urls[5:]
    if _hidden:
        _hidden_risky = sum(1 for r in _hidden if may_hide_video_id(r.video_url))
        problems.append(f"…ほかに URL から動画IDを読めない録画が {len(_hidden)}件あります"
                        + (f" (うち {_hidden_risky}件は登録を止める行)" if _hidden_risky
                           else " (どれも登録は止めていません)")
                        + " — 上の5件を直してからもう一度「① 確認する」を押すと残りが出ます")

    for pid, name in named:
        s = slot_of(name)
        if not s:
            # ★blocking にしない。名前が読めない再生リスト = 授業用ではない、が普通
            #   (旧「以前の再生リスト」16件がこれ)。ここで投入を止めると、名前を1つ
            #   打ち間違えただけで**15クラス全部の配布が止まる**。
            #   配布漏れは下の「授業側カバレッジ」で必ず捕まるので、そちらに任せる。
            # ★notes(参考)に出す。授業用でない再生リスト (講義まとめ等) に名前を付けると
            #   毎回 ⚠ が並び、同じ一覧に出る STALE 警告 (配布が止まっている合図) が埋もれる。
            rep["skipped_name"] += 1
            notes.append(f"{name}: 名前から曜日+限を読めないので自動割り当ての対象外 "
                         f"(授業用なら「月曜1限 …」のように曜日と限を先頭に入れる)")
            continue
        day_index, raw_slot, slot = s
        matches = [(i, t) for i, t in sessions if t.startswith(slot)]
        legacy = None
        if not matches and slot in LEGACY_SLOT:
            # DB がまだ旧ラベル = 移送前。ここで止めると他14クラスの配布まで巻き添えになる。
            legacy = LEGACY_SLOT[slot]
            matches = [(i, t) for i, t in sessions if t.startswith(legacy)]
            if matches:
                notes.append(f"{raw_slot}: 授業名が旧ラベル ({legacy}…) のまま — "
                             f"scripts/class_timetable/rename_thu3_to_fri3.py --apply を実行すること")
            else:
                legacy = None
        if len(matches) != 1:
            # ★0件のとき「CEO で授業を作る」と案内してはいけない。旧ラベルの授業が残っていると、
            #   その通りに作った瞬間に同名の授業が2件になり、以後ずっと「判別できない」で止まる。
            _orphan = [t for _, t in sessions if t.startswith(LEGACY_SLOT.get(slot, "\0"))]
            problems.append(
                f"{raw_slot}: 公開中の授業が{len(matches)}件マッチ"
                + (f" — 旧ラベルの授業 ({', '.join(_orphan)}) が残っている。**CEO で授業を作らないこと**。"
                   f"先に scripts/class_timetable/rename_thu3_to_fri3.py --apply を実行する"
                   if (not matches and _orphan)
                   else " — 授業が無いか非公開。CEO で授業を作る/公開する" if not matches
                   else f" — {[t for _, t in matches]} のどれか判別できない"))
            rep["blocking"] += 1
            continue
        sid, stitle = matches[0]
        attempted_sids.add(sid)
        _note = ("  ※授業名が旧ラベルのまま (移送が要る)" if legacy
                 else "  ※再生リスト名と授業名が違うのは設定どおり" if raw_slot != slot else "")
        items, fatal, warn = fetch_playlist(pid, get=get)
        if warn:
            # YouTube の INFO (「1本の利用できない動画が非表示」等) は正常状態。
            # ★これを problems に積むと、動画を1本消しただけで毎回 ⚠ が出続け、
            #   本物の警告まで無視されるようになる (警告疲れ)。参考情報として分ける。
            notes.append(f"{raw_slot}: {warn}")
        if items is None:
            problems.append(f"{raw_slot}: {fatal}")
            rep["blocking"] += 1
            line = f"  {raw_slot:<7} 取得できず  [{stitle}]{_note}"
            rep["rows"].append({"slot": raw_slot, "session": stitle, "ok": False,
                                "detail": fatal, "line": line})
            say(line)
            continue
        rep["fetched"] += 1
        covered_sids.add(sid)   # ★取得できた授業だけを「見に行けた」と数える
        if fatal:      # items はあるが不完全 (1ページ上限)
            problems.append(f"{raw_slot}: {fatal}")
            rep["blocking"] += 1
        fresh = skipped = known = 0
        old_labels = []
        for vid, vtitle in items:
            if (sid, vid) in known_pairs:
                known += 1
                continue
            if vid in loose_vids:
                known += 1          # 授業に紐づかない=全塾生に配信済み。配布漏れではない
                continue
            if vid in db_vids:
                # ★DB では別の授業に登録済み。このクラスの生徒には見えていない
                #   (録画は受講クラス限定で配信される)。勝手に足さずに知らせる。
                #   ※この実行で他クラスに計画しただけの分はここに来ない (合同授業を壊さないため)。
                problems.append(f"{raw_slot}: 動画 {vid[:4]}… ({vtitle!r}) が別の授業に登録されている "
                                f"= このクラスの生徒には見えていない。合同授業ならこのクラスにも "
                                f"手で追加し、取り違えなら CEO 画面で登録先を直す")
                skipped += 1
                continue
            label, why = date_label(vtitle, day_index, today)
            if not label:
                problems.append(f"{raw_slot}: {why} — 動画 {vid[:4]}… は CEO 画面から手で登録する")
                skipped += 1
                continue
            # ★前回のタイトルをコピペして日付を直し忘れた形。ズレが7の倍数だと曜日検算を
            #   すり抜けるので、ここが唯一の見張り。同じ日に2本ある授業も同じ道で人に回す
            #   (どちらが何限の回か機械には決められない)。
            # ★「既に登録済み」と「同じ再生リストに2本」は塾長のやることが違うので言い分ける。
            #   探しに行っても見つからない案内をしない。
            if label in db_labels.get(sid, ()):
                problems.append(f"{raw_slot}: このクラスには既に {label} の録画が登録されている "
                                f"({vtitle!r} / 動画 {vid[:4]}…) — 前回のタイトルの日付を直し忘れて "
                                f"いないか確かめて、正しければ CEO 画面から手で登録する")
                skipped += 1
                continue
            if label in run_labels.get(sid, ()):
                problems.append(f"{raw_slot}: 同じ再生リストに {label} の回が2本ある "
                                f"({vtitle!r} / 動画 {vid[:4]}…) — 今回登録するのは先に見つかった1本だけ。"
                                f"日付の打ち間違いでなければ、この1本を CEO 画面から手で登録する")
                skipped += 1
                continue
            if not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
                # 書いた URL は次回必ず video_id() で読み戻せる、が全体の前提。
                problems.append(f"{raw_slot}: 動画IDの形が想定外 — この行をそのまま開発者に伝えてください")
                rep["blocking"] += 1
                rep["hazard"] += 1
                skipped += 1
                continue
            known_pairs.add((sid, vid))   # 同じ授業に二重に積まない。
            #   ★db_vids には足さない。足すと、同じ動画を2クラスに配る合同授業のとき
            #     2クラス目が「別の授業に登録されている」と**嘘**を言い、しかも
            #     「登録先を直す」に従うと1クラス目から剥がすことになる。
            run_labels.setdefault(sid, set()).add(label)   # 同じ実行で同じ日付を二度作らない
            rep["planned"].append({"session_id": sid, "session_title": stitle,
                                   "slot": raw_slot, "label": label, "video_id": vid})
            fresh += 1
            _d0, _ = resolve_year(int(label.split("/")[0]), int(label.split("/")[1]), today)
            if _d0 and (today - _d0).days > OLD_LABEL_DAYS:
                old_labels.append(label)
        if old_labels:
            # ★古い回を弾かずに登録する代わりに、必ず知らせる。MAX_AGE_DAYS を緩めた分の
            #   人手の見張りはここ**だけ**なので、「対応は不要」と読める書き方にしない。
            #   過去分の取り込みなら正常。毎週の運用でこれが出たら日付の打ち間違い。
            notes.append(f"👀 {raw_slot}: {OLD_LABEL_DAYS}日より古い回を {len(old_labels)}本 登録します "
                         f"({'・'.join(old_labels[:8])}{' ほか' if len(old_labels) > 8 else ''})。"
                         f"過去分をまとめて取り込んだのなら正常です (日付は再生リストの曜日と一致)。"
                         f"心当たりが無ければ、登録する前にこの日付が合っているか確かめてください")
        _last = last_rec.get(sid)
        _last_s = "録画なし"
        if not _last and fresh == 0:
            # ★いちばん重い状態 (一度も配布されていない) が、STALE 判定の外に落ちて
            #   無警告になっていた。STALE は「最新録画日」が要るので、録画0本のクラスには
            #   時間の見張りが一切効かない = 新設クラスは永久に緑のままになる。
            problems.append(f"{raw_slot}: このクラスの録画が1本も登録されていない "
                            f"(再生リストは {len(items)}本) — 講師が別の再生リストに上げていないか、"
                            f"別のクラスに登録されていないか確認する (新設で初回前なら無視してよい)")
        if _last:
            _d = _last.date() if hasattr(_last, "date") else _last
            if isinstance(_d, str):
                # ★ドライバによっては TIMESTAMP が文字列で返る。ここで諦めると
                #   録画があるクラスに「録画なし」と出し、配布が止まっていても
                #   STALE 警告が一切鳴らない (時間による見張りが丸ごと死ぬ)。
                try:
                    _d = datetime.date.fromisoformat(_d[:10])
                except ValueError:
                    _d = None
            if isinstance(_d, datetime.date):
                _age = (today - _d).days
                _last_s = f"最新 {_d.month}/{_d.day} ({_age}日前)"
                if fresh == 0 and _age > STALE_DAYS:
                    problems.append(f"{raw_slot}: 最新の録画が {_age}日前 ({_d}) で止まっている — "
                                    f"再生リストを作り直して名前を付け忘れていないか / "
                                    f"アップロード漏れが無いか確認する (長期休みなら無視してよい)")
        line = (f"  {raw_slot:<7} {len(items):>3}本  新着 {fresh} / 登録済 {known} / 保留 {skipped}  "
                f"{_last_s:<18} [{stitle}]{_note}")
        rep["rows"].append({"slot": raw_slot, "session": stitle, "ok": True, "items": len(items),
                            "fresh": fresh, "known": known, "skipped": skipped,
                            "last": _last_s, "line": line})
        say(line)

    # ★授業側のカバレッジ。ここを印字だけにすると「1本も見に行っていない」が
    #   「新着なし・exit 0」と**完全に同じ見た目**になる。
    #   見に行けなかった授業は必ず problems に積んで投入も止める。
    rep["covered"] = len(covered_sids)
    rep["uncovered"] = [t for i, t in sessions if i not in covered_sids]
    rep["no_playlist"] = [t for i, t in sessions if i not in attempted_sids]
    if rep["no_playlist"]:
        # ★対応する再生リストが無い授業。取得失敗はすでに上で1件ずつ数えているので二重計上しない。
        problems.append(f"{len(rep['no_playlist'])}件の授業に対応する再生リストが無い "
                        f"({', '.join(rep['no_playlist'])}) = この授業の配布漏れは検出できていない")
        rep["blocking"] += 1
    elif rep["uncovered"]:
        problems.append(f"{len(rep['uncovered'])}件の授業は再生リストを見に行けなかった = 配布漏れは検出できていない")
    return rep


def recording_url(vid):
    """登録する video_url。★次回 video_id() で必ず読み戻せる形にする (二重登録の防止)。"""
    return f"https://youtu.be/{vid}"
