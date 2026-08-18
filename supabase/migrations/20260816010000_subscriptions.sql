-- =============================================================================
-- サブスク販売: Stripe 契約とアカウントの対応表
--
--   1 ユーザー 1 行。書くのは Vercel 関数 (service_role) だけで、
--   生徒 (authenticated) は「自分の行を読む」ことしかできない。
--   利用可否そのものはこの表では判定しない — 解約・支払い停止のとき
--   webhook が auth 側でアカウントを ban する (行は履歴と表示用)。
--
--   ★ 先生が手動発行した無料アカウント (自塾生) はこの表に行が無い。
--     行が無い = 無料アカウント。混ぜて数えないこと。
-- =============================================================================

create table if not exists public.subscriptions (
    user_id                uuid primary key references auth.users (id) on delete cascade,
    email                  text not null,
    student_name           text not null default '',
    grade                  text not null default '',
    school                 text not null default '',
    stripe_customer_id     text not null default '',
    stripe_subscription_id text not null default '',
    -- Stripe の subscription.status をそのまま持つ (勝手な語彙を作らない)
    status                 text not null default 'incomplete'
        constraint subscriptions_status_known check (status in (
            'incomplete', 'incomplete_expired', 'trialing', 'active',
            'past_due', 'canceled', 'unpaid', 'paused')),
    current_period_end     timestamptz,
    created_at             timestamptz not null default now(),
    updated_at             timestamptz not null default now()
);

-- 同じ Stripe subscription が 2 ユーザーに紐つく事故を形で止める
-- (空文字は「まだ紐ついていない」なので除外する)
create unique index if not exists subscriptions_stripe_sub_uniq
    on public.subscriptions (stripe_subscription_id)
    where stripe_subscription_id <> '';

drop trigger if exists subscriptions_touch_updated_at on public.subscriptions;
create trigger subscriptions_touch_updated_at
    before update on public.subscriptions
    for each row execute function public.touch_updated_at();

alter table public.subscriptions enable row level security;

-- 生徒: 自分の行だけ読める (契約管理画面が「契約中かどうか」を出すのに使う)
grant select on public.subscriptions to authenticated;
drop policy if exists subscriptions_own_read on public.subscriptions;
create policy subscriptions_own_read on public.subscriptions
    for select to authenticated
    using (auth.uid() = user_id);

-- 先生: 全行読める (契約者の一覧)。書き込みは webhook (service_role) に任せるので
-- ここでは配らない (grant が select だけなので、policy が all でも書けない)。
drop policy if exists subscriptions_teacher_all on public.subscriptions;
create policy subscriptions_teacher_all on public.subscriptions
    for all to authenticated
    using (public.is_teacher())
    with check (public.is_teacher());

-- webhook (service_role) が upsert する
grant all on public.subscriptions to service_role;
