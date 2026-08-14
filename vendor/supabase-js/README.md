# supabase-js (vendored)

`@supabase/supabase-js` **2.112.3** を **単一ファイルの ESM に固めた**もの。

## なぜ固めるのか
npm 版の `dist/index.mjs` は `@supabase/auth-js` などを **裸の import** で参照していて、
バンドラ無しのブラウザでは解決できない。このリポジトリはビルド無しの静的サイトなので、
esbuild で 1 ファイルにまとめてから vendor に置く。

CDN 直リンク (jsdelivr など) は使わない。外部の可用性と改ざんに製品を預けないため。

## 作り直し方
```bash
npm i @supabase/supabase-js@<版>
npx esbuild --bundle --format=esm --platform=browser --minify --target=es2020 \
  --outfile=vendor/supabase-js/supabase.mjs \
  node_modules/@supabase/supabase-js/dist/index.mjs
```
`VERSION` と、参照側の `?v=` も揃えること。
