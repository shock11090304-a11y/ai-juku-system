#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""冊子受験画面 (exam-book*) を **実ブラウザで通しで動かす**ゲート。

    python3 scripts/book_exam/check_exam_book_browser.py

■ なぜ静的検査だけでは足りないか
  check_book_exam.py は「書き方」を見る。だが この画面の事故は
  「起動はするが手書きが保存されない」「提出したのに 0 点」のように
  **動かして初めて分かる**形で出る。静的検査は 1 件も落とさずに通る。
  だから起動 → 解答 → 手書き → 消しゴム → 戻す → 提出 → 結果 まで
  実際の Chromium で 1 回通す。

■ 何を差し替えるか (★ここを広げないこと)
  差し替えるのは **接続設定 (exam-book-config.mjs) と supabase-js の 2 本だけ**。
  exam-book*.mjs / pdf.js / CSS / HTML は **配信するものそのもの**を読ませる。
  偽 Supabase は updated_at の CAS と提出後の 42501 を本物と同じ意味で返すので、
  「0 行更新なのに成功に見える」「提出後に書けてしまう」はここで落ちる。

■ 回せないとき
  playwright-core か Chromium が無ければ **飛ばしたことを必ず印字して** 0 で終わる。
  黙って緑にしない。CI に Chromium がある環境なら自動で回る。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SMOKE = os.path.join(HERE, "browser_smoke.mjs")
MOCK = os.path.join(HERE, "mock_supabase.mjs")


# =============================================================================
# 検査用の 2 ページ PDF を作る (リポジトリにバイナリを置かない)
# =============================================================================
def make_pdf(path):
    pages = ["Page One - Reading Passage", "Page Two - Questions"]
    contents = [
        (f"BT /F1 24 Tf 60 700 Td ({t}) Tj ET\n0 0 1 RG 4 w 60 100 m 500 600 l S").encode()
        for t in pages
    ]
    n = 2 + len(pages) * 2
    out = [None] * (n + 1)
    out[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids = []
    for i in range(len(pages)):
        pid, cid = 3 + i * 2, 4 + i * 2
        kids.append(pid)
        out[pid] = (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                    f"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 "
                    f"/BaseFont /Helvetica >> >> >> /Contents {cid} 0 R >>").encode()
        out[cid] = (b"<< /Length " + str(len(contents[i])).encode() + b" >>\nstream\n"
                    + contents[i] + b"\nendstream")
    out[2] = (f"<< /Type /Pages /Count {len(pages)} /Kids ["
              + " ".join(f"{k} 0 R" for k in kids) + "] >>").encode()

    buf = b"%PDF-1.4\n"
    offs = {}
    for i in range(1, n + 1):
        offs[i] = len(buf)
        buf += f"{i} 0 obj\n".encode() + out[i] + b"\nendobj\n"
    xref = len(buf)
    buf += f"xref\n0 {n + 1}\n0000000000 65535 f \n".encode()
    for i in range(1, n + 1):
        buf += f"{offs[i]:010d} 00000 n \n".encode()
    buf += f"trailer\n<< /Size {n + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    with open(path, "wb") as f:
        f.write(buf)


# =============================================================================
def find_chromium():
    if os.environ.get("CHROME_BIN") and os.path.exists(os.environ["CHROME_BIN"]):
        return os.environ["CHROME_BIN"]
    roots = [os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or "/opt/pw-browsers",
             os.path.expanduser("~/.cache/ms-playwright")]
    for root in roots:
        if not os.path.isdir(root):
            continue
        for d in sorted(os.listdir(root)):
            if not d.startswith("chromium"):
                continue
            for rel in ("chrome-linux/chrome", "chrome-mac/Chromium.app/Contents/MacOS/Chromium"):
                p = os.path.join(root, d, rel)
                if os.path.exists(p):
                    return p
    for name in ("chromium", "chromium-browser", "google-chrome"):
        p = shutil.which(name)
        if p:
            return p
    return None


def find_node_path():
    """playwright-core が置いてある node_modules を探す。"""
    cands = [os.environ.get("NODE_PATH"), os.path.join(ROOT, "node_modules")]
    scratch = os.environ.get("CLAUDE_SCRATCHPAD")
    if scratch:
        cands.append(os.path.join(scratch, "node_modules"))
    for c in cands:
        if c and os.path.isdir(os.path.join(c, "playwright-core")):
            return c
    return None


def main():
    print("=== 冊子受験画面 実ブラウザ通し確認 ===")
    node = shutil.which("node")
    chrome = find_chromium()
    node_path = find_node_path()

    missing = []
    if not node:
        missing.append("node")
    if not chrome:
        missing.append("Chromium (PLAYWRIGHT_BROWSERS_PATH / CHROME_BIN)")
    if not node_path:
        missing.append("playwright-core (npm i playwright-core)")
    if missing:
        print(f"  [skip] 実ブラウザ確認は未実行 — {', '.join(missing)} が無い")
        print("         ★ これは「通った」ではない。手元では")
        print("         npm i playwright-core && CHROME_BIN=... python3 "
              "scripts/book_exam/check_exam_book_browser.py")
        return 0

    print(f"  node={node}")
    print(f"  chromium={chrome}")
    print(f"  playwright-core={node_path}")
    print("  差し替えるのは exam-book-config.mjs と supabase-js の 2 本だけ "
          "(他は配信するものそのもの)")

    with tempfile.TemporaryDirectory(prefix="exambook_smoke_") as tmp:
        shutil.copy(MOCK, os.path.join(tmp, "mock_supabase.mjs"))
        make_pdf(os.path.join(tmp, "book.pdf"))
        env = dict(os.environ, CHROME_BIN=chrome, NODE_PATH=node_path)
        r = subprocess.run([node, SMOKE, ROOT, tmp], env=env, timeout=260,
                           capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode:
        sys.stdout.write(r.stderr[-2000:])
        return 1
    return 0


sys.exit(main())
