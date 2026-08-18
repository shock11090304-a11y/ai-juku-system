# daigaku/r_grammar 【単元】タグ整備 (2026-08-18)

週次弱点プリントの英語選定 (`server/main.py::_grammar_unit_rows`) は
**explanation/stem 中のリテラル `【単元】<単元名>`** を SQL LIKE で引き、
大問内の**全小問**が当該単元のときだけ①タグ一致経路で配信する。
タグの正典は `_derive_question_unit` (q.unit > 解説/設問の【単元】 > fallback)。

## タグ語彙 (21 語・この文字列以外を書かない)

時制 / 助動詞 / 受動態 / 不定詞 / 動名詞 / 分詞 / 分詞構文 / 比較 / 関係詞 / 仮定法 /
接続詞 / 前置詞 / 倒置 / 否定 / 疑問詞 / 話法 / 強調 / 名詞・代名詞 / 冠詞 / 形容詞・副詞 / 語法

- However/No matter how 等の複合関係詞の譲歩 = **関係詞** (弱点記録の既存規約
  「関係詞(複合関係副詞however 譲歩+形容詞)」に合わせる。接続詞にしない)
- 選択肢が前置詞 4 択の熟語 (be good at 等) = **前置詞** / 選択肢が動詞変化形 = **動名詞** など、
  「正解と誤答を分ける知識」で分類する

## 新規行の取込時 (推奨: タグ漏れを作らない)

seed の各小問 explanation 冒頭に `【単元】<単元名>` を 1 行入れる (+ `unit` フィールドも同値)。
タグ無しでも配信は止まらない (②全文 LIKE へフォールバック) が、単元一致精度が
27% 水準に落ちる。漏れは `scripts/health_check/prod_healthcheck.py` の
`r_grammar_unit_tags` チェックと、週次 cron result の `unit_tag_picks` /
`like_fallback_picks` 比率で検知できる。

## 既存行への一括付与 (2026-08-18 に 308 行へ適用済み)

1. 未タグ小問を抽出 → LLM 二重盲分類 (Sonnet/Opus 独立) + ルール分類で突合、
   不一致は人裁定 (2026-08-18 実績: 723 小問で 94% 一致・21 件裁定)
2. ラベル JSON (`labels_20260818.json` が実績) を作り、dry-run で件数照合:
   `railway run -s Postgres python3 scripts/r_grammar_unit_tags/apply_unit_tags.py <labels.json>`
3. `--apply` で書込み。**変更前の行は exam_questions_archive に退避される**
   (2026-08-18 適用分: `replacement_batch_id='r_grammar_unit_tags_20260818'`)
4. 検証: choices/answer/passage が不変で explanation/stem がタグ分だけ変化したことを
   archive と突合 (適用時は 308 行/748 小問で異常 0)

## ロールバック

```sql
UPDATE exam_questions q SET question_data = a.question_data
FROM exam_questions_archive a
WHERE a.original_id = q.id AND a.replacement_batch_id = 'r_grammar_unit_tags_20260818';
```
