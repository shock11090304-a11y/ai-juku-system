#!/usr/bin/env python3
"""
AI学習コーチ塾 — プリフライトチェックスクリプト
本番デプロイ前の最終確認ツール

使い方:
    cd ai-juku-system
    python3 pre-launch-check.py
"""

import os
import re
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent
PASS = "\033[32m✅\033[0m"
FAIL = "\033[31m❌\033[0m"
WARN = "\033[33m⚠️ \033[0m"
INFO = "\033[36mℹ️ \033[0m"

results = {"pass": 0, "warn": 0, "fail": 0}

def check(label, condition, fix_hint=None, warn_only=False):
    if condition:
        print(f"  {PASS} {label}")
        results["pass"] += 1
        return True
    else:
        marker = WARN if warn_only else FAIL
        print(f"  {marker} {label}")
        if fix_hint:
            print(f"      → {fix_hint}")
        if warn_only:
            results["warn"] += 1
        else:
            results["fail"] += 1
        return False


def section(title):
    print(f"\n\033[1m{title}\033[0m")


print("=" * 60)
print("  🚀 AI学習コーチ塾 プリフライトチェック")
print("=" * 60)

# ==========================================================================
# 1. ファイル存在チェック
# ==========================================================================
section("1. ファイル存在確認")
required_files = [
    "index.html", "lp.html", "style.css", "app.js",
    "ceo.html", "ceo.js", "ceo.css",
    "mypage.html", "blog.html", "article.html", "articles.js",
    "business.html", "legal.html", "checkout.html",
    "server/main.py", "server/requirements.txt", "server/.env.example",
    "manifest.json", "sw.js", "analytics.js",
    "robots.txt", "sitemap.xml", "render.yaml",
]
for f in required_files:
    check(f"{f} が存在", (ROOT / f).exists())

# ==========================================================================
# 2. プレースホルダードメインチェック
# ==========================================================================
section("2. プレースホルダー置換状況（ai-juku.example → 実ドメイン）")
placeholder_files = []
for html_file in ROOT.glob("*.html"):
    content = html_file.read_text()
    if "ai-juku.example" in content:
        count = content.count("ai-juku.example")
        placeholder_files.append((html_file.name, count))

if not placeholder_files:
    check("全ページで実ドメインに置換済み", True)
else:
    check(f"プレースホルダーが残存 ({len(placeholder_files)}ファイル)", False,
          "各HTMLの「ai-juku.example」を実ドメイン（ai-juku.jp等）に置換してください:\n"
          "          cd ai-juku-system && sed -i '' 's/ai-juku.example/YOUR-DOMAIN.jp/g' *.html *.xml *.txt")
    for fname, count in placeholder_files:
        print(f"         - {fname}: {count}箇所")

# ==========================================================================
# 3. GA4 測定ID
# ==========================================================================
section("3. Google Analytics 4 設定")
if (ROOT / "analytics.js").exists():
    content = (ROOT / "analytics.js").read_text()
    check("GA4測定IDが設定されている", "G-XXXXXXXX" not in content,
          "analytics.js の 'G-XXXXXXXX' を実測定ID（analytics.google.com で取得）に置換",
          warn_only=True)

# ==========================================================================
# 4. .env 環境変数チェック
# ==========================================================================
section("4. 環境変数（.env）")
env_file = ROOT / "server" / ".env"
if not env_file.exists():
    check("server/.env が存在", False,
          "cp server/.env.example server/.env して、各キーを設定してください")
else:
    env_content = env_file.read_text()
    # 読み取って placeholder のままでないか確認
    placeholders = [
        ("STRIPE_SECRET_KEY", "sk_test_your"),
        ("ANTHROPIC_API_KEY", "sk-ant-api03-xxxxx"),
        ("LINE_CHANNEL_ACCESS_TOKEN", "your_line_channel_access_token"),
        ("STRIPE_PRICE_AI", "price_XXXXX"),
    ]
    for key, placeholder in placeholders:
        has_real_value = re.search(rf"{key}=(?!{re.escape(placeholder)}).+", env_content) is not None
        check(f"{key} が設定済み", has_real_value,
              f"server/.env の {key}= の後に実際の値を設定",
              warn_only=(key == "LINE_CHANNEL_ACCESS_TOKEN"))

