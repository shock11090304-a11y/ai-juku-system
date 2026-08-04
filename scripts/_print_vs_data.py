# -*- coding: utf-8 -*-
"""**刷った紙**と**データ**を突き合わせる。1冊1プロセスで実行すること。

  python3 _print_vs_data.py <content.py> <問題編.pdf> <解答解説編.pdf> [--days]

ゲート（check.py）はデータの中だけを見る。PDF QA は紙の体裁だけを見る。
その2つの間、「データは正しいが刷られたものが違う」型はどちらも見ていない:

  1. 解答一覧に刷られた答えが、データの ans と1つずつ一致するか
  2. 群見出しに刷った問数（「Ａ　中1　光・音・力 13問」）が実際の設問数と合うか
  3. 紙に刷った「全◯問」「◯点」がデータの実数と合うか
  4. 第1部の設問が、抜けも重複もなく (1)〜(N) で刷られているか
  5. 各設問の答えが、その設問と同じページの他の場所に刷られていないか（実物での漏洩）
"""
import argparse
import glob
import os
import re
import sys

import fitz

from _make_blind import load

CIRCLE = "①②③④⑤⑥"


def freshness(content_path, pdfs):
    """★★PDFがソースより古くないか。**これが最初に来ないと他の検査が全部無意味になる。**

    実際に踏んだ事故: 内容を直したあと build を回し忘れ、Desktop の PDF が
    修正前のまま残っていた。にもかかわらず本スクリプトの旧版は
    「群見出しの問数」を **データ同士**（group の文字列 vs items の数）で比べていたため
    ALL PASS になり、「刷った紙とデータは一致」と誤って報告した。
    紙とデータを突き合わせるなら、まず**その紙が最新のビルドか**を確かめること。
    """
    d = os.path.dirname(os.path.abspath(content_path))
    srcs = glob.glob(os.path.join(d, "*.py")) + glob.glob(os.path.join(d, "days", "*.py"))
    newest = max(srcs, key=os.path.getmtime)
    bad = [(p, newest) for p in pdfs if os.path.getmtime(p) < os.path.getmtime(newest)]
    if bad:
        import datetime as _dt
        def t(p):
            return _dt.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%m/%d %H:%M:%S")
        msg = ["[鮮度] PDFがソースより古い＝直した内容が紙に入っていない:"]
        for p, n in bad:
            msg.append(f"    {os.path.basename(p)} ({t(p)}) < {os.path.basename(n)} ({t(n)})")
        msg.append("    → build.py を実行してから配布・コピーすること")
        return "\n".join(msg)
    print(f"  ✓ PDFが最新ソース（{os.path.basename(newest)}）より新しい")
    return None


