# 英語学習アプリ — DB スキーマ (Supabase)

問題集 (PDF + 設問) を配って、生徒が解いて、手書きで書き込んで、誤答が復習キューに溜まる、
までを支える Postgres スキーマ。**Supabase 前提** (`auth.users` / `auth.uid()` /
`anon`・`authenticated` ロール / Storage を使う)。

> ★ このリポジトリの本体 API (Railway の `server/main.py`) とは**別の DB**。
>   `server/main.py` の `init_db()` が作るテーブル群とは無関係で、名前もぶつかっていない。

## ファイル

| ファイル | 中身 |
| --- | --- |
| `migrations/20260813010000_english_learning_core.sql` | テーブル 7 本・制約・インデックス・`updated_at` トリガ |
| `migrations/20260813010100_english_learning_rls.sql` | 権限・RLS ポリシー 28 本・`auth.users` 連携・生徒向け view |
| `migrations/20260813010200_english_learning_storage.sql` | 問題 PDF の bucket (`book-pdfs`) と読み書き権限 |
| `migrations/20260813010300_english_learning_grading.sql` | 採点 RPC `submit_attempt()` と、点数を直接書けなくする権限 |
| `migrations/20260813010400_english_learning_question_data.sql` | JSON 問題の設問本体 `questions.question_data` と view の更新 |
| `seed.sql` | 動作確認用の中身 (仮定法の演習 1 冊 5 問 + 未公開の模試 1 冊) |
| `demo/index.html` | 動作確認ページ (開発用。本番サイトには載せない) |
| `tests/00_local_stubs.sql` | 素の Postgres で試すための Supabase 相当スタブ (**本番に流さない**) |
| `tests/10_schema_expectations.sql` | 振る舞いテスト 74 件 |

5 本とも**何度流しても安全**（`if not exists` / `or replace` / `drop … if exists`）。

## 流し方

```bash
# Supabase CLI
supabase db push

# または SQL Editor に 010000 → 010100 → 010200 → 010300 → 010400 の順で貼る
```

★ **core だけ流して止めない**こと。RLS は 2 本目に入っているので、core だけの状態は
「ログインした全員が全生徒の答案を読める」DB になる。

3 本目 (Storage) は PDF を配らないなら省いてよい。
5 本目 (question_data) は PDF 運用しかしないなら省いてよい。
**1 本目と 2 本目と 4 本目は必須**（4 本目が無いと採点できる経路が存在しない）。

## 使ってみる

`supabase/demo/index.html` が動作確認ページ。RLS・正解の伏せ方・採点 RPC・手書き保存を
実際に触って確かめられる。**開発用**なので本番サイトには載せない (`.vercelignore` で除外済み)。

### A. 手元だけで動かす (Docker が要る・いちばん手軽)

```bash
npm install -g supabase          # 未導入なら
cd <このリポジトリ>
supabase init                    # supabase/config.toml が無ければ
supabase start                   # 初回は数分。API URL と anon key が表示される
supabase db reset                # migrations/*.sql → seed.sql を流す

python3 -m http.server 8080      # 別のターミナルで
# → http://localhost:8080/supabase/demo/ を開く
```

`supabase start` が出す **API URL** (既定 `http://127.0.0.1:54321`) と **anon key** を
デモの「1. 接続」に貼る。ローカルはメール確認が既定で無効なので、
そのまま新規登録 → ログインできる。

### B. ホストの Supabase プロジェクトで動かす

```bash
supabase link --project-ref <プロジェクトID>
supabase db push                 # migrations だけ流れる (seed は流れない)
```

シードを入れるなら SQL Editor に `supabase/seed.sql` を貼る。
デモには **Settings → API** の Project URL と **anon public** キーを貼る
(`service_role` キーは絶対に貼らない。RLS を全部素通りしてしまう)。

★ メール確認が既定で有効なので、新規登録してもすぐログインできない。
確認メールを踏むか、Authentication → Providers → Email の "Confirm email" を
一時的に切る。

### 触る順番

1. **生徒として新規登録** → `handle_new_user` が `profiles` を自動で作る (role=student)
2. **3. ブック一覧** → 「英文法 仮定法 演習5」だけ出る。未公開の模試は出ない (RLS)
3. **受験する** → 設問文と選択肢は出るが、正解は伏せられている
   (`correct_answer = null`。画面にもそう出る)
4. **手書き** で書いて保存 → `annotations.strokes` に入る。読み直すと戻る
5. **採点して提出する** → `submit_attempt()` が走り、点数と正解と解説が出る
6. **6. 復習キュー** → 間違えた設問が積まれている。もう一度受験して同じ問題を落とすと
   `wrong_count` が 2 になる
