#!/usr/bin/env python3
"""授業録画(YouTube 限定公開)を再生リストから拾って class_recordings に割り当てる。

  railway run -s Postgres python3 scripts/class_recordings/assign_from_playlists.py                 # dry-run
  railway run -s Postgres python3 scripts/class_recordings/assign_from_playlists.py --apply         # 投入
  ... --apply --allow-partial   # 取得できない再生リストがあっても、取れた分だけ投入する

終了コード: 0=確認事項なし / 1=確認事項あり(要確認の一覧を印字) / 2=投入を中止した・引数エラー / 3=異常終了

★このリポジトリは PUBLIC。再生リストID・動画IDは**絶対にここへ書かない**
  (2026-08-06 に平文16IDを公開していた youtube-playlists.md を削除したが、
   git履歴からは今も取り出せる = 実効的な対処は YouTube 側で再生リストを非公開にすること)。
  再生リストは DB の admin_youtube_playlists からだけ読む。端末出力でも動画IDは伏せる。
★動画のタイトルは信用しない。「どの再生リストに入っているか」が曜日+限の正。
  (2026-08-06: 火曜3限の動画名が「8.３」だったが正は火曜=8/4)
  日付ラベルだけは動画名から取らざるを得ないので、**再生リストの曜日と突き合わせて**検算する。
★「取得できなかった」を「0本(新着なし)」と言わない。ここを間違えると
  配布漏れを「配布済み」と誤報告する。判定は下の fetch_playlist() を参照。

★既知の限界 (2026-08-18):
  - class_recordings に UNIQUE 制約が無いので、**2つの端末で同時に --apply すると重複する**。
    1人が順に実行する運用なら安全 (2回目以降は登録済みとして弾く)。
  - 再生リストの1ページ目 (先頭100本) しか読まない。100本に達したら警告して投入を止める。
"""
import datetime
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.parse

# ★psycopg は main() の中で import する。トップレベルに置くと、DBを使わない
#   判定表ゲート (check_assign_logic.py) が psycopg 未導入の CI で ModuleNotFoundError で
#   落ち、「CRASH = 検査していない」状態になる (CI は sympy/fonttools/pymupdf/numpy しか入れない)。

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")

# 再生リスト名 → class_sessions.title の先頭ラベル。
# ★時間割とのズレはここに明示する: 「金曜3時間目」の再生リストは時間割に無く、
#   逆に木曜3限は再生リストが無い (2026-08-07 にこの対応で割り当て済み)。
#   ズレていても**日付の検算は再生リスト側の曜日**で行う (動画の実収録日は金曜のため)。
SLOT_OVERRIDE = {"金曜3限": "木曜3限", "日曜1限": "日曜"}  # 日曜は1コマだけで title が「日曜 高校国語」

DAY = {"月": 0, "火": 1, "水": 2, "木": 3, "金": 4, "土": 5, "日": 6}
DAY_LABEL = {v: k for k, v in DAY.items()}
PAGE_LIMIT = 100          # 1ページに載る上限。継続トークンは追わない。
MAX_AGE_DAYS = 120        # これより古い日付ラベルは打ち間違いを疑って手作業に回す
_COMMITTED = False        # commit 済みか (中断・異常終了時の文言を事実に合わせるため)


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


