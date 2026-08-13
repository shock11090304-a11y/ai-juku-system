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
