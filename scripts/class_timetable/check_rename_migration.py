#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔧 rename_thu3_to_fri3.py (本番DB移送) の挙動を sqlite の偽DBで検査する (run_all_gates.py が拾う)。

    python3 scripts/class_timetable/check_rename_migration.py

ネットワークにも本番DBにも触らない。psycopg のごく薄いスタブ (sqlite バックエンド) を
sys.path に差し込み、移送スクリプトの main() をそのまま走らせて、
**書き換わった中身**まで読み返して照合する。

★このゲートが在る理由 (2026-09-01 のレビューで見つかった穴):
  移送スクリプトは「本番の生徒データを 1 度だけ書き換える」性質上、手で試せない。
  実際、レビュー前の版には次の 2 つが入っていた。どちらも下見 (--apply なし) では
  一切見えず、本番で --apply した瞬間に初めて出る種類の不具合だった:
    ① 木曜でない出欠が 1 件でもあると、検算の母集団を取り違えて**移送全体が巻き戻る**
       (「その行はラベルだけ直す」と自分で謳っている経路で必ず失敗する)。
    ② 同じ移送の中で「木曜行を +1 日した先」と「元から金曜日付の旧ラベル行」がぶつかると、
       事前の衝突検査 (class_label = 新ラベル で引く) が原理的に拾えず、
       2 本目の UPDATE で UNIQUE 違反 → 全ロールバック。
  どちらも「本番データが特定の形のときだけ」なので、目視でも下見でも永久に気づけない。
