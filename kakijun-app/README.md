# kakijun-app — 書き順学習 PWA（開発者向け）

未就学児向けの ひらがな・カタカナ・数字 書き順練習アプリ。
仕様書のフェーズ構成（Phase 0〜8）に沿って実装済み。保護者向け案内は `docs/README.md`。

## コマンド

```bash
npm install
npm run dev        # 開発サーバー (http://localhost:5173)
npm test           # 判定エンジン・データ全数・音声文言の単体テスト (Vitest)
npm run typecheck  # tsc --noEmit
npm run build      # 本番ビルド → dist/ (PWA/Service Worker 込み)
npm run e2e        # 本番ビルドに対する E2E (要: 先に npm run build)
```

## 構成の要点

- `src/engine/` — ★ 書き順判定エンジン。**UI・DOM・Canvas 非依存の純関数群**。
  Catmull-Rom 補間 → 等間隔64点リサンプリング、弧長相対の許容量、
  前方一致 + 累積移動距離の逸脱判定、進行方向内積の逆走判定 (仕様書 §6)
- `src/data/characters/*.json` — 全183項目のストロークデータ（正規化座標の制御点列）。
  濁音・半濁音は `composedFrom` で合成。**全項目が「理想軌跡がエンジンを0ミスで通る」
  テストで守られている**ので、データをいじったら `npm test` を必ず回すこと
- `src/canvas/` — Canvas 3層（背景/ガイド/インク）、DPR対応、パームリジェクション
- `src/store/` — IndexedDB (idb) 永続化: 進捗・設定・練習時間
- `src/audio/` — mp3 優先 + SpeechSynthesis フォールバック。文言は `voiceLines.ts`
- `tools/stroke-editor/` — データ作成用エディタ。`npm run dev` 中に
  `http://localhost:5173/tools/stroke-editor/index.html` を開く
- `tools/render/contact-sheet.ts` — 全字を下敷きフォントと重ねて目視QAするシート:
  `npx vite-node tools/render/contact-sheet.ts -- hiragana` → HTML 出力
- `tools/gen-derived.mts` — 濁音・小書き字の一括生成（済み。再実行は冪等）
- `tools/gen-icons.mts` — PWA アイコン生成
- `tools/drive-*.mts` — 実ブラウザでの手動検証シナリオ（開発用）

## デプロイ

`npm run build` の `dist/` を **HTTPS の静的ホスティング**に置くだけ（サーバー不要）。
`base: './'` なのでサブディレクトリ配信も可。iPad では「共有 → ホーム画面に追加」で
全画面アプリとして動く。オフライン動作は Service Worker が全アセットを事前キャッシュ。

## 実機（iPad）での確認が必要な項目

自動テストで担保できない §14 の項目: Apple Pencil の筆圧・遅延、パームリジェクション、
初回タップからの音、Retina の線質、回転時の再描画。実機で一通り確認すること。
