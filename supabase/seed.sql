-- =============================================================================
-- 動作確認用の中身 (仮定法の演習 1 冊 + 未公開の模試 1 冊)
--
--   `supabase db reset` が自動で流す標準の置き場所。
--   ホスト側の Supabase に入れたいときは SQL Editor に貼るか
--       psql "<プロジェクトの接続文字列>" -f supabase/seed.sql
--
-- ★ 本番プロジェクトに `supabase db push` しても seed は流れない (ローカル専用の扱い)。
-- ★ 何度流しても増えない (on conflict do nothing)。
-- ★ 講師アカウントはここでは作らない (auth.users はサインアップで作るため)。
--   created_by は NULL のまま。誰が作ったかを入れたければ後から update する。
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1 冊目: 公開済み。生徒に見える
-- -----------------------------------------------------------------------------
insert into public.books (id, title, subject, level, pdf_path, page_count,
                          time_limit_sec, is_published)
values ('5eed0001-5eed-4eed-8eed-5eed00000001',
        '英文法 仮定法 演習5', 'grammar', '標準',
        null,          -- PDF は使わない (question_data に設問を持つ JSON 問題)
        null, 600, true)
on conflict (id) do nothing;

-- -----------------------------------------------------------------------------
-- 2 冊目: 未公開。生徒には見えない / PDF も落とせない
-- -----------------------------------------------------------------------------
insert into public.books (id, title, subject, level, pdf_path, page_count,
                          time_limit_sec, is_published)
values ('5eed0002-5eed-4eed-8eed-5eed00000002',
        '第4回 英検準1級模試 (準備中)', 'eiken', '難関',
        'books/eiken-junichi-04.pdf', 24, 5400, false)
on conflict (id) do nothing;

-- -----------------------------------------------------------------------------
-- 設問 (合計 8 点)
-- -----------------------------------------------------------------------------
-- 解説は CLAUDE.md の英語 4 セクション形式:
--   ## 🎯 コアイメージ → ## 🔬 文構造分析 → ## 📍 本文の根拠 → ## ❌ 誤答 NG 理由
insert into public.questions
    (id, book_id, number, page, answer_type, choice_count, correct_answer,
     accepted_answers, points, unit_tag, question_data, explanation)
