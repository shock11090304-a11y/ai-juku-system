#!/usr/bin/env python3
"""🏦 塾月謝アプリの楽天銀行 PDF 取込 (pdf.js) の回帰テスト (静的検査・本番に触れない)。

2026-09-08: 楽天銀行の入出金明細 PDF (iText 生成・HeiseiMin-W3 を埋め込まず CMap UniJIS-UCS2-HW-H を参照) で
pdf.js の getTextContent が全ページ 0 件になり「PDF からテキストを取得できませんでした」になっていた。
原因は getDocument に cMapUrl を渡していなかったこと (cdnjs は cmaps/ を配信しない → jsdelivr の npm パッケージ)。
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def main():
    print("🏦 楽天銀行 PDF 取込 回帰テスト\n")
    js = open(os.path.join(REPO, "payment", "app.js"), encoding="utf-8").read()
    html = open(os.path.join(REPO, "payment", "index.html"), encoding="utf-8").read()
    m = re.search(r"pdf\.js/(\d+\.\d+\.\d+)/pdf\.min\.js", html)
    check("index.html が pdf.js を CDN から読む", bool(m), "pdf.min.js not found")
    ver = m.group(1) if m else ""
    seg = js[js.index("async function extractPdfText"):js.index("function parsePDFText")]
    check("getDocument に cMapUrl / cMapPacked を渡す", "cMapUrl:" in seg and "cMapPacked: true" in seg)
    check("CMap は jsdelivr の pdfjs-dist から (cdnjs は cmaps/ を配信しない)", f"https://cdn.jsdelivr.net/npm/pdfjs-dist@{ver}/" in seg and "cmaps/" in seg, ver)
    check("worker も同じ版", f"pdf.js/{ver}/pdf.worker.min.js" in seg, ver)
    check("診断文言に CMap の可能性を明記", "CMap" in js[js.index("async function handleFile"):js.index("async function extractPdfText")])
    check("app.js の ?v= が更新済み (20260908b 以降)", bool(re.search(r"app\.js\?v=2026090[89]|app\.js\?v=20260[9]1|app\.js\?v=2026[1-9]", html)) and "app.js?v=20260908-monthend-ux" not in html)
    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
