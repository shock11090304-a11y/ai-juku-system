<!-- このファイルは実装の正典。判断と理由を残すためのもの。
     生成: 設計案3本 → 相互批評 → 統合 (2026-08-14)。
     実装で設計を変えたときは、ここも直すこと。 -->

# 冊子受験画面 — 統合設計 (実装用)

3 案の骨格は同じ結論に収束している (「ページ枠 1 箱に PDF/ink を重ね、正規化ベクタだけを正とする」)。以下はその骨格を残し、批評で死んだ部分を全部差し替えた **1 本の実装仕様**。

**設計の優先順位 (迷ったらこの順に倒す)**
1. 生徒の書き込みが失われない
2. 座標がずれない
3. 提出が通る (手書きの保存失敗で提出を止めない)
4. 見た目・書き味

---

## 0. 事前に確認した事実 (この設計の前提)

| 事項 | 実物 |
|---|---|
| pdf.js | `vendor/pdfjs/` に **6.2.108 legacy ESM** (`pdf.min.mjs` / `pdf.worker.min.mjs` / `VERSION`) が既にある。README が「v3 は CVE-2024-4367 未修正なので使うな」と明記。**v3 は選択肢に無い** |
| `answers` の grant | `insert (attempt_id, question_id, user_answer, time_spent_sec)` / `update (user_answer, time_spent_sec)` → **upsert は初回から 42501** |
| `annotations` | `unique(attempt_id,page)` + `updated_at` を **サーバ側トリガ** `annotations_touch_updated_at` が now() で打つ → **これが版番号として使える (CAS 可能)** |
| `strokes_are_valid()` | `v='1'` は `->>` 比較 (文字列 "1" も通る) / 5000 本上限 / `w` は `>0` かつ `<=0.1` / 点は 2 要素・数値・0〜1。**キー欠落 (`c`/`w`/`p` が無い) は素通しする** |
| RLS | annotations・answers の insert/update は `attempt_is_open()` (自分の & 未提出)。提出後は 42501 |
| `student_questions` | `revealed` = 提出済み答案にその設問の answers 行がある **かつ そのブックに未提出 attempt が 1 つも無い**。`b.is_published` が where にあるので非公開化で **0 行** |
| `submit_attempt` | 存在する answers 行しか採点しない。`answered_count` は行数 (= 事前作成すると常に満点) |
| デプロイ | `supabase/` は `.vercelignore` で丸ごと除外 → **製品ページはリポジトリ直下に置く** |
| vercel.json | no-cache は `*.html` / `/` / cache-purge.js / auth-guard.js のみ |

---

## 1. 作るファイルと責務

自作 JS は **すべて ESM (`.mjs`)**。pdf.js 6 が ESM なので混在させない。node からも同じファイルを import できるのでゲートが実物を検査できる (これが `.js` でなく `.mjs` にする実利)。

| パス | 責務 |
|---|---|
| `/exam-book.html` | 骨組みだけ。`<script type="module" src="/exam-book.mjs">` 1 本。冊子ペイン / 答案ペイン / ツールバー / ダイアログの空箱。`user-scalable` は切らない |
| `/exam-book.css` | レイアウト (横=2ペイン, 縦=ボトムシート)、`.page` のレイヤ重ね、`touch-action` / `overscroll-behavior` / `user-select` の指定。**position:sticky / fixed をペイン内に使わない** (ネイティブピンチ中に流れるため) |
| `/exam-book-config.mjs` | `export const SUPABASE = {url, anonKey}` のみ。`anonKey` の `role` が `anon` でなければ throw (service_role 貼り付け事故を止める)。冒頭に「Railway 側 auth-guard.js とは別系統の認証」と明記 |
| `/exam-book-sb.mjs` | supabase クライアント生成 / **fetch ラッパ** (レスポンスの `Date` ヘッダを拾って `serverNow()` を提供) / **エラー分類器 `classify(err, count)`** (§8.5)。ここ以外で `sb.from(...)` を直に呼ばない |
| `/exam-book-model.mjs` | **純関数のみ。DOM も Supabase も触らない。** §5 のモデル、`toNorm` の数式、`quant`、`validateStrokes`(送信前バリデータ)、間引き、消しゴム当たり判定、undo スタックの適用。**node からそのまま import してゲートが検査する** |
| `/exam-book-pdf.mjs` | pdf.js ロード、PDF バイト取得、**全ページ寸法の先取り**、ページ枠生成、帯(band)描画、ズーム段階、renderTask キャンセル、canvas 面積上限管理 |
| `/exam-book-ink.mjs` | 入力の振り分け (pen/touch/mouse)、2本指パン、描画 (wet/dry)、消しゴム、undo/redo、ページ単位モデルの出し入れ |
| `/exam-book-sync.mjs` | 保存キュー (ページ単位・単一飛行・CAS・バックオフ)、ローカル写し、`answers` の insert/update、提出手順の I/O |
| `/exam-book-answers.mjs` | 答案ペインの生成・入力・進捗・設問⇄ページ連動・結果表示 |
| `/exam-book.mjs` | エントリ。起動状態機械 (§9)・提出状態機械 (§10)・タイマー・モード切替 |
| `/vendor/pdfjs/cmaps/` | **追加が要る** (日本語 PDF。無いと本文が空白) |
| `/vendor/pdfjs/standard_fonts/` | **追加が要る** |
| `/vendor/supabase-js/2.x/supabase.mjs` + `LICENSE` | supabase-js を vendor 固定。jsdelivr 直リンクは製品に持ち込まない |
| `/scripts/book_exam/check_book_exam.py` | 静的ゲート (§12)。**引数なしの既定が「配信する全ファイル」**。何を見たか印字。違反で `sys.exit(1)` |
| `/scripts/book_exam/roundtrip_strokes.mjs` | node で `exam-book-model.mjs` を呼び、**異常系入力から実際に JSON を生成**して stdout に出す。上のゲートが使い捨て DB の `strokes_are_valid()` に食わせる |
| `/supabase/tests/10_schema_expectations.sql` (追記) | 回帰: (I-a) answers を PostgREST 形の upsert で書くと permission denied、(I-b) `{"v":1,"strokes":[{}]}` が **通ってしまう** ことを既知の穴として固定 (JS 側で守る根拠) |
| `/docs/book-exam.md` | 判断と理由。半年後の自分向け |

**`vercel.json` に追記** (これを忘れると保存形式を直した日に古い `exam-book-model.mjs` を掴んだ端末が古い形式で書き続ける):

```json
{ "source": "/(exam-book.*\\.(mjs|css))", "headers": [{ "key": "Cache-Control", "value": "no-cache, must-revalidate" }] }
```

---

## 2. pdf.js の導入手順

### 2.1 版
**既に vendor 済みの 6.2.108 legacy ESM をそのまま使う。新規に vendor しない。** 3 案とも 3.11.174 を提案しているが、根拠 (「mypage.js が vendor の 3.11.174 を使っている」) は事実誤認で、あれは cdnjs 直リンク。v3 は CVE-2024-4367 (PDF のフォント経由で任意 JS 実行) が未修正で、そのオリジンには Supabase の JWT が載る。

### 2.2 不足分の追加
```bash
npm pack pdfjs-dist@6.2.108
tar xzf pdfjs-dist-6.2.108.tgz package/cmaps package/standard_fonts
mv package/cmaps package/standard_fonts vendor/pdfjs/
git add vendor/pdfjs/cmaps vendor/pdfjs/standard_fonts && git commit
```
`cmaps/` が無いと非埋め込み CJK が **エラーにならず空白で描画される**。

