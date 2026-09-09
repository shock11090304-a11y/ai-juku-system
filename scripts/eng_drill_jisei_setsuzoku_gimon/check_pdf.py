# -*- coding: utf-8 -*-
"""刷り上がった PDF を読み返して、正典と1問ずつ突き合わせる。

    python3 scripts/eng_drill_jisei_setsuzoku_gimon/build_pdf.py      # 先に刷る
    python3 scripts/eng_drill_jisei_setsuzoku_gimon/check_pdf.py      # 紙を照合する

★これは「同じデータから刷ったのだから合っているはず」を確かめる検査ではない。
  組版で**落ちる・化ける・混ざる**のを捕まえる検査。実際に、刷って初めて見えた不良がある
  (正解位置が 1,2,3,4,1,2,3,4… の周期で、解答一覧を見れば解かずに当てられた)。
★PDF は生成物でリポジトリに入らないので CI では回せない。トップレベルで fitz を import
  しているため run_all_gates.py --no-pdf が自動で外す (外したものは一覧に出る)。
  手元では build_pdf.py のあとに必ず回すこと。
"""
import os
import re
import sys

import fitz     # ← トップレベル import。run_all_gates の needs_pdf がこれを見て CI から外す

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import build    # noqa: E402

PDF_Q = os.path.join(BASE, "英文法練習_時制接続詞疑問_問題.pdf")
PDF_A = os.path.join(BASE, "英文法練習_時制接続詞疑問_解答解説.pdf")
MARU = "①②③④"
NG = []


def norm(s):
    """組版で入る改行・行末ハイフン・全半角の空白差を吸収して比べられる形にする。"""
    s = s.replace("­", "").replace("​", "")
    s = re.sub(r"[\s　]+", " ", s)
    return s.strip()


def squash(s):
    """空白を全部落とす。日本語は行末で改行しても空白が入らないが、**PDF の抽出側が
    改行位置に空白を挿入する**ので、そのままでは全文一致が取れない (実測で90問中76問が不一致)。
    両側から落として比べれば、途中で切れていないかを全文で確かめられる。"""
    return re.sub(r"[\s　­​]+", "", s)


def text_of(path):
    with fitz.open(path) as d:
        return norm(" ".join(p.get_text() for p in d)), d.page_count


def main():
    for p in (PDF_Q, PDF_A):
        if not os.path.exists(p):
            print(f"違反 1 件\n  NG: {os.path.basename(p)} が無い。先に build_pdf.py を回すこと")
            sys.exit(1)

    rows, _ = build.build()
    answers = build.answers()
    tq, pages_q = text_of(PDF_Q)
    ta, pages_a = text_of(PDF_A)
    sa = squash(ta)

    # 空所は印刷では下線に置き換わるので、前後の断片で照合する
    for i, (r, ans_text) in enumerate(zip(rows, answers), 1):
        head, tail = [norm(x) for x in r["stem"].split("(   )")]
        for label, frag in (("前半", head), ("後半", tail)):
            if len(frag) >= 12 and frag not in tq:
                NG.append(f"NG: 第{i}問 の設問文{label}が問題編に出ていない: {frag[:48]}")
        for c in r["choices"]:
            if norm(c) not in tq:
                NG.append(f"NG: 第{i}問 の選択肢が問題編に出ていない: {c}")
        # 解説編: 完成文と解説は**全文**で照合する (途中で切れていないか)
        if squash(r["stem"].replace("(   )", ans_text)) not in sa:
            NG.append(f"NG: 第{i}問 の完成文が解答解説編に出ていない")
        if squash(r["explanation"]) not in sa:
            NG.append(f"NG: 第{i}問 の解説が解答解説編に全文で出ていない (途中で切れている?)")
        marker = norm(f'{i}. 正解 {MARU[r["answer"]]} {ans_text}')
        if marker not in ta:
            NG.append(f"NG: 第{i}問 の正解表示が紙とデータで食い違う (期待: {marker})")

    # 解答解説編の冒頭「正解一覧」の表を読み直して、1問ずつ突き合わせる。
    #   ★ここがずれると、生徒は解説ではなく一覧で丸つけをするので被害が大きい。
    listed = {}
    for head, tail in re.findall(r"問((?:\s+\d+){1,10})\s*答((?:\s+\d+){1,10})", ta):
        nums, vals = head.split(), tail.split()
        if len(nums) != len(vals):
            NG.append(f"NG: 正解一覧の行で問と答の数が合わない ({len(nums)} 対 {len(vals)})")
            continue
        for n, v in zip(nums, vals):
            listed[int(n)] = int(v)
    if len(listed) != len(rows):
        NG.append(f"NG: 正解一覧に載っているのが {len(listed)} 問 (全 {len(rows)} 問のはず)")
    for i, r in enumerate(rows, 1):
        if listed.get(i) != r["answer"] + 1:
            NG.append(f"NG: 正解一覧の第{i}問が {listed.get(i)} だが、正しくは {r['answer'] + 1}")
    if tq.count("解答欄") < 1:
        NG.append("NG: 問題編に解答欄が無い")

    # 豆腐 (グリフが無い文字) と、日本語が1文字も無い = フォント事故
    for name, t in (("問題編", tq), ("解答解説編", ta)):
        if "�" in t or "□" in t:
            NG.append(f"NG: {name} に文字化け/豆腐がある")
        if not re.search(r"[ぁ-んァ-ヶ一-龥]", t):
            NG.append(f"NG: {name} に日本語が1文字も無い (フォント事故の疑い)")

    # ★数式を入れたら KaTeX を通す約束。今は数式が無いことを機械で固定しておく
    for i, r in enumerate(rows, 1):
        if re.search(r"\\\(|\\\[|\$\$", r["stem"] + r["explanation"]):
            NG.append(f"NG: 第{i}問 に LaTeX がある。PDF は KaTeX を通していないので化ける")

    print("=== 刷り上がりと正典の照合 ===")
    print(f"問題編     {os.path.basename(PDF_Q)}  {pages_q} ページ")
    print(f"解答解説編 {os.path.basename(PDF_A)}  {pages_a} ページ")
    print(f"照合  設問文 {len(rows)} 問 / 選択肢 {sum(len(r['choices']) for r in rows)} 個 / "
          f"完成文・解説(全文)・正解番号 各 {len(rows)} 件 / 正解一覧 {len(listed)} 問")
    if NG:
        print(f"\n違反 {len(NG)} 件")
        for m in NG[:40]:
            print(" ", m)
        if len(NG) > 40:
            print(f"  … ほか {len(NG) - 40} 件")
        sys.exit(1)
    print("\n違反: 0 件  [OK] 紙に落ちた問題・選択肢・正解・解説は、すべて正典と一致")


if __name__ == "__main__":
    main()
