# 入試問題道場「🧒 中学生（公立高校入試 標準・弱点克服）」プール増量 v3

塾長依頼 2026-10-04「AIアプリの中学生の入試問題道場の弱点克服の問題を増やして欲しい」。
対象は `exam_questions` の `exam_id='chugaku' / eiken_grade='koukou'` (dojo-drill.html の `CHU_UNIT_PRESETS` が使うプール)。
単元カタログ `../units.json` の 61 単元に **各 24 問** (24 → 48 問。8 問セットが 6 回ぶん) を足す。
生成元 (正典) は `verified/<part>__<gi>.json`、本番に入れる行は `build/rows.json`。

## 手順 (作問から本番まで)
```bash
cd /Users/adachishouhei/Documents/GitHub/ai-juku-system
python3 scripts/chugaku_dojo/expand_v3/collect_existing.py      # 既存プールの stem → blind/ (再生成可)
#  作問エージェント (AUTHOR_SPEC.md) → drafts/<part>__<gi>.json
python3 scripts/chugaku_dojo/expand_v3/lint_drafts.py <part>    # 形式・重複・位置語を機械検査 → blind/*.blind.json / *.key.json
python3 scripts/chugaku_dojo/expand_v3/make_batches.py <part>   # 盲検の束 blind/batch_<part>_<n>.json
#  盲検エージェント 3 レンズ (SOLVER_SPEC.md) → blind/ans_<part>_{A,B,C}_<n>.json
python3 scripts/chugaku_dojo/expand_v3/score_blind.py <part>    # 3 名全員が key と一致 & confident のみ合格
python3 scripts/chugaku_dojo/expand_v3/select_verified.py <part> # 単元ごとに 24 問 → verified/ (余りは blind/surplus_*)
#  独立レビュー (同じ枠の重複・読まずに当たる癖・解説の誤り) → blind/review_<part>_*.json (stem 鍵)
python3 scripts/chugaku_dojo/expand_v3/apply_review.py <part>   # drop は余りから補充・fix_expl は解説のみ
#   fix_choice / fix_stem (選択肢・設問文の書きかえ) は盲検をやり直した版だけを渡し、--allow-choice を付けて適用する
python3 scripts/chugaku_dojo/expand_v3/build.py                 # ゲート → build/rows.json / flat.json (verified/ も位置を書き戻す)
python3 scripts/chugaku_dojo/expand_v3/check_expand_v3.py       # CI と同じ読むだけのゲート
# ── ここから本番 (塾長の端末・承認つき) ──
railway run -s Postgres python3 scripts/chugaku_dojo/expand_v3/insert.py            # dry-run
railway run -s Postgres python3 scripts/chugaku_dojo/expand_v3/insert.py --commit   # 本番投入 (冪等)
python3 scripts/chugaku_dojo/expand_v3/post_check.py --before                       # (任意) 投入前: 本番の既存がリポジトリの見積もりと合うか
python3 scripts/chugaku_dojo/expand_v3/post_check.py                                # 投入後: 公開 API で配信を確認
```
rollback: `DELETE FROM exam_questions WHERE model = 'chugaku-koukou-expand-v3';`

静的フロント (dojo-drill.html) の変更は不要 (カードは既にある)。本番反映は insert だけで届く。

## 実際に回した順番 (2026-10-04 の v3)
1. 作問 61 単元 (各 34 問・読解は本文 8 本×4 問) → lint → 盲検 3 レンズ (A 自力 / B 全肢点検 / C 計算 or Web 裏取り) → 3 名一致のみ合格 → 単元ごとに 24 問を選抜
2. 独立レビュー R1 (重複・範囲)・R2 (事実・読まずに当たる癖・解説) → `apply_review.py` (drop は予備から補充)
3. R3 (生徒の画面の目: 条件不足・表示の崩れ・解説の伝わりやすさ) → 適用
4. ★このラウンドで**入れ替えた問題と書きかえた解説だけ**を F1 (正しさ・事実)・F2 (癖・整合・重複) で再検証 (`blind/apply_log_<part>.json` の _id から検証対象の `final_<part>.json` を手で組んだ。専用スクリプトは無い)。入れ替えが出たら、その分だけまた検証 (出なくなるまで)
5. 「設問文の語が正解の選択肢にだけ入っている」機械スキャン (下記) → 本物だけ設問文を書きかえ → 盲検 3 名 + 独立チェック → `score_tells.py <part> --write` (2 回目は `--round2` も) → `apply_review.py <part> --allow-choice` で fix_stem を適用
6. `polish_display.py --apply` (表示の統一のみ) → `build.py` → `check_expand_v3.py`