### 2.3 読み込みと worker
```js
// exam-book-pdf.mjs
import * as pdfjsLib from '/vendor/pdfjs/pdf.min.mjs?v=6.2.108';
pdfjsLib.GlobalWorkerOptions.workerSrc = '/vendor/pdfjs/pdf.worker.min.mjs?v=6.2.108';
```
- worker は **同一オリジン必須**。v6 は module worker として起動する (`{type:'module'}`)。vendor 配置なのでこれで通る。
- worker 起動に失敗すると fake worker (メインスレッド) に落ちる。動くが描画中にペンが固まるので、`getDocument` の 1 ページ目描画が 3 秒を超えたら画面に「表示が重くなっています。再読込してください」を出す (黙って遅くしない)。
- **参照している `?v=` と `vendor/pdfjs/VERSION` の一致をゲートが検査する** (ファイル名の存在確認ではなく VERSION との照合。案 3 のゲートは実在しないファイル名を照合して緑になる形だった)。

### 2.4 PDF の取得
```js
const { data, error } = await sb.storage.from('book-pdfs').createSignedUrl(book.pdf_path, 3600);
const res  = await fetch(data.signedUrl);         // 進捗は Content-Length + reader で表示
const buf  = await res.arrayBuffer();             // ★原本は保持する
const doc  = await pdfjsLib.getDocument({
  data: new Uint8Array(buf.slice(0)),             // worker に transfer されて detach するので複製を渡す
  cMapUrl: '/vendor/pdfjs/cmaps/', cMapPacked: true,
  standardFontDataUrl: '/vendor/pdfjs/standard_fonts/',
  isEvalSupported: false,
}).promise;
```
- **署名 URL を getDocument に直接渡さない**。Range 遅延取得だと 60 分超の模試の途中で署名が切れ、まだ見ていないページが開けなくなる。
- 取得は 1 回だけ・失敗したら署名を取り直して 2 回まで再試行。それでも駄目なら **受験を開始させない** (attempt を insert しない)。
- 進捗バーは必須 (bucket 上限 50MB)。
- **PDF バイトを IndexedDB に保存しない** (§14 スコープ外)。共用 iPad に非公開 PDF が残る経路を作らない。
- `pdf_path` が NULL のブックは「この本には冊子 PDF がありません」で終了 (NULL 許容列)。
- 差し替え検知: `sb.storage.from('book-pdfs').list(dir)` で当該オブジェクトの `updated_at` を取り、`localStorage` に `pdfver:{book_id}` として持つ。**再開時に値が変わっていたら書き込みを凍結して警告** (「冊子が差し替えられています。この答案には書き込めません。先生に連絡してください」)。`books` に版列が無いので Storage 側のメタが唯一の手がかり。

### 2.5 CSP
今の `vercel.json` は HTML に CSP を付けていない。**今回も足さない** (130 枚の既存ページを巻き込む変更を 1 画面のために入れない)。将来入れるときに必要な行だけ `docs/book-exam.md` に残す:
```
script-src 'self'; worker-src 'self' blob:; connect-src 'self' https://<ref>.supabase.co; img-src 'self' data: blob:
```

---

## 3. 画面構造とレイヤ

```
.viewer  (overflow:auto — 冊子スクローラ。縦に全ページ)
 └ .page[data-page="n"]           position:relative; width:var(--page-w); aspect-ratio:<Wn/Hn>
    └ .band                        position:absolute; left:0; top:<bt>px; height:<bh>px; right:0
       ├ canvas.pdf                position:absolute; inset:0; width:100%; height:100%
       ├ canvas.dry                同上 (確定ストローク)
       └ canvas.wet                同上 (描いている 1 本だけ)
```
- **座標系の持ち主は `.page` ただ 1 つ。** `.band` は描画のための切り出しで、座標計算には一切出てこない。
- 3 枚の canvas は `.band` を 100% で満たす以外のサイズ指定を持たない。**個別の transform を掛けない・スクロール量でオフセットしない。**
- `.page` は起動時に **全ページ分を先に生成**し、`aspect-ratio` には **そのページの実寸** (§4.4) を入れる。仮寸で作らない。
- ページ枠は `.page` ごとに `ResizeObserver` を張る。回転 / Split View / ソフトキーボード / ボトムシートの開閉 / 仕切りドラッグ — **window の resize も scroll も起きない変化を全部これで拾う** (案 1 が rect キャッシュを壊した経路)。
- DPR 変化 (別 DPI のモニタへ移動) は ResizeObserver では発火しないので、`matchMedia('(resolution: ' + dpr + 'dppx)')` に change リスナを張って再描画する。

---

## 4. 座標変換

### 4.1 入力 → 保存 (唯一の入口)
```js
// exam-book-model.mjs
export const OUT = Symbol('out');
const q4 = v => Math.round(v * 1e4) / 1e4;

export function toNorm(clientX, clientY, rect) {
  if (!rect || !(rect.width > 0) || !(rect.height > 0)) return null;   // ★ 0 除算を作らない
  const x = (clientX - rect.left) / rect.width;
  const y = (clientY - rect.top)  / rect.height;
  if (!Number.isFinite(x) || !Number.isFinite(y)) return null;         // ★ NaN/Infinity は捨てる
  if (x < -0.02 || x > 1.02 || y < -0.02 || y > 1.02) return OUT;      // ★ 枠外は「壁に貼る」のでなく分割
  return [q4(Math.min(1, Math.max(0, x))), q4(Math.min(1, Math.max(0, y)))];
}
```
- `rect` は `.page.getBoundingClientRect()` を pointerdown で 1 回取ってキャッシュし、**ResizeObserver / scroll / visualViewport.resize のいずれかで無効化**して次の点で取り直す。
- `null` が返ったら **その点を捨てる** (ストロークは継続)。`OUT` が返ったら **現在のストロークを確定して新しいストロークを始める** (余白へ引き抜いた線が x=1.0 に直角に貼り付くのを防ぐ)。
- 出てくる値は必ず 0〜1 の有限数・小数 4 桁。DB の CHECK(5) を構造的に満たす。

**なぜこれで拡大・スクロール・回転・DPR にずれないか**
`clientX/Y` も `getBoundingClientRect()` も同じ **レイアウト CSS px 空間**にあるので、比を取った瞬間に「スクロール量」「アプリ内ズーム倍率」「ネイティブのピンチ倍率 (visual viewport)」「端末の物理サイズ」が全部約分されて消える。**DPR はこの式に一度も現れない** — DPR は描画側だけの値。

### 4.2 保存 → 描画
```
pw = .page の CSS 幅,  ph = .page の CSS 高さ
bt = band の top(CSS px, ページ内),  bh = band の高さ
dprEff = min(devicePixelRatio||1, 2) を面積上限で下げた値 (§4.3)

canvas.width  = Math.round(pw * dprEff)
canvas.height = Math.round(bh * dprEff)

X = x * pw * dprEff
Y = y * ph * dprEff - bt * dprEff
ctx.lineWidth = s.w * pw * dprEff      // ★ w は「ページ幅」に対する比。高さは掛けない
```
`ctx.setTransform` は使わない (帯オフセットと DPR を 1 か所の式に閉じ込める)。

### 4.3 canvas 面積上限と帯 (band)
iOS Safari は canvas 面積上限を超えると**例外ではなく真っ白**になる。
```
MAXPX = 4_194_304                       // 2048^2。iOS の実効上限に対して十分安全側
needFull = pw * ph * dpr^2 <= MAXPX
band = needFull ? {bt:0, bh:ph}
                : {bt: clamp(可視上端 - 可視高*0.5), bh: 可視高 * 2}
dprEff = Math.min(dpr, 2, Math.sqrt(MAXPX / (pw * bh)))
```
- 帯は **PDF と ink で必ず同じ `.band` div を共有**するので、2 層が食い違う経路が構造的に無い。
- 帯の張り替えはスクロール停止 120ms デバウンス。張り替え中も既存ビットマップが残るので白飛びしない。
- 生かす `.band` は **可視ページ ±1 の 3 枚まで**。捨てるときは `canvas.width = 0` にしてから参照を切る (iOS はこれをしないとメモリが返らない)。

