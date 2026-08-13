# pdf.js (vendored)

pdfjs-dist **6.2.108** の `legacy/build` を固定配置したもの。

- 取得元: `npm pack pdfjs-dist@6.2.108` → `package/legacy/build/`
- 参照は `/vendor/pdfjs/pdf.min.mjs?v=6.2.108` の形（katex と同じ作法）
- `legacy` を使うのは、古い iPad Safari を対象に残すため（トランスパイル済み）

## ★ v3 系を使わないこと
UMD (`<script src>`) で読める v3 は既存の作法に馴染むが、
**CVE-2024-4367（細工した PDF のフォント経由で任意 JS 実行）が未修正**。
修正は 4.2.67 以降。PDF を上げるのは講師だけとはいえ、既知の RCE 級を承知で
入れる理由がないので v4 以降（= ESM）を使う。

## 上げ方
```bash
npm pack pdfjs-dist@<新しい版>
tar xzf pdfjs-dist-<版>.tgz package/legacy/build/pdf.min.mjs \
    package/legacy/build/pdf.worker.min.mjs package/LICENSE
```
を `vendor/pdfjs/` に置き直し、`VERSION` と参照側の `?v=` を揃える。
