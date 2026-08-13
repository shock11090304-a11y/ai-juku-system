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
