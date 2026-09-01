#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔧 [2026-09-01 塾長指摘] 時間割ラベル「木曜3限 国公立コース 長文読解」→「金曜3限 …」の移送。

    railway run -s Postgres python3 scripts/class_timetable/rename_thu3_to_fri3.py            # 下見 (既定)
    railway run -s Postgres python3 scripts/class_timetable/rename_thu3_to_fri3.py --apply    # 実行
    ... --apply --no-shift-dates   # 出欠の日付は木曜のまま (ラベルだけ直す)

終了コード: 0=正常 (下見・実行とも) / 1=要確認あり / 2=引数エラー・中止 / 3=異常終了

■ なぜラベルを直すだけでは足りないか
  label は「クラス別ファイル配布・出欠・録画の紐づけキー」そのものなので、コード側だけ直すと
  既存データが**どのクラスにも属さない孤児**になる。具体的には:
    students.class_labels   録画の可視判定 (feed の title not in my_classes) に直撃 →
                            旧ラベルのままの生徒はそのクラスの録画が 0 件になる。
    class_attend            出欠 UI は「曜日から作った日付 + label」で引くので、旧ラベルは表示されない。
    class_sessions.title    録画がぶら下がっている親。ここが旧ラベルだと誰にも録画が出ない。
    class_files.class_label クラス別 配布ファイルのグループ。

■ 出欠の日付 (--shift-dates 既定 ON)
  旧ラベルの出欠は**木曜の日付**で記録されている。アプリが木曜に表示していたためで、
  実際の授業は金曜だった。金曜3限に移す以上、日付も +1 日して金曜に揃えないと、
  出欠 UI (金曜の日付で引く) からは永久に見えなくなる。
  ★木曜以外の日付が混ざっていたら**触らずに報告**する (推測で日付を動かさない)。

■ 冪等
  2 回目以降は対象 0 件で何もしない。書き込みは commit の**前**に検算し、合わなければ 1 件も書かずに巻き戻す。

■ ★実行順序 (ここを守らないと無言で壊れる)
  ① このスクリプトを --apply  → ② main に push (Vercel 数秒 / Railway 約1分) → ③ 動作確認
  ・録画の可視判定 (server/main.py の student_class_feed) は class_sessions.title と
    students.class_labels の **DB 同士**の照合なので、移送を先に済ませれば旧コードのままでも録画は見え続ける。
  ・逆順 (先に push) にすると、旧ラベルのままの生徒3名は class.html の受講クラス絞り込みから外れ、
    出欠のカードが消える。CEO 側も旧ラベルは _TIMETABLE_LABELS から消えているため 400 で開けない。
  ・★①と②の間に CEO「受講クラス」個別編集を保存しないこと。あの画面は生徒が持つ**未知の label を
    描画しないまま配列ごと上書き**するので (server/main.py の admin_set_student_classes)、
    移送結果あるいは旧ラベルが無言で消える。
  ・録画の自動割り当て (scripts/class_recordings/assign_from_playlists.py) は ① の後に回すこと。
    未移送でも LEGACY_SLOT が吸収して止まりはしないが、毎回「旧ラベルのまま」と警告が出る。
