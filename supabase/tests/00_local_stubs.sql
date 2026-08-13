-- =============================================================================
-- 素の Postgres で migration を試すための Supabase 相当スタブ
--
--   ★ 本番 (Supabase) では絶対に流さない。auth / storage は Supabase 側の実体がある。
--     このファイルは scripts/english_schema/check_schema.py が使い捨ての DB を作って
--     migration を実際に流すときにだけ使う。
--
--   再現するもの:
--     - ロール anon / authenticated / service_role
--     - auth.users (id / email / raw_user_meta_data)
--     - auth.uid()  … request.jwt.claims GUC から sub を取り出す (Supabase 実装と同じ形)
--     - storage.buckets / storage.objects
-- =============================================================================

do $$
begin
    if not exists (select 1 from pg_roles where rolname = 'anon') then
        create role anon nologin noinherit;
    end if;
    if not exists (select 1 from pg_roles where rolname = 'authenticated') then
        create role authenticated nologin noinherit;
    end if;
    if not exists (select 1 from pg_roles where rolname = 'service_role') then
        create role service_role nologin noinherit bypassrls;
    end if;
end
$$;

create schema if not exists auth;
grant usage on schema auth to anon, authenticated, service_role;

create table if not exists auth.users (
    id                 uuid primary key default gen_random_uuid(),
    email              text unique,
    raw_user_meta_data jsonb not null default '{}'::jsonb,
    created_at         timestamptz not null default now()
);

-- Supabase 本体と同じ実装。JWT の sub を GUC から読む。
create or replace function auth.uid()
returns uuid
language sql
stable
as $$
    select coalesce(
        nullif(current_setting('request.jwt.claim.sub', true), ''),
        (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
    )::uuid;
$$;

create schema if not exists storage;
grant usage on schema storage to anon, authenticated, service_role;

create table if not exists storage.buckets (
    id                 text primary key,
    name               text not null,
    public             boolean not null default false,
    file_size_limit    bigint,
    allowed_mime_types text[],
    created_at         timestamptz not null default now()
);

create table if not exists storage.objects (
    id         uuid primary key default gen_random_uuid(),
    bucket_id  text references storage.buckets (id),
    name       text not null,
    owner      uuid,
    metadata   jsonb,
    created_at timestamptz not null default now(),
    unique (bucket_id, name)
);

alter table storage.objects enable row level security;
grant select, insert, update, delete on storage.objects to authenticated;
