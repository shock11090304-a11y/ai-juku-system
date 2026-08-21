#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ChatGPT に神テストの問題を書かせるための**指示文**を作る。

    python3 scripts/book_exam/make_llm_prompt.py math
    python3 scripts/book_exam/make_llm_prompt.py japanese --honban --n 8
    python3 scripts/book_exam/make_llm_prompt.py science --out ~/Desktop/prompt.txt

■ ★ なぜ生成するのか — 指示文を手で書くと必ず腐る
    解説の見出しや subject の集合が変わっても、どこかに貼ってある指示文は
    変わらない。ここは正典 (_book_build.SUBJECT_HEADINGS /
    exam-book-admin-model.mjs の SUBJECTS) から組み立てるので、規則が変われば
    指示文も変わる。ずれていないことは check_llm_pipeline.py が確かめる。

■ 使い方
    1. このコマンドで指示文を作り、ChatGPT に丸ごと貼る
       (題材・単元は最後の 1 行に足す。例:「単元は 数学I の 2 次関数」)
    2. 返ってきた JSON を spec.json として保存
    3. python3 scripts/book_exam/materials/build_from_spec.py spec.json
       → 通れば冊子ができる。落ちたら「貼り戻し文」が出るので、
         それを ChatGPT に貼って直させる
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "materials"))
import _book_build as B  # noqa: E402

ADMIN_MJS = os.path.join(ROOT, "exam-app", "exam-book-admin-model.mjs")


def subjects():
    """subject の閉じた集合 (画面と DB の正典から読む)。"""
    with open(ADMIN_MJS, encoding="utf-8") as f:
        src = f.read()
    m = re.search(r"export const SUBJECTS\s*=\s*Object\.freeze\(\[(.*?)\]\)",
                  src, re.S)
    return re.findall(r"\{\s*value:\s*'([^']+)'\s*,\s*label:\s*'([^']+)'\s*\}",
                      m.group(1)) if m else []


EXAMPLE = '''```json
{
  "book": {
    "stem": "数学I_二次関数_第2集",
    "title": "数学I 二次関数 演習 第2集",
    "subject": "math",
    "subject_name": "数学",
    "level": "標準",
    "time_limit_min": 25,
    "intro": "解答は別画面の答案に入力してください。"
  },
  "questions": [
    {
      "number": 1,
      "points": 2,
      "unit_tag": "SUGAKU1A-HEIHOU",
      "stem": "2 次関数 $y = x^{2} - 6x + 5$ の最小値を求めよ。",
      "choices": ["$5$", "$-4$", "$3$", "$-3$"],
      "choices_plain": ["5", "-4", "3", "-3"],
      "answer": 2,
      "check": "minimum(x**2 - 6*x + 5, x)",
      "explanation": "【方針】平方完成して頂点を読む。下に凸なので頂点で最小。\\n【立式】y = (x - 3)^2 - 9 + 5\\n【計算】y = (x - 3)^2 - 4。頂点は (3, -4)。\\n【答え】最小値 -4 (このとき x = 3)\\n【誤答の切り方】\\n1. 5 — 定数項をそのまま答えにした。x = 0 のときの値でしかない。\\n3. 3 — 頂点の x 座標。聞かれているのは y の最小値。\\n4. -3 — 平方完成で引く 9 を 6 と取り違えた形。"
    }
  ]
}
```'''


