#!/usr/bin/env python3
"""コース価格 同期チェック (billing integrity hardening)

カード払い自己登録のコース単価は 2 ファイルで二重管理されており、ズレると
「保護者が見た価格」と「実際にカードから引き落とす金額」が食い違う = 請求事故になる:

  payment/courses.json          … フロント表示価格 (保護者が見る)
  api/register-subscribe.py     … COURSES / OPTIONS dict (サーバ側・実課金額の計算元)

このスクリプトは全 id について
  - courses.json の price == register-subscribe.py の price
  - name が一致
  - 片方にしか無い id が存在しない (courses ⇄ COURSES, options ⇄ OPTIONS)
を検証し、1 つでもズレていれば exit 1 で大きく失敗する。

サーバ側は source の regex parse ではなく実際の COURSES / OPTIONS dict を
import して照合する (= 実際に請求される値そのものを検証する)。

使い方:
    cd ai-juku-system
    python3 scripts/check_course_price_sync.py

Exit code:
  0  : 全 id で price / name / 存在 が一致
  1  : 不一致を検出 (請求事故リスク・要修正)
  2  : ファイル不在 / 読み込み失敗
"""

import importlib.util
import json
import sys
from pathlib import Path

# CI ランナー等で stdout が非 UTF-8 ロケール (LANG=C 等) でも
# emoji / ¥ / 日本語の print が UnicodeEncodeError で落ちないようにする。
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
COURSES_JSON = ROOT / "payment" / "courses.json"
API_FILE = ROOT / "api" / "register-subscribe.py"

PASS = "\033[32m✅\033[0m"
FAIL = "\033[31m❌\033[0m"
BOLD = "\033[1m"
RESET = "\033[0m"


def load_json_catalog():
    """payment/courses.json → (courses[], options[])"""
    data = json.loads(COURSES_JSON.read_text(encoding="utf-8"))
    return data.get("courses", []), data.get("options", [])


def load_server_catalog():
    """register-subscribe.py の実際の COURSES / OPTIONS dict を import して取得。

    ファイル名にハイフンが含まれ通常の import 不可なので importlib で読み込む。
    当該ファイルは stdlib のみ依存・import 時の副作用なし (サーバ起動しない)。
    """
    spec = importlib.util.spec_from_file_location("register_subscribe", API_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.COURSES, module.OPTIONS


def index_by_id(entries, label, errors):
    """[{id, name, price}, ...] → {id: entry}。id 欠落・重複は errors に記録。"""
    out = {}
    for e in entries:
        cid = e.get("id")
        if cid is None:
            errors.append(f"[{label}] id の無いエントリがあります: {e}")
            continue
        if cid in out:
            errors.append(f"[{label}] id が重複しています: {cid}")
        out[cid] = e
    return out


def compare(kind, json_list, server_dict, errors):
    """kind='course' or 'option' について id 集合 / price / name を照合。"""
    json_map = index_by_id(json_list, f"courses.json {kind}", errors)
    json_ids, server_ids = set(json_map), set(server_dict)

    # 片方にしか無い id
    for cid in sorted(json_ids - server_ids):
        errors.append(f"[{kind}] '{cid}' は courses.json にあるが register-subscribe.py に無い")
    for cid in sorted(server_ids - json_ids):
        errors.append(f"[{kind}] '{cid}' は register-subscribe.py にあるが courses.json に無い")

    # 両方に存在する id の price / name (price と name は独立に判定し、両方とも報告)
    for cid in sorted(json_ids & server_ids):
        j, s = json_map[cid], server_dict[cid]
        jp, sp = j.get("price"), s.get("price")
        jn, sn = j.get("name"), s.get("name")
        entry_ok = True
        if jp is None or sp is None:
            errors.append(f"[{kind}] '{cid}' price が欠落: courses.json={jp!r} / register-subscribe.py={sp!r}")
            entry_ok = False
        elif jp != sp:
            errors.append(f"[{kind}] '{cid}' price 不一致: courses.json=¥{jp} / register-subscribe.py=¥{sp}")
            entry_ok = False
        if jn is None or sn is None:
            errors.append(f"[{kind}] '{cid}' name が欠落: courses.json={jn!r} / register-subscribe.py={sn!r}")
            entry_ok = False
        elif jn != sn:
            errors.append(f"[{kind}] '{cid}' name 不一致: courses.json={jn!r} / register-subscribe.py={sn!r}")
            entry_ok = False
        if entry_ok:
            print(f"  {PASS} [{kind}] {cid}: {jn} ¥{jp:,}")


def main():
    print("=" * 64)
    print("  💴 コース価格 同期チェック (courses.json ⇄ register-subscribe.py)")
    print("=" * 64)

    missing = [p for p in (COURSES_JSON, API_FILE) if not p.exists()]
    if missing:
        for p in missing:
            print(f"  {FAIL} ファイルが見つかりません: {p}")
        return 2

    try:
        json_courses, json_options = load_json_catalog()
    except Exception as e:
        print(f"  {FAIL} courses.json の読み込みに失敗: {e}")
        return 2
    try:
        server_courses, server_options = load_server_catalog()
    except Exception as e:
        print(f"  {FAIL} register-subscribe.py の読み込みに失敗: {e}")
        return 2

    # sanity floor: 両側とも courses が空 = 読み込み失敗の疑い。「0 件で一致」と誤判定しない。
    if not json_courses and not server_courses:
        print(f"  {FAIL} courses カタログが両側とも空です — 読み込みに失敗している可能性があります。")
        return 2

    errors = []
    print(f"\n{BOLD}── コース (courses) ──{RESET}")
    compare("course", json_courses, server_courses, errors)
    print(f"\n{BOLD}── オプション (options) ──{RESET}")
    compare("option", json_options, server_options, errors)

    print("\n" + "=" * 64)
    if errors:
        print(f"  🔴 {FAIL} {BOLD}{len(errors)} 件の不一致を検出しました{RESET}")
        for msg in errors:
            print(f"     {FAIL} {msg}")
        print(
            "\n     courses.json (保護者が見る表示価格) と register-subscribe.py "
            "(実際にカードから引き落とす金額) がズレています。"
        )
        print("     → 2 ファイルを一致させてから commit してください。")
        return 1

    total = len(json_courses) + len(json_options)
    print(f"  🎉 {PASS} {BOLD}全 {total} 件 (コース/オプション) で price・name・id が一致{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
