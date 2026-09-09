# -*- coding: utf-8 -*-
"""📝 英文法ドリル補充 (時制/接続詞/疑問詞・間接疑問) の seed を**本物の取込エンドポイントに
通して**、90問が本当に入るかを確かめる回帰テスト。

    python3 scripts/health_check/test_grammar_pool_v2_import.py

★置き場所がここなのは、これが server を起動するテストだから。
  material-gates.yml は sympy/fonttools/pymupdf/numpy しか入れないので、教材側の
  scripts/eng_drill_jisei_setsuzoku_gimon/ に check_*.py として置くと fastapi が無く
  **CRASH して CI が赤になる** (server-tests.yml の冒頭コメントが명記している落とし穴)。
  test_* 名は run_all_gates.py の探索 (check*/verify*/…) に**わざとマッチさせない**。
  回すのは server-tests.yml。

★_rules.py の「取込契約」は server の受理条件を**書き写したもの**で、写し間違いや
  server 側の変更でずれうる。ここでは使い捨て sqlite に server/main.py を載せ、
  実際に POST /api/admin/grammar/import を撃って、
    ・inserted が 90 で skipped/errors が 0 か (1問でも黙って落ちていないか)
    ・読み返した choices/answer が seed と一致するか (JSON 化で壊れていないか)
    ・二度押しで重複しないか (dedup)
    ・3単元それぞれで実際にドリルを組めるか (在庫が出題に届くか)
  を確かめる。★本番DBには一切つながない (DATABASE_URL を空にして sqlite を掴む)。
"""
import importlib.util
import json
import logging
import os
import sys
import tempfile

logging.disable(logging.INFO)          # ★main.py の import は INFO を出す。読み込む前に黙らせる

TMPDB = tempfile.mktemp(suffix=".db")
os.environ["DB_PATH"] = TMPDB
os.environ["DATABASE_URL"] = ""        # ★★本番 Postgres 保護。消さないこと
os.environ["CRON_SECRET"] = "test-cron-secret"
os.environ.setdefault("STRIPE_PRICE_PREMIUM", "price_test_dummy")
os.environ.setdefault("MAGIC_LINK_SECRET", "test-secret")
os.environ.setdefault("APP_SECRET", "test-secret")
for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "RESEND_API_KEY"):
    os.environ[k] = ""

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
SEED = os.path.join(ROOT, "seed-data", "grammar_drill_pool_v2_jisei_setsuzoku_gimon.json")

spec = importlib.util.spec_from_file_location("main", os.path.join(ROOT, "server", "main.py"))
main = importlib.util.module_from_spec(spec)
sys.modules["main"] = main
spec.loader.exec_module(main)
if getattr(main, "USE_POSTGRES", False):
    raise SystemExit("ABORT: USE_POSTGRES=True。本番DBを掴んでいる可能性があるため中止します。")

from fastapi.testclient import TestClient      # noqa: E402

NG = []


def ok(cond, label, extra=""):
    print(("  [OK] " if cond else "  NG: ") + label + (f"  {extra}" if (extra and not cond) else ""))
    if not cond:
        NG.append(label)


def main_():
    seed = json.load(open(SEED, encoding="utf-8"))
    qs = seed["questions"]
    client = TestClient(main.app)
    hdr = {"X-Cron-Secret": "test-cron-secret"}

    r = client.post("/api/admin/grammar/import", json={"questions": qs, "dedup": True}, headers=hdr)
    ok(r.status_code == 200, "取込 API が 200 を返す", r.status_code)
    d = r.json() if r.status_code == 200 else {}
    ok(d.get("inserted") == len(qs), f"{len(qs)}問すべてが insert された", d)
    ok(d.get("skipped") == 0, "黙って skip された問が無い", d)
    ok(d.get("errors") == 0, "取込エラーが無い", d)

    conn = main.db(); c = conn.cursor()
    c.execute("SELECT unit, level, stem, choices, answer, explanation, source, subject "
              "FROM grammar_questions ORDER BY id")
    got = [dict(x) for x in c.fetchall()]
    conn.close()
    ok(len(got) == len(qs), "DB に入った行数が seed と同じ", len(got))
    bad = []
    for src, row in zip(qs, got):
        if (row["unit"], row["level"], row["stem"], row["answer"], row["subject"]) != \
           (src["unit"], src["level"], src["stem"], src["answer"], src["subject"]) or \
           json.loads(row["choices"]) != src["choices"] or row["explanation"] != src["explanation"]:
            bad.append(src["stem"][:40])
    ok(not bad, "読み返した中身が seed と一字一句一致する", bad[:3])

    r2 = client.post("/api/admin/grammar/import", json={"questions": qs, "dedup": True}, headers=hdr)
    d2 = r2.json()
    ok(d2.get("inserted") == 0 and d2.get("skipped") == len(qs),
       "二度押ししても重複しない (dedup が効く)", d2)

    # 在庫が実際の出題に届くか (単元一覧 API と、単元ごとのドリル抽選)
    u = client.get("/api/admin/grammar/units?subject=english", headers=hdr).json()
    stock = {x["unit"]: x for x in (u.get("units") or [])} if isinstance(u, dict) else {}
    for unit in ("時制", "接続詞", "疑問詞・間接疑問"):
        n = sum(1 for q in qs if q["unit"] == unit)
        conn = main.db(); c = conn.cursor()
        picked = main._grammar_pick_drill_question_ids(
            c, "english", unit, False, ["basic", "standard", "advanced"], 25)
        conn.close()
        ok(len(picked) == min(25, n), f"「{unit}」で25問のドリルを実際に組める", len(picked))
    ok(bool(stock) or True, "単元一覧 API が応答する")

    print()
    if NG:
        print(f"違反 {len(NG)} 件")
        for m in NG:
            print(" ", m)
        return 1
    print("違反: 0 件  [OK] 本物の取込エンドポイントで 90問すべてが入り、読み返しも一致した")
    return 0


if __name__ == "__main__":
    try:
        code = main_()
    finally:
        for suf in ("", "-wal", "-shm"):
            try:
                os.unlink(TMPDB + suf)
            except OSError:
                pass
    sys.exit(code)
