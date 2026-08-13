#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""migrations/*.sql と seed.sql を 1 本にまとめた `bundle.sql` を作る。

    python3 supabase/build_bundle.py            # 作り直す
    python3 supabase/build_bundle.py --check    # 中身が最新かだけ見る (ゲートが使う)

★ なぜ要るか
  Supabase / Vercel のダッシュボードは塾長のブラウザからしか触れない
  (この作業環境はプロキシのポリシーで supabase.com に出られない)。
  ターミナルを使わずに済ませるには「SQL Editor に 1 回貼るだけ」の形が要る。
  ファイルを何本も順番に貼るのは、順番を間違えたときに気づきにくい。

★ 生成物だが **コミットする**。貼る対象そのものなので、リポジトリに無いと意味がない。
★ 古いまま置いておくのがいちばん危ないので、
  scripts/english_schema/check_schema.py が「中身が最新か」を毎回検査する。
  migration を足したり直したりしたら、このスクリプトを回し直すこと。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "bundle.sql")

# 各ファイルの一行説明。★ここに無いファイルがあると build が止まる。
#   見出しを手書きの一覧にしていたら、migration を足したときに更新し忘れて
#   「§5 の 1 本が一覧から抜け、seed の番号もずれる」が実際に起きた (2026-08-14)。
#   一覧は下の build() が **実ファイルから組み立てる**ので、もう手で数えなくてよい。
DESCRIPTIONS = {
    "english_learning_core":           "テーブル 7 本・制約・インデックス・updated_at トリガ",
    "english_learning_rls":            "権限と RLS ポリシー・auth.users 連携・生徒向け view",
    "english_learning_storage":        "問題 PDF の bucket (book-pdfs) と読み書き権限",
    "english_learning_grading":        "採点 RPC submit_attempt() と、点数を直接書けなくする権限",
    "english_learning_retake_fix":     "再受験中に正解が見えてしまう穴の修正",
    "english_learning_strokes_format": "手書きストロークの形 (設計書 §5)・正規化座標だけを通す",
    "english_learning_strokes_missing_keys":
                                       "手書きの検査でキーの欠落を弾けていなかったのを直す",
    "seed":                            "動作確認用の中身 (仮定法の演習 1 冊 5 問 + 未公開の模試 1 冊)",
}

HEADER = """-- =============================================================================
-- 英語学習アプリ — Supabase に貼る用のひとまとめ
--
--   ★ これは **生成物**。直接編集しない。
--     元は supabase/migrations/*.sql と supabase/seed.sql。
--     直したら `python3 supabase/build_bundle.py` で作り直す
--     (中身が古いと scripts/english_schema/check_schema.py が落ちる)。
--
-- ■ 使い方
--   Supabase ダッシュボード → SQL Editor → 全部貼って Run。
--   ターミナルも Supabase CLI も要らない。
--
-- ■ 中身 (この順に流れる)
{contents}
--
--   ★ {seed_no} (seed) は動作確認用。本番に入れるときは末尾の seed 部分を消して貼ること。
--
-- ■ 何度貼っても安全
--   全部 if not exists / or replace / drop … if exists / on conflict do nothing。
--   2 回貼ってもデータは増えないし、エラーにもならない。
-- =============================================================================

"""

SEP = """

-- ##############################################################################
-- ## {n}. {title}
-- ##    ({src})
-- ##############################################################################

"""


def parts():
    """(番号, 説明, リポジトリ内の相対パス, 実パス) を流す順に返す。"""
    mig = os.path.join(HERE, "migrations")
    out = []
    for i, f in enumerate(sorted(x for x in os.listdir(mig) if x.endswith(".sql")), 1):
        key = f.split("_", 1)[1].rsplit(".", 1)[0]        # 20260813010000_xxx.sql → xxx
        out.append((i, key, os.path.join("supabase", "migrations", f),
                    os.path.join(mig, f)))
    seed = os.path.join(HERE, "seed.sql")
    if os.path.exists(seed):
        out.append((len(out) + 1, "seed", os.path.join("supabase", "seed.sql"), seed))
    return out


def describe(key):
    if key not in DESCRIPTIONS:
        raise SystemExit(
            f"✗ {key} の説明が DESCRIPTIONS にありません。\n"
            f"  supabase/build_bundle.py の DESCRIPTIONS に 1 行足してください "
            f"(見出しの一覧はここから組み立てています)。")
    return DESCRIPTIONS[key]


def build():
    ps = parts()
    contents = "\n".join(f"--   {n}. {describe(key)}" for n, key, _rel, _p in ps)
    seed_no = next((n for n, key, _r, _p in ps if key == "seed"), len(ps))
    buf = [HEADER.format(contents=contents, seed_no=seed_no)]
    for n, key, rel, path in ps:
        buf.append(SEP.format(n=n, title=describe(key), src=rel))
        with open(path, encoding="utf-8") as f:
            buf.append(f.read().rstrip() + "\n")
    return "".join(buf)


def main():
    want = build()
    check = "--check" in sys.argv
    have = None
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            have = f.read()

    if check:
        if have is None:
            print("✗ supabase/bundle.sql が無い (python3 supabase/build_bundle.py で作る)")
            return 1
        if have != want:
            print("✗ supabase/bundle.sql が元の SQL と食い違っている "
                  "(python3 supabase/build_bundle.py で作り直す)")
            return 1
        print(f"[ok] supabase/bundle.sql は最新 ({len(parts())} 本ぶん / "
              f"{len(want.splitlines())} 行)")
        return 0

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(want)
    print(f"[ok] supabase/bundle.sql ({len(parts())} 本ぶん / "
          f"{len(want.splitlines())} 行 / {len(want.encode()) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