7. **7. 守られているかを試す** → 6 つの攻撃が全部弾かれることを確認する

### 講師として見る

講師への昇格は SQL でしかできない (生徒が自分で上げられないようにしてあるため)。
SQL Editor か `supabase db reset` 後のローカル Studio で:

```sql
update public.profiles set role = 'teacher' where id = (
    select id from auth.users where email = 'あなたのアドレス');
```

講師でログインし直すと、未公開ブックも `questions` テーブルも直接見えるようになる。

## 検査

```bash
python3 scripts/english_schema/check_schema.py     # 単体
python3 scripts/run_all_gates.py english_schema    # リポジトリ共通の入口から
```

- **静的検査** … RLS を有効にし忘れたテーブル、ポリシーの無い操作、`search_path` を
  固定していない `security definer` 関数、`anon` 向けポリシー、冪等でない DDL などを落とす。
  DB が無くても回るので CI (`material-gates.yml`) でも走る。
- **実DB検査** … 使い捨ての Postgres に stubs → migrations を **2 周**流して
  (冪等性の確認)、`tests/10_schema_expectations.sql` の 74 件を回す。
  Postgres が見つからないときは実行しないが、**飛ばしたことを必ず印字する**。
  手元で明示的に指定するなら:

  ```bash
  ENGLISH_SCHEMA_TEST_DSN=postgresql://localhost/postgres \
    python3 scripts/english_schema/check_schema.py
  ```

  DSN が Railway / Supabase / RDS 等の本番らしいホストを指していたら実行を拒否する
  (使い捨て DB を `create` / `drop` するため)。

検査の内訳: 制約 14 / トリガ 3 / 生徒の RLS 20 / 講師の RLS 9 / 未ログイン 4 /
Storage 3 / 参照整合性 5 / 採点 6 / JSON問題と受験フロー 10。

---

## ★ 生徒に設問を返すときは `student_questions` を使う

`questions` テーブルには `correct_answer` と `explanation` が同じ行に入っている。
生徒に `select * from questions` を許すと**受験前に正解が全部読める**ので、
生徒向けの RLS は **`questions` を 1 行も返さない**ようにしてある。

代わりに view `public.student_questions` を使う:

```js
// ❌ 生徒のクライアントからは 0 行しか返らない
const { data } = await supabase.from('questions').select('*').eq('book_id', id)

// ✅ こちら
const { data } = await supabase.from('student_questions').select('*').eq('book_id', id)
```

この view が返すもの:

- 公開済み (`is_published = true`) のブックの設問だけ
- `question_data`（設問文・選択肢）は常に返る。無いと解けないため
- `correct_answer` / `accepted_answers` / `explanation` は、次の**両方**を満たすときだけ返る。
  それ以外は `NULL`。判定結果は `revealed` 列にも出るので UI の出し分けに使える
  1. その生徒が提出済みの答案でその設問に解答している
  2. そのブックを**いま受験中でない**（未提出の答案が 1 つも無い）

  条件 2 が無いと、一度提出した本をもう一度受験するときに正解が出たままになる
  (期待値テストの I8 がこの穴を捕まえた)。

講師 (`profiles.role = 'teacher'`) は `questions` テーブルを直接読める。

> Supabase のセキュリティリンタは `student_questions` を
> 「security definer view」として警告する。正解列を隠すのが目的なので意図的。

## 誰が何を触れるか (RLS)

| テーブル | 生徒 | 講師 |
| --- | --- | --- |
| `profiles` | 自分の行を読む・表示名を変える (`role` は変えられない) | 全員を読む・`role` を変えられる |
| `books` | 公開済みだけ読む | 全部読む・作る・直す・消す |
| `questions` | **直接は読めない** (`student_questions` 経由) | 全部読む・作る・直す・消す |
| `attempts` | 開始 (insert) だけ。**直接の UPDATE 権限は無く**、提出は `submit_attempt()` 経由 | 全員の分を読む |
| `answers` | 自分の未提出 attempt にだけ書ける。書けるのは `user_answer` と `time_spent_sec` の 2 列だけ | 全員の分を読む |
| `annotations` | 同上 (手書き) | 全員の分を読む |
| `review_items` | 自分の分だけ読み書き | 全員の分を読む |

未ログイン (`anon`) はどのテーブルにも触れない (`grant` ごと剥がしてある)。

## 採点は `submit_attempt()` でしかできない

```js
const { data } = await supabase.rpc('submit_attempt', { p_attempt: attemptId })
// → { total_score, max_score, correct_count, answered_count, question_count }
```

この RPC が、自分の未提出の答案かを確かめたうえで