"""
import argparse
import datetime
import json
import os
import sys

OLD = "木曜3限 国公立コース 長文読解"
NEW = "金曜3限 国公立コース 長文読解"
THURSDAY = 3  # date.weekday(): 月=0 … 木=3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="実際に書き込む (既定は下見のみ)")
    ap.add_argument("--shift-dates", dest="shift", action="store_true", default=True,
                    help="class_attend の木曜の日付を +1日して金曜に揃える (既定)")
    ap.add_argument("--no-shift-dates", dest="shift", action="store_false",
                    help="日付は動かさずラベルだけ直す")
    args = ap.parse_args()

    try:
        import psycopg
    except ImportError:
        print("❌ psycopg が無い。`railway run -s Postgres python3 ...` で実行すること。")
        return 3
    dsn = os.environ.get("DATABASE_PUBLIC_URL") or os.environ.get("DATABASE_URL")
    if not dsn:
        print("❌ DATABASE_PUBLIC_URL / DATABASE_URL が無い。`railway run -s Postgres` を付けること。")
        return 2

    conn = psycopg.connect(dsn)
    conn.autocommit = False
    cur = conn.cursor()
    problems = []
    plan = {}

    print(f"🔧 {OLD!r} → {NEW!r}  ({'実行' if args.apply else '下見'})")

    # ---------------------------------------------------------------- 事前確認
    # 新ラベルが既に一部だけ入っていないか (途中まで走った形跡)
    cur.execute("select count(*) from class_attend where class_label = %s", (NEW,))
    pre_new_attend = cur.fetchone()[0]
    if pre_new_attend:
        print(f"  ℹ class_attend に新ラベルが既に {pre_new_attend}件 ある — 衝突は1件ずつ確認して畳む")

    # ---------------------------------------------------------------- ① students.class_labels
    cur.execute("select id, class_labels from students "
                "where class_labels is not null and class_labels <> '' and class_labels like %s",
                ("%" + OLD + "%",))
    stu = []
    for sid, raw in cur.fetchall():
        try:
            labels = json.loads(raw)
        except Exception:
            problems.append(f"students id={sid}: class_labels が JSON として壊れている — 手当てが要る")
            continue
        if not isinstance(labels, list):
            problems.append(f"students id={sid}: class_labels が配列でない — 手当てが要る")
            continue
        new = [NEW if l == OLD else l for l in labels]
        # 旧と新の両方を持っていたら重複するので畳む (順序は保つ)
        dedup, seen = [], set()
        for l in new:
            if l not in seen:
                seen.add(l)
                dedup.append(l)
        if dedup != labels:
            stu.append((sid, json.dumps(dedup, ensure_ascii=False)))
    plan["students.class_labels"] = len(stu)
    print(f"  ① students.class_labels : {len(stu)}名  (id: {', '.join(str(s[0]) for s in stu) or 'なし'})")

    # ---------------------------------------------------------------- ② class_attend
    cur.execute("select id, student_id, att_date, status, source from class_attend "
                "where class_label = %s order by att_date, student_id", (OLD,))
    att_rows = cur.fetchall()
    att = []
    planned_keys = {}    # (student_id, 更新後の日付) -> 先に計画した行 id。★DB既存だけでなく**バッチ内**の衝突も見る。
    for rid, sid, d, status, source in att_rows:
        nd = d
        if args.shift:
            if d.weekday() != THURSDAY:
                problems.append(f"class_attend id={rid}: 日付 {d} が木曜でない — 日付は動かさずラベルだけ直す")
            else:
                nd = d + datetime.timedelta(days=1)
        # UNIQUE(student_id, class_label, att_date) と衝突しないか (① 既存の新ラベル行)
        cur.execute("select id, status, source from class_attend "
                    "where student_id = %s and class_label = %s and att_date = %s", (sid, NEW, nd))
        clash = cur.fetchone()
        if clash:
            problems.append(f"class_attend id={rid} (生徒 {sid} / {d}→{nd}) は既存 id={clash[0]} と衝突する"
                            f" — 既存 {clash[1]}/{clash[2]} を残し、この行は触らない")
            continue
        # ② 同じバッチ内の衝突。計画時点では全行が旧ラベルなので ① では原理的に拾えない
        #    (例: 木曜の行を +1日した先に、元から金曜日付で入っていた旧ラベル行がいる)。
        #    ここを見ないと UPDATE の2本目で UniqueViolation になり、下見では気づけない。
        if (sid, nd) in planned_keys:
            problems.append(f"class_attend id={rid} (生徒 {sid} / {d}→{nd}) は同じ移送内の "
                            f"id={planned_keys[(sid, nd)]} と同じ日になる — 先に計画した方を残し、この行は触らない")
            continue
        planned_keys[(sid, nd)] = rid
        att.append((rid, sid, d, nd, status, source))
    plan["class_attend"] = len(att)
    print(f"  ② class_attend          : {len(att)}件"
          + (f"  (日付 +1日: {sum(1 for a in att if a[2] != a[3])}件)" if args.shift else "  (日付そのまま)"))
    for rid, sid, d, nd, status, source in att:
        print(f"       id={rid:<5} 生徒 {sid:<5} {d} → {nd}  {status}/{source}")

    # ---------------------------------------------------------------- ③ class_sessions.title
    cur.execute("select id, title, session_date from class_sessions where title = %s", (OLD,))
    sess = cur.fetchall()
    plan["class_sessions.title"] = len(sess)
    print(f"  ③ class_sessions.title  : {len(sess)}件  (id: {', '.join(str(s[0]) for s in sess) or 'なし'})")
    for sid_, _t, sdate in sess:
        cur.execute("select count(*) from class_recordings where session_id = %s", (sid_,))
        # ★session_date も出す。class_sessions は「クラスの器」として日付 NULL で使う運用だが、
        #   もし木曜の日付が入っていたら出欠 (+1日で金曜へ) と噛み合わなくなるので、目で見て判断する。
        _ds = str(sdate) if sdate else "なし(クラスの器)"
        print(f"       session {sid_}: 録画 {cur.fetchone()[0]}本 / 授業日 {_ds}"
              f"  (親の名前を直すだけなので録画の紐づけは維持される)")
        if sdate and sdate.weekday() == THURSDAY:
            problems.append(f"class_sessions id={sid_}: 授業日 {sdate} が木曜のまま — "
                            f"出欠は金曜へ移すので、この授業日も CEO で金曜に直すか判断すること")

    # ★class_sessions.title に UNIQUE 制約は無い (server/main.py の CREATE TABLE)。
    #   既に「金曜3限…」の公開授業があるところへ移送すると**同名2件**になり、
    #   assign_from_playlists.py の照合 (title.startswith(slot) が1件に絞れること) が
    #   恒久的に blocking する。情報ではなく中止条件にする。
    cur.execute("select id, title, session_date, is_published from class_sessions "
                "where title like %s and title <> %s order by id", (NEW[:4] + "%", OLD))
    dup_sess = cur.fetchall()
    if sess and dup_sess:
        print(f"\n❌ 中止: 「{NEW[:4]}…」の授業が既に {len(dup_sess)}件 ある。移送すると同名2件になり、"
              f"録画の自動割り当てが恒久的に止まる。")
        for rid_, t_, d_, pub_ in dup_sess:
            print(f"  - id={rid_} {t_!r} 授業日={d_} 公開={pub_}")
        print("  CEO 画面でどちらを残すか決めてから、もう一度実行すること。")
        conn.rollback()
        conn.close()
        return 2

    # ---------------------------------------------------------------- ④ class_files.class_label
    cur.execute("select id from class_files where class_label = %s", (OLD,))
    files = [r[0] for r in cur.fetchall()]
    plan["class_files.class_label"] = len(files)
    print(f"  ④ class_files.class_label: {len(files)}件  (id: {', '.join(map(str, files)) or 'なし'})")

    # ---------------------------------------------------------------- ⑤ course_applications.subjects
    #   登録フォームは受講クラス label を「・」連結して subjects に送る。承認時
    #   (server/main.py の admin_approve_course_application) が _TIMETABLE_LABELS に無い label を
    #   **黙って捨てて** students.class_labels を作るので、未承認 (pending) のまま旧ラベルを抱えた
    #   申込を移送後に承認すると、そのクラスだけ無言で欠ける。さらに既存生徒への合流パスは
    #   class_labels を丸ごと上書きするので、①で直した生徒の移送結果まで巻き戻る。
    cur.execute("select id, subjects from course_applications "
                "where status = 'pending' and subjects is not null and subjects like %s",
                ("%" + OLD + "%",))
    apps = []
    for aid, subj in cur.fetchall():
        parts, seen = [], set()
        for x in (y.strip() for y in subj.split("・")):
            if not x:
                continue
            x = NEW if x == OLD else x
            if x not in seen:
                seen.add(x)
                parts.append(x)
        ns = "・".join(parts)
        if ns != subj:
            apps.append((aid, ns))
    plan["course_applications.subjects"] = len(apps)
    print(f"  ⑤ course_applications    : {len(apps)}件 (未承認の申込・id: "
          f"{', '.join(str(a[0]) for a in apps) or 'なし'})")

    total = sum(plan.values())
    if problems:
        print("\n⚠ 要確認:")
        for p in problems:
            print(f"  - {p}")

    if not args.apply:
        print(f"\n下見だけで終了。書き込むなら --apply を付けること (対象 {total}件)。")
        conn.rollback()
        conn.close()
        return 1 if problems else 0

    if total == 0:
        print("\n対象 0 件。何もしない (移送済み)。")
        conn.rollback()
        conn.close()
        return 1 if problems else 0

    # ---------------------------------------------------------------- 実行
    #   ★検算は **commit の前** に同じトランザクションの中で回す。commit してから確かめると、
    #     おかしいと分かっても戻せない (本番の生徒データを壊したまま「検算で残りが見つかった」と
    #     報告するだけになる)。ここで落ちたら rollback して 1件も変えずに終わる。
    untouched_att = len(att_rows) - len(att)      # 衝突等で触らなかった出欠行 (旧ラベルのまま残るのが正しい)
    shifted_ids = [a[0] for a in att if a[2] != a[3]]   # 実際に日付を +1日する行だけ
    # 日付を動かさなかった行 (元が木曜でない) はラベルだけ直すので、新ラベル側に非金曜が残るのは想定内。
    #   ★母集団を混ぜないこと: untouched_att は「旧ラベルのまま残る行」で、
    #     非金曜の検算対象は「新ラベルになった行」= 交わらない別集合。前は両者を比べていて、
    #     木曜以外の出欠が1件あるだけで移送全体が巻き戻っていた。

    def leftovers(cur_):
        """このトランザクション/接続から見える「移送し残し」を数える。"""
        bad_ = []
        cur_.execute("select count(*) from students where class_labels like %s", ("%" + OLD + "%",))
        n_ = cur_.fetchone()[0]
        if n_:
            bad_.append(f"students.class_labels に旧ラベルが {n_}名 残っている")
        cur_.execute("select count(*) from class_attend where class_label = %s", (OLD,))
        n_ = cur_.fetchone()[0]
        if n_ != untouched_att:
            bad_.append(f"class_attend に旧ラベルが {n_}件 残っている (想定 {untouched_att}件 = 衝突で触らなかった分)")
        for table, col in (("class_sessions", "title"), ("class_files", "class_label")):
            cur_.execute(f"select count(*) from {table} where {col} = %s", (OLD,))
            n_ = cur_.fetchone()[0]
            if n_:
                bad_.append(f"{table}.{col} に旧ラベルが {n_}件 残っている")
        cur_.execute("select count(*) from course_applications "
                     "where status = 'pending' and subjects like %s", ("%" + OLD + "%",))
        n_ = cur_.fetchone()[0]
        if n_:
            bad_.append(f"course_applications (未承認) に旧ラベルが {n_}件 残っている")
        if args.shift and shifted_ids:
            # Postgres の extract(dow) は 0=日曜 … 5=金曜。★母集団は「日付を動かした行」だけ。
            cur_.execute("select count(*) from class_attend "
                         "where id = any(%s) and extract(dow from att_date) <> 5", (shifted_ids,))
            n_ = cur_.fetchone()[0]
            if n_:
                bad_.append(f"日付を +1日したのに金曜になっていない出欠が {n_}件 ある")
        return bad_

    try:
        for sid, js in stu:
            cur.execute("update students set class_labels = %s where id = %s", (js, sid))
        for rid, _sid, _d, nd, _st, _src in att:
            cur.execute("update class_attend set class_label = %s, att_date = %s where id = %s", (NEW, nd, rid))
        cur.execute("update class_sessions set title = %s, updated_at = current_timestamp where title = %s", (NEW, OLD))
        cur.execute("update class_files set class_label = %s where class_label = %s", (NEW, OLD))
        for aid, ns in apps:
            cur.execute("update course_applications set subjects = %s where id = %s", (ns, aid))
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        print(f"\n❌ 失敗 ({type(e).__name__}: {e})。1件も書き込まれていない。")
        conn.close()
        return 3

    bad = leftovers(cur)
    if bad:
        conn.rollback()
        print("\n❌ commit 前の検算で異常。**1件も書き込まずに巻き戻した**:")
        for b in bad:
            print(f"  - {b}")
        conn.close()
        return 3
    conn.commit()

    # ---------------------------------------------------------------- 別トランザクションで読み直す
    conn.autocommit = True
    after = leftovers(cur)
    cur.execute("select count(*) from students where class_labels like %s", ("%" + NEW + "%",))
    n_stu = cur.fetchone()[0]
    cur.execute("select count(*) from class_attend where class_label = %s", (NEW,))
    n_att = cur.fetchone()[0]
    print(f"\n✅ 移送した。新ラベル: 生徒 {n_stu}名 / 出欠 {n_att}件"
          f" / 授業 {plan['class_sessions.title']}件 / ファイル {plan['class_files.class_label']}件"
          f" / 未承認の申込 {plan['course_applications.subjects']}件")
    if untouched_att:
        print(f"  ℹ 衝突等で触らなかった出欠 {untouched_att}件 は旧ラベルのまま (上の要確認を参照)")
    _kept = len(att) - len(shifted_ids)
    if args.shift and _kept:
        print(f"  ℹ 日付が木曜でなかった {_kept}件 はラベルだけ直した (日付はそのまま = 出欠 UI では金曜に出ない)")
    if after:
        print("❌ commit 後の読み直しで残りが見つかった:")
        for b in after:
            print(f"  - {b}")
        conn.close()
        return 1
    conn.close()
    return 1 if problems else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n中止した。")
        sys.exit(2)
