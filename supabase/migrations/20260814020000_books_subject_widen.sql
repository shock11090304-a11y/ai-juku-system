-- =============================================================================
-- books.subject を英語 4 種類から他教科へ広げる
--
-- ★ なぜ必要になったか
--   元の設計は英語学習アプリだったので subject を
--       ('grammar', 'reading', 'eiken', 'mock')
--   に閉じていた。だが実際に入れたい紙の教材は
--       数学 1,119 問 / 古文 144 問 / 社会・理科 168 問 / 英語 271 問
--   で、英語以外の方が多い。冊子アプリの中身 (PDF + 設問 + 手書き) は
--   教科に依存しないので、ここだけが詰まっていた。
--
-- ★ 閉じた集合のままにする理由
--   自由入力にすると 'math' / 'Math' / '数学' / 'すうがく' が混ざり、
--   一覧の絞り込みが黙って壊れる。増やすときはここに 1 行足す。
--
-- ★ 既存の行は 4 種類のどれかなので、広げる方向の変更で必ず通る。
--   それでも not valid は使わない (全行を見て確かめる)。
-- =============================================================================

alter table public.books drop constraint if exists books_subject_check;

alter table public.books
    add constraint books_subject_check
    check (subject in (
        -- 英語 (元からあったもの)
        'grammar', 'reading', 'eiken', 'mock',
        -- 追加
        'math',      -- 数学
        'japanese',  -- 国語 (現代文・古文・漢文)
        'science',   -- 理科 (物理・化学・生物)
        'social',    -- 社会 (地理・歴史・公民)
        'other'      -- どれにも当てはまらないもの
    ));

comment on column public.books.subject is
    '教科。grammar / reading / eiken / mock (英語) / math / japanese / science / social / other';