def build(subject, n, honban, unit, note=""):
    heads = B.SUBJECT_HEADINGS[subject]
    ng = B.ng_heading(heads)
    label = dict(subjects()).get(subject, subject)
    subj_list = " / ".join(f"{v} ({l})" for v, l in subjects())

    p = []
    p.append("あなたは大学受験の教材をつくるプロの作問者です。"
             "これから「神テスト」という冊子受験アプリに載せる問題を作ります。")
    p.append("")
    p.append("# 出力の形")
    p.append("")
    p.append("**JSON のコードブロックを 1 つだけ**出してください。"
             "前置き・あとがき・解説文は書かないでください。"
             "この JSON はそのまま機械が読み、規則に合わないものは**すべて弾かれます**。")
    p.append("")
    p.append("# 何を作るか")
    p.append("")
    p.append(f"- 教科: **{label}** (`\"subject\": \"{subject}\"`)")
    p.append(f"- 設問数: **{n} 問**")
    p.append(f"- 単元・題材: {unit or '（ここに指定を書く）'}")
    if honban:
        p.append("- レベル: **共通テスト本番相当**。次の 4 つを必ず入れてください。")
        p.append("  1. **場面設定または資料**を `passages` に置く"
                 "（会話文・実測データの表・本文など）")
        p.append("  2. **誘導連鎖** — 前の設問の結果を次の設問で使う")
        p.append("  3. **判断・考察の設問** — 計算ではなく"
                 "「〜さんの考えは正しいか」「測定値はどちらへずれるか」")
        p.append("  4. **転用の設問** — 最後に条件を変えて同じ手順をたどらせる")
        p.append("  ★ ただし**各設問は単独でも解ける**ようにしてください。"
                 "必要な数値は設問文にも書く（1 問落とすと以降が全部落ちる冊子にしない）。")
    else:
        p.append("- レベル: 単元別の演習（各設問が独立していてよい）")
    if note:
        p.append("")
        p.append("## この冊子への追加の注文")
        p.append("")
        for line in str(note).splitlines():
            if line.strip():
                p.append(f"- {line.strip()}")
    p.append("")

    p.append("# 絶対に守る規則（破ると機械が弾きます）")
    p.append("")
    p.append("## 解答の形")
    p.append(f"- `subject` は次のどれか: {subj_list}")
    p.append("- **選択式**: `choices` に 2〜10 個（**4 個を既定**）。"
             "`answer` は **1 から始まる番号**（`0` 始まりにしない）")
    p.append("- **記述**: `choices` を書かない。`answer` は文字列。"
             "★ **数字だけの答えは弾かれます**（`\"50\"` は不可、`\"50Ω\"` は可）。"
             "単位をつけさせるなら**設問文に「単位をつけて答えよ (例: 12A)」と書く**")
    p.append("- ★ **共通テストのマーク欄（アに 5、イに −3）は作れません。**"
             "このアプリは 1〜10 の番号ボタンしか出せず、0 も負号も表現できません。"
             "誘導の中身は本番どおりでよいので、**解答形式は 4 択**にしてください")
    p.append("- `unit` という項目は使えません（紙と画面で食い違うため）")
    p.append("")
    p.append("## 解説（`explanation`）")
    p.append(f"- {label}の解説は次の見出しを、**この順で 1 回ずつ**使います。")
    p.append("")
    for h in heads:
        p.append(f"      {h}")
    p.append("")
    p.append(f"- 記述の設問では `{ng}` は書かなくてかまいません（誤答が無いため）")
    p.append(f"- `{ng}` は **1 行 1 誤答**で、行の頭を")
    p.append("  `番号. 選択肢の書き出し — 理由。` の形にしてください。")
    p.append("  - **正解の番号は書かない**、**誤答は 1 つも欠かさない**")
    p.append("  - 書き出しは、その選択肢だと**一目で分かるところまで**引く"
             "（他の選択肢と書き出しがかぶるなら、かぶりが解けるまで）")
    p.append("  - 理由は「なぜその誤りが起きるか」まで書く。"
             "「誤り」とだけ書かない")
    p.append("- ★ **解説に LaTeX を書かないでください。**"
             "画面では素のテキストとして出るので、`\\frac{1}{2}` や `$x$` は"
             "記号のまま表示されます。`x^2` `(a+b)/2` `√2` `≦` の形で書いてください")
    p.append("")
    p.append("## 数式（設問文と選択肢の中だけ）")
    p.append("- 設問文と選択肢の数式は `$…$` で囲みます（PDF で組版されます）")
    p.append("- `$…$` を使った選択肢には `choices_plain` も付けて、"
             "**素の表記**を同じ順で書いてください（解説の照合に使います）")
    if subject == "math":
        p.append("- ★ **正解を自分で決めないでください。** 各設問に `check` を付け、"
                 "**正解を計算する sympy の式**を書いてください。"
                 "機械がそれを独立に計算し、`choices_plain[answer-1]` と"
                 "一致しなければ弾きます。")
        p.append("  - 使える名前: "
                 "`x y a b c k n t` / `minimum maximum solve diff expand factor "
                 "simplify sqrt Rational discriminant Abs pi`")
        p.append("  - 例: `\"check\": \"minimum(x**2 - 6*x + 5, x)\"`")
        p.append("  - `choices_plain` は **sympy が読める形**にしてください"
                 "（`-2*x**2 + 40*x`）。範囲や日本語の選択肢には `check` を付けません")
    p.append("")
    p.append("## 正解の位置")
    lo, hi = n // 4, -(-n // 4)
    p.append(f"- 4 択 {n} 問なら、正解の番号 1〜4 が**それぞれ {lo}〜{hi} 回**に"
             "なるよう散らしてください")
    p.append("- **同じ番号を 3 問続けない**でください")
    p.append("")
    p.append("## その他")
    p.append("- `page`（ページ番号）は**書かないでください**。刷ってから機械が入れます")
    p.append("- `unit_tag` は `英大文字か数字-英大文字か数字` の形"
             "（例 `SUGAKU1A-HEIHOU`）。設問ごとに変えてください")
    p.append("- `passages`（本文・資料）を使うなら `title` と `html` が必須。"
             "`<p>` `<table>` `<u>` などの簡単な HTML だけ。"
             "`<script>` や `on…=` は使えません")
    p.append("- 図を付けるなら `figure` に **SVG の文字列**。線と文字は "
             "`currentColor`、`<script>` 禁止。"
             "★ **図に出す数値は設問文か本文にも書いてください**"
             "（図が潰れても解けるように）")
    p.append("- ★ **記述の答えを、他の設問文・本文・図に書かないでください**"
             "（答えが冊子の中に漏れます）")
    p.append("")
    p.append("# 使える項目（これ以外を書くと弾かれます）")
    p.append("")
    p.append("- `book`: `stem`（ファイル名になる。日本語とアンダースコア）/ "
             "`title` / `subject` / `subject_name` / `level` / "
             "`time_limit_min` / `intro`（任意）")
    p.append("- `passages`（任意・並び）: `title` / `html` / `source`（任意） / "
             "`break_before`（任意・真偽）")
    p.append("- `questions`（並び）: `number` / `points` / `unit_tag` / `stem` / "
             "`choices`（選択式のみ） / `choices_plain`（任意） / `answer` / "
             "`accepted`（記述の別解・任意） / `figure`（任意） / "
             "`figure_ticks`（任意） / `check`（任意） / `explanation`")
    p.append("")
    p.append("# 見本（1 問だけ。実際は上の設問数ぶん出してください）")
    p.append("")
    p.append(EXAMPLE)
    p.append("")
    p.append("# 最後に自分で確かめてから出してください")
    p.append("")
    p.append(f"- [ ] 設問は {n} 問ちょうどか")
    p.append("- [ ] `answer` は 1 始まりか（0 始まりになっていないか）")
    p.append(f"- [ ] 解説に {len(heads)} 個の見出しが順番どおり 1 回ずつあるか")
    p.append(f"- [ ] `{ng}` に**正解を書いていない**か、誤答が全部あるか")
    p.append("- [ ] 解説に LaTeX（`\\frac` や `$`）が混ざっていないか")
    p.append("- [ ] 正解の番号が偏っていないか、3 連続していないか")
    p.append("- [ ] **誤答が別の読み方で正解にならないか**"
             "（ここだけは機械が見られません。1 問ずつ疑って読み直してください）")
    return "\n".join(p) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("subject", choices=sorted(B.SUBJECT_HEADINGS),
                    help="教科 (math / japanese / science / social / grammar …)")
    ap.add_argument("--n", type=int, default=10, help="設問数 (既定 10)")
    ap.add_argument("--honban", action="store_true",
                    help="共通テスト本番相当の構成を求める")
    ap.add_argument("--unit", default="", help="単元・題材の指定")
    ap.add_argument("--note", default="",
                    help="この冊子への追加の注文 (改行で複数書ける)")
    ap.add_argument("--out", help="書き出し先 (既定 標準出力)")
    a = ap.parse_args()
    text = build(a.subject, a.n, a.honban, a.unit, a.note)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[ok] {a.out} に書き出しました ({len(text)} 文字)")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
