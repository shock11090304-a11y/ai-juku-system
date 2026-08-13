-- =============================================================================
-- 英語学習アプリ: スキーマの振る舞いテスト
--
--   使い捨ての DB に 00_local_stubs.sql → migrations/*.sql を流した後にこれを流す。
--   入口は python3 scripts/english_schema/check_schema.py (自分で DB を作って消す)。
--
-- ★ 各検査は「通ってはいけないものが通ったら raise exception」で書く。
--   psql -v ON_ERROR_STOP=1 で流すので、落ちた行が失敗した検査そのもの。
-- ★ RLS の検査は `set local role authenticated` + request.jwt.claims で
--   Supabase の PostgREST が作るのと同じ状態を再現している。
--   ★ RLS はテーブル所有者には効かない。postgres のまま select して
--     「見えた」と言っても何も検査していないことになる (この種の空振りを防ぐため、
--     下の検査は必ず set local role してから数える)。
-- =============================================================================

\set ON_ERROR_STOP on
\set QUIET on
set client_min_messages to notice;

-- -----------------------------------------------------------------------------
-- 下ごしらえ
-- -----------------------------------------------------------------------------
insert into auth.users (id, email, raw_user_meta_data) values
    ('aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'teacher@example.test',
     '{"display_name": "講師テスト"}'),
    ('bbbbbbb1-bbbb-4bbb-8bbb-bbbbbbbbbbb1', 'student1@example.test',
     '{"display_name": "生徒1"}'),
    ('bbbbbbb2-bbbb-4bbb-8bbb-bbbbbbbbbbb2', 'student2@example.test', '{}');

-- 講師の任命 (JWT 無し = service_role 相当なので guard を素通りする)
update public.profiles set role = 'teacher'
 where id = 'aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1';

insert into public.books (id, title, subject, level, pdf_path, page_count,
                          time_limit_sec, is_published, created_by) values
    ('ccccccc1-cccc-4ccc-8ccc-ccccccccccc1', '英文法 仮定法 演習20', 'grammar', '標準',
     'books/kateiho.pdf', 8, 1200, true,  'aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1'),
    ('ccccccc2-cccc-4ccc-8ccc-ccccccccccc2', '第3回 英検準1級模試', 'eiken', '難関',
     'books/eiken3.pdf', 24, 5400, false, 'aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1');

insert into public.questions (id, book_id, number, page, answer_type, choice_count,
                              correct_answer, accepted_answers, points, unit_tag, explanation) values
    ('ddddddd1-dddd-4ddd-8ddd-ddddddddddd1', 'ccccccc1-cccc-4ccc-8ccc-ccccccccccc1',
     1, 2, 'choice', 4, '3', null, 1, 'SV-01', '## 🎯 コアイメージ\n仮定法過去は…'),
    ('ddddddd2-dddd-4ddd-8ddd-ddddddddddd2', 'ccccccc1-cccc-4ccc-8ccc-ccccccccccc1',
     2, 3, 'short', null, 'were', array['Were', 'was not'], 2, 'REL-03', '解説2'),
    ('ddddddd3-dddd-4ddd-8ddd-ddddddddddd3', 'ccccccc2-cccc-4ccc-8ccc-ccccccccccc2',
     1, 1, 'choice', 4, '1', null, 1, 'EIK-01', '未公開ブックの設問');

insert into public.attempts (id, book_id, user_id, started_at, submitted_at,
                             total_score, max_score, elapsed_sec) values
    ('eeeeeee1-eeee-4eee-8eee-eeeeeeeeeee1', 'ccccccc1-cccc-4ccc-8ccc-ccccccccccc1',
     'bbbbbbb1-bbbb-4bbb-8bbb-bbbbbbbbbbb1',
     now() - interval '1 hour', now() - interval '40 min', 1, 3, 1200),
    ('eeeeeee2-eeee-4eee-8eee-eeeeeeeeeee2', 'ccccccc1-cccc-4ccc-8ccc-ccccccccccc1',
     'bbbbbbb2-bbbb-4bbb-8bbb-bbbbbbbbbbb2', now(), null, null, null, null);

-- S1 は Q1 だけ解答して提出済み (Q2 は白紙)
insert into public.answers (attempt_id, question_id, user_answer, is_correct, time_spent_sec) values
    ('eeeeeee1-eeee-4eee-8eee-eeeeeeeeeee1', 'ddddddd1-dddd-4ddd-8ddd-ddddddddddd1',
     '3', true, 45);

insert into public.annotations (attempt_id, page, strokes) values
    ('eeeeeee1-eeee-4eee-8eee-eeeeeeeeeee1', 2,
     '{"v":1,"strokes":[{"c":"#1b2233","w":0.003,"p":[[0.10,0.10],[0.20,0.20]]}]}');

insert into public.review_items (user_id, question_id, wrong_count, tags) values
    ('bbbbbbb1-bbbb-4bbb-8bbb-bbbbbbbbbbb1', 'ddddddd2-dddd-4ddd-8ddd-ddddddddddd2',
     2, array['仮定法', '語形変化']),
    ('bbbbbbb2-bbbb-4bbb-8bbb-bbbbbbbbbbb2', 'ddddddd1-dddd-4ddd-8ddd-ddddddddddd1', 1, null);

insert into storage.objects (bucket_id, name) values
    ('book-pdfs', 'books/kateiho.pdf'),
    ('book-pdfs', 'books/eiken3.pdf');

\echo '--- 下ごしらえ完了 ---'

-- =============================================================================
-- A. 制約 — 「入れてはいけない行」が入らないこと
-- =============================================================================
do $$
declare
    n_ok int := 0;
begin
    -- A1: choice なのに選択肢が 1 つ
    begin
        insert into public.questions (book_id, number, answer_type, choice_count, correct_answer)
        values ('ccccccc1-cccc-4ccc-8ccc-ccccccccccc1', 901, 'choice', 1, '1');
        raise exception '[fail] A1 choice_count=1 の設問が入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- A2: choice なのに選択肢が 11
    begin
        insert into public.questions (book_id, number, answer_type, choice_count, correct_answer)
        values ('ccccccc1-cccc-4ccc-8ccc-ccccccccccc1', 902, 'choice', 11, '1');
        raise exception '[fail] A2 choice_count=11 の設問が入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- A3: 正解番号が選択肢数を超えている (4択なのに正解が 5)
    begin
        insert into public.questions (book_id, number, answer_type, choice_count, correct_answer)
        values ('ccccccc1-cccc-4ccc-8ccc-ccccccccccc1', 903, 'choice', 4, '5');
        raise exception '[fail] A3 4択で correct_answer=5 の設問が入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- A4: choice なのに正解が数字でない
    --     ★ ここは「弾かれること」だけでなく **弾かれ方** を見ている。
    --       check_violation でなく 22P02 (invalid input syntax for type integer) で
    --       落ちるとこの handler では捕まらず、検査が失敗する。
    --       CHECK を plpgsql 関数に出しているのはこの 1 件のため (core migration の注参照)。
    begin
        insert into public.questions (book_id, number, answer_type, choice_count, correct_answer)
        values ('ccccccc1-cccc-4ccc-8ccc-ccccccccccc1', 904, 'choice', 4, 'あ');
        raise exception '[fail] A4 correct_answer=あ の choice 設問が入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- A5: short なのに choice_count が入っている
    begin
        insert into public.questions (book_id, number, answer_type, choice_count, correct_answer)
        values ('ccccccc1-cccc-4ccc-8ccc-ccccccccccc1', 905, 'short', 4, 'were');
        raise exception '[fail] A5 short + choice_count=4 が入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- A6: 正解が空文字
    begin
        insert into public.questions (book_id, number, answer_type, correct_answer)
        values ('ccccccc1-cccc-4ccc-8ccc-ccccccccccc1', 906, 'short', '   ');
        raise exception '[fail] A6 correct_answer が空白だけの設問が入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- A7: 別解の配列に NULL 要素 (採点が静かに落ちる形)
    begin
        insert into public.questions (book_id, number, answer_type, correct_answer, accepted_answers)
        values ('ccccccc1-cccc-4ccc-8ccc-ccccccccccc1', 907, 'short', 'were',
                array['Were', null]);
        raise exception '[fail] A7 accepted_answers に NULL 要素が入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- A8: 同じブックに同じ設問番号
    begin
        insert into public.questions (book_id, number, answer_type, choice_count, correct_answer)
        values ('ccccccc1-cccc-4ccc-8ccc-ccccccccccc1', 1, 'choice', 4, '1');
        raise exception '[fail] A8 (book_id, number) が重複した設問が入ってしまった';
    exception when unique_violation then n_ok := n_ok + 1;
    end;

    -- A9: 表示名が空
    begin
        insert into auth.users (id, email, raw_user_meta_data)
        values ('fffffff1-ffff-4fff-8fff-fffffffffff1', 'blank@example.test',
                '{"display_name": "   "}');
        -- handle_new_user が空白を弾いて email のローカル部に落とすので、ここは通るのが正しい。
        -- 直接 profiles に空を入れる方を検査する。
        delete from public.profiles where id = 'fffffff1-ffff-4fff-8fff-fffffffffff1';
        insert into public.profiles (id, display_name)
        values ('fffffff1-ffff-4fff-8fff-fffffffffff1', '  ');
        raise exception '[fail] A9 display_name が空白だけの profile が入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- A10: 未知の role
    begin
        update public.profiles set role = 'admin'
         where id = 'bbbbbbb1-bbbb-4bbb-8bbb-bbbbbbbbbbb1';
        raise exception '[fail] A10 role=admin が入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- A11: 未知の subject
    begin
        insert into public.books (title, subject) values ('リスニング教材', 'listening');
        raise exception '[fail] A11 subject=listening が入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- A12: 提出時刻が開始より前
    begin
        insert into public.attempts (book_id, user_id, started_at, submitted_at)
        values ('ccccccc1-cccc-4ccc-8ccc-ccccccccccc1',
                'bbbbbbb1-bbbb-4bbb-8bbb-bbbbbbbbbbb1',
                now(), now() - interval '1 hour');
        raise exception '[fail] A12 submitted_at < started_at の attempt が入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- A13: 同じ attempt の同じページに 2 行
    begin
        insert into public.annotations (attempt_id, page, strokes)
        values ('eeeeeee1-eeee-4eee-8eee-eeeeeeeeeee1', 2, '{"v":1,"strokes":[]}');
        raise exception '[fail] A13 (attempt_id, page) が重複した annotation が入ってしまった';
    exception when unique_violation then n_ok := n_ok + 1;
    end;

    -- A14: 配点 0
    begin
        insert into public.questions (book_id, number, answer_type, correct_answer, points)
        values ('ccccccc1-cccc-4ccc-8ccc-ccccccccccc1', 908, 'short', 'x', 0);
        raise exception '[fail] A14 points=0 の設問が入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    if n_ok <> 14 then
        raise exception '[fail] A: 想定 14 件のうち % 件しか検査できていない', n_ok;
    end if;
    raise notice '[ok] A 制約 14 件';
end
$$;

-- =============================================================================
-- B. トリガ
-- =============================================================================
do $$
declare
    v_name text;
    v_role text;
    v_before timestamptz;
    v_after  timestamptz;
begin
    -- B1: auth.users を作ると profiles が自動でできる。表示名は meta から。
    select display_name, role into v_name, v_role
      from public.profiles where id = 'bbbbbbb1-bbbb-4bbb-8bbb-bbbbbbbbbbb1';
    if v_name is distinct from '生徒1' then
        raise exception '[fail] B1 display_name が meta から入っていない: %', v_name;
    end if;
    if v_role is distinct from 'student' then
        raise exception '[fail] B1 既定の role が student でない: %', v_role;
    end if;

    -- B2: display_name の meta が無いときは email のローカル部に落ちる
    select display_name into v_name
      from public.profiles where id = 'bbbbbbb2-bbbb-4bbb-8bbb-bbbbbbbbbbb2';
    if v_name is distinct from 'student2' then
        raise exception '[fail] B2 表示名のフォールバックが効いていない: %', v_name;
    end if;

    -- B3: annotations を更新すると updated_at が DB 側で進む
    select updated_at into v_before from public.annotations
     where attempt_id = 'eeeeeee1-eeee-4eee-8eee-eeeeeeeeeee1' and page = 2;
    perform pg_sleep(0.01);
    update public.annotations
       set strokes = '{"v":1,"strokes":[{"c":"#ef4444","w":0.003,"p":[[0.01,0.01]]}]}',
           updated_at = '2000-01-01'::timestamptz   -- 嘘の時刻を送りつけても
     where attempt_id = 'eeeeeee1-eeee-4eee-8eee-eeeeeeeeeee1' and page = 2;
    select updated_at into v_after from public.annotations
     where attempt_id = 'eeeeeee1-eeee-4eee-8eee-eeeeeeeeeee1' and page = 2;
    if v_after <= v_before then
        raise exception '[fail] B3 updated_at が進んでいない (% → %)', v_before, v_after;
    end if;

    raise notice '[ok] B トリガ 3 件';
end
$$;

-- =============================================================================
-- C. RLS — 生徒 (S1)
-- =============================================================================
do $$
declare
    n int;
    v_correct text;
    v_expl    text;
begin
    perform set_config('request.jwt.claims',
        '{"sub":"bbbbbbb1-bbbb-4bbb-8bbb-bbbbbbbbbbb1","role":"authenticated"}', true);
    execute 'set local role authenticated';

    -- C1: 自分の attempt しか見えない
    select count(*) into n from public.attempts;
    if n <> 1 then raise exception '[fail] C1 生徒に attempts が % 件見えている (期待 1)', n; end if;

    -- C2: 他人の answers が見えない
    select count(*) into n from public.answers;
    if n <> 1 then raise exception '[fail] C2 生徒に answers が % 件見えている (期待 1)', n; end if;

    -- C3: 他人の手書きが見えない
    select count(*) into n from public.annotations;
    if n <> 1 then raise exception '[fail] C3 生徒に annotations が % 件見えている (期待 1)', n; end if;

    -- C4: 他人の復習キューが見えない
    select count(*) into n from public.review_items;
    if n <> 1 then raise exception '[fail] C4 生徒に review_items が % 件見えている (期待 1)', n; end if;

    -- C5: 他人の profile が見えない
    select count(*) into n from public.profiles;
    if n <> 1 then raise exception '[fail] C5 生徒に profiles が % 件見えている (期待 1)', n; end if;

    -- C6: 未公開ブックが見えない (公開 1 冊だけ)
    select count(*) into n from public.books;
    if n <> 1 then raise exception '[fail] C6 生徒に books が % 件見えている (期待 1)', n; end if;

    -- C7: ★ questions テーブルは 1 行も見えない (正解が同じ行にあるため)
    select count(*) into n from public.questions;
    if n <> 0 then
        raise exception '[fail] C7 生徒が questions を % 件読めている — 正解が漏れる', n;
    end if;

    -- C8: view 経由なら公開ブックの設問が見える (未公開ブックの分は出ない)
    select count(*) into n from public.student_questions;
    if n <> 2 then
        raise exception '[fail] C8 student_questions が % 件 (期待 2 = 公開ブックの設問だけ)', n;
    end if;

    -- C9: 提出済みで解答した設問は正解と解説が見える
    select correct_answer, explanation into v_correct, v_expl
      from public.student_questions where id = 'ddddddd1-dddd-4ddd-8ddd-ddddddddddd1';
    if v_correct is distinct from '3' or v_expl is null then
        raise exception '[fail] C9 提出済みの設問で正解が見えない (correct=%)', v_correct;
    end if;

    -- C10: ★ 未解答の設問は正解も解説も NULL
    select correct_answer, explanation into v_correct, v_expl
      from public.student_questions where id = 'ddddddd2-dddd-4ddd-8ddd-ddddddddddd2';
    if v_correct is not null or v_expl is not null then
        raise exception '[fail] C10 未解答なのに正解が見えている (correct=%)', v_correct;
    end if;

    -- C11: ★ attempts の直接 UPDATE 権限をそもそも配っていない (点数の捏造を閉じる)
    --      提出も点数も submit_attempt() 経由だけ。提出済み・未提出を問わず書けない。
    begin
        update public.attempts set total_score = 999
         where id = 'eeeeeee1-eeee-4eee-8eee-eeeeeeeeeee1';
        raise exception '[fail] C11 生徒が attempts を直接 UPDATE できてしまった';
    exception when insufficient_privilege then null;
    end;

    -- C12: 提出済みの attempt に解答を足せない
    begin
        insert into public.answers (attempt_id, question_id, user_answer)
        values ('eeeeeee1-eeee-4eee-8eee-eeeeeeeeeee1',
                'ddddddd2-dddd-4ddd-8ddd-ddddddddddd2', 'were');
        raise exception '[fail] C12 提出済みの答案に解答を足せてしまった';
    exception when insufficient_privilege then null;
    end;

    -- C13: 他人名義の attempt を作れない
    begin
        insert into public.attempts (book_id, user_id)
        values ('ccccccc1-cccc-4ccc-8ccc-ccccccccccc1',
                'bbbbbbb2-bbbb-4bbb-8bbb-bbbbbbbbbbb2');
        raise exception '[fail] C13 他人名義の attempt を作れてしまった';
    exception when insufficient_privilege then null;
    end;

    -- C14: 未公開ブックの attempt を作れない
    begin
        insert into public.attempts (book_id, user_id)
        values ('ccccccc2-cccc-4ccc-8ccc-ccccccccccc2',
                'bbbbbbb1-bbbb-4bbb-8bbb-bbbbbbbbbbb1');
        raise exception '[fail] C14 未公開ブックの attempt を作れてしまった';
    exception when insufficient_privilege then null;
    end;

    -- C15: ブックを作れない
    begin
        insert into public.books (title, subject) values ('生徒が作った本', 'grammar');
        raise exception '[fail] C15 生徒がブックを作れてしまった';
    exception when insufficient_privilege then null;
    end;

    -- C16: 他人の answers を書き換えられない
    update public.answers set user_answer = 'ハック'
     where attempt_id = 'eeeeeee2-eeee-4eee-8eee-eeeeeeeeeee2';
    get diagnostics n = row_count;
    if n <> 0 then raise exception '[fail] C16 他人の解答を書き換えられた'; end if;

    -- C17: ★ 自分を講師に昇格できない
    begin
        update public.profiles set role = 'teacher'
         where id = 'bbbbbbb1-bbbb-4bbb-8bbb-bbbbbbbbbbb1';
        raise exception '[fail] C17 生徒が自分を講師に昇格できてしまった';
    exception when insufficient_privilege then null;
    end;

    -- C18: 表示名の変更はできる (正常系。締めすぎていないことの確認)
    update public.profiles set display_name = '生徒1改'
     where id = 'bbbbbbb1-bbbb-4bbb-8bbb-bbbbbbbbbbb1';
    get diagnostics n = row_count;
    if n <> 1 then raise exception '[fail] C18 自分の表示名を変えられない'; end if;

    -- C19: 未提出の attempt には解答を書ける (正常系)
    perform set_config('request.jwt.claims',
        '{"sub":"bbbbbbb2-bbbb-4bbb-8bbb-bbbbbbbbbbb2","role":"authenticated"}', true);
    insert into public.answers (attempt_id, question_id, user_answer, time_spent_sec)
    values ('eeeeeee2-eeee-4eee-8eee-eeeeeeeeeee2',
            'ddddddd1-dddd-4ddd-8ddd-ddddddddddd1', '2', 30);

    -- C20: is_correct は自分では書けない (正誤の自己申告を閉じる)
    begin
        update public.answers set is_correct = true
         where attempt_id = 'eeeeeee2-eeee-4eee-8eee-eeeeeeeeeee2';
        raise exception '[fail] C20 生徒が is_correct を書けてしまった';
    exception when insufficient_privilege then null;
    end;

    reset role;
    raise notice '[ok] C 生徒の RLS 20 件';
end
$$;

-- =============================================================================
-- D. RLS — 講師
-- =============================================================================
do $$
declare
    n int;
begin
    perform set_config('request.jwt.claims',
        '{"sub":"aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1","role":"authenticated"}', true);
    execute 'set local role authenticated';

    select count(*) into n from public.attempts;
    if n <> 2 then raise exception '[fail] D1 講師に attempts が % 件 (期待 2)', n; end if;

    select count(*) into n from public.answers;
    if n <> 2 then raise exception '[fail] D2 講師に answers が % 件 (期待 2)', n; end if;

    select count(*) into n from public.annotations;
    if n <> 1 then raise exception '[fail] D3 講師に annotations が % 件 (期待 1)', n; end if;

    select count(*) into n from public.questions;
    if n <> 3 then raise exception '[fail] D4 講師に questions が % 件 (期待 3)', n; end if;

    select count(*) into n from public.books;
    if n <> 2 then raise exception '[fail] D5 講師に books が % 件 (期待 2 = 未公開込み)', n; end if;

    select count(*) into n from public.profiles;
    if n <> 3 then raise exception '[fail] D6 講師に profiles が % 件 (期待 3)', n; end if;

    insert into public.books (id, title, subject, is_published, created_by)
    values ('ccccccc9-cccc-4ccc-8ccc-ccccccccccc9', '講師が作った本', 'reading', false,
            'aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1');

    insert into public.questions (book_id, number, answer_type, choice_count, correct_answer)
    values ('ccccccc9-cccc-4ccc-8ccc-ccccccccccc9', 1, 'choice', 4, '2');

    -- D7: 講師は生徒を講師に昇格できる
    update public.profiles set role = 'teacher'
     where id = 'bbbbbbb2-bbbb-4bbb-8bbb-bbbbbbbbbbb2';
    get diagnostics n = row_count;
    if n <> 1 then raise exception '[fail] D7 講師が role を変更できない'; end if;
    -- 後続の検査に影響しないよう戻す
    update public.profiles set role = 'student'
     where id = 'bbbbbbb2-bbbb-4bbb-8bbb-bbbbbbbbbbb2';

    reset role;
    raise notice '[ok] D 講師の RLS 9 件';
end
$$;

-- =============================================================================
-- E. 未ログイン (anon) — 何も触れないこと
-- =============================================================================
do $$
declare
    n int;
begin
    perform set_config('request.jwt.claims', '', true);
    execute 'set local role anon';

    begin
        select count(*) into n from public.profiles;
        raise exception '[fail] E1 anon が profiles を読めてしまった (% 件)', n;
    exception when insufficient_privilege then null;
    end;

    begin
        select count(*) into n from public.answers;
        raise exception '[fail] E2 anon が answers を読めてしまった (% 件)', n;
    exception when insufficient_privilege then null;
    end;

    begin
        select count(*) into n from public.student_questions;
        raise exception '[fail] E3 anon が student_questions を読めてしまった (% 件)', n;
    exception when insufficient_privilege then null;
    end;

    begin
        select count(*) into n from public.books;
        raise exception '[fail] E4 anon が books を読めてしまった (% 件)', n;
    exception when insufficient_privilege then null;
    end;

    reset role;
    raise notice '[ok] E anon 4 件';
end
$$;

-- =============================================================================
-- F. Storage — 未公開ブックの PDF が受験前に落とせないこと
-- =============================================================================
do $$
declare
    n int;
begin
    perform set_config('request.jwt.claims',
        '{"sub":"bbbbbbb1-bbbb-4bbb-8bbb-bbbbbbbbbbb1","role":"authenticated"}', true);
    execute 'set local role authenticated';

    select count(*) into n from storage.objects where bucket_id = 'book-pdfs';
    if n <> 1 then
        raise exception '[fail] F1 生徒に PDF が % 件見えている (期待 1 = 公開ブックの分だけ)', n;
    end if;

    select count(*) into n from storage.objects where name = 'books/eiken3.pdf';
    if n <> 0 then
        raise exception '[fail] F2 未公開ブックの PDF が生徒に見えている';
    end if;

    perform set_config('request.jwt.claims',
        '{"sub":"aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1","role":"authenticated"}', true);
    select count(*) into n from storage.objects where bucket_id = 'book-pdfs';
    if n <> 2 then
        raise exception '[fail] F3 講師に PDF が % 件しか見えていない (期待 2)', n;
    end if;

    reset role;
    raise notice '[ok] F Storage 3 件';
end
$$;

-- =============================================================================
-- G. 参照整合性 — 消したときに何が起きるか (README「参照整合性の効き方」の裏取り)
-- =============================================================================
do $$
declare
    n int;
begin
    -- G1: 受験履歴のあるブックは消せない (attempts / answers が参照している)
    begin
        delete from public.books where id = 'ccccccc1-cccc-4ccc-8ccc-ccccccccccc1';
        raise exception '[fail] G1 受験履歴のあるブックが消せてしまった';
    exception when foreign_key_violation then null;
    end;

    -- G2: 一度も受験されていないブックは設問ごと消える (cascade)
    delete from public.books where id = 'ccccccc9-cccc-4ccc-8ccc-ccccccccccc9';
    select count(*) into n from public.questions
     where book_id = 'ccccccc9-cccc-4ccc-8ccc-ccccccccccc9';
    if n <> 0 then raise exception '[fail] G2 ブックを消しても設問が % 件残った', n; end if;

    -- G3: attempt を消すと解答と手書きが一緒に消える (cascade)
    insert into public.attempts (id, book_id, user_id)
    values ('eeeeeee9-eeee-4eee-8eee-eeeeeeeeeee9',
            'ccccccc1-cccc-4ccc-8ccc-ccccccccccc1',
            'bbbbbbb1-bbbb-4bbb-8bbb-bbbbbbbbbbb1');
    insert into public.answers (attempt_id, question_id, user_answer)
    values ('eeeeeee9-eeee-4eee-8eee-eeeeeeeeeee9',
            'ddddddd2-dddd-4ddd-8ddd-ddddddddddd2', 'was');
    insert into public.annotations (attempt_id, page, strokes)
    values ('eeeeeee9-eeee-4eee-8eee-eeeeeeeeeee9', 1, '{"v":1,"strokes":[]}');
    delete from public.attempts where id = 'eeeeeee9-eeee-4eee-8eee-eeeeeeeeeee9';
    select count(*) into n from public.answers
     where attempt_id = 'eeeeeee9-eeee-4eee-8eee-eeeeeeeeeee9';
    if n <> 0 then raise exception '[fail] G3 attempt を消しても解答が残った'; end if;
    select count(*) into n from public.annotations
     where attempt_id = 'eeeeeee9-eeee-4eee-8eee-eeeeeeeeeee9';
    if n <> 0 then raise exception '[fail] G3 attempt を消しても手書きが残った'; end if;

    -- G4: ★ 受験履歴のある生徒は auth.users から消せない
    --     (profiles は cascade で落ちるが attempts が参照して止まる)
    --     退会処理を書くときはここで詰まる。README に手順を書いてある。
    begin
        delete from auth.users where id = 'bbbbbbb1-bbbb-4bbb-8bbb-bbbbbbbbbbb1';
        raise exception '[fail] G4 受験履歴のある生徒が消せてしまった (履歴が孤児になる)';
    exception when foreign_key_violation then null;
    end;

    -- G5: 履歴の無い生徒は消せて、profiles も一緒に落ちる
    insert into auth.users (id, email) values
        ('fffffff2-ffff-4fff-8fff-fffffffffff2', 'ghost@example.test');
    delete from auth.users where id = 'fffffff2-ffff-4fff-8fff-fffffffffff2';
    select count(*) into n from public.profiles
     where id = 'fffffff2-ffff-4fff-8fff-fffffffffff2';
    if n <> 0 then raise exception '[fail] G5 auth.users を消しても profile が残った'; end if;

    raise notice '[ok] G 参照整合性 5 件';
end
$$;

-- =============================================================================
-- H. 採点 (submit_attempt) — 生徒が自分では書けない値をサーバ側が書くこと
-- =============================================================================
-- 生徒2 の attempt2 は未提出で、解答が 1 件だけ入っている:
--   Q1 (4択・正解 '3'・1点) に '2' と答えた → 誤答
--   Q2 (短答・2点) は白紙 (answers 行なし)
-- ブック1 の満点は 1 + 2 = 3 点。
do $$
declare
    r record;
    v_correct boolean;
    n int;
begin
    perform set_config('request.jwt.claims',
        '{"sub":"bbbbbbb2-bbbb-4bbb-8bbb-bbbbbbbbbbb2","role":"authenticated"}', true);
    execute 'set local role authenticated';

    -- H1: 提出できて、点数がサーバ側で計算される
    select * into r from public.submit_attempt('eeeeeee2-eeee-4eee-8eee-eeeeeeeeeee2');
    if r.total_score <> 0 then
        raise exception '[fail] H1 誤答なのに % 点ついた', r.total_score;
    end if;
    if r.max_score <> 3 then
        raise exception '[fail] H1 満点が % (期待 3 = 1点 + 2点・白紙も分母)', r.max_score;
    end if;
    if r.correct_count <> 0 or r.answered_count <> 1 or r.question_count <> 2 then
        raise exception '[fail] H1 集計がおかしい (correct=% answered=% questions=%)',
            r.correct_count, r.answered_count, r.question_count;
    end if;

    -- H2: is_correct がサーバ側で埋まっている
    select is_correct into v_correct from public.answers
     where attempt_id = 'eeeeeee2-eeee-4eee-8eee-eeeeeeeeeee2';
    if v_correct is not false then
        raise exception '[fail] H2 is_correct が埋まっていない (%)', v_correct;
    end if;

    -- H3: 誤答が復習キューに積まれる。既にある行は wrong_count が増える
    --     (下ごしらえで 生徒2 × Q1 が wrong_count=1 で入っている → 2 になるはず)
    select wrong_count into n from public.review_items
     where user_id = 'bbbbbbb2-bbbb-4bbb-8bbb-bbbbbbbbbbb2'
       and question_id = 'ddddddd1-dddd-4ddd-8ddd-ddddddddddd1';
    if n <> 2 then
        raise exception '[fail] H3 wrong_count が % (期待 2 = 既存 1 + 今回の誤答)', n;
    end if;

    -- H4: 二重提出できない
    begin
        perform public.submit_attempt('eeeeeee2-eeee-4eee-8eee-eeeeeeeeeee2');
        raise exception '[fail] H4 同じ答案を 2 回提出できてしまった';
    exception when insufficient_privilege then null;
    end;

    -- H5: 提出したので、解答した設問の正解が view に出る
    select correct_answer into v_correct from (
        select (correct_answer is not null) as correct_answer
          from public.student_questions
         where id = 'ddddddd1-dddd-4ddd-8ddd-ddddddddddd1') s;
    if v_correct is not true then
        raise exception '[fail] H5 提出後なのに正解が伏せられたまま';
    end if;

    -- H6: 他人の答案は採点できない
    begin
        perform public.submit_attempt('eeeeeee1-eeee-4eee-8eee-eeeeeeeeeee1');
        raise exception '[fail] H6 他人の答案を提出できてしまった';
    exception when insufficient_privilege then null;
    end;

    reset role;
    raise notice '[ok] H 採点 6 件';
end
$$;

-- =============================================================================
-- I. 受験フロー (PDF 運用) と、再受験中に正解を伏せること
-- =============================================================================
-- ★ ここは supabase/demo/index.html が投げるのと同じ形の SQL を流している。
--   列単位の grant を足したので、「RLS は通るのに grant で落ちる」形が
--   机上で見落としやすい。実際の形で確かめる。
-- ★ I2 は「前は見えていた」ことを先に確認してから伏せる。順序を逆にすると、
--   もともと見えていなかっただけの状態でも通ってしまう (空振りする検査になる)。
do $$
declare
    n int;
    v_correct text;
begin
    perform set_config('request.jwt.claims',
        '{"sub":"bbbbbbb1-bbbb-4bbb-8bbb-bbbbbbbbbbb1","role":"authenticated"}', true);
    execute 'set local role authenticated';

    -- I1: 前提 — 生徒1 は既に attempt1 を提出済みなので、いま Q1 の正解は見えている
    select correct_answer into v_correct from public.student_questions
     where id = 'ddddddd1-dddd-4ddd-8ddd-ddddddddddd1';
    if v_correct is distinct from '3' then
        raise exception '[fail] I1 前提が崩れている: 提出済みなのに正解が見えない (%)', v_correct;
    end if;

    -- I2: 受験を開始する (attempts への insert)
    insert into public.attempts (id, book_id, user_id)
    values ('eeeeeee5-eeee-4eee-8eee-eeeeeeeeeee5',
            'ccccccc1-cccc-4ccc-8ccc-ccccccccccc1',
            'bbbbbbb1-bbbb-4bbb-8bbb-bbbbbbbbbbb1');

    -- I3: ★ 受験を始めた瞬間、さっきまで見えていた正解が伏せられる (再受験の穴)
    select correct_answer into v_correct from public.student_questions
     where id = 'ddddddd1-dddd-4ddd-8ddd-ddddddddddd1';
    if v_correct is not null then
        raise exception '[fail] I3 再受験中なのに正解が見えている (%)', v_correct;
    end if;

    -- I4: 解答用紙の行をまとめて作る。★ デモは列を 4 つだけ送る (is_correct は送らない)
    insert into public.answers (attempt_id, question_id, user_answer, time_spent_sec)
    select 'eeeeeee5-eeee-4eee-8eee-eeeeeeeeeee5', q.id, null, 0
      from public.student_questions q
     where q.book_id = 'ccccccc1-cccc-4ccc-8ccc-ccccccccccc1';
    get diagnostics n = row_count;
    if n <> 2 then
        raise exception '[fail] I4 解答欄が % 行しか作れない (期待 2)', n;
    end if;

    -- I5: 解答を書く (user_answer だけの update)
    update public.answers set user_answer = '3', time_spent_sec = 40
     where attempt_id = 'eeeeeee5-eeee-4eee-8eee-eeeeeeeeeee5'
       and question_id = 'ddddddd1-dddd-4ddd-8ddd-ddddddddddd1';
    get diagnostics n = row_count;
    if n <> 1 then raise exception '[fail] I5 解答を保存できない'; end if;

    -- I6: 手書きの upsert (insert … on conflict do update)。列の grant で落ちないこと
    insert into public.annotations (attempt_id, page, strokes)
    values ('eeeeeee5-eeee-4eee-8eee-eeeeeeeeeee5', 1, '{"v":1,"strokes":[]}'::jsonb)
    on conflict (attempt_id, page) do update
       set strokes = excluded.strokes, attempt_id = excluded.attempt_id, page = excluded.page;
    insert into public.annotations (attempt_id, page, strokes)
    values ('eeeeeee5-eeee-4eee-8eee-eeeeeeeeeee5', 1,
            '{"v":1,"strokes":[{"c":"#1b2233","w":0.003,"p":[[0.01,0.02]]}]}'::jsonb)
    on conflict (attempt_id, page) do update
       set strokes = excluded.strokes, attempt_id = excluded.attempt_id, page = excluded.page;
    select jsonb_array_length(strokes -> 'strokes') into n from public.annotations
     where attempt_id = 'eeeeeee5-eeee-4eee-8eee-eeeeeeeeeee5' and page = 1;
    if n <> 1 then raise exception '[fail] I6 手書きの upsert が効いていない (% 本)', n; end if;

    -- I7: 採点して提出
    perform public.submit_attempt('eeeeeee5-eeee-4eee-8eee-eeeeeeeeeee5');

    -- I8: 提出し終わったので正解がまた見える
    select correct_answer into v_correct from public.student_questions
     where id = 'ddddddd1-dddd-4ddd-8ddd-ddddddddddd1';
    if v_correct is distinct from '3' then
        raise exception '[fail] I8 提出後も正解が返らない (%)', v_correct;
    end if;

    -- I9: 提出したので手書きはもう保存できない (答案ごと凍結)
    begin
        insert into public.annotations (attempt_id, page, strokes)
        values ('eeeeeee5-eeee-4eee-8eee-eeeeeeeeeee5', 2, '{"v":1,"strokes":[]}'::jsonb);
        raise exception '[fail] I9 提出後に手書きを保存できてしまった';
    exception when insufficient_privilege then null;
    end;

    reset role;
    raise notice '[ok] I 受験フローと再受験 9 件';
end
$$;

-- =============================================================================
-- J. 手書きストロークの形 (§5) — 正規化座標だけを通すこと
-- =============================================================================
-- ★ ここが緩いと「書いた端末以外では位置を復元できないデータ」が溜まる。
--   溜まってからでは基準サイズが無いので変換できない = 直せない種類の事故なので、
--   書き込みの時点で止める。
do $$
declare
    n_ok int := 0;
    v_att uuid := 'eeeeeee2-eeee-4eee-8eee-eeeeeeeeeee2';   -- 生徒2 の attempt
begin
    -- 正常系を先に確かめる (これが通らないと以下の「弾けた」に意味が無い)
    insert into public.annotations (attempt_id, page, strokes)
    values (v_att, 7, '{"v":1,"strokes":[{"c":"#1b2233","w":0.003,
            "p":[[0.3124,0.4551],[0.318,0.4612]]}]}');

    -- 空のページ (何も書いていない) も通る
    insert into public.annotations (attempt_id, page, strokes)
    values (v_att, 8, '{"v":1,"strokes":[]}');

    -- J1: 旧形式 (裸の配列)
    begin
        insert into public.annotations (attempt_id, page, strokes)
        values (v_att, 91, '[{"points":[[10,10]],"color":"#000"}]');
        raise exception '[fail] J1 旧形式の裸の配列が入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- J2: 版が無い
    begin
        insert into public.annotations (attempt_id, page, strokes)
        values (v_att, 92, '{"strokes":[]}');
        raise exception '[fail] J2 v の無いストロークが入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- J3: ★本命 — ピクセル座標が紛れ込む
    begin
        insert into public.annotations (attempt_id, page, strokes)
        values (v_att, 93, '{"v":1,"strokes":[{"c":"#1b2233","w":0.003,
                "p":[[387,798],[394,808]]}]}');
        raise exception '[fail] J3 ピクセル座標 (387, 798) が入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- J4: わずかに範囲外 (1.0 は可、1.0001 は不可)
    begin
        insert into public.annotations (attempt_id, page, strokes)
        values (v_att, 94, '{"v":1,"strokes":[{"c":"#1b2233","w":0.003,
                "p":[[1.0001,0.5]]}]}');
        raise exception '[fail] J4 座標 1.0001 が入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- J5: 負の座標
    begin
        insert into public.annotations (attempt_id, page, strokes)
        values (v_att, 95, '{"v":1,"strokes":[{"c":"#1b2233","w":0.003,
                "p":[[-0.01,0.5]]}]}');
        raise exception '[fail] J5 負の座標が入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- J6: 筆圧付き (3 要素)。持たないと決めたので弾く
    begin
        insert into public.annotations (attempt_id, page, strokes)
        values (v_att, 96, '{"v":1,"strokes":[{"c":"#1b2233","w":0.003,
                "p":[[0.3,0.4,0.75]]}]}');
        raise exception '[fail] J6 筆圧付きの 3 要素の点が入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- J7: 点の無いストローク
    begin
        insert into public.annotations (attempt_id, page, strokes)
        values (v_att, 97, '{"v":1,"strokes":[{"c":"#1b2233","w":0.003,"p":[]}]}');
        raise exception '[fail] J7 点の無いストロークが入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- J8: 線幅が数値でない
    --     ★ (s -> 'w')::numeric を型の確認前に評価すると 22023 で落ちて
    --       check_violation にならない。段階を分けている理由がこれ。
    begin
        insert into public.annotations (attempt_id, page, strokes)
        values (v_att, 98, '{"v":1,"strokes":[{"c":"#1b2233","w":"ふつう",
                "p":[[0.3,0.4]]}]}');
        raise exception '[fail] J8 w が文字列のストロークが入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- J9: 線幅がページ幅の 10% 超
    begin
        insert into public.annotations (attempt_id, page, strokes)
        values (v_att, 99, '{"v":1,"strokes":[{"c":"#1b2233","w":0.5,
                "p":[[0.3,0.4]]}]}');
        raise exception '[fail] J9 w=0.5 のストロークが入ってしまった';
    exception when check_violation then n_ok := n_ok + 1;
    end;

    -- J10: 端の値 0 と 1 はちょうど通る (境界の取り違えを止める)
    insert into public.annotations (attempt_id, page, strokes)
    values (v_att, 100, '{"v":1,"strokes":[{"c":"#1b2233","w":0.003,
            "p":[[0,0],[1,1]]}]}');

    if n_ok <> 9 then
        raise exception '[fail] J: 想定 9 件のうち % 件しか検査できていない', n_ok;
    end if;
    raise notice '[ok] J 手書きの形 (§5) 12 件';
end
$$;

\echo '=== 全ての検査を通過 (A 14 / B 3 / C 20 / D 9 / E 4 / F 3 / G 5 / H 6 / I 9 / J 12) ==='
