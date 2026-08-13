-- =============================================================================
-- 英語学習アプリ: strokes_are_valid() の「キーが無い」を弾けていなかったのを直す
--
-- ★ 何が起きていたか
--   判定を `jsonb_typeof(s -> 'c') <> 'string'` と書いていた。
--   **キーが存在しない**と `s -> 'c'` は SQL NULL になり、`jsonb_typeof(NULL)` も NULL、
--   `NULL <> 'string'` は真でも偽でもなく **NULL**。WHERE で NULL は真でないので、
--   違反として数えられずに素通りしていた。
--
--   実測 (この migration 適用前):
--     {"v":1}                                          → 通る (strokes が無いのに)
--     {"v":1,"strokes":[{}]}                           → 通る (空のストローク)
--     {"v":1,"strokes":[{"w":0.003,"p":[[0.5,0.5]]}]}  → 通る (c が無い)
--     {"v":1,"strokes":[{"c":"#000","p":[[0.5,0.5]]}]} → 通る (w が無い)
--     {"v":1,"strokes":[{"c":"#000","w":0.003}]}       → 通る (p が無い)
--     {"v":"1","strokes":[]}                           → 通る (v が数値でなく文字列)
--
--   座標の範囲 (ピクセル座標の混入) や筆圧の 3 要素は正しく弾けていた。
--   欠けているのは「キーそのものが無い」場合だけ。読み出しても何も描けないデータが
--   静かに溜まる形なので、書き込みの時点で止める。
--
-- ★ なぜテストで見つからなかったか
--   J 群は「壊れた値が入っている」入力ばかりで、**「キーが無い」入力を 1 つも
--   書いていなかった**。K 群として追加した (12 件)。
--   ★ jsonb を検査するときは「値が変」と「キーが無い」を必ず別々に試すこと。
--     前者は <> で捕まるが、後者は NULL になって素通りする。
--
-- ■ 直し方
--   すべての型判定を `is distinct from` にする。NULL を「違う」と扱ってくれる。
--   併せて v を「JSON の数値の 1」に厳格化する (文字列 "1" を弾く)。
-- =============================================================================

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
    if jsonb_typeof(p_strokes) is distinct from 'object' then
        return false;
    end if;
    -- ★ v は「JSON の数値の 1」。文字列 "1" は弾く (->> だけで見ると通ってしまう)
    if jsonb_typeof(p_strokes -> 'v') is distinct from 'number' then
        return false;
    end if;
    if (p_strokes ->> 'v') is distinct from '1' then
        return false;
    end if;
    -- ★ キーが無い場合も含めて弾く (以前は <> で書いていて素通りしていた)
    if jsonb_typeof(p_strokes -> 'strokes') is distinct from 'array' then
        return false;
    end if;

    -- 暴走した書き込みで 1 行が肥大するのを止める (1 ページ分としては十分な上限)
    if jsonb_array_length(p_strokes -> 'strokes') > 5000 then
        return false;
    end if;
    if jsonb_array_length(p_strokes -> 'strokes') = 0 then
        return true;                          -- 何も書いていないページ
    end if;

    -- (1) ストロークの型。★ c / w / p が **無い** 場合もここで落ちる
    select count(*) into n
      from jsonb_array_elements(p_strokes -> 'strokes') s
     where jsonb_typeof(s)        is distinct from 'object'
        or jsonb_typeof(s -> 'c') is distinct from 'string'
        or jsonb_typeof(s -> 'w') is distinct from 'number'
        or jsonb_typeof(s -> 'p') is distinct from 'array';
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
     where jsonb_typeof(pt) is distinct from 'array';
    if n > 0 then return false; end if;

    -- (4) 2 要素で、どちらも数値か (★筆圧は持たないので 3 要素は誤り)
    select count(*) into n
      from jsonb_array_elements(p_strokes -> 'strokes') s,
           jsonb_array_elements(s -> 'p') pt
     where jsonb_array_length(pt) <> 2
        or jsonb_typeof(pt -> 0) is distinct from 'number'
        or jsonb_typeof(pt -> 1) is distinct from 'number';
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
    'annotations.strokes が §5 の形か (v は数値の 1 / 正規化座標 0〜1 / 点は [x,y] の 2 要素)。'
    'キーの欠落も弾く (型判定は is distinct from で書くこと。<> だと NULL が素通りする)';