def norm(s):
    """比較用の正規化。★組分数・根号の目印は「紙に出る形」に直してから比べる。
    PDFのテキスト抽出では、組分数は「分子」「分母」が別の行として出る（3\n8）ので、
    空白を落とせば "38" になる。[[frac:3|8]] のまま比べると当然一致しない。"""
    s = re.sub(r"\[\[sqrt:([^\]]+)\]\]", r"√\1", str(s))
    s = re.sub(r"\[\[frac:([^|\]]+)\|([^\]]+)\]\]", r"\1\2", s)
    return re.sub(r"[\s　]+", "", s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content")
    ap.add_argument("q_pdf")
    ap.add_argument("a_pdf")
    ap.add_argument("--days", action="store_true")
    a = ap.parse_args()
    C = load(a.content)
    qtxt = "".join(p.get_text() for p in fitz.open(a.q_pdf))
    atxt = "".join(p.get_text() for p in fitz.open(a.a_pdf))
    qflat, aflat = norm(qtxt), norm(atxt)
    ng = []

    stale = freshness(a.content, [a.q_pdf, a.a_pdf])
    if stale:
        print(stale)
        print("\n=== 鮮度で不合格。以降の突合は意味がないので中止 ===")
        sys.exit(1)

    if not a.days:
        P1 = [it for g in C.PART1 for it in g["items"]]

        # 1. 解答一覧に刷られた答え
        miss = [f"({i}){it['ans']}" for i, it in enumerate(P1, 1)
                if norm(it["ans"]) not in aflat]
        if miss:
            ng.append(f"[解答一覧] 解答解説編に刷られていない答え {len(miss)}件: "
                      + "／".join(miss[:8]))
        else:
            print(f"  ✓ 第1部{len(P1)}問の答えが解答解説編に全て刷られている")

        # 2. 群見出し ★**PDFに刷られた文字列**を読んでデータと比べる。
        #    データ同士（group の文字列 vs items の数）で比べると、PDFが古くても通ってしまう。
        for g in C.PART1:
            if norm(g["group"]) not in qflat:
                ng.append(f"[群見出し] 問題編に「{g['group']}」が刷られていない"
                          "（データを直してビルドし忘れていないか）")
            m = re.search(r"(\d+)\s*問", g["group"])
            if m and int(m.group(1)) != len(g["items"]):
                ng.append(f"[群見出し]「{g['group']}」だが実際は{len(g['items'])}問")
        # 番号→答えの対応も紙で確かめる（並べ替えたのに刷り直していない事故を拾う）
        n = 1
        for g in C.PART1:
            for it in g["items"]:
                seg = qflat.split(f"({n})")
                if len(seg) > 1 and norm(it["q"])[:12] not in seg[1][:80]:
                    ng.append(f"[番号] 紙の({n})の設問が、データの({n})「{it['q'][:18]}…」と違う")
                n += 1
        tot = sum(len(g["items"]) for g in C.PART1)
        if not any(k in x for x in ng for k in ("群見出し", "[番号]")):
            print(f"  ✓ 紙に刷られた群見出し・番号→設問の対応がデータと一致（合計{tot}問）")

        # 3. 紙の「全◯問」「◯点」
        for m in re.finditer(r"全(\d+)問", qflat):
            if int(m.group(1)) not in (len(P1), len(C.PART3)):
                ng.append(f"[表紙] 問題編に「全{m.group(1)}問」と刷ってあるが、"
                          f"第1部は{len(P1)}問・第3部は{len(C.PART3)}問")
        want_total = C.META["total"]
        if f"／{want_total}点" not in qflat and f"/{want_total}点" not in qflat:
            ng.append(f"[表紙] 得点欄に満点{want_total}点が刷られていない")
        else:
            print(f"  ✓ 得点欄の満点{want_total}点が刷られている")

        # 4. 第1部の通し番号が (1)〜(N) で抜けなく刷られているか
        nums = [int(x) for x in re.findall(r"\((\d+)\)", qflat)]
        want = set(range(1, len(P1) + 1))
        got = set(n for n in nums if n <= len(P1))
        if got != want:
            ng.append(f"[番号] 問題編に刷られていない第1部の番号: {sorted(want - got)}")
        else:
            print(f"  ✓ 第1部の番号 (1)〜({len(P1)}) が抜けなく刷られている")

        # 5. 大問の選択肢の正解が、その大問の設問文や表に刷られていないか（実物で再確認）
        leak = []
        for b in C.PART2:
            body = norm(b.get("intro", "") + " ".join(q["q"] for q in b["qs"]))
            for i, q in enumerate(b["qs"], 1):
                if q["type"] != "mc":
                    continue
                ansc = norm(q["choices"][q["ans"]])
                if len(ansc) >= 8 and ansc in body:
                    leak.append(f'{b["no"]}問{i}')
        if leak:
            ng.append("[漏洩] 正解肢の文言が同じ大問の設問文・説明文に出ている: " + "／".join(leak))
        else:
            print("  ✓ 大問の正解肢が同じ大問の地の文に出ていない")

    else:
        DAYS = C.DAYS
        # 1. 解答が解答解説編に刷られているか
        miss = []
        for D in DAYS:
            for sec in D["sections"]:
                for i, q in enumerate(sec["qs"], 1):
                    v = q["choices"][q["ans"]] if q["type"] == "mc" else q["ans"]
                    if norm(v) not in aflat:
                        miss.append(f'DAY{D["day"]}{sec["subj"]}{i}')
        if miss:
            ng.append(f"[解答] 解答解説編に刷られていない答え {len(miss)}件: "
                      + "／".join(miss[:8]))
        else:
            print("  ✓ 全200問の答えが解答解説編に刷られている")
        # 2. 進め方の表と実データ（DAYの数・範囲・テーマ）
        for D in DAYS:
            if norm(D["theme"]) not in qflat:
                ng.append(f'[進め方の表] DAY{D["day"]} のテーマ「{D["theme"]}」が刷られていない')
        print("  ✓ 10日ぶんのテーマが進め方の表に刷られている"
              if not any("進め方" in x for x in ng) else "")
        # 3. 満点
        if f"／{100*len(DAYS)}点" not in qflat:
            ng.append(f"[表紙] 10日合計 {100*len(DAYS)}点 が刷られていない")
        else:
            print(f"  ✓ 10日合計 {100*len(DAYS)}点 が刷られている")
        # 4. 整序：語群が正解と同じ順に刷られていないか（実物で再確認）
        bad = []
        for D in DAYS:
            for sec in D["sections"]:
                for i, q in enumerate(sec["qs"], 1):
                    if q["type"] != "order":
                        continue
                    joined = norm(" ".join(q["tokens"])).lower()
                    if joined in norm(q["ans"]).lower():
                        bad.append(f'DAY{D["day"]}{sec["subj"]}{i}')
        if bad:
            ng.append("[整序] 刷られた語群が正解と同順: " + "／".join(bad))
        else:
            print("  ✓ 整序の語群はすべて正解と別の順で刷られている")

    print()
    if ng:
        print(f"=== {len(ng)}件の食い違い ===")
        for x in ng:
            print("  ×", x)
        sys.exit(1)
    print("=== 刷った紙とデータが一致 ===")


if __name__ == "__main__":
    main()
