-- =============================================================================
-- 英語学習アプリ: auth 連携 と RLS (行レベルセキュリティ)
--
-- 方針 (2 行で言うと):
--   生徒 = 自分の行だけ。公開済みブックの設問は「正解を伏せた view」経由でしか読めない。
--   講師 = 全部読める。ブックと設問を書けるのは講師だけ。
--
-- ★ ここを流さないと **誰でも全生徒の答案を読める**。core migration の直後に必ず流す。
-- ★ 検査: python3 scripts/english_schema/check_schema.py
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 0. 権限の土台
-- -----------------------------------------------------------------------------
-- Supabase は public スキーマの新規テーブルに anon / authenticated の権限を既定で配る。
-- 未ログイン (anon) にこのアプリのデータを触らせる理由が 1 つも無いので明示的に剥がす。
-- (RLS のポリシーを全部 `to authenticated` で書いてあるので二重の守りになる)
grant usage on schema public to anon, authenticated;

revoke all on public.profiles, public.books, public.questions, public.attempts,
               public.answers, public.annotations, public.review_items
       from anon;

grant select, insert, update on public.profiles     to authenticated;
grant select, insert, update, delete on public.books       to authenticated;
grant select, insert, update, delete on public.questions   to authenticated;
grant select, insert, update, delete on public.attempts    to authenticated;
grant select, insert, update, delete on public.answers     to authenticated;
grant select, insert, update, delete on public.annotations to authenticated;
grant select, insert, update, delete on public.review_items to authenticated;
-- profiles の delete は誰にも配らない。退会は auth.users を消せば cascade で落ちる。

-- -----------------------------------------------------------------------------
-- 1. 判定用のヘルパー
-- -----------------------------------------------------------------------------
-- ★ security definer なのは、profiles のポリシーの中から profiles を読むと
--   RLS が再帰して `infinite recursion detected in policy` で全クエリが落ちるため。
--   definer なら所有者権限で読むので RLS を通らない。
-- ★ security definer の関数には必ず search_path を固定する。固定しないと
--   呼び出し側が search_path を差し替えて別スキーマの profiles を読ませられる。
create or replace function public.is_teacher()
returns boolean
language sql
stable
security definer
set search_path = public, pg_temp
as $$
    select exists (
        select 1 from public.profiles p
        where p.id = auth.uid() and p.role = 'teacher'
    );
$$;

comment on function public.is_teacher() is
    '呼び出し元 (JWT の sub) が講師か。profiles のポリシーから呼ぶため security definer。';

-- 「この attempt は自分のものか」「まだ提出前 (書き換えてよい) か」
create or replace function public.attempt_is_mine(p_attempt uuid)
returns boolean
language sql
stable
security definer
set search_path = public, pg_temp
as $$
    select exists (
        select 1 from public.attempts a
        where a.id = p_attempt and a.user_id = auth.uid()
    );
$$;

create or replace function public.attempt_is_open(p_attempt uuid)
returns boolean
language sql
stable
security definer
set search_path = public, pg_temp
as $$
    select exists (
        select 1 from public.attempts a
        where a.id = p_attempt
          and a.user_id = auth.uid()
          and a.submitted_at is null
    );
$$;

comment on function public.attempt_is_open(uuid) is
    '自分の attempt で、かつ未提出か。提出後に答案・手書きを書き換えられないようにする。';

revoke execute on function public.is_teacher()          from public;
revoke execute on function public.attempt_is_mine(uuid) from public;
revoke execute on function public.attempt_is_open(uuid) from public;
grant  execute on function public.is_teacher()          to authenticated;
grant  execute on function public.attempt_is_mine(uuid) to authenticated;
grant  execute on function public.attempt_is_open(uuid) to authenticated;

-- -----------------------------------------------------------------------------
-- 2. auth.users → profiles の自動作成
-- -----------------------------------------------------------------------------
-- profiles.display_name は not null なので、これが無いとサインアップが失敗する。
-- 表示名はサインアップ時の options.data.display_name から取る。
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
    insert into public.profiles (id, display_name, role)
    values (
        new.id,
        coalesce(
            nullif(btrim(new.raw_user_meta_data ->> 'display_name'), ''),
            nullif(btrim(new.raw_user_meta_data ->> 'name'), ''),
            nullif(split_part(coalesce(new.email, ''), '@', 1), ''),
            'ゲスト'
        ),
        'student'   -- 講師への昇格は必ず手動 (下の profiles_guard_role を参照)
    )
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();