# ==========================================================================
# 5. Python syntax チェック
# ==========================================================================
section("5. Python構文チェック（backend）")
import ast
py_files = list((ROOT / "server").glob("*.py"))
for pf in py_files:
    try:
        ast.parse(pf.read_text())
        check(f"{pf.relative_to(ROOT)} の構文OK", True)
    except SyntaxError as e:
        check(f"{pf.relative_to(ROOT)} の構文", False, f"Syntax error: {e}")

# ==========================================================================
# 6. manifest.json 形式チェック
# ==========================================================================
section("6. PWA manifest.json")
try:
    manifest = json.loads((ROOT / "manifest.json").read_text())
    check("manifest.json が有効なJSON", True)
    check(f"name が設定されている ({manifest.get('name')})", "name" in manifest)
    check(f"icons が2種以上定義", len(manifest.get("icons", [])) >= 2)
    check(f"start_url が相対パス", manifest.get("start_url", "").startswith("/"))
except Exception as e:
    check(f"manifest.json パース", False, str(e))

# ==========================================================================
# 7. sitemap.xml
# ==========================================================================
section("7. sitemap.xml（SEO）")
if (ROOT / "sitemap.xml").exists():
    sitemap = (ROOT / "sitemap.xml").read_text()
    url_count = sitemap.count("<url>")
    check(f"sitemap.xml にURL登録 ({url_count}件)", url_count >= 5,
          "ブログ記事を追加したら sitemap.xml にも <url> 追加")

# ==========================================================================
# 8. SSL証明書用 HTTPS 準備
# ==========================================================================
section("8. セキュリティ")
# Check for hardcoded API keys in frontend
for js_file in ROOT.glob("*.js"):
    content = js_file.read_text()
    has_real_key = re.search(r"sk-ant-api03-[a-zA-Z0-9_-]{20,}", content) or \
                   re.search(r"sk_live_[a-zA-Z0-9]{20,}", content)
    check(f"{js_file.name} に本番APIキーが直書きされていない",
          not has_real_key,
          "フロントJSに本番キーを書き込まないでください")

# ==========================================================================
# 9. バックエンド起動確認
# ==========================================================================
section("9. バックエンドライブラリ")
req_file = ROOT / "server" / "requirements.txt"
if req_file.exists():
    reqs = req_file.read_text()
    for pkg in ["fastapi", "uvicorn", "stripe", "pydantic"]:
        check(f"{pkg} が requirements.txt に含まれる", pkg in reqs)

# ==========================================================================
# 10. 法的ページ
# ==========================================================================
section("10. 法的ページ（日本法対応）")
if (ROOT / "legal.html").exists():
    legal = (ROOT / "legal.html").read_text()
    check("特定商取引法に基づく表記がある", "特定商取引法" in legal)
    check("利用規約がある", "利用規約" in legal)
    check("プライバシーポリシーがある", "プライバシー" in legal)

# ==========================================================================
# Summary
# ==========================================================================
print("\n" + "=" * 60)
total = results["pass"] + results["warn"] + results["fail"]
print(f"  📊 結果サマリー")
print(f"     {PASS} 合格: {results['pass']}/{total}")
print(f"     {WARN} 警告: {results['warn']}")
print(f"     {FAIL} 失敗: {results['fail']}")

if results["fail"] == 0 and results["warn"] == 0:
    print(f"\n  🎉 {PASS} \033[1m全チェック合格！本番デプロイ可能です\033[0m")
    print(f"\n  次のステップ:")
    print(f"     1. GitHub にpush")
    print(f"     2. Render.com で New Blueprint → render.yaml選択")
    print(f"     3. 環境変数を Render Dashboard で設定")
    print(f"     4. Deploy!")
    sys.exit(0)
elif results["fail"] == 0:
    print(f"\n  🟡 警告はあるが、デプロイ可能。warnの内容を確認してください。")
    sys.exit(0)
else:
    print(f"\n  🔴 {FAIL} \033[1m{results['fail']}件の失敗があります。デプロイ前に修正してください。\033[0m")
    sys.exit(1)