values
-- 第1問 --------------------------------------------------------------------
('5eedaa01-5eed-4eed-8eed-5eed0000aa01', '5eed0001-5eed-4eed-8eed-5eed00000001',
 1, null, 'choice', 4, '3', null, 1, 'SUBJ-01',
 jsonb_build_object(
   'stem', 'If I (      ) you, I would accept that offer right away.',
   'choices', jsonb_build_array('am', 'was', 'were', 'will be')),
'## 🎯 コアイメージ
「今の事実に反すること」を言うときは、時制をひとつ後ろへずらして**距離**を作る。
現在の話なのに過去形を使うのは「これは現実ではない」という合図。

## 🔬 文構造分析
`If + S + 動詞の過去形 …, S + would + 動詞の原形 …` が仮定法過去の骨格。
主節が `would accept`（助動詞の過去形 + 原形）なので、if 節も過去形にそろえる。
be 動詞は主語が I でも **were** を使うのが原則。

## 📍 本文の根拠
主節の `I **would** accept that offer` が決め手。would がある以上、
if 節を現在形のままにはできない。

## ❌ 誤答 NG 理由
- **am** … 直説法。「実際に私があなたである」場合の形で、事実に反する仮定を表せない。
- **was** … 口語では見かけるが、仮定法過去の be は were が原則。4 択では were を選ぶ。
- **will be** … 条件を表す副詞節の中では未来を will で表さない。'),

-- 第2問 --------------------------------------------------------------------
('5eedaa02-5eed-4eed-8eed-5eed0000aa02', '5eed0001-5eed-4eed-8eed-5eed00000001',
 2, null, 'choice', 4, '4', null, 2, 'SUBJ-02',
 jsonb_build_object(
   'stem', 'If she had started ten minutes earlier, she (      ) the last train.',
   'choices', jsonb_build_array('catches', 'caught', 'would catch', 'would have caught')),
'## 🎯 コアイメージ
**過去**の事実に反することを言うときは、もう一段だけ時制を後ろへずらす。
「あのとき〜していたら、〜だったのに」は済んでしまった話なので、
助動詞のうしろも `have + 過去分詞` になる。

## 🔬 文構造分析
`If + S + had + 過去分詞 …, S + would have + 過去分詞 …` が仮定法過去完了の骨格。
if 節が `had started` と過去完了になっている時点で、主節は would have + 過去分詞で受ける。

## 📍 本文の根拠
if 節の `she **had started** ten minutes earlier` が過去完了。
実際には「10 分早く出発しなかった」＝過去の事実に反する仮定。

## ❌ 誤答 NG 理由
- **catches** … 直説法の現在形。過去の反実仮想に使えない。
- **caught** … 単なる過去形。「実際に乗った」ことになり、if 節と矛盾する。
- **would catch** … 仮定法**過去**の主節。現在の反実仮想の形なので、
  `had started` という過去完了と時制が噛み合わない。'),

-- 第3問 --------------------------------------------------------------------
('5eedaa03-5eed-4eed-8eed-5eed0000aa03', '5eed0001-5eed-4eed-8eed-5eed00000001',
 3, null, 'short', null, 'could', array['could speak'], 2, 'SUBJ-03',
 jsonb_build_object(
   'stem', 'I wish I (      ) speak French fluently.  （can を適切な形にして入れなさい）'),
'## 🎯 コアイメージ
`wish` は「そうでない今」を嘆く動詞。願っている中身は**現実ではない**ので、
wish のうしろは必ず時制をひとつ後ろへずらす。

## 🔬 文構造分析
`I wish + S + 動詞の過去形 …` で「〜ならいいのに」。
ここは can が助動詞なので、過去形の **could** にする。

## 📍 本文の根拠
`I **wish** I … speak French fluently.` の wish が合図。
「実際には流暢に話せない」ことを前提にした文。

## ❌ 誤答 NG 理由
- **can** … 直説法。「実際に話せる」ことになり、wish と矛盾する。
- **will be able to** … wish のうしろに未来の will は置けない。
- **had been able to** … それは「あのとき話せたらよかったのに」という過去の話。
  この文は「今」話せないことを嘆いている。'),

-- 第4問 --------------------------------------------------------------------
('5eedaa04-5eed-4eed-8eed-5eed0000aa04', '5eed0001-5eed-4eed-8eed-5eed00000001',
 4, null, 'choice', 4, '2', null, 1, 'SUBJ-04',
 jsonb_build_object(
   'stem', '(      ) it not been for your advice, I would have made a serious mistake.',
   'choices', jsonb_build_array('If', 'Had', 'Were', 'Should')),
'## 🎯 コアイメージ
仮定法の if は**省略できる**。省略すると、代わりに助動詞が主語の前に出てくる（倒置）。
`If it had not been for …` → `**Had** it not been for …`。

## 🔬 文構造分析
`Had + S + 過去分詞 …` は if 節の倒置形。
`if it had not been for A`（A が無かったら）が元の形で、If を消して had を前に出した。
主節が `would have made` と仮定法過去完了なので、if 節も過去完了で受ける。

## 📍 本文の根拠
`… I **would have made** a serious mistake.` が主節。
would have + 過去分詞なので、空所は過去完了側でなければならない。

## ❌ 誤答 NG 理由
- **If** … If を残すなら `If it had not been for` の語順。`If it not been` にはならない。
- **Were** … `Were it not for …`（今 A が無かったら）は仮定法**過去**。
  主節の would have made と時制が合わない。
- **Should** … `Should it …` は「万一〜なら」で、これから起きることの話。'),

-- 第5問 --------------------------------------------------------------------
('5eedaa05-5eed-4eed-8eed-5eed0000aa05', '5eed0001-5eed-4eed-8eed-5eed00000001',
 5, null, 'short', null, 'does not rain', array['doesn''t rain'], 2, 'SUBJ-05',
 jsonb_build_object(
   'stem', 'If it (      ) tomorrow, we will go hiking.  （not rain を適切な形にして入れなさい）'),
'## 🎯 コアイメージ
仮定法とまぎらわしいが、これは**ただの条件**。
「明日雨が降らない」は十分ありうる話で、事実に反していない。だから時制をずらさない。

## 🔬 文構造分析
`If + S + 現在形 …, S + will + 原形 …` が直説法の条件文。
条件を表す副詞節の中では、未来のことでも**現在形**で書く（if it will not rain とはしない）。
主語 it は三人称単数なので `does not rain` / `doesn''t rain`。

## 📍 本文の根拠
主節が `we **will** go hiking` と will。
would ではないので、この文は反実仮想ではなく単なる条件。

## ❌ 誤答 NG 理由
- **will not rain** … 条件の副詞節の中で will は使わない。
- **did not rain** … 仮定法過去の形。主節が will なので噛み合わない。
- **do not rain** … 主語 it は三人称単数。does が要る。')
on conflict (id) do nothing;

-- 未公開ブックの設問 (生徒には見えないことの確認用)
insert into public.questions
    (id, book_id, number, page, answer_type, choice_count, correct_answer,
     points, unit_tag, explanation)
values ('5eedbb01-5eed-4eed-8eed-5eed0000bb01', '5eed0002-5eed-4eed-8eed-5eed00000002',
        1, 3, 'choice', 4, '1', 1, 'EIK-01',
        '未公開ブックの設問。生徒からは student_questions に出てこない。')
on conflict (id) do nothing;
