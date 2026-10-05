# 進行状況 (2026-10-05: 13 カード × 30 問 = 390 問 確定・GitHub 保存済み・本番投入待ち)

## 決めたこと
- 範囲: 英文法 13 カード (塾長の選択)。各 +30 問 = 390 問。作問は 42 問/カード。
- 形式は既存の英文法プールに合わせる (6 問/行・answer 整数・unit は tag(細目))。詳細は README。

## 工程
- [x] 調査 (91 カードの棚卸し・AI 自動生成の枠・解説の型・週次プリントのタグ読み)
- [x] パイプライン (中学 v3 を英文法用に写して直す)。合成データ 13 カード × 30 で lint→盲検採点→選抜→build (2 回同一)→check→insert (偽 DB 7 通り) を通した
- [x] 作問 13 × 42 (workflow)。12 カードは 1 回で完了、助動詞は 1 回の出力上限 (64k) 超えで失敗 → 21 問ずつ 2 回に分けて書き直し
- [x] lint (12 カード 504 問・drop 0) → 盲検 3 レンズ × 7 束 (別解 0・自信なし 17 → 合格 487) → 選抜 30 × 12 = 360 (助動詞は別途)
- [x] 独立レビュー R1×2 / R2×12 / R3×4 → 適用 → 再検証 F→G→H→I→J→K→L→M (各巡の落ち 46→19→5→3→1→1→0→1)。倒置は補充作問 12 (盲検 12/12) で 30 に復帰。仮定法は補充作問 8 (盲検 8/8) で 30 (M で 1 問落ち→予備から入れ替え)。
- [x] N: 仮定法の入れ替え 1 問の最終チェック → drop 0・fix_expl 1 (用語「過去完了形」→「過去完了進行形」の訂正) を適用済み。**13 カード × 30 問 = 390 問 確定 (未コミット)。**
- [ ] 助動詞の補充作問 8 問 (blind/topup_r_grammar__5.json) は予備の積み増し用 (カードは 30 問そろっている)。使うなら `topup.py prep r_grammar 5` → 盲検 3 名 → `topup.py score r_grammar 5` (余りは surplus へ)。使わなくてもよい。
- [x] build 2 回同一 → check PASS → run_all_gates → PII ALL PASS → コミット前の 3 観点レビュー (blocker 0・should_fix 7 を反映: 押し出し判定を model で・post_check の --before 必須化・kosei_baseline.py をリポジトリへ・CI でもドリル重複検査・glob の接頭辞衝突) → commit/push
- [ ] 本番 (塾長の端末): `python3 scripts/kosei_dojo/eibunpo_v2/post_check.py --before` と `kosei_baseline.py` (scratchpad) → `railway run -s Postgres python3 scripts/kosei_dojo/eibunpo_v2/insert.py` (dry-run) → `--commit` → `post_check.py`
  基準取り (kosei_baseline.py) 2026-10-05 08:39 実施 → ~/Desktop/kosei_baseline_20261005.json。**助動詞カードは窓 50/50 で満杯、受動態 49・前置詞 48**
  (AI の古い行 '?' が 2026-08-18 のタグ付けで LIKE に当たる)。insert.py は押し出される行が AI の古い行だけなら進め、手作りなら止める (README 参照)。