### 4.4 ページ実寸の先取り (★これが「インクだけ縦に伸びる」事故を消す)
受験開始の**前**に全ページの `getViewport({scale:1})` を取り、`.page` の `aspect-ratio` を確定させる。
```js
for (let n = 1; n <= doc.numPages; n++) {
  const vp = (await doc.getPage(n)).getViewport({ scale: 1 });   // /Rotate を反映済み
  sizes[n] = { w: vp.width, h: vp.height };
}
```
- `page.view` ではなく `getViewport` を使う (回転ページで縦横が入れ替わる)。
- `books.page_count` と `doc.numPages` が食い違ったら **numPages を正**とし、警告を出す。`annotations.page` は 1〜numPages に clamp (範囲外を書くと誰も読まない孤児行になる)。
- **実寸が入るまでそのページには 1 点も書けない** (§8.1 の書き込みゲート)。

### 4.5 ズーム
**方式を 1 つに決める。JS ピンチは実装しない。**
- アプリ内ズームは **段階ボタンのみ**: 幅フィット / ページフィット / 125% / 150% / 200%。
  `--page-w = min(利用可能幅, 利用可能高 × アスペクト比) × zoom`。**高さも入力に入れる** (幅だけだとページフィットが表現できない)。
- ズーム変更 → `--page-w` が変わる → rect が変わる → 比は不変。PDF は 150ms デバウンスで再ラスタライズ、ink は正規化モデルから全描き直し (**ラスタを拡大しないので誤差が蓄積しない**)。
- **読むモードではネイティブのピンチをそのまま許す** (`touch-action: pinch-zoom`)。これは「一時的な虫めがね」であって、ぼやける。精細に拡大したいときは段階ボタン、という役割分担を UI に書く。ピンチ中に sticky/fixed が流れないよう、ペイン内に sticky/fixed を置かない。
- **書くモードではネイティブピンチは効かない** (touch-action: none)。代わりに 2 本指ピンチを検出して**段階を 1 つスナップ**する (§5.3)。

---

## 5. 入力の振り分け (パームリジェクション / スクロール)

### 5.1 モード
| モード | `.viewer` | `canvas.wet/dry` | 指 | ペン |
|---|---|---|---|---|
| 読む (既定) | `touch-action: pan-x pan-y pinch-zoom` | `pointer-events: none` | ネイティブのスクロール・ピンチ | ネイティブのスクロール |
| 書く | `touch-action: none` | `pointer-events: auto` | **1 本 = 何も起きない (紙を押さえられる)** / 2 本 = 自前パン | 描く |
| 書く(指ペン) | 同上 | 同上 | 1 本 = 描く / 2 本 = 自前パン | 描く |

モード切替ボタンは **常時見える位置に固定**。`pointerType === 'pen'` を一度でも観測したら「書く」を既定にし、`localStorage` に覚える。

### 5.2 判定 (これが本体)
```js
function onPointerDown(e) {
  if (mode === 'read') return;                       // ink は pointer-events:none なので来ない
  if (e.pointerType === 'touch') {
    touches.set(e.pointerId, {x: e.clientX, y: e.clientY});
    if (touches.size >= 2) beginPan();
    if (!fingerDraw || touches.size >= 2) return;    // ★ 指では描かない = パームリジェクション本体
  }
  if (e.pointerType === 'mouse' && !(e.buttons & 1)) return;
  if (!page.canInk) return;                          // §8.1 の書き込みゲート
  const p = toNorm(e.clientX, e.clientY, page.rect);
  if (p === null || p === OUT) return;               // ★ 不正な最初の点でストロークを作らない
  target.setPointerCapture(e.pointerId);
  cur = { c: pen.c, w: pen.w, p: [p] };              // ★ c/w/p を必ず同時に埋める (§7.2)
}
```
- **`touch-action: none` にするのが要点。** 案 1・案 2 は `pan-x pan-y` のままだったので、生徒が普通にやる「(1) 小指の付け根を置く → (2) ペンを下ろす」の (1) の時点でネイティブのパンが始まり、ペンを下ろす頃には紙が動いている。`preventDefault()` では止められない (それを止めるのが touch-action の役割)。**紙を押さえて書ける**ことを取る。
- その代償として書くモードでは 1 本指スクロールができない。だから **2 本指パンを自前で実装する** (§5.3) + ページ送りボタン + スクロールバーを常設する。
- `getCoalescedEvents` は **必ずガードする**: `const evs = e.getCoalescedEvents ? e.getCoalescedEvents() : [e];` (無ガードだと未実装端末で pointermove ごとに TypeError → その iPad では 1 本も書けない)。
- `getPredictedEvents` は **使わない** (Safari 未実装、かつ予測点を保存すると実際に書いていない座標が DB に残る)。
- **`pointercancel` / `pointerleave` / `lostpointercapture` で必ずストロークを確定**し、wet レイヤをクリアする。iPadOS の画面端スワイプ・着信・アプリ切替で日常的に飛ぶ。確定処理は「点が 1 つ以上あれば dry へ焼いて dirty、0 なら破棄」。
- **点 0 個のストロークを配列に push しない。** 分割 (点数上限 / `OUT`) のときは「新しいストロークを push するのは次の有効な点が来たとき」にする (案 1 の 1000 点分割は 0 点ストロークを作って DB にページ丸ごと拒否させる経路だった)。

### 5.3 2 本指パン / ピンチスナップ (書くモード専用)
```js
// pointermove, touches.size >= 2
const c = centroid(touches);
viewer.scrollTop  = pan0.top  - (c.y - pan0.y);
viewer.scrollLeft = pan0.left - (c.x - pan0.x);
const r = dist(touches) / pan0.dist;
if (!pan0.zoomed && r > 1.30) { zoomStep(+1); pan0.zoomed = true; }
if (!pan0.zoomed && r < 0.77) { zoomStep(-1); pan0.zoomed = true; }   // 1 ジェスチャ 1 段まで
```
慣性は付けない (自前の慣性はネイティブより必ず劣る。段階ズーム + ページ送りで補う)。

### 5.4 消しゴム
- 方式は **ストローク単位消しゴム 1 択**。白塗り (下の PDF ごと隠れる) もラスタ部分消去 (§5 に保存できない) も採らない。
- 当たり判定は **等方座標に直してから**:
```
ar = ph / pw
d2(P, Q) = (Px-Qx)^2 + ((Py-Qy)*ar)^2          // ページ幅を 1 とする単位に揃える
r = (ERASER_CSS_PX / pw)                        // 既定 12px → 拡大率に依らず指先感覚が一定
hit ⇔ 点-線分距離^2 < (r + s.w)^2
```
ストロークごとに作成時に bbox を持たせ、bbox に触れないものは即除外。
- **切り替えは画面上のボタンのみ。** Apple Pencil のダブルタップ / スクイーズは Safari に一切イベントが来ないので、初回に「ペンのダブルタップは使えません」を明示する (書かないと故障扱いされる)。`e.buttons === 32` の自動切替は **入れない** (iPad では発火せず、誤発火すると書いたつもりの線が既存を消す)。
- undo/redo はメモリのみ 50 手。`{type:'add', i}` / `{type:'erase', items:[{i, stroke}]}` で **元の index に戻す** (順序が変わると重なりの見え方が変わる)。リロードで消えることを docs に明記。
- 「このページを全部消す」は確認ダイアログ + undo 可能。

### 5.5 CSS 雑務 (これが無いと iPad で壊れる)
`.viewer { -webkit-user-select:none; user-select:none; -webkit-touch-callout:none; overscroll-behavior: contain; }` / ツールバーは `touch-action: manipulation`。
**答案ペインにはこれを掛けない** — 短答入力に Pencil を当てたときの iPadOS Scribble はむしろ便利なので殺さない。

---

## 6. 描画 (書き味)

