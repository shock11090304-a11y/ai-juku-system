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
python3 scripts/run_all_gates.py instagram_carousel         # 検査 (2 本)
```
### 刷ったものをデスクトップに置く
```bash
python3 scripts/instagram_carousel/build_vol.py vol01 --desktop
# → ~/Desktop/trillion-ig/vol01/ に PNG 6枚 + 投稿文 + 一覧が揃う
python3 scripts/instagram_carousel/build_vol.py vol01 --out ~/Downloads/ig
```
★**刷る場所そのものは `out_vol/` から動かさない**。配布先へ直接刷るようにすると、
検査 (刷り上がりと一覧 JPG の突き合わせ) が見に行く場所を見失う。
`--desktop` / `--out` は**出来上がったものを配る**だけのステップ。
`--desktop` はデスクトップのある端末 (塾長の Mac) 用で、クラウドや CI では落ちる。
1:1 の `build.py` にこの口は無い (出力がコミット済みで、刷り直す運用にしていないため)。

その他のオプション: `--no-fit` (はみ出しの実測を省く・**納品には使わない**) /
`--no-font-fetch` (フォントを取りに行かない・オフライン用)。
Pillow が要る (版面の較正と刷り上がりの検査に使う)。

## 塾長の Mac で回すとき (デスクトップに置きたい場合)

★**クラウドの Claude Code (claude.ai/code) は、どのセッションでも塾長の端末の
デスクトップには書けない**。別のマシンで動いているので届かない。
セッションを取り直しても同じ。デスクトップに置きたいときは
**塾長の Mac の Claude Code か、Mac のターミナル**で回すこと。
(`class_recordings` の `railway run` と同じ事情。CLAUDE.md にも書いてある)

★**手順に `#` のコメントを混ぜないこと**。zsh は対話モードで既定では
コメントを解釈しないので、`cd ~/repo  # 説明` が「引数が多すぎる」で失敗し、
以降のコマンドが**全部リポジトリの外で走る**。2026-08-31 に実際にこれで
「not a git repository」を 3 回出させた。貼り付ける手順は素のコマンドだけにする。

リポジトリの場所を探す (どこに置いたか分からないとき):
```
find ~ -maxdepth 5 -type d -name ai-juku-system 2>/dev/null
```

刷ってデスクトップに置く (そのまま貼れる):
```
cd ~/ai-juku-system
git fetch origin claude/instagram-image-memory-search-37kkan
git checkout claude/instagram-image-memory-search-37kkan
python3 -m pip install Pillow
python3 scripts/instagram_carousel/build_vol.py vol01 --desktop
open ~/Desktop/trillion-ig/vol01
```

要るもの: Python 3 (3.9 で動く。macOS の Command Line Tools 付属で可) /
Pillow / Google Chrome (`/Applications/` にあれば自動で見つける)。
初回だけ Noto フォント (約 30MB) を取りに行く (2 回目以降はキャッシュ)。

★Mac と Linux で**同じフォント (Noto) を使う**ので版面は一致するが、Chrome の
バージョン差でアンチエイリアスが微妙に変わり、PNG がバイト単位で一致しないことはある。
その場合 `<key>_sheet.jpg` も一緒に刷り直されるので、`git status` に出たらコミットしてよい
(「別の端末で刷り直した」という意味)。

## ファイルの役割

| ファイル | 役割 |
|---|---|
| `chrome.py` | **撮り方の正典**。Chrome の探索と HTML→PNG。両シリーズが共有する |
| `fonts.py` | 和文フォントの調達 (Google Fonts → `~/.cache/trillion-ig-fonts`) |
| `theme_vol.py` | **4:5 の意匠の正典**。色・寸法・CSS・インライン記法 |
| `build_vol.py` | 部品の組み立てと `verify()` (刷る前の検査)、はみ出しの実測 |
| `vols/vol01.py` | vol.01 (京大 as / 様態 vs みなす) の文言・図版・投稿文 |
| `vols/vol02.py` | vol.02 (It is A that / 強調構文の識別)。例文は自塾教材の原創文 |
| `check_instagram_carousel.py` | ゲート。`run_all_gates.py` が拾う |
| `check_carousel_guards.py` | 上のゲートの**変異試験**。18 種の壊し方を仕込んで全部捕まるか見る |

## vol.02 を足す手順

1. `vols/vol02.py` を作り、`VOL = dict(key="vol02", ...)` を書く。**`build_vol.py` は触らない。**
2. `passage` に正典の英文を 1 本入れる。スライドに出す英文はここに実在しないと `verify` が落とす。
3. 説明用の例文 (本文の引用ではないもの) は `en_examples` に宣言する。
4. 裏を取っていない主張 (出典表記など) は `unverified` に宣言する。宣言漏れも消し忘れも落ちる。
   ★「実在の入試問題ではありません」のような**打ち消し**は `disclaimers` に書く。
   出典らしさの判定 (`_is_claim`) は取りこぼさない側に倒してあるので打ち消し文まで拾う。
   これが無いと「正直に打ち消すほど検査に落ちる」逆の誘因になる。
   `disclaimers` は打ち消し表現 (ではありません/ではない/ではなく) を含むことが必須で、
   裏の取れない断言をここに書いて `unverified` を迂回することはできない。
5. `caption` に投稿文 (`full` / `short` / `hashtags`) を書く。
   **投稿文もスライドと同じ vol に置く。** 別ファイルに分けると、画像だけ直して
   投稿文が古いまま、という事故が起きる。上限 2,200字 / ハッシュタグ 30個 と、
   出典の断言・引用英文の実在は画像と同じ規律でゲートが見る。
