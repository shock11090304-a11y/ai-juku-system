#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""★ソースを直したのに PDF を再ビルドし忘れる事故を検出する。

  python3 sync_check.py suuA

実際に「content を直したが PDF は古いまま」で納品しかけた（レビューで発覚）。
KaTeX で組んだ PDF は数式部分がテキスト抽出で改行になるため、素朴な文字列比較は
偽陰性を出す（これも実際に踏んだ）。日本語部分だけを取り出して突き合わせる。
"""
import importlib
import os
import subprocess
import re
import sys

import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_kiso as BK  # noqa: E402

JP = re.compile(r"[ぁ-んァ-ヶ一-龥、。（）「」]{4,}")


def jp_chunks(s):
    """日本語の連続部分だけを取り出す（数式は KaTeX 描画で消えるため比較対象にしない）。"""
    return {m.group(0) for m in JP.finditer(re.sub(r"\s+", "", s))}


def main():
    # ★引数なしのときは **刷る巻を全部** 見る。以前は kiso 1巻だけで、
    #   run_all_gates.py は引数を渡さないので残り4巻が無検査だった。
    if len(sys.argv) <= 1:
        rc, ng = 0, []
        for v in BK.VOLUMES:
            print(f"\n########## {v} ##########", flush=True)
            r = subprocess.run([sys.executable, __file__, v], capture_output=True,
                               encoding="utf-8", errors="replace")
            print(r.stdout + r.stderr, end="")
            rc |= r.returncode
            if r.returncode:
                # ★どの巻がどう落ちたかを親の要約に出す。出さないと、1巻が「PDFが無い」で
                #   落ちただけで run_all_gates 側が全体を PDF-MISSING に分類し、
                #   **別巻の本物の不一致（172件）が報告から消える**（実測）。
                why = "PDF が無い" if "PDF が無い" in (r.stdout + r.stderr) else "本文が不一致"
                ng.append(f"{v}({why})")
        n = len(BK.VOLUMES)
        if ng:
            print(f"\n########## 突合できた巻 {n - len(ng)}/{n} ／ 落ちた巻: {' '.join(ng)} ##########")
        else:
            print(f"\n########## 突合できた巻 {n}/{n} すべて一致 ##########")
        sys.exit(rc)
    vol = sys.argv[1]
    if vol not in BK.VOLUMES:
        sys.exit(f"知らない巻: {vol}（{'/'.join(BK.VOLUMES)}）")
    V = BK.VOLUMES[vol]
    C = importlib.import_module(V["content"])
    pdf = os.path.join(HERE, V["out"])
    if not os.path.exists(pdf):
        sys.exit(f"PDF が無い: {pdf}")

    # ★解説は explanations_*.py が **オーバーレイで差し替える**（build_kiso.py:138）。
    #   content 側の explanation は、EXPL に登録がある問題では紙に出ない。
    #   そこを見ずに content だけ照合すると「PDFに無い＝ビルドし忘れ」と誤報告する
    #   （実測88件。刷り直しても直らないので、原因を誤らせる質の悪い誤検出だった）。
    EXPL, PTS = {}, {}
    if V.get("expl"):
        try:
            E = importlib.import_module(V["expl"])
        except ModuleNotFoundError:
            sys.exit(f"解説オーバーレイ {V['expl']} が見つからない（build_kiso.py と食い違っている）")
        EXPL = getattr(E, "EXPL", {}) or {}
        # ★POINTS(この単元のキモ)も紙に出る（build_kiso.py:157 の .pointbox）。
        #   しかも **EXPL が非空なのは kiso だけ**で、残り4巻はオーバーレイの中身が
        #   POINTS だけ。これを見ないと「オーバーレイを照合していない」穴が4巻ぶん残る。
        PTS = getattr(E, "POINTS", {}) or {}

    # ★問題文だけでなく、**紙に刷られる文字は全部**照合対象にする。
    #   単元名(目次と帯)・group見出し・編名・表紙・使い方は build_kiso.py が印字するのに
    #   検査していなかった。「単元名を直して刷り忘れる」は実際によくある編集。
    src_txt = [V.get("title", ""), V.get("subtitle", ""), V.get("tagline", ""),
               V.get("howto", ""), *[str(x) for x in PTS.values()]]
    for p in C.PARTS:
        src_txt += [p.get("area", ""), p.get("sub", "")]
        for u in p["units"]:
            src_txt += [u.get("name", ""), u.get("tag", "")]
    # ★キーの作り方は build_kiso.py:277 と同じにする（単元番号は **part をまたぐ通し番号**）。
    #   ここがずれると EXPL を1件も引けず、元の誤検出に戻る。
    for ui, u in enumerate((u for p in C.PARTS for u in p["units"]), 1):
        # ★`no` は content には無く **ビルド時に採番される**（build_kiso.py:109）。
        #   q.get("no") で引くと全部 None になり EXPL を1件も引けない（実測 一致0件）。
        for j, q in enumerate(u["problems"], 1):
            src_txt += [q.get("stem", ""), q.get("answer", "")]
            # 紙に出るのはどちらか一方（build_kiso.py:139）。出る方だけを照合する。
            src_txt.append(EXPL.get(f"{ui}-{j}") or q.get("explanation", ""))
    want = set()
    for s in src_txt:
        want |= jp_chunks(s)

    # ★集合の完全一致で照合すると、PDF側は数式のところで分断されて別チャンクになり
    #   ほぼ全件が「無い」と誤検出される（実際そうなった）。空白を除いた本文に対する
    #   部分文字列検索で照合する。
    got = re.sub(r"\s+", "", " ".join(pg.get_text() for pg in fitz.open(pdf)))
    missing = sorted(w for w in want if w not in got)

    print(f"=== ソース↔PDF 同期チェック（{V['out']}）===")
    print(f"  日本語チャンク: ソース{len(want)}個 ／ PDFに存在 {len(want)-len(missing)}個")
    if missing:
        print(f"\n  ★PDFに無い（＝再ビルドし忘れ）: {len(missing)}件")
        for m in missing[:12]:
            print("   ×", m[:60])
        sys.exit(1)
    print("  ✓ ソースの本文はすべてPDFに反映されている")


if __name__ == "__main__":
    main()
