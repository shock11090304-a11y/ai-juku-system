#!/usr/bin/env python3
"""📜 [kokugo-passage-fix 2026-06-15] 共通テスト国語 (古文/漢文/現代文) 不良大問の再生成・差し替えツール。

audit_kokugo_questions.py が検出する不良大問 (passage 空 / 傍線部「X」が passage に存在しない) を
修正済みの国語専用生成器 (_generate_kokugo_exam_question) で作り直し、
「passage 非空 & 傍線部引用が passage に exact substring」を **機械検証してから** DB を差し替える。

⚠️ 本番 Postgres を書き換える破壊的操作。実行には prod env が必要:
    DATABASE_URL=postgresql://...   ANTHROPIC_API_KEY=sk-ant-...

使い方:
  # 1) まず dry-run (既定): 何件を作り直すかを表示するだけ。API も DB も書き込まない。
  DATABASE_URL=... python3 repair_kokugo_questions.py

  # 2) 実際に再生成して差し替え (各大問につき最大3回まで生成し検証通過のみ書き込み)
  DATABASE_URL=... ANTHROPIC_API_KEY=... python3 repair_kokugo_questions.py --apply

  # 件数制限 / 部分指定
  python3 repair_kokugo_questions.py --apply --max 20 --part kanbun

差し替えは「再生成が検証を通過した大問」のみ。通過しなければ元データを温存 (fail-closed・プールを悪化させない)。
[[dojo-drill-feature]] が使うプール。検証規約は dojo-drill.html markUnderlines と一致。
"""
import argparse
import json
import os
import sys

os.environ.setdefault("ANTHROPIC_API_KEY", "")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main  # noqa: E402


def _load_bad_rows(part_filter=None, include_soft=False):
    """DB から国語の全大問を取り、修復対象の (id, part, grade, qd, reasons) を返す。
    既定は解答不能 (strict=False で NG = 本文欠落/語句が本文に無い) のみ。
    include_soft=True で下線のみ不良 (strict NG だが lenient OK) も対象に含める。"""
    conn = main.db()
    c = conn.cursor()
    bad = []
    parts = [part_filter] if part_filter else list(main.DAIGAKU_KOKUGO_PARTS)
    for part in parts:
        c.execute(
            "SELECT id, eiken_grade, question_data FROM exam_questions WHERE exam_id = ? AND part_key = ?",
            ("daigaku", part),
        )
        for row in c.fetchall():
            rid = row["id"] if hasattr(row, "keys") else row[0]
            grade = (row["eiken_grade"] if hasattr(row, "keys") else row[1])
            raw = row["question_data"] if hasattr(row, "keys") else row[2]
            try:
                qd = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                qd = {}
            ok_lenient, reasons = main._validate_kokugo_question(qd, part, strict=False)
            if not ok_lenient:
                bad.append((rid, part, grade, qd, reasons))  # 解答不能 (最優先)
            elif include_soft:
                ok_strict, sreasons = main._validate_kokugo_question(qd, part, strict=True)
                if not ok_strict:
                    bad.append((rid, part, grade, qd, ["underline_only"] + sreasons[:2]))
    conn.close()
    return bad


def _replace_row(rid, qd):
    """1行を差し替え (UPDATE)。書き込み前に呼び出し側で検証済みであること。"""
    conn = main.db()
    c = conn.cursor()
    try:
        c.execute(
            "UPDATE exam_questions SET question_data = ?, model = ? WHERE id = ?",
            (json.dumps(qd, ensure_ascii=False), main.EXAM_QUESTIONS_MODEL, rid),
        )
        conn.commit()
    finally:
        conn.close()


def main_cli():
    ap = argparse.ArgumentParser(description="共通テスト国語 不良大問の再生成・差し替え")
    ap.add_argument("--apply", action="store_true", help="実際に再生成して DB を差し替える (既定は dry-run)")
    ap.add_argument("--max", type=int, default=0, help="差し替える最大件数 (0=無制限)")
    ap.add_argument("--part", choices=list(main.DAIGAKU_KOKUGO_PARTS), help="対象 part を限定")
    ap.add_argument("--include-soft", action="store_true",
                    help="下線のみ不良 (解答は可能だが傍線部の下線が描画されない) も修復対象に含める")
    args = ap.parse_args()

    bad = _load_bad_rows(args.part, include_soft=args.include_soft)
    label = "修復対象 (解答不能" + ("+下線のみ不良" if args.include_soft else "") + ")"
    print(f"📜 {label}: {len(bad)} 件" + (f" (part={args.part})" if args.part else ""))
    for rid, part, grade, qd, reasons in bad[:50]:
        print(f"  qid={rid} {part}/{grade}: {reasons[:3]}")
    if len(bad) > 50:
        print(f"  … 他 {len(bad) - 50} 件")

    if not args.apply:
        print("\n(dry-run) --apply を付けると再生成・差し替えを実行します。")
        print("⚠️  --apply には DATABASE_URL と ANTHROPIC_API_KEY (prod) が必要です。")
        return

    if not main.ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY 未設定。再生成できません。")
        sys.exit(2)

    targets = bad[: args.max] if args.max > 0 else bad
    fixed = 0
    skipped = 0
    for rid, part, grade, qd, reasons in targets:
        try:
            new_qd = main._generate_kokugo_exam_question(part, grade)
        except Exception as e:
            print(f"  qid={rid} 再生成 例外: {type(e).__name__}: {e} → 温存")
            skipped += 1
            continue
        if not new_qd:
            print(f"  qid={rid} {part}/{grade}: 再生成が検証を通過せず → 元データ温存")
            skipped += 1
            continue
        ok, vr = main._validate_kokugo_question(new_qd, part)  # 二重検証 (書き込み直前)
        if not ok:
            print(f"  qid={rid} {part}/{grade}: 二重検証 NG ({vr[:2]}) → 温存")
            skipped += 1
            continue
        _replace_row(rid, new_qd)
        fixed += 1
        print(f"  ✅ qid={rid} {part}/{grade}: 差し替え完了 (設問{len(new_qd.get('questions') or [])}問)")

    print(f"\n差し替え {fixed} 件 / 温存 {skipped} 件 (対象 {len(targets)} 件)")


if __name__ == "__main__":
    main_cli()
