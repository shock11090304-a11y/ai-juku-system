# 中学英語「不定詞の用法」ドリル 30問

塾長依頼 2026-07-29: 月曜1限 中学応用 (高校受験生) 向けの不定詞ドリル宿題。
無課金のため AI 生成は使わず作問し、検証後に `exam_questions` へ直INSERT。

## 使い方
```bash
python3 scripts/chugaku_dojo/futeishi/build.py            # items.py → build/ を生成 + gate 16種
railway run -s Postgres python3 scripts/chugaku_dojo/futeishi/insert.py           # dry-run
railway run -s Postgres python3 scripts/chugaku_dojo/futeishi/insert.py --commit  # 本番投入(冪等)
python3 scripts/chugaku_dojo/futeishi/post_check.py       # 本番の公開APIで投入結果を検証
```

## rollback
```sql
DELETE FROM exam_questions WHERE model = 'chugaku-koukou-futeishi-v1';
```

## 落とし穴 (再利用時に必ず読むこと)
- **filter を素の「不定詞」にしない**。dojo-drill の unitExact は
  `pref(q.unit).startsWith(preset.filter)` なので、「不定詞」だと既存「不定詞・動名詞」を巻き込む。
  「不定詞の用法」は既存単元と相互に接頭辞にならないので分離できる (gate G12 が検査)。
- **投入は静的フロントの push より先に**。プールが空のまま preset だけ本番に出ると、
  bank が topic 0件で全プールへフォールバックし、client の unitExact も 0件マッチで素通りするため
  「不定詞」カードで助動詞や長文が配信される (エラーにならないので気づけない)。
- **question_data は `json.dumps(ensure_ascii=False)` で保存**。ensure_ascii=True だと
  `\uXXXX` 化して bank の日本語 LIKE が一致しない。
- **解説に他単元の名前を書かない**。bank は question_data 全体を LIKE で引くので、解説に
  「過去形」と書くと過去形カードの取得枠にこの行が混ざる (gate G16 が検査)。
- **正解位置は分布だけ見ても足りない**。`pos = i % 4` は分布 [n,n,n,n] を満たすが 0,1,2,3 の
  完全周期になり、英文を読まず位置だけで全問正解できる (gate G15 が検査)。stem の md5 順に振る。
- **「答えはいつも to +原形」も tell**。空所補充だけで揃えず、原形不定詞・同意文書きかえ・
  用法の識別・意味の選択を混ぜて 12/30 に抑えている (gate G13)。
- **設問の同一判定は必ず (設問文, 選択肢) の組で行う**。「次の中から、英文として正しいものを
  選びなさい。」のように**指示文だけが stem になる形式は複数問で正当に重複**する。stem 単独で
  判定すると別問題を同一とみなして弾き、**本番に 25/30 問しか入らない事故**になる (実際に発生)。
  `build.py` の G2 / `insert.py` の冪等判定 / `post_check.py` の照合は**同じ規則**にそろえること。
- **insert.py は行(大問)単位で skip する**。1小問でも既出なら、その行の5問がまるごと入らない。
  既存の途中に問題を挿入すると後続の行がずれて全部 skip になるので、**追加は末尾に足すか、
  rollback の DELETE をしてから全件入れ直す**こと (エラーにならないので気づけない)。
- **解説だけを直しても再投入されない**(設問文と選択肢が同じなので skip される)。
  文言を直したときは rollback の DELETE → `insert.py --commit` で入れ直す。