- 描画中は **wet レイヤに新しい線分だけ**を描く (O(1))。全再描画は resize / ズーム / undo / 消しゴム / 読み込み時のみ。
- `pointermove` で rAF に回さずその場で描く (Safari は既に表示レートに合わせて配信している)。
- 平滑化は **中点 + `quadraticCurveTo`** (点は増やさない・描画時のみ)。`lineCap/lineJoin = 'round'`。
- 間引きは **pointerup の確定時に 1 回だけ**: 隣接点が 0.0008 (ページ幅単位) 未満なら捨てる。**保存のたびに間引かない** (同じ線が保存ごとに痩せる)。
- 筆圧は持たない (§5 確定済み)。太さは **固定プリセット 3 段の定数** `0.0015 / 0.003 / 0.006`、色 3 色 `#1b2233 / #ef4444 / #3b82f6`。
  ★ **w を px から計算しない。** 計算して 4 桁丸めすると拡大時に `0.0000` に丸まり、DB の `w > 0` に弾かれてページ全体が保存不能になる。定数なのでこの経路が存在しない。

---

## 7. データモデルと送信前バリデータ

### 7.1 メモリ上の形
```js
pageState[n] = {
  sized:false, loaded:false,          // ★ 両方 true になるまで canInk = false
  strokes: [], rowExists:false, knownUpdatedAt:null,
  dirty:false, inFlight:false, again:false, erasedSinceLoad:false,
  frozen:false, lastError:null,
}
```

### 7.2 `validateStrokes()` — 送信直前に必ず通す (DB の CHECK より厳しい)
DB の `strokes_are_valid()` は **キー欠落を素通しする** (`{}` すら valid)。`JSON.stringify` は `undefined` のキーを黙って落とすので、初期化漏れ 1 行で「保存は 200 成功するのに再読込すると線が消えている」が起きる。ここは JS でしか守れない。

```js
export function validateStrokes(list) {          // → {ok:[...], dropped:[{i, why}]}
  const ok = [], dropped = [];
  for (let i = 0; i < list.length; i++) {
    const s = list[i];
    if (!s || typeof s !== 'object')                       { dropped.push({i,why:'not-object'}); continue; }
    if (typeof s.c !== 'string' || !s.c)                   { dropped.push({i,why:'c'}); continue; }
    if (!Number.isFinite(s.w) || s.w <= 0 || s.w > 0.02)   { dropped.push({i,why:'w'}); continue; }
    if (!Array.isArray(s.p) || s.p.length === 0)           { dropped.push({i,why:'p-empty'}); continue; }
    let bad = false;
    for (const pt of s.p) {
      if (!Array.isArray(pt) || pt.length !== 2) { bad = true; break; }
      const [x, y] = pt;
      if (!Number.isFinite(x) || !Number.isFinite(y) || x < 0 || x > 1 || y < 0 || y > 1) { bad = true; break; }
    }
    if (bad) { dropped.push({i,why:'point'}); continue; }
    ok.push({ c: s.c, w: s.w, p: s.p });                   // ★ 余計なキーを持ち込まない
  }
  return { ok: ok.slice(0, 5000), dropped };
}
```
- **不正なストロークは捨てて残りを保存する。** 1 本のために 1 ページ (数千本) を人質に取らせない。`dropped` が空でなければ (a) console.error、(b) ヘッダに「保存できなかった線が n 本あります」、(c) ローカル写しには**捨てる前の生データも**残す (原因調査用)。
- 上限: **4500 本で警告、4800 本で新規ストロークを断る** (5000 ちょうどで DB に拒否されると原因が分からない)。

### 7.3 読み込み側
```js
const raw = row?.strokes;
const okShape = raw && typeof raw === 'object' && String(raw.v) === '1' && Array.isArray(raw.strokes);
```
★ `raw.v === 1` の厳密比較にしない。DB は `->>'v'` 比較なので `"v":"1"` (文字列) の行も存在しうる。書き手と読み手で厳しさを揃える (揃えないと読み捨てて全消しになる)。読んだ直後にも `validateStrokes` を通す。

---

## 8. 自動保存

### 8.1 書き込みゲート (★ 消失を防ぐ最重要の不変条件)
```
page.canInk = page.sized && page.loaded && !page.frozen && !submitted && !pdfReplaced
```
- `sized` … §4.4 のページ実寸が入った (入る前に書くと基準系が後から変わってインクだけ縦に伸びる)
- `loaded` … **そのページの annotations がサーバから届いた** (届く前に書いて flush すると、ページ丸ごと上書きなので既存の書き込みが全消しになる)
- ゲートが下りている間はペンを受け付けず、ページ枠に「読み込み中」を出す。**「取得失敗」と「白紙」を絶対に区別する** (失敗は loaded=false のまま)。

annotations は attempt 確定直後に **1 クエリで全ページ分**取る。数 MB になる場合に備え、`.order('page')` で取りつつ、**可視ページが含まれるレスポンスが返った時点で** そのページの `loaded` を立てる (全件待ちで全ページが書けない時間を作らない)。取得失敗は再試行 (3 回) → 失敗したら受験開始させない。

### 8.2 タイミング
| きっかけ | 動作 |
|---|---|
| `pointermove` | **絶対に送らない** |
| ストローク確定 (`pointerup`/`pointercancel`)・消しゴム操作終了 | **① ローカル写しを同期で書く ② dirty=true ③ デバウンスタイマー開始** |
| 最終描画から **1.2 秒アイドル** | flush |
| 最初に dirty になってから **8 秒** | 強制 flush (書き続けても必ず落ちる) |
| ページが可視範囲から 1 画面ぶん外れた / モード切替 / ズーム変更 | 即時 flush |
| `visibilitychange → hidden` | 即時 flush (ベストエフォート) |
| 提出 | §10 の手順 |

★ **`pagehide` での送信は「最後の砦」に数えない。** `sendBeacon` は `apikey`/`Authorization` を付けられず 401、`fetch(keepalive:true)` はボディ 64KB 上限で手書きページ (数百 KB) は送れない。ハンドラは置くが、保険は **ローカル写し** の側にある。

### 8.3 ローカル写し (これが唯一の実質的な保険)
- **`pointerup` の時点で同期的に書く** (flush 時ではない)。守りたい窓は「サーバに入る前に iOS がタブを捨てる」で、それはまさにアイドル 1.2 秒の中にある。
- キー `ink:{attempt_id}:{page}`、値はページ全量 JSON。
- ページ JSON が **256KB を超えたら追記方式に切り替え**: 本体は flush 成功時のみ更新し、`pointerup` では `ink:{attempt}:{page}:tail` に最後の 1 ストロークだけを追記する (毎回 300KB を同期 stringify するとペンがカクつく)。
- `QuotaExceededError` は握って: 他 attempt の写しを古い順に削除 → 再試行 → それでも駄目なら **ヘッダに「端末側の控えが取れていません」を出す** (黙って落とさない)。
- サーバ保存が確定したら消す。復帰時にローカルの方が新しければ「この端末の書き込みを復元しますか」。
- **提出後も自動では消さない** (§10 の 42501 の扱いを参照)。

### 8.4 書き込み文 (CAS。upsert は使わない)
```js
// 初回 (行が無い)
const r = await sb.from('annotations')
  .insert({ attempt_id, page, strokes: {v:1, strokes: ok} })
  .select('updated_at').single();
// 2 回目以降 (★ 楽観的排他)
const r = await sb.from('annotations')
  .update({ strokes: {v:1, strokes: ok} })
  .eq('attempt_id', attempt.id).eq('page', page)
  .eq('updated_at', st.knownUpdatedAt)
  .select('updated_at');
if (!r.error && r.data.length === 0) → 競合 (§8.6)
```
- `updated_at` は **サーバ側トリガが now() で打つ**ので、クライアントの時計に依存しない単調な版番号そのもの。「DB に版番号が無いから防げない」は誤り。
- 成功したら `knownUpdatedAt` を返り値で更新する。
- **同一ページに 2 本同時に飛ばさない**: `inFlight` 中に dirty になったら `again` を立て、完了後に 1 回だけ再投入。
- ★ **`update` が 0 行でもエラーにならない**。RLS で行が見えないときも 0 行。**必ず返却行数で判定する** (`error` を見るだけだと「保存しました」と出しながら 1 文字も書かれない)。

