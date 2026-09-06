#!/usr/bin/env python3
"""🧹 生徒に紐づくテーブルが、削除 cascade の 4 つのリストすべてに入っていることを機械で確認する (2026-09-07)。

CLAUDE.md の規則「生徒に紐づく新しいテーブルを足したら、プレビュー / 個別削除 / purge / _ORPHAN_SWEEP_TABLES の
全部に足す」を、人の記憶ではなく検査で固定する。1 箇所でも漏れると 2026-09-04 の 30,388 行の孤児化が再発する。
判定: server/main.py の DDL から student_id 列を持つテーブルを集め、各リストとの差を出す。差があれば exit 1。
例外 (設計上の意図): course_applications は NULL 化 (削除しない)、payments は FK で自動、anthropic_usage_log は
NULL 化のみ (会計記録) で sweep から外す。
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src = open(os.path.join(REPO, "server", "main.py"), encoding="utf-8").read()


def block(start_marker, end_marker, from_pos=0):
    i = src.index(start_marker, from_pos)
    j = src.index(end_marker, i)
    return src[i:j]


# DDL: student_id 列を持つテーブル
ddl = block('CREATE TABLE IF NOT EXISTS students (', '_migrations = [')
ddl = re.sub(r"--[^\n]*", "", ddl)
with_sid = set()
for t, body in re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)\s*\((.*?)\);", ddl, re.S):
    if re.search(r"\bstudent_id\b", body):
        with_sid.add(t)
# 4 リスト
delete_fn = block("def admin_student_delete(", "\n@app.", 0)
preview = set(re.findall(r'\("(\w+)", "student_id"\)', delete_fn))
delete_ = set(re.findall(r'\("(\w+)", "(?:DELETE FROM|UPDATE) ', delete_fn))
purge_fn = block("def admin_students_purge_stale(", "\n@app.", 0)
purge = set(re.findall(r'\("(\w+)", f"(?:DELETE FROM|UPDATE) ', purge_fn))
sweep = set(re.findall(r'"(\w+)"', block("_ORPHAN_SWEEP_TABLES = (", ")\n")))
KEEP = {"course_applications"}                       # NULL 化 (履歴保持)
NO_SWEEP = {"payments", "anthropic_usage_log"}       # FK / 会計記録 (NULL 化のみ)
problems = {}
for name, got, extra_ok in (("プレビュー (related_tables)", preview, set()), ("個別削除 (delete_tables)", delete_, set()),
                            ("purge (cascade_tables)", purge, set()), ("_ORPHAN_SWEEP_TABLES", sweep, NO_SWEEP)):
    missing = with_sid - KEEP - extra_ok - got
    if missing:
        problems[name] = sorted(missing)
print(f"student_id を持つテーブル: {len(with_sid)} / プレビュー {len(preview)} / 個別削除 {len(delete_)} / purge {len(purge)} / sweep {len(sweep)}")
if problems:
    print("❌ cascade リストに漏れ:")
    for k, v in problems.items():
        print(f"  - {k}: {v}")
    print("  → CLAUDE.md の規則どおり 4 箇所すべてに足してください")
    sys.exit(1)
print("✅ 4 リストとも揃っています")
