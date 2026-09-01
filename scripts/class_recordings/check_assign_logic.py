#!/usr/bin/env python3
"""授業録画の割り当て判定を機械で検査する (run_all_gates.py が拾う)。

検査対象は **server/class_recording_assign.py** (判定の正典)。ネットワークにも DB にも
触らない。合成した ytInitialData を fetch_playlist に食わせ、docstring に書いた判定表どおりに
「取得失敗(fatal)」「本当に空(0本)」「正常」を区別できるかだけを見る。

★このゲートが在る理由: 2026-08-18 のレビューで、
  「1 本の利用できない動画が非表示です」というお知らせが**あるだけ**で
  本数の食い違いを無条件に許してしまい、8本消えていても
  「新しい録画はありません (exit 0)」で終わる穴が見つかった。
  配布漏れを「配布済み」と誤報告する = この仕組みの存在理由そのものが壊れる種類の穴で、
  かつ画面上は完全に正常に見えるので、人の目視では二度と気づけない。

★ロジックは CLI (scripts/.../assign_from_playlists.py) と CEO 画面のボタン
  (server/main.py の auto-assign API) が**共有**する。片方だけ差し替えられて検査が
  素通りにならないよう、CLI が正典と**同一オブジェクト**を re-export していることも見る。
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
TARGET = os.path.join(REPO, "server", "class_recording_assign.py")
CLI = os.path.join(HERE, "assign_from_playlists.py")


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load():
    # ★実名で sys.modules に載せてから CLI を読む。こうすると CLI の
    #   `from class_recording_assign import ...` が**この実体**を掴むので、
    #   下の同一性チェックが「CLI が自前で書き直していないか」を本当に見る。
    mod = _load(TARGET, "class_recording_assign")
    sys.modules["class_recording_assign"] = mod
    return mod


def page(n_items, shown=None, alert=None, alert_type="INFO", empty=False, contents=True):
    """再生リストページの ytInitialData を合成する。"""
    d = {}
    if contents:
        d["contents"] = {"x": [
            {"lockupViewModel": {
                "contentType": "LOCKUP_CONTENT_TYPE_VIDEO",
                "contentId": f"VID{i:08d}",
                "metadata": {"lockupMetadataViewModel": {"title": {"content": "8/17"}}},
            }} for i in range(n_items)]}
    if shown is not None:
        d.setdefault("header", {})["t"] = {"content": f"{shown} 本の動画"}
    if empty:
        d.setdefault("header", {})["e"] = {"simpleText": "この再生リストには動画がありません"}
    if alert:
        d["alerts"] = [{"alertRenderer": {"type": alert_type, "text": {"runs": [{"text": alert}]}}}]
    return d


# (ラベル, ページ, 期待する判定)  期待値: "fatal" / "N本" / "N本+警告"
CASES = [
    # ★contents を**有り**にすること。contents 無しにすると後段の contents ガードだけで
    #   期待値が満たされ、ERROR 判定を丸ごと消してもこのケースが緑のままになる (空振りテスト)。
    ("削除済み/存在しない (ERROR alert・contents あり)",
     page(3, shown=3, alert="再生リストが存在しません。", alert_type="ERROR"), "fatal"),
    ("ERROR alert + 空表示 (ERROR が優先されること)",
     page(0, empty=True, alert="再生リストが存在しません。", alert_type="ERROR"), "fatal"),
    ("削除済み (contents も無い)",
     page(0, alert="再生リストが存在しません。", alert_type="ERROR", contents=False), "fatal"),
    ("本当に空の再生リスト", page(0, empty=True), "0本"),
    ("正常 3本", page(3, shown=3), "3本"),
    ("★8本欠落なのにお知らせは1本 (見逃してはいけない)",
     page(3, shown=11, alert="1 本の利用できない動画が非表示になっています"), "fatal"),
    ("非表示1本と差がちょうど一致 (正常扱い)",
     page(10, shown=11, alert="1 本の利用できない動画が非表示になっています"), "10本"),
    ("★1ページ上限 + お知らせ (上限警告が飲み込まれてはいけない)",
     page(100, shown=150, alert="1 本の利用できない動画が非表示になっています"), "100本+警告"),
    ("1ページ上限 (お知らせなし)", page(100, shown=150), "100本+警告"),
    ("本数表記が読めないのに解析できた (構造変更の疑い)", page(3), "fatal"),
    ("本数表記も空表示も無い (構造変更の疑い)", page(0), "fatal"),
    ("contents が無い", page(0, contents=False), "fatal"),
    # ★contents ガードを**単独で**固定するケース。上の2つは別のガード (本数表記なし/空表示なし)
    #   でも fatal になるため、contents ガードを消しても緑のままだった。
    #   このケースは「本数表記だけ在って contents が無い」= ガードを外すと 0本 に化ける。
    ("contents 無しなのに本数表記だけ在る (0本に化ける)", page(0, shown=0, contents=False), "fatal"),
]


def main():
    mod = load()
    failures = []
    print(f"判定表の自己テスト: {os.path.relpath(TARGET, REPO)}")
    for label, data, expect in CASES:
        fake = f'<script>var ytInitialData = {json.dumps(data, ensure_ascii=False)};</script>'
        # 取得口を差し替えて判定部分だけを動かす (ネットワーク不要)
        try:
            items, fatal, _warn = mod.fetch_playlist("DUMMY", get=lambda _url: (fake, None))
        except Exception as e:
            failures.append(f"{label}: 例外 {type(e).__name__}: {e}")
            print(f"  ❌ {label}: 例外 {type(e).__name__}")
            continue
        got = "fatal" if items is None else f"{len(items)}本" + ("+警告" if fatal else "")
        if got == expect:
            print(f"  ✅ {label}: {got}")
        else:
            failures.append(f"{label}: {got} (期待 {expect})")
            print(f"  ❌ {label}: {got} (期待 {expect})")

    # ★取得そのものに失敗したとき (通信断・ブロック) を「0本」にしない。
    #   ここが緑でないと、ネットが切れているだけで「新しい録画はありません」と言う。
    print("取得失敗の扱い:")
    for label, ret in [("本文が取れない", (None, "YouTube に接続できない")),
                       ("本文が取れずエラー文も無い", (None, None))]:
        items, fatal, _w = mod.fetch_playlist("DUMMY", get=lambda _url, r=ret: r)
        if items is None and fatal:
            print(f"  ✅ {label}: fatal ({fatal[:24]}…)")
        else:
            failures.append(f"取得失敗({label}) が fatal にならない: items={items!r} fatal={fatal!r}")
            print(f"  ❌ {label}: items={items!r} fatal={fatal!r}")

    # 年の決め方 (年またぎ・過去側の直近)
    #   ★「今日にいちばん近い年」だと半年より古い日付が**翌年**に化け、正しい日付に
    #     「曜日が合わない」と嘘を言う (2026-08-28 に日曜1限で実測)。過去側を採ること。
    import datetime
    D = datetime.date
    print("年の決め方 (resolve_year):")
    YEAR_CASES = [
        # (月, 日, 今日, 期待する過去側, 期待する未来側)
        (2, 8, D(2026, 8, 28), D(2026, 2, 8), D(2027, 2, 8)),   # ★半年より古い = 翌年に化けていた
        (8, 23, D(2026, 8, 28), D(2026, 8, 23), D(2027, 8, 23)),
        (12, 28, D(2026, 1, 5), D(2025, 12, 28), D(2026, 12, 28)),  # 年またぎ
        (8, 29, D(2026, 8, 28), D(2026, 8, 29), D(2027, 8, 29)),    # 猶予の中の「明日」は過去側
        (9, 6, D(2026, 8, 28), D(2025, 9, 6), D(2026, 9, 6)),       # 猶予の外の未来は未来側
        (2, 29, D(2026, 8, 28), None, None),                        # その年に存在しない日付
    ]
    for mo, dy, day0, exp_past, exp_ahead in YEAR_CASES:
        got = mod.resolve_year(mo, dy, day0)
        if got == (exp_past, exp_ahead):
            print(f"  ✅ {mo}/{dy} @ {day0} → 過去 {got[0]} / 未来 {got[1]}")
        else:
            failures.append(f"resolve_year({mo},{dy},{day0}) = {got} (期待 {(exp_past, exp_ahead)})")
            print(f"  ❌ {mo}/{dy} @ {day0} → {got} (期待 {(exp_past, exp_ahead)})")

    # 日付ラベルの検算 (曜日・未来・離れすぎ・複数候補・年つき)
    T = datetime.date(2026, 8, 18)              # 火曜
    T2 = datetime.date(2026, 8, 28)             # 金曜 (塾長の実データを再現した日)
    DATE_CASES = [
        (T, "8/17", 0, "8/17"),                  # 月曜の再生リスト・月曜の日付
        (T, "8.３", 0, "8/3"),
        (T, "８・６", 3, "8/6"),
        (T, "8/17", 1, None),                    # 火曜の再生リストに月曜の日付 → 拒否
        (T, "2026/8/17", 0, None),               # 年つき → 拒否
        (T, "1.5倍速 8/17", 0, None),             # 候補が複数 → 拒否
        # ★「候補が複数」ルールを**単独で**固定するケース。上の '1.5倍速' は先頭候補 1/5 が
        #   曜日でも落ちるため、複数候補チェックを消しても緑のままになりうる。
        #   7/6 は月曜かつ 43日前で他の全ガードを通り抜けるので、この規則だけを試せる。
        (T, "7.6倍速 8/17", 0, None),
        (T, "8/24", 0, None),                    # 6日先 = 猶予の外。未来として拒否
        # ★猶予 (FUTURE_SLACK_DAYS) の中の未来。曜日は合うので、未来チェックだけが拒否できる。
        (T, "8/20", 3, None),
        # ★MAX_AGE_DAYS を**単独で**固定するケース。2025-09-29 は月曜なので曜日では落ちず、
        #   323日前 = 過去側の読みと未来側の読みの区別が付かない。
        (T, "9/29", 0, None),
        (T, "8/45", 0, None),                    # 日付として不正 → 拒否
        # ★ここから 2026-08-28 の実データ (直した当のバグ)。120日で弾いていた正しい過去回と、
        #   翌年に化けて「曜日が合わない」と誤報していた回を、どちらも受け取れること。
        (T, "4/13", 0, "4/13"),                  # 127日前の月曜 = 過去分の取り込み → 通す
        (T2, "2月8日（第2講義①）", 6, "2/8"),      # 201日前の日曜 (旧: 2027-02-08 月曜と誤読)
        (T2, "4月26日", 6, "4/26"),               # 124日前の日曜 (旧: 120日より古いと誤判定)
        (T2, "8/25", 2, None),                   # 水曜の再生リストに火曜の日付 = 本物の打ち間違い
    ]
    print("日付ラベルの検算:")
    for day0, raw, day, expect in DATE_CASES:
        label, _why = mod.date_label(raw, day, day0)
        if label == expect:
            print(f"  ✅ {day0} {raw!r} ({mod.DAY_LABEL[day]}曜) → {label}")
        else:
            failures.append(f"date_label({raw!r}, {day}, {day0}) = {label} (期待 {expect})")
            print(f"  ❌ {day0} {raw!r} ({mod.DAY_LABEL[day]}曜) → {label} (期待 {expect})")

    # 動画ID抽出 (取りこぼすと既存動画を新着と誤認して二重登録する)
    ID = "ABCDEFGHIJK"
    URL_CASES = [
        (f"https://youtu.be/{ID}", ID), (f"https://youtu.be/{ID}?si=x", ID),
        (f"https://www.youtube.com/watch?v={ID}", ID),
        (f"https://www.youtube.com/watch?app=desktop&v={ID}", ID),
        (f"https://www.youtube.com/live/{ID}", ID),
        (f"https://www.youtube.com/shorts/{ID}", ID),
        (f"https://YouTube.com/embed/{ID}", ID),
        ("https://www.youtube.com/playlist?list=PLxxxx", None),
        (f"https://evil.com/watch?v={ID}", None),
        (f"https://youtube.com.evil.com/watch?v={ID}", None),
        ("", None),
    ]
    print("動画IDの抽出:")
    for url, expect in URL_CASES:
        got = mod.video_id(url)
        if got == expect:
            print(f"  ✅ {url[:52]:<52} → {got}")
        else:
            failures.append(f"video_id({url!r}) = {got} (期待 {expect})")
            print(f"  ❌ {url[:52]:<52} → {got} (期待 {expect})")

    # ★登録URLは次回必ず読み戻せること (往復しないと、入れた動画を毎回「新着」と誤認して増殖する)
    rt = mod.video_id(mod.recording_url(ID))
    print("登録URLの往復:")
    if rt == ID:
        print(f"  ✅ recording_url → video_id → {rt}")
    else:
        failures.append(f"recording_url の往復に失敗: {rt} (期待 {ID})")
        print(f"  ❌ recording_url → video_id → {rt} (期待 {ID})")

    # 読めない URL の分類 (may_hide_video_id / provider_of / redact_url)
    #   ★2026-08-28 のデプロイ前レビューで、ここを「壊れ方の側から数える」実装にしていて
    #     壊れた動画URLを素通りさせていた。壊れ方は無限にあるので、安全な形の側を数える。
    print("読めない URL の分類:")
    ID11 = "dQw4w9WgXcQ"
    HAZARD_CASES = [
        # (URL, 動画IDを隠しうるか)
        (f"https://youtu.be/{ID11[:7]} {ID11[7:]}", True),    # 貼り付けで空白が混入 (7+4文字に割れる)
        (f"https://youtu.be/{ID11}_2", True),                  # 末尾に文字が続いて13文字
        (f"https://youtu.be/{ID11[:7]}%20{ID11[7:]}", True),   # %エスケープで割れる
        (f"youtu.be/{ID11}", True),                            # http(s):// が無い
        ("https://www.youtube.com/watch?v=broken", True),      # 壊れた watch URL
        ("https://www.youtube.com/playlist?list=PL" + "a" * 32, False),   # 再生リスト = 隠しようがない
        ("https://www.youtube.com/playlist?list=PLaa&v=broken", True),    # 一覧でも v= があれば動画URL
        ("https://www.youtube.com/@juku_channel", False),      # チャンネル
        ("https://www.youtube.com/channel/UCabcdefghijklmnop", False),
        ("", False),                                           # 空URL
    ]
    for url, expect in HAZARD_CASES:
        got = mod.may_hide_video_id(url)
        if got == expect:
            print(f"  ✅ {url[:46]:<46} → 止める={got}")
        else:
            failures.append(f"may_hide_video_id({url!r}) = {got} (期待 {expect})")
            print(f"  ❌ {url[:46]:<46} → 止める={got} (期待 {expect})")

    Rec = mod.Recording
    PROVIDER_CASES = [
        # provider 列が空の古い行。★hostname で見ると http(s):// 無しの YouTube URL を
        #   link に落とし、二重登録の見張りから丸ごと外してしまう。
        (f"youtu.be/{ID11}", "youtube"),
        (f"https://youtu.be/{ID11}", "youtube"),
        ("https://drive.google.com/file/d/1a2b3c4d5e6f/view", "link"),
        ("https://vimeo.com/123456789", "vimeo"),
    ]
    print("provider 列が空の行の見分け:")
    for url, expect in PROVIDER_CASES:
        got = mod.provider_of(Rec(1, url, "", "題名", 1))
        if got == expect:
            print(f"  ✅ {url[:46]:<46} → {got}")
        else:
            failures.append(f"provider_of({url!r}) = {got} (期待 {expect})")
            print(f"  ❌ {url[:46]:<46} → {got} (期待 {expect})")

    # ★伏せた URL から動画IDが復元できないこと (記号で割れても破片を出さない)
    print("URL の伏せ字:")
    for url in [f"https://youtu.be/{ID11}", f"https://youtu.be/{ID11[:7]}%20{ID11[7:]}",
                f"https://www.youtube.com/watch?v={ID11}"]:
        red = mod.redact_url(url)
        leaked = [p for p in (ID11[:5], ID11[5:], ID11[3:9], ID11) if len(p) >= 5 and p in red]
        if not leaked:
            print(f"  ✅ {url[:44]:<44} → {red}")
        else:
            failures.append(f"redact_url({url!r}) = {red} が動画IDの破片 {leaked} を出している")
            print(f"  ❌ {url[:44]:<44} → {red} (破片 {leaked})")

    # 計画づくり (build_plan) — 読めない URL の名指しと、同じ日付ラベルの重複
    #   ★どちらも「塾長が直せるか」に直結する。2026-08-28 に、読めない URL が1件あるだけで
    #     どの録画か分からないまま全クラスの割り当てが止まっていた (hazard は
    #     --allow-partial でも免除されない)。
    print("計画づくり (build_plan):")
    PL_TITLES = ["2月8日（第2講義①）", "4月26日", "8/23", "8/16", "8/16 第20講義", "第2講義問題3"]
    pl_page = {"contents": {"x": [
        {"lockupViewModel": {"contentType": "LOCKUP_CONTENT_TYPE_VIDEO",
                             "contentId": f"SUNVIDEO{i:03d}"[:11],
                             "metadata": {"lockupMetadataViewModel": {"title": {"content": t}}}}}
        for i, t in enumerate(PL_TITLES)]},
        "header": {"t": {"content": f"{len(PL_TITLES)} 本の動画"}}}
    fake_pl = f'<script>var ytInitialData = {json.dumps(pl_page, ensure_ascii=False)};</script>'
    recordings = [
        # (session_id, video_url, provider, title, rec_id) = Recording の並び
        (1, "https://www.youtube.com/playlist?list=PLaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
         "youtube", "まとめ", 77),                      # 動画IDを隠しようがない → 止めない
        (None, "https://youtu.be/ABCDEFGHIJ", "youtube", "全員向け", 78),   # 11文字に足りない → 止める
        (1, "https://drive.google.com/file/d/1a2b3c4d5e6f7g8h9i0j/view", "", "配布", 79),  # link 録画
        (1, "https://youtu.be/KNOWNVIDEO1", "youtube", "8/16", 80),        # 既に 8/16 が居る
    ]
    rep2 = mod.build_plan(T2, [("PL_SUN", "日曜1限")], [(1, "日曜 高校国語")], recordings, {},
                          get=lambda _url: (fake_pl, None))
    joined = " / ".join(rep2["problems"])
    checks = [
        ("読めない URL を録画番号で名指しする", "#77" in joined and "#78" in joined),
        ("動画IDを隠せない URL では投入を止めない", rep2["hazard"] == 1 and rep2["blocking"] == 1),
        ("provider 空のリンク録画を巻き込まない", "#79" not in joined),
        ("既に登録済みの日付と重なる回を人に回す",
         sum(1 for p in rep2["problems"] if "既に 8/16 の録画が登録されている" in p) == 2),
        ("日付を読めない動画は人に回す", any("第2講義問題3" in p for p in rep2["problems"])),
        # ★120日より古い正しい回 (2/8・4/26) を弾かない = 直した当のバグ
        ("過去分の取り込みを弾かない",
         sorted(p["label"] for p in rep2["planned"]) == ["2/8", "4/26", "8/23"]),
        ("古い回を登録するときは必ず知らせる",
         any("より古い回を 2本 登録します" in n for n in rep2["notes"])),
    ]
    # ★同じ**再生リスト**に同じ日付が2本あるとき (DB には無い) も人に回すこと。
    #   DB 由来の重複とは塾長のやることが違うので、言い方も分ける。
    dup_page = {"contents": {"x": [
        {"lockupViewModel": {"contentType": "LOCKUP_CONTENT_TYPE_VIDEO", "contentId": f"DUPVIDEO{i:03d}"[:11],
                             "metadata": {"lockupMetadataViewModel": {"title": {"content": t}}}}}
        for i, t in enumerate(["8/23", "8/23 後半"])]},
        "header": {"t": {"content": "2 本の動画"}}}
    rep4 = mod.build_plan(T2, [("PL_SUN", "日曜1限")], [(1, "日曜 高校国語")], [], {},
                          get=lambda _u: (f'<script>var ytInitialData = '
                                          f'{json.dumps(dup_page, ensure_ascii=False)};</script>', None))
    checks.append(("同じ再生リストに同じ日付が2本あれば人に回す",
                   len(rep4["planned"]) == 1
                   and any("同じ再生リストに 8/23 の回が2本ある" in p for p in rep4["problems"])))
    # ★"08/23" のような表記ゆれの既存行も台帳に載ること (前ゼロで照合が外れていた)
    rep5 = mod.build_plan(T2, [("PL_SUN", "日曜1限")], [(1, "日曜 高校国語")],
                          [(1, "https://youtu.be/OTHERVIDEO", "youtube", "08/23", 200)], {},
                          get=lambda _u: (f'<script>var ytInitialData = '
                                          f'{json.dumps(dup_page, ensure_ascii=False)};</script>', None))
    checks.append(("既存タイトルの前ゼロ (08/23) も同じ日付として照合する",
                   any("既に 8/23 の録画が登録されている" in p for p in rep5["problems"])))

    # ★読めない URL の**表示**は5件までに絞るが、**数える**のは全件。
    #   絞って数えると、6件目以降が危ない URL でも登録が通る (2026-08-28 に一度作った穴)。
    #   ★危ない行は表示枠 (5件) より**多く**置く。枠に収まる数だと、数える側を
    #     枠で打ち切る書き方 (bad_urls[:5] / continue を break に) を捕まえられない。
    #   ★無害な行を**先頭**に置く。危ない行が先に並んだ入力にすると、危険度順の
    #     並べ替えを消しても偶然そのままの順になり、並べ替えを検査できない。
    many = ([(1, f"https://www.youtube.com/playlist?list=PL{'a' * 32}{i}", "youtube", "まとめ", 200 + i)
             for i in range(2)]
            + [(1, f"https://youtu.be/BROKEN{i}", "youtube", "切れたURL", 100 + i) for i in range(7)])
    rep3 = mod.build_plan(T2, [], [(1, "日曜 高校国語")], many, {}, get=lambda _u: (fake_pl, None))
    checks.append(("表示は5件に絞っても、止める行は全件数える", rep3["hazard"] == 7))
    # ★止めている当の行が**名指しされる**こと。DB の行順のまま5件で切ると、
    #   「止めません」と書かれた無害な5件だけが並び、塾長は止めている行に辿り着けない。
    checks.append(("止めている行が表示枠に入る (危ない順に出す)",
                   sum(1 for p in rep3["problems"] if "登録を止めています" in p) == 5))
    checks.append(("枠から溢れた分は「うち何件が止める行か」を言う",
                   any("うち 2件は登録を止める行" in p for p in rep3["problems"])))

    for label, ok in checks:
        if ok:
            print(f"  ✅ {label}")
        else:
            failures.append(f"build_plan: {label} が成立していない")
            print(f"  ❌ {label}")
    if failures:
        print(f"     (参考) problems={rep2['problems']}")
        print(f"     (参考) notes={rep2['notes']}")

    # 再生リスト名 → 割り当て先 slot (2026-09-01 の「木曜3限 → 金曜3限」是正で書き換えた箇所)
    print("再生リスト名 → 割り当て先 slot:")
    for name, e_day, e_raw, e_slot in [
        ("8月以降金曜日３時間目", 4, "金曜3限", "金曜3限"),   # 付け替えを撤去したので素通し
        ("日曜1限 高校国語", 6, "日曜1限", "日曜"),           # 日曜だけは title が「日曜 高校国語」
        ("月曜2限", 0, "月曜2限", "月曜2限"),
    ]:
        got = mod.slot_of(name)
        if got == (e_day, e_raw, e_slot):
            print(f"  ✅ {name!r} → {got}")
        else:
            failures.append(f"slot_of({name!r}) = {got} (期待 {(e_day, e_raw, e_slot)})")
            print(f"  ❌ {name!r} → {got} (期待 {(e_day, e_raw, e_slot)})")
    if mod.SLOT_OVERRIDE.get("金曜3限"):
        failures.append("SLOT_OVERRIDE に「金曜3限 → …」の付け替えが復活している "
                        "(時間割の label 自体が金曜3限に直っているので不要・二重にずれる)")

    # ★移送中の一時フォールバック (LEGACY_SLOT) は平常時は空であること。
    #   空でないまま放置すると、旧ラベルの授業に当て続けて「移送が済んでいない」ことに気づけない。
    if mod.LEGACY_SLOT:
        print(f"  ℹ LEGACY_SLOT が入っている: {mod.LEGACY_SLOT}"
              " — 移送 (scripts/class_timetable/rename_thu3_to_fri3.py --apply) が済んだら空に戻すこと")

    # ★CLI が正典と同一の実装を使っていること。別実装に差し替わると、このゲートが
    #   緑のまま塾長のターミナルだけ判定が変わる (検査していない状態になる)。
    print("CLI が正典を共有していること:")
    try:
        cli = _load(CLI, "assign_cli")
        shared = all(getattr(cli, n, None) is getattr(mod, n)
                     for n in ("fetch_playlist", "date_label", "video_id", "slot_of", "build_plan"))
        if shared:
            print(f"  ✅ {os.path.relpath(CLI, REPO)} は server/class_recording_assign.py を re-export している")
        else:
            failures.append("CLI が正典と別の実装を使っている (判定がずれる)")
            print("  ❌ CLI が正典と別の実装を使っている")
    except Exception as e:
        failures.append(f"CLI を読み込めない: {type(e).__name__}: {e}")
        print(f"  ❌ CLI を読み込めない: {type(e).__name__}")

    if failures:
        print(f"\n❌ VIOLATION: {len(failures)} 件")
        for f in failures:
            print(f"   - {f}")
        return 1
    print("\n=== ALL PASS (判定表・取得失敗・年の決め方・日付検算・動画ID抽出・計画づくり・slot対応表・CLI共有) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