### 8.5 エラー分類 (これを 4 分岐にすることが設計の核)
`exam-book-sb.mjs` の `classify(err, rowCount)`:

| 分類 | 条件 | 挙動 |
|---|---|---|
| **形式 (非リトライ)** | `23514` / `22P02` / 400 | **再送しない。** `validateStrokes` を再適用して不正ストロークを隔離 → 1 回だけ再送。それでも駄目なら該当ページを frozen にし、**赤で生徒に通知** + ローカル写しは残す。★ここを再試行にすると 1 点の NaN で 30 秒ごとに永久に叩き続け、試験が終われなくなる |
| **凍結 (非リトライ)** | `42501` / 403 | **提出前なら異常**: 「別の端末でこの答案が提出されました」→ 全ページ frozen・読み取り専用・**ローカル写しを消さない**・「保存できていない書き込みがあります」を出す。**提出後なら正常**: 静かにキューを止める (赤く出さない) |
| **認証** | `401` / `PGRST301` | `sb.auth.refreshSession()` → 成功なら 1 回だけ再送。失敗なら「ログインし直してください (書き込みはこの端末に残っています)」 |
| **通信 / 5xx** | それ以外 | 指数バックオフ 1s→2s→4s→…→30s。dirty は落とさない。ヘッダに「未保存 n ページ」を出し続ける |
| **沈黙** | `error === null && rowCount === 0` | 競合として §8.6 へ |

### 8.6 競合 (2 端末 / 2 タブ)
- 同一ブラウザの 2 タブ目は `BroadcastChannel('exam-book:'+attempt_id)` + localStorage のリーダー選出で **即座に読み取り専用**にする。
- 別端末は CAS の 0 行返却で **上書きする前に**検出できる。検出したらそのページの自動保存を止めてダイアログ:
  1. **両方を残す** … ★このページで **消しゴムを使っていない (`erasedSinceLoad === false`) ときだけ出す**。サーバ側の最新を読み直し、`ローカルの読み込み後に追加した分` を末尾に連結して CAS で再送。手書きは追記型なので両端末の書き込みが両方残る。
  2. この端末の書き込みで上書き (サーバの `updated_at` を読み直して CAS)
  3. サーバ側を読み直す (この端末の続きは破棄。破棄前にローカル写しへ退避)
- 自動マージはしない (消しゴムの結果を機械的に合流させると「消したはずの線が戻る」)。

---

## 9. 答案 (`answers`) と起動フロー

### 9.1 起動状態機械
```
BOOT
 → 認証確認 (未ログイン → /auth へ)
 → books を 1 件取得 (is_published)。pdf_path が NULL → NO_PDF で終了
 → PDF バイト取得 (進捗表示・2 回まで再試行) — 失敗 → PDF_ERROR で終了 (attempt を作らない)
 → 全ページ寸法の先取り → .page 生成 (sized=true)
 → attempt の確定:
      select attempts where book_id & user_id & submitted_at is null order by started_at desc
      ・1 件 → それを再利用
      ・2 件以上 → 最新を再利用し、警告「受験中の答案が他に n 件あります。
                   ★この本の正解と解説は、それを全部提出するまで表示されません」
                   → 「古い答案を開いて提出する」導線を出す。★削除ボタンは出さない (cascade で手書きごと消える)
      ・0 件 → insert(...).select().single()      ← ここで初めて started_at が動く
 → student_questions を取得 (0 行 → 「この冊子は現在公開停止です」で凍結)
 → answers を取得 → 不足分だけ insert (§9.2)
 → annotations を取得 (loaded=true)
 → READY (受験中)
```
★ **attempt の insert は PDF ダウンロードと寸法取得の後**。先に insert すると数十秒のダウンロードが試験時間から引かれる。

### 9.2 `answers` の書き方 (upsert 禁止)
```js
// 開始時: 不足分だけ insert (デモ supabase/demo/index.html:392-402 と同じ形)
const missing = questions.filter(q => !have[q.id])
  .map(q => ({ attempt_id, question_id: q.id, user_answer: null, time_spent_sec: 0 }));
await sb.from('answers').insert(missing).select();      // 23505 → 再 select して再計算 (最大 2 回)

// 以後: 明示列だけの update
const r = await sb.from('answers')
  .update({ user_answer: v, time_spent_sec: t })        // ★ この 2 列以外を絶対に入れない
  .eq('attempt_id', attempt.id).eq('question_id', qid)
  .select('question_id');
if (!r.error && r.data.length === 0) → 凍結 or 権限として扱う (「保存しました」と出さない)
```
- **`upsert` は使えない。** PostgREST は payload の全列を `ON CONFLICT DO UPDATE SET` に並べるので `attempt_id`/`question_id` が SET に入り、列 grant に無いため **衝突していない初回 insert でも 42501** (権限判定はプラン時)。
- 行オブジェクトをそのまま `.update(row)` に渡さない (`id`/`is_correct` が payload に入って permission denied)。**送信オブジェクトを組み立てる関数を 1 つに絞り、ゲートで守る**。
- 事前作成の副作用: `submit_attempt` の `answered_count` は常に `question_count` と等しくなる。**結果表示に answered_count を使わない。** 進捗は自前で `user_answer` が非空の件数を数える。
- 事前作成の必要性: `student_questions.revealed` は「提出済み attempt に**その設問の answers 行がある**」が条件。行が無い設問は **提出後も永久に正解と解説が返らない** (提出後は insert も 42501 で塞がる)。だから事前作成は必須で、さらに §10 で行数を照合する。

### 9.3 入力・レイアウト
- 選択肢の値は **`String(i + 1)` の 1 箇所だけ**で作る (DB の `correct_answer` は 1 起算の数字文字列。0 起算や 'A'/'①' を書くと全員 0 点になり、それを落とす検査がどこにも無い → ゲートで守る §12)。
- choice = 44px 以上のピル (`role=radiogroup`)、再タップで解除可。change で即保存。
- short = `<input type=text autocapitalize=off autocorrect=off spellcheck=false>` (iOS の自動修正で別語に化けるため必須)。600ms デバウンス + blur。
- レイアウトは 2 種類だけ (`matchMedia` 1 本): 横 ≥1000px = 左冊子/右答案 (仕切りドラッグ可・比率は localStorage)、縦 = ボトムシート (peek / half / full)。
- 設問 ⇄ ページ連動: 設問タップ → そのページへスクロール + ハイライト / スクロール → そのページの設問群へ自動スクロール (**生徒が答案ペインを手で動かしたら 5 秒間は自動追従を止める**。止めないと震える)。
- **`questions.page` が NULL の設問は「ページ指定なし」グループとして常に先頭に出す。** peek 表示でも必ず出す (「このページの設問だけ」で絞ると NULL が永久に見えなくなり解答できない)。
- タイマー: `books.time_limit_sec` (NULL = 無制限 → 自動提出しない) と `attempts.started_at` から計算。**現在時刻はブラウザの時計ではなく `serverNow()`** = `sb` の fetch ラッパが記録した最後のレスポンスの `Date` ヘッダ + 経過。`visibilitychange` 復帰で必ず再計算する。★制限時間は画面上の約束にすぎない (RPC は締切を見ない) と docs に明記。

---

## 10. 提出フロー (状態遷移)