1. `answers.is_correct` を `questions.correct_answer` と突き合わせて埋め
2. `attempts` に点数・満点・所要時間・`submitted_at` を書き
3. 誤答を `review_items` に積む（同じ設問を落とすたびに `wrong_count` が増える）

を 1 トランザクションで行う。`for update` で行を掴むので、二重に押しても二重採点しない。

**クライアントは点数を書けない。** `attempts` の UPDATE 権限は誰にも配っておらず、
`answers` に書けるのは `user_answer` と `time_spent_sec` の 2 列だけ（列単位の grant）。
`total_score` と `is_correct` を書けるのはこの関数だけになっている。

そもそも生徒は提出前に `correct_answer` を読めない（view が伏せる）ので、
クライアント側に「正解と突き合わせる」瞬間が存在しない。採点をサーバに置くのは
方針というより、この設計だとそれ以外に経路が無い。

短答の照合は「前後の空白を落として小文字化」＋ `accepted_answers` の別解。
ここを緩めると採点が甘くなる。厳しくする分はアプリ側で吸収できるが、
甘くしたものは後から締められない（生徒の点数が下がるため）。

## 参照整合性の効き方 (何が消せて何が消せないか)

実測値 (`tests/10_schema_expectations.sql` の G 群が裏を取っている):

| 消すもの | 起きること |
| --- | --- |
| 一度も受験されていないブック | 設問ごと消える (cascade) |
| **受験履歴のあるブック** | **消せない** (`attempts` / `answers` が止める) |
| attempt | 解答と手書きが一緒に消える (cascade) |
| **解答された設問** | **消せない** (`answers` が止める) |
| まだ解答されていない設問 | 消える。その設問の復習キューも一緒に落ちる (cascade) |
| 履歴の無い `auth.users` | `profiles` ごと消える (cascade) |
| **受験履歴のある `auth.users`** | **消せない** (`attempts.user_id` が止める) |

配布済みのブックは削除ではなく `is_published = false` で下げる運用になる。
退会で本当に履歴ごと消すなら、消す順は
`answers` / `annotations` → `attempts` → `review_items` → `auth.users`。
(`attempts` を消せば `answers` と `annotations` は cascade で落ちるので実際は
`attempts` → `review_items` → `auth.users` の 3 手)

---

## 元の設計からの差分

もらった設計をそのまま起こしたうえで、以下だけ足している。**削ったものは無い**。

### 1. 参照とデフォルト

| 箇所 | 差分 | 理由 |
| --- | --- | --- |
| `profiles.id → auth.users` | `on delete cascade` を追加 | 付けないと退会 (auth.users の削除) が参照で失敗して退会処理が通らない |
| `books.created_by` | `on delete set null` | 講師が抜けてもブックは残す |
| `review_items.user_id` / `.question_id` | `on delete cascade` | 誤答ノートは派生データ。元が消えたら残す意味が無い |
| 全 `created_at` / `started_at` / `last_wrong_at` / `updated_at` | `not null` を追加 | `default` があっても明示 `NULL` は入れられる |
| `is_published` / `points` / `wrong_count` / `is_resolved` | `not null` を追加 | 同上。3 値論理を持ち込まない |
| 各 FK 列 (`questions.book_id`・`attempts.book_id`/`user_id`・`answers.*`・`annotations.attempt_id`・`review_items.*`) | `not null` を追加 | 親の無い子行に意味が無く、UNIQUE 制約も NULL では重複を止められない |

`attempts.book_id` / `attempts.user_id` / `answers.question_id` は**設計どおり
`on delete` を付けていない** (＝削除を止める)。上の「参照整合性の効き方」がその結果。

### 2. 追加した CHECK 制約

| 制約 | 中身 |
| --- | --- |
| `questions_answer_shape` | `choice` なら `choice_count` 2〜10 かつ `correct_answer` が 1〜`choice_count` の番号。`short` なら `choice_count` は NULL で正解は非空 |
| `questions_accepted_answers_no_null` | 別解の配列に NULL 要素を入れさせない (`= any(...)` が NULL を返して採点が静かに落ちるため) |
| `books_subject_check` | `subject` を `grammar`/`reading`/`eiken`/`mock` に限定 |
| `attempts_submitted_after_started` | `submitted_at >= started_at` |
| 各種 | `page` / `number` / `page_count` / `time_limit_sec` / `points` は正数、スコアと秒数は非負、`display_name` と `title` は空白だけ禁止 |

`subject` は元の設計ではコメントでの列挙だったが、`role` と `answer_type` が
`check` で書かれているのに合わせて閉じた集合と読んだ。増やすときは:

```sql
alter table public.books drop constraint books_subject_check;
alter table public.books add constraint books_subject_check
    check (subject in ('grammar', 'reading', 'eiken', 'mock', 'listening'));
```

