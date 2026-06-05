#!/usr/bin/env python3
"""
ai-juku-system スマホ viewport 実スクショ取得 (CH12 用)
iPhone 14 Pro (390x844) で本物 mobile UI を撮影
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUT_DIR = Path("/tmp/ai_juku_screens_mobile")
OUT_DIR.mkdir(exist_ok=True)

BASE = "https://trillion-ai-juku.com"

# CH12 (ai-juku の最高の部分 7 機能) に差し替える主要機能のモバイル版
MOBILE_PAGES = [
    ("lp_mobile", f"{BASE}/", 390, 1700),
    ("login_mobile", f"{BASE}/login.html", 390, 800),
    ("mypage_mobile", f"{BASE}/mypage.html", 390, 900),  # login gate
    ("ai_tutor_photo_mobile", f"{BASE}/ai-tutor-photo.html", 390, 1300),
    ("mock_exam_mobile", f"{BASE}/mock-exam.html", 390, 1400),
    ("vocab_mobile", f"{BASE}/vocab.html", 390, 1300),
    ("english_exam_mobile", f"{BASE}/english-exam.html", 390, 1500),
    ("textbook_generator_mobile", f"{BASE}/textbook-generator.html", 390, 1300),
    ("material_scan_mobile", f"{BASE}/material-scan.html", 390, 1100),
    ("university_exam_mobile", f"{BASE}/university-exam.html", 390, 1200),
    ("exam_prep_mobile", f"{BASE}/exam-prep.html", 390, 1100),
    ("safety_school_mobile", f"{BASE}/safety-school.html", 390, 1000),
    ("referral_mobile", f"{BASE}/referral.html", 390, 1400),
    ("course_kokuritsu_mobile", f"{BASE}/course-kokuritsu-nankan.html", 390, 1700),
    ("pricing_compare_mobile", f"{BASE}/pricing-compare.html", 390, 1700),
    ("success_stories_mobile", f"{BASE}/success-stories.html", 390, 1700),
    ("launch_mobile", f"{BASE}/launch.html", 390, 1500),
    ("checkout_mobile", f"{BASE}/checkout.html", 390, 1100),
]


async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        results = []
        for name, url, width, height in MOBILE_PAGES:
            try:
                ctx = await browser.new_context(
                    viewport={"width": width, "height": height},
                    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                    locale="ja-JP",
                    device_scale_factor=2,
                    is_mobile=True,
                    has_touch=True,
                )
                page = await ctx.new_page()
                await page.goto(url, wait_until="networkidle", timeout=20000)
                try:
                    await page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
                except Exception:
                    pass
                out_path = OUT_DIR / f"{name}_{width}x{height}.png"
                await page.screenshot(path=str(out_path), full_page=False)
                results.append((name, str(out_path), "OK"))
                print(f"✅ {name}")
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
