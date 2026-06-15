#!/usr/bin/env python3
"""📜 [kokugo-passage-fix 2026-06-15] 共通テスト国語 (古文/漢文/現代文) プールのデータ生成不全 監査ツール。

検出する欠陥 (規約は dojo-drill.html markUnderlines / server/main.py _validate_kokugo_question と一致):
  - Class A: 設問が傍線部/下線部を参照するのに passage(本文)が空 → 本文が描画されず解答不能。
  - Class B: 傍線部「X」が passage に exact substring で存在しない (漢字順入替・句読点挿入・言い換え)。

使い方:
  # 公開 API を叩いて latest プールを監査 (認証不要・本番 READ のみ。デフォルト)
  python3 audit_kokugo_questions.py
  python3 audit_kokugo_questions.py --base https://trillion-ai-juku.com --limit 50

  # DATABASE_URL の Postgres/SQLite を直接叩いてプール全件を監査 (権威ある全数監査)
  DATABASE_URL=postgresql://... python3 audit_kokugo_questions.py --db

欠陥 0 で exit 0 / 1 件以上で exit 1 (CI/プリフライト用)。

検証ロジックは server/main.py の _validate_kokugo_question を import して使う (単一の真実源・drift 防止)。
[[desktop-pdf-choice-defect]] の audit_choice_defects.py と同系統の常設プリフライト監査。
"""
import argparse
import json
import os
import sys
import urllib.request

# main.py の検証関数を単一の真実源として import (drift 防止)。
# import 時の重い副作用を避けるため、未設定の env にダミーを入れてから import する。
os.environ.setdefault("ANTHROPIC_API_KEY", "")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main  # noqa: E402

KOKUGO_PARTS = list(main.DAIGAKU_KOKUGO_PARTS)  # ("kobun", "kanbun", "gendai")
# 共通テスト型 (kyotsu) を最優先で監査。二次記述 (todai/kyodai) も対象。
UNIV_KEYS = ["kyotsu", "center", "todai", "kyodai"]


def _audit_items(items, part):
    """items を2段階で検証して (hard, soft, empty) を返す。
      hard = 解答不能 (passage 空 / 語句自体が本文に無い・lenient で NG) = 要修復の (qid, reasons) リスト。
      soft = 下線が引けないだけ (装飾括弧/句読点差・strict NG だが lenient OK = 解答は可能) の (qid, ['underline_only'])。
      empty = 傍線部参照ありで passage 空の件数。"""
    hard = []
    soft = []
    empty = 0
    for it in items:
        qid = it.get("_question_id") or it.get("id") or "?"
        ok_strict, _ = main._validate_kokugo_question(it, part, strict=True)
        ok_lenient, reasons = main._validate_kokugo_question(it, part, strict=False)
        if any(r.startswith("empty_passage") for r in reasons):
            empty += 1
        if not ok_lenient:
            hard.append((qid, reasons[:4]))
        elif not ok_strict:
            soft.append((qid, ["underline_only"]))
    return hard, soft, empty


def _flag(hard, soft):
    return "🚨" if hard else ("⚠️ " if soft else "✅")


def audit_via_api(base, limit):
    base = base.rstrip("/")
    total_hard = 0
    total_soft = 0
    for part in KOKUGO_PARTS:
        for univ in UNIV_KEYS:
            url = f"{base}/api/exam-questions/bank?exam=daigaku&part={part}&univ={univ}&limit={limit}"
            try:
                with urllib.request.urlopen(url, timeout=40) as r:
                    d = json.load(r)
            except Exception as e:
                print(f"[{part}/{univ}] API ERROR: {e}")
                continue
            items = d.get("all", []) or []
            if not items:
                print(f"[{part}/{univ}] (プール空)")
                continue
            hard, soft, empty = _audit_items(items, part)
            total_hard += len(hard)
            total_soft += len(soft)
            print(f"{_flag(hard, soft)} [{part}/{univ}] items={len(items)} "
                  f"解答不能={len(hard)} 下線のみ不良={len(soft)} (空passage={empty})")
            for qid, reasons in hard[:8]:
                print(f"      🚨 qid={qid}: {reasons}")
            if len(hard) > 8:
                print(f"      … 他 解答不能 {len(hard) - 8} 件")
    return total_hard, total_soft


def audit_via_db():
    """DATABASE_URL の DB から exam_questions を全件取得して監査 (権威ある全数監査)。"""
    conn = main.db()
    c = conn.cursor()
    total_hard = 0
    total_soft = 0
    for part in KOKUGO_PARTS:
        c.execute(
            "SELECT id, eiken_grade, question_data FROM exam_questions WHERE exam_id = ? AND part_key = ?",
            ("daigaku", part),
        )
        rows = c.fetchall()
        by_univ = {}
        for row in rows:
            rid = row["id"] if hasattr(row, "keys") else row[0]
            grade = (row["eiken_grade"] if hasattr(row, "keys") else row[1]) or "(none)"
            raw = row["question_data"] if hasattr(row, "keys") else row[2]
            try:
                qd = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                qd = {}
            qd["_question_id"] = rid
            by_univ.setdefault(grade, []).append(qd)
        for grade, items in sorted(by_univ.items()):
            hard, soft, empty = _audit_items(items, part)
            total_hard += len(hard)
            total_soft += len(soft)
            print(f"{_flag(hard, soft)} [{part}/{grade}] 全{len(items)}件 "
                  f"解答不能={len(hard)} 下線のみ不良={len(soft)} (空passage={empty})")
            for qid, reasons in hard[:12]:
                print(f"      🚨 qid={qid}: {reasons}")
            if len(hard) > 12:
                print(f"      … 他 解答不能 {len(hard) - 12} 件")
    conn.close()
    return total_hard, total_soft


def main_cli():
    ap = argparse.ArgumentParser(description="共通テスト国語プールの本文欠落/傍線部不一致 監査")
    ap.add_argument("--db", action="store_true", help="DATABASE_URL の DB を直接叩いて全件監査")
    ap.add_argument("--base", default=os.getenv("AUDIT_BASE", "https://trillion-ai-juku.com"),
                    help="API モードのベース URL")
    ap.add_argument("--limit", type=int, default=50, help="API モードの part あたり取得件数 (最大50)")
    args = ap.parse_args()

    print("=" * 72)
    print("📜 共通テスト国語 (古文/漢文/現代文) 本文欠落・傍線部不一致 監査")
    print("   規約: passage 非空 & 傍線部「X」が passage に exact substring (markUnderlines 準拠)")
    print("=" * 72)

    if args.db:
        if not main.USE_POSTGRES and not os.path.exists(str(main.DB_PATH)):
            print("⚠️  DATABASE_URL 未設定 (SQLite ローカル DB を監査します)")
        total_hard, total_soft = audit_via_db()
    else:
        total_hard, total_soft = audit_via_api(args.base, min(args.limit, 50))

    print("-" * 72)
    print(f"凡例: 🚨解答不能(本文欠落/語句が本文に無い→要修復)  ⚠️下線のみ不良(本文を読めば解答可能・任意)")
    if total_hard:
        print(f"🚨 解答不能の大問 合計 {total_hard} 件。repair_kokugo_questions.py --apply で再生成・差し替えが必要。")
        if total_soft:
            print(f"⚠️  下線のみ不良 {total_soft} 件 (任意修復・--apply --include-soft で同時修復可)。")
        sys.exit(1)
    print(f"✅ 解答不能の大問 0 件。" + (f" (下線のみ不良 {total_soft} 件は任意)" if total_soft else ""))
    sys.exit(0)


if __name__ == "__main__":
    main_cli()
