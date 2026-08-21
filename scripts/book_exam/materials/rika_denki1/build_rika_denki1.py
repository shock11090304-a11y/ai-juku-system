#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""神テスト 教材「物理基礎 電気回路 演習 第1集」— 問題 PDF と取り込み JSON を作る。

    python3 scripts/book_exam/materials/rika_denki1/build_rika_denki1.py

出力 (どちらも**コミットする**): 物理基礎_電気回路_第1集.json / 同_問題.pdf
作法は docs/kamitest-manual/README.md (共通編) と rika.md。

★ 下の QUESTIONS が**唯一の正典**。JSON と PDF は _book_build.py が同時生成する。
★ 選択式 8 問 (2 点) + 記述 2 問 (3 点) = 22 点。記述を混ぜてあるのは、
  ・正解位置の配りが選択式だけを数えること
  ・記述には「誤答の切り方」が要らないこと
  を実物で通しておくため。
★ 正解の位置は 1:2 / 2:2 / 3:2 / 4:2 (選択式 8 問でちょうど 2 回ずつ)。
★ 記述の答え方は**設問文に書く** (「単位をつけて答えよ (例: 12A)」)。
  画面の入力欄には単位の手がかりが出ないので、書かないと正しく解いた生徒が落ちる。
★ 図は currentColor だけで描く (PDF は白地・アプリは暗地)。図に出す数値は
  設問文にも書く — 図が潰れても設問が解けるようにするため (verify が全数照合する)。
★ 相互チェック (CLAUDE.md 2026-08-16):
  ① _book_build.run() が刷り上がり PDF を読み返して全問・全選択肢・図の文字を逆照合
  ② verify() + check_grammar_books.py
  ③ 正解の一意性を敵対的に再読 — 合成抵抗は直列/並列で誤答が入れ替わるだけなので、
     どの誤答も「別の設定なら正しい値」にとどめ、この設問では一意になるようにした。

取り込み: python3 scripts/book_exam/import_books.py \
    scripts/book_exam/materials/rika_denki1 \
    --pdf-dir scripts/book_exam/materials/rika_denki1 --dry-run
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import _book_build as B  # noqa: E402

META = {
    "stem": "物理基礎_電気回路_第1集",
    "title": "物理基礎 電気回路 演習 第1集",
    "subject": "science",
    "subject_name": "理科",
    "level": "標準",
    "time_limit_min": 25,
    "intro": "記述の設問は、答え方を設問文のとおりにしてください (単位をつける)。"
             "解答は別画面の答案に入力してください。この冊子には自由に書き込めます。",
}

FIG_CHOKURETSU = (
    '<svg viewBox="0 0 320 116" width="320" height="116" role="img" '
    'aria-label="2 つの抵抗を直列につないだ回路">'
    '<g fill="none" stroke="currentColor" stroke-width="2">'
    '<path d="M20 96 V30 H90"/>'
    '<rect x="90" y="18" width="52" height="24"/>'
    '<path d="M142 30 H190"/>'
    '<rect x="190" y="18" width="52" height="24"/>'
    '<path d="M242 30 H300 V96 H20"/>'
    '<path d="M8 84 H32 M14 72 H26"/>'
    '</g>'
    '<g fill="currentColor" font-size="13" text-anchor="middle">'
    '<text x="116" y="60">20 Ω</text>'
    '<text x="216" y="60">30 Ω</text>'
    '<text x="20" y="112">電源</text>'
    '</g></svg>')

FIG_HEIRETSU = (
    '<svg viewBox="0 0 320 172" width="320" height="172" role="img" '
    'aria-label="2 つの抵抗を並列につないだ回路">'
    '<g fill="none" stroke="currentColor" stroke-width="2">'
    '<path d="M20 150 V40 H90"/>'
    '<path d="M90 40 V100"/>'
    '<path d="M90 40 H120"/>'
    '<rect x="120" y="28" width="52" height="24"/>'
    '<path d="M172 40 H230"/>'
    '<path d="M90 100 H120"/>'
    '<rect x="120" y="88" width="52" height="24"/>'
    '<path d="M172 100 H230"/>'
    '<path d="M230 40 V100"/>'
    '<path d="M230 40 H300 V150 H20"/>'
    '<path d="M8 138 H32 M14 126 H26"/>'
    '</g>'
    '<g fill="currentColor" font-size="13" text-anchor="middle">'
    '<text x="146" y="22">20 Ω</text>'
    '<text x="146" y="128">30 Ω</text>'
    '<text x="20" y="168">電源</text>'
    '</g></svg>')


