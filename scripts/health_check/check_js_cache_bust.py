#!/usr/bin/env python3
"""🧷 JS を変えたのに、それを読み込む HTML の `?v=` を上げていない commit を止める (2026-09-07)。

vercel.json の no-cache は *.html と auth-guard.js / cache-purge.js だけで、他の JS はブラウザに残る。
`?v=` を据え置くと「新しい HTML + キャッシュされた古い JS」で動く端末が出る (CLAUDE.md / memory の規則)。
直近の履歴では mypage.js の約半分・ceo.js の 6 割がバンプ漏れだった (システム点検で実測)。

使い方:
  python3 scripts/health_check/check_js_cache_bust.py [BASE] [HEAD]      # 省略時 HEAD~1..HEAD
  CI (server-tests.yml) は BASE=${{ github.event.before }} で呼ぶ。BASE が無ければ HEAD~1 に落とす。
判定:
  変更された *.js (root と payment/ 等・vendor/kakijun/exam-app/api/scripts は対象外) について、
  HEAD 側で `<script src="X.js?v=...">` で参照している HTML を全部集め、BASE 側と ?v= が同じなら違反。
  ?v= 無しで参照される JS (inline / no-cache 側) は対象外。違反が 1 件でもあれば exit 1。
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXEMPT_JS = {"auth-guard.js", "cache-purge.js"}          # vercel.json で no-cache
SKIP_PREFIX = ("kakijun/", "exam-app/", "vendor/", "static/", "api/", "scripts/", "server/", "node_modules/")
PAT = re.compile(r'<script[^>]+src="([^"?]+\.js)\?v=([^"]*)"')


def git(*a, check=True):
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True, check=check).stdout


def exists(rev):
    return subprocess.run(["git", "cat-file", "-e", f"{rev}^{{commit}}"], cwd=REPO, capture_output=True).returncode == 0


def show(rev, path):
    r = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=REPO, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def main():
    base = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BASE_SHA", "")).strip()
    head = (sys.argv[2] if len(sys.argv) > 2 else "HEAD").strip() or "HEAD"
    if not base or set(base) == {"0"} or not exists(base):
        base = f"{head}~1"
    changed = [f for f in git("diff", "--name-only", base, head).split("\n") if f]
    js_changed = [f for f in changed if f.endswith(".js") and os.path.basename(f) not in EXEMPT_JS and not f.startswith(SKIP_PREFIX)]
    print(f"🧷 JS キャッシュバスト検査: {base[:12]}..{head[:12]}  変更された JS: {js_changed or 'なし'}")
    if not js_changed:
        print("✅ 対象の JS 変更なし")
        return 0
    html_files = [h for h in git("ls-tree", "-r", "--name-only", head).split("\n") if h.endswith(".html")]
    head_htmls = {h: show(head, h) or "" for h in html_files}
    problems, checked = [], 0
    for js in js_changed:
        js_norm = os.path.normpath(js)
        refs = []
        for h, html in head_htmls.items():
            for m in PAT.finditer(html):
                src, v = m.group(1), m.group(2)
                if os.path.normpath(os.path.join(os.path.dirname(h), src)) == js_norm:
                    refs.append((h, src, v))
        if not refs:
            print(f"  ・{js}: ?v= 付きで参照する HTML なし (対象外)")
            continue
        for h, src, v in refs:
            checked += 1
            base_html = show(base, h)
            if base_html is None:
                continue  # HTML が新規
            m2 = re.search(r'<script[^>]+src="' + re.escape(src) + r'\?v=([^"]*)"', base_html)
            if m2 and m2.group(1) == v:
                problems.append(f"{js} を変更したのに {h} の `{src}?v={v}` が据え置き")
            else:
                print(f"  ・{js} ← {h}: ?v= 更新済み ({(m2.group(1) if m2 else '新規')} → {v})")
    if problems:
        print("\n❌ キャッシュバスト漏れ:")
        for p in problems:
            print(f"  - {p}")
        print("  → 参照側 HTML の ?v= を今日の日付+要点 (例 ?v=20260907-xxx) に更新してください。"
              " 据え置くと古い JS がキャッシュされた端末で新しい API/HTML と食い違います。")
        return 1
    print(f"✅ ?v= 更新漏れなし ({checked} 参照を確認)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