`level` は「基礎 / 標準 / 難関 **など**」と書かれていたので自由記述のままにしてある。

`questions_answer_shape` の判定を plpgsql 関数
(`public.question_answer_is_valid`) に出しているのは、素の SQL の `and` は
**評価順が仕様として保証されない**ため。順序が入れ替わると
`answer_type='choice'`・`correct_answer='あ'` の行が `check_violation` ではなく
`22P02 (invalid input syntax for type integer)` で落ちるようになり、アプリ側で
「入力ミス」と「バグ」の区別が壊れる。plpgsql なら文の順序が保証される。

### 3. インデックス 9 本

Postgres は外部キーに自動でインデックスを張らない。UNIQUE 制約が先頭列をカバーしている
分 (`answers.attempt_id` / `review_items.user_id` / `questions.book_id`) は張らず、
カバーされていない参照と実際の画面のクエリだけ張ってある。
`review_items` の復習キューは `where not is_resolved` の部分インデックス
(解決済みが時間とともに大半を占めるため)、`tags` は GIN。

### 4. トリガ 3 本

| トリガ | 何をするか |
| --- | --- |
| `on_auth_user_created` (`auth.users`) | サインアップ時に `profiles` を作る。表示名は `options.data.display_name` → `name` → メールのローカル部の順で拾う。`display_name` が `not null` なので、これが無いとサインアップが失敗する |
| `profiles_guard_role` (`profiles`) | 生徒が自分の `role` を `teacher` に書き換えるのを止める。★ RLS の `with check` だけでは止まらない (「自分の行を更新してよい」ポリシーは列の値まで見ない)。JWT の無い呼び出し (`service_role` / サーバ側の管理タスク) は素通しするので、講師の任命はそこから行う |
| `annotations_touch_updated_at` | `updated_at` を DB 側で打つ (クライアントの時計を信じない) |

### 5. 採点 RPC と、点数を書けなくする権限 (`…_grading.sql`)

`submit_attempt()` を足し、同時に `attempts` の UPDATE 権限を剥がして
`answers` を列単位の grant にした。詳細は上の「採点は `submit_attempt()` でしかできない」。

**元の設計には採点の置き場が無かった**。生徒は提出前に正解を読めず、提出後は答案が
凍結されるので、クライアントが採点できる瞬間がどこにも無い。これを足さないと
「解いて提出する」までしか動かない。

### 6. `questions.question_data` (`…_question_data.sql`)

元の設計の `pdf_path text -- Supabase Storage 上のパス。NULL可（JSON問題のみの場合）`
に対して、その「JSON問題」を入れる列が無かった。PDF があるブックは本文が PDF 側にあり
`questions.page` が飛び先を持っているので足りているが、PDF が無いブックだけ
設問文と選択肢の置き場が無い。

```
question_data jsonb  -- {"stem": "設問文", "choices": ["…"], "figure_svg": "…"}
```

正解は入れない (`correct_answer` は今までどおり別列で、view が伏せる)。
名前は既存の `exam_questions.question_data` に合わせた。
選択肢の数が `choice_count` と食い違う行は CHECK で弾く
(ボタンの数と正解番号の範囲がずれるため)。

### 7. Storage

bucket `book-pdfs` (非公開・50MB・`application/pdf` のみ)。
読めるのは `books.pdf_path` が指していて、かつ**公開済み**のブックの PDF だけ
(講師は未公開も読める)。書けるのは講師だけ。

★「bucket が `book-pdfs` なら誰でも読める」にはしていない。オブジェクト名は一覧 API で
列挙できるので、それだと未公開の模試 PDF が受験前に落とせてしまう。

配信は署名付き URL で:

```js
const { data } = await supabase.storage.from('book-pdfs').createSignedUrl(book.pdf_path, 3600)
```

---

## 未確定

- **`annotations.strokes` の形は制約していない**。設計書 §5 のフォーマットが
  このリポジトリに無いため。推測で `jsonb_typeof(strokes) = 'array'` を強制すると、
  実際が `{"version":1,"strokes":[…]}` 形式だった場合に書き込みが全部落ちる。
  §5 が確定したら CHECK をここに足すこと (テストは `tests/10_schema_expectations.sql`)。
  ページ 1 枚分のストロークがそのまま 1 行に入るので、
  長時間の書き込みでサイズが膨らむ場合は間引き (点の間引き / 折れ線の簡略化) は
  クライアント側で行う前提。
- **`questions.question_data` は追加した列**（差分の 6 を参照）。元の設計に
  設問文の置き場が無く、`pdf_path` が NULL の「JSON問題のみ」のブックを表現できなかったため。
  PDF 運用しかしないなら 5 本目の migration ごと省いてよい。
