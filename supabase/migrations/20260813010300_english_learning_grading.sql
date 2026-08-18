-- =============================================================================
-- 英語学習アプリ: 採点 (提出 RPC)
--
-- ★ なぜ要るか — 前の 3 本だけでは **採点できる経路が無い**。
--     - 生徒は提出前に correct_answer を読めない (student_questions が伏せる)
--     - 提出後は answers も attempts も凍結される (RLS)
--   つまりクライアントには「正解と突き合わせる」瞬間が存在しない。
--   採点はサーバ側 (security definer) でやるしかない。
--
-- ここで同時に、クライアントが点数を捏造する経路も閉じる:
--     - attempts の直接 UPDATE 権限を配らない (提出は submit_attempt() だけ)
--     - answers.is_correct をクライアントに書かせない (列単位の権限)
--   → total_score / is_correct を書けるのはこの関数だけになる。
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 採点して提出する
-- -----------------------------------------------------------------------------
--   1. 自分の未提出 attempt か確かめる (他人の答案・二重提出を弾く)
--   2. answers.is_correct を questions と突き合わせて埋める
--   3. attempts に点数・満点・所要時間・提出時刻を書く
--   4. 誤答を review_items に積む (既にあれば wrong_count を増やす)
--
-- 短答の照合は「前後の空白を落として小文字化」+ accepted_answers の別解。
-- ★ ここを緩めると採点が甘くなる。厳しくする分にはアプリ側で弾けるが、
--   甘くしたものは後から締められない (生徒の点数が下がるため)。
create or replace function public.submit_attempt(p_attempt uuid)
returns table (
    total_score    int,
    max_score      int,
    correct_count  int,
    answered_count int,
    question_count int
)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
    v_user  uuid := auth.uid();
    v_book  uuid;
    v_total int;
    v_max   int;
begin
    if v_user is null then
        raise exception 'ログインが必要です' using errcode = 'insufficient_privilege';
    end if;

    -- for update: 同時に 2 回押されたときに二重採点しない
    select a.book_id into v_book
      from public.attempts a
     where a.id = p_attempt
       and a.user_id = v_user
       and a.submitted_at is null
       for update;

    if not found then
        raise exception '提出できる答案がありません (他人の答案か、既に提出済みです)'
            using errcode = 'insufficient_privilege';
    end if;

    -- 2. 採点
    update public.answers a
       set is_correct = case
               when q.answer_type = 'choice' then
                   btrim(coalesce(a.user_answer, '')) = q.correct_answer
               else
                   lower(btrim(coalesce(a.user_answer, ''))) <> ''
                   and (
                       lower(btrim(coalesce(a.user_answer, ''))) = lower(btrim(q.correct_answer))
                       or lower(btrim(coalesce(a.user_answer, ''))) = any (
                           select lower(btrim(x))
                             from unnest(coalesce(q.accepted_answers, '{}'::text[])) as x)
                   )
           end
      from public.questions q
     where q.id = a.question_id
       and a.attempt_id = p_attempt;

    -- 3. 集計。満点はブックの全設問 (白紙も分母に入れる)
    select coalesce(sum(case when a.is_correct then q.points else 0 end), 0)
      into v_total
      from public.answers a
      join public.questions q on q.id = a.question_id
     where a.attempt_id = p_attempt;

    select coalesce(sum(q.points), 0)
      into v_max
      from public.questions q
     where q.book_id = v_book;

    update public.attempts a
       set submitted_at = now(),
           total_score  = v_total,
           max_score    = v_max,
           elapsed_sec  = greatest(0, extract(epoch from (now() - a.started_at))::int)
     where a.id = p_attempt;

    -- 4. 誤答を復習キューへ。同じ設問を落とすたびに wrong_count が増える。
    --    ★ is_resolved は false に戻す (一度「できるようになった」判定でも、また間違えたら復活)
    insert into public.review_items (user_id, question_id, wrong_count, last_wrong_at, is_resolved)
    select v_user, a.question_id, 1, now(), false
      from public.answers a
     where a.attempt_id = p_attempt
       and a.is_correct is not true
    on conflict (user_id, question_id) do update
       set wrong_count   = review_items.wrong_count + 1,
           last_wrong_at = now(),
           is_resolved   = false;

    return query
    select v_total,
           v_max,
           (select count(*)::int from public.answers x
             where x.attempt_id = p_attempt and x.is_correct),
           (select count(*)::int from public.answers x where x.attempt_id = p_attempt),
           (select count(*)::int from public.questions x where x.book_id = v_book);
end;
$$;

comment on function public.submit_attempt(uuid) is
    '自分の未提出 answers を採点して提出する。total_score / is_correct を書けるのはこの関数だけ。';

revoke execute on function public.submit_attempt(uuid) from public;
grant  execute on function public.submit_attempt(uuid) to authenticated;

-- -----------------------------------------------------------------------------
-- クライアントから点数を書けなくする
-- -----------------------------------------------------------------------------
-- ★ attempts の UPDATE は誰にも配らない。
--   生徒が正当に更新したい列がもう無い (提出は RPC、点数も RPC が書く)。
--   受験の開始は INSERT、提出は submit_attempt()、それ以外は触らせない。
revoke update on public.attempts from authenticated;

drop policy if exists attempts_update_self on public.attempts;

-- answers は「自分が書いた解答」だけ書かせる。is_correct は RPC の領分。
-- ★ 列を挙げた grant は、その列**以外**を書こうとした時点で permission denied になる。
--   RLS (行の可否) では列は守れないので、ここは grant 側で守る。
revoke insert, update on public.answers from authenticated;
grant  select on public.answers to authenticated;
grant  insert (attempt_id, question_id, user_answer, time_spent_sec) on public.answers to authenticated;
grant  update (user_answer, time_spent_sec) on public.answers to authenticated;
grant  delete on public.answers to authenticated;
