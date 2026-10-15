# 📖🧪 英語長文・習熟度テストの取込 (scripts/drill_import)

Codex などの AI が作った **英語長文** (科目 `english_long`・長文読解クラスの宿題) と **習熟度テスト** (科目 `proficiency_test`) の
ファイルを、検査してから本番の科目別ドリルに入れる道具です。形式は取込仕様書 `docs/drill-import-spec.md` (v1) が正本です。

| ファイル | 役目 |
|---|---|
| `validate_drill_import.py` | 検査 (仕様書 11 章のエラー・警告)・盲検のシート作り (`--make-blind`)・盲検の解答用紙の照合。引数なしは自己検査 |
| `import_drill_file.py` | 取込。既定は試運転 (本番に書かない)。`--apply` で本番に入れ、読み返して確かめる |
| `check_no_test_keys_in_repo.py` | 公開リポジトリにテスト・長文の取込ファイルが入っていないかのゲート (`run_all_gates.py` が毎 push 回す) |
| `fixtures/` | 自己検査用の**架空**のファイル (`"_fixture": true`)。`ok_*` は通る例、`bad_*` は `_expect` のコードだけで落ちる例 |

## 置き場所 (塾長のデスクトップ)

- 道具: `~/Desktop/📝 模試・演習/習熟度テスト/_tools/` に `validate_drill_import.py` と `import_drill_file.py` と この README を写して使う
  (英語長文も同じ道具)。**リポジトリの正本を直したら、この 3 本を写し直す。**
  ```bash
  cp scripts/drill_import/validate_drill_import.py scripts/drill_import/import_drill_file.py scripts/drill_import/README.md \
     "$HOME/Desktop/📝 模試・演習/習熟度テスト/_tools/"
  ```
- 英語長文: `~/Desktop/📚 教材/英語/02_長文読解/長文クラス用_科目別ドリル/<Lv1|Lv2|国公立>/<set_id>_<YYYY-MM-DD>/drill.json`
- 習熟度テスト: `~/Desktop/📝 模試・演習/習熟度テスト/<test_id>_第<N>回/test.json`
- 盲検の記録は同じフォルダの `_review/`。
- ★**リポジトリ (git の中) と seed-data には置かない。** 公開されるのでテストの答えが漏れる。2 本のスクリプトはどちらも
  git の中・seed-data の中のファイルを拒否する (`E_LOCATION`)。

## 流れ

```
作る (Codex) → 検査 → 盲検のシート → 3 名が解く → _review を書く → 検査 (照合まで) → 試運転 → 塾長が数を確認 → --apply → 読み返し
```

```bash
T="$HOME/Desktop/📝 模試・演習/習熟度テスト/_tools"
# 1. 検査 (盲検の前は E_REVIEW_MISSING 以外が 0 件になるまで直す)
python3 -I "$T/validate_drill_import.py" test.json
# 2. 盲検のシート (正解・解説・全訳・skill を外したシートと、解答用紙のひな形)
python3 -I "$T/validate_drill_import.py" --make-blind _review/blind_sheet test.json
# 3. 作者以外の 3 名がシートだけで解き、answer_template.json を写して _review/blind_A.json などに書く (choice_no は 1 始まり)
# 4. _review を書いて、もう一度検査 → エラー 0 (解答用紙との照合まで自動)
python3 -I "$T/validate_drill_import.py" test.json
# 5. 試運転 (本番には書かない。入る本数・問題数・飛ばす数を表示)
python3 -I "$T/import_drill_file.py" test.json
# 6. 塾長が数を確かめてから本番へ (入れた後に単元の本数と 👀 プレビューを読み返して照合)
python3 -I "$T/import_drill_file.py" test.json --apply
```

- `--json` で機械向けの出力。`--accept-warnings` は警告の中身を確かめたときだけ付ける。`--offline` は通信せず検査と変換だけ。
- 同じファイルを 2 回 `--apply` しても「取込済み」と言って何も送らない。取込済みのテスト・set_id に本文を足すことはできない
  (直した版はテストなら `revision` を上げて「第N回改1」、長文なら新しい set_id)。
- 結果はファイルの隣の `<ファイル名>.import_log.json` に残る (秘密は書かない)。

## 秘密と送り先

- 秘密は環境変数 `CRON_SECRET`、無ければ `~/.ai-juku-cron-secret` (Railway の `CRON_SECRET` と同じ値を 1 行・`chmod 600`)。
  自分以外も読める設定なら止まる。値は画面にもログにも出さない。
- 送り先は環境変数 `AI_JUKU_API_BASE` (既定 `https://ai-juku-api-production.up.railway.app`)。https 以外は手元の `127.0.0.1` / `localhost` だけ。
- 本番への取込は塾長が行う (作る側の AI はリポジトリの編集・本番への取込をしない)。

## 検査のコード

仕様書 11 章のとおり。加えて警告が 2 つある。
- `W_QUESTIONS` … 英語長文の設問数が単元の目安 (Lv.1 4〜5 問・Lv.2 / 国公立 5〜6 問) の外 (仕様書 3 章「設問数は目安」)
- `W_SKILL` … 習熟度テストの `skill` に単元名の決まっていない科目 (高校の math・japanese・social など) を書いた。外して取り込む (仕様書 10 章)

盲検の照合: `item_hash` は本文・問題文・選択肢から計算する (解説・訳・skill を直しても変わらない)。直した問題は `E_BLIND_STALE`、
解き手が 0 始まりで書いたと見られると `E_BLIND_OFFSET`、答えが正解と違う・note に「別解」「あいまい」などがあると `E_BLIND_MISMATCH`。

## 単体で動く (サーバの表の写し)

- 2 本とも **Python 3.9 の標準ライブラリだけ** (塾長の Mac の `/usr/bin/python3` は 3.9.6)・`python3 -I` でどのフォルダからでも動く。
  サーバのデプロイ前でも検査できるように、サーバの単元表などを `validate_drill_import.py` の `SERVER_TABLES` に写して持つ。
- ★サーバ (`server/main.py`) の単元 (`GRAMMAR_UNITS`・`_GRAMMAR_SUBJECT_UNIT_ORDER`)・科目・習熟度テストの単元名の形・上限を変えたら、
  `SERVER_TABLES` も同じ commit で直す。ずれると CI の `scripts/health_check/test_drill_import_parity.py` が落ちる。直したら上の cp で写し直す。

## テスト

- `python3 scripts/drill_import/validate_drill_import.py` … 自己検査 (fixtures・`--make-blind`・照合・`python3 -I`)。`run_all_gates.py` が拾う
- `python3 scripts/drill_import/check_no_test_keys_in_repo.py` … リポジトリに取込ファイルが無いこと (`run_all_gates.py` が拾う)
- `python3 scripts/health_check/test_drill_import_parity.py` … サーバの表との一致・出典の形・単体で動くこと・取込スクリプトの安全装置 (CI server-tests)
- `python3 scripts/health_check/test_proficiency_test_import.py` … `build_payloads` での変換 (1 始まり → 0 始まり) と、
  fixtures を取込スクリプトで実際のサーバ (TestClient) に入れて全問を照合 (CI server-tests)
- fixtures を作り直すときは中身を架空のままにし、`"_fixture": true` を付ける。メールアドレスの例はファイルに書かない (自己検査がコードで組む)
