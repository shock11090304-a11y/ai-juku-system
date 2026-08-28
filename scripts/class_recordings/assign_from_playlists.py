#!/usr/bin/env python3
"""授業録画(YouTube 限定公開)を再生リストから拾って class_recordings に割り当てる。

  railway run -s Postgres python3 scripts/class_recordings/assign_from_playlists.py                 # dry-run
  railway run -s Postgres python3 scripts/class_recordings/assign_from_playlists.py --apply         # 投入
  ... --apply --allow-partial   # 取得できない再生リストがあっても、取れた分だけ投入する

終了コード: 0=確認事項なし / 1=確認事項あり(要確認の一覧を印字) / 2=投入を中止した・引数エラー / 3=異常終了

★判定ロジックは **server/class_recording_assign.py が正典**。ここには DB 入出力と印字しかない。
  CEO 画面のボタン (POST /api/admin/class-recordings/auto-assign) が同じモジュールを呼ぶ。
  ロジックをこちらに書き戻すと、ターミナルとボタンで判定がずれる。
★このリポジトリは PUBLIC。再生リストID・動画IDは**絶対にここへ書かない**
  (2026-08-06 に平文16IDを公開していた youtube-playlists.md を削除したが、
   git履歴からは今も取り出せる = 実効的な対処は YouTube 側で再生リストを非公開にすること)。
  再生リストは DB の admin_youtube_playlists からだけ読む。端末出力でも動画IDは伏せる。
★動画のタイトルは信用しない。「どの再生リストに入っているか」が曜日+限の正。
  (2026-08-06: 火曜3限の動画名が「8.３」だったが正は火曜=8/4)
  日付ラベルだけは動画名から取らざるを得ないので、**再生リストの曜日と突き合わせて**検算する。
★「取得できなかった」を「0本(新着なし)」と言わない。ここを間違えると
  配布漏れを「配布済み」と誤報告する。判定は class_recording_assign.fetch_playlist() を参照。

★既知の限界 (2026-08-18):
  - class_recordings に UNIQUE 制約が無いので、**2つの端末で同時に --apply すると重複する**。
    1人が順に実行する運用なら安全 (2回目以降は登録済みとして弾く)。CEO 画面のボタンとの
    同時実行も同じ (サーバ側は1プロセス内で直列化しているが、こちらとは排他できない)。
  - 再生リストの1ページ目 (先頭100本) しか読まない。100本に達したら警告して投入を止める。
  - **再生リストに名前が無いと丸ごと対象外**になる (名前から曜日+限を読むため)。新学期に
    再生リストを作り直して名前を付け忘れると、古い再生リストが全授業をカバーしたまま
    「新着0・見に行けた 15/15」で緑になる。唯一の手がかりは「どのクラスも新着が無い」ことなので、
    クラスごとの最新録画日を印字し、STALE_DAYS(28日)より古ければ警告する (長期休みなら無視してよい)。
    名前は CEO の再生リスト一覧から保存できる (2026-08-19 に DB 保存へ修正)。
"""
import os
import sys

# ★判定ロジックは server/ に置いてある (Railway のデプロイ範囲がそこなので、CEO 画面の
#   ボタンからも同じ実装を呼べる)。ここからは相対パスで読み込む。
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "server"))
from class_recording_assign import (  # noqa: E402
    DAY, DAY_LABEL, FUTURE_SLACK_DAYS, MAX_AGE_DAYS, OLD_LABEL_DAYS, PAGE_LIMIT, SLOT_OVERRIDE,
    STALE_DAYS, build_plan, date_label, fetch_playlist, recording_url, resolve_year, slot_of,
    today_jst, video_id,
)

# ★判定表ゲート (check_assign_logic.py) は「CLI が正典と**同一オブジェクト**を持っているか」を
#   見る。ここで束ねておかないと「未使用の import」に見えて整理され、検査が空振りになる。
_RE_EXPORTED = (DAY, DAY_LABEL, FUTURE_SLACK_DAYS, MAX_AGE_DAYS, OLD_LABEL_DAYS, PAGE_LIMIT,
                SLOT_OVERRIDE, STALE_DAYS, build_plan, date_label, fetch_playlist, recording_url,
                resolve_year, slot_of, today_jst, video_id)

