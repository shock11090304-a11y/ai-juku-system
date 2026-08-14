-- =============================================================================
-- 英語学習アプリ: 講師が PDF を上げられない穴の修正
--
-- ■ 何が起きたか (2026-08-14、登録画面から初めて PDF を上げたとき)
--   「PDF を上げられませんでした: new row violates row-level security policy」。
--   冊子の行は作れるのに、PDF のアップロードだけが落ちる。
--
-- ■ 原因 (使い捨て Postgres で再現して確定)
--   読み取りポリシー book_pdfs_select_published が、講師にも
--   「books.pdf_path がそのオブジェクトを指していること」を要求していた。
--   アプリの手順は ① books の行を作る → ② PDF を上げる → ③ pdf_path を書く。
--   ②の時点では pdf_path がまだ無い。Storage のアップロードは
--   INSERT ... RETURNING で行を返すので、返す行に SELECT ポリシーが適用され、
--   insert 自体は通るのに RETURNING で弾かれていた。
--   (実測: is_teacher() = true / RETURNING 無しの insert は通る /
--    直後の select が 0 行 — 自分が上げたファイルが自分に見えない)
--
-- ■ 直し方
--   講師は bucket 全体を読めるようにする (元のコメントの意図「講師は未公開も
--   読める」どおり)。生徒側は変えない — 公開済みの冊子が指す PDF だけ。
-- =============================================================================

drop policy if exists "book_pdfs_select_published" on storage.objects;
create policy "book_pdfs_select_published" on storage.objects
    for select to authenticated
    using (
        bucket_id = 'book-pdfs'
        and (
            (select public.is_teacher())
            or exists (
                select 1 from public.books b
                where b.pdf_path = storage.objects.name
                  and b.is_published
            )
        )
    );
