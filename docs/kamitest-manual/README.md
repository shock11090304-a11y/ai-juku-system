<!-- 神テスト (exam-app) に載せる問題の作り方 — 全教科共通の契約。
     ここに書いた「コードの事実」は scripts/book_exam/check_kamitest_manual.py が
     実物と突き合わせる。数字や名前を直したらゲートも一緒に緑にすること。 -->

# 神テスト 問題作成マニュアル — 共通編

神テスト (`exam-app/` → https://…/exam-book.html) に載せる**冊子**を作る人向け。
教科ごとの作法は下のリンク先。**共通編を読まずに教科別だけ読まない**こと。ここに
「全員 0 点の冊子」を作らないための契約が入っている。

| 教科 | マニュアル | `books.subject` |
|---|---|---|
| 英語 (文法・読解・英検・模試) | [eigo.md](eigo.md) | `grammar` / `reading` / `eiken` / `mock` |
| 数学 | [sugaku.md](sugaku.md) | `math` |
| 国語 (現代文・古文・漢文) | [kokugo.md](kokugo.md) | `japanese` |
| 理科 (物理・化学・生物) | [rika.md](rika.md) | `science` |
| 社会 (地理・歴史・公民) | [shakai.md](shakai.md) | `social` |

正典コード (迷ったら**マニュアルではなくこちらを読む**):

- `exam-app/exam-book-admin-model.mjs` — 入力の検証。ここを通らないものは登録できない
- `scripts/book_exam/import_books.py` — 取り込み。`validate_questions_py` が上の写し
- `supabase/migrations/20260813010000_english_learning_core.sql` — questions の CHECK
- `scripts/book_exam/materials/_book_build.py` — **全教科共通の冊子ビルダー**。
  検証・取り込み JSON・問題 PDF (KaTeX 込み)・刷り上がり PDF の読み返しを引き受ける
- `scripts/book_exam/materials/_grammar_build.py` — 英文法 15 冊が使っている旧ビルダー。
  英文法専用 (subject 固定・空所必須・4 択固定)。**新しい冊子はこちらを使わない**
- `docs/book-exam.md` — 受験画面そのものの設計

---

## 0. 30 秒で分かる「神テストの冊子」の正体

**1 冊 = ① 問題 PDF 1 本 + ② 取り込み JSON 1 本。**

★ **設問文も選択肢の文言も本文も図表も、DB には 1 文字も入らない。**
`questions` テーブルが持つのは 番号 / ページ / 解答形式 / 選択肢の数 / 正解 / 別解 /
配点 / 単元タグ / 解説 だけ。生徒の画面 (答案ペイン) に出るのは

    第3問  [1][2][3][4]        ← 選択式は 1〜N の数字ボタンだけ
    第7問  [            ]      ← 記述は 1 行の入力欄だけ

これしかない。**生徒が読む問題文は PDF の中にしか無い。**

→ 「問題を作る」とは「**PDF を組む**」+「**答えと解説の表を作る**」の 2 つ。
→ この 2 つが**同じ 1 つの正典から同時に生成**されていないと必ずずれる。
  「画面の第3問」と「冊子の第3問」が違う事故は、生徒には**採点結果がおかしい**
  としか見えない。だから正典は 1 つ、出力は 2 つ、という形を崩さない。

---

## 1. 作る手順 (この順を守る)

```
① scripts/book_exam/materials/〈冊子名〉/build_〈冊子名〉.py を書く
     └ META と QUESTIONS が唯一の正典。ここにだけ設問文・選択肢・正解・解説を書く
     └ 組み立ては _book_build.run() を呼ぶだけ (実物の型は sugaku_nijikansu1/)
② python3 scripts/book_exam/materials/〈冊子名〉/build_〈冊子名〉.py
     └ verify() が通ったら 〈STEM〉.json と 〈STEM〉_問題.pdf を同時に書き出し、
       刷り上がり PDF を読み返して正典と逆照合する (①層が build に入っている)
③ python3 scripts/run_all_gates.py book_exam       # 機械ゲート
④ 刷り上がり PDF を自分の目で読む + 全問を敵対的に読み直す (§7 の③層)
⑤ git add → commit → push        # JSON も PDF もコミットする
⑥ python3 scripts/book_exam/import_books.py 〈冊子ディレクトリ〉 \
       --pdf-dir 〈冊子ディレクトリ〉 --dry-run      # ★ まず予行
⑦ 同じコマンドから --dry-run を外す                  # 非公開で入る + 読み返し検証
⑧ 生徒に配ってよいと確認できたら --publish
```

★ **⑥⑦は必ず `--dry-run` を先に回す**。取り込みは冪等 (同じ冊子を二重に作らない)
が、間違った PDF が付いた冊子は「画面は壊れていないのに全部が狂う」形で残る。

★ 取り込みは `service_role` を使わない。講師のメール + パスワードでログインし、
登録画面と同じ RLS の中で動く。パスワードをコマンド列やファイルに書かない
(`EXAM_TEACHER_EMAIL` / `EXAM_TEACHER_PASSWORD`、無ければその場で聞かれる)。

---

## 2. 取り込み JSON (bundle) の形

`build_*.py` が書き出す 1 冊 1 ファイル。`import_books.py` が読む唯一の形。

```json
{
  "source": "英文法_名詞冠詞_第1集.yaml",
  "subject_name": "英語",
  "book": {
    "title": "英文法 名詞・冠詞 演習 第1集",
    "subject": "grammar",
    "level": "標準",
    "time_limit_min": 20
  },
  "questions": [ { …§3… }, … ]
}
```

| キー | 意味 / 落とし穴 |
|---|---|
| `source` | 元データのファイル名。**PDF 探しの一番堅い手がかり**で、`〈source の stem〉_問題.pdf` が完全一致で選ばれる。ビルダーが JSON と PDF を同名で書き出すのはこのため |
| `subject_name` | 人が読む科目名。`source` で PDF が絞れなかったときの二番手の手がかり + `time_limit_min` が `null` のときの既定時間。<!-- canon:time-limits -->英語R 80 / 国語 90 / 数学IA 70 / 数学IIB 60 / 物理 60 / 化学 60 / 生物 60 / 世界史 60 / 日本史 60<!-- /canon:time-limits --> (分) |
| `book.title` | 冊子名。**同名の冊子があると取り込みは触らない** (設問 0 の同名冊子だけ入れ直す)。改訂版は題名を変える |
| `book.subject` | ★ **閉じた集合**。下の表以外を入れると保存時に 23514 で落ちる |
| `book.level` | 自由記述 (「基礎」「標準」「難関」など) |
| `book.time_limit_min` | 分。`null` なら無制限扱い。DB には秒で入る |

### 字体 (本番の冊子に寄せる)

| 用途 | 書体 | CSS の並び |
|---|---|---|
| 本文・設問文・選択肢・解説 | **明朝** | ヒラギノ明朝 → 游明朝 → IPAex明朝 → IPA明朝 |
| 冊子名・第N問・配点・解答欄・表の見出し | **ゴシック** | ヒラギノ角ゴ → 游ゴシック → IPAexゴシック → IPAゴシック |
| 数式 | KaTeX の既定 | `vendor/katex` |

★ **日本語フォントが 1 つも入っていない環境で刷ると、Chrome は中国語フォント
(WenQuanYi) に落ちる。** PDF は正常に生成され、テキスト抽出も通るので、
**紙を見るまで気づけない** (2026-08-21 に committed 19 冊すべてがこの状態だった)。
build は刷ったあとに**埋め込みフォントを読み返して**落とす。
Linux / CI で刷るなら先に入れること:

```bash
sudo apt-get install -y fonts-ipafont-mincho fonts-ipafont-gothic fonts-ipaexfont
```

Mac はヒラギノが既定で在るので何もしなくてよい (埋め込み名が変わるだけ)。

★ 問題 PDF は 1 本 **50MB** まで (Storage の bucket 上限)。超えると取り込みが落ちる。図を多く積む冊子は画像の解像度を落として収める。

### 取り込みが PDF について確かめること (すべて**上げる前**か、上げた直後)

| いつ | 何を | 落ちたときの意味 |
|---|---|---|
| 上げる前 | 0 バイトでないか | 刷り忘れ・コピー失敗 |
| 上げる前 | 先頭が `%PDF-` か | 拡張子だけ `.pdf`。bucket は `application/pdf` と名乗れば**受け取ってしまう**ので、受験画面で開けずに初めて分かる |
| 上げる前 | 50MB 以下か | bucket の `file_size_limit` |
| 上げる前 | ページ数が読めるか | `_metadata.json` → pypdf → pymupdf の順。読めない = 壊れた PDF |
| 上げる前 | **全設問の `page` が PDF のページ数以内か** | 登録画面と同じ規則。超えると設問タップで冊子が飛べない |
| 上げた直後 | **署名 URL を取れるか** | 受験画面と同じ経路。取れなければ実体が置けていない → その冊子は公開しない |

★ 順序は **上げる → `pdf_path` を書く → 署名を取る**。Storage の読み取りポリシーが
`books.pdf_path = オブジェクト名` を条件にしているので、`pdf_path` を書く前は
**講師でも署名を取れない**。入れ替えると必ず失敗する。

★ 登録画面 (`exam-book-admin`) から上げるときは、選んだ時点で **pdf.js が実際に開いて**
ページ数を数える。パスワード付き・壊れた PDF はそこで止まる。

<!-- canon:subjects -->
| `books.subject` | 画面の表示名 |
|---|---|
| `grammar` | 英文法 |
| `reading` | 長文読解 |
| `eiken` | 英検 |
| `mock` | 模試 |
| `math` | 数学 |
| `japanese` | 国語 (現代文・古文・漢文) |
| `science` | 理科 |
| `social` | 社会 |
| `other` | その他 |
<!-- /canon:subjects -->

★ この集合を増やすときは **DB の CHECK (`…_books_subject_widen.sql`) と
`exam-book-admin-model.mjs` の `SUBJECTS` の両方**に足す。片方だけだと
「画面では選べるのに保存で落ちる」になる。

---

## 3. 設問 1 件の形

<!-- canon:question-keys -->
```json
{
  "number": 1,
  "page": 1,
  "answer_type": "choice",
  "choice_count": 4,
  "correct_answer": "3",
  "accepted_answers": null,
  "points": 2,
  "unit_tag": "MEISHI-FUKASAN",
  "explanation": "## 🎯 コアイメージ\n…"
}
```
<!-- /canon:question-keys -->

| キー | 規則 (これを外すと取り込みが落ちる) |
|---|---|
| `number` | 1 以上の整数。**冊子の中で重複禁止**。PDF の「第N問」と必ず一致させる |
| `page` | 1 以上の整数か `null`。**PDF の実ページ数を超えられない**。設問タップで冊子がその頁へ飛ぶ動線に使う。`null` だと飛べないだけで受験はできる |
| `answer_type` | `choice` か `short` のどちらか。他の値は不可 |
| `choice_count` | `choice` のとき **2〜10**。`short` のときは `null` (値を入れると落ちる) |
| `correct_answer` | `choice` → **`"1"`〜`"choice_count"` の数字文字列 (1 起算)**。`"0"`・`"A"`・`"①"` は不可。`short` → 正解の文字列。**数字だけの文字列は弾かれる** (選択式の取りこぼしを捕まえる砦) |
| `accepted_answers` | `short` の別解の配列。`choice` では使えない。空要素を混ぜない |
| `points` | 1 以上の整数 |
| `unit_tag` | 単元 ID。DB は自由テキストだが、ビルダーの `verify()` は `英大文字/数字-英大文字/数字` (例 `MEISHI-FUKASAN`) を要求する。教科別マニュアルの接頭辞に従う |
| `explanation` | 解説。**Markdown ではなく素のテキストとして出る** (§5)。見出しは教科別マニュアルの型に従う。★ **記述 (`short`) の設問では「誤答を潰す節」(英語 `## ❌ 誤答 NG 理由` / 他教科【誤答の切り方】) は書かなくてよい** — 選択肢が無いので誤答も無い。書いてもよい |

★ **`correct_answer` の 1 起算は「全員 0 点」を止める最後の砦**。0 起算で書くと
DB の CHECK も採点 RPC も何も言わずに通り、**その冊子を解いた生徒が全員間違いになる**。
`seed-data` 側の 4 択 (`"ans": 0` 起算) からコピーしてくるときが一番危ない。

### 本文・資料・図 (正典にだけ在り、DB には入らない)

| 置き場所 | 形 | 規則 |
|---|---|---|
| `META["passages"]` | `{page, title, html, source}` の並び | 本文・資料・年表・統計表。`page` は必須。`source` に出典 (社会は年次も)。`<script>` / `on*` / `<foreignObject>` は使えない |
| 設問の `figure` | SVG の文字列 | `<svg` から始めること。線と文字は `currentColor`、塗りは中間色。`<script>` / `on*` は使えない |
| 設問の `figure_ticks` | 数の並び | ★ **図に設問文・本文に無い数値を出さない** (出すと設問の根拠が図の外に出る)。軸の目盛りのように読み取らせる数だけ、ここに宣言して除く |

★ 図の中の文字も**解答漏洩の走査対象**。図に答えを書かない。
★ 図の文字と本文は、刷り上がり PDF から読み返して照合する。

★ **前書きや資料に「第1問」と書いてよい** (「第1問〜第3問は資料を見て答えよ」)。
逆照合は `第N問（N点）` という見出しの形で設問を切り分けるので、混同しない。

---

## 4. 採点のされ方 (`submit_attempt`)

- `choice` — 生徒が押したボタンの値 (`"1"`〜) と `correct_answer` の**完全一致**
- `short` — **前後の空白を落として小文字化**した完全一致。`correct_answer` と
  `accepted_answers` の**和集合**で照合
- **部分一致も正規表現も無い。** 「〜から。」「〜ため。」の揺れは全部 `accepted_answers`
  に書き出すしかない
- 得点 = 正解した設問の `points` の合計。`answers` 行が無い設問は採点対象外

★ だから **記述 (`short`) は「表記が 1 通りに決まる語」だけに使う**。
文で答えさせる設問を `short` にすると、正しく書けた生徒が不正解になる。
文で答えさせたいなら **PDF に手書きの解答欄を刷る**か、選択式に組み替える。
★ 手書きは `annotations` に残り、RLS 上は講師が読める。ただし
**講師用の閲覧画面はまだ無い** (`exam-book-admin` は冊子と設問の登録だけ)。
画面ができるまで、手書きの答案は**その場で紙として見る**前提で設計する。

---

## 5. 解説の出方 ★ ここを勘違いすると解説が読めない形で出る

```js
// exam-app/exam-book-answers.mjs
ex.textContent = r.explanation;      // ★ Markdown は解釈しない (HTML 注入を作らない)
```
```css
/* exam-app/exam-book.css */
.res-exp { margin-top: 6px; white-space: pre-wrap; }
```

つまり:

- **改行はそのまま残る** (`pre-wrap`)。段落は `\n\n` で作れる
- **`## 見出し` は「## 見出し」と記号ごと表示される。`**太字**` は星ごと出る**
- だから見出しは**それ自体が見出しに見える形**にする。英文法 15 冊が
  `## 🎯 コアイメージ` のように絵文字を使っているのはこの理由 (装飾ではなく目印)
- HTML タグを書いても効かない (そのまま文字として出る)。書かない
- **LaTeX を書かない**。`\(AB=6\)` はそのまま `\(AB=6\)` と出る (→ [sugaku.md](sugaku.md))

**解説が生徒に見える条件** (`student_questions` view):

1. ブックが公開済み (`is_published`)、かつ
2. その設問に**提出済みの答案の解答行がある**、かつ
3. **同じブックに未提出の答案が 1 つも無い** (解き直している最中は伏せる)

→ 受験中に解説は絶対に出ない。「解説が出ない」と言われたら、まず
**解きかけの答案が残っていないか**を見る。

---

## 6. 機械ゲート (書いたら必ず回す・必ずコミットする)

```bash
python3 scripts/run_all_gates.py book_exam     # 冊子まわりだけ
python3 scripts/run_all_gates.py               # 全教材 (CI と同じ)
```

冊子に効くゲート:

| ゲート | 何を見るか |
|---|---|
| `_book_build.py::verify()` | build 時。正典 (`QUESTIONS`) を直接見る唯一の層。番号の連番・ページの逆行・選択肢の重複・正解番号・配点・単元タグの形・**教科ごとの解説見出し**・**誤答の節の番号と選択肢の一致**・**解説の生 LaTeX**・**記述の答えの漏洩**・正解位置の配り |
| `_book_build.py::verify_pdf()` | build 時。**刷り上がり PDF を読み返して**全問・全選択肢が正典どおりのページに在るか + **生の LaTeX が残っていないか** (= KaTeX が全部描けたか) |
| `scripts/book_exam/check_book_build.py` | **ビルダー自身の自己検査**。記述 (`short`) を混ぜた冊子で誤検出しないこと・それでも本当の違反は捕まえること (シナリオ 26 件)。Chrome も PDF ライブラリも要らないので CI でも同じものが走る |
| `scripts/book_exam/materials/check_grammar_books.py` | コミット済み JSON 全数 (**全教科**)。取り込みと同じ検証 + 隣に `_問題.pdf` が在るか + 教科ごとの解説の形 + 正解位置 |
| `scripts/book_exam/materials/check_pdf_canon_match.py` | 英文法 15 冊 (`_grammar_build` 系) の PDF 逆照合 |
| `scripts/book_exam/check_import_books.py` | 取り込みスクリプトと `exam-book-admin-model.mjs` のずれ |
| `scripts/book_exam/check_kamitest_manual.py` | **このマニュアルとコードのずれ** |
| `scripts/check_no_pii.py` | 生徒の氏名・連絡先 (§8) |

★ ランナーは「違反検出」だけでなく **ゲート自体の故障 (CRASH)・誰も呼んでいない検査
(DEAD)・exit 0 なのに違反を印字している (INCONSISTENT)** も落とす。
どれも「通った」ではなく「**検査していない**」。

★ PDF を読む検査は CI では回せない (PDF は生成物)。**手元で build のあとに
`--no-pdf` を付けずに回す**こと。

### 検査が「見送る」条件 (黙って減らさないための覚え書き)

| 検査 | 見送る条件 | build がその場で印字する |
|---|---|---|
| 正解位置の偏り | 選択式が**選択肢の数の 2 倍未満** (4 択なら 8 問未満) / 選択肢の数がそろっていない / 選択式が無い | `! 正解位置の偏り: 選択式 3 問 / 4 択では見ていない` |
| PDF の選択肢の字面 | 選択肢が `\frac` などコマンド入りの数式で、KaTeX の描いた字形が予測できない | `! PDF 逆照合: 選択肢 40 個のうち 2 個は…` |

★ **正解位置の 3 連続は「設問番号が連続している選択式」だけを見る。**
  記述を挟んだ第1・3・5問は 3 連続ではない。

---

## 7. 納品前の相互チェック 3 層 (CLAUDE.md 2026-08-16)

単一経路の生成物を信じない。**独立した経路どうしを突き合わせて初めて「できた」と言う。**

1. **出力物どうしの照合** — 同じ正典から JSON と PDF を生成し、**刷り上がり PDF から
   抽出して**全問・全選択肢を逆照合 (`check_pdf_canon_match.py`)
2. **機械検査** — build 時 `verify()` + コミット済みゲート + **取り込み後の DB 読み返し**
   (`import_books.py` が問数と第1問の正解を突き合わせる)
3. **人手の再点検** — ★ **正解の一意性**。誤答が別解釈で正解にならないか、正解が 2 つ
   ないか。**機械には見えない**ので全問を敵対的に読み直す。用法が割れる題材
   (例: 冠詞の任意脱落) は**出題しない**で逃げるのが正しい

---

## 8. ★ このリポジトリは PUBLIC — 生徒の氏名を書かない

- `github.com/shock11090304-a11y/ai-juku-system` は公開。氏名を 1 行書いて
  コミットすると即公開され、**履歴に永久に残る**
- 宛名は `os.environ.get("STUDENT_NAME", "")` で渡す。コードに書かない
- **ファイル名も見る**。氏名入りのファイル名を作らない
- `python3 scripts/check_no_pii.py` で止める。**生徒の氏名を baseline に足して
  黙らせない**

---

## 9. 今ある冊子 (これを写して次を作る)

| 教科 | 冊子 | 正典 | 使っている仕掛け |
|---|---|---|---|
| 英語 (`grammar`) | 英文法 演習 第1集 × 15 | `scripts/book_exam/materials/meishi1/build_meishi1.py` ほか | 旧ビルダー `_grammar_build.py`。4 択 10 問 |
| 数学 (`math`) | 数学I 二次関数 演習 第1集 | `scripts/book_exam/materials/sugaku_nijikansu1/build_sugaku_nijikansu1.py` | KaTeX の数式 / sympy による正解の再計算 |
| 数学 (`math`) | 数学I 二次関数 **共通テスト型** 第1集 | `scripts/book_exam/materials/sugaku_kyotsu1/build_sugaku_kyotsu1.py` | 会話文の場面設定 (`passages`) / 8 問の誘導連鎖 |
| 理科 (`science`) | 物理基礎 電気回路 演習 第1集 | `scripts/book_exam/materials/rika_denki1/build_rika_denki1.py` | 図 (SVG) / 記述 (`short`) と別解 |
| 社会 (`social`) | 公民 日本の政治のしくみ 演習 第1集 | `scripts/book_exam/materials/shakai_seiji1/build_shakai_seiji1.py` | 資料の表 (`passages`) / 空欄の資料読み取り |
| 国語 (`japanese`) | 古文 徒然草を読む 演習 第1集 | `scripts/book_exam/materials/kokugo_kobun1/build_kokugo_kobun1.py` | 本文 (`passages`) + 注 + 出典 / 記述 |

★ `reading` / `eiken` / `mock` (英語の長文・英検・模試) の 1 冊目はまだ無い。
作るときは [eigo.md](eigo.md) §6〜§8 と、本文・図の載せ方 (§3) を見ること。

---

## 10. よくある落とし穴 (全教科共通)

| 症状 | 原因 |
|---|---|
| その冊子を解いた生徒が**全員 0 点** | `correct_answer` を 0 起算で書いた / 選択肢の並べ替えを PDF 側だけに入れた |
| 生徒が「設問と違う冊子が開く」 | `find_pdf` が別の PDF を掴んだ。`source` の stem と PDF 名を一致させる |
| 解説が `## 🎯 …` と記号ごと出て読みにくい | 仕様どおり (§5)。Markdown は解釈されない |
| 解説が出ない | 未提出の答案が残っている / ブックが未公開 (§5) |
| 記述で正しい答えが不正解になる | `short` の完全一致採点。別解を `accepted_answers` に全部書く (§4) |
| 設問タップで冊子が飛ばない | `page` が `null` |
| 取り込みが「検証を通らない」で止まる | §3 の表のどれか。**ネットワークに出る前に落ちる**ので DB は汚れていない |
| 取り込みが「PDF ではありません」で止まる | 拡張子だけ `.pdf` のファイル。刷り直す |
| 取り込みが「この冊子は N ページまでです」で止まる | 設問の `page` が PDF のページ数を超えている |
| 取り込みが「署名 URL を取れない」で止まる | 上げたのに実体が無い。**その冊子は公開しない**で、回し直す |
| 取り込みが「ページ数が分かりません」で止まる | `python3 -m pip install pypdf` (pymupdf でも可) |
| 「PDF なし」の冊子が一覧に残った | 上げる途中で落ちた。同じコマンドを回し直せば続きから入る (二重には入らない) |
| 図が画面に出ない | 仕様。**図は PDF にしか置けない** (§0) |
