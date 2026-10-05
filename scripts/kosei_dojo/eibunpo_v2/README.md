# 入試問題道場「単元別（弱点克服）」英文法 13 カード プール増量 v2

塾長依頼 2026-10-05「高校生用の入試問題道場の弱点克服の問題を増やして」→ 範囲は塾長の選択で **英文法 13 カード**から。
対象は `exam_questions` の `exam_id='daigaku' / eiken_grade='teiki'`、`part_key` は r_grammar_unit (関係詞・仮定法・時制・比較・分詞) と
r_grammar (助動詞・受動態・不定詞・動名詞・接続詞・前置詞・語法・倒置・強調) — dojo-drill.html の `UNIT_PRESETS` の英文法と 1:1。
各カードに **+30 問** (10 問セットが 3 回ぶん)。「英文法 総合」カードは r_grammar/teiki 全体の新しい順 50 行なので、直接は足さない。
生成元 (正典) は `verified/<part>__<gi>.json`、本番に入れる行は `build/rows.json`。カードのカタログは `units.json`。

## 手順 (作問から本番まで) — 中学 v3 (`scripts/chugaku_dojo/expand_v3/README.md`) と同じ工程
```bash
cd /Users/adachishouhei/Documents/GitHub/ai-juku-system
python3 scripts/kosei_dojo/eibunpo_v2/collect_existing.py      # 既存プールの設問文 → blind/ (再生成可)
#  作問エージェント (AUTHOR_SPEC.md) → drafts/<part>__<gi>.json (1 カード 42 問)
python3 scripts/kosei_dojo/eibunpo_v2/lint_drafts.py            # 形式・重複・位置語・他カード名を機械検査 → blind/*.blind.json / *.key.json
python3 scripts/kosei_dojo/eibunpo_v2/make_batches.py <part>    # 盲検の束 blind/batch_<part>_<n>.json
#  盲検エージェント 3 レンズ (SOLVER_SPEC.md) → blind/ans_<part>_{A,B,C}_<n>.json
python3 scripts/kosei_dojo/eibunpo_v2/score_blind.py <part>     # 3 名全員が key と一致 & confident のみ合格
python3 scripts/kosei_dojo/eibunpo_v2/select_verified.py <part> # カードごとに 30 問 → verified/ (余りは blind/surplus_*)
#  独立レビュー R1/R2/R3 (REVIEW_SPEC.md) → blind/review_<part>_*.json (stem 鍵)
python3 scripts/kosei_dojo/eibunpo_v2/apply_review.py <part> [--allow-choice]   # drop は余りから補充 / fix_expl / fix_unit / fix_stem・fix_choice は --allow-choice
python3 scripts/kosei_dojo/eibunpo_v2/build.py                  # ゲート → build/rows.json / flat.json (verified/ も位置を書き戻す)。2 回回して同一を確認
python3 scripts/kosei_dojo/eibunpo_v2/check_eibunpo_v2.py       # CI と同じ読むだけのゲート
# ── ここから本番 (塾長の端末・承認つき) ──
python3 scripts/kosei_dojo/eibunpo_v2/post_check.py --before                       # ★必須: 投入前の配信数を保存 (投入後の比較)
railway run -s Postgres python3 scripts/kosei_dojo/eibunpo_v2/insert.py            # dry-run (窓から押し出される行の評価も出る)
railway run -s Postgres python3 scripts/kosei_dojo/eibunpo_v2/insert.py --commit   # 本番投入 (冪等)
python3 scripts/kosei_dojo/eibunpo_v2/post_check.py                                # 公開 API で配信を確認
```
rollback: `DELETE FROM exam_questions WHERE model = 'kosei-eibunpo-expand-v2';`
静的フロント (dojo-drill.html) の変更は不要 (カードは既にある)。

