#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""目録ゲート `check_materials_index.py` が **本当に落とすか** を変異で確かめる。

    python3 scripts/materials_index/verify_index_gate.py

■ なぜ要るか
  `sys.exit(1)` の書き忘れや正規表現の書き間違いが 1 行あるだけで、ゲートは
  「常に緑」になる。緑を見て「検査した」と思い込むのが一番危ない状態なので、
  **違反を仕込んだ目録を渡して、1 つ残らず捕まえられることを機械で固定する**。

■ 副作用ゼロ
  一時ファイルを書かない。`check_index()` が dict を受ける形にしてあるので、
  メモリ上で目録を壊して渡すだけで済む。
"""
import copy
import sys

import check_materials_index as gate

# ★実名らしき文字列をソースに直書きすると check_no_pii.py 自身が落とす（それが正しい挙動）。
#   ここは「宛名を検出できるか」を試す負のテストなので、literal として繋がらない形で組む。
FAKE_ADDRESSEE = "佐" + "々" + "木" + "さん専用プリント"

BASE = {
    "schema": 1,
    "note": "テスト用",
    "sources": [
        {"id": "local", "label": "~/Desktop", "kind": "local",
         "scanned_at": "2026-08-27", "count": 2},
    ],
    "items": [
        {"id": "local:eng/a.pdf", "source": "local", "title": "英文法演習.pdf",
         "locator": "eng/a.pdf", "mime": "pdf", "bytes": 100, "modified": "2026-08-01",
         "subject": "英語", "kind": "問題", "tags": []},
        {"id": "local:math/b.pdf", "source": "local", "title": "三角関数ドリル.pdf",
         "locator": "math/b.pdf", "mime": "pdf", "bytes": 200, "modified": "2026-08-02",
         "subject": "数学", "kind": "問題", "tags": []},
    ],
}


def mutate(fn):
    d = copy.deepcopy(BASE)
    fn(d)
    return d


def _set_count(d, n):
    d["sources"][0]["count"] = n


MUTATIONS = [
    ("schema が違う",            lambda d: d.__setitem__("schema", 2)),
    ("登録 0 件",                lambda d: (d.__setitem__("items", []), _set_count(d, 0))),
    ("必須キー欠落 (title)",     lambda d: d["items"][0].pop("title")),
    ("型違反 (tags が文字列)",   lambda d: d["items"][0].__setitem__("tags", "英語")),
    ("id 重複",                  lambda d: d["items"][1].__setitem__("id", d["items"][0]["id"])),
    ("本文の混入 (長い文字列)",  lambda d: d["items"][0].__setitem__("title", "あ" * 400)),
    ("個人あて資料 (面談記録)",  lambda d: d["items"][0].__setitem__("title", "面談記録_1学期.pdf")),
    ("個人あて資料 (カルテ)",    lambda d: d["items"][0].__setitem__("locator", "karte/2026.pdf")),
    ("宛名らしき語",             lambda d: d["items"][0].__setitem__("title", FAKE_ADDRESSEE + ".pdf")),
    ("絶対パス (/Users)",        lambda d: d["items"][0].__setitem__("locator", "/Users/foo/eng/a.pdf")),
    ("絶対パス (~/)",            lambda d: d["items"][0].__setitem__("locator", "~/Desktop/a.pdf")),
    ("locator に ..",            lambda d: d["items"][0].__setitem__("locator", "../../etc/a.pdf")),
    ("未知の科目",               lambda d: d["items"][0].__setitem__("subject", "体育")),
    ("未知の種別",               lambda d: d["items"][0].__setitem__("kind", "なんか")),
    ("count がずれている",       lambda d: _set_count(d, 99)),
    ("宣言の無い出所",           lambda d: d["items"][0].__setitem__("source", "usb")),
]


def main():
    print(f"■ 検査対象 : {gate.__name__}.check_index()")
    print(f"■ 変異     : {len(MUTATIONS)} 種")

    survived = []

    # まず「正しい目録は通る」ことを確かめる。これが落ちるならゲートが厳しすぎる。
    base_v = gate.check_index(copy.deepcopy(BASE), quiet=True)
    if base_v:
        print("\n✗ VIOLATION: 正しい目録が通らない（ゲートが厳しすぎる）")
        for m in base_v:
            print(f"  - {m}")
        return 1
    print("■ 正常系   : 素の目録は PASS ✓")

    for name, fn in MUTATIONS:
        v = gate.check_index(mutate(fn), quiet=True)
        mark = "捕捉" if v else "★素通り"
        print(f"    {mark:6s} {name}" + (f"  → {v[0][:60]}" if v else ""))
        if not v:
            survived.append(name)

    if survived:
        print(f"\n✗ VIOLATION {len(survived)} 件: ゲートが素通りさせた変異がある")
        for name in survived:
            print(f"  - {name}")
        return 1
    print(f"\n✓ ALL PASS（{len(MUTATIONS)} 種の変異をすべて捕捉）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
