#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""塾長の手元にある教材を **目録 (materials/INDEX.json) に登録する**。

    # デスクトップを丸ごと棚卸し（塾長の端末で 1 回回す）
    python3 scripts/materials_index/build_index.py ~/Desktop

    # 何が登録されるかだけ見る（書き込まない）
    python3 scripts/materials_index/build_index.py ~/Desktop --dry-run

    # Google ドライブ等の一覧 JSON を取り込む（クラウド側の Claude が使う経路）
    python3 scripts/materials_index/build_index.py --import-listing drive.json \
        --source-id gdrive --label 'Google ドライブ (マイドライブ)'

■ 何のためのものか
  クラウドの Claude Code は塾長のデスクトップを見られない。そのため毎回
  「ファイルをアップして」「どこそこを探して」と指示する手間がかかっていた。
  これを消すための仕組み。**中身ではなく所在だけ**をリポジトリに置くことで、
  次のセッションの Claude は最初から「どこに何があるか」を知っている状態になる。
  結果、渡すのは実際に使う 1 本だけでよくなる。

■ ★本文は絶対に入れない（2 つの理由）
  1. このリポジトリは PUBLIC。教材本文を入れたら世界中から読め、履歴に永久に残る。
  2. 入試問題の本文は著作権法 30 条の 4 の範囲で扱う方針で、本番の
     `past_exam_upload` も**元問題のテキストを DB に保存していない**（server/main.py）。
     目録がその抜け道になってはいけない。
  したがってこのスクリプトは **ファイルを一度も開かない**。名前・サイズ・更新日時だけを見る。
  科目・種別の分類もファイル名と親フォルダ名からの推定にとどめる。

■ 個人情報
  指導メモ・面談記録・カルテ・答案 … は `check_no_pii.py` と**同じ判定**で索引から外す。
  判定を書き写すと片方だけ直されてずれるので、正典を import して使う。
  ★外した件数と理由は必ず印字する。0 件のときも「0 件除外」と出す。黙って落とすと
    「無かった」のか「見ていなかった」のか後から区別できない。

■ 保存先のパスについて
  ローカル分は **走査したフォルダからの相対パス**で持つ（`/Users/<氏名>/…` を書かないため）。
  絶対パスは目録に残さない。塾長の手元では `<root>/<rel>` で辿れる。
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX_PATH = os.path.join(ROOT, "materials", "INDEX.json")
SCHEMA = 1

# ★個人情報の判定は check_no_pii.py が正典。import して同じものを使う（写経しない）。
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import check_no_pii as pii  # noqa: E402

ADDRESSEE_RE = re.compile(pii.ADDRESSEE)

# 教材になりうる拡張子。これ以外は「教材ではない」として黙って飛ばさず件数に出す。
MATERIAL_EXT = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
                ".txt", ".md", ".csv", ".json", ".png", ".jpg", ".jpeg", ".webp",
                ".pages", ".numbers", ".key", ".epub", ".html"}

# 走査しないディレクトリ（生成物・アプリの中身・同期の作業領域）
SKIP_DIR = {".git", "node_modules", "__pycache__", ".venv", "venv", ".Trash",
            "Library", ".DS_Store", ".cache", "dist", "build", ".next"}