## 設計の要点 / 落とし穴 (futeishi/README.md も読むこと)
- ★**選択肢を差しかえたら解説も必ず読み直す。** 2×2 に組み直した 3 問で、解説が消えた誤答 (「2√13cm は…」) を説明したまま残っていた。
  レビュー担当にも「解説が今の選択肢に無い値を説明していないか」を毎回見させる。
- ★**盲検でもレビューでも「設問文の語が正解にだけ入っている」が抜ける。** 例「花粉が入っている袋」→花粉のう、「束のように」→維管束、
  「不景気が世界中に」→世界恐慌。正解の選択肢の漢字・片仮名のうち設問文にあって誤答に無いものを数えると候補が出る (偶然の 1 字も多いので人が仕分ける)。
  直し方は設問文からその語を外す (答えと選択肢は変えない) → 盲検をやり直す。
- ★**予備から補充した問題は誰もレビューしていない。** drop のたびに入る補充問題を、次の検証に必ず回す (`apply_log`)。
- 社会・理科の事実レビューは「記憶で確認した」と返すことがある → Web 裏取りを名指しで指示する (近世の 24 問は 2 回目に Web で全件確認)。
- **bank API は `question_data LIKE '%<単元名>%'` を created_at DESC で、画面が頼んだ行数**しか返さない。
  画面 (dojo-drill.html) は `limit = min(50, agg*8)` で頼むので、ふつうの単元は 50 行、**読解 3 単元 (agg 4) は 32 行**。
  他単元の解説に単元名が書かれていると、その行が予算を食い、古い本物の行が配信から押し出される。→ 作問仕様で他単元名を禁止し、
  `build.py` が「単元名を含む行 ≤ その単元の取得行数」(`_v3lib.bank_limit`) をゲートにしている。
  `insert.py` は dry-run で見込みを出し、--commit では commit 前に同じトランザクションで数え、超えたら rollback して何も入れない。
- `insert.py` の安全装置: 最初に check_expand_v3 を回す (NG なら DB につながない)・接続に idle_in_transaction_session_timeout 60 秒 /
  lock_timeout 5 秒 (死んだ接続の idle in transaction で本番 API が止まった前例への備え)・advisory lock で同時実行を止める。
- ★**解説の接頭辞「【単元】…。正解は「…」。」を外す処理は、正解の本文に「」が入る問題で壊れていた** (2026-10-04 コミット前に発覚)。
  最短一致 `正解は「.*?」` が正解の中の最初の 」 で切れ、build のたびに正解の後ろ半分が解説の頭に 1 つずつ増えた (敬語・詩歌・文学的文章・近世の 8 問)。
  今は `_v3lib._strip_one` がかっこの対応を数える。`build.py` のゲートは「作り直しても解説が変わらない」と
  「正解の後ろ半分が頭に重複していない」を見る。`check_expand_v3.py` は rows.json の解説・本文・選択肢の並びが verified と完全一致かも見る
  (verified を直して build.py を回し忘れると CI が落ちる)。
- 道場にしかない英語カード: **過去形** は『過去形』を含む行が当たる (既存 9 行 = 時制 5・助動詞 2・be動詞 1・現在完了 1、v3 で時制 5 行が加わり 14 行)。
  unit が「過去形」で始まる小問は 0 なので unitExact は効かず、これらの単元の小問が混ざって出る。
  **未来形** は『未来形』を含む行が 0 → bank は単元で絞らず英語の新しい順 50 行を返す (全単元の混在)。どちらも v3 以前からの仕様で、
  専用の問題を作るかカードを外すかは塾長の判断 (残件)。
- 正解位置は単元ごとに md5(stem) 順で 0,1,2,3 (均等・保存順に周期を作らない)。解説は正解テキスト参照なので入れ替えても壊れない。
- 設問の同一判定は (設問文, 選択肢) の組 (`_v3lib.sig`)。lint / build / insert / post_check で同じ規則。
- 盲検の答えは **添字でなく選択肢の本文**で受け取る ([[blind-solve-index-offbyone-2026-09-23]])。レビューの指し示しも stem。
- 「読まずに当たる」(正解だけ長い・部分最多・形が 1 つだけ違う) は盲検では見えない。作問仕様 §2 と lint の警告、
  `scan_choice_convergence.converges` を build で流し、独立レビューで癖を別に見る。
- `question_data` は `ensure_ascii=False` で保存 (日本語 LIKE のため)。
- 読解単元 (英 長文読解・国 説明的文章/文学的文章) は本文ごと 1 行。本文は完全オリジナル (著作権)。
- drafts/ と build/blind.json は .gitignore (生出力・誰も読まない写し)。blind/ は `../.gitignore`。verified/ と build/rows.json・flat.json・report.json はコミットする。
  post_check.py は本番につなぐので run_all_gates の SKIP。post_check は画面と同じ行数 (読解 32 / それ以外 50) で取り、新規 24 問が全部届き本文が完全一致するかまで見る。