```
READY
 │ 提出ボタン / 残り 0 秒
 ▼
CONFIRM            未解答の設問番号 (ページ付きジャンプリンク) / 未保存ページ数 /
 │                 「提出すると解答も書き込みも変更できません」
 ▼ (はい)
FREEZE             ★最初に凍結: ink を pointer-events:none、入力 disabled、
 │                 提出ボタン disabled、自動保存タイマー全停止
 ▼
DRAIN              ★送信キューを drain: in-flight を await し、バックオフ待ちを全部取り消す
 │                 (これをしないと RPC 後に届いた再送が 42501 で黙って消える)
 ▼
FLUSH_ANSWERS      デバウンス保留中の answers を全部 flush
 │  失敗 → SUBMIT_BLOCKED (凍結解除・「解答が保存できていません。通信を確認して再度提出」)
 ▼
RECONCILE          select count(answers where attempt) と questions 件数を照合
 │                 不足があれば不足分だけ insert (23505 → 再 select、最大 2 回)
 │  失敗 → SUBMIT_BLOCKED   ★ここを飛ばすと、その設問は無得点・復習キュー不参加・
 │                            解説が永久に出ない の三重障害になる
 ▼
FLUSH_INK          annotations の dirty を flush。★ベストエフォート。
 │                 ページあたり 15 秒 / 全体 45 秒でタイムアウト (時間切れ自動提出時は全体 20 秒)
 │  一部失敗 → CONFIRM_INK: 「手書きの一部が保存できていません (n ページ)。
 │                提出すると、この書き込みは二度と保存できません。提出しますか」
 │                → いいえ = 凍結解除して READY / はい = 次へ (ローカル写しは残す)
 ▼
SUBMITTING         sb.rpc('submit_attempt', {p_attempt})
 │   成功            → RESULT
 │   42501           → attempts を select し submitted_at を確認
 │                      入っている → RESULT (往復で応答が落ちただけ)
 │                      入っていない → SUBMIT_BLOCKED (「別ユーザでログインしていませんか」)
 │   通信断          → RETRY_SUBMIT (再試行可。未提出のときしか通らないので二重採点は起きない)
 ▼
RESULT             attempts / student_questions / answers を読み直す。
                   ★画面は 2 ペインのまま「復習モード」に変わる。
                   冊子と手書きはそのまま残し、読み取り専用にする。
                   ★取得した correct_answer / explanation を **メモリに保持**する (下記)
```

**提出後の扱い**
- annotations の 42501 は **正常** として静かに扱う (再試行しない・赤く出さない)。
- ただし **FLUSH_INK で送り切れなかったページのローカル写しは消さない**。「この端末に保存できなかった書き込みが残っています」を結果画面に出し、先生への連絡導線を置く (黙って捨てない)。
- 「もう一度受験する」は結果画面の**下の方**に置き、確認を挟む。★押した瞬間に新しい未提出 attempt ができ、`student_questions.revealed` が **ブック単位で false に落ちる** = 前回の結果画面からも正解と解説が消える (`is_correct` だけ残るので「○× は出るのに解説が空」という一番分かりにくい壊れ方)。ダイアログに「開始すると前回の解説が見えなくなります」と書き、かつ結果表示は再取得ではなく**メモリに保持した値**を使い続ける。
- 誤答は RPC が `review_items` に積むので復習キューへの導線を出す。

---

## 11. 致命的問題 → この設計での防ぎ方 (対応表)

| # | 批評で挙がった致命的問題 | この設計での防ぎ方 |
|---|---|---|
| F1 | `rect.width===0` で 0 除算 → NaN → `JSON.stringify` が null → 23514 でページ全体が永久に保存不能 | `toNorm` が `rect.width>0 && rect.height>0` と `Number.isFinite` を検査し、通らない点は **null を返して捨てる** (§4.1)。さらに送信直前に `validateStrokes` が `Number.isFinite` を必須検査 (§7.2)。加えて 23514 は **非リトライ** (§8.5) |
| F2 | 1000 点分割・pointercancel で **0 点ストローク** が残り 23514 | 「新しいストロークは次の有効な点が来たときに push」に変更 (§5.2)。`validateStrokes` が `p.length===0` を落とす |
| F3 | DB の CHECK が **キー欠落を素通し** (`{}` が valid、`c`/`w`/`p` が undefined だと stringify で消える) → 保存は成功するのに再読込で線が消える | `validateStrokes` が c/w/p の **存在と型を必須検査**し、送信オブジェクトは `{c,w,p}` を明示的に組み直す (§7.2)。`supabase/tests` に「この穴は DB では塞がっていない」を回帰として固定 |
| F4 | rect キャッシュがボトムシート開閉 / 仕切りドラッグで壊れ、線の途中からずれる (window の resize も scroll も起きない) | `.page` ごとに **ResizeObserver** を張って rect を無効化 (§3)。DPR 変化は `matchMedia('(resolution: Xdppx)')` で別途拾う |
| F5 | **実寸未確定のページ**に書くと、実寸確定時にインクだけ縦に伸びる | 受験開始の**前に全ページの `getViewport({scale:1})` を取得**して aspect-ratio を確定 (§4.4)。かつ書き込みゲートに `sized` を入れる (§8.1) |
| F6 | **未ロードのページ**に 1 本書くと、そのページの既存ストロークが全消し | 書き込みゲートの `loaded` (§8.1)。「取得失敗」と「白紙」を区別する。ゲートが下りている間はペンを受け付けない |
| F7 | localStorage 写しが **flush 時に書かれる** ため、守りたい窓 (pointerup〜1.5 秒) が空いている | **pointerup で同期的に書く** (§8.3)。大きいページは tail 追記方式に切替 |
| F8 | `pagehide` flush は sendBeacon (ヘッダ不可) / keepalive (64KB) のどちらでも実現できないのに「必須」としていた | pagehide は**ベストエフォートに格下げ**。保険は §8.3 のローカル写し。`visibilitychange:hidden` での flush は行う (§8.2) |
| F9 | 2 端末 last-writer-wins を「構造的に防げない」と誤断 / upsert だと検出すらできない | `updated_at` (サーバトリガの now()) を版番号として **CAS update** (§8.4)。0 行 = 上書きする**前**に検出。消しゴム未使用なら**追記マージで両方残す** (§8.6) |
| F10 | 2 タブの SELECT→UPSERT が TOCTOU で両方通り全消し | CAS は 1 文で原子的。加えて同一ブラウザは BroadcastChannel で 2 タブ目を読み取り専用に |
| F11 | 他端末で先に提出されると 42501 を **30 秒ごとに永久リトライ**し、生徒には「未保存」だけ出る | エラー 4 分類 (§8.5)。提出前の 42501 = 異常として全ページ frozen + 明示通知 + ローカル写し保持 |
| F12 | 23514 の無限リトライ + 「flush 失敗なら提出させない」で **試験が終われなくなる** | 23514 は非リトライ (§8.5)。かつ提出は **answers = 必須 / annotations = ベストエフォート + タイムアウト** に分離 (§10) |
| F13 | 提出後、IndexedDB/ローカルに残った未送信分が 42501 で **黙って捨てられる** | 提出後の 42501 は静かに扱うが、**ローカル写しは消さない**。結果画面に「保存できなかった書き込みが残っています」を出す (§10) |
| F14 | 提出直前の flush は待つが、**バックオフ待ちの再送**を待たない → RPC 後に届いて 42501 で消える | 提出手順に **DRAIN** 状態を置き、in-flight を await + 予約済み再送を全取り消し (§10) |
| F15 | `answers` の upsert が列 grant で **初回から 42501** (= 全問白紙 0 点) | upsert を使わない。開始時に不足行だけ insert、以後は 2 列だけの update (§9.2)。ゲートで `.upsert(` を禁止 |
| F16 | 提出後の `.update()` は **0 行更新でもエラーにならない** → 「保存しました」と出しながら書かれない | すべての update は `.select()` を付けて **返却行数で判定** (§8.4 / §9.2) |
| F17 | `answers` 行の欠落 → 無得点・復習キュー不参加・**解説が永久に非表示** | 提出手順に **RECONCILE** (行数照合 + 不足補填) を必須ステップとして置く (§10) |
| F18 | 常に `attempts` を insert → 二重 attempt → そのブックの正解と解説が全部伏せられる | 起動時に未提出 attempt を必ず再利用。複数あれば警告 + 「開いて提出する」導線 (§9.1) |
| F19 | 未提出 attempt の「破棄」導線が **cascade で手書き全消し** | **削除ボタンを出さない** (§9.1)。復旧は提出で行う |
| F20 | pdf.js 3.11.174 への降格 (CVE-2024-4367 未修正、vendor に 2 版同居、ゲートが実在しないファイル名を照合) | vendor 済みの **6.2.108 legacy ESM をそのまま使う**。cmaps/standard_fonts のみ追加。ゲートは `vendor/pdfjs/VERSION` と参照側 `?v=` を照合し、**vendor/pdfjs に版が 1 つしか無いこと**も見る (§2 / §12) |
| F21 | ネイティブピンチ (`pinch-zoom`) と JS ピンチの二重仕様 → JS 側が一度も走らず必ずボケる | 方式を 1 つに固定 (§4.5)。**読むモード = ネイティブピンチのみ (虫めがね扱い) / 書くモード = touch-action:none + 2 本指で段階スナップ**。JS の連続ズームは実装しない |
| F22 | `pointercancel` 未処理 → 書きかけの 1 本が黙って消える / capture 無しで次の描画に直線が連結 | `setPointerCapture` + `pointercancel`/`pointerleave`/`lostpointercapture` で必ず確定し wet をクリア (§5.2) |
| F23 | パームリジェクションが「手のひらで線が引かれること」しか防げず、**手のひらでページが動く** (最も普通の持ち方で破綻) | 書くモードは `.viewer { touch-action: none }`。1 本指 touch は**何も起こさない**＝紙を押さえられる。スクロールは 2 本指の自前パン + ページ送り (§5.1-5.3) |

