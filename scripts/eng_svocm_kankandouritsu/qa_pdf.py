# -*- coding: utf-8 -*-
"""刷り上がった PDF を開いて、原稿（content.py）と**逆に照合**する。

    python3 build.py && python3 qa_pdf.py

★CLAUDE.md の「相互チェック」層①（出力物どうしの照合）。check.py は原稿と組版結果の
  文字列を見るが、こちらは **実際に PDF に焼かれた文字**を読み返す。
  Chrome の組版で欠けた・重なった・改ページで落ちた、は check.py では見えない。

★CI では回らない（PDF は生成物でリポジトリに無い）。トップレベルで fitz を import して
  いるので run_all_gates.py --no-pdf が自動的に外す。**紙の検査は手元で build 後に回すこと。**

★字形の照合は「刷るフォント」の cmap を正典にする（scripts/kaki_koushuu_eng/_print_font_cmap.txt）。
  その場にあるフォントで照合すると、Noto にあって Arial Unicode に無い字が素通りして
  紙で豆腐になる。刻印（ノンブル・柱）は Arial Unicode で焼くので**エラー**、
  本文は CSS のヒラギノで出るので**警告**にする。
"""
import os
import re
import sys
import unicodedata

import fitz

from layout import CIRCLE, parse, top_segments
from content import META, PART1, PART2, PART3

HERE = os.path.dirname(os.path.abspath(__file__))
DESKTOP = os.path.expanduser("~/Desktop")
BASE = "英語_英文解釈とSVOCM判別_関関同立"
CMAP_FILE = os.path.normpath(os.path.join(HERE, "..", "kaki_koushuu_eng", "_print_font_cmap.txt"))
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"
SAFE_SO = "★▲●◆■□◇→←↑↓〜" + CIRCLED
ERR, WARN = [], []


def err(w, m):
    ERR.append(f"[NG] {w}: {m}")


def load_cmap():
    """刷るフォント（Arial Unicode）が持っている符号位置の集合。"""
    ranges = []
    if not os.path.exists(CMAP_FILE):
        WARN.append(f"[warn] 刷るフォントの cmap が無い（{CMAP_FILE}）。字形の照合を飛ばした")
        return None
    for line in open(CMAP_FILE, encoding="utf-8"):
        line = line.split("#")[0].strip()
        if not line:
            continue
        a, _, b = line.partition("-")
        ranges.append((int(a, 16), int(b or a, 16)))
    return ranges


def in_cmap(ranges, ch):
    o = ord(ch)
    return any(a <= o <= b for a, b in ranges)


_WS = re.compile(r"\s+")
_MK = re.compile(f"[{CIRCLED}]")


def flat(s):
    """PDF から取った文字列を照合できる形に均す（改行・丸数字・全角空白を潰す）。"""
    return _WS.sub(" ", _MK.sub(" ", s.replace("　", " "))).strip()


def norm_en(s):
    return _WS.sub(" ", s).strip()


def dense(s):
    """空白を**全部**落とす。日本語は PDF の改行位置で語が割れ、空白を1つに潰すと
    原稿には無い空白が入って一致しなくなる（実測で和訳 20 件が誤検出になった）。"""
    return _WS.sub("", s.replace("　", ""))


_ASCII_RUN = re.compile(r"[A-Za-z0-9'’,.\-]+(?:\s+[A-Za-z0-9'’,.\-]+)*")


def ja_only(s):
    """英文の引用を落として、日本語の地の文だけを残す。
    ★解説は冒頭で本文の英語を引用することがある。その英語は問題編にも当然刷られているので、
      引用ごと照合すると「解説が問題編に漏れている」と誤って報告する（実測）。"""
    return dense(_ASCII_RUN.sub(" ", re.sub(r"<[^>]+>", " ", s)))


def read(tag, name):
    path = os.path.join(DESKTOP, name)
    if not os.path.exists(path):
        err(tag, f"PDF が無い: {path}（先に build.py を回すこと）")
        return None
    d = fitz.open(path)
    pages = [p.get_text() for p in d]
    n = d.page_count
    d.close()
    raw = "\n".join(pages)
    return {"tag": tag, "path": path, "pages": pages, "n": n,
            "raw": raw, "flat": flat(raw), "dense": dense(_MK.sub("", raw))}


