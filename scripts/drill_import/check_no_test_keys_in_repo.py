#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧪 公開リポジトリに習熟度テスト・英語長文の取込ファイル (= テストの答え) が入っていないかの検査 (2026-10-15)。

    python3 scripts/drill_import/check_no_test_keys_in_repo.py      # exit 0 = 入っていない / 1 = 入っている

★このリポジトリは PUBLIC。習熟度テストの答えが 1 回でも push されると、履歴に永久に残り、生徒が先に答えを見られる。
  取込ファイルは塾長のデスクトップ (取込仕様書 docs/drill-import-spec.md の 1-10) に置き、取込スクリプトが本番の API に送る。
  seed-data にも置かない (Vercel で公開されている)。scripts/run_all_gates.py が拾って毎 push 回す (material-gates)。

見るもの (git が追跡しているファイル。git が使えなければフォルダを歩く):
  1. JSON: 形式 trillion-drill-import/v1 / trillion-blind-answers/v1 / trillion-blind-sheet/v1、または kind が proficiency_test /
     english_long のもの。scripts/drill_import/fixtures/ の中で "_fixture": true (架空の自己検査用) のものだけ許す。
  2. seed-data/*.json: subject が proficiency_test / english_long の行 (どこにあっても)。
  3. テキスト (.md .py .js .html .txt .csv .tsv): 「"kind": "proficiency_test"」と correct_choice_no の両方を含むもの。
     仕様書 (docs/drill-import-spec.md の例) と "_fixture" の印があるもの (テストの架空の例) は除く。
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIXTURE_DIR = "scripts/drill_import/fixtures/"
FORMATS = {"trillion-drill-import/v1", "trillion-blind-answers/v1", "trillion-blind-sheet/v1"}
KINDS = {"proficiency_test", "english_long"}
TEXT_EXT = {".md", ".py", ".js", ".html", ".txt", ".csv", ".tsv"}
TEXT_OK = {"docs/drill-import-spec.md"}   # 仕様書 (架空の例だけ)
WALK_SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv", "lesson-prints"}
_KIND_RE = re.compile(r'"kind"\s*:\s*"proficiency_test"')
_SUBJ_RE = re.compile(rb'"subject"\s*:\s*"(?:proficiency_test|english_long)"')


def tracked_files():
    try:
        r = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True)
        if r.returncode == 0 and r.stdout:
            return [p.decode("utf-8", "surrogateescape") for p in r.stdout.split(b"\0") if p], "git ls-files"
    except OSError:
        pass
    out = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in WALK_SKIP]
        for f in files:
            out.append(os.path.relpath(os.path.join(base, f), ROOT).replace(os.sep, "/"))
    return out, "フォルダを歩いた (git が使えない)"


def _rows_with_subject(obj):
    if isinstance(obj, dict):
        if obj.get("subject") in KINDS:
            yield obj
        for v in obj.values():
            yield from _rows_with_subject(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _rows_with_subject(v)


def main():
    files, how = tracked_files()
    bad, n_json, n_text = [], 0, 0
    for rel in sorted(files):
        full = os.path.join(ROOT, rel)
        ext = os.path.splitext(rel)[1].lower()
        if ext != ".json" and ext not in TEXT_EXT:
            continue
        try:
            with open(full, "rb") as f:
                raw = f.read()
        except OSError:
            continue        # 追跡しているが作業ツリーに無い (消した直後など)
        if ext == ".json":
            n_json += 1
            hit = (b"trillion-drill-import" in raw or b"trillion-blind" in raw or b"proficiency_test" in raw or b"english_long" in raw)
            if not hit:
                continue
            try:
                doc = json.loads(raw.decode("utf-8"))
            except ValueError:
                bad.append((rel, "JSON として読めないのに取込ファイルの印がある (中身を確かめる)"))
                continue
            if isinstance(doc, dict) and (doc.get("format") in FORMATS or doc.get("kind") in KINDS):
                if not (rel.startswith(FIXTURE_DIR) and doc.get("_fixture") is True):
                    bad.append((rel, "習熟度テスト・英語長文の取込ファイル (または盲検の記録) がリポジトリにある。デスクトップの決まったフォルダに置く"))
            if rel.startswith("seed-data/") and _SUBJ_RE.search(raw):
                rows = list(_rows_with_subject(doc))
                if rows:
                    bad.append((rel, f"seed-data に subject proficiency_test / english_long の行が {len(rows)} 件 (seed-data は公開。取込スクリプトで入れる)"))
            continue
        n_text += 1
        if rel in TEXT_OK or rel.startswith("scripts/drill_import/"):
            continue
        text = raw.decode("utf-8", "replace")
        if _KIND_RE.search(text) and "correct_choice_no" in text and "_fixture" not in text:
            bad.append((rel, "習熟度テストの中身 (kind proficiency_test と correct_choice_no) が書かれている"))
    if n_json + n_text == 0:
        print(f"✗ 検査したファイルが 0 本 ({how})。検査していないのと同じ")
        return 1
    if bad:
        print(f"✗ 公開リポジトリにテスト・長文の取込ファイルが入っている ({len(bad)} 本・{how}):")
        for rel, why in bad:
            print(f"  ✗ {rel}: {why}")
        print("  → git rm --cached で外し、ファイルはデスクトップへ (docs/drill-import-spec.md 1-10)。push 済みなら塾長に知らせる")
        return 1
    print(f"OK: 公開リポジトリに習熟度テスト・英語長文の取込ファイルは無い (JSON {n_json} 本・テキスト {n_text} 本を確認・{how})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