"""
import contextlib
import datetime
import importlib.util
import io
import json
import os
import re
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "rename_thu3_to_fri3.py")
OLD = "木曜3限 国公立コース 長文読解"
NEW = "金曜3限 国公立コース 長文読解"
THU = ["2026-07-02", "2026-07-09", "2026-07-16"]      # 木曜


# ----------------------------------------------------------------- psycopg スタブ (sqlite)
class _Cur:
    def __init__(self, c):
        self._c = c

    def _tr(self, sql, args):
        """Postgres 方言を sqlite に寄せる。★対応できない構文は素通しせず例外にする
        (黙って別のSQLに化けると「通ったのに検査していない」になる)。"""
        args = list(args or [])
        m = re.search(r"id\s*=\s*any\(%s\)", sql, re.I)
        if m:                                    # id = any(%s) → id IN (?,?,…)
            idx = sql[:m.start()].count("%s")
            lst = args[idx]
            sql = sql[:m.start()] + "id IN (" + ",".join("?" * len(lst)) + ")" + sql[m.end():]
            args[idx:idx + 1] = list(lst)
        sql = re.sub(r"extract\(dow from (\w+)\)", r"CAST(strftime('%w', \1) AS INTEGER)", sql, flags=re.I)
        if re.search(r"\bany\s*\(|\bextract\s*\(", sql, re.I):
            raise AssertionError(f"スタブが訳せない Postgres 構文が残っている: {sql}")
        sql = sql.replace("%s", "?")
        args = [a.isoformat() if isinstance(a, (datetime.date, datetime.datetime)) else a for a in args]
        return sql, args

    def execute(self, sql, args=()):
        s, a = self._tr(sql, args)
        self._c.execute(s, a)
        return self

    @staticmethod
    def _conv(row):
        return tuple(datetime.date.fromisoformat(v)
                     if isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) else v
                     for v in row)

    def fetchone(self):
        r = self._c.fetchone()
        return self._conv(r) if r else None

    def fetchall(self):
        return [self._conv(r) for r in self._c.fetchall()]


class _Conn:
    def __init__(self, path):
        self._db = sqlite3.connect(path)
        self.autocommit = False

    def cursor(self):
        return _Cur(self._db.cursor())

    def commit(self):
        self._db.commit()

    def rollback(self):
        self._db.rollback()

    def close(self):
        self._db.close()


def _install_stub(tmpdir):
    mod = os.path.join(tmpdir, "psycopg.py")
    with io.open(mod, "w", encoding="utf-8") as f:
        f.write("connect = None\n")            # 中身は下で差し替える
    sys.path.insert(0, tmpdir)
    import psycopg
    psycopg.connect = lambda dsn: _Conn(dsn)
    return psycopg


# ----------------------------------------------------------------- フィクスチャ
def build(path, attend, sessions, apps=(), files=()):
    if os.path.exists(path):
        os.remove(path)
    db = sqlite3.connect(path)
    c = db.cursor()
    c.execute("create table students (id int, class_labels text)")
    c.execute("create table class_attend (id int, student_id int, class_label text, att_date text, "
              "status text, source text, unique(student_id, class_label, att_date))")
    c.execute("create table class_sessions (id int, title text, session_date text, is_published int, updated_at text)")
    c.execute("create table class_files (id int, class_label text)")
    c.execute("create table class_recordings (id int, session_id int)")
    c.execute("create table course_applications (id int, status text, subjects text)")
    for sid, labels in [(1, [OLD, "月曜1限 中学応用"]), (2, [OLD])]:
        c.execute("insert into students values (?,?)", (sid, json.dumps(labels, ensure_ascii=False)))
    for i, (sid, lab, d, st, src) in enumerate(attend, 1):
        c.execute("insert into class_attend values (?,?,?,?,?,?)", (i, sid, lab, d, st, src))
    for i, (t, d, pub) in enumerate(sessions, 10):
        c.execute("insert into class_sessions values (?,?,?,?,null)", (i, t, d, pub))
        c.execute("insert into class_recordings values (?,?)", (i, i))
    for i, lab in enumerate(files, 1):
        c.execute("insert into class_files values (?,?)", (i, lab))
    for i, (stt, subj) in enumerate(apps, 1):
        c.execute("insert into course_applications values (?,?,?)", (i, stt, subj))
    db.commit()
    db.close()


def run(path, argv):
    os.environ["DATABASE_PUBLIC_URL"] = path
    spec = importlib.util.spec_from_file_location("mig_under_test", TARGET)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    saved, sys.argv = sys.argv[:], ["mig"] + list(argv)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = mod.main()
    finally:
        sys.argv = saved
    return code, buf.getvalue()


def dump(path):
    db = sqlite3.connect(path)
    c = db.cursor()
    out = (c.execute("select id, student_id, class_label, att_date from class_attend order by id").fetchall(),
           c.execute("select id, class_labels from students order by id").fetchall(),
           c.execute("select id, title from class_sessions order by id").fetchall(),
           c.execute("select id, status, subjects from course_applications order by id").fetchall())
    db.close()
    return out


def main():
    if not os.path.exists(TARGET):
        print(f"❌ 検査対象が無い: {TARGET}")
        return 1
    tmp = tempfile.mkdtemp(prefix="rename_mig_gate_")
    _install_stub(tmp)
    dbp = os.path.join(tmp, "t.db")
    failures = []
    print("移送スクリプトの実挙動 (sqlite の偽DBで --apply を走らせて中身を読み返す):")

    # (ラベル, フィクスチャ, argv, 期待exit, 期待する中身) ★終了コード: 0=正常 / 1=要確認あり / 2=中止
    CASES = [
        ("木曜のみ3件 → 全件 +1日で金曜へ",
         dict(attend=[(1, OLD, THU[0], "present", "self"), (1, OLD, THU[1], "present", "self"),
                      (2, OLD, THU[2], "absent", "self")], sessions=[(OLD, None, 1)]),
         ["--apply"], 0,
         lambda d: (sorted(a[3] for a in d[0]) == ["2026-07-03", "2026-07-10", "2026-07-17"]
                    and all(a[2] == NEW for a in d[0]) and d[2][0][1] == NEW
                    and all(OLD not in s for _, s in d[1]))),
        # ★旧実装はここで「検算で異常」と言って**移送全体を巻き戻して**いた
        ("木曜でない振替が1件混在 → 他は移送し、その行はラベルだけ直す",
         dict(attend=[(1, OLD, THU[0], "present", "self"), (1, OLD, "2026-08-05", "present", "admin")],
              sessions=[(OLD, None, 1)]),
         ["--apply"], 1,
         lambda d: [(a[2], a[3]) for a in d[0]] == [(NEW, "2026-07-03"), (NEW, "2026-08-05")]),
        # ★旧実装はここで UNIQUE 違反 → 全ロールバック (下見では見えない)
        ("同じ移送内の衝突 (木曜+1日 == 元から金曜日付の旧ラベル行)",
         dict(attend=[(1, OLD, "2026-07-02", "present", "self"), (1, OLD, "2026-07-03", "absent", "admin")],
              sessions=[(OLD, None, 1)]),
         ["--apply"], 1,
         lambda d: (len([a for a in d[0] if a[2] == NEW]) == 1
                    and len([a for a in d[0] if a[2] == OLD]) == 1)),
        ("既存の新ラベル行と衝突 → 既存を残してその行は触らない",
         dict(attend=[(1, OLD, THU[0], "present", "self"), (1, NEW, "2026-07-03", "late", "admin")],
              sessions=[(OLD, None, 1)]),
         ["--apply"], 1,
         lambda d: [a[2] for a in d[0]] == [OLD, NEW]),
        # ★同名2件を作ると assign_from_playlists.py が恒久的に blocking する
        ("金曜3限の授業が既にある → 中止して1件も書かない",
         dict(attend=[(1, OLD, THU[0], "present", "self")], sessions=[(OLD, None, 1), (NEW, None, 1)]),
         ["--apply"], 2,
         lambda d: sorted(t for _, t in d[2]) == sorted([OLD, NEW]) and d[0][0][2] == OLD),
        ("未承認の申込 subjects も移送する (承認済みは触らない)",
         dict(attend=[(1, OLD, THU[0], "present", "self")], sessions=[(OLD, None, 1)],
              apps=[("pending", "水曜3限 国公立コース 英文法・" + OLD + "・日曜 高校国語"),
                    ("approved", OLD)]),
         ["--apply"], 0,
         lambda d: (d[3][0][2] == "水曜3限 国公立コース 英文法・" + NEW + "・日曜 高校国語"
                    and d[3][1][2] == OLD)),
        ("--no-shift-dates は日付を動かさない",
         dict(attend=[(1, OLD, THU[0], "present", "self")], sessions=[(OLD, None, 1)]),
         ["--apply", "--no-shift-dates"], 0,
         lambda d: d[0][0][2] == NEW and d[0][0][3] == THU[0]),
        ("下見 (--apply なし) は1件も書き換えない",
         dict(attend=[(1, OLD, THU[0], "present", "self")], sessions=[(OLD, None, 1)]),
         [], 0,
         lambda d: d[0][0][2] == OLD and d[2][0][1] == OLD and all(OLD in s for _, s in d[1])),
        ("class_files も移送する",
         dict(attend=[], sessions=[(OLD, None, 1)], files=[OLD]),
         ["--apply"], 0,
         lambda d: d[2][0][1] == NEW),
    ]

    for label, fx, argv, want_code, check in CASES:
        build(dbp, **fx)
        try:
            code, out = run(dbp, argv)
        except Exception as e:
            failures.append(f"{label}: 例外 {type(e).__name__}: {e}")
            print(f"  ❌ {label}: 例外 {type(e).__name__}: {e}")
            continue
        ok = code == want_code
        why = "" if ok else f" (期待 {want_code})"
        if ok:
            try:
                ok = bool(check(dump(dbp)))
            except Exception as e:
                ok, why = False, f" (照合で例外 {type(e).__name__}: {e})"
            if not ok and not why:
                why = f" (中身が期待と違う: {dump(dbp)})"
        print(("  ✅ " if ok else "  ❌ ") + f"{label} → exit={code}{why}")
        if not ok:
            failures.append(label + why)
            print("\n".join("      " + l for l in out.splitlines()))

    # 冪等: 同じDBに2回 --apply しても2回目は対象0件
    build(dbp, attend=[(1, OLD, THU[0], "present", "self")], sessions=[(OLD, None, 1)])
    c1, _ = run(dbp, ["--apply"])
    c2, o2 = run(dbp, ["--apply"])
    if c1 == 0 and c2 == 0 and "対象 0 件" in o2:
        print("  ✅ 冪等: 2回目は「対象 0 件」で何もしない")
    else:
        failures.append(f"冪等 (1回目 exit={c1} / 2回目 exit={c2})")
        print(f"  ❌ 冪等: 1回目 exit={c1} / 2回目 exit={c2}")

    if failures:
        print(f"\n❌ VIOLATION {len(failures)}件")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\n✅ ALL PASS — 移送スクリプトは境界ケースでも期待どおり")
    return 0


if __name__ == "__main__":
    sys.exit(main())
