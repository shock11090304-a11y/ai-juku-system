-- =============================================================================
-- 英語学習アプリ: JSON 問題 (PDF を使わないブック) の設問本体
--
-- ★ なぜ要るか — 元の設計は `pdf_path … NULL可（JSON問題のみの場合）` と書いてあるが、
--   その「JSON問題」を入れる列が questions に無い。
--   PDF があるブックなら本文は PDF 側にあり、questions.page が飛び先を持っているので
--   足りている。PDF が無いブックだけ、設問文と選択肢の置き場が無い。
--
--   ここで足すのは 1 列だけ:
--       question_data jsonb  … {"stem": "設問文", "choices": ["…","…"], "figure_svg": "…"}
--   ★ 正解は入れない。correct_answer / accepted_answers は今までどおり別列で、
--     student_questions view が提出前は伏せる。question_data は伏せずに常に返す
--     (設問文と選択肢は受験中に見えないと解けない)。
--
--   命名は既存の exam_questions に合わせた (CLAUDE.md の question_data.figure_svg)。
--   PDF 運用しかしないなら、この migration は流さなくてよい。
-- =============================================================================

alter table public.questions
    add column if not exists question_data jsonb;

comment on column public.questions.question_data is
    'PDF を使わないブック用の設問本体 {"stem", "choices", "figure_svg"}。'
    'PDF があるブックでは NULL (本文は PDF 側・page が飛び先)。正解は入れない。';

-- 選択肢の数が choice_count とずれていると、画面のボタン数と採点の番号がずれる。
-- ★ 判定を plpgsql に出す理由は question_answer_is_valid と同じ
--   (素の SQL の and は評価順が保証されず、jsonb_array_length が配列でない値に
--    当たると 22023 で落ちて check_violation にならない)。
create or replace function public.question_data_is_valid(
    p_answer_type   text,
    p_choice_count  int,
    p_question_data jsonb
) returns boolean
language plpgsql
immutable
set search_path = pg_catalog, pg_temp
as $$
begin
    if p_question_data is null then
        return true;                          -- PDF 運用のブックは NULL でよい
    end if;
    if jsonb_typeof(p_question_data) <> 'object' then
        return false;
    end if;
    if coalesce(btrim(p_question_data ->> 'stem'), '') = '' then
        return false;                         -- 設問文が無い JSON 問題は解けない
    end if;
    if p_answer_type = 'choice' then
        if jsonb_typeof(p_question_data -> 'choices') <> 'array' then
            return false;
        end if;
        if jsonb_array_length(p_question_data -> 'choices') <> p_choice_count then
            return false;                     -- ボタン数と正解番号の範囲がずれる
        end if;
    end if;
    return true;
end;
$$;

do $$
begin
    if not exists (select 1 from pg_constraint
                    where conname = 'questions_question_data_shape'
                      and conrelid = 'public.questions'::regclass) then
        alter table public.questions
            add constraint questions_question_data_shape
            check (public.question_data_is_valid(answer_type, choice_count, question_data));
    end if;
end
$$;

-- -----------------------------------------------------------------------------
-- 生徒向け view に question_data を足す
-- -----------------------------------------------------------------------------
-- ★ 定義を丸ごと置き直す。create or replace view は列の追加が末尾にしかできず、
--   並びが読みにくくなるため。中身は 010100 の view + question_data。
--
-- ★ ついでに「再受験中は正解を伏せる」条件を足す (010100 の穴)。
--   旧定義は revealed を「提出済みの答案でその設問に解答したことがあるか」だけで
--   決めていたので、**同じ本をもう一度受験している最中も正解が出たまま**だった。
--   受験中 (未提出の答案がそのブックに 1 つでもある) 間は伏せる。
--   期待値テストの I8 がこの穴を捕まえた。
drop view if exists public.student_questions;

create view public.student_questions
with (security_invoker = false) as
select
    q.id,
    q.book_id,
    q.number,
    q.page,
    q.answer_type,
    q.choice_count,
    q.points,
    q.unit_tag,
    q.question_data,                            -- 設問文と選択肢 (正解は入っていない)
    r.revealed,
    case when r.revealed then q.correct_answer   end as correct_answer,
    case when r.revealed then q.accepted_answers end as accepted_answers,
    case when r.revealed then q.explanation      end as explanation
from public.questions q
join public.books b on b.id = q.book_id
cross join lateral (
    select exists (
             select 1
             from public.answers a
             join public.attempts t on t.id = a.attempt_id
             where a.question_id = q.id
               and t.user_id = auth.uid()
               and t.submitted_at is not null
           )
           -- 受験中は伏せる。同じ本の未提出の答案が 1 つでもあれば「今解いている最中」。
           and not exists (
             select 1
             from public.attempts t2
             where t2.book_id = q.book_id
               and t2.user_id = auth.uid()
               and t2.submitted_at is null
           ) as revealed
) r
where auth.uid() is not null
  and b.is_published;

comment on view public.student_questions is
    '生徒向けの設問 view。公開済みブックのみ。正解と解説は、提出済みの答案でその設問に'
    '解答していて、かつ そのブックを受験中でない ときだけ返す (再受験中は伏せる)。';

revoke all on public.student_questions from anon;
grant select on public.student_questions to authenticated;
