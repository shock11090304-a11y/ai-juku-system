#!/bin/zsh
# 刷り上がりと講師用メモを Desktop の教材フォルダへ届ける。
# ★build.py と check.py（PDF照合）を通してから実行すること。
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="/Users/adachishouhei/Desktop/📚 教材/国語/04_共通テスト/古文_第4問_演習問題集_基礎から本番_202609"
mkdir -p "$DEST"
cp "$HERE/out/共通テスト形式_古文_第4問_演習問題集_基礎から本番まで_問題編.pdf" "$DEST/"
cp "$HERE/out/共通テスト形式_古文_第4問_演習問題集_基礎から本番まで_解答解説編.pdf" "$DEST/"
cp "$HERE/out/講師用メモ_本文の典拠と校訂の記録.txt" "$DEST/"
ls -la "$DEST"
