#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""塾長ログイン (ceo.html) が「パスワード管理アプリで入れる」形を保っているか検査する。

    python3 scripts/check_admin_login_ux.py

■ なぜこの検査が要るか
  ceo.html はかつて、Safari の自動入力が誤った値を連続送信して 401 → rate limit に
  陥る事故を嫌い、**自動入力を全面禁止**していた
  (type=text / autocomplete=off / name を非標準に / readonly→focus で解除)。
  その結果、塾長は**毎回パスワードを手打ち**することになり、
  「毎回ログインに苦戦する」という状態が常態化した (2026-08-17 指摘)。
  直したあと、同じ「自動入力を殺す」変更が再び入ると、また手打ちに戻る。
  ★戻ったことに気づけるよう、形を機械で固定する。

■ 見るもの
  1. パスワード欄が type="password" で autocomplete="current-password" であること
  2. 管理アプリが「サイト＋利用者」の組で保存できるよう username 欄があること
  3. 自動入力を殺す仕掛けが**無い**こと
     (autocomplete="off" / data-lpignore / data-1p-ignore / readonly→focus の解除 /
      -webkit-text-security で password に見せかける手口)
  4. セッションの自動延長 (renewed) を受け取って保存していること
  5. サーバ側 (/api/admin/verify) が延長を返す実装になっていること

★ この検査は**読むだけ**。パスワードそのものには一切触れない。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CEO = os.path.join(ROOT, "ceo.html")
SERVER = os.path.join(ROOT, "server", "main.py")


def main():
    bad = []
    if not os.path.exists(CEO):
        print(f"NG: {CEO} が無い")
        return 1
    html = open(CEO, encoding="utf-8").read()

    # --- ログインフォームだけを切り出す (ページ全体は巨大で誤検出のもと) ---
    m = re.search(r'<form id="adminLoginForm".*?</form>', html, re.S)
    if not m:
        print("NG: adminLoginForm が見つからない (ログイン画面の形が変わった)")
        return 1
    form = m.group(0)

    # 1. パスワード欄
    pw = re.search(r'<input[^>]*id="adminPassword"[^>]*>', form, re.S)
    if not pw:
        bad.append("パスワード欄 (#adminPassword) が無い")
    else:
        tag = pw.group(0)
        if 'type="password"' not in tag:
            bad.append('パスワード欄が type="password" でない '
                       '(type=text + text-security は管理アプリが認識できない)')
        if 'autocomplete="current-password"' not in tag:
            bad.append('パスワード欄に autocomplete="current-password" が無い')

    # 2. username 欄 (管理アプリが組で保存するために要る)
    if 'autocomplete="username"' not in form:
        bad.append('username 欄 (autocomplete="username") が無い — '
                   '管理アプリの保存が曖昧になり、古い値を拾う事故が起きやすい')

    # 3. 自動入力を殺す仕掛けが復活していないか
    for pat, why in (
        (r'autocomplete\s*=\s*"off"', 'autocomplete="off" が復活している'),
        (r'data-lpignore', 'data-lpignore が復活している'),
        (r'data-1p-ignore', 'data-1p-ignore が復活している'),
        (r'text-security', '-webkit-text-security で password に見せかけている'),
        (r'removeAttribute\(\s*[\'"]readonly', 'readonly→focus で解除する手口が復活している'),
    ):
        if re.search(pat, form):
            bad.append(f"自動入力を妨げる指定: {why}")

    # 4. 自動延長の受け取り
    if "renewed" not in html:
        bad.append("セッションの自動延長 (renewed) を受け取っていない — "
                   "固定期限のままだと期限切れのたびに手打ちになる")

    # 5. サーバ側
    if os.path.exists(SERVER):
        src = open(SERVER, encoding="utf-8").read()
        v = re.search(r"def admin_verify\(.*?\n(?=\n@|\ndef |\nclass )", src, re.S)
        if not v:
            bad.append("server/main.py に admin_verify が見つからない")
        elif '"renewed"' not in v.group(0):
            bad.append("/api/admin/verify が renewed を返していない (自動延長が効かない)")
    else:
        print("-- server/main.py が無いのでサーバ側は検査していない")

    if bad:
        for x in bad:
            print(f"NG: {x}")
        print(f"違反 {len(bad)} 件")
        return 1
    print("[OK] ceo.html — password 欄 / username 欄 / 自動入力の妨害なし / 自動延長")
    print("=== ALL PASS (塾長ログインは管理アプリで入れる形) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