6. `python3 build_vol.py vol02` → `python3 scripts/run_all_gates.py instagram_carousel`。
   投稿文は `out_vol/<key>/<key>_caption.txt` に貼り付け用として書き出される
   (正典は .py 側。テキストは `.gitignore` 済みの生成物)。

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

### 3. はみ出しは 2 通りある。片方だけ測ると「検査があるように見えて効いていない」
- **縦**: `.mid` が `flex:1; min-height:0` なので、本文が多いと**縮んでフッターに重なる**。
  画面の外には出ないので、版面の下を覗く検査は**常に緑になる**(実際に空振りした)。
  `.stage{height:auto}` `.mid{flex:0 0 auto}` にして「本文が必要とする高さ」を測る。
- **横**: 英文は `white-space:nowrap` で組むので幅が足りないと横へ溢れる。
  ★撮影窓を版面と同じ幅にすると、溢れた分は**スクリーンショットに写らない**。
  一度これで「横は必ず 0」という嘘の検査を書いた。版面の左右に観測用の余白 (300px) を
  作った窓で撮り、その余白に色が乗るかを見る。中央寄せは左右どちらにも溢れるので両側見る。
  ★観測用の余白は `body` だけに当てる。`html` にも当てると版面ごとずれて
  **全スライドが横に溢れている**と誤報する (これも一度やった)。

### 3b. 「測れなかった」を 0 と報告しない
`chrome.py` の較正 (UI オフセットの実測) が失敗したとき 0 を返すと、
**Mac の正しい 0 と区別がつかない**。0 だと版面の下端が欠けた PNG が実寸検査を
そのまま通り、フッターの無い画像が無言で納品される。測れなければ `CalibrationError`
で落とす。Pillow が無いのも「測れない」に含める。

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
| ① 出力物どうしの照合 | 投稿文もスライドと同じ検査にかける (英文の実在・出典の宣言・記法の消し忘れ・Instagram の上限)。組んだ HTML から**位置**(点灯ドットの位置・ページ番号の表示)を読み戻してデータと突き合わせる。刷り上がり PNG を**コミットしてある一覧 JPG と画素で照合**する。引用した英文が正典 `passage` に「その並びで」実在するか全数照合 | `check_instagram_carousel.py` |
| ② 機械検査 | 刷る前の `verify()` (記法・番号・図版の禁則・未検証の主張の宣言) + はみ出しの縦横実測 + ゲート + **ゲート自体の変異試験 40 件** | `build_vol.py` / `check_*.py` |
| ③ 人手の再点検 | 訳の一意性・日本語の自然さ・図の読みやすさ。**機械では見えない**。vol データの `editorial_notes` に書いておくとゲートが毎回印字する | 人 |

`python3 scripts/run_all_gates.py instagram_carousel` で 2 本まとめて回る。

### ★検査を書いたら「消したら落ちるか」を確かめる
`check_carousel_guards.py` は**鳴るべき見張りの文言まで指定**して変異を仕込む。
以前は「違反が 1 件でも出れば合格」にしていたため、18 種のうち 9 種が
**別のガードの巻き添えで**捕まっており、本命を消しても緑だった。
同じ理由で `except Exception: ok = True` も禁止 (無関係な例外を合格に数える)。
vol が複数あるときは vol ごとに AND を取る (OR だと 1 冊が免疫でも通る)。
実測: 見張り 16 個を 1 つずつ無効化して、**16/16 で変異試験が落ちる**ことを確認済み。

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
- 「大手予備校の模範解答が割れた」は、該当しそうな記事の下線部が**この一文ではない**
  可能性が高い (別問題の話の貼り替え)。出すなら割れた 2 案をスライドに載せること。

### 教え方について残っている論点 (`vols/vol01.py` の `editorial_notes`)
ゲートが毎回そのまま印字する。塾長の既発表分は勝手に書き換えていないが、黙っても通さない。
最大のものは **「as + S+V → 様態」は一般則としては狭い**こと
(as + S+V は理由・時・比例にもなる)。自塾の教材の正典は
「as は後ろ次第 —— 名詞なら「として」、S+V なら様態・理由・時を文脈で」。
6 枚目 (提示画像に無く新規に起こした側) はこの正典に合わせて直してある。

### ★著作権の扱いが、このリポジトリの他の教材と違う
`scripts/*_eigo_mirror/build.py` は 4 本とも docstring に
**「本文は著作権配慮で完全オリジナル」**と書いてある。実在の入試英文を verbatim で
持っているのは `scripts/kyotsu_eng2026_kaisetu/content.py` (2026 共通テスト) **1 箇所だけ**。
vol.01 は実在の入試英文とされるものを 1 文まるごと持っており、しかも
**このリポジトリは PUBLIC**。1 文の引用は教育目的の引用として通る可能性が高いが、
リポジトリの他の教材が取っている方針とは違う。増やす前に塾長の判断を仰ぐこと。

## vol.02 以降のネタ元 (リポジトリ内にある)

- **教え方の骨格はもう repo にある**。`scripts/eng_therules/rulehunt03/content.py` の
  `TARGETS` に識別ルール **6 本**が sign / mark / slogan つきで入っている
  (rulehunt01〜04 を合わせると 18〜24 本)。vol.01 が扱った as もそこにある (`key="aid"`)。
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