# ── 分類表 ────────────────────────────────────────────────────────────
# ★上から順に当てる。先に書いたものが勝つ（「模試の問題」は 模試 に寄せたい等）。
SUBJECT_RULES = [
    ("英語", r"英語|英文|英検|eiken|english|長文|語法|語彙|単語|リスニング|英作文|和訳|構文|品詞"),
    ("数学", r"数学|math|数[ⅠⅡⅢIA-C]|微分|積分|三角関数|ベクトル|確率|数列|二次関数|図形と"),
    ("国語", r"国語|現代文|古文|漢文|古典|漢字|評論|小説"),
    ("理科", r"物理|化学|生物|地学|理科"),
    ("社会", r"日本史|世界史|地理|公民|政治経済|倫理|社会科"),
    ("情報", r"情報[ⅠI]|プログラミング"),
]
# ★一次規則で科目が決まらなかったときだけ効く保険。英文法の用語は科目名を含まない
#   （「高校2年生（形容詞）宿題プリント」等）ので、これが無いと半分が "不明" に落ちる。
#   一次規則より**後**に当てるのが肝。先に当てると古文文法の「助動詞」まで英語にしてしまう。
SUBJECT_FALLBACK = [
    ("英語", r"文法|語法|時制|仮定法|不定詞|分詞構文|関係詞|受動態|完了形|助動詞|"
             r"前置詞|接続詞|動名詞|準動詞|品詞|和訳|構文|長文|空所補充"),
]
KIND_RULES = [
    ("過去問", r"過去問|入試問題|本試験|赤本|センター試験"),
    ("模試", r"模試|模擬|実戦|予想問題|プレテスト"),
    ("単語テスト", r"単語テスト|語彙テスト|単語帳|ターゲット|システム英単語|シス単"),
    ("解答解説", r"解答|解説|答案例|answer"),
    ("問題", r"問題|演習|ドリル|練習|小テスト|確認テスト|課題"),
    ("授業プリント", r"プリント|授業|講義|特講|レジュメ|テキスト|教材"),
    ("資料", r"案内|概要|料金|リスト|一覧|比較|要項|カリキュラム|シラバス"),
]
TAG_RULES = [
    (r"英検\s*準?[1-5]級", None),
    (r"共通テスト", None),
    (r"(東大|京大|阪大|名大|東北大|九大|北大|一橋|東工大|早稲田|慶應|上智|"
     r"青山|明治|立教|中央|法政|同志社|立命館|関西大|関学|MARCH|GMARCH|日東駒専)", None),
    (r"(中[1-3]|高[1-3]|小[1-6])", None),
    (r"(20[0-9]{2})\s*年?度?", None),
]


def classify(text):
    """ファイル名（＋親フォルダ名）から 科目 / 種別 / タグ を推定する。

    ★中身は読まない。読まない以上「推定」でしかないので、確信が持てないものは
      "不明" を返す。埋めたくなるが、埋めると目録が嘘をつく。
    """
    subject = next((s for s, pat in SUBJECT_RULES if re.search(pat, text, re.I)), "不明")
    if subject == "不明":
        subject = next((s for s, pat in SUBJECT_FALLBACK if re.search(pat, text, re.I)), "不明")
    kind = next((k for k, pat in KIND_RULES if re.search(pat, text, re.I)), "不明")
    tags = []
    for pat, _ in TAG_RULES:
        for m in re.finditer(pat, text, re.I):
            t = m.group(0).strip()
            if t and t not in tags:
                tags.append(t)
    return subject, kind, tags


def pii_reason(path_like):
    """個人あて資料なら理由を返す。索引に載せてよいなら None。"""
    if pii.BAD_NAME.search(path_like):
        return "個人あて資料の語（指導メモ・面談・カルテ・答案 等）"
    for m in ADDRESSEE_RE.finditer(path_like):
        if not pii._is_generic_addressee(m):
            return f"宛名らしき語（{m.group('nm')}〜）"
    return None


def scan_dir(root, source_id, label):
    """ローカルフォルダを走査して目録エントリを作る。ファイルは開かない。"""
    items, excluded, skipped_ext = [], [], 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR and not d.startswith(".")]
        for fn in filenames:
            if fn.startswith("."):
                continue
            ext = os.path.splitext(fn)[1].lower()
            if ext not in MATERIAL_EXT:
                skipped_ext += 1
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            reason = pii_reason(rel)
            if reason:
                # ★ファイル名そのものは記録しない。記録したら除外の意味がない。
                excluded.append((os.path.dirname(rel) or ".", reason))
                continue
            try:
                st = os.stat(full)
            except OSError as e:
                excluded.append((rel, f"stat 失敗: {e.__class__.__name__}"))
                continue
            subject, kind, tags = classify(rel)
            items.append({
                "id": f"{source_id}:{rel}",
                "source": source_id,
                "title": fn,
                "locator": rel,
                "mime": ext.lstrip("."),
                "bytes": st.st_size,
                "modified": datetime.fromtimestamp(st.st_mtime, timezone.utc).strftime("%Y-%m-%d"),
                "subject": subject,
                "kind": kind,
                "tags": tags,
            })
    return items, excluded, skipped_ext


