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
| `tests/00_local_stubs.sql` | 素の Postgres で試すための Supabase 相当スタブ (**本番に流さない**) |
| `tests/10_schema_expectations.sql` | 振る舞いテスト 58 件 |

3 本とも**何度流しても安全**（`if not exists` / `or replace` / `drop … if exists`）。

## 流し方

```bash
# Supabase CLI
supabase db push

# または SQL Editor に 20260813010000 → 010100 → 010200 の順で貼る
```

★ **core だけ流して止めない**こと。RLS は 2 本目に入っているので、core だけの状態は
「ログインした全員が全生徒の答案を読める」DB になる。

## 検査

```bash
python3 scripts/english_schema/check_schema.py     # 単体
python3 scripts/run_all_gates.py english_schema    # リポジトリ共通の入口から
```

- **静的検査** … RLS を有効にし忘れたテーブル、ポリシーの無い操作、`search_path` を
  固定していない `security definer` 関数、`anon` 向けポリシー、冪等でない DDL などを落とす。
  DB が無くても回るので CI (`material-gates.yml`) でも走る。
- **実DB検査** … 使い捨ての Postgres に stubs → migrations を **2 周**流して
  (冪等性の確認)、`tests/10_schema_expectations.sql` の 58 件を回す。
  Postgres が見つからないときは実行しないが、**飛ばしたことを必ず印字する**。
  手元で明示的に指定するなら:

  ```bash
  ENGLISH_SCHEMA_TEST_DSN=postgresql://localhost/postgres \
    python3 scripts/english_schema/check_schema.py
  ```

  DSN が Railway / Supabase / RDS 等の本番らしいホストを指していたら実行を拒否する
  (使い捨て DB を `create` / `drop` するため)。

検査の内訳: 制約 14 / トリガ 3 / 生徒の RLS 20 / 講師の RLS 9 / 未ログイン 4 /
Storage 3 / 参照整合性 5。

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
- `correct_answer` / `accepted_answers` / `explanation` は、**その生徒が提出済みの
  答案でその設問に解答している場合だけ**返る。それ以外は `NULL`。
  判定結果は `revealed` 列にも出るので、UI の出し分けに使える。

講師 (`profiles.role = 'teacher'`) は `questions` テーブルを直接読める。

> Supabase のセキュリティリンタは `student_questions` を
> 「security definer view」として警告する。正解列を隠すのが目的なので意図的。

## 誰が何を触れるか (RLS)

| テーブル | 生徒 | 講師 |
| --- | --- | --- |
| `profiles` | 自分の行を読む・表示名を変える (`role` は変えられない) | 全員を読む・`role` を変えられる |
| `books` | 公開済みだけ読む | 全部読む・作る・直す・消す |
| `questions` | **直接は読めない** (`student_questions` 経由) | 全部読む・作る・直す・消す |
| `attempts` | 自分の分だけ。**提出後は自分でも書き換えられない** | 全員の分を読む |
| `answers` | 自分の未提出 attempt にだけ書ける | 全員の分を読む |
| `annotations` | 同上 (手書き) | 全員の分を読む |
| `review_items` | 自分の分だけ読み書き | 全員の分を読む |

未ログイン (`anon`) はどのテーブルにも触れない (`grant` ごと剥がしてある)。

提出の凍結は `attempts` の update ポリシーの `using` 側にだけ `submitted_at is null` を
置くことで実現している。「未提出 → 提出」の 1 回だけ通り、以後は点数も答案も動かせない。

### まだ DB では守れていないこと

**採点はクライアントが送った点数をそのまま保存している**。生徒は自分の未提出 attempt を
更新できるので、`total_score` に好きな値を入れて提出できる。DB だけでこれを塞ぐには
`security definer` の採点 RPC (`submit_attempt(attempt_id)` が `questions.correct_answer` と
`answers.user_answer` を突き合わせて `is_correct` / `total_score` を **サーバ側で**
書き、その中で `submitted_at` を打つ) を足して、`attempts.total_score` /
`answers.is_correct` への直接の update を落とす必要がある。今回のスキーマには入れていない。

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

### 5. Storage

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
- **採点の server-side 化** (上の「まだ DB では守れていないこと」)。
