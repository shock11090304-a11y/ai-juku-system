# Instagram カルーセル画像ジェネレータ

**作業前にここを読むこと。** 同じ穴を掘り直さないために、踏んだ罠を全部書いてある。

HTML/CSS で 1 枚を組み、headless Chrome で PNG に焼く。Pillow で直接描く方式
(`marketing-assets/generate_ig_*.py`) より、丸囲み・破線・下線・グラデが桁違いに書きやすい。

## 2 つのシリーズ (混ぜないこと)

| | 版面 | 入口 | 出力 | 宛先 |
|---|---|---|---|---|
| **1:1 カルーセル A/B** | 1080×1080 | `build.py` | `out/` | `@trillion_eng` (オンライン英語塾) |
| **4:5 vol シリーズ** | 1080×1350 | `build_vol.py` | `out_vol/<key>/` | `@trillion_ai` (AIコーチング) |

Instagram のフィードは 4:5 が縦にいちばん大きく取れる。**読ませる投稿は 4:5**。

```bash
python3 scripts/instagram_carousel/build_vol.py             # 全 vol を刷る
python3 scripts/instagram_carousel/build_vol.py vol01       # 1 つだけ
python3 scripts/instagram_carousel/build_vol.py --html-only # Chrome 無しで HTML だけ
python3 scripts/instagram_carousel/fonts.py --fetch         # 和文フォントを取り直す
cd scripts/instagram_carousel && python3 check_instagram_carousel.py   # 検査
```

## ファイルの役割

| ファイル | 役割 |
|---|---|
| `chrome.py` | **撮り方の正典**。Chrome の探索と HTML→PNG。両シリーズが共有する |
| `fonts.py` | 和文フォントの調達 (Google Fonts → `~/.cache/trillion-ig-fonts`) |
| `theme_vol.py` | **4:5 の意匠の正典**。色・寸法・CSS・インライン記法 |
| `build_vol.py` | 部品の組み立てと `verify()` (刷る前の検査)、はみ出しの実測 |
| `vols/vol01.py` | vol.01 の**文言と図版だけ**。意匠は書かない |
| `check_instagram_carousel.py` | ゲート。`run_all_gates.py` が拾う |
| `check_carousel_guards.py` | 上のゲートの**変異試験**。18 種の壊し方を仕込んで全部捕まるか見る |

## vol.02 を足す手順

1. `vols/vol02.py` を作り、`VOL = dict(key="vol02", ...)` を書く。**`build_vol.py` は触らない。**
2. `passage` に正典の英文を 1 本入れる。スライドに出す英文はここに実在しないと `verify` が落とす。
3. 説明用の例文 (本文の引用ではないもの) は `en_examples` に宣言する。
4. 裏を取っていない主張 (出典表記など) は `unverified` に宣言する。宣言漏れも消し忘れも落ちる。
5. `python3 build_vol.py vol02` → `cd . && python3 check_instagram_carousel.py`。

### インライン記法
`[a]琥珀[/a] [p]ピンク[/p] [w]白太[/w] [u]琥珀下線[/u] [m]薄灰[/m] [s]セリフ[/s] [o]丸囲み[/o]`
/ `\n` は改行。閉じ忘れと未知タグはビルド時に落ちる。

### 部品
`badge chip quote dashbox_en dashbox bigq h lead gloss trans eyebrow opts pill_pink
hint answer goodbox badbox rulebox notebar dashnote fig source cta gap push`

---

## ★踏んだ罠 (2026-08-31)

### 1. Chrome の `--window-size` はブラウザUI分を含む
Linux の headless Chromium 141 では、指定した高さより **87 CSS px 少なく描画**され、
足りない分は地の色で埋まる = **版面の下端が丸ごと出ない**。macOS の Chrome では 0 だった。
定数で持つと環境が変わった瞬間に壊れるので、`chrome.py` が起動時に**実測して吸収**する
(`_measure_ui_offset`)。ここを消すと下 87px が消える。

### 2. 版面を `position:absolute; inset:0` で作らない
上の理由でビューポート高が指定と一致しないため、絶対配置だと版面がビューポートに
縮む。`.stage` を `width/height` 固定の**通常フローの箱**にして、背景もそこに持たせる。

### 3. はみ出しは「版面の外」ではなく「フッターへの重なり」で起きる
`.mid` が `flex:1; min-height:0` なので、本文が多いと**縮んでフッターに重なる**。
画面の外には出ないので、版面の下を覗く検査は**常に緑になる**(実際に空振りした)。
`overflow_px()` は `.stage{height:auto}` `.mid{flex:0 0 auto}` にして
「本文が必要とする高さ」を測り、1350 との差を返す。ビルドが刷る前に必ず回す。

### 4. 修飾子にレイアウト用のクラス名を使わない
`<div class="dashnote mid">` がレイアウト用の `.mid` (flex 縦積み) を拾い、
中の `<span>` が**全部改行された**。修飾子は `.ctr` のように専用名にする。
ゲートが「レイアウト用クラスに許していない修飾子が同居していないか」で見張る。

