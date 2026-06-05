#!/usr/bin/env python3
"""
ai-juku-system 本物スクショ取得スクリプト
Playwright で trillion-ai-juku.com の Green pages + Yellow pages を撮影
PDF v4 用 mockup 差し替え素材を /tmp/ai_juku_screens/ に保存
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUT_DIR = Path("/tmp/ai_juku_screens")
OUT_DIR.mkdir(exist_ok=True)

BASE = "https://trillion-ai-juku.com"

# Green pages: PII リスクゼロ・pre-login で完結
GREEN_PAGES = [
    ("lp_top", f"{BASE}/", "PC", 1440, 900, 0),
    ("lp_full", f"{BASE}/", "PC", 1440, 2400, 0),
    ("login", f"{BASE}/login.html", "PC", 1440, 900, 0),
    ("pricing_compare", f"{BASE}/pricing-compare.html", "PC", 1440, 1800, 0),
    ("referral_lp", f"{BASE}/referral.html", "PC", 1440, 1600, 0),
    ("success_stories", f"{BASE}/success-stories.html", "PC", 1440, 1800, 0),
    ("course_kokuritsu", f"{BASE}/course-kokuritsu-nankan.html", "PC", 1440, 1800, 0),
    ("launch", f"{BASE}/launch.html", "PC", 1440, 1600, 0),
]

# Yellow pages: login redirect or UI shell — UI design 撮影に使用
# (実生徒 data なし・login 不要部分のみ撮影 / API 失敗で空 UI も価値あり)
YELLOW_PAGES = [
    ("mypage_login_gate", f"{BASE}/mypage.html", "PC", 1440, 1200, 0),
    ("ai_tutor_photo", f"{BASE}/ai-tutor-photo.html", "PC", 1440, 1400, 0),
    ("mock_exam", f"{BASE}/mock-exam.html", "PC", 1440, 1400, 0),
    ("textbook_generator", f"{BASE}/textbook-generator.html", "PC", 1440, 1400, 0),
    ("vocab", f"{BASE}/vocab.html", "PC", 1440, 1400, 0),
    ("english_exam", f"{BASE}/english-exam.html", "PC", 1440, 1400, 0),
    ("material_scan", f"{BASE}/material-scan.html", "PC", 1440, 1400, 0),
    ("university_exam", f"{BASE}/university-exam.html", "PC", 1440, 1400, 0),
    ("exam_prep", f"{BASE}/exam-prep.html", "PC", 1440, 1400, 0),
    ("safety_school", f"{BASE}/safety-school.html", "PC", 1440, 1200, 0),
    ("checkout", f"{BASE}/checkout.html", "PC", 1440, 1200, 0),
]

ALL_PAGES = GREEN_PAGES + YELLOW_PAGES


async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        results = []
        for name, url, viewport_type, width, height, wait_ms in ALL_PAGES:
            try:
                ctx = await browser.new_context(
                    viewport={"width": width, "height": height},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="ja-JP",
                )
                page = await ctx.new_page()
                # localStorage clear for safety (avoid stale tokens)
                await page.goto(url, wait_until="networkidle", timeout=20000)
                if wait_ms:
                    await page.wait_for_timeout(wait_ms)
                # PII 防御: localStorage clear
                try:
                    await page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
                except Exception:
                    pass
                out_path = OUT_DIR / f"{name}_{width}x{height}.png"
                # full_page=True で full scroll capture
                await page.screenshot(path=str(out_path), full_page=False)
                results.append((name, str(out_path), "OK"))
                print(f"✅ {name}: {out_path}")
                await ctx.close()
            except Exception as e:
                results.append((name, None, f"ERROR: {e}"))
                print(f"❌ {name}: {e}")
        await browser.close()
        return results


if __name__ == "__main__":
    results = asyncio.run(capture())
    ok = sum(1 for r in results if r[2] == "OK")
    fail = sum(1 for r in results if r[2] != "OK")
    print(f"\n=== Summary: {ok} OK / {fail} FAIL ===")
    for name, path, status in results:
        if status != "OK":
            print(f"  [FAIL] {name}: {status}")
