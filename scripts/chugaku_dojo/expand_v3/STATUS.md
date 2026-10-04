# 進行状況 (2026-10-04 完了・GitHub に保存済み・本番投入待ち)

## できたもの
- 61 単元 × 24 問 = **1,464 問** (英語 312・数学 360・国語 192・理科 336・社会 264)。正典は `verified/`、本番に入れる行は `build/rows.json` (308 行)。
- `python3 build.py` と `python3 check_expand_v3.py` は PASS。正解の位置は 0/1/2/3 が 366 問ずつ。
- dojo-drill.html の 61 枚の単元カードそれぞれに、新しい問題がちょうど 24 問ずつ出ることをカードの定義から模擬して確認済み。
- `insert.py` は偽の DB で 初回 308 行 / 2 回目 0 行 (冪等) / 一部既出は 1 問単位で除外 / dry-run は書かない、を確認済み。

## 品質の工程 (実施済み)
- 盲検 3 名 (自力・全肢点検・計算 or Web 裏取り) が全員一致した問題だけを採用 (不合格 11 問)。
- 独立レビュー R1 (重複・範囲)・R2 (事実・読まずに当たる癖・解説)・R3 (生徒の画面の目)、入れ替え・書きかえ分の再検証 (F/G/H)。
  差し替え 58 問・解説の書き直し 43 問・選択肢の組み直し 5 問 (盲検やり直し済み)。
- 「設問文の語が正解の選択肢にだけ入っている」機械スキャン → 28 問の設問文を書きかえ (盲検 3 名 + 独立チェック合格)。
- 表示の統一 60 問 (`polish_display.py`)。
- コミット前の 3 観点レビュー (投入スクリプト・データと画面・リポジトリ) で blocker 0。minor を直した:
  解説の接頭辞の取りこぼしで 8 問の解説の頭に正解の後ろ半分が重複していたのを修正し、ゲートを追加 /
  平方根 1 問の √{…} を √(…) に統一 (盲検 3 名一致) / insert.py は commit 前に LIKE 予算を数えて超えたら rollback /
  読解カードの取得行数 32 をゲート・post_check に反映 / check_expand_v3 は rows.json の解説・本文・並びまで照合。
- 変更後の差分を 3 観点で再レビュー (blocker 0)。insert.py に安全装置 (先に CI ゲート・idle_in_transaction/lock の timeout・
  同時実行の lock・dry-run で予算の見込み)、check_expand_v3 に subject・設問文の完全一致・id 重複、post_check に --before と再試行。

## 残っていること
1. **本番投入 (塾長の端末で)**:
   ```
   cd ~/Documents/GitHub/ai-juku-system
   python3 scripts/chugaku_dojo/expand_v3/post_check.py --before                       # (任意) 投入前の基準確認
   railway run -s Postgres python3 scripts/chugaku_dojo/expand_v3/insert.py            # dry-run (書かない・単元名 LIKE の見込みも出る)
   railway run -s Postgres python3 scripts/chugaku_dojo/expand_v3/insert.py --commit   # 本番投入
   python3 scripts/chugaku_dojo/expand_v3/post_check.py                                # 公開 API で配信を確認
   ```
   戻し方: `DELETE FROM exam_questions WHERE model = 'chugaku-koukou-expand-v3';`
2. 英語の「過去形」「未来形」カードは専用問題が無い (v3 以前から)。作るかカードを外すかは塾長の判断 (README 参照)。
