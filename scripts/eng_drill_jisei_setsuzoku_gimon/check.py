# -*- coding: utf-8 -*-
"""英文法ドリル補充 (時制/接続詞/疑問詞・間接疑問) の機械ゲート。

    python3 scripts/eng_drill_jisei_setsuzoku_gimon/check.py

scripts/run_all_gates.py と CI (material-gates.yml) が引数なしで回す。**何も書かない**。

見るもの:
  1. コミット済み JSON そのもの     … 実際に取り込まれる中身を _rules.validate で測る
                                       (build の出力ではなくファイルを見る = 手編集も同じ網にかかる)
  2. 再生成して差分ゼロか            … ビルダーを直さずに JSON だけ書き換える抜け道を塞ぐ
  3. seed-data 全体での重複          … (stem, unit) が既存プールと衝突すると取込が黙って skip する
  4. CEO 画面の取込ボタン            … data-seed の指す先・件数・click ハンドラ
                                       (押せる導線が無いと、作っても本番には1問も入らない)
  5. 盲解き用ビューが本当に盲か      … 正解・解説が混ざっていないか

判定の中身 (単元名・正解の一意性・値参照の解説・正解位置の偏り) は _rules.py にある。
このゲート自身が効いているかは selftest_gate.py が変異試験で確かめる。
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(BASE, "..", ".."))
SEED_PATH = os.path.join(ROOT, "seed-data", "grammar_drill_pool_v2_jisei_setsuzoku_gimon.json")
BLIND_PATH = os.path.join(BASE, "blind_view.json")

sys.path.insert(0, BASE)
import _rules    # noqa: E402
import build     # noqa: E402

NG = []


def main():
    NG.clear()
    committed = open(SEED_PATH, encoding="utf-8").read()
    doc = json.loads(committed)
    rows = doc.get("questions") if isinstance(doc, dict) else doc
    if not isinstance(rows, list) or not rows:
        print(f"違反 1 件\n  NG: {os.path.relpath(SEED_PATH, ROOT)} に questions 配列が無い")
        sys.exit(1)

    # ---- 1. 取り込まれる中身そのものを測る (正典 content.py の正解文字列と突き合わせる)
    NG.extend(_rules.validate(rows, build.answers(), ROOT))

    # ---- 2. 再生成して差分ゼロか
    regen_rows, regen_blind = build.build()
    if (json.dumps(build.seed_document(regen_rows), ensure_ascii=False, indent=1) + "\n") != committed:
        NG.append(f"NG: seed JSON が build.py の出力と一致しない (手で編集された?): "
                  f"{os.path.relpath(SEED_PATH, ROOT)} … content.py を直して build.py で再生成すること")
    if (json.dumps(regen_blind, ensure_ascii=False, indent=1) + "\n") != open(BLIND_PATH, encoding="utf-8").read():
        NG.append("NG: blind_view.json が build.py の出力と一致しない")

    # ---- 3. seed-data 全体での重複 (同一 stem + 同一 unit は取込時に dedup で skip される)
    NG.extend(_rules.duplicate_across_seed(rows, ROOT, SEED_PATH))

    # ---- 4. CEO 画面の取込ボタンが繋がっているか (押せなければ本番に1問も入らない)
    NG.extend(_rules.ceo_button_wiring(
        open(os.path.join(ROOT, "ceo.html"), encoding="utf-8").read(),
        "/seed-data/" + os.path.basename(SEED_PATH), len(rows)))

    # ---- 5. 盲解き用ビューが本当に盲か
    for b in json.loads(open(BLIND_PATH, encoding="utf-8").read()):
        extra = set(b) - {"n", "unit", "level", "stem", "choices"}
        if extra:
            NG.append(f"NG: blind_view.json に余計なキー (答えが漏れている): {sorted(extra)}")

    # ---- 出力
    print("=== 英文法ドリル補充 (時制 / 接続詞 / 疑問詞・間接疑問) ===")
    print(f"検査対象: {os.path.relpath(SEED_PATH, ROOT)}  {len(rows)} 問")
    for k, cnt in sorted(_rules.position_report(rows).items(), key=lambda x: str(x[0])):
        n = sum(cnt.values())
        print(f"  {k[0]:<12s} {k[1]:<9s} {n:3d} 問  正解位置 {cnt}")
    if NG:
        print(f"\n違反 {len(NG)} 件")
        for m in NG:
            print(" ", m)
        sys.exit(1)
    print("\n違反: 0 件  [OK] 取込契約・正解の一意性・値参照の解説・正解位置・重複、すべて通過")


if __name__ == "__main__":
    main()