**併せて仕様に反映した「serious」**: `getCoalescedEvents` のガード / `getPredictedEvents` 不使用 / `w` を定数プリセットにして下限割れを構造的に排除 / `String(raw.v)==='1'` で読む / 枠外の点は clamp でなく分割 / `answered_count` を使わず自前カウント / 選択肢は `String(i+1)` の 1 箇所 / `questions.page` NULL の常時表示 / `pdf_path` NULL / `is_published` を戻されたときの 0 行 / PDF 差し替え検知 / Pencil ダブルタップの明示 / `e.buttons===32` の自動切替を入れない / exam-book*.mjs の no-cache ヘッダ / 時間切れ自動提出の annotations タイムアウト / サインアップを招待制にする運用前提。

---

## 12. ゲート (`scripts/book_exam/check_book_exam.py`)

**引数なしの既定は「配信する全ファイル」。何を検査したか必ず印字。違反で `sys.exit(1)`。作ったその場でコミットする** (CLAUDE.md)。`scripts/run_all_gates.py` が `check*` で拾う。

静的検査:
1. `vendor/pdfjs/VERSION` と HTML/JS の `?v=` の一致。**vendor/pdfjs に版ディレクトリが 2 つ以上ないこと**。
2. `exam-book*` に CDN 直リンク (`cdnjs`/`jsdelivr`/`unpkg`) が無いこと。
3. `answers` に対して `.upsert(` が現れないこと。`answers` の `.update(` の引数リテラルが `user_answer` と `time_spent_sec` 以外のキーを持たないこと。
4. `String(` で選択肢値を作る箇所が **1 関数だけ**であること (`choiceValue()` 以外で `q.choice_count` から値文字列を生成していない)。
5. `annotations` への書き込みが `validateStrokes(` を通っていること (呼び出しの直近に現れること)。
6. `service_role` / 生の JWT / 生徒氏名の混入禁止 (`check_no_pii.py` と重複してよい)。
7. `vercel.json` に `exam-book` の no-cache ヘッダがあること。

実 DB 往復検査 (`scripts/english_schema/check_schema.py` の使い捨て DB 基盤を再利用):
8. `node scripts/book_exam/roundtrip_strokes.mjs` が **実物の `exam-book-model.mjs`** を import して異常系入力から JSON を生成 → その JSON を `strokes_are_valid()` に食わせて **全部 true** になること。入力に必ず含める: `rect.width=0`、`clientX=NaN`、点数上限直後の pointercancel、枠外へのドラッグ、負座標、`{c:undefined}`、4900 本、5001 本、`w` が px 由来で 0 に丸まる値、空 `p`。
   ★ 「clamp01 という文字列が存在する」ことを grep する検査は無意味 (吐かれる JSON が通るかとは無関係)。ここは**実際に JSON を生成して DB に投げる**。

`supabase/tests/10_schema_expectations.sql` への追記:
- (I-a) `answers` を PostgREST 形の upsert (`SET` に attempt_id/question_id を含む) で書くと permission denied になること。
- (I-b) `{"v":1,"strokes":[{}]}` が `strokes_are_valid` を **通ってしまう**こと (JS 側で守る必要があるという事実を固定)。

---

## 13. 実装順序 (この順に緑にする)

1. `exam-book-model.mjs` + `roundtrip_strokes.mjs` + ゲート → **先に往復検査を緑にする** (ここが全部の土台)
2. vendor に cmaps/standard_fonts を追加 → PDF 1 ページ表示 + 全ページ寸法先取り
3. `.page`/`.band` のレイヤ + 描画 (読み取り専用) + 既存 annotations の読み込み
4. 入力振り分け (ペン / 2 本指パン / モード) + 消しゴム + undo
5. `exam-book-sync.mjs` (CAS・エラー 4 分類・ローカル写し) — **単体で「機内モードにして書く → 復帰して保存される」を実機で確認**
6. 答案ペイン + 起動状態機械
7. 提出状態機械 (DRAIN / RECONCILE を含む) + 結果表示
8. iPad 実機での確認項目: 手のひら先着 / 電話着信 (pointercancel) / アプリ切替 → 復帰 / 回転 / Split View / 2 端末同時 / 別端末から提出 / 時間切れ自動提出 / 機内モード提出

---

## 14. 今回は作らないもの (スコープ外) と理由

| 作らないもの | 理由 |
|---|---|
| **textLayer (PDF 内の検索・コピー・読み上げ)** | DOM がペンのポインタを奪い、書こうとして選択が始まる。書き味を採る。**アクセシビリティ上は明確な後退**なので、必要になったら「読むモード限定・`pointer-events:none`」で後付けする |
| **筆圧 / 入り抜き** | §5 が筆圧を持たない (確定済み)。線幅の速度変調はストローク分割が要り 5000 本上限を食う |
| **部分消し (点消し・ストローク分割)** | §5 の形のままでも表現できるが、ストローク数が増えて 5000 本上限に近づく。上限に当たると **そのページの保存が丸ごと止まる**方が痛い。v2 で上限管理とセットで |
| **PDF バイトの IndexedDB キャッシュ / オフライン受験** | 共用 iPad に非公開 PDF が残る。消し損ねの経路も残る。`sw.js` は無効化専用 SW なので触らない |
| **JS による連続ピンチズーム** | ネイティブピンチと二重仕様になる (F21)。段階ズーム + 読むモードのネイティブピンチで代替 |
| **帯より細かいタイル描画** | 高倍率での精細さは帯 (§4.3) で確保する。完全なタイル管理は canvas 破棄の順序が増え、白飛びの経路が増える |
| **Supabase Realtime による複数端末同時編集** | 依存を増やす。CAS + 追記マージ (§8.6) で「消える」ことだけは防ぐ |
| **undo/redo の永続化** | DB は最新状態しか持てない (スキーマ変更不可) |
| **サーバ側での締切強制** | `submit_attempt` は経過秒を記録するだけ。RPC を触れない前提では塞げない。**画面上の約束にすぎない**と docs に明記 |
| **ページ回転 UI / 図形ツール / テキスト注釈** | §5 のストローク配列で表現できない |
| **PDF 差し替えへの自動追従** | 座標は 0〜1 なので数値は生き残るが、ページ挿入で `page` がずれ、比が変われば相対位置もずれる。**検知して凍結する**だけにする (§2.4)。冊子の差し替えは運用上「別のブック」として扱う |