def sci(genshou, housoku, rikishiki, keisan, ngs=None):
    """理科の解説 5 見出し。記述 (誤答が無い設問) では ngs を省く。"""
    body = (f"【何が起きているか】{genshou}\n"
            f"【使う法則】{housoku}\n"
            f"【立式】{rikishiki}\n"
            f"【計算】{keisan}")
    if ngs:
        body += "\n【誤答の切り方】\n" + "\n".join(ngs)
    return body


QUESTIONS = [
    dict(number=1, page=1, points=2, unit_tag="BUTSURI-CHOKURETSU",
         stem="図のように 20 Ω と 30 Ω の抵抗を直列につないだ。"
              "回路全体の合成抵抗は何 Ω か。",
         figure=FIG_CHOKURETSU,
         choices=["12 Ω", "25 Ω", "50 Ω", "600 Ω"], answer=3,
         explanation=sci(
             "抵抗が 1 本道に並んでいる。電流の通り道は 1 つしかない。",
             "直列の合成抵抗は足し算。R = R1 + R2",
             "R = 20 + 30",
             "R = 50 Ω。直列では合成抵抗は必ず**どの抵抗より大きく**なる。",
             ["1. 12 Ω — 並列につないだときの答え。1/R = 1/20 + 1/30 を使っている。",
              "2. 25 Ω — 2 つの平均。直列でも並列でも出てこない値。",
              "4. 600 Ω — 20 × 30 のかけ算。直列は和であって積ではない。"])),

    dict(number=2, page=1, points=2, unit_tag="BUTSURI-HEIRETSU",
         stem="図のように 20 Ω と 30 Ω の抵抗を並列につないだ。"
              "回路全体の合成抵抗は何 Ω か。",
         figure=FIG_HEIRETSU,
         choices=["12 Ω", "25 Ω", "50 Ω", "10 Ω"], answer=1,
         explanation=sci(
             "電流の通り道が 2 つに分かれている。",
             "並列の合成抵抗は逆数の和。1/R = 1/R1 + 1/R2",
             "1/R = 1/20 + 1/30 = 3/60 + 2/60 = 5/60",
             "R = 60/5 = 12 Ω。並列では合成抵抗は必ず**いちばん小さい抵抗より小さく**なる。",
             ["2. 25 Ω — 2 つの平均。いちばん小さい 20 Ω より大きいので、"
              "この時点で並列の答えにならない。",
              "3. 50 Ω — 直列につないだときの答え。",
              "4. 10 Ω — 20 Ω の半分。同じ抵抗 2 本を並列にしたときの形で、"
              "20 と 30 では使えない。"])),

    dict(number=3, page=2, points=3, unit_tag="BUTSURI-OHM",
         stem="100 V の電源に 25 Ω の抵抗をつないだ。流れる電流はいくらか。"
              "単位をつけて答えよ (例: 12A)。",
         answer="4A", accepted=["4 A", "4アンペア", "4 アンペア"],
         explanation=sci(
             "抵抗 1 本だけの回路なので、電源の電圧がそのままこの抵抗に掛かる。",
             "オームの法則 V = R × I",
             "100 = 25 × I",
             "I = 100 ÷ 25 = 4A。答えは単位をつけて「4A」と書く。")),

    dict(number=4, page=2, points=2, unit_tag="BUTSURI-DENRYOKU",
         stem="100 V の電源につないだ器具に 2 A の電流が流れている。"
              "この器具の消費電力は何 W か。",
         choices=["50 W", "100 W", "102 W", "200 W"], answer=4,
         explanation=sci(
             "電圧と電流の両方が分かっているので、そのまま電力が出る。",
             "電力 P = V × I",
             "P = 100 × 2",
             "P = 200 W。",
             ["1. 50 W — 100 ÷ 2 の割り算。電力はかけ算。",
              "2. 100 W — 電圧の数値をそのまま電力にした。",
              "3. 102 W — 100 + 2 の足し算。単位の違う量は足せない。"])),

    dict(number=5, page=2, points=2, unit_tag="BUTSURI-DENRYOKURYO",
         stem="500 W の電気ポットを 2 時間使った。使った電力量は何 Wh か。",
         choices=["250 Wh", "1000 Wh", "502 Wh", "2000 Wh"], answer=2,
         explanation=sci(
             "電力量は「どれだけの勢いで」×「どれだけの時間」使ったか。",
             "電力量 = 電力 × 時間。Wh で答えるなら時間は「時間」のまま使う。",
             "500 × 2",
             "1000 Wh (= 1 kWh)。",
             ["1. 250 Wh — 500 ÷ 2 の割り算。",
              "3. 502 Wh — 500 + 2 の足し算。",
              "4. 2000 Wh — 500 × 2 をさらに 2 倍している。"])),

    dict(number=6, page=2, points=2, unit_tag="BUTSURI-TEIKORITSU",
         stem="同じ材質で同じ太さの導線について、長さだけを 2 倍にすると、"
              "抵抗の大きさはどうなるか。",
         choices=["変わらない", "2 分の 1 になる", "2 倍になる", "4 倍になる"], answer=3,
         explanation=sci(
             "電子が通る道が長くなるほど、通りにくくなる。",
             "抵抗は長さに比例し、断面積に反比例する。",
             "長さが 2 倍 → 抵抗も 2 倍 (断面積は変えていない)",
             "2 倍になる。",
             ["1. 変わらない — 長さは抵抗に効く。効かないのは材質を変えないことだけ。",
              "2. 2 分の 1 になる — 太さ (断面積) を 2 倍にしたときの話。",
              "4. 4 倍になる — 長さを 2 倍にして断面積を半分にしたときの話。"])),

    dict(number=7, page=3, points=3, unit_tag="BUTSURI-BUNATSU",
         stem="20 Ω と 30 Ω を直列につなぎ、全体に 100 V を加えた。"
              "20 Ω の抵抗にかかる電圧はいくらか。単位をつけて答えよ (例: 12V)。",
         answer="40V", accepted=["40 V", "40ボルト", "40 ボルト"],
         explanation=sci(
             "直列なので 2 つの抵抗に**同じ電流**が流れる。まず電流を出す。",
             "オームの法則 V = R × I と、直列の合成抵抗 R = R1 + R2",
             "全体: 100 = (20 + 30) × I → I = 2A。20 Ω の分: V = 20 × 2",
             "V = 40V。残りの 60V が 30 Ω に掛かり、40 + 60 = 100V で合う。")),

    dict(number=8, page=3, points=2, unit_tag="BUTSURI-SEISHITSU",
         stem="並列につないだ 2 つの抵抗について、抵抗の値が違っていても"
              "必ず等しくなるものはどれか。",
         choices=["それぞれにかかる電圧", "それぞれに流れる電流",
                  "それぞれの抵抗の値", "それぞれの消費電力"], answer=1,
         explanation=sci(
             "並列は 2 つの抵抗が同じ 2 点の間に橋渡しされている形。",
             "同じ 2 点の間の電位差は 1 つしかない。",
             "どちらの抵抗も、電源の両端と同じ電圧が掛かる。",
             "等しくなるのは**電圧**。電流は I = V/R なので抵抗が小さい方に多く流れる。",
             ["2. それぞれに流れる電流 — 等しくなるのは直列のとき。",
              "3. それぞれの抵抗の値 — 問題文が「値が違っていても」と断っている。",
              "4. それぞれの消費電力 — P = V^2/R なので抵抗が違えば違う。"])),

    dict(number=9, page=3, points=2, unit_tag="BUTSURI-KEIKI",
         stem="回路に電流計と電圧計をつなぐとき、正しいつなぎ方はどれか。",
         choices=["電流計を並列、電圧計を並列", "電流計を並列、電圧計を直列",
                  "電流計を直列、電圧計を直列", "電流計を直列、電圧計を並列"], answer=4,
         explanation=sci(
             "電流計は「通り道に割り込んで数える」、電圧計は「両端の差を測る」道具。",
             "電流計の抵抗はとても小さく、電圧計の抵抗はとても大きい。",
             "小さい抵抗は直列に入れても回路を変えない。"
             "大きい抵抗は並列に足しても回路を変えない。",
             "電流計は直列、電圧計は並列。",
             ["1. 電流計を並列、電圧計を並列 — 電流計を並列にすると、"
              "抵抗がほぼ 0 の道ができて大きな電流が流れ、計器が壊れる。",
              "2. 電流計を並列、電圧計を直列 — 両方とも逆。",
              "3. 電流計を直列、電圧計を直列 — 電圧計を直列に入れると"
              "抵抗が大きすぎて、回路にほとんど電流が流れなくなる。"])),

    dict(number=10, page=3, points=2, unit_tag="BUTSURI-JOULE",
         stem="40 W の電熱線に 5 分間電流を流した。発生する熱量は何 J か。",
         choices=["200 J", "12000 J", "8 J", "2400 J"], answer=2,
         explanation=sci(
             "電熱線が使った電気エネルギーが、そのまま熱になる。",
             "熱量 Q = 電力 × 時間。**時間は秒に直す**。",
             "5 分 = 300 秒。Q = 40 × 300",
             "Q = 12000 J。",
             ["1. 200 J — 40 × 5。分のまま計算している。",
              "3. 8 J — 40 ÷ 5 の割り算。",
              "4. 2400 J — 40 × 60。1 分ぶんしか数えていない。"])),
]

if __name__ == "__main__":
    sys.exit(B.run(HERE, META, QUESTIONS))
