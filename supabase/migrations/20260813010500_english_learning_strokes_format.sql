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