**運用側の前提条件 (設計ではないが、これが無いと教材が流出する)**: `exam-book-config.mjs` に anon key を置く前に、Supabase 側でサインアップを**招待制 / メール確認 ON / ドメイン制限**のいずれかにすること。開いたままだと第三者が登録 → 公開ブックの PDF を署名付き URL で取得 → 適当に提出して `correct_answer` と `explanation` まで取れる。
---

## 15. 実装の記録 (2026-08-14)

§13 の 1〜7 まで実装した。**8 (iPad 実機) だけが未実施**で、これは手元に実機が要る。

### 15.1 実装したファイル

| パス | 中身 |
|---|---|
| `exam-book.html` / `.css` | 骨組みとレイアウト。`user-scalable` は切っていない。ペイン内に `position: sticky/fixed` を置いていない |
| `exam-book-config.mjs` | `SUPABASE = {url, anonKey}` と `assertAnonKey()`。**url / anonKey は空のまま**なので、貼るのは運用者 |
| `exam-book-sb.mjs` | クライアント生成 / fetch ラッパ (`Date` ヘッダ → `serverNow()`) / `classify()` |
| `exam-book-model.mjs` | 純関数。`toNorm` / `thin` / `strokeHit` / `validateStrokes` / `parseStrokes` / `mergeAppend` / undo スタック |
| `exam-book-pdf.mjs` | 全バイト取得 → 全ページ寸法の先取り → ページ枠生成 → DPR 込みの描画 (面積上限 12M・renderTask キャンセル) |
| `exam-book-ink.mjs` | 入力振り分け (1 本指 touch は無反応 / 2 本指パン)、wet-dry 2 枚、消しゴム、undo/redo |
| `exam-book-sync.mjs` | `LocalCopy` / `TabLock` / `InkQueue` (CAS・単一飛行・バックオフ) / `AnswerQueue` (seed・2 列 update・reconcile) / `submitAttempt` |
| `exam-book-answers.mjs` | 答案ペイン。`choiceValue()` はここ 1 箇所 |
| `exam-book.mjs` | 起動状態機械 (§9.1) と提出状態機械 (§10)、タイマー、仕切り / ボトムシート |

`vercel.json` に `"/(exam-book.*\\.(mjs|css))"` の `no-cache` を追加済み。

### 15.2 検査 (2 本。どちらも `scripts/run_all_gates.py` が拾う)

**`scripts/book_exam/check_book_exam.py`** — 静的 + 使い捨て DB との往復。
pdf.js の版照合 / `answers` の `.upsert(` 禁止 / `.update(`・`.insert(` に `.select()` があるか /
CDN 直リンク / 往復検査がモデルを写経していないか / `vercel.json` の no-cache / anon key の実値 /
`answers` の update に余計な列が無いか / `choiceValue()` が 1 箇所か / `annotations` の書き込みが
`validateStrokes()` を通っているか / **JS が掴む `#id` と `[data-*]` が HTML に実在するか** / 構文。

**`scripts/book_exam/check_exam_book_browser.py`** — 実 Chromium で通しで動かす (**45 項目**)。
起動 → 解答 → **答案の通信断と復帰** → 手書き → 消しゴム → 戻す → **通信断のまま書いて提出** →
結果 → **iPad 縦画面 (820×1180) で読み込み直し** → **書き込みの取得失敗**。差し替えるのは `exam-book-config.mjs` と `supabase-js` の **2 本だけ**で、
`exam-book*.mjs` / pdf.js / CSS / HTML は配信するものそのものを読ませる。
偽 Supabase は `updated_at` の CAS と提出後の 42501 を本物と同じ意味で返す。
200 秒のウォッチドッグを持つ (**ハングは「検査していない」と同じ**なので必ず赤で終わる)。
`playwright-core` か Chromium が無い環境では **飛ばしたことを印字して** 0 で終わる (黙って緑にしない)。

### 15.3 ★ 検査を壊して確かめた (これをやらないとゲートは飾り)

書いた検査が本当に落とせるかを、**コードをわざと壊して 1 件ずつ確認した**。
静的側 9 件・ブラウザ側 12 件。この作業で **自分の検査の穴が 6 つ**見つかった:

| 検査の穴 | 直し方 |
|---|---|
| 選択肢を `data-value="2"` で押していた | 値が何であれ同じ値が保存されるので **必ず通る**。**何番目のピルか**で押して、保存値が 1 起算かを見る。満点判定も足した |
| 手のひら排除の確認が `pointerup` の 300ms 後 | デバウンス (1.2 秒) の内側なので、線が引かれていても 0 件に見える。保存まで待ってから数える |
| 提出前に手書きを保存し終えてから提出していた | `FLUSH_INK` を消しても通ってしまう。**通信断のまま書いて、そのまま提出する**形に変えた |
| `aspect-ratio` を「数字 / 数字 の形か」で見ていた | 仮寸 `1 / 1.414` でも通る。実寸 595×842 と照合する。**許容差 1e-3 でも通ってしまう** (差は 5.6e-4) ので 1e-4 にした |
| 書き込みの **取得失敗**を一度も起こしていなかった | 取得を落として再読込し、「白紙で受験を始めない」ことを見る (F6) |
| 結果画面の**位置**を見ていなかった | 値の検査は全部通るのに右隣に並ぶ。矩形で「答案の下にある」ことを見る |
| 縦画面の検査を **リサイズだけ**で済ませていた | 横画面のままだと答案リストがそもそもスクロールしないので、勝手にスクロールする不具合が起きていても `scrollTop` は 0 のまま。**読み込みからやり直す**形に変えた |

**コードの方の欠陥も 4 つ見つかった** (どれもゲートではなく読み返しで発見。ゲートは直した後の回帰用):

| 欠陥 | 直し方 |
|---|---|
| `AnswerQueue.flush()` の再帰に上限が無い | 通信断だと `want` に戻り続けるので **バックオフ無しで叩き続け、提出手順の `FLUSH_ANSWERS` の await が永久に返らない**。再帰を 1 段までにした |
| `#pane` が横並びで、結果が答案の**右隣**に出る | `#pane-body` を挟んで中身を縦に積む (取っ手と本体で向きが直交するため) |
| `#viewer` に `position: relative` が無い | `.page` の `offsetParent` が body になり、`offsetTop` がスクロール量と別の座標系になる (ページ送りがヘッダの高さぶんずれる)。`.ans-list` も同じ |
| 1 ページ 4800 本の上限で**黙って捨てていた** | 生徒は書けたつもりでいる。`onLimit` で赤帯を出す |
| 起動直後に答案ペインが勝手にスクロールする | `IntersectionObserver` が読み込み時に 1 回発火し、そこで追従すると **「ページ指定なし」の設問が最初から画面の外**に流れる (縦画面のボトムシートだと特に気づけない)。冊子を一度も動かすまで追従しない |

### 15.4 まだ確かめていないこと (★ 実機が要る)

§13-8 の項目は 1 つも実機で見ていない。Chromium のマウスイベントで代用しているだけなので、
**次に iPad が手元にあるとき**に必ず通すこと:
手のひら先着 / 電話着信 (`pointercancel`) / アプリ切替 → 復帰 / 回転 / Split View /
2 端末同時 / 別端末から提出 / 時間切れ自動提出 / 機内モードのまま提出。

### 15.5 動かす前に必要なこと (運用者の作業)

1. Supabase プロジェクトを作り、`supabase/bundle.sql` を SQL Editor に貼って流す。
2. **サインアップを招待制 / メール確認 ON / ドメイン制限のいずれかにする** (§14 末尾。開いたままだと教材が流出する)。
3. `exam-book-config.mjs` の `url` と `anonKey` に **anon (publishable)** を貼る。
   `assertAnonKey()` が secret / role≠anon を形で弾く。
4. `books` に 1 行入れ、PDF を `book-pdfs` バケットへ上げて `pdf_path` を合わせ、`is_published = true`。
5. `questions` を入れる (`correct_answer` は選択式なら **1 起算の数字文字列**)。
