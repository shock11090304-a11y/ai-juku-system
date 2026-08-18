-- =============================================================================
-- 英語学習アプリ: 再受験中に正解が見えてしまう穴を塞ぐ
--
-- ★ 010100 の student_questions は revealed を
--     「提出済みの答案でその設問に解答したことがあるか」
--   だけで決めていた。これだと **同じ本をもう一度受験している最中も正解が出たまま**になる。
--   一度提出した本を解き直す (復習キューから戻る・時間を置いて再挑戦する) 動線は
--   普通にあるので、そこで答えが見えるのは実害がある。
--
--   条件を 1 つ足す: そのブックに未提出の答案が 1 つでもあれば「今解いている最中」
--   とみなして伏せる。提出し終われば (未提出が無くなれば) また見える。
--
--   期待値テストの I 群がこの穴を捕まえた。手で気づいたものではないので、
--   検査ごと残しておくこと。
--
-- ★ view の定義を丸ごと置き直している。010100 の定義との差分は
--   cross join lateral の中の `and not exists (…)` だけ。
-- =============================================================================

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
           -- ★ 受験中は伏せる。同じ本の未提出の答案が 1 つでもあれば「今解いている最中」。
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