-- 生徒が自分の role を 'teacher' に書き換えて全生徒の答案を読む、を止める。
-- ★ RLS の with check だけでは止まらない。「自分の行を更新してよい」ポリシーは
--   role 列の値までは見ないので、update profiles set role='teacher' が通ってしまう。
create or replace function public.profiles_guard_role()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
    -- JWT が無い = service_role / サーバ側の管理タスク。講師の任命はここから行う。
    if auth.uid() is null then
        return new;
    end if;

    if public.is_teacher() then
        return new;
    end if;

    if tg_op = 'INSERT' then
        new.role := 'student';       -- 自己申告の teacher は黙って student に落とす
        return new;
    end if;

    if new.role is distinct from old.role then
        raise exception '権限がありません: role を変更できるのは講師だけです'
            using errcode = 'insufficient_privilege';
    end if;

    return new;
end;
$$;

drop trigger if exists profiles_guard_role on public.profiles;
create trigger profiles_guard_role
    before insert or update on public.profiles
    for each row execute function public.profiles_guard_role();

-- -----------------------------------------------------------------------------
-- 3. RLS を有効にする
-- -----------------------------------------------------------------------------
-- ★ force row level security は付けない。付けるとテーブル所有者にも RLS がかかり、
--   下の student_questions (security definer view) が自分のテーブルを読めなくなる。
alter table public.profiles     enable row level security;
alter table public.books        enable row level security;
alter table public.questions    enable row level security;
alter table public.attempts     enable row level security;
alter table public.answers      enable row level security;
alter table public.annotations  enable row level security;
alter table public.review_items enable row level security;

-- -----------------------------------------------------------------------------
-- 4. ポリシー
-- -----------------------------------------------------------------------------
-- ★ `(select auth.uid())` と `(select public.is_teacher())` の形で書く。
--   裸で書くと行ごとに関数が呼ばれる。select で包むと InitPlan になって 1 回で済む
--   (Supabase の RLS パフォーマンス指針)。数千行の answers で効いてくる。

-- profiles ---------------------------------------------------------------------
drop policy if exists profiles_select         on public.profiles;
drop policy if exists profiles_insert_self    on public.profiles;
drop policy if exists profiles_update_self    on public.profiles;
drop policy if exists profiles_update_teacher on public.profiles;

create policy profiles_select on public.profiles
    for select to authenticated
    using (id = (select auth.uid()) or (select public.is_teacher()));

create policy profiles_insert_self on public.profiles
    for insert to authenticated
    with check (id = (select auth.uid()));

create policy profiles_update_self on public.profiles
    for update to authenticated
    using (id = (select auth.uid()))
    with check (id = (select auth.uid()));

create policy profiles_update_teacher on public.profiles
    for update to authenticated
    using ((select public.is_teacher()))
    with check ((select public.is_teacher()));

-- books ------------------------------------------------------------------------
drop policy if exists books_select        on public.books;
drop policy if exists books_insert_teacher on public.books;
drop policy if exists books_update_teacher on public.books;
drop policy if exists books_delete_teacher on public.books;

create policy books_select on public.books
    for select to authenticated
    using (is_published or (select public.is_teacher()));

create policy books_insert_teacher on public.books
    for insert to authenticated
    with check ((select public.is_teacher()));

create policy books_update_teacher on public.books
    for update to authenticated
    using ((select public.is_teacher()))
    with check ((select public.is_teacher()));

create policy books_delete_teacher on public.books
    for delete to authenticated
    using ((select public.is_teacher()));

-- questions --------------------------------------------------------------------
-- ★ 生徒には **テーブルを直接読ませない**。correct_answer と explanation が同じ行に
--   入っているので、`select * from questions` を許すと受験前に正解が全部読める。
--   生徒は下の public.student_questions view を使う。
drop policy if exists questions_select_teacher on public.questions;
drop policy if exists questions_insert_teacher on public.questions;
drop policy if exists questions_update_teacher on public.questions;
drop policy if exists questions_delete_teacher on public.questions;

create policy questions_select_teacher on public.questions
    for select to authenticated
    using ((select public.is_teacher()));

create policy questions_insert_teacher on public.questions
    for insert to authenticated
    with check ((select public.is_teacher()));

create policy questions_update_teacher on public.questions
    for update to authenticated
    using ((select public.is_teacher()))
    with check ((select public.is_teacher()));

create policy questions_delete_teacher on public.questions
    for delete to authenticated
    using ((select public.is_teacher()));

-- attempts ---------------------------------------------------------------------
drop policy if exists attempts_select      on public.attempts;
drop policy if exists attempts_insert_self on public.attempts;
drop policy if exists attempts_update_self on public.attempts;
drop policy if exists attempts_delete_self on public.attempts;