## 中学 v3 と違うところ (この形式に合わせた点)
- 1 行 **6 小問** (既存の英文法プールと同じ)。`answer` は **整数** (既存に合わせる。中学は文字列)。`format_type` は無い。
- `unit` は **`<tag>(<細目>)`** (例: 関係詞(非制限用法 which))。tag は `units.json` の tag。画面の unitExact は接頭辞 (「(」の前) が filter で始まるかで絞り、
  週次の弱点プリント (`server/main.py` `_grammar_unit_rows`) は `【単元】<tag>` の文字列で引くので、解説は `【単元】<unit>。正解は「…」。` で始める
  (`_derive_question_unit` は「(」の前までを単元名として読む)。★このプリントが引くのは part_key='r_grammar' だけ (従来仕様) で、
  r_grammar_unit の 5 カード (関係詞・仮定法・時制・比較・分詞) の問題はプリントには出ない (道場のカードには出る)。
- 既存プールは `seed-data/dojo_batch4_manual.json / dojo_eibunpo_expand1_manual.json / dojo_eibunpou_precision_manual.json` (108 行 / 623 問)。
  ★本番の r_grammar 行は 2026-08-18 に `scripts/r_grammar_unit_tags/` で解説に 【単元】タグが足されている (seed は未更新) ので、
  LIKE 予算の既存行数は seed の近似より本番が多い。`~/Desktop/kosei_baseline_*.json` (`kosei_baseline.py` の結果) があれば build.py がその数で警告する (判定は insert.py)。
- 両プールとも `EXAM_QUESTION_AUTO_GENERATE_SKIP` に入っているので AI の自動補充は来ない (本番 = 手動取込だけ)。
- 単元ドリル (grammar_questions・別機能) の seed (`grammar_drill_pool_v1/v2`) の設問文も重複回避の対象にした (同じ文を 2 つの機能で出さない)。

## 設計の要点 / 落とし穴
- 中学 v3 の README の落とし穴はすべてここにも当てはまる (解説の接頭辞の取りこぼし・予備から補充した問題の再検証・Web 裏取りの名指し・build を 2 回回す)。
- 英文法で最も多い不良は **口語・米英差で許容される 2 正解** と **解説の誤った断定**。盲検 B は「英語として成立するか」だけで判定させ、C は辞書サイトで裏取りさせる。
- ★**本番の英文法 (r_grammar/teiki) プールは seed の 65 行よりずっと大きい** (2026-10-05 の基準取り `kosei_baseline.py`): 助動詞カードは
  単元名 LIKE に当たる行が **50/50 で窓が満杯**、受動態 49・前置詞 48・動名詞 45・不定詞 44・接続詞 43。出どころ不明 ('?') の行は
  r_grammar/teiki が AUTO_GENERATE_SKIP に入る前 (2026-05-13〜06-18) に AI が自動生成した行で、2026-08-18 の単元タグ付けで
  解説に『【単元】助動詞』が入り LIKE に当たるようになった。bank は `%<topic>%` の素の LIKE (コードのコメントの「【単元】<topic>」は不正確)。
  基準取りは `python3 scripts/kosei_dojo/eibunpo_v2/kosei_baseline.py` (公開 API を読むだけ・~/Desktop/kosei_baseline_<日付>.json に保存。build.py が読む)。
  → `insert.py` は上限を超えるカードで「窓から押し出される行」を created_at 順に特定し (同時刻の行は全部評価)、押し出されるのが
  AI の自動生成行 (model が `claude-sonnet-4-6` のような素のモデル名) だけなら警告して進め、手作り/取込の行 (manual2・*verified*・
  claude-max-plan・NULL など) が含まれるなら止める。★AI の行も `univ_simulated` ('teiki' など) を持つので question_data では見分けない
  (基準の出どころ 'teiki' は AI 行)。dry-run は押し出される行の id・model・日時を表示する。了承して進めるなら
  `--allow-pushout=r_grammar/助動詞,…` (カード指定) か `--allow-pushout` (全カード)。
  `build.py` は seed 近似で上限超えなら NG、本番の基準で超えるぶんは warn (判定は insert.py)。`post_check.py` は「既存 + 30」の等式
  ではなく「新規 30 問が全部届く・不一致 0・配信数が投入前 (--before で保存) より減らない」で判定する。
- 同じ基準取りで、高校の他のカードも多くが窓の上限に達している (日本史 4/5・世界史 3/5・生物 1/5・物理基礎 2/5・化学基礎 1/5・数学 数列 など)。
  AI 生成の古い行が窓を占めているので、増量の前に bank の窓を単元タグ優先にする (サーバ側) か窓を広げる改修を検討する (別件・塾長判断)。
- 「英文法 総合」は filter 無しで新しい順 50 行 → 投入直後は今回の 40 行が大半を占める (零和。以前からの仕様)。
- ★`make_batches.py` の束の掃除は glob `batch_<part>_*` だと、part 名が前方一致する別 part (r_grammar → r_grammar_unit) の束まで消す
  (2026-10-05 に盲検の解答者 21 人のうち 9 人が「束が無い」と報告。決定的に作り直して解いたので結果は有効)。番号だけに限定する正規表現に直した。
  part 名が互いの接頭辞になる組み合わせでは、ファイル名のパターンは必ず区切り文字と桁数まで書く。
- R1 (重複と範囲) は 360 問中 40 問を落とした (R1〜R3 の初回適用で入れ替えは 46 問)。最多は倒置カード 8/30 (既存プールの定番文型と同じ枠)。英文法は定番の文型が限られるので、
  作問者に「既存の設問文」だけでなく「既存の文型 (正解語+構造)」の一覧を渡し、同じ枠を避けさせるほうが落ちが少ない (次回の改善点)。
