# -*- coding: utf-8 -*-
"""解答解説編の機械ゲート。

G1  タグ露出／Markdown 記法の漏れ／制御文字
G2  解答一覧(ans_kiso/ans_jissen)と各設問カードの正解バッジの一致
G3  選択肢を切る表で「○」がちょうど1つ、しかもそれが正解番号
G4  問題編PDFの正解と、こちらの正解の突合(外部の正解表)
G5  半端ページ(文字数が極端に少ないページ)の検出
G6  品詞分解の行が (語, 品詞, 意味) の3要素になっているか

usage: python3 check.py <final.pdf>
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content_ch1 import CH1
from content_ch2 import CH2
from content_ch3 import CH3
from content_ch4 import CH4

CHAPTERS = [CH1, CH2, CH3, CH4]

# 問題編PDFを独立に読んで確定させた正解（このファイルが唯一の外部基準）
EXPECTED_JISSEN = {
    1: ["③", "②", "⑤", "④", "③"],
    2: ["③", "②", "⑤", "④", "②", "①"],
    3: ["②", "④", "①", "③"],
    4: ["②", "③", "④", "①", "③"],
}
EXPECTED_KISO = {
    1: ["②", "①", "②", "①", "①", "②", "①", "②", "①", "②", "③", "①", "②", "③"],
    2: ["①", "②", "②", "②", "①", "①", "④", "②", "①", "③", "④",
        "③", "④", "①", "②", "②", "③", "②", "③"],
    3: ["①", "②", "①", "②", "①", "②", "①"],
    4: [],
}
MARU = "①②③④⑤⑥"

fails = []
warns = []


def fail(g, msg):
    fails.append("[%s] %s" % (g, msg))


def warn(g, msg):
    warns.append("[%s] %s" % (g, msg))


def all_strings(obj, path="root"):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from all_strings(v, "%s.%s" % (path, k))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from all_strings(v, "%s[%d]" % (path, i))


ALLOWED = re.compile(r"</?[bukrn]>")


def g1_tags():
    for ch in CHAPTERS:
        for path, s in all_strings(ch):
            if "**" in s:
                fail("G1", "Markdown ** : %s : %s" % (path, s[:60]))
            for ch_ in s:
                if ord(ch_) < 0x20 and ch_ != "\n":
                    fail("G1", "制御文字 U+%04X : %s" % (ord(ch_), path))
            if "�" in s:
                fail("G1", "置換文字 : %s" % path)
            # 許可外のタグらしき文字列
            for m in re.finditer(r"</?[A-Za-z][A-Za-z0-9]*\s*/?>", s):
                if not ALLOWED.fullmatch(m.group(0)):
                    fail("G1", "未許可タグ %s : %s" % (m.group(0), path))


def g2_answers():
    for ch in CHAPTERS:
        n = ch["no"]
        kiso_badges = [it["ans"] for b in ch.get("kiso", []) for it in b["items"]]
        listed = [a for _, a in ch["ans_kiso"]]
        if kiso_badges != listed:
            fail("G2", "第%d章 基礎: 一覧%s ≠ カード%s" % (n, listed, kiso_badges))
        jis_badges = [q["ans"] for q in ch.get("jissen", [])]
        listed_j = [a for _, a in ch["ans_jissen"]]
        if jis_badges != listed_j:
            fail("G2", "第%d章 実戦: 一覧%s ≠ カード%s" % (n, listed_j, jis_badges))


def g3_cut():
    for ch in CHAPTERS:
        n = ch["no"]
        items = [("基礎", it) for b in ch.get("kiso", []) for it in b["items"]]
        items += [("実戦", q) for q in ch.get("jissen", [])]
        for kind, q in items:
            cut = q.get("cut")
            if not cut:
                continue
            oks = [no for no, ok, _ in cut if ok]
            if len(oks) != 1:
                fail("G3", "第%d章 %s %s: ○が%d個" % (n, kind, q["no"], len(oks)))
                continue
            if oks[0] != q["ans"]:
                fail("G3", "第%d章 %s %s: ○=%s だが正解=%s"
                     % (n, kind, q["no"], oks[0], q["ans"]))
            nos = [no for no, _, _ in cut]
            if len(set(nos)) != len(nos):
                fail("G3", "第%d章 %s %s: 選択肢番号が重複 %s" % (n, kind, q["no"], nos))
            # 番号が①から連番か
            want = list(MARU[: len(nos)])
            if nos != want:
                fail("G3", "第%d章 %s %s: 選択肢番号が連番でない %s" % (n, kind, q["no"], nos))


def g4_external():
    for ch in CHAPTERS:
        n = ch["no"]
        got = [a for _, a in ch["ans_jissen"]]
        if got != EXPECTED_JISSEN[n]:
            fail("G4", "第%d章 実戦の正解が外部基準と不一致: %s vs %s"
                 % (n, got, EXPECTED_JISSEN[n]))
        gotk = [a for _, a in ch["ans_kiso"]]
        if gotk != EXPECTED_KISO[n]:
            fail("G4", "第%d章 基礎の正解が外部基準と不一致: %s vs %s"
                 % (n, gotk, EXPECTED_KISO[n]))


def g6_bunkai():
    for ch in CHAPTERS:
        p = ch.get("passage")
        if not p:
            continue
        for sec in p["sections"]:
            for r in sec["rows"]:
                if r[0] == "#":
                    continue
                if len(r) != 3:
                    fail("G6", "第%d章 %s: 行の要素数が%d — %s"
                         % (ch["no"], sec["no"], len(r), r))
                if not r[1].strip():
                    fail("G6", "第%d章 %s: 品詞欄が空 — %s" % (ch["no"], sec["no"], r[0]))
            if not sec.get("yaku"):
                fail("G6", "第%d章 %s: 訳が無い" % (ch["no"], sec["no"]))


def g5_pdf(path):
    import fitz

    d = fitz.open(path)
    txt_all = []
    for i, p in enumerate(d, 1):
        t = p.get_text()
        txt_all.append(t)
        body = t.replace("\n", "")
        if len(body) < 220 and i not in (1,):
            warn("G5", "p%d の文字数が少ない(%d)" % (i, len(body)))
    joined = "".join(txt_all)
    for bad in ("<b>", "</b>", "<u>", "</u>", "<span", "**", "\x00", "�"):
        if bad in joined:
            fail("G1", "PDF本文にタグ/記号が露出: %r" % bad)
    # 全設問の正解バッジがPDFに出ているか(章ごとの一覧の並びで確認)
    print("  PDF %d ページ / 総文字数 %d" % (d.page_count, len(joined)))
    return d.page_count


if __name__ == "__main__":
    g1_tags()
    g2_answers()
    g3_cut()
    g4_external()
    g6_bunkai()
    if len(sys.argv) > 1:
        g5_pdf(sys.argv[1])
    for w in warns:
        print("WARN", w)
    for f in fails:
        print("FAIL", f)
    print("---")
    print("FAIL=%d WARN=%d" % (len(fails), len(warns)))
    sys.exit(1 if fails else 0)