create policy attempts_select on public.attempts
    for select to authenticated
    using (user_id = (select auth.uid()) or (select public.is_teacher()));

-- 自分名義で、かつ自分に見えているブック (公開済み or 自分が講師) にしか作れない
create policy attempts_insert_self on public.attempts
    for insert to authenticated
    with check (
        user_id = (select auth.uid())
        and exists (
            select 1 from public.books b
            where b.id = book_id
              and (b.is_published or (select public.is_teacher()))
        )
    );

-- ★ using 側に `submitted_at is null` を置き、with check 側には置かない。
--   こうすると「未提出 → 提出」の 1 回だけ通り、提出後は自分でも更新できなくなる。
create policy attempts_update_self on public.attempts
    for update to authenticated
    using (user_id = (select auth.uid()) and submitted_at is null)
    with check (user_id = (select auth.uid()));

create policy attempts_delete_self on public.attempts
    for delete to authenticated
    using (user_id = (select auth.uid()) and submitted_at is null);

-- answers ----------------------------------------------------------------------
drop policy if exists answers_select      on public.answers;
drop policy if exists answers_insert_self on public.answers;
drop policy if exists answers_update_self on public.answers;
drop policy if exists answers_delete_self on public.answers;

create policy answers_select on public.answers
    for select to authenticated
    using ((select public.attempt_is_mine(attempt_id)) or (select public.is_teacher()));

create policy answers_insert_self on public.answers
    for insert to authenticated
    with check ((select public.attempt_is_open(attempt_id)));

create policy answers_update_self on public.answers
    for update to authenticated
    using ((select public.attempt_is_open(attempt_id)))
    with check ((select public.attempt_is_open(attempt_id)));

create policy answers_delete_self on public.answers
    for delete to authenticated
    using ((select public.attempt_is_open(attempt_id)));

-- annotations ------------------------------------------------------------------
drop policy if exists annotations_select      on public.annotations;
drop policy if exists annotations_insert_self on public.annotations;
drop policy if exists annotations_update_self on public.annotations;
drop policy if exists annotations_delete_self on public.annotations;

create policy annotations_select on public.annotations
    for select to authenticated
    using ((select public.attempt_is_mine(attempt_id)) or (select public.is_teacher()));

create policy annotations_insert_self on public.annotations
    for insert to authenticated
    with check ((select public.attempt_is_open(attempt_id)));

create policy annotations_update_self on public.annotations
    for update to authenticated
    using ((select public.attempt_is_open(attempt_id)))
    with check ((select public.attempt_is_open(attempt_id)));

create policy annotations_delete_self on public.annotations
    for delete to authenticated
    using ((select public.attempt_is_open(attempt_id)));

-- review_items -----------------------------------------------------------------
drop policy if exists review_items_select      on public.review_items;
drop policy if exists review_items_insert_self on public.review_items;
drop policy if exists review_items_update_self on public.review_items;
drop policy if exists review_items_delete_self on public.review_items;

create policy review_items_select on public.review_items
    for select to authenticated
    using (user_id = (select auth.uid()) or (select public.is_teacher()));

create policy review_items_insert_self on public.review_items
    for insert to authenticated
    with check (user_id = (select auth.uid()));

create policy review_items_update_self on public.review_items
    for update to authenticated
    using (user_id = (select auth.uid()))
    with check (user_id = (select auth.uid()));

create policy review_items_delete_self on public.review_items
    for delete to authenticated
    using (user_id = (select auth.uid()));

-- -----------------------------------------------------------------------------
-- 5. 生徒が設問を読むための view
-- -----------------------------------------------------------------------------
-- 列単位の権限では講師と生徒を分けられない (どちらも authenticated ロール) ので、
-- view で分ける。security_invoker = false (＝所有者権限) にして questions の RLS を
-- 迂回し、代わりに **この view の where と case で** 見せてよい範囲を決める。
--   - 公開済みブックの設問だけ
--   - correct_answer / accepted_answers / explanation は
--     「自分が提出済みの答案でその設問に解答している」ときだけ返す
--
-- ★ Supabase のセキュリティリンタは security definer view を警告する。ここでは
--   「正解列を隠す」という目的そのものなので意図的。警告は無視してよい。
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
    ) as revealed
) r
where auth.uid() is not null
  and b.is_published;

comment on view public.student_questions is
    '生徒向けの設問 view。公開済みブックのみ。正解と解説は提出済みの答案がある設問だけ返す。';

revoke all on public.student_questions from anon;
grant select on public.student_questions to authenticated;
