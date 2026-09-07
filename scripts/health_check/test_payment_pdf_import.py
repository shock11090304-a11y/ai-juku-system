#!/usr/bin/env python3
"""🏦 塾月謝アプリの楽天銀行 PDF 取込 (pdf.js) の回帰テスト (静的検査・本番に触れない)。

2026-09-08: 楽天銀行の入出金明細 PDF (iText 生成・HeiseiMin-W3 を埋め込まず CMap UniJIS-UCS2-HW-H を参照) で
pdf.js の getTextContent が全ページ 0 件になり「PDF からテキストを取得できませんでした」になっていた。
原因は getDocument に cMapUrl を渡していなかったこと (cdnjs は cmaps/ を配信しない → jsdelivr の npm パッケージ)。
"""
import os
import re
import shutil
import subprocess
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
    _v = re.search(r"app\.js\?v=(\d{8})([a-z]?)", html)
    check("app.js の ?v= が更新済み (20260908b 以降)", bool(_v) and (_v.group(1) > "20260908" or (_v.group(1) == "20260908" and _v.group(2) >= "b")), _v.group(0) if _v else "no ?v=")
    # ---- 2026-09-08: 名簿に無い新規生の入金 (要確認) の扱い ----
    print("2) 新規生の入金: ➕ 生徒を作る / 記帳月 / 申込取り込みの再照合 / Stripe 入金の除外")
    check("Stripe からの入金はノイズ (全角/半角)", "ストライプジ[ャヤ]パン" in js and "ｽﾄﾗｲﾌﾟｼﾞ[ｬﾔ]ﾊﾟﾝ" in js)
    check("isNoise は半角カナを全角に寄せても判定", "NOISE_PATTERNS.some(p => p.test(raw) || p.test(wide))" in js)
    check("振込人名の末尾「塾」を無視", "|塾|じゅく)$/" in js)
    check("申込取り込み: 保護者フリガナは括弧の内外どちらでも", "kanaRe.test(inside) ? inside : (kanaRe.test(outside) ? outside : '')" in js)
    check("申込取り込み: 毎月/初月の金額を読む", "firstMonthFee" in js and "monthlyTotal" in js)
    check("要確認行に「➕ 生徒を作る」", 'data-action="newstudent"' in js and "function startNewStudentFromCandidate(" in js)
    check("生徒追加の保存後にその入金を当月分として紐付け", "IMPORT.linkAfterAdd" in js and "c.monthMode = 'current'" in js)
    check("生徒追加/申込取り込み後に要確認行を再照合", js.count("rematchPendingCandidates()") >= 2 and "function rematchPendingCandidates(" in js)
    check("行ごとの記帳月 (翌月分/当月分) と初月ヒント", 'class="match-month-select"' in js and "looksLikeFirstMonth(" in js and "function candidateMonth(" in js)
    check("確定時: 当月分は入金月に記帳・要確認の残りは警告して残す", "candidateMonth(c)" in js and "は今回は反映されません" in js and "IMPORT.candidates = IMPORT.candidates.filter(c => !c.decided && !c.ignored)" in js)
    check("取込タブに「📥 申込取り込み」ボタン", 'id="importAppsFromImportBtn"' in html and "importAppsFromImportBtn" in js)
    check("生徒追加モーダルに取込ヒント欄", 'id="addStudentImportHint"' in html)
    check("style.css の ?v= が更新済み", "style.css?v=20260908" in html)
    # 純粋関数の実行検査 (jsc / node があるときだけ・CI では静的検査のみ)
    jsc = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"
    node = shutil.which("node")
    logic = os.path.join(REPO, "scripts", "health_check", "payment_import_logic.test.js")
    runner = jsc if os.path.exists(jsc) else (node if node else None)
    if runner and os.path.exists(logic):
        r = subprocess.run([runner, logic], cwd=REPO, capture_output=True, text=True)
        check("payment_import_logic.test.js (jsc/node) が ALL PASS", r.returncode == 0 and "❌" not in r.stdout, (r.stdout + r.stderr)[-400:])
    else:
        print("  ⏭ 実行検査はスキップ (jsc/node なし)")

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