### 5. Linux の和文フォントは中国語字形に落ちる (豆腐にならないので気づけない)
`fc-list :lang=ja` に IPAGothic / WenQuanYi / Unifont しか無く、
`font-family:"Hiragino Sans",sans-serif` は **WenQuanYi Zen Hei (中国語)** に解決される。
直・令・漢・今・戸・画 などの字形が日本語と 19〜36% 違う。和文明朝は無く、太字も合成
(weight 700 と 900 が同一ビットマップ)。
→ `fonts.py` が Noto Sans JP / Noto Serif JP を取ってきて `@font-face` で埋める。
**スタックの先頭を Noto にする**のは、Mac と CI で字幅を揃えるためでもある
(英文を `white-space:nowrap` で組むので、字幅が変わると片方だけはみ出す)。

- Google Fonts は **UA で返る形式が変わる**。`MSIE 6` を名乗ると **EOT** が返り、
  Chrome では使えない (大きさは正しいので大きさだけ見ていると気づけない)。
  素の `Mozilla/5.0` が 1 ウェイト 1 個の TTF を返す。
- 取得は**ビルド時だけ**。描画時に Chrome を外に出さない (ネットの無い環境でも刷れるように)。
- キャッシュはリポジトリの外に置く。`scripts/` の中だと `run_all_gates.py` の
  「検査を回したらファイルが変わった」検出に引っかかる。

### 6. 刷った PNG / HTML はリポジトリに残らない
`.gitignore` の `scripts/**/*.png` `scripts/**/*.html` で弾かれる。
`out/` の 1:1 PNG が入っているのは最初の取り込みコミットの名残 (追跡済みには効かないため)。
**新しく刷ったものは `git status` に出ないまま消える。**
→ 現物の代わりに、全スライドを並べた `out_vol/<key>/<key>_sheet.jpg` だけをコミットする
(拡張子が違うので追跡できる)。次のセッションはこれで「正しい見た目」を確かめられる。
→ ★`out/` の 1:1 PNG は Mac のヒラギノで刷ったもの。別環境で刷り直すと字形が変わって
  30MB の差分になる。刷り直すときは `build.OUT` を別の場所へ向けること。

---

## 検査 (CLAUDE.md の相互チェック 3 層)

| 層 | 何をするか | どこ |
|---|---|---|
| ① 出力物どうしの照合 | 組んだ HTML からページ番号・ドット・ブランド行を読み戻してデータと突き合わせる。引用した英文が正典 `passage` に実在するか全数照合 | `check_instagram_carousel.py` |
| ② 機械検査 | 刷る前の `verify()` (記法・番号・図版の禁則・未検証の主張の宣言) + はみ出しの実測 + ゲート + **ゲート自体の変異試験 18 種** | `build_vol.py` / `check_*.py` |
| ③ 人手の再点検 | 訳の一意性・日本語の自然さ・図の読みやすさ。**機械では見えない**ので必ず目で見る | 人 |

`python3 scripts/run_all_gates.py instagram_carousel` で 2 本まとめて回る。

---

## vol.01 の出所と、裏を取っていないこと

- スライド 1〜5 は**塾長が既に投稿した画像を書き起こしたもの**。6 枚目は提示が無かったので
  新規に起こした (まとめ + CTA)。
- 次の 3 つは**このリポジトリでは裏を取っていない**。`vols/vol01.py` の `unverified` に
  宣言してあり、宣言を外すとゲートが落ちる:
  - 「実際の入試問題」という位置づけ
  - 「京都大学 2023年 英語 第2問」という出典表記
  - 「大手予備校の模範解答が割れた」
- 出す前に塾長が出典を確認すること。**機械では確かめられない。**

### ★著作権の扱いが、このリポジトリの他の教材と違う
`scripts/*_eigo_mirror/build.py` は 4 本とも docstring に
**「本文は著作権配慮で完全オリジナル」**と書いてある。実在の入試英文を verbatim で
持っているのは `scripts/kyotsu_eng2026_kaisetu/content.py` (2026 共通テスト) **1 箇所だけ**。
vol.01 は実在の入試英文とされるものを 1 文まるごと持っており、しかも
**このリポジトリは PUBLIC**。1 文の引用は教育目的の引用として通る可能性が高いが、
リポジトリの他の教材が取っている方針とは違う。増やす前に塾長の判断を仰ぐこと。

## vol.02 以降のネタ元 (リポジトリ内にある)

- **教え方の骨格はもう repo にある**。`scripts/eng_therules/rulehunt03/content.py` に
  識別ルール 24 本が sign / mark / slogan つきで入っている。
  vol.01 が扱った as もそこにある (`key="aid"`)。
- ★ただし**そこに書いてある as の規則の方が正しくて広い**:
  - repo: 「as は後ろ次第 —— 名詞なら**「として」**、S+V なら**様態・理由・時**を文脈で。」
  - vol.01 のスライド: 「as + 名詞 →「〜とみなす」/ as + S+V →「〜するように」(様態)」
  vol.01 は `see A as B` の文脈に絞った言い方なので**この一文には効く**が、
  規則として読むと狭い (as + S+V は理由・時のこともある)。
  vol.02 以降で as を再び扱うなら repo 側の言い方に合わせること。
- **実在の入試英文はリポジトリにほぼ無い**。大学名がついた教材 (`*_eigo_mirror`,
  `eng_kokkoritsu_nankan` 等) は**オリジナルの類題**。
  「実際の入試問題」の看板を続けるなら、毎回リポジトリの外から手で取ってくることになる。
  看板を「難関大で狙われる読み方」に緩めれば、repo のデータから量産できる。
