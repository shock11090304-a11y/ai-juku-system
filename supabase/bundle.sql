-- =============================================================================
-- 英語学習アプリ — Supabase に貼る用のひとまとめ
--
--   ★ これは **生成物**。直接編集しない。
--     元は supabase/migrations/*.sql と supabase/seed.sql。
--     直したら `python3 supabase/build_bundle.py` で作り直す
--     (中身が古いと scripts/english_schema/check_schema.py が落ちる)。
--
-- ■ 使い方
--   Supabase ダッシュボード → SQL Editor → 全部貼って Run。
--   ターミナルも Supabase CLI も要らない。
--
-- ■ 中身 (この順に流れる)
--   1. テーブル 7 本・制約・インデックス・updated_at トリガ
--   2. 権限と RLS ポリシー・auth.users 連携・生徒向け view
--   3. 問題 PDF の bucket (book-pdfs) と読み書き権限
--   4. 採点 RPC submit_attempt() と、点数を直接書けなくする権限
--   5. 再受験中に正解が見えてしまう穴の修正
--   6. 動作確認用の中身 (仮定法の演習 1 冊 5 問 + 未公開の模試 1 冊)
--
--   ★ 6 (seed) は動作確認用。本番に入れるときは末尾の seed 部分を消して貼ること。
--
-- ■ 何度貼っても安全
--   全部 if not exists / or replace / drop … if exists / on conflict do nothing。
--   2 回貼ってもデータは増えないし、エラーにもならない。
-- =============================================================================



-- ##############################################################################
-- ## 1. english learning core
-- ##    (supabase/migrations/20260813010000_english_learning_core.sql)
-- ##############################################################################

-- =============================================================================
-- 英語学習アプリ: コアスキーマ (テーブル / 制約 / インデックス / トリガ)
--
--   profiles / books / questions / attempts / answers / annotations / review_items
--
-- ★ RLS (行レベルセキュリティ) は次の migration で入れる。
--   このファイルだけを流した状態は **全員が全行を読める** ので、本番に出す前に
--   20260813010100_english_learning_rls.sql まで必ず流すこと。
--   検査: python3 scripts/english_schema/check_schema.py が「RLS の無いテーブル」を落とす。
--
-- ★ Supabase 前提。auth.users と auth.uid() / ロール anon・authenticated が要る。
--   手元の素の Postgres で試すときは supabase/tests/00_local_stubs.sql を先に流す。
--
-- ★ 何度流しても安全 (if not exists / or replace) にしてある。
-- =============================================================================

-- -----------------------------------------------------------------------------
-- profiles — auth.users に 1:1 で貼るユーザープロフィール
-- -----------------------------------------------------------------------------
-- 元の設計からの意図的な差分 (README.md「設計からの差分」に一覧):
--   - auth.users への参照に on delete cascade を付けた。付けないと退会 (auth.users の
--     削除) が profiles の参照で失敗して、退会処理そのものが通らない。
--   - created_at に not null を足した。default があっても明示 NULL は入れられるため。
create table if not exists public.profiles (
    id           uuid        primary key references auth.users (id) on delete cascade,
    display_name text        not null check (btrim(display_name) <> ''),
    role         text        not null default 'student'
                             check (role in ('student', 'teacher')),
    created_at   timestamptz not null default now()
);

comment on table  public.profiles is 'ユーザープロフィール (auth.users に 1:1)';
comment on column public.profiles.role is
    'student = 生徒 / teacher = 講師。生徒が自分で teacher に昇格できないよう、'
    'RLS migration の profiles_guard_role トリガで変更を止めている。';

-- -----------------------------------------------------------------------------
-- books — 問題セット (＝ブック)
-- -----------------------------------------------------------------------------
-- 例:「英文法 仮定法 演習20」「第3回 英検準1級模試」
--
-- ★ subject は元の設計ではコメントでの列挙だったが、閉じた集合と読んで check にした。
--   増やすときは 1 行の ALTER で足す (README「設計からの差分」に手順)。
--   level は「基礎 / 標準 / 難関 など」と "など" 付きなので自由記述のまま。
create table if not exists public.books (
    id             uuid        primary key default gen_random_uuid(),
    title          text        not null check (btrim(title) <> ''),
    subject        text        not null
                               check (subject in ('grammar', 'reading', 'eiken', 'mock')),
    level          text,
    pdf_path       text,       -- Supabase Storage 上のパス。NULL 可 (JSON 問題のみの場合)
    page_count     int         check (page_count is null or page_count > 0),
    time_limit_sec int         check (time_limit_sec is null or time_limit_sec > 0),
    is_published   boolean     not null default false,
    created_by     uuid        references public.profiles (id) on delete set null,
    created_at     timestamptz not null default now()
);

comment on table  public.books is '問題セット (ブック)。1 冊 = 1 回分の演習または模試';
comment on column public.books.pdf_path is
    'Supabase Storage (bucket: book-pdfs) 上のオブジェクトパス。NULL なら JSON 問題のみ。';
comment on column public.books.is_published is
    'false の間は講師にしか見えない (RLS)。生徒に配るときに true にする。';
comment on column public.books.time_limit_sec is 'NULL なら無制限';

-- -----------------------------------------------------------------------------
-- questions — 設問
-- -----------------------------------------------------------------------------
-- 正解の形を DB 側で保証する。手入力の正解を信じないのはこのリポジトリの既定方針
-- (CLAUDE.md「数学の正解は手入力しない」と同じ考え方) で、ここでは
--   - choice なら choice_count は 2〜10 で、correct_answer は 1〜choice_count の番号
--   - short なら choice_count は NULL で、correct_answer は空でない
-- を満たさない行を **入れられなくする**。
--
-- ★ 判定を plpgsql の関数に出しているのは、CHECK 式を素の SQL で
--     `correct_answer ~ '^[0-9]+$' and correct_answer::int <= choice_count`
--   と書くと、**and の評価順が仕様として保証されない**ため
--   (Postgres のマニュアルは AND/OR の評価順を当てにするなと明記している。
--    手元の PG16 は左から評価するので今は動くが、プランナが並べ替えてよい)。
--   順序が入れ替わった瞬間、`correct_answer='あ'` の行は check_violation ではなく
--   22P02 (invalid input syntax for type integer) で落ちるようになり、
--   アプリ側の「入力ミス」と「バグ」の区別が壊れる。plpgsql なら文の順序が保証される。
create or replace function public.question_answer_is_valid(
    p_answer_type    text,
    p_choice_count   int,
    p_correct_answer text
) returns boolean
language plpgsql
immutable
set search_path = pg_catalog, pg_temp
as $$
begin
    if p_correct_answer is null or btrim(p_correct_answer) = '' then
        return false;
    end if;

    if p_answer_type = 'choice' then
        if p_choice_count is null or p_choice_count < 2 or p_choice_count > 10 then
            return false;
        end if;
        -- 先に形を見てから数値にする (順序が保証されるのが plpgsql を使う理由)
        if p_correct_answer !~ '^[1-9][0-9]?$' then
            return false;
        end if;
        return p_correct_answer::int between 1 and p_choice_count;
    end if;

    if p_answer_type = 'short' then
        return p_choice_count is null;
    end if;

    return false;   -- 未知の answer_type
end;
$$;

comment on function public.question_answer_is_valid(text, int, text) is
    'questions の answer_type / choice_count / correct_answer の整合を見る (CHECK 制約から呼ぶ)';

create table if not exists public.questions (
    id               uuid    primary key default gen_random_uuid(),
    book_id          uuid    not null references public.books (id) on delete cascade,
    number           int     not null check (number > 0),   -- 表示上の設問番号
    page             int     check (page is null or page > 0),  -- PDF 内の該当ページ (ジャンプ用)
    answer_type      text    not null check (answer_type in ('choice', 'short')),
    choice_count     int,    -- answer_type='choice' のとき 2〜10
    correct_answer   text    not null,   -- choice なら '3'、short なら正解文字列
    accepted_answers text[], -- short の別解 (大文字小文字・冠詞ゆれ等)
    points           int     not null default 1 check (points > 0),
    unit_tag         text,   -- 「基礎核」単元ID。例: 'SV-01', 'REL-03'
    explanation      text,   -- 解説 (Markdown)

    unique (book_id, number),

    constraint questions_answer_shape
        check (public.question_answer_is_valid(answer_type, choice_count, correct_answer)),

    -- 別解の配列に NULL 要素が混ざると `user_answer = any(accepted_answers)` が
    -- NULL を返して採点が静かに落ちるので、要素の NULL は入れさせない。
    constraint questions_accepted_answers_no_null
        check (accepted_answers is null or array_position(accepted_answers, null) is null)
);

comment on table  public.questions is '設問。book_id + number で一意';
comment on column public.questions.correct_answer is
    'choice なら選択肢番号 (1 起算の文字列)、short なら正解文字列';
comment on column public.questions.accepted_answers is
    'short の別解。採点は correct_answer と accepted_answers の和集合で行う。';
comment on column public.questions.unit_tag is '「基礎核」単元ID。例: SV-01, REL-03';

-- -----------------------------------------------------------------------------
-- attempts — 演習セッション (1 回の受験)
-- -----------------------------------------------------------------------------
create table if not exists public.attempts (
    id           uuid        primary key default gen_random_uuid(),
    book_id      uuid        not null references public.books (id),
    user_id      uuid        not null references public.profiles (id),
    started_at   timestamptz not null default now(),
    submitted_at timestamptz,
    total_score  int         check (total_score is null or total_score >= 0),
    max_score    int         check (max_score is null or max_score >= 0),
    elapsed_sec  int         check (elapsed_sec is null or elapsed_sec >= 0),

    -- 提出したのに時刻が開始より前、のような行を残さない
    constraint attempts_submitted_after_started
        check (submitted_at is null or submitted_at >= started_at)
);

comment on table  public.attempts is '演習セッション (1 回の受験)';
comment on column public.attempts.submitted_at is
    'NULL = 受験中。値が入ると RLS 側で更新が止まり、答案が凍結される。';

-- -----------------------------------------------------------------------------
-- answers — 設問ごとの解答
-- -----------------------------------------------------------------------------
create table if not exists public.answers (
    id             uuid    primary key default gen_random_uuid(),
    attempt_id     uuid    not null references public.attempts (id) on delete cascade,
    question_id    uuid    not null references public.questions (id),
    user_answer    text,
    is_correct     boolean,
    time_spent_sec int     check (time_spent_sec is null or time_spent_sec >= 0),

    unique (attempt_id, question_id)
);

comment on table  public.answers is '設問ごとの解答。attempt_id + question_id で一意';
comment on column public.answers.time_spent_sec is 'その設問を表示していた累計秒数';

-- -----------------------------------------------------------------------------
-- annotations — 手書きストローク (ページ単位でまとめて保存)
-- -----------------------------------------------------------------------------
-- ★ strokes の中身は設計書 §5 のフォーマット。§5 はこのリポジトリに無いので、
--   jsonb の形は **わざと制約していない** (推測で `array` を強制すると
--   `{"version":1,"strokes":[...]}` 形式だった場合に書き込みが全部落ちる)。
--   §5 が確定したら jsonb_typeof / json schema の CHECK をここに足すこと。
create table if not exists public.annotations (
    id         uuid        primary key default gen_random_uuid(),
    attempt_id uuid        not null references public.attempts (id) on delete cascade,
    page       int         not null check (page > 0),
    strokes    jsonb       not null,
    updated_at timestamptz not null default now(),

    unique (attempt_id, page)
);

comment on table  public.annotations is '手書きストローク (attempt × page で 1 行にまとめる)';
comment on column public.annotations.strokes is
    '設計書 §5 のストロークフォーマット。DB 側では形を検査していない。';

-- updated_at はアプリに任せず DB で打つ (クライアントの時計を信じない)
create or replace function public.touch_updated_at()
returns trigger
language plpgsql
set search_path = pg_catalog, pg_temp
as $$
begin
    new.updated_at := now();
    return new;
end;
$$;

drop trigger if exists annotations_touch_updated_at on public.annotations;
create trigger annotations_touch_updated_at
    before update on public.annotations
    for each row execute function public.touch_updated_at();

-- -----------------------------------------------------------------------------
-- review_items — 復習キュー (誤答ノート)
-- -----------------------------------------------------------------------------
create table if not exists public.review_items (
    id            uuid        primary key default gen_random_uuid(),
    user_id       uuid        not null references public.profiles (id) on delete cascade,
    question_id   uuid        not null references public.questions (id) on delete cascade,
    wrong_count   int         not null default 1 check (wrong_count >= 0),
    last_wrong_at timestamptz not null default now(),
    is_resolved   boolean     not null default false,
    tags          text[],

    unique (user_id, question_id)
);

comment on table  public.review_items is '復習キュー (誤答ノート)。生徒 × 設問で 1 行';
comment on column public.review_items.is_resolved is '復習で 2 回連続正解したら true';

-- =============================================================================
-- インデックス
--   Postgres は外部キーに自動でインデックスを張らない。UNIQUE 制約が先頭列を
--   カバーしている分は張らず、**カバーされていない参照と実際の画面の問い合わせ**だけ張る。
-- =============================================================================

-- 生徒の「受験履歴」画面: 自分の attempt を新しい順
create index if not exists idx_attempts_user_started
    on public.attempts (user_id, started_at desc);

-- 講師の「このブックの受験状況」画面 + books 削除時の参照検査
create index if not exists idx_attempts_book
    on public.attempts (book_id);

-- answers は unique(attempt_id, question_id) が attempt_id 側をカバーする。
-- question_id 側は素通しなので、設問ごとの正答率集計のために張る。
create index if not exists idx_answers_question
    on public.answers (question_id);

-- review_items も unique(user_id, question_id) が user_id 側をカバーする。
create index if not exists idx_review_items_question
    on public.review_items (question_id);

-- 復習キューの本体クエリ: 自分の未解決を古い誤答から。部分インデックスで
-- 解決済み (時間が経つほど大半を占める) を最初から外す。
create index if not exists idx_review_items_queue
    on public.review_items (user_id, last_wrong_at desc)
    where not is_resolved;

-- タグ絞り込み (`tags && array['仮定法']`)
create index if not exists idx_review_items_tags
    on public.review_items using gin (tags);

-- 生徒のブック一覧は公開済みだけを見る。件数が増えても公開分だけ舐める。
create index if not exists idx_books_published
    on public.books (subject, level)
    where is_published;

create index if not exists idx_books_created_by
    on public.books (created_by);

-- 「基礎核」単元ごとの弱点集計
create index if not exists idx_questions_unit_tag
    on public.questions (unit_tag)
    where unit_tag is not null;


-- ##############################################################################
-- ## 2. english learning rls
-- ##    (supabase/migrations/20260813010100_english_learning_rls.sql)
-- ##############################################################################

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


-- ##############################################################################
-- ## 3. english learning storage
-- ##    (supabase/migrations/20260813010200_english_learning_storage.sql)
-- ##############################################################################

-- =============================================================================
-- 英語学習アプリ: 問題 PDF の置き場 (Supabase Storage)
--
--   books.pdf_path が指すオブジェクトの bucket と、その読み書き権限。
--
-- ★ この migration だけは Supabase 専用 (storage スキーマが要る)。
--   bucket を管理画面で先に作ってある場合は insert が no-op になるだけで害は無い。
-- =============================================================================

-- 非公開 bucket。署名付き URL (createSignedUrl) 経由でしか配らない。
-- public = true にすると URL を知っている人全員に問題 PDF が配られるので必ず false。
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('book-pdfs', 'book-pdfs', false, 52428800, array['application/pdf'])
on conflict (id) do update
    set public             = excluded.public,
        file_size_limit    = excluded.file_size_limit,
        allowed_mime_types = excluded.allowed_mime_types;

-- -----------------------------------------------------------------------------
-- 読み取り: 公開済みブックの PDF だけ。講師は未公開も読める。
-- -----------------------------------------------------------------------------
-- ★ 「bucket_id が book-pdfs なら誰でも読める」にしてはいけない。オブジェクト名は
--   一覧 API で列挙できるので、未公開の模試 PDF が受験前に落とせてしまう。
--   books.pdf_path と突き合わせて、公開済みのものだけに限る。
drop policy if exists "book_pdfs_select_published" on storage.objects;
create policy "book_pdfs_select_published" on storage.objects
    for select to authenticated
    using (
        bucket_id = 'book-pdfs'
        and exists (
            select 1 from public.books b
            where b.pdf_path = storage.objects.name
              and (b.is_published or (select public.is_teacher()))
        )
    );

-- -----------------------------------------------------------------------------
-- 書き込み: 講師だけ
-- -----------------------------------------------------------------------------
drop policy if exists "book_pdfs_insert_teacher" on storage.objects;
create policy "book_pdfs_insert_teacher" on storage.objects
    for insert to authenticated
    with check (bucket_id = 'book-pdfs' and (select public.is_teacher()));

drop policy if exists "book_pdfs_update_teacher" on storage.objects;
create policy "book_pdfs_update_teacher" on storage.objects
    for update to authenticated
    using (bucket_id = 'book-pdfs' and (select public.is_teacher()))
    with check (bucket_id = 'book-pdfs' and (select public.is_teacher()));

drop policy if exists "book_pdfs_delete_teacher" on storage.objects;
create policy "book_pdfs_delete_teacher" on storage.objects
    for delete to authenticated
    using (bucket_id = 'book-pdfs' and (select public.is_teacher()));


-- ##############################################################################
-- ## 4. english learning grading
-- ##    (supabase/migrations/20260813010300_english_learning_grading.sql)
-- ##############################################################################

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


-- ##############################################################################
-- ## 5. english learning retake fix
-- ##    (supabase/migrations/20260813010400_english_learning_retake_fix.sql)
-- ##############################################################################

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


-- ##############################################################################
-- ## 6. english learning strokes format
-- ##    (supabase/migrations/20260813010500_english_learning_strokes_format.sql)
-- ##############################################################################

-- =============================================================================
-- 英語学習アプリ: 手書きストロークの形 (設計書 §5 の確定版)
--
-- ★ 2026-08-13 に塾長が決定した内容:
--     - 座標は **ページの幅・高さを 1 とした正規化座標 (0〜1)**
--     - 筆圧・傾きは **持たない**（点は [x, y] の 2 要素だけ）
--
-- ■ 形
--     {
--       "v": 1,
--       "strokes": [
--         {"c": "#1b2233", "w": 0.003, "p": [[0.3124, 0.4551], [0.3180, 0.4612]]}
--       ]
--     }
--
--     v       … このフォーマットの版。整数の 1。将来変えるときはここを上げて
--               strokes_are_valid() に新しい版の分岐を足す
--     strokes … ストロークの配列。空配列でよい (何も書いていないページ)
--     c       … 色 (文字列)
--     w       … 線の太さ。★これも **ページ幅を 1 とした比**。
--               例: 幅 1200px のページで 3.6px の線なら 0.003
--     p       … 点の配列。1 点以上。各点は [x, y] の 2 要素で、どちらも 0〜1
--
-- ■ なぜ正規化するのか
--   iPad で書いて PC で見る、拡大率を変える、PDF を差し替える —— どれをしても
--   書き込みの位置がずれないため。ピクセル座標で持つと、書いたときの表示サイズを
--   一緒に記録しない限り**後から復元できなくなる**。
--   ★ これは「データが溜まってからでは直せない」種類の決定なので、
--     運用を始める前に確定させた。
--
-- ■ 既存データの扱い
--   制約は **NOT VALID** で足している。動作確認で入れた旧形式 (裸の配列) の行は
--   そのまま残るが、**新しい書き込みは全部この形でしか通らない**。
--   旧形式の行は座標の基準が記録されていないので変換できない。消すなら:
--       delete from public.annotations
--        where jsonb_typeof(strokes) <> 'object' or (strokes ->> 'v') is distinct from '1';
--   消したあとに全行を検査対象へ格上げするなら:
--       alter table public.annotations validate constraint annotations_strokes_shape;
-- =============================================================================

-- ★ 判定を段階に分けているのは、SQL の or が評価順を保証しないため。
--   型を確かめる前に `(s -> 'w')::numeric` を評価すると、w が文字列だったときに
--   check_violation ではなく 22023 で落ちる。plpgsql で「型 → 値」の順を固定する。
create or replace function public.strokes_are_valid(p_strokes jsonb)
returns boolean
language plpgsql
immutable
set search_path = pg_catalog, pg_temp
as $$
declare
    n int;
begin
    if p_strokes is null then
        return false;
    end if;
    -- 旧形式 (裸の配列) はここで落ちる
    if jsonb_typeof(p_strokes) <> 'object' then
        return false;
    end if;
    if (p_strokes ->> 'v') is distinct from '1' then
        return false;
    end if;
    if jsonb_typeof(p_strokes -> 'strokes') <> 'array' then
        return false;
    end if;

    -- 暴走した書き込みで 1 行が肥大するのを止める (1 ページ分としては十分な上限)
    if jsonb_array_length(p_strokes -> 'strokes') > 5000 then
        return false;
    end if;
    if jsonb_array_length(p_strokes -> 'strokes') = 0 then
        return true;                          -- 何も書いていないページ
    end if;

    -- (1) ストロークの型
    select count(*) into n
      from jsonb_array_elements(p_strokes -> 'strokes') s
     where jsonb_typeof(s)        <> 'object'
        or jsonb_typeof(s -> 'c') <> 'string'
        or jsonb_typeof(s -> 'w') <> 'number'
        or jsonb_typeof(s -> 'p') <> 'array';
    if n > 0 then return false; end if;

    -- (2) 型が確かめられたので数値を見る
    select count(*) into n
      from jsonb_array_elements(p_strokes -> 'strokes') s
     where (s -> 'w')::numeric <= 0
        or (s -> 'w')::numeric > 0.1          -- ページ幅の 10% を超える線は誤り
        or jsonb_array_length(s -> 'p') = 0;  -- 点の無いストローク
    if n > 0 then return false; end if;

    -- (3) 各点が配列か
    select count(*) into n
      from jsonb_array_elements(p_strokes -> 'strokes') s,
           jsonb_array_elements(s -> 'p') pt
     where jsonb_typeof(pt) <> 'array';
    if n > 0 then return false; end if;

    -- (4) 2 要素で、どちらも数値か (★筆圧は持たないので 3 要素は誤り)
    select count(*) into n
      from jsonb_array_elements(p_strokes -> 'strokes') s,
           jsonb_array_elements(s -> 'p') pt
     where jsonb_array_length(pt) <> 2
        or jsonb_typeof(pt -> 0) <> 'number'
        or jsonb_typeof(pt -> 1) <> 'number';
    if n > 0 then return false; end if;

    -- (5) ★本命: 0〜1 に収まっているか。
    --     ピクセル座標 ([387, 798] など) が紛れ込むのをここで止める。
    --     見逃すと、書いた端末以外では位置が復元できないデータが溜まる。
    select count(*) into n
      from jsonb_array_elements(p_strokes -> 'strokes') s,
           jsonb_array_elements(s -> 'p') pt
     where (pt -> 0)::numeric < 0 or (pt -> 0)::numeric > 1
        or (pt -> 1)::numeric < 0 or (pt -> 1)::numeric > 1;
    return n = 0;
end;
$$;

comment on function public.strokes_are_valid(jsonb) is
    'annotations.strokes が §5 の形か (v=1 / 正規化座標 0〜1 / 点は [x,y] の 2 要素)';

do $$
begin
    if not exists (select 1 from pg_constraint
                    where conname = 'annotations_strokes_shape'
                      and conrelid = 'public.annotations'::regclass) then
        -- NOT VALID: 既存行は検査しない (動作確認で入れた旧形式の行を壊さないため)。
        -- 新規の insert / update は全部この制約を通る。
        alter table public.annotations
            add constraint annotations_strokes_shape
            check (public.strokes_are_valid(strokes)) not valid;
    end if;
end
$$;

comment on column public.annotations.strokes is
    '手書きストローク (設計書 §5)。{"v":1,"strokes":[{"c","w","p"}]}。'
    '座標 p と線幅 w はページの幅・高さを 1 とした正規化値。筆圧は持たない。';


-- ##############################################################################
-- ## 7. 動作確認用のデータ (本番では消す)
-- ##    (supabase/seed.sql)
-- ##############################################################################

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
--
-- ★ PDF 運用。設問文と選択肢は **PDF の中**にあり、DB 側は
--   「何ページ目か (questions.page)」と「答案の形 (選択肢の数 / 短答)」だけを持つ。
--   冊子は supabase/demo/sample-book.pdf (supabase/demo/build_sample_pdf.py が作る)。
--   ★ 設問番号とページは PDF と一対一で対応している。片方だけ直すとずれる。
--     デモ画面の「講師」パネルからこの PDF を books/kateiho-enshu5.pdf として上げる。
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1 冊目: 公開済み。生徒に見える
-- -----------------------------------------------------------------------------
insert into public.books (id, title, subject, level, pdf_path, page_count,
                          time_limit_sec, is_published)
values ('5eed0001-5eed-4eed-8eed-5eed00000001',
        '英文法 仮定法 演習5', 'grammar', '標準',
        'books/kateiho-enshu5.pdf', 2, 600, true)
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
-- 提出するまで生徒には返らない (student_questions view が伏せる)。
insert into public.questions
    (id, book_id, number, page, answer_type, choice_count, correct_answer,
     accepted_answers, points, unit_tag, explanation)
values
-- 第1問 (PDF 1 ページ目) ------------------------------------------------------
--   If I (   ) you, I would accept that offer right away.
--   1. am  2. was  3. were  4. will be
('5eedaa01-5eed-4eed-8eed-5eed0000aa01', '5eed0001-5eed-4eed-8eed-5eed00000001',
 1, 1, 'choice', 4, '3', null, 1, 'SUBJ-01',
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

-- 第2問 (PDF 1 ページ目) ------------------------------------------------------
--   If she had started ten minutes earlier, she (   ) the last train.
--   1. catches  2. caught  3. would catch  4. would have caught
('5eedaa02-5eed-4eed-8eed-5eed0000aa02', '5eed0001-5eed-4eed-8eed-5eed00000001',
 2, 1, 'choice', 4, '4', null, 2, 'SUBJ-02',
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

-- 第3問 (PDF 1 ページ目・短答) -------------------------------------------------
--   I wish I (   ) speak French fluently.  can を適切な形にして書きなさい。
('5eedaa03-5eed-4eed-8eed-5eed0000aa03', '5eed0001-5eed-4eed-8eed-5eed00000001',
 3, 1, 'short', null, 'could', array['could speak'], 2, 'SUBJ-03',
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

-- 第4問 (PDF 2 ページ目) ------------------------------------------------------
--   (   ) it not been for your advice, I would have made a serious mistake.
--   1. If  2. Had  3. Were  4. Should
('5eedaa04-5eed-4eed-8eed-5eed0000aa04', '5eed0001-5eed-4eed-8eed-5eed00000001',
 4, 2, 'choice', 4, '2', null, 1, 'SUBJ-04',
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

-- 第5問 (PDF 2 ページ目・短答) -------------------------------------------------
--   If it (   ) tomorrow, we will go hiking.  not rain を適切な形にして書きなさい。
('5eedaa05-5eed-4eed-8eed-5eed0000aa05', '5eed0001-5eed-4eed-8eed-5eed00000001',
 5, 2, 'short', null, 'does not rain', array['doesn''t rain'], 2, 'SUBJ-05',
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
