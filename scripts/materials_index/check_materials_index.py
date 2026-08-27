#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""教材目録 `materials/INDEX.json` のゲート。

    python3 scripts/materials_index/check_materials_index.py          # ★既定＝目録の全件
    python3 scripts/materials_index/check_materials_index.py <file>   # 別ファイルを見る（負のテスト用）

■ この検査が守っているもの
  目録は「所在だけを PUBLIC リポジトリに置く」という前提で成立している。
  その前提が崩れる入り方が 3 つあるので、そこを機械で塞ぐ。
    1. 本文の混入   … 長い文字列が紛れ込んだら、それは所在ではなく中身
                       （PUBLIC 公開 + 入試問題の著作権。`past_exam_upload` が
                         元問題を DB に残さない方針と揃える）
    2. 個人情報     … 指導メモ・面談・答案・宛名。判定は check_no_pii.py を import
                       （写経すると片方だけ直されてずれる）
    3. 絶対パス     … `/Users/<氏名>/…` が locator に入るとユーザ名が公開される

■ 「検査したつもり」を作らないための約束
  - 目録ファイルが無ければ **FAIL**。「対象なし ALL PASS」を出さない
    （引数なしのゲートが見本を見て緑になる事故を過去にやっている）。
  - 0 件なら **FAIL**。空の目録は「調べた結果 0 件」ではなく「まだ作っていない」。
  - 何件を何のファイルで見たかを必ず印字する。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_INDEX = os.path.join(ROOT, "materials", "INDEX.json")

sys.path.insert(0, os.path.join(ROOT, "scripts"))
import check_no_pii as pii  # noqa: E402

ADDRESSEE_RE = re.compile(pii.ADDRESSEE)

MAX_FIELD_LEN = 300          # これを超える文字列は「所在」ではなく「中身」とみなす
REQUIRED = {"id": str, "source": str, "title": str, "locator": str,
            "subject": str, "kind": str, "tags": list}
KNOWN_SUBJECT = {"英語", "数学", "国語", "理科", "社会", "情報", "不明"}
KNOWN_KIND = {"過去問", "模試", "単語テスト", "解答解説", "問題",
              "授業プリント", "資料", "不明"}
ABS_PATH_RE = re.compile(r"^(/|[A-Za-z]:\\|~/)|/Users/|/home/")


def check(path):
    """ファイルを読んで check_index() に渡す。"""
    if not os.path.exists(path):
        print(f"✗ 目録が無い: {os.path.relpath(path, ROOT)}")
        print("  → 塾長の端末で `python3 scripts/materials_index/build_index.py ~/Desktop` を回して作る")
        return ["目録ファイルが存在しない"]
    with open(path, encoding="utf-8") as f:
        index = json.load(f)
    return check_index(index, os.path.relpath(path, ROOT))


def check_index(index, label="(メモリ上)", quiet=False):
    """目録そのもの（dict）を検査して違反の一覧を返す。

    ★ファイルではなく dict を受けるのは、変異テスト
      (verify_index_gate.py) が一時ファイルを書かずに済むようにするため。
      ゲート本体を副作用ゼロに保てる。
    """
    v = []                                   # 違反（1 件でもあれば exit 1）
    items = index.get("items", [])
    sources = index.get("sources", [])
    local_ids = {s["id"] for s in sources if s.get("kind") == "local"}

    if not quiet:
        print(f"■ 検査対象 : {label}")
        print(f"■ 出所     : {len(sources)} 件")
        for s in sources:
            print(f"    - {s.get('id')}  {s.get('label')}  ({s.get('kind')}, "
                  f"{s.get('count')} 件, 走査 {s.get('scanned_at')})")
        print(f"■ 登録件数 : {len(items)} 件")

    if index.get("schema") != 1:
        v.append(f"schema が 1 でない: {index.get('schema')!r}")
    if not items:
        v.append("登録 0 件（空の目録は『調べて 0 件』ではなく『まだ作っていない』）")

    seen = {}
    for i, it in enumerate(items):
        where = f"items[{i}] {it.get('title', '?')[:40]}"
        for key, typ in REQUIRED.items():
            if key not in it:
                v.append(f"{where}: 必須キー {key} が無い")
            elif not isinstance(it[key], typ):
                v.append(f"{where}: {key} の型が {typ.__name__} でない")
        if "id" in it:
            if it["id"] in seen:
                v.append(f"{where}: id が重複（先: items[{seen[it['id']]}]）")
            seen[it["id"]] = i
        # 1. 本文の混入
        for key, val in it.items():
            if isinstance(val, str) and len(val) > MAX_FIELD_LEN:
                v.append(f"{where}: {key} が {len(val)} 文字（本文の混入を疑う。上限 {MAX_FIELD_LEN}）")
        # 2. 個人情報
        probe = f"{it.get('title', '')} {it.get('locator', '')}"
        if pii.BAD_NAME.search(probe):
            v.append(f"{where}: 個人あて資料の語が入っている")
        for m in ADDRESSEE_RE.finditer(probe):
            if not pii._is_generic_addressee(m):
                v.append(f"{where}: 宛名らしき語が入っている（{m.group('nm')}〜）")
        # 3. 絶対パス（ローカル出所のみ。Drive 等の locator は URL なので対象外）
        loc = it.get("locator", "")
        if it.get("source") in local_ids and isinstance(loc, str):
            if ABS_PATH_RE.search(loc):
                v.append(f"{where}: locator が絶対パス（ユーザ名が漏れる）: {loc[:60]}")
            if ".." in loc.split("/"):
                v.append(f"{where}: locator に .. が入っている: {loc[:60]}")
        # 語彙
        if it.get("subject") not in KNOWN_SUBJECT:
            v.append(f"{where}: 未知の科目 {it.get('subject')!r}")
        if it.get("kind") not in KNOWN_KIND:
            v.append(f"{where}: 未知の種別 {it.get('kind')!r}")

    # sources の件数と実データの整合
    actual = {}
    for it in items:
        actual[it.get("source")] = actual.get(it.get("source"), 0) + 1
    for s in sources:
        if s.get("count") != actual.get(s["id"], 0):
            v.append(f"出所 {s['id']}: count={s.get('count')} だが実データは {actual.get(s['id'], 0)} 件")
    for src in actual:
        if src not in {s["id"] for s in sources}:
            v.append(f"items に出所 {src!r} があるが sources に宣言が無い")
    return v


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INDEX
    v = check(path)
    if v:
        print(f"\n✗ VIOLATION {len(v)} 件")
        for msg in v:
            print(f"  - {msg}")
        return 1
    print("\n✓ ALL PASS（所在のみ・個人情報なし・絶対パスなし）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