def load_listing(path, source_id):
    """一覧 JSON（title/locator/mime/bytes/modified）を目録エントリに変換する。"""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    items, excluded = [], []
    for e in raw:
        title = e["title"]
        reason = pii_reason(title)
        if reason:
            excluded.append(("(一覧)", reason))
            continue
        subject, kind, tags = classify(title)
        items.append({
            "id": f"{source_id}:{e.get('key') or e['locator']}",
            "source": source_id,
            "title": title,
            "locator": e["locator"],
            "mime": e.get("mime", ""),
            "bytes": int(e.get("bytes") or 0),
            "modified": e.get("modified", ""),
            "subject": subject,
            "kind": kind,
            "tags": tags,
        })
    return items, excluded, 0


def merge(index, source_id, label, kind_label, items):
    """同じ source の古いエントリを**丸ごと入れ替える**（再実行が冪等になる）。"""
    index["items"] = [i for i in index["items"] if i.get("source") != source_id]
    index["items"].extend(items)
    index["items"].sort(key=lambda i: (i["source"], i["subject"], i["title"]))
    index["sources"] = [s for s in index.get("sources", []) if s.get("id") != source_id]
    index["sources"].append({
        "id": source_id, "label": label, "kind": kind_label,
        "scanned_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "count": len(items),
    })
    index["sources"].sort(key=lambda s: s["id"])
    return index


def main():
    ap = argparse.ArgumentParser(description="教材の目録を作る（本文は入れない）")
    ap.add_argument("directory", nargs="?", help="走査するフォルダ（例: ~/Desktop）")
    ap.add_argument("--import-listing", help="一覧 JSON を取り込む（Drive 等）")
    ap.add_argument("--source-id", default=None, help="出所の識別子（既定: local / listing 時は必須）")
    ap.add_argument("--label", default=None, help="目録に出す出所の表示名")
    ap.add_argument("--dry-run", action="store_true", help="書き込まずに結果だけ出す")
    args = ap.parse_args()

    if not args.directory and not args.import_listing:
        ap.error("走査するフォルダか --import-listing のどちらかが要る")

    if args.import_listing:
        source_id = args.source_id or "listing"
        label = args.label or os.path.basename(args.import_listing)
        kind_label = "listing"
        items, excluded, skipped_ext = load_listing(args.import_listing, source_id)
        target = args.import_listing
    else:
        root = os.path.abspath(os.path.expanduser(args.directory))
        if not os.path.isdir(root):
            print(f"✗ フォルダが無い: {root}")
            return 1
        source_id = args.source_id or "local"
        # ★表示名にホームの絶対パス（＝ユーザ名）を出さない
        label = args.label or root.replace(os.path.expanduser("~"), "~")
        kind_label = "local"
        items, excluded, skipped_ext = scan_dir(root, source_id, label)
        target = label

    # ── 何を見たかを必ず印字する ──────────────────────────────────
    print(f"■ 走査対象 : {target}")
    print(f"■ 出所 id  : {source_id}   表示名: {label}")
    print(f"■ 登録     : {len(items)} 件")
    print(f"■ 対象外   : 教材でない拡張子 {skipped_ext} 件 / 個人情報で除外 {len(excluded)} 件")
    for where, reason in excluded:
        print(f"    - {where} … {reason}")
    if items:
        by_subject, by_kind = {}, {}
        for i in items:
            by_subject[i["subject"]] = by_subject.get(i["subject"], 0) + 1
            by_kind[i["kind"]] = by_kind.get(i["kind"], 0) + 1
        print("■ 科目別   : " + " / ".join(f"{k} {v}" for k, v in sorted(by_subject.items())))
        print("■ 種別     : " + " / ".join(f"{k} {v}" for k, v in sorted(by_kind.items())))
    if not items:
        print("✗ 1 件も登録できなかった。走査先か拡張子の指定を確認すること。")
        return 1

    if args.dry_run:
        print("\n(--dry-run のため書き込んでいない)")
        return 0

    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = {"schema": SCHEMA, "note": "所在のみ。本文は入れない（PUBLIC リポジトリ・著作権）。",
                 "sources": [], "items": []}
    index = merge(index, source_id, label, kind_label, items)
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\n✓ 書き出した: {os.path.relpath(INDEX_PATH, ROOT)}  （全 {len(index['items'])} 件）")
    print("  次: python3 scripts/materials_index/check_materials_index.py で検査してからコミット")
    return 0


if __name__ == "__main__":
    sys.exit(main())
