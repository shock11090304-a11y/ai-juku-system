# 手元の教材の目録 (materials index)

塾長のデスクトップ / Google ドライブにある教材の **所在だけ**を `materials/INDEX.json` に持つ仕組み。

## 何を解決するのか

クラウドの Claude Code は塾長のデスクトップを見られない（コンテナの中で動いており
`~/Desktop` が存在しない）。そのため毎回

- 「このファイルをアップして」
- 「〇〇の教材どこにあるか探して」

を人手でやる必要があった。目録をリポジトリに置くと、**次のセッションの Claude は最初から
「どこに何があるか」を知っている状態**で始まる。結果、実際に使う 1 本だけを渡せばよくなる。

## ★入れてよいもの / 絶対に入れないもの

| | |
|---|---|
| 入れる | ファイル名・所在・サイズ・更新日・推定した科目/種別/タグ |
| **入れない** | **教材の本文**、個人あて資料（指導メモ・面談・カルテ・答案 …） |

理由は 2 つ。

1. **このリポジトリは PUBLIC**。本文を入れれば世界中から読め、履歴に永久に残る。
2. 入試問題の本文は著作権法 30 条の 4 の範囲で扱う方針で、本番の `past_exam_upload` も
   **元問題のテキストを DB に保存していない**（`server/main.py`）。目録がその抜け道になってはいけない。

`build_index.py` は **ファイルを一度も開かない**（名前と `stat` だけ）。分類も名前からの推定に留める。
個人情報の判定は `scripts/check_no_pii.py` を **import して**使う（写経すると片方だけ直されてずれる）。

## 使い方

### デスクトップを棚卸しする（塾長の端末で）

```bash
python3 scripts/materials_index/build_index.py ~/Desktop --dry-run   # 何が載るか見るだけ
python3 scripts/materials_index/build_index.py ~/Desktop             # 目録に登録
python3 scripts/materials_index/check_materials_index.py             # 検査してからコミット
```

- 同じ出所を再実行すると、その出所の分を**丸ごと入れ替える**（冪等）。増えた教材は再実行するだけ。
- 除外したファイルは件数と理由を必ず印字する。0 件のときも「0 件除外」と出す。

### Google ドライブ側を更新する（クラウドの Claude が回す）

Drive コネクタで一覧を取り、`{key,title,locator,mime,bytes,modified}` の JSON にして渡す。

```bash
python3 scripts/materials_index/build_index.py --import-listing drive.json \
    --source-id gdrive --label 'Google ドライブ (マイドライブ)'
```

## 検査

| ファイル | 見るもの |
|---|---|
| `check_materials_index.py` | 目録の中身（本文混入・個人情報・絶対パス・スキーマ・件数整合） |
| `verify_index_gate.py` | **上のゲートが本当に落とすか**を 16 種の変異で確認（副作用ゼロ・メモリ上のみ） |

どちらも `scripts/run_all_gates.py` が再帰探索で拾うので、CI (`material-gates.yml`) でも回る。

`check_materials_index.py` は **目録が無ければ FAIL、0 件でも FAIL**。
「対象なし ALL PASS」を出さない（引数なしのゲートが見本を見て緑になる事故を過去にやっている）。