# ★psycopg は main() の中で import する。トップレベルに置くと、DBを使わない
#   判定表ゲート (check_assign_logic.py) が psycopg 未導入の CI で ModuleNotFoundError で
#   落ち、「CRASH = 検査していない」状態になる (CI は sympy/fonttools/pymupdf/numpy しか入れない)。

_COMMITTED = False        # commit 済みか (中断・異常終了時の文言を事実に合わせるため)


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

    today = today_jst()
    conn = psycopg.connect(os.environ["DATABASE_PUBLIC_URL"])
    try:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("select playlist_id, name from admin_youtube_playlists order by sort_order, id")
        playlists = cur.fetchall()
        # ★公開中の授業だけを相手にする。非公開セッションに入れると「投入した」と出るのに誰にも見えない。
        cur.execute("select id, title from class_sessions where is_published = 1 order by id")
        sessions = cur.fetchall()
        # ★クラスごとの最新録画日。再生リストを作り直して**名前を付け忘れる**と、
        #   古い再生リストが全授業をカバーしたまま「新着0・見に行けた 15/15」で緑になる。
        #   そのとき唯一おかしいのは「どのクラスも何週間も新着が無い」ことなので、時間で気づく。
        cur.execute("select session_id, max(created_at) from class_recordings "
                    "where session_id is not null group by session_id")
        last_rec = {sid: dt for sid, dt in cur.fetchall()}
        # ★列の並びは class_recording_assign.Recording と一致させる (足りなければ TypeError)。
        cur.execute("select session_id, video_url, coalesce(provider, ''), coalesce(title, ''), id "
                    "from class_recordings")
        recordings = cur.fetchall()

        print(f"再生リスト {len(playlists)}件 "
              f"(名前未登録の{len(playlists) - len([1 for _, n in playlists if (n or '').strip()])}件は対象外)")
        print(f"公開中の授業 {len(sessions)}件 / 登録済み録画 {len(recordings)}件 "
              f"(動画IDを読めた {len({v for v in (video_id(r[1]) for r in recordings) if v})}件)")

        rep = build_plan(today, playlists, sessions, recordings, last_rec, progress=print)
        planned, problems, notes = rep["planned"], rep["problems"], rep["notes"]
        blocking, hazard = rep["blocking"], rep["hazard"]

        print(f"\nYouTube を見に行った再生リスト: {rep['fetched']}件 "
              f"(名前から曜日+限を読めず飛ばした {rep['skipped_name']}件 / "
              f"名前未登録 {rep['playlist_total'] - rep['playlist_named']}件)")
        print(f"\nYouTube を見に行けた授業: {rep['covered']}/{rep['sessions_total']}")
        if rep["uncovered"]:
            print(f"  見に行けなかった授業 ({len(rep['uncovered'])}件): {', '.join(rep['uncovered'])}")

        if notes:
            print("\n(参考) 補足 (対応は不要):")
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
        for p in planned:
            print(f"   {p['slot']:<7} {p['label']:>5}  動画 {p['video_id'][:4]}…  "
                  f"→ session {p['session_id']} {p['session_title']}")
        if not apply_mode:
            if blocking:
                print(f"\n⚠ このままでは --apply しても **1件も登録されません** (投入を止める項目が {blocking}件)。"
                      "\n   上の一覧を直してから再実行してください。")
            else:
                print("\n投入するなら --apply を付けて再実行。")
            return _finish(1 if problems else 0)
        if hazard:
            print(f"\n❌ 二重登録の恐れがある項目が {hazard}件あるので投入しない。"
                  "\n   これは --allow-partial でも免除しません (重複は取り返せないため)。")
            return _finish(2)
        if blocking and not allow_partial:
            print(f"\n❌ 見落としの恐れがある項目が {blocking}件あるので投入しない。"
                  "\n   直してから再実行する。承知のうえで取れた分だけ入れるなら --allow-partial。")
            return _finish(2)

        conn.autocommit = False
        global _COMMITTED
        try:
            for p in planned:
                cur.execute("insert into class_recordings (session_id, title, video_url, provider, is_published) "
                            "values (%s,%s,%s,'youtube',1)",
                            (p["session_id"], p["label"], recording_url(p["video_id"])))
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
            for p in planned:
                cur.execute("select count(*) from class_recordings where session_id=%s and video_url=%s",
                            (p["session_id"], recording_url(p["video_id"])))
                n = cur.fetchone()[0]
                if n != 1:
                    bad.append(f"{p['slot']} {p['label']} 動画 {p['video_id'][:4]}… が {n}件")
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