def fetch_playlist(pid):
    """再生リストを読む → (items, fatal, warn)。items が None なら**中身を信用しない**。

    ★実測(2026-08-18)で確かめた見分け方:
      - 削除/存在しないID → HTTP 200 + ytInitialData あり + alerts(type=ERROR) + contents 無し
        = 素朴に解析すると「0本」に化ける。ここを fatal にするのがこの関数の主目的。
      - 本当に空 → contents あり・alerts 無し・本数表記なし・「この再生リストには動画がありません」あり
      - 正常 → 「N 本の動画」表記があるので解析本数と突き合わせる。食い違えば構造変更 (fatal)。
    """
    r = subprocess.run(["curl", "-s", "-m", "30", "-A", UA, "-H", "Accept-Language: ja",
                        f"https://www.youtube.com/playlist?list={pid}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None, ("取得に時間がかかりすぎた — もう一度実行してください" if r.returncode == 28 else f"YouTube に接続できない (curl exit {r.returncode}) — ネット接続を確認してもう一度実行してください"), None
    m = re.search(r"ytInitialData\s*=\s*(\{.*?\});\s*</script>", r.stdout, re.S)
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
        #   「新しい録画はありません」で終わる = このスクリプトが防ぐべき当の事故になる。
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


def video_id(url):
    """URLから動画IDを取り出す。★取りこぼすと既存動画を「新着」と誤認して二重登録する。

    class.html の ytId() が再生できる形は全部ここでも拾う (youtu.be / watch?v= / embed /
    shorts / live、v= がクエリの先頭に無い形、ホスト大文字)。読めなければ None。
    """
    if not url:
        return None
    try:
        u = urllib.parse.urlparse(url.strip())
    except ValueError:
        return None
    host = (u.hostname or "").lower()
    if not (host == "youtu.be" or host.endswith(".youtu.be")
            or host == "youtube.com" or host.endswith(".youtube.com")):
        return None
    if host.endswith("youtu.be"):
        cand = u.path.lstrip("/").split("/")[0]
        return cand if re.fullmatch(r"[A-Za-z0-9_-]{11}", cand) else None
    v = urllib.parse.parse_qs(u.query).get("v", [None])[0]
    if v and re.fullmatch(r"[A-Za-z0-9_-]{11}", v):
        return v
    m = re.match(r"/(?:embed|shorts|live|v)/([A-Za-z0-9_-]{11})", u.path)
    return m.group(1) if m else None


def date_label(raw, day_index, today):
    """動画名から日付ラベルを作る → (ラベル, 問題点)。**推測はしない**。

    '8/17'・'8.３'・'８・６'・'8月17日' は拾う。'2026/8/17' のような年つきは
    先頭2桁を月と誤読する (実測で '26/8' になった) ので弾く。
    ★曜日が再生リストと違う / 未来 / 古すぎる ものは返さない。前回のタイトルを
      コピペして日付を直し忘れる打ち間違いは 7 の倍数のズレになりやすく、
      曜日検算だけでは捕まらないため上限・下限も見る。
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
    # 年は書かれないので、今日にいちばん近い年を採る (年またぎ対策)
    best = None
    for y in (today.year - 1, today.year, today.year + 1):
        try:
            d = datetime.date(y, mo, dy)
        except ValueError:
            continue
        if best is None or abs((d - today).days) < abs((best - today).days):
            best = d
    if best is None:
        return None, f"存在しない日付 ({raw!r} → {mo}/{dy})"
    if best.weekday() != day_index:
        return None, (f"日付と再生リストの曜日が合わない ({raw!r} → {best} は"
                      f"{DAY_LABEL[best.weekday()]}曜 / 再生リストは{DAY_LABEL[day_index]}曜) — 手で確認する")
    if best > today:
        return None, f"未来の日付 ({raw!r} → {best}) — 動画名の打ち間違いを疑う"
    if (today - best).days > MAX_AGE_DAYS:
        return None, f"{MAX_AGE_DAYS}日より古い日付 ({raw!r} → {best}) — 動画名の打ち間違いを疑う"
    return f"{mo}/{dy}", None


def main():
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print(__doc__)
        return 0
    apply_mode = "--apply" in args
    allow_partial = "--allow-partial" in args
    unknown = [a for a in args if a not in ("--apply", "--allow-partial")]
    if unknown:
        print(f"知らない引数: {unknown}  (使えるのは --apply / --allow-partial / --help)")
        return 2
    if not os.environ.get("DATABASE_PUBLIC_URL"):
        print(f"DATABASE_PUBLIC_URL が無い。`railway run -s Postgres python3 {sys.argv[0]}` で実行する。")
        return 2

    import psycopg   # ここで初めて要る (判定表ゲートは DB を使わないので import させない)

    today = datetime.date.today()
    conn = psycopg.connect(os.environ["DATABASE_PUBLIC_URL"])
    try:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("select playlist_id, name from admin_youtube_playlists order by sort_order, id")
        rows = cur.fetchall()
        named = [(p, n) for p, n in rows if (n or "").strip()]
        # ★公開中の授業だけを相手にする。非公開セッションに入れると「投入した」と出るのに誰にも見えない。
        cur.execute("select id, title from class_sessions where is_published = 1 order by id")
        sessions = cur.fetchall()
        cur.execute("select video_url, coalesce(provider, '') from class_recordings")
        recs = cur.fetchall()
        urls = [u for u, _ in recs]
        known_ids = {v for v in (video_id(u) for u in urls) if v}
        # ★provider=vimeo/link は正当な録画。YouTube 以外を「読めないURL」に数えると、
        #   1件あるだけで --apply が恒久的に止まり、直しようのない指示が出る。
        unparsed = sum(1 for u, pv in recs if (pv or "youtube") == "youtube" and not video_id(u))

        print(f"再生リスト {len(rows)}件中 {len(named)}件を走査 (名前未登録の{len(rows) - len(named)}件は対象外)")
        print(f"公開中の授業 {len(sessions)}件 / 登録済み録画 {len(urls)}件 (動画IDを読めた {len(known_ids)}件)")

        planned, problems, notes, blocking = [], [], [], 0
        # ★「実際に YouTube を見に行けた授業」だけを数える。対応表があった時点で数えると、
        #   全リストが取得失敗しても「15/15」と出て、出力中で最も安心させる数字が嘘になる。
        covered_sids = set()
        attempted_sids = set()   # 再生リストが対応していた授業 (取得の成否は問わない)
        if unparsed:
            # 自分で「二重登録の恐れ」と書いておいて素通りさせない (UNIQUE 制約が無く取り返せない損害)
            problems.append(f"登録済み録画のうち {unparsed}件の URL から動画IDを読めない "
                            f"= 同じ動画を新着と誤認して二重登録する恐れ。CEO 画面でその録画のURLを "
                            f"https://youtu.be/〜 の形に直してから実行する")
            blocking += 1
        for pid, name in named:
            s = slot_of(name)
            if not s:
                problems.append(f"{name}: 再生リスト名から曜日+限を読めない")
                blocking += 1
                continue
            day_index, raw_slot, slot = s
            matches = [(i, t) for i, t in sessions if t.startswith(slot)]
            if len(matches) != 1:
                problems.append(
                    f"{raw_slot}: 公開中の授業が{len(matches)}件マッチ"
                    + (" — 授業が無いか非公開。CEO で授業を作る/公開する" if not matches
                       else f" — {[t for _, t in matches]} のどれか判別できない"))
                blocking += 1
                continue
            sid, stitle = matches[0]
            attempted_sids.add(sid)
            _note = "  ※再生リスト名と授業名が違うのは設定どおり" if raw_slot != slot else ""
            items, fatal, warn = fetch_playlist(pid)
            if warn:
                # YouTube の INFO (「1本の利用できない動画が非表示」等) は正常状態。
                # ★これを problems に積むと、動画を1本消しただけで毎回 ⚠ が出続け、
                #   本物の警告まで無視されるようになる (警告疲れ)。参考情報として分ける。
                notes.append(f"{raw_slot}: {warn}")
            if items is None:
                problems.append(f"{raw_slot}: {fatal}")
                blocking += 1
                print(f"  {raw_slot:<7} 取得できず  [{stitle}]{_note}")
                continue
            covered_sids.add(sid)   # ★取得できた授業だけを「見に行けた」と数える
            if fatal:      # items はあるが不完全 (1ページ上限)
                problems.append(f"{raw_slot}: {fatal}")
                blocking += 1
            fresh = skipped = known = 0
            for vid, vtitle in items:
                if vid in known_ids:
                    known += 1
                    continue
                label, why = date_label(vtitle, day_index, today)
                if not label:
                    problems.append(f"{raw_slot}: {why} — 動画 {vid[:4]}… は CEO 画面から手で登録する")
                    skipped += 1
                    continue
                if not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
                    # 書いた URL は次回必ず video_id() で読み戻せる、が全体の前提。
                    problems.append(f"{raw_slot}: 動画IDの形が想定外 — この行をそのまま開発者に伝えてください")
                    blocking += 1
                    skipped += 1
                    continue
                known_ids.add(vid)  # ★同じ動画が2つの再生リストに居ても二重に積まない
                planned.append((sid, stitle, raw_slot, label, vid))
                fresh += 1
            print(f"  {raw_slot:<7} {len(items):>3}本  新着 {fresh} / 登録済 {known} / 保留 {skipped}  [{stitle}]{_note}")

        # ★授業側のカバレッジ。ここを印字だけにすると「1本も見に行っていない」が
        #   「新着なし・exit 0」と**完全に同じ見た目**になる (前回の指摘が授業軸で再発していた)。
        #   見に行けなかった授業は必ず problems に積んで投入も止める。
        uncovered = [t for i, t in sessions if i not in covered_sids]
        no_playlist = [t for i, t in sessions if i not in attempted_sids]
        print(f"\nYouTube を見に行けた授業: {len(covered_sids)}/{len(sessions)}")
        if uncovered:
            print(f"  見に行けなかった授業 ({len(uncovered)}件): {', '.join(uncovered)}")
        if no_playlist:
            # ★対応する再生リストが無い授業。取得失敗はすでに上で1件ずつ数えているので二重計上しない。
            problems.append(f"{len(no_playlist)}件の授業に対応する再生リストが無い "
                            f"({', '.join(no_playlist)}) = この授業の配布漏れは検出できていない")
            blocking += 1
        elif uncovered:
            problems.append(f"{len(uncovered)}件の授業は再生リストを見に行けなかった = 配布漏れは検出できていない")

        if notes:
            print("\n(参考) YouTube からのお知らせ:")
            for n in notes:
                print(f"   - {n}")
        if problems:
            print("\n⚠ 確認が要るもの:")
            for p in problems:
                print(f"   - {p}")

        def _finish(code, applied=0):
            if problems:
                if blocking and applied:
                    tail = f" うち {blocking}件は今回見に行けなかった分 (配布漏れがあっても検出できていない)。"
                elif blocking:
                    tail = f" うち {blocking}件は投入を止める項目 (--apply しても1件も登録されない)。"
                else:
                    tail = ""
                print(f"\n⚠ 未解決 {len(problems)}件 — 上の一覧を確認すること。" + tail)
            return code

        if not planned:
            print("\n新しい録画はありません。" if not problems else "\n投入できる新着はありません。")
            return _finish(1 if problems else 0)

        print(f"\n{'投入する' if apply_mode else 'dry-run — 投入せず'} {len(planned)}件:")
        for sid, stitle, raw_slot, label, vid in planned:
            print(f"   {raw_slot:<7} {label:>5}  動画 {vid[:4]}…  → session {sid} {stitle}")
        if not apply_mode:
            if blocking:
                print(f"\n⚠ このままでは --apply しても **1件も登録されません** (投入を止める項目が {blocking}件)。"
                      "\n   上の一覧を直してから再実行してください。")
            else:
                print("\n投入するなら --apply を付けて再実行。")
            return _finish(1 if problems else 0)
        if blocking and not allow_partial:
            print(f"\n❌ 見落としの恐れがある項目が {blocking}件あるので投入しない。"
                  "\n   直してから再実行する。承知のうえで取れた分だけ入れるなら --allow-partial。")
            return _finish(2)

        conn.autocommit = False
        global _COMMITTED
        try:
            for sid, stitle, raw_slot, label, vid in planned:
                cur.execute("insert into class_recordings (session_id, title, video_url, provider, is_published) "
                            "values (%s,%s,%s,'youtube',1)", (sid, label, f"https://youtu.be/{vid}"))
            conn.commit()
            _COMMITTED = True
        except Exception as e:
            # ★接続が切れているときは rollback 自体が例外を投げる。ここで落ちると
            #   「何も登録していない」という肝心の一文が出ずに生のトレースバックだけが残る。
            try:
                conn.rollback()
            except Exception:
                pass
            # ★例外文をそのまま出さない。Postgres の DETAIL は失敗行の URL (=動画ID) を平文で載せる。
            print(f"\n❌ 投入に失敗した ({type(e).__name__})。ほぼ確実に**1件も登録されていない**が、"
                  "通信が切れた場合は登録済みの可能性もある。"
                  "\n   CEO 画面の「授業録画」を確認してから、もう一度実行してください "
                  "(登録済みなら次回は「登録済」として飛ばします)。")
            return _finish(3)
        # ★投入した行が本当に1件ずつ入ったかを読み直して確かめる (件数の引き算では重複を見抜けない)
        try:
            conn.autocommit = True
            bad = []
            for sid, stitle, raw_slot, label, vid in planned:
                cur.execute("select count(*) from class_recordings where session_id=%s and video_url=%s",
                            (sid, f"https://youtu.be/{vid}"))
                n = cur.fetchone()[0]
                if n != 1:
                    bad.append(f"{raw_slot} {label} 動画 {vid[:4]}… が {n}件")
        except Exception as e:
            print(f"\n⚠ {len(planned)}件の登録は**完了している**が、確認の読み直しに失敗した ({type(e).__name__})。"
                  "\n   CEO 画面の「授業録画」で重複が無いか目視してください。")
            return _finish(3)
        if bad:
            print("\n❌ 投入後の確認で異常 (CEO 画面で手で直すこと):")
            for b in bad:
                print(f"   - {b}")
            return _finish(3)
        print(f"\n✅ {len(planned)}件を投入した (各1件で登録されていることを確認済み)")
        return _finish(1 if problems else 0, applied=len(planned))
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        # ★commit 済みかを見て文言を変える。無条件に「1件も行っていない」と言うと嘘になる窓がある。
        print("\n中断した (登録は完了済み。CEO 画面で確認してください)。" if _COMMITTED
              else "\n中断した (投入は1件も行っていない)。")
        sys.exit(3)
    except Exception as e:
        # ★想定外の例外を Python 既定の exit 1 (=「確認事項あり」と同じ) にしない。
        #   例外文はそのまま出さない (動画IDが載りうる)。
        print(f"\n❌ 異常終了した ({type(e).__name__})。"
              + ("登録は完了済み。CEO 画面で確認してください。" if _COMMITTED
                 else "登録は行っていない。もう一度実行してください。")
              + "\n   繰り返す場合はこの行をそのまま開発者に伝えてください。")
        sys.exit(3)