def main():
    cmap = load_cmap()
    q = read("問題編", f"{BASE}_問題編.pdf")
    a = read("解答解説編", f"{BASE}_解答解説編.pdf")
    if not q or not a:
        print("\n".join(ERR))
        sys.exit(1)

    items1 = [it for g in PART1 for it in g["items"]]
    items3 = [it for g in PART3 for it in g["items"]]

    # ---------- 字形 ----------
    for doc in (q, a):
        bad = {}
        for ch in doc["raw"]:
            if ch in "\n\r\t ":
                continue
            if ord(ch) < 0x20 or ord(ch) in (0xFFFD, 0x25A0):
                bad[ch] = bad.get(ch, 0) + 1
            elif unicodedata.category(ch) == "So" and ch not in SAFE_SO:
                bad[ch] = bad.get(ch, 0) + 1
        if bad:
            err(doc["tag"], "豆腐・制御文字・想定外の記号: "
                            + str({f"U+{ord(k):04X}": v for k, v in bad.items()}))
        if cmap:
            miss = sorted({ch for ch in doc["raw"]
                           if ch not in "\n\r\t " and not in_cmap(cmap, ch)})
            if miss:
                WARN.append(f"[warn] {doc['tag']}: 刷るフォント(Arial Unicode)に無い字 "
                            f"{miss[:12]}（本文はヒラギノで出るので紙には出るが、"
                            "ノンブル・柱に使うと豆腐になる）")
        # 刻印（柱）は Arial Unicode で焼くので、こちらはエラー
        if cmap:
            stamp = f'{META["title"]} {doc["tag"].replace("解答解説編", "解答・解説編")}'
            bad_stamp = sorted({ch for ch in stamp if ch != " " and not in_cmap(cmap, ch)})
            if bad_stamp:
                err(doc["tag"], f"柱に焼く文字が刷るフォントに無い: {bad_stamp}")
        thin = [(i + 1, len(t.strip())) for i, t in enumerate(doc["pages"])
                if len(t.strip()) < 120]
        if thin:
            err(doc["tag"], f"中身の薄いページ（組版が崩れた疑い）: {thin}")

    # ---------- 刷り上がりからの逆照合 ----------
    for it in items1 + items3:
        if norm_en(it["en"]) not in q["flat"]:
            err("問題編", f'{it["id"]} の英文が紙に出ていない: {it["en"][:52]}…')
    for it in PART2:
        if norm_en(it["en"]) not in q["flat"]:
            err("問題編", f'{it["id"]} の英文が紙に出ていない: {it["en"][:52]}…')
        for ci, c in enumerate(it["choices"]):
            body = flat(re.sub(r"<[^>]+>", "", c))
            if body not in q["flat"]:
                err("問題編", f'{it["id"]} の選択肢{CIRCLE[ci]}が紙に出ていない: {body[:44]}…')

    # 答えが問題編に漏れていないか（紙で確認する）
    for it in items1 + items3 + list(PART2):
        for what, txt in [("和訳", it.get("ja"))] + \
                [(f"採点ポイント{i}", p) for i, p in enumerate(it.get("points") or [])]:
            if txt and len(dense(txt)) >= 14 and dense(txt) in q["dense"]:
                err("問題編", f'{it["id"]} の{what}が問題編に刷られている: {txt[:34]}…')
        if it.get("exp"):
            body = ja_only(it["exp"])[:34]
            if len(body) >= 20 and body in q["dense"]:
                err("問題編", f'{it["id"]} の解説が問題編に刷られている: {body}…')

    # 解答編に解答・解説がそろっているか
    for it in items1 + items3 + list(PART2):
        if dense(it["ja"]) not in a["dense"]:
            err("解答解説編", f'{it["id"]} の和訳が紙に出ていない: {it["ja"][:32]}…')
        for i, p in enumerate(it.get("points") or []):
            if dense(p) not in a["dense"]:
                err("解答解説編", f'{it["id"]} の採点ポイント[{i}]が紙に出ていない: {p[:30]}…')
        # ★解説の本体は notes。ここを照合していなかったので、丸ごと落ちても気づけなかった。
        for i, n in enumerate(it.get("notes") or []):
            body = dense(re.sub(r"<[^>]+>", "", n)
                         .replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"))
            if body[:30] not in a["dense"]:
                err("解答解説編", f'{it["id"]} の notes[{i}] が紙に出ていない: {n[:30]}…')
    # 第1部の解答記号が解答編に出ているか（①②③ の答えの行）
    for it in items1:
        labels = [lb for lb, _t, _u in top_segments(parse(it["dsl"]))]
        row = " ".join(labels)
        if row not in _WS.sub(" ", a["raw"]).replace("　", " "):
            err("解答解説編", f'{it["id"]} の解答記号 [{row}] が紙に出ていない')

    # ---------- 集計 ----------
    print("=" * 66)
    print(f"問題編 {q['n']} ページ / 解答解説編 {a['n']} ページ")
    print(f"逆照合: 第1部 {len(items1)} 問 / 第2部 {len(PART2)} 問 / 第3部 {len(items3)} 文")
    print("=" * 66)
    for w in WARN:
        print(w)
    if ERR:
        print(f"\n*** 紙の検査に通らなかった項目 {len(ERR)} 件 ***")
        for e in ERR:
            print(e)
        sys.exit(1)
    print("NG 0 件 / 刷り上がりと原稿は一致した")


if __name__ == "__main__":
    main()
